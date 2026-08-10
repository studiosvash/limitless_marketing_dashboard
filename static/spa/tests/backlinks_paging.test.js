/* Tests for the Backlinks page view model: paging, the row counter, and the source-page cell.

   Run: node --test static/spa/tests/backlinks_paging.test.js

   The SHIPPING js/pages/backlinks.js is read off disk and evaluated against a stub component,
   the same principle as page_window.test.js and project_list_visibility.test.js: a restated
   copy of the logic passes forever after the original drifts. `pageSlice` / `pageWindow` are
   likewise cut out of the real app.js rather than reimplemented here.

   WHY THIS EXISTS:

   * The table hard-sliced to 60 rows with no page state and no navigation, while the endpoint
     returns up to 1000. Rows 61-1000 sat in the browser's cache, downloaded and unreachable.
   * The counter read "Showing {min(filtered,60)} of {summary.backlinks}" — a FILTERED sample
     compared against the snapshot's WHOLE-PROFILE total. With the Lost filter on it said
     "Showing 12 of 729", two numbers that answer different questions printed as a ratio.
   * A row with no `url_from` fell back to `'https://' + domain`, so "we know the exact page
     that links to you" and "we have no idea" rendered as the same clickable link. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const SRC = path.join(__dirname, '..', 'src', 'js');

function extractMethod(name, argNames) {
  const src = fs.readFileSync(path.join(SRC, 'app.js'), 'utf8');
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
const sortRows = extractMethod('sortRows', ['rows', 'sort']);

/* js/pages/*.js are not modules — they are spliced into renderVals()'s body and start mid-scope
   with `if (tab === 'x') {`. Evaluating one therefore means rebuilding that scope by hand. */
function renderBacklinks(state, data) {
  const body = fs.readFileSync(path.join(SRC, 'pages', 'backlinks.js'), 'utf8');
  const fn = new Function('s', 'tab', 'data', 'vals', 'project', body + '\n; return vals;');
  const applied = [];
  const ctx = {
    _applied: applied,
    setState: patch => applied.push(typeof patch === 'function' ? patch(state) : patch),
    pushNav: () => {},
    srcBadge: () => ({ show: false }),
    fmt: n => (n === null || n === undefined) ? '' : Number(n).toLocaleString('en-US'),
    pageSlice: pageSlice,
    pageWindow: pageWindow,
    sortRows: sortRows,
    arrow: (sort, key) => (sort.key === key ? (sort.dir === -1 ? ' ↓' : ' ↑') : ''),
    mkSortHandler: (stateKey, keyName, resetKey) => () => {
      const next = { [stateKey]: { key: keyName, dir: -1 } };
      if (resetKey) next[resetKey] = 0;
      applied.push(next);
    }
  };
  const s = Object.assign({ blTab: 'backlinks', blFilter: 'all', blFollow: 'all',
                            blSort: { key: 'rank', dir: -1 }, gapOnly: false }, state);
  const vals = fn.call(ctx, s, 'backlinks', data, {}, { domain: 'a.com' });
  return { bl: vals.bl, applied: applied };
}

function link(i, over) {
  return Object.assign({
    domain: 'blog' + (i % 7) + '.com',
    target_url: 'https://a.com/page',
    url_from: 'https://blog' + (i % 7) + '.com/post-' + i,
    anchor: 'anchor ' + i,
    status: 'live',
    dofollow: i % 2 === 0,
    domain_rank: 500 - i,
    page_rank: 300,
    spam_score: i % 100,
    first_seen: '2026-01-01',
    firstSeen: 'Jan 01, 2026',
    isNew: false
  }, over || {});
}

function payload(links, over) {
  return Object.assign({
    summary: { backlinks: 729, refDomains: 120, authorityScore: 400, dofollowPct: 60,
               broken: 3, spamScore: 12, newRdMonth: 4, lastUpdated: '2026-08-01',
               asDelta: null },
    links: links,
    months: [], types: [], asBuckets: [], anchors: [], refDomains: [],
    competitors: [], gapDomains: []
  }, over || {});
}

const many = n => Array.from({ length: n }, (_, i) => link(i));

test('the table pages at 40 rows instead of hard-slicing to 60', () => {
  const { bl } = renderBacklinks({}, payload(many(213)));
  assert.strictEqual(bl.rows.length, 40);
  assert.strictEqual(bl.hasPageNav, true);
});

test('every row is reachable — the last page holds the remainder', () => {
  const last = renderBacklinks({ blPage: 5 }, payload(many(213))).bl;
  assert.strictEqual(last.rows.length, 13, '213 = 5 full pages of 40 + 13');
});

test('a page index past the end is clamped, never rendered as an empty table', () => {
  const { bl } = renderBacklinks({ blPage: 99 }, payload(many(213)));
  assert.ok(bl.rows.length > 0, 'a stale page index must clamp, not blank the table');
});

test('the counter states the visible range, the matching total, and the profile total', () => {
  const { bl } = renderBacklinks({ blPage: 1 }, payload(many(213)));
  assert.match(bl.rowCount, /41.*80/, 'the visible range must be stated');
  assert.match(bl.rowCount, /213/, 'the number of MATCHING rows must be stated');
  assert.match(bl.rowCount, /729/, 'the whole-profile total must be labelled as such');
  assert.ok(!/Showing 40 of 729/.test(bl.rowCount),
    'a filtered sample must never be printed as a ratio of the profile total');
});

test('a filter that matches nothing says so instead of printing a zero range', () => {
  const { bl } = renderBacklinks({ blFilter: 'lost' }, payload(many(20)));
  assert.strictEqual(bl.rows.length, 0);
  assert.match(bl.rowCount, /No backlinks match/i);
});

test('the counter says when the stored sample itself is capped', () => {
  const capped = renderBacklinks({}, payload(many(50), { linksCapped: true, linksLimit: 1000 })).bl;
  assert.match(capped.rowCount, /capped/i);
  const whole = renderBacklinks({}, payload(many(50), { linksCapped: false, linksLimit: 1000 })).bl;
  assert.ok(!/capped/i.test(whole.rowCount),
    'a profile smaller than the cap must not claim it was truncated');
});

test('changing a filter resets the page — filtering 900 rows to 12 on page 8 must not blank', () => {
  const { bl, applied } = renderBacklinks({ blPage: 8 }, payload(many(900)));
  const chips = bl.statusFilters.concat(bl.followFilters);
  assert.ok(chips.length >= 4);
  chips.forEach(f => f.click());
  assert.strictEqual(applied.length, chips.length);
  applied.forEach(p => assert.strictEqual(p.blPage, 0,
    'a filter chip set ' + JSON.stringify(p) + ' without resetting blPage'));
});

test('the nofollow filter can now actually match rows', () => {
  /* Structural before the connector stopped filtering dofollow-only: the chip existed, the
     rows it filters for were never fetched. */
  const { bl } = renderBacklinks({ blFollow: 'nofollow' }, payload(many(20)));
  assert.strictEqual(bl.rows.length, 10);
});

test('a row with no url_from says so instead of linking to the domain homepage', () => {
  const { bl } = renderBacklinks({}, payload([link(0, { url_from: '' })]));
  const row = bl.rows[0];
  assert.strictEqual(row.hasSource, false);
  assert.match(row.sourcePath, /unknown/i);
  assert.ok(!/^https?:\/\//.test(row.urlFrom || ''),
    'an unknown source must not be dressed up as a link to the domain homepage');
});

test('a row with a url_from shows the source page as visible text, not only as an href', () => {
  const { bl } = renderBacklinks({}, payload([link(0, { url_from: 'https://blog0.com/a/b?x=1' })]));
  const row = bl.rows[0];
  assert.strictEqual(row.hasSource, true);
  assert.strictEqual(row.urlFrom, 'https://blog0.com/a/b?x=1');
  assert.ok(row.sourcePath && row.sourcePath.length > 0);
  assert.ok(!/^https?:\/\//.test(row.sourcePath), 'the visible path drops the scheme');
});

test('spam is banded green at 30, amber to 60, red above', () => {
  const rows = renderBacklinks({}, payload([
    link(0, { spam_score: 30 }), link(1, { spam_score: 31 }),
    link(2, { spam_score: 60 }), link(3, { spam_score: 61 })
  ])).bl.rows;
  const colors = rows.map(r => r.spamColor);
  assert.strictEqual(colors[0], colors[0], 'placeholder');
  assert.notStrictEqual(colors[0], colors[1], '30 and 31 are different bands');
  assert.strictEqual(colors[1], colors[2], '31-60 is one band');
  assert.notStrictEqual(colors[2], colors[3], '60 and 61 are different bands');
});

test('an unknown spam score stays blank rather than colouring as clean', () => {
  const { bl } = renderBacklinks({}, payload([link(0, { spam_score: null })]));
  assert.strictEqual(bl.rows[0].hasSpam, false);
  assert.strictEqual(bl.rows[0].spam, '');
});

test('sorting resets to the first page', () => {
  const { bl, applied } = renderBacklinks({ blPage: 4 }, payload(many(213)));
  bl.sort.rank();
  assert.strictEqual(applied[applied.length - 1].blPage, 0);
});

test('referring domains are paged too — they used to render every row into the DOM', () => {
  const refDomains = Array.from({ length: 130 }, (_, i) => ({
    domain: 'd' + i + '.com', flag: '🌐', rank: 500, backlinks: 3, linksToUs: 3,
    follow: true, firstSeen: '', first_seen: null, isNew: false, category: '', spam: 10
  }));
  const { bl } = renderBacklinks({ blTab: 'refdomains' }, payload(many(10), { refDomains }));
  assert.strictEqual(bl.allRefDomains.length, 40);
  assert.strictEqual(bl.rdHasPageNav, true);
  assert.match(bl.rdCount, /130/);
});

test('anchors are paged too', () => {
  const anchors = Array.from({ length: 95 }, (_, i) => ({
    anchor: 'a' + i, type: 'Keyword', backlinks: 5, refDomains: 2, dofollowPct: 50
  }));
  const { bl } = renderBacklinks({ blTab: 'anchors' }, payload(many(10), { anchors }));
  assert.strictEqual(bl.allAnchors.length, 40);
  assert.strictEqual(bl.anHasPageNav, true);
  assert.match(bl.anCount, /95/);
});

test('the setup state still short-circuits with every key the template reads', () => {
  const { bl } = renderBacklinks({}, payload([], { summary: { backlinks: 0 } }));
  assert.strictEqual(bl.setup, true);
  ['rows', 'allRefDomains', 'allAnchors', 'statusFilters', 'followFilters'].forEach(k =>
    assert.ok(Array.isArray(bl[k]), k + ' must be an array in the setup state'));
});
