"""
Dashboard app models (Django ORM, django_internal.db).

Insight is team-entered qualitative context — app state, not analytics — so it
lives in Django's DB with a user FK and is editable via Django admin/forms.
"""
from django.conf import settings
from django.db import models


class Insight(models.Model):
    """Team-entered context linking business events to metrics."""

    TEAM_CHOICES = [
        ("seo", "SEO"),
        ("ads", "Ads"),
        ("product", "Product"),
        ("marketing", "Marketing"),
    ]
    IMPACT_CHOICES = [
        ("positive", "Positive"),
        ("negative", "Negative"),
        ("neutral", "Neutral"),
    ]

    site_url = models.CharField(max_length=255, db_index=True)
    date = models.DateField(db_index=True)
    team = models.CharField(max_length=50, choices=TEAM_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    affected_metric = models.CharField(max_length=100, null=True, blank=True)
    dimension = models.CharField(max_length=200, null=True, blank=True)
    impact = models.CharField(max_length=50, choices=IMPACT_CHOICES, default="neutral")
    hypothesis = models.TextField(null=True, blank=True)
    action_taken = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Insights"

    def __str__(self) -> str:
        return f"[{self.team}] {self.title} ({self.date})"
