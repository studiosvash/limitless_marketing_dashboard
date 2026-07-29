"""Tests for the sync scheduler: cadence due-logic, orphaned-run reaping, and the
run_scheduled_syncs command's contract.

These are the proofs behind the claims in apps/sync/scheduling.py -- particularly that
`manual` never runs automatically and never gets a fabricated next-run date, and that a
`running` row orphaned by a server restart is cleared instead of blocking the site forever.
"""
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
