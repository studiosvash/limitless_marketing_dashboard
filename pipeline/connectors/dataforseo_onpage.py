"""
pipeline/connectors/dataforseo_onpage.py — DataForSEO On-Page API connector.
"""

import os
import time
import requests
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.retry import with_retry

load_dotenv()


class DataForSEOOnPageConnector(BaseConnector):
    """
    DataForSEO On-Page API connector.
    Crawls the target domain and identifies technical SEO issues.
    """
    name = "dataforseo_onpage"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.target = os.getenv("DATAFORSEO_TARGET_DOMAIN", "")
        if not self.login or not self.password:
            raise ValueError("[dataforseo_onpage] Missing credentials in .env.")
        self.auth = (self.login, self.password)
        self.clean_target = self.target.replace("https://", "").replace("http://", "").rstrip("/")
        # USD DataForSEO reported for the current fetch(), summed over task_post +
        # the summary polls + the pages call, and written as one row per crawl.
        self._run_cost = 0.0
        # `crawl_status.pages_crawled` from the summary endpoint — the honest meter for
        # OnPage, which bills per crawled page (see OnPage_API_Docs.md L777-L780).
        self._pages_crawled = None
        # Per-page link/word counts harvested from the SAME /v3/on_page/pages response that
        # produces the technical issues. Stashed on the instance (like _run_cost above) because
        # `fetch()` may return exactly one list and that list is the technical-issue rows;
        # `_write_records` picks this up and writes it to its own table. Never override sync().
        self._page_meta: list[dict] = []

    @with_retry(max_retries=3, base_delay=10.0)
    def _create_task(self) -> str:
        """Submit an on-page crawl task. Returns task_id."""
        payload = [{
            "target": self.clean_target,
            "max_crawl_pages": 200,
            "load_resources": False,
            "store_raw_html": False,
            "enable_browser_rendering": False,
        }]

        resp = requests.post(
            "https://api.dataforseo.com/v3/on_page/task_post",
            auth=self.auth,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # OnPage bills the crawl at task_post (priced by max_crawl_pages and the
        # resource/JS flags set above) — the charge is on this envelope.
        self._run_cost += extract_cost(data)
        task_id = data["tasks"][0]["id"]
        self.logger.info(f"[dataforseo_onpage] Task created: {task_id}")
        return task_id

    def _wait_for_completion(self, task_id: str, max_wait: int = 600) -> bool:
        """Poll until on-page crawl is complete. Returns True on success."""
        elapsed = 0
        interval = 30

        while elapsed < max_wait:
            time.sleep(interval)
            elapsed += interval

            resp = requests.get(
                f"https://api.dataforseo.com/v3/on_page/summary/{task_id}",
                auth=self.auth,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            self._run_cost += extract_cost(data)
            summary = data["tasks"][0].get("result", [{}])[0] or {}
            crawl_progress = summary.get("crawl_progress", "")
            # Remember the real page count so the cost row's `units` is what OnPage
            # actually meters, not a proxy like "pages we happened to keep".
            pages = (summary.get("crawl_status") or {}).get("pages_crawled")
            if pages is not None:
                self._pages_crawled = pages

            self.logger.info(f"[dataforseo_onpage] Crawl status: {crawl_progress} ({elapsed}s)")
            if crawl_progress == "finished":
                return True

        self.logger.warning(f"[dataforseo_onpage] Crawl timed out after {max_wait}s")
        return False

    @staticmethod
    def _as_count(value) -> Optional[int]:
        """Coerce an OnPage count to int, or None when it was not measured.

        `plain_text_word_count` is documented as a float; the link counts as integers. A field
        OnPage could not measure is absent or null, and it must stay None all the way to the
        payload — a 0 here would claim "this page has no internal links", which is a real and
        different finding (an orphan page).
        """
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return None

    def _fetch_issues(self, task_id: str) -> list[dict]:
        """Fetch technical issues from completed on-page task, and harvest the per-page
        link/word counts from the same response into `self._page_meta`.

        `/v3/on_page/pages` returns, per item (OnPage_API_Docs.md L969-L971, L987):
            meta.internal_links_count            -> internal links ON the page
            meta.external_links_count            -> external links on the page
            meta.inbound_links_count             -> internal links POINTING AT the page
            meta.content.plain_text_word_count   -> words on the page
        This method used to read `item["checks"]` and `item["url"]` and discard the entire
        `meta` object, which is why the Site Audit page had no real source for in-links,
        internal links or word count. Lighthouse cannot supply them: it has no word-count audit
        at all, and its `link-text` audit is generic-anchor-text detection, not a link count.
        """
        resp = requests.post(
            "https://api.dataforseo.com/v3/on_page/pages",
            auth=self.auth,
            json=[{"id": task_id, "limit": 1000, "filters": [["meta.htags", ">", 0]]}],
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._run_cost += extract_cost(data)

        tasks = data.get("tasks") or []
        if not tasks:
            return []

        task = tasks[0]
        result = task.get("result")
        if not result:
            return []

        items = result[0].get("items") or []

        records = []
        page_meta = []
        now = datetime.now(timezone.utc)

        for item in items:
            url = item.get("url", "")
            meta = item.get("meta") or {}
            content = meta.get("content") or {}
            counts = {
                "internal_links_count": self._as_count(meta.get("internal_links_count")),
                "external_links_count": self._as_count(meta.get("external_links_count")),
                "inbound_links_count": self._as_count(meta.get("inbound_links_count")),
                "word_count": self._as_count(content.get("plain_text_word_count")),
            }
            # A row is only worth storing if OnPage measured at least one of the four. An
            # all-None row would create a "we crawled this page" marker carrying no
            # measurement, which the payload would then have to distinguish from a real zero.
            if url and any(v is not None for v in counts.values()):
                page_meta.append({"url": url, "crawled_at": now, **counts})

            checks = item.get("checks", {})
            for issue_type, has_issue in checks.items():
                if has_issue and has_issue is not True:
                    continue
                if not has_issue:
                    continue
                severity = "high" if "error" in issue_type else "medium"
                records.append({
                    "url": url,
                    "issue_type": issue_type,
                    "severity": severity,
                    "description": "",
                    "detected_at": now,
                })

        self._page_meta = page_meta
        self.logger.info(
            f"[dataforseo_onpage] Harvested link/word counts for {len(page_meta)} "
            f"of {len(items)} returned pages"
        )
        return records

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        self._run_cost = 0.0
        self._pages_crawled = None
        self._page_meta = []
        try:
            task_id = self._create_task()
            completed = self._wait_for_completion(task_id)
            if not completed:
                return []
            records = self._fetch_issues(task_id)
        finally:
            # One row per crawl. `units` = pages crawled, which is what OnPage meters.
            # In `finally` because a crawl that times out or errors mid-poll has still
            # been billed at task_post — dropping it would understate the real bill.
            record_cost(
                self.name, site_id, self._run_cost, units=self._pages_crawled,
                notes=f"on_page task_post+summary+pages for {self.clean_target}",
            )
        self.logger.info(f"[dataforseo_onpage] Found {len(records)} technical issues")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Persist BOTH outputs of the one crawl: the technical issues and the per-page
        link/word counts harvested alongside them. Both go through a writer upsert, so a
        re-crawl updates and never duplicates."""
        from pipeline.db.writer import upsert_page_crawl_meta, upsert_technical_issues
        issues = upsert_technical_issues(session, records, site_id=site_id)
        meta = upsert_page_crawl_meta(session, self._page_meta, site_id=site_id)
        self.logger.info(f"[dataforseo_onpage] Wrote {issues} issue rows + {meta} page-meta rows")
        return issues + meta


if __name__ == "__main__":
    c = DataForSEOOnPageConnector()
    r = c.fetch()
    print(f"SUCCESS On-Page issues: {len(r)} records, page meta: {len(c._page_meta)} rows")
    if c._page_meta:
        print(f"  sample: {c._page_meta[0]}")
