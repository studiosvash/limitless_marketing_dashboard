"""Keyword volume / KD / CPC are bought at most once per VOLUME_FRESH_DAYS per keyword
(2026-09-01).

`dataforseo_keywords` runs inside every positions run, so a weekly city refresh re-bought
volume for all 21 keywords every week — $6.37 of $25 over 90 days — for a number Google
itself updates monthly. A keyword priced within the window is carried forward into today's
row instead (no API call), so every reader that takes the newest row still sees a volume;
a keyword never priced, or priced too long ago, is fetched as before.
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from django.test import TestCase, override_settings
from sqlalchemy import select

import pipeline.utils.db_connection as db_connection
from pipeline.connectors import dataforseo_keywords as kw_mod
from pipeline.db.engine import get_engine
from pipeline.db.schema import KeywordRanking, init_db
from pipeline.utils.db_connection import get_session

SITE = "premierstaff.com"
LOC = "United States - Charlotte, NC"


class VolumeFreshnessTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        db_connection._SessionFactory = None

        today = date.today()
        with get_session() as session:
            session.add_all([
                # priced 10 days ago -> fresh, carried forward
                KeywordRanking(date=today - timedelta(days=10), site_id=SITE, location=LOC,
                               keyword="event staffing", search_volume=880,
                               keyword_difficulty=31.0, cpc=4.2, trend="[800,880]"),
                # priced 40 days ago -> stale, re-bought
                KeywordRanking(date=today - timedelta(days=40), site_id=SITE, location=LOC,
                               keyword="stadium staffing", search_volume=210),
                # rank-checked 10 days ago but never priced -> bought
                KeywordRanking(date=today - timedelta(days=10), site_id=SITE, location=LOC,
                               keyword="usher staffing", position=7, search_volume=None),
                # fresh, but for ANOTHER city -> this project still buys its own
                KeywordRanking(date=today - timedelta(days=2), site_id=SITE,
                               location="United States - Houston, TX",
                               keyword="trade show staffing", search_volume=500),
            ])
            session.commit()

    def _connector(self):
        with mock.patch.dict("os.environ", {"DATAFORSEO_LOGIN": "l", "DATAFORSEO_PASSWORD": "p"}):
            c = kw_mod.DataForSEOKeywordsConnector()
        return c

    def _fetch(self, keywords):
        c = self._connector()
        volume = mock.Mock(side_effect=lambda kws, loc: [
            {"keyword": k, "search_volume": 999, "cpc": 1.0, "monthly_searches": []} for k in kws])
        with mock.patch.object(c, "_resolve_site_id", return_value=SITE), \
             mock.patch.object(c, "_resolve_location", return_value=LOC), \
             mock.patch.object(c, "_load_keywords", return_value=keywords), \
             mock.patch.object(c, "_fetch_search_volume", volume), \
             mock.patch.object(c, "_fetch_keyword_difficulty", return_value={}), \
             mock.patch.object(kw_mod, "record_cost"):
            records = c.fetch(SITE)
        return records, volume

    def test_window_is_thirty_days(self):
        self.assertEqual(kw_mod.VOLUME_FRESH_DAYS, 30)

    def test_only_stale_or_unpriced_keywords_reach_the_api(self):
        _, volume = self._fetch(["event staffing", "stadium staffing", "usher staffing",
                                 "trade show staffing"])
        sent = sorted(volume.call_args.args[0])
        self.assertEqual(sent, ["stadium staffing", "trade show staffing", "usher staffing"])

    def test_a_fresh_keyword_is_carried_forward_into_todays_row(self):
        records, _ = self._fetch(["event staffing"])
        self.assertEqual(len(records), 1)
        row = records[0]
        self.assertEqual(row["keyword"], "event staffing")
        self.assertEqual(row["search_volume"], 880)
        self.assertEqual(row["keyword_difficulty"], 31.0)
        self.assertEqual(row["cpc"], 4.2)
        self.assertEqual(row["trend"], "[800,880]")
        self.assertEqual(row["date"], kw_mod.yesterday())

    def test_nothing_stale_means_no_api_call_at_all(self):
        _, volume = self._fetch(["event staffing"])
        volume.assert_not_called()

    def test_bought_and_carried_rows_come_back_together(self):
        records, _ = self._fetch(["event staffing", "stadium staffing"])
        by_kw = {r["keyword"]: r["search_volume"] for r in records}
        self.assertEqual(by_kw, {"event staffing": 880, "stadium staffing": 999})
