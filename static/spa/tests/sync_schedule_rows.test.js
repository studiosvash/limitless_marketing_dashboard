/* Tests for the Settings -> Automation schedule panel: the per-module rows and the
   future-timestamp formatter behind their "next run" text.

   Run: node --test static/spa/tests/*.test.js

   Same extraction approach as visibility_scores.test.js — the SPA has no bundler, so
   `untilTime` is cut out of the shipping app.js by brace-matching and evaluated. A pasted
   copy would keep passing after the original drifted.

   WHY THIS EXISTS. Three failures met on this panel and none of them was visible from it.

   1. THE MODULE THAT COULD NOT BE SCHEDULED. Until 2026-08-18 the six rows here were the
      only schedulable modules, and none of their connector lists contained plain `gsc` —
      the connector behind the organic clicks / impressions / average position the dashboard
      opens on. So the headline number had no cadence at all and moved only when a human
      pressed "Refresh all". On premierstaff.com it sat three weeks stale while every module
      the user HAD scheduled ran exactly as promised. `organic` is that missing row, and
      the backend-order test below is what stops this list from silently falling behind
      apps/sync/scheduling.SYNC_MODULES again.

   2. ONE "LAST RUN" FOR SEVEN CLOCKS. The header's site-wide last-run is the newest SyncLog
      row from ANY connector, so a 12-hourly Ads sync made the whole panel read as current
      while Search Console had not been fetched in three weeks. Each row now carries its own
      last-run, and these tests pin that it is `last_success` — a failed attempt fetched
      nothing and must not read as a run.

   3. `relTime` ON A FUTURE DATE. relTime computes `Date.now() - t` and returns 'just now'
      for anything under a minute — which a NEGATIVE difference also satisfies. Used for a
      next-run date it renders "next sync in 6 days" as "just now": on a schedule panel that
      reads as "this just ran", the exact opposite of the truth. `untilTime` is the mirror
      that must be used instead, and most of the assertions below are about that boundary. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const SRC = f => fs.readFileSync(path.join(__dirname, '..', 'src', 'js', ...f), 'utf8');
const APP_JS = SRC(['app.js']);
const SETTINGS_JS = SRC(['pages', 'settings.js']);

function extractMethod(src, marker, args) {
  const start = src.indexOf(marker);
  assert.notStrictEqual(start, -1, marker + ' not found');
  let depth = 0, i = src.indexOf('{', start + marker.length - 1);
  const bodyStart = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  return new Function(...args, src.slice(bodyStart + 1, i));
}

const untilTime = extractMethod(APP_JS, 'untilTime(ts) {', ['ts']);
const iso = msFromNow => new Date(Date.now() + msFromNow).toISOString();
const MIN = 60000, HOUR = 60 * MIN, DAY = 24 * HOUR;

/* ── untilTime: the formatter relTime cannot be ─────────────────────────────────────── */

test('a date already past reads as now, never as a negative duration', () => {
  assert.strictEqual(untilTime(iso(-3 * DAY)), 'now');
  assert.strictEqual(untilTime(iso(-30 * MIN)), 'now');
});

test('the boundary relTime gets wrong: a future date is never "just now"', () => {
  /* relTime(iso(+6 days)) returns 'just now' because -518400000 < 60000. That is the whole
     reason a second formatter exists, so it is asserted as an explicit inequality. */
  for (const ahead of [2 * HOUR, 3 * DAY, 20 * DAY]) {
    const out = untilTime(iso(ahead));
    assert.notStrictEqual(out, 'just now');
    assert.notStrictEqual(out, 'now');
    assert.ok(!out.includes('ago'), 'a future date must not be described in the past: ' + out);
  }
});

test('minutes, hours and days each get their own unit', () => {
  assert.match(untilTime(iso(25 * MIN)), /^in \d+m$/);
  assert.match(untilTime(iso(5 * HOUR)), /^in \d+h$/);
  assert.match(untilTime(iso(3 * DAY)), /^in \d+d$/);
});

test('past a week it becomes an absolute date, because "in 23d" is not actionable', () => {
  const out = untilTime(iso(23 * DAY));
  assert.ok(!out.startsWith('in '), 'expected an absolute date, got ' + out);
  assert.ok(/\d/.test(out), 'expected a day number in ' + out);
});

test('a missing or unparseable timestamp is passed through, never guessed at', () => {
  assert.strictEqual(untilTime(null), '');
  assert.strictEqual(untilTime(''), '');
  assert.strictEqual(untilTime('not a date'), 'not a date');
});

/* ── the rows themselves ────────────────────────────────────────────────────────────── */

const SYNC_MODS_SRC = (() => {
  const start = SETTINGS_JS.indexOf('const SYNC_MODS = [');
  assert.notStrictEqual(start, -1, 'SYNC_MODS not found in settings.js');
  return SETTINGS_JS.slice(start, SETTINGS_JS.indexOf('];', start) + 2);
})();

function syncMods() {
  return new Function('return ' + SYNC_MODS_SRC.slice('const SYNC_MODS = '.length, -1))();
}

/* The backend list this panel must not fall behind. Read out of the Python source rather
   than restated, so adding a module there and forgetting the row here fails HERE. */
function backendModules() {
  const py = fs.readFileSync(
    path.join(__dirname, '..', '..', '..', 'apps', 'sync', 'scheduling.py'), 'utf8'
  );
  const m = py.match(/SYNC_MODULES:\s*tuple\[str, \.\.\.\]\s*=\s*\(([\s\S]*?)\)/);
  assert.ok(m, 'SYNC_MODULES not found in apps/sync/scheduling.py');
  return m[1].match(/"([a-z_]+)"/g).map(s => s.replace(/"/g, ''));
}

test('there is a row for every schedulable module, in the backend order', () => {
  assert.deepStrictEqual(syncMods().map(r => r[0]), backendModules());
});

test('organic (Search Console + GA4) is one of them', () => {
  const organic = syncMods().find(r => r[0] === 'organic');
  assert.ok(organic, 'the module that keeps the Overview KPIs fresh has no row');
  assert.match(organic[1], /Search Console/);
});

test('every row can be run on demand — no module is dropdown-only', () => {
  /* `ads` used to pass null here, so the one module on a 12-hour cadence was also the one
     with no way to trigger it by hand when something looked wrong. */
  for (const row of syncMods()) {
    assert.strictEqual(typeof row[3], 'string', row[0] + ' has no Sync-now scope');
    assert.ok(row[3].length, row[0] + ' has an empty Sync-now scope');
  }
});

test('every row offers the same full cadence ladder', () => {
  /* Rows used to carry per-module option subsets, so "Backlinks daily" was unreachable with
     nothing on screen explaining why. One shared list means one place to change. */
  assert.ok(
    !SYNC_MODS_SRC.includes("['daily',") && !SYNC_MODS_SRC.includes("['weekly',"),
    'a row still carries its own option list; all rows must share cadOpts'
  );
  const ladder = SETTINGS_JS.match(/const CADENCES = \[([^\]]*)\]/);
  assert.ok(ladder, 'CADENCES not found');
  for (const c of ['12h', 'daily', 'weekly', 'biweekly', 'monthly', 'manual']) {
    assert.ok(ladder[1].includes("'" + c + "'"), 'cadence ' + c + ' is not offered');
  }
});

/* ── how the row text is built ──────────────────────────────────────────────────────── */

const ROW_SRC = (() => {
  const start = SETTINGS_JS.indexOf('syncRows: SYNC_MODS.map(');
  assert.notStrictEqual(start, -1, 'syncRows not found');
  return SETTINGS_JS.slice(start, SETTINGS_JS.indexOf('}),', start));
})();

test('last run is success-anchored, so a failed attempt never reads as a run', () => {
  assert.ok(ROW_SRC.includes('info.last_success'), 'row does not read last_success');
  assert.ok(!ROW_SRC.includes('last_attempt'), 'row must not present an attempt as a run');
});

test('the past uses relTime and the future uses untilTime', () => {
  assert.ok(/relTime\(info\.last_success\)/.test(ROW_SRC), 'last run should use relTime');
  assert.ok(/untilTime\(info\.next_run\)/.test(ROW_SRC), 'next run must not use relTime');
  assert.ok(!/relTime\(info\.next_run\)/.test(ROW_SRC), 'relTime on a future date says "just now"');
});

test('a manual module is never described as due', () => {
  assert.ok(/cadence === 'manual'/.test(ROW_SRC), 'manual is not special-cased');
});

test('the cadence shown is the one the backend resolved, not the raw saved blob', () => {
  /* `syncCfg[key] || 'weekly'` was the old value. On a project that had never opened this
     tab it printed "Weekly" under a module the scheduler was running every 12 hours. */
  assert.ok(/info\.cadence \|\|/.test(ROW_SRC), 'row does not prefer the resolved cadence');
});
