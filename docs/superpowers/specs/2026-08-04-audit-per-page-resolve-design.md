# Site Audit — per-page resolve/undo — design

**Date:** 2026-08-04
**Status:** approved, ready for an implementation plan

---

## 1. The problem

The Issues tab's "Mark as resolved" only works at the level of a whole check. Clicking it on
**Duplicate title tags** resolves all 107 affected pages in one shot, whether or not the team has
actually looked at each one. There is no way to work through a check's affected pages one at a
time, track which specific pages have been handled, or have the check quietly clear itself once
every page in it has actually been dealt with.

The team lead wants row-level acknowledgment: each affected page gets its own Resolve/Undo
control, a page shows a "Resolved" tag once acknowledged, and the section itself only drops out of
the active view once every one of its currently-affected pages has been individually resolved.

---

## 2. Scope

**In:**

* A Resolve/Undo control on every row of every check's affected-pages table (not just Duplicate
  title tags — this is generic on `checks[].pages[]`, so it applies everywhere in the Issues tab).
* A "Resolved" tag on an acknowledged row.
* The existing whole-check "Mark as resolved" keeps working as a bulk shortcut, not a second
  system — see §3.
* A check appears in the existing top-level "Resolved" filter once every page currently reported
  under it has been individually acknowledged, and drops back to active the moment a page's
  affected-set changes such that something in it is not yet acknowledged (new page joins the
  group, etc.) — the same auto-behavior the check-level toggle already has today, just computed
  from the bottom up instead of set by one click.

**Out, and deliberately so:**

* **A separate "resolved" sub-view inside an expanded check.** Resolved rows stay inline in the
  same list, tagged, rather than moving to a separate panel — decided in clarifying questions:
  the existing top-level filter row is the only place "Resolved" is surfaced as a view.
  Continuing to render resolved rows inline (rather than removing them from the expanded list)
  also means the row's KEEP/REDIRECT/REWRITE duplicate-title recommendation stays visible after
  it's marked resolved, which matters for anyone auditing what was actually done.
* **History of "was this ever resolved before."** No audit trail of past resolve/undo cycles —
  just current acknowledgment state, matching how `auditHidden`/`auditResolved` already work.
* **The offline demo-mode mock layer** (`static/spa/app/api.js`, explicitly commented "replaced
  by real DB later"). Not touched.

---

## 3. Data model

No new table. `auditResolved` — already persisted per-project through
`apps/dashboard/services/mutation_state.py` — keeps its existing shape, `{check_id: [urls]}`, but
its meaning generalizes:

* **Before:** the snapshot of affected URLs taken at the instant the whole check was marked
  resolved; equality-compared against the check's current URLs on every read.
* **After:** the accumulated set of URLs acknowledged so far for that check, built up one row at a
  time (or all at once via the existing whole-check button) — a check is "resolved" when its
  current URL set is a **subset** of this list, not equal to it.

This is a strict generalization: a single click of the existing whole-check button still produces
exactly the old snapshot-equals-current behavior as a special case (it writes every currently
affected URL into the list at once), so nothing about today's UX changes unless a user starts
using the new per-row controls.

`toggle_resolved_check(site_id, check_id)` (existing) is unchanged. New:

```python
def toggle_resolved_page(site_id: str, check_id: str, url: str) -> list[str]:
    """Add/remove one URL from this check's acknowledged list. Returns the check's
    current acknowledged list, sorted."""
```

`build_site_audit_response`'s per-check `is_resolved` computation changes from:

```python
is_resolved = issue_type in resolved_snapshots and resolved_snapshots[issue_type] == current_urls
```

to:

```python
acked = set(resolved_snapshots.get(issue_type, []))
is_resolved = bool(current_urls) and set(current_urls) <= acked
```

Each entry in `checks[].pages[]` gains `"resolved": url in acked`.

---

## 4. API

```
POST /api/projects/<slug>/audit/toggle-page-resolved   {checkId, url}
                                                        -> {"resolved": [...]}     # this check's acknowledged list
```

Mirrors `POST /api/projects/<slug>/audit/toggle-resolved` exactly: same view pattern
(`AuditTogglePageResolvedView`), same `@method_decorator(login_not_required, name="dispatch")`,
same 400 on a missing `checkId`/`url`, same `resolve_project_or_404` for the slug.

---

## 5. Frontend

`static/spa/src/pages/pages.html` / `static/spa/src/js/pages/site_audit.js` — the affected-pages
table's per-row action, added at the right end of each row alongside the existing
KEEP/REDIRECT/REWRITE badge (which stays where it is, in the URL cell):

* Unresolved row: a small "Resolve" button.
* Resolved row: a green "Resolved" tag + a small "Undo" action.

Both call the new endpoint and refetch the audit tab, following the exact pattern
`toggleResolvedCheck` already uses in `app.js` (`this.fetchTab('pages', pid, this.state.range,
true)` on success, a toast via `this.notify(...)` on failure). No new client-side state machine —
the resolved/unresolved read comes straight from `pages[].resolved` in the payload on every fetch.

---

## 6. Changes by file

| File | Change |
|---|---|
| `apps/dashboard/services/site_audit_service.py` | `toggle_resolved_page()`; subset-based `is_resolved`; `pages[].resolved` in the payload |
| `apps/api/views.py`, `apps/api/urls.py` | `POST /api/projects/<slug>/audit/toggle-page-resolved` |
| `static/spa/src/pages/pages.html` | per-row Resolve/Undo control + Resolved tag |
| `static/spa/src/js/pages/site_audit.js` | wires `pg.resolved` / the new action into each row's render data |
| `static/spa/src/js/app.js` | `togglePageResolved(checkId, url)`, same pattern as `toggleResolvedCheck` |
| `apps/api/tests/test_mutations.py` | tests for the new endpoint |
| `.claude/api-reference.md` | document the new endpoint, same change as the behavior |

---

## 7. Testing

* `toggle_resolved_page` adds a URL on first call, removes it on second call, for the right
  `check_id` only (does not touch other checks' lists).
* Subset `is_resolved`: a check with 3 currently-affected pages is not resolved with 2
  acknowledged, becomes resolved on the 3rd, and drops back to unresolved the moment a 4th
  (unacknowledged) page appears in a later crawl — while the original 3 keep their individual
  `resolved: true`.
* The existing whole-check `toggle_resolved_check` still resolves a check in one call (regression
  check on the generalized subset logic).
* `POST .../toggle-page-resolved` — 400 on missing `checkId`/`url`, 404 on unknown slug, 200 +
  correct list on success.
* Manual pass in the browser: resolve every row in **Duplicate title tags** one at a time, confirm
  it moves into the "Resolved" filter on the last one; Undo one row, confirm it reappears active
  and the row's own state flips back; confirm the KEEP/REDIRECT/REWRITE badge is still visible on
  a resolved row.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| A stale acknowledged URL (page no longer affected) silently masks nothing, since the subset check only looks at currently-affected URLs | No mitigation needed — this is by design, not a bug |
| Two browser tabs racing on the same check's list (read-modify-write on a JSON blob) | Same exposure as the existing `auditHidden`/`auditResolved` writes today; not introduced by this change, not addressed here |
| Per-row control on a check with hundreds of pages (e.g. a 500-row capped list) adds a lot of buttons | Table already virtualizes via `PAGE_PREVIEW`/`RENDER_MAX`; no additional windowing needed |
