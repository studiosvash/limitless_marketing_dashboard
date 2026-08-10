"""Tests for _dedupe_by_keys — the guard against Postgres's
`CardinalityViolation: ON CONFLICT DO UPDATE command cannot affect row a second time`.

READ THIS BEFORE ADDING A CASE HERE. These tests run on SQLite, and SQLite **cannot** raise
the error they defend against: it applies a multi-row INSERT one row at a time, so a duplicate
inside the batch silently UPDATEs the row the previous one just inserted. Postgres treats the
whole statement as one command and refuses. That is exactly how the backlinks outage reached
production — `manage.py test` is forced onto SQLite (config/settings/base.py, RUNNING_TESTS),
so no integration test in this repo can reproduce it.

So the coverage is split deliberately:
  * the dedupe function is tested as a PURE FUNCTION on the record list, where the behaviour
    is dialect-independent and fully assertable;
  * one integration test goes through upsert_backlinks to prove the helper is actually WIRED
    IN and that "last wins" survives the round trip.
"""
import unittest

from sqlalchemy import select

from pipeline.db.engine import get_engine, get_sessionmaker
from pipeline.db.schema import Backlink
from pipeline.db.writer import _dedupe_by_keys, upsert_backlinks


class DedupeByKeysTests(unittest.TestCase):
    """Pure-function behaviour. Dialect-independent, so these assertions are the real contract."""

    # The live backlinks key. `url_from` joined it on 2026-08-10 — see
    # `test_two_source_pages_on_one_domain_are_two_backlinks` below.
    KEYS = ("site_id", "referring_domain", "url_from", "target_url")

    def test_returns_input_untouched_when_nothing_duplicates(self):
        records = [
            {"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1", "anchor": "one"},
            {"site_id": "a.com", "referring_domain": "y.com", "target_url": "/1", "anchor": "two"},
        ]
        self.assertEqual(_dedupe_by_keys(records, self.KEYS), records)

    def test_short_circuits_on_zero_and_one_record(self):
        self.assertEqual(_dedupe_by_keys([], self.KEYS), [])
        one = [{"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1"}]
        self.assertEqual(_dedupe_by_keys(one, self.KEYS), one)

    def test_last_occurrence_wins(self):
        """Matches on_conflict_do_update semantics: the value a row-by-row apply would leave."""
        out = _dedupe_by_keys([
            {"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1", "domain_rank": 10},
            {"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1", "domain_rank": 20},
            {"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1", "domain_rank": 30},
        ], self.KEYS)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["domain_rank"], 30)

    def test_survivor_keeps_the_first_occurrences_position(self):
        """Order stability keeps batching deterministic and diffs reviewable."""
        out = _dedupe_by_keys([
            {"site_id": "a.com", "referring_domain": "dup.com", "target_url": "/1", "anchor": "first"},
            {"site_id": "a.com", "referring_domain": "other.com", "target_url": "/1", "anchor": "middle"},
            {"site_id": "a.com", "referring_domain": "dup.com", "target_url": "/1", "anchor": "last"},
        ], self.KEYS)
        self.assertEqual([r["referring_domain"] for r in out], ["dup.com", "other.com"])
        self.assertEqual(out[0]["anchor"], "last")

    def test_the_real_backlinks_shape_site_wide_footer_links(self):
        """The production case: one referring domain links to the same target from N pages.

        This test used to assert `len(out) == 1` and call that correct, because `url_from` was
        not in the key — so 199 of these 200 rows were thrown away in Python before the insert
        and the survivor kept whichever source URL arrived last. A site-wide footer link from a
        200-page blog IS 200 backlinks; it is what DataForSEO bills for, what Semrush shows,
        and what made the stored profile read 362 against DataForSEO's own 729. Nothing about
        the dedupe helper changed — the KEY did, and the helper now correctly keeps all 200.
        """
        records = [
            {"site_id": "a.com", "referring_domain": "blog.com", "target_url": "https://a.com/",
             "url_from": f"https://blog.com/post-{i}",
             "anchor": f"link {i}", "dofollow": True, "domain_rank": 50}
            for i in range(200)
        ]
        out = _dedupe_by_keys(records, self.KEYS)
        self.assertEqual(len(out), 200)
        self.assertEqual({r["url_from"] for r in out}, {f"https://blog.com/post-{i}" for i in range(200)})

    def test_two_source_pages_on_one_domain_are_two_backlinks(self):
        """The minimal statement of the same rule, so the intent survives a refactor."""
        out = _dedupe_by_keys([
            {"site_id": "a.com", "referring_domain": "blog.com", "target_url": "https://a.com/",
             "url_from": "https://blog.com/a"},
            {"site_id": "a.com", "referring_domain": "blog.com", "target_url": "https://a.com/",
             "url_from": "https://blog.com/b"},
        ], self.KEYS)
        self.assertEqual(len(out), 2)

    def test_the_same_source_page_twice_still_collapses(self):
        """The dedupe helper's real job is unchanged: DataForSEO can return the same source
        page twice in one response, and Postgres refuses a batch that conflicts with itself."""
        out = _dedupe_by_keys([
            {"site_id": "a.com", "referring_domain": "blog.com", "target_url": "https://a.com/",
             "url_from": "https://blog.com/a", "anchor": "first"},
            {"site_id": "a.com", "referring_domain": "blog.com", "target_url": "https://a.com/",
             "url_from": "https://blog.com/a", "anchor": "last"},
        ], self.KEYS)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["anchor"], "last")

    def test_differing_only_outside_the_key_still_collapses(self):
        out = _dedupe_by_keys([
            {"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1", "status": 200},
            {"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1", "status": 301},
        ], self.KEYS)
        self.assertEqual(len(out), 1)

    def test_none_in_a_key_column_compares_like_any_other_value(self):
        """Two records with the same NULL key collapse here. (Postgres would NOT treat them as
        conflicting in the index itself — that is the separate open issue in SKILLS.md §9.)"""
        out = _dedupe_by_keys([
            {"site_id": "a.com", "referring_domain": None, "target_url": "/1", "status": 200},
            {"site_id": "a.com", "referring_domain": None, "target_url": "/1", "status": 404},
        ], self.KEYS)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["status"], 404)

    def test_a_missing_key_is_not_the_same_as_a_different_value(self):
        out = _dedupe_by_keys([
            {"site_id": "a.com", "target_url": "/1"},                              # no referring_domain
            {"site_id": "a.com", "referring_domain": "x.com", "target_url": "/1"},
        ], self.KEYS)
        self.assertEqual(len(out), 2)


class UpsertBacklinksDedupeIntegrationTests(unittest.TestCase):
    """Proves the helper is wired into upsert_backlinks, not just defined next to it."""

    def setUp(self):
        self.engine = get_engine(":memory:")
        self.Session = get_sessionmaker(":memory:")
        self.Session.configure(bind=self.engine)
        Backlink.__table__.create(self.engine)

    def _rows(self):
        with self.Session() as s:
            return s.execute(select(Backlink)).scalars().all()

    def test_one_row_per_source_page_survives_the_round_trip(self):
        """The key change, asserted through the writer rather than the helper alone."""
        batch = [
            {"referring_domain": "blog.com", "target_url": "https://a.com/",
             "url_from": f"https://blog.com/p{i}", "anchor": f"anchor {i}"}
            for i in range(50)
        ]
        with self.Session() as s:
            upsert_backlinks(s, batch, site_id="a.com")
            s.commit()

        self.assertEqual(len(self._rows()), 50)

    def test_a_batch_full_of_duplicates_writes_one_row_with_the_last_values(self):
        """Same source page repeated — the case `_dedupe_by_keys` genuinely exists for.

        These records carry no `url_from` at all, which `upsert_backlinks` normalises to ''
        rather than leaving NULL: a NULL in a conflict-target column bypasses ON CONFLICT
        entirely on Postgres and duplicates on every sync (skills.md §9).
        """
        batch = [
            {"referring_domain": "blog.com", "target_url": "https://a.com/",
             "anchor": f"anchor {i}", "dofollow": True, "domain_rank": i}
            for i in range(50)
        ]
        with self.Session() as s:
            upsert_backlinks(s, batch, site_id="a.com")
            s.commit()

        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].anchor, "anchor 49")
        self.assertEqual(rows[0].domain_rank, 49)
        self.assertEqual(rows[0].url_from, "")   # never NULL — see the docstring above

    def test_duplicates_do_not_cost_the_other_rows_in_the_batch(self):
        """The outage's real damage: one bad key rolled back the ENTIRE 1000-row batch."""
        batch = [
            {"referring_domain": "dup.com", "target_url": "https://a.com/", "anchor": "a", "domain_rank": 1},
            {"referring_domain": "dup.com", "target_url": "https://a.com/", "anchor": "b", "domain_rank": 2},
        ] + [
            {"referring_domain": f"good{i}.com", "target_url": "https://a.com/",
             "anchor": f"g{i}", "domain_rank": i}
            for i in range(100)
        ]
        with self.Session() as s:
            upsert_backlinks(s, batch, site_id="a.com")
            s.commit()

        self.assertEqual(len(self._rows()), 101)  # 100 unique + 1 collapsed pair

    def test_a_second_sync_still_updates_in_place(self):
        """Dedupe must not break the normal re-sync path."""
        with self.Session() as s:
            upsert_backlinks(s, [{"referring_domain": "x.com", "target_url": "https://a.com/",
                                  "anchor": "old", "domain_rank": 10}], site_id="a.com")
            s.commit()
        with self.Session() as s:
            upsert_backlinks(s, [{"referring_domain": "x.com", "target_url": "https://a.com/",
                                  "anchor": "new", "domain_rank": 99}], site_id="a.com")
            s.commit()

        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].anchor, "new")
        self.assertEqual(rows[0].domain_rank, 99)

    def test_batch_larger_than_batch_size_still_dedupes_across_batch_boundaries(self):
        """Dedupe runs BEFORE batching, so a duplicate pair split across two SQLite batches of
        80 cannot slip through."""
        batch = [
            {"referring_domain": f"d{i}.com", "target_url": "https://a.com/", "anchor": f"a{i}"}
            for i in range(100)
        ]
        batch.append({"referring_domain": "d0.com", "target_url": "https://a.com/", "anchor": "winner"})
        with self.Session() as s:
            upsert_backlinks(s, batch, site_id="a.com")
            s.commit()

        rows = self._rows()
        self.assertEqual(len(rows), 100)
        self.assertEqual(next(r.anchor for r in rows if r.referring_domain == "d0.com"), "winner")
