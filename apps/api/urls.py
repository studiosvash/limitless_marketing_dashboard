from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("ping", views.PingView.as_view(), name="ping"),
    path("projects", views.ProjectListCreateView.as_view(), name="projects"),
    path("projects/<slug:slug>", views.ProjectDetailView.as_view(), name="project-detail"),
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
    path("projects/<slug:slug>/team", views.ProjectTeamView.as_view(), name="project-team"),
    path("projects/<slug:slug>/team/<int:user_id>", views.ProjectTeamView.as_view(), name="project-team-detail"),
    path("projects/<slug:slug>/invite", views.ProjectInviteView.as_view(), name="project-invite"),
    path("projects/<slug:slug>/invite/<int:invite_id>", views.ProjectInviteView.as_view(), name="project-invite-detail"),
    path("projects/<slug:slug>/invite/<int:invite_id>/resend", views.ProjectInviteResendView.as_view(), name="project-invite-resend"),
    path("auth/invite-status", views.AuthInviteStatusView.as_view(), name="auth-invite-status"),
    path("auth/accept-invite", views.AuthInviteAcceptView.as_view(), name="auth-accept-invite"),
    path("auth/password", views.ChangePasswordView.as_view(), name="auth-password"),
    path("projects/<slug:slug>/data", views.ProjectDataCleanView.as_view(), name="project-data-clean"),
    # Mutations (HANDOFF_SPEC 1)
    path("projects/<slug:slug>/audit/toggle-check", views.AuditToggleCheckView.as_view(), name="audit-toggle-check"),
    path("projects/<slug:slug>/ads/status", views.AdsStatusView.as_view(), name="ads-status"),
    path("projects/<slug:slug>/ads/budget", views.AdsBudgetView.as_view(), name="ads-budget"),
    path("projects/<slug:slug>/ads/negatives", views.AdsNegativesView.as_view(), name="ads-negatives"),
    path("projects/<slug:slug>/ads/promote", views.AdsPromoteView.as_view(), name="ads-promote"),
    # Batch route first: "alerts/ack" and "alerts/<alert_id>/ack" have different segment
    # counts so they cannot collide, but the specific-before-generic order documents intent.
    path("alerts/ack", views.AlertBatchAckView.as_view(), name="alert-ack-batch"),
    path("alerts/<str:alert_id>/ack", views.AlertAckView.as_view(), name="alert-ack"),
    path("alerts/<str:alert_id>/unack", views.AlertUnackView.as_view(), name="alert-unack"),
    # Refresh / Sync
    # `sync/active` before `sync` is not strictly required (different segment counts), but it
    # documents the specific-before-generic intent, matching the alerts/ack pair above.
    path("projects/<slug:slug>/sync/cancel", views.ProjectSyncCancelView.as_view(), name="project-sync-cancel"),
    path("projects/<slug:slug>/sync/active", views.ProjectSyncActiveView.as_view(), name="project-sync-active"),
    path("projects/<slug:slug>/sync", views.ProjectSyncView.as_view(), name="project-sync"),
    path("tasks/<int:task_id>", views.TaskStatusView.as_view(), name="task-status"),
    # Keyword / Prompt Explorer (project id in body)
    path("research", views.KeywordResearchView.as_view(), name="keyword-research"),
    path("prompt-research", views.PromptResearchView.as_view(), name="prompt-research"),
    path("domain-overview", views.DomainOverviewView.as_view(), name="domain-overview"),
    path("live-serp", views.LiveSERPView.as_view(), name="live-serp"),
    # Connection check — the FOURTH sanctioned live-API endpoint (with research,
    # domain-overview and live-serp). Allowed to call out because a human pressed a button;
    # see CLAUDE.md and .claude/api-reference.md.
    path("connection-check", views.ConnectionCheckView.as_view(), name="connection-check"),
]
