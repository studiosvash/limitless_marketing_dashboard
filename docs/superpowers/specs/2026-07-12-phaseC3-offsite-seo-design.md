# Phase C3 — Off-site SEO Page Design Spec

> Status: draft, self-authored (continuing autonomously per user's standing "continue... without
> any permission" instruction, most recently confirmed as "continue same way — one sub-phase at a
> time"). Third of four Phase C sub-projects (C1 Backlinks, C2 Site Audit done; C3 Off-site SEO,
> C4 Ads remain). Branched from `phase-c2-site-audit`.

## What "Off-site SEO" means in this app (not backlinks/citations)

Despite the name, this page is **not** a backlinks/citations/brand-mention page (that's C1). Per
the Phase A roadmap doc (`docs/superpowers/specs/2026-07-10-limitless-migration-roadmap-and-phaseA-design.md:189`)
and `HANDOFF_SPEC.md` §2.6, "Off-site SEO" here means **GA4 referral/organic-social traffic**:
session totals, channel mix (organic social / referral / direct / etc.), per-platform social
impressions, top referring domains, and top landing pages by session — everything downstream of
"how do off-site channels drive traffic to the site," not "who links to us" (C1) or "is the site
technically crawlable" (C2).

## Why this phase is scoped differently again — a real, live connector, but missing dimensions

Unlike C1/C2 (both blocked entirely on unfunded DataForSEO credentials), **GA4 is live and
credentialed today** (`GA4_PROPERTY_ID` set, real OAuth, `pipeline/connectors/ga4.py` runs on
every sync) — so this is genuinely closer to "build what's new" than "reshape what's blocked."
However, the current `GA4Connector.fetch()` only pulls `date, country, deviceCategory, pagePath`
into `SEODaily` — it does **not** fetch `sessionDefaultChannelGroup`, `sessionSource`, or
`totalRevenue`, so there is no channel/source dimension anywhere in this database. Adding those
GA4 report dimensions, extending `SEODaily`'s schema, and re-syncing historical data is real,
separate connector/schema work — the same category of "don't guess at an unvalidated integration
in one sitting" reasoning C1/C2 already established, just for a different reason (missing
dimensions, not missing credentials).

**Decision:** build ONLY an honest reshape of what `SEODaily` already stores today — `sessions`,
`engagement_rate`, `conversions`, `users`, `landing_page` (all real, already populated by every
GA4 sync since Phase 3 of the old MVP) — for `totals`/`trend`/`landingPages`. Everything requiring
a channel/source/platform dimension (`channels[]`, `referrers[]`, `social[]`, per-platform
`connectors{}`) reports `state:"setup"` or an honest `false`/`[]`. LinkedIn/Meta connectors
(`pipeline/connectors/linkedin.py`/`meta.py`) have blank credentials in `.env` today, and no
Reddit/YouTube/X/Instagram connector exists as a file at all — so `social[]` is `state:"setup"`
regardless of GA4's own readiness.

## Mapping — what's real vs. `state:"setup"`

| Field | Source | Status |
|---|---|---|
| `totals.sessions/users/engagementRate/keyEvents/engagedSessions` | Real — `SEODaily.sessions`/`users`/`engagement_rate`/`conversions` aggregated over the period (same `func.sum`/`func.avg` pattern as `overview_service.get_kpi_raw`). `keyEvents` = `conversions` (GA4's current term for what this column already tracks; not a new metric). `engagedSessions` = `round(sessions * engagement_rate)`, the same GA4-standard derivation used in `trend[]` below, summed for the whole period instead of per-day — the SPA's KPI card (`index.html:5012`) reads this field directly off `totals`, not just off `trend` | Real |
| `totals.revenue` | No revenue column exists in `SEODaily` (GA4 revenue events aren't fetched) | Honest `0`, not fabricated — same "true zero vs. fabricated" distinction C2 established for `totals.errors/warnings/notices` |
| `totals.referringDomains` | Would require the `sessionSource` dimension, which doesn't exist in this DB | Honest `0` (not derivable without the missing dimension, not invented) |
| `prev.*` | Same fields, previous period — real, mirrors every other range-taking endpoint's curr/prev pattern | Real |
| `trend[]` (date, sessions, engagedSessions, keyEvents, revenue) | `sessions`/`keyEvents` real (daily `SEODaily` aggregation, matching `overview_service.query_daily_traffic_raw`'s exact pattern). `engagedSessions` = `round(sessions * engagement_rate)` — GA4's own standard derived-metric formula, not invented. `revenue` honest `0` per-day (same reasoning as totals) | Real (revenue sub-field honest zero) |
| `channels[]` | Requires `sessionDefaultChannelGroup` — not fetched | Honest `[]` (true empty array — matches the established C1/C2 convention that array-typed fields report `[]`, not a `state:"setup"` object; only object-typed fields like `syncMeta` below use `state:"setup"`) |
| `referrers[]` | Requires `sessionSource` — not fetched | Honest `[]` |
| `social[]` (per-platform impressions) | Requires per-platform connectors; LinkedIn/Meta credentials blank, Reddit/YouTube/X/Instagram connectors don't exist | Honest `[]` |
| `landingPages[]` | Real — reshape of `SEODaily.landing_page` grouped by `sessions`/`engagement_rate`/`conversions` over the period (same shape as the existing-but-unused `_get_page_health`'s landing_page grouping in `apps/dashboard/views.py:594-612`, adapted to GA4 metrics instead of GSC clicks/impressions) | Real |
| `connectors{linkedin,reddit,youtube,x,facebook,instagram}` | All currently unconnected — an honest `false` for every key is itself real information (not a placeholder), matching `.env`'s actual blank credentials | Real (all `false`) |
| `syncMeta{cadence,last_pull,next_pull,ga4_tokens_used,ga4_tokens_limit}` | No sync-metadata tracking table exists for GA4 pulls specifically | `state:"setup"` (the one genuinely object-shaped field in this response) |

**Why arrays are `[]` and not `state:"setup"` here (correcting an earlier draft of this table):**
matches the convention C1 (`months`/`types`/`asBuckets`/`refDomains`/`anchors`/`gapDomains`) and C2
(`domainChecks`/`checks`/`crawledPages`/`structure`/`snapshots`) already established — only
object-typed fields (C1's `summary`, C2's `score`/`crawl`/`catScore`/`cwv.tbt`) get
`{"state": "setup"}`; array-typed fields always get a true `[]`. This choice also has a direct,
verified consequence for the SPA fix below: because `channels`/`referrers`/`social` are real
(empty) arrays rather than an object lacking array methods, `data.channels.map(...)`,
`data.referrers.slice(...)`, and `data.social.find(...)` (already defensively `|| {...}`-guarded
in the SPA source) all execute safely against `[]` with no crash — unlike C1/C2, where the
analogous fields were single rich objects the SPA dereferenced without any null-guard.

## Architecture

- New file `apps/dashboard/services/offsite_service.py`:
  - `query_offsite_totals_raw(site_id, start, end) -> dict` — `sessions`/`users`/`engagement_rate`/`conversions` aggregated, same `get_stats`-closure pattern as `overview_service.get_kpi_raw`.
  - `query_offsite_trend_raw(site_id, start, end) -> list[dict]` — daily `date/sessions/engagedSessions/keyEvents/revenue`, same pattern as `overview_service.query_daily_traffic_raw`.
  - `query_offsite_landing_pages_raw(site_id, start, end) -> list[dict]` — `landing_page` grouped by sessions/engagement_rate/conversions, capped `.limit(50)` (matching the existing `_get_page_health` cap convention).
  - `build_offsite_response(site_id, curr_start, curr_end, prev_start, prev_end) -> dict` — assembles real `totals`/`prev`/`trend`/`landingPages` plus honest `state:"setup"`/`[]`/`false` for the rest.
- `apps/api/views.py`: `ProjectOffsiteView` on `GET /api/projects/<slug>/offsite?range=7d|30d|90d` — **does** take a `range` param (unlike C1/C2's current-state endpoints), so uses the shared `resolve_range_periods` helper, matching `ProjectOverviewView`/`ProjectPositionsView`.
- **SPA fidelity fix, planned proactively and scoped precisely up front** (not discovered post-hoc as in C1, nor fixed-but-unplanned as in C2): independent research plus a direct read of the current `if (tab === 'offsite')` block (`static/spa/index.html:4996-5090`) traced every one of its data dependencies against the real/`[]` shape this design commits to, field by field. Conclusion: **this tab does not need the C1/C2-style whole-tab "not connected yet" guard at all.** Because `totals`/`prev`/`trend`/`landingPages` are always real objects/arrays (never `undefined` or a bare `{state:"setup"}`) and `channels`/`referrers`/`social` are real (possibly-empty) arrays — not setup-state objects — every `.map`/`.slice`/`.find`/`Math.max.apply(...).concat([1])` call in the block already executes safely against empty data (the SPA's own `.find(...) || {...}` and `.concat([1])` guards do the rest). The **only** fidelity gap is cosmetic: `data.syncMeta` is the one genuinely `state:"setup"` object field, and lines 5007-5008 (`off.cadence`/`off.tokens`) read `.cadence`/`.ga4_tokens_used`/`.ga4_tokens_limit` off it with no fallback, producing literal `"undefined / — GA4 tokens"` text in the source banner. Task 3 fixes just those two lines — a 2-line change, not a tab-wide guard — and is called out explicitly so it isn't mistaken for a shortcut.

## Verification

- Full suite green.
- `GET /api/projects/<slug>/offsite?range=30d` returns real `totals`/`prev`/`trend`/`landingPages`
  (currently reflecting whatever real GA4-synced data exists) and honest `state:"setup"`/`[]`/
  `false` for `channels`/`referrers`/`social`/`syncMeta` — never fabricated numbers.
- SPA Off-site SEO tab renders a clean "not connected yet" state (or partial real KPIs — see Task
  3 brief for the exact decision) instead of crashing, when fed the honest setup-mixed payload.

## Explicitly out of scope

- Extending `GA4Connector.fetch()` to pull `sessionDefaultChannelGroup`/`sessionSource`/
  `totalRevenue` dimensions, the corresponding `SEODaily` schema migration, and historical
  backfill — real, scoped connector/schema work for a future phase, not something to guess at
  field-by-field here.
- LinkedIn organic-social API integration (only LinkedIn *Ads* connector exists today, a
  different product surface) and any Reddit/YouTube/X/Instagram connector — net-new integrations,
  each deserving their own credential/design/build cycle.
- `syncMeta` GA4-quota tracking — needs new schema, not attempted here.
- C4 (Ads).
