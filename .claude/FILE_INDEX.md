# FuseHealth — File Index

*The ground-truth map of the project. Read this to answer "where does X live?" instead of
guessing. **Update this file whenever you add, move, or remove a file** — a stale index is
worse than none. Status: (exists) = on disk now · (planned: Phase N) = not yet created.*

## Project root — `fusehealth/`

| Path | Purpose | Status |
|---|---|---|
| `manage.py` | Django CLI entrypoint; defaults to `config.settings.local` | exists |
| `django_internal.db` | Default DB (Django ORM): auth, sessions, admin, UserProfile, sync_log | exists |
| `CLAUDE.md` | Project brain / router (auto-loaded) | exists |
| `README.md` | Setup & run guide (venv, install, migrate, seed_users, runserver, refresh, troubleshooting) | exists |
| `FEATURES.md` | Page-by-page, plain-English feature overview — client-facing & shareable (🟢/🟡/🔌 status) | exists |
| `.env` | Secrets & config for dev (git-ignored) | exists |
| `.env.example` | Documented template of every env var + availability status | exists |
| `.gitignore` | Ignores .env, *.db, venvs, build/IDE artifacts | exists |
| `requirements.txt` | Python dependencies for the Django app | exists |
| `scripts/audit_env.py` | Live credential audit; reports API availability (no secrets printed) | exists |

## Config package — `config/`

| Path | Purpose | Status |
|---|---|---|
| `config/urls.py` | Root URL conf (currently admin only) | exists |
| `config/wsgi.py` · `config/asgi.py` | Server entrypoints; default to `config.settings.production` | exists |
| `config/settings/base.py` | Shared settings: apps, dual-DB, templates, static, auth redirects, `ANALYTICS_DB_PATH` | exists |
| `config/settings/local.py` | Dev overrides: DEBUG=True, localhost, dev key | exists |
| `config/settings/production.py` | VPS overrides: DEBUG=False, HTTPS hardening, secrets from env | exists |

## Apps — `apps/`

| Path | Purpose | Status |
|---|---|---|
| `apps/accounts/models.py` | `Role`, `UserProfile` (role + `can_access`), `ROLE_PAGE_ACCESS`, auto-profile signal | exists |
| `apps/accounts/decorators.py` | `role_required(page_key)` view guard | exists |
| `apps/accounts/views.py` | Branded `LoginView` (login_not_required) | exists |
| `apps/accounts/urls.py` | `login` / `logout` routes | exists |
| `apps/accounts/admin.py` | User admin with role inline | exists |
| `apps/accounts/management/commands/seed_users.py` | Creates founder/seo/ads users from env passwords | exists |
| `templates/registration/login.html` | Branded login page (light + indigo) | exists |
| `apps/dashboard/models.py` | `Insight` Django model — team-entered context (date, team, title, impact, created_by, is_verified). +Phase D: `AITarget` (site_url unique, brand/aliases/competitors, setup_done), `AIPromptList` (site_url, name), `AIPrompt` (site_url, list FK nullable, text, tracked_models) — first-party AI Optimization app state (brand/competitor tracking, prompt lists), same `site_url`-string-keyed pattern as `Insight`. Uses a module-level `_empty_list()` helper (not bare `default=list`) because `AIPrompt.list` as a field name shadows the builtin `list` within the class body. +Phase E: `ProjectSettings` (site_url unique, `data` JSONField default `{}` via `_empty_dict()`, `updated_at`) — blob store for every Settings group with no dedicated relational need (workspace/notifications/aiConfig/dataPrefs/syncConfig/platformConnectors/budget.cap+.enforce/alertRules/crawl); genuine persistence, not a crash-avoidance sentinel | exists |
| `apps/dashboard/admin.py` | `InsightAdmin` | exists |
| `apps/dashboard/migrations/` | 0001 initial + 0002 Meta ordering | exists |
| `apps/dashboard/` | views/templates per page; reads DB only | scaffolded (pages: Phase 5) |
| `apps/dashboard/services/overview_service.py` | Phase A: Overview page query logic extracted to one place — raw DB calculators (`get_kpi_raw`, `query_top_pages_raw`, `query_daily_traffic_raw`, `get_ai_summary_text`) plus both an old-template formatter (`format_kpi_cards`, `build_traffic_chart`) and a new API-shaped formatter (`build_kpis_api`, `build_top_pages_api`, `build_pillars`, `build_modules`, `build_summary_lists`). Phase B4: `build_priority_feed(feed, limit=6)` — filters `alerts_service.build_alerts_response(...)['feed']` to unacknowledged items, severity-sorts, caps at `limit`, tags each with its owning module (kind→module map); wired into `ProjectOverviewView`'s `priority[]` field. Shared by the old Django Overview view and `apps.api.views.ProjectOverviewView` | exists |
| `apps/dashboard/services/tests/test_overview_service.py` | Tests for the above (raw calculators, DB-error fallbacks, API-shape builders, `build_priority_feed`) | exists |
| `apps/dashboard/services/seo_service.py` | Phase B1: SEO page query logic extracted to one place — raw DB calculators (`query_low_ctr_pages_raw`, `query_seo_by_dimension_raw`, `query_seo_anomalies_raw`, `count_technical_issues`, `count_quick_win_keywords`) plus both an old-template formatter (`format_recent_anomalies`) and a new API-shaped builder (`build_seo_response`, with corrected `kpis.critical`/`kpis.total_issues` semantics). Shared by the old Django `seo()` view and `apps.api.views.ProjectSEOView` | exists |
| `apps/dashboard/services/tests/test_seo_service.py` | Tests for the above (raw calculators, `build_seo_response` shape/semantics) | exists |
| `apps/dashboard/services/keywords_service.py` | Phase B2: Keywords page query logic extracted to one place — `get_keyword_intelligence_raw` (health score, intent/KD distribution, quick-wins/striking/declining/low-CTR segments; fixed so `all_keywords` carries `prevPos` for every tracked keyword, not just the top-15-per-segment ones) plus a new API-shaped builder (`build_keywords_response`). Shared by the old Django `keywords()` view and `apps.api.views.ProjectKeywordsView` | exists |
| `apps/dashboard/services/tests/test_keywords_service.py` | Tests for the above (raw calculator, `build_keywords_response` shape/`prevPos` fix) | exists |
| `apps/dashboard/services/positioning_service.py` | Phase B3: Position Tracking page API-shaped builder — `build_positions_response` reshapes the existing `_get_ranking_distribution`/`_get_position_changes`/`_get_competitor_grid` (from `apps.dashboard.views`, reused as-is) plus `get_keyword_intelligence_raw`'s `full_keywords` (for `movers[]`, filtered to `|pos_change| >= 2`) into the `HANDOFF_SPEC.md` `positions` view shape. Consumed by `apps.api.views.ProjectPositionsView` | exists |
| `apps/dashboard/services/tests/test_positioning_service.py` | Tests for the above (`build_positions_response` shape/semantics) | exists |
| `apps/dashboard/services/alerts_service.py` | Phase B4: Alerts page query logic — new, unlimited-count raw calculators (`query_alert_anomalies_raw`, `query_alert_technical_issues_raw`, separate from `apps.dashboard.views`' capped `_get_all_anomalies`/`_get_technical_issues`) plus `build_alerts_response(site_id)`, the `HANDOFF_SPEC.md` `alerts` view shape: `{feed: [{id, ts, kind, severity, title, detail, acknowledged}]}`. Consumed by `apps.api.views.ProjectAlertsView` and, via `overview_service.build_priority_feed`, by `ProjectOverviewView`'s `priority[]` field | exists |
| `apps/api/tests/test_alerts.py` | Tests for `GET /api/projects/<slug>/alerts` (real feed data, auth) | exists |
| `apps/dashboard/services/backlinks_service.py` | Phase C1: Backlinks page query logic extracted to one place — raw DB calculators (`query_backlinks_summary_raw`, `query_backlinks_table_raw`) plus API-shaped builder (`build_backlinks_response`). Returns real `kpis`/`links`/`competitors` with honest `state:"setup"` for fields requiring DataForSEO sub-endpoint connectors not yet available. Consumed by `apps.api.views.ProjectBacklinksView` | exists |
| `apps/api/tests/test_backlinks.py` | Tests for `GET /api/projects/<slug>/backlinks` (real data + setup states, auth) | exists |
| `apps/dashboard/services/site_audit_service.py` | Phase C2: Site Audit page query logic extracted to one place — raw DB calculators (`query_indexing_breakdown_raw`, `query_cwv_raw`) plus API-shaped builder (`build_site_audit_response`). Returns real `breakdown` (IndexingStatus categories) and `cwv` metrics (LCP/CLS from PageSpeed mobile data) with honest `state:"setup"` for fields requiring DataForSEO OnPage connector (rules catalog, crawl metadata, snapshots). Consumed by `apps.api.views.ProjectSiteAuditView` | exists |
| `apps/dashboard/services/offsite_service.py` | Phase C3: Off-site SEO page query logic extracted to one place — raw DB calculators (`query_offsite_totals_raw`, `query_offsite_trend_raw`, `query_offsite_landing_pages_raw`) plus API-shaped builder (`build_offsite_response`), reshaping real GA4-sourced `SEODaily` columns (`sessions`/`users`/`engagement_rate`/`conversions`/`landing_page`) into `totals`/`prev`/`trend`/`landingPages`, with honest `[]` for `channels`/`referrers`/`social` (no `sessionDefaultChannelGroup`/`sessionSource` GA4 dimension fetched yet), real all-`false` `connectors{}`, and `state:"setup"` `syncMeta` (no GA4 pull-metadata table). Consumed by `apps.api.views.ProjectOffsiteView` | exists |
| `apps/dashboard/services/ads_service.py` | Phase C4: Ads page query logic extracted to one place — raw DB calculators (`query_ads_totals_raw` — spend-weighted `roas` averaged only over rows with a known `roas`, plus GA4 `SEODaily.conversions` cross-reference for `ga4_key_events`; `query_ads_trend_raw` — per-day `AdMetricDaily`+`SEODaily` merge; `query_ads_pacing_raw` — real calendar-month-to-date spend, honest-zero budget/projection, not range-scoped) plus API-shaped builder (`build_ads_response`). Unlike C1-C3, `totals`/`prev`/`pacing`/`syncMeta` are REAL fully-keyed objects with honest zero/`None` values, never a `{"state":"setup"}` sentinel (the SPA's Ads block has no setup-guard and would crash on `.toFixed()`/`.map()`); `campaigns`/`searchTerms`/`attribution`/`landingPages`/`negatives` are honest `[]` (no backing schema/connector). `syncMeta.connected` reflects real `GOOGLE_ADS_CUSTOMER_ID`/`GOOGLE_ADS_DEVELOPER_TOKEN` env presence. Consumed by `apps.api.views.ProjectAdsView` | exists |
| `apps/dashboard/services/ai_service.py` | Phase D: AI Optimization page — `query_ai_keywords_raw` (real `AIKeywordData` reshape scoped to the latest snapshot date only; flattens the connector's `[{year,month,ai_search_volume}]` trend shape into a chronologically-sorted, start-zero-padded 12-element list; `ratio` is `None`, not a fabricated `0%`, when there's no Google-volume denominator; `mentions`/`gap` are ALWAYS `0`/`False` — no LLM Mentions data exists to derive them from) plus `build_ai_response` (assembles real `targets`/`lists`/`prompts`/`setupDone` from the Django ORM `AITarget`/`AIPromptList`/`AIPrompt`, plus honest empty/zero for every field requiring LLM Mentions/Responses/scraper infrastructure that doesn't exist: `sov`/`trend`/`topPages`/`topDomains`/`suggestions`/`history`/`budget`/`costs`/`next_run`). Consumed by `apps.api.views.ProjectAIView`/`ProjectAIActionView` | exists |
| `apps/dashboard/services/tests/test_ai_service.py` | Tests for the above (trend reshape/sort/padding, honest `ratio: None`, no-fabrication contract on `mentions`/`gap`, `build_ai_response` shape/site-isolation) | exists |
| `apps/dashboard/tests/test_ai_models.py` | Tests for `AITarget`/`AIPromptList`/`AIPrompt` (uniqueness, nullable list FK, real-empty-list JSONField defaults) | exists |
| `apps/dashboard/tests/test_settings_models.py` | Phase E: tests for `ProjectSettings` (`site_url` uniqueness raises `IntegrityError`, default `data` is a real empty dict — not `None` — on an unspecified create) | exists |
| `apps/dashboard/services/settings_service.py` | Phase E: Settings page — `query_connectors_raw` (real `SyncLog` reshape), `query_team_raw` (real 3 fixed Django users, read-only, honest blank `email`/`None` `last_active`, `initials` derived from username), `DEFAULT_SETTINGS_BLOB` (honest static defaults — NOT the fixture's fabricated workspace/2FA/billing numbers), `build_settings_response` (assembles real `project`/`credentials`/`connectors`/`team` + genuinely-persisted blob, PLUS `sync` and `usage` — two GET-only keys the design spec/plan never documented but which the SPA's Settings render code dereferences unguarded on every load; see module docstring for the two SPA-fidelity corrections found during Task 2: `usage`/`sync`, and `team[].initials`), `apply_settings_update` (routes a PUT body's top-level key(s); `credentials`→`update_site`, `project.competitors`→`set_tracked_competitors`, `budgetCap`/`budgetEnforce`→merge into `budget`, blob keys→per-key merge; `team`/`security`→`{"error": "not_yet_available"}`, never a false-success 200). Consumed by `apps.api.views.ProjectSettingsView` | exists |
| `apps/dashboard/services/tests/test_settings_service.py` | Tests for the above (connector reshape incl. site-isolation, team reshape incl. honest blanks/initials, `build_settings_response` exact-default-blob + partial-blob-merge cases incl. `usage`/`sync` shape, `apply_settings_update` persistence/per-key-merge/budget-sub-merge/team+security-rejection cases) | exists |
| `apps/dashboard/spa_views.py` | Phase A: `spa_index` — serves the approved Limitless Marketing SPA (`static/spa/index.html`) at `/app/`; injects an auth-token bootstrap script (see module docstring for 3 footguns re: duplicate `<head>` text, `api.js` double-execution, `baseUrl` truthy gate) | exists |
| `apps/sync/models.py` | `SyncLog` + `RefreshRun` Django models + `SyncStatus`/`RefreshStatus` TextChoices | exists |
| `apps/sync/admin.py` | `SyncLogAdmin`, `RefreshRunAdmin` | exists |
| `apps/sync/migrations/` | 0001 initial + 0002 TextChoices/ordering | exists |
| `apps/sync/management/commands/migrate_legacy_data.py` | One-time MVP→production data migration (analytics + insights); `--source` option | exists |
| `apps/sync/management/commands/add_project_fields.py` | Phase A: idempotent one-off command adding `vertical`/`location`/`slug` columns to the SQLAlchemy `sites` table + backfilling `slug` (not a Django migration — see `.claude/DATABASE.md` §3.1) | exists |
| `apps/sync/views.py` | `sync_all_view`, `sync_page_view`, `sync_status_view` — HTMX polling endpoints | exists |
| `apps/sync/urls.py` | `/sync/all/`, `/sync/page/<page>/`, `/sync/status/` (app_name="sync") | exists |
| `templates/sync/progress.html` | HTMX progress bar partial (self-polling when active_sync=True) | exists |

## API app — `apps/api/` (Phase A: DRF API foundation for the SPA)

| Path | Purpose | Status |
|---|---|---|
| `apps/api/authentication.py` | `BearerTokenAuthentication` — DRF `TokenAuthentication` subclass using `Bearer` keyword (the SPA's `app/api.js` sends `Authorization: Bearer <token>`, not DRF's default `Token`) | exists |
| `apps/api/views.py` | `resolve_project_or_404`/`latest_data_anchor` shared helpers (slug→Site lookup, latest-SEO-date anchor — used by every project-scoped view); `PingView` (auth smoke test), `ProjectListCreateView` (`GET`/`POST /api/projects`), `ProjectOverviewView` (`GET /api/projects/<slug>/overview`), `ProjectSEOView` (`GET /api/projects/<slug>/seo`, Phase B1), `ProjectKeywordsView` (`GET /api/projects/<slug>/keywords`, Phase B2), `ProjectPositionsView` (`GET /api/projects/<slug>/positions`, Phase B3 — accepts `range`, unlike SEO/Keywords), `ProjectAlertsView` (`GET /api/projects/<slug>/alerts`, Phase B4), `ProjectBacklinksView` (`GET /api/projects/<slug>/backlinks`, Phase C1), `ProjectSiteAuditView` (`GET /api/projects/<slug>/audit`, Phase C2), `ProjectOffsiteView` (`GET /api/projects/<slug>/offsite`, Phase C3 — accepts `range` via `resolve_range_periods`, like Positions), `ProjectAdsView` (`GET /api/projects/<slug>/ads`, Phase C4 — accepts `range` via `resolve_range_periods`, like Positions/Offsite), `ProjectAIView` (`GET /api/projects/<slug>/ai`, Phase D — no `range` param, unlike Ads/Offsite/Positions) + `ProjectAIActionView` (`POST /api/projects/<slug>/ai/<action>`, Phase D — the project's first real first-party mutation endpoint; dispatches by `action` path segment to 6 handlers: `setup`/`targets`/`prompts`/`prompts-remove`/`prompts-config`/`lists`; any unmapped action, including `run`/`inspect`, returns a clean 400), `ProjectSettingsView` (`GET`/`PUT /api/projects/<slug>/settings`, Phase E — no `range` param, like AI; the project's first `GET`+`PUT`-on-the-same-view endpoint — `PUT` returns a clean 400 via `apply_settings_update`'s `{"error": ...}` for `team`/`security`, otherwise re-fetches and returns the full `build_settings_response` shape like Phase D's mutation-then-reload pattern) — all `login_not_required` so DRF's own auth returns 401 instead of a 302 to the login page | exists |
| `apps/api/serializers.py` | `ProjectSerializer`, `ProjectCreateSerializer`, `OverviewQuerySerializer` (validates `range=7d\|30d\|90d`) | exists |
| `apps/api/urls.py` | `/api/ping`, `/api/projects`, `/api/projects/<slug>/overview`, `/api/projects/<slug>/seo` (Phase B1), `/api/projects/<slug>/keywords` (Phase B2), `/api/projects/<slug>/positions` (Phase B3), `/api/projects/<slug>/alerts` (Phase B4), `/api/projects/<slug>/backlinks` (Phase C1), `/api/projects/<slug>/audit` (Phase C2), `/api/projects/<slug>/offsite` (Phase C3), `/api/projects/<slug>/ads` (Phase C4), `/api/projects/<slug>/ai` + `/api/projects/<slug>/ai/<action>` (Phase D — the plain `ai` GET route and the `ai/<action>` POST route don't conflict: the `slug` converter's regex excludes `/`, so `ai` alone never matches the second pattern), `/api/projects/<slug>/settings` (Phase E, `GET`+`PUT` on the same route) (app_name="api"); mounted at `path('api/', ...)` in `config/urls.py` | exists |
| `apps/api/tests/` | `test_ping.py`, `test_projects.py`, `test_overview.py`, `test_seo.py` (Phase B1), `test_keywords.py` (Phase B2), `test_positions.py` (Phase B3), `test_alerts.py` (Phase B4), `test_backlinks.py` (Phase C1), `test_site_audit.py` (Phase C2), `test_offsite.py` (Phase C3 — real-data current-period case, `range=7d`/`90d` boundary-shift cases, 404, 401), `test_ads.py` (Phase C4 — real-data current/prev period-isolation case, `range=7d` boundary-shift case excluding an out-of-window row, 404, 401), `test_ai.py` (Phase D — GET real-data/empty-DB/404/401; POST coverage for all 6 mutation actions incl. update-not-duplicate on `targets`, added-count + list-scoping on `prompts`, real-usable-FK on `lists` create, GET-after-mutation persistence proof on `setup`; `run`/`inspect`/unknown action all assert a clean 400), `test_settings.py` (Phase E — GET real-`SyncLog`/real-team case, fresh-project honest-defaults case incl. `usage`/`sync`, 404, 401; PUT `credentials` persistence-on-next-GET, PUT `budgetCap` then `notifications` per-key-merge proof via a follow-up GET, PUT `team`/`security` clean 400 + nothing persisted, 401/404 on PUT) | exists |

*Each app currently holds the default Django files (`models.py`, `views.py`, `admin.py`,
`apps.py`, `tests.py`, `migrations/`). App configs use dotted name `apps.<name>` with a short
`label`.*

## Pipeline DB — `pipeline/db/` (Phase 3: schema + engine created)

| Path | Purpose | Status |
|---|---|---|
| `pipeline/db/schema.py` | SQLAlchemy ORM for all analytics tables + `init_db(engine)`. +2026-06-15: `CompetitorKeywordRanking`, `TrackedCompetitor`, `AIKeywordData`. +2026-06-17: `SavedKeyword` (Keyword Explorer research list) | exists |
| `pipeline/db/engine.py` | `get_engine(db_path)`, `get_sessionmaker(db_path)` factories | exists |
| `pipeline/db/tests/test_schema.py` | 9 tests covering all table families + prediction tables | exists |
| `pipeline/db/tests/test_engine.py` | engine creation + SELECT 1 tests | exists |
| `pipeline/db/writer.py` | All upsert helpers (batched, SQLAlchemy 2.x) + `ensure_tables()`. +2026-06-15: `upsert_competitor_keyword_rankings`, `upsert_ai_keyword_data`. +2026-06-17: `upsert_saved_keywords` | exists |
| `pipeline/connectors/base.py` | `BaseConnector` — `sync()`, `_write_records()`, Django `SyncLog` bridge | exists |
| `pipeline/connectors/<name>.py` | connector files (gsc, ga4, gsc_keywords, gsc_pages, url_inspection, pagespeed, sitemap, dataforseo_*, google_ads, meta, linkedin, webflow, wordpress) | exists |
| `pipeline/connectors/dataforseo_serp_competitors.py` | +2026-06-15: per-keyword competitor rank capture (full-SERP); writes `competitor_keyword_rankings` | exists |
| `pipeline/connectors/dataforseo_ai_keywords.py` | +2026-06-15: AI Optimization AI-search keyword volume; writes `ai_keyword_data` | exists |
| `pipeline/services/sync_engine.py` | `sync_all()` + `sync_page()` + `PAGE_CONNECTORS` map — called from background threads | exists |
| `pipeline/services/site_service.py` | `list_sites`, `get_default_site_id`, `add_site`, `update_site`, `delete_site` | exists |
| `pipeline/services/competitor_service.py` | +2026-06-15: resolve tracked competitor columns (auto-seed from `competitor_domains` or editable override) | exists |
| `pipeline/services/saved_keyword_service.py` | +2026-06-17: Keyword Explorer saved research list — list/save/delete over the `saved_keywords` table (separate from keyword tracking) | exists |
| `pipeline/connectors/tests/test_dataforseo_lookup.py` | +2026-06-17: tests for `DataForSEOKeywordsConnector.lookup_keywords` (mocked HTTP) | exists |
| `pipeline/db/tests/test_saved_keywords.py` | +2026-06-17: `upsert_saved_keywords` + `saved_keyword_service` round-trip tests | exists |
| `pipeline/services/aggregate_service.py` | `rebuild_seo_aggregates(site_url)` — impression-weighted CTR + position rollup | exists |
| `pipeline/services/anomaly_service.py` | `AnomalyDetector` — rolling-baseline anomaly detection across SEO + Ads metrics | exists |
| `pipeline/utils/db_connection.py` | Django-settings-aware SQLAlchemy session factory (thread-safe singleton) | exists |
| `pipeline/utils/logger.py` | `get_logger(name)` — writes to `fusehealth/logs/fusehealth.log` | exists |
| `pipeline/utils/keywords.py` | `load_tracked_keywords()` — reads `fusehealth/keywords.txt` | exists |
| `pipeline/utils/period_utils.py` | Date/period helpers (rolling windows, week/month offsets) | exists |
| `pipeline/utils/auth.py` | Google OAuth2 credential refresh helper | exists |
| `pipeline/utils/retry.py` | Exponential-backoff retry decorator | exists |

## Frontend — `templates/`, `static/`

| Path | Purpose | Status |
|---|---|---|
| `templates/base.html` | Global shell (sidebar + topbar + content), Tailwind+brand tokens, HTMX, Plotly, Inter | exists |
| `templates/partials/_sidebar.html` | Nav sidebar; active state via `active`, items via `navigation` processor | exists |
| `templates/partials/_topbar.html` | Page title/subtitle + date range + Refresh; block-overridable | exists |
| `templates/components/stat_card.html` | KPI card (label, value, up/down delta pill) | exists |
| `templates/components/refresh_button.html` | Primary refresh button (HTMX wired Phase 4) | exists |
| `templates/components/sync_progress.html` | Live sync progress bar partial (polled Phase 4) | exists |
| `templates/dashboard/overview.html` | Overview page (demo data; real queries Phase 5) | exists |
| `templates/dashboard/keywords.html` | Keywords page. +2026-06-17: **Keyword Explorer** section (ad-hoc research) + `explorerTable` Alpine logic in `body_extra` | exists |
| `templates/dashboard/partials/_explorer_results.html` | +2026-06-17: Keyword Explorer results table (Alpine: sort/select/download/copy/save) | exists |
| `templates/dashboard/partials/_saved_keywords.html` | +2026-06-17: saved research keywords panel (swap target `#saved-keywords-panel`) | exists |
| `static/css/global.css` | Small custom CSS on top of Tailwind (scrollbar, htmx fade) | exists |
| `static/spa/` | Phase A: copied assets of the approved Limitless Marketing SPA design export — `index.html`, `app/api.js`, `app/fixtures.js`, `support.js`, `css/`, `assets/`. Served raw (not through Django templates) by `apps/dashboard/spa_views.py` at `/app/` | exists |
| `apps/dashboard/views.py` | `overview` view (+ demo Plotly spec builder) | exists |
| `apps/dashboard/urls.py` | dashboard routes (`overview` at `/`) | exists |
| `apps/dashboard/context_processors.py` | `navigation` — sidebar items + availability badges | exists |

## Brain — `.claude/`

| Path | Purpose | Status |
|---|---|---|
| `.claude/PRODUCT_CONTEXT.md` | What/who/why + the product contract + scope | exists |
| `.claude/ARCHITECTURE.md` | Layers, structure, apps, settings, data flows | exists |
| `.claude/FILE_INDEX.md` | This map | exists |
| `.claude/SKILLS.md` | Coding standards & patterns | exists (v1) |
| `.claude/checklist.md` | The live build plan / current state | exists |
| `.claude/DESIGN.md` | Design system (colors, type, components, chart theme) | exists |
| `.claude/DATABASE.md` | Analytics schema + column lists + two-DB boundary + prediction layer + migration counts | exists |
| `.claude/API_REFERENCE.md` | Each API: class, credentials, tables written, rate limits, status, dependency order | exists |

## Design docs — `docs/superpowers/`

| Path | Purpose | Status |
|---|---|---|
| `docs/superpowers/specs/2026-06-11-phase3-database-design.md` | Phase 3 DB design spec (two-DB boundary, all tables, prediction layer, migration approach) | exists |
| `docs/superpowers/plans/2026-06-11-phase3-database.md` | Phase 3 implementation plan (9 TDD tasks) | exists |

---

## Old MVP — parent directory (reference only, do not extend)

`app.py`, `pages/*.py`, `worker.py`, and the original `connectors|db|services|utils` folders are
the Streamlit MVP. Kept for reference and as the source for the Phase 4 pipeline copy.
