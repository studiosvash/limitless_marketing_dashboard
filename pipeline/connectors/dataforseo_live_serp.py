"""
pipeline/connectors/dataforseo_live_serp.py — DataForSEO Live SERP Connector

Fetches the real-time top organic ranking results for a given keyword and location.
"""

import os
import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.retry import with_retry

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


# ---------------------------------------------------------------------------
# location_name normalisation
# ---------------------------------------------------------------------------
# DataForSEO's SERP API docs (Design_features/uploads/API Docs/SERP_API_Docs.md,
# "Additional Parameters" of /serp/google/organic/live/advanced) define the field as:
#
#   | `location_name` | string | *full name of search engine location* ...
#     example: `London,England,United Kingdom` |
#
# and the /serp/google/locations response documents the same shape:
#
#   "location_name": "Vienna International Airport,Lower Austria,Austria"
#   "location_name": "Lower Austria,Austria"
#
# So the expected form is MOST-SPECIFIC-FIRST, comma-delimited, no spaces around the
# commas and no dash. The DataForSEO Labs API (used by the domain-overview connector)
# takes the identical `location_name` field with the same convention.
#
# The SPA's location picker is fed from static/spa/us_cities.json, which is the exact
# opposite, human-readable order:
#     "United States"                     -> already valid (country only)
#     "United States - Texas"             -> "Texas,United States"
#     "United States - Austin, TX"        -> "Austin,Texas,United States"
#
# Passing those through untouched (as both connectors previously did) makes every
# state- or city-level selection return nothing or error out.
#
# This helper lives here, and dataforseo_domain_overview.py imports it, so there is
# exactly ONE implementation. It belongs in the SERP connector because the SERP API
# docs are where the `location_name` contract is actually specified; the Labs docs
# only reference the field.

# US state / territory abbreviations used by static/spa/us_cities.json city entries
# ("United States - Austin, TX"). DataForSEO wants the full state name.
_US_STATE_BY_ABBR = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "PR": "Puerto Rico",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

DEFAULT_LOCATION_NAME = "United States"


def normalize_location_name(location_name: str) -> str:
    """Convert the SPA's "Country - Region" location string into DataForSEO's
    `location_name` form (most specific first, comma-delimited, no spaces).

    Already-valid values are returned unchanged, so this is safe to apply to every
    caller's input:

        ""                            -> "United States"   (falls back to the default)
        "United States"               -> "United States"
        "United Kingdom"              -> "United Kingdom"
        "Texas,United States"         -> "Texas,United States"   (already correct)
        "United States - Texas"       -> "Texas,United States"
        "United States - Austin, TX"  -> "Austin,Texas,United States"
    """
    if not location_name or not str(location_name).strip():
        return DEFAULT_LOCATION_NAME

    value = str(location_name).strip()

    # No " - " separator means this is not the SPA's dash form. It is either a plain
    # country ("United States") or a value already in DataForSEO order
    # ("Texas,United States") -- only tidy the spacing around any commas.
    if " - " not in value:
        return ",".join(p.strip() for p in value.split(",") if p.strip()) or DEFAULT_LOCATION_NAME

    country, _, region = value.partition(" - ")
    country = country.strip()
    region = region.strip()
    if not region:
        return country or DEFAULT_LOCATION_NAME

    # region is either a state ("Texas") or a city + state abbreviation ("Austin, TX").
    parts = [p.strip() for p in region.split(",") if p.strip()]
    # Expand a trailing 2-letter US state abbreviation to its full name; leave any
    # unrecognised value alone rather than dropping or inventing data.
    if len(parts) >= 2:
        parts[-1] = _US_STATE_BY_ABBR.get(parts[-1].upper(), parts[-1])

    if country:
        parts.append(country)
    return ",".join(parts)


class DataForSEOLiveSERPConnector(BaseConnector):
    name = "dataforseo_live_serp"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.auth = (self.login, self.password)

    @with_retry(max_retries=2, base_delay=3.0)
    def get_live_serp(self, keyword: str, location_name: str = "United States", depth: int = 15,
                      site_id: str = "") -> dict:
        """
        Fetch real-time SERP for a specific keyword.

        `site_id` is optional and only attributes the connector_costs row this call writes.
        The live-SERP drawer is request-scoped and its API view carries no project at all,
        so unless a caller supplies one the spend is booked against the unattributed ""
        site — still counted in the account-wide total, just not per project.
        """
        if not self.login or not self.password:
            return {"status": "error", "error": "DataForSEO credentials are not configured."}

        keyword = keyword.strip()
        if not keyword:
            return {"status": "error", "error": "Keyword cannot be empty."}

        # The UI sends "United States - Austin, TX"; DataForSEO wants "Austin,Texas,United States".
        location_name = normalize_location_name(location_name)

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

        # Live SERP is the most expensive retrieval method (SERP_API_Docs.md L62) and it is
        # already billed by the time we parse. Read the charge off the envelope up front so
        # every early return below still books what was spent.
        run_cost = extract_cost(data)
        # `units` = 1 SERP query. That is what the endpoint meters; note the docs' rule that
        # `depth` above the endpoint default multiplies the price of that single query, so
        # cost/units legitimately varies with the depth the caller asked for.
        cost_note = f"serp/google/organic/live/advanced '{keyword}' @ {location_name} depth={depth}"

        tasks = data.get("tasks", [])
        if not tasks:
            record_cost(self.name, site_id, run_cost, units=1, notes=f"{cost_note} (no tasks)")
            return {"status": "error", "error": "No tasks returned from DataForSEO."}

        task = tasks[0]
        if task.get("status_code") != 20000:
            record_cost(self.name, site_id, run_cost, units=1,
                        notes=f"{cost_note} (status {task.get('status_code')})")
            return {"status": "error", "error": f"DataForSEO error: {task.get('status_message')}"}

        record_cost(self.name, site_id, run_cost, units=1, notes=cost_note)

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
