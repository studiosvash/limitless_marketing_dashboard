"""
pipeline/connectors/dataforseo_live_serp.py — DataForSEO Live SERP Connector

Fetches the real-time top organic ranking results for a given keyword and location.
"""

import os
import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.utils.retry import with_retry

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


class DataForSEOLiveSERPConnector(BaseConnector):
    name = "dataforseo_live_serp"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.auth = (self.login, self.password)

    @with_retry(max_retries=2, base_delay=3.0)
    def get_live_serp(self, keyword: str, location_name: str = "United States", depth: int = 15) -> dict:
        """
        Fetch real-time SERP for a specific keyword.
        """
        if not self.login or not self.password:
            return {"status": "error", "error": "DataForSEO credentials are not configured."}

        keyword = keyword.strip()
        if not keyword:
            return {"status": "error", "error": "Keyword cannot be empty."}

        payload = [{
            "keyword": keyword,
            "location_name": location_name,
            "language_name": "English",
            "depth": depth
        }]

        try:
            resp = requests.post(
                f"{DATAFORSEO_BASE}/serp/google/organic/live/advanced",
                auth=self.auth,
                json=payload,
                timeout=45,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.logger.warning(f"[dataforseo_live_serp] Failed to fetch live SERP: {exc}")
            return {"status": "error", "error": f"Failed to fetch data: {exc}"}

        tasks = data.get("tasks", [])
        if not tasks:
            return {"status": "error", "error": "No tasks returned from DataForSEO."}
            
        task = tasks[0]
        if task.get("status_code") != 20000:
            return {"status": "error", "error": f"DataForSEO error: {task.get('status_message')}"}
            
        results = task.get("result", [])
        if not results:
            return {"status": "ok", "items": []}
            
        result = results[0]
        if not result:
            return {"status": "ok", "items": []}
            
        items_raw = result.get("items") or []
        
        parsed_items = []
        for item in items_raw:
            if item.get("type") != "organic":
                continue
                
            parsed_items.append({
                "position": item.get("rank_absolute", 0),
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "domain": item.get("domain", ""),
            })

        return {
            "status": "ok",
            "keyword": keyword,
            "items": parsed_items,
            "cost": task.get("cost", 0)
        }
