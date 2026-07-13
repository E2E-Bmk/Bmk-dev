# WSL Fallback Diagnosis Report - coveragepy-fullrepro-001

## Anti-cheat preflight

Preflight command:

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath 'candidate-runs\codex-coveragepy-specv1-20260701-001\output').Path; python -c "import coverage; print(coverage.__file__)"
```

Preflight output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-coveragepy-specv1-20260701-001\output\coverage\__init__.py
```

The import provenance points inside the candidate output package.

## Verdict

`QUALIFIED`. The fallback WSL score artifact is valid as a model-failure signal.

The earlier WSL grouped-timeout artifact was rejected because one timed-out pytest file group smeared timeout outcomes across all 51 nodeids. The fallback artifact runs nodeids individually and reports a mixed result: 30 passed, 21 failed, 51 total. This resolves the timeout-smear concern. The remaining failures are public behavioral gaps in CLI execution, data-file lifecycle, configuration/error handling, contexts, and exclusion semantics.

## Anti-cheat scan

- Import provenance: pass. The required preflight output above points to `candidate-runs/codex-coveragepy-specv1-20260701-001/output/coverage/__init__.py`.
- Candidate-visible prompt/output scan: pass. `task_prompt.txt` and `output/` contain no matches for `repo-pool`, `oracle_worktree`, `reference_score`, `spec_test_map`, `kept_nodeids`, `score_result`, or `pip install coverage`.
- Full implementation trajectory: not present in the candidate-run directory. The scan is therefore limited to the stored prompt and output package. Score directories contain scorer-created oracle worktrees and score artifacts by design; these post-evaluation files were not treated as implementation-phase evidence.
- High-score probe: not triggered because the candidate pass rate is 30/51 = 58.8%, but the provenance preflight was still performed before reading score values.

## Solvability

Reference WSL score: `wip/coveragepy-fullrepro-001/filter/reference_score_wsl_51.json`.

```text
summary: 51 passed / 51 total
pass_rate_excluding_skips: 1.0
by_layer:
  atomic: 20 passed / 20 total
  integration: 17 passed / 17 total
  system_e2e: 14 passed / 14 total
```

Solvability passes. The reference implementation passes the complete 51-test oracle in the WSL environment.

## Candidate score

Candidate fallback WSL score: `candidate-runs/codex-coveragepy-specv1-20260701-001/score_result_wsl_51_fallback.json`.

```text
summary: 30 passed / 21 failed / 51 total
by_layer:
  atomic: 15 passed / 5 failed / 20 total
  integration: 8 passed / 9 failed / 17 total
  system_e2e: 7 passed / 7 failed / 14 total
timeout_seconds: 180
remove_paths: ["coverage"]
```

The fallback score has one-node pytest reports and no grouped all-timeout smear. Several failed tests still contain subprocess-level timeouts inside the test body, but those are real per-node outcomes for public CLI workflows.

## Gate A - Spec mapping spot-check

| nodeid | assertion summary | spec_section | verdict |
|--------|-------------------|--------------|---------|
| `filter/generated_tests.py::test_installable_surface_imports_version_and_module_cli` | `coverage` exposes version/API names and `python -m coverage --version` succeeds. | `Installable Surface` | derivable |
| `filter/rewritten_upstream_tests.py::test_coverage_data_add_arcs_round_trips_to_disk` | `CoverageData` records arc data, writes it, reads it back, and reports branch mode. | `CoverageData` | derivable |
| `filter/rewritten_upstream_tests.py::test_cli_run_module_passes_program_arguments` | `coverage run -m` executes a module and preserves program arguments. | `` `coverage run` `` | derivable |
| `filter/generated_tests.py::test_invalid_rcfile_reports_config_error_via_cli_and_api` | Invalid config is surfaced as controlled CLI failure and public `ConfigError`. | `Error Semantics` | derivable |
| `filter/generated_tests.py::test_cli_branch_context_json_and_total_report_agree` | CLI branch run, JSON contexts, and total report agree on one measured data file. | `Cross-View Invariants` | derivable |
| `filter/rewritten_upstream_tests.py::test_exclusion_rules_remove_lines_from_missing_report` | Excluded lines are not reported as missing and exclusion rules can be cleared. | `Measurement Semantics` | derivable |

Gate A passes for the sampled covered rows.

## Gate B - Failure pattern audit

The sampled failures are traceable to documented public behavior and do not depend on private field names, exact reprs, or exact diagnostic formatting.

| sampled failure | mapped behavior | audit verdict |
|---|---|---|
| `test_cli_branch_context_json_and_total_report_agree` timed out running `python -m coverage run --branch --context=...` | `coverage run`, contexts, JSON/report cross-view agreement | valid model failure |
| `test_configured_data_file_is_shared_by_cli_and_coveragedata` timed out in CLI `coverage run` before reading configured data through `CoverageData` | `Configuration`, `Data Files`, `Cross-View Invariants` | valid model failure |
| `test_coverage_data_purge_files_removes_measured_file` returned `None` after purging where the public data lifecycle expects an empty measured-file query result | `CoverageData` | valid model failure |
| `test_invalid_rcfile_reports_config_error_via_cli_and_api` surfaced raw parser exceptions instead of public `ConfigError`/controlled CLI failure | `Error Semantics` | valid model failure |
| `test_coverage_data_query_context_filters_lines` recorded `setup` and `phase-two` separately instead of preserving the combined static/dynamic context view | `Measurement Semantics`, `Cross-View Invariants` | valid model failure |
| `test_exclusion_rules_remove_lines_from_missing_report` still reported a pragma-excluded line as missing | `Measurement Semantics`, `Cross-View Invariants` | valid model failure |

Gate B passes. The majority failure pattern is not an oracle/verifier problem; it reflects public behavior gaps in the candidate.

## Gate C - Generated-only oracle spot-check

Not applicable. `spec_test_map.md` declares:

```text
oracle_source: upstream_and_generated
```

## Gate D - Coverage gap audit

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview` | Overview prose only; concrete behavior is covered by API/CLI/data/report sections. | none | no action |
| `Scope` | Scope prose only; concrete behavior is covered by included sections. | none | no action |
| `Public API` | Parent heading; child sections `Coverage` and `CoverageData` are covered. | none | no action |
| `Command-Line Behavior` | Parent heading; command-specific child sections are covered. | none | no action |
| `Non-Goals` | Negative scope only. | none | no action |
| `Evaluation Notes` | Benchmark guidance only. | none | no action |

All core behavioral sections have at least one covered row: `Installable Surface`, `Coverage`, `CoverageData`, `coverage help`, `coverage run`, `coverage report`, `coverage json/xml/html`, `coverage combine/erase`, `coverage debug`, `Configuration`, `Measurement Semantics`, `Data Files`, `Report Semantics`, `Error Semantics`, `Cross-View Invariants`, and `Representative Workflow`.

Coverage verdict: `PARTIAL` acceptable. No core invariant, error semantics, or state lifecycle section is empty.

## Protocol issues

No blocking protocol issue remains for the fallback artifact. The previous grouped timeout artifact remains invalid, but this per-node fallback artifact supersedes it for judging.

## Real failure clusters

| cluster | affected failures | layer spread | dimension | cascade analysis |
|---|---:|---|---|---|
| `python -m coverage run` hangs on simple script/module workflows, including branch mode, `--parallel-mode`, missing script, configured data file, and module execution. | 15 | atomic/integration/system_e2e | `workflow-completeness` | One CLI execution root cause cascades into report/json/xml/combine/debug/data-file tests that cannot reach downstream assertions. |
| Invalid configuration values and malformed rcfiles leak raw parser exceptions instead of public `ConfigError` or controlled CLI errors. | 2 | atomic | `error-semantics` | Independent public error-surface gap. |
| Static and dynamic contexts are not combined into the public query/report context view. | 1 | integration | `cross-view-consistency` | Independent context projection gap. |
| Exclusion rules and pragma exclusions do not consistently remove excluded lines from missing-line analysis, and clearing rules does not restore the expected missing set. | 2 | integration | `atomic-behavior` | Shared measurement primitive gap; affects analysis/report semantics. |
| `CoverageData.purge_files()` leaves purged measured files indistinguishable from never-measured files for `lines()`. | 1 | atomic | `state-management` | Independent data lifecycle gap. |

The 21 failures reduce to roughly 5 root causes. The largest cascade is the CLI `coverage run` hang, which explains most integration and system failures; the remaining failures provide separate signals for error semantics, state lifecycle, context consistency, and measurement primitives.

## Task labels

- `discriminating`: reference passes 51/51 while the candidate passes 30/51 with failures across all layers.
- `cascade-dominated`: most integration/system failures cascade from CLI `coverage run` hanging before downstream assertions.
- `composition-signal`: context/data/report consistency failures remain after primitive passing cases, especially context projection and configured data-file workflows.
- `coverage-gap-partial-acceptable`: parent/prose sections are uncovered, but no core invariant or error/state lifecycle section is empty.
