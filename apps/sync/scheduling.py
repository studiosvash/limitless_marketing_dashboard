"""Cadence arithmetic for the Settings -> Automation sync schedule, plus the reaper for
orphaned RefreshRun rows.

WHY this module exists
----------------------
Settings -> Automation has always persisted a cadence per module in
`ProjectSettings.data["syncConfig"]` ({"positions": "weekly", "audit": "monthly", ...}) and
nothing ever read it: there is no Celery, no cron, no scheduler anywhere in this repo, so
`settings_service._sync_summary_raw()` honestly reported `next_run: None` and the panel said
"not yet scheduled".

This module is the single place that turns a cadence + real run history into an answer to
"is this module due?" / "when does it next run?". Two callers share it deliberately, so the
date Settings shows and the decision the scheduler makes can never drift apart:

    apps/sync/management/commands/run_scheduled_syncs.py  -> due_modules() / reap_orphaned_runs()
    apps/dashboard/services/settings_service.py           -> schedule_summary()

Nothing here calls an external API or starts a sync; it only reads RefreshRun history and
`syncConfig`. Starting a sync stays the job of the existing
`apps.dashboard.services.sync_api_service.start_sync_run`.
"""
from __future__ import annotations

import logging
import os
import signal
import sys
from datetime import datetime, timedelta

from django.utils import timezone

from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus
from pipeline.services.sync_engine import ALL_CONNECTORS, PAGE_CONNECTORS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Modules and cadences
# ---------------------------------------------------------------------------

# The keys the Settings -> Automation UI writes into `syncConfig`. These are also the
# scope strings the SPA POSTs to /api/projects/<slug>/sync, so they are passed straight to
# start_sync_run() -- which owns the aliases that differ from the engine's page key
# (positions -> positioning, organic -> seo; see sync_api_service.SCOPE_ALIASES). Kept as an
# ordered tuple because it doubles as the tie-break order when two modules come due in the
# same hour.
#
# `organic` was added 2026-08-18 and is the reason this comment is worth reading. The list was
# ("positions", "backlinks", "audit", "keywords", "ads", "ai") -- six modules whose connector
# lists between them contain `gsc_keywords`, `gsc_pages` and `ga4`, but NOT plain `gsc`. `gsc`
# is the connector that writes `seo_daily_totals`, i.e. the organic clicks / impressions /
# average position the dashboard OPENS on. So the headline number had no cadence that could
# refresh it: it moved only when a human pressed "Refresh all". On premierstaff.com it sat
# three weeks stale while every module the user HAD scheduled ran exactly as promised, and the
# Overview's own "7d" window -- which anchors to the newest stored date, not to today --
# silently drifted three weeks behind Search Console's own 7-day report.
#
# It is deliberately FIRST in the tuple. The command starts at most one module per site per
# tick, and ties are broken by this order; `organic` is two free, fast API calls (no DataForSEO
# meter, no crawl), so letting it win a tie costs nothing and keeps the most-looked-at number
# on the most-frequent clock.
SYNC_MODULES: tuple[str, ...] = (
    "organic", "positions", "backlinks", "audit", "keywords", "ads", "ai",
)

# Cadence code -> how long a successful run stays "fresh". These are exactly the values the
# Settings dropdowns emit (see settings_service._CADENCE_LABELS).
#
# `monthly` is 30 days rather than a calendar month on purpose: a calendar month would make
# the due date drift with month length and would need a "same day-of-month" rule for the 31st.
# A fixed 30-day window is what the user actually asked for ("about once a month") and is
# trivially explainable in the UI.
#
# `manual` maps to None and is the load-bearing case: a module set to manual must NEVER be
# started automatically and must NEVER be given a fabricated next-run date.
CADENCE_INTERVALS: dict[str, timedelta | None] = {
    "12h": timedelta(hours=12),
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "biweekly": timedelta(days=14),
    "monthly": timedelta(days=30),
    "manual": None,
}

# A module whose connectors are all part of sync_all()'s connector list is genuinely refreshed
# by a scope='all' run, so an "all" run must count as a run of that module -- otherwise the
# scheduler would re-sync `positions` an hour after the user pressed "Refresh all", double-
# spending DataForSEO credits on data that is already fresh.
#
# `ads` is the module this deliberately excludes: PAGE_CONNECTORS["ads"] contains
# `google_ads`, which is NOT in ALL_CONNECTORS, so a full refresh never actually pulls Ads
# data and must not be allowed to reset the Ads clock.
# Mirrors sync_api_service.SCOPE_ALIASES. It is a copy rather than an import because
# sync_api_service pulls in the whole sync stack and this module is reached from
# AppConfig-adjacent code paths; `test_scheduling.ScopeAliasMirrorTests` asserts the two agree,
# so the copy cannot drift without a test failing.
_SCOPE_TO_PAGE_KEY = {"positions": "positioning", "organic": "seo"}


def _covered_by_all_scope(module: str) -> bool:
    connectors = PAGE_CONNECTORS.get(_SCOPE_TO_PAGE_KEY.get(module, module), [])
    # A module with no connectors at all is not "covered" by anything -- there is nothing to run.
    return bool(connectors) and set(connectors) <= set(ALL_CONNECTORS)


def _covered_by_core_scope(module: str) -> bool:
    """Same reasoning as `_covered_by_all_scope`, for the topbar's 'core' refresh (2026-08-31):
    a 'core' run really does fetch organic/backlinks/audit, so it must reset those modules'
    clocks -- otherwise the scheduler re-buys data the button just fetched."""
    connectors = PAGE_CONNECTORS.get(_SCOPE_TO_PAGE_KEY.get(module, module), [])
    return bool(connectors) and set(connectors) <= set(PAGE_CONNECTORS.get("core", []))


# ---------------------------------------------------------------------------
# Orphaned-run reaping
# ---------------------------------------------------------------------------

# A run can still stop reporting without finishing -- the machine is rebooted, the process is
# OOM-killed, the run wedges inside a connector -- and the row then sits at status='running'
# forever: the SPA polls /api/tasks/<id> and never sees `done`, and the per-site "already
# running?" guard blocks the site permanently.
#
# Since start_sync_run() moved the sync into its own process (RefreshRun.pid), the pid check in
# reap_orphaned_runs() catches most of these within one tick. THIS timeout is the fallback for
# the cases the pid cannot answer: rows with no pid, and a process that is alive but stuck.
#
# The timeout is picked from the real worst case of a scope='all' run, adding up the
# connectors' own hard limits rather than guessing:
#     pagespeed              self-capped by RUN_BUDGET_SECONDS, checked before each page ~ 1800s
#     dataforseo_serp        20 polls x 15s + per-task task_get calls                  ~  600s
#     dataforseo_serp_comp.  same polling budget                                       ~  600s
#     dataforseo_onpage      600s crawl poll + 3 x 30s requests                        ~  690s
#     url_inspection         50 pages x (request + 0.2s pacing)                        ~  300s
#     domain_checks          6 probes in parallel at a 3.5s timeout each               ~    4s
#     the 10 remaining connectors at their 30-60s request timeouts                     ~  450s
#     post-sync rebuild: aggregates + anomalies + technical issues + AI summary        ~  120s
#                                                                            total    ~ 4550s (~76 min)
#
# The pagespeed line is a real ceiling now, not an estimate that could be exceeded. It used to
# read "15 pages x (60s request + 60s retry)  ~1950s", which understated the shipped worst case
# by 2x: the connector scanned each page twice (mobile AND desktop), so 15 pages was 30 requests
# and ~3900s, and raising its page coverage would have silently pushed a slow run past this
# timeout and had it reaped as dead. It now scans mobile only and stops on its own wall clock
# (pipeline/connectors/pagespeed.py RUN_BUDGET_SECONDS), so page count no longer enters this sum
# at all — covering more pages costs coverage inside that budget, never more time.
#
# 2 hours is ~1.5x that absolute worst case, so a legitimately slow run is never killed, while
# a genuinely dead row is cleared within one or two scheduler ticks instead of never. It is
# deliberately NOT much larger: every hour a dead row survives is an hour of automation lost.
RUN_TIMEOUT = timedelta(hours=2)

# WHY: reaping is a best-effort correction, not proof the run failed -- the row is marked
# `error` so the SPA stops polling and the scheduler unblocks. The message says exactly that,
# because "sync failed" would be a claim we cannot support.
REAP_MESSAGE = (
    "Sync did not report a result within {hours:.0f}h and was marked failed by the scheduler. "
    "The most likely cause is a server restart while the sync was running. Re-run the refresh "
    "to try again."
)

# Shown on a connector row (SyncLog) whose sync process died mid-connector. Deliberately says
# what is and is not known: the connector may well have written rows before it was killed (both
# pagespeed and url_inspection had), so this must not read as "this connector produced nothing".
ORPHANED_CONNECTOR_MESSAGE = (
    "This connector was still running when its sync process ended, and never reported a "
    "result — most likely a server restart mid-sync. Any rows it had already written were "
    "kept. Re-run the refresh to complete it."
)

# The same situation as ORPHANED_CONNECTOR_MESSAGE -- a connector's SyncLog row left at
# `running` because its process died mid-connector -- but with a KNOWN, deliberate cause.
# Reporting a user's own Stop click as an infrastructure failure is how the next person
# spends an hour looking for a server problem that never happened.
CANCELLED_CONNECTOR_MESSAGE = (
    "This connector was running when the refresh was cancelled, so it never reported a "
    "result. Any rows it had already written were kept. Run the refresh again to complete it."
)

# Used when the pid is gone: this is not a guess, so it does not hedge.
DEAD_PROCESS_MESSAGE = (
    "The sync process (pid {pid}) is no longer running but never reported a result. It was most "
    "likely killed by a server restart or deploy. Re-run the refresh to try again."
)

# A just-spawned run has a NULL pid for a moment: start_sync_run creates the row, THEN spawns
# the process and writes the pid back. Without this grace period the reaper could look at that
# row mid-spawn, see no pid, and kill a run that was about to start.
PID_GRACE = timedelta(minutes=2)


def _windows_process_alive(pid: int) -> bool:
    """Ask the Win32 API directly whether `pid` exists.

    `os.kill` cannot be used here — see `_process_alive`. OpenProcess answers the question
    without touching the process: a handle means it exists, ERROR_ACCESS_DENIED means it exists
    but belongs to someone else, and ERROR_INVALID_PARAMETER means there is no such pid.

    (A process that exited with code 259 is indistinguishable from a running one, because 259 is
    STILL_ACTIVE. That collision keeps us on the True side, which is the bias this whole function
    is built around, and RUN_TIMEOUT still catches it.)
    """
    import ctypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    ERROR_ACCESS_DENIED = 5
    STILL_ACTIVE = 259

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ctypes.get_last_error() == ERROR_ACCESS_DENIED
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return True          # the handle opened, so it exists; the read is what failed
        return code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def _process_alive(pid: int) -> bool:
    """Is this pid a live process? Returns True on any uncertainty.

    Biased towards True on purpose: wrongly declaring a live 30-minute sync dead is far worse
    than leaving a dead row for the RUN_TIMEOUT fallback to clear.

    The pid-reuse race (the OS recycling a pid onto an unrelated process) is not worth
    defending against here: it would make us keep waiting for a run that is already dead, and
    the timeout catches that anyway.

    **`os.kill(pid, 0)` is POSIX-only and must never run on Windows.** CPython maps any signal
    other than CTRL_C_EVENT/CTRL_BREAK_EVENT onto TerminateProcess, so on Windows the "existence
    check" *terminates the process it is asking about* — and this function is reached from every
    GET /api/sync/active, i.e. every few seconds while a sync is running. It also raised
    OSError(WinError 87) for an unknown pid, which the old bare `except Exception: return True`
    swallowed, so dead runs were never reaped either. Both halves are fixed by not going near
    os.kill on Windows.
    """
    try:
        import psutil  # type: ignore[import]
        return bool(psutil.pid_exists(pid))
    except ImportError:
        pass

    if sys.platform == "win32":
        try:
            return _windows_process_alive(pid)
        except Exception:
            logger.warning("[scheduler] Windows liveness check failed for pid %s", pid,
                           exc_info=True)
            return True

    if hasattr(os, "kill"):
        try:
            os.kill(pid, 0)      # signal 0 = existence check only (POSIX semantics)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True          # exists, owned by someone else
        except Exception:
            return True
    return True


def _windows_terminate(pid: int) -> bool:
    """Kill `pid` through the Win32 API. Returns True if it is now gone.

    Deliberately explicit rather than relying on `os.kill`'s accidental mapping onto
    TerminateProcess. `_process_alive` documents at length why that mapping is a trap; a
    kill path that depends on the same trap would be one refactor away from becoming a
    liveness check again.
    """
    import ctypes

    PROCESS_TERMINATE = 0x0001
    ERROR_INVALID_PARAMETER = 87

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if not handle:
        # No such pid means the job is already done; anything else means we could not.
        return ctypes.get_last_error() == ERROR_INVALID_PARAMETER
    try:
        return bool(kernel32.TerminateProcess(handle, 1))
    finally:
        kernel32.CloseHandle(handle)


def terminate_sync_process(pid: int | None) -> bool:
    """Stop the `manage.py run_sync` process behind a cancelled run.

    Returns True when we believe the process is gone (including "it had already exited").
    False means we could not kill it -- which is not fatal: cancellation sets
    RefreshRun.status='cancelled' FIRST, and sync_all/sync_page re-read that between
    connectors, so an unkillable process still stops before the next connector. The kill
    is what makes Stop feel immediate rather than "immediate once this 600-second
    DataForSEO poll finishes".

    Callers must only reach here after a conditional status update changed exactly one
    row -- that is the pid-reuse guard. Without it, a recycled pid means killing an
    unrelated process.

    **This is NOT a liveness check.** See `_process_alive` for why the two must stay
    apart on Windows.
    """
    if not pid or pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            return _windows_terminate(pid)
        except Exception:
            logger.warning("[sync] Windows terminate failed for pid %s", pid, exc_info=True)
            return False

    try:
        # SIGTERM, not SIGKILL: run_sync holds no lock and buffers no analytics writes, so
        # the default terminate is enough and leaves a clean exit in the per-run log file.
        # The child is its own session (start_new_session=True) but spawns no children of
        # its own -- connectors are in-process HTTP calls -- so the bare pid is the whole
        # process tree.
        os.kill(pid, signal.SIGTERM)
        return True
    except ProcessLookupError:
        return True          # already gone; the outcome we wanted
    except Exception:
        logger.warning("[sync] could not terminate pid %s", pid, exc_info=True)
        return False


def reap_orphaned_runs(now: datetime | None = None, dry_run: bool = False) -> list[RefreshRun]:
    """Resolve every RefreshRun stuck at `running` that cannot still be making progress.

    Two independent reasons a row gets reaped:

    1. **Its process is gone.** Since syncs run as `manage.py run_sync` in their own process
       (RefreshRun.pid), a missing pid is direct evidence, not an inference — so these are
       cleared within one tick instead of after RUN_TIMEOUT. This is the case that used to hurt
       most: a deploy mid-sync left the row 'running' for two hours, the SPA polled a frozen
       progress bar the whole time, and the scheduler treated the site as busy.
    2. **It has exceeded RUN_TIMEOUT.** The fallback, for rows with no pid (created before the
       field existed, or caught mid-spawn) and for a process that is alive but wedged.

    Returns the affected rows (fetched before the update, so callers can log them). With
    dry_run=True nothing is written and the rows are only reported.

    Safe to call concurrently and repeatedly: every UPDATE is filtered on status='running', so a
    run that finishes between the SELECT and the UPDATE is left alone, and a second pass finds
    nothing to do.
    """
    now = now or timezone.now()

    timed_out = list(
        RefreshRun.objects.filter(status=RefreshStatus.RUNNING, started_at__lt=now - RUN_TIMEOUT)
    )
    timed_out_ids = {r.pk for r in timed_out}

    # Candidates for the pid check: still running, young enough that the timeout hasn't caught
    # them, and past the spawn grace period.
    dead: list[RefreshRun] = [
        r for r in RefreshRun.objects.filter(
            status=RefreshStatus.RUNNING, started_at__lt=now - PID_GRACE,
        ).exclude(pk__in=timed_out_ids)
        if r.pid and not _process_alive(r.pid)
    ]

    stale = timed_out + dead
    if not stale or dry_run:
        # Still sweep the connector rows. An orphaned SyncLog outlives the run it belonged to
        # (that run is already `error`), so gating this on "was anything reaped this tick?"
        # would leave every row orphaned before today stuck at `running` for good.
        reconcile_orphaned_sync_logs(dry_run=dry_run)
        return stale

    if timed_out:
        RefreshRun.objects.filter(
            pk__in=timed_out_ids, status=RefreshStatus.RUNNING
        ).update(
            status=RefreshStatus.ERROR,
            current_connector=None,
            finished_at=now,
            error_message=REAP_MESSAGE.format(hours=RUN_TIMEOUT.total_seconds() / 3600),
        )
    for run in dead:
        RefreshRun.objects.filter(pk=run.pk, status=RefreshStatus.RUNNING).update(
            status=RefreshStatus.ERROR,
            current_connector=None,
            finished_at=now,
            error_message=DEAD_PROCESS_MESSAGE.format(pid=run.pid),
        )

    for run in stale:
        logger.warning(
            "[scheduler] Reaped orphaned RefreshRun#%s (%s@%s) started %s pid=%s reason=%s",
            run.pk, run.scope, run.site_url, run.started_at.isoformat(), run.pid,
            "timeout" if run.pk in timed_out_ids else "dead-process",
        )

    # AFTER the reap, so the connector that died inside a run just cleared is cleared by this
    # same tick rather than the next one.
    reconcile_orphaned_sync_logs()
    return stale


def reconcile_orphaned_sync_logs(
    dry_run: bool = False,
    site_url: str | None = None,
    message: str = ORPHANED_CONNECTOR_MESSAGE,
) -> list[SyncLog]:
    """Resolve every SyncLog row stuck at `running` whose sync can no longer be in flight.

    Reaping the RefreshRun was only half the job. A connector's own row is set to `running` by
    BaseConnector.sync() on the way in and rewritten on the way out; when the sync process is
    killed in between, nothing rewrites it and -- unlike RefreshRun -- nothing ever reaped it.
    The row stayed `running` permanently, and since Settings -> Data pipeline reads SyncLog,
    the connector that happened to be in flight when the process died reported "Last synced:
    never" forever. On premierstaff.com that was pagespeed and url_inspection, stuck since
    three consecutive audit runs were killed by server restarts on 2026-07-24, while
    `page_speed` held 96 real Lighthouse rows written by those very runs.

    "Can no longer be in flight" is decided by exactly one fact, not by a timeout: the site has
    no RefreshRun at `running`. That is sound because connector.sync() is reachable only
    through sync_engine.sync_all/sync_page, both of which require a run_id, and start_sync_run
    creates the RefreshRun row BEFORE spawning the process -- so a live connector always has a
    live run behind it. Running this AFTER the reap in the same tick is what lets a just-reaped
    run's connector be cleared immediately rather than on the following tick.

    Only `status` and `error_message` are written. `records_written` and `last_synced` are left
    exactly as they are: what a killed run managed to write before dying is a real measurement,
    and erasing it would trade one false "never" for another.

    `site_url` scopes the sweep to one project, and `message` says why. Both exist for
    cancellation: cancelling site A must not relabel site B's genuinely-orphaned rows
    with "you cancelled this". Called with neither, the behaviour is unchanged -- which
    is what the scheduler's own periodic call relies on.
    """
    live_sites = set(
        RefreshRun.objects.filter(status=RefreshStatus.RUNNING).values_list("site_url", flat=True)
    )
    candidates = SyncLog.objects.filter(status=SyncStatus.RUNNING).exclude(site_url__in=live_sites)
    if site_url is not None:
        candidates = candidates.filter(site_url=site_url)
    orphaned = list(candidates)
    if not orphaned or dry_run:
        return orphaned

    # Filtered on status='running' again so a connector that finishes between the SELECT and the
    # UPDATE keeps its own result -- the same concurrency rule reap_orphaned_runs() follows.
    SyncLog.objects.filter(
        pk__in=[log.pk for log in orphaned], status=SyncStatus.RUNNING
    ).update(status=SyncStatus.ERROR, error_message=message)

    for log in orphaned:
        logger.warning(
            "[scheduler] Reconciled orphaned SyncLog %s@%s (records_written=%s kept)",
            log.connector, log.site_url, log.records_written,
        )
    return orphaned


def is_sync_running(site_url: str, ignore_ids: list[int] | None = None) -> bool:
    """True if this site already has a RefreshRun in flight. Callers should reap first, so a
    row orphaned by a restart does not block the site forever.

    `ignore_ids` exists for --dry-run: a dry run does not write the reap, so without it the
    dry run would report "already running" for rows a real run would just have cleared, i.e.
    it would predict the opposite of what actually happens.
    """
    qs = RefreshRun.objects.filter(site_url=site_url, status=RefreshStatus.RUNNING)
    if ignore_ids:
        qs = qs.exclude(pk__in=ignore_ids)
    return qs.exists()


# ---------------------------------------------------------------------------
# Cadence arithmetic
# ---------------------------------------------------------------------------

# WHY a separate backoff from the cadence: a run finishes `error` whenever ANY connector
# errored (sync_engine sets final_status that way), which is the normal steady state for a
# site with one unconfigured credential. Anchoring "due" on the last SUCCESS alone would then
# re-run that scope every single hour forever, burning metered DataForSEO calls on a failure
# that is not going to fix itself. A failed attempt therefore also holds the module off for
# this long -- long enough to stop the hammering, short enough that a transient outage still
# recovers the same day.
FAILED_RUN_BACKOFF = timedelta(hours=6)


def get_sync_config(site_url: str) -> dict:
    """This site's `syncConfig`, merged over the shipped defaults so a partially-saved blob
    (or no blob at all) still yields a cadence for every module."""
    # Imported lazily: settings_service imports this module back for its schedule summary, and
    # it pulls in SQLAlchemy + the accounts models, which we do not want at AppConfig.ready().
    from apps.dashboard.models import ProjectSettings
    from apps.dashboard.services.settings_service import DEFAULT_SETTINGS_BLOB

    defaults = dict(DEFAULT_SETTINGS_BLOB["syncConfig"])
    row = ProjectSettings.objects.filter(site_url=site_url).first()
    saved = (row.data or {}).get("syncConfig") if row else None
    if isinstance(saved, dict):
        defaults.update({k: v for k, v in saved.items() if k in defaults})
    return defaults


def _scope_filter(module: str):
    """Q-style scope list for a module: its own scope, plus 'all' when a full refresh really
    does run every one of its connectors."""
    scopes = [module]
    if _covered_by_all_scope(module):
        scopes.append("all")
    if _covered_by_core_scope(module):
        scopes.append("core")
    return scopes


def last_run_at(site_url: str, module: str, statuses: list[str]) -> datetime | None:
    """`started_at` of the most recent RefreshRun for this (site, module) in `statuses`.

    started_at (not finished_at) is the anchor because it is what "when did we last hit the
    APIs" means, and it is the only one of the two that is always set.
    """
    return (
        RefreshRun.objects.filter(
            site_url=site_url, scope__in=_scope_filter(module), status__in=statuses
        )
        .order_by("-started_at")
        .values_list("started_at", flat=True)
        .first()
    )


def next_run_for(site_url: str, module: str, cadence: str) -> datetime | None:
    """When this module's next automatic sync is due, or None when there is no honest answer.

    None in exactly two cases:
      * cadence is `manual` (or unrecognised) -- it will never run automatically, so any date
        would be an invention;
      * the module has never completed a successful run -- there is no anchor to measure a
        cadence from, and nothing in the database proves an OS scheduler is even installed
        yet. The scheduler still treats this module as due (see is_due), but Settings does not
        promise a date it cannot derive from real history.

    A due date already in the past is clamped to `now`: the module is overdue and the next
    hourly tick will pick it up, so "now" is the true answer and a stale past date is not.
    """
    interval = CADENCE_INTERVALS.get(cadence)
    if interval is None:
        return None
    last_success = last_run_at(site_url, module, [RefreshStatus.SUCCESS])
    if last_success is None:
        return None
    return max(last_success + interval, timezone.now())


def is_due(site_url: str, module: str, cadence: str, now: datetime | None = None) -> tuple[bool, str]:
    """Should the scheduler start this module right now? Returns (due, human reason).

    The reason string is what --dry-run prints and what the log line records, so it is written
    to be read by the operator, not parsed.
    """
    now = now or timezone.now()
    interval = CADENCE_INTERVALS.get(cadence)
    if interval is None:
        return False, "manual" if cadence == "manual" else f"unknown cadence {cadence!r}"

    # A failed attempt holds the module off even though it did not refresh anything -- see
    # FAILED_RUN_BACKOFF for why.
    last_attempt = last_run_at(
        site_url, module, [RefreshStatus.SUCCESS, RefreshStatus.ERROR, RefreshStatus.RUNNING]
    )
    last_success = last_run_at(site_url, module, [RefreshStatus.SUCCESS])

    if last_attempt is not None and last_attempt != last_success:
        retry_at = last_attempt + min(FAILED_RUN_BACKOFF, interval)
        if now < retry_at:
            return False, (
                f"last attempt did not succeed ({_ago(now, last_attempt)}); "
                f"retry after {retry_at:%Y-%m-%d %H:%M} UTC"
            )

    if last_success is None:
        return True, "never synced"

    due_at = last_success + interval
    if now >= due_at:
        return True, f"last synced {_ago(now, last_success)} ({cadence})"
    return False, f"next due {due_at:%Y-%m-%d %H:%M} UTC ({cadence})"


def _ago(now: datetime, then: datetime) -> str:
    """Compact '3d 4h ago' for log lines."""
    delta = now - then
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        return f"{int(delta.total_seconds() // 60)}m ago"
    if hours < 48:
        return f"{hours}h ago"
    return f"{hours // 24}d {hours % 24}h ago"


def due_modules(site_url: str, now: datetime | None = None) -> list[dict]:
    """Every module for this site with its cadence, whether it is due, and why.

    Returns ALL modules, not just the due ones, so --dry-run can show the full picture.
    Ordered most-overdue first (SYNC_MODULES order breaks ties), because the caller starts at
    most one sync per site per tick -- see the command for why.
    """
    now = now or timezone.now()
    config = get_sync_config(site_url)
    rows = []
    for module in SYNC_MODULES:
        cadence = config.get(module, "manual")
        due, reason = is_due(site_url, module, cadence, now=now)
        last_success = last_run_at(site_url, module, [RefreshStatus.SUCCESS])
        interval = CADENCE_INTERVALS.get(cadence)
        overdue = timedelta(0)
        if due and last_success is not None and interval is not None:
            overdue = now - (last_success + interval)
        elif due:
            # Never synced: maximally overdue, so a brand-new site's first sync wins the slot.
            overdue = timedelta.max
        rows.append({
            "module": module,
            "cadence": cadence,
            "due": due,
            "reason": reason,
            "last_success": last_success,
            "next_run": next_run_for(site_url, module, cadence),
            "overdue": overdue,
        })
    rows.sort(key=lambda r: (not r["due"], -r["overdue"].total_seconds() if r["due"] else 0))
    return rows


def schedule_summary(site_url: str) -> dict:
    """The Automation panel's header values: `{"next_run": "YYYY-MM-DD"|None, "day": <weekday>|None}`.

    The panel shows ONE next run for the whole site, so this is the earliest next_run across
    every module that has one. Modules set to `manual`, and modules with no successful run to
    measure from, contribute nothing -- if that leaves nothing at all, both values stay None
    and the panel keeps saying "not yet scheduled", which is then still the true answer.

    Date-only (not a timestamp) to match what the SPA renders:
    `data.sync.next_run + ' (' + data.sync.day + ')'` (static/spa/src/js/pages/settings.js).
    """
    config = get_sync_config(site_url)
    candidates = [
        dt for dt in (next_run_for(site_url, m, config.get(m, "manual")) for m in SYNC_MODULES)
        if dt is not None
    ]
    if not candidates:
        return {"next_run": None, "day": None}
    soonest = timezone.localtime(min(candidates))
    return {"next_run": soonest.date().isoformat(), "day": soonest.strftime("%A")}
