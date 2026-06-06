# MiniSQLiteUtils Unit/System Task Readiness

Date: 2026-06-03

This directory contains the public candidate packet for the SQLite unit/system gap task.

## Claim Fit

The task is intended to test whether models can implement local features while preserving system-level database consistency across multi-command workflows. It supports the target benchmark claim:

`Unit score > System score`, with a stable gap between local feature behavior and composed system behavior.

## PRD Compliance

| Requirement | Status | Evidence |
| --- | --- | --- |
| 6-12 feature modules | Pass | The packet defines 7 modules: insert, upsert, query/metadata, extract, FTS, transform, and error/atomicity. |
| Cross-module data/state dependencies | Pass | Inserted rows flow into upsert, extract, FTS, transform, query, and metadata commands. |
| Global invariants | Pass | The packet explicitly defines PK/row preservation, derived-structure consistency, unrelated-table isolation, metadata consistency, and failed-command atomicity. |
| API/CLI behavior explicit | Pass | Each command documents arguments, JSON/stdout behavior, mutation behavior, and non-zero error behavior. |
| Implementation not prescribed | Pass | The packet specifies observable SQLite behavior but does not require private data structures or module layout. |
| Moderate difficulty target | Pass | Two model pre-runs show high unit scores with substantially lower system scores. |

## Unit Coverage

The hidden v1 rubric has 16 unit cases, all self-contained. When a case needs pre-existing database state, it uses direct SQL setup instead of invoking other product commands.

| Feature module | Unit cases | Count |
| --- | --- | ---: |
| insert | `SQU001`, `SQU002` | 2 |
| upsert | `SQU003`, `SQU004` | 2 |
| query/metadata | `SQU005`, `SQU006`, `SQU007`, `SQU016` | 4 |
| extract | `SQU008`, `SQU009` | 2 |
| FTS | `SQU010`, `SQU011` | 2 |
| transform | `SQU012`, `SQU013` | 2 |
| error/atomicity | `SQU014`, `SQU015` | 2 |

## System Coverage

The hidden v1 rubric has 12 system cases. Every case crosses at least two feature modules and has a `system_dimension` label.

| Dimension | Cases | Count |
| --- | --- | ---: |
| `cross_feature_dataflow` | `SQS001`, `SQS008` | 2 |
| `state_accumulation` | `SQS002`, `SQS003` | 2 |
| `global_invariant` | `SQS004`, `SQS009` | 2 |
| `error_atomicity` | `SQS005`, `SQS006` | 2 |
| `boundary_crossing` | `SQS007`, `SQS010` | 2 |
| `operation_order_sensitivity` | `SQS011`, `SQS012` | 2 |

The v1 system set now covers all six requested system dimensions.

## Traceability Artifacts

- Public packet: `public_packet.md`
- Hidden rubric: `../scoring/rubrics_unit_system_v1.json`
- Deterministic scorer: `../scoring/score_dbmini_unit_system.py`
- Spec-test alignment: `../scoring/requirement_map_unit_system_v1.md`

## Verification

| Solution | Unit | System | Gap | Report |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | `../score_report_reference_unit_system_v1.json` |
| Codex subagent | 87.50% | 41.67% | 45.83pp | `../score_report_codex_subagent_001_unit_system_v1.json` |
| OpenHands + DeepSeek V4 Pro | 93.75% | 41.67% | 52.08pp | `../score_report_openhands_deepseek_v4_pro_001_unit_system_v1.json` |

SQLite v1 is therefore a valid first task under the revised unit/system benchmark standard.
