"""`seo_daily_totals` is what every headline KPI reads, so what it must never do is what the
old code did: derive a window's CTR and average position by averaging per-day values.

Both are ratios. Averaging them unweighted lets a quiet Sunday count as much as a Tuesday
with fifty times the impressions, which is how the dashboard came to disagree with Search
Console even on days it had synced completely.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from apps.dashboard.services.overview_service import get_kpi_raw, query_gsc_totals
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, SEODailyTotal
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE = "example.com"


def _total(day, clicks, impressions, position):
    return SEODailyTotal(date=day, site_id=SITE, clicks=clicks, impressions=impressions,
                         ctr=(clicks / impressions) if impressions else 0.0,
                         avg_position=position)


class AnalyticsDBTestCase(TestCase):
    """A private analytics database per test. Django's transaction rollback covers the ORM
    connection only — the SQLAlchemy session these services use is outside it, so without
    this every test would inherit the previous one's rows."""

    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)


class QueryGscTotalsTests(AnalyticsDBTestCase):
    def _seed(self, *rows):
        with get_session() as session:
            for r in rows:
                session.add(r)
            session.commit()

    def test_ctr_is_total_clicks_over_total_impressions_not_a_mean_of_daily_ctrs(self):
        # Day one: 1 click in 10 impressions -> 10%. Day two: 9 clicks in 9,990 -> 0.09%.
        # The mean of the two daily CTRs is ~5%; the real CTR is 10/10,000 = 0.1%.
        self._seed(
            _total(date(2026, 5, 1), clicks=1, impressions=10, position=5.0),
            _total(date(2026, 5, 2), clicks=9, impressions=9_990, position=5.0),
        )
        with get_session() as session:
            got = query_gsc_totals(session, SITE, date(2026, 5, 1), date(2026, 5, 2))

        self.assertEqual(got["clicks"], 10)
        self.assertEqual(got["impressions"], 10_000)
        self.assertAlmostEqual(got["ctr"], 0.001, places=6)

    def test_position_is_impression_weighted(self):
        # 100 impressions at position 90, 9,900 at position 3. The unweighted mean is 46.5;
        # weighted by impressions it is 3.87 — which is what Search Console reports.
        self._seed(
            _total(date(2026, 5, 1), clicks=0, impressions=100, position=90.0),
            _total(date(2026, 5, 2), clicks=0, impressions=9_900, position=3.0),
        )
        with get_session() as session:
            got = query_gsc_totals(session, SITE, date(2026, 5, 1), date(2026, 5, 2))

        self.assertAlmostEqual(got["avg_position"], (100 * 90.0 + 9_900 * 3.0) / 10_000, places=6)

    def test_window_excludes_days_outside_it(self):
        self._seed(
            _total(date(2026, 4, 30), clicks=500, impressions=1_000, position=1.0),
            _total(date(2026, 5, 1), clicks=7, impressions=100, position=2.0),
        )
        with get_session() as session:
            got = query_gsc_totals(session, SITE, date(2026, 5, 1), date(2026, 5, 31))

        self.assertEqual(got["clicks"], 7)

    def test_empty_window_reports_not_found_rather_than_a_real_zero(self):
        with get_session() as session:
            got = query_gsc_totals(session, SITE, date(2026, 5, 1), date(2026, 5, 31))

        self.assertFalse(got["found"])
        self.assertEqual(got["clicks"], 0)


class GetKpiRawSourceTests(AnalyticsDBTestCase):
    """The headline KPIs must read the totals, not the (date, country, device, page)
    breakdown — Google withholds sub-threshold rows from the breakdown, so summing it
    undercounts what Search Console reports."""

    def _seed_breakdown(self, day, clicks, impressions, position):
        with get_session() as session:
            session.add(SEODaily(date=day, site_id=SITE, country="USA", device="mobile",
                                 landing_page=f"https://{SITE}/", clicks=clicks,
                                 impressions=impressions,
                                 ctr=(clicks / impressions) if impressions else 0.0,
                                 avg_position=position))
            session.commit()

    def test_totals_win_over_the_breakdown_for_the_same_day(self):
        day = date(2026, 5, 10)
        self._seed_breakdown(day, clicks=55, impressions=9_921, position=34.0)
        with get_session() as session:
            session.add(_total(day, clicks=135, impressions=12_761, position=24.0))
            session.commit()

        curr, _ = get_kpi_raw(SITE, day, day, date(2026, 5, 1), date(2026, 5, 1))

        self.assertEqual(curr["clicks"], 135)
        self.assertEqual(curr["impressions"], 12_761)
        self.assertAlmostEqual(curr["avg_position"], 24.0, places=6)

    def test_falls_back_to_the_breakdown_when_no_totals_exist(self):
        """A site synced before the totals table existed still renders rather than showing a
        zero that would read as 'no traffic'."""
        day = date(2026, 5, 10)
        self._seed_breakdown(day, clicks=55, impressions=9_921, position=34.0)

        curr, _ = get_kpi_raw(SITE, day, day, date(2026, 5, 1), date(2026, 5, 1))

        self.assertEqual(curr["clicks"], 55)
        self.assertAlmostEqual(curr["ctr"], 55 / 9_921, places=6)

    def test_never_compares_totals_against_the_breakdown(self):
        """The 2361.6% bug: the current period read the totals while the comparison period,
        having none, fell through to the breakdown. A complete figure measured against a
        41%-of-reality one reads as explosive growth on a site that has not moved."""
        curr_day, prev_day = date(2026, 5, 10), date(2026, 4, 10)
        # Both periods have breakdown rows; only the current one has totals.
        self._seed_breakdown(curr_day, clicks=437, impressions=50_000, position=25.5)
        self._seed_breakdown(prev_day, clicks=430, impressions=49_000, position=25.6)
        with get_session() as session:
            session.add(_total(curr_day, clicks=10_757, impressions=1_100_000, position=19.8))
            session.commit()

        curr, prev = get_kpi_raw(SITE, curr_day, curr_day, prev_day, prev_day)

        self.assertEqual(curr["clicks"], 10_757)
        # Not 437. An absent baseline must read as "unknown", not as a number from the
        # other table that would manufacture a +2361% delta.
        self.assertEqual(prev.get("clicks", 0), 0)

    def test_uses_the_breakdown_for_both_when_no_totals_exist_at_all(self):
        """Consistency cuts the other way too: with no totals anywhere, both periods come
        from the breakdown, so the delta between them is still meaningful."""
        curr_day, prev_day = date(2026, 5, 10), date(2026, 4, 10)
        self._seed_breakdown(curr_day, clicks=200, impressions=10_000, position=20.0)
        self._seed_breakdown(prev_day, clicks=100, impressions=9_000, position=22.0)

        curr, prev = get_kpi_raw(SITE, curr_day, curr_day, prev_day, prev_day)

        self.assertEqual(curr["clicks"], 200)
        self.assertEqual(prev["clicks"], 100)

    def test_fallback_position_is_impression_weighted_across_breakdown_rows(self):
        day = date(2026, 5, 10)
        self._seed_breakdown(day, clicks=0, impressions=100, position=90.0)
        with get_session() as session:
            session.add(SEODaily(date=day, site_id=SITE, country="GBR", device="desktop",
                                 landing_page=f"https://{SITE}/b", clicks=0,
                                 impressions=9_900, ctr=0.0, avg_position=3.0))
            session.commit()

        curr, _ = get_kpi_raw(SITE, day, day, date(2026, 5, 1), date(2026, 5, 1))

        self.assertAlmostEqual(curr["avg_position"], (100 * 90.0 + 9_900 * 3.0) / 10_000, places=6)
