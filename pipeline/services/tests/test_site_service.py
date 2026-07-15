import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings
from sqlalchemy import select

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class AddProjectFieldsCommandTests(TestCase):
    def setUp(self):
        # get_session() memoizes its engine per-process (see db_connection.py) — reset it so
        # each test binds to its own temp DB instead of leaking the previous test's engine.
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)

    def test_adds_columns_and_backfills_slug(self):
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))

        # Simulate a pre-Phase-A database: a site row with no slug/vertical/location.
        # (init_db already creates the new columns since schema.py Step 1 added them — to
        # simulate the *pre-migration* state we insert directly via raw SQL, matching what a
        # real already-deployed DB looks like before this command runs.)
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO sites (site_url, site_name, is_active) VALUES (?, ?, 1)",
            ("sc-domain:fusehealth.com", "FuseHealth"),
        )
        conn.commit()
        conn.close()

        with override_settings(ANALYTICS_DB_PATH=db_path):
            db_connection._SessionFactory = None
            call_command("add_project_fields")

            with get_session() as session:
                site = session.execute(select(Site)).scalars().first()
                self.assertEqual(site.slug, "fusehealth")
                self.assertEqual(site.location, "United States")

    def test_idempotent_when_run_twice(self):
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))

        with override_settings(ANALYTICS_DB_PATH=db_path):
            db_connection._SessionFactory = None
            call_command("add_project_fields")
            call_command("add_project_fields")  # must not raise

            with get_session() as session:
                site = session.execute(select(Site)).scalars().first()
                self.assertIsNone(site)  # no sites were inserted in this test — just checking no crash

    def test_adds_columns_to_a_genuinely_pre_migration_table_and_is_idempotent(self):
        """
        Verify the add_project_fields command correctly handles a genuinely pre-migration
        sites table (one created *before* the vertical/location/slug columns existed).

        This test builds a raw pre-schema table (without those three columns, simulating
        a real production database before this migration), runs the command, and confirms:
        1. The ALTER TABLE statements add the columns
        2. The slug is backfilled correctly
        3. Running the command again is a no-op (idempotent)
        """
        import sqlite3

        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")

        # Create a pre-migration sites table using raw SQL (no vertical/location/slug columns)
        # Include all other Site model columns so SQLAlchemy can read the row after ALTER TABLE
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE sites (
                id INTEGER PRIMARY KEY,
                site_url TEXT,
                site_name TEXT,
                gsc_property TEXT,
                ga4_property_id TEXT,
                dataforseo_target_domain TEXT,
                is_active INTEGER,
                created_at TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO sites (site_url, site_name, gsc_property, ga4_property_id, dataforseo_target_domain, is_active, created_at) VALUES (?, ?, ?, ?, ?, 1, datetime('now'))",
            ("sc-domain:fusehealth.com", "FuseHealth", None, None, None),
        )
        conn.commit()
        conn.close()

        # Run the command against the pre-migration table
        with override_settings(ANALYTICS_DB_PATH=db_path):
            db_connection._SessionFactory = None
            call_command("add_project_fields")

            # Verify the columns were added and slug was backfilled
            with get_session() as session:
                site = session.execute(select(Site)).scalars().first()
                self.assertIsNotNone(site)
                self.assertEqual(site.slug, "fusehealth")
                self.assertEqual(site.location, "United States")
                self.assertIsNone(site.vertical)

        # Run the command again against the same DB to verify idempotency
        with override_settings(ANALYTICS_DB_PATH=db_path):
            db_connection._SessionFactory = None
            call_command("add_project_fields")  # must not raise

            # Verify the slug remains unchanged and no duplicate columns were created
            with get_session() as session:
                site = session.execute(select(Site)).scalars().first()
                self.assertIsNotNone(site)
                self.assertEqual(site.slug, "fusehealth")
                self.assertEqual(site.location, "United States")
                self.assertIsNone(site.vertical)
