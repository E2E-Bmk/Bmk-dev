# Diagnosis Report - tox-envrunner-fullrepro-001

## Verdict

Status: QUALIFIED

The oracle is valid for judging this candidate run. The candidate failures are real public tox behavior gaps, not an environment, provenance, or verifier fairness failure.

## Preflight output

Command:

```bash
PYTHONPATH=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-tox-specv1-20260701-001/solution .envs/s4-score-linux/bin/python -c "import tox; print(tox.__file__)"
```

Literal output:

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-tox-specv1-20260701-001/solution/tox/__init__.py
```

The literal `__file__` resolves inside the candidate solution directory.

## Anti-Cheat

Import provenance passed. The candidate solution directory was scanned for forbidden provenance indicators including `repo-pool`, `kept_nodeids`, `spec_test_map`, `reference_score`, `score_result`, `filter/`, `wip/`, `tests/`, and `conftest.py`; no hits were found in solution files. The cleanroom manifest and run prompt include only `public_packet/spec.md` and `task_prompt.txt`. No full terminal transcript is available, so the conclusion is based on import provenance, manifest, prompt, and solution scan.

## Solvability

Reference score: 31/31 passed, pass rate 100.0%.

Layer ceiling:

| layer | reference |
|---|---|
| atomic | 9/9 |
| integration | 17/17 |
| system_e2e | 5/5 |

Scorer isolation used `--remove-path tox`. The oracle has no collection errors and no unknown taxonomy layer.

## Fairness Gates

Gate A, spec mapping spot-check: PASS.

| sampled test | mapped section | judgment |
|---|---|---|
| `test_tox_ini_is_discovered_before_tox_toml` | Configuration Files | The spec states configuration discovery and precedence; the test checks public `tox list` output for selected config. |
| `test_ini_generative_env_list_expands_and_substitutes_env_name` | Environment Selection | The spec describes generative env lists, factor selection, and `{env_name}` substitution. |
| `test_toxfile_plugin_can_add_env_config_key` | Public API | The public plugin hook is listed and the test checks public config output after hook registration. |
| `test_schema_command_includes_core_sections` | Cross-View Invariants | The spec requires schema/config projections to expose public configuration sections. |
| `test_pep723_runner_rejects_base_python_override` | Error Semantics | The spec requires handled non-zero errors for inconsistent configuration. |

Gate B, failure pattern audit: PASS.

Candidate failures are public-surface and behavioral: config file discovery, environment expansion, labels/factors, config/schema projections, plugin-added config, module invocation/version, and selected run behavior. The tests assert observable CLI/API/file outputs, not private classes, private attributes, repr strings, or implementation-only shapes.

Gate C, generated-only spot-check: not applicable. `spec_test_map.md` is `oracle_source: upstream_and_generated`, not generated-only.

## Gate D - Coverage Gap Audit

Coverage verdict: PARTIAL.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| Product Overview, Scope, Non-Goals, Evaluation Notes | framing sections, not independent executable behavior | acceptable | no action |
| Packaging | package build modes are not directly asserted by this oracle | secondary gap; environment lifecycle tests still exercise package=skip and command execution | future enrichment can add owned packaging cases |
| Representative Workflows | examples are decomposed across config/list/config/run tests rather than mapped to this heading | acceptable | no action |

Core sections for configuration, environment selection, lifecycle, substitutions, commands/env vars, parallel/failure behavior, error semantics, and cross-view invariants all have coverage.

## Candidate Score

Candidate score: 4/31 passed, pass rate 12.90%.

| layer | candidate result |
|---|---|
| atomic | 1/9 passed |
| integration | 0/17 passed |
| system_e2e | 3/5 passed |

## Real Failure Clusters

| cluster | dimension | evidence |
|---|---|---|
| CLI/config projection completeness | workflow-completeness | Most `tox config`, `tox schema`, `tox list`, and output-file tests fail or emit run-like `py: OK` output instead of structured config/schema data. |
| Environment selection and generative names | workflow-completeness | Factor expansion and `--no-desc` list behavior produce wrong names or run status strings. |
| Cross-view consistency | cross-view-consistency | `tox list`, `tox config`, labels, inherited TOML values, and dependency order disagree across public views. |
| Public API / plugin surface | api-surface | Plugin config hook behavior and module/version invocation are incomplete. |
| Error semantics | error-semantics | Mutually exclusive option and PEP 723/base_python failures do not preserve expected public error surface. |

Cascade analysis: the 27 failures represent several root families, dominated by an incomplete CLI/config engine rather than one import collapse. This is a discriminating score, not a saturated or broken run.
