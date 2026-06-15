"""
pipeline/connectors/sitemap.py — Framer sitemap parser with Robots.txt checks.
"""

import os
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.utils.robots_parser import RobotsParser
from pipeline.db.writer import upsert_pages

load_dotenv()


class SitemapConnector(BaseConnector):
    name = "sitemap"

    def __init__(self):
        super().__init__()
        self.sitemap_url = os.getenv("FRAMER_SITEMAP_URL")
        if not self.sitemap_url:
            raise ValueError("[sitemap] Missing FRAMER_SITEMAP_URL in .env.")

        # Reconstruct base site URL from sitemap URL
        parsed = urlparse(self.sitemap_url)
        self.site_url = f"{parsed.scheme}://{parsed.netloc}"

        # Load Robots.txt rules
        self.robots = RobotsParser(self.site_url)
        self.robots.load()
        self.blocked_issues = []

    @with_retry(max_retries=3, base_delay=5.0)
    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Parse Framer sitemap.xml to extract page URLs + last-modified dates.
        Cross-references with robots.txt rules to identify blocked index pages.
        """
        self.logger.info(f"[sitemap] Parsing sitemap: {self.sitemap_url}")
        resp = requests.get(self.sitemap_url, timeout=30)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        records = []
        self.blocked_issues = []

        for url_el in root.findall("sm:url", ns):
            loc = url_el.find("sm:loc", ns)
            lastmod = url_el.find("sm:lastmod", ns)

            url = loc.text if loc is not None else None
            if not url:
                continue

            last_mod_str = lastmod.text[:10] if lastmod is not None and lastmod.text else None

            records.append({
                "url": url,
                "cms_type": "framer",
                "title": None,      # Not available in sitemap
                "sessions": 0,
                "clicks": 0,
                "impressions": 0,
                "issues": None,
                "last_modified": last_mod_str,
            })

            # Check robots.txt permissions
            if not self.robots.is_allowed(url):
                self.logger.warning(f"[sitemap] Blocked crawler URL detected: {url}")
                self.blocked_issues.append({
                    "url": url,
                    "issue_type": "robots_txt_blocked",
                    "severity": "medium",
                    "description": "Page is disallowed by robots.txt crawl rules.",
                    "detected_at": datetime.now(timezone.utc)
                })

        self.logger.info(f"[sitemap] Parsed {len(records)} URLs from sitemap. Blocked pages: {len(self.blocked_issues)}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        # 1. Upsert discovered sitemap pages
        written = upsert_pages(session, records, site_id=site_id)

        # 2. Upsert crawlability blockages to technical_issues table
        if self.blocked_issues:
            from pipeline.db.writer import upsert_technical_issues
            upsert_technical_issues(session, self.blocked_issues, site_id=site_id)
            self.logger.info(f"[sitemap] Logged {len(self.blocked_issues)} robots.txt blocks to technical_issues.")

        return written


if __name__ == "__main__":
    try:
        c = SitemapConnector()
        records = c.fetch()
        print(f"{c.name}: {len(records)} pages parsed.")
        if c.blocked_issues:
            print(f"Sample blocked issue: {c.blocked_issues[0]}")
    except Exception as exc:
        print(f"SitemapConnector main block execution failed: {exc}")
