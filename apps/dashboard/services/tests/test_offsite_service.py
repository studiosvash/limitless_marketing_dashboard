import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, GA4TrafficSourceDaily
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
                # Off-site channels -- must be counted.
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 5), channel="Referral",
                                      source="thinkiwi.com", sessions=100, engaged_sessions=50,
                                      conversions=10, revenue=20.0),
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 15), channel="Organic Social",
                                      source="linkedin.com", sessions=200, engaged_sessions=140,
                                      conversions=20, revenue=30.0),
                # On-site / paid channels -- this is the bug this whole test class guards:
                # "Off-site sessions" used to sum the WHOLE site (seo_daily.sessions), so
                # Organic Search and Paid Social traffic inflated a KPI titled "off-site".
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 5), channel="Organic Search",
                                      source="google", sessions=500, engaged_sessions=400,
                                      conversions=50, revenue=100.0),
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 15), channel="Paid Social",
                                      source="facebook.com", sessions=300, engaged_sessions=200,
                                      conversions=30, revenue=60.0),
                # Outside-period row -- must be excluded from the aggregation.
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 5, 15), channel="Referral",
                                      source="other.com", sessions=999, engaged_sessions=999,
                                      conversions=99, revenue=999.0),
            ])

    def test_query_offsite_totals_raw_counts_offsite_channels_only(self):
        from apps.dashboard.services.offsite_service import query_offsite_totals_raw
        totals = query_offsite_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))

        # Referral (100) + Organic Social (200) = 300. Organic Search, Paid Social and the
        # outside-period Referral row must all be excluded.
        self.assertEqual(totals["sessions"], 300)
        # No per-channel user count exists on ga4_traffic_source_daily -- None, not the old
        # whole-site seo_daily.users number under a new label.
        self.assertIsNone(totals["users"])
        self.assertEqual(totals["keyEvents"], 30)
        self.assertEqual(totals["engagedSessions"], 190)
        self.assertEqual(totals["engagementRate"], round(190 / 300 * 100, 1))
        self.assertEqual(totals["revenue"], 50.0)
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
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 1), channel="Referral",
                                      source="a.com", sessions=100, engaged_sessions=50,
                                      conversions=5, revenue=0.0),
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 2), channel="Organic Social",
                                      source="linkedin.com", sessions=200, engaged_sessions=50,
                                      conversions=10, revenue=0.0),
                # Day 3 has ONLY an on-site channel -- it must still appear in the trend with
                # 0 off-site sessions, not be dropped: a missing day would compress the
                # chart's x-axis instead of showing a real gap (see query_offsite_trend_raw).
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 3), channel="Organic Search",
                                      source="google", sessions=50, engaged_sessions=40,
                                      conversions=2, revenue=0.0),
            ])

    def test_query_offsite_trend_raw_is_per_day_and_zero_fills_on_site_only_days(self):
        from apps.dashboard.services.offsite_service import query_offsite_trend_raw
        trend = query_offsite_trend_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 3))

        self.assertEqual(len(trend), 3)
        self.assertEqual([p["date"] for p in trend],
                          ["2026-06-01", "2026-06-02", "2026-06-03"])

        expected = [
            (100, 50, 5),
            (200, 50, 10),
            (0, 0, 0),
        ]
        for point, (sessions, engaged, conversions) in zip(trend, expected):
            self.assertEqual(point["sessions"], sessions)
            self.assertEqual(point["keyEvents"], conversions)
            self.assertEqual(point["engagedSessions"], engaged)
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
            "users": None,
            # None, not 0.0 — an engagement rate over zero sessions is undefined. This key
            # used to re-coerce _engagement's None back to zero on the way out, so the KPI
            # card claimed "0% engaged" for a project GA4 has never measured.
            "engagementRate": None,
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
        # Local to this test (not shared setUp): totals/trend/channels come from
        # GA4TrafficSourceDaily, not SEODaily -- test_unbuilt_fields_report_setup_not_fake_data
        # below shares this class's setUp and asserts `channels == []`, which these rows
        # would break.
        with get_session() as session:
            session.add_all([
                # Off-site channel -- counted in totals/trend.
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 5), channel="Referral",
                                      source="a.com", sessions=100, engaged_sessions=50,
                                      conversions=10, revenue=20.0),
                # On-site channel, same period -- must be excluded from totals/trend even
                # though it dwarfs the off-site row (this is the exact bug being guarded).
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 6, 15), channel="Organic Search",
                                      source="google", sessions=999, engaged_sessions=900,
                                      conversions=90, revenue=500.0),
                GA4TrafficSourceDaily(site_id=SITE_ID, date=date(2026, 5, 10), channel="Referral",
                                      source="a.com", sessions=70, engaged_sessions=40,
                                      conversions=7, revenue=15.0),
            ])

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
        # Sanity: the real data actually landed where expected (not both empty by accident),
        # and the 999-session Organic Search row is excluded from an "off-site" total even
        # though it dwarfs the real off-site (Referral) sessions in the same period.
        self.assertEqual(body["totals"]["sessions"], 100)
        self.assertEqual(body["prev"]["sessions"], 70)

    def test_unbuilt_fields_report_setup_not_fake_data(self):
        from apps.dashboard.services.offsite_service import build_offsite_response
        body = build_offsite_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        self.assertEqual(body["channels"], [])
        self.assertEqual(body["referrers"], [])
        self.assertEqual(body["connectors"], {
            "linkedin": False, "reddit": False, "youtube": False,
            "x": False, "facebook": False, "instagram": False,
        })
        # syncMeta reports the real `ga4` SyncLog row — GA4 is what feeds every number on
        # this page. Nothing has synced in this test, so `lastUpdated` is None and
        # `lastStatus` is "never": the banner prints "never synced" instead of a date.
        # `lastUpdated` used to be handed `totals["engagementRate"]` — an engagement-rate
        # percentage under a key the frontend renders as a timestamp — so assert it is
        # None-or-a-string here and never a number.
        self.assertEqual(body["syncMeta"]["state"], "ready")
        self.assertIsNone(body["syncMeta"]["lastUpdated"])
        self.assertEqual(body["syncMeta"]["lastStatus"], "never")

        # `social` is built from the sources GA4 actually measured, with LinkedIn pinned. No
        # traffic-source rows are seeded here, so LinkedIn's pinned row is all there is — the
        # table no longer manufactures Reddit/YouTube/X rows for platforms this project has
        # never been seen on. LinkedIn's 0 is a measurement (GA4 reported no sessions from it),
        # not a gap, and the spotlight card beside the table reads this row by name.
        #
        # What this test exists to guard is `impressions`. GA4 can only see sessions that
        # ARRIVED from a source; it cannot see how many times a post was shown on the
        # platform. That number lives in each platform's own API and no platform connector is
        # wired, so it is None for every row, connected or not. It used to be invented as
        # `sessions * 12 / 8 / 5 / 4` — that is the fabrication that must never come back.
        self.assertEqual([r["platform"] for r in body["social"]], ["LinkedIn"])
        for row in body["social"]:
            self.assertIsNone(row["impressions"], f"{row['platform']} impressions must stay None")
            self.assertFalse(row["connected"])
            self.assertEqual(row["sessions"], 0)
            # An engagement rate over zero sessions is undefined, not 0% — "0% of visitors
            # engaged" claims a measurement nobody took. See offsite_service._engagement.
            self.assertIsNone(row["engagedRate"], f"{row['platform']} engagedRate over 0 sessions")
            self.assertIsNone(row["engagementRate"])

    def test_stale_platform_connector_toggle_does_not_claim_a_connection(self):
        """`connected` must not come from ProjectSettings["platformConnectors"].

        Those booleans were set by a Settings "Connect" button that authenticated nothing —
        no OAuth, no credentials, no verification — and a `true` made this page announce
        "Connector live · impressions + click-throughs" for a platform whose impressions are
        None and whose connector is not registered in the sync engine at all. The button is
        now inert, so a project carrying a stale `true` from before could never clear it.
        A connection nobody made must not be reported as one.
        """
        from apps.dashboard.models import ProjectSettings
        from apps.dashboard.services.offsite_service import build_offsite_response

        ProjectSettings.objects.create(
            site_url=SITE_ID,
            data={"platformConnectors": {"linkedin": True, "reddit": True, "youtube": True,
                                         "x": True, "facebook": True, "instagram": True}},
        )

        body = build_offsite_response(
            SITE_ID, self.curr_start, self.curr_end, self.prev_start, self.prev_end
        )

        self.assertEqual(body["connectors"], {
            "linkedin": False, "reddit": False, "youtube": False,
            "x": False, "facebook": False, "instagram": False,
        })
        for row in body["social"]:
            self.assertFalse(row["connected"], f"{row['platform']} claimed a connection from a toggle")
            self.assertIsNone(row["impressions"], f"{row['platform']} impressions must stay None")


class EngagementRateTests(TestCase):
    """`_engagement` is the single place that decides whether an engagement rate exists.
    Every rate on this page (social platforms, referring domains, channel mix) goes through
    it, so the "undefined is not zero" rule cannot drift apart between them."""

    def test_zero_sessions_is_undefined_not_zero(self):
        from apps.dashboard.services.offsite_service import _engagement
        self.assertEqual(_engagement(0, 0),
                         {"engagedRate": None, "engagementRate": None})

    def test_measured_sessions_still_produce_a_real_rate(self):
        """The guard must not swallow real data — a rate of exactly 0 over REAL sessions is a
        genuine measurement and has to survive as 0, not become None."""
        from apps.dashboard.services.offsite_service import _engagement
        self.assertEqual(_engagement(30, 120),
                         {"engagedRate": 0.25, "engagementRate": 25.0})
        self.assertEqual(_engagement(0, 120),
                         {"engagedRate": 0.0, "engagementRate": 0.0})

    def test_the_two_keys_never_disagree_about_existence(self):
        from apps.dashboard.services.offsite_service import _engagement
        for engaged, sessions in ((0, 0), (0, 10), (5, 10), (10, 10)):
            result = _engagement(engaged, sessions)
            self.assertEqual(result["engagedRate"] is None,
                             result["engagementRate"] is None,
                             f"disagreement at engaged={engaged} sessions={sessions}")
