# Domain Overview — persist every lookup, and stop throwing away paid data

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or
> superpowers:executing-plans. Steps use `- [ ]` for tracking.

**Goal:** Every Domain Overview lookup is stored permanently, so re-opening a URL costs nothing;
and the fields DataForSEO already bills us for — keyword difficulty, 12-month trends, rank
movement, featured-snippet wins — stop being parsed and discarded.

**Architecture:** One new analytics table, `domain_lookups`, holding one JSON payload per
(domain, path, location, block). Reads go DB → 24h cache → network, in that order, and the
network step only runs on a first lookup or an explicit **Refresh**. The connectors keep the
fields they already receive; the SPA renders them.

**Tech Stack:** SQLAlchemy analytics DB (SQLite dev / Postgres prod), Django 6 + DRF, no-build SPA.

## Global Constraints

- Analytics schema changes go through the `ensure_*` pattern in `pipeline/db/schema.py`. No
  Django migration touches `fusehealth.db`.
- New unique constraints get **new names** — `_swap_unique_constraint` detects by name.
- Never `None → 0`. A keyword with no difficulty on record is `null`, not easy.
- Live calls stay behind their own buttons, `ensure_budget()`, and `record_cost`.
- Tests use the temp-DB fixture from `.claude/skills.md` §8; targeted modules per task, full
  suite once at the end.
- Update `.claude/api-reference.md` and `features.md` with the behaviour they describe.

---

## Why this is the cost fix

Measured, not assumed (`llm_mentions/search/live`, real account):

```
limit 10 -> $0.1100      limit 25 -> $0.1250      => $0.10 per REQUEST + $0.001 per row
```

The request is the expense. So the only real levers are **make fewer requests** and **never
make the same one twice**. A 24h cache already covers "twice today"; a table covers "ever
again". After this, a domain looked up once is free forever until someone presses Refresh.

Per-URL cost today, from this account's own `connector_costs`:

| Press | Calls | Cost |
|---|---|---|
| Analyze | 1 × Labs ranked_keywords (limit 50) | $0.015 |
| Load backlinks | summary + backlinks(100) + anchors(60) | ~$0.030 |
| Find questions | 1 × llm_mentions/search (limit 100, chat_gpt) | $0.200 |

After this plan, each of those is paid **once per (domain, path, location)** rather than once
per 24h.

---

## What we are already paying for and discarding

From `dataforseo_labs/google/ranked_keywords/live`, per keyword — all of it in the response we
already buy:

| Field | Worth showing | Why |
|---|---|---|
| `keyword_properties.keyword_difficulty` | **Yes** | The one number that says "can I win this?" |
| `keyword_info.monthly_searches[12]` | **Yes** | Seasonality; a sparkline per keyword |
| `ranked_serp_element.serp_item.rank_changes` | **Yes** | `is_new` / `is_up` / `is_down` — movement |
| `...serp_item.is_featured_snippet` | **Yes** | Position 0 is not position 1 |
| `keyword_info.competition_level` | **Yes** | LOW/MEDIUM/HIGH, cheap to show |
| `metrics.organic.pos_*` | **Yes** | Full position distribution; we use 3 of 16 numbers |
| `avg_backlinks_info.*` | Later | Useful, but a second table's worth of detail |
| bid ranges, `impressions_info` | No | Paid-search planning, not this page's job |

From `llm_mentions/search/live`, per question:

| Field | Worth showing | Why |
|---|---|---|
| `fan_out_queries` | **Yes** | The sub-searches the engine ran — direct content targets |
| `sources[]` full list | **Yes** | Who got cited instead of us |
| `monthly_searches` | **Yes** | Is this question growing? |
| `brand_entities` | No | Noisy, rarely about us |

---

## File structure

| File | Responsibility |
|---|---|
| `pipeline/db/schema.py` | `DomainLookup` model + `ensure_domain_lookups()` |
| `pipeline/db/writer.py` | `upsert_domain_lookup()` |
| `apps/dashboard/services/domain_lookup_store.py` | **new** — read/write one block, age-aware |
| `apps/dashboard/services/domain_overview_service.py` | DB-first read order; `refresh=` flag |
| `pipeline/connectors/dataforseo_domain_overview.py` | Keep the discarded keyword fields |
| `static/spa/src/js/pages/domain_overview.js` | New columns, sparkline, movement chips |
| `static/spa/src/pages/domain_overview.html` | Markup for the above + the Questions tab |

---

### Task 1: `domain_lookups` table

**Files:** Create model + `ensure_domain_lookups()` in `pipeline/db/schema.py`; `upsert_domain_lookup()` in `pipeline/db/writer.py`; test `pipeline/db/tests/test_domain_lookups.py`.

**Interfaces:**
- Produces: `DomainLookup(domain, path, location, block, payload, fetched_at, cost)`,
  unique `(domain, path, location, block)` as `uq_domain_lookup`.
- Produces: `upsert_domain_lookup(session, records) -> int`.

- [ ] **Step 1: Failing test** — upsert two blocks for one domain; assert both stored, assert a
      re-upsert of the same key UPDATES rather than duplicating, assert `payload` round-trips a
      dict, assert a NULL `path` is stored as `""` (a NULL key column bypasses Postgres
      ON CONFLICT — the documented §9 trap).
- [ ] **Step 2: Run** `python manage.py test pipeline.db.tests.test_domain_lookups` → FAIL.
- [ ] **Step 3: Model.** `payload` is `Text` holding JSON (not a JSON column — SQLite and
      Postgres disagree on JSON semantics and every read here is whole-blob anyway).
      `path` defaults `""`, never NULL. `ensure_domain_lookups()` mirrors
      `ensure_tracked_competitor_project`: idempotent, never raises, called from `init_db` AND
      lazily from the writer so a deployed DB self-provisions.
- [ ] **Step 4: Writer.** `upsert_domain_lookup` uses `pipeline/db/dialect.upsert_insert`, dedupes
      by the conflict key first (`_dedupe_by_keys`), batches at `max_batch_size`.
- [ ] **Step 5: Run → PASS. Step 6: Commit** `feat(db): store every Domain Overview lookup`

### Task 2: The store — DB first, then cache, then network

**Files:** Create `apps/dashboard/services/domain_lookup_store.py`; test `apps/dashboard/services/tests/test_domain_lookup_store.py`.

**Interfaces:**
- Produces: `load_block(domain, path, location, block) -> dict | None` (adds `storedAt`, `ageDays`).
- Produces: `save_block(domain, path, location, block, payload, cost) -> None` (never raises).

- [ ] **Step 1: Failing test** — save then load returns the payload with `storedAt` set; loading
      a block never saved returns `None`; a save failure logs and returns without raising
      (services do not raise); `ageDays` is computed from `fetched_at`.
- [ ] **Step 2: Run → FAIL. Step 3: Implement.** JSON encode/decode at this boundary only.
- [ ] **Step 4: Run → PASS. Step 5: Commit** `feat(domain-overview): a store for looked-up blocks`

### Task 3: Read order, and an explicit Refresh

**Files:** Modify `apps/dashboard/services/domain_overview_service.py` (all three `fetch_*_block`
functions + `run_domain_overview`); modify `apps/api/views.py` (`DomainOverviewView` reads
`refresh`); test `apps/api/tests/test_domain_overview_persistence.py`.

**Interfaces:**
- Produces: `fetch_*_block(target, ..., allow_fetch=True, refresh=False)`.
- Produces: `run_domain_overview(..., refresh: bool = False)`.

- [ ] **Step 1: Failing tests** — (a) a second lookup of a domain stored last week makes NO
      network call and returns `storedAt`; (b) `refresh=True` DOES call and overwrites the row;
      (c) `allow_fetch=False` (the PDF) still reads the stored row, so a report of a domain
      looked up a month ago is complete and costs nothing; (d) a stored row is returned even
      when the 24h cache has expired.
- [ ] **Step 2: Run → FAIL.** Today the store does not exist, so every expiry re-buys.
- [ ] **Step 3: Implement** the order: `refresh` ? network : (DB → cache → network). Every
      returned block carries `storedAt` and `ageDays` so the UI can show "as of" honestly and
      offer Refresh rather than silently serving old data as new.
- [ ] **Step 4: Run → PASS. Step 5: Commit** `perf(domain-overview): a domain is paid for once, not once a day`

### Task 4: Keep the keyword fields we already buy

**Files:** Modify `pipeline/connectors/dataforseo_domain_overview.py`; test `pipeline/connectors/tests/test_domain_overview_fields.py`.

**Interfaces:**
- Produces, per keyword: existing 7 fields **plus** `kd`, `competition`, `monthly` (12 ints),
  `movement` (`new|up|down|lost|flat`), `rankAbsolute`, `featuredSnippet`, `title`.
- Produces, in `metrics`: the full `pos_*` distribution.

- [ ] **Step 1: Failing test** — parse a fixture trimmed from a REAL captured response (build it
      from a live call, never from documentation — §9 trap) and assert each new field; assert a
      missing `keyword_difficulty` stays `None` and is NOT 0; assert `monthly` is [] when absent.
- [ ] **Step 2: Run → FAIL. Step 3: Implement.** No new API call and no cost change: every field
      is already in the response being parsed.
- [ ] **Step 4: Run → PASS. Step 5: Commit** `feat(domain-overview): show the keyword data we already pay for`

### Task 5: The UI — new columns and the AI Questions tab

**Files:** Modify `static/spa/src/js/pages/domain_overview.js`, `static/spa/src/pages/domain_overview.html`; test `static/spa/tests/domain_overview_columns.test.js`.

- [ ] **Step 1: Failing test** — the view-model builder maps KD to a colour band, renders `null`
      KD as `—` (never 0 or green), builds a 12-point sparkline from `monthly`, and emits a
      movement chip only when movement is known.
- [ ] **Step 2: Run → FAIL. Step 3: Implement.** Keywords table gains KD, trend sparkline,
      movement chip, featured-snippet marker. New **AI Questions** tab: question, volume, trend,
      Cited/Seen badge, our URL, expandable answer, fan-out queries, and who was cited instead.
      An "as of <date> · Refresh" line on every block that came from the store.
- [ ] **Step 4: Run → PASS. Step 5: Commit** `feat(domain-overview): AI questions tab and the fuller keyword table`

### Task 6: PDF + docs

**Files:** Modify `apps/dashboard/services/domain_overview_report_service.py`, `templates/reports/domain_overview.html`, `.claude/api-reference.md`, `.claude/features.md`.

- [ ] **Step 1** Report gains the Questions section and the new keyword columns, reading the
      store with `allow_fetch=False` — a report never buys anything.
- [ ] **Step 2** Docs: the new table, the read order, the measured cost model, the per-block
      limits. **Step 3: Commit** `docs: record the Domain Overview store and its cost model`

### Task 7: Close-out

- [ ] Full `python manage.py test`.
- [ ] Add to `.claude/skills.md` §9: "a 24h cache is not persistence — a metered lookup a user
      may repeat belongs in a table, keyed and refreshable."

## Open question for the owner

Google AI Overviews is currently off (`QUESTIONS_PLATFORMS = ("chat_gpt",)`), which halves the
questions cost. With the store in place a second platform is paid once per domain rather than
daily, so enabling it becomes ~$0.20 one-off. Worth a toggle in Task 5 rather than a constant.
