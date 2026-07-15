# Candidate Score Report - astroid

run_id: codex-astroid-specv2-20260708-002
spec_version: v2
candidate_output: output/

## Score

- passed: 73
- failed: 6
- skipped: 0
- total: 79
- pass_rate: 92.41%

## Isolation

Import preflight:

```text
/Users/zijian/bench/Bmk-dev/candidate-runs/codex-astroid-specv2-20260708-002/output/astroid/__init__.py
```

Score command used `score_pytest_original.py` with `--remove-path astroid`, `solution_dir=output`, and repaired spec_v2 oracle source `wip/astroid/filter/oracle_source_with_generated`.

## Layer Breakdown

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 47 | 4 | 51 |
| integration | 18 | 0 | 18 |
| system_e2e | 8 | 2 | 10 |

## Failed Nodeids

- `filter/generated_tests.py::test_statement_returns_nearest_statement_node`
- `filter/generated_tests.py::test_infer_unknown_dynamic_call_yields_uninferable_or_result_boundary`
- `filter/generated_tests.py::test_uninferable_is_identity_comparable_sentinel`
- `filter/generated_tests.py::test_public_exception_aliases_match_resolution_categories`
- `filter/generated_tests.py::test_cross_view_extract_node_parent_chain_and_rendering_are_consistent`
- `filter/generated_tests.py::test_cross_view_class_instance_and_attribute_lookup_share_tree_state`
