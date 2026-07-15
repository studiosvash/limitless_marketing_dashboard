import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, Anomaly
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class AlertsEndpointTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url="sc-domain:fusehealth.com", site_name="FuseHealth",
                              slug="fusehealth", is_active=1))
            session.add(Anomaly(date=date(2026, 6, 28), site_id="sc-domain:fusehealth.com",
                                 metric_type="seo_clicks", actual_value=50, baseline_value=100,
                                 deviation_pct=-50.0, severity="high",
                                 description="Clicks dropped 50%.", is_acknowledged=0))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_alerts_returns_real_feed(self):
        resp = self.client_auth.get("/api/projects/fusehealth/alerts")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("feed", body)
        self.assertEqual(len(body["feed"]), 1)
        self.assertEqual(body["feed"][0]["kind"], "anomaly")

    def test_failed_refresh_appears_as_system_alert(self):
        """When the latest refresh ended in error, the feed must lead with a kind=system
        alert naming the failed connector(s) — so the failure shows on the Overview
        priority feed instead of the page just staying blank."""
        from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus

        RefreshRun.objects.create(
            site_url="sc-domain:fusehealth.com", scope="all", status=RefreshStatus.ERROR,
            completed_count=7, total_count=7,
            error_message="gsc: <HttpError 403 insufficient permission>",
        )
        SyncLog.objects.create(
            connector="gsc", site_url="sc-domain:fusehealth.com", status=SyncStatus.ERROR,
            error_message="<HttpError 403 insufficient permission for site>",
        )

        feed = self.client_auth.get("/api/projects/fusehealth/alerts").json()["feed"]
        system = [f for f in feed if f["kind"] == "system"]
        self.assertEqual(len(system), 1)
        self.assertEqual(system[0]["severity"], "high")
        self.assertIn("gsc", system[0]["title"])
        self.assertIn("Settings", system[0]["detail"])

    def test_successful_latest_refresh_produces_no_system_alert(self):
        from apps.sync.models import RefreshRun, RefreshStatus

        RefreshRun.objects.create(
            site_url="sc-domain:fusehealth.com", scope="all", status=RefreshStatus.SUCCESS,
            completed_count=7, total_count=7,
        )
        feed = self.client_auth.get("/api/projects/fusehealth/alerts").json()["feed"]
        self.assertEqual([f for f in feed if f["kind"] == "system"], [])

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/alerts")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/alerts")
        self.assertEqual(resp.status_code, 401)
