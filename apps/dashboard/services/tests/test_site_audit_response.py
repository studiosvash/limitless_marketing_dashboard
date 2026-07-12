import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, IndexingStatus, PageSpeed
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class BuildSiteAuditResponseTests(TestCase):
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

    def test_with_real_data_assembles_response_correctly(self):
        """Seed real IndexingStatus/PageSpeed rows, call build_site_audit_response,
        assert breakdown and cwv fields match the raw calculators' output reshaped correctly."""
        from apps.dashboard.services.site_audit_service import build_site_audit_response

        with get_session() as session:
            session.add_all([
                # IndexingStatus for breakdown test
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/healthy",
                                verdict="PASS", coverage_state="Submitted and indexed",
                                robots_txt_state="ALLOWED"),
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/with-issues",
                                verdict="NEUTRAL", coverage_state="Crawled - currently not indexed",
                                robots_txt_state="ALLOWED"),
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/broken",
                                verdict="NEUTRAL", coverage_state="Not found (404)",
                                robots_txt_state="ALLOWED"),
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/redirected",
                                verdict="NEUTRAL", coverage_state="Page with redirect",
                                robots_txt_state="ALLOWED"),
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/blocked",
                                verdict="FAIL", coverage_state="Blocked by robots.txt",
                                robots_txt_state="DISALLOWED"),
                # PageSpeed for cwv test (mobile strategy only)
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/a", strategy="mobile",
                          lcp_ms=2000, cls=0.05),
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/b", strategy="mobile",
                          lcp_ms=3000, cls=0.15),
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/c", strategy="mobile",
                          lcp_ms=5000, cls=0.3),
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/d", strategy="mobile",
                          lcp_ms=2400, cls=0.08),
            ])

        response = build_site_audit_response(self.site_id)

        # Assert breakdown matches expected values (1 healthy, 1 withIssues, 1 broken, 1 redirected, 1 blocked)
        self.assertEqual(response["breakdown"]["healthy"], 1)
        self.assertEqual(response["breakdown"]["withIssues"], 1)
        self.assertEqual(response["breakdown"]["broken"], 1)
        self.assertEqual(response["breakdown"]["redirected"], 1)
        self.assertEqual(response["breakdown"]["blocked"], 1)

        # Assert cwv.lcp is reshaped correctly from raw data
        lcp = response["cwv"]["lcp"]
        self.assertEqual(lcp["p75"], 3.0)  # p75 of [2.0, 2.4, 3.0, 5.0] is 3.0
        self.assertEqual(lcp["unit"], "s")
        self.assertEqual(lcp["good"], 2.5)
        self.assertEqual(lcp["poor"], 4.0)
        self.assertEqual(lcp["buckets"]["good"], 2)   # 2.0s, 2.4s
        self.assertEqual(lcp["buckets"]["mid"], 1)    # 3.0s
        self.assertEqual(lcp["buckets"]["poor"], 1)   # 5.0s

        # Assert cwv.cls is reshaped correctly from raw data
        cls = response["cwv"]["cls"]
        self.assertEqual(cls["p75"], 0.15)  # p75 of [0.05, 0.08, 0.15, 0.3] is 0.15
        self.assertEqual(cls["unit"], "")
        self.assertEqual(cls["good"], 0.1)
        self.assertEqual(cls["poor"], 0.25)
        self.assertEqual(cls["buckets"]["good"], 2)   # 0.05, 0.08
        self.assertEqual(cls["buckets"]["mid"], 1)    # 0.15
        self.assertEqual(cls["buckets"]["poor"], 1)   # 0.3

    def test_all_setup_state_fields_present_and_honest(self):
        """Assert every state:"setup" field is exactly as specified (no fabrication)."""
        from apps.dashboard.services.site_audit_service import build_site_audit_response

        response = build_site_audit_response(self.site_id)

        # Exact-equality assertions for every setup field
        self.assertEqual(response["score"], {"state": "setup"})
        self.assertEqual(response["crawl"], {"state": "setup"})
        self.assertEqual(response["catScore"], {"state": "setup"})
        self.assertEqual(response["cwv"]["tbt"], {"state": "setup"})
        self.assertEqual(response["domainChecks"], [])
        self.assertEqual(response["checks"], [])
        self.assertEqual(response["totals"], {"errors": 0, "warnings": 0, "notices": 0})
        self.assertEqual(response["crawledPages"], [])
        self.assertEqual(response["structure"], [])
        self.assertEqual(response["snapshots"], [])

    def test_empty_db_returns_zeros_and_none_p75_not_crash(self):
        """Empty-DB case (no IndexingStatus/PageSpeed rows at all): assert breakdown is all zeros
        and cwv.lcp.p75/cwv.cls.p75 are None, not a crash or a fabricated default."""
        from apps.dashboard.services.site_audit_service import build_site_audit_response

        response = build_site_audit_response("sc-domain:no-data.com")

        # Assert breakdown is all zeros
        self.assertEqual(response["breakdown"]["healthy"], 0)
        self.assertEqual(response["breakdown"]["withIssues"], 0)
        self.assertEqual(response["breakdown"]["broken"], 0)
        self.assertEqual(response["breakdown"]["redirected"], 0)
        self.assertEqual(response["breakdown"]["blocked"], 0)

        # Assert cwv p75 values are None, not fabricated
        self.assertIsNone(response["cwv"]["lcp"]["p75"])
        self.assertIsNone(response["cwv"]["cls"]["p75"])

        # Assert cwv bucket counts are zero
        self.assertEqual(response["cwv"]["lcp"]["buckets"]["good"], 0)
        self.assertEqual(response["cwv"]["lcp"]["buckets"]["mid"], 0)
        self.assertEqual(response["cwv"]["lcp"]["buckets"]["poor"], 0)
        self.assertEqual(response["cwv"]["cls"]["buckets"]["good"], 0)
        self.assertEqual(response["cwv"]["cls"]["buckets"]["mid"], 0)
        self.assertEqual(response["cwv"]["cls"]["buckets"]["poor"], 0)

        # Assert all other fields are still present and correct
        self.assertEqual(response["score"], {"state": "setup"})
        self.assertEqual(response["crawl"], {"state": "setup"})
        self.assertEqual(response["domainChecks"], [])
        self.assertEqual(response["catScore"], {"state": "setup"})
        self.assertEqual(response["cwv"]["tbt"], {"state": "setup"})
        self.assertEqual(response["checks"], [])
        self.assertEqual(response["totals"], {"errors": 0, "warnings": 0, "notices": 0})
        self.assertEqual(response["crawledPages"], [])
        self.assertEqual(response["structure"], [])
        self.assertEqual(response["snapshots"], [])
