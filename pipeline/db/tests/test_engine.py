import unittest

from sqlalchemy import inspect

from pipeline.db.engine import get_engine, get_sessionmaker
from pipeline.db.schema import init_db


class EngineTests(unittest.TestCase):
    def test_engine_creates_tables_in_memory(self):
        engine = get_engine(":memory:")
        init_db(engine)
        tables = set(inspect(engine).get_table_names())
        self.assertIn("sites", tables)

    def test_sessionmaker_returns_usable_session(self):
        from sqlalchemy import text

        sm = get_sessionmaker(":memory:")
        with sm() as session:
            self.assertEqual(session.execute(text("SELECT 1")).scalar(), 1)


if __name__ == "__main__":
    unittest.main()
