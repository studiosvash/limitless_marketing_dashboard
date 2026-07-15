"""Overview page data -- raw calculators (shared by the old Django view and the new
DRF API view) plus the old view's presentation formatters. Query logic lives here
exactly once; each caller formats it however its output needs (see
docs/superpowers/specs/2026-07-10-limitless-migration-roadmap-and-phaseA-design.md 2.2)."""

from datetime import date, timedelta

from sqlalchemy import func, select

from pipeline.db.schema import (
    SEODaily, AISummary, Anomaly, TechnicalIssue, IndexingStatus, PageSpeed,
)
from pipeline.utils.db_connection import get_session


# Severity rank for sorting the Intelligence (priority) feed: high first.
_SEV_RANK = {"high": 0, "medium": 1, "info": 2}


def get_kpi_raw(site_id: str, curr_start: date, curr_end: date,
                 prev_start: date, prev_end: date) -> tuple[dict, dict]:
    """Raw current/previous period stats: clicks, impressions, ctr, avg_position."""
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

    clicks_delta, clicks_dir = calc_delta(current["clicks"], previous["clicks"])
    impr_delta, impr_dir = calc_delta(current["impressions"], previous["impressions"])
    ctr_delta, ctr_dir = calc_delta(current["ctr"], previous["ctr"])
    pos_delta, pos_dir = calc_delta_inv(current["avg_position"], previous["avg_position"])

    return [
        {"label": "Clicks", "value": f"{int(current['clicks']):,}", "delta": clicks_delta, "delta_dir": clicks_dir},
        {"label": "Impressions", "value": f"{int(current['impressions']):,}", "delta": impr_delta, "delta_dir": impr_dir},
        {"label": "Avg. CTR", "value": f"{(current['ctr'] * 100):.2f}%", "delta": ctr_delta, "delta_dir": ctr_dir},
        {"label": "Avg. Position", "value": f"{current['avg_position']:.1f}", "delta": pos_delta, "delta_dir": pos_dir},
    ]


def query_top_pages_raw(site_id: str, start_date: date, end_date: date, limit: int = 10) -> list[dict]:
    """Raw numeric top pages by clicks. Key is `page` (matches the old template's
    variable name); Task 7 renames it to `url` for the API shape."""
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


def query_daily_traffic_raw(site_id: str, start_date: date, end_date: date) -> list[dict]:
    """Raw [{date, clicks, impressions}] points -- the API `trend[]` shape and also the
    source data for the old view's Plotly chart dict."""
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


def range_to_period_dates(range_key: str, anchor: date) -> tuple[date, date, date, date]:
    """Maps the API's stateless `range` query param (7d/30d/90d) to
    (curr_start, curr_end, prev_start, prev_end), anchored to the latest data date.
    Unlike the old view, this never reads/writes Django session state -- the API is
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
    """HANDOFF_SPEC.md 2.1 kpi shape: [{label, value, delta, unit}], numeric -- not the old
    view's pre-formatted display strings (see format_kpi_cards for that)."""
    from pipeline.utils.period_utils import compute_delta

    clicks_delta = compute_delta(current["clicks"], previous["clicks"])
    impr_delta = compute_delta(current["impressions"], previous["impressions"])
    ctr_delta = compute_delta(current["ctr"] * 100, previous["ctr"] * 100)
    # Avg position: lower is better, so "improvement" delta is (previous - current).
    pos_delta_val = round((previous["avg_position"] or 0) - (current["avg_position"] or 0), 1)

    return [
        {"label": "Total clicks", "value": int(current["clicks"]), "delta": clicks_delta["pct_change"], "unit": "%"},
        {"label": "Impressions", "value": int(current["impressions"]), "delta": impr_delta["pct_change"], "unit": "%"},
        {"label": "Avg. CTR", "value": round(current["ctr"] * 100, 2), "delta": ctr_delta["pct_change"], "unit": "%"},
        {"label": "Avg. position", "value": round(current["avg_position"], 1), "delta": pos_delta_val, "unit": "pos"},
    ]


def build_top_pages_api(site_id: str, start_date: date, end_date: date, limit: int = 6) -> list[dict]:
    """HANDOFF_SPEC.md overview `topPages[<=6]` shape: [{url, clicks, impressions, ctr}]."""
    raw = query_top_pages_raw(site_id, start_date, end_date, limit=limit)
    return [{"url": p["page"], "clicks": p["clicks"], "impressions": p["impressions"], "ctr": p["ctr"]} for p in raw]


# --- E1: Site health (real data, not "setup") -------------------------------------
def compute_site_health(site_id: str, curr_start: date, curr_end: date) -> dict | None:
    """Composite site-health score from data we already have: GSC page coverage +
    indexing status (+ PageSpeed when present). Returns None when we have no page-level
    data at all -- the pillar then honestly reports state='setup' (no fake number).

    Resilient by construction: the `pagespeed` table may not exist yet (never synced),
    so that query is wrapped -- a missing table just means the speed component is skipped,
    it never turns the whole pillar into an error.
    """
    with get_session() as session:
        traffic_rows = session.execute(
            select(
                SEODaily.landing_page,
                func.sum(SEODaily.clicks).label("clicks"),
            )
            .where(SEODaily.site_id == site_id, SEODaily.date >= curr_start,
                   SEODaily.date <= curr_end, SEODaily.landing_page.isnot(None))
            .group_by(SEODaily.landing_page)
        ).all()

        try:
            index_rows = session.execute(
                select(IndexingStatus.verdict).where(IndexingStatus.site_id == site_id)
            ).all()
        except Exception:
            index_rows = []

        try:
            speed_rows = session.execute(
                select(PageSpeed.performance_score)
                .where(PageSpeed.site_id == site_id, PageSpeed.strategy == "mobile")
            ).all()
        except Exception:
            speed_rows = []

    total_pages = len(traffic_rows)
    has_indexing = len(index_rows) > 0
    speed_vals = [r.performance_score for r in speed_rows if r.performance_score is not None]
    has_speed = len(speed_vals) > 0

    if total_pages == 0 and not has_indexing:
        return None  # nothing to score -> "setup"

    scores = []
    if total_pages:
        pct_with_clicks = sum(1 for r in traffic_rows if (r.clicks or 0) > 0) / total_pages * 100
        scores.append(min(100.0, pct_with_clicks))
    if has_speed:
        scores.append(sum(speed_vals) / len(speed_vals))
    if has_indexing:
        indexed = sum(1 for r in index_rows if r.verdict == "PASS")
        scores.append(indexed / len(index_rows) * 100)

    score = int(sum(scores) / len(scores)) if scores else 0
    not_indexed = sum(1 for r in index_rows if r.verdict and r.verdict != "PASS")

    return {
        "score": score,
        "issues": not_indexed,
        "total_pages": total_pages,
        "has_speed": has_speed,
        "has_indexing": has_indexing,
    }


def _tone_for_score(score: int) -> str:
    return "ok" if score >= 70 else "warn" if score >= 40 else "bad"


def build_pillars(kpis_current: dict, kpis_previous: dict, top3_count: int,
                  site_health: dict | None) -> list[dict]:
    """HANDOFF_SPEC.md 2.2 pillar shape (5 cards).

    Site health is now REAL (E1) -- populated from compute_site_health when page data
    exists, else state='setup'. Paid ROAS and AI visibility stay 'setup': Ads and the
    DataForSEO AI Optimization surface are genuinely not connected yet (no fake data)."""
    clicks_delta = round(
        ((kpis_current["clicks"] - kpis_previous["clicks"]) / kpis_previous["clicks"] * 100)
        if kpis_previous["clicks"] else 0, 1,
    )

    if site_health is not None:
        sh_pillar = {
            "label": "Site health", "target": "pages", "valueKind": "score",
            "value": site_health["score"], "delta": None, "deltaUnit": "pts",
            "sub": (f"{site_health['issues']} to fix" if site_health["issues"]
                    else "no indexing issues"),
            "state": "ok",
        }
    else:
        sh_pillar = {
            "label": "Site health", "target": "pages", "valueKind": "score",
            "value": None, "delta": None, "deltaUnit": "pts",
            "sub": "Site Audit not set up yet", "state": "setup",
        }

    return [
        {"label": "Organic clicks", "target": "overview", "valueKind": "num",
         "value": int(kpis_current["clicks"]), "delta": clicks_delta, "deltaUnit": "%",
         "sub": "clicks", "state": "ok"},
        {"label": "Avg. position", "target": "positioning", "valueKind": "pos",
         "value": round(kpis_current["avg_position"], 1), "delta": None, "deltaUnit": "pos",
         "sub": f"{top3_count} keywords in top 3", "state": "ok"},
        sh_pillar,
        {"label": "Paid ROAS", "target": "ads", "valueKind": "roas",
         "value": None, "delta": None, "deltaUnit": None, "sub": "Ads not connected yet",
         "state": "setup"},
        {"label": "AI visibility", "target": "ai", "valueKind": "pct",
         "value": None, "delta": None, "deltaUnit": "pts", "sub": "not set up yet",
         "state": "setup"},
    ]


def build_modules(seo_module_stat: str, keywords_count: int, top3_count: int,
                  avg_position: float, site_health: dict | None) -> list[dict]:
    """HANDOFF_SPEC.md 2.2 module-status card shape (7 cards). The Site Audit module now
    reflects the real page-health score (E1) when we have data; Backlinks / AI / Paid Media
    stay 'setup' until their integrations land."""
    if site_health is not None:
        site_audit_card = {
            "label": "Site Audit", "target": "pages",
            "stat": f"{site_health['score']}/100",
            "sub": (f"{site_health['issues']} issues to fix" if site_health["issues"]
                    else f"{site_health['total_pages']} pages healthy"),
            "tone": _tone_for_score(site_health["score"]),
        }
    else:
        site_audit_card = {"label": "Site Audit", "target": "pages", "stat": "Not set up",
                           "sub": "", "tone": "setup"}

    return [
        {"label": "SEO Performance", "target": "seo", "stat": seo_module_stat, "sub": "",
         "tone": "ok"},
        {"label": "Keywords", "target": "keywords", "stat": f"{keywords_count} tracked",
         "sub": f"{top3_count} in top 3", "tone": "ok"},
        {"label": "Position Tracking", "target": "positioning", "stat": f"#{avg_position:.1f} avg",
         "sub": "", "tone": "ok"},
        {"label": "Backlinks", "target": "backlinks", "stat": "Not connected", "sub": "",
         "tone": "setup"},
        site_audit_card,
        {"label": "AI Optimization", "target": "ai", "stat": "Not set up",
         "sub": "Track ChatGPT, Claude, Gemini", "tone": "setup"},
        {"label": "Paid Media", "target": "ads", "stat": "Not connected", "sub": "",
         "tone": "setup"},
    ]


# --- E2: Cross-module Intelligence (priority) feed ---------------------------------
def build_priority_feed(site_id: str, curr_start: date, curr_end: date,
                        signals: list[dict], limit: int = 6) -> list[dict]:
    """Unacknowledged alerts across EVERY module (not just Site Audit), severity-sorted,
    each tagged with its owning module for the colored chip + click-through.

    Sources (all DB-only, all pre-existing tables):
      - Anomaly            -> SEO           (metric spikes/drops)
      - TechnicalIssue     -> Site Audit    (404s, redirects, long URLs)
      - IndexingStatus     -> Site Audit    (pages not indexed)
      - decision signals   -> SEO / Ads     (negative + opportunity signals)
    """
    items: list[dict] = []
    _anom_labels = {
        "seo_clicks": "Clicks", "seo_impressions": "Impressions", "seo_ctr": "CTR",
        "seo_avg_position": "Avg. position", "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
        "ad_impressions": "Ad impressions", "ad_conversions": "Conversions",
    }
    _issue_labels = {
        "not_found_404": "404 - Not found", "crawled_not_indexed": "Crawled, not indexed",
        "page_with_redirect": "Redirect", "long_url": "Long URL",
    }

    with get_session() as session:
        # 1. SEO anomalies (unacknowledged)
        try:
            anomalies = session.execute(
                select(Anomaly)
                .where(Anomaly.site_id == site_id, Anomaly.is_acknowledged == 0)
                .order_by(Anomaly.date.desc())
                .limit(20)
            ).scalars().all()
        except Exception:
            anomalies = []
        for a in anomalies:
            up = (a.actual_value or 0) >= (a.baseline_value or 0)
            metric = _anom_labels.get(a.metric_type, a.metric_type)
            items.append({
                "id": f"anomaly-{a.id}",
                "severity": a.severity or "medium",
                "kind": "anomaly",
                "title": f"{metric} {'spike' if up else 'drop'} "
                         f"({'+' if up else '-'}{abs(a.deviation_pct or 0):.0f}%)",
                "detail": f"{metric} was {a.actual_value:,.0f} vs. a baseline of "
                          f"{a.baseline_value:,.0f} on {a.date}.",
                "ts": str(a.date),
                "module": {"label": "SEO", "target": "seo"},
            })

        # 2. Technical issues (Site Audit)
        try:
            issues = session.execute(
                select(TechnicalIssue)
                .where(TechnicalIssue.site_id == site_id)
                .order_by(TechnicalIssue.detected_at.desc())
                .limit(20)
            ).scalars().all()
        except Exception:
            issues = []
        for it in issues:
            label = _issue_labels.get(it.issue_type, (it.issue_type or "Issue").replace("_", " ").title())
            url_short = (it.url or "").split("//")[-1][:60]
            items.append({
                "id": f"tech-{it.id}",
                "severity": it.severity or "medium",
                "kind": "technical",
                "title": f"{label}: {url_short}",
                "detail": it.description or "Technical issue detected during the last crawl.",
                "ts": str(it.detected_at.date()) if it.detected_at else "",
                "module": {"label": "Site Audit", "target": "pages"},
            })

        # 3. Indexing problems (Site Audit)
        try:
            idx = session.execute(
                select(IndexingStatus)
                .where(IndexingStatus.site_id == site_id, IndexingStatus.verdict != "PASS")
                .order_by(IndexingStatus.last_crawl_time.desc())
                .limit(10)
            ).scalars().all()
        except Exception:
            idx = []
        for r in idx:
            if not r.verdict:
                continue
            url_short = (r.url or "").split("//")[-1][:60]
            items.append({
                "id": f"index-{r.id}",
                "severity": "medium",
                "kind": "technical",
                "title": f"Not indexed: {url_short}",
                "detail": f"Coverage: {r.coverage_state or 'unknown'}. This page is not in "
                          "Google's index, so it can't rank.",
                "ts": str(r.last_crawl_time.date()) if r.last_crawl_time else "",
                "module": {"label": "Site Audit", "target": "pages"},
            })

    # 4. Decision-engine signals (negative -> alerts; opportunity -> info)
    for i, s in enumerate(signals or []):
        stype = s.get("type")
        if stype == "positive":
            continue  # wins belong in the summary, not the alert feed
        is_ad = "ad" in (s.get("title", "").lower())
        items.append({
            "id": f"signal-{i}",
            "severity": "high" if stype == "negative" else "info",
            "kind": "ads" if is_ad else "anomaly",
            "title": s.get("title", "Signal"),
            "detail": s.get("detail", ""),
            "ts": str(curr_end),
            "module": {"label": "Ads", "target": "ads"} if is_ad
                      else {"label": "SEO", "target": "seo"},
        })

    items.sort(key=lambda x: _SEV_RANK.get(x["severity"], 1))
    return items[:limit]


def build_summary_lists(ai_summary_sections: list[dict]) -> dict:
    """HANDOFF_SPEC.md summary{wins, critical, watch} -- flattens the parsed AI summary
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


def get_ai_summary_text(site_id: str) -> str | None:
    with get_session() as session:
        row = (
            session.execute(
                select(AISummary).where(AISummary.site_id == site_id)
                .order_by(AISummary.week_start.desc()).limit(1)
            ).scalars().first()
        )
        return row.summary_text if row and row.summary_text else None


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
        if "\U0001f534" in title or "critical" in t or "issue" in t or "fix" in t:
            return "critical"
        if "\U0001f7e2" in title or "win" in t or "maintain" in t or "strength" in t:
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
