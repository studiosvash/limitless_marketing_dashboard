"""Off-site SEO page (Phase C3) — real reshape of GA4-sourced SEODaily columns (sessions,
engagement_rate, conversions, users, landing_page) plus honest state:"setup"/[] placeholders
for everything requiring GA4 dimensions (channel, source) this codebase doesn't fetch yet, or
per-platform social connectors that don't exist/aren't credentialed. See
docs/superpowers/specs/2026-07-12-phaseC3-offsite-seo-design.md for the full field mapping."""
import logging

from sqlalchemy import func, select

from pipeline.db.schema import SEODaily
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def query_offsite_totals_raw(site_id: str, start, end) -> dict:
    """Real sessions/users/engagementRate/keyEvents/engagedSessions aggregated over the period.
    revenue/referringDomains are honest 0 (no GA4 revenue/source dimension exists yet) --
    included here, not left for the builder, so this function's return shape is already the
    complete real-data contract for `totals`/`prev`."""
    try:
        with get_session() as session:
            row = session.execute(
                select(
                    func.sum(SEODaily.sessions).label("sessions"),
                    func.sum(SEODaily.users).label("users"),
                    func.avg(SEODaily.engagement_rate).label("engagement_rate"),
                    func.sum(SEODaily.conversions).label("conversions"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
            ).first()
    except Exception as e:
        logger.error(f"query_offsite_totals_raw error: {e}", exc_info=True)
        row = None

    sessions = int(row.sessions or 0) if row else 0
    engagement_rate = float(row.engagement_rate or 0.0) if row else 0.0
    return {
        "sessions": sessions,
        "users": int(row.users or 0) if row else 0,
        "engagementRate": round(engagement_rate * 100, 1),
        "engagedSessions": round(sessions * engagement_rate),
        "keyEvents": int(row.conversions or 0) if row else 0,
        "revenue": 0,
        "referringDomains": 0,
    }


def query_offsite_trend_raw(site_id: str, start, end) -> list[dict]:
    """Real daily [{date, sessions, engagedSessions, keyEvents, revenue}] -- same pattern as
    overview_service.query_daily_traffic_raw. revenue honest 0 per day (see totals note)."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.date,
                    func.sum(SEODaily.sessions).label("sessions"),
                    func.avg(SEODaily.engagement_rate).label("engagement_rate"),
                    func.sum(SEODaily.conversions).label("conversions"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
                .group_by(SEODaily.date)
                .order_by(SEODaily.date.asc())
            ).all()
    except Exception as e:
        logger.error(f"query_offsite_trend_raw error: {e}", exc_info=True)
        return []

    out = []
    for r in rows:
        sessions = int(r.sessions or 0)
        er = float(r.engagement_rate or 0.0)
        out.append({
            "date": str(r.date),
            "sessions": sessions,
            "engagedSessions": round(sessions * er),
            "keyEvents": int(r.conversions or 0),
            "revenue": 0,
        })
    return out


def query_offsite_landing_pages_raw(site_id: str, start, end) -> list[dict]:
    """Real [{url, topSource, sessions, engagedRate, keyEvents}], capped at 50 (matching the
    existing _get_page_health cap convention in apps/dashboard/views.py). topSource is honestly
    "" -- no GA4 source dimension exists yet to attribute it, see design spec."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page.label("url"),
                    func.sum(SEODaily.sessions).label("sessions"),
                    func.avg(SEODaily.engagement_rate).label("engagement_rate"),
                    func.sum(SEODaily.conversions).label("conversions"),
                )
                .where(
                    SEODaily.site_id == site_id,
                    SEODaily.date >= start,
                    SEODaily.date <= end,
                    SEODaily.landing_page.isnot(None),
                )
                .group_by(SEODaily.landing_page)
                .order_by(func.sum(SEODaily.sessions).desc())
                .limit(50)
            ).all()
    except Exception as e:
        logger.error(f"query_offsite_landing_pages_raw error: {e}", exc_info=True)
        return []

    return [
        {
            "url": r.url,
            "topSource": "",
            "sessions": int(r.sessions or 0),
            "engagedRate": round(float(r.engagement_rate or 0.0), 4),
            "keyEvents": int(r.conversions or 0),
        }
        for r in rows
    ]


def build_offsite_response(site_id: str, curr_start, curr_end, prev_start, prev_end) -> dict:
    """API-shaped Off-site SEO response. Real: totals, prev, trend, landingPages (reshaped from
    real SEODaily GA4 columns). channels/referrers/social honestly [] -- no channel/source GA4
    dimension or social-platform connector exists yet. connectors{} real (all currently false).
    syncMeta honestly state:"setup" -- no GA4 pull-metadata table exists. See design spec for why
    each field is scoped the way it is."""
    return {
        "totals": query_offsite_totals_raw(site_id, curr_start, curr_end),
        "prev": query_offsite_totals_raw(site_id, prev_start, prev_end),
        "trend": query_offsite_trend_raw(site_id, curr_start, curr_end),
        "channels": [],
        "referrers": [],
        "social": [],
        "landingPages": query_offsite_landing_pages_raw(site_id, curr_start, curr_end),
        "connectors": {
            "linkedin": False, "reddit": False, "youtube": False,
            "x": False, "facebook": False, "instagram": False,
        },
        "syncMeta": {"state": "setup"},
    }
