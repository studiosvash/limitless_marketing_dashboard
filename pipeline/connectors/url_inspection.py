"""
pipeline/connectors/url_inspection.py — GSC URL Inspection Connector.

Fetches REAL indexing status for pages using Google Search Console
URL Inspection API. Tells you which pages are indexed, blocked, or errored.

Scans: Top 100 pages by traffic + all pages with 0 clicks (potential issues).
Returns: Indexing verdict, coverage state, crawl status, mobile usability.
Rate limit: 2,000 requests/day, 600/minute. We scan top pages only.
"""

import os
import time
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build

from pipeline.connectors.base import BaseConnector
from pipeline.db.dialect import max_batch_size, upsert_insert
from pipeline.db.schema import IndexingStatus
from sqlalchemy import text
from pipeline.utils.auth import get_google_credentials
from pipeline.utils.db_connection import get_session

load_dotenv()


class URLInspectionConnector(BaseConnector):
    name = "url_inspection"

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

    def _get_pages_to_inspect(self, site_url: str, limit: int = 50) -> list[str]:
        """
        Intelligently sample pages to inspect:
        1. Homepage & Main Templates (Depth 1 / short paths like /services)
        2. Sample of blog pages
        3. High traffic fallback
        4. Zero-click pages with impressions (potential indexing errors)
        """
        with get_session() as session:
            rows = session.execute(
                text(
                    "SELECT url FROM pages "
                    "WHERE site_id = :sid "
                    "ORDER BY clicks DESC LIMIT 200"
                ),
                {"sid": site_url}
            ).fetchall()
            
        all_urls = [r[0] for r in rows]
        sampled = []
        
        # 1. Homepage
        home = next((u for u in all_urls if u.strip('/') == site_url.strip('/')), None)
        if home:
            sampled.append(home)
            
        # 2. Main Templates (Depth 1 paths e.g., /pricing, /about)
        main_pages = []
        for u in all_urls:
            if u in sampled: continue
            path = u.replace(site_url, '').strip('/')
            if 0 <= path.count('/') <= 1 and 'blog' not in path and 'news' not in path:
                main_pages.append(u)
        sampled.extend(main_pages[:30])
        
        # 3. Blog pages
        blog_pages = []
        for u in all_urls:
            if u in sampled: continue
            if '/blog' in u or '/news' in u or '/article' in u:
                blog_pages.append(u)
        sampled.extend(blog_pages[:2])
        
        # 4. Fallback (top traffic)
        for u in all_urls:
            if len(sampled) >= limit: break
            if u not in sampled:
                sampled.append(u)
                
        # 5. Fill remaining slots with zero-click pages to find indexing errors
        if len(sampled) < limit:
            with get_session() as session:
                zero_click = session.execute(
                    text(
                        "SELECT url FROM pages "
                        "WHERE clicks = 0 AND impressions > 0 AND site_id = :sid "
                        "ORDER BY impressions DESC LIMIT 20"
                    ),
                    {"sid": site_url}
                ).fetchall()
            for r in zero_click:
                if len(sampled) >= limit: break
                if r[0] not in sampled:
                    sampled.append(r[0])
                
        return sampled[:limit]

    def _inspect_url(self, service, url: str, site_url: str, canonical: str) -> dict | None:
        """
        Call the URL Inspection API for a single URL.
        `site_url` is the GSC property to query; `canonical` is the Site.site_url key the
        record is stored under (they differ for sc-domain properties — see gsc.py).
        Returns parsed result dict, or None on failure.
        """
        try:
            body = {
                "inspectionUrl": url,
                "siteUrl": site_url,
            }

            response = service.urlInspection().index().inspect(body=body).execute()
            result = response.get("inspectionResult", {})

            # Parse indexing result
            index_status = result.get("indexStatusResult", {})
            mobile = result.get("mobileUsabilityResult", {})
            rich = result.get("richResultsResult", {})

            # Parse crawl time
            crawl_time_str = index_status.get("lastCrawlTime")
            crawl_time = None
            if crawl_time_str:
                try:
                    crawl_time = datetime.fromisoformat(crawl_time_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            return {
                "site_id": canonical,
                "url": url,
                "verdict": index_status.get("verdict", "VERDICT_UNSPECIFIED"),
                "coverage_state": index_status.get("coverageState", ""),
                "indexing_state": index_status.get("indexingState", ""),
                "last_crawl_time": crawl_time,
                "crawl_status": index_status.get("pageFetchState", ""),
                "robots_txt_state": index_status.get("robotsTxtState", ""),
                "mobile_usability": mobile.get("verdict", ""),
                "rich_results_status": rich.get("verdict", ""),
                "last_checked": datetime.now(timezone.utc),
            }

        except Exception as e:
            error_msg = str(e)
            # Handle quota exceeded gracefully
            if "429" in error_msg or "quota" in error_msg.lower():
                self.logger.warning(f"[url_inspection] Quota exceeded. Stopping scan.")
                return "QUOTA_EXCEEDED"
            self.logger.warning(f"[url_inspection] Error inspecting {url}: {e}")
            return None

    def fetch(self, site_id: Optional[str] = None, days: int = 0) -> list[dict]:
        """Fetch URL Inspection data for top pages of the given site."""
        site_url = self._resolve_site(site_id)
        if not site_url:
            raise ValueError("[url_inspection] No GSC site configured for this Site row or .env.")
        canonical = site_id or site_url

        pages = self._get_pages_to_inspect(canonical, limit=50)
        if not pages:
            self.logger.warning(f"[url_inspection] No pages in DB for {site_url} — run gsc_pages first.")
            return []

        self.logger.info(f"[url_inspection] Inspecting {len(pages)} pages for {site_url}")

        creds = get_google_credentials()
        service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

        records = []
        for i, url in enumerate(pages):
            self.logger.info(f"[url_inspection] [{i+1}/{len(pages)}] {url}")

            result = self._inspect_url(service, url, site_url, canonical)

            if result == "QUOTA_EXCEEDED":
                self.logger.warning(f"[url_inspection] Stopped at {i+1}/{len(pages)} due to quota")
                break

            if result:
                records.append(result)

            # Rate limiting: 600/min = 0.1s/req, but be conservative
            if i < len(pages) - 1:
                time.sleep(0.2)

        self.logger.info(
            f"[url_inspection] Inspected {len(records)}/{len(pages)} pages on {site_url}. "
            f"Indexed: {sum(1 for r in records if r.get('verdict') == 'PASS')}, "
            f"Not indexed: {sum(1 for r in records if r.get('verdict') != 'PASS')}"
        )
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Upsert URL Inspection records. Unique on (site_id, url)."""
        if not records:
            return 0

        # Ensure site_id is present on every record before insert.
        for r in records:
            r.setdefault("site_id", site_id or "")

        insert = upsert_insert(session)
        BATCH_SIZE = max_batch_size(session, 50)
        total = 0
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            stmt = insert(IndexingStatus).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["site_id", "url"],
                set_={
                    "verdict": stmt.excluded.verdict,
                    "coverage_state": stmt.excluded.coverage_state,
                    "indexing_state": stmt.excluded.indexing_state,
                    "last_crawl_time": stmt.excluded.last_crawl_time,
                    "crawl_status": stmt.excluded.crawl_status,
                    "robots_txt_state": stmt.excluded.robots_txt_state,
                    "mobile_usability": stmt.excluded.mobile_usability,
                    "rich_results_status": stmt.excluded.rich_results_status,
                    "last_checked": stmt.excluded.last_checked,
                },
            )
            session.execute(stmt)
            total += len(batch)
        return total


if __name__ == "__main__":
    connector = URLInspectionConnector()
    records = connector.fetch()
    print(f"Inspected {len(records)} URLs")
    for r in records[:5]:
        print(f"  {r['url']}: {r['verdict']} — {r['coverage_state']}")
