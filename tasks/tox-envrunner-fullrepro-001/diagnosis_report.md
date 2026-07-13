# Stage 5 Diagnosis Report: tox-envrunner-fullrepro-001 WSL 51-test Rejudge

Date: 2026-07-03

Verdict: QUALIFIED

This report is a legal Stage 5 re-judge for the 51-test Linux/WSL score. It repairs the prior History risk where the task was left as QUALIFIED after a retroactive Gate D oracle expansion without a candidate rerun. The 51-test candidate score used here is the WSL rerun in `candidate-runs/codex-tox-specv1-20260701-001/score_result.json`.

## Anti-Cheat Preflight

Command:

```powershell
python -c "import tox; print(tox.__file__)"
```

Working directory:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-tox-specv1-20260701-001\solution
```

### Preflight output

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-tox-specv1-20260701-001\solution\tox\__init__.py
```

Provenance verdict: PASS. The imported `tox` package resolves inside the candidate solution directory.

## Anti-Cheat Scan

The cleanroom manifest says the candidate-visible inputs were only `public_packet/spec.md` and `task_prompt.txt`, while hidden benchmark assets, reference artifacts, prior runs, filter files, tests, and scoring outputs were excluded by policy.

I scanned the candidate solution, prompt, and manifest for forbidden implementation-phase indicators including `repo-pool`, `kept_nodeids`, `spec_test_map`, score reports, reference scores, oracle carrier paths, copied tests, and `pip install tox` patterns. No forbidden hit was found in the candidate solution or prompt. The candidate score also used `remove_paths: ["tox"]`, and the preflight above confirms imports come from the candidate solution.

Anti-cheat verdict: PASS.

## Solvability

Reference score source: `wip/tox-envrunner-fullrepro-001/filter/reference_score_retro_gate_d.json`.

Reference result: 51/51 passed, pass rate excluding skips 1.0. This is above the required 95% solvability threshold.

| layer | reference result |
|---|---:|
| atomic | 13/13 |
| integration | 28/28 |
| system_e2e | 10/10 |

Reference solvability verdict: PASS.

## Candidate Score

Candidate score source: `candidate-runs/codex-tox-specv1-20260701-001/score_result.json`.

Platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`.

Candidate result: 11/51 passed, 40 failed, pass rate excluding skips 0.21568627450980393.

| layer | candidate result |
|---|---:|
| atomic | 3/13 |
| integration | 2/28 |
| system_e2e | 6/10 |

The run directory recorded in the score is `/mnt/g/research/01_agents/swe-e2e/Bmk-dev/.tmp/retro-candidate-scores/tox-wsl-rerun-20260703`, so this is not the stale 31-test candidate score.

## Gate A - Spec Mapping Spot-Check

Gate A verdict: PASS.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_tox_ini_is_discovered_before_tox_toml` | Public `tox list` uses `tox.ini` when both `tox.ini` and `tox.toml` are present. | `Configuration Files` | derivable |
| `filter/generated_tests.py::test_ini_generative_env_list_expands_and_substitutes_env_name` | INI brace expansion produces the expected environment names and resolves `{env_name}` in config. | `Environment Selection` | derivable |
| `filter/generated_tests.py::test_config_json_preserves_native_types_and_inherited_values` | JSON config output preserves inherited settings and native list/bool values. | `Cross-View Invariants` | derivable |
| `filter/generated_tests.py::test_mutually_exclusive_no_capture_and_result_json_fails_before_writing_json` | Mutually exclusive CLI options fail before result JSON is written. | `Error Semantics` | derivable |
| `filter/rewritten_upstream_tests.py::test_toxfile_plugin_can_add_env_config_key` | A project-local `toxfile.py` hook can add an environment config key visible through public config output. | `Public API` | derivable |
| `filter/rewritten_upstream_tests.py::test_recreate_flag_recreates_environment` | `tox run -r` forces recreation and updates observable environment state. | `Environment Lifecycle` | derivable |

The sampled rows quote exact H2 headings from `spec/spec_v1.md`. They assert public CLI/API behavior rather than private object shape.

## Gate B - Failure Pattern Audit

Gate B verdict: PASS.

The 40 candidate failures are consistent with documented public behavior gaps:

| cluster | failed tests | dimension | audit result |
|---|---:|---|---|
| Config/list/schema projection and cross-view consistency | 32 | cross-view-consistency | Real model failures. The candidate often ran environments and printed status lines such as `py: OK` where the spec requires list/config/schema projections, JSON/TOML output, selected keys, labels, factors, or inherited values. |
| Public CLI/API surface | 4 | api-surface | Real model failures. Examples include `main(["--version"])` returning failure and CLI help/version behavior not matching the documented public entry point. |
| Error semantics | 3 | error-semantics | Real model failures. Handled error surfaces for mutually exclusive options, missing interpreters, and PEP 723 `base_python` rejection are incomplete or too generic. |
| Workflow command execution | 1 | workflow-completeness | Real model failure. The candidate does not fully preserve the documented `tox exec`/run command split in the selected scenario. |

The failures are behavioral and observable through public imports, CLI invocations, config files, subprocess return codes, stdout/stderr, and generated files. They do not depend on private tox modules, private attributes, exact repr strings, or source layout.

Cascade analysis: the score is dominated by an incomplete config/list/schema engine and cross-view projection layer, not by one import failure. The system_e2e pass rate is higher than integration because some command-running primitives work, while projection-heavy tests expose missing public behavior.

## Gate C - Generated-Only Oracle Spot-Check

Gate C is not required. `spec_test_map.md` declares `oracle_source: upstream_and_generated`, not `generated_only`.

Additional check: generated rows sampled during Gate A are spec-driven and behavioral. No circular or internal-shape generated assertion was identified in the sampled set.

## Gate D - Coverage Gap Audit

Gate D verdict: PASS with PARTIAL coverage.

`spec_test_map.md` contains 51 covered rows and no `spec_gap`, `source-only`, or `excluded` final rows. Coverage by behavioral section:

| spec section | covered rows | verdict |
|---|---:|---|
| Installable Surface | 3 | covered |
| Public API | 5 | covered |
| Configuration Files | 9 | covered |
| Environment Selection | 9 | covered |
| Environment Lifecycle | 1 direct + 1 shared with Representative Workflows | covered |
| Packaging | 2 | covered |
| Substitutions and Conditional Values | 5 | covered |
| Environment Variables and Commands | 3 | covered |
| Parallel and Failure Behavior | 2 | covered |
| Error Semantics | 5 | covered |
| Cross-View Invariants | 6 | covered |
| Representative Workflows | 1 shared with Environment Lifecycle | covered |

Uncovered sections:

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| Product Overview | Narrative framing, not an independently testable contract. | None for scoring validity. | No action. |
| Scope | Boundary summary, decomposed into behavioral sections below. | None for scoring validity. | No action. |
| Non-Goals | Negative boundary statements rather than required candidate behavior. | None for scoring validity. | No action. |
| Evaluation Notes | Benchmark guidance, not candidate-visible library behavior. | None for scoring validity. | No action. |

Coverage verdict: PARTIAL. No core invariant section is empty. `Cross-View Invariants` and `Error Semantics` both meet the higher core coverage expectation, and the remaining zero-coverage headings are non-behavioral framing/boundary sections.

## Protocol Issues

No Stage 5 protocol issue blocks qualification after this rejudge.

The old History row that described a retroactive 31-to-51 Gate D supplement without a candidate rerun is superseded by the 2026-07-03 WSL score and this report. The candidate was rerun against the 51-nodeid oracle, the score JSON platform confirms Linux/WSL, the reference score passes 51/51, and this report contains the required preflight output before citing score values.

## Real Failure Clusters

| cluster | dimension | evidence | affected tests |
|---|---|---|---|
| Config/list/schema projection completeness | cross-view-consistency | `tox list`, `tox config`, and `tox schema` frequently emit command-run output or non-JSON text instead of the documented projected configuration/schema views. | 32 failures, mostly integration |
| Environment generation and selection | workflow-completeness | INI/TOML factor expansion, label selection, generated env names, and dependency views do not compose consistently across list/config/depends. | included in the 32 projection failures |
| Public entry-point behavior | api-surface | `main(["--version"])` and module/CLI version behavior fail when no config is present, despite the spec documenting the public entry point. | 4 atomic/API failures |
| Handled error semantics | error-semantics | Mutually exclusive options, missing interpreters, PEP 723 runner restrictions, and dependency/deps conflicts are not consistently reported through documented handled errors. | 3 direct failures plus related cascades |

## Labels

- `discriminating`
- `cross-view-consistency-signal`
- `workflow-completeness`
- `not-saturated`

## Final Verdict

QUALIFIED. The 51-test WSL oracle is reference-solvable, provenance is clean, Gate A/B/D pass, Gate C is not applicable, and the candidate failures are legitimate public tox behavior gaps.
