"""A page target must be tried both with and without its trailing slash.

Reported live: analysing https://premierstaff.com/blog/6-steps-to-calculate-wedding-bartender-cost
returned an empty Overview and an empty Keywords table. Verified against the real API rather
than guessed:

    .../6-steps-to-calculate-wedding-bartender-cost   -> total_count: null, items: []
    .../6-steps-to-calculate-wedding-bartender-cost/  -> total_count: 46, items: [...]

DataForSEO Labs matches a page target EXACTLY, and that page canonicalises with a trailing
slash. A human pasting a URL out of a browser bar routinely drops it, so "no data for this
page" was being reported for a page with 46 ranked keywords, one of them at position 2.

The retry costs a call only in the case that already produced a useless answer, and only for
a PAGE target — a bare domain has nothing to toggle.
"""
from unittest import mock

from django.test import SimpleTestCase

from pipeline.connectors.dataforseo_domain_overview import slash_variants


class SlashVariantTests(SimpleTestCase):
    def test_a_page_without_a_slash_offers_the_slashed_form_second(self):
        self.assertEqual(slash_variants("https://premierstaff.com/blog/x"),
                         ["https://premierstaff.com/blog/x",
                          "https://premierstaff.com/blog/x/"])

    def test_a_page_with_a_slash_offers_the_bare_form_second(self):
        self.assertEqual(slash_variants("https://premierstaff.com/blog/x/"),
                         ["https://premierstaff.com/blog/x/",
                          "https://premierstaff.com/blog/x"])

    def test_a_bare_domain_has_nothing_to_retry(self):
        """Nothing to toggle, and a second call would be pure waste."""
        self.assertEqual(slash_variants("premierstaff.com"), ["premierstaff.com"])

    def test_a_domain_with_only_a_root_slash_has_nothing_to_retry(self):
        self.assertEqual(slash_variants("https://premierstaff.com/"),
                         ["https://premierstaff.com/"])

    def test_a_query_string_is_left_alone(self):
        """Toggling a slash before a query would produce a URL that matches nothing at all."""
        self.assertEqual(slash_variants("https://premierstaff.com/blog/x?utm=1"),
                         ["https://premierstaff.com/blog/x?utm=1"])


class RetryTests(SimpleTestCase):
    """The connector retries once, and only when the first form found nothing."""

    def setUp(self):
        patcher = mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l",
                                                 "DATAFORSEO_PASSWORD": "p"})
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def _envelope(items, total=None):
        return {"tasks": [{"status_code": 20000, "result": [
            {"total_count": total, "items": items,
             "metrics": {"organic": {"count": total or 0}}}]}]}

    def _run(self, responses):
        from pipeline.connectors.dataforseo_domain_overview import DataForSEODomainOverviewConnector
        conn = DataForSEODomainOverviewConnector.__new__(DataForSEODomainOverviewConnector)
        conn.login, conn.password = "l", "p"
        conn.auth = ("l", "p")
        import logging
        conn.logger = logging.getLogger("test")
        with mock.patch("pipeline.connectors.dataforseo_domain_overview.requests.post") as post:
            post.side_effect = [mock.Mock(raise_for_status=mock.Mock(return_value=None),
                                          json=mock.Mock(return_value=r)) for r in responses]
            out = conn.get_domain_overview("https://premierstaff.com/blog/x")
            targets = [c.kwargs["json"][0]["target"] for c in post.call_args_list]
        return out, targets

    def test_an_empty_first_answer_triggers_the_slashed_retry(self):
        out, targets = self._run([self._envelope([]), self._envelope([{"keyword_data": {}}], 46)])
        self.assertEqual(targets, ["https://premierstaff.com/blog/x",
                                   "https://premierstaff.com/blog/x/"])
        self.assertEqual(len(out["keywords"]), 1)

    def test_a_non_empty_first_answer_does_not_retry(self):
        """The retry exists for the empty case; paying for a second call otherwise is waste."""
        out, targets = self._run([self._envelope([{"keyword_data": {}}], 12)])
        self.assertEqual(len(targets), 1)

    def test_both_forms_empty_reports_an_honest_empty(self):
        out, targets = self._run([self._envelope([]), self._envelope([])])
        self.assertEqual(len(targets), 2)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["keywords"], [])
