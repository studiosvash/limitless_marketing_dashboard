/* Tests for App.sortRows — the single comparator behind every sortable table in the SPA
   (Crawled Pages, Keywords, Campaigns, Search Terms, Referring domains).

   Run: node --test static/spa/tests/

   There is no bundler here: the SPA is string-concatenated from `#include` directives at
   request time (apps/dashboard/spa_views.py), and app.js is a class-body fragment that cannot
   be `require`d. So this test extracts the real `sortRows` method out of the shipping source by
   brace-matching and evaluates that — a copy of the function pasted here would pass forever
   after the original drifted.

   WHY THIS EXISTS: sortRows used to substitute -1 for a null value before comparing. -1 is
   lower than every real metric on this dashboard (scores 0-100, ms, counts, sessions), so any
   ascending sort put every UNMEASURED row above every measured one. On Site Audit -> Crawled
   Pages, which defaults to score-ascending and renders only the first 40 rows, that filled the
   whole visible table with "—" while 27 real Lighthouse scores sat below the fold — the page
   looked like it had no data at all. This module's convention is that null means "not
   measured", never a value; a comparator that ranks null as worse-than-zero breaks that
   convention the moment a user sorts. Unmeasured rows sink to the bottom in BOTH directions:
   they are not the best and not the worst, they are not results. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

function extractSortRows() {
  const src = fs.readFileSync(
    path.join(__dirname, '..', 'src', 'js', 'app.js'), 'utf8'
  );
  const start = src.indexOf('sortRows(rows, sort) {');
  assert.notStrictEqual(start, -1, 'sortRows(rows, sort) not found in app.js');
  let depth = 0, i = src.indexOf('{', start);
  const bodyStart = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  const body = src.slice(bodyStart + 1, i);
  return new Function('rows', 'sort', body);
}

const sortRows = extractSortRows();
const keys = rows => rows.map(r => r.k);

test('ascending: unmeasured rows sink to the bottom, not the top', () => {
  const rows = [
    { k: 'unmeasured-a', score: null },
    { k: 'worst', score: 46 },
    { k: 'unmeasured-b', score: null },
    { k: 'best', score: 88 },
  ];
  const out = sortRows(rows, { key: 'score', dir: 1 });
  assert.deepStrictEqual(keys(out), ['worst', 'best', 'unmeasured-a', 'unmeasured-b']);
});

test('descending: unmeasured rows still sink to the bottom', () => {
  const rows = [
    { k: 'unmeasured', score: null },
    { k: 'worst', score: 46 },
    { k: 'best', score: 88 },
  ];
  const out = sortRows(rows, { key: 'score', dir: -1 });
  assert.deepStrictEqual(keys(out), ['best', 'worst', 'unmeasured']);
});

test('a real 0 is a result and outranks unmeasured in both directions', () => {
  // The distinction the whole payload is built around: 0 in-links means an orphan page
  // (a finding), null means the crawler never reached it (not a finding).
  const rows = [{ k: 'null', inLinks: null }, { k: 'zero', inLinks: 0 }, { k: 'five', inLinks: 5 }];
  assert.deepStrictEqual(keys(sortRows(rows, { key: 'inLinks', dir: 1 })), ['zero', 'five', 'null']);
  assert.deepStrictEqual(keys(sortRows(rows, { key: 'inLinks', dir: -1 })), ['five', 'zero', 'null']);
});

test('undefined is treated as unmeasured too', () => {
  const rows = [{ k: 'missing' }, { k: 'ten', v: 10 }];
  assert.deepStrictEqual(keys(sortRows(rows, { key: 'v', dir: 1 })), ['ten', 'missing']);
});

test('string columns: empty/missing values sort last, present values stay alphabetical', () => {
  const rows = [{ k: 'blank', url: null }, { k: 'b', url: 'b.com' }, { k: 'a', url: 'a.com' }];
  assert.deepStrictEqual(keys(sortRows(rows, { key: 'url', dir: 1 })), ['a', 'b', 'blank']);
  assert.deepStrictEqual(keys(sortRows(rows, { key: 'url', dir: -1 })), ['b', 'a', 'blank']);
});

test('the input array is not mutated', () => {
  const rows = [{ k: 'b', v: 2 }, { k: 'a', v: 1 }];
  sortRows(rows, { key: 'v', dir: 1 });
  assert.deepStrictEqual(keys(rows), ['b', 'a']);
});

test('regression: a page with a real score is visible in the first 40 rows', () => {
  // The exact shape of the reported bug: 28 unmeasured + 27 measured pages, score ascending,
  // table renders rows.slice(0, 40). Before the fix the first real score was at index 28 and
  // the top of the table was 28 consecutive dashes.
  const rows = [];
  for (let i = 0; i < 28; i++) rows.push({ k: 'unmeasured-' + i, score: null });
  for (let i = 0; i < 27; i++) rows.push({ k: 'measured-' + i, score: 40 + i });
  const out = sortRows(rows, { key: 'score', dir: 1 });
  assert.strictEqual(out[0].score, 40, 'the lowest real score must be the first row');
  assert.strictEqual(
    out.slice(0, 40).filter(r => r.score != null).length, 27,
    'all 27 measured pages must fall inside the 40 rows the table renders'
  );
});
