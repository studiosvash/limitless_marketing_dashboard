"""The AI Questions block: opt-in, cached, and never bought by the report.

Same contract the backlink sections established — a section that costs money gets its own
button, its own 24h cache, and is invisible to the default Analyze press.
"""
from unittest import mock

from django.core.cache import cache
# TestCase, not SimpleTestCase: `ensure_budget()` reads BudgetState, and under SimpleTestCase
# that read raises, the gate fails open by design, and every test here would pass without ever
# exercising the gate it sits behind.
from django.test import TestCase

from apps.dashboard.services import domain_overview_service as svc

ROWS = [
    {"question": "how many bartenders for 50 guests?", "answer": "...", "platform": "chat_gpt",
     "model_name": "gpt-5-5", "our_url": "https://premierstaff.com/blog/x",
     "cited": True, "retrieved": False, "ai_search_volume": 82, "monthly_searches": {},
     "first_response_at": None, "last_response_at": None, "fan_out_queries": [],
     "cited_domains": ["premierstaff.com"]},
    {"question": "who staffs events?", "answer": "...", "platform": "google",
     "model_name": "", "our_url": "https://premierstaff.com/services",
     "cited": False, "retrieved": True, "ai_search_volume": 10, "monthly_searches": {},
     "first_response_at": None, "last_response_at": None, "fan_out_queries": [],
     "cited_domains": ["rival.com"]},
]

OK = {"status": "ok", "rows": ROWS, "total": 2, "domain": "premierstaff.com", "page": None,
      "platforms": ["chat_gpt", "google"], "partial": None, "cost": 0.36}


class QuestionsBlockTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_cited_and_seen_are_counted_separately(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=OK):
            block = svc.fetch_questions_block("premierstaff.com")
        self.assertEqual(block["state"], "ok")
        self.assertEqual(block["citedCount"], 1)
        self.assertEqual(block["seenCount"], 1)

    def test_a_second_press_is_served_from_cache_and_buys_nothing(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=OK) as fetch:
            svc.fetch_questions_block("premierstaff.com")
            again = svc.fetch_questions_block("premierstaff.com")
        self.assertEqual(fetch.call_count, 1)
        self.assertTrue(again["cached"])

    def test_a_page_and_its_domain_do_not_share_a_cache_entry(self):
        """The page filter changes the answer, so one must not serve the other."""
        self.assertNotEqual(svc.questions_cache_key("premierstaff.com"),
                            svc.questions_cache_key("premierstaff.com/blog/x"))

    def test_the_report_path_never_fetches(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as fetch:
            block = svc.fetch_questions_block("premierstaff.com", allow_fetch=False)
        fetch.assert_not_called()
        self.assertEqual(block["state"], "not_loaded")

    def test_the_report_path_reads_what_the_user_already_bought(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=OK):
            svc.fetch_questions_block("premierstaff.com")
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as fetch:
            block = svc.fetch_questions_block("premierstaff.com", allow_fetch=False)
        fetch.assert_not_called()
        self.assertEqual(block["total"], 2)

    def test_the_budget_gate_refuses_before_spending(self):
        with mock.patch("pipeline.connectors.dataforseo_cost.ensure_budget",
                        return_value={"error": "Monthly DataForSEO budget reached"}), \
             mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as fetch:
            block = svc.fetch_questions_block("premierstaff.com")
        fetch.assert_not_called()
        self.assertEqual(block["state"], "budget")

    def test_no_questions_found_is_an_honest_empty_not_an_error(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value={**OK, "rows": [], "total": 0}):
            block = svc.fetch_questions_block("premierstaff.com")
        self.assertEqual(block["state"], "empty")
        self.assertIn("no AI answers on record", block["note"])

    def test_missing_credentials_report_setup_rather_than_zero_questions(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value={"status": "setup", "rows": [], "total": 0, "cost": 0.0,
                                      "error": "DataForSEO credentials are not configured."}):
            block = svc.fetch_questions_block("premierstaff.com")
        self.assertEqual(block["state"], "setup")

    def test_the_default_analyze_press_does_not_buy_questions(self):
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **kw: r), \
             mock.patch.object(svc, "fetch_questions_block") as questions:
            out = svc.run_domain_overview("premierstaff.com")
        questions.assert_not_called()
        self.assertNotIn("questions", out)

    def test_include_questions_adds_the_block(self):
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **kw: r), \
             mock.patch.object(svc, "fetch_questions_block",
                               return_value={"state": "ok", "rows": ROWS}) as questions:
            out = svc.run_domain_overview("premierstaff.com", include=["questions"])
        questions.assert_called_once()
        self.assertEqual(out["questions"]["state"], "ok")
