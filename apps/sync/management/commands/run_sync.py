"""Execute one RefreshRun in its own OS process.

    python manage.py run_sync --run-id 123

WHY THIS COMMAND EXISTS
-----------------------
`start_sync_run` used to do `threading.Thread(target=sync_all, daemon=True).start()` inside
the gunicorn web worker. A scope='all' run takes 20-30 minutes typically and up to ~80 in the
worst case (see the itemised budget on scheduling.RUN_TIMEOUT), and a daemon thread dies with
its process. Every one of these killed a running sync outright:

  * gunicorn's `--timeout 120` watchdog. It is a WORKER watchdog, not a request timeout: the
    arbiter SIGKILLs any worker that has not heartbeated, and all three workers also serve
    normal page requests, so one slow request on the sync-hosting worker took the sync with it.
    (The deploy doc's justification for raising the timeout to 120 "because syncs take 5+
    minutes" was based on this misunderstanding.)
  * `systemctl restart` / any deploy / `git pull` + reload.
  * In dev, `runserver`'s autoreloader — the sync writes to logs/fusehealth.log, which lives
    inside the watched project tree, so the sync restarted the server that was running it.
    (Proven 2026-07-27; see the note in pipeline/utils/logger.py.)

In every case the thread vanished with no traceback and the RefreshRun row stayed 'running'
for two hours until the reaper found it, while the SPA polled a progress bar that would never
advance. That is the "sync ruk gaya" symptom.

As a separate process the sync outlives all of it. The trade-off is one extra Python
interpreter start (~1s against a 20-minute job) and no shared in-process state — neither
matters here, because the run communicates entirely through the RefreshRun row.

This command is also directly runnable by an operator, which is how you debug a failing sync:
you get the full traceback on your terminal instead of one truncated line in the UI.
"""
import logging
import traceback

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.sync.models import RefreshRun, RefreshStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the connectors for an existing RefreshRun row (one run per process)."

    def add_arguments(self, parser):
        parser.add_argument("--run-id", type=int, required=True,
                            help="Primary key of the RefreshRun row to execute.")

    def handle(self, *args, **options):
        run_id = options["run_id"]
        try:
            run = RefreshRun.objects.get(pk=run_id)
        except RefreshRun.DoesNotExist:
            raise CommandError(f"RefreshRun #{run_id} does not exist.")

        if run.status != RefreshStatus.RUNNING:
            # Not an error: the reaper or a previous attempt may have already resolved it.
            # Refusing to re-run protects against a duplicate launch double-spending metered
            # DataForSEO calls.
            self.stdout.write(f"RefreshRun #{run_id} is already {run.status} — nothing to do.")
            return

        # SCOPE_ALIASES lives with the JSON API because it translates the SPA's scope names
        # into the engine's page keys. Imported lazily so this command stays importable even
        # if the API layer is mid-refactor.
        from apps.dashboard.services.sync_api_service import SCOPE_ALIASES
        from pipeline.services.sync_engine import sync_all, sync_page

        scope = run.scope or "all"
        # Nobody triggered it => nobody is watching it. The scheduler (and any other unattended
        # caller) creates the row with no user; a click always carries one. The SERP connectors
        # price and pace themselves on this — normal-priority queue, longer poll window — so a
        # cron run costs half per query and a watched refresh still finishes while the user
        # is looking at the bar.
        scheduled = run.triggered_by_id is None
        self.stdout.write(f"Running scope={scope!r} for {run.site_url!r} (run #{run_id}"
                          f"{', scheduled' if scheduled else ''})…")

        try:
            # `run.site_pk` names the project that triggered this run; the connectors need it to
            # resolve THEIR OWN tracking location rather than a sibling project's. It rides on
            # the row because this command is a separate process — see RefreshRun.site_pk.
            if scope == "all":
                summary = sync_all(run.site_url, run.pk, site_pk=run.site_pk,
                                   scheduled=scheduled)
            else:
                summary = sync_page(SCOPE_ALIASES.get(scope, scope), run.site_url, run.pk,
                                    site_pk=run.site_pk, scheduled=scheduled)
        except Exception:
            # sync_all/sync_page mark the row themselves on the paths they control, but a crash
            # OUTSIDE their per-connector try/except (an import error, a DB outage, or a bug
            # like the NameError that broke sync_all entirely) would otherwise leave the row
            # 'running' forever -- exactly the failure mode this whole change exists to end.
            tb = traceback.format_exc()
            logger.error("[run_sync] run #%s crashed:\n%s", run_id, tb)
            last_line = tb.strip().splitlines()[-1] if tb.strip() else "unknown error"
            RefreshRun.objects.filter(pk=run_id, status=RefreshStatus.RUNNING).update(
                status=RefreshStatus.ERROR,
                current_connector=None,
                finished_at=timezone.now(),
                error_message=f"Sync process crashed: {last_line}",
            )
            raise CommandError(f"Sync crashed — see the log. {last_line}")

        self.stdout.write(self.style.SUCCESS(
            f"Done: {summary['completed']}/{summary['total']} connectors, "
            f"{summary['records_written']} records, {len(summary['errors'])} error(s)."
        ))
        for err in summary["errors"]:
            self.stdout.write(self.style.WARNING(f"  ! {err}"))
