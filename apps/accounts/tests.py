from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token


class AutoTokenTests(TestCase):
    def test_new_user_gets_a_token(self):
        user = get_user_model().objects.create_user("newbie", password="x")
        self.assertTrue(Token.objects.filter(user=user).exists())

    def test_existing_user_keeps_the_same_token_on_resave(self):
        user = get_user_model().objects.create_user("resaved", password="x")
        original_key = Token.objects.get(user=user).key
        user.first_name = "Changed"
        user.save()
        self.assertEqual(Token.objects.get(user=user).key, original_key)
