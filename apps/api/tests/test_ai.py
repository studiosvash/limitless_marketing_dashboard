import os
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

from apps.dashboard.models import AITarget, AIPromptList, AIPrompt


SITE_URL = "sc-domain:fusehealth.com"


def _bootstrap_ai_test_env(test_case):
    """Point the SQLAlchemy analytics DB at a fresh temp sqlite file, seed the `Site` row
    resolve_project_or_404 needs, and hand back an authenticated APIClient -- a plain function
    (not a shared TestCase subclass), matching the established pattern in
    apps/dashboard/services/tests/test_ai_service.py's `_new_analytics_db` and this project's
    test-class hygiene rule (every test class inherits directly from APITestCase; no
    inheritance-based test-duplication risk from a sibling test class)."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)

    with get_session() as session:
        session.add(Site(site_url=SITE_URL, site_name="FuseHealth",
                          slug="fusehealth", is_active=1))

    user = get_user_model().objects.create_user("founder1", password="x")
    token = Token.objects.get(user=user)
    client_auth = APIClient()
    client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client_auth


class AIGetEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_get_returns_real_seeded_data(self):
        AITarget.objects.create(
            site_url=SITE_URL, brand="FuseHealth", aliases=["Fuse"],
            competitors=["Acme"], setup_done=True,
        )
        plist = AIPromptList.objects.create(site_url=SITE_URL, name="Branded")
        AIPrompt.objects.create(site_url=SITE_URL, list=plist, text="best iv therapy near me",
                                 tracked_models=["chatgpt"])
        AIPrompt.objects.create(site_url=SITE_URL, text="unscoped prompt")

        resp = self.client_auth.get("/api/projects/fusehealth/ai")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        self.assertTrue(body["setupDone"])
        self.assertEqual(body["targets"], {
            "brand": "FuseHealth", "aliases": ["Fuse"], "competitors": ["Acme"],
        })
        self.assertEqual(len(body["lists"]), 1)
        self.assertEqual(body["lists"][0]["name"], "Branded")
        self.assertEqual(len(body["prompts"]), 2)
        texts = {p["text"] for p in body["prompts"]}
        self.assertEqual(texts, {"best iv therapy near me", "unscoped prompt"})
        scoped = next(p for p in body["prompts"] if p["text"] == "best iv therapy near me")
        self.assertEqual(scoped["listId"], plist.id)
        # cfg is a nested object (not flat "models") -- the SPA's render code dereferences
        # pr.cfg.models/.cadence and crashes without this exact shape.
        self.assertEqual(scoped["cfg"]["models"], ["chatgpt"])
        self.assertEqual(scoped["cfg"]["cadence"], "weekly")
        self.assertEqual(scoped["results"], {})

    def test_get_empty_db_is_honest_not_a_crash(self):
        resp = self.client_auth.get("/api/projects/fusehealth/ai")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body["setupDone"])
        self.assertEqual(body["targets"], {"brand": "", "aliases": [], "competitors": []})
        self.assertEqual(body["lists"], [])
        self.assertEqual(body["prompts"], [])
        self.assertEqual(body["aiKeywords"], [])

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/ai")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/ai")
        self.assertEqual(resp.status_code, 401)


class AISetupActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_setup_creates_target_and_prompts_and_persists_on_next_get(self):
        payload = {
            "brand": "FuseHealth",
            "aliases": ["Fuse", "Fuse Health"],
            "competitors": ["Acme", "Globex"],
            "prompts": ["best iv therapy", "  ", "top wellness clinics"],
        }
        resp = self.client_auth.post("/api/projects/fusehealth/ai/setup", payload, format="json")
        self.assertEqual(resp.status_code, 200)

        target = AITarget.objects.get(site_url=SITE_URL)
        self.assertTrue(target.setup_done)
        self.assertEqual(target.brand, "FuseHealth")
        self.assertEqual(target.aliases, ["Fuse", "Fuse Health"])
        self.assertEqual(target.competitors, ["Acme", "Globex"])
        # blank/whitespace-only prompt text is skipped
        self.assertEqual(AIPrompt.objects.filter(site_url=SITE_URL).count(), 2)

        # Prove persistence via a fresh GET, not just the mutation's own 200.
        get_resp = self.client_auth.get("/api/projects/fusehealth/ai")
        body = get_resp.json()
        self.assertTrue(body["setupDone"])
        self.assertEqual(body["targets"]["brand"], "FuseHealth")
        self.assertEqual(len(body["prompts"]), 2)


class AITargetsActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_targets_updates_not_duplicates(self):
        payload_1 = {"brand": "FuseHealth", "aliases": [], "competitors": ["Acme"]}
        payload_2 = {"brand": "FuseHealth Renamed", "aliases": ["FH"], "competitors": ["Acme", "Globex"]}

        resp1 = self.client_auth.post("/api/projects/fusehealth/ai/targets", payload_1, format="json")
        self.assertEqual(resp1.status_code, 200)
        resp2 = self.client_auth.post("/api/projects/fusehealth/ai/targets", payload_2, format="json")
        self.assertEqual(resp2.status_code, 200)

        self.assertEqual(AITarget.objects.filter(site_url=SITE_URL).count(), 1)
        target = AITarget.objects.get(site_url=SITE_URL)
        self.assertEqual(target.brand, "FuseHealth Renamed")
        self.assertEqual(target.aliases, ["FH"])
        self.assertEqual(target.competitors, ["Acme", "Globex"])
        # the targets action never sets setup_done itself
        self.assertFalse(target.setup_done)


class AIPromptsActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_prompts_added_count_matches_and_list_scoping_works(self):
        plist = AIPromptList.objects.create(site_url=SITE_URL, name="Branded")
        payload = {"texts": ["prompt one", "prompt two", ""], "listId": plist.id}

        resp = self.client_auth.post("/api/projects/fusehealth/ai/prompts", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"added": 2})

        prompts = AIPrompt.objects.filter(site_url=SITE_URL)
        self.assertEqual(prompts.count(), 2)
        for p in prompts:
            self.assertEqual(p.list_id, plist.id)

    def test_prompts_without_list_id_are_unscoped(self):
        payload = {"texts": ["standalone prompt"]}
        resp = self.client_auth.post("/api/projects/fusehealth/ai/prompts", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"added": 1})
        prompt = AIPrompt.objects.get(site_url=SITE_URL)
        self.assertIsNone(prompt.list_id)


class AIPromptsRemoveActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_removes_only_the_targeted_prompt(self):
        keep = AIPrompt.objects.create(site_url=SITE_URL, text="keep me")
        remove = AIPrompt.objects.create(site_url=SITE_URL, text="remove me")

        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-remove", {"id": remove.id}, format="json"
        )
        self.assertEqual(resp.status_code, 200)

        remaining = AIPrompt.objects.filter(site_url=SITE_URL)
        self.assertEqual(remaining.count(), 1)
        self.assertEqual(remaining.first().id, keep.id)

    def test_removes_multiple_targeted_prompts_by_ids(self):
        # The Tracked Prompts grid's select-all-then-remove bulk action posts "ids", not "id".
        keep = AIPrompt.objects.create(site_url=SITE_URL, text="keep me")
        remove_a = AIPrompt.objects.create(site_url=SITE_URL, text="remove a")
        remove_b = AIPrompt.objects.create(site_url=SITE_URL, text="remove b")

        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-remove",
            {"ids": [remove_a.id, remove_b.id]}, format="json",
        )
        self.assertEqual(resp.status_code, 200)

        remaining = AIPrompt.objects.filter(site_url=SITE_URL)
        self.assertEqual(remaining.count(), 1)
        self.assertEqual(remaining.first().id, keep.id)

    def test_bulk_remove_only_deletes_this_projects_prompts(self):
        other = AIPrompt.objects.create(site_url="https://other-project.com", text="not yours")
        mine = AIPrompt.objects.create(site_url=SITE_URL, text="mine")

        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-remove",
            {"ids": [mine.id, other.id]}, format="json",
        )
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(AIPrompt.objects.filter(id=mine.id).exists())
        self.assertTrue(AIPrompt.objects.filter(id=other.id).exists())


class AIPromptsConfigActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_updates_tracked_models(self):
        # Body shape here is the REAL one the SPA's "Save settings" button sends
        # ({id, cfg: {models, ...}, listId}) -- a final-review finding caught that an
        # earlier version of this test used a top-level "models" key that the SPA never
        # actually sends, masking a silent-data-loss bug (see the handler's own comment).
        prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": prompt.id, "cfg": {"models": ["chatgpt", "claude"], "cadence": "weekly",
                                       "country": "US", "city": "", "webSearch": False},
             "listId": None},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        prompt.refresh_from_db()
        self.assertEqual(prompt.tracked_models, ["chatgpt", "claude"])

    def test_a_save_with_no_model_changes_does_not_wipe_tracked_models(self):
        # The exact regression this bug caused: opening "Settings" and saving without
        # touching models used to wipe tracked_models to [] because the handler read a
        # top-level "models" key the real request body never had.
        prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy",
                                          tracked_models=["chatgpt"])
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": prompt.id, "cfg": {"models": ["chatgpt"], "cadence": "weekly",
                                       "country": "", "city": "", "webSearch": False},
             "listId": None},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        prompt.refresh_from_db()
        self.assertEqual(prompt.tracked_models, ["chatgpt"])

    def test_config_save_can_edit_the_prompt_text(self):
        prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": prompt.id, "cfg": {"models": ["chatgpt"]},
             "text": "what is the best iv therapy in austin"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        prompt.refresh_from_db()
        self.assertEqual(prompt.text, "what is the best iv therapy in austin")

    def test_config_save_with_blank_text_does_not_wipe_the_prompt(self):
        # Clearing the editable text box by accident must never save an empty question.
        prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": prompt.id, "cfg": {"models": ["chatgpt"]}, "text": "   "},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        prompt.refresh_from_db()
        self.assertEqual(prompt.text, "best iv therapy")

    def test_config_save_moves_prompt_to_a_new_list(self):
        plist = AIPromptList.objects.create(site_url=SITE_URL, name="New List")
        prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": prompt.id, "cfg": {"models": []}, "listId": plist.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        prompt.refresh_from_db()
        self.assertEqual(prompt.list_id, plist.id)

    def test_unknown_id_is_a_clean_404_not_a_false_success(self):
        # Final-review finding: a silent 200 here would tell the SPA "saved" for a config
        # change that never happened -- a false-success signal, not just a no-op.
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": 999999, "cfg": {"models": ["chatgpt"]}},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_cross_project_id_is_404_and_leaves_other_project_untouched(self):
        other_prompt = AIPrompt.objects.create(site_url="https://other-project.com", text="not yours")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": other_prompt.id, "cfg": {"models": ["chatgpt"]}},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)
        other_prompt.refresh_from_db()
        self.assertEqual(other_prompt.tracked_models, [])


class AIListsActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_create_returns_real_usable_fk(self):
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/lists", {"op": "create", "name": "New List"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        new_id = resp.json()["id"]
        self.assertTrue(AIPromptList.objects.filter(id=new_id, site_url=SITE_URL).exists())

        # The returned id must be immediately usable as a real FK, exactly like the SPA does
        # right after creating a list.
        prompt = AIPrompt.objects.create(site_url=SITE_URL, list_id=new_id, text="scoped prompt")
        prompt.refresh_from_db()
        self.assertEqual(prompt.list_id, new_id)
        self.assertEqual(prompt.list.name, "New List")

    def test_rename_and_delete(self):
        plist = AIPromptList.objects.create(site_url=SITE_URL, name="Old Name")

        rename_resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/lists",
            {"op": "rename", "id": plist.id, "name": "New Name"},
            format="json",
        )
        self.assertEqual(rename_resp.status_code, 200)
        plist.refresh_from_db()
        self.assertEqual(plist.name, "New Name")

        delete_resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/lists", {"op": "delete", "id": plist.id}, format="json"
        )
        self.assertEqual(delete_resp.status_code, 200)
        self.assertFalse(AIPromptList.objects.filter(id=plist.id).exists())

    def test_unknown_op_is_a_clean_400(self):
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/lists", {"op": "bogus"}, format="json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_rename_unknown_id_is_a_clean_404_not_a_false_success(self):
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/lists",
            {"op": "rename", "id": 999999, "name": "New Name"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_rename_cross_project_id_is_404_and_leaves_other_project_untouched(self):
        other_list = AIPromptList.objects.create(site_url="https://other-project.com", name="Not yours")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/lists",
            {"op": "rename", "id": other_list.id, "name": "Hijacked"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)
        other_list.refresh_from_db()
        self.assertEqual(other_list.name, "Not yours")

    def test_delete_cross_project_id_is_idempotent_and_leaves_other_project_untouched(self):
        # Delete stays a no-op (idempotent-safe, matching standard REST practice) -- unlike
        # rename/config, "the thing is gone" is the correct end state either way.
        other_list = AIPromptList.objects.create(site_url="https://other-project.com", name="Not yours")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/lists", {"op": "delete", "id": other_list.id}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(AIPromptList.objects.filter(id=other_list.id, name="Not yours").exists())


class AIRunInspectValidationTests(APITestCase):
    """run/inspect are implemented now (they call a live answer engine), so the old
    "unimplemented -> 400" expectation for `run` no longer describes the contract: the SPA's
    "Run all now" button really does post an empty body, and the honest answer to "run all"
    with nothing to run is a 200 saying zero prompts ran -- not a 400. Nothing here may reach
    the network: no OPENAI_API_KEY is set under test, so every platform is not_connected."""

    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_run_with_empty_body_and_no_prompts_runs_nothing(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/run", {}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ran"], 0)
        self.assertEqual(resp.json()["checked"], 0)
        self.assertEqual(resp.json()["cost"], 0.0)

    def test_run_with_unknown_prompt_id_is_a_clean_404_not_a_false_success(self):
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/run", {"promptId": 999999}, format="json"
        )
        self.assertEqual(resp.status_code, 404)

    def test_run_cross_project_prompt_id_is_404(self):
        other = AIPrompt.objects.create(site_url="https://other-project.com", text="not yours")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/run", {"promptId": other.id}, format="json"
        )
        self.assertEqual(resp.status_code, 404)

    def test_inspect_without_a_question_is_a_clean_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/inspect", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_totally_unknown_action_is_a_clean_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/frobnicate", {}, format="json")
        self.assertEqual(resp.status_code, 400)


ANSWER_CITED = """Top IV therapy clinics in Austin:

1. FuseHealth — mobile drips, same-day booking.
2. Acme Wellness — downtown walk-in clinic.

All are licensed."""

ANSWER_ABSENT = "Check your state's licensing directory for accredited providers."


def _openai_response(text, prompt_tokens=120, completion_tokens=80):
    """A stubbed OpenAI chat-completions response. The real API is NEVER called from a test:
    a check is a real charge."""
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                  "total_tokens": prompt_tokens + completion_tokens},
    }
    return resp


EXPECTED_COST = round(120 / 1_000_000 * 0.15 + 80 / 1_000_000 * 0.60, 6)


@mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
class AIRunPersistenceTests(APITestCase):
    """"Run now" must persist a real observed result and it must come back on the next GET --
    the whole point of the button. OpenAI is stubbed; nothing here reaches the network."""

    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)
        AITarget.objects.create(site_url=SITE_URL, brand="FuseHealth",
                                competitors=["Acme Wellness"], setup_done=True)
        self.prompt = AIPrompt.objects.create(
            site_url=SITE_URL, text="best iv therapy in austin", tracked_models=["chatgpt"],
        )

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_run_persists_a_real_result_visible_on_the_next_get(self, post):
        post.return_value = _openai_response(ANSWER_CITED)

        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/run", {"promptId": self.prompt.id}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["ran"], 1)
        self.assertEqual(resp.json()["checked"], 1)
        self.assertEqual(resp.json()["cost"], EXPECTED_COST)

        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        pr = body["prompts"][0]
        self.assertEqual(pr["results"]["chatgpt"]["verdict"], "cited")
        self.assertTrue(pr["results"]["chatgpt"]["cited"])
        self.assertEqual(pr["results"]["chatgpt"]["position"], 1)
        self.assertIsNotNone(pr["lastRun"])
        # The competitor really named in the answer, at its real rank.
        self.assertEqual(pr["results"]["chatgpt"]["competitors"][0]["name"], "Acme Wellness")

        # The answer is archived for the Answer Inspector, in the shape it reads.
        self.assertEqual(len(body["history"]), 1)
        entry = body["history"][0]
        self.assertEqual(entry["verdict"], "cited")
        self.assertEqual(entry["question"], "best iv therapy in austin")
        self.assertEqual(entry["scrape"]["model"], "gpt-4o-mini")
        self.assertEqual(entry["scrape"]["citations"], [])
        self.assertTrue(any(p["hit"] for p in entry["scrape"]["paragraphs"]))

        # Real spend was recorded and is read back as real money, not an estimate.
        self.assertEqual(body["budget"]["spent"], EXPECTED_COST)
        self.assertEqual(body["costs"]["model"], EXPECTED_COST)
        self.assertEqual(body["kpis"]["mentions"], 1)
        self.assertEqual(body["kpis"]["prompt_coverage"], {"cited": 1, "total": 1})

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_absent_answer_is_recorded_as_absent_not_dropped(self, post):
        post.return_value = _openai_response(ANSWER_ABSENT)
        self.client_auth.post("/api/projects/fusehealth/ai/run",
                              {"promptId": self.prompt.id}, format="json")
        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        cell = body["prompts"][0]["results"]["chatgpt"]
        self.assertEqual(cell["verdict"], "absent")
        self.assertFalse(cell["mentioned"])
        self.assertEqual(body["kpis"]["mentions"], 0)
        self.assertEqual(body["kpis"]["prompt_coverage"], {"cited": 0, "total": 1})

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_unconnected_engine_is_recorded_as_not_connected_never_simulated(self, post):
        post.return_value = _openai_response(ANSWER_CITED)
        self.prompt.tracked_models = ["chatgpt", "claude", "perplexity"]
        self.prompt.save()

        resp = self.client_auth.post("/api/projects/fusehealth/ai/run",
                                     {"promptId": self.prompt.id}, format="json")
        # Only the one connected engine was actually called.
        self.assertEqual(post.call_count, 1)
        self.assertEqual(resp.json()["checked"], 1)
        self.assertEqual(resp.json()["notConnected"], ["claude", "perplexity"])

        results = self.client_auth.get("/api/projects/fusehealth/ai").json()["prompts"][0]["results"]
        for pid in ("claude", "perplexity"):
            self.assertEqual(results[pid]["state"], "not_connected")
            self.assertIsNone(results[pid]["verdict"])
            self.assertFalse(results[pid]["mentioned"])
            self.assertEqual(results[pid]["cost"], 0.0)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_run_without_a_brand_spends_nothing(self, post):
        AITarget.objects.filter(site_url=SITE_URL).update(brand="")
        resp = self.client_auth.post("/api/projects/fusehealth/ai/run",
                                     {"promptId": self.prompt.id}, format="json")
        post.assert_not_called()
        self.assertEqual(resp.json()["checked"], 0)
        self.assertEqual(resp.json()["cost"], 0.0)
        self.assertIn("brand", resp.json()["detail"].lower())

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_run_all_covers_every_prompt_in_the_project_only(self, post):
        post.return_value = _openai_response(ANSWER_CITED)
        AIPrompt.objects.create(site_url=SITE_URL, text="second prompt",
                                tracked_models=["chatgpt"])
        AIPrompt.objects.create(site_url="https://other-project.com", text="not ours",
                                tracked_models=["chatgpt"])

        resp = self.client_auth.post("/api/projects/fusehealth/ai/run", {}, format="json")
        self.assertEqual(resp.json()["ran"], 2)
        self.assertEqual(post.call_count, 2)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_run_by_list_scopes_to_that_list(self, post):
        post.return_value = _openai_response(ANSWER_CITED)
        plist = AIPromptList.objects.create(site_url=SITE_URL, name="Branded")
        AIPrompt.objects.create(site_url=SITE_URL, list=plist, text="in the list",
                                tracked_models=["chatgpt"])

        resp = self.client_auth.post("/api/projects/fusehealth/ai/run",
                                     {"listId": plist.id}, format="json")
        self.assertEqual(resp.json()["ran"], 1)
        self.assertEqual(post.call_count, 1)


class AIRunWithoutApiKeyTests(APITestCase):
    """Without OPENAI_API_KEY the whole feature degrades honestly -- exactly as
    ai_summary_service skips -- rather than simulating an answer."""

    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)
        AITarget.objects.create(site_url=SITE_URL, brand="FuseHealth", setup_done=True)
        self.prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy",
                                              tracked_models=["chatgpt"])

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_run_makes_no_call_and_reports_why(self, post):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/run",
                                     {"promptId": self.prompt.id}, format="json")
        post.assert_not_called()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["checked"], 0)
        self.assertEqual(resp.json()["cost"], 0.0)
        self.assertIn("OPENAI_API_KEY", resp.json()["detail"])

        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(body["history"], [])
        self.assertEqual(body["budget"]["spent"], 0)
        self.assertIsNone(body["costs"]["model"])
        self.assertEqual(body["prompts"][0]["results"]["chatgpt"]["state"], "not_connected")
        self.assertIsNone(body["prompts"][0]["lastRun"])

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_inspect_is_503_not_a_fabricated_answer(self, post):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/inspect",
                                     {"question": "best iv therapy"}, format="json")
        post.assert_not_called()
        self.assertEqual(resp.status_code, 503)
        self.assertIn("OPENAI_API_KEY", resp.json()["detail"])


@mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False)
class AIInspectPersistenceTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)
        AITarget.objects.create(site_url=SITE_URL, brand="FuseHealth",
                                competitors=["Acme Wellness"], setup_done=True)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_inspect_returns_the_entry_and_stores_it_in_history(self, post):
        post.return_value = _openai_response(ANSWER_CITED)
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/inspect",
            {"question": "best iv therapy in austin", "promptId": None}, format="json",
        )
        self.assertEqual(resp.status_code, 200)
        entry = resp.json()
        self.assertEqual(entry["verdict"], "cited")
        self.assertEqual(entry["position"], 1)
        self.assertEqual(entry["cost"], EXPECTED_COST)
        self.assertEqual(entry["scrape"]["citations"], [])

        body = self.client_auth.get("/api/projects/fusehealth/ai").json()
        self.assertEqual(len(body["history"]), 1)
        self.assertEqual(body["history"][0]["question"], "best iv therapy in austin")
        self.assertEqual(body["costs"]["inspect"], EXPECTED_COST)
        self.assertEqual(body["budget"]["spent"], EXPECTED_COST)

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_inspecting_a_tracked_prompt_also_updates_its_row(self, post):
        post.return_value = _openai_response(ANSWER_CITED)
        prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy in austin",
                                         tracked_models=["chatgpt"])
        self.client_auth.post(
            "/api/projects/fusehealth/ai/inspect",
            {"question": prompt.text, "promptId": prompt.id}, format="json",
        )
        pr = self.client_auth.get("/api/projects/fusehealth/ai").json()["prompts"][0]
        self.assertEqual(pr["results"]["chatgpt"]["verdict"], "cited")
        self.assertIsNotNone(pr["lastRun"])

    @mock.patch("pipeline.services.ai_visibility_service.requests.post")
    def test_provider_failure_is_a_400_not_a_fabricated_entry(self, post):
        post.side_effect = RuntimeError("connection reset")
        resp = self.client_auth.post("/api/projects/fusehealth/ai/inspect",
                                     {"question": "best iv therapy"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.client_auth.get("/api/projects/fusehealth/ai").json()["history"], [])


class AIMutationAuthAndSlugTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_unauthenticated_post_is_401(self):
        resp = APIClient().post(
            "/api/projects/fusehealth/ai/targets", {"brand": "x"}, format="json"
        )
        self.assertEqual(resp.status_code, 401)

    def test_unknown_slug_post_is_404(self):
        resp = self.client_auth.post(
            "/api/projects/does-not-exist/ai/targets", {"brand": "x"}, format="json"
        )
        self.assertEqual(resp.status_code, 404)
