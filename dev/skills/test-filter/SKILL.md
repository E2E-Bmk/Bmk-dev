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

**Q1 strict enforcement for atomic tests:** Atomic tests may only import through entry points explicitly described in the spec's prose (the "Public Interface > Import Surface" section or equivalent). If a test imports from a sub-module path not mentioned in the spec text, it violates Q1 regardless of whether the path has an underscore prefix. The test: "if the model puts this function in a different sub-module (behavior identical), would this test fail due to ImportError?" — if yes, exclude.

**Q2 — Spec-derivable?**
> Can a senior engineer who has only read the spec infer what this test expects?

A test passes if and only if it can be mapped to a specific point in the spec - explicitly stated, or derivable by a senior engineer from what is stated. If the mapping cannot be written, the test is excluded.

Both criteria are enforced structurally: filling `spec_test_map.md` one row per test **is** the filtering process. A row that cannot be completed means the test fails one or both criteria.

**Clause traceability (for tasks whose spec has a `clauses.md` sidecar):** every test ADDED or MODIFIED after the SDD clause discipline shipped must name the clause IDs it verifies in its docstring — `Verifies: KEDRO-SCAF-003, KEDRO-SCAF-004`. A test that cannot name a supporting clause is either checking an implementation detail (exclude it) or has found a genuine spec gap (route a `spec_gap` patch through spec-writer first, then cite the new clause). The reverse query — clauses with no covering test — is the standing ADD-TEST backlog.

**Shared-helper contract audit (mandatory):** enumerate every CLI flag, keyword argument, environment variable, file-layout convention, and output-format assumption used by shared helpers/fixtures (`run_*` wrappers, project scaffolders, `conftest.py`). Each one must be either stated in the spec or Q2-derivable. One unstated helper convention zeroes an entire layer for every model at once (observed: `--colored no`, `python -m` entry, `regex_subs=`); helpers concentrate risk and get audited first, before per-test rows.

---

## Mechanical Pre-Filter

Scan each test nodeid. Any match -> exclude immediately, no further judgment needed. Scan per nodeid, not per file.

1. **Private import** - imports a private symbol: `from lib._xxx import ...` or `import lib._xxx`
2. **Private assertion** - asserts on a private attribute or accesses `obj._field` / `obj.__dict__`
3. **Environment dependency** - makes network requests, uses absolute filesystem paths, or reads environment variables not injected by the test itself
4. **Fixture side-effect dependency** - setup requires calling public feature A solely to construct input for feature B, where A is not the behavior under test
5. **Duplicate top-level import** — two or more `from X import ...` statements at module level import the same symbol name. Shadowed imports cause unpredictable behavior during test collection. Consolidate into a single import line per symbol.
6. **Missing fixture file** — test references a file via `Path(__file__).parent / 'subdir' / 'file'` but the referenced path does not exist in the oracle directory. Missing fixtures cause unconditional test failures that are environment artifacts, not model capability signals.

---

## Filtering Process

For every test nodeid in the suite:

1. Apply the six mechanical pre-filter rules. Any match -> mark `excluded`, record the rule, move on.
2. For tests that pass: attempt to write the `spec_test_map.md` row - identify the spec section or inferrable principle, classify the layer, assign status.
3. If the row cannot be completed -> status is `source-only` or `excluded`.

---

## Assertion Kind (mandatory per test)

Layer answers "how many components does this test cross"; assertion kind answers "what does passing prove". Both are required, they are orthogonal, and the gap metric depends on both.

| Kind | Definition | Dummy-passable? |
|------|-----------|-----------------|
| `positive` | At least one assertion checks a produced value or observable side effect: equality/membership on returns, file/db/stdout content, exit code == 0 | No |
| `failure_path` | All checks verify rejection: `pytest.raises`, `assert not x`, `is False`/`is None`, non-zero exit codes, exception-shaped helper calls | Yes — an implementation that rejects everything passes |
| `shape` | All checks are existence/type only: `isinstance`, `hasattr`, `callable` | Yes |
| `no_check` | No assertion-like construct | Yes |

Classify through helper indirection: a test whose only check is a call to `_assert_usage_failure(...)` is `failure_path`, not `positive`. Trace what the helper asserts.

**Hard gates (enforced by `verify_task.py` at release):**
- Atomic layer: `positive` share >= 60%. A layer dominated by failure_path can be passed by a stub that raises everywhere — it stops measuring "primitives work" and fabricates Integration Gap. (Observed: a task whose 20/20 atomic tests all asserted usage failures gave near-free atomic points to every model.)
- `no_check` tests: zero tolerance in either layer. "Constructor does not raise" smoke tests must gain a value assertion or be excluded.
- `failure_path` tests are legitimate (error semantics are spec content) but belong mostly to the layer whose spec section they verify, and their pass rates are reported separately from the positive gap.

---

## Classification

| Layer | Definition |
|-------|-----------|
| `atomic` | Tests a single public behavior; no cross-component setup required |
| `integration` | Crosses >=2 public boundaries; fixture constructed directly |
| `system_e2e` | Full user workflow: state established via public API, multiple views verified against the same underlying state |

**Classification examples (use as reference):**

| Test pattern | Layer | Rationale |
|---|---|---|
| `assert parse("yesterday") == date(...)` | atomic | Single function, one behavior |
| `MockBackend() → ConnectionPool() → pool.request()` | integration | Pool crosses into backend + stream; mock replaces network |
| `subprocess.run(["cli", "run", ...])` then check stdout + file output | system_e2e | Full user workflow from CLI entry through file side effects |
| `Config(sources=[A, B]) → settings.get(key)` | integration | Two components (loader + getter) cooperating |
| `VCR.use_cassette() → requests.get() → assert cassette.responses` | system_e2e | State written via interception, read via cassette API, cross-view |
| `URL("http://example.com").host` | atomic | Single object attribute access |
| `Connection.request() → Response.read()` on same connection | integration | Two public objects linked by network stream state |

When in doubt: if removing one component's implementation would prevent the test from running at all (not just failing), it's integration or higher.

---

## spec_test_map.md

**Mandatory artifact. Do not skip, defer, or summarize.**

Process each test nodeid one at a time. Write its row in `spec_test_map.md` before moving to the next nodeid. Do not batch-decide or produce the map at the end.

If you are about to score, run tests, or move to the next stage without a complete `spec_test_map.md`, stop: the filtering is not done. A complete map is the only evidence that filtering happened.

For every `covered` row, the `spec_section` value must match a heading that actually exists in `spec_vN.md`. The spec now uses a 6-layer structure (see `Spec2Repo/docs/SPEC_STANDARD.md`): Context (Product Overview, Non-Goals), Orientation (Representative Workflows), Behavior (domain sections), Contract (State Model, Error Semantics, Cross-View Invariants), Reference (Public Interface), Meta (Appendix A/B). Verify the heading exists before writing the row. A `spec_section` cell that cannot be matched to a real spec heading means Q2 was not properly applied — reclassify the row.

Produced during filtering, not after.

```markdown
| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| tests/test_foo.py::test_bar | atomic | positive | section Public API - foo() | covered | |
| tests/test_foo.py::test_internal | atomic | positive | - | excluded | asserts _cache private attr |
| tests/test_foo.py::test_bad_input | atomic | failure_path | section Error Semantics | covered | |
| tests/test_baz.py::test_workflow | system_e2e | positive | section Workflow + section State Invariants | covered | |
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

**Kept set too large:** if the kept set exceeds ~150 base nodeids, provide an explicit argument that the spec can cover the entire retained surface in behavioral language. A large oracle forces the candidate to reconstruct a near-complete API in one pass — if the spec cannot describe all of it without becoming a fill-in-the-blanks template, scope down to a core workflow subset and re-filter. The oracle size should match what the spec can honestly specify, not the full upstream test suite.

**Preserved rate is not sufficient alone.** A high preserved rate can be misleading if failures cluster around a few broken primitives or if import provenance was not fully audited. Audit by failure surface and cascade root count, not just the percentage of retained tests.

**Per-layer minimum count:** The final oracle must contain at least 15 atomic tests AND at least 15 integration+system_e2e tests. If either layer falls below 15 after filtering, return to Track B generation targeting the deficient layer until the minimum is met. This ensures Integration Gap computation has statistical significance (each layer needs enough samples to avoid >10% random fluctuation from a single test).

**Per-layer composition floor:** After the per-layer minimum, check assertion-kind composition: atomic `positive` share >= 60% and zero `no_check` in both layers (see Assertion Kind section). A deficient atomic layer is fixed by generating positive-behavior tests for the same primitives (call the reference, observe the produced value, assert it), not by deleting failure_path tests.

**Coverage too low:** if a significant share of kept tests are `source-only` after resolution, the library may not be viable - its tests cover behavior that cannot be fairly specified.

**Test collection safety:** Before finalizing the oracle, run `pytest --collect-only` against all oracle test files to verify they can be parsed and imported without errors. Collection failures (ImportError, SyntaxError, missing fixtures) zero an entire layer's score for ALL models — they are the highest-impact bugs in the oracle. Fix all collection errors before proceeding.

When `spec_gap` rows trigger spec patches, patches must pass spec-writer validation (all 25 checks) before the row is re-labeled `covered`.

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

**Scorer isolation requirement:** All evaluation runs against `kept_nodeids.txt` must use `--remove-path <pkg>` (or equivalent isolation flag) to prevent a system-installed copy of the target package from shadowing the candidate solution. Record the isolation method in `task.json` under `oracle.scorer_isolation`. Scores produced without this flag are invalid and must be discarded.

`taxonomy.jsonl` - scorer-compatible. Key format must match `score_pytest_original.py` mapping `tests/path.py::test_name` -> `path_stem::test_name`. One JSON object per line:

```jsonl
{"taxonomy_key": "test_foo::test_bar", "layer": "atomic"}
{"taxonomy_key": "test_baz::test_workflow", "layer": "system_e2e"}
```

### Oracle File Layout (tasks/{task-id}/oracle/)

When a task graduates to `tasks/`, its oracle directory must contain exactly two test files split by taxonomy layer:

```
oracle/
├── test_atomic.py        # all "atomic" layer tests
├── test_integration.py   # all "integration" + "system_e2e" layer tests
├── conftest.py           # shared fixtures (optional, only if needed)
└── requirements.txt      # test runtime dependencies (pytest, mocks, etc.)
```

**Split rules:**
- Each test function goes into the file matching its taxonomy layer
- Helper functions, fixtures, and imports used by both files may be duplicated in each, or placed in `conftest.py`
- Test function names must not change (must still match `kept_nodeids.txt`)
- File headers: `# Spec2Repo oracle - atomic tests for {task-id}` / `# Spec2Repo oracle - integration tests for {task-id}`

**Rationale:** This split enables direct computation of Integration Gap = (atomic pass rate) − (integration pass rate) without post-hoc taxonomy lookup. The scorer can run each file independently.

**Oracle atomic update rule:** whenever any oracle file is modified after Stage 3 completes (including retro additions), all four files (kept_nodeids.txt, taxonomy.jsonl, spec_test_map.md, reference_score) must be updated together and assigned a new `oracle_version` timestamp in spec_test_map.md header. Partial updates that leave counts inconsistent across files are invalid.

**Dependency extraction (required before leaving Stage 3):** Extract test runtime dependencies from the upstream repository's `pyproject.toml` (test extras or dev dependencies). Write these to `oracle/requirements.txt`, excluding the target package itself (that's what the candidate implements). If the upstream repo has no explicit test extras, inspect test file imports for third-party packages and list them manually.

**Preservation rule:** do not delete the `wip/{task}/` directory after a task reaches QUALIFIED. The wip directory is the audit trail. Its removal makes evaluation scores permanently unverifiable.

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

**Shared fixture and helper file cleanup (mandatory before node-level work):** Before processing any test file, scan every shared fixture file (`tests/conftest.py`, `tests/helpers.py`, `tests/util.py`, and any file imported by multiple test files) for private imports. Remove or replace each private import with a public-API equivalent in-place. If a helper function cannot be expressed without private API, remove that function and mark any test that calls it as `excluded`. This step must complete before per-function work begins — a shared helper with an unresolved private import will cause cleanroom collection failure for every test that imports it, even if those tests are otherwise clean.

**Per-function atomic extraction (unit test files):** When a unit test file has private module-level imports that cannot be removed at file level, do not discard the entire file. Instead, scan **every** test function in the file individually — not a sample, not a selection of easy ones:
1. Does the function body reference any private symbol? If yes, mark `excluded` in `candidate_filter_map.md` with the specific private symbol.
2. If the function body uses only public API names from the spec, extract it into `filter/rewritten_upstream_tests.py` with corrected imports (public paths only), and classify as `atomic` layer.

This recovers atomic-layer coverage from otherwise-excluded unit test files. The extracted functions must satisfy the same rewrite criterion as file-level rewrites: behavioral intent preserved, setup uses only public API, test would still fail on a wrong implementation.

**Rewrite criterion:** a rewrite is valid if (1) the resulting test exercises the same behavioral contract, (2) the setup uses only public API names listed in the spec, and (3) the test would still fail on a wrong implementation. A rewrite that changes what the test actually verifies is not a valid rewrite — discard instead.

**Execution requirement:** the rewrite audit (`rewrite_audit.md`) records decisions; it does not constitute the rewrite. Actual rewritten test code must appear in `filter/rewritten_upstream_tests.py`. A file marked "retain with rewrite plan" in the audit that has no corresponding functions in `rewritten_upstream_tests.py` has not been rewritten. After Step 1 and Step 2 complete, every function in every retained file must appear either in `rewritten_upstream_tests.py` (kept) or in `candidate_filter_map.md` with status `excluded` (with reason). Functions that appear in neither are processing gaps — go back and handle them before proceeding.

**Track B trigger (early):** If >50% of test files are discarded after rewrite attempts (not just before), start Track B immediately in parallel.

**State update (required before leaving Step 1):** Count the total number of test functions across all retained files (sum from `rewrite_audit.md` summary row). Write this value to `PIPELINE_STATE.md` as `functions_in_scope`. This value is set once and becomes readonly — do not update it in later steps.

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

Run the entire kept set against a dummy implementation (every public function `return None` / `raise NotImplementedError`). Discard any test that passes the dummy — these are structurally trivial, not difficulty evidence.

**Execution requirement:** the dummy gate must be a real pytest invocation — not a structural code review or manual inspection. A "structural audit" does not substitute.

**Interpretation rule:** if the dummy run produces collection errors (not just failures), this is a carrier-block signal, not a pass. A dummy that cannot even import means the test harness depends on private implementation details that will not exist in any clean candidate environment. Treat this as a hard blocker: diagnose the carrier dependency before continuing. Do not record collection errors as "passed dummy gate."

**Output:** `filter/kept_upstream.txt`

**State update (required before leaving Step 3):** Count functions in `filter/rewritten_upstream_tests.py` → write to `PIPELINE_STATE.md` as `functions_kept`. Count `excluded` rows in `candidate_filter_map.md` → write as `functions_excluded`. Verify `functions_kept + functions_excluded = functions_in_scope` before continuing. Mismatch → go back to Step 2 and account for the missing functions.

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

Run `python Bmk-dev/tools/format_coverage.py filter/coverage.json <source_root>` -> produces `filter/coverage_gaps.txt` with uncovered branches annotated with surrounding source lines.

### Step 3: Codex subagent / Claude Code

Give the agent:
- `filter/coverage_gaps.txt`
- `spec/spec_vN.md`
- Execute-only access to the reference implementation (import and run; do not read source files)

Task: exercise the missing branches by calling the reference with varied inputs, observe the actual outputs, then construct assertions from those observations.

**Minimum coverage quota:** Before calling the agent, enumerate every H2/H3 section in `spec_vN.md`. For each section, count how many tests in `kept_upstream.txt` already cover it. Apply the following per-section minimums — any section below its floor is a mandatory generation target:

| Section type | Minimum tests |
|---|---|
| `Cross-View Invariants` | ≥ 5 |
| `Error Semantics` | ≥ 3 |
| Main workflow / Representative Workflows | ≥ 3 |
| All other sections | ≥ 3 |

**Global floor:** the combined oracle (Track A + Track B) must contain at least **50 scoreable tests** before proceeding to Stage 4. If the merged oracle is below 50 after Track B, return to generation and expand coverage until the floor is met or all mandatory targets are saturated. A sub-50 oracle may still proceed only if every spec section is at or above its per-section minimum and no further test generation is possible without introducing circular assertions — record the shortfall as a caveat in `spec_test_map.md` header.

A flat target of 12–30 total tests is insufficient for any library with more than 5 spec sections — the quota is per-section and subject to the global floor.

Generation protocol:
1. Call `reference_pkg.fn(input)` and record the real return value / side effect
2. Write the test assertion from the observed result, not from spec inference. Keep test code natural — do not embed spec phrases or section names inside test code.
3. For each generated test, fill its `spec_test_map.md` row immediately: identify the `spec_section` heading it maps to. If the row cannot be completed (no spec section covers this behavior), discard the test — do not add spec content to compensate. The derivability check lives in the map row, not in the test code.
4. After generation, verify each mandatory target section meets its per-section minimum and total oracle ≥ 50. If either fails, return to generation.

Enforce in prompt:
- Execute reference to observe behavior; do not read reference source files
- Assert on the observed return values and side effects only
- No repr, no internal state, no exact error message text
- Each test must assert something that would fail on a wrong implementation
- Docstring names the spec clause IDs verified (`Verifies: <ID>, <ID>`) when the task has a `clauses.md` sidecar

**Layer-role targets (construct: integration capability; spec-to-repo is the instrument):**
- `atomic` is the control condition — its job is complete coverage of unit behavior (so "units work" is a credible premise) and a reliable floor (dummy fails everything). Depth means covering the parameter domain, error taxonomy, and single-object state cycles that the spec states — not manufacturing difficulty.
- `integration`/`system_e2e` carry the discriminative load — target cross-component composition, cross-view state consistency, and multi-step workflows.
- Deep-water tests stay within their layer: same-object parameter interactions and single-object lifecycles are atomic; cross-API joint decisions and cross-view consistency are integration. Depth is orthogonal to layer.

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

If oracle is Track-B-only (no upstream tests survived), mark `filter/oracle_source: generated_only` in spec_test_map.md header. task-judge will apply an additional spot-check gate. Prefer lifecycle combinations that bind multiple public projections over single-behavior checklist rows.

**State update (required before leaving oracle merge):** Count all `covered` rows in `spec_test_map.md` → write to `PIPELINE_STATE.md` as `oracle_count`. If `oracle_count < 50`, do not proceed to S4_SETUP — return to Track B generation to expand coverage.

---
