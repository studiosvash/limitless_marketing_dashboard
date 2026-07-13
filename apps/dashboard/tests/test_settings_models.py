from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.dashboard.models import ProjectSettings


class ProjectSettingsUniquenessTests(TestCase):
    def setUp(self):
        self.site_url = "https://example.com"
        ProjectSettings.objects.create(site_url=self.site_url)

    def test_duplicate_site_url_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProjectSettings.objects.create(site_url=self.site_url)

    def test_different_site_url_is_allowed(self):
        other = ProjectSettings.objects.create(site_url="https://other.com")
        self.assertEqual(ProjectSettings.objects.count(), 2)
        self.assertEqual(other.site_url, "https://other.com")


class ProjectSettingsDefaultsTests(TestCase):
    def setUp(self):
        self.settings_obj = ProjectSettings.objects.create(site_url="https://example.com")

    def test_data_defaults_to_real_empty_dict(self):
        self.assertEqual(self.settings_obj.data, {})
        self.assertIsNotNone(self.settings_obj.data)
        self.assertIsInstance(self.settings_obj.data, dict)

    def test_data_default_survives_reload_from_db(self):
        self.settings_obj.refresh_from_db()
        self.assertEqual(self.settings_obj.data, {})

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.settings_obj.updated_at)

    def test_str(self):
        self.assertIn("example.com", str(self.settings_obj))
