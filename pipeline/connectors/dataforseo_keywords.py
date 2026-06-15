"""
pipeline/connectors/dataforseo_keywords.py — DataForSEO Keywords Data connector.

Fetches: search volume, keyword difficulty, CPC for tracked keywords.
Writes to: keyword_rankings table (enriches existing position records).

Rate limit: 12 req/min for Google Ads live endpoint.
Strategy: Batch up to 1,000 keywords per request (live endpoint is fine for metadata).
Google Trends: Always use Standard method — never Live (shared 250 req/min global limit).
"""

import os
import time
from datetime import date
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import yesterday
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_keyword_rankings

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


class DataForSEOKeywordsConnector(BaseConnector):
    name = "dataforseo_keywords"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.auth = (self.login, self.password)

    def _resolve_site_id(self, site_id: Optional[str]) -> str:
        """Pick the right site_id to tag records with."""
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return site.site_url
        return site_id or os.getenv("GSC_SITE_URL", "")

    def _load_keywords(self) -> list[str]:
        """Load tracked keywords from keywords.txt (skips comments/blanks)."""
        from pipeline.utils.keywords import load_tracked_keywords
        return load_tracked_keywords()

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_search_volume(self, keywords: list[str]) -> list[dict]:
        """
        Fetch search volume + CPC for a batch of keywords.
        Max 1,000 keywords per request. Rate limit: 12 req/min.
        """
        payload = [{
            "keywords": keywords[:1000],
            "location_name": "United States",
            "language_name": "English",
        }]

        resp = requests.post(
            f"{DATAFORSEO_BASE}/keywords_data/google_ads/search_volume/live",
            auth=self.auth,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("tasks", [{}])[0].get("result", [])

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_keyword_difficulty(self, keywords: list[str]) -> dict[str, float]:
        """
        Fetch keyword difficulty (0-100) for a batch via the DataForSEO Labs
        bulk_keyword_difficulty endpoint. Returns {keyword_lower: difficulty}.
        Failures degrade gracefully to an empty map (KD stays None).
        """
        payload = [{
            "keywords": [k.lower() for k in keywords[:1000]],
            "location_name": "United States",
            "language_name": "English",
        }]
        try:
            resp = requests.post(
                f"{DATAFORSEO_BASE}/dataforseo_labs/google/bulk_keyword_difficulty/live",
                auth=self.auth,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json().get("tasks", [{}])[0].get("result", []) or []
        except Exception as exc:
            self.logger.warning(f"[dataforseo_keywords] Keyword-difficulty fetch failed: {exc}")
            return {}

        # Shape: result[].items[] = {keyword, keyword_difficulty}
        kd_map: dict[str, float] = {}
        for block in result:
            for item in (block.get("items") or []):
                kw = (item.get("keyword") or "").lower()
                kd = item.get("keyword_difficulty")
                if kw and kd is not None:
                    kd_map[kw] = float(kd)
        return kd_map

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Fetch keyword metadata (volume, KD, CPC) for all tracked keywords.
        Enriches the keyword_rankings table — site-scoped via site_id tag.
        """
        if not self.login or not self.password:
            raise ValueError("[dataforseo_keywords] Missing DATAFORSEO_LOGIN or DATAFORSEO_PASSWORD in .env.")
        resolved_site_id = self._resolve_site_id(site_id)

        keywords = self._load_keywords()
        if not keywords:
            self.logger.warning("[dataforseo_keywords] No keywords found.")
            return []

        self.logger.info(f"[dataforseo_keywords] Fetching metadata for {len(keywords)} keywords (site: {resolved_site_id})")
        tracking_date = yesterday()
        records = []

        # Process in batches of 1,000 (API limit)
        batch_size = 1000
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            try:
                results = self._fetch_search_volume(batch)
                # Keyword difficulty comes from a separate Labs endpoint; merge by keyword.
                kd_map = self._fetch_keyword_difficulty(batch)
                for item in results:
                    kw = item.get("keyword", "")
                    records.append({
                        "date": tracking_date,
                        "site_id": resolved_site_id,
                        "keyword": kw,
                        "position": None,       # Set by SERP connector
                        "url": None,
                        "search_volume": item.get("search_volume"),
                        "keyword_difficulty": kd_map.get((kw or "").lower()),
                        "cpc": item.get("cpc"),
                    })
            except Exception as exc:
                self.logger.warning(f"[dataforseo_keywords] Batch {i//batch_size + 1} failed: {exc}")

            # Rate limit: 12 req/min = 5s between requests
            if i + batch_size < len(keywords):
                time.sleep(5)

        self.logger.info(f"[dataforseo_keywords] Fetched metadata for {len(records)} keywords")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """
        Upsert keyword metadata. Only updates search_volume and cpc
        so we don't overwrite positions set by the SERP connector.
        """
        if not records:
            return 0

        for r in records:
            r.setdefault("site_id", site_id or "")

        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from pipeline.db.schema import KeywordRanking

        stmt = sqlite_insert(KeywordRanking).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["date", "site_id", "keyword"],
            set_={
                "search_volume": stmt.excluded.search_volume,
                "cpc": stmt.excluded.cpc,
                "keyword_difficulty": stmt.excluded.keyword_difficulty,
            },
        )
        session.execute(stmt)
        return len(records)
