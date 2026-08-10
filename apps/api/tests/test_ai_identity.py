"""Your own entity must be detected on the same footing as a competitor's.

`_target_for_run` returned only brand / aliases / competitors -- the project's OWN DOMAIN was
never a detection needle. Competitors, meanwhile, are stored as domains and matched with
hostname expansion. Combine that with the word-boundary matcher and the brand "Limitless" does
NOT match inside "limitlesshold.com" (the next character is `h`), so an answer naming the site
by domain was scored "absent" and the grid said Not mentioned -- while the Inspector, which
tested identity a THIRD way (hostname match against project.domain), could render a "You" chip
on a citation sitting directly under that verdict.

One identity function now feeds the verdict, the grid and the chips. And because
`analyze_answer` is pure and network-free by design, correcting your targets can re-score the
answers you already paid for at zero cost, instead of requiring a paid re-run.
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

SITE_URL = "sc-domain:limitlesshold.com"
DFS_ENV = {"DATAFORSEO_LOGIN": "login", "DATAFORSEO_PASSWORD": "secret"}

# The reported answer shape: the site is named by DOMAIN, and the brand word "Limitless" never
# appears with a clean right-hand boundary.
ANSWER_BY_DOMAIN = """Providers worth a look:

1. limitlesshold.com — full-service, same-day booking.
2. rival.com — regional operator.

Check licensing before booking."""


def _dfs_response(text, cost=0.0055):
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "cost": cost,
        "tasks": [{
            "status_code": 20000, "status_message": "Ok.", "cost": cost,
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
        session.add(Site(site_url=SITE_URL, site_name="Limitless", slug="limitless",
                         is_active=1))
    user = get_user_model().objects.create_user("identity", password="x")
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


@mock.patch.dict(os.environ, DFS_ENV, clear=False)
@mock.patch("apps.dashboard.services.ai_service._spawn_run_process", return_value=7)
class AIOwnDomainIsDetectedTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)
        AITarget.objects.create(site_url=SITE_URL, brand="Limitless",
                                competitors=["rival.com"], setup_done=True)
        self.prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best provider",
                                              tracked_models=["chatgpt"])

    def _run(self):
        started = self.client_auth.post("/api/projects/limitless/ai/run", {},
                                        format="json").json()
        if started.get("task_id"):
            ai_service.execute_ai_run(SITE_URL, started["task_id"])

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_an_answer_naming_the_site_by_domain_is_not_absent(self, post, spawn):
        post.return_value = _dfs_response(ANSWER_BY_DOMAIN)
        self._run()
        cell = self.client_auth.get("/api/projects/limitless/ai").json()[
            "prompts"][0]["results"]["chatgpt"]
        self.assertEqual(cell["verdict"], "cited")
        self.assertEqual(cell["position"], 1)
        self.assertTrue(cell["mentioned"])

    def test_targets_expose_the_needles_the_verdict_actually_uses(self, spawn):
        targets = self.client_auth.get("/api/projects/limitless/ai").json()["targets"]
        self.assertIn("limitlesshold.com", targets["identity"])
        # The user's own typed aliases stay exactly as typed -- identity is additive.
        self.assertEqual(targets["aliases"], [])


@mock.patch.dict(os.environ, DFS_ENV, clear=False)
@mock.patch("apps.dashboard.services.ai_service._spawn_run_process", return_value=7)
class AIRescanTests(APITestCase):
    """Re-scoring stored answers against corrected targets is FREE: `analyze_answer` is pure
    text analysis with no network. This is what makes the Targets editor corrective."""

    def setUp(self):
        self.client_auth = _bootstrap(self)
        AITarget.objects.create(site_url=SITE_URL, brand="Limitless", competitors=[],
                                setup_done=True)
        self.prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best provider",
                                              tracked_models=["chatgpt"])

    def _run(self):
        started = self.client_auth.post("/api/projects/limitless/ai/run", {},
                                        format="json").json()
        if started.get("task_id"):
            ai_service.execute_ai_run(SITE_URL, started["task_id"])

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_rescan_picks_up_a_newly_added_competitor_without_a_paid_call(self, post, spawn):
        post.return_value = _dfs_response(ANSWER_BY_DOMAIN)
        self._run()
        before = self.client_auth.get("/api/projects/limitless/ai").json()
        self.assertEqual(before["prompts"][0]["results"]["chatgpt"]["competitors"], [])
        spent_before = before["budget"]["spent"]

        AITarget.objects.filter(site_url=SITE_URL).update(competitors=["rival.com"])
        calls_before = post.call_count
        resp = self.client_auth.post("/api/projects/limitless/ai/rescan", {}, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["rescanned"], 1)
        self.assertEqual(resp.json()["changed"], 1)
        self.assertEqual(post.call_count, calls_before, "a re-scan must never call an engine")

        after = self.client_auth.get("/api/projects/limitless/ai").json()
        self.assertEqual(after["prompts"][0]["results"]["chatgpt"]["competitors"][0]["name"],
                         "rival.com")
        self.assertEqual(after["budget"]["spent"], spent_before, "and must never cost anything")

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_rescan_with_no_stored_answers_is_an_honest_zero(self, post, spawn):
        resp = self.client_auth.post("/api/projects/limitless/ai/rescan", {}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"rescanned": 0, "changed": 0})
        post.assert_not_called()


@mock.patch.dict(os.environ, DFS_ENV, clear=False)
@mock.patch("apps.dashboard.services.ai_service._spawn_run_process", return_value=7)
class AIHistoryCapIsPerCellTests(APITestCase):
    """MAX_HISTORY was a single global cap of 50. One "Run all" over 20 prompts x 4 engines
    produces 80 entries and dropped 30 of them immediately -- so prompts that had JUST been
    run, and JUST been billed, opened the Inspector claiming they had never been run."""

    def setUp(self):
        self.client_auth = _bootstrap(self)
        AITarget.objects.create(site_url=SITE_URL, brand="Limitless", setup_done=True)
        self.prompts = [
            AIPrompt.objects.create(site_url=SITE_URL, text=f"prompt {i}",
                                    tracked_models=["chatgpt", "claude", "gemini",
                                                    "perplexity"])
            for i in range(20)
        ]

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_every_cell_of_one_big_run_keeps_its_answer(self, post, spawn):
        post.return_value = _dfs_response(ANSWER_BY_DOMAIN)
        started = self.client_auth.post("/api/projects/limitless/ai/run", {},
                                        format="json").json()
        self.assertEqual(started["planned"], 80)
        ai_service.execute_ai_run(SITE_URL, started["task_id"])

        history = self.client_auth.get("/api/projects/limitless/ai").json()["history"]
        cells = {(e["promptId"], e["platform"]) for e in history}
        self.assertEqual(len(cells), 80, "every prompt x engine the run paid for must be here")
