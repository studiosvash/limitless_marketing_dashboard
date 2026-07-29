"""The scheduler tick. Point a real OS scheduler at this command, hourly.

    python manage.py run_scheduled_syncs

There is no Celery, no cron daemon and no in-process scheduler in this repo, and adding one
would be a new dependency for 2-3 internal users. So the schedule the user configures in
Settings -> Automation is enforced by the one mechanism that is already there: a management
command the operator's own scheduler (Windows Task Scheduler / cron) invokes on a fixed tick.

Each invocation:
  1. reaps RefreshRun rows orphaned by a server restart (see scheduling.RUN_TIMEOUT);
  2. reads every active Site and its `syncConfig` cadences;
  3. starts at most ONE due module per site, through the existing start_sync_run().

WHY at most one per site: start_sync_run() spawns a background thread per run and the
connectors are rate-limited and metered. Firing five modules at once would run five threads
against the same DataForSEO account, and the SPA's progress bar tracks a single task id. The
most-overdue module wins the slot and the rest are picked up on the following ticks -- with an
hourly tick, a full backlog drains within hours, which is well inside every supported cadence.

Idempotency: running this twice in a row starts nothing the second time. Either the first run
is still in flight (the per-site "already running" guard skips it) or it finished and reset
that module's cadence clock. Nothing here depends on the tick landing at a particular minute,
so a missed tick just means the sync happens an hour late, never twice.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.sync import scheduling
from apps.sync.scheduling import SYNC_MODULES


class Command(BaseCommand):
    help = (
        "Start any syncs that are due per each site's Settings -> Automation cadences. "
        "Intended to be run hourly by Windows Task Scheduler or cron."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Print what would run (and what would be reaped) without starting or writing anything.",
        )
        parser.add_argument(
            "--site", default=None, metavar="SITE_URL",
            help=(
                "Only consider this site_url (default: every active site). Reaping is "
                "deliberately still global -- a stuck row on another site is worth clearing "
                "whichever site you were targeting."
            ),
        )
        parser.add_argument(
            "--scope", default=None, metavar="MODULE",
            help=(
                "Force this module to run now, ignoring its cadence -- including 'manual'. "
                f"One of: {', '.join(SYNC_MODULES)}."
            ),
        )

    # -- helpers ------------------------------------------------------------

    def _site_urls(self, only: str | None) -> list[str]:
        from pipeline.services.site_service import get_active_site_ids

        active = get_active_site_ids()
        if only is None:
            return active
        if only not in active:
            # Deliberately an error, not a silent no-op: a typo'd --site in a scheduled task
            # would otherwise look like "nothing was due" forever.
            raise CommandError(f"{only!r} is not an active site. Active: {', '.join(active) or '(none)'}")
        return [only]

    def _start(self, site_url: str, module: str, reason: str, dry_run: bool) -> None:
        if dry_run:
            self.stdout.write(f"  WOULD START  {module:<10} — {reason}")
            return
        # The one sanctioned way to run a sync. Not reimplemented here: start_sync_run owns the
        # RefreshRun row, the scope aliasing (positions -> positioning) and the worker thread.
        from apps.dashboard.services.sync_api_service import start_sync_run

        info = start_sync_run(site_url, module)
        self.stdout.write(self.style.SUCCESS(
            f"  STARTED      {module:<10} — {reason} (task {info['task_id']}, "
            f"{len(info['steps'])} connector(s))"
        ))

    # -- main ---------------------------------------------------------------

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        forced = opts["scope"]
        if forced is not None and forced not in SYNC_MODULES:
            raise CommandError(f"Unknown --scope {forced!r}. One of: {', '.join(SYNC_MODULES)}")

        now = timezone.now()
        self.stdout.write(
            f"run_scheduled_syncs @ {now:%Y-%m-%d %H:%M} UTC"
            + ("  [DRY RUN — nothing will be started or written]" if dry_run else "")
        )

        # Reap first. An orphaned 'running' row would otherwise block its site's guard below
        # for good, which is the exact failure this command must not inherit.
        reaped = scheduling.reap_orphaned_runs(now=now, dry_run=dry_run)
        # A dry run does not write the reap, so tell the "already running?" guard below to
        # pretend it did -- otherwise --dry-run predicts the exact opposite of the real run.
        reaped_ids = [r.pk for r in reaped] if dry_run else []
        for run in reaped:
            verb = "WOULD REAP" if dry_run else "REAPED"
            self.stdout.write(self.style.WARNING(
                f"{verb} RefreshRun#{run.pk} ({run.scope}@{run.site_url}) — running since "
                f"{run.started_at:%Y-%m-%d %H:%M} UTC, past the "
                f"{scheduling.RUN_TIMEOUT.total_seconds() / 3600:.0f}h timeout"
            ))

        site_urls = self._site_urls(opts["site"])
        if not site_urls:
            self.stdout.write("No active sites — nothing to do.")
            return

        started = 0
        for site_url in site_urls:
            self.stdout.write(f"\n{site_url}")

            if scheduling.is_sync_running(site_url, ignore_ids=reaped_ids):
                self.stdout.write(
                    "  SKIPPED — a sync is already running for this site; will retry next tick"
                )
                continue

            if forced is not None:
                cadence = scheduling.get_sync_config(site_url).get(forced, "manual")
                self._start(site_url, forced, f"forced via --scope (cadence: {cadence})", dry_run)
                started += 1
                continue

            rows = scheduling.due_modules(site_url, now=now)
            due = [r for r in rows if r["due"]]
            if not due:
                for r in rows:
                    self.stdout.write(f"  not due      {r['module']:<10} — {r['reason']}")
                continue

            # Most overdue first (due_modules already sorted); the rest wait for the next tick.
            winner, deferred = due[0], due[1:]
            self._start(site_url, winner["module"], winner["reason"], dry_run)
            started += 1
            for r in deferred:
                self.stdout.write(
                    f"  DEFERRED     {r['module']:<10} — due ({r['reason']}) but one sync per "
                    f"site per tick; next tick"
                )
            for r in rows:
                if not r["due"]:
                    self.stdout.write(f"  not due      {r['module']:<10} — {r['reason']}")

        verb = "would start" if dry_run else "started"
        self.stdout.write(f"\nDone — {verb} {started} sync(s) across {len(site_urls)} site(s).")
