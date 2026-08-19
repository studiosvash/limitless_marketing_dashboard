/* Does the assembled SPA actually parse?

   Run: node --test static/spa/tests/*.test.js

   WHY THIS EXISTS. There is no bundler and no build step: `apps/dashboard/spa_views.py`
   resolves the two "#include" directive spellings (an HTML comment and a block comment) at
   request time and ships one big inline script. Every other test in this directory cuts ONE
   function out of
   ONE source file and evaluates it, so all of them keep passing while the assembled page is a
   syntax error — and a syntax error in a page-level fragment does not break that fragment, it
   breaks the ENTIRE app: the browser aborts the whole script and every screen renders blank
   under a red "Root: Invalid or unexpected token" banner, with nothing naming the file.

   That is not hypothetical. On 2026-08-18 a multi-line tooltip string was written with real
   newlines instead of `\n` escapes, which terminated the string literal early. `node --check`
   on the individual file could not have caught it either — these page fragments are class
   bodies, so they are not standalone-parseable at all and fail `--check` even when correct.
   Only the assembled whole is a valid program, so only the assembled whole can be checked.

   This test does exactly what the browser does: resolve the includes, pull out every inline
   script, and compile each one. It asserts nothing about behaviour — compiling is the whole
   assertion. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SRC_DIR = path.join(__dirname, '..', 'src');
const INDEX = path.join(SRC_DIR, 'index.html');

/* The same directive and the same recursion as spa_views.resolve_includes. Deliberately a
   re-implementation rather than a call into Python: this suite runs under plain node. If the
   directive syntax ever changes on the server, the include below stops resolving and the
   "every fragment is included" test fails loudly rather than checking a shrunken page. */
const INCLUDE = /<!--\s*#include\s+"([^"]+)"\s*-->|\/\*\s*#include\s+"([^"]+)"\s*\*\//g;

function resolveIncludes(file) {
  return fs.readFileSync(file, 'utf8').replace(INCLUDE, (whole, a, b) => {
    const target = path.join(SRC_DIR, a || b);
    return fs.existsSync(target) ? resolveIncludes(target) : whole;
  });
}

/* Inline scripts only. A `<script src=...>` has no body to compile and its file is served
   as-is, so it is out of scope here. */
function inlineScripts(html) {
  const out = [];
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (/\ssrc\s*=/i.test(m[1])) continue;
    if (m[2].trim()) out.push({ body: m[2], at: m.index });
  }
  return out;
}

const HTML = resolveIncludes(INDEX);

test('every include actually resolved — the page under test is the whole page', () => {
  const unresolved = HTML.match(INCLUDE);
  assert.strictEqual(unresolved, null,
    'unresolved include directive(s): ' + (unresolved || []).join(', '));
  assert.ok(HTML.length > 200000,
    'assembled page is only ' + HTML.length + " bytes — the includes did not pull the app in, "
    + 'so a syntax error anywhere in them would go unnoticed');
});

test('every page fragment is present in the assembled page', () => {
  /* Checked so that a page dropped from index.html is caught here rather than by a user
     finding a blank screen — and so the compile test above is known to have covered it.

     Matched on the fragment's own CONTENT, not on a derived marker: the file name and the tab
     key are not the same thing (ai_optimization.js serves tab 'ai'), and a rule that guesses
     one from the other fails on the file it is least likely to be revisited for. */
  const dir = path.join(SRC_DIR, 'js', 'pages');
  const fragments = fs.readdirSync(dir).filter(f => f.endsWith('.js'));
  assert.ok(fragments.length >= 10, 'expected the page fragments to exist');
  for (const f of fragments) {
    const lines = fs.readFileSync(path.join(dir, f), 'utf8').split('\n')
      .map(l => l.trim())
      .filter(l => l.length > 40 && !l.startsWith('/*') && !l.startsWith('*') && !l.startsWith('//'));
    assert.ok(lines.length, f + ' has no substantial line to match on');
    assert.ok(HTML.includes(lines[Math.floor(lines.length / 2)]),
      f + ' is not included in the assembled page');
  }
});

test('the assembled page compiles — no syntax error reaches the browser', () => {
  const scripts = inlineScripts(HTML);
  assert.ok(scripts.length > 0, 'no inline scripts found — the extraction regex is wrong');
  for (const s of scripts) {
    /* new vm.Script() parses without running: it catches exactly the class of error the
       browser reports as "Invalid or unexpected token", and nothing else. */
    assert.doesNotThrow(
      () => new vm.Script(s.body),
      err => {
        /* Report the offending line with context — the browser's own message names no file. */
        const line = Number((String(err.stack || '').match(/:(\d+)\n/) || [])[1] || 0);
        const around = s.body.split('\n').slice(Math.max(0, line - 3), line + 2).join('\n');
        return new Error(
          'inline <script> at byte ' + s.at + ' does not parse: ' + err.message
          + '\n--- near line ' + line + ' ---\n' + around
        );
      }
    );
  }
});
