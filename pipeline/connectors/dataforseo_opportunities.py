"""
pipeline/connectors/dataforseo_opportunities.py — DataForSEO Labs Automated Keyword Opportunities connector.

Finds high-potential keywords by analyzing the top competitors (already stored in the database)
and fetching their ranked keywords using the DataForSEO Labs `ranked_keywords/live` endpoint.
It filters for keywords with decent search volume and saves them to the keyword_rankings table.
"""

import os
from datetime import date
from typing import Optional

import requests
from dotenv import load_dotenv
from sqlalchemy import select

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.retry import with_retry
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_keyword_rankings
from pipeline.db.schema import CompetitorDomain

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
ENDPOINT = f"{DATAFORSEO_BASE}/dataforseo_labs/google/ranked_keywords/live"


class DataForSEOOpportunitiesConnector(BaseConnector):
    name = "dataforseo_opportunities"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        if not self.login or not self.password:
            raise ValueError(
                "[dataforseo_opportunities] Missing DATAFORSEO_LOGIN or DATAFORSEO_PASSWORD in .env."
            )
        self.auth = (self.login, self.password)
        # USD DataForSEO reported for the current fetch() — one ranked_keywords call per
        # top competitor, summed into a single row per run.
        self._run_cost = 0.0

    def _resolve(self, site_id: Optional[str]) -> tuple[str, str]:
        """Return (site_url_for_db, bare_target_domain)."""
        from pipeline.services.site_service import get_site

        def _strip(domain: str) -> str:
            return (domain or "").replace("https://", "").replace("http://", "").replace("sc-domain:", "").rstrip("/")

        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return (site.site_url, _strip(site.dataforseo_target_domain or site.site_url))

        fallback_target = _strip(os.getenv("DATAFORSEO_TARGET_DOMAIN", "") or os.getenv("GSC_SITE_URL", ""))
        return (site_id or "", fallback_target)

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_competitor_keywords(self, target: str, limit: int = 50) -> list[dict]:
        """Single live call to DataForSEO Labs. Returns the raw items list."""
        payload = [{
            "target": target,
            "location_name": "United States",
            "language_name": "English",
            "limit": limit
        }]
        resp = requests.post(ENDPOINT, auth=self.auth, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        # Read the charge before any early return — a non-20000 task is still billable.
        self._run_cost += extract_cost(data)

        tasks = data.get("tasks") or []
        if not tasks:
            return []
        task = tasks[0]
        if task.get("status_code") != 20000:
            self.logger.warning(
                f"[dataforseo_opportunities] Non-success status: "
                f"{task.get('status_code')} — {task.get('status_message')}"
            )
            return []
        results = task.get("result") or []
        if not results:
            return []
        return results[0].get("items") or []

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Fetch keyword opportunities based on top competitors for the site.
        Returns rows shaped for the keyword_rankings table.
        """
        resolved_site_id, target = self._resolve(site_id)
        if not target:
            raise ValueError("[dataforseo_opportunities] No target domain configured.")

        # 1. Get Top 3 Competitors from the database
        top_competitors = []
        with get_session() as session:
            rows = session.execute(
                select(CompetitorDomain.competitor_domain)
                .where(CompetitorDomain.site_id == resolved_site_id)
                .order_by(CompetitorDomain.intersections.desc())
                .limit(3)
            ).scalars().all()
            top_competitors = list(rows)

        if not top_competitors:
            self.logger.warning(f"[dataforseo_opportunities] No competitors found for {target}. Run `dataforseo_labs_competitors` first.")
            return []

        self.logger.info(f"[dataforseo_opportunities] Fetching keyword opportunities based on competitors: {', '.join(top_competitors)}")

        # 2. Fetch keywords for each competitor
        records = []
        seen_keywords = set()
        self._run_cost = 0.0
        keyword_rows_returned = 0

        for comp in top_competitors:
            items = self._fetch_competitor_keywords(comp, limit=30)
            keyword_rows_returned += len(items)
            for item in items:
                keyword_data = item.get("keyword_data") or {}
                keyword = keyword_data.get("keyword")
                if not keyword or keyword in seen_keywords:
                    continue

                seen_keywords.add(keyword)
                keyword_info = keyword_data.get("keyword_info") or {}
                intent = None

                # Try to parse intent if available
                search_intent_info = keyword_data.get("search_intent_info")
                if search_intent_info and getattr(search_intent_info, "get", None):
                    main_intent = search_intent_info.get("main_intent")
                    if main_intent:
                        intent = main_intent.capitalize()

                records.append({
                    "date": date.today(),
                    "site_id": resolved_site_id,
                    "keyword": keyword,
                    "position": None,
                    "url": None,
                    "clicks": 0,
                    "impressions": 0,
                    "ctr": 0.0,
                    "search_volume": keyword_info.get("search_volume") or 0,
                    "keyword_difficulty": keyword_info.get("keyword_difficulty") or 0,
                    "cpc": keyword_info.get("cpc") or 0.0,
                    "intent": intent,
                })

        # One row per run, summing the ranked_keywords call made per competitor.
        # `units` = keyword rows returned across those calls, which is what Labs
        # ranked_keywords meters (not the number of competitors queried).
        record_cost(
            self.name, resolved_site_id, self._run_cost, units=keyword_rows_returned,
            notes=f"labs/ranked_keywords live x{len(top_competitors)} competitors",
        )

        self.logger.info(
            f"[dataforseo_opportunities] Discovered {len(records)} keyword opportunities for {target}"
        )
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_keyword_rankings(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = DataForSEOOpportunitiesConnector()
    print("Loaded. To run for the active site: connector.sync()")
