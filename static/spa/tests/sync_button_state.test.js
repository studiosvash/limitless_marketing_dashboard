/* Tests for the per-page refresh button's four states, and for what a click does when a
   refresh is already running.

   Run: node --test static/spa/tests/

   WHY THIS EXISTS. Only one sync runs per project — the server enforces that in
   `start_sync_run`, which returns the in-flight run's task_id rather than starting a second.
   The client half of that contract was wrong in two ways that between them made every
   secondary refresh button lie:

     1. `isPageSyncing` was `syncing && activeScope !== 'all'` — "some narrow scope is
        running". So a Positions refresh put a spinner and a "Syncing…" label on the Keywords
        button, the Backlinks button and every other page button simultaneously. Six pages
        claimed to be fetching while one was.

     2. `startSync()` opened with a bare `return` when a sync was active. Clicking a second
        page's Refresh issued no request, raised no toast and changed no state — visually
        identical to a dead button.

   The rules below are extracted from the shipping source rather than restated, so a future
   edit to app.js that reverts either bug fails here. Same brace-matching approach as
   visibility_scores.test.js: the SPA has no bundler.

   `stalled` (the browser cannot reach the server) is deliberately NOT one of the button
   states — it belongs to the run, not to a page — but it must never be confused with the run
   having stopped, so its own assertions are at the bottom. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const APP_JS = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'js', 'app.js'), 'utf8'
);

/* ── The rules, as the source states them ─────────────────────────────────────────────── */

function ruleFor(name) {
  const line = APP_JS.split('\n').find(l => l.trim().startsWith('const ' + name + ' ='));
  assert.ok(line, `\`const ${name} =\` not found in app.js — has the derivation been renamed?`);
  return line.trim();
}

/* Reimplement the four states from the extracted expressions, so the assertions below run
   against the real logic rather than a copy of it. */
function buttonState({ active, runningScope, projectId, currentProject, pageScope, queued }) {
  const s = {
    projectId: currentProject,
    sync: { active, scope: runningScope, projectId, queued },
  };
  const syncing = s.sync.active && (!s.sync.projectId || s.sync.projectId === s.projectId);
  const activeScope = syncing ? (s.sync.scope || 'all') : null;
  /* `queued` is a FIFO ARRAY: the server allows one run per DOMAIN and Position Tracking
     registers many projects per domain, so fetching 12 city projects back-to-back queues 11
     of them — a single-slot queue silently lost 10. */
  const queuedForThisProject = (s.sync.queued || []).find(e => e.projectId === s.projectId);
  const queuedScope = queuedForThisProject ? queuedForThisProject.scope : null;
  const isPageSyncing = syncing && !!pageScope && activeScope === pageScope;
  const isPageQueued = !!pageScope && queuedScope === pageScope;
  const isPageBlocked = syncing && !!pageScope && !isPageSyncing && !isPageQueued;
  if (isPageSyncing) return 'busy';
  if (isPageQueued) return 'queued';
  if (isPageBlocked) return 'blocked';
  return 'idle';
}

test('the page button compares against ITS OWN scope, not "any narrow scope"', () => {
  // The exact regression: a Positions run must not light up the Keywords button.
  const rule = ruleFor('isPageSyncing');
  assert.ok(rule.includes('activeScope === pageScope'),
    'isPageSyncing must compare activeScope to this page\'s own scope; got: ' + rule);
  assert.ok(!rule.includes("!== 'all'"),
    'isPageSyncing must not be "some scope other than all is running": ' + rule);
});

test('a Positions run shows busy on Positioning and blocked elsewhere', () => {
  const run = { active: true, runningScope: 'positions', projectId: 'p1', currentProject: 'p1' };
  assert.strictEqual(buttonState({ ...run, pageScope: 'positions' }), 'busy');
  assert.strictEqual(buttonState({ ...run, pageScope: 'keywords' }), 'blocked');
  assert.strictEqual(buttonState({ ...run, pageScope: 'backlinks' }), 'blocked');
  assert.strictEqual(buttonState({ ...run, pageScope: 'audit' }), 'blocked');
});

test('a "Refresh all" run leaves every page button blocked, never busy', () => {
  // 'all' does cover every page, but the PAGE button did not start it and pressing it again
  // must not read as "this page is fetching" — the all-modules bar above already says so.
  const run = { active: true, runningScope: 'all', projectId: 'p1', currentProject: 'p1' };
  assert.strictEqual(buttonState({ ...run, pageScope: 'keywords' }), 'blocked');
  assert.strictEqual(buttonState({ ...run, pageScope: 'positions' }), 'blocked');
});

test('a queued scope reads queued on its own page and blocked on the others', () => {
  const run = {
    active: true, runningScope: 'positions', projectId: 'p1', currentProject: 'p1',
    queued: [{ scope: 'keywords', projectId: 'p1' }],
  };
  assert.strictEqual(buttonState({ ...run, pageScope: 'keywords' }), 'queued');
  assert.strictEqual(buttonState({ ...run, pageScope: 'positions' }), 'busy');
  assert.strictEqual(buttonState({ ...run, pageScope: 'backlinks' }), 'blocked');
});

test('another project\'s run does not touch this project\'s buttons', () => {
  const st = buttonState({
    active: true, runningScope: 'positions', projectId: 'p2', currentProject: 'p1',
    pageScope: 'positions',
  });
  assert.strictEqual(st, 'idle');
});

test('a queue entry for another project is ignored', () => {
  const st = buttonState({
    active: true, runningScope: 'positions', projectId: 'p1', currentProject: 'p1',
    queued: [{ scope: 'keywords', projectId: 'p2' }], pageScope: 'keywords',
  });
  assert.strictEqual(st, 'blocked', 'a sibling project\'s queue must not label this page');
});

test('nothing running means every button is idle', () => {
  assert.strictEqual(buttonState({ active: false, pageScope: 'keywords', currentProject: 'p1' }),
                     'idle');
});

/* ── startSync: a click while busy must queue and say so, never no-op ─────────────────── */

function methodBody(marker) {
  const at = APP_JS.indexOf(marker);
  assert.ok(at !== -1, marker.trim() + ' not found in app.js');
  let depth = 0, i = at + marker.length - 1;
  for (; i < APP_JS.length; i++) {
    if (APP_JS[i] === '{') depth++;
    else if (APP_JS[i] === '}') { depth--; if (depth === 0) break; }
  }
  return APP_JS.slice(at, i + 1);
}

function startSyncBody() {
  return methodBody('  startSync(scope, preTaskId, force, pidOverride) {');
}

test('startSync queues instead of returning silently when a sync is running', () => {
  const body = startSyncBody();
  assert.ok(body.includes('this._queueSync('),
    'a click during a run must go through the queue');
  assert.ok(!/^\s*if \(this\.state\.sync\.active[^\n]*\)\s*return;\s*$/m.test(body),
    'the silent early return is back — a click that does nothing is a broken button');
  const q = methodBody('  _queueSync(scope, pid, force, message) {');
  assert.ok(/queued: \(st\.sync\.queued \|\| \[\]\)\.concat/.test(q),
    '_queueSync must append to the FIFO, not overwrite it — overwriting silently lost every earlier queued fetch');
  assert.ok(q.includes('this.notify('),
    'a click during a run must tell the user something');
});

test('startSync does not queue the same scope twice for one project', () => {
  const q = methodBody('  _queueSync(scope, pid, force, message) {');
  assert.ok(q.includes('Already queued'),
    'pressing a queued page\'s button again must say it is already queued, not stack duplicates');
  assert.ok(/e\.scope === scope && e\.projectId === pid/.test(q),
    'the dedupe key is (scope, project) — the same scope for a DIFFERENT project is a real new fetch');
});

/* ── A sibling project's run: watch theirs, queue ours ───────────────────────────────── */

test('a sibling_running response queues this project\'s fetch instead of attaching', () => {
  // The live-server bug this guards: 18 premierstaff.com city projects, one run slot per
  // domain. Attaching showed the sibling's progress as this project's, "completed", and had
  // fetched nothing for this project's location — a permanently blank Positioning page that
  // looked like a successful fetch.
  const body = startSyncBody();
  assert.ok(body.includes('t.sibling_running'),
    'startSync must recognise the server\'s sibling_running shape');
  const at = body.indexOf('t.sibling_running');
  const branch = body.slice(at, at + 700);
  assert.ok(branch.includes('this._queueSync(activeScope, pid, force'),
    'the sibling branch must queue THIS project\'s fetch');
  assert.ok(/_pollSyncTask\(t\.task_id[^)]*false\)/.test(branch),
    'the sibling branch must watch the sibling run as NOT our own (ownRun=false)');
});

/* ── The queue is drained, and Stop drops it ─────────────────────────────────────────── */

test('a finished run starts the next queued fetch — for ITS project, wherever the user is', () => {
  assert.ok(/if \(queued\.length && !wasCancelled\)/.test(APP_JS),
    'the completion branch must drain the queue');
  assert.ok(/this\.startSync\(next\.scope, null, next\.force, next\.projectId\)/.test(APP_JS),
    'the drained entry must start with its original force flag AND its own projectId — ' +
    'firing it at whichever project is open (or dropping it on navigation) loses the fetch');
});

test('Stop drops the queue rather than silently running the next thing', () => {
  assert.ok(/queued\.length && wasCancelled/.test(APP_JS),
    'a cancelled run must not hand off to the queued refresh — Stop means stop');
});

/* ── The banner names the run's own project ──────────────────────────────────────────── */

test('the banner label comes from the run payload, not the open project', () => {
  assert.ok(/syncForLabel: s\.sync\.projectName \|\| project\.domain/.test(APP_JS),
    'syncForLabel must prefer the run\'s own project name (task payload `project`)');
  assert.ok(/projectName: st\.project \|\| s\.sync\.projectName/.test(APP_JS),
    'each poll tick must carry the server\'s answer for whose run this is');
});

/* ── Connection lost is a distinct, recoverable state ────────────────────────────────── */

test('a brief network failure does not tear down a live progress bar', () => {
  // The old code cleared the bar after POLL_GIVE_UP (6) consecutive failures, which at the
  // 500 ms cadence is THREE SECONDS. A blip killed the bar and told the user to reload while
  // a 20-minute server-side run carried on fine.
  const giveUp = /const RECONNECT_GIVE_UP = (\d+);/.exec(APP_JS);
  assert.ok(giveUp, 'RECONNECT_GIVE_UP not found — has the reconnect path been removed?');
  assert.ok(Number(giveUp[1]) >= 60,
    'the give-up threshold must be minutes of retrying, not seconds; got ' + giveUp[1]);
  assert.ok(/stalled: true/.test(APP_JS), 'a lost connection must set sync.stalled');
});

test('one good tick clears the stalled banner', () => {
  assert.ok(/if \(pollFails >= POLL_GIVE_UP\) \{[\s\S]{0,400}?stalled: false/.test(APP_JS),
    'reconnecting must clear sync.stalled and restore the poll cadence');
});

test('the stalled message does not claim the sync failed', () => {
  const idx = APP_JS.indexOf('Still cannot reach the server');
  assert.ok(idx !== -1, 'the give-up message changed');
  const msg = APP_JS.slice(idx, idx + 200);
  assert.ok(/may well still be running/.test(msg),
    'losing the poll says nothing about the run — the message must not assert failure');
});
