/**
 * "Brand Mentions by Platform" renders blank on a real project (reported 2026-08-10).
 *
 * The live database has exactly ONE weekly snapshot (week_start 2026-07-27 — the LLM mentions
 * connector has only captured once). The x coordinate is
 *
 *     x = (k / (trend.length - 1)) * 590 + 5
 *
 * so with a single point that divisor is zero: 0/0 is NaN, every point becomes "NaN,y", and an
 * SVG polyline with a NaN coordinate draws NOTHING. The card renders as an empty box with
 * gridlines under a heading that says "last 12 weeks", which reads as "we measured and found
 * nothing" rather than "we have measured once so far".
 *
 * Two separate facts have to survive this: a single measurement is still a measurement and must
 * be VISIBLE, and the user must be told a trend needs a second week. Zero measurements is a
 * third, different state.
 */
/* `describe`/`it` are NOT globals under `node --test` — without this require the whole
   file threw ReferenceError before a single assertion ran, and a suite that collected
   zero tests looks exactly like a suite that passed (skills.md §9). */
const { describe, it } = require('node:test');
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'src', 'js', 'pages', 'ai_optimization.js');

/* The chart maths is inline in renderVals(), so it is extracted by brace matching the same way
   the other SPA tests do it. `buildTrend(trend, platforms, active)` is the seam. */
function extractFn(name) {
  const src = fs.readFileSync(SRC, 'utf8');
  const marker = 'const ' + name + ' = ';
  const start = src.indexOf(marker);
  assert.ok(start !== -1, name + ' not found in ai_optimization.js');
  let i = src.indexOf('{', start);
  let depth = 0;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  return eval('(' + src.slice(start + marker.length, i + 1) + ')');
}

const PLATFORMS = [
  { id: 'google', name: 'AI Overviews', color: '#4f46e5' },
  { id: 'chat_gpt', name: 'ChatGPT', color: '#10b981' },
];
const ACTIVE = { google: true, chat_gpt: true };

// Exactly what the live project holds: one week, one Google mention, zero ChatGPT.
const ONE_WEEK = [{ date: '2026-07-27', google: 1, chat_gpt: 0 }];
const TWO_WEEKS = [
  { date: '2026-07-27', google: 1, chat_gpt: 0 },
  { date: '2026-08-03', google: 3, chat_gpt: 2 },
];

const noNaN = s => assert.ok(!/NaN/.test(s), 'coordinates must never contain NaN: ' + s);

describe('AI mentions trend chart', () => {
  const buildTrend = extractFn('buildTrend');

  it('a single weekly measurement produces drawable coordinates', () => {
    const out = buildTrend(ONE_WEEK, PLATFORMS, ACTIVE);
    out.lines.forEach(l => noNaN(l.pts));
  });

  it('a single measurement is shown as a visible point, not an invisible line', () => {
    const out = buildTrend(ONE_WEEK, PLATFORMS, ACTIVE);
    // A one-point polyline draws nothing even with valid numbers -- there is no segment.
    // The series must therefore expose a dot for the renderer.
    const google = out.lines.find(l => l.color === '#4f46e5');
    assert.ok(google.dot, 'a lone measurement needs a dot to be visible at all');
    assert.ok(!/NaN/.test(String(google.dot.cx)) && !/NaN/.test(String(google.dot.cy)));
  });

  it('says a trend needs a second week instead of showing an empty box', () => {
    const out = buildTrend(ONE_WEEK, PLATFORMS, ACTIVE);
    assert.strictEqual(out.singlePoint, true);
    assert.match(out.note, /one weekly measurement|second week/i);
  });

  it('two or more weeks draw a real line and carry no note', () => {
    const out = buildTrend(TWO_WEEKS, PLATFORMS, ACTIVE);
    assert.strictEqual(out.singlePoint, false);
    assert.strictEqual(out.note, '');
    out.lines.forEach(l => {
      noNaN(l.pts);
      assert.strictEqual(l.pts.split(' ').length, 2, 'one coordinate pair per week');
    });
  });

  it('no measurements at all is its own state, not the single-week one', () => {
    const out = buildTrend([], PLATFORMS, ACTIVE);
    assert.strictEqual(out.lines.length, 0);
    assert.strictEqual(out.singlePoint, false);
    assert.match(out.note, /no weekly/i);
  });

  it('a deselected platform contributes no line', () => {
    const out = buildTrend(TWO_WEEKS, PLATFORMS, { google: true, chat_gpt: false });
    assert.strictEqual(out.lines.length, 1);
  });

  it('an all-zero series still draws along the baseline rather than vanishing', () => {
    const zeros = [{ date: 'a', google: 0, chat_gpt: 0 }, { date: 'b', google: 0, chat_gpt: 0 }];
    const out = buildTrend(zeros, PLATFORMS, ACTIVE);
    out.lines.forEach(l => noNaN(l.pts));
  });

  it('a missing platform key in a week counts as zero, not NaN', () => {
    // The connector omits a group_element entirely when the value is zero -- a documented
    // DataForSEO shape, so the week object legitimately lacks the key.
    const sparse = [{ date: 'a', google: 2 }, { date: 'b', chat_gpt: 1 }];
    const out = buildTrend(sparse, PLATFORMS, ACTIVE);
    out.lines.forEach(l => noNaN(l.pts));
  });
});
