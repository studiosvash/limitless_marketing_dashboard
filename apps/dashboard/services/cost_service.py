"""Connector spend — the read side of `connector_costs`.

Every DataForSEO response carries the charge it just incurred (`tasks[].cost`, documented
in every endpoint family's response table). Until now every connector discarded it, which
is why Settings → Usage & Budget could only print "Cost tracking not available yet" next
to each module and why the budget cap the user sets there could not be enforced: nothing
knew what had been spent.

The connectors now append one row per run via `pipeline.db.writer.insert_connector_cost`.
This module is the only thing that reads them back. Three questions, three functions:

  cost_last_90_days(site_id)          "what has this project cost lately, and on what?"
  cost_by_month(site_id, months=3)    "is that going up or down?"
  cost_since(site_id, start_date)     "has the budget cap been passed?" (enforcement
                                       is not built here — this is the number it needs)

Honesty rules, matching the rest of the codebase:
  - No row recorded yet => 0.0 and an empty breakdown. Never None where a number belongs,
    never a projection dressed up as a measurement.
  - Nothing here estimates or extrapolates. Every figure returned is a sum of rows that
    a real, billed API response reported.
  - A query failure logs and returns the same honest zeros rather than 500-ing the page.

SQL notes: aggregation is plain SQLAlchemy Core (func.sum/count + group_by), which is
identical on SQLite and Postgres. Month bucketing is done in PYTHON, not in SQL, because
strftime() is SQLite-only and date_trunc() is Postgres-only — the one place this would
otherwise have needed a dialect branch.
"""
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select

from pipeline.db.schema import ConnectorCost
from pipeline.db.writer import ensure_tables
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

# The window Settings → Usage & Budget summarises.
DEFAULT_WINDOW_DAYS = 90


def _as_datetime(value) -> datetime:
    """Accept a date or datetime and return a naive UTC datetime for comparison.

    `ConnectorCost.run_at` is a plain DateTime column: SQLite hands back naive values and
    Postgres would compare an aware bound parameter against a naive column. Normalising to
    naive-UTC here keeps one code path for both.
    """
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    raise TypeError(f"expected date or datetime, got {type(value).__name__}")


def _rows_since(site_id: str, start: datetime) -> list:
    """Raw (connector, run_at, cost, units) tuples for a site at/after `start`.

    Returns [] on any failure — a cost panel must never take a page down.
    """
    try:
        with get_session() as session:
            # Self-provision like every other 2026-07 table: a database created before
            # connector_costs existed must not raise "no such table" on first read.
            ensure_tables(session, ConnectorCost)
            return list(session.execute(
                select(
                    ConnectorCost.connector,
                    ConnectorCost.run_at,
                    ConnectorCost.cost,
                    ConnectorCost.units,
                )
                .where(ConnectorCost.site_id == (site_id or ""))
                .where(ConnectorCost.run_at >= start)
                .order_by(ConnectorCost.run_at)
            ).all())
    except Exception as exc:
        logger.error(f"cost_service: could not read connector_costs: {exc}", exc_info=True)
        return []


def cost_last_90_days(site_id: str, days: int = DEFAULT_WINDOW_DAYS) -> dict:
    """Total spend and a per-connector breakdown for the trailing `days` window.

    Shape:
        {
          "total": 12.3456,          # float, USD — 0.0 when nothing recorded
          "currency": "USD",
          "days": 90,
          "start": "2026-04-28",     # ISO; the window's inclusive lower bound
          "end": "2026-07-27",
          "runs": 42,                # spend events counted
          "by_connector": [          # descending by cost; [] when nothing recorded
            {"connector": "dataforseo_serp", "cost": 8.4, "runs": 14,
             "units": 3500, "cost_per_unit": 0.0024},
            ...
          ],
        }

    `units` is whatever that connector meters (keywords looked up, pages crawled, SERP
    queries posted). `cost_per_unit` is None — not 0 — when a connector recorded no units,
    because "we don't know the denominator" and "it's free" are different facts.
    """
    days = max(1, int(days or DEFAULT_WINDOW_DAYS))
    end = datetime.now(timezone.utc).replace(tzinfo=None)
    start = end - timedelta(days=days)

    rows = _rows_since(site_id, start)

    totals: dict[str, dict] = {}
    grand_total = 0.0
    for connector, _run_at, cost, units in rows:
        amount = float(cost or 0.0)
        grand_total += amount
        bucket = totals.setdefault(connector, {"cost": 0.0, "runs": 0, "units": 0, "had_units": False})
        bucket["cost"] += amount
        bucket["runs"] += 1
        if units is not None:
            bucket["units"] += int(units)
            bucket["had_units"] = True

    by_connector = []
    for connector, bucket in totals.items():
        unit_total = bucket["units"] if bucket["had_units"] else None
        by_connector.append({
            "connector": connector,
            "cost": round(bucket["cost"], 4),
            "runs": bucket["runs"],
            "units": unit_total,
            "cost_per_unit": (
                round(bucket["cost"] / unit_total, 6) if unit_total else None
            ),
        })
    by_connector.sort(key=lambda r: r["cost"], reverse=True)

    return {
        "total": round(grand_total, 4),
        "currency": "USD",
        "days": days,
        "start": start.date().isoformat(),
        "end": end.date().isoformat(),
        "runs": len(rows),
        "by_connector": by_connector,
    }


def cost_by_month(site_id: str, months: int = 3) -> list[dict]:
    """Spend per calendar month, oldest first, for a simple trend line.

    Always returns exactly `months` entries — a month with no recorded spend is a real
    0.0, not a gap, so the trend does not silently compress and imply activity that
    never happened. Shape per entry:

        {"month": "2026-07", "label": "Jul 2026", "cost": 4.12, "runs": 9,
         "partial": True}      # True only for the current, still-accruing month
    """
    months = max(1, int(months or 3))
    today = datetime.now(timezone.utc).replace(tzinfo=None)

    # First day of the earliest month in the window.
    year, month = today.year, today.month
    for _ in range(months - 1):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    start = datetime(year, month, 1)

    rows = _rows_since(site_id, start)

    buckets: dict[str, dict] = {}
    for _connector, run_at, cost, _units in rows:
        when = _as_datetime(run_at) if run_at is not None else None
        if when is None:
            continue
        key = f"{when.year:04d}-{when.month:02d}"
        bucket = buckets.setdefault(key, {"cost": 0.0, "runs": 0})
        bucket["cost"] += float(cost or 0.0)
        bucket["runs"] += 1

    # Walk the window forward so the caller gets a dense, ordered series.
    out: list[dict] = []
    cursor_year, cursor_month = year, month
    current_key = f"{today.year:04d}-{today.month:02d}"
    for _ in range(months):
        key = f"{cursor_year:04d}-{cursor_month:02d}"
        bucket = buckets.get(key, {"cost": 0.0, "runs": 0})
        out.append({
            "month": key,
            "label": date(cursor_year, cursor_month, 1).strftime("%b %Y"),
            "cost": round(bucket["cost"], 4),
            "runs": bucket["runs"],
            "partial": key == current_key,
        })
        cursor_month += 1
        if cursor_month == 13:
            cursor_month = 1
            cursor_year += 1

    return out


def cost_since(site_id: str, start_date) -> float:
    """Total USD spent by this site at/after `start_date`. Accepts a date or datetime.

    The primitive budget enforcement will be built on: pass the first of the billing month
    and compare against the user's configured cap. Returns 0.0 when nothing is recorded or
    the read fails — never None, so a caller can always compare it numerically.
    """
    try:
        start = _as_datetime(start_date)
    except TypeError as exc:
        logger.error(f"cost_since: {exc}")
        return 0.0

    try:
        with get_session() as session:
            ensure_tables(session, ConnectorCost)
            total = session.execute(
                select(func.sum(ConnectorCost.cost))
                .where(ConnectorCost.site_id == (site_id or ""))
                .where(ConnectorCost.run_at >= start)
            ).scalar()
    except Exception as exc:
        logger.error(f"cost_since: could not read connector_costs: {exc}", exc_info=True)
        return 0.0

    return round(float(total or 0.0), 4)
