/* Tests for listVisibility — the projects LIST row's visibility cell.

   Run: node --test static/spa/tests/

   Same brace-matching extraction as visibility_scores.test.js: the real function is cut out
   of the shipping positioning.js and evaluated, so a drifted copy cannot silently pass.

   WHY THIS EXISTS: the list used to derive visibility from avg_position with a linear
   (100 - pos) / 1.2 formula. avg_position is averaged over ranked keywords only, so a
   project ranking on 1 of its 48 tracked keywords (the brand name, position 2.2) displayed
   82% — while the Semrush-style CTR-weighted reading of the same data is ~1%. The cell now
   renders the backend's `visibility` field (same CTR curve as buildVisibilityScores, every
   tracked keyword in the denominator) and must never reconstruct a score from avg_position. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

function extractListVisibility() {
  const src = fs.readFileSync(
    path.join(__dirname, '..', 'src', 'js', 'pages', 'positioning.js'), 'utf8'
  );
  const marker = 'const listVisibility = p => {';
  const start = src.indexOf(marker);
  assert.notStrictEqual(start, -1, 'listVisibility not found in positioning.js');
  let depth = 0, i = src.indexOf('{', start + marker.length - 1);
  const bodyStart = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  const body = src.slice(bodyStart + 1, i);
  return new Function('p', body);
}

const listVisibility = extractListVisibility();

test('renders the backend score, not anything derived from avg_position', () => {
  /* The 82% regression pinned: avg_position 2.2 arrives alongside a real CTR-weighted
     1.1 — the cell must show 1.1%, and the old formula would have shown 82%. */
  const out = listVisibility({ visibility: 1.1, avg_position: 2.2 });
  assert.strictEqual(out.label, '1.1%');
  assert.strictEqual(out.hasVis, true);
});

test('null visibility renders an em dash', () => {
  const out = listVisibility({ visibility: null, avg_position: 2.2 });
  assert.strictEqual(out.label, '—');
  assert.strictEqual(out.hasVis, false);
});

test('a payload without the field (cached SPA against an old API) degrades to em dash', () => {
  const out = listVisibility({ avg_position: 12 });
  assert.strictEqual(out.label, '—');
  assert.strictEqual(out.hasVis, false);
});

test('a real zero is shown as 0%, not hidden as missing', () => {
  const out = listVisibility({ visibility: 0 });
  assert.strictEqual(out.label, '0%');
  assert.strictEqual(out.hasVis, true);
});

test('whole numbers drop the decimal, fractional keep one', () => {
  assert.strictEqual(listVisibility({ visibility: 25 }).label, '25%');
  assert.strictEqual(listVisibility({ visibility: 100 }).label, '100%');
  assert.strictEqual(listVisibility({ visibility: 5.7 }).label, '5.7%');
});

/* THE BAR NEVER EXISTED ON SCREEN. positioning.html rendered the fill as an inline
   <span>, and CSS gives a non-replaced inline box no width and no height — so every
   barWidth this function computed was applied to a box that could not use it, from the
   day the column shipped. The track and fill are gone and so is barWidth; the coloured
   percentage is the whole cell. Pinned here so nobody reinstates the arithmetic for a
   bar that isn't there. */
test('no bar geometry is computed — the cell is the percentage', () => {
  ['barWidth', 'visBarStyle'].forEach(k => {
    assert.strictEqual(listVisibility({ visibility: 0.4 })[k], undefined,
      k + ' is back; the fill span it fed was an inline box and never rendered');
  });
});
