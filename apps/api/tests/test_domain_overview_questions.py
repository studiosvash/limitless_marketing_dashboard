"""The AI Questions block: opt-in, cached, and never bought by the report.

Same contract the backlink sections established — a section that costs money gets its own
button, its own 24h cache, and is invisible to the default Analyze press.
"""
import tempfile
from pathlib import Path
from unittest import mock

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db

from django.core.cache import cache
from django.test import override_settings
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
        # The analytics-DB fixture is REQUIRED here now, and was not before: these blocks are
        # persisted to `domain_lookups`, so without it every test wrote into the developer's
        # real data/fusehealth.db and the stored rows leaked between tests — and between runs.
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None

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

    def test_every_page_on_a_domain_shares_one_cache_entry(self):
        """THE cost decision on this tab, pinned.

        The request can only ask for a domain, so one call already answers for every page on
        it. Keying the cache per URL would re-buy the same domain for each page checked — ten
        blog posts on one competitor would be ten calls at $0.10 base apiece.
        """
        self.assertEqual(svc.questions_cache_key("premierstaff.com"),
                         svc.questions_cache_key("https://premierstaff.com/blog/x"))

    def test_a_second_page_on_a_looked_up_domain_costs_nothing(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=OK) as fetch:
            svc.fetch_questions_block("premierstaff.com/blog/x")
            svc.fetch_questions_block("premierstaff.com/services")
        self.assertEqual(fetch.call_count, 1, "the domain was already bought")

    def test_a_page_lookup_returns_only_that_page_s_questions(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=OK):
            block = svc.fetch_questions_block("https://premierstaff.com/blog/x")
        self.assertEqual(block["total"], 1)
        self.assertEqual(block["rows"][0]["our_url"], "https://premierstaff.com/blog/x")
        self.assertEqual(block["page"], "https://premierstaff.com/blog/x")

    def test_a_page_with_no_questions_says_so_without_denying_the_domain_s(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=OK):
            block = svc.fetch_questions_block("premierstaff.com/nothing-here")
        self.assertEqual(block["state"], "empty")
        self.assertEqual(block["domainTotal"], 2)
        self.assertIn("2 question(s) reference the domain", block["note"])

    def test_only_one_platform_is_bought_by_default(self):
        """Two platforms means two $0.10 base fees for a second opinion."""
        self.assertEqual(svc.QUESTIONS_PLATFORMS, ("chat_gpt",))

    def test_the_fetch_asks_for_the_whole_domain_not_the_page(self):
        """Filtering happens on read; fetching pre-filtered would waste the other pages."""
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=OK) as fetch:
            svc.fetch_questions_block("https://premierstaff.com/blog/x")
        self.assertEqual(fetch.call_args.kwargs["page_url"], "")

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
        """The guarantee is that Analyze cannot SPEND on questions — not that the block is
        never consulted.

        Since blocks already owned are handed back for free, a plain Analyze does now call
        `fetch_questions_block`, but only with `allow_fetch=False`, which returns what is
        stored and can never reach the network. Asserting "not called" would forbid the free
        restore that fixed "hard refresh loses my backlinks".
        """
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **kw: r), \
             mock.patch.object(svc, "fetch_questions_block",
                               return_value={"state": "not_loaded"}) as questions:
            out = svc.run_domain_overview("premierstaff.com")

        for call in questions.call_args_list:
            self.assertFalse(call.kwargs.get("allow_fetch", True),
                             "a plain Analyze must never be able to buy questions")
        self.assertNotIn("questions", out, "and nothing owned means nothing to show")

    def test_include_questions_adds_the_block(self):
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **kw: r), \
             mock.patch.object(svc, "fetch_questions_block",
                               return_value={"state": "ok", "rows": ROWS}) as questions:
            out = svc.run_domain_overview("premierstaff.com", include=["questions"])
        questions.assert_called_once()
        self.assertEqual(out["questions"]["state"], "ok")
