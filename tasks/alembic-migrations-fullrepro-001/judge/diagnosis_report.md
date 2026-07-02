# Stage 5 Diagnosis Report

Task: `alembic-migrations-fullrepro-001`

Candidate run: `codex-alembic-specv3-20260630-001`

Status: `QUALIFIED`

## Anti-Cheat Scan

Accepted import provenance was checked from the candidate output directory with `PYTHONPATH` pointing only at the candidate output.

### Preflight output

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-alembic-specv3-20260630-001\output\alembic\__init__.py
```

Deliverable scan result:

- No candidate-output hits for source repo paths, `spec_test_map`, `kept_nodeids`, `score_report`, `score_result`, or `rewritten_upstream_tests`.
- No `test_*.py` or `conftest.py` files were present in the candidate output tree.
- `run_metadata.md` records that the candidate agent received only public prompt/spec files and the output directory.

Anti-cheat result: pass.

## Solvability

Reference implementation result: 30 passed / 30 total, pass rate 100%.

Candidate result after filter correction: 29 passed / 30 total, pass rate 96.67%.

Candidate score by layer:

| layer | passed | failed | total |
|-------|--------|--------|-------|
| atomic | 14 | 0 | 14 |
| integration | 10 | 1 | 11 |
| system_e2e | 5 | 0 | 5 |

Solvability result: pass.

## Fairness

Gate A spot-check:

| test | mapped section | result |
|------|----------------|--------|
| `test_config_programmatic_options_and_attributes_round_trip` | Configuration | valid |
| `test_script_directory_heads_follow_revision_graph` | Script Directory And Revision Graph | valid after spec_v3 return-type patch |
| `test_operations_create_table_online` | Operations API | valid after filter correction to explicit `Operations(ctx)` |
| `test_autogenerate_detects_removed_table` | Autogenerate | valid after shape-tolerant filter correction |
| `test_offline_downgrade_range_writes_drop_sql` | Offline SQL | valid |

Gate B failure audit:

The only remaining failure is `test_offline_downgrade_range_writes_drop_sql`. It is traceable to `spec_v3.md` Offline SQL: range syntax such as `start:end` is meaningful for upgrade/downgrade SQL generation. The test checks observable SQL generation behavior, not private internals.

Fairness result: pass.

## Real Failure Cluster

| root cause | dimension | affected tests |
|------------|-----------|----------------|
| Candidate did not parse downgrade SQL range syntax such as `create_account:base`; it attempted to resolve the whole range string as one revision identifier and raised `ResolutionError`. | workflow-completeness | 1 integration |

## Cascade Analysis

Root failure clusters: 1.

Affected tests: 1.

No cascade: atomic and system_e2e layers reached full pass rates; the single integration failure is isolated to offline downgrade range handling.

## Task Labels

- `discriminating`
- `small-isolated-failure`
- `offline-sql-range-signal`
