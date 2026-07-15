from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.dashboard.models import AIPrompt, AIPromptList, AITarget


class AITargetUniquenessTests(TestCase):
    def setUp(self):
        self.site_url = "https://example.com"
        AITarget.objects.create(site_url=self.site_url, brand="Acme")

    def test_duplicate_site_url_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AITarget.objects.create(site_url=self.site_url, brand="Other Brand")

    def test_different_site_url_is_allowed(self):
        other = AITarget.objects.create(site_url="https://other.com", brand="Other Brand")
        self.assertEqual(AITarget.objects.count(), 2)
        self.assertEqual(other.site_url, "https://other.com")


class AITargetDefaultsTests(TestCase):
    def setUp(self):
        self.target = AITarget.objects.create(site_url="https://example.com")

    def test_aliases_and_competitors_default_to_real_empty_lists(self):
        self.assertEqual(self.target.aliases, [])
        self.assertEqual(self.target.competitors, [])
        self.assertIsNotNone(self.target.aliases)
        self.assertIsNotNone(self.target.competitors)

    def test_setup_done_defaults_false_and_brand_defaults_empty(self):
        self.assertFalse(self.target.setup_done)
        self.assertEqual(self.target.brand, "")

    def test_str(self):
        self.assertIn("example.com", str(self.target))


class AIPromptNullableListTests(TestCase):
    def setUp(self):
        self.site_url = "https://example.com"

    def test_prompt_with_no_list_is_valid(self):
        prompt = AIPrompt.objects.create(site_url=self.site_url, text="best CRM software")
        prompt.refresh_from_db()
        self.assertIsNone(prompt.list)
        self.assertIsNone(prompt.list_id)

    def test_prompt_with_list_links_correctly(self):
        plist = AIPromptList.objects.create(site_url=self.site_url, name="Branded")
        prompt = AIPrompt.objects.create(site_url=self.site_url, text="who makes X", list=plist)
        prompt.refresh_from_db()
        self.assertEqual(prompt.list_id, plist.id)
        self.assertIn(prompt, plist.prompts.all())

    def test_deleting_list_sets_prompt_list_to_null(self):
        plist = AIPromptList.objects.create(site_url=self.site_url, name="Branded")
        prompt = AIPrompt.objects.create(site_url=self.site_url, text="who makes X", list=plist)
        plist.delete()
        prompt.refresh_from_db()
        self.assertIsNone(prompt.list_id)


class AIPromptDefaultsTests(TestCase):
    def setUp(self):
        self.prompt = AIPrompt.objects.create(
            site_url="https://example.com", text="what is the best widget"
        )

    def test_tracked_models_defaults_to_real_empty_list(self):
        self.assertEqual(self.prompt.tracked_models, [])
        self.assertIsNotNone(self.prompt.tracked_models)

    def test_str(self):
        self.assertIn("what is the best widget", str(self.prompt))


class AIPromptListBasicTests(TestCase):
    def setUp(self):
        self.plist = AIPromptList.objects.create(
            site_url="https://example.com", name="Competitor prompts"
        )

    def test_create_and_field_roundtrip(self):
        self.plist.refresh_from_db()
        self.assertEqual(self.plist.site_url, "https://example.com")
        self.assertEqual(self.plist.name, "Competitor prompts")
        self.assertIsNotNone(self.plist.created_at)

    def test_str(self):
        self.assertIn("Competitor prompts", str(self.plist))
