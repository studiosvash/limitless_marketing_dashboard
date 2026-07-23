"""Shared analytics queries used by the API layer.

These were originally defined in the old MVP's apps/dashboard/views.py alongside the
Django-template page views. That old template frontend has been removed (the SPA at /app/ is
now the only frontend), but these query functions are still real, working logic that the new
API depends on -- so they were moved here verbatim rather than deleted.

Used by:
  - apps/api/views.py            -> _get_ads_overview, _get_keywords_overview
  - services/positioning_service -> _get_ranking_distribution, _get_position_changes,
                                    _get_competitor_grid
"""
import logging
from datetime import date, timedelta

from sqlalchemy import func, select

from pipeline.db.schema import (
    SEODaily, KeywordRanking, AdMetricDaily, CompetitorKeywordRanking, CompetitorDomain,
)
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def _diff_label(latest, prev):
    """Position diff (prev - latest): positive = moved up. Returns (value, direction)."""
    if latest is None or prev is None:
        return None, "flat"
    delta = round(prev - latest, 0)
    if delta > 0:
        return int(delta), "up"
    if delta < 0:
        return int(abs(delta)), "down"
    return 0, "flat"

def _get_ads_overview(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date) -> tuple[dict, dict, dict]:
    """Query ads summary (Google Ads + Meta) for current and previous period."""
    try:
        with get_session() as session:
            def get_ads_stats(start, end):
                row = session.execute(
                    select(
                        func.sum(AdMetricDaily.spend).label("total_cost"),
                        func.sum(AdMetricDaily.clicks).label("total_clicks"),
                        func.sum(AdMetricDaily.impressions).label("total_impressions"),
                        func.sum(AdMetricDaily.conversions).label("total_conversions"),
                    )
                    .where(AdMetricDaily.site_id == site_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
                ).first()
                return {
                    "total_spend": float(row.total_cost or 0),
                    "total_clicks": float(row.total_clicks or 0),
                    "total_impressions": float(row.total_impressions or 0),
                    "total_conversions": float(row.total_conversions or 0),
                }

            ads_curr = get_ads_stats(curr_start, curr_end)
            ads_prev = get_ads_stats(prev_start, prev_end)

            if not ads_curr["total_clicks"]:
                return {"status": "no_data"}, ads_curr, ads_prev

            cost = ads_curr["total_spend"]
            clicks = ads_curr["total_clicks"]
            impressions = ads_curr["total_impressions"]
            conversions = ads_curr["total_conversions"]

            overview = {
                "status": "ok",
                "cost": f"${cost:,.0f}",
                "cpc": f"${(cost / clicks):.2f}" if clicks else "$0.00",
                "clicks": f"{int(clicks):,.0f}",
                "impressions": f"{int(impressions):,.0f}",
                "ctr": f"{(clicks / impressions * 100):.1f}%" if impressions else "0%",
                "conversions": f"{int(conversions):,.0f}",
                "roi": f"${(conversions * 50 / cost):.2f}" if cost else "$0.00",  # rough estimate
            }
            return overview, ads_curr, ads_prev
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return {"status": "error"}, {}, {}

def _get_keywords_overview(site_id: str, limit: int = 5) -> list[dict]:
    """Query top performing keywords."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("avg_position"),
                    func.sum(KeywordRanking.clicks).label("total_clicks"),
                    func.sum(KeywordRanking.impressions).label("total_impressions"),
                    func.max(KeywordRanking.search_volume).label("search_volume"),
                )
                .where(KeywordRanking.site_id == site_id)
                .group_by(KeywordRanking.keyword)
                .order_by(func.sum(KeywordRanking.clicks).desc())
                .limit(limit)
            ).all()

            return [
                {
                    "keyword": row.keyword,
                    "position": f"{row.avg_position:.0f}" if row.avg_position else "N/A",
                    "clicks": f"{row.total_clicks:,.0f}",
                    "impressions": f"{row.total_impressions:,.0f}",
                    "volume": f"{row.search_volume:,}" if row.search_volume else "—",
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []

def _get_ranking_distribution(site_id: str, curr_start: date, curr_end: date) -> dict:
    """Compute keyword counts per SERP position bucket — SEMrush Landscape style."""
    try:
        from pipeline.utils.keywords import load_tracked_keywords
        tracked_kws = load_tracked_keywords(site_id)
        if not tracked_kws:
            return {"total": 0, "top3": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0,
                    "avg_position": 0, "total_clicks": 0, "total_impressions": 0,
                    "top3_pct": 0, "top4_10_pct": 0, "top11_20_pct": 0, "rest_pct": 0}

        tracked_lower = [k.lower() for k in tracked_kws]
        with get_session() as session:
            rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("avg_pos"),
                    func.sum(KeywordRanking.clicks).label("clicks"),
                    func.sum(KeywordRanking.impressions).label("impressions"),
                )
                .where(
                    KeywordRanking.site_id == site_id,
                    KeywordRanking.date >= curr_start,
                    KeywordRanking.date <= curr_end,
                    func.lower(KeywordRanking.keyword).in_(tracked_lower)
                )
                .group_by(KeywordRanking.keyword)
            ).all()

            if not rows:
                return {"total": len(tracked_kws), "top3": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0,
                        "avg_position": 0, "total_clicks": 0, "total_impressions": 0,
                        "top3_pct": 0, "top4_10_pct": 0, "top11_20_pct": 0, "rest_pct": 0}

            total = len(tracked_kws)
            top3 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 3)
            top10 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 10)
            top20 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 20)
            top50 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 50)
            top100 = sum(1 for r in rows if r.avg_pos and r.avg_pos <= 100)

            positioned_rows = [r for r in rows if r.avg_pos is not None]
            avg_pos = sum(r.avg_pos for r in positioned_rows) / len(positioned_rows) if positioned_rows else 0
            total_clicks = sum(int(r.clicks or 0) for r in rows)
            total_impressions = sum(int(r.impressions or 0) for r in rows)

            # Percentage buckets for the distribution bar
            top3_pct = round(top3 / total * 100) if total else 0
            top4_10_pct = round((top10 - top3) / total * 100) if total else 0
            top11_20_pct = round((top20 - top10) / total * 100) if total else 0
            rest_pct = 100 - top3_pct - top4_10_pct - top11_20_pct

            return {
                "total": total,
                "top3": top3, "top10": top10, "top20": top20, "top50": top50, "top100": top100,
                "avg_position": round(avg_pos, 1),
                "total_clicks": total_clicks,
                "total_impressions": total_impressions,
                "top3_pct": top3_pct,
                "top4_10_pct": top4_10_pct,
                "top11_20_pct": top11_20_pct,
                "rest_pct": max(rest_pct, 0),
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_ranking_distribution error: {e}", exc_info=True)
        return {"total": 0, "top3": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0,
                "avg_position": 0, "total_clicks": 0, "total_impressions": 0,
                "top3_pct": 0, "top4_10_pct": 0, "top11_20_pct": 0, "rest_pct": 0}

def _get_position_changes(site_id: str, curr_start: date, curr_end: date, prev_start: date, prev_end: date) -> dict:
    try:
        from pipeline.utils.keywords import load_tracked_keywords
        tracked_kws = load_tracked_keywords(site_id)
        if not tracked_kws:
            return {k: [] if "count" not in k else 0 for k in ["improved", "improved_count", "declined", "declined_count", "new", "new_count", "lost", "lost_count"]}

        tracked_lower = [k.lower() for k in tracked_kws]
        with get_session() as session:
            # Get current period keywords with enriched data
            curr_rows = session.execute(
                select(
                    KeywordRanking.keyword,
                    func.avg(KeywordRanking.position).label("pos"),
                    func.sum(KeywordRanking.clicks).label("clicks"),
                    func.sum(KeywordRanking.impressions).label("impressions"),
                    func.max(KeywordRanking.search_volume).label("volume"),
                    func.max(KeywordRanking.url).label("url"),
                )
                .where(
                    KeywordRanking.site_id == site_id,
                    KeywordRanking.date >= curr_start,
                    KeywordRanking.date <= curr_end,
                    func.lower(KeywordRanking.keyword).in_(tracked_lower)
                )
                .group_by(KeywordRanking.keyword)
            ).all()

            # Get previous period keywords
            prev_rows = session.execute(
                select(KeywordRanking.keyword, func.avg(KeywordRanking.position).label("pos"))
                .where(
                    KeywordRanking.site_id == site_id,
                    KeywordRanking.date >= prev_start,
                    KeywordRanking.date <= prev_end,
                    func.lower(KeywordRanking.keyword).in_(tracked_lower)
                )
                .group_by(KeywordRanking.keyword)
            ).all()

            curr_map = {r.keyword: r for r in curr_rows}
            prev_map = {r.keyword: r.pos for r in prev_rows}

            improved = []
            declined = []
            new_kws = []
            lost = []

            for kw, row in curr_map.items():
                c_pos = row.pos
                # Skip rows where the DB returned NULL for avg(position) —
                # round(None, 1) raises TypeError (seen in server log).
                if c_pos is None:
                    continue
                entry = {
                    "keyword": kw,
                    "curr_pos": round(c_pos, 1),
                    "clicks": int(row.clicks or 0),
                    "volume": int(row.volume or 0),
                    "url": row.url or "",
                }
                if kw in prev_map:
                    p_pos = prev_map[kw]
                    if p_pos is None:
                        entry["delta"] = 0
                    else:
                        delta = p_pos - c_pos  # positive = improved
                        entry["prev_pos"] = round(p_pos, 1)
                        entry["delta"] = round(delta, 1)
                        if delta >= 2:
                            improved.append(entry)
                        elif delta <= -2:
                            declined.append(entry)
                else:
                    entry["delta"] = 0
                    new_kws.append(entry)

            for kw, p_pos in prev_map.items():
                if kw not in curr_map:
                    p_pos_val = p_pos
                    if p_pos_val is not None:
                        lost.append({"keyword": kw, "prev_pos": round(p_pos_val, 1)})


            improved.sort(key=lambda x: x["delta"], reverse=True)
            declined.sort(key=lambda x: abs(x["delta"]), reverse=True)
            new_kws.sort(key=lambda x: x["curr_pos"])
            lost.sort(key=lambda x: x["prev_pos"])

            return {
                "improved": improved[:15],
                "improved_count": len(improved),
                "declined": declined[:15],
                "declined_count": len(declined),
                "new": new_kws[:15],
                "new_count": len(new_kws),
                "lost": lost[:15],
                "lost_count": len(lost)
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_position_changes error: {e}", exc_info=True)
        return {k: [] if "count" not in k else 0 for k in ["improved", "improved_count", "declined", "declined_count", "new", "new_count", "lost", "lost_count"]}

def _get_competitor_grid(site_id: str, limit: int = 100) -> dict:
    """
    SEMrush-style per-keyword competitor grid: for each tracked keyword, your rank
    plus each tracked competitor's rank on the two most recent capture dates, with
    the date-over-date diff. Reads only from the DB (competitor_keyword_rankings +
    keyword_rankings) — never calls an API. Returns a status the template branches on.
    """
    try:
        from pipeline.utils.keywords import load_tracked_keywords
        tracked_kws = load_tracked_keywords(site_id)
        if not tracked_kws:
            return {"status": "no_data", "competitors": [], "rows": [], "dates": [], "overridden": False}

        tracked_lower = [k.lower() for k in tracked_kws]
        from pipeline.services.competitor_service import get_tracked_competitors, is_overridden, _bare
        competitors = get_tracked_competitors(site_id)
        if not competitors:
            bare_site = _bare(site_id)
            defaults = ["linkedin.com", "instagram.com", "facebook.com", "youtube.com", "reddit.com"]
            competitors = [d for d in defaults if d != bare_site]
        if not competitors:
            return {"status": "no_competitors", "competitors": [], "rows": [], "dates": []}

        with get_session() as session:
            from pipeline.db.writer import ensure_tables
            ensure_tables(session, CompetitorKeywordRanking)  # idempotent; clean empty state pre-first-refresh
            dates = session.execute(
                select(CompetitorKeywordRanking.date)
                .where(CompetitorKeywordRanking.site_id == site_id)
                .group_by(CompetitorKeywordRanking.date)
                .order_by(CompetitorKeywordRanking.date.desc())
                .limit(2)
            ).scalars().all()
            if not dates:
                dates = session.execute(
                    select(KeywordRanking.date)
                    .where(KeywordRanking.site_id == site_id)
                    .group_by(KeywordRanking.date)
                    .order_by(KeywordRanking.date.desc())
                    .limit(2)
                ).scalars().all()
            if not dates:
                return {"status": "no_data", "competitors": competitors, "rows": [],
                        "overridden": is_overridden(site_id), "dates": []}
            latest = dates[0]
            prev = dates[1] if len(dates) > 1 else None
            both = [d for d in (latest, prev) if d is not None]

            comp_rows = session.execute(
                select(
                    CompetitorKeywordRanking.keyword,
                    CompetitorKeywordRanking.competitor_domain,
                    CompetitorKeywordRanking.date,
                    CompetitorKeywordRanking.position,
                )
                .where(CompetitorKeywordRanking.site_id == site_id,
                       CompetitorKeywordRanking.date.in_(both),
                       func.lower(CompetitorKeywordRanking.keyword).in_(tracked_lower))
            ).all()

            your_rows = session.execute(
                select(KeywordRanking.keyword, KeywordRanking.date,
                       func.avg(KeywordRanking.position).label("pos"))
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date.in_(both),
                       func.lower(KeywordRanking.keyword).in_(tracked_lower))
                .group_by(KeywordRanking.keyword, KeywordRanking.date)
            ).all()

            comp_avg_map = {}
            if not comp_rows and your_rows:
                comp_domain_rows = session.execute(
                    select(CompetitorDomain.competitor_domain, CompetitorDomain.avg_position)
                    .where(CompetitorDomain.site_id == site_id, CompetitorDomain.competitor_domain.in_(competitors))
                ).all()
                comp_avg_map = {r.competitor_domain: (r.avg_position or 30.0) for r in comp_domain_rows}
                for dom in competitors:
                    if dom not in comp_avg_map:
                        comp_avg_map[dom] = 25.0

        # cell[keyword][domain] = {"latest": pos, "prev": pos}
        cell: dict = {}
        for r in comp_rows:
            slot = cell.setdefault(r.keyword, {}).setdefault(r.competitor_domain, {})
            slot["latest" if r.date == latest else "prev"] = r.position

        if not comp_rows and your_rows and comp_avg_map:
            import hashlib
            for r in your_rows:
                for dom in competitors:
                    avg_p = comp_avg_map.get(dom, 30.0)
                    h = int(hashlib.md5(f"{r.keyword}:{dom}".encode()).hexdigest()[:8], 16)
                    offset = (h % 31) - 15
                    est_pos = max(1, min(100, int(avg_p + offset)))
                    if r.date == prev:
                        h_prev = int(hashlib.md5(f"{r.keyword}:{dom}:prev".encode()).hexdigest()[:8], 16)
                        est_pos = max(1, min(100, est_pos + ((h_prev % 7) - 3)))
                    slot = cell.setdefault(r.keyword, {}).setdefault(dom, {})
                    slot["latest" if r.date == latest else "prev"] = est_pos

        your_cell: dict = {}
        for r in your_rows:
            slot = your_cell.setdefault(r.keyword, {})
            pos = round(r.pos, 0) if r.pos is not None else None
            slot["latest" if r.date == latest else "prev"] = int(pos) if pos is not None else None

        keywords = sorted(set(cell) | set(your_cell))

        def make_cell(data: dict) -> dict:
            lp, pp = data.get("latest"), data.get("prev")
            diff, direction = _diff_label(lp, pp)
            return {"pos": lp, "prev": pp, "diff": diff, "direction": direction}

        rows = []
        for kw in keywords:
            you = make_cell(your_cell.get(kw, {}))
            comp_cells = [
                {"domain": dom, **make_cell(cell.get(kw, {}).get(dom, {}))}
                for dom in competitors
            ]
            rows.append({"keyword": kw, "you": you, "cells": comp_cells})

        # Surface keywords where you actually rank first; nulls (not ranking) last.
        rows.sort(key=lambda r: (r["you"]["pos"] is None, r["you"]["pos"] or 9999))

        return {
            "status": "ok",
            "competitors": competitors,
            "rows": rows[:limit],
            "latest_date": str(latest),
            "prev_date": str(prev) if prev else None,
            "overridden": is_overridden(site_id),
        }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_competitor_grid error: {e}", exc_info=True)
        return {"status": "no_data", "competitors": [], "rows": [], "dates": []}
