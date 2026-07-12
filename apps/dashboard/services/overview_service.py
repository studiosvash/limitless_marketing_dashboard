"""Overview page data — raw calculators (shared by the old Django view and the new
DRF API view) plus the old view's presentation formatters. Query logic lives here
exactly once; each caller formats it however its output needs (see
docs/superpowers/specs/2026-07-10-limitless-migration-roadmap-and-phaseA-design.md §2.2)."""

from datetime import date, timedelta

from sqlalchemy import func, select

from pipeline.db.schema import SEODaily, AISummary
from pipeline.utils.db_connection import get_session


def get_kpi_raw(site_id: str, curr_start: date, curr_end: date,
                 prev_start: date, prev_end: date) -> tuple[dict, dict]:
    """Raw current/previous period stats: clicks, impressions, ctr, avg_position."""
    try:
        with get_session() as session:
            def get_stats(start, end):
                row = session.execute(
                    select(
                        func.sum(SEODaily.clicks).label("clicks"),
                        func.sum(SEODaily.impressions).label("impressions"),
                        func.avg(SEODaily.ctr).label("ctr"),
                        func.avg(SEODaily.avg_position).label("avg_position"),
                    )
                    .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
                ).first()
                return {
                    "clicks": row.clicks or 0,
                    "impressions": row.impressions or 0,
                    "ctr": row.ctr or 0.0,
                    "avg_position": row.avg_position or 0.0,
                }
            return get_stats(curr_start, curr_end), get_stats(prev_start, prev_end)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return {}, {}


def format_kpi_cards(current: dict, previous: dict) -> list[dict]:
    """Old dashboard/overview.html template shape: pre-formatted display strings."""
    def calc_delta(curr_val, prev_val):
        if not prev_val:
            return "0%", "neutral"
        delta_pct = ((curr_val - prev_val) / prev_val) * 100
        direction = "up" if delta_pct > 0 else "down" if delta_pct < 0 else "neutral"
        return f"{abs(delta_pct):.1f}%", direction

    def calc_delta_inv(curr_val, prev_val):
        if not prev_val:
            return "0%", "neutral"
        delta_pct = ((curr_val - prev_val) / prev_val) * 100
        direction = "up" if delta_pct < 0 else "down" if delta_pct > 0 else "neutral"
        return f"{abs(delta_pct):.1f}%", direction

    # .get(..., 0) defaults: current/previous can be {} when get_kpi_raw hit a DB
    # error and returned its safe fallback — must not KeyError in that case.
    clicks_delta, clicks_dir = calc_delta(current.get("clicks", 0), previous.get("clicks", 0))
    impr_delta, impr_dir = calc_delta(current.get("impressions", 0), previous.get("impressions", 0))
    ctr_delta, ctr_dir = calc_delta(current.get("ctr", 0.0), previous.get("ctr", 0.0))
    pos_delta, pos_dir = calc_delta_inv(current.get("avg_position", 0.0), previous.get("avg_position", 0.0))

    return [
        {"label": "Clicks", "value": f"{int(current.get('clicks', 0)):,}", "delta": clicks_delta, "delta_dir": clicks_dir},
        {"label": "Impressions", "value": f"{int(current.get('impressions', 0)):,}", "delta": impr_delta, "delta_dir": impr_dir},
        {"label": "Avg. CTR", "value": f"{(current.get('ctr', 0.0) * 100):.2f}%", "delta": ctr_delta, "delta_dir": ctr_dir},
        {"label": "Avg. Position", "value": f"{current.get('avg_position', 0.0):.1f}", "delta": pos_delta, "delta_dir": pos_dir},
    ]


def query_top_pages_raw(site_id: str, start_date: date, end_date: date, limit: int = 10) -> list[dict]:
    """Raw numeric top pages by clicks. Key is `page` (matches the old template's
    variable name); Task 7 renames it to `url` for the API shape."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page,
                    func.sum(SEODaily.clicks).label("total_clicks"),
                    func.sum(SEODaily.impressions).label("total_impressions"),
                    func.avg(SEODaily.ctr).label("avg_ctr"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date,
                       SEODaily.landing_page.isnot(None))
                .group_by(SEODaily.landing_page)
                .order_by(func.sum(SEODaily.clicks).desc())
                .limit(limit)
            ).all()
            return [
                {
                    "page": row.landing_page or "/",
                    "clicks": int(row.total_clicks or 0),
                    "impressions": int(row.total_impressions or 0),
                    "ctr": round((row.avg_ctr or 0) * 100, 1),
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def query_daily_traffic_raw(site_id: str, start_date: date, end_date: date) -> list[dict]:
    """Raw [{date, clicks, impressions}] points — the API `trend[]` shape and also the
    source data for the old view's Plotly chart dict."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.date,
                    func.sum(SEODaily.clicks).label("total_clicks"),
                    func.sum(SEODaily.impressions).label("total_impressions"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date)
                .group_by(SEODaily.date)
                .order_by(SEODaily.date.asc())
            ).all()
            return [
                {"date": str(r.date), "clicks": int(r.total_clicks or 0), "impressions": int(r.total_impressions or 0)}
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def build_traffic_chart(points: list[dict]) -> dict | None:
    """Old view's Plotly chart spec, built from query_daily_traffic_raw's output."""
    if not points:
        return None
    dates = [p["date"] for p in points]
    clicks = [p["clicks"] for p in points]
    impressions = [p["impressions"] for p in points]
    return {
        "data": [
            {"x": dates, "y": clicks, "name": "Clicks", "type": "scatter", "mode": "lines",
             "line": {"color": "#4f46e5", "width": 3, "shape": "spline"},
             "fill": "tozeroy", "fillcolor": "rgba(79,70,229,0.08)"},
            {"x": dates, "y": impressions, "name": "Impressions", "type": "scatter", "mode": "lines",
             "yaxis": "y2", "line": {"color": "#94a3b8", "width": 2, "dash": "dot", "shape": "spline"}},
        ],
        "layout": {
            "font": {"family": "Inter", "size": 12, "color": "#64748b"},
            "paper_bgcolor": "white", "plot_bgcolor": "white",
            "margin": {"l": 40, "r": 40, "t": 10, "b": 30},
            "xaxis": {"showgrid": False},
            "yaxis": {"gridcolor": "#f1f5f9", "zeroline": False},
            "yaxis2": {"overlaying": "y", "side": "right", "showgrid": False},
            "legend": {"orientation": "h", "y": 1.15, "x": 0},
            "hovermode": "x unified",
        },
        "config": {"displayModeBar": False, "responsive": True},
    }


def get_ai_summary_text(site_id: str) -> str | None:
    try:
        with get_session() as session:
            row = (
                session.execute(
                    select(AISummary).where(AISummary.site_id == site_id)
                    .order_by(AISummary.week_start.desc()).limit(1)
                ).scalars().first()
            )
            return row.summary_text if row and row.summary_text else None
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return None


def parse_ai_summary(text: str) -> list[dict]:
    """Turn the markdown AI summary into structured, styled sections (critical/win/info)."""
    import re
    from django.utils.html import escape, mark_safe

    if not text:
        return []

    def render_inline(s: str):
        s = escape(s.strip())
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return mark_safe(s)

    def classify(title: str) -> str:
        t = title.lower()
        if "🔴" in title or "critical" in t or "issue" in t or "fix" in t:
            return "critical"
        if "🟢" in title or "win" in t or "maintain" in t or "strength" in t:
            return "win"
        return "info"

    sections, current = [], None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        heading = re.match(r"^#{1,4}\s+(.*)$", line)
        if heading:
            title = heading.group(1).strip()
            current = {"kind": classify(title), "title": title, "items": [], "prose": []}
            sections.append(current)
            continue
        if current is None:
            current = {"kind": "info", "title": "Summary", "items": [], "prose": []}
            sections.append(current)
        item = re.match(r"^\s*(?:\d+\.|[-*])\s+(.*)$", line)
        if item:
            current["items"].append(render_inline(item.group(1)))
        else:
            current["prose"].append(render_inline(line))
    return sections


def range_to_period_dates(range_key: str, anchor: date) -> tuple[date, date, date, date]:
    """Maps the API's stateless `range` query param (7d/30d/90d) to
    (curr_start, curr_end, prev_start, prev_end), anchored to the latest data date.
    Unlike the old view, this never reads/writes Django session state — the API is
    stateless per HANDOFF_SPEC.md's caching model (cache key includes `range`)."""
    from pipeline.utils.period_utils import get_period_dates

    if range_key == "7d":
        return get_period_dates("weekly", 0, anchor=anchor)
    if range_key == "90d":
        custom_end = anchor - timedelta(days=1)
        custom_start = custom_end - timedelta(days=89)
        return get_period_dates("custom", 0, custom_start=custom_start, custom_end=custom_end, anchor=anchor)
    return get_period_dates("monthly", 0, anchor=anchor)  # "30d" and any unrecognized value


def build_kpis_api(current: dict, previous: dict) -> list[dict]:
    """HANDOFF_SPEC.md §2.1 kpi shape: [{label, value, delta, unit}], numeric — not the old
    view's pre-formatted display strings (see format_kpi_cards for that)."""
    from pipeline.utils.period_utils import compute_delta

    # .get(..., default) fallbacks: current/previous can be {} when get_kpi_raw hit a DB
    # error and returned its safe fallback (see format_kpi_cards for the same pattern) —
    # must not KeyError in that case.
    clicks_delta = compute_delta(current.get("clicks", 0), previous.get("clicks", 0))
    impr_delta = compute_delta(current.get("impressions", 0), previous.get("impressions", 0))
    ctr_delta = compute_delta(current.get("ctr", 0.0) * 100, previous.get("ctr", 0.0) * 100)
    # Avg position: lower is better, so "improvement" delta is (previous - current).
    pos_delta_val = round((previous.get("avg_position", 0.0) or 0) - (current.get("avg_position", 0.0) or 0), 1)

    return [
        {"label": "Total clicks", "value": int(current.get("clicks", 0)), "delta": clicks_delta["pct_change"], "unit": "%"},
        {"label": "Impressions", "value": int(current.get("impressions", 0)), "delta": impr_delta["pct_change"], "unit": "%"},
        {"label": "Avg. CTR", "value": round(current.get("ctr", 0.0) * 100, 2), "delta": ctr_delta["pct_change"], "unit": "%"},
        {"label": "Avg. position", "value": round(current.get("avg_position", 0.0), 1), "delta": pos_delta_val, "unit": "pos"},
    ]


def build_top_pages_api(site_id: str, start_date: date, end_date: date, limit: int = 6) -> list[dict]:
    """HANDOFF_SPEC.md overview `topPages[≤6]` shape: [{url, clicks, impressions, ctr}]."""
    raw = query_top_pages_raw(site_id, start_date, end_date, limit=limit)
    return [{"url": p["page"], "clicks": p["clicks"], "impressions": p["impressions"], "ctr": p["ctr"]} for p in raw]


def build_pillars(site_id: str, kpis_current: dict, kpis_previous: dict, top3_count: int) -> list[dict]:
    """HANDOFF_SPEC.md §2.2 pillar shape. Site health / Paid ROAS / AI visibility report
    state='setup' — Site Audit, Ads, and AI Optimization aren't built yet (Phases C/D)."""
    # .get(..., default) fallbacks: kpis_current/kpis_previous can be {} when get_kpi_raw hit
    # a DB error and returned its safe fallback (see format_kpi_cards for the same pattern) —
    # must not KeyError in that case.
    current_clicks = kpis_current.get("clicks", 0)
    previous_clicks = kpis_previous.get("clicks", 0)
    clicks_delta = round(
        ((current_clicks - previous_clicks) / previous_clicks * 100)
        if previous_clicks else 0, 1,
    )
    return [
        {"label": "Organic clicks", "target": "overview", "valueKind": "num",
         "value": int(current_clicks), "delta": clicks_delta, "deltaUnit": "%",
         "sub": f"clicks", "state": "ok"},
        {"label": "Avg. position", "target": "positioning", "valueKind": "pos",
         "value": round(kpis_current.get("avg_position", 0.0), 1), "delta": None, "deltaUnit": "pos",
         "sub": f"{top3_count} keywords in top 3", "state": "ok"},
        {"label": "Site health", "target": "pages", "valueKind": "score",
         "value": None, "delta": None, "deltaUnit": "pts", "sub": "Site Audit not set up yet",
         "state": "setup"},
        {"label": "Paid ROAS", "target": "ads", "valueKind": "roas",
         "value": None, "delta": None, "deltaUnit": None, "sub": "Ads not connected yet",
         "state": "setup"},
        {"label": "AI visibility", "target": "ai", "valueKind": "pct",
         "value": None, "delta": None, "deltaUnit": "pts", "sub": "not set up yet",
         "state": "setup"},
    ]


def build_modules(seo_module_stat: str, keywords_count: int, top3_count: int,
                   avg_position: float) -> list[dict]:
    """HANDOFF_SPEC.md §2.2 module-status card shape."""
    return [
        {"label": "SEO Performance", "target": "seo", "stat": seo_module_stat, "sub": "",
         "tone": "ok"},
        {"label": "Keywords", "target": "keywords", "stat": f"{keywords_count} tracked",
         "sub": f"{top3_count} in top 3", "tone": "ok"},
        {"label": "Position Tracking", "target": "positioning", "stat": f"#{avg_position:.1f} avg",
         "sub": "", "tone": "ok"},
        {"label": "Backlinks", "target": "backlinks", "stat": "Not connected", "sub": "",
         "tone": "setup"},
        {"label": "Site Audit", "target": "pages", "stat": "Not set up", "sub": "",
         "tone": "setup"},
        {"label": "AI Optimization", "target": "ai", "stat": "Not set up",
         "sub": "Track ChatGPT, Claude, Gemini", "tone": "setup"},
        {"label": "Paid Media", "target": "ads", "stat": "Not connected", "sub": "",
         "tone": "setup"},
    ]


_KIND_MODULE_MAP = {
    # Must match the approved SPA's own kindMap exactly
    # (Limitless marketing dashboard2/app/api.js:141-145) — its labels are used as
    # lookup keys into a hardcoded color map (`modColor` in the .dc.html source), so
    # any label that doesn't match falls back to gray instead of the designed color.
    "anomaly": {"label": "SEO", "target": "seo"},
    "ranking": {"label": "Positions", "target": "positioning"},
    "backlink": {"label": "Backlinks", "target": "backlinks"},
    "technical": {"label": "Site Audit", "target": "pages"},
    "ads": {"label": "Ads", "target": "ads"},
    "system": {"label": "System", "target": "alerts"},
}


def build_priority_feed(feed: list[dict], limit: int = 6) -> list[dict]:
    """HANDOFF_SPEC.md overview `priority[≤6]` — unacknowledged alerts, severity-sorted,
    each tagged with its owning module. `feed` is apps.dashboard.services.alerts_service
    .build_alerts_response(...)['feed'] — the caller (ProjectOverviewView) passes it in
    rather than this module importing alerts_service directly, keeping overview_service
    free of a hard dependency on a sibling page's service module."""
    severity_rank = {"high": 0, "medium": 1, "info": 2, "low": 3}
    unacked = [item for item in feed if not item["acknowledged"]]
    # Matches the SPA's sort exactly (app/api.js, right after kindMap):
    #   .sort((a, b) => (sevRank[a.severity] - sevRank[b.severity]) || (a.ts < b.ts ? 1 : -1))
    # i.e. severity ascending (high first), and within the same severity, newest ts first.
    # Two stable passes: sort by ts descending first, then by severity ascending — the
    # second pass preserves the ts-descending order for items that tie on severity.
    unacked.sort(key=lambda item: item["ts"], reverse=True)
    unacked.sort(key=lambda item: severity_rank.get(item["severity"], 9))

    out = []
    for item in unacked[:limit]:
        module = _KIND_MODULE_MAP.get(item["kind"], {"label": "General", "target": "alerts"})
        out.append({**item, "module": module})
    return out


def build_summary_lists(ai_summary_sections: list[dict]) -> dict:
    """HANDOFF_SPEC.md summary{wins, critical, watch} — flattens the parsed AI summary
    sections (see parse_ai_summary) into complete-sentence string lists per kind."""
    out = {"wins": [], "critical": [], "watch": []}
    kind_to_key = {"win": "wins", "critical": "critical", "info": "watch"}
    for section in ai_summary_sections:
        key = kind_to_key.get(section["kind"], "watch")
        for item in section["items"]:
            out[key].append(str(item))
        for para in section["prose"]:
            out[key].append(str(para))
    return out
