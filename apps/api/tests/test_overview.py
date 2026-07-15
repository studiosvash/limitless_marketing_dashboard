import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

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

    def test_alerts_endpoint_returns_feed(self):
        # The SPA fetches this on every boot for the sidebar badge; without it the whole
        # app (including Overview) fails to render. It must return {feed: [...]}.
        resp = self.client_auth.get("/api/projects/fusehealth/alerts")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("feed", body)
        self.assertIsInstance(body["feed"], list)
        # We seeded one anomaly + one technical issue -> both surface here.
        kinds = {a["kind"] for a in body["feed"]}
        self.assertIn("anomaly", kinds)
        self.assertIn("technical", kinds)
        for a in body["feed"]:
            for field in ("id", "severity", "kind", "title", "detail", "ts", "acknowledged"):
                self.assertIn(field, a)

    def test_alerts_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/alerts")
        self.assertEqual(resp.status_code, 404)

    def test_research_returns_rows_and_flags_tracked(self):
        # Seed one tracked keyword so the endpoint flags it.
        from pipeline.db.schema import KeywordRanking
        with get_session() as session:
            session.add(KeywordRanking(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                       keyword="iv therapy", search_volume=100))

        fake = {
            "status": "ok", "location": "United States", "cost": 0.02, "error": None,
            "rows": [
                {"kw": "iv therapy", "volume": 8100, "kd": 42, "cpc": 3.99, "intent": "commercial",
                 "match": "exact", "monthly": [1, 2, 3], "serpFeatures": ["organic"]},
                {"kw": "mobile iv drip", "volume": 500, "kd": 20, "cpc": 1.10, "intent": "informational",
                 "match": "related", "monthly": [3, 2, 1], "serpFeatures": []},
            ],
        }
        with mock.patch(
            "pipeline.connectors.dataforseo_keywords.DataForSEOKeywordsConnector.expand_keywords",
            return_value=fake,
        ):
            resp = self.client_auth.post("/api/research", {
                "project": "fusehealth", "keywords": ["iv therapy"], "location": "United States",
            }, format="json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["location"], "United States")
        self.assertEqual(body["cost"], 0.02)
        by_kw = {r["kw"]: r for r in body["rows"]}
        self.assertTrue(by_kw["iv therapy"]["tracked"])
        self.assertFalse(by_kw["mobile iv drip"]["tracked"])

    def test_research_empty_seeds_is_400(self):
        resp = self.client_auth.post("/api/research", {"project": "fusehealth", "keywords": []},
                                     format="json")
        self.assertEqual(resp.status_code, 400)
