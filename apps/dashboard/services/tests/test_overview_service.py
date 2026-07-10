import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from sqlalchemy import select

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, AISummary
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class OverviewServiceTests(TestCase):
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
                SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                         clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                         landing_page="https://fusehealth.com/a"),
                SEODaily(date=date(2026, 7, 2), site_id="sc-domain:fusehealth.com",
                         clicks=120, impressions=1100, ctr=0.109, avg_position=7.5,
                         landing_page="https://fusehealth.com/a"),
                SEODaily(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                         clicks=50, impressions=900, ctr=0.055, avg_position=9.0,
                         landing_page="https://fusehealth.com/a"),
            ])

    def test_get_kpi_raw_sums_current_period(self):
        from apps.dashboard.services.overview_service import get_kpi_raw
        current, previous = get_kpi_raw(
            "sc-domain:fusehealth.com",
            date(2026, 7, 1), date(2026, 7, 2),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertEqual(current["clicks"], 220)
        self.assertEqual(current["impressions"], 2100)
        self.assertEqual(previous["clicks"], 50)

    def test_format_kpi_cards_matches_old_shape(self):
        from apps.dashboard.services.overview_service import get_kpi_raw, format_kpi_cards
        current, previous = get_kpi_raw(
            "sc-domain:fusehealth.com",
            date(2026, 7, 1), date(2026, 7, 2),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        cards = format_kpi_cards(current, previous)
        self.assertEqual(cards[0]["label"], "Clicks")
        self.assertEqual(cards[0]["value"], "220")

    def test_query_top_pages_raw_returns_numbers(self):
        from apps.dashboard.services.overview_service import query_top_pages_raw
        pages = query_top_pages_raw("sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2))
        self.assertEqual(pages[0]["clicks"], 220)
        self.assertIsInstance(pages[0]["clicks"], int)

    def test_query_daily_traffic_raw(self):
        from apps.dashboard.services.overview_service import query_daily_traffic_raw
        points = query_daily_traffic_raw("sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2))
        self.assertEqual(len(points), 2)
        self.assertEqual(points[0]["date"], "2026-07-01")
        self.assertEqual(points[0]["clicks"], 100)

    # ── Error-path resilience: a transient DB error must degrade gracefully to
    # the same safe fallback the pre-refactor _get_kpi_stats/_get_top_pages/
    # _get_traffic_chart/_get_ai_summary returned, not propagate and 500 the page.

    def test_get_kpi_raw_returns_empty_dicts_on_db_error(self):
        from apps.dashboard.services import overview_service
        with patch.object(overview_service, "get_session", side_effect=RuntimeError("db down")):
            current, previous = overview_service.get_kpi_raw(
                "sc-domain:fusehealth.com",
                date(2026, 7, 1), date(2026, 7, 2),
                date(2026, 6, 1), date(2026, 6, 1),
            )
        self.assertEqual(current, {})
        self.assertEqual(previous, {})

    def test_format_kpi_cards_does_not_crash_on_empty_fallback(self):
        # Proves the view-level chain (get_kpi_raw error -> format_kpi_cards) survives:
        # format_kpi_cards must not KeyError when handed the {} / {} fallback shape.
        from apps.dashboard.services.overview_service import format_kpi_cards
        cards = format_kpi_cards({}, {})
        self.assertEqual(cards[0]["value"], "0")
        self.assertEqual(cards[0]["delta"], "0%")

    def test_query_top_pages_raw_returns_empty_list_on_db_error(self):
        from apps.dashboard.services import overview_service
        with patch.object(overview_service, "get_session", side_effect=RuntimeError("db down")):
            pages = overview_service.query_top_pages_raw(
                "sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2)
            )
        self.assertEqual(pages, [])

    def test_query_daily_traffic_raw_returns_empty_list_on_db_error(self):
        from apps.dashboard.services import overview_service
        with patch.object(overview_service, "get_session", side_effect=RuntimeError("db down")):
            points = overview_service.query_daily_traffic_raw(
                "sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2)
            )
        self.assertEqual(points, [])

    def test_get_ai_summary_text_returns_none_on_db_error(self):
        from apps.dashboard.services import overview_service
        with patch.object(overview_service, "get_session", side_effect=RuntimeError("db down")):
            summary = overview_service.get_ai_summary_text("sc-domain:fusehealth.com")
        self.assertIsNone(summary)


class RangeAndApiShapeTests(TestCase):
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
                SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                         clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                         landing_page="https://fusehealth.com/a"),
                SEODaily(date=date(2026, 7, 2), site_id="sc-domain:fusehealth.com",
                         clicks=120, impressions=1100, ctr=0.109, avg_position=7.5,
                         landing_page="https://fusehealth.com/a"),
                SEODaily(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                         clicks=50, impressions=900, ctr=0.055, avg_position=9.0,
                         landing_page="https://fusehealth.com/a"),
            ])

    def test_range_to_period_dates_7d(self):
        from apps.dashboard.services.overview_service import range_to_period_dates
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates("7d", date(2026, 7, 10))
        self.assertEqual((curr_end - curr_start).days, 6)
        self.assertEqual(curr_end, date(2026, 7, 9))

    def test_range_to_period_dates_90d(self):
        from apps.dashboard.services.overview_service import range_to_period_dates
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates("90d", date(2026, 7, 10))
        self.assertEqual((curr_end - curr_start).days, 89)

    def test_range_to_period_dates_defaults_to_30d(self):
        from apps.dashboard.services.overview_service import range_to_period_dates
        a = range_to_period_dates("garbage", date(2026, 7, 10))
        b = range_to_period_dates("30d", date(2026, 7, 10))
        self.assertEqual(a, b)

    def test_build_kpis_api_shape(self):
        from apps.dashboard.services.overview_service import build_kpis_api
        current = {"clicks": 220, "impressions": 2100, "ctr": 0.10, "avg_position": 8.0}
        previous = {"clicks": 200, "impressions": 2000, "ctr": 0.09, "avg_position": 9.0}
        kpis = build_kpis_api(current, previous)
        self.assertEqual(kpis[0], {"label": "Total clicks", "value": 220, "delta": 10.0, "unit": "%"})
        self.assertEqual(kpis[3]["unit"], "pos")
        self.assertEqual(kpis[3]["value"], 8.0)

    def test_build_top_pages_api_shape(self):
        from apps.dashboard.services.overview_service import build_top_pages_api
        pages = build_top_pages_api("sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2))
        self.assertEqual(pages[0]["url"], "https://fusehealth.com/a")
        self.assertIn("ctr", pages[0])
        self.assertNotIn("page", pages[0])
