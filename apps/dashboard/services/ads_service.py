"""Ads page (Phase C4) — real reshape of AdMetricDaily + GA4 SEODaily data plus honest
empty/zero placeholders for everything requiring Google Ads credentials (currently blank in
.env) or schema that doesn't exist yet (SearchTerm/Attribution models, rich per-campaign
metadata). See docs/superpowers/specs/2026-07-13-phaseC4-ads-design.md for the full mapping.

IMPORTANT: unlike backlinks_service/site_audit_service/offsite_service, totals/prev/pacing/
syncMeta here must be REAL fully-keyed objects with honest zero/None values -- never a bare
{"state": "setup"} sentinel. The SPA's Ads block has no setup-guard anywhere and will crash
(TypeError on .toFixed()/.map()) if these are sentinel objects instead of real-shaped ones."""
import logging
import os
from datetime import date

from sqlalchemy import func, select

from pipeline.db.schema import AdMetricDaily, SEODaily
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def query_ads_totals_raw(site_id: str, start: date, end: date) -> dict:
    """Real AdMetricDaily aggregation (spend-weighted roas) + real GA4 conversions
    cross-reference from SEODaily. Honest 0 for conv_value/ga4_revenue (no such columns
    exist anywhere in this schema)."""
    try:
        with get_session() as session:
            row = session.execute(
                select(
                    func.sum(AdMetricDaily.spend).label("spend"),
                    func.sum(AdMetricDaily.clicks).label("clicks"),
                    func.sum(AdMetricDaily.impressions).label("impressions"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                ).where(AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
            ).first()
            spend = float(row.spend or 0)
            clicks = float(row.clicks or 0)
            impressions = float(row.impressions or 0)
            conversions = float(row.conversions or 0)

            weighted = session.execute(
                select(
                    func.sum(AdMetricDaily.spend * AdMetricDaily.roas).label("weighted_roas_sum"),
                    func.sum(AdMetricDaily.spend).label("known_roas_spend"),
                ).where(
                    AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end,
                    AdMetricDaily.roas.isnot(None),
                )
            ).first()
            known_roas_spend = float(weighted.known_roas_spend or 0)
            # Weighted average over only the rows that actually have a roas value -- spend
            # with roas=None must NOT be treated as a zero-return contributor to the
            # denominator, or the result silently understates roas (fabrication-by-omission).
            roas = float(weighted.weighted_roas_sum or 0) / known_roas_spend if known_roas_spend else 0.0

            ga4_row = session.execute(
                select(func.sum(SEODaily.conversions)).where(
                    SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end
                )
            ).scalar()
            ga4_key_events = float(ga4_row or 0)
    except Exception as e:
        logger.error(f"query_ads_totals_raw error: {e}", exc_info=True)
        return {"spend": 0.0, "clicks": 0.0, "impressions": 0.0, "conversions": 0.0,
                "cpc": 0.0, "roas": 0.0, "conv_value": 0.0, "ga4_key_events": 0.0, "ga4_revenue": 0.0}

    return {
        "spend": spend, "clicks": clicks, "impressions": impressions, "conversions": conversions,
        "cpc": spend / clicks if clicks else 0.0,
        "roas": roas,
        "conv_value": 0.0,  # no revenue/value column exists on AdMetricDaily
        "ga4_key_events": ga4_key_events,
        "ga4_revenue": 0.0,  # no revenue column exists on SEODaily
    }


def query_ads_trend_raw(site_id: str, start: date, end: date) -> list[dict]:
    """Real per-day spend/conversions + GA4 conversions cross-reference. Same shape/pattern
    as offsite_service.query_offsite_trend_raw."""
    try:
        with get_session() as session:
            ads_rows = session.execute(
                select(
                    AdMetricDaily.date,
                    func.sum(AdMetricDaily.spend).label("spend"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                ).where(AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
                .group_by(AdMetricDaily.date).order_by(AdMetricDaily.date)
            ).all()
            ads_by_date = {r.date: (float(r.spend or 0), float(r.conversions or 0)) for r in ads_rows}

            ga4_rows = session.execute(
                select(SEODaily.date, func.sum(SEODaily.conversions).label("conversions"))
                .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
                .group_by(SEODaily.date).order_by(SEODaily.date)
            ).all()
            ga4_by_date = {r.date: float(r.conversions or 0) for r in ga4_rows}
    except Exception as e:
        logger.error(f"query_ads_trend_raw error: {e}", exc_info=True)
        return []

    all_dates = sorted(set(ads_by_date) | set(ga4_by_date))
    return [
        {
            "date": d.isoformat(),
            "spend": ads_by_date.get(d, (0.0, 0.0))[0],
            "conversions": ads_by_date.get(d, (0.0, 0.0))[1],
            "ga4_key_events": ga4_by_date.get(d, 0.0),
        }
        for d in all_dates
    ]


def query_ads_pacing_raw(site_id: str) -> dict:
    """Real calendar-month-to-date spend + honest-zero budget/projection math. Always 'this
    calendar month' -- independent of the range param, matching the SPA's 'day X of Y' label."""
    today = date.today()
    month_start = today.replace(day=1)
    try:
        with get_session() as session:
            row = session.execute(
                select(func.sum(AdMetricDaily.spend)).where(
                    AdMetricDaily.site_id == site_id, AdMetricDaily.date >= month_start, AdMetricDaily.date <= today
                )
            ).scalar()
            mtd_spend = float(row or 0)
    except Exception as e:
        logger.error(f"query_ads_pacing_raw error: {e}", exc_info=True)
        mtd_spend = 0.0

    day_of_month = today.day
    if today.month == 12:
        days_in_month = 31
    else:
        next_month = today.replace(month=today.month + 1, day=1)
        days_in_month = (next_month - month_start).days

    monthly_budget = 0.0  # no budget-setting feature exists anywhere in this codebase
    projected = (mtd_spend / day_of_month * days_in_month) if day_of_month else 0.0
    pct = min(100, round(mtd_spend / monthly_budget * 100)) if monthly_budget else 0

    return {
        "monthly_budget": monthly_budget, "mtd_spend": mtd_spend, "projected": projected,
        "day_of_month": day_of_month, "days_in_month": days_in_month, "pct": pct,
        "channels": [],  # no per-platform budget data exists
    }


def build_ads_response(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date) -> dict:
    """API-shaped Ads response. Real: totals, prev, trend, pacing (all honest-zero today
    since AdMetricDaily has 0 rows), window. Honest []: campaigns, searchTerms, attribution,
    landingPages, negatives (no backing schema for the rich per-row fields the SPA's tabs
    need, or no model exists at all). syncMeta.connected reflects the real Google Ads
    credential state -- see docs/superpowers/specs/2026-07-13-phaseC4-ads-design.md."""
    totals = query_ads_totals_raw(site_id, curr_start, curr_end)
    prev = query_ads_totals_raw(site_id, prev_start, prev_end)
    trend = query_ads_trend_raw(site_id, curr_start, curr_end)
    pacing = query_ads_pacing_raw(site_id)

    connected = bool(os.getenv("GOOGLE_ADS_CUSTOMER_ID") and os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"))

    return {
        "totals": totals,
        "prev": prev,
        "trend": trend,
        "pacing": pacing,
        "campaigns": [],
        "searchTerms": [],
        "attribution": [],
        "landingPages": [],
        "negatives": [],
        "window": {"from": curr_start.isoformat(), "to": curr_end.isoformat(), "days": (curr_end - curr_start).days + 1},
        "syncMeta": {
            "connected": connected,
            "cadence": None, "last_pull": None, "next_pull": None,
            "ops_used": 0, "ops_limit": 0, "ga4_tokens_used": 0, "ga4_tokens_limit": 0,
        },
    }
