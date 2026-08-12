"""The store that makes a domain cost money once instead of once a day."""
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from django.test import TestCase, override_settings
from sqlalchemy import select, update

import pipeline.utils.db_connection as db_connection
from apps.dashboard.services.domain_lookup_store import load_block, save_block
from pipeline.db.engine import get_engine
from pipeline.db.schema import DomainLookup, init_db
from pipeline.utils.db_connection import get_session

PAYLOAD = {"state": "ok", "rows": [{"question": "how many bartenders?", "cited": True}],
           "total": 1}


class DomainLookupStoreTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None

    def test_a_saved_block_comes_back(self):
        self.assertTrue(save_block("premierstaff.com", "questions", PAYLOAD))
        got = load_block("premierstaff.com", "questions")
        self.assertEqual(got["total"], 1)
        self.assertEqual(got["rows"][0]["question"], "how many bartenders?")

    def test_a_block_never_looked_up_is_none_not_an_empty_result(self):
        """None means "never asked"; an empty dict would read as "asked, found nothing"."""
        self.assertIsNone(load_block("premierstaff.com", "questions"))

    def test_a_page_and_its_domain_are_stored_apart(self):
        save_block("premierstaff.com", "questions", {"total": 9})
        save_block("premierstaff.com/blog/x", "questions", {"total": 2})
        self.assertEqual(load_block("premierstaff.com", "questions")["total"], 9)
        self.assertEqual(load_block("premierstaff.com/blog/x", "questions")["total"], 2)

    def test_the_url_form_does_not_change_the_key(self):
        save_block("https://www.premierstaff.com/blog/x/", "questions", {"total": 3})
        self.assertEqual(load_block("premierstaff.com/blog/x", "questions")["total"], 3)

    def test_blocks_of_one_target_do_not_overwrite_each_other(self):
        save_block("premierstaff.com", "questions", {"total": 1})
        save_block("premierstaff.com", "keywords", {"total": 50})
        self.assertEqual(load_block("premierstaff.com", "questions")["total"], 1)
        self.assertEqual(load_block("premierstaff.com", "keywords")["total"], 50)

    def test_a_re_save_replaces_rather_than_accumulating(self):
        save_block("premierstaff.com", "questions", {"total": 1})
        save_block("premierstaff.com", "questions", {"total": 7})
        self.assertEqual(load_block("premierstaff.com", "questions")["total"], 7)
        with get_session() as s:
            self.assertEqual(len(s.execute(select(DomainLookup)).scalars().all()), 1)

    def test_the_age_is_reported_so_the_ui_can_say_as_of(self):
        save_block("premierstaff.com", "questions", PAYLOAD)
        with get_session() as s:
            s.execute(update(DomainLookup).values(
                fetched_at=datetime.now(timezone.utc) - timedelta(days=9)))
            s.commit()
        got = load_block("premierstaff.com", "questions")
        self.assertEqual(got["ageDays"], 9)
        self.assertIsNotNone(got["storedAt"])
        self.assertTrue(got["fromStore"])

    def test_the_age_markers_are_not_themselves_stored(self):
        """Storing them would freeze the first write's moment into every later answer."""
        save_block("premierstaff.com", "questions", {**PAYLOAD, "storedAt": "1999-01-01",
                                                     "ageDays": 999, "cached": True})
        got = load_block("premierstaff.com", "questions")
        self.assertNotEqual(got["storedAt"], "1999-01-01")
        self.assertEqual(got["ageDays"], 0)

    def test_a_write_failure_is_reported_not_raised(self):
        """A service never raises: losing persistence costs money, not correctness."""
        with mock.patch("apps.dashboard.services.domain_lookup_store.upsert_domain_lookup",
                        side_effect=RuntimeError("disk full")):
            self.assertFalse(save_block("premierstaff.com", "questions", PAYLOAD))

    def test_a_read_failure_returns_none_rather_than_raising(self):
        with mock.patch("apps.dashboard.services.domain_lookup_store.get_session",
                        side_effect=RuntimeError("db gone")):
            self.assertIsNone(load_block("premierstaff.com", "questions"))

    def test_a_target_that_is_not_a_domain_is_refused_quietly(self):
        self.assertFalse(save_block("", "questions", PAYLOAD))
        self.assertIsNone(load_block("", "questions"))
