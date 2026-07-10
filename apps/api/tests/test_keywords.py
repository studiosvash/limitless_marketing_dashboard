import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, KeywordRanking
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class KeywordsEndpointTests(APITestCase):
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
            session.add(KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                        keyword="iv therapy near me", position=6, clicks=12,
                                        impressions=200, search_volume=2400,
                                        keyword_difficulty=24, cpc=4.2, intent="commercial",
                                        url="/services/iv-therapy"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_keywords_returns_all_required_keys_with_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/keywords")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "intents", "difficulty", "segments", "keywords"]:
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["total"], 1)
        self.assertEqual(body["keywords"][0]["kw"], "iv therapy near me")

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/keywords")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/keywords")
        self.assertEqual(resp.status_code, 401)
