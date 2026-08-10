"""Three Off-site surfaces that discarded data the query had already fetched.

  * the trend grouped by (date, channel) and then summed the channel away;
  * the social table rendered a FIXED four-platform roster, so every other real source GA4
    measured was invisible and platforms GA4 never saw printed a row anyway;
  * the referring-domain table already knew which links drove traffic and which did not, and
    expressed the difference as a 0 in a column.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Backlink, GA4TrafficSourceDaily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_ID = "sc-domain:fusehealth.com"
CURR = (date(2026, 6, 1), date(2026, 6, 30))
PREV = (date(2026, 5, 1), date(2026, 5, 31))


class _AnalyticsDbTestCase(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def _build(self):
        from apps.dashboard.services.offsite_service import build_offsite_response
        return build_offsite_response(SITE_ID, CURR[0], CURR[1], PREV[0], PREV[1])

    @staticmethod
    def _row(source, sessions, channel="Referral", day=5, engaged=0, conv=0, rev=0.0):
        return GA4TrafficSourceDaily(
            site_id=SITE_ID, date=date(2026, 6, day), channel=channel, source=source,
            sessions=sessions, engaged_sessions=engaged, conversions=conv, revenue=rev,
        )


class TrendByChannelTests(_AnalyticsDbTestCase):
    def setUp(self):
        super().setUp()
        with get_session() as session:
            session.add_all([
                self._row("a.com", 100, channel="Referral", day=1),
                self._row("linkedin.com", 40, channel="Organic Social", day=1),
                self._row("a.com", 60, channel="Referral", day=2),
                self._row("youtube.com", 20, channel="Organic Video", day=2),
                # On-site only day: kept on the x-axis at zero, with a zero for every band.
                self._row("google", 900, channel="Organic Search", day=3),
            ])

    def test_each_point_carries_its_per_channel_split(self):
        from apps.dashboard.services.offsite_service import query_offsite_trend_raw
        trend = query_offsite_trend_raw(SITE_ID, *CURR)
        by_date = {p["date"]: p for p in trend}

        self.assertEqual(by_date["2026-06-01"]["channels"],
                         {"Referral": 100, "Organic Social": 40, "Organic Video": 0})
        self.assertEqual(by_date["2026-06-02"]["channels"],
                         {"Referral": 60, "Organic Social": 0, "Organic Video": 20})
        self.assertEqual(by_date["2026-06-03"]["channels"],
                         {"Referral": 0, "Organic Social": 0, "Organic Video": 0})

    def test_the_bands_always_add_up_to_the_line_they_replace(self):
        """The stacked areas and the `sessions` total are the same measurement drawn twice;
        they must not be able to disagree."""
        from apps.dashboard.services.offsite_service import query_offsite_trend_raw
        for point in query_offsite_trend_raw(SITE_ID, *CURR):
            self.assertEqual(sum(point["channels"].values()), point["sessions"],
                             f"bands != total on {point['date']}")

    def test_every_point_carries_the_same_channel_keys(self):
        """A stacked chart needs one stable band set across the whole x-axis; a per-day key
        set would make a band appear and vanish mid-series."""
        from apps.dashboard.services.offsite_service import query_offsite_trend_raw
        trend = query_offsite_trend_raw(SITE_ID, *CURR)
        keys = {tuple(p["channels"].keys()) for p in trend}
        self.assertEqual(len(keys), 1, f"channel key sets differ across points: {keys}")


class SocialTableIsRealSourcesTests(_AnalyticsDbTestCase):
    def setUp(self):
        super().setUp()
        with get_session() as session:
            session.add_all([
                # The biggest real off-site source on this fixture is not a "platform" at all.
                self._row("news.ycombinator.com", 800, channel="Referral", day=2,
                          engaged=400, conv=8, rev=80.0),
                self._row("substack.com", 300, channel="Referral", day=3),
                self._row("reddit.com", 200, channel="Organic Social", day=4),
                self._row("m.reddit.com", 50, channel="Organic Social", day=5),
                self._row("youtu.be", 90, channel="Organic Video", day=6),
                # Paid Social must stay out — it is bought, not earned.
                self._row("facebook.com", 5000, channel="Paid Social", day=7),
            ])

    def test_real_sources_appear_instead_of_a_fixed_roster(self):
        body = self._build()
        platforms = [r["platform"] for r in body["social"]]
        self.assertIn("news.ycombinator.com", platforms)
        self.assertIn("substack.com", platforms)
        self.assertIn("Reddit", platforms)
        self.assertIn("YouTube", platforms)
        # A platform GA4 never saw no longer prints a manufactured row.
        self.assertNotIn("X / Twitter", platforms)
        # Paid Social is not off-site.
        self.assertNotIn("facebook.com", platforms)

    def test_linkedin_is_pinned_first_even_with_no_sessions(self):
        """The LinkedIn spotlight card reads this list by platform name, and LinkedIn is the
        platform this page reports on by name, so its row stays whether or not GA4 saw it."""
        body = self._build()
        self.assertEqual(body["social"][0]["platform"], "LinkedIn")
        self.assertEqual(body["social"][0]["sessions"], 0)
        self.assertIsNone(body["social"][0]["engagementRate"])

    def test_rows_after_the_pin_are_ordered_by_sessions(self):
        body = self._build()
        rest = [r["sessions"] for r in body["social"][1:]]
        self.assertEqual(rest, sorted(rest, reverse=True))
        self.assertEqual(body["social"][1]["platform"], "news.ycombinator.com")
        self.assertEqual(body["social"][1]["sessions"], 800)

    def test_a_platforms_hosts_are_merged_into_one_row(self):
        body = self._build()
        reddit = next(r for r in body["social"] if r["platform"] == "Reddit")
        self.assertEqual(reddit["sessions"], 250)

    def test_impressions_are_still_never_invented(self):
        body = self._build()
        for row in body["social"]:
            self.assertIsNone(row["impressions"], f"{row['platform']} impressions")
            self.assertFalse(row["connected"])


class ReferrerTrafficSplitTests(_AnalyticsDbTestCase):
    def setUp(self):
        super().setUp()
        with get_session() as session:
            session.add_all([
                Backlink(site_id=SITE_ID, referring_domain="drives.com",
                         target_url="https://fusehealth.com/a", domain_rank=80, dofollow=1),
                Backlink(site_id=SITE_ID, referring_domain="silent-one.com",
                         target_url="https://fusehealth.com/b", domain_rank=40, dofollow=1),
                Backlink(site_id=SITE_ID, referring_domain="silent-two.com",
                         target_url="https://fusehealth.com/c", domain_rank=30, dofollow=1),
                self._row("drives.com", 45, channel="Referral", day=4),
            ])

    def test_each_row_says_whether_it_drove_traffic(self):
        body = self._build()
        by_domain = {r["domain"]: r for r in body["referrers"]}
        self.assertTrue(by_domain["drives.com"]["drivesTraffic"])
        self.assertFalse(by_domain["silent-one.com"]["drivesTraffic"])

    def test_the_split_is_counted_over_every_linking_domain(self):
        body = self._build()
        self.assertEqual(body["referrerSplit"],
                         {"total": 3, "driving": 1, "linkOnly": 2})
