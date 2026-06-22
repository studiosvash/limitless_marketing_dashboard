# FuseHealth — Architecture

*Read this before touching project structure, settings, routing, or the sync flow. It describes
the **clean Django project** in `fusehealth/`. Items marked (scaffolded) physically exist today;
items marked (planned: Phase N) are designed but not yet built — do not assume their code exists.*

## 1. The four layers

```
┌──────────────────────────────────────────────────────────────┐
│  L4  UI — Django templates + Tailwind (CDN) + HTMX           │
│      apps/dashboard (pages, views) · apps/accounts (auth)    │
│      Reads ONLY from the DB. Never calls an external API.    │
└───────────────────────────┬──────────────────────────────────┘
                            │ reads
┌───────────────────────────▼──────────────────────────────────┐
│  L3  DATA — two SQLite databases                             │
│      django_internal.db  (Django ORM: auth, sessions, admin, │
│                           UserProfile, sync_log)             │
│      fusehealth.db        (SQLAlchemy: all analytics tables) │
└───────────────────────────▲──────────────────────────────────┘
                            │ writes
┌───────────────────────────┴──────────────────────────────────┐
│  L2  PIPELINE — pipeline/ (reused, planned: Phase 4)         │
│      connectors/ · db/ · services/ · utils/                  │
│      Fetches from APIs, normalizes, upserts to fusehealth.db │
│      Triggered by the sync engine (apps/sync), never by a    │
│      page-render view.                                        │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP / SDK
┌───────────────────────────▼──────────────────────────────────┐
│  L1  EXTERNAL APIS (~12) — GSC · GA4 · Google Ads · Meta ·   │
│      LinkedIn · DataForSEO ×5 · Webflow · WordPress · Framer │
└──────────────────────────────────────────────────────────────┘
```

## 2. Project structure (scaffolded)

```
fusehealth/
├── manage.py                  # DJANGO_SETTINGS_MODULE defaults to config.settings.local
├── django_internal.db         # default DB (Django ORM)
├── config/                    # the Django "project" package
│   ├── settings/
│   │   ├── base.py            # shared: apps, dual-DB, templates, static, auth redirects
│   │   ├── local.py           # dev: DEBUG=True, localhost, throwaway key
│   │   └── production.py      # VPS: DEBUG=False, HTTPS hardening, secrets required from env
│   ├── urls.py · wsgi.py · asgi.py   # wsgi/asgi default to config.settings.production
├── apps/
│   ├── accounts/   (label: accounts)   # auth, roles, UserProfile        — built in Phase 2
│   ├── dashboard/  (label: dashboard)  # pages, views, templates          — built in Phase 5
│   └── sync/       (label: sync)       # sync engine, sync_log, progress  — built in Phase 4
├── pipeline/                  # reused data layer (planned: copied in Phase 4)
│   └── connectors/ · db/ · services/ · utils/
├── templates/                 # project-level templates (base.html, components, pages)
├── static/                    # css/ js/ (Tailwind via CDN; global.css here)
├── CLAUDE.md                  # project brain (router)
└── .claude/                   # brain references (this folder)
```

## 3. The three Django apps — responsibilities

- **accounts** — authentication, the three roles (`founder`/`seo`/`ads`), `UserProfile`,
  the `@role_required` guard, and the `seed_users` command. Owns login/logout.
- **dashboard** — one view + template per page. Views read from the DB (Django ORM for internal
  data, SQLAlchemy via the pipeline for analytics), render HTML, and serve HTMX partials.
  Views never call an external API.
- **sync** — the on-demand sync engine. Owns the `sync_log` model, the `sync_all` /
  `sync_page` orchestration, the endpoints the Refresh buttons hit, and the status endpoint
  HTMX polls for the live progress bar.

## 4. Settings & environment model

- Three settings modules: `base` (shared) → imported by `local` (dev) and `production` (VPS).
- `manage.py` defaults to `config.settings.local`; `wsgi.py`/`asgi.py` default to
  `config.settings.production`.
- Secrets and host-specific values come from the environment: a `.env` file in dev (loaded by
  python-dotenv in `base.py`), real environment variables in production.
- `production.py` **refuses to start** without `DJANGO_SECRET_KEY` — fail loud, never boot
  insecure.

## 5. The two databases (why split)

- **`django_internal.db`** (`default`, Django ORM): Django's own tables plus our `UserProfile`
  and `sync_log`. Managed by Django migrations.
- **`fusehealth.db`** (analytics, SQLAlchemy): all marketing/SEO tables. Managed by the reused
  pipeline's SQLAlchemy layer, **not** the Django ORM. Its path is exposed as
  `settings.ANALYTICS_DB_PATH` so the pipeline reads one settings-driven location.
- The final analytics schema is decided in Phase 3 (see `DATABASE.md` when written).

## 6. Two request paths

**Read path (every normal page load) — no APIs touched:**
```
browser → dashboard view → db/queries (SQLAlchemy) on fusehealth.db
        → DataFrame / dict → template (+ Plotly JSON) → HTML
```

**Refresh path (user clicks a Refresh button):**
```
browser → POST /sync/all/ or /sync/page/<page>/ → sync engine starts (background thread)
        → connectors fetch APIs → upsert to fusehealth.db → sync_log rows updated
browser → HTMX polls GET /sync/status/ every ~2s → progress bar partial re-renders
        → on completion, the page's data container reloads from the DB
```

The sync engine maps each page to its relevant connectors (e.g. SEO page → GSC + GA4) so a
per-page refresh only hits what that page needs.

## 7. What is intentionally NOT here (see PRODUCT_CONTEXT.md "Out of scope")

No multi-tenancy, no websockets, no daily cron (refresh is on-demand by design), no
customer-facing surface.
