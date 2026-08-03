import calendar
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, AdMetricDaily, SEODaily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_ID = "sc-domain:fusehealth.com"


class AdsTotalsRawTests(TestCase):
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
                # In-period rows -- chosen so the spend-weighted roas average (3.5) differs
                # from the naive/unweighted average ((2.0 + 4.0) / 2 == 3.0).
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 6, 5), platform="google",
                               campaign="Brand", spend=100.0, clicks=10, impressions=1000,
                               conversions=5, roas=2.0),
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 6, 15), platform="google",
                               campaign="NonBrand", spend=300.0, clicks=20, impressions=2000,
                               conversions=8, roas=4.0),
                # Outside-period row -- must be excluded from the aggregation.
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 5, 15), platform="google",
                               campaign="Old", spend=9999.0, clicks=999, impressions=99999,
                               conversions=999, roas=100.0),
                # GA4 cross-reference row, in-period.
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 10), sessions=500, users=400,
                         engagement_rate=0.6, conversions=25),
                # GA4 outside-period row -- must be excluded.
                SEODaily(site_id=SITE_ID, date=date(2026, 5, 10), sessions=500, users=400,
                         engagement_rate=0.6, conversions=999),
            ])

    def test_query_ads_totals_raw_uses_spend_weighted_roas_average(self):
        from apps.dashboard.services.ads_service import query_ads_totals_raw
        totals = query_ads_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))

        total_spend = 400.0
        naive_avg_roas = (2.0 + 4.0) / 2  # 3.0
        weighted_avg_roas = (100.0 * 2.0 + 300.0 * 4.0) / total_spend  # 3.5
        self.assertNotEqual(round(weighted_avg_roas, 4), round(naive_avg_roas, 4))

        self.assertEqual(totals["spend"], total_spend)
        self.assertEqual(totals["clicks"], 30.0)
        self.assertEqual(totals["impressions"], 3000.0)
        self.assertEqual(totals["conversions"], 13.0)
        self.assertEqual(totals["cpc"], total_spend / 30.0)
        self.assertEqual(totals["roas"], weighted_avg_roas)

    def test_query_ads_totals_raw_ga4_key_events_reflects_seo_daily(self):
        from apps.dashboard.services.ads_service import query_ads_totals_raw
        totals = query_ads_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(totals["ga4_key_events"], 25.0)

    def test_query_ads_totals_raw_conv_value_and_ga4_revenue_are_always_zero(self):
        from apps.dashboard.services.ads_service import query_ads_totals_raw
        totals = query_ads_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(totals["conv_value"], 0.0)
        self.assertEqual(totals["ga4_revenue"], 0.0)


class AdsTotalsRawMixedRoasTests(TestCase):
    """A row with spend but no roas value must not be treated as a zero-return contributor
    to the weighted average's denominator -- that would silently deflate roas below the true
    average over the rows that actually report one (final-review finding on Task 1)."""

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
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 6, 5), platform="google",
                               campaign="Known", spend=800.0, clicks=40, impressions=4000,
                               conversions=16, roas=4.0),
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 6, 15), platform="google",
                               campaign="Unknown", spend=200.0, clicks=10, impressions=1000,
                               conversions=0, roas=None),
            ])

    def test_null_roas_spend_excluded_from_weighted_average_denominator(self):
        from apps.dashboard.services.ads_service import query_ads_totals_raw
        totals = query_ads_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))

        # Total spend across both rows is 1000, but only 800 of it has a known roas.
        self.assertEqual(totals["spend"], 1000.0)
        # The naive "divide by all spend" bug would give 3200/1000 = 3.2.
        self.assertNotEqual(totals["roas"], 3.2)
        # The correct weighted average is over only the known-roas population: 3200/800 = 4.0.
        self.assertEqual(totals["roas"], 4.0)


class AdsTotalsRawEmptyDbTests(TestCase):
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

    def test_query_ads_totals_raw_is_real_zeros_on_empty_db(self):
        from apps.dashboard.services.ads_service import query_ads_totals_raw
        totals = query_ads_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(totals, {
            "spend": 0.0, "clicks": 0.0, "impressions": 0.0, "conversions": 0.0,
            "cpc": 0.0, "roas": 0.0, "conv_value": 0.0, "ga4_key_events": 0.0, "ga4_revenue": 0.0,
        })
        for value in totals.values():
            self.assertIsNotNone(value)


class AdsTrendRawTests(TestCase):
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
                # 2026-06-01: only AdMetricDaily.
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 6, 1), platform="google",
                               campaign="A", spend=50.0, clicks=5, impressions=500,
                               conversions=3, roas=1.5),
                # 2026-06-02: only SEODaily.
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 2), sessions=100, users=90,
                         engagement_rate=0.5, conversions=7),
                # 2026-06-03: both.
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 6, 3), platform="google",
                               campaign="B", spend=20.0, clicks=2, impressions=200,
                               conversions=1, roas=2.0),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 3), sessions=40, users=35,
                         engagement_rate=0.4, conversions=4),
            ])

    def test_query_ads_trend_raw_merges_per_day_without_dropping_dates(self):
        from apps.dashboard.services.ads_service import query_ads_trend_raw
        trend = query_ads_trend_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 3))

        self.assertEqual(len(trend), 3)
        self.assertEqual([p["date"] for p in trend],
                          ["2026-06-01", "2026-06-02", "2026-06-03"])

        day1, day2, day3 = trend
        # Day with only AdMetricDaily -- ga4_key_events honestly 0.
        self.assertEqual(day1["spend"], 50.0)
        self.assertEqual(day1["conversions"], 3.0)
        self.assertEqual(day1["ga4_key_events"], 0.0)
        # Day with only SEODaily -- spend/conversions honestly 0.
        self.assertEqual(day2["spend"], 0.0)
        self.assertEqual(day2["conversions"], 0.0)
        self.assertEqual(day2["ga4_key_events"], 7.0)
        # Day with both.
        self.assertEqual(day3["spend"], 20.0)
        self.assertEqual(day3["conversions"], 1.0)
        self.assertEqual(day3["ga4_key_events"], 4.0)


class AdsPacingRawTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.today = date.today()
        self.month_start = self.today.replace(day=1)
        # Guaranteed to fall in the previous calendar month regardless of today's date.
        self.last_month_day = self.month_start - timedelta(days=1)

        with get_session() as session:
            session.add_all([
                AdMetricDaily(site_id=SITE_ID, date=self.month_start, platform="google",
                               campaign="ThisMonth", spend=150.0, clicks=15, impressions=1500,
                               conversions=3, roas=1.0),
                AdMetricDaily(site_id=SITE_ID, date=self.last_month_day, platform="google",
                               campaign="LastMonth", spend=9999.0, clicks=999, impressions=99999,
                               conversions=999, roas=1.0),
            ])

    def test_query_ads_pacing_raw_scopes_to_calendar_month_to_date(self):
        from apps.dashboard.services.ads_service import query_ads_pacing_raw
        pacing = query_ads_pacing_raw(SITE_ID)

        # Only the current-month row counts; last month's spend is excluded.
        self.assertEqual(pacing["mtd_spend"], 150.0)
        self.assertEqual(pacing["monthly_budget"], 0.0)
        self.assertEqual(pacing["pct"], 0)
        self.assertEqual(pacing["channels"], [])

        day_of_month = self.today.day
        days_in_month = calendar.monthrange(self.today.year, self.today.month)[1]
        self.assertEqual(pacing["day_of_month"], day_of_month)
        self.assertEqual(pacing["days_in_month"], days_in_month)

        expected_projected = 150.0 / day_of_month * days_in_month
        self.assertEqual(pacing["projected"], expected_projected)


class BuildAdsResponseTests(TestCase):
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
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 6, 5), platform="google",
                               campaign="A", spend=100.0, clicks=10, impressions=1000,
                               conversions=5, roas=2.0),
                AdMetricDaily(site_id=SITE_ID, date=date(2026, 5, 5), platform="google",
                               campaign="A", spend=60.0, clicks=6, impressions=600,
                               conversions=3, roas=1.0),
            ])

    def test_honest_empty_arrays_are_exactly_empty(self):
        from apps.dashboard.services.ads_service import build_ads_response
        body = build_ads_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        self.assertEqual(body["campaigns"], [])
        self.assertEqual(body["searchTerms"], [])
        self.assertEqual(body["attribution"], [])
        self.assertEqual(body["landingPages"], [])
        self.assertEqual(body["negatives"], [])

    def test_sync_meta_is_real_connected_flag_plus_honest_zeros(self):
        from apps.dashboard.services.ads_service import build_ads_response
        body = build_ads_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        sync_meta = body["syncMeta"]
        self.assertIn(sync_meta["connected"], (True, False))
        self.assertIsInstance(sync_meta["connected"], bool)
        self.assertIsNone(sync_meta["cadence"])
        self.assertIsNone(sync_meta["last_pull"])
        self.assertIsNone(sync_meta["next_pull"])
        self.assertEqual(sync_meta["ops_used"], 0)
        self.assertEqual(sync_meta["ops_limit"], 0)
        self.assertEqual(sync_meta["ga4_tokens_used"], 0)
        self.assertEqual(sync_meta["ga4_tokens_limit"], 0)

    def test_window_matches_passed_in_dates(self):
        from apps.dashboard.services.ads_service import build_ads_response
        body = build_ads_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        self.assertEqual(body["window"], {
            "from": "2026-06-01",
            "to": "2026-06-30",
            "days": (self.curr_end - self.curr_start).days + 1,
        })

    def test_real_fields_match_raw_calculators(self):
        from apps.dashboard.services.ads_service import (
            build_ads_response,
            query_ads_totals_raw,
            query_ads_trend_raw,
            query_ads_pacing_raw,
        )
        body = build_ads_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        self.assertEqual(body["totals"], query_ads_totals_raw(SITE_ID, self.curr_start, self.curr_end))
        self.assertEqual(body["prev"], query_ads_totals_raw(SITE_ID, self.prev_start, self.prev_end))
        self.assertEqual(body["trend"], query_ads_trend_raw(SITE_ID, self.curr_start, self.curr_end))
        self.assertEqual(body["pacing"], query_ads_pacing_raw(SITE_ID))
        # Sanity: the real data actually landed where expected (not both empty by accident).
        self.assertEqual(body["totals"]["spend"], 100.0)
        self.assertEqual(body["prev"]["spend"], 60.0)


class SyncMetaConnectedFromDbCredentialTests(TestCase):
    """A Google Ads credential saved through Settings (encrypted, per-site, no .env
    involvement) must make the Ads page's syncMeta.connected flag True even before any
    sync has ever written a spend row -- otherwise Settings says "Test connection: OK"
    while the Ads page says "not connected" for the exact same site and platform
    (final-review finding on this feature)."""

    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        # Deliberately no seeded AdMetricDaily rows -- no sync has ever run.

    @mock.patch.dict("os.environ", {"GOOGLE_ADS_CUSTOMER_ID": "", "GOOGLE_ADS_DEVELOPER_TOKEN": ""})
    def test_connected_true_with_no_env_no_spend_but_saved_db_credential(self):
        from apps.dashboard.services.settings_service import apply_settings_update
        from apps.dashboard.services.ads_service import build_ads_response

        result = apply_settings_update(SITE_ID, {"adsCredentials": {"google_ads": {
            "developer_token": "supersecrettoken1234", "customer_id": "123-456-7890",
        }}})
        self.assertEqual(result, {"ok": True})

        body = build_ads_response(
            SITE_ID, date(2026, 6, 1), date(2026, 6, 30), date(2026, 5, 1), date(2026, 5, 31),
        )
        self.assertEqual(body["totals"]["spend"], 0.0)
        self.assertIs(body["syncMeta"]["connected"], True)
