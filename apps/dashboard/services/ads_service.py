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

from apps.dashboard.services.mutation_state import get_state, set_state
from pipeline.db.schema import AdMetricDaily, SEODaily
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

_ADS_OVERRIDES_DEFAULT = {"status": {}, "budget": {}, "negatives": [], "promoted": []}


def get_ads_overrides(site_id: str) -> dict:
    """User-recorded Ads intent (HANDOFF_SPEC 8 'write-back semantics'): campaign pause/
    budget edits, negative keywords, promoted terms. Persisted immediately so subsequent
    GETs reflect them; the actual Google Ads write-back happens on the next 12h sync once
    the Ads connector has credentials."""
    stored = get_state(site_id, "adsOverrides", {})
    return {**_ADS_OVERRIDES_DEFAULT, **stored}


def set_campaign_status(site_id: str, campaign_id: str, status: str) -> str:
    if status not in ("enabled", "paused"):
        raise ValueError("status must be 'enabled' or 'paused'")
    overrides = get_ads_overrides(site_id)
    overrides["status"] = {**overrides["status"], str(campaign_id): status}
    set_state(site_id, "adsOverrides", overrides)
    return status


def set_campaign_budget(site_id: str, campaign_id: str, budget_daily) -> int:
    """HANDOFF_SPEC 2.7: budget_daily edits round to integers >= 1."""
    value = max(1, round(float(budget_daily)))
    overrides = get_ads_overrides(site_id)
    overrides["budget"] = {**overrides["budget"], str(campaign_id): value}
    set_state(site_id, "adsOverrides", overrides)
    return value


def add_negative(site_id: str, term: str, match_type: str, campaign_id=None) -> list[dict]:
    """Campaign-level negative when campaign_id is given, shared set otherwise. Returns the
    full negatives list (the endpoint's response body). Idempotent per (term, campaignId)."""
    overrides = get_ads_overrides(site_id)
    negatives = overrides["negatives"]
    key = (term.strip().lower(), str(campaign_id) if campaign_id else None)
    if not any((n["term"].strip().lower(), n.get("campaignId")) == key for n in negatives):
        negatives = negatives + [{
            "term": term.strip(),
            "matchType": match_type if match_type in ("exact", "phrase", "broad") else "exact",
            "campaignId": str(campaign_id) if campaign_id else None,
        }]
        overrides["negatives"] = negatives
        set_state(site_id, "adsOverrides", overrides)
    return negatives


def mark_promoted(site_id: str, term: str) -> None:
    overrides = get_ads_overrides(site_id)
    if term not in overrides["promoted"]:
        overrides["promoted"] = overrides["promoted"] + [term]
        set_state(site_id, "adsOverrides", overrides)


def _search_term_status(term_row: dict, negatives: list[dict], promoted: list[str]) -> str:
    """HANDOFF_SPEC 2.7: derived server-side, precedence negative > tracked > converting > wasted."""
    term_l = (term_row.get("term") or "").strip().lower()
    if any(n["term"].strip().lower() == term_l for n in negatives):
        return "negative"
    if term_row.get("term") in promoted:
        return "tracked"
    if (term_row.get("conversions") or 0) > 0:
        return "converting"
    return "wasted"


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
    overrides = get_ads_overrides(site_id)

    # Campaign/searchTerm rows are [] until the Google Ads connector has credentials, but
    # user intent (negatives, promoted terms, status/budget edits) must be visible in GETs
    # immediately (HANDOFF_SPEC 8 'Mutation -> refetch'). When campaign rows exist, apply
    # the recorded status/budget overrides and the derived searchTerm status here.
    campaigns: list[dict] = []
    for c in campaigns:
        cid = str(c.get("id"))
        if cid in overrides["status"]:
            c["status"] = overrides["status"][cid]
        if cid in overrides["budget"]:
            c["budget_daily"] = overrides["budget"][cid]
    search_terms: list[dict] = []
    for t in search_terms:
        t["status"] = _search_term_status(t, overrides["negatives"], overrides["promoted"])

    connected = bool(os.getenv("GOOGLE_ADS_CUSTOMER_ID") and os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"))

    return {
        "totals": totals,
        "prev": prev,
        "trend": trend,
        "pacing": pacing,
        "campaigns": campaigns,
        "searchTerms": search_terms,
        "attribution": [],
        "landingPages": [],
        "negatives": overrides["negatives"],
        "window": {"from": curr_start.isoformat(), "to": curr_end.isoformat(), "days": (curr_end - curr_start).days + 1},
        "syncMeta": {
            "connected": connected,
            "cadence": None, "last_pull": None, "next_pull": None,
            "ops_used": 0, "ops_limit": 0, "ga4_tokens_used": 0, "ga4_tokens_limit": 0,
        },
    }
