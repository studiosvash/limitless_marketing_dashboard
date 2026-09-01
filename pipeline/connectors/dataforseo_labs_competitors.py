"""
pipeline/connectors/dataforseo_labs_competitors.py — DataForSEO Labs competitors_domain connector.

Auto-discovers organic search competitors for the focus site via the
/dataforseo_labs/google/competitors_domain/live endpoint. Powers the SEMrush-style
Positioning page.

Cost: ~$0.01 per call (live endpoint is fine here — single call per site, weekly cadence).
Returns up to `limit` competing domains ordered by `intersections` (count of shared keywords).
Writes to: competitor_domains table.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.retry import with_retry
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_competitor_domains

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
ENDPOINT = f"{DATAFORSEO_BASE}/dataforseo_labs/google/competitors_domain/live"

# How long a domain's competitor list stays good before it is bought again. The list is
# per DOMAIN (`competitor_domains` is keyed site_id + competitor_domain) but this connector
# runs inside every city project's positions run, so 18 premierstaff.com projects re-bought
# and overwrote the same 25 rows every week. Weekly per domain matches the positions cadence.
COMPETITORS_FRESH_DAYS = 7

# DataForSEO Labs returns keyword COUNTS per SERP position band (not a position).
# Map each band to a representative midpoint so we can derive a weighted avg position.
_POSITION_BANDS = {
    "pos_1": 1.0,
    "pos_2_3": 2.5,
    "pos_4_10": 7.0,
    "pos_11_20": 15.5,
    "pos_21_30": 25.5,
    "pos_31_40": 35.5,
    "pos_41_50": 45.5,
    "pos_51_100": 75.5,
}


def avg_position_from_bands(organic: dict) -> Optional[float]:
    """
    Estimate a competitor's average organic position from DataForSEO Labs
    position-band keyword counts (metrics.organic.pos_*).

    Returns a weighted average using band midpoints, or None when no band
    data is present (so we never store a fake/zero position).
    """
    if not isinstance(organic, dict):
        return None
    weighted_sum = 0.0
    total = 0.0
    for band, midpoint in _POSITION_BANDS.items():
        count = organic.get(band)
        if not count:
            continue
        try:
            count = float(count)
        except (TypeError, ValueError):
            continue
        weighted_sum += count * midpoint
        total += count
    if total <= 0:
        return None
    return round(weighted_sum / total, 1)


class DataForSEOLabsCompetitorsConnector(BaseConnector):
    name = "dataforseo_labs_competitors"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        if not self.login or not self.password:
            raise ValueError(
                "[dataforseo_labs_competitors] Missing DATAFORSEO_LOGIN or DATAFORSEO_PASSWORD in .env."
            )
        self.auth = (self.login, self.password)
        # USD DataForSEO reported for the current fetch() (one live call per run).
        self._run_cost = 0.0

    @staticmethod
    def _strip(domain: str) -> str:
        return (
            (domain or "")
            .replace("https://", "")
            .replace("http://", "")
            .replace("sc-domain:", "")
            .rstrip("/")
        )

    def _resolve(self, site_id: Optional[str]) -> tuple[str, str]:
        """Return (site_url_for_db, bare_target_domain)."""
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return (site.site_url, self._strip(site.dataforseo_target_domain or site.site_url))
        # Fallback to .env
        fallback_target = self._strip(
            os.getenv("DATAFORSEO_TARGET_DOMAIN", "") or os.getenv("GSC_SITE_URL", "")
        )
        return (site_id or "", fallback_target)

    @with_retry(max_retries=3, base_delay=5.0)
    def _call(self, target: str, limit: int) -> list[dict]:
        """Single live call to DataForSEO Labs. Returns the raw items list."""
        payload = [{
            "target": target,
            "location_name": "United States",
            "language_name": "English",
            "limit": limit,
            # Useful filter: drop competitors that share only 1 keyword (noise)
            "filters": [["intersections", ">", 1]],
        }]
        resp = requests.post(ENDPOINT, auth=self.auth, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        # Labs bills the live call itself — the charge is on this envelope. Read it before
        # any status/empty-result early return, because a non-20000 task is still billable.
        self._run_cost += extract_cost(data)

        tasks = data.get("tasks") or []
        if not tasks:
            return []
        task = tasks[0]
        if task.get("status_code") != 20000:
            self.logger.warning(
                f"[dataforseo_labs_competitors] Non-success status: "
                f"{task.get('status_code')} — {task.get('status_message')}"
            )
            return []
        results = task.get("result") or []
        if not results:
            return []
        return results[0].get("items") or []

    def fetch(self, site_id: Optional[str] = None, limit: int = 25) -> list[dict]:
        """
        Fetch up to `limit` competitor domains for the site's target domain.
        Returns rows shaped for the competitor_domains table.
        """
        resolved_site_id, target = self._resolve(site_id)
        if not target:
            raise ValueError(
                "[dataforseo_labs_competitors] No DataForSEO target domain "
                "configured for this site (Settings → Manage Sites)."
            )

        recent = self._recent_rows(resolved_site_id)
        if recent:
            # Bought within COMPETITORS_FRESH_DAYS — by this project or a sibling on the same
            # domain. Returned as-is so the run still reports the rows it has, with no API
            # call and no spend event (record_cost skips a zero).
            self.logger.info(
                f"[dataforseo_labs_competitors] {len(recent)} competitor domains for {target} "
                f"fetched within {COMPETITORS_FRESH_DAYS} days — reused, nothing fetched"
            )
            return recent

        self.logger.info(
            f"[dataforseo_labs_competitors] Fetching top {limit} competitors for {target}"
        )
        self._run_cost = 0.0
        items = self._call(target, limit)
        # `units` = competitor domains returned. Labs competitors_domain meters per
        # returned row, so cost/units is the real per-competitor price. Placed after the
        # call rather than in a `finally`: if _call raised, no response was parsed, so
        # _run_cost is 0 and there is genuinely nothing to book.
        record_cost(
            self.name, resolved_site_id, self._run_cost, units=len(items),
            notes=f"labs/competitors_domain live for {target}",
        )

        records = []
        for item in items:
            competitor_domain = item.get("domain")
            if not competitor_domain:
                continue

            # DataForSEO Labs returns nested metrics under metrics.organic.*
            organic = (item.get("metrics") or {}).get("organic", {}) or {}
            full_metrics = item.get("full_domain_metrics") or {}
            full_org = (full_metrics.get("organic") or {}) if isinstance(full_metrics, dict) else {}

            records.append({
                "site_id": resolved_site_id,
                "competitor_domain": competitor_domain,
                "intersections": int(item.get("intersections") or 0),
                "full_domain_metrics_organic_count": int(full_org.get("count") or 0),
                # Weighted avg organic position estimated from the position-band counts.
                "avg_position": avg_position_from_bands(organic),
                "median_position": None,
                "etv": float(organic.get("etv") or 0.0),
                "last_fetched": datetime.now(timezone.utc),
            })

        self.logger.info(
            f"[dataforseo_labs_competitors] Discovered {len(records)} competitor domains for {target}"
        )
        return records

    def _recent_rows(self, site_id: str) -> list[dict]:
        """This domain's stored competitor list if its newest row is within
        COMPETITORS_FRESH_DAYS, else []. Never raises — a lookup failure means "fetch"."""
        try:
            from sqlalchemy import select

            from pipeline.db.schema import CompetitorDomain
            from pipeline.utils.site_ids import resolve_site_ids

            with get_session() as session:
                rows = session.execute(
                    select(CompetitorDomain)
                    .where(CompetitorDomain.site_id.in_(resolve_site_ids(site_id)))
                ).scalars().all()
                session.expunge_all()
        except Exception as exc:
            self.logger.warning(f"[dataforseo_labs_competitors] freshness lookup failed — fetching: {exc}")
            return []
        if not rows:
            return []

        def _utc_naive(value):
            if value is None:
                return None
            return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

        stamps = [_utc_naive(r.last_fetched) for r in rows if r.last_fetched is not None]
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=COMPETITORS_FRESH_DAYS)
        if not stamps or max(stamps) < cutoff:
            return []
        return [{
            "site_id": r.site_id,
            "competitor_domain": r.competitor_domain,
            "intersections": r.intersections,
            "full_domain_metrics_organic_count": r.full_domain_metrics_organic_count,
            "avg_position": r.avg_position,
            "median_position": r.median_position,
            "etv": r.etv,
            "last_fetched": r.last_fetched,
        } for r in rows]

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_competitor_domains(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = DataForSEOLabsCompetitorsConnector()
    print(f"Loaded. To run for the active site: connector.sync()")
