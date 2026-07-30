"""Tests that actually EXECUTE sync_all() and sync_page().

Why this file exists: every other sync test patches the background thread away
(`@patch("apps.dashboard.services.sync_api_service.threading.Thread")` in
test_sync_and_research.py), so they assert the HTTP contract and never run a single line of
the engine. That gap let commit 2260104 ship a `NameError` on the FIRST statement of
sync_all's loop -- `incremental_kws` and `page` are sync_page's variables and do not exist in
sync_all. Because those lines sat outside the try/except, the exception escaped sync_all, the
daemon thread died silently, and the RefreshRun row stayed at status='running'/completed_count=0
forever. scope='all' was 100% broken in production and no test noticed.

These tests run the loop against fake connectors, so they need no network and no analytics DB.
`_run_post_sync` is patched out because refresh_domain_checks() inside it makes six live
network requests.
"""
from unittest.mock import patch

from django.test import TestCase

from apps.sync.models import RefreshRun, RefreshStatus
from pipeline.services import sync_engine
from pipeline.services.sync_engine import ALL_CONNECTORS, PAGE_CONNECTORS, sync_all, sync_page

SITE_URL = "sc-domain:fusehealth.com"


class FakeConnector:
    """Minimal stand-in for BaseConnector: records how it was called."""

    def __init__(self, name, records=5, status="success", raises=None):
        self.name = name
        self._records = records
        self._status = status
        self._raises = raises
        self.sync_calls = []

    def sync(self, site_id=None):
        self.sync_calls.append(site_id)
        if self._raises:
            raise self._raises
        result = {"status": self._status, "records_written": self._records}
        if self._status == "error":
            result["error"] = f"{self.name} exploded"
        return result


class SyncEngineTests(TestCase):
    def setUp(self):
        # Every test in this file runs the connector loop; none of them should reach the
        # network via the post-sync hooks.
        p = patch.object(sync_engine, "_run_post_sync", lambda *a, **kw: None)
        p.start()
        self.addCleanup(p.stop)
        self.built = {}

    def _stub_connectors(self, **overrides):
        """Patch _get_connector to hand out FakeConnectors, recording each one."""

        def factory(name):
            if name in overrides and overrides[name] is None:
                return None  # simulates missing credentials
            conn = overrides.get(name) or FakeConnector(name)
            self.built[name] = conn
            return conn

        p = patch.object(sync_engine, "_get_connector", side_effect=factory)
        p.start()
        self.addCleanup(p.stop)

    def _run_row(self, scope="all"):
        return RefreshRun.objects.create(
            site_url=SITE_URL, scope=scope, status=RefreshStatus.RUNNING
        )

    # ------------------------------------------------------------------ sync_all

    def test_sync_all_runs_every_connector_to_completion(self):
        """The regression test for 2260104: before the fix this raised NameError on connector 1."""
        self._stub_connectors()
        run = self._run_row()

        summary = sync_all(SITE_URL, run.pk)

        self.assertEqual(summary["completed"], len(ALL_CONNECTORS))
        self.assertEqual(summary["errors"], [])
        self.assertEqual(sorted(self.built), sorted(ALL_CONNECTORS))
        for name, conn in self.built.items():
            self.assertEqual(conn.sync_calls, [SITE_URL], f"{name} was not synced exactly once")

        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.SUCCESS)
        self.assertEqual(run.completed_count, len(ALL_CONNECTORS))
        self.assertEqual(run.total_count, len(ALL_CONNECTORS))
        self.assertEqual(run.records_written, 5 * len(ALL_CONNECTORS))
        self.assertIsNone(run.error_message)
        self.assertIsNotNone(run.finished_at)

    def test_sync_all_never_narrows_keywords(self):
        """scope='all' means all. Narrowing belongs to positioning_new, not here."""
        self._stub_connectors()
        sync_all(SITE_URL, self._run_row().pk)

        for name, conn in self.built.items():
            self.assertFalse(
                hasattr(conn, "only_keywords"),
                f"{name} was narrowed during a full refresh -- keywords would be silently skipped",
            )

    def test_sync_all_records_a_failing_connector_but_finishes_the_rest(self):
        self._stub_connectors(ga4=FakeConnector("ga4", records=0, status="error"))
        run = self._run_row()

        summary = sync_all(SITE_URL, run.pk)

        self.assertEqual(summary["completed"], len(ALL_CONNECTORS))
        self.assertEqual(summary["errors"], ["ga4: ga4 exploded"])
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.ERROR)
        self.assertIn("ga4", run.error_message)
        # The other 13 still ran and their records still counted.
        self.assertEqual(run.records_written, 5 * (len(ALL_CONNECTORS) - 1))

    def test_sync_all_survives_a_connector_that_raises(self):
        """A raising connector must be caught inside the loop, not kill the whole run."""
        self._stub_connectors(gsc=FakeConnector("gsc", raises=RuntimeError("boom")))
        run = self._run_row()

        sync_all(SITE_URL, run.pk)

        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.ERROR)
        self.assertIn("boom", run.error_message)
        self.assertEqual(run.completed_count, len(ALL_CONNECTORS))

    def test_sync_all_skips_an_unavailable_connector_and_keeps_going(self):
        self._stub_connectors(dataforseo_backlinks=None)
        run = self._run_row()

        sync_all(SITE_URL, run.pk)

        self.assertNotIn("dataforseo_backlinks", self.built)
        run.refresh_from_db()
        self.assertEqual(run.completed_count, len(ALL_CONNECTORS))
        self.assertEqual(run.status, RefreshStatus.SUCCESS)

    # ----------------------------------------------------------------- sync_page

    def test_sync_page_runs_only_that_pages_connectors(self):
        self._stub_connectors()
        run = self._run_row(scope="overview")

        summary = sync_page("overview", SITE_URL, run.pk)

        self.assertEqual(sorted(self.built), sorted(PAGE_CONNECTORS["overview"]))
        self.assertEqual(summary["completed"], len(PAGE_CONNECTORS["overview"]))
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.SUCCESS)

    @patch("pipeline.utils.keywords.keywords_needing_backfill")
    def test_positioning_new_actually_applies_the_narrowing(self, mock_backfill):
        """The mirror half of the 2260104 bug: sync_page computed incremental_kws, logged
        'narrowing to N keyword(s)', then never assigned it -- so positions_new re-queried the
        entire tracked set against metered DataForSEO endpoints, which is the exact cost the
        scope exists to avoid."""
        mock_backfill.return_value = ["blue widgets", "red widgets"]
        self._stub_connectors()
        run = self._run_row(scope="positioning_new")

        sync_page("positioning_new", SITE_URL, run.pk)

        narrowed = sync_engine._INCREMENTAL_SCOPES["positioning_new"]
        for name in narrowed:
            self.assertEqual(
                getattr(self.built[name], "only_keywords", None),
                ["blue widgets", "red widgets"],
                f"{name} was not narrowed -- positions_new is paying for a full re-query",
            )
        # Connectors in the scope that are NOT metered per keyword stay un-narrowed.
        for name, conn in self.built.items():
            if name not in narrowed:
                self.assertFalse(hasattr(conn, "only_keywords"))

    @patch("pipeline.utils.keywords.keywords_needing_backfill")
    def test_positioning_new_short_circuits_when_nothing_needs_backfill(self, mock_backfill):
        """Empty backfill list must finish the run, NOT fall through to a full re-query."""
        mock_backfill.return_value = []
        self._stub_connectors()
        run = self._run_row(scope="positioning_new")

        summary = sync_page("positioning_new", SITE_URL, run.pk)

        self.assertEqual(self.built, {}, "no connector should have run")
        self.assertEqual(summary["records_written"], 0)
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.SUCCESS)

    def test_page_with_no_connectors_succeeds_immediately(self):
        self._stub_connectors()
        run = self._run_row(scope="nonexistent_page")

        summary = sync_page("nonexistent_page", SITE_URL, run.pk)

        self.assertEqual(summary, {"completed": 0, "total": 0, "records_written": 0, "errors": []})
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.SUCCESS)
        self.assertIsNotNone(run.finished_at)
