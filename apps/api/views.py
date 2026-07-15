import math
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


def json_safe(obj):
    """Recursively replace NaN/inf floats with None. pandas leaves NaN in numeric columns,
    and DRF's JSON renderer rejects them ('Out of range float values are not JSON compliant').
    Applied to any payload built from a DataFrame before it goes out the wire."""
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    return obj


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


@method_decorator(login_not_required, name="dispatch")
class ProjectKeywordsView(APIView):
    """GET /api/projects/<slug>/keywords -> {keywords, segments, kpis, intents, difficulty}

    The tracked-keyword portfolio for the Keywords page (DB-first, reads keyword_rankings).
    The Keyword Explorer (POST /api/research) sits on top of this page, so the page must
    render for the Explorer to be reachable. Reuses the existing keyword-intelligence query
    (apps.dashboard.views._get_keyword_intelligence) rather than re-deriving segments."""

    _KD_HARD = 60
    _KD_MED = 30

    def get(self, request, slug):
        from datetime import timedelta

        from django.http import Http404

        from apps.dashboard.views import _get_keyword_intelligence
        from pipeline.db.schema import KeywordRanking

        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
            site_url = site.site_url if site else None
        if site_url is None:
            raise Http404(f"No project with slug '{slug}'")

        with get_session() as session:
            anchor = session.execute(
                select(func.max(KeywordRanking.date)).where(KeywordRanking.site_id == site_url)
            ).scalar() or date_cls.today()

        # Include the anchor date (unlike the Overview window, which treats it as "today").
        curr_end, curr_start = anchor, anchor - timedelta(days=90)
        prev_end, prev_start = curr_start - timedelta(days=1), curr_start - timedelta(days=91)
        intel = _get_keyword_intelligence(site_url, curr_start, curr_end, prev_start, prev_end)

        import math

        def _num(v):
            # pandas leaves NaN (a float) in numeric columns even after None-substitution, and
            # `float('nan') or 0` is NaN (truthy) -> int(NaN) explodes. Coerce NaN/None -> None.
            if v is None:
                return None
            try:
                f = float(v)
            except (TypeError, ValueError):
                return None
            return None if math.isnan(f) else f

        def _row(r):
            pos, prev = _num(r.get("position")), _num(r.get("prev_position"))
            return {
                "id": r["keyword"],
                "kw": r["keyword"],
                "url": r.get("url"),
                "source": r.get("source") or "gsc",
                "intent": (r.get("intent") or "informational").lower(),
                "pos": round(pos) if pos is not None else None,
                "prevPos": round(prev) if prev is not None else None,
                "volume": int(_num(r.get("search_volume")) or 0),
                "kd": int(_num(r.get("keyword_difficulty")) or 0),
                "clicks": int(_num(r.get("clicks")) or 0),
                "monthly": [],  # per-keyword monthly trend not stored; sparkline renders flat
            }

        keywords = [_row(r) for r in intel["all_keywords"]]
        seg_ids = lambda seg: [r["keyword"] for r in intel.get(seg, [])]

        return Response(json_safe({
            "keywords": keywords,
            "segments": {
                "quick_wins": seg_ids("quick_wins"),
                "striking": seg_ids("striking"),
                "declining": seg_ids("declining"),
                "low_ctr": seg_ids("low_ctr"),
            },
            "kpis": {
                "total": int(_num(intel["total_tracked"]) or 0),
                "avg_pos": round(_num(intel["avg_position"]), 1) if _num(intel["avg_position"]) else 0,
                "total_volume": int(_num(intel["total_volume"]) or 0),
                "total_clicks": int(_num(intel["total_clicks"]) or 0),
            },
            "intents": intel["intent_distribution"],
            "difficulty": {
                "easy": intel["kd_easy"],
                "medium": intel["kd_medium"],
                "hard": intel["kd_hard"],
            },
        }))


@method_decorator(login_not_required, name="dispatch")
class ProjectBacklinksView(APIView):
    """GET /api/projects/<slug>/backlinks -> the SPA Backlinks `data` payload.

    DB-first: returns the stored DataForSEO snapshot (built by backlinks_service on Refresh).
    Before the first Refresh there's no snapshot, so a zeroed empty-state payload is returned
    and the page renders cleanly instead of erroring."""

    def get(self, request, slug):
        from django.http import Http404

        from pipeline.services.backlinks_service import load_backlinks, empty_backlinks_payload

        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
            site_url = site.site_url if site else None
        if site_url is None:
            raise Http404(f"No project with slug '{slug}'")

        _, payload = load_backlinks(site_url)
        return Response(json_safe(payload or empty_backlinks_payload()))


@method_decorator(login_not_required, name="dispatch")
class KeywordResearchView(APIView):
    """POST /api/research  {project, keywords:[...], location} -> {location, cost, rows:[...]}

    The Keyword Explorer's on-demand expansion: one metered DataForSEO keyword_ideas call
    turns seed(s) into many keyword ideas. Read-only (never writes) and user-triggered, so
    calling the API here is consistent with the data-first contract. Rows already tracked for
    the project are flagged so the SPA can show the 'Tracked' badge."""

    def post(self, request):
        from pipeline.db.schema import KeywordRanking
        from pipeline.connectors.dataforseo_keywords import DataForSEOKeywordsConnector

        keywords = request.data.get("keywords") or []
        location = (request.data.get("location") or "United States").strip()
        slug = (request.data.get("project") or "").strip()
        if isinstance(keywords, str):
            keywords = keywords.split(",")
        seeds = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
        if not seeds:
            return Response({"detail": "At least one seed keyword is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        result = DataForSEOKeywordsConnector().expand_keywords(seeds, location)
        if result["status"] != "ok":
            return Response({"detail": result["error"]}, status=status.HTTP_502_BAD_GATEWAY)

        # Flag rows already tracked for this project (cheap distinct lookup, best-effort).
        tracked: set[str] = set()
        if slug:
            with get_session() as session:
                site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
                if site:
                    rows = session.execute(
                        select(KeywordRanking.keyword).where(KeywordRanking.site_id == site.site_url).distinct()
                    ).scalars().all()
                    tracked = {(k or "").lower() for k in rows}
        for row in result["rows"]:
            row["tracked"] = row["kw"].lower() in tracked

        return Response({
            "location": result["location"],
            "cost": result["cost"],
            "rows": result["rows"],
        })
