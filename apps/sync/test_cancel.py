"""Cancellation and the fields it needs.

A cancelled run is deliberately NOT an error. Two things in this codebase treat `error`
as meaningful: Settings -> Connections renders it as a live problem, and
scheduling.FAILED_RUN_BACKOFF holds a module off for 6 hours after a failed run -- so
recording a cancel as an error would lock you out of the restart you cancelled in order
to make.
"""
import signal
from unittest import mock

from django.test import TestCase

from apps.sync import scheduling
from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus

SITE_URL = "sc-domain:fusehealth.com"
OTHER_SITE = "sc-domain:premierstaff.com"


class RefreshRunCancelFieldsTests(TestCase):
    def test_a_run_can_be_marked_cancelled(self):
        run = RefreshRun.objects.create(site_url=SITE_URL, scope="audit",
                                        status=RefreshStatus.RUNNING)
        run.status = RefreshStatus.CANCELLED
        run.save(update_fields=["status"])

        run.refresh_from_db()
        self.assertEqual(run.status, "cancelled")
        self.assertNotEqual(run.status, RefreshStatus.ERROR)

    def test_skipped_connectors_defaults_to_an_empty_list(self):
        run = RefreshRun.objects.create(site_url=SITE_URL, scope="audit",
                                        status=RefreshStatus.RUNNING)
        run.refresh_from_db()
        self.assertEqual(run.skipped_connectors, [])

    def test_skipped_connectors_round_trips_a_list(self):
        run = RefreshRun.objects.create(
            site_url=SITE_URL, scope="positioning", status=RefreshStatus.RUNNING,
            skipped_connectors=["gsc_keywords", "dataforseo_keywords"],
        )
        run.refresh_from_db()
        self.assertEqual(run.skipped_connectors, ["gsc_keywords", "dataforseo_keywords"])

    def test_a_cancelled_run_does_not_anchor_a_cadence(self):
        """A run that was stopped refreshed nothing, so it must not push the next scheduled
        sync out. This holds today only because every `last_run_at` caller passes an explicit
        status list -- [SUCCESS] or [SUCCESS, ERROR, RUNNING] -- and CANCELLED is in neither.
        That is a silent invariant one careless edit could break, so it is pinned here."""
        from apps.sync import scheduling

        RefreshRun.objects.create(site_url=SITE_URL, scope="backlinks",
                                  status=RefreshStatus.CANCELLED)

        self.assertIsNone(
            scheduling.last_run_at(SITE_URL, "backlinks", [RefreshStatus.SUCCESS])
        )
        self.assertIsNone(
            scheduling.last_run_at(
                SITE_URL, "backlinks",
                [RefreshStatus.SUCCESS, RefreshStatus.ERROR, RefreshStatus.RUNNING],
            )
        )


class TerminateSyncProcessTests(TestCase):
    def test_no_pid_kills_nothing(self):
        """A run created before the pid field existed, or caught mid-spawn, has no pid.
        There is nothing safe to kill, and killing pid 0 or -1 is catastrophic."""
        with mock.patch.object(scheduling.os, "kill") as killer:
            self.assertFalse(scheduling.terminate_sync_process(None))
            self.assertFalse(scheduling.terminate_sync_process(0))
            self.assertFalse(scheduling.terminate_sync_process(-1))
        killer.assert_not_called()

    def test_posix_sends_sigterm(self):
        with mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill") as killer:
            self.assertTrue(scheduling.terminate_sync_process(4321))
        killer.assert_called_once_with(4321, signal.SIGTERM)

    def test_posix_already_gone_counts_as_terminated(self):
        with mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill", side_effect=ProcessLookupError):
            self.assertTrue(scheduling.terminate_sync_process(4321))

    def test_posix_permission_error_reports_failure(self):
        """We could not kill it, so we must not claim we did -- the DB flag is what
        actually stops the run in that case."""
        with mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill", side_effect=PermissionError):
            self.assertFalse(scheduling.terminate_sync_process(4321))

    def test_windows_never_calls_os_kill(self):
        """The mirror of test_windows_never_calls_os_kill for _process_alive, from the
        other direction: killing on Windows must go through TerminateProcess explicitly,
        not through os.kill's accidental mapping onto it."""
        with mock.patch.object(scheduling.sys, "platform", "win32"), \
             mock.patch.object(scheduling, "_windows_terminate", return_value=True) as win, \
             mock.patch.object(scheduling.os, "kill") as killer:
            self.assertTrue(scheduling.terminate_sync_process(4321))
        win.assert_called_once_with(4321)
        killer.assert_not_called()

    def test_liveness_check_is_not_the_kill_helper(self):
        """_process_alive must never terminate anything. It runs on every
        GET /api/sync/active, i.e. every couple of seconds during a sync."""
        with mock.patch.object(scheduling.sys, "platform", "win32"), \
             mock.patch.object(scheduling, "_windows_terminate") as win, \
             mock.patch.object(scheduling, "_windows_process_alive", return_value=True):
            scheduling._process_alive(4321)
        win.assert_not_called()


class ReconcileScopingTests(TestCase):
    def _running_log(self, site, connector):
        return SyncLog.objects.create(connector=connector, site_url=site,
                                      status=SyncStatus.RUNNING, records_written=42)

    def test_site_url_scopes_the_reconcile(self):
        """Cancelling one site must not relabel another site's orphaned rows."""
        mine = self._running_log(SITE_URL, "pagespeed")
        theirs = self._running_log(OTHER_SITE, "pagespeed")

        scheduling.reconcile_orphaned_sync_logs(
            site_url=SITE_URL, message=scheduling.CANCELLED_CONNECTOR_MESSAGE
        )

        mine.refresh_from_db()
        theirs.refresh_from_db()
        self.assertEqual(mine.status, SyncStatus.ERROR)
        self.assertEqual(mine.error_message, scheduling.CANCELLED_CONNECTOR_MESSAGE)
        self.assertEqual(theirs.status, SyncStatus.RUNNING, "other site was touched")

    def test_unscoped_call_still_clears_every_site(self):
        """The scheduler's own periodic call must keep its existing whole-fleet behaviour."""
        self._running_log(SITE_URL, "pagespeed")
        self._running_log(OTHER_SITE, "url_inspection")

        scheduling.reconcile_orphaned_sync_logs()

        self.assertEqual(
            SyncLog.objects.filter(status=SyncStatus.RUNNING).count(), 0
        )

    def test_records_written_is_never_erased(self):
        """What a stopped connector managed to write is a real measurement."""
        log = self._running_log(SITE_URL, "pagespeed")
        scheduling.reconcile_orphaned_sync_logs(site_url=SITE_URL)
        log.refresh_from_db()
        self.assertEqual(log.records_written, 42)

    def test_the_cancel_message_does_not_blame_a_server_restart(self):
        self.assertNotIn("restart", scheduling.CANCELLED_CONNECTOR_MESSAGE.lower())
        self.assertIn("cancel", scheduling.CANCELLED_CONNECTOR_MESSAGE.lower())
