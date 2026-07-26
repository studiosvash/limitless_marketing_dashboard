"""
pipeline/connectors/pagespeed.py — Google PageSpeed Insights Connector.

Fetches REAL Core Web Vitals and Lighthouse scores for top pages.
Uses the free PageSpeed Insights API v5 (requires GOOGLE_API_KEY).

Scans: Top 50 pages by traffic from the pages table.
Returns: Performance, SEO, Accessibility scores + LCP, CLS, INP, FCP, TTFB.
Rate limit: ~400 requests/day free tier. We scan top pages only.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.db.schema import PageSpeed
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import select, text
from pipeline.utils.db_connection import get_session

load_dotenv()

PSI_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


class PageSpeedConnector(BaseConnector):
    name = "pagespeed"

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def _resolve_site(self, site_id: Optional[str]) -> str:
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return site.site_url
        return os.getenv("GSC_SITE_URL", "")

    def _get_top_pages(self, site_url: str, limit: int = 15) -> list[str]:
        """Intelligently sample top pages (Home, short paths, blogs, fallback) up to the limit."""
        with get_session() as session:
            # Fetch a larger pool to sample from
            rows = session.execute(
                text(
                    "SELECT url FROM pages "
                    "WHERE clicks > 0 AND site_id = :sid "
                    "ORDER BY clicks DESC LIMIT 100"
                ),
                {"sid": site_url}
            ).fetchall()
            
        all_urls = [r[0] for r in rows]
        sampled = []
        
        # 1. Homepage
        home = next((u for u in all_urls if u.strip('/') == site_url.strip('/')), None)
        if home:
            sampled.append(home)
            
        # 2. Main Templates (Short paths e.g., /pricing, /about)
        main_pages = []
        for u in all_urls:
            if u in sampled: continue
            path = u.replace(site_url, '').strip('/')
            if 0 <= path.count('/') <= 1 and 'blog' not in path and 'news' not in path:
                main_pages.append(u)
        sampled.extend(main_pages[:5])
        
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
                
        return sampled[:limit]

    def _fetch_psi(self, url: str, strategy: str = "mobile") -> dict | None:
        """
        Call the PageSpeed Insights API for a single URL.
        Returns parsed scores dict, or None on failure.
        """
        params = {
            "url": url,
            "key": self.api_key,
            "strategy": strategy,
            "category": ["performance", "accessibility", "seo", "best-practices"],
        }

        try:
            resp = requests.get(PSI_API_URL, params=params, timeout=60)
            if resp.status_code == 429:
                self.logger.warning(f"[pagespeed] Rate limited. Waiting 10s...")
                time.sleep(10)
                resp = requests.get(PSI_API_URL, params=params, timeout=60)

            if resp.status_code != 200:
                self.logger.warning(
                    f"[pagespeed] API error {resp.status_code} for {url}: {resp.text[:200]}"
                )
                return None

            data = resp.json()
            lh = data.get("lighthouseResult", {})
            categories = lh.get("categories", {})
            audits = lh.get("audits", {})

            # Extract scores (API returns 0-1, we convert to 0-100)
            def score(cat_key):
                cat = categories.get(cat_key, {})
                s = cat.get("score")
                return int(s * 100) if s is not None else None

            # Extract CWV metrics from audits
            def audit_ms(audit_key):
                a = audits.get(audit_key, {})
                val = a.get("numericValue")
                return round(val, 1) if val is not None else None

            def audit_val(audit_key):
                a = audits.get(audit_key, {})
                val = a.get("numericValue")
                return round(val, 4) if val is not None else None

            # Extract detailed audits for Technical Issues (score < 1 or opportunity with savings)
            failed_audits = []
            for audit_id, audit in audits.items():
                sc = audit.get("score")
                details = audit.get("details", {})
                savings = details.get("overallSavingsMs", 0)
                if (sc is not None and sc < 1) or savings > 0:
                    failed_audits.append({
                        "id": audit_id,
                        "title": audit.get("title", ""),
                        "description": audit.get("description", ""),
                        "score": sc,
                        "savings_ms": savings,
                        "displayValue": audit.get("displayValue", "")
                    })

            return {
                "url": url,
                "strategy": strategy,
                "performance_score": score("performance"),
                "seo_score": score("seo"),
                "accessibility_score": score("accessibility"),
                "best_practices_score": score("best-practices"),
                "lcp_ms": audit_ms("largest-contentful-paint"),
                "cls": audit_val("cumulative-layout-shift"),
                "inp_ms": audit_ms("experimental-interaction-to-next-paint") or audit_ms("interaction-to-next-paint"),
                "fcp_ms": audit_ms("first-contentful-paint"),
                "ttfb_ms": audit_ms("server-response-time"),
                "si_ms": audit_ms("speed-index"),
                "lighthouse_audits": json.dumps(failed_audits) if failed_audits else None,
                "last_checked": datetime.now(timezone.utc),
            }

        except requests.exceptions.Timeout:
            self.logger.warning(f"[pagespeed] Timeout for {url}")
            return None
        except Exception as e:
            self.logger.error(f"[pagespeed] Error for {url}: {e}")
            return None

    def fetch(self, site_id: Optional[str] = None, days: int = 0) -> list[dict]:
        """
        Fetch PageSpeed data for top pages of the given site.
        Scans both mobile and desktop so the dashboard can show each separately
        (mobile-first indexing matters, but desktop UX is still graded).
        """
        if not self.api_key:
            raise ValueError("[pagespeed] Missing GOOGLE_API_KEY in .env")
        site_url = self._resolve_site(site_id)
        if not site_url:
            raise ValueError("[pagespeed] No site configured.")

        pages = self._get_top_pages(site_url, limit=15)
        if not pages:
            self.logger.warning(f"[pagespeed] No pages in DB for {site_url} — run gsc_pages first.")
            return []

        strategies = ("mobile", "desktop")
        total = len(pages) * len(strategies)
        self.logger.info(f"[pagespeed] Scanning {len(pages)} pages × {len(strategies)} strategies = {total} requests for {site_url}")

        records = []
        done = 0
        for url in pages:
            for strategy in strategies:
                done += 1
                self.logger.info(f"[pagespeed] [{done}/{total}] ({strategy}) {url}")
                result = self._fetch_psi(url, strategy=strategy)
                if result:
                    result["site_id"] = site_url
                    records.append(result)

                # Rate limiting: ~2.5 seconds between requests (safe for free tier)
                if done < total:
                    time.sleep(2.5)

        self.logger.info(f"[pagespeed] Scanned {len(records)}/{total} requests on {site_url}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Upsert PageSpeed records. Unique on (site_id, url, strategy)."""
        if not records:
            return 0

        for r in records:
            r.setdefault("site_id", site_id or "")

        BATCH_SIZE = 40
        total = 0
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            stmt = sqlite_insert(PageSpeed).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["site_id", "url", "strategy"],
                set_={
                    "performance_score": stmt.excluded.performance_score,
                    "seo_score": stmt.excluded.seo_score,
                    "accessibility_score": stmt.excluded.accessibility_score,
                    "best_practices_score": stmt.excluded.best_practices_score,
                    "lcp_ms": stmt.excluded.lcp_ms,
                    "cls": stmt.excluded.cls,
                    "inp_ms": stmt.excluded.inp_ms,
                    "fcp_ms": stmt.excluded.fcp_ms,
                    "ttfb_ms": stmt.excluded.ttfb_ms,
                    "si_ms": stmt.excluded.si_ms,
                    "lighthouse_audits": stmt.excluded.lighthouse_audits,
                    "last_checked": stmt.excluded.last_checked,
                },
            )
            session.execute(stmt)
            total += len(batch)
        return total


if __name__ == "__main__":
    connector = PageSpeedConnector()
    records = connector.fetch()
    print(f"Fetched {len(records)} PageSpeed records")
    if records:
        r = records[0]
        print(f"  {r['url']}")
        print(f"  Performance: {r['performance_score']}, SEO: {r['seo_score']}")
        print(f"  LCP: {r['lcp_ms']}ms, CLS: {r['cls']}, FCP: {r['fcp_ms']}ms")
