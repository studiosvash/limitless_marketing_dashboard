from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("ping", views.PingView.as_view(), name="ping"),
    path("projects", views.ProjectListCreateView.as_view(), name="projects"),
    path("projects/<slug:slug>/overview", views.ProjectOverviewView.as_view(), name="project-overview"),
    path("projects/<slug:slug>/seo", views.ProjectSEOView.as_view(), name="project-seo"),
    path("projects/<slug:slug>/keywords", views.ProjectKeywordsView.as_view(), name="project-keywords"),
    path("projects/<slug:slug>/positions", views.ProjectPositionsView.as_view(), name="project-positions"),
    path("projects/<slug:slug>/alerts", views.ProjectAlertsView.as_view(), name="project-alerts"),
    path("projects/<slug:slug>/backlinks", views.ProjectBacklinksView.as_view(), name="project-backlinks"),
    path("projects/<slug:slug>/audit", views.ProjectSiteAuditView.as_view(), name="project-audit"),
    path("projects/<slug:slug>/offsite", views.ProjectOffsiteView.as_view(), name="project-offsite"),
    path("projects/<slug:slug>/ads", views.ProjectAdsView.as_view(), name="project-ads"),
    path("projects/<slug:slug>/ai", views.ProjectAIView.as_view(), name="project-ai"),
    path("projects/<slug:slug>/ai/<str:action>", views.ProjectAIActionView.as_view(), name="project-ai-action"),
    path("projects/<slug:slug>/settings", views.ProjectSettingsView.as_view(), name="project-settings"),
]
