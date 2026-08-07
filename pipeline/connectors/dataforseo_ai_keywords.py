"""
pipeline/connectors/dataforseo_ai_keywords.py — AI search keyword data.

Calls DataForSEO's AI Optimization API (AI Keyword Data) to get, per tracked
keyword, the estimated frequency it's used in questions people ask AI tools
(ai_search_volume) plus a 12-month trend. A research input surfaced on the
Keywords page — NOT a daily rank tracker.

Endpoint (Live, instant — no task_post/task_get polling):
  POST /v3/ai_optimization/ai_keyword_data/keywords_search_volume/live
Response: tasks[].result[].items[] with keyword, ai_search_volume,
ai_monthly_searches[] (year, month, ai_search_volume).

Writes to: ai_keyword_data table.
Cost: per DataForSEO AI Optimization pricing; up to 1000 keywords per call.
Triggered by the Keywords page refresh / scheduled sync only (DB-first contract).
"""

import json
import os
from datetime import date
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import yesterday
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_ai_keyword_data

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
ENDPOINT = f"{DATAFORSEO_BASE}/ai_optimization/ai_keyword_data/keywords_search_volume/live"
MAX_KEYWORDS_PER_CALL = 1000


class DataForSEOAIKeywordsConnector(BaseConnector):
    name = "dataforseo_ai_keywords"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        if not self.login or not self.password:
            raise ValueError(
                "[dataforseo_ai_keywords] Missing DATAFORSEO_LOGIN or "
                "DATAFORSEO_PASSWORD in .env."
            )
        self.auth = (self.login, self.password)
        # USD DataForSEO reported for the current fetch(), summed across the
        # 1000-keyword batches and written as one row per run.
        self._run_cost = 0.0

    def _resolve_site_id(self, site_id: Optional[str]) -> str:
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return site.site_url
        return site_id or ""

    def _load_keywords(self, site_id: str = "") -> list[str]:
        """This PROJECT's tracked keywords — scoped by `site_pk`, which sync_engine stamps on
        every connector before the run. This is a metered per-keyword endpoint, so an unscoped
        list bills this project for every sibling project's keywords as well."""
        from pipeline.services.site_service import resolve_tracking_location
        from pipeline.utils.keywords import load_tracked_keywords
        site_pk = getattr(self, "site_pk", None)
        keywords = load_tracked_keywords(
            site_id, location=resolve_tracking_location(site_pk, site_id), site_pk=site_pk)
        if not keywords:
            self.logger.warning(
                "[dataforseo_ai_keywords] No keywords in keywords.txt — nothing to fetch."
            )
        return keywords

    @with_retry(max_retries=3, base_delay=5.0)
    def _call(self, keywords: list[str]) -> list[dict]:
        """Single Live call for up to MAX_KEYWORDS_PER_CALL keywords. Returns items list."""
        payload = [{
            "keywords": keywords,
            "location_name": "United States",
            "language_name": "English",
            "tag": "fusehealth_ai_kw",
        }]
        resp = requests.post(ENDPOINT, auth=self.auth, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # AI Optimization uses the same envelope: read the charge before any early return.
        self._run_cost += extract_cost(data)

        tasks = data.get("tasks") or []
        if not tasks:
            return []
        task = tasks[0]
        if task.get("status_code") != 20000:
            self.logger.warning(
                f"[dataforseo_ai_keywords] Non-success status: "
                f"{task.get('status_code')} — {task.get('status_message')}"
            )
            return []
        results = task.get("result") or []
        if not results:
            return []
        return results[0].get("items") or []

    @staticmethod
    def _prev_month_volume(monthly: list[dict]) -> Optional[int]:
        """Second-most-recent month's AI volume from the trend array (for a delta arrow)."""
        if not monthly or len(monthly) < 2:
            return None
        ordered = sorted(
            monthly,
            key=lambda m: (m.get("year") or 0, m.get("month") or 0),
        )
        val = ordered[-2].get("ai_search_volume")
        return int(val) if val is not None else None

    def _normalize(self, items: list[dict], tracking_date: date, site_id: str) -> list[dict]:
        records = []
        for item in items:
            keyword = item.get("keyword")
            if not keyword:
                continue
            monthly = item.get("ai_monthly_searches") or []
            asv = item.get("ai_search_volume")
            records.append({
                "date": tracking_date,
                "site_id": site_id,
                "keyword": keyword,
                "ai_search_volume": int(asv) if asv is not None else None,
                "prev_ai_search_volume": self._prev_month_volume(monthly),
                "search_volume": None,   # left for optional later enrichment from keyword_rankings
                "intent": None,
                "trend": json.dumps(monthly) if monthly else None,
            })
        return records

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Fetch AI search volume for all tracked keywords. Returns rows for
        ai_keyword_data. Returns [] (not an error) when keywords.txt is empty.
        """
        resolved_site_id = self._resolve_site_id(site_id)
        keywords = self._load_keywords(resolved_site_id)
        if not keywords:
            return []

        tracking_date = yesterday()
        records: list[dict] = []
        self._run_cost = 0.0
        try:
            for i in range(0, len(keywords), MAX_KEYWORDS_PER_CALL):
                batch = keywords[i:i + MAX_KEYWORDS_PER_CALL]
                items = self._call(batch)
                records.extend(self._normalize(items, tracking_date, resolved_site_id))
        finally:
            # `units` = keywords submitted — AI Keyword Data meters per keyword, and a
            # later batch failing must not lose the earlier batches already billed.
            record_cost(
                self.name, resolved_site_id, self._run_cost, units=len(keywords),
                notes="ai_optimization/ai_keyword_data/keywords_search_volume live",
            )

        self.logger.info(
            f"[dataforseo_ai_keywords] Fetched AI volume for {len(records)} keywords "
            f"({resolved_site_id!r})"
        )
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_ai_keyword_data(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = DataForSEOAIKeywordsConnector()
    print("Loaded. To run for the active site: connector.sync()")
