"""
pipeline/services/aggregate_service.py — Daily/weekly/monthly rollup of seo_daily into seo_aggregates.

Why this table exists:
  - The dashboard's Daily/Weekly/Monthly selector reads from seo_aggregates
    for snappy charts. Custom date ranges still hit seo_daily directly.
  - One rebuild walks seo_daily and writes three period_type rollups:
    'daily', 'weekly', 'monthly'.

Triggered by pipeline tasks after each connector sync run.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import text as sa_text

from pipeline.db.dialect import is_postgres
from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger
from pipeline.db.writer import upsert_seo_aggregate

logger = get_logger("aggregate_service")


# Date-grouping expressions per period type, per backend. There is no portable
# SQL for "truncate to the start of the week/month", so each dialect gets its own
# literal. Both maps MUST produce the same buckets — a Monday-anchored week and a
# first-of-month — or the rollups would silently disagree between environments.
_PERIOD_EXPR_SQLITE = {
    "daily":   "date",
    "weekly":  "DATE(date, '-' || ((strftime('%w', date) + 6) % 7) || ' days')",  # Monday-anchored
    "monthly": "DATE(date, 'start of month')",
}

# Postgres DATE_TRUNC('week', ...) is already Monday-anchored, so it matches the
# SQLite expression above without an offset. The ::date casts drop the timestamp
# DATE_TRUNC returns, keeping the value the same shape the SQLite branch yields.
_PERIOD_EXPR_POSTGRES = {
    "daily":   "date",
    "weekly":  "(DATE_TRUNC('week', date))::date",
    "monthly": "(DATE_TRUNC('month', date))::date",
}

# Historical name — some callers/docs reference it; the SQLite map is the original.
_PERIOD_EXPR = _PERIOD_EXPR_SQLITE


def rebuild_seo_aggregates(site_id: str, days_back: int = 365) -> dict:
    """
    Walk seo_daily for the last `days_back` days and upsert the daily, weekly,
    monthly rollups into seo_aggregates.

    Returns a dict {period_type: rows_written}.
    """
    if not site_id:
        raise ValueError("[aggregate_service] site_id is required.")

    end = date.today()
    start = end - timedelta(days=days_back)

    results: dict = {}
    with get_session() as session:
        period_exprs = _PERIOD_EXPR_POSTGRES if is_postgres(session) else _PERIOD_EXPR_SQLITE
        for period_type, period_expr in period_exprs.items():
            rows = session.execute(
                sa_text(f"""
                    SELECT
                        {period_expr}                                AS period_start,
                        SUM(COALESCE(clicks, 0))                     AS clicks,
                        SUM(COALESCE(impressions, 0))                AS impressions,
                        CASE WHEN SUM(COALESCE(impressions, 0)) > 0
                             THEN CAST(SUM(COALESCE(clicks, 0)) AS REAL) / SUM(COALESCE(impressions, 0))
                             ELSE 0.0 END                              AS ctr,
                        CASE WHEN SUM(COALESCE(impressions, 0)) > 0
                             THEN SUM(COALESCE(avg_position, 0) * COALESCE(impressions, 0)) / SUM(COALESCE(impressions, 0))
                             ELSE 0.0 END                              AS avg_position,
                        SUM(COALESCE(sessions, 0))                   AS sessions,
                        SUM(COALESCE(pageviews, 0))                  AS pageviews,
                        SUM(COALESCE(users, 0))                      AS users,
                        SUM(COALESCE(new_users, 0))                  AS new_users,
                        AVG(COALESCE(engagement_rate, 0))            AS engagement_rate
                    FROM seo_daily
                    WHERE site_id = :sid
                      AND date BETWEEN :start AND :end
                    GROUP BY {period_expr}
                """),
                {"sid": site_id, "start": start, "end": end},
            ).fetchall()

            records = []
            for r in rows:
                period_start_raw = r[0]
                # SQLite may return string or date depending on driver; Postgres
                # returns a real date object — normalize both to date.
                if isinstance(period_start_raw, str):
                    try:
                        period_start = date.fromisoformat(period_start_raw[:10])
                    except ValueError:
                        continue
                else:
                    period_start = period_start_raw
                if not period_start:
                    continue

                period_end = _period_end(period_start, period_type)

                total_users = int(r[7] or 0)
                new_users = int(r[8] or 0)
                records.append({
                    "site_id":          site_id,
                    "period_type":      period_type,
                    "period_start":     period_start,
                    "period_end":       period_end,
                    "clicks":           int(r[1] or 0),
                    "impressions":      int(r[2] or 0),
                    "ctr":              round(float(r[3] or 0), 6),
                    "avg_position":     round(float(r[4] or 0), 2),
                    "sessions":         int(r[5] or 0),
                    "pageviews":        int(r[6] or 0),
                    "users":            total_users,
                    "new_users":        new_users,
                    "returning_users":  max(total_users - new_users, 0),
                    "engagement_rate":  round(float(r[9] or 0), 6),
                })

            written = upsert_seo_aggregate(session, records)
            results[period_type] = written
            logger.info(f"[aggregate_service] {site_id} {period_type}: {written} rows")

    return results


def _period_end(period_start: date, period_type: str) -> date:
    if period_type == "daily":
        return period_start
    if period_type == "weekly":
        return period_start + timedelta(days=6)
    # monthly
    if period_start.month == 12:
        return date(period_start.year, 12, 31)
    next_month = date(period_start.year, period_start.month + 1, 1)
    return next_month - timedelta(days=1)
