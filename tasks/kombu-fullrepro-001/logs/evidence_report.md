# Local Artifact Evidence Report

## Identity

- Task: `kombu-fullrepro-001`
- Repository: `celery/kombu`
- Fixed source commit: `bb4c7755641ca274efa45969e71a2b93bb53ca1a`
- Status: `ARTIFACT_ONLY`

## Test Inventory

- Atomic: 34
- Integration: 29
- System E2E: 0
- Total: 63

## Current Bound Evidence

| Replay | Interpreter | Result | Pytest warnings | Logger warnings | JSON log | SHA-256 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Python 3.10 reference | `Python 3.10.8 local replay` | 63/63 | 0 | 0 | `logs/reference_py310_clean.json` | `19708cd7f1b584a8fb1aeef0dd528ca891ecce4e238492500d0c6342dfcbd3fd` |
| Python 3.11 reference | `Python 3.11.15 local replay` | 63/63 | 0 | 0 | `logs/reference_py311.json` | `4d874816fdd927052fb0ceef0c3ce8196c2d15b55abfde475baca1474d8a21a4` |
| Python 3.10 dummy | `Python 3.10.8 empty dummy replay` | 0/63 | 0 | 0 | `logs/dummy_py310_clean.json` | `0bde53659130d2d8cf8258f78bb4a96851e7a2602c8810f7307c2cde1317037c` |

## Trust Boundary

These JSON reports are local, same-process reproducibility artifacts. They do not prove
a trusted runner, strict black-box isolation, network isolation, a trusted signature,
Docker replay, candidate qualification, or trusted score provenance.

- `stage4.mode`: `ARTIFACT_ONLY`
- `same_process_private_evaluator`: `true`
- `strict_black_box_proven`: `false`
- `network_isolation_proven`: `false`
- `trusted_signature_present`: `false`
- `qualification_claim`: `false`
- `candidate_score`: `None`
- `integration_gap.computed`: `false`

## Bookkeeping

Physical test functions, `kept_nodeids.txt`, `taxonomy.jsonl`, `spec_test_map.md`,
and the counts embedded in `task.json` are checked by `tools/audit_task_package.py`.
