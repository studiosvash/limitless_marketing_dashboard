from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("ping", views.PingView.as_view(), name="ping"),
    path("projects", views.ProjectListCreateView.as_view(), name="projects"),
    path("projects/<slug:slug>/overview", views.ProjectOverviewView.as_view(), name="project-overview"),
    path("projects/<slug:slug>/alerts", views.ProjectAlertsView.as_view(), name="project-alerts"),
    path("projects/<slug:slug>/keywords", views.ProjectKeywordsView.as_view(), name="project-keywords"),
    path("projects/<slug:slug>/positions", views.ProjectPositioningView.as_view(), name="project-positions"),
    path("projects/<slug:slug>/backlinks", views.ProjectBacklinksView.as_view(), name="project-backlinks"),
    path("research", views.KeywordResearchView.as_view(), name="keyword-research"),
]
