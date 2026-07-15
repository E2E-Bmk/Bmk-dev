# Task Judge Diagnosis — astroid

run_id: codex-astroid-specv2-20260708-002
candidate_output: /Users/zijian/bench/Bmk-dev/candidate-runs/codex-astroid-specv2-20260708-002/output/
verdict: QUALIFIED
route: terminal
reason: hard checks and fairness gates pass for the repaired spec_v2 generated-only oracle; the remaining six failures are real candidate behavior gaps.

## Preflight output

```text
/Users/zijian/bench/Bmk-dev/candidate-runs/codex-astroid-specv2-20260708-002/output/astroid/__init__.py
```

## Entry State

`PIPELINE_STATE.md` was read after the task-judge skill file. The current state was `S5_JUDGE`, and `/Users/zijian/bench/Bmk-dev/candidate-runs/codex-astroid-specv2-20260708-002/score_result.json` exists.

This report intentionally re-judges spec_v2/run 002 and does not carry forward the old spec_v1/run 001 BROKEN verdict.

## Hard Checks

Anti-cheat provenance: PASS. The required preflight imports `astroid` from the candidate output directory, not from the oracle worktree or an installed package.

Candidate prompt/output scan: PASS with available evidence. `task_prompt.txt` contains no `INTERNAL` header and no hits for forbidden implementation-time artifacts such as `repo-pool`, `spec_test_map`, `kept_nodeids`, `score_result`, `reference_score`, `candidate-runs`, or oracle/filter paths. Candidate-created files are confined to `candidate-runs/codex-astroid-specv2-20260708-002/output/`:

- `pyproject.toml`
- `astroid/__init__.py`
- `astroid/__main__.py`
- `astroid/exceptions.py`
- `astroid/manager.py`
- `astroid/nodes.py`

Limitation: the run directory does not contain a full agent trajectory log. The anti-cheat scan therefore cannot prove absence of forbidden reads beyond the prompt, output, and scoring artifacts available in the candidate run.

Reference solvability: PASS. `filter/reference_score.json` reports `79/79` passing, collected `79`, using the reference solution directory `/Users/zijian/bench/repo-pool/astroid-main`.

Dummy solvability gate: PASS. `filter/dummy_score.json` reports `0/79` passing on the minimal dummy package.

Scorer isolation: PASS. `MANIFEST.json` records `score_pytest_original.py` with `--remove-path astroid`, `runner_python=Bmk-dev/.venv-pyramid/bin/python`, reference result `79/79 passed`, and dummy result `0/79 passed`.

Candidate score observed after hard checks: `73/79` passed. Layer breakdown:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 47 | 4 | 51 |
| integration | 18 | 0 | 18 |
| system_e2e | 8 | 2 | 10 |

## Gate A — Spec Mapping Spot Check

Verdict: PASS.

Sampled covered rows from `spec_test_map.md` map to behavior-bearing spec sections that exist in `spec_v2.md` and whose expected outcomes are derivable from those sections:

| sampled row | mapped section | judgment |
|---|---|---|
| `test_parse_returns_module_with_name_and_path` | Parsing and Extraction | Spec-driven and behavioral: checks returned `Module`, name, and path. |
| `test_statement_returns_nearest_statement_node` | Nodes | Spec-driven and behavioral: checks `statement()` nearest statement behavior after public extraction. |
| `test_scope_parentless_non_scope_raises_parent_missing_error` | Nodes | Spec-driven and behavioral: repaired setup obtains the node through public extraction, then detaches it to trigger documented parentless scope behavior. |
| `test_repr_tree_respects_max_depth_truncation_signal` | Nodes | Spec-driven and behavioral: repaired assertion checks truncation by output differences/length relation, not exact internal field text. |
| `test_lookup_missing_name_returns_builtin_scope_without_statements` | Nodes | Spec-driven to spec_v2 lookup behavior, though the row should more naturally map to `Lookup and Inference`; the assertion itself is behavioral. |
| `test_cli_without_subcommand_returns_usage_error` | Installable Surface | Spec-driven and behavioral: checks exit code 2 and usage presence, not exact help text. |
| `test_public_exception_aliases_match_resolution_categories` | Error Semantics | Spec-driven and behavioral: checks public exception category aliases and unresolved-name raise category. |
| `test_cross_view_class_instance_and_attribute_lookup_share_tree_state` | Cross-View Invariants | Spec-driven through Product State Model binding/inference projection plus cross-view consistency; checks public `ClassDef`/`Instance` lookup behavior. |

The one imperfect row label (`lookup_missing_name` mapped to `Nodes`) is a mapping precision issue, not a fairness failure: the relevant behavior is explicitly specified in `Lookup and Inference`, and the test remains spec-driven and public.

## Gate C — Generated-Only Oracle Spot Check

`spec_test_map.md` declares `filter/oracle_source: generated_only`, so this gate manually samples generated tests before accepting candidate failures as model evidence.

Verdict: PASS.

| sampled generated test | required coverage | spec-driven? | behavioral? | judgment |
|---|---|---:|---:|---|
| `test_scope_parentless_non_scope_raises_parent_missing_error` | repaired `scope_parentless` | yes | yes | Uses `astroid.extract_node("1")` then detaches `parent`; no constructor-only assumption remains. |
| `test_repr_tree_respects_max_depth_truncation_signal` | repaired `repr_tree` | yes | yes | Checks depth truncation through relative output change/length, not exact `repr_tree` body fragments. |
| `test_lookup_missing_name_returns_builtin_scope_without_statements` | repaired missing lookup | yes | yes | Matches spec_v2: unresolved lookup returns builtins scope with empty statements. |
| `test_cli_without_subcommand_returns_usage_error` | repaired CLI usage | yes | yes | Checks documented exit code 2 and presence of usage text, not exact wording. |
| `test_cli_ast_command_prints_repr_tree_for_valid_file` | CLI valid file | yes | yes | Checks exit code 0 and structural `repr_tree` markers for a valid Python file. |
| `test_cross_view_extract_node_parent_chain_and_rendering_are_consistent` | cross-view/workflow | yes | yes | Checks that `__(...)` extraction removes wrapper consistently from selected expression and parent statement rendering. |
| `test_representative_workflow_parse_infer_extract_and_extend` | workflow | yes | yes | Directly follows the Representative Workflow section: parse, infer constant, extract nodes, register extender, expose public names. |
| `test_public_exception_aliases_match_resolution_categories` | repaired exception aliases | yes | yes | Uses public exception categories and alias relationships; no message wording or private fields. |

## Gate B — Failure Pattern Audit

Verdict: PASS. All six failures are traceable to public spec behavior and check observable outcomes rather than implementation internals.

| failing test | layer | dimension | model failure judgment |
|---|---|---|---|
| `test_statement_returns_nearest_statement_node` | atomic | atomic-behavior | Real. `extract_node`/`statement()` should expose the marked return-line statement path; candidate returns a path whose nearest statement is `FunctionDef`. |
| `test_infer_unknown_dynamic_call_yields_uninferable_or_result_boundary` | atomic | error-semantics | Real. Unresolved name inference must raise the public `NameInferenceError` category for this name-inference path. |
| `test_uninferable_is_identity_comparable_sentinel` | atomic | error-semantics | Real. Candidate misses the same unresolved-name raise path before the public sentinel identity checks. |
| `test_public_exception_aliases_match_resolution_categories` | atomic | error-semantics | Real. The unresolved-name raise path fails, preventing validation of the public resolution category aliases. |
| `test_cross_view_extract_node_parent_chain_and_rendering_are_consistent` | system_e2e | cross-view-consistency | Real. Candidate removes the wrapper for the selected expression but leaves `__(...)` in the parent statement rendering. |
| `test_cross_view_class_instance_and_attribute_lookup_share_tree_state` | system_e2e | api-surface | Real. Candidate lacks `ClassDef.getattr`, so class attribute lookup and inferred instance attribute lookup cannot share the parsed tree state. |

No failing test depends on private attributes, exact error messages, exact repr fragments, memory identity beyond the public `Uninferable` sentinel contract, or candidate-invisible oracle data.

## Real Failure Clusters

| cluster | root cause | dimension | affected tests | cascade |
|---|---|---|---|---|
| Marked return-line statement selection | Extracted node or parent chain points to the enclosing function for `statement()` instead of the nearest return statement. | atomic-behavior | 1 atomic | Standalone. |
| Unresolved-name inference error category | Missing `NameInferenceError` raise for unresolved names. | error-semantics | 3 atomic | One root behavior causes the unknown-call, sentinel smoke, and alias-category failures. |
| Wrapper removal across parent rendering | `extract_node("__(...)")` selection is rendered correctly, but its parent statement still includes the marker call. | cross-view-consistency | 1 system_e2e | Standalone cross-view failure. |
| Class/instance attribute lookup surface | `ClassDef.getattr` is absent, blocking class-to-instance attribute consistency. | api-surface | 1 system_e2e | Standalone public API gap. |

Cascade analysis: six failing tests reduce to four root causes. The error-semantics cluster accounts for three atomic failures; the two system failures are independent cross-view/API-surface gaps rather than cascades from primitive import or collection errors. This run provides discriminating signal: the candidate passes all integration tests and most atomic/system tests, but still misses specific public behavior.

## Gate D — Coverage Gap Audit

Coverage verdict: FULL.

Behavior-bearing H2/H3 sections have at least one `covered` generated row in `spec_test_map.md`. Container/meta sections are listed below as exempt because their behavior is decomposed into concrete child sections or evaluation guidance.

| spec section | covered rows | FULL/PARTIAL/GAP verdict | uncovered behaviors | impact | recommendation |
|---|---:|---|---|---|---|
| Product Overview | 0 | FULL | None; overview only. | None. | No action. |
| Scope | 0 | FULL | None; scope boundary only. | None. | No action. |
| Installable Surface | 4 | FULL | None. | Public imports/CLI covered. | No action. |
| Product State Model | 0 | FULL | None as standalone; invariants are covered under `Cross-View Invariants`. | None. | No action. |
| Public API | 0 | FULL | None; container for H3 sections. | None. | No action. |
| Parsing and Extraction | 10 | FULL | None. | Core parsing/extraction covered. | No action. |
| Nodes | 25 | FULL | None. | Node traversal/rendering/scope behavior covered. | No action. |
| Lookup and Inference | 9 | FULL | None. | Lookup/inference behavior covered. | No action. |
| Manager, Imports, and Cache | 10 | FULL | None. | Manager/cache behavior covered. | No action. |
| Transforms and Extenders | 5 | FULL | None. | Transform/extender behavior covered. | No action. |
| Deprecated Top-Level Node Aliases | 3 | FULL | None. | Alias warning behavior covered. | No action. |
| Error Semantics | 3 | FULL | None. | Public exception categories covered. | No action. |
| Cross-View Invariants | 7 | FULL | None. | Core invariant section covered. | No action. |
| Representative Workflow | 3 | FULL | None. | End-to-end workflow covered. | No action. |
| Non-Goals | 0 | FULL | None; negative/meta constraints. | None. | No action. |
| Evaluation Notes | 0 | FULL | None; evaluation guidance only. | None. | No action. |

No `coverage-gap` label is required.

## Verdict and Actions

Verdict: QUALIFIED.

Actions taken:

- Updated this diagnosis report for spec_v2/run 002 with the required `Preflight output` block.
- Appended model weakness rows for `atomic-behavior`, `error-semantics`, `cross-view-consistency`, and `api-surface`.
- Updated `MANIFEST.json` judge metadata to run 002, candidate score `73/79`, QUALIFIED verdict, labels, and notes.
- Updated `PIPELINE_STATE.md` from `S5_JUDGE` to `QUALIFIED`.

No files were copied into `tasks/`; final migration remains for the orchestrator.
