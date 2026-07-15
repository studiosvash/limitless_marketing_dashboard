"""
pipeline/connectors/gsc.py — Google Search Console connector.

Fetches: daily clicks, impressions, CTR, avg_position per site.
Writes to: seo_daily table.

Rate limit: 50,000 page-keyword pairs/day.
Strategy: Fetch only data for dates NOT already in SQLite (append-only).
Auth: OAuth2 via pipeline/utils/auth.py — auto-refreshes every hour.

GSC has a 3-day data delay. We always fetch D-3 to avoid empty responses.
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
from pipeline.db.writer import upsert_seo_daily
from pipeline.db.schema import SEODaily
from sqlalchemy import select, func

load_dotenv()


class GSCConnector(BaseConnector):
    name = "gsc"

    def __init__(self):
        super().__init__()
        # site_url is now resolved per-call from the Site row (Phase 2).
        # We still keep the .env value as a last-resort fallback so this
        # class can be instantiated even when no Site row exists yet.
        self.site_url = os.getenv("GSC_SITE_URL")

    def _resolve_site(self, site_id: Optional[str]) -> str:
        """Return the GSC site URL to query — prefers Site.gsc_property, falls back to .env.
        The stored value is auto-matched against the account's real property list (and the
        Site row repaired) because add_site defaults it to a bare domain, which the GSC API
        reads as the http:// URL-prefix property and 403s — see gsc_property.py."""
        from pipeline.connectors.gsc_property import resolve_gsc_property
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            stored = (site.gsc_property or site.site_url) if site else None
            key = site.site_url if site else None
        if stored:
            return resolve_gsc_property(key, stored)
        return self.site_url or ""

    def _get_last_synced_date(self, site_url: str) -> Optional[date]:
        """
        Check the SQLite DB for the most recent date in seo_daily for the given site.
        """
        with get_session() as session:
            try:
                result = session.execute(
                    select(func.max(SEODaily.date)).where(
                        SEODaily.site_id == site_url,
                    )
                ).scalar()
            except Exception:
                result = None
        return result

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_date_range(self, site_url: str, start_str: str, end_str: str) -> list[dict]:
        """
        Fetch GSC data for a specific date range from a specific site.
        Makes paginated requests (25,000 rows per call, max 2 pages for most sites).
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
                "dimensions": ["date", "country", "device", "page"],
                "rowLimit": row_limit,
                "startRow": start_row,
            }

            self.logger.debug(
                f"[gsc] Fetching rows {start_row}–{start_row + row_limit} "
                f"for {start_str} → {end_str} on {site_url}"
            )

            response = (
                service.searchanalytics()
                .query(siteUrl=site_url, body=body)
                .execute()
            )

            rows = response.get("rows", [])
            all_rows.extend(rows)

            # Stop if fewer rows returned than requested (last page)
            if len(rows) < row_limit:
                break

            start_row += row_limit

        return all_rows

    def _normalize(self, raw_rows: list[dict], site_url: str) -> list[dict]:
        """
        Convert GSC API response rows to seo_daily table format.
        """
        records = []
        for row in raw_rows:
            keys = row.get("keys", [])
            if len(keys) < 4:
                continue

            row_date_str = keys[0]
            country_iso = keys[1].upper()  # ISO 3166-1 alpha-3 code (e.g. USA)
            device = keys[2].lower()
            landing_page = keys[3]

            if not row_date_str:
                continue

            records.append({
                "date":         date.fromisoformat(row_date_str),
                "site_id":      site_url,
                "country":      country_iso,
                "device":       device,
                "landing_page": landing_page,
                "clicks":       int(row.get("clicks", 0)),
                "impressions":  int(row.get("impressions", 0)),
                "ctr":          float(row.get("ctr", 0.0)),
                "avg_position": float(row.get("position", 0.0)),

                # GA4 fields - defaulted so SQLAlchemy compile operates clean
                "sessions":     0,
                "pageviews":    0,
                "bounce_rate":  0.0,
                "conversions":  0,
            })

        return records

    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """
        Fetch GSC data. Skips dates already stored in SQLite (append-only strategy).

        Args:
            site_id: The Site.site_url to fetch for. None falls back to first active site.
            days: Max number of days to fetch on first run. Default: 90.

        Returns:
            List of normalized dicts for seo_daily table.
        """
        site_url = self._resolve_site(site_id)
        if not site_url:
            raise ValueError(
                "[gsc] No site configured. Add a Site row in Settings → Manage Sites "
                "or set GSC_SITE_URL in .env."
            )

        start_str, end_str = gsc_safe_range(days)

        # Optimize: only fetch new dates if we already have data
        last_date = self._get_last_synced_date(site_url)
        if last_date:
            new_start = last_date + timedelta(days=1)
            new_end = date.fromisoformat(end_str)

            if new_start > new_end:
                self.logger.info(f"[gsc] No new dates to fetch for {site_url}. Last synced: {last_date}")
                return []

            start_str = iso(new_start)
            self.logger.info(f"[gsc] Incremental fetch [{site_url}]: {start_str} → {end_str}")
        else:
            self.logger.info(f"[gsc] Full historical fetch [{site_url}]: {start_str} → {end_str}")

        raw_rows = self._fetch_date_range(site_url, start_str, end_str)
        records = self._normalize(raw_rows, site_url)

        self.logger.info(f"[gsc] Fetched {len(records)} rows for {site_url}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_seo_daily(session, records, site_id=site_id)


if __name__ == "__main__":
    """
    Quick test: python pipeline/connectors/gsc.py
    Prints how many records were fetched without writing to DB.
    """
    import json
    connector = GSCConnector()
    records = connector.fetch(days=30)
    print(f"Fetched {len(records)} records from GSC")
    if records:
        print("Sample record:")
        print(json.dumps(str(records[0]), indent=2))
