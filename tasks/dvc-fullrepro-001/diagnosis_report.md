# Stage 5 Diagnosis Report - dvc-fullrepro-001 WSL 50-test rerun

Verdict: QUALIFIED

Run: `candidate-runs/codex-dvc-specv1-20260701-002`
Task spec: `spec/spec_v1.md`
Oracle source: generated_only
Scoring set: 50 generated behavioral tests
Platform: Linux/WSL rerun 2026-07-03

## Anti-cheat scan

The candidate packet manifest says the candidate-visible run contained only `public_packet/spec.md` and `task_prompt.txt`; hidden benchmark assets, reference artifacts, prior runs, filter files, tests, and scoring outputs were excluded by policy. The task prompt explicitly prohibited reading tests, parent/sibling benchmark artifacts, source repositories, score reports, and the real `dvc` package.

Implementation-artifact scan over the candidate `solution/` directory found no references to `repo-pool`, `kept_nodeids`, `spec_test_map`, `generated_tests`, `reference_score`, `score_result`, or `pip install`. The candidate run directory itself now contains scorer artifacts from evaluation, so the anti-cheat scan treats `solution/`, `cleanroom_manifest.json`, and `task_prompt.txt` as the relevant candidate-access evidence.

### Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-dvc-specv1-20260701-002\solution'; python -c "import dvc; print(dvc.__file__)"
```

Output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-dvc-specv1-20260701-002\solution\dvc\__init__.py
```

The import provenance points inside the candidate solution directory, so the score is not importing the reference package or an installed DVC package.

## Solvability

Reference score artifact: `filter/reference_score_retro_gate_d.json`

Reference result: 50/50 passed, pass_rate 1.0, stdout summary `50 passed in 156.76s (0:02:36)`. This satisfies the >=95% solvability gate. The artifact notes that the retroactive Gate D oracle supplement did not rerun the candidate at that time; the 2026-07-03 WSL rerun fixes that procedural gap for this Stage 5 judgment.

## Candidate score

Candidate score artifact: `candidate-runs/codex-dvc-specv1-20260701-002/score_result.json`

Candidate result: 41 passed, 5 failed, 4 error, total 50, pass_rate 0.82.

Layer summary:

| layer | passed | total | failed/error |
|---|---:|---:|---:|
| atomic | 13 | 14 | 1 error |
| integration | 21 | 27 | 5 failed, 1 error |
| system_e2e | 7 | 9 | 2 error |

Platform field is `Linux/WSL rerun 2026-07-03`, satisfying the non-Windows Stage 4/5 requirement.

## Gate A - Spec Mapping Spot-check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `generated_tests.py::test_stage_add_without_run_does_not_create_lockfile` | `stage add` without `--run` writes only the stage definition and no lockfile. | `## Stage Creation` | derivable |
| `generated_tests.py::test_repro_no_commit_writes_public_lock_stage` | Reproduction writes a public `dvc.lock` stage entry. | `## Pipeline Files` | derivable |
| `generated_tests.py::test_status_json_changes_after_dependency_file_changes` | Changing a dependency file makes status report a changed stage. | `## Cross-View Invariants` | derivable |
| `generated_tests.py::test_local_status_rejects_revision_expansion_option` | Local status rejects branch/tag/commit expansion options. | `## Error Semantics` | derivable |
| `generated_tests.py::test_repo_reproduce_force_returns_reproduced_stages` | `Repo.reproduce()` returns the stages that actually reproduced. | `## Public API` | derivable |
| `generated_tests.py::test_run_cache_restores_deleted_output_without_rerunning_command` | Run cache can restore an output without running the stage command. | `## Cache And Run Cache` | derivable |

Gate A verdict: PASS. Sampled mappings point to real spec headings and the expected outcomes are derivable from those sections.

## Gate B - Failure Pattern Audit

Non-passed tests group into two public-behavior clusters:

| cluster | tests | spec basis | audit verdict |
|---|---:|---|---|
| No-commit/status lifecycle | 5 failed tests: no-commit status JSON, quiet status, repeated no-commit rerun, rerun after dependency change, rerun after output deletion | `## Reproduction Behavior`, `## Status, Freeze, And Pull`, `## Cross-View Invariants` | real model failure |
| Missing local remote setup CLI | 4 fixture setup errors: clean status, quiet clean status, run-cache restore, pull restore from local remote | `## Status, Freeze, And Pull`, `## Cache And Run Cache`, `## Public API` CLI surface | real model failure cascade from missing `dvc remote add` command |

The failures check return codes, YAML/lock/workspace state, status mappings, command execution counts, and local remote restoration. They do not depend on private module paths, repr strings, internal object identities, or exact error message text. Gate B verdict: PASS.

## Gate C - Generated-only Oracle Spot-check

The map header contains `filter/oracle_source: generated_only`, so generated test spot-check is required.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `generated_tests.py::test_stage_list_name_only_reports_created_stage` | A stage created by `stage add` is visible through `dvc stage list --name-only`. | `## Cross-View Invariants` | derivable; behavioral |
| `generated_tests.py::test_outs_no_cache_is_serialized_with_cache_false` | `-O/--outs-no-cache` serializes the public `cache: false` output option. | `## Pipeline Files` | derivable; behavioral |
| `generated_tests.py::test_stage_command_receives_dvc_root_environment` | Stage commands receive `DVC_ROOT` as the project root. | `## Reproduction Behavior` | derivable; behavioral |
| `generated_tests.py::test_failing_command_list_does_not_run_later_commands` | A failed command in a list-valued stage stops later commands. | `## Error Semantics` | derivable; behavioral |
| `generated_tests.py::test_frozen_stage_does_not_reproduce_changed_params` | Frozen stages do not reproduce through changed parameters until unfrozen. | `## Status, Freeze, And Pull` | derivable; behavioral |
| `generated_tests.py::test_pull_restores_stage_output_from_local_remote` | Pull restores tracked output data from a configured local remote. | `## Status, Freeze, And Pull` | derivable; behavioral |
| `generated_tests.py::test_always_changed_stage_runs_even_without_input_changes` | `always_changed` stages reproduce repeatedly even without input changes. | `## Reproduction Behavior` | derivable; behavioral |

Gate C verdict: PASS. No sampled generated test is circular or internal-shape dependent.

## Gate D - Coverage Gap Audit

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `## Product Overview` | Framing text only; no distinct behavioral assertion. | none | No action. Covered behavioral sections exercise the described pipeline workflow. |
| `## Scope` | Scope boundary text only; behavior appears in later sections. | none | No action. |
| `## Non-Goals` | Exclusion list; tests should avoid these behaviors rather than cover them. | none | No action. |
| `## Evaluation Notes` | Scoring guidance; not candidate behavior. | none | No action. |

All core behavioral sections have at least one covered row: `Installable Surface`, `Public API`, `Pipeline Files`, `Stage Creation`, `Reproduction Behavior`, `Status, Freeze, And Pull`, `Cache And Run Cache`, `Error Semantics`, `Cross-View Invariants`, and `Representative Workflows`.

Coverage verdict: PARTIAL (acceptable). No core invariant, error semantics, state lifecycle, or run-cache section is empty.

## Protocol issues

No oracle repair is required from this judge pass. The earlier History row claiming a 43-to-50 retroactive update without a candidate rerun was procedurally invalid under the REOPENED_S3 rule. This report judges the later 50-test WSL candidate rerun and updates pipeline history to represent the actual REOPENED_S3 -> S4 rerun -> S5 rejudge -> QUALIFIED chain.

## Real failure clusters

| cluster | layer(s) | dimension | evidence | root/cascade |
|---|---|---|---|---|
| No-commit status and rerun lifecycle | integration | state-management | `status --json` after `--no-commit` returns `{}` instead of reporting `prepare`; quiet status returns 0; repeated `--no-commit --no-run-cache` reruns produce counts `1,1,2,3` rather than `1,2,3,4`. | One root lifecycle bug cascades across five assertions. |
| Missing `dvc remote add` command | atomic/integration/system_e2e | api-surface | Fixture setup fails with `unknown command: remote` for `remote add -d localstore ...`. | One missing public CLI command blocks four tests in clean status, run-cache, and pull workflows. |

Cascade analysis: 9 non-passed tests reduce to 2 root causes. The score remains discriminating: the candidate passes most stage-add/repro/freeze/API basics while failing more durable state and remote/pull workflow behavior.

## Labels

- `discriminating`
- `generated-only-valid`
- `state-management-signal`
- `api-surface-cascade`
- `coverage-partial-acceptable`

## Final decision

QUALIFIED. Hard checks pass: import provenance is inside the candidate solution, reference passes 50/50, candidate rerun is Linux/WSL with 50 collected tests, Gates A/B/C/D pass, and non-passed tests are real public-behavior failures rather than verifier failures or cheat evidence.
