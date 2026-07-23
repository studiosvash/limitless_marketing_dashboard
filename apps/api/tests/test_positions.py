import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, KeywordRanking, SavedKeyword
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class PositionsEndpointTests(APITestCase):
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
            session.add(SavedKeyword(site_id="sc-domain:fusehealth.com", keyword="iv therapy"))
            session.add(KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                        keyword="iv therapy", position=2, clicks=40,
                                        impressions=500, search_volume=3000, intent="commercial",
                                        url="/iv-therapy"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_positions_returns_all_required_keys_with_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/positions", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "distribution", "movement", "competitors", "movers", "rankings", "keywords"]:
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["tracked"], 1)
        self.assertEqual(body["rankings"][0]["kw"], "iv therapy")

    def test_range_defaults_to_30d(self):
        resp = self.client_auth.get("/api/projects/fusehealth/positions")
        self.assertEqual(resp.status_code, 200)

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/positions")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/positions")
        self.assertEqual(resp.status_code, 401)
