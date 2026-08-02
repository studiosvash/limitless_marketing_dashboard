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

    def _seed_real_site(self):
        """2 indexed pages + 1 broken, a PageSpeed row, and a real TechnicalIssue."""
        from pipeline.db.schema import TechnicalIssue
        with get_session() as session:
            session.add_all([
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/a",
                                verdict="PASS", coverage_state="Submitted and indexed",
                                robots_txt_state="ALLOWED"),
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/b",
                                verdict="PASS", coverage_state="Submitted and indexed",
                                robots_txt_state="ALLOWED"),
                IndexingStatus(site_id=self.site_id, url="https://fusehealth.com/gone",
                                verdict="FAIL", coverage_state="Not found (404)",
                                robots_txt_state="ALLOWED"),
                PageSpeed(site_id=self.site_id, url="https://fusehealth.com/a",
                          strategy="mobile", performance_score=80, seo_score=90,
                          accessibility_score=70, best_practices_score=100,
                          lcp_ms=2000.0, cls=0.05, ttfb_ms=400.0),
                TechnicalIssue(site_id=self.site_id, url="https://fusehealth.com/gone",
                                issue_type="not_found_404", severity="high",
                                description="Returns 404"),
            ])

    def test_score_and_crawl_are_real_not_setup_sentinels(self):
        """Regression: score/crawl/catScore used to be hardcoded {"state": "setup"}. The SPA
        gates the WHOLE Site Audit page on data.score.state === 'setup', so the page could
        never render -- even with real IndexingStatus/PageSpeed rows sitting in the DB."""
        from apps.dashboard.services.site_audit_service import build_site_audit_response

        self._seed_real_site()
        response = build_site_audit_response(self.site_id)

        self.assertIsInstance(response["score"], int)
        self.assertNotIsInstance(response["score"], dict)   # never a setup sentinel again
        self.assertGreaterEqual(response["score"], 0)
        self.assertLessEqual(response["score"], 100)

        self.assertEqual(response["crawl"]["pagesCrawled"], 3)
        self.assertEqual(response["crawl"]["status"], "complete")
        self.assertEqual(response["catScore"]["Performance"], 80)   # real Lighthouse score
        self.assertEqual(response["catScore"]["Indexing"], 67)      # 2 of 3 indexed

    def test_real_technical_issues_become_checks_and_totals(self):
        """The real TechnicalIssue rows must surface as checks + totals (they used to be
        dropped entirely: checks was hardcoded [])."""
        from apps.dashboard.services.site_audit_service import build_site_audit_response

        self._seed_real_site()
        response = build_site_audit_response(self.site_id)

        self.assertEqual(len(response["checks"]), 1)
        check = response["checks"][0]
        self.assertEqual(check["id"], "not_found_404")
        self.assertEqual(check["severity"], "error")     # high -> error
        self.assertEqual(check["count"], 1)
        self.assertEqual(check["pages"][0]["url"], "https://fusehealth.com/gone")
        self.assertEqual(response["totals"], {"errors": 1, "warnings": 0, "notices": 0})

        # every indexed page shows up as a real crawled page
        self.assertEqual(len(response["crawledPages"]), 3)
        gone = next(p for p in response["crawledPages"] if p["url"].endswith("/gone"))
        self.assertEqual(gone["statusCode"], 404)
        self.assertEqual(gone["errors"], 1)

    def test_fields_with_no_data_source_stay_honestly_empty(self):
        """Whatever genuinely has no data source must stay empty -- never fabricated."""
        from apps.dashboard.services.site_audit_service import build_site_audit_response

        self._seed_real_site()
        response = build_site_audit_response(self.site_id)

        # The SSL/robots/sitemap probes now run in the sync path (the `domain_checks`
        # connector), not in this GET, and nothing has been synced here -- so there is no
        # stored result to show.
        self.assertEqual(response["domainChecks"], [])
        self.assertEqual(response["snapshots"], [])      # no crawl has been recorded for this site

        # TBT comes from the real PageSpeed.tbt_ms column now. This fixture seeds no value for
        # it, so the honest answer is None. It must NEVER be estimated from a paint-timing
        # spread, and INP must never be substituted -- that is a different metric.
        self.assertIsNone(response["cwv"]["tbt"]["p75"])

        # In-links, internal links and word count come from DataForSEO OnPage's per-page `meta`
        # (inbound_links_count / internal_links_count / plain_text_word_count), stored in
        # PageCrawlMeta. This fixture seeds no crawl meta, so all three must be None.
        #
        # This assertion used to read `p["inLinks"] == 0`, back when nothing measured in-links
        # and the payload hardcoded a zero. That zero WAS the fabrication this test exists to
        # catch: it asserted "we measured zero in-links" when the truth was "we never looked".
        # Zero and unknown are different facts, so the honest value is None.
        for p in response["crawledPages"]:
            self.assertIsNone(p["inLinks"], f"{p['url']} reported in-links with no crawl meta")
            self.assertIsNone(p["internalLinks"])
            self.assertIsNone(p["wordCount"])

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

        # Assert all other fields are still present and correct (honest zeros/empties, and
        # a real score of 0 -- not a crash, not a fabricated default)
        self.assertEqual(response["score"], 0)
        self.assertEqual(response["crawl"]["pagesCrawled"], 0)
        self.assertEqual(response["crawl"]["status"], "never")
        self.assertEqual(response["domainChecks"], [])
        self.assertEqual(response["catScore"]["Performance"], 0)
        self.assertIsNone(response["cwv"]["tbt"]["p75"])
        self.assertEqual(response["checks"], [])
        self.assertEqual(response["totals"], {"errors": 0, "warnings": 0, "notices": 0})
        self.assertEqual(response["crawledPages"], [])
        self.assertEqual(response["structure"], [])
        self.assertEqual(response["snapshots"], [])
