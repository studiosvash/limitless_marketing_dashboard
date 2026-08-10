"""Platform attribution on the Off-site page.

Every assertion here guards the same class of bug: deciding which platform sent a session by
asking whether a short string appears ANYWHERE inside GA4's `sessionSource`. `"t.co" in source`
is true for `reddit.com`, `hubspot.com`, `blogspot.com` and every `*t.com` domain, and false for
`twitter.com` — so Reddit's traffic was added to X's row, X's own domain was not, and LinkedIn's
own shortener (`lnkd.in`) went to no platform at all.
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


class PlatformDomainMapTests(TestCase):
    """The matcher itself, independent of the database."""

    def test_a_platform_domain_matches_the_host_or_a_subdomain_of_it(self):
        from apps.dashboard.services.offsite_service import platform_for_source
        self.assertEqual(platform_for_source("reddit.com"), "reddit")
        self.assertEqual(platform_for_source("m.reddit.com"), "reddit")
        self.assertEqual(platform_for_source("out.reddit.com"), "reddit")
        self.assertEqual(platform_for_source("redd.it"), "reddit")

    def test_t_co_no_longer_swallows_every_domain_that_contains_it(self):
        """`"t.co" in "reddit.com"` is True. That single substring test moved Reddit's whole
        referral volume into the X / Twitter row while X's own domain matched nothing."""
        from apps.dashboard.services.offsite_service import platform_for_source
        self.assertEqual(platform_for_source("t.co"), "x")
        self.assertEqual(platform_for_source("twitter.com"), "x")
        self.assertEqual(platform_for_source("x.com"), "x")
        for not_x in ("reddit.com", "hubspot.com", "blogspot.com", "content.com", "t.com"):
            self.assertNotEqual(platform_for_source(not_x), "x", f"{not_x} attributed to X")

    def test_platform_shorteners_are_attributed_to_their_platform(self):
        from apps.dashboard.services.offsite_service import platform_for_source
        self.assertEqual(platform_for_source("lnkd.in"), "linkedin")
        self.assertEqual(platform_for_source("linkedin.com"), "linkedin")
        self.assertEqual(platform_for_source("youtu.be"), "youtube")
        self.assertEqual(platform_for_source("youtube.com"), "youtube")
        self.assertEqual(platform_for_source("m.youtube.com"), "youtube")

    def test_a_bare_non_host_source_matches_nothing(self):
        from apps.dashboard.services.offsite_service import platform_for_source
        for src in ("google", "(direct)", "newsletter", "", None, "linkedin"):
            self.assertIsNone(platform_for_source(src), f"{src!r} was attributed to a platform")

    def test_every_source_maps_to_at_most_one_platform(self):
        """First match wins, so no session can be counted under two platforms."""
        from apps.dashboard.services.offsite_service import PLATFORM_DOMAINS, platform_for_source
        for platform, domains in PLATFORM_DOMAINS.items():
            for domain in domains:
                self.assertEqual(platform_for_source(domain), platform)
                self.assertEqual(platform_for_source("www." + domain), platform)


class SocialAttributionTests(_AnalyticsDbTestCase):
    def setUp(self):
        super().setUp()
        with get_session() as session:
            session.add_all([
                # Reddit — must NOT land in the X row.
                self._row("reddit.com", 300, day=2),
                self._row("m.reddit.com", 40, day=3),
                # X — the substring test matched none of these.
                self._row("t.co", 25, day=4),
                self._row("twitter.com", 15, day=5),
                self._row("x.com", 10, day=6),
                # LinkedIn's own shortener, and the same platform under a second channel.
                self._row("linkedin.com", 100, channel="Organic Social", day=7),
                self._row("lnkd.in", 60, channel="Organic Social", day=8),
                # YouTube's shortener, under Organic Video.
                self._row("youtube.com", 70, channel="Organic Video", day=9),
                self._row("youtu.be", 30, channel="Organic Video", day=10),
                # Domains that merely CONTAIN a platform string.
                self._row("hubspot.com", 500, day=11),
                self._row("blogspot.com", 400, day=12),
                # Paid Social is not off-site: it is bought traffic. The social table used to
                # scan every row with no channel filter, so this leaked into LinkedIn's row and
                # the table could exceed the "off-site sessions" KPI directly above it.
                self._row("linkedin.com", 999, channel="Paid Social", day=13),
            ])

    def _platform_sessions(self, body, platform):
        row = next((r for r in body["social"] if r["platform"] == platform), None)
        self.assertIsNotNone(row, f"no {platform} row in the social table")
        return row["sessions"]

    def test_reddit_traffic_is_not_double_counted_into_x(self):
        body = self._build()
        self.assertEqual(self._platform_sessions(body, "Reddit"), 340)
        # t.co + twitter.com + x.com only.
        self.assertEqual(self._platform_sessions(body, "X / Twitter"), 50)

    def test_platform_shorteners_are_counted(self):
        body = self._build()
        self.assertEqual(self._platform_sessions(body, "LinkedIn"), 160)
        self.assertEqual(self._platform_sessions(body, "YouTube"), 100)

    def test_paid_social_never_reaches_the_social_table_or_the_spotlight(self):
        body = self._build()
        self.assertEqual(self._platform_sessions(body, "LinkedIn"), 160)
        offsite_sessions = body["totals"]["sessions"]
        social_sessions = sum(r["sessions"] for r in body["social"])
        self.assertLessEqual(
            social_sessions, offsite_sessions,
            "the social table reports more sessions than the off-site KPI above it",
        )

    def test_no_session_is_attributed_to_two_platforms(self):
        body = self._build()
        known = {"LinkedIn", "Reddit", "YouTube", "X / Twitter"}
        attributed = sum(r["sessions"] for r in body["social"] if r["platform"] in known)
        # 340 Reddit + 50 X + 160 LinkedIn + 100 YouTube = 650. hubspot.com and
        # blogspot.com are real off-site sessions that belong to no platform, and must
        # not be borrowed by one.
        self.assertEqual(attributed, 650)


class ReferrerSourceMapTests(_AnalyticsDbTestCase):
    """`source_map` used to be a dict comprehension keyed on source and filtered to
    Referral/Social, so Organic Video was dropped entirely and a source appearing under two
    channels silently kept only whichever row the comprehension saw last."""

    def setUp(self):
        super().setUp()
        with get_session() as session:
            session.add_all([
                Backlink(site_id=SITE_ID, referring_domain="youtube.com",
                         target_url="https://fusehealth.com/a", domain_rank=90, dofollow=1),
                Backlink(site_id=SITE_ID, referring_domain="linkedin.com",
                         target_url="https://fusehealth.com/b", domain_rank=95, dofollow=1),
                Backlink(site_id=SITE_ID, referring_domain="nolinkhere.com",
                         target_url="https://fusehealth.com/c", domain_rank=10, dofollow=1),
                # Organic Video — excluded by the old "Referral|Social" filter.
                self._row("youtube.com", 120, channel="Organic Video", day=4,
                          engaged=60, conv=6, rev=12.0),
                # The same source under two channels. GA4 does this routinely.
                self._row("linkedin.com", 200, channel="Organic Social", day=5,
                          engaged=100, conv=10, rev=20.0),
                self._row("linkedin.com", 50, channel="Referral", day=6,
                          engaged=25, conv=2, rev=5.0),
            ])

    def _ref(self, body, domain):
        row = next((r for r in body["referrers"] if r["domain"] == domain), None)
        self.assertIsNotNone(row, f"no referrer row for {domain}")
        return row

    def test_organic_video_sessions_reach_a_referring_domain(self):
        body = self._build()
        self.assertEqual(self._ref(body, "youtube.com")["sessions"], 120)
        self.assertEqual(self._ref(body, "youtube.com")["keyEvents"], 6)

    def test_one_source_under_two_channels_sums_instead_of_last_wins(self):
        body = self._build()
        row = self._ref(body, "linkedin.com")
        self.assertEqual(row["sessions"], 250)
        self.assertEqual(row["keyEvents"], 12)
        self.assertEqual(row["revenue"], 25.0)
        self.assertEqual(row["engagementRate"], 50.0)

    def test_a_domain_ga4_never_measured_reports_zero_sessions_and_no_rate(self):
        """A referring domain is listed because it LINKS to us. Most drive no measured
        sessions — that is a real 0, and an engagement rate over it is undefined, not 0%."""
        body = self._build()
        row = self._ref(body, "nolinkhere.com")
        self.assertEqual(row["sessions"], 0)
        self.assertIsNone(row["engagementRate"])
