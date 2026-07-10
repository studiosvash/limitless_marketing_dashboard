# Phase B2 — Keywords Page Design Spec

> Status: approved 2026-07-10. Second of four Phase B sub-projects (B1 SEO done, B2
> Keywords, B3 Position Tracking, B4 Alerts). Branched from `phase-b-seo`.

## Goal

Expose the Keywords page through `GET /api/projects/<slug>/keywords`, reusing the existing
`_get_keyword_intelligence()` function (already computes health score, intent distribution,
KD buckets, and action-bucket segments — built in Phase 5.5 of the old MVP). Also extract the
shared slug-lookup + anchor-date logic used by every `apps/api` view into one helper, per the
Phase B1 final review's recommendation, before a third near-identical endpoint clones it again.

## Target response shape (verified against the real SPA source)

From `Limitless marketing dashboard2/app/api.js`'s `keywordsView(fix)`:

```jsonc
{
  "kpis": { "total": 87, "avg_pos": 14.2, "total_volume": 184200, "total_clicks": 3210 },
  "intents": { "informational": 20, "commercial": 40, "transactional": 15, "navigational": 12 },
  "difficulty": { "easy": 30, "medium": 40, "hard": 17 },
  "segments": {
    "quick_wins": ["hydration iv therapy", "..."],   // arrays of keyword IDs (see below)
    "striking": [...], "declining": [...], "low_ctr": [...]
  },
  "keywords": [
    { "id": "hydration iv therapy", "kw": "hydration iv therapy", "intent": "commercial",
      "pos": 6.0, "prevPos": 8.0, "volume": 2400, "kd": 24, "cpc": 4.2,
      "clicks": 42, "impressions": 900, "ctr": 4.7, "url": "/services/iv-therapy",
      "monthly": [], "source": "sync", "serpFeatures": [] }
  ]
}
```

## Mapping — old MVP source → new shape (pure mapping, `_get_keyword_intelligence` already
computes almost everything)

| New field | Old source | Reshape |
|---|---|---|
| `kpis.total/avg_pos/total_volume/total_clicks` | `total_tracked/avg_position/total_volume/total_clicks` | rename keys |
| `intents{}` | `intent_distribution` | rename key |
| `difficulty{easy,medium,hard}` | `kd_easy/kd_medium/kd_hard` | nest into dict |
| `segments.{quick_wins,striking,declining,low_ctr}` | same-named lists, currently **full row dicts** (top 15 each) | reshape to **arrays of `id` strings** — `id` = the keyword text itself (already unique per aggregation group; no other natural unique identifier exists in this schema, and inventing a fake numeric ID scheme would be worse) |
| `keywords[]` | `all_keywords` (built from `df`, capped at 200, **missing `prevPos`**) | **real gap, not just renaming**: `all_keywords` is currently built from `df` (the current-period aggregation only), while `prev_position`/`pos_change` only exist on `merged` (used for the segment lists). Fix: build `all_keywords` from `merged` instead of `df` so every keyword — not just the top-15-per-segment ones — carries `prevPos`. This is an additive change to the dict's keys (adds `prev_position`/`pos_change`), which the old Django template ignores (it reads specific keys, not all of them) — verify this with a pinning test, not just an assumption. |
| `keywords[].monthly` | *(does not exist)* | honest empty array `[]` — this system doesn't track 12-month historical volume trend per keyword yet. Not fabricated. |
| `keywords[].serpFeatures` | *(does not exist)* | honest empty array `[]` — SERP feature capture per keyword isn't stored yet. Not fabricated. |
| `keywords[].source` | *(does not exist as a per-row field)* | `"sync"` for every row — all currently-tracked keywords come from the sync pipeline, not manual entry (manual/ads_term sources are a Phase D concept, not built yet) |

## Shared API-view helper (new, small, cross-cutting)

`apps/api/views.py` currently has the same ~11-line block duplicated in both
`ProjectOverviewView` and `ProjectSEOView`: resolve `slug` → `Site` → 404, then find
`max(SEODaily.date)` as the anchor. Before adding a third copy, extract:

```python
def resolve_project_or_404(slug: str) -> Site: ...   # raises Http404
def latest_data_anchor(site_id: str) -> date: ...     # falls back to today() if no data
```

Both existing views are retrofitted to call these (pure refactor, their tests must still
pass unchanged) before `ProjectKeywordsView` is built using them from the start.

## Architecture

- New file `apps/dashboard/services/keywords_service.py`:
  - `get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start, prev_end) ->
    dict` — the extracted, behavior-preserving move of `_get_keyword_intelligence`, with the
    `all_keywords`-from-`merged` fix described above.
  - `build_keywords_response(site_id, curr_start, curr_end, prev_start, prev_end) -> dict` —
    the new API-shaped builder, calling the raw function above and reshaping.
- `apps/api/views.py`: `resolve_project_or_404`/`latest_data_anchor` helpers (module-level
  functions, not a class — keeps every view a plain, readable `APIView`), then
  `ProjectKeywordsView(APIView)` on `GET /api/projects/<slug>/keywords` (no `range` param,
  matching the spec's endpoint table — same as SEO).
- `keywords()` (the old Django view) is rewired to import from the new service module,
  pinning test proves identical rendered output.

## Verification

- Full test suite green, including pinning tests against real seeded data.
- Old Keywords page (`/keywords/`) renders unchanged.
- `ProjectOverviewView`/`ProjectSEOView` still pass their existing tests after the shared-helper
  retrofit (no behavior change to either).
- `GET /api/projects/<slug>/keywords` returns real data; segment ID arrays correctly
  reference entries in the `keywords[]` array (every ID in `segments.*` has a matching
  `keywords[].id`).

## Explicitly out of scope

Position Tracking, Alerts (B3–B4). The Keyword Explorer feature (`keywords/explore/`,
already built, live DataForSEO on-demand lookup) is a user-action endpoint, not a page-render
GET — mapping it to the new API's `POST /api/research` is separate follow-up work, not part
of this page's read endpoint.
