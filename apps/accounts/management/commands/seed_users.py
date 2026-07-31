"""Create the internal team's user accounts with their roles.

Idempotent: re-running updates roles/passwords without creating duplicates.
Passwords are read from the environment so they are never hardcoded:
    FUSEHEALTH_FOUNDER_PASSWORD, FUSEHEALTH_SEO_PASSWORD, FUSEHEALTH_ADS_PASSWORD
If a password env var is missing, a clearly-temporary default is set and the command
warns you to change it (via `manage.py changepassword` or the admin).

Run:  python manage.py seed_users
"""

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.accounts.models import UserProfile

# (username, role, is_superuser, env var for password)
#
# Roles are the LIVE vocabulary — Owner / Admin / Analyst — not apps.accounts.models.Role
# (founder/seo/ads), which is the retired system nothing enforces any more
# (.claude/skills.md §7). Seeding the retired values wrote strings no live check understands:
# `check_owner_admin` only blocks the exact string "Analyst", so a user stored as "seo" or
# "ads" silently had full Admin access anyway, while the Settings team table printed the raw
# value and showed a role the UI has no concept of.
#
# `seo` and `ads` map to **Admin**, not Analyst, deliberately: that is the access they already
# have today, and this change is meant to make the stored label honest, not to quietly revoke
# anyone's permissions. Demoting either account to Analyst is a real product decision — do it
# from Settings → Team, where it is visible and reversible.
USERS = [
    ("founder", "Owner", True, "FUSEHEALTH_FOUNDER_PASSWORD"),
    ("seo", "Admin", False, "FUSEHEALTH_SEO_PASSWORD"),
    ("ads", "Admin", False, "FUSEHEALTH_ADS_PASSWORD"),
]


class Command(BaseCommand):
    help = "Create/update the internal team users (founder, seo, ads) with roles."

    def handle(self, *args, **options):
        for username, role, is_super, env_key in USERS:
            password = os.environ.get(env_key)
            temporary = password is None
            if temporary:
                password = f"changeme-{username}"

            user, created = User.objects.get_or_create(username=username)
            user.is_staff = is_super
            user.is_superuser = is_super
            user.set_password(password)
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            status = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(f"  {username:<8} role={role:<8} ({status})")
            )
            if temporary:
                self.stdout.write(
                    self.style.WARNING(
                        f"    ! no {env_key} set — temporary password 'changeme-{username}'. "
                        f"Change it: python manage.py changepassword {username}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Done. 3 users ready."))
