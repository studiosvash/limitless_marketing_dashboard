"""Visibility computed from the prompts the user actually added.

The AI Visibility tab led with DataForSEO's LLM Mentions index: counts over queries this
project never asked, two weeks stale, and impossible to drill into because that endpoint
returns totals only. Beside it the Prompts tab said 0. The user's objection was exact — "as a
user I won't go look at the database; whatever prompts I added, my overview should show THAT
data, and it should be real."

So the headline is now computed from the stored answers of the tracked prompts. Every number
here is traceable to a row the user can open in the Answer Inspector, and it moves when they
add a prompt or run a check — which is the whole point.

Absence of evidence is kept distinct from evidence of absence throughout: an unrun prompt and
an errored check are NOT counted as "nobody was mentioned there".
"""
from django.test import SimpleTestCase

from apps.dashboard.services.ai_service import build_prompt_visibility

YOU = "premierstaff.com"


def cell(**kw):
    base = {"state": "checked", "mentioned": False, "cited": False, "competitors": []}
    base.update(kw)
    return base


def prompt(pid, results, text="q"):
    return {"id": pid, "text": text, "results": results}


class PromptVisibilityTests(SimpleTestCase):
    def test_counts_prompts_that_mention_you(self):
        prompts = [
            prompt(1, {"chatgpt": cell(mentioned=True, cited=True, position=8)}),
            prompt(2, {"chatgpt": cell()}),
        ]
        out = build_prompt_visibility(prompts, YOU, [])
        self.assertEqual(out["you"]["prompts"], 1)
        self.assertEqual(out["total_prompts"], 2)

    def test_a_prompt_counts_once_however_many_engines_found_you(self):
        prompts = [prompt(1, {
            "chatgpt": cell(mentioned=True),
            "claude": cell(mentioned=True),
            "gemini": cell(mentioned=True),
        })]
        self.assertEqual(build_prompt_visibility(prompts, YOU, [])["you"]["prompts"], 1)

    def test_share_of_voice_is_computed_over_your_prompts_only(self):
        prompts = [
            prompt(1, {"chatgpt": cell(mentioned=True)}),
            prompt(2, {"chatgpt": cell(competitors=[{"name": "rival.com"}])}),
            prompt(3, {"chatgpt": cell(competitors=[{"name": "rival.com"}])}),
        ]
        out = build_prompt_visibility(prompts, YOU, ["rival.com"])
        rows = {r["domain"]: r for r in out["rows"]}
        self.assertEqual(rows[YOU]["prompts"], 1)
        self.assertEqual(rows["rival.com"]["prompts"], 2)
        # 1 of 3 appearances is yours.
        self.assertEqual(rows[YOU]["share"], 33)
        self.assertEqual(rows["rival.com"]["share"], 67)

    def test_a_tracked_competitor_never_seen_still_gets_a_row(self):
        """Absence is information on this page — a competitor at zero is a real finding."""
        prompts = [prompt(1, {"chatgpt": cell(mentioned=True)})]
        out = build_prompt_visibility(prompts, YOU, ["ghost.com"])
        rows = {r["domain"]: r for r in out["rows"]}
        self.assertIn("ghost.com", rows)
        self.assertEqual(rows["ghost.com"]["prompts"], 0)
        self.assertEqual(rows["ghost.com"]["share"], 0)

    def test_which_prompts_named_each_domain_is_returned_for_drill_down(self):
        prompts = [
            prompt(1, {"chatgpt": cell(competitors=[{"name": "rival.com"}])}, text="who staffs events"),
            prompt(2, {"chatgpt": cell(mentioned=True)}, text="bartenders per guest"),
        ]
        out = build_prompt_visibility(prompts, YOU, ["rival.com"])
        rows = {r["domain"]: r for r in out["rows"]}
        self.assertEqual(rows["rival.com"]["promptIds"], [1])
        self.assertEqual(rows[YOU]["promptIds"], [2])

    def test_unrun_prompts_are_reported_not_counted_as_absence(self):
        prompts = [
            prompt(1, {"chatgpt": cell(mentioned=True)}),
            prompt(2, {}),                       # never run
        ]
        out = build_prompt_visibility(prompts, YOU, [])
        self.assertEqual(out["run_prompts"], 1)
        self.assertEqual(out["unrun_prompts"], 1)
        self.assertEqual(out["total_prompts"], 2)

    def test_an_errored_check_observed_nothing(self):
        prompts = [prompt(1, {"claude": {"state": "error", "competitors": []}})]
        out = build_prompt_visibility(prompts, YOU, [])
        self.assertEqual(out["run_prompts"], 0)
        self.assertEqual(out["you"]["prompts"], 0)

    def test_no_run_prompts_yields_a_setup_state_not_a_zero_share(self):
        """0% would assert we looked and found nothing. We have not looked."""
        out = build_prompt_visibility([prompt(1, {})], YOU, ["rival.com"])
        self.assertEqual(out["state"], "no_runs")
        self.assertIsNone(out["you"]["share"])

    def test_per_engine_breakdown_reflects_real_checks(self):
        prompts = [
            prompt(1, {"chatgpt": cell(mentioned=True), "claude": cell()}),
            prompt(2, {"chatgpt": cell(mentioned=True)}),
        ]
        out = build_prompt_visibility(prompts, YOU, [])
        engines = {e["platform"]: e for e in out["engines"]}
        self.assertEqual(engines["chatgpt"]["you"], 2)
        self.assertEqual(engines["chatgpt"]["checks"], 2)
        self.assertEqual(engines["claude"]["you"], 0)
        self.assertEqual(engines["claude"]["checks"], 1)

    def test_cited_outranks_mentioned_in_the_headline_count(self):
        """Cited and mentioned are different strengths; both count as an appearance, and the
        stronger one is reported separately so the page can say which it was."""
        prompts = [
            prompt(1, {"chatgpt": cell(mentioned=True, cited=True)}),
            prompt(2, {"chatgpt": cell(mentioned=True)}),
        ]
        out = build_prompt_visibility(prompts, YOU, [])
        self.assertEqual(out["you"]["prompts"], 2)
        self.assertEqual(out["you"]["cited_prompts"], 1)

    def test_competitor_names_are_matched_case_insensitively(self):
        prompts = [prompt(1, {"chatgpt": cell(competitors=[{"name": "Rival.com"}])})]
        out = build_prompt_visibility(prompts, YOU, ["rival.com"])
        rows = {r["domain"]: r for r in out["rows"]}
        self.assertEqual(rows["rival.com"]["prompts"], 1)

    def test_an_untracked_domain_in_an_answer_is_ignored_here(self):
        """The share is over YOUR competitive set; a stray domain would change the
        denominator without the user having chosen to track it."""
        prompts = [prompt(1, {"chatgpt": cell(competitors=[{"name": "stranger.com"}])})]
        out = build_prompt_visibility(prompts, YOU, ["rival.com"])
        self.assertNotIn("stranger.com", {r["domain"] for r in out["rows"]})
