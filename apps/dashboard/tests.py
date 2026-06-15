from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.dashboard.models import Insight


class InsightTests(TestCase):
    def test_create_with_user(self):
        user = get_user_model().objects.create_user("seo_lead", password="x")
        ins = Insight.objects.create(
            site_url="https://fusehealth.com",
            date=date(2026, 6, 1),
            team="seo",
            title="Relaunched pricing page",
            description="Rebuilt the pricing page copy.",
            impact="positive",
            created_by=user,
        )
        self.assertEqual(ins.impact, "positive")
        self.assertFalse(ins.is_verified)
        self.assertEqual(ins.created_by.username, "seo_lead")

    def test_created_by_nullable(self):
        ins = Insight.objects.create(
            site_url="https://fusehealth.com",
            date=date(2026, 6, 1),
            team="ads",
            title="No owner",
            description="Imported note.",
        )
        self.assertIsNone(ins.created_by)
        self.assertEqual(ins.impact, "neutral")
