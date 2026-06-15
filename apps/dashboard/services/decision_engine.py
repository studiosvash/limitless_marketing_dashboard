"""
fusehealth/apps/dashboard/services/decision_engine.py

Generates actionable decision signals derived from real metric comparisons.
This is the intelligence layer:
- Positive signals (What's Working)
- Negative signals (Needs Attention)
- Opportunity signals (Actionable Advice)
"""

from typing import Optional


def compute_delta(current: float, previous: float) -> dict:
    """Helper to compute percentage difference."""
    if not previous or previous == 0:
        return {"has_data": False, "pct_change": 0, "formatted": "0%"}
    
    pct_change = ((current - previous) / previous) * 100
    direction = "up" if pct_change > 0 else "down" if pct_change < 0 else "flat"
    formatted = f"{abs(pct_change):.1f}%"
    return {"has_data": True, "pct_change": pct_change, "formatted": formatted, "direction": direction}


def generate_signals(
    seo_curr: dict,
    seo_prev: dict,
    ads_curr: Optional[dict] = None,
    ads_prev: Optional[dict] = None,
) -> list[dict]:
    """
    Generate actionable signals from real metric data.
    Only generates signals when there is actual data to compare.
    """
    signals = []

    # ── SEO Signals ──
    if seo_curr and seo_prev and seo_prev.get("clicks", 0) > 0:
        clicks_delta = compute_delta(
            seo_curr.get("clicks", 0),
            seo_prev.get("clicks", 0)
        )
        if clicks_delta["pct_change"] > 10:
            signals.append({
                "type":   "positive",
                "title":  f"Organic traffic up {clicks_delta['formatted']}",
                "detail": f"Clicks grew from {int(seo_prev.get('clicks',0)):,} to "
                          f"{int(seo_curr.get('clicks',0)):,}. "
                          "Review your top pages to understand what's driving growth.",
            })
        elif clicks_delta["pct_change"] < -10:
            signals.append({
                "type":   "negative",
                "title":  f"Organic traffic dropped {clicks_delta['formatted']}",
                "detail": f"Clicks fell from {int(seo_prev.get('clicks',0)):,} to "
                          f"{int(seo_curr.get('clicks',0)):,}. "
                          "Check for ranking drops, indexing issues, or algorithm changes.",
            })

        # CTR signal
        ctr_curr = seo_curr.get("ctr", 0)
        ctr_prev = seo_prev.get("ctr", 0)
        if ctr_prev > 0:
            ctr_delta = compute_delta(ctr_curr, ctr_prev)
            if ctr_delta["pct_change"] < -15:
                signals.append({
                    "type":   "negative",
                    "title":  f"CTR declined {ctr_delta['formatted']}",
                    "detail": f"Average CTR dropped from {(ctr_prev*100):.2f}% to {(ctr_curr*100):.2f}%. "
                              "Review title tags and meta descriptions for your top impression pages.",
                })
            elif ctr_delta["pct_change"] > 15:
                signals.append({
                    "type":   "positive",
                    "title":  f"CTR improved {ctr_delta['formatted']}",
                    "detail": f"Average CTR up from {(ctr_prev*100):.2f}% to {(ctr_curr*100):.2f}%. "
                              "Recent title/meta optimizations are working — apply to more pages.",
                })

        # Position signal
        pos_curr = seo_curr.get("avg_position", 0)
        pos_prev = seo_prev.get("avg_position", 0)
        if pos_prev > 0 and pos_curr > 0:
            pos_delta = compute_delta(pos_curr, pos_prev)
            if pos_delta["pct_change"] > 10:  # Position number went up = got worse
                signals.append({
                    "type":   "negative",
                    "title":  f"Average ranking dropped (pos {pos_prev:.1f} → {pos_curr:.1f})",
                    "detail": "Rankings are declining on average. "
                              "Audit your most important keywords for ranking drops and competitor movement.",
                })
            elif pos_delta["pct_change"] < -10:  # Position number went down = improved
                signals.append({
                    "type":   "positive",
                    "title":  f"Rankings improving (pos {pos_prev:.1f} → {pos_curr:.1f})",
                    "detail": "Average position is improving. "
                              "Continue your current SEO strategy and watch for page 1 breakthroughs.",
                })

    # ── Ads Signals ──
    if ads_curr and ads_prev and ads_prev.get("total_spend", 0) > 0:
        spend_delta = compute_delta(
            ads_curr.get("total_spend", 0),
            ads_prev.get("total_spend", 0)
        )
        conv_delta = compute_delta(
            ads_curr.get("total_conversions", 0),
            ads_prev.get("total_conversions", 0)
        )

        # Spend spike without conversion lift = efficiency problem
        if spend_delta["pct_change"] > 20 and conv_delta["pct_change"] < 5:
            signals.append({
                "type":   "negative",
                "title":  f"Ad spend up {spend_delta['formatted']} but conversions flat",
                "detail": f"Spend increased to ${ads_curr.get('total_spend',0):,.2f} "
                          f"but conversions only at {int(ads_curr.get('total_conversions',0)):,}. "
                          "Review campaign targeting and bid strategies for efficiency.",
            })
        elif conv_delta["pct_change"] > 15:
            signals.append({
                "type":   "positive",
                "title":  f"Ad conversions up {conv_delta['formatted']}",
                "detail": f"Conversions grew from {int(ads_prev.get('total_conversions',0)):,} "
                          f"to {int(ads_curr.get('total_conversions',0)):,}. "
                          "Identify your top-performing campaigns and scale them.",
            })

    # ── Opportunity Signal ──
    if seo_curr and seo_curr.get("impressions", 0) > 1000:
        impr = seo_curr.get("impressions", 0)
        clicks = seo_curr.get("clicks", 0)
        if impr > 0:
            effective_ctr = (clicks / impr) * 100
            if effective_ctr < 2.0:
                signals.append({
                    "type":   "opportunity",
                    "title":  "Low CTR opportunity — many impressions not converting to clicks",
                    "detail": f"You have {int(impr):,} impressions but only {int(clicks):,} clicks "
                              f"({effective_ctr:.1f}% CTR). "
                              "Optimizing title tags and meta descriptions could unlock significant traffic gains.",
                })

    return signals

def generate_ad_overlap_signals(site_id: str, curr_start, curr_end) -> list[dict]:
    """
    Identify keywords where the site ranks organically in the top 3, 
    but is still spending ad budget on campaigns matching those keywords.
    """
    from pipeline.utils.db_connection import get_session
    from pipeline.db.schema import KeywordRanking, AdMetricDaily
    from sqlalchemy import select, func

    signals = []
    try:
        with get_session() as session:
            # 1. Get organic keywords ranking <= 3
            top_keywords = session.execute(
                select(KeywordRanking.keyword, func.avg(KeywordRanking.position).label("avg_pos"))
                .where(
                    KeywordRanking.site_id == site_id,
                    KeywordRanking.date >= curr_start,
                    KeywordRanking.date <= curr_end
                )
                .group_by(KeywordRanking.keyword)
                .having(func.avg(KeywordRanking.position) <= 3)
            ).all()

            if not top_keywords:
                return signals

            top_kw_dict = {row.keyword.lower(): row.avg_pos for row in top_keywords if row.keyword}

            # 2. Check Ad spend for campaigns matching these keywords
            ad_spend = session.execute(
                select(AdMetricDaily.campaign, func.sum(AdMetricDaily.spend).label("total_spend"))
                .where(
                    AdMetricDaily.site_id == site_id,
                    AdMetricDaily.date >= curr_start,
                    AdMetricDaily.date <= curr_end,
                    AdMetricDaily.spend > 0
                )
                .group_by(AdMetricDaily.campaign)
            ).all()

            for row in ad_spend:
                campaign = (row.campaign or "").lower()
                spend = row.total_spend or 0
                if not campaign or spend == 0:
                    continue
                
                # Check if campaign name matches any top keyword
                for kw, pos in top_kw_dict.items():
                    if kw in campaign:
                        signals.append({
                            "type": "opportunity",
                            "title": f"Ad/Organic Overlap for '{kw}'",
                            "detail": f"You rank organically at position {pos:.1f} for '{kw}', "
                                      f"but spent ${spend:,.2f} on a matching ad campaign ('{row.campaign}'). "
                                      "Consider pausing the ad to see if organic traffic captures the demand.",
                        })
                        # Avoid duplicate signals per campaign
                        break

    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Ad overlap error: {e}", exc_info=True)

    return signals
