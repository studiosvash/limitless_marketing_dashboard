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
   and the earlier sins must not return: no linear (100-pos)/100 credit, no invented
   positions.

   VOLUME WEIGHTING (decision 2026-08-13, tech lead: match Semrush exactly): the SHARE is
   now weighted by each keyword's search volume (`r.vol`), because that is Semrush's own
   Share of Voice definition — being #1 on a 1,000-search keyword is worth 100x being #1
   on a 10-search keyword. The INDEX stays equal-weight (that matches Semrush's
   Visibility, which weights keywords equally). A keyword with unknown/zero volume weighs
   1, so rows without volume data degrade to the old equal-weight behaviour instead of
   vanishing from the field. */

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
   (read from r.you.pos), every other domain is matched inside r.comps by name.
   `vol` is the keyword's search volume, mapped in from data.rankings at the call site —
   absent/0 means "no volume on record" and weighs 1. */
function row(youPos, comps, vol) {
  return {
    you: youPos != null ? { pos: youPos } : null,
    comps: Object.keys(comps || {}).map(d => ({ domain: d, pos: comps[d] })),
    vol: vol
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

test('share of voice is volume-weighted, Semrush-style', () => {
  /* a.com is #1 on the 1,000-search keyword and #10 on the 10-search one; b.com is the
     mirror image. Equal weighting would split the field 50/50 — volume weighting must
     hand a.com nearly everything: 1000x31.7 + 10x1.8 = 31,718 vs 1000x1.8 + 10x31.7 =
     2,117 -> ~93.7% / ~6.3%. */
  const rows = [
    row(1, { 'b.com': 10 }, 1000),
    row(10, { 'b.com': 1 }, 10)
  ];
  const out = build(['a.com', 'b.com'], rows);
  assert.ok(out[0].sov > 90, 'volume must dominate the split, got ' + out[0].sov);
  assert.ok(out[1].sov < 10, 'the low-volume #1 earns a small share, got ' + out[1].sov);
  const total = out.reduce((t, d) => t + d.sov, 0);
  assert.ok(Math.abs(total - 100) < 1e-9, 'weighted shares must still sum to 100');
});

test('the index ignores volume — it matches Semrush Visibility, which weights equally', () => {
  const flat = build(['a.com', 'b.com'], [row(1, { 'b.com': 10 }), row(10, { 'b.com': 1 })]);
  const weighted = build(['a.com', 'b.com'],
    [row(1, { 'b.com': 10 }, 1000), row(10, { 'b.com': 1 }, 10)]);
  assert.strictEqual(weighted[0].visScore, flat[0].visScore,
    'volume must move the share, never the absolute index');
});

test('rows without volume fall back to equal weight, not to vanishing', () => {
  /* No `vol` anywhere (an unpriced keyword list): every weight is 1, so the share must be
     exactly the pre-weighting behaviour — not 0/NaN and not a division by zero. */
  const rows = [row(1, { 'b.com': 10 }), row(10, { 'b.com': 1 })];
  const out = build(['a.com', 'b.com'], rows);
  assert.ok(Math.abs(out[0].sov - 50) < 1e-9, 'symmetric field with no volumes splits evenly, got ' + out[0].sov);
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

test('fractional average positions score real numbers, never NaN', () => {
  /* Regression: /api/positions reports 1-dp average positions (8.4, 24.5 — every service
     rounds to 1 dp), and the credit lookup indexed the CTR curve with them raw:
     CTR_CURVE[8.4 - 1] is undefined, one undefined poisoned the whole earned sum, and the
     Overview card printed "index NaN · 20/28 keywords · avg #25" on real projects. The
     curve is defined at whole positions, so a fractional position rounds to the nearest. */
  const rows = [
    row(8.4, { 'b.com': 3.6 }),
    row(24.5, { 'b.com': null }),
    row(1.2, { 'b.com': 19.5 })
  ];
  const out = build(['a.com', 'b.com'], rows);
  for (const d of out) {
    assert.ok(Number.isFinite(d.visScore), d.dom + ' visScore must be finite, got ' + d.visScore);
    assert.ok(Number.isFinite(d.sov), d.dom + ' sov must be finite, got ' + d.sov);
  }
  /* 8.4 rounds to #8 (credit 3.5), not down to #8.4-floor-by-accident: check the exact
     earned points so the rounding rule itself is pinned. 8.4→#8=3.5, 24.5→#25(wait, rounds
     to 24 or 25? Math.round(24.5)=25)=0.05, 1.2→#1=31.7. */
  assert.ok(Math.abs(out[0].earned - (3.5 + 0.05 + 31.7)) < 1e-9,
            'expected exact rounded-curve credit, got ' + out[0].earned);
});
