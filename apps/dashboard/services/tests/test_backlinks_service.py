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


class BuildBacklinksResponseTests(TestCase):
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
            session.add(Backlink(site_id="sc-domain:fusehealth.com", referring_domain="healthline.com",
                                  target_url="https://fusehealth.com/iv-therapy", anchor="iv therapy",
                                  status="live", dofollow=1, domain_rank=88))

    def test_top_level_keys(self):
        from apps.dashboard.services.backlinks_service import build_backlinks_response
        body = build_backlinks_response("sc-domain:fusehealth.com")
        for key in ["kpis", "links", "summary", "months", "types", "asBuckets",
                    "refDomains", "anchors", "competitors", "gapDomains"]:
            self.assertIn(key, body)

    def test_kpis_and_links_are_real(self):
        from apps.dashboard.services.backlinks_service import build_backlinks_response
        body = build_backlinks_response("sc-domain:fusehealth.com")
        self.assertEqual(body["kpis"]["total"], 1)
        self.assertEqual(body["links"][0]["domain"], "healthline.com")

    def test_unbuilt_fields_report_setup_not_fake_data(self):
        from apps.dashboard.services.backlinks_service import build_backlinks_response
        body = build_backlinks_response("sc-domain:fusehealth.com")
        # summary is REAL now (it used to be hardcoded {"state": "setup"}, which made the SPA
        # hide the entire Backlinks page -- even after a successful backlinks sync).
        self.assertNotEqual(body["summary"], {"state": "setup"})
        self.assertEqual(body["summary"]["backlinks"], body["kpis"]["total"])
        self.assertEqual(body["summary"]["refDomains"], body["kpis"]["referring_domains"])
        # Genuinely no data source for these -- must stay empty, never fabricated.
        self.assertEqual(body["months"], [])       # no backlink history table
        self.assertEqual(body["types"], [])        # link types aren't captured
        self.assertEqual(body["asBuckets"], [])
        self.assertEqual(body["anchors"], [])      # needs an anchor-rollup connector
        self.assertEqual(body["gapDomains"], [])   # needs a domain-intersection connector

        # refDomains IS real now -- rolled up from the actual Backlink rows.
        self.assertEqual(len(body["refDomains"]), 1)
        self.assertEqual(body["refDomains"][0]["domain"], "healthline.com")
        self.assertEqual(body["refDomains"][0]["backlinks"], 1)

    def test_competitors_uses_real_tracked_list(self):
        from unittest import mock
        from apps.dashboard.services import backlinks_service
        with mock.patch.object(backlinks_service, "get_tracked_competitors", return_value=["driphydration.com"]):
            body = backlinks_service.build_backlinks_response("sc-domain:fusehealth.com")
            self.assertEqual(body["competitors"], ["driphydration.com"])
