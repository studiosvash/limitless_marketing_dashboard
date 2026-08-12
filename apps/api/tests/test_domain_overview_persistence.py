"""A domain is paid for once, not once a day.

The three Domain Overview blocks held their results in a 24-hour cache and nothing else, so
re-opening a URL the next morning bought it again. On the AI-questions endpoint that is a $0.10
fixed fee per request before a single row is counted, so the repeat was the most expensive
habit the page had.

Read order is now: stored row -> 24h cache -> network, and only an explicit Refresh skips the
first two.
"""
import tempfile
from pathlib import Path
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from apps.dashboard.services import domain_overview_service as svc
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db

KEYWORDS_OK = {"status": "ok", "metrics": {"ranked_keywords": 5},
               "keywords": [{"keyword": "event staffing", "volume": 100}], "cost": 0.015}
QUESTIONS_OK = {"status": "ok", "total": 1, "domain": "premierstaff.com", "cost": 0.20,
                "platforms": ["chat_gpt"], "partial": None,
                "rows": [{"question": "how many bartenders?", "our_url":
                          "https://premierstaff.com/blog/x", "cited": True,
                          "ai_search_volume": 82}]}


class PersistenceTests(TestCase):
    def setUp(self):
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

    # ---------------- keywords ----------------

    def _keywords(self, **kw):
        return mock.patch(
            "pipeline.connectors.dataforseo_domain_overview.DataForSEODomainOverviewConnector",
            **kw)

    def test_a_lookup_survives_the_cache_expiring(self):
        with self._keywords() as conn:
            conn.return_value.get_domain_overview.return_value = KEYWORDS_OK
            svc.fetch_keywords_block("premierstaff.com", "United States")

            cache.clear()          # a day passes
            again = svc.fetch_keywords_block("premierstaff.com", "United States")
            self.assertEqual(conn.return_value.get_domain_overview.call_count, 1,
                             "the stored answer must serve the second lookup")
        self.assertTrue(again["fromStore"])
        self.assertEqual(again["metrics"]["ranked_keywords"], 5)

    def test_refresh_buys_a_new_answer_and_replaces_the_stored_one(self):
        with self._keywords() as conn:
            conn.return_value.get_domain_overview.return_value = KEYWORDS_OK
            svc.fetch_keywords_block("premierstaff.com", "United States")

            conn.return_value.get_domain_overview.return_value = {
                **KEYWORDS_OK, "metrics": {"ranked_keywords": 99}}
            fresh = svc.fetch_keywords_block("premierstaff.com", "United States", refresh=True)
            self.assertEqual(conn.return_value.get_domain_overview.call_count, 2)
        self.assertEqual(fresh["metrics"]["ranked_keywords"], 99)

        cache.clear()
        with self._keywords() as conn:
            stored = svc.fetch_keywords_block("premierstaff.com", "United States")
            conn.return_value.get_domain_overview.assert_not_called()
        self.assertEqual(stored["metrics"]["ranked_keywords"], 99, "refresh replaced the row")

    def test_the_report_path_reads_a_month_old_lookup_and_spends_nothing(self):
        with self._keywords() as conn:
            conn.return_value.get_domain_overview.return_value = KEYWORDS_OK
            svc.fetch_keywords_block("premierstaff.com", "United States")
        cache.clear()
        with self._keywords() as conn:
            block = svc.fetch_keywords_block("premierstaff.com", "United States",
                                             allow_fetch=False)
            conn.return_value.get_domain_overview.assert_not_called()
        self.assertIsNotNone(block, "a report of a stored domain must not come back empty")
        self.assertEqual(block["metrics"]["ranked_keywords"], 5)

    def test_a_market_is_stored_separately(self):
        with self._keywords() as conn:
            conn.return_value.get_domain_overview.return_value = KEYWORDS_OK
            svc.fetch_keywords_block("premierstaff.com", "United States")
            cache.clear()
            svc.fetch_keywords_block("premierstaff.com", "United Kingdom")
            self.assertEqual(conn.return_value.get_domain_overview.call_count, 2)

    # ---------------- questions ----------------

    def test_questions_survive_the_cache_and_still_filter_by_page(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=QUESTIONS_OK) as fetch:
            svc.fetch_questions_block("premierstaff.com")
            cache.clear()
            page = svc.fetch_questions_block("premierstaff.com/blog/x")
            self.assertEqual(fetch.call_count, 1, "the domain was already bought")
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["page"], "premierstaff.com/blog/x")

    def test_a_stored_domain_answers_a_page_that_has_no_questions_honestly(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=QUESTIONS_OK):
            svc.fetch_questions_block("premierstaff.com")
        cache.clear()
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as fetch:
            block = svc.fetch_questions_block("premierstaff.com/nothing")
            fetch.assert_not_called()
        self.assertEqual(block["state"], "empty")
        self.assertEqual(block["domainTotal"], 1)

    def test_questions_refresh_re_buys(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=QUESTIONS_OK) as fetch:
            svc.fetch_questions_block("premierstaff.com")
            svc.fetch_questions_block("premierstaff.com", refresh=True)
            self.assertEqual(fetch.call_count, 2)

    def test_run_domain_overview_threads_refresh_to_every_block(self):
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}) as kw, \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **k: r), \
             mock.patch.object(svc, "fetch_questions_block", return_value={}) as q, \
             mock.patch.object(svc, "fetch_backlinks_block", return_value={}) as bl:
            svc.run_domain_overview("premierstaff.com", include=["questions", "backlinks"],
                                    refresh=True)
        self.assertTrue(kw.call_args.kwargs["refresh"])
        self.assertTrue(q.call_args.kwargs["refresh"])
        self.assertTrue(bl.call_args.kwargs["refresh"])
