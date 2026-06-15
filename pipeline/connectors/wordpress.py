"""
pipeline/connectors/wordpress.py — WordPress REST API connector.
"""

import os
from typing import Optional
import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.db.writer import upsert_pages

load_dotenv()


class WordPressConnector(BaseConnector):
    name = "wordpress"

    def __init__(self):
        super().__init__()
        self.site_url = os.getenv("WP_SITE_URL", "").rstrip("/")
        self.username = os.getenv("WP_USERNAME")
        self.app_password = os.getenv("WP_APP_PASSWORD")

        if not self.site_url:
            raise ValueError("[wordpress] Missing WP_SITE_URL in .env.")

        # Auth only needed for private/draft content
        self.auth = (self.username, self.app_password) if self.username else None

    @with_retry(max_retries=3, base_delay=5.0)
    def _get_content(self, endpoint: str) -> list[dict]:
        """
        Fetch all published posts or pages from WordPress REST API.
        Paginated — fetches 100 items per page.
        """
        base_url = f"{self.site_url}/wp-json/wp/v2/{endpoint}"
        all_items = []
        page = 1

        while True:
            params = {"per_page": 100, "page": page, "status": "publish", "_fields": "id,link,title,date_gmt,modified_gmt"}
            resp = requests.get(
                base_url,
                auth=self.auth,
                params=params,
                timeout=20,
            )

            # WordPress returns 400 when page exceeds total pages
            if resp.status_code == 400:
                break
            resp.raise_for_status()

            items = resp.json()
            if not items:
                break

            all_items.extend(items)
            page += 1

        return all_items

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """Fetch all published posts and pages from WordPress."""
        posts = self._get_content("posts")
        pages = self._get_content("pages")
        all_content = posts + pages
        self.logger.info(f"[wordpress] Fetched {len(posts)} posts + {len(pages)} pages")

        records = []
        for item in all_content:
            records.append({
                "url": item.get("link", ""),
                "cms_type": "wordpress",
                "title": item.get("title", {}).get("rendered", ""),
                "sessions": 0,
                "clicks": 0,
                "impressions": 0,
                "issues": None,
                "last_modified": item.get("modified_gmt", "")[:10] if item.get("modified_gmt") else None,
            })

        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_pages(session, records, site_id=site_id)


if __name__ == "__main__":
    try:
        c = WordPressConnector()
        records = c.fetch()
        print(f"{c.name}: {len(records)} pages fetched")
        if records:
            print(f"Sample: {records[0]}")
    except Exception as exc:
        print(f"WordPressConnector main block execution failed: {exc}")
