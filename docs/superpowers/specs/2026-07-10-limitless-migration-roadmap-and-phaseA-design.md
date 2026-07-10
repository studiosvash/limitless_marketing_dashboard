# Limitless Marketing Dashboard — Migration Roadmap + Phase A Design

> Status: approved 2026-07-10. Roadmap section is the standing decomposition for the whole
> redesign migration. Phase A is the fully-specced sub-project ready for implementation
> planning; Phases B–F are scoped at roadmap level only and each gets its own design doc
> when we reach it.

## 0. Context — what changed

The project owner rated the Streamlit→Django MVP 7/10 and commissioned a designer to
finalize a production frontend. That finalized design was handed off in
`fusehealth/Limitless marketing dashboard2/`:

- **`Limitless Marketing Dashboard v2.dc.html`** (+ `app/api.js`, `app/fixtures.js`) — the
  real, approved frontend. A self-contained single-page app that currently runs on fixture
  data and is built to talk to a JSON API via `window.FuseAPI`.
- **`HANDOFF_SPEC.md`** — the designer's own backend contract: every endpoint, JSON shape,
  and DataForSEO/GA4/Ads data-source mapping the frontend needs. Treated as authoritative
  for route names and object shapes throughout this migration.
- **`templates/` folder inside the design export is NOT the new design** — it's a stale
  copy of our *current* Django templates that the design tool pulled in as context. Ignore
  it; do not confuse it with the SPA.

Three decisions were made before this roadmap was written (all recorded here so later
phases don't re-litigate them):

1. **Architecture: full adoption of the SPA + JSON API**, not a template reskin and not a
   permanent hybrid. We build a DRF API matching `HANDOFF_SPEC.md` and serve the approved
   `.dc.html` file as the real frontend. HTMX/server-rendered dashboard pages are retired
   once every page is ported (end of Phase F).
2. **Credentials for new integrations (DataForSEO balance, Google Ads, Meta, LinkedIn)
   remain unresolved.** Backend logic, schema, and endpoints for the features that depend on
   them are built now; those specific responses return `state:"setup"`/empty until
   credentials land — never fake data, same rule as today's MVP.
3. **Scope is now multi-client.** "Limitless Marketing" is the agency brand; `projects` are
   client websites (FuseHealth being one of several going forward). Real project CRUD
   replaces today's fixed single-site selector.

## 1. Roadmap — phase decomposition

Each phase is an independent sub-project with its own spec → plan → build cycle. Order
matters: later phases depend on Phase A's plumbing.

| Phase | Scope | Depends on |
|---|---|---|
| **A — Foundation** | DRF API app, token auth, project model/CRUD, SPA serving, Overview page fully wired end-to-end | — |
| **B — Port what works** | SEO, Keywords, Position Tracking, Alerts — re-expose data we already fetch (GSC/GA4/existing DataForSEO) via the new API shapes, render in the SPA | A |
| **C — Shells for blocked features** | Backlink Analytics, Site Audit (OnPage crawler), Off-site SEO (GA4 referral/social), Ads (Google Ads/Meta + campaign mutations) — real schema/endpoints/connectors, `state:"setup"` until credentials resolve | A |
| **D — Net-new intelligence** | AI Optimization (LLM mention tracking, Prompt Explorer), Keyword Explorer | A, and reuses the existing Keyword Explorer design (`2026-06-17-keyword-explorer-design.md`) where applicable |
| **E — Settings expansion** | Grow from today's handful of fields to the 15 groups in `HANDOFF_SPEC.md §2.8` (workspace, team, security, budget/quotas, notifications, etc.) | A |
| **F — Production hardening & deploy** | CORS, token issuance hardening, DEBUG/SSL, flip `/` to the SPA, retire old Django templates, VPS deploy | A–E complete |

Phases C and D are gated on external factors (credentials, and in D's case genuinely new
DataForSEO product surfaces) — their internal ordering can shift without affecting B or E.

## 2. Phase A — Foundation (specced for implementation)

### 2.1 Goal

Prove the entire new chain — DRF API, token auth, the real SPA file, real DB data — works
end-to-end on one page (Overview) before any other page is touched. Every later phase reuses
this plumbing; none of it is page-specific.

### 2.2 New Django app: `apps/api/`

- DRF-based (`djangorestframework` added to `requirements.txt` and `INSTALLED_APPS`).
- Mounted at `/api/` in `config/urls.py`, alongside (not replacing) existing
  `apps.accounts`/`apps.dashboard`/`apps.sync` URL includes.
- Route/shape contract: `HANDOFF_SPEC.md §1`/`§2` verbatim — same path names
  (`/api/projects`, `/api/projects/:id/overview`, …), same JSON keys, same enums.
- **No duplicated query logic.** The SQL/aggregation currently inline in
  `apps/dashboard/views.py` (e.g. `_get_kpi_stats`, the Decision Signals engine) is extracted
  into plain functions in `apps/dashboard/services/` (or a new `pipeline/services/` module
  if more broadly reusable) that return dicts. Both the old view and the new DRF viewset call
  the same function during the transition window (Phases A–E) — this is the one deliberate
  duplication point (two callers, one source of truth), removed when old views are deleted in
  Phase F.

### 2.3 Auth — DRF TokenAuthentication

- Per `HANDOFF_SPEC.md §0.1`'s own recommendation: one header, no CSRF dance, appropriate
  for 2-3 internal users.
- `rest_framework.authtoken` added; existing Django session login page
  (`registration/login.html`, already role-aware) stays as the login UI. On successful
  login it also returns/refreshes the user's DRF token (via `Token.objects.get_or_create`),
  which the SPA stores and sends as `Authorization: Bearer <token>` per
  `FuseAPI.config.authToken`.
- `LoginRequiredMiddleware` (session) continues protecting the old dashboard URLs unchanged.
  API views use DRF's own `IsAuthenticated` + `TokenAuthentication` — independent of the
  session middleware, so both auth paths coexist without interfering.

### 2.4 Project model — reuse `sites`, don't duplicate it

The `sites` table (`fusehealth.db`, SQLAlchemy, `pipeline/db/schema.py`) already holds
`site_url`, `site_name`, `gsc_property`, `ga4_property_id`, `dataforseo_target_domain`,
`is_active` — this **is** the project registry, just under the old single-site naming.

- Add columns via the pipeline's schema (self-provisioned, same pattern as other additive
  changes): `vertical` (String, nullable), `location` (String, nullable, default
  `"United States"`) — needed to match `settings.project{domain, name, vertical, location}`.
- `competitor_domains` (already exists, 26 rows migrated) backs `project.competitors[]`.
- `GET /api/projects` → list `sites` where `is_active=1`, shaped to
  `[{id, domain, name, vertical, location}]` (`domain` = `site_url` stripped of the
  `sc-domain:` prefix for display; keep the raw value for `gsc_property` internally).
- `POST /api/projects` → creates a new `sites` row. Confirms the multi-client decision from
  §0.3 — this is real create, not a stub.

### 2.5 Serving the SPA

- New static-ish view (Django `TemplateView` or a simple file-serve view) mounts the design
  export at `/app/`: `Limitless Marketing Dashboard v2.dc.html`, `app/api.js`,
  `app/fixtures.js`, `support.js`, `static/css/global.css`, `assets/` copied into
  `fusehealth/static/spa/` (or served from the design folder directly in dev — finalize in
  the implementation plan).
- `app/fixtures.js` is dropped from the served build once `FuseAPI.config.baseUrl` is set to
  `/api` — fixtures never ship to the real app, only used if we need local frontend-only
  debugging.
- The existing Django dashboard keeps serving unchanged at its current URLs throughout
  Phases A–E. Nothing breaks; old and new are viewable side by side for comparison at any
  time. Root URL (`/`) flips from the old dashboard to the SPA only in Phase F, after every
  page is ported.

### 2.6 Overview endpoint — the Phase A deliverable

`GET /api/projects/:id/overview?range=7d|30d|90d` returns (per `HANDOFF_SPEC.md §1`/`§2.2`):

- `kpis[4]`, `trend[]`, `topPages[≤6]`, `signals[≤3]` — **real data**, sourced from the
  extracted `_get_kpi_stats`-equivalent service functions and the existing Decision Signals
  engine (already built, Phase 5.5).
- `pillars[5]`, `modules[7]`, `priority[≤6]`, `summary{wins,critical,watch}` — populate what
  we can from existing data (e.g. "Site health" pillar can use existing technical-issues
  count; "SEO"/"Keywords"/"Positioning" modules use existing aggregates); any pillar/module
  whose source feature isn't built yet (AI visibility, Site Audit score, Ads, Backlinks)
  reports `state:"setup"`/`tone:"setup"` with no invented numbers, per the credentials
  decision in §0.3. `summary` reuses the existing AI weekly summary (already live).

### 2.7 Verification for Phase A

- `manage.py check` clean with the new `api` app installed.
- DRF browsable API: `GET /api/projects` returns real project rows; `POST /api/projects`
  creates one.
- Token login flow: log in via the existing page, confirm a token is issued/retrievable.
- `GET /api/projects/:id/overview` returns real fusehealth.com data matching (or explaining
  any deliberate divergence from) what the old Overview page shows today.
- The SPA at `/app/` loads, `FuseAPI.config.baseUrl` set to `/` (**not** `/api` — corrected
  post-implementation: `app/api.js`'s `get()`/`post()`/`put()` gate real-backend mode on a plain
  JS truthy check, and `/api` would double the prefix since every call site already passes an
  `/api/...`-prefixed path; see `apps/dashboard/spa_views.py`'s module docstring, footgun #3, for
  the full explanation), Overview tab renders real KPIs/trend/topPages/signals from the live API
  (not fixtures.js).
- Old dashboard at its existing URLs still works, untouched.

### 2.8 Explicitly out of scope for Phase A

Every page other than Overview; all 15 Settings groups; Ads mutations; Backlinks/Site
Audit/AI Optimization/Off-site data; Keyword/Prompt Explorer. These are Phases B–E.

## 3. Open items carried forward (not blocking Phase A)

- Exact static-file serving strategy for the SPA in production (WhiteNoise vs. separate
  static bundle) — decide in the Phase A implementation plan, doesn't change the design.
- Whether `range` query param semantics (7d/30d/90d) map cleanly onto the existing
  `period_mode`/`period_offset` session-based period system, or need a small adapter —
  resolve during implementation; both represent the same underlying concept (a date window).

## 4. Design fidelity — guaranteed by construction

The product must end up looking **exactly** like the approved design. This is not a
translation risk: from Phase A onward we serve the actual approved file
(`Limitless Marketing Dashboard v2.dc.html` + `app/`) as the real frontend — every screen is
pixel-identical because it *is* that file, not a hand-rebuilt copy of it. All engineering
effort in every phase is on the backend (the API feeding it real data); there is no step in
this roadmap where UI is redrawn from a screenshot. Visual parity is therefore a property of
the plan, not a QA task to verify per page.

## 5. Feature completeness commitment — every feature in the new design gets built

No feature present in the new design is dropped or descoped. Full gap analysis, MVP vs. new
design, mapped to the phase that builds it:

| Feature | In old MVP today | In new design | Plan |
|---|---|---|---|
| Overview | Yes | Yes — expanded (pillars/modules/priority feed) | **Phase A** |
| Multi-project switcher | No (single site only) | Yes | **Phase A** |
| SEO Performance | Yes | Yes | Phase B — port |
| Keywords tracking | Yes | Yes | Phase B — port |
| Position Tracking | Yes (as "Positioning") | Yes | Phase B — port |
| Alerts | Yes | Yes — expanded (`ai`, `ads` kinds added) | Phase B — port + expand |
| Off-site SEO (GA4 referral/social) | No | Yes | Phase C — buildable with live data now (GA4 already connected) |
| Backlink Analytics (full suite) | No (empty state only) | Yes | Phase C — built now, live data waits on DataForSEO balance |
| Site Audit (crawler, score, CWV) | No | Yes | Phase C — built now, live data waits on DataForSEO balance |
| Ads (incl. pause/budget/negatives write-back) | No (blocked, report-only) | Yes — full mutation support | Phase C — built now, live data waits on Google Ads/Meta credentials |
| AI Optimization (LLM mentions, 4 models, Answer Inspector) | No | Yes | Phase D — live data waits on DataForSEO AI Optimization API |
| Keyword Explorer | No | Yes | Phase D |
| Prompt Explorer | No | Yes | Phase D |
| Settings (15 groups: team, billing, security, notifications, budget/quotas, sync config, alert rules, crawl config, data prefs) | Partial (site selector, connector status, refresh, basic prefs only) | Yes | Phase E — expand |

For every credential-blocked row, "built now" means the complete code path — schema,
connectors, API endpoints, and SPA wiring — ships in its assigned phase, not a stub deferred
indefinitely. The page reports an honest `state:"setup"`/empty response (per the no-fake-data
rule, §0.3) until the credential is resolved; no further development work is needed at that
point — the feature is already finished and goes live the moment the credential lands.
