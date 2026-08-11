"""POST /api/domain-overview/report — the first non-JSON endpoint in apps/api.

The rule under test is the one that matters: a report reads the 24-hour caches and NEVER
triggers a backlink fetch. Three billed API calls are not something a "Download PDF" press
should buy, so the connector classes here raise if they are constructed at all.

The engine is patched in the HTTP tests rather than depended on, so they assert what the
TEMPLATE says regardless of which engines happen to be installed. But a fixture never
touches a real renderer, so `RealPdfEngineTests` drives the actual resolver end to end --
that is the only test that can catch "the engine we ship cannot render our own template",
which is exactly how this endpoint spent its whole life answering 501.
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
    """Captures the HTML it was asked to render so the template itself is exercised.

    Shaped as `load_pdf_renderer`'s return value -- `(render_fn, engine_name)` -- not as
    WeasyPrint's HTML class, which is what it imitated before the fallback engine landed.
    """

    last_html = None

    @classmethod
    def as_renderer(cls, engine="weasyprint"):
        def render(html):
            cls.last_html = html
            return b"%PDF-1.7 fake"
        return (render, engine)


class DomainOverviewReportTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)
        FakePdfEngine.last_html = None

    def _seed_keyword_cache(self, target="example.com", location="United States"):
        cache.set(keywords_cache_key(target, location), dict(_OK_PAYLOAD), CACHE_TTL)

    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    @patch.object(report_service, "load_pdf_renderer",
           side_effect=lambda: FakePdfEngine.as_renderer())
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
    @patch.object(report_service, "load_pdf_renderer",
           side_effect=lambda: FakePdfEngine.as_renderer())
    def test_an_empty_keyword_cache_buys_exactly_one_labs_call_and_says_so(self, _engine):
        resp = self.client_auth.post("/api/domain-overview/report",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["X-Report-Fetched"], "keywords")
        self.assertEqual(len(FakeOverviewConnector.instances[0].calls), 1)
        self.assertIn("performed one DataForSEO Labs lookup", FakePdfEngine.last_html)

    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    @patch.object(report_service, "load_pdf_renderer",
           side_effect=lambda: FakePdfEngine.as_renderer())
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
    @patch.object(report_service, "load_pdf_renderer", return_value=None)
    def test_a_missing_pdf_engine_is_a_501_not_a_500(self, _engine):
        self._seed_keyword_cache()
        resp = self.client_auth.post("/api/domain-overview/report",
                                     {"target": "example.com"}, format="json")
        self.assertEqual(resp.status_code, 501)
        self.assertIn("No PDF engine is available", resp.json()["detail"])

    def test_missing_target_is_400(self):
        resp = self.client_auth.post("/api/domain-overview/report", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    @patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
           RaisingBacklinksConnector)
    @patch.object(report_service, "load_pdf_renderer",
           side_effect=lambda: FakePdfEngine.as_renderer())
    def test_the_template_prints_no_django_comment_text(self, _engine):
        """Regression: {# … #} is SINGLE-LINE in Django.

        Two multi-line ones sat in this template, so their explanatory prose was rendered as
        visible paragraphs in every PDF the endpoint ever produced. Asserted on the rendered
        HTML rather than by eye because nothing else would ever have noticed.
        """
        self._seed_keyword_cache()
        self.client_auth.post("/api/domain-overview/report",
                              {"target": "example.com"}, format="json")
        html = FakePdfEngine.last_html
        self.assertNotIn("{#", html)
        self.assertNotIn("#}", html)
        self.assertNotIn("Stated first", html)
        self.assertNotIn("three billed API calls are not something", html)


class PdfEngineResolutionTests(TestCase):
    """`load_pdf_renderer` picks the best AVAILABLE engine and never raises for a missing one."""

    def test_the_first_working_engine_wins_and_its_name_comes_back(self):
        def bad():
            raise OSError("no cairo here")   # exactly WeasyPrint's real failure mode

        def good():
            return lambda html: b"%PDF-x"

        with patch.object(report_service, "PDF_ENGINES",
                          (("weasyprint", bad), ("xhtml2pdf", good))):
            render, name = report_service.load_pdf_renderer()
        # WeasyPrint is preferred but unusable, so the fallback is selected -- and named, so
        # the template can branch on it.
        self.assertEqual(name, "xhtml2pdf")
        self.assertEqual(render("<p>x</p>"), b"%PDF-x")

    def test_no_usable_engine_returns_none_rather_than_raising(self):
        def bad():
            raise ImportError("nothing installed")

        with patch.object(report_service, "PDF_ENGINES",
                          (("weasyprint", bad), ("xhtml2pdf", bad))):
            self.assertIsNone(report_service.load_pdf_renderer())

    def test_xhtml2pdf_escalates_a_failed_render_instead_of_returning_broken_bytes(self):
        """pisa.CreatePDF returns an error COUNT; it does not raise.

        Handing those bytes back would download a truncated file that looks like a PDF,
        which is the "fabricated shape" failure this codebase refuses. It must raise.
        """
        render = report_service._xhtml2pdf_renderer()
        with patch("xhtml2pdf.pisa.CreatePDF", return_value=type("R", (), {"err": 3})()):
            with self.assertRaises(RuntimeError):
                render("<p>x</p>")


class RealPdfEngineTests(TestCase):
    """Drives the ACTUAL resolver and the ACTUAL template — no fake renderer anywhere.

    Every other test here hands the service a fake, and a fake never touches a real engine.
    That is precisely why "the shipped engine cannot parse our own stylesheet" survived: the
    suite was green while the endpoint answered 501 on every deployment. xhtml2pdf's CSS
    parser genuinely RAISES on WeasyPrint's @bottom-center margin box, so without this test
    the engine branch in the template could be deleted and nothing would go red.
    """

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_an_engine_is_available_and_renders_the_real_template_to_real_pdf_bytes(self):
        from django.template.loader import render_to_string

        loaded = report_service.load_pdf_renderer()
        self.assertIsNotNone(
            loaded, "requirements.txt ships xhtml2pdf, so an engine must always resolve")
        render, engine = loaded

        cache.set(keywords_cache_key("example.com", "United States"),
                  dict(_OK_PAYLOAD), CACHE_TTL)
        with patch("pipeline.connectors.dataforseo_backlinks.DataForSEOBacklinksConnector",
                   RaisingBacklinksConnector):
            ctx = report_service.build_report_context("example.com", "United States",
                                                      engine=engine)
        pdf = render(render_to_string("reports/domain_overview.html", ctx))

        self.assertTrue(pdf.startswith(b"%PDF-"), "engine did not produce a PDF")
        self.assertGreater(len(pdf), 1000, "a PDF this small rendered nothing")


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
