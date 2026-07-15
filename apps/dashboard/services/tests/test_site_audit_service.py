import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, IndexingStatus, PageSpeed
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class IndexingBreakdownRawQueryTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.site_id = "sc-domain:fusehealth.com"
        with get_session() as session:
            session.add_all([
                # healthy: PASS verdict, no blocking/redirect/broken signals
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/healthy",
                                verdict="PASS", coverage_state="Submitted and indexed",
                                robots_txt_state="ALLOWED"),
                # withIssues: verdict NEUTRAL, not otherwise categorized
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/with-issues",
                                verdict="NEUTRAL", coverage_state="Crawled - currently not indexed",
                                robots_txt_state="ALLOWED"),
                # broken: coverage_state contains "not found"/"404"
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/broken",
                                verdict="NEUTRAL", coverage_state="Not found (404)",
                                robots_txt_state="ALLOWED"),
                # redirected: coverage_state contains "redirect"
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/redirected",
                                verdict="NEUTRAL", coverage_state="Page with redirect",
                                robots_txt_state="ALLOWED"),
                # blocked: robots_txt_state == DISALLOWED
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/blocked",
                                verdict="FAIL", coverage_state="Blocked by robots.txt",
                                robots_txt_state="DISALLOWED"),
                # priority-order case: PASS verdict + DISALLOWED robots -> still blocked, not healthy
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/blocked-but-pass",
                                verdict="PASS", coverage_state="Submitted and indexed",
                                robots_txt_state="DISALLOWED"),
            ])

    def test_each_bucket_counted_once(self):
        from apps.dashboard.services.site_audit_service import query_indexing_breakdown_raw
        breakdown = query_indexing_breakdown_raw(self.site_id)
        self.assertEqual(breakdown["healthy"], 1)
        self.assertEqual(breakdown["withIssues"], 1)
        self.assertEqual(breakdown["broken"], 1)
        self.assertEqual(breakdown["redirected"], 1)
        # blocked has 2 rows: the plain blocked row + the PASS-but-DISALLOWED priority-order row
        self.assertEqual(breakdown["blocked"], 2)

    def test_priority_order_blocked_beats_healthy(self):
        """A PASS-verdict row that's also robots-blocked must land in `blocked`, not `healthy`,
        because blocked/redirected/broken are checked before the healthy/withIssues split."""
        from apps.dashboard.services.site_audit_service import query_indexing_breakdown_raw
        breakdown = query_indexing_breakdown_raw(self.site_id)
        self.assertEqual(breakdown["healthy"], 1)  # only the genuinely unblocked PASS row
        self.assertGreaterEqual(breakdown["blocked"], 1)

    def test_no_rows_returns_all_zero_buckets(self):
        from apps.dashboard.services.site_audit_service import query_indexing_breakdown_raw
        breakdown = query_indexing_breakdown_raw("sc-domain:no-data.com")
        self.assertEqual(breakdown, {"healthy": 0, "withIssues": 0, "broken": 0,
                                      "redirected": 0, "blocked": 0})

    def test_db_error_returns_zeros_not_crash(self):
        from unittest import mock
        from apps.dashboard.services import site_audit_service
        with mock.patch.object(site_audit_service, "get_session", side_effect=RuntimeError("boom")):
            breakdown = site_audit_service.query_indexing_breakdown_raw(self.site_id)
            self.assertEqual(breakdown, {"healthy": 0, "withIssues": 0, "broken": 0,
                                          "redirected": 0, "blocked": 0})


class CwvRawQueryTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.site_id = "sc-domain:fusehealth.com"
        with get_session() as session:
            session.add_all([
                # mobile rows: lcp seconds -> [2.0, 3.0, 5.0, 2.4]; cls -> [0.05, 0.15, 0.3, 0.08]
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/a", strategy="mobile",
                          lcp_ms=2000, cls=0.05),
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/b", strategy="mobile",
                          lcp_ms=3000, cls=0.15),
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/c", strategy="mobile",
                          lcp_ms=5000, cls=0.3),
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/d", strategy="mobile",
                          lcp_ms=2400, cls=0.08),
                # desktop row: must be excluded from the mobile-only calculation
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/e", strategy="desktop",
                          lcp_ms=100000, cls=5.0),
            ])

    def test_lcp_bucket_counts_and_p75(self):
        from apps.dashboard.services.site_audit_service import query_cwv_raw
        result = query_cwv_raw(self.site_id)
        lcp = result["lcp"]
        self.assertEqual(lcp["good"], 2)   # 2.0s, 2.4s <= 2.5s good threshold
        self.assertEqual(lcp["mid"], 1)    # 3.0s
        self.assertEqual(lcp["poor"], 1)   # 5.0s > 4.0s poor threshold
        self.assertIsNotNone(lcp["p75"])
        self.assertEqual(lcp["p75"], 3.0)
        self.assertEqual(lcp["unit"], "s")
        self.assertEqual(lcp["good_threshold"], 2.5)
        self.assertEqual(lcp["poor_threshold"], 4.0)

    def test_cls_bucket_counts_and_p75(self):
        from apps.dashboard.services.site_audit_service import query_cwv_raw
        result = query_cwv_raw(self.site_id)
        cls = result["cls"]
        self.assertEqual(cls["good"], 2)   # 0.05, 0.08 <= 0.1 good threshold
        self.assertEqual(cls["mid"], 1)    # 0.15
        self.assertEqual(cls["poor"], 1)   # 0.3 > 0.25 poor threshold
        self.assertIsNotNone(cls["p75"])
        self.assertEqual(cls["p75"], 0.15)
        self.assertEqual(cls["unit"], "")
        self.assertEqual(cls["good_threshold"], 0.1)
        self.assertEqual(cls["poor_threshold"], 0.25)

    def test_desktop_rows_excluded(self):
        from apps.dashboard.services.site_audit_service import query_cwv_raw
        result = query_cwv_raw(self.site_id)
        # If the desktop row (lcp_ms=100000 -> 100s, cls=5.0) were included, it would blow
        # past the poor bucket and shift totals/p75. Total sample size must stay at 4.
        total_lcp = result["lcp"]["good"] + result["lcp"]["mid"] + result["lcp"]["poor"]
        total_cls = result["cls"]["good"] + result["cls"]["mid"] + result["cls"]["poor"]
        self.assertEqual(total_lcp, 4)
        self.assertEqual(total_cls, 4)
        self.assertLess(result["lcp"]["p75"], 100)

    def test_empty_data_returns_none_p75_not_fabricated(self):
        from apps.dashboard.services.site_audit_service import query_cwv_raw
        result = query_cwv_raw("sc-domain:no-data.com")
        self.assertEqual(result["lcp"]["p75"], None)
        self.assertEqual(result["lcp"]["good"], 0)
        self.assertEqual(result["lcp"]["mid"], 0)
        self.assertEqual(result["lcp"]["poor"], 0)
        self.assertEqual(result["cls"]["p75"], None)
        self.assertEqual(result["cls"]["good"], 0)
        self.assertEqual(result["cls"]["mid"], 0)
        self.assertEqual(result["cls"]["poor"], 0)
