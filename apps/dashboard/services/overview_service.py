"""Overview page data — raw calculators (shared by the old Django view and the new
DRF API view) plus the old view's presentation formatters. Query logic lives here
exactly once; each caller formats it however its output needs (see
.claude/api-reference.md §2.2)."""

import logging
from datetime import date, timedelta

from sqlalchemy import func, select

from pipeline.db.schema import SEODaily, SEODailyTotal, AISummary, PageSpeed
from pipeline.db.writer import ensure_tables
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def query_gsc_totals(session, site_id: str, start: date, end: date) -> dict:
    """Search Console's own figures for a window, read from `seo_daily_totals`.

    Both derived metrics are recomputed across the window rather than averaged over the
    stored per-day values, because both are ratios:

      CTR      = SUM(clicks) / SUM(impressions)
      position = SUM(position x impressions) / SUM(impressions)

    A plain `AVG()` over days weights a 200-impression Sunday the same as a 15,000-impression
    Tuesday, which is what made the dashboard's CTR and average position disagree with Search
    Console even on the days it had fully synced.

    `found` is False when the window has no rows at all. Callers must not read that as a real
    zero — it means the totals have not been synced for this window yet.
    """
    ensure_tables(session, SEODailyTotal)
    row = session.execute(
        select(
            func.coalesce(func.sum(SEODailyTotal.clicks), 0),
            func.coalesce(func.sum(SEODailyTotal.impressions), 0),
            func.coalesce(func.sum(SEODailyTotal.avg_position * SEODailyTotal.impressions), 0.0),
            func.count(SEODailyTotal.id),
        ).where(
            SEODailyTotal.site_id == site_id,
            SEODailyTotal.date >= start,
            SEODailyTotal.date <= end,
        )
    ).one()

    clicks, impressions, weighted_position, days = int(row[0]), int(row[1]), float(row[2]), int(row[3])
    return {
        "clicks": clicks,
        "impressions": impressions,
        "ctr": (clicks / impressions) if impressions else 0.0,
        "avg_position": (weighted_position / impressions) if impressions else 0.0,
        "found": days > 0,
    }


def get_kpi_raw(site_id: str, curr_start: date, curr_end: date,
                 prev_start: date, prev_end: date) -> tuple[dict, dict]:
    """Raw current/previous period stats: clicks, impressions, ctr, avg_position.

    Reads `seo_daily_totals`, which holds what Search Console itself reports. It does NOT
    sum `seo_daily`: that table is stored at (date, country, device, page) grain and Google
    withholds sub-threshold rows from a grouped response, so summing it undercounts — 41% of
    clicks and 78% of impressions on a measured day. See SEODailyTotal for the numbers.

    A site synced before this table existed falls back to the breakdown so its pages still
    render, but the fallback is logged: the figures it produces are the undercounted ones and
    the fix is to run the sync, not to trust them.

    **Both periods always come from the same table.** Reading the current period from the
    totals and the previous one from the breakdown compares a complete figure against a
    41%-of-reality one, and the difference surfaces as growth: the Decision Signals panel
    reported "Organic traffic up 2361.6%, clicks grew from 437 to 10,757" on a site whose
    traffic had barely moved. When the totals cannot cover both windows, the previous period
    is returned empty — a missing baseline shows as no delta, which is honest, where a
    mismatched one invents a trend.
    """
    try:
        with get_session() as session:
            def from_totals(start, end):
                stats = query_gsc_totals(session, site_id, start, end)
                found = stats.pop("found")
                return stats, found

            def from_breakdown(start, end):
                row = session.execute(
                    select(
                        func.coalesce(func.sum(SEODaily.clicks), 0),
                        func.coalesce(func.sum(SEODaily.impressions), 0),
                        func.coalesce(func.sum(SEODaily.avg_position * SEODaily.impressions), 0.0),
                    ).where(SEODaily.site_id == site_id,
                            SEODaily.date >= start, SEODaily.date <= end)
                ).one()
                clicks, impressions, weighted = int(row[0]), int(row[1]), float(row[2])
                return {
                    "clicks": clicks,
                    "impressions": impressions,
                    "ctr": (clicks / impressions) if impressions else 0.0,
                    "avg_position": (weighted / impressions) if impressions else 0.0,
                }

            curr, curr_found = from_totals(curr_start, curr_end)
            if curr_found:
                prev, prev_found = from_totals(prev_start, prev_end)
                if not prev_found:
                    logger.warning(
                        "[overview] %s has totals for %s..%s but none for the comparison "
                        "window %s..%s — reporting no baseline rather than comparing against "
                        "the undercounted breakdown. Extend the GSC totals backfill.",
                        site_id, curr_start, curr_end, prev_start, prev_end,
                    )
                    prev = {}
                return curr, prev

            curr = from_breakdown(curr_start, curr_end)
            if curr["impressions"]:
                logger.warning(
                    "[overview] no seo_daily_totals for %s %s..%s — falling back to the "
                    "(date, country, device, page) breakdown, which undercounts Search "
                    "Console. Run the GSC sync to populate the totals.",
                    site_id, curr_start, curr_end,
                )
            return curr, from_breakdown(prev_start, prev_end)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
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
                    # Derived from this page's own totals, not AVG(ctr) over its daily rows:
                    # a day with 3 impressions and 1 click would otherwise drag a 33% CTR into
                    # the mean alongside a day with 9,000 impressions.
                    "ctr": round((row.total_clicks / row.total_impressions) * 100, 1)
                           if row.total_impressions else 0.0,
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def query_top_ga4_pages_weekly_raw(site_id: str) -> list[dict]:
    """Top 10 GA4 pages this week with location and traffic count (sessions)."""
    today = date.today()
    start_date = today - timedelta(days=7)
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page,
                    func.max(SEODaily.country).label("top_location"),
                    func.sum(SEODaily.sessions).label("total_traffic")
                )
                .where(
                    SEODaily.site_id == site_id, 
                    SEODaily.date >= start_date, 
                    SEODaily.date <= today,
                    SEODaily.landing_page.isnot(None),
                    SEODaily.sessions > 0
                )
                .group_by(SEODaily.landing_page)
                .order_by(func.sum(SEODaily.sessions).desc())
                .limit(10)
            ).all()
            return [
                {
                    "url": row.landing_page,
                    "location": row.top_location or "Unknown",
                    "traffic": int(row.total_traffic or 0)
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def query_top_audit_pages_raw(site_id: str, limit: int = 10) -> list[dict]:
    """Slowest audited pages, worst Lighthouse performance score first.

    Fixed 2026-07-27, and it had been silently dead: `PageSpeed` was referenced here but never
    imported, so every call raised `NameError`, the blanket `except` swallowed it, and the
    Overview "Slowest pages (Site Audit)" panel returned `[]` forever. It read as "no audit data
    yet" on projects that had a full PageSpeed table.

    Three things the restored query has to get right, all of which the original got wrong:

    1. `strategy == "mobile"`. `page_speed` holds one row per (url, strategy). Without the
       filter this mixes desktop and mobile and can list the same URL twice with different
       scores. Mobile is what `site_audit_service` scores the site on, so the two must agree.
    2. Both `site_id` forms. Sites are registered with or without the `sc-domain:` prefix and
       the analytics tables contain both; matching one form only silently returns nothing for
       half of them. Same reason `site_audit_service._site_id_variants` exists.
    3. `None`, not `0`. The old code coerced with `or 0`, so a page whose SEO score had not been
       captured was reported as scoring zero -- indistinguishable from a genuinely terrible
       page, and the frontend's score chip rendered it red. A missing measurement is `None` and
       the UI prints a dash.
    """
    variants = [site_id]
    if site_id.startswith("sc-domain:"):
        variants.append(site_id.replace("sc-domain:", "", 1))
    else:
        variants.append(f"sc-domain:{site_id}")

    try:
        with get_session() as session:
            rows = session.execute(
                select(PageSpeed)
                .where(PageSpeed.site_id.in_(variants), PageSpeed.strategy == "mobile")
                .order_by(PageSpeed.performance_score.asc().nulls_last())
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "url": r.url,
                    "performance": int(r.performance_score) if r.performance_score is not None else None,
                    "seo": int(r.seo_score) if r.seo_score is not None else None,
                    "lcp": float(r.lcp_ms) if r.lcp_ms is not None else None,
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []


def query_daily_traffic_raw(site_id: str, start_date: date, end_date: date) -> list[dict]:
    """Raw [{date, clicks, impressions, ctr, position}] points — the API `trend[]` shape and
    also the source data for the old view's Plotly chart dict.

    Reads `seo_daily_totals` for the same reason the KPIs do, and it matters more here than
    it looks: a chart summed from the breakdown would put a different number on the same day
    than the card above it, and the user's whole reason for this dashboard is not having to
    open Search Console to find out which one is right.

    Every point carries the day's own CTR and position too, so a hover can show all four
    figures without a second request.
    """
    try:
        with get_session() as session:
            ensure_tables(session, SEODailyTotal)
            rows = session.execute(
                select(SEODailyTotal.date, SEODailyTotal.clicks, SEODailyTotal.impressions,
                       SEODailyTotal.ctr, SEODailyTotal.avg_position)
                .where(SEODailyTotal.site_id == site_id,
                       SEODailyTotal.date >= start_date, SEODailyTotal.date <= end_date)
                .order_by(SEODailyTotal.date.asc())
            ).all()

            if not rows:
                rows = session.execute(
                    select(
                        SEODaily.date,
                        func.sum(SEODaily.clicks),
                        func.sum(SEODaily.impressions),
                        # Per-day ratios, derived rather than averaged — the same rule the
                        # window-level aggregates follow.
                        (func.sum(SEODaily.clicks) * 1.0
                         / func.nullif(func.sum(SEODaily.impressions), 0)),
                        (func.sum(SEODaily.avg_position * SEODaily.impressions)
                         / func.nullif(func.sum(SEODaily.impressions), 0)),
                    )
                    .where(SEODaily.site_id == site_id,
                           SEODaily.date >= start_date, SEODaily.date <= end_date)
                    .group_by(SEODaily.date)
                    .order_by(SEODaily.date.asc())
                ).all()

            return [
                {
                    "date": str(r[0]),
                    "clicks": int(r[1] or 0),
                    "impressions": int(r[2] or 0),
                    "ctr": round(float(r[3] or 0.0) * 100, 2),
                    "position": round(float(r[4] or 0.0), 1),
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
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
    """Maps the API's stateless `range` query param (7d/28d/90d) to
    (curr_start, curr_end, prev_start, prev_end), anchored to the latest data date.
    Unlike the old view, this never reads/writes Django session state — the API is
    stateless per HANDOFF_SPEC.md's caching model (cache key includes `range`).

    28 days, not 30: Search Console's Performance report offers 7 / 28 / 90-day windows, and
    the dashboard exists so nobody has to open Search Console to check a number. A 30-day
    window would put two different figures on two screens and leave the user to work out
    which one is wrong. `"30d"` is still accepted from older clients and means exactly the
    same 28-day window — one window, one number, whichever key asked for it.
    """
    from pipeline.utils.period_utils import get_period_dates

    if range_key == "7d":
        return get_period_dates("weekly", 0, anchor=anchor)

    days = 90 if range_key == "90d" else 28
    custom_end = anchor - timedelta(days=1)
    custom_start = custom_end - timedelta(days=days - 1)
    return get_period_dates("custom", 0, custom_start=custom_start,
                            custom_end=custom_end, anchor=anchor)


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


def _to_number(raw):
    """A number, or `None` when there is no value — never 0 as a stand-in for "unknown".

    `shared_queries._get_keywords_overview` returns raw numbers and `None` (it used to emit
    display strings — "1,234" / "N/A" / "—" — and that lossy formatting was removed on
    2026-07-27). This guard exists only so a `None` stays a `None` and so any non-numeric
    value that somehow reaches here becomes `None` rather than a fabricated zero. It
    deliberately does NOT parse strings back into numbers: doing so would make "formatted
    string" a supported input shape again, which is exactly the two-sources-of-truth problem
    that was just removed."""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return raw
    return None


def build_top_keywords_api(keywords_overview: list[dict]) -> list[dict]:
    """Overview `topKeywords[<=5]` shape: [{keyword, position, clicks, impressions, volume}]
    with **raw numbers** (or `None`), not display strings.

    Every value in the Overview response is a raw number that the SPA renders through
    `this.fmt()` / `this.posBadge()`. Handing the frontend pre-formatted strings would mean
    the one page formats numbers two different ways, and would make the columns unsortable
    and uncomparable (`"1,234" < "9"` is true as a string). This function is the adapter:
    overview_service owns the shape of the Overview response.

    Precision is now preserved end-to-end: `_get_keywords_overview` returns
    `round(avg(position), 1)`, so a keyword averaging 8.4 arrives as 8.4 and the caller
    decides whether to show it whole. (Before 2026-07-27 the query formatted it with
    `f"{avg:.0f}"` and the decimal could not be recovered here.)

    `None` is preserved as `None` so the UI can say "no data" rather than print a zero."""
    out = []
    for row in keywords_overview or []:
        out.append({
            "keyword": row.get("keyword") or "",
            # None everywhere the source had no value — never coerced to 0, which the UI
            # would render as a real "zero clicks" instead of "we don't know".
            "position": _to_number(row.get("position")),
            "clicks": _to_number(row.get("clicks")),
            "impressions": _to_number(row.get("impressions")),
            "volume": _to_number(row.get("volume")),
        })
    return out


def _coverage_state(ranked: int, total: int) -> str:
    """How much of the comparison keyword set a competitor was actually captured on.

    'none'    -> zero captured positions. There is NO average to show.
    'partial' -> captured on some but not all of the compared keywords; the average is real
                 but covers a smaller keyword set than a fully-captured competitor's, so it
                 is not comparable like-for-like and the UI must qualify it.
    'ok'      -> captured on every keyword in the comparison set.
    """
    if total <= 0 or ranked <= 0:
        return "none"
    return "ok" if ranked >= total else "partial"


def _avg_position(positions: list) -> float | None:
    """Mean of the captured positions, or None when nothing was captured. Never 0."""
    real = [p for p in positions if p is not None]
    if not real:
        return None
    return round(sum(real) / len(real), 1)


def build_positioning_overview(site_id: str) -> dict:
    """Overview `positioningOverview` — the summary card the approved design calls
    "Positioning vs Competitors": your average position next to each tracked competitor's.

    Aggregates shared_queries._get_competitor_grid, which returns per-keyword cells
    ({kw, you, comps:[{domain, pos}]}). This is the Overview *summary*; the per-keyword
    Competitor Map on the Positioning page renders the same grid in full detail.

    HONESTY CONTRACT (the reason this function is careful). That grid used to invent a
    competitor's position from an MD5 hash of keyword+domain whenever no capture existed;
    the fabrication was removed and missing pairs are now genuinely absent. An average is
    exactly the kind of aggregate that can quietly re-fabricate that data — mean over a
    list that silently skips the gaps produces a confident-looking number that describes a
    keyword set the reader never sees. So:

      * A competitor with zero captured positions gets `avgPosition: None` and
        `state: "none"`. It is never averaged, never ranked against you, and never given a
        stand-in number.
      * A competitor captured on some keywords gets a real average over exactly those
        keywords, plus `keywordsRanked`/`keywordsTotal` and `state: "partial"` so the
        number can never be read as covering more than it does.
      * The same rule applies to your own row — partial coverage of your own positions is
        labelled the same way.

    Returns `status: "setup"` (with a `note` naming what is missing) rather than an empty
    "ok" card when there are no tracked keywords, no tracked competitors, or no captured
    dates yet."""
    try:
        from apps.dashboard.services.shared_queries import _get_competitor_grid

        grid = _get_competitor_grid(site_id)
        competitors = grid.get("competitors") or []
        rows = grid.get("rows") or []

        # Order matters: name the *actual* thing that is missing. An empty grid can mean no
        # tracked keywords (competitors also come back empty), no tracked competitors, or
        # keywords + competitors but no captured ranking dates yet — three different fixes.
        if not rows and not competitors:
            # _get_competitor_grid returns competitors=[] as soon as the tracked-keyword
            # list is empty, even when competitor domains ARE tracked — so this note states
            # what the card needs rather than asserting which piece is missing.
            return _positioning_setup(
                "Nothing to compare yet. This card needs tracked keywords and captured "
                "positions: track keywords in the Keyword Explorer, add competitor domains "
                "on the Positioning page, then run a positions sync."
            )
        if grid.get("status") == "no_competitors" or not competitors:
            return _positioning_setup(
                "No competitors are being tracked yet. Add competitor domains on the "
                "Positioning page, then run a positions sync."
            )
        if not rows:
            # Either no tracked keywords, or no captured ranking dates. Both mean there is
            # nothing real to average — say so instead of rendering an empty comparison.
            return _positioning_setup(
                "No captured keyword positions yet. Track keywords and run a positions "
                "sync to compare against your competitors."
            )

        # The comparison set is the grid's own row set — the tracked keywords where at least
        # one party (you or a competitor) has a captured position. It is NOT the full tracked
        # keyword list: a keyword nobody ranks for produces no row, and counting it as
        # "uncovered" would understate every competitor equally for no information gain.
        keywords_total = len(rows)

        your_positions = [r.get("you", {}).get("pos") for r in rows]
        your_ranked = sum(1 for p in your_positions if p is not None)
        you = {
            "avgPosition": _avg_position(your_positions),
            "keywordsRanked": your_ranked,
            "keywordsTotal": keywords_total,
            "state": _coverage_state(your_ranked, keywords_total),
        }

        by_domain: dict[str, list] = {domain: [] for domain in competitors}
        for row in rows:
            for cell in row.get("comps") or []:
                domain = cell.get("domain")
                if domain in by_domain:
                    by_domain[domain].append(cell.get("pos"))

        competitor_rows = []
        for domain in competitors:
            positions = by_domain.get(domain, [])
            ranked = sum(1 for p in positions if p is not None)
            competitor_rows.append({
                "domain": domain,
                "avgPosition": _avg_position(positions),   # None when ranked == 0
                "keywordsRanked": ranked,
                "keywordsTotal": keywords_total,
                "state": _coverage_state(ranked, keywords_total),
            })

        # Best average first; competitors with no captured positions sort last, because
        # "no data" is not a good rank and must never lead the list.
        competitor_rows.sort(
            key=lambda c: (c["avgPosition"] is None, c["avgPosition"] if c["avgPosition"] is not None else 0)
        )

        covered = sum(1 for c in competitor_rows if c["state"] != "none")
        return {
            "status": "ok",
            "note": "",
            "you": you,
            "competitors": competitor_rows,
            "keywordsTotal": keywords_total,
            "competitorsWithData": covered,
            "capturedAt": grid.get("latest_date"),
        }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return _positioning_setup("Positioning comparison is unavailable right now.")


def _positioning_setup(note: str) -> dict:
    """Honest empty shape for build_positioning_overview — no invented averages, and a
    note naming exactly what is missing so the card can tell the user what to do."""
    return {"status": "setup", "note": note, "you": None, "competitors": [],
            "keywordsTotal": 0, "competitorsWithData": 0, "capturedAt": None}


def build_pillars(site_id: str, kpis_current: dict, kpis_previous: dict, top3_count: int) -> list[dict]:
    """HANDOFF_SPEC.md §2.2 pillar shape. Site health goes live as soon as the Site Audit
    page has real data (same score the audit page shows — the two must never disagree);
    Paid ROAS / AI visibility stay state='setup' until Ads credentials / AI connectors
    exist. Lazy import: pillar cards are rollups OF the sibling pages, so this is the one
    place overview_service legitimately reads a sibling page's service."""
    from apps.dashboard.services.site_audit_service import site_health_summary
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
        # Impressions ride along in the subtitle rather than taking a pillar of their own:
        # clicks without the impressions behind them can't be read (400 clicks is good news
        # on 5,000 impressions and bad news on 500,000), and the two always move together.
        {"label": "Organic clicks", "target": "overview", "valueKind": "num",
         "value": int(current_clicks), "delta": clicks_delta, "deltaUnit": "%",
         "sub": f"clicks · {int(kpis_current.get('impressions', 0)):,} impressions",
         "state": "ok"},
        {"label": "Avg. position", "target": "positioning", "valueKind": "pos",
         "value": round(kpis_current.get("avg_position", 0.0), 1), "delta": None, "deltaUnit": "pos",
         "sub": f"{top3_count} keywords in top 3", "state": "ok"},
        _site_health_pillar(site_health_summary(site_id)),
        {"label": "Paid ROAS", "target": "ads", "valueKind": "roas",
         "value": None, "delta": None, "deltaUnit": None, "sub": "Ads not connected yet",
         "state": "setup"},
        {"label": "AI visibility", "target": "ai", "valueKind": "pct",
         "value": None, "delta": None, "deltaUnit": "pts", "sub": "not set up yet",
         "state": "setup"},
    ]


def _site_health_pillar(health: dict | None) -> dict:
    """Site health pillar card — real score when audit data exists, honest setup otherwise."""
    if health is None:
        return {"label": "Site health", "target": "pages", "valueKind": "score",
                "value": None, "delta": None, "deltaUnit": "pts",
                "sub": "Site Audit not set up yet", "state": "setup"}
    errors = health["errors"]
    return {"label": "Site health", "target": "pages", "valueKind": "score",
            "value": health["score"], "delta": None, "deltaUnit": "pts",
            "sub": f"{errors} error{'s' if errors != 1 else ''} to fix" if errors else "no errors found",
            "state": "ok"}


def _score_tone(score: int) -> str:
    """Module-card status dot from a 0-100 score, matching the audit page's own bands
    (>=80 healthy, >=60 needs work, else poor)."""
    return "ok" if score >= 80 else ("warn" if score >= 60 else "bad")


def build_modules(site_id: str, seo_module_stat: str, keywords_count: int, top3_count: int,
                   avg_position: float) -> list[dict]:
    """HANDOFF_SPEC.md §2.2 module-status card shape. Backlinks / Site Audit cards go live
    when their pages have real data (same rollups those pages show); Ads / AI stay setup."""
    from apps.dashboard.services.backlinks_service import query_backlinks_summary_raw
    from apps.dashboard.services.site_audit_service import site_health_summary

    health = site_health_summary(site_id)
    if health is None:
        audit_card = {"label": "Site Audit", "target": "pages", "stat": "Not set up",
                      "sub": "", "tone": "setup"}
    else:
        audit_card = {"label": "Site Audit", "target": "pages",
                      "stat": f"{health['score']}/100",
                      "sub": (f"{health['errors']} error{'s' if health['errors'] != 1 else ''}"
                              if health["errors"] else "no errors"),
                      "tone": _score_tone(health["score"])}

    bl = query_backlinks_summary_raw(site_id)
    if bl["total"]:
        backlinks_card = {"label": "Backlinks", "target": "backlinks",
                          "stat": f"{bl['live']} live",
                          "sub": f"{bl['unique_domains']} referring domains",
                          "tone": "ok" if bl["live"] >= bl["lost"] else "warn"}
    else:
        backlinks_card = {"label": "Backlinks", "target": "backlinks", "stat": "Not connected",
                          "sub": "", "tone": "setup"}

    return [
        {"label": "SEO Performance", "target": "seo", "stat": seo_module_stat, "sub": "",
         "tone": "ok"},
        {"label": "Keywords", "target": "keywords", "stat": f"{keywords_count} tracked",
         "sub": f"{top3_count} in top 3", "tone": "ok"},
        {"label": "Position Tracking", "target": "positioning", "stat": f"#{avg_position:.1f} avg",
         "sub": "", "tone": "ok"},
        backlinks_card,
        audit_card,
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
