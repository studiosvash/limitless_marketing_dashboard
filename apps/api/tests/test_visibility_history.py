"""The Positioning → Overview visibility trend, and the list/workspace range agreement.

TWO BUGS, one card.

1. THE CHART COULD NEVER RENDER. `positioning.js` hardcoded `hasHistory: false` with an empty
   `series`, so "No visibility history yet" was the only reachable state of the card whatever
   the database held. Behind it, nothing supplied history either: `/api/positions` returned no
   history field, and `competitor_visibility` is a table whose writer
   (`pipeline/db/writer.upsert_competitor_visibility`) has never had a single call site. The
   history was in the database the whole time — `keyword_rankings` and
   `competitor_keyword_rankings` are both keyed per date and accumulate a row per capture — so
   `_get_visibility_history` scores the dates that were already stored rather than starting a
   fresh snapshot log that would leave the chart empty for another two syncs.

2. THE LIST AND THE WORKSPACE DISAGREED ON ANY RANGE BUT 28d. `ProjectSerializer._pos_summary`
   hardcoded a 28-day window while `ProjectPositionsView` honours `?range=`. Selecting 7d moved
   "Your visibility" in the workspace and left the list's Visibility column on its 28-day
   reading — one project, two percentages, neither labelled with its window. (The wall-clock
   half of this was fixed earlier; see test_positions_visibility.py. This is the range half.)
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import (
    CompetitorKeywordRanking, KeywordRanking, SavedKeyword, Site, TrackedCompetitor, init_db,
)
from pipeline.utils.db_connection import get_session

LOCATION = "United States - Washington, DC"
KEYWORDS = ("event staffing", "brand ambassadors", "trade show models")


class _Fixture(APITestCase):
    """Analytics-DB fixture (skills.md §8) plus an authenticated client."""

    def _open_db(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def _auth(self, username):
        user = get_user_model().objects.create_user(username, password="x")
        token = Token.objects.get(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        return client


class VisibilityHistoryTests(_Fixture):
    """Two capture dates, seven days apart, and one competitor measured on only the newer.

    Positions are chosen so every expected figure is exact. Semrush credit curve
    (_SEMRUSH_CREDIT; #1 = 1.0 per keyword, perfect = 1.0 each):

      day_a: #5 -> 0.167582, #14 -> 0.035714, unranked -> 0  = 0.203296 / 3 = 6.8%
      day_b: #3 -> 0.260990, #10 -> 0.060439, unranked -> 0  = 0.321429 / 3 = 10.7%
      headline = snapshot of each keyword's latest = day_b's reading = 10.7%
    """

    def setUp(self):
        self._open_db()
        self.day_b = date.today() - timedelta(days=5)
        self.day_a = self.day_b - timedelta(days=7)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location=LOCATION, is_active=1))
            for kw in KEYWORDS:
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location=LOCATION))
            for day, best, mid in ((self.day_a, 5, 14), (self.day_b, 3, 10)):
                session.add(KeywordRanking(date=day, site_id="premierstaff.com",
                                           keyword="event staffing", location=LOCATION,
                                           position=best, rank_checked_at=day))
                session.add(KeywordRanking(date=day, site_id="premierstaff.com",
                                           keyword="brand ambassadors", location=LOCATION,
                                           position=mid, rank_checked_at=day))
                # Measured and ranks nowhere — earns 0 but keeps its place in the denominator.
                session.add(KeywordRanking(date=day, site_id="premierstaff.com",
                                           keyword="trade show models", location=LOCATION,
                                           position=None, rank_checked_at=day))
            session.add(TrackedCompetitor(site_id="premierstaff.com", site_pk=1,
                                          competitor_domain="eventstaff.com"))
            # The competitor sync only landed on the newer date.
            session.add(CompetitorKeywordRanking(date=self.day_b, site_id="premierstaff.com",
                                                 keyword="event staffing", location=LOCATION,
                                                 competitor_domain="eventstaff.com", position=3))
        self.client_auth = self._auth("histuser")

    def _history(self, range_key="28d"):
        body = self.client_auth.get("/api/projects/staff-dc/positions",
                                    {"range": range_key}).json()
        return body["visibility_history"], body

    def test_the_response_carries_a_history_at_all(self):
        hist, _ = self._history()
        self.assertEqual(hist["dates"],
                         [self.day_a.isoformat(), self.day_b.isoformat()],
                         "one point per date actually captured, oldest first")

    def test_your_own_series_is_the_per_date_index_and_the_headline_is_its_last_point(self):
        hist, body = self._history()
        own = next(s for s in hist["series"] if s["own"])
        self.assertEqual(own["domain"], "premierstaff.com",
                         "keyed by the same bare domain the legend and the cards use")
        self.assertEqual([round(p, 1) for p in own["points"]], [6.8, 10.7])
        # Since 2026-08-13 (tech lead: match Semrush) the headline is a SNAPSHOT of each
        # keyword's latest measurement — exactly Semrush's landscape, where the big number
        # is today's reading and the chart is its history. So the headline must EQUAL the
        # newest chart point.
        self.assertAlmostEqual(body["kpis"]["visibility"], 10.7, places=1)
        self.assertAlmostEqual(body["kpis"]["visibility"], own["points"][-1], places=1,
                               msg="the headline is the trend's latest point, by definition")

    def test_a_competitor_measured_on_one_date_only_is_null_on_the_other(self):
        hist, _ = self._history()
        comp = next(s for s in hist["series"] if s["domain"] == "eventstaff.com")
        self.assertIsNone(comp["points"][0],
                          "nobody measured this domain that day — 0 would draw a cliff "
                          "nobody observed")
        # #3 on 1 of 3 tracked keywords: 0.260990 / 3 = 8.7 on the Semrush credit curve.
        self.assertAlmostEqual(comp["points"][1], 8.7, places=1)

    def test_the_denominator_is_the_whole_tracked_list(self):
        hist, _ = self._history()
        self.assertEqual(hist["tracked_total"], len(KEYWORDS))

    def test_a_narrower_range_drops_the_older_capture(self):
        """7d ends on the newest capture, so the older one falls outside it and there is
        nothing left to draw a line between — the empty state is a real outcome, not a
        hardcoded one."""
        hist, _ = self._history("7d")
        self.assertEqual(hist["dates"], [self.day_b.isoformat()])


class IncrementalCaptureTests(_Fixture):
    """A `positions_new` run must not put a crash on the chart.

    That sync scope deliberately measures ONLY keywords never measured before, so it writes a
    date holding a handful of rows out of the whole tracked list. The denominator is the full
    list (features.md's trap: a per-day denominator would report sync coverage as performance),
    which means an incremental date scored naively plots near zero — a cliff caused by the user
    pressing "Track These New Keywords", not by anything Google did.
    """

    def setUp(self):
        self._open_db()
        self.full_day = date.today() - timedelta(days=9)
        self.incremental_day = date.today() - timedelta(days=4)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location=LOCATION, is_active=1))
            for kw in KEYWORDS + ("catering staff", "promo models", "brand hosts"):
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location=LOCATION))
            # A full sync: every tracked keyword measured, most of them ranking well.
            for kw in KEYWORDS + ("catering staff", "promo models", "brand hosts"):
                session.add(KeywordRanking(date=self.full_day, site_id="premierstaff.com",
                                           keyword=kw, location=LOCATION, position=3,
                                           rank_checked_at=self.full_day))
            # An incremental run five days later: one keyword, and it happens to rank badly.
            session.add(KeywordRanking(date=self.incremental_day, site_id="premierstaff.com",
                                       keyword="brand hosts", location=LOCATION, position=40,
                                       rank_checked_at=self.incremental_day))
        self.client_auth = self._auth("incruser")

    def test_the_incremental_date_is_not_plotted(self):
        body = self.client_auth.get("/api/projects/staff-dc/positions",
                                    {"range": "28d"}).json()
        hist = body["visibility_history"]
        self.assertEqual(hist["dates"], [self.full_day.isoformat()],
                         "1 keyword out of 6 is an incremental capture, not a reading of the "
                         "whole board — plotting it draws a crash nobody measured")

    def test_a_full_recapture_is_still_plotted_even_when_it_is_bad_news(self):
        """The guard is about COVERAGE, not about hiding declines. A second full capture that
        genuinely collapsed must appear."""
        with get_session() as session:
            # "brand hosts" already has a row on this date from the incremental run — the
            # unique key is (date, site_id, keyword, location), so only the other five land.
            for kw in KEYWORDS + ("catering staff", "promo models"):
                session.add(KeywordRanking(date=self.incremental_day, site_id="premierstaff.com",
                                           keyword=kw, location=LOCATION, position=60,
                                           rank_checked_at=self.incremental_day))
        body = self.client_auth.get("/api/projects/staff-dc/positions",
                                    {"range": "28d"}).json()
        hist = body["visibility_history"]
        self.assertEqual(hist["dates"],
                         [self.full_day.isoformat(), self.incremental_day.isoformat()])
        own = next(s for s in hist["series"] if s["own"])
        self.assertGreater(own["points"][0], own["points"][1])
        self.assertEqual(own["measured"], [6, 6])


class NoHistoryTests(_Fixture):
    """Never measured: an empty history, not a fabricated series."""

    def setUp(self):
        self._open_db()
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff NY",
                             slug="staff-ny", location="United States - New York", is_active=1))
            session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1,
                                     keyword="event staffing",
                                     location="United States - New York"))
        self.client_auth = self._auth("nohistuser")

    def test_history_is_empty_rather_than_invented(self):
        body = self.client_auth.get("/api/projects/staff-ny/positions").json()
        self.assertEqual(body["visibility_history"]["dates"], [])
        self.assertEqual(body["visibility_history"]["series"], [])


class ListRangeAgreementTests(_Fixture):
    """The list's Visibility column and the workspace figure, on the SAME range."""

    def setUp(self):
        self._open_db()
        self.day_b = date.today() - timedelta(days=5)
        self.day_a = self.day_b - timedelta(days=7)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location=LOCATION, is_active=1))
            for kw in KEYWORDS:
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location=LOCATION))
            for day, best, mid in ((self.day_a, 5, 14), (self.day_b, 3, 10)):
                session.add(KeywordRanking(date=day, site_id="premierstaff.com",
                                           keyword="event staffing", location=LOCATION,
                                           position=best, rank_checked_at=day))
                session.add(KeywordRanking(date=day, site_id="premierstaff.com",
                                           keyword="brand ambassadors", location=LOCATION,
                                           position=mid, rank_checked_at=day))
        self.client_auth = self._auth("rangeuser")

    def _row(self, range_key=None):
        params = {"range": range_key} if range_key else {}
        listed = self.client_auth.get("/api/projects", params).json()
        return next(p for p in listed if p["id"] == "staff-dc")

    def _workspace(self, range_key):
        return self.client_auth.get("/api/projects/staff-dc/positions",
                                    {"range": range_key}).json()["kpis"]["visibility"]

    def test_the_two_surfaces_agree_on_every_range(self):
        for range_key in ("7d", "28d", "90d"):
            with self.subTest(range=range_key):
                self.assertEqual(self._row(range_key)["visibility"],
                                 self._workspace(range_key))

    def test_the_range_does_not_move_the_visibility_number(self):
        """Inverted on 2026-08-13 (tech lead: match Semrush). Visibility is now a snapshot
        of each keyword's LATEST measurement, so the range selector must NOT move it — in
        Semrush, switching the date range moves the diff and the chart, never today's
        reading. This test used to assert the opposite (7d != 28d) back when the number was
        a window average; if these ever differ again, the average has crept back in."""
        self.assertEqual(self._row("7d")["visibility"], self._row("28d")["visibility"])
        self.assertEqual(self._row("28d")["visibility"], self._row("90d")["visibility"])

    def test_a_caller_that_sends_no_range_still_gets_the_28d_reading(self):
        self.assertEqual(self._row()["visibility"], self._row("28d")["visibility"])
