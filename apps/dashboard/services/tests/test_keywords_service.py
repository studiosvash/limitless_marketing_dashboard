import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, KeywordRanking
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class KeywordIntelligenceTests(TestCase):
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
                # quick-win: pos 6 (current), pos 9 (previous) -> improved, not "declining"
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=6, clicks=12,
                               impressions=200, search_volume=2400, keyword_difficulty=24,
                               cpc=4.2, intent="commercial", url="/services/iv-therapy"),
                KeywordRanking(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=9, clicks=8,
                               impressions=180),
                # a second keyword with NO previous-period row -> prevPos should be null, not crash
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=15, clicks=0,
                               impressions=60, search_volume=880, keyword_difficulty=18,
                               intent="informational", url="/services/mobile"),
            ])

    def test_all_keywords_includes_prev_position_for_every_row(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:fusehealth.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        by_kw = {row["keyword"]: row for row in result["all_keywords"]}
        self.assertEqual(len(result["all_keywords"]), 2)
        # the keyword WITH a previous-period row has a real prev_position
        self.assertEqual(by_kw["iv therapy near me"]["prev_position"], 9)
        # the keyword with NO previous-period row has prev_position None, not a crash/omission
        self.assertIsNone(by_kw["mobile iv drip"]["prev_position"])

    def test_quick_wins_segment_still_populated(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:fusehealth.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertEqual(len(result["quick_wins"]), 1)
        self.assertEqual(result["quick_wins"][0]["keyword"], "iv therapy near me")

    def test_empty_data_returns_safe_defaults(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:no-such-site.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertEqual(result["total_tracked"], 0)
        self.assertEqual(result["all_keywords"], [])
