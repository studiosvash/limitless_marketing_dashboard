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
            crawl_progress = data["tasks"][0].get("result", [{}])[0].get("crawl_progress", "")

            self.logger.info(f"[dataforseo_onpage] Crawl status: {crawl_progress} ({elapsed}s)")
            if crawl_progress == "finished":
                return True

        self.logger.warning(f"[dataforseo_onpage] Crawl timed out after {max_wait}s")
        return False

    def _fetch_issues(self, task_id: str) -> list[dict]:
        """Fetch technical issues from completed on-page task."""
        resp = requests.post(
            "https://api.dataforseo.com/v3/on_page/pages",
            auth=self.auth,
            json=[{"id": task_id, "limit": 1000, "filters": [["meta.htags", ">", 0]]}],
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        tasks = data.get("tasks", [])
        if not tasks:
            return []

        task = tasks[0]
        result = task.get("result")
        if not result:
            return []

        items = result[0].get("items", [])

        records = []
        now = datetime.now(timezone.utc)

        for item in items:
            checks = item.get("checks", {})
            for issue_type, has_issue in checks.items():
                if has_issue and has_issue is not True:
                    continue
                if not has_issue:
                    continue
                severity = "high" if "error" in issue_type else "medium"
                records.append({
                    "url": item.get("url", ""),
                    "issue_type": issue_type,
                    "severity": severity,
                    "description": "",
                    "detected_at": now,
                })

        return records

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        task_id = self._create_task()
        completed = self._wait_for_completion(task_id)
        if not completed:
            return []
        records = self._fetch_issues(task_id)
        self.logger.info(f"[dataforseo_onpage] Found {len(records)} technical issues")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        from pipeline.db.writer import upsert_technical_issues
        return upsert_technical_issues(session, records, site_id=site_id)


if __name__ == "__main__":
    c = DataForSEOOnPageConnector()
    r = c.fetch()
    print(f"SUCCESS On-Page issues: {len(r)} records")
