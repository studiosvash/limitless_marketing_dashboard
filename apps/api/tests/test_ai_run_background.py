"""POST /ai/run must not execute the run inside the request.

A full grid is prompts x engines sequential DataForSEO calls at up to 120s each, so the run
used to sit inside one POST for 8-15 minutes: nginx/gunicorn/Cloudflare killed the request, the
SPA's stuck busy flag turned every Run button into a silent no-op for the rest of the session,
and because results were persisted only ONCE after the whole loop, a worker killed at check 41
of 60 discarded 40 checks DataForSEO had already billed.

These tests pin the replacement: the POST plans, records a task, spawns `manage.py
run_ai_checks` and returns immediately; the worker persists after EVERY prompt and reports
progress on the task; the task -- not a client-side flag -- says whether a run is in flight.
Nothing here reaches the network.
"""
import os
import tempfile
from datetime import datetime, timedelta, timezone as dt_timezone
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

ANSWER_CITED = """Top IV therapy clinics in Austin:

1. FuseHealth — mobile drips, same-day booking.
2. Acme Wellness — downtown walk-in clinic.

All are licensed."""


def _dfs_response(text, cost=0.0055):
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "cost": cost,
        "tasks": [{
            "status_code": 20000, "status_message": "Ok.", "cost": cost,
            "result": [{
                "model_name": "gpt-4o-mini", "input_tokens": 120, "output_tokens": 80,
                "items": [{"type": "message", "sections": [{"type": "text", "text": text}]}],
            }],
        }],
    }
    return resp


def _bootstrap(test_case):
    # `resolve_model` reads the provider's free model list with requests.GET before every
    # check. Free is not the same as allowed: a test must never touch the real host, and
    # `available_models` already degrades to "keep the configured preference" on any failure.
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
    user = get_user_model().objects.create_user("bgrunner", password="x")
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@mock.patch.dict(os.environ, DFS_ENV, clear=False)
@mock.patch("apps.dashboard.services.ai_service._spawn_run_process", return_value=4242)
class AIRunIsNonBlockingTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)
        AITarget.objects.create(site_url=SITE_URL, brand="FuseHealth",
                                competitors=["Acme Wellness"], setup_done=True)
        self.p1 = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy in austin",
                                          tracked_models=["chatgpt"])

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_post_returns_a_task_id_without_calling_any_engine(self, post, spawn):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/run", {}, format="json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsNotNone(body["task_id"])
        self.assertEqual(body["planned"], 1)
        # The request itself must do no work: the paid calls belong to the spawned worker.
        post.assert_not_called()
        spawn.assert_called_once()

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_a_second_post_while_a_run_is_active_attaches_instead_of_forking(self, post, spawn):
        first = self.client_auth.post("/api/projects/fusehealth/ai/run", {}, format="json").json()
        with mock.patch("apps.sync.scheduling._process_alive", return_value=True):
            second = self.client_auth.post("/api/projects/fusehealth/ai/run", {},
                                           format="json").json()
        self.assertEqual(second["task_id"], first["task_id"])
        self.assertTrue(second["already_running"])
        self.assertEqual(spawn.call_count, 1)
        post.assert_not_called()

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_the_get_reports_the_run_as_in_flight(self, post, spawn):
        self.client_auth.post("/api/projects/fusehealth/ai/run", {}, format="json")
        with mock.patch("apps.sync.scheduling._process_alive", return_value=True):
            body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(body["run"]["state"], "running")
        self.assertEqual(body["run"]["total"], 1)
        self.assertEqual(body["run"]["completed"], 0)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_a_dead_worker_resolves_the_task_so_the_buttons_re_enable(self, post, spawn):
        self.client_auth.post("/api/projects/fusehealth/ai/run", {}, format="json")
        # Age the task past PID_GRACE so the liveness probe is consulted at all.
        task = ai_service.get_state(SITE_URL, ai_service.RUN_TASK_KEY, {})
        task["startedAt"] = (datetime.now(dt_timezone.utc) - timedelta(minutes=30)).isoformat()
        ai_service.set_state(SITE_URL, ai_service.RUN_TASK_KEY, task)

        with mock.patch("apps.sync.scheduling._process_alive", return_value=False):
            body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(body["run"]["state"], "error")
        self.assertIn("4242", body["run"]["error"])


@mock.patch.dict(os.environ, DFS_ENV, clear=False)
@mock.patch("apps.dashboard.services.ai_service._spawn_run_process", return_value=4242)
class AIRunWorkerTests(APITestCase):
    """The worker half: `execute_ai_run` is what `manage.py run_ai_checks` calls."""

    def setUp(self):
        self.client_auth = _bootstrap(self)
        AITarget.objects.create(site_url=SITE_URL, brand="FuseHealth", setup_done=True)
        self.p1 = AIPrompt.objects.create(site_url=SITE_URL, text="prompt one",
                                          tracked_models=["chatgpt"])
        self.p2 = AIPrompt.objects.create(site_url=SITE_URL, text="prompt two",
                                          tracked_models=["chatgpt"])

    def _start(self):
        return self.client_auth.post("/api/projects/fusehealth/ai/run", {},
                                     format="json").json()["task_id"]

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_worker_runs_the_plan_and_marks_the_task_done(self, post, spawn):
        post.return_value = _dfs_response(ANSWER_CITED)
        task_id = self._start()
        ai_service.execute_ai_run(SITE_URL, task_id)

        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(body["run"]["state"], "done")
        self.assertEqual(body["run"]["completed"], 2)
        self.assertEqual(body["run"]["total"], 2)
        for pr in body["prompts"]:
            self.assertEqual(pr["results"]["chatgpt"]["verdict"], "cited")

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_a_crash_midway_keeps_the_checks_already_paid_for(self, post, spawn):
        """The whole point of persisting per prompt: prompt one's billed result survives a
        worker killed while prompt two was in flight."""
        post.return_value = _dfs_response(ANSWER_CITED)
        task_id = self._start()

        real_check = ai_service.check_prompt
        calls = {"n": 0}

        def flaky(*a, **kw):
            calls["n"] += 1
            if calls["n"] > 1:
                raise KeyboardInterrupt("worker killed")
            return real_check(*a, **kw)

        with mock.patch.object(ai_service, "check_prompt", side_effect=flaky):
            with self.assertRaises(KeyboardInterrupt):
                ai_service.execute_ai_run(SITE_URL, task_id)

        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        done = [pr for pr in body["prompts"] if pr["results"].get("chatgpt")]
        self.assertEqual(len(done), 1, "the first prompt's paid result must be on disk already")
        self.assertEqual(done[0]["results"]["chatgpt"]["verdict"], "cited")

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_progress_is_reported_per_prompt(self, post, spawn):
        post.return_value = _dfs_response(ANSWER_CITED)
        task_id = self._start()
        seen = []
        real_check = ai_service.check_prompt

        def spy(*a, **kw):
            seen.append(dict(ai_service.get_state(SITE_URL, ai_service.RUN_TASK_KEY, {})))
            return real_check(*a, **kw)

        with mock.patch.object(ai_service, "check_prompt", side_effect=spy):
            ai_service.execute_ai_run(SITE_URL, task_id)

        self.assertEqual([t["completed"] for t in seen], [0, 1])
        self.assertEqual([t["current"] for t in seen], ["prompt one", "prompt two"])

    @mock.patch("apps.dashboard.services.budget_service.budget_status")
    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_budget_crossed_mid_run_stops_gracefully_and_keeps_partial_results(
            self, post, budget, spawn):
        post.return_value = _dfs_response(ANSWER_CITED)
        task_id = self._start()
        states = [{"exceeded": False, "spent": 1.0, "cap": 50.0},
                  {"exceeded": True, "spent": 50.0, "cap": 50.0}]
        budget.side_effect = lambda: states.pop(0) if len(states) > 1 else states[0]

        ai_service.execute_ai_run(SITE_URL, task_id)

        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(body["run"]["state"], "done")
        self.assertIn("budget", (body["run"]["detail"] or "").lower())
        done = [pr for pr in body["prompts"] if pr["results"].get("chatgpt")]
        self.assertEqual(len(done), 1)
