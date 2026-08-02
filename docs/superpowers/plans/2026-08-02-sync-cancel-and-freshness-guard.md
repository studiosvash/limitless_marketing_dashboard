# Sync Cancellation + Manual-Refresh Freshness Guard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user stop a running sync from the UI, and stop manual refreshes from re-spending metered API budget on connectors that already synced recently.

**Architecture:** Cancellation is two-halved on purpose — a conditional DB status flip (`RefreshRun.status = 'cancelled'`) that the connector loop re-reads between connectors, plus an OS kill of the `run_sync` process by its stored pid. The DB half is the reliable one; the kill is the fast one. The freshness guard is computed **once**, in `start_sync_run`, and stored on the run row as `skipped_connectors`, so the separate sync process reads a decision rather than recomputing one.

**Tech Stack:** Django 6 + DRF, SQLite (`django_internal.db` for ORM state), SQLAlchemy for analytics, vanilla-JS SPA with `#include`-resolved HTML templates (no build step).

**Spec:** `docs/superpowers/specs/2026-08-02-sync-cancel-and-freshness-guard-design.md`

## Global Constraints

- Every API view needs `@method_decorator(login_not_required, name="dispatch")` — `LoginRequiredMiddleware` runs before DRF and would otherwise 302 token requests to the login page.
- Never fabricate data to fill a shape — return empty, `null`, or an explicit state.
- Analytics writes go through `pipeline/db/writer.py`; this plan touches only Django ORM state (`django_internal.db`).
- `os.kill(pid, 0)` must **never** run on Windows — CPython maps every signal except `CTRL_C_EVENT`/`CTRL_BREAK_EVENT` onto `TerminateProcess`, so the "check" kills the process. The existing `scheduling._process_alive` is **not** to be modified.
- The SPA is served from `static/spa/src/` with includes resolved per request (`apps/dashboard/spa_views.py`). There is no build step — edit `src/` directly.
- SPA confirmations use `window.confirm` (existing pattern: `app.js:1421`, `1496`, `1590`).
- Update the relevant `.claude/` reference in the same change as the behaviour it describes.
- Run tests with `python manage.py test <label>`. Full suite baseline is currently **570 passing**.
- Commit after every task.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `apps/sync/models.py` | Operational sync state | `RefreshStatus.CANCELLED`; `RefreshRun.skipped_connectors` |
| `apps/sync/migrations/00XX_*.py` | Schema | one migration, both changes |
| `apps/sync/scheduling.py` | Process liveness, reaping, cadence | **new** kill helper; scoped/parameterised `reconcile_orphaned_sync_logs` |
| `apps/dashboard/services/sync_api_service.py` | JSON wrapper over the sync engine | `cancel_sync_run`; freshness computation; `force`; skip-aware `_step_details` |
| `pipeline/services/sync_engine.py` | Connector orchestration | cancellation checks; honour `skipped_connectors` |
| `apps/api/views.py` / `urls.py` | HTTP surface | `POST /api/projects/<slug>/sync/cancel` |
| `apps/sync/management/commands/run_scheduled_syncs.py` | The scheduler tick | pass `manual=False` — the window must never apply here |
| `apps/dashboard/services/settings_service.py` | Settings blob | `manualSync.skip_fresh_within` |
| `static/spa/src/index.html` | Sync banner | Stop control |
| `static/spa/src/js/app.js` | SPA controller | `cancelSync`; cancelled + `fresh` handling; `force` |
| `static/spa/src/pages/settings.html` / `js/pages/settings.js` | Settings → Automation | the window dropdown |

**Test files:**
- `apps/sync/test_cancel.py` (new) — kill helper, `cancel_sync_run`, reconcile scoping
- `apps/api/tests/test_sync_engine.py` (existing) — engine cancellation + skip honouring
- `apps/dashboard/services/tests/test_sync_freshness.py` (new) — freshness rule, `start_sync_run`, `_step_details`

---

## Task 1: Model — `cancelled` status and `skipped_connectors`

**Files:**
- Modify: `apps/sync/models.py:19-23` (`RefreshStatus`), `apps/sync/models.py:47-75` (`RefreshRun`)
- Create: `apps/sync/migrations/` (generated)
- Test: `apps/sync/test_cancel.py` (new)

**Interfaces:**
- Consumes: nothing
- Produces: `RefreshStatus.CANCELLED == "cancelled"`; `RefreshRun.skipped_connectors: list[str]` (JSONField, `default=list`)

- [ ] **Step 1: Write the failing test**

Create `apps/sync/test_cancel.py`:

```python
"""Cancellation and the fields it needs.

A cancelled run is deliberately NOT an error. Two things in this codebase treat `error`
as meaningful: Settings -> Connections renders it as a live problem, and
scheduling.FAILED_RUN_BACKOFF holds a module off for 6 hours after a failed run -- so
recording a cancel as an error would lock you out of the restart you cancelled in order
to make.
"""
from django.test import TestCase

from apps.sync.models import RefreshRun, RefreshStatus

SITE_URL = "sc-domain:fusehealth.com"


class RefreshRunCancelFieldsTests(TestCase):
    def test_a_run_can_be_marked_cancelled(self):
        run = RefreshRun.objects.create(site_url=SITE_URL, scope="audit",
                                        status=RefreshStatus.RUNNING)
        run.status = RefreshStatus.CANCELLED
        run.save(update_fields=["status"])

        run.refresh_from_db()
        self.assertEqual(run.status, "cancelled")
        self.assertNotEqual(run.status, RefreshStatus.ERROR)

    def test_skipped_connectors_defaults_to_an_empty_list(self):
        run = RefreshRun.objects.create(site_url=SITE_URL, scope="audit",
                                        status=RefreshStatus.RUNNING)
        run.refresh_from_db()
        self.assertEqual(run.skipped_connectors, [])

    def test_skipped_connectors_round_trips_a_list(self):
        run = RefreshRun.objects.create(
            site_url=SITE_URL, scope="positioning", status=RefreshStatus.RUNNING,
            skipped_connectors=["gsc_keywords", "dataforseo_keywords"],
        )
        run.refresh_from_db()
        self.assertEqual(run.skipped_connectors, ["gsc_keywords", "dataforseo_keywords"])

    def test_a_cancelled_run_does_not_anchor_a_cadence(self):
        """A run that was stopped refreshed nothing, so it must not push the next scheduled
        sync out. This holds today only because every `last_run_at` caller passes an explicit
        status list -- [SUCCESS] or [SUCCESS, ERROR, RUNNING] -- and CANCELLED is in neither.
        That is a silent invariant one careless edit could break, so it is pinned here."""
        from apps.sync import scheduling

        RefreshRun.objects.create(site_url=SITE_URL, scope="backlinks",
                                  status=RefreshStatus.CANCELLED)

        self.assertIsNone(
            scheduling.last_run_at(SITE_URL, "backlinks", [RefreshStatus.SUCCESS])
        )
        self.assertIsNone(
            scheduling.last_run_at(
                SITE_URL, "backlinks",
                [RefreshStatus.SUCCESS, RefreshStatus.ERROR, RefreshStatus.RUNNING],
            )
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.sync.test_cancel -v 1`
Expected: FAIL — `AttributeError: type object 'RefreshStatus' has no attribute 'CANCELLED'`

- [ ] **Step 3: Add the status choice**

In `apps/sync/models.py`, replace the `RefreshStatus` class:

```python
class RefreshStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    ERROR = "error", "Error"
    # A run stopped by the user from the sync banner. Deliberately NOT `error`:
    # Settings -> Connections renders errors as live problems needing attention, and
    # scheduling.FAILED_RUN_BACKOFF holds a module off for 6 hours after a failed run --
    # so filing a cancel under `error` would block the restart the user cancelled in
    # order to make. It is also excluded from every cadence anchor, because a run that
    # was stopped did not refresh anything.
    CANCELLED = "cancelled", "Cancelled"
```

- [ ] **Step 4: Add the field**

In `apps/sync/models.py`, add to `RefreshRun` immediately after the `pid` field:

```python
    # Connectors this run will NOT execute because they synced successfully inside the
    # manual-refresh freshness window (see sync_api_service.fresh_connectors).
    #
    # Decided ONCE, by start_sync_run, and stored -- not recomputed inside the sync
    # process. Three reasons: `force` is then baked in at creation rather than being a
    # second flag to thread across a process boundary; the row becomes an honest record
    # of what this run decided, which is what the step checklist renders; and the rule
    # has exactly one implementation instead of two that can drift.
    #
    # Empty for every scheduled run and for any run started with force=True.
    skipped_connectors = models.JSONField(default=list, blank=True)
```

- [ ] **Step 5: Generate the migration**

Run: `python manage.py makemigrations sync`
Expected: a new migration adding `skipped_connectors` and altering `status` choices.

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test apps.sync.test_cancel -v 1`
Expected: PASS (4 tests)

- [ ] **Step 7: Commit**

```bash
git add apps/sync/models.py apps/sync/migrations/ apps/sync/test_cancel.py
git commit -m "feat(sync): add cancelled status and skipped_connectors to RefreshRun"
```

---

## Task 2: Cross-platform kill helper

**Files:**
- Modify: `apps/sync/scheduling.py` (add after `_process_alive`, ~line 226)
- Test: `apps/sync/test_cancel.py`

**Interfaces:**
- Consumes: nothing
- Produces: `scheduling.terminate_sync_process(pid: int | None) -> bool` — True when we believe the process is now gone. `scheduling._windows_terminate(pid: int) -> bool`.

**Why a separate helper:** `_process_alive` exists to *ask* whether a pid is alive and is called from every `GET /api/sync/active`. Merging a kill into it would be catastrophic. Keep them apart and test the separation.

- [ ] **Step 1: Write the failing test**

Append to `apps/sync/test_cancel.py`:

```python
import signal
from unittest import mock

from apps.sync import scheduling


class TerminateSyncProcessTests(TestCase):
    def test_no_pid_kills_nothing(self):
        """A run created before the pid field existed, or caught mid-spawn, has no pid.
        There is nothing safe to kill, and killing pid 0 or -1 is catastrophic."""
        with mock.patch.object(scheduling.os, "kill") as killer:
            self.assertFalse(scheduling.terminate_sync_process(None))
            self.assertFalse(scheduling.terminate_sync_process(0))
            self.assertFalse(scheduling.terminate_sync_process(-1))
        killer.assert_not_called()

    def test_posix_sends_sigterm(self):
        with mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill") as killer:
            self.assertTrue(scheduling.terminate_sync_process(4321))
        killer.assert_called_once_with(4321, signal.SIGTERM)

    def test_posix_already_gone_counts_as_terminated(self):
        with mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill", side_effect=ProcessLookupError):
            self.assertTrue(scheduling.terminate_sync_process(4321))

    def test_posix_permission_error_reports_failure(self):
        """We could not kill it, so we must not claim we did -- the DB flag is what
        actually stops the run in that case."""
        with mock.patch.object(scheduling.sys, "platform", "linux"), \
             mock.patch.object(scheduling.os, "kill", side_effect=PermissionError):
            self.assertFalse(scheduling.terminate_sync_process(4321))

    def test_windows_never_calls_os_kill(self):
        """The mirror of test_windows_never_calls_os_kill for _process_alive, from the
        other direction: killing on Windows must go through TerminateProcess explicitly,
        not through os.kill's accidental mapping onto it."""
        with mock.patch.object(scheduling.sys, "platform", "win32"), \
             mock.patch.object(scheduling, "_windows_terminate", return_value=True) as win, \
             mock.patch.object(scheduling.os, "kill") as killer:
            self.assertTrue(scheduling.terminate_sync_process(4321))
        win.assert_called_once_with(4321)
        killer.assert_not_called()

    def test_liveness_check_is_not_the_kill_helper(self):
        """_process_alive must never terminate anything. It runs on every
        GET /api/sync/active, i.e. every couple of seconds during a sync."""
        with mock.patch.object(scheduling.sys, "platform", "win32"), \
             mock.patch.object(scheduling, "_windows_terminate") as win, \
             mock.patch.object(scheduling, "_windows_process_alive", return_value=True):
            scheduling._process_alive(4321)
        win.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.sync.test_cancel.TerminateSyncProcessTests -v 1`
Expected: FAIL — `AttributeError: module 'apps.sync.scheduling' has no attribute 'terminate_sync_process'`

- [ ] **Step 3: Implement the helper**

In `apps/sync/scheduling.py`, add `import signal` to the imports, then insert immediately after `_process_alive` ends (before `def reap_orphaned_runs`):

```python
def _windows_terminate(pid: int) -> bool:
    """Kill `pid` through the Win32 API. Returns True if it is now gone.

    Deliberately explicit rather than relying on `os.kill`'s accidental mapping onto
    TerminateProcess. `_process_alive` documents at length why that mapping is a trap; a
    kill path that depends on the same trap would be one refactor away from becoming a
    liveness check again.
    """
    import ctypes

    PROCESS_TERMINATE = 0x0001
    ERROR_INVALID_PARAMETER = 87

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if not handle:
        # No such pid means the job is already done; anything else means we could not.
        return ctypes.get_last_error() == ERROR_INVALID_PARAMETER
    try:
        return bool(kernel32.TerminateProcess(handle, 1))
    finally:
        kernel32.CloseHandle(handle)


def terminate_sync_process(pid: int | None) -> bool:
    """Stop the `manage.py run_sync` process behind a cancelled run.

    Returns True when we believe the process is gone (including "it had already exited").
    False means we could not kill it -- which is not fatal: cancellation sets
    RefreshRun.status='cancelled' FIRST, and sync_all/sync_page re-read that between
    connectors, so an unkillable process still stops before the next connector. The kill
    is what makes Stop feel immediate rather than "immediate once this 600-second
    DataForSEO poll finishes".

    Callers must only reach here after a conditional status update changed exactly one
    row -- that is the pid-reuse guard. Without it, a recycled pid means killing an
    unrelated process.

    **This is NOT a liveness check.** See `_process_alive` for why the two must stay
    apart on Windows.
    """
    if not pid or pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            return _windows_terminate(pid)
        except Exception:
            logger.warning("[sync] Windows terminate failed for pid %s", pid, exc_info=True)
            return False

    try:
        # SIGTERM, not SIGKILL: run_sync holds no lock and buffers no analytics writes, so
        # the default terminate is enough and leaves a clean exit in the per-run log file.
        # The child is its own session (start_new_session=True) but spawns no children of
        # its own -- connectors are in-process HTTP calls -- so the bare pid is the whole
        # process tree.
        os.kill(pid, signal.SIGTERM)
        return True
    except ProcessLookupError:
        return True          # already gone; the outcome we wanted
    except Exception:
        logger.warning("[sync] could not terminate pid %s", pid, exc_info=True)
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.sync.test_cancel -v 1`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/sync/scheduling.py apps/sync/test_cancel.py
git commit -m "feat(sync): add terminate_sync_process, kept separate from the liveness check"
```

---

## Task 3: Scope and parameterise the orphaned-`SyncLog` reconciler

**Files:**
- Modify: `apps/sync/scheduling.py:302-345` (`reconcile_orphaned_sync_logs`), plus a new message constant near `ORPHANED_CONNECTOR_MESSAGE` (~line 126)
- Test: `apps/sync/test_cancel.py`

**Interfaces:**
- Consumes: nothing
- Produces: `reconcile_orphaned_sync_logs(dry_run: bool = False, site_url: str | None = None, message: str = ORPHANED_CONNECTOR_MESSAGE) -> list[SyncLog]`; `scheduling.CANCELLED_CONNECTOR_MESSAGE: str`

**Why:** killing the process leaves the in-flight connector's `SyncLog` row at `running` forever. That is already solved — but the existing message blames a server restart, and the existing function clears **every** site. Cancelling site A must not stamp site B's genuinely-orphaned rows with "you cancelled this".

- [ ] **Step 1: Write the failing test**

Append to `apps/sync/test_cancel.py`:

```python
from apps.sync.models import SyncLog, SyncStatus

OTHER_SITE = "sc-domain:premierstaff.com"


class ReconcileScopingTests(TestCase):
    def _running_log(self, site, connector):
        return SyncLog.objects.create(connector=connector, site_url=site,
                                      status=SyncStatus.RUNNING, records_written=42)

    def test_site_url_scopes_the_reconcile(self):
        """Cancelling one site must not relabel another site's orphaned rows."""
        mine = self._running_log(SITE_URL, "pagespeed")
        theirs = self._running_log(OTHER_SITE, "pagespeed")

        scheduling.reconcile_orphaned_sync_logs(
            site_url=SITE_URL, message=scheduling.CANCELLED_CONNECTOR_MESSAGE
        )

        mine.refresh_from_db()
        theirs.refresh_from_db()
        self.assertEqual(mine.status, SyncStatus.ERROR)
        self.assertEqual(mine.error_message, scheduling.CANCELLED_CONNECTOR_MESSAGE)
        self.assertEqual(theirs.status, SyncStatus.RUNNING, "other site was touched")

    def test_unscoped_call_still_clears_every_site(self):
        """The scheduler's own periodic call must keep its existing whole-fleet behaviour."""
        self._running_log(SITE_URL, "pagespeed")
        self._running_log(OTHER_SITE, "url_inspection")

        scheduling.reconcile_orphaned_sync_logs()

        self.assertEqual(
            SyncLog.objects.filter(status=SyncStatus.RUNNING).count(), 0
        )

    def test_records_written_is_never_erased(self):
        """What a stopped connector managed to write is a real measurement."""
        log = self._running_log(SITE_URL, "pagespeed")
        scheduling.reconcile_orphaned_sync_logs(site_url=SITE_URL)
        log.refresh_from_db()
        self.assertEqual(log.records_written, 42)

    def test_the_cancel_message_does_not_blame_a_server_restart(self):
        self.assertNotIn("restart", scheduling.CANCELLED_CONNECTOR_MESSAGE.lower())
        self.assertIn("cancel", scheduling.CANCELLED_CONNECTOR_MESSAGE.lower())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.sync.test_cancel.ReconcileScopingTests -v 1`
Expected: FAIL — `AttributeError: module 'apps.sync.scheduling' has no attribute 'CANCELLED_CONNECTOR_MESSAGE'`

- [ ] **Step 3: Add the message constant**

In `apps/sync/scheduling.py`, immediately after the `ORPHANED_CONNECTOR_MESSAGE` assignment (~line 130):

```python
# The same situation as ORPHANED_CONNECTOR_MESSAGE -- a connector's SyncLog row left at
# `running` because its process died mid-connector -- but with a KNOWN, deliberate cause.
# Reporting a user's own Stop click as an infrastructure failure is how the next person
# spends an hour looking for a server problem that never happened.
CANCELLED_CONNECTOR_MESSAGE = (
    "This connector was running when the refresh was cancelled, so it never reported a "
    "result. Any rows it had already written were kept. Run the refresh again to complete it."
)
```

- [ ] **Step 4: Parameterise the reconciler**

In `apps/sync/scheduling.py`, change the signature and the two lines that use the new parameters:

```python
def reconcile_orphaned_sync_logs(
    dry_run: bool = False,
    site_url: str | None = None,
    message: str = ORPHANED_CONNECTOR_MESSAGE,
) -> list[SyncLog]:
```

Add to the existing docstring, before the closing `"""`:

```
    `site_url` scopes the sweep to one project, and `message` says why. Both exist for
    cancellation: cancelling site A must not relabel site B's genuinely-orphaned rows
    with "you cancelled this". Called with neither, the behaviour is unchanged -- which
    is what the scheduler's own periodic call relies on.
```

Then replace the query and the update:

```python
    live_sites = set(
        RefreshRun.objects.filter(status=RefreshStatus.RUNNING).values_list("site_url", flat=True)
    )
    candidates = SyncLog.objects.filter(status=SyncStatus.RUNNING).exclude(site_url__in=live_sites)
    if site_url is not None:
        candidates = candidates.filter(site_url=site_url)
    orphaned = list(candidates)
    if not orphaned or dry_run:
        return orphaned

    # Filtered on status='running' again so a connector that finishes between the SELECT and the
    # UPDATE keeps its own result -- the same concurrency rule reap_orphaned_runs() follows.
    SyncLog.objects.filter(
        pk__in=[log.pk for log in orphaned], status=SyncStatus.RUNNING
    ).update(status=SyncStatus.ERROR, error_message=message)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.sync.test_cancel apps.sync.test_scheduling -v 1`
Expected: PASS — new tests pass and the existing scheduling suite is unaffected.

- [ ] **Step 6: Commit**

```bash
git add apps/sync/scheduling.py apps/sync/test_cancel.py
git commit -m "feat(sync): let the SyncLog reconciler be scoped to one site with its own message"
```

---

## Task 4: `cancel_sync_run()`

**Files:**
- Modify: `apps/dashboard/services/sync_api_service.py` (add after `start_sync_run`, ~line 177)
- Test: `apps/sync/test_cancel.py`

**Interfaces:**
- Consumes: `scheduling.terminate_sync_process`, `scheduling.reconcile_orphaned_sync_logs`, `scheduling.CANCELLED_CONNECTOR_MESSAGE`, `RefreshStatus.CANCELLED`
- Produces: `cancel_sync_run(site_url: str, user=None) -> dict` — `{"cancelled": True, "task_id": int, "killed": bool}` or `{"cancelled": False, "reason": str}`

- [ ] **Step 1: Write the failing test**

Append to `apps/sync/test_cancel.py`:

```python
from apps.dashboard.services.sync_api_service import cancel_sync_run


class CancelSyncRunTests(TestCase):
    def _running_run(self, pid=4321):
        return RefreshRun.objects.create(site_url=SITE_URL, scope="audit",
                                         status=RefreshStatus.RUNNING, pid=pid,
                                         total_count=5, completed_count=2)

    def test_cancelling_marks_the_run_and_kills_the_process(self):
        run = self._running_run()
        with mock.patch.object(scheduling, "terminate_sync_process", return_value=True) as kill:
            result = cancel_sync_run(SITE_URL)

        self.assertTrue(result["cancelled"])
        self.assertEqual(result["task_id"], run.pk)
        kill.assert_called_once_with(4321)
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.CANCELLED)
        self.assertIsNotNone(run.finished_at)
        self.assertIsNone(run.current_connector)

    def test_records_written_so_far_are_kept(self):
        run = self._running_run()
        RefreshRun.objects.filter(pk=run.pk).update(records_written=154)
        with mock.patch.object(scheduling, "terminate_sync_process", return_value=True):
            cancel_sync_run(SITE_URL)
        run.refresh_from_db()
        self.assertEqual(run.records_written, 154)
        self.assertEqual(run.completed_count, 2, "progress so far must not be rewritten")

    def test_nothing_running_is_not_an_error_and_kills_nothing(self):
        with mock.patch.object(scheduling, "terminate_sync_process") as kill:
            result = cancel_sync_run(SITE_URL)
        self.assertFalse(result["cancelled"])
        kill.assert_not_called()

    def test_a_finished_run_is_never_killed(self):
        """THE pid-reuse guard. If the run resolved between our SELECT and our UPDATE, the
        pid may now belong to an unrelated process and must not be touched."""
        run = self._running_run()

        def finish_it(*_args, **_kwargs):
            RefreshRun.objects.filter(pk=run.pk).update(status=RefreshStatus.SUCCESS)
            return 0

        with mock.patch.object(scheduling, "terminate_sync_process") as kill, \
             mock.patch("apps.dashboard.services.sync_api_service._claim_for_cancel",
                        side_effect=finish_it):
            result = cancel_sync_run(SITE_URL)

        self.assertFalse(result["cancelled"])
        kill.assert_not_called()

    def test_second_cancel_kills_nothing(self):
        self._running_run()
        with mock.patch.object(scheduling, "terminate_sync_process", return_value=True) as kill:
            first = cancel_sync_run(SITE_URL)
            second = cancel_sync_run(SITE_URL)

        self.assertTrue(first["cancelled"])
        self.assertFalse(second["cancelled"])
        self.assertEqual(kill.call_count, 1)

    def test_the_in_flight_connector_row_is_resolved_with_the_cancel_message(self):
        self._running_run()
        log = SyncLog.objects.create(connector="dataforseo_onpage", site_url=SITE_URL,
                                     status=SyncStatus.RUNNING, records_written=7)
        with mock.patch.object(scheduling, "terminate_sync_process", return_value=True):
            cancel_sync_run(SITE_URL)

        log.refresh_from_db()
        self.assertEqual(log.status, SyncStatus.ERROR)
        self.assertEqual(log.error_message, scheduling.CANCELLED_CONNECTOR_MESSAGE)
        self.assertEqual(log.records_written, 7)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.sync.test_cancel.CancelSyncRunTests -v 1`
Expected: FAIL — `ImportError: cannot import name 'cancel_sync_run'`

- [ ] **Step 3: Implement**

In `apps/dashboard/services/sync_api_service.py`, add after `start_sync_run` ends:

```python
def _claim_for_cancel(run_pk: int, message: str) -> int:
    """Flip exactly this run from `running` to `cancelled`. Returns rows changed (0 or 1).

    Split out as its own function because it is THE pid-reuse guard and the tests need to
    drive the race: the caller may kill a process only when this returned 1. A run that
    resolved between the SELECT and this UPDATE returns 0, and its pid may by then belong
    to an unrelated process.
    """
    return (
        RefreshRun.objects
        .filter(pk=run_pk, status=RefreshStatus.RUNNING)
        .update(
            status=RefreshStatus.CANCELLED,
            current_connector=None,
            finished_at=timezone.now(),
            error_message=message,
        )
    )


def cancel_sync_run(site_url: str, user=None) -> dict:
    """Stop the refresh in flight for this site.

    Two halves, in this order and both required:

      1. **Mark the row `cancelled`.** The reliable half. sync_all/sync_page re-read the
         status between connectors, so the run stops before the next connector even if
         the kill below fails outright.
      2. **Kill the run_sync process.** The fast half, and the only reason Stop feels
         immediate: without it a cancel issued 40 seconds into `dataforseo_onpage`'s
         600-second poll would appear to do nothing for ten minutes.

    Records already written are kept -- a run stopped at step 2 of 5 keeps steps 1 and 2
    in full. What is saved is every connector that had not started yet. The connector
    that WAS running may already be billed (DataForSEO meters on task submission, not on
    poll completion), and nothing here pretends otherwise.

    "Nothing was running" is a normal outcome, not an error: the run may have finished
    while the user was reaching for the button.
    """
    from apps.sync import scheduling

    run = (RefreshRun.objects
           .filter(site_url=site_url, status=RefreshStatus.RUNNING)
           .order_by("-started_at").first())
    if run is None:
        return {"cancelled": False, "reason": "no refresh is running for this site"}

    who = None
    if user is not None and getattr(user, "is_authenticated", False):
        who = user.get_username()
    message = f"Cancelled by {who}." if who else "Cancelled."

    if _claim_for_cancel(run.pk, message) != 1:
        # Someone else cancelled it, or it finished on its own, between the SELECT above
        # and this UPDATE. Either way this call does not own the pid and must not kill.
        logger.info("[sync] run #%s resolved before the cancel landed — killing nothing", run.pk)
        return {"cancelled": False, "reason": "that refresh had already finished"}

    killed = scheduling.terminate_sync_process(run.pid)
    logger.info("[sync] cancelled run #%s (%s@%s) pid=%s killed=%s",
                run.pk, run.scope, site_url, run.pid, killed)

    # The connector that was mid-flight left its SyncLog row at `running`; nothing else
    # will ever rewrite it. Scoped to this site and given the cancel message so another
    # project's genuinely-orphaned rows are not relabelled. Safe to run now because the
    # RefreshRun is no longer `running`, which is the one fact this reconciler tests.
    #
    # A small race remains: if the process writes its row again in the moment between the
    # kill and this call, the row goes back to `running`. That self-heals -- the same
    # reconciler runs on the next reap, which every start_sync_run and sync/active poll
    # triggers.
    try:
        scheduling.reconcile_orphaned_sync_logs(
            site_url=site_url, message=scheduling.CANCELLED_CONNECTOR_MESSAGE
        )
    except Exception:
        logger.warning("[sync] reconciling connector rows after cancel failed", exc_info=True)

    return {"cancelled": True, "task_id": run.pk, "killed": killed}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.sync.test_cancel -v 1`
Expected: PASS (19 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/services/sync_api_service.py apps/sync/test_cancel.py
git commit -m "feat(sync): cancel_sync_run — claim the row, then kill the process"
```

---

## Task 5: The engine stops between connectors

**Files:**
- Modify: `pipeline/services/sync_engine.py` — new helper near `_get_connector`; loop guards in `sync_all` (~line 302) and `sync_page` (~line 430)
- Test: `apps/api/tests/test_sync_engine.py`

**Interfaces:**
- Consumes: `RefreshStatus.CANCELLED`
- Produces: `sync_engine._run_cancelled(run_id: int) -> bool`; both `sync_all` and `sync_page` return `{..., "cancelled": True}` when stopped early

- [ ] **Step 1: Write the failing test**

Append to `apps/api/tests/test_sync_engine.py`, inside `SyncEngineTests`:

```python
    # ------------------------------------------------------------- cancellation

    def test_sync_page_stops_before_the_next_connector_when_cancelled(self):
        """The reliable half of Stop. Even if the kill fails outright, the run must not
        start another connector -- that is what stops the money."""
        run = self._run_row(scope="audit")

        def factory(name):
            conn = FakeConnector(name)
            self.built[name] = conn
            # Cancel lands while the FIRST connector is running.
            if len(self.built) == 1:
                RefreshRun.objects.filter(pk=run.pk).update(status=RefreshStatus.CANCELLED)
            return conn

        p = patch.object(sync_engine, "_get_connector", side_effect=factory)
        p.start()
        self.addCleanup(p.stop)

        summary = sync_page("audit", SITE_URL, run.pk)

        self.assertTrue(summary["cancelled"])
        self.assertEqual(len(self.built), 1, "a second connector ran after cancellation")
        self.assertEqual(summary["records_written"], 5, "work already done must be kept")

    def test_a_cancelled_run_keeps_its_cancelled_status(self):
        """sync_page must not overwrite `cancelled` with success/error on its way out."""
        run = self._run_row(scope="overview")
        RefreshRun.objects.filter(pk=run.pk).update(status=RefreshStatus.CANCELLED)
        self._stub_connectors()

        sync_page("overview", SITE_URL, run.pk)

        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.CANCELLED)

    def test_cancelling_skips_post_sync_processing(self):
        """Rebuilding aggregates and technical issues from a half-finished run would
        publish numbers derived from partial data."""
        run = self._run_row(scope="overview")
        RefreshRun.objects.filter(pk=run.pk).update(status=RefreshStatus.CANCELLED)
        self._stub_connectors()

        with patch.object(sync_engine, "_run_post_sync") as post:
            sync_page("overview", SITE_URL, run.pk)

        post.assert_not_called()

    def test_sync_all_stops_when_cancelled(self):
        run = self._run_row(scope="all")
        RefreshRun.objects.filter(pk=run.pk).update(status=RefreshStatus.CANCELLED)
        self._stub_connectors()

        summary = sync_all(SITE_URL, run.pk)

        self.assertTrue(summary["cancelled"])
        self.assertEqual(self.built, {}, "no connector should have run")
```

Note: `SyncEngineTests.setUp` patches `_run_post_sync` for the whole class, so
`test_cancelling_skips_post_sync_processing` re-patches it locally to assert on it — the
inner patch wins.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.api.tests.test_sync_engine -v 1`
Expected: FAIL — `KeyError: 'cancelled'`

- [ ] **Step 3: Add the helper**

In `pipeline/services/sync_engine.py`, add immediately before `_run_post_sync`:

```python
def _run_cancelled(run_id: int) -> bool:
    """Has this run been stopped from the UI since the last connector finished?

    Checked between connectors, which is the whole cancellation contract on this side:
    the API marks the row `cancelled` and then kills this process, but a kill can fail
    (stale pid, permissions) and a signal can arrive late. This check is what guarantees
    the run stops anyway -- before the next connector, i.e. before the next API spend.

    One cheap indexed query per connector, against a run that takes minutes.
    """
    from apps.sync.models import RefreshRun, RefreshStatus  # type: ignore[import]
    return RefreshRun.objects.filter(pk=run_id, status=RefreshStatus.CANCELLED).exists()
```

- [ ] **Step 4: Guard the `sync_all` loop**

In `sync_all`, replace the first two lines of the `for name in connectors:` body so it begins:

```python
    for name in connectors:
        if _run_cancelled(run_id):
            logger.info(f"[sync_engine] sync_all cancelled — stopping before {name!r} "
                        f"({completed}/{total} done, {total_records} records kept)")
            return {"completed": completed, "total": total,
                    "records_written": total_records, "errors": errors, "cancelled": True}

        logger.info(f"[sync_engine] [{completed + 1}/{total}] Running connector: {name!r}")
        RefreshRun.objects.filter(pk=run_id).update(current_connector=name)
```

Returning early leaves the row at `cancelled` (the final-status update below is never
reached) and skips `_run_post_sync`.

- [ ] **Step 5: Guard the `sync_page` loop**

In `sync_page`, apply the identical change, with `sync_all` → `sync_page` in the log line:

```python
    for name in connector_names:
        if _run_cancelled(run_id):
            logger.info(f"[sync_engine] sync_page cancelled — stopping before {name!r} "
                        f"({completed}/{total} done, {total_records} records kept)")
            return {"completed": completed, "total": total,
                    "records_written": total_records, "errors": errors, "cancelled": True}

        logger.info(f"[sync_engine] [{completed + 1}/{total}] Running connector: {name!r}")
        RefreshRun.objects.filter(pk=run_id).update(current_connector=name)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_sync_engine -v 1`
Expected: PASS (21 tests)

- [ ] **Step 7: Commit**

```bash
git add pipeline/services/sync_engine.py apps/api/tests/test_sync_engine.py
git commit -m "feat(sync): stop the connector loop when a run is cancelled"
```

---

## Task 6: `POST /api/projects/<slug>/sync/cancel`

**Files:**
- Modify: `apps/api/views.py` (after `ProjectSyncView`, ~line 1008), `apps/api/urls.py:46`
- Also modify: `apps/dashboard/services/sync_api_service.py` — `task_status`'s step text
- Test: `apps/api/tests/test_sync_cancel_api.py` (new)

**Interfaces:**
- Consumes: `cancel_sync_run(site_url, user=None)`
- Produces: `POST /api/projects/<slug>/sync/cancel` → `{"cancelled": bool, ...}`, always `200`; `task_status()` returns `step == "Cancelled"` and `status == "cancelled"`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_sync_cancel_api.py`:

```python
"""HTTP contract for stopping a refresh."""
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token

from apps.dashboard.models import Project
from apps.sync import scheduling
from apps.sync.models import RefreshRun, RefreshStatus


class SyncCancelApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("tester", password="pw12345678")
        self.token = Token.objects.get_or_create(user=self.user)[0]
        self.project = Project.objects.create(name="FuseHealth", slug="fusehealth",
                                              site_url="sc-domain:fusehealth.com")
        self.url = f"/api/projects/{self.project.slug}/sync/cancel"

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

    def test_cancelling_a_running_refresh_returns_cancelled_true(self):
        run = RefreshRun.objects.create(site_url=self.project.site_url, scope="audit",
                                        status=RefreshStatus.RUNNING, pid=4321)
        with mock.patch.object(scheduling, "terminate_sync_process", return_value=True):
            response = self.client.post(self.url, {}, content_type="application/json",
                                        **self._auth())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["cancelled"])
        self.assertEqual(response.json()["task_id"], run.pk)

    def test_nothing_running_is_200_not_an_error(self):
        """The run may have finished while the user was reaching for the button. That is a
        race, not a client mistake, and a 4xx would make the SPA show a failure toast."""
        response = self.client.post(self.url, {}, content_type="application/json",
                                    **self._auth())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["cancelled"])
        self.assertIn("reason", response.json())

    def test_unknown_project_is_404(self):
        response = self.client.post("/api/projects/nope/sync/cancel", {},
                                    content_type="application/json", **self._auth())
        self.assertEqual(response.status_code, 404)

    def test_token_auth_is_not_redirected_to_the_login_page(self):
        """Without login_not_required, LoginRequiredMiddleware runs before DRF and 302s
        the token request to /login/."""
        with mock.patch.object(scheduling, "terminate_sync_process", return_value=True):
            response = self.client.post(self.url, {}, content_type="application/json",
                                        **self._auth())
        self.assertNotEqual(response.status_code, 302)


class TaskStatusCancelledTests(TestCase):
    def test_a_cancelled_run_reports_done_and_says_cancelled(self):
        from apps.dashboard.services.sync_api_service import task_status

        run = RefreshRun.objects.create(site_url="sc-domain:fusehealth.com", scope="audit",
                                        status=RefreshStatus.CANCELLED, total_count=5,
                                        completed_count=2)
        status = task_status(run.pk)

        self.assertTrue(status["done"])
        self.assertEqual(status["status"], RefreshStatus.CANCELLED)
        self.assertIn("Cancelled", status["step"])
        self.assertIsNone(status["error"], "a cancel is not a failure")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.api.tests.test_sync_cancel_api -v 1`
Expected: FAIL — 404 on the cancel URL; `task_status` reports the error branch.

- [ ] **Step 3: Fix `task_status`' step text**

In `apps/dashboard/services/sync_api_service.py`, in `task_status`, replace the status
branch chain:

```python
    done = run.status != RefreshStatus.RUNNING
    error = None
    if run.status == RefreshStatus.RUNNING:
        step = f"Syncing {run.current_connector or '...'}"
    elif run.status == RefreshStatus.SUCCESS:
        step = f"Done -- {run.records_written:,} records written"
    elif run.status == RefreshStatus.CANCELLED:
        # Not an error branch: `error` stays None so the SPA does not paint a red banner
        # over a deliberate user action, and the count says what was actually kept.
        step = f"Cancelled -- {run.completed_count} of {run.total_count} steps finished"
    else:
        # Failed connectors: short readable step line (the SPA renders it verbatim);
        # the full messages ride along in `error` and in Settings -> Connections.
        first_line = (run.error_message or "Sync error").splitlines()[0]
        step = f"Completed with errors -- {first_line[:160]}"
        error = run.error_message
```

- [ ] **Step 4: Add the view**

In `apps/api/views.py`, after `ProjectSyncView`:

```python
@method_decorator(login_not_required, name="dispatch")
class ProjectSyncCancelView(APIView):
    """Stop the refresh in flight for this site. (POST /api/projects/<slug>/sync/cancel)

    Always 200. "Nothing was running" is a race the user cannot avoid -- the run may have
    finished while they were reaching for the button -- and a 4xx would make the SPA show
    a failure toast for a non-failure.

    No role gate: with 2-3 internal users, a run started by a colleague is far more likely
    to be one you are waiting on than one you must not touch, and being unable to stop a
    wrong run costs more than stopping someone else's. RefreshRun.triggered_by already
    records who started it.
    """
    def post(self, request, slug):
        from apps.dashboard.services.sync_api_service import cancel_sync_run
        site_id = resolve_project_or_404(slug).site_url
        return Response(cancel_sync_run(site_id, user=request.user))
```

- [ ] **Step 5: Route it**

In `apps/api/urls.py`, add above the existing `sync/active` line (specific before generic,
matching the comment already there):

```python
    path("projects/<slug:slug>/sync/cancel", views.ProjectSyncCancelView.as_view(), name="project-sync-cancel"),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_sync_cancel_api -v 1`
Expected: PASS (5 tests)

- [ ] **Step 7: Commit**

```bash
git add apps/api/views.py apps/api/urls.py apps/dashboard/services/sync_api_service.py apps/api/tests/test_sync_cancel_api.py
git commit -m "feat(api): POST /api/projects/<slug>/sync/cancel"
```

---

## Task 7: SPA — Stop button and cancelled handling

**Files:**
- Modify: `static/spa/src/index.html:149-151` (sync banner), `static/spa/src/js/app.js` (`_pollSyncTask` done branch ~line 672; handlers ~line 2321; vals ~line 2539)
- Test: manual (no JS test harness for `app.js`; `static/spa/tests/` covers page modules only)

**Interfaces:**
- Consumes: `POST /api/projects/<id>/sync/cancel`; `task_status().status`
- Produces: `h.syncStop` handler; `syncStopLabel` val; `this.cancelSync()`

- [ ] **Step 1: Add the `cancelSync` method**

In `static/spa/src/js/app.js`, immediately after `startSync` ends (before the
`_pollSyncTask` comment block):

```js
  /* Stop the run in flight. The server marks the row cancelled and kills the sync process;
     this method does NOT tear down the poll loop itself. Letting the existing poller observe
     status='cancelled' keeps one code path in charge of finishing a run, so a cancel cannot
     leave the banner in a state a normal finish would have cleaned up. The only immediate
     local change is the button label, so the click has visible feedback inside the poll
     interval (up to 2s once polling has backed off). */
  cancelSync() {
    const pid = this.state.sync.projectId || this.state.projectId;
    if (!pid || this.state.sync.stopping) return;
    this.setState(st => ({ sync: Object.assign({}, st.sync, { stopping: true }) }));
    window.FuseAPI.post('/api/projects/' + pid + '/sync/cancel', {})
      .then(r => {
        if (!this._alive) return;
        if (!r.cancelled) {
          /* Not a failure: the run finished while the click was in flight. The poller is
             about to report it done, so only the label needs putting back. */
          this.setState(st => ({ sync: Object.assign({}, st.sync, { stopping: false }) }));
          this.notify(r.reason || 'That refresh had already finished');
        }
      })
      .catch(err => {
        if (!this._alive) return;
        this.setState(st => ({ sync: Object.assign({}, st.sync, { stopping: false }) }));
        this.notify((err && err.detail) || 'Could not stop the refresh');
      });
  }
```

- [ ] **Step 2: Handle the cancelled outcome in the poller**

In `_pollSyncTask`, replace the `if (st.done) {` block's body down to the `notify` call:

```js
        if (st.done) {
          clearInterval(this._iv); this._iv = null;
          const wasCancelled = st.status === 'cancelled';
          this.setState(s => {
            const cache = {};
            Object.keys(s.cache).forEach(k2 => { if (k2.indexOf(pid + ':') !== 0) cache[k2] = s.cache[k2]; });
            return {
              sync: { active: false, scope: null, progress: 1, step: 'Done', cost: estCost, projectId: null, startTime: null, steps: [], warnings: [], stopping: false },
              /* A cancelled run did NOT refresh the page, so the freshness pill must not
                 claim it did. Everything the run managed to write before stopping is still
                 real and still worth re-reading, hence the cache clear and refetch below. */
              freshness: wasCancelled ? s.freshness : 'Just now',
              cache,
            };
          });
          this.fetchTab(this.state.tab, pid, this.state.range, true);
          if (this.state.tab !== 'alerts') this.fetchTab('alerts', pid, this.state.range, false);
          this.loadSyncLog(pid);
          const proj = this.state.projects.find(p => p.id === pid) || {};
          const dom = proj.domain || pid;
          if (wasCancelled) {
            const left = Math.max(0, (st.total || 0) - (st.completed || 0));
            this.notify('Refresh stopped for ' + dom + (left ? ' — ' + left + ' step(s) did not run' : ''));
          } else {
            const scopeNotif = { domain_checks: 'Domain checks refreshed for ' + dom, audit: 'Crawl complete — Site Audit refreshed for ' + dom, positions: 'Positioning data refreshed for ' + dom, positions_new: 'New keywords measured for ' + dom, positioning_new: 'New keywords measured for ' + dom, positioning: 'Positioning data refreshed for ' + dom, keywords: 'Keywords data refreshed for ' + dom, backlinks: 'Backlinks data refreshed for ' + dom, ads: 'Ads data refreshed for ' + dom, ai: 'AI Optimization data refreshed for ' + dom, overview: 'Overview data refreshed for ' + dom, seo: 'SEO data refreshed for ' + dom };
            this.notify(scopeNotif[scope] || (scope === 'all' ? ('All modules refreshed for ' + dom) : (scope + ' refreshed for ' + dom)));
          }
        } else {
```

- [ ] **Step 3: Add the handler and the label val**

In `static/spa/src/js/app.js`, beside `syncPanelToggle` in the handlers object:

```js
      syncStop: () => this.cancelSync(),
```

And in the vals object, immediately after the `syncPanelToggleLabel` line:

```js
      syncStopLabel: s.sync.stopping ? 'Stopping…' : 'Stop',
```

- [ ] **Step 4: Add the Stop control to the banner**

In `static/spa/src/index.html`, replace the `sc-if` around the details toggle (lines
149-151) with:

```html
            <sc-if value="{{ syncStepsCount }}" hint-placeholder-val="{{ false }}">
              <span onClick="{{ h.syncPanelToggle }}" role="button" aria-label="Toggle sync step details" style="flex-shrink: 0; font-size: 12px; font-weight: 600; color: #4f46e5; cursor: pointer; white-space: nowrap;">{{ syncPanelToggleLabel }}</span>
            </sc-if>
            <!-- No confirmation on purpose: a Stop button that asks "are you sure?" is a Stop
                 button that does not stop. Recovery is clicking Fetch again. Connectors that
                 have not started are never run; the one in flight may already be billed. -->
            <span onClick="{{ h.syncStop }}" role="button" aria-label="Stop this refresh" style="flex-shrink: 0; font-size: 12px; font-weight: 600; color: #b91c1c; cursor: pointer; white-space: nowrap; border: 1px solid #fecaca; border-radius: 6px; padding: 4px 10px; background: #fef2f2;" style-hover="background:#fee2e2">{{ syncStopLabel }}</span>
```

- [ ] **Step 5: Verify manually**

Run: `python manage.py runserver`
Then: start a sync from any page, click **Stop**.
Expected: the label becomes "Stopping…", the banner clears within ~2s, a toast reads
"Refresh stopped for <domain> — N step(s) did not run", the sidebar freshness pill does
**not** flip to "Just now", and clicking Fetch again starts a new run.

- [ ] **Step 6: Commit**

```bash
git add static/spa/src/index.html static/spa/src/js/app.js
git commit -m "feat(spa): Stop control in the sync banner"
```

---

## Task 8: The freshness setting

**Files:**
- Modify: `apps/dashboard/services/settings_service.py:65-84` (`DEFAULT_SETTINGS_BLOB`), `:739-740` (the pass-through key tuple)
- Test: `apps/dashboard/services/tests/test_sync_freshness.py` (new)

**Interfaces:**
- Consumes: nothing
- Produces: `DEFAULT_SETTINGS_BLOB["manualSync"] == {"skip_fresh_within": "24h"}`; the key is persisted by `apply_settings_update`

**Why a dict group:** `build_settings_response` merges defaults per key with
`if isinstance(defaults, dict) and isinstance(blob.get(key), dict)` (line 620-622), so a
bare string default would silently never merge. It cannot live inside `syncConfig` either —
`scheduling.get_sync_config` merges only keys present in the defaults and `SYNC_MODULES`
iterates them as modules, so a non-module key there would leak into cadence logic.

- [ ] **Step 1: Write the failing test**

Create `apps/dashboard/services/tests/test_sync_freshness.py`:

```python
"""The manual-refresh freshness window: its setting, its rule, and its wiring.

The scheduler has had per-module cadences since 2026-07 (scheduling.CADENCE_INTERVALS).
This is the equivalent for the manual path, which until now checked exactly one thing --
"is a run already going" -- and never asked whether the data was already fresh.
"""
from django.test import TestCase

from apps.dashboard.models import ProjectSettings
from apps.dashboard.services.settings_service import (
    DEFAULT_SETTINGS_BLOB, apply_settings_update, build_settings_response,
)

SITE_URL = "sc-domain:fusehealth.com"


class ManualSyncSettingTests(TestCase):
    def test_the_default_window_is_24h(self):
        self.assertEqual(DEFAULT_SETTINGS_BLOB["manualSync"]["skip_fresh_within"], "24h")

    def test_the_setting_persists(self):
        apply_settings_update(SITE_URL, {"manualSync": {"skip_fresh_within": "6h"}})
        blob = ProjectSettings.objects.get(site_url=SITE_URL).data
        self.assertEqual(blob["manualSync"]["skip_fresh_within"], "6h")

    def test_a_partially_saved_blob_still_yields_a_window(self):
        """Same merge guarantee every other settings group has."""
        ProjectSettings.objects.create(site_url=SITE_URL, data={"manualSync": {}})
        response = build_settings_response(SITE_URL)
        self.assertEqual(response["manualSync"]["skip_fresh_within"], "24h")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness -v 1`
Expected: FAIL — `KeyError: 'manualSync'`

- [ ] **Step 3: Add the default**

In `apps/dashboard/services/settings_service.py`, add to `DEFAULT_SETTINGS_BLOB`
immediately after the `syncConfig` entry:

```python
    # The manual path's equivalent of syncConfig's cadences. `syncConfig` governs the
    # SCHEDULER; this governs the refresh BUTTONS, which until now spent metered API
    # budget with no freshness check of any kind.
    #
    # Deliberately a separate group rather than a key inside syncConfig: SYNC_MODULES
    # iterates syncConfig's keys as module names, so a non-module key there would be
    # read as a module. Values are the keys of sync_api_service.FRESHNESS_WINDOWS.
    "manualSync": {"skip_fresh_within": "24h"},
```

- [ ] **Step 4: Persist it**

In `apply_settings_update`, add `"manualSync"` to the pass-through tuple:

```python
    for key in ("workspace", "prefs", "notifications", "aiConfig", "dataPrefs", "syncConfig",
                "manualSync", "platformConnectors", "alertRules", "crawl"):
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness -v 1`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/settings_service.py apps/dashboard/services/tests/test_sync_freshness.py
git commit -m "feat(settings): manualSync.skip_fresh_within, default 24h"
```

---

## Task 9: The freshness rule

**Files:**
- Modify: `apps/dashboard/services/sync_api_service.py` (imports; new constants and functions before `_connectors_for_scope`)
- Test: `apps/dashboard/services/tests/test_sync_freshness.py`

**Interfaces:**
- Consumes: `DEFAULT_SETTINGS_BLOB["manualSync"]`
- Produces:
  - `FRESHNESS_WINDOWS: dict[str, timedelta | None]` — keys `off, 1h, 6h, 12h, 24h, 48h, 7d`
  - `freshness_window(site_url: str) -> timedelta | None`
  - `fresh_connectors(site_url, connectors: list[str], window: timedelta | None, now=None) -> dict[str, datetime]`

- [ ] **Step 1: Write the failing test**

Append to `apps/dashboard/services/tests/test_sync_freshness.py`:

```python
from datetime import timedelta

from django.utils import timezone

from apps.dashboard.services.sync_api_service import (
    FRESHNESS_WINDOWS, fresh_connectors, freshness_window,
)
from apps.sync.models import SyncLog, SyncStatus


class FreshConnectorsTests(TestCase):
    def _log(self, connector, minutes_ago, status=SyncStatus.SUCCESS):
        return SyncLog.objects.create(
            connector=connector, site_url=SITE_URL, status=status,
            last_synced=timezone.now() - timedelta(minutes=minutes_ago),
        )

    def test_a_recent_success_is_fresh(self):
        self._log("dataforseo_backlinks", minutes_ago=40)
        fresh = fresh_connectors(SITE_URL, ["dataforseo_backlinks"], timedelta(hours=24))
        self.assertEqual(list(fresh), ["dataforseo_backlinks"])

    def test_an_old_success_is_not_fresh(self):
        self._log("dataforseo_backlinks", minutes_ago=60 * 30)
        fresh = fresh_connectors(SITE_URL, ["dataforseo_backlinks"], timedelta(hours=24))
        self.assertEqual(fresh, {})

    def test_a_recent_error_is_never_fresh(self):
        """The single most important row in this table. Clicking Refresh right after fixing
        a credential is the whole reason the button exists -- skipping it because the
        FAILURE was recent would make the fix untestable."""
        self._log("dataforseo_backlinks", minutes_ago=5, status=SyncStatus.ERROR)
        fresh = fresh_connectors(SITE_URL, ["dataforseo_backlinks"], timedelta(hours=24))
        self.assertEqual(fresh, {})

    def test_a_connector_that_never_ran_is_never_fresh(self):
        fresh = fresh_connectors(SITE_URL, ["dataforseo_backlinks"], timedelta(hours=24))
        self.assertEqual(fresh, {})

    def test_a_null_window_skips_nothing(self):
        self._log("dataforseo_backlinks", minutes_ago=1)
        self.assertEqual(fresh_connectors(SITE_URL, ["dataforseo_backlinks"], None), {})

    def test_only_the_requested_connectors_are_considered(self):
        self._log("gsc", minutes_ago=5)
        self._log("ga4", minutes_ago=5)
        fresh = fresh_connectors(SITE_URL, ["gsc"], timedelta(hours=24))
        self.assertEqual(list(fresh), ["gsc"])

    def test_freshness_reads_rows_written_by_the_scheduler_too(self):
        """SyncLog does not record WHO ran a connector, and that is correct here: if the
        scheduler refreshed Backlinks an hour ago, a manual click should still see it."""
        self._log("dataforseo_backlinks", minutes_ago=60)
        fresh = fresh_connectors(SITE_URL, ["dataforseo_backlinks"], timedelta(hours=24))
        self.assertEqual(list(fresh), ["dataforseo_backlinks"])


class FreshnessWindowTests(TestCase):
    def test_off_means_no_window(self):
        self.assertIsNone(FRESHNESS_WINDOWS["off"])

    def test_the_default_window_is_24_hours(self):
        self.assertEqual(freshness_window(SITE_URL), timedelta(hours=24))

    def test_the_saved_setting_wins(self):
        apply_settings_update(SITE_URL, {"manualSync": {"skip_fresh_within": "6h"}})
        self.assertEqual(freshness_window(SITE_URL), timedelta(hours=6))

    def test_off_disables_the_guard(self):
        apply_settings_update(SITE_URL, {"manualSync": {"skip_fresh_within": "off"}})
        self.assertIsNone(freshness_window(SITE_URL))

    def test_an_unrecognised_value_disables_the_guard(self):
        """A hand-edited blob must not invent a window. Skipping a connector the user did
        not ask to skip is worse than running one they might not have needed."""
        apply_settings_update(SITE_URL, {"manualSync": {"skip_fresh_within": "banana"}})
        self.assertIsNone(freshness_window(SITE_URL))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness -v 1`
Expected: FAIL — `ImportError: cannot import name 'FRESHNESS_WINDOWS'`

- [ ] **Step 3: Implement**

In `apps/dashboard/services/sync_api_service.py`, add to the imports at the top:

```python
from datetime import datetime, timedelta
```

and add `SyncLog, SyncStatus` to the existing `apps.sync.models` import:

```python
from apps.sync.models import RefreshRun, RefreshStatus, SyncLog, SyncStatus
```

Then insert immediately after the `SCOPE_ALIASES` dict:

```python
# ---------------------------------------------------------------------------
# Manual-refresh freshness guard
# ---------------------------------------------------------------------------
#
# The scheduler has had freshness logic since 2026-07: scheduling.CADENCE_INTERVALS plus
# FAILED_RUN_BACKOFF decide when a module is due. The MANUAL path had none -- start_sync_run
# checked only "is a run already going for this site" -- so re-clicking a refresh button
# re-spent metered DataForSEO credits on data that had not changed.
#
# This is the manual path's equivalent, and it is deliberately manual-ONLY. Applying it to
# scheduled runs would put two systems in charge of one decision: a 24h skip window stacked
# on a 12h `ads` cadence means Ads silently never runs again, and the symptom of that bug is
# nothing happening, which is the hardest kind to notice.
FRESHNESS_WINDOWS: dict[str, timedelta | None] = {
    "off": None,
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "12h": timedelta(hours=12),
    "24h": timedelta(hours=24),
    "48h": timedelta(hours=48),
    "7d": timedelta(days=7),
}


def freshness_window(site_url: str) -> timedelta | None:
    """This site's manual-refresh window, or None when the guard is off.

    None for `off` AND for any unrecognised value. Falling back to a default on garbage
    would skip connectors the user never asked to skip; running something unnecessarily is
    the cheaper mistake.
    """
    # Lazy: settings_service pulls in SQLAlchemy and the accounts models.
    from apps.dashboard.models import ProjectSettings
    from apps.dashboard.services.settings_service import DEFAULT_SETTINGS_BLOB

    default = DEFAULT_SETTINGS_BLOB["manualSync"]["skip_fresh_within"]
    row = ProjectSettings.objects.filter(site_url=site_url).first()
    saved = (row.data or {}).get("manualSync") if row else None
    value = saved.get("skip_fresh_within", default) if isinstance(saved, dict) else default
    return FRESHNESS_WINDOWS.get(value)


def fresh_connectors(
    site_url: str,
    connectors: list[str],
    window: timedelta | None,
    now: datetime | None = None,
) -> dict[str, datetime]:
    """{connector: last_synced} for those that SUCCEEDED inside `window`.

    Per connector, not per scope, because SyncLog is UNIQUE(connector, site_url) -- so
    `positioning` can legitimately have two connectors refreshed this morning and three
    that are nine days old, and only the stale three need running.

    Never skips a connector whose last run ERRORED, however recent. Clicking Refresh right
    after fixing a credential is the single most common reason to press the button, and
    treating a fresh failure as "fresh" would make that fix impossible to verify.

    Never skips one that has no SyncLog row: never-synced is not fresh.
    """
    if window is None or not connectors:
        return {}
    cutoff = (now or timezone.now()) - window
    rows = SyncLog.objects.filter(
        connector__in=connectors,
        site_url=site_url,
        status=SyncStatus.SUCCESS,
        last_synced__gte=cutoff,
    ).values_list("connector", "last_synced")
    return {connector: last_synced for connector, last_synced in rows}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness -v 1`
Expected: PASS (15 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/services/sync_api_service.py apps/dashboard/services/tests/test_sync_freshness.py
git commit -m "feat(sync): per-connector freshness rule for manual refreshes"
```

---

## Task 10: Wire the guard into `start_sync_run`

**Files:**
- Modify: `apps/dashboard/services/sync_api_service.py:96-176` (`start_sync_run`)
- Modify: `apps/sync/management/commands/run_scheduled_syncs.py:82` (`_start`)
- Modify: `apps/api/views.py:1007` (`ProjectSyncView.post` — forward `force`)
- Test: `apps/dashboard/services/tests/test_sync_freshness.py`

**Interfaces:**
- Consumes: `freshness_window`, `fresh_connectors`, `RefreshRun.skipped_connectors`
- Produces: `start_sync_run(site_url, scope, user=None, force=False, manual=True) -> dict`. Adds the all-fresh shape `{"fresh": True, "scope": str, "connectors": list[str], "last_synced": str, "detail": str}` and `"skipped": list[str]` on the normal shape.

**Two flags, one meaning each — do not collapse them:**
- `manual=False` — the caller is the **scheduler**, whose cadences already are its freshness logic. The window never applies. Spec §4.2.
- `force=True` — the caller is a **user** who answered "Refresh anyway" to the all-fresh confirm. The window is ignored for this one run.

`run_scheduled_syncs._start` reads `info['task_id']` immediately after calling `start_sync_run`. The all-fresh shape has no `task_id`, so without `manual=False` the scheduler would **crash with a KeyError** as well as silently starving any module whose cadence is shorter than the window.

- [ ] **Step 1: Write the failing test**

Append to `apps/dashboard/services/tests/test_sync_freshness.py`:

```python
from unittest import mock

from apps.dashboard.services.sync_api_service import start_sync_run
from apps.sync.models import RefreshRun


class StartSyncRunFreshnessTests(TestCase):
    def setUp(self):
        p = mock.patch("apps.dashboard.services.sync_api_service._spawn_sync_process",
                       return_value=4321)
        p.start()
        self.addCleanup(p.stop)

    def _log(self, connector, minutes_ago, status=SyncStatus.SUCCESS):
        SyncLog.objects.create(connector=connector, site_url=SITE_URL, status=status,
                               last_synced=timezone.now() - timedelta(minutes=minutes_ago))

    def test_all_fresh_creates_no_run_at_all(self):
        """The point of the guard: no RefreshRun, no process, no API call."""
        self._log("dataforseo_backlinks", minutes_ago=40)

        result = start_sync_run(SITE_URL, "backlinks")

        self.assertTrue(result["fresh"])
        self.assertEqual(result["connectors"], ["dataforseo_backlinks"])
        self.assertIn("last_synced", result)
        self.assertEqual(RefreshRun.objects.count(), 0)

    def test_partially_fresh_runs_and_records_what_it_skipped(self):
        self._log("gsc", minutes_ago=30)          # fresh
        self._log("ga4", minutes_ago=60 * 40)     # stale

        result = start_sync_run(SITE_URL, "overview")

        self.assertNotIn("fresh", result)
        self.assertEqual(result["skipped"], ["gsc"])
        run = RefreshRun.objects.get(pk=result["task_id"])
        self.assertEqual(run.skipped_connectors, ["gsc"])
        self.assertEqual(run.total_count, 2, "skipped steps still count toward the total")

    def test_force_ignores_the_window_entirely(self):
        self._log("dataforseo_backlinks", minutes_ago=1)

        result = start_sync_run(SITE_URL, "backlinks", force=True)

        self.assertNotIn("fresh", result)
        run = RefreshRun.objects.get(pk=result["task_id"])
        self.assertEqual(run.skipped_connectors, [])

    def test_off_reproduces_the_old_behaviour(self):
        apply_settings_update(SITE_URL, {"manualSync": {"skip_fresh_within": "off"}})
        self._log("dataforseo_backlinks", minutes_ago=1)

        result = start_sync_run(SITE_URL, "backlinks")

        run = RefreshRun.objects.get(pk=result["task_id"])
        self.assertEqual(run.skipped_connectors, [])

    def test_a_brand_new_site_is_never_skipped(self):
        """No SyncLog rows means nothing is fresh, so the initial sync POST /api/projects
        auto-starts always runs in full."""
        result = start_sync_run(SITE_URL, "all")
        run = RefreshRun.objects.get(pk=result["task_id"])
        self.assertEqual(run.skipped_connectors, [])

    def test_refresh_all_is_subject_to_the_window(self):
        """The most expensive manual run there is; exempting it would defeat the feature."""
        self._log("gsc", minutes_ago=10)
        result = start_sync_run(SITE_URL, "all")
        self.assertIn("gsc", result["skipped"])

    def test_an_already_running_sync_still_wins_over_freshness(self):
        """The one-run-per-site guard must be checked first: attaching to the live run is
        what the user wanted, and reporting 'everything is fresh' would hide it."""
        RefreshRun.objects.create(site_url=SITE_URL, scope="backlinks",
                                  status=RefreshStatus.RUNNING, pid=999)
        self._log("dataforseo_backlinks", minutes_ago=5)

        result = start_sync_run(SITE_URL, "backlinks")

        self.assertTrue(result.get("already_running"))
        self.assertNotIn("fresh", result)

    def test_a_scheduled_run_ignores_the_window(self):
        """Spec 4.2. The cadences ARE the scheduler's freshness logic; stacking a 24h window
        on a 12h `ads` cadence would mean Ads silently never runs again."""
        self._log("dataforseo_backlinks", minutes_ago=5)

        result = start_sync_run(SITE_URL, "backlinks", manual=False)

        self.assertNotIn("fresh", result)
        run = RefreshRun.objects.get(pk=result["task_id"])
        self.assertEqual(run.skipped_connectors, [])

    def test_a_scheduled_run_always_returns_a_task_id(self):
        """run_scheduled_syncs._start reads info['task_id'] on the very next line. The
        all-fresh shape has no such key, so reaching it from the scheduler is a crash."""
        for connector in ("gsc", "ga4"):
            self._log(connector, minutes_ago=1)

        result = start_sync_run(SITE_URL, "overview", manual=False)

        self.assertIn("task_id", result)
```

Add `from apps.sync.models import RefreshStatus` to this test file's imports.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness.StartSyncRunFreshnessTests -v 1`
Expected: FAIL — `KeyError: 'fresh'`

- [ ] **Step 3: Change the signature and docstring**

In `apps/dashboard/services/sync_api_service.py`, change the `def` line:

```python
def start_sync_run(site_url: str, scope: str, user=None, force: bool = False,
                   manual: bool = True) -> dict:
```

and add to the docstring, after the "Missing credentials warn" bullet:

```
    * **Already-fresh connectors are skipped.** A manual refresh no longer re-spends metered
      API budget on data that synced minutes ago. If EVERY connector in the scope is fresh,
      no run is created at all and the caller gets `{"fresh": True, ...}` -- a shape with NO
      `task_id` -- so the SPA can confirm with the user; answering "Refresh anyway" re-calls
      with `force=True`. See `fresh_connectors`.

      `manual=False` disables the guard entirely and is what `run_scheduled_syncs` passes.
      Two reasons, and both matter: the cadences in `syncConfig` already ARE the scheduler's
      freshness logic (a 24h window stacked on a 12h `ads` cadence would silently starve
      Ads), and `_start` reads `info['task_id']` on the next line, which the all-fresh shape
      does not have.
```

- [ ] **Step 4: Insert the guard**

In `start_sync_run`, insert between the `existing is not None` block's closing and the
`try:` that computes `warnings`:

```python
    # Freshness is checked AFTER the one-run-per-site guard on purpose: if a run is already
    # in flight, attaching to it is what the user wanted, and answering "everything is
    # fresh" would hide a run they are waiting on.
    skip_guard = manual and not force
    fresh = (fresh_connectors(site_url, connectors, freshness_window(site_url))
             if skip_guard else {})
    if connectors and len(fresh) == len(connectors):
        newest = max(fresh.values())
        logger.info("[sync] %r for %r is entirely fresh (%d connector(s)) — no run created",
                    scope, site_url, len(fresh))
        return {
            "fresh": True,
            "scope": scope,
            "connectors": sorted(fresh),
            "last_synced": newest.isoformat(),
            "detail": (
                f"Every step in this refresh synced recently (most recent: "
                f"{newest.isoformat()}). Nothing needs re-fetching."
            ),
        }
    skipped = sorted(fresh)
```

- [ ] **Step 5: Store the skip list and report it**

In the same function, change the `RefreshRun.objects.create(...)` call to include the field,
and the return dict to report it:

```python
    run = RefreshRun.objects.create(
        site_url=site_url,
        scope=scope,
        triggered_by=user if (user is not None and user.is_authenticated) else None,
        status=RefreshStatus.RUNNING,
        # Skipped connectors still count toward the total, so the checklist can show WHAT was
        # skipped and why, and progress still reaches 100% honestly.
        total_count=len(connectors),
        skipped_connectors=skipped,
    )
```

```python
    return {
        "task_id": run.pk,
        # SPA shows steps[0] as the first progress label; connector names are the honest steps.
        "steps": connectors or ["No connectors for this scope"],
        "est_cost": 0,  # real per-connector cost estimation is future work; honest 0, not faked
        "skipped": skipped,
        "warnings": warnings,
    }
```

- [ ] **Step 6: Exempt the scheduler**

In `apps/sync/management/commands/run_scheduled_syncs.py`, in `_start`, change the call:

```python
        # manual=False: the cadences this command already enforces ARE the freshness logic
        # for scheduled runs. Letting the manual-refresh window apply here too would put two
        # systems in charge of one decision -- a 24h window over a 12h `ads` cadence means
        # Ads silently never runs again -- and the all-fresh response has no `task_id` for
        # the line below to read.
        info = start_sync_run(site_url, module, manual=False)
```

- [ ] **Step 7: Forward `force` from the API**

In `apps/api/views.py`, in `ProjectSyncView.post`, change the last two lines:

```python
        scope = request.data.get("scope", "all")
        # Set only by the SPA's "Refresh anyway" answer to the all-fresh confirm. Anything
        # truthy in the body means "ignore the freshness window for this run".
        force = bool(request.data.get("force", False))
```

```python
        return Response(start_sync_run(site_id, scope, user=request.user, force=force))
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness apps.sync.test_scheduling -v 1`
Expected: PASS (24 new tests, and the existing scheduling suite still green)

- [ ] **Step 9: Commit**

```bash
git add apps/dashboard/services/sync_api_service.py apps/dashboard/services/tests/test_sync_freshness.py apps/sync/management/commands/run_scheduled_syncs.py apps/api/views.py
git commit -m "feat(sync): skip fresh connectors on manual refreshes; scheduler exempt"
```

---

## Task 11: The engine honours `skipped_connectors`

**Files:**
- Modify: `pipeline/services/sync_engine.py` — new helper beside `_run_cancelled`; loop bodies in `sync_all` and `sync_page`; the `_run_post_sync` call sites (lines ~365 and ~497)
- Test: `apps/api/tests/test_sync_engine.py`

**Interfaces:**
- Consumes: `RefreshRun.skipped_connectors`
- Produces: `sync_engine._run_skipped(run_id: int) -> set[str]`

- [ ] **Step 1: Write the failing test**

Append to `SyncEngineTests` in `apps/api/tests/test_sync_engine.py`:

```python
    # ------------------------------------------------------------- fresh skips

    def test_sync_page_does_not_build_a_skipped_connector(self):
        """A skipped connector must never be constructed -- constructing DataForSEO
        connectors is cheap, but running one is not, and the skip has to be provably
        upstream of the API call."""
        self._stub_connectors()
        run = self._run_row(scope="overview")
        RefreshRun.objects.filter(pk=run.pk).update(skipped_connectors=["gsc"])

        summary = sync_page("overview", SITE_URL, run.pk)

        self.assertEqual(list(self.built), ["ga4"])
        self.assertEqual(summary["completed"], 2, "progress must still reach the total")
        run.refresh_from_db()
        self.assertEqual(run.status, RefreshStatus.SUCCESS)
        self.assertEqual(run.completed_count, 2)

    def test_post_sync_only_sees_the_connectors_that_actually_ran(self):
        """_run_post_sync gates aggregate rebuilds on which connectors ran. Passing a
        skipped connector would rebuild SEOAggregate off data nothing refreshed."""
        self._stub_connectors()
        run = self._run_row(scope="overview")
        RefreshRun.objects.filter(pk=run.pk).update(skipped_connectors=["gsc"])

        with patch.object(sync_engine, "_run_post_sync") as post:
            sync_page("overview", SITE_URL, run.pk)

        post.assert_called_once_with(SITE_URL, ["ga4"])

    def test_sync_all_honours_the_skip_list(self):
        self._stub_connectors()
        run = self._run_row(scope="all")
        RefreshRun.objects.filter(pk=run.pk).update(skipped_connectors=["gsc", "ga4"])

        sync_all(SITE_URL, run.pk)

        self.assertNotIn("gsc", self.built)
        self.assertNotIn("ga4", self.built)
        self.assertEqual(len(self.built), len(ALL_CONNECTORS) - 2)

    def test_an_empty_skip_list_changes_nothing(self):
        self._stub_connectors()
        run = self._run_row(scope="overview")

        sync_page("overview", SITE_URL, run.pk)

        self.assertEqual(sorted(self.built), sorted(PAGE_CONNECTORS["overview"]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.api.tests.test_sync_engine -v 1`
Expected: FAIL — `gsc` is still built.

- [ ] **Step 3: Add the helper**

In `pipeline/services/sync_engine.py`, immediately after `_run_cancelled`:

```python
def _run_skipped(run_id: int) -> set[str]:
    """Connectors this run must NOT execute because they were already fresh when it started.

    Read, never recomputed. `start_sync_run` decided this once and stored it on the row, so
    the rule has one implementation and `force` needed no second flag across the process
    boundary. Read once per run, before the loop.
    """
    from apps.sync.models import RefreshRun  # type: ignore[import]
    skipped = (RefreshRun.objects.filter(pk=run_id)
               .values_list("skipped_connectors", flat=True).first())
    return set(skipped or [])
```

- [ ] **Step 4: Apply it in `sync_all`**

In `sync_all`, after the `RefreshRun.objects.filter(pk=run_id).update(total_count=total, ...)`
call and before the loop:

```python
    skipped = _run_skipped(run_id)
    ran: list[str] = []
```

Then inside the loop, immediately after the `_run_cancelled` guard added in Task 5:

```python
        if name in skipped:
            logger.info(f"[sync_engine] [{completed + 1}/{total}] Skipping {name!r} — synced "
                        f"recently (manual-refresh freshness window)")
            completed += 1
            RefreshRun.objects.filter(pk=run_id).update(completed_count=completed)
            continue
```

Then, after the `try/except` that runs the connector, add `ran.append(name)` — place it
immediately after `completed += 1`:

```python
        records = result.get("records_written", 0)
        completed += 1
        total_records += records
        ran.append(name)
```

Finally change the post-sync call:

```python
    # Only the connectors that ACTUALLY ran. _run_post_sync gates every rebuild on this
    # list, so passing a skipped connector would rebuild aggregates off data that nothing
    # refreshed.
    _run_post_sync(site_url, ran)
```

- [ ] **Step 5: Apply the same three edits in `sync_page`**

In `sync_page`: add `skipped = _run_skipped(run_id)` and `ran: list[str] = []` after the
`incremental_kws` resolution block and before `for name in connector_names:`; add the same
`if name in skipped:` guard after the `_run_cancelled` guard; add `ran.append(name)` after
`completed += 1`; and change the post-sync call to:

```python
    _run_post_sync(site_url, ran)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_sync_engine -v 1`
Expected: PASS (25 tests)

- [ ] **Step 7: Commit**

```bash
git add pipeline/services/sync_engine.py apps/api/tests/test_sync_engine.py
git commit -m "feat(sync): the engine skips connectors the run recorded as fresh"
```

---

## Task 12: The checklist tells the two skips apart

**Files:**
- Modify: `apps/dashboard/services/sync_api_service.py:179-232` (`_step_details`), plus a new `_humanise_age` helper above it
- Test: `apps/dashboard/services/tests/test_sync_freshness.py`

**Interfaces:**
- Consumes: `RefreshRun.skipped_connectors`
- Produces: `_humanise_age(when: datetime, now: datetime | None = None) -> str`; `_step_details` emits `detail` starting `"Skipped — synced "` for fresh skips and `"Skipped — credentials not configured"` for credential skips

**Why:** a connector skipped as fresh is a *success* — we already have the data. One skipped
for missing credentials is a *problem*. Rendering both as one grey "skipped" is how a broken
integration stays invisible for weeks, which `_step_details`' own docstring already warns about.

- [ ] **Step 1: Write the failing test**

Append to `apps/dashboard/services/tests/test_sync_freshness.py`:

```python
from apps.dashboard.services.sync_api_service import _humanise_age, task_status


class StepDetailSkipKindsTests(TestCase):
    def test_the_two_skip_kinds_are_not_conflated(self):
        run = RefreshRun.objects.create(
            site_url=SITE_URL, scope="overview", status=RefreshStatus.SUCCESS,
            total_count=2, completed_count=2, skipped_connectors=["gsc"],
        )
        SyncLog.objects.create(connector="gsc", site_url=SITE_URL, status=SyncStatus.SUCCESS,
                               last_synced=timezone.now() - timedelta(hours=4))
        # ga4 has no row touched during this run -> the credentials case.

        steps = {s["name"]: s for s in task_status(run.pk)["steps"]}

        self.assertEqual(steps["gsc"]["state"], "skipped")
        self.assertIn("synced", steps["gsc"]["detail"])
        self.assertNotIn("credentials", steps["gsc"]["detail"])

        self.assertEqual(steps["ga4"]["state"], "skipped")
        self.assertIn("credentials", steps["ga4"]["detail"])

    def test_a_fresh_skip_reports_when_it_last_synced(self):
        run = RefreshRun.objects.create(
            site_url=SITE_URL, scope="backlinks", status=RefreshStatus.SUCCESS,
            total_count=1, completed_count=1, skipped_connectors=["dataforseo_backlinks"],
        )
        SyncLog.objects.create(connector="dataforseo_backlinks", site_url=SITE_URL,
                               status=SyncStatus.SUCCESS,
                               last_synced=timezone.now() - timedelta(hours=4))

        step = task_status(run.pk)["steps"][0]
        self.assertEqual(step["detail"], "Skipped — synced 4h ago")


class HumaniseAgeTests(TestCase):
    def test_minutes(self):
        now = timezone.now()
        self.assertEqual(_humanise_age(now - timedelta(minutes=40), now), "40m ago")

    def test_hours(self):
        now = timezone.now()
        self.assertEqual(_humanise_age(now - timedelta(hours=4), now), "4h ago")

    def test_days(self):
        now = timezone.now()
        self.assertEqual(_humanise_age(now - timedelta(days=3), now), "3d ago")

    def test_just_now(self):
        now = timezone.now()
        self.assertEqual(_humanise_age(now - timedelta(seconds=5), now), "just now")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness -v 1`
Expected: FAIL — `ImportError: cannot import name '_humanise_age'`

- [ ] **Step 3: Add the helper**

In `apps/dashboard/services/sync_api_service.py`, immediately before `_step_details`:

```python
def _humanise_age(when: datetime, now: datetime | None = None) -> str:
    """"4h ago" for a step-checklist line. Coarse on purpose: the user is deciding whether
    a skip was reasonable, not reading a timestamp."""
    seconds = ((now or timezone.now()) - when).total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"
```

- [ ] **Step 4: Teach `_step_details` the second skip kind**

In `_step_details`, add to the docstring before the closing `"""`:

```
    There are now TWO kinds of skip and they must not be conflated. A connector skipped
    because it was already fresh is a SUCCESS -- we have the data. One skipped because its
    credentials are missing is a PROBLEM. Rendering both as one grey "skipped" is exactly
    the invisibility this docstring warns about above.
```

Then add the skip-list read after the `logs` dict is built, and the branch at the top of the
loop:

```python
    finished = run.completed_count
    running_now = run.status == RefreshStatus.RUNNING
    skipped_fresh = set(run.skipped_connectors or [])

    steps = []
    for i, name in enumerate(connectors):
        log = logs.get(name)
        ran_this_time = bool(log and log.last_synced and log.last_synced >= run.started_at)

        if name in skipped_fresh:
            when = _humanise_age(log.last_synced) if (log and log.last_synced) else "recently"
            steps.append({
                "name": name,
                "state": "skipped",
                "detail": f"Skipped — synced {when}",
                "records": None,
                "seconds": None,
            })
            continue

        if i < finished:
```

(The rest of the loop body is unchanged.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_sync_freshness -v 1`
Expected: PASS (28 tests)

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/sync_api_service.py apps/dashboard/services/tests/test_sync_freshness.py
git commit -m "feat(sync): distinguish a fresh skip from a credentials skip in the checklist"
```

---

## Task 13: SPA — the all-fresh dialog and the settings dropdown

**Files:**
- Modify: `static/spa/src/js/app.js` (`startSync` ~line 607), `static/spa/src/pages/settings.html:406`, `static/spa/src/js/pages/settings.js` (~line 505)
- Test: manual

**Interfaces:**
- Consumes: `start_sync_run`'s `{"fresh": True, ...}` shape; `manualSync.skip_fresh_within`
- Produces: `startSync(scope, preTaskId, force)`; `this.editSkipFresh(value)`; `h.skipFreshSet` handler; `st.skipFresh` / `st.skipFreshOptions` vals

- [ ] **Step 1: Handle the fresh response in `startSync`**

In `static/spa/src/js/app.js`, change the signature and the POST body, and add the branch:

```js
  /* startSync(scope, preTaskId, force)
   *   scope      – 'all' | 'positions' | 'backlinks' | etc.
   *   preTaskId  – (optional) task_id already created server-side (e.g., from POST /api/projects).
   *                When supplied the POST /api/projects/<slug>/sync call is skipped and we go
   *                straight to polling, avoiding a redundant second sync run.
   *   force      – (optional) ignore the manual-refresh freshness window. Set only by the
   *                "Refresh anyway" answer to the all-fresh confirm below. */
  startSync(scope, preTaskId, force) {
    if (this.state.sync.active && (!this.state.sync.projectId || this.state.sync.projectId === this.state.projectId)) return;
    const pid = this.state.projectId;
    const activeScope = scope || 'all';

    if (preTaskId != null) {
      // Task already created server-side — skip POST /sync and go straight to polling.
      this._pollSyncTask(preTaskId, activeScope, pid, 0, []);
      return;
    }

    window.FuseAPI.post('/api/projects/' + pid + '/sync', { scope: activeScope, force: !!force })
      .then(t => {
        if (!this._alive) return;
        /* Every connector in this scope synced inside the freshness window, so the server
           created NO run — there was nothing to fetch. Ask rather than silently doing
           nothing: "I pressed Refresh and the app ignored me" is worse than one dialog.
           This is the only place `force` is ever set. */
        if (t.fresh) {
          const n = (t.connectors || []).length;
          if (window.confirm('Everything in this refresh is already up to date — '
                + n + ' step(s) synced recently.\n\nRefresh anyway? This will re-run them '
                + 'and re-spend any API credits they cost.')) {
            this.startSync(scope, null, true);
          }
          return;
        }
        if (t.warnings && t.warnings.length) {
          // Shown once, at start, rather than repeated on every poll tick: "N steps will be
          // skipped because X credential is missing" is a fact about the whole run, not a
          // per-second update.
          t.warnings.forEach(w => this.notify(w));
        }
        if (t.skipped && t.skipped.length) {
          this.notify(t.skipped.length + ' step(s) skipped — already synced recently');
        }
        this._pollSyncTask(t.task_id, activeScope, pid, t.est_cost || 0, t.steps || []);
      })
      .catch(err => { if (this._alive) this.notify(err.detail || 'Could not start sync'); });
  }
```

- [ ] **Step 2: Add the settings handler**

In `static/spa/src/js/pages/settings.js`, find the `editSyncCfg` call site pattern and add a
sibling. In the vals object, immediately after the `syncRows:` entry:

```js
        /* The manual path's freshness window. Separate from the cadence dropdowns above it
           because it governs the BUTTONS, not the scheduler — stacking a 24h skip on a 12h
           cadence would silently starve that module. */
        skipFresh: skipFresh,
        skipFreshOptions: [
          { value: 'off', label: 'Off — always re-fetch' },
          { value: '1h', label: '1 hour' },
          { value: '6h', label: '6 hours' },
          { value: '12h', label: '12 hours' },
          { value: '24h', label: '24 hours' },
          { value: '48h', label: '48 hours' },
          { value: '7d', label: '7 days' }
        ],
```

And in `static/spa/src/js/app.js`, add the method immediately after `editSyncCfg` (line
~1449), mirroring it exactly — `putSettings(body, message)` is the shared settings-PUT helper:

```js
  /* The manual-refresh freshness window. Sibling of editSyncCfg, but a DIFFERENT settings
     group: syncConfig drives the scheduler, manualSync drives the refresh buttons. */
  editSkipFresh(value) {
    this.setState({ skipFresh: value });
    this.putSettings({ manualSync: { skip_fresh_within: value } }, 'Manual refresh window updated');
  }
```

and the handler beside `syncCfgSet` (line ~2481):

```js
      skipFreshSet: e => this.editSkipFresh(e.target.value),
```

In `static/spa/src/js/pages/settings.js`, read the local override first so the dropdown
does not snap back before the PUT lands — mirroring `const syncCfg = s.syncCfg || data.syncConfig;`
at line 23:

```js
      const skipFresh = s.skipFresh || (data.manualSync || {}).skip_fresh_within || '24h';
```

and use `skipFresh` for the `skipFresh:` val below instead of re-reading `data`.

- [ ] **Step 3: Add the dropdown**

In `static/spa/src/pages/settings.html`, insert immediately after the "Next scheduled sync"
paragraph (line 406) and before `<div style="display: flex; flex-direction: column;">`:

```html
            <div style="display: flex; align-items: center; gap: 14px; padding: 13px 0; border-top: 1px solid #f1f5f9;">
              <div style="min-width: 0; flex: 1;">
                <div style="font-size: 13.5px; font-weight: 600; color: #0f172a;">Skip connectors synced within</div>
                <div style="font-size: 12px; color: #94a3b8;">Applies to the manual refresh buttons only — scheduled syncs use the cadences below</div>
              </div>
              <select value="{{ st.skipFresh }}" onChange="{{ h.skipFreshSet }}" style="padding: 7px 11px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 12.5px; color: #334155; background: white; outline: none; min-width: 140px;">
                <sc-for list="{{ st.skipFreshOptions }}" as="o" hint-placeholder-count="7"><option value="{{ o.value }}">{{ o.label }}</option></sc-for>
              </select>
            </div>
```

- [ ] **Step 4: Verify manually**

Run: `python manage.py runserver`
Then:
1. Settings → Automation — the new dropdown reads "24 hours"; change it to "7 days" and reload; it persists.
2. Go to Backlinks, click **Fetch Backlinks** twice. The second click shows the confirm; **Cancel** starts nothing; clicking again and choosing **OK** starts a full run.
3. On a scope with mixed freshness, the banner's step details show `Skipped — synced Xh ago` on the fresh ones and progress still reaches 100%.
4. Set the dropdown to **Off** and confirm refreshes behave exactly as before.

- [ ] **Step 5: Commit**

```bash
git add static/spa/src/js/app.js static/spa/src/js/pages/settings.js static/spa/src/pages/settings.html
git commit -m "feat(spa): all-fresh confirm and the skip-fresh-within setting"
```

---

## Task 14: Documentation and full verification

**Files:**
- Modify: `.claude/api-reference.md` (§ Scope → connector registry, ~line 1148; the sync endpoint list, ~line 6), `.claude/features.md` (§3 topbar, ~line 156-162)
- Test: the full suite

- [ ] **Step 1: Document the endpoint**

In `.claude/api-reference.md`, in the sync section's endpoint list, add beneath the existing
`POST /api/projects/<slug>/sync` line:

```
    POST /api/projects/<slug>/sync/cancel     -> {task_id|null, cancelled, reason?}
```

- [ ] **Step 2: Document both behaviours**

In `.claude/api-reference.md`, immediately after the `domain_checks` paragraph added in the
previous change, add:

```markdown
**Cancellation.** `POST /api/projects/<slug>/sync/cancel` stops the run in flight. Two halves,
both required: the row is flipped to `cancelled` (which `sync_all`/`sync_page` re-read between
connectors, so the run stops even if the kill fails), then the `run_sync` process is killed by
its stored pid. Always `200` — "nothing was running" is a race, not a client error.

`cancelled` is a distinct `RefreshStatus`, never `error`: Settings → Connections renders errors
as live problems, and `FAILED_RUN_BACKOFF` would hold the module off for 6 hours, blocking the
restart the user cancelled in order to make. The kill goes through
`scheduling.terminate_sync_process`, which is deliberately **separate** from `_process_alive` —
see that function's warning about `os.kill` on Windows. The kill fires only when the conditional
status update changed exactly one row; that is the pid-reuse guard.

**Manual-refresh freshness.** `start_sync_run` skips connectors whose `SyncLog` row shows a
`success` inside `manualSync.skip_fresh_within` (default `24h`; `off` disables it). Never skips
an `error` — a failure must be retryable the moment a credential is fixed — and never skips a
connector that has no row. The decision is stored on `RefreshRun.skipped_connectors`, not
recomputed in the sync process. When *every* connector is fresh, no run is created and the
response is `{"fresh": true, connectors, last_synced, detail}`; `force: true` in the POST body
ignores the window. **Manual only** — the scheduler's cadences are its own freshness logic, and
stacking a 24h window on a 12h cadence would silently starve that module.
```

- [ ] **Step 3: Document the UI**

In `.claude/features.md`, replace the two topbar refresh bullets:

```markdown
- **Page refresh button** (green, "Fetch …") — appears only on pages that map to a sync scope.
  Spins and disables while that scope is running.
- **Refresh all button** (indigo) — runs every connector in `ALL_CONNECTORS`.
- **Sync banner** — during any refresh, shows scope, current step, a progress bar, a per-connector
  checklist, and a **Stop** control. Stop takes effect within a couple of seconds, keeps everything
  already written, and skips every connector that had not started; the one in flight may already be
  billed. There is no confirmation — recovery is clicking Fetch again.
- **Already up to date** — a manual refresh skips connectors that synced successfully within
  Settings → Automation's *Skip connectors synced within* window (default 24 hours). Skipped steps
  show *"Skipped — synced 4h ago"* in the checklist. If everything in the scope is fresh, nothing
  runs and a confirm offers **Refresh anyway**. Failed connectors are never skipped.
```

- [ ] **Step 4: Run the full suite**

Run: `python manage.py test`
Expected: PASS. Baseline was 570; this plan adds roughly 50 tests.

- [ ] **Step 5: End-to-end smoke test**

Run: `python manage.py runserver`
1. Start a **Refresh all**, click **Stop** within a few seconds. Confirm the banner clears, the toast reports steps that did not run, and `logs/sync_run_<id>.log` ends without a traceback.
2. Confirm in Settings → Data pipeline that the connector that was mid-flight reads the cancel message, **not** the server-restart one.
3. Click **Fetch Backlinks** twice; confirm the all-fresh dialog on the second.

- [ ] **Step 6: Commit**

```bash
git add .claude/api-reference.md .claude/features.md
git commit -m "docs: record sync cancellation and the manual-refresh freshness guard"
```

---

## Notes for the implementer

- **Do not touch `scheduling._process_alive`.** It carries a hard-won warning that `os.kill` on Windows terminates the process it is asked about, and it runs on every `GET /api/sync/active`. Task 2 adds a *separate* kill helper and Task 2's final test asserts they stay apart.
- **`manual=False` for the scheduler is not optional** (Task 10, Step 6). `run_scheduled_syncs._start` reads `info['task_id']` on the line after `start_sync_run` returns, and the all-fresh shape has no such key — so forgetting it is both a silent cadence-starvation bug and an outright crash in the hourly tick.
- **The pid-reuse guard is the one thing that must not be simplified.** `cancel_sync_run` may kill only when `_claim_for_cancel` returned exactly 1. Collapsing that into `run.save()` reintroduces the race.
- **`_run_post_sync` must receive only the connectors that ran** (Task 11). It gates aggregate rebuilds, anomaly detection, technical-issue rebuilds and the audit snapshot on that list.
- **`static/spa/src/` has no build step** — includes are resolved per request by `apps/dashboard/spa_views.py`. Edit `src/`, reload the browser.
- **Test count check:** the full suite should be green at each commit, not only at the end.
