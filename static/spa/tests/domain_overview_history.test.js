/* Tests for the Domain Overview localStorage search history.

   Run: node --test static/spa/tests/domain_overview_history.test.js

   The methods are read out of the shipping app.js by brace-matching, the same way
   match_rows.test.js and sort_rows.test.js read theirs. Restating them here would keep
   passing forever after the originals drifted.

   WHY THIS EXISTS — this history is not a convenience feature, it is a SPEND control. Every
   Analyze press is a billed DataForSEO Labs call, and the server-side 24h cache runs on
   Django's default LocMemCache: per process, lost on restart, not shared between gunicorn
   workers. So localStorage is the only cache that reliably holds. Three properties have to
   stay true or the feature either costs money it promised not to, or loses data:

   1. A fresh entry restores WITHOUT a network call; a stale one must fall through to a real
      lookup. Get this backwards and the page shows day-old numbers as current.
   2. Re-analysing the same (domain, market) replaces its entry rather than appending, or ten
      slots fill with one domain and the history is useless.
   3. A quota failure sheds the oldest entries instead of throwing. These payloads are whole
      lookup responses, so quota exhaustion is a real outcome, and an exception thrown inside
      setState takes the render down. */

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

const blId = extractMethod('doBlCacheId', ['target']);
const blLoad = extractMethod('doBlCacheLoad', []);
const blSave = extractMethod('doBlCacheSave', ['list']);
const blGet = extractMethod('doBlCacheGet', ['target']);
const blPut = extractMethod('doBlCachePut', ['target', 'data']);
const normalizeDomain = extractMethod('_normalizeDomain', ['value']);

const histKey = extractMethod('doHistKey', ['pid']);
const histLoad = extractMethod('doHistLoad', ['pid']);
const histSave = extractMethod('doHistSave', ['pid', 'hist']);
const histId = extractMethod('doHistId', ['query', 'location']);
const histPush = extractMethod('doHistPush', ['pid', 'query', 'location', 'data']);
const histOpen = extractMethod('doHistOpen', ['entry']);

const DAY = 24 * 60 * 60 * 1000;

/* A minimal stand-in for the component: the real class fields the methods read, a fake
   localStorage, and recorders for setState / runDomainOverview. */
function mkApp(opts) {
  opts = opts || {};
  const store = opts.store || {};
  global.localStorage = {
    getItem: k => (k in store ? store[k] : null),
    setItem: (k, v) => {
      if (opts.quota && v.length > opts.quota) throw new Error('QuotaExceededError');
      store[k] = v;
    },
    removeItem: k => { delete store[k]; }
  };
  const app = {
    DO_HIST_MAX: 10,
    DO_HIST_TTL: DAY,
    DO_BL_MAX: 5,
    DO_BL_KEY: 'fh_do_bl',
    _store: store,
    _normalizeDomain: function (v) { return normalizeDomain.call(this, v); },
    doBlCacheId: function (t) { return blId.call(this, t); },
    doBlCacheLoad: function () { return blLoad.call(this); },
    doBlCacheSave: function (l) { return blSave.call(this, l); },
    doBlCacheGet: function (t) { return blGet.call(this, t); },
    doBlCachePut: function (t, d) { return blPut.call(this, t, d); },
    state: { projectId: 'p1' },
    setStateCalls: [],
    ranLookup: 0,
    doHistKey: function (pid) { return histKey.call(this, pid); },
    doHistLoad: function (pid) { return histLoad.call(this, pid); },
    doHistSave: function (pid, hist) { return histSave.call(this, pid, hist); },
    doHistId: function (q, l) { return histId.call(this, q, l); },
    doHistPush: function (pid, q, l, d) { return histPush.call(this, pid, q, l, d); },
    doHistOpen: function (e) { return histOpen.call(this, e); },
    runDomainOverview: function () { this.ranLookup++; },
    setState: function (patch, cb) {
      this.setStateCalls.push(patch);
      Object.assign(this.state, patch);
      if (cb) cb();
    }
  };
  return app;
}

function entry(query, ageMs, extra) {
  return Object.assign({
    id: query + '|United States', query: query, location: 'United States',
    data: { status: 'ok', keywords: [] }, ts: Date.now() - ageMs
  }, extra || {});
}

/* ---------- 1. fresh restores free, stale re-runs ---------- */

test('a fresh entry restores from storage and makes no network call', () => {
  const app = mkApp();
  app.doHistOpen(entry('apple.com', 60 * 60 * 1000));   // one hour old

  assert.strictEqual(app.ranLookup, 0, 'a fresh entry must not spend a DataForSEO call');
  const patch = app.setStateCalls[0];
  assert.strictEqual(patch.doQuery, 'apple.com');
  assert.deepStrictEqual(patch.doData, { status: 'ok', keywords: [] });
  assert.ok(patch.doFromHist, 'the replay must be flagged so the page can say it is a capture');
  // Opening a saved result lands on the first tab, not wherever the last lookup left off.
  assert.strictEqual(patch.doTab, 'overview');
});

test('an entry past the 24h TTL re-runs the real lookup instead of showing stale numbers', () => {
  const app = mkApp();
  app.doHistOpen(entry('apple.com', DAY + 1000));

  assert.strictEqual(app.ranLookup, 1, 'a stale entry must fall through to a live lookup');
  const patch = app.setStateCalls[0];
  assert.strictEqual(patch.doQuery, 'apple.com');
  assert.strictEqual(patch.doData, undefined, 'stale data must not be painted on screen');
  assert.strictEqual(patch.doFromHist, null);
});

test('the TTL boundary is exclusive — exactly-24h-old data is not served as fresh', () => {
  const app = mkApp();
  const e = entry('apple.com', 0);
  e.ts = Date.now() - DAY;
  app.doHistOpen(e);
  assert.strictEqual(app.ranLookup, 1);
});

test('opening nothing does nothing', () => {
  const app = mkApp();
  app.doHistOpen(null);
  assert.strictEqual(app.ranLookup, 0);
  assert.strictEqual(app.setStateCalls.length, 0);
});

/* ---------- 2. one entry per (domain, market) ---------- */

test('re-analysing the same domain and market replaces its entry rather than appending', () => {
  const app = mkApp();
  app.doHistPush('p1', 'apple.com', 'United States', { status: 'ok', n: 1 });
  app.doHistPush('p1', 'apple.com', 'United States', { status: 'ok', n: 2 });

  const hist = app.doHistLoad('p1');
  assert.strictEqual(hist.length, 1, 'ten slots must hold ten DISTINCT lookups');
  assert.strictEqual(hist[0].data.n, 2, 'the newer result wins');
});

test('the same domain in a different market is a different entry', () => {
  const app = mkApp();
  app.doHistPush('p1', 'apple.com', 'United States', { n: 1 });
  app.doHistPush('p1', 'apple.com', 'Germany', { n: 2 });
  assert.strictEqual(app.doHistLoad('p1').length, 2);
});

test('the match ignores case and surrounding whitespace, as the lookup itself does', () => {
  const app = mkApp();
  app.doHistPush('p1', 'apple.com', 'United States', { n: 1 });
  app.doHistPush('p1', '  APPLE.com ', 'United States', { n: 2 });
  const hist = app.doHistLoad('p1');
  assert.strictEqual(hist.length, 1);
  assert.strictEqual(hist[0].query, 'APPLE.com', 'stored trimmed, matched case-insensitively');
});

test('newest is first and the list is capped at DO_HIST_MAX', () => {
  const app = mkApp();
  for (let i = 0; i < 14; i++) app.doHistPush('p1', 'd' + i + '.com', 'United States', { i: i });
  const hist = app.doHistLoad('p1');
  assert.strictEqual(hist.length, 10);
  assert.strictEqual(hist[0].query, 'd13.com');
  assert.strictEqual(hist[9].query, 'd4.com');
});

test('history is per project — switching projects never shows another project\'s lookups', () => {
  const app = mkApp();
  app.doHistPush('p1', 'apple.com', 'United States', {});
  app.doHistPush('p2', 'banana.com', 'United States', {});
  assert.deepStrictEqual(app.doHistLoad('p1').map(h => h.query), ['apple.com']);
  assert.deepStrictEqual(app.doHistLoad('p2').map(h => h.query), ['banana.com']);
});

/* ---------- 3. survives hostile storage ---------- */

test('a full quota sheds the oldest entries instead of throwing', () => {
  // Small enough that the full ten-entry list cannot be written, but a short one can.
  const app = mkApp({ quota: 400 });
  for (let i = 0; i < 8; i++) {
    app._doHistCache = null;   // force a re-read, as a fresh render would
    app.doHistPush('p1', 'domain' + i + '.com', 'United States', { pad: 'x'.repeat(20) });
  }
  const hist = app.doHistLoad('p1');
  assert.ok(hist.length > 0, 'a degraded history beats no history');
  assert.ok(hist.length < 8, 'oldest entries were shed to fit');
  assert.strictEqual(hist[0].query, 'domain7.com', 'the newest lookup is the one kept');
});

test('corrupt or non-array stored JSON reads as empty rather than crashing the render', () => {
  const app = mkApp({ store: { 'fh_do_hist_p1': '{not json' } });
  assert.deepStrictEqual(app.doHistLoad('p1'), []);

  const app2 = mkApp({ store: { 'fh_do_hist_p1': '{"a":1}' } });
  assert.deepStrictEqual(app2.doHistLoad('p1'), [],
    'a stored object is not a history list — .filter/.map on it would throw');
});

test('the memo cache is refreshed by a save, so a chip appears without a reload', () => {
  const app = mkApp();
  app.doHistLoad('p1');                                    // seeds the memo with []
  app.doHistPush('p1', 'apple.com', 'United States', {});
  assert.strictEqual(app.doHistLoad('p1').length, 1,
    'a stale memo would hide the search the user just ran');
});

/* ---------- 4. the backlink cache ----------

   The costlier store: one press buys THREE Backlinks API calls against Analyze's one. It is
   deliberately keyed and scoped differently from the history above, and getting either wrong
   is a spend bug rather than a cosmetic one:

   - DOMAIN ONLY, no market. The Backlinks API has no location parameter, so keying by market
     would re-buy identical data once per country.
   - Not per project. A competitor checked from two projects should be bought once.
   - Paths are case-sensitive; hosts are not. Collapsing /Blog into /blog would show one
     page's links under the other page's name.
   - Refusals (setup / budget / error) are not answers. Caching one would pin a transient
     failure to a domain for 24h and make the retry look broken. */

const BL_OK = { state: 'ok', summary: { backlinks: 746, refDomains: 380 } };

test('a stored backlink block comes back for the same domain and costs nothing', () => {
  const app = mkApp();
  app.doBlCachePut('premierstaff.com', BL_OK);
  const hit = app.doBlCacheGet('premierstaff.com');
  assert.ok(hit, 'the three calls already bought must not be bought again');
  assert.deepStrictEqual(hit.data, BL_OK);
  assert.ok(hit.ts, 'the age is stored so the button can say how old the saved copy is');
});

test('the market is not part of the key — the Backlinks API has no location', () => {
  const app = mkApp();
  app.doBlCachePut('premierstaff.com', BL_OK);
  // Same domain, and the caller has since switched the market selector. Still a hit.
  assert.ok(app.doBlCacheGet('premierstaff.com'), 'a market switch must not re-buy backlinks');
  assert.strictEqual(app.doBlCacheLoad().length, 1, 'one domain must occupy one slot');
});

test('scheme, www and case do not split one domain across slots', () => {
  const app = mkApp();
  app.doBlCachePut('https://www.PremierStaff.com/', BL_OK);
  assert.ok(app.doBlCacheGet('premierstaff.com'));
  assert.ok(app.doBlCacheGet('http://premierstaff.com'));
  assert.strictEqual(app.doBlCacheLoad().length, 1);
});

test('paths keep their case — /Blog and /blog are different pages to DataForSEO', () => {
  const app = mkApp();
  app.doBlCachePut('premierstaff.com/Blog', { state: 'ok', which: 'upper' });
  app.doBlCachePut('premierstaff.com/blog', { state: 'ok', which: 'lower' });
  assert.strictEqual(app.doBlCacheLoad().length, 2, 'two pages, two entries');
  assert.strictEqual(app.doBlCacheGet('premierstaff.com/Blog').data.which, 'upper');
  assert.strictEqual(app.doBlCacheGet('premierstaff.com/blog').data.which, 'lower');
});

test('a page and its bare domain are separate entries', () => {
  const app = mkApp();
  app.doBlCachePut('premierstaff.com', { state: 'ok', which: 'domain' });
  app.doBlCachePut('premierstaff.com/hostesses', { state: 'ok', which: 'page' });
  assert.strictEqual(app.doBlCacheGet('premierstaff.com').data.which, 'domain');
  assert.strictEqual(app.doBlCacheGet('premierstaff.com/hostesses').data.which, 'page');
});

test('a bare trailing slash is not a path', () => {
  const app = mkApp();
  app.doBlCachePut('premierstaff.com/', BL_OK);
  assert.strictEqual(app.doBlCacheId('premierstaff.com/'), 'premierstaff.com');
  assert.ok(app.doBlCacheGet('premierstaff.com'));
});

test('an entry past the 24h TTL is a miss, so the button offers a real refresh', () => {
  const app = mkApp();
  app.doBlCachePut('premierstaff.com', BL_OK);
  app.doBlCacheLoad()[0].ts = Date.now() - DAY - 1000;
  assert.strictEqual(app.doBlCacheGet('premierstaff.com'), null,
    'day-old link counts must not be shown as current');
});

test('an empty-but-real answer is cached; a refusal is not', () => {
  const app = mkApp();
  // DataForSEO indexes no backlinks for this target. That answer was paid for.
  app.doBlCachePut('nolinks.com', { state: 'empty', note: 'no indexed backlinks' });
  assert.ok(app.doBlCacheGet('nolinks.com'), 'a measured "none" is data and was billed');

  // These three bought nothing, so there is nothing to remember.
  ['setup', 'budget', 'error'].forEach(st => {
    app.doBlCachePut('refused' + st + '.com', { state: st, note: 'nope' });
    assert.strictEqual(app.doBlCacheGet('refused' + st + '.com'), null,
      st + ' is a refusal, not a result — caching it would break the retry for 24h');
  });
  assert.strictEqual(app.doBlCacheLoad().length, 1);
});

test('nothing is stored for an unusable target', () => {
  const app = mkApp();
  app.doBlCachePut('', BL_OK);
  app.doBlCachePut('   ', BL_OK);
  assert.strictEqual(app.doBlCacheLoad().length, 0);
  assert.strictEqual(app.doBlCacheGet(''), null);
});

test('re-loading a domain replaces its entry and moves it to the front', () => {
  const app = mkApp();
  app.doBlCachePut('a.com', { state: 'ok', n: 1 });
  app.doBlCachePut('b.com', { state: 'ok', n: 2 });
  app.doBlCachePut('a.com', { state: 'ok', n: 3 });
  const all = app.doBlCacheLoad();
  assert.strictEqual(all.length, 2);
  assert.strictEqual(all[0].id, 'a.com', 'the freshest lookup is the last one shed on quota');
  assert.strictEqual(app.doBlCacheGet('a.com').data.n, 3);
});

test('the store is capped at DO_BL_MAX, newest kept', () => {
  const app = mkApp();
  for (let i = 0; i < 8; i++) app.doBlCachePut('d' + i + '.com', BL_OK);
  const all = app.doBlCacheLoad();
  assert.strictEqual(all.length, 5);
  assert.strictEqual(all[0].id, 'd7.com');
  assert.strictEqual(app.doBlCacheGet('d0.com'), null, 'the oldest was evicted');
});

test('a full quota sheds the oldest backlink entries instead of throwing', () => {
  // These payloads are the biggest thing the page stores — 100 link rows and 60 anchors.
  const app = mkApp({ quota: 300 });
  for (let i = 0; i < 5; i++) {
    app._doBlCache = null;   // force a re-read, as a fresh render would
    app.doBlCachePut('domain' + i + '.com', { state: 'ok', pad: 'x'.repeat(40) });
  }
  const all = app.doBlCacheLoad();
  assert.ok(all.length > 0, 'a degraded cache beats no cache');
  assert.ok(all.length < 5, 'oldest entries were shed to fit');
  assert.strictEqual(all[0].id, 'domain4.com');
});

test('corrupt stored JSON reads as empty rather than crashing the render', () => {
  const app = mkApp({ store: { 'fh_do_bl': '{not json' } });
  assert.deepStrictEqual(app.doBlCacheLoad(), []);

  const app2 = mkApp({ store: { 'fh_do_bl': '{"a":1}' } });
  assert.deepStrictEqual(app2.doBlCacheLoad(), [],
    'a stored object is not a list — .filter on it would throw');
});

test('the memo is refreshed by a save, so the card fills without a reload', () => {
  const app = mkApp();
  app.doBlCacheLoad();                    // seeds the memo with []
  app.doBlCachePut('premierstaff.com', BL_OK);
  assert.ok(app.doBlCacheGet('premierstaff.com'),
    'a stale memo would still show "Load backlinks" right after loading them');
});
