---
name: task-judge
description: "Judge whether a SWE-E2E benchmark task and evaluation run are valid, diagnose model failures, and record model weaknesses. Use after a candidate evaluation run to determine task status (QUALIFIED/BROKEN/CHEAT_DETECTED), produce a diagnosis report, and update the weakness table. Core principle: every scoring test must be spec-driven (traceable to a spec section) and behavioral (checks observable outcomes, not internal structure). Apply this principle before reading any score."
---

# Task Judge

## State Machine Interface

**Entry:** Read `wip/{task}/PIPELINE_STATE.md`. Verify `state` is `S5_JUDGE`. Verify `candidate-runs/.../score_result.json` exists — if not, set `state → S4_EVAL_RUN` and stop.

**Exit (QUALIFIED):** Set `state → QUALIFIED`, append History row, execute QUALIFIED terminal todo.

**Exit (loop — spec gap):** Set `state → S2_SPEC_DRAFT`, increment `spec_iter`, reset `todo`. If `spec_iter > 3`, set `state → RETIRED` instead.

**Exit (loop — filter issue):** Set `state → S3_ORACLE_MERGE`, increment `filter_iter`, reset `todo`. If `filter_iter > 2`, set `state → RETIRED` instead.

**Exit (loop — cheat/env):** Set `state → S4_SETUP`, increment `eval_iter`. If `eval_iter > 2`, set `state → RETIRED` instead.

**Exit (RETIRED):** Set `state → RETIRED`, append History row, execute RETIRED terminal todo.

---

## Core Principle

> **Every test in the scoring set must be spec-driven and behavioral. Apply this before reading any score.**

**Spec-driven**: the test traces to a spec section; its expected outcome is derivable from the spec alone.

**Behavioral**: the test checks observable behavior that any correct reimplementation would produce — not internal field names, repr strings, exception message wording, or implementation-specific shapes.

A failure on a test that violates either condition is a **verifier failure**, not a model failure. The judge uses actual pass/fail results as evidence to audit the instrument: if a cluster of failures aligns with undocumented internal shapes, that is a signal about test quality, not model capability.

**Do not interpret scores before verifying the instrument against these two conditions.**

---

## Hard Checks

All three must pass for any results to be considered valid.

### 0. Role Boundary

The judge reads artifacts and produces verdicts. The judge does not modify oracle files, add test cases, or strengthen kept_nodeids.txt. Any gap found during judging must be returned to test-filter via `filter_correction_request.md` (filter_iter + 1). Adding a test case to the oracle and then judging against it in the same pass is invalid.

### 1. Anti-Cheat

Before reading any score, run an import provenance preflight:

```bash
python -c "import <pkg>; print(<pkg>.__file__)"
```

**Write the literal output of this command into your diagnosis report as a `Preflight output` block before opening any score file or quoting any score value.** If this block is absent from your report, the report is structurally invalid — do not proceed.

This must point into the candidate solution directory, not the oracle worktree or any installed package. If running pytest from a copied source worktree, `sys.path[0]` may shadow `PYTHONPATH` — use `--remove-path <package>` when invoking pytest, or confirm via the preflight above before accepting any score. If provenance check fails, fix the environment and re-run.

**High-score mandatory probe:** for any run where candidate pass rate ≥ 95%, the preflight probe is not optional — it is a prerequisite for reading any score value. If the probe output shows `__file__` pointing outside the candidate solution directory, the run is invalid regardless of score. Record the probe output verbatim in the diagnosis report before citing any number.

Then scan the agent's full trajectory/log for any access to information the model should not have. Any match -> mark run `CHEAT_DETECTED`, discard score.

Forbidden access patterns:
- Reading any file under the source repo path (`repo-pool/`, oracle worktrees, reference environments)
- `pip install <target-library>` or any install that pulls the target package
- Reading test files or fixture files containing expected values
- Reading score reports, prior attempt outputs, or any evaluation artifact from earlier runs
- Importing the target library from a non-candidate path (confirmed by the preflight above)
- Reading the spec_test_map.md or kept_nodeids.txt during the implementation phase

A high-scoring run with any of the above is invalid regardless of score.

---

### 2. Solvability

Run the reference implementation against the scoring set in a **library-specific dependency environment** — not a generic shared environment. Missing dependencies (e.g. sqlite_fts4, optional pytest plugins) will produce collection errors or 0% pass rates that are environment failures, not task failures.

If reference pass rate is significantly below the scoring set size:
1. Diagnose first: check for missing dependencies, pytest plugins, or environment misconfiguration — fix environment
2. Re-run; if still low, the scoring set has broken tests -> return to test-filter for remediation
3. Do not label a task QUALIFIED until reference passes at a high rate (>= 95%)

**Relationship to Stage 3 reference gate:** Stage 3 (S3_REFERENCE_RUN) requires **100%** pass rate as the oracle construction gate — any failure there means the oracle itself is broken. Stage 5 re-checks at **≥95%** as a solvability sanity check in the actual scoring environment; residual failures (≤5%) after environment setup may reflect optional-behavior tests that are acceptable caveats. If S5 reference is below 95%, treat as environment failure — do not proceed to scoring.

---

### 3. Fairness

**Gate A — Spec mapping spot-check**

Sample a subset of `covered` rows from `spec_test_map.md`. For each sampled test, record a four-column table:

| nodeid | assertion summary | spec_section | verdict |
|--------|------------------|--------------|---------|

The `spec_section` cell must quote the exact heading from the spec file. The `verdict` cell is `derivable` only if a senior engineer reading that section could predict the test outcome without any other information. Writing `derivable` without quoting the spec section is invalid — the row must be completed in full or the spot-check does not count.

If spot-check finds incorrect mappings → return to test-filter to correct the map.

**Gate B — Failure pattern audit**

After scoring, sample failing tests and check whether failures are consistent with the two principles:
- Are failures traceable to documented spec behavior? If not, the test is checking undocumented internal shapes — verifier failure, not model failure.
- Do failures represent observable behavioral gaps, or internal structure mismatches (exact field names, repr format, exception message wording)?

If the majority of failures cluster around undocumented atomic internal shapes, return a `filter_correction_request.md` to test-filter — this is a BROKEN/fairness verdict, not a model capability signal.

**Gate C — Generated-only oracle spot-check**

If `spec_test_map.md` header contains `oracle_source: generated_only`, manually sample >= 5 generated tests and record a four-column table for each:

| nodeid | assertion summary | spec_section | verdict |
|--------|------------------|--------------|---------|

Apply both core principles per row:
- **Spec-driven**: is the assertion's expected value derivable from the quoted `spec_section`? Mark `circular` if the generator inferred the value from its own spec reading rather than from reference execution.
- **Behavioral**: would a correct reimplementation with different internals pass this test? Mark `internal-shape` if the test checks repr format, internal field names, or exact error message text.

Any `circular` or `internal-shape` verdict → return `filter_correction_request.md` to test-filter for regeneration.

**Gate D — Coverage Gap Audit**

For each H2/H3 section in the spec, check whether `spec_test_map.md` contains at least one `covered` row mapping to that section. List any uncovered sections:

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|

Coverage verdict:
- **FULL** — 0 spec sections with zero coverage
- **PARTIAL** (acceptable) — 1–2 secondary sections uncovered; no core invariant section is empty
- **GAP** (requires action) — any core invariant section (`Cross-View Invariants`, `Error Semantics`, state lifecycle sections) has zero coverage

On a GAP verdict: issue a `filter_correction_request.md` routing back to test-filter with the list of uncovered sections. Test-filter must generate additional tests for each GAP section until per-section minimums are met (see test-filter SKILL). Do not issue QUALIFIED with an unresolved GAP. A GAP may only be accepted as a caveat (recorded in `task.json` under `coverage_gap`) if test-filter has already attempted generation and confirmed no further spec-derivable tests can be produced for those sections without introducing circular assertions — this exception must be explicitly stated in the diagnosis report.

---

## Task Labels

Not gates. Attach to the task record for downstream analysis of benchmark quality and model capability patterns.

Derive labels from what you actually observe — do not limit yourself to a fixed list. Good labels are specific claims about the task's measurement properties or the model's failure pattern, grounded in evidence from the run.

Examples of the kind of labels that carry signal:
- `discriminating` — score spread exists across models; task differentiates capability
- `trivially-solved` — SOTA pass rate near ceiling; limited benchmark value
- `too-hard` — all models near floor; may indicate spec gap or task difficulty mismatch
- `composition-signal` — at least one failure traceable to cross-component state drift, not primitive cascade
- `cascade-dominated` — most integration/system failures explained by a small number of broken primitives
- `saturated-candidate-score` — candidate pass rate = 100%; combine with `trivially-solved` when saturation is confirmed
- `coverage-gap` — one or more core invariant spec sections have no oracle coverage (Gate D)

These are examples, not an exhaustive set. If the evidence suggests a label not listed here, add it.

**Saturation heuristic (mandatory check when candidate pass rate = 100%):** If the candidate consolidates the upstream package into significantly fewer files than the original (e.g. 4 files vs 20+) AND achieves 100% pass rate, apply both `trivially-solved` and `saturated-candidate-score`. Record in the diagnosis report that the run pattern is consistent with recall from training data rather than reconstruction from spec. This does not block QUALIFIED but must appear in MANIFEST caveats.

---

## REOPENED_S3 Protocol

If any oracle file (kept_nodeids.txt, taxonomy.jsonl, spec_test_map.md) is modified after a task has reached QUALIFIED status:

1. Set `state → REOPENED_S3` in PIPELINE_STATE.md.
2. Add `superseded_by: {new_oracle_version}` to the existing CANDIDATES.md QUALIFIED row — do not overwrite it.
3. Invalidate the existing score_result.json by renaming it `score_result_superseded_{date}.json`.
4. Re-run Stage 4 → Stage 5 against the new oracle before reinstating QUALIFIED.

The transition `QUALIFIED → QUALIFIED` (same state, updated oracle, no re-run) is explicitly forbidden.

---

## Diagnostic Procedure

Work through failures in two passes.

**Pass 1 — Instrument validity**

Before attributing any failure to the model, verify each failure cluster satisfies the two principles:

| Question | Answer | Action |
|----------|--------|--------|
| Does the failed test trace to a spec section? | No | Verifier failure — return to test-filter, mark excluded |
| Would a correct reimplementation with different internals pass this test? | No | Verifier failure — test checks internal structure, return to test-filter |
| Both yes | — | Proceed to Pass 2 |

If a significant share of failures fail Pass 1, set task status to `BROKEN` (fairness) and issue `filter_correction_request.md`. Do not score the run as QUALIFIED difficulty evidence.

**Negative Gap diagnostic:** If the candidate's atomic pass rate is lower than its integration pass rate, diagnose the cause before finalizing:
- Are atomic failures caused by ImportError/collection errors on paths not in spec? → Flag as Q1 violation, return to Stage 3 for test cleanup
- Are atomic failures genuine assertion errors (model implemented the function but got behavior wrong)? → Normal model weakness, proceed
- Are integration tests passing because they're too weak (only check "no exception" without verifying behavior)? → Flag as test quality issue, return to Stage 3
Document the diagnosis in the judge report.

**Spec adequacy check for integration failures:** For each failed integration/system_e2e test, verify that the spec contains the cross-module constraint being tested. If the spec does not describe the interaction that failed, this is a spec gap (not a model failure) — issue a spec_patch_request to add the missing constraint, then re-evaluate.

**Pass 2 — Model failure analysis**

For every failure cluster that passed Pass 1:

**Step 1 — Is this a protocol issue or a model issue?**

For each failure, ask two questions in sequence:

**Q-A:** Does the candidate's output match what the spec says should happen?
- Yes → the model implemented the spec correctly. Proceed to Q-B.
- No → the model diverged from the spec. Mark as real model failure (Step 3).

**Q-B (only when Q-A = Yes):** Does the reference implementation pass this test?
- No → the test's expected value is wrong even for the reference; this is a verifier failure — return to test-filter, mark `excluded`.
- Yes → the reference passes but the spec-compliant candidate fails. **The spec has a factual error** (it documents a behavior different from what the reference actually does). Issue `spec_patch_request.md` with `type: spec_error` and route to spec-writer.

**Legacy branch (when Q-A cannot be answered — spec is silent or ambiguous):**
- Spec is ambiguous or incomplete → spec gap; issue `spec_patch_request.md` with `type: spec_gap`.
- Arbitrary format / internal name in test → mark `excluded` in spec_test_map.md.

**Step 2 — Protocol issues**

| Type | Detected by | Action |
|------|-------------|--------|
| Spec has a factual error (Q-A=Yes, Q-B=Yes) | Reference passes; spec-compliant candidate fails | `spec_patch_request.md` type=spec_error → spec-writer |
| Spec is ambiguous or incomplete | Spec is silent; test is behaviorally valid | `spec_patch_request.md` type=spec_gap → spec-writer |
| Arbitrary format / internal name in test | Q-A=Yes, Q-B=No | Mark `excluded` in spec_test_map.md |

**Step 3 — Real model failures**

For each real failure, record:
- Which layer it's in (atomic / integration / system_e2e)
- Root cause category (see capability dimensions below)
- Whether other failures cascade from this one

Distinguish: a broken import or missing class can cascade into dozens of test failures. Count root failures, not cascaded failures. Low integration/system scores caused by missing primitives or import-surface failures are cascade, not composition signal — only failures that cannot be explained by a missing primitive count as cross-component state evidence.

---

## Capability Dimensions

Used for weakness table entries. Assign one primary dimension per failure cluster:

| Dimension | What it covers |
|-----------|---------------|
| `api-surface` | Missing or wrong public import paths, function names, class names |
| `atomic-behavior` | Single-function correctness: wrong output, wrong default, wrong type |
| `error-semantics` | Wrong exception type, wrong trigger condition, missing raise |
| `state-management` | Incorrect lifecycle, mutation not persisted, stale state |
| `cross-view-consistency` | Two public projections of the same fact disagree |
| `workflow-completeness` | Full end-to-end workflow fails; partial implementation |

---

## Integration Gap Metrics

The judge produces two complementary gap measurements, both recorded in `task.json`:

**1. Rate-difference (quick screening):**
```json
"integration_gap": {
  "atomic_rate": 0.87,
  "integration_e2e_rate": 0.62,
  "rate_gap": 0.25
}
```

**2. True Integration Gap Events (paper-level narrative):**
A True Integration Gap Event occurs when an integration/system_e2e test fails, but ALL atomic tests that exercise its depended primitives pass. This isolates architectural composition failures from primitive cascade.

```json
"true_gap_events": [
  {
    "failed_test": "test_workflow::test_full_pipeline",
    "layer": "integration",
    "depended_atomic_tests": ["test_foo::test_parse", "test_bar::test_emit"],
    "all_depended_pass": true,
    "root_cause_dimension": "cross-view-consistency"
  }
]
```

To compute: for each failed integration/e2e test, identify which atomic-layer behaviors it exercises (via spec_test_map.md section overlap). If all those atomic tests passed → record as a True Gap Event.

Rate-difference is always computed. True Gap Events are computed for QUALIFIED tasks where rate_gap > 0 and sufficient dependency mapping exists.

---

## Output Artifacts

### Task Status

One of:
- `QUALIFIED` - all hard checks pass, scoring set is valid. Track-B-only oracles with fewer than 30 tests are not QUALIFIED; treat as `small-oracle/exploratory` until the verifier is expanded or merged with upstream tests.
- `BROKEN` - solvability or fairness check failed; task needs repair
- `CHEAT_DETECTED` - forbidden access found in trace; run is invalid

### Diagnosis Report

Per evaluation run, a structured narrative covering:
1. Anti-cheat scan result
2. Reference pass rate and environment notes
3. Candidate score by layer (atomic / integration / system_e2e)
4. Protocol issues found and actions taken
5. Real failure clusters with root cause and dimension
6. Cascade analysis: how many failures root in how many root causes

### Weakness Recording

**Weakness recording:** When the verdict is QUALIFIED, identify model failure dimensions from the candidate score and write them directly into `task.json` as:
```json
"weaknesses": [
  {"dimension": "cross-view-consistency", "description": "...", "affected_tests": 8, "layer": "system_e2e"},
  {"dimension": "error-semantics", "description": "...", "affected_tests": 3, "layer": "atomic"}
]
```

`task.json.weaknesses` is the sole authority for model failure records. Do not maintain a separate `weakness_table.md` — that file is deprecated.

The description should name the specific behavior gap, not just the test names. This is the material for paper discussion about model capability.
