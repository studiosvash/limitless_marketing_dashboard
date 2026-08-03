"""GSC incremental cursor — regression for the permanently-zero Overview.

`seo_daily` is a SHARED table: the `gsc` connector owns the search columns
(clicks/impressions/ctr/avg_position) and the `ga4` connector owns the analytics columns
(sessions/pageviews/...). GA4 writes its rows with the search columns left at 0.

GSC's incremental fetch asked "what is the newest date in seo_daily for this site?" without
distinguishing whose rows those were. GA4's window ends *yesterday*; GSC's safe window ends
*today − 3* (GSC lags 3 days). So the moment GA4 ran even once, GSC computed
`new_start = yesterday + 1 > new_end = today - 3`, logged "No new dates to fetch" and
returned `[]` — forever. The connector reported `status=success, records=0` on every run, so
nothing surfaced as broken, while every GSC number on the Overview page stayed 0.

Observed on production 2026-07-30 (premierstaff.com): `ga4` wrote 18 324 records, `gsc` wrote
0, and every seo_daily row carried clicks=0/impressions=0 while `keyword_rankings` (written by
the separate `gsc_keywords` connector, which has its own cursor) held real GSC clicks.

The cursor must therefore count only dates GSC itself has written. `impressions > 0` is that
test exactly: the Search Analytics API only returns a row because the page was *served*, so
every GSC row has impressions >= 1, and a GA4-only row has impressions = 0 by construction
(see ga4._normalize).
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from pipeline.connectors.gsc import GSCConnector
from pipeline.db.engine import get_engine
from pipeline.db.schema import SEODaily, Site, init_db
from pipeline.utils.date_helpers import gsc_safe_range, iso
from pipeline.utils.db_connection import get_session

SITE = "example.com"


class GscIncrementalCursorTests(TestCase):
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
            session.add(Site(site_url=SITE, slug="example", is_active=1,
                             gsc_property=f"sc-domain:{SITE}"))

        self.connector = GSCConnector()
        # _resolve_site would call the live GSC API to auto-match the property; the property
        # string is not what this test is about.
        self.connector._resolve_site = lambda site_id: f"sc-domain:{SITE}"
        self.requested = []

        def record(site_url, start_str, end_str):
            self.requested.append((start_str, end_str))
            return []

        self.connector._fetch_date_range = record

        # The daily-totals call is a second, independent request to the same API. It has its
        # own window (it re-reads past the cursor by RESTATEMENT_DAYS) and would otherwise go
        # out over the network from these tests. Recorded separately so asserting on
        # `self.requested` still describes only the breakdown cursor this class is about.
        self.totals_requested = []

        def record_totals(site_url, canonical, start_str, end_str):
            self.totals_requested.append((start_str, end_str))
            return []

        self.connector._fetch_totals = record_totals

    def _seed(self, day: date, *, impressions: int, sessions: int):
        with get_session() as session:
            session.add(SEODaily(date=day, site_id=SITE, country="USA", device="mobile",
                                 landing_page=f"https://{SITE}/", clicks=0,
                                 impressions=impressions, ctr=0.0, avg_position=0.0,
                                 sessions=sessions))
            session.commit()

    def test_ga4_only_rows_do_not_advance_the_gsc_cursor(self):
        """GA4 rows reaching yesterday must not convince GSC it is already up to date."""
        today = date.today()
        for back in range(1, 61):                       # GA4's window: 60 days ending yesterday
            self._seed(today - timedelta(days=back), impressions=0, sessions=12)

        self.connector.fetch(site_id=SITE)

        expected_start, expected_end = gsc_safe_range(90)
        self.assertEqual(
            self.requested, [(expected_start, expected_end)],
            "GSC must still fetch its full window when the only rows present are GA4's",
        )

    def test_gsc_rows_do_advance_the_cursor(self):
        """A real GSC row still makes the next fetch incremental — the optimisation stays."""
        last_gsc_day = date.today() - timedelta(days=10)
        self._seed(last_gsc_day, impressions=940, sessions=0)

        self.connector.fetch(site_id=SITE)

        _, expected_end = gsc_safe_range(90)
        self.assertEqual(self.requested, [(iso(last_gsc_day + timedelta(days=1)), expected_end)])

    def test_gsc_rows_win_over_newer_ga4_rows(self):
        """Mixed table: the cursor follows the newest GSC row, not the newest row overall."""
        today = date.today()
        last_gsc_day = today - timedelta(days=10)
        self._seed(last_gsc_day, impressions=940, sessions=0)
        for back in range(1, 10):
            self._seed(today - timedelta(days=back), impressions=0, sessions=12)

        self.connector.fetch(site_id=SITE)

        _, expected_end = gsc_safe_range(90)
        self.assertEqual(self.requested, [(iso(last_gsc_day + timedelta(days=1)), expected_end)])
