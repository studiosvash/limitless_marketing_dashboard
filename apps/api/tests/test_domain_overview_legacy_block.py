"""Renaming a storage key must not orphan what the user already paid for.

Reported: the AI Questions tab said "Not looked up yet" and offered to buy again, for a domain
whose questions had already been fetched. Confirmed from the live table:

    block=questions          <- written before the platform selector existed
    block=questions:google

Adding the engine picker changed the block name from `questions` to `questions:<platforms>`,
which orphaned every row already stored under the bare name. The data was there; the new code
was looking for a key that had never been written.

Two defences, because guessing key names is what caused this:
  * the default platform set falls back to the legacy name;
  * the restore asks the STORE which blocks exist instead of trying a hardcoded list of
    combinations — a list can only ever miss whichever one the user actually bought.
"""
import tempfile
from pathlib import Path
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from apps.dashboard.services import domain_overview_service as svc
from apps.dashboard.services.domain_lookup_store import save_block, stored_blocks
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db

BLOCK = {"state": "ok", "total": 2, "domain": "premierstaff.com", "platforms": ["chat_gpt"],
         "rows": [
             {"question": "how many bartenders?", "cited": True, "ai_search_volume": 82,
              "our_url": "https://premierstaff.com/blog/6-steps"},
             {"question": "who staffs events?", "cited": False, "ai_search_volume": 10,
              "our_url": "https://premierstaff.com/services"},
         ]}


class LegacyQuestionsBlockTests(TestCase):
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

    def test_a_block_stored_under_the_old_name_is_still_read(self):
        save_block("premierstaff.com", "questions", BLOCK)          # the legacy row
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as f:
            got = svc.fetch_questions_block("premierstaff.com")
            f.assert_not_called()
        self.assertEqual(got["state"], "ok")
        self.assertEqual(got["total"], 2)

    def test_the_legacy_fallback_applies_only_to_the_default_engine_set(self):
        """A legacy row was fetched with the default. Serving it for a DIFFERENT choice would
        report Google numbers that were never bought."""
        save_block("premierstaff.com", "questions", BLOCK)
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as f:
            got = svc.fetch_questions_block("premierstaff.com", allow_fetch=False,
                                            platforms=["google"])
            f.assert_not_called()
        self.assertEqual(got["state"], "not_loaded")

    def test_a_page_view_reads_the_legacy_domain_block(self):
        """The reported screen exactly: a blog post, whose domain's questions were bought
        before the rename."""
        save_block("premierstaff.com", "questions", BLOCK)
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as f:
            got = svc.fetch_questions_block(
                "https://premierstaff.com/blog/6-steps-to-calculate-wedding-bartender-cost/")
            f.assert_not_called()
        self.assertEqual(got["domainTotal"], 2)


class StoredBlockDiscoveryTests(TestCase):
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

    def test_blocks_are_listed_for_a_domain(self):
        save_block("premierstaff.com", "keywords", {"status": "ok"})
        save_block("premierstaff.com", "questions:google", BLOCK)
        self.assertEqual(set(stored_blocks("premierstaff.com")),
                         {"keywords", "questions:google"})

    def test_the_prefix_narrows_the_list(self):
        save_block("premierstaff.com", "keywords", {"status": "ok"})
        save_block("premierstaff.com", "questions:google", BLOCK)
        self.assertEqual(stored_blocks("premierstaff.com", prefix="questions"),
                         ["questions:google"])

    def test_a_page_url_lists_its_domain_s_blocks(self):
        save_block("premierstaff.com", "questions:chat_gpt", BLOCK)
        self.assertEqual(stored_blocks("premierstaff.com/blog/x", prefix="questions"),
                         ["questions:chat_gpt"])

    def test_nothing_stored_is_an_empty_list(self):
        self.assertEqual(stored_blocks("premierstaff.com"), [])

    def test_a_read_failure_reports_nothing_owned(self):
        with mock.patch("apps.dashboard.services.domain_lookup_store.get_session",
                        side_effect=RuntimeError("db gone")):
            self.assertEqual(stored_blocks("premierstaff.com"), [])

    def test_analyze_restores_whichever_engine_set_was_actually_bought(self):
        """The hardcoded-guess version tried chat_gpt first and would have missed this."""
        save_block("premierstaff.com", "questions:google", {**BLOCK, "platforms": ["google"]})
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **k: r), \
             mock.patch.object(svc, "recent_lookups", return_value=[]), \
             mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as f:
            out = svc.run_domain_overview("premierstaff.com")
            f.assert_not_called()
        self.assertEqual(out["questions"]["total"], 2)

    def test_analyze_restores_a_legacy_block_too(self):
        save_block("premierstaff.com", "questions", BLOCK)
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **k: r), \
             mock.patch.object(svc, "recent_lookups", return_value=[]), \
             mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as f:
            out = svc.run_domain_overview("premierstaff.com")
            f.assert_not_called()
        self.assertEqual(out["questions"]["total"], 2)
