import tempfile
from pathlib import Path

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
        self.assertEqual(scoped["models"], ["chatgpt"])

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


class AIPromptsConfigActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_updates_tracked_models(self):
        prompt = AIPrompt.objects.create(site_url=SITE_URL, text="best iv therapy")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": prompt.id, "models": ["chatgpt", "claude"]},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        prompt.refresh_from_db()
        self.assertEqual(prompt.tracked_models, ["chatgpt", "claude"])

    def test_unknown_id_is_a_clean_404_not_a_false_success(self):
        # Final-review finding: a silent 200 here would tell the SPA "saved" for a config
        # change that never happened -- a false-success signal, not just a no-op.
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": 999999, "models": ["chatgpt"]},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_cross_project_id_is_404_and_leaves_other_project_untouched(self):
        other_prompt = AIPrompt.objects.create(site_url="https://other-project.com", text="not yours")
        resp = self.client_auth.post(
            "/api/projects/fusehealth/ai/prompts-config",
            {"id": other_prompt.id, "models": ["chatgpt"]},
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


class AIUnimplementedActionTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap_ai_test_env(self)

    def test_run_is_a_clean_400_not_a_crash(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/run", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_inspect_is_a_clean_400_not_a_crash(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/inspect", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_totally_unknown_action_is_a_clean_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ai/frobnicate", {}, format="json")
        self.assertEqual(resp.status_code, 400)


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
