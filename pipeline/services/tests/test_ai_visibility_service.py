"""Tests for the real answer-engine visibility check.

Nothing here touches the network: `check_prompt` is exercised with a stubbed `requests.post`,
and every other test is pure text analysis (`analyze_answer` exists precisely so the detection
logic is testable without an API key or a charge).
"""
import os
from unittest import mock

from django.test import SimpleTestCase

from pipeline.services import ai_visibility_service as svc


ANSWER_CITED = """Here are the best IV therapy clinics in Austin:

1. FuseHealth — mobile IV drips, same-day booking.
2. Acme Wellness — walk-in clinic downtown.
3. Globex Health — subscription memberships.

All three are licensed."""

ANSWER_COMPETITOR_ONLY = """The best-known providers are:

1. Acme Wellness — the largest chain in the state.
2. Globex Health — strong reviews for hydration therapy.

Prices vary by city."""

ANSWER_MENTION_ONLY = (
    "There are several options in the area. FuseHealth is one provider people bring up, "
    "though most guides recommend booking through a clinic directory instead."
)


def _openai_response(text, prompt_tokens=120, completion_tokens=80):
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "choices": [{"message": {"content": text}}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return resp


class NeedleMatchingTests(SimpleTestCase):
    def test_domain_expands_to_its_label(self):
        self.assertIn("acme.com", svc._needles("https://www.acme.com/pricing"))
        self.assertIn("acme", svc._needles("https://www.acme.com/pricing"))

    def test_brand_containing_a_full_stop_is_not_split_into_a_fragment(self):
        # Regression: the inherited draft split on the first "." unconditionally, so this
        # brand produced the needle "dr" and matched every answer containing "Dr.".
        self.assertNotIn("dr", svc._needles("Dr. Smith Clinics"))

    def test_three_letter_domain_labels_are_not_expanded(self):
        # "one" is an ordinary English word; the domain itself still matches.
        needles = svc._needles("one.com")
        self.assertIn("one.com", needles)
        self.assertNotIn("one", needles)

    def test_substring_matches_are_not_false_positives(self):
        self.assertFalse(svc._contains("acmeium is a mineral", "acme"))
        self.assertTrue(svc._contains("we recommend acme wellness", "acme"))

    def test_aliases_are_all_searchable(self):
        needles = svc.target_needles("FuseHealth", ["Fuse Health", "fusehealth.com"])
        self.assertIn("fusehealth", needles)
        self.assertIn("fuse health", needles)
        self.assertIn("fusehealth.com", needles)


class ListOrdinalTests(SimpleTestCase):
    def test_nested_bullets_do_not_shift_the_top_level_ordinal(self):
        # Regression: one flat counter reported the brand at position #2 here.
        text = "1. Acme\n   - fast delivery\n   - good support\n2. FuseHealth\n"
        result = svc.analyze_answer(text, "FuseHealth")
        self.assertEqual(result["position"], 2)

    def test_model_written_numbers_win_over_running_position(self):
        text = "3. FuseHealth is the standout option.\n"
        self.assertEqual(svc.analyze_answer(text, "FuseHealth")["position"], 3)


class AnalyzeAnswerTests(SimpleTestCase):
    def test_brand_cited_in_a_ranked_list(self):
        result = svc.analyze_answer(ANSWER_CITED, "FuseHealth", competitors=["Acme Wellness"])
        self.assertEqual(result["verdict"], "cited")
        self.assertTrue(result["cited"])
        self.assertTrue(result["mentioned"])
        self.assertEqual(result["position"], 1)
        self.assertIn("FuseHealth", result["snippet"])

    def test_competitor_mentioned_is_reported_with_its_real_position(self):
        result = svc.analyze_answer(
            ANSWER_COMPETITOR_ONLY, "FuseHealth", competitors=["Acme Wellness", "Globex Health"]
        )
        self.assertEqual(result["verdict"], "absent")
        self.assertFalse(result["mentioned"])
        by_name = {c["name"]: c for c in result["competitors"]}
        self.assertEqual(set(by_name), {"Acme Wellness", "Globex Health"})
        self.assertEqual(by_name["Acme Wellness"]["position"], 1)
        self.assertEqual(by_name["Globex Health"]["position"], 2)

    def test_absent_when_nobody_is_named(self):
        result = svc.analyze_answer("Check a local directory for licensed providers.",
                                    "FuseHealth", competitors=["Acme Wellness"])
        self.assertEqual(result["verdict"], "absent")
        self.assertFalse(result["mentioned"])
        self.assertFalse(result["cited"])
        self.assertIsNone(result["position"])
        self.assertEqual(result["competitors"], [])

    def test_mentioned_but_not_ranked(self):
        result = svc.analyze_answer(ANSWER_MENTION_ONLY, "FuseHealth")
        self.assertEqual(result["verdict"], "mentioned")
        self.assertTrue(result["mentioned"])
        self.assertFalse(result["cited"])
        self.assertIsNone(result["position"])

    def test_no_brand_gives_no_verdict_rather_than_a_false_absent(self):
        self.assertIsNone(svc.analyze_answer(ANSWER_CITED, "")["verdict"])

    def test_citations_are_always_empty(self):
        # The chat-completions API returns prose, not verified sources.
        self.assertEqual(svc.analyze_answer(ANSWER_CITED, "FuseHealth")["citations"], [])

    def test_paragraphs_flag_only_the_blocks_that_really_contain_the_brand(self):
        paras = svc.analyze_answer(ANSWER_CITED, "FuseHealth")["paragraphs"]
        self.assertTrue(any(p["hit"] for p in paras))
        self.assertTrue(any(not p["hit"] for p in paras))


class CostTests(SimpleTestCase):
    def test_cost_comes_from_the_returned_token_counts(self):
        cost = svc._cost_usd("gpt-4o-mini", {"prompt_tokens": 1_000_000,
                                             "completion_tokens": 1_000_000})
        self.assertEqual(cost, round(0.15 + 0.60, 6))

    def test_missing_usage_is_unknown_not_zero(self):
        self.assertIsNone(svc._cost_usd("gpt-4o-mini", None))
        self.assertIsNone(svc._cost_usd("gpt-4o-mini", {"prompt_tokens": 10}))

    def test_unknown_model_has_no_guessed_price(self):
        self.assertIsNone(svc._cost_usd("some-future-model",
                                        {"prompt_tokens": 10, "completion_tokens": 10}))


class ConnectivityTests(SimpleTestCase):
    def test_only_openai_is_connectable(self):
        self.assertEqual(svc.connectable_platforms(), ["chatgpt"])

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
    def test_other_engines_stay_not_connected_even_with_an_openai_key(self):
        self.assertEqual(svc.connected_platforms(), ["chatgpt"])
        for pid in ("claude", "gemini", "perplexity"):
            self.assertFalse(svc.is_platform_connected(pid))

    def test_not_connected_result_never_claims_a_verdict(self):
        result = svc.not_connected_result("claude")
        self.assertEqual(result["state"], "not_connected")
        self.assertIsNone(result["verdict"])
        self.assertFalse(result["mentioned"])
        self.assertFalse(result["cited"])
        self.assertEqual(result["cost"], 0.0)


class CheckPromptTests(SimpleTestCase):
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_real_check_returns_verdict_and_real_cost(self, post):
        post.return_value = _openai_response(ANSWER_CITED)
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth",
                                  competitors=["Acme Wellness"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "checked")
        self.assertEqual(result["verdict"], "cited")
        self.assertEqual(result["position"], 1)
        self.assertEqual(result["model"], "gpt-4o-mini")
        self.assertEqual(result["tokens"], {"input": 120, "output": 80, "total": 200})
        self.assertEqual(result["cost"],
                         round(120 / 1_000_000 * 0.15 + 80 / 1_000_000 * 0.60, 6))
        # Exercised the OpenAI chat-completions endpoint the same way ai_summary_service does.
        self.assertEqual(post.call_args.args[0], svc.OPENAI_CHAT_URL)
        self.assertEqual(post.call_args.kwargs["json"]["model"], "gpt-4o-mini")
        self.assertEqual(post.call_args.kwargs["timeout"], svc.REQUEST_TIMEOUT)

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_competitor_only_answer_is_absent_for_us(self, post):
        post.return_value = _openai_response(ANSWER_COMPETITOR_ONLY)
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth",
                                  competitors=["Acme Wellness"])
        self.assertEqual(result["verdict"], "absent")
        self.assertEqual([c["name"] for c in result["competitors"]], ["Acme Wellness"])

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_no_api_key_degrades_honestly_without_calling_anything(self, post):
        result = svc.check_prompt("best iv therapy", "FuseHealth")
        post.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "not_connected")
        self.assertIsNone(result["verdict"])
        self.assertIn("OPENAI_API_KEY", result["error"])

    @mock.patch.object(svc.requests, "post")
    def test_unconnected_engine_is_never_called_or_simulated(self, post):
        result = svc.check_prompt("best iv therapy", "FuseHealth", platform="perplexity")
        post.assert_not_called()
        self.assertEqual(result["state"], "not_connected")

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_provider_failure_is_an_error_state_not_a_verdict(self, post):
        post.side_effect = RuntimeError("connection reset")
        result = svc.check_prompt("best iv therapy", "FuseHealth")
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])
        self.assertIn("connection reset", result["error"])

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_empty_answer_is_an_error_not_an_absent_verdict(self, post):
        post.return_value = _openai_response("   ")
        result = svc.check_prompt("best iv therapy", "FuseHealth")
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_no_brand_refuses_before_spending_money(self, post):
        result = svc.check_prompt("best iv therapy", "")
        post.assert_not_called()
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])
