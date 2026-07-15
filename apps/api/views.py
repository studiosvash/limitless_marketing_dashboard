from datetime import date as date_cls

from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sqlalchemy import func, select

from pipeline.db.schema import Site, SEODaily
from pipeline.services.site_service import add_site, list_sites
from pipeline.utils.db_connection import get_session

from .serializers import OverviewQuerySerializer, ProjectCreateSerializer, ProjectSerializer


@method_decorator(login_not_required, name="dispatch")
class PingView(APIView):
    """Smoke-test endpoint: proves auth + routing work before any real data endpoint exists."""

    def get(self, request):
        return Response({"ok": True})


@method_decorator(login_not_required, name="dispatch")
class ProjectListCreateView(APIView):
    """GET  /api/projects        -> list active projects (sites), HANDOFF_SPEC project shape.
    POST /api/projects         -> create a new project (site)."""

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
    """GET /api/projects/<slug>/overview?range=7d|30d|90d

    Returns {kpis, pillars, modules, priority, signals, trend, summary, topPages} per
    HANDOFF_SPEC.md 1/2.2 -- all real DB data. Site health (pillars/modules) and the
    cross-module Intelligence (priority) feed are populated from data we already have
    (GSC coverage, indexing, anomalies, technical issues, decision signals)."""

    def get(self, request, slug):
        from django.http import Http404

        from apps.dashboard.services.overview_service import (
            get_kpi_raw, build_kpis_api, build_top_pages_api, query_daily_traffic_raw,
            range_to_period_dates, get_ai_summary_text, parse_ai_summary,
            build_summary_lists, build_pillars, build_modules, compute_site_health,
            build_priority_feed,
        )
        from apps.dashboard.services.decision_engine import (
            generate_signals, generate_ad_overlap_signals,
        )
        from apps.dashboard.views import (
            _get_ads_overview, _get_keywords_overview,
        )

        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
            site_url = site.site_url if site else None
        if site_url is None:
            raise Http404(f"No project with slug '{slug}'")

        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        range_key = query.validated_data["range"]

        with get_session() as session:
            anchor = session.execute(
                select(func.max(SEODaily.date)).where(SEODaily.site_id == site_url)
            ).scalar() or date_cls.today()

        curr_start, curr_end, prev_start, prev_end = range_to_period_dates(range_key, anchor)

        kpis_current, kpis_previous = get_kpi_raw(site_url, curr_start, curr_end, prev_start, prev_end)
        kpis = build_kpis_api(kpis_current, kpis_previous)
        trend = query_daily_traffic_raw(site_url, curr_start, curr_end)
        top_pages = build_top_pages_api(site_url, curr_start, curr_end)

        ads_overview, ads_curr, ads_prev = _get_ads_overview(site_url, curr_start, curr_end, prev_start, prev_end)
        signals = generate_signals(kpis_current, kpis_previous, ads_curr, ads_prev)
        signals += generate_ad_overlap_signals(site_url, curr_start, curr_end)

        keywords_overview = _get_keywords_overview(site_url)
        top3_count = sum(
            1 for k in keywords_overview
            if k["position"] not in ("N/A",) and float(k["position"] or 99) <= 3
        )

        site_health = compute_site_health(site_url, curr_start, curr_end)
        pillars = build_pillars(kpis_current, kpis_previous, top3_count, site_health)
        seo_stat = f"{int(kpis_current['clicks']):,} clicks"
        modules = build_modules(seo_stat, len(keywords_overview), top3_count,
                                kpis_current["avg_position"], site_health)

        priority = build_priority_feed(site_url, curr_start, curr_end, signals)

        ai_summary_sections = parse_ai_summary(get_ai_summary_text(site_url))
        summary = build_summary_lists(ai_summary_sections)

        return Response({
            "kpis": kpis,
            "pillars": pillars,
            "modules": modules,
            "priority": priority,
            "signals": signals[:3],
            "trend": trend,
            "summary": summary,
            "topPages": top_pages,
        })


@method_decorator(login_not_required, name="dispatch")
class ProjectAlertsView(APIView):
    """GET /api/projects/<slug>/alerts -> {feed: [alert, ...]}

    The SPA fetches this on EVERY boot (for the sidebar 'Alerts' badge), so without it
    the app sets a global error and no view -- including Overview -- can render. The feed
    is the same cross-module aggregation that powers the Overview priority feed, returned
    in full (severity-sorted). Ack/mutation is Phase B; every item is unacknowledged here."""

    def get(self, request, slug):
        from django.http import Http404

        from apps.dashboard.services.overview_service import (
            range_to_period_dates, get_kpi_raw, build_alerts_feed,
        )
        from apps.dashboard.services.decision_engine import (
            generate_signals, generate_ad_overlap_signals,
        )
        from apps.dashboard.views import _get_ads_overview

        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
            site_url = site.site_url if site else None
        if site_url is None:
            raise Http404(f"No project with slug '{slug}'")

        with get_session() as session:
            anchor = session.execute(
                select(func.max(SEODaily.date)).where(SEODaily.site_id == site_url)
            ).scalar() or date_cls.today()

        curr_start, curr_end, prev_start, prev_end = range_to_period_dates("30d", anchor)
        kpis_current, kpis_previous = get_kpi_raw(site_url, curr_start, curr_end, prev_start, prev_end)
        _, ads_curr, ads_prev = _get_ads_overview(site_url, curr_start, curr_end, prev_start, prev_end)
        signals = generate_signals(kpis_current, kpis_previous, ads_curr, ads_prev)
        signals += generate_ad_overlap_signals(site_url, curr_start, curr_end)

        feed = build_alerts_feed(site_url, curr_start, curr_end, signals)
        return Response({"feed": feed})
