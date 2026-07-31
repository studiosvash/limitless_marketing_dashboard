from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.dashboard.models import Insight


class SpaViewTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_app_url_still_redirects_to_the_spa_root(self):
        """/app/ was the SPA's original home; config/urls.py keeps it as a redirect so old
        bookmarks survive. Asserted separately from the anonymous case above, which never
        reaches the redirect because LoginRequiredMiddleware answers first."""
        user = get_user_model().objects.create_user("bookmarker", password="x")
        self.client.force_login(user)
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/")

    def test_logged_in_gets_the_spa_html(self):
        user = get_user_model().objects.create_user("viewer", password="x")
        self.client.force_login(user)
        # The SPA is served at "/" (config/urls.py: path('', spa_index, name='spa')); it moved
        # off /app/ when the Django template dashboard was removed.
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/html; charset=utf-8")
        body = resp.content.decode()
        # It's the approved SPA (loads api.js) configured to hit the real API rather than
        # the bundled fixtures. The data-props `apiBaseUrl` default is deliberately "" —
        # the real value is forced by the bootstrap interceptor spa_index() injects, which
        # is the only thing that runs early enough (app/api.js executes twice and reassigns
        # window.FuseAPI each time; see the spa_views module docstring). `'/'` and not `''`
        # is load-bearing: an empty string is falsy, so the transport would silently serve
        # fixture data forever.
        self.assertIn("/static/spa/app/api.js", body)
        self.assertIn("v.config.baseUrl='/'", body)
        # The token and role the SPA authenticates every API call with come from the same
        # injected block, so a logged-in response must carry them.
        self.assertIn("var authToken=", body)
        self.assertIn('"username": "viewer"', body)


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
