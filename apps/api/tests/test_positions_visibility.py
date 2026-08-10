"""One visibility number, wherever it is read from (C1).

THE BUG. Three formulas answered the question "how visible is this project?":

  1. The projects LIST  — `shared_queries._get_ranking_distribution`'s CTR-credit score, over a
     window `ProjectSerializer._pos_summary` built from `date.today() - 28`.
  2. The project OVERVIEW card — recomputed IN THE BROWSER from `data.competitors.rows`, which
     `_get_competitor_grid` builds from a SINGLE latest capture date with integer-rounded
     positions, ignoring the requested range entirely.
  3. `build_positions_response` itself, which COMPUTED `dist["visibility"]` and then dropped it
     on the floor — it was never in the returned `kpis`.

So the same project showed two different visibility percentages on two screens, and the number
the backend actually computed for the page was the one nobody could see. The wall-clock window
in (1) is the sharpest edge: a project last synced 40 days ago has no rankings inside
`today - 28`, so its list row reported "—" (never captured) while its own workspace, which
re-anchors on the newest measurement via `latest_ranking_anchor`, reported a real score.
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
from pipeline.db.schema import KeywordRanking, SavedKeyword, Site, init_db
from pipeline.utils.db_connection import get_session

LOCATION = "United States - Washington, DC"


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


class StaleProjectVisibilityTests(_Fixture):
    """A project last measured 40 days ago must report the SAME number on both surfaces."""

    def setUp(self):
        self._open_db()
        # Deliberately older than the 28-day wall-clock window the serializer used to build.
        self.rank_day = date.today() - timedelta(days=40)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location=LOCATION, is_active=1))
            for kw in ("event staffing", "brand ambassadors", "trade show models"):
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location=LOCATION))
            # One keyword ranks at #2, one at #14, one was measured and does not rank.
            session.add(KeywordRanking(date=self.rank_day, site_id="premierstaff.com",
                                       keyword="event staffing", location=LOCATION,
                                       position=2, rank_checked_at=self.rank_day))
            session.add(KeywordRanking(date=self.rank_day, site_id="premierstaff.com",
                                       keyword="brand ambassadors", location=LOCATION,
                                       position=14, rank_checked_at=self.rank_day))
            session.add(KeywordRanking(date=self.rank_day, site_id="premierstaff.com",
                                       keyword="trade show models", location=LOCATION,
                                       position=None, rank_checked_at=self.rank_day))
        self.client_auth = self._auth("visuser")

    def test_positions_kpis_carry_the_visibility_the_backend_computed(self):
        body = self.client_auth.get("/api/projects/staff-dc/positions",
                                    {"range": "28d"}).json()
        self.assertIn("visibility", body["kpis"],
                      "build_positions_response computes dist['visibility'] and must return it")
        self.assertIsNotNone(body["kpis"]["visibility"],
                             "three tracked keywords were measured — this is not 'never captured'")
        # #2 = 24.7 CTR points, #14 = 0.9, unranked = 0, over 3 keywords x 31.7 perfect.
        self.assertAlmostEqual(body["kpis"]["visibility"], 26.9, places=1)

    def test_the_project_list_reports_the_same_number(self):
        listed = self.client_auth.get("/api/projects").json()
        row = next(p for p in listed if p["id"] == "staff-dc")
        positions = self.client_auth.get("/api/projects/staff-dc/positions",
                                         {"range": "28d"}).json()
        self.assertEqual(
            row["visibility"], positions["kpis"]["visibility"],
            "the list anchored on wall-clock today-28 and the workspace on the newest "
            "measurement, so one screen said '—' and the other said 26.9%",
        )

    def test_the_list_does_not_report_a_stale_project_as_never_captured(self):
        listed = self.client_auth.get("/api/projects").json()
        row = next(p for p in listed if p["id"] == "staff-dc")
        self.assertIsNotNone(
            row["visibility"],
            "null means 'never captured'; this project was captured, 40 days ago",
        )


class NoMeasurementVisibilityTests(_Fixture):
    """Nothing measured is `null` on BOTH surfaces — never a fabricated 0."""

    def setUp(self):
        self._open_db()
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff NY",
                             slug="staff-ny", location="United States - New York", is_active=1))
            session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1,
                                     keyword="event staffing",
                                     location="United States - New York"))
        self.client_auth = self._auth("nullvisuser")

    def test_positions_visibility_is_null(self):
        body = self.client_auth.get("/api/projects/staff-ny/positions").json()
        self.assertIsNone(body["kpis"]["visibility"])

    def test_project_list_visibility_is_null(self):
        listed = self.client_auth.get("/api/projects").json()
        row = next(p for p in listed if p["id"] == "staff-ny")
        self.assertIsNone(row["visibility"])
