"""SEO page data — raw calculators (shared by the old Django view and the new DRF API
view) plus the old view's presentation formatters. See
.claude/api-reference.md for the field mapping."""

from datetime import date

from sqlalchemy import func, select

from pipeline.db.schema import SEODaily, Anomaly, TechnicalIssue, KeywordRanking
from pipeline.utils.db_connection import get_session


def query_low_ctr_pages_raw(site_id: str, start_date: date, end_date: date,
                             min_impressions: int = 100, max_ctr: float = 0.02,
                             limit: int = 15) -> list[dict]:
    """Pages that get seen but not clicked: high impressions, low CTR."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page,
                    func.sum(SEODaily.clicks).label("clicks"),
                    func.sum(SEODaily.impressions).label("impressions"),
                    # Impression-weighted, the way Search Console computes it. A plain AVG
                    # over this page's daily rows lets a day it surfaced once at position 90
                    # count as much as a day it drew 9,000 impressions at position 4.
                    func.sum(SEODaily.avg_position * SEODaily.impressions).label("weighted_position"),
                )
                .where(
                    SEODaily.site_id == site_id,
                    SEODaily.date >= start_date, SEODaily.date <= end_date,
                    SEODaily.landing_page.isnot(None),
                )
                .group_by(SEODaily.landing_page)
                .having(func.sum(SEODaily.impressions) >= min_impressions)
            ).all()

            out = []
            for r in rows:
                impr = int(r.impressions or 0)
                clicks = int(r.clicks or 0)
                ctr = (clicks / impr) if impr else 0
                if ctr <= max_ctr:
                    out.append({
                        "url": r.landing_page,
                        "url_short": (r.landing_page or "").split("//")[-1][:55],
                        "clicks": clicks,
                        "impressions": impr,
                        "ctr": round(ctr * 100, 2),
                        "avg_position": round((r.weighted_position or 0) / impr, 1) if impr else 0.0,
                    })
            out.sort(key=lambda x: x["impressions"], reverse=True)
            return out[:limit]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_low_ctr_pages_raw error: {e}", exc_info=True)
        return []


def query_seo_by_dimension_raw(site_id: str, start_date: date, end_date: date) -> dict:
    """Raw numeric SEO metrics by country and device for the period."""
    try:
        with get_session() as session:
            # CTR and position are ratios, so both are DERIVED from the group's own totals,
            # never AVG()ed over its (date, page) rows — an unweighted mean let a 3-impression
            # row count as much as a 9,000-impression one and overstated USA's CTR by 43%
            # (0.63% shown, 0.44% real) and GBR's by 600% (0.14% vs 0.02%), measured
            # 2026-08-03. Same rule as the Overview KPIs and seo_daily_totals.
            by_country = session.execute(
                select(
                    SEODaily.country,
                    func.sum(SEODaily.clicks).label("total_clicks"),
                    func.sum(SEODaily.impressions).label("total_impressions"),
                    func.sum(SEODaily.avg_position * SEODaily.impressions).label("weighted_position"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date, SEODaily.country.isnot(None))
                .group_by(SEODaily.country)
                .order_by(func.sum(SEODaily.clicks).desc())
                .limit(5)
            ).all()

            by_device = session.execute(
                select(
                    SEODaily.device,
                    func.sum(SEODaily.clicks).label("total_clicks"),
                    func.sum(SEODaily.impressions).label("total_impressions"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date, SEODaily.device.isnot(None))
                .group_by(SEODaily.device)
                .order_by(func.sum(SEODaily.clicks).desc())
            ).all()

            def _ctr(clicks, impressions):
                return round(clicks / impressions * 100, 2) if impressions else 0.0

            return {
                "by_country": [
                    {"country": r.country or "Unknown", "clicks": int(r.total_clicks or 0),
                     "impressions": int(r.total_impressions or 0),
                     "ctr": _ctr(int(r.total_clicks or 0), int(r.total_impressions or 0)),
                     "avg_position": round((r.weighted_position or 0) / r.total_impressions, 1)
                                     if r.total_impressions else 0.0}
                    for r in by_country
                ],
                "by_device": [
                    {"device": r.device or "Unknown", "clicks": int(r.total_clicks or 0),
                     "impressions": int(r.total_impressions or 0),
                     "ctr": _ctr(int(r.total_clicks or 0), int(r.total_impressions or 0))}
                    for r in by_device
                ],
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_seo_by_dimension_raw error: {e}", exc_info=True)
        return {"by_country": [], "by_device": []}


def query_seo_anomalies_raw(site_id: str, limit: int = 10) -> list[dict]:
    """Raw unacknowledged anomalies, full fields (id + description included, needed by
    the new API shape — the old page's formatter historically dropped both)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(Anomaly)
                .where(Anomaly.site_id == site_id, Anomaly.is_acknowledged == 0)
                .order_by(Anomaly.date.desc())
                .limit(limit)
            ).scalars().all()

            out = []
            for r in rows:
                up = r.actual_value >= r.baseline_value
                out.append({
                    "id": r.id,
                    "metric_type": r.metric_type,
                    "severity": r.severity,
                    "direction": "up" if up else "down",
                    "deviation_pct": r.deviation_pct,
                    "actual_value": r.actual_value,
                    "baseline_value": r.baseline_value,
                    "date": r.date,
                    "description": r.description or "",
                })
            return out
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_seo_anomalies_raw error: {e}", exc_info=True)
        return []


def count_technical_issues(site_id: str, issue_type: str | None = None) -> int:
    """Unlimited COUNT(*) of technical issues, optionally filtered by type. NOT the same
    as len(_get_technical_issues(...)), which caps at limit=15 for display purposes."""
    try:
        with get_session() as session:
            q = select(func.count()).select_from(TechnicalIssue).where(TechnicalIssue.site_id == site_id)
            if issue_type is not None:
                q = q.where(TechnicalIssue.issue_type == issue_type)
            return session.execute(q).scalar() or 0
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"count_technical_issues error: {e}", exc_info=True)
        return 0


def query_technical_issues_raw(site_id: str, limit: int = 15) -> list[dict]:
    """The technical issues themselves, not just count_technical_issues()'s number.

    Grouped by (issue_type, severity) exactly like alerts_service.query_alert_technical_issues_raw
    — a site with 400 soft-404s is one problem to fix, not 400 rows to scroll. `limit` caps
    GROUPS, not underlying rows, so the affected-page counts stay whole.

    The example url/description come from a second lookup keyed on MIN(id) rather than from
    MAX(url)/MAX(description) aggregates, because two independent aggregates can return values
    from two different rows — i.e. a URL paired with another page's description. Both queries
    use only COUNT/MIN/GROUP BY/IN, so they run identically on SQLite and Postgres.
    """
    # Reused verbatim from the alerts feed so one issue_type never gets two different human
    # labels across pages. Do not fork these maps — extend the ones in alerts_service.
    # Imported inside the function, not at module scope: alerts_service reaches the Django
    # ORM (mutation_state -> apps.dashboard.models), and this module is otherwise pure
    # SQLAlchemy, safe to import before the app registry is ready.
    from apps.dashboard.services.alerts_service import _ISSUE_LABELS, _SEVERITY_RANK

    try:
        with get_session() as session:
            groups = session.execute(
                select(
                    TechnicalIssue.issue_type,
                    TechnicalIssue.severity,
                    func.count(TechnicalIssue.id).label("pages"),
                    func.min(TechnicalIssue.id).label("example_id"),
                )
                .where(TechnicalIssue.site_id == site_id)
                .group_by(TechnicalIssue.issue_type, TechnicalIssue.severity)
            ).all()
            if not groups:
                return []

            examples = {
                row.id: row
                for row in session.execute(
                    select(TechnicalIssue).where(
                        TechnicalIssue.id.in_([g.example_id for g in groups])
                    )
                ).scalars().all()
            }

            out = []
            for g in groups:
                example = examples.get(g.example_id)
                issue_type = g.issue_type or ""
                out.append({
                    "issue_type": issue_type,
                    "label": _ISSUE_LABELS.get(issue_type, issue_type.replace("_", " ").title()),
                    "severity": g.severity or "medium",
                    "pages": int(g.pages or 0),
                    "example_url": (example.url if example is not None else "") or "",
                    "description": (example.description if example is not None else "") or "",
                })
            # Worst first, then widest blast radius. Sorted in Python because the severity
            # ranking is semantic, not alphabetical, and a portable SQL CASE buys nothing here.
            out.sort(key=lambda i: (_SEVERITY_RANK.get(i["severity"], 9), -i["pages"]))
            return out[:limit]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_technical_issues_raw error: {e}", exc_info=True)
        return []


def count_quick_win_keywords(site_id: str, start_date: date, end_date: date) -> int:
    """Count of keywords ranking 4-10 (page 1, not yet top-3) with real clicks in the period —
    same 'quick win' rule used elsewhere (e.g. the Keywords page's action buckets)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("avg_position"),
                    func.sum(KeywordRanking.clicks).label("total_clicks"),
                )
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= start_date, KeywordRanking.date <= end_date)
                .group_by(KeywordRanking.keyword)
            ).all()
            return sum(
                1 for r in rows
                if r.avg_position is not None and 4 <= r.avg_position <= 10 and (r.total_clicks or 0) > 0
            )
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"count_quick_win_keywords error: {e}", exc_info=True)
        return 0


def format_recent_anomalies(raw_anomalies: list[dict]) -> list[dict]:
    """Old dashboard/seo.html template shape — human labels, formatted strings."""
    labels = {
        "seo_clicks": "Clicks", "seo_impressions": "Impressions",
        "seo_ctr": "CTR", "seo_avg_position": "Avg. position",
        "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
        "ad_impressions": "Ad impressions", "ad_conversions": "Conversions",
    }
    out = []
    for r in raw_anomalies:
        out.append({
            "metric": labels.get(r["metric_type"], r["metric_type"]),
            "severity": r["severity"],
            "direction": r["direction"],
            "deviation": f"{'+' if r['direction'] == 'up' else '-'}{abs(r['deviation_pct']):.0f}%",
            "actual": f"{r['actual_value']:,.0f}",
            "baseline": f"{r['baseline_value']:,.0f}",
            "date": str(r["date"]),
        })
    return out


def build_seo_response(site_id: str, curr_start: date, curr_end: date) -> dict:
    """HANDOFF_SPEC.md `seo` view shape — verified against the real fixture's seoView()
    in Limitless marketing dashboard2/app/api.js. See
    .claude/api-reference.md for the field mapping and the
    kpis.critical/total_issues correction."""
    low_ctr_raw = query_low_ctr_pages_raw(site_id, curr_start, curr_end)
    by_dim = query_seo_by_dimension_raw(site_id, curr_start, curr_end)
    anomalies_raw = query_seo_anomalies_raw(site_id)
    issues_raw = query_technical_issues_raw(site_id)
    critical_count = count_technical_issues(site_id, issue_type="not_found_404")
    total_issue_count = count_technical_issues(site_id)
    quick_win_count = count_quick_win_keywords(site_id, curr_start, curr_end)

    return {
        "kpis": {
            "low_ctr": len(low_ctr_raw),
            "anomalies": len(anomalies_raw),
            "critical": critical_count,
            "total_issues": total_issue_count + len(anomalies_raw) + len(low_ctr_raw),
        },
        "lowCtrPages": [
            {"url": p["url"], "impressions": p["impressions"], "clicks": p["clicks"],
             "ctr": p["ctr"], "avg_pos": p["avg_position"]}
            for p in low_ctr_raw
        ],
        "countries": by_dim["by_country"],
        # by_dim already computed this; it used to be dropped on the floor.
        "devices": by_dim["by_device"],
        "issues": issues_raw,
        "anomalies": [
            {
                "id": str(a["id"]),
                "metric": {"seo_clicks": "Clicks", "seo_impressions": "Impressions",
                           "seo_ctr": "CTR", "seo_avg_position": "Avg. position",
                           "ad_spend": "Ad spend", "ad_clicks": "Ad clicks",
                           "ad_impressions": "Ad impressions", "ad_conversions": "Conversions"
                           }.get(a["metric_type"], a["metric_type"]),
                "severity": a["severity"],
                "deviation": f"{'+' if a['direction'] == 'up' else '-'}{abs(a['deviation_pct']):.0f}%",
                "date": str(a["date"]),
                "detail": a["description"],
            }
            for a in anomalies_raw
        ],
        "quickWinKws": quick_win_count,
    }
