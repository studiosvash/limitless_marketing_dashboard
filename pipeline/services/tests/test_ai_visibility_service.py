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
                  annotations=None, model_name="gpt-4o-mini", status_code=20000,
                  web_search_used=None, status_message=None):
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
            "status_message": status_message or ("Ok." if status_code == 20000 else "Task error."),
            "cost": cost,
            "result": [{
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                **({"web_search": web_search_used} if web_search_used is not None else {}),
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

    def test_top_pick_is_the_answers_first_list_item_whoever_it_names(self):
        # ANSWER_COMPETITOR_ONLY ranks Acme Wellness first and never names us — the top pick
        # is still extracted, because "who did the model actually recommend" is a fact of the
        # answer independent of whether we appear in it.
        result = svc.analyze_answer(ANSWER_COMPETITOR_ONLY, "FuseHealth")
        self.assertIn("Acme Wellness", result["topPick"])

    def test_an_answer_with_no_list_has_no_top_pick(self):
        self.assertIsNone(svc.analyze_answer(ANSWER_MENTION_ONLY, "FuseHealth")["topPick"])


class CitationMatchingTests(SimpleTestCase):
    """How tracked entities are found in provider-verified citations.

    The 2026-08-27 addition under test: a competitor tracked by BARE BRAND NAME
    ("eventstaff") now matches a citation whose host's registrable label equals it exactly
    (eventstaff.com, blog.eventstaff.com, eventstaff.co.uk). Live data showed the gap:
    eventstaff.com stood at source #2 of a stored Perplexity answer while the tracked
    competitor "eventstaff" reported nothing, because only hostname-shaped needles were ever
    compared against citation URLs.
    """

    CITS = [
        {"title": "Runway Waiters", "url": "https://www.runwaywaiters.com/hire"},
        {"title": "Booking guide — Eventstaff", "url": "https://eventstaff.com/blog/guide"},
    ]

    def test_bare_name_competitor_matches_the_hosts_registrable_label(self):
        result = svc.analyze_answer("Rates vary by city.", "Premier Staff",
                                    competitors=["eventstaff"], citations=self.CITS)
        self.assertEqual(len(result["competitors"]), 1)
        hit = result["competitors"][0]
        self.assertEqual(hit["name"], "eventstaff")
        self.assertTrue(hit["cited"])
        self.assertEqual(hit["position"], 2)  # the [n] the user sees in the source list

    def test_bare_name_matches_subdomain_and_cctld_hosts(self):
        for url in ("https://blog.eventstaff.com/post", "https://eventstaff.co.uk/rates"):
            result = svc.analyze_answer("Rates vary.", "Premier Staff",
                                        competitors=["eventstaff"],
                                        citations=[{"title": "t", "url": url}])
            self.assertTrue(result["competitors"], url)

    def test_bare_name_is_equality_never_a_substring(self):
        # "acme" must not match acme-lookalike.io — the design rule the substring test broke.
        result = svc.analyze_answer("Rates vary.", "Acme",
                                    citations=[{"title": "t",
                                                "url": "https://acme-lookalike.io/x"}])
        self.assertEqual(result["verdict"], "absent")

    def test_names_with_spaces_or_under_four_chars_never_match_a_label(self):
        result = svc.analyze_answer("Rates vary.", "Premier Staff",
                                    competitors=["julia valler", "ats"],
                                    citations=[{"title": "t", "url": "https://ats.com/x"}])
        self.assertEqual(result["competitors"], [])

    def test_own_domain_citation_still_upgrades_the_verdict_to_cited(self):
        # The pre-existing hostname-needle path, untouched: our domain rides in as an alias.
        result = svc.analyze_answer("Nothing names us in prose.", "Premier Staff",
                                    aliases=["premierstaff.com"],
                                    citations=[{"title": "Average cost",
                                                "url": "https://premierstaff.com/blog/cost"}])
        self.assertEqual(result["verdict"], "cited")
        self.assertEqual(result["position"], 1)


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
        # Read from PLATFORMS rather than pinned: the configured default is policy, and this
        # test is about the request shape, not about which tier is current this quarter.
        self.assertEqual(task["model_name"], svc.PLATFORMS["chatgpt"]["model"])
        self.assertEqual(task["user_prompt"], "best iv therapy in austin")
        # Web search is the DEFAULT (2026-08-27): citations only exist on a web-search-enabled
        # check, and the no-arg call is what the Answer Inspector and any future caller gets.
        self.assertIs(task["web_search"], True)
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
    def test_a_rejected_optional_field_is_dropped_and_the_call_retried(self, post, _models):
        # Live failure this reproduces: gpt-5.x rejects `max_output_tokens` with 40501.
        # The rejected task bills 0, so dropping the named field and retrying turns a dead
        # check into a real answer for the same money.
        # Learned rejections are process-global by design; keep them out of other tests.
        self.addCleanup(svc._REJECTED_FIELDS.clear)
        # Both live wordings of the rejection, in the order gpt-5.4-mini produced them.
        post.side_effect = [
            _dfs_response("", status_code=40501,
                          status_message="Invalid Field: 'max_output_tokens'."),
            _dfs_response("", status_code=40501,
                          status_message="Invalid Field: 'this model does not support "
                                         "'temperature''."),
            _dfs_response(ANSWER_CITED),
        ]
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth")
        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "cited")
        retried = post.call_args.kwargs["json"][0]
        self.assertNotIn("max_output_tokens", retried)
        self.assertNotIn("temperature", retried)
        self.assertEqual(post.call_count, 3)

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_an_unknown_task_failure_still_errors_without_retrying(self, post, _models):
        post.return_value = _dfs_response("", status_code=40402,
                                          status_message="Some other failure.")
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth")
        self.assertEqual(result["state"], "error")
        self.assertEqual(post.call_count, 1)

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_truncated_answer_is_an_error_not_an_absent_verdict(self, post, _models):
        # Live failure this reproduces: the stream died right after "…options to consider:",
        # so the list that would have named the brands never arrived. "Absent" from that stump
        # would be fabricated; an error cell gets retried by the next run instead.
        post.return_value = _dfs_response(
            "Here are several reputable options to consider:\n\n ")
        result = svc.check_prompt("best staffing agency in nyc", "FuseHealth")
        self.assertEqual(result["state"], "error")
        self.assertIsNone(result["verdict"])
        self.assertIn("truncated", result["error"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_response_web_search_flag_and_top_pick_are_reported(self, post, _models):
        # DataForSEO says whether the provider REALLY searched; None when the envelope is
        # silent. The top pick rides along from analyze_answer on every checked result.
        post.return_value = _dfs_response(ANSWER_CITED, web_search_used=True)
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth")
        self.assertIs(result["webSearchUsed"], True)
        self.assertIn("FuseHealth", result["topPick"])

        post.return_value = _dfs_response(ANSWER_CITED)
        self.assertIsNone(
            svc.check_prompt("best iv therapy in austin", "FuseHealth")["webSearchUsed"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_chatgpt_and_claude_get_the_full_web_search_field_set(self, post, _models):
        # Both providers document web_search, force_web_search, country AND city. force_web_
        # search matters: a model handed the search tool may still answer from memory, and the
        # check must measure the grounded answer.
        for platform in ("chatgpt", "claude"):
            post.return_value = _dfs_response(ANSWER_CITED)
            result = svc.check_prompt("best iv therapy", "FuseHealth", platform=platform,
                                      web_search=True, country="US", city="Austin")
            task = post.call_args.kwargs["json"][0]
            self.assertIs(task["web_search"], True, platform)
            self.assertIs(task["force_web_search"], True, platform)
            self.assertEqual(task["web_search_country_iso_code"], "US", platform)
            self.assertEqual(task["web_search_city"], "Austin", platform)
            self.assertEqual(result["location"], "US · Austin", platform)

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_gemini_gets_web_search_only_and_never_a_geo_field(self, post, _models):
        # The exact production failure this guards: gemini rejects geo fields with
        # `40501 Invalid Field: 'web_search_country_iso_code'`, so sending the configured
        # country errored the whole check instead of being ignored.
        post.return_value = _dfs_response(ANSWER_CITED, model_name="gemini-2.5-flash-lite")
        result = svc.check_prompt("best iv therapy", "FuseHealth", platform="gemini",
                                  web_search=True, country="US", city="Austin")
        task = post.call_args.kwargs["json"][0]
        self.assertIs(task["web_search"], True)
        self.assertNotIn("force_web_search", task)
        self.assertNotIn("web_search_country_iso_code", task)
        self.assertNotIn("web_search_city", task)
        # The location field reports what was SENT, never what was configured.
        self.assertIsNone(result["location"])

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_perplexity_gets_only_the_country_code(self, post, _models):
        # Sonar models always search; the endpoint documents NO web_search/force/city fields.
        post.return_value = _dfs_response(ANSWER_CITED, model_name="sonar")
        result = svc.check_prompt("best iv therapy", "FuseHealth", platform="perplexity",
                                  web_search=True, country="US", city="Austin")
        task = post.call_args.kwargs["json"][0]
        self.assertNotIn("web_search", task)
        self.assertNotIn("force_web_search", task)
        self.assertNotIn("web_search_city", task)
        self.assertEqual(task["web_search_country_iso_code"], "US")
        self.assertEqual(result["location"], "US")

    @mock.patch.dict(os.environ, DFS_ENV, clear=False)
    @mock.patch.object(svc.requests, "post")
    def test_web_search_false_is_still_honoured_and_omitted_from_the_task(self, post, _models):
        # The opt-out must keep working: a caller that explicitly wants the cheaper,
        # source-less completion sends no web_search key at all (DataForSEO treats absence
        # as off; sending false would be redundant).
        post.return_value = _dfs_response(ANSWER_CITED)
        result = svc.check_prompt("best iv therapy in austin", "FuseHealth", web_search=False)
        self.assertTrue(result["ok"])
        self.assertNotIn("web_search", post.call_args.kwargs["json"][0])

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
