"""Portfolio KPIs — scope decided by the product owner (2026-08-03):

Total keywords / Total volume / intent / difficulty cover EVERY keyword saved for the site
(position tracking ∪ research lists), deduplicated across lists; average position stays
tracked-only because a list keyword has no measured position. A keyword repeated across
lists counts once, with its volume counted once.
"""
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from apps.dashboard.services.keywords_service import (
    get_keyword_lists_raw, query_keyword_portfolio_raw,
)
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, KeywordRanking, SavedKeyword, Site
from pipeline.db.writer import replace_keyword_lists
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE = "example.com"


class PortfolioTestCase(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        with get_session() as s:
            s.add(Site(site_url=SITE, site_name="Example"))
            s.commit()

    def _track(self, kw, volume=None, kd=None, intent=None):
        with get_session() as s:
            s.add(SavedKeyword(site_id=SITE, keyword=kw, search_volume=volume,
                               keyword_difficulty=kd, intent=intent))
            s.commit()

    def _lists(self, lists):
        with get_session() as s:
            replace_keyword_lists(s, SITE, lists)
            s.commit()


class QueryKeywordPortfolioTests(PortfolioTestCase):
    def test_union_deduplicates_across_tracking_and_lists(self):
        """'iv therapy' is tracked AND in two lists — one keyword, its volume counted once."""
        self._track("iv therapy", volume=5000, kd=42, intent="commercial")
        self._lists([
            {"name": "A", "keywords": [{"keyword": "iv therapy", "volume": 5000},
                                       {"keyword": "mobile iv", "volume": 900, "kd": 10,
                                        "intent": "transactional"}]},
            {"name": "B", "keywords": [{"keyword": "IV Therapy", "volume": 5000}]},
        ])

        got = query_keyword_portfolio_raw(SITE)

        self.assertEqual(got["total"], 2)                    # not 4
        self.assertEqual(got["total_volume"], 5900)          # 5000 once + 900
        self.assertEqual(got["difficulty"], {"easy": 1, "medium": 1, "hard": 0})
        self.assertEqual(got["intents"]["commercial"], 1)
        self.assertEqual(got["intents"]["transactional"], 1)

    def test_synced_rankings_metrics_beat_the_saved_snapshot(self):
        """The list snapshot said 100 volume; a later sync measured 800. Fresh wins."""
        self._lists([{"name": "A", "keywords": [{"keyword": "event staff", "volume": 100}]}])
        with get_session() as s:
            s.add(KeywordRanking(site_id=SITE, keyword="event staff", date=date(2026, 7, 1),
                                 position=8, search_volume=800, keyword_difficulty=65,
                                 intent="commercial"))
            s.commit()

        got = query_keyword_portfolio_raw(SITE)

        self.assertEqual(got["total_volume"], 800)
        self.assertEqual(got["difficulty"], {"easy": 0, "medium": 0, "hard": 1})

    def test_keyword_with_no_metrics_still_counts_as_a_keyword(self):
        """Membership is the fact being counted; missing metrics contribute nothing but the
        keyword itself must not vanish from Total."""
        self._lists([{"name": "A", "keywords": [{"keyword": "brand new idea"}]}])

        got = query_keyword_portfolio_raw(SITE)

        self.assertEqual(got["total"], 1)
        self.assertEqual(got["total_volume"], 0)
        self.assertEqual(sum(got["intents"].values()), 0)

    def test_empty_portfolio_reports_zero_not_error(self):
        got = query_keyword_portfolio_raw(SITE)
        self.assertEqual(got["total"], 0)


class KeywordListsRoundTripTests(PortfolioTestCase):
    def test_replace_and_read_back(self):
        self._lists([{"name": "Priority", "keywords": [
            {"keyword": "iv therapy", "volume": 5000, "kd": 42, "intent": "commercial"}]}])

        lists = get_keyword_lists_raw(SITE)

        self.assertEqual(len(lists), 1)
        self.assertEqual(lists[0]["name"], "Priority")
        self.assertEqual(lists[0]["keywords"][0]["kw"], "iv therapy")
        self.assertEqual(lists[0]["keywords"][0]["volume"], 5000)

    def test_replace_is_wholesale_removed_entries_stay_removed(self):
        """The delete-then-insert contract: what was sent is exactly what is stored — an
        upsert would resurrect the keyword the user just removed."""
        self._lists([{"name": "A", "keywords": [{"keyword": "one"}, {"keyword": "two"}]}])
        self._lists([{"name": "A", "keywords": [{"keyword": "one"}]}])

        lists = get_keyword_lists_raw(SITE)
        self.assertEqual([k["kw"] for k in lists[0]["keywords"]], ["one"])

    def test_bare_string_keywords_are_accepted(self):
        """The localStorage migration sends legacy lists whose keywords are plain strings."""
        self._lists([{"name": "Legacy", "keywords": ["old one", "old two"]}])

        lists = get_keyword_lists_raw(SITE)
        self.assertEqual([k["kw"] for k in lists[0]["keywords"]], ["old one", "old two"])
