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
        """Return the GSC site URL to query, from the Site row or .env fallback. Auto-matched
        against the account's property list (see gsc_property.py) so a bare-domain value
        can't 403 as an http:// URL-prefix property."""
        from pipeline.connectors.gsc_property import resolve_gsc_property
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            stored = (site.gsc_property or site.site_url) if site else None
            key = site.site_url if site else None
        if stored:
            return resolve_gsc_property(key, stored)
        return self._default_site_url or ""

    def _get_last_synced_date(self, site_url: str):
        """Most recent date **this connector** has written keyword data for, or None.

        `impressions > 0` is load-bearing, for the same reason as gsc._get_last_synced_date:
        `keyword_rankings` is a shared table where the DataForSEO connectors write position
        rows stamped `date = yesterday()` with clicks/impressions at 0. A bare `max(date)`
        therefore reads the DataForSEO cursor, and because gsc_safe_range ends *today − 3*,
        fetch() computes `new_start > new_end` and returns [] on every run once any DataForSEO
        keyword sync has happened — GSC clicks/impressions/CTR enrichment silently never
        refreshes again. A GSC Search Analytics row always has impressions >= 1, so the
        predicate selects exactly this connector's own rows.
        """
        with get_session() as session:
            try:
                result = session.execute(
                    select(func.max(KeywordRanking.date)).where(
                        KeywordRanking.site_id == site_url,
                        KeywordRanking.impressions > 0,
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
        # Query the resolved GSC property; STORE under the canonical Site.site_url key the
        # app reads by (they differ when gsc_property is the sc-domain: form — see gsc.py).
        canonical = site_id or site_url

        start_str, end_str = gsc_safe_range(days)

        # Incremental: only fetch new dates for this site
        last_date = self._get_last_synced_date(canonical)
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
        records = self._normalize(raw_rows, canonical)
        self.logger.info(f"[gsc_keywords] {len(records)} keyword-date records for {site_url} (from {len(raw_rows)} raw rows)")
        return records

    def _resolve_location(self, site_id: str) -> str:
        """This PROJECT's tracking location — the same value the SERP connectors stamp.

        Search Console data is not market-specific (it is whatever the property recorded), but
        it shares `keyword_rankings` with the per-market SERP capture, and that table is keyed
        by location. Writing GSC rows under a different location than the project's own would
        put its clicks and impressions in rows the project never reads — the columns would
        simply stay empty. Stamping the project's location merges them into the same rows the
        SERP capture writes, which is what the Position Tracking grid expects.
        """
        from pipeline.services.site_service import resolve_tracking_location
        return resolve_tracking_location(getattr(self, "site_pk", None), site_id)

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Upsert via the shared writer — see `pipeline/db/writer.upsert_keyword_rankings`.

        This used to build its own `insert(...).on_conflict_do_update(...)` with
        `index_elements=["date", "site_id", "keyword"]`. That duplicated the writer (against
        the project's "analytics writes go through a writer upsert" rule) and it broke outright
        the moment `location` joined the unique key on 2026-08-06: Postgres answered
        `InvalidColumnReference: there is no unique or exclusion constraint matching the ON
        CONFLICT specification`, so every Position Tracking refresh reported "GSC queries
        refresh failed" after writing ~2200 rows.

        The shared writer also updates with `coalesce(excluded, existing)`, so a NULL coming
        from GSC (search_volume, keyword_difficulty, cpc — GSC has none of them) leaves
        DataForSEO's stored values alone rather than blanking them. That is what the old
        hand-written `set_` was trying to achieve by listing columns explicitly.
        """
        if not records:
            return 0

        from pipeline.db.writer import upsert_keyword_rankings

        location = self._resolve_location(site_id or "")
        clean_records = []
        for r in records:
            clean_records.append({
                "date": r["date"],
                "site_id": r.get("site_id") or site_id or "",
                "keyword": r["keyword"],
                "location": location,
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
                # Search Console only returns a query row because the page was actually served
                # for it, so this IS a rank observation — see KeywordRanking.rank_checked_at.
                # Stamped with the row's own date, not today's: it records when the position
                # was true, which is what the reader of the column needs.
                "rank_checked_at": r["date"],
            })

        return upsert_keyword_rankings(session, clean_records, site_id=site_id)


if __name__ == "__main__":
    import json
    connector = GSCKeywordsConnector()
    records = connector.fetch(days=90)
    print(f"Fetched {len(records)} keyword records from GSC")
    if records:
        print(f"Sample: {records[0]}")
