# Stage 5 Judge Diagnosis: pre-commit-hooks-fullrepro-002

Status: QUALIFIED
Date: 2026-07-03
Candidate run: `candidate-runs/codex-precommit-specv1-20260701-001`
Spec: `wip/pre-commit-hooks-fullrepro-002/spec/spec_v1.md`
Oracle: generated-only WSL oracle, 52 kept tests
Score result: `candidate-runs/codex-precommit-specv1-20260701-001/score_result_wsl_52_precommit002.json`

## Preflight output

Command:

```bash
cd /mnt/g/research/01_agents/swe-e2e/Bmk-dev && PYTHONPATH=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-precommit-specv1-20260701-001/solution python3 -c 'import pre_commit; print(pre_commit.__file__)'
```

Literal output:

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-precommit-specv1-20260701-001/solution/pre_commit/__init__.py
```

## Anti-cheat scan

The import provenance points into the candidate solution directory, not the reference repo, oracle worktree, or an installed package. The WSL score also records `remove_paths: ["pre_commit"]`, which prevents source-tree shadowing during pytest.

`cleanroom_manifest.json` states that the implementation packet contained only `public_packet/spec.md` and `task_prompt.txt`; it explicitly excluded source repositories, tests, filter artifacts, score reports, and previous attempts. `task_prompt.txt` repeats the cleanroom rule that the public spec is the only permitted source and forbids reading tests, benchmark repositories, source repositories, filter artifacts, score reports, and prior candidate runs. No implementation-phase trajectory artifact available in the run directory contradicts that manifest. No cheating evidence found.

## Solvability and platform

Reference score: 52/52 passed, 0 failed, 0 collection errors. The reference artifact platform is `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`, with `remove_paths: ["pre_commit"]` and the library-specific dependency layer noted in `PIPELINE_STATE.md` as `.tmp/precommit-pydeps`. This satisfies the >=95% solvability gate.

Candidate score platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`; not Windows. Candidate score: 43/52 passed, 9 failed, 0 collection errors.

Candidate score by layer:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 19 | 0 | 19 |
| integration | 12 | 7 | 19 |
| system_e2e | 12 | 2 | 14 |

## Gate A - Spec mapping spot-check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_load_manifest_applies_hook_defaults` | `load_manifest()` returns documented hook defaults and normalizes `language: system`. | `## Hook Manifest` | derivable |
| `filter/generated_tests.py::test_load_config_applies_top_level_defaults` | Empty config receives documented top-level defaults, including default install hook type and default stages. | `## Configuration File` | derivable |
| `filter/generated_tests.py::test_store_make_local_reuses_matching_dependency_sets` | `Store.make_local()` reuses cache entries for the same dependency tuple and separates different tuples. | `## Store And Cache` | derivable |
| `filter/generated_tests.py::test_cli_install_and_uninstall_manage_selected_hook_script` | `install` writes a selected hook script and `uninstall` removes it. | `## Installing Git Hooks` | derivable |
| `filter/generated_tests.py::test_cli_run_files_limits_hook_input_to_explicit_files` | `run --files` limits selected filenames to the explicit list. | `## Running Hooks` | derivable |
| `filter/generated_tests.py::test_cli_validate_config_fails_when_any_file_is_invalid` | Multi-file validation returns failure if any config is invalid. | `## Error Semantics` | derivable |

Gate A passes. The sampled rows map to real spec headings, and the expected outcomes are derivable from those sections without private implementation knowledge.

## Spec-test-map consistency audit

`filter/spec_test_map.md` has stale non-row metadata: its title still says `pre-commit-hooks-fullrepro-001`, and its footer says `Covered by layer: atomic=18 | integration=23 | system_e2e=12`, which sums to 53 and is inconsistent with the current 52-test successor oracle. The final rescue note in that file also references the older 53-test predecessor state.

This inconsistency does not affect the accepted score or fairness verdict:

| artifact / source | observed count |
|---|---:|
| `filter/kept_nodeids.txt` | 52 |
| `spec_test_map.md` covered data rows | 52 |
| `taxonomy.jsonl` layer rows | atomic 19, integration 19, system_e2e 14 |
| candidate score `by_layer` | atomic 19, integration 19, system_e2e 14 |
| reference score summary | 52/52 |

The stale title/footer are metadata defects in the map, not scoring inputs and not per-test mappings. The row-level `nodeid`, `source`, `layer`, `spec_section`, and `status` values are internally consistent with the current 52 kept tests and with the score/taxonomy artifacts. Therefore this is recorded as a non-blocking packaging caveat rather than a BROKEN/fairness verdict. The judge role does not modify oracle files.

## Gate B - Failure pattern audit

The nine failures are concentrated in public behavior:

| failure cluster | failed tests | spec basis | verdict |
|---|---:|---|---|
| Loader normalization | 4 | `## Hook Manifest`, `## Configuration File`, `## Bounded Local Languages` | valid model failure |
| Hook resolution defaults | 2 | `## Hook Resolution`, `## Configuration File` | valid model failure |
| CLI install option surface | 1 | `## Command Line Interface`, `## Installing Git Hooks` | valid model failure |
| Config migration semantics | 1 | `## Validation And Utility Behavior` | valid model failure |
| Run fail-fast workflow | 1 | `## Running Hooks` | valid model failure |

No sampled failure depends on private modules, private field names, repr strings, exact long help text, exact terminal column formatting, or exact exception-message wording. Gate B passes.

## Gate C - Generated-only oracle spot-check

`spec_test_map.md` marks this oracle as `filter/oracle_source: generated_only`, so generated tests were manually sampled.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_stages_extend_hook_types_with_manual` | Supported stages are hook types plus `manual`, while hook types do not include `manual`. | `## Configuration File` | spec-driven, behavioral |
| `filter/generated_tests.py::test_load_manifest_normalizes_script_language` | `language: script` is accepted as `unsupported_script`. | `## Bounded Local Languages` and `## Hook Manifest` | spec-driven, behavioral |
| `filter/generated_tests.py::test_all_hooks_resolves_meta_identity_hook` | `repo: meta` exposes the built-in `identity` hook and inherits supported stages. | `## Hook Resolution` | spec-driven, behavioral |
| `filter/generated_tests.py::test_cli_run_pygrep_fails_when_pattern_matches` | `language: pygrep` fails when the configured regex matches a selected file. | `## Bounded Local Languages` | spec-driven, behavioral |
| `filter/generated_tests.py::test_cli_migrate_config_rewrites_legacy_stage_names` | `migrate-config` rewrites legacy stage names to normalized names. | `## Validation And Utility Behavior` and `## Configuration File` | spec-driven, behavioral |
| `filter/generated_tests.py::test_cli_run_fail_fast_stops_after_first_failing_hook` | `run --fail-fast` stops after the first failing hook. | `## Running Hooks` | spec-driven, behavioral |

Gate C passes. The sampled tests check observable outcomes through public APIs or CLI calls. None is circular or tied to internal shapes.

## Gate D - Coverage Gap Audit

Score-bearing behavior sections with direct mapped rows:

| spec section | covered rows | status |
|---|---:|---|
| `## Configuration File` | 14 | covered |
| `## Hook Manifest` | 6 | covered |
| `## Hook Resolution` | 2 | covered |
| `## Store And Cache` | 2 | covered |
| `## Installing Git Hooks` | 1 | covered |
| `## Running Hooks` | 9 | covered |
| `## Bounded Local Languages` | 2 | covered |
| `## Validation And Utility Behavior` | 10 | covered |
| `## Error Semantics` | 6 | covered |

Uncovered headings:

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `## Product Overview` | Narrative summary only. | non-score-bearing | no action |
| `## Scope` | Boundary summary only. | non-score-bearing | no action |
| `## Installable Surface` | Import and console-script surface is exercised by imports and CLI calls, but no row is mapped to this heading. | low; import surface is incidentally covered | no routing required |
| `## Command Line Interface` | Common CLI options are exercised under command-specific sections rather than this overview heading. | low; command behavior covered elsewhere | no routing required |
| `## Cross-View Invariants` | No row is directly mapped to this heading, but invariant substance is exercised by store reuse, validation loader/CLI agreement, install/uninstall script state, migration preservation, hook resolution, and run/file-selection workflows mapped to their concrete behavior sections. | partial direct-map gap, not an empty core behavior gap in substance | record as PARTIAL coverage, no filter loop |
| `## Representative Workflows` / H3 workflow headings | Workflows are decomposed across command/config/hook-resolution rows rather than mapped to the narrative workflow headings. | low | no action |
| `## Non-Goals` | Boundary exclusions. | non-score-bearing | no action |
| `## Evaluation Notes` | Benchmark note, not a behavior contract. | non-score-bearing | no action |

Coverage verdict: PARTIAL acceptable. `## Error Semantics` is directly covered, and the cross-view invariant behaviors are materially covered by executable public workflow tests even though the map uses more specific behavior headings. No unresolved Gate D routing is required for this successor.

## Protocol issues

No spec error, spec gap, or verifier failure was found. No `spec_patch_request.md` or `filter_correction_request.md` is required.

## Real failure clusters

1. Configuration and manifest normalization: 4 integration failures. The candidate leaves `language: system` as `system` instead of the public normalized `unsupported`, leaves `language: script` as `script` instead of `unsupported_script`, and omits `manual` from default stages.
2. Hook resolution consistency: 2 integration failures. Resolved local and meta hook objects do not propagate the public normalized language and stage defaults.
3. CLI install option surface: 1 system_e2e failure. `install` rejects the documented common `--color never` option.
4. Migration semantics: 1 integration failure. `migrate-config` does not rewrite `language: python_venv` to `language: python`.
5. Fail-fast workflow control: 1 system_e2e failure. `run --fail-fast` is not accepted/preserved in a two failing-hook workflow and returns an argparse error instead of the first hook failure.

Cascade analysis: 9 failed tests reduce to five public behavior clusters. There is no import-surface collapse, no collection cascade, and all atomic checks pass; the score is a meaningful discrimination signal for integration/workflow reconstruction.

## Labels

`discriminating`, `generated-only-valid`, `integration-heavy-signal`, `partial-direct-cross-view-map`

## Verdict

QUALIFIED. Hard checks pass: preflight imports from candidate solution, reference is 52/52 on Linux/WSL, candidate score is 43/52 on Linux/WSL, generated-only Gate C passes, and Gates A/B/D do not reveal verifier unfairness requiring another loop. The stale `spec_test_map.md` title/footer layer summary is a non-blocking metadata inconsistency because the 52 covered rows, kept nodeids, taxonomy, reference score, and candidate score all agree on the actual scoring set.
