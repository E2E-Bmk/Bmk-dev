# Go Stage 1-3 batch progress

Branch: `cursor/8-26-50tasks-go-a9d6`. Deliverable: 10 Go task packets at Stage 3
completion (S3_DONE), each under `staging/{task_id}/`.

## Packet layout (Definition A)

```
staging/{task_id}/
|-- spec.md                     candidate-visible body only (internal header omitted;
|                               source_boundary recorded in filter_notes.md)
|-- task.json                   language=go, taxonomy, stats, repo_commit
|-- PIPELINE_STATE.md           state machine instance, S1_SCREENING -> S3_DONE
|-- filter_notes.md             Stage 1 evidence brief + source_boundary
|-- oracle/
|   |-- go.mod                  module {task}-oracle, requires target at v0.0.0
|   |-- go.sum                  dependency snapshot from the reference run
|   |-- atomic/*_test.go        package atomic
|   `-- integration/*_test.go   package integration
`-- filter/
    |-- spec_test_map.md        one row per test, spec_section per row, footer totals
    |-- kept_nodeids.txt        suite::TestName, covered rows only
    |-- taxonomy.jsonl          {"taxonomy_key": "atomic::TestX", "layer": "atomic"}
    |-- lint_result.txt         oracle_import_lint output, first line LINT_PASS
    |-- reference_score.json    reference run at pinned version, must be 100%
    `-- dummy_result.txt        adversarial dummy run evidence (0 passes required)
```

## Harness note (required to reproduce lint results)

`harness/oracle_import_lint.py` on `main` has no Go oracle layout support and no
`TARGET_IMPORTS` entries for these tasks; the write scope of this batch is
`staging/` only, so the harness was not modified on this branch. Lint results in
each packet were produced with the Go-enabled lint from branch
`origin/go-tasks-20260821` (commit 85c6278: adds `go_target_symbols` and the
`oracle/atomic` + `oracle/integration` layout detection), run from a gitignored
copy under `wip/_tools/harness/`, with the following entries appended to its
`TARGET_IMPORTS` copy (these must be added to `harness/target_imports.py` when
the packets graduate):

```python
# to be filled in as tasks are selected
```

Reference runs execute `go test -json ./...` per suite against the pinned
upstream version wired in with `go mod edit -replace`, mirroring
`harness/runners/go.py` setup. Dummy runs use an adversarial stub module
(zero-value returns and non-nil errors, not panics) at the same module path.

## Status

| # | task_id | repo | state | oracle (atomic+integration) | reference | notes |
|---|---------|------|-------|-----------------------------|-----------|-------|

## Candidate selection log (CANDIDATES.md rows deferred; write scope is staging/ only)

| repo | status | metric | detail |
|------|--------|--------|--------|
