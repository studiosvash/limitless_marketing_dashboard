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
    SEODaily, KeywordRanking, AdMetricDaily, CompetitorKeywordRanking,
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
    """Top performing keywords by clicks, as **raw numbers** — never display strings.

    Shape: [{keyword: str, position: float|None, clicks: int|None, impressions: int|None,
             volume: int|None}]

    WHY RAW (changed 2026-07-27). This function used to format every value here, for the
    old Django template that no longer exists:

        "position": f"{row.avg_position:.0f}"   -> "8"  for a true 8.4 average
        "clicks":   f"{row.total_clicks:,.0f}"  -> "1,234"
        "volume":   f"{row.search_volume:,}"    -> "1,234"  / "—" when null

    That destroyed data before any consumer could see it. `build_top_keywords_api()` (the
    only live consumer's adapter) received `8` for an 8.4 average and could not recover the
    decimal, and a comma-formatted count sorts as text — `"1,234" < "9"` is True — so the
    Overview table's columns could not be sorted or compared. A query function's job is to
    return the data; **formatting belongs at the edge that renders it** (the SPA already does
    it via `this.fmt()` / `this.posBadge()`).

    NULL IS NOT ZERO. `avg(position)` and `max(search_volume)` are NULL when no row carries
    one; those become `None`, not `0`, because "we never captured a position" and "this
    keyword ranks at position 0" are different facts and a 0 on screen reads as the second.
    The old sentinels for the same thing were the strings "N/A" and "—". The same applies to
    the click/impression sums: NULL in, `None` out (the old formatter raised TypeError there
    and the whole call fell through to `[]`).

    If a future caller genuinely needs display strings, format them in that caller — do not
    reintroduce formatting here, or the two shapes become two sources of truth again.
    (`apps/dashboard/views_export.py` is the only other reference to this function; it is a
    dead, unrouted module that cannot even import — see skills.md §10.)
    """
    try:
        from pipeline.db.schema import ensure_ranking_location_columns, ensure_ranking_location_keys
        with get_session() as session:
            ensure_ranking_location_columns(session)
            ensure_ranking_location_keys(session)
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
                    # Rounded to 1 dp, matching every other average this codebase reports
                    # (_get_ranking_distribution, _get_position_changes, _avg_position).
                    # 8.4 stays 8.4; the caller decides whether to show it whole.
                    "position": (round(float(row.avg_position), 1)
                                 if row.avg_position is not None else None),
                    "clicks": int(row.total_clicks) if row.total_clicks is not None else None,
                    "impressions": (int(row.total_impressions)
                                    if row.total_impressions is not None else None),
                    "volume": int(row.search_volume) if row.search_volume is not None else None,
                }
                for row in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Error: {e}", exc_info=True)
        return []

def _location_clause(model, location: str | None) -> list:
    """WHERE terms restricting a ranking query to one project's tracking location.

    `location` is the SPA display form stored on `sites.location` and on every ranking row
    (see `KeywordRanking.location`). Passing None returns no terms — every row for the domain,
    which is what a domain-level caller (the Overview page) genuinely wants.

    Why a per-project filter is required and not cosmetic: several projects can track one
    domain in different cities, and they all share `site_id`. Filtering on `site_id` alone
    merges every city's rankings into one set, which is why six Premierstaff projects reported
    the same visibility %, the same keyword count and the same up/down counts. This clause is
    the read-side half of that fix; the write-side half is `location` joining the unique key.

    A project whose city has not been synced yet correctly matches NOTHING. That is the honest
    outcome — it has no measurements in that city — and the page shows its normal empty state.
    Falling back to the domain's other rows would put another city's numbers under this
    project's name, which is the exact bug being removed.
    """
    return [model.location == location] if location else []


def _get_ranking_distribution(site_id: str, curr_start: date, curr_end: date,
                              location: str | None = None,
                              site_pk: int | None = None) -> dict:
    """Compute keyword counts per SERP position bucket — SEMrush Landscape style.

    `location` scopes the MEASUREMENTS to one project's tracking location (see
    `_location_clause`); `site_pk` scopes the TRACKED KEYWORD LIST the measurements are counted
    over to that same project (see the site_pk comment on SavedKeyword). Both are needed: a
    location with no project id still counts a sibling's keywords as this project's.
    """
    try:
        from pipeline.utils.keywords import load_tracked_keywords
        tracked_kws = load_tracked_keywords(site_id, location=location, site_pk=site_pk)
        if not tracked_kws:
            return {"total": 0, "top3": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0,
                    "avg_position": 0, "total_clicks": 0, "total_impressions": 0,
                    "top3_pct": 0, "top4_10_pct": 0, "top11_20_pct": 0, "rest_pct": 0}

        tracked_lower = [k.lower() for k in tracked_kws]
        from pipeline.db.schema import ensure_ranking_location_columns, ensure_ranking_location_keys
        with get_session() as session:
            ensure_ranking_location_columns(session)
            ensure_ranking_location_keys(session)
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
                    func.lower(KeywordRanking.keyword).in_(tracked_lower),
                    *_location_clause(KeywordRanking, location),
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

def _get_position_changes(site_id: str, curr_start: date, curr_end: date, prev_start: date,
                          prev_end: date, location: str | None = None,
                          site_pk: int | None = None) -> dict:
    """`location` scopes the measurements to one project's tracking location (see
    `_location_clause`); `site_pk` scopes the tracked keyword list to that project."""
    try:
        from pipeline.utils.keywords import load_tracked_keywords
        tracked_kws = load_tracked_keywords(site_id, location=location, site_pk=site_pk)
        if not tracked_kws:
            return {k: [] if "count" not in k else 0 for k in ["improved", "improved_count", "declined", "declined_count", "new", "new_count", "lost", "lost_count"]}

        tracked_lower = [k.lower() for k in tracked_kws]
        from pipeline.db.schema import ensure_ranking_location_columns, ensure_ranking_location_keys
        with get_session() as session:
            ensure_ranking_location_columns(session)
            ensure_ranking_location_keys(session)
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
                    func.lower(KeywordRanking.keyword).in_(tracked_lower),
                    *_location_clause(KeywordRanking, location),
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
                    func.lower(KeywordRanking.keyword).in_(tracked_lower),
                    *_location_clause(KeywordRanking, location),
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

def _get_competitor_map(site_id: str, limit: int = 12, location: str | None = None,
                        site_pk: int | None = None) -> dict:
    """Domain-level aggregate of the per-keyword competitor capture — the "map".

    `location` scopes every read to one project's tracking location (see `_location_clause`);
    `site_pk` scopes the tracked keyword list the map is built over to that same project.
    This function computes the `visibility` percentage the project list shows, so leaving it
    unscoped is exactly what made six Premierstaff city projects all report 65%.

    Where _get_competitor_grid answers "who ranks where for this one keyword", this answers
    "how does each competitor sit relative to us overall": how many of our tracked keywords
    they were actually captured on (overlap), how strongly they rank on those (avg/best
    position, top-3/top-10 counts), and how often they are ahead of us head-to-head. That
    pair — overlap and strength — is what the caller plots each domain at.

    EVERY NUMBER COMES FROM A CAPTURED ROW. This file previously synthesised a competitor's
    position from an MD5 of the keyword+domain string whenever no capture existed; that was
    removed and must not come back in any form here. A (keyword, domain) pair with no row on
    the capture date is not scored, not interpolated and not counted as a rank — the
    dataforseo_serp_competitors connector captures the SERP to depth 30 and writes a row only
    where the domain actually appeared, so "no row" means "not in the captured top 30", and
    the only honest treatment is to leave it out of the position statistics and report the
    coverage separately. With no captured rows at all the map returns status "no_data" and an
    empty domains list; the caller renders an empty state rather than a picture.

    Two dates are reported, not one, because they come from two connectors:
      captured_date — the latest date in competitor_keyword_rankings (the competitors' ranks)
      your_date     — the latest date in keyword_rankings at or before it (your own ranks)
    They are normally the same day; when they are not, the caller can say so instead of
    implying a same-moment comparison.
    """
    empty = {"status": "no_data", "captured_date": None, "your_date": None,
             "keywords_captured": 0, "tracked_total": 0, "volume_weighted": False,
             "domains": []}
    try:
        from pipeline.utils.keywords import load_tracked_keywords
        tracked_kws = load_tracked_keywords(site_id, location=location, site_pk=site_pk)
        if not tracked_kws:
            return empty
        tracked_lower = [k.lower() for k in tracked_kws]

        from pipeline.services.competitor_service import get_tracked_competitors, _bare
        competitors = get_tracked_competitors(site_id)
        if not competitors:
            return {**empty, "status": "no_competitors", "tracked_total": len(tracked_kws)}

        from pipeline.db.schema import ensure_ranking_location_columns, ensure_ranking_location_keys
        with get_session() as session:
            ensure_ranking_location_columns(session)
            ensure_ranking_location_keys(session)
            from pipeline.db.writer import ensure_tables
            ensure_tables(session, CompetitorKeywordRanking)  # idempotent; clean pre-first-refresh state

            captured_date = session.execute(
                select(func.max(CompetitorKeywordRanking.date))
                .where(CompetitorKeywordRanking.site_id == site_id,
                       *_location_clause(CompetitorKeywordRanking, location))
            ).scalar()
            if captured_date is None:
                return {**empty, "tracked_total": len(tracked_kws)}

            comp_rows = session.execute(
                select(CompetitorKeywordRanking.keyword,
                       CompetitorKeywordRanking.competitor_domain,
                       CompetitorKeywordRanking.position)
                .where(CompetitorKeywordRanking.site_id == site_id,
                       CompetitorKeywordRanking.date == captured_date,
                       func.lower(CompetitorKeywordRanking.keyword).in_(tracked_lower),
                       *_location_clause(CompetitorKeywordRanking, location))
            ).all()

            # Your own ranks: the latest keyword_rankings date at or before the capture date,
            # so the comparison never reads your future position against their past one.
            your_date = session.execute(
                select(func.max(KeywordRanking.date))
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date <= captured_date,
                       *_location_clause(KeywordRanking, location))
            ).scalar()
            your_rows = []
            if your_date is not None:
                your_rows = session.execute(
                    select(KeywordRanking.keyword,
                           func.avg(KeywordRanking.position).label("pos"))
                    .where(KeywordRanking.site_id == site_id,
                           KeywordRanking.date == your_date,
                           func.lower(KeywordRanking.keyword).in_(tracked_lower),
                           *_location_clause(KeywordRanking, location))
                    .group_by(KeywordRanking.keyword)
                ).all()

            # Search volume is the weight for the visibility figure. Taken across all dates
            # (max) because volume is a market fact refreshed on its own cadence, not a
            # per-capture measurement.
            vol_rows = session.execute(
                select(KeywordRanking.keyword,
                       func.max(KeywordRanking.search_volume).label("vol"))
                .where(KeywordRanking.site_id == site_id,
                       func.lower(KeywordRanking.keyword).in_(tracked_lower),
                       *_location_clause(KeywordRanking, location))
                .group_by(KeywordRanking.keyword)
            ).all()

        your_pos = {r.keyword.lower(): (int(round(r.pos)) if r.pos is not None else None)
                    for r in your_rows}
        volumes = {r.keyword.lower(): int(r.vol or 0) for r in vol_rows}

        # keyword -> domain -> position, captured rows only.
        captured: dict = {}
        for r in comp_rows:
            if r.position is None:
                continue
            captured.setdefault(r.keyword.lower(), {})[r.competitor_domain] = int(r.position)
        keywords_captured = len(captured)
        if not keywords_captured:
            return {**empty, "captured_date": str(captured_date),
                    "your_date": str(your_date) if your_date else None,
                    "tracked_total": len(tracked_kws)}

        # Weighting: real volumes when any exist, otherwise every keyword counts once. The
        # fallback is a stated assumption about the WEIGHTS over the same real positions, not
        # a substitute for a missing position.
        weight_pool = [volumes.get(k, 0) for k in captured]
        volume_weighted = any(w > 0 for w in weight_pool)

        def weight(kw_lower: str) -> float:
            return float(volumes.get(kw_lower, 0)) if volume_weighted else 1.0

        def summarise(label: str, positions: dict, is_you: bool) -> dict:
            """positions: {keyword_lower: position} — captured/known ranks only."""
            ranked = [p for p in positions.values() if p is not None]
            # Visibility: weighted mean of (101 - position)/100 over EVERY captured keyword,
            # so a domain absent from a keyword's top 30 scores 0 for it rather than being
            # skipped. Denominator is the same for every domain, which is what makes the
            # scores comparable.
            denom = sum(weight(k) for k in captured)
            numer = 0.0
            for kw_lower in captured:
                pos = positions.get(kw_lower)
                if pos is not None and 1 <= pos <= 100:
                    numer += weight(kw_lower) * ((101 - pos) / 100.0)
            head_to_head = beats_you = you_beat = 0
            if not is_you:
                for kw_lower, pos in positions.items():
                    mine = your_pos.get(kw_lower)
                    if pos is None or mine is None:
                        continue
                    head_to_head += 1
                    if pos < mine:
                        beats_you += 1
                    elif mine < pos:
                        you_beat += 1
            return {
                "domain": label,
                "is_you": is_you,
                "keywords_ranked": len(ranked),
                "coverage_pct": round(len(ranked) / keywords_captured * 100, 1) if keywords_captured else 0.0,
                "avg_position": round(sum(ranked) / len(ranked), 1) if ranked else None,
                "best_position": min(ranked) if ranked else None,
                "top3": sum(1 for p in ranked if p <= 3),
                "top10": sum(1 for p in ranked if p <= 10),
                "head_to_head": head_to_head,
                "beats_you": beats_you,
                "you_beat": you_beat,
                "visibility": round(numer / denom * 100, 1) if denom else None,
            }

        domains = [summarise(
            _bare(site_id) or site_id,
            {k: v for k, v in your_pos.items() if k in captured and v is not None},
            is_you=True,
        )]
        for dom in competitors:
            positions = {kw: pos_map[dom] for kw, pos_map in captured.items() if dom in pos_map}
            domains.append(summarise(dom, positions, is_you=False))

        # You first, then competitors by how much of your keyword set they cover, then by how
        # strongly they rank on it.
        rivals = sorted(domains[1:],
                        key=lambda d: (-d["keywords_ranked"], d["avg_position"] if d["avg_position"] is not None else 999))
        return {
            "status": "ok",
            "captured_date": str(captured_date),
            "your_date": str(your_date) if your_date else None,
            "keywords_captured": keywords_captured,
            "tracked_total": len(tracked_kws),
            "volume_weighted": volume_weighted,
            "domains": domains[:1] + rivals[:limit],
        }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"_get_competitor_map error: {e}", exc_info=True)
        return empty


def _get_competitor_grid(site_id: str, limit: int = 100, location: str | None = None,
                         site_pk: int | None = None) -> dict:
    """
    SEMrush-style per-keyword competitor grid: for each tracked keyword, your rank
    plus each tracked competitor's rank on the two most recent capture dates, with
    the date-over-date diff. Reads only from the DB (competitor_keyword_rankings +
    keyword_rankings) — never calls an API. Returns a status the template branches on.

    `location` scopes every read below to one project's tracking location; see
    `_location_clause`. It is applied to the DATE queries as well as the row queries — picking
    "the two most recent capture dates" across all of a domain's cities would anchor this
    project's grid to a date another city was synced on and then find no rows for it.
    `site_pk` scopes the tracked keyword list the grid's rows are built from to that project.
    """
    try:
        from pipeline.utils.keywords import load_tracked_keywords
        tracked_kws = load_tracked_keywords(site_id, location=location, site_pk=site_pk)
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

        from pipeline.db.schema import ensure_ranking_location_columns, ensure_ranking_location_keys
        with get_session() as session:
            ensure_ranking_location_columns(session)
            ensure_ranking_location_keys(session)
            from pipeline.db.writer import ensure_tables
            ensure_tables(session, CompetitorKeywordRanking)  # idempotent; clean empty state pre-first-refresh
            dates = session.execute(
                select(CompetitorKeywordRanking.date)
                .where(CompetitorKeywordRanking.site_id == site_id,
                       *_location_clause(CompetitorKeywordRanking, location))
                .group_by(CompetitorKeywordRanking.date)
                .order_by(CompetitorKeywordRanking.date.desc())
                .limit(2)
            ).scalars().all()
            if not dates:
                dates = session.execute(
                    select(KeywordRanking.date)
                    .where(KeywordRanking.site_id == site_id,
                           *_location_clause(KeywordRanking, location))
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
                    # The competitor's OWN ranking URL. Without it the grid had no per-cell
                    # URL at all, so the UI fell back to your row-level URL and every
                    # competitor cell showed one of YOUR pages.
                    CompetitorKeywordRanking.url,
                )
                .where(CompetitorKeywordRanking.site_id == site_id,
                       CompetitorKeywordRanking.date.in_(both),
                       func.lower(CompetitorKeywordRanking.keyword).in_(tracked_lower),
                       *_location_clause(CompetitorKeywordRanking, location))
            ).all()

            # Your own two latest dates are picked independently of `both` (the competitor
            # sync's dates). The two syncs are billed and run separately, so a day where
            # dataforseo_serp captured nothing usable for your domain (every row written with
            # position=NULL -- e.g. a failed/partial run) must not blank out the whole "you"
            # column just because dataforseo_serp_competitors happened to run that same day.
            # Picking the latest dates that actually have a captured position surfaces the
            # real, most recent data instead of an empty read caused by an unrelated sync's
            # calendar.
            your_dates = session.execute(
                select(KeywordRanking.date)
                .where(KeywordRanking.site_id == site_id,
                       KeywordRanking.position.isnot(None),
                       func.lower(KeywordRanking.keyword).in_(tracked_lower),
                       *_location_clause(KeywordRanking, location))
                .group_by(KeywordRanking.date)
                .order_by(KeywordRanking.date.desc())
                .limit(2)
            ).scalars().all()
            your_latest = your_dates[0] if your_dates else None
            your_prev = your_dates[1] if len(your_dates) > 1 else None
            your_both = [d for d in (your_latest, your_prev) if d is not None]

            your_rows = session.execute(
                select(KeywordRanking.keyword, KeywordRanking.date,
                       func.avg(KeywordRanking.position).label("pos"),
                       # max() only to satisfy the GROUP BY; one keyword/date has one URL.
                       func.max(KeywordRanking.url).label("url"))
                .where(KeywordRanking.site_id == site_id, KeywordRanking.date.in_(your_both),
                       func.lower(KeywordRanking.keyword).in_(tracked_lower),
                       *_location_clause(KeywordRanking, location))
                .group_by(KeywordRanking.keyword, KeywordRanking.date)
            ).all()

        # cell[keyword][domain] = {"latest": pos, "prev": pos}
        # Populated ONLY from real CompetitorKeywordRanking rows (captured by the
        # dataforseo_serp_competitors connector). A keyword/domain pair with no captured row
        # stays absent, and make_cell() below renders it as "—".
        #
        # REMOVED (2026-07): this block used to invent a position for every missing pair when
        # `competitor_keyword_rankings` was empty -- it took the competitor's site-wide average
        # from CompetitorDomain (defaulting to 30.0, or a flat 25.0 for domains with no row at
        # all) and added an MD5-derived offset of the keyword+domain string, then a second hash
        # for the previous date so the grid even showed a plausible-looking movement arrow.
        # The numbers were deterministic, which made them look stable and therefore real, and
        # they fed the Positioning score cards and the visibility comparison. Nobody could tell
        # them apart from captured data. Per skills.md rule 3, an absent cell is the honest
        # answer: run a positions sync to capture real competitor ranks.
        cell: dict = {}
        for r in comp_rows:
            slot = cell.setdefault(r.keyword, {}).setdefault(r.competitor_domain, {})
            key = "latest" if r.date == latest else "prev"
            slot[key] = r.position
            if key == "latest":
                slot["url"] = r.url or ""

        your_cell: dict = {}
        for r in your_rows:
            slot = your_cell.setdefault(r.keyword, {})
            pos = round(r.pos, 0) if r.pos is not None else None
            key = "latest" if r.date == your_latest else "prev"
            slot[key] = int(pos) if pos is not None else None
            if key == "latest":
                slot["url"] = r.url or ""

        keywords = sorted(set(cell) | set(your_cell))

        def make_cell(data: dict) -> dict:
            lp, pp = data.get("latest"), data.get("prev")
            diff, direction = _diff_label(lp, pp)
            # `url` is the ranking URL for THIS cell -- this domain, this keyword. Empty
            # string when the snapshot recorded none; never another domain's URL.
            return {"pos": lp, "prev": pp, "diff": diff, "direction": direction,
                    "url": data.get("url") or ""}

        rows = []
        for kw in keywords:
            kw_comps = [
                {"domain": dom, **make_cell(cell.get(kw, {}).get(dom, {}))}
                for dom in competitors
            ]
            rows.append({
                "kw": kw,
                "you": make_cell(your_cell.get(kw, {})),
                "comps": kw_comps
            })

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
