"""Tests for the sync scheduler: cadence due-logic, orphaned-run reaping, and the
run_scheduled_syncs command's contract.

These are the proofs behind the claims in apps/sync/scheduling.py -- particularly that
`manual` never runs automatically and never gets a fabricated next-run date, and that a
`running` row orphaned by a server restart is cleared instead of blocking the site forever.
"""
import os
import sys
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.dashboard.models import ProjectSettings
from apps.sync import scheduling
from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus

SITE = "https://fusehealth.com"


def make_run(site_url, scope, status, age):
    """A RefreshRun that started `age` ago. started_at is auto_now_add, so it has to be
    written back after creation."""
    run = RefreshRun.objects.create(site_url=site_url, scope=scope, status=status)
    started = timezone.now() - age
    RefreshRun.objects.filter(pk=run.pk).update(started_at=started)
    run.refresh_from_db()
    return run


def set_cadences(site_url, **cadences):
    """Set the named cadences and pin EVERY other module to `manual`.

    The pinning is the point. get_sync_config() merges a saved blob over the shipped defaults,
    so a module a test does not mention inherits its real default -- and a test that means
    "exactly these two modules are due" would silently acquire a third the day a new module
    ships with a live default cadence. That is exactly what happened when `organic` was added:
    five fixtures that named all six modules by hand started asserting against seven.
    """
    blob = {m: "manual" for m in scheduling.SYNC_MODULES}
    blob.update(cadences)
    ProjectSettings.objects.update_or_create(
        site_url=site_url, defaults={"data": {"syncConfig": blob}}
    )


class CadenceDueLogicTests(TestCase):
    def test_every_cadence_is_due_after_its_interval_and_not_before(self):
        for cadence, interval in scheduling.CADENCE_INTERVALS.items():
            if interval is None:
                continue
            with self.subTest(cadence=cadence):
                RefreshRun.objects.all().delete()
                # Just inside the window -> not due.
                make_run(SITE, "positions", RefreshStatus.SUCCESS, interval - timedelta(minutes=30))
                due, _ = scheduling.is_due(SITE, "positions", cadence)
                self.assertFalse(due, f"{cadence} went due before its interval elapsed")

                RefreshRun.objects.all().delete()
                # Just past the window -> due.
                make_run(SITE, "positions", RefreshStatus.SUCCESS, interval + timedelta(minutes=30))
                due, _ = scheduling.is_due(SITE, "positions", cadence)
                self.assertTrue(due, f"{cadence} did not go due after its interval elapsed")

    def test_manual_is_never_due_however_old_the_last_run(self):
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=365))
        due, reason = scheduling.is_due(SITE, "positions", "manual")
        self.assertFalse(due)
        self.assertEqual(reason, "manual")

    def test_manual_is_never_due_when_never_run(self):
        due, _ = scheduling.is_due(SITE, "positions", "manual")
        self.assertFalse(due)

    def test_never_run_module_is_due(self):
        due, reason = scheduling.is_due(SITE, "positions", "weekly")
        self.assertTrue(due)
        self.assertEqual(reason, "never synced")

    def test_unknown_cadence_never_runs(self):
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=365))
        due, reason = scheduling.is_due(SITE, "positions", "hourly-ish")
        self.assertFalse(due)
        self.assertIn("unknown cadence", reason)

    def test_failed_run_holds_the_module_off_then_releases_it(self):
        """A run that ends in `error` refreshes nothing, but must still stop the scheduler
        re-firing every hour against a broken credential."""
        make_run(SITE, "positions", RefreshStatus.ERROR, timedelta(hours=1))
        due, reason = scheduling.is_due(SITE, "positions", "weekly")
        self.assertFalse(due)
        self.assertIn("did not succeed", reason)

        RefreshRun.objects.all().delete()
        make_run(SITE, "positions", RefreshStatus.ERROR, scheduling.FAILED_RUN_BACKOFF + timedelta(hours=1))
        due, _ = scheduling.is_due(SITE, "positions", "weekly")
        self.assertTrue(due)

    def test_a_full_refresh_counts_as_a_run_of_the_modules_it_covers(self):
        make_run(SITE, "all", RefreshStatus.SUCCESS, timedelta(hours=1))
        due, _ = scheduling.is_due(SITE, "positions", "weekly")
        self.assertFalse(due, "'all' runs every positioning connector; it must reset that clock")

    def test_a_full_refresh_does_not_count_as_an_ads_run(self):
        """sync_all()'s connector list has no google_ads, so a full refresh never actually
        pulls Ads data and must not be allowed to reset the Ads clock."""
        make_run(SITE, "all", RefreshStatus.SUCCESS, timedelta(hours=1))
        due, reason = scheduling.is_due(SITE, "ads", "12h")
        self.assertTrue(due)
        self.assertEqual(reason, "never synced")

    def test_due_modules_orders_most_overdue_first(self):
        set_cadences(SITE, positions="weekly", backlinks="weekly", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=8))
        make_run(SITE, "backlinks", RefreshStatus.SUCCESS, timedelta(days=30))
        rows = scheduling.due_modules(SITE)
        self.assertEqual([r["module"] for r in rows[:2]], ["backlinks", "positions"])
        self.assertTrue(all(r["due"] for r in rows[:2]))
        self.assertTrue(all(not r["due"] for r in rows[2:]))


class NextRunTests(TestCase):
    def test_weekly_module_gets_a_real_next_run(self):
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=2))
        nxt = scheduling.next_run_for(SITE, "positions", "weekly")
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.date(), (timezone.now() + timedelta(days=5)).date())

    def test_manual_module_never_gets_a_next_run(self):
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=2))
        self.assertIsNone(scheduling.next_run_for(SITE, "positions", "manual"))

    def test_overdue_module_reports_now_not_a_past_date(self):
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=30))
        nxt = scheduling.next_run_for(SITE, "positions", "weekly")
        self.assertEqual(nxt.date(), timezone.now().date())

    def test_never_run_module_has_no_next_run(self):
        self.assertIsNone(scheduling.next_run_for(SITE, "positions", "weekly"))

    def test_schedule_summary_picks_the_soonest_and_names_its_day(self):
        set_cadences(SITE, positions="weekly", backlinks="monthly", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=2))   # due in 5d
        make_run(SITE, "backlinks", RefreshStatus.SUCCESS, timedelta(days=2))   # due in 28d
        summary = scheduling.schedule_summary(SITE)
        expected = timezone.localtime(timezone.now() + timedelta(days=5))
        self.assertEqual(summary["next_run"], expected.date().isoformat())
        self.assertEqual(summary["day"], expected.strftime("%A"))

    def test_schedule_summary_is_none_when_everything_is_manual(self):
        set_cadences(SITE, positions="manual", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=2))
        self.assertEqual(scheduling.schedule_summary(SITE), {"next_run": None, "day": None})

    def test_settings_service_serves_the_same_real_next_run(self):
        from apps.dashboard.services.settings_service import _sync_summary_raw

        set_cadences(SITE, positions="weekly", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=2))
        summary = _sync_summary_raw(SITE)
        self.assertEqual(summary["next_run"], (timezone.now() + timedelta(days=5)).date().isoformat())
        self.assertIsNotNone(summary["day"])
        self.assertIn("last_run", summary)


class ReapOrphanedRunsTests(TestCase):
    def test_run_older_than_the_timeout_becomes_error(self):
        run = make_run(SITE, "all", RefreshStatus.RUNNING, scheduling.RUN_TIMEOUT + timedelta(hours=1))
        reaped = scheduling.reap_orphaned_runs()
        self.assertEqual([r.pk for r in reaped], [run.pk])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.ERROR)
        self.assertIsNotNone(run.finished_at)
        self.assertIn("server restart", run.error_message)

    def test_recent_running_run_is_left_alone(self):
        run = make_run(SITE, "all", RefreshStatus.RUNNING, timedelta(minutes=5))
        self.assertEqual(scheduling.reap_orphaned_runs(), [])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.RUNNING)

    def test_dry_run_reports_but_writes_nothing(self):
        run = make_run(SITE, "all", RefreshStatus.RUNNING, scheduling.RUN_TIMEOUT + timedelta(hours=1))
        reaped = scheduling.reap_orphaned_runs(dry_run=True)
        self.assertEqual([r.pk for r in reaped], [run.pk])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.RUNNING)

    def test_reaping_is_idempotent(self):
        make_run(SITE, "all", RefreshStatus.RUNNING, scheduling.RUN_TIMEOUT + timedelta(hours=1))
        scheduling.reap_orphaned_runs()
        self.assertEqual(scheduling.reap_orphaned_runs(), [])

    def test_reaping_unblocks_the_concurrency_guard(self):
        make_run(SITE, "all", RefreshStatus.RUNNING, scheduling.RUN_TIMEOUT + timedelta(hours=1))
        self.assertTrue(scheduling.is_sync_running(SITE))
        scheduling.reap_orphaned_runs()
        self.assertFalse(scheduling.is_sync_running(SITE))


class PidAwareReapTests(TestCase):
    """The sync now runs as its own process (RefreshRun.pid), so a dead pid is direct evidence
    a run is orphaned -- it no longer has to wait out the full RUN_TIMEOUT (2h) to be cleared.
    This is what makes 'refresh-all survives navigating away or reloading the page' also mean
    'a genuinely killed run gets noticed promptly' rather than trading one silent-hang failure
    mode for another."""

    def _run_with_pid(self, pid, age=timedelta(minutes=10)):
        run = make_run(SITE, "all", RefreshStatus.RUNNING, age)
        RefreshRun.objects.filter(pk=run.pk).update(pid=pid)
        run.refresh_from_db()
        return run

    @mock.patch.object(scheduling, "_process_alive", return_value=False)
    def test_dead_pid_is_reaped_well_before_the_timeout(self, _mock_alive):
        run = self._run_with_pid(pid=99999)  # 10 minutes old -- nowhere near RUN_TIMEOUT (2h)
        reaped = scheduling.reap_orphaned_runs()
        self.assertEqual([r.pk for r in reaped], [run.pk])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.ERROR)
        self.assertIn(str(run.pid), run.error_message)
        self.assertIn("no longer running", run.error_message)

    @mock.patch.object(scheduling, "_process_alive", return_value=True)
    def test_live_pid_is_never_reaped_even_if_old(self, _mock_alive):
        run = self._run_with_pid(pid=1, age=timedelta(hours=1, minutes=50))  # under RUN_TIMEOUT
        self.assertEqual(scheduling.reap_orphaned_runs(), [])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.RUNNING)

    @mock.patch.object(scheduling, "_process_alive", return_value=True)
    def test_a_run_past_the_timeout_is_still_reaped_even_with_a_live_pid(self, _mock_alive):
        """The pid check is a faster path to the SAME conclusion, not a replacement for the
        timeout: a live-but-permanently-wedged process must still eventually be cleared."""
        run = self._run_with_pid(pid=1, age=scheduling.RUN_TIMEOUT + timedelta(minutes=1))
        reaped = scheduling.reap_orphaned_runs()
        self.assertEqual([r.pk for r in reaped], [run.pk])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.ERROR)
        self.assertIn("server restart", run.error_message)  # the timeout message, not the pid one

    @mock.patch.object(scheduling, "_process_alive", return_value=False)
    def test_a_freshly_spawned_run_is_not_pid_checked_during_the_grace_period(self, mock_alive):
        """start_sync_run() creates the row, THEN spawns the process and writes the pid back --
        so a row can briefly have pid=None (or, under a slow spawn, a pid the OS hasn't
        scheduled yet) moments after creation. PID_GRACE stops the reaper from treating that
        normal startup window as evidence of death."""
        run = self._run_with_pid(pid=99999, age=scheduling.PID_GRACE - timedelta(seconds=30))
        self.assertEqual(scheduling.reap_orphaned_runs(), [])
        mock_alive.assert_not_called()
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.RUNNING)

    def test_a_run_with_no_pid_falls_back_to_the_timeout_untouched(self):
        """Rows created before the pid column existed, or caught exactly mid-spawn, must not be
        treated as dead just because pid is unknown -- NULL means unknown, never dead."""
        run = self._run_with_pid(pid=None, age=timedelta(minutes=30))
        self.assertEqual(scheduling.reap_orphaned_runs(), [])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.RUNNING)


class OrphanedSyncLogTests(TestCase):
    """Reaping the RefreshRun was only half the job.

    BaseConnector.sync() marks its SyncLog row `running` on the way in and rewrites it on the
    way out. When the sync PROCESS is killed in between, nothing ever rewrites it -- and unlike
    RefreshRun, SyncLog had no reaper at all, so the row stayed `running` permanently. Settings
    -> Data pipeline reads SyncLog, so the connector that was in flight when the process died
    reported "Last synced: never" forever, even with real rows sitting in its analytics table.
    That is exactly what happened to pagespeed and url_inspection on premierstaff.com: three
    consecutive audit runs were killed by server restarts, and both cards read "never" while
    page_speed held 96 real Lighthouse rows.

    The invariant that makes this safe: connector.sync() is only ever reached through
    sync_engine.sync_all/sync_page, both of which require a run_id, and start_sync_run creates
    that RefreshRun row BEFORE spawning the process. So a `running` SyncLog row whose site has
    no `running` RefreshRun cannot be making progress -- it is orphaned by construction.
    """

    def _running_log(self, connector, site_url=SITE, **kwargs):
        return SyncLog.objects.create(
            connector=connector, site_url=site_url, status=SyncStatus.RUNNING, **kwargs
        )

    def test_running_row_with_no_run_in_flight_is_reconciled(self):
        log = self._running_log("pagespeed")
        scheduling.reap_orphaned_runs()
        log.refresh_from_db()
        self.assertEqual(log.status, SyncStatus.ERROR)
        self.assertIn("never reported a result", log.error_message)

    def test_running_row_is_left_alone_while_its_site_is_actually_syncing(self):
        make_run(SITE, "audit", RefreshStatus.RUNNING, timedelta(minutes=5))
        log = self._running_log("pagespeed")
        scheduling.reap_orphaned_runs()
        log.refresh_from_db()
        self.assertEqual(log.status, SyncStatus.RUNNING)

    def test_a_run_on_another_site_does_not_protect_this_one(self):
        make_run("https://other.example", "audit", RefreshStatus.RUNNING, timedelta(minutes=5))
        log = self._running_log("pagespeed")
        scheduling.reap_orphaned_runs()
        log.refresh_from_db()
        self.assertEqual(log.status, SyncStatus.ERROR)

    def test_reaping_a_dead_run_also_reconciles_the_connector_it_died_inside(self):
        """The whole point: the run and the connector row are cleared by the same tick, so the
        Settings card stops claiming `never` the moment the reaper notices the run is gone."""
        run = make_run(SITE, "audit", RefreshStatus.RUNNING,
                       scheduling.RUN_TIMEOUT + timedelta(hours=1))
        log = self._running_log("pagespeed")
        reaped = scheduling.reap_orphaned_runs()
        self.assertEqual([r.pk for r in reaped], [run.pk])
        log.refresh_from_db()
        self.assertEqual(log.status, SyncStatus.ERROR)

    def test_rows_in_any_other_status_are_untouched(self):
        stamped = timezone.now() - timedelta(days=1)
        for status in (SyncStatus.SUCCESS, SyncStatus.ERROR, SyncStatus.NEVER):
            SyncLog.objects.create(
                connector=f"c_{status}", site_url=SITE, status=status,
                last_synced=stamped, records_written=7, error_message="kept",
            )
        scheduling.reap_orphaned_runs()
        for status in (SyncStatus.SUCCESS, SyncStatus.ERROR, SyncStatus.NEVER):
            log = SyncLog.objects.get(connector=f"c_{status}", site_url=SITE)
            self.assertEqual(log.status, status)
            self.assertEqual(log.last_synced, stamped)
            self.assertEqual(log.error_message, "kept")

    def test_what_the_dead_run_did_write_is_preserved(self):
        """url_inspection wrote 150 rows before its process was killed. That count is a
        measurement, not a leftover -- reconciling the status must not erase it."""
        stamped = timezone.now() - timedelta(days=2)
        log = self._running_log("url_inspection", records_written=150, last_synced=stamped)
        scheduling.reap_orphaned_runs()
        log.refresh_from_db()
        self.assertEqual(log.records_written, 150)
        self.assertEqual(log.last_synced, stamped)

    def test_dry_run_writes_nothing(self):
        log = self._running_log("pagespeed")
        scheduling.reap_orphaned_runs(dry_run=True)
        log.refresh_from_db()
        self.assertEqual(log.status, SyncStatus.RUNNING)

    def test_reconciling_is_idempotent(self):
        self._running_log("pagespeed")
        scheduling.reap_orphaned_runs()
        self.assertEqual(scheduling.reconcile_orphaned_sync_logs(), [])


class RunScheduledSyncsCommandTests(TestCase):
    """The command is exercised with start_sync_run patched out -- it spawns a thread that
    calls real connectors, which a test must never do."""

    def _run(self, *args, **kwargs):
        out = StringIO()
        with mock.patch("pipeline.services.site_service.get_active_site_ids", return_value=[SITE]), \
             mock.patch("apps.dashboard.services.sync_api_service.start_sync_run") as started:
            started.side_effect = lambda site_url, scope, **kw: {"task_id": 999, "steps": ["gsc"], "est_cost": 0}
            call_command("run_scheduled_syncs", *args, stdout=out, **kwargs)
        return out.getvalue(), started

    def test_dry_run_with_nothing_due_starts_nothing(self):
        set_cadences(SITE, positions="weekly", backlinks="weekly", audit="monthly",
                     keywords="monthly", ads="12h", ai="weekly")
        for scope in ("positions", "backlinks", "audit", "keywords", "ads", "ai"):
            make_run(SITE, scope, RefreshStatus.SUCCESS, timedelta(minutes=10))
        output, started = self._run("--dry-run")
        started.assert_not_called()
        self.assertIn("would start 0 sync(s)", output)
        self.assertNotIn("WOULD START", output)

    def test_dry_run_starts_nothing_even_when_work_is_due(self):
        set_cadences(SITE, positions="weekly", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=30))
        output, started = self._run("--dry-run")
        started.assert_not_called()
        self.assertIn("WOULD START  positions", output)

    def test_starts_exactly_one_due_module_per_site(self):
        set_cadences(SITE, positions="weekly", backlinks="weekly", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=30))
        make_run(SITE, "backlinks", RefreshStatus.SUCCESS, timedelta(days=8))
        output, started = self._run()
        self.assertEqual(started.call_count, 1)
        self.assertEqual(started.call_args.args, (SITE, "positions"))  # most overdue wins
        self.assertIn("DEFERRED     backlinks", output)

    def test_skips_a_site_that_already_has_a_sync_running(self):
        set_cadences(SITE, positions="weekly", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=30))
        make_run(SITE, "all", RefreshStatus.RUNNING, timedelta(minutes=5))
        output, started = self._run()
        started.assert_not_called()
        self.assertIn("already running", output)

    def test_running_twice_does_not_double_sync(self):
        """Second invocation sees the RefreshRun the first one left `running` and stands down."""
        set_cadences(SITE, positions="weekly", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=30))

        out = StringIO()
        with mock.patch("pipeline.services.site_service.get_active_site_ids", return_value=[SITE]), \
             mock.patch("apps.dashboard.services.sync_api_service.start_sync_run") as started:
            # Stand in for the real thing: it creates the `running` row, which is what makes
            # the second invocation a no-op.
            started.side_effect = lambda site_url, scope, **kw: {
                "task_id": RefreshRun.objects.create(
                    site_url=site_url, scope=scope, status=RefreshStatus.RUNNING).pk,
                "steps": ["gsc"], "est_cost": 0,
            }
            call_command("run_scheduled_syncs", stdout=out)
            call_command("run_scheduled_syncs", stdout=out)
            self.assertEqual(started.call_count, 1)

    def test_scope_forces_a_manual_module(self):
        set_cadences(SITE, positions="manual", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(minutes=5))
        output, started = self._run("--scope", "positions")
        self.assertEqual(started.call_args.args, (SITE, "positions"))
        self.assertIn("forced via --scope", output)

    def test_unknown_scope_is_rejected(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self._run("--scope", "not-a-module")

    def test_unknown_site_is_rejected(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self._run("--site", "https://nope.example")

    def test_reaps_before_deciding(self):
        """The orphan is cleared in the same invocation that then decides what is due --
        without that ordering it would block this site's guard forever."""
        set_cadences(SITE, positions="weekly", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=30))
        orphan = make_run(SITE, "all", RefreshStatus.RUNNING,
                          scheduling.FAILED_RUN_BACKOFF + timedelta(hours=2))
        output, started = self._run()
        orphan.refresh_from_db()
        self.assertEqual(orphan.status, RefreshStatus.ERROR)
        self.assertIn("REAPED", output)
        self.assertEqual(started.call_count, 1, "the orphan must not block this site")

    def test_a_just_reaped_orphan_still_gets_the_failure_backoff(self):
        """Deliberate: an orphaned run is a failed attempt that may already have spent metered
        API calls, so the module waits out FAILED_RUN_BACKOFF rather than re-firing on the very
        next tick after a restart. Bounded, unlike the old permanent block."""
        set_cadences(SITE, positions="weekly", backlinks="manual", audit="manual",
                     keywords="manual", ads="manual", ai="manual")
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=30))
        make_run(SITE, "positions", RefreshStatus.RUNNING, scheduling.RUN_TIMEOUT + timedelta(minutes=5))
        output, started = self._run()
        started.assert_not_called()
        self.assertIn("REAPED", output)
        self.assertIn("retry after", output)


class ProcessAliveTests(TestCase):
    """`_process_alive` itself, which every other test in this file mocks away.

    That blanket mocking is exactly why the Windows bug below shipped unnoticed: the reaper's
    logic was covered, but the one function that touches the OS never was.
    """

    def _no_psutil(self):
        """Force the fallback path. psutil is a requirement, but the fallback must still be
        correct — a venv built before it was added still runs this code."""
        return mock.patch.dict(sys.modules, {"psutil": None})

    def test_windows_never_calls_os_kill(self):
        """os.kill(pid, 0) is NOT an existence check on Windows.

        CPython maps every signal other than CTRL_C_EVENT/CTRL_BREAK_EVENT onto TerminateProcess,
        so the "is this sync still alive?" probe would KILL the sync it was asking about — and
        the reaper runs on every GET /api/sync/active.
        """
        with self._no_psutil(), \
             mock.patch.object(scheduling.sys, "platform", "win32"), \
             mock.patch.object(scheduling, "_windows_process_alive", return_value=True), \
             mock.patch.object(scheduling.os, "kill") as killer:
            scheduling._process_alive(4242)
        killer.assert_not_called()

    def test_windows_reports_a_dead_pid_as_dead(self):
        """The old bare `except Exception: return True` swallowed Windows' OSError for an unknown
        pid, so dead runs were never reaped and sat at 'running' until RUN_TIMEOUT (2h)."""
        with self._no_psutil(), \
             mock.patch.object(scheduling.sys, "platform", "win32"), \
             mock.patch.object(scheduling, "_windows_process_alive", return_value=False):
            self.assertIs(scheduling._process_alive(4242), False)

    def test_posix_dead_pid_is_false(self):
        with self._no_psutil(), \
             mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill", side_effect=ProcessLookupError):
            self.assertIs(scheduling._process_alive(4242), False)

    def test_posix_live_pid_is_true(self):
        with self._no_psutil(), \
             mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill", return_value=None):
            self.assertIs(scheduling._process_alive(4242), True)

    def test_posix_permission_error_means_it_exists(self):
        """Owned by another user — that is an answer, not an uncertainty."""
        with self._no_psutil(), \
             mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill", side_effect=PermissionError):
            self.assertIs(scheduling._process_alive(4242), True)

    def test_psutil_is_preferred_when_installed(self):
        fake = mock.Mock()
        fake.pid_exists.return_value = False
        with mock.patch.dict(sys.modules, {"psutil": fake}), \
             mock.patch.object(scheduling.os, "kill") as killer:
            self.assertIs(scheduling._process_alive(4242), False)
        fake.pid_exists.assert_called_once_with(4242)
        killer.assert_not_called()

    def test_this_processs_own_pid_is_alive_on_the_real_platform(self):
        """End-to-end on whatever OS the suite is running on, with no mocking at all."""
        self.assertIs(scheduling._process_alive(os.getpid()), True)


class OrganicTrafficModuleTests(TestCase):
    """The Overview headline KPIs (organic clicks / impressions / avg position) are written by
    the `gsc` connector into `seo_daily_totals`. Until 2026-08-18 no schedulable module ran it:
    `SYNC_MODULES` was ("positions", "backlinks", "audit", "keywords", "ads", "ai"), and the
    connector lists behind those six contain `gsc_keywords`, `gsc_pages` and `ga4` but never
    plain `gsc`. So the one number the dashboard opens on could ONLY be refreshed by a human
    pressing "Refresh all" — on premierstaff.com it therefore sat three weeks stale while the
    Settings panel truthfully reported that everything the user HAD scheduled was running.

    These tests pin the fix: a module whose connectors include `gsc`, schedulable like the rest.
    """

    def test_some_schedulable_module_actually_runs_the_gsc_connector(self):
        """The regression itself. If this fails, the Overview KPIs are unschedulable again."""
        from pipeline.services.sync_engine import PAGE_CONNECTORS

        runs_gsc = [
            m for m in scheduling.SYNC_MODULES
            if "gsc" in PAGE_CONNECTORS.get(scheduling._SCOPE_TO_PAGE_KEY.get(m, m), [])
        ]
        self.assertTrue(
            runs_gsc,
            "No schedulable module runs the `gsc` connector, so nothing can keep the Overview "
            "organic clicks/impressions/position fresh except a manual Refresh all.",
        )

    def test_organic_resolves_to_the_gsc_and_ga4_connectors(self):
        """Same resolution the scheduler and the sync API both go through, so the row the user
        sees in Settings and the connectors that actually run cannot drift apart."""
        from apps.dashboard.services.sync_api_service import _connectors_for_scope

        self.assertEqual(_connectors_for_scope("organic"), ["gsc", "ga4"])

    def test_organic_has_a_shipped_default_cadence(self):
        """Search Console and GA4 cost nothing per call, so the default is a real cadence, not
        `manual` — an unconfigured project must still keep its headline numbers current."""
        from apps.dashboard.services.settings_service import DEFAULT_SETTINGS_BLOB

        cadence = DEFAULT_SETTINGS_BLOB["syncConfig"].get("organic")
        self.assertIn(cadence, scheduling.CADENCE_INTERVALS)
        self.assertIsNotNone(
            scheduling.CADENCE_INTERVALS[cadence],
            "`organic` must not default to manual: GSC/GA4 are free and this is the module "
            "that keeps the Overview honest.",
        )

    def test_a_full_refresh_counts_as_an_organic_run(self):
        """`gsc` and `ga4` are both in ALL_CONNECTORS, so Refresh all genuinely refreshes this
        module and must reset its clock rather than re-running it an hour later."""
        make_run(SITE, "all", RefreshStatus.SUCCESS, timedelta(hours=1))
        due, _ = scheduling.is_due(SITE, "organic", "daily")
        self.assertFalse(due)

    def test_organic_is_not_due_before_a_day_has_passed(self):
        make_run(SITE, "organic", RefreshStatus.SUCCESS, timedelta(hours=23))
        self.assertFalse(scheduling.is_due(SITE, "organic", "daily")[0])

    def test_organic_is_due_once_a_day_has_passed(self):
        make_run(SITE, "organic", RefreshStatus.SUCCESS, timedelta(hours=25))
        self.assertTrue(scheduling.is_due(SITE, "organic", "daily")[0])

    def test_the_command_accepts_organic_as_a_forced_scope(self):
        """`--scope` validates against SYNC_MODULES, so an unregistered module is a hard
        CommandError -- which is how an operator would discover the gap, if they looked."""
        out = StringIO()
        with mock.patch("pipeline.services.site_service.get_active_site_ids", return_value=[SITE]):
            call_command("run_scheduled_syncs", "--dry-run", "--site", SITE,
                         "--scope", "organic", stdout=out)
        self.assertIn("WOULD START  organic", out.getvalue())


class ScopeAliasMirrorTests(TestCase):
    """`scheduling._SCOPE_TO_PAGE_KEY` is a hand-copy of `sync_api_service.SCOPE_ALIASES`.
    A copy that drifts is worse than no copy: the scheduler would decide "is this module due?"
    against one connector list and then start a run that fetches a different one. These pin the
    copy to the original."""

    def test_the_two_alias_maps_agree(self):
        from apps.dashboard.services.sync_api_service import SCOPE_ALIASES

        for scope, page in scheduling._SCOPE_TO_PAGE_KEY.items():
            self.assertEqual(
                SCOPE_ALIASES.get(scope), page,
                f"scheduling maps {scope!r} to {page!r} but sync_api_service maps it to "
                f"{SCOPE_ALIASES.get(scope)!r} — the scheduler and the runner would disagree.",
            )

    def test_every_schedulable_module_resolves_to_real_connectors(self):
        """A module the UI can set a cadence on but whose scope runs nothing is a control that
        appears to schedule work and schedules none."""
        from apps.dashboard.services.sync_api_service import _connectors_for_scope

        for module in scheduling.SYNC_MODULES:
            self.assertTrue(
                _connectors_for_scope(module),
                f"{module!r} is schedulable but resolves to no connectors.",
            )

    def test_every_schedulable_module_has_a_shipped_default(self):
        """get_sync_config() merges saved values OVER the defaults and drops unknown keys, so a
        module absent from DEFAULT_SETTINGS_BLOB can never be scheduled at all."""
        from apps.dashboard.services.settings_service import DEFAULT_SETTINGS_BLOB

        self.assertEqual(
            set(DEFAULT_SETTINGS_BLOB["syncConfig"]), set(scheduling.SYNC_MODULES),
        )


class PerModuleScheduleTests(TestCase):
    """`_sync_summary_raw` used to serve THREE values for the whole panel -- one next_run, one
    last_run, one weekday -- so a user looking at six cadence dropdowns had no way to tell
    which module the dates belonged to, or that one of them had not run in three weeks. The
    header dates are kept (they are still the "what happens next on this site" answer) and a
    per-module breakdown is added alongside, derived from the same `due_modules()` the
    scheduler itself acts on."""

    def _summary(self):
        from apps.dashboard.services.settings_service import _sync_summary_raw

        return _sync_summary_raw(SITE)

    def test_every_schedulable_module_appears_exactly_once(self):
        by_module = {m["module"]: m for m in self._summary()["modules"]}
        self.assertEqual(set(by_module), set(scheduling.SYNC_MODULES))
        self.assertEqual(len(self._summary()["modules"]), len(scheduling.SYNC_MODULES))

    def test_a_module_reports_its_own_last_success_not_the_sites(self):
        """The bug this exists to prevent: one site-wide "Last run" made a three-week-stale
        module look as fresh as the one that ran an hour ago."""
        set_cadences(SITE, organic="daily", positions="weekly")
        make_run(SITE, "organic", RefreshStatus.SUCCESS, timedelta(hours=1))
        make_run(SITE, "positions", RefreshStatus.SUCCESS, timedelta(days=21))

        by_module = {m["module"]: m for m in self._summary()["modules"]}
        organic = timezone.now() - timedelta(hours=1)
        positions = timezone.now() - timedelta(days=21)
        self.assertAlmostEqual(
            (timezone.datetime.fromisoformat(by_module["organic"]["last_success"]) - organic)
            .total_seconds(), 0, delta=5,
        )
        self.assertAlmostEqual(
            (timezone.datetime.fromisoformat(by_module["positions"]["last_success"]) - positions)
            .total_seconds(), 0, delta=5,
        )

    def test_a_module_that_never_ran_reports_null_not_a_date(self):
        by_module = {m["module"]: m for m in self._summary()["modules"]}
        self.assertIsNone(by_module["backlinks"]["last_success"])
        self.assertIsNone(by_module["backlinks"]["next_run"])

    def test_a_manual_module_gets_no_next_run_even_after_a_successful_one(self):
        set_cadences(SITE, ai="manual")
        make_run(SITE, "ai", RefreshStatus.SUCCESS, timedelta(days=1))
        by_module = {m["module"]: m for m in self._summary()["modules"]}
        self.assertIsNotNone(by_module["ai"]["last_success"])
        self.assertIsNone(by_module["ai"]["next_run"])
        self.assertEqual(by_module["ai"]["cadence"], "manual")

    def test_each_row_carries_the_cadence_and_the_due_reason_the_scheduler_uses(self):
        set_cadences(SITE, organic="daily")
        make_run(SITE, "organic", RefreshStatus.SUCCESS, timedelta(days=3))
        organic = next(m for m in self._summary()["modules"] if m["module"] == "organic")
        self.assertEqual(organic["cadence"], "daily")
        self.assertTrue(organic["due"])
        self.assertIn("daily", organic["reason"])

    def test_the_header_values_are_unchanged(self):
        """The SPA dereferences next_run/day/last_run unguarded; adding a key must not move
        them."""
        summary = self._summary()
        for key in ("next_run", "day", "last_run"):
            self.assertIn(key, summary)
