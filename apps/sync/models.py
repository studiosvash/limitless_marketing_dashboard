"""
Operational sync state (Django ORM, django_internal.db).

These tables are app state, not analytics — they live in Django's default DB so
views and the HTMX progress bar can read them directly. The sync engine
(apps.sync, built in Phase 4) writes them; connectors do not.
"""
from django.conf import settings
from django.db import models


class SyncStatus(models.TextChoices):
    NEVER = "never", "Never synced"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    ERROR = "error", "Error"


class RefreshStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    ERROR = "error", "Error"


class SyncLog(models.Model):
    """Last known result of one connector for one site. One row per (connector, site_url)."""

    connector = models.CharField(max_length=100, db_index=True)
    site_url = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, choices=SyncStatus.choices, default=SyncStatus.NEVER)
    last_synced = models.DateTimeField(null=True, blank=True)
    records_written = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connector", "site_url"], name="uq_synclog_connector_site"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.connector}@{self.site_url}: {self.status}"


class RefreshRun(models.Model):
    """One user-triggered refresh run. The HTMX progress bar polls this row."""

    site_url = models.CharField(max_length=255, db_index=True)
    scope = models.CharField(max_length=50, default="all")  # 'all' or a page key (e.g. 'seo', 'keywords') from the page registry
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=20, choices=RefreshStatus.choices, default=RefreshStatus.RUNNING, db_index=True)
    current_connector = models.CharField(max_length=100, null=True, blank=True)
    completed_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    records_written = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"RefreshRun#{self.pk} {self.scope}@{self.site_url}: {self.status}"

    @property
    def percent(self) -> int:
        """Completion percent for the progress bar; 0 when total is unknown."""
        if not self.total_count:
            return 0
        return int(100 * self.completed_count / self.total_count)
