"""
pipeline/connectors/gsc_keywords.py — GSC Query-Level Keyword Rankings Connector.

Fetches REAL keyword data from Google Search Console (site set via GSC_SITE_URL in .env).
Uses the 'query' dimension to get every search term the site ranks for,
along with actual position, clicks, impressions, and CTR.

This replaces the need for DataForSEO SERP tracking for basic keyword audits.
Writes to: keyword_rankings table.

What GSC gives us (that DataForSEO doesn't):
- REAL click and impression data (not estimated)
- ACTUAL average position in Google search results
- Real CTR for each keyword

What GSC does NOT give us (would need DataForSEO):
- Search volume (monthly searches)
- Keyword difficulty
- Competitor rankings
"""

import os
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build

from pipeline.connectors.base import BaseConnector
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import gsc_safe_range, iso
from pipeline.utils.db_connection import get_session
from pipeline.db.schema import KeywordRanking
from sqlalchemy import select, func

load_dotenv()


class GSCKeywordsConnector(BaseConnector):
    name = "gsc_keywords"

    def __init__(self):
        super().__init__()
        # Defaults from .env — used only if no Site row exists.
        self._default_site_url = os.getenv("GSC_SITE_URL")

    def _resolve_site(self, site_id: Optional[str]) -> str:
        """Return the GSC site URL to query, from the Site row or .env fallback."""
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return site.gsc_property or site.site_url
        return self._default_site_url or ""

    def _get_last_synced_date(self, site_url: str):
        """Check the DB for the most recent date in keyword_rankings for this site."""
        with get_session() as session:
            try:
                result = session.execute(
                    select(func.max(KeywordRanking.date)).where(
                        KeywordRanking.site_id == site_url,
                    )
                ).scalar()
            except Exception:
                result = None
        return result

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_queries(self, site_url: str, start_str: str, end_str: str) -> list[dict]:
        """
        Fetch query-level data from GSC.
        Dimensions: date + query → gives keyword + position per day.
        Also fetch query + page to know which URL ranks for each keyword.
        """
        creds = get_google_credentials()
        service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

        all_rows = []
        start_row = 0
        row_limit = 25000

        while True:
            body = {
                "startDate": start_str,
                "endDate": end_str,
                "dimensions": ["date", "query", "page"],
                "rowLimit": row_limit,
                "startRow": start_row,
            }

            self.logger.info(
                f"[gsc_keywords] Fetching rows {start_row}-{start_row + row_limit} "
                f"for {start_str} to {end_str}"
            )

            response = (
                service.searchanalytics()
                .query(siteUrl=site_url, body=body)
                .execute()
            )

            rows = response.get("rows", [])
            all_rows.extend(rows)

            if len(rows) < row_limit:
                break
            start_row += row_limit

        return all_rows

    def _normalize(self, raw_rows: list[dict], site_url: str) -> list[dict]:
        """
        Convert GSC query response to keyword_rankings format.

        For each date+query combination, we keep the best-performing page URL.
        """
        # Group by date+query, keep the page with most clicks
        best_by_date_query = {}
        for row in raw_rows:
            keys = row.get("keys", [])
            if len(keys) < 3:
                continue

            row_date_str = keys[0]
            query = keys[1]
            page_url = keys[2]
            clicks = int(row.get("clicks", 0))
            impressions = int(row.get("impressions", 0))
            position = float(row.get("position", 0.0))
            ctr = float(row.get("ctr", 0.0))

            key = (row_date_str, query)
            existing = best_by_date_query.get(key)

            if existing is None or clicks > existing["clicks"]:
                best_by_date_query[key] = {
                    "date": date.fromisoformat(row_date_str),
                    "site_id": site_url,
                    "keyword": query,
                    "position": round(position),
                    "url": page_url,
                    "search_volume": None,  # GSC doesn't provide this
                    "keyword_difficulty": None,  # GSC doesn't provide this
                    "cpc": None,  # GSC doesn't provide this
                    "intent": None,
                    "trend": None,
                    # Store extra GSC data in a way we can use
                    "clicks": clicks,
                    "impressions": impressions,
                    "ctr": ctr,
                }

        records = list(best_by_date_query.values())
        return records

    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """Fetch real keyword query data from GSC for the given site."""
        site_url = self._resolve_site(site_id)
        if not site_url:
            raise ValueError("[gsc_keywords] No GSC site configured for this Site row or .env.")

        start_str, end_str = gsc_safe_range(days)

        # Incremental: only fetch new dates for this site
        last_date = self._get_last_synced_date(site_url)
        if last_date:
            new_start = last_date + timedelta(days=1)
            new_end = date.fromisoformat(end_str)
            if new_start > new_end:
                self.logger.info(f"[gsc_keywords] No new dates for {site_url}. Last synced: {last_date}")
                return []
            start_str = iso(new_start)
            self.logger.info(f"[gsc_keywords] Incremental [{site_url}]: {start_str} to {end_str}")
        else:
            self.logger.info(f"[gsc_keywords] Full fetch [{site_url}]: {start_str} to {end_str}")

        raw_rows = self._fetch_queries(site_url, start_str, end_str)
        records = self._normalize(raw_rows, site_url)
        self.logger.info(f"[gsc_keywords] {len(records)} keyword-date records for {site_url} (from {len(raw_rows)} raw rows)")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Upsert keyword records in batches to avoid SQLite parameter limits.
        SQLite max ~999 vars; each record has ~10 cols → batch size 80.
        """
        if not records:
            return 0

        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        # Clean records: keep all schema fields including GSC engagement metrics
        clean_records = []
        for r in records:
            clean_records.append({
                "date": r["date"],
                "site_id": r.get("site_id") or site_id or "",
                "keyword": r["keyword"],
                "position": r["position"],
                "url": r["url"],
                # GSC real engagement — these tell us which keywords actually drive traffic
                "clicks": r.get("clicks", 0) or 0,
                "impressions": r.get("impressions", 0) or 0,
                "ctr": r.get("ctr", 0.0) or 0.0,
                # DataForSEO market data (None until DataForSEO is connected)
                "search_volume": r.get("search_volume"),
                "keyword_difficulty": r.get("keyword_difficulty"),
                "cpc": r.get("cpc"),
                "intent": r.get("intent"),
                "trend": r.get("trend"),
            })

        # Batch insert to avoid SQLite "too many SQL variables" error
        BATCH_SIZE = 80
        total_written = 0
        for i in range(0, len(clean_records), BATCH_SIZE):
            batch = clean_records[i:i + BATCH_SIZE]
            stmt = sqlite_insert(KeywordRanking).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["date", "site_id", "keyword"],
                set_={
                    "position": stmt.excluded.position,
                    "url": stmt.excluded.url,
                    "clicks": stmt.excluded.clicks,
                    "impressions": stmt.excluded.impressions,
                    "ctr": stmt.excluded.ctr,
                },
            )
            session.execute(stmt)
            total_written += len(batch)

        return total_written


if __name__ == "__main__":
    import json
    connector = GSCKeywordsConnector()
    records = connector.fetch(days=90)
    print(f"Fetched {len(records)} keyword records from GSC")
    if records:
        print(f"Sample: {records[0]}")
