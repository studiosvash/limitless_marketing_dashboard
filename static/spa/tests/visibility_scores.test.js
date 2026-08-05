/* Tests for buildVisibilityScores — the Positioning Overview's per-domain scoring:
   share of voice (primary, % of the tracked field, sums to 100) plus the absolute
   visibility index (100 = #1 on every tracked keyword) on the sub-line.

   Run: node --test static/spa/tests/

   Same extraction approach as sort_rows.test.js: the SPA has no bundler (fragments are
   string-concatenated by apps/dashboard/spa_views.py), so the real function is cut out of
   the shipping source by brace-matching and evaluated. A pasted copy would pass forever
   after the original drifted.

   WHY THIS EXISTS: the Overview cards used to show ONLY the absolute index, and on real
   projects the strongest domain read "9.0" — true (it ranked on 7/24 keywords, avg #8)
   but unreadable next to Semrush's competitive percentages. The 2026-08-05 direction is a
   two-part reading: a market-share-style % relative to the competitors actually shown,
   with the absolute index kept underneath so a field of weak boards splitting 100% is
   still visibly weak. The share MUST come from the same CTR-curve points as the index,
   and the earlier sins must not return: no linear (100-pos)/100 credit, no volume
   weighting, no invented positions. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

function extractBuilder() {
  const src = fs.readFileSync(
    path.join(__dirname, '..', 'src', 'js', 'pages', 'positioning.js'), 'utf8'
  );
  const marker = 'const buildVisibilityScores = (domains, rows) => {';
  const start = src.indexOf(marker);
  assert.notStrictEqual(start, -1, 'buildVisibilityScores not found in positioning.js');
  let depth = 0, i = src.indexOf('{', start + marker.length - 1);
  const bodyStart = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  const body = src.slice(bodyStart + 1, i);
  return new Function('domains', 'rows', body);
}

const build = extractBuilder();

/* Row shape mirrors /api/positions competitors.rows: index 0 of `domains` is "you"
   (read from r.you.pos), every other domain is matched inside r.comps by name. */
function row(youPos, comps) {
  return {
    you: youPos != null ? { pos: youPos } : null,
    comps: Object.keys(comps || {}).map(d => ({ domain: d, pos: comps[d] }))
  };
}

test('share of voice sums to 100 across measured domains', () => {
  const rows = [
    row(1, { 'b.com': 3, 'c.com': 8 }),
    row(5, { 'b.com': 2, 'c.com': null }),
    row(12, { 'b.com': null, 'c.com': 4 })
  ];
  const out = build(['a.com', 'b.com', 'c.com'], rows);
  const total = out.reduce((t, d) => t + d.sov, 0);
  assert.ok(Math.abs(total - 100) < 1e-9, 'expected 100, got ' + total);
});

test('#1 on every keyword scores index exactly 100', () => {
  const rows = [row(1, { 'b.com': 5 }), row(1, { 'b.com': 9 })];
  const out = build(['a.com', 'b.com'], rows);
  assert.strictEqual(out[0].visScore, 100);
});

test('ranking nowhere scores index 0 and share 0 when rivals rank', () => {
  const rows = [row(null, { 'b.com': 1 }), row(null, { 'b.com': 2 })];
  const out = build(['a.com', 'b.com'], rows);
  assert.strictEqual(out[0].visScore, 0);
  assert.strictEqual(out[0].sov, 0);
  assert.strictEqual(out[0].rankedCount, 0);
});

test('no captured rows at all yields null, not a number', () => {
  const out = build(['a.com', 'b.com'], []);
  out.forEach(d => {
    assert.strictEqual(d.visScore, null);
    assert.strictEqual(d.sov, null);
  });
});

test('nobody ranks anywhere: index is a real 0, share is null (undefined split)', () => {
  const rows = [row(null, { 'b.com': null })];
  const out = build(['a.com', 'b.com'], rows);
  out.forEach(d => {
    assert.strictEqual(d.visScore, 0);
    assert.strictEqual(d.sov, null);
  });
});

test('better positions earn a larger share (CTR curve, not linear)', () => {
  const rows = [row(1, { 'b.com': 10 }), row(1, { 'b.com': 10 })];
  const out = build(['a.com', 'b.com'], rows);
  assert.ok(out[0].sov > out[1].sov);
  /* #1 vs #10 on the curve is 31.7 vs 1.8 — the share gap must reflect that,
     not the linear (100-1) vs (100-10) which would give a near-even split. */
  assert.ok(out[0].sov > 90, 'a.com share should dominate, got ' + out[0].sov);
});

test('deep positions past #20 earn almost nothing, past #100 nothing', () => {
  const rows = [row(45, { 'b.com': 101 })];
  const out = build(['a.com', 'b.com'], rows);
  assert.ok(out[0].earned > 0 && out[0].earned <= 0.05);
  assert.strictEqual(out[1].earned, 0);
  /* pos 101 is out of range: no credit, but it was still a captured measurement,
     so it must count as ranked=0 (not crash) */
  assert.strictEqual(out[1].rankedCount, 1);
});

test('avg position and coverage are reported per domain', () => {
  const rows = [row(2, { 'b.com': 4 }), row(6, { 'b.com': null }), row(null, { 'b.com': null })];
  const out = build(['a.com', 'b.com'], rows);
  assert.strictEqual(out[0].rankedCount, 2);
  assert.strictEqual(out[0].avgPos, 4); // (2+6)/2
  assert.strictEqual(out[1].rankedCount, 1);
  assert.strictEqual(out[1].avgPos, 4);
});
