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

# Backlink rows the weekly project sync buys. DataForSEO bills per returned row, so this is
# the price of a sync, and it is the one number worth turning down on a large site that does
# not need its whole profile refreshed every week.
DEFAULT_SYNC_LIMIT = 1000
ALLOWED_SYNC_LIMITS = (250, 500, 1000)


def sync_limit_for(site_id: Optional[str]) -> int:
    """The configured per-sync backlink row limit for a project, or the 1000 default.

    Stored under ProjectSettings.data["backlinksSyncLimit"] via mutation_state, NOT in a
    Settings group: apply_settings_update replaces a whole group object with whatever the
    request body carried, so a key the Settings form does not send would be wiped on the
    next save of any unrelated field in that group. The mutation_state keys are documented
    as the ones a Settings PUT can never clobber.

    A value outside ALLOWED_SYNC_LIMITS falls back to the default rather than being honoured
    -- this figure is money, and an arbitrary number arriving from a stored blob should not
    be able to buy 50 000 rows.

    Django is imported lazily so this module stays runnable outside Django (skills.md §13).
    """
    if not site_id:
        return DEFAULT_SYNC_LIMIT
    try:
        from apps.dashboard.services.mutation_state import get_state
        value = int(get_state(site_id, "backlinksSyncLimit", DEFAULT_SYNC_LIMIT))
    except Exception:
        return DEFAULT_SYNC_LIMIT
    return value if value in ALLOWED_SYNC_LIMITS else DEFAULT_SYNC_LIMIT


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
    def fetch(self, site_id: Optional[str] = None, limit: Optional[int] = None,
              dofollow_only: bool = False) -> list[dict]:
        """Fetch live backlinks using DataForSEO Backlinks Live endpoint.

        `limit` is the row count DataForSEO BILLS for, not a display cap -- the Backlinks API
        meters per returned row. It was hardcoded at 1000, which is right for the weekly
        project sync (buy the profile once, read it all week) and far too expensive for the
        Domain Overview lookup, which buys an arbitrary domain's profile the moment somebody
        types one in. The sync path keeps 1000 by default; Domain Overview passes 100.

        `dofollow_only` now defaults to FALSE, which reverses the sync's long-standing
        behaviour. The filter used to be hardcoded, so every stored profile was dofollow-only
        -- and the Backlinks page has a "Nofollow" filter chip and a Follow column on the
        referring-domain rollup, both of which could therefore only ever render the dofollow
        half of reality. The chip's empty state was structural: no site's link profile could
        have made it show a row. Nothing in the UI has to change to fix that; the rows already
        carry a `dofollow` flag and the filter already reads it. Same argument Domain Overview
        already made when it turned the filter off for its spam breakdown -- a review that
        silently drops every nofollow link is a review of the half of the profile least likely
        to be spam. A caller that genuinely wants dofollow-only can still pass True.

        `mode` is now sent explicitly. It was unset, and DataForSEO's documented default is
        `as_is` (all backlinks), so nothing was actually wrong -- but the other two values are
        `one_per_domain` and `one_per_anchor`, and `one_per_domain` returns exactly one row per
        referring domain. That would defeat the per-source-page unique key completely while
        looking like a perfectly healthy sync, so the answer should not depend on a remote
        default nobody in this codebase controls.

        There is deliberately NO offset/pagination loop here. The Backlinks API meters per
        RETURNED row, so paging past `limit` multiplies the price of a sync linearly with no
        cap; if one is ever added it belongs behind a setting that defaults to off.
        """
        target = site_id.replace("sc-domain:", "").replace("https://", "").replace("http://", "").rstrip("/") if site_id else self.clean_target
        if limit is None:
            limit = sync_limit_for(site_id)
        self.logger.info(f"[dataforseo_backlinks] Fetching {limit} backlinks for target: {target}")

        payload = [{
            "target": target,
            "limit": limit,
            # Verified against DataForSEO's own docs for backlinks/backlinks/live: allowed
            # values are as_is | one_per_domain | one_per_anchor, default as_is. Stated here
            # rather than inherited, because one_per_domain is one word away and would silently
            # undo the per-source-page key.
            "mode": "as_is",
            "include_subdomains": True,
            "order_by": ["rank,desc"]
        }]
        if dofollow_only:
            payload[0]["filters"] = [["dofollow", "=", True]]

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

        # `units` = backlink rows returned — the Backlinks API meters per returned row, so
        # cost/units is the real price per backlink. The requested limit is in the note
        # because it is what the row count was bounded by.
        record_cost(self.name, site_id, run_cost, units=len(items),
                    notes=f"backlinks/backlinks live for {target} (limit {limit})")

        records = []
        for item in items:
            domain = item.get("domain_from") or item.get("domain")
            # `url_to` is the page ON OUR SITE being linked to; `url_from` (below) is the
            # separate, actual page that carries the link. Never conflate the two.
            target_url = item.get("url_to") or item.get("target")
            if not domain or not target_url:
                continue

            records.append({
                "referring_domain": domain,
                "target_url": target_url,
                "anchor": item.get("anchor", ""),
                # DataForSEO has no `status` field -- it reports `is_lost` (bool). Reading a
                # nonexistent "status" key always fell back to the "live" default, so a
                # backlink that had actually gone dead still showed as live forever.
                "status": "lost" if item.get("is_lost") else "live",
                "dofollow": 1 if item.get("dofollow") else 0,
                # `domain_from_rank` is the referring DOMAIN's own authority (0-1000). The
                # previous field, `rank`, is a per-BACKLINK score that mixes in this specific
                # link's own signals -- unrelated domains landing on the same `rank` value was
                # the symptom of reading the wrong field.
                "domain_rank": item.get("domain_from_rank"),
                "first_seen": self._parse_date(item.get("first_seen")),
                "last_seen": self._parse_date(item.get("last_seen")),
                # The exact page carrying the link -- lets the UI link to the real backlink,
                # not just the bare referring domain.
                "url_from": item.get("url_from") or "",
                # The referring PAGE's own authority, distinct from the domain-wide rank above.
                "page_from_rank": item.get("page_from_rank"),
                "spam_score": item.get("backlink_spam_score"),
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
