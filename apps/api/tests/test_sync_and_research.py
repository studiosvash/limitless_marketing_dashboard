"""Tests for the Refresh/Sync + Keyword/Prompt Explorer endpoints (the features the new SPA
called but which had no backend: POST /sync, GET /tasks/<id>, POST /research,
POST /prompt-research, POST /projects/<slug>/keywords)."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

from apps.sync.models import RefreshRun, RefreshStatus

SITE_URL = "sc-domain:fusehealth.com"


def _bootstrap(test_case):
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)

    with get_session() as session:
        session.add(Site(site_url=SITE_URL, site_name="FuseHealth", slug="fusehealth", is_active=1))

    user = get_user_model().objects.create_user("founder_sr", password="x")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {Token.objects.get(user=user).key}")
    return client


class SyncEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)

    @patch("apps.dashboard.services.sync_api_service.threading.Thread")
    def test_sync_creates_run_and_returns_task_contract(self, mock_thread):
        """POST /sync must return exactly what the SPA's startSync reads: task_id/steps/est_cost."""
        resp = self.client_auth.post(
            "/api/projects/fusehealth/sync", {"scope": "overview"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("task_id", body)
        self.assertIn("est_cost", body)
        # overview syncs the real gsc + ga4 connectors
        self.assertEqual(body["steps"], ["gsc", "ga4"])

        run = RefreshRun.objects.get(pk=body["task_id"])
        self.assertEqual(run.site_url, SITE_URL)
        self.assertEqual(run.total_count, 2)
        mock_thread.assert_called_once()  # background sync actually kicked off

    @patch("apps.dashboard.services.sync_api_service.threading.Thread")
    def test_scope_alias_positions_maps_to_positioning(self, _mock_thread):
        resp = self.client_auth.post(
            "/api/projects/fusehealth/sync", {"scope": "positions"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json()["steps"], ["gsc_keywords", "dataforseo_serp_competitors"]
        )

    @patch("apps.dashboard.services.sync_api_service.threading.Thread")
    def test_backlinks_scope_is_no_longer_a_silent_noop(self, _mock_thread):
        """Regression: backlinks/ads had EMPTY connector lists, so Refresh did nothing."""
        resp = self.client_auth.post(
            "/api/projects/fusehealth/sync", {"scope": "backlinks"}, format="json"
        )
        self.assertEqual(resp.json()["steps"], ["dataforseo_backlinks"])

        resp = self.client_auth.post(
            "/api/projects/fusehealth/sync", {"scope": "ads"}, format="json"
        )
        self.assertEqual(resp.json()["steps"], ["google_ads", "ga4"])

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.post("/api/projects/nope/sync", {"scope": "all"}, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().post("/api/projects/fusehealth/sync", {"scope": "all"}, format="json")
        self.assertEqual(resp.status_code, 401)


class TaskStatusEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)

    def test_running_then_done_progress_contract(self):
        """GET /tasks/<id> must return what the SPA's poll loop reads: done/progress/step."""
        run = RefreshRun.objects.create(
            site_url=SITE_URL, scope="overview", status=RefreshStatus.RUNNING,
            total_count=4, completed_count=1, current_connector="gsc",
        )
        body = self.client_auth.get(f"/api/tasks/{run.pk}").json()
        self.assertFalse(body["done"])
        self.assertAlmostEqual(body["progress"], 0.25)
        self.assertIn("gsc", body["step"])

        run.status = RefreshStatus.SUCCESS
        run.completed_count = 4
        run.records_written = 7269
        run.save()

        body = self.client_auth.get(f"/api/tasks/{run.pk}").json()
        self.assertTrue(body["done"])
        self.assertEqual(body["progress"], 1.0)
        self.assertIn("7,269", body["step"])

    def test_failed_run_surfaces_error_in_step_and_error_field(self):
        """A refresh that completed with connector errors must SAY so — it used to dump the
        raw joined error string as the step (or the SPA just showed 'done'), leaving the
        user with a silent, blank page and no clue which connector failed."""
        from apps.sync.models import RefreshRun, RefreshStatus

        run = RefreshRun.objects.create(
            site_url="sc-domain:fusehealth.com", scope="all",
            status=RefreshStatus.ERROR, completed_count=7, total_count=7,
            error_message="gsc: <HttpError 403 ... insufficient permission>; ga4: quota",
        )
        body = self.client_auth.get(f"/api/tasks/{run.pk}").json()
        self.assertTrue(body["done"])
        self.assertTrue(body["step"].startswith("Completed with errors"))
        self.assertIn("gsc", body["step"])
        self.assertIn("insufficient permission", body["error"])

    def test_unknown_task_returns_done_true(self):
        # HANDOFF_SPEC 1: "unknown ids should return {done: true}" — the SPA polls every
        # 500ms and treats non-2xx as a hard error, so 404 would break the progress bar
        # for tasks that finished before a page reload.
        resp = self.client_auth.get("/api/tasks/999999")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["done"])


class KeywordResearchEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)

    @patch("pipeline.connectors.dataforseo_keywords.DataForSEOKeywordsConnector")
    def test_research_maps_connector_rows_to_spa_shape(self, mock_conn):
        mock_conn.return_value.lookup_keywords.return_value = {
            "status": "ok",
            "rows": [{
                "keyword": "iv therapy", "search_volume": 40500, "keyword_difficulty": 58,
                "cpc": 7.63, "intent": "Informational", "serp_features": "people_also_ask, video",
            }],
            "no_data": [], "location": "United States",
        }
        resp = self.client_auth.post(
            "/api/research",
            {"project": "fusehealth", "keywords": ["iv therapy"], "location": "United States"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        row = resp.json()["rows"][0]
        # exactly the keys the SPA's research table reads
        self.assertEqual(row["kw"], "iv therapy")
        self.assertEqual(row["volume"], 40500)
        self.assertEqual(row["kd"], 58)
        self.assertEqual(row["cpc"], 7.63)
        self.assertEqual(row["match"], "exact")
        self.assertEqual(row["serpFeatures"], ["people_also_ask", "video"])
        self.assertIs(row["tracked"], False)

    @patch("pipeline.connectors.dataforseo_keywords.DataForSEOKeywordsConnector")
    def test_connector_failure_is_honest_empty_not_a_500(self, mock_conn):
        mock_conn.return_value.lookup_keywords.side_effect = RuntimeError("no credentials")
        resp = self.client_auth.post(
            "/api/research", {"project": "fusehealth", "keywords": ["x"]}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["rows"], [])   # honest empty -- never fabricated rows
        self.assertIn("error", body)

    def test_empty_keywords_is_handled(self):
        body = self.client_auth.post(
            "/api/research", {"project": "fusehealth", "keywords": []}, format="json"
        ).json()
        self.assertEqual(body["rows"], [])

    def test_unauthenticated_is_401(self):
        resp = APIClient().post("/api/research", {"project": "fusehealth"}, format="json")
        self.assertEqual(resp.status_code, 401)


class PromptResearchEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)

    def test_seeds_expand_into_prompts_with_honest_zero_volume(self):
        body = self.client_auth.post(
            "/api/prompt-research", {"project": "fusehealth", "seeds": ["iv therapy"]},
            format="json",
        ).json()
        self.assertTrue(len(body["rows"]) > 0)
        row = body["rows"][0]
        self.assertIn("iv therapy", row["text"])
        self.assertEqual(row["aiVolume"], 0)   # honest: no AI-volume source exists yet
        self.assertIs(row["tracked"], False)
        self.assertIn("category", row)


class TrackKeywordEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)

    def test_post_keyword_saves_to_db(self):
        from pipeline.services.saved_keyword_service import list_saved_keywords

        resp = self.client_auth.post(
            "/api/projects/fusehealth/keywords",
            {"kw": "iv therapy", "volume": 40500, "kd": 58, "cpc": 7.63, "intent": "Informational"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["saved"], 1)

        saved = [r["keyword"] for r in list_saved_keywords(SITE_URL)]
        self.assertIn("iv therapy", saved)

    def test_missing_kw_is_400(self):
        resp = self.client_auth.post(
            "/api/projects/fusehealth/keywords", {"volume": 100}, format="json"
        )
        self.assertEqual(resp.status_code, 400)
