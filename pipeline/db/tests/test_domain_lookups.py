"""`domain_lookups` — every Domain Overview lookup, kept.

A 24-hour cache is not persistence. Re-opening a URL the day after it was looked up re-bought
it, and on this endpoint the bill is a $0.10 FIXED FEE PER REQUEST plus $0.001 per row — so
"the same request again" is the single most expensive thing the page can do and the easiest to
avoid. A domain is now paid for once and refreshed on purpose.

One row per (domain, path, location, block). `path` is part of the key because the AI-questions
block is filtered to a page, and `""` — never NULL — because Postgres does not treat NULL=NULL
as a conflict inside a unique index, so a null key column silently bypasses ON CONFLICT and
duplicates on every write (skills.md §9).
"""
import json
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from sqlalchemy import select

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import DomainLookup, init_db
from pipeline.db.writer import upsert_domain_lookup
from pipeline.utils.db_connection import get_session

DOMAIN = "premierstaff.com"
LOC = "United States"


def _row(block="keywords", path="", payload=None, cost=0.015):
    return {"domain": DOMAIN, "path": path, "location": LOC, "block": block,
            "payload": json.dumps(payload if payload is not None else {"rows": [1, 2]}),
            "cost": cost}


class DomainLookupTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        self.engine = get_engine(db_path)
        init_db(self.engine)
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        db_connection._SessionFactory = None

    def _all(self):
        with get_session() as s:
            return s.execute(select(DomainLookup)).scalars().all()

    def test_two_blocks_for_one_domain_are_separate_rows(self):
        with get_session() as s:
            upsert_domain_lookup(s, [_row("keywords"), _row("questions")])
            s.commit()
        self.assertEqual({r.block for r in self._all()}, {"keywords", "questions"})

    def test_re_looking_up_the_same_block_updates_rather_than_duplicates(self):
        with get_session() as s:
            upsert_domain_lookup(s, [_row(payload={"rows": ["old"]})])
            s.commit()
        with get_session() as s:
            upsert_domain_lookup(s, [_row(payload={"rows": ["new"]})])
            s.commit()

        rows = self._all()
        self.assertEqual(len(rows), 1, "a re-lookup replaces, it does not accumulate")
        self.assertEqual(json.loads(rows[0].payload)["rows"], ["new"])

    def test_a_page_and_its_domain_are_different_rows(self):
        with get_session() as s:
            upsert_domain_lookup(s, [_row(path=""), _row(path="/blog/x")])
            s.commit()
        self.assertEqual(len(self._all()), 2)

    def test_the_payload_round_trips(self):
        payload = {"rows": [{"keyword": "event staffing", "kd": None, "monthly": [1, 2, 3]}],
                   "metrics": {"pos_1": 4}}
        with get_session() as s:
            upsert_domain_lookup(s, [_row(payload=payload)])
            s.commit()
        self.assertEqual(json.loads(self._all()[0].payload), payload)

    def test_a_missing_path_is_stored_as_empty_string_never_null(self):
        """A NULL in a unique-key column bypasses Postgres ON CONFLICT entirely, so the row
        would duplicate on every single write instead of updating in place."""
        with get_session() as s:
            upsert_domain_lookup(s, [{"domain": DOMAIN, "location": LOC, "block": "keywords",
                                      "payload": "{}"}])
            s.commit()
        self.assertEqual(self._all()[0].path, "")

    def test_a_duplicate_inside_one_batch_does_not_break_postgres(self):
        """Two rows sharing the conflict key in a single multi-row upsert raise
        CardinalityViolation on Postgres and roll the WHOLE batch back — SQLite hides it."""
        with get_session() as s:
            written = upsert_domain_lookup(s, [_row(payload={"n": 1}), _row(payload={"n": 2})])
            s.commit()
        self.assertEqual(len(self._all()), 1)
        self.assertEqual(json.loads(self._all()[0].payload)["n"], 2, "last one wins")
        self.assertEqual(written, 1)

    def test_fetched_at_is_stamped(self):
        with get_session() as s:
            upsert_domain_lookup(s, [_row()])
            s.commit()
        self.assertIsNotNone(self._all()[0].fetched_at)

    def test_the_cost_of_the_lookup_is_kept(self):
        with get_session() as s:
            upsert_domain_lookup(s, [_row(cost=0.2)])
            s.commit()
        self.assertAlmostEqual(self._all()[0].cost, 0.2)

    def test_the_ensure_function_is_idempotent_and_never_raises(self):
        from pipeline.db.schema import ensure_domain_lookups
        self.assertIsNotNone(ensure_domain_lookups(self.engine))
        ensure_domain_lookups(self.engine)   # second call must not raise
