"""User roles for FuseHealth.

We keep Django's built-in User for auth and attach a one-to-one UserProfile that
holds the role. This avoids a custom-user migration while giving us role-based
access. A profile is created automatically for every user via a signal (below).
"""

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Role(models.TextChoices):
    FOUNDER = "founder", "Founder"   # full access to every page
    SEO = "seo", "SEO"               # SEO, Keywords, Pages, Backlinks, Positioning, Insights
    ADS = "ads", "Ads"               # Ads Performance only


# Which page keys each role may open. Pages not listed are blocked for that role.
# `founder` is handled as "all" in the access check, so it is intentionally omitted.
# Phase 5.5: 7 pages built (overview, seo, keywords, pages, positioning, alerts, settings).
ROLE_PAGE_ACCESS: dict[str, set[str]] = {
    Role.SEO: {"overview", "seo", "keywords", "pages", "positioning", "alerts", "settings", "backlinks"},
    Role.ADS: {"overview", "alerts", "settings", "ads"},
}


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.FOUNDER)

    def __str__(self) -> str:
        return f"{self.user.get_username()} ({self.get_role_display()})"

    def can_access(self, page_key: str) -> bool:
        """True if this user's role may open the given page."""
        if self.role == Role.FOUNDER:
            return True
        return page_key in ROLE_PAGE_ACCESS.get(self.role, set())


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    """Every user gets a profile. New users default to the most restrictive sensible role
    only if explicitly set later; default here is FOUNDER for the initial internal team and
    is overridden by seed_users / admin as needed."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
