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
| `apps/dashboard/models.py` | `Insight` Django model — team-entered context (date, team, title, impact, created_by, is_verified) | exists |
| `apps/dashboard/admin.py` | `InsightAdmin` | exists |
| `apps/dashboard/migrations/` | 0001 initial + 0002 Meta ordering | exists |
| `apps/dashboard/` | views/templates per page; reads DB only | scaffolded (pages: Phase 5) |
| `apps/sync/models.py` | `SyncLog` + `RefreshRun` Django models + `SyncStatus`/`RefreshStatus` TextChoices | exists |
| `apps/sync/admin.py` | `SyncLogAdmin`, `RefreshRunAdmin` | exists |
| `apps/sync/migrations/` | 0001 initial + 0002 TextChoices/ordering | exists |
| `apps/sync/management/commands/migrate_legacy_data.py` | One-time MVP→production data migration (analytics + insights); `--source` option | exists |
| `apps/sync/views.py` | `sync_all_view`, `sync_page_view`, `sync_status_view` — HTMX polling endpoints | exists |
| `apps/sync/urls.py` | `/sync/all/`, `/sync/page/<page>/`, `/sync/status/` (app_name="sync") | exists |
| `templates/sync/progress.html` | HTMX progress bar partial (self-polling when active_sync=True) | exists |

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
