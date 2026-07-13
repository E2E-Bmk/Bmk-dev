# Diagnosis Report - hatch-envbuild-fullrepro-001

## User-Authorized Exception

This qualification uses a `user-authorized exception on 2026-07-03`: the task was explicitly reopened after RETIRED, `filter_iter` was reset to 0, and the Stage 3 oracle was repaired for the Gate D lockfile coverage gap. This is not a normal SKILL rescue rule and must not be treated as precedent outside this task.

## Preflight output

Command:

```bash
cd /mnt/g/research/01_agents/swe-e2e/Bmk-dev && PYTHONPATH=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-hatch-specv1-20260703-001/output .envs/s4-score-linux/bin/python -c 'import hatch; print(hatch.__file__)'
```

Output:

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-hatch-specv1-20260703-001/output/hatch/__init__.py
```

The literal `__file__` preflight points into the candidate solution directory, so the WSL score may be read.

## Verdict

Task status verdict: **QUALIFIED** under `user-authorized exception on 2026-07-03`.

The repaired oracle has 59 scoreable tests. WSL reference gate passed 59/59 with scorer isolation (`--remove-path hatch --remove-path hatchling`). The candidate run `codex-hatch-specv1-20260703-001` scored 49/59 on Linux/WSL.

## Anti-Cheat

Preflight passed and imports resolve to the candidate output directory. The candidate-visible prompt and output were previously scanned for source-repo, oracle, kept-nodeid, spec-map, score, and reference-artifact access; no forbidden candidate-phase access was found. The scorer JSON contains oracle paths only as post-implementation evaluation metadata.

## Solvability

Reference score artifact: `wip/hatch-envbuild-fullrepro-001/filter/reference_score_wsl_59_v4_exception_raw.json`.

| layer | passed | total |
|---|---:|---:|
| atomic | 36 | 36 |
| integration | 16 | 16 |
| system_e2e | 7 | 7 |

Reference gate result: **59/59 passed** on WSL/Linux. Platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`.

## Candidate Score

Score artifact: `candidate-runs/codex-hatch-specv1-20260703-001/score_result.json`.

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 35 | 1 | 36 |
| integration | 13 | 3 | 16 |
| system_e2e | 1 | 6 | 7 |

Overall: **49/59 passed**.

## Gate A - Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `test_env_lock_default_check_reports_default_lockfile` | `env lock default --check` checks `pylock.toml` for the default environment. | `Environment Lockfile Behavior` | derivable |
| `test_env_lock_named_check_reports_named_lockfile` | named env lock check uses `pylock.<ENV_NAME>.toml`. | `Environment Lockfile Behavior` | derivable |
| `test_env_lock_custom_filename_check_uses_override` | `lock-filename` overrides the selected lockfile path. | `Environment Lockfile Behavior` | derivable |
| `test_env_lock_export_and_export_all_are_mutually_exclusive` | `--export` and `--export-all` fail when combined. | `Environment Lockfile Behavior` | derivable |
| `test_dep_lock_uses_active_root_environment` | `dep lock --check` uses the active root environment selected by `-e`. | `Environment Lockfile Behavior` | derivable |
| `test_config_set_env_directory_affects_env_find` | config-set env directory affects later `env find`. | `Cross-View Invariants` | derivable |
| `test_build_custom_location_writes_artifact` | build writes wheel artifacts to selected output location. | `Build And Clean Behavior` | derivable |

Gate A result: **PASS**. Sampled covered rows quote real spec headings and test observable behavior.

## Gate B - Failure Pattern Audit

The prior exact wording issues were repaired: help now checks lowercase-normalized help behavior, `hatch run` missing-command only checks failure, and static-version set only checks failure. No retained candidate failure depends on exact non-contractual message wording.

| failure cluster | tests | spec trace | audit verdict |
|---|---:|---|---|
| Config commands are blocked by project mode after setting `mode = project`. | 1 | `Project And Configuration Behavior` | real candidate state-management failure |
| Script projection returns raw strings instead of resolved command lists, including after `hatch.toml` precedence. | 2 | `Environment Command Behavior`; `Project And Configuration Behavior` | real candidate cross-view failure |
| `env run -e system -- ...` passes the delimiter to the shell. | 1 | `Invocation Protocol`; `Environment Command Behavior` | real candidate workflow failure |
| `hatch shell test` accepts a matrix parent with one generated environment. | 1 | `Environment Command Behavior` | real candidate error-semantics failure |
| Build workflow crashes before artifact creation and before force-include validation, cascading into clean workflows. | 5 | `Build And Clean Behavior`; `Error Semantics`; `Cross-View Invariants` | real candidate workflow cascade |

Gate B result: **PASS**. Remaining failures are behavioral and spec-driven.

## Gate C - Generated-Only Oracle

Not applicable. The oracle is `upstream_rewritten_plus_user_authorized_exception`, not generated-only.

## Gate D - Coverage Gap Audit

Coverage verdict: **FULL** for scoreable behavioral sections. The previous zero-coverage core gap for `Environment Lockfile Behavior` was repaired under `user-authorized exception on 2026-07-03` with eight covered rows.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview` | Informational overview. | No direct oracle requirement. | No action. |
| `Scope` | Informational scope list. | No direct oracle requirement. | No action. |
| `Installable Surface` | Direct `from hatch.cli import hatch, main` import is not a separate row. | Secondary; root/module CLI behavior is covered. | Optional future API-surface row. |
| `Product State Model` | High-level projection list. | Covered through concrete cross-view and lifecycle rows. | No action. |
| `Environment Lockfile Behavior` | None for core validation/selection behavior covered here. | Core gap repaired. | Keep v4 lockfile rows. |
| `Representative Workflow` | Full example not duplicated as one monolithic test. | Covered piecemeal by matrix, version, build, clean, and precedence tests. | No action. |
| `Non-Goals` | Exclusion list. | Not scoreable positive behavior. | No action. |
| `Evaluation Notes` | Assessment guidance. | Not scoreable positive behavior. | No action. |

Gate D result: **PASS**.

## Real Failure Clusters

| root cause | dimension | affected tests |
|---|---|---|
| Config commands incorrectly depend on selected project state after `mode = project`. | state-management | 1 integration |
| Environment script JSON projection is not normalized to the resolved command-list form. | cross-view-consistency | 1 integration + 1 system_e2e |
| `env run -e system` mishandles the `--` delimiter before command execution. | workflow-completeness | 1 system_e2e |
| Matrix parent shell selection is accepted instead of rejected. | error-semantics | 1 integration |
| Build target workflow crashes before wheel creation and force-include validation, cascading into clean workflows. | workflow-completeness | 1 atomic + 4 system_e2e |

Cascade analysis: 10 raw failures reduce to 5 real root causes. The build/clean group is one workflow cascade, not five independent failures.

## Labels

- `qualified-user-authorized-exception-2026-07-03`
- `lockfile-coverage-repaired`
- `workflow-completeness-signal`
- `build-clean-cascade`
- `cross-view-consistency`
