from django.contrib import admin

from apps.sync.models import SyncLog, RefreshRun


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("connector", "site_url", "status", "last_synced", "records_written")
    list_filter = ("status", "connector")
    search_fields = ("connector", "site_url")


@admin.register(RefreshRun)
class RefreshRunAdmin(admin.ModelAdmin):
    list_display = ("id", "scope", "site_url", "status", "completed_count", "total_count", "started_at")
    list_filter = ("status", "scope")
