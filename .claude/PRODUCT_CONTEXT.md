# FuseHealth — Product Context

*The "why" of the project. Read this when you're unsure what we're building or why a decision
was made. This file is the single source of truth for the product contract and scope.*

## What this is

An **internal SEO + Ads intelligence dashboard** for the FuseHealth team. It pulls marketing
and search data from ~12 external APIs, stores it in a local database, and presents it as a
clean, fast, branded dashboard. It is **not** a SaaS product and has **no external customers**.

## Who uses it

2–3 internal users, by role:

| Role | Sees |
|---|---|
| `founder` | Everything |
| `seo` | SEO, Keywords, Pages, Backlinks, Positioning, Insights |
| `ads` | Ads Performance |

## The core experience (the product contract)

The dashboard is **database-first**. The user always looks at saved data; fresh data is pulled
only on demand.

- **On load:** every page reads from the database and renders instantly. No API calls.
- **Refresh All:** a global button fetches *all* APIs → writes to DB → UI updates.
- **Per-page refresh:** each page has its own button that fetches *only that page's* APIs.
- **Live progress:** during any refresh, a progress bar shows each API completing in real time
  (HTMX polls a sync-status endpoint backed by the `sync_log` table).
- **Between refreshes:** the user keeps seeing the last saved data.

Why this shape: the external APIs are rate-limited and a full sync takes minutes. Pulling them
on page load would make the dashboard slow, flickery, and quota-hungry. Decoupling "view" from
"fetch" is the central design decision of the whole product.

## The stack

| Layer | Technology |
|---|---|
| UI | Django templates + **Tailwind CSS (CDN)** + **HTMX** |
| App server | Django (Gunicorn in production) |
| Background sync | On-demand sync engine triggered by the Refresh buttons; live progress via HTMX polling |
| Analytics DB | `fusehealth.db` (SQLite, SQLAlchemy) |
| Auth / sessions / logs DB | `django_internal.db` (Django ORM) |
| Charts | Plotly (served as JSON, rendered client-side) |
| Deployment | VPS — Nginx + Gunicorn + systemd |

## What changes vs. the Streamlit MVP

| MVP (Streamlit) | Production (Django) |
|---|---|
| `app.py` + `pages/*.py` | Django views + HTML templates |
| `worker.py` (APScheduler, daily cron) | On-demand sync engine triggered by Refresh buttons |
| Streamlit Cloud | VPS (Nginx + Gunicorn + systemd) |
| Whole-page reruns on every click | HTMX partial swaps — only the changed widget reloads |
| Rigid vertical layout | Custom Tailwind design system |

## What stays the same (reuse, do not rewrite)

The proven data pipeline is reused. It is copied into `fusehealth/pipeline/` in Phase 4:

- **Connectors** (`connectors/*.py`) — the API integration logic
- **Services** (`services/*.py`) — aggregation, anomaly, insight, refresh, site
- **DB layer** (`db/*.py`) — SQLAlchemy schema, queries, writers (may be *refined* in Phase 3,
  not thrown away)
- **Utils** (`utils/*.py`) — auth, retry, logger, date helpers, security

The migration replaces the **UI and the trigger mechanism** — not the data pipeline.

## Out of scope (YAGNI — do not build these)

- Multi-tenancy / per-client logins
- Public sign-up, billing, or any customer-facing surface
- Real-time websockets (HTMX polling is sufficient for 2–3 users)
- A native mobile app (responsive web is enough)
