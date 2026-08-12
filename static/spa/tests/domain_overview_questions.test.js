/**
 * The AI Questions tab's view model, and the keyword columns that were being discarded.
 *
 * Two rules carried over from the backend, because a friendly-looking default in the UI undoes
 * an honest null in the service:
 *
 *   - a keyword with no difficulty on record renders as an em dash, never 0 and never green;
 *   - "cited" and "seen" are different findings and never collapse into one badge.
 */
/* `describe`/`it` are NOT globals under `node --test` — without this require the whole
   file threw ReferenceError before a single assertion ran, and a suite that collected
   zero tests looks exactly like a suite that passed (skills.md §9). */
const { describe, it } = require('node:test');
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'src', 'js', 'pages', 'domain_overview.js');

/* These live inside renderVals() and some of them call component helpers through `this`
   (`this.fmt`), so the extracted body is evaluated with a stand-in host rather than bare. */
const HOST = {
  fmt: (n) => (n === null || n === undefined) ? '' : Number(n).toLocaleString('en-US'),
};

function extractFn(name) {
  const src = fs.readFileSync(SRC, 'utf8');
  const marker = 'const ' + name + ' = ';
  const start = src.indexOf(marker);
  assert.ok(start !== -1, name + ' not found in domain_overview.js');
  let i = src.indexOf('{', start);
  let depth = 0;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  const body = src.slice(start + marker.length, i + 1);
  // The extracted value is an arrow function, and an arrow closes over `this` LEXICALLY — so
  // it is built inside a normal function invoked with HOST as the receiver, and `this.fmt`
  // inside it then resolves to the stand-in.
  return eval('(function () { return ' + body + '; }).call(HOST)');
}

describe('domain overview — keyword difficulty', () => {
  const kdView = extractFn('kdView');

  it('an unknown difficulty is a dash, not a zero', () => {
    assert.strictEqual(kdView(null).label, '—');
    assert.strictEqual(kdView(undefined).label, '—');
  });

  it('an unknown difficulty is not coloured as easy', () => {
    // Green on an unknown reads as "trivial to rank for" — the opposite of what we know.
    assert.notStrictEqual(kdView(null).color, kdView(5).color);
  });

  it('a real zero is shown as zero', () => {
    assert.strictEqual(kdView(0).label, '0');
  });

  it('bands run easy to hard', () => {
    const bands = [kdView(10).band, kdView(35).band, kdView(60).band, kdView(85).band];
    assert.deepStrictEqual(bands, ['easy', 'medium', 'hard', 'very hard']);
  });
});

describe('domain overview — rank movement', () => {
  const moveView = extractFn('moveView');

  it('unknown movement renders nothing rather than "flat"', () => {
    assert.strictEqual(moveView(null).show, false);
    assert.strictEqual(moveView(undefined).show, false);
  });

  it('each movement gets its own arrow', () => {
    assert.strictEqual(moveView('up').label, '▲');
    assert.strictEqual(moveView('down').label, '▼');
    assert.strictEqual(moveView('new').label, 'new');
    assert.strictEqual(moveView('lost').label, 'lost');
  });
});

describe('domain overview — sparkline', () => {
  const sparkPoints = extractFn('sparkPoints');

  it('a single month cannot draw a line and says so', () => {
    // The AI trend chart shipped with exactly this bug: (k / (len - 1)) is 0/0 = NaN, and an
    // SVG polyline carrying NaN draws nothing at all.
    assert.ok(!/NaN/.test(sparkPoints([5])));
  });

  it('no months at all is an empty string, not a broken path', () => {
    assert.strictEqual(sparkPoints([]), '');
    assert.strictEqual(sparkPoints(null), '');
  });

  it('twelve months produce twelve points', () => {
    const pts = sparkPoints([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
    assert.strictEqual(pts.split(' ').length, 12);
    assert.ok(!/NaN/.test(pts));
  });

  it('an all-zero series still draws along the baseline', () => {
    assert.ok(!/NaN/.test(sparkPoints([0, 0, 0])));
  });
});

describe('domain overview — AI questions', () => {
  const questionRows = extractFn('questionRows');

  const ROWS = [
    { question: 'how many bartenders for 50 guests?', ai_search_volume: 82, cited: true,
      retrieved: false, our_url: 'https://premierstaff.com/blog/x', platform: 'chat_gpt',
      monthly_searches: { '2026-07': 82, '2026-06': 85 }, answer: 'For 50 guests...',
      fan_out_queries: ['bartender ratio'], cited_domains: ['premierstaff.com'] },
    { question: 'who staffs events?', ai_search_volume: null, cited: false, retrieved: true,
      our_url: 'https://premierstaff.com/services', platform: 'google',
      monthly_searches: {}, answer: '', fan_out_queries: [], cited_domains: ['rival.com'] },
  ];

  it('cited and seen keep separate badges', () => {
    const rows = questionRows(ROWS);
    assert.strictEqual(rows[0].badge.label, 'Cited');
    assert.strictEqual(rows[1].badge.label, 'Seen');
    assert.notStrictEqual(rows[0].badge.color, rows[1].badge.color);
  });

  it('an unknown volume is a dash, never zero', () => {
    assert.strictEqual(questionRows(ROWS)[1].volume, '—');
  });

  it('the monthly map becomes an ordered series, oldest first', () => {
    assert.deepStrictEqual(questionRows(ROWS)[0].monthly, [85, 82]);
  });

  it('who was cited instead of us is surfaced', () => {
    assert.strictEqual(questionRows(ROWS)[1].citedInstead, 'rival.com');
    assert.strictEqual(questionRows(ROWS)[0].citedInstead, '');
  });

  it('an empty list yields no rows rather than throwing', () => {
    assert.deepStrictEqual(questionRows([]), []);
    assert.deepStrictEqual(questionRows(null), []);
  });
});
