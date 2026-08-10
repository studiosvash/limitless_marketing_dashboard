/* Tests for ptLocationChangeWarning — the confirm text shown before a project's tracking
   location changes.

   Run: node --test static/spa/tests/location_change_warning.test.js

   Same brace-matching extraction as listVisibility / buildVisibilityScores: the real function
   is cut out of the shipping positioning.js and evaluated, so a drifted copy cannot pass.

   WHY THIS EXISTS. `sites.location` is a filter, not a label: every positioning read narrows
   to the project's CURRENT location and every ranking row carries the location it was measured
   in. Changing it therefore makes 100% of the project's measured history unreadable in one
   click — Rankings Overview blanks, the whole tracked list drops into "Newly Added Keywords —
   Not Tracked Yet", and the next sync re-buys every keyword from DataForSEO. This was reported
   as "editing a project's location removed my tracked keywords". The rows are still there, so
   the warning must say both things: what is about to happen, and that changing it back undoes
   it. Cost is never asserted as $0.00 — per-keyword DataForSEO pricing is not known here, and
   a fabricated zero on a spend warning is the worst possible number to invent. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

function extractFn(marker, argNames) {
  const src = fs.readFileSync(
    path.join(__dirname, '..', 'src', 'js', 'pages', 'positioning.js'), 'utf8'
  );
  const start = src.indexOf(marker);
  assert.notStrictEqual(start, -1, marker + ' not found in positioning.js');
  let depth = 0, i = src.indexOf('{', start + marker.length - 1);
  const bodyStart = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  return new Function(...argNames, src.slice(bodyStart + 1, i));
}

const warn = extractFn('const ptLocationChangeWarning = (oldLoc, newLoc, kwCount) => {',
                       ['oldLoc', 'newLoc', 'kwCount']);

test('names both locations', () => {
  const t = warn('United States - New York', 'United States - Washington, DC', 12);
  assert.ok(t.includes('United States - New York'), t);
  assert.ok(t.includes('United States - Washington, DC'), t);
});

test('states that the existing rankings stay under the old location', () => {
  const t = warn('New York', 'Austin', 12).toLowerCase();
  assert.ok(t.includes('old location') || t.includes('new york'), t);
  assert.ok(t.includes("won't show") || t.includes('will not show'), t);
});

test('includes the tracked keyword count that will be re-measured', () => {
  assert.ok(warn('New York', 'Austin', 12).includes('12 tracked keywords'),
            'the user needs the size of the re-measurement they are authorising');
  assert.ok(warn('New York', 'Austin', 1).includes('1 tracked keyword'));
});

test('says the cost is unknown — never fabricates $0.00', () => {
  const t = warn('New York', 'Austin', 12);
  assert.ok(/cost unknown/i.test(t), t);
  assert.ok(!t.includes('$0.00'),
            'a fabricated zero on a spend warning is the worst number to invent');
  assert.ok(!/\$0\b/.test(t), t);
});

test('says changing it back restores the old series, because it does', () => {
  const t = warn('New York', 'Austin', 12).toLowerCase();
  assert.ok(t.includes('back'), t);
  assert.ok(t.includes('restor') || t.includes('reappear') || t.includes('return'), t);
});

test('a project with nothing tracked yet does not claim keywords will be re-measured', () => {
  const t = warn('New York', 'Austin', 0);
  assert.ok(!t.includes('0 tracked keyword'),
            'zero keywords is not a re-measurement warning; do not print a fake count');
});
