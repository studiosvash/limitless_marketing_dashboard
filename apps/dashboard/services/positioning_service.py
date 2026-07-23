"""Position Tracking page — API-shaped builder. Reuses existing query functions
(_get_ranking_distribution, _get_position_changes, _get_competitor_grid) from
apps.dashboard.views AS-IS — they are not moved or modified, since the old positioning()
view uses more functions than this API needs. See
docs/superpowers/specs/2026-07-11-phaseB3-positioning-design.md for the field mapping."""

from datetime import date

from apps.dashboard.services.keywords_service import get_keyword_intelligence_raw, to_api_keyword


def build_positions_response(site_id: str, curr_start: date, curr_end: date,
                              prev_start: date, prev_end: date) -> dict:
    """HANDOFF_SPEC.md `positions` view shape — verified against the real fixture's
    positionsView() in Limitless marketing dashboard2/app/api.js."""
    from apps.dashboard.services.shared_queries import (
        _get_ranking_distribution, _get_position_changes, _get_competitor_grid,
    )
    from pipeline.services.saved_keyword_service import list_saved_keywords

    dist = _get_ranking_distribution(site_id, curr_start, curr_end)
    changes = _get_position_changes(site_id, curr_start, curr_end, prev_start, prev_end)
    grid = _get_competitor_grid(site_id)
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
            # If already in seen, let's enrich missing volume/kd/cpc/intent if needed
            for item in merged_kws_raw:
                if (item.get("keyword") or "").lower() == kw_text.lower():
                    if not item.get("search_volume") and sk.get("search_volume"):
                        item["search_volume"] = sk.get("search_volume")
                    if not item.get("keyword_difficulty") and sk.get("keyword_difficulty"):
                        item["keyword_difficulty"] = sk.get("keyword_difficulty")
                    if not item.get("cpc") and sk.get("cpc"):
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
            "search_volume": sk.get("search_volume") or 0,
            "keyword_difficulty": sk.get("keyword_difficulty") or 0,
            "cpc": sk.get("cpc") or 0.0,
            "intent": sk.get("intent") or "informational",
            "url": "",
            "action": "new",
        })

    movers_raw = [
        r for r in merged_kws_raw
        if r.get("pos_change") is not None and abs(r["pos_change"]) >= 2
    ]
    movers_raw.sort(key=lambda r: abs(r["pos_change"]), reverse=True)
    movers = [to_api_keyword(r) for r in movers_raw[:8]]
    rankings = [to_api_keyword(r) for r in merged_kws_raw]

    domains = grid.get("competitors", [])
    comp_rows_map = {row["keyword"].lower(): row for row in grid.get("rows", [])}
    comp_rows = []
    for r in merged_kws_raw:
        kw = r["keyword"]
        if kw.lower() in comp_rows_map:
            row = comp_rows_map[kw.lower()]
            comps = [
                next((c["pos"] for c in row["cells"] if c["domain"] == dom), None)
                for dom in domains
            ]
            comp_rows.append({"kw": kw, "you": row["you"]["pos"], "comps": comps})
        else:
            comp_rows.append({"kw": kw, "you": r.get("position"), "comps": [None] * len(domains)})
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

    return {
        "kpis": kpis,
        "distribution": distribution,
        "movement": movement,
        "competitors": competitors,
        "movers": movers,
        "rankings": rankings,
        "keywords": rankings,
    }
