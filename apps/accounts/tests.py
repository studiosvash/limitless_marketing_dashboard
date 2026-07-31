from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserProfile
from apps.dashboard.services.settings_service import LIVE_ROLES


class SeedUsersRolesTests(TestCase):
    """`seed_users` used to write apps.accounts.models.Role (founder/seo/ads) — the retired
    system nothing enforces (.claude/skills.md §7). Those strings meant nothing to
    check_owner_admin, which refuses only the literal "Analyst", so the accounts had full
    Admin access while the Settings team table displayed a role the UI has no concept of."""

    def test_seeded_roles_are_all_in_the_live_vocabulary(self):
        call_command("seed_users", stdout=StringIO(), stderr=StringIO())
        roles = dict(UserProfile.objects.values_list("user__username", "role"))

        self.assertEqual(roles["founder"], "Owner")
        self.assertEqual(roles["seo"], "Admin")
        self.assertEqual(roles["ads"], "Admin")
        for username, role in roles.items():
            self.assertIn(role, LIVE_ROLES, f"{username} was seeded with a non-live role")

    def test_rerun_is_idempotent(self):
        call_command("seed_users", stdout=StringIO(), stderr=StringIO())
        call_command("seed_users", stdout=StringIO(), stderr=StringIO())
        self.assertEqual(get_user_model().objects.filter(username="seo").count(), 1)
        self.assertEqual(UserProfile.objects.get(user__username="seo").role, "Admin")


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
