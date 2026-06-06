# MiniURLUtils Unit/System Task Readiness

Date: 2026-06-03

This directory contains the public candidate packet for the MiniURLUtils unit/system gap task.

## Claim Fit

The task tests whether models can implement local URL parsing and editing features while preserving system-level consistency across parsed components, mutable URL object state, ordered query parameters, normalization, navigation, link extraction, serialization, and error recovery.

## PRD Compliance

| Requirement | Status | Evidence |
| --- | --- | --- |
| 6-12 feature modules | Pass | The packet defines 6 modules: parsing, URL object state, query parameters, navigation/normalization, link extraction, and errors. |
| Cross-module data/state dependencies | Pass | Parsed components feed URL objects; query params mutate URL serialization; normalization affects later navigation; extracted links become mutable URL objects. |
| Global invariants | Pass | The packet defines missing-component consistency, authority/userinfo separation, query order, normalize/navigate state, link-derived URL behavior, and error recovery. |
| API behavior explicit | Pass | Public functions, attributes, methods, query-param behavior, serialization, and error behavior are documented. |
| Implementation not prescribed | Pass | The packet specifies observable Python API behavior without requiring parser architecture or private layout. |
| Moderate difficulty target | Pass | Current Codex and OpenHands-compatible runs have 100.00% unit and substantially lower system scores. |

## Unit Coverage

The hidden v1 rubric has 9 unit cases, all self-contained.

| Feature module | Unit cases | Count |
| --- | --- | ---: |
| imports/package shape | `MUU001` | 1 |
| parsing | `MUU002` | 1 |
| URL object | `MUU003` | 1 |
| query parameters | `MUU004`, `MUU005` | 2 |
| navigation | `MUU006` | 1 |
| normalization | `MUU007` | 1 |
| link extraction | `MUU008` | 1 |
| errors | `MUU009` | 1 |

## System Coverage

The hidden v1 rubric has 10 system cases. Every case crosses at least two feature modules and has a `system_dimension` label.

| Dimension | Cases | Count |
| --- | --- | ---: |
| `cross_feature_dataflow` | `MUS004`, `MUS006` | 2 |
| `state_accumulation` | `MUS005` | 1 |
| `global_invariant` | `MUS001`, `MUS009` | 2 |
| `error_atomicity` | `MUS008` | 1 |
| `operation_order_sensitivity` | `MUS003`, `MUS010` | 2 |
| `boundary_crossing` | `MUS002`, `MUS007` | 2 |

## Traceability Artifacts

- Public packet: `public_packet.md`
- Hidden rubric: `../scoring/rubrics_unit_system_v1.json`
- Deterministic scorer: `../scoring/score_miniurlutils_unit_system.py`
- Spec-test alignment: `../scoring/requirement_map_unit_system_v1.md`

## Verification

| Solution | Unit | System | Gap | Report |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | `../score_report_reference_unit_system_v1.json` |
| Codex subagent | 100.00% | 70.00% | 30.00pp | `../score_report_codex_subagent_001_unit_system_v1.json` |
| OpenHands + DeepSeek V4 Pro | 100.00% | 60.00% | 40.00pp | `../score_report_openhands_deepseek_v4_pro_001_unit_system_v1.json` |

MiniURLUtils v1 is therefore a valid new repository task under the revised unit/system benchmark standard. It should replace Cookiecutter as the added core evidence if the benchmark needs a third task beyond SQLite and ZK.
