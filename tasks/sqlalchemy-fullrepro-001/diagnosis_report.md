# Diagnosis Report - sqlalchemy-fullrepro-001

Status: QUALIFIED
Date: 2026-07-03
Candidate run: `candidate-runs/codex-sqlalchemy-specv1-20260701-001`
Score file: `candidate-runs/codex-sqlalchemy-specv1-20260701-001/score_result_wsl_filter50.json`
Spec: `spec_v1`
Filter: `generated_only_filter50`

## Preflight output

```text
python -c "import sqlalchemy; print(sqlalchemy.__file__)"
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-sqlalchemy-specv1-20260701-001\output\sqlalchemy\__init__.py
```

## Hard Checks

Anti-cheat: PASS. The import provenance preflight points into the candidate solution directory, not the oracle worktree, reference package, or installed SQLAlchemy package. The WSL score was produced with `remove_paths: ["sqlalchemy"]`, `solution_dir` set to `/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-sqlalchemy-specv1-20260701-001/output`, and `nodeids` set to the 50-test oracle under `wip/sqlalchemy-fullrepro-001/filter/kept_nodeids.txt`. The candidate-visible prompt is the public spec body and the candidate output contains only the reconstructed `sqlalchemy` package files.

Platform: PASS. `score_result_wsl_filter50.json` reports `platform: Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`; the platform field does not contain Windows.

Solvability: PASS. `wip/sqlalchemy-fullrepro-001/filter/reference_score_retro_gate_d.json` reports reference passed 50/50 with `pass_rate_excluding_skips: 1.0`; this is >=95% and establishes that the scoring set is solvable by the reference implementation. WSL reference evidence is also present under `wip/sqlalchemy-fullrepro-001/filter/reference_wsl_filter50/` and the candidate run's `score-work-wsl-filter50/oracle_worktree/`.

Oracle source: generated-only. The `spec_test_map.md` header states `filter/oracle_source: generated_only`, so Gate C is required.

## Score

Candidate score: 25/50 passed, 25/50 failed, pass rate 0.50.

By layer:
- atomic: 9/15 passed, 6/15 failed
- integration: 13/29 passed, 16/29 failed
- system_e2e: 3/6 passed, 3/6 failed

No collection errors, not-collected tests, or unknown taxonomy entries were present in the WSL score.

## Gate A - Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `test_result_rows_support_positions_attributes_and_mappings` | Rows expose positional, attribute, and mapping access; labeled mappings expose label keys. | `### Engine and Execution` | derivable |
| `test_reflection_inspector_reports_columns_pk_fk_indexes_unique` | Inspector reports columns, primary keys, foreign keys, indexes, and unique constraints. | `### Reflection and Inspection` | derivable |
| `test_select_where_bindparams_order_by_limit_offset` | Select statements support filters, bind parameters, ordering, limit, and offset. | `### SQL Expressions and Compilation` | derivable |
| `test_relationship_back_populates_and_cascade_persist_children` | Relationship back-populates synchronizes both sides and default save-update cascade persists related children. | `### Relationships and Loading` | derivable |
| `test_core_insert_then_orm_query_over_same_table` | Core-inserted rows are visible through ORM mappings over the same table. | `## Cross-View Invariants` | derivable |
| `test_result_cardinality_errors_for_scalar_one` | Scalar one-style consumption raises `NoResultFound` or `MultipleResultsFound` for invalid cardinality. | `## Error Semantics` | derivable |

Gate A verdict: PASS. Sampled covered rows quote real spec headings and the expected observable behavior is derivable from the quoted section.

## Gate B - Failure Pattern Audit

Sampled WSL failures are public behavioral gaps, not verifier artifacts:

| failing area | evidence | verdict |
|---|---|---|
| SQL expression projection | selected/labeled columns fail with SQLite `no such column` errors in result row and aggregate tests | model failure |
| Reflection | inspector does not report public index/constraint metadata expected by the spec | model failure |
| ORM unit of work | autoflush, expiration, delete/flush sequencing, and session-bound entity selection fail through public Session APIs | model failure |
| Relationship loading | `selectinload`, `joinedload`, `raiseload`, `contains_eager`, and many-to-one lazy loading diverge through public loader APIs | model failure |
| Public API surface and type behavior | `make_url`, `Numeric(precision, scale)`, JSON path expressions, and connection transaction begin are incomplete | model failure |

Gate B verdict: PASS. The failures are traceable to documented public behavior and do not rely on private imports, exact repr strings, exact exception message text, or internal field names.

## Gate C - Generated-Only Oracle Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `test_connect_block_rolls_back_uncommitted_work` | Uncommitted work in a `connect()` block is rolled back when the block exits without commit. | `### Engine and Execution` | spec-driven behavioral |
| `test_sqlite_insert_on_conflict_do_nothing_and_do_update` | SQLite dialect insert supports conflict do-nothing and conflict update behavior. | `### SQLite Dialect Behavior` | spec-driven behavioral |
| `test_session_flush_autoflush_no_autoflush_and_rollback` | Session autoflush/no_autoflush/rollback behavior affects database visibility as documented. | `### Session and Unit of Work` | spec-driven behavioral |
| `test_joinedload_collection_requires_unique_for_duplicate_primary_rows` | Joined eager loading of collections requires unique consumption to collapse duplicate primary rows. | `### Relationships and Loading` | spec-driven behavioral |
| `test_table_column_key_label_and_row_mapping_views_agree` | Column key/name, labels, row mapping, and reflection remain cross-view consistent. | `## Cross-View Invariants` | spec-driven behavioral |
| `test_sqlite_json_path_expression_reads_nested_value` | SQLite JSON path expressions read nested JSON values through public expression APIs. | `### SQLite Dialect Behavior` | spec-driven behavioral |

Gate C verdict: PASS. The sampled generated tests are derived from the spec and reference-observed public behavior. They do not check private shapes, exact reprs, or exact error-message text.

## Gate D - Coverage Gap Audit

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| Product Overview | Narrative overview only; no independent behavioral assertions. | None. | No action; non-behavioral section. |
| Scope | Boundary narrative only; behavioral subsections are covered below. | None. | No action; boundary section. |
| Installable Surface | Covered by one import-surface test plus many tests importing the named APIs. | Acceptable partial coverage. | Keep as caveat only. |
| Public API | Covered through its H3 subsections. | None. | Use subsection coverage as the behavioral signal. |
| Metadata, Tables, Columns, and Types | Common type/metadata behavior has two direct tests plus cross-view metadata tests. | Acceptable partial coverage. | No blocking gap. |
| DML | Insert/update/delete and executemany behavior have two direct tests plus workflow coverage. | Acceptable partial coverage. | No blocking gap. |
| ORM Declarative Mapping | Declarative table/default-init behavior has two direct tests plus ORM workflows. | Acceptable partial coverage. | No blocking gap. |
| Representative Workflows | Covered by the full Core/ORM/reflection workflow and Core/ORM over SQLite tests. | Acceptable partial coverage. | No blocking gap. |
| Non-Goals | Boundary exclusions only. | None. | No action; not a scoreable behavior target. |
| Evaluation Notes | Benchmark-process guidance only. | None. | No action; not candidate-facing behavior. |

Coverage verdict: PARTIAL. Core invariant and error sections have nonzero coverage above their required minimums: `## Cross-View Invariants` has 5 covered tests and `## Error Semantics` has 6 covered tests. The remaining zero rows are narrative or boundary sections, not unresolved behavioral gaps.

## Real Failure Clusters

1. SQL expression and result projection behavior (`atomic-behavior`): selected/labeled columns, aggregates, casts, row mappings, and column key/name projections are incomplete, producing missing-column errors or wrong mapping values.

2. Reflection and metadata/type surface (`api-surface`): index/constraint reflection, metadata column collections, `make_url`, and `Numeric(precision, scale)` support are missing or incomplete.

3. ORM unit-of-work and state lifecycle (`state-management`): autoflush, expiration, delete/flush sequencing, committed identity state, and detached/expired attribute handling diverge from public Session semantics.

4. Relationship loader semantics (`cross-view-consistency`): eager/lazy/raise/contains-eager strategies do not preserve the specified object identity, collection population, and access-error behavior.

5. Error semantics and transaction behavior (`error-semantics`): unresolved foreign key errors, raiseload errors, JSON path expression behavior, and explicit connection transaction begin are incomplete through public APIs.

## Cascade Analysis

The 25 WSL failures reduce to about five root capability gaps. Several integration/system failures cascade from ORM lifecycle and relationship loader limitations, while SQL-expression projection and reflection/API-surface failures remain independent. The task remains discriminating because the candidate passes 25 behavioral tests while failing multiple distinct public capability clusters.

## Verdict

QUALIFIED. This legal Stage 5 WSL rejudge uses the 50-test oracle after the retroactive Gate D expansion. The preflight points to the candidate solution, the platform is Linux/WSL, reference solvability is 50/50, generated-only Gates A/B/C pass, Gate D is acceptable PARTIAL with no unresolved core-invariant or error-semantics gap, and the candidate score is a valid 25/50 public-behavior signal.
