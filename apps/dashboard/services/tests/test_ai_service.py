import json
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings

from apps.dashboard.models import AITarget, AIPromptList, AIPrompt
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, AIKeywordData
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_ID = "https://example.com"


def _new_analytics_db(test_case):
    """Point the SQLAlchemy analytics DB at a fresh temp sqlite file for the duration of
    a test, matching the established pattern in test_offsite_service.py. Registers cleanup
    to restore global state so tests don't leak into each other."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)


class QueryAiKeywordsRawTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)

        # Real shape (pipeline/connectors/dataforseo_ai_keywords.py::_normalize): a list of
        # {year, month, ai_search_volume} objects, NOT a flat list of numbers -- and
        # deliberately out of chronological order here, to prove the reshape sorts by
        # (year, month) rather than trusting input order. Aug 2025 (10) .. Jul 2026 (120).
        months = [(2025, m, (m - 7) * 10) for m in range(8, 13)] + [(2026, m, (m + 5) * 10) for m in range(1, 8)]
        self.full_trend = [{"year": y, "month": m, "ai_search_volume": v} for (y, m, v) in months]
        self.expected_flat_trend = [v for (_, _, v) in months]  # already chronological
        shuffled = self.full_trend[3:] + self.full_trend[:3]  # rotate, still all present
        with get_session() as session:
            session.add_all([
                # Latest-date rows -- both must be included.
                AIKeywordData(
                    site_id=SITE_ID, date=date(2026, 7, 10), keyword="best crm software",
                    ai_search_volume=120, prev_ai_search_volume=100, search_volume=400,
                    intent="commercial", trend=json.dumps(shuffled),
                ),
                AIKeywordData(
                    site_id=SITE_ID, date=date(2026, 7, 10), keyword="what is agile",
                    ai_search_volume=50, prev_ai_search_volume=None, search_volume=0,
                    intent=None, trend=None,
                ),
                # Older-dated row for a different keyword -- must be excluded entirely.
                AIKeywordData(
                    site_id=SITE_ID, date=date(2026, 6, 1), keyword="stale keyword",
                    ai_search_volume=999, prev_ai_search_volume=999, search_volume=999,
                    intent="commercial", trend=None,
                ),
            ])

    def _rows_by_kw(self):
        from apps.dashboard.services.ai_service import query_ai_keywords_raw
        rows = query_ai_keywords_raw(SITE_ID)
        return {r["kw"]: r for r in rows}, rows

    def test_scopes_to_latest_date_only(self):
        by_kw, rows = self._rows_by_kw()
        self.assertEqual(len(rows), 2)
        self.assertNotIn("stale keyword", by_kw)
        self.assertIn("best crm software", by_kw)
        self.assertIn("what is agile", by_kw)

    def test_full_trend_row_reshapes_correctly(self):
        by_kw, _ = self._rows_by_kw()
        row = by_kw["best crm software"]
        self.assertEqual(row["aiVolume"], 120)
        self.assertEqual(row["gVolume"], 400)
        self.assertEqual(row["ratio"], round(120 / 400 * 100))
        self.assertEqual(row["intent"], "commercial")
        # Proves the reshape flattens {year,month,ai_search_volume} objects into a plain
        # number list AND sorts chronologically, even though the seeded JSON was shuffled.
        self.assertEqual(row["trend"], self.expected_flat_trend)
        self.assertEqual(len(row["trend"]), 12)

    def test_null_trend_row_gets_real_12_zero_list(self):
        by_kw, _ = self._rows_by_kw()
        row = by_kw["what is agile"]
        self.assertEqual(row["trend"], [0] * 12)
        self.assertIsNotNone(row["trend"])
        self.assertEqual(row["gVolume"], 0)
        # None (not a fabricated 0%) -- there's no Google-volume denominator to compare
        # against, which is a different honest state than "0% AI share."
        self.assertIsNone(row["ratio"])
        self.assertEqual(row["intent"], "")

    def test_mentions_and_gap_are_always_honest_zero_false(self):
        _, rows = self._rows_by_kw()
        self.assertTrue(len(rows) > 0)
        for row in rows:
            self.assertEqual(row["mentions"], 0)
            self.assertIs(row["gap"], False)

    def test_excludes_other_sites_data(self):
        from apps.dashboard.services.ai_service import query_ai_keywords_raw
        with get_session() as session:
            session.add(AIKeywordData(
                site_id="https://other-project.com", date=date(2026, 7, 10),
                keyword="other project keyword", ai_search_volume=999, search_volume=999,
                intent=None, trend=None,
            ))
        rows = query_ai_keywords_raw(SITE_ID)
        self.assertNotIn("other project keyword", {r["kw"] for r in rows})
        other_rows = query_ai_keywords_raw("https://other-project.com")
        self.assertEqual({r["kw"] for r in other_rows}, {"other project keyword"})


class QueryAiKeywordsRawShortTrendTests(TestCase):
    """A trend shorter than 12 months (a keyword newly tracked mid-year) must pad with
    zeros at the START, not the end -- the SPA treats trend[11] as the current month, so
    end-padding would push real (older) data forward and fabricate zero as "most recent"."""

    def setUp(self):
        _new_analytics_db(self)
        with get_session() as session:
            session.add(AIKeywordData(
                site_id=SITE_ID, date=date(2026, 7, 10), keyword="new keyword",
                ai_search_volume=90, search_volume=None, intent=None,
                trend=json.dumps([
                    {"year": 2026, "month": 6, "ai_search_volume": 80},
                    {"year": 2026, "month": 7, "ai_search_volume": 90},
                ]),
            ))

    def test_short_trend_is_padded_at_start(self):
        from apps.dashboard.services.ai_service import query_ai_keywords_raw
        rows = query_ai_keywords_raw(SITE_ID)
        self.assertEqual(len(rows), 1)
        trend = rows[0]["trend"]
        self.assertEqual(len(trend), 12)
        self.assertEqual(trend[-2:], [80, 90])
        self.assertEqual(trend[:10], [0] * 10)


class QueryAiKeywordsRawEmptyDbTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)
        # Deliberately no seeded rows.

    def test_empty_db_returns_empty_list(self):
        from apps.dashboard.services.ai_service import query_ai_keywords_raw
        self.assertEqual(query_ai_keywords_raw(SITE_ID), [])


class BuildAiResponseNoTargetTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)
        # Deliberately no AITarget/AIPromptList/AIPrompt rows.

    def test_no_target_row_gives_honest_defaults(self):
        from apps.dashboard.services.ai_service import build_ai_response
        body = build_ai_response(SITE_ID)

        self.assertIs(body["setupDone"], False)
        self.assertEqual(body["targets"], {"brand": "", "aliases": [], "competitors": []})
        self.assertEqual(body["lists"], [])
        self.assertEqual(body["prompts"], [])
        self.assertEqual(body["aiKeywords"], [])


class BuildAiResponseWithTargetTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)
        self.target = AITarget.objects.create(
            site_url=SITE_ID, brand="Acme", aliases=["Acme Co"],
            competitors=["Widgets Inc"], setup_done=True,
        )

    def test_setup_done_true_and_targets_reflect_real_row(self):
        from apps.dashboard.services.ai_service import build_ai_response
        body = build_ai_response(SITE_ID)

        self.assertIs(body["setupDone"], True)
        self.assertEqual(body["targets"], {
            "brand": "Acme", "aliases": ["Acme Co"], "competitors": ["Widgets Inc"],
        })


class BuildAiResponseListsAndPromptsTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)
        self.plist = AIPromptList.objects.create(site_url=SITE_ID, name="Branded")
        self.prompt_in_list = AIPrompt.objects.create(
            site_url=SITE_ID, list=self.plist, text="who makes the best widget",
            tracked_models=["chatgpt", "claude"],
        )
        self.prompt_no_list = AIPrompt.objects.create(
            site_url=SITE_ID, text="best widget brands 2026",
        )
        # Different project's data -- must never leak into this site's response.
        AIPromptList.objects.create(site_url="https://other-project.com", name="Other project list")
        AIPrompt.objects.create(site_url="https://other-project.com", text="other project prompt")

    def test_lists_appear_in_response(self):
        from apps.dashboard.services.ai_service import build_ai_response
        body = build_ai_response(SITE_ID)

        self.assertEqual(len(body["lists"]), 1)
        self.assertEqual(body["lists"][0]["id"], self.plist.id)
        self.assertEqual(body["lists"][0]["name"], "Branded")

    def test_prompts_appear_with_correct_shape(self):
        from apps.dashboard.services.ai_service import build_ai_response
        body = build_ai_response(SITE_ID)

        prompts_by_id = {p["id"]: p for p in body["prompts"]}
        self.assertEqual(len(prompts_by_id), 2)

        in_list = prompts_by_id[self.prompt_in_list.id]
        self.assertEqual(in_list["text"], "who makes the best widget")
        self.assertEqual(in_list["listId"], self.plist.id)
        self.assertEqual(in_list["models"], ["chatgpt", "claude"])
        self.assertEqual(in_list["results"], [])

        no_list = prompts_by_id[self.prompt_no_list.id]
        self.assertEqual(no_list["text"], "best widget brands 2026")
        self.assertIsNone(no_list["listId"])
        self.assertEqual(no_list["models"], [])
        self.assertEqual(no_list["results"], [])

    def test_excludes_other_sites_lists_and_prompts(self):
        from apps.dashboard.services.ai_service import build_ai_response
        body = build_ai_response(SITE_ID)
        self.assertNotIn("Other project list", [l["name"] for l in body["lists"]])
        self.assertNotIn("other project prompt", [p["text"] for p in body["prompts"]])


class BuildAiResponseHonestEmptyFieldsTests(TestCase):
    """Even with real data seeded on both DBs (target/prompts/keywords), everything requiring
    the nonexistent LLM Mentions/Responses/scraper infra must stay exactly honest empty/zero --
    never fabricated from adjacent real data."""

    def setUp(self):
        _new_analytics_db(self)
        AITarget.objects.create(site_url=SITE_ID, brand="Acme", setup_done=True)
        AIPromptList.objects.create(site_url=SITE_ID, name="Branded")
        AIPrompt.objects.create(site_url=SITE_ID, text="who makes the best widget")
        with get_session() as session:
            session.add(AIKeywordData(
                site_id=SITE_ID, date=date(2026, 7, 10), keyword="best crm software",
                ai_search_volume=120, search_volume=400, intent="commercial",
                trend=json.dumps([{"year": 2026, "month": m, "ai_search_volume": m * 10} for m in range(1, 13)]),
            ))

    def test_honest_empty_zero_fields_exact_equality(self):
        from apps.dashboard.services.ai_service import build_ai_response
        body = build_ai_response(SITE_ID)

        self.assertEqual(body["sov"], {"you": 0, "delta": 0, "rows": []})
        self.assertEqual(body["trend"], [])
        self.assertEqual(body["topPages"], [])
        self.assertEqual(body["topDomains"], [])
        self.assertEqual(body["suggestions"], [])
        self.assertEqual(body["history"], [])
        self.assertEqual(body["budget"], {"cap": 0, "spent": 0, "weekly_est": 0})
        self.assertEqual(body["costs"], {"model": None, "inspect": None})
        self.assertIsNone(body["next_run"])

    def test_ai_keywords_field_matches_raw_calculator(self):
        from apps.dashboard.services.ai_service import build_ai_response, query_ai_keywords_raw
        body = build_ai_response(SITE_ID)
        self.assertEqual(body["aiKeywords"], query_ai_keywords_raw(SITE_ID))
        self.assertEqual(len(body["aiKeywords"]), 1)
