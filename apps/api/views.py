from datetime import date as date_cls

from django.contrib.auth.decorators import login_not_required
from django.http import Http404
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sqlalchemy import func, select

from pipeline.services.site_service import add_site, list_sites
from pipeline.utils.db_connection import get_session
from pipeline.db.schema import Site, SEODaily

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
from apps.dashboard.views import (
    _get_ads_overview, _get_keywords_overview,
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
        return Response(body, status=status.HTTP_201_CREATED)


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
        modules = build_modules(seo_stat, len(keywords_overview), top3_count, kpis_current["avg_position"])

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
