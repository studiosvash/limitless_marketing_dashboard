# Skills — Onboarding Guide for AI Coding Assistants

> Read this before writing any code in this repository. It is written for you, not for end users:
> it explains how the codebase is organised, which patterns are load-bearing, and which mistakes
> this project has already made and fixed. Companion docs: `api-reference.md` (endpoints),
> `features.md` (product behaviour), `design.md` (UI tokens), `tech-stack.md` (dependencies).

---

## 1. Project in one paragraph

An internal SEO / paid-media intelligence dashboard for a 2–3 person team. A Django + DRF backend
serves a single-page frontend that is assembled server-side from HTML fragments and driven by a
bundled React runtime. All page data comes from two local SQLite databases. External APIs
(Google Search Console, GA4, PageSpeed, DataForSEO, OpenAI, optionally Google Ads) are called
**only** by a background sync triggered from a Refresh button, plus three explicit
user-initiated lookup endpoints.

---

## 2. The rules that actually matter

These are ordered by how expensive it is to get them wrong.

**1. Never call an external API from a page-data endpoint.** Pages read SQLite and return
instantly. The whole product contract rests on this. The three sanctioned exceptions are
`/api/research`, `/api/domain-overview` and `/api/live-serp` — explicit user lookups, not page
renders. (`/positions` used to violate this by backfilling missing keyword volume via a billable
DataForSEO call on every render; it was removed on 2026-07-27 — the `dataforseo_keywords`
connector in the positioning sync scope already writes that data. A keyword with no stored volume
now reports `null` and is counted in the response's `volume_coverage`.)

**2. Every API view needs `@method_decorator(login_not_required, name="dispatch")`.**
`LoginRequiredMiddleware` runs before DRF, so without it a token-authenticated request is 302'd
to the login page instead of reaching your view. This is the single most common mistake in this
codebase.

**3. Never fabricate data to fill a shape.** When a data source does not exist, return an honest
empty list, `null`, or a `state: "setup"` marker — and say so in a comment. Multiple existing
modules carry docstrings recording where a previous version faked a number and what broke.
Where placeholders do exist (Backlinks link rows, AI share-of-voice, Ads pacing), they are
flagged in `features.md` §17; do not add more.

**4. Analytics writes are always upserts.** Use the helpers in `pipeline/db/writer.py`, which
issue `sqlite_insert(...).on_conflict_do_update(...)`. Never a bare `INSERT`. Batch at 60–80 rows
to stay under SQLite's ~999 bound-parameter ceiling.

**5. Secrets come from the environment.** Read via `settings` or `os.getenv`. Never hardcode,
never log, never commit `.env`.

**6. Service functions do not raise.** They catch, log with
`logging.getLogger(__name__).error(..., exc_info=True)`, and return a safe empty shape of the
right type. That is why API views rarely need try/except.

**7. One concern per file.** A view resolves and delegates; a service computes; a connector
fetches; a writer persists. Do not fetch in a view or compute in a template.

---

## 3. Architecture map

```
Browser
  │  Bearer token, JSON
  ▼
apps/api/views.py ─── resolve_project_or_404(slug) ─► Site.site_url  ("site_id")
  │
  ├─► apps/dashboard/services/<page>_service.py     # all business logic
  │        │
  │        ├─► pipeline/utils/db_connection.get_session()  ─► fusehealth.db (SQLAlchemy)
  │        └─► Django ORM                                  ─► django_internal.db
  │
  └─► apps/dashboard/services/sync_api_service.start_sync_run()
           └─► thread ─► pipeline/services/sync_engine.sync_all|sync_page
                              └─► pipeline/connectors/*.sync()
                                       ├─► external API
                                       ├─► pipeline/db/writer.upsert_*  ─► fusehealth.db
                                       └─► apps.sync.SyncLog            ─► django_internal.db
```

**The one identifier you must understand:** the URL carries `Site.slug` (`"fusehealth"`), but
everything below the view layer uses `Site.site_url` (`"sc-domain:fusehealth.com"`) as the
`site_id` string. It is the join key across both databases. `resolve_project_or_404(slug).site_url`
is the conversion, and every slug-taking view calls it as its first statement.

Because nothing enforces which spelling of a site gets written, **four** appear in the analytics
tables for the same site:

```
premierstaff.com                 <- sites.site_url, what every view resolves a slug to
sc-domain:premierstaff.com       <- Search Console domain properties
https://premierstaff.com/        <- Search Console URL-prefix properties, and whatever a
https://premierstaff.com            connector happened to be handed the day it ran
```

**`pipeline/utils/site_ids.resolve_site_ids(site_id)` is the one matcher.** It expands a site_id
into every spelling it could have been stored under, exact input first. Call it whenever you
query an analytics table:

```python
from pipeline.utils.site_ids import resolve_site_ids
... .where(Model.site_id.in_(resolve_site_ids(site_id)))
```

`ads_service`, `offsite_service`, `backlinks_service`, `site_audit_service` and `ai_service` each
keep a thin `_resolve_site_ids` / `_site_id_variants` wrapper that delegates to it. They used to
carry five separate copies that knew only the `sc-domain:` prefix — see §9.

**`www.x.com` and `x.com` ARE one site (changed 2026-08-02; this file previously said the
opposite).** The same module exposes the registration rule:

```python
from pipeline.utils.site_ids import normalize_domain
normalize_domain("https://www.premierstaff.com/careers")   # -> "premierstaff.com"
```

`normalize_domain()` strips the scheme, `sc-domain:`, a leading `www.`, any path, port, trailing
dot and trailing slash, and lowercases. `add_site()` stores its output as `sites.site_url` and
dedupes on it, so a site cannot be registered twice under two spellings. `resolve_site_ids()`
expands to **both** hosts, so rows written under the www spelling before this rule existed stay
readable — this was a read-side widening, not a data rewrite.

The old rule (Search Console models `www.x.com` and `x.com` as separate properties, so merging
could cross-attribute traffic) was correct in the abstract and wrong in practice: the registry
let one site be added twice, producing two projects, two slugs, two sync budgets, two halves of
one history, and a project switcher offering a choice between them. No domain in this product
serves different content on the two hosts.

Two functions, two questions — don't swap them:

| Function | Question it answers | `https://www.x.com/` → |
|---|---|---|
| `canonical_domain()` | *Which host is this string?* — right for matching against a GSC property list | `www.x.com` |
| `normalize_domain()` | *Which site is this?* — right for registration, dedup, comparing to `Site.site_url` | `x.com` |

Projects registered before the rule keep their old `site_url` until
`python manage.py normalize_site_urls --apply` runs (dry-run by default; it moves the
`site_url`-keyed Django rows with them and refuses to merge two projects for one site).

---

## 4. The data model

### `django_internal.db` — Django ORM, `manage.py migrate`

| Model | App | Purpose |
|---|---|---|
| `User`, `Session`, `Token` | contrib / authtoken | Auth |
| `UserProfile` | accounts | `user` (1-1), `role`. Auto-created by a `post_save` signal. |
| `UserInvitation` | accounts | `email`, `role`, `invited_by`, `token`, `created_at`, `expires_at`, `is_accepted` |
| `Insight` | dashboard | Team-entered qualitative context. Admin-only; **no API or UI surface.** |
| `AITarget` | dashboard | One per site: `brand`, `aliases[]`, `competitors[]`, `setup_done` |
| `AIPromptList` | dashboard | Named prompt group |
| `AIPrompt` | dashboard | `text`, `list` FK, `tracked_models[]` |
| `ProjectSettings` | dashboard | `site_url` + a single `data` JSONField — **the app's key-value store** |
| `SyncLog` | sync | Last result per (connector, site_url): `status`, `last_synced`, `records_written`, `error_message`, `duration_seconds` |
| `RefreshRun` | sync | One refresh: `scope`, `status`, `current_connector`, `completed_count`/`total_count`, `records_written`, `error_message`, `percent` property |

**`ProjectSettings.data` holds more than Settings.** Three non-settings keys live there and must
never be clobbered by a settings save: `alertAcks` (acknowledged alert ids), `auditHidden`
(hidden audit checks), `adsOverrides` (campaign status/budget/negatives/promoted), and
`domainChecksCache`. Access them through `apps/dashboard/services/mutation_state.py`
(`get_state` / `set_state`), never directly.

### `data/fusehealth.db` — SQLAlchemy, `pipeline/db/schema.py`

Every table has a `site_id VARCHAR(255)` column. Uniqueness is enforced by explicit
`UniqueConstraint`s, which is what makes the upserts work.

| Table | Model | Unique on | Written by |
|---|---|---|---|
| `sites` | `Site` | `site_url`, `slug` | `site_service` |
| `seo_daily` | `SEODaily` | date, site_id, country, device, landing_page | `gsc` (search cols), `ga4` (analytics cols) |
| `ga4_traffic_source_daily` | `GA4TrafficSourceDaily` | date, site_id, channel, source | `ga4` |
| `keyword_rankings` | `KeywordRanking` | date, site_id, keyword | `gsc_keywords`, `dataforseo_serp` (position), `dataforseo_keywords` (volume/CPC only) |
| `pages` | `Page` | site_id, url | `gsc_pages`, `sitemap`, CMS connectors |
| `ad_metrics_daily` | `AdMetricDaily` | date, site_id, platform, campaign | `google_ads` |
| `backlinks` | `Backlink` | site_id, referring_domain, target_url | `dataforseo_backlinks` |
| `backlinks_snapshot` | `BacklinksSnapshot` | site_id (PK) | `manage.py refresh_backlinks` |
| `competitor_visibility` | `CompetitorVisibility` | date, site_id, competitor_domain | *(unwritten)* |
| `competitor_domains` | `CompetitorDomain` | site_id, competitor_domain | `dataforseo_labs_competitors` |
| `competitor_keyword_rankings` | `CompetitorKeywordRanking` | date, site_id, keyword, competitor_domain | `dataforseo_serp_competitors` |
| `tracked_competitors` | `TrackedCompetitor` | **site_pk**, competitor_domain | `competitor_service` (user override) — per-PROJECT, like `saved_keywords` |
| `technical_issues` | `TechnicalIssue` | site_id, url, issue_type | `dataforseo_onpage`, `technical_issues_service` |
| `page_speed` | `PageSpeed` | site_id, url, strategy | `pagespeed` |
| `indexing_status` | `IndexingStatus` | site_id, url | `url_inspection` |
| `seo_aggregates` | `SEOAggregate` | site_id, period_type, period_start | `aggregate_service` |
| `ai_summaries` | `AISummary` | week_start, site_id | `ai_summary_service` |
| `ai_keyword_data` | `AIKeywordData` | date, site_id, keyword | `dataforseo_ai_keywords` |
| `llm_mention_metrics` | `LLMMentionMetric` | site_id, week_start, subject_domain, platform | `dataforseo_llm_mentions` |
| `llm_cited_pages` | `LLMCitedPage` | site_id, week_start, url | `dataforseo_llm_mentions` |
| `saved_keywords` | `SavedKeyword` | **site_pk**, site_id, keyword, location | `saved_keyword_service` — **the tracked-keyword list** |
| `anomalies` | `Anomaly` | date, site_id, metric_type | `anomaly_service` |
| `comparative_metrics` | `ComparativeMetrics` | site_id, metric_type, week_start | *(unwritten)* |
| `metric_forecasts` | `MetricForecast` | site_id, metric_type, period_type, target_date, model_name | *(unwritten — designed, never built)* |
| `keyword_opportunities` | `KeywordOpportunity` | site_id, keyword | *(unwritten)* |
| `risk_signals` | `RiskSignal` | — | *(unwritten)* |

**`SavedKeyword` is the money table.** `pipeline/utils/keywords.load_tracked_keywords()` reads
it, and the paid per-keyword DataForSEO connectors read that. Adding rows here increases API
spend; that is why the UI gates it behind an explicit "Track" action.

**It is the one analytics table keyed by PROJECT, not by domain.** `saved_keywords.site_pk` is
the owning `sites.id`. Every read and write of it takes a `site_pk` and every caller that has a
project must pass one — `list_saved_keywords`, `save_keywords`, `clear_saved_keywords`,
`delete_saved_keyword`, `load_tracked_keywords`, `keywords_needing_backfill`. Use
`saved_keyword_service.project_scope(site_id, site_pk)` to build the WHERE clause rather than
writing your own: with a `site_pk` it scopes on that **alone** (the project id already implies
the domain, and ANDing `site_id` hides rows filed under another spelling of it — §3), and
without one it falls back to `resolve_site_ids`. See the §9 trap for what an unscoped read did.

**`llm_mention_metrics` counts are not comparable across different competitor sets.** A live
cross-aggregation call for the same domain returned 20 mentions when the project tracked 1
competitor and 1 mention when it tracked 3. This is DataForSEO's real attribution behaviour, not
a bug — share-of-voice is inherently a share *within the queried competitive set*, so adding or
removing a competitor changes the denominator the API attributes mentions against. It is the
correct reading of "share of voice," but it means `sov.rows` from two weekly snapshots are only
directly comparable if `AITarget.competitors` did not change between them — check that before
reading a week-over-week `sov.delta` as a real trend.

`technical_issues` is **rebuilt wholesale** after every GSC/GA4 sync
(`rebuild_technical_issues` deletes then re-inserts), so its primary keys are not stable. That is
why alert acknowledgement keys technical items on a SHA-1 of `(url, issue_type)`.

### Changing the analytics schema

Django migrations do **not** cover `fusehealth.db`. Options, in order of preference:

1. **New table** — add the model to `schema.py`; `init_db()` creates it, and
   `ensure_tables(session, Model)` will self-provision it on first use in an existing database.
2. **New nullable column** — add it to the model, then write a guarded one-off management command
   using `PRAGMA table_info` + `ALTER TABLE` (copy
   `apps/sync/management/commands/add_project_fields.py`).
3. **Anything else** — you are writing a migration script by hand. Think first.

---

## 5. Backend patterns

### Adding an API endpoint

1. **Route** — add to `apps/api/urls.py`. No trailing slash. Name it `resource-action`.
2. **View** — a plain `APIView` in `apps/api/views.py`:

```python
@method_decorator(login_not_required, name="dispatch")
class ProjectThingView(APIView):
    def get(self, request, slug):
        site_id, curr_start, curr_end, prev_start, prev_end = resolve_range_periods(request, slug)
        return Response(build_thing_response(site_id, curr_start, curr_end, prev_start, prev_end))
```

   Use `resolve_range_periods(request, slug)` for a range-aware endpoint; use
   `resolve_project_or_404(slug).site_url` when there is no period concept.
   **Views contain no business logic** — resolve, delegate, return.

3. **Service** — `apps/dashboard/services/<page>_service.py`, exposing:
   - `query_*_raw(...)` — one DB read each, returning primitives, wrapped in try/except.
   - `build_*_response(...)` — assembles the exact JSON the frontend reads.
4. **Test** — `apps/api/tests/test_<page>.py`, using the temp-DB fixture from §8.
5. **Document** — add the endpoint to `api-reference.md`.

### Adding a mutation

```python
@method_decorator(login_not_required, name="dispatch")
class ThingActionView(APIView):
    def post(self, request, slug):
        from apps.dashboard.services.thing_service import do_thing   # lazy: avoids a cycle
        site_id = resolve_project_or_404(slug).site_url
        value = (request.data.get("value") or "").strip()
        if not value:
            return Response({"detail": "value is required"}, status=400)
        return Response({"ok": True, "result": do_thing(site_id, value)})
```

Rules: validate explicitly and return `{"detail": "..."}` with a 4xx; make it **idempotent**
(the frontend fires bulk actions in parallel); persist first-party state through
`mutation_state.get_state/set_state`; return a minimal ack, because the SPA always refetches.

### Adding a connector

1. Subclass `BaseConnector` in `pipeline/connectors/`:

```python
class MyConnector(BaseConnector):
    name = "my_source"                       # the SyncLog key

    @with_retry(max_retries=3, base_delay=5.0)
    def fetch(self, site_id: str | None = None, **kw) -> list[dict]:
        ...                                  # raise on unrecoverable failure

    def _write_records(self, session, records, site_id=None) -> int:
        return upsert_my_table(session, records, site_id=site_id)
```

   `BaseConnector.sync()` handles timing, the `SyncLog` row, and the success/error envelope.
   **Never override `sync()`.**

2. Register it in `sync_engine._get_connector`'s `connector_map`.
3. Add it to the relevant `PAGE_CONNECTORS` scope and/or `ALL_CONNECTORS`.
4. Add an `upsert_*` helper to `pipeline/db/writer.py` if the table is new.

A connector that cannot be constructed (missing credentials) returns `None` from the factory and
is **skipped silently** — the run still completes. Raise inside `fetch()` if you want a visible
error instead.

### Where things live

| Need | Location |
|---|---|
| A new page's data logic | `apps/dashboard/services/<page>_service.py` |
| A query two pages share | `apps/dashboard/services/shared_queries.py` |
| First-party per-project state | `ProjectSettings.data` via `mutation_state` |
| A period calculation | `pipeline/utils/period_utils.py` |
| A DB write | `pipeline/db/writer.py` |
| An external call | `pipeline/connectors/` |
| A derived-from-owned-data computation | `pipeline/services/` |

---

## 6. Frontend patterns

### The mental model

There is one React component. `state` is one object. `renderVals()` runs on every render and
returns one object; every `{{ … }}` in every template reads from it. Files in `js/pages/` are
**not modules** — they are spliced into `renderVals()`'s body by the `#include` preprocessor and
start mid-scope with `if (tab === 'x') { … }`.

Available inside a `js/pages/*.js` file: `s` (state), `tab`, `data` (the cached response for the
current tab), `vals`, `project`, and `this` (the component). Nothing is imported.

### Adding a page

1. `static/spa/src/pages/<name>.html` — the fragment, wrapped in
   `<sc-if value="{{ showName }}">`.
2. `static/spa/src/js/pages/<name>.js` — the view model:

```js
    /* ============ NAME ============ */
    if (tab === 'name') {
      vals.showName = true;
      const setup = !data || !data.kpis || data.kpis.total === 0;
      if (setup) { vals.nm = { setup: true, rows: [] }; return vals; }
      vals.nm = { /* …every value and style the template reads… */ };
    }
```

3. Add both `#include` directives — the HTML in `index.html`'s `<main>`, the JS at the bottom of
   `app.js`'s `renderVals()`.
4. Register the tab in `app.js`: `VALID`, `RES` (tab → API resource), the `titles` map, and
   `SEOTABS`/`ADSTABS` if it belongs to a group.
5. Add a nav entry in `components/sidebar.html` plus `navStyle` / `dotStyle` / `h.navName`.
6. Add a sync scope to `tabToScope` / `tabToLabel` if the page has its own refresh.

### Data fetching

`fetchTab(tab, pid, range, force)` is the only fetch path. It keys the cache as
`pid:tab[:range]` (range only for range-aware tabs), sets `loading`, calls
`FuseAPI.get('/api/projects/' + pid + '/' + this.RES[tab], params)`, and stores the result.

After a mutation, drop the affected keys and refetch:

```js
this.setState(s => {
  const cache = {};
  Object.keys(s.cache).forEach(k => { if (k.indexOf(pid + ':ads') !== 0) cache[k] = s.cache[k]; });
  return { cache };
});
this.fetchTab(this.state.tab, pid, this.state.range, true);
```

### Forms

There is no form library and no `<form>` element in the SPA. A field is a controlled input:
`value="{{ x }}"` + `onInput`/`onChange` writing to state. Multi-field forms keep a **draft**
object in state (`wsDraft`, `notifDraft`, `aiDraft`, `dataDraft`, `teamDraft`, `crawlCfg`),
seeded from the fetched data on first load of that tab and submitted whole by a Save button that
flips its label to `Saved ✓`. Validate in the handler before calling the API; show errors as
inline state (`addSiteError`, `createUserError`, `cpwMsg`).

### Tables

Build rows in `renderVals()` — every cell value **and** every cell style pre-computed. Sorting
uses `this.sortRows(rows, sort)` plus `mkSortHandler(stateKey, key)` and `arrow(sort, key)`.
Filtering is plain `Array.filter` over the cached data. Selection is an array of ids in state
with a `Set` for lookup.

### State conventions

- One flat `state` object; namespaced prefixes per page (`au*` audit, `ai*` AI, `pt*` positions,
  `trm*` search terms, `cmp*` campaigns, `bl*` backlinks, `res*` explorer results).
- Non-render values go on `this` directly: `_alive`, `_hist`, `_histIdx`, `_iv` (poll interval),
  `_nt` (toast timer), `_rt`/`_bt` (debounce timers).
- Guard every async callback with `if (!this._alive) return;`.
- `localStorage` holds three things: `fh_selected_project`, `fh_keyword_lists`, and the
  per-project search histories `fh_kw_hist_<pid>` (Keyword Explorer) / `fh_do_hist_<pid>`
  (Domain Overview). The two histories share a shape and a purpose — replay a past search
  without re-billing DataForSEO — and the Domain Overview one stores the whole response
  payload, because the server's 24-hour cache is Django's default LocMemCache and therefore
  per-process and lost on restart. Anything storing a payload needs the quota-shedding
  retry `doHistSave` uses: these values are large enough that `QuotaExceededError` is a real
  outcome, and it would otherwise be thrown inside `setState`.

---

## 7. Auth & permissions

**In the backend:**

```python
if not check_owner_admin(request.user):     # blocks Analyst
    return Response({"detail": "…requires Owner or Admin access."}, status=403)

if not check_owner_only(request.user):      # blocks everyone but Owner
    return Response({"detail": "Only the Owner can …"}, status=403)
```

Both return `True` for an unauthenticated user and hard-allow `user.id == 1` or a username of
`founder`/`owner`. **These are UI guards, not a security boundary** — do not rely on them to
protect anything that matters.

**In the frontend:** the role arrives via the injected bootstrap as
`window.FuseAPI.config.user.role` and surfaces as `vals.userRole` / `vals.canManageSettings`.
Gate nav items with `<sc-if value="{{ canManageSettings }}">` and add a server-side check too.

**Do not extend the legacy role system.** `apps/accounts/models.Role` (`founder`/`seo`/`ads`),
`ROLE_PAGE_ACCESS`, and `apps/accounts/decorators.role_required` are dead — no live caller uses
them, and `UserProfile.role` actually stores `Owner`/`Admin`/`Analyst`, which are outside the
declared choices. Use the live vocabulary.

---

## 8. Testing

Run: `python manage.py test` (a specific module: `python manage.py test apps.api.tests.test_overview`).

**The analytics-DB fixture — copy this verbatim:**

```python
class MyEndpointTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url="sc-domain:example.com", site_name="Example",
                             slug="example", is_active=1))
            # … seed the rows your assertions depend on …

        user = get_user_model().objects.create_user("tester", password="x")
        token = Token.objects.get(user=user)          # created by the post_save signal
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
```

Resetting `_SessionFactory` is mandatory — it is a module-level singleton and will otherwise leak
the previous test's database.

**What to test:** every top-level key of the response shape; that numbers reflect seeded data;
that unbuilt features report `setup` rather than a fake value; that an unknown slug 404s; that
the default range is 30d; that mutations persist and are idempotent.

**Watch the period arithmetic.** The current window is anchored to the *latest data date* and
ends the day before it, so the newest seeded row is intentionally excluded. Seed two rows and
assert against the older one — `test_overview.py` explains this in a comment.

Never call a real external API from a test. Inject a fake object
(`pipeline/connectors/tests/test_gsc_property.py` shows the pattern).

---

## 9. Things that will bite you

Each of these is a real bug that was found and fixed. Do not re-introduce them.

| Trap | Why it matters |
|---|---|
| Missing `@login_not_required` on an API view | Token requests get 302'd to `/login/`, not 401'd |
| `html.replace("<head>", …)` in `spa_views` | The literal string `<head>` also appears inside a JS string in the SPA; a blanket replace corrupts the script. Insert by **position** using `str.index()` |
| Setting `FuseAPI.config` once | `app/api.js` executes **twice** (parse + `<helmet>` relocation) and reassigns `window.FuseAPI` each time. Hence the `defineProperty` interceptor |
| `config.baseUrl = ''` | Empty string is falsy, so the transport silently falls through to fixture data forever. It must be `'/'` |
| Acking alerts by database id | `technical_issues` rows are rebuilt after every sync and their PKs change. Key on a content hash |
| Falling back to `.env` `GA4_PROPERTY_ID` when a `Site` row lacks one | Once wrote 6 654 rows of one site's data under another site's id. Fail loudly instead |
| Storing GSC rows under the queried *property* URL | The property and the canonical `site_url` differ for `sc-domain:` sites; once filed 47 k rows under a key no page reads |
| `default=list` on a `JSONField` in `apps/dashboard/models.py` | `AIPrompt` has a field literally named `list`, which shadows the builtin for the rest of the class body. Use `_empty_list` / `_empty_dict` |
| `round(None, 1)` on an aggregate | `avg(position)` returns `NULL` when every row is null. Guard before rounding |
| `.where(pd.notna(df), None)` on a float column | pandas silently reverts `None` to `NaN`. Cast with `.astype(object)` first |
| Reading `request.data.get("models")` for prompt config | The SPA nests it as `{cfg: {models: …}}`; the flat read wiped `tracked_models` on every save |
| Comparing `SyncLog.status` to `"ok"` | The real values are `never|running|success|error` |
| A 404 from `GET /api/tasks/<id>` | The SPA polls at 500 ms and treats any non-2xx as fatal. Unknown ids must return `{done: true}` |
| Building a segment list from a different slice than the table | A tab can then show a count with no matching rows. Union the segments into the table set |
| Dropping an explicit `None` in `_update_django_sync_log` | Stale error text stuck to successful rows forever |
| Assuming "Refresh all" runs everything | `ALL_CONNECTORS` deliberately **excludes** `google_ads`, `google_ads_search_terms` and `meta`. Only the `ads` scope runs them — check the list before promising a button refreshes something |
| Taking the audit snapshot before `rebuild_technical_issues` | The snapshot stores that crawl's issue counts, so ordering it first permanently freezes the **previous** crawl's numbers into history |
| `all([])` is `True` | An empty domain-check list silently scored HTTPS 100/100. Guard the empty case before treating an all-pass as a pass |
| `import sqlalchemy.dialects.sqlite` | Breaks Postgres outright. Use `pipeline/db/dialect.py` — `upsert_insert()`, `max_batch_size()`. Same for `strftime()` (SQLite-only) and `date_trunc()` (Postgres-only): bucket in Python instead |
| `PRAGMA table_info` in a migration | A syntax error on Postgres. Use `sqlalchemy.inspect()` to ask the connected dialect what columns exist — see `ensure_site_columns()` |
| Formatting numbers in a `query_*_raw` / shared helper | `_get_keywords_overview` formatted position as `f"{avg:.0f}"` before any caller saw it, so 8.4 arrived as 8 irrecoverably and the column sorted as text (`"1,234" < "9"`). Return raw numbers; format at the edge |
| Coercing an absent value to `0` | Zero and unknown are different facts. `None` position, `None` volume, `cost_per_unit: None` when no units were recorded — all deliberate. The Keyword Explorer broke this in three places on one path (`_parse_idea_item`, `_to_spa_row`, `_enrich_expanded_row`) while the tracked-keywords path beside it stayed honest, so the same column asserted a measured `0` for one row and printed an em dash for another. It was not only cosmetic: the volume-min filter read `r.volume >= s.resVolMin`, and JS coerces `null` to `0`, so every unknown-volume keyword vanished from "101+" as though it had been measured and found empty. **A filter must exclude only values that were actually tested** — an unknown fails no numeric comparison |
| `.fillna(0)` as the guard on a division | `fillna` sees `0/0 → NaN` but **not** `n/0 → ±inf`. `keywords_service` computed `(clicks / impressions * 100).fillna(0)`, and a keyword with clicks and zero impressions is routine (Search Console withholds sub-threshold impression rows while still reporting the click) — the resulting `inf` flowed into the `ctr < 2.0` segment comparison and into the response, where `json.dumps` emits a bare `Infinity` literal that is not valid JSON and that a strict client parser rejects, taking the whole Keywords payload down rather than one cell. Mask non-finite values to unknown (`_safe_ctr`); never to `0`, which is a fabricated measurement |
| A live API call in a page-data endpoint | Rate limits, latency, **and money**. `/positions` was billing DataForSEO on every render. Only `/research`, `/domain-overview`, `/live-serp` and `/connection-check` may call out, because a user pressed a button |
| A multi-row `insert(...).values(batch).on_conflict_do_update(...)` without deduping `batch` by the conflict-target columns first | Postgres raises `CardinalityViolation: ON CONFLICT DO UPDATE command cannot affect row a second time` and rolls back the **entire batch** if two records share a conflict key — e.g. `upsert_backlinks` conflicts on `(site_id, referring_domain, target_url)` but the connector drops `url_from`, so every site-wide footer/nav link collapsed to one key. **SQLite hides this completely** (it applies rows one at a time, so a duplicate just re-updates in place) — the whole test suite forces SQLite, so this class of bug is invisible until it hits production Postgres. Use `pipeline/db/writer._dedupe_by_keys(records, keys)` (last-occurrence-wins) before every batch |
| A NULL value in an upsert's conflict-target column | Postgres does **not** treat `NULL = NULL` as a conflict inside a unique index, so a record with a null key column bypasses `ON CONFLICT` entirely and duplicates on every sync instead of updating in place. `_dedupe_by_keys` does not fix this (it's a Postgres index semantic, not a batch-dedup problem) — open in `upsert_seo_daily` (defaults `country`/`device`/`landing_page` to `None`) and `upsert_ad_search_terms` (`campaign_id` to `None`). Needs a schema decision (sentinel value vs. a partial index) before fixing |
| A credential-save endpoint forwarding every field unconditionally | `apply_settings_update`'s credentials branch used to always pass `dataforseo_target_domain=body["credentials"].get(...) or None`, so saving *just* GSC + GA4 (the only two fields the UI ever showed) silently blanked an explicitly-configured DataForSEO target on every save. Only touch the keys actually present in the request body |
| Pasting `properties/123456789` into a GA4 property field | GA4's own admin UI displays the property with that prefix, and every request builder does `f"properties/{id}"` — storing the prefixed form doubles it to `properties/properties/123456789` and fails with `INVALID_ARGUMENT` deep inside a sync, long after the save reported success. Normalise with `pipeline.connectors.ga4.normalise_property_id()` at every write path |
| Gating a live-lookup feature behind `!kw.setup` (or any "no synced data" flag) | The Keyword Explorer is `POST /api/research` — it works identically on a project with zero synced rows, but the markup nested it inside the same `sc-if` as the measured KPI/table section, so a brand-new project hid a feature that would have worked. Only gate the sections that genuinely have nothing to show before a sync |
| A credential pre-flight check that returns a blanket 400 | `POST /.../sync` used to resolve GSC + GA4 up front and refuse the **entire** run if either was unset/wrong — so a brand-new site (GA4 is `NULL` by definition) couldn't sync anything, including scopes that touch neither credential (e.g. `backlinks`). Skip what's missing and report it in `warnings`; don't refuse the whole request |
| `threading.Thread(daemon=True)` for a 20-30 minute job inside the web worker | Dies with the worker: a `gunicorn --timeout` SIGKILL, a deploy, or (in dev) the `runserver` autoreloader restarting on the sync's own log write all silently kill it mid-run, leaving the row `running` for up to `RUN_TIMEOUT` (2h). Run it as `manage.py run_sync` in its own `subprocess.Popen` instead, and track the pid on the row so a dead process is detected directly instead of waited out |
| Deriving one connector's incremental cursor from `max(date)` over a table **two** connectors write | `seo_daily` is shared: `gsc` owns clicks/impressions/ctr/avg_position, `ga4` owns sessions/pageviews/users and leaves the GSC columns at 0. `GSCConnector._get_last_synced_date` asked for the newest row of any kind, so it read GA4's cursor. GA4's window ends **yesterday**, `gsc_safe_range` ends **today − 3** (GSC lags 3 days) — so from the first GA4 run onwards `new_start > new_end` and `fetch()` returned `[]` **forever**, logging `success, 0 records` every time. Production ran three weeks like this: `ga4` 18 324 records, `gsc` 0, every Overview KPI stuck at 0 while Keywords/Positions (fed by `gsc_keywords` → `keyword_rankings`, its own cursor) looked healthy. The cursor now filters `impressions > 0`, which is exactly "a row GSC wrote" — the Search Analytics API only returns a row because the page was served. **A `success, 0 records` SyncLog row is not proof a connector is working; check that the columns it owns are non-zero.** See `pipeline/connectors/tests/test_gsc_incremental.py` |
| Writing `apps.accounts.models.Role` (`founder`/`seo`/`ads`) into `UserProfile.role` | That vocabulary is retired (§7) and nothing enforces it: `check_owner_admin` refuses exactly one string, `"Analyst"`, so a profile stored as `"seo"` had full Admin access while the Settings team table printed a role the UI has no concept of. `seed_users` wrote those values until it was corrected to Owner/Admin/Admin, and `query_team_raw` now heals any non-`LIVE_ROLES` value to `Admin` — Admin, not Analyst, because that is the access those rows already had and a self-heal must never silently re-permission anyone |
| A test fixture that calls `tempfile.mkdtemp()` and never removes the directory | The analytics-DB fixture (§8) is copied at 58 call sites across 34 modules, each leaving a 0.5-1 MB SQLite file behind. That accumulated **29 216 directories / 16.6 GB** and filled the drive to zero bytes, at which point the suite could not run at all. Fixed centrally rather than 58 times: `config/test_runner.py` points `tempfile.tempdir` at one run-scoped directory and deletes it in `teardown_test_environment` (disposing the `_SessionFactory` engine first, or Windows keeps the SQLite handles open). New fixtures need no cleanup code — but they must not pass an explicit `dir=` |
| A page-data read matching `site_id ==` while its own date anchor matches every spelling | `views.latest_ranking_anchor` — which decides **which window the Positioning page renders** — used `resolve_site_ids()`, but all 15 ranking reads in `shared_queries` (and one in `keywords_service`) compared `site_id` exactly. Rows a connector filed under `https://x.com/` for the project registered as `x.com` moved the anchor forward while staying invisible to the queries that fill the page, so Positioning rendered **empty *because* data existed** — the most confusing failure shape there is. Both halves now go through `shared_queries._site_clause(model, site_id)`. **When you scope a read, check what scopes the window around it** |
| A site-id matcher that only knows the `sc-domain:` prefix | The join key is a string and four spellings exist (§3). Five services each carried their own two-line copy that expanded `sc-domain:` and nothing else, so a project registered as `premierstaff.com` could not see the 16 `ai_keyword_data` rows a connector had written under `https://premierstaff.com/` — the AI Optimization page rendered **completely empty over data that was already in the database**, and `saved_keywords` was split 24/16 across the two spellings. Use `pipeline/utils/site_ids.resolve_site_ids()`; do not write a sixth copy |
| `os.kill(pid, 0)` as a liveness check | POSIX-only. On Windows CPython maps **every** signal other than `CTRL_C_EVENT`/`CTRL_BREAK_EVENT` onto `TerminateProcess`, so the "is this sync still alive?" probe *kills the sync it is asking about* — and `reap_orphaned_runs()` runs on every `GET /api/sync/active`, i.e. every few seconds during a refresh. The same call raised `OSError(WinError 87)` for an unknown pid, which a bare `except Exception: return True` swallowed, so dead runs were never reaped either and sat at `running` until `RUN_TIMEOUT` (2h). `_process_alive` now prefers `psutil` (a requirement) and falls back to `OpenProcess`/`GetExitCodeProcess` on Windows. Note every reaper test mocked `_process_alive` away, which is exactly why this shipped — test the function that touches the OS |
| `.strip()` on a user-supplied keyword | Removes whitespace, not punctuation. A pasted comma-separated list split on newlines only left all 16 of one project's tracked keywords stored as `"festival staffing,"` — a different phrase, which went to DataForSEO inside the query, returned `ai_search_volume = 0` for 11 of 16, and was billed anyway. `saved_keyword_service._clean_row` now strips leading/trailing list separators; a comma **inside** a phrase (`"austin, tx event staff"`) is real and survives |
| Hardcoding a default project id / domain in the SPA | `state.projectId` defaulted to the literal slug `'fusehealth'` and `renderVals` fell back to `{domain:'fusehealth.com'}`. On a deployment without that project, every boot request (page data, sync log, sync resume) fired at a 404 and the 404's `.catch` could land *after* the corrected refetch, pinning `error` on over fully-loaded data; on a deployment that has it, the app silently opened a project the user never picked and labelled exports with someone else's domain. `boot()` now waits for `/api/projects` when nothing is remembered, and `fetchTab`'s `.catch` ignores rejections for a project the user has moved off |
| Assuming a DataForSEO `group_element` always carries its metric | A group_element omits `mentions`/`ai_search_volume` **entirely** when the value is zero — `{"type": "group_element", "key": "chat_gpt"}` is a complete, valid element meaning "no mentions". `.get("mentions", 0)` is fine but `el["mentions"]` raises, and treating a missing element as "no such platform" loses a real zero. Read with `.get(...) or 0` |
| Trusting `llm_mentions/top_pages` to return only YOUR pages | It returns co-occurring pages from other domains too — a live call for `driphydration.com` came back containing `https://www.perfectb.com/...`. Filter on `canonical_domain(url) == own_domain` before storing, or "Your Most-Cited Pages" lists a competitor's content |
| Two state keys that must track each other but live in different files | `app.js`'s `aiPlat` default was `{chatgpt, perplexity}` while `llm_mentions_service.MENTION_PLATFORMS`' ids became `google`/`chat_gpt`, so both platform toggle chips silently defaulted to "off" — nothing raised, the Share-of-Voice trend just rendered as if every platform were deselected. `mentionPlatforms` (2 entries, DataForSEO-backed) and `llmPlatforms` (4 entries, the Prompts tab's own LLM keys) are deliberately different lists; a frontend default keyed on one must be written against *that* list's ids, not copied from the other |
| Naming a REST endpoint after its MCP tool identifier | The connector shipped calling `llm_mentions/aggregation_metrics` and `llm_mentions/cross_aggregation_metrics`, carried over from the MCP tool names `ai_opt_llm_ment_agg_metrics` / `ai_opt_llm_ment_cross_agg_metrics`. Both return a plain HTTP 404 — the real REST paths are `llm_mentions/aggregated_metrics/live` and `llm_mentions/cross_aggregated_metrics/live` (**`aggregated`, not `aggregation`**, and every DataForSEO Live endpoint needs the `/live` suffix, exactly like the working `ai_keyword_data/keywords_search_volume/live`). Every test passed the whole time this was wrong, because a fixture never touches a URL — only a real call against the real host exercises the path string. `EndpointUrlTests` in `pipeline/connectors/tests/test_llm_mentions_parsing.py` now pins the verified paths so this can't regress silently |
| A domain-equality check that strips the scheme but not `www.` | `sites.site_url` is the cross-database join key, and `add_site`'s duplicate guard compared a `_bare_domain()` that stripped `https://`, `http://`, `sc-domain:` and a trailing slash — **not a leading `www.`**. So `premierstaff.com` and `www.premierstaff.com` were both accepted as new sites: two projects, two slugs, two sync budgets, two halves of one site's history, and a project switcher that offered the user a choice between them with no way to tell which was real. The SPA's client-side pre-check (`_addSiteDomain`) had the identical gap, so nothing caught it on either side. Use `pipeline/utils/site_ids.normalize_domain()` — §3 — at every point that asks "is this the same site?" Note the two follow-on traps this created: `canonical_domain("https://")` used to fall back to the raw string and yield `"https"`, a domain-shaped non-domain that would have been stored as a `site_url`; and `POST /api/projects` passed the **raw typed string** to `start_sync_run()`, which would have filed a brand-new site's entire first sync under a key no page reads |
| Scoping a per-project table by `site_id`, or by `location` as a stand-in for project identity | `saved_keywords` is per-PROJECT, and one domain is registered as several projects (`add_site(allow_duplicate=True)`) that all carry the same `site_url`. Reading it by `site_id` gave a **brand-new project 28 keywords its user had never added**, sitting in Positioning's "Newly Added Keywords — Not Tracked Yet" card with a button offering to buy DataForSEO lookups for all of them. The first fix used `location` as the discriminator, and that is not an identity: two projects on a domain may track the same market, and the wizard defaults every project to "United States", so the sibling case in front of us separated nothing. The write side was worse than the read — the unique key `(site_id, keyword, location)` meant a second project tracking a keyword its sibling already tracked silently **UPDATED the sibling's row**, and the bulk-replace endpoint's own `delete(SavedKeyword).where(site_id == ...)` wiped every sibling's entire list while reporting only the rows it wrote back. The owner is now `saved_keywords.site_pk` (`sites.id`), leading the unique key. Ask "could two projects legitimately have the same value here?" before treating any column as an identity |
| A write path that resolves a project with `select(Site).where(site_url == …).first()` | The mirror image of the read-side trap below, and it shipped for months after that one was fixed. `build_settings_response` resolved by **primary key**; `apply_settings_update` resolved by **first match on the domain**. With two projects on one `site_url`, the Edit modal showed the opened project's values and the save rewrote the OLDEST sibling's row — its location, name, engine, device and language. Because every positioning read filters on the project's *current* location, that sibling then matched zero `keyword_rankings` rows: its Rankings Overview went blank and its whole tracked list moved into "Newly Added Keywords — Not Tracked Yet". Reported as *"editing a project's location removed my tracked keywords"*, on a project the user never opened. `settings_service._resolve_write_target(session, site_id, site_pk)` is the one resolver now: pk wins, a pk/`site_url` mismatch **refuses** rather than falling through (the fallthrough IS the bug), and the pk-less branch logs that it cannot tell siblings apart. **Rule: if a read is scoped by `site_pk`, its write must be too — check both halves whenever you scope one** |
| Rebuilding a list from a request body that only carries part of the row | `PUT /keywords` cleared the project's tracked list and rewrote it from the payload. The Edit Project modal has no metrics to send, so it filled every row with `{volume: 0, kd: null, cpc: null, intent: 'Informational'}` — and each "Save Settings" press overwrote every keyword's real, DataForSEO-billed search volume with a fabricated `0` and wiped difficulty, CPC and intent. The `0` was worse than a null: `_volume_coverage` counts only nulls, so the response then reported **full volume coverage over invented numbers**. `reconcile_saved_keywords` diffs by cleaned, case-folded keyword — insert what's missing, delete what's gone, never touch a survivor — so a caller that lacks metrics cannot destroy metrics. Incoming metrics still apply to genuinely new rows (the Explorer's send-to-project flow really does carry them). Ask "does this payload contain everything the stored row holds?" before letting it replace one |
| A destructive write inside a page-data GET, scoped by domain | `persist_keyword_opportunities` runs on every `GET /positions` and deleted stale rows `WHERE site_id = …`. Two projects on one domain therefore deleted each other's scored rows on every render — B's page wiped every row of A's whose keyword B doesn't track, then A's next render did the same back — and the `(site_id, keyword)` upsert key silently overwrote a sibling's score for any shared keyword. Now keyed `(site_pk, keyword)`. Note the table did **not** get a backfill like `saved_keywords`: these rows are a recomputed cache, not a list a user chose, so unowned legacy rows are dropped by the next persist rather than guessed into an owner — a backfill is for data someone would miss |
| `get_site(session, unknown_id)` falling back to "first active site" | Same shape as the `.env` `GA4_PROPERTY_ID` fallback that once wrote 6 654 rows under another site's id: a connector handed an id it couldn't resolve was given a **stranger's row**, then used that row's `site_url` as its write key and its `dataforseo_target_domain` as its target. It now returns `None` for a given-but-unknown id (every caller already guarded for a missing row and had its own explicit default), while a call with **no** id still means "the default site" — a different question `get_default_site_id` depends on |
| A batch string-replace across model names that share a prefix | While converting `shared_queries`' exact `site_id ==` reads to `_site_clause(...)`, replacing `KeywordRanking.site_id == site_id` first silently corrupted four `CompetitorKeywordRanking...` lines into `Competitor_site_clause(KeywordRanking, …)` — `CompetitorKeywordRanking` **contains** `KeywordRanking`. It parsed as valid Python (a call to an undefined name) and would have raised only at request time. Replace longest-name-first, or anchor the pattern, and grep for the mangled prefix afterwards |
| Deriving "which algorithm produced this row" from the shape of the words in it | The Keyword Explorer's Related tab tagged a row `related` only when its shape classifier said `broad` — i.e. only when the keyword did **not** contain the seed. `related_keywords/live` returns Google's *"searches related to"*, which almost always **does** contain it: for DataForSEO's own documented example (seed `keyword research` → `free keyword research`, `keyword research tools`, `best free keyword research tool`, `keyword research google ads`) not one of the four qualified, so the tab rendered empty over rows the API had returned **and billed for**, while the rows sat under Phrase. Provenance and word shape are two questions and now have two fields: `match` (shape → Broad/Phrase/Exact/Questions) and `source`/`sources` (which fetch → Related). Three more defects hid behind it: `depth` was unset so DataForSEO's default of 1 returned **at most 8 keywords** and `limit` was inert; the dedup set was filled from the 100 volume-ordered `keyword_ideas` rows *before* the related loop read, and "searches related to" keywords are popular by definition, so most were claimed and dropped; and related ran for `cleaned[0]` only |
| A test module written for a framework this project does not run | `test_dataforseo_expand.py` was five bare `def test_*(monkeypatch)` pytest functions. **pytest is not installed here** and `manage.py test` uses unittest, which collects `TestCase` subclasses only — `manage.py test pipeline.connectors.tests.test_dataforseo_expand` printed *"Found 0 test(s)"* and nobody noticed for months. It also monkeypatched `_fetch_keyword_suggestions` while the code under test called `_fetch_question_ideas`, so had it ever run it would have made a **real billed HTTP call** with whatever credentials were in the environment, and its cost assertion (`== 0.004`) could only ever have summed to 0.003. Two rules follow: a new test must be a `TestCase`, and **run it once before you trust it** — a green suite that collected zero tests looks identical to a green suite that passed. Connector tests now inherit a base class that replaces `requests.post` with a raiser and asserts it was never called |
| An endpoint the UI advertises but nothing calls | `_fetch_keyword_suggestions` was implemented, correct, and had **no production caller**, while the Explorer's algorithm strip named `dataforseo_labs/google/keyword_suggestions` on two tabs. Nothing failed; the UI simply described work the backend never did. Same class as a fabricated number — check the claim, not just the code path |
| Deciding what a host IS with `if needle in host` | A domain is a structured name, not a blob of text, and substring containment answers a different question than "is this that site?". `get_social_metrics("t.co")` on the Off-site page matched `reddit.com`, `hubspot.com`, `blogspot.com` and every `*t.com` — so Reddit's entire referral volume was reported as X / Twitter traffic while `twitter.com` and `x.com` matched nothing — and `"linkedin" in "lnkd.in"` is False, so LinkedIn's own shortener (which carries most of the click-throughs from a LinkedIn post) was attributed to no platform at all. Match host-wise with a dot boundary — `host == d or host.endswith("." + d)` — so `m.reddit.com` is Reddit and `hubspot.com` can never be X. Same rule for the `www.` strip: `.replace("www.", "")` removes the substring anywhere; only a leading label is a prefix. See `offsite_service.PLATFORM_DOMAINS` |
| A substring test standing in for a category definition | `_is_offsite_channel` was `("Organic" in ch or "Referral" in ch or …) and ch != "Organic Search" and "Paid" not in ch`, which silently admitted GA4's standard `Organic Shopping` channel into an "off-site sessions" KPI purely because its name contains the word Organic — and would admit whatever Google names next. An allow-list can only ever count what someone deliberately put in it; a substring list counts whatever happens to match. Same shape as the trap above, one level up |
| A `{k: v for …}` comprehension over rows whose key repeats | A dict comprehension keeps the LAST value for a repeated key, silently. `source_map` on the Off-site page was built this way over `(channel, source)` rows, and one source under two channels is routine in GA4 (`linkedin.com` under both Referral and Organic Social) — so whichever row came last DISCARDED the other channel's sessions, key events and revenue with nothing in the logs. If the key is not unique in the source data, accumulate into a `setdefault` instead |
| A page button wired to a scope map that has no entry for its tab | The Off-site empty state's "⚡ Fetch Off-site Data Now" — the one button a user with no data is told to press — called `h.refreshPage`, but `tabToScope` in `app.js` had no `offsite` key, so `startSync` received `undefined` and did nothing. No error, no toast, no spinner: the button simply did not work, for as long as the page existed. When you add a page with its own refresh, add `tabToScope`/`tabToLabel` in the same change, and press the button once |
| `int(value)` on a GA4 metric string | GA4 Data API metrics arrive as STRINGS, and `conversions` is a floating-point metric (partial conversion credit is real), so a property that answers `"3"` one day answers `"3.0"` the next and `int("3.0")` raises ValueError. In `ga4.py::_normalize_offsite` that exception escaped into `fetch()` and killed the ENTIRE GA4 sync, discarding the seo_daily and campaign reports already fetched in the same run. Use `int(float(v or 0))` for any count, and default empty strings to zero |
| Two surfaces computing "the same" metric independently | Visibility had **three** implementations: `_get_ranking_distribution`'s CTR-credit score (read by the projects list), a share-of-voice recomputed **in the browser** from `competitors.rows` — a single latest capture date, integer-rounded, range ignored — printed under the heading "Visibility" on the workspace card, and `dist["visibility"]`, which `build_positions_response` computed on every request and then **dropped**: it was never in the returned `kpis`, so the one number the backend actually calculated for the page was the only one nobody could read. Two of the three were on screen at once and disagreed. Compute a metric **once**, return it, and give a differently-computed number a different name — the browser calculation is now labelled "share of voice", which is the question it really answers |
| Two surfaces windowing "the same" metric differently | The other half of the same bug. `ProjectSerializer._pos_summary` built its window from `date.today() - 28` while `ProjectPositionsView` anchors on `latest_ranking_anchor`. Identical formula, identical rows, different windows — so a project last synced 40 days ago had no measurement inside the wall-clock window and its list row reported `—`, which **means "never captured"**, beside a workspace showing a real score for the same rows. If two callers must agree on a number, they must share the anchor, not just the function |
| Re-anchoring a window in one direction only | `ProjectPositionsView` re-anchored to the rank measurement only when it was *newer* than the GSC traffic anchor (`rank_anchor > curr_end + 1 day`). That fixed the fresh case and left the stale case broken the other way: a project whose last sync predates the window rendered an empty workspace while its own share-of-voice cards — which read the latest capture whenever it happened — showed real positions on the same screen. The core contract says the user sees the last saved data between refreshes; anchor on the measurement in **both** directions |
| Deriving a "the rest" bucket by subtracting from a tracked-list total | `distribution["p21_100"]` was `dist["total"] - dist["top20"]`, and `total` is the size of the tracked list, not the number of measurements. A project tracking 40 keywords with 3 measured, all top-10, rendered **"21–100: 37"** — 37 asserted positions that were never measured — while those same 37 rows appeared as never-measured in the "Newly Added" card on the same screen. A residual computed against the wrong denominator is a fabricated measurement. Count the bucket from measured rows and give "no position" its own visible segment |
| A COALESCE-everything upsert on a table several connectors share | `upsert_keyword_rankings` used `coalesce(excluded[k], stored[k])` for every column, correctly stopping the three connectors that write this row from blanking each other. But `dataforseo_serp` writes `position: None` when the domain is not in the captured top 30, and that is a **measurement**, not a gap — COALESCE discarded it while stamping a fresh `rank_checked_at`, so a site that fell off page one kept advertising the rank it used to hold, dated today, forever. A caller now declares the columns it OWNS via `overwrite_columns` (`SERP_MEASUREMENT_COLUMNS`) and those are written even when NULL. Ask per column, not per table: "is a NULL from this writer an absence of data, or a measured absence?" |
| A `<span>` used as a progress-bar fill | CSS gives a **non-replaced inline box** no width and no height. The projects list's visibility bar had an inline track containing an inline fill, so every width the view model computed was applied to a box that could not use it — the bar never drew for any project since the column shipped, and nobody noticed because an empty grey track looks like a legitimately-zero bar. If you size a box, make it `display:block`/`inline-block`/`flex` |
| A well-written, fully-documented service function with zero callers | `delete_saved_keyword` was correct, tested by inspection and unreachable: no route, no caller. The only way to untrack a keyword was the bulk `PUT` — re-sending the whole list minus one through a modal that rewrites five other fields on the same save. Grep for callers before trusting that a capability exists; a function is not a feature |
| An `apps/<app>/tests/` package added next to an existing `apps/<app>/tests.py` | The package shadows the module, so every test in `tests.py` silently stops being discovered. `apps/sync` already had `tests.py`, `test_cancel.py` and `tests_normalize_site_urls.py`; a new module goes beside them (`test*.py` is the discovery pattern), not into a new package |
| A fixture built from a tool's rendering of a response, not the response itself | The real envelope is `tasks[0].result[0] == {"total": {...}, "items": [...]}`. DataForSEO's MCP tool happens to present that `result` array under a field it labels `items` in its own output, which got misread as an *extra* nesting level inside the real envelope — so all three parsers read `result[0]["items"][0]` as the block. `.get("total")` on that was always `None`, so every parser returned `[]`: both live syncs reported **success with 0 records written** while all 37 tests stayed green, because the hand-written fixtures matched the wrong shape the code expected. Fixtures in `test_llm_mentions_parsing.py` are now trimmed from real captured responses (`.superpowers/sdd/2026-07-31-llm-mentions-ai-visibility/real-*.json`). Build a fixture from a captured response, never from documentation or a tool's rendering of one |
| Giving an optional field a DEFAULT in a partial-update handler | `_handle_prompts_config` read `cfg.get("models", [])`, so a body that changed only the cadence, only the city, or only the list supplied `[]` and **wiped `tracked_models`**. An empty `tracked_models` renders every grid cell `off` *and* makes the run planner skip the prompt, so a prompt silently stopped being checked after an edit that had nothing to do with models. Absence and emptiness are different requests: gate on `if "models" in cfg`, and let an explicitly empty list still untrack everything. Identical shape to the credentials-branch bug above — forward the keys the caller actually sent, never a default. Note the follow-on: once a body can leave `update_fields` empty, `.update(**{})` is a SQL statement with an empty SET clause, so existence has to be checked directly rather than inferred from a row count that would always be 0 |
| `Math.max.apply(null, [])` guarded with `\|\| 1` | It returns `-Infinity`, which is **truthy**, so the fallback never fires and every derived width becomes `NaN%`. Both AI share-of-voice bar charts rendered this way whenever the row set was empty. Guard the empty array (`arr.length ? … : 1`), not the falsy result — the same reasoning as `all([])` being `True` further up this table |
| Dividing by a configurable cap without checking it is set | `d.budget.spent / d.budget.cap` with an unset (0) cap is `Infinity`, and `Infinity >= 0.8` is `true` — so **every project that had never configured a budget** wore the alarm-red "AI spend $0.00 of $0.00 cap" chip: a false alarm wrapped around a sentence that means nothing. An unset limit is not a limit of zero |
| A multi-line `{# … #}` in a Django template | Django's inline comment syntax is **single-line only** — the lexer's pattern is not DOTALL, so a `{# … #}` containing a newline never matches and its text is rendered as literal content. Two of them sat in `templates/reports/domain_overview.html`, so their explanatory prose was printed as visible paragraphs in **every PDF the report endpoint ever produced**, right under the heading. Nothing failed and no test looked, because the only reader is a human opening a PDF. Multi-line means `{% comment %}`, always — and assert on the rendered HTML (`assertNotIn("{#", html)`), because that is the only thing that would ever notice |
| Assuming a second rendering engine accepts the first one's stylesheet | The Domain Overview report gained an xhtml2pdf fallback so it would stop answering 501 on servers without WeasyPrint's cairo/pango libraries. But xhtml2pdf's CSS parser **raises** on WeasyPrint's `@page { @bottom-center { … } }` margin box — a `TypeError` deep inside `cssParser._parseAtPage`, not a warning and not a silently-dropped rule. Adding the engine without branching the template would have replaced "501, no engine" with "500, every render fails", which is worse: the first is honest. The template now branches on an `engine` context value, and `RealPdfEngineTests` drives the real resolver against the real template — every other test in that module hands the service a **fake renderer, and a fake never touches a real engine**, which is the same blind spot that let the wrong DataForSEO URLs ship (see the `aggregated`/`aggregation` row above) |
| A filter predicate that tests "has any match" instead of "matches the SELECTED value" | The AI domain filter must return prompts mentioning *that* domain; the natural-looking `Object.keys(mentionSet).length > 0` returns every prompt that mentions **anybody** the moment one competitor is clicked — which is exactly the symptom the feature was reported for before it existed. Related: a new filter must **AND** with the existing one, never replace it, and picking one must reset any selection it hides, or rows filtered out of view stay selected and get swept into the next bulk action |

---

## 10. Known-broken code — do not copy

**Still broken**

- `apps/dashboard/context_processors.py` — still lists the removed template pages; harmless but
  meaningless now that no Django template renders a dashboard.

**Fixed in the 2026-07 pass — listed so nobody reintroduces the shape**

- `app.js::clearData()` read `this.props.ctx.route.params.id`, which does not exist in this
  runtime, so the handler threw before reaching the API. There is no router ctx on that
  component; the project id lives in `this.state.projectId`, like every other settings call.
- Position Tracking's delete action called `window.FuseAPI.delete(...)`; the transport exposes
  `del`.
- The email-invite path created a `User` immediately, emailed a **plaintext temporary password**
  and a plain login link, and never wrote a `UserInvitation` — so invitees never appeared in the
  pending list and could not be revoked. It now creates the invitation, emails an
  `#/accept-invite?token=` link, and lets the invitee choose their own password.
- `.catch(() => {})` on user-initiated mutations, 16 of them in `app.js` alone. The worst had
  `.catch()` sitting **before** `.then()`, converting every rejection into a resolution: a
  refused POST still marked rows tracked, wiped three cached tabs, and toasted success.
- Site Audit's `get_domain_checks()` performed **six live network requests inside a page-data
  GET** — the only place in the codebase that reached the network while rendering. Its 6-hour
  cache protected nothing, because only a page view ever wrote that cache.
- Site Audit's page-detail drawer read `pg3.failed.length`, `pg3.cwv` and `pg3.externalLinks`,
  none of which ever existed in the payload — clicking any crawled-page row threw a `TypeError`
  and took the render down.
- Competitor positions were synthesised from a site-wide average plus an **MD5-derived offset**.
  Being deterministic, they looked stable and therefore real. An absent cell is the answer.
- `sync_all()` had two lines pasted into it from `sync_page()` — reading `incremental_kws`/
  `page`, neither of which exists in `sync_all`. They sat **outside** the per-connector
  try/except, so the first connector raised `NameError`, the exception escaped the whole
  function, and the background sync died silently on every single "Refresh all" from the
  commit that introduced this until the fix — the row stayed `running` forever with
  `completed_count=0`. No test called `sync_all()`/`sync_page()` directly (every existing test
  patches the thread away), which is how this shipped; see `apps/api/tests/test_sync_engine.py`.
- `ai_optimization.js`'s Prompts table read `pr.results[platform].cited` / `.snippet` with no
  null guard. `results` is genuinely `{}` until a prompt has been run at least once, so any
  tracked-but-never-run model crashed the whole `vals()` build — the entire SPA render went
  blank on a project whose setup wizard had just seeded `tracked_models` for the first time.

If you touch any of these, fix them properly rather than extending them.

---

## 11. Common tasks

**Add a metric to an existing page** — extend the service's `query_*_raw`, add it to
`build_*_response`, surface it in `js/pages/<page>.js`, render it in the fragment, extend the
test, update `api-reference.md`.

**Add a page** — §6 "Adding a page" plus §5 "Adding an API endpoint". Do both halves in one
change; a half-wired page is worse than none.

**Add an external data source** — §5 "Adding a connector". Then decide which scope runs it and
which page reads it, and add the env vars to `.env.example`.

**Add a settings group** — add its defaults to `DEFAULT_SETTINGS_BLOB` in `settings_service.py`,
add the key to the persisted list in `apply_settings_update`, add a draft to frontend state, and
add the sub-tab UI. It persists automatically.

**Change the sync scope of a page** — edit `PAGE_CONNECTORS` in `pipeline/services/sync_engine.py`
and `tabToScope` in `app.js`. Add an alias to `SCOPE_ALIASES` if the names differ.

---

## 12. Before you finish

- [ ] No external API call added to a page-data path.
- [ ] Every new API view carries `@method_decorator(login_not_required, name="dispatch")`.
- [ ] Every new analytics write goes through a `writer.py` upsert helper.
- [ ] No fabricated value fills a gap — empty, `null`, or `setup` instead, with a comment.
- [ ] Every service function catches, logs and returns a safe shape.
- [ ] Loading, error, empty-no-data, empty-filtered and setup states all exist for new UI.
- [ ] Mutations are idempotent, confirm with a toast, and invalidate their caches.
- [ ] `python manage.py test` passes.
- [ ] `api-reference.md` / `features.md` / `design.md` updated if behaviour, endpoints or tokens
      changed.
- [ ] No secret hardcoded; new env vars added to `.env.example`.

---

## 13. What not to do

- Do not add a frontend build step, a CSS framework, or a component library. The inline-style,
  text-inclusion approach is a deliberate decision (see `design.md` §1).
- Do not edit `static/spa/vendor/support.js` — it is generated.
- Do not put business logic in `apps/api/views.py` or in a template.
- Do not import Django models into `pipeline/connectors/` at module level; the lazy import inside
  `_update_django_sync_log` is intentional so the pipeline stays runnable outside Django.
- Do not add cross-database foreign keys. There are two databases; the join key is a string.
- Do not "clean up" the long explanatory docstrings. They record why the code is shaped the way
  it is, and they have already prevented regressions.
- Do not trust `docs/superpowers/`, `Design_features/`, or `scratch/` as specifications. They are
  historical design material and throwaway scripts. **The code is the specification; these five
  `.claude/` files describe the code.**
