from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token

from apps.dashboard.models import Insight


class SpaViewTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_logged_in_gets_html_with_bootstrap_script(self):
        user = get_user_model().objects.create_user("viewer", password="x")
        self.client.force_login(user)
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/html; charset=utf-8")
        token = Token.objects.get(user=user).key
        body = resp.content.decode()
        self.assertIn(f"window.FuseAPI.config.authToken = '{token}'", body)
        self.assertIn("window.FuseAPI.config.baseUrl = '/'", body)
        # The bootstrap must come after api.js defines window.FuseAPI.
        self.assertLess(body.index("/static/spa/app/api.js"), body.index("FuseAPI.config.authToken"))


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
