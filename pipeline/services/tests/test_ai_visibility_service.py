"""Tests for the real answer-engine visibility check.

Nothing here touches the network: `check_prompt` is exercised with a stubbed `requests.post`,
and every other test is pure text analysis (`analyze_answer` exists precisely so the detection
logic is testable without credentials or a charge).
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

# Both DataForSEO credentials present / explicitly absent, for connectivity control.
DFS_ENV = {"DATAFORSEO_LOGIN": "login", "DATAFORSEO_PASSWORD": "secret"}
NO_DFS_ENV = {"DATAFORSEO_LOGIN": "", "DATAFORSEO_PASSWORD": ""}

STUB_COST = 0.0055


def _dfs_response(text, input_tokens=120, output_tokens=80, cost=STUB_COST,
                  annotations=None, model_name="gpt-4o-mini", status_code=20000):
    """A stubbed DataForSEO llm_responses/live envelope. The real API is NEVER called from a
    test: a check is a real charge."""
    section = {"type": "text", "text": text}
    if annotations is not None:
        section["annotations"] = annotations
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "cost": cost,
        "tasks": [{
            "status_code": status_code,
            "status_message": "Ok." if status_code == 20000 else "Task error.",
            "cost": cost,
            "result": [{
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "items": [
                    # A reasoning item must never leak into the answer text.
                    {"type": "reasoning", "sections": [{"type": "summary_text",
                                                        "text": "thinking…"}]},
                    {"type": "message", "sections": [section]},
                ],
            }] if status_code == 20000 else None,
        }],
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

    def test_citations_are_empty_in_pure_text_analysis(self):
        # analyze_answer never invents sources from prose; real citations only come from
        # DataForSEO's web-search annotations, which check_prompt merges in.
        self.assertEqual(svc.analyze_answer(ANSWER_CITED, "FuseHealth")["citations"], [])

    def test_paragraphs_flag_only_the_blocks_that_really_contain_the_brand(self):
        paras = svc.analyze_answer(ANSWER_CITED, "FuseHealth")["paragraphs"]
        self.assertTrue(any(p["hit"] for p in paras))
        self.assertTrue(any(not p["hit"] for p in paras))


class ExtractAnswerTests(SimpleTestCase):
    def test_reasoning_items_are_skipped_and_annotations_become_citations(self):
        result = {
            "items": [
                {"type": "reasoning", "sections": [{"text": "chain of thought"}]},
                {"type": "message", "sections": [
                    {"text": "First part.",
                     "annotations": [{"title": "Source A", "url": "https://a.example"}]},
                    {"text": "Second part.",
                     "annotations": [{"title": "Dup", "url": "https://a.example"},
                                     {"title": "Source B", "url": "https://b.example"}]},
                ]},
            ],
        }
        answer, citations = svc._extract_answer(result)
        self.assertEqual(answer, "First part.\n\nSecond part.")
        self.assertNotIn("chain of thought", answer)
        # Deduped by URL, order preserved.
        self.assertEqual(citations, [
            {"title": "Source A", "url": "https://a.example"},
            {"title": "Source B", "url": "https://b.example"},
        ])


class ConnectivityTests(SimpleTestCase):
    def test_all_four_engines_are_connectable(self):
        self.assertEqual(svc.connectable_platforms(),
                         ["chatgpt", "claude", "gemini", "perplexity"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    def test_dataforseo_credentials_connect_every_engine(self):
        self.assertEqual(svc.connected_platforms(),
                         ["chatgpt", "claude", "gemini", "perplexity"])

    @mock.patch.dict(os.environ, {**NO_DFS_ENV, "OPENAI_API_KEY": "sk-test"}, clear=False)
    def test_an_openai_key_alone_connects_nothing(self):
        # Prompt checks no longer ride OPENAI_API_KEY (that key only feeds the AI summary).
        self.assertEqual(svc.connected_platforms(), [])

    @mock.patch.dict(os.environ, {**DFS_ENV, "DATAFORSEO_PASSWORD": ""}, clear=False)
    def test_half_a_credential_pair_is_not_connected(self):
        self.assertEqual(svc.connected_platforms(), [])

    def test_not_connected_result_never_claims_a_verdict(self):
        result = svc.not_connected_result("claude")
        self.assertEqual(result["state"], "not_connected")
        self.assertIsNone(result["verdict"])
        self.assertFalse(result["mentioned"])
        self.assertFalse(result["cited"])
        self.assertEqual(result["cost"], 0.0)


class ResolveModelTests(SimpleTestCase):
    """A hardcoded model name is what broke this feature in production: the configured Claude
    default had been retired by the provider, DataForSEO answered `40501 Invalid Field:
    'model_name'` on every check, and the run still reported success. `resolve_model` validates
    the preference against the provider's live list so a retired name self-heals."""

    def setUp(self):
        svc._MODEL_CACHE.clear()
        self.addCleanup(svc._MODEL_CACHE.clear)

    def test_preferred_model_is_used_when_the_provider_still_lists_it(self):
        with mock.patch.object(svc, "available_models",
                               return_value=["claude-haiku-4-5", "claude-opus-5"]):
            self.assertEqual(svc.resolve_model("claude"), "claude-haiku-4-5")

    def test_retired_model_falls_back_to_the_cheapest_listed_tier(self):
        with mock.patch.object(svc, "available_models",
                               return_value=["claude-opus-5", "claude-haiku-4-5"]):
            # Not simply names[0] — opus is several times the price for no better signal
            # about who gets mentioned.
            self.assertEqual(svc.resolve_model("claude", "claude-3-5-haiku-latest"),
                             "claude-haiku-4-5")

    def test_no_cheap_tier_listed_falls_back_to_the_first_offered(self):
        with mock.patch.object(svc, "available_models", return_value=["some-new-model"]):
            self.assertEqual(svc.resolve_model("claude", "gone"), "some-new-model")

    def test_unreadable_model_list_keeps_the_preference(self):
        # A free metadata endpoint being down must not stop a paid check the user asked for.
        with mock.patch.object(svc, "available_models", return_value=[]):
            self.assertEqual(svc.resolve_model("claude"), "claude-haiku-4-5")

    def test_every_configured_default_is_a_plausible_cheap_tier(self):
        # Guards against a future edit quietly promoting a default to a frontier model.
        for pid, meta in svc.PLATFORMS.items():
            self.assertTrue(
                any(h in meta["model"].lower() for h in svc._CHEAP_TIER_HINTS),
                f"{pid} default {meta['model']!r} is not a cheap tier",
            )


# Every check_prompt test stubs the model list too: `resolve_model` would otherwise reach the
# live models endpoint over the network, which the suite must never do.
@mock.patch.object(svc, "available_models", return_value=[])
class CheckPromptTests(SimpleTestCase):
    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_real_check_returns_verdict_and_the_reported_charge(self, post, _models):
        post.return_value = _dfs_response(ANSWER_CITED)
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth",
                                  competitors=["Acme Wellness"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "checked")
        self.assertEqual(result["verdict"], "cited")
        self.assertEqual(result["position"], 1)
        self.assertEqual(result["model"], "gpt-4o-mini")
        self.assertEqual(result["tokens"], {"input": 120, "output": 80, "total": 200})
        # Cost is what DataForSEO's envelope says it charged — no local price table.
        self.assertEqual(result["cost"], STUB_COST)
        self.assertEqual(
            post.call_args.args[0],
            f"{svc.DATAFORSEO_BASE}/ai_optimization/chat_gpt/llm_responses/live",
        )
        self.assertEqual(post.call_args.kwargs["auth"], ("login", "secret"))
        task = post.call_args.kwargs["json"][0]
        self.assertEqual(task["model_name"], "gpt-4o-mini")
        self.assertEqual(task["user_prompt"], "best iv therapy in austin")
        self.assertNotIn("web_search", task)  # off unless the prompt's config turns it on
        self.assertEqual(post.call_args.kwargs["timeout"], svc.REQUEST_TIMEOUT)

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_each_platform_uses_its_own_endpoint_and_default_model(self, post, _models):
        # Defaults are read from PLATFORMS rather than repeated here: this test previously
        # pinned the literals, so when the configured Claude default was corrected the test
        # failed for describing the old value rather than for any real change in behaviour.
        for platform, llm_type in [("claude", "claude"), ("gemini", "gemini"),
                                   ("perplexity", "perplexity")]:
            default_model = svc.PLATFORMS[platform]["model"]
            post.return_value = _dfs_response(ANSWER_CITED, model_name=default_model)
            result = svc.check_prompt("best iv therapy", "FuseHealth", platform=platform)
            self.assertTrue(result["ok"], platform)
            self.assertEqual(result["model"], default_model)
            self.assertEqual(
                post.call_args.args[0],
                f"{svc.DATAFORSEO_BASE}/ai_optimization/{llm_type}/llm_responses/live",
            )
            self.assertEqual(post.call_args.kwargs["json"][0]["model_name"], default_model)

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_web_search_is_requested_and_its_annotations_become_citations(self, post, _models):
        post.return_value = _dfs_response(
            ANSWER_CITED,
            annotations=[{"title": "Best IV therapy — Healthline",
                          "url": "https://healthline.example/iv"}],
        )
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth", web_search=True)
        self.assertIs(post.call_args.kwargs["json"][0]["web_search"], True)
        self.assertEqual(result["citations"], [
            {"title": "Best IV therapy — Healthline", "url": "https://healthline.example/iv"},
        ])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_competitor_only_answer_is_absent_for_us(self, post, _models):
        post.return_value = _dfs_response(ANSWER_COMPETITOR_ONLY)
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth",
                                  competitors=["Acme Wellness"])
        self.assertEqual(result["verdict"], "absent")
        self.assertEqual([c["name"] for c in result["competitors"]], ["Acme Wellness"])

    @mock.patch.dict(os.environ, NO_DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_no_credentials_degrades_honestly_without_calling_anything(self, post, _models):
        result = svc.check_prompt("best iv therapy", "FuseHealth")
        post.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "not_connected")
        self.assertIsNone(result["verdict"])
        self.assertIn("DATAFORSEO", result["error"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_provider_failure_is_an_error_state_not_a_verdict(self, post, _models):
        post.side_effect = RuntimeError("connection reset")
        result = svc.check_prompt("best iv therapy", "FuseHealth")
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])
        self.assertIn("connection reset", result["error"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_failed_task_status_is_an_error_state_not_a_verdict(self, post, _models):
        post.return_value = _dfs_response("", status_code=40501)
        result = svc.check_prompt("best iv therapy", "FuseHealth")
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])
        self.assertIn("40501", result["error"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_empty_answer_is_an_error_not_an_absent_verdict(self, post, _models):
        post.return_value = _dfs_response("   ")
        result = svc.check_prompt("best iv therapy", "FuseHealth")
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_no_brand_refuses_before_spending_money(self, post, _models):
        result = svc.check_prompt("best iv therapy", "")
        post.assert_not_called()
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_overlong_prompt_is_truncated_to_the_api_limit(self, post, _models):
        post.return_value = _dfs_response(ANSWER_CITED)
        svc.check_prompt("x" * 900, "FuseHealth")
        sent = post.call_args.kwargs["json"][0]["user_prompt"]
        self.assertEqual(len(sent), svc.PROMPT_MAX_CHARS)
