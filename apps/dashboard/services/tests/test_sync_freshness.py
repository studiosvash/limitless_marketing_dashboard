"""The "already fetched recently" prompt on manual refreshes, and the cancel HTTP contract.

Until now a manual refresh checked exactly one thing -- "is a run already going for this
site" -- and never asked whether the data was already fresh, so re-clicking a refresh button
re-spent metered DataForSEO credits on data that had not changed.

The scheduler is deliberately NOT subject to this: its per-module cadences
(scheduling.CADENCE_INTERVALS) already are its freshness logic.
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.dashboard.services.sync_api_service import (
    FRESH_WITHIN, scope_last_synced, start_sync_run, task_status,
)
from apps.sync import scheduling
from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus

SITE_URL = "sc-domain:fusehealth.com"


def _log(connector, minutes_ago, status=SyncStatus.SUCCESS, site=SITE_URL):
    return SyncLog.objects.create(
        connector=connector, site_url=site, status=status,
        last_synced=timezone.now() - timedelta(minutes=minutes_ago),
    )


class ScopeLastSyncedTests(TestCase):
    def test_the_window_is_24_hours(self):
        self.assertEqual(FRESH_WITHIN, timedelta(hours=24))

    def test_a_fully_fresh_scope_returns_its_oldest_timestamp(self):
        """Oldest, not newest: the answer means "every step is at least this fresh", which is
        what the prompt shows the user."""
        _log("gsc", minutes_ago=30)
        _log("ga4", minutes_ago=90)

        result = scope_last_synced(SITE_URL, ["gsc", "ga4"])

        self.assertIsNotNone(result)
        age_minutes = (timezone.now() - result).total_seconds() / 60
        self.assertAlmostEqual(age_minutes, 90, delta=1)

    def test_one_stale_connector_makes_the_whole_scope_stale(self):
        _log("gsc", minutes_ago=30)
        _log("ga4", minutes_ago=60 * 40)
        self.assertIsNone(scope_last_synced(SITE_URL, ["gsc", "ga4"]))

    def test_a_recent_error_is_never_fresh(self):
        """The most important row here. Clicking Refresh right after fixing a credential is
        the whole reason the button exists -- skipping it because the FAILURE was recent
        would make the fix impossible to verify."""
        _log("gsc", minutes_ago=30)
        _log("ga4", minutes_ago=5, status=SyncStatus.ERROR)
        self.assertIsNone(scope_last_synced(SITE_URL, ["gsc", "ga4"]))

    def test_a_connector_that_never_ran_is_never_fresh(self):
        _log("gsc", minutes_ago=30)
        self.assertIsNone(scope_last_synced(SITE_URL, ["gsc", "ga4"]))

    def test_another_sites_rows_do_not_count(self):
        _log("gsc", minutes_ago=5, site="sc-domain:premierstaff.com")
        self.assertIsNone(scope_last_synced(SITE_URL, ["gsc"]))

    def test_an_empty_scope_is_never_fresh(self):
        self.assertIsNone(scope_last_synced(SITE_URL, []))


class StartSyncRunFreshnessTests(TestCase):
    def setUp(self):
        p = mock.patch("apps.dashboard.services.sync_api_service._spawn_sync_process",
                       return_value=4321)
        p.start()
        self.addCleanup(p.stop)

    def test_a_fresh_scope_creates_no_run_and_reports_when(self):
        """The point of the guard: no RefreshRun, no process, no API call -- just the facts
        the SPA needs to ask the user."""
        _log("dataforseo_backlinks", minutes_ago=40)

        result = start_sync_run(SITE_URL, "backlinks")

        self.assertTrue(result["fresh"])
        self.assertIn("last_synced", result)
        self.assertNotIn("task_id", result)
        self.assertEqual(RefreshRun.objects.count(), 0)

    def test_a_stale_scope_runs_normally(self):
        _log("dataforseo_backlinks", minutes_ago=60 * 40)
        result = start_sync_run(SITE_URL, "backlinks")
        self.assertNotIn("fresh", result)
        self.assertIn("task_id", result)

    def test_force_ignores_the_window(self):
        _log("dataforseo_backlinks", minutes_ago=1)
        result = start_sync_run(SITE_URL, "backlinks", force=True)
        self.assertNotIn("fresh", result)
        self.assertIn("task_id", result)

    def test_a_brand_new_site_always_runs(self):
        """No SyncLog rows means nothing is fresh, so the initial sync auto-started by
        POST /api/projects runs in full."""
        result = start_sync_run(SITE_URL, "all")
        self.assertIn("task_id", result)

    def test_refresh_all_is_subject_to_the_window(self):
        """The most expensive manual run there is; exempting it would defeat the feature."""
        from pipeline.services.sync_engine import ALL_CONNECTORS
        for connector in ALL_CONNECTORS:
            _log(connector, minutes_ago=10)

        result = start_sync_run(SITE_URL, "all")

        self.assertTrue(result["fresh"])

    def test_a_scheduled_run_ignores_the_window(self):
        """The cadences ARE the scheduler's freshness logic; stacking a 24h window on a 12h
        `ads` cadence would mean Ads silently never runs again."""
        _log("dataforseo_backlinks", minutes_ago=5)

        result = start_sync_run(SITE_URL, "backlinks", manual=False)

        self.assertNotIn("fresh", result)

    def test_a_scheduled_run_always_returns_a_task_id(self):
        """run_scheduled_syncs._start reads info['task_id'] on the very next line. The fresh
        shape has no such key, so reaching it from the scheduler is a crash."""
        _log("dataforseo_backlinks", minutes_ago=1)
        result = start_sync_run(SITE_URL, "backlinks", manual=False)
        self.assertIn("task_id", result)

    def test_an_already_running_sync_wins_over_freshness(self):
        """Attaching to the live run is what the user wanted; reporting "already fresh" would
        hide a run they are waiting on."""
        RefreshRun.objects.create(site_url=SITE_URL, scope="backlinks",
                                  status=RefreshStatus.RUNNING, pid=999)
        _log("dataforseo_backlinks", minutes_ago=5)

        result = start_sync_run(SITE_URL, "backlinks")

        self.assertTrue(result.get("already_running"))
        self.assertNotIn("fresh", result)


class SiblingProjectRunTests(TestCase):
    """Several projects share one domain (`add_site(allow_duplicate=True)` — e.g. eighteen
    premierstaff.com city projects). A RUNNING run belongs to ONE of them, and another
    project's fetch must not silently attach to it: attaching shows the sibling's progress
    bar as this project's and fetches nothing for this project's location, which is exactly
    how brand-new city projects stayed permanently blank on the live server."""

    def setUp(self):
        p = mock.patch("apps.dashboard.services.sync_api_service._spawn_sync_process",
                       return_value=4321)
        p.start()
        self.addCleanup(p.stop)

    def test_a_sibling_projects_run_is_reported_not_attached_to(self):
        existing = RefreshRun.objects.create(site_url=SITE_URL, site_pk=11, scope="positions",
                                             status=RefreshStatus.RUNNING, pid=999)

        result = start_sync_run(SITE_URL, "positions", site_pk=22)

        self.assertTrue(result.get("sibling_running"))
        self.assertNotIn("already_running", result, "a sibling's run is not this project's run")
        self.assertEqual(result["task_id"], existing.pk,
                         "the SPA still needs the live run's id, to watch for the free slot")
        self.assertEqual(result["scope"], "positions")
        self.assertIn("project", result)
        self.assertEqual(RefreshRun.objects.count(), 1, "no second run may start")

    def test_a_domain_wide_run_is_a_sibling_to_a_specific_project(self):
        """A run with no site_pk (the scheduler's) did not fetch THIS project's location
        either, so a project-specific fetch must queue behind it, not vanish into it."""
        RefreshRun.objects.create(site_url=SITE_URL, site_pk=None, scope="all",
                                  status=RefreshStatus.RUNNING, pid=999)
        result = start_sync_run(SITE_URL, "positions", site_pk=22)
        self.assertTrue(result.get("sibling_running"))

    def test_the_same_projects_run_is_attached_to(self):
        RefreshRun.objects.create(site_url=SITE_URL, site_pk=22, scope="positions",
                                  status=RefreshStatus.RUNNING, pid=999)
        result = start_sync_run(SITE_URL, "positions", site_pk=22)
        self.assertTrue(result.get("already_running"))
        self.assertNotIn("sibling_running", result)

    def test_a_caller_with_no_project_attaches_as_before(self):
        """The scheduler passes no site_pk and reads info['task_id'] on the next line —
        the per-domain attach semantics it was written against must not change."""
        RefreshRun.objects.create(site_url=SITE_URL, site_pk=11, scope="backlinks",
                                  status=RefreshStatus.RUNNING, pid=999)
        result = start_sync_run(SITE_URL, "backlinks", manual=False)
        self.assertTrue(result.get("already_running"))
        self.assertIn("task_id", result)


class PerProjectFreshnessTests(TestCase):
    """SyncLog is keyed (connector, site_url) — domain-level. One sibling's positioning sync
    used to make every other city project on the domain read as "fresh" for 24 hours, so
    their first fetch was answered with the already-fetched prompt instead of a run, and a
    user who did not press "Refetch anyway" got a permanently blank Positioning page."""

    def setUp(self):
        p = mock.patch("apps.dashboard.services.sync_api_service._spawn_sync_process",
                       return_value=4321)
        p.start()
        self.addCleanup(p.stop)

    def _domain_positioning_fresh(self):
        from pipeline.services.sync_engine import get_connector_names_for_page
        for connector in get_connector_names_for_page("positioning"):
            _log(connector, minutes_ago=40)

    def test_domain_fresh_but_project_never_fetched_runs_anyway(self):
        self._domain_positioning_fresh()
        result = start_sync_run(SITE_URL, "positions", site_pk=22)
        self.assertNotIn("fresh", result,
                         "a sibling's rows are for ITS location; this project has nothing yet")
        self.assertIn("task_id", result)

    def test_a_projects_own_recent_run_is_fresh(self):
        self._domain_positioning_fresh()
        RefreshRun.objects.create(site_url=SITE_URL, site_pk=22, scope="positions",
                                  status=RefreshStatus.SUCCESS,
                                  finished_at=timezone.now() - timedelta(hours=1))
        result = start_sync_run(SITE_URL, "positions", site_pk=22)
        self.assertTrue(result.get("fresh"))
        self.assertNotIn("task_id", result)

    def test_a_projects_own_all_run_covers_positions(self):
        """A scope='all' run includes every positioning connector, so it counts."""
        self._domain_positioning_fresh()
        RefreshRun.objects.create(site_url=SITE_URL, site_pk=22, scope="all",
                                  status=RefreshStatus.SUCCESS,
                                  finished_at=timezone.now() - timedelta(hours=1))
        result = start_sync_run(SITE_URL, "positions", site_pk=22)
        self.assertTrue(result.get("fresh"))

    def test_a_projects_old_run_is_not_fresh(self):
        self._domain_positioning_fresh()
        RefreshRun.objects.create(site_url=SITE_URL, site_pk=22, scope="positions",
                                  status=RefreshStatus.SUCCESS,
                                  finished_at=timezone.now() - FRESH_WITHIN - timedelta(hours=1))
        result = start_sync_run(SITE_URL, "positions", site_pk=22)
        self.assertNotIn("fresh", result)

    def test_domain_level_scopes_keep_domain_freshness(self):
        """Backlinks are per-domain — one domain's links are the same answer for every city
        project — so a sibling's fetch genuinely covers this one."""
        _log("dataforseo_backlinks", minutes_ago=40)
        result = start_sync_run(SITE_URL, "backlinks", site_pk=22)
        self.assertTrue(result.get("fresh"))


class TaskStatusProjectNameTests(TestCase):
    """The progress payload must say WHICH PROJECT the run belongs to. The banner used to
    print only the domain ('Syncing Positions for premierstaff.com'), which with eighteen
    projects on one domain hid whose fetch was actually running."""

    def setUp(self):
        import tempfile
        from pathlib import Path

        from django.test import override_settings

        from pipeline.db.schema import Site, init_db
        from pipeline.utils import db_connection
        from pipeline.utils.db_connection import get_engine, get_session

        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            site = Site(site_url="premierstaff.com", site_name="PS/ES - Chicago",
                        slug="ps-3", is_active=1)
            session.add(site)
            session.flush()
            self.site_pk = site.id

    def test_the_payload_names_the_owning_project(self):
        run = RefreshRun.objects.create(site_url="premierstaff.com", site_pk=self.site_pk,
                                        scope="positions", status=RefreshStatus.RUNNING)
        status = task_status(run.pk)
        self.assertEqual(status["project"], "PS/ES - Chicago")
        self.assertEqual(status["site_pk"], self.site_pk)
        self.assertEqual(status["site_url"], "premierstaff.com")

    def test_a_run_with_no_project_reports_none(self):
        run = RefreshRun.objects.create(site_url="premierstaff.com", site_pk=None,
                                        scope="all", status=RefreshStatus.RUNNING)
        status = task_status(run.pk)
        self.assertIsNone(status["project"])


class TaskStatusCancelledTests(TestCase):
    def test_a_cancelled_run_reports_done_without_an_error(self):
        run = RefreshRun.objects.create(site_url=SITE_URL, scope="audit",
                                        status=RefreshStatus.CANCELLED,
                                        total_count=5, completed_count=2)
        status = task_status(run.pk)

        self.assertTrue(status["done"])
        self.assertEqual(status["status"], RefreshStatus.CANCELLED)
        self.assertIn("Cancelled", status["step"])
        self.assertIsNone(status["error"], "a cancel is not a failure")


class SyncCancelApiTests(TestCase):
    """HTTP contract for Stop. `resolve_project_or_404` is patched because projects live in
    the SQLAlchemy analytics DB, not the Django ORM -- seeding one here would test that
    lookup rather than the cancel endpoint."""

    def setUp(self):
        user = get_user_model().objects.create_user("tester", password="pw12345678")
        token = Token.objects.get_or_create(user=user)[0]
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        self.url = "/api/projects/fusehealth/sync/cancel"

        p = mock.patch("apps.api.views.resolve_project_or_404",
                       return_value=mock.Mock(site_url=SITE_URL))
        p.start()
        self.addCleanup(p.stop)

    def test_cancelling_a_running_refresh(self):
        run = RefreshRun.objects.create(site_url=SITE_URL, scope="audit",
                                        status=RefreshStatus.RUNNING, pid=4321)
        with mock.patch.object(scheduling, "terminate_sync_process", return_value=True):
            response = self.client_auth.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["cancelled"])
        self.assertEqual(response.json()["task_id"], run.pk)
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.CANCELLED)

    def test_nothing_running_is_200_not_an_error(self):
        """The run may have finished while the user was reaching for the button. That is a
        race, not a client mistake, and a 4xx would show a failure toast for a non-failure."""
        response = self.client_auth.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["cancelled"])
        self.assertIn("reason", response.json())

    def test_token_auth_is_not_redirected_to_the_login_page(self):
        """Without login_not_required, LoginRequiredMiddleware runs before DRF and 302s the
        token request to /login/."""
        response = self.client_auth.post(self.url, {}, format="json")
        self.assertNotEqual(response.status_code, 302)
