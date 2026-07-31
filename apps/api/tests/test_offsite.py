import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, SEODaily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class OffsiteEndpointTests(APITestCase):
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
            session.add(SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                  sessions=100, users=40, engagement_rate=0.5, conversions=8,
                                  landing_page="/a"))
            session.add(SEODaily(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                                  sessions=500, users=200, engagement_rate=0.9, conversions=50,
                                  landing_page="/b"))

        resp = self.client_auth.get("/api/projects/fusehealth/offsite")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        # current period reflects only the in-window row, not the previous-period row's bleed
        self.assertEqual(body["totals"]["sessions"], 100)
        self.assertEqual(body["totals"]["users"], 40)
        self.assertEqual(body["totals"]["keyEvents"], 8)

        # previous period reflects only its own row
        self.assertEqual(body["prev"]["sessions"], 500)
        self.assertEqual(body["prev"]["users"], 200)

        self.assertEqual(len(body["trend"]), 1)
        self.assertEqual(body["trend"][0]["date"], "2026-07-01")
        self.assertEqual(body["trend"][0]["sessions"], 100)

        self.assertEqual(len(body["landingPages"]), 1)
        self.assertEqual(body["landingPages"][0]["url"], "/a")

        # honest setup/empty fields, unaffected by seeded data
        self.assertEqual(body["channels"], [])
        self.assertEqual(body["referrers"], [])
        # `social` is a fixed four-platform roster, not an empty list — see the fuller
        # explanation in test_offsite_service.test_unbuilt_fields_report_setup_not_fake_data.
        # The invariant that matters here: platform impressions are never invented.
        self.assertEqual([r["platform"] for r in body["social"]],
                         ["LinkedIn", "Reddit", "YouTube", "X / Twitter"])
        for row in body["social"]:
            self.assertIsNone(row["impressions"])
            self.assertEqual(row["sessions"], 0)
        self.assertEqual(body["connectors"], {
            "linkedin": False, "reddit": False, "youtube": False,
            "x": False, "facebook": False, "instagram": False,
        })
        # syncMeta carries the real `ga4` SyncLog row; nothing has synced here, so the banner
        # gets None + "never" rather than an invented date (api-reference.md §offsite).
        self.assertEqual(body["syncMeta"]["state"], "ready")
        self.assertIsNone(body["syncMeta"]["lastUpdated"])
        self.assertEqual(body["syncMeta"]["lastStatus"], "never")

    def test_range_7d_shifts_window_and_excludes_older_row(self):
        # anchor = 2026-07-10. 7d window: curr = [2026-07-03, 2026-07-09].
        with get_session() as session:
            session.add(SEODaily(date=date(2026, 7, 10), site_id="sc-domain:fusehealth.com",
                                  sessions=1, users=1, engagement_rate=0.1, conversions=0,
                                  landing_page="/anchor"))
            # inside the 7d window
            session.add(SEODaily(date=date(2026, 7, 5), site_id="sc-domain:fusehealth.com",
                                  sessions=50, users=20, engagement_rate=0.5, conversions=3,
                                  landing_page="/in-window"))
            # outside the 7d window (would be inside 30d/90d), must be excluded
            session.add(SEODaily(date=date(2026, 6, 25), site_id="sc-domain:fusehealth.com",
                                  sessions=999, users=999, engagement_rate=0.9, conversions=99,
                                  landing_page="/out-of-window"))

        resp = self.client_auth.get("/api/projects/fusehealth/offsite", {"range": "7d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["totals"]["sessions"], 50)
        self.assertEqual(body["totals"]["users"], 20)

    def test_range_90d_shifts_window_and_excludes_older_row(self):
        # anchor = 2026-07-10. 90d window: curr = [2026-04-11, 2026-07-09].
        with get_session() as session:
            session.add(SEODaily(date=date(2026, 7, 10), site_id="sc-domain:fusehealth.com",
                                  sessions=1, users=1, engagement_rate=0.1, conversions=0,
                                  landing_page="/anchor"))
            # inside the 90d window
            session.add(SEODaily(date=date(2026, 5, 1), site_id="sc-domain:fusehealth.com",
                                  sessions=70, users=30, engagement_rate=0.4, conversions=5,
                                  landing_page="/in-window"))
            # well outside the 90d window, must be excluded
            session.add(SEODaily(date=date(2026, 1, 1), site_id="sc-domain:fusehealth.com",
                                  sessions=999, users=999, engagement_rate=0.9, conversions=99,
                                  landing_page="/out-of-window"))

        resp = self.client_auth.get("/api/projects/fusehealth/offsite", {"range": "90d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["totals"]["sessions"], 70)
        self.assertEqual(body["totals"]["users"], 30)

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/offsite")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/offsite")
        self.assertEqual(resp.status_code, 401)
