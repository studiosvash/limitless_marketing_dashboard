"""Dashboard page views.

These read from the database and render HTML — they never call an external API
(see the data-first contract in CLAUDE.md). Charts follow the DESIGN.md pattern:
build a Plotly spec dict in the view, hand it to the template via {{ ...|json_script }},
render client-side with Plotly.
"""

from datetime import date, timedelta

from django.shortcuts import render
from django.views.decorators.http import require_POST
from sqlalchemy import func, select

from apps.accounts.decorators import role_required
from apps.dashboard.services.overview_service import (
    get_kpi_raw, format_kpi_cards, query_top_pages_raw, query_daily_traffic_raw,
    build_traffic_chart, get_ai_summary_text, parse_ai_summary,
)
from apps.dashboard.services.seo_service import (
    query_low_ctr_pages_raw, query_seo_by_dimension_raw, query_seo_anomalies_raw,
    count_technical_issues, format_recent_anomalies,
)
from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw
from apps.dashboard.services.backlinks_service import query_backlinks_summary_raw, query_backlinks_table_raw
from pipeline.db.schema import SEODaily, SEOAggregate, AISummary, KeywordRanking, AdMetricDaily, CompetitorDomain, Anomaly, TechnicalIssue, PageSpeed, IndexingStatus, Backlink, KeywordOpportunity, CompetitorKeywordRanking, AIKeywordData
from pipeline.services.site_service import get_default_site_id
from pipeline.utils.period_utils import get_period_dates
from pipeline.utils.db_connection import get_session


def _get_latest_data_date(site_id: str):
    """Most recent day we actually have SEO data for. Periods anchor to this so
    the dashboard never defaults to a window that postdates the data."""
    try:
        with get_session() as session:
            return session.execute(
                select(func.max(SEODaily.date)).where(SEODaily.site_id == site_id)
            ).scalar()
    except Exception:
        return None


def get_active_period(request, site_id: str = None):
    """Read the active period dates from Django session, anchored to the latest
    available data date (not today's calendar date)."""
    mode = request.session.get("period_mode", "monthly")
    offset = request.session.get("period_offset", 0)

    # Optional: handle custom dates if they are stored as strings
    custom_start = request.session.get("start_date", None)
    custom_end = request.session.get("end_date", None)
    if custom_start and isinstance(custom_start, str):
        custom_start = date.fromisoformat(custom_start)
    if custom_end and isinstance(custom_end, str):
        custom_end = date.fromisoformat(custom_end)

    if site_id is None:
        site_id = request.session.get("selected_site_url") or get_default_site_id()
    anchor = _get_latest_data_date(site_id)

    curr_s, curr_e, prev_s, prev_e = get_period_dates(
        mode, offset, custom_start, custom_end, anchor=anchor
    )
    return curr_s, curr_e, prev_s, prev_e, mode


def _get_last_sync_time(site_id: str) -> str:
    """Calculate time since last successful sync."""
    try:
        from apps.sync.models import SyncLog, SyncStatus
        from django.utils.timezone import now
        log = SyncLog.objects.filter(site_url=site_id, status=SyncStatus.SUCCESS).order_by("-last_synced").first()
        if not log or not log.last_synced:
            return "Never"
        
        diff = now() - log.last_synced
        hours = int(diff.total_seconds() / 3600)
        
        if hours == 0:
            return "Just now"
        elif hours < 24:
            return f"{hours}h ago"
        else:
            return f"{hours // 24}d ago"
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_last_sync_time error: {e}", exc_info=True)
        return "Unknown"

def _get_ads_overview(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date) -> tuple[dict, dict, dict]:
    """Query ads summary (Google Ads + Meta) for current and previous period."""
    try:
        with get_session() as session:
            def get_ads_stats(start, end):
                row = session.execute(
                    select(
                        func.sum(AdMetricDaily.spend).label("total_cost"),
                        func.sum(AdMetricDaily.clicks).label("total_clicks"),
                        func.sum(AdMetricDaily.impressions).label("total_impressions"),
                        func.sum(AdMetricDaily.conversions).label("total_conversions"),
                    )
                    .where(AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
                ).first()
                return {
                    "total_spend": float(row.total_cost or 0),
                    "total_clicks": float(row.total_clicks or 0),
                    "total_impressions": float(row.total_impressions or 0),
                    "total_conversions": float(row.total_conversions or 0),
                }

            ads_curr = get_ads_stats(curr_start, curr_end)
            ads_prev = get_ads_stats(prev_start, prev_end)

            if not ads_curr["total_clicks"]:
                return {"status": "no_data"}, ads_curr, ads_prev

            cost = ads_curr["total_spend"]
            clicks = ads_curr["total_clicks"]
            impressions = ads_curr["total_impressions"]
            conversions = ads_curr["total_conversions"]

            overview = {
                "status": "ok",
                "cost": f"${cost:,.0f}",
                "cpc": f"${(cost / clicks):.2f}" if clicks else "$0.00",
                "clicks": f"{int(clicks):,.0f}",
                "impressions": f"{int(impressions):,.0f}",
                "ctr": f"{(clicks / impressions * 100):.1f}%" if impressions else "0%",
                "conversions": f"{int(conversions):,.0f}",
                "roi": f"${(conversions * 50 / cost):.2f}" if cost else "$0.00",  # rough estimate
            }
            return overview, ads_curr, ads_prev
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return {"status": "error"}, {}, {}


def _get_keywords_overview(site_id: str, limit: int = 5) -> list[dict]:
    """Query top performing keywords."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("avg_position"),
                    func.sum(KeywordRanking.clicks).label("total_clicks"),
                    func.sum(KeywordRanking.impressions).label("total_impressions"),
                    func.max(KeywordRanking.search_volume).label("search_volume"),
                )
                .where(KeywordRanking.site_id == site_id)
                .group_by(KeywordRanking.keyword)
                .order_by(func.sum(KeywordRanking.clicks).desc())
                .limit(limit)
            ).all()

            return [
                {
                    "keyword": row.keyword,
                    "position": f"{row.avg_position:.0f}" if row.avg_position else "N/A",
                    "clicks": f"{row.total_clicks:,.0f}",
                    "impressions": f"{row.total_impressions:,.0f}",
                    "volume": f"{row.search_volume:,}" if row.search_volume else "—",
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []

def _get_campaigns(site_id: str, start_date: date, end_date: date) -> list[dict]:
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    AdMetricDaily.campaign,
                    AdMetricDaily.platform,
                    func.sum(AdMetricDaily.spend).label("spend"),
                    func.sum(AdMetricDaily.clicks).label("clicks"),
                    func.sum(AdMetricDaily.impressions).label("impressions"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                    func.avg(AdMetricDaily.roas).label("roas"),
                )
                .where(AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start_date, AdMetricDaily.date <= end_date)
                .group_by(AdMetricDaily.campaign, AdMetricDaily.platform)
                .order_by(func.sum(AdMetricDaily.spend).desc())
            ).all()

            return [
                {
                    "campaign": row.campaign or "Unknown",
                    "platform": row.platform or "Unknown",
                    "spend": float(row.spend or 0),
                    "clicks": int(row.clicks or 0),
                    "impressions": int(row.impressions or 0),
                    "conversions": int(row.conversions or 0),
                    "cpc": float((row.spend or 0) / (row.clicks or 1)) if row.clicks else 0.0,
                    "ctr": float((row.clicks or 0) / (row.impressions or 1)) * 100 if row.impressions else 0.0,
                    "roas": float(row.roas or 0),
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_campaigns error: {e}", exc_info=True)
        return []

@role_required("ads")
def ads(request):
    """Ads page — paid media strategy."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)

    overview, curr, prev = _get_ads_overview(site_id, curr_start, curr_end, prev_start, prev_end)
    campaigns = _get_campaigns(site_id, curr_start, curr_end)

    context = {
        "active": "ads",
        "overview": overview,
        "campaigns": campaigns,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/ads.html", context)


def _get_keyword_opportunities(site_id: str, limit: int = 20) -> list[dict]:
    """Query top keyword opportunities (quick wins, striking distance, content gaps)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(KeywordOpportunity)
                .where(
                    KeywordOpportunity.site_id == site_id,
                    KeywordOpportunity.opportunity_type.in_(['quick_win', 'striking_distance', 'content_gap', 'rising'])
                )
                .order_by(KeywordOpportunity.opportunity_score.desc())
                .limit(limit)
            ).scalars().all()

            return [
                {
                    "keyword": row.keyword,
                    "current_position": row.current_position or "—",
                    "search_volume": f"{row.search_volume:,}" if row.search_volume else "—",
                    "difficulty": f"{row.keyword_difficulty:.0f}" if row.keyword_difficulty else "—",
                    "type": row.opportunity_type.replace('_', ' ').title() if row.opportunity_type else "Unknown",
                    "traffic_gain": f"+{row.estimated_traffic_gain:.0f}" if row.estimated_traffic_gain else "—",
                    "score": f"{row.opportunity_score:.0f}",
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_keyword_opportunities error: {e}", exc_info=True)
        return []


def _get_positioning_overview(site_id: str) -> dict:
    """Query competitor positioning summary."""
    try:
        with get_session() as session:
            competitors = session.execute(
                select(CompetitorDomain.competitor_domain, CompetitorDomain.avg_position)
                .where(CompetitorDomain.site_id == site_id)
                .order_by(CompetitorDomain.intersections.desc())
                .limit(3)
            ).all()

            if not competitors:
                return {"status": "no_data", "competitors": []}

            avg_your_position = session.execute(
                select(func.avg(KeywordRanking.position))
                .where(KeywordRanking.site_id == site_id)
            ).scalar()

            return {
                "status": "ok",
                "your_avg_position": f"{avg_your_position:.1f}" if avg_your_position else "N/A",
                "competitors": [
                    {
                        "domain": c.competitor_domain,
                        "position": f"{c.avg_position:.1f}" if c.avg_position else "N/A",
                    }
                    for c in competitors
                ],
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return {"status": "error", "competitors": []}


def _get_technical_issues(site_id: str, limit: int = 15) -> list[dict]:
    """Query recent technical SEO issues."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(TechnicalIssue)
                .where(TechnicalIssue.site_id == site_id)
                .order_by(TechnicalIssue.detected_at.desc())
                .limit(limit)
            ).scalars().all()

            issue_labels = {
                "not_found_404": "404 — Not found",
                "crawled_not_indexed": "Crawled, not indexed",
                "page_with_redirect": "Redirect",
                "long_url": "Long URL",
            }
            return [
                {
                    "url": (r.url or "").split("//")[-1][:55],
                    "issue": issue_labels.get(r.issue_type, r.issue_type.replace("_", " ").title()),
                    "severity": r.severity or "medium",
                    "description": r.description or "",
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


from apps.dashboard.services.decision_engine import generate_signals

@role_required("overview")
def overview(request):
    """Overview page — KPI cards, 30-day trend, AI summary, top pages, ads, keywords, positioning."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()

    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)

    seo_curr, seo_prev = get_kpi_raw(site_id, curr_start, curr_end, prev_start, prev_end)
    stats = format_kpi_cards(seo_curr, seo_prev)
    top_pages_raw = query_top_pages_raw(site_id, curr_start, curr_end)
    top_pages = [
        {"page": p["page"], "clicks": f"{p['clicks']:,}", "impressions": f"{p['impressions']:,}", "ctr": f"{p['ctr']:.1f}%"}
        for p in top_pages_raw
    ]
    chart = build_traffic_chart(query_daily_traffic_raw(site_id, curr_start, curr_end))
    ai_summary = get_ai_summary_text(site_id)
    ai_summary_sections = parse_ai_summary(ai_summary)
    ads_overview, ads_curr, ads_prev = _get_ads_overview(site_id, curr_start, curr_end, prev_start, prev_end)
    keywords_overview = _get_keywords_overview(site_id)
    positioning_overview = _get_positioning_overview(site_id)

    from apps.dashboard.services.decision_engine import generate_signals, generate_ad_overlap_signals
    signals = generate_signals(seo_curr, seo_prev, ads_curr, ads_prev)
    ad_overlap_signals = generate_ad_overlap_signals(site_id, curr_start, curr_end)
    signals.extend(ad_overlap_signals)
    context = {
        "active": "overview",
        "stats": stats,
        "top_pages": top_pages,
        "chart": chart,
        "ai_summary": ai_summary,
        "ai_summary_sections": ai_summary_sections,
        "ads_overview": ads_overview,
        "keywords_overview": keywords_overview,
        "positioning_overview": positioning_overview,
        "decision_signals": signals,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/overview.html", context)


@role_required("seo")
def seo(request):
    """SEO page — decision-focused: what needs attention, low-CTR opportunities,
    anomalies, technical issues, then geography/device context."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()

    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)

    seo_by_dim_raw = query_seo_by_dimension_raw(site_id, curr_start, curr_end)
    seo_by_country = [
        {"country": r["country"], "clicks": f"{r['clicks']:,.0f}", "impressions": f"{r['impressions']:,.0f}",
         "ctr": f"{r['ctr']:.2f}%", "position": f"{r['avg_position']:.1f}"}
        for r in seo_by_dim_raw["by_country"]
    ]
    seo_by_device = [
        {"device": r["device"], "clicks": f"{r['clicks']:,.0f}", "impressions": f"{r['impressions']:,.0f}",
         "ctr": f"{r['ctr']:.2f}%"}
        for r in seo_by_dim_raw["by_device"]
    ]
    anomalies_raw = query_seo_anomalies_raw(site_id)
    anomalies = format_recent_anomalies(anomalies_raw)
    issues = _get_technical_issues(site_id)
    low_ctr_raw = query_low_ctr_pages_raw(site_id, curr_start, curr_end)
    low_ctr = [
        {"url": p["url"], "url_short": p["url_short"], "clicks": p["clicks"],
         "impressions": p["impressions"], "ctr": p["ctr"], "avg_position": p["avg_position"]}
        for p in low_ctr_raw
    ]

    # Attention summary — counts that tell the user where to look first.
    high_sev_issues = sum(1 for i in issues if i.get("severity") == "high")
    attention = {
        "low_ctr_count": len(low_ctr),
        "anomaly_count": len(anomalies),
        "issue_count": len(issues),
        "high_sev_issues": high_sev_issues,
    }

    context = {
        "active": "seo",
        "seo_by_country": seo_by_country,
        "seo_by_device": seo_by_device,
        "anomalies": anomalies,
        "technical_issues": issues,
        "low_ctr_pages": low_ctr,
        "attention": attention,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/seo.html", context)


def _get_competitor_comparison(site_id: str) -> dict:
    """Query top competitors and their keyword overlap."""
    try:
        with get_session() as session:
            competitors = session.execute(
                select(CompetitorDomain)
                .where(CompetitorDomain.site_id == site_id)
                .order_by(CompetitorDomain.intersections.desc())
                .limit(5)
            ).scalars().all()

            return {
                "competitors": [
                    {
                        "domain": c.competitor_domain,
                        "intersections": c.intersections,
                        "avg_position": f"{c.avg_position:.1f}" if c.avg_position else "N/A",
                        "organic_keywords": c.full_domain_metrics_organic_count or 0,
                    }
                    for c in competitors
                ],
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return {"competitors": []}


def _get_ai_keywords(site_id: str, limit: int = 100) -> dict:
    """
    AI-search keyword data (DataForSEO AI Optimization) for the latest captured
    date: AI search volume + month-over-month trend. Reads only from the DB.
    Returns {"status": ..., "rows": [...]} the template branches on.
    """
    try:
        with get_session() as session:
            from pipeline.db.writer import ensure_tables
            ensure_tables(session, AIKeywordData)  # idempotent; clean empty state pre-first-refresh
            latest = session.execute(
                select(func.max(AIKeywordData.date)).where(AIKeywordData.site_id == site_id)
            ).scalar()
            if latest is None:
                return {"status": "no_data", "rows": []}

            rows = session.execute(
                select(AIKeywordData)
                .where(AIKeywordData.site_id == site_id, AIKeywordData.date == latest)
                .order_by(AIKeywordData.ai_search_volume.desc().nullslast())
                .limit(limit)
            ).scalars().all()

        out = []
        for r in rows:
            asv, prev = r.ai_search_volume, r.prev_ai_search_volume
            if asv is not None and prev is not None and prev != 0:
                change = round((asv - prev) / prev * 100)
                direction = "up" if change > 0 else "down" if change < 0 else "flat"
            else:
                change, direction = None, "flat"
            out.append({
                "keyword": r.keyword,
                "ai_volume": asv,
                "prev_volume": prev,
                "change_pct": abs(change) if change is not None else None,
                "direction": direction,
                "search_volume": r.search_volume,
            })
        return {"status": "ok", "rows": out, "latest_date": str(latest)}
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_ai_keywords error: {e}", exc_info=True)
        return {"status": "no_data", "rows": []}


# Locations offered in the Keyword Explorer dropdown (DataForSEO location_name values).
EXPLORER_LOCATIONS = [
    "United States", "United Kingdom", "Canada", "Australia", "India",
    "Germany", "France", "Spain", "Italy", "Netherlands",
    "Brazil", "Mexico", "United Arab Emirates", "Singapore",
]


@role_required("keywords")
def keywords(request):
    """Keywords page — Action buckets, Keyword Health Score, AI search demand, and the
    Keyword Explorer (ad-hoc research). The page render stays DB-only; the Explorer's
    DataForSEO call happens on the separate explore endpoint when the user searches."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)

    intelligence = get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start, prev_end)
    ai_keywords = _get_ai_keywords(site_id)

    from pipeline.services.saved_keyword_service import list_saved_keywords

    context = {
        "active": "keywords",
        "intelligence": intelligence,
        "ai_keywords": ai_keywords,
        "saved_keywords": list_saved_keywords(site_id),
        "explorer_locations": EXPLORER_LOCATIONS,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/keywords.html", context)


@role_required("keywords")
@require_POST
def keyword_explorer_search(request):
    """Keyword Explorer search — calls DataForSEO live for the entered keywords and
    returns the results table partial. This is the user-action API path (like Refresh),
    not a page render, so the live call here is consistent with the data-first contract."""
    raw = request.POST.get("keywords", "")
    location = (request.POST.get("location") or "United States").strip() or "United States"
    if location not in EXPLORER_LOCATIONS:
        location = "United States"

    keywords_list = [k.strip() for k in raw.split(",") if k.strip()]

    if not keywords_list:
        return render(request, "dashboard/partials/_explorer_results.html", {
            "result": {"status": "error", "rows": [], "no_data": [],
                       "location": location, "error": "Enter at least one keyword to search."},
        })

    try:
        from pipeline.connectors.dataforseo_keywords import DataForSEOKeywordsConnector
        result = DataForSEOKeywordsConnector().lookup_keywords(keywords_list, location)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"keyword_explorer_search error: {e}", exc_info=True)
        result = {"status": "error", "rows": [], "no_data": keywords_list,
                  "location": location, "error": "Something went wrong fetching keyword data."}

    return render(request, "dashboard/partials/_explorer_results.html", {"result": result})


@role_required("keywords")
@require_POST
def save_keywords(request):
    """Save selected Explorer rows to the site's research list, return the refreshed panel."""
    import json
    site_id = request.session.get("selected_site_url") or get_default_site_id()

    try:
        payload = json.loads(request.body or "{}")
        rows = payload.get("rows", [])
    except (ValueError, TypeError):
        rows = []

    from pipeline.services.saved_keyword_service import save_keywords as svc_save, list_saved_keywords
    svc_save(site_id, rows)

    return render(request, "dashboard/partials/_saved_keywords.html", {
        "saved_keywords": list_saved_keywords(site_id),
    })


@role_required("keywords")
@require_POST
def delete_saved_keyword(request):
    """Remove one saved research keyword, return the refreshed panel."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    keyword = (request.POST.get("keyword") or "").strip()
    location = (request.POST.get("location") or "United States").strip()

    from pipeline.services.saved_keyword_service import delete_saved_keyword as svc_delete, list_saved_keywords
    if keyword:
        svc_delete(site_id, keyword, location)

    return render(request, "dashboard/partials/_saved_keywords.html", {
        "saved_keywords": list_saved_keywords(site_id),
    })


def _get_page_health(site_id: str, curr_start: date, curr_end: date) -> dict:
    """
    Merge GSC traffic, PageSpeed, and IndexingStatus into a unified page health view.
    Returns site health score + critical issues + full page list.
    """
    try:
        with get_session() as session:
            # 1. GSC traffic per landing_page in period
            traffic_rows = session.execute(
                select(
                    SEODaily.landing_page.label("url"),
                    func.sum(SEODaily.clicks).label("clicks"),
                    func.sum(SEODaily.impressions).label("impressions"),
                    func.avg(SEODaily.ctr).label("avg_ctr"),
                    func.avg(SEODaily.avg_position).label("avg_position"),
                )
                .where(
                    SEODaily.site_id == site_id,
                    SEODaily.date >= curr_start,
                    SEODaily.date <= curr_end,
                    SEODaily.landing_page.isnot(None),
                )
                .group_by(SEODaily.landing_page)
                .order_by(func.sum(SEODaily.clicks).desc())
                .limit(200)
            ).all()

            # 2. PageSpeed (mobile strategy)
            speed_rows = session.execute(
                select(
                    PageSpeed.url,
                    PageSpeed.performance_score,
                    PageSpeed.seo_score,
                    PageSpeed.lcp_ms,
                    PageSpeed.cls,
                )
                .where(PageSpeed.site_id == site_id, PageSpeed.strategy == "mobile")
            ).all()

            # 3. Indexing status
            index_rows = session.execute(
                select(
                    IndexingStatus.url,
                    IndexingStatus.verdict,
                    IndexingStatus.coverage_state,
                )
                .where(IndexingStatus.site_id == site_id)
            ).all()

        # Build lookup dicts
        speed_map = {r.url: {"speed": r.performance_score, "seo_score": r.seo_score, "lcp_ms": r.lcp_ms, "cls": r.cls} for r in speed_rows}
        index_map = {r.url: {"verdict": r.verdict, "coverage": r.coverage_state} for r in index_rows}

        # Build page list
        pages_list = []
        for row in traffic_rows:
            url = row.url
            speed = speed_map.get(url, {})
            idx = index_map.get(url, {})
            pages_list.append({
                "url": url,
                "url_short": url.split("//")[-1][:60] if url else "",
                "clicks": int(row.clicks or 0),
                "impressions": int(row.impressions or 0),
                "ctr": round((row.avg_ctr or 0) * 100, 2),
                "avg_position": round(row.avg_position or 0, 1),
                "speed_score": speed.get("speed"),
                "seo_score": speed.get("seo_score"),
                "lcp_ms": speed.get("lcp_ms"),
                "cls": speed.get("cls"),
                "index_verdict": idx.get("verdict"),
                "index_coverage": idx.get("coverage"),
            })

        total = len(pages_list)

        # Compute composite site health score
        has_speed = any(p["speed_score"] is not None for p in pages_list)
        has_indexing = any(p["index_verdict"] is not None for p in pages_list)

        scores = []
        if pages_list:
            pct_with_clicks = sum(1 for p in pages_list if p["clicks"] > 0) / total * 100
            scores.append(min(100, pct_with_clicks))
        if has_speed:
            avg_speed = sum(p["speed_score"] for p in pages_list if p["speed_score"] is not None) / max(1, sum(1 for p in pages_list if p["speed_score"] is not None))
            scores.append(avg_speed)
        if has_indexing:
            pct_indexed = sum(1 for p in pages_list if p["index_verdict"] == "PASS") / max(1, sum(1 for p in pages_list if p["index_verdict"] is not None)) * 100
            scores.append(pct_indexed)

        site_health = int(sum(scores) / max(1, len(scores))) if scores else 0

        if site_health >= 70:
            health_color, health_label = "#10b981", "Healthy"
        elif site_health >= 40:
            health_color, health_label = "#f59e0b", "Needs Attention"
        else:
            health_color, health_label = "#ef4444", "Critical Issues"

        # Critical issues lists
        not_indexed = [p for p in pages_list if p["index_verdict"] and p["index_verdict"] != "PASS"]
        slow_pages = [p for p in pages_list if p["speed_score"] is not None and p["speed_score"] < 50]
        zero_traffic_high_impr = [p for p in pages_list if p["clicks"] == 0 and p["impressions"] >= 50]

        return {
            "site_health": site_health,
            "health_label": health_label,
            "health_color": health_color,
            "total_pages": total,
            "pages": pages_list,
            "not_indexed": not_indexed[:20],
            "slow_pages": sorted(slow_pages, key=lambda x: x["speed_score"])[:20],
            "zero_traffic_high_impr": zero_traffic_high_impr[:20],
            "has_speed": has_speed,
            "has_indexing": has_indexing,
        }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return {
            "site_health": 0, "health_label": "Error", "health_color": "#ef4444",
            "total_pages": 0, "pages": [], "not_indexed": [], "slow_pages": [],
            "zero_traffic_high_impr": [], "has_speed": False, "has_indexing": False,
        }


@role_required("pages")
def pages(request):
    """Page Health Intelligence — GSC + PageSpeed + Indexing merged view."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)

    page_health = _get_page_health(site_id, curr_start, curr_end)

    context = {
        "active": "pages",
        "page_health": page_health,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/pages.html", context)



def _get_all_anomalies(site_id: str, limit: int = 50) -> list[dict]:
    """Query all recent anomalies (not just unacknowledged)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(Anomaly)
                .where(Anomaly.site_id == site_id)
                .order_by(Anomaly.detected_at.desc())
                .limit(limit)
            ).scalars().all()

            labels = {
                "seo_clicks": "Clicks", "seo_impressions": "Impressions",
                "seo_ctr": "CTR", "seo_avg_position": "Avg. position",
                "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
                "ad_impressions": "Ad impressions", "ad_conversions": "Conversions",
            }
            out = []
            for r in rows:
                up = r.actual_value >= r.baseline_value
                out.append({
                    "id": r.id,
                    "metric": labels.get(r.metric_type, r.metric_type),
                    "severity": r.severity,
                    "direction": "up" if up else "down",
                    "deviation": f"{'+' if up else '-'}{r.deviation_pct:.0f}%",
                    "actual": f"{r.actual_value:,.0f}",
                    "baseline": f"{r.baseline_value:,.0f}",
                    "date": str(r.date),
                    "acknowledged": r.is_acknowledged,
                })
            return out
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def _get_page_speed_issues(site_id: str, limit: int = 20) -> list[dict]:
    """Query pages with poor PageSpeed scores."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(PageSpeed)
                .where(PageSpeed.site_id == site_id)
                .order_by(PageSpeed.performance_score.asc())
                .limit(limit)
            ).scalars().all()

            return [
                {
                    "url": r.url.split("/")[-1][:40],
                    "performance": r.performance_score or 0,
                    "seo": r.seo_score or 0,
                    "accessibility": r.accessibility_score or 0,
                    "best_practices": r.best_practices_score or 0,
                    "lcp": f"{r.lcp_ms}ms" if r.lcp_ms else "—",
                    "cls": f"{r.cls:.2f}" if r.cls else "—",
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def _humanize_enum(value: str) -> str:
    """Turn raw GSC enum strings into something a person can read.
    e.g. 'INDEXING_STATE_UNSPECIFIED' → '—', 'INDEXING_ALLOWED' → 'Allowed'."""
    if not value:
        return "—"
    v = value.strip()
    mapping = {
        "PASS": "Indexed",
        "NEUTRAL": "Needs attention",
        "FAIL": "Failed",
        "VERDICT_UNSPECIFIED": "—",
        "INDEXING_ALLOWED": "Allowed",
        "INDEXING_STATE_UNSPECIFIED": "—",
        "BLOCKED_BY_META_TAG": "Blocked (meta tag)",
        "BLOCKED_BY_HTTP_HEADER": "Blocked (HTTP header)",
        "BLOCKED_BY_ROBOTS_TXT": "Blocked (robots.txt)",
        "MOBILE_USABILITY_UNSPECIFIED": "—",
    }
    if v in mapping:
        return mapping[v]
    if v.endswith("_UNSPECIFIED"):
        return "—"
    # Fallback: ENUM_CASE → Title case
    return v.replace("_", " ").capitalize()


def _get_indexing_issues(site_id: str, limit: int = 200) -> list[dict]:
    """Query indexing status, humanized, with problems sorted to the top."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(IndexingStatus)
                .where(IndexingStatus.site_id == site_id)
                .order_by(IndexingStatus.last_crawl_time.desc())
                .limit(limit)
            ).scalars().all()

            out = []
            for r in rows:
                coverage = r.coverage_state or "—"
                is_ok = (r.verdict == "PASS")
                out.append({
                    "url": (r.url or "").split("//")[-1][:55],
                    "verdict": r.verdict or "",
                    "verdict_label": _humanize_enum(r.verdict),
                    "is_ok": is_ok,
                    "coverage": coverage,
                    "indexing": _humanize_enum(r.indexing_state),
                    "mobile_usability": _humanize_enum(r.mobile_usability),
                })
            # Problems first (not OK), then OK pages.
            out.sort(key=lambda x: x["is_ok"])
            return out
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def _get_indexing_summary(indexing: list[dict]) -> dict:
    """Counts for the Alerts header: how many pages are healthy vs problematic."""
    total = len(indexing)
    indexed = sum(1 for i in indexing if i["is_ok"])
    not_found = sum(1 for i in indexing if "404" in i["coverage"] or "not found" in i["coverage"].lower())
    not_indexed = sum(1 for i in indexing if not i["is_ok"] and "not indexed" in i["coverage"].lower())
    return {
        "total": total,
        "indexed": indexed,
        "not_found": not_found,
        "not_indexed": not_indexed,
        "problems": total - indexed,
    }


@role_required("backlinks")
def backlinks(request):
    """Backlinks page — link acquisition and lost links."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()

    summary = query_backlinks_summary_raw(site_id)
    table = query_backlinks_table_raw(site_id)

    context = {
        "active": "backlinks",
        "summary": summary,
        "backlinks": table,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/backlinks.html", context)




def _get_position_changes(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date) -> dict:
    try:
        with get_session() as session:
            # Get current period keywords with enriched data
            curr_rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("pos"),
                    func.sum(KeywordRanking.clicks).label("clicks"),
                    func.sum(KeywordRanking.impressions).label("impressions"),
                    func.max(KeywordRanking.search_volume).label("volume"),
                    func.max(KeywordRanking.url).label("url"),
                )
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= curr_start, KeywordRanking.date <= curr_end)
                .group_by(KeywordRanking.keyword)
            ).all()

            # Get previous period keywords
            prev_rows = session.execute(
                select(KeywordRanking.keyword, func.avg(KeywordRanking.position).label("pos"))
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= prev_start, KeywordRanking.date <= prev_end)
                .group_by(KeywordRanking.keyword)
            ).all()

            curr_map = {r.keyword: r for r in curr_rows}
            prev_map = {r.keyword: r.pos for r in prev_rows}

            improved = []
            declined = []
            new_kws = []
            lost = []

            for kw, row in curr_map.items():
                c_pos = row.pos
                entry = {
                    "keyword": kw,
                    "curr_pos": round(c_pos, 1),
                    "clicks": int(row.clicks or 0),
                    "volume": int(row.volume or 0),
                    "url": row.url or "",
                }
                if kw in prev_map:
                    p_pos = prev_map[kw]
                    delta = p_pos - c_pos  # positive = improved
                    entry["prev_pos"] = round(p_pos, 1)
                    entry["delta"] = round(delta, 1)
                    if delta >= 2:
                        improved.append(entry)
                    elif delta <= -2:
                        declined.append(entry)
                else:
                    entry["delta"] = 0
                    new_kws.append(entry)

            for kw, p_pos in prev_map.items():
                if kw not in curr_map:
                    lost.append({"keyword": kw, "prev_pos": round(p_pos, 1)})

            improved.sort(key=lambda x: x["delta"], reverse=True)
            declined.sort(key=lambda x: abs(x["delta"]), reverse=True)
            new_kws.sort(key=lambda x: x["curr_pos"])
            lost.sort(key=lambda x: x["prev_pos"])

            return {
                "improved": improved[:15],
                "improved_count": len(improved),
                "declined": declined[:15],
                "declined_count": len(declined),
                "new": new_kws[:15],
                "new_count": len(new_kws),
                "lost": lost[:15],
                "lost_count": len(lost)
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_position_changes error: {e}", exc_info=True)
        return {k: [] if "count" not in k else 0 for k in ["improved", "improved_count", "declined", "declined_count", "new", "new_count", "lost", "lost_count"]}


def _get_ranking_distribution(site_id: str, curr_start: date, curr_end: date) -> dict:
    """Compute keyword counts per SERP position bucket — SEMrush Landscape style."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("avg_pos"),
                    func.sum(KeywordRanking.clicks).label("clicks"),
                    func.sum(KeywordRanking.impressions).label("impressions"),
                )
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= curr_start, KeywordRanking.date <= curr_end)
                .group_by(KeywordRanking.keyword)
            ).all()

            if not rows:
                return {"total": 0, "top3": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0,
                        "avg_position": 0, "total_clicks": 0, "total_impressions": 0,
                        "top3_pct": 0, "top10_pct": 0, "top20_pct": 0, "rest_pct": 0}

            total = len(rows)
            top3 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 3)
            top10 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 10)
            top20 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 20)
            top50 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 50)
            top100 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 100)

            positioned_rows = [r for r in rows if r.avg_pos is not None]
            avg_pos = sum(r.avg_pos for r in positioned_rows) / len(positioned_rows) if positioned_rows else 0
            total_clicks = sum(int(r.clicks or 0) for r in rows)
            total_impressions = sum(int(r.impressions or 0) for r in rows)

            # Percentage buckets for the distribution bar
            top3_pct = round(top3 / total * 100) if total else 0
            top4_10_pct = round((top10 - top3) / total * 100) if total else 0
            top11_20_pct = round((top20 - top10) / total * 100) if total else 0
            rest_pct = 100 - top3_pct - top4_10_pct - top11_20_pct

            return {
                "total": total,
                "top3": top3, "top10": top10, "top20": top20, "top50": top50, "top100": top100,
                "avg_position": round(avg_pos, 1),
                "total_clicks": total_clicks,
                "total_impressions": total_impressions,
                "top3_pct": top3_pct,
                "top4_10_pct": top4_10_pct,
                "top11_20_pct": top11_20_pct,
                "rest_pct": max(rest_pct, 0),
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_ranking_distribution error: {e}", exc_info=True)
        return {"total": 0, "top3": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0,
                "avg_position": 0, "total_clicks": 0, "total_impressions": 0,
                "top3_pct": 0, "top4_10_pct": 0, "top11_20_pct": 0, "rest_pct": 0}


def _get_full_rankings(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date, limit: int = 200) -> list[dict]:
    """Get full keyword rankings table with position deltas — for the Rankings tab."""
    try:
        with get_session() as session:
            curr_rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("position"),
                    func.sum(KeywordRanking.clicks).label("clicks"),
                    func.sum(KeywordRanking.impressions).label("impressions"),
                    func.max(KeywordRanking.search_volume).label("volume"),
                    func.max(KeywordRanking.keyword_difficulty).label("kd"),
                    func.max(KeywordRanking.cpc).label("cpc"),
                    func.max(KeywordRanking.intent).label("intent"),
                    func.max(KeywordRanking.url).label("url"),
                )
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= curr_start, KeywordRanking.date <= curr_end)
                .group_by(KeywordRanking.keyword)
                .order_by(func.sum(KeywordRanking.clicks).desc())
                .limit(limit)
            ).all()

            prev_rows = session.execute(
                select(KeywordRanking.keyword, func.avg(KeywordRanking.position).label("pos"))
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= prev_start, KeywordRanking.date <= prev_end)
                .group_by(KeywordRanking.keyword)
            ).all()

            prev_map = {r.keyword: r.pos for r in prev_rows}

            results = []
            for r in curr_rows:
                pos = round(r.position, 1) if r.position else None
                prev_pos = prev_map.get(r.keyword)
                delta = round(prev_pos - pos, 1) if prev_pos and pos else None

                results.append({
                    "keyword": r.keyword,
                    "position": pos,
                    "prev_position": round(prev_pos, 1) if prev_pos else None,
                    "delta": delta,
                    "clicks": int(r.clicks or 0),
                    "impressions": int(r.impressions or 0),
                    "volume": int(r.volume) if r.volume else None,
                    "kd": round(r.kd, 0) if r.kd else None,
                    "cpc": round(r.cpc, 2) if r.cpc else None,
                    "intent": r.intent or "",
                    "url": r.url or "",
                    "url_short": (r.url or "").split("//")[-1][:50] if r.url else "",
                })
            return results
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_full_rankings error: {e}", exc_info=True)
        return []


def _get_visibility_trend(site_id: str, days: int = 90) -> dict:
    try:
        start_date = date.today() - timedelta(days=days)
        with get_session() as session:
            rows = session.execute(
                select(SEODaily.date, func.avg(SEODaily.position).label("avg_pos"))
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date)
                .group_by(SEODaily.date)
                .order_by(SEODaily.date.asc())
            ).all()
            if not rows:
                return None

            dates = [str(r.date) for r in rows]
            pos = [float(r.avg_pos) for r in rows]

            return {
                "data": [{
                    "x": dates,
                    "y": pos,
                    "name": "Avg Position",
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": "#10b981", "width": 3, "shape": "spline"},
                    "fill": "tozeroy",
                    "fillcolor": "rgba(16,185,129,0.08)",
                }],
                "layout": {
                    "font": {"family": "Inter", "size": 12, "color": "#64748b"},
                    "paper_bgcolor": "white",
                    "plot_bgcolor": "white",
                    "margin": {"l": 40, "r": 40, "t": 10, "b": 30},
                    "xaxis": {"showgrid": False},
                    "yaxis": {"gridcolor": "#f1f5f9", "zeroline": False, "autorange": "reversed"},
                    "hovermode": "x unified",
                },
                "config": {"displayModeBar": False, "responsive": True},
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_visibility_trend error: {e}", exc_info=True)
        return None


def _diff_label(latest, prev):
    """Position diff (prev - latest): positive = moved up. Returns (value, direction)."""
    if latest is None or prev is None:
        return None, "flat"
    delta = round(prev - latest, 0)
    if delta > 0:
        return int(delta), "up"
    if delta < 0:
        return int(abs(delta)), "down"
    return 0, "flat"


def _get_competitor_grid(site_id: str, limit: int = 100) -> dict:
    """
    SEMrush-style per-keyword competitor grid: for each tracked keyword, your rank
    plus each tracked competitor's rank on the two most recent capture dates, with
    the date-over-date diff. Reads only from the DB (competitor_keyword_rankings +
    keyword_rankings) — never calls an API. Returns a status the template branches on.
    """
    try:
        from pipeline.services.competitor_service import get_tracked_competitors, is_overridden
        competitors = get_tracked_competitors(site_id)
        if not competitors:
            return {"status": "no_competitors", "competitors": [], "rows": [], "dates": []}

        with get_session() as session:
            from pipeline.db.writer import ensure_tables
            ensure_tables(session, CompetitorKeywordRanking)  # idempotent; clean empty state pre-first-refresh
            dates = session.execute(
                select(CompetitorKeywordRanking.date)
                .where(CompetitorKeywordRanking.site_id == site_id)
                .group_by(CompetitorKeywordRanking.date)
                .order_by(CompetitorKeywordRanking.date.desc())
                .limit(2)
            ).scalars().all()
            if not dates:
                return {"status": "no_data", "competitors": competitors, "rows": [],
                        "overridden": is_overridden(site_id), "dates": []}
            latest = dates[0]
            prev = dates[1] if len(dates) > 1 else None
            both = [d for d in (latest, prev) if d is not None]

            comp_rows = session.execute(
                select(
                    CompetitorKeywordRanking.keyword,
                    CompetitorKeywordRanking.competitor_domain,
                    CompetitorKeywordRanking.date,
                    CompetitorKeywordRanking.position,
                )
                .where(CompetitorKeywordRanking.site_id == site_id,
                       CompetitorKeywordRanking.date.in_(both))
            ).all()

            your_rows = session.execute(
                select(KeywordRanking.keyword, KeywordRanking.date,
                       func.avg(KeywordRanking.position).label("pos"))
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date.in_(both))
                .group_by(KeywordRanking.keyword, KeywordRanking.date)
            ).all()

        # cell[keyword][domain] = {"latest": pos, "prev": pos}
        cell: dict = {}
        for r in comp_rows:
            slot = cell.setdefault(r.keyword, {}).setdefault(r.competitor_domain, {})
            slot["latest" if r.date == latest else "prev"] = r.position
        your_cell: dict = {}
        for r in your_rows:
            slot = your_cell.setdefault(r.keyword, {})
            pos = round(r.pos, 0) if r.pos is not None else None
            slot["latest" if r.date == latest else "prev"] = int(pos) if pos is not None else None

        keywords = sorted(set(cell) | set(your_cell))

        def make_cell(data: dict) -> dict:
            lp, pp = data.get("latest"), data.get("prev")
            diff, direction = _diff_label(lp, pp)
            return {"pos": lp, "prev": pp, "diff": diff, "direction": direction}

        rows = []
        for kw in keywords:
            you = make_cell(your_cell.get(kw, {}))
            comp_cells = [
                {"domain": dom, **make_cell(cell.get(kw, {}).get(dom, {}))}
                for dom in competitors
            ]
            rows.append({"keyword": kw, "you": you, "cells": comp_cells})

        # Surface keywords where you actually rank first; nulls (not ranking) last.
        rows.sort(key=lambda r: (r["you"]["pos"] is None, r["you"]["pos"] or 9999))

        return {
            "status": "ok",
            "competitors": competitors,
            "rows": rows[:limit],
            "latest_date": str(latest),
            "prev_date": str(prev) if prev else None,
            "overridden": is_overridden(site_id),
        }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_competitor_grid error: {e}", exc_info=True)
        return {"status": "no_data", "competitors": [], "rows": [], "dates": []}


@role_required("positioning")
def positioning(request):
    """Position Tracking page — SEMrush-style rank tracker dashboard."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)

    pos_overview = _get_positioning_overview(site_id)
    distribution = _get_ranking_distribution(site_id, curr_start, curr_end)
    changes = _get_position_changes(site_id, curr_start, curr_end, prev_start, prev_end)
    trend = _get_visibility_trend(site_id, days=90)
    rankings = _get_full_rankings(site_id, curr_start, curr_end, prev_start, prev_end)
    opportunities = _get_keyword_opportunities(site_id, limit=20)
    competitor_grid = _get_competitor_grid(site_id)

    context = {
        "active": "positioning",
        "overview": pos_overview,
        "competitors": pos_overview.get("competitors", []),
        "distribution": distribution,
        "position_changes": changes,
        "visibility_trend": trend,
        "rankings": rankings,
        "opportunities": opportunities,
        "competitor_grid": competitor_grid,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/positioning.html", context)


@role_required("alerts")
def alerts(request):
    """Alerts page — anomalies, PageSpeed issues, indexing problems, technical issues."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()

    anomalies = _get_all_anomalies(site_id)
    page_speed = _get_page_speed_issues(site_id)
    indexing = _get_indexing_issues(site_id)
    indexing_summary = _get_indexing_summary(indexing)
    issues = _get_technical_issues(site_id)

    context = {
        "active": "alerts",
        "anomalies": anomalies,
        "page_speed": page_speed,
        "indexing": indexing,
        "indexing_summary": indexing_summary,
        "technical_issues": issues,
        "last_sync": _get_last_sync_time(site_id),
    }
    return render(request, "dashboard/alerts.html", context)


from django.http import HttpResponse
from django.views.decorators.http import require_POST

@role_required("alerts")
@require_POST
def acknowledge_anomaly(request, anomaly_id):
    """Mark an anomaly as acknowledged via HTMX."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    try:
        with get_session() as session:
            anomaly = session.execute(
                select(Anomaly).where(Anomaly.id == anomaly_id, Anomaly.site_id == site_id)
            ).scalars().first()
            
            if anomaly:
                anomaly.is_acknowledged = True
                session.commit()
                # Return the updated row (or a success badge to swap)
                return HttpResponse('<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-500">Acknowledged</span>')
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"acknowledge_anomaly error: {e}", exc_info=True)
    return HttpResponse('Error', status=500)


def _get_page_keywords(site_id: str, url: str, curr_start: date, curr_end: date) -> list[dict]:
    """Query keywords that rank for a specific page."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("avg_position"),
                    func.sum(KeywordRanking.clicks).label("clicks"),
                    func.sum(KeywordRanking.impressions).label("impressions"),
                )
                .where(
                    KeywordRanking.site_id == site_id,
                    KeywordRanking.landing_page == url,
                    KeywordRanking.date >= curr_start,
                    KeywordRanking.date <= curr_end
                )
                .group_by(KeywordRanking.keyword)
                .order_by(func.sum(KeywordRanking.clicks).desc())
                .limit(50)
            ).all()

            return [
                {
                    "keyword": row.keyword,
                    "position": f"{row.avg_position:.0f}" if row.avg_position else "—",
                    "clicks": f"{row.clicks:,.0f}",
                    "impressions": f"{row.impressions:,.0f}",
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_page_keywords error: {e}", exc_info=True)
        return []


@role_required("seo")
def page_detail(request):
    """HTMX modal content: keywords driving traffic to a specific page."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    url = request.GET.get("url")
    if not url:
        return HttpResponse("No URL provided.", status=400)

    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)
    keywords = _get_page_keywords(site_id, url, curr_start, curr_end)

    context = {
        "url": url,
        "url_short": url.replace("https://", "").replace("http://", "").rstrip("/"),
        "keywords": keywords,
    }
    return render(request, "dashboard/partials/_page_keywords.html", context)


def settings(request):
    """Settings page — site selection, connected APIs, user preferences."""
    from apps.sync.models import SyncLog

    site_id = request.session.get("selected_site_url") or get_default_site_id()

    try:
        with get_session() as session:
            from pipeline.db.schema import Site
            site_obj = session.execute(
                select(Site).where(Site.site_url == site_id).limit(1)
            ).scalars().first()
            site_name = site_obj.site_name if site_obj else site_id
            site_gsc_property = site_obj.gsc_property if site_obj else site_id
            site_ga4_property_id = site_obj.ga4_property_id if site_obj else ""
            site_dataforseo_domain = site_obj.dataforseo_target_domain if site_obj else ""
            site_db_id = site_obj.id if site_obj else None
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        site_name = site_id
        site_gsc_property = site_id
        site_ga4_property_id = ""
        site_dataforseo_domain = ""
        site_db_id = None

    # Get all sync logs for the site to show connector status
    sync_logs = SyncLog.objects.filter(site_url=site_id).order_by('-last_synced')

    # Group by connector status
    working = sync_logs.filter(status='success')
    errored = sync_logs.filter(status='error')
    never_run = sync_logs.filter(status='never')

    # Tracked competitors (editable grid columns) + auto-discovered suggestions.
    try:
        from pipeline.services.competitor_service import (
            get_tracked_competitors, get_discovered_competitors, is_overridden,
        )
        tracked_competitors = get_tracked_competitors(site_id)
        discovered_competitors = get_discovered_competitors(site_id)
        competitors_overridden = is_overridden(site_id)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"settings competitors error: {e}", exc_info=True)
        tracked_competitors, discovered_competitors, competitors_overridden = [], [], False

    context = {
        "active": "settings",
        "site_id": site_id,
        "site_name": site_name,
        "site_db_id": site_db_id,
        "site_gsc_property": site_gsc_property,
        "site_ga4_property_id": site_ga4_property_id,
        "site_dataforseo_domain": site_dataforseo_domain,
        "working_connectors": working,
        "errored_connectors": errored,
        "never_run_connectors": never_run,
        "tracked_competitors": tracked_competitors,
        "discovered_competitors": discovered_competitors,
        "competitors_overridden": competitors_overridden,
    }
    return render(request, "dashboard/settings.html", context)


@require_POST
def set_competitors(request):
    """Save the site's tracked competitor list (grid columns). Empty = revert to auto-seed."""
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    from pipeline.services.competitor_service import set_tracked_competitors

    site_id = request.session.get("selected_site_url") or get_default_site_id()
    raw = request.POST.get("competitors", "")
    # Accept newline- or comma-separated domains.
    domains = [d.strip() for d in raw.replace(",", "\n").splitlines() if d.strip()]
    try:
        set_tracked_competitors(site_id, domains)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"set_competitors error: {e}", exc_info=True)

    return HttpResponseRedirect(reverse("dashboard:settings"))


def set_period(request):
    """Set the global period context in the session."""
    from django.http import HttpResponseRedirect
    from django.urls import reverse

    mode = request.GET.get('mode', 'monthly')
    if mode in ['daily', 'weekly', 'monthly', 'custom']:
        request.session['period_mode'] = mode

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return HttpResponseRedirect(reverse('dashboard:overview'))


def set_site(request):
    """Set the globally-selected website in the session, then return to the
    page the user came from. Accepts the site_url via GET or POST. Validates
    against the active site registry so a stale/invalid value can't be stored."""
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    from pipeline.services.site_service import get_active_site_ids

    site_url = (request.POST.get("site_url") or request.GET.get("site_url") or "").strip()
    if site_url and site_url in get_active_site_ids():
        request.session["selected_site_url"] = site_url

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return HttpResponseRedirect(referer)
    return HttpResponseRedirect(reverse("dashboard:overview"))

def add_site(request):
    """Add a new website to track."""
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    from pipeline.services.site_service import add_site as service_add_site
    import logging
    _log = logging.getLogger(__name__)

    if request.method == "POST":
        site_url = request.POST.get("site_url", "").strip()
        site_name = request.POST.get("site_name", "").strip() or site_url
        if site_url:
            try:
                service_add_site(site_url=site_url, site_name=site_name)
                _log.info(f"[add_site] Added new site: {site_url}")
            except ValueError as e:
                # Site already exists — still activate it in the session so
                # the user ends up on the correct domain instead of staying
                # on the old one with no feedback.
                _log.warning(f"[add_site] {e} — activating existing site in session")
            except Exception as e:
                _log.error(f"[add_site] Unexpected error adding site {site_url!r}: {e}", exc_info=True)
            finally:
                # Always switch the session to the requested site if it exists
                # in the registry (handles both new-add and already-exists).
                from pipeline.services.site_service import get_active_site_ids
                if site_url and site_url in get_active_site_ids():
                    request.session["selected_site_url"] = site_url

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return HttpResponseRedirect(referer)
    return HttpResponseRedirect(reverse("dashboard:settings"))


@require_POST
def update_site_credentials(request):
    """Update the GSC property, GA4 property ID, and DataForSEO domain for the active site.
    Called from the Site Credentials form in Settings. Allows correcting the auto-filled
    gsc_property (e.g. changing 'eventstaff.com' → 'sc-domain:eventstaff.com')."""
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    from pipeline.services.site_service import update_site
    import logging
    _log = logging.getLogger(__name__)

    site_db_id = request.POST.get("site_db_id", "").strip()
    gsc_property = request.POST.get("gsc_property", "").strip()
    ga4_property_id = request.POST.get("ga4_property_id", "").strip() or None
    dataforseo_target_domain = request.POST.get("dataforseo_target_domain", "").strip() or None

    if site_db_id:
        try:
            update_site(
                int(site_db_id),
                gsc_property=gsc_property or None,
                ga4_property_id=ga4_property_id,
                dataforseo_target_domain=dataforseo_target_domain,
            )
            _log.info(f"[update_site_credentials] Updated site #{site_db_id}: gsc={gsc_property!r} ga4={ga4_property_id!r}")
        except Exception as e:
            _log.error(f"[update_site_credentials] Failed to update site #{site_db_id}: {e}", exc_info=True)

    return HttpResponseRedirect(reverse("dashboard:settings"))


from django.http import HttpResponse

@role_required("seo")
def export_csv(request, table_name):
    """Generic CSV export for all data tables."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)
    
    data = []
    try:
        if table_name == "top_pages":
            top_pages_raw = query_top_pages_raw(site_id, curr_start, curr_end)
            data = [
                {"page": p["page"], "clicks": f"{p['clicks']:,}", "impressions": f"{p['impressions']:,}", "ctr": f"{p['ctr']:.1f}%"}
                for p in top_pages_raw
            ]
        elif table_name == "keywords":
            data = _get_keywords_overview(site_id, limit=5000)
        elif table_name == "seo_country":
            country_raw = query_seo_by_dimension_raw(site_id, curr_start, curr_end)["by_country"]
            data = [
                {"country": r["country"], "clicks": f"{r['clicks']:,.0f}", "impressions": f"{r['impressions']:,.0f}",
                 "ctr": f"{r['ctr']:.2f}%", "position": f"{r['avg_position']:.1f}"}
                for r in country_raw
            ]
        elif table_name == "backlinks":
            data = query_backlinks_table_raw(site_id, limit=5000)
        elif table_name == "anomalies":
            data = _get_all_anomalies(site_id, limit=5000)
        elif table_name == "page_speed":
            data = _get_page_speed_issues(site_id, limit=5000)
        elif table_name == "indexing":
            data = _get_indexing_issues(site_id, limit=5000)
        elif table_name == "technical_issues":
            data = _get_technical_issues(site_id, limit=5000)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"export_csv error: {e}", exc_info=True)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="fusehealth_{table_name}_{site_id}_{curr_end}.csv"'
    
    if data:
        writer = csv.DictWriter(response, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    else:
        writer = csv.writer(response)
        writer.writerow(["No data available"])
        
    return response
