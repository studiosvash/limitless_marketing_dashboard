import datetime
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserInvitation, UserProfile
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


class AcceptInvitePageTests(TestCase):
    """The page the invitation email links to. It has to work for someone with no account
    and no session -- the previous SPA route sent them to the login form instead."""

    def setUp(self):
        self.owner = get_user_model().objects.create_user("owner", email="owner@x.com", password="x")
        self.invitation = UserInvitation.objects.create(
            email="invitee@company.com", role="Analyst", invited_by=self.owner,
            token="tok-valid", expires_at=timezone.now() + datetime.timedelta(hours=48),
        )

    def test_page_is_reachable_logged_out(self):
        resp = self.client.get("/accept-invite/?token=tok-valid")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "invitee@company.com")

    def test_expired_token_explains_itself_instead_of_showing_the_form(self):
        self.invitation.expires_at = timezone.now() - datetime.timedelta(hours=1)
        self.invitation.save(update_fields=["expires_at"])
        resp = self.client.get("/accept-invite/?token=tok-valid")
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "expired", status_code=400)

    def test_unknown_token_is_rejected(self):
        self.assertEqual(self.client.get("/accept-invite/?token=nope").status_code, 404)

    def test_setting_a_password_creates_the_account_and_signs_in(self):
        resp = self.client.post("/accept-invite/", {
            "token": "tok-valid",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
        })
        self.assertRedirects(resp, "/", fetch_redirect_response=False)

        user = get_user_model().objects.get(email="invitee@company.com")
        self.assertEqual(user.username, "invitee@company.com")   # username IS the email
        self.assertTrue(user.check_password("SecurePassword123!"))
        self.assertEqual(user.profile.role, "Analyst")
        self.assertTrue(UserInvitation.objects.get(pk=self.invitation.pk).is_accepted)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_mismatched_confirmation_creates_nothing(self):
        resp = self.client.post("/accept-invite/", {
            "token": "tok-valid", "password": "SecurePassword123!", "password_confirm": "Different123!",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "do not match", status_code=400)
        self.assertFalse(get_user_model().objects.filter(email="invitee@company.com").exists())

    def test_weak_password_is_rejected_by_djangos_validators(self):
        resp = self.client.post("/accept-invite/", {
            "token": "tok-valid", "password": "password", "password_confirm": "password",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(get_user_model().objects.filter(email="invitee@company.com").exists())

    def test_a_used_token_cannot_be_replayed(self):
        self.client.post("/accept-invite/", {
            "token": "tok-valid", "password": "SecurePassword123!", "password_confirm": "SecurePassword123!",
        })
        resp = self.client.get("/accept-invite/?token=tok-valid")
        self.assertContains(resp, "already been accepted", status_code=400)


class PasswordResetTests(TestCase):
    def test_login_page_offers_a_reset_link(self):
        self.assertContains(self.client.get("/login/"), "/password-reset/")

    def test_reset_form_is_reachable_logged_out_and_mails_a_link_for_this_host(self):
        get_user_model().objects.create_user("someone", email="someone@company.com", password="x")
        self.assertEqual(self.client.get("/password-reset/").status_code, 200)

        with override_settings(ALLOWED_HOSTS=["limitless.example.com", "testserver"]):
            resp = self.client.post("/password-reset/", {"email": "someone@company.com"},
                                    HTTP_HOST="limitless.example.com")
        self.assertRedirects(resp, "/password-reset/sent/", fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("http://limitless.example.com/reset/", mail.outbox[0].body)

    def test_unknown_address_does_not_reveal_itself(self):
        resp = self.client.post("/password-reset/", {"email": "ghost@company.com"})
        self.assertRedirects(resp, "/password-reset/sent/", fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)


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
