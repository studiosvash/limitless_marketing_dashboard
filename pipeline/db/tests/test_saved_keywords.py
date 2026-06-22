"""Tests for the SavedKeyword table: the writer upsert and the saved_keyword_service
round-trip. Uses an isolated temp SQLite DB; never touches the real analytics DB."""
import os
import tempfile
import unittest
import unittest.mock
from contextlib import contextmanager

from sqlalchemy import select

from pipeline.db.engine import get_engine, get_sessionmaker
from pipeline.db.schema import SavedKeyword
from pipeline.db.writer import upsert_saved_keywords


class SavedKeywordWriterTests(unittest.TestCase):
    def setUp(self):
        self.engine = get_engine(":memory:")
        self.Session = get_sessionmaker(":memory:")
        # Bind the in-memory sessionmaker to the same engine so tables persist.
        self.Session.configure(bind=self.engine)
        SavedKeyword.__table__.create(self.engine)

    def test_upsert_inserts_and_updates_in_place(self):
        with self.Session() as s:
            n = upsert_saved_keywords(s, [{
                "keyword": "seo agency", "location": "United States",
                "search_volume": 1000, "keyword_difficulty": 45.0, "cpc": 12.5,
                "competition": "HIGH", "intent": "Commercial", "serp_features": "organic",
            }], site_id="example.com")
            s.commit()
        self.assertEqual(n, 1)

        # Re-saving the same (site, keyword, location) updates rather than duplicating.
        with self.Session() as s:
            upsert_saved_keywords(s, [{
                "keyword": "seo agency", "location": "United States",
                "search_volume": 2000, "keyword_difficulty": 50.0, "cpc": 9.0,
                "competition": "MEDIUM", "intent": "Commercial", "serp_features": "organic, paid",
            }], site_id="example.com")
            s.commit()

        with self.Session() as s:
            rows = s.execute(select(SavedKeyword).where(SavedKeyword.site_id == "example.com")).scalars().all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].search_volume, 2000)
        self.assertEqual(rows[0].competition, "MEDIUM")

    def test_empty_records_writes_nothing(self):
        with self.Session() as s:
            self.assertEqual(upsert_saved_keywords(s, [], site_id="example.com"), 0)


class SavedKeywordServiceTests(unittest.TestCase):
    """Exercises list/save/delete by redirecting the service's get_session to a temp-file DB."""

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.engine = get_engine(self.path)
        SavedKeyword.__table__.create(self.engine, checkfirst=True)
        Session = get_sessionmaker(self.path)
        Session.configure(bind=self.engine)

        @contextmanager
        def fake_get_session():
            s = Session()
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise
            finally:
                s.close()

        import pipeline.services.saved_keyword_service as svc
        self._patcher = unittest.mock.patch.object(svc, "get_session", fake_get_session)
        self._patcher.start()
        self.svc = svc

    def tearDown(self):
        self._patcher.stop()
        self.engine.dispose()
        try:
            os.remove(self.path)
        except OSError:
            pass

    def test_save_list_delete_roundtrip(self):
        saved = self.svc.save_keywords("example.com", [
            {"keyword": "seo agency", "location": "United States", "search_volume": "1000",
             "keyword_difficulty": "45", "cpc": "12.5", "competition": "HIGH", "intent": "Commercial"},
            {"keyword": "", "location": "United States"},  # blank keyword is skipped
        ])
        self.assertEqual(saved, 1)

        rows = self.svc.list_saved_keywords("example.com")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["keyword"], "seo agency")
        self.assertEqual(rows[0]["search_volume"], 1000)   # coerced from string
        self.assertEqual(rows[0]["cpc"], 12.5)

        self.assertTrue(self.svc.delete_saved_keyword("example.com", "seo agency", "United States"))
        self.assertEqual(self.svc.list_saved_keywords("example.com"), [])

    def test_list_is_site_scoped(self):
        self.svc.save_keywords("a.com", [{"keyword": "k1", "location": "United States"}])
        self.svc.save_keywords("b.com", [{"keyword": "k2", "location": "United States"}])
        self.assertEqual(len(self.svc.list_saved_keywords("a.com")), 1)
        self.assertEqual(self.svc.list_saved_keywords("a.com")[0]["keyword"], "k1")


if __name__ == "__main__":
    unittest.main()
