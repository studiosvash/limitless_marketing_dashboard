"""POST /api/auth/password — regression for the missing login_not_required decorator.

Every API view must opt out of LoginRequiredMiddleware so DRF's own token auth runs.
ChangePasswordView was the one view in views.py without the decorator, so a Bearer-token
request was 302'd to the login page instead of reaching the view. These tests pin both the
happy path and the failure mode that made the bug invisible to session-cookie clients.
"""
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase


class ChangePasswordAuthTests(APITestCase):
    def _client(self, username="pw-user", password="original-pw"):
        user = get_user_model().objects.create_user(username, password=password)
        token = Token.objects.get(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        return user, client

    def test_bearer_token_request_reaches_the_view_not_a_login_redirect(self):
        user, client = self._client()
        resp = client.post("/api/auth/password", {
            "old_password": "original-pw", "new_password": "brand-new-pw",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})
        user.refresh_from_db()
        self.assertTrue(user.check_password("brand-new-pw"))

    def test_wrong_current_password_is_400_not_302(self):
        _, client = self._client("pw-user2")
        resp = client.post("/api/auth/password", {
            "old_password": "not-it", "new_password": "brand-new-pw",
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_anonymous_request_is_still_rejected(self):
        resp = APIClient().post("/api/auth/password", {
            "old_password": "x", "new_password": "y-long-enough",
        }, format="json")
        self.assertIn(resp.status_code, (401, 403))
