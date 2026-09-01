"""
pipeline/connectors/dataforseo_serp.py — DataForSEO SERP rank tracking connector.

Fetches: daily keyword positions for the target domain.
Writes to: keyword_rankings table.

Cost: $0.003/query (Priority Queue — see TASK_PRIORITY). Live mode is not usable on this
account (`live/advanced` answers 40102 Not Enough Money regardless of balance), and the
Standard Queue is real but far too slow to finish inside a Refresh the user is watching.
Strategy: submit batch → poll every 10 s → fetch results.
Optimizations: depth=30, target=domain.

DataForSEO stores task results for 30 days, and every run drains `tasks_ready` first, so a
result that lands after this run's poll window is collected by the next one instead of paid
for and thrown away.
"""

import hashlib
import os
import time
from datetime import date
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
# One shared implementation of the SPA-form -> DataForSEO-form location converter; see the
# long note above it in dataforseo_live_serp.py for the format contract.
from pipeline.connectors.dataforseo_live_serp import normalize_location_name
from pipeline.db.schema import DEFAULT_LOCATION
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import iso, yesterday
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import SERP_MEASUREMENT_COLUMNS, upsert_keyword_rankings

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


def scope_tag(prefix: str, site_id: str, api_location: str) -> str:
    """Tag prefix identifying WHICH project's task sits in the shared `tasks_ready` list.

    The DataForSEO account is shared by every project, and `tasks_ready` only exposes a
    task's tag — fetching a task's result consumes it, so drains must decide ownership from
    the tag alone, BEFORE task_get. A date-only tag let one project's drain adopt another
    project's leftovers and stamp them with its own site/location (a cross-project
    corruption: it even recorded measured-"not ranked" rows for keywords the adopting
    project never submitted). Hashing (site_id, wire-form location) into the tag pins each
    task to the exact scope that paid for it. Same-scope runs still share leftovers, which
    is correct — the measurements are interchangeable.
    """
    digest = hashlib.sha1(f"{site_id}|{api_location}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}_"


# ── DataForSEO task status codes, and why each set matters ────────────────────────────────
#
# Getting these wrong is not cosmetic — every one of them silently cost this project real
# money for zero rows. Measured against the live API on 2026-08-06:
#
#   20100  Task Created      task_post succeeded. THE ONLY code worth polling. This connector
#                            used to append `task["id"]` for every task in the response
#                            without looking at its status, so a REJECTED task's id went into
#                            the poll list and was polled to the end of the window; the run
#                            then reported "N tasks did not complete" and wrote 0 records.
#   20000  Ok                task_get succeeded — the result is in the envelope.
#   40601  Task Handed       handed to a worker, STILL RUNNING.
#   40602  Task In Queue     queued, STILL RUNNING.
#
# 40601 was in this connector's *error* list, so a task that was merely still working was
# logged as failed and dropped — the single reason 198 completed, paid-for SERP results were
# sitting uncollected in `tasks_ready` when this was found.
TASK_CREATED = 20100
TASK_OK = 20000
TASK_PENDING = (40601, 40602)      # still working — keep polling, never discard

# Priority 2 = DataForSEO's high-priority queue, $0.003/query against Standard's $0.0015.
# The Standard Queue is not "slow but fine" here: a probe task sat at `Task Handed` for over
# five minutes, while the same keyword on priority 2 returned a full 29-item SERP in 79
# seconds. A Refresh the user is watching cannot block for an unbounded queue, and doubling
# a third of a cent per keyword to make the button actually finish is the right trade.
TASK_PRIORITY = 2

# The queue a run nobody is watching takes. A scheduled (cron) run has no progress bar and no
# user waiting, so paying double for an 80-second answer buys nothing; the normal queue costs
# half per query and `_poll_budget` waits accordingly. A task still pending when that window
# closes is not lost — `_drain_ready_tasks` collects it on the next run.
NORMAL_PRIORITY = 1

# Poll windows, (polls, seconds between polls). Priority-2 tasks measured ~80 s, so the watched
# window is generous at 4 min; the normal queue is slower and unwatched, so it gets 12.
_WATCHED_POLL_BUDGET = (24, 10)
_SCHEDULED_POLL_BUDGET = (48, 15)

# The (device, os) pairs a SERP task_post accepts. Keys are the lowercased form of
# `sites.device`; anything unrecognised (or unset) tracks the desktop SERP.
_DEVICE_PAYLOADS = {
    "mobile": ("mobile", "android"),
    "desktop": ("desktop", "windows"),
}


def _resolve_device(site_pk, site_id) -> tuple[str, str]:
    """The (device, os) a SERP capture should be posted with, for THIS project.

    Both SERP connectors used to hardcode `"device": "desktop", "os": "windows"` while
    `sites.device` sat stored-but-unread, so a "Los Angeles - Mobile" project was silently
    tracking desktop SERPs — and Semrush reconciliation requires mirroring the device the
    project declares, because mobile and desktop are different SERPs with different ranks.

    Resolution mirrors `resolve_tracking_location`: the exact project by pk first (siblings
    on one domain can differ), the domain as a fallback, desktop when nothing is configured.
    Never raises — a resolution failure must not stop a sync, so it degrades to desktop.
    """
    try:
        from pipeline.services.site_service import get_site, get_site_by_pk
        with get_session() as session:
            site = get_site_by_pk(session, site_pk) or get_site(session, site_id)
            if site:
                key = (site.device or "").strip().lower()
                if key in _DEVICE_PAYLOADS:
                    return _DEVICE_PAYLOADS[key]
    except Exception:
        import logging
        logging.getLogger("dataforseo_serp").warning(
            "[dataforseo_serp] could not resolve the project's device; tracking desktop",
            exc_info=True,
        )
    return _DEVICE_PAYLOADS["desktop"]


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
        # USD DataForSEO reported for the current fetch(). Accumulated across the
        # task_post batches and the task_get polls, written once per run in fetch().
        self._run_cost = 0.0

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
        from pipeline.services.site_service import get_site, get_site_by_pk
        with get_session() as session:
            # Prefer the exact project when the run named one: several projects can share a
            # site_url, and get_site() would return an arbitrary sibling whose
            # dataforseo_target_domain may differ.
            site = get_site_by_pk(session, getattr(self, "site_pk", None)) \
                or get_site(session, site_id)
            if site:
                target = self._strip(site.dataforseo_target_domain or site.site_url)
                return (site.site_url, target)
        return (site_id or "", self._default_target)

    def _resolve_location(self, site_id: str) -> str:
        """This PROJECT's tracking location, in the SPA's display form.

        Before this existed the payload below carried a hardcoded
        `location_name="United States"`, so every project — whatever city its wizard had
        collected — was measured against the same national SERP. That is why six Premierstaff
        city projects reported byte-identical rankings, and why a New York project ranked the
        generic homepage rather than the /event-staffing-agency-nyc/ page a New York searcher
        actually sees.
        """
        from pipeline.services.site_service import resolve_tracking_location
        return resolve_tracking_location(getattr(self, "site_pk", None), site_id)

    def _load_keywords(self, site_id: str = "", location: str = "") -> list[str]:
        """This PROJECT's tracked keywords (falls back to keywords.txt only when unscoped)."""
        from pipeline.utils.keywords import load_tracked_keywords
        keywords = load_tracked_keywords(site_id, location=location or None,
                                         site_pk=getattr(self, "site_pk", None))
        if keywords:
            # NOT keywords.txt. The tracked list comes from `saved_keywords` — what the user
            # sent from the Keyword Explorer — and the file is a legacy fallback used only for
            # an unscoped call. Naming the wrong source sends anyone debugging an empty run to
            # edit a file that nothing reads.
            self.logger.info(f"[dataforseo_serp] Loaded {len(keywords)} tracked keywords")
        else:
            self.logger.warning(
                "[dataforseo_serp] No keywords in keywords.txt — nothing will be tracked."
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
                f"[dataforseo_serp] incremental run: {len(subset)} of {len(keywords)} tracked keywords"
            )
            return subset
        return keywords

    # -- run context (attached by sync_engine._attach_run_context; absent when standalone) --

    def _priority(self) -> int:
        return NORMAL_PRIORITY if getattr(self, "scheduled", False) else TASK_PRIORITY

    def _poll_budget(self) -> tuple[int, int]:
        """(max_polls, poll_interval) for this run — longer when nobody is watching."""
        return _SCHEDULED_POLL_BUDGET if getattr(self, "scheduled", False) else _WATCHED_POLL_BUDGET

    def _publish(self, task_data: dict) -> None:
        """Hand a completed SERP to the rest of this run.

        `dataforseo_serp_competitors` reads competitor ranks, SERP features and AI Overview
        citations off exactly these results instead of buying the identical SERP a second
        time — the reason this connector now fetches the ADVANCED rendering with the AI
        Overview loaded. No-op outside a sync run (no `run_shared` attached).
        """
        shared = getattr(self, "run_shared", None)
        if isinstance(shared, dict):
            shared.setdefault("serp_tasks", []).append(task_data)

    @with_retry(max_retries=3, base_delay=5.0)
    def _submit_tasks(self, keywords: list[str], target_domain: str,
                      location: str = DEFAULT_LOCATION,
                      device: str = "desktop", os_name: str = "windows") -> list[str]:
        """
        Submit keywords to DataForSEO Standard Queue for a specific target domain.
        Batch up to 100 keywords per request for efficiency.

        `location` is this project's tracking location in the SPA's display form
        ("United States - Las Vegas, NV"); it is converted to DataForSEO's wire form here.
        `device`/`os_name` come from `_resolve_device` — the project's configured device,
        not a hardcoded desktop (see that function for what hardcoding it cost).

        Returns:
            List of task_ids to poll.
        """
        # DataForSEO accepts up to 100 tasks per POST request
        batch_size = 100
        task_ids = []
        # "United States - Las Vegas, NV" -> "Las Vegas,Nevada,United States". The API rejects
        # the SPA's dash form outright, so this conversion is what makes a city SERP possible
        # at all rather than a nicety.
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
                    "target": target_domain,         # Per-site target (resolved from Site row)
                    # NO `stop_crawl_on_match`. The API rejects it outright —
                    # `40501 Invalid Field: 'stop_crawl_on_match'` — so EVERY task this
                    # connector ever posted was refused at submission. It was described in this
                    # file's header as a cost optimisation; it was in fact the reason position
                    # tracking produced nothing.
                    "depth": 30,                     # Top 30 only (not 100)
                    "calculate_rectangles": False,   # Not needed
                    # +$0.0006/query, refunded by DataForSEO when the SERP has no AI
                    # Overview. This purchase is now the ONLY SERP purchase per keyword —
                    # the competitor connector reads off it (see _publish) — so the AI
                    # Overview it used to load on its own duplicate task is loaded here.
                    "load_async_ai_overview": True,
                    "priority": self._priority(),    # watched: fast queue; scheduled: normal
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

            # The queue bills at task_post; the charge for this batch of task submissions is
            # on the envelope we already have.
            self._run_cost += extract_cost(data)

            # Only queue what the API actually ACCEPTED. A rejected task still comes back with
            # an id and a 4xx status, and taking the id regardless is what turned a one-line
            # field error into a five-minute poll of tasks that did not exist. The rejection
            # reason is logged per task, because "0 records" with no reason is what let this
            # survive: the envelope says 20000 Ok even when every task inside it failed.
            for task in data.get("tasks", []):
                status = task.get("status_code")
                if status == TASK_CREATED and task.get("id"):
                    task_ids.append(task["id"])
                else:
                    self.logger.error(
                        "[dataforseo_serp] task_post REJECTED (%s): %s",
                        status, task.get("status_message", "no message"),
                    )

            self.logger.debug(f"[dataforseo_serp] Submitted batch {i//batch_size + 1}: {len(batch)} keywords")
            time.sleep(0.5)  # Brief pause between batch submissions

        self.logger.info(f"[dataforseo_serp] Submitted {len(task_ids)} tasks to Standard Queue")
        return task_ids

    def _poll_and_fetch(
        self,
        task_ids: list[str],
        target_domain: str,
        site_id: str,
        location: str = DEFAULT_LOCATION,
        max_polls: int | None = None,
        poll_interval: int | None = None,
    ) -> list[dict]:
        """
        Poll the queue for completed tasks.
        Measured completion time on priority 2: ~80 s. Max wait: max_polls x poll_interval,
        defaulting to `_poll_budget()` — longer for a scheduled run on the normal queue.

        A task still pending when the window closes is NOT lost — it stays in DataForSEO's
        `tasks_ready` list for 30 days and the next run's `_drain_ready_tasks()` collects it.

        Reads the ADVANCED rendering (free — billing happened at task_post): the organic
        items this connector needs are identical, and the AI Overview / feature items that
        only exist there are what the competitor connector reads off the published result.

        Returns:
            Normalized records for keyword_rankings table.
        """
        if max_polls is None or poll_interval is None:
            budget_polls, budget_interval = self._poll_budget()
            max_polls = budget_polls if max_polls is None else max_polls
            poll_interval = budget_interval if poll_interval is None else poll_interval
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
                        f"{DATAFORSEO_BASE}/serp/google/organic/task_get/advanced/{task_id}",
                        auth=self.auth,
                        timeout=20,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    # Usually 0 (the Standard Queue charged at task_post) but retrieval
                    # is billable on some endpoints, so take whatever it reports.
                    self._run_cost += extract_cost(data)

                    task_data = data.get("tasks", [{}])[0]
                    status_code = task_data.get("status_code", 0)

                    if status_code == TASK_OK:
                        task_records = self._normalize_task(task_data, tracking_date,
                                                            target_domain, site_id, location)
                        records.extend(task_records)
                        self._publish(task_data)
                    elif status_code in TASK_PENDING:
                        still_pending.append(task_id)      # 40601/40602 — still working
                    else:
                        # A real failure (auth, not found, out of funds). Logged at ERROR, not
                        # WARNING: this is money spent for no row, and it needs to be visible
                        # in Settings -> Connections rather than buried.
                        self.logger.error(
                            "[dataforseo_serp] Task %s failed (%s): %s", task_id, status_code,
                            task_data.get("status_message", "unknown error"),
                        )

                except Exception as exc:
                    self.logger.warning(f"[dataforseo_serp] Poll error for {task_id}: {exc}")
                    still_pending.append(task_id)

            pending = still_pending

        if pending:
            self.logger.warning(
                f"[dataforseo_serp] {len(pending)} task(s) still running after "
                f"{max_polls * poll_interval}s — they stay in tasks_ready and the next run "
                f"collects them. Task IDs: {pending[:5]}"
            )

        return records

    def _drain_ready_tasks(self, target_domain: str, site_id: str,
                           location: str = DEFAULT_LOCATION) -> list[dict]:
        """Collect results this connector paid for but never fetched, from `tasks_ready`.

        WHY THIS EXISTS. A queued task's result waits in DataForSEO's `tasks_ready` list for 30
        days after it completes. Nothing here ever read that list, so any task that finished
        after its run's poll window closed was simply abandoned — bought and binned. When this
        was written there were **198 completed, paid-for SERP results** sitting in that list,
        the oldest four days old, because the poll loop also mistook `40601 Task Handed` for a
        permanent failure.

        Running this at the START of every fetch makes the poll window a best-effort
        optimisation rather than a deadline: a slow task costs a delay, never a row.

        Only this connector's own tasks are taken (`fusehealth_` tag, which
        `dataforseo_serp_competitors` deliberately does not share — its tag is `fusehealth_comp_`),
        so two connectors draining the same list cannot steal each other's results.

        Never raises: a failure to collect leftovers must not stop the fresh submission below.
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
            self.logger.warning(f"[dataforseo_serp] tasks_ready lookup failed: {exc}")
            return records

        mine = [r for r in ready
                if r.get("id") and str(r.get("tag") or "").startswith("fusehealth_")
                and not str(r.get("tag") or "").startswith("fusehealth_comp_")]
        if not mine:
            return records

        self.logger.info(f"[dataforseo_serp] Collecting {len(mine)} result(s) left ready by an "
                         f"earlier run")
        for row in mine:
            try:
                resp = requests.get(
                    f"{DATAFORSEO_BASE}/serp/google/organic/task_get/advanced/{row['id']}",
                    auth=self.auth, timeout=20,
                )
                resp.raise_for_status()
                payload = resp.json()
                self._run_cost += extract_cost(payload)
                task_data = (payload.get("tasks") or [{}])[0]
                if task_data.get("status_code") == TASK_OK:
                    records.extend(self._normalize_task(task_data, tracking_date,
                                                        target_domain, site_id, location))
                    self._publish(task_data)
            except Exception as exc:
                self.logger.warning(f"[dataforseo_serp] Could not collect {row['id']}: {exc}")
        return records

    def _normalize_task(self, task_data: dict, tracking_date: date,
                        target_domain: str, site_id: str,
                        location: str = DEFAULT_LOCATION) -> list[dict]:
        """
        Extract keyword + position from a completed SERP task result.
        Returns at most one record per keyword (our domain's position).
        Tags every record with site_id AND the location it was measured in — both are part
        of the row's identity, so two city projects on one domain no longer overwrite each
        other's ranks (see KeywordRanking.location).
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
                "location": location,
                "position": item.get("rank_absolute"),
                "url": url,
                "search_volume": None,   # Will be enriched by Keywords connector
                "keyword_difficulty": None,
                "cpc": None,
                # This connector looked at the SERP — see KeywordRanking.rank_checked_at.
                "rank_checked_at": tracking_date,
            }]

        # Domain not found in top 30 — record as not ranking
        return [{
            "date": tracking_date,
            "site_id": site_id,
            "keyword": keyword,
            "location": location,
            "position": None,  # Not ranked in top 30
            "url": None,
            "search_volume": None,
            "keyword_difficulty": None,
            "cpc": None,
            # THE WHOLE POINT OF THIS COLUMN. `position: None` here is a MEASURED result —
            # the SERP was fetched to depth 30 and this domain is not in it — and it is
            # indistinguishable by any other column from a row that was merely priced by
            # dataforseo_keywords and never rank-checked at all. Without this stamp the
            # Positioning page filed a just-measured keyword back under "Not Tracked Yet".
            "rank_checked_at": tracking_date,
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

        location = self._resolve_location(resolved_site_id)
        # Scoped to THIS project. Several projects share one site_url (one per market), each
        # with its own tracked list, so an unscoped load would make every project pay to
        # re-measure its siblings' keywords as well as its own.
        keywords = self._load_keywords(resolved_site_id, location)
        if not keywords:
            self.logger.warning(
                "[dataforseo_serp] This project tracks no keywords yet — add some from the "
                "Keyword Explorer. (Not a keywords.txt problem: that file is a legacy "
                "fallback this project-scoped call deliberately skips.)"
            )
            return []

        self.logger.info(
            f"[dataforseo_serp] Tracking {len(keywords)} keywords for {target_domain} "
            f"@ {location!r}"
        )
        self._run_cost = 0.0
        records: list[dict] = []
        # Declare the shared SERP list up front, even if it stays empty: its PRESENCE is how
        # the competitor connector knows this connector ran in this process and must not buy
        # the SERPs itself — an empty list means "paid for, still pending, drained next run".
        shared = getattr(self, "run_shared", None)
        if isinstance(shared, dict):
            shared.setdefault("serp_tasks", [])
        try:
            # Leftovers first: results an earlier run paid for and never collected. Free —
            # task_get on an already-charged task costs nothing — and it means a slow queue
            # delays a number rather than losing it.
            records = self._drain_ready_tasks(target_domain, resolved_site_id, location)

            device, os_name = _resolve_device(getattr(self, "site_pk", None), resolved_site_id)
            task_ids = self._submit_tasks(keywords, target_domain, location,
                                          device=device, os_name=os_name)
            if not task_ids:
                # Not "no response" — every task was REJECTED, and _submit_tasks has already
                # logged each rejection reason. Raise instead of returning [], so the run is
                # marked `error` and says why in Settings -> Connections. Returning an empty
                # list here reported `success, 0 records` and is exactly how a payload the API
                # refuses on every single call went unnoticed.
                if records:
                    return records          # leftovers are still a real result
                raise ValueError(
                    "[dataforseo_serp] DataForSEO rejected every SERP task at submission — "
                    "see the task_post errors logged above."
                )

            records += self._poll_and_fetch(task_ids, target_domain, resolved_site_id, location)
        finally:
            # One row per run. `units` = SERP queries posted: what this endpoint meters
            # ($0.003/query on the priority queue). Recorded in `finally` so a run that blew
            # up mid-poll still books the queries it already paid for.
            record_cost(
                self.name, resolved_site_id, self._run_cost, units=len(keywords),
                notes=f"serp/google/organic task_post+task_get for {target_domain} @ {location}",
            )
        self.logger.info(f"[dataforseo_serp] Retrieved {len(records)} ranking records for {target_domain}")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        # This connector INSPECTED the SERP, so the columns it owns are written unconditionally
        # rather than COALESCEd. It captures to depth 30 and writes `position: None` when the
        # domain is not in it — a measured absence, not a gap. Under the default COALESCE that
        # None was discarded and the row kept whatever rank it already held, while
        # `rank_checked_at` was stamped fresh on top: a keyword that fell off page one on a day
        # it had previously been recorded at #4 went on reporting #4, marked freshly checked,
        # permanently. See writer.SERP_MEASUREMENT_COLUMNS.
        return upsert_keyword_rankings(session, records, site_id=site_id,
                                       overwrite_columns=SERP_MEASUREMENT_COLUMNS)


if __name__ == "__main__":
    connector = DataForSEOSERPConnector()
    keywords = connector._load_keywords()
    print(f"Keywords loaded: {len(keywords)}")
    if keywords:
        print(f"First 5: {keywords[:5]}")
        print("\nTo run a full sync: connector.sync()")
