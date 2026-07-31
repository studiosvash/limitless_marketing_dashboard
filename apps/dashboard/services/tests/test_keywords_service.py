import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, KeywordRanking, SavedKeyword
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

    def test_full_keywords_includes_every_tracked_keyword(self):
        from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
        result = get_keyword_intelligence_raw(
            "sc-domain:fusehealth.com",
            date(2026, 6, 30), date(2026, 6, 30),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertIn("full_keywords", result)
        full_ids = {row["keyword"] for row in result["full_keywords"]}
        self.assertEqual(full_ids, {"iv therapy near me", "mobile iv drip"})
        # every row must carry pos_change (real number or None), not be missing the key
        by_kw = {row["keyword"]: row for row in result["full_keywords"]}
        self.assertIn("pos_change", by_kw["iv therapy near me"])
        self.assertIsNotNone(by_kw["iv therapy near me"]["pos_change"])


class BuildKeywordsResponseTests(TestCase):
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
                # build_keywords_response runs get_keyword_intelligence_raw(tracked_only=True),
                # so every figure is bounded by the site's saved_keywords list. With none in
                # the DB, load_tracked_keywords() falls back to the repo's legacy keywords.txt
                # and none of the rows below match — the response comes back empty.
                SavedKeyword(site_id="sc-domain:fusehealth.com", keyword="iv therapy near me"),
                SavedKeyword(site_id="sc-domain:fusehealth.com", keyword="mobile iv drip"),
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=6, clicks=12,
                               impressions=200, search_volume=2400, keyword_difficulty=24,
                               cpc=4.2, intent="commercial", url="/services/iv-therapy"),
                KeywordRanking(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                               keyword="iv therapy near me", position=9, clicks=8, impressions=180),
                KeywordRanking(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                               keyword="mobile iv drip", position=15, clicks=0, impressions=60,
                               search_volume=880, keyword_difficulty=18, intent="informational",
                               url="/services/mobile"),
            ])

    def test_top_level_keys(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        for key in ["kpis", "intents", "difficulty", "segments", "keywords"]:
            self.assertIn(key, body)

    def test_segments_are_id_arrays_not_full_objects(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        self.assertEqual(body["segments"]["quick_wins"], ["iv therapy near me"])
        for seg_ids in body["segments"].values():
            for kw_id in seg_ids:
                self.assertIsInstance(kw_id, str)

    def test_every_segment_id_has_a_matching_keyword(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        known_ids = {k["id"] for k in body["keywords"]}
        for seg_ids in body["segments"].values():
            for kw_id in seg_ids:
                self.assertIn(kw_id, known_ids)

    def test_keyword_row_shape_and_prev_pos(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response("sc-domain:fusehealth.com", date(2026, 6, 30), date(2026, 6, 30),
                                        date(2026, 6, 1), date(2026, 6, 1))
        by_id = {k["id"]: k for k in body["keywords"]}
        row = by_id["iv therapy near me"]
        for key in ["id", "kw", "intent", "pos", "prevPos", "volume", "kd", "cpc",
                    "clicks", "impressions", "ctr", "url", "monthly", "source", "serpFeatures"]:
            self.assertIn(key, row)
        self.assertEqual(row["prevPos"], 9)
        self.assertEqual(row["monthly"], [])
        self.assertEqual(row["serpFeatures"], [])
        self.assertEqual(row["source"], "sync")
        # the keyword with no previous-period row must have prevPos None, not a KeyError/crash
        self.assertIsNone(by_id["mobile iv drip"]["prevPos"])


class BuildKeywordsResponseBeyondTopClicksCapTests(TestCase):
    """Regression coverage for the whole-branch-review bug: all_keywords used to be capped at
    the top 200 keywords BY CLICKS, while the segments (quick_wins/striking/declining/low_ctr)
    sort by their own criteria. On a site tracking >200 keywords, a keyword can qualify for a
    segment (e.g. striking: high impressions, low/no clicks) while falling outside the
    top-200-by-clicks slice -- producing a segment ID with no matching entry in keywords[]."""

    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        self.site_id = "sc-domain:fusehealth.com"
        self.curr_date = date(2026, 6, 30)

        with get_session() as session:
            # 200 filler keywords with high clicks and low impressions/position-1, so they
            # dominate the top-200-by-clicks slice and never qualify for any segment
            # (position=1 fails quick_wins' 4-10 range and striking's 11-20 range;
            # impressions=10 fails low_ctr's impressions>=50 threshold).
            fillers = [
                KeywordRanking(date=self.curr_date, site_id=self.site_id,
                                keyword=f"filler keyword {i}", position=1,
                                clicks=1000 - i, impressions=10)
                for i in range(200)
            ]
            # the one keyword that must survive: 0 clicks (so it ranks below all 200 fillers
            # and is excluded from the top-200-by-clicks slice), position 15 (in the 11-20
            # "striking" range), and impressions well above the segment thresholds.
            target = KeywordRanking(date=self.curr_date, site_id=self.site_id,
                                     keyword="low click high impression target", position=15,
                                     clicks=0, impressions=500)
            # The whole set has to be TRACKED for build_keywords_response to see it
            # (tracked_only=True bounds it by saved_keywords) — and tracking all 201 is what
            # makes this a real >200-keyword site, which is the condition under test.
            tracked = [SavedKeyword(site_id=self.site_id, keyword=f"filler keyword {i}")
                       for i in range(200)]
            tracked.append(SavedKeyword(site_id=self.site_id,
                                        keyword="low click high impression target"))
            session.add_all(fillers + [target] + tracked)

    def test_striking_keyword_outside_top_200_by_clicks_still_has_a_keywords_entry(self):
        from apps.dashboard.services.keywords_service import build_keywords_response
        body = build_keywords_response(
            self.site_id, self.curr_date, self.curr_date,
            self.curr_date, self.curr_date,
        )
        target_id = "low click high impression target"

        # the target must be classified into the striking segment...
        self.assertIn(target_id, body["segments"]["striking"])

        # ...and every ID in segments.* must have a matching entry in keywords[] (per-ID
        # lookup, not just a length check) -- this is the assertion that failed pre-fix, since
        # the target's 0 clicks put it outside the old top-200-by-clicks all_keywords cap.
        known_ids = {k["id"] for k in body["keywords"]}
        self.assertIn(target_id, known_ids)


from apps.dashboard.services.keywords_service import to_api_keyword


class ToApiKeywordTests(TestCase):
    def test_shapes_a_raw_row_into_the_api_keyword_object(self):
        row = {
            "keyword": "iv therapy near me", "intent": "commercial", "position": 6.0,
            "prev_position": 9.0, "search_volume": 2400, "keyword_difficulty": 24.0,
            "cpc": 4.2, "clicks": 12, "impressions": 200, "ctr": 6.0,
            "url": "/services/iv-therapy",
        }
        api_kw = to_api_keyword(row)
        self.assertEqual(api_kw["id"], "iv therapy near me")
        self.assertEqual(api_kw["pos"], 6.0)
        self.assertEqual(api_kw["prevPos"], 9.0)
        self.assertEqual(api_kw["monthly"], [])
        self.assertEqual(api_kw["source"], "sync")
