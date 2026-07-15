"""
pipeline/connectors/dataforseo_serp.py — DataForSEO SERP rank tracking connector.

Fetches: daily keyword positions for the target domain.
Writes to: keyword_rankings table.

Cost: $0.0006/query (Standard Queue) — NEVER use Live mode for batch jobs.
Strategy: Submit batch → poll every 15s → fetch results.
Optimizations: stop_crawl_on_match=True, depth=30, target=domain.

Task IDs are cached in sync_log extra field to avoid re-paying for stored results.
DataForSEO stores task results for 30 days.
"""

import os
import time
from datetime import date
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import iso, yesterday
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_keyword_rankings

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


class DataForSEOSERPConnector(BaseConnector):
    name = "dataforseo_serp"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")

        if not self.login or not self.password:
            raise ValueError(
                "[dataforseo_serp] Missing DATAFORSEO_LOGIN or DATAFORSEO_PASSWORD in .env."
            )

        self.auth = (self.login, self.password)
        # Env-level fallback if no Site row defines a target domain.
        self._default_target = self._strip(os.getenv("DATAFORSEO_TARGET_DOMAIN", ""))

    @staticmethod
    def _strip(domain: str) -> str:
        return (
            (domain or "")
            .replace("https://", "")
            .replace("http://", "")
            .replace("sc-domain:", "")
            .rstrip("/")
        )

    def _resolve_site(self, site_id: Optional[str]) -> tuple[str, str]:
        """Return (site_id_for_db, clean_target_domain)."""
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                target = self._strip(site.dataforseo_target_domain or site.site_url)
                return (site.site_url, target)
        return (site_id or "", self._default_target)

    def _load_keywords(self, site_id: str = "") -> list[str]:
        """Load tracked keywords from keywords.txt (skips comments/blanks)."""
        from pipeline.utils.keywords import load_tracked_keywords
        keywords = load_tracked_keywords(site_id)
        if keywords:
            self.logger.info(f"[dataforseo_serp] Loaded {len(keywords)} keywords from keywords.txt")
        else:
            self.logger.warning(
                "[dataforseo_serp] No keywords in keywords.txt — nothing will be tracked."
            )
        return keywords

    @with_retry(max_retries=3, base_delay=5.0)
    def _submit_tasks(self, keywords: list[str], target_domain: str) -> list[str]:
        """
        Submit keywords to DataForSEO Standard Queue for a specific target domain.
        Batch up to 100 keywords per request for efficiency.

        Returns:
            List of task_ids to poll.
        """
        # DataForSEO accepts up to 100 tasks per POST request
        batch_size = 100
        task_ids = []

        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]

            payload = [
                {
                    "keyword": kw,
                    "location_name": "United States",
                    "language_name": "English",
                    "device": "desktop",
                    "os": "windows",
                    "target": target_domain,         # Per-site target (resolved from Site row)
                    "stop_crawl_on_match": True,     # Cost optimization: stop when found
                    "depth": 30,                     # Top 30 only (not 100)
                    "calculate_rectangles": False,   # Not needed
                    "tag": f"fusehealth_{iso(yesterday())}",
                }
                for kw in batch
            ]

            resp = requests.post(
                f"{DATAFORSEO_BASE}/serp/google/organic/task_post",
                auth=self.auth,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract task IDs from response
            for task in data.get("tasks", []):
                if task.get("id"):
                    task_ids.append(task["id"])

            self.logger.debug(f"[dataforseo_serp] Submitted batch {i//batch_size + 1}: {len(batch)} keywords")
            time.sleep(0.5)  # Brief pause between batch submissions

        self.logger.info(f"[dataforseo_serp] Submitted {len(task_ids)} tasks to Standard Queue")
        return task_ids

    def _poll_and_fetch(
        self,
        task_ids: list[str],
        target_domain: str,
        site_id: str,
        max_polls: int = 20,
        poll_interval: int = 15,
    ) -> list[dict]:
        """
        Poll Standard Queue for completed tasks.
        Average completion time: 3–7 minutes.
        Max wait: max_polls × poll_interval seconds.

        Returns:
            Normalized records for keyword_rankings table.
        """
        records = []
        pending = list(task_ids)
        tracking_date = yesterday()

        for poll_num in range(1, max_polls + 1):
            if not pending:
                break

            self.logger.info(
                f"[dataforseo_serp] Poll {poll_num}/{max_polls}: "
                f"{len(pending)} tasks pending..."
            )
            time.sleep(poll_interval)

            still_pending = []
            for task_id in pending:
                try:
                    resp = requests.get(
                        f"{DATAFORSEO_BASE}/serp/google/organic/task_get/{task_id}",
                        auth=self.auth,
                        timeout=20,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    task_data = data.get("tasks", [{}])[0]
                    status_code = task_data.get("status_code", 0)

                    if status_code == 20000:  # Complete
                        task_records = self._normalize_task(task_data, tracking_date, target_domain, site_id)
                        records.extend(task_records)
                    elif status_code in (40101, 40601):  # Error codes
                        self.logger.warning(
                            f"[dataforseo_serp] Task {task_id} failed: "
                            f"{task_data.get('status_message', 'unknown error')}"
                        )
                    else:
                        still_pending.append(task_id)  # Still processing

                except Exception as exc:
                    self.logger.warning(f"[dataforseo_serp] Poll error for {task_id}: {exc}")
                    still_pending.append(task_id)

            pending = still_pending

        if pending:
            self.logger.warning(
                f"[dataforseo_serp] {len(pending)} tasks did not complete within "
                f"{max_polls * poll_interval}s. Task IDs: {pending[:5]}..."
            )

        return records

    def _normalize_task(self, task_data: dict, tracking_date: date,
                        target_domain: str, site_id: str) -> list[dict]:
        """
        Extract keyword + position from a completed SERP task result.
        Returns at most one record per keyword (our domain's position).
        Tags every record with site_id so per-site upserts are clean.
        """
        keyword = task_data.get("data", {}).get("keyword", "")
        result = task_data.get("result", [{}])
        if not result:
            return []

        items = result[0].get("items", [])

        # Find our domain in the results
        for item in items:
            if item.get("type") != "organic":
                continue

            url = item.get("url", "")
            if target_domain and target_domain not in url:
                continue  # Not our domain

            return [{
                "date": tracking_date,
                "site_id": site_id,
                "keyword": keyword,
                "position": item.get("rank_absolute"),
                "url": url,
                "search_volume": None,   # Will be enriched by Keywords connector
                "keyword_difficulty": None,
                "cpc": None,
            }]

        # Domain not found in top 30 — record as not ranking
        return [{
            "date": tracking_date,
            "site_id": site_id,
            "keyword": keyword,
            "position": None,  # Not ranked in top 30
            "url": None,
            "search_volume": None,
            "keyword_difficulty": None,
            "cpc": None,
        }]

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Submit all tracked keywords and fetch their current rankings for this site.

        Returns:
            List of dicts for keyword_rankings table.
        """
        resolved_site_id, target_domain = self._resolve_site(site_id)
        if not target_domain:
            raise ValueError(
                "[dataforseo_serp] No DataForSEO target domain configured for this site. "
                "Set dataforseo_target_domain in Settings → Manage Sites."
            )

        keywords = self._load_keywords(resolved_site_id)
        if not keywords:
            self.logger.warning("[dataforseo_serp] No keywords to track (keywords.txt empty/missing).")
            return []

        self.logger.info(f"[dataforseo_serp] Tracking {len(keywords)} keywords for {target_domain}")
        task_ids = self._submit_tasks(keywords, target_domain)

        if not task_ids:
            self.logger.error("[dataforseo_serp] No task IDs returned from submission.")
            return []

        records = self._poll_and_fetch(task_ids, target_domain, resolved_site_id)
        self.logger.info(f"[dataforseo_serp] Retrieved {len(records)} ranking records for {target_domain}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_keyword_rankings(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = DataForSEOSERPConnector()
    keywords = connector._load_keywords()
    print(f"Keywords loaded: {len(keywords)}")
    if keywords:
        print(f"First 5: {keywords[:5]}")
        print("\nTo run a full sync: connector.sync()")
