"""
pipeline/connectors/gsc_pages.py — GSC Page-Level Performance Connector.

Fetches REAL page performance data from Google Search Console.
Uses the 'page' dimension to get every indexed URL with actual
clicks, impressions, CTR, and average position.

This replaces the need for Webflow/WordPress/Sitemap connectors
for building the page inventory with real performance data.

Writes to: pages table.
"""

import os
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build

from pipeline.connectors.base import BaseConnector
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import gsc_safe_range
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_pages

load_dotenv()


class GSCPagesConnector(BaseConnector):
    name = "gsc_pages"

    def __init__(self):
        super().__init__()
        self._default_site_url = os.getenv("GSC_SITE_URL")

    def _resolve_site(self, site_id: Optional[str]) -> str:
        """Auto-matched against the account's property list (see gsc_property.py) so a
        bare-domain value can't 403 as an http:// URL-prefix property."""
        from pipeline.connectors.gsc_property import resolve_gsc_property
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            stored = (site.gsc_property or site.site_url) if site else None
            key = site.site_url if site else None
        if stored:
            return resolve_gsc_property(key, stored)
        return self._default_site_url or ""

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_pages(self, site_url: str, start_str: str, end_str: str) -> list[dict]:
        """
        Fetch page-level aggregated data from GSC.
        Dimensions: page → gives URL + total clicks/impressions for the period.
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
                "dimensions": ["page"],
                "rowLimit": row_limit,
                "startRow": start_row,
            }

            self.logger.info(
                f"[gsc_pages] Fetching rows {start_row}-{start_row + row_limit}"
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
        """Convert GSC page response to pages table format."""
        records = []
        for row in raw_rows:
            keys = row.get("keys", [])
            if not keys:
                continue

            url = keys[0]
            clicks = int(row.get("clicks", 0))
            impressions = int(row.get("impressions", 0))

            # Determine CMS type from URL pattern
            cms_type = None
            if "/blog/" in url or "/post/" in url:
                cms_type = "blog"
            elif "/services/" in url or "/service/" in url:
                cms_type = "service"
            else:
                cms_type = "page"

            # Extract a reasonable title from URL path
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            path = unquote(parsed.path.strip("/"))
            if path:
                title = path.split("/")[-1].replace("-", " ").replace("_", " ").title()
            else:
                title = parsed.netloc + " (Homepage)"

            records.append({
                "site_id": site_url,
                "url": url,
                "cms_type": cms_type,
                "title": title,
                "sessions": 0,  # Will be filled by GA4
                "clicks": clicks,
                "impressions": impressions,
                "issues": None,
                "last_modified": None,
            })

        return records

    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """Fetch real page performance from GSC for the given site."""
        site_url = self._resolve_site(site_id)
        if not site_url:
            raise ValueError("[gsc_pages] No GSC site configured for this Site row or .env.")
        # Query the resolved GSC property; STORE under the canonical Site.site_url key the
        # app reads by (they differ when gsc_property is the sc-domain: form — see gsc.py).
        canonical = site_id or site_url

        start_str, end_str = gsc_safe_range(days)
        self.logger.info(f"[gsc_pages] Fetching pages [{site_url}]: {start_str} to {end_str}")

        raw_rows = self._fetch_pages(site_url, start_str, end_str)
        records = self._normalize(raw_rows, canonical)

        self.logger.info(f"[gsc_pages] Got {len(records)} pages from GSC for {site_url}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_pages(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = GSCPagesConnector()
    records = connector.fetch(days=90)
    print(f"Fetched {len(records)} pages from GSC")
    if records:
        for r in records[:5]:
            print(f"  {r['url']} - clicks:{r['clicks']} imp:{r['impressions']}")
