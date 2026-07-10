# Phase B3 — Position Tracking Page Design Spec

> Status: approved 2026-07-11 (continuing autonomously per user instruction). Third of four
> Phase B sub-projects (B1 SEO, B2 Keywords done; B3 Position Tracking; B4 Alerts).
> Branched from `phase-b2-keywords`.

## Goal

Expose the Position Tracking page through `GET /api/projects/<slug>/positions?range=`, reusing
existing query functions (`_get_ranking_distribution`, `_get_position_changes`,
`_get_competitor_grid`) already built in the old MVP. Pure mapping — no new connectors.

## Target response shape (verified against the real SPA source)

From `Limitless marketing dashboard2/app/api.js`'s `positionsView(fix)`:

```jsonc
{
  "kpis": { "tracked": 87, "avg_pos": 14.2, "est_traffic": 3210, "impressions": 45200 },
  "distribution": { "top3": 12, "p4_10": 20, "p11_20": 18, "p21_100": 37 },
  "movement": { "improved": 15, "declined": 9, "added": 3, "lost": 2 },
  "competitors": {
    "domains": ["driphydration.com", "..."],
    "rows": [{ "kw": "iv therapy near me", "you": 6, "comps": [8, null, 22] }]
  },
  "movers": [ /* same shape as a Keywords-endpoint keyword object, top 8 by |delta| */ ]
}
```

**Important, non-obvious finding:** `movers[]` is NOT a lightweight summary — the fixture
builds it from the same full keyword-object array as the Keywords endpoint's `keywords[]`
(`kws.filter(...).sort(...).slice(0,8)` where `kws = mergedKeywords(fix)`). So each mover
needs the full `{id, kw, intent, pos, prevPos, volume, kd, cpc, clicks, impressions, ctr,
url, monthly, source, serpFeatures}` shape B2 already built for `keywords[]` — not a
positioning-specific shape. **Reuse, don't reimplement**: promote B2's `to_api_keyword`
(currently a private nested closure inside `build_keywords_response`) to a standalone,
importable function in `keywords_service.py`, and import it here.

## Mapping — old MVP source → new shape

| New field | Old source | Reshape |
|---|---|---|
| `kpis.tracked/avg_pos/est_traffic/impressions` | `_get_ranking_distribution()`'s `total/avg_position/total_clicks/total_impressions` | rename keys |
| `distribution.top3` | `_get_ranking_distribution()`'s `top3` | direct |
| `distribution.p4_10` | `top10 - top3` | computed |
| `distribution.p11_20` | `top20 - top10` | computed |
| `distribution.p21_100` | `total - top20` | computed (fixture defines this as "everything below rank 20", not literally capped at 100 despite the field name) |
| `movement.improved/declined` | `_get_position_changes()`'s `improved_count/declined_count` | direct |
| `movement.added` | `_get_position_changes()`'s `new_count` (keywords with no previous-period position) | rename |
| `movement.lost` | `_get_position_changes()`'s `lost_count` | direct |
| `competitors.domains` | `pipeline.services.competitor_service.get_tracked_competitors(site_id)` (already used internally by `_get_competitor_grid`) | direct |
| `competitors.rows` | `_get_competitor_grid(site_id)`'s `rows[]` (currently `{keyword, you:{pos,prev,diff,direction}, cells:[{domain,pos,...}]}`) | reshape to `{kw, you: <pos number>, comps: [<pos number or null>, ...]}` — new shape wants raw position numbers only, not the diff/direction detail (that richer detail isn't part of this endpoint's contract; the old MVP template shows it, this API doesn't need to) |
| `movers[≤8]` | **new**: build from `_get_position_changes()`'s `improved`+`declined` lists (both already have `keyword`/`delta`), sorted by `abs(delta)` desc, capped at 8, each reshaped via the promoted `to_api_keyword` (see above) — needs a fresh per-keyword query for full API-shape fields, not just the summary fields `_get_position_changes` already returns | genuinely new assembly, reusing B2's keyword-shaping function |

## Architecture

- **Promote `to_api_keyword` in `keywords_service.py`** from a nested closure to a top-level
  function (pure refactor, zero behavior change to `build_keywords_response`'s output —
  verify with existing B2 tests, which must still pass unchanged).
- New file `apps/dashboard/services/positioning_service.py`:
  - Raw calculators (reused as-is, no change): imports `_get_ranking_distribution` and
    `_get_position_changes` from `apps/dashboard/views.py`, `_get_competitor_grid` likewise
    — these are NOT extracted/moved (the old `positioning()` view uses more functions than
    this API needs — e.g. `_get_full_rankings`, `_get_keyword_opportunities`,
    `_get_visibility_trend` — that stay in `views.py`, untouched, out of this task's scope).
  - `build_positions_response(site_id, curr_start, curr_end, prev_start, prev_end) -> dict`
    — the new API-shaped builder.
- `apps/api/views.py`: `ProjectPositionsView(APIView)` on `GET /api/projects/<slug>/positions?range=`
  — this endpoint DOES take `range` (unlike SEO/Keywords), per `HANDOFF_SPEC.md`'s endpoint
  table (`positions | range | ...`). Uses the shared `resolve_project_or_404`/
  `latest_data_anchor` helpers from B2 Task 1.

## Verification

- Full suite green.
- `GET /api/projects/<slug>/positions?range=30d` returns real data; every mover has the full
  keyword-object shape (not a truncated summary); `competitors.rows[].comps` array length
  matches `competitors.domains` length for every row (positional alignment, not a dict).
- Old `/positioning/` page completely untouched (this task reuses existing functions as-is,
  doesn't modify them — lowest-risk task of the four Phase B sub-projects so far).

## Explicitly out of scope

Alerts (B4). `_get_full_rankings`, `_get_keyword_opportunities`, `_get_visibility_trend`,
`_get_positioning_overview` are NOT touched — the old page keeps using them unchanged, and
the new API doesn't need them (this endpoint's shape is narrower than the old page's content).
