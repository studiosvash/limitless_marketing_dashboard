# Phase B4 — Alerts Page Design Spec

> Status: approved 2026-07-11 (continuing autonomously per user instruction). Last of four
> Phase B sub-projects (B1 SEO, B2 Keywords, B3 Position Tracking done; B4 Alerts). Branched
> from `phase-b3-positioning`. Completing this phase closes out Phase B entirely.

## Goal

Expose the Alerts page through `GET /api/projects/<slug>/alerts`, and fold in the shared
range/period-resolve helper the B3 final review recommended (Overview and Positions
currently duplicate the same 4-line `OverviewQuerySerializer` → `latest_data_anchor` →
`range_to_period_dates` block; B4 would be a third copy without this).

## Target response shape (verified against the real SPA source)

From `Limitless marketing dashboard2/app/api.js`'s `alertsView(fix)`:

```jsonc
{ "feed": [
  { "id": "fusehealth-al-2", "ts": "2026-06-28", "kind": "anomaly", "severity": "high",
    "title": "Clicks dropped 38% vs. daily average", "detail": "...", "acknowledged": false }
] }
```

`kind` per `HANDOFF_SPEC.md`'s alert object: `anomaly|ranking|backlink|technical|ads|ai|system`.

## Mapping — old MVP source → new shape

The old `alerts()` view already assembles anomalies, page-speed issues, indexing issues, and
technical issues onto one page — but only two of those map naturally to a flat "one alert per
event" feed with a real acknowledgment story:

| Source | `kind` | Real ack support? | In scope for `feed[]`? |
|---|---|---|---|
| `Anomaly` rows (`_get_all_anomalies`) | `"anomaly"` | Yes — `Anomaly.is_acknowledged`, already has a working mutation (`acknowledge_anomaly` view) | Yes |
| `TechnicalIssue` rows (`_get_technical_issues`, unlimited — not the display-capped version) | `"technical"` | No — `TechnicalIssue` has no acknowledgment column | Yes, `acknowledged` honestly hardcoded `false` (not fabricated — there is genuinely no ack state for this type today) |
| `PageSpeed` rows | — | No | **Out of scope** — `PageSpeed` has no title/detail/severity fields, just numeric scores; it doesn't map to a discrete "alert event" the way anomalies/technical-issues do. Stays a dedicated section on the old page, not folded into this feed. |
| `IndexingStatus` rows | — | No | **Out of scope**, same reasoning as PageSpeed — a status table, not a discrete alert-event stream. |
| Backlinks/Ads/AI kinds | `"backlink"/"ads"/"ai"` | N/A | **Out of scope** — those features aren't built yet (Phase C/D); no data exists to alert on, so nothing to include (honest empty, not a gap). |

**`id` scheme**: prefixed by source so a single flat list stays unambiguous —
`f"anomaly-{Anomaly.id}"` / `f"issue-{TechnicalIssue.id}"`. Both underlying tables have real
integer PKs already.

**Sort order**: by date descending, then severity (high → medium → low), matching the old
page's "problems first" convention already used elsewhere (e.g. `_get_indexing_issues`'s
sort).

**Mutation (`POST /api/alerts/<alert_id>/ack`) is explicitly OUT of scope for B4** — B1/B2/B3
were all read-only GET endpoints matching the pattern established since Phase A; adding the
first mutation endpoint is a distinct concern deserving its own design/plan cycle, not
folded into a page-port task. The old page's existing `acknowledge_anomaly` HTMX endpoint is
untouched and keeps working for the old UI in the meantime.

## Architecture

- **Task 1 (cross-cutting, recommended by B3's final review)**: extract
  `resolve_range_periods(request, slug) -> (site_id, curr_start, curr_end, prev_start,
  prev_end)` in `apps/api/views.py` — wraps `resolve_project_or_404` + `OverviewQuerySerializer`
  + `latest_data_anchor` + `range_to_period_dates` in one call. Retrofit `ProjectOverviewView`
  and `ProjectPositionsView` to use it (their existing tests must pass unchanged — zero
  behavior change, same as B2's Task 1 pattern for `resolve_project_or_404`/`latest_data_anchor`).
- New file `apps/dashboard/services/alerts_service.py`:
  - Raw calculators: `query_alert_anomalies_raw(site_id, limit=None)` (unlimited, unlike the
    old page's capped `_get_all_anomalies`), `query_alert_technical_issues_raw(site_id,
    limit=None)` (unlimited, unlike the capped `_get_technical_issues`) — new functions, NOT
    modifications to the existing capped versions (those stay as-is for the old page's
    display tables, out of scope, same "don't touch working display-capped helpers" pattern
    as B1/B3).
  - `build_alerts_response(site_id) -> dict` — the API-shaped builder. No `range`/`curr_start`
    params needed — alerts are inherently "current state", not period-scoped (matches
    `HANDOFF_SPEC.md`'s endpoint table: `alerts | — | feed[...]`, no `range` column).
- `apps/api/views.py`: `ProjectAlertsView(APIView)` on `GET /api/projects/<slug>/alerts` — no
  `range` param, uses only `resolve_project_or_404` (not the new `resolve_range_periods`,
  since this endpoint has no period concept).

## Verification

- Full suite green.
- Old `/alerts/` page completely untouched (new unlimited raw queries are new functions, not
  modifications).
- `GET /api/projects/<slug>/alerts` returns real data; every feed item's `id` is
  source-prefixed and unique; `acknowledged` reflects real `Anomaly.is_acknowledged` for
  anomaly-kind items and is honestly `false` for technical-issue-kind items.

## Explicitly out of scope

`POST /api/alerts/<id>/ack` mutation (separate future task). PageSpeed/Indexing as feed
items (no natural mapping). Backlinks/Ads/AI-kind alerts (features don't exist yet).
