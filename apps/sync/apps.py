import logging
import os

from django.apps import AppConfig
from django.core.signals import request_started

logger = logging.getLogger(__name__)


def _reap_once(sender, **kwargs):
    """Clear runs orphaned by the previous process, once per server process.

    Disconnects itself first, so this costs exactly one query per process, not one per
    request, and so a failure cannot make it retry on every request.
    """
    request_started.disconnect(_reap_once)
    try:
        from apps.sync.scheduling import reap_orphaned_runs

        reaped = reap_orphaned_runs()
        if reaped:
            logger.warning(
                "[startup] Reaped %d orphaned sync run(s) left behind by a previous process.",
                len(reaped),
            )
    except Exception as exc:  # noqa: BLE001
        # Best-effort cleanup: an unmigrated or unreachable database must never turn the first
        # request after a deploy into a 500. run_scheduled_syncs reaps the same rows on its
        # next tick, so failing here costs at most one hour.
        logger.warning("[startup] Orphaned-run reap skipped: %s", exc)


class SyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sync'
    label = 'sync'

    def ready(self):
        """Arrange for orphaned RefreshRun rows to be reaped when this process starts serving.

        WHY at all: a sync runs in `threading.Thread(daemon=True)` (sync_api_service.start_sync_run),
        so a restart kills it mid-run and leaves the row at status='running' forever -- the SPA
        polls /api/tasks/<id> and never sees `done`, and the scheduler's per-site "already
        running?" guard is blocked permanently. A restart is precisely the event that creates
        those rows, so a restart is the right moment to clear them.

        WHY on the FIRST REQUEST rather than inside ready() itself: ready() runs for EVERY
        management command -- including `migrate`/`makemigrations` against a database where
        sync_refreshrun does not exist yet, `collectstatic` (which may have no database at
        all), and `test`. Querying there would be noise at best and a failed deploy at worst,
        and Django warns about it outright ("Accessing the database during app initialization
        is discouraged"). Hanging the work off request_started gets the same effect with none
        of that: it fires under runserver, gunicorn and any WSGI/ASGI server, and never fires
        for a command that serves no requests. The cost is that the cleanup lands a few
        milliseconds into the first request instead of during boot, which no user can observe.

        SYNC_SKIP_STARTUP_REAP=1 opts out entirely, for any environment where the scheduler
        tick alone is preferred.
        """
        if os.environ.get("SYNC_SKIP_STARTUP_REAP"):
            return
        request_started.connect(_reap_once, weak=False)
