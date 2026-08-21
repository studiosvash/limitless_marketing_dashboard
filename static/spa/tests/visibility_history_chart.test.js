/* Tests for buildHistoryChart — the Positioning → Overview visibility trend line.

   Run: node --test static/spa/tests/

   Same brace-matching extraction as visibility_scores.test.js and
   project_list_visibility.test.js: the real function is cut out of the shipping
   positioning.js and evaluated, so a drifted copy cannot silently pass.

   WHY THIS EXISTS: this card had `hasHistory: false` and `series: []` written into the
   source as literals, so "No visibility history yet" was the ONLY reachable state of the
   chart whatever the database held — and before that the six points per domain came from
   Math.random(), which re-rolled the "trend" on every render. `hasHistory` must now be an
   OUTCOME of the data: two distinct capture dates draw a line, one does not. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

function extract(marker, argNames) {
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

const buildHistoryChart = extract('const buildHistoryChart = (hist, hidden, colorOf) => {',
                                  ['hist', 'hidden', 'colorOf']);

const COLOR = d => ({ 'premierstaff.com': '#4f46e5', 'eventstaff.com': '#a855f7' }[d] || '#000');

const TWO_DATES = {
  dates: ['2026-08-01', '2026-08-08'],
  series: [{ domain: 'premierstaff.com', own: true, points: [10.9, 21.6] }],
  tracked_total: 3
};

test('two capture dates draw a line', () => {
  const out = buildHistoryChart(TWO_DATES, [], COLOR);
  assert.strictEqual(out.hasHistory, true);
  assert.strictEqual(out.chart.series.length, 1);
  assert.strictEqual(out.chart.series[0].color, '#4f46e5');
});

test('one capture date is not a trend', () => {
  const out = buildHistoryChart(
    { dates: ['2026-08-08'], series: [{ domain: 'premierstaff.com', points: [21.6] }] },
    [], COLOR);
  assert.strictEqual(out.hasHistory, false,
    'a single-point polyline renders as nothing — the empty state is the honest answer');
});

test('no history at all, and a missing field, both fall to the empty state', () => {
  assert.strictEqual(buildHistoryChart({ dates: [], series: [] }, [], COLOR).hasHistory, false);
  assert.strictEqual(buildHistoryChart(undefined, [], COLOR).hasHistory, false);
});

test('points span the full plot area, oldest at the left', () => {
  const out = buildHistoryChart(TWO_DATES, [], COLOR);
  const [first, last] = out.chart.series[0].points.split(' ');
  assert.strictEqual(first.split(',')[0], '50.0');
  assert.strictEqual(last.split(',')[0], '700.0');
  /* Higher visibility is a HIGHER point on screen: y decreases as the value rises. */
  assert.ok(parseFloat(last.split(',')[1]) < parseFloat(first.split(',')[1]));
});

test('the dot marks the most recent reading', () => {
  const out = buildHistoryChart(TWO_DATES, [], COLOR);
  const pts = out.chart.series[0].points.split(' ');
  const [x, y] = pts[pts.length - 1].split(',');
  assert.strictEqual(out.chart.series[0].dotX, x);
  assert.strictEqual(out.chart.series[0].dotY, y);
});

/* THE AXIS MUST FOLLOW THE DATA. These indices are routinely under 5 ("index 3.6" is a real
   reading from a live project), and the template's original fixed 0–80 axis squashed every
   one of them into the bottom two pixels of the plot — a line that is technically drawn and
   practically unreadable. */
test('the y axis scales to the data instead of a fixed 0-80', () => {
  const small = buildHistoryChart({
    dates: ['2026-08-01', '2026-08-08'],
    series: [{ domain: 'premierstaff.com', points: [2.9, 3.6] }]
  }, [], COLOR);
  const top = parseFloat(small.chart.grid[0].label);
  assert.ok(top <= 5, 'a 3.6 peak must not be plotted against an 80 ceiling, got ' + top);
  // '0%' not '0' since 2026-08-21: the y labels carry the unit (Semrush-style axes).
  assert.strictEqual(small.chart.grid[small.chart.grid.length - 1].label, '0%',
    'the axis still starts at zero — a truncated baseline exaggerates every movement');
});

test('a null point is skipped, not drawn as zero', () => {
  const out = buildHistoryChart({
    dates: ['2026-08-01', '2026-08-08', '2026-08-15'],
    series: [{ domain: 'eventstaff.com', points: [null, 5, 8] }]
  }, [], COLOR);
  const pts = out.chart.series[0].points.split(' ');
  assert.strictEqual(pts.length, 2, 'the unmeasured date contributes no vertex');
  assert.notStrictEqual(pts[0].split(',')[0], '50.0',
    'the line starts at the first date that was actually measured, not at the axis');
});

test('a series with nothing but nulls is dropped rather than drawn flat', () => {
  const out = buildHistoryChart({
    dates: ['2026-08-01', '2026-08-08'],
    series: [{ domain: 'premierstaff.com', points: [10.9, 21.6] },
             { domain: 'eventstaff.com', points: [null, null] }]
  }, [], COLOR);
  assert.strictEqual(out.chart.series.length, 1);
});

test('legend toggles remove a domain from the chart', () => {
  const both = {
    dates: ['2026-08-01', '2026-08-08'],
    series: [{ domain: 'premierstaff.com', points: [10.9, 21.6] },
             { domain: 'eventstaff.com', points: [4.0, 6.0] }]
  };
  assert.strictEqual(buildHistoryChart(both, [], COLOR).chart.series.length, 2);
  assert.strictEqual(buildHistoryChart(both, ['eventstaff.com'], COLOR).chart.series.length, 1);
  assert.strictEqual(
    buildHistoryChart(both, ['premierstaff.com', 'eventstaff.com'], COLOR).hasHistory, false,
    'hiding every domain leaves nothing to plot');
});

/* The x labels were hardcoded Feb–Jul month names when the data was random. They are real
   dates now, and a 90-day window must not overprint its own axis. */
test('x labels are the real capture dates, capped so they stay legible', () => {
  const out = buildHistoryChart(TWO_DATES, [], COLOR);
  assert.deepStrictEqual(out.chart.xTicks.map(t => t.label), ['Aug 1', 'Aug 8']);

  const dates = [];
  for (let d = 1; d <= 28; d++) dates.push('2026-06-' + String(d).padStart(2, '0'));
  const many = buildHistoryChart(
    { dates: dates, series: [{ domain: 'premierstaff.com', points: dates.map((_, i) => i) }] },
    [], COLOR);
  assert.ok(many.chart.xTicks.length <= 7, 'got ' + many.chart.xTicks.length + ' labels');
  assert.strictEqual(many.chart.xTicks[0].label, 'Jun 1');
  assert.strictEqual(many.chart.xTicks[many.chart.xTicks.length - 1].label, 'Jun 28',
    'the newest date is always labelled — it is the one the user is reading');
});
