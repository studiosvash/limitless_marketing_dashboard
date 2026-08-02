# Sync cancellation + manual-refresh freshness guard — design

**Date:** 2026-08-02
**Status:** approved, ready for an implementation plan

---

## 1. The problem

Two complaints, one root cause: **a manual refresh spends metered API budget with no way to
prevent it and no way to take it back.**

1. **No way to stop a running sync.** Once `start_sync_run` spawns `manage.py run_sync`, the
   only exits are: finishing, crashing, or the reaper killing the row after `RUN_TIMEOUT`
   (2 hours). Click "Fetch Backlinks" on the wrong page and you watch it burn.
2. **No way to prevent a pointless one.** `start_sync_run` checks exactly one thing — is a run
   already in flight for this site. It never asks "did these connectors run twenty minutes
   ago?" So re-clicking a button re-spends DataForSEO credits on data that has not changed.

The second is the more interesting gap, because **the answer already exists in the codebase and
is only wired to the wrong caller.** `apps/sync/scheduling.py` has a complete per-module
freshness system — `CADENCE_INTERVALS` (12h/daily/weekly/biweekly/monthly/manual), a 6-hour
`FAILED_RUN_BACKOFF`, `last_run_at`, `next_run_for` — and Settings → Automation already edits
it. But it governs only `run_scheduled_syncs`. Every manual button press walks straight past it.

---

## 2. Scope

**In:**

* Stop a running sync from the SPA's sync banner.
* Skip connectors that synced successfully within a configurable window, on **manual** runs.
* A settings control for that window.

**Out, and deliberately so:**

* **Pause / resume.** Resuming requires persisting mid-connector state (which of 50 pages was
  `url_inspection` on?) and would need per-connector resume logic in all 16 connectors. Stop +
  click again recovers most of the value for a fraction of the work and none of the risk.
* **Per-connector or per-module freshness windows.** One global number is enough for a 2–3
  person team. Per-module can be added later without redesigning anything; per-connector would
  mean 16 dropdowns in a settings page nobody reads.
* **Changing scheduled-sync behaviour.** The cadences already are the scheduler's freshness
  logic. See §4.2.

---

## 3. Feature A — Stop a running sync

### 3.1 Behaviour

A **Stop** control appears in the sync progress banner whenever a run is in flight. Clicking it:

1. Marks the run `cancelled` in the database.
2. Kills the `run_sync` OS process by its stored `pid`.

**In that order, and both.** The database flag is the *reliable* half: `sync_all` / `sync_page`
re-read it between connectors, so even if the kill fails (stale pid, permission error, the
process already gone) the run still stops before the next connector. The kill is the *fast*
half: it is what makes Stop feel instant instead of "instant after this 600-second poll".

**No confirmation dialog.** A Stop button that asks "are you sure?" is a Stop button that
doesn't stop. Recovery is re-clicking Fetch.

### 3.2 What is kept, what is saved

**Kept:** every record already written. `sync_page`/`sync_all` write per connector, so a run
stopped at step 2 of 5 keeps steps 1 and 2 in full. This matches the codebase's existing stance
on killed runs (`ORPHANED_CONNECTOR_MESSAGE`: *"Any rows it had already written were kept"*).

**Saved:** every connector that had not started. Stopping a 5-connector `audit` at step 2 skips
3 connectors including the metered `dataforseo_onpage`.

**Not saved:** the connector currently running. DataForSEO bills on task submission, not on
poll completion, so a `dataforseo_onpage` crawl already submitted is already paid for. The UI
must not imply otherwise — see §3.5.

### 3.3 Why a new status, not `error`

`RefreshStatus` gains `CANCELLED = "cancelled"`. Reusing `error` would be wrong twice over:
Settings → Connections renders errors as live problems needing attention, and
`scheduling.FAILED_RUN_BACKOFF` holds a module off for 6 hours after a failed run — so
cancelling a run you meant to restart would lock you out of restarting it.

A cancelled run must also **not** count as a run for cadence purposes. `last_run_at` is called
with an explicit `statuses` list, so `cancelled` simply never appears in those lists.

### 3.4 The in-flight connector's `SyncLog` row

`BaseConnector.sync` sets its `SyncLog` row to `running` on the way in and rewrites it on the
way out. Killing the process between those two leaves the row stuck at `running` forever —
this is a known, already-solved failure mode (`reap_stale_connector_rows`, added after three
`premierstaff.com` audit runs were killed by server restarts on 2026-07-24).

Reuse that machinery, with a **different message**. The existing text blames a server restart;
a cancelled run must say it was cancelled. Reporting a deliberate user action as an
infrastructure failure is how the next person loses an hour.

### 3.5 Cross-platform kill

The child is spawned detached — `start_new_session` on POSIX, `CREATE_NEW_PROCESS_GROUP |
DETACHED_PROCESS` on Windows (dev). Killing needs both paths.

**A trap already documented in this codebase:** `scheduling._process_alive` carries an explicit
warning that `os.kill(pid, 0)` must never run on Windows, because CPython maps every signal
other than `CTRL_C_EVENT`/`CTRL_BREAK_EVENT` onto `TerminateProcess` — the liveness *check*
kills the process it is asking about. For cancellation that mapping is what we want, but the
asymmetry must be respected: **check** liveness through the existing `_process_alive` helper,
**kill** through a new, separately-tested helper. Do not merge them.

**pid reuse** is the other hazard: a recycled pid means killing an unrelated process. Mitigated
by making the status transition the gate — a conditional
`filter(pk=…, status=RUNNING).update(status=CANCELLED)` returns the number of rows changed, and
the kill fires **only** when that is exactly 1. A second Stop click, or a run that finished
microseconds earlier, changes 0 rows and kills nothing.

### 3.6 API

```
POST /api/projects/<slug>/sync/cancel   ->  {"cancelled": true,  "task_id": 42}
                                        ->  {"cancelled": false, "reason": "no run in flight"}
```

`200` in both cases. "Nothing was running" is a normal outcome of a race (the run finished
while you were reaching for the button), not a client error.

Must carry `@method_decorator(login_not_required, name="dispatch")` like every other API view —
`LoginRequiredMiddleware` runs before DRF and would otherwise 302 the token request to the
login page.

**Permissions:** any authenticated user who can start a sync can stop one. No role gate. With
2–3 internal users, a run started by a colleague is far more likely to be one you are waiting
on than one you must not touch, and the cost of not being able to stop a wrong run exceeds the
cost of stopping someone else's. `RefreshRun.triggered_by` already records who started it, so
the cancelled-run message can name them.

### 3.7 SPA

* **Stop** control in the sync banner (`index.html`, the `{{ syncing }}` block), beside the
  existing "Hide details" toggle.
* `_pollSyncTask` already treats any non-`running` status as `done`. It needs a cancelled
  branch: notify *"Sync cancelled — N connectors did not run"* rather than the success text,
  and **do not** set `freshness: 'Just now'` — a cancelled run did not refresh the page.
* The existing done-path refetch is kept: partial data was written and the page should show it.
* `startSync`'s concurrency guard clears itself, so re-clicking Fetch immediately works.

---

## 4. Feature B — Freshness guard on manual refreshes

### 4.1 The setting

One control in **Settings → Automation**, above the existing per-module cadence rows:

> **Skip connectors synced within:** `Off · 1h · 6h · 12h · 24h · 48h · 7 days`
> *Applies to manual refresh buttons only. Scheduled syncs use the cadences below.*

Stored as `skipFreshWithin` in the settings blob (`DEFAULT_SETTINGS_BLOB`), default `"24h"`,
persisted through `apply_settings_update`'s existing pass-through key list.

### 4.2 Manual-only, and why

Applying this to scheduled runs would put two systems in charge of the same decision. A 24h
skip window stacked on top of a 12h `ads` cadence means Ads silently never runs again — a bug
that would take a long time to notice, because the symptom is *nothing happening*.

The cadences **are** the scheduler's freshness logic. This window is the manual path's
equivalent, and the two never overlap.

The *check* still reads `SyncLog` regardless of origin: if the scheduler refreshed Backlinks an
hour ago, a manual click sees that and skips. Only the *enforcement* is manual-only.

### 4.3 Skip rule, per connector

`SyncLog` is `UNIQUE(connector, site_url)` and holds the last result for that pair — so
freshness is naturally per connector, not per scope.

| `SyncLog` state | Skip? | Why |
|---|---|---|
| `success`, within the window | **yes** | Nothing has changed; the call would be waste |
| `success`, older than the window | no | |
| `error` | **never** | A failure must be retryable immediately — that is the whole point of clicking Refresh after fixing a credential |
| no row / `never` | **never** | Never synced is not fresh |
| window = `Off` | **never** | Today's behaviour, unchanged |

### 4.4 The three outcomes

1. **Some fresh, some stale** — the run starts, skipping the fresh ones. Skipped connectors
   appear in the live checklist greyed, detail *"Skipped — synced 4h ago"*. `total_count` still
   counts them, so progress reaches 100% honestly and the user can see what was skipped.
2. **All fresh** — **no `RefreshRun` row is created at all.** The POST returns
   `{"fresh": true, "connectors": [...], "last_synced": "...", "scope": "backlinks"}` with `200`.
   The SPA shows a dialog: *"Everything in Backlinks synced 40 minutes ago. Refresh anyway?"*
   → **Refresh anyway** re-POSTs with `force: true`.
3. **`force: true`** — every window is ignored; the run is created with an empty skip list.

Outcome 2 is where options A and B from the discussion meet: the dialog appears **only** when
skipping would leave nothing to do, so it is informative rather than a click-through tax.

### 4.4.1 What counts as "manual"

Every path that reaches `start_sync_run` from a user action, which is all three of:

* the per-page **Fetch …** button and the card-level buttons (`audit`, `domain_checks`, …);
* **Refresh all** (`scope='all'`) — it is a manual run like any other, and it is the most
  expensive one, so exempting it would defeat the feature;
* **Sync now** on each Settings → Automation row.

The one caller that is *not* subject to it is `run_scheduled_syncs` (§4.2). The initial sync
auto-started by `POST /api/projects` is technically manual but never affected in practice: a
brand-new site has no `SyncLog` rows, so nothing is fresh.

### 4.5 The skip list is decided once and stored

`RefreshRun` gains `skipped_connectors` (JSON, default `[]`), written at creation time by
`start_sync_run`. The sync process **reads** it; it does not recompute freshness.

Three reasons:

* `force` is baked in at creation — no second flag to thread through to another process.
* The row becomes an honest record of what the run decided, which is what
  `_step_details` renders and what an operator reads afterwards.
* One implementation of the rule. Computing it in both `start_sync_run` and `sync_page` is how
  two copies drift apart.

The ~1 second between the POST and the process starting is not a correctness concern at a 1-hour
minimum window.

### 4.6 Progress checklist

`_step_details` currently infers "skipped" from *counted as finished but no `SyncLog` row
touched since `run.started_at`* — which today means exactly one thing: missing credentials.
With an explicit skip list there are two distinct skips, and they must not be conflated:

| State | Detail |
|---|---|
| `skipped` (credentials) | `Skipped — credentials not configured` |
| `skipped` (fresh) | `Skipped — synced 4h ago` |

A connector skipped as fresh is a *success* (we already have the data). A connector skipped for
missing credentials is a *problem*. Rendering both as one grey "skipped" is how a broken
integration stays invisible for weeks — the exact failure `_step_details`' existing docstring
warns about.

---

## 5. Changes by file

| File | Change |
|---|---|
| `apps/sync/models.py` | `RefreshStatus.CANCELLED`; `RefreshRun.skipped_connectors` (JSON) |
| `apps/sync/migrations/` | one migration for both |
| `apps/dashboard/services/sync_api_service.py` | `cancel_sync_run()`; freshness computation in `start_sync_run`; `force`; skip-aware `_step_details` |
| `apps/sync/scheduling.py` | kill helper (separate from `_process_alive`); cancelled-run `SyncLog` message; exclude `cancelled` from cadence anchors |
| `pipeline/services/sync_engine.py` | honour `skipped_connectors`; check for cancellation between connectors |
| `apps/api/views.py`, `apps/api/urls.py` | `POST /api/projects/<slug>/sync/cancel` |
| `apps/dashboard/services/settings_service.py` | `skipFreshWithin` in `DEFAULT_SETTINGS_BLOB` + update path |
| `static/spa/src/index.html` | Stop control in the sync banner |
| `static/spa/src/js/app.js` | `cancelSync()`; cancelled + `fresh` response handling; the confirm dialog |
| `static/spa/src/pages/settings.html`, `js/pages/settings.js` | the window dropdown |
| `.claude/api-reference.md`, `.claude/features.md` | same change as the behaviour |

---

## 6. Testing

**Cancellation**

* Cancelling a running run sets `cancelled`, and the kill fires exactly once.
* Cancelling a run that already finished changes nothing and **kills no process** (the pid-reuse
  guard — assert the kill helper is not called).
* Two concurrent cancels: one wins, the second kills nothing.
* `sync_page` stops before the next connector when the row flips to `cancelled` mid-run, and
  keeps the records written so far.
* Windows: the liveness check never calls a killing primitive (mirroring the existing
  `test_windows_never_calls_os_kill`), and the kill helper does.
* A cancelled run does not anchor a cadence — the module is still due.

**Freshness**

* A connector that succeeded inside the window is skipped; one that errored inside the window
  is **not**.
* All-fresh returns `fresh: true` and creates **no** `RefreshRun`.
* `force: true` creates a run with an empty skip list even when everything is fresh.
* `Off` reproduces today's behaviour exactly.
* Scheduled runs are unaffected by the window (a `run_scheduled_syncs` tick with everything
  "fresh" still runs its due module).
* `_step_details` reports the two skip kinds distinctly.
* Progress reaches 100% when connectors are skipped.
* `scope='all'` is subject to the window like any other manual run.
* A brand-new site (no `SyncLog` rows) never has anything skipped, so the initial sync started
  by `POST /api/projects` runs in full.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| **pid reuse** — killing an unrelated process | Kill only when the conditional status update changed exactly 1 row (§3.5) |
| **Windows signal semantics** — a "check" that kills | Separate check/kill helpers, each with its own test; the existing `_process_alive` is not touched |
| **Freshness hides a real need to refresh** | Errors are never skipped; the skip reason is always visible in the checklist; `force` always available |
| **Two freshness systems disagree** | The window is manual-only; cadences remain the scheduler's sole authority (§4.2) |
| **A cancelled run blocks the next one** | `cancelled` is terminal, so `start_sync_run`'s "one run per site" guard releases immediately; `FAILED_RUN_BACKOFF` does not apply |
