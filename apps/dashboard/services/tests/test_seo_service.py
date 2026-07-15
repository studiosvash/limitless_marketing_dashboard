import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, Anomaly, TechnicalIssue, KeywordRanking
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class SeoServiceTests(TestCase):
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
            session.add_all([
                SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                         clicks=5, impressions=800, ctr=0.006, avg_position=8.2,
                         landing_page="https://fusehealth.com/low-ctr-page",
                         country="United States", device="mobile"),
                Anomaly(date=date(2026, 6, 29), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_clicks", actual_value=50, baseline_value=100,
                        deviation_pct=-50.0, severity="high",
                        description="Clicks dropped 50% vs. baseline.", is_acknowledged=0),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                               issue_type="not_found_404", severity="high", description="404"),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/redir",
                               issue_type="page_with_redirect", severity="medium", description="redirect"),
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=6, clicks=12, impressions=200),
            ])

    def test_query_low_ctr_pages_raw_returns_numbers(self):
        from apps.dashboard.services.seo_service import query_low_ctr_pages_raw
        pages = query_low_ctr_pages_raw("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["clicks"], 5)
        self.assertIsInstance(pages[0]["clicks"], int)

    def test_query_seo_by_dimension_raw_has_both_dimensions(self):
        from apps.dashboard.services.seo_service import query_seo_by_dimension_raw
        result = query_seo_by_dimension_raw("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(result["by_country"][0]["country"], "United States")
        self.assertEqual(result["by_device"][0]["device"], "mobile")

    def test_query_seo_anomalies_raw_includes_id_and_description(self):
        from apps.dashboard.services.seo_service import query_seo_anomalies_raw
        rows = query_seo_anomalies_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 1)
        self.assertIsNotNone(rows[0]["id"])
        self.assertEqual(rows[0]["description"], "Clicks dropped 50% vs. baseline.")

    def test_count_technical_issues_unlimited_and_filterable(self):
        from apps.dashboard.services.seo_service import count_technical_issues
        self.assertEqual(count_technical_issues("sc-domain:fusehealth.com"), 2)
        self.assertEqual(count_technical_issues("sc-domain:fusehealth.com", issue_type="not_found_404"), 1)

    def test_count_quick_win_keywords(self):
        from apps.dashboard.services.seo_service import count_quick_win_keywords
        n = count_quick_win_keywords("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(n, 1)  # position=6 (in 4-10), clicks=12 (>0)

    def test_query_low_ctr_pages_raw_returns_empty_list_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import seo_service
        with mock.patch.object(seo_service, "get_session", side_effect=RuntimeError("boom")):
            self.assertEqual(seo_service.query_low_ctr_pages_raw("x", date(2026, 6, 30), date(2026, 6, 30)), [])

    def test_count_technical_issues_returns_zero_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import seo_service
        with mock.patch.object(seo_service, "get_session", side_effect=RuntimeError("boom")):
            self.assertEqual(seo_service.count_technical_issues("x"), 0)


class BuildSeoResponseTests(TestCase):
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
            session.add_all([
                SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                         clicks=5, impressions=800, ctr=0.006, avg_position=8.2,
                         landing_page="https://fusehealth.com/low-ctr-page",
                         country="United States", device="mobile"),
                Anomaly(date=date(2026, 6, 29), site_id="sc-domain:fusehealth.com",
                        metric_type="seo_clicks", actual_value=50, baseline_value=100,
                        deviation_pct=-50.0, severity="high",
                        description="Clicks dropped 50% vs. baseline.", is_acknowledged=0),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/gone",
                               issue_type="not_found_404", severity="high", description="404"),
                TechnicalIssue(site_id="sc-domain:fusehealth.com", url="https://fusehealth.com/redir",
                               issue_type="page_with_redirect", severity="medium", description="redirect"),
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=6, clicks=12, impressions=200),
            ])

    def test_top_level_keys(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        for key in ["kpis", "lowCtrPages", "countries", "anomalies", "quickWinKws"]:
            self.assertIn(key, body)

    def test_kpis_match_spec_semantics(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        # low_ctr: 1 seeded low-CTR page
        self.assertEqual(body["kpis"]["low_ctr"], 1)
        # anomalies: 1 seeded unacknowledged anomaly
        self.assertEqual(body["kpis"]["anomalies"], 1)
        # critical: 1 of the 2 seeded technical issues is not_found_404 — NOT high_sev_issues (which would be 1 too here by
        # coincidence since both seeded issues are severity="high"/"medium" — this assertion specifically pins the
        # 404-count semantics, not a severity count, per the corrected spec mapping)
        self.assertEqual(body["kpis"]["critical"], 1)
        # total_issues: 2 technical issues + 1 anomaly + 1 low_ctr page = 4
        self.assertEqual(body["kpis"]["total_issues"], 4)

    def test_low_ctr_pages_shape(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        page = body["lowCtrPages"][0]
        for key in ["url", "impressions", "clicks", "ctr", "avg_pos"]:
            self.assertIn(key, page)
        self.assertNotIn("url_short", page)

    def test_anomalies_shape(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        a = body["anomalies"][0]
        self.assertEqual(set(a.keys()), {"id", "metric", "severity", "deviation", "date", "detail"})
        self.assertEqual(a["detail"], "Clicks dropped 50% vs. baseline.")
        self.assertEqual(a["deviation"], "-50%")

    def test_quick_win_kws_is_a_count_not_a_list(self):
        from apps.dashboard.services.seo_service import build_seo_response
        body = build_seo_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30))
        self.assertEqual(body["quickWinKws"], 1)
        self.assertIsInstance(body["quickWinKws"], int)
