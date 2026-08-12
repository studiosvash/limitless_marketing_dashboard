"""Recent lookups come from the database, not the browser.

Reported: a URL analysed a minute earlier was missing from Recent after a hard refresh. The
history lived in localStorage AND stored each entry's full payload there, so the quota filled
and `doHistSave` shed entries to recover — silently, and starting with the ones that had the
most data behind them.

`domain_lookups` already records every lookup, so the list is derived from it. A second copy
could only ever disagree with the first.
"""
import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from apps.dashboard.services.domain_lookup_store import recent_lookups, save_block
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db


class RecentLookupTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None

    def test_nothing_looked_up_yet_is_an_empty_list(self):
        self.assertEqual(recent_lookups(), [])

    def test_a_lookup_appears_with_its_full_target(self):
        save_block("premierstaff.com/blog/x", "keywords", {"status": "ok"},
                   location="United States")
        recent = recent_lookups()
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["target"], "premierstaff.com/blog/x")
        self.assertEqual(recent[0]["location"], "United States")
        self.assertIsNotNone(recent[0]["storedAt"])

    def test_a_page_and_its_domain_are_separate_entries(self):
        save_block("premierstaff.com", "keywords", {"status": "ok"})
        save_block("premierstaff.com/blog/x", "keywords", {"status": "ok"})
        self.assertEqual(len(recent_lookups()), 2)

    def test_re_analysing_the_same_target_does_not_add_a_second_entry(self):
        save_block("premierstaff.com", "keywords", {"status": "ok"})
        save_block("premierstaff.com", "keywords", {"status": "ok"})
        self.assertEqual(len(recent_lookups()), 1)

    def test_only_the_block_every_analyze_writes_counts(self):
        """A questions-only press must not create a Recent entry for a domain whose keywords
        were never looked up — the chip would replay a lookup that does not exist."""
        save_block("premierstaff.com", "questions:chat_gpt", {"state": "ok"})
        self.assertEqual(recent_lookups(), [])

    def test_the_list_is_capped(self):
        for i in range(15):
            save_block(f"site{i}.com", "keywords", {"status": "ok"})
        self.assertEqual(len(recent_lookups(limit=10)), 10)

    def test_a_read_failure_is_an_empty_chip_row_not_a_broken_page(self):
        with mock.patch("apps.dashboard.services.domain_lookup_store.get_session",
                        side_effect=RuntimeError("db gone")):
            self.assertEqual(recent_lookups(), [])

    def test_the_analyze_response_carries_the_list(self):
        from apps.dashboard.services import domain_overview_service as svc

        save_block("premierstaff.com", "keywords", {"status": "ok"})
        with mock.patch.object(svc, "fetch_keywords_block", return_value={"status": "ok"}), \
             mock.patch.object(svc, "apply_tracked_flags", side_effect=lambda r, **k: r):
            out = svc.run_domain_overview("premierstaff.com")
        self.assertEqual(out["recent"][0]["target"], "premierstaff.com")
