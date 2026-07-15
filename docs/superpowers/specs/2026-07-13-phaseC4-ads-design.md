# Phase C4 — Ads Design Spec

> Status: approved, self-authored (continuing autonomously per user's standing "continue
> according to plan" instruction). Last of four Phase C sub-projects (C1 Backlinks, C2 Site
> Audit, C3 Off-site SEO all done). Branched from `phase-c3-offsite-seo`.

## Why this phase is different from C1-C3

Ads is the biggest remaining page: FOUR sub-pages (Paid Overview / Campaigns / Search Terms /
Attribution), all fed by **one shared endpoint** — `GET /api/projects/<slug>/ads?range=` — per
`HANDOFF_SPEC.md` §2.7 and confirmed by the SPA's own `ADSTABS = ['ads','campaigns','terms',
'attribution']` routing (`static/spa/index.html:3429`, single fetch keyed off `ADSTABS.includes(tab)`).

**Critical difference from C1-C3's `state:"setup"` convention:** the shared computed-values
block (`static/spa/index.html:5956-6269`) has **no setup guard anywhere** — no tab in this
codebase's SPA branches on a `state === "setup"` sentinel here, unlike Backlinks/Site
Audit/Offsite. It unconditionally does `t.roas.toFixed(2)` (`t = data.totals`), `pc.projected >
pc.monthly_budget * 1.05` (`pc = data.pacing`), `tr.map(d => d.spend)` (`tr = data.trend`).
**If `totals`/`prev`/`pacing` are `{state:"setup"}` objects, this crashes** (`undefined.toFixed`
is a `TypeError`). The C1-C3 sentinel-object convention would break this page. Only genuinely
absent **arrays** (`campaigns`/`searchTerms`/`attribution`/`landingPages`/`negatives`) are safe
to leave honestly empty — `totals`/`prev`/`pacing`/`syncMeta`/`window` must be real, fully-keyed
objects with honest zero/null values, never a bare sentinel.

**Connector status**: `pipeline/connectors/google_ads.py` exists and is well-built (real GAQL
query for campaign-level spend/clicks/impressions/conversions) but `.env`'s
`GOOGLE_ADS_DEVELOPER_TOKEN`/`GOOGLE_ADS_CUSTOMER_ID`/`GOOGLE_ADS_LOGIN_CUSTOMER_ID` are blank —
credential-blocked identically to DataForSEO/LinkedIn/Meta. `AdMetricDaily` (the backing table)
currently has **0 rows** for the real site.

**Structurally nonexistent, not just credential-blocked**: no `SearchTerm` or `Attribution`
model exists anywhere in `pipeline/db/schema.py` — Search Terms and Attribution are 100%
honest-empty regardless of credentials, same category as C2's 28-rule checks catalog.

**Do not port `_get_ads_overview`'s `roi` field** (`apps/dashboard/views.py:130`,
`f"${(conversions * 50 / cost):.2f}"`) — it's explicitly commented "rough estimate," i.e. an
invented constant ($50/conversion), exactly the fabrication this project forbids. Not part of
this response's shape anyway (SPA reads `roas`/`conv_value`, not `roi`).

## Mapping — what's real vs. honest-empty/zero

| Field | Source | Status |
|---|---|---|
| `totals.spend/clicks/impressions/conversions` | Real — `sum(AdMetricDaily.*)` over period (same pattern as `_get_ads_overview`) | Real (currently 0, honestly) |
| `totals.cpc` | Real — `spend/clicks` if `clicks>0` else honest `0` | Real |
| `totals.roas` | Real — spend-weighted avg of `AdMetricDaily.roas` (`sum(spend*roas)/sum(spend)` if `spend>0` else `0`) — the only defensible aggregation since revenue itself isn't stored, only a per-row ratio | Real (honest `0` today) |
| `totals.conv_value` | No revenue/value column exists on `AdMetricDaily` | Honest `0`, not fabricated |
| `totals.ga4_key_events` | Real — `SEODaily.conversions` summed over the period (GA4-side, same cross-reference `_get_ads_overview`'s signals already imply) | Real |
| `totals.ga4_revenue` | No revenue column exists on `SEODaily` either (confirmed in C3's design spec) | Honest `0` |
| `prev.*` | Same fields, previous period | Real / honest zero, mirrors `totals` |
| `trend[]` (date/spend/conversions/ga4_key_events) | Real — daily `AdMetricDaily`+`SEODaily` aggregation, same shape as `offsite_service`'s daily trend | Real (per-day honest zeros while `AdMetricDaily` is empty) |
| `pacing.monthly_budget` | No budget-setting feature/table exists anywhere in this codebase | Honest `0` |
| `pacing.mtd_spend` | Real — `sum(AdMetricDaily.spend)` for the real calendar month-to-date (independent of the `range` param — pacing is always "this calendar month," matching the SPA's `dayLabel`) | Real |
| `pacing.projected` | Real derived formula — `mtd_spend / day_of_month * days_in_month` (standard run-rate math, not invented; `0` if `day_of_month` is `0`, can't happen for a real date) | Real |
| `pacing.day_of_month`/`days_in_month` | Real calendar values for today (`date.today()`) | Real |
| `pacing.pct` | Real — `min(100, round(mtd_spend/monthly_budget*100))` if `monthly_budget>0` else `0` (avoids div-by-zero; honest `0` since budget is always `0` today) | Real |
| `pacing.channels[]` | No per-platform budget data exists | Honest `[]` |
| `campaigns[]` | The SPA's Campaigns tab needs `id`/`status`(enabled/paused, live Google Ads state)/`budget_daily`/`lost_is_budget`(impression-share-lost-to-budget)/`type`/`adGroups[]`/per-row `prev` — **none of these exist in `AdMetricDaily`**, which only has spend/clicks/impressions/conversions/roas per campaign+platform+date. Inventing budget/status/adGroups values would be fabrication, not a reshape. With 0 real rows today regardless, the honest choice is a true empty array — richer campaign metadata is real, unvalidated Google Ads API integration work for a future task, not a guess to make now | Honest `[]` |
| `searchTerms[]` | No `SearchTerm` model exists | Honest `[]` |
| `attribution[]` | No `Attribution` model exists | Honest `[]` |
| `landingPages[]` | Would require joining ad campaigns to GA4 landing pages by UTM/campaign — no such join/table exists (different from C3's generic GA4 landing pages, this needs ads-attribution specifically) | Honest `[]` |
| `negatives[]` | No negative-keyword tracking table exists | Honest `[]` |
| `window.from/to/days` | Real — derived directly from the real `curr_start`/`curr_end` params already computed by `resolve_range_periods` | Real |
| `syncMeta.cadence/last_pull/next_pull` | No ads-sync-tracking table exists | Honest `None` (JS-side fallback needed — see SPA fidelity fix) |
| `syncMeta.ops_used/ops_limit/ga4_tokens_used/ga4_tokens_limit` | No live ops-quota tracking for ads exists | Honest `0` |
| `syncMeta.connected` | Real — reflects whether Google Ads credentials are present (`bool(GOOGLE_ADS_DEVELOPER_TOKEN and GOOGLE_ADS_CUSTOMER_ID)` from settings/env), same honesty pattern as C3's `connectors.linkedin` | Real (`False` today) |

## Architecture

- New file `apps/dashboard/services/ads_service.py`:
  - `query_ads_totals_raw(site_id, start, end)` — real `AdMetricDaily` aggregation (spend-weighted `roas`) + real GA4 `ga4_key_events` cross-reference from `SEODaily.conversions`.
  - `query_ads_trend_raw(site_id, start, end)` — real per-day aggregation, same shape/pattern as `offsite_service.query_offsite_trend_raw`.
  - `query_ads_pacing_raw(site_id)` — real calendar-month-to-date spend + honest-zero budget/projection math. Not period-scoped (always "this calendar month," independent of `range`).
  - `build_ads_response(site_id, curr_start, curr_end, prev_start, prev_end) -> dict` — assembles real `totals`/`prev`/`trend`/`pacing`/`window` plus honest `[]` for `campaigns`/`searchTerms`/`attribution`/`landingPages`/`negatives`, and a real-but-honest `syncMeta` (including the real `connected` flag).
- `apps/api/views.py`: `ProjectAdsView` on `GET /api/projects/<slug>/ads` — **range-aware**, uses `resolve_range_periods` (matches Positions/Offsite, not Backlinks/Audit which have no period concept — Ads genuinely has one: `totals` vs `prev`, `trend[]` over the window).
- **SPA fidelity fix, scoped precisely up front** (same discipline as C3, now three-for-three
  proactive): the shared `if (this.ADSTABS.includes(tab))` block reads `sm.cadence`/
  `fmtTs(sm.last_pull)`/`fmtTs(sm.next_pull)` with no fallback. `fmtTs(null)` → `new
  Date(null).toLocaleString(...)` → renders a fake-looking "Jan 1, 1970" timestamp, not a crash
  but a fabricated-looking date against honestly-null data — same class of issue as C3's
  `syncMeta.cadence`/LinkedIn-badge findings. Additionally, `static/spa/index.html:2276`-ish
  region (verify exact line at implementation time) hardcodes a green "connected" dot next to
  the sync line — same hardcoded-honesty-badge issue as C3's LinkedIn card, must gate on the
  real `syncMeta.connected` field this design adds specifically to support that fix. Task 3
  applies both fixes, narrowly, mirroring C3's approach — not a whole-tab guard (unnecessary:
  every `.map`/`.filter`/`.reduce`/`Math.max.apply(...).concat([1])` in the Ads block already
  handles empty arrays safely, and `totals`/`prev`/`pacing` are real fully-keyed zero-value
  objects per the mapping table above, so no `.toFixed()`-on-undefined crash risk exists once
  Task 1/2 ship the response shape this spec commits to).
- **Mutation endpoints explicitly out of scope**: `POST /ads/status` (toggle campaign
  enabled/paused), `/ads/budget` (edit daily budget), `/ads/negatives` (add negative keyword),
  `/ads/promote` (promote search term to tracked keyword) all call live Google Ads mutate
  operations. With `campaigns`/`searchTerms` honestly empty, none of these controls render any
  rows today (`rows.map(...)` on `[]` → no toggle switches/budget editors/negative-menus ever
  appear), so there's no dead/broken UI control to guard — these are real future integration
  work once Google Ads credentials exist, not something to stub now.

## Verification

- Full suite green.
- No existing page in `apps/dashboard/views.py` is touched (new-shape work — `ads()`/
  `_get_ads_overview`/`_get_campaigns` stay exactly as they are for the old page).
- `GET /api/projects/<slug>/ads?range=` returns real `totals`/`prev`/`trend`/`pacing`/`window`
  (currently all-honest-zero since `AdMetricDaily` has 0 rows) and honest `[]` for
  `campaigns`/`searchTerms`/`attribution`/`landingPages`/`negatives` — never fabricated numbers,
  never an invented `roi`-style estimate.
- SPA renders the Ads tabs without crashing and without a fabricated-looking timestamp or a
  false "connected" claim, verified by direct trace (no JS test harness exists for this SPA,
  same limitation noted in every prior phase's review).

## Explicitly out of scope

- Rich per-campaign metadata (`status`/`budget_daily`/`lost_is_budget`/`type`/`adGroups[]`) —
  needs new schema + a richer Google Ads API integration once credentials exist.
- `SearchTerm`/`Attribution` models and their connectors — new schema design, future phase.
- The 4 mutation endpoints (`ads/status`, `ads/budget`, `ads/negatives`, `ads/promote`).
- Ads-attributed `landingPages[]` (campaign↔GA4-landing-page join).
- Phase D (AI Optimization / Keyword+Prompt Explorer), Phase E (Settings), Phase F (deploy).
