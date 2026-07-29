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
from datetime import datetime, timedelta

from django.utils import timezone

from apps.sync.models import RefreshRun, RefreshStatus
from pipeline.services.sync_engine import ALL_CONNECTORS, PAGE_CONNECTORS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Modules and cadences
# ---------------------------------------------------------------------------

# The six keys the Settings -> Automation UI writes into `syncConfig`. These are also the
# scope strings the SPA POSTs to /api/projects/<slug>/sync, so they are passed straight to
# start_sync_run() -- which owns the one alias that differs from the engine's page key
# (positions -> positioning, see sync_api_service.SCOPE_ALIASES). Kept as an ordered tuple
# because it doubles as the tie-break order when two modules come due in the same hour.
SYNC_MODULES: tuple[str, ...] = ("positions", "backlinks", "audit", "keywords", "ads", "ai")

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
_SCOPE_TO_PAGE_KEY = {"positions": "positioning"}  # mirrors sync_api_service.SCOPE_ALIASES


def _covered_by_all_scope(module: str) -> bool:
    connectors = PAGE_CONNECTORS.get(_SCOPE_TO_PAGE_KEY.get(module, module), [])
    # A module with no connectors at all is not "covered" by anything -- there is nothing to run.
    return bool(connectors) and set(connectors) <= set(ALL_CONNECTORS)


# ---------------------------------------------------------------------------
# Orphaned-run reaping
# ---------------------------------------------------------------------------

# start_sync_run() runs the sync in `threading.Thread(daemon=True)`. A server restart (or a
# crash, or Ctrl-C in dev) kills that thread mid-run and leaves the RefreshRun row at
# status='running' forever: the SPA polls /api/tasks/<id> and never sees `done`, and the
# scheduler's "is a sync already running for this site?" guard would be blocked permanently.
#
# The timeout is picked from the real worst case of a scope='all' run, adding up the
# connectors' own hard limits rather than guessing:
#     pagespeed              15 pages x (60s request + 60s retry + rate-limit sleeps)  ~ 1950s
#     dataforseo_serp        20 polls x 15s + per-task task_get calls                  ~  600s
#     dataforseo_serp_comp.  same polling budget                                       ~  600s
#     dataforseo_onpage      600s crawl poll + 3 x 30s requests                        ~  690s
#     url_inspection         50 pages x (request + 0.2s pacing)                        ~  300s
#     the 9 remaining connectors at their 30-60s request timeouts                      ~  400s
#     post-sync rebuild: aggregates + anomalies + technical issues + AI summary        ~  120s
#                                                                            total    ~ 4700s (~80 min)
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
    "The most likely cause is a server restart while the sync was running (syncs run in a "
    "daemon thread and do not survive one). Re-run the refresh to try again."
)


def reap_orphaned_runs(now: datetime | None = None, dry_run: bool = False) -> list[RefreshRun]:
    """Mark every RefreshRun still `running` past RUN_TIMEOUT as `error`.

    Returns the affected rows (fetched before the update, so callers can log them). With
    dry_run=True nothing is written and the rows are only reported.

    Safe to call concurrently and repeatedly: the UPDATE is filtered on status='running', so a
    run that finishes between the SELECT and the UPDATE is left alone, and a second reaper pass
    finds nothing to do.
    """
    now = now or timezone.now()
    cutoff = now - RUN_TIMEOUT

    stale = list(
        RefreshRun.objects.filter(status=RefreshStatus.RUNNING, started_at__lt=cutoff)
    )
    if not stale or dry_run:
        return stale

    RefreshRun.objects.filter(
        pk__in=[r.pk for r in stale], status=RefreshStatus.RUNNING
    ).update(
        status=RefreshStatus.ERROR,
        current_connector=None,
        finished_at=now,
        error_message=REAP_MESSAGE.format(hours=RUN_TIMEOUT.total_seconds() / 3600),
    )
    for run in stale:
        logger.warning(
            "[scheduler] Reaped orphaned RefreshRun#%s (%s@%s) started %s",
            run.pk, run.scope, run.site_url, run.started_at.isoformat(),
        )
    return stale


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
