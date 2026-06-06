# MiniSQLiteUtils Unit/System Requirement Map

Date: 2026-06-03

Public packet: `candidate_task_unit_system/public_packet.md`

Rubric: `scoring/rubrics_unit_system_v1.json`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-feature-set` | Bounded 7-module feature set | Feature Set | Product has insert, upsert, query/metadata, extract, FTS, transform, error/atomicity |
| `REQ-global-invariants` | Cross-feature system invariants | Global Invariants | PK identity, row count, derived structures, unrelated tables, and failed-command safety remain consistent |
| `REQ-import` | JSON/CSV insert and type inference | Data Import | Creates/extends tables, infers SQLite-compatible types, handles PKs, fails on unknown columns without alter |
| `REQ-upsert` | PK update lifecycle | Upsert | Updates matching rows, preserves omitted values, inserts new rows, supports compound PKs and alter |
| `REQ-query` | Rows/query/tables/schema | Querying And Metadata | Returns JSON rows and metadata reflecting current DB state |
| `REQ-extract` | Lookup normalization | Extract | Builds first-seen lookup table and replaces source column with foreign-key ids |
| `REQ-fts` | FTS build/search lifecycle | Full Text Search | Builds/rebuilds `TABLE_fts`; search returns original rows |
| `REQ-transform` | Schema rewrite | Transform | Rename/drop/not-null/default while preserving rows and PKs; default may create new columns |
| `REQ-atomic` | Error and atomicity | Error Behavior | Invalid commands fail nonzero and preserve existing state |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | Unit tests exercise one feature module with direct setup when needed |
| `REQ-system-eval` | System testing definition | Evaluation Style | System tests cross at least two feature modules and carry `system_dimension` labels |

## Unit Coverage

| Test | Feature | Requirement refs | Public basis |
| --- | --- | --- | --- |
| `SQU001` | insert | `REQ-import` | JSON import, PK, type inference, compact JSON storage for lists |
| `SQU002` | insert | `REQ-import` | CSV import, integer/real/boolean/text type inference |
| `SQU003` | upsert | `REQ-upsert` | Upsert preserves omitted values and inserts new rows |
| `SQU004` | upsert | `REQ-upsert` | Compound PK upsert with alter and omitted-value preservation |
| `SQU005` | query | `REQ-query` | `rows` supports where/order/limit JSON output |
| `SQU006` | query | `REQ-query` | `query SQL` returns JSON row objects |
| `SQU007` | metadata | `REQ-query` | `tables --counts` and `schema TABLE` reflect DB metadata |
| `SQU008` | extract | `REQ-extract` | Repeated values normalize into lookup table |
| `SQU009` | extract | `REQ-extract` | Nulls ignored; first-seen lookup order |
| `SQU010` | FTS | `REQ-fts` | `enable-fts` builds `TABLE_fts` |
| `SQU011` | FTS | `REQ-fts` | `search` returns original rows from existing index |
| `SQU012` | transform | `REQ-transform` | Rename/drop/default; default may create new columns |
| `SQU013` | transform/error | `REQ-transform`, `REQ-atomic` | Invalid not-null transform leaves rows/schema unchanged |
| `SQU014` | import/error | `REQ-import`, `REQ-atomic` | Unknown column without alter fails and preserves rows |
| `SQU015` | import/error | `REQ-import`, `REQ-atomic` | Invalid JSON import fails nonzero |
| `SQU016` | query | `REQ-query` | Empty match returns empty JSON list |

Unit requirement coverage:

- `REQ-import`: covered by `SQU001`, `SQU002`, `SQU014`, `SQU015`
- `REQ-upsert`: covered by `SQU003`, `SQU004`
- `REQ-query`: covered by `SQU005`, `SQU006`, `SQU007`, `SQU016`
- `REQ-extract`: covered by `SQU008`, `SQU009`
- `REQ-fts`: covered by `SQU010`, `SQU011`
- `REQ-transform`: covered by `SQU012`, `SQU013`
- `REQ-atomic`: covered by `SQU013`, `SQU014`, `SQU015`

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `SQS001` | `cross_feature_dataflow` | insert -> upsert -> rows/query | `REQ-import`, `REQ-upsert`, `REQ-query`, `REQ-global-invariants` | CSV-inferred values flow into upsert and JSON query output |
| `SQS002` | `state_accumulation` | insert -> extract -> transform -> query | `REQ-import`, `REQ-extract`, `REQ-transform`, `REQ-query`, `REQ-global-invariants` | Lookup ids and transformed rows remain queryable |
| `SQS003` | `state_accumulation` | insert -> enable-fts -> upsert -> rebuild FTS -> search | `REQ-import`, `REQ-upsert`, `REQ-fts`, `REQ-query` | Explicit FTS rebuild reflects updated source rows |
| `SQS004` | `global_invariant` | insert -> transform -> tables/schema/rows | `REQ-import`, `REQ-transform`, `REQ-query`, `REQ-global-invariants` | PK, row count, schema, and rows remain mutually consistent |
| `SQS005` | `error_atomicity` | insert -> extract -> invalid transform | `REQ-import`, `REQ-extract`, `REQ-transform`, `REQ-atomic`, `REQ-global-invariants` | Failed transform preserves original and lookup tables |
| `SQS006` | `error_atomicity` | insert -> invalid upsert -> rows/schema | `REQ-import`, `REQ-upsert`, `REQ-query`, `REQ-atomic` | Unknown upsert column without alter fails without schema corruption |
| `SQS007` | `boundary_crossing` | compound insert -> upsert alter -> transform default | `REQ-import`, `REQ-upsert`, `REQ-transform` | Compound PK, alter, omitted values, and default-created columns compose |
| `SQS008` | `cross_feature_dataflow` | insert -> extract -> enable-fts -> search | `REQ-import`, `REQ-extract`, `REQ-fts`, `REQ-query` | Extract output becomes FTS input and remains linked to source rows |
| `SQS009` | `global_invariant` | insert two tables -> transform one -> tables/query | `REQ-import`, `REQ-transform`, `REQ-query`, `REQ-global-invariants` | Transforming one table does not alter unrelated table state |
| `SQS010` | `boundary_crossing` | CSV insert -> upsert -> transform -> rows | `REQ-import`, `REQ-upsert`, `REQ-transform`, `REQ-query` | CSV type inference, omitted upsert values, rename, and JSON defaults compose |
| `SQS011` | `operation_order_sensitivity` | insert -> transform rename/default -> extract -> query | `REQ-import`, `REQ-transform`, `REQ-extract`, `REQ-query` | A rename changes the column that a later extract must normalize |
| `SQS012` | `operation_order_sensitivity` | insert -> extract -> transform generated id column -> query | `REQ-import`, `REQ-extract`, `REQ-transform`, `REQ-query` | Extract-created lookup id columns remain transformable and queryable |

System dimension coverage:

- `cross_feature_dataflow`: `SQS001`, `SQS008`
- `state_accumulation`: `SQS002`, `SQS003`
- `global_invariant`: `SQS004`, `SQS009`
- `error_atomicity`: `SQS005`, `SQS006`
- `boundary_crossing`: `SQS007`, `SQS010`
- `operation_order_sensitivity`: `SQS011`, `SQS012`

The v1 SQLite system set now covers all 6 requested system dimensions. The operation-order cases use public transform/extract semantics and avoid penalizing stronger FTS trigger implementations.

## Reference And Model Verification

| Solution | Unit | System | Gap | Report |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | `score_report_reference_unit_system_v1.json` |
| Codex subagent | 87.50% | 41.67% | 45.83pp | `score_report_codex_subagent_001_unit_system_v1.json` |
| OpenHands + DeepSeek V4 Pro | 93.75% | 41.67% | 52.08pp | `score_report_openhands_deepseek_v4_pro_001_unit_system_v1.json` |

## Fairness Notes

- CSV empty-field behavior was removed from v1 hidden checks after audit because it was a public-signal gray area.
- Transform defaults creating new columns are now explicit in `candidate_task_unit_system/public_packet.md`.
- SQLite v1 meets the new unit/system claim for this task, but OpenHands + DeepSeek unit score is slightly above the ideal 70-90% target band. This is acceptable for v1 evidence but should be monitored when more models are added.
