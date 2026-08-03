import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, SEODaily, KeywordRanking, AISummary, Anomaly
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

    def test_site_health_pillar_goes_live_with_audit_data(self):
        """Overview's Site health pillar/module must show the SAME score the Site Audit page
        computes (60% Lighthouse perf + 40% indexed share) — it used to stay hardcoded
        'setup' even when the audit page had real data."""
        from pipeline.db.schema import IndexingStatus, PageSpeed, TechnicalIssue
        from datetime import datetime

        with get_session() as session:
            # 1 indexed of 2 pages (50%) + avg mobile perf 80 -> round(0.6*80 + 0.4*50) = 68
            session.add(IndexingStatus(site_id="sc-domain:fusehealth.com",
                                       url="https://fusehealth.com/", verdict="PASS"))
            session.add(IndexingStatus(site_id="sc-domain:fusehealth.com",
                                       url="https://fusehealth.com/404",
                                       coverage_state="Not found (404)"))
            session.add(PageSpeed(site_id="sc-domain:fusehealth.com",
                                  url="https://fusehealth.com/", strategy="mobile",
                                  performance_score=80))
            session.add(TechnicalIssue(site_id="sc-domain:fusehealth.com",
                                       url="https://fusehealth.com/404",
                                       issue_type="not_found_404", severity="high",
                                       description="404", detected_at=datetime(2026, 7, 1)))

        body = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"}).json()

        pillar = next(p for p in body["pillars"] if p["label"] == "Site health")
        self.assertEqual(pillar["state"], "ok")
        self.assertEqual(pillar["value"], 68)
        self.assertEqual(pillar["sub"], "1 error to fix")

        audit_score = self.client_auth.get("/api/projects/fusehealth/audit").json()["score"]
        self.assertEqual(pillar["value"], audit_score)  # the two views must never disagree

        module = next(m for m in body["modules"] if m["label"] == "Site Audit")
        self.assertEqual(module["stat"], "68/100")
        self.assertEqual(module["tone"], "warn")

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

    def test_priority_reflects_real_unacknowledged_alerts(self):
        with get_session() as session:
            session.add(Anomaly(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                 metric_type="seo_clicks", actual_value=50, baseline_value=100,
                                 deviation_pct=-50.0, severity="high",
                                 description="Clicks dropped.", is_acknowledged=0))
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        body = resp.json()
        self.assertEqual(len(body["priority"]), 1)
        self.assertEqual(body["priority"][0]["module"]["target"], "seo")


class PositioningOverviewCoverageTests(APITestCase):
    """`positioningOverview` must never invent a competitor position.

    THE BUG THIS GUARDS AGAINST. `shared_queries._get_competitor_grid` used to synthesise a
    position for every (keyword, competitor) pair it had no captured row for: the
    competitor's site-wide average from `CompetitorDomain` (defaulting to 30.0, or a flat
    25.0 for a domain with no row at all) plus an MD5-derived offset of the keyword+domain
    string. It was deterministic, so it looked stable and therefore real, and nobody could
    tell it apart from captured data. It was removed — but an AGGREGATE is exactly where it
    could come back unnoticed: an average over a list that quietly skips its gaps produces a
    confident number describing a keyword set the reader never sees.

    So these assertions are written to fail if any form of it returns:
      * a competitor captured on 1 of 3 keywords must average over THAT ONE keyword only —
        if the other two were filled in (by a hash, a site-wide average, or a 0) the mean
        moves and `keywordsRanked` stops being 1;
      * a competitor with no captures at all must report `avgPosition is None` — not 0, not
        the site average, not a plausible number;
      * `state` must say `partial`/`none` so the UI can never read a partial average as
        like-for-like.

    Seeded shape (capture date 2026-06-30):
        tracked keywords : "iv therapy", "mobile iv drip", "vitamin drip"   (3)
        you              : positions 10, 20, 30                 -> avg 20.0, full coverage
        partial.com      : position 5 on "iv therapy" only      -> avg 5.0, 1 of 3
        absent.com       : tracked, never captured              -> avgPosition None, 0 of 3
    """

    CAPTURE_DATE = date(2026, 6, 30)
    SITE = "sc-domain:fusehealth.com"
    KEYWORDS = ["iv therapy", "mobile iv drip", "vitamin drip"]
    YOUR_POSITIONS = [10, 20, 30]

    def setUp(self):
        from pipeline.db.schema import (
            SavedKeyword, TrackedCompetitor, CompetitorKeywordRanking,
        )

        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url=self.SITE, site_name="FuseHealth",
                             slug="fusehealth", is_active=1))
            session.add(SEODaily(date=self.CAPTURE_DATE, site_id=self.SITE,
                                 clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                                 landing_page="https://fusehealth.com/a"))

            # The tracked list. _get_competitor_grid reads it via load_tracked_keywords,
            # which reads saved_keywords — seeding it here is what keeps this test from
            # falling back to the repo's optional keywords.txt.
            for kw in self.KEYWORDS:
                session.add(SavedKeyword(site_id=self.SITE, keyword=kw))

            # Your own captured positions: one per tracked keyword.
            for kw, pos in zip(self.KEYWORDS, self.YOUR_POSITIONS):
                session.add(KeywordRanking(date=self.CAPTURE_DATE, site_id=self.SITE,
                                           keyword=kw, position=pos, clicks=10,
                                           impressions=100))

            session.add(TrackedCompetitor(site_id=self.SITE, competitor_domain="partial.com"))
            session.add(TrackedCompetitor(site_id=self.SITE, competitor_domain="absent.com"))

            # partial.com appears in the captured SERP for ONE keyword only. absent.com gets
            # no row at all — "not in the captured top 30" is a fact, not a missing value.
            session.add(CompetitorKeywordRanking(
                date=self.CAPTURE_DATE, site_id=self.SITE, keyword=self.KEYWORDS[0],
                competitor_domain="partial.com", position=5,
            ))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def _overview(self) -> dict:
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        return resp.json()["positioningOverview"]

    def _row(self, po: dict, domain: str) -> dict:
        match = next((c for c in po["competitors"] if c["domain"] == domain), None)
        self.assertIsNotNone(match, f"{domain} missing from positioningOverview.competitors")
        return match

    def test_status_is_ok_with_captured_data(self):
        po = self._overview()
        self.assertEqual(po["status"], "ok")
        self.assertEqual(po["keywordsTotal"], 3)
        self.assertEqual(po["capturedAt"], str(self.CAPTURE_DATE))

    def test_partial_competitor_averages_only_its_captured_keyword(self):
        """1 of 3 keywords captured -> state 'partial' and the mean of that ONE position.

        5.0 is the position of the single captured row. Any fabricated stand-in for the two
        uncaptured keywords — an MD5 offset, the site-wide average, or a 0 — changes this
        number, so this assertion is what makes the fabrication impossible to reintroduce
        silently."""
        row = self._row(self._overview(), "partial.com")
        self.assertEqual(row["state"], "partial")
        self.assertEqual(row["keywordsRanked"], 1)
        self.assertEqual(row["keywordsTotal"], 3)
        self.assertEqual(row["avgPosition"], 5.0)

    def test_competitor_with_no_captures_has_no_average_at_all(self):
        """Zero captured positions -> `avgPosition` is None. Never 0, never a number.

        assertIsNone, not assertFalse: 0 is falsy and 0 is precisely the wrong answer here —
        "ranks at position 0" is not "we have never seen it rank"."""
        row = self._row(self._overview(), "absent.com")
        self.assertEqual(row["state"], "none")
        self.assertEqual(row["keywordsRanked"], 0)
        self.assertIsNone(row["avgPosition"])
        self.assertNotIsInstance(row["avgPosition"], (int, float))

    def test_uncaptured_competitors_are_not_counted_as_having_data(self):
        po = self._overview()
        self.assertEqual(po["competitorsWithData"], 1)   # partial.com only
        # ...and the domain with no data sorts last, so "no data" never leads the list.
        self.assertEqual(po["competitors"][-1]["domain"], "absent.com")

    def test_your_own_row_is_averaged_over_your_real_positions(self):
        po = self._overview()
        you = po["you"]
        self.assertEqual(you["state"], "ok")
        self.assertEqual(you["keywordsRanked"], 3)
        self.assertEqual(you["avgPosition"], 20.0)   # mean(10, 20, 30)
        # A competitor's average must not be your average with an offset — the shape the
        # removed MD5 fabrication produced.
        self.assertNotEqual(self._row(po, "partial.com")["avgPosition"], you["avgPosition"])


class TopKeywordsPrecisionTests(APITestCase):
    """`topKeywords` must carry raw numbers and preserve "we have no value" as null.

    `shared_queries._get_keywords_overview` used to format every value for the old Django
    template: position through `f"{avg:.0f}"`, counts through `f"{n:,.0f}"`, and the two
    null cases as the strings "N/A" and "—". That threw away the data before any consumer
    could see it (an 8.5 average arrived as "8") and made the columns sort as text.
    """

    SITE = "sc-domain:fusehealth.com"

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
            session.add(Site(site_url=self.SITE, site_name="FuseHealth",
                             slug="fusehealth", is_active=1))
            session.add(SEODaily(date=date(2026, 6, 30), site_id=self.SITE,
                                 clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                                 landing_page="https://fusehealth.com/a"))

            # Two days at positions 8 and 9 -> avg 8.5. The old formatter rendered this as
            # "8" and the decimal could not be recovered downstream.
            session.add(KeywordRanking(date=date(2026, 6, 29), site_id=self.SITE,
                                       keyword="iv therapy", position=8, clicks=60,
                                       impressions=600, search_volume=1234))
            session.add(KeywordRanking(date=date(2026, 6, 30), site_id=self.SITE,
                                       keyword="iv therapy", position=9, clicks=60,
                                       impressions=600, search_volume=1234))
            # Tracked but never captured: no position, no volume. Clicks keep it in the
            # top-5-by-clicks slice so the null actually reaches the response.
            session.add(KeywordRanking(date=date(2026, 6, 30), site_id=self.SITE,
                                       keyword="vitamin drip", position=None, clicks=30,
                                       impressions=300, search_volume=None))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def _top_keywords(self) -> dict:
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        return {row["keyword"]: row for row in resp.json()["topKeywords"]}

    def test_position_keeps_its_decimal_and_is_a_number(self):
        row = self._top_keywords()["iv therapy"]
        self.assertIsInstance(row["position"], float)
        self.assertEqual(row["position"], 8.5)      # was "8" while the query formatted it

    def test_counts_and_volume_are_numbers_not_formatted_strings(self):
        row = self._top_keywords()["iv therapy"]
        for key in ("clicks", "impressions", "volume"):
            self.assertIsInstance(row[key], int, f"{key} must be a raw int")
        self.assertEqual(row["clicks"], 120)
        self.assertEqual(row["impressions"], 1200)
        self.assertEqual(row["volume"], 1234)       # not the string "1,234"

    def test_missing_position_and_volume_are_null_never_zero(self):
        row = self._top_keywords()["vitamin drip"]
        self.assertIsNone(row["position"])
        self.assertIsNone(row["volume"])
        # 0 is a real position/volume; it must never stand in for "unknown".
        self.assertNotEqual(row["position"], 0)
        self.assertNotEqual(row["volume"], 0)


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

    def test_defaults_range_to_28d_when_absent(self):
        """28 days inclusive (a 27-day span), matching Search Console's own window."""
        from django.test import RequestFactory
        from rest_framework.request import Request
        from apps.api.views import resolve_range_periods

        django_request = RequestFactory().get("/api/projects/fusehealth/positions")
        request = Request(django_request)
        _, curr_start, curr_end, _, _ = resolve_range_periods(request, "fusehealth")
        self.assertEqual((curr_end - curr_start).days, 27)

    def test_legacy_30d_resolves_to_the_same_28d_window(self):
        """An older SPA build or a bookmarked ?range=30d must not get a second, different
        window — the whole point of moving to 28d is that one number exists, not two."""
        from django.test import RequestFactory
        from rest_framework.request import Request
        from apps.api.views import resolve_range_periods

        legacy = Request(RequestFactory().get("/api/projects/fusehealth/positions?range=30d"))
        current = Request(RequestFactory().get("/api/projects/fusehealth/positions?range=28d"))
        self.assertEqual(resolve_range_periods(legacy, "fusehealth"),
                         resolve_range_periods(current, "fusehealth"))

    def test_unknown_slug_raises_404(self):
        from django.http import Http404
        from django.test import RequestFactory
        from rest_framework.request import Request
        from apps.api.views import resolve_range_periods

        django_request = RequestFactory().get("/api/projects/does-not-exist/positions")
        request = Request(django_request)
        with self.assertRaises(Http404):
            resolve_range_periods(request, "does-not-exist")
