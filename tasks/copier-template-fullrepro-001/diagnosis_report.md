# Fresh 51-Test Stage 5 Judge - copier-template-fullrepro-001

## Verdict

Status: QUALIFIED for this fresh Stage 5 pass.

The repaired live generated-only oracle is solvable by the reference implementation, the active candidate score is the fresh 51-test score, and the candidate failures are attributable to documented public behavior rather than verifier internals. No oracle files, score files, state files, candidate registry files, task files, or weakness tables were modified by this judge pass. This report is the only written artifact.

## Preflight output

Command run before accepting or citing score values:

```bash
cd /mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-copier-specv1-20260701-001/solution
python3 -c 'import copier; print(copier.__file__)'
```

Literal output:

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-copier-specv1-20260701-001/solution/copier/__init__.py
```

The import resolves inside the candidate solution directory.

## Anti-Cheat

Import provenance passed. Candidate-facing artifacts (`solution`, `public_packet`, `task_prompt.txt`, and `cleanroom_manifest.json`) were scanned for forbidden references including `repo-pool`, `spec_test_map`, `kept_nodeids`, `generated_tests`, score artifacts, reference artifacts, private `copier._*` imports, and `pip install copier`. The only hits were cleanroom policy text in `task_prompt.txt` and `cleanroom_manifest.json`; no solution or public-packet leakage indicator was found.

No implementation-phase transcript was available in the provided artifacts. Scorer worktrees and score outputs are evaluation artifacts created after implementation, not candidate-authored evidence.

## Solvability

Reference solvability passes on the repaired live oracle.

| artifact | result | platform |
|---|---:|---|
| `filter/reference_score.json` | 51/51, pass rate excluding skips 1.0 | Linux WSL2 |
| `filter/reference_score_wsl_live_repair_20260704.json` | 51/51, pass rate excluding skips 1.0 | Linux WSL2 |

Reference layer ceiling from `filter/reference_score.json`:

| layer | reference |
|---|---:|
| atomic | 22/22 |
| integration | 12/12 |
| system_e2e | 17/17 |

## Candidate Score

The active `candidate-runs/codex-copier-specv1-20260701-001/score_result.json` matches `score_result_wsl_filter51_fresh_20260704.json` and reports 36/51 passed, 15 failed, 0 collection errors, pass rate excluding skips 0.7058823529411765.

| layer | candidate |
|---|---:|
| atomic | 21/22 |
| integration | 11/12 |
| system_e2e | 4/17 |

The score file records the repaired live oracle source path (`tmp/copier-live-oracle-source-20260704-001`) and fresh run directory (`score_wsl_filter51_fresh_20260704`). The stale `python -m copier` and exact empty-list `Settings.trust` failures from the prior judge report are no longer present.

## Gate A - Spec Mapping Spot-Check

Verdict: PASS.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_settings_defaults_are_used_when_defaults_mode_is_enabled` | Settings defaults override template question defaults in defaults-mode copy. | `Settings` and `load_settings` | derivable |
| `filter/generated_tests.py::test_cli_copy_with_defaults_renders_template` | `copier copy --defaults TEMPLATE DEST` renders a template to the destination. | CLI Behavior | derivable |
| `filter/generated_tests.py::test_cli_data_takes_precedence_over_data_file` | Explicit CLI `--data` overrides `--data-file`. | CLI Behavior | derivable |
| `filter/generated_tests.py::test_run_recopy_reuses_recorded_source_and_answers` | Recopy uses the recorded template source and answers to render later template changes. | `run_recopy` + Cross-View Invariants + Representative Workflows + Create and Update a Git-Versioned Project | derivable |
| `filter/generated_tests.py::test_error_namespace_exports_documented_base_classes` | Public error namespace exports documented base classes and inheritance. | Installable Surface | derivable |

## Gate B - Failure Pattern Audit

Verdict: PASS. The 15 failures are public behavioral failures.

| cluster | failed tests | evidence | dimension |
|---|---:|---|---|
| Missing CLI carrier / command module | 13 system_e2e | All failing CLI tests invoke the documented `copier` console script and fail with `ModuleNotFoundError: No module named 'copier.__main__'`; reference passes the same tests. | api-surface / workflow-completeness |
| Settings defaults precedence | 1 atomic + 1 integration | API copy with `settings=Settings(defaults={"project": "FromSettings"})` renders `Builtin` instead of `FromSettings`; spec says Settings defaults override template defaults in defaults-mode runs. | atomic-behavior |

The failures check observable outcomes: command exit status, rendered files, answers-file behavior, and documented precedence. They do not depend on private fields, private modules, exact repr text, or exception-message wording.

## Gate C - Generated-Only Oracle Spot-Check

`spec_test_map.md` declares `oracle_source: generated_only`, so generated-only scrutiny applies.

Verdict: PASS for sampled generated tests.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_defaults_mode_uses_question_defaults` | Defaults-mode copy uses a configured question default. | `run_copy` | spec-driven and behavioral |
| `filter/generated_tests.py::test_custom_answers_file_path_is_used_for_recorded_answers` | Template-selected answers file path controls persisted answers. | Answers Files | spec-driven and behavioral |
| `filter/generated_tests.py::test_cli_data_overrides_default` | CLI `--data` value is parsed and used for rendering. | CLI Behavior | spec-driven and behavioral |
| `filter/generated_tests.py::test_load_settings_missing_env_path_returns_empty_with_warning` | Missing env settings path warns and returns empty settings. | `Settings` and `load_settings` | spec-driven and behavioral |
| `filter/generated_tests.py::test_cli_help_lists_copy_recopy_update_and_check_update` | CLI help exposes documented commands. | CLI Behavior + Updates + Check Updates from Automation | spec-driven and behavioral |
| `filter/generated_tests.py::test_run_recopy_reuses_recorded_source_and_answers` | Recopy reuses recorded answers and source. | `run_recopy` + Cross-View Invariants + Representative Workflows + Create and Update a Git-Versioned Project | spec-driven and behavioral |

## Gate D - Coverage Gap Audit

Verdict: PARTIAL acceptable.

The repaired 51-test map covers all core behavioral areas: installable surface, public API, `run_copy`, `run_recopy`, `run_update`, Settings/loading, Phase/VcsRef, CLI behavior, template configuration, rendering, template variables, Settings Reference, answers files, updates/check-update, unsafe features, error semantics, cross-view invariants, and representative workflows.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| Product Overview | framing only | no scoring impact | no action |
| Scope | boundary/framing text | no scoring impact | no action |
| Non-Goals | exclusions rather than positive behavior | no scoring impact | no action |
| Evaluation Notes | evaluator guidance | no scoring impact | no action |

No core invariant section is empty.

## Protocol Issues

None blocking. The prior stale-score issue is repaired: the active score now matches the fresh WSL score and reports 36/51 against the live repaired oracle with no collection errors.

## Real Failure Clusters

| cluster | layer | root cause | affected tests | dimension |
|---|---|---|---:|---|
| CLI command surface missing `copier.__main__` | system_e2e | Candidate exposes API imports but lacks the console-script target needed by the installed `copier` command. | 13 | api-surface / workflow-completeness |
| Settings defaults not applied before template defaults | atomic/integration | Defaults-mode resolution does not give `Settings.defaults` the documented precedence over template question defaults. | 2 | atomic-behavior |

## Cascade Analysis

The 15 failures reduce to two root causes. Thirteen system failures cascade from one missing CLI entry-point/module issue, so they are not independent composition failures. Two API-level failures share one Settings precedence defect. The task remains discriminating: the candidate solves most API/rendering behavior but misses important CLI workflow completeness and one documented default-precedence rule.

## Labels

`discriminating`, `cascade-dominated-cli`, `api-surface`, `workflow-completeness`, `atomic-behavior`

## Final Judge Decision

QUALIFIED. All hard checks pass for the fresh repaired-oracle run: import provenance is valid, reference solvability is 51/51, fairness gates pass, the active candidate score is fresh, and the score provides usable model-failure evidence.
