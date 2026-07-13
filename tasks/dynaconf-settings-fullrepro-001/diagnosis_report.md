# WSL Task Judge Diagnosis - dynaconf-settings-fullrepro-001

Date: 2026-07-03
Judge role: SWE-E2E Stage 5 task-judge subagent
Task wip: `wip/dynaconf-settings-fullrepro-001/`
Candidate run: `candidate-runs/codex-dynaconf-trackb-specv2-20260630-001/`
WSL score result: `candidate-runs/codex-dynaconf-trackb-specv2-20260630-001/score_result_wsl.json`
Canonical oracle files: `filter/kept_nodeids.txt`, `filter/taxonomy.jsonl`, `filter/spec_test_map.md`, `filter/reference_score.json`

## Recommendation

Verdict recommendation: keep `QUALIFIED`.

Route: no BROKEN or RETIRED route is warranted. The WSL score artifact has one verifier/runner encoding collection error caused by a UTF-8 BOM in `kept_nodeids.txt`; this should be treated as scorer/filter hygiene for a clean WSL rerun, not as a task fairness failure and not as a real model behavior failure. The task remains legally QUALIFIED because the canonical oracle is behavioral/spec-driven, reference solvability is 51/51, dummy gate is 0/51, and the candidate still shows discriminating public-behavior failures.

I did not modify `PIPELINE_STATE.md`, `CANDIDATES.md`, `weakness_table.md`, or `tasks/`.

## Entry State Note

`PIPELINE_STATE.md` currently records `state: QUALIFIED`, not `S5_JUDGE`. This report is therefore a WSL post-qualification audit of the existing candidate run, not a state-machine transition. Per instruction, no pipeline state edits were made.

## Anti-Cheat

Preflight command run before reading or quoting the WSL score:

```bash
wsl bash -lc "cd /mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-dynaconf-trackb-specv2-20260630-001 && PYTHONPATH=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-dynaconf-trackb-specv2-20260630-001/output python3 -c 'import dynaconf; print(dynaconf.__file__)'"
```

Preflight output:

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-dynaconf-trackb-specv2-20260630-001/output/dynaconf/__init__.py
```

The import provenance points into the candidate output package. The WSL score JSON also records `remove_paths: ["dynaconf"]` and `solution_dir: /mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-dynaconf-trackb-specv2-20260630-001/output`, consistent with scoring the candidate rather than the oracle worktree or an installed package.

Cleanroom evidence: `cleanroom_notes.md` and `task_prompt.txt` restrict the implementation phase to `spec.md` and `output/`. Static scan of `candidate-runs/.../output` found no forbidden references to `repo-pool`, `wip`, `generated_tests`, score reports, hidden tests, oracle artifacts, or `pip install dynaconf`. Mentions of `repo-pool` and oracle paths inside `score_wsl_filter51/oracle_worktree` are evaluation-stage artifacts, not candidate implementation artifacts.

## Platform And Solvability

The WSL score is a Linux/WSL run:

```text
platform: Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31
python_version: 3.11.15
```

Canonical reference evidence from `filter/reference_score.json`:

```text
status: pass
oracle_source: generated_only
total: 51
passed: 51
failed: 0
errors: 0
by_layer: atomic 15/15, integration 30/30, system_e2e 6/6
```

Canonical dummy evidence from `filter/dummy_gate_report.json`:

```text
status: pass
total: 51
dummy_passed: 0
dummy_failed: 51
```

This satisfies solvability and anti-dummy requirements for the canonical oracle. The reference evidence is not a low-ceiling or dependency-missing run.

## WSL Score Summary

`score_result_wsl.json` summary:

```text
passed: 36
failed: 14
collection_error: 1
total: 51
pass_rate_excluding_skips: 0.7058823529411765
```

Layer summary:

```text
atomic: 10 passed, 4 failed, total 14
integration: 21 passed, 9 failed, total 30
system_e2e: 5 passed, 1 failed, total 6
unknown: 1 collection_error, total 1
```

The main WSL pytest report collected and ran 50 tests: 36 passed and 14 failed. The separate collection error attempted to run:

```text
锘縢enerated_tests.py::test_public_import_surface_exposes_configured_visible_state
```

Pytest stderr:

```text
ERROR: file or directory not found: 锘縢enerated_tests.py::test_public_import_surface_exposes_configured_visible_state
```

Root cause: the canonical `kept_nodeids.txt` starts with UTF-8 BOM bytes:

```text
EF BB BF 67 65 6E 65 72 61 74 65 64 5F 74 65 73
```

Those bytes precede the first ASCII nodeid, `generated_tests.py::test_public_import_surface_exposes_configured_visible_state`. The WSL runner decoded the BOM incorrectly and passed a bogus filename to pytest. The test itself exists in `filter/generated_tests.py`, is mapped in `spec_test_map.md`, and is included in reference/dummy evidence. Therefore this is a scorer/filter encoding issue, not a model behavior failure and not evidence that the oracle assertion is invalid.

This collection error does not block the task from remaining QUALIFIED. It should be recorded as a WSL artifact caveat and fixed by stripping the BOM or reading nodeids as `utf-8-sig` before any future WSL score rerun.

## Gate A - Spec Mapping Spot Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `generated_tests.py::test_public_import_surface_exposes_configured_visible_state` | Public imports resolve and constructor keyword settings are visible through attribute access and `as_dict()`. | `## Public Import Surface` | derivable |
| `generated_tests.py::test_environment_default_global_and_active_values` | Active environment values override default values while default and global values remain visible in the active view. | `## Layered Environments` and mapped stricter section `## Cross-View Invariants` | derivable |
| `generated_tests.py::test_file_declared_dynaconf_include_loads_relative_file` | `dynaconf_include` inside a settings file loads the referenced relative file. | `## File Loading` | derivable |
| `generated_tests.py::test_auto_cast_false_leaves_envvar_tokens_as_strings` | With `auto_cast=False`, explicit casting tokens remain uninterpreted while ordinary envvar TOML parsing remains public behavior. | `## Casting Tokens and Lazy Values` | derivable |
| `generated_tests.py::test_validator_callable_default_can_read_settings_context` | Callable validator defaults can read the settings context. | `## Validators` | derivable |
| `generated_tests.py::test_cli_list_json_filters_by_key` | CLI `list --json --key` filters user-defined settings and prints JSON. | `## CLI Behavior` | derivable |

Spot-check result: pass. The sampled rows are spec-driven and behavioral. They assert public outputs and visible state, not internal field names, repr strings, or private module structure.

## Gate B - Failure Pattern Audit

The 14 executed WSL failures are public behavior failures:

```text
integration  generated_tests.py::test_merge_marker_combines_environment_dictionary
integration  generated_tests.py::test_environment_default_global_and_active_values
integration  generated_tests.py::test_file_declared_dynaconf_include_loads_relative_file
integration  generated_tests.py::test_comma_separated_active_envs_load_in_order
integration  generated_tests.py::test_from_env_keep_chains_existing_values
integration  generated_tests.py::test_auto_cast_false_leaves_envvar_tokens_as_strings
atomic       generated_tests.py::test_get_token_reads_another_setting_and_casts_default
integration  generated_tests.py::test_insert_token_adds_list_item_at_requested_position
integration  generated_tests.py::test_global_merge_enabled_merges_later_dictionaries_and_lists
atomic       generated_tests.py::test_validator_or_and_and_composition
atomic       generated_tests.py::test_validator_callable_default_can_read_settings_context
atomic       generated_tests.py::test_validator_casts_are_ordered_and_mutate_state
integration  generated_tests.py::test_fresh_var_reloads_source_on_access
system_e2e   generated_tests.py::test_cli_list_json_filters_by_key
```

Failure examples:

- Merge/cross-view: `settings.get("database.host")` returns `None` where file data must remain visible after an envvar `@merge`.
- Layered environments: default/global values such as `SIZE`, `DEV_ONLY`, or `SHARED` are missing from active or chained environment views.
- File loading: `dynaconf_include` does not load the referenced relative file.
- Casting tokens: `@insert` inserts the wrong list item, and `@get` default typing diverges from the expected public behavior.
- Validators: composed validators and validator casts/defaults do not mutate or read the same public settings state.
- Runtime state: `fresh_vars` does not reload source values on later access.
- CLI: `list --json --key FOO` returns JSON without the requested `FOO` key.

These are observable public outcomes. The majority does not cluster around undocumented internal shapes. Gate B passes.

## Gate C - Generated-Only Oracle Spot Check

`spec_test_map.md` declares `filter/oracle_source: generated_only`, so generated-only sampling is mandatory.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `generated_tests.py::test_public_import_surface_exposes_configured_visible_state` | Public names import from `dynaconf`; configured values are visible through public accessors. | `## Public Import Surface` | spec-driven and behavioral |
| `generated_tests.py::test_merge_marker_combines_environment_dictionary` | Envvar `@merge` combines a dictionary with existing file dictionary data and hides marker syntax from visible state. | `## Merge Semantics` and mapped stricter section `## Cross-View Invariants` | spec-driven and behavioral |
| `generated_tests.py::test_environment_default_global_and_active_values` | Default, global, and active environment values project into one final active environment view. | `## Layered Environments` and mapped stricter section `## Cross-View Invariants` | spec-driven and behavioral |
| `generated_tests.py::test_validator_callable_default_can_read_settings_context` | Callable validator defaults can inspect current settings during validation. | `## Validators` | spec-driven and behavioral |
| `generated_tests.py::test_cli_list_json_filters_by_key` | CLI `list --json --key` exposes the requested user setting as JSON. | `## CLI Behavior` | spec-driven and behavioral |
| `generated_tests.py::test_cli_get_missing_key_without_default_returns_nonzero` | Missing CLI key without default exits nonzero. | `## Error Semantics` | spec-driven and behavioral |

No sampled generated test is circular or internal-shape-based. Gate C passes.

## Gate D - Coverage Gap Audit

Covered score-bearing `spec_v2.md` sections from `spec_test_map.md`:

```text
## Public Import Surface
## Constructing Settings
## Source Loading Order
## File Loading
## Layered Environments
## Environment Variables
## Casting Tokens and Lazy Values
## Accessing Settings
## Runtime Updates
## Merge Semantics
## Validators
## Hooks
## Inspection and History
## CLI Behavior
## Error Semantics
## Cross-View Invariants
```

Uncovered score-bearing sections: none. `## Product Overview` and `## Non-Goals` are contextual rather than direct score-bearing behavior sections.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| none | none | no coverage gap | keep QUALIFIED |

Coverage verdict: FULL for score-bearing sections. Core invariant sections `## Cross-View Invariants`, `## Error Semantics`, and state lifecycle sections have mapped coverage. Gate D passes.

## Real Failure Clusters

The WSL failures collapse into the same meaningful capability clusters as the non-WSL Stage 5 report, except the public import surface test was not executed in WSL because of the BOM nodeid issue.

| dimension | root behavior gap | affected executed WSL tests |
|---|---|---|
| `cross-view-consistency` | File/env merge and default/global active environment state do not remain visible through the same public access views. | merge marker, global merge, default/global active environment |
| `state-management` | Environment chaining and fresh source reload do not maintain or refresh state according to public lifecycle semantics. | comma env list, `from_env(keep=True)`, `fresh_vars` |
| `atomic-behavior` | Casting token parsing and validator composition/casts/defaults diverge from documented public behavior. | `@get`, `@insert`, validator OR/AND, callable default, ordered casts |
| `workflow-completeness` | CLI JSON key filtering fails despite other CLI workflows passing. | `cli_list_json_filters_by_key` |
| `api-surface` | Public import/configured-state coverage is valid but was not executed in WSL because of the BOM nodeid collection error. | collection artifact only in WSL; real candidate failure was observed in the prior canonical Stage 5 report |

Cascade analysis: the 14 executed failures represent several root behavior gaps rather than a single import collapse. The WSL collection error is orthogonal to these model failures.

## Final Verdict

Keep `QUALIFIED`.

The single WSL `collection_error` is a verifier/runner encoding issue from a BOM-prefixed first nodeid. It is not a real model failure and not an oracle fairness failure. It also does not make the task BROKEN or RETIRED because the canonical oracle artifacts show 51/51 reference solvability, 0/51 dummy pass, full score-bearing spec coverage, and generated-only spot checks that are behavioral and spec-driven.

Operational follow-up: strip the BOM from `kept_nodeids.txt` or make the WSL scorer read nodeids with `utf-8-sig`, then rerun WSL scoring if a clean no-collection-error WSL score artifact is required.
