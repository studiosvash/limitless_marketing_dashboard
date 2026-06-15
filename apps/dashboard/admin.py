from django.contrib import admin

from apps.dashboard.models import Insight


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "impact", "site_url", "date", "is_verified")
    list_filter = ("team", "impact", "is_verified")
    search_fields = ("title", "description", "dimension")
