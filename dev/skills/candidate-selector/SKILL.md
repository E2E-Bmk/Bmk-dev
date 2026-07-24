---
name: candidate-selector
description: "Select a Python repository as a SWE-E2E benchmark task candidate. Use when evaluating whether a repo qualifies as a reconstruction task: checking hard/soft gates, recording the evidence brief in filter_notes.md, and logging retired candidates in CANDIDATES.md."
---

# Candidate Selector

## State Machine Interface

**Entry:** Read `wip/{task}/PIPELINE_STATE.md`. Verify `state` is `S1_SCREENING`. If absent, copy from `Bmk-dev/skills/PIPELINE_STATE.template.md` to `wip/{task}/PIPELINE_STATE.md` and replace `{TASK_ID}` and `{DATE}`.

**Exit (keep):** Set `state → S1_SELECTED`, update `todo` to S1_SELECTED catalogue todo, append History row.

**Exit (reject):** Set `state → RETIRED`, append History row, stop.

---

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

## Selection Preferences

**Multi-component collaboration preference:** Prioritize frameworks, engines, pipelines, protocol stacks, and multi-layer architectures. Avoid utility function collections, single-class libraries, and pure algorithm packages. Quick test: does the library's typical usage involve ≥3 cooperating objects to complete one user scenario? If it can be fully demonstrated in one line of code, it's not suitable.

---

## Test Import Pre-Screen

Before writing filter_notes.md, run an AST-level import closure check — not just underscore-prefixed names. For each test file, collect all imported top-level package names and compare against the spec's Public Interface > Import Surface (or the candidate repo's `__all__` / `__init__` exports if the spec does not yet exist).

```bash
# Quick grep for explicit private imports
grep -rn "from <pkg>\._\|import <pkg>\._" tests/

# Also check for undocumented non-underscore modules used as test carriers:
# e.g. `from scrapy.utils._deps_compat import`, `from pelican.tests.support import`
# These do not have underscores but are not part of the public API surface.
python - <<'EOF'
import ast, pathlib, sys
pkg = sys.argv[1] if len(sys.argv) > 1 else "<pkg>"
bad = []
for f in pathlib.Path("tests").rglob("*.py"):
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or (node.names[0].name if isinstance(node, ast.Import) else "")
            if mod and mod.startswith(pkg + ".") and not mod.split(".")[1].startswith("_"):
                bad.append((str(f), mod))
for f, m in bad:
    print(f"UNDOC_IMPORT {f}: {m}")
EOF
```

If > 30% of test files have module-level private imports **or** undocumented carrier imports, mark `test_import_audit: HIGH_RISK`. This is the leading cause of collection errors in clean candidate environments.

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
scope_plan: {if src_loc > 15000 or test_functions > 300, write: target_subdomain=X, expected_oracle_max=N; otherwise write: N/A}
```

When `scope_plan` is not N/A, the Stage 3 handoff must verify the actual kept set matches the stated `target_subdomain` and does not exceed `expected_oracle_max`. If it does, return to Stage 2 to scope down.

## Selection Record

**source_meta collection:** When a task reaches QUALIFIED, record in task.json:
- `source_meta.github_stars`: GitHub star count at time of qualification
- `source_meta.pypi_monthly_downloads`: approximate PyPI downloads
- `source_meta.loc`: lines of code in source package
- `source_meta.first_release`: date of first PyPI release

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

