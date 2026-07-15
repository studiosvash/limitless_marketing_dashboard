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

    dist = _get_ranking_distribution(site_id, curr_start, curr_end)
    changes = _get_position_changes(site_id, curr_start, curr_end, prev_start, prev_end)
    grid = _get_competitor_grid(site_id)

    kpis = {
        "tracked": dist["total"],
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

    domains = grid.get("competitors", [])
    comp_rows = []
    for row in grid.get("rows", []):
        comps = [
            next((c["pos"] for c in row["cells"] if c["domain"] == dom), None)
            for dom in domains
        ]
        comp_rows.append({"kw": row["keyword"], "you": row["you"]["pos"], "comps": comps})
    competitors = {"domains": domains, "rows": comp_rows}

    intel = get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start, prev_end)
    movers_raw = [
        r for r in intel["full_keywords"]
        if r.get("pos_change") is not None and abs(r["pos_change"]) >= 2
    ]
    movers_raw.sort(key=lambda r: abs(r["pos_change"]), reverse=True)
    movers = [to_api_keyword(r) for r in movers_raw[:8]]

    return {
        "kpis": kpis,
        "distribution": distribution,
        "movement": movement,
        "competitors": competitors,
        "movers": movers,
    }
