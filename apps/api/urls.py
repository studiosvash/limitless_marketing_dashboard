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
]
