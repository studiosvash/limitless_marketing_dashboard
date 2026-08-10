"""A run must only pay for cells that have never been answered.

There was no "already run" concept anywhere: every "Run all" re-billed the entire grid, even
seconds after a successful run. The unit of work is a CELL -- one (prompt, platform) pair --
and the planner selects only cells with no usable stored result.

The approved rule is skip-if-ever-run with NO time-based staleness window: editing a prompt's
text re-runs it (the stored answer was measured against a different question), a failed check
retries because nothing was billed for it, and everything else is left alone until the user
explicitly asks for fresh answers with "Re-run".
"""
import os
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.dashboard.models import AITarget, AIPrompt
from apps.dashboard.services import ai_service
from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_URL = "sc-domain:fusehealth.com"
DFS_ENV = {"DATAFORSEO_LOGIN": "login", "DATAFORSEO_PASSWORD": "secret"}

ANSWER = """Top clinics:

1. FuseHealth — mobile drips.

All are licensed."""


def _dfs_response(text=ANSWER, cost=0.0055, status_code=20000):
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "cost": cost,
        "tasks": [{
            "status_code": status_code, "status_message": "Ok.", "cost": cost,
            "result": [{
                "model_name": "gpt-4o-mini", "input_tokens": 12, "output_tokens": 8,
                "items": [{"type": "message", "sections": [{"type": "text", "text": text}]}],
            }],
        }],
    }
    return resp


def _bootstrap(test_case):
    getp = mock.patch("pipeline.services.ai_visibility_service.requests.get",
                      side_effect=AssertionError("a test must never reach DataForSEO"))
    getp.start()
    test_case.addCleanup(getp.stop)
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)
    with get_session() as session:
        session.add(Site(site_url=SITE_URL, site_name="FuseHealth", slug="fusehealth",
                         is_active=1))
    user = get_user_model().objects.create_user("planner", password="x")
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@mock.patch.dict(os.environ, DFS_ENV, clear=False)
@mock.patch("apps.dashboard.services.ai_service._spawn_run_process", return_value=7)
class AIRunPlanningTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)
        AITarget.objects.create(site_url=SITE_URL, brand="FuseHealth", setup_done=True)
        self.prompt = AIPrompt.objects.create(
            site_url=SITE_URL, text="best iv therapy in austin",
            tracked_models=["chatgpt", "claude"])

    def _run(self, body=None):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/run", body or {},
                                     format="json")
        task_id = resp.json().get("task_id")
        if task_id:
            ai_service.execute_ai_run(SITE_URL, task_id)
        return resp.json()

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_a_second_run_plans_nothing_and_bills_nothing(self, post, spawn):
        post.return_value = _dfs_response()
        first = self._run()
        self.assertEqual(first["planned"], 2)
        self.assertEqual(post.call_count, 2)

        second = self._run()
        self.assertIsNone(second["task_id"])
        self.assertEqual(second["planned"], 0)
        self.assertEqual(second["detail"], "Everything is up to date.")
        self.assertEqual(post.call_count, 2, "no cell may be re-billed")

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_only_the_unrun_engine_is_planned_when_one_was_added_later(self, post, spawn):
        post.return_value = _dfs_response()
        self.prompt.tracked_models = ["chatgpt"]
        self.prompt.save()
        self._run()
        self.assertEqual(post.call_count, 1)

        self.prompt.tracked_models = ["chatgpt", "claude"]
        self.prompt.save()
        second = self._run()
        self.assertEqual(second["planned"], 1)
        self.assertEqual(post.call_count, 2)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_editing_the_prompt_text_makes_its_cells_unrun_again(self, post, spawn):
        post.return_value = _dfs_response()
        self._run()
        self.assertEqual(post.call_count, 2)

        self.prompt.text = "best iv therapy in dallas"
        self.prompt.save()
        again = self._run()
        self.assertEqual(again["planned"], 2, "a stored answer measured a different question")
        self.assertEqual(post.call_count, 4)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_force_re_runs_everything(self, post, spawn):
        post.return_value = _dfs_response()
        self._run()
        forced = self._run({"force": True})
        self.assertEqual(forced["planned"], 2)
        self.assertEqual(post.call_count, 4)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_a_failed_check_is_retried_because_nothing_was_billed(self, post, spawn):
        post.side_effect = RuntimeError("connection reset")
        self._run()
        self.assertEqual(post.call_count, 2)

        post.side_effect = None
        post.return_value = _dfs_response()
        retry = self._run()
        self.assertEqual(retry["planned"], 2)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_three_consecutive_failures_take_a_cell_out_of_auto_plans(self, post, spawn):
        post.side_effect = RuntimeError("connection reset")
        for _ in range(3):
            self._run()
        self.assertEqual(post.call_count, 6)

        blocked = self._run()
        self.assertIsNone(blocked["task_id"])
        self.assertEqual(blocked["planned"], 0)
        self.assertEqual(blocked["failing"], 2)
        self.assertEqual(post.call_count, 6, "one broken prompt must not tax every Run all")

        # ...but an explicit Re-run still forces them.
        forced = self._run({"force": True})
        self.assertEqual(forced["planned"], 2)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_a_recovered_cell_clears_its_failure_count(self, post, spawn):
        post.side_effect = RuntimeError("connection reset")
        self._run()
        self._run()
        post.side_effect = None
        post.return_value = _dfs_response()
        self._run()

        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(body["prompts"][0]["results"]["chatgpt"]["failCount"], 0)
        self.assertEqual(body["prompts"][0]["unrun"], [])

    def test_estimated_cost_is_unknown_not_zero_before_anything_is_billed(self, spawn):
        started = self.client_auth.post("/api/projects/fusehealth/ai/run", {},
                                        format="json").json()
        self.assertEqual(started["planned"], 2)
        self.assertIsNone(started["estimated_cost"],
                          "a paid action may not advertise itself as free")

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_the_get_reports_which_cells_are_unrun(self, post, spawn):
        post.return_value = _dfs_response()
        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(sorted(body["prompts"][0]["unrun"]), ["chatgpt", "claude"])

        self._run()
        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(body["prompts"][0]["unrun"], [])
        self.assertIsNotNone(body["costs"]["model"])


class AILegacyResultsAreNotRebilledTests(APITestCase):
    """Results stored before cells carried a prompt hash must not all be re-billed once on
    upgrade. A hash that is ABSENT means "we never recorded which text this measured", which
    is not evidence the text changed; only a hash that is PRESENT AND DIFFERENT is."""

    def setUp(self):
        self.client_auth = _bootstrap(self)
        AITarget.objects.create(site_url=SITE_URL, brand="FuseHealth", setup_done=True)
        self.prompt = AIPrompt.objects.create(site_url=SITE_URL, text="legacy prompt",
                                              tracked_models=["chatgpt"])
        ai_service.set_state(SITE_URL, ai_service.RESULTS_KEY, {
            str(self.prompt.id): {
                "lastRun": "2026-08-01T00:00:00+00:00",
                "results": {"chatgpt": {"state": "checked", "verdict": "cited",
                                        "mentioned": True, "cited": True, "position": 1}},
            }
        })

    @mock.patch("apps.dashboard.services.ai_service._spawn_run_process", return_value=7)
    def test_a_hashless_stored_result_still_counts_as_run(self, spawn):
        started = self.client_auth.post("/api/projects/fusehealth/ai/run", {},
                                        format="json").json()
        self.assertEqual(started["planned"], 0)
        spawn.assert_not_called()
