---
name: candidate-selector
description: "Select a Python repository as a SWE-E2E benchmark task candidate. Use when evaluating whether a repo qualifies as a reconstruction task: checking hard/soft gates, recording the evidence brief in filter_notes.md, and logging retired candidates in CANDIDATES.md."
---

# Candidate Selector

## Hard Gates (all must pass)

Reject if any of the following:

- Pure Python package source LOC < 3,000
- Implementable as a single Python file without violating the public packet
- No shared fact source with >= 2 independent public projections (e.g. CLI + API + file state)
- Test suite absent, network-bound, or > 70% snapshot/exact-output checks
- Core behavior is a closed standard or high-saturation pattern (Jinja2, Redis, argparse) where strong models can pattern-match the implementation
- Evaluator requires private implementation details to score correctly
- Docs-test projection mismatch: public docs cover only CLI/syntax behavior while the test suite exercises Python API internals — a correct spec cannot be derived from docs alone, and the test suite cannot be fairly retained without benchmark-owned verifier tests

## Soft Gates (positive signals)

Prefer repos with:

- Durable state: file trees, databases, event logs, templates, indexes, caches
- Multiple public surfaces over the same facts: CLI, Python API, file output, search, schema introspection
- Official docs with enough behavioral coverage to write a traceable spec
- No mandatory external services; network calls removable or mockable
- Test files that import only public API symbols at module level (no `from pkg._xxx import` at top level)

## Test Import Pre-Screen

Before writing filter_notes.md, run:

```bash
grep -rn "from <pkg>\._\|import <pkg>\._" tests/
```

If > 30% of test files have module-level private imports, mark `test_import_audit: HIGH_RISK`. This is the leading cause of collection errors in clean candidate environments — it does not block selection but must be flagged, because Stage 3 Track A will require significant rewrite work or will trigger Track B early.

## Gate 1: Evidence Record

Create `wip/{task}/filter_notes.md` with:

```
repo: {name}
source_path: {local or URL}
commit: {hash}
src_loc: {N}
test_functions: {N}
test_files: {list or count}
dominant_test_styles: {unit/integration/snapshot/...}
public_docs: {list of doc pages used}
core_fact_source: {what is the shared state}
derived_views: {list of public projections}
external_deps: {list and isolation plan}
test_import_audit: {clean|HIGH_RISK — result of private-import grep; estimate % of test files affected}
docs_test_alignment: {aligned|MISMATCH — do docs cover the same projection type that tests exercise?}
contamination_note: {repo}@{version}, released {date}, relative to training cutoff: {before|after|unknown}
decision: {keep|defer|reject}
reason: {one sentence}
risks: {key risks}
```

## Selection Record

When a candidate is accepted, append to `CANDIDATES.md`:

```
| {repo} | SELECTED | {src_loc} | {test_count} | {reason} |
```

## Retirement Record

When a candidate is abandoned after repeated failed iterations, append to `CANDIDATES.md`:

```
| {repo} | RETIRED | {iteration_count} | {failure_reason} |
```

Create `CANDIDATES.md` at `Bmk-dev/CANDIDATES.md` if it does not exist, with header:

```markdown
# Candidates

| repo | status | metric | detail |
|------|--------|--------|--------|
```

