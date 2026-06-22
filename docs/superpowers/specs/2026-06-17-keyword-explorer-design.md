# Keyword Explorer — Design Spec

> Status: approved 2026-06-17. A standalone keyword-research section on the existing
> Keywords page. Does **not** touch existing keyword-tracking functionality.

## Goal

Let internal users research arbitrary keywords on demand: type one keyword or many
(comma-separated), Search, and get a sortable table of metrics from DataForSEO. Users can
select rows and Download (CSV), Copy, or Save them to a dedicated research list.

## Architecture fit (the data-first contract)

The iron rule forbids calling an external API from a **page-rendering** view. The explorer's
API call happens on an **explicit user action** (Search) through a dedicated endpoint — the
same shape as the Refresh path, which is allowed. Therefore:

- The `keywords` page render stays **DB-only** (tracked-keyword intelligence + saved list).
- Only the new `keywords/explore/`, `keywords/save/`, `keywords/saved/delete/` endpoints
  touch the API / write the DB, and only when the user acts.
- No existing tracking code (`keywords.txt`, `keyword_rankings`, sync engine) is modified.

## Data source — one DataForSEO call

Add a read-only method to the **existing** `DataForSEOKeywordsConnector`:

```
lookup_keywords(keywords: list[str], location_name: str = "United States") -> dict
```

- Calls DataForSEO Labs `POST /v3/dataforseo_labs/google/keyword_overview/live`
  (accepts up to 700 keywords/call; we batch defensively at 700).
- Returns **all 8 columns from one endpoint**, parsed defensively with `.get()`:
  | Column | Source field |
  |---|---|
  | Keyword | `keyword` |
  | Search Volume | `keyword_info.search_volume` |
  | Keyword Difficulty | `keyword_properties.keyword_difficulty` |
  | CPC | `keyword_info.cpc` |
  | Competition | `keyword_info.competition_level` (fallback: `keyword_info.competition`) |
  | Search Intent | `search_intent_info.main_intent` |
  | SERP Features | `serp_info.serp_item_types` (list) |
  | Country / Location | the requested `location_name` |
- **Does not** write to the DB and **does not** read `keywords.txt` — fully separate from the
  tracking `fetch()`/`sync()` path, which is left untouched.
- Return shape: `{"status": "ok"|"error", "rows": [ {…8 fields…}, … ],
  "no_data": [kw, …], "location": location_name, "error": str|None}`.
  - `rows` = keywords DataForSEO returned data for.
  - `no_data` = requested keywords with no result (so the UI can note them while still showing
    the successful ones).
  - Whole-call failure (missing creds, negative balance, network/HTTP error) → `status="error"`
    with a human-readable `error`; raised exceptions are caught at the view layer.

Note: balance is currently `BALANCE_NEGATIVE`, so live verification is deferred. Field paths
follow DataForSEO Labs `keyword_overview` docs and are covered by mocked unit tests.

## Persistence — new `SavedKeyword` table

New SQLAlchemy analytics table (in `fusehealth.db`), **self-provisioned** via `ensure_tables`
on first use — no Django migration, identical pattern to `AIKeywordData` /
`CompetitorKeywordRanking`.

`saved_keywords` columns:
- `id` PK
- `site_id` (indexed) — research is site-scoped, shared across the 2–3 users
- `keyword` (indexed)
- `location` (the DataForSEO `location_name`)
- `search_volume` (Integer, nullable)
- `keyword_difficulty` (Float, nullable)
- `cpc` (Float, nullable)
- `competition` (String, nullable) — stores the level/label
- `intent` (String, nullable)
- `serp_features` (Text, nullable) — comma-joined list
- `saved_at` (DateTime, server default now)
- Unique on `(site_id, keyword, location)` → re-saving updates in place.

Writer: `upsert_saved_keywords(session, records, site_id)` following the existing batched
`on_conflict_do_update` pattern. Delete handled in the service.

## Service — `pipeline/services/saved_keyword_service.py`

- `list_saved_keywords(site_id) -> list[dict]`
- `save_keywords(site_id, rows: list[dict]) -> int`
- `delete_saved_keyword(site_id, keyword, location) -> bool`

All read/write only the `saved_keywords` table; `ensure_tables` guards first use.

## Views (`apps/dashboard/views.py`) & URLs

- `keywords()` — **extended**, still DB-only: also loads `saved_keywords` (service) and a
  static `locations` list (default "United States") into the context.
- `keyword_explorer_search` — `POST keywords/explore/`, `@role_required("keywords")`.
  Parses `keywords` (split on comma, trim, dedupe, drop blanks) + `location`. Empty → validation
  message partial. Calls `connector.lookup_keywords(...)` (wrapped in try/except). Renders
  `dashboard/partials/_explorer_results.html`.
- `save_keywords` — `POST keywords/save/`, `@role_required("keywords")`. Receives selected rows
  (JSON body), upserts via service, returns refreshed `dashboard/partials/_saved_keywords.html`.
- `delete_saved_keyword` — `POST keywords/saved/delete/`, `@role_required("keywords")`. Removes
  one (keyword+location), returns refreshed saved panel.

CSRF: HTMX/fetch POSTs include the CSRF token (per existing base.html setup).

## Templates

- `templates/dashboard/keywords.html` — add a **Keyword Explorer** card (matches existing
  slate/brand card styling): heading, a text input for comma-separated keywords, a location
  `<select>`, a Search button (`hx-post` to explore, `hx-target` results container,
  `hx-indicator` spinner for the loading state), the results container, and the Saved Keywords
  panel (`{% include _saved_keywords.html %}`).
- `templates/dashboard/partials/_explorer_results.html` — **new**. Alpine component initialised
  from a `json_script` rows blob. Renders the 8-column table with a leading checkbox column.
  - **Sort**: Volume / KD / CPC headers toggle asc/desc client-side (Alpine sorts the array).
  - **Selection**: per-row + select-all checkboxes tracked in Alpine.
  - **Bulk bar** (visible when ≥1 selected): Download CSV + Copy (TSV) built client-side over
    selected rows (no re-fetch, no API cost); Save posts selected rows JSON to `keywords/save/`.
  - **Error state**: if `status == "error"`, render an inline red banner with the message.
  - **No-data note**: if `no_data` non-empty, a small note lists those keywords.
  - **Empty input**: friendly validation message.
- `templates/dashboard/partials/_saved_keywords.html` — **new**. The saved-keywords panel
  (table of saved rows + per-row remove button posting to delete). Swapped on save/delete.

## Data flow

1. **Page load** — `keywords()` reads tracked intelligence (unchanged) + saved list + locations.
   No API call.
2. **Search** — HTMX `POST keywords/explore/` → parse → `lookup_keywords` → one Labs call →
   `_explorer_results.html` swapped into the results container; spinner via `hx-indicator`.
3. **Select → Download/Copy** — pure client-side over selected rows.
4. **Select → Save** — `POST keywords/save/` → `upsert_saved_keywords` → refreshed saved panel
   swapped in.
5. **Remove saved** — `POST keywords/saved/delete/` → delete → refreshed saved panel.

## Error handling

- Missing creds / negative balance / network / HTTP error → connector returns
  `status="error"` (or view catches exception) → inline banner, nothing crashes.
- Per-keyword: keywords with no DataForSEO result go into `no_data`; successful keywords still
  render (partial-failure requirement satisfied).
- Empty / whitespace-only input → validation message, no API call.

## Testing

- **Connector**: `lookup_keywords` parses a mocked `keyword_overview` response into the 8 fields;
  handles missing nested keys; splits returned vs `no_data`; error path on raised request.
- **Service + writer**: save → list → delete round-trip against a temp SQLite DB; re-save
  updates in place (unique constraint).
- **Views**: explore endpoint with the connector mocked renders rows + handles the error banner;
  save endpoint persists and returns the panel.
- Tests live under `pipeline/db/tests/` (writer/service) and Django test for views, matching the
  existing layout.

## Files touched

| File | Change |
|---|---|
| `pipeline/db/schema.py` | + `SavedKeyword` model |
| `pipeline/db/writer.py` | + `upsert_saved_keywords` |
| `pipeline/connectors/dataforseo_keywords.py` | + `lookup_keywords()` (read-only) |
| `pipeline/services/saved_keyword_service.py` | **new** — list/save/delete |
| `apps/dashboard/views.py` | extend `keywords()`; + explore/save/delete views |
| `apps/dashboard/urls.py` | + 3 routes |
| `templates/dashboard/keywords.html` | + Keyword Explorer section |
| `templates/dashboard/partials/_explorer_results.html` | **new** |
| `templates/dashboard/partials/_saved_keywords.html` | **new** |
| `.claude/FILE_INDEX.md`, `.claude/API_REFERENCE.md` | doc updates |

## Out of scope (YAGNI)

- Named/multiple saved lists (single per-site list only).
- Server-side sorting or pagination (client-side sort over a single search result is enough).
- Persisting raw search history beyond what the user explicitly Saves.
- Adding research keywords into the tracking pipeline.
