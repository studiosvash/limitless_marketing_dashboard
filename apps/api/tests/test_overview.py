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


class OverviewEndpointTests(APITestCase):
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
            # 06-30 is inside the current 30d window; 07-01 (the max/anchor date) is excluded
            # by design (range_to_period_dates treats the anchor as "today").
            session.add(SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                 clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                                 landing_page="https://fusehealth.com/a"))
            session.add(SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                 clicks=999, impressions=9999, ctr=0.50, avg_position=1.0,
                                 landing_page="https://fusehealth.com/a"))
            # Cross-module alert sources: one SEO anomaly + one Site Audit technical issue.
            session.add(Anomaly(site_id="sc-domain:fusehealth.com", date=date(2026, 6, 30),
                                metric_type="seo_clicks", severity="high", actual_value=100,
                                baseline_value=300, deviation_pct=-66, is_acknowledged=0))
            session.add(TechnicalIssue(site_id="sc-domain:fusehealth.com",
                                       url="https://fusehealth.com/gone", issue_type="not_found_404",
                                       severity="medium", description="Page returns 404."))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_overview_returns_all_required_top_level_keys(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "pillars", "modules", "priority", "signals", "trend", "summary", "topPages"]:
            self.assertIn(key, body, f"missing top-level key: {key}")

    def test_kpis_use_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        kpis = resp.json()["kpis"]
        clicks_kpi = next(k for k in kpis if k["label"] == "Total clicks")
        self.assertEqual(clicks_kpi["value"], 100)

    def test_site_health_pillar_is_real_when_page_data_exists(self):
        # E1: Site health is no longer hardcoded 'setup' -- we have GSC page data, so it
        # reports a real score. (Paid ROAS / AI visibility remain 'setup' -- genuinely
        # not connected.)
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        pillars = resp.json()["pillars"]
        site_health = next(p for p in pillars if p["label"] == "Site health")
        self.assertEqual(site_health["state"], "ok")
        self.assertIsInstance(site_health["value"], int)

        paid = next(p for p in pillars if p["label"] == "Paid ROAS")
        self.assertEqual(paid["state"], "setup")
        self.assertIsNone(paid["value"])

    def test_priority_feed_spans_multiple_modules(self):
        # E2: the Intelligence feed aggregates alerts across modules, not just Site Audit.
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        priority = resp.json()["priority"]
        self.assertGreaterEqual(len(priority), 2)
        module_labels = {p["module"]["label"] for p in priority}
        self.assertIn("SEO", module_labels)
        self.assertIn("Site Audit", module_labels)
        # High-severity SEO anomaly must sort to the top.
        self.assertEqual(priority[0]["severity"], "high")

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/overview")
        self.assertEqual(resp.status_code, 404)

    def test_range_defaults_to_30d(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview")
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/overview")
        self.assertEqual(resp.status_code, 401)
