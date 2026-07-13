"""
Dashboard app models (Django ORM, django_internal.db).

Insight is team-entered qualitative context — app state, not analytics — so it
lives in Django's DB with a user FK and is editable via Django admin/forms.
"""
from django.conf import settings
from django.db import models


def _empty_list():
    """Callable default for JSONField list defaults. Used instead of the bare
    builtin `list` because AIPrompt has a field literally named `list` (the FK to
    AIPromptList) -- inside that class body, `list = models.ForeignKey(...)` shadows
    the builtin `list` name for every subsequent line, so `default=list` on a later
    field would silently bind to the ForeignKey descriptor instance, not the builtin
    type (confirmed via Django's own fields.E010 system-check warning). This helper
    sidesteps the shadowing entirely, and is used on every list-default JSONField
    here for consistency."""
    return []


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


class AITarget(models.Model):
    """AI Optimization tracked brand/competitors — one row per project. First-party app
    state (which brand/competitors/aliases to watch for in AI-answer-engine mentions), not
    analytics data -- same site_url-string-keyed pattern as Insight."""

    site_url = models.CharField(max_length=255, unique=True, db_index=True)
    brand = models.CharField(max_length=255, blank=True, default="")
    aliases = models.JSONField(default=_empty_list)
    competitors = models.JSONField(default=_empty_list)
    setup_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"AITarget({self.site_url}, brand={self.brand!r})"


class AIPromptList(models.Model):
    """User-defined grouping of AIPrompt rows (e.g. "Branded", "Competitor")."""

    site_url = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"AIPromptList({self.site_url}, {self.name!r})"


class AIPrompt(models.Model):
    """A tracked prompt to (eventually) check against external AI answer engines.
    tracked_models is a persisted preference of which LLMs this prompt WOULD check once
    'run' exists -- never a live/fabricated check result."""

    site_url = models.CharField(max_length=255, db_index=True)
    list = models.ForeignKey(
        AIPromptList, null=True, blank=True, on_delete=models.SET_NULL, related_name="prompts"
    )
    text = models.TextField()
    tracked_models = models.JSONField(default=_empty_list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AIPrompt({self.site_url}, {self.text[:40]!r})"
