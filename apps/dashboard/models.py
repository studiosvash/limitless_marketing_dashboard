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


def _empty_dict():
    """Callable default for JSONField dict defaults (Phase E, ProjectSettings.data).
    Named/defined separately from `_empty_list` above (rather than reusing a generic
    helper) for the same reason `_empty_list` exists in the first place: AIPrompt above
    has a field literally named `list`, which shadows the builtin `list` for every
    subsequent line in that class body. `ProjectSettings` below has no field named `dict`,
    but this helper is still defined as an explicit callable -- never `default=dict` or
    `default={}` -- to match this file's established convention and avoid the same class of
    bug if a future field here is ever named `dict`."""
    return {}


class ProjectSettings(models.Model):
    """Blob store for Settings groups with no dedicated relational need (workspace,
    notifications, aiConfig, dataPrefs, syncConfig, platformConnectors, budget.cap/.enforce,
    alertRules, crawl) -- see design spec for why these are a single JSONField rather than
    one model each. Genuine persistence (saves survive reload); several groups are honestly
    disclosed as not yet wired to any downstream system."""

    site_url = models.CharField(max_length=255, unique=True, db_index=True)
    data = models.JSONField(default=_empty_dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"ProjectSettings({self.site_url})"


class Notification(models.Model):
    """The topbar bell's feed — system events, not analytics alerts.

    Deliberately separate from Anomaly/TechnicalIssue (see alerts_service.py / the Alerts
    page): those are per-project data-quality findings the user acts on from the Alerts
    workspace. This table is short operational pings — connection failures, budget/balance
    crossings, a refresh finishing, a teammate joining — that belong in the bell, not mixed
    into the Alerts feed the sidebar badge counts. `site_url` is blank for account-wide
    events (DataForSEO budget/balance are one shared account, not per-project)."""

    KIND_CHOICES = [
        ("connection_fail", "Connection failure"),
        ("sync_success", "Sync succeeded"),
        ("sync_error", "Sync failed"),
        ("budget", "Budget"),
        ("balance", "DataForSEO balance"),
        ("user_added", "Team member added"),
    ]
    SEVERITY_CHOICES = [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]

    site_url = models.CharField(max_length=255, blank=True, default="", db_index=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="info")
    title = models.CharField(max_length=255)
    detail = models.TextField(blank=True, default="")
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification({self.kind}, {self.title[:40]!r})"


class BudgetState(models.Model):
    """Singleton row (pk=1) holding the DataForSEO account's last-known balance and the
    monthly-budget notification state. Not per-project: DataForSEO bills one shared
    account, so 'available balance' and the $/month cap are account-wide facts, and this
    table exists only so a low-balance warning fires once instead of on every sync."""

    dataforseo_balance = models.FloatField(null=True, blank=True)
    balance_checked_at = models.DateTimeField(null=True, blank=True)
    low_balance_notified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"BudgetState(balance={self.dataforseo_balance})"
