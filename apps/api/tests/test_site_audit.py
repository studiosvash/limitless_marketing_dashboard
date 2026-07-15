import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, IndexingStatus, PageSpeed
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class SiteAuditEndpointTests(APITestCase):
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
            # Healthy indexing status: PASS verdict, no robots block, no redirects/404
            session.add(IndexingStatus(site_id="sc-domain:fusehealth.com",
                                        url="https://fusehealth.com/page1",
                                        verdict="PASS",
                                        coverage_state=None,
                                        robots_txt_state=None))
            # PageSpeed data with mobile strategy
            session.add(PageSpeed(site_id="sc-domain:fusehealth.com",
                                   url="https://fusehealth.com/page1",
                                   strategy="mobile",
                                   lcp_ms=2000.0,
                                   cls=0.08))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_site_audit_returns_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/audit")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # Check that breakdown reflects the seeded IndexingStatus
        self.assertEqual(body["breakdown"]["healthy"], 1)
        self.assertEqual(body["breakdown"]["withIssues"], 0)
        self.assertEqual(body["breakdown"]["broken"], 0)
        self.assertEqual(body["breakdown"]["redirected"], 0)
        self.assertEqual(body["breakdown"]["blocked"], 0)
        # Check that CWV metrics have real data (not setup state)
        self.assertIn("lcp", body["cwv"])
        self.assertIn("cls", body["cwv"])
        self.assertIsNotNone(body["cwv"]["lcp"]["p75"])
        self.assertIsNotNone(body["cwv"]["cls"]["p75"])
        # score/crawl are real derived values now (they used to be {"state": "setup"}, which
        # made the SPA hide the entire Site Audit page even when real data existed).
        self.assertIsInstance(body["score"], int)
        self.assertGreaterEqual(body["crawl"]["pagesCrawled"], 1)
        # things with genuinely no data source stay honestly empty
        self.assertEqual(body["domainChecks"], [])
        self.assertEqual(body["snapshots"], [])

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/audit")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/audit")
        self.assertEqual(resp.status_code, 401)
