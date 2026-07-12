import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, Backlink
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class BacklinksEndpointTests(APITestCase):
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
            session.add(Backlink(site_id="sc-domain:fusehealth.com", referring_domain="healthline.com",
                                  target_url="https://fusehealth.com/iv-therapy", anchor="iv therapy",
                                  status="live", dofollow=1, domain_rank=88))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_backlinks_returns_real_data_and_setup_states(self):
        resp = self.client_auth.get("/api/projects/fusehealth/backlinks")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["kpis"]["total"], 1)
        self.assertEqual(body["summary"], {"state": "setup"})

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/backlinks")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/backlinks")
        self.assertEqual(resp.status_code, 401)
