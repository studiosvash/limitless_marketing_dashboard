"""The competitor DOMAIN list is bought at most once per COMPETITORS_FRESH_DAYS per domain
(2026-09-01).

`competitor_domains` is keyed (site_id, competitor_domain) — one list per DOMAIN — yet the
connector ran inside every city project's positions run, so 18 premierstaff.com projects
re-bought and overwrote the same 25 rows every week. A list fetched within the window is
returned as-is (no API call, no spend event); an older one is refreshed as before.
"""
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from pipeline.connectors import dataforseo_labs_competitors as labs_mod
from pipeline.db.engine import get_engine
from pipeline.db.schema import CompetitorDomain, init_db
from pipeline.utils.db_connection import get_session

SITE = "premierstaff.com"


class CompetitorListFreshnessTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        db_connection._SessionFactory = None

    def _seed(self, days_ago):
        stamp = datetime.now(timezone.utc) - timedelta(days=days_ago)
        with get_session() as session:
            session.add_all([
                CompetitorDomain(site_id=SITE, competitor_domain="eventstaff.com",
                                 intersections=12, etv=100.0, last_fetched=stamp),
                CompetitorDomain(site_id=SITE, competitor_domain="juliavaller.com",
                                 intersections=9, etv=50.0, last_fetched=stamp),
            ])
            session.commit()

    def _fetch(self):
        with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l", "DATAFORSEO_PASSWORD": "p"}):
            c = labs_mod.DataForSEOLabsCompetitorsConnector()
        call = mock.Mock(return_value=[{"domain": "fresh.com", "intersections": 1,
                                        "metrics": {"organic": {"etv": 1.0}}}])
        with mock.patch.object(c, "_resolve", return_value=(SITE, "premierstaff.com")), \
             mock.patch.object(c, "_call", call), \
             mock.patch.object(labs_mod, "record_cost"):
            records = c.fetch(SITE)
        return records, call

    def test_window_is_seven_days(self):
        self.assertEqual(labs_mod.COMPETITORS_FRESH_DAYS, 7)

    def test_a_list_fetched_two_days_ago_is_reused_without_an_api_call(self):
        self._seed(days_ago=2)
        records, call = self._fetch()
        call.assert_not_called()
        self.assertEqual(sorted(r["competitor_domain"] for r in records),
                         ["eventstaff.com", "juliavaller.com"])
        self.assertEqual(records[0]["site_id"], SITE)

    def test_a_list_fetched_eight_days_ago_is_refreshed(self):
        self._seed(days_ago=8)
        records, call = self._fetch()
        call.assert_called_once()
        self.assertEqual([r["competitor_domain"] for r in records], ["fresh.com"])

    def test_no_list_at_all_is_fetched(self):
        _, call = self._fetch()
        call.assert_called_once()
