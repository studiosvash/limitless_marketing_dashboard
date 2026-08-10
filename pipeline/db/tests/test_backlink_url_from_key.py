"""The `backlinks` unique key must include `url_from`, and `url_from` must never be NULL.

Why both halves matter, and why they are one migration rather than two:

  * WITHOUT url_from in the key, `(site_id, referring_domain, target_url)` collapses every
    page of a referring domain that links to the same target into ONE row. A site-wide
    footer link from a 200-page blog stored 1 row, not 200, and the survivor kept whichever
    `url_from` happened to arrive last. The exact source URLs Semrush shows could not be
    held by this table at all, and the total/live/lost counts (which are `len(rows)` of the
    collapsed set) were deflated by the same factor — 362 stored against DataForSEO's own
    729 for the same profile.

  * WITH url_from in the key but still NULLABLE, Postgres would not treat two rows whose
    `url_from` is NULL as conflicting (NULL != NULL inside a unique index), so every legacy
    row would bypass ON CONFLICT and duplicate on EVERY sync. That is the documented
    skills.md §9 trap, and it is why the backfill and the NOT NULL are part of this change
    and not a follow-up.

These tests run on SQLite (the suite forces it), so the Postgres-only NULL semantics cannot
be reproduced here. What IS assertable everywhere is the shape the migration leaves behind:
the constraint's columns, its name, and that no NULL survives the backfill.
"""
import unittest

from sqlalchemy import inspect, select, text

from pipeline.db.engine import get_engine
from pipeline.db.schema import Backlink, ensure_backlink_url_from_key, init_db
from pipeline.db.writer import upsert_backlinks
from sqlalchemy.orm import sessionmaker


NEW_KEY = {"site_id", "referring_domain", "url_from", "target_url"}
OLD_KEY = {"site_id", "referring_domain", "target_url"}


def _unique_col_sets(insp, table):
    sets = [set(uc["column_names"]) for uc in insp.get_unique_constraints(table)]
    sets += [set(i["column_names"]) for i in insp.get_indexes(table) if i.get("unique")]
    return sets


def _unique_names(insp, table):
    names = {uc.get("name") for uc in insp.get_unique_constraints(table)}
    names |= {i.get("name") for i in insp.get_indexes(table) if i.get("unique")}
    return names


class FreshDatabaseTests(unittest.TestCase):
    """A database created today must already carry the new key — no migration involved."""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_engine(":memory:")
        init_db(cls.engine)
        cls.insp = inspect(cls.engine)

    def test_unique_key_covers_url_from(self):
        self.assertIn(NEW_KEY, _unique_col_sets(self.insp, "backlinks"))

    def test_the_old_three_column_key_is_gone(self):
        self.assertNotIn(OLD_KEY, _unique_col_sets(self.insp, "backlinks"))

    def test_the_constraint_was_renamed(self):
        """`_swap_unique_constraint` decides whether a database is already reconciled by the
        constraint NAME, so redefining `uq_backlink_site` in place would leave every existing
        database silently on the old key forever."""
        self.assertIn("uq_backlink_site_url_from", _unique_names(self.insp, "backlinks"))

    def test_url_from_is_not_nullable(self):
        col = next(c for c in self.insp.get_columns("backlinks") if c["name"] == "url_from")
        self.assertFalse(col["nullable"])


# The `backlinks` table exactly as it existed before this migration: three-column key,
# nullable url_from. Written out rather than generated so the test still describes the old
# shape after the model has moved on.
_LEGACY_DDL = """
CREATE TABLE backlinks (
    id INTEGER NOT NULL,
    site_id VARCHAR(255) NOT NULL,
    referring_domain VARCHAR(500) NOT NULL,
    target_url TEXT NOT NULL,
    anchor TEXT,
    status VARCHAR(20),
    dofollow INTEGER,
    domain_rank INTEGER,
    first_seen DATE,
    last_seen DATE,
    url_from TEXT,
    page_from_rank INTEGER,
    spam_score INTEGER,
    PRIMARY KEY (id),
    CONSTRAINT uq_backlink_site UNIQUE (site_id, referring_domain, target_url)
)
"""


class LegacyDatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = get_engine(":memory:")
        with self.engine.begin() as conn:
            conn.execute(text(_LEGACY_DDL))
            conn.execute(text(
                "INSERT INTO backlinks (site_id, referring_domain, target_url, anchor, url_from) "
                "VALUES ('a.com', 'blog.com', 'https://a.com/', 'never synced url_from', NULL)"
            ))
            conn.execute(text(
                "INSERT INTO backlinks (site_id, referring_domain, target_url, anchor, url_from) "
                "VALUES ('a.com', 'news.com', 'https://a.com/', 'has one', 'https://news.com/post')"
            ))

    def _insp(self):
        return inspect(self.engine)

    def test_migration_swaps_the_key_and_reports_that_it_changed_something(self):
        self.assertTrue(ensure_backlink_url_from_key(self.engine))
        insp = self._insp()
        self.assertIn(NEW_KEY, _unique_col_sets(insp, "backlinks"))
        self.assertNotIn(OLD_KEY, _unique_col_sets(insp, "backlinks"))

    def test_null_url_from_is_backfilled_to_empty_string(self):
        """'' is the same value the connector already writes when DataForSEO omits url_from
        (`item.get("url_from") or ""`), so "source page unknown" has ONE representation
        rather than two that the UI would have to tell apart."""
        ensure_backlink_url_from_key(self.engine)
        with self.engine.begin() as conn:
            nulls = conn.execute(text(
                "SELECT COUNT(*) FROM backlinks WHERE url_from IS NULL")).scalar()
            blanks = conn.execute(text(
                "SELECT COUNT(*) FROM backlinks WHERE url_from = ''")).scalar()
        self.assertEqual(nulls, 0)
        self.assertEqual(blanks, 1)

    def test_existing_rows_survive_the_rebuild(self):
        ensure_backlink_url_from_key(self.engine)
        with self.engine.begin() as conn:
            rows = conn.execute(text(
                "SELECT referring_domain, anchor, url_from FROM backlinks "
                "ORDER BY referring_domain")).fetchall()
        self.assertEqual(
            [tuple(r) for r in rows],
            [("blog.com", "never synced url_from", ""),
             ("news.com", "has one", "https://news.com/post")],
        )

    def test_url_from_becomes_not_nullable(self):
        ensure_backlink_url_from_key(self.engine)
        col = next(c for c in self._insp().get_columns("backlinks") if c["name"] == "url_from")
        self.assertFalse(col["nullable"])

    def test_second_call_is_a_no_op(self):
        self.assertTrue(ensure_backlink_url_from_key(self.engine))
        self.assertFalse(ensure_backlink_url_from_key(self.engine))

    def test_after_migrating_the_same_domain_can_store_one_row_per_source_page(self):
        """The point of the whole change, asserted end-to-end through the writer."""
        ensure_backlink_url_from_key(self.engine)
        Session = sessionmaker(bind=self.engine, future=True)
        with Session() as s:
            upsert_backlinks(s, [
                {"referring_domain": "blog.com", "target_url": "https://a.com/",
                 "url_from": f"https://blog.com/post-{i}", "anchor": f"link {i}"}
                for i in range(200)
            ], site_id="a.com")
            s.commit()
        with Session() as s:
            stored = s.execute(
                select(Backlink).where(Backlink.referring_domain == "blog.com")
            ).scalars().all()
        # 200 real source pages + the one legacy row whose url_from was never captured.
        self.assertEqual(len(stored), 201)
        self.assertEqual(len({b.url_from for b in stored}), 201)


if __name__ == "__main__":
    unittest.main()
