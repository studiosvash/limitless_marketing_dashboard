import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, KeywordRanking, SavedKeyword
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class PositionsEndpointTests(APITestCase):
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
            session.add(Site(site_url="sc-domain:fusehealth.com", site_name="FuseHealth",
                              slug="fusehealth", is_active=1))
            session.add(SavedKeyword(site_id="sc-domain:fusehealth.com", keyword="iv therapy"))
            session.add(KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                        keyword="iv therapy", position=2, clicks=40,
                                        impressions=500, search_volume=3000, intent="commercial",
                                        url="/iv-therapy"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_positions_returns_all_required_keys_with_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/positions", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "distribution", "movement", "competitors", "movers", "rankings", "keywords"]:
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["tracked"], 1)
        self.assertEqual(body["rankings"][0]["kw"], "iv therapy")

    def test_range_defaults_to_30d(self):
        resp = self.client_auth.get("/api/projects/fusehealth/positions")
        self.assertEqual(resp.status_code, 200)

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/positions")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/positions")
        self.assertEqual(resp.status_code, 401)


class RankAnchorTests(APITestCase):
    """A freshly measured SERP position must be inside the window that displays it.

    THE BUG. `latest_data_anchor` reads the two GSC TRAFFIC tables, and
    `range_to_period_dates` ends the window at `anchor - 1 day` because Search Console's last
    day is partial. Search Console also lags ~3 days, so the window ends around today-4.
    `dataforseo_serp` stamps its rows with `yesterday()` — today-1. A rank measured by the
    refresh the user just watched succeed was therefore ~3 days NEWER than the end of its own
    window, every single time, so the page never changed. Not intermittent: no DataForSEO rank
    could EVER be displayed.

    It hid behind `gsc_keywords`, which writes a row per day across the whole window and so
    always had something inside it — and behind the fact that `dataforseo_serp` had never run
    at all (its entry in sync_engine's connector_map named a class that does not exist).

    Seeded here the way production looks: GSC traffic several days stale, one rank row from
    yesterday.
    """

    def setUp(self):
        from datetime import timedelta
        from pipeline.db.schema import SEODailyTotal

        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.today = date.today()
        self.gsc_day = self.today - timedelta(days=4)    # GSC lag
        self.rank_day = self.today - timedelta(days=1)   # what dataforseo_serp stamps

        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location="United States - Washington, DC",
                             is_active=1))
            session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1,
                                     keyword="event staffing",
                                     location="United States - Washington, DC"))
            session.add(SEODailyTotal(date=self.gsc_day, site_id="premierstaff.com",
                                      clicks=10, impressions=100))
            session.add(KeywordRanking(
                date=self.rank_day, site_id="premierstaff.com", keyword="event staffing",
                location="United States - Washington, DC", position=7, clicks=0,
                impressions=0, search_volume=2400))

        user = get_user_model().objects.create_user("anchoruser", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_yesterdays_rank_is_visible_on_the_positions_page(self):
        resp = self.client_auth.get("/api/projects/staff-dc/positions", {"range": "28d"})
        self.assertEqual(resp.status_code, 200)
        rows = {r["kw"]: r for r in resp.json()["rankings"]}
        self.assertIn("event staffing", rows)
        self.assertEqual(
            rows["event staffing"]["pos"], 7,
            "the rank measured yesterday fell outside the window — the GSC-lagged anchor is "
            "back and no DataForSEO measurement can be displayed",
        )

    def test_the_gsc_anchor_alone_would_have_excluded_it(self):
        """Pins the cause, so a future 'simplification' back to one anchor fails here."""
        from apps.api.views import latest_data_anchor, latest_ranking_anchor, range_to_period_dates

        gsc_only = range_to_period_dates("28d", latest_data_anchor("premierstaff.com"))
        self.assertLess(gsc_only[1], self.rank_day,
                        "fixture no longer reproduces the lag this test exists for")

        rank_anchor = latest_ranking_anchor("premierstaff.com",
                                            "United States - Washington, DC")
        widened = range_to_period_dates("28d", rank_anchor)
        self.assertGreaterEqual(widened[1], self.rank_day)

    def test_a_siblings_newer_sync_does_not_move_this_projects_window(self):
        """The anchor is location-scoped: several projects share one site_url, and a sibling
        measured in another market must not drag this project's window past its own data."""
        from datetime import timedelta
        from apps.api.views import latest_ranking_anchor

        with get_session() as session:
            session.add(KeywordRanking(
                date=self.today, site_id="premierstaff.com", keyword="event staffing",
                location="United States - New York", position=3, clicks=0, impressions=0))
            session.commit()

        dc = latest_ranking_anchor("premierstaff.com", "United States - Washington, DC")
        self.assertEqual(dc, self.rank_day + timedelta(days=1),
                         "the New York row leaked into the DC project's anchor")


class MeasuredVsUnrankedTests(APITestCase):
    """A keyword that was measured and does not rank is NOT "Not Tracked Yet".

    `position IS NULL` meant two different things and nothing could tell them apart:

        never rank-checked          -> belongs in "Newly Added Keywords — Not Tracked Yet"
        checked, outside the top 30 -> a real measurement; belongs in Rankings Overview

    So a user who ran Fetch Positions, watched it succeed and paid for it saw the same three
    keywords sitting in the "no captured position yet" card, above a button offering to buy
    the measurement again. `keyword_rankings.rank_checked_at` makes it a recorded fact:
    written by the rank connectors (`dataforseo_serp` even when the domain is not in the top
    30, `gsc_keywords` because a query row means the page was served), never by
    `dataforseo_keywords`, which only prices a keyword.
    """

    def setUp(self):
        from datetime import timedelta

        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.day = date.today() - timedelta(days=1)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location="United States - Washington, DC",
                             is_active=1))
            for kw in ("ranks well", "measured but unranked", "never checked"):
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location="United States - Washington, DC"))
            # Found at #4.
            session.add(KeywordRanking(
                date=self.day, site_id="premierstaff.com", keyword="ranks well",
                location="United States - Washington, DC", position=4,
                search_volume=900, rank_checked_at=self.day))
            # dataforseo_serp looked and the domain was not in the top 30: a real result.
            session.add(KeywordRanking(
                date=self.day, site_id="premierstaff.com", keyword="measured but unranked",
                location="United States - Washington, DC", position=None,
                search_volume=6600, rank_checked_at=self.day))
            # dataforseo_keywords priced it; no rank connector has ever looked.
            session.add(KeywordRanking(
                date=self.day, site_id="premierstaff.com", keyword="never checked",
                location="United States - Washington, DC", position=None,
                search_volume=480, rank_checked_at=None))

        user = get_user_model().objects.create_user("measureduser", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def _rows(self):
        resp = self.client_auth.get("/api/projects/staff-dc/positions", {"range": "28d"})
        self.assertEqual(resp.status_code, 200)
        return resp.json(), {r["kw"]: r for r in resp.json()["rankings"]}

    def test_measured_but_unranked_is_measured(self):
        _, rows = self._rows()
        row = rows["measured but unranked"]
        self.assertTrue(row["measured"],
                        "a checked keyword outside the top 30 is a real measurement")
        self.assertIsNone(row["pos"], "and it must still report no position, never a fake one")

    def test_never_checked_is_not_measured(self):
        _, rows = self._rows()
        self.assertFalse(rows["never checked"]["measured"],
                         "a volume-only row is not a rank measurement")

    def test_a_captured_position_is_measured(self):
        _, rows = self._rows()
        self.assertTrue(rows["ranks well"]["measured"])
        self.assertEqual(rows["ranks well"]["pos"], 4)

    def test_only_the_unchecked_keyword_lands_in_the_new_card(self):
        """The split the SPA performs: `measured` decides the card, `pos` decides the cell."""
        _, rows = self._rows()
        unmeasured = sorted(k for k, r in rows.items() if not r["measured"])
        self.assertEqual(unmeasured, ["never checked"])

    def test_the_competitor_grid_keeps_measured_unranked_keywords(self):
        """The grid used to hide every row whose own position was null — dropping exactly the
        keywords where a competitor ranks and you do not, which is the gap it exists to show."""
        body, _ = self._rows()
        grid = {r["kw"]: r for r in body["competitors"]["rows"]}
        self.assertTrue(grid["measured but unranked"]["you"]["measured"])
        self.assertFalse(grid["never checked"]["you"]["measured"])


class BackfillUsesRankCheckedAtTests(APITestCase):
    """`keywords_needing_backfill` must not re-buy a keyword already measured as unranked.

    It used to infer "has a rank connector run?" from `position IS NOT NULL OR impressions > 0`,
    which cannot see a measured "not in the top 30" — so every genuinely unranked keyword was
    re-queried on every incremental sync, and paid for again each time.
    """

    def setUp(self):
        from datetime import timedelta

        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.day = date.today() - timedelta(days=1)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", slug="staff-dc",
                             location="United States - Washington, DC", is_active=1))
            for kw in ("checked unranked", "never checked"):
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location="United States - Washington, DC"))
            session.add(KeywordRanking(
                date=self.day, site_id="premierstaff.com", keyword="checked unranked",
                location="United States - Washington, DC", position=None,
                search_volume=6600, rank_checked_at=self.day))
            session.add(KeywordRanking(
                date=self.day, site_id="premierstaff.com", keyword="never checked",
                location="United States - Washington, DC", position=None,
                search_volume=480, rank_checked_at=None))

    def test_only_the_unchecked_keyword_needs_work(self):
        from pipeline.utils.keywords import keywords_needing_backfill

        outstanding = keywords_needing_backfill(
            "premierstaff.com", site_pk=1, location="United States - Washington, DC")
        self.assertEqual(outstanding, ["never checked"],
                         "a measured-unranked keyword must not be bought again")
