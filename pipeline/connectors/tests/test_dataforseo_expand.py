"""Unit tests for the Keyword Explorer expansion (parsing, provenance tagging, fan-out).

NOTHING HERE TOUCHES THE NETWORK, and `_NoNetwork` enforces that rather than trusting it.

Two things about the previous revision of this module are worth recording, because between
them they meant it could not have caught any of the bugs it was written to guard:

  1. **It never ran.** Every test was a bare `def test_*(monkeypatch)` pytest function, and
     pytest is not installed in this project — `python manage.py test` uses unittest, which
     collects `TestCase` subclasses only. `manage.py test pipeline.connectors.tests.
     test_dataforseo_expand` reported "Found 0 test(s)". Everything below is a `TestCase`.
  2. **It patched a method the code does not call.** It monkeypatched
     `_fetch_keyword_suggestions` while `expand_keywords` called `_fetch_question_ideas`, so
     the questions fetch fell through to `requests.post` and issued a REAL HTTP request with
     whatever credentials were in the environment. The cost assertion (`== 0.004`) could only
     ever have summed to 0.003, so the test was failing for a reason nobody saw because it
     was never collected.

Hence `_NoNetwork`: `requests.post` inside the connector module is replaced with a raiser AND
asserted un-called at the end of every test, so a fetch that is not stubbed fails loudly
instead of quietly billing DataForSEO.
"""
import unittest
from unittest.mock import MagicMock, patch

from pipeline.connectors.dataforseo_keywords import DataForSEOKeywordsConnector as C


def _task(items, cost):
    """A DataForSEO Labs live-endpoint envelope: tasks[0].result[0].items[]."""
    return {"cost": cost, "tasks": [{"cost": cost, "result": [{"items": items}]}]}


def _item(keyword, volume):
    return {"keyword": keyword, "keyword_info": {"search_volume": volume}}


class _NoNetwork(unittest.TestCase):
    """Base class: a connector test may never make a real HTTP call."""

    def setUp(self):
        patcher = patch(
            "pipeline.connectors.dataforseo_keywords.requests.post",
            side_effect=AssertionError(
                "a connector test tried to make a real HTTP call — stub the fetch method"
            ),
        )
        self._post = patcher.start()
        self.addCleanup(patcher.stop)
        # record_cost opens an analytics session to append a connector_costs row. It swallows
        # every failure, but a unit test still has no business writing to the developer's real
        # fusehealth.db, so it is stubbed here rather than per-test.
        cost_patch = patch("pipeline.connectors.dataforseo_keywords.record_cost")
        cost_patch.start()
        self.addCleanup(cost_patch.stop)
        self.addCleanup(
            lambda: self.assertEqual(
                self._post.call_count, 0,
                "requests.post was called: some fetch on the expand path is not stubbed",
            )
        )

    def _connector(self):
        c = C()
        c.login, c.password = "test", "secret"
        c.auth = ("test", "secret")
        return c


class ClassifyMatchTests(unittest.TestCase):
    def test_buckets(self):
        seed_phrases = ["iv therapy"]
        seed_token_sets = [{"iv", "therapy"}]
        cases = {
            "iv therapy": "exact",
            "what is iv therapy": "questions",   # question word wins over phrase
            "mobile iv therapy": "phrase",       # contiguous seed phrase
            "therapy iv drip": "broad",          # tokens present, not contiguous -> broad
            "vitamin drip clinic": "broad",      # category-relevant (widest net) -> broad
        }
        for kw, expected in cases.items():
            self.assertEqual(C._classify_match(kw, seed_phrases, seed_token_sets), expected, kw)

    def test_never_returns_related(self):
        """`match` is a string-SHAPE classification and nothing else. Which fetch produced a
        row is `source`/`sources`, and the Related tab reads that — see ProvenanceTests."""
        for kw in ("keyword research tools", "free keyword research", "promo staff near me"):
            self.assertIn(C._classify_match(kw, ["keyword research"], [set()]),
                          {"exact", "phrase", "questions", "broad"})


class ParseIdeaItemTests(unittest.TestCase):
    def test_maps_shape_and_reverses_monthly(self):
        item = {
            "keyword": "iv therapy near me",
            "keyword_info": {
                "search_volume": 8100, "cpc": 3.987, "competition_level": "HIGH",
                # newest-first, as DataForSEO returns it
                "monthly_searches": [
                    {"year": 2026, "month": 6, "search_volume": 90},
                    {"year": 2026, "month": 5, "search_volume": 70},
                    {"year": 2026, "month": 4, "search_volume": 50},
                ],
            },
            "keyword_properties": {"keyword_difficulty": 42},
            "search_intent_info": {"main_intent": "transactional"},
            "serp_info": {"serp_item_types": ["organic", "local_pack", "people_also_ask"]},
        }
        row = C._parse_idea_item(item)
        self.assertEqual(row["kw"], "iv therapy near me")
        self.assertEqual(row["volume"], 8100)
        self.assertEqual(row["kd"], 42)
        self.assertEqual(row["cpc"], 3.99)                  # rounded
        self.assertEqual(row["intent"], "transactional")    # lowercase, matches intentView
        self.assertEqual(row["monthly"], [50, 70, 90])      # reversed to oldest->newest
        self.assertEqual(row["serpFeatures"], ["organic", "local_pack", "people_also_ask"])

    def test_missing_keyword_returns_none(self):
        self.assertIsNone(C._parse_idea_item({"keyword_info": {"search_volume": 10}}))


class RelatedRequestTests(unittest.TestCase):
    """The request `related_keywords/live` actually receives."""

    def test_depth_two_is_sent(self):
        """Without an explicit `depth`, DataForSEO defaults to depth 1 = AT MOST 8 keywords,
        which makes the `limit` parameter inert and starves the Related tab at the source."""
        c = C()
        c.auth = ("u", "p")
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = _task([], 0.001)
        with patch("pipeline.connectors.dataforseo_keywords.requests.post",
                   return_value=resp) as post:
            c._fetch_related_keywords("keyword research", "United States", 50)
        payload = post.call_args.kwargs["json"][0]
        self.assertEqual(payload["depth"], 2)
        self.assertEqual(payload["keyword"], "keyword research")


class ProvenanceTests(_NoNetwork):
    """The Related tab is fed by PROVENANCE — which fetch returned the row — not by the shape
    of the words in it."""

    # DataForSEO's own documented example for related_keywords: seed "keyword research".
    # Every single result CONTAINS the seed, which is the normal case for Google's
    # "searches related to" — and the exact case the old shape-based tagging got wrong.
    SEED = "keyword research"
    RELATED_ITEMS = [
        _item("free keyword research", 2400),
        _item("keyword research tools", 8100),
        _item("best free keyword research tool", 590),
        _item("keyword research google ads", 320),
    ]

    def _run(self, ideas=None, related=None, questions=None, seeds=None):
        c = self._connector()
        c._fetch_keyword_ideas = lambda s, loc, lim: _task(ideas or [], 0.002)
        c._fetch_related_keywords = lambda s, loc, lim: _task(related or [], 0.001)
        c._fetch_question_ideas = lambda s, loc, lim: _task(questions or [], 0.001)
        c._fetch_keyword_suggestions = lambda s, loc, lim: _task([], 0.0)
        return c.expand_keywords(seeds or [self.SEED], "United States")

    def test_seed_containing_related_rows_are_still_tagged_related(self):
        res = self._run(related=self.RELATED_ITEMS)
        self.assertEqual(res["status"], "ok")
        by_kw = {r["kw"]: r for r in res["rows"]}
        for it in self.RELATED_ITEMS:
            kw = it["keyword"]
            self.assertIn("related", by_kw[kw]["sources"],
                          f"{kw!r} came from related_keywords and must stay reachable there")

    def test_shape_classification_still_drives_the_other_tabs(self):
        """`match` keeps serving Broad/Phrase/Exact/Questions — the two axes coexist."""
        res = self._run(related=self.RELATED_ITEMS)
        by_kw = {r["kw"]: r for r in res["rows"]}
        self.assertEqual(by_kw["keyword research tools"]["match"], "phrase")
        self.assertEqual(by_kw["free keyword research"]["match"], "phrase")

    def test_a_keyword_returned_by_ideas_first_is_still_related(self):
        """The dedup used to be filled from keyword_ideas (100 rows, volume-desc) BEFORE the
        related loop read — and "searches related to" keywords are popular by definition, so
        most were already claimed and silently dropped. One row per keyword is right; losing
        its related provenance is not."""
        res = self._run(ideas=[_item("keyword research tools", 8100)],
                        related=[_item("keyword research tools", 8100)])
        rows = [r for r in res["rows"] if r["kw"] == "keyword research tools"]
        self.assertEqual(len(rows), 1, "one row per keyword, no duplicates in the All tab")
        self.assertEqual(sorted(rows[0]["sources"]), ["ideas", "related"])

    def test_every_row_carries_its_source(self):
        res = self._run(ideas=[_item("keyword research course", 210)],
                        related=[_item("keyword research tools", 8100)],
                        questions=[_item("how to do keyword research", 1000)])
        by_kw = {r["kw"]: r for r in res["rows"]}
        self.assertEqual(by_kw["keyword research course"]["source"], "ideas")
        self.assertEqual(by_kw["keyword research tools"]["source"], "related")
        self.assertEqual(by_kw["how to do keyword research"]["source"], "questions")

    def test_empty_related_response_yields_no_related_rows(self):
        """An honest empty — distinguishable from the old silently-mislabelled empty because
        no row anywhere claims `related` provenance."""
        res = self._run(ideas=[_item("keyword research course", 210)], related=[])
        self.assertEqual(res["status"], "ok")
        self.assertEqual([r for r in res["rows"] if "related" in r["sources"]], [])


class RelatedFanOutTests(_NoNetwork):
    def test_related_runs_for_up_to_three_seeds(self):
        """related_keywords/live takes ONE seed per task. Running it for `cleaned[0]` alone
        meant seeds 2..n contributed nothing to the Related tab."""
        seen = []
        c = self._connector()
        c._fetch_keyword_ideas = lambda s, loc, lim: _task([], 0.002)
        c._fetch_question_ideas = lambda s, loc, lim: _task([], 0.001)
        c._fetch_keyword_suggestions = lambda s, loc, lim: _task([], 0.0)

        def rel(seed, loc, lim):
            seen.append(seed)
            return _task([_item(seed + " tools", 100)], 0.001)

        c._fetch_related_keywords = rel
        res = c.expand_keywords(["alpha", "beta", "gamma", "delta", "epsilon"], "United States")
        self.assertEqual(sorted(seen), ["alpha", "beta", "gamma"])
        self.assertEqual(res["status"], "ok")
        # each seed's related rows are present and tagged
        self.assertEqual(
            sorted(r["kw"] for r in res["rows"] if "related" in r["sources"]),
            ["alpha tools", "beta tools", "gamma tools"],
        )


class CostTests(_NoNetwork):
    def test_cost_sums_every_task_that_ran(self):
        c = self._connector()
        c._fetch_keyword_ideas = lambda s, loc, lim: _task([_item("a", 1)], 0.002)
        c._fetch_related_keywords = lambda s, loc, lim: _task([_item("b", 1)], 0.001)
        c._fetch_question_ideas = lambda s, loc, lim: _task([_item("c", 1)], 0.001)
        c._fetch_keyword_suggestions = lambda s, loc, lim: _task([], 0.0)
        res = c.expand_keywords(["seed one", "seed two"], "United States")
        # two seeds -> two related tasks at 0.001 each, plus ideas 0.002 and questions 0.001
        self.assertAlmostEqual(res["cost"], 0.005, places=6)


class GuardrailTests(unittest.TestCase):
    def test_empty_seeds_is_error(self):
        out = C().expand_keywords([], "United States")
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["rows"], [])
