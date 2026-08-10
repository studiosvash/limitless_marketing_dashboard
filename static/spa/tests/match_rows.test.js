/* Tests for the Keyword Explorer's tab + filter predicate.

   Run: node --test static/spa/tests/match_rows.test.js

   `matchRows` is read out of the shipping app.js by brace-matching, the same way
   sort_rows.test.js and page_window.test.js read theirs. Restating the predicate here would
   keep passing forever after the original drifted.

   WHY THIS EXISTS — two bugs, both of which put a wrong fact on screen:

   1. The Related tab filtered on `r.match === 'related'`, but `match` is a string-SHAPE
      classification and `related_keywords/live` returns Google's "searches related to",
      which almost always CONTAINS the seed. So every related row was shape-classified as
      `phrase` and the Related tab rendered empty over rows DataForSEO had returned and
      billed for. Which fetch produced a row is provenance (`sources`), not word shape.

   2. The volume-min filter read `r.volume >= s.resVolMin` while an unknown volume was being
      coerced to `0` upstream. Zero and unknown are different facts: an unknown-volume
      keyword is not a keyword with no searches, and silently dropping it from "101+" hides
      rows for a reason the reader cannot see. */

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

const matchRowsBody = extractMethod('matchRows', ['skipGroup']);

const BASE_STATE = {
  matchType: 'all', resVolMin: 0, resKdMin: 0, resKdMax: 100,
  resIntents: [], resIncl: '', resExcl: '', resGroup: null
};

function run(rows, overrides) {
  const state = Object.assign({}, BASE_STATE, { research: { rows: rows } }, overrides || {});
  return matchRowsBody.call({ state: state }, false).map(r => r.kw);
}

function row(kw, extra) {
  return Object.assign({ kw: kw, match: 'broad', volume: 100, kd: 10, intent: 'informational' },
                       extra || {});
}

/* ---------- 1. Related is provenance, not shape ---------- */

test('Related tab shows rows related_keywords returned, even when they contain the seed', () => {
  // DataForSEO's own documented example for seed "keyword research": every result contains it,
  // so every one of them shape-classifies as `phrase`.
  const rows = [
    row('free keyword research', { match: 'phrase', source: 'related', sources: ['related'] }),
    row('keyword research tools', { match: 'phrase', source: 'related', sources: ['related'] }),
    row('keyword research course', { match: 'phrase', source: 'ideas', sources: ['ideas'] })
  ];
  assert.deepStrictEqual(run(rows, { matchType: 'related' }),
                         ['free keyword research', 'keyword research tools']);
});

test('a keyword returned by both ideas and related is still on the Related tab', () => {
  const rows = [row('keyword research tools',
                    { match: 'phrase', source: 'ideas', sources: ['ideas', 'related'] })];
  assert.deepStrictEqual(run(rows, { matchType: 'related' }), ['keyword research tools']);
});

test('Related tab is empty when nothing carried related provenance', () => {
  const rows = [row('keyword research course', { match: 'phrase', source: 'ideas', sources: ['ideas'] })];
  assert.deepStrictEqual(run(rows, { matchType: 'related' }), []);
});

test('shape tabs still read `match`, unaffected by provenance', () => {
  const rows = [
    row('keyword research tools', { match: 'phrase', source: 'related', sources: ['related'] }),
    row('vitamin drip clinic', { match: 'broad', source: 'ideas', sources: ['ideas'] }),
    row('keyword research', { match: 'exact', source: 'ideas', sources: ['ideas'] }),
    row('how to do keyword research', { match: 'questions', source: 'questions', sources: ['questions'] })
  ];
  assert.deepStrictEqual(run(rows, { matchType: 'phrase' }),
                         ['keyword research tools', 'keyword research']);
  assert.deepStrictEqual(run(rows, { matchType: 'exact' }), ['keyword research']);
  assert.deepStrictEqual(run(rows, { matchType: 'questions' }), ['how to do keyword research']);
  assert.deepStrictEqual(run(rows, { matchType: 'broad' }).length, 3);
});

/* ---------- 2. Unknown volume is not zero volume ---------- */

test('volume-min excludes only rows with a KNOWN volume below the threshold', () => {
  const rows = [
    row('big', { volume: 5000 }),
    row('small', { volume: 20 }),
    row('unknown', { volume: null })
  ];
  assert.deepStrictEqual(run(rows, { resVolMin: 101 }), ['big', 'unknown']);
});

test('volume-min at Any keeps everything, unknowns included', () => {
  const rows = [row('a', { volume: null }), row('b', { volume: 0 })];
  assert.deepStrictEqual(run(rows, { resVolMin: 0 }), ['a', 'b']);
});

test('a genuine zero volume is still filtered out — zero is a measurement', () => {
  const rows = [row('zero', { volume: 0 }), row('unknown', { volume: null })];
  assert.deepStrictEqual(run(rows, { resVolMin: 101 }), ['unknown']);
});

test('a cached response from before `sources` existed still populates Related', () => {
  // localStorage holds past searches; a response saved under the old contract carries
  // match === 'related' and no provenance at all.
  const rows = [row('promo staff near me', { match: 'related' })];
  assert.deepStrictEqual(run(rows, { matchType: 'related' }), ['promo staff near me']);
});

