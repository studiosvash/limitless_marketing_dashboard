"""Which pages the `pagespeed` connector measures, and which it is allowed to skip.

Nothing here touches the network — `_fetch_psi` is patched in the one test that calls `fetch`.

WHY THIS EXISTS. The Site Audit table showed a dash for 27 of a 55-page site's pages, and the
reason was not the dashboard: this connector could never have measured them. Three separate
limits stacked up, none of them visible from the UI:

  1. the sampling pool was `SELECT url FROM pages WHERE clicks > 0`, so a page that had not yet
     earned a Google click was permanently ineligible -- exactly the new/important pages whose
     speed a user most wants to fix;
  2. `limit=15` (lowered from 50 in commit 2718c2b) capped it again;
  3. every page was scanned twice, mobile AND desktop, and NOTHING reads the desktop rows --
     every consumer filters `strategy == "mobile"` (site_audit_service x3, overview_service),
     and test_site_audit_service.test_desktop_rows_excluded asserts they stay out. Half of
     every run's time and quota bought rows no screen has ever displayed.

The rule these tests pin down: eligibility is "the page exists", not "the page already gets
traffic"; clicks decide ORDER, never membership; and when a cap does bite it is loud, because a
silently truncated audit reads as a complete one.
"""
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Page
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_URL = "https://www.fusehealth.com"


class AnalyticsDbTestCase(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)

    def add_pages(self, specs):
        """specs: list of (url, clicks)."""
        with get_session() as session:
            session.add_all([
                Page(site_id=SITE_URL, url=url, clicks=clicks) for url, clicks in specs
            ])


class TopPageSelectionTests(AnalyticsDbTestCase):
    def _select(self, **kwargs):
        from pipeline.connectors.pagespeed import PageSpeedConnector
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            return PageSpeedConnector()._get_top_pages(SITE_URL, **kwargs)

    def test_a_page_with_zero_clicks_is_still_measured(self):
        """The bug in one assertion. A page nobody has clicked yet is not unimportant -- it is
        usually the newest one, and the whole point of a speed audit is to fix it before it has
        to compete. `clicks > 0` made that page permanently unmeasurable."""
        self.add_pages([
            (SITE_URL + "/", 500),
            (SITE_URL + "/brand-new-service-page", 0),
        ])
        self.assertIn(SITE_URL + "/brand-new-service-page", self._select())

    def test_clicks_decide_order_not_membership(self):
        """Traffic still ranks the list, so if the cap ever bites it drops the least-visited
        pages rather than an arbitrary slice -- but it never removes anyone from the list."""
        self.add_pages([
            (SITE_URL + "/quiet", 0),
            (SITE_URL + "/busiest", 900),
            (SITE_URL + "/middling", 40),
        ])
        selected = self._select()
        self.assertEqual(selected[0], SITE_URL + "/busiest")
        self.assertEqual(selected[-1], SITE_URL + "/quiet")
        self.assertEqual(len(selected), 3)

    def test_a_whole_small_site_fits_under_the_cap(self):
        """55 pages is this project's real site. Every one of them must be measurable in a
        single run: 'your main pages must not be skipped' is the requirement."""
        self.add_pages([(SITE_URL + "/p%d" % i, i) for i in range(55)])
        self.assertEqual(len(self._select()), 55)

    def test_truncation_says_so_out_loud(self):
        """A cap that silently drops pages turns a partial audit into one that looks complete.
        When it bites, it must name the number it dropped."""
        self.add_pages([(SITE_URL + "/p%d" % i, i) for i in range(12)])
        with self.assertLogs("fusehealth.pagespeed", level=logging.WARNING) as cm:
            selected = self._select(limit=10)
        self.assertEqual(len(selected), 10)
        self.assertTrue(
            any("12" in m and "10" in m for m in cm.output),
            f"the warning must state how many pages were considered and how many ran: {cm.output}",
        )

    def test_no_pages_at_all_returns_empty_without_error(self):
        self.assertEqual(self._select(), [])


class RotationTests(AnalyticsDbTestCase):
    """Staleness ranks above traffic, so a site larger than one run's budget is covered across
    consecutive runs instead of re-measuring the same head every time.

    Ordering by clicks alone is correct only while the whole site fits in one run. On a
    1 139-page site (premierstaff) a ~200-page budget would re-measure the same top 200 forever
    and the remaining 939 would never get a score — permanently, not just this week. That is the
    same "some pages are structurally ineligible" failure as the old `clicks > 0`, just arrived
    at by a different route. Rotation is also why no content-type filter is needed: excluding
    /blog would still leave 792 pages on that site, so it never solved the scale problem, and it
    would have blinded the audit to 23% of its clicks.
    """

    def _select(self, **kwargs):
        from pipeline.connectors.pagespeed import PageSpeedConnector
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            return PageSpeedConnector()._get_top_pages(SITE_URL, **kwargs)

    def add_scores(self, specs):
        """specs: list of (url, last_checked datetime)."""
        from pipeline.db.schema import PageSpeed
        with get_session() as session:
            session.add_all([
                PageSpeed(site_id=SITE_URL, url=url, strategy="mobile",
                          performance_score=50, last_checked=when)
                for url, when in specs
            ])

    def test_a_never_measured_page_outranks_a_busier_measured_one(self):
        """A newly published page has no score at all; the busiest page already has one that is
        a week old. The page with NO data is the one the next run must not skip."""
        self.add_pages([(SITE_URL + "/busiest", 5000), (SITE_URL + "/brand-new", 0)])
        self.add_scores([(SITE_URL + "/busiest", datetime(2026, 7, 26, 12, 0))])
        self.assertEqual(self._select()[0], SITE_URL + "/brand-new")

    def test_the_stalest_score_is_refreshed_first(self):
        self.add_pages([
            (SITE_URL + "/fresh", 900),
            (SITE_URL + "/stale", 10),
        ])
        self.add_scores([
            (SITE_URL + "/fresh", datetime(2026, 8, 1, 12, 0)),
            (SITE_URL + "/stale", datetime(2026, 5, 1, 12, 0)),
        ])
        self.assertEqual(self._select()[0], SITE_URL + "/stale")

    def test_traffic_still_breaks_ties_among_equally_stale_pages(self):
        """Clicks keep their job — they just rank below staleness now."""
        self.add_pages([(SITE_URL + "/quiet", 1), (SITE_URL + "/busy", 800)])
        self.assertEqual(self._select()[0], SITE_URL + "/busy")

    def test_consecutive_runs_cover_a_site_bigger_than_one_run(self):
        """The property that makes 'no page is ever permanently skipped' true on a large site:
        run 2 must measure what run 1 could not reach, not repeat run 1."""
        self.add_pages([(SITE_URL + "/p%d" % i, 1000 - i) for i in range(10)])

        first = self._select(limit=4)
        # Whatever run 1 measured now carries a timestamp; the rest are still unmeasured.
        self.add_scores([(u, datetime(2026, 8, 2, 12, 0)) for u in first])
        second = self._select(limit=4)

        self.assertEqual(set(first) & set(second), set(),
                         "run 2 re-measured pages run 1 had already done")
        self.assertEqual(len(set(first) | set(second)), 8)


class StrategyTests(AnalyticsDbTestCase):
    def test_only_mobile_is_requested(self):
        """Desktop rows are written by nobody's request and read by nothing. Scanning for them
        doubled every run's wall-clock and quota, which is the budget that was capping page
        coverage in the first place. Google indexes mobile-first; the dashboard reports mobile
        only. If a desktop view is ever built, this test is the place to change."""
        from pipeline.connectors.pagespeed import PageSpeedConnector

        self.add_pages([(SITE_URL + "/a", 10), (SITE_URL + "/b", 5)])
        seen = []

        def fake_psi(url, strategy="mobile"):
            seen.append((url, strategy))
            return {"url": url, "strategy": strategy, "performance_score": 50}

        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            conn = PageSpeedConnector()
            # `_resolve_site` reads the `sites` table / GSC_SITE_URL and is not what is under
            # test here; pinning it keeps this test about strategy selection only.
            with patch.object(conn, "_resolve_site", return_value=SITE_URL), \
                 patch.object(conn, "_fetch_psi", side_effect=fake_psi), \
                 patch("time.sleep"):
                records = conn.fetch(site_id=SITE_URL)

        self.assertEqual({s for _, s in seen}, {"mobile"},
                         "desktop scans are pure waste until something reads them")
        self.assertEqual(len(seen), 2, "one request per page, not two")
        self.assertEqual(len(records), 2)

    def test_pages_dropped_by_the_time_budget_are_reported(self):
        """The connector cannot be allowed to run the whole sync past RUN_TIMEOUT just because
        PSI is slow (apps/sync/scheduling.py sizes the 2h reaper from these limits). It stops on
        a wall clock rather than on a page count -- and says how many pages it never reached, so
        the gap is visible instead of looking like those pages were fine."""
        from pipeline.connectors import pagespeed as ps_mod
        from pipeline.connectors.pagespeed import PageSpeedConnector

        self.add_pages([(SITE_URL + "/p%d" % i, 100 - i) for i in range(6)])

        clock = {"t": 0.0}

        def fake_monotonic():
            clock["t"] += 100.0          # every call advances 100s
            return clock["t"]

        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            conn = PageSpeedConnector()
            with patch.object(conn, "_resolve_site", return_value=SITE_URL), \
                 patch.object(conn, "_fetch_psi",
                              side_effect=lambda url, strategy="mobile": {"url": url}), \
                 patch("time.sleep"), \
                 patch.object(ps_mod.time, "monotonic", side_effect=fake_monotonic), \
                 patch.object(ps_mod, "RUN_BUDGET_SECONDS", 250):
                with self.assertLogs("fusehealth.pagespeed", level=logging.WARNING) as cm:
                    records = conn.fetch(site_id=SITE_URL)

        self.assertLess(len(records), 6, "the budget must actually stop the loop")
        self.assertTrue(
            any("budget" in m.lower() for m in cm.output),
            f"stopping early must be logged: {cm.output}",
        )
