import logging
from datetime import date as date_cls

from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sqlalchemy import func, select, delete

logger = logging.getLogger(__name__)


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
    build_pillars, build_modules, build_priority_feed, query_top_ga4_pages_weekly_raw, query_top_audit_pages_raw,
    build_top_keywords_api, build_positioning_overview
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
from apps.dashboard.services.ai_service import (
    build_ai_response, inspect_question, run_prompt_checks,
)
from pipeline.services.ai_visibility_service import connectable_platforms
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

        try:
            new_id = add_site(
                site_url=site_url,
                site_name=data.get("name") or None,
                vertical=data.get("vertical") or None,
                location=data.get("location") or "United States",
                gsc_property=data.get("gsc_property") or None,
                ga4_property_id=data.get("ga4_property_id") or None,
                dataforseo_target_domain=data.get("dataforseo_target_domain") or None,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        with get_session() as session:
            site = session.get(Site, new_id)
            body = ProjectSerializer(site).data

        # Verify Google Search Console connectivity immediately so the UI can warn
        # the user if they added a site the connected Google Account doesn't own. The
        # Add-domain modal already runs this same check (POST /api/connection-check) before
        # the user ever presses "Add site", so for that path this is a confirming re-check.
        # It stays here as a safety net for any other caller (a script, a future integration)
        # that creates a project without going through the modal.
        try:
            from pipeline.connectors.gsc_property import resolve_gsc_property
            resolve_gsc_property(site_url, data.get("gsc_property") or site_url)
            body["gsc_connected"] = True
        except ValueError:
            body["gsc_connected"] = False
        except Exception:
            # A transient failure here answers "we don't know", not "yes". Silently reporting
            # True on any non-ValueError exception used to hide the one case this whole check
            # exists to catch -- a real connectivity problem that happens not to raise
            # ValueError -- behind a false "connected" claim the user had no reason to doubt.
            body["gsc_connected"] = False

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
class ProjectDetailView(APIView):
    def delete(self, request, slug):
        site = resolve_project_or_404(slug)
        from pipeline.services.site_service import delete_site
        delete_site(site.id, hard=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        top_ga4_pages = query_top_ga4_pages_weekly_raw(site_id)
        top_audit_pages = query_top_audit_pages_raw(site_id)

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
            # Already computed above for top3_count / the Keywords module card and then
            # discarded — the approved Overview design has a Top keywords table that had
            # nothing to read. Shape (shared_queries._get_keywords_overview): <=5 rows of
            # {keyword, position, clicks, impressions, volume}.
            # Passed through build_top_keywords_api so the rows carry raw numbers like
            # every other value in this response, instead of _get_keywords_overview's
            # old-Django-template display strings ("1,234"/"N/A"/"—").
            "topKeywords": build_top_keywords_api(keywords_overview),
            # Positioning vs Competitors summary card. Aggregated from the same competitor
            # grid the Positioning page renders per keyword; competitors with no captured
            # positions report state "none" and no average rather than a plausible number.
            "positioningOverview": build_positioning_overview(site_id),
            "topPages": top_pages,
            "topGa4Pages": top_ga4_pages,
            "topAuditPages": top_audit_pages,
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
        """Track a keyword (or batch of keywords) found in the Keyword Explorer -- persists to the site's saved
        keyword list (SavedKeyword), reusing saved_keyword_service. Supports either single {kw, volume, kd, cpc, intent}
        or batch {keywords: [{kw, volume, kd, cpc, intent}, ...]} payloads."""
        from pipeline.services.saved_keyword_service import save_keywords

        site = resolve_project_or_404(slug)
        site_id = site.site_url
        location = request.data.get("location") or site.location or "United States"

        # Check for batch payload first
        batch = request.data.get("keywords")
        if isinstance(batch, list) and batch:
            rows = []
            first_kw = ""
            for item in batch:
                if not isinstance(item, dict):
                    continue
                k = (item.get("kw") or item.get("keyword") or "").strip()
                if not k:
                    continue
                if not first_kw:
                    first_kw = k
                rows.append({
                    "keyword": k,
                    "search_volume": item.get("volume") if item.get("volume") is not None else item.get("search_volume"),
                    "keyword_difficulty": item.get("kd") if item.get("kd") is not None else item.get("keyword_difficulty"),
                    "cpc": item.get("cpc"),
                    "intent": item.get("intent"),
                })
            if not rows:
                return Response({"detail": "keywords list is empty or invalid"}, status=400)
            saved = save_keywords(site_id, rows, location=location)
            return Response({"ok": True, "saved": saved, "keyword": _tracked_keyword_body(first_kw, batch[0], "manual")})

        # Single keyword payload
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
        saved = save_keywords(site_id, [row], location=location)
        # HANDOFF_SPEC 1: track-keyword returns {ok, keyword} (keyword echoed in spec shape).
        return Response({"ok": True, "saved": saved, "keyword": _tracked_keyword_body(kw, request.data, "manual")})

    def put(self, request, slug):
        """Bulk replace all tracked keywords for the project."""
        from pipeline.services.saved_keyword_service import save_keywords
        from pipeline.utils.db_connection import get_session
        from pipeline.db.schema import SavedKeyword
        from sqlalchemy import delete
        
        site = resolve_project_or_404(slug)
        site_id = site.site_url
        location = request.data.get("location") or site.location or "United States"
        batch = request.data.get("keywords")
        # Kept as a debug signal (the batch is what the SPA actually sent, which is the first
        # thing you want when a save looks wrong) but routed through the module logger rather
        # than print(): a bare print wrote user keyword data to stdout on every save and
        # bypassed the logging config entirely, so it could be neither filtered nor routed.
        logger.debug("Incoming tracked-keyword batch for %s: %s", slug, batch)

        if not isinstance(batch, list):
            return Response({"detail": "keywords list required"}, status=400)
            
        with get_session() as session:
            session.execute(delete(SavedKeyword).where(SavedKeyword.site_id == site_id))
            session.commit()
            
        if batch:
            rows = []
            for item in batch:
                if not isinstance(item, dict):
                    continue
                k = (item.get("kw") or item.get("keyword") or "").strip()
                if not k:
                    continue
                rows.append({
                    "keyword": k,
                    "search_volume": item.get("volume") if item.get("volume") is not None else item.get("search_volume"),
                    "keyword_difficulty": item.get("kd") if item.get("kd") is not None else item.get("keyword_difficulty"),
                    "cpc": item.get("cpc"),
                    "intent": item.get("intent"),
                })
            save_keywords(site_id, rows, location)
            
        return Response({"ok": True, "count": len(batch)})


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
    `run` and `inspect` are the two handlers that spend money: they call a live answer engine
    through pipeline/services/ai_visibility_service and persist what really came back. They are
    reachable ONLY from this POST -- never from ProjectAIView's GET -- because one check is a
    real charge. Any other unmapped action still falls through to a clean 400."""

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
                # Seed the engines this build actually has a connector for, so "Run now" does
                # something on a freshly set-up project. `connectable_platforms()` (not
                # `connected_platforms()`) deliberately ignores whether the key is set right
                # now: which engines a prompt tracks must not depend on which env vars happened
                # to be present the moment setup ran.
                AIPrompt.objects.create(site_url=site_id, text=text.strip(),
                                        tracked_models=connectable_platforms())
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
        # Every "add prompts" path in the SPA (AI Keywords bulk-add, the Prompt Explorer, the
        # composer) funnels through this one handler. It used to create rows with no
        # tracked_models, which falls back to AIPrompt's default `[]` -- so a newly added
        # prompt showed "0 models", every model cell read "off", and run_prompt_checks skipped
        # it entirely (it treats an empty tracked_models list as nothing to run). The AI
        # Keywords -> "add as prompt" flow was therefore creating prompts that could never be
        # run. Seed the same connectable_platforms() _handle_setup already uses, so a prompt
        # is runnable the moment it's created regardless of which entry point added it.
        data = request.data
        list_id = data.get("listId")
        texts = [t.strip() for t in data.get("texts", []) if t and t.strip()]
        created = [
            AIPrompt(site_url=site_id, list_id=list_id, text=t, tracked_models=connectable_platforms())
            for t in texts
        ]
        AIPrompt.objects.bulk_create(created)
        return Response({"added": len(created)})

    def _handle_prompts_remove(self, request, site_id):
        # Accepts either a single "id" (the per-row Remove action) or a list "ids"
        # (the Tracked Prompts grid's select-all-then-remove bulk action) -- both funnel
        # through the same filter so a bulk remove is just as scoped to this project.
        ids = request.data.get("ids")
        if ids is None:
            single = request.data.get("id")
            ids = [single] if single is not None else []
        AIPrompt.objects.filter(site_url=site_id, id__in=ids).delete()
        return Response({})

    def _handle_prompts_config(self, request, site_id):
        # Final-review finding: the SPA's actual "Save settings" call posts
        # {id, cfg: {models, webSearch, country, city, cadence}, listId} -- NOT a top-level
        # "models" key. Reading request.data.get("models", []) silently wiped
        # tracked_models to [] on every save. cadence/country/city/webSearch used to be accepted
        # and silently discarded -- AIPrompt has no columns for them -- so the config modal
        # looked like it saved values that were never actually persisted. They now round-trip
        # through ai_service.set_prompt_cfg/get_prompt_cfg (see ai_service.PROMPT_CFG_KEY).
        # "text" is optional -- present only when the Prompt settings modal's editable
        # question field was changed. Blank/whitespace-only is ignored rather than saved,
        # so clearing the box by accident can never wipe out the tracked question.
        cfg = request.data.get("cfg", {})
        prompt_id = request.data.get("id")
        update_fields = {"tracked_models": cfg.get("models", [])}
        list_id = request.data.get("listId")
        if list_id is not None:
            update_fields["list_id"] = list_id
        text = request.data.get("text")
        if isinstance(text, str) and text.strip():
            update_fields["text"] = text.strip()
        updated = AIPrompt.objects.filter(site_url=site_id, id=prompt_id).update(
            **update_fields
        )
        if not updated:
            return Response({"detail": "Prompt not found"}, status=404)

        from apps.dashboard.services.ai_service import set_prompt_cfg
        set_prompt_cfg(
            site_id, prompt_id,
            cadence=cfg.get("cadence"), country=cfg.get("country"),
            city=cfg.get("city"), web_search=cfg.get("webSearch"),
        )
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

    def _handle_run(self, request, site_id):
        """Run tracked prompts against their tracked answer engines, for real.

        Scope comes from the body, matching what the SPA sends: `{promptId}` for one row's
        "Run now", `{listId}` for "Run <list> now", `{}` for "Run all now". Costs real money,
        which is why it is a POST the user pressed and never part of the page GET."""
        prompt_id = request.data.get("promptId")
        list_id = request.data.get("listId")
        qs = AIPrompt.objects.filter(site_url=site_id)
        if prompt_id is not None:
            qs = qs.filter(id=prompt_id)
            if not qs.exists():
                # Same false-success reasoning as _handle_prompts_config: telling the SPA "ran"
                # for a prompt that does not exist here is worse than a clean 404.
                return Response({"detail": "Prompt not found"}, status=404)
        elif list_id is not None:
            qs = qs.filter(list_id=list_id)
        return Response(run_prompt_checks(site_id, list(qs)))

    def _handle_inspect(self, request, site_id):
        """One ad-hoc answer-engine check for the Answer Inspector. Returns the stored history
        entry itself -- the SPA renders the response directly and then re-fetches."""
        outcome = inspect_question(
            site_id, request.data.get("question"), request.data.get("promptId")
        )
        if outcome.get("ok"):
            return Response(outcome["entry"])
        # 503 (not 200 with an empty shell) when the engine simply isn't reachable: a 200 would
        # let the UI render "you are not mentioned" for an answer that was never requested.
        status_code = 503 if outcome.get("notConnected") else 400
        return Response({"detail": outcome.get("reason")}, status=status_code)


def check_owner_admin(user):
    """Fail closed: an anonymous caller is never Owner/Admin. Every view that calls this is
    decorated `login_not_required` (so LoginRequiredMiddleware doesn't 302 token requests)
    but still inherits DRF's default IsAuthenticated, so a real request always arrives with
    an authenticated user -- returning True for AnonymousUser only ever opened a hole."""
    if not user or not user.is_authenticated:
        return False
    if user.id == 1 or user.username.lower() in ("founder", "owner"):
        return True
    profile = getattr(user, "profile", None)
    if profile and profile.role == "Analyst":
        return False
    return True


def check_owner_only(user):
    """Strict check: only Owner role (or user.id==1 / founder) can invite new users.
    Fail closed for anonymous callers -- see check_owner_admin above for why that is safe."""
    if not user or not user.is_authenticated:
        return False
    if user.id == 1 or getattr(user, "username", "").lower() in ("founder", "owner"):
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == "Owner")


@method_decorator(login_not_required, name="dispatch")
class ProjectSettingsView(APIView):
    """Phase E: GET/PUT /api/projects/<slug>/settings -- no `range` param (Settings has no
    period concept, matching Backlinks/SiteAudit/Alerts/AI). GET returns the fully-shaped
    real+honestly-defaulted response from `build_settings_response`; PUT routes a partial
    body's top-level key(s) to `apply_settings_update`, which returns a clean 400 (never a
    false-success 200) for `team`/`security` -- the two groups this phase explicitly does not
    persist (see .claude/api-reference.md)."""

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


@method_decorator(login_not_required, name="dispatch")
class ProjectInviteView(APIView):
    """POST /invite to send secure email invitation (Owner only). GET lists pending invitations. DELETE revokes."""
    
    def get(self, request, slug):
        from apps.accounts.models import UserInvitation
        resolve_project_or_404(slug)
        invites = UserInvitation.objects.filter(is_accepted=False).order_by("-created_at")
        return Response([
            {
                "id": inv.id,
                "email": inv.email,
                "role": inv.role,
                "invited_by": inv.invited_by.username if inv.invited_by else "Owner",
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            }
            for inv in invites
        ])

    def post(self, request, slug):
        if not check_owner_only(request.user):
            return Response({"detail": "Only the Owner can invite users via email."}, status=403)
        from django.contrib.auth.models import User
        from apps.accounts.models import UserInvitation
        from django.core.mail import send_mail
        from django.conf import settings
        from django.utils import timezone
        import datetime
        import secrets

        resolve_project_or_404(slug)

        email = request.data.get("email", "").strip()
        role = request.data.get("role", "Analyst")
        if role not in ("Admin", "Analyst"):
            role = "Analyst"

        if not email or "@" not in email:
            return Response({"detail": "Enter a valid email address."}, status=400)

        if User.objects.filter(email__iexact=email).exists():
            return Response({"detail": "A user with this email address already exists."}, status=400)

        # Remove any previous unaccepted invitation for this email so we can send a fresh one
        UserInvitation.objects.filter(email__iexact=email, is_accepted=False).delete()

        invited_by_user = request.user if (request.user and request.user.is_authenticated) else User.objects.filter(id=1).first()
        if not invited_by_user:
            invited_by_user = User.objects.first()

        # Token flow, NOT account-creation-plus-emailed-password. The previous version created
        # the User here and mailed a plaintext temporary password, which (a) put a credential in
        # an unencrypted channel, and (b) never wrote a UserInvitation row -- so the invite was
        # invisible to GET /invite, to Settings -> Pending invitations, and to the resend and
        # revoke endpoints, all of which query that table. The account is now created by
        # AuthInviteAcceptView once the invitee sets their own username and password.
        try:
            invitation = UserInvitation.objects.create(
                email=email,
                role=role,
                invited_by=invited_by_user,
                token=secrets.token_urlsafe(32),
                expires_at=timezone.now() + datetime.timedelta(hours=48),
                is_accepted=False,
            )
        except Exception as e:
            return Response({"detail": f"Failed to create invitation: {str(e)}"}, status=500)

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8000")
        # Same link shape ProjectInviteResendView already sends, so both paths land on the
        # accept-invite modal the SPA opens from the #/accept-invite route.
        invite_link = f"{frontend_url.rstrip('/')}/#/accept-invite?token={invitation.token}"

        subject = f"Invitation to join Limitless Marketing Dashboard ({role})"
        message = (
            f"Hello,\n\n"
            f"You have been invited by {invited_by_user.username if invited_by_user else 'Owner'} to join "
            f"the Limitless Marketing Dashboard as an {role}.\n\n"
            f"Click the link below to choose your own username and password (valid for 48 hours):\n"
            f"{invite_link}\n\n"
            f"If you weren't expecting this invitation you can ignore this email.\n\n"
            f"Best regards,\nLimitless Team"
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Limitless Dashboard <no-reply@fusehealth.com>")

        try:
            send_mail(subject, message, from_email, [email], fail_silently=False)
            logger.info(f"Sent invitation email to {email}")
        except Exception as e:
            logger.warning(f"Could not deliver email via SMTP ({e}).")

        # `id` is what the caller needs to resend or revoke this invitation without a
        # second round-trip; the SPA's pending-invitations list and the test suite both
        # read it. The token is deliberately NOT returned -- it belongs only in the email.
        return Response({"ok": True, "id": invitation.id, "email": invitation.email,
                         "role": invitation.role,
                         "expires_at": invitation.expires_at.isoformat()})

    def delete(self, request, slug, invite_id):
        if not check_owner_only(request.user):
            return Response({"detail": "Only the Owner can revoke invitations."}, status=403)
        from apps.accounts.models import UserInvitation
        resolve_project_or_404(slug)
        deleted, _ = UserInvitation.objects.filter(id=invite_id, is_accepted=False).delete()
        if not deleted:
            return Response({"detail": "Invitation not found or already accepted."}, status=404)
        return Response({"ok": True})


@method_decorator(login_not_required, name="dispatch")
class ProjectInviteResendView(APIView):
    """POST /invite/<id>/resend to resend email and extend validity by 48h (Owner only)."""

    def post(self, request, slug, invite_id):
        if not check_owner_only(request.user):
            return Response({"detail": "Only the Owner can resend invitations."}, status=403)
        from apps.accounts.models import UserInvitation
        from django.core.mail import send_mail
        from django.conf import settings
        from django.utils import timezone
        import datetime

        resolve_project_or_404(slug)
        invitation = UserInvitation.objects.filter(id=invite_id, is_accepted=False).first()
        if not invitation:
            return Response({"detail": "Invitation not found or already accepted."}, status=404)

        invitation.expires_at = timezone.now() + datetime.timedelta(hours=48)
        invitation.save(update_fields=["expires_at"])

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8000")
        invite_link = f"{frontend_url.rstrip('/')}/#/accept-invite?token={invitation.token}"

        subject = f"Reminder: Invitation to join Limitless Marketing Dashboard ({invitation.role})"
        message = (
            f"Hello,\n\n"
            f"This is a reminder that you have been invited to join the Limitless Marketing Dashboard as an {invitation.role}.\n\n"
            f"Please click the link below to set your username and secure password (valid for 48 hours):\n"
            f"{invite_link}\n\n"
            f"Best regards,\nLimitless Team"
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Limitless Dashboard <no-reply@fusehealth.com>")

        try:
            send_mail(subject, message, from_email, [invitation.email], fail_silently=False)
            logger.info(f"Resent invitation email to {invitation.email}: {invite_link}")
        except Exception as e:
            logger.warning(f"Could not deliver email via SMTP ({e}). Link: {invite_link}")

        return Response({"ok": True, "link": invite_link})


@method_decorator(login_not_required, name="dispatch")
class AuthInviteStatusView(APIView):
    """GET /api/auth/invite-status?token=XYZ to check if token is valid and return email/role."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from apps.accounts.models import UserInvitation
        from django.utils import timezone
        token = request.query_params.get("token", "").strip()
        if not token:
            return Response({"valid": False, "reason": "missing_token"}, status=400)

        invitation = UserInvitation.objects.filter(token=token).first()
        if not invitation:
            return Response({"valid": False, "reason": "not_found"}, status=404)

        if invitation.is_accepted:
            return Response({"valid": False, "reason": "already_accepted"}, status=400)

        if invitation.expires_at < timezone.now():
            return Response({"valid": False, "reason": "expired"}, status=400)

        return Response({
            "valid": True,
            "email": invitation.email,
            "role": invitation.role,
            "invited_by": invitation.invited_by.username if invitation.invited_by else "Owner"
        })


@method_decorator(login_not_required, name="dispatch")
class AuthInviteAcceptView(APIView):
    """POST /api/auth/accept-invite with {token, username, password} to activate user account."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):

        from django.contrib.auth.models import User
        from apps.accounts.models import UserInvitation, UserProfile
        from django.utils import timezone
        from django.db import transaction

        token = request.data.get("token", "").strip()
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()

        if not token or not username or not password:
            return Response({"detail": "Token, username, and password are required."}, status=400)

        if len(password) < 8:
            return Response({"detail": "Password must be at least 8 characters long."}, status=400)

        invitation = UserInvitation.objects.filter(token=token).first()
        if not invitation:
            return Response({"detail": "Invitation link is invalid or not found."}, status=404)

        if invitation.is_accepted:
            return Response({"detail": "This invitation has already been accepted."}, status=400)

        if invitation.expires_at < timezone.now():
            return Response({"detail": "This invitation link has expired. Please ask the owner to resend it."}, status=400)

        if User.objects.filter(username__iexact=username).exists():
            return Response({"detail": "This username is already taken. Please choose another username."}, status=400)

        if User.objects.filter(email__iexact=invitation.email).exists():
            return Response({"detail": "A user account with this email address already exists."}, status=400)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=invitation.email,
                    password=password
                )
                user.is_active = True
                user.save(update_fields=["is_active"])

                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = invitation.role
                profile.save(update_fields=["role"])

                invitation.is_accepted = True
                invitation.save(update_fields=["is_accepted"])

            return Response({
                "ok": True,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": invitation.role
            })
        except Exception as e:
            return Response({"detail": str(e)}, status=500)




# ---------------------------------------------------------------------------
# Refresh / Sync -- the database-first "Refresh" path: calls the connectors,
# writes the DB, and the page then reads the fresh DB. (Engine already exists:
# pipeline.services.sync_engine + apps.sync.models.RefreshRun.)
# ---------------------------------------------------------------------------
class ChangePasswordView(APIView):
    """POST /api/auth/password to change the logged-in user's password."""
    def post(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"detail": "Not logged in."}, status=401)
        old_pw = request.data.get("old_password", "")
        new_pw = request.data.get("new_password", "")
        if not user.check_password(old_pw):
            return Response({"detail": "Incorrect current password."}, status=400)
        if len(new_pw) < 8:
            return Response({"detail": "New password must be at least 8 characters."}, status=400)
        user.set_password(new_pw)
        user.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        return Response({"ok": True})


@method_decorator(login_not_required, name="dispatch")
class ProjectSyncView(APIView):
    def post(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        scope = request.data.get("scope", "all")

        # No credential gate here, on purpose. This used to refuse the WHOLE run with a 400
        # when Search Console access failed or the GA4 property was unset, for every scope
        # except positions/positions_new. Three things were wrong with that:
        #
        #   1. A brand-new domain has no GA4 property BY DEFINITION (add_site stores NULL), so
        #      the first "Refresh all" on every new site was rejected outright and nothing at
        #      all synced -- including the 9 connectors that never touch GA4.
        #   2. It gated scopes that need neither credential. The Backlinks refresh runs one
        #      DataForSEO connector, and it was blocked by a missing GA4 property.
        #   3. The 400 body has no `steps` key, so the SPA's startSync broke on the response
        #      shape rather than showing the message.
        #
        # start_sync_run now returns `warnings` describing exactly which steps will be skipped
        # and why, the run proceeds with everything that CAN run, and each unusable connector
        # reports its own honest status in the step checklist. One missing credential should
        # cost you that credential's data, not the entire refresh.
        return Response(start_sync_run(site_id, scope, user=request.user))


@method_decorator(login_not_required, name="dispatch")
class ProjectSyncActiveView(APIView):
    """Is a refresh in flight for this site? (GET /api/projects/<slug>/sync/active)

    The SPA calls this on boot so the progress bar survives a page reload. Without it, a hard
    refresh mid-sync lost the task id and a live 20-30 minute run became invisible -- which
    looks exactly like the sync having stopped.
    """
    def get(self, request, slug):
        from apps.dashboard.services.sync_api_service import active_run
        return Response(active_run(resolve_project_or_404(slug).site_url))


@method_decorator(login_not_required, name="dispatch")
class TaskStatusView(APIView):
    """Polled by the SPA during a sync (GET /api/tasks/<id>)."""
    def get(self, request, task_id):
        status_data = task_status(task_id)
        if status_data is None:
            # HANDOFF_SPEC 1: "unknown ids should return {done: true}" — the SPA treats any
            # non-2xx as a hard error, so a 404 here breaks the progress bar for tasks that
            # finished before a page reload.
            return Response({"task_id": task_id, "done": True})
        return Response(status_data)


@method_decorator(login_not_required, name="dispatch")
class ConnectionCheckView(APIView):
    """Live-probe GSC / GA4 / DataForSEO (+ optional integrations) for a domain.

    POST /api/connection-check
      {domain, gsc_property?, ga4_property_id?, dataforseo_target?, include_optional?}
      -> {ok, checks: [{id, label, state, detail, ...}]}

    This calls external APIs, which every page-data endpoint is forbidden to do. It is allowed
    here for the same reason /api/research, /api/domain-overview and /api/live-serp are: a user
    pressed a button and is waiting for the answer. It renders no page and is never polled.

    Takes a bare `domain` rather than a project slug on purpose -- the Add-domain modal runs
    this BEFORE the site exists, which is the whole point: verify the credentials, then create
    the site with working ones.
    """
    def post(self, request):
        from apps.dashboard.services.connection_check_service import check_connections

        domain = (request.data.get("domain") or "").strip().lower()
        domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
        if not domain:
            return Response({"detail": "domain is required"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(check_connections(
            domain=domain,
            gsc_property=request.data.get("gsc_property"),
            ga4_property_id=request.data.get("ga4_property_id"),
            dataforseo_target=request.data.get("dataforseo_target"),
            include_optional=bool(request.data.get("include_optional", True)),
        ))


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


@method_decorator(login_not_required, name="dispatch")
class DomainOverviewView(APIView):
    def post(self, request):
        from django.core.cache import cache
        from pipeline.connectors.dataforseo_domain_overview import DataForSEODomainOverviewConnector
        
        target = request.data.get("target") or ""
        location = request.data.get("location") or "United States"
        slug = request.data.get("project") or ""

        if not target:
            return Response({"detail": "Target URL is required"}, status=400)

        # Resolve the project up front so the metered call can be attributed to it. Without a
        # site_id the DataForSEO spend lands on an unattributed "" row and Settings' cost
        # breakdown under-reports whichever project actually ran the lookup.
        cost_site_id = ""
        if slug:
            try:
                cost_site_id = resolve_project_or_404(slug).site_url
            except Http404:
                raise

        cache_key = f"domain_overview_{target}_{location}"
        result = cache.get(cache_key)
        if result is None:
            connector = DataForSEODomainOverviewConnector()
            result = connector.get_domain_overview(target, location, site_id=cost_site_id)
            if result.get("status") == "ok":
                cache.set(cache_key, result, 60 * 60 * 24)  # 24 hours

        # `tracked` is applied AFTER the cache read, never stored in it: the DataForSEO payload
        # is identical for every project, but which of those keywords you already track is not.
        # Baking it into the cached blob would show project A's tracking state to project B.
        # Without a `project` the flag is simply absent -- the UI then shows Track on every row,
        # which is harmless because save_keywords upserts.
        if slug and result.get("status") == "ok" and result.get("keywords"):
            try:
                from pipeline.services.saved_keyword_service import list_saved_keywords
                site_id = resolve_project_or_404(slug).site_url
                tracked = {(k.get("keyword") or "").strip().lower()
                           for k in list_saved_keywords(site_id)}
                result = {**result, "keywords": [
                    {**row, "tracked": (row.get("keyword") or "").strip().lower() in tracked}
                    for row in result["keywords"]
                ]}
            except Http404:
                raise
            except Exception as e:
                # A tracking-state lookup must never break the research result itself.
                logger.warning(f"domain-overview tracked-flag lookup failed: {e}")

        return Response(result)


@method_decorator(login_not_required, name="dispatch")
class LiveSERPView(APIView):
    def post(self, request):
        from django.core.cache import cache
        from pipeline.connectors.dataforseo_live_serp import DataForSEOLiveSERPConnector
        
        keyword = request.data.get("keyword") or ""
        location = request.data.get("location") or "United States"

        # Attribute this call's DataForSEO charge to the project that made it. Without this,
        # every live SERP lookup wrote a connector_costs row with site_id="" -- real money that
        # no project's Usage & Budget panel could ever show. (Verified in the 2026-07-27
        # Postgres data: 3 of 5 recorded charges had an empty site_id.)
        #
        # `project` is OPTIONAL and resolved leniently on purpose: a live SERP lookup is a
        # global query that does not need a project to be meaningful, so a missing or unknown
        # slug must not 404 a working feature. It only costs the row its attribution.
        site_id = ""
        slug = request.data.get("project") or ""
        if slug:
            try:
                site_id = resolve_project_or_404(slug).site_url
            except Http404:
                logger.warning("live-serp: unknown project %r; cost will be unattributed", slug)

        if not keyword:
            return Response({"detail": "Keyword is required"}, status=400)

        # Cache key deliberately excludes site_id: a SERP for a keyword+location is the same
        # result whoever asked, so sharing it across projects avoids paying twice. Note this
        # means a cache HIT records no cost at all, which is correct -- no API call was made.
        cache_key = f"live_serp_{keyword}_{location}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        connector = DataForSEOLiveSERPConnector()
        result = connector.get_live_serp(keyword, location, site_id=site_id)
        
        if result.get("status") == "ok":
            cache.set(cache_key, result, 60 * 60 * 24) # 24 hours caching
            
        return Response(result)


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
class AlertUnackView(APIView):
    """POST /api/alerts/<alert_id>/unack -> {ok}. Undo for the row's "✓ Acknowledged" state.

    Acknowledging is not a destructive action, but it was a one-way one: a misclick (or an
    "Acknowledge all") hid a real alert from the badge with no way back short of editing the
    stored state. This reverses exactly what AlertAckView wrote, and resolves the site set
    the same way — with ?project= when the SPA scopes it, otherwise every active project —
    so an ack recorded across several projects is fully undone rather than half undone.
    Idempotent: un-acking something that was never acked is a no-op that still returns ok."""

    def post(self, request, alert_id):
        from apps.dashboard.services.alerts_service import unack_alert

        slug = request.query_params.get("project") or request.data.get("project")
        if slug:
            sites = [resolve_project_or_404(slug).site_url]
        else:
            sites = [s.site_url for s in list_sites(active_only=True)]
        for site_id in sites:
            unack_alert(site_id, alert_id)
        return Response({"ok": True})


@method_decorator(login_not_required, name="dispatch")
class AlertBatchAckView(APIView):
    """POST /api/alerts/ack {ids: [...], project?: <slug>} -> {ok, acknowledged: [...],
    failed: [{id, detail}]}.

    'Acknowledge all' used to mean one POST per unacknowledged row -- ~104 requests from a
    single click on a real feed, each re-reading and rewriting the same alertAcks list. This
    takes the whole list in one request and still reports a PER-ID outcome, so a partial
    failure stays visible and retryable instead of collapsing into one boolean.

    `project` scopes the ack to one site (the SPA always knows which project it is showing);
    without it the ack is recorded for every active project, matching AlertAckView, because
    feed ids embed no site. AlertAckView is unchanged and still serves single-row acks."""

    MAX_IDS = 500  # keeps the mirror UPDATE's bound parameters well under SQLite's ~999 cap

    def post(self, request):
        from apps.dashboard.services.alerts_service import ack_alerts

        ids = request.data.get("ids")
        if not isinstance(ids, list) or not ids:
            return Response({"detail": "ids must be a non-empty list of alert ids."}, status=400)
        if len(ids) > self.MAX_IDS:
            return Response(
                {"detail": f"Too many alerts in one request (max {self.MAX_IDS})."}, status=400
            )

        slug = request.query_params.get("project") or request.data.get("project")
        if slug:
            sites = [resolve_project_or_404(slug).site_url]
        else:
            sites = [s.site_url for s in list_sites(active_only=True)]

        if not sites:
            return Response({"detail": "No active project to acknowledge against."}, status=400)

        # With no `project` the same ids are acked against several sites. An id is only
        # reported acknowledged if EVERY site it was written to accepted it -- reporting
        # success while one site silently dropped it is exactly the invisible partial
        # failure this endpoint exists to prevent.
        failures: dict[str, dict] = {}
        accepted: list[str] = []
        for site_id in sites:
            result = ack_alerts(site_id, ids)
            for item in result["failed"]:
                failures.setdefault(str(item["id"]), item)
            for alert_id in result["acknowledged"]:
                if alert_id not in accepted:
                    accepted.append(alert_id)
        acknowledged = [a for a in accepted if a not in failures]
        failed = list(failures.values())
        return Response({"ok": not failed, "acknowledged": acknowledged, "failed": failed})


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
