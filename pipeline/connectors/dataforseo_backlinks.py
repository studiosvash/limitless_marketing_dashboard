"""
pipeline/connectors/dataforseo_backlinks.py — DataForSEO Backlinks live connector.
"""

import os
from datetime import datetime
from typing import Optional
import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.retry import with_retry
from pipeline.db.writer import upsert_backlinks

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


class DataForSEOBacklinksConnector(BaseConnector):
    name = "dataforseo_backlinks"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.target = os.getenv("DATAFORSEO_TARGET_DOMAIN", "")
        if not self.target:
            self.target = os.getenv("GSC_SITE_URL", "")

        if not self.login or not self.password:
            raise ValueError("[dataforseo_backlinks] Missing credentials in .env.")

        self.auth = (self.login, self.password)
        self.clean_target = self.target.replace("https://", "").replace("http://", "").rstrip("/")

    def _parse_date(self, date_str: str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except Exception:
            return None

    @with_retry(max_retries=3, base_delay=5.0)
    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """Fetch live backlinks using DataForSEO Backlinks Live endpoint."""
        target = site_id.replace("sc-domain:", "").replace("https://", "").replace("http://", "").rstrip("/") if site_id else self.clean_target
        self.logger.info(f"[dataforseo_backlinks] Fetching backlinks for target: {target}")

        payload = [{
            "target": target,
            "limit": 1000,
            "filters": [["dofollow", "=", True]],  # Only dofollow backlinks
            "include_subdomains": True,
            "order_by": ["rank,desc"]
        }]

        resp = requests.post(
            f"{DATAFORSEO_BASE}/backlinks/backlinks/live",
            auth=self.auth,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # The live Backlinks call is already billed by the time we parse it. Read the
        # charge off the envelope before any of the early returns below, so a failed or
        # empty task still books what it cost.
        run_cost = extract_cost(data)

        tasks = data.get("tasks", [])
        if not tasks:
            self.logger.warning("[dataforseo_backlinks] No tasks returned in response.")
            record_cost(self.name, site_id, run_cost, units=0,
                        notes=f"backlinks/backlinks live for {target} (no tasks)")
            return []

        task = tasks[0]
        status_code = task.get("status_code")
        if status_code != 20000:
            self.logger.error(f"[dataforseo_backlinks] Task failed with status: {status_code} - {task.get('status_message')}")
            record_cost(self.name, site_id, run_cost, units=0,
                        notes=f"backlinks/backlinks live for {target} (status {status_code})")
            return []

        result = task.get("result", [])
        if not result:
            self.logger.warning("[dataforseo_backlinks] Empty result returned.")
            record_cost(self.name, site_id, run_cost, units=0,
                        notes=f"backlinks/backlinks live for {target} (empty result)")
            return []

        items = result[0].get("items", [])
        self.logger.info(f"[dataforseo_backlinks] Retrieved {len(items)} raw backlinks items.")

        # `units` = backlink rows returned — the Backlinks API meters per returned row
        # (this call requests limit=1000), so cost/units is the real price per backlink.
        record_cost(self.name, site_id, run_cost, units=len(items),
                    notes=f"backlinks/backlinks live for {target}")

        records = []
        for item in items:
            domain = item.get("domain_from") or item.get("domain")
            target_url = item.get("url_to") or item.get("url_from") or item.get("target")
            if not domain or not target_url:
                continue

            records.append({
                "referring_domain": domain,
                "target_url": target_url,
                "anchor": item.get("anchor", ""),
                "status": item.get("status", "live"),
                "dofollow": 1 if item.get("dofollow") else 0,
                "domain_rank": item.get("rank"),
                "first_seen": self._parse_date(item.get("first_seen")),
                "last_seen": self._parse_date(item.get("last_seen")),
            })

        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        from pipeline.db.writer import ensure_tables
        from pipeline.db.schema import Backlink
        ensure_tables(session, Backlink)
        return upsert_backlinks(session, records, site_id=site_id)


if __name__ == "__main__":
    try:
        c = DataForSEOBacklinksConnector()
        records = c.fetch()
        print(f"SUCCESS {c.name}: {len(records)} backlinks fetched")
        if records:
            print(f"Sample: {records[0]}")
    except Exception as exc:
        print(f"DataForSEOBacklinksConnector main block execution failed: {exc}")
