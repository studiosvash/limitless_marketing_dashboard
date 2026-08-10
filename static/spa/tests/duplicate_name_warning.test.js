/* Tests for ptDuplicateNameWarning — the Edit modal's soft duplicate-name check.

   Run: node --test static/spa/tests/duplicate_name_warning.test.js

   Mirrors apps/dashboard/services/project_naming.find_project_name_conflicts, whose docstring
   carries the full reasoning. In short: one domain can legitimately be several projects (one
   per city), so this is never a block — but two projects on one domain sharing a NAME are
   indistinguishable in the switcher, the header and every export, and two sharing a
   (domain, location) pair read the same keyword_rankings rows and report identical numbers
   under two names forever.

   Extracted from the shipping positioning.js by brace-matching, like listVisibility. */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

function extractFn(marker, argNames) {
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

const warn = extractFn(
  'const ptDuplicateNameWarning = (projects, selfId, name, domain, location) => {',
  ['projects', 'selfId', 'name', 'domain', 'location']
);

const PROJECTS = [
  { id: 'staff-ny', name: 'Premierstaff NY', domain: 'premierstaff.com',
    location: 'United States - New York' },
  { id: 'staff-dc', name: 'Premierstaff DC', domain: 'premierstaff.com',
    location: 'United States - Washington, DC' },
  { id: 'fuse', name: 'Premierstaff DC', domain: 'fusehealth.com',
    location: 'United States - Washington, DC' }
];

test('a distinct name and location on the domain says nothing', () => {
  assert.strictEqual(
    warn(PROJECTS, 'staff-ny', 'Premierstaff Austin', 'premierstaff.com',
         'United States - Austin, TX'),
    ''
  );
});

test('an exact name match on the same domain warns and names the sibling', () => {
  const t = warn(PROJECTS, 'staff-ny', 'Premierstaff DC', 'premierstaff.com',
                 'United States - Austin, TX');
  assert.ok(t, 'expected a warning');
  assert.ok(t.includes('Premierstaff DC'), t);
});

test('the comparison is case- and whitespace-folded', () => {
  assert.ok(warn(PROJECTS, 'staff-ny', '  premierstaff dc ', 'premierstaff.com',
                 'United States - Austin, TX'));
});

test('the same name on a DIFFERENT domain is not a conflict', () => {
  assert.strictEqual(
    warn(PROJECTS, null, 'Premierstaff DC', 'driphydration.com',
         'United States - Austin, TX'),
    ''
  );
});

test('www and bare are one domain', () => {
  assert.ok(warn(PROJECTS, 'staff-ny', 'Premierstaff DC', 'www.premierstaff.com',
                 'United States - Austin, TX'));
});

test('same domain + same location warns even when the name is distinct', () => {
  const t = warn(PROJECTS, 'staff-ny', 'Premierstaff Capital', 'premierstaff.com',
                 'United States - Washington, DC');
  assert.ok(t, 'expected a warning');
  assert.ok(/same rankings|same numbers/i.test(t), t);
});

test('a project never conflicts with itself', () => {
  assert.strictEqual(
    warn(PROJECTS, 'staff-dc', 'Premierstaff DC', 'premierstaff.com',
         'United States - Washington, DC'),
    ''
  );
});

test('it always reads as allowed — never as a refusal', () => {
  const t = warn(PROJECTS, 'staff-ny', 'Premierstaff DC', 'premierstaff.com',
                 'United States - Washington, DC');
  assert.ok(/allowed/i.test(t), 'the copy must say this is permitted: ' + t);
});

test('an empty project list or a blank name asks nothing', () => {
  assert.strictEqual(warn([], 'x', 'Anything', 'premierstaff.com', 'X'), '');
  assert.strictEqual(warn(PROJECTS, 'staff-ny', '   ', 'premierstaff.com', ''), '');
});
