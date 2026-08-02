/* Tests for the Crawled Pages table's pagination arithmetic.

   Run: node --test static/spa/tests/page_window.test.js

   `pageSlice` and `pageWindow` are read out of the shipping app.js by brace-matching, the same
   way sort_rows.test.js reads sortRows. Restating the maths here instead would keep passing
   forever after the original drifted, which is the one thing a test of arithmetic must not do.

   WHY THIS EXISTS: the table rendered `rows.slice(0, 40)` and told the reader to "export the
   full list" for the rest — on a 1 139-page site, 96% of an already-downloaded payload was
   unreachable in the UI. Paging is cheap. The two things worth pinning down are that the last
   page is not off by one, and that a stale page index is CLAMPED: an out-of-range slice renders
   an empty table, which reads as "nothing matched your filter" rather than "you are past the
   end of a list that just got shorter". */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

function extractMethod(name, argNames) {
  const src = fs.readFileSync(path.join(__dirname, '..', 'src', 'js', 'app.js'), 'utf8');
  const sig = name + '(' + argNames.join(', ') + ') {';
  const start = src.indexOf(sig);
  assert.notStrictEqual(start, -1, sig + ' not found in app.js');
  let i = src.indexOf('{', start), depth = 0;
  const bodyStart = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  return new Function(...argNames, src.slice(bodyStart + 1, i));
}

const pageSlice = extractMethod('pageSlice', ['total', 'requestedPage', 'size']);
const pageWindow = extractMethod('pageWindow', ['pageCount', 'pageIdx']);

const SIZE = 40;
const label = p => p.shown === 0 ? 'none' : (p.from + 1) + '-' + (p.from + p.shown);
// pageWindow returns 0-based indices and the string 'gap'; the UI renders n + 1.
const human = (count, idx) => pageWindow(count, idx).map(n => n === 'gap' ? '…' : n + 1);

test('a 55-page site paginates into two pages, the second one short', () => {
  const first = pageSlice(55, 0, SIZE);
  assert.deepStrictEqual(first, { pageCount: 2, pageIdx: 0, from: 0, shown: 40 });
  assert.strictEqual(label(first), '1-40');

  const second = pageSlice(55, 1, SIZE);
  assert.strictEqual(label(second), '41-55');
});

test('the page count is not off by one when the total is an exact multiple', () => {
  const p = pageSlice(80, 1, SIZE);
  assert.strictEqual(p.pageCount, 2, '80 rows is exactly 2 pages, not 3');
  assert.strictEqual(label(p), '41-80');
});

test('a stale page index is clamped to the last page, never rendered empty', () => {
  // The reader was on page 12 of an unfiltered 1 139-page list, then typed a filter matching 3.
  const p = pageSlice(3, 11, SIZE);
  assert.strictEqual(p.pageIdx, 0);
  assert.strictEqual(p.shown, 3, 'clamping must show the rows, not an empty table');
});

test('a negative or missing page index falls back to the first page', () => {
  assert.strictEqual(pageSlice(55, -4, SIZE).pageIdx, 0);
  assert.strictEqual(pageSlice(55, undefined, SIZE).pageIdx, 0);
});

test('an empty result set still yields exactly one page, showing nothing', () => {
  const p = pageSlice(0, 5, SIZE);
  assert.strictEqual(p.pageCount, 1);
  assert.strictEqual(p.shown, 0);
});

test('every row is reachable from some page, and none appears on two', () => {
  const total = 1139;                       // premierstaff.com
  const seen = new Set();
  for (let i = 0; i < pageSlice(total, 0, SIZE).pageCount; i++) {
    const p = pageSlice(total, i, SIZE);
    for (let r = p.from; r < p.from + p.shown; r++) {
      assert.ok(!seen.has(r), 'row ' + r + ' appeared on two pages');
      seen.add(r);
    }
  }
  assert.strictEqual(seen.size, total, 'every row must be reachable from some page');
});

test('the page-number window stays short and keeps both ends one click away', () => {
  assert.deepStrictEqual(human(2, 0), [1, 2]);
  assert.deepStrictEqual(human(29, 0), [1, 2, 3, 4, 5, 6, 7, '…', 29]);
  assert.deepStrictEqual(human(29, 14), [1, '…', 12, 13, 14, 15, 16, 17, 18, '…', 29]);
  assert.deepStrictEqual(human(29, 28), [1, '…', 23, 24, 25, 26, 27, 28, 29]);
  for (const idx of [0, 3, 14, 27, 28]) {
    const w = human(29, idx);
    assert.ok(w.includes(1) && w.includes(29), 'both ends must stay reachable at page ' + idx);
    assert.ok(w.filter(x => x !== '…').length <= 9, 'the window must not grow with page count');
  }
});

test('the current page is always inside the window', () => {
  for (const count of [2, 8, 29, 285]) {
    for (const idx of [0, 1, Math.floor(count / 2), count - 2, count - 1]) {
      if (idx < 0) continue;
      assert.ok(human(count, idx).includes(idx + 1),
        'page ' + (idx + 1) + ' of ' + count + ' is not in its own window');
    }
  }
});

test('a single page of results shows no navigation at all', () => {
  assert.deepStrictEqual(pageWindow(1, 0), []);
});
