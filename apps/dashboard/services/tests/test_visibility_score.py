"""The project list's visibility % must be the industry-standard reading.

Semrush/Ahrefs visibility is a CTR-weighted click share: each keyword earns the CTR of its
position (#1 = 31.7 … #10 = 1.8, ~0 past #20), divided by the perfect score of ranking #1 on
EVERY tracked keyword. Two properties matter and both are pinned here:

1. The denominator is ALL tracked keywords — a keyword with no ranking earns 0 but still
   counts. The old avg-position-derived number ignored unranked keywords, which is how a
   project ranking on 1 of 48 keywords (the brand name, position 2.2) displayed 82%.
2. "No capture at all" is None (the UI shows —), while "captured but ranks nowhere" is a
   real 0.0 — that distinction is information, mirroring buildVisibilityScores in the SPA.
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import TestCase, override_settings

from apps.dashboard.services.shared_queries import _get_ranking_distribution
from pipeline.db.schema import KeywordRanking, SavedKeyword, init_db
from pipeline.db.writer import ensure_tables, upsert_keyword_rankings
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session


def _new_analytics_db(test_case):
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)


SITE = "fusehealth.com"
LOC = "United States"
DAY = date(2026, 8, 6)
START, END = DAY - timedelta(days=30), DAY


def _track(keywords):
    with get_session() as session:
        ensure_tables(session, SavedKeyword)
        for kw in keywords:
            session.add(SavedKeyword(site_id=SITE, keyword=kw, location=LOC))
        session.commit()


def _seed(positions_by_keyword):
    with get_session() as session:
        ensure_tables(session, KeywordRanking, SavedKeyword)
        upsert_keyword_rankings(session, [
            {"date": DAY, "site_id": SITE, "keyword": kw, "location": LOC,
             "position": pos, "url": f"https://{SITE}/"}
            for kw, pos in positions_by_keyword.items()
        ], site_id=SITE)


class VisibilityScoreTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)

    def _vis(self):
        return _get_ranking_distribution(SITE, START, END, location=LOC)["visibility"]

    def test_number_one_on_every_tracked_keyword_is_100(self):
        _track(["a", "b"])
        _seed({"a": 1, "b": 1})
        self.assertEqual(self._vis(), 100.0)

    def test_unranked_keywords_count_in_the_denominator(self):
        # The 82% bug: 1 of 4 keywords at #1 is 25% visibility, not 100%.
        _track(["a", "b", "c", "d"])
        _seed({"a": 1})
        self.assertEqual(self._vis(), 25.0)

    def test_credit_follows_the_semrush_curve_not_a_linear_scale(self):
        # #10 earns 0.060439 of a perfect 1.0 on the measured Semrush credit curve
        # (_SEMRUSH_CREDIT, 2026-08-21) → 6.0%. Linear (100-10)/100 would say 90%.
        _track(["a"])
        _seed({"a": 10})
        self.assertEqual(self._vis(), 6.0)

    def test_no_capture_in_window_is_none_not_zero(self):
        _track(["a", "b"])
        self.assertIsNone(self._vis())

    def test_captured_but_ranking_nowhere_is_a_real_zero(self):
        _track(["a"])
        _seed({"a": 101})
        self.assertEqual(self._vis(), 0.0)

    def test_no_tracked_keywords_is_none(self):
        self.assertIsNone(self._vis())


class ProjectSerializerVisibilityTests(TestCase):
    """The serializer must pass the score through to the projects list payload."""

    def setUp(self):
        _new_analytics_db(self)

    def test_serializer_exposes_visibility(self):
        _track(["a", "b"])
        _seed({"a": 1})

        class _Site:  # the three attributes _pos_summary actually reads
            id = None
            site_url = SITE
            location = LOC

        from apps.api.serializers import ProjectSerializer
        vis = ProjectSerializer().get_visibility(_Site())
        self.assertEqual(vis, 50.0)
