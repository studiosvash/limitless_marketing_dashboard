from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase


class PingAuthTests(APITestCase):
    def test_unauthenticated_ping_is_401(self):
        client = APIClient()
        resp = client.get("/api/ping")
        self.assertEqual(resp.status_code, 401)

    def test_bearer_token_ping_is_200(self):
        user = get_user_model().objects.create_user("pinger", password="x")
        token = Token.objects.get(user=user)  # auto-created by the accounts signal
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        resp = client.get("/api/ping")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})

    def test_default_token_keyword_is_rejected(self):
        """Confirms the Bearer override is active — DRF's default `Token` keyword must NOT work,
        otherwise a future settings change could silently revert to the wrong scheme."""
        user = get_user_model().objects.create_user("pinger2", password="x")
        token = Token.objects.get(user=user)  # auto-created by the accounts signal
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        resp = client.get("/api/ping")
        self.assertEqual(resp.status_code, 401)
