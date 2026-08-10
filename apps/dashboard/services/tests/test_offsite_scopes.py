"""What the Off-site page counts, and what it admits it cannot answer.

Two separate honesty questions live here:

  * `_is_offsite_channel` decides which GA4 channel groups this page is about. It used to be a
    substring test (`"Organic" in ch`), which is not a definition — it silently admitted
    channels nobody meant and excluded ones the substrings happened to miss.
  * The landing-pages section reads `seo_daily`, which has no channel column at all, so it
    cannot be scoped to referral & social no matter how its heading is worded.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, GA4TrafficSourceDaily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_ID = "sc-domain:fusehealth.com"


class OffsiteChannelAllowListTests(TestCase):
    def test_the_three_offsite_channels_are_counted(self):
        from apps.dashboard.services.offsite_service import _is_offsite_channel
        for ch in ("Referral", "Organic Social", "Organic Video"):
            self.assertTrue(_is_offsite_channel(ch), f"{ch} must count as off-site")

    def test_organic_shopping_is_not_offsite(self):
        """The old test was `"Organic" in ch and ch != "Organic Search"`, so GA4's standard
        `Organic Shopping` channel -- a shopping-surface listing, not an earned link -- was
        counted as off-site traffic purely because its name contains the word Organic."""
        from apps.dashboard.services.offsite_service import _is_offsite_channel
        self.assertFalse(_is_offsite_channel("Organic Shopping"))

    def test_on_site_paid_and_unrelated_channels_are_excluded(self):
        from apps.dashboard.services.offsite_service import _is_offsite_channel
        for ch in ("Organic Search", "Paid Search", "Paid Social", "Paid Video", "Direct",
                   "Display", "Cross-network", "Email", "Affiliates", "Audio", "SMS",
                   "Unassigned", "", None):
            self.assertFalse(_is_offsite_channel(ch), f"{ch!r} must not count as off-site")

    def test_the_allow_list_is_the_only_source_of_truth(self):
        from apps.dashboard.services.offsite_service import OFFSITE_CHANNELS, _is_offsite_channel
        for ch in OFFSITE_CHANNELS:
            self.assertTrue(_is_offsite_channel(ch))


class UnknownEngagementRateTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def test_engagement_rate_over_zero_sessions_is_none_not_zero(self):
        """`_engagement` has returned None for an undefined rate since 2026-08, and every other
        rate on this page respects that. The KPI card alone re-coerced it back to 0.0 on the way
        out, so the headline "Engagement rate" printed a confident 0% for a project GA4 has
        never measured -- exactly the claim the None convention exists to avoid."""
        from apps.dashboard.services.offsite_service import query_offsite_totals_raw
        totals = query_offsite_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(totals["sessions"], 0)
        self.assertIsNone(totals["engagementRate"])

    def test_a_measured_rate_still_survives(self):
        from apps.dashboard.services.offsite_service import query_offsite_totals_raw
        with get_session() as session:
            session.add(GA4TrafficSourceDaily(
                site_id=SITE_ID, date=date(2026, 6, 5), channel="Referral", source="a.com",
                sessions=200, engaged_sessions=50, conversions=0, revenue=0.0))
        totals = query_offsite_totals_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(totals["engagementRate"], 25.0)


class LandingPagesAreNotChannelScopedTests(TestCase):
    """`seo_daily` carries no channel dimension, so this list is the site's WHOLE traffic --
    Organic Search and Direct included -- under a heading that used to say "Pages that referral
    & social visitors enter on". And the `landing_page` column is filled from GA4's `pagePath`
    dimension, so its rows are page VIEWS, not entrances."""

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
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 1), sessions=300, pageviews=900,
                         engagement_rate=0.5, conversions=10, landing_page="/a"),
                SEODaily(site_id=SITE_ID, date=date(2026, 6, 1), sessions=100, pageviews=150,
                         engagement_rate=0.3, conversions=5, landing_page="/b"),
            ])

    def test_page_views_are_returned_alongside_sessions(self):
        """screenPageViews is written by every GA4 sync and was read by nothing. It is the
        additive metric at this grain -- sessions are not, because one visit that viewed three
        pages contributes to three rows here."""
        from apps.dashboard.services.offsite_service import query_offsite_landing_pages_raw
        rows = query_offsite_landing_pages_raw(SITE_ID, date(2026, 6, 1), date(2026, 6, 2))
        self.assertEqual({r["url"]: r["pageviews"] for r in rows}, {"/a": 900, "/b": 150})
