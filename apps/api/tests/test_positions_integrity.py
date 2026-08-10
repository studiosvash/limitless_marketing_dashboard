"""Ranking-integrity fixes on the Positioning payload (P3, P4, P8, P10).

Each class states the bug it pins. The common thread is the rule this codebase keeps
relearning: an absent value is not a zero, and a number that looks real is worse than a gap.
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import KeywordRanking, SavedKeyword, Site, init_db
from pipeline.utils.db_connection import get_session

LOC = "United States - Washington, DC"


class OpportunityUnknownVolumeTests(TestCase):
    """`score_keyword_opportunities` fabricated a 0 for unknown volume, then printed it (P3).

    `int(row.get("search_volume") or 0)` turned "we have never looked this keyword up" into
    "this keyword gets zero searches a month", and the rationale then asserted it as fact:
    "volume 0/mo is 0% of your highest-volume tracked keyword". The SPA rendered the literal 0
    in the Volume column beside it.

    Worse, `if position is None and volume <= 0: continue` silently DROPPED every keyword with
    no position and no volume — which is exactly what a brand-new project consists of. The
    Opportunities card sat empty with no explanation of what had happened to the 12 keywords the
    user had just tracked.
    """

    def _rows(self):
        return [
            {"keyword": "known volume", "position": 8, "search_volume": 2400},
            {"keyword": "unknown volume", "position": 12, "search_volume": None},
            {"keyword": "genuinely zero", "position": 15, "search_volume": 0},
            {"keyword": "awaiting first measurement", "position": None, "search_volume": None},
        ]

    def test_unknown_volume_stays_none_and_is_never_scored_as_zero(self):
        from apps.dashboard.services.positioning_service import score_keyword_opportunities

        scored = {o["keyword"]: o for o in score_keyword_opportunities(self._rows())}
        self.assertIsNone(scored["unknown volume"]["volume"],
                          "None means unknown; 0 would claim nobody searches for it")
        self.assertEqual(scored["genuinely zero"]["volume"], 0,
                         "a stored 0 is a real DataForSEO answer and must survive as 0")

    def test_the_rationale_says_unknown_rather_than_asserting_zero(self):
        from apps.dashboard.services.positioning_service import score_keyword_opportunities

        scored = {o["keyword"]: o for o in score_keyword_opportunities(self._rows())}
        self.assertNotIn("volume 0/mo", scored["unknown volume"]["rationale"])
        self.assertIn("unknown", scored["unknown volume"]["rationale"].lower())
        self.assertIn("volume 0/mo", scored["genuinely zero"]["rationale"],
                      "a known zero is still stated as the fact it is")

    def test_an_unknown_volume_does_not_drag_the_score_to_the_floor(self):
        """Dropping the component and renormalising is the existing rule for an unknown KD."""
        from apps.dashboard.services.positioning_service import score_keyword_opportunities

        scored = {o["keyword"]: o for o in score_keyword_opportunities(self._rows())}
        self.assertGreater(scored["unknown volume"]["score"],
                           scored["genuinely zero"]["score"],
                           "a known 0 volume should score below an unknown one, not above it")

    def test_evidence_free_keywords_are_counted_not_silently_dropped(self):
        from apps.dashboard.services.positioning_service import (
            count_opportunities_awaiting_data, score_keyword_opportunities,
        )

        scored = [o["keyword"] for o in score_keyword_opportunities(self._rows())]
        self.assertNotIn("awaiting first measurement", scored,
                         "there is no evidence to score it on — still true")
        self.assertEqual(count_opportunities_awaiting_data(self._rows()), 1,
                         "but the card must be able to say so instead of just being short")


class PositionsIntegrityEndpointTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.day = date.today() - timedelta(days=1)
        self.prev_day = self.day - timedelta(days=30)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location=LOC, is_active=1))
            # Three measured (all top 10) and two the connector has never looked at.
            for kw in ("top a", "top b", "top c", "never measured a", "never measured b"):
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location=LOC))
            for kw, pos in (("top a", 2), ("top b", 5), ("top c", 9)):
                session.add(KeywordRanking(date=self.day, site_id="premierstaff.com",
                                           keyword=kw, location=LOC, position=pos,
                                           rank_checked_at=self.day))
            # "top a" was at #5 a month ago: a 3-place IMPROVEMENT.
            session.add(KeywordRanking(date=self.prev_day, site_id="premierstaff.com",
                                       keyword="top a", location=LOC, position=5,
                                       rank_checked_at=self.prev_day))
            # "top c" was at #6: a 3-place DECLINE — the case that rendered "▼-3".
            session.add(KeywordRanking(date=self.prev_day, site_id="premierstaff.com",
                                       keyword="top c", location=LOC, position=6,
                                       rank_checked_at=self.prev_day))

        user = get_user_model().objects.create_user("integrityuser", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def _body(self, rng="7d"):
        resp = self.client_auth.get("/api/projects/staff-dc/positions", {"range": rng})
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def test_never_measured_keywords_are_not_counted_as_positions_21_to_100(self):
        """P4. `dist["total"] - dist["top20"]` counted the tracked list's unmeasured rows.

        A project tracking 5 keywords with 3 measured, all top-10, rendered "21–100: 2" — two
        asserted measured positions that were never measured — while the same two rows appeared
        in the "Newly Added" card on the same screen as never measured.
        """
        dist = self._body()["distribution"]
        self.assertEqual(dist["p21_100"], 0,
                         "no keyword was measured outside the top 20")
        self.assertEqual(dist["unmeasured"], 2,
                         "the two never-measured keywords get their own honest segment")
        self.assertEqual(dist["top3"] + dist["p4_10"] + dist["p11_20"] + dist["p21_100"]
                         + dist["unmeasured"], 5,
                         "the segments must still account for every tracked keyword")

    def test_the_competitor_grid_diff_is_unsigned_with_a_direction(self):
        """P8. `"diff": r["pos_change"]` is SIGNED; the renderer prints '▼' + diff verbatim,
        so a declining keyword rendered '▼-3' — an arrow and a minus sign fighting each other.
        """
        rows = {r["kw"]: r for r in self._body("28d")["competitors"]["rows"]}
        declined = rows["top c"]["you"]
        self.assertEqual(declined["direction"], "down")
        self.assertEqual(declined["diff"], 3,
                         "unsigned — the direction field carries the sign")
        improved = rows["top a"]["you"]
        self.assertEqual(improved["direction"], "up")
        self.assertEqual(improved["diff"], 3)

    def test_the_fallback_row_diff_is_unsigned_too(self):
        """The `else` branch — a keyword the competitor grid has no cell for.

        `_get_competitor_grid` builds its "you" column from the two most recent dates that
        carry a captured position, so a keyword measured only on an older date falls through
        to this branch, which built its diff straight from the signed `pos_change`.
        """
        from unittest.mock import patch

        empty_grid = {"status": "no_data", "competitors": [], "rows": [], "dates": []}
        with patch("apps.dashboard.services.shared_queries._get_competitor_grid",
                   return_value=empty_grid):
            rows = {r["kw"]: r for r in self._body("28d")["competitors"]["rows"]}
        self.assertEqual(rows["top c"]["you"]["direction"], "down")
        self.assertEqual(rows["top c"]["you"]["diff"], 3,
                         "'▼' + -3 rendered as '▼-3' on screen")
        self.assertEqual(rows["top a"]["you"]["direction"], "up")
        self.assertEqual(rows["top a"]["you"]["diff"], 3)

    def test_a_keyword_with_no_previous_position_reports_no_diff(self):
        rows = {r["kw"]: r for r in self._body("28d")["competitors"]["rows"]}
        self.assertIsNone(rows["top b"]["you"]["diff"])
        self.assertEqual(rows["top b"]["you"]["direction"], "flat")

    def test_awaiting_first_measurement_is_reported_on_the_payload(self):
        """P3, the endpoint half: the card can say '2 keywords awaiting first measurement'."""
        self.assertEqual(self._body()["opportunities_awaiting_data"], 2)


class PositionZeroIsNotFalsyTests(TestCase):
    """P10. `if r.avg_pos and r.avg_pos <= 3` — 0 and 0.0 are falsy, so a stored position of 0
    was excluded from every bucket while `positioned_rows` two lines below already used the
    correct `is not None` idiom. The two disagreed about the same rows.
    """

    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.day = date.today() - timedelta(days=1)
        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", slug="staff-dc", location=LOC,
                             is_active=1))
            session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1,
                                     keyword="zero position", location=LOC))
            session.add(KeywordRanking(date=self.day, site_id="premierstaff.com",
                                       keyword="zero position", location=LOC, position=0,
                                       rank_checked_at=self.day))

    def test_a_zero_position_counts_in_every_bucket(self):
        from apps.dashboard.services.shared_queries import _get_ranking_distribution

        dist = _get_ranking_distribution("premierstaff.com", self.day, self.day,
                                         location=LOC, site_pk=1)
        for bucket in ("top3", "top10", "top20", "top50", "top100"):
            self.assertEqual(dist[bucket], 1,
                             f"{bucket} dropped a row because 0 is falsy")
