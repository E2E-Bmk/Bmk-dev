# MiniZK Unit/System Task Readiness

Date: 2026-06-03

This directory contains the public candidate packet for the ZK unit/system gap task.

## Claim Fit

The task tests whether models can implement local notebook features while preserving system-level consistency across parsed note state, config, filters, tag counts, link resolution, graph export, and failure behavior.

## PRD Compliance

| Requirement | Status | Evidence |
| --- | --- | --- |
| 6-12 feature modules | Pass | The packet defines 8 modules: notebook, note creation, note parsing, tags, links/graph, list/filter/sort, config, and errors. |
| Cross-module data/state dependencies | Pass | Created files are parsed; parsed tags/links feed list, tag counts, and graph; config affects creation and named filters. |
| Global invariants | Pass | The packet explicitly defines notebook-root consistency, parsed metadata consistency, tag count consistency, graph consistency, and failure safety. |
| API/CLI behavior explicit | Pass | Each command documents flags, output formats, JSON shapes, path behavior, and error behavior. |
| Implementation not prescribed | Pass | The packet specifies observable Markdown notebook behavior without requiring a database or private layout. |
| Moderate difficulty target | Pass | Two model pre-runs have unit scores of 83.33% and lower system scores. |

## Unit Coverage

The hidden v1 rubric has 18 unit cases, all self-contained. Existing notes/config are created directly in setup instead of being produced through other product commands.

| Feature module | Unit cases | Count |
| --- | --- | ---: |
| notebook lifecycle/discovery | `ZKU001`, `ZKU002` | 2 |
| note creation | `ZKU003`, `ZKU004` | 2 |
| note parsing | `ZKU005`, `ZKU006` | 2 |
| tag semantics | `ZKU007`, `ZKU008` | 2 |
| link and graph semantics | `ZKU009`, `ZKU010`, `ZKU014` | 3 |
| list filtering/sorting | `ZKU011`, `ZKU012`, `ZKU013` | 3 |
| config | `ZKU017`, `ZKU018` | 2 |
| errors | `ZKU015`, `ZKU016` | 2 |

## System Coverage

The hidden v1 rubric has 12 system cases. Every case crosses at least two feature modules and has a `system_dimension` label.

| Dimension | Cases | Count |
| --- | --- | ---: |
| `cross_feature_dataflow` | `ZKS001`, `ZKS007` | 2 |
| `state_accumulation` | `ZKS004`, `ZKS009` | 2 |
| `global_invariant` | `ZKS003`, `ZKS008` | 2 |
| `error_atomicity` | `ZKS006` | 1 |
| `boundary_crossing` | `ZKS002`, `ZKS005`, `ZKS010` | 3 |
| `operation_order_sensitivity` | `ZKS011`, `ZKS012` | 2 |

## Traceability Artifacts

- Public packet: `public_packet.md`
- Hidden rubric: `../scoring/rubrics_unit_system_v1.json`
- Deterministic scorer: `../scoring/score_zmini.py`
- Spec-test alignment: `../scoring/requirement_map_unit_system_v1.md`

## Verification

| Solution | Unit | System | Gap | Report |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | `../score_report_reference_unit_system_v1.json` |
| Codex subagent | 83.33% | 58.33% | 25.00pp | `../score_report_codex_subagent_001_unit_system_v1.json` |
| OpenHands + DeepSeek V4 Pro | 83.33% | 41.67% | 41.67pp | `../score_report_openhands_deepseek_v4_pro_001_unit_system_v1.json` |

ZK v1 is therefore a valid second task under the revised unit/system benchmark standard.
