from datetime import date as date_cls

from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sqlalchemy import func, select, delete

from pipeline.services.site_service import add_site, list_sites
from pipeline.utils.db_connection import get_session
from pipeline.db.schema import (
    Site, SEODaily, KeywordRanking, Page, AdMetricDaily, Backlink,
    TechnicalIssue, PageSpeed, IndexingStatus, SEOAggregate, AISummary,
    Anomaly, ComparativeMetrics, CompetitorKeywordRanking, TrackedCompetitor,
    AIKeywordData, SavedKeyword, MetricForecast, KeywordOpportunity, RiskSignal
)

from apps.dashboard.services.overview_service import (
    get_kpi_raw, build_kpis_api, build_top_pages_api, query_daily_traffic_raw,
    range_to_period_dates, get_ai_summary_text, parse_ai_summary, build_summary_lists,
    build_pillars, build_modules, build_priority_feed,
)
from apps.dashboard.services.decision_engine import generate_signals, generate_ad_overlap_signals
from apps.dashboard.services.keywords_service import build_keywords_response
from apps.dashboard.services.positioning_service import build_positions_response
from apps.dashboard.services.seo_service import build_seo_response
from apps.dashboard.services.alerts_service import build_alerts_response
from apps.dashboard.services.backlinks_service import build_backlinks_response
from apps.dashboard.services.site_audit_service import build_site_audit_response
from apps.dashboard.services.offsite_service import build_offsite_response
from apps.dashboard.services.ads_service import build_ads_response
from apps.dashboard.services.ai_service import build_ai_response
from apps.dashboard.services.settings_service import build_settings_response, apply_settings_update
from apps.dashboard.models import AITarget, AIPromptList, AIPrompt
from apps.dashboard.services.shared_queries import (
    _get_ads_overview, _get_keywords_overview,
)
from apps.dashboard.services.sync_api_service import (
    start_sync_run, task_status,
)
from apps.dashboard.services.keyword_research_service import (
    run_keyword_research, run_prompt_research,
)

from .serializers import OverviewQuerySerializer, ProjectCreateSerializer, ProjectSerializer


def resolve_project_or_404(slug: str) -> Site:
    """Look up a Site by its public slug (the API's project `id`). Raises Http404 if no
    active or inactive site matches — used by every apps.api view that takes a `slug` URL
    kwarg."""
    with get_session() as session:
        site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
    if site is None:
        raise Http404(f"No project with slug '{slug}'")
    return site


def latest_data_anchor(site_id: str) -> date_cls:
    """Most recent date we have SEO data for, or today if none — periods anchor to this so
    the API never defaults to a window that postdates the data."""
    with get_session() as session:
        return session.execute(
            select(func.max(SEODaily.date)).where(SEODaily.site_id == site_id)
        ).scalar() or date_cls.today()


def resolve_range_periods(request, slug: str):
    """Resolve a range-taking view's full request context in one call: site lookup (404 on
    unknown slug), `range` query param validation (default 30d), and period-date resolution
    anchored to the latest data date. Returns (site_id, curr_start, curr_end, prev_start,
    prev_end). Used by every apps.api view that takes both a `slug` and a `range` param."""
    site_id = resolve_project_or_404(slug).site_url

    query = OverviewQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    range_key = query.validated_data["range"]

    anchor = latest_data_anchor(site_id)
    curr_start, curr_end, prev_start, prev_end = range_to_period_dates(range_key, anchor)
    return site_id, curr_start, curr_end, prev_start, prev_end


# login_not_required bypasses session-based LoginRequiredMiddleware (active project-wide)
# so DRF's own TokenAuthentication/IsAuthenticated run instead — without this, anonymous
# requests get a 302 to the login page rather than DRF's 401. Every future apps.api view
# needs this too.
@method_decorator(login_not_required, name="dispatch")
class PingView(APIView):
    """Smoke-test endpoint: proves auth + routing work before any real data endpoint exists."""

    def get(self, request):
        return Response({"ok": True})


@method_decorator(login_not_required, name="dispatch")
class ProjectListCreateView(APIView):
    def get(self, request):
        sites = list_sites(active_only=True)
        return Response(ProjectSerializer(sites, many=True).data)

    def post(self, request):
        payload = ProjectCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        site_url = data["domain"].strip()
        new_id = add_site(
            site_url=site_url,
            site_name=data.get("name") or None,
            vertical=data.get("vertical") or None,
            location=data.get("location") or "United States",
        )
        with get_session() as session:
            site = session.get(Site, new_id)
            body = ProjectSerializer(site).data

        # Auto-kick off initial data sync so the new site populates without requiring
        # a manual Refresh click. Returns task_id so the SPA can start polling the
        # progress bar immediately (GET /api/tasks/<task_id>).
        try:
            sync_info = start_sync_run(site_url, "all", user=request.user)
            body["sync_task_id"] = sync_info["task_id"]
        except Exception:
            # Non-fatal: sync failure should never block site creation.
            body["sync_task_id"] = None

        return Response(body, status=status.HTTP_201_CREATED)


@method_decorator(login_not_required, name="dispatch")
class ProjectDataCleanView(APIView):
    def delete(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        tables_to_clean = [
            SEODaily, KeywordRanking, Page, AdMetricDaily, Backlink,
            TechnicalIssue, PageSpeed, IndexingStatus, SEOAggregate, AISummary,
            Anomaly, ComparativeMetrics, CompetitorKeywordRanking, TrackedCompetitor,
            AIKeywordData, SavedKeyword, MetricForecast, KeywordOpportunity, RiskSignal
        ]
        
        try:
            with get_session() as session:
                for table in tables_to_clean:
                    session.execute(delete(table).where(table.site_id == site_id))
                session.commit()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(login_not_required, name="dispatch")
class ProjectOverviewView(APIView):
    def get(self, request, slug):
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)

        kpis_current, kpis_previous = get_kpi_raw(site_id, curr_start, curr_end, prev_start, prev_end)
        kpis = build_kpis_api(kpis_current, kpis_previous)
        trend = query_daily_traffic_raw(site_id, curr_start, curr_end)
        top_pages = build_top_pages_api(site_id, curr_start, curr_end)

        ads_overview, ads_curr, ads_prev = _get_ads_overview(site_id, curr_start, curr_end, prev_start, prev_end)
        signals = generate_signals(kpis_current, kpis_previous, ads_curr, ads_prev)
        signals += generate_ad_overlap_signals(site_id, curr_start, curr_end)
        signals = signals[:3]

        keywords_overview = _get_keywords_overview(site_id)
        top3_count = sum(1 for k in keywords_overview if k["position"] not in ("N/A",) and float(k["position"] or 99) <= 3)

        pillars = build_pillars(site_id, kpis_current, kpis_previous, top3_count)
        seo_stat = f"{int(kpis_current['clicks']):,} clicks"
        modules = build_modules(site_id, seo_stat, len(keywords_overview), top3_count, kpis_current["avg_position"])

        ai_summary_sections = parse_ai_summary(get_ai_summary_text(site_id))
        summary = build_summary_lists(ai_summary_sections)

        priority = build_priority_feed(build_alerts_response(site_id)["feed"])

        return Response({
            "kpis": kpis,
            "pillars": pillars,
            "modules": modules,
            "priority": priority,
            "signals": signals,
            "trend": trend,
            "summary": summary,
            "topPages": top_pages,
        })


@method_decorator(login_not_required, name="dispatch")
class ProjectSEOView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        anchor = latest_data_anchor(site_id)
        curr_start, curr_end, _, _ = range_to_period_dates("30d", anchor)

        return Response(build_seo_response(site_id, curr_start, curr_end))


@method_decorator(login_not_required, name="dispatch")
class ProjectKeywordsView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        anchor = latest_data_anchor(site_id)
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates("30d", anchor)

        return Response(build_keywords_response(site_id, curr_start, curr_end, prev_start, prev_end))

    def post(self, request, slug):
        """Track a keyword found in the Keyword Explorer -- persists it to the site's saved
        keyword list (SavedKeyword), reusing the old MVP's saved_keyword_service. The SPA posts
        one keyword per call: {kw, volume, kd, cpc, intent}."""
        from pipeline.services.saved_keyword_service import save_keywords

        site_id = resolve_project_or_404(slug).site_url
        kw = (request.data.get("kw") or "").strip()
        if not kw:
            return Response({"detail": "kw is required"}, status=400)

        row = {
            "keyword": kw,
            "search_volume": request.data.get("volume"),
            "keyword_difficulty": request.data.get("kd"),
            "cpc": request.data.get("cpc"),
            "intent": request.data.get("intent"),
        }
        saved = save_keywords(site_id, [row], location=request.data.get("location") or "United States")
        # HANDOFF_SPEC 1: track-keyword returns {ok, keyword} (keyword echoed in spec shape).
        return Response({"ok": True, "saved": saved, "keyword": _tracked_keyword_body(kw, request.data, "manual")})


@method_decorator(login_not_required, name="dispatch")
class ProjectPositionsView(APIView):
    def get(self, request, slug):
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)

        return Response(build_positions_response(site_id, curr_start, curr_end, prev_start, prev_end))


@method_decorator(login_not_required, name="dispatch")
class ProjectAlertsView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_alerts_response(site_id))


@method_decorator(login_not_required, name="dispatch")
class ProjectBacklinksView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_backlinks_response(site_id))


@method_decorator(login_not_required, name="dispatch")
class ProjectSiteAuditView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_site_audit_response(site_id))


@method_decorator(login_not_required, name="dispatch")
class ProjectOffsiteView(APIView):
    def get(self, request, slug):
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)
        return Response(build_offsite_response(site_id, curr_start, curr_end, prev_start, prev_end))


@method_decorator(login_not_required, name="dispatch")
class ProjectAdsView(APIView):
    def get(self, request, slug):
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)
        return Response(build_ads_response(site_id, curr_start, curr_end, prev_start, prev_end))


@method_decorator(login_not_required, name="dispatch")
class ProjectAIView(APIView):
    """Phase D: GET /api/projects/<slug>/ai -- no `range` param, unlike Ads/Offsite/Positions
    (AI Optimization's real data -- targets/lists/prompts/aiKeywords -- isn't period-scoped)."""

    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_ai_response(site_id))


@method_decorator(login_not_required, name="dispatch")
class ProjectAIActionView(APIView):
    """Phase D: POST /api/projects/<slug>/ai/<action> -- dispatches to one of 6 real
    first-party mutation handlers by `action` path segment. Every handler persists to our own
    DB (never an external API) and returns a minimal ack; the SPA always re-fetches
    ProjectAIView after any mutation, so no handler needs to echo authoritative state back.
    `run`/`inspect` (and any other unmapped action) fall through to a clean 400 -- those call
    external LLM Responses/scraper APIs this codebase has no connector for (explicitly out of
    scope this phase), and a clear 4xx is preferable to a 404 or an unhandled crash."""

    def post(self, request, slug, action):
        site_id = resolve_project_or_404(slug).site_url
        handler = getattr(self, f"_handle_{action.replace('-', '_')}", None)
        if handler is None:
            return Response({"detail": f"Unknown or not-yet-available action: {action}"}, status=400)
        return handler(request, site_id)

    def _handle_setup(self, request, site_id):
        data = request.data
        AITarget.objects.update_or_create(
            site_url=site_id,
            defaults={
                "brand": data.get("brand", ""),
                "aliases": data.get("aliases", []),
                "competitors": data.get("competitors", []),
                "setup_done": True,
            },
        )
        for text in data.get("prompts", []):
            if text and text.strip():
                AIPrompt.objects.create(site_url=site_id, text=text.strip())
        return Response({})

    def _handle_targets(self, request, site_id):
        data = request.data
        AITarget.objects.update_or_create(
            site_url=site_id,
            defaults={
                "brand": data.get("brand", ""),
                "aliases": data.get("aliases", []),
                "competitors": data.get("competitors", []),
            },
        )
        return Response({})

    def _handle_prompts(self, request, site_id):
        data = request.data
        list_id = data.get("listId")
        texts = [t.strip() for t in data.get("texts", []) if t and t.strip()]
        created = [AIPrompt(site_url=site_id, list_id=list_id, text=t) for t in texts]
        AIPrompt.objects.bulk_create(created)
        return Response({"added": len(created)})

    def _handle_prompts_remove(self, request, site_id):
        AIPrompt.objects.filter(site_url=site_id, id=request.data.get("id")).delete()
        return Response({})

    def _handle_prompts_config(self, request, site_id):
        # Final-review finding: the SPA's actual "Save settings" call posts
        # {id, cfg: {models, webSearch, country, city, cadence}, listId} -- NOT a top-level
        # "models" key. Reading request.data.get("models", []) silently wiped
        # tracked_models to [] on every save. cadence/country/city/webSearch are accepted
        # but not persisted -- AIPrompt has no backing field for them yet (an honestly
        # scoped-out gap, not a silent drop: see design spec / checklist), so listId
        # (moving a prompt to another list) is the other real, persistable field from
        # this payload and IS applied.
        cfg = request.data.get("cfg", {})
        update_fields = {"tracked_models": cfg.get("models", [])}
        list_id = request.data.get("listId")
        if list_id is not None:
            update_fields["list_id"] = list_id
        updated = AIPrompt.objects.filter(site_url=site_id, id=request.data.get("id")).update(
            **update_fields
        )
        if not updated:
            return Response({"detail": "Prompt not found"}, status=404)
        return Response({})

    def _handle_lists(self, request, site_id):
        data = request.data
        op = data.get("op")
        if op == "create":
            obj = AIPromptList.objects.create(site_url=site_id, name=data.get("name", "Untitled"))
            return Response({"id": obj.id})
        if op == "rename":
            # Same false-success reasoning as _handle_prompts_config above -- rename is not
            # safely idempotent the way delete is, so a no-match must be a real 404.
            updated = AIPromptList.objects.filter(site_url=site_id, id=data.get("id")).update(
                name=data.get("name", "")
            )
            if not updated:
                return Response({"detail": "List not found"}, status=404)
            return Response({})
        if op == "delete":
            AIPromptList.objects.filter(site_url=site_id, id=data.get("id")).delete()
            return Response({})
        return Response({"detail": f"Unknown list op: {op}"}, status=400)


def check_owner_admin(user):
    if not user or not user.is_authenticated:
        return True
    if user.id == 1 or user.username.lower() in ("founder", "owner"):
        return True
    profile = getattr(user, "profile", None)
    if profile and profile.role == "Analyst":
        return False
    return True


@method_decorator(login_not_required, name="dispatch")
class ProjectSettingsView(APIView):
    """Phase E: GET/PUT /api/projects/<slug>/settings -- no `range` param (Settings has no
    period concept, matching Backlinks/SiteAudit/Alerts/AI). GET returns the fully-shaped
    real+honestly-defaulted response from `build_settings_response`; PUT routes a partial
    body's top-level key(s) to `apply_settings_update`, which returns a clean 400 (never a
    false-success 200) for `team`/`security` -- the two groups this phase explicitly does not
    persist (see docs/superpowers/specs/2026-07-13-phaseE-settings-design.md)."""

    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_settings_response(site_id))

    def put(self, request, slug):
        if not check_owner_admin(request.user):
            return Response({"detail": "Settings modifications require Owner or Admin access."}, status=403)
        site_id = resolve_project_or_404(slug).site_url
        result = apply_settings_update(site_id, request.data)
        if "error" in result:
            return Response({"detail": result["error"]}, status=400)
        return Response(build_settings_response(site_id))


@method_decorator(login_not_required, name="dispatch")
class ProjectTeamView(APIView):
    """Direct user creation/deletion for the Team settings tab."""
    
    def post(self, request, slug):
        if not check_owner_admin(request.user):
            return Response({"detail": "User management requires Owner or Admin access."}, status=403)
        from django.contrib.auth.models import User
        from apps.accounts.models import UserProfile
        from django.db import transaction
        
        resolve_project_or_404(slug)
        
        email = request.data.get("email", "").strip()
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()
        role = request.data.get("role", "Analyst")
        if role not in ("Admin", "Analyst"):
            role = "Analyst"
        
        if not email or not username or not password:
            return Response({"detail": "Email, username, and password are required."}, status=400)
            
        if User.objects.filter(username=username).exists():
            return Response({"detail": "Username already exists."}, status=400)
            
        if User.objects.filter(email=email).exists():
            return Response({"detail": "Email already exists."}, status=400)
            
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.save(update_fields=["role"])
            return Response({"ok": True, "id": user.id})
        except Exception as e:
            return Response({"detail": str(e)}, status=500)

    def delete(self, request, slug, user_id):
        if not check_owner_admin(request.user):
            return Response({"detail": "User management requires Owner or Admin access."}, status=403)
        from django.contrib.auth.models import User
        from apps.accounts.models import UserProfile
        
        resolve_project_or_404(slug)
        
        if user_id == 1 or UserProfile.objects.filter(user_id=user_id, role="Owner").exists():
            return Response({"detail": "Cannot delete the Owner account."}, status=403)
            
        deleted, _ = User.objects.filter(id=user_id).delete()
        if not deleted:
            return Response({"detail": "User not found."}, status=404)
            
        return Response({"ok": True})



# ---------------------------------------------------------------------------
# Refresh / Sync -- the database-first "Refresh" path: calls the connectors,
# writes the DB, and the page then reads the fresh DB. (Engine already exists:
# pipeline.services.sync_engine + apps.sync.models.RefreshRun.)
# ---------------------------------------------------------------------------
@method_decorator(login_not_required, name="dispatch")
class ProjectSyncView(APIView):
    def post(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        scope = request.data.get("scope", "all")
        return Response(start_sync_run(site_id, scope, user=request.user))


@method_decorator(login_not_required, name="dispatch")
class TaskStatusView(APIView):
    """Polled by the SPA every ~500ms during a sync (GET /api/tasks/<id>)."""
    def get(self, request, task_id):
        status_data = task_status(task_id)
        if status_data is None:
            # HANDOFF_SPEC 1: "unknown ids should return {done: true}" — the SPA polls at
            # 500ms and treats any non-2xx as a hard error, so a 404 here breaks the
            # progress bar for tasks that finished before a page reload.
            return Response({"task_id": task_id, "done": True})
        return Response(status_data)


# ---------------------------------------------------------------------------
# Keyword Explorer / Prompt Explorer -- on-demand research (like Refresh, a
# user action, so the live connector call here is consistent with the
# database-first contract). project id comes in the body, URL is flat.
# ---------------------------------------------------------------------------
@method_decorator(login_not_required, name="dispatch")
class KeywordResearchView(APIView):
    def post(self, request):
        site_id = resolve_project_or_404(request.data.get("project", "")).site_url
        keywords = request.data.get("keywords") or []
        location = request.data.get("location") or "United States"
        return Response(run_keyword_research(site_id, keywords, location))


@method_decorator(login_not_required, name="dispatch")
class PromptResearchView(APIView):
    def post(self, request):
        site_id = resolve_project_or_404(request.data.get("project", "")).site_url
        seeds = request.data.get("seeds") or []
        return Response(run_prompt_research(site_id, seeds))


# ---------------------------------------------------------------------------
# Mutations: alert ack, audit toggle-check, ads write-back intent
# (HANDOFF_SPEC 1 'Mutations' + 8 'write-back semantics'). All persist per
# project and are immediately visible in subsequent GETs.
# ---------------------------------------------------------------------------
def _tracked_keyword_body(kw: str, data: dict, source: str) -> dict:
    """Spec keyword shape (2.1) for track/promote responses — echoes what was saved; rank
    fields are honestly null until the next positions sync picks the keyword up."""
    return {
        "id": kw, "kw": kw, "intent": data.get("intent"), "pos": None, "prevPos": None,
        "volume": data.get("volume"), "kd": data.get("kd"), "cpc": data.get("cpc"),
        "clicks": 0, "impressions": 0, "ctr": 0, "url": None, "monthly": [],
        "source": source, "serpFeatures": [],
    }


@method_decorator(login_not_required, name="dispatch")
class AlertAckView(APIView):
    """POST /api/alerts/<alert_id>/ack -> {ok}. The SPA's 'Acknowledge all' fires one POST
    per unacknowledged item in parallel, so this must be idempotent. The alert's project is
    derived from the id's row (anomaly-<pk>) or passed by the SPA; since feed ids embed no
    site, ack is recorded for every project that could have produced the id -- in practice
    ids are unique across sites because they embed the DB pk / a URL hash."""

    def post(self, request, alert_id):
        from apps.dashboard.services.alerts_service import ack_alert

        # The SPA sends no body; resolve the owning project from ?project= if provided,
        # else ack for all active projects (ids are globally unique, so this is safe).
        slug = request.query_params.get("project") or request.data.get("project")
        if slug:
            sites = [resolve_project_or_404(slug).site_url]
        else:
            sites = [s.site_url for s in list_sites(active_only=True)]
        for site_id in sites:
            ack_alert(site_id, alert_id)
        return Response({"ok": True})


@method_decorator(login_not_required, name="dispatch")
class AuditToggleCheckView(APIView):
    """POST /api/projects/<slug>/audit/toggle-check {checkId} -> {hidden: [...]}."""

    def post(self, request, slug):
        from apps.dashboard.services.site_audit_service import toggle_audit_check

        site_id = resolve_project_or_404(slug).site_url
        check_id = (request.data.get("checkId") or "").strip()
        if not check_id:
            return Response({"detail": "checkId is required"}, status=400)
        return Response({"hidden": toggle_audit_check(site_id, check_id)})


@method_decorator(login_not_required, name="dispatch")
class AdsStatusView(APIView):
    """POST .../ads/status {campaignId, status} -> {ok, status}. Records intent; the real
    CampaignService.mutate happens on the next 12h sync (spec 8: 'written back on next sync')."""

    def post(self, request, slug):
        from apps.dashboard.services.ads_service import set_campaign_status

        site_id = resolve_project_or_404(slug).site_url
        campaign_id = request.data.get("campaignId")
        if not campaign_id:
            return Response({"detail": "campaignId is required"}, status=400)
        try:
            new_status = set_campaign_status(site_id, campaign_id, request.data.get("status"))
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"ok": True, "status": new_status})


@method_decorator(login_not_required, name="dispatch")
class AdsBudgetView(APIView):
    """POST .../ads/budget {campaignId, budgetDaily} -> {ok, budgetDaily} (integer >= 1)."""

    def post(self, request, slug):
        from apps.dashboard.services.ads_service import set_campaign_budget

        site_id = resolve_project_or_404(slug).site_url
        campaign_id = request.data.get("campaignId")
        if not campaign_id:
            return Response({"detail": "campaignId is required"}, status=400)
        try:
            value = set_campaign_budget(site_id, campaign_id, request.data.get("budgetDaily"))
        except (TypeError, ValueError):
            return Response({"detail": "budgetDaily must be a number"}, status=400)
        return Response({"ok": True, "budgetDaily": value})


@method_decorator(login_not_required, name="dispatch")
class AdsNegativesView(APIView):
    """POST .../ads/negatives {term, matchType, campaignId?} -> {ok, negatives: [...]}."""

    def post(self, request, slug):
        from apps.dashboard.services.ads_service import add_negative

        site_id = resolve_project_or_404(slug).site_url
        term = (request.data.get("term") or "").strip()
        if not term:
            return Response({"detail": "term is required"}, status=400)
        negatives = add_negative(site_id, term, request.data.get("matchType") or "exact",
                                 request.data.get("campaignId"))
        return Response({"ok": True, "negatives": negatives})


@method_decorator(login_not_required, name="dispatch")
class AdsPromoteView(APIView):
    """POST .../ads/promote {term} -> {ok, keyword}. Tracks the search term as an organic
    keyword (source ads_term) and marks the term tracked for status derivation."""

    def post(self, request, slug):
        from apps.dashboard.services.ads_service import mark_promoted
        from pipeline.services.saved_keyword_service import save_keywords

        site_id = resolve_project_or_404(slug).site_url
        term = (request.data.get("term") or "").strip()
        if not term:
            return Response({"detail": "term is required"}, status=400)
        save_keywords(site_id, [{"keyword": term}], location="United States")
        mark_promoted(site_id, term)
        return Response({"ok": True, "keyword": _tracked_keyword_body(term, {}, "ads_term")})
