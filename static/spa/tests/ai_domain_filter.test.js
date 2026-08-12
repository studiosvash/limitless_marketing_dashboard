/**
 * The AI Prompts tab's domain filter (F3), and the two ways it could be built wrong.
 *
 * This feature had never existed. The chips the team were clicking were PROMPT-LIST filters
 * sitting exactly where a domain tab-bar would be, which is why clicking one read as a broken
 * domain filter: selecting a list showed prompts that had nothing to do with the domain named
 * on the chip.
 *
 * Two rules are pinned here because getting either wrong reproduces the reported bug:
 *
 *   1. The predicate tests membership of the SELECTED domain in that prompt's own mention set.
 *      "Has any mention at all" is the failure that was reported -- clicking a competitor and
 *      getting back every prompt that mentions anybody.
 *   2. It composes with the list filter by AND. Replacing the list filter would silently widen
 *      the result the moment a domain is picked.
 *
 * The view model is built by a `js/pages/*.js` file that is spliced into one big render
 * function and is not a module, so the logic under test is extracted here the same way
 * `project_list_visibility.test.js` does it: read the source, pull the named helper out by
 * brace matching, and evaluate it in isolation.
 */
/* `describe`/`it` are NOT globals under `node --test` — without this require the whole
   file threw ReferenceError before a single assertion ran, and a suite that collected
   zero tests looks exactly like a suite that passed (skills.md §9). */
const { describe, it } = require('node:test');
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'src', 'js', 'pages', 'ai_optimization.js');

/* `matchesDomain` calls `mentionSetOf`, so they are extracted and evaluated TOGETHER in one
   scope. Pulling them out individually left the second one referencing a name that did not
   exist, which fails for a reason that has nothing to do with the behaviour under test. */
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
  // YOU_KEY is a plain const the two helpers close over; declared here so the extracted
  // bodies evaluate against the same sentinel the page uses rather than a copy.
  const youKey = src.match(/const YOU_KEY = '([^']+)'/);
  assert.ok(youKey, 'YOU_KEY not found in ai_optimization.js');
  return eval("(function () {\nconst YOU_KEY = '" + youKey[1] + "';\n" + decls.join('\n')
              + '\nreturn {' + names.join(', ') + ', YOU_KEY};\n})()');
}

/* A prompt as the view model sees it: results keyed by platform id, each carrying the
   detector's verdict for us (`mentioned`) and the competitors it found by name. */
const prompt = (id, listId, results) => ({ id: id, listId: listId, results: results });

const YOU = '__you';

const PROMPTS = [
  // Mentions us only.
  prompt('p1', 'l1', { chat_gpt: { state: 'checked', mentioned: true, competitors: [] } }),
  // Mentions competitor A only.
  prompt('p2', 'l1', { chat_gpt: { state: 'checked', mentioned: false, competitors: [{ name: 'a.com' }] } }),
  // Mentions competitor B only -- the row that must NOT come back when A is selected.
  prompt('p3', 'l2', { chat_gpt: { state: 'checked', mentioned: false, competitors: [{ name: 'b.com' }] } }),
  // Mentions us AND competitor A, but sits in a different list.
  prompt('p4', 'l2', { chat_gpt: { state: 'checked', mentioned: true, competitors: [{ name: 'a.com' }] } }),
  // Never run: results is {} until a prompt has been checked at least once.
  prompt('p5', 'l1', {}),
];

describe('AI prompts domain filter', () => {
  const fns = extractFns(['mentionSetOf', 'matchesDomain']);
  const mentionSetOf = fns.mentionSetOf;
  const matchesDomain = fns.matchesDomain;

  it('collects the domains a prompt actually mentions', () => {
    assert.deepStrictEqual(mentionSetOf(PROMPTS[0]), { [YOU]: 1 });
    assert.deepStrictEqual(mentionSetOf(PROMPTS[1]), { 'a.com': 1 });
    assert.deepStrictEqual(mentionSetOf(PROMPTS[3]), { [YOU]: 1, 'a.com': 1 });
  });

  it('a never-run prompt mentions nothing', () => {
    // Not "mentions nobody, so show it everywhere" -- an unrun prompt is an absence of
    // evidence and belongs to no domain chip.
    assert.deepStrictEqual(mentionSetOf(PROMPTS[4]), {});
  });

  it('selecting a competitor returns ONLY prompts mentioning THAT competitor', () => {
    const got = PROMPTS.filter(p => matchesDomain(p, 'a.com')).map(p => p.id);
    // p3 mentions b.com. If the predicate were "has any mention", p3 would be here -- that is
    // the exact bug that was reported.
    assert.deepStrictEqual(got, ['p2', 'p4']);
  });

  it('selecting You returns only prompts where the detector found us', () => {
    assert.deepStrictEqual(PROMPTS.filter(p => matchesDomain(p, YOU)).map(p => p.id), ['p1', 'p4']);
  });

  it('no domain selected leaves every prompt visible', () => {
    assert.strictEqual(PROMPTS.filter(p => matchesDomain(p, null)).length, PROMPTS.length);
  });

  it('composes with the list filter by AND, never replacing it', () => {
    const visible = PROMPTS
      .filter(p => p.listId === 'l2')
      .filter(p => matchesDomain(p, 'a.com'))
      .map(p => p.id);
    // p2 also mentions a.com but is in l1; a domain pick must not widen past the chosen list.
    assert.deepStrictEqual(visible, ['p4']);
  });

  it('counts per domain reflect prompts, not mentions', () => {
    const count = dom => PROMPTS.filter(p => matchesDomain(p, dom)).length;
    assert.strictEqual(count('a.com'), 2);
    assert.strictEqual(count('b.com'), 1);
    assert.strictEqual(count(YOU), 2);
  });
});
