# FuseHealth — SEO & Ads Intelligence Dashboard

An internal dashboard that pulls SEO, analytics, and ads data from Google Search Console,
Google Analytics, PageSpeed, and keyword/backlink tools into one place, stores it locally, and
presents it as decision-focused pages (opportunities, anomalies, health scores) for a small team.

**Stack:** Django 6 · HTMX · Tailwind (CDN) · Plotly · SQLAlchemy (analytics DB) · Python 3.11+

> The data-first contract: pages **only read from the database** and open instantly. Fetching from
> external APIs happens on a **Refresh**, which writes to the DB and updates the UI. See
> [`CLAUDE.md`](CLAUDE.md) and the `.claude/` reference docs for architecture details.

---

## 1. Prerequisites

- **Python 3.11+** (developed on 3.13)
- A working **`.env`** file (copy from [`.env.example`](.env.example) and fill in credentials)

---

## 2. Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your environment file and fill in secrets
#    (Windows: copy .env.example .env)
cp .env.example .env

# 4. Set up the Django database
python manage.py migrate

# 5. Create the login users (founder / seo / ads)
python manage.py seed_users

# 6. Run the development server
python manage.py runserver
```

Then open **http://127.0.0.1:8000/** and log in.

The default settings module is `config.settings.local` (already set in `manage.py`).

---

## 3. The two databases

This project uses **two** databases on purpose:

| Database | Engine | Holds |
|---|---|---|
| `django_internal.db` | Django ORM | Users, roles, sync logs, refresh runs, team insights |
| `fusehealth.db` (under `data/`) | SQLAlchemy | All analytics data — GSC, GA4, keywords, pages, anomalies, etc. |

`migrate` only touches `django_internal.db`. The analytics DB is populated by **refreshing data**
(below). Both are git-ignored.

---

## 4. Logging in & roles

`seed_users` creates three accounts (passwords come from `.env`, with a temporary fallback printed
as a warning if unset):

- **founder** — sees every page
- **seo** — SEO, keywords, pages, positioning, backlinks, alerts
- **ads** — ads, overview, alerts

---

## 5. Refreshing data

Pages read from the database, so a fresh checkout shows whatever data is already in `fusehealth.db`.
To pull the latest:

- **In the app:** use **Refresh All** (top bar) or a page's own refresh button. A live progress bar
  shows each connector running. This is the normal path.
- Each refresh also rebuilds aggregates, **detects traffic anomalies**, and **derives technical
  issues** (404s, long URLs, redirects) automatically — no external API needed for those.

> **PageSpeed note:** page-speed scores require the **PageSpeed Insights API** to be enabled *and*
> the Google API key to allow it (key → *API restrictions*). If speed columns are empty, that's the
> cause — enable it, then refresh.

---

## 6. Project layout

```
fusehealth/
├── config/              # Django project (settings split: base / local / production)
├── apps/
│   ├── accounts/        # auth, roles, seed_users
│   ├── dashboard/       # the pages (views, templates, services)
│   └── sync/            # refresh endpoints + sync logs
├── pipeline/            # the proven data layer (connectors, db, services, utils)
├── templates/           # base, partials, components, per-page templates
├── static/              # CSS
├── data/                # fusehealth.db (analytics) — git-ignored
├── .claude/             # project reference docs (architecture, database, API, design)
└── manage.py
```

For "where does X live?" see [`.claude/FILE_INDEX.md`](.claude/FILE_INDEX.md).

---

## 7. Production

Deployment (VPS: Nginx + Gunicorn + systemd, `collectstatic`, SSL) is tracked in
[`.claude/checklist.md`](.claude/checklist.md) under Phase 7. Use `config.settings.production` and
set real environment variables there.

---

## 8. Troubleshooting

| Symptom | Likely cause |
|---|---|
| A page is empty for the **7-day** range | The data may be a few days old; try **30d**. Periods anchor to the latest available data. |
| **Speed** columns are blank | PageSpeed Insights API not enabled / key restricted (see §5). |
| **Ads / Backlinks** show empty states | Those accounts aren't connected yet (expected). |
| Login fails | Run `python manage.py seed_users` and check `.env` passwords. |
