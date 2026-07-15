import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, SEODaily, AdMetricDaily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class AdsEndpointTests(APITestCase):
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

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_real_data_default_range_reflects_current_period_only(self):
        # anchor = max(SEODaily.date) = 2026-07-10 (filler row, excluded from every period
        # since periods anchor to "yesterday" relative to the latest data date).
        # Default 30d window: curr = [2026-06-10, 2026-07-09], prev = [2026-05-11, 2026-06-09].
        with get_session() as session:
            session.add(SEODaily(date=date(2026, 7, 10), site_id="sc-domain:fusehealth.com",
                                  sessions=1, users=1, engagement_rate=0.1, conversions=0,
                                  landing_page="/anchor"))
            # current-period AdMetricDaily row
            session.add(AdMetricDaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                       platform="google", campaign="curr-campaign",
                                       spend=100.0, clicks=20, impressions=1000,
                                       conversions=5, roas=2.0))
            # previous-period AdMetricDaily row — must not bleed into totals
            session.add(AdMetricDaily(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                                       platform="google", campaign="prev-campaign",
                                       spend=200.0, clicks=40, impressions=2000,
                                       conversions=10, roas=3.0))

        resp = self.client_auth.get("/api/projects/fusehealth/ads")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        # current period reflects only the in-window row, not the previous-period row's bleed
        self.assertEqual(body["totals"]["spend"], 100.0)
        self.assertEqual(body["totals"]["clicks"], 20.0)
        self.assertEqual(body["totals"]["impressions"], 1000.0)
        self.assertEqual(body["totals"]["conversions"], 5.0)
        self.assertEqual(body["totals"]["cpc"], 5.0)
        self.assertEqual(body["totals"]["roas"], 2.0)

        # previous period reflects only its own row
        self.assertEqual(body["prev"]["spend"], 200.0)
        self.assertEqual(body["prev"]["clicks"], 40.0)
        self.assertEqual(body["prev"]["impressions"], 2000.0)
        self.assertEqual(body["prev"]["conversions"], 10.0)
        self.assertEqual(body["prev"]["roas"], 3.0)

        self.assertEqual(len(body["trend"]), 1)
        self.assertEqual(body["trend"][0]["date"], "2026-07-01")
        self.assertEqual(body["trend"][0]["spend"], 100.0)

        # honest-empty fields, unaffected by seeded data (no backing schema/connector)
        self.assertEqual(body["campaigns"], [])
        self.assertEqual(body["searchTerms"], [])
        self.assertEqual(body["attribution"], [])
        self.assertEqual(body["landingPages"], [])
        self.assertEqual(body["negatives"], [])

    def test_range_7d_shifts_window_and_excludes_older_row(self):
        # anchor = 2026-07-10. 7d window: curr = [2026-07-03, 2026-07-09].
        with get_session() as session:
            session.add(SEODaily(date=date(2026, 7, 10), site_id="sc-domain:fusehealth.com",
                                  sessions=1, users=1, engagement_rate=0.1, conversions=0,
                                  landing_page="/anchor"))
            # inside the 7d window
            session.add(AdMetricDaily(date=date(2026, 7, 5), site_id="sc-domain:fusehealth.com",
                                       platform="google", campaign="in-window",
                                       spend=50.0, clicks=10, impressions=500,
                                       conversions=2, roas=1.5))
            # outside the 7d window (would be inside 30d/90d), must be excluded
            session.add(AdMetricDaily(date=date(2026, 6, 25), site_id="sc-domain:fusehealth.com",
                                       platform="google", campaign="out-of-window",
                                       spend=999.0, clicks=999, impressions=99999,
                                       conversions=99, roas=9.0))

        resp = self.client_auth.get("/api/projects/fusehealth/ads", {"range": "7d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["totals"]["spend"], 50.0)
        self.assertEqual(body["totals"]["clicks"], 10.0)

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/ads")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/ads")
        self.assertEqual(resp.status_code, 401)
