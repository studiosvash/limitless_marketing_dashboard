"""`manage.py run_sync` tells the engine whether anyone is watching.

A run with no `triggered_by` was started by the scheduler (or another unattended caller);
one with a user came from a click. The SERP connectors price and pace themselves on that
(normal-priority queue + longer poll window when unattended), so the flag has to travel
from the row into `sync_page`/`sync_all`.
"""
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.sync.models import RefreshRun, RefreshStatus

SITE = "premierstaff.com"


def _summary():
    return {"completed": 1, "total": 1, "records_written": 0, "errors": []}


class RunSyncScheduledFlagTests(TestCase):
    def _run(self, run):
        out = StringIO()
        with mock.patch("pipeline.services.sync_engine.sync_page", return_value=_summary()) as page, \
             mock.patch("pipeline.services.sync_engine.sync_all", return_value=_summary()) as full:
            call_command("run_sync", "--run-id", str(run.pk), stdout=out)
        return page, full

    def test_a_run_nobody_triggered_is_scheduled(self):
        run = RefreshRun.objects.create(site_url=SITE, scope="positions", site_pk=21,
                                        status=RefreshStatus.RUNNING)
        page, _ = self._run(run)
        self.assertTrue(page.call_args.kwargs.get("scheduled"))
        self.assertEqual(page.call_args.kwargs.get("site_pk"), 21)

    def test_a_run_a_user_clicked_is_not_scheduled(self):
        user = get_user_model().objects.create_user("founder", password="x")
        run = RefreshRun.objects.create(site_url=SITE, scope="positions", site_pk=21,
                                        status=RefreshStatus.RUNNING, triggered_by=user)
        page, _ = self._run(run)
        self.assertFalse(page.call_args.kwargs.get("scheduled"))

    def test_a_full_run_carries_the_flag_too(self):
        run = RefreshRun.objects.create(site_url=SITE, scope="all",
                                        status=RefreshStatus.RUNNING)
        _, full = self._run(run)
        self.assertTrue(full.call_args.kwargs.get("scheduled"))
