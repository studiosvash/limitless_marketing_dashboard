"""What you already own comes back free, and you choose which engines to ask.

Reported live: after a hard refresh the Backlinks tab asked to Load again for a target whose
backlinks were sitting in the store. The data had been bought and kept — the plain Analyze
press simply never asked for it, because blocks were only returned when named in `include`.

They are now handed back whenever they are already owned, through `allow_fetch=False`, which
cannot reach the network. Buying still requires the button.
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

QUESTIONS_OK = {"status": "ok", "total": 1, "domain": "premierstaff.com", "cost": 0.20,
                "platforms": ["chat_gpt"], "partial": None,
                "rows": [{"question": "how many bartenders?", "cited": True,
                          "our_url": "https://premierstaff.com/blog/x",
                          "ai_search_volume": 82}]}


class OwnedBlockTests(TestCase):
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

    def _analyze(self, **kw):
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **k: r):
            return svc.run_domain_overview("premierstaff.com", **kw)

    def test_a_plain_analyze_returns_questions_already_owned(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=QUESTIONS_OK):
            svc.fetch_questions_block("premierstaff.com", platforms=["chat_gpt"])
        cache.clear()

        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as fetch:
            out = self._analyze()
            fetch.assert_not_called()
        self.assertEqual(out["questions"]["total"], 1)

    def test_a_plain_analyze_buys_nothing_when_nothing_is_owned(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions") as fetch:
            out = self._analyze()
            fetch.assert_not_called()
        self.assertNotIn("questions", out)

    def test_refresh_does_not_hand_back_the_old_block(self):
        """Refresh means "buy me a new one"; serving the stored copy would ignore the press."""
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=QUESTIONS_OK):
            svc.fetch_questions_block("premierstaff.com", platforms=["chat_gpt"])
        out = self._analyze(refresh=True)
        self.assertNotIn("questions", out)


class PlatformChoiceTests(TestCase):
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

    def test_the_default_is_chatgpt_alone(self):
        self.assertEqual(svc.normalise_platforms(None), ("chat_gpt",))
        self.assertEqual(svc.normalise_platforms([]), ("chat_gpt",))

    def test_both_can_be_chosen(self):
        self.assertEqual(svc.normalise_platforms(["google", "chat_gpt"]),
                         ("chat_gpt", "google"))

    def test_the_order_is_fixed_so_the_cache_key_is_stable(self):
        """However the checkboxes were ticked, the same pair must hit the same entry."""
        self.assertEqual(svc.normalise_platforms(["google", "chat_gpt"]),
                         svc.normalise_platforms(["chat_gpt", "google"]))

    def test_an_unknown_engine_is_dropped(self):
        self.assertEqual(svc.normalise_platforms(["claude", "google"]), ("google",))

    def test_a_wholly_unknown_choice_falls_back_to_the_default(self):
        self.assertEqual(svc.normalise_platforms(["claude"]), ("chat_gpt",))

    def test_one_platform_and_both_are_stored_apart(self):
        """Asking ChatGPT alone and asking both are different answers; serving one for the
        other would under-report without ever saying so."""
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=QUESTIONS_OK) as fetch:
            svc.fetch_questions_block("premierstaff.com", platforms=["chat_gpt"])
            svc.fetch_questions_block("premierstaff.com", platforms=["chat_gpt", "google"])
            self.assertEqual(fetch.call_count, 2)

    def test_the_chosen_platforms_reach_the_connector(self):
        with mock.patch("pipeline.connectors.dataforseo_llm_questions.fetch_llm_questions",
                        return_value=QUESTIONS_OK) as fetch:
            svc.fetch_questions_block("premierstaff.com", platforms=["google"])
        self.assertEqual(fetch.call_args.kwargs["platforms"], ("google",))
