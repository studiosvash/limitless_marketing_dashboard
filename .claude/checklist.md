# FuseHealth — Production Migration Checklist

**From:** Streamlit MVP → **To:** Django + HTMX + Tailwind (production)
**Users:** 2–3 internal (Founder · SEO · Ads Manager)
**Deployment:** VPS (Nginx + Gunicorn + systemd)

> This file now lives at `fusehealth/.claude/checklist.md` and is the live build plan
> referenced by `fusehealth/CLAUDE.md`. All paths below are relative to the project root
> `fusehealth/`.

**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked / needs decision

> **Companion doc:** `FEATURES.md` (project root) is the **simple, client-facing** description of
> what the dashboard does — shareable, no status tags. **All build status/progress is tracked
> here** in this checklist. If a feature's *scope* changes (add/drop/rename), update both docs.

---

## Core Product Behavior (the contract — never violate)

1. The dashboard **always reads from the database.** It never calls an external API on page load.
2. A global **"Refresh All Data"** button fetches every API → writes to DB → shows new data.
3. Each page has its **own refresh button** that fetches only that page's relevant APIs → updates DB → reloads that page's data.
4. During any refresh, the user sees a **live progress bar** showing each API completing in real time.
5. Until a refresh runs, the user keeps seeing the **last saved data** from the database.

---

## PHASE 0 — Project Brain & Scaffold

### 0.1 — Claude Brain Files *(format designed via skill-creator principles, not copied from old files)*
- [x] Create `checklist.md` *(this file; now at `.claude/checklist.md`)*
- [x] Create thin root `CLAUDE.md` pointer (workspace root) → routes to `fusehealth/CLAUDE.md`
- [x] Create `fusehealth/CLAUDE.md` — lean auto-loaded router; the always-in-context brain
- [x] Create `.claude/PRODUCT_CONTEXT.md` — what we build, who uses it, the core contract
- [x] Create `.claude/ARCHITECTURE.md` — real scaffold structure, layers, data flows
- [x] Create `.claude/SKILLS.md` (v1) — coding standards
- [x] Create `.claude/FILE_INDEX.md` — ground-truth file map (living)
- [x] Move `checklist.md` → `.claude/checklist.md`
- [ ] `.claude/DESIGN.md` — authored in Phase 1 (after design discussion)
- [ ] `.claude/DATABASE.md` — authored in Phase 3 (after schema discussion)
- [ ] `.claude/API_REFERENCE.md` — authored in Phase 4 (after API audit)

### 0.2 — Django Scaffold
- [x] Scaffold clean Django project in `fusehealth/` (`config/` package, `manage.py`)
- [x] Split settings → `base.py`, `local.py`, `production.py`
- [x] Configure dual databases (`django_internal.db` Django ORM · `fusehealth.db` SQLAlchemy)
- [x] Create apps `accounts`, `dashboard`, `sync`; register; configure templates/static dirs
- [x] `python manage.py check` passes with zero errors *(verified)*
- [x] `python manage.py migrate` applied to `django_internal.db` *(verified)*

### 0.3 — Environment & Secrets
- [x] Audit every credential via `scripts/audit_env.py` (live auth tests, no secrets printed)
- [x] Add Django vars to `.env.example` (`DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, CSRF origins)
- [x] Write `.env.example` — every var commented + availability status
- [x] Add `.gitignore` (.env, *.db, venvs); `requirements.txt`
- [x] Copy working `.env` into project root (git-ignored)

**Audit result (2026-06-10):**
- READY (live auth PASS): Google OAuth → GSC + GA4 · OpenAI · DataForSEO *(auth ok)*
- PRESENT: Google API key (PageSpeed)
- ⚠ DataForSEO **balance negative** — top up before SERP/Keywords/Backlinks/OnPage work
- EMPTY (unavailable): Google Ads · Meta · LinkedIn · Webflow · WordPress · Framer

---

## PHASE 1 — Design System *(discussion before any template)*
- [x] Lock visual identity — **light & airy**, **indigo/violet** accent, **Inter** type
- [x] Lock component style — cards, tables, buttons, badges, charts (Plotly theme)
- [x] Mockup built + approved by user (`scratch/mockup_overview.html`)
- [x] Write `.claude/DESIGN.md` + add design rules/pointer to `SKILLS.md`
- [x] Build `base.html` + `_sidebar` / `_topbar` / `stat_card` / `refresh_button` / `sync_progress`
- [x] Build `static/css/global.css`; wire Tailwind CDN + brand tokens + HTMX + Plotly + Inter
- [x] Verify render via Django test client — Overview page returns 200 with all elements
- [ ] *(deferred to Phase 4/5)* HTMX wiring of Refresh button + live `/sync/status/` polling

---

## PHASE 2 — Authentication ✅
- [x] Roles: `founder` (all) · `seo` (SEO/keywords/pages/backlinks/positioning/insights/alerts) · `ads` (ads/overview/alerts)
- [x] `UserProfile` model with `role` + `can_access()`; auto-create signal
- [x] `manage.py seed_users` — founder/seo/ads from env passwords (temp fallback + warning)
- [x] Branded login page (`registration/login.html`) + logout button in sidebar
- [x] `LoginRequiredMiddleware` protects all views; login is `@login_not_required`
- [x] `@role_required` decorator applied (Overview guarded; applied per page in Phase 5)
- [x] **Verified:** anon→302 login · login works · role matrix correct (seo≠ads)
- [ ] *(Phase 6)* custom 403 page for blocked roles

---

## PHASE 3 — Database Design ✅
- [x] Discuss + decide storage for each source (two-DB boundary spec in `docs/superpowers/specs/2026-06-11-phase3-database-design.md`)
- [x] Design production schema — types, NOT NULL, indexes, upsert keys (18 tables in `pipeline/db/schema.py`)
- [x] `SyncLog` + `RefreshRun` Django models (connector, status, started/finished, records_written, error)
- [x] `Insight` Django model (team, date, impact, site_url, created_by)
- [x] Prediction layer — `metric_forecasts`, `keyword_opportunities`, `risk_signals`
- [x] Migrate real MVP data into `fusehealth.db` + Django: 5596 seo_daily, 1223 keywords, 51 pages, 5 insights
- [x] Write `.claude/DATABASE.md`

---

## PHASE 4 — API & Connector Layer ✅
- [x] Audit 19 connectors — WORKING: gsc, ga4, gsc_keywords, gsc_pages, url_inspection, pagespeed · NO_CREDS_NEEDED: sitemap · BALANCE_NEGATIVE: 6× DataForSEO · CREDENTIALS_MISSING: google_ads, meta, linkedin, webflow, wordpress
- [x] Port all connectors to `pipeline/connectors/` — updated imports, removed `data_source`, SQLAlchemy 2.x compat, Django SyncLog bridge
- [x] Every connector: `BaseConnector`, retry, logging, writes Django `SyncLog` row via `_update_django_sync_log`
- [x] `pipeline/services/sync_engine.py` — `sync_all()` + `sync_page(page)` with `RefreshRun` progress writes + post-sync aggregate rebuild
- [x] `PAGE_CONNECTORS` map wired — WORKING connectors only; blocked ones documented
- [x] Views: `POST /sync/all/`, `POST /sync/page/<page>/`, `GET /sync/status/` (HTMX poll) — `apps/sync/views.py` + `urls.py` wired into `config/urls.py`
- [x] Write `.claude/API_REFERENCE.md` — all 19 connectors documented (credentials, tables, rate limits, dependency order)

---

## PHASE 5 — Core Dashboard Pages ✅ *(7 pages, 6 live + 1 blocked)*
For each: view → url → template → per-page refresh button → real-data test → role guard.

**Scope: 7 core pages only (no full MVP copy). Build solution, not just migration.**

- [x] 01 Overview ✅ — KPI cards + deltas, 30-day trend, AI summary, top pages, ads summary, top keywords, competitor positioning. Multi-site selector (session-persisted).
- [x] 02 SEO ✅ — Metrics by country/device, recent anomalies, technical issues. Aggregates from seo_daily + anomalies table.
- [x] 03 Keywords ✅ — All tracked keywords with search volume, KD, CPC, position, intent. Full keyword_rankings enrichment.
- [x] 04 Positioning ✅ — Top keywords vs competitors (Semrush-style). Competitor domain list, shared keywords, avg position.
- [ ] 05 Ads — Google Ads + Meta metrics (ad_metrics_daily) — BLOCKED (no credentials; Ads page shows badge)
- [x] 06 Alerts ✅ — Anomalies, PageSpeed scores (performance/SEO/accessibility), indexing status, technical issues. All-in-one audit.
- [x] 07 Settings ✅ — Site selector (switch between tracked websites), connector status (working/errored/never-run), refresh buttons, preferences.

---

## PHASE 5.5 — The Decision Engine (Rescue Sprint) ✅
- [x] Sprint 1: Global Temporal Context (period selector + views integration)
- [x] Sprint 2: The Actionable Keywords Page (Quick Wins, Striking Distance, Health Score)
- [x] Sprint 3: The Decision Signals Engine (port from MVP to Overview page)
- [x] Sprint 4: Page Health Intelligence (port Pages dashboard)

---

## PHASE 5.6 — DataForSEO Competitor Intelligence + AI Keywords ✅ (2026-06-15, client request)

Spec: `docs/superpowers/specs/2026-06-15-dataforseo-competitor-intelligence-design.md`.
**Additive only** — no existing connector/query/page behavior changed; all reads stay DB-first
(new connectors run on per-page Refresh only).

- [x] Schema: `competitor_keyword_rankings`, `tracked_competitors`, `ai_keyword_data` (schema.py).
      Self-provisioned via `writer.ensure_tables()` (idempotent `create_all`, never alters data).
- [x] Writers: `upsert_competitor_keyword_rankings`, `upsert_ai_keyword_data`.
- [x] Connector `dataforseo_serp_competitors.py` — full-SERP capture of every tracked competitor's
      position per keyword (sibling of `dataforseo_serp.py`, which is untouched).
- [x] Connector `dataforseo_ai_keywords.py` — DataForSEO AI Optimization (AI search volume + MoM trend).
- [x] `competitor_service.py` — tracked competitor columns: auto-seed from `competitor_domains`
      (top by intersections) or an editable override; discovery connector untouched.
- [x] Sync: registered `dataforseo_serp_competitors` (positioning) + `dataforseo_ai_keywords`
      (keywords) in `PAGE_CONNECTORS`. `ALL_CONNECTORS` left as-is (global Refresh-All cost profile
      unchanged).
- [x] Positioning page: new **Competitor Rankings** grid (your rank vs each competitor, per keyword,
      date-over-date diff) *above* the untouched domain-level Competitor Map.
- [x] Keywords page: new **AI Search Demand** section.
- [x] Settings page: **Tracked Competitors** editor (textarea + discovered-domain chips) →
      `/set-competitors/`.
- [x] Verified: `manage.py check` clean; Positioning/Keywords/Settings render 200 with new sections;
      competitor save round-trips; empty states show before first refresh (no crashes).
- [ ] *Deferred (send to client):* Domain Analytics, Content Analysis, AI-Overview/LLM-mention
      visibility flavors. Pre-existing bug noted (not fixed, out of scope):
      `_get_visibility_trend` uses `SEODaily.position` (should be `avg_position`).

---

## PHASE 6 — Production Hardening ⏸️ (Paused for Phase 5.5)
- [ ] `DEBUG=False`, `ALLOWED_HOSTS` locked, CSRF on all POST, SSL redirect
- [ ] View-level caching; query optimization; WhiteNoise for static
- [ ] Plotly served as JSON → rendered client-side
- [ ] Custom 403 / 404 / 500 pages; graceful "no data" states; no white crash screens
- [ ] check what we show in mvp and and what is in production missing, features, section, components
- [ ] Audit as a experience business owner who know the google analytics, google search console, keyword researching, and SEO is this dashboard data help you to take decesion or it is just a dashboard that fetch data and show is this healpful or not. You are an business owner why you invest in dis dashboard. 

---

## PHASE A — SPA + API Foundation ✅ (2026-07-10)
Migrates the dashboard's front end from Django server-rendered pages to the approved
Limitless Marketing SPA design, backed by a real DRF API. The old Streamlit-derived Django
dashboard pages (Phase 5) still serve unchanged at `/` — this phase adds a parallel `/app/`
route; nothing at `/` was touched or removed.

- [x] DRF installed and wired (`apps/api/`), `rest_framework.authtoken` enabled
- [x] Bearer token auth: every Django user gets an auth token automatically via a
      `post_save` signal (Task 2)
- [x] `Site` model extended with `vertical` / `location` / `slug` fields (project identity)
- [x] `GET/POST /api/projects` — list/create projects, real DB-backed
- [x] `GET /api/projects/<slug>/overview?range=` — real Overview KPIs/pillars/modules,
      stateless per-request (no session `period_mode` coupling, per `HANDOFF_SPEC.md`)
- [x] SPA served at `/app/`, login-protected, with `window.FuseAPI.config` bootstrapped
      server-side per request (real Bearer token, `baseUrl` pointed at the real backend)
- [x] Verified end-to-end in a real browser (Playwright): logged-out redirect to `/login/`,
      real `GET /api/projects` and `GET /api/projects/<slug>/overview` calls firing and
      returning real DB data (compared 1:1 against `/`'s numbers for fusehealth.com — both
      show zero traffic because this account has never been synced, confirming the SPA is
      reading the same real data source, not fixture placeholders)

**Non-obvious fixes required (all in `apps/dashboard/spa_views.py`, documented inline):**
the exported design file's own JS contains an Excel-export helper whose string content
literally includes the text `<head>...</head>` and `...</table></body></html>`, so a naive
`str.replace("</body>", ...)` corrupts the SPA's own logic script; the fix targets the
structural tag by position (`index()`/`rindex()`), never a blanket replace. Separately,
`app/api.js`'s script tag executes twice in a real browser (once at parse time, once via the
SPA's own `<helmet>` relocation), each time creating a fresh `window.FuseAPI` with default
config — a one-shot post-load assignment gets silently wiped out, so the bootstrap installs
an `Object.defineProperty` interceptor instead. And `config.baseUrl` must be `'/'`, not `''`
— `api.js`'s `get()/post()/put()` gate real-backend mode on a truthy check, so an empty
string (the literal reading of "paths already hardcode `/api/...`") silently keeps the SPA in
fixture/demo mode forever; `'/'` is truthy and still strips to an empty effective prefix.

**Known gap, out of this phase's scope:** the SPA's Overview tab also always fetches
`/api/projects/<slug>/alerts` in the background (for a notification badge); that endpoint
doesn't exist yet (404), which surfaces an error banner over the Overview content area even
though the KPI data itself loads correctly. Not a Task 8 defect — `/alerts` (and every other
non-Overview endpoint: Keywords, Backlinks, Site Audit, AI, Ads, Settings, …) is explicitly
Phase B–D scope per the design doc's §2.8 boundary.

---

## PHASE B1 — SEO ✅ (2026-07-10)
Wires the SPA's SEO tab to a real DRF endpoint, following the exact pattern established by
Phase A's Overview endpoint.

- [x] SEO page query logic extracted into `apps/dashboard/services/seo_service.py`, shared
      by the old `/seo/` Django view and the new API view (no duplicated queries)
- [x] `build_seo_response(site_id, curr_start, curr_end)` — API-shaped builder matching
      `HANDOFF_SPEC.md`'s `seo` view shape, with corrected `kpis.critical` (404-count) /
      `kpis.total_issues` (fresh sum of issues + anomalies + low-CTR pages) semantics
- [x] `GET /api/projects/<slug>/seo` — real DB-backed, same "anchor to latest data date"
      pattern as Overview but with a fixed 30-day window (no `range` param — the SEO page
      has no period selector in the new design)
- [x] Verified against a real seeded DB: API response's `lowCtrPages`/`countries`/
      `anomalies`/`quickWinKws` matched the old `/seo/` page's numbers for the same site
      and period

---

## PHASE B2 — Keywords ✅ (2026-07-11)
Wires the SPA's Keywords tab to a real DRF endpoint, following the exact pattern established by
Phase B1's SEO endpoint — now built on the `resolve_project_or_404`/`latest_data_anchor` helpers
shared across every project-scoped `apps.api` view instead of duplicating that lookup a third time.

- [x] Shared `resolve_project_or_404`/`latest_data_anchor` helpers extracted in `apps/api/views.py`
      (used by Overview, SEO, and now Keywords — confirmed the pre-extraction blocks were
      byte-identical duplicates)
- [x] Keyword intelligence query logic extracted into `apps/dashboard/services/keywords_service.py`,
      shared by the old `/keywords/` Django view and the new API view (no duplicated queries); real
      fix along the way — `all_keywords` (and therefore the API's `keywords[]`) is now built from
      the `merged` frame (carries `prev_position`/`pos_change` for every tracked keyword), not the
      current-period-only `df`, so `prevPos` is a proper `None`/number for every row instead of
      silently missing for anything outside the top-15-per-segment lists
- [x] `build_keywords_response(site_id, curr_start, curr_end, prev_start, prev_end)` — API-shaped
      builder matching `HANDOFF_SPEC.md`'s `keywords` view shape, with honest-empty `monthly`/
      `serpFeatures` fields (not tracked yet, not fabricated)
- [x] `GET /api/projects/<slug>/keywords` — real DB-backed, same "anchor to latest data date,
      fixed 30-day window" pattern as SEO
- [x] Verified against the real dev DB (`fusehealth-com`, 1,492 `KeywordRanking` rows): the API's
      `kpis.total/avg_pos/total_volume/total_clicks` (172 / 38.2 / 2260 / 303) matched the old
      `/keywords/` page's KPI cards exactly, for the same site and period

---

## PHASE B3 — Position Tracking ✅ (2026-07-11)
Wires the SPA's Position Tracking tab to a real DRF endpoint, following the same
`resolve_project_or_404`/`latest_data_anchor` pattern as B1/B2 — but this endpoint accepts a
`range` query param (reusing `OverviewQuerySerializer` as-is), unlike SEO/Keywords which
hardcode a fixed 30-day window.

- [x] `build_positions_response(site_id, curr_start, curr_end, prev_start, prev_end)` — API-shaped
      builder matching `HANDOFF_SPEC.md`'s `positions` view shape, reshaping the existing
      `_get_ranking_distribution`/`_get_position_changes`/`_get_competitor_grid` query functions
      (reused as-is, not moved or modified) plus `get_keyword_intelligence_raw`'s `full_keywords`
      for `movers[]` (top 8 by `|pos_change|`, requires `>= 2`); competitor grid `None` values
      (unranked keyword / no competitor data) preserved as `None`, not coerced to 0
- [x] `GET /api/projects/<slug>/positions?range=7d|30d|90d` — real DB-backed, accepts `range`
      with a `30d` default (same semantics as Overview's period selector)
- [x] Verified with a real seeded temp DB via Django's test client (`APITestCase`): all required
      top-level keys (`kpis`/`distribution`/`movement`/`competitors`/`movers`) present, `range`
      default works, unknown slug is 404, unauthenticated is 401

---

## PHASE B4 — Alerts ✅ (closes Phase B) (2026-07-12)
Wires the SPA's Alerts tab to a real DRF endpoint (Tasks 1–4), then closes a gap Phase A
deliberately left open by wiring Overview's `priority[]` field to that same real data (Task 5).

- [x] Alerts page query logic extracted into `apps/dashboard/services/alerts_service.py` — new,
      unlimited-count `query_alert_anomalies_raw`/`query_alert_technical_issues_raw` functions,
      kept separate from `apps.dashboard.views`' capped `_get_all_anomalies`/
      `_get_technical_issues` (old page's display tables are unmodified)
- [x] `build_alerts_response(site_id)` — API-shaped builder matching `HANDOFF_SPEC.md`'s `alerts`
      view shape: `{feed: [{id, ts, kind, severity, title, detail, acknowledged}]}`, merging
      anomalies (`kind: "anomaly"`) and technical issues (`kind: "technical"`, always
      `acknowledged: false` — honest reflection of no ack mechanism existing yet for that table),
      sorted by date desc then severity
- [x] `GET /api/projects/<slug>/alerts` — real DB-backed, same `resolve_project_or_404` pattern as
      every other project-scoped view
- [x] `build_priority_feed(feed, limit=6)` in `overview_service.py` — filters the Alerts feed to
      unacknowledged items, sorts by severity, caps at 6, tags each with its owning module via a
      `kind → {label, target}` map (`anomaly→SEO`, `technical→Page Health`; `ranking`/`backlink`/
      `ads`/`ai`/`system` mapped for forward-compatibility but unreachable today — those alert
      kinds don't exist yet)
- [x] `ProjectOverviewView`'s hardcoded `"priority": []` (Phase A placeholder, "no fake data, empty
      until built") replaced with `build_priority_feed(build_alerts_response(site_id)["feed"])`;
      every other Overview response field (`kpis`/`pillars`/`modules`/`signals`/`trend`/`summary`/
      `topPages`) is untouched — confirmed by diff (only the import line and the `priority` value
      changed) and by the full existing Overview test suite passing unmodified
- [x] Verified against the real dev DB: `GET /api/projects/fusehealth/overview` returns 6 real
      priority items (4 seeded `anomaly` rows + 2 `technical` `TechnicalIssue` rows), each tagged
      with the correct module (`seo` / `pages`)

**Phase B is now complete.** All 4 sub-projects (SEO, Keywords, Position Tracking, Alerts) are
built and DB-verified. Phase C (Backlinks, Site Audit, Off-site SEO, Ads) begins fresh feature
work rather than more page-porting.

---

## PHASE C1 — Backlinks ✅ (2026-07-12)
Wires the SPA's Backlinks tab to a real DRF endpoint, following the exact pattern established
by Phase B. This is the final task of Phase C1: implementation of the real data flow without
attempting the 5 missing DataForSEO sub-endpoint connectors (those remain scope for a future
phase once credentials exist).

- [x] Backlinks page query logic extracted into `apps/dashboard/services/backlinks_service.py`
      (Task 2) — raw DB calculators (`query_backlinks_summary_raw`, `query_backlinks_table_raw`)
      plus API-shaped builder (`build_backlinks_response`). Honest empty states for fields
      requiring DataForSEO connectors not yet available (`summary`, `months`, `types`, `asBuckets`,
      `refDomains`, `anchors`, `gapDomains` all return empty or `state:"setup"`).
- [x] `GET /api/projects/<slug>/backlinks` — real DB-backed (Task 3), same `resolve_project_or_404`
      pattern as every other project-scoped view
- [x] Test suite: 3 new tests in `apps/api/tests/test_backlinks.py` (real data + setup states,
      404 on unknown slug, 401 unauthenticated)
- [x] All 137 tests pass (134 baseline + 3 new)

**Scope discipline:** Phase C1 deliberately does NOT implement the 5 missing DataForSEO
sub-endpoint connectors (`referring-domains-by-country`, `anchor-keywords`, `referring-domains-by-type`,
`referring-domains-by-authority-score`, `text-analytics`) — that is real, unvalidated integration
work for a future phase once credentials exist and discovery is complete, not something to guess
at now. The endpoint returns real data (`kpis`/`links`/`competitors`) with honest
`state:"setup"` placeholders for the rest — never fabricated numbers.

**Final-review fix (2026-07-12):** the whole-branch review caught that the approved SPA's
Backlinks tab reads its headline stats from `data.summary.*`/`data.refDomains[]`, not from
`data.kpis`/`data.links` — and had no `state:"setup"` guard for this tab (only the Overview
pillars had one). Feeding it the honest `summary:{state:"setup"}` payload rendered a broken UI
(`NaN` authority gauge, `undefined` deltas/percentages, "Showing 0 of — backlinks"). Fixed in
`static/spa/index.html`: the Backlinks tab's computed-values function (`if (tab === 'backlinks')`)
now short-circuits on `data.summary.state === 'setup'` before touching any of the
`Math.max`/`.toFixed` chart math, and the template wraps the whole rich sub-tab UI in
`<sc-if value="{{ !bl.setup }}">`/`<sc-if value="{{ bl.setup }}">` guards — the setup branch
shows one clean "Backlinks data isn't connected yet" card instead. **This is now the reference
pattern for C2 (Site Audit)/C3 (Off-site SEO)/C4 (Ads): before wiring any deep-dive tab to a
`state:"setup"` backend contract, check what fields the SPA's own render function for that tab
actually reads (not just the mock's declared shape) and add the same short-circuit + guard if
none exists.** Verified via direct API call (`summary.state === "setup"` confirmed) and a
tag-balance check across the whole SPA template (163 `sc-if` open/close pairs, 144 `sc-for`
pairs — unchanged from before the edit, confirming no template corruption). No Python changed;
full suite unaffected.

---

## PHASE 7 — Deployment (VPS)
- [ ] Ubuntu 22.04, Python 3.11+, venv, requirements, `.env` on server
- [ ] `collectstatic` · `migrate` · `seed_users`
- [ ] `gunicorn.service` + `gunicorn.socket`, enabled
- [ ] Nginx reverse proxy + Let's Encrypt SSL; HTTP→HTTPS redirect
- [ ] Final QA: each role logs in, Refresh All shows live progress, all 10 pages load real data,
      auto-restart verified
