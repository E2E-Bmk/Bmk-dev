import { expect, test } from 'vitest';

import { format } from '../subject';
import { dep, mod, result } from '../helpers';

/* The reporter contracts. Text wording is asserted only where the specification
   fixes it; otherwise the assertions read the exit code, the shape, and the
   presence of the coordinates a reporter is required to render. */

const RULE_SET = {
  forbidden: [{
      name: "no-b",
      severity: "error",
      from: {

      },
      to: {
        path: "b"
      },
      comment: "b is off limits"
    }],
  allowed: [],
  required: []
};

function dirtyResult() {
  return result(
    [
      mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: false, rules: [{ name: 'no-b', severity: 'error' }] })] }),
      mod('b.js'),
    ],
    RULE_SET,
  );
}
function cleanResult() {
  return result(
    [mod('a.js', { deps: [dep('b.js', { module: 'b.js', valid: true, rules: [] })] }), mod('b.js')],
    { forbidden: [{ name: 'no-b', severity: 'error', from: {}, to: { path: 'b' } }], allowed: [], required: [] },
  );
}

// Verifies: 
test("the json reporter serialises the whole result with a two-space indent and exit code zero", async () => {
  const out = await format(dirtyResult(), { outputType: 'json', ruleSet: RULE_SET });
  expect(out.exitCode).toBe(0);
  expect(out.output.endsWith('\n')).toBe(true);
  const parsed = JSON.parse(out.output);
  expect(parsed.summary.violations).toHaveLength(1);
  expect(parsed.modules).toHaveLength(2);
  expect(out.output).toBe(JSON.stringify(parsed, null, '  ') + '\n');
});

// Verifies: 
test("the err reporter announces a clean graph and returns exit code zero", async () => {
  const out = await format(cleanResult(), { outputType: 'err', ruleSet: cleanResult().summary.ruleSetUsed });
  expect(out.exitCode).toBe(0);
  expect(out.output).toMatch(/no dependency violations found/);
});

// Verifies: 
test("the err reporter lists a dependency violation and returns exit code equal to the error count", async () => {
  const out = await format(dirtyResult(), { outputType: 'err', ruleSet: RULE_SET });
  expect(out.exitCode).toBe(1);
  expect(out.output).toMatch(/no-b/);
  expect(out.output).toMatch(/a\.js/);
  expect(out.output).toMatch(/b\.js/);
});

// Verifies: 
test("the err-long reporter appends the matched rule comment under the violation", async () => {
  const out = await format(dirtyResult(), { outputType: 'err-long', ruleSet: RULE_SET });
  expect(out.exitCode).toBe(1);
  expect(out.output).toMatch(/b is off limits/);
});

// Verifies: 
test("the csv reporter returns an incidence matrix and exit code zero", async () => {
  const out = await format(dirtyResult(), { outputType: 'csv', ruleSet: RULE_SET });
  expect(out.exitCode).toBe(0);
  expect(out.output.split('\n')[0].startsWith('""')).toBe(true);
  expect(out.output).toMatch(/"a\.js"/);
});

// Verifies: DC-ERR-001, DC-ERR-002, DC-ERR-003
test("an unknown reporter name is rejected before any reporter runs", async () => {
  await expect(format(dirtyResult(), { outputType: 'not-a-reporter', ruleSet: RULE_SET })).rejects.toThrow();
});

// Verifies: DC-ERR-001, DC-ERR-002, DC-ERR-003
test("a structurally invalid result is rejected before any reporter runs", async () => {
  await expect(format({ not: 'a result' }, { outputType: 'json' })).rejects.toThrow();
});

// Verifies: DC-ERR-001, DC-ERR-002, DC-ERR-003
test("an unknown output type is rejected when it cannot be normalised", async () => {
  await expect(format(dirtyResult(), { outputType: 42 })).rejects.toThrow();
});
