"""Overview page data — raw calculators (shared by the old Django view and the new
DRF API view) plus the old view's presentation formatters. Query logic lives here
exactly once; each caller formats it however its output needs (see
docs/superpowers/specs/2026-07-10-limitless-migration-roadmap-and-phaseA-design.md §2.2)."""

from datetime import date

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
