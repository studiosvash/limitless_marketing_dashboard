"""
pipeline/connectors/dataforseo_domain_overview.py — DataForSEO Domain Overview Connector

Fetches top organic keywords and basic overview metrics for a given domain or URL.
"""

import os
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.retry import with_retry
# Single shared implementation of the DataForSEO `location_name` normaliser. It is
# defined in the live-SERP connector (where the SERP API docs specify the format) and
# imported here so the two connectors cannot drift apart. The DataForSEO Labs endpoint
# used below takes the same `location_name` field with the same convention.
from pipeline.connectors.dataforseo_live_serp import normalize_location_name

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


class DataForSEODomainOverviewConnector(BaseConnector):
    name = "dataforseo_domain_overview"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.auth = (self.login, self.password)

    @with_retry(max_retries=2, base_delay=3.0)
    def get_domain_overview(self, target_url: str, location_name: str = "United States",
                            limit: int = 50, site_id: str = "") -> dict:
        """
        Fetch domain overview metrics and top organic keywords for a domain or specific URL.

        `site_id` is optional and only attributes the connector_costs row this call writes.
        This is a request-scoped lookup (the Domain Overview drawer), and its API view calls
        it without a project in hand, so the spend is booked against the unattributed ""
        site unless a caller passes one. The returned `cost` field is unchanged.
        """
        if not self.login or not self.password:
            return {"status": "error", "error": "DataForSEO credentials are not configured."}

        target_url = target_url.strip().lower()
        if not target_url:
            return {"status": "error", "error": "Target URL cannot be empty."}

        # The UI sends "United States - Texas"; DataForSEO wants "Texas,United States".
        location_name = normalize_location_name(location_name)

        # Ensure scheme for urlparse
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            parsed_url = urlparse("https://" + target_url)
        else:
            parsed_url = urlparse(target_url)

        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        
        path = parsed_url.path
        # Remove trailing slash if present for consistency, except if root
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        payload = {
            "target": domain,
            "location_name": location_name,
            "language_name": "English",
            "item_types": ["organic"],
            "limit": limit,
            "order_by": ["keyword_data.keyword_info.search_volume,desc"]
        }

        # If a specific page path is given, apply filter
        if path and path != "/":
            payload["filters"] = [["ranked_serp_element.serp_item.relative_url", "=", path]]

        try:
            resp = requests.post(
                f"{DATAFORSEO_BASE}/dataforseo_labs/google/ranked_keywords/live",
                auth=self.auth,
                json=[payload],
                timeout=45,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.logger.warning(f"[dataforseo_domain_overview] Failed to fetch ranked keywords: {exc}")
            return {"status": "error", "error": f"Failed to fetch data: {exc}"}

        # The live Labs call is already billed by the time we get here. Read the charge off
        # the envelope up front so the early returns below still book what was spent.
        run_cost = extract_cost(data)

        tasks = data.get("tasks", [])
        if not tasks:
            record_cost(self.name, site_id, run_cost, units=0,
                        notes=f"labs/ranked_keywords live for {domain} (no tasks)")
            return {"status": "error", "error": "No tasks returned from DataForSEO."}

        task = tasks[0]
        if task.get("status_code") != 20000:
            record_cost(self.name, site_id, run_cost, units=0,
                        notes=f"labs/ranked_keywords live for {domain} (status {task.get('status_code')})")
            return {"status": "error", "error": f"DataForSEO error: {task.get('status_message')}"}

        results = task.get("result", [])
        if not results:
            record_cost(self.name, site_id, run_cost, units=0,
                        notes=f"labs/ranked_keywords live for {domain} (no result)")
            return {"status": "ok", "metrics": {}, "keywords": []}

        result = results[0]
        if not result:
            record_cost(self.name, site_id, run_cost, units=0,
                        notes=f"labs/ranked_keywords live for {domain} (empty result)")
            return {"status": "ok", "metrics": {}, "keywords": []}

        metrics = result.get("metrics") or {}
        metrics_raw = metrics.get("organic", {}) or {}
        
        # High-level KPIs
        metrics = {
            "organic_traffic": metrics_raw.get("etv", 0),
            "traffic_value": metrics_raw.get("estimated_paid_traffic_cost", 0),
            "ranked_keywords": metrics_raw.get("count", 0)
        }

        # Top keywords list
        items = result.get("items") or []
        keywords = []
        for item in items:
            kw_data = item.get("keyword_data", {})
            kw_info = kw_data.get("keyword_info", {})
            kw_props = kw_data.get("keyword_properties", {})
            serp_elem = item.get("ranked_serp_element", {}).get("serp_item", {})
            intent_info = kw_data.get("search_intent_info", {})
            main_intent = intent_info.get("main_intent") if isinstance(intent_info, dict) else None

            keywords.append({
                "keyword": kw_data.get("keyword", ""),
                "intent": main_intent.capitalize() if main_intent else "Informational",
                "position": serp_elem.get("rank_group", 0),
                "volume": kw_info.get("search_volume", 0),
                "cpc": round(kw_info.get("cpc", 0) or 0, 2),
                "traffic": round(serp_elem.get("etv", 0) or 0, 2),
                "url": serp_elem.get("url", "")
            })

        # `units` = ranked keyword rows returned — Labs ranked_keywords meters per returned
        # keyword, so cost/units is the true per-keyword price of this lookup.
        record_cost(self.name, site_id, run_cost, units=len(keywords),
                    notes=f"labs/ranked_keywords live for {domain}{path if path != '/' else ''}")

        return {
            "status": "ok",
            "metrics": metrics,
            "keywords": keywords,
            "target": target_url,
            "domain": domain,
            "path": path,
            "cost": task.get("cost", 0)
        }
