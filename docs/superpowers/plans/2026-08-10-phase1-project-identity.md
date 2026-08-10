# Phase 1 — Project Identity & Data Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every write path resolve a project by its primary key (`site_pk`), so edits can never land on a sibling project sharing the same domain, and make the Edit-modal keyword save stop destroying stored keyword metrics.

**Architecture:** Thread `sites.id` (as `site_pk`) from `resolve_project_or_404` through `apply_settings_update`, `set_tracked_competitors`, and `persist_keyword_opportunities`; migrate `tracked_competitors` and `keyword_opportunities` onto pk-led unique keys using the exact `saved_keywords` migration recipe already in `pipeline/db/schema.py` (`_alter_missing_columns` → backfill → `_swap_unique_constraint`, wrapped in a lazy idempotent `ensure_*` function). Replace the keywords bulk PUT's clear-and-rewrite with a name-keyed reconcile that inserts/deletes but never updates surviving rows. Remove `get_site()`'s silent first-active fallback for a *given* id, and widen the positioning read queries to `resolve_site_ids()`.

**Tech Stack:** Django 6 + DRF, SQLAlchemy (analytics DB, SQLite dev / Postgres prod), vanilla-React SPA (no build step).

## Global Constraints

- Analytics DB schema changes only via the `ensure_*` pattern in `pipeline/db/schema.py` — no Django migrations touch `fusehealth.db`.
- New unique constraints get **new names** (the swap detector keys on the name).
- A NULL in a unique-key column bypasses Postgres ON CONFLICT — pk columns get `DEFAULT UNOWNED_SITE_PK`, never NULL.
- Service functions never raise; they log and return a safe shape.
- No `None → 0` coercion anywhere (zero and unknown are different facts).
- Every API view keeps `@method_decorator(login_not_required, name="dispatch")`.
- Tests use the temp-DB fixture from `.claude/skills.md` §8 verbatim; targeted test modules per task, full `manage.py test` once at the end of the phase.
- Update `.claude/skills.md` / `api-reference.md` in the same commit as the behaviour they describe.

---

### Task 1: `tracked_competitors` becomes project-scoped (schema + service)

**Files:**
- Modify: `pipeline/db/schema.py` (TrackedCompetitor model ~:627-642; new spec tuples beside `_SAVED_KEYWORD_PROJECT_KEY` ~:1081; new `ensure_tracked_competitor_project()` beside `ensure_saved_keyword_project` ~:1325; call in `init_db`)
- Modify: `pipeline/services/competitor_service.py` (all four public functions)
- Test: `pipeline/services/tests/test_competitor_service.py` (new)

**Interfaces:**
- Produces: `get_tracked_competitors(site_id, limit=5, site_pk=None)`, `is_overridden(site_id, site_pk=None)`, `set_tracked_competitors(site_id, domains, site_pk=None)` — `site_pk` scopes alone when given; fallback widens `site_id` through `resolve_site_ids()`.
- Produces: `ensure_tracked_competitor_project(session_or_engine) -> bool` (idempotent, never raises).

- [ ] **Step 1: Failing test** — two Sites, same `site_url` `dup.com`, pk A and B. `set_tracked_competitors("dup.com", ["compB.com"], site_pk=B)` then `get_tracked_competitors("dup.com", site_pk=A)` must NOT contain `compB.com`; `set` for B must not delete A's rows. Also: rows written pre-migration (site_pk = UNOWNED) are readable via the fallback path and get backfilled to the oldest project.
- [ ] **Step 2: Run** `python manage.py test pipeline.services.tests.test_competitor_service -v 2` → FAIL (no `site_pk` kwarg).
- [ ] **Step 3: Schema** — model: add `site_pk = Column(Integer, nullable=False, index=True, default=UNOWNED_SITE_PK, server_default=str(UNOWNED_SITE_PK))`; constraint becomes `UniqueConstraint("site_pk", "competitor_domain", name="uq_tracked_competitor_project")`. Spec tuples:

```python
_TRACKED_COMPETITORS_ADDED_COLUMNS = (("site_pk", "INTEGER", UNOWNED_SITE_PK),)
_TRACKED_COMPETITOR_PROJECT_KEY = (
    "tracked_competitors", "uq_tracked_competitor_site", "uq_tracked_competitor_project",
    ("site_pk", "competitor_domain"),
)
```

`_backfill_tracked_competitor_projects(conn)`: same shape as `_backfill_saved_keyword_projects` minus the location tiebreak (this table has none) — owners map spelling → oldest pk via `resolve_site_ids`, rows with no matching project keep UNOWNED. `ensure_tracked_competitor_project()`: alter → backfill → swap, wrapped in try/except that logs and returns bool. Wire into `init_db` after `ensure_saved_keyword_project` and call lazily from `competitor_service` (replacing the bare `ensure_tables` calls) so deployed DBs self-provision on first read.
- [ ] **Step 4: Service** — add `site_pk` kwarg to all four functions; a local `_scope(site_id, site_pk)` mirrors `saved_keyword_service.project_scope` (pk alone when given; else `TrackedCompetitor.site_id.in_(resolve_site_ids(site_id))`). `set_tracked_competitors` deletes with `_scope` and inserts rows carrying `"site_pk": site_pk or UNOWNED_SITE_PK`. Reads in `get_tracked_competitors`/`is_overridden` use `_scope`.
- [ ] **Step 5: Run test** → PASS. **Step 6: Commit** `fix(competitors): scope tracked_competitors by project pk, not domain string`

### Task 2: Settings writes resolve by pk (`apply_settings_update`)

**Files:**
- Modify: `apps/dashboard/services/settings_service.py:682` (signature), `:713-738` (credentials branch), `:740-766` (project branch)
- Modify: `apps/api/views.py:825` (pass `site_pk=site.id`)
- Test: extend the existing settings test module under `apps/api/tests/` (locate `test_settings*.py`; add class `SiblingProjectSettingsTests`)

**Interfaces:**
- Consumes: `get_site_by_pk(session, site_pk)` (`pipeline/services/site_service.py:127`), Task 1's `set_tracked_competitors(..., site_pk=...)`.
- Produces: `apply_settings_update(site_id, body, site_pk=None) -> dict`.

- [ ] **Step 1: Failing test** — seed two Sites on one `site_url` (slugs `dup`, `dup-2`); `PUT /api/projects/dup-2/settings` with `{"project": {"location": "Las Vegas"}}`; assert `dup-2`'s row changed and `dup`'s did **not** (today it's the reverse). Second test: pk/site_url mismatch returns `{"error": ...}` and writes nothing.
- [ ] **Step 2: Run** → FAIL (older sibling mutated).
- [ ] **Step 3: Implement** — signature `def apply_settings_update(site_id: str, body: dict, site_pk: int | None = None) -> dict:`. One resolver used by both branches:

```python
def _resolve_write_target(session, site_id, site_pk):
    """The sites row a settings write may touch. Pk wins; a pk/domain mismatch refuses
    (never falls through to first-match — that fallthrough IS bug C3a). String match is
    only for pk-less legacy callers, and logs that it can't distinguish siblings."""
    if site_pk:
        site = get_site_by_pk(session, site_pk)
        if site is None:
            return None, {"error": "Project no longer exists."}
        if site.site_url != site_id:
            logger.error("[settings] refused write: site_pk=%s is %r, caller said %r",
                         site_pk, site.site_url, site_id)
            return None, {"error": "Project mismatch — reload and try again."}
        return site, None
    logger.warning("[settings] pk-less write for %r — sibling projects are ambiguous", site_id)
    site = session.execute(select(Site).where(Site.site_url == site_id)).scalars().first()
    return site, None
```

Both branches use it; an error dict propagates as the function's return (the view already 400s on `"error"`). `set_tracked_competitors(site_id, proj["competitors"], site_pk=site_pk)`. View passes `site_pk=site.id`.
- [ ] **Step 4: Run test + the module's existing tests** → PASS. **Step 5: Commit** `fix(settings): resolve write target by project pk — sibling domains no longer cross-write (C3a)`

### Task 3: Keywords PUT becomes a name-keyed reconcile

**Files:**
- Create: `reconcile_saved_keywords()` in `pipeline/services/saved_keyword_service.py`
- Modify: `apps/api/views.py:450-497` (`ProjectKeywordsView.put`)
- Modify: `static/spa/src/js/pages/positioning.js:29-73` (`ptEditSave`)
- Test: `pipeline/services/tests/test_saved_keyword_reconcile.py` (new) + extend the API test for the PUT
- Docs: `.claude/api-reference.md` PUT /keywords response

**Interfaces:**
- Produces: `reconcile_saved_keywords(site_id, rows, location=None, site_pk=None) -> dict` returning `{"added": int, "removed": int, "kept": int}`. `rows` are the same dicts `save_keywords` takes; metrics apply to **new** rows only.

- [ ] **Step 1: Failing tests** — (a) existing row `{"kw": "festival staffing", volume: 480}`; reconcile with `[{"keyword": "festival staffing"}, {"keyword": "new kw"}]` → survivor keeps volume 480 (today's clear+rewrite nulls it), `new kw` added with `search_volume=None`, kept=1 added=1; (b) omitted keyword deleted; (c) case/whitespace variant ("Festival Staffing ") counts as the same keyword — kept, not delete+insert; (d) idempotent: same input twice → second call `{added: 0, removed: 0}`; (e) new row WITH real metrics (Explorer path) stores them.
- [ ] **Step 2: Run** → FAIL (function missing).
- [ ] **Step 3: Implement** in `saved_keyword_service.py`:

```python
def reconcile_saved_keywords(site_id, rows, location=None, site_pk=None):
    """Insert missing, delete removed, NEVER touch surviving rows' metrics. Identity is the
    cleaned, case-folded keyword. Exists because the bulk PUT's clear+rewrite let the Edit
    modal overwrite every stored volume with a fabricated 0 (report C3c)."""
    incoming = {}
    for row in rows or []:
        rec = _clean_row(row if isinstance(row, dict) else {"keyword": row}, location)
        if rec:
            incoming.setdefault(rec["keyword"].lower(), rec)
    existing = {(r["keyword"] or "").strip().lower(): r for r in list_saved_keywords(site_id, site_pk)}
    to_add = [incoming[k] for k in incoming.keys() - existing.keys()]
    to_remove = [existing[k]["keyword"] for k in existing.keys() - incoming.keys()]
    added = save_keywords(site_id, to_add, location, site_pk=site_pk) if to_add else 0
    removed = 0
    for kw in to_remove:
        if delete_saved_keyword(site_id, kw, location or "", site_pk=site_pk):
            removed += 1
    return {"added": added, "removed": removed,
            "kept": len(incoming.keys() & existing.keys())}
```

- [ ] **Step 4: View** — `put` builds the same `rows` mapping it does today (metrics travel for the Explorer caller) but calls `reconcile_saved_keywords(site_id, rows, location, site_pk=site.id)` instead of clear+save; response `{"ok": True, **result}`. The `clear_saved_keywords` import stays only for whoever else uses it. Docstring updated to name C3c.
- [ ] **Step 5: Frontend** — `positioning.js:33`: `kwsToSend = kwLines.map(kw => ({ kw: kw }))` (no fabricated volume/intent). Sequence the halves: settings PUT `.then` keywords PUT (location lands before new rows are stamped), keeping the existing per-half error copy; on success additionally refetch `/api/projects` (reuses the loader `positioning.js` already calls after create/delete at `:184/:372`). If `kwLines` is empty and the modal opened with a non-empty list, `window.confirm('Remove all N tracked keywords?')` guards the save.
- [ ] **Step 6: Run** targeted service + API keyword tests → PASS. **Step 7: Commit** `fix(keywords): PUT reconciles by name — survivors keep their metrics (C3c)`

### Task 4: `keyword_opportunities` scoped by project (P2)

**Files:**
- Modify: `pipeline/db/schema.py` (KeywordOpportunity ~:830-850 + spec tuples + `ensure_keyword_opportunity_project()`), `apps/dashboard/services/positioning_service.py:200-277` (+ its caller ~:503 and the table's read query), `apps/api/views.py` positions view (thread `site_pk` into `build_positions_response` if not already passed)
- Test: extend `apps/api/tests/test_positions*.py`

**Interfaces:**
- Produces: `persist_keyword_opportunities(site_id, opportunities, site_pk=None)`; upsert keys `("site_pk", "keyword")`; new constraint `uq_opportunity_project_keyword`.

- [ ] **Step 1: Failing test** — project A persists opportunities for keywords {x, y}; project B (same domain) persists {z}; assert A's rows still exist (today B's persist deletes them).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Schema** — add `site_pk` column (same spec as Task 1), constraint → `("site_pk", "keyword")` named `uq_opportunity_project_keyword`, `ensure_keyword_opportunity_project()` (alter → swap; **no backfill** — this is a computed cache; instead the persist function deletes rows `site_id.in_(resolve_site_ids(site_id)) & site_pk == UNOWNED_SITE_PK` once, absorbing legacy rows). Wire into `init_db`; call lazily at the top of `persist_keyword_opportunities` and the read query.
- [ ] **Step 4: Service** — records carry `site_pk or UNOWNED_SITE_PK`; the stale-delete and the read query scope by `site_pk` when given; upsert `keys = ("site_pk", "keyword")`. Thread `site_pk` from the view through `build_positions_response` (verify signature at implementation; add kwarg defaulting None).
- [ ] **Step 5: Run** → PASS. **Step 6: Commit** `fix(positions): keyword_opportunities scoped by project — GET no longer deletes sibling data (P2)`

### Task 5: `get_site` stops guessing (P7) + positioning reads widen (P1)

**Files:**
- Modify: `pipeline/services/site_service.py:113-124`, `pipeline/connectors/dataforseo_serp.py` (`_resolve_site` ~:126), `apps/dashboard/services/shared_queries.py` (13 exact `site_id ==` reads: :227, :313, :329, :453, :463, :473, :481, :494, :629, :638, :662, :678, :695 — verify each at implementation), `apps/dashboard/services/keywords_service.py:126`
- Test: `pipeline/connectors/tests/test_serp_unknown_site.py` (new), extend a shared_queries/positions test seeding rows under `https://example.com/` while the project is `sc-domain:example.com`

**Interfaces:**
- Produces: `get_site(session, site_id)` returns `None` for a **given-but-unknown** id (no fallback); `get_site(session)` (no id) keeps first-active behaviour — `get_default_site_id` depends on it.

- [ ] **Step 1: Failing tests** — (a) `get_site(session, "nope.example")` is `None`; (b) SERP connector `fetch(site_id="nope.example")` raises (→ visible SyncLog error) instead of writing under the first active site; (c) positions distribution sees `keyword_rankings` rows stored under an alternate spelling.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** — `get_site`: `if site_id: ... return None` after the warning (drop the fallthrough); audit remaining callers by grep (`get_site(`) — `resolve_tracking_location` already handles `None`. `_resolve_site`: on `None`, `raise ValueError(f"unknown site_id {site_id!r} — refusing to sync under another site's key")` from inside `fetch()`. Reads: `KeywordRanking.site_id.in_(resolve_site_ids(site_id))` (import once per module, matching `views.latest_ranking_anchor`).
- [ ] **Step 4: Run** targeted tests → PASS. **Step 5: Commit** `fix(pipeline): unknown site ids fail loudly; positioning reads match all site-id spellings (P1, P7)`

### Task 6: Phase close-out

- [ ] Update `.claude/skills.md` §9: mark the C3a/P2 traps fixed with the pk-threading rule ("a write path that resolves a project by site_url .first() is the bug"); note the two new `ensure_*` functions. Update `api-reference.md` for the PUT /keywords response shape.
- [ ] Run the FULL suite once: `python manage.py test` — fix fallout.
- [ ] Commit `docs: record project-pk write rule; phase 1 complete`

## Self-review notes
- Task 1 before Task 2 because `apply_settings_update` passes `site_pk` into `set_tracked_competitors`.
- The reconcile intentionally accepts metric-bearing rows: the Explorer "send to project" flow PUTs real volumes for NEW keywords; only survivors are immutable.
- `clear_saved_keywords` remains for legitimate wipe flows; the PUT just stops using it.
- Windows dev note: schema swap on SQLite rebuilds the table — dev DBs only; prod is Postgres two-statement swap.
