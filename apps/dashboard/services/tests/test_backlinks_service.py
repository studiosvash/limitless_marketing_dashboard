import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Backlink
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class BacklinksRawQueryTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add_all([
                Backlink(site_id="sc-domain:fusehealth.com", referring_domain="healthline.com",
                         target_url="https://fusehealth.com/iv-therapy", anchor="iv therapy",
                         status="live", dofollow=1, domain_rank=88),
                Backlink(site_id="sc-domain:fusehealth.com", referring_domain="spamsite.net",
                         target_url="https://fusehealth.com/", anchor="", status="lost",
                         dofollow=0, domain_rank=5),
            ])

    def test_query_backlinks_summary_raw(self):
        from apps.dashboard.services.backlinks_service import query_backlinks_summary_raw
        summary = query_backlinks_summary_raw("sc-domain:fusehealth.com")
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["live"], 1)
        self.assertEqual(summary["lost"], 1)
        self.assertEqual(summary["unique_domains"], 2)

    def test_query_backlinks_table_raw(self):
        from apps.dashboard.services.backlinks_service import query_backlinks_table_raw
        rows = query_backlinks_table_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 2)
        top = next(r for r in rows if r["domain"] == "healthline.com")
        self.assertEqual(top["domain_rank"], 88)
        self.assertEqual(top["status"], "live")

    def test_query_backlinks_summary_raw_returns_zeros_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import backlinks_service
        with mock.patch.object(backlinks_service, "get_session", side_effect=RuntimeError("boom")):
            summary = backlinks_service.query_backlinks_summary_raw("x")
            self.assertEqual(summary, {"total": 0, "live": 0, "lost": 0, "unique_domains": 0, "avg_dr": 0})
