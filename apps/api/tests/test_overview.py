import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, SEODaily, KeywordRanking, AISummary
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
            # Two rows, not one: range_to_period_dates("30d", anchor) treats `anchor` (the max
            # data date) as "today" and excludes it from the current window (yesterday =
            # anchor - 1 — pre-existing behavior in pipeline/utils/period_utils.py, not
            # introduced here). The 07-01 row is the max date and therefore intentionally
            # excluded; 06-30 is the one actually inside the current-period window.
            session.add(SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                  clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                                  landing_page="https://fusehealth.com/a"))
            session.add(SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                  clicks=999, impressions=9999, ctr=0.50, avg_position=1.0,
                                  landing_page="https://fusehealth.com/a"))

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
        # 100, not 100+999=1099 — the 07-01 row is the max date, excluded from the current
        # window by design (see the comment on the seeded rows in setUp above).
        self.assertEqual(clicks_kpi["value"], 100)

    def test_unbuilt_pillars_report_setup_state_not_fake_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        pillars = resp.json()["pillars"]
        site_health = next(p for p in pillars if p["label"] == "Site health")
        self.assertEqual(site_health["state"], "setup")
        self.assertIsNone(site_health["value"])

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/overview")
        self.assertEqual(resp.status_code, 404)

    def test_range_defaults_to_30d(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview")
        self.assertEqual(resp.status_code, 200)

    def test_pillars_modules_and_summary_reflect_seeded_keyword_and_ai_data(self):
        """Task 7's genuinely-new logic (build_pillars, build_modules, top3_count,
        build_summary_lists) only produces non-trivial output when KeywordRanking/AISummary
        rows exist — setUp() above seeds neither, so this test seeds its own and asserts
        real numeric/string output, not just key presence."""
        with get_session() as session:
            # position=2 (<=3, counts toward top3_count) and position=15 (does not).
            session.add(KeywordRanking(
                date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                keyword="buy protein powder", position=2, clicks=40, impressions=400,
                search_volume=1200,
            ))
            session.add(KeywordRanking(
                date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                keyword="health supplements guide", position=15, clicks=10, impressions=800,
                search_volume=500,
            ))
            session.add(AISummary(
                week_start=date(2026, 6, 29), site_id="sc-domain:fusehealth.com",
                summary_text=(
                    "## 🟢 Win: Great CTR growth\n"
                    "- CTR grew 20% this month\n"
                    "- Impressions increased significantly\n\n"
                    "## 🔴 Critical: Ranking drop\n"
                    "- Lost 5 positions on primary keyword\n"
                    "- Traffic decreased on key landing page\n"
                ),
            ))

        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        # Keywords module: 2 tracked (both seeded keywords), 1 in top 3 (position 2 only).
        keywords_module = next(m for m in body["modules"] if m["label"] == "Keywords")
        self.assertEqual(keywords_module["stat"], "2 tracked")
        self.assertEqual(keywords_module["sub"], "1 in top 3")

        # Avg. position pillar's `sub` reports the same top3_count.
        avg_pos_pillar = next(p for p in body["pillars"] if p["label"] == "Avg. position")
        self.assertEqual(avg_pos_pillar["sub"], "1 keywords in top 3")
        # 8.0 == the single SEODaily row's avg_position inside the current window (setUp).
        self.assertEqual(avg_pos_pillar["value"], 8.0)

        # Organic clicks pillar value is a real number matching setUp's SEODaily total.
        organic_clicks_pillar = next(p for p in body["pillars"] if p["label"] == "Organic clicks")
        self.assertEqual(organic_clicks_pillar["value"], 100)

        # AI summary wins/critical are populated with the actual seeded bullet text.
        summary = body["summary"]
        self.assertTrue(any("CTR grew 20% this month" in w for w in summary["wins"]))
        self.assertTrue(any("Impressions increased significantly" in w for w in summary["wins"]))
        self.assertTrue(any("Lost 5 positions on primary keyword" in c for c in summary["critical"]))
        self.assertTrue(any("Traffic decreased on key landing page" in c for c in summary["critical"]))


class ResolveProjectHelperTests(APITestCase):
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
            session.add(SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                  clicks=1, impressions=1, ctr=0.1, avg_position=1.0))

    def test_resolve_project_or_404_finds_real_site(self):
        from apps.api.views import resolve_project_or_404
        site = resolve_project_or_404("fusehealth")
        self.assertEqual(site.site_url, "sc-domain:fusehealth.com")

    def test_resolve_project_or_404_raises_on_unknown_slug(self):
        from django.http import Http404
        from apps.api.views import resolve_project_or_404
        with self.assertRaises(Http404):
            resolve_project_or_404("does-not-exist")

    def test_latest_data_anchor_finds_max_date(self):
        from apps.api.views import latest_data_anchor
        anchor = latest_data_anchor("sc-domain:fusehealth.com")
        self.assertEqual(anchor, date(2026, 7, 1))

    def test_latest_data_anchor_falls_back_to_today_when_no_data(self):
        from datetime import date as date_cls
        from apps.api.views import latest_data_anchor
        anchor = latest_data_anchor("sc-domain:no-data-site.com")
        self.assertEqual(anchor, date_cls.today())


class ResolveRangePeriodsTests(APITestCase):
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
            session.add(SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                  clicks=1, impressions=1, ctr=0.1, avg_position=1.0))

    def test_resolves_site_id_and_period_dates(self):
        from django.test import RequestFactory
        from rest_framework.request import Request
        from apps.api.views import resolve_range_periods

        django_request = RequestFactory().get("/api/projects/fusehealth/positions", {"range": "7d"})
        request = Request(django_request)
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, "fusehealth")
        self.assertEqual(site_id, "sc-domain:fusehealth.com")
        self.assertEqual((curr_end - curr_start).days, 6)

    def test_defaults_range_to_30d_when_absent(self):
        from django.test import RequestFactory
        from rest_framework.request import Request
        from apps.api.views import resolve_range_periods

        django_request = RequestFactory().get("/api/projects/fusehealth/positions")
        request = Request(django_request)
        _, curr_start, curr_end, _, _ = resolve_range_periods(request, "fusehealth")
        self.assertEqual((curr_end - curr_start).days, 29)

    def test_unknown_slug_raises_404(self):
        from django.http import Http404
        from django.test import RequestFactory
        from rest_framework.request import Request
        from apps.api.views import resolve_range_periods

        django_request = RequestFactory().get("/api/projects/does-not-exist/positions")
        request = Request(django_request)
        with self.assertRaises(Http404):
            resolve_range_periods(request, "does-not-exist")
