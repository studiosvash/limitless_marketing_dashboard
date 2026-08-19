"""Refresh/Sync JSON API service (new SPA) -- a thin JSON wrapper over the existing, proven
sync engine (pipeline.services.sync_engine + apps.sync.models.RefreshRun). The old MVP drove
the exact same engine through HTMX partials (apps/sync/views.py); this exposes it as the JSON
contract the new SPA expects:

    POST /api/projects/<slug>/sync   {scope}  -> {task_id, steps[], est_cost, warnings[]}
    GET  /api/tasks/<task_id>                 -> {done, progress, step, steps[], ...}
    GET  /api/projects/<slug>/sync/active     -> {task_id|null, scope, ...}

The SPA (app.js startSync) fires the POST, then polls the task endpoint until `done`, then
re-fetches the current tab from the DB -- i.e. the database-first contract: Refresh calls the
APIs, writes the DB, and the page reads the fresh DB. No page render ever calls an external API.

The run itself does NOT execute here. start_sync_run() spawns `manage.py run_sync` as its own
process; this module only creates the row, launches that process, and reports its progress.
That boundary is the point: a 20-30 minute sync must not live or die with the web worker that
happened to receive the button click.
"""
import logging
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus
from pipeline.services.sync_engine import (
    get_connector_names_for_page, get_all_connector_names,
)

logger = logging.getLogger(__name__)

# The SPA sends its own scope names; map the few that differ from the engine's page keys.
# (Everything not listed is passed through unchanged -- e.g. 'keywords', 'backlinks', 'ads',
#  'ai', 'audit' now all match real PAGE_CONNECTORS keys after the sync_engine fix.)
SCOPE_ALIASES = {
    "positions": "positioning",
    # Incremental positions refresh: same connectors, narrowed at run time to the keywords
    # that have never been measured. Exists so that sending a handful of new keywords from
    # the Keyword Explorer does not require re-querying the entire tracked set against every
    # competitor -- which is slow and, because DataForSEO meters per query, billable.
    "positions_new": "positioning_new",
    # Settings -> Automation's "Organic traffic (Search Console + GA4)" row and the scheduler
    # module of the same name. It maps onto the existing `seo` page key (gsc + ga4) rather than
    # adding a seventh connector list, so the scheduled run and the SEO page's own Refresh
    # button are by construction the same fetch. Added 2026-08-18: until then NO schedulable
    # module ran the plain `gsc` connector, so the Overview's headline organic numbers could
    # only be refreshed by pressing "Refresh all" -- see apps/sync/scheduling.SYNC_MODULES.
    "organic": "seo",
}


def _connectors_for_scope(scope: str) -> list[str]:
    if scope == "all":
        return get_all_connector_names()
    page = SCOPE_ALIASES.get(scope, scope)
    return get_connector_names_for_page(page)


# How recently a scope must have synced for a manual refresh to ask "are you sure?" instead of
# just running. Not configurable: one number the whole team can remember beats a settings row
# nobody visits. The SCHEDULER is unaffected -- its per-module cadences in Settings -> Automation
# already are its freshness logic, and stacking this on top of a 12h cadence would silently
# starve that module (see start_sync_run's `manual` argument).
FRESH_WITHIN = timedelta(hours=24)


# Scopes whose connectors fetch PER-PROJECT (location-scoped) data. Several projects can share
# one domain (add_site(allow_duplicate=True) — e.g. eighteen premierstaff.com city projects),
# and for these scopes a sibling's sync wrote rows for ITS tracking location, not this one's —
# so neither a sibling's SyncLog freshness nor a sibling's live run can stand in for this
# project's own fetch. 'all' is included because ALL_CONNECTORS contains the positioning
# connectors. Domain-level scopes (backlinks, seo, ads, …) are deliberately absent: one
# domain's links/traffic are the same answer for every sibling.
_LOCATION_SCOPED_PAGES = {"positioning", "positioning_new"}


def _scope_is_location_scoped(scope: str) -> bool:
    if scope == "all":
        return True
    return SCOPE_ALIASES.get(scope, scope) in _LOCATION_SCOPED_PAGES


def project_scope_last_ran(site_url: str, site_pk: int, scope: str, now=None):
    """When THIS project itself last completed this scope, within FRESH_WITHIN — else None.

    RefreshRun is the only per-PROJECT record of a sync; SyncLog is keyed (connector,
    site_url) and cannot tell siblings on one domain apart. A 'positions' ask is also
    covered by the project's own 'all' run (ALL_CONNECTORS includes every positioning
    connector) and 'positions_new' by a full 'positions' run. Only SUCCESS counts: a run
    that errored or was cancelled did not refresh what the user is asking for.
    """
    covering = {scope, "all"}
    if scope == "positions_new":
        covering.add("positions")
    cutoff = (now or timezone.now()) - FRESH_WITHIN
    run = (RefreshRun.objects
           .filter(site_url=site_url, site_pk=site_pk, scope__in=covering,
                   status=RefreshStatus.SUCCESS, finished_at__gte=cutoff)
           .order_by("-finished_at").first())
    return run.finished_at if run else None


def _project_name_for_pk(site_pk: int | None) -> str | None:
    """Display name of the project that owns a run, or None when the run is domain-wide.

    Never raises: the name decorates progress payloads polled twice a second, and a lookup
    failure must not take the progress bar down with it.
    """
    if not site_pk:
        return None
    try:
        from pipeline.services.site_service import get_site_by_pk
        from pipeline.utils.db_connection import get_session
        with get_session() as session:
            site = get_site_by_pk(session, site_pk)
            if site is None:
                return None
            return site.site_name or site.slug or site.site_url
    except Exception:
        logger.warning("[sync] could not resolve project name for site_pk=%r", site_pk,
                       exc_info=True)
        return None


def scope_last_synced(site_url: str, connectors: list[str], now=None):
    """When this whole scope last succeeded, or None if any part of it is stale.

    Returns the OLDEST of the connectors' `last_synced` values -- so the answer means "every
    step in this refresh is at least this fresh". None the moment ANY connector is missing a
    successful row inside the window, because then there is genuinely something to fetch.

    A connector whose last run ERRORED is never fresh, however recent: clicking Refresh right
    after fixing a credential is the most common reason to press the button, and treating a
    fresh failure as "up to date" would make that fix impossible to verify.
    """
    if not connectors:
        return None
    cutoff = (now or timezone.now()) - FRESH_WITHIN
    fresh = dict(
        SyncLog.objects.filter(
            connector__in=connectors, site_url=site_url,
            status=SyncStatus.SUCCESS, last_synced__gte=cutoff,
        ).values_list("connector", "last_synced")
    )
    if len(fresh) < len(set(connectors)):
        return None
    return min(fresh.values())


def _spawn_sync_process(run_id: int) -> int | None:
    """Launch `manage.py run_sync --run-id <id>` as a detached child. Returns its pid.

    Detached on purpose: the sync must survive the web worker that started it. See the module
    docstring of apps/sync/management/commands/run_sync.py for the four ways the old in-process
    thread was routinely killed mid-run.

    Output goes to a per-run file rather than a pipe. A pipe whose reader is the web worker
    would fill its OS buffer and BLOCK the sync partway through a 30-minute run, and if the
    worker is recycled the child inherits a dead write end. A file also leaves an operator
    something to read after the fact.
    """
    manage_py = Path(settings.BASE_DIR) / "manage.py"
    log_dir = Path(os.getenv("FUSEHEALTH_LOG_DIR") or (Path(settings.BASE_DIR) / "logs"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        out = open(log_dir / f"sync_run_{run_id}.log", "ab", buffering=0)
    except Exception:
        logger.warning("[sync] could not open a log file for run #%s; discarding its output",
                       run_id, exc_info=True)
        out = subprocess.DEVNULL

    # Fully detach the child from the parent's process group / console so a signal aimed at
    # the web worker (or closing the dev terminal) does not reach it.
    kwargs: dict = {}
    if hasattr(os, "setsid"):  # POSIX — production
        kwargs["start_new_session"] = True
    elif hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):  # Windows — dev
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                   | getattr(subprocess, "DETACHED_PROCESS", 0))

    proc = subprocess.Popen(
        [sys.executable, str(manage_py), "run_sync", "--run-id", str(run_id)],
        cwd=str(settings.BASE_DIR),
        stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
        **kwargs,
    )
    logger.info("[sync] spawned run #%s as pid %s", run_id, proc.pid)
    return proc.pid


def _attach_or_report_sibling(existing: RefreshRun, site_url: str, site_pk: int | None) -> dict:
    """The response for "a run is already in flight for this domain".

    Two different truths, and the caller's `site_pk` decides which one applies:

    * **Same project (or no project in hand)** — attach: return the live run's id so the SPA
      shows its progress. Re-clicking your own running fetch, a second tab, or the scheduler
      (which passes no site_pk and reads `task_id` unconditionally) all land here.

    * **A DIFFERENT project on the same domain** — `sibling_running`: the live run is
      fetching a SIBLING's location-scoped data, so attaching would show its progress bar as
      this project's and then "complete" having fetched nothing for this project. That is
      exactly how new city projects stayed permanently blank while the user watched a
      progress bar succeed. The SPA queues this project's fetch instead and may still watch
      `task_id` to know when the slot frees. A running row with NO site_pk is a domain-wide
      run — it did not fetch this project's location either, so it counts as a sibling.
    """
    if site_pk is not None and existing.site_pk != site_pk:
        owner = _project_name_for_pk(existing.site_pk)
        logger.info("[sync] run #%s (project %r) holds the slot for %r — reporting sibling, "
                    "not attaching", existing.pk, owner or existing.site_pk, site_url)
        return {
            "task_id": existing.pk,
            "scope": existing.scope,
            "sibling_running": True,
            "project": owner or site_url,
            "est_cost": 0,
            "warnings": [],
        }

    logger.info("[sync] run #%s already in flight for %r — attaching instead of starting a "
                "second one", existing.pk, site_url)
    return {
        "task_id": existing.pk,
        "steps": _connectors_for_scope(existing.scope) or ["No connectors for this scope"],
        "est_cost": 0,
        "already_running": True,
        "warnings": [
            f"A {existing.scope!r} refresh is already running for this site — showing its "
            f"progress instead of starting another."
        ],
    }


def start_sync_run(site_url: str, scope: str, user=None, force: bool = False,
                   manual: bool = True, site_pk: int | None = None) -> dict:
    """Create a RefreshRun and execute it in a SEPARATE PROCESS.

    Returns the JSON the SPA's startSync expects: {task_id, steps, est_cost, warnings}.

    `site_pk` names the PROJECT that triggered this run (`sites.id`). Pass it whenever a
    specific project is in hand — every per-project API view has one — so location-aware
    connectors query that project's own city instead of a sibling's. Omitting it is correct
    only for a per-domain run (the scheduler), where it falls back to a by-URL lookup.

    Three behaviours worth knowing about:

    * **Already-fresh scopes ask first.** If every connector in the scope synced successfully
      within FRESH_WITHIN, no run is created and the caller gets
      `{"fresh": True, "last_synced": ...}` -- a shape with NO `task_id` -- so the SPA can show
      "last fetched 40 minutes ago, refetch anyway?". Answering yes re-calls with `force=True`.

      `manual=False` disables that check entirely and is what `run_scheduled_syncs` passes. Two
      reasons, both load-bearing: the cadences in `syncConfig` already ARE the scheduler's
      freshness logic (a 24h window over a 12h `ads` cadence would silently starve Ads), and
      the scheduler reads `info['task_id']` on the line after this returns, which the fresh
      shape does not have.

    * **One run per site.** If a run is already in flight for this site, its task_id is
      returned instead of starting a second one. There was no guard here at all (only the cron
      command had one), so two browser tabs, two users, or a cron tick during a manual refresh
      each forked a whole second sync over the same connectors -- racing on SyncLog's
      UNIQUE(connector, site_url) row and the same analytics tables, and double-spending
      metered DataForSEO calls. Returning the existing id means the second caller simply
      attaches to the run already running, which is what the user wanted anyway.

    * **Missing credentials warn, they do not block.** `warnings` names the steps that will be
      skipped and why. The view used to refuse the entire run with a 400 instead; see the
      comment in ProjectSyncView.post for why that was wrong.
    """
    scope = (scope or "all").strip() or "all"
    connectors = _connectors_for_scope(scope)

    # Clear rows orphaned by an old crash first, so a dead run cannot block this site forever.
    from apps.sync import scheduling
    try:
        scheduling.reap_orphaned_runs()
    except Exception:
        logger.warning("[sync] reaping before start failed; continuing", exc_info=True)

    existing = (RefreshRun.objects
                .filter(site_url=site_url, status=RefreshStatus.RUNNING)
                .order_by("-started_at").first())
    if existing is not None:
        return _attach_or_report_sibling(existing, site_url, site_pk)

    # The DataForSEO paywall. Checked AFTER the one-run-per-site guard (attaching to a run
    # already in flight is always fine — its spend already happened) and BEFORE the
    # freshness check (going over budget must block a refetch even of "fresh" data, since
    # 'force' would otherwise still spend past the cap). Only scopes that actually call
    # DataForSEO are refused — a pure GSC/GA4 refresh costs nothing and stays available.
    from apps.dashboard.services.budget_service import budget_status, is_billable_connectors
    if is_billable_connectors(connectors):
        status = budget_status()
        if status["exceeded"]:
            logger.info("[sync] refused %r for %r — DataForSEO budget exceeded ($%.2f of $%.2f)",
                        scope, site_url, status["spent"], status["cap"])
            return {
                "budget_exceeded": True,
                "spent": status["spent"],
                "cap": status["cap"],
                "message": (
                    f"Monthly DataForSEO budget of ${status['cap']:.2f} reached "
                    f"(${status['spent']:.2f} spent). Syncs that call DataForSEO are paused "
                    "until next month, or until the budget is raised."
                ),
            }

    # Checked AFTER the one-run-per-site guard: if a run is already in flight, attaching to it
    # is what the user wanted, and answering "already up to date" would hide it.
    if manual and not force:
        last_synced = scope_last_synced(site_url, connectors)
        if last_synced is not None and site_pk is not None and _scope_is_location_scoped(scope):
            # SyncLog freshness is DOMAIN-level, but this scope fetches per-project data:
            # a sibling city project's sync an hour ago says nothing about THIS project's
            # location. Fresh only if this project itself ran it recently — and the prompt
            # then quotes this project's own timestamp, not the sibling's.
            last_synced = project_scope_last_ran(site_url, site_pk, scope)
        if last_synced is not None:
            logger.info("[sync] %r for %r is already fresh (since %s) — asking before running",
                        scope, site_url, last_synced.isoformat())
            return {
                "fresh": True,
                "scope": scope,
                "last_synced": last_synced.isoformat(),
            }

    try:
        from apps.dashboard.services.connection_check_service import requirement_warnings
        warnings = requirement_warnings(site_url, connectors)
    except Exception:
        logger.error("[sync] pre-flight credential check failed", exc_info=True)
        warnings = []

    try:
        run = RefreshRun.objects.create(
            site_url=site_url,
            # Which project asked. Carried on the row rather than passed as an argument because the
            # sync executes in a SEPARATE PROCESS (`manage.py run_sync --run-id`), so the row is the
            # only channel between the request and the connectors. See RefreshRun.site_pk.
            site_pk=site_pk,
            scope=scope,
            triggered_by=user if (user is not None and user.is_authenticated) else None,
            status=RefreshStatus.RUNNING,
            total_count=len(connectors),
        )
    except IntegrityError:
        # Lost the race with a simultaneous start: the `one_running_refresh_per_site`
        # constraint rejected a second RUNNING row for this site. Attach to the winner
        # instead of spawning a second metered sync — same response shape as the
        # "already in flight" check above.
        existing = (RefreshRun.objects
                    .filter(site_url=site_url, status=RefreshStatus.RUNNING)
                    .order_by("-started_at").first())
        if existing is None:
            raise
        logger.info("[sync] lost start race for %r to run #%s", site_url, existing.pk)
        return _attach_or_report_sibling(existing, site_url, site_pk)

    try:
        pid = _spawn_sync_process(run.pk)
        RefreshRun.objects.filter(pk=run.pk).update(pid=pid)
    except Exception as exc:
        # A run we could not start must not be left claiming to be running: it would block this
        # site's next refresh until the reaper cleared it two hours later.
        logger.error("[sync] could not spawn the sync process for run #%s", run.pk, exc_info=True)
        RefreshRun.objects.filter(pk=run.pk).update(
            status=RefreshStatus.ERROR,
            error_message=f"Could not start the sync process: {exc}",
        )
        raise

    return {
        "task_id": run.pk,
        # SPA shows steps[0] as the first progress label; connector names are the honest steps.
        "steps": connectors or ["No connectors for this scope"],
        "est_cost": 0,  # real per-connector cost estimation is future work; honest 0, not faked
        "warnings": warnings,
    }


def _claim_for_cancel(run_pk: int, message: str) -> int:
    """Flip exactly this run from `running` to `cancelled`. Returns rows changed (0 or 1).

    Split out as its own function because it is THE pid-reuse guard and the tests need to
    drive the race: the caller may kill a process only when this returned 1. A run that
    resolved between the SELECT and this UPDATE returns 0, and its pid may by then belong
    to an unrelated process.
    """
    return (
        RefreshRun.objects
        .filter(pk=run_pk, status=RefreshStatus.RUNNING)
        .update(
            status=RefreshStatus.CANCELLED,
            current_connector=None,
            finished_at=timezone.now(),
            error_message=message,
        )
    )


def cancel_sync_run(site_url: str, user=None) -> dict:
    """Stop the refresh in flight for this site.

    Two halves, in this order and both required:

      1. **Mark the row `cancelled`.** The reliable half. sync_all/sync_page re-read the
         status between connectors, so the run stops before the next connector even if
         the kill below fails outright.
      2. **Kill the run_sync process.** The fast half, and the only reason Stop feels
         immediate: without it a cancel issued 40 seconds into `dataforseo_onpage`'s
         600-second poll would appear to do nothing for ten minutes.

    Records already written are kept -- a run stopped at step 2 of 5 keeps steps 1 and 2
    in full. What is saved is every connector that had not started yet. The connector
    that WAS running may already be billed (DataForSEO meters on task submission, not on
    poll completion), and nothing here pretends otherwise.

    "Nothing was running" is a normal outcome, not an error: the run may have finished
    while the user was reaching for the button.
    """
    from apps.sync import scheduling

    run = (RefreshRun.objects
           .filter(site_url=site_url, status=RefreshStatus.RUNNING)
           .order_by("-started_at").first())
    if run is None:
        return {"cancelled": False, "reason": "no refresh is running for this site"}

    who = None
    if user is not None and getattr(user, "is_authenticated", False):
        who = user.get_username()
    message = f"Cancelled by {who}." if who else "Cancelled."

    if _claim_for_cancel(run.pk, message) != 1:
        # Someone else cancelled it, or it finished on its own, between the SELECT above
        # and this UPDATE. Either way this call does not own the pid and must not kill.
        logger.info("[sync] run #%s resolved before the cancel landed — killing nothing", run.pk)
        return {"cancelled": False, "reason": "that refresh had already finished"}

    killed = scheduling.terminate_sync_process(run.pid)
    logger.info("[sync] cancelled run #%s (%s@%s) pid=%s killed=%s",
                run.pk, run.scope, site_url, run.pid, killed)

    # The connector that was mid-flight left its SyncLog row at `running`; nothing else
    # will ever rewrite it. Scoped to this site and given the cancel message so another
    # project's genuinely-orphaned rows are not relabelled. Safe to run now because the
    # RefreshRun is no longer `running`, which is the one fact this reconciler tests.
    #
    # A small race remains: if the process writes its row again in the moment between the
    # kill and this call, the row goes back to `running`. That self-heals -- the same
    # reconciler runs on the next reap, which every start_sync_run and sync/active poll
    # triggers.
    try:
        scheduling.reconcile_orphaned_sync_logs(
            site_url=site_url, message=scheduling.CANCELLED_CONNECTOR_MESSAGE
        )
    except Exception:
        logger.warning("[sync] reconciling connector rows after cancel failed", exc_info=True)

    return {"cancelled": True, "task_id": run.pk, "killed": killed}


def _step_details(run: RefreshRun, connectors: list[str]) -> list[dict]:
    """Per-connector state for the live checklist under the progress bar.

    NO NEW TABLE. Everything needed is already recorded:
      * position in the ordered connector list vs `run.completed_count` gives
        finished / running / pending, because sync_all and sync_page increment
        completed_count once per connector, in order;
      * the SyncLog row gives the OUTCOME of a finished connector -- BaseConnector.sync writes
        it live, three times per connector (running, then success/error) with records_written,
        duration_seconds and error_message.

    The one subtlety: SyncLog is UNIQUE(connector, site_url), so it holds the LAST run's result
    and is destructively overwritten. A row therefore only describes THIS run if it was touched
    since the run began -- hence the `last_synced >= run.started_at` test. A connector counted
    as finished with no such row never actually ran: `_get_connector` returned None because its
    credentials are missing, and sync_page/sync_all increment completed_count and move on while
    still reporting the run as SUCCESS. That case is reported as "skipped" rather than a tick,
    because a green tick on a connector that did nothing is how a broken integration stays
    invisible for weeks.
    """
    from apps.sync.models import SyncLog

    logs = {
        row.connector: row
        for row in SyncLog.objects.filter(connector__in=connectors, site_url=run.site_url)
    }
    finished = run.completed_count
    running_now = run.status == RefreshStatus.RUNNING

    steps = []
    for i, name in enumerate(connectors):
        log = logs.get(name)
        ran_this_time = bool(log and log.last_synced and log.last_synced >= run.started_at)

        if i < finished:
            if not ran_this_time:
                # "Skipped" is all we know: sync_engine could not construct the connector, and
                # it does not record why. DO NOT NAME A CAUSE HERE. This line used to read
                # "Skipped — credentials not configured", which was a guess presented as a
                # diagnosis — and it was wrong for the most important connector in the
                # product: `dataforseo_serp` was unconstructable because its entry in
                # `connector_map` named a class that does not exist, so position tracking
                # never ran while the UI blamed billing. Weeks of "our DataForSEO plan must be
                # limited" came from this one string. An honest "check the log" sends the
                # reader to the AttributeError; a confident wrong answer sends them nowhere.
                state, detail = "skipped", "Skipped — could not start (see sync log)"
            elif log.status == "error":
                state, detail = "error", (log.error_message or "Failed")
            else:
                state, detail = "done", f"{(log.records_written or 0):,} records"
        elif i == finished and running_now:
            state, detail = "running", "Running…"
        else:
            state, detail = "pending", "Waiting"

        steps.append({
            "name": name,
            "state": state,
            "detail": detail,
            "records": (log.records_written or 0) if (log and ran_this_time) else None,
            "seconds": round(log.duration_seconds, 1) if (log and ran_this_time and log.duration_seconds) else None,
        })
    return steps


def _reap_if_dead(run: RefreshRun) -> RefreshRun:
    """Resolve THIS run if its OS process is gone. Returns the row, refreshed if it changed.

    `GET /api/tasks/<id>` is the only thing the SPA polls during a sync, and it used to trust
    `status` verbatim — so when the sync process died (a crash, a deploy, a `runserver` reload,
    a killed terminal) the row sat at `running` and the progress bar spun on a ghost for up to
    RUN_TIMEOUT (2 hours). Observed exactly that: a 3-keyword `positions_new` run whose pid had
    been gone for six minutes while the UI reported "Syncing… 33% · Est. 10m remaining" and the
    user waited for API calls that nobody was making.

    Deliberately a single-row pid check rather than `reap_orphaned_runs()`, which sweeps every
    running row and reconciles the SyncLog table. This runs on every poll — twice a second at
    the start of a sync — and must stay cheap. The full sweep still runs where it belongs: at
    `start_sync_run`, at `active_run`, on app start and on every scheduler tick.

    PID_GRACE is honoured for the same reason the sweep honours it: a row is written before
    `Popen` returns, so a just-started run legitimately has no live pid yet.
    """
    from apps.sync.scheduling import DEAD_PROCESS_MESSAGE, PID_GRACE, _process_alive

    if run.status != RefreshStatus.RUNNING or not run.pid or not run.started_at:
        return run
    if timezone.now() - run.started_at < PID_GRACE:
        return run
    try:
        if _process_alive(run.pid):
            return run
    except Exception:
        logger.warning("[sync] liveness check failed for run #%s", run.pk, exc_info=True)
        return run

    # Filtered on status='running', so a run that finished between the read and here is left
    # alone — the same concurrency rule reap_orphaned_runs() follows.
    updated = RefreshRun.objects.filter(pk=run.pk, status=RefreshStatus.RUNNING).update(
        status=RefreshStatus.ERROR,
        current_connector=None,
        finished_at=timezone.now(),
        error_message=DEAD_PROCESS_MESSAGE.format(pid=run.pid),
    )
    if not updated:
        return run
    logger.warning("[sync] run #%s reaped while polling — pid %s is gone", run.pk, run.pid)
    return RefreshRun.objects.get(pk=run.pk)


def task_status(task_id: int) -> dict | None:
    """Progress for the SPA's polling loop. None if the run id is unknown (view -> 404)."""
    try:
        run = RefreshRun.objects.get(pk=task_id)
    except RefreshRun.DoesNotExist:
        return None

    run = _reap_if_dead(run)

    done = run.status != RefreshStatus.RUNNING
    error = None
    if run.status == RefreshStatus.RUNNING:
        step = f"Syncing {run.current_connector or '...'}"
    elif run.status == RefreshStatus.SUCCESS:
        step = f"Done -- {run.records_written:,} records written"
    elif run.status == RefreshStatus.CANCELLED:
        # NOT the error branch: `error` stays None so the SPA does not paint a failure over a
        # deliberate Stop click, and the count says what was actually kept.
        step = f"Cancelled -- {run.completed_count} of {run.total_count} steps finished"
    else:
        # Failed connectors: short readable step line (the SPA renders it verbatim);
        # the full messages ride along in `error` and in Settings -> Connections.
        first_line = (run.error_message or "Sync error").splitlines()[0]
        step = f"Completed with errors -- {first_line[:160]}"
        error = run.error_message

    connectors = _connectors_for_scope(run.scope or "all")
    return {
        "done": done,
        "progress": (run.percent / 100.0) if not done else 1.0,
        "step": step,
        "status": run.status,
        "error": error,
        # ── Everything below is additive, for the live step checklist. ──
        "scope": run.scope,
        "current": run.current_connector,
        "completed": run.completed_count,
        "total": run.total_count,
        "records": run.records_written,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "elapsed": int((timezone.now() - run.started_at).total_seconds()) if run.started_at else 0,
        "steps": _step_details(run, connectors),
        # WHOSE run this is. With several projects on one domain the banner used to print
        # only the domain, so the user could not tell which project's fetch was actually
        # running — see _attach_or_report_sibling. `project` is None for a domain-wide run.
        "site_url": run.site_url,
        "site_pk": run.site_pk,
        "project": _project_name_for_pk(run.site_pk),
    }


def active_run(site_url: str) -> dict:
    """The run currently in flight for this site, or {"task_id": None}.

    Exists so the progress bar SURVIVES A PAGE RELOAD. `boot()` restores the tab, range and
    project but had no way to ask "is a sync running?", and GET /api/tasks/<id> needs an id the
    reloaded client no longer has -- so a hard refresh made a live 30-minute sync completely
    invisible, which reads as "the sync stopped".

    Reaps first, so a row orphaned by an old crash is not reported as live progress.
    """
    from apps.sync import scheduling
    try:
        scheduling.reap_orphaned_runs()
    except Exception:
        logger.warning("[sync] reaping before active_run failed; continuing", exc_info=True)

    run = (RefreshRun.objects
           .filter(site_url=site_url, status=RefreshStatus.RUNNING)
           .order_by("-started_at").first())
    if run is None:
        return {"task_id": None}
    return {"task_id": run.pk, "scope": run.scope, **(task_status(run.pk) or {})}
