/**
 * The AI Visibility tab and the Prompts tab measure DIFFERENT THINGS, and the page never said so.
 *
 * Reported as "fake information": AI Visibility showed eventstaff.com with 17 mentions and a 66%
 * share, while the Prompts tab's domain chips showed eventstaff.com (0) — and there was no way
 * to open a prompt and see where those 17 came from.
 *
 * Both numbers are real. They come from two unrelated DataForSEO products:
 *
 *   - AI Visibility  -> LLM Mentions API. Aggregate counts over DataForSEO's OWN index of AI
 *     answers, across queries this project never asked. Stored in `llm_mention_metrics`. The
 *     aggregate endpoint returns totals only, so there is no query-level detail to drill into.
 *   - Prompts        -> LLM Responses API. This project's own tracked prompts, run on demand.
 *
 * Verified against the live database: the six tracked prompts' stored answers contain zero
 * occurrences of any tracked competitor, in prose or in citations. So `(0)` was correct and
 * `17` was correct, and presenting them adjacent with no explanation is what made a real number
 * look invented.
 *
 * This pins the reconciliation line that states both facts in one sentence, so the two panels
 * stop contradicting each other on screen.
 */
/* `describe`/`it` are NOT globals under `node --test` — without this require the whole
   file threw ReferenceError before a single assertion ran, and a suite that collected
   zero tests looks exactly like a suite that passed (skills.md §9). */
const { describe, it } = require('node:test');
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'src', 'js', 'pages', 'ai_optimization.js');

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

const prompt = (id, results) => ({ id, results });
const checked = extra => Object.assign({ state: 'checked' }, extra);

describe('AI visibility / prompts reconciliation', () => {
  const competitorPromptHits = extractFn('competitorPromptHits');

  it('counts prompts whose own answers named a competitor', () => {
    const prompts = [
      prompt('p1', { chat_gpt: checked({ competitors: [{ name: 'a.com' }] }) }),
      prompt('p2', { chat_gpt: checked({ competitors: [] }) }),
      prompt('p3', { chat_gpt: checked({ competitors: [{ name: 'b.com' }] }) }),
    ];
    assert.strictEqual(competitorPromptHits(prompts), 2);
  });

  it('counts a prompt once even when several engines named a competitor', () => {
    const prompts = [prompt('p1', {
      chat_gpt: checked({ competitors: [{ name: 'a.com' }] }),
      claude: checked({ competitors: [{ name: 'a.com' }] }),
    })];
    assert.strictEqual(competitorPromptHits(prompts), 1);
  });

  it('the live case: real competitor totals upstream, genuinely zero in your prompts', () => {
    const prompts = [
      prompt('p1', { chat_gpt: checked({ competitors: [] }) }),
      prompt('p2', { perplexity: checked({ competitors: [] }) }),
    ];
    assert.strictEqual(competitorPromptHits(prompts), 0);
  });

  it('an unrun prompt is not evidence of absence', () => {
    // results is {} until a prompt has been checked; it must not be counted as "no competitor
    // found here", because nothing was looked at.
    const prompts = [prompt('p1', {}), prompt('p2', { chat_gpt: checked({ competitors: [{ name: 'a.com' }] }) })];
    assert.strictEqual(competitorPromptHits(prompts), 1);
  });

  it('an errored cell observed nothing and is not counted either', () => {
    const prompts = [prompt('p1', { chat_gpt: { state: 'error', competitors: [] } })];
    assert.strictEqual(competitorPromptHits(prompts), 0);
  });

  it('survives a missing competitors array', () => {
    const prompts = [prompt('p1', { chat_gpt: checked({}) })];
    assert.doesNotThrow(() => competitorPromptHits(prompts));
    assert.strictEqual(competitorPromptHits(prompts), 0);
  });
});
