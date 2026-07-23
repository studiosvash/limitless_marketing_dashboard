"""
pipeline/connectors/dataforseo_serp_competitors.py — Per-keyword competitor rank capture.

Sibling of dataforseo_serp.py (which it does NOT import or modify). Where that
connector keeps only YOUR domain's position per keyword, this one runs the same
tracked keywords through the SERP API and keeps the position of every TRACKED
COMPETITOR domain found in the results — the data behind the SEMrush-style
Positioning grid (your rank vs each competitor's, tracked over time).

Fetches: daily SERP positions for each tracked competitor domain, per keyword.
Writes to: competitor_keyword_rankings table.

Cost: $0.0006/query (Standard Queue) — same profile as dataforseo_serp, paid
separately. Triggered by the Positioning page refresh / scheduled sync only;
never on page render (DB-first contract).
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
from pipeline.db.writer import upsert_competitor_keyword_rankings

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


class DataForSEOSerpCompetitorsConnector(BaseConnector):
    name = "dataforseo_serp_competitors"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        if not self.login or not self.password:
            raise ValueError(
                "[dataforseo_serp_competitors] Missing DATAFORSEO_LOGIN or "
                "DATAFORSEO_PASSWORD in .env."
            )
        self.auth = (self.login, self.password)

    @staticmethod
    def _strip(domain: str) -> str:
        return (
            (domain or "")
            .replace("https://", "")
            .replace("http://", "")
            .replace("sc-domain:", "")
            .rstrip("/")
            .lower()
        )

    def _resolve_site_id(self, site_id: Optional[str]) -> str:
        """Return the site_id string used for DB rows (the site's URL)."""
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return site.site_url
        return site_id or ""

    def _load_keywords(self, site_id: str = "") -> list[str]:
        from pipeline.utils.keywords import load_tracked_keywords
        keywords = load_tracked_keywords(site_id)
        if not keywords:
            self.logger.warning(
                "[dataforseo_serp_competitors] No keywords in keywords.txt — nothing to track."
            )
        return keywords

    @with_retry(max_retries=3, base_delay=5.0)
    def _submit_tasks(self, keywords: list[str]) -> list[str]:
        """
        Submit keywords to the Standard Queue. Unlike dataforseo_serp, we do NOT
        set a `target` or `stop_crawl_on_match` — we need the full result set so
        every competitor's position is visible.
        """
        batch_size = 100
        task_ids: list[str] = []

        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            payload = [
                {
                    "keyword": kw,
                    "location_name": "United States",
                    "language_name": "English",
                    "device": "desktop",
                    "os": "windows",
                    "depth": 30,                 # top 30 — same depth as own-domain tracking
                    "calculate_rectangles": False,
                    "tag": f"fusehealth_comp_{iso(yesterday())}",
                }
                for kw in batch
            ]
            resp = requests.post(
                f"{DATAFORSEO_BASE}/serp/google/organic/task_post",
                auth=self.auth, json=payload, timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for task in data.get("tasks", []):
                if task.get("id"):
                    task_ids.append(task["id"])
            time.sleep(0.5)

        self.logger.info(f"[dataforseo_serp_competitors] Submitted {len(task_ids)} tasks")
        return task_ids

    def _poll_and_fetch(self, task_ids: list[str], competitors: set[str], site_id: str,
                        max_polls: int = 20, poll_interval: int = 15) -> list[dict]:
        """Poll the Standard Queue and normalize completed tasks into competitor rows."""
        records: list[dict] = []
        pending = list(task_ids)
        tracking_date = yesterday()

        for poll_num in range(1, max_polls + 1):
            if not pending:
                break
            self.logger.info(
                f"[dataforseo_serp_competitors] Poll {poll_num}/{max_polls}: "
                f"{len(pending)} pending"
            )
            time.sleep(poll_interval)

            still_pending = []
            for task_id in pending:
                try:
                    resp = requests.get(
                        f"{DATAFORSEO_BASE}/serp/google/organic/task_get/regular/{task_id}",
                        auth=self.auth, timeout=20,
                    )
                    resp.raise_for_status()
                    task_data = resp.json().get("tasks", [{}])[0]
                    status_code = task_data.get("status_code", 0)
                    if status_code == 20000:
                        records.extend(
                            self._normalize_task(task_data, tracking_date, competitors, site_id)
                        )
                    elif status_code in (40101, 40601):
                        self.logger.warning(
                            f"[dataforseo_serp_competitors] Task {task_id} failed: "
                            f"{task_data.get('status_message', 'unknown error')}"
                        )
                    else:
                        still_pending.append(task_id)
                except Exception as exc:
                    self.logger.warning(f"[dataforseo_serp_competitors] Poll error {task_id}: {exc}")
                    still_pending.append(task_id)
            pending = still_pending

        if pending:
            self.logger.warning(
                f"[dataforseo_serp_competitors] {len(pending)} tasks did not complete in "
                f"{max_polls * poll_interval}s."
            )
        return records

    def _normalize_task(self, task_data: dict, tracking_date: date,
                        competitors: set[str], site_id: str) -> list[dict]:
        """
        Keep the BEST (lowest) position per (keyword, competitor) from one SERP.
        A competitor not present in the captured depth simply yields no row for
        that keyword (rendered as "—" in the grid).
        """
        keyword = task_data.get("data", {}).get("keyword", "")
        result = task_data.get("result") or [{}]
        items = (result[0] or {}).get("items") or []

        best: dict[str, dict] = {}
        for item in items:
            if item.get("type") != "organic":
                continue
            url = item.get("url", "") or ""
            domain = self._strip(item.get("domain") or url)
            match = next((c for c in competitors if c and c in domain), None)
            if not match:
                continue
            pos = item.get("rank_absolute")
            existing = best.get(match)
            if existing is None or (pos is not None and pos < existing["position"]):
                best[match] = {
                    "date": tracking_date,
                    "site_id": site_id,
                    "keyword": keyword,
                    "competitor_domain": match,
                    "position": pos,
                    "url": url,
                }
        return list(best.values())

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Submit all tracked keywords and capture each tracked competitor's position.

        Returns rows for competitor_keyword_rankings. Returns [] (not an error)
        when there are no keywords or no tracked competitors yet.
        """
        from pipeline.services.competitor_service import get_tracked_competitors

        resolved_site_id = self._resolve_site_id(site_id)
        competitors = set(get_tracked_competitors(resolved_site_id))
        if not competitors:
            self.logger.warning(
                "[dataforseo_serp_competitors] No tracked competitors for "
                f"{resolved_site_id!r} (none discovered/selected yet) — nothing to capture."
            )
            return []

        keywords = self._load_keywords(resolved_site_id)
        if not keywords:
            return []

        self.logger.info(
            f"[dataforseo_serp_competitors] Tracking {len(competitors)} competitors "
            f"across {len(keywords)} keywords for {resolved_site_id!r}"
        )
        task_ids = self._submit_tasks(keywords)
        if not task_ids:
            self.logger.error("[dataforseo_serp_competitors] No task IDs returned.")
            return []

        records = self._poll_and_fetch(task_ids, competitors, resolved_site_id)
        self.logger.info(
            f"[dataforseo_serp_competitors] Captured {len(records)} competitor ranking rows"
        )
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_competitor_keyword_rankings(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = DataForSEOSerpCompetitorsConnector()
    print("Loaded. To run for the active site: connector.sync()")
