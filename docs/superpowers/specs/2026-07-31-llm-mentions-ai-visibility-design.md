# AI Visibility from DataForSEO LLM Mentions — design

**Date:** 2026-07-31
**Status:** approved, ready for implementation plan
**Scope:** Lean v1 — everything except the 12-week trend chart UI

> Note: `docs/superpowers/` is not authoritative in this repo (see `CLAUDE.md`). This file is the
> working design record. When the code lands, `.claude/api-reference.md`, `.claude/features.md`
> and `.claude/SKILLS.md` get updated in the same change — those stay the authoritative docs.

---

## Problem

The AI Optimization page's whole top half is hardcoded to zero. `sov`, `trend`, `topPages`,
`topDomains`, `kpis.impressions` and `kpis.cited_pages` are literal constants in
`apps/dashboard/services/ai_service.py`, and the UI labels them *"LLM Mentions API"* — an API
that is not integrated at all. The page claims to measure something it never measured.

Only one of DataForSEO's four AI Optimization APIs is wired (`ai_keyword_data`, which works and
feeds the AI Keywords tab). The **LLM Mentions API** — which provides exactly the missing
numbers — is unused.

## Why it is worth building (verified, not assumed)

A live `cross_aggregation_metrics` call on 2026-07-31 for `fusehealth.com` and its three tracked
competitors returned:

| Domain | Mentions | AI search volume | Share |
|---|---:|---:|---:|
| driphydration.com | 3,633 | 1,617,742 | 59.2% |
| mobileivmedics.com | 2,506 | 1,144,915 | 40.8% |
| **fusehealth.com** | **1** | **50** | **0.02%** |
| restoreiv.com | 0 | 0 | 0% |

The design mockups show a flattering **34%**. Reality is **0.02%** — fusehealth is effectively
invisible in AI answers while two competitors dominate. That gap is the entire justification for
this feature: the page must report the real number, not the mockup's.

The same response also revealed what AI actually cites in this niche (`youtube.com`,
`healthline.com`, `my.clevelandclinic.org`), which is a directly actionable content signal.

Platform reality from the same call: `google` (AI Overviews) 5,785 mentions vs `chat_gpt` 115.
The API supports **only these two platforms** — Claude, Gemini and Perplexity are not available
from DataForSEO at any price.

## Decisions

| # | Decision | Rationale |
|---|---|---|
| 1 | Store a **weekly snapshot** row; **defer the trend chart UI** | The API returns current state only, no history. Storing `week_start` costs one column; not storing it loses history permanently, since DataForSEO cannot backfill. The chart can be switched on later against data already collected. |
| 2 | Track **domain + brand name + aliases** together | One `aggregation_key` accepts up to 10 entities, so both cost the same single call. Domain citations feed *Cited Pages*; brand-name mentions feed *Brand Mentions* — matching what the labels already claim. |
| 3 | Runs in the **`ai` scope** — AI page refresh **and** Refresh all | Matches every other connector. The weekly guard (below) makes repeated refreshes free. |
| 4 | **Two tables**, discriminated by `subject_type` | SoV subjects and discovered domains share an identical grain (domain + week + mentions + volume). A `subject_type` column avoids a near-duplicate table and makes "which new domain is rising?" a single-table query. |
| 5 | **Never** a JSON blob per week | `ai_service.py:56-64` documents what that cost last time: unqueryable, capped at 50 entries, last-write-wins, trend "out of scope". Trend is the whole point here. |

## API call plan

Two endpoints, at most two calls per project per week.

| Call | Endpoint | Provides | When |
|---|---|---|---|
| 1 | `llm_mentions/cross_aggregation_metrics` | per-subject mentions + `ai_search_volume`, platform split, `total.sources_domain` (top domains) | always |
| 2 | `llm_mentions/top_pages` | your most-cited URLs | only if call 1 shows your domain mentions > 0 |

**Deliberately NOT called** — both are redundant against call 1, verified in the live response:

- `aggregation_metrics` — call 1's `items[]` already contains your own target's metrics.
- `top_domains` — call 1's `total.sources_domain` already returns the top domains (5 entries).
  If more than 5 rows are wanted later, add the dedicated endpoint then.

Target construction, one `aggregation_key` per subject:

```
you                 → [{domain: <site domain>}, {keyword: <brand>}, {keyword: <alias>}…]
<competitor domain> → [{domain: <competitor>}, {keyword: <competitor name>}]
```

Location and language come from the `sites.location` column where it is set, falling back to
`United States` / `en`. `sites.location` already exists (added by
`apps/sync/management/commands/add_project_fields.py`), so no schema change is needed for it.

## Cost controls

1. **Weekly dedupe (the important one).** `fetch()` first checks whether rows already exist for
   `(site_id, week_start)`. If they do it returns `[]` immediately — no HTTP call. Pressing
   "Refresh all" five times in a day costs **one** API call, not five. The guard lives inside the
   connector, so it applies no matter which code path triggers the sync.
2. **Skip unconfigured projects.** No brand and no competitors → no call. The data would be
   meaningless.
3. **Cap competitors at 9** (API allows 10 targets including yours).
4. **Record spend** through the existing `record_cost` helper so it appears in `connector_costs`
   and the Settings usage view.

Realistic steady-state cost: 2 projects × 1–2 calls, once per week.

**Edge case:** `cross_aggregation_metrics` requires **at least 2 targets**. A project with zero
competitors falls back to `aggregation_metrics` (one call) for its own mentions, and the SoV
section renders the "add competitors" state rather than a meaningless 100%.

## Schema

Two new tables in `pipeline/db/schema.py`, following the `AIKeywordData` pattern. Self-provisioned
on first use via `ensure_tables(session, Model)`.

```
llm_mention_metrics
  id, site_id, week_start, subject_domain, subject_type, platform,
  mentions, ai_search_volume, last_fetched
  UNIQUE(site_id, week_start, subject_domain, platform)
  INDEX(site_id, week_start)

llm_cited_pages
  id, site_id, week_start, url, mentions, ai_search_volume, platforms, last_fetched
  UNIQUE(site_id, week_start, url)
  INDEX(site_id, week_start)
```

- `week_start` is the **Monday of the ISO week** in which the sync ran (`date - timedelta(days=date.weekday())`), in UTC. This is the dedupe key, so it must be computed one way everywhere.
- `subject_domain` is the bare canonical host, via `pipeline/utils/site_ids.canonical_domain()` — the
  same normaliser the rest of the codebase now uses. For the `you` row it is the project's own host.
- `subject_type` ∈ `you` | `competitor` | `discovered`.
- `platform` ∈ `google` | `chat_gpt`. Only real platforms are stored; totals are summed in the
  service. Verified against live data — `driphydration: 3632 + 1 = 3633`,
  `mobileivmedics: 2392 + 114 = 2506`.
- `platforms` on `llm_cited_pages` is a JSON list, because the SPA reads `pg.platforms.join(' · ')`.

**Two traps this repo has already paid for** (`.claude/SKILLS.md` §9), both of which apply here:

- Every conflict-target column is **NOT NULL**. Postgres does not treat `NULL = NULL` as a
  conflict, so a null key column duplicates on every sync instead of updating in place.
- Batches go through `writer._dedupe_by_keys()` before the upsert. A duplicate conflict key makes
  Postgres raise `CardinalityViolation` and roll back the **entire batch** — and SQLite hides it
  completely, so the test suite cannot catch it.

## Components

**`pipeline/connectors/dataforseo_llm_mentions.py`** — `DataForSEOLLMMentionsConnector`,
`name = "dataforseo_llm_mentions"`.

- Subclasses `BaseConnector`; **does not override `sync()`**.
- `fetch()` returns one flat list where each record carries `_table: "metrics" | "pages"`.
  `_write_records()` splits on that key and calls the two upsert helpers within the single session
  `BaseConnector` provides. This keeps the two-table write inside the existing one-method contract.
- `AITarget` (brand/aliases/competitors) is imported **lazily inside `fetch()`** — connectors must
  not import Django models at module level, so the pipeline stays runnable outside Django.
- Registered in `sync_engine._get_connector`'s `connector_map`, then added to
  `PAGE_CONNECTORS["ai"]` and `ALL_CONNECTORS`.

**`pipeline/db/writer.py`** — `upsert_llm_mention_metrics()`, `upsert_llm_cited_pages()`.

**`apps/dashboard/services/llm_mentions_service.py`** — new module, so the 628-line
`ai_service.py` does not grow further.

- `query_mention_metrics_raw(site_id, weeks)` / `query_cited_pages_raw(site_id, week_start)` —
  one DB read each, wrapped in try/except, returning primitives.
- `build_visibility_block(site_id)` — assembles `sov`, the three KPI values, `topPages`,
  `topDomains` and `mentionPlatforms`.
- `ai_service.build_ai_response()` calls it and merges the result. `ai_service` stays the
  assembler; the computation lives in its own file.

## Data flow

```
Refresh (AI page or Refresh all)
  └─ sync_engine → DataForSEOLLMMentionsConnector.sync()
       ├─ week already stored?  → yes: return [] (no API call, no spend)
       ├─ cross_aggregation_metrics   → subject rows + discovered domains
       ├─ top_pages (only if own mentions > 0) → cited page rows
       └─ _write_records → upsert into both tables

GET /api/projects/<slug>/ai  (no external call, ever)
  └─ ai_service.build_ai_response
       └─ llm_mentions_service.build_visibility_block  → reads latest week
```

## Response shapes

Already defined by the SPA (`static/spa/src/js/pages/ai_optimization.js:119-172`) — the frontend
is built; only the data is missing.

- `sov` → `{you, delta, rows: [{domain, sov, mentions, isYou}]}`
- `kpis.mentions` / `.impressions` / `.cited_pages`
- `topPages` → `[{url, mentions, impressions, platforms: []}]`
- `topDomains` → `[{domain, share, mentions, isYou, isComp}]`
- `mentionPlatforms` → `[{id, name, color}]`

**SoV maths:** denominator is the sum of tracked subjects' mentions (you + competitors), so the
rows total 100% as the design shows. The API's own `total` (5,900) is deduplicated across
overlapping responses and is deliberately not used.

**`mentionPlatforms` and `llmPlatforms` must stop being the same list.** They currently both point
at the same four-item constant. Their sources differ:

| Field | Values | Source |
|---|---|---|
| `mentionPlatforms` | AI Overviews, ChatGPT (2) | DataForSEO LLM Mentions |
| `llmPlatforms` | ChatGPT, Claude, Gemini, Perplexity (4) | your own API keys, Prompts tab |

This matches the mockups exactly: the AI Visibility toggles show two platforms, the Prompts table
shows four columns.

**KPI sources change:** `mentions`, `impressions` and `cited_pages` come from LLM Mentions
(they are currently hardcoded 0 or counted from prompt runs). `prompt_coverage` continues to come
from prompt runs — a different measurement that stays as it is.

## Honest states

Rule #3 of this codebase: never fabricate a value to fill a shape. Each empty case has its own
truth.

| State | Shown |
|---|---|
| Never synced | Visibility block in setup state |
| No competitors configured | "Add competitors to see share of voice" — never a fake 100% |
| First week, no prior snapshot | `sov.delta = null` → neutral "no comparison yet" chip |
| Your domain never cited | "AI has not cited any of your pages yet" — a real finding, not an error |
| Zero-data competitor (e.g. `restoreiv.com`) | Listed at 0%, not hidden — absence is information |

**Pre-existing SPA bug that v1 must fix:** `ai_optimization.js:123` renders
`(sov.delta >= 0 ? '▲ +' : '▼ ')`, so a null delta prints **"▲ +0 pts vs. last week"** — claiming a
comparison that never happened. The SoV card ships in v1, so this is in scope.

**Pre-existing SPA bug deferred with the chart:** `ai_optimization.js:153` computes
`k / (d.trend.length - 1)`, which is `0/0 → NaN` when exactly one point exists, breaking the SVG.
`trend` stays `[]` in v1 so it cannot trigger, but this **must** be guarded before the chart is
enabled.

**Header copy:** "Brand visibility across ChatGPT, AI Overviews, Claude, Gemini & Perplexity"
overstates what LLM Mentions covers (two of five). Corrected to match reality.

## Testing

Per `.claude/SKILLS.md` §8 — a real external API is never called from a test; fake responses are
injected.

- **Connector — the weekly guard first.** Two consecutive `fetch()` calls must result in exactly
  one HTTP call. This is the test that protects the budget, so it is written first.
- **Connector — parsing.** A captured fake `cross_aggregation_metrics` response maps to the right
  subject rows, platform split and discovered domains. `top_pages` is skipped when own mentions
  are 0.
- **Connector — no competitors** falls back to `aggregation_metrics`.
- **Service.** SoV percentages sum to 100; platform totals sum correctly; each of the five honest
  states renders its own shape rather than a zero.
- **Writer.** `_dedupe_by_keys` applied; a re-sync of the same week updates rather than duplicates.

## Out of scope

- 12-week trend chart UI — data collection starts now, chart wired later.
- Dedicated `top_domains` endpoint — the free 5 rows from call 1 are enough for now.
- Claude / Gemini / Perplexity mention tracking — not offered by the API at any price.
- The existing per-prompt "Run now" feature — left exactly as it is.
