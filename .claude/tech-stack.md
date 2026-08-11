# Tech Stack

> Reverse-engineered from the current codebase. Every statement here describes code that
> exists on disk today. Where a dependency is installed but unused, that is stated explicitly.

---

## 1. At a glance

| Layer | Technology | Where |
|---|---|---|
| Backend framework | Django 6.0 | `config/`, `apps/` |
| REST layer | Django REST Framework 3.15 | `apps/api/` |
| App database | SQLite via Django ORM (`django_internal.db`) | `apps/accounts`, `apps/dashboard`, `apps/sync` |
| Analytics database | SQLite via SQLAlchemy 2.x (`data/fusehealth.db`) | `pipeline/db/` |
| Data pipeline | Plain Python connector classes + `requests` / Google client libs | `pipeline/connectors/` |
| Frontend | Single-page app on a bundled React 18 runtime ("dc-runtime") | `static/spa/` |
| Frontend build | **None.** Server-side `#include` text expansion at request time | `apps/dashboard/spa_views.py` |
| Styling | Inline `style="…"` objects in templates; Tailwind CDN on the login page only | `static/spa/src/`, `templates/registration/login.html` |
| Charts | Hand-written inline SVG (`<polyline>`, `<path>`, conic-gradient gauges) | `static/spa/src/js/pages/*.js` |
| Auth (pages) | Django sessions + `LoginRequiredMiddleware` | `config/settings/base.py` |
| Auth (API) | DRF `TokenAuthentication` with the `Bearer` keyword | `apps/api/authentication.py` |
| Background work | `threading.Thread(daemon=True)` per refresh run | `apps/dashboard/services/sync_api_service.py` |
| Production serving | Gunicorn + WhiteNoise (declared in requirements; no deploy config in repo) | `requirements.txt` |
| Tests | Django `TestCase` / DRF `APITestCase` | `apps/**/tests/`, `pipeline/**/tests/` |

---

## 2. Backend

### Django 6.0

- Project package: `config/`. Settings are split three ways:
  - `config/settings/base.py` — shared configuration, `env()` helper, logging, email, DB paths.
  - `config/settings/local.py` — `DEBUG=True`, permissive `ALLOWED_HOSTS`, throwaway secret key. **This is the default** (`manage.py` sets `DJANGO_SETTINGS_MODULE=config.settings.local`).
  - `config/settings/production.py` — `DEBUG=False`, raises `RuntimeError` at import if `DJANGO_SECRET_KEY` is unset, HSTS/SSL redirect/secure cookies, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` read from comma-separated env vars.
- Installed apps: `django.contrib.*`, `rest_framework`, `rest_framework.authtoken`, plus `apps.accounts`, `apps.dashboard`, `apps.sync`, `apps.api`.
- Middleware is stock Django plus **`django.contrib.auth.middleware.LoginRequiredMiddleware`**, which protects every view by default. Views opt out with `@login_not_required`.
- Root URLconf `config/urls.py` exposes only four things: `/admin/`, the `apps.accounts` auth routes (`/login/`, `/logout/`, `/accept-invite/`, `/password-reset/…`, `/reset/…`), `/api/…`, and `/` (the SPA). `/app/` is a permanent-less redirect to `/` for old bookmarks.

**Why Django:** the app needs sessions, an admin, a migration system, and a battle-tested auth stack for a small internal team. None of that is worth hand-rolling.

### Django REST Framework 3.15

Configured in `config/settings/base.py`:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.api.authentication.BearerTokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
```

All API views are plain `APIView` subclasses — no viewsets, no routers, no pagination classes. Serializers are used in exactly three places (`apps/api/serializers.py`): shaping a `Site` row into a project object, validating project creation, and validating the `range` query parameter. Everything else returns hand-built dictionaries from the service layer.

**Why DRF and not plain Django views:** the `Response`/`APIView` pair gives consistent JSON rendering, content negotiation, and a pluggable auth/permission layer for near-zero cost. The team deliberately stopped short of viewsets because the endpoints are read-shaped views over a service layer, not CRUD over models.

---

## 3. Databases

Two SQLite databases, split on purpose.

### `django_internal.db` — Django ORM

Path from `DJANGO_INTERNAL_DB` env var, defaulting to `BASE_DIR / "django_internal.db"`.
Created and evolved by `python manage.py migrate`.

Holds: `auth_user`, sessions, admin log, DRF `authtoken`, and the project's own Django models —
`UserProfile`, `UserInvitation`, `Insight`, `AITarget`, `AIPromptList`, `AIPrompt`,
`ProjectSettings`, `SyncLog`, `RefreshRun`.

### `data/fusehealth.db` — SQLAlchemy

Resolved by `pipeline/utils/db_connection.py::_get_db_url()`, most specific first:
`settings.ANALYTICS_DB_URL` → env `ANALYTICS_DB_URL` → `settings.ANALYTICS_DB_PATH` →
env `ANALYTICS_DB_PATH` → `BASE_DIR / "data" / "fusehealth.db"`. The last three are filesystem
paths and get wrapped as `sqlite:///<path>`; the first two are full SQLAlchemy URLs.

In production `settings.ANALYTICS_DB_URL` is a `postgresql+psycopg://` DSN pointing at the same
database Django uses (see `config/settings/base.py`), so the analytics layer runs on Postgres
there and SQLite everywhere else — **both paths are supported at once, this is not a cutover.**
Created by `init_db(engine)` in `pipeline/db/schema.py`; **not** covered by Django migrations.
Schema changes are applied either by `init_db` (new tables), by `ensure_tables(session, Model)`
(lazy per-table creation at first use), or by a one-off management command
(`apps/sync/management/commands/add_project_fields.py` uses guarded `ALTER TABLE`).

Connection is configured in `pipeline/utils/db_connection.py`: a lazily-built, thread-locked
`sessionmaker` with `expire_on_commit=False`, and `PRAGMA journal_mode=WAL`,
`foreign_keys=ON`, `synchronous=NORMAL` applied on every connect — **only when the engine's
dialect is `sqlite`**, since those PRAGMAs are invalid SQL on Postgres.

**Why two databases:** Django's ORM owns app/operational state that benefits from migrations and
the admin. The analytics tables are wide, upsert-heavy, written by non-Django pipeline code, and
were inherited from a pre-Django MVP. Keeping them under SQLAlchemy means the pipeline never
imports Django's ORM, and a schema change to one side can't break the other.

**The cross-database join key is a string.** Every analytics table has a `site_id`
`VARCHAR(255)` column holding the site's URL (e.g. `sc-domain:example.com`), which matches
`Site.site_url` and the `site_url` `CharField` on the Django models. There are no cross-database
foreign keys, and there cannot be.

### ORM usage

- Django ORM for everything in `django_internal.db`.
- SQLAlchemy 2.x Core-style `select()` / `insert()` for analytics reads, plus
  `upsert_insert(session)(...).on_conflict_do_update(...)` for every write
  (see `pipeline/db/writer.py`). **Writes are always upserts, never blind inserts.**
- **Never import `sqlalchemy.dialects.sqlite.insert` directly.** Use
  `pipeline/db/dialect.py` — `upsert_insert(session)` returns the sqlite or postgresql
  `insert` construct for the live connection (only those carry `on_conflict_do_update`),
  and `max_batch_size(session, <sqlite_value>)` returns the row-batch size. The same
  writer runs against both backends, and the test suite always drives SQLite.
- Writes are batched (60–80 rows on SQLite) to stay under SQLite's ~999 bound-parameter
  limit; on Postgres the batch is 1000, since its limit is 65535.
- Anything expressed as raw SQL must be checked against both dialects. Known case:
  `pipeline/services/aggregate_service.py` keeps a separate week/month truncation
  expression per backend (`_PERIOD_EXPR_SQLITE` / `_PERIOD_EXPR_POSTGRES`).

---

## 4. Frontend

There is no npm, no bundler, no `package.json`, and no build step.

### The runtime: dc-runtime (`static/spa/vendor/support.js`)

A ~62 KB pre-built, generated bundle (header comment: *"GENERATED from dc-runtime/src/*.ts — do
not edit"*). It boots a React 18 application from declarative HTML:

- It loads **React 18.3.1 UMD**, **ReactDOM 18.3.1 UMD**, and **@babel/standalone 7.29.0**
  from `unpkg.com` at runtime. These are the only external front-end dependencies, and they are
  **not vendored** — the app requires network access to unpkg to boot.
- It parses the `<x-dc>` element in the document as a template and the
  `<script type="text/x-dc" data-dc-script>` block as the component class body.
- Template directives: `{{ expression }}` interpolation, `<sc-if value="{{ … }}">`,
  `<sc-for list="{{ … }}" as="item">`, `<helmet>` (hoists tags into `<head>`), plus
  `sc-host`, `sc-name`, `sc-placeholder`, `sc-interp` internals.
- `hint-placeholder-val` / `hint-placeholder-count` attributes drive the design-time preview
  only; they have no effect at runtime.
- The component class extends `DCLogic` and exposes React-like `state`, `setState`,
  `componentDidMount`, `componentWillUnmount`, plus a project-specific `renderVals()` that
  returns the object every `{{ … }}` hole reads from.

### The application (`static/spa/src/`)

| File | Role |
|---|---|
| `index.html` | Document shell: `<helmet>`, layout skeleton, `#include` directives, the `<script data-dc-script>` wrapper |
| `components/*.html` | Sidebar, topbar, change-password modal, accept-invite modal |
| `pages/*.html` | One template fragment per screen |
| `js/app.js` | The component body: state, router, data fetching, all mutation handlers, formatters, and the top of `renderVals()` |
| `js/pages/*.js` | Per-page view-model builders, each `#include`d into the bottom of `renderVals()` |

### The `#include` preprocessor

`apps/dashboard/spa_views.resolve_includes()` recursively expands two directive forms before the
HTML is served:

```html
<!-- #include "components/sidebar.html" -->
/*  #include "js/pages/overview.js"    */
```

This is why `index.html` on disk is ~800 lines but the served document is far larger, and why
`js/pages/*.js` files start mid-scope (they are spliced into `renderVals()`'s body).

**Why this instead of a bundler:** the design source is an exported design-tool document. A build
step would have created a second source of truth and a toolchain to maintain for a two-to-three
user internal app. Text inclusion keeps the served output byte-identical to the authored files.

### Legacy/fixture files

`static/spa/app/api.js` is the frontend's transport **and** a complete in-browser fixture backend.
It exposes `window.FuseAPI = { config, get, post, put, del }`. When `config.baseUrl` is falsy it
serves demo data from `static/spa/app/fixtures.js`; when truthy every call becomes a real
`fetch()`. In production `spa_views.spa_index` forces `baseUrl = '/'`, so the fixture branch is
dead in the served app — but it remains the reason `get/post/put/del` have their current shapes.

`static/spa/index.html`, `static/spa/css/global.css`, and `static/css/global.css` are leftovers
from the removed HTMX/Tailwind template UI. `static/spa/us_cities.json` (~1 MB) is fetched by
`app.js` at boot to populate the Position Tracking location picker.

---

## 5. Authentication & authorization

### Page authentication

- `LoginRequiredMiddleware` protects everything. `LOGIN_URL = "login"`,
  `LOGIN_REDIRECT_URL = "spa"`, `LOGOUT_REDIRECT_URL = "login"`.
- `apps/accounts/views.py` wraps Django's built-in `LoginView` (branded template,
  `redirect_authenticated_user=True`) and a CSRF-exempt `LogoutView` that redirects to `/login/`.
- It also holds the two public flows that must work **without** an account: `AcceptInviteView`
  (`/accept-invite/?token=…`, the invitation email's target) and the four
  `PasswordReset*View` subclasses. All are `@login_not_required` — that decorator is the whole
  reason they are subclasses instead of `auth_views.*` wired straight into `urls.py`.
- Links in outbound email are built from the incoming request's host
  (`apps/api/views.py::build_frontend_link` for invites, Django's `RequestSite` for password
  resets), so dev mails localhost and production mails the deployed domain with no config.
  `FRONTEND_URL` overrides the former only when it isn't a stale localhost value.
- `apps/accounts/backends.EmailOrUsernameModelBackend` lets a user sign in with **either**
  username or email. It is listed before `ModelBackend` in `AUTHENTICATION_BACKENDS` and
  performs a dummy password hash on a miss to flatten the timing signal.

### API authentication

- `apps/api/authentication.BearerTokenAuthentication` is stock DRF `TokenAuthentication` with
  `keyword = "Bearer"` (the frontend transport sends `Authorization: Bearer <token>`).
- A `post_save` signal on `AUTH_USER_MODEL` (`apps/accounts/models.ensure_auth_token`)
  `get_or_create`s a token for every user, so tokens always exist.
- Because `LoginRequiredMiddleware` runs *before* DRF's authentication, API views must be
  decorated `@method_decorator(login_not_required, name="dispatch")` or a token-only request is
  302'd to the login page instead of reaching DRF. Nearly every view carries this decorator.

### Token delivery to the SPA

`spa_views.spa_index` injects a bootstrap `<script>` immediately after the **first** `<head>`
occurrence. It installs an `Object.defineProperty` setter on `window.FuseAPI` that re-applies
`baseUrl='/'`, `authToken`, and `user` to *every* object `app.js` ever assigns — because that
script executes twice (once during normal parse, once when the runtime relocates `<helmet>`
content). The three footguns behind this design are documented at length in the module docstring.

### Roles

There are **two independent role vocabularies in the code today**, and they do not agree:

| Vocabulary | Values | Defined in | Used by |
|---|---|---|---|
| Legacy | `founder`, `seo`, `ads` | `apps/accounts/models.Role` + `ROLE_PAGE_ACCESS` | `seed_users`, `apps/accounts/decorators.role_required` (**no live caller**) |
| Live | `Owner`, `Admin`, `Analyst` | Literal strings in `apps/api/views.py`, `settings_service.query_team_raw`, `spa_views.spa_index` | Every current permission check |

`UserProfile.role` is a `CharField(choices=Role.choices)` but is written with `"Owner"` /
`"Admin"` / `"Analyst"` values that are outside those choices. SQLite does not enforce choices,
so this works — but it means `get_role_display()` and `can_access()` are unreliable, and the
legacy `role_required` decorator has no remaining page views to guard. Treat the *live*
vocabulary as authoritative and the legacy one as dead weight awaiting removal.

---

## 6. External services

Credentials come from `.env` in development (`python-dotenv`, loaded in `config/settings/base.py`
and again in several `pipeline/` modules) and from real environment variables in production.
`.env` is git-ignored; `.env.example` documents every variable.

| Service | Auth | Used by | Status in code |
|---|---|---|---|
| Google Search Console | OAuth2 refresh token (`pipeline/utils/auth.py`) | `gsc`, `gsc_keywords`, `gsc_pages`, `url_inspection`, `gsc_property` | Wired, in `ALL_CONNECTORS` |
| Google Analytics 4 Data API | Same OAuth2 credentials | `ga4` | Wired |
| PageSpeed Insights | `GOOGLE_API_KEY` | `pagespeed` | Wired |
| Google Ads | `GOOGLE_ADS_*` | `google_ads` | Connector exists; credentials empty by default; reachable via the `ads` page scope |
| DataForSEO | HTTP Basic (`DATAFORSEO_LOGIN` / `_PASSWORD`) | 10 connectors + 2 live endpoints | Wired |
| OpenAI | `OPENAI_API_KEY` | `pipeline/services/ai_summary_service.py` | Wired; skipped with a warning when the key is absent |
| Meta / LinkedIn / Webflow / WordPress | Env vars | `meta`, `linkedin`, `webflow`, `wordpress` connectors | Code exists, registered in the connector factory, **not** in `ALL_CONNECTORS` or any page scope |
| SMTP (email) | `EMAIL_*` | Team invitations | Falls back to the console backend when `EMAIL_HOST_USER` is empty |

Google client libraries in use: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`
(Search Console + URL Inspection), `google-analytics-data` (GA4). DataForSEO is called with plain
`requests`. OpenAI is called with plain `requests` against
`https://api.openai.com/v1/chat/completions` — the `openai` package is in `requirements.txt` but
is **not imported anywhere**.

See `api-reference.md` §"External integrations" for endpoint-level detail.

---

## 7. Python dependencies

From `requirements.txt`:

| Package | Constraint | Actually used? |
|---|---|---|
| `Django` | `>=6.0,<6.1` | Yes |
| `djangorestframework` | `>=3.15,<3.16` | Yes |
| `python-dotenv` | `>=1.0` | Yes |
| `django-htmx` | `>=1.17` | **No** — not in `INSTALLED_APPS`; leftover from the removed template UI |
| `gunicorn` | `>=22.0` | Production only; no systemd/nginx config in the repo |
| `whitenoise` | `>=6.6` | **Not** in `MIDDLEWARE`; declared but unwired |
| `pandas` | `>=2.0` | Yes — `apps/dashboard/services/keywords_service.py` |
| `plotly` | `>=5.20` | **No** — `overview_service.build_traffic_chart()` emits a Plotly spec dict, but nothing renders it |
| `SQLAlchemy` | `>=2.0` | Yes |
| `requests` | `>=2.31` | Yes |
| `lxml`, `beautifulsoup4` | | Sitemap/HTML parsing in `pipeline/connectors/sitemap.py` |
| `openai` | `>=1.30` | **No** — OpenAI is called via raw `requests` |
| `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client` | | Yes |
| `google-analytics-data` | `>=0.18` | Yes |
| `google-ads` | `>=24.0` | Only when Google Ads credentials exist |
| `weasyprint` | `>=62.0` | Preferred engine for `POST /api/domain-overview/report`. **Needs system libraries; see below.** |
| `xhtml2pdf` | `>=0.2.16` | Fallback engine for the same endpoint. Pure Python — no system libraries. |

### Two PDF engines, tried in order

`domain_overview_report_service.load_pdf_renderer()` returns `(render_fn, engine_name)` for
the first engine that imports cleanly, in the order declared by `PDF_ENGINES`:

1. **WeasyPrint** — best fidelity, but needs the system libraries below.
2. **xhtml2pdf** — pure Python on top of reportlab, so `pip install -r requirements.txt` is
   genuinely sufficient. Narrower CSS: it silently drops `letter-spacing`, and it has no CSS
   page-margin boxes at all.

**501 now means BOTH failed**, which should not happen on a machine that installed
requirements. This matters because the endpoint previously shipped WeasyPrint-only and
therefore answered 501 on every deployment that had not run the apt step — which was all of
them.

**The two engines spell page footers differently, and this is not cosmetic.** xhtml2pdf's
CSS parser *raises* on WeasyPrint's `@bottom-center` margin box (`TypeError` inside
`cssParser._parseAtPage`), so it does not merely lose the page number — it fails the whole
render. `templates/reports/domain_overview.html` therefore branches on the `engine` context
value: `@bottom-center` for WeasyPrint, an `@frame` pointing at a `#reportFooter` element for
xhtml2pdf. **Adding an engine to `PDF_ENGINES` means adding a branch there too.**

`RealPdfEngineTests` in `apps/api/tests/test_domain_overview_report.py` drives the real
resolver against the real template for exactly this reason: every other test in that module
hands the service a fake renderer, and a fake never touches a real engine.

### WeasyPrint needs system libraries (deploy step)

WeasyPrint binds to **cairo, pango and libgobject at import time** through ctypes, so
`pip install -r requirements.txt` on a bare VPS installs the Python package and the import
still fails — with `OSError`, not `ImportError`. On Debian/Ubuntu:

```
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
                   libffi-dev shared-mime-info
```

`load_pdf_renderer()` imports it lazily and catches both failure shapes, so a server without
these libraries runs the whole API normally and simply falls through to xhtml2pdf. Never move
that import to module scope: it would take the entire API down to serve one endpoint.

**Fonts are a second, separate deploy concern.** A PDF is rendered on the server with the
server's fonts, and a headless box has almost none — a unicode domain or an RTL anchor comes
out as empty boxes with nothing in the logs. Either install a broad font
(`apt-get install fonts-dejavu-core fonts-noto-core`) or drop a `.ttf`/`.otf` into
`static/fonts/report/` (or point `REPORT_FONT_PATH` at one), which the report embeds via
`@font-face`.

Python 3.11+ (the code uses PEP 604 `str | None` unions and `str.removeprefix`). README notes
development on 3.13.

---

## 8. Environment variables

| Variable | Purpose | Consumed by |
|---|---|---|
| `DJANGO_SECRET_KEY` | Signing key. Required in production. | `config/settings/*` |
| `FIELD_ENCRYPTION_KEY` | Fernet key encrypting saved Ads platform credentials (Google Ads / Meta Ads) at rest. Required in production. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Rotating it orphans every previously-saved Ads credential -- `get_decrypted_credential` treats an `InvalidToken` from a rotated key identically to "nothing saved". | `config/settings/*`, `apps/dashboard/services/ads_credentials.py` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames | `production.py` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins with scheme | `production.py` |
| `DJANGO_INTERNAL_DB` | Override path to the Django DB | `base.py` |
| `ANALYTICS_DB_PATH` | Override *path* to the SQLite analytics DB | `base.py`, `pipeline/utils/db_connection.py` |
| `ANALYTICS_DB_URL` | Full SQLAlchemy URL for the analytics DB; outranks `ANALYTICS_DB_PATH`. Set from `POSTGRES_*` in `base.py`, or directly for standalone pipeline runs. | `base.py`, `pipeline/utils/db_connection.py` |
| `FUSEHEALTH_FOUNDER_PASSWORD`, `_SEO_`, `_ADS_` | Seed passwords | `manage.py seed_users` |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` | Google OAuth2 | `pipeline/utils/auth.py` |
| `GSC_SITE_URL` | Fallback GSC property | `gsc`, `ga4`, `site_service` |
| `GA4_PROPERTY_ID` | Fallback GA4 property (only when no `Site` row exists) | `ga4` |
| `GOOGLE_API_KEY` | PageSpeed Insights | `pagespeed` |
| `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`, `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Google Ads | `google_ads`, and `ads_service` reads two of them to derive a `connected` flag |
| `OPENAI_API_KEY` | Weekly AI summary | `ai_summary_service` |
| `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | DataForSEO Basic auth | all DataForSEO connectors |
| `DATAFORSEO_TARGET_DOMAIN` | Default rank-tracking target | `site_service`, `refresh_backlinks` |
| `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` | Meta Marketing API | `meta` (unwired) |
| `LINKEDIN_*` | LinkedIn Ads API | `linkedin` (unwired) |
| `WEBFLOW_*`, `WP_*`, `FRAMER_SITEMAP_URL` | CMS connectors | `webflow`, `wordpress`, `sitemap` (unwired) |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL` | Invitation email | `base.py`, `apps/api/views.py` |
| `FRONTEND_URL` | Optional override for the base URL in invitation emails. **Leave blank** — the link is derived from the request's own host | `apps/api/views.py` |

`scripts/audit_env.py` performs a live credential audit and reports availability without
printing secrets.

---

## 9. Background jobs & scheduling

- **No Celery and no RQ.** Scheduling is one management command driven by the OS scheduler.
- A refresh is its own OS process — `manage.py run_sync`, spawned by `start_sync_run()`, with
  its pid stored on the `RefreshRun` row. Progress is written to that row; the SPA polls
  `GET /api/tasks/<id>` every 500 ms until `done`. (It used to be a daemon thread inside the
  web worker, where any restart or worker recycle killed it silently. A run now survives a
  web-server restart.)
- A run that dies anyway is reaped by `apps/sync/scheduling.reap_orphaned_runs()` — a dead pid
  is direct evidence, with `RUN_TIMEOUT` (2 h) as the fallback. It runs on the first request of
  each web process, on every scheduler tick, and before a run is started or reported.
- The same call then runs `reconcile_orphaned_sync_logs()`, which clears the **connector**
  (`SyncLog`) rows left at `running` by that death. Without it, Settings → Data pipeline
  reported "Last synced: never · 0 records" forever for whichever connector was in flight —
  see `.claude/api-reference.md` § Orphaned-run reaping.
- `SyncLog.last_synced` means *last finished*: only the `success`/`error` writes stamp it, and a
  start leaves the stored value alone.
- The Settings → Automation "sync schedule" (`syncConfig`) is read and acted on by
  `manage.py run_scheduled_syncs` (point Task Scheduler / cron at it hourly); it starts at most
  one due module per site per tick. `settings_service` and the scheduler share
  `apps/sync/scheduling.py`, so the date shown and the decision made cannot drift apart.

---

## 10. Logging & monitoring

- `LOGGING` in `config/settings/base.py`: console handler at `INFO`, plus a
  `RotatingFileHandler` at `ERROR` writing `logs/django_errors.log` (5 MB × 5 backups).
  `logs/` is created at import time.
- `pipeline/utils/logger.get_logger(name)` is used throughout the pipeline; it also writes
  `logs/fusehealth.log`.
- No Sentry, no APM, no metrics exporter, no analytics on the dashboard itself.

---

## 11. Testing

- Framework: Django's test runner (`python manage.py test`). Tests are `TestCase` /
  `APITestCase` subclasses — pytest is not configured (no `pytest.ini` / `pyproject.toml`),
  though a stale `.pytest_cache/` exists from ad-hoc runs.
- Layout:
  - `apps/api/tests/` — 17 endpoint test modules (one per feature area).
  - `apps/dashboard/services/tests/` — 12 service-layer modules.
  - `apps/dashboard/tests/` — model tests and `test_spa_views.py`.
  - `pipeline/db/tests/`, `pipeline/connectors/tests/`, `pipeline/services/tests/`.
- **The standard analytics-DB fixture pattern** (used by every API test): reset
  `db_connection._SessionFactory = None`, build a temp-directory SQLite file, `init_db()` it,
  and wrap the test in `override_settings(ANALYTICS_DB_PATH=…)` with an `addCleanup` teardown.
  Copy this verbatim when writing a new test — see `apps/api/tests/test_overview.py`.
- External APIs are never called from tests; connectors are tested through injected fakes
  (`pipeline/connectors/tests/test_gsc_property.py` uses a `FakeService`).

---

## 12. Deployment

The repo contains production *settings* but no deployment automation: no Dockerfile, no
`docker-compose.yml`, no systemd unit, no nginx config, no CI workflow.

What exists:

- `config/settings/production.py` — hardened settings, fails fast on a missing secret key.
- `config/wsgi.py` / `config/asgi.py`.
- `STATIC_ROOT = BASE_DIR / "staticfiles"` for `collectstatic`.
- `gunicorn` and `whitenoise` in `requirements.txt` (WhiteNoise is not yet added to `MIDDLEWARE`).

Deploying today means: set real env vars, `DJANGO_SETTINGS_MODULE=config.settings.production`,
`migrate`, `collectstatic`, and run Gunicorn behind a TLS-terminating reverse proxy.

---

## 13. Folder structure

```
Limitless_marketing_dashboard/
├── manage.py                      # defaults to config.settings.local
├── config/
│   ├── settings/{base,local,production}.py
│   ├── urls.py                    # /admin/, /login/, /logout/, /api/, /app/ -> /, /
│   ├── wsgi.py, asgi.py
├── apps/
│   ├── accounts/                  # auth: UserProfile, UserInvitation, login/logout, seed_users
│   ├── api/                       # the entire JSON API: urls.py, views.py, serializers.py, authentication.py
│   ├── dashboard/                 # SPA host + the service layer
│   │   ├── spa_views.py           # serves the SPA, expands #includes, injects the auth bootstrap
│   │   ├── models.py              # Insight, AITarget, AIPromptList, AIPrompt, ProjectSettings
│   │   └── services/              # one module per page + shared_queries, decision_engine, mutation_state
│   └── sync/                      # SyncLog, RefreshRun, admin, management commands
├── pipeline/                      # the data layer (no Django imports except lazy SyncLog writes)
│   ├── connectors/                # one class per external API, all extending BaseConnector
│   ├── db/                        # schema.py (SQLAlchemy models), writer.py (upserts), engine.py
│   ├── services/                  # sync_engine, anomaly, aggregate, technical_issues, ai_summary, …
│   └── utils/                     # auth, db_connection, period_utils, keywords, logger, retry
├── static/
│   ├── spa/src/                   # THE frontend (index.html, components/, pages/, js/)
│   ├── spa/vendor/support.js      # dc-runtime (generated; do not edit)
│   ├── spa/app/{api.js,fixtures.js}   # transport + legacy fixture backend
│   └── spa/us_cities.json
├── templates/registration/login.html  # the only server-rendered PAGE
├── templates/reports/domain_overview.html  # print-CSS source for the Domain Overview PDF
├── data/fusehealth.db             # analytics DB (git-ignored)
├── django_internal.db             # app DB (git-ignored)
├── docs/superpowers/              # historical design specs & plans (not authoritative)
├── Design_features/               # exported design source + vendor API docs (reference only)
└── scratch/                       # throwaway scripts and screenshots (not part of the app)
```

---

## 14. Coding conventions

**Python**

- Type hints on function signatures; docstrings on every public service function and connector
  `fetch()`.
- Comments explain *why*, not *what*. Several modules carry long docstrings recording a real bug
  and the reasoning behind the fix — keep that habit; it is the project's institutional memory.
- Service functions never raise for data problems: they log via
  `logging.getLogger(__name__).error(..., exc_info=True)` and return a safe empty shape. The API
  layer therefore rarely needs try/except.
- Lazy imports inside functions are used deliberately to break import cycles
  (`overview_service` → `site_audit_service`, `views` → the mutation services). Follow the local
  convention rather than hoisting them.
- Naming: `query_*_raw()` for a DB read returning primitives, `build_*_response()` for the
  API-shaped payload, `_private()` for module-internal helpers.

**JavaScript**

- No modules, no `import`/`export` — every file is spliced into one class body.
- ES2017-level syntax only (arrow functions, template literals, spread, `Object.assign`);
  no optional chaining or nullish coalescing in the app code.
- All state lives in the single `state` object at the top of `app.js`; nothing is stored on
  `this` outside `state` except deliberate non-render caches (`this._hist`, `this._iv`,
  `this._alive`).
- Styling is inline JS style objects returned from `renderVals()`, never CSS classes.

---

## 15. Architecture in one paragraph

The browser loads a single HTML document assembled at request time from `static/spa/src/`, runs a
React-based template runtime, and thereafter talks only to `/api/…` over JSON with a Bearer
token. Every API endpoint reads exclusively from SQLite and returns a fully-shaped view model —
no external API is ever called while rendering a page. External data enters the system only when
a user clicks a Refresh button, which creates a `RefreshRun` row, spawns a daemon thread that
walks a registry of connectors, upserts their output into the analytics database, and reports
progress back through a polled endpoint. Three endpoints break the read-only rule by design
(`/api/research`, `/api/domain-overview`, `/api/live-serp`) because they are explicit,
user-initiated lookups rather than page renders.
