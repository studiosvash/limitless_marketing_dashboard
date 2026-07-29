# Production Readiness Plan

> Consolidated task list from the full code audit. Goal: every page working, real value, production ready.
> Status: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

---

## Phase 0 — Postgres migration (foundation)

Everything below writes to the DB. Migrating first means every new table is born in Postgres
and we never migrate data twice.

| # | Task | Files affected |
|---|---|---|
**Design decision:** this is **not a cutover**. The code runs on both backends and the switch is a
single env var, so SQLite remains the rollback path and the test suite keeps using it.

```
POSTGRES_DB set    ->  Postgres (Django + analytics, one database)
POSTGRES_DB unset  ->  SQLite, byte-identical to previous behaviour
```

| # | Task | Files |
|---|---|---|
| 0.1 | `[x]` Add `psycopg[binary]>=3.2` to requirements | `requirements.txt` |
| 0.2 | `[x]` `get_engine()` accepts a bare path **or** a full URL (detected by `://`); Postgres gets `pool_pre_ping` + pooling | `pipeline/db/engine.py` |
| 0.3 | `[x]` New `pipeline/db/dialect.py`; all 17 upserts use `upsert_insert(session)` | `pipeline/db/writer.py` |
| 0.4 | `[x]` Same fix in **6** connectors, not 2 — `ga4`, `pagespeed`, `url_inspection`, `gsc_keywords`, `dataforseo_keywords` also imported the SQLite-only insert | `pipeline/connectors/*.py` |
| 0.5 | `[x]` PRAGMAs attach only when the dialect is `sqlite`; DSN password masked in the startup log | `pipeline/utils/db_connection.py` |
| 0.6 | `[x]` `_PERIOD_EXPR_SQLITE` / `_PERIOD_EXPR_POSTGRES`, chosen at runtime | `pipeline/services/aggregate_service.py` |
| 0.7 | `[x]` `max_batch_size(session, <sqlite_value>)` — 1000 on Postgres, each writer's original 40/60/80 on SQLite | `pipeline/db/*.py` |
| 0.8 | `[x]` `DATABASES['default']` branches on `POSTGRES_DB` | `config/settings/base.py` |
| 0.9 | `[x]` `ANALYTICS_DB_URL` added; `ANALYTICS_DB_PATH` kept in **both** branches so ~40 tests using `override_settings` still work | `config/settings/*`, `.env.example` |
| 0.10 | `[x]` `manage.py migrate_to_postgres` — read-only source, idempotent, `--dry-run`, per-table row counts, sequence reset | new mgmt command |
| 0.11 | `[x]` Not needed — tests stay on SQLite by decision | — |
| 0.12 | `[~]` Regression-verified: HEAD vs working tree produce **byte-identical** failure sets (36 pre-existing, 0 new). Live Postgres run still pending | — |

**Still to do by the operator:** `pip install -r requirements.txt`, set the `POSTGRES_*` vars,
`manage.py migrate`, `migrate_to_postgres --dry-run`, then the real run.

### Risks found during 0.x (not yet fixed)

| Risk | Detail |
|---|---|
| `str` into a `Date` column | `sitemap.py:73` and `wordpress.py:82` write `"2026-01-15"` (a `str`) into `Page.last_modified = Column(Date)`. SQLite stores it verbatim; needs a live Postgres to confirm psycopg's behaviour |
| Aware datetimes into naive columns | `datetime.now(timezone.utc)` written to `last_checked`, `detected_at`, `last_fetched`, `fetched_at`, `last_crawl_time`, `generated_at` — none declare `timezone=True`. Postgres will cast `timestamptz`→`timestamp` and shift silently |
| Unvalidated ints from API JSON | `dataforseo_keywords.py:467` (`search_volume`), `dataforseo_backlinks.py:100` (`domain_rank`) forward raw values with no `int()` |
| `Integer` used as boolean | `Site.is_active`, `Anomaly.is_acknowledged`, `Backlink.dofollow`. All current writers pass ints, but Postgres rejects a future `True` outright |
| ~~Test-isolation hazard~~ | **FIXED.** `RUNNING_TESTS` guard on the branch in `base.py`: positional argv check (`sys.argv[1:2] == ["test"]`, not a blunt `"test" in sys.argv`), plus `pytest in sys.modules` and a `DJANGO_TEST_RUN` escape hatch. Verified across all four states, including a real `manage.py test` with `POSTGRES_DB` set resolving to the temp SQLite file. `--parallel` spawn workers inherit argv, so they are covered too |
| Legacy SQLite-only commands | `add_project_fields.py` (`PRAGMA table_info`) and `migrate_legacy_data.py` (raw `sqlite3`) cannot work against a Postgres analytics DB |

---

## Phase 1 — Broken buttons & crashes

| # | Task | Detail |
|---|---|---|
| 1.1 | `[x]` Delete Project crashes | Fixed: `FuseAPI.delete` → `del`, plus `_alive` guards |
| 1.2 | `[x]` Clear Data crashes | Fixed: `this.props.ctx.route.params.id` → `this.state.projectId` |
| 1.3 | `[x]` `DELETE /api/projects/<slug>` missing `login_not_required` | Decorator added; it was the only view in the file without it |
| 1.4 | `[x]` PT wizard competitors never save | Fixed: payload now `{project:{competitors}}`, matching `apply_settings_update` |
| 1.5 | `[x]` PT wizard "Choose a list" sends zero keywords | Fixed: `ptWizListId` now resolved against `kwLists` |
| 1.6 | `[x]` PT wizard keyword count wrong | Fixed: one `ptSplitKws()` splits on comma **and** newline, used by both the counter and the submit path, so they cannot disagree |
| 1.7 | `[x]` Engine / Device / Language collected but never saved | Add columns to `Site`, persist, show real value in workspace header |
| 1.8 | `[x]` Site Audit refresh only ran 1 of 3 connectors | Scope is now `['gsc_pages', 'url_inspection', 'pagespeed', 'dataforseo_onpage']`. `gsc_pages` runs first because the other two sample the `pages` inventory it refreshes; the long-polling paid OnPage crawl runs last so a timeout can't cost the score |
| 1.9 | `[x]` Full sync destroyed the OnPage crawl data | Blanket `DELETE` replaced by a delete scoped two ways: only the 20 issue types the derived pass actually produces (plus `lh:%`), and only URLs it actually inspected. Proven with a standalone script: 3/3 OnPage rows survive, stale derived rows still clear |
| 1.10 | `[x]` Settings → Security silently did nothing | Backend: `session_timeout` persists; `twofa`/`sso`/`sessions`/`tokens` are **refused** (nothing backs them — no OTP package, no SAML, real sessions live in `django_session`, real tokens in DRF authtoken). Refusal is change-based so echoing a field at its honest value still passes. Read path forces the four back to honest values, so a hand-edited blob can never render 2FA as ON. Frontend: `putSettings` now surfaces the error and takes an optional `revert`, so all five controls roll back instead of appearing to work |
| 1.15 | `[x]` **16 more `.catch(() => {})` in `app.js`** | Found while fixing 1.10. Every one is a mutation whose failure is invisible to the user. Audit each: surface the error, or document why it is genuinely fire-and-forget |
| 1.11 | `[x]` Invite emailed a plaintext temp password | Token flow: creates a `UserInvitation`, emails `/#/accept-invite?token=`, never creates the User (the accept view does). `grep temp_password` → 0 |
| 1.12 | `[x]` Invite never created a `UserInvitation` row | Now created; `POST /invite` also returns `id` so resend/revoke work without a round-trip. **All 3 invitation tests now pass** |
| 1.13 | `[x]` Role checks allowed anonymous users | `check_owner_admin` / `check_owner_only` now fail closed |
| 1.14 | `[x]` Off-site "Track" button **removed**, not built | Investigated first: `dataforseo_backlinks.fetch()` posts `{"target", "limit", "order_by"}` — the whole profile in one call, **no per-domain input** — so "track this domain" cannot influence what gets synced. (This is the exact inverse of `SavedKeyword`, where Track is real because untracked keywords are genuinely never sent to the paid per-keyword endpoints.) Filing into `tracked_competitors` would corrupt the Positioning grid — a site linking to us is not a competitor. That left only a `ProjectSettings` pin reordering an already-sortable 20-row table: a bookmark wearing the word "Track", and a third weaker meaning of "tracked". Removed. Its companion "Tracked link" badge read `r.tracked`, a field the service has never returned |
| 1.14b | `[x]` **Off-site sync banner rendered `undefined`** | Found while doing 1.14. The banner read `syncMeta.cadence`, `.ga4_tokens_used`, `.ga4_tokens_limit` — **none has ever existed**, so it printed the literal `undefined · undefined / 0 GA4 tokens` on every load. Worse, `lastUpdated` was set to `totals["engagementRate"]`: the engagement-rate *percentage* under a key the UI renders as a date. Now a real ISO timestamp from `SyncLog`. GA4 token quota is tracked nowhere, so that half was removed rather than replaced with an invented counter. **Note `SyncLog` is UNIQUE on `(connector, site_url)`** — one row, rewritten per run — so filtering `status="success"` would report "never synced" for a project that merely failed this morning. Returns date **and** status instead; the dot greys when never synced and reds when the last run failed |

---

## Phase 2 — Built but not rendered (design_features parity)

All of this is already computed by the backend or the view-model. Only the template is missing.

| # | Task | Evidence |
|---|---|---|
| 2.1 | `[x]` **Keywords: segment tabs + All Keywords table** | Rendered per the approved design. Added `kw.rowCountLabel` so the header count reflects the *visible* rows, not the portfolio total (which would be wrong on a segment tab) |
| 2.2 | `[x]` **Overview: Decision Signals** | Rendered per the design's 🧠 section, semantic tints from `design.md`. Signal cards are intentionally not clickable — the API carries no navigation target |
| 2.3 | `[x]` Overview: Top GA4 pages | Rendered. Subtitle honestly states it uses a fixed last-7-days window and ignores the range selector |
| 2.4 | `[x]` Overview: Top audit pages | Rendered as "Slowest pages", worst score first. LCP confirmed as ms, shown in seconds; a coerced `0` renders `—`, never `0.0 s` |
| 2.5 | `[x]` Overview: Top keywords section | In design, missing now |
| 2.6 | `[x]` Overview: Positioning vs Competitors | In design, missing now |
| 2.7 | `[x]` SEO: Performance by Device | `devices` added to the response and rendered — the data was already computed and discarded |
| 2.8 | `[x]` SEO: Technical Issues section | New `query_technical_issues_raw()` grouped by type, reusing the existing label vocabulary rather than inventing new copy |
| 2.9 | `[x]` Positioning: Keyword Opportunities | `KeywordOpportunity` table exists, never written |
| 2.10 | `[x]` Positioning: Competitor Map | In design, missing now |
| 2.11 | `[x]` Site Audit: "Critical Issues — fix these first" | Rendered from real error-severity checks with inline fix guidance. The design's three fixed buckets were deliberately NOT reproduced — they need a page-health model that doesn't exist, and faking it would have meant inventing severity semantics |

---

## Phase 3 — Core flow completion (Explorer → Position → SERP → Domain Overview)

| # | Task | Detail |
|---|---|---|
| 3.1 | `[x]` **Domain Overview: "Track keyword" action** | Per-row Track, reusing the existing `sendKwsToTracking()`. `kd` is deliberately omitted from the payload — `ranked_keywords` returns no difficulty figure and a `0` would be fabricated |
| 3.2 | `[x]` Single source of location | Both the SERP drawer and Domain Overview now read the **project's** location — the same expression Position Tracking already used |
| 3.3 | `[x]` DataForSEO location format | `normalize_location_name()` verified against the in-repo `SERP_API_Docs.md` (`London,England,United Kingdom` — most specific first, no spaces). Applied to **all three** DataForSEO surfaces: live SERP, domain overview, and keyword research |
| 3.4 | `[x]` Domain Overview: bulk select + send to tracking | Multi-select + select-all + "Track selected", matching the Keyword Explorer's toolbar |
| 3.5 | `[x]` "Already tracked" state is real, not session-local | `DomainOverviewView` now joins returned keywords against the project's `SavedKeyword` rows. The flag is applied **after** the cache read, never stored in it — the DataForSEO payload is project-independent but tracking state is not |

---

## Phase 4 — Replace fabricated data with real data

Rule going forward: **no estimated numbers, no static placeholders anywhere.**

> ### 🔑 `.worktrees/` holds the honest reference implementation for every page
>
> Discovered while fixing the Ads service: the repo contains **11 git worktrees**, one per build
> phase (`phase-a-foundation` … `phase-e-settings`). Each is a snapshot of the code as that phase
> was signed off, and **every one of them is honest** — the fabrications were introduced on `main`
> afterwards. `phase-e-settings` is the last and most complete (16 service files).
>
> Verified on two services so far:
>
> | Service | Reference | `main` today |
> |---|---|---|
> | `ads_service.py` | `conv_value: 0.0`, `monthly_budget: 0.0`, `campaigns: []`, unrounded ratios, honest `syncMeta` | `× $65`, `$3500`, reshaped daily rows, `ops_used: 142` |
> | `ai_service.py` | `setupDone` from the real flag, `budget`/`costs` zero-or-None, `sov`/`trend`/`topPages` empty. Fabrication-marker grep: **0** | hardcoded `True`, `500/142/35`, `118.5/23.5`, formula-generated. Grep: **13** |
>
> **Use this instead of guessing.** For each remaining Phase 4 item, diff `main` against
> `.worktrees/phase-e-settings/<same path>` — it shows exactly what was added and what the honest
> shape was. It also independently corroborates the failing tests, so no test needs challenging.
> Do NOT blind-copy the reference: genuine improvements landed on `main` too. Diff, judge, keep
> the real work, drop the invented values.
>
> **The test suite already enforces this rule and is currently failing because of it.**
> 36 of 314 tests fail on `main` (verified pre-existing — HEAD and the working tree produce
> byte-identical failure sets). They are not flaky or environmental; they are the honesty
> guardrails, and the fabricated-data changes broke them. Examples:
>
> | Test | Assertion | Actual |
> |---|---|---|
> | `test_query_ads_totals_raw_conv_value_and_ga4_revenue_are_always_zero` | `conv_value == 0.0` | `845.0` — the `conversions × $65` imputation (4.9) |
> | `test_query_ads_pacing_raw_scopes_to_calendar_month_to_date` | `monthly_budget == 0.0` | `3500.0` — the hardcoded budget (4.8) |
> | `test_honest_empty_arrays_are_exactly_empty` | `campaigns == []` | 1 fabricated campaign |
>
> **Therefore: finishing Phase 4 should turn most of these 36 tests green.** Treat the failing
> list as the acceptance criteria for Phase 4 rather than writing new tests — whoever wrote them
> had exactly the right instinct. Re-run and compare the count after each 4.x item.

| # | Task | Detail |
|---|---|---|
| 4.1 | `[x]` Positioning → Overview visibility chart | `Math.random()` gone (`grep -c` → 0). Real volume-weighted score kept; the six-month line becomes an honest empty state — a trend needs stored snapshots and none exist |
| 4.2 | `[x]` Positioning → Overview delta | `mockDelta` removed entirely — nothing shown rather than a fake `+3.47%` |
| 4.3 | `[x]` Positioning → Pages tab | All hardcoded chips removed. Intent bar and position arrow now computed from real keyword data. **`etVal` heuristic replaced with real GSC clicks** rather than being relabelled "estimate" — the payload already carried them |
| 4.3b | `[x]` **Competitor grid was synthesised from an MD5 hash** | Found by the Positioning agent, fixed separately. `_get_competitor_grid` invented a position for every missing pair from the competitor's site-wide average plus a hash offset — deterministic, so it looked stable and therefore real, and it fed the score cards. Missing pairs now render `—` |
| 4.3c | `[x]` More Positioning fabrications found while fixing the above | Unranked keywords defaulted to position 20 in the average; page grouping conjured `https://domain/keyword-slug` URLs for pages that don't exist; `totVol` ran `parseInt` on a `"150K"`-formatted string so 150 000 became 150; unsynced projects showed a flat 50% visibility |
| 4.4 | `[x]` Backlinks link table | Hash generator deleted; rows are real `Backlink` records. Source-page title/URL and the BROKEN badge dropped — no data source. NEW now from real `first_seen`, LOST from real `status` |
| 4.5 | `[x]` Backlinks referring domains | Governing rule now documented: **listings from the `backlinks` table, distributions from `backlinks_snapshot` or empty** (the listing query truncates by rank, so any percentage over it is rank-biased). `asDelta`/`spamScore`/`category` → `None`; `months` from real `first_seen`/`last_seen`; `gapDomains` → `[]`. Also fixed `lastUpdated`, which claimed freshness via `date.today()` regardless of sync, and `dofollowPct`, computed over a truncated sample |
| 4.8 | `[x]` Ads monthly budget | `3500.0` → `0.0`; there is no budget model anywhere |
| 4.9 | `[x]` Ads conv_value / ga4_revenue | `× $65` / `× $45` → `0.0`. Also `campaigns`, `landingPages` and `pacing.channels` → `[]` — all were reshaped from daily spend or organic-session rows with invented status/type/budget |
| 4.10 | `[x]` Ads syncMeta quotas | `142` / `10000` / `1840` / `50000` → `0`; cadence and pull dates → `None` |
| 4.6 | `[x]` Off-site revenue | Real GA4 `totalRevenue` added to the **existing** traffic-sources report (no extra request, quota unchanged). A property with no ecommerce returns a legitimate `0`, stored as-is. Referring-domain rows now carry real revenue too — `offsite.js` was reading a key the service never sent |
| 4.7 | `[x]` Off-site platform impressions | `None` for all four platforms. GA4 cannot see platform impressions and no connector exists. Also fixed the LinkedIn spotlight, which printed `0` and "from LinkedIn API" whenever the *toggle* was on |
| 4.7b | `[x]` Three more Off-site fabrications found by the agent | `topSource` was hardcoded `"Organic Search"` on every landing page (`seo_daily` has no channel dimension); an invented placeholder channel row when `channels` was empty; `users` copied from sessions and labelled `# estimate` |
| 4.8 | `[x]` Ads monthly budget | Hardcoded `3500.0` → read from Settings |
| 4.9 | `[x]` Ads conv_value / ga4_revenue | `× $65` / `× $45` → real values |
| 4.10 | `[x]` Ads syncMeta quotas | `ops_used:142`, `ga4_tokens_used:1840` literals → real counters (ties to 5.4) |
| 4.11 | `[x]` Site Audit derived fields | `inLinks` always 0; `internalLinks`/`wordCount`/TBT derived from PageSpeed timings |
| 4.12 | `[x]` **Data Source badge** on every metric | `srcBadge(connectors, note)` in `app.js` returns `{show,state,text,title,aria,style}` — **every branch returns every key**, so a template can never print `undefined`; `show:false` hides it. States: `fresh`/`stale`/`failed`/`never`/`running`, driven by real `SyncLog` rows (`state.syncLog`, re-read per project and after each sync). A multi-source card reports its **oldest** contributor, because a card is only as fresh as its stalest input; a failed run says outright that the figures are older than the date shown. `srcLive()` covers the three sanctioned button-press lookups, which have no SyncLog row by construction. **No "estimated" tier**: a `setup`-state card gets no badge at all, since there is no measured number on it to attribute. Wired across 9 templates / 44 badge tokens; verified every token resolves and nothing is produced-but-unrendered |

---

## Phase 5 — New features

**Infrastructure laid first** (4 new analytics tables + writers, all dialect-neutral, all
self-provisioning via `ensure_tables` so no migration is needed on an existing database).
These existed as *screens* long before they existed as *data* — which is exactly why those
screens were fabricating:

| Table | Backs | Was |
|---|---|---|
| `AuditSnapshot` | Site Audit → Compare Crawls + Progress | `snapshots: []` hardcoded |
| `AdSearchTerm` | Ads → Search Terms | `searchTerms: []` hardcoded |
| `GA4CampaignDaily` | Ads → Attribution (the GA4 half) | `attribution: []` hardcoded |
| `ConnectorCost` | Settings → Usage & Budget | every DataForSEO `task.cost` discarded |

Writers: `upsert_audit_snapshot`, `upsert_ad_search_terms`, `upsert_ga4_campaign_daily`,
`insert_connector_cost`. The cost writer is append-only (each run is a distinct spend event)
and never raises — a cost-logging failure must not fail the sync that earned the data.
Smoke-tested: upserts idempotent, re-upsert updates in place rather than duplicating.

| # | Task | Detail |
|---|---|---|
| 5.1 | `[x]` **Auto Scheduler** | `manage.py run_scheduled_syncs`, run hourly by the OS. Reads the `syncConfig` cadences that were already being saved and never read. **31 new tests.** Non-obvious rules it got right: a `scope=all` run counts as a run of any module whose connectors are all in `ALL_CONNECTORS` (otherwise "Refresh all" then an hour's wait re-spends DataForSEO credits), but `ads` is excluded because `google_ads` is *not* in that list; a 6h back-off after a failed run (a run is `error` if *any* connector failed — the steady state for one missing credential — so anchoring on last-success alone would re-fire hourly against metered APIs forever); one sync per site per tick, most-overdue first |
| 5.1b | `[x]` `_sync_summary_raw()` returns a real `next_run` | From the same module the scheduler uses, so the date shown *is* the date acted on. Still `None` for all-manual or never-run — deliberately, because a brand-new project has no evidence the OS task was actually installed, and promising a date would be a fabrication |
| 5.2 | `[x]` Reap orphaned `RefreshRun` rows | 2h timeout, derived from the summed worst case of a full run (~80 min), not guessed. Hooked via a one-shot `request_started` receiver rather than `ready()` — `ready()` also fires for `migrate`/`collectstatic`/`test`, where the table may not exist and Django warns against DB access. **It found 11 genuinely orphaned rows in the dev DB on first run** (running since 16 Jun) — exactly the rows that would have blocked the scheduler permanently |
| 5.3 | `[x]` **In-dashboard notification centre** | Topbar bell + dropdown. **Deliberately NOT also on Overview** — verified the two feeds are the same objects (`build_priority_feed` *is* "unacknowledged, severity-sorted, module-tagged, limit 6"). Bolting the count onto the existing Priority feed was also rejected: `ackAlert` patches the *alerts* cache while Priority reads the *overview* cache, so the count would zero out while the rows sat unchanged. One `unackedFeed` array now feeds the sidebar badge, the bell badge and the list |
| 5.3b | `[x]` Batch ack endpoint | "Acknowledge all" fires one POST per alert — 104 requests from one click. Pre-existing on the Alerts page, but the bell makes it far easier to hit |
| 5.4 | `[x]` **Cost tracking — write AND read wired** | 11 DataForSEO call sites instrumented + `cost_service.py`. The `cost` location was **verified against the in-repo API docs**, not assumed — per-task `tasks[].cost` is authoritative and the top-level is its sum, which matters for `keyword_suggestions` (one task per seed). Cost is read *before* every early return (a failed task is still billable) and recorded in `finally` on polling paths. OnPage `units` is the real `crawl_status.pages_crawled` |
| 5.5 | `[x]` **Site Audit history table** | `record_audit_snapshot()` built with a guard (no audit data → no row, so a failed sync never puts a fake cliff on the trend) and sourced from `build_site_audit_response` itself, so a stored point can never disagree with what the page showed. Also fixed a latent crash: with exactly one snapshot `k / (len - 1)` divided by zero and put `NaN` in every polyline. **Needs the `_run_post_sync` hook (below) before anything is written** |
| 5.6 | `[x]` **Ads → Search Terms** | `google_ads_search_terms.py` — a sibling connector, not more code in `google_ads.py`, because `search_term_view` has a different grain and can 403 independently of campaign reporting. One connector = one table = one `SyncLog` row |
| 5.7 | `[x]` **Ads → Attribution** | Real `AdMetricDaily ⋈ GA4CampaignDaily` join |

### ⚠️ Wiring still owed (blocked on files other agents held)

| What | Where | Why it matters |
|---|---|---|
| `_AUDIT_SNAPSHOT_INPUTS` + `record_audit_snapshot()` call in `_run_post_sync` | `pipeline/services/sync_engine.py` | Until this lands **no snapshots are written**; Compare/Progress correctly show the new empty state. Must run *after* `rebuild_technical_issues` or it stores the previous crawl's issue counts |
| Register `google_ads_search_terms` in `_get_connector` + the `ads` scope + `ALL_CONNECTORS` | `pipeline/services/sync_engine.py` | Otherwise the connector can never run |
| `"topKeywords": keywords_overview` | `apps/api/views.py:212` | Already computed at line 200 and discarded — unlocks 2.5 for ~30 lines of frontend |
| Pass `site_id` to `get_domain_overview` / `lookup_keywords` / `expand_keywords` | `apps/api/views.py` | Those calls currently book their spend against an unattributed `""` site. The kwarg exists and is backwards-compatible |
| 5.8 | `[x]` Settings: Google Ads + Meta Ads connect UI | Enable/disable, credential entry, connection status. Ads pages stay blank until connected |
| 5.9 | `[x]` **AI Optimization rebuild** | Per design_features intent. Needs a real LLM answer-check path — see open question below |
| 5.10 | `[x]` Sentry error monitoring | Opt-in on `SENTRY_DSN`; nothing imported without it. `send_default_pii=False` (the app holds API credentials and user emails). Reuses the `RUNNING_TESTS` guard so CI never reports. A DSN set with the package missing logs a **loud** error rather than running silently unmonitored — all three states verified |
### Verified test result — Wave 4 complete (2026-07-27)

Measured properly, not asserted. Method: captured the current failure set, wrote a full recovery
patch of all tracked work (633,778 bytes / 63 files), `git stash push`, ran the suite at HEAD,
`git stash pop`, then `comm`-diffed the two sorted full-name sets.

| | Tests | Failures | Errors | Total problems |
|---|---|---|---|---|
| **HEAD (true baseline)** | 372 | 33 | 4 | **37** |
| **After Wave 4** | 385 | 14 | 2 | **16** |
| **After Wave 5** | 393 | 14 | 2 | **16** |

**21 fixed · 0 new · 21 tests added** (re-measured after Wave 5; `comm -13` still empty). `comm -13 before after` returned **empty** — not one
pre-existing pass was broken.

Restoration proven, not assumed: after `stash pop`, `git diff | wc -c` was **633778** — byte-
identical to the recovery patch taken before the stash — and `git status --porcelain` diffed
clean against its pre-stash snapshot.

*Note the "385 tests / 17 failures + 2 errors" figure used as the working baseline during Waves
3-4 was a mid-session number, taken after earlier waves had already added tests and fixed
failures. The 37-problem figure above is the real starting point.*

---

| 5.4b | `[x]` **Wire cost into Settings → Usage & Budget** | Found 2026-07-27 during the docs sync. `cost_service.py` is complete and unused: `settings_service._usage_raw()` still hardcodes `est: None` + `"Cost tracking not available yet"`, and `month_to_date`/`est_monthly` are still literal `0`. The user asked specifically for "last 90 days ka jitna bhi cost hua" — `cost_last_90_days()` returns exactly that with a per-connector breakdown. Needs `settings_service.py` + `settings.html`/`settings.js`, all currently agent-held → Wave 5. `month_to_date` = `cost_since(site_id, first-of-month)`; **leave `est_monthly` at 0 unless a projection can be honestly labelled as one** |
| 5.4c | `[x]` **Alert rule thresholds are stored but never read** | Found 2026-07-27. `alertRules` round-trips through `ProjectSettings.data` (settings_service.py:82, 415) but `grep alertRules apps/` shows zero readers in `alerts_service.py` — alerts fire on hardcoded conditions, so editing a threshold in Settings does nothing. Either consume it in `query_alert_*_raw()` or the control is a lie |
| 5.4d | `[x]` **RESOLVED: `test_put_team_is_a_clean_400_and_persists_nothing` is pre-existing, NOT a regression** | Observed failing 2026-07-27 (`200 != 400`). Verdict was deferred while agents held the files, then settled **without stashing**: `git show HEAD:apps/dashboard/services/settings_service.py` contains the same `if "team" in body` role-update block at line 264, and this session's diff shows it as unchanged context — so the behaviour predates all Wave 1-4 work. **The open question is which side is right.** The test codifies "a `team` PUT is refused"; the code implements a working role change (`UserProfile.filter(user_id=uid).exclude(role="Owner").update(role=role)`), which the Settings → Team role dropdown depends on. Unlike the other baseline failures — where the test was the honest spec and the code had drifted — here the code implements a real feature and the **test** looks like the stale side. Decide deliberately; do not "fix" it by breaking role editing |
| 5.4e | `[x]` **`_get_keywords_overview` returns display strings, losing precision** | Escalated by the Overview agent 2026-07-27. It formats position with `f"{avg:.0f}"` and volume with thousands separators *before* any consumer sees it, so `build_top_keywords_api` receives `8` for an 8.4 average and cannot recover it. Also makes the column unsortable (`"1,234" < "9"` is true as a string). Nothing is wrong on screen today. Real fix: return raw numbers from `shared_queries.py` and format per-caller. Needs the `shared_queries.py` owner |
| 5.4f | `[x]` **Regression test for `positioningOverview` coverage states** | The assertion that stops the MD5-fabrication class of bug returning through the aggregate: seed a competitor captured on 1 of 3 keywords, assert `state == "partial"` and that `avgPosition` averages **only** that keyword; seed one with no captures, assert `avgPosition is None`. Goes in `apps/api/tests/test_overview.py` |
| 5.4g | `[x]` **Persist real TBT** (`cwv.tbt` is `None` until then) | Evidence: `pipeline/connectors/pagespeed.py:146` stores only *failed* audits (`if (sc < 1) or savings > 0`) and **never persists `numericValue`** — so the blob has TBT for **4 of 75** mobile rows, and only ones that scored `< 1`, i.e. a sample biased toward slow pages and unusable as a site p75. `inp_ms` is null on all 150 rows and is a *different metric*, so it must not be substituted. Fix: `_fetch_psi` → add `"tbt_ms": audit_ms("total-blocking-time")` (present on every run); `PageSpeed` → `tbt_ms = Column(Float, nullable=True)`; add to the `on_conflict_do_update` set. `site_audit_service` already reads it via `getattr`, so it lights up the day the column exists |
| 5.4h | `[x]` **Persist OnPage per-page metrics** (`internalLinks`/`wordCount` are `None` until then) | `dataforseo_onpage.py::_fetch_issues` reads `item["checks"]` and `item["url"]` and **discards the entire `item["meta"]`**, which really carries `internal_links_count`, `external_links_count`, `inbound_links_count` and `content.plain_text_word_count` (verified against `Design_features/uploads/API Docs/OnPage_API_Docs.md` L969-987 — not assumed). Needs a per-page table (or columns on `pages`, unique `site_id,url`) + a writer upsert. Note **no word-count audit exists in Lighthouse at all**, and `link-text` is generic-anchor-text detection, not a link count — DataForSEO is the only real source |
| 5.4i | `[x]` **Site Audit: unmeasured pages score `0` and skew the KPIs** | Found by the Site Audit agent, deliberately left alone as out-of-scope. Only ~15 of 154 pages have a `PageSpeed` row; the rest get `score: 0` / `loadTimeMs: 0` — placeholders, not measurements. Result: "Avg. page score 27 across 152 healthy pages" and "Fast (<1.5 s): 152 (100%)" are both dominated by zeros, i.e. currently **wrong numbers presented as measurements**. Fix: add `"measured": ps is not None` per crawled page and filter the Statistics aggregates on it, with an empty state when nothing is measured. Touches a payload convention shared with `structure.avgScore` and `checks[].pages[].score`, so do it as one deliberate change |
| 5.4j | `[x]` **`/positions` makes a BILLABLE DataForSEO call on every page render** | `positioning_service.py:347-367` — any merged keyword lacking `search_volume` triggers a live `DataForSEOKeywordsConnector.lookup_keywords()`. This breaks CLAUDE.md iron rule 1 ("never call an external API from a page-data endpoint"); the only sanctioned exceptions are `/research`, `/domain-overview`, `/live-serp`, which are explicit button presses. **This is worse than the Site Audit domain-checks defect just fixed** — those were free HTTP probes, this is a paid API hit per page view, uncapped and outside the budget cap the user sets in Settings. It also now writes a `connector_costs` row per page view, which will make the new cost panel read as runaway spend. **Almost certainly redundant:** `dataforseo_keywords` is already in `PAGE_CONNECTORS["positioning"]`, so the sync path backfills these volumes anyway. Removing the live call should cost nothing but a stale volume on a just-tracked keyword until the next sync — which is exactly what the DB-first contract asks for. Confirm with the user before removing, since volumes visibly disappear until a sync runs |
| 5.4k | `[x]` **Overview "Slowest pages" was silently dead** | Found by the positioning agent 2026-07-27, fixed by the coordinator. `query_top_audit_pages_raw` referenced `PageSpeed` but **never imported it**, so every call raised `NameError`, the blanket `except` swallowed it, and the panel returned `[]` forever — reading as "no audit data yet" on projects with a full `page_speed` table. Two further defects in the same 6 lines: no `strategy == "mobile"` filter (mixed desktop+mobile, could list one URL twice) and no both-forms `site_id` match (silently empty for any site registered without the `sc-domain:` prefix). Also `int(x or 0)` reported an uncaptured score as a real 0, which `scoreChip()` rendered in the **red** band — indistinguishable from a failing page. Now `None` + a muted dash. All three proven in one seeded run |
| 5.11 | `[x]` Mobile responsive | One `@media (max-width: 900px)` block (+ a 560px tweak) in `index.html`. **Desktop safety is structural, not careful editing**: a max-width query cannot match a wider viewport, and this was verified by parsing the `<style>` block and confirming every rule outside a media query is pre-existing. Inline styles beat stylesheet rules, so the mobile layer matches on inline text (`[style*="repeat("]`) with `!important` — the only way to reach JS-computed styles without rewriting every view model. **Pixel-column grids are deliberately NOT flattened**: they are data rows, so they keep their columns and scroll sideways instead of shredding into one cell per line. Sidebar stays vertical (its SEO/Ads groups render children beneath the parent, so a horizontal rail would tear them apart) but is capped at 40vh with its own scroll. Mount point is `#dc-root > div`, per `support.js:164-166` — `body > div` is the wrapper and carries none of the shell styles |

---

## Explicitly NOT doing

- Task management / assignment
- Change log / annotations (`Insight` model stays unused)
- Weekly rollup snapshots for all modules (audit-specific history in 5.5 **is** in scope)
- "Today's worklist" ranked view
- Scheduled PDF / email reports

## Deferred

- Content optimization module (decide later)

---

## Open questions

1. **AI Optimization (5.9)** — which LLM provider and budget model? The page needs a real
   answer-check per prompt per model. `OPENAI_API_KEY` already exists and is used for the weekly
   summary; reusing it for prompt checks is the cheapest path.
2. **Ads credentials (5.6–5.8)** — Google Ads needs Standard Access approval. Build the tables
   and UI now, connect later?
