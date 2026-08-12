/**
 * The Cited Pages list — the full weekly top_pages snapshot, in a sub-tab and a fullscreen
 * overlay that the "Your Most-Cited Pages" card opens.
 *
 * Why this exists: the card showed four rows out of a DataForSEO response that carried ten,
 * because the connector filtered every URL not on our own host out before storing it. The
 * fix keeps all of them (up to TOP_PAGES_LIMIT = 100) and splits them at read time, so the
 * page now has two lists — ours, and the co-cited pages on other domains — rendered by ONE
 * view model in TWO places. Three things are pinned here:
 *
 *   1. "Load all" is free. It reveals rows that are already in the cached response; if it ever
 *      grows a fetch, this file fails. The user chose the free behaviour explicitly.
 *   2. The filter matches URL *or* host, because "who else is being cited?" is asked by typing
 *      a domain on the co-cited tab.
 *   3. Every `aiv.*` binding the markup reads is actually assigned. The sub-tab and the overlay
 *      are duplicated markup — the failure mode is one of them silently rendering blanks.
 */
const { describe, it } = require('node:test');
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'src', 'js', 'pages', 'ai_optimization.js');
const TPL = path.join(__dirname, '..', 'src', 'pages', 'site_audit.html');

/* The view model is spliced into one big render function and is not a module, so the helpers
   are pulled out by brace matching — the same seam every other SPA test uses. */
function extractFns(names) {
  const src = fs.readFileSync(SRC, 'utf8');
  const decls = names.map(name => {
    const marker = 'const ' + name + ' = ';
    const start = src.indexOf(marker);
    assert.ok(start !== -1, name + ' not found in ai_optimization.js');
    let i = src.indexOf('{', start);
    let depth = 0;
    for (; i < src.length; i++) {
      if (src[i] === '{') depth++;
      else if (src[i] === '}') { depth--; if (depth === 0) break; }
    }
    return marker + src.slice(start + marker.length, i + 1) + ';';
  });
  return eval('(function () {\n' + decls.join('\n') + '\nreturn {' + names.join(', ') + '};\n})()');
}

const page = (url, domain) => ({ url: url, domain: domain || '', mentions: 1, impressions: 1, platforms: ['google'] });

const OURS = [
  page('https://premierstaff.com/blog/6-steps-to-calculate-wedding-staff', 'premierstaff.com'),
  page('https://premierstaff.com/blog/shorts/average-cost-to-hire-event-staff', 'premierstaff.com'),
  page('https://premierstaff.com/blog/bartender-resume-template', 'premierstaff.com'),
];
const OTHERS = [
  page('https://www.eventstaff.com/pricing', 'www.eventstaff.com'),
  page('https://fash.com/costs/bartender', 'fash.com'),
];

describe('Cited Pages — filtering', () => {
  const { pgFilter } = extractFns(['pgFilter']);

  it('an empty query returns every row, and the same array identity is fine', () => {
    assert.strictEqual(pgFilter(OURS, '').length, 3);
    assert.strictEqual(pgFilter(OURS, null).length, 3);
    assert.strictEqual(pgFilter(OURS, '   ').length, 3, 'whitespace is not a search');
  });

  it('matches inside the URL', () => {
    assert.deepStrictEqual(pgFilter(OURS, 'bartender').map(p => p.url), [OURS[2].url]);
  });

  it('matches the host too — the co-cited tab is read by domain', () => {
    // This is the whole point of carrying `domain` on the row: on the co-cited list the
    // question is "who else is being cited?", and the answer is typed as a domain.
    assert.deepStrictEqual(pgFilter(OTHERS, 'eventstaff').map(p => p.url), [OTHERS[0].url]);
  });

  it('is case-insensitive and trims the query', () => {
    assert.strictEqual(pgFilter(OTHERS, '  FASH.COM ').length, 1);
  });

  it('a query nothing matches returns empty, not everything', () => {
    // The inverse ("no matches, so show all") is the classic filter bug, and it reads as the
    // filter being ignored.
    assert.deepStrictEqual(pgFilter(OURS, 'zzz-nothing'), []);
  });

  it('survives a row with no url or domain', () => {
    assert.doesNotThrow(() => pgFilter([{}], 'x'));
    assert.deepStrictEqual(pgFilter([{}], 'x'), []);
  });
});

describe('Cited Pages — "Load all"', () => {
  const { pgPage } = extractFns(['pgPage']);
  const rows = Array.from({ length: 100 }, (_, i) => page('https://x.com/p' + i, 'x.com'));

  it('shows the preview slice until it is pressed', () => {
    assert.strictEqual(pgPage(rows, false, 25).length, 25);
  });

  it('shows everything once it is pressed — up to the 100 a week can hold', () => {
    assert.strictEqual(pgPage(rows, true, 25).length, 100);
  });

  it('never pads: a short list is shown whole either way', () => {
    assert.strictEqual(pgPage(OURS, false, 25).length, 3);
    assert.strictEqual(pgPage(OURS, true, 25).length, 3);
  });

  it('is a render, not a fetch — it may only touch local state', () => {
    // The rows are already in the cached AI response. If "Load all" ever called the API it
    // would be a paid button wearing a free button's label.
    const src = fs.readFileSync(SRC, 'utf8');
    const handler = src.slice(src.indexOf('aiv.pgLoadAll ='), src.indexOf('aiv.pgQ ='));
    assert.ok(/setState\(\{ aiPgAll: true \}\)/.test(handler), handler);
    ['fetchTab', 'aiPost', 'aiReload', 'aiRun', 'FuseAPI'].forEach(bad => {
      assert.ok(handler.indexOf(bad) === -1, '"Load all" must not call ' + bad);
    });
  });
});

describe('Cited Pages — the markup and the view model agree', () => {
  it('every aiv.* binding the AI markup reads is assigned by the view model', () => {
    // The sub-tab and the fullscreen overlay render the SAME values in two blocks of markup.
    // A typo in one of them is invisible on screen — it renders as a blank cell.
    const tpl = fs.readFileSync(TPL, 'utf8');
    const src = fs.readFileSync(SRC, 'utf8');
    const used = new Set([...tpl.matchAll(/aiv\.([A-Za-z0-9_]+)/g)].map(m => m[1]));
    const assigned = new Set([...src.matchAll(/aiv\.([A-Za-z0-9_]+)\s*=/g)].map(m => m[1]));
    // `aiv` is seeded with a literal (`const aiv = { domain, showWizard, showMain }`), so those
    // keys are assigned without ever appearing as `aiv.x =`.
    const seed = src.slice(src.indexOf('const aiv = {'));
    [...seed.slice(0, seed.indexOf('}') + 1).matchAll(/([A-Za-z0-9_]+):/g)].forEach(m => assigned.add(m[1]));
    const missing = [...used].filter(k => !assigned.has(k));
    assert.deepStrictEqual(missing, [], 'markup reads aiv keys nothing assigns: ' + missing.join(', '));
  });

  it('both the sub-tab and the overlay render the list', () => {
    const tpl = fs.readFileSync(TPL, 'utf8');
    assert.ok(tpl.indexOf('{{ aiv.showPages }}') !== -1, 'the Cited Pages sub-tab is gone');
    assert.ok(tpl.indexOf('{{ aiv.pgOpen }}') !== -1, 'the fullscreen overlay is gone');
    const rows = tpl.split('{{ aiv.pgRows }}').length - 1;
    assert.strictEqual(rows, 2, 'the two surfaces must both read the one row list');
  });

  it('the card opens the full list', () => {
    const tpl = fs.readFileSync(TPL, 'utf8');
    assert.ok(tpl.indexOf('{{ aiv.pgOpenOurs }}') !== -1,
              '"Your Most-Cited Pages" no longer opens the fullscreen list');
  });
});
