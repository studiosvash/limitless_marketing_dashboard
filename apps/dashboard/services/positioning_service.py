"""Position Tracking page — API-shaped builder. Reuses existing query functions
(_get_ranking_distribution, _get_position_changes, _get_competitor_grid) from
apps.dashboard.views AS-IS — they are not moved or modified, since the old positioning()
view uses more functions than this API needs. See
.claude/api-reference.md for the field mapping."""

import logging
from datetime import date

from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw, to_api_keyword

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Keyword Opportunities — the scorer behind `keyword_opportunities`
# ─────────────────────────────────────────────
#
# The table has existed in pipeline/db/schema.py since the prediction layer was designed and
# nothing had ever written a row to it. This is that writer. Every input is data the site
# already has: the current SERP position, the search volume, the keyword difficulty and the
# period-over-period position change — the same columns the Keywords page already segments
# into Quick Wins (positions 4-10) and Striking Distance (11-20).
#
# THE FORMULA, stated in full so any number on screen can be re-derived by hand:
#
#   score = 100 x weighted mean of the components below, weights renormalised over whichever
#           components are actually known for that keyword
#
#     proximity (weight 0.5) — how close you already are, from the table below. Not
#         "headroom": a keyword you already rank near page 1 for is the cheapest to move, and
#         the score is meant to rank what to do NEXT, not what would be biggest in theory.
#     volume    (weight 0.3) — this keyword's search volume as a fraction of the highest
#         search volume among the site's own scored keywords. Normalised inside the site
#         because an absolute volume means nothing without the site's own scale.
#     ease      (weight 0.2) — (100 - keyword_difficulty) / 100.
#
#   A keyword with no keyword_difficulty on record drops the ease component and the remaining
#   weights are renormalised (0.5/0.8 and 0.3/0.8). No KD is ever assumed. Likewise the volume
#   component is dropped entirely when the site has no volume data at all.
#
# NOT SCORED (deliberately, rather than scored as a zero):
#   * positions 1-3 — already top 3; "what to target next" is not this.
#   * a keyword with neither a captured position nor a search volume — there is no evidence
#     about it at all, and an evidence-free row with a number next to it is the exact failure
#     mode skills.md rule 3 exists to prevent.
#
# estimated_traffic_gain IS ALWAYS None. Turning "position 14 -> position 8" into a click
# count requires a position->CTR curve, and this project has no such curve from a real
# source: the per-keyword clicks/impressions in keyword_rankings come from Search Console at
# the position each keyword ACTUALLY held, which says nothing about the CTR it would earn at
# a position it has never held. Deriving one from a handful of the site's own keywords would
# be a fabricated model wearing real data's clothing. The column stays NULL and the UI prints
# "—" with the reason, which is a smaller lie than a plausible number.
_OPPORTUNITY_ESTIMATED_TRAFFIC_GAIN = None

# (inclusive upper position bound, proximity component, human phrase)
_PROXIMITY_BANDS = (
    (10, 1.00, "positions 4-10, one step from the top 3"),
    (20, 0.75, "positions 11-20, page 2"),
    (30, 0.50, "positions 21-30"),
    (50, 0.30, "positions 31-50"),
    (100, 0.15, "positions 51-100"),
)
_PROXIMITY_UNRANKED = 0.05  # tracked but not ranking in the captured data

_W_PROXIMITY, _W_VOLUME, _W_EASE = 0.5, 0.3, 0.2

_OPPORTUNITY_TYPE_LABELS = {
    "quick_win": "Quick Win",
    "rising": "Rising",
    "striking_distance": "Striking Distance",
    "content_gap": "Content Gap",
}


def _proximity(position):
    """(component, phrase) for a position, or the unranked pair when position is None."""
    if position is None:
        return _PROXIMITY_UNRANKED, "not ranking in the captured data"
    for upper, component, phrase in _PROXIMITY_BANDS:
        if position <= upper:
            return component, phrase
    return _PROXIMITY_UNRANKED, "below position 100"


def _opportunity_type(position, pos_change) -> str:
    """Classify into the four values schema.py's KeywordOpportunity documents.

    Order matters and is deliberate: the 4-10 band is checked before momentum, because a
    Quick Win is the more actionable label for a keyword that is both. `content_gap` covers
    both "not ranking at all" and "ranking below position 20" — in either case there is no
    page-1/page-2 foothold to defend, which is what makes it a gap.
    """
    if position is not None and 4 <= position <= 10:
        return "quick_win"
    if pos_change is not None and pos_change >= 2:
        return "rising"
    if position is not None and 11 <= position <= 20:
        return "striking_distance"
    return "content_gap"


def score_keyword_opportunities(rows: list[dict], limit: int = 25) -> list[dict]:
    """Score the site's keywords into opportunity rows, best first. Pure function of `rows`.

    `rows` are the merged per-keyword records build_positions_response already assembles
    (keyword / position / prev_position / pos_change / search_volume / keyword_difficulty /
    cpc / clicks). Returns API-shaped dicts; no database access, so it is trivially testable
    and the same numbers can be recomputed from a response body.
    """
    candidates = []
    for row in rows:
        keyword = (row.get("keyword") or "").strip()
        if not keyword:
            continue
        position = row.get("position")
        position = round(float(position)) if position is not None else None
        volume = int(row.get("search_volume") or 0)
        if position is not None and position <= 3:
            continue                      # already top 3 — not "what to target next"
        if position is None and volume <= 0:
            continue                      # no position and no volume = no evidence at all
        kd = row.get("keyword_difficulty")
        kd = float(kd) if kd is not None and kd != "" else None
        if kd is not None and kd <= 0:
            kd = None                     # 0 is this pipeline's "unknown", not "effortless"
        change = row.get("pos_change")
        candidates.append({
            "keyword": keyword,
            "position": position,
            "volume": volume,
            "kd": kd,
            "cpc": float(row["cpc"]) if row.get("cpc") not in (None, "") else None,
            "pos_change": round(float(change), 1) if change is not None else None,
        })

    if not candidates:
        return []

    max_volume = max(c["volume"] for c in candidates)

    scored = []
    for c in candidates:
        proximity, proximity_phrase = _proximity(c["position"])
        parts = [(_W_PROXIMITY, proximity)]
        reasons = [
            f"Position {c['position']} ({proximity_phrase}) scores {proximity:.2f} on proximity"
            if c["position"] is not None
            else f"No captured position ({proximity_phrase}) scores {proximity:.2f} on proximity"
        ]

        if max_volume > 0:
            volume_component = c["volume"] / max_volume
            parts.append((_W_VOLUME, volume_component))
            reasons.append(
                f"volume {c['volume']:,}/mo is {volume_component * 100:.0f}% of your "
                f"highest-volume tracked keyword ({max_volume:,})"
            )
        else:
            reasons.append("no search volume on record for any tracked keyword, so the "
                           "volume component was dropped and its weight redistributed")

        if c["kd"] is not None:
            ease = max(0.0, min(1.0, (100.0 - c["kd"]) / 100.0))
            parts.append((_W_EASE, ease))
            reasons.append(f"keyword difficulty {c['kd']:.0f} leaves {ease * 100:.0f}% ease")
        else:
            reasons.append("no keyword difficulty on record, so the ease component was "
                           "dropped and its weight redistributed")

        weight_total = sum(w for w, _ in parts)
        score = round(sum(w * v for w, v in parts) / weight_total * 100, 1) if weight_total else 0.0

        opportunity_type = _opportunity_type(c["position"], c["pos_change"])
        if c["pos_change"] is not None and c["pos_change"] != 0:
            direction = "up" if c["pos_change"] > 0 else "down"
            reasons.append(f"moved {direction} {abs(c['pos_change']):g} vs the previous period")

        weights_used = " + ".join(f"{w:.2f}x{v:.2f}" for w, v in parts)
        reasons.append(f"score = ({weights_used}) / {weight_total:.2f} x 100 = {score:.1f}")

        scored.append({
            "keyword": c["keyword"],
            "position": c["position"],
            "type": opportunity_type,
            "type_label": _OPPORTUNITY_TYPE_LABELS[opportunity_type],
            "volume": c["volume"],
            "kd": round(c["kd"], 1) if c["kd"] is not None else None,
            "cpc": c["cpc"],
            "score": score,
            "estimated_traffic_gain": _OPPORTUNITY_ESTIMATED_TRAFFIC_GAIN,
            "rationale": "; ".join(reasons) + ".",
        })

    scored.sort(key=lambda o: (-o["score"], o["position"] if o["position"] is not None else 999))
    return scored[:limit]


def persist_keyword_opportunities(site_id: str, opportunities: list[dict]) -> int:
    """Upsert the scored rows into keyword_opportunities and drop the ones that no longer
    score, so the table is a snapshot of the current answer rather than an ever-growing log.

    WHY THE UPSERT LIVES HERE AND NOT IN pipeline/db/writer.py: writer.py's own contract is
    "only from connectors and pipeline tasks" — it is the persistence layer for FETCHED data.
    These rows are not fetched from anywhere; they are computed from data this site already
    owns, by this service, and this is their only writer. The mechanics still follow writer.py
    exactly: the dialect-neutral insert construct from pipeline.db.dialect (never a direct
    sqlalchemy.dialects.sqlite import), ON CONFLICT DO UPDATE on the table's own unique key,
    and a batch size the same helper sizes per backend.

    Returns the number of rows written. Never raises: failing to cache the answer must not
    stop the page from rendering it.
    """
    from datetime import datetime

    from pipeline.db.dialect import max_batch_size, upsert_insert
    from pipeline.db.schema import KeywordOpportunity
    from pipeline.db.writer import ensure_tables
    from pipeline.utils.db_connection import get_session
    from sqlalchemy import delete, select

    try:
        with get_session() as session:
            ensure_tables(session, KeywordOpportunity)  # never written before: may not exist yet

            kept = {o["keyword"] for o in opportunities}
            existing = session.execute(
                select(KeywordOpportunity.keyword).where(KeywordOpportunity.site_id == site_id)
            ).scalars().all()
            stale = [k for k in existing if k not in kept]
            # Deleted in bounded batches rather than one NOT IN (...): a tracked list can be
            # long enough to blow SQLite's ~999 bound-parameter ceiling.
            for i in range(0, len(stale), 200):
                session.execute(
                    delete(KeywordOpportunity).where(
                        KeywordOpportunity.site_id == site_id,
                        KeywordOpportunity.keyword.in_(stale[i:i + 200]),
                    )
                )

            if not opportunities:
                return 0

            now = datetime.now()
            records = [{
                "site_id": site_id,
                "keyword": o["keyword"],
                "current_position": o["position"],
                "search_volume": o["volume"],
                "keyword_difficulty": o["kd"],
                "cpc": o["cpc"],
                "opportunity_score": o["score"],
                "opportunity_type": o["type"],
                "estimated_traffic_gain": o["estimated_traffic_gain"],
                "rationale": o["rationale"],
                "computed_at": now,
            } for o in opportunities]

            insert = upsert_insert(session)
            batch_size = max_batch_size(session, 60)
            keys = ("site_id", "keyword")
            update_cols = [k for k in records[0] if k not in keys]
            written = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                stmt = insert(KeywordOpportunity).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=list(keys),
                    set_={k: stmt.excluded[k] for k in update_cols},
                )
                session.execute(stmt)
                written += len(batch)
            return written
    except Exception as e:
        logger.error(f"persist_keyword_opportunities error: {e}", exc_info=True)
        return 0


def _volume_coverage(rows: list[dict], sample_limit: int = 25) -> dict:
    """How many merged keywords actually have a stored search volume, and which don't.

    This exists because the honest answer to "we have no volume for this keyword" is a
    visible gap, not a silent one and not a paid live lookup (see the long comment in
    build_positions_response). `missing` is the count of rows whose `search_volume` is
    `None` — genuinely unknown. A stored volume of 0 is a KNOWN value (DataForSEO really
    does report 0 for some keywords) and counts as covered; conflating the two is the whole
    bug this guards against.

    Pure function of `rows`; no database access, no external call.
    """
    total = len(rows)
    missing = [(r.get("keyword") or "").strip() for r in rows if r.get("search_volume") is None]
    missing = [k for k in missing if k]
    note = ""
    if missing:
        note = (
            f"{len(missing)} of {total} tracked keyword"
            f"{'s have' if len(missing) != 1 else ' has'} no stored search volume. "
            "Volume is written by the `dataforseo_keywords` connector during a Positioning "
            "refresh — keywords tracked since the last refresh have none yet. Run Refresh to "
            "fill them in; this page never buys the data on its own."
        )
    return {
        "tracked": total,
        "with_volume": total - len(missing),
        "missing_volume": len(missing),
        "missing_keywords": sorted(missing)[:sample_limit],
        "note": note,
    }


def build_positions_response(site_id: str, curr_start: date, curr_end: date,
                              prev_start: date, prev_end: date) -> dict:
    """HANDOFF_SPEC.md `positions` view shape — verified against the real fixture's
    positionsView() in Limitless marketing dashboard2/app/api.js."""
    from apps.dashboard.services.shared_queries import (
        _get_ranking_distribution, _get_position_changes, _get_competitor_grid,
        _get_competitor_map,
    )
    from pipeline.services.saved_keyword_service import list_saved_keywords

    dist = _get_ranking_distribution(site_id, curr_start, curr_end)
    changes = _get_position_changes(site_id, curr_start, curr_end, prev_start, prev_end)
    grid = _get_competitor_grid(site_id)
    comp_map = _get_competitor_map(site_id)
    saved_kws = list_saved_keywords(site_id)

    intel = get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start, prev_end, tracked_only=True)
    intel_kws = intel.get("full_keywords", [])
    ranked_map = {r["keyword"].lower(): r for r in intel_kws if r.get("keyword")}

    # Merge saved keywords with synced rankings from keyword_rankings
    merged_kws_raw = []
    seen = set()

    # First, bring in everything that has synced rankings
    for r in intel_kws:
        kw_text = (r.get("keyword") or "").strip()
        if not kw_text:
            continue
        seen.add(kw_text.lower())
        merged_kws_raw.append(r)

    # Next, bring in any saved keyword that hasn't been synced to SERP rankings yet
    for sk in saved_kws:
        kw_text = (sk.get("keyword") or "").strip()
        if not kw_text:
            continue
        if kw_text.lower() in seen:
            # Already present from keyword_rankings — top up the columns the SERP capture
            # doesn't carry from the site's OWN saved_keywords row. Both sides are database
            # reads; nothing here reaches an external API.
            #
            # `is None`, not falsy: a real search volume of 0, a KD of 0 or a CPC of 0.0
            # are values, and `if not item.get(...)` would silently overwrite them with the
            # saved-list copy.
            for item in merged_kws_raw:
                if (item.get("keyword") or "").lower() == kw_text.lower():
                    if item.get("search_volume") is None and sk.get("search_volume") is not None:
                        item["search_volume"] = sk.get("search_volume")
                    if item.get("keyword_difficulty") is None and sk.get("keyword_difficulty") is not None:
                        item["keyword_difficulty"] = sk.get("keyword_difficulty")
                    if item.get("cpc") is None and sk.get("cpc") is not None:
                        item["cpc"] = sk.get("cpc")
                    if not item.get("intent") and sk.get("intent"):
                        item["intent"] = sk.get("intent")
            continue
        seen.add(kw_text.lower())
        merged_kws_raw.append({
            "keyword": kw_text,
            "position": None,
            "prev_position": None,
            "pos_change": None,
            "clicks": 0,
            "impressions": 0,
            "ctr": 0.0,
            # None, never 0 (changed 2026-07-27). This keyword is tracked but has no
            # synced row yet; `or 0` here claimed "this keyword gets zero searches a
            # month / has zero difficulty / costs nothing", which is a fabricated fact,
            # not a missing one. Unknown must stay visibly unknown — see
            # `volume_coverage` below, which counts exactly these rows.
            "search_volume": sk.get("search_volume"),
            "keyword_difficulty": sk.get("keyword_difficulty"),
            "cpc": sk.get("cpc"),
            "intent": sk.get("intent") or "informational",
            "url": "",
            "action": "new",
        })

    # ─────────────────────────────────────────────────────────────────────────────
    # DO NOT REINTRODUCE A LIVE API CALL HERE.  (removed 2026-07-27)
    #
    # This block used to call DataForSEOKeywordsConnector.lookup_keywords() for every
    # merged keyword with no stored search_volume, on every single GET /positions.
    # That broke CLAUDE.md iron rule 1 in the most expensive way available:
    #   * it is BILLABLE (Labs keyword_overview meters per keyword submitted) and it ran
    #     per page view, uncapped, outside the budget cap the user sets in Settings;
    #   * it wrote a `connector_costs` row per page view, so the Settings cost panel read
    #     as runaway spend that no refresh had authorised;
    #   * it put a 30 s external timeout on a page render whose whole contract is
    #     "instant, from SQLite".
    # It was also redundant. `dataforseo_keywords` is already in
    # PAGE_CONNECTORS["positioning"] AND in ALL_CONNECTORS (pipeline/services/sync_engine.py),
    # and its fetch() loads its keyword list from pipeline.utils.keywords.load_tracked_keywords
    # — the SAME saved_keywords list that produces `saved_kws` and bounds `intel_kws`
    # (tracked_only=True) above. So the Refresh path already backfills volume, KD and CPC
    # into keyword_rankings for exactly this keyword set. The paid call bought data the
    # sync had already been paid for.
    #
    # THE ONE REAL GAP, stated instead of papered over: a keyword tracked *since* the last
    # positioning sync has no keyword_rankings row yet, and the volume the Explorer captured
    # when it was saved may be absent. Same for the reverse window — dataforseo_keywords
    # stamps its metrics on the `yesterday()` row, so a request whose period window ends
    # before that date will not see them. Both cases are surfaced in `volume_coverage`
    # below, and both are fixed by the Refresh button, not by spending money on a page load.
    # ─────────────────────────────────────────────────────────────────────────────
    volume_coverage = _volume_coverage(merged_kws_raw)

    movers_raw = [
        r for r in merged_kws_raw
        if r.get("pos_change") is not None and abs(r["pos_change"]) >= 2
    ]
    movers_raw.sort(key=lambda r: abs(r["pos_change"]), reverse=True)
    movers = [to_api_keyword(r) for r in movers_raw[:8]]
    rankings = [to_api_keyword(r) for r in merged_kws_raw]

    domains = grid.get("competitors", [])
    comp_rows_map = {(row.get("kw") or row.get("keyword") or "").lower(): row for row in grid.get("rows", [])}
    comp_rows = []
    for r in merged_kws_raw:
        kw = r["keyword"]
        if kw.lower() in comp_rows_map:
            row = comp_rows_map[kw.lower()]
            comps = []
            for dom in domains:
                c = next((cell for cell in row.get("comps", []) if cell["domain"] == dom), None)
                comps.append(c)
            comp_rows.append({"kw": kw, "you": row["you"], "comps": comps})
        else:
            comp_rows.append({"kw": kw, "you": {"pos": r.get("position"), "prev": r.get("prev_position"), "diff": r.get("pos_change"), "direction": "up" if r.get("pos_change") and r.get("pos_change") > 0 else ("down" if r.get("pos_change") and r.get("pos_change") < 0 else "flat")}, "comps": [None] * len(domains)})
    competitors = {"domains": domains, "rows": comp_rows}

    total_tracked = max(dist["total"], len(merged_kws_raw))
    kpis = {
        "tracked": total_tracked,
        "avg_pos": dist["avg_position"],
        "est_traffic": dist["total_clicks"],
        "impressions": dist["total_impressions"],
    }
    distribution = {
        "top3": dist["top3"],
        "p4_10": dist["top10"] - dist["top3"],
        "p11_20": dist["top20"] - dist["top10"],
        "p21_100": dist["total"] - dist["top20"],
    }
    movement = {
        "improved": changes["improved_count"],
        "declined": changes["declined_count"],
        "added": changes["new_count"],
        "lost": changes["lost_count"],
    }

    # Scored from the same merged rows the table above renders, so a user can check any
    # score against the row it came from. Persisted as a side effect — a database write, not
    # an external call, so the DB-first contract is intact — because keyword_opportunities is
    # the documented home for this answer and nothing had ever filled it.
    opportunities = score_keyword_opportunities(merged_kws_raw)
    persist_keyword_opportunities(site_id, opportunities)

    # The project's own tracking preferences, so the workspace header can print what the user
    # actually chose in the wizard instead of a hardcoded "Desktop".
    project = _project_tracking_prefs(site_id)

    return {
        "kpis": kpis,
        "distribution": distribution,
        "movement": movement,
        "competitors": competitors,
        "competitor_map": comp_map,
        # Makes the "no stored volume" gap visible in the payload instead of hiding it
        # behind a live paid lookup (removed 2026-07-27) or a fabricated 0.
        "volume_coverage": volume_coverage,
        "opportunities": opportunities,
        "project": project,
        "movers": movers,
        "rankings": rankings,
        "keywords": rankings,
    }


def _project_tracking_prefs(site_id: str) -> dict:
    """The stored search engine / device / language / location for this project.

    Falls back to the wizard's own default options only when no Site row resolves or the
    column is NULL — never invents a different value. These are a recorded preference: no
    connector reads them yet (see the note on Site in pipeline/db/schema.py).
    """
    defaults = {"search_engine": "Google", "device": "Desktop", "language": "English",
                "location": "United States"}
    try:
        from pipeline.services.site_service import get_site
        from pipeline.utils.db_connection import get_session
        with get_session() as session:
            site = get_site(session, site_id)
            if site is None or site.site_url != site_id:
                return defaults
            return {
                "search_engine": site.search_engine or defaults["search_engine"],
                "device": site.device or defaults["device"],
                "language": site.language or defaults["language"],
                "location": site.location or defaults["location"],
            }
    except Exception as e:
        logger.error(f"_project_tracking_prefs error: {e}", exc_info=True)
        return defaults
