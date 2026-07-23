from datetime import timedelta
import tempfile
from pathlib import Path
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from sqlalchemy import create_engine

from apps.accounts.models import Role, UserInvitation, UserProfile
from pipeline.db.schema import Site, init_db
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_session


class InvitationSystemTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(create_engine(f"sqlite:///{db_path}"))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url="sc-domain:fusehealth.com", site_name="FuseHealth", slug="fusehealth", is_active=1))

        # Create Owner user (id=1 / founder)
        self.owner = User.objects.create_user(username="founder", email="owner@fusehealth.com", password="x")
        self.owner_profile, _ = UserProfile.objects.get_or_create(user=self.owner)
        self.owner_profile.role = Role.FOUNDER
        self.owner_profile.save()

        # Create Analyst user
        self.analyst = User.objects.create_user(username="analyst1", email="analyst@fusehealth.com", password="x")
        self.analyst_profile, _ = UserProfile.objects.get_or_create(user=self.analyst)
        self.analyst_profile.role = Role.SEO
        self.analyst_profile.save()

        self.client = APIClient()

    def test_only_owner_can_invite_users(self):
        self.client.force_authenticate(user=self.analyst)
        resp = self.client.post("/api/projects/fusehealth/invite", {"email": "newbie@company.com", "role": "Analyst"})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(UserInvitation.objects.count(), 0)

        self.client.force_authenticate(user=self.owner)
        resp = self.client.post("/api/projects/fusehealth/invite", {"email": "newbie@company.com", "role": "Analyst"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data.get("ok"))
        self.assertEqual(UserInvitation.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/#/accept-invite?token=", mail.outbox[0].body)

    def test_invite_resend_and_revoke(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post("/api/projects/fusehealth/invite", {"email": "test@company.com", "role": "Admin"})
        inv_id = resp.data["id"]

        # Resend
        resp_resend = self.client.post(f"/api/projects/fusehealth/invite/{inv_id}/resend")
        self.assertEqual(resp_resend.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

        # Delete / Revoke
        resp_del = self.client.delete(f"/api/projects/fusehealth/invite/{inv_id}")
        self.assertEqual(resp_del.status_code, 200)
        self.assertEqual(UserInvitation.objects.count(), 0)

    def test_auth_invite_status_and_accept(self):
        self.client.force_authenticate(user=self.owner)
        self.client.post("/api/projects/fusehealth/invite", {"email": "invited@company.com", "role": "Admin"})
        inv = UserInvitation.objects.get(email="invited@company.com")

        # Check status
        self.client.logout()
        status_resp = self.client.get(f"/api/auth/invite-status?token={inv.token}")
        self.assertEqual(status_resp.status_code, 200)
        self.assertTrue(status_resp.data["valid"])
        self.assertEqual(status_resp.data["email"], "invited@company.com")
        self.assertEqual(status_resp.data["role"], "Admin")

        # Accept invitation
        accept_resp = self.client.post("/api/auth/accept-invite", {
            "token": inv.token,
            "username": "newadmin",
            "password": "SecurePassword123!"
        })
        self.assertEqual(accept_resp.status_code, 200)
        self.assertTrue(accept_resp.data["ok"])

        inv.refresh_from_db()
        self.assertTrue(inv.is_accepted)

        new_user = User.objects.get(username="newadmin")
        self.assertTrue(new_user.is_active)
        self.assertTrue(new_user.check_password("SecurePassword123!"))
        self.assertEqual(new_user.profile.role, "Admin")

        # Second accept attempt should fail
        accept_resp_2 = self.client.post("/api/auth/accept-invite", {
            "token": inv.token,
            "username": "anothername",
            "password": "SecurePassword123!"
        })
        self.assertEqual(accept_resp_2.status_code, 400)
        self.assertIn("already been accepted", accept_resp_2.data["detail"])
