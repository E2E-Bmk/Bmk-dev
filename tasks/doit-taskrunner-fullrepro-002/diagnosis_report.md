# WSL Judge Diagnosis Report - 2026-07-03

Task: `doit-taskrunner-fullrepro-002`
Predecessor: `doit-taskrunner-fullrepro-001`
Candidate run: `candidate-runs/codex-doit-specv1-20260701-001`
Score artifact: `score_result_wsl_nobom.json`

## Anti-Cheat Preflight

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-doit-specv1-20260701-001\output'; python -c "import doit; print(doit.__file__)"
```

Preflight output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-doit-specv1-20260701-001\output\doit\__init__.py
```

Verdict: PASS. Import provenance points into the candidate output directory, not the reference checkout, oracle worktree, or an installed package.

Available implementation-scope anti-cheat scan:

```powershell
rg -n -i "repo-pool|oracle_worktree|reference env|reference_score|score_result|kept_nodeids|spec_test_map|generated_tests|pip install|doit==|pydoit|source repo|/repo|\\repo" task_prompt.txt output/
```

Result: one match in `task_prompt.txt`, which is the task instruction forbidding access to source repos, tests, filter artifacts, score reports, or previous runs. No forbidden access pattern was found in candidate output. The candidate directory contains score worktrees after evaluation, but those are evaluation artifacts rather than implementation trajectory evidence. No separate full agent trajectory log was present in the candidate run directory.

## Entry State

`PIPELINE_STATE.md` was in `S5_JUDGE` with inherited `filter_iter=2` and `oracle_count=53`, matching the reopened-task context.

## Environment And Score

Score platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`

Python: `3.11.15`

Evaluation isolation evidence:

- `solution_dir`: `/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-doit-specv1-20260701-001/output`
- `source_repo`: `/mnt/g/research/01_agents/swe-e2e/Bmk-dev/wip/doit-taskrunner-fullrepro-001/filter`
- `remove_paths`: `doit`
- `run_dir`: `score_wsl_filter53_nobom`
- scoring nodeids and taxonomy use no-BOM temp copies.

Candidate summary:

| metric | value |
|---|---:|
| passed | 47 |
| failed | 6 |
| total | 53 |
| collection errors | 0 |
| pass rate excluding skips | 0.8867924528301887 |

Candidate by layer:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 14 | 4 | 18 |
| integration | 27 | 1 | 28 |
| system_e2e | 6 | 1 | 7 |

## Reference And Dummy Evidence

Reference gate evidence from `filter/reference_score.json`:

| gate | total | passed | failed | errors | pass_rate |
|---|---:|---:|---:|---:|---:|
| reference | 53 | 53 | 0 | 0 | 1.0 |

Reference notes state the oracle was expanded to 53 generated tests, run with `pytest-base` and `PYTHONPATH` set to the reference checkout, and all 53 passed.

Dummy gate evidence from `filter/dummy_gate_report.json`:

| gate | total | passed | failed | errors | status |
|---|---:|---:|---:|---:|---|
| dummy | 53 | 0 | 53 | 0 | pass |

This supports solvability and non-triviality: the reference ceiling is 100%, while the no-op dummy implementation is rejected by every scoreable test.

## Gate A - Spec Mapping Spot-Check

Sampled covered rows from `spec_test_map.md` against exact headings in `spec/spec_v1.md`:

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `generated_tests.py::test_get_var_reads_cli_variable_during_task_loading` | CLI `color=blue` is visible through `doit.get_var` during dodo loading and produces `color.txt=blue`. | `Public API` | derivable |
| `generated_tests.py::test_task_params_long_option_is_injected_into_task_creator` | `@task_params` exposes `--name Grace` and injects `name="Grace"` into the task creator. | `Public API` | derivable |
| `generated_tests.py::test_create_after_materializes_selected_delayed_task` | Selecting delayed task `late` materializes it after `build`, runs both tasks, and writes `seed-late`. | `Task Definitions` | derivable |
| `generated_tests.py::test_python_action_dictionary_result_feeds_getargs` | A dict action result from `produce` is passed through `getargs` into `consume`. | `Actions and Results` | derivable |
| `generated_tests.py::test_implicit_target_dependency_runs_producer_before_consumer` | Selecting a task whose `file_dep` is another task's target runs the producer before the consumer. | `Cross-View Invariants` | derivable |
| `generated_tests.py::test_task_params_short_boolean_inverse_can_disable_default` | Boolean task parameter inverse flag `--no-flag` sets the default `True` value to `False`. | `Configuration` | derivable |
| `generated_tests.py::test_calc_dep_adds_late_file_dependency` | A `calc_dep` result adds late `file_dep` metadata that affects later freshness checks. | `Dependencies and Up-To-Date Status` | derivable |
| `generated_tests.py::test_json_reporter_reports_same_task_success_as_console_side_effect` | JSON reporter success agrees with the file side effect of the executed task. | `Cross-View Invariants` | derivable |

Gate A verdict: PASS. Sampled mappings quote real spec headings and test observable behavior.

## Gate B - Failure Pattern Audit

Failing tests:

| nodeid | layer | audited behavior | verdict |
|---|---|---|---|
| `test_task_params_long_option_is_injected_into_task_creator` | atomic | Candidate's `task_params` callable rejects decorator-style use with a missing `param_def`, so task parameter injection fails before execution. | real model failure, `api-surface` / `atomic-behavior` |
| `test_create_after_materializes_selected_delayed_task` | integration | Candidate cannot select a delayed task declared through `create_after(..., creates=["late"])`; CLI reports unknown task. | real model failure, `workflow-completeness` |
| `test_invalid_task_dictionary_returns_command_error_without_running` | atomic | Candidate returns command error 3 for an invalid task field but does not identify the selected invalid task name in user-facing output. | real model failure, `error-semantics`; output-name assertion is behavioral and non-exact |
| `test_info_reports_missing_target_as_reason_to_run` | atomic | Candidate prints missing-target reasons but returns 0 instead of the reference command status for an out-of-date info query. | real model failure, `error-semantics`; minor protocol caveat on return-code explicitness |
| `test_task_params_short_boolean_inverse_can_disable_default` | atomic | Candidate accepts `--no-flag` but does not inject `False`; action observes the default `True`. | real model failure, `atomic-behavior` |
| `test_calc_dep_adds_late_file_dependency` | system_e2e | Candidate reruns one extra time after a late dependency is established, yielding count `3` instead of `2`. | real model failure, `state-management` |

Gate B verdict: PASS with caveat. Failures cluster around public CLI/API/state behavior, not private fields, repr strings, internal class names, or exact error wording. The `info` return-code assertion is the only borderline protocol detail; because the test also checks documented missing-target reporting and the reference passes it, this is recorded as a non-blocking caveat rather than a filter-breaking majority pattern.

## Gate C - Generated-Only Oracle Spot-Check

`spec_test_map.md` declares `filter/oracle_source: generated_only`, so generated tests were manually sampled:

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `test_get_var_reads_cli_variable_during_task_loading` | CLI variables are consumed before task execution and exposed through `get_var`. | `Public API` | spec-driven, behavioral |
| `test_task_params_long_option_is_injected_into_task_creator` | Decorator-defined task params become task CLI options and creator arguments. | `Public API` | spec-driven, behavioral |
| `test_create_after_materializes_selected_delayed_task` | Delayed creation via `create_after` makes the created task selectable and executable after prerequisite execution. | `Task Definitions` | spec-driven, behavioral |
| `test_python_action_dictionary_result_feeds_getargs` | Saved dictionary values flow to another task through `getargs`. | `Actions and Results` | spec-driven, behavioral |
| `test_implicit_target_dependency_runs_producer_before_consumer` | Target/file dependency relationship creates execution ordering. | `Cross-View Invariants` | spec-driven, behavioral |
| `test_task_params_short_boolean_inverse_can_disable_default` | Boolean inverse parameter disables the default value. | `Configuration` | spec-driven, behavioral |
| `test_calc_dep_adds_late_file_dependency` | `calc_dep` adds late dependency metadata that controls later up-to-date decisions. | `Dependencies and Up-To-Date Status` | spec-driven, behavioral |

Gate C verdict: PASS. No sampled generated test is circular or internal-shape dependent.

## Gate D - Coverage Gap Audit

Behavioral core section coverage from `spec_test_map.md`:

| spec section | covered rows | impact |
|---|---:|---|
| `Public API` | 2 | core covered |
| `Task Definitions` | 5 | core covered |
| `Actions and Results` | 7 | core covered |
| `Dependencies and Up-To-Date Status` | 6 | core covered |
| `Built-In Tools` | 4 | core covered |
| `Command Line` | 18 | core covered |
| `Configuration` | 3 | core covered |
| `Extension Surfaces` | 1 | core covered |
| `Error Semantics` | 4 | core covered |
| `Cross-View Invariants` | 3 | core covered |

Uncovered or indirectly covered secondary sections:

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview` | descriptive overview, no separate expected behavior | none | no action |
| `Scope` | scope declaration, no direct assertion | none | no action |
| `Installable Surface` | imports and `python -m doit` are exercised by many tests but not mapped to this heading directly | low | optional future map refinement |
| `Representative Workflow` | example workflow is decomposed across dependency/getargs/clean/info sections rather than mapped directly | low | no action |
| `Non-Goals` | exclusion list, should not be scored directly | none | no action |
| `Evaluation Notes` | evaluator guidance, not product behavior | none | no action |

Gate D verdict: PARTIAL acceptable. No core invariant, error semantics, state lifecycle, dependency, command, or configuration section is empty.

## Protocol Issues

No blocking protocol issue found. The repaired generated-only oracle avoids the earlier JSON reporter shape overconstraint noted in pipeline history. The `info` return-code failure is noted as a small spec-explicitness caveat, but the overall failing set does not indicate verifier breakage or an internal-shape majority.

## Real Failure Clusters

| cluster | affected tests | layer(s) | dimension | description | cascade |
|---|---|---|---|---|---|
| Task parameter injection | 2 | atomic | `atomic-behavior` | Candidate does not correctly implement decorator-style `task_params` and boolean inverse injection into task action/creator options. | two independent parameter behaviors, no broad cascade |
| Delayed task creation | 1 | integration | `workflow-completeness` | Candidate does not materialize/select a `create_after` delayed task by declared `creates` basename. | isolated workflow gap |
| Command/error semantics | 2 | atomic | `error-semantics` | Candidate diverges on user-facing invalid-task reporting and info status code for missing target/run-needed state. | isolated CLI semantics |
| Late dependency state | 1 | system_e2e | `state-management` | Candidate records or applies `calc_dep` late file dependencies incorrectly, causing an extra rerun after state should be stable. | isolated state-management signal |

Cascade analysis: 6 failed tests reduce to 4 root clusters. The failures are not dominated by one missing import or one broken primitive; they are discrete public-behavior gaps. The system_e2e failure is a genuine state-management signal rather than a cascade from a missing API.

## Labels

Suggested labels:

- `discriminating`: candidate passes most tests but misses several public behavior clusters.
- `generated-only-valid`: generated-only oracle passes reference and dummy gates and survives manual spot-check.
- `state-management-signal`: `calc_dep` failure exposes persistent freshness-state behavior.
- `cli-error-semantics-signal`: failing command/status behavior is observable at the CLI boundary.
- `coverage-partial-secondary`: non-behavioral or indirectly covered spec sections are not directly mapped.

## Verdict

Verdict: `QUALIFIED`.

Route: terminal `QUALIFIED`; no return to spec writer, test filter, or setup is required for this reopened task. The oracle is solvable, non-vacuous, generated-only spot-checks pass, core coverage is present, anti-cheat provenance is clean, and candidate failures represent meaningful public behavior gaps.
