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
from apps.sync.models import RefreshRun, RefreshStatus

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
    ProjectSettings.objects.update_or_create(
        site_url=site_url, defaults={"data": {"syncConfig": cadences}}
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
