# FuseHealth — Coding Standards (SKILLS)

*How to write code in this project. Read before writing any Python or template. This is v1 —
sections marked (expanded: Phase N) get filled in once that layer is built. When you establish a
new pattern, add it here so the next session matches it.*

## Golden rules (the non-negotiables, with reasons)

1. **No external API call in a page-render view.** Views read the DB and return HTML. API calls
   happen only inside the sync engine (`apps/sync`). Reason: the DB-first contract — pages must
   be instant and must not depend on rate-limited, minutes-long API calls.
2. **Secrets come from the environment, never the code.** Read via `settings` (which reads
   `.env`/env vars). Never hardcode a key; never log a secret; never commit `.env`.
3. **Reuse the pipeline, don't rewrite it.** The connectors/services/db logic is proven. Import
   and call it; only refine it when a task genuinely requires it.
4. **One concern per file.** A view module renders; a service computes; a connector fetches.
   Don't mix fetching into a view or business logic into a template.

## Python style

- **Type hints** on every function signature. **Docstrings** on every public function/connector
  `fetch()` — state what it returns and what it raises.
- **Function length:** aim under ~30 lines; if longer, extract a helper. You reason better about
  small focused functions, and so will the next session.
- **Comments explain WHY, not WHAT.** The code already says what; comment the non-obvious reason.
- **Error messages are specific:** include the component, the operation, and the actual cause.
  Never `raise Exception("error")`.
  ```python
  # good
  raise ValueError(f"[{self.name}] missing env var DATAFORSEO_LOGIN — check .env")
  # bad
  raise ValueError("missing login")
  ```

## Django conventions

- **Settings:** put shared config in `config/settings/base.py`; environment-specific overrides in
  `local.py` / `production.py`. Read values with the `env()` helper in `base.py`.
- **Apps:** code lives under `apps/<name>/`; app configs use `name = "apps.<name>"` with a short
  `label`. Reference models/urls by the `label`.
- **Internal data** (users, sync_log) uses the **Django ORM** on the `default` DB.
  **Analytics data** uses the reused **SQLAlchemy** pipeline on `fusehealth.db` — do not create
  Django models for analytics tables.
- **URLs are namespaced** per app (e.g. `dashboard:overview`); use `{% url %}` / `reverse()`,
  never hardcode paths.
- **Every view that shows data is behind login**, and behind `@role_required` where the role
  matters (see `apps/accounts`, Phase 2).

## Templates, HTMX & charts

**`DESIGN.md` is the authority for all visual decisions** (colors, type, spacing, components,
Plotly theme). Never introduce an off-palette color or a second font — use the brand tokens
registered in `base.html`. The patterns:

- Every page **extends `base.html`** and fills its blocks (`page_title`, `page_subtitle`,
  `topbar_actions`, `content`, `body_extra`). Never hand-roll a page shell.
- Reusable pieces live in `templates/components/` (`stat_card`, `refresh_button`,
  `sync_progress`); shared chrome in `templates/partials/` (`_sidebar`, `_topbar`).
- Sidebar nav data comes from the `navigation` context processor — add nav/badges there, once.
- **Tailwind via CDN**, **HTMX** included once in `base.html`. No Node build step.
- A page = a full template extending `base.html` + small **partials** for the HTMX-swappable
  regions (a chart, a table, the progress bar).
- **Filters/refresh use HTMX**: `hx-post`/`hx-get` returns just the partial HTML for the changed
  region (`hx-target`), never a full-page reload.
- **Progress bar** polls the status endpoint: `hx-trigger="every 2s" hx-get="/sync/status/"`,
  and stops polling when the sync row reports done.
- **Plotly** charts are serialized to JSON in the view (`PlotlyJSONEncoder`) and rendered
  client-side with `Plotly.newPlot` — keep heavy rendering off the server.

## Connectors & sync (expanded: Phase 4)

- Every connector inherits `BaseConnector` (retry + logging built in) and writes a `sync_log`
  row: start time, finish time, records fetched, error (if any).
- The sync engine maps each page to its connectors so a per-page refresh hits only what's needed.
- Connectors **upsert** (never blind insert) so re-running a sync doesn't duplicate rows.

## Definition of done (per task)

- Code runs; `python manage.py check` is clean.
- New/changed files reflected in `.claude/FILE_INDEX.md`.
- No secret in the diff (`.env` untouched, no key in any `.py`).
- For a page: it loads from the DB with real data, and its refresh button updates that data.
