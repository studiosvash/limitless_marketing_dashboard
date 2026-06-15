import sqlite3
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, override_settings

from sqlalchemy import inspect as sa_inspect

from pipeline.db.engine import get_engine
from apps.sync.models import SyncLog, RefreshRun


class SyncLogTests(TestCase):
    def test_unique_connector_site(self):
        SyncLog.objects.create(connector="gsc", site_url="https://fusehealth.com")
        with self.assertRaises(IntegrityError):
            SyncLog.objects.create(connector="gsc", site_url="https://fusehealth.com")

    def test_defaults(self):
        log = SyncLog.objects.create(connector="ga4", site_url="https://fusehealth.com")
        self.assertEqual(log.status, "never")
        self.assertEqual(log.records_written, 0)


class RefreshRunTests(TestCase):
    def test_percent_zero_when_no_total(self):
        run = RefreshRun.objects.create(site_url="https://fusehealth.com")
        self.assertEqual(run.percent, 0)

    def test_percent_computes(self):
        run = RefreshRun.objects.create(
            site_url="https://fusehealth.com", completed_count=3, total_count=4
        )
        self.assertEqual(run.percent, 75)


def _build_old_db(path: str) -> None:
    """Create a tiny legacy cache.db with real+demo rows and a global anomalies table."""
    c = sqlite3.connect(path)
    c.executescript(
        """
        CREATE TABLE sites (id INTEGER PRIMARY KEY, site_url TEXT, site_name TEXT, is_active INTEGER);
        INSERT INTO sites (site_url, site_name, is_active) VALUES ('https://fusehealth.com', 'Fuse', 1);

        CREATE TABLE seo_daily (id INTEGER PRIMARY KEY, date DATE, site_id TEXT, clicks INTEGER, data_source TEXT);
        INSERT INTO seo_daily (date, site_id, clicks, data_source) VALUES
            ('2026-06-01', 'https://fusehealth.com', 10, 'real'),
            ('2026-06-02', 'https://fusehealth.com', 20, 'demo');

        CREATE TABLE anomalies (id INTEGER PRIMARY KEY, date DATE, metric_type TEXT,
            actual_value REAL, baseline_value REAL, deviation_pct REAL, severity TEXT);
        INSERT INTO anomalies (date, metric_type, actual_value, baseline_value, deviation_pct, severity)
            VALUES ('2026-06-01', 'seo_clicks', 5, 10, -50, 'high');

        CREATE TABLE insights (id INTEGER PRIMARY KEY, date DATE, team TEXT, title TEXT,
            description TEXT, impact TEXT, created_by TEXT, is_verified INTEGER);
        INSERT INTO insights (date, team, title, description, impact, created_by, is_verified)
            VALUES ('2026-06-01', 'seo', 'Pricing relaunch', 'Rebuilt pricing page', 'positive', 'seo_lead', 1);
        """
    )
    c.commit()
    c.close()


class MigrateLegacyDataTests(TestCase):
    def test_copies_real_rows_and_backfills_site_id(self):
        tmp = tempfile.mkdtemp()
        old_db = str(Path(tmp) / "cache.db")
        new_db = str(Path(tmp) / "fusehealth.db")
        _build_old_db(old_db)

        with override_settings(ANALYTICS_DB_PATH=new_db):
            call_command("migrate_legacy_data", source=old_db)

            insp = sa_inspect(get_engine(new_db))
            self.assertIn("seo_daily", insp.get_table_names())

        conn = sqlite3.connect(new_db)
        # only the 'real' seo_daily row copied (demo filtered out)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM seo_daily").fetchone()[0], 1)
        # anomalies row got site_id backfilled from the active site
        site_id = conn.execute("SELECT site_id FROM anomalies").fetchone()[0]
        self.assertEqual(site_id, "https://fusehealth.com")
        conn.close()

    def test_idempotent(self):
        # Asserts on anomalies, whose unique key (date, site_id, metric_type) has no
        # NULL columns. (seo_daily has all-NULL dimension columns, which SQLite treats
        # as DISTINCT in a unique index, so it is NOT dedupe-safe on re-run by design.)
        tmp = tempfile.mkdtemp()
        old_db = str(Path(tmp) / "cache.db")
        new_db = str(Path(tmp) / "fusehealth.db")
        _build_old_db(old_db)
        with override_settings(ANALYTICS_DB_PATH=new_db):
            call_command("migrate_legacy_data", source=old_db)
            call_command("migrate_legacy_data", source=old_db)
        conn = sqlite3.connect(new_db)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM anomalies").fetchone()[0], 1)
        conn.close()


class MigrateInsightsTests(TestCase):
    def test_insights_copied_to_django(self):
        from django.contrib.auth import get_user_model
        from apps.dashboard.models import Insight

        get_user_model().objects.create_user("seo_lead", password="x")
        tmp = tempfile.mkdtemp()
        old_db = str(Path(tmp) / "cache.db")
        new_db = str(Path(tmp) / "fusehealth.db")
        _build_old_db(old_db)

        with override_settings(ANALYTICS_DB_PATH=new_db):
            call_command("migrate_legacy_data", source=old_db)

        self.assertEqual(Insight.objects.count(), 1)
        ins = Insight.objects.first()
        self.assertEqual(ins.title, "Pricing relaunch")
        self.assertEqual(ins.site_url, "https://fusehealth.com")
        self.assertEqual(ins.created_by.username, "seo_lead")
        self.assertTrue(ins.is_verified)
