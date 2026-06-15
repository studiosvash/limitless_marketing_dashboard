"""
pipeline/connectors/webflow.py — Webflow CMS connector.
"""

import os
import time
from typing import Optional
import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.db.writer import upsert_pages

load_dotenv()


# ─────────────────────────────────────────────────────────
# Webflow CMS Connector
# Rate limit: 60 req/min, 1,000 req/hr
# Strategy: time.sleep(1) between paginated requests
# ─────────────────────────────────────────────────────────

class WebflowConnector(BaseConnector):
    name = "webflow"

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("WEBFLOW_API_KEY")
        self.site_id = os.getenv("WEBFLOW_SITE_ID")

        if not self.api_key or not self.site_id:
            raise ValueError("[webflow] Missing WEBFLOW_API_KEY or WEBFLOW_SITE_ID in .env.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept-version": "2.0.0",
            "Content-Type": "application/json",
        }

    @with_retry(max_retries=3, base_delay=5.0)
    def _get_pages(self) -> list[dict]:
        """Fetch all pages from Webflow site (paginated)."""
        url = f"https://api.webflow.com/v2/sites/{self.site_id}/pages"
        all_pages = []
        offset = 0
        limit = 100

        while True:
            resp = requests.get(
                url,
                headers=self.headers,
                params={"limit": limit, "offset": offset},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

            pages = data.get("pages", [])
            all_pages.extend(pages)

            # Stop when fewer results than limit
            if len(pages) < limit:
                break

            offset += limit
            time.sleep(1)  # Stay under 60 req/min limit

        return all_pages

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """Fetch Webflow pages and normalize for pages table."""
        raw_pages = self._get_pages()
        self.logger.info(f"[webflow] Fetched {len(raw_pages)} pages")

        records = []
        for page in raw_pages:
            records.append({
                "url": page.get("url") or f"https://site/{page.get('slug', '')}",
                "cms_type": "webflow",
                "title": page.get("title") or page.get("name", ""),
                "sessions": 0,
                "clicks": 0,
                "impressions": 0,
                "issues": None,
                "last_modified": None,
            })

        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_pages(session, records, site_id=site_id)


if __name__ == "__main__":
    try:
        c = WebflowConnector()
        records = c.fetch()
        print(f"{c.name}: {len(records)} pages fetched")
        if records:
            print(f"Sample: {records[0]}")
    except Exception as exc:
        print(f"WebflowConnector main block execution failed: {exc}")
