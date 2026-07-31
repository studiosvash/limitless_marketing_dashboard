"""The AI Visibility block: real numbers when they exist, honest states when they do not."""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from apps.dashboard.services.llm_mentions_service import build_visibility_block
from pipeline.db.schema import init_db
from pipeline.db.writer import upsert_llm_cited_pages, upsert_llm_mention_metrics
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session

SITE = "fusehealth.com"
THIS_WEEK = date(2026, 7, 27)
LAST_WEEK = THIS_WEEK - timedelta(days=7)


class VisibilityBlockTests(SimpleTestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        init_db(get_engine(str(Path(tmp) / "fusehealth.db")))
        self._ctx = override_settings(ANALYTICS_DB_PATH=str(Path(tmp) / "fusehealth.db"))
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def _seed(self, rows, week=THIS_WEEK):
        recs = [{
            "site_id": SITE, "week_start": week, "subject_domain": d,
            "subject_type": t, "platform": p, "mentions": m, "ai_search_volume": v,
        } for d, t, p, m, v in rows]
        with get_session() as s:
            upsert_llm_mention_metrics(s, recs)
            s.commit()

    def test_never_synced_reports_setup_not_zeros(self):
        block = build_visibility_block(SITE)
        self.assertEqual(block["state"], "setup")
        self.assertEqual(block["sov"]["rows"], [])
        self.assertIsNone(block["sov"]["delta"])

    def test_share_of_voice_sums_platforms_and_totals_100(self):
        self._seed([
            ("fusehealth.com", "you", "google", 1, 50),
            ("fusehealth.com", "you", "chat_gpt", 0, 0),
            ("driphydration.com", "competitor", "google", 3632, 1617710),
            ("driphydration.com", "competitor", "chat_gpt", 1, 32),
            ("mobileivmedics.com", "competitor", "google", 2392, 1142040),
            ("mobileivmedics.com", "competitor", "chat_gpt", 114, 2875),
        ])
        block = build_visibility_block(SITE)
        rows = block["sov"]["rows"]
        self.assertEqual([r["domain"] for r in rows][:2],
                         ["driphydration.com", "mobileivmedics.com"])
        self.assertEqual(rows[0]["mentions"], 3633)
        self.assertEqual(sum(r["sov"] for r in rows), 100)
        you = next(r for r in rows if r["isYou"])
        self.assertEqual(you["domain"], "fusehealth.com")
        self.assertEqual(block["sov"]["you"], you["sov"])

    def test_first_week_has_no_delta(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("x.com", "competitor", "google", 10, 100)])
        block = build_visibility_block(SITE)
        self.assertIsNone(block["sov"]["delta"],
                          "no prior week means no comparison — not a zero")

    def test_delta_is_computed_once_a_prior_week_exists(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("x.com", "competitor", "google", 90, 900)], week=LAST_WEEK)
        self._seed([("fusehealth.com", "you", "google", 30, 300),
                    ("x.com", "competitor", "google", 70, 700)], week=THIS_WEEK)
        block = build_visibility_block(SITE)
        self.assertEqual(block["sov"]["you"], 30)
        self.assertEqual(block["sov"]["delta"], 20)

    def test_no_competitors_reports_its_own_state(self):
        self._seed([("fusehealth.com", "you", "google", 5, 50)])
        block = build_visibility_block(SITE)
        self.assertEqual(block["state"], "no_competitors")
        self.assertEqual(block["mentions"], 5, "own mentions are still real and still shown")

    def test_zero_data_competitor_is_listed_not_hidden(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("restoreiv.com", "competitor", "google", 0, 0)])
        block = build_visibility_block(SITE)
        self.assertIn("restoreiv.com", [r["domain"] for r in block["sov"]["rows"]])

    def test_top_domains_come_from_discovered_rows_and_flag_you_and_competitors(self):
        self._seed([
            ("fusehealth.com", "you", "google", 100, 1000),
            ("driphydration.com", "competitor", "google", 300, 3000),
            ("www.youtube.com", "discovered", "all", 600, 6000),
        ])
        block = build_visibility_block(SITE)
        by = {d["domain"]: d for d in block["topDomains"]}
        self.assertTrue(by["fusehealth.com"]["isYou"])
        self.assertTrue(by["driphydration.com"]["isComp"])
        self.assertFalse(by["www.youtube.com"]["isYou"])
        self.assertFalse(by["www.youtube.com"]["isComp"])

    def test_cited_pages_are_read_for_the_latest_week(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("x.com", "competitor", "google", 10, 100)])
        with get_session() as s:
            upsert_llm_cited_pages(s, [{
                "site_id": SITE, "week_start": THIS_WEEK,
                "url": "https://fusehealth.com/locations/dallas",
                "mentions": 36, "ai_search_volume": 1627,
                "platforms": '["google"]',
            }])
            s.commit()
        block = build_visibility_block(SITE)
        self.assertEqual(block["cited_pages"], 1)
        self.assertEqual(block["topPages"][0]["url"], "https://fusehealth.com/locations/dallas")
        self.assertEqual(block["topPages"][0]["impressions"], 1627)
        self.assertEqual(block["topPages"][0]["platforms"], ["google"])

    def test_no_cited_pages_is_an_empty_list_not_an_error(self):
        self._seed([("fusehealth.com", "you", "google", 1, 50),
                    ("x.com", "competitor", "google", 10, 100)])
        block = build_visibility_block(SITE)
        self.assertEqual(block["topPages"], [])
        self.assertEqual(block["cited_pages"], 0)

    def test_mention_platforms_are_the_two_the_api_actually_covers(self):
        block = build_visibility_block(SITE)
        self.assertEqual([p["id"] for p in block["mentionPlatforms"]], ["google", "chat_gpt"])
        self.assertEqual([p["name"] for p in block["mentionPlatforms"]],
                         ["AI Overviews", "ChatGPT"])
