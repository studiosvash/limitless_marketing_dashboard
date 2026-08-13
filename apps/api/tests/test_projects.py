import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db
import pipeline.utils.db_connection as db_connection


def _auth_client(user) -> APIClient:
    token = Token.objects.get(user=user)  # created by the Task 2 signal
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


class ProjectsEndpointTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        self.db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(self.db_path))
        self._settings_ctx = override_settings(ANALYTICS_DB_PATH=self.db_path)
        self._settings_ctx.enable()
        self.addCleanup(self._settings_ctx.disable)

        self.user = get_user_model().objects.create_user("founder1", password="x")
        self.client_auth = _auth_client(self.user)

    def test_list_projects_empty(self):
        resp = self.client_auth.get("/api/projects")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_create_then_list_project(self):
        resp = self.client_auth.post("/api/projects", {"domain": "fusehealth.com", "name": "FuseHealth"}, format="json")
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["domain"], "fusehealth.com")
        self.assertEqual(body["name"], "FuseHealth")
        self.assertEqual(body["id"], "fusehealth")

        resp = self.client_auth.get("/api/projects")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        item = resp.json()[0]
        self.assertEqual(item["id"], "fusehealth")
        for key in ["tracked_keywords_count", "avg_position", "improved_count", "declined_count", "last_updated"]:
            self.assertIn(key, item)

    def test_updated_and_syncing_reflect_the_projects_own_runs(self):
        """The list's Updated column answers "when did I last FETCH this project", and
        `syncing` marks a run in flight — both keyed on RefreshRun.site_pk, because SyncLog
        and the measurement dates are domain-level and `dataforseo_serp` stamps its rows
        `yesterday()`, which made a fetch finished two minutes ago read "Yesterday"."""
        from datetime import timedelta

        from unittest import mock

        from django.utils import timezone

        from apps.sync.models import RefreshRun, RefreshStatus

        # The auto-started initial sync would itself be a RUNNING run (and a real spawned
        # process); these assertions are about runs this test creates deliberately.
        with mock.patch("apps.api.views.start_sync_run", return_value={"task_id": None}):
            resp = self.client_auth.post("/api/projects", {"domain": "premierstaff.com"},
                                         format="json")
        self.assertEqual(resp.status_code, 201)

        from pipeline.db.schema import Site
        from pipeline.utils.db_connection import get_session
        with get_session() as session:
            site_pk = session.query(Site.id).filter(Site.site_url == "premierstaff.com").scalar()

        RefreshRun.objects.create(site_url="premierstaff.com", site_pk=site_pk,
                                  scope="positions", status=RefreshStatus.SUCCESS,
                                  finished_at=timezone.now() - timedelta(minutes=5))
        item = self.client_auth.get("/api/projects").json()[0]
        self.assertEqual(item["last_updated"], "Today",
                         "a fetch that finished five minutes ago is not 'Yesterday'")
        self.assertFalse(item["syncing"])

        RefreshRun.objects.create(site_url="premierstaff.com", site_pk=site_pk,
                                  scope="positions", status=RefreshStatus.RUNNING)
        item = self.client_auth.get("/api/projects").json()[0]
        self.assertTrue(item["syncing"], "a run in flight must show on the project's row")

    def test_a_siblings_run_does_not_mark_this_project_updated_or_syncing(self):
        from datetime import timedelta
        from unittest import mock

        from django.utils import timezone

        from apps.sync.models import RefreshRun, RefreshStatus

        with mock.patch("apps.api.views.start_sync_run", return_value={"task_id": None}):
            self.client_auth.post("/api/projects", {"domain": "premierstaff.com"}, format="json")
        RefreshRun.objects.create(site_url="premierstaff.com", site_pk=999999,
                                  scope="positions", status=RefreshStatus.SUCCESS,
                                  finished_at=timezone.now() - timedelta(minutes=5))
        RefreshRun.objects.create(site_url="premierstaff.com", site_pk=999998,
                                  scope="positions", status=RefreshStatus.RUNNING)
        item = self.client_auth.get("/api/projects").json()[0]
        self.assertFalse(item["syncing"], "the running fetch belongs to a sibling project")
        self.assertEqual(item["last_updated"], "No sync yet",
                         "a sibling's fetch is not this project's update")

    def test_create_missing_domain_is_400(self):
        resp = self.client_auth.post("/api/projects", {"name": "No domain"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects")
        self.assertEqual(resp.status_code, 401)
