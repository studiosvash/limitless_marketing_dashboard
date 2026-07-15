import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_ID = "sc-domain:fusehealth.com"


class OffsiteTotalsRawTests(TestCase):
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
                # In-period rows.
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 5), sessions=100, users=80,
                         engagement_rate=0.5, conversions=10, landing_page="/a"),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 15), sessions=200, users=150,
                         engagement_rate=0.7, conversions=20, landing_page="/b"),
                # Outside-period row -- must be excluded from the aggregation.
                SEODaily(site_id=SITE_ID, date=date(2026, 5, 15), sessions=999, users=999,
                         engagement_rate=0.9, conversions=99, landing_page="/c"),
            ])

    def test_query_offsite_totals_raw_aggregates_in_period_rows_only(self):
        from apps.dashboard.services.offsite_service import query_offsite_totals_raw
        totals = query_offsite_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))

        total_sessions = 300
        avg_engagement_rate = (0.5 + 0.7) / 2  # 0.6
        self.assertEqual(totals["sessions"], total_sessions)
        self.assertEqual(totals["users"], 230)
        self.assertEqual(totals["keyEvents"], 30)
        self.assertEqual(totals["engagementRate"], round(avg_engagement_rate * 100, 1))
        self.assertEqual(totals["engagedSessions"], round(total_sessions * avg_engagement_rate))
        self.assertEqual(totals["revenue"], 0)
        self.assertEqual(totals["referringDomains"], 0)


class OffsiteTrendRawTests(TestCase):
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
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 1), sessions=100,
                         engagement_rate=0.5, conversions=5),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 2), sessions=200,
                         engagement_rate=0.25, conversions=10),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 3), sessions=50,
                         engagement_rate=0.8, conversions=2),
            ])

    def test_query_offsite_trend_raw_is_per_day_not_period_average(self):
        from apps.dashboard.services.offsite_service import query_offsite_trend_raw
        trend = query_offsite_trend_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 3))

        self.assertEqual(len(trend), 3)
        self.assertEqual([p["date"] for p in trend],
                          ["2026-06-01", "2026-06-02", "2026-06-03"])

        expected = [
            (100, 0.5, 5),
            (200, 0.25, 10),
            (50, 0.8, 2),
        ]
        for point, (sessions, er, conversions) in zip(trend, expected):
            self.assertEqual(point["sessions"], sessions)
            self.assertEqual(point["keyEvents"], conversions)
            self.assertEqual(point["engagedSessions"], round(sessions * er))
            self.assertEqual(point["revenue"], 0)


class OffsiteLandingPagesRawTests(TestCase):
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
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 1), sessions=300,
                         engagement_rate=0.5, conversions=10, landing_page="/a"),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 1), sessions=100,
                         engagement_rate=0.3, conversions=5, landing_page="/b"),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 1), sessions=200,
                         engagement_rate=0.4, conversions=8, landing_page="/c"),
                # Null landing_page -- must be excluded entirely.
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 2), sessions=999,
                         engagement_rate=0.9, conversions=99, landing_page=None),
            ])

    def test_query_offsite_landing_pages_raw_orders_desc_and_excludes_null(self):
        from apps.dashboard.services.offsite_service import query_offsite_landing_pages_raw
        rows = query_offsite_landing_pages_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 2))

        self.assertEqual(len(rows), 3)
        self.assertEqual([r["url"] for r in rows], ["/a", "/c", "/b"])
        self.assertEqual([r["sessions"] for r in rows], [300, 200, 100])
        for r in rows:
            self.assertEqual(r["topSource"], "")


class OffsiteEmptyDbTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        # Deliberately no seeded rows.

    def test_all_three_raw_calculators_are_safe_on_empty_db(self):
        from apps.dashboard.services.offsite_service import (
            query_offsite_totals_raw,
            query_offsite_trend_raw,
            query_offsite_landing_pages_raw,
        )
        totals = query_offsite_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(totals, {
            "sessions": 0,
            "users": 0,
            "engagementRate": 0.0,
            "engagedSessions": 0,
            "keyEvents": 0,
            "revenue": 0,
            "referringDomains": 0,
        })
        self.assertEqual(query_offsite_trend_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30)), [])
        self.assertEqual(query_offsite_landing_pages_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30)), [])


class BuildOffsiteResponseTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.curr_start, self.curr_end = date(2026, 6, 1), date(2026, 6, 30)
        self.prev_start, self.prev_end = date(2026, 5, 1), date(2026, 5, 31)

        with get_session() as session:
            session.add_all([
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 5), sessions=100, users=80,
                         engagement_rate=0.5, conversions=10, landing_page="/a"),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 15), sessions=50, users=40,
                         engagement_rate=0.6, conversions=5, landing_page="/b"),
                SEODaily(site_id=SITE_ID, date=date(2026, 5, 10), sessions=70, users=60,
                         engagement_rate=0.4, conversions=7, landing_page="/a"),
            ])

    def test_real_fields_match_raw_calculators(self):
        from apps.dashboard.services.offsite_service import (
            build_offsite_response,
            query_offsite_totals_raw,
            query_offsite_trend_raw,
            query_offsite_landing_pages_raw,
        )
        body = build_offsite_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        self.assertEqual(body["totals"], query_offsite_totals_raw(SITE_ID, self.curr_start, self.curr_end))
        self.assertEqual(body["prev"], query_offsite_totals_raw(SITE_ID, self.prev_start, self.prev_end))
        self.assertEqual(body["trend"], query_offsite_trend_raw(SITE_ID, self.curr_start, self.curr_end))
        self.assertEqual(
            body["landingPages"],
            query_offsite_landing_pages_raw(SITE_ID, self.curr_start, self.curr_end),
        )
        # Sanity: the real data actually landed where expected (not both empty by accident).
        self.assertEqual(body["totals"]["sessions"], 150)
        self.assertEqual(body["prev"]["sessions"], 70)

    def test_unbuilt_fields_report_setup_not_fake_data(self):
        from apps.dashboard.services.offsite_service import build_offsite_response
        body = build_offsite_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        self.assertEqual(body["channels"], [])
        self.assertEqual(body["referrers"], [])
        self.assertEqual(body["social"], [])
        self.assertEqual(body["connectors"], {
            "linkedin": False, "reddit": False, "youtube": False,
            "x": False, "facebook": False, "instagram": False,
        })
        self.assertEqual(body["syncMeta"], {"state": "setup"})
