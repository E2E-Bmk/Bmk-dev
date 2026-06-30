---
name: task-judge
description: "Judge whether a SWE-E2E benchmark task and evaluation run are valid, diagnose model failures, and record model weaknesses. Use after a candidate evaluation run to determine task status (QUALIFIED/BROKEN/CHEAT_DETECTED), produce a diagnosis report, and update the weakness table. Core principle: every scoring test must be spec-driven (traceable to a spec section) and behavioral (checks observable outcomes, not internal structure). Apply this principle before reading any score."
---

# Task Judge

## Core Principle

> **Every test in the scoring set must be spec-driven and behavioral. Apply this before reading any score.**

**Spec-driven**: the test traces to a spec section; its expected outcome is derivable from the spec alone.

**Behavioral**: the test checks observable behavior that any correct reimplementation would produce — not internal field names, repr strings, exception message wording, or implementation-specific shapes.

A failure on a test that violates either condition is a **verifier failure**, not a model failure. The judge uses actual pass/fail results as evidence to audit the instrument: if a cluster of failures aligns with undocumented internal shapes, that is a signal about test quality, not model capability.

**Do not interpret scores before verifying the instrument against these two conditions.**

---

## Hard Checks

All three must pass for any results to be considered valid.

### 1. Anti-Cheat

Before reading any score, run an import provenance preflight:

```bash
python -c "import <pkg>; print(<pkg>.__file__)"
```

**Write the literal output of this command into your diagnosis report as a `Preflight output` block before opening any score file or quoting any score value.** If this block is absent from your report, the report is structurally invalid — do not proceed.

This must point into the candidate solution directory, not the oracle worktree or any installed package. If running pytest from a copied source worktree, `sys.path[0]` may shadow `PYTHONPATH` — use `--remove-path <package>` when invoking pytest, or confirm via the preflight above before accepting any score. If provenance check fails, fix the environment and re-run.

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

The reference pass rate establishes the ceiling: the task is only valid if the oracle can pass it. Residual collection errors after a >95% pass rate should be noted and checked against spec_test_map.md — if they correspond to undocumented or optional behavior, flag for filter update rather than treating them as task failures.

---

### 3. Fairness

**Gate A — Spec mapping spot-check**

Sample a subset of `covered` rows from `spec_test_map.md`. For each sampled test, verify the spec_section mapping is correct — that a senior engineer reading only that spec section could predict the test outcome. If spot-check finds incorrect mappings -> return to test-filter to correct the map.

**Gate B — Failure pattern audit**

After scoring, sample failing tests and check whether failures are consistent with the two principles:
- Are failures traceable to documented spec behavior? If not, the test is checking undocumented internal shapes — verifier failure, not model failure.
- Do failures represent observable behavioral gaps, or internal structure mismatches (exact field names, repr format, exception message wording)?

If the majority of failures cluster around undocumented atomic internal shapes, return a `filter_correction_request.md` to test-filter — this is a BROKEN/fairness verdict, not a model capability signal.

**Gate C — Generated-only oracle spot-check**

If `spec_test_map.md` header contains `oracle_source: generated_only`, the tests were machine-generated and have not been author-validated. Manually sample >= 5 generated tests and re-apply the two core principles to each:
- **Spec-driven**: is the assertion's expected value derivable from a specific spec section? Or did the generator infer it from its own spec reading (circular)?
- **Behavioral**: would a correct reimplementation with different internals pass this test? Or does it check repr format, internal field names, or exact error message text?

If Gate C fails, return `filter_correction_request.md` to test-filter for regeneration.

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

These are examples, not an exhaustive set. If the evidence suggests a label not listed here, add it.

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

**Pass 2 — Model failure analysis**

For every failure cluster that passed Pass 1:

**Step 1 — Is this a protocol issue or a model issue?**

Ask: if the model had correctly implemented the spec, would this test pass?
- No, because the spec is ambiguous or incomplete -> spec gap
- Yes, the model should have gotten this -> real model failure

**Step 2 — Protocol issues**

| Type | Action |
|------|--------|
| Spec is ambiguous about this behavior | Patch spec; re-run test-filter coverage check |
| Arbitrary format / internal name in test | Mark `excluded` in spec_test_map.md |

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

### Weakness Table

File: `Bmk-dev/weakness_table.md`

One row per (model, task, dimension). Append; do not overwrite.

```markdown
| model | task | dimension | description | affected_tests |
|-------|------|-----------|-------------|----------------|
| gpt-4o | cookiecutter | cross-view-consistency | Model maintained template context in generate() but did not propagate to replay cache | 8 system_e2e |
| claude-sonnet | cookiecutter | error-semantics | Raised ValueError instead of UndefinedVariableError for missing context keys | 3 atomic |
```

The description should name the specific behavior gap, not just the test names. This is the material for paper discussion about model capability.
