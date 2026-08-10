"""`upsert_keyword_rankings` — a measured absence must be able to overwrite a position (P6).

THE BUG. The upsert COALESCEd every column: `set_={k: coalesce(excluded[k], stored[k])}`. That
is correct for the columns three connectors share — `dataforseo_keywords` writes volume/KD/CPC
and knows nothing about positions, `gsc_keywords` writes clicks/impressions and would otherwise
blank them for each other — but it made a MEASURED DROP unrecordable.

`dataforseo_serp` captures to depth 30 and writes `position: None` when the domain is not in
that depth. That is a measurement, not a gap. COALESCE discarded it and kept whatever rank the
row already held, while stamping a fresh `rank_checked_at` on top — so a site that fell off page
one on the same date it had been recorded at #4 kept showing #4, marked as freshly checked,
forever.

The fix is per-caller: a writer that owns a column can declare it overwrite-always, and every
other column keeps COALESCE so the volume-only and GSC connectors still cannot null out each
other's data.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings
from sqlalchemy import select

from pipeline.db.engine import get_engine
from pipeline.db.schema import KeywordRanking, init_db
from pipeline.db.writer import SERP_MEASUREMENT_COLUMNS, upsert_keyword_rankings

DAY = date(2026, 8, 1)
LOC = "United States"


class RankingOverwriteTests(TestCase):
    def setUp(self):
        # The module-level session factory is a singleton and would otherwise leak the previous
        # test's (or the developer's real) database — skills.md §8.
        import pipeline.utils.db_connection as db_connection
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "ranks.db")
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        self.engine = get_engine(db_path)
        init_db(self.engine)
        from sqlalchemy.orm import sessionmaker
        self.Session = sessionmaker(bind=self.engine)
        self.addCleanup(self.engine.dispose)

    def _row(self, keyword="event staffing"):
        with self.Session() as session:
            return session.execute(
                select(KeywordRanking).where(KeywordRanking.keyword == keyword)
            ).scalars().one()

    def _write(self, records, **kw):
        with self.Session() as session:
            n = upsert_keyword_rankings(session, records, site_id="premierstaff.com", **kw)
            session.commit()
            return n

    def _base(self, **over):
        rec = {"date": DAY, "site_id": "premierstaff.com", "keyword": "event staffing",
               "location": LOC, "position": 4, "url": "https://premierstaff.com/dc",
               "rank_checked_at": DAY}
        rec.update(over)
        return rec

    def test_a_measured_drop_clears_the_position(self):
        self._write([self._base()])
        self._write([self._base(position=None, url=None)],
                    overwrite_columns=SERP_MEASUREMENT_COLUMNS)
        row = self._row()
        self.assertIsNone(
            row.position,
            "the SERP was checked and the domain was not in the captured depth — the dashboard "
            "must not keep advertising a rank the site no longer holds",
        )
        self.assertIsNone(row.url, "and not a ranking URL for a page that no longer ranks")
        self.assertEqual(row.rank_checked_at, DAY)

    def test_a_measured_drop_leaves_the_other_connectors_columns_alone(self):
        """The whole reason COALESCE is there: three connectors write this one row."""
        self._write([self._base()])
        self._write([{"date": DAY, "site_id": "premierstaff.com", "keyword": "event staffing",
                      "location": LOC, "search_volume": 2400, "cpc": 3.5}])
        self._write([self._base(position=None, url=None)],
                    overwrite_columns=SERP_MEASUREMENT_COLUMNS)
        row = self._row()
        self.assertEqual(row.search_volume, 2400,
                         "the SERP writer must not null out dataforseo_keywords' volume")
        self.assertEqual(row.cpc, 3.5)

    def test_the_default_is_unchanged_coalesce(self):
        """No `overwrite_columns` = today's behaviour exactly, for every existing caller."""
        self._write([self._base()])
        self._write([self._base(position=None, url=None)])
        row = self._row()
        self.assertEqual(row.position, 4)
        self.assertEqual(row.url, "https://premierstaff.com/dc")

    def test_a_volume_only_writer_cannot_clear_a_position(self):
        """It never sends `position`, so the column is not in its update set at all."""
        self._write([self._base()])
        self._write([{"date": DAY, "site_id": "premierstaff.com", "keyword": "event staffing",
                      "location": LOC, "search_volume": 2400}],
                    overwrite_columns=SERP_MEASUREMENT_COLUMNS)
        self.assertEqual(self._row().position, 4)

    def test_a_real_position_still_overwrites_an_older_one(self):
        self._write([self._base()])
        self._write([self._base(position=11)], overwrite_columns=SERP_MEASUREMENT_COLUMNS)
        self.assertEqual(self._row().position, 11)

    def test_an_unknown_column_name_is_ignored_not_raised(self):
        """`serp_features` has no column on this table; a caller naming it must not 500."""
        self._write([self._base()])
        self._write([self._base(position=None)],
                    overwrite_columns=("position", "serp_features", "not_a_column"))
        self.assertIsNone(self._row().position)
