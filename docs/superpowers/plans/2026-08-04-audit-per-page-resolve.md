# Site Audit — Per-Page Resolve/Undo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user resolve/undo a single affected page inside any Site Audit check, not just the whole check at once, with the check itself auto-clearing once every one of its current pages is acknowledged.

**Architecture:** Generalize the existing check-level `auditResolved` store (`{check_id: [urls]}`, persisted via `apps/dashboard/services/mutation_state.py`) from "snapshot taken when the whole check was resolved" to "every URL acknowledged so far, one at a time or all at once." A new `toggle_resolved_page` service function + API endpoint writes one URL in/out of that same list; `build_site_audit_response`'s resolved check switches from exact-equality to a subset comparison so both the old bulk button and the new per-row buttons feed the same rule.

**Tech Stack:** Django 6 + DRF (backend), vanilla-JS class-component SPA templated via `#include` (frontend), Python `unittest`/DRF `APITestCase` (backend tests).

## Global Constraints

- No new database table or migration — this reuses the existing `ProjectSettings.data["auditResolved"]` JSON blob via `get_state`/`set_state`.
- The existing whole-check "Mark as resolved" button (`toggle_resolved_check`, `AuditToggleResolvedView`) must keep working exactly as it does today — it is not being replaced, only generalized underneath.
- Applies to **every** check in the Issues tab (the change is on the shared `checks[].pages[]` shape, not special-cased to `duplicate_titles`).
- The KEEP/REDIRECT/REWRITE duplicate-title badge already in `static/spa/src/js/pages/site_audit.js` / `static/spa/src/pages/pages.html` must keep rendering unchanged.
- Do not touch `static/spa/app/api.js` — it is an explicitly-labeled offline demo-mode mock, unrelated to the real backend this feature targets.
- No new client-side state machine on the frontend — a row's resolved/unresolved state is read straight from `pages[].resolved` in the `/audit` payload on every fetch, matching how `toggleResolvedCheck` already works.
- Every API view needs `@method_decorator(login_not_required, name="dispatch")` (project-wide rule — `LoginRequiredMiddleware` runs before DRF).

---

## Task 1: Backend — per-page resolve endpoint

**Files:**
- Modify: `apps/dashboard/services/site_audit_service.py:632-646` (add `toggle_resolved_page`, after the existing `toggle_resolved_check`)
- Modify: `apps/dashboard/services/site_audit_service.py:826-864` (subset-based `is_resolved`; add `pages[].resolved`)
- Modify: `apps/api/views.py:1499-1510` (add `AuditTogglePageResolvedView` after `AuditToggleResolvedView`)
- Modify: `apps/api/urls.py:36` (add the new route)
- Modify: `apps/api/tests/test_mutations.py` (new `AuditTogglePageResolvedTests` class, after `AuditToggleResolvedTests`)
- Modify: `.claude/api-reference.md:960-982` and `:1517` (document the new endpoint + the changed resolved rule)

**Interfaces:**
- Consumes: `get_state(site_id, key, default)` / `set_state(site_id, key, value)` from `apps/dashboard/services/mutation_state.py` (already used by `toggle_resolved_check`, unchanged signature).
- Produces: `toggle_resolved_page(site_id: str, check_id: str, url: str) -> list[str]` — returns the check's current acknowledged URL list, sorted. Consumed by `AuditTogglePageResolvedView` in this task, and by Task 2's frontend call to `POST /api/projects/<slug>/audit/toggle-page-resolved`.
- Produces: each dict in `build_site_audit_response(...)["checks"][i]["pages"]` gains `"resolved": bool`. Consumed by Task 2.

- [ ] **Step 1: Write the failing tests**

Open `apps/api/tests/test_mutations.py`. Insert a new test class immediately after `AuditToggleResolvedTests` ends (after the `test_recurrence_auto_unresolves` method, before `class AdsMutationTests(MutationTestBase):`):

```python
class AuditTogglePageResolvedTests(MutationTestBase):
    def test_toggle_resolves_single_page(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                                     format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"resolved": ["https://fusehealth.com/a"]})

        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in after["checks"] if c["id"] == "not_found_404")
        page = next(p for p in check["pages"] if p["url"] == "https://fusehealth.com/a")
        self.assertTrue(page["resolved"])

    def test_second_toggle_unresolves_the_page(self):
        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                              format="json")
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                                     format="json")
        self.assertEqual(resp.json(), {"resolved": []})

    def test_missing_url_is_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_missing_checkid_is_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                                     {"url": "https://fusehealth.com/a"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_check_resolves_once_every_current_page_is_acknowledged(self):
        """Fixture seeds ONE not_found_404 page (see MutationTestBase.setUp). Add a second
        so the check has two current pages, then confirm it only flips to resolved once
        BOTH are acknowledged -- not on the first one."""
        with get_session() as session:
            session.add(TechnicalIssue(site_id=SITE, url="https://fusehealth.com/b",
                                       issue_type="not_found_404", severity="high",
                                       description="404 page", detected_at=datetime(2026, 7, 3, 9)))

        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                              format="json")
        mid = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check_mid = next(c for c in mid["checks"] if c["id"] == "not_found_404")
        self.assertFalse(check_mid["resolved"])  # /b still unacknowledged
        page_a = next(p for p in check_mid["pages"] if p["url"] == "https://fusehealth.com/a")
        self.assertTrue(page_a["resolved"])

        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/b"},
                              format="json")
        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check_after = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check_after["resolved"])
        self.assertEqual(after["totals"]["errors"], 0)

    def test_whole_check_resolve_still_works(self):
        """Regression: the existing bulk 'Mark as resolved' button must still resolve a
        check in one call after is_resolved switches from equality to a subset check."""
        resp = self.client_auth.post("/api/projects/fusehealth/audit/toggle-resolved",
                                     {"checkId": "not_found_404"}, format="json")
        self.assertEqual(resp.status_code, 200)
        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check["resolved"])

    def test_resolved_check_reverts_when_a_new_unacknowledged_page_appears(self):
        """A check fully resolved page-by-page must drop back to active the moment a later
        crawl adds a page under it that was never acknowledged -- while the page that WAS
        acknowledged keeps its own resolved:true. Mirrors AuditToggleResolvedTests'
        test_recurrence_auto_unresolves, but for the per-page path."""
        self.client_auth.post("/api/projects/fusehealth/audit/toggle-page-resolved",
                              {"checkId": "not_found_404", "url": "https://fusehealth.com/a"},
                              format="json")
        resolved = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check = next(c for c in resolved["checks"] if c["id"] == "not_found_404")
        self.assertTrue(check["resolved"])

        with get_session() as session:
            session.add(TechnicalIssue(site_id=SITE, url="https://fusehealth.com/c",
                                       issue_type="not_found_404", severity="high",
                                       description="404 page", detected_at=datetime(2026, 7, 4, 9)))

        after = self.client_auth.get("/api/projects/fusehealth/audit").json()
        check_after = next(c for c in after["checks"] if c["id"] == "not_found_404")
        self.assertFalse(check_after["resolved"])
        page_a = next(p for p in check_after["pages"] if p["url"] == "https://fusehealth.com/a")
        page_c = next(p for p in check_after["pages"] if p["url"] == "https://fusehealth.com/c")
        self.assertTrue(page_a["resolved"])
        self.assertFalse(page_c["resolved"])
```

No new imports needed — `get_session`, `TechnicalIssue`, `datetime`, `SITE` are already imported at the top of this file (used by `AuditToggleResolvedTests.test_recurrence_auto_unresolves` already).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_mutations.AuditTogglePageResolvedTests -v 2`
Expected: every test **errors or fails** — `toggle-page-resolved` doesn't resolve to a view yet (404 on the POST), and `pages[].resolved` doesn't exist in the GET response yet.

- [ ] **Step 3: Add `toggle_resolved_page` to `site_audit_service.py`**

In `apps/dashboard/services/site_audit_service.py`, immediately after the existing `toggle_resolved_check` function (ends at line 646, right before `def query_audit_snapshots`), add:

```python
def toggle_resolved_page(site_id: str, check_id: str, url: str) -> list[str]:
    """Mark/unmark a single page as resolved within a check (HANDOFF_SPEC POST
    audit/toggle-page-resolved). Adds or removes `url` from the same `{check_id: [urls]}`
    store `toggle_resolved_check` writes -- the whole-check button and the per-page
    buttons share one list, so either one always sees what the other did. Returns the
    check's current acknowledged list, sorted."""
    resolved = get_state(site_id, "auditResolved", {})
    resolved = dict(resolved)
    urls = list(resolved.get(check_id, []))
    if url in urls:
        urls.remove(url)
    else:
        urls.append(url)
    if urls:
        resolved[check_id] = sorted(urls)
    elif check_id in resolved:
        del resolved[check_id]
    set_state(site_id, "auditResolved", resolved)
    return resolved.get(check_id, [])
```

- [ ] **Step 4: Switch `is_resolved` to a subset check and add `pages[].resolved`**

In the same file, find this block (currently lines 833-864):

```python
    resolved_snapshots = get_state(site_id, "auditResolved", {})
    for issue_type, items in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        title, category, how_to_fix = _humanize(issue_type)
        if issue_type.startswith("lh:") and items[0].description:
            how_to_fix = items[0].description

        severity = _SEVERITY_MAP.get((items[0].severity or "").lower(), "notice")
        is_hidden = issue_type in hidden_ids
        current_urls = sorted({i.url for i in items})
        is_resolved = (
            issue_type in resolved_snapshots
            and resolved_snapshots[issue_type] == current_urls
        )
        if not is_hidden and not is_resolved:  # HANDOFF_SPEC 2.4: totals over active checks only
            totals[_TOTALS_KEY[severity]] += len(items)
        checks.append({
            "id": issue_type,
            "severity": severity,
            "category": category,
            "title": title,
            "howToFix": how_to_fix,
            "count": len(items),
            "hidden": is_hidden,
            "resolved": is_resolved,
            "pages": [{
                "url": i.url,
                # None, not 0, when Lighthouse never scored this page -- same rule as
                # crawledPages[].score, so the two views of a page cannot disagree.
                "score": _page_score(i.url),
                "status": i.description or title,
            } for i in items],
        })
```

Replace it with:

```python
    resolved_snapshots = get_state(site_id, "auditResolved", {})
    for issue_type, items in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        title, category, how_to_fix = _humanize(issue_type)
        if issue_type.startswith("lh:") and items[0].description:
            how_to_fix = items[0].description

        severity = _SEVERITY_MAP.get((items[0].severity or "").lower(), "notice")
        is_hidden = issue_type in hidden_ids
        current_urls = sorted({i.url for i in items})
        # A check counts as resolved once every one of its CURRENT pages has been
        # individually acknowledged -- a subset check, not equality. This is what lets
        # the existing whole-check button (writes every current URL at once) and the
        # per-page button (writes one URL at a time) share one rule: the check clears
        # the moment its last unacknowledged page is acked, and drops back to active the
        # moment an unacknowledged page shows up under it (a new page tripping the same
        # check, or a later crawl whose affected set the old acknowledgment doesn't cover).
        acked_urls = set(resolved_snapshots.get(issue_type, []))
        is_resolved = bool(current_urls) and set(current_urls) <= acked_urls
        if not is_hidden and not is_resolved:  # HANDOFF_SPEC 2.4: totals over active checks only
            totals[_TOTALS_KEY[severity]] += len(items)
        checks.append({
            "id": issue_type,
            "severity": severity,
            "category": category,
            "title": title,
            "howToFix": how_to_fix,
            "count": len(items),
            "hidden": is_hidden,
            "resolved": is_resolved,
            "pages": [{
                "url": i.url,
                # None, not 0, when Lighthouse never scored this page -- same rule as
                # crawledPages[].score, so the two views of a page cannot disagree.
                "score": _page_score(i.url),
                "status": i.description or title,
                "resolved": i.url in acked_urls,
            } for i in items],
        })
```

- [ ] **Step 5: Add the view**

In `apps/api/views.py`, immediately after `AuditToggleResolvedView` (ends at line 1510, right before `class AdsStatusView`), add:

```python
@method_decorator(login_not_required, name="dispatch")
class AuditTogglePageResolvedView(APIView):
    """POST /api/projects/<slug>/audit/toggle-page-resolved {checkId, url} -> {resolved: [...]}.

    Writes to the same store as AuditToggleResolvedView -- toggles one URL in or out of
    that check's acknowledged list instead of writing the whole current set at once.
    """

    def post(self, request, slug):
        from apps.dashboard.services.site_audit_service import toggle_resolved_page

        site_id = resolve_project_or_404(slug).site_url
        check_id = (request.data.get("checkId") or "").strip()
        url = (request.data.get("url") or "").strip()
        if not check_id:
            return Response({"detail": "checkId is required"}, status=400)
        if not url:
            return Response({"detail": "url is required"}, status=400)
        return Response({"resolved": toggle_resolved_page(site_id, check_id, url)})
```

- [ ] **Step 6: Add the route**

In `apps/api/urls.py`, line 36 currently reads:

```python
    path("projects/<slug:slug>/audit/toggle-resolved", views.AuditToggleResolvedView.as_view(), name="audit-toggle-resolved"),
```

Add immediately after it:

```python
    path("projects/<slug:slug>/audit/toggle-page-resolved", views.AuditTogglePageResolvedView.as_view(), name="audit-toggle-page-resolved"),
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_mutations.AuditTogglePageResolvedTests apps.api.tests.test_mutations.AuditToggleResolvedTests apps.api.tests.test_mutations.AuditToggleCheckTests -v 2`
Expected: all PASS, including the pre-existing `AuditToggleResolvedTests` and `AuditToggleCheckTests` (regression check that the subset-comparison change didn't break the existing whole-check behavior).

- [ ] **Step 8: Run the full test file to check for unrelated breakage**

Run: `python manage.py test apps.api.tests.test_mutations -v 2`
Expected: all PASS.

- [ ] **Step 9: Update the API reference doc**

In `.claude/api-reference.md`, replace the two sections currently at lines 966-982:

```markdown
### `POST /api/projects/<slug>/audit/toggle-resolved`

Body `{"checkId": "not_found_404"}` (missing → **400**). Marks/unmarks a check resolved.
Returns `{"resolved": ["..."]}` — the full list of currently-resolved check ids.

Persisted in `ProjectSettings.data["auditResolved"]` as `{check_id: [affected urls at the
moment it was resolved]}`, not a plain id list — the URL snapshot is what lets
`build_site_audit_response` distinguish "still genuinely fixed" from "recurred" on the next
crawl **without a background job**: on every `/audit` read, a resolved check's current
affected-page URLs are diffed against the stored snapshot. Same set → stays resolved. Any
change (pages fixed, new pages tripping the same check) → renders active again this request
("auto-unresolve"); the stale snapshot is left in place rather than written back from the GET,
keeping `/audit` a pure read.

Resolved checks get `checks[].resolved: true` and are excluded from `/audit`'s `totals` and the
Overview error count — same treatment as hidden checks. The Issues tab's severity filter gets a
5th pill, `Resolved (n)`, alongside `Hidden (n)`.
```

with:

```markdown
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
```

Then find line 1517:

```markdown
| `/audit` + `/audit/toggle-check` + `/audit/toggle-resolved` | Site Audit |
```

Replace with:

```markdown
| `/audit` + `/audit/toggle-check` + `/audit/toggle-resolved` + `/audit/toggle-page-resolved` | Site Audit |
```

- [ ] **Step 10: Commit**

```bash
git add apps/dashboard/services/site_audit_service.py apps/api/views.py apps/api/urls.py apps/api/tests/test_mutations.py .claude/api-reference.md
git commit -m "feat(audit): add per-page resolve/undo alongside the whole-check toggle"
```

---

## Task 2: Frontend — per-row Resolve/Undo control

**Files:**
- Modify: `static/spa/src/js/app.js` (add `togglePageResolved`, after `toggleResolvedCheck`)
- Modify: `static/spa/src/js/pages/site_audit.js` (row-level styles + fields on each `pages[]` entry)
- Modify: `static/spa/src/pages/pages.html` (Action column: header + per-row cell)

**Interfaces:**
- Consumes: `POST /api/projects/<slug>/audit/toggle-page-resolved {checkId, url}` from Task 1.
- Consumes: `pg.resolved: bool` from the `/audit` payload (Task 1).
- Produces: `this.togglePageResolved(checkId, url)` on the app component, called from `site_audit.js`'s per-row `resolveToggle` handler.

- [ ] **Step 1: Add the click handler in `app.js`**

In `static/spa/src/js/app.js`, immediately after `toggleResolvedCheck` (ends at line 2121, right before the comment `/* The one comparator behind every sortable table here...`), add:

```js
  togglePageResolved(checkId, url) {
    const pid = this.state.projectId;
    window.FuseAPI.post('/api/projects/' + pid + '/audit/toggle-page-resolved', { checkId, url }).then(() => {
      if (!this._alive) return;
      /* Unlike toggleAuditCheck/toggleResolvedCheck, this does NOT reset auOpen/auAllPages --
         resolving one row is meant to happen one at a time inside an already-expanded check,
         and collapsing the panel after every click would make working through a long list
         of affected pages painful. */
      this.fetchTab('pages', pid, this.state.range, true);
    }).catch(err => {
      if (!this._alive) return;
      this.notify(this.errText(err, 'Could not update that page'));
    });
  }
```

- [ ] **Step 2: Add row styles and per-row fields in `site_audit.js`**

In `static/spa/src/js/pages/site_audit.js`, find the end of the `dupTitleBadge` function (it currently ends with):

```js
        if (desc.indexOf('Rewrite the title on this page') >= 0) {
          return { label: 'REWRITE', style: Object.assign({}, badgeBase, { background: '#fee2e2', color: '#b91c1c' }) };
        }
        return null;
      };
```

Immediately after that closing `};`, add:

```js
      /* Per-page resolve/undo (right end of each affected-page row, every check). Reads
         straight off `pg.resolved` from the payload each fetch -- no client-side tracking
         of which rows are acknowledged, matching how the whole-check resolve already works. */
      const resolvedTagStyle = { display: 'inline-flex', padding: '2px 8px', borderRadius: '999px', fontSize: '10.5px', fontWeight: 700, background: '#dcfce7', color: '#15803d', marginRight: '8px' };
      const resolveLinkStyle = { fontSize: '11.5px', fontWeight: 600, color: '#4f46e5', cursor: 'pointer' };
      const undoLinkStyle = { fontSize: '11.5px', fontWeight: 600, color: '#94a3b8', cursor: 'pointer' };
```

Then find the `pages: shown.map(u => {...})` block:

```js
            pages: shown.map(u => {
              const urlStr = typeof u === 'string' ? u : u.url;
              const pg2 = pgByUrl[urlStr];
              /* Both sources carry the same measured-or-null score by contract, so an
                 unscored page shows the neutral dash chip here too rather than a red 0. */
              const sc3 = pg2 ? pg2.score : (u && u.score !== undefined ? u.score : null);
              /* The recommendation badge is derived from the description regardless of what
                 the status column displays -- a page can have a real 200 status AND a
                 keep/redirect/rewrite recommendation at the same time. */
              const badge = dupTitleBadge(u && u.status);
              return {
                url: urlStr,
                score: scoreText(sc3),
                scoreStyle: scoreChip(sc3),
                status: (pg2 && pg2.statusCode) ? statusOf(pg2) : (u.status || '200'),
                hasBadge: !!badge,
                badgeLabel: badge ? badge.label : '',
                badgeStyle: badge ? badge.style : {}
              };
            }),
```

Replace it with:

```js
            pages: shown.map(u => {
              const urlStr = typeof u === 'string' ? u : u.url;
              const pg2 = pgByUrl[urlStr];
              /* Both sources carry the same measured-or-null score by contract, so an
                 unscored page shows the neutral dash chip here too rather than a red 0. */
              const sc3 = pg2 ? pg2.score : (u && u.score !== undefined ? u.score : null);
              /* The recommendation badge is derived from the description regardless of what
                 the status column displays -- a page can have a real 200 status AND a
                 keep/redirect/rewrite recommendation at the same time. */
              const badge = dupTitleBadge(u && u.status);
              const pageResolved = !!(u && u.resolved);
              return {
                url: urlStr,
                score: scoreText(sc3),
                scoreStyle: scoreChip(sc3),
                status: (pg2 && pg2.statusCode) ? statusOf(pg2) : (u.status || '200'),
                hasBadge: !!badge,
                badgeLabel: badge ? badge.label : '',
                badgeStyle: badge ? badge.style : {},
                resolved: pageResolved,
                resolvedTagStyle,
                resolveLabel: pageResolved ? 'Undo' : 'Resolve',
                resolveStyle: pageResolved ? undoLinkStyle : resolveLinkStyle,
                resolveToggle: (e) => { if (e && e.stopPropagation) e.stopPropagation(); this.togglePageResolved(c.id, urlStr); }
              };
            }),
```

- [ ] **Step 3: Add the Action column in `pages.html`**

In `static/spa/src/pages/pages.html`, find the affected-pages table header:

```html
<thead><tr style="text-align: left; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em;"><th style="font-weight: 500; padding: 6px 0;">Affected page</th><th style="font-weight: 500; padding: 6px 12px; text-align: center;">Page score</th><th style="font-weight: 500; padding: 6px 0; text-align: right;">Status</th></tr></thead>
```

Replace with:

```html
<thead><tr style="text-align: left; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em;"><th style="font-weight: 500; padding: 6px 0;">Affected page</th><th style="font-weight: 500; padding: 6px 12px; text-align: center;">Page score</th><th style="font-weight: 500; padding: 6px 0; text-align: right;">Status</th><th style="font-weight: 500; padding: 6px 0 6px 12px; text-align: right;">Action</th></tr></thead>
```

Then find the row markup:

```html
                              <tr style="border-top: 1px solid #f1f5f9;">
                                <td style="padding: 7px 0; font-family: monospace; font-size: 12px; color: #475569;">{{ pg.url }}<sc-if value="{{ pg.hasBadge }}" hint-placeholder-val="{{ false }}"><span style="{{ pg.badgeStyle }}">{{ pg.badgeLabel }}</span></sc-if></td>
                                <td style="padding: 7px 12px; text-align: center;"><span style="{{ pg.scoreStyle }}">{{ pg.score }}</span></td>
                                <td style="padding: 7px 0; text-align: right; color: #64748b; font-size: 12px;">{{ pg.status }}</td>
                              </tr>
```

Replace with:

```html
                              <tr style="border-top: 1px solid #f1f5f9;">
                                <td style="padding: 7px 0; font-family: monospace; font-size: 12px; color: #475569;">{{ pg.url }}<sc-if value="{{ pg.hasBadge }}" hint-placeholder-val="{{ false }}"><span style="{{ pg.badgeStyle }}">{{ pg.badgeLabel }}</span></sc-if></td>
                                <td style="padding: 7px 12px; text-align: center;"><span style="{{ pg.scoreStyle }}">{{ pg.score }}</span></td>
                                <td style="padding: 7px 0; text-align: right; color: #64748b; font-size: 12px;">{{ pg.status }}</td>
                                <td style="padding: 7px 0 7px 12px; text-align: right; white-space: nowrap;"><sc-if value="{{ pg.resolved }}" hint-placeholder-val="{{ false }}"><span style="{{ pg.resolvedTagStyle }}">Resolved</span></sc-if><span onClick="{{ pg.resolveToggle }}" style="{{ pg.resolveStyle }}" style-hover="opacity:0.7">{{ pg.resolveLabel }}</span></td>
                              </tr>
```

- [ ] **Step 4: Syntax-check the edited files**

Run: `node --check static/spa/src/js/app.js && node --check static/spa/src/js/pages/site_audit.js && echo OK`
Expected: `OK`

- [ ] **Step 5: Manual verification in the browser**

Start the dev server if it isn't already running (`python manage.py runserver`). Open the Site Audit → Issues tab for a real project, and:

1. Expand a check with more than one affected page (e.g. Duplicate title tags).
2. Confirm each row shows a "Resolve" link at the right end, and the KEEP/REDIRECT/REWRITE badge (where present) still renders next to the URL.
3. Click "Resolve" on one row. Confirm: the panel stays open (does not collapse), that row now shows a green "Resolved" tag + "Undo" link, and the check's top-level severity/count still shows it as active (since not every page is acknowledged yet).
4. Click "Resolve" on every remaining row in that check. On the last one, confirm the check now appears under the "Resolved" filter pill at the top of the Issues tab instead of the active list.
5. Reopen the check from the Resolved filter, click "Undo" on one row. Confirm that row flips back to "Resolve", and the check reappears in the active list.
6. Repeat steps 1–3 on a **different** check (not Duplicate title tags) to confirm the control isn't special-cased to one check type.

- [ ] **Step 6: Commit**

```bash
git add static/spa/src/js/app.js static/spa/src/js/pages/site_audit.js static/spa/src/pages/pages.html
git commit -m "feat(audit): per-row Resolve/Undo control in the Issues tab"
```
