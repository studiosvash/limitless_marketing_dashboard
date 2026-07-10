"""SEO page data — raw calculators (shared by the old Django view and the new DRF API
view) plus the old view's presentation formatters. See
docs/superpowers/specs/2026-07-10-phaseB1-seo-design.md for the field mapping."""

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
                    func.avg(SEODaily.avg_position).label("avg_position"),
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
                        "avg_position": round(r.avg_position or 0, 1),
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
            by_country = session.execute(
                select(
                    SEODaily.country,
                    func.sum(SEODaily.clicks).label("total_clicks"),
                    func.sum(SEODaily.impressions).label("total_impressions"),
                    func.avg(SEODaily.ctr).label("avg_ctr"),
                    func.avg(SEODaily.avg_position).label("avg_position"),
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
                    func.avg(SEODaily.ctr).label("avg_ctr"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date, SEODaily.device.isnot(None))
                .group_by(SEODaily.device)
                .order_by(func.sum(SEODaily.clicks).desc())
            ).all()

            return {
                "by_country": [
                    {"country": r.country or "Unknown", "clicks": int(r.total_clicks or 0),
                     "impressions": int(r.total_impressions or 0),
                     "ctr": round((r.avg_ctr or 0) * 100, 2), "avg_position": round(r.avg_position or 0, 1)}
                    for r in by_country
                ],
                "by_device": [
                    {"device": r.device or "Unknown", "clicks": int(r.total_clicks or 0),
                     "impressions": int(r.total_impressions or 0), "ctr": round((r.avg_ctr or 0) * 100, 2)}
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
