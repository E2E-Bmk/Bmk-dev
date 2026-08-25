import { expect, test } from 'vitest';

import { format } from '../subject';
import { dep, mod, result } from '../helpers';

/* Every test joins at least two projections over one result and pins the exact
   value each projection is contracted to produce — the whole violation record
   of §6.1, the counts of §6.3, and the json serialisation of §7.2 — so a
   delivery that is internally consistent but wrong in any one field fails. A
   root passes only when every owner it joins is right at once. */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any;

const RS_STD = {
  forbidden: [
    { name: 'no-b', severity: 'error', from: {}, to: { path: 'b' }, comment: 'b is off limits' },
    { name: 'warn-c', severity: 'warn', from: {}, to: { path: 'c' } },
  ],
  allowed: [],
  required: [],
};

const buildStd = () =>
  result(
    [
      mod('a.js', {
        deps: [
          dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] }),
          dep('c.js', { module: 'c.js', valid: false, rules: [{ name: 'warn-c', severity: 'warn' }] }),
        ],
      }),
      mod('b.js'),
      mod('c.js'),
    ],
    RS_STD,
  );

const STD_VIOL = [
  { type: 'dependency', from: 'a.js', to: 'b.js', unresolvedTo: 'b.js', dependencyTypes: ['local'], rule: { name: 'no-b', severity: 'error' } },
  { type: 'dependency', from: 'a.js', to: 'c.js', unresolvedTo: 'c.js', dependencyTypes: ['local'], rule: { name: 'warn-c', severity: 'warn' } },
];

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation; the four severity counts tally the violations and sum to the list length; the err reporter lists a dependency violation and returns exit code equal to the error count
// Verifies: DC-CVI-001, DC-CVI-002
test('the json summary pins both the full violation list and the four counts', async () => {
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  const e = await format(buildStd(), { outputType: 'err', ruleSet: RS_STD });
  expect(j.summary.violations).toEqual(STD_VIOL);
  expect([j.summary.error, j.summary.warn, j.summary.info, j.summary.ignore]).toEqual([1, 1, 0, 0]);
  expect(e.exitCode).toBe(j.summary.error);
});

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation; the err reporter lists a dependency violation and returns exit code equal to the error count
// Verifies: DC-CVI-001, DC-CVI-002
test('the json violation list and the err exit code agree on error count and shape', async () => {
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  const e = await format(buildStd(), { outputType: 'err', ruleSet: RS_STD });
  expect(j.summary.violations).toEqual(STD_VIOL);
  expect(j.summary.violations).toHaveLength(2);
  expect(e.exitCode).toBe(1);
  expect(e.output).toMatch(/no-b/);
  expect(e.output).toMatch(/warn-c/);
});

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation; the csv reporter returns an incidence matrix and exit code zero
// Verifies: DC-CVI-001, DC-CVI-002
test('the csv header column count matches the module count and the json list is exact', async () => {
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  const c = await format(buildStd(), { outputType: 'csv', ruleSet: RS_STD });
  const headerCells = c.output.split('\n')[0].split(',').length;
  expect(j.modules).toHaveLength(3);
  expect(headerCells).toBe(5);
  expect(j.summary.violations).toEqual(STD_VIOL);
  expect(c.exitCode).toBe(0);
});

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation; violations of equal severity are ordered by rule name
// Verifies: DC-CVI-001, DC-CVI-002
test('every reporter reads the same exact violation list from one result', async () => {
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  expect(j.summary.violations).toEqual(STD_VIOL);
  expect(j.summary.violations.map((v: Any) => v.rule.name)).toEqual(['no-b', 'warn-c']);
  expect(j.summary.violations.map((v: Any) => [v.from, v.to])).toEqual([['a.js', 'b.js'], ['a.js', 'c.js']]);
});

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation; the err-long reporter appends the matched rule comment under the violation
// Verifies: DC-CVI-001, DC-CVI-002
test('the err-long comment is the matched comment while the json record stays exact', async () => {
  const el = await format(buildStd(), { outputType: 'err-long', ruleSet: RS_STD });
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  expect(el.output).toMatch(/b is off limits/);
  expect(el.exitCode).toBe(1);
  expect(j.summary.violations).toEqual(STD_VIOL);
});

// DependsOn: an invalid circular dependency under a circular rule becomes a cycle violation
// Verifies: DC-CVI-001, DC-CVI-002
test('a cycle violation carries the exact cycle array and no other carrier', async () => {
  const RS = { forbidden: [{ name: 'no-circular', severity: 'error', from: {}, to: { circular: true }, comment: 'no loops' }], allowed: [], required: [] };
  const build = () =>
    result(
      [
        mod('a.js', {
          deps: [
            dep('b.js', {
              module: 'b.js',
              valid: false,
              rules: [{ name: 'no-circular', severity: 'error' }],
              cycle: [
                { name: 'b.js', dependencyTypes: ['local'] },
                { name: 'a.js', dependencyTypes: ['local'] },
              ],
            }),
          ],
        }),
        mod('b.js'),
      ],
      RS,
    );
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations).toEqual([
    {
      type: 'cycle',
      from: 'a.js',
      to: 'b.js',
      unresolvedTo: 'b.js',
      dependencyTypes: ['local'],
      rule: { name: 'no-circular', severity: 'error' },
      cycle: [
        { name: 'b.js', dependencyTypes: ['local'] },
        { name: 'a.js', dependencyTypes: ['local'] },
      ],
    },
  ]);
  const v = j.summary.violations[0];
  expect(v.via).toBeUndefined();
  expect(v.metrics).toBeUndefined();
});

// DependsOn: an invalid edge under a moreUnstable rule with instability on both ends becomes an instability violation
// Verifies: DC-CVI-001, DC-CVI-002
test('an instability violation carries the exact metrics and no other carrier', async () => {
  const RS = { forbidden: [{ name: 'nmu', severity: 'warn', from: {}, to: { moreUnstable: true } }], allowed: [], required: [] };
  const build = () =>
    result(
      [
        mod('a.js', { instability: 0.2, deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'nmu', severity: 'warn' }], instability: 0.8 })] }),
        mod('b.js', { instability: 0.8 }),
      ],
      RS,
    );
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations).toEqual([
    {
      type: 'instability',
      from: 'a.js',
      to: 'b.js',
      unresolvedTo: 'b.js',
      dependencyTypes: ['local'],
      rule: { name: 'nmu', severity: 'warn' },
      metrics: { from: { instability: 0.2 }, to: { instability: 0.8 } },
    },
  ]);
  const v = j.summary.violations[0];
  expect(v.cycle).toBeUndefined();
  expect(v.via).toBeUndefined();
});

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation
// Verifies: DC-CVI-001, DC-CVI-002
test('a plain dependency violation carries the exact record and no coordinate carrier', async () => {
  const RS = { forbidden: [{ name: 'no-b', severity: 'error', from: {}, to: { path: 'b' } }], allowed: [], required: [] };
  const build = () => result([mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] })] }), mod('b.js')], RS);
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations).toEqual([
    { type: 'dependency', from: 'a.js', to: 'b.js', unresolvedTo: 'b.js', dependencyTypes: ['local'], rule: { name: 'no-b', severity: 'error' } },
  ]);
});

// DependsOn: the four severity counts tally the violations and sum to the list length; an ignore-severity violation counts under ignore and not under error; violations are ordered by ascending severity rank
// Verifies: DC-CVI-001, DC-CVI-002
test('the severity counts and full list agree across a mixed graph', async () => {
  const RS = {
    forbidden: [
      { name: 'e', severity: 'error', from: {}, to: { path: 'b' } },
      { name: 'w', severity: 'warn', from: {}, to: { path: 'c' } },
      { name: 'i', severity: 'info', from: {}, to: { path: 'd' } },
      { name: 'g', severity: 'ignore', from: {}, to: { path: 'e' } },
    ],
    allowed: [],
    required: [],
  };
  const build = () =>
    result(
      [
        mod('a.js', {
          deps: [
            dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'e', severity: 'error' }] }),
            dep('c.js', { module: 'c.js', valid: false, rules: [{ name: 'w', severity: 'warn' }] }),
            dep('d.js', { module: 'd.js', valid: false, rules: [{ name: 'i', severity: 'info' }] }),
            dep('e.js', { module: 'e.js', valid: false, rules: [{ name: 'g', severity: 'ignore' }] }),
          ],
        }),
        mod('b.js'),
        mod('c.js'),
        mod('d.js'),
        mod('e.js'),
      ],
      RS,
    );
  const s = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output).summary;
  expect([s.error, s.warn, s.info, s.ignore]).toEqual([1, 1, 1, 1]);
  expect(s.violations).toHaveLength(4);
  expect(s.error + s.warn + s.info + s.ignore).toBe(s.violations.length);
  expect(s.violations.map((v: Any) => v.rule.name)).toEqual(['e', 'w', 'i', 'g']);
});

// DependsOn: an ignore-severity violation counts under ignore and not under error; the err reporter lists a dependency violation and returns exit code equal to the error count
// Verifies: DC-CVI-001, DC-CVI-002
test('an ignore-severity violation keeps the err exit code at zero and the count under ignore', async () => {
  const RS = { forbidden: [{ name: 'g', severity: 'ignore', from: {}, to: { path: 'b' } }], allowed: [], required: [] };
  const build = () => result([mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'g', severity: 'ignore' }] })] }), mod('b.js')], RS);
  const s = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output).summary;
  const e = await format(build(), { outputType: 'err', ruleSet: RS });
  expect([s.error, s.warn, s.info, s.ignore]).toEqual([0, 0, 0, 1]);
  expect(s.violations).toHaveLength(1);
  expect(e.exitCode).toBe(0);
});

// DependsOn: two identical violation records collapse to one
// Verifies: DC-CVI-001, DC-CVI-002
test('de-duplication leaves one exact violation and one is what json reports', async () => {
  const RS = { forbidden: [{ name: 'no-b', severity: 'error', from: {}, to: { path: 'b' } }], allowed: [], required: [] };
  const build = () =>
    result(
      [
        mod('a.js', {
          deps: [
            dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] }),
            dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] }),
          ],
        }),
        mod('b.js'),
      ],
      RS,
    );
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations).toEqual([
    { type: 'dependency', from: 'a.js', to: 'b.js', unresolvedTo: 'b.js', dependencyTypes: ['local'], rule: { name: 'no-b', severity: 'error' } },
  ]);
});

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation; violations are ordered by ascending severity rank
// Verifies: DC-CVI-001, DC-CVI-002
test('the returned violation list is the same exact value across two independent calls', async () => {
  const first = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output).summary.violations;
  const second = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output).summary.violations;
  expect(first).toEqual(STD_VIOL);
  expect(second).toEqual(first);
});

// DependsOn: violations are ordered by ascending severity rank; violations of equal severity are ordered by rule name
// Verifies: DC-CVI-001, DC-CVI-002
test('severity rank orders error ahead of warning in the exact returned list', async () => {
  const RS = {
    forbidden: [
      { name: 'warn-c', severity: 'warn', from: {}, to: { path: 'c' } },
      { name: 'no-b', severity: 'error', from: {}, to: { path: 'b' } },
    ],
    allowed: [],
    required: [],
  };
  const build = () =>
    result(
      [
        mod('a.js', {
          deps: [
            dep('c.js', { module: 'c.js', valid: false, rules: [{ name: 'warn-c', severity: 'warn' }] }),
            dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] }),
          ],
        }),
        mod('b.js'),
        mod('c.js'),
      ],
      RS,
    );
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations.map((v: Any) => v.rule.severity)).toEqual(['error', 'warn']);
  expect(j.summary.violations.map((v: Any) => v.rule.name)).toEqual(['no-b', 'warn-c']);
});

// DependsOn: the environment block is carried through unchanged; the json reporter serialises the whole result with a two-space indent and exit code zero
// Verifies: DC-CVI-001, DC-CVI-002
test('the environment block survives the json reporter unchanged', async () => {
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  expect(j.summary.environment).toEqual({
    version: '18.2.0',
    nodeVersionSupported: '^42',
    nodeVersionFound: 'v42.0.0',
    osVersionFound: 'riscv pinecil@1.2.3',
    transpilersFound: [],
    extensionsFound: [],
  });
  expect(j.summary.violations).toEqual(STD_VIOL);
});

// DependsOn: a clean graph reports zero on every severity count; the err reporter announces a clean graph and returns exit code zero
// Verifies: DC-CVI-001, DC-CVI-002
test('a clean graph reports an empty list and a zero exit code', async () => {
  const RS = { forbidden: [], allowed: [], required: [] };
  const build = () => result([mod('a.js', { deps: [dep('b.js', { module: 'b.js' })] }), mod('b.js')], RS);
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  const e = await format(build(), { outputType: 'err', ruleSet: RS });
  expect(j.summary.violations).toEqual([]);
  expect([j.summary.error, j.summary.warn, j.summary.info, j.summary.ignore]).toEqual([0, 0, 0, 0]);
  expect(e.exitCode).toBe(0);
});

// DependsOn: an invalid module becomes one module violation from and to itself
// Verifies: DC-CVI-001, DC-CVI-002
test('a module violation pins from and to the same source in the exact record', async () => {
  const RS = { forbidden: [{ name: 'orphan', severity: 'info', from: { orphan: true }, to: {}, comment: 'nobody needs it' }], allowed: [], required: [] };
  const build = () => result([mod('a.js', { orphan: true, rules: [{ name: 'orphan', severity: 'info' }] }), mod('b.js')], RS);
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations).toEqual([{ type: 'module', from: 'a.js', to: 'a.js', rule: { name: 'orphan', severity: 'info' } }]);
  expect([j.summary.error, j.summary.warn, j.summary.info, j.summary.ignore]).toEqual([0, 0, 1, 0]);
});

// DependsOn: a rule name absent from the rule set keeps the default dependency type
// Verifies: DC-CVI-001, DC-CVI-002
test('a missing rule-set entry withholds the comment but not the exact violation record', async () => {
  const RS = { forbidden: [], allowed: [], required: [] };
  const build = () => result([mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'ghost', severity: 'error' }] })] }), mod('b.js')], RS);
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations).toEqual([
    { type: 'dependency', from: 'a.js', to: 'b.js', unresolvedTo: 'b.js', dependencyTypes: ['local'], rule: { name: 'ghost', severity: 'error' } },
  ]);
});

// DependsOn: the json reporter serialises the whole result with a two-space indent and exit code zero; a forbidden dependency on an invalid edge becomes one dependency violation
// Verifies: DC-CVI-001, DC-CVI-002
test('the json output round-trips through the json parser to the same exact violation list', async () => {
  const out = await format(buildStd(), { outputType: 'json', ruleSet: RS_STD });
  const reparsed = JSON.parse(out.output);
  expect(reparsed.summary.violations).toEqual(STD_VIOL);
  expect(out.output).toBe(JSON.stringify(JSON.parse(out.output), null, '  ') + '\n');
  expect(out.exitCode).toBe(0);
});

// DependsOn: two invalid dependencies on one module become two violations; the err reporter lists a dependency violation and returns exit code equal to the error count
// Verifies: DC-CVI-001, DC-CVI-002
test('two distinct edges produce the exact two-violation list and matching err exit', async () => {
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  const e = await format(buildStd(), { outputType: 'err', ruleSet: RS_STD });
  expect(j.summary.violations).toEqual(STD_VIOL);
  expect(e.exitCode).toBe(j.summary.error);
});

// DependsOn: an unresolved specifier surfaces as unresolvedTo distinct from the resolved path
// Verifies: DC-CVI-001, DC-CVI-002
test('the unresolved specifier and the resolved path both appear in the exact record', async () => {
  const RS = { forbidden: [{ name: 'no-x', severity: 'warn', from: {}, to: { path: 'x' } }], allowed: [], required: [] };
  const build = () => result([mod('a.js', { deps: [dep('node_modules/x/index.js', { module: 'x', valid: false, rules: [{ name: 'no-x', severity: 'warn' }] })] })], RS);
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(j.summary.violations).toEqual([
    { type: 'dependency', from: 'a.js', to: 'node_modules/x/index.js', unresolvedTo: 'x', dependencyTypes: ['local'], rule: { name: 'no-x', severity: 'warn' } },
  ]);
});

// DependsOn: a forbidden dependency on an invalid edge becomes one dependency violation
// Verifies: DC-CVI-001, DC-CVI-002
test('a resolved dependency reports the exact record whose unresolvedTo equals the path', async () => {
  const RS = { forbidden: [{ name: 'no-b', severity: 'error', from: {}, to: { path: 'b' } }], allowed: [], required: [] };
  const build = () => result([mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] })] }), mod('b.js')], RS);
  const v = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output).summary.violations[0];
  expect(v.to).toBe('b.js');
  expect(v.unresolvedTo === undefined || v.unresolvedTo === 'b.js').toBe(true);
});

// DependsOn: a structurally invalid result is rejected before any reporter runs
// Verifies: DC-ERR-001, DC-ERR-002
test('an invalid input is rejected identically whichever reporter was asked for', async () => {
  await expect(format({ bad: true }, { outputType: 'json' })).rejects.toThrow();
  await expect(format({ bad: true }, { outputType: 'err' })).rejects.toThrow();
  await expect(format({ bad: true }, { outputType: 'csv' })).rejects.toThrow();
});

// DependsOn: the csv reporter returns an incidence matrix and exit code zero; a forbidden dependency on an invalid edge becomes one dependency violation
// Verifies: DC-CVI-001, DC-CVI-002
test('the csv first cell is empty-quoted and the json list stays exact', async () => {
  const c = await format(buildStd(), { outputType: 'csv', ruleSet: RS_STD });
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  const rows = c.output.split('\n').filter((r) => r.length > 0);
  expect(rows[0].startsWith('""')).toBe(true);
  expect(rows[0].split(',').length).toBe(5);
  expect(rows).toHaveLength(4);
  expect(c.exitCode).toBe(0);
  expect(j.summary.violations).toEqual(STD_VIOL);
});

// DependsOn: the json reporter serialises the whole result with a two-space indent and exit code zero; a forbidden dependency on an invalid edge becomes one dependency violation
// Verifies: DC-CVI-001, DC-CVI-002
test('json exit code stays zero even when the exact list carries an error', async () => {
  const j = await format(buildStd(), { outputType: 'json', ruleSet: RS_STD });
  const parsed = JSON.parse(j.output);
  expect(parsed.summary.violations).toEqual(STD_VIOL);
  expect(parsed.summary.error).toBe(1);
  expect(j.exitCode).toBe(0);
});

// DependsOn: a dependency carrying two rules becomes two violations at one edge
// Verifies: DC-EVAL-001, DC-EVAL-002
test('two rules on one edge produce the exact two-violation list at one edge', async () => {
  const RS = {
    forbidden: [
      { name: 'r1', severity: 'error', from: {}, to: { path: 'b' } },
      { name: 'r2', severity: 'warn', from: {}, to: { path: 'b' }, comment: 'second opinion' },
    ],
    allowed: [],
    required: [],
  };
  const build = () =>
    result([mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'r1', severity: 'error' }, { name: 'r2', severity: 'warn' }] })] }), mod('b.js')], RS);
  const s = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output).summary;
  expect(s.violations).toEqual([
    { type: 'dependency', from: 'a.js', to: 'b.js', unresolvedTo: 'b.js', dependencyTypes: ['local'], rule: { name: 'r1', severity: 'error' } },
    { type: 'dependency', from: 'a.js', to: 'b.js', unresolvedTo: 'b.js', dependencyTypes: ['local'], rule: { name: 'r2', severity: 'warn' } },
  ]);
  expect([s.error, s.warn]).toEqual([1, 1]);
});

// DependsOn: the err-long reporter appends the matched rule comment under the violation; a forbidden dependency on an invalid edge becomes one dependency violation
// Verifies: DC-CVI-001, DC-CVI-002
test('err-long falls back to a dash and json reports the exact record', async () => {
  const RS = { forbidden: [{ name: 'no-b', severity: 'error', from: {}, to: { path: 'b' } }], allowed: [], required: [] };
  const build = () => result([mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] })] }), mod('b.js')], RS);
  const el = await format(build(), { outputType: 'err-long', ruleSet: RS });
  const j = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output);
  expect(el.output).toMatch(/no-b/);
  expect(el.exitCode).toBe(1);
  expect(j.summary.violations).toEqual([
    { type: 'dependency', from: 'a.js', to: 'b.js', unresolvedTo: 'b.js', dependencyTypes: ['local'], rule: { name: 'no-b', severity: 'error' } },
  ]);
});

// DependsOn: the four severity counts tally the violations and sum to the list length; a forbidden dependency on an invalid edge becomes one dependency violation
// Verifies: DC-CVI-001, DC-CVI-002
test('the totals are carried through from the input and the list is exact', async () => {
  const j = JSON.parse((await format(buildStd(), { outputType: 'json', ruleSet: RS_STD })).output);
  expect(j.summary.totalCruised).toBe(3);
  expect(j.summary.totalDependenciesCruised).toBe(2);
  expect(j.summary.violations).toEqual(STD_VIOL);
});

const RS_MIXED = {
  forbidden: [
    { name: 'e', severity: 'error', from: {}, to: { path: 'b' } },
    { name: 'w', severity: 'warn', from: {}, to: { path: 'c' } },
    { name: 'i', severity: 'info', from: {}, to: { path: 'd' } },
    { name: 'g', severity: 'ignore', from: {}, to: { path: 'e' } },
  ],
  allowed: [],
  required: [],
};

const buildMixed = () =>
  result(
    [
      mod('a.js', {
        deps: [
          dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'e', severity: 'error' }] }),
          dep('c.js', { module: 'c.js', valid: false, rules: [{ name: 'w', severity: 'warn' }] }),
          dep('d.js', { module: 'd.js', valid: false, rules: [{ name: 'i', severity: 'info' }] }),
          dep('e.js', { module: 'e.js', valid: false, rules: [{ name: 'g', severity: 'ignore' }] }),
        ],
      }),
      mod('b.js'),
      mod('c.js'),
      mod('d.js'),
      mod('e.js'),
    ],
    RS_MIXED,
  );

// DependsOn: the four severity counts tally the violations and sum to the list length; an ignore-severity violation counts under ignore and not under error; the err reporter lists a dependency violation and returns exit code equal to the error count
// Verifies: DC-CVI-001, DC-CVI-002
test('the err listing covers every non-ignored violation and omits the ignored one', async () => {
  const s = JSON.parse((await format(buildMixed(), { outputType: 'json', ruleSet: RS_MIXED })).output).summary;
  const e = await format(buildMixed(), { outputType: 'err', ruleSet: RS_MIXED });
  expect(s.violations.map((v: Any) => v.rule.name)).toEqual(['e', 'w', 'i', 'g']);
  expect([s.error, s.warn, s.info, s.ignore]).toEqual([1, 1, 1, 1]);
  expect(e.output).toMatch(/error e: a\.js/);
  expect(e.output).toMatch(/warn w: a\.js/);
  expect(e.output).toMatch(/info i: a\.js/);
  expect(e.output).not.toMatch(/ignore g: a\.js/);
  expect(e.exitCode).toBe(1);
});

// DependsOn: the csv reporter returns an incidence matrix and exit code zero; the four severity counts tally the violations and sum to the list length
// Verifies: DC-CVI-001, DC-CVI-002
test('the csv matrix over a five-module graph agrees with the json module count', async () => {
  const j = JSON.parse((await format(buildMixed(), { outputType: 'json', ruleSet: RS_MIXED })).output);
  const c = await format(buildMixed(), { outputType: 'csv', ruleSet: RS_MIXED });
  const rows = c.output.split('\n').filter((r) => r.length > 0);
  expect(j.modules).toHaveLength(5);
  expect(rows[0].split(',')).toHaveLength(7);
  expect(rows).toHaveLength(6);
  expect(c.exitCode).toBe(0);
  expect(j.summary.totalDependenciesCruised).toBe(4);
});

// DependsOn: the err-long reporter appends the matched rule comment under the violation; a dependency carrying two rules becomes two violations at one edge
// Verifies: DC-CVI-001, DC-CVI-002
test('err-long resolves one comment and one dash over the same two-violation edge', async () => {
  const RS = {
    forbidden: [
      { name: 'r1', severity: 'error', from: {}, to: { path: 'b' } },
      { name: 'r2', severity: 'warn', from: {}, to: { path: 'b' }, comment: 'second opinion' },
    ],
    allowed: [],
    required: [],
  };
  const build = () =>
    result([mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'r1', severity: 'error' }, { name: 'r2', severity: 'warn' }] })] }), mod('b.js')], RS);
  const el = await format(build(), { outputType: 'err-long', ruleSet: RS });
  const s = JSON.parse((await format(build(), { outputType: 'json', ruleSet: RS })).output).summary;
  expect(el.output).toMatch(/second opinion/);
  expect(el.output).toMatch(/-/);
  expect(el.exitCode).toBe(1);
  expect(s.violations).toHaveLength(2);
  expect(s.violations.map((v: Any) => v.rule.name)).toEqual(['r1', 'r2']);
});
