import tempfile
from datetime import date
from pathlib import Path

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
