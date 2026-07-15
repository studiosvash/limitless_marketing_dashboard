"""Refresh/Sync JSON API service (new SPA) -- a thin JSON wrapper over the existing, proven
sync engine (pipeline.services.sync_engine + apps.sync.models.RefreshRun). The old MVP drove
the exact same engine through HTMX partials (apps/sync/views.py); this exposes it as the JSON
contract the new SPA expects:

    POST /api/projects/<slug>/sync   {scope}  -> {task_id, steps[], est_cost}
    GET  /api/tasks/<task_id>                 -> {done, progress, step}

The SPA (static/spa/index.html startSync) fires the POST, then polls the task endpoint every
500ms until `done`, then re-fetches the current tab from the DB -- i.e. the database-first
contract: Refresh calls the APIs, writes the DB, and the page reads the fresh DB. No page render
ever calls an external API.
"""
import logging
import threading

from apps.sync.models import RefreshRun, RefreshStatus
from pipeline.services.sync_engine import (
    sync_all, sync_page, get_connector_names_for_page, get_all_connector_names,
)

logger = logging.getLogger(__name__)

# The SPA sends its own scope names; map the few that differ from the engine's page keys.
# (Everything not listed is passed through unchanged -- e.g. 'keywords', 'backlinks', 'ads',
#  'ai', 'audit' now all match real PAGE_CONNECTORS keys after the sync_engine fix.)
SCOPE_ALIASES = {
    "positions": "positioning",
}


def _connectors_for_scope(scope: str) -> list[str]:
    if scope == "all":
        return get_all_connector_names()
    page = SCOPE_ALIASES.get(scope, scope)
    return get_connector_names_for_page(page)


def start_sync_run(site_url: str, scope: str, user=None) -> dict:
    """Create a RefreshRun and kick off the sync in a background thread (same pattern as the
    old apps/sync/views.py). Returns the JSON the SPA's startSync expects."""
    scope = (scope or "all").strip() or "all"
    connectors = _connectors_for_scope(scope)

    run = RefreshRun.objects.create(
        site_url=site_url,
        scope=scope,
        triggered_by=user if (user is not None and user.is_authenticated) else None,
        status=RefreshStatus.RUNNING,
        total_count=len(connectors),
    )

    if scope == "all":
        target, args = sync_all, (site_url, run.pk)
    else:
        # sync_page looks the connectors up by the engine's page key, so pass the aliased key.
        target, args = sync_page, (SCOPE_ALIASES.get(scope, scope), site_url, run.pk)

    threading.Thread(target=target, args=args, daemon=True).start()

    return {
        "task_id": run.pk,
        # SPA shows steps[0] as the first progress label; connector names are the honest steps.
        "steps": connectors or ["No connectors for this scope"],
        "est_cost": 0,  # real per-connector cost estimation is future work; honest 0, not faked
    }


def task_status(task_id: int) -> dict | None:
    """Progress for the SPA's polling loop. None if the run id is unknown (view -> 404)."""
    try:
        run = RefreshRun.objects.get(pk=task_id)
    except RefreshRun.DoesNotExist:
        return None

    done = run.status != RefreshStatus.RUNNING
    error = None
    if run.status == RefreshStatus.RUNNING:
        step = f"Syncing {run.current_connector or '...'}"
    elif run.status == RefreshStatus.SUCCESS:
        step = f"Done -- {run.records_written:,} records written"
    else:
        # Failed connectors: short readable step line (the SPA renders it verbatim);
        # the full messages ride along in `error` and in Settings -> Connections.
        first_line = (run.error_message or "Sync error").splitlines()[0]
        step = f"Completed with errors -- {first_line[:160]}"
        error = run.error_message

    return {
        "done": done,
        "progress": (run.percent / 100.0) if not done else 1.0,
        "step": step,
        "status": run.status,
        "error": error,
    }
