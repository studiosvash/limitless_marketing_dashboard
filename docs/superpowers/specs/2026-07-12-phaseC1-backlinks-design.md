# Phase C1 — Backlinks Page Design Spec

> Status: approved 2026-07-12 (continuing autonomously per user instruction). First of four
> Phase C sub-projects (C1 Backlinks, C2 Site Audit, C3 Off-site SEO, C4 Ads). Branched from
> `phase-b4-alerts`. Phase C is genuinely new feature work, not page-porting — see the scope
> note below.

## Why this phase is scoped differently from Phase B

Phase A/B's work was validated against real synced data at every step. Phase C's full scope
(per `HANDOFF_SPEC.md §2.3`) needs data from FIVE separate DataForSEO Backlinks API surfaces
(`summary`, `history`, `referring_domains`, `anchors`, `domain_intersection`) — **none of
which this codebase has a connector for today**, and DataForSEO credentials are currently
blocked (negative balance, per `.claude/checklist.md`). Writing five new, unvalidated API
integrations in one sitting — with no way to confirm field names/response shapes against a
real response — carries real rework risk once credentials land.

**Decision**: this task builds ONLY what's honestly buildable against real, existing
infrastructure right now — the `Backlink` table and `DataForSEOBacklinksConnector` already
exist (from an earlier phase, currently 0 rows since credentials are blocked, but the code
path is real). Everything else in the target shape reports `state:"setup"`, same pattern as
Phase A's Site Audit/Ads/AI pillars. The five missing sub-endpoint connectors are each a
separate, larger follow-up — not attempted speculatively here.

## Target response shape (verified against the real SPA source)

From `Limitless marketing dashboard2/app/api.js`'s `backlinksView(fix)`:

```jsonc
{
  "kpis": { "total": 12400, "live": 128, "lost": 22, "referring_domains": 1450, "avg_rank": 47 },
  "links": [{ "domain": "...", "rank": .., "source": "...", ... }],
  "summary": { "authorityScore": 47, "asDelta": 2, "refDomains": 1450, "backlinks": 12400,
               "dofollowPct": 71, "broken": 64, "spamScore": 6, "newRdMonth": 38,
               "lastUpdated": "..." },
  "months": [ /* 24 entries */ ], "types": [...], "asBuckets": [...],
  "refDomains": [...], "anchors": [...], "competitors": [...], "gapDomains": [...]
}
```

## Mapping — what's real vs. what's `state:"setup"`

| Field | Source | Status |
|---|---|---|
| `kpis.total/live/lost/referring_domains/avg_rank` | Existing `_get_backlinks_summary()` (`Backlink` table) | Real — reshape only |
| `links[]` | Existing `_get_backlinks_table()` (`Backlink` table) | Real — reshape only |
| `summary.*` (authorityScore, asDelta, dofollowPct, broken, spamScore, newRdMonth) | `backlinks/summary` API — no connector exists | `state:"setup"`, no invented numbers |
| `months[24]` | `backlinks/history` API — no connector exists | `state:"setup"`, empty array |
| `types[]` | `backlinks/summary` (`referring_links_types`) — no connector exists | `state:"setup"`, empty array |
| `asBuckets[]` | `backlinks/referring_domains` grouped — no connector exists | `state:"setup"`, empty array |
| `refDomains[]` | `backlinks/referring_domains` (Live) — no connector exists | `state:"setup"`, empty array |
| `anchors[]` | `backlinks/anchors` — no connector exists | `state:"setup"`, empty array |
| `gapDomains[]` | `backlinks/domain_intersection` — no connector exists | `state:"setup"`, empty array |
| `competitors[]` | Already-tracked competitor domains (`pipeline.services.competitor_service.get_tracked_competitors`, reused from Phase B3) | Real — this list exists independent of backlinks data |

## Architecture

- New file `apps/dashboard/services/backlinks_service.py`:
  - `query_backlinks_summary_raw`/`query_backlinks_table_raw` — pure extraction of the
    existing `_get_backlinks_summary`/`_get_backlinks_table` logic (pinning tests, old page
    unaffected), matching the established Phase B pattern.
  - `build_backlinks_response(site_id) -> dict` — assembles the real `kpis`/`links`/
    `competitors` plus `state:"setup"` placeholders for everything else.
- `apps/api/views.py`: `ProjectBacklinksView` on `GET /api/projects/<slug>/backlinks` — no
  `range` param (matches `HANDOFF_SPEC.md`'s endpoint table: `backlinks | — | ...`).

## Verification

- Full suite green.
- Old `/backlinks/` page unaffected.
- `GET /api/projects/<slug>/backlinks` returns the real (currently empty, since 0 rows
  synced) `kpis`/`links`, real `competitors`, and `state:"setup"` for the 7 unbuilt fields —
  never fabricated numbers.

## Explicitly out of scope

The five new DataForSEO Backlinks API connector methods (`summary`, `history`,
`referring_domains`, `anchors`, `domain_intersection`) and their corresponding schema/service
work — each is real, unvalidated integration work deserving its own careful build-and-test
cycle once DataForSEO credentials are resolved. C2 (Site Audit), C3 (Off-site SEO), C4 (Ads).
