---
name: test-filter
description: "Filter and classify a Python test suite for SWE-E2E benchmark scoring. Use when processing a raw test collection to produce a filtered subset with atomic/integration/system_e2e taxonomy and spec-test coverage map. Covers Step 3 (hard filtering + classification) and Step 3.5 (spec_test_map.md + coverage gate) of the benchmark pipeline."
---

# Test Filter

## State Machine Interface

**Entry:** Read `wip/{task}/PIPELINE_STATE.md`. Verify `state` is one of the S3 states. Do not begin work until state is confirmed. If `filter_iter > 2`, stop and escalate.

**Forbidden transition (hard gate):** `S3B_TRIGGER` requires `filter/rewrite_audit.md` to exist. If it does not exist, set `state → S3A_REWRITE` and complete that state before proceeding. Never jump from any S3A state directly to `S3B_TRIGGER` without this file.

**Exit each sub-state:** After completing a sub-state's todo list, set `state` to the next state per Catalogue, reset `todo` to that state's catalogue todo, append History row. Do not skip sub-states.

**Exit (loop):** When looping back (e.g. `S3_REFERENCE_RUN → S3_ORACLE_MERGE`), set `state` to loop target, reset `todo`, increment `filter_iter`, append History row.

---

## Core Criterion

Every filtering decision reduces to two questions. Both must be true to keep a test.

**Q1 — Behavioral?**
> Would a correct reimplementation that uses different internal structures pass this test?

A test that checks exact field names, repr strings, internal maps, exception message wording, or singleton shapes answers No — a correct reimplementation with different internals would fail it. Exclude these regardless of import visibility.

**Q2 — Spec-derivable?**
> Can a senior engineer who has only read the spec infer what this test expects?

A test passes if and only if it can be mapped to a specific point in the spec - explicitly stated, or derivable by a senior engineer from what is stated. If the mapping cannot be written, the test is excluded.

Both criteria are enforced structurally: filling `spec_test_map.md` one row per test **is** the filtering process. A row that cannot be completed means the test fails one or both criteria.

---

## Mechanical Pre-Filter

Scan each test nodeid. Any match -> exclude immediately, no further judgment needed. Scan per nodeid, not per file.

1. **Private import** - imports a private symbol: `from lib._xxx import ...` or `import lib._xxx`
2. **Private assertion** - asserts on a private attribute or accesses `obj._field` / `obj.__dict__`
3. **Environment dependency** - makes network requests, uses absolute filesystem paths, or reads environment variables not injected by the test itself
4. **Fixture side-effect dependency** - setup requires calling public feature A solely to construct input for feature B, where A is not the behavior under test

---

## Filtering Process

For every test nodeid in the suite:

1. Apply the four mechanical pre-filter rules. Any match -> mark `excluded`, record the rule, move on.
2. For tests that pass: attempt to write the `spec_test_map.md` row - identify the spec section or inferrable principle, classify the layer, assign status.
3. If the row cannot be completed -> status is `source-only` or `excluded`.

---

## Classification

| Layer | Definition |
|-------|-----------|
| `atomic` | Tests a single public behavior; no cross-component setup required |
| `integration` | Crosses >=2 public boundaries; fixture constructed directly |
| `system_e2e` | Full user workflow: state established via public API, multiple views verified against the same underlying state |

---

## spec_test_map.md

**Mandatory artifact. Do not skip, defer, or summarize.**

Process each test nodeid one at a time. Write its row in `spec_test_map.md` before moving to the next nodeid. Do not batch-decide or produce the map at the end.

If you are about to score, run tests, or move to the next stage without a complete `spec_test_map.md`, stop: the filtering is not done. A complete map is the only evidence that filtering happened.

For every `covered` row, the `spec_section` value must match a heading that actually exists in `spec_vN.md`. Verify the heading exists before writing the row. A `spec_section` cell that cannot be matched to a real spec heading means Q2 was not properly applied — reclassify the row.

Produced during filtering, not after.

```markdown
| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| tests/test_foo.py::test_bar | atomic | section Public API - foo() | covered | |
| tests/test_foo.py::test_internal | atomic | - | excluded | asserts _cache private attr |
| tests/test_baz.py::test_workflow | system_e2e | section Workflow + section State Invariants | covered | |
```

**Status values:**

| Status | Meaning | Action |
|--------|---------|--------|
| `covered` | In spec, or derivable by a senior engineer from spec | Keep |
| `spec_gap` | Behavior is grounded in public docs or domain conventions, but was omitted from the spec. Any correct reimplementation must satisfy it. The gap is in the spec, not in the library. | Patch spec -> re-label `covered`; patch must pass spec-writer validation |
| `source-only` | Behavior is an arbitrary implementation choice not prescribed by public docs. A different correct implementation could behave differently with equal validity. Includes Q1 failures: tests that check repr format, internal field shapes, exception message wording, or dataclass slots even when the imported name has no underscore prefix. | Exclude |
| `excluded` | Mechanical pre-filter rule match (private `_` import, private assertion, environment dependency, fixture side-effect dependency) or evaluation protocol artifact (score file, prior attempt output, arbitrary format string). | Exclude |

`source-only` and `excluded` are kept separate: high `source-only` count signals the library has implementation-specific behavior not suited for a behavioral spec; high `excluded` signals test quality or protocol issues.

File footer (required):

```
Total: N | kept (covered): N | spec_gap: N | source-only: N | excluded: N | final scoreable: N
```

---

## Rate Checks

**Kept set too small:** if the kept set is small relative to the original suite, investigate before proceeding:
1. Check whether spec is missing a behavior class -> patch spec, reclaim tests
2. Rewrite fixture using public API instead of internal construction
3. Accept a lower count for high unit-test style libraries
4. None of the above -> retire candidate

**Preserved rate is not sufficient alone.** A high preserved rate can be misleading if failures cluster around a few broken primitives or if import provenance was not fully audited. Audit by failure surface and cascade root count, not just the percentage of retained tests.

**Coverage too low:** if a significant share of kept tests are `source-only` after resolution, the library may not be viable - its tests cover behavior that cannot be fairly specified.

When `spec_gap` rows trigger spec patches, patches must pass spec-writer validation (all 5 checks) before the row is re-labeled `covered`.

---

## Parameterized Tests

A parameterized test expands into multiple nodeids but represents one behavior. Report both:

- **Preserved rate**: calculated over distinct test functions (before parametrization)
- **Scoring**: runs over all nodeids

When a large share of nodeids come from parametrized expansion of few functions, note this explicitly - it affects how to interpret the preserved rate.

---

## Output Artifacts

`spec_test_map.md` - primary artifact (format above)

`kept_nodeids.txt` - one nodeid per line, `covered` rows only

`taxonomy.jsonl` - scorer-compatible. Key format must match `score_pytest_original.py` mapping `tests/path.py::test_name` -> `path_stem::test_name`. One JSON object per line:

```jsonl
{"taxonomy_key": "test_foo::test_bar", "layer": "atomic"}
{"taxonomy_key": "test_baz::test_workflow", "layer": "system_e2e"}
```

Key generation algorithm: strip parameter suffixes (e.g. `[case0]`), replace the file path with its stem, and for nested nodeid parts after the file (class name, method name) join them with `.` — e.g. `tests/test_req.py::TestParsing::test_valid` → `test_req.TestParsing.test_valid`.

Before finalizing: dry-run check that `by_layer` counts are non-zero. If all `unknown`, key format is wrong.

---

## Linkage with spec-writer

If a test fails because it checks an arbitrary string format, a specific internal name, or an evaluation protocol artifact -> mark `excluded`, do not patch the spec to compensate.

Only `spec_gap` rows justify patching the spec from within the filtering workflow.

---

## Verifier Builder Extension

## Overview

Stage 3 runs two tracks. Run Track A first. Trigger Track B when Track A yields too few tests or all upstream files are unfixable.

```
Track A: upstream test cleanup  ->  kept_upstream.txt
Track B: coverage-guided generation (Codex subagent / Claude Code)  ->  generated_tests.py

oracle = Track A output + Track B output (merged)
```

---

## Track A - Upstream Test Cleanup

### Step 1: Import audit & public API rewrite (file level)

For every test file, scan top-level imports for non-public dependencies. For each problematic import, ask: **can the test's behavioral intent be preserved by rewriting the setup using only the public API from the spec?**

| Import type | Example | Action |
|---|---|---|
| Standalone test helper | `from tests.util import assert_ppo` | Copy `tests/util.py` into harness env; keep file |
| Package pure constant | `from pkg import _URL_RE` | Inject constant via conftest.py; keep file |
| Upstream test infrastructure | `from pkg.tests.base import BaseTestCase` | Attempt rewrite: replace test helper setup with equivalent public API calls; keep if rewritable, discard if not |
| Library internal (unidirectional) | `from pkg._parser import _P` where `_P` doesn't construct candidate types | Pre-fill from reference; keep file |
| Library internal (bidirectional) | `from pkg._parser import _P` where `_P` constructs types the candidate must implement | Attempt rewrite: replace internal construction with public API setup; keep if rewritable, discard if not |
| In-process runner | `from pkg.main import run` | Attempt rewrite using public CLI/API entry point; discard if runner is the behavior under test |
| Out-of-scope module | `from pkg.other import X` (X not in spec scope) | Discard entire file — out-of-scope behavior cannot be rewritten into scope |

**Rewrite criterion:** a rewrite is valid if (1) the resulting test exercises the same behavioral contract, (2) the setup uses only public API names listed in the spec, and (3) the test would still fail on a wrong implementation. A rewrite that changes what the test actually verifies is not a valid rewrite — discard instead.

**Track B trigger (early):** If >50% of test files are discarded after rewrite attempts (not just before), start Track B immediately in parallel.

### Step 2: Fairness audit (nodeid level)

For each retained nodeid, compare assertion surface against public docs:

**Exclude if assertion checks:**
- exact `repr()` output not specified in docs
- internal object fields or dataclass slots absent from docs
- private attribute names (even if accessible without underscore)
- exact exception message text (exception type is acceptable; message wording is not)
- parser-internal maps, singleton registries, or implementation-shape invariants
- `isinstance(x, InternalClass)` for classes not documented as part of public API

**Keep if assertion checks:**
- return value semantics documented in public API reference
- file / database / stdout side effects from documented public workflows
- exception type from documented error conditions
- public attribute values documented in the API reference or examples

### Step 3: Dummy gate

Run the entire kept set against a dummy implementation (every public function `return None` / `raise NotImplementedError`). Discard any test that passes the dummy - these are structurally trivial, not difficulty evidence.

**Output:** `filter/kept_upstream.txt`

**Track A termination:** if fewer than 30 nodeids remain, or all files were discarded -> proceed to Track B.

---

## Track B - Coverage-Guided Generation

**Trigger conditions:**

Early triggers — start Track B immediately in parallel, do not wait for Track A to finish:
- Step 1 discards >50% of test files after rewrite attempts (import saturation)
- All upstream files discarded at Step 1 (no files survive to per-node filtering)

Late triggers — evaluate after Track A completes, then start Track B:
- Track A final kept count < 30 nodeids
- Track A kept count ≥ 30 but retained set is mostly atomic or implementation-shaped with no integration/system_e2e coverage

Track B may run even when Track A has ≥ 30 kept nodeids if the retained set does not cover the intended integration/system agreement surface.

### Step 1: Run branch coverage on reference

```bash
# Isolated venv with reference package installed (not candidate)
coverage run --branch --source=<pkg> -m pytest filter/kept_upstream.py
coverage json -o filter/coverage.json
```

If Track A produced zero kept tests, run coverage with a minimal smoke import instead:
```bash
coverage run --branch --source=<pkg> -c "import <pkg>"
```

### Step 2: Format gaps for agent

Run `tools/format_coverage.py filter/coverage.json <source_root>` -> produces `filter/coverage_gaps.txt` with uncovered branches annotated with surrounding source lines.

### Step 3: Codex subagent / Claude Code

Give the agent:
- `filter/coverage_gaps.txt`
- `spec/spec_vN.md`
- Execute-only access to the reference implementation (import and run; do not read source files)

Task: exercise the missing branches by calling the reference with varied inputs, observe the actual outputs, then construct assertions from those observations.

Generation protocol:
1. Call `reference_pkg.fn(input)` and record the real return value / side effect
2. Write the test assertion from the observed result, not from spec inference
3. For each generated test, verify: is this I/O relationship derivable from the spec? If not, discard the test — do not add spec content to compensate

Enforce in prompt:
- Execute reference to observe behavior; do not read reference source files
- Assert on the observed return values and side effects only
- No repr, no internal state, no exact error message text
- Each test must assert something that would fail on a wrong implementation

### Step 4: Dummy gate

Same as Track A Step 3. Discard tests that pass dummy stubs.

### Step 5: Reference gate

Run generated tests against the reference implementation. Require >= 95% pass. If lower, return failing tests to the agent for correction.

**Output:** `filter/generated_tests.py`

---

## Merging the Oracle

```
oracle = tests in kept_upstream.txt  +  test functions in generated_tests.py
```

Write `filter/spec_test_map.md` listing all oracle tests with:
- source: `upstream` or `generated`
- taxonomy: `atomic` / `integration` / `system_e2e`
- the spec behavior it covers

If oracle is Track-B-only (no upstream tests survived), mark `filter/oracle_source: generated_only` in spec_test_map.md header. task-judge will apply an additional spot-check gate. Target at least 30 nontrivial tests before Stage 5 qualification; if fewer than 30 are produced, the result is exploratory unless merged with fair upstream tests. Prefer lifecycle combinations that bind multiple public projections over single-behavior checklist rows.

---
