"""Cancellation and the fields it needs.

A cancelled run is deliberately NOT an error. Two things in this codebase treat `error`
as meaningful: Settings -> Connections renders it as a live problem, and
scheduling.FAILED_RUN_BACKOFF holds a module off for 6 hours after a failed run -- so
recording a cancel as an error would lock you out of the restart you cancelled in order
to make.
"""
from django.test import TestCase

from apps.sync.models import RefreshRun, RefreshStatus

SITE_URL = "sc-domain:fusehealth.com"


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
