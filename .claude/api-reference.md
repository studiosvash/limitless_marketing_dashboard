# API Reference

> Reverse-engineered from `apps/api/urls.py`, `apps/api/views.py`, the service layer, and
> `pipeline/connectors/`. Every endpoint, field, and status code below was read out of the code.

---

## 1. Conventions

**Base path:** all JSON endpoints live under `/api/`. Note that URL patterns have **no trailing
slash** (`/api/projects`, not `/api/projects/`).

**Authentication:** `Authorization: Bearer <token>` where the token is a DRF
`rest_framework.authtoken` key. The class is `apps.api.authentication.BearerTokenAuthentication`
— stock `TokenAuthentication` with `keyword = "Bearer"`. Session cookies also authenticate,
because the SPA is served from the same origin with `credentials: 'include'`.

**Default permission:** `IsAuthenticated` (set globally in `REST_FRAMEWORK`). Two endpoints
override this to be fully public (§6).

**The `login_not_required` requirement.** `LoginRequiredMiddleware` is active project-wide and
runs *before* DRF. Any API view that should answer a token-only request must be decorated:

```python
@method_decorator(login_not_required, name="dispatch")
class MyView(APIView): ...
```

Without it, an unauthenticated request is redirected (302) to the login page instead of getting
DRF's 401. **Exactly one view is missing this decorator** — `ProjectDetailView`
(`DELETE /api/projects/<slug>`) — so it only works for a caller holding a valid session cookie.

**Project identity.** The `<slug>` path segment is `Site.slug` (e.g. `fusehealth`), not the
integer primary key and not the domain. `resolve_project_or_404(slug)` looks the row up and
raises `Http404` on a miss; every slug-taking endpoint returns **404** for an unknown project.
Internally the slug is immediately converted to `Site.site_url`, which is the `site_id` string
used as the join key across both databases.

**Date ranges.** Endpoints marked *range-aware* accept `?range=7d|28d|90d` (default `28d`,
validated by `OverviewQuerySerializer`; any other value is a **400**). `30d` is still accepted
from cached SPA builds and bookmarked URLs and resolves to the *same* 28-day window, never a
second slightly-different one — 28 matches Search Console's own 7/28/90 choices, so one number
appears on both screens. Periods are anchored to
`latest_data_anchor(site_id)` so a stale dataset never yields an empty window.

That anchor is **`newest day with Search Console data + 1 day`**, or today when there is none.
Both halves were wrong until 2026-08-18 and the corrections are worth knowing:

* **It reads GSC's own rows, not any row.** `seo_daily` is shared — the `ga4` connector writes
  the analytics columns and leaves clicks/impressions/ctr/avg_position at `0`, and GA4's window
  runs to *yesterday* while `gsc_safe_range` stops at *today − 3*. An unfiltered `MAX(date)`
  therefore anchored a Search Console window on a day Search Console had no data for. On
  premierstaff.com the 7-day window ran 26 Jul – 1 Aug while `seo_daily_totals` stopped on
  31 Jul: a "7-day" figure built from six days, drifting further with every GA4-only sync. The
  fix is the predicate `impressions > 0` — exact, not a heuristic, because the Search Analytics
  API only returns a row for a page that was served. `gsc._get_last_synced_date` already
  applied it to its own cursor for the same reason. `seo_daily_totals` needs no predicate: the
  `gsc` connector is its only writer.
* **The `+ 1` cancels `get_period_dates`' `anchor − 1`.** That `− 1` guards against Search
  Console's most recent day being partial — true of *today*, not of this anchor, since
  `gsc_safe_range` already ends at today − 3 and only settled days are ever stored. The two
  margins stacked and the newest real day fell outside every window meant to show it.
  `latest_ranking_anchor` resolves the identical mismatch identically, for rank measurements.

So the current window now **ends on the newest day of Search Console data, inclusive.** The
fallback stays *today*, never today + 1 — an anchor of tomorrow would put the window end in the
future.

`GET /overview` returns the window it used as **`window: {start, end}`** (ISO dates, inclusive)
and the page prints it — "Showing 25 – 31 Jul 2026". Without it a window that has drifted weeks
behind still renders a complete, plausible week, and the only visible symptom is that it
disagrees with Search Console — which reads as "the dashboard is wrong" rather than "the data
is old". That is exactly how the 2026-08-18 investigation started.

⚠️ **This window is not Search Console's own "last 7 days".** `gsc_safe_range` deliberately stops
at *today − 3* (Google keeps revising a day for ~2 days after first publishing it), so a freshly
synced 7-day window is `today−9 … today−3` where Search Console's UI shows `today−8 … today−2`.
The two screens are one day apart on both ends **by design**, and their totals will differ
accordingly. Do not "fix" this by comparing the two numbers — compare the dates first.

**Errors.** The API returns:

| Status | When |
|---|---|
| 200 | Success |
| 201 | `POST /api/projects` |
| 204 | `DELETE /api/projects/<slug>`, `DELETE /api/projects/<slug>/data` |
| 400 | Validation failure, unknown action, or a group the backend refuses to persist. Body: `{"detail": "..."}` |
| 401 | Missing/invalid token on a `login_not_required` view |
| 403 | Role check failed. Body: `{"detail": "..."}` |
| 404 | Unknown project slug, unknown invitation, unknown user, or unknown list/prompt |
| 500 | Unhandled exception in a mutation path. Body: `{"detail": "..."}` or `{"error": "..."}` |

Note the inconsistency: most errors use `detail`, but `DELETE /api/projects/<slug>/data` uses
`error`. The frontend's `http()` helper reads `detail` only.

**Roles used by permission checks** (string literals on `UserProfile.role`):

```python
check_owner_admin(user)  # False only when profile.role == "Analyst"
check_owner_only(user)   # True only when profile.role == "Owner"
```

Both functions return **`True` for an unauthenticated user** (`if not user.is_authenticated:
return True`) and both hard-allow `user.id == 1` or a username of `founder`/`owner`. This means
role enforcement is effectively bypassed for anonymous callers — it is a UI-level guard, not a
security boundary.

---

## 2. Non-API routes

| Path | View | Auth | Notes |
|---|---|---|---|
| `/` | `apps.dashboard.spa_views.spa_index` | `@login_required` | Serves the SPA. Expands `#include` directives, injects the auth bootstrap script. Named `spa`. |
| `/login/` | `apps.accounts.views.LoginView` | public | Branded Django login. Accepts username **or** email. |
| `/logout/` | `apps.accounts.views.LogoutView` | public, CSRF-exempt | Logs out, redirects to `/login/`. |
| `/accept-invite/?token=…` | `apps.accounts.views.AcceptInviteView` | public | Where the invitation email lands. Shows the invited email read-only (it **is** the username) and asks only for a password; on success signs the new user in and redirects to `/`. |
| `/password-reset/`, `/password-reset/sent/`, `/reset/<uidb64>/<token>/`, `/reset/done/` | `apps.accounts.views.PasswordReset*View` | public | Django's four-step reset, branded. Reached from *Forgot password?* on the login form. |
| `/admin/` | Django admin | staff | Registers `User`+`UserProfile` inline, `Insight`, `SyncLog`, `RefreshRun`. |
| `/app/` | `RedirectView` | — | Redirects to `/` (legacy bookmark support). |

---

## 3. Projects

### `GET /api/ping`

Smoke test. Auth: Bearer. Returns `{"ok": true}`.

### `GET /api/projects`

Lists active sites (`Site.is_active == 1`), ordered by `site_url`.

**Response** — array of:

```json
[{
  "id": "fusehealth",
  "domain": "fusehealth.com",
  "name": "FuseHealth",
  "vertical": "Healthcare",
  "location": "United States",
  "tracked_keywords_count": 42,
  "avg_position": 12.4,
  "visibility": 1.6,
  "improved_count": 5,
  "declined_count": 2,
  "last_updated": "2 days ago",
  "syncing": false
}]
```

`id` is the slug. `domain` is `_bare_domain(site.site_url)` (scheme, `sc-domain:` prefix and
trailing slash stripped). The stats fields come from `ProjectSerializer._pos_summary()`,
which caches its result on the instance and degrades to zeros + `"No sync yet"` on any
exception. `last_updated` is a human string: `"Today"`, `"Yesterday"`, `"N days ago"`, or
`"No sync yet"` — and it means **when this project itself last completed a positioning run**
(`RefreshRun` by `site_pk`, scopes `positions`/`positions_new`/`all`), falling back to the
newest measurement date only for legacy runs with no pk. It used to be the measurement date
alone, and `dataforseo_serp` stamps rows `yesterday()`, so a fetch finished two minutes ago
read "Yesterday". `syncing` is true while a run is in flight **for this project** (again by
`site_pk` — a sibling project's run on the same domain does not light it); the Position
Tracking list renders it as "Fetching…".

**Query params:** `range` — `7d` | `28d` | `90d`, default `28d`. Optional; a caller that only
wants the project list can omit it.

**The window is the same one `GET /positions` renders** (changed 2026-08-10, completed
2026-08-12): a window anchored on `views.latest_ranking_anchor` — this project's newest
`keyword_rankings` date, in its own location — falling back to `date.today()` only when the
project has never been measured.

Two halves to that, fixed separately. The **anchor** used to be a fixed rolling 28 days ending
*today*, with no reference to when the project was actually measured, so a project last synced
40 days ago had no measurement inside its own window: the list row said `—` ("never captured")
beside a workspace reporting a real score for the same project. The **length** used to be
hardcoded `28d` here while `ProjectPositionsView` honours `?range=`, so picking 7d or 90d moved
the workspace figure and left this row on its 28-day reading — one project, two percentages,
neither labelled with its window. `ProjectListCreateView.get` now passes the caller's range to
`ProjectSerializer` through `context={"range": ...}`, and the SPA sends it from `boot()` and
re-reads the list in `setRange()` (`App.reloadProjects`). Every other `/api/projects` re-read in
the SPA (project create / edit / delete, keywords sent to tracking) goes through
`reloadProjects()` for the same reason — a bare re-read would silently snap the list back to 28d.

`visibility` is Semrush's Visibility, reproduced (0–100, 1 dp), computed in
`_get_ranking_distribution`: each tracked keyword earns `_SEMRUSH_CREDIT[position]` — a curve
**measured from Semrush's own per-keyword contributions** for the team's real campaign
(2026-08-21; #1 = 1.0, #2 = 0.343, #49 still 0.014, 0 past #100; provenance and validation —
reproduces Semrush's reported 21.83 to the decimal — in the constant's comment; same values in
the SPA's `buildVisibilityScores`) — divided by a perfect #1 on **every** tracked keyword,
equal weight, no volume. **A keyword's position is its best placement including SERP
features**: Local Pack slot, AI Overview citation slot (from `serp_feature_rankings`) — a #1
AIO citation with no organic ranking earns the full 1.0, exactly as Semrush counts it.
Keywords with no ranking anywhere earn 0 but stay in the denominator. **Snapshot, not window
average** (decision 2026-08-13, matching Semrush):
each keyword contributes its **latest measurement** (per-keyword max date ≤ window end — not
one latest capture date, which a `positions_new` incremental sync would break). The range
selector moves the distribution buckets and movement counts, not this number. `null` means
"never captured in the window" (UI shows `—`); `0.0` means "captured, ranks nowhere" — a real
number. Never derive visibility from `avg_position`: it averages ranked keywords only, which
once made 1 branded keyword at #2 out of 48 read as 82%.

**Related frontend:** topbar site selector, Position Tracking project list.

### `POST /api/projects`

Creates a site, verifies Search Console access, and kicks off a full sync.

**Request**

```json
{ "domain": "example.com", "name": "Example Co.", "vertical": "Health", "location": "United States",
  "gsc_property": "sc-domain:example.com", "ga4_property_id": "123456789",
  "dataforseo_target_domain": "example.com" }
```

`domain` is required (max 255). Everything else is optional. `gsc_property`,
`ga4_property_id`, `dataforseo_target_domain` are collected by the topbar's Add-domain modal's
Connections step (its "Check all connections" button hits `POST /api/connection-check` first,
below) — added because the site used to always be created with `gsc_property` defaulted to the
bare domain (which Search Console reads as a URL-prefix property, not the `sc-domain:` property
most accounts actually own) and `ga4_property_id = NULL`, so a new site's GA4-backed pages
stayed empty until someone visited Settings. The modal's "Skip for now" path omits all three
and still creates the site — that's a supported, honest choice, not an error state.

**Behaviour**

1. `add_site()` **normalises `domain` before storing it**:
   `pipeline/utils/site_ids.normalize_domain()` strips the scheme, `sc-domain:`, a leading
   `www.`, any path, port, trailing dot and trailing slash, and lowercases. So
   `https://www.example.com/`, `http://example.com`, `www.example.com` and `example.com` all
   store `sites.site_url = "example.com"` — one project, whichever the user typed. Input with no
   readable host (`""`, `"https://"`) raises `ValueError` → **400** rather than storing an empty
   join key.
2. The duplicate check compares that same normalised form against every existing row, so a
   second spelling of an already-registered site raises `ValueError` → **400** with
   `{"detail": "Site already exists: <the stored spelling>"}`. This is the fix for the bug
   where `premierstaff.com` and `www.premierstaff.com` were both accepted and one site became
   two projects.
3. The row is inserted with a unique slug from `slugify_unique()`. Any of the three credential
   fields that were sent are stored as given; omitted ones fall back to the same defaults as
   before (`gsc_property` → bare domain, `ga4_property_id` → `NULL`, `dataforseo_target_domain`
   → bare domain). **`gsc_property` is never normalised** — it is a Search Console property
   identifier and the account may genuinely own the `https://www.example.com/` URL-prefix
   property.
4. `resolve_gsc_property()` is called against whichever `gsc_property` was stored; on
   `ValueError` the response carries `gsc_connected: false`. Any other exception also reports
   `false` — it used to assume `true` on any non-`ValueError` exception, which hid the one case
   this check exists to catch (a real connectivity problem that doesn't happen to raise
   `ValueError`) behind a false "connected" claim.
5. `start_sync_run(site_url, "all")` is fired, where `site_url` is read back off the **stored**
   row, not the request body — passing the raw typed string would file the whole first sync
   under a key no page ever reads. Failure is swallowed and `sync_task_id` is `null`: a sync
   problem never blocks site creation.

**Response `201`** — the `ProjectSerializer` body plus:

```json
{ "gsc_connected": true, "sync_task_id": 17 }
```

**Related frontend:** topbar "Add a site" modal (`toggleAddSite`/`addSiteNext`/`addSiteCheck`/
`addSiteSubmit`/`addSiteSkip` in `app.js`); Position Tracking "Create SEO Project" wizard.

### `POST /api/connection-check`

Live-probes GSC / GA4 / DataForSEO (and optionally PageSpeed/OpenAI/Google Ads) for a domain —
**before** a `Site` row necessarily exists, so the Add-domain modal can validate credentials
pre-creation. A sanctioned live-lookup exception to the database-first contract (same category
as `/api/research`): it only ever runs because a human pressed "Check all connections" or "Test
connection".

**Request**

```json
{ "domain": "example.com", "gsc_property": "sc-domain:example.com",
  "ga4_property_id": "123456789", "dataforseo_target": "example.com",
  "include_optional": false }
```

Only `domain` is required. `include_optional: true` (the default) also probes PageSpeed,
OpenAI and Google Ads presence/validity; the Add-domain modal and Settings' "Test connection"
button pass `false` to keep the check to the three credentials they actually collect.

**Response**

```json
{
  "ok": true,
  "checks": [
    {"id": "gsc", "label": "Google Search Console", "state": "ok",
     "detail": "Verified property: sc-domain:example.com",
     "options": ["sc-domain:example.com", "https://other-verified-property.com/"],
     "resolved": "sc-domain:example.com"},
    {"id": "ga4", "label": "Google Analytics 4", "state": "ok",
     "detail": "Property 123456789 readable — 42 sessions in the last 7 days.",
     "resolved": "123456789"},
    {"id": "dataforseo", "label": "DataForSEO", "state": "ok",
     "detail": "Credentials valid — balance $38.84."}
  ]
}
```

`state` is one of `ok` / `fail` / `absent` (not configured — not a failure, since skipping GA4
is a legitimate choice) / `unknown` (configured but not cheaply verifiable, e.g. PageSpeed,
which would cost a real Lighthouse run to probe). `ok` in the top-level response covers only
`gsc`/`ga4`/`dataforseo` and only counts a hard `fail`.

`checks[].options` (GSC only) lists every property the connected Google account can verify-list
— the Add-domain modal renders it as a dropdown so the property can't be mistyped. `resolved`
is the exact value that would be stored if the site were created right now.

Backed by `apps/dashboard/services/connection_check_service.py`. Never raises — every probe is
wrapped, because the entire point of this endpoint is to survive the failures it describes.
Also has a CLI twin: `python manage.py check_connections [<slug>]`.

### `POST /api/projects/<slug>/ads-credentials/test`

Live-probes a Google Ads / Meta Ads credential — either freshly typed into the Settings
form (not yet saved) or the credential already stored for this site (`useSaved: true`).
**Permission:** `check_owner_admin` → **403** for an `Analyst` (same gate as the settings
PUT, since this spends a real API call against the platform's quota).

**Request**

```json
{ "platform": "google_ads", "developer_token": "...", "customer_id": "1234567890" }
```
or
```json
{ "platform": "meta_ads", "useSaved": true }
```

**Response:** `{ "ok": true, "detail": "Verified — customer 1234567890 is reachable." }`

Backed by `apps/dashboard/services/connection_check_service.py::test_google_ads_credential`
/ `test_meta_ads_credential`, which delegate to `pipeline/connectors/{google_ads,meta}.py`'s
`probe_credential()`. Every result (pass or fail) is recorded as `last_test` on the site's
stored `adsCredentials` entry via `ads_credentials.record_test_result`, so it survives a
page reload.

### `DELETE /api/projects/<slug>`

Hard-deletes the `Site` row (`delete_site(site.id, hard=True)`). Analytics rows keyed on the old
`site_id` string are **not** removed. Returns **204**.

⚠️ This view lacks `@login_not_required`, so a token-only call is 302'd to the login page. It
works from the SPA, which sends a session cookie.

The caller — Position Tracking's workspace delete button — used to invoke
`window.FuseAPI.delete(...)`, which does not exist (the transport exposes `del`), so the button
threw a `TypeError`. Fixed 2026-07; it now uses the real transport method and surfaces a failure
via `.catch()` instead of dying silently.

### `DELETE /api/projects/<slug>/data`

Wipes analytics data for the project without deleting the project. Executes
`DELETE FROM <table> WHERE site_id = <site_url>` across 19 tables: `SEODaily`, `KeywordRanking`,
`Page`, `AdMetricDaily`, `Backlink`, `TechnicalIssue`, `PageSpeed`, `IndexingStatus`,
`SEOAggregate`, `AISummary`, `Anomaly`, `ComparativeMetrics`, `CompetitorKeywordRanking`,
`TrackedCompetitor`, `AIKeywordData`, `SavedKeyword`, `MetricForecast`, `KeywordOpportunity`,
`RiskSignal`.

Returns **204**, or **500** with `{"error": "..."}`.

Its caller `app.js::clearData()` used to read `this.props.ctx.route.params.id`, which does not
exist in this runtime, so the handler threw before ever reaching the API. Fixed 2026-07: it reads
`this.state.projectId`, the same source every other settings call in that file uses — there is no
router ctx on that component.

---

## 4. Page data endpoints

All are `GET`, all read exclusively from SQLite, and all return a fully-shaped view model. Keys
below are the top level of the response.

### `GET /api/projects/<slug>/overview` — *range-aware*

`apps/dashboard/services/overview_service.py` + `decision_engine` + `alerts_service`.

| Key | Shape | Source |
|---|---|---|
| `kpis` | `[{label, value, delta, unit}]` × 4 — Total clicks, Impressions, Avg. CTR, Avg. position | `SEODaily` current vs previous period. Avg-position delta is `previous − current` (lower is better). |
| `pillars` | `[{label, target, valueKind, value, delta, deltaUnit, sub, state}]` × 5 | Organic clicks, Avg. position, Site health, Paid ROAS, AI visibility. `state` is `ok` or `setup`; Paid ROAS and AI visibility are always `setup`. Site health goes live only when audit data exists and **must equal** `/audit`'s `score`. |
| `modules` | `[{label, target, stat, sub, tone}]` × 7 | SEO Performance, Keywords, Position Tracking, Backlinks, Site Audit, AI Optimization, Paid Media. `tone` ∈ `ok|warn|bad|setup`. |
| `priority` | `[{…feed item, module:{label,target}}]` ≤ 6 | Unacknowledged alerts, sorted severity-ascending then newest-first, each tagged with an owning module. |
| `signals` | `[{type, title, detail}]` ≤ 3 | `decision_engine.generate_signals` (traffic/CTR/position/ads deltas) + `generate_ad_overlap_signals` (organic top-3 keyword that also has ad spend). `type` ∈ `positive|negative|opportunity`. |
| `trend` | `[{date, clicks, impressions}]` | Daily `SEODaily` totals across the window. |
| `summary` | `{wins: [], critical: [], watch: []}` | The latest `AISummary.summary_text` parsed from Markdown; `#`-headings are classified by emoji/keyword into win/critical/info. Items are **HTML strings** (`**bold**` → `<strong>`) and are injected with `dangerouslySetInnerHTML` on the frontend. |
| `topPages` | `[{url, clicks, impressions, ctr}]` ≤ 6 | Top `SEODaily.landing_page` by clicks. |
| `topGa4Pages` | `[{url, location, traffic}]` ≤ 10 | Last 7 days by GA4 sessions. Uses a hard-coded `date.today()` window, **not** the request range. |
| `topAuditPages` | `[{url, performance, seo, lcp}]` ≤ 10 | `PageSpeed` rows ordered by lowest performance score. |
| `topKeywords` | `[{keyword, position, clicks, impressions, volume}]` ≤ 5 | `build_top_keywords_api()`. **Raw numbers, not display strings** — every other Overview value is a raw number the SPA formats via `this.fmt()`/`this.posBadge()`, and the position chip's colour bands need a number. `null` is preserved wherever the source had no value (`"N/A"` position, `"—"` volume) and is never coerced to `0`. |
| `positioningOverview` | `{status, note, you, competitors[], keywordsTotal, competitorsWithData, capturedAt}` | `build_positioning_overview()` aggregating `_get_competitor_grid`. |

**`positioningOverview` coverage states.** `you` and each entry in `competitors` carry
`{domain, avgPosition, keywordsRanked, keywordsTotal, state}`:

| `state` | Meaning | `avgPosition` |
|---|---|---|
| `ok` | Captured on every keyword in the comparison set | Real average |
| `partial` | Captured on some keywords | Real, but averaged **only over those keywords** — always shipped with `keywordsRanked`/`keywordsTotal` so the UI can say "1 of 3 keywords captured" and it is never read as like-for-like |
| `none` | Zero captured positions | **`null`** — never averaged, never ranked, sorted last |

`status` is `"ok"` or `"setup"`; on `setup` the `note` names the fix and `competitors` is `[]`.
`keywordsTotal` is the grid's row set (keywords where *someone* ranks), not the tracked list.

**Precision is preserved end-to-end** *(fixed 2026-07-27)*. `_get_keywords_overview` in
`shared_queries.py` used to format every value for the removed Django template — position through
`f"{avg:.0f}"`, counts through `f"{n:,.0f}"`, nulls as the strings `"N/A"` / `"—"` — so an 8.4
average reached `build_top_keywords_api` as `8` and could not be recovered, and the columns sorted
as text (`"1,234" < "9"`). It now returns raw numbers: `position` = `round(avg, 1)`, counts and
`volume` as `int`, and `None` (never `0`) wherever the aggregate was NULL. Formatting belongs to
whatever renders the row; do not reintroduce it in the query.

**Related frontend:** Overview page.

### `GET /api/projects/<slug>/seo` — *range-aware*

`?range=7d|28d|90d`, default `28d`, via the same `resolve_range_periods` helper as Overview
(anchored to the latest data date, not `today()`).

```json
{
  "kpis": {"low_ctr": 12, "anomalies": 3, "critical": 4, "total_issues": 61},
  "lowCtrPages": [{"url", "impressions", "clicks", "ctr", "avg_pos"}],
  "countries":   [{"country", "clicks", "impressions", "ctr", "avg_position"}],
  "anomalies":   [{"id", "metric", "severity", "deviation", "date", "detail"}],
  "issues":      [{"issue_type", "severity", "pages", "example_url", "description"}],
  "window":      {"from": "2026-07-05", "to": "2026-08-01", "days": 28},
  "quickWinKws": 7
}
```

`low_ctr` = pages with ≥100 impressions and ≤2 % CTR (max 15 returned) **within the requested
window**, not a fixed 30 days. `critical` counts `TechnicalIssue` rows of type `not_found_404`
(these are not window-scoped — technical issues have no date dimension). `total_issues` = all
technical issues + anomalies + low-CTR pages. `quickWinKws` counts keywords ranking 4–10 with
real clicks in the window. `countries` is capped at the top 5 by clicks. `window` is the same
`{from, to, days}` shape as the Ads endpoint's `window` — the SPA's SEO page renders it next to
"Pages seen but not clicked" so the table's date range is never ambiguous.

### `GET /api/projects/<slug>/keywords`

Not range-aware — `30d` window. Built by `keywords_service.build_keywords_response`, which runs
the pandas keyword-intelligence pipeline **restricted to tracked keywords** (`SavedKeyword`).

```json
{
  "kpis":       {"total", "avg_pos", "total_volume", "total_clicks"},
  "intents":    {"informational", "commercial", "transactional", "navigational"},
  "difficulty": {"easy", "medium", "hard"},
  "segments":   {"quick_wins": ["kw", …], "striking": [], "declining": [], "low_ctr": []},
  "keywords":   [{"id","kw","intent","pos","prevPos","volume","kd","cpc","clicks",
                  "impressions","ctr","url","monthly","source","serpFeatures"}]
}
```

Keyword `id` is the keyword text itself. Segment definitions: **quick_wins** = position 4–10
with clicks; **striking** = position 11–20; **declining** = dropped ≥3 positions; **low_ctr** =
position ≤20, ≥50 impressions, <2 % CTR. Each capped at 15. `keywords` is the union of the
top-200-by-clicks slice with every segment member, so a segment tab can never reference a
keyword absent from the table. `monthly` and `serpFeatures` are always `[]` (no data source
yet); `source` is always `"sync"` here.

### `GET /api/projects/<slug>/positions` — *range-aware*

`positioning_service.build_positions_response`.

```json
{
  "kpis":            {"tracked", "avg_pos", "est_traffic", "impressions", "visibility"},
  "distribution":    {"top3", "p4_10", "p11_20", "p21_100", "unmeasured"},
  "movement":        {"improved", "declined", "added", "lost"},
  "competitors":     {"domains": ["a.com"], "rows": [{"kw", "you": cell, "comps": [cell|null]}]},
  "competitor_map":  {"status", "captured_date", "your_date", "keywords_captured",
                      "tracked_total", "volume_weighted", "domains": [mapdomain]},
  "visibility_history": {"dates": ["2026-08-01"], "tracked_total": 45,
                         "series": [{"domain", "own": bool, "points": [12.3, null]}]},
  "volume_coverage": {"tracked", "with_volume", "missing_volume",
                      "missing_keywords": ["kw"], "note": ""},
  "opportunities":   [opportunity],
  "opportunities_awaiting_data": 12,
  "project":         {"search_engine", "device", "language", "location"},
  "movers":          [keyword],
  "rankings":        [keyword],
  "keywords":        [keyword]
}
```

A *cell* is `{pos, prev, diff, direction}` with `direction ∈ up|down|flat` — plus, since
2026-08-18, two SERP-feature fields (Semrush parity, tech-lead request): `aio` (int|null — the
domain's 1-based **citation slot in Google's AI Overview** source list for that keyword; a
real ordinal, not a rank) and `feat` (`{type, slot}`|null — best non-organic feature slot,
`type ∈ local_pack|featured_snippet`). Both come from the `serp_feature_rankings` table,
written by `dataforseo_serp_competitors` (task_post now sends `load_async_ai_overview: true`,
+$0.0006/query auto-refunded when no AIO exists, and results are fetched via
`task_get/advanced` — the regular endpoint never returns AI Overview items). The whole
reference list is stored per capture (every cited domain, not just tracked ones), so
share-of-AIO-citations can be computed later without refetching. Cells for domains the
snapshot did not record keep `aio`/`feat` null — nothing is invented.
`rankings` and `keywords` are the same array (the template reads both names).

**`kpis.visibility` is THE visibility number** (added 2026-08-10; snapshot-based since
2026-08-13 — see the `GET /api/projects` section for the exact rule) — the same
`_get_ranking_distribution` field that `GET /api/projects` returns per project, so the
workspace and the project list cannot disagree. `null` = nothing measured in the window (UI
shows `—`); `0.0` = measured, ranks nowhere. `build_positions_response` computed it and
discarded it for months while the SPA's Overview card recomputed a *different* figure in the
browser from `competitors.rows`. That browser calculation still runs, but only as **share of
voice** — and since 2026-08-13 the share is **volume-weighted** (Semrush's own SoV
definition: each keyword's CTR credit × its search volume, unknown/zero volume weighs 1),
while the index printed on the card's sub-line stays equal-weight like Semrush Visibility.

The window is anchored on `views.latest_ranking_anchor` whenever the project has any
`keyword_rankings` row, forwards *or* backwards from the GSC traffic anchor. Anchoring forward
only (the pre-2026-08-10 rule) left a stale project's workspace blank while its share-of-voice
cards, which read the latest capture whenever it happened, showed real positions on the same
screen.

**`visibility_history` is the Overview trend line** (added 2026-08-12) —
`shared_queries._get_visibility_history`. One point per date the project was actually captured
on, per domain: `dates` is ascending ISO dates, and each `series` entry's `points` array is
index-aligned to it. A point is the same CTR-curve index as `kpis.visibility` computed over a
**one-day** window, so the last point and the headline are the same function of the same rows
and cannot disagree. `null` at an index means that domain was not measured that day — the SPA
draws the line straight through to the next real reading rather than dropping to 0, which would
invent a cliff nobody observed. Your own domain is `own: true` and keyed by the same
`_bare_domain(site_url)` string the legend, the share-of-voice cards and `GET /api/projects`
use; competitor lines come from `competitor_keyword_rankings` and equal the "index N" sub-line
those cards already print, so the chart is the cards over time rather than a fourth definition
of visibility.

**It is derived, not snapshotted, and that is deliberate.** `competitor_visibility` exists as a
table and has never had a writer — `pipeline/db/writer.upsert_competitor_visibility` has no call
site anywhere in the pipeline, which is why this card showed "No visibility history yet" on
every project since it shipped (the SPA compounded it: `hasHistory: false` and `series: []` were
hardcoded, so the SVG could not render whatever the API returned). Starting a snapshot log would
have left the chart empty for two more syncs, and that table's unique key
`(date, site_id, competitor_domain)` carries no `location`, so the six Premierstaff city
projects would overwrite each other's history exactly as they once did their positions.
`keyword_rankings` and `competitor_keyword_rankings` are both keyed per date and already
accumulate a row per capture — the history was in the database the whole time. Do not add a
snapshot writer for this; if you need a stored series, add `location` to the table first.

**`distribution` counts measured positions only** (changed 2026-08-10). `p21_100` was
`total − top20`, where `total` is the size of the *tracked list* — so every keyword nobody had
measured yet was asserted as a measured position between 21 and 100. A project tracking 40
keywords with 3 measured, all top-10, rendered "21–100: 37" while those same 37 rows sat in the
"Newly Added" card as never measured, on the same screen. `unmeasured` is now its own segment:
tracked keywords with no captured position in the window, whether never rank-checked or checked
and outside the captured depth (the "Newly Added" card splits those two on `rank_checked_at`).
The five keys sum to `kpis.tracked`.

**`opportunities_awaiting_data`** is how many tracked keywords the scorer had nothing to score —
no captured position *and* no search volume. They are still excluded from `opportunities` (an
evidence-free row with a number beside it is what rule 3 forbids), but they used to be excluded
*silently*, which on a brand-new project is the entire list. `opportunity.volume` is `null` when
unknown and `0` only when DataForSEO really reported 0; the scorer used to coerce the first into
the second and then print "volume 0/mo is 0% of your highest-volume tracked keyword" as fact.

A *cell*'s `diff` is **unsigned** and `direction` carries the sign, in every row including the
fallback built for keywords the competitor grid has no cell for. That branch used to pass the
signed `pos_change` straight through, and the renderer prints `▼` + `diff` verbatim — so a
keyword that had dropped three places rendered `▼-3`. All cells now go through
`shared_queries._diff_label`.

Each keyword's `source` is `"new"` when it was tracked since the last positioning sync and has no
`keyword_rankings` row in the current window at all — `"sync"` otherwise. `source` alone is NOT
enough to know whether `pos` is populated: a `dataforseo_keywords`-only row is `"sync"` (a row
exists) but still carries `pos: null` if no rank connector has ever captured that keyword. The
Landscape tab's frontend splits on `pos == null` instead — the one check that actually predicts
an unrenderable Pos/Δ cell: `pt.trackedCount` counts only rows with a real `pos` (the "All (N)"
tab label and every sub-tab filter), and `pos == null` rows are rendered in their own "Recently
Added — Awaiting First Sync" table instead of appearing as blank cells in the main grid. Don't
reintroduce a merged table — a row a user can't read anything from is worse than a separate,
honestly-labelled section.

A *mapdomain* is `{domain, is_you, keywords_ranked, coverage_pct, avg_position, best_position,
top3, top10, head_to_head, beats_you, you_beat, visibility}` — the domain-level aggregate of
`competitor_keyword_rankings` on its latest capture date. `status ∈ ok|no_data|no_competitors`.
Only captured rows are counted: a (keyword, domain) pair with no row is left out of the position
statistics entirely, never interpolated, so `no_data` is the honest answer before a positions
sync has run. `your_date` is the latest `keyword_rankings` date **at or before** `captured_date`,
reported separately because the two halves come from different connectors.

An *opportunity* is `{keyword, position, type, type_label, volume, kd, cpc, score,
estimated_traffic_gain, rationale}` with `type ∈ quick_win|striking_distance|content_gap|rising`.
`score` is 0–100 from `positioning_service.score_keyword_opportunities` — a weighted mean of
proximity (0.5), volume-relative-to-your-own-max (0.3) and ease = `(100 − KD)/100` (0.2), with
any unknown component dropped and the remaining weights renormalised rather than assumed.
`rationale` states that arithmetic in words for every row. Keywords already in positions 1–3, and
keywords with neither a position nor a volume, are not scored at all.
**`estimated_traffic_gain` is always `null`** — converting a position change into clicks needs a
position→CTR curve and no real one exists here. Each response also upserts its rows into
`keyword_opportunities` (a database write, not an external call) and prunes the ones that no
longer score, so the table is a snapshot rather than a log.

`volume_coverage` makes the "no stored search volume" gap visible instead of buying the data on
page load. `missing_volume` counts merged keywords whose `search_volume` is **`null`** — a stored
volume of `0` is a known value (DataForSEO does report 0 for some keywords) and counts as covered.
`missing_keywords` is a sample capped at 25; `note` is `""` when nothing is missing and otherwise
names the fix (run a Positioning refresh).

`project` carries the Position Tracking wizard's stored "Tracking area" choices so the workspace
header can show them. `search_engine` / `language` / `device` remain **a recorded preference
only**: both SERP connectors still post `language_name="English"` and `device="desktop"` as
literals and read neither field.

`location` is different as of **2026-08-06** — it is now a real sync parameter *and* a data key:

- `dataforseo_serp` / `dataforseo_serp_competitors` resolve it per project through
  `site_service.resolve_tracking_location(site_pk, site_id)` and send it as `location_name`
  (converted to DataForSEO's wire form by `normalize_location_name`). They used to post a
  literal `"United States"`, so a project configured for a city was measured against the
  national SERP.
- `keyword_rankings.location` / `competitor_keyword_rankings.location` store it and are part of
  those tables' unique keys. Position Tracking registers one domain as several projects (one
  per city, `add_site(allow_duplicate=True)`) and they all share `site_url` — without location
  in the key they overwrote each other's rows, and every city project rendered the union of all
  of them (identical visibility %, keyword count and up/down counts across six projects).
- Every position read is scoped by it (`shared_queries._location_clause`). A project whose city
  has not been synced yet reads **empty**, deliberately: showing another city's numbers under
  this project's name is the bug being removed.
- Which project triggered a run travels on `RefreshRun.site_pk` → `sync_all`/`sync_page` →
  `connector.site_pk`, because `site_url` alone cannot identify one of several projects sharing
  a domain and `get_site()` returns an arbitrary sibling.

**`location` scopes the measurements; `site_pk` scopes the keyword list** — two axes, both
needed, added **2026-08-06**. The view passes `resolve_project_or_404(slug).id` as `site_pk` and
`build_positions_response` threads it into every `saved_keywords` read
(`saved_keywords.site_pk` is the owning `sites.id` — see skills.md §4). Without it the
`source: "new"` rows — the SPA's **"Newly Added Keywords — Not Tracked Yet"** card — were every
sibling project's untracked keywords, so a project created minutes earlier listed 28 keywords
nobody had sent it, above a button offering to buy DataForSEO lookups for all of them.
`location` cannot substitute: two projects on a domain may track the same market, and the wizard
defaults every project to "United States".

`POST`/`PUT /api/projects/<slug>/keywords` are scoped the same way. The `PUT` reconciles through
`saved_keyword_service.reconcile_saved_keywords(site_id, rows, location, site_pk)`; an earlier
`delete(SavedKeyword).where(site_id == …)` used to destroy every sibling project's tracked list
and report only the rows it wrote back.

**The same project-scoping applies to writes, not just reads.**
`PUT /api/projects/<slug>/settings` passes `site_pk` into `apply_settings_update`, which resolves
the target row by primary key and **refuses** on a pk/domain mismatch. It previously resolved
with `select(Site).where(site_url == …).first()`, so on a duplicated domain the modal showed one
project's values and the save rewrote the oldest sibling's row — reported as "editing a
project's location removed my tracked keywords", on a project the user never opened.
`tracked_competitors` and `keyword_opportunities` are now per-PROJECT tables too (keyed
`site_pk`), as is the delete in `POST /api/projects/<slug>/clear-data`.

Two behaviours worth knowing:

- **This endpoint calls no external API.** *(fixed 2026-07-27)* It used to: any merged keyword
  lacking `search_volume` triggered a live billable `DataForSEOKeywordsConnector.lookup_keywords()`
  on every page render, uncapped, outside the Settings budget cap, writing a `connector_costs`
  row per page view. It was removed as a breach of iron rule 1 — and it was redundant:
  `dataforseo_keywords` is already in `PAGE_CONNECTORS["positioning"]` and `ALL_CONNECTORS`, and
  its `fetch()` reads the same `load_tracked_keywords()` list that bounds this endpoint's merged
  keyword set, so the Refresh path already backfills volume/KD/CPC into `keyword_rankings`.
  Do not reintroduce it in any form.
- **The gap that call papered over is now reported, not hidden.** A keyword tracked *since* the
  last positioning sync has no `keyword_rankings` row yet (and `dataforseo_keywords` stamps its
  metrics on the `yesterday()` row, so a window ending earlier will not see them). Such a keyword
  carries `volume: null` — **never `0`**, which would assert a real zero-search-volume fact — and
  is counted in `volume_coverage`.
- **The competitor grid is never estimated.** It used to synthesise a competitor's position from
  `CompetitorDomain.avg_position` plus an MD5-derived offset whenever `CompetitorKeywordRanking`
  was empty; that was removed. A pair with no captured row now renders `—`, and
  `competitor_map.status` is `no_data` until a capture exists. Do not reintroduce any form of it.

Competitor columns resolve as: explicit `TrackedCompetitor` rows → auto-discovered
`CompetitorDomain` (top by intersections) → a hard-coded fallback list
(`linkedin.com, instagram.com, facebook.com, youtube.com, reddit.com`).

### `GET /api/projects/<slug>/alerts`

```json
{"feed": [{"id", "ts", "kind", "severity", "title", "detail", "acknowledged"}]}
```

Three item kinds are merged and sorted by `(ts, -severity_rank)` descending:

| `kind` | `id` format | Source |
|---|---|---|
| `system` | `syncerr-<run_pk>` | Present only when the site's **latest** `RefreshRun` ended in `error`. Names the failing connectors from `SyncLog`. |
| `anomaly` | `anomaly-<pk>` | Every `Anomaly` row (full history, not just unacknowledged). |
| `technical` | `issue-<sha1[:12]>` | `TechnicalIssue` rows grouped by `(issue_type, severity, description)`. The id is a content hash of `(url, issue_type)` **because issue rows are wholesale-rebuilt after every sync and their PKs change** — a PK-keyed acknowledgement would silently un-ack. |

`severity` ∈ `high|medium|low|info`.

**Settings → Alerts & Rules gates this feed.** `alerts_service.load_alert_rules(site_id)` reads
`ProjectSettings.data["alertRules"]`; the `traffic_anomaly` rule gates `anomaly` items (its
`threshold` is the minimum `|deviation_pct|`) and `audit_errors` gates `technical` items (its
`threshold` is the minimum affected-page count in the group). A rule with `on: false`
suppresses its kind at source — the detector is not queried at all. `system` is never
suppressible. Missing/`null`/malformed `alertRules`, or a rule whose `threshold` will not parse,
falls back to the unfiltered pre-rules behaviour, never to an empty feed. The `pos_drop` and
`lost_backlink` rules drive nothing — no such detector exists. **The response shape is
unchanged by rules**; only which items are present changes. See `features.md` → Alerts & Rules.

### `GET /api/projects/<slug>/backlinks`

`backlinks_service.build_backlinks_response` (`apps/dashboard/services/backlinks_service.py`).
Two honest sources, never blended: **listings** (`links`, `refDomains`) come from the `Backlink`
table (matched against both the `site_id` and its `sc-domain:`-toggled variant); **distributions**
(`months`, `types`, `asBuckets`, `anchors`) come from the `BacklinksSnapshot` JSON blob that
`manage.py refresh_backlinks <slug>` writes via `pipeline/services/backlinks_service.py`. A site
that has synced individual backlinks but never run `refresh_backlinks` will have real `links`/
`refDomains` and *empty* `months`/`types`/`asBuckets`/`anchors` — that is correct, not a bug;
run the command (or wire up its own Refresh action) to populate them.

```json
{
  "kpis":      {"total", "live", "lost", "referring_domains", "avg_rank"},
  "links":     [{"domain","target_url","url_from","anchor","status","dofollow",
                 "domain_rank","page_rank","spam_score","first_seen","last_seen"}],
  "summary":   {"authorityScore","asDelta","refDomains","backlinks","dofollowPct",
                "broken","spamScore","newRdMonth","lastUpdated"},
  "months":    [{"label","nw","lost"}],
  "types":     [{"label","color","count","pct"}],
  "asBuckets": [{"label","color","count"}],
  "refDomains":[{"domain","flag","rank","backlinks","linksToUs","follow",
                 "firstSeen","isNew","category","spam"}],
  "anchors":   [{"anchor","backlinks","refDomains","type","dofollowPct"}],
  "competitors": ["a.com"],
  "gapDomains":  []
}
```

Every field is real; nothing is synthesised. `refDomains[].category` and `gapDomains` are
genuinely empty — no column/connector backs them yet (Link Gap needs a competitor-backlinks
sync that doesn't exist). `kpis.avg_rank`, `links[].domain_rank`/`page_rank`, and
`refDomains[].rank` are DataForSEO's **raw 0-1000 rank scale** (`domain_from_rank` /
`page_from_rank` from `backlinks/backlinks/live`) — the SPA (`backlinks.js`'s `asOf()`) divides
by 10 and clamps to 0-100 wherever it renders an "AS" chip or the authority donut; API
consumers doing their own math must apply the same scaling. `spam_score` is DataForSEO's
`backlink_spam_score`, already 0-100. `summary.authorityScore` is `avg(domain_rank)` over the
raw `Backlink` rows (also 0-1000, pre-scaling) — it does NOT come from the snapshot's own
(already-scaled) authority score, by design (see the module docstring's "two honest sources").

### `GET /api/projects/<slug>/audit`

`site_audit_service.build_site_audit_response`, derived from `IndexingStatus` + `PageSpeed`
(mobile only) + `TechnicalIssue`.

```json
{
  "score": 68,
  "crawl":        {"status","pagesCrawled","maxPages","startedAt","duration","userAgent"},
  "domainChecks": [{"label","detail","ok"}],
  "breakdown":    {"healthy","withIssues","broken","redirected","blocked"},
  "catScore":     {"Performance": 80, "SEO": 92, …},
  "cwv": {"lcp": {…}, "cls": {…}, "tbt": {…}},
  "checks":       [{"id","severity","category","title","howToFix","count","hidden","resolved","pages":[…]}],
  "totals":       {"errors","warnings","notices"},
  "crawledPages": [{"id","url","score","statusCode","errors","warnings","notices","depth",
                    "inLinks","internalLinks","wordCount","loadTimeMs","kind"}],
  "structure":    [{"folder","pages","avgScore","errors","warnings","notices"}],
  "snapshots":    []
}
```

- **`score` = `round(0.6 × avg mobile Lighthouse performance + 0.4 × % of pages indexed)`.**
  The Overview page's Site-health pillar uses the identical formula via
  `site_health_summary()`; the two must never disagree, and a test asserts this.
- `severity` maps from `TechnicalIssue.severity`: `high|critical → error`, `medium → warning`,
  `low → notice`. `totals` counts **only non-hidden** checks.
- `domainChecks` is a **pure state read** — `stored_domain_checks()`, straight out of
  `ProjectSettings.data["domainChecksCache"]`. The six live probes (SSL handshake,
  `/sitemap.xml`, `/robots.txt`, HTTP/2 reachability, www-vs-non-www consolidation, `/llms.txt`)
  live in the **`domain_checks` connector** (`pipeline/connectors/domain_checks.py`), which runs
  with every other outbound request in the sync path. Until it has run, the card shows a §10
  empty state rather than a blank.

  The card's own button runs the `domain_checks` **scope**, not `audit`: the probes are cheap
  and credential-free, so refreshing one card must not cost a full crawl. `audit` and `all`
  still include the connector, so a full crawl refreshes the checks too.

  *Why this changed:* the probes used to run inside the GET. The 6-hour cache did not protect
  anything, because **nothing but a page view ever wrote that cache** — so the first Site Audit
  load for every new project, after every deploy, and once every 6 hours thereafter paid a TLS
  handshake plus five HTTP fetches (3.5 s timeouts each) before rendering. It was the only place
  in the codebase reaching the network while rendering a page, and it was what made
  `test_site_audit_response`'s `domainChecks == []` assertions fail on any machine with internet.
- `cwv.tbt.p75` is **`None`** until a real `PageSpeed.tbt_ms` column exists. It is no longer
  estimated from the speed-index-minus-FCP or LCP-minus-FCP spread. `inp_ms` is deliberately not
  substituted — it is a different metric and is null on every stored row.
- `crawledPages[].internalLinks` and `wordCount` are **`None`**. They used to be
  `performance_score × 0.4` and `fcp_ms × 1.5` — a Lighthouse score and a paint timing presented
  as a link count and a word count. The real source is DataForSEO OnPage `items[].meta`
  (`internal_links_count`, `content.plain_text_word_count`), which the connector currently
  discards. `inLinks` stays `0` **only** because `test_site_audit_response.py:164` asserts it; no
  UI reads it.
- `snapshots` is real crawl history from the `audit_snapshots` table, ascending by date, which
  is what the Compare Crawls and Progress sub-tabs read. One row is written per completed sync
  by `record_audit_snapshot()` in `_run_post_sync`, **after** `rebuild_technical_issues` — the
  snapshot stores that crawl's issue counts, so taking it earlier would freeze the previous
  crawl's numbers. Both sub-tabs are empty only until the second sync completes, since
  comparing and trending need at least two points.
- `checks[].id` is the `issue_type`. Ids beginning `lh:` are dynamic Lighthouse audits, parsed
  as `lh:<category>:<title>`.

### `GET /api/projects/<slug>/offsite` — *range-aware*

`offsite_service.build_offsite_response`, over `SEODaily` and `GA4TrafficSourceDaily`.

```json
{
  "totals":  {"sessions","users","engagementRate","engagedSessions","keyEvents","revenue","referringDomains"},
  "prev":    {…same shape…},
  "trend":   [{"date","sessions","engagedSessions","keyEvents","revenue",
               "channels": {"Referral","Organic Social","Organic Video"}}],
  "channels":[{"channel","sessions","pct","engagementRate","keyEvents","offsite"}],
  "referrers":[{"domain","authorityScore","sessions","drivesTraffic","users","engagementRate","keyEvents"}],
  "referrerSplit": {"total","driving","linkOnly"},
  "social":  [{"platform","source","channel","connected","impressions","sessions",
               "engagedRate","engagementRate","keyEvents","revenue"}],
  "landingPages":[{"url","topSource","pageviews","sessions","engagedRate","bounceRate","newUsers","keyEvents"}],
  "connectors": {"linkedin","reddit","youtube","x","facebook","instagram"},
  "syncMeta": {"state": "ready", "lastUpdated": …}
}
```

`revenue` is **real**: `sum(ga4_traffic_source_daily.revenue)`, written from GA4's `totalRevenue`
metric. A property with no ecommerce/revenue events reports a genuine `0.0`, which is stored as
such — it is never back-filled with the old `conversions × $45` estimate.

`trend[].channels` is per-channel sessions for the stacked area chart, zero-filled with the **same
keys on every point** (`offsite_service.OFFSITE_CHANNELS`, in stack order) so a band cannot appear
and vanish mid-series. It always sums to that point's `sessions`.

`referrerSplit` counts **every** linking domain (not the 20 in `referrers[]`) as
links-that-drove-traffic vs links-only; `referrers[].drivesTraffic` is the same fact per row.

`social[]` is the off-site sources GA4 actually measured, ordered by sessions, capped at
`SOCIAL_TABLE_LIMIT` (8) — with **LinkedIn pinned into the first slot** even at zero sessions,
because the LinkedIn spotlight card reads that row by name. It used to be a fixed
LinkedIn/Reddit/YouTube/X roster that printed whether or not GA4 had seen them and discarded every
other source. A platform's hosts are merged into one row and matched **host-wise with a dot
boundary** against `offsite_service.PLATFORM_DOMAINS` (`linkedin.com`+`lnkd.in`, `t.co`+
`twitter.com`+`x.com`, `youtube.com`+`youtu.be`, `reddit.com`+`redd.it`); a source matching no
platform appears under its own host. Only off-site channels are read, so a Paid Social campaign on
a platform domain never appears here. `social[].impressions` is **always `null`**, connector toggle
or not:
GA4 can only see sessions that *arrived* from a source, never how many times a post was shown on
the platform, and that number lives in each platform's own API — none of which is wired. It was
formerly invented as `sessions × a per-platform multiplier`.

`syncMeta.lastUpdated` is the last successful `ga4` sync for the site (`null` when GA4 has never
run, with `lastStatus: "never"`); `cadence` and `ga4_tokens_used/limit` are deliberately absent
because nothing in this codebase tracks them.

**`engagedRate` / `engagementRate` are `null` when `sessions` is 0** — on `social[]`,
`referrers[]` and `channels[]` alike (all three go through `offsite_service._engagement`). A rate
over zero sessions is undefined, not 0%: "0% engaged" asserts visitors arrived and none engaged,
which is a measurement nobody took. A rate of `0.0` over real sessions is a genuine result and is
returned as `0.0`. The SPA renders `null` as an em dash. This matters most on `referrers[]`, where
a domain is listed because it *links* to us — most drive no measured GA4 sessions at all.

`channels[].offsite` flags membership of `offsite_service.OFFSITE_CHANNELS` — an explicit
allow-list of `Referral`, `Organic Social`, `Organic Video`. It was a substring test that also
admitted `Organic Shopping`.

`landingPages[]` is **not channel-scoped and is not entrances.** It reads `seo_daily`, which has
no channel column, so it includes Organic Search and Direct; and its `landing_page` column is
filled from GA4's `pagePath` dimension, so `pageviews` (`screenPageViews`) is the metric that is
additive at this grain — `sessions` counts once per page a visit touched. A real off-site
landing-page table needs a new GA4 report on `landingPage` × `sessionDefaultChannelGroup`.

**`connectors` (and every
`social[].connected`) is hard-`False` for all six platforms.** It used to mirror the
`platformConnectors` booleans from Settings, which a "Connect" button set without authenticating
anything — so a `true` made the page announce "Connector live · impressions + click-throughs"
next to an impressions value of `null`. No platform connector is registered in the sync engine
(neither `pipeline/connectors/linkedin.py` nor `meta.py` appears in `PAGE_CONNECTORS` /
`ALL_CONNECTORS`; Reddit/YouTube/X have no module at all), so `False` is the only honest value —
including for projects still carrying a stale `true`, which the now-inert Settings row cannot
clear. Flip these to a real per-connector check (a `SyncLog` row, as the Ads status cards do)
in the same change that registers the connector — not before.
`ProjectSettings.data["platformConnectors"]` is still accepted by `PUT .../settings` for
backwards compatibility, but nothing in the UI writes it and nothing reads it.

### `GET /api/projects/<slug>/ads` — *range-aware*

`ads_service.build_ads_response`, over `AdMetricDaily` + `SEODaily`.

```json
{
  "totals": {"spend","clicks","impressions","conversions","cpc","roas","conv_value",
             "ga4_key_events","ga4_revenue"},
  "prev":   {…}, "trend": [{"date","spend","conversions","ga4_key_events"}],
  "pacing": {"monthly_budget","mtd_spend","projected","day_of_month","days_in_month","pct",
             "channels":[{"platform","spend","budget","roas"}]},
  "campaigns": [{"id","name","status","type","platform","budget_daily","spend","clicks",
                 "impressions","ctr","cpc","conversions","cpa","conv_value","roas",
                 "lost_is_budget","prev","adGroups"}],
  "searchTerms": [], "attribution": [],
  "landingPages": [{"url","campaign","clicks","sessions","engagedRate","spend",
                    "conversions","keyEvents","revenue","roas"}],
  "negatives": [{"term","matchType","campaignId"}],
  "window":   {"from","to","days"},
  "syncMeta": {"connected","cadence","last_pull","next_pull","ops_used","ops_limit",
               "ga4_tokens_used","ga4_tokens_limit"}
}
```

`searchTerms` now reads the real `ad_search_terms` table (written by the
`google_ads_search_terms` connector) and `attribution` joins `ad_metrics_daily` against
`ga4_campaign_daily`. Both are **empty until Google grants Standard Access** to the Ads API — a
developer-token approval outside this codebase, not missing code. Note also that
`ALL_CONNECTORS` (the "Refresh all" list) deliberately excludes `google_ads`,
`google_ads_search_terms` and `meta`; only the `ads` scope runs them. `pacing.monthly_budget` is hard-coded to `3500.0`
whenever any spend exists (`0.0` otherwise); `syncMeta.ops_used/ops_limit/ga4_tokens_*` are
fixed literals. `conv_value` is imputed as `conversions × $65`, `ga4_revenue` as
`ga4_key_events × $45`. `campaigns[].adGroups` is always `[]`.
`syncMeta.connected` is `true` when Google Ads env vars exist **or** any spend was recorded.

### `GET /api/projects/<slug>/ai`

`ai_service.build_ai_response` — a mixture of genuine first-party state, real stored DataForSEO
LLM Mentions snapshots, and a couple of remaining honest placeholders.

```json
{
  "setupDone": true,
  "targets": {"brand","aliases":[],"competitors":[]},
  "budget": {"cap":500,"spent":142,"weekly_est":35},
  "costs":  {"model":118.5,"inspect":23.5},
  "next_run": "2026-07-29",
  "mentionPlatforms": [{"id","name","color"}],
  "llmPlatforms":     [{"id","name","color"}],
  "sov":   {"you","delta","rows":[{"domain","sov","mentions","isYou"}]},
  "kpis":  {"mentions","impressions","cited_pages","prompt_coverage":{"cited","total"}},
  "trend": [],
  "topPages":     [{"url","mentions","impressions","platforms","domain"}],
  "coCitedPages": [{"url","mentions","impressions","platforms","domain"}],
  "topDomains":   [{"domain","share","mentions","isYou","isComp"}],
  "visibilityState": "ok",
  "lists":   [{"id","name"}],
  "prompts": [{"id","text","listId","cfg":{"models","cadence","country","city","webSearch"},
               "results":{},"lastRun":null}],
  "suggestions": [{"id","text","category","aiVolume"}],
  "aiKeywords":  [{"kw","aiVolume","gVolume","ratio","intent","trend","mentions","gap"}],
  "history": []
}
```

**Real:** `targets`, `lists`, `prompts` (from the `AITarget` / `AIPromptList` / `AIPrompt`
Django models), `aiKeywords` when `AIKeywordData` rows exist, and — as of the LLM Mentions
feature — `sov`, `kpis.mentions`, `kpis.impressions`, `kpis.cited_pages`, `topPages`,
`coCitedPages`, `topDomains` and `visibilityState`, all assembled by
`apps/dashboard/services/llm_mentions_service.build_visibility_block(site_id)` from the
`llm_mention_metrics` / `llm_cited_pages` tables that `pipeline/connectors/dataforseo_llm_mentions.py`
writes weekly. Nothing on this page calls DataForSEO directly — the connector is the only caller,
gated behind the sync scopes like every other connector.

**`topPages` vs. `coCitedPages` — one stored list, split when it is read.** The weekly
`llm_mentions/top_pages` call returns up to `TOP_PAGES_LIMIT` (100) cited URLs, and they are
**not all ours**: a call for `driphydration.com` comes back carrying `perfectb.com` pages that
were cited in the same AI answers. Every row is stored; `llm_mentions_service.page_is_ours(url,
own_domain)` decides ownership per row at read time (host-wise, `www.`-insensitive, dot-boundary
so `blog.<us>.com` is ours). `topPages` is ours — it is what the "Your Most-Cited Pages" card and
the `cited_pages` KPI mean — and `coCitedPages` is everyone else's. Until 2026-08-12 the
connector **discarded** the co-cited rows before storing them and asked for only 10 pages, so a
real project stored four rows out of a response it had already paid for. The limit is now 100
because this endpoint's cost is dominated by the per-request fee, not the row count.

`setupDone` is real — `bool(target and target.setup_done)` — so the setup wizard shows when the
project genuinely has not been configured.

`sov.delta` is `None` until a **second** weekly snapshot exists for the site — a week-over-week
change needs a real prior measurement, and the first captured week has none. It stays `None`,
never `0`, so the SPA can tell "no change" apart from "nothing to compare against yet". Note
also that `sov` is only comparable week-over-week if `AITarget.competitors` didn't change between
the two snapshots — DataForSEO's mention counts are attributed within the queried competitive
set, so adding or dropping a competitor moves the numbers on its own (see `SKILLS.md` §4).

**`visibilityState`** is one of:

| Value | Meaning |
|---|---|
| `setup` | No `llm_mention_metrics` rows for the site yet — the connector hasn't run (no brand/competitors configured, or no sync yet) |
| `no_competitors` | Rows exist but the project has zero tracked competitors, so `cross_aggregation_metrics` couldn't run (it needs ≥2 targets) and the connector fell back to `aggregation_metrics` for the project's own numbers only. `sov.rows` contains just the project's own row — a share-of-voice percentage against nobody would be meaningless, so the SPA shows an "add competitors" state instead of a false 100% |
| `ok` | At least one competitor is tracked and captured; `sov.rows` is a real ranked list |

**`mentionPlatforms` vs `llmPlatforms` — two different lists, two different sources, do not
conflate them:**

| | `mentionPlatforms` | `llmPlatforms` |
|---|---|---|
| Entries | 2: `google` ("AI Overviews"), `chat_gpt` ("ChatGPT") | 4: `chatgpt`, `claude`, `gemini`, `perplexity` |
| Source | `llm_mentions_service.MENTION_PLATFORMS` — the only two platforms DataForSEO's LLM Mentions API covers | `ai_service.MENTION_PLATFORMS` — the four answer engines the Prompts tab checks, all four reachable through DataForSEO's separate LLM Responses API (`ai_visibility_service.PLATFORMS`) |
| Drives | The AI Visibility tab's platform-toggle chips and (once wired) the trend chart's series | The Prompts tab's per-model columns in the Tracked Prompts grid |
| Why they must stay separate | These are two distinct DataForSEO products with different platform coverage. **LLM Mentions** (share-of-voice / who's cited) covers only Google AI Overviews and ChatGPT, and requires its own $100/mo subscription commitment — not wired in this deployment. **LLM Responses** (ask-and-observe-the-answer, what `run`/`inspect` call) is pay-as-you-go and covers all four engines. `ai_optimization.js`'s `aiPlat` toggle state is keyed on `mentionPlatforms`' ids (`google`/`chat_gpt`); a default written against `llmPlatforms`' ids (as happened once — see `SKILLS.md` §9) silently renders both toggles "off" |

Both objects share the same `{id, name, color}` shape — the SPA reads `.name` (not `.label`) off
either one.

**`trend` stays `[]`** — Lean v1 collects a weekly LLM Mentions snapshot per project (see the new
analytics tables in `SKILLS.md` §4), but the 12-week trend chart itself is not wired to read them
in this release. `suggestions` and `costs`/`budget` placeholders are unrelated and documented
below/above; do not reintroduce a fabricated `trend` in the meantime.

`prompts[].results` is always `{}` and `lastRun` always `null` until `run`/`inspect` (§5) is
called on that prompt — no LLM is ever queried from a page-data GET.
`history` is always `[]`.

**Frontend consequence:** every prompt cell renders "—" until a prompt has been run at least
once, and the Answer Inspector / History sub-tabs stay empty until then.

### `GET /api/projects/<slug>/settings`

`settings_service.build_settings_response`.

```json
{
  "project":     {"id","domain","name","vertical","location","competitors":[],"tracked_keywords":[]},
  "credentials": {"gsc_property","ga4_property_id","dataforseo_target_domain"},
  "connectors":  [{"name","status","records","last_sync","error"}],
  "team":        [{"id","name","email","role","status","last_active","initials"}],
  "invitations": [{"id","email","role","invited_by","created_at","expires_at"}],
  "sync":  {"next_run": null, "day": null, "last_run": "2026-07-24T…",
            "modules": [{"module","cadence","due","reason","last_success","next_run"}]},
  "usage": {"budget","currency","month_to_date","est_monthly","items":[{"module","cadence","est","note"}]},

  "workspace":  {"name","timezone","week_start","owner_email"},
  "prefs":      {"email_alerts","weekly_digest"},
  "notifications": {"email_enabled","weekly_digest","digest_day","recipients",
                    "slack_enabled","slack_webhook","quiet_start","quiet_end",
                    "route_high","route_medium","route_info"},
  "aiConfig":   {"provider","model","tone","cadence","monthly_cap","brand_voice"},
  "dataPrefs":  {"export_format","retention","report_timezone","number_format"},
  "syncConfig": {"organic","positions","backlinks","audit","keywords","ads","ai"},
  "platformConnectors": {"linkedin","reddit","youtube","x","facebook","instagram","meta_ads"},
  "budget":     {"cap","enforce","quotas":{…}},
  "alertRules": [{"id","label","threshold","unit","on"}],
  "crawl":      {"maxPages","frequency","jsRendering","respectRobots","excludedPaths"},
  "security":   {"twofa","sso","session_timeout","sessions":[],"tokens":[]}
}
```

The block from `workspace` down is a merge of `DEFAULT_SETTINGS_BLOB` with whatever is stored in
`ProjectSettings.data` — genuine persistence, per-key defaulted.

`connectors[].status` is a real `SyncLog` value: `never|running|success|error` (**not** `ok`).
`team` self-heals roles: the first user by id becomes `Owner`, and any other `Owner`/`Viewer`
is normalised to `Admin` and written back.

`sync.next_run` / `sync.day` are **real**: computed by `apps.sync.scheduling.schedule_summary()`
— the same cadence + run-history logic `manage.py run_scheduled_syncs` itself acts on, so the
date shown is by construction the date the scheduler will use, not a parallel guess. They are
`null` only where no honest date exists: every module set to `manual`, or a brand-new project
with no successful run to measure a cadence from.

`sync.modules` is the **per-module** breakdown behind those three header values, one entry per
`apps.sync.scheduling.SYNC_MODULES` key, built from the same `due_modules()` the scheduler calls:

| field | meaning |
|---|---|
| `module` | `organic` \| `positions` \| `backlinks` \| `audit` \| `keywords` \| `ads` \| `ai` |
| `cadence` | the resolved cadence (saved value merged over `DEFAULT_SETTINGS_BLOB`), **not** the raw blob — a project that never opened Settings still reports the cadence actually in force |
| `due` | the scheduler's own verdict for right now |
| `reason` | its wording for that verdict, e.g. `"next due 2026-08-25 15:12 UTC (weekly)"` |
| `last_success` | `started_at` of the newest **successful** run, or `null`. Success-anchored on purpose: a failed attempt fetched nothing, and presenting it as "last run" reports a module as current when it is not |
| `next_run` | `null` for `manual`, and `null` when there is no successful run to measure a cadence from — both cases where any date would be invented |

The header keys keep their names and types (the SPA dereferences `next_run`/`day`/`last_run`
unguarded); `modules` is purely additive, and an older client that ignores it is unaffected.

`syncConfig` gained `organic` (Search Console + GA4, default `daily`) on 2026-08-18. Its keys
must stay exactly `SYNC_MODULES`: `get_sync_config()` merges a saved blob **over** the defaults
and drops keys the defaults do not contain, so a module missing from `DEFAULT_SETTINGS_BLOB`
cannot be scheduled however the UI is configured. `test_scheduling.ScopeAliasMirrorTests` pins
the two lists together.

`usage` is **real measured spend**. `_usage_raw()` calls all three `cost_service` readers over
the `connector_costs` rows the DataForSEO connectors write per run. The five original keys keep
their names and types (the SPA dereferences them unguarded — omitting one throws a `TypeError`);
everything else is additive:

| Key | Meaning |
|---|---|
| `window` | the full `cost_last_90_days` payload — `total`, `runs`, `by_connector[]` |
| `by_month` | dense 3-month series, `partial: true` on the current month |
| `month_to_date` | `cost_since(first of this calendar month)` — measured |
| `est_monthly` | **a projection**: `month_to_date / days_elapsed × days_in_month` |
| `est_monthly_is_projection` | `True` only when `month_runs > 0` — i.e. there is a real rate to extrapolate from |
| `est_monthly_basis` | the sentence stating what the projection was computed from |
| `has_recorded_spend` | `window.runs > 0` — distinguishes *never measured* from *measured zero* |
| `attributed_total` / `unattributed_total` | module rows vs spend from connectors no module owns (Domain overview, Live SERP, AI visibility), so the rows reconcile against the total |

Two conventions that carry meaning:
- **"Never synced" is told apart from "$0" by run counts, never by totals.** A project with no
  billed run renders a §10 empty state, not `$0.00`. A project with history but nothing this
  month shows a genuine measured `$0.00`.
- **`cost_per_unit` is `null`, not `0`**, when a connector recorded no units — and also when a
  module aggregates 2+ connectors (`units_mixed`), because summing SERP queries with crawled
  pages yields a denominator with no single meaning.

`est_monthly` never appears bare: the tile carries a `PROJECTED` chip and prints
`est_monthly_basis` beneath it. With no billed run this month it is `0` with
`is_projection: false`, and the UI renders an em dash rather than a confident `$0.00`.

Still honest zeros with no backing infrastructure: `budget.quotas.*`.

⚠️ `cost_service` matches `site_id` **exactly**, without the `_resolve_site_ids` both-forms trick
that `ai_service` uses on the same table. Correct today because `connector_costs` is new and
always written with the canonical `Site.site_url` — but it would miss rows if a site were ever
re-registered under the other `sc-domain:` form.

### `PUT /api/projects/<slug>/settings`

**Permission:** `check_owner_admin` → **403** for an `Analyst`.

Accepts a partial body; each recognised top-level key is routed to its backing store:

| Key | Effect |
|---|---|
| `credentials` | `update_site(gsc_property, ga4_property_id, dataforseo_target_domain)` |
| `project.competitors` | `set_tracked_competitors()` (empty list clears the override) |
| `project.name` / `project.location` | `update_site()` |
| `team` | Sets `UserProfile.role` for each `{id, role}` where role ∈ `Admin|Analyst`; `Owner` rows are excluded |
| `budgetCap` / `budgetEnforce` | Written into the blob's `budget` sub-object |
| `adsCredentials` | Per-platform (`google_ads`/`meta_ads`) fields, encrypted and merged into `ProjectSettings.data` — see `apps/dashboard/services/ads_credentials.py`. A blank submitted field leaves the stored value alone. |
| `workspace`, `prefs`, `notifications`, `aiConfig`, `dataPrefs`, `syncConfig`, `platformConnectors`, `alertRules`, `crawl` | Stored verbatim in `ProjectSettings.data` |
| `security` | **Per-field.** `session_timeout` persists like any other preference. `twofa`, `sso`, `sessions`, `tokens` are refused → **400** with a message naming the refused fields |

On success the response is the **full refreshed `GET` body**, not an ack.

The `security` split is deliberate: no TOTP or SAML implementation exists in this codebase, so a
stored `twofa: true` would assert a security guarantee that is not real. Refusing is the honest
answer; `session_timeout` is a plain preference and saves normally.

The UI no longer lies about it. `app.js::putSettings(body, msg, flag, revert)` takes a `revert`
callback, surfaces the error message, and rolls the control back to its previous state — the old
`.catch(() => {})` that swallowed the 400 while the toggle animated to "on" is gone.

---

## 5. Mutations

### `POST /api/projects/<slug>/keywords`

Tracks one keyword or a batch into `SavedKeyword`.

**Single:** `{"kw": "...", "volume": 1200, "kd": 34, "cpc": 2.4, "intent": "commercial", "location": "United States"}`
**Batch:** `{"keywords": [{...}, ...], "location": "..."}`

Accepts either `kw` or `keyword`, and either `volume`/`kd` or `search_volume`/`keyword_difficulty`.
Empty/invalid batch → **400** `{"detail": "keywords list is empty or invalid"}`.
Missing `kw` on the single path → **400** `{"detail": "kw is required"}`.

**Response:** `{"ok": true, "saved": <int>, "keyword": {…spec keyword shape…}}` where the echoed
keyword has `pos`/`prevPos` `null` and `clicks`/`impressions`/`ctr` `0` — honest until the next
positions sync picks it up.

### `PUT /api/projects/<slug>/keywords`

**Reconcile by name** (changed 2026-08-10 — it used to clear and rewrite).
Body: `{"keywords": [...], "location": "..."}`. A non-list `keywords` → **400**.
Returns `{"ok": true, "count": <int>, "added": <int>, "removed": <int>, "kept": <int>}`.
An empty list is valid and clears all tracking (the SPA confirms before sending one).

Identity is the cleaned, case-folded keyword. Keywords missing from the payload are deleted,
new ones are inserted, and **surviving rows are never touched** — metrics on an incoming row
apply only to keywords that are genuinely new, so the Keyword Explorer's send-to-project flow
still stores real volume/KD/CPC/intent while a caller that has none cannot blank them.

> Why it stopped being a bulk replace: the Edit Project modal has no metrics to send, so it
> filled every row with `{volume: 0, kd: null, cpc: null, intent: "Informational"}`. Each
> "Save Settings" press therefore overwrote every tracked keyword's real, DataForSEO-billed
> search volume with a fabricated `0` and wiped its difficulty, CPC and intent. The `0` was
> worse than a null — `_volume_coverage` counts only nulls, so `/positions` then reported
> **full volume coverage over invented numbers**.

> The incoming batch is logged at `DEBUG` through the module logger (it used to be a bare
> `print`, which wrote user keyword data to stdout on every save and bypassed logging config).

### `DELETE /api/projects/<slug>/keywords`

Untrack **one** keyword for this project. Body: `{"keyword": "..."}` (`kw` also accepted).
Missing or blank → **400**. Unknown slug → **404**.
Returns `{"ok": true, "keyword": "...", "deleted": <bool>}`.

**Idempotent**: deleting a keyword that is not tracked is a `200` with `deleted: false`, not a
404 — the SPA fires row actions in parallel. Scoped by `site.id`, so a sibling project tracking
the same phrase in its own market keeps its row.

> Added 2026-08-10. `saved_keyword_service.delete_saved_keyword` existed, correct and
> documented, with **zero callers and no route**, so the only way to untrack a keyword was the
> bulk `PUT` — re-sending the whole list minus one, through the Edit Project modal, which
> rewrites the project's name, engine, device, language and location on the same save. The
> Rankings Overview table now carries a per-row ✕ with a confirm.

### `POST /api/alerts/<alert_id>/ack`

Idempotent acknowledgement. Persists the id into `ProjectSettings.data["alertAcks"]`, and for
`anomaly-<pk>` ids also mirrors `Anomaly.is_acknowledged = 1`.

The project is resolved from `?project=<slug>` or a `project` body key; **when neither is
supplied the ack is recorded for every active project**, which is safe only because feed ids
embed a PK or a URL hash. Used by each row's own Acknowledge button; must stay idempotent.

Returns `{"ok": true}`.

### `POST /api/alerts/<alert_id>/unack`

**Undo an acknowledgement** — what the row's **Undo** button calls. The exact inverse of
`.../ack`: drops the id from `ProjectSettings.data["alertAcks"]` and, for `anomaly-<pk>` ids,
mirrors `Anomaly.is_acknowledged = 0`.

Both sides must be cleared, because `build_alerts_response()` reports an anomaly as
acknowledged when the mirror is set **or** the id is in `alertAcks` — clearing one alone would
leave the row permanently acknowledged.

Project resolution matches `.../ack` (`?project=<slug>` / `project` body key, otherwise every
active project) so an ack written across several projects is fully undone. Idempotent:
un-acking a never-acknowledged id is a no-op that still returns `{"ok": true}`.

### `POST /api/alerts/ack`

**Batch acknowledgement** — what "Acknowledge all" now calls. Body:
`{"ids": ["anomaly-12", "issue-ab12cd34ef56", …], "project": "<slug>"}` (`project` also
accepted as `?project=`). One read, one write and one mirror `UPDATE` regardless of batch size;
previously this button fired one POST per row (~104 requests on a real feed).

Validation: `ids` missing, not a list, or empty → **400**; more than **500** ids → **400**
(keeps the mirror `UPDATE`'s bound parameters under SQLite's ~999 cap); unknown `project` →
**404**. Without `project` the ack is recorded for every active project, as above.

Returns per-id outcomes so a partial failure stays visible and retryable:

```json
{"ok": false,
 "acknowledged": ["anomaly-12"],
 "failed": [{"id": "", "detail": "Not a valid alert id."}]}
```

`ok` is `true` only when `failed` is empty. Ids that are not usable strings fail individually
without stopping the rest; if the persist itself fails, every id is reported failed. An id with
no matching row still acknowledges (acks are stored by feed id — technical ids are content
hashes with no row of their own); only the `Anomaly.is_acknowledged` mirror is a no-op.
Idempotent: re-acking reports success.

### `POST /api/projects/<slug>/audit/toggle-check`

Body `{"checkId": "not_found_404"}` (missing → **400**). Toggles the id in
`ProjectSettings.data["auditHidden"]`. Returns `{"hidden": ["..."]}` — the full list.
Hidden checks are excluded from `/audit`'s `totals` and from the Overview error count.

### `POST /api/projects/<slug>/audit/toggle-resolved`

Body `{"checkId": "not_found_404"}` (missing → **400**). Acknowledges every page currently
affected by this check at once — a shortcut over `toggle-page-resolved` below. Unresolving
clears every acknowledgment for the check. Returns `{"resolved": ["..."]}` — the full list of
currently-resolved check ids.

### `POST /api/projects/<slug>/audit/toggle-page-resolved`

Body `{"checkId": "not_found_404", "url": "https://..."}` (either missing → **400**).
Acknowledges/unacknowledges a single page within a check. Returns `{"resolved": ["..."]}` — the
full list of currently-acknowledged URLs for that check (URLs, not check ids — don't confuse
this with the list shape the endpoint above returns).

Both endpoints write to the same store: `ProjectSettings.data["auditResolved"]` as
`{check_id: [acknowledged urls]}`. A check is `checks[].resolved: true` once every URL it
currently reports is in that list — a **subset** check, computed fresh on every `/audit` read,
never written back from a GET. This is what lets the two controls compose: acknowledging a
check's pages one at a time via `toggle-page-resolved` has the exact same end effect as clicking
the whole-check button once every page is covered, and the check drops back to active the moment
an unacknowledged page shows up under it — one tripping the check for the first time, or one a
later crawl's affected set isn't covered by an older acknowledgment.

Each entry in `checks[].pages[]` also carries its own `"resolved": bool`, independent of whether
the check as a whole is resolved yet.

Resolved checks get `checks[].resolved: true` and are excluded from `/audit`'s `totals` and the
Overview error count — same treatment as hidden checks. The Issues tab's severity filter gets a
5th pill, `Resolved (n)`, alongside `Hidden (n)`.

### `POST /api/projects/<slug>/ads/status`

Body `{"campaignId": "123", "status": "enabled"|"paused"}`.
`status` outside that set → **400**. Missing `campaignId` → **400**.
Persists to `ProjectSettings.data["adsOverrides"]["status"]`. Returns `{"ok": true, "status": "..."}`.

**This records intent only.** No Google Ads mutation is performed — the value is overlaid onto
the campaign row on the next `GET /ads`.

### `POST /api/projects/<slug>/ads/budget`

Body `{"campaignId": "123", "budgetDaily": 45}`. Coerced to `max(1, round(float(v)))`;
non-numeric → **400**. Returns `{"ok": true, "budgetDaily": 45}`. Intent-only, as above.

### `POST /api/projects/<slug>/ads/negatives`

Body `{"term": "...", "matchType": "exact"|"phrase"|"broad", "campaignId": "123"|null}`.
Missing `term` → **400**; an unrecognised `matchType` silently becomes `exact`.
De-duplicated on `(term.lower(), campaignId)`. Returns `{"ok": true, "negatives": [...]}`.

### `POST /api/projects/<slug>/ads/promote`

Body `{"term": "..."}` (missing → **400**). Saves the term as a tracked keyword
(`SavedKeyword`, source `ads_term`) and marks it promoted so its status derives as `tracked`.
Returns `{"ok": true, "keyword": {…}}`.

### `POST /api/projects/<slug>/ai/<action>`

Dispatches on the `action` path segment to `_handle_<action with - replaced by _>`.
An unmapped action returns **400** `{"detail": "Unknown or not-yet-available action: <x>"}`.

| Action | Body | Effect | Response |
|---|---|---|---|
| `setup` | `{brand, aliases[], competitors[], prompts[]}` | Upserts `AITarget` with `setup_done=True`, creates an `AIPrompt` per non-empty prompt | `{}` |
| `targets` | `{brand, aliases[], competitors[]}` | Upserts `AITarget` | `{}` |
| `prompts` | `{texts: [], listId}` | `bulk_create` of `AIPrompt` | `{"added": n}` |
| `prompts-remove` | `{id}` | Deletes the prompt | `{}` |
| `prompts-config` | `{id, cfg: {models, webSearch, country, city, cadence}, listId}` | Persists `tracked_models` from `cfg.models` and optionally moves the prompt to another list. `cadence`/`country`/`city`/`webSearch` now round-trip through `ai_service.set_prompt_cfg`/`get_prompt_cfg` (`PROMPT_CFG_KEY` in the `ProjectSettings` blob — `AIPrompt` itself has no columns for them). Unknown id → **404** | `{}` |
| `lists` | `{op: "create"\|"rename"\|"delete", id, name}` | CRUD on `AIPromptList`. `create` → `{"id": n}`. `rename` on an unknown id → **404**. `delete` is idempotent. Unknown `op` → **400** | varies |
| `run` | `{promptId}` \| `{promptIds: [..]}` \| `{listId}` \| `{}` (all tracked) | Runs the scoped prompts against their tracked answer engines for real, through `pipeline/services/ai_visibility_service.run_prompt_checks` — costs real money, which is why this is a POST the user pressed rather than part of the page GET. `promptIds` is the checkbox toolbar's "Run selected"; ids from other projects are excluded by the site filter. Unknown `promptId` or a `promptIds` list matching nothing → **404** | the `run_prompt_checks` result |
| `inspect` | `{question, promptId?}` | One ad-hoc live answer-engine check for the Answer Inspector (`ai_visibility_service.inspect_question`); the result is also persisted as a `history` entry | the stored entry, or **503** (engine not connected) / **400** (other failure) with `{"detail": "..."}` |

*(Corrected 2026-07-31: this section previously said `run`/`inspect` were "deliberately
unimplemented" and that `cadence`/`country`/`city`/`webSearch` were "accepted but not stored".
Both handlers exist in `apps/api/views.py` (`_handle_run`, `_handle_inspect`) and call real,
billed answer-engine checks through `pipeline/services/ai_visibility_service`; the four prompt
config fields persist through `ai_service.PROMPT_CFG_KEY`. Neither statement matched the code
this session found — updated rather than left stale.)*

*(Corrected 2026-08-06: `run`/`inspect` previously called OpenAI's chat-completions API
directly (`OPENAI_API_KEY`), so only `chatgpt` was ever connectable — Claude/Gemini/Perplexity
were permanently `not_connected`. All four now go through DataForSEO's AI Optimization LLM
Responses API (`POST /v3/ai_optimization/<llm_type>/llm_responses/live`) on the standard
`DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD` pair — no separate key per provider, and `cost` is the
USD DataForSEO's own response envelope reports, not a local price table. `webSearch` (from
`PROMPT_CFG_KEY`) now actually reaches the request and, when on, `citations` on the result/history
entry are the real provider-verified `{title, url}` source annotations DataForSEO returns —
previously always `[]`. `not_connected` now means "DataForSEO credentials are unset", not
"this provider has no connector".)*

*(Changed 2026-08-27: `webSearch` now defaults **on** — in `DEFAULT_PROMPT_CFG`, in
`check_prompt`'s own signature, and in `inspect` (which passes the inspected prompt's stored
config, or the default for an ad-hoc question — previously the Inspector always ran searchless).
Without web search only Perplexity's search-native `sonar` ever returned citations, so the other
three columns could not show "Cited" at all. Web-search checks bill higher per call; the
per-prompt toggle still opts out. `_citation_hit` additionally matches a bare-brand-name needle
against a citation host's registrable label by exact equality, so competitors tracked by name
rather than domain are seen in citations.)*

*(Also 2026-08-27 — web-search request fields are now gated per provider
(`_WEB_SEARCH_FIELDS`), verified against DataForSEO's per-provider docs and one live failure:
**chatgpt/claude** accept `web_search` + `force_web_search` + `web_search_country_iso_code` +
`web_search_city` (all four now sent, force included so the model cannot skip the search);
**gemini** accepts `web_search` only — a geo field comes back `40501 Invalid Field` and kills
the check, which is exactly what happened in production; **perplexity** (sonar always searches)
accepts only `web_search_country_iso_code`. The prompt config's City field is therefore REAL
for ChatGPT/Claude and the modal says so. `check_prompt` results and history entries now carry
`location` = the geo targeting actually sent ("US · Austin") or the honest "No location
targeting". Per-prompt `cadence` remains stored-but-unscheduled: nothing runs tracked prompts
automatically (`next_run: None` by design — the site Automation "ai" module refreshes only
AI keywords + LLM Mentions). Cells and history entries additionally carry `topPick` — the
answer's own #1 ranked-list item, whoever it names, extracted by `analyze_answer` and
backfilled by the free rescan — and `webSearchUsed`, DataForSEO's report of whether the
provider REALLY searched (None when the envelope is silent); the Answer Inspector renders
both. ChatGPT's default model is `gpt-5.4-mini` (was `gpt-4o-mini`, mid-2024 and two
generations behind chatgpt.com; noticeably pricier per check ~$0.03 with web search).
`check_prompt` self-heals `40501 Invalid Field` rejections by dropping the named optional
field and retrying — gpt-5.x rejects `max_output_tokens`, `temperature` AND
`force_web_search`, all fine on gpt-4o; rejected tasks bill $0, and learned rejections are
cached per (platform, model) for the process. An answer whose text ends in a colon-intro
("…options to consider:") is treated as provider truncation → `state: "error"`, never scored
"absent" — observed live on 2 of 5 gpt-4o-mini checks. New prompts seed
`DEFAULT_TRACKED_MODELS` = chatgpt/gemini/perplexity — Claude is excluded from DEFAULT
tracking by founder cost decision (each engine's web-search fee is per-provider;
~$0.072/prompt for the trio vs ~$0.094 for four) but stays connectable and can be re-added
per prompt in Settings.)*

---

## 6. Team, invitations & account

### `POST /api/projects/<slug>/team`

Creates a user directly. **Permission:** `check_owner_admin` → 403 for an Analyst.

Body `{"email", "username", "password", "role"}`; `role` outside `Admin|Analyst` becomes
`Analyst`. Missing any of email/username/password → **400**. Duplicate username or email →
**400**. Wrapped in `transaction.atomic()`. Returns `{"ok": true, "id": <user_id>}`, or **500**
`{"detail": "<exception>"}`.

### `DELETE /api/projects/<slug>/team/<user_id>`

**Permission:** `check_owner_admin`. Refuses (**403**) to delete `user_id == 1` or any user whose
profile role is `Owner`. Unknown user → **404**. Returns `{"ok": true}`.

### `GET /api/projects/<slug>/invite`

Lists all **unaccepted** `UserInvitation` rows, newest first. Note this is not scoped to the
project — invitations are global.

### `POST /api/projects/<slug>/invite`

**Permission:** `check_owner_only` → **403** for anyone but the Owner.

Body `{"email", "role"}`. Invalid email (no `@`) → **400**. Existing user with that email →
**400**.

Behaviour: deletes any prior unaccepted invitation for the email, creates a **`UserInvitation`**
row carrying a random token and an expiry, and emails a `<base>/accept-invite/?token=<token>`
link pointing at the server-rendered accept page (`apps.accounts.views.AcceptInviteView`).
It does **not** create the `User`; the account is created by the invitee when they accept, with a
password only they have chosen. SMTP failure is logged as a warning, not surfaced.
Returns `{"ok": true, "id": <invitation_id>}`.

`<base>` comes from `build_frontend_link` (`apps/api/views.py`): the origin of the incoming
request, so a dev box mails `http://localhost:8000/...` and the deployed site mails
`https://limitless.vashstudios.cloud/...` with no config. `settings.FRONTEND_URL` overrides it
when set — **except** when it points at localhost while the request came from a real host, which
is a copied-`.env` mistake, not a split-origin deployment.

*(Fixed 2026-08. The link used to be `FRONTEND_URL/#/accept-invite?token=…`, a route inside the
SPA — which is served from `/` behind `LoginRequiredMiddleware`, so every invitee was 302'd to
a sign-in form they had no account for. The URL fragment never reaches the server, so no
middleware exception could have rescued that shape.)*

*(Rewritten 2026-07. The previous handler generated a `secrets.token_urlsafe(10)` temporary
password, created the `User` and `UserProfile` immediately, and emailed the plaintext password
with a plain `/login/` link — while never writing a `UserInvitation` row, so invitees never
appeared in `GET /invite` or Settings' pending list and could not be revoked. The `id` in the
response is what the resend/revoke tests key off.)*

### `POST /api/projects/<slug>/invite/<invite_id>/resend`

**Permission:** `check_owner_only`. Unknown/accepted invitation → **404**. Extends
`expires_at` by 48 hours and re-sends an email containing the same
`<base>/accept-invite/?token=<token>` link. Returns `{"ok": true, "link": "..."}`.

### `DELETE /api/projects/<slug>/invite/<invite_id>`

**Permission:** `check_owner_only`. Deletes an unaccepted invitation; unknown → **404**.
Returns `{"ok": true}`.

### `GET /api/auth/invite-status?token=…`

**Public** — `permission_classes = []`, `authentication_classes = []`.

| Outcome | Status | Body |
|---|---|---|
| Missing token | 400 | `{"valid": false, "reason": "missing_token"}` |
| Not found | 404 | `{"valid": false, "reason": "not_found"}` |
| Already accepted | 400 | `{"valid": false, "reason": "already_accepted"}` |
| Expired | 400 | `{"valid": false, "reason": "expired"}` |
| Valid | 200 | `{"valid": true, "email", "role", "invited_by"}` |

### `POST /api/auth/accept-invite`

**Public.** Body `{"token", "password"}` — `username` is optional and **defaults to the
invitation's email address**, which is what the emailed page relies on.

Validation: token + password required (**400**); token must exist (**404**), be unaccepted
(**400**) and unexpired (**400**); username must be free (**400**); no existing user may hold
the invitation's email (**400**); password must pass `AUTH_PASSWORD_VALIDATORS` (**400**) —
the same rules `/admin` and the password-reset flow apply, not a bare length check.

On success (inside `transaction.atomic()`): creates an active `User`, sets `UserProfile.role`
from the invitation, marks the invitation accepted. Returns
`{"ok": true, "user_id", "username", "email", "role"}`, or **500** on an unexpected error.

The rules live in `apps/accounts/services.py::accept_invitation`, shared with the
server-rendered `/accept-invite/` page so the two entry points cannot drift.

### `POST /api/auth/password`

Changes the **logged-in** user's password. This view is **not** `login_not_required`, so it
requires a session; it also checks `request.user.is_authenticated` and returns **401** otherwise.

Body `{"old_password", "new_password"}`. Wrong current password → **400**; new password shorter
than 8 → **400**. On success calls `update_session_auth_hash` so the session survives, and
returns `{"ok": true}`.

---

## 7. Refresh / sync

### `POST /api/projects/<slug>/sync`

Body `{"scope": "all"}` (default `all`). Valid scopes are the `PAGE_CONNECTORS` keys plus
`all`; the SPA also sends `positions`, which is aliased to `positioning`.

**No credential gate.** This used to resolve the GSC property and the GA4 property id
up front and return a blanket **400** if either was missing or wrong — which meant a
brand-new site (GA4 property is `NULL` by definition until someone visits Settings) could not
run *any* scope, including `backlinks`, which touches neither credential. Now the run always
starts; connectors that cannot be instantiated for a missing credential are skipped (see
below), and the response's `warnings` names exactly which ones and why, instead of refusing
the whole refresh.

Creates a `RefreshRun` row (`status=running`, `total_count=len(connectors)`, `pid=NULL`) and
launches `python manage.py run_sync --run-id <id>` as its **own OS process** via
`subprocess.Popen` (detached) — not a thread inside the web worker. This is why a refresh
survives navigating to another page, reloading, or even a `gunicorn`/`systemctl` restart: the
process outlives the request, and outlives the worker that started it. The run's pid is written
back onto the row once the child launches (`sync_api_service.start_sync_run`).

**Concurrency guard — one run per DOMAIN, answered per PROJECT.** Only one `RefreshRun` may be
`running` per `site_url` (a partial unique index enforces it). What the second caller gets
depends on whose run holds the slot:

* **Same project (or the caller passed no `site_pk`)** — the existing `task_id` is returned
  with `already_running: true`: two tabs, a re-click, or a cron tick during a manual refresh
  attach to the same run rather than forking a race over the same `SyncLog` rows.
* **A DIFFERENT project on the same domain** (Position Tracking registers many projects per
  domain) — the response is `{"sibling_running": true, "task_id": <live run>, "scope": ...,
  "project": "<owning project's name>"}` and **no attach happens**. Attaching used to show the
  sibling's progress bar as this project's and then "complete" having fetched nothing for this
  project's location — which is how new city projects stayed permanently blank while the user
  watched a successful-looking fetch. The SPA queues this project's fetch client-side
  (`state.sync.queued`, a FIFO) and starts it when the slot frees; `task_id` is returned so it
  can watch the live run. A running row with `site_pk NULL` (scheduler) counts as a sibling to
  any project-specific request.

**Freshness — per project for location-scoped scopes.** The already-fresh prompt
(`{"fresh": true, "last_synced": ...}`, manual non-forced calls only) is based on `SyncLog`,
which is keyed `(connector, site_url)` — domain-level. For scopes that fetch per-project data
(`positions`, `positions_new`, and `all`, which includes the positioning connectors), a request
carrying a `site_pk` is only "fresh" if **that project itself** has a successful `RefreshRun`
for that scope (or `all`) inside the 24 h window — a sibling's sync an hour ago says nothing
about this project's location, and used to swallow every other city project's first fetch for
a day. Domain-level scopes (`backlinks`, `seo`, `ads`, …) keep domain-level freshness.

**Response**

```json
{"task_id": 17, "steps": ["gsc", "ga4", …], "est_cost": 0,
 "warnings": ["Google Analytics 4 is not configured, so 1 step(s) will be skipped (ga4). Set it in Settings → Connections, then refresh again."]}
```

`est_cost` is always `0` (no cost model exists). `steps` falls back to
`["No connectors for this scope"]` when the scope maps to an empty list. `warnings` is `[]`
when every connector this scope needs has its credentials configured.

### `GET /api/tasks/<task_id>`

Polled by the SPA — 500 ms for the first ~6 s, then every 2 s (the 500 ms cadence was itself
contributing to "the UI feels frozen": against a handful of gunicorn workers, ticks piling up
behind a slow one competed with whatever page GET the user had just triggered).

```json
{
  "done": false, "progress": 0.42, "step": "Syncing ga4", "status": "running", "error": null,
  "steps": [
    {"name": "gsc", "label": "gsc", "state": "done", "records": 189, "error": null},
    {"name": "ga4", "label": "ga4", "state": "running", "records": null, "error": null},
    {"name": "gsc_keywords", "label": "gsc_keywords", "state": "pending", "records": null, "error": null}
  ]
}
```

`progress` is `completed_count / total_count` while running and `1.0` once done.
`step` becomes `"Done — N records written"` on success or
`"Completed with errors — <first line>"` on failure, with the full text in `error`.

The payload also carries **whose run this is**: `site_url`, `site_pk`, and `project` (the
owning project's display name; `null` for a domain-wide run). The SPA banner renders
`project` — with many projects per domain, "Syncing Positions for premierstaff.com" never
said whose fetch was actually running.

`steps[].state` is one of `done` / `running` / `pending` / `error` / `skipped`. A `done` step's
`records`/`error` come from that connector's live `SyncLog` row for *this* run
(`SyncLog.last_synced >= run.started_at` distinguishes it from a previous run's row); a
finished step with no such row is `skipped` — the connector's credentials were missing, so it
never ran, and the checklist says so rather than showing a false ✓.

**An unknown `task_id` returns `200 {"task_id": id, "done": true}`, not 404** — the SPA treats
any non-2xx as a hard error, and a 404 would break the progress bar for a task that finished
before a page reload.

### `GET /api/projects/<slug>/sync/preflight[?scope=all]`

Free, read-only feed for the confirm dialog "Refresh all" opens BEFORE spending anything
(added 2026-08-31 — the button used to start a 20-30-minute metered run on one bare click).
`{scope, groups: [{label, connectors, last_synced, est_cost, est_seconds}], total_est_cost,
total_est_seconds, cost_partial, time_partial}`. Groups are `sync_api_service._PREFLIGHT_GROUPS`
(each connector in exactly one group — no double-counted sums). `last_synced` is the OLDEST
success among the group's connectors and null whenever any of them has never succeeded — an
errored last run means there genuinely is something to fetch. Estimates come from the site's
own history: `SyncLog.duration_seconds` and the mean of each connector's last 5 `ConnectorCost`
rows — never a price table; `cost_partial`/`time_partial` flag missing history so the SPA words
totals as "at least" rather than faking precision. The SPA (app.js `openRefreshConfirm`) skips
the dialog and refreshes directly if this read fails — the guard must never become the outage —
and a click while a run is active keeps its old queue/notify meaning.

### `GET /api/projects/<slug>/sync/active`

`{"task_id": 17, "scope": "all", …}` for the in-flight `RefreshRun` on this site — the full
`GET /api/tasks/<id>` payload rides along, including `project`/`site_pk` (the run may belong
to a sibling project on the same domain; the reloaded SPA uses `project` to label the banner
truthfully and to decide the run is not its own) — or `{"task_id": null}` if none. Called once from the SPA's `boot()` so a hard page reload
re-attaches to a sync already running server-side instead of losing track of it — before this
endpoint existed, a reload made a 20-30 minute run invisible to the user for its remaining
duration even though it was still writing to the database.

### Orphaned-run reaping (`apps/sync/scheduling.reap_orphaned_runs`)

A `RefreshRun` can only be marked `running` forever if the process behind it died without
updating the row. Now that the pid is known, a dead process is detected directly —
`os.kill(pid, 0)` fails — rather than waiting out the full `RUN_TIMEOUT` (2 h). Rows younger
than `PID_GRACE` (2 min) are never pid-checked, because `start_sync_run` creates the row
*before* the child process exists, and killing a run that is mid-spawn on that basis would be
exactly the bug this exists to prevent. A row with no pid (predates this column, or the race
window itself) still falls back to `RUN_TIMEOUT`.

Callers: app startup (`apps/sync/apps.py`, once per web process, on the first request),
`run_scheduled_syncs`, and `sync_api_service` before it starts or reports a run.

#### Orphaned-connector reconciliation (`reconcile_orphaned_sync_logs`)

Reaping the run was only half the job. `BaseConnector.sync()` sets its `SyncLog` row to
`running` on the way in and rewrites it on the way out; when the process is killed in between,
nothing rewrites it — and unlike `RefreshRun`, **nothing used to reap it**, so the row stayed
`running` permanently. Settings → Data pipeline reads `SyncLog`, so the connector that happened
to be in flight when the process died reported *"Last synced: never · 0 records"* forever, even
with real rows in its analytics table. Observed on `premierstaff.com`: `pagespeed` and
`url_inspection` were stuck from 2026-07-24, while `page_speed` held 96 real Lighthouse rows
written by those very runs.

`reconcile_orphaned_sync_logs()` runs at the end of every `reap_orphaned_runs()` call — including
the ticks that reap nothing, since an orphaned `SyncLog` outlives the run it belonged to. A row
is orphaned when **its site has no `RefreshRun` at `running`**. That is a fact, not a timeout:
`connector.sync()` is reachable only through `sync_engine.sync_all`/`sync_page`, both of which
require a `run_id`, and `start_sync_run` creates the `RefreshRun` row *before* spawning the
process — so a live connector always has a live run behind it.

Only `status` (→ `error`) and `error_message` are written. `records_written` and `last_synced`
are left untouched: what a killed run managed to write before dying is a real measurement.

#### `SyncLog.last_synced` means *last finished*, never *last started*

Only the `success`/`error` writes stamp it. A start deliberately leaves the stored value alone,
so a running connector reads *"last synced &lt;then&gt;, running now"*. It used to be overwritten
with `None` on every start, which destroyed that answer the instant a sync began — and if the
process was then killed, the loss was permanent (the bug above). A connector that has genuinely
never finished still has `NULL`, because the column defaults to `NULL` on insert.

This is what `_step_details`' `last_synced >= run.started_at` test relies on to tell *this* run's
row from a previous run's: a finished connector is always stamped after `run.started_at`, and a
connector skipped for missing credentials is never written at all.

### Scope → connector registry

From `pipeline/services/sync_engine.PAGE_CONNECTORS`:

| Scope | Connectors |
|---|---|
| `overview` | `gsc`, `ga4` |
| `seo` | `gsc`, `ga4` |
| `alerts` | `gsc`, `ga4` |
| `ads` | `google_ads`, `google_ads_search_terms`, `ga4` |
| `keywords` | `gsc_keywords`, `dataforseo_ai_keywords` |
| `pages` | `gsc_pages`, `url_inspection`, `pagespeed` |
| `backlinks` | `dataforseo_backlinks` |
| `positioning` (alias `positions`) | `dataforseo_serp`, `dataforseo_keywords`, `dataforseo_labs_competitors`, `dataforseo_serp_competitors` — **DataForSEO only, deliberately** (2026-08-06): `gsc_keywords` was removed because it is a whole-account Search Console report, not a per-project fetch; the grid's clicks/impressions/CTR still refresh via the `keywords` scope and "Refresh all" |
| `positioning_new` (alias `positions_new`) | `dataforseo_serp`, `dataforseo_keywords`, `dataforseo_serp_competitors` — narrowed by `keywords_needing_backfill()` to keywords missing volume OR never rank-checked (no `position` and no `impressions` on any row — volume alone isn't enough, since `dataforseo_keywords` can price a keyword `dataforseo_serp` has never touched) |
| `ai` | `dataforseo_ai_keywords`, `dataforseo_llm_mentions` |
| `audit` | `domain_checks`, `gsc_pages`, `url_inspection`, `pagespeed`, `dataforseo_onpage` |
| `domain_checks` | `domain_checks` |
| `insights`, `settings` | *(none — succeed immediately)* |
| `all` | the 16 connectors in `ALL_CONNECTORS` |

`ALL_CONNECTORS` = `domain_checks, gsc, ga4, gsc_keywords, dataforseo_serp, dataforseo_keywords,
gsc_pages, url_inspection, pagespeed, sitemap, dataforseo_labs_competitors,
dataforseo_serp_competitors, dataforseo_backlinks, dataforseo_onpage, dataforseo_ai_keywords,
dataforseo_llm_mentions`.

**Stopping a run.** `POST /api/projects/<slug>/sync/cancel` → `{cancelled, task_id}` or
`{cancelled: false, reason}`. Always `200` — "nothing was running" is a race (the run finished
while the user reached for the button), not a client error. Two halves, both required: the row
is flipped to `cancelled` via a CONDITIONAL update (`filter(pk=…, status=RUNNING).update(…)`),
and only if that changed exactly one row is the `run_sync` process killed by its stored pid.
That condition is the pid-reuse guard — a recycled pid would otherwise mean killing an
unrelated process. `sync_all`/`sync_page` re-read the status between connectors, so the run
stops even when the kill fails. Records already written are kept; the connector in flight may
already be billed. The kill goes through `scheduling.terminate_sync_process`, deliberately
**separate** from `_process_alive` (see that function's warning about `os.kill` on Windows).

`cancelled` is its own `RefreshStatus`, never `error`: Settings → Connections renders errors as
live problems, and `FAILED_RUN_BACKOFF` would hold the module off for 6 hours — blocking the
restart the user cancelled in order to make.

**"Already fetched recently".** Before starting a MANUAL run, `start_sync_run` calls
`scope_last_synced()`. If every connector in the scope has a `success` row inside
`FRESH_WITHIN` (24 hours, a module constant — not configurable), no run is created and the
response is `{"fresh": true, "scope", "last_synced"}` — a shape with **no `task_id`**. The SPA
prompts "last fetched 40 minutes ago — refetch anyway?" and re-POSTs with `force: true`.
A connector whose last run **errored** is never fresh, so a refresh right after fixing a
credential always runs. `manual=False` disables the check entirely and is what
`run_scheduled_syncs` passes: the cadences already are the scheduler's freshness logic (a 24h
window over a 12h `ads` cadence would silently starve Ads), and it reads `info['task_id']` on
the next line.

**`domain_checks` is the one scope that exists for a single card.** Its connector needs no
credentials and makes no metered call — six plain HTTPS requests to the customer's own domain,
about four seconds in total. It exists because the Domain Checks card's button used to fire
`audit`, i.e. 20-30 minutes and a billable DataForSEO OnPage crawl, to record those six
booleans. `audit` still runs it (first, so the card fills in while the slow connectors work),
so a full crawl refreshes the checks exactly as before.

**Post-sync processing** (`_run_post_sync`, all failures logged and swallowed):
when `gsc` or `ga4` ran → rebuild `SEOAggregate` and run anomaly detection; when any of
`gsc`/`ga4`/`gsc_pages`/`url_inspection`/`pagespeed` ran → rebuild `TechnicalIssue`; when any of
`url_inspection`/`pagespeed`/`dataforseo_onpage` ran → write the `AuditSnapshot`; when any of
`gsc`/`ga4`/`gsc_pages`/`url_inspection` ran → generate the OpenAI weekly summary.
The domain checks used to be a fourth hook here and are now the `domain_checks` connector —
which is what gives them a `SyncLog` row, a step in the refresh checklist and a visible error
state, none of which a swallowed side effect had.

A connector that cannot be instantiated (missing credentials) is **skipped silently** —
`completed_count` advances and the run can still report `success`.

---

## 8. On-demand research endpoints

These three intentionally call an external API during the request. They are user-initiated
lookups, not page renders.

### `POST /api/research`

Keyword Explorer. Body `{"project": "<slug>", "keywords": ["seed", …], "location": "United States"}`.

`location` is validated against a 19-entry allow-list (`EXPLORER_LOCATIONS`); anything else
silently becomes `United States`. An empty keyword list returns
`{"rows": [], "cost": 0, "location": …, "error": "Enter at least one keyword."}`.

Strategy: `DataForSEOKeywordsConnector.expand_keywords(seeds, location, limit=100)`, falling
back to `lookup_keywords()` on failure, then a second `lookup_keywords()` pass to backfill any
seed the expansion omitted.

`expand_keywords` runs **four** DataForSEO Labs fetches in parallel and merges them into one
deduplicated row set:

| Fetch | Endpoint | Seeds per call | `source` |
|---|---|---|---|
| ideas | `keyword_ideas/live` | all seeds, one task | `ideas` |
| related | `related_keywords/live`, `depth: 2` | **one seed per task**, first 3 seeds | `related` |
| suggestions | `keyword_suggestions/live` | **one task per seed**, first 3 seeds | `suggestions` |
| questions | `keyword_ideas/live` + 8 question-prefix filters | all seeds, one task | `questions` |

The two per-seed endpoints are capped at `RELATED_SEED_CAP = 3` because they are billed per
task, so seed count is a direct cost multiplier. `depth: 2` on related is required for `limit`
to mean anything — DataForSEO's default of depth 1 returns at most 8 keywords. A whole search
runs roughly $0.02–0.03; the response's `cost` is the figure DataForSEO reported for itself and
is what the SPA prints, so no estimate is fabricated.

**Response** `{"rows": [...], "cost": <float>, "location": "...", "status": "ok", "error"?: "..."}`
where each row is
`{kw, match, source, sources[], volume, kd, cpc, intent, serpFeatures[], monthly[], tracked}`.
`tracked` reflects whether the site already has `KeywordRanking` rows for that keyword.

**`volume` is `null` when DataForSEO reported no figure** — the same contract the tracked-keyword
endpoints use, and the SPA renders it as an em dash. A literal `0` means "measured at zero" and
is a different fact. Rows are ordered volume-descending with `null` volumes last.

**`match` and `source` are two different axes and the SPA reads both:**

| Field | Question it answers | Values | Drives |
|---|---|---|---|
| `match` | what shape are these words relative to the seed? | `exact`\|`phrase`\|`questions`\|`broad` | Broad / Phrase / Exact / Questions tabs |
| `sources` | which fetch(es) returned this keyword? | `ideas`, `related`, `questions`, `suggestions`, `lookup` | Related tab |

`source` is the first (primary) entry of `sources`; a keyword returned by more than one
algorithm appears **once**, with every algorithm listed. `match` never carries the value
`related` — deriving the Related tab from word shape emptied it, because
`related_keywords/live` returns keywords that contain the seed and those classify as `phrase`.
Rows cached by the SPA before this field existed still carry `match: "related"`, and the tab
filter accepts either form.

Returns honest empty rows (never fabricated data) when DataForSEO is unavailable.

### `POST /api/prompt-research`

Prompt Explorer. Body `{"project": "<slug>", "seeds": ["term", …]}`.

**No external API is called.** Six templates are expanded per seed
(recommendation ×2, cost, comparison, question, local), deduplicated, capped at 40.

**Response** `{"rows": [{text, category, aiVolume: 0, tracked}], "cost": 0, "location": "n/a"}`.
`aiVolume` is honestly `0`; `tracked` checks existing `AIPrompt` rows.

### `POST /api/domain-overview`

Body `{"target": "example.com/path", "location": "United States", "project": "<slug>",
"include": ["backlinks"]}`. Missing target → **400**; a non-list `include` → **400**.

The view is a passthrough. All of the logic — the caches, the spend gate, the tracked-keyword
join, the backlink sections — lives in `apps/dashboard/services/domain_overview_service.py`.

**`include: ["questions"]` — AI questions.** Which questions an answer engine was asked where
this URL comes back, from `ai_optimization/llm_mentions/search/live`. Its own button, like
`backlinks`; the default Analyze press never buys it. Per row: `question`, `answer`, `platform`,
`our_url`, `cited`, `retrieved`, `ai_search_volume`, `monthly_searches`, `fan_out_queries`,
`cited_domains`. **`cited` and `retrieved` are distinct and must stay so** — cited means the
engine quoted the page, retrieved means it found the page and quoted somebody else.

DataForSEO **rejects a path** in its `domain` field (40501), so the request always carries the
bare domain and the page filter is applied to the rows. One press therefore answers for every
page on that domain. A page with no questions reports `domainTotal` alongside, because "this
page is not referenced" and "this domain is not referenced" are different findings.

**Persistence and `refresh`.** All three blocks are stored in `domain_lookups`, one row per
(domain, path, location, block). Read order is **store → 24h cache → network**; `{"refresh":
true}` is the only thing that re-buys. Blocks served from the store carry `storedAt`/`ageDays`
so the UI can say "as of" rather than implying the answer is live. Measured cost model for the
questions endpoint: **$0.10 per request + ~$0.001 per row**, so a smaller `limit` saves almost
nothing and fewer requests saves everything.

**Spend gate.** Three of the four live lookups call
`pipeline.connectors.dataforseo_cost.ensure_budget()` before constructing a connector:
`/api/domain-overview`, `/api/research` and `/api/live-serp`. `/api/connection-check` is
deliberately **not** gated — its DataForSEO probe is the free `appendix/user_data` balance call,
so refusing it would block credential setup to save nothing, and a user who cannot verify
credentials cannot fix their spend either. (`/api/research` is the most expensive of the four:
one press fans out to `keyword_ideas`, `related_keywords`, `keyword_suggestions` and question
ideas, several of them one metered task *per seed*.) When
the monthly cap is configured (`DATAFORSEO_MONTHLY_BUDGET` > 0, the default is 100) and
month-to-date spend has reached it, the response is a **200** with
`{"status": "error", "error": "Monthly DataForSEO budget reached — raise it in Settings to
continue", "budget_exceeded": true, "spent", "cap"}`. A cap of 0 means *no cap configured* and
the gate does nothing. The cache is read first, so a target already looked up this session
still answers past the cap. `record_cost` only ever *notified* on a crossing; nothing refused
a call outside `start_sync_run`'s sync paywall.

Calls DataForSEO Labs `ranked_keywords/live`. When a path is supplied it is applied as a
`ranked_serp_element.serp_item.relative_url` filter. Results are cached in Django's cache under
`domain_overview_<target>_<location>` for **24 hours** (only on `status == "ok"`).

**Location is COUNTRY-LEVEL here, unlike Position Tracking.** DataForSEO Labs documents
`"location_type": "Country"` as *the only supported location_type*, so a city value returns
`Invalid Field: 'location_name'` and the whole lookup fails — which is what every
city-configured project used to get: an error banner and empty KPIs. The connector now degrades
any finer location to its country via `dataforseo_live_serp.country_of` and reports that it did.
The SPA's market dropdown therefore offers countries plus a "Same as project" default, and shows
a note whenever a downgrade happened. This is an upstream API limit, not something to work
around; per-city measurement lives in Position Tracking, which uses the SERP API.

**Response**

```json
{"status":"ok","metrics":{"organic_traffic","traffic_value","ranked_keywords"},
 "keywords":[{"keyword","intent","position","volume","cpc","traffic","url"}],
 "target","domain","path","cost",
 "location","requested_location","location_downgraded"}
```

or `{"status": "error", "error": "..."}` — note this is a **200 with an error body**, not a 4xx.

**`include: ["backlinks"]` — opt-in, a deliberate second press.** Adds a `backlinks` key to the
same response. Three billed calls: `backlinks/summary/live`, `backlinks/backlinks/live`
(**limit 100**, dofollow filter OFF — a spam review must see nofollow links) and
`backlinks/anchors/live` (**limit 60**). The default Analyze press is unchanged: one Labs call,
50 keywords.

```json
"backlinks": {
  "state": "ok|empty|setup|budget|error", "note", "cached", "target",
  "limit": 100, "anchorsLimit": 60, "locationApplies": false,
  "summary": {"backlinks","refDomains","refPages","dofollowPct","broken","authorityScore","spamScore"},
  "spam": {"targetScore","highSpamLinks","mediumSpamLinks","scoredLinks","unknownLinks"},
  "links": [{"urlFrom","referringDomain","targetUrl","anchor","dofollow","domainRank",
             "pageRank","spamScore","spamBand","firstSeen","status"}],
  "anchors": [{"anchor","type","backlinks","refDomains","dofollowPct"}]
}
```

- **Cached 24h under `domain_overview_backlinks_<domain>` — DOMAIN ONLY.** The Backlinks API
  has no location parameter at all, so the market dropdown does not apply to this block and
  `locationApplies: false` says so. Keying it by location would buy the same profile twice.
- `spamBand` is `low` (≤30) / `medium` (31–60) / `high` (>60) / **`unknown`**. Unknown is its
  own band, never green: a link DataForSEO has not scored has not been found clean.
  `spam.targetScore` is `null` (not 0) when the summary reports none. **The spam data costs
  zero extra calls** — `backlink_spam_score` rides on every backlink row and
  `backlinks_spam_score` on the summary; both were already being paid for by the Backlinks
  sync and never read.
- `state: "setup"` when the credentials are missing — `DataForSEOBacklinksConnector.__init__`
  **raises** (unlike the domain-overview connector, which returns an error dict), so it is
  constructed inside a try. `state: "empty"` when DataForSEO indexes no backlinks for the
  target; the section is never silently hidden.
- A URL target fetches for the exact page: host lowercased, `www.` stripped, path preserved
  case-sensitively.

### `POST /api/domain-overview/report`

Body `{"target", "location", "project"}` → **`application/pdf`** as an attachment. The **first
non-JSON endpoint in `apps/api`**: it returns a plain `django.http.HttpResponse`, not a DRF
`Response`, so renderer negotiation is bypassed (JSONRenderer would otherwise be handed PDF
bytes). Template: `templates/reports/domain_overview.html`.

**It reads the 24-hour caches and NEVER triggers a backlink fetch.** Generated straight after
a lookup it costs $0. A section that was never loaded prints "Backlinks not loaded for this
report". The one exception: an expired *keywords* cache lets it make the single Labs call the
Analyze button would have made — reported in the PDF and in the **`X-Report-Fetched`** header
(`keywords`, or empty when nothing was bought).

Prompts are free: `run_prompt_research` template-expands the top 5 keywords with no external
call, labelled "Suggested prompts" with volume printed as *not measured*. A project's stored
`AIPrompt` rows are added only when the target resolves via `normalize_domain` to a registered
project. Tables cap at 25 keywords / 25 backlinks / 15 anchors with a caption naming the true
total.

Rendered by whichever engine `load_pdf_renderer()` resolves first — **WeasyPrint**, else
**xhtml2pdf** (pure Python, no system libraries). Both imports are lazy. The chosen engine's
name is passed to the template, which branches on it for the page footer; see
`.claude/tech-stack.md` §7.

**501** `{"detail": "No PDF engine is available — …"}` only when **both** engines fail to
import, which should not occur after `pip install -r requirements.txt`. **400** on a missing
target.

### `POST /api/live-serp`

Body `{"keyword": "...", "location": "United States"}`. Missing keyword → **400**.

Calls DataForSEO `serp/google/organic/live/advanced` at depth 15, filters to `type == "organic"`.
Cached 24 hours under `live_serp_<keyword>_<location>`.

**Response** `{"status":"ok","keyword","items":[{position,url,title,domain}],"cost"}`
or `{"status":"error","error":"..."}` at 200.

---

## 9. External integrations

### Google — OAuth2 (`pipeline/utils/auth.py`)

Scopes: `webmasters.readonly`, `analytics.readonly`, `adwords`. Credentials are rebuilt from
`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN` and auto-refreshed;
a `RefreshError` is re-raised with instructions to run
`python pipeline/utils/auth.py --generate-token`.

| Connector | API | Writes |
|---|---|---|
| `gsc` | Search Console `searchanalytics.query`, dimensions `date, country, device, page`, paginated 25 000/page | `SEODaily` (GSC columns) |
| `gsc_keywords` | Same API with the `query` dimension | `KeywordRanking` |
| `gsc_pages` | Same API, page-level | `Page` |
| `url_inspection` | Search Console URL Inspection API | `IndexingStatus` |
| `gsc_property` | `sites.list` — resolves the *real* property form | *(helper, no writes)* |
| `ga4` | GA4 Data API `runReport` ×2 | `SEODaily` (GA4 columns) + `GA4TrafficSourceDaily` |
| `pagespeed` | `https://www.googleapis.com/pagespeedonline/v5/runPagespeed` | `PageSpeed` |
| `google_ads` | Google Ads API (requires Standard Access) | `AdMetricDaily` |

Behaviours worth knowing:

- **GSC is incremental.** It reads `MAX(SEODaily.date)` and fetches only newer dates.
  It also queries under the resolved *property* URL but stores rows under the canonical
  `Site.site_url` — mixing the two once filed 47 k rows under an unread key.
- **`gsc_property.resolve_gsc_property()`** exists because `add_site` defaults `gsc_property` to
  a bare domain, which the API interprets as the `http://` URL-prefix property and 403s. It
  matches the stored value against the account's real property list and repairs the `Site` row.
- **GA4 requires a per-site property id.** When a `Site` row exists without `ga4_property_id`,
  the connector raises rather than falling back to `.env` — the fallback once wrote 6 654 rows of
  one site's data under another site's id.
- GA4 sends **one batched request per report** to conserve its 14 000-token/hour quota.
- **`pagespeed` measures every known page, mobile only, stalest first.** Order is: never
  measured → longest since measured → most clicks → url. Staleness outranks traffic so that a
  site larger than one run's budget is covered *across consecutive runs* and then rotates —
  ordering by clicks alone would re-measure the same head forever and leave the tail with no
  score, permanently. A newly published page, having no score at all, is first in line on the
  next run. **No content-type filter**: excluding `/blog` URLs was considered and rejected on
  the data — it would still have left 792 of premierstaff's 1 139 pages, so it never solved the
  scale problem it was proposed for, while hiding 23% of that site's clicks and quietly turning
  "site health" into "health of the pages we chose to measure". Its bound is
  `RUN_BUDGET_SECONDS` (1 800 s, checked before each request), not a page quota, so covering
  more pages costs coverage inside the budget and never more wall-clock — which is what lets
  `apps/sync/scheduling.py` size the 2 h orphan-reaper against it. Three earlier limits made it
  measure 15 pages of a 55-page site and are worth not reintroducing: a `WHERE clicks > 0` pool
  that made "has traffic already" a condition of ever being audited; a `limit=15`; and a second
  scan of every page at `strategy="desktop"` that nothing reads — every consumer filters
  `strategy == "mobile"` (`site_audit_service` ×3, `overview_service`), so half of each run's
  time bought rows no screen displays. Truncation by budget, truncation by
  `MAX_PAGES_PER_RUN`, and URLs PSI could not score are each logged with a count; none of them
  is silent, because on Site Audit an unmeasured page and a healthy page look identical.

### DataForSEO — HTTP Basic, base `https://api.dataforseo.com/v3`

| Connector / caller | Endpoint | Writes |
|---|---|---|
| `dataforseo_keywords` | `keywords_data/google_ads/search_volume/live`, `dataforseo_labs/google/bulk_keyword_difficulty/live`, `.../keyword_overview/live`, `.../keyword_ideas/live`, `.../related_keywords/live`, `.../keyword_suggestions/live` | `KeywordRanking` (volume/CPC only — never positions) |
| `dataforseo_serp` | `serp/google/organic/task_post` → `task_get/regular/{id}` | `KeywordRanking` positions |
| `dataforseo_serp_competitors` | Same task_post/task_get pair | `CompetitorKeywordRanking` |
| `dataforseo_labs_competitors` | `dataforseo_labs/google/competitors_domain/live` | `CompetitorDomain` |
| `dataforseo_backlinks` | `backlinks/backlinks/live` | `Backlink` |
| `dataforseo_onpage` | `on_page/task_post` → `on_page/summary/{id}` → `on_page/pages` | `TechnicalIssue` |
| `dataforseo_ai_keywords` | `ai_optimization/ai_keyword_data/keywords_search_volume/live` (max 1 000 keywords/call) | `AIKeywordData` |
| `dataforseo_opportunities` | `dataforseo_labs/google/ranked_keywords/live` | `KeywordRanking` — **not in any scope**, unreachable from the UI |
| `dataforseo_domain_overview` | `dataforseo_labs/google/ranked_keywords/live` | *(none — request-scoped, 24 h cache)* |
| `dataforseo_live_serp` | `serp/google/organic/live/advanced` | *(none — request-scoped, 24 h cache)* |
| `pipeline/services/backlinks_service` | `backlinks/summary`, `backlinks/referring_domains`, `backlinks/anchors`, `backlinks/history` | `BacklinksSnapshot` JSON blob |

`pipeline/services/backlinks_service._post` books every one of those four calls to
`connector_costs` under the name **`dataforseo_backlinks_live`** with `units: None`. It recorded
nothing at all until 2026-08, so the Backlinks page's Refresh spent real money that Settings →
Usage & Budget never showed and that never counted towards the monthly cap. The name is
deliberately *not* `dataforseo_backlinks` (the per-backlink connector, which records real
`units`): one name for both would divide two connectors' cost by one connector's unit count.
`units` is None because the four endpoints meter four different things.

`dataforseo_backlinks.fetch(site_id, limit, dofollow_only)` — `limit` defaults to
`sync_limit_for(site_id)`, i.e. `ProjectSettings.data["backlinksSyncLimit"]` (250/500/1000,
default **1000**, out-of-range values ignored), read through `mutation_state` rather than a
Settings group so an unrelated Settings save cannot wipe it. Domain Overview passes
`limit=100, dofollow_only=False`.

Every DataForSEO response wraps results as `tasks[0].result[0]`; a `task.status_code != 20000`
is treated as an error. Costs are read from `task.cost` where the caller surfaces them.

**Which keywords cost money:** the paid per-keyword connectors read
`pipeline/utils/keywords.load_tracked_keywords(site_id, location=…, site_pk=…)`, which returns
**that project's** `SavedKeyword` rows (falling back to a legacy `keywords.txt` only when the DB
has none and the call is unscoped). This is why "Track" in the Keyword Explorer is the control
that governs API spend — and why `site_pk` is not optional in practice: several projects share
one `site_url`, so an unscoped call bills one project for every sibling's keywords. Connectors
read it off `self.site_pk`, which `sync_engine` stamps before each run.

### OpenAI

`pipeline/services/ai_summary_service.generate_ai_summary(site_id)` posts to
`https://api.openai.com/v1/chat/completions` with model **`gpt-4o-mini`**, `temperature=0.3`,
`max_tokens=800`, 30 s timeout. The prompt embeds the site's 30-day KPIs, up to 5 high-severity
technical issues, and backlink live/lost counts, and demands an exact Markdown shape:
`# 🔴 Critical Issues`, `# 🟢 Key Wins`, `# ℹ️ Summary`.

The result is upserted into `AISummary` keyed on the current ISO week start, and surfaced as
`overview.summary`. **Without `OPENAI_API_KEY` the function logs a warning and returns** — the
Overview summary block is simply absent.

### Email (SMTP)

Django's `send_mail`, configured from `EMAIL_*`. When `EMAIL_HOST_USER` is empty and the backend
is still SMTP, `base.py` swaps in the console backend so development never fails with
`ConnectionRefused`. Both invitation paths call `send_mail(..., fail_silently=False)` inside a
try/except that logs a warning — the API always reports success.

### Unwired connectors

`meta`, `linkedin`, `webflow`, `wordpress`, and `sitemap` are registered in the connector factory
but only `sitemap` appears in `ALL_CONNECTORS`. Meta/LinkedIn/Webflow/WordPress are reachable
from no scope and no UI action.

**Not integrated at all:** Stripe, Clerk, or any payment/identity provider. Authentication is
entirely Django's.

---

## 10. Endpoint → page map

| Endpoint | Frontend page(s) |
|---|---|
| `GET /projects` | Topbar site selector, Position Tracking list |
| `POST /projects` | Topbar "Add a site", Position Tracking wizard |
| `DELETE /projects/<slug>` | Position Tracking workspace (currently broken) |
| `DELETE /projects/<slug>/data` | Settings → General → Danger zone (currently broken) |
| `/overview` | Overview |
| `/seo` | SEO Performance |
| `/keywords` (GET/POST/PUT) | Keywords, Keyword Explorer, Position Tracking wizard/edit |
| `/positions` | Position Tracking |
| `/alerts` | Alerts + the sidebar unacknowledged badge (prefetched on every project change) |
| `/backlinks` | Backlinks |
| `/audit` + `/audit/toggle-check` + `/audit/toggle-resolved` + `/audit/toggle-page-resolved` | Site Audit |
| `/offsite` | Off-site SEO |
| `/ads` + `/ads/{status,budget,negatives,promote}` | Paid Overview, Campaigns, Search Terms, Attribution |
| `/ai` + `/ai/<action>` | AI Optimization |
| `/settings` (GET/PUT), `/team`, `/invite*` | Settings (all 8 sub-tabs) |
| `/auth/password` | Change-password modal (sidebar) |
| `/auth/invite-status`, `/auth/accept-invite` | Accept-invite modal (`#/accept-invite?token=…`) |
| `/sync`, `/tasks/<id>` | Topbar Refresh buttons, per-page fetch buttons, Settings run-now buttons |
| `/research` | Keywords → Keyword Explorer |
| `/prompt-research` | AI Optimization → Prompts → Prompt Explorer |
| `/domain-overview` | Domain Overview (`include: ["backlinks"]` behind its own Load backlinks button) |
| `/domain-overview/report` | Domain Overview → Download PDF (returns `application/pdf`) |
| `/live-serp` | Position Tracking → workspace → SERP drawer |
