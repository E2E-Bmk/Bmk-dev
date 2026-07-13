# Diagnosis Report - invoke-taskrunner-fullrepro-001

## Preflight output

Command:

```bash
PYTHONPATH=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-invoke-specv1-20260703-001/output python3 -c 'import invoke; print(invoke.__file__)'
```

Output:

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-invoke-specv1-20260703-001/output/invoke/__init__.py
```

Verdict: QUALIFIED

## Hard Checks

Anti-cheat: PASS. The import provenance points inside the candidate solution directory. The candidate-visible prompt explicitly forbids reading benchmark workflow files, tests, source repositories, score reports, and prior attempts. Static scan of the candidate `output/` source and metadata found no forbidden references to `repo-pool`, oracle artifacts, `spec_test_map`, `kept_nodeids`, score reports, or `pip install invoke` patterns. No separate implementation-phase transcript was present under the candidate run directory; the scanned artifacts were `task_prompt.txt`, candidate `output/`, and the post-run scoring artifacts.

Solvability: PASS. The WSL reference gate used scorer isolation with `--remove-path invoke` and passed 67/67 retained tests in the library-specific scoring environment.

Candidate score: 52/67 overall on Linux/WSL. By layer: atomic 20/30, integration 18/22, system_e2e 14/15.

Protocol issues: none found. The failing samples are spec-driven and behavioral; no oracle mutation, spec patch request, or filter correction request is required.

## Gate A - Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `test_task_decorator_options_set_name_aliases_and_default` | `@task(name=..., aliases=..., default=True)` exposes name, aliases, and default metadata. | `Tasks` | derivable |
| `test_task_arguments_drop_context_and_dash_underscores` | Generated task arguments omit the context parameter and retain Python argument metadata. | `Tasks` | derivable |
| `test_collection_task_names_include_dotted_names_aliases_and_defaults` | Nested default task path and aliases appear in `Collection.task_names`. | `Collections and Namespaces` | derivable |
| `test_config_environment_casts_existing_boolean_and_numeric_defaults` | Existing boolean and numeric config defaults are overridden and cast from `INVOKE_` environment values. | `Configuration` | derivable |
| `test_context_cd_changes_cwd_for_command` | `Context.cd()` affects the command string used by `Context.run`. | `Contexts, Runners, and Results` | derivable |
| `test_context_run_wraps_failing_watcher_in_failure` | Watcher rejection during a command is wrapped as `Failure`. | `Watchers and Prompt Responses` | derivable |
| `test_cli_json_list_reports_tasks_aliases_and_default` | JSON `--list` exposes collection name, task entries, aliases, and default marker. | `CLI Behavior` | derivable |
| `test_cli_environment_variable_overrides_existing_config_key` | CLI task execution sees environment overrides through the same config/context projection. | `Cross-View Invariants` | derivable |
| `test_cli_unknown_task_exits_unsuccessfully` | Unknown CLI task names are parse errors and exit unsuccessfully. | `Error Semantics` | derivable |
| `test_python_module_invocation_runs_same_program` | `python -m invoke` dispatches to the same program as console entry points. | `Invocation Protocol` | derivable |

## Gate B - Failure Pattern Audit

The 15 candidate failures are behavioral public-contract failures, not verifier overreach:

| sample failing nodeid | mapped section | behavioral/spec-driven audit |
|---|---|---|
| `test_task_decorator_options_set_name_aliases_and_default` | `Tasks` | Public `Task` metadata is specified; missing `is_default` is an API-surface gap. |
| `test_task_arguments_drop_context_and_dash_underscores` | `Tasks` | Argument generation is explicitly specified; missing `get_arguments()` blocks observable CLI/parser metadata. |
| `test_collection_task_names_include_dotted_names_aliases_and_defaults` | `Collections and Namespaces` | `task_names` is a documented public projection; default/alias mismatch is observable without inspecting internals. |
| `test_config_supports_dict_and_attribute_access` | `Configuration` | Dict and attribute access are explicit public behavior; `KeyError: runners` is a candidate merge bug. |
| `test_config_unknown_runtime_file_extension_raises` | `Configuration` | Unknown runtime config extension behavior is explicitly specified; wrong lifecycle/raise timing is public error semantics. |
| `test_context_cd_changes_cwd_for_command` | `Contexts, Runners, and Results` | `cd` affecting `Context.run` command/cwd is specified and visible through a configured runner. |
| `test_context_run_wraps_failing_watcher_in_failure` | `Watchers and Prompt Responses` | Watcher rejection translation to `Failure` is documented public behavior. |
| `test_cli_json_list_reports_tasks_aliases_and_default` | `CLI Behavior` | JSON list shape is documented as a public CLI output, not an internal representation. |
| `test_cli_iterable_argument_accumulates_repeated_values` | `CLI Behavior` | Repeated iterable flags accumulating into a list is a documented CLI workflow. |

Gate B verdict: PASS.

Gate C: not applicable. The map declares `oracle_source: upstream`, not `generated_only`.

## Gate D - Coverage Gap Audit

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview` | Framing summary only; concrete behaviors are covered in later sections. | Low | No action. |
| `Scope` | Scope boundary only; concrete in-scope behaviors are covered in API/CLI/config sections. | Low | No action. |
| `Installable Surface` | No direct row mapped to this heading, though imports and entry points are exercised through API and invocation tests. | Low-medium | Consider an explicit import-surface smoke test in a future expansion, but current oracle still exercises exported names used by all tests. |
| `Product State Model` | No direct row mapped to this parent heading; projection consistency is covered under `Cross-View Invariants` plus API sections. | Low | No action. |
| `Public API` | Parent heading only; all child H3 API sections have coverage. | Low | No action. |
| `Representative Workflow` | End-to-end example is not directly mapped; its elements are decomposed across CLI, tasks, config, context, and watcher tests. | Low | No action. |
| `Non-Goals` | Exclusion list, not positive scoreable behavior. | None | No action. |
| `Evaluation Notes` | Benchmark guidance, not product behavior. | None | No action. |

Covered behavioral sections: `Tasks`, `Collections and Namespaces`, `Configuration`, `Contexts, Runners, and Results`, `Watchers and Prompt Responses`, `CLI Behavior`, `Error Semantics`, `Cross-View Invariants`, and `Invocation Protocol`.

Gate D coverage verdict: PARTIAL. No core invariant section is empty; the uncovered headings are framing, parent, non-goal, or evaluation-note sections rather than independent behavioral requirements.

## Real Failure Clusters

1. Task metadata and argument API surface: 4 atomic failures. The candidate omitted public `Task.is_default` and `Task.get_arguments()`, so default metadata and generated argument metadata cannot be inspected as specified.

2. Collection/list projection consistency: 1 atomic plus 1 integration failure. `Collection.task_names` omits the default collection path alias, and JSON `--list` emits a task mapping shape where the spec requires task entries carrying aliases/default metadata.

3. Config source lifecycle/state management: 5 failures. `Config(defaults=...)` does not preserve the documented global default structure needed for `runners.local`, causing `KeyError: runners` across dict/attribute access, cloning, overrides, and environment casting.

4. Error semantics: 2 failures. Unknown runtime file extension is raised during construction instead of the documented runtime load path, and watcher rejection is not wrapped as `Failure` from `Context.run`.

5. Context command state: 1 integration failure. `Context.cd()` stores state but does not apply it to the effective command seen by the configured local runner.

6. CLI iterable workflow completeness: 1 system_e2e failure. Repeated iterable flags are parsed far enough to create a list, but task-call deduplication uses the list in a hash identity and crashes before task execution.

Cascade analysis: 15 failed tests reduce to about 6 root causes. The score is moderately discriminating and cascade-influenced: most integration/system failures are explained by missing primitives in task metadata, config merging, list projection, watcher wrapping, and iterable dedupe rather than a broad end-to-end collapse.

## Labels

`discriminating`, `cascade-dominated`, `api-surface-gaps`, `config-state-lifecycle`, `error-semantics`, `workflow-completeness`
