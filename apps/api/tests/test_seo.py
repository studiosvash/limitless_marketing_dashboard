import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, SEODaily, Anomaly, TechnicalIssue
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class SeoEndpointTests(APITestCase):
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
            session.add(SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                  clicks=5, impressions=800, ctr=0.006, avg_position=8.2,
                                  landing_page="https://fusehealth.com/low-ctr-page",
                                  country="United States", device="mobile"))
            session.add(TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                                        issue_type="not_found_404", severity="high"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_seo_returns_all_required_keys_with_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/seo")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "lowCtrPages", "countries", "anomalies", "quickWinKws"]:
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["critical"], 1)

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/seo")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/seo")
        self.assertEqual(resp.status_code, 401)
