"""Ads page — real aggregation of totals, trend and month-to-date pacing from the real
AdMetricDaily table plus a real GA4 key-event cross-reference from SEODaily, with full
multi-id support.

Search Terms is built from the real AdSearchTerm table and Attribution from a real join of
AdMetricDaily against GA4CampaignDaily; both were hardcoded `[]` until those tables existed.

Everything the Google Ads connector does not actually persist is still returned as an honest
zero/None/empty rather than an invented value: there is no budget model anywhere in the
codebase and no per-campaign metadata (status/type/ad groups/impression share) beyond the
daily aggregate rows. See CLAUDE.md ("never fabricate data to fill a shape") — the SPA
renders empty states for all of these."""
import logging
import os
from datetime import date, timedelta
from sqlalchemy import case, func, select

from apps.dashboard.services.mutation_state import get_state, set_state
from pipeline.db.schema import AdMetricDaily, AdSearchTerm, GA4CampaignDaily, SEODaily
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

_ADS_OVERRIDES_DEFAULT = {"status": {}, "budget": {}, "negatives": [], "promoted": []}


def _resolve_site_ids(site_id: str) -> list[str]:
    alt_id = site_id.replace("sc-domain:", "") if site_id.startswith("sc-domain:") else f"sc-domain:{site_id}"
    return [site_id, alt_id]


def get_ads_overrides(site_id: str) -> dict:
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
    value = max(1, round(float(budget_daily)))
    overrides = get_ads_overrides(site_id)
    overrides["budget"] = {**overrides["budget"], str(campaign_id): value}
    set_state(site_id, "adsOverrides", overrides)
    return value


def add_negative(site_id: str, term: str, match_type: str, campaign_id=None) -> list[dict]:
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
    cross-reference from SEODaily. Honest 0 for conv_value/ga4_revenue — no revenue or
    conversion-value column exists on either table."""
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            row = session.execute(
                select(
                    func.sum(AdMetricDaily.spend).label("spend"),
                    func.sum(AdMetricDaily.clicks).label("clicks"),
                    func.sum(AdMetricDaily.impressions).label("impressions"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                ).where(AdMetricDaily.site_id.in_(site_ids), AdMetricDaily.date >= start, AdMetricDaily.date <= end)
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
                    AdMetricDaily.site_id.in_(site_ids), AdMetricDaily.date >= start, AdMetricDaily.date <= end,
                    AdMetricDaily.roas.isnot(None),
                )
            ).first()
            known_roas_spend = float(weighted.known_roas_spend or 0)
            # Weighted average over only the rows that actually report a roas -- spend with
            # roas=None must NOT count toward the denominator, or the result silently
            # understates roas (fabrication by omission).
            roas = float(weighted.weighted_roas_sum or 0) / known_roas_spend if known_roas_spend else 0.0

            ga4_row = session.execute(
                select(func.sum(SEODaily.conversions)).where(
                    SEODaily.site_id.in_(site_ids), SEODaily.date >= start, SEODaily.date <= end
                )
            ).scalar()
            ga4_key_events = float(ga4_row or 0)
    except Exception as e:
        logger.error(f"query_ads_totals_raw error: {e}", exc_info=True)
        return {"spend": 0.0, "clicks": 0.0, "impressions": 0.0, "conversions": 0.0,
                "cpc": 0.0, "roas": 0.0, "conv_value": 0.0, "ga4_key_events": 0.0, "ga4_revenue": 0.0}

    return {
        "spend": spend, "clicks": clicks, "impressions": impressions, "conversions": conversions,
        # Derived ratios are returned at full precision -- rounding here would silently
        # disagree with the numerator/denominator shipped alongside them.
        "cpc": spend / clicks if clicks else 0.0,
        "roas": roas,
        "conv_value": 0.0,  # no revenue/conversion-value column exists on AdMetricDaily
        "ga4_key_events": ga4_key_events,
        "ga4_revenue": 0.0,  # no revenue column exists on SEODaily
    }


def query_ads_trend_raw(site_id: str, start: date, end: date) -> list[dict]:
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            ads_rows = session.execute(
                select(
                    AdMetricDaily.date,
                    func.sum(AdMetricDaily.spend).label("spend"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                ).where(AdMetricDaily.site_id.in_(site_ids), AdMetricDaily.date >= start, AdMetricDaily.date <= end)
                .group_by(AdMetricDaily.date).order_by(AdMetricDaily.date)
            ).all()
            ads_by_date = {r.date: (float(r.spend or 0), float(r.conversions or 0)) for r in ads_rows}

            ga4_rows = session.execute(
                select(SEODaily.date, func.sum(SEODaily.conversions).label("conversions"))
                .where(SEODaily.site_id.in_(site_ids), SEODaily.date >= start, SEODaily.date <= end)
                .group_by(SEODaily.date).order_by(SEODaily.date)
            ).all()
            ga4_by_date = {r.date: float(r.conversions or 0) for r in ga4_rows}
    except Exception as e:
        logger.error(f"query_ads_trend_raw error: {e}", exc_info=True)
        return []

    all_dates = sorted(set(ads_by_date) | set(ga4_by_date))
    if not all_dates:
        # Build daily trend curve across requested range
        days_span = max(1, (end - start).days + 1)
        for i in range(days_span):
            all_dates.append(start + timedelta(days=i))

    out = []
    for d in all_dates:
        sp, conv = ads_by_date.get(d, (0.0, 0.0))
        g_conv = ga4_by_date.get(d, 0.0)

        out.append({
            "date": d.isoformat(),
            "spend": round(sp, 2),
            "conversions": round(conv, 1),
            "ga4_key_events": g_conv,
        })
    return out


def query_ads_pacing_raw(site_id: str) -> dict:
    """Real calendar-month-to-date spend + honest-zero budget/projection math. Always
    'this calendar month' -- independent of the range param, matching the SPA's
    'day X of Y' label."""
    site_ids = _resolve_site_ids(site_id)
    today = date.today()
    month_start = today.replace(day=1)
    try:
        with get_session() as session:
            row = session.execute(
                select(func.sum(AdMetricDaily.spend)).where(
                    AdMetricDaily.site_id.in_(site_ids), AdMetricDaily.date >= month_start, AdMetricDaily.date <= today
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

    # No budget-setting feature exists anywhere in this codebase and Google Ads budgets are
    # not persisted by the connector, so there is no honest number to report here. pct then
    # falls out as 0 rather than a percentage of an invented denominator.
    monthly_budget = 0.0
    projected = (mtd_spend / day_of_month * days_in_month) if day_of_month else 0.0
    pct = min(100, round(mtd_spend / monthly_budget * 100)) if monthly_budget else 0

    # Per-channel pacing is a spend-against-budget breakdown; with no budget source there is
    # nothing to pace against, so this stays honestly empty rather than shipping rows whose
    # budget field is a placeholder zero.
    channels = []

    return {
        "monthly_budget": monthly_budget, "mtd_spend": mtd_spend, "projected": projected,
        "day_of_month": day_of_month, "days_in_month": days_in_month, "pct": pct,
        "channels": channels,
    }


def query_ads_search_terms_raw(site_id: str, start: date, end: date) -> list[dict]:
    """Real AdSearchTerm rows, rolled up to one row per (term, campaign) for the window.

    Shaped exactly as the SPA's Search Terms tab reads it: id, term, matchedKeyword,
    matchType, campaign, campaignId, impressions, clicks, cost, conversions, cpa, status.

    `cpa` is None (not 0) when a term produced no conversions — cost-per-acquisition of zero
    acquisitions is undefined, and the SPA already renders None as an em dash.
    `status` is derived by the existing `_search_term_status()` against the user's real
    negatives/promoted lists.

    Returns [] when the table is missing or empty — the honest not-connected state, since
    Google Ads Standard Access has not been granted and nothing has ever been written.
    """
    site_ids = _resolve_site_ids(site_id)
    overrides = get_ads_overrides(site_id)
    try:
        with get_session() as session:
            # Ordered ascending by date so the descriptive columns (matched keyword, match
            # type, campaign name) end up holding the MOST RECENT real values for the term:
            # they can legitimately change mid-window, and picking the latest is a real
            # observation rather than an average of two different keywords.
            rows = session.execute(
                select(
                    AdSearchTerm.term, AdSearchTerm.campaign_id, AdSearchTerm.campaign,
                    AdSearchTerm.matched_keyword, AdSearchTerm.match_type,
                    AdSearchTerm.impressions, AdSearchTerm.clicks,
                    AdSearchTerm.cost, AdSearchTerm.conversions,
                ).where(
                    AdSearchTerm.site_id.in_(site_ids),
                    AdSearchTerm.date >= start, AdSearchTerm.date <= end,
                ).order_by(AdSearchTerm.date)
            ).all()
    except Exception as e:
        logger.warning(f"query_ads_search_terms_raw error: {e}")
        return []

    merged: dict[tuple, dict] = {}
    for r in rows:
        key = (r.term, r.campaign_id)
        agg = merged.get(key)
        if agg is None:
            agg = merged[key] = {
                # Stable, deterministic row id: the SPA keys checkbox selection and the
                # negative-keyword menu off it, and it must survive a refetch. The natural
                # key already is (term, campaign) after the roll-up, so no counter is needed.
                "id": f"{r.campaign_id or ''}|{r.term}",
                "term": r.term,
                "impressions": 0, "clicks": 0, "cost": 0.0, "conversions": 0.0,
            }
        agg["matchedKeyword"] = r.matched_keyword or ""
        agg["matchType"] = r.match_type
        agg["campaign"] = r.campaign
        agg["campaignId"] = r.campaign_id
        agg["impressions"] += int(r.impressions or 0)
        agg["clicks"] += int(r.clicks or 0)
        agg["cost"] += float(r.cost or 0.0)
        agg["conversions"] += float(r.conversions or 0.0)

    out = []
    for agg in merged.values():
        conversions = agg["conversions"]
        cost = round(agg["cost"], 2)
        agg["cost"] = cost
        agg["conversions"] = round(conversions, 2)
        agg["cpa"] = round(cost / conversions, 2) if conversions else None
        agg["status"] = _search_term_status(agg, overrides["negatives"], overrides["promoted"])
        out.append(agg)

    out.sort(key=lambda t: (-t["cost"], t["term"]))
    return out


def _norm_campaign(name) -> str:
    """Join key for matching a Google Ads campaign name against a GA4 sessionCampaignName.

    Case- and whitespace-insensitive only. Nothing fuzzier: a near-match heuristic that
    merged two genuinely different campaigns would silently manufacture the very agreement
    this table exists to measure.
    """
    return (name or "").strip().lower()


def query_ads_attribution_raw(site_id: str, start: date, end: date) -> list[dict]:
    """Per-campaign Google Ads (last click) vs GA4 (cross-channel) comparison.

    Shape per row, as the SPA's Attribution tab reads it:
        id, name, platform, ads_conversions, ga4_key_events, ads_value, ga4_revenue, gap_pct

    Campaign-matching rule
    ----------------------
    1. The table requires BOTH halves to have rows in the window. If either side contributed
       nothing, return [] and let the page show its empty state. Rendering the surviving half
       against a wall of zeros would report a 100% attribution gap for every campaign — a
       fabricated finding about attribution, when the truth is simply that one connector has
       not run. (With no Google Ads credentials this is exactly what happens, and it is why
       the page stays clean rather than accusing GA4 of losing every conversion.)
    2. Given both halves, rows are the FULL OUTER JOIN of campaign names on `_norm_campaign`.
       A campaign present on one side only is kept — never dropped — because "Ads spent here
       and GA4 saw nothing" is a real, actionable attribution finding.
    3. The absent side of such a row is None, never 0, and `gap_pct` is None with it. Zero
       would assert "GA4 measured no key events"; None says "GA4 has no row for this name",
       which is the only thing actually known. `matched` and `sources` are carried alongside
       so a consumer can tell the two apart without inspecting the numbers.
    4. `gap_pct` is also None when the campaign matched but recorded 0 Ads conversions — the
       percentage difference from zero is undefined, not 0%.
    """
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            ads_rows = session.execute(
                select(
                    AdMetricDaily.campaign,
                    AdMetricDaily.platform,
                    func.min(AdMetricDaily.campaign_id).label("campaign_id"),
                    func.sum(AdMetricDaily.conversions).label("conversions"),
                    # Conversion value is not a column; it is reconstructible as spend * roas
                    # for exactly the rows that carry a roas. Rows with roas IS NULL
                    # contribute nothing and are counted separately so an all-NULL campaign
                    # reports None instead of a $0.00 that looks measured.
                    func.sum(case((AdMetricDaily.roas.isnot(None),
                                   AdMetricDaily.spend * AdMetricDaily.roas), else_=0.0)).label("value"),
                    func.sum(case((AdMetricDaily.roas.isnot(None), 1), else_=0)).label("value_rows"),
                ).where(
                    AdMetricDaily.site_id.in_(site_ids),
                    AdMetricDaily.date >= start, AdMetricDaily.date <= end,
                ).group_by(AdMetricDaily.campaign, AdMetricDaily.platform)
            ).all()

            ga4_rows = session.execute(
                select(
                    GA4CampaignDaily.campaign,
                    func.sum(GA4CampaignDaily.key_events).label("key_events"),
                    func.sum(GA4CampaignDaily.revenue).label("revenue"),
                ).where(
                    GA4CampaignDaily.site_id.in_(site_ids),
                    GA4CampaignDaily.date >= start, GA4CampaignDaily.date <= end,
                ).group_by(GA4CampaignDaily.campaign)
            ).all()
    except Exception as e:
        logger.warning(f"query_ads_attribution_raw error: {e}")
        return []

    # Rule 1 — one-sided data is not a comparison.
    if not ads_rows or not ga4_rows:
        return []

    ads_by_key: dict[str, dict] = {}
    for r in ads_rows:
        key = _norm_campaign(r.campaign)
        if not key:
            continue
        ads_by_key[key] = {
            "id": r.campaign_id,
            "name": r.campaign,
            # platformChip() in the SPA compares against 'Meta'; AdMetricDaily stores the
            # lowercase platform slug, so title-case it to the label the chip expects.
            "platform": (r.platform or "").title() or None,
            "ads_conversions": float(r.conversions or 0),
            "ads_value": round(float(r.value or 0.0), 2) if int(r.value_rows or 0) else None,
        }

    ga4_by_key: dict[str, dict] = {}
    for r in ga4_rows:
        key = _norm_campaign(r.campaign)
        if not key:
            continue
        ga4_by_key[key] = {
            "name": r.campaign,
            "ga4_key_events": float(r.key_events or 0),
            "ga4_revenue": round(float(r.revenue or 0.0), 2),
        }

    out = []
    for key in list(ads_by_key) + [k for k in ga4_by_key if k not in ads_by_key]:
        ads = ads_by_key.get(key)
        ga4 = ga4_by_key.get(key)

        ads_conv = ads["ads_conversions"] if ads else None
        ga4_conv = ga4["ga4_key_events"] if ga4 else None
        gap_pct = (
            round((ga4_conv - ads_conv) / ads_conv * 100)
            if (ads and ga4 and ads_conv) else None
        )

        out.append({
            "id": ads["id"] if ads else None,
            "name": ads["name"] if ads else ga4["name"],
            # A GA4-only campaign name carries no platform: GA4 sees campaigns from every ad
            # network, so guessing 'Google' would be an invention.
            "platform": ads["platform"] if ads else None,
            "ads_conversions": ads_conv,
            "ga4_key_events": ga4_conv,
            "ads_value": ads["ads_value"] if ads else None,
            "ga4_revenue": ga4["ga4_revenue"] if ga4 else None,
            "gap_pct": gap_pct,
            # Additive to the shape the SPA reads; lets any consumer distinguish "measured
            # zero" from "no row on that side" without re-deriving it from the Nones.
            "matched": bool(ads and ga4),
            "sources": (["ads"] if ads else []) + (["ga4"] if ga4 else []),
        })

    out.sort(key=lambda r: (-(r["ads_conversions"] or 0), -(r["ga4_key_events"] or 0), r["name"]))
    return out


def build_ads_response(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date) -> dict:
    """API-shaped Ads response. Real: totals, prev, trend, pacing, window, negatives (real
    user-entered overrides), searchTerms (AdSearchTerm), attribution (AdMetricDaily joined to
    GA4CampaignDaily) and syncMeta.connected. Honest []: campaigns, landingPages -- no
    backing schema exists for the per-row fields those tabs need, and inventing them would be
    worse than a visible gap.

    searchTerms and attribution are [] whenever their tables are empty, which is the current
    state: Google Ads Standard Access has not been granted, so no search term has ever been
    written and the attribution join has no Ads half to compare against. The moment
    credentials land and the connectors run, both populate with no further code change.

    IMPORTANT: totals/prev/pacing/syncMeta must stay REAL fully-keyed objects with honest
    zero/None values -- never a bare {"state": "setup"} sentinel. The SPA's Ads block has no
    setup guard and will crash (TypeError on .toFixed()/.map()) on a sentinel object."""
    totals = query_ads_totals_raw(site_id, curr_start, curr_end)
    prev = query_ads_totals_raw(site_id, prev_start, prev_end)
    trend = query_ads_trend_raw(site_id, curr_start, curr_end)
    pacing = query_ads_pacing_raw(site_id)
    overrides = get_ads_overrides(site_id)

    tot_spend = totals.get("spend", 0.0)

    # A campaign row in the SPA is status/type/daily budget/conversion value/impression
    # share lost/ad groups -- none of which AdMetricDaily stores. Reshaping the daily spend
    # aggregate into that shape means inventing every field that makes it a campaign record,
    # so the list stays honestly empty until a real campaign-level sync exists.
    campaigns = []

    search_terms = query_ads_search_terms_raw(site_id, curr_start, curr_end)
    attribution = query_ads_attribution_raw(site_id, curr_start, curr_end)

    # The Ads landing-page tab is paid traffic: clicks, spend, revenue and roas per landing
    # page. SEODaily holds organic sessions and has no spend or revenue column, so filling
    # this table from it would relabel organic sessions as ad clicks and pad the rest with
    # zeros. Honestly empty until the Ads connector persists landing-page performance.
    landing_pages = []

    connected = bool(os.getenv("GOOGLE_ADS_CUSTOMER_ID") and os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")) or tot_spend > 0

    return {
        "totals": totals,
        "prev": prev,
        "trend": trend,
        "pacing": pacing,
        "campaigns": campaigns,
        "searchTerms": search_terms,
        "attribution": attribution,
        "landingPages": landing_pages,
        "negatives": overrides["negatives"],
        "window": {"from": curr_start.isoformat(), "to": curr_end.isoformat(), "days": (curr_end - curr_start).days + 1},
        # connected is the one real signal here: Google Ads credentials are configured, or a
        # previous sync actually landed spend rows. Cadence/pull timestamps and the Ads
        # ops / GA4 token quota counters are not recorded anywhere, so they are None/0
        # rather than plausible-looking numbers the user would read as their real quota.
        "syncMeta": {
            "connected": connected,
            "cadence": None, "last_pull": None, "next_pull": None,
            "ops_used": 0, "ops_limit": 0, "ga4_tokens_used": 0, "ga4_tokens_limit": 0,
        },
    }
