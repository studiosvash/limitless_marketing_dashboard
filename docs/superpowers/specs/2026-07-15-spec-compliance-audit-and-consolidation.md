# Spec-Compliance Audit & Consolidation Plan — 2026-07-15

**Spec of record:** `Limitless marketing dashboard2/HANDOFF_SPEC.md` (v2, supersedes API_CONTRACT.md v1).
**Frontend of record:** `Limitless marketing dashboard2/Limitless Marketing Dashboard v2.dc.html` — already
served at `/app/` as `static/spa/index.html` (byte-identical apart from 4 deliberate patches: static paths,
`apiBaseUrl:"/"`, `demoLatency:false`, "Priority feed"→"Intelligence").

---

## 1. Headline finding: the repo contains TWO divergent backend implementations

They forked from merge-base `8835cb7` (2026-07-10) and both build `apps/api` + services independently:

| Line | Where | Coverage | Tests | Last activity |
|---|---|---|---|---|
| **Phase stack** | `.worktrees/phase-e-settings` (branch `phase-e-settings`, tip of a stacked chain a→b→b2→b3→b4→c1→c2→c3→c4→d→e, **101 commits**) | **Full spec surface**: overview, seo, keywords (+track POST), positions, alerts, backlinks, audit, offsite, ads, ai (+8 actions), settings GET/PUT, sync POST, tasks GET, research, prompt-research | **274 passing** (`DJANGO_SETTINGS_MODULE=config.settings.local python -m pytest`) | 2026-07-15 08:55 |
| **Main line** | `main` (**13 commits** past merge-base) | overview, alerts, keywords (GET only), positions, backlinks, research; SPA serving at `/app/` | ~none (5 pipeline test files) | 2026-07-15 16:14 (`7a21c55` wire Positions) |

The main line has been *re-implementing pages the phase stack already finished* (keywords, backlinks,
positions). Both lines also patch the same SPA copy (`static/spa/`).

**⚠ A commit landed on main at 16:14 today, during this analysis — if another Claude/dev session is still
running against main, consolidation must wait until it stops.**

## 2. Page-by-page gap matrix (SPA tab → backend)

Status shown as **main / phase-e**. "DB" = reads only the database (per the core contract). No fixture or
demo data was found in either line's responses — unconnected modules honestly return `setup`/zero states.

| SPA tab | Endpoint | main | phase-e | Remaining gap (on phase-e) |
|---|---|---|---|---|
| Overview | GET `…/overview?range` | ✅ DB | ✅ DB | AI/Paid pillars stay `setup` until AI + Ads data exist |
| SEO | GET `…/seo` | ❌ 404 | ✅ DB | — |
| Keywords | GET `…/keywords` | ⚠ shape gaps (no cpc/impr/ctr/serpFeatures, `monthly:[]`) | ✅ | verify per-keyword `monthly` sparkline data |
| — track keyword | POST `…/keywords` | ❌ | ✅ | — |
| Positioning | GET `…/positions?range` | ✅ (competitors empty) | ✅ | competitor grid needs `dataforseo_serp_competitors` synced |
| Backlinks (4 sub-tabs) | GET `…/backlinks` | ⚠ empty-state omits `kpis`/`syncMeta` | ✅ | `gapDomains` needs `domain_intersection` connector (missing) |
| Site Audit | GET `…/audit` | ❌ 404 | ✅ | real crawl blocked: DataForSEO balance |
| — hide check | POST `…/audit/toggle-check` | ❌ | ❌ | **build** |
| Off-site SEO | GET `…/offsite?range` | ❌ 404 | ✅ | platform impression connectors return `connected:false` (spec-OK) |
| AI Optimization | GET `…/ai` | ❌ 404 | ✅ | — |
| — 8 AI actions | POST `…/ai/:action` | ❌ | ✅ (run/inspect 4xx — no LLM connectors) | **build LLM Mentions/Responses + ChatGPT-scraper connectors** |
| Ads (4 sub-tabs) | GET `…/ads?range` | ❌ 404 | ✅ | real data blocked: Google Ads creds empty |
| — status/budget/negatives/promote | POST `…/ads/*` | ❌ | ❌ | **build** (record-intent semantics per spec §8) |
| Alerts | GET `…/alerts` | ✅ (ack ignored) | ✅ | — |
| — acknowledge | POST `/api/alerts/:id/ack` | ❌ | ❌ | **build** (needs persisted ack + stable alert ids) |
| Settings (8 groups in UI) | GET/PUT `…/settings` | ❌ 404 | ✅ (team/security → explicit 4xx, not persisted) | decide: persist team/security JSON (spec §9.4 says persisting is enough) |
| Refresh (all scopes) | POST `…/sync` → `{task_id,est_cost,steps[]}` | ❌ (only legacy HTMX `/sync/…`) | ✅ | — |
| Progress polling | GET `/api/tasks/:id` | ❌ | ✅ | — |
| Keyword Explorer | POST `/api/research` | ✅ live DataForSEO | ✅ | blocked by DataForSEO balance |
| Prompt Explorer | POST `/api/prompt-research` | ❌ | ✅ | — |
| Add website → switch | GET/POST `/api/projects` | ✅ | ✅ | — |

## 3. Data layer & connectors (shared pipeline, both lines)

**Storage exists** for: sites (multi-project w/ per-site `gsc_property`+`ga4_property_id`), GSC/GA4 dailies,
keyword_rankings, backlinks + JSON snapshot, technical issues, page speed, indexing, anomalies, competitor
tables, AI keyword volumes, refresh runs. *(Phase branches add more — inventory during consolidation.)*

**Missing / broken vs spec §3:**
- **Connectors absent:** DataForSEO LLM **Mentions**, LLM **Responses**, **ChatGPT scraper** (AI Optimization
  live data); `domain_intersection` (backlink Link Gap); `keyword_suggestions`/`related_keywords`/
  `search_intent` (Explorer match-type coverage); **OpenAI weekly-summary generator** (table + reader exist,
  no writer — `OPENAI_API_KEY` present but unused).
- **Cost/usage tracking:** DataForSEO per-call `cost` is parsed then discarded; no usage table (spec §5).
- **Sync registry:** all DataForSEO connectors + Google Ads are commented out of `PAGE_CONNECTORS`
  (`pipeline/services/sync_engine.py:26`) — backlinks/ads pages sync **zero** connectors.

**External blockers only the owner can clear:**
1. **DataForSEO account balance is negative** → backlinks refresh, OnPage crawl, SERP, Explorer, AI-keyword
   volumes all disabled. Top up, then re-enable the connectors in `PAGE_CONNECTORS`/`ALL_CONNECTORS`.
2. **Google Ads API credentials empty** (`GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`,
   `GOOGLE_ADS_LOGIN_CUSTOMER_ID`) → Ads page can only show empty/setup state.
3. (Optional) `ANTHROPIC_API_KEY` if Claude should write the weekly summary instead of OpenAI.

## 4. Consolidation plan (recommended)

**Base = `phase-e-settings`** (superset, 274 tests). **Port from main** the newer, SPA-critical fixes:
`static/spa/app/api.js` race-fix (baseUrl `'/'` default + CSRF echo, 13:35 today), any backlinks-snapshot or
keyword-explorer improvements from `c454329`/`367278b`/`7a21c55` that phase-c1/b2/b3 lack (diff per file),
and the `feat/phase-a-overview-api` SPA-serving commits already on main.

Steps:
1. **Freeze main** (confirm no other session is committing).
2. `git merge phase-e-settings` into `main`; for conflicted `apps/api/*`, `apps/dashboard/services/*`,
   `static/spa/*` prefer **phase-e**, then re-apply main's api.js race-fix and diff-check the 3 wiring
   commits for anything phase-e lacks.
3. Run the 274-test suite + boot a fresh single server, click through every tab at `/app/` (memory:
   kill stale runservers first).
4. Then close the remaining gaps in order:
   a. alerts ack (model + endpoint + stable ids) · audit/toggle-check · 4 ads mutations — small, unblocked.
   b. Persist settings team/security groups (JSON per spec §9.4).
   c. OpenAI weekly-summary cron/command (key exists).
   d. Cost/usage recording into settings `usage` (spec §5).
   e. After DataForSEO top-up: re-enable connectors, add `domain_intersection` + Explorer match-type
      endpoints (§2.9), verify Backlinks/Audit/Explorer with real data.
   f. After Google Ads creds: wire ads connector into sync, verify Ads tabs.
   g. LLM Mentions/Responses + scraper connectors → AI Optimization live (biggest new build).
5. Production hardening: Postgres for Django default DB (decided 2026-07), delete stale worktrees after
   merge, single auth story (session same-origin is fine per current SPA), remove legacy HTMX dashboard
   only when the SPA fully replaces it (user decision).

## 5. Static-data verdict (the user's core question)

The served SPA at `/app/` calls the real API for **every** tab (`baseUrl:"/"`; fixtures inert). Nothing in
either backend line fabricates data. What *looks* like "static data" today is actually:
- tabs whose endpoint 404s on main (seo/audit/ai/offsite/ads/settings) → SPA error panel, or
- honest empty/setup states where connectors are disabled (backlinks/ads) or never built (AI), or
- the **design file opened directly** (fixture mode, `baseUrl:""`) — that copy is *supposed* to show fixtures.

Consolidating to phase-e + clearing the two credential blockers is what makes every page show live DB data.
