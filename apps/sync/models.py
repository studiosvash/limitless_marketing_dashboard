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
    # A run stopped by the user from the sync banner. Deliberately NOT `error`:
    # Settings -> Connections renders errors as live problems needing attention, and
    # scheduling.FAILED_RUN_BACKOFF holds a module off for 6 hours after a failed run --
    # so filing a cancel under `error` would block the restart the user cancelled in
    # order to make. It is also excluded from every cadence anchor, because a run that
    # was stopped did not refresh anything.
    CANCELLED = "cancelled", "Cancelled"


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
    # WHICH PROJECT asked for this run — `sites.id` in the analytics DB.
    #
    # `site_url` alone cannot answer that. Position Tracking's wizard registers the same domain
    # as several independent projects (`add_site(allow_duplicate=True)`), so "Premierstaff NY"
    # and "Premierstaff Las Vegas" are distinct `sites` rows that share one `site_url` — and
    # `site_service.get_site(site_url)` returns whichever one it finds FIRST. A connector
    # resolving its tracking location that way read an arbitrary sibling's city, which is part
    # of why every city project produced identical numbers.
    #
    # Nullable, and every consumer falls back to the by-URL lookup: rows created before this
    # field existed have no pk, and the scheduled sync legitimately runs per domain rather than
    # per project. NULL means "no specific project", never "project 0".
    site_pk = models.IntegerField(null=True, blank=True, db_index=True)
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
    # OS process id of the `manage.py run_sync` worker executing this run.
    #
    # Syncs used to run in a daemon thread INSIDE the gunicorn web worker, where any worker
    # recycle killed them silently and left the row at status='running' forever -- for two
    # hours, until the reaper's RUN_TIMEOUT elapsed. The SPA polled that row the whole time
    # and showed a frozen progress bar, which is what "the sync just stops" looked like.
    #
    # Now that a run is its own process, the pid turns "did this die?" from a guess based on
    # elapsed time into a fact: reap_orphaned_runs() can ask the OS. Nullable because rows
    # created before this field existed have no pid, and because the pid is written a moment
    # after the row (Popen needs the run id to exist first) -- so a NULL pid means "unknown",
    # never "dead", and those rows still fall back to the timeout.
    pid = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            # start_sync_run's "already running" SELECT is check-then-create with several
            # queries (reap, budget, freshness) between the check and the INSERT, so two
            # simultaneous POSTs could both pass it and each spawn a full metered sync.
            # This partial unique index is the authoritative guard: the second INSERT
            # raises IntegrityError, which start_sync_run catches and turns into an
            # attach-to-existing response. Works on both SQLite and Postgres.
            models.UniqueConstraint(
                fields=["site_url"],
                condition=models.Q(status="running"),
                name="one_running_refresh_per_site",
            ),
        ]

    def __str__(self) -> str:
        return f"RefreshRun#{self.pk} {self.scope}@{self.site_url}: {self.status}"

    @property
    def percent(self) -> int:
        """Completion percent for the progress bar; 0 when total is unknown."""
        if not self.total_count:
            return 0
        return int(100 * self.completed_count / self.total_count)
