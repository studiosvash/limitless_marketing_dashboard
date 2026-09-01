"""
pipeline/connectors/dataforseo_serp_competitors.py — Per-keyword competitor rank capture.

Sibling of dataforseo_serp.py (which it does NOT import or modify). Where that
connector keeps only YOUR domain's position per keyword, this one runs the same
tracked keywords through the SERP API and keeps the position of every TRACKED
COMPETITOR domain found in the results — the data behind the SEMrush-style
Positioning grid (your rank vs each competitor's, tracked over time).

Fetches: daily SERP positions for each tracked competitor domain, per keyword —
plus the SERP features on the same result set (AI Overview citations, local pack,
featured snippet), retrieved via `task_get/advanced` (the `regular` endpoint returns
only organic/paid/featured_snippet; `ai_overview` items exist only on `advanced`,
and retrieval itself is free — billing happens at task_post).
Writes to: competitor_keyword_rankings + serp_feature_rankings tables.

Cost: $0.0006/query (Standard Queue) — same profile as dataforseo_serp, paid
separately — plus a +$0.0006/query surcharge for `load_async_ai_overview`, which
is auto-refunded by DataForSEO whenever the SERP has no AI Overview. Triggered by
the Positioning page refresh / scheduled sync only; never on page render
(DB-first contract).
"""

import os
import time
from datetime import date
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
# Shared SPA-form -> DataForSEO-form location converter (see dataforseo_live_serp.py).
from pipeline.connectors.dataforseo_live_serp import normalize_location_name
# One definition of the DataForSEO task status codes and the queue priority, with
# the full account of what each wrong value cost. See dataforseo_serp.py.
from pipeline.connectors.dataforseo_serp import (
    NORMAL_PRIORITY, TASK_CREATED, TASK_OK, TASK_PENDING, TASK_PRIORITY,
    _SCHEDULED_POLL_BUDGET, _WATCHED_POLL_BUDGET, _resolve_device,
)
from pipeline.db.schema import DEFAULT_LOCATION
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import iso, yesterday
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import (
    upsert_competitor_keyword_rankings, upsert_serp_feature_rankings,
)

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
        # USD DataForSEO reported for the current fetch() — accumulated across the
        # task_post batches and task_get polls, written once per run in fetch().
        self._run_cost = 0.0
        # SERP-feature rows (serp_feature_rankings) collected by _normalize_task as a side
        # channel of the current fetch(). fetch() resets it before any task is drained or
        # submitted; _write_records writes it in the same session as the competitor rows.
        self._feature_records: list[dict] = []

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
        from pipeline.services.site_service import get_site, get_site_by_pk
        with get_session() as session:
            site = get_site_by_pk(session, getattr(self, "site_pk", None)) \
                or get_site(session, site_id)
            if site:
                return site.site_url
        return site_id or ""

    def _resolve_location(self, site_id: str) -> str:
        """This PROJECT's tracking location — see the identical method on dataforseo_serp.

        Without it the competitor grid was captured from the national SERP for every project,
        so the New York and Las Vegas grids held the same positions and, sharing one unique
        key, physically overwrote one another on each sync.
        """
        from pipeline.services.site_service import resolve_tracking_location
        return resolve_tracking_location(getattr(self, "site_pk", None), site_id)

    def _load_keywords(self, site_id: str = "", location: str = "") -> list[str]:
        """This PROJECT's tracked keywords — see dataforseo_serp._load_keywords."""
        from pipeline.utils.keywords import load_tracked_keywords
        keywords = load_tracked_keywords(site_id, location=location or None,
                                         site_pk=getattr(self, "site_pk", None))
        if not keywords:
            self.logger.warning(
                "[dataforseo_serp_competitors] No keywords in keywords.txt — nothing to track."
            )
        # Incremental sync: sync_engine may set `only_keywords` to restrict this run to the
        # keywords that actually need work (see pipeline/utils/keywords.keywords_needing_
        # backfill). DataForSEO meters per query, so re-querying every tracked keyword to
        # pick up five new ones is both slow and billable. Absent/empty => full list, so
        # the scheduled sync and every existing caller behave exactly as before.
        only = getattr(self, "only_keywords", None)
        if only:
            wanted = set(k.strip().lower() for k in only if k and k.strip())
            subset = [k for k in keywords if (k or "").strip().lower() in wanted]
            self.logger.info(
                f"[dataforseo_serp_competitors] incremental run: {len(subset)} of {len(keywords)} tracked keywords"
            )
            return subset
        return keywords

    # -- run context (attached by sync_engine._attach_run_context; absent when standalone) --

    def _priority(self) -> int:
        return NORMAL_PRIORITY if getattr(self, "scheduled", False) else TASK_PRIORITY

    def _poll_budget(self) -> tuple[int, int]:
        return _SCHEDULED_POLL_BUDGET if getattr(self, "scheduled", False) else _WATCHED_POLL_BUDGET

    def _shared_serps(self) -> Optional[list[dict]]:
        """The SERPs `dataforseo_serp` bought earlier in THIS run, or None when it did not
        run in this process (standalone use) and this connector must buy its own.

        An empty list is not None: it means the own-domain connector ran but every task was
        still pending when its poll window closed. Those SERPs are paid for and will be
        drained on the next run; buying them again here is the exact double spend this
        sharing exists to end.
        """
        shared = getattr(self, "run_shared", None)
        if not isinstance(shared, dict):
            return None
        tasks = shared.get("serp_tasks")
        return list(tasks) if isinstance(tasks, list) else None

    @with_retry(max_retries=3, base_delay=5.0)
    def _submit_tasks(self, keywords: list[str],
                      location: str = DEFAULT_LOCATION,
                      device: str = "desktop", os_name: str = "windows") -> list[str]:
        """
        Submit keywords to the Standard Queue. Unlike dataforseo_serp, we do NOT
        set a `target` or `stop_crawl_on_match` — we need the full result set so
        every competitor's position is visible.

        `location` is this project's tracking location in the SPA's display form; it is
        converted to DataForSEO's wire form here. `device`/`os_name` come from
        `_resolve_device` (dataforseo_serp) — the project's configured device, not a
        hardcoded desktop.
        """
        batch_size = 100
        task_ids: list[str] = []
        api_location = normalize_location_name(location)

        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            payload = [
                {
                    "keyword": kw,
                    "location_name": api_location,
                    "language_name": "English",
                    # The PROJECT's device (sites.device via _resolve_device), not a literal:
                    # a "Los Angeles - Mobile" project was silently tracking desktop SERPs,
                    # and Semrush reconciliation requires mirroring device.
                    "device": device,
                    "os": os_name,
                    "depth": 30,                 # top 30 — same depth as own-domain tracking
                    "calculate_rectangles": False,
                    # +$0.0006/query surcharge, auto-refunded when the SERP has no AI
                    # Overview. Makes the ai_overview item (and its citation references)
                    # available on task_get/advanced — retrieval itself is free.
                    "load_async_ai_overview": True,
                    # Priority queue when a user is watching — see TASK_PRIORITY in
                    # dataforseo_serp.py for the measurement; the normal queue when scheduled.
                    "priority": self._priority(),
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
            # Standard Queue bills at task_post — the charge is already on this envelope.
            self._run_cost += extract_cost(data)
            # Only what the API ACCEPTED — see the same guard in dataforseo_serp._submit_tasks.
            # A rejected task still returns an id, and polling it burns the whole window.
            for task in data.get("tasks", []):
                status = task.get("status_code")
                if status == TASK_CREATED and task.get("id"):
                    task_ids.append(task["id"])
                else:
                    self.logger.error(
                        "[dataforseo_serp_competitors] task_post REJECTED (%s): %s",
                        status, task.get("status_message", "no message"),
                    )
            time.sleep(0.5)

        self.logger.info(f"[dataforseo_serp_competitors] Submitted {len(task_ids)} tasks")
        return task_ids

    def _poll_and_fetch(self, task_ids: list[str], competitors: set[str], site_id: str,
                        location: str = DEFAULT_LOCATION,
                        max_polls: int | None = None, poll_interval: int | None = None) -> list[dict]:
        """Poll the queue and normalize completed tasks into competitor rows. The window
        defaults to `_poll_budget()` — longer for a scheduled run on the normal queue."""
        if max_polls is None or poll_interval is None:
            budget_polls, budget_interval = self._poll_budget()
            max_polls = budget_polls if max_polls is None else max_polls
            poll_interval = budget_interval if poll_interval is None else poll_interval
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
                    # `advanced`, not `regular`: the regular endpoint returns only
                    # organic/paid/featured_snippet — ai_overview items exist only here.
                    # Retrieval is free either way; billing happened at task_post.
                    resp = requests.get(
                        f"{DATAFORSEO_BASE}/serp/google/organic/task_get/advanced/{task_id}",
                        auth=self.auth, timeout=20,
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                    # Usually 0 on the Standard Queue, but record whatever it reports.
                    self._run_cost += extract_cost(payload)
                    task_data = payload.get("tasks", [{}])[0]
                    status_code = task_data.get("status_code", 0)
                    if status_code == TASK_OK:
                        records.extend(
                            self._normalize_task(task_data, tracking_date, competitors,
                                                 site_id, location)
                        )
                    elif status_code in TASK_PENDING:
                        still_pending.append(task_id)      # 40601/40602 — still working
                    else:
                        self.logger.error(
                            "[dataforseo_serp_competitors] Task %s failed (%s): %s", task_id,
                            status_code, task_data.get("status_message", "unknown error"),
                        )
                except Exception as exc:
                    self.logger.warning(f"[dataforseo_serp_competitors] Poll error {task_id}: {exc}")
                    still_pending.append(task_id)
            pending = still_pending

        if pending:
            self.logger.warning(
                f"[dataforseo_serp_competitors] {len(pending)} task(s) still running after "
                f"{max_polls * poll_interval}s — they stay in tasks_ready and the next run "
                f"collects them."
            )
        return records

    def _drain_ready_tasks(self, competitors: set[str], site_id: str,
                           location: str = DEFAULT_LOCATION) -> list[dict]:
        """Collect competitor SERPs this connector paid for but never fetched.

        Same contract as `dataforseo_serp._drain_ready_tasks` — read the long note there. This
        connector is where the evidence came from: 198 completed, paid-for tasks tagged
        `fusehealth_comp_*` and up to four days old were sitting uncollected in `tasks_ready`,
        because the poll loop treated `40601 Task Handed` as a permanent failure and nothing
        ever went back for them.

        Matches only the `fusehealth_comp_` tag, so it cannot consume the own-domain
        connector's results.

        Never raises.
        """
        tracking_date = yesterday()
        records: list[dict] = []
        try:
            resp = requests.get(f"{DATAFORSEO_BASE}/serp/google/organic/tasks_ready",
                                auth=self.auth, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            self._run_cost += extract_cost(data)
            ready = (data.get("tasks") or [{}])[0].get("result") or []
        except Exception as exc:
            self.logger.warning(f"[dataforseo_serp_competitors] tasks_ready lookup failed: {exc}")
            return records

        mine = [r for r in ready
                if r.get("id") and str(r.get("tag") or "").startswith("fusehealth_comp_")]
        if not mine:
            return records

        self.logger.info(f"[dataforseo_serp_competitors] Collecting {len(mine)} result(s) left "
                         f"ready by an earlier run")
        for row in mine:
            try:
                # `advanced` for the same reason as the poll loop above: ai_overview items
                # are absent from the `regular` rendering of the same paid-for task.
                resp = requests.get(
                    f"{DATAFORSEO_BASE}/serp/google/organic/task_get/advanced/{row['id']}",
                    auth=self.auth, timeout=20,
                )
                resp.raise_for_status()
                payload = resp.json()
                self._run_cost += extract_cost(payload)
                task_data = (payload.get("tasks") or [{}])[0]
                if task_data.get("status_code") == TASK_OK:
                    records.extend(self._normalize_task(task_data, tracking_date, competitors,
                                                        site_id, location))
            except Exception as exc:
                self.logger.warning(
                    f"[dataforseo_serp_competitors] Could not collect {row['id']}: {exc}")
        return records

    def _normalize_task(self, task_data: dict, tracking_date: date,
                        competitors: set[str], site_id: str,
                        location: str = DEFAULT_LOCATION) -> list[dict]:
        """
        Keep the BEST (lowest) position per (keyword, competitor) from one SERP.
        A competitor not present in the captured depth simply yields no row for
        that keyword (rendered as "—" in the grid).

        Rows carry the location they were measured in — part of their identity, so two city
        projects on one domain keep separate grids instead of overwriting each other.

        Side channel: SERP-feature items on the same (advanced) result — ai_overview,
        local_pack, featured_snippet — are appended to `self._feature_records`, one row per
        referenced domain, UNFILTERED by the tracked-competitor set. See
        SerpFeatureRanking's docstring: matching to tracked domains is a read-time
        contains-match, and the full citation list is the denominator share-of-AIO needs.
        """
        keyword = task_data.get("data", {}).get("keyword", "")
        result = task_data.get("result") or [{}]
        items = (result[0] or {}).get("items") or []

        self._extract_feature_records(items, keyword, tracking_date, site_id, location)

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
                    "location": location,
                    "position": pos,
                    "url": url,
                }
        return list(best.values())

    def _extract_feature_records(self, items: list, keyword: str, tracking_date: date,
                                 site_id: str, location: str = DEFAULT_LOCATION) -> None:
        """Append serp_feature_rankings rows for one SERP's feature items.

        ai_overview — one row per DISTINCT referenced domain. The combined, in-order
        reference list is the item's top-level `references` followed by each nested
        element's own `references`; `slot` is the 1-based order of the domain's FIRST
        appearance in that combined list (a repeat keeps its first slot).
        local_pack — one row per item that names a domain; slot = rank_group (1-3).
        featured_snippet — one row, slot 1.

        Nothing is filtered by the tracked-competitor set — every referenced domain is
        stored (see SerpFeatureRanking's docstring for why).
        """
        def _row(domain: str, feature_type: str, slot, url, title) -> dict:
            return {
                "date": tracking_date,
                "site_id": site_id,
                "keyword": keyword,
                "location": location,
                "domain": domain,
                "feature_type": feature_type,
                "slot": slot,
                "url": url,
                "title": title,
            }

        for item in items or []:
            itype = item.get("type")
            if itype == "ai_overview":
                # Combined, in-order citation list: top-level references first, then each
                # nested element's references.
                refs = list(item.get("references") or [])
                for el in item.get("items") or []:
                    refs.extend((el or {}).get("references") or [])
                seen: set[str] = set()
                for ref in refs:
                    domain = self._strip((ref or {}).get("domain")
                                         or (ref or {}).get("url") or "")
                    if not domain or domain in seen:
                        continue    # first appearance wins the slot
                    seen.add(domain)
                    self._feature_records.append(_row(
                        domain, "ai_overview", len(seen),
                        (ref or {}).get("url"), (ref or {}).get("title"),
                    ))
            elif itype == "local_pack":
                domain = self._strip(item.get("domain") or "")
                if domain:
                    self._feature_records.append(_row(
                        domain, "local_pack", item.get("rank_group"),
                        item.get("url"), item.get("title"),
                    ))
            elif itype == "featured_snippet":
                domain = self._strip(item.get("domain") or item.get("url") or "")
                if domain:
                    self._feature_records.append(_row(
                        domain, "featured_snippet", 1,
                        item.get("url"), item.get("title"),
                    ))

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Submit all tracked keywords and capture each tracked competitor's position.

        Returns rows for competitor_keyword_rankings. Returns [] (not an error)
        when there are no keywords or no tracked competitors yet.
        """
        from pipeline.services.competitor_service import get_tracked_competitors

        resolved_site_id = self._resolve_site_id(site_id)
        # site_pk, which every other read in this connector already passes. Unscoped, this
        # bought SERP captures for EVERY sibling project's competitors on the domain — and,
        # while the auto-discovery fallback existed, for whatever DataForSEO had discovered
        # too, which on a real account meant paying to track youtube.com and indeed.com.
        competitors = set(get_tracked_competitors(
            resolved_site_id, site_pk=getattr(self, "site_pk", None)))
        if not competitors:
            self.logger.warning(
                "[dataforseo_serp_competitors] No tracked competitors for "
                f"{resolved_site_id!r} (none discovered/selected yet) — nothing to capture."
            )
            return []

        location = self._resolve_location(resolved_site_id)
        # Scoped to THIS project — see dataforseo_serp.fetch().
        keywords = self._load_keywords(resolved_site_id, location)
        if not keywords:
            return []

        self.logger.info(
            f"[dataforseo_serp_competitors] Tracking {len(competitors)} competitors "
            f"across {len(keywords)} keywords for {resolved_site_id!r} @ {location!r}"
        )
        self._run_cost = 0.0
        # Reset BEFORE the drain: _normalize_task appends feature rows for every task it
        # normalizes, drained leftovers included, and a stale list from a previous fetch()
        # would re-write another run's rows under this run's summary.
        self._feature_records = []
        records: list[dict] = []
        try:
            # Leftovers an earlier run paid for and abandoned — free to collect, and the
            # reason a slow queue now costs a delay rather than the data.
            records = self._drain_ready_tasks(competitors, resolved_site_id, location)

            # ONE SERP purchase per keyword per run. When the own-domain connector ran earlier
            # in this process it bought the very SERPs this connector used to buy again — same
            # keyword, city, device and depth, with the AI Overview loaded and the ADVANCED
            # rendering fetched — so competitor ranks and SERP features are read off those.
            # Nothing is posted and nothing is billed. (2026-09-01: the duplicate purchase was
            # the largest line on the DataForSEO bill.)
            shared = self._shared_serps()
            if shared is not None:
                tracking_date = yesterday()
                for task_data in shared:
                    records.extend(self._normalize_task(task_data, tracking_date, competitors,
                                                        resolved_site_id, location))
                self.logger.info(
                    f"[dataforseo_serp_competitors] Read {len(shared)} SERP(s) bought by "
                    f"dataforseo_serp in this run — no tasks posted"
                )
                return records

            device, os_name = _resolve_device(getattr(self, "site_pk", None), resolved_site_id)
            task_ids = self._submit_tasks(keywords, location, device=device, os_name=os_name)
            if not task_ids:
                # Every task was REJECTED (each reason already logged). Raise rather than
                # return [], so the run shows `error` and its cause instead of the
                # `success, 0 records` that hid a permanently-broken payload.
                if records:
                    return records
                raise ValueError(
                    "[dataforseo_serp_competitors] DataForSEO rejected every SERP task at "
                    "submission — see the task_post errors logged above."
                )

            records += self._poll_and_fetch(task_ids, competitors, resolved_site_id, location)
        finally:
            # `units` = SERP queries posted on the fallback path (own tasks). On the shared
            # path nothing was posted, `_run_cost` is 0 and record_cost skips the row — a
            # purchase that did not happen is not a spend event.
            record_cost(
                self.name, resolved_site_id, self._run_cost,
                units=len(keywords) if self._run_cost else 0,
                notes=(f"serp/google/organic task_post+task_get, {len(competitors)} "
                       f"competitors @ {location}") if self._run_cost
                else "reused dataforseo_serp's SERPs from this run — nothing posted",
            )
        self.logger.info(
            f"[dataforseo_serp_competitors] Captured {len(records)} competitor ranking rows "
            f"and {len(self._feature_records)} SERP-feature rows"
        )
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        written = upsert_competitor_keyword_rankings(session, records, site_id=site_id)
        # Same session/write step: the feature rows _normalize_task collected alongside the
        # competitor rows. Their dicts already carry the resolved site_id (stamped in
        # _normalize_task, same as competitor rows); the writer's param only fills gaps.
        # They count toward the run's records_written — they are rows this run captured.
        feature_records = getattr(self, "_feature_records", None) or []
        if feature_records:
            written += upsert_serp_feature_rankings(session, feature_records, site_id=site_id)
        return written


if __name__ == "__main__":
    connector = DataForSEOSerpCompetitorsConnector()
    print("Loaded. To run for the active site: connector.sync()")
