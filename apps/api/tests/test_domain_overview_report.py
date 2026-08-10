"""POST /api/domain-overview/report — the first non-JSON endpoint in apps/api.

The rule under test is the one that matters: a report reads the 24-hour caches and NEVER
triggers a backlink fetch. Three billed API calls are not something a "Download PDF" press
should buy, so the connector classes here raise if they are constructed at all.

The PDF engine is patched in every test rather than depended on: WeasyPrint needs cairo and
pango system libraries, and a test suite that only passes on a machine with them is a test
suite that reports the wrong thing everywhere else. The 501 guard has its own test.
"""
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.api.tests.test_domain_overview import (
    FakeOverviewConnector, RaisingBacklinksConnector, SITE_URL, _OK_PAYLOAD, _bootstrap,
)
from apps.dashboard.services import domain_overview_report_service as report_service
from apps.dashboard.services.domain_overview_service import (
    backlinks_cache_key, keywords_cache_key, CACHE_TTL,
)


class FakePdfEngine:
    """Captures the HTML it was asked to render so the template itself is exercised."""

    last_html = None

    def __init__(self, string="", base_url=None):
        FakePdfEngine.last_html = string

    def write_pdf(self):
        return b"%PDF-1.7 fake"


class DomainOverviewReportTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)
        FakePdfEngine.last_html = None

    def _seed_keyword_cache(self, target="example.com", location="United States"):
        cache.set(keywords_cache_key(target, location), dict(_OK_PAYLOAD), CACHE_TTL)

    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    @patch.object(report_service, "load_pdf_engine", return_value=FakePdfEngine)
    def test_a_report_after_a_lookup_costs_nothing_and_never_buys_backlinks(self, _engine):
        self._seed_keyword_cache()
        resp = self.client_auth.post("/api/domain-overview/report",
                                     {"target": "example.com"}, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertIn("attachment;", resp["Content-Disposition"])
        self.assertIn(".pdf", resp["Content-Disposition"])
        # Nothing was fetched: no Labs call (the cache had it) and no backlinks call ever.
        self.assertEqual(resp["X-Report-Fetched"], "")
        self.assertIn("This report cost nothing", FakePdfEngine.last_html)
        self.assertIn("Backlinks not loaded for this report", FakePdfEngine.last_html)
        # RaisingBacklinksConnector would have raised had anything tried to construct it.

    @patch("pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
           FakeOverviewConnector)
    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    @patch.object(report_service, "load_pdf_engine", return_value=FakePdfEngine)
    def test_an_empty_keyword_cache_buys_exactly_one_labs_call_and_says_so(self, _engine):
        resp = self.client_auth.post("/api/domain-overview/report",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["X-Report-Fetched"], "keywords")
        self.assertEqual(len(FakeOverviewConnector.instances[0].calls), 1)
        self.assertIn("performed one DataForSEO Labs lookup", FakePdfEngine.last_html)

    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    @patch.object(report_service, "load_pdf_engine", return_value=FakePdfEngine)
    def test_a_loaded_backlinks_cache_is_printed_including_the_spam_bands(self, _engine):
        self._seed_keyword_cache()
        cache.set(backlinks_cache_key("example.com"), {
            "state": "ok", "note": "", "cached": False, "target": "example.com",
            "links": [{"referringDomain": "spam.biz", "urlFrom": "https://spam.biz/y",
                       "anchor": "cheap widgets", "dofollow": True, "domainRank": 30,
                       "spamScore": 92, "spamBand": "high"}],
            "anchors": [{"anchor": "example", "type": "Branded", "backlinks": 9,
                         "refDomains": 2, "dofollowPct": 100}],
            "spam": {"targetScore": 71, "highSpamLinks": 1, "mediumSpamLinks": 0,
                     "scoredLinks": 1, "unknownLinks": 0},
            "summary": {"backlinks": 4210, "refDomains": 311},
            "limit": 100, "anchorsLimit": 60, "locationApplies": False,
        }, CACHE_TTL)

        resp = self.client_auth.post("/api/domain-overview/report",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        html = FakePdfEngine.last_html
        self.assertNotIn("Backlinks not loaded", html)
        self.assertIn("band-high", html)
        self.assertIn("spam.biz", html)
        self.assertIn("4,210", html)

    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    @patch.object(report_service, "load_pdf_engine", return_value=None)
    def test_a_missing_pdf_engine_is_a_501_not_a_500(self, _engine):
        self._seed_keyword_cache()
        resp = self.client_auth.post("/api/domain-overview/report",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.status_code, 501)
        self.assertIn("PDF engine not installed", resp.json()["detail"])

    def test_missing_target_is_400(self):
        resp = self.client_auth.post("/api/domain-overview/report", {}, format="json")
        self.assertEqual(resp.status_code, 400)


class ReportContextTests(TestCase):
    """The context builder's honesty rules, without an HTTP round trip."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_long_tables_are_capped_with_a_caption_that_states_the_real_total(self):
        self.assertEqual(report_service._caption(0, 25, "keywords"), "")
        self.assertEqual(report_service._caption(9, 25, "keywords"), "Showing all 9 keywords.")
        self.assertEqual(report_service._caption(4218, 25, "backlinks"),
                         "Showing the top 25 of 4,218 backlinks.")

    def test_prompts_are_free_and_never_claim_an_ai_volume(self):
        rows = report_service._prompt_rows(
            [{"keyword": "widget repair"}, {"keyword": "blue widgets"}], site_id="")
        self.assertTrue(rows["suggested"])
        # run_prompt_research is deterministic template expansion -- no external call, and
        # aiVolume is honestly 0 because no AI-volume data source exists.
        self.assertTrue(all(r.get("aiVolume") == 0 for r in rows["suggested"]))
        self.assertEqual(rows["stored"], [])

    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    def test_an_unloaded_backlinks_section_is_stated_not_silently_dropped(self):
        cache.set(keywords_cache_key("example.com", "United States"), dict(_OK_PAYLOAD), CACHE_TTL)
        ctx = report_service.build_report_context("example.com", "United States")
        self.assertFalse(ctx["backlinks_loaded"])
        self.assertIn("Load backlinks", ctx["backlinks_note"])
        self.assertEqual(ctx["fetched"], [])
