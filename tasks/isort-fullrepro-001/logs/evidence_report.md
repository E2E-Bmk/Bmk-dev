# Local Artifact Evidence Report

## Identity

- Task: `isort-fullrepro-001`
- Repository: `https://github.com/PyCQA/isort`
- Fixed source commit: `fd8bd075176d074af69aa6acae7ed89a6a89bb05`
- Status: `ARTIFACT_ONLY`

## Test Inventory

- Atomic: 32
- Integration: 34
- System E2E: 0
- Total: 66

## Current Bound Evidence

| Replay | Interpreter | Result | Pytest warnings | Logger warnings | JSON log | SHA-256 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Python 3.10 reference | `Python 3.10.8 local replay` | 66/66 | 0 | 0 | `logs/reference_py310_replay.json` | `196d80b1ba9c3e28cc1ac7f74e33a834cf579061b7ea39e46dbd764aad7e9fc8` |
| Python 3.11 reference | `Python 3.11.15 local replay` | 66/66 | 0 | 0 | `logs/reference_py311_replay.json` | `0c0ecb3bd8a3222e3a88446ba28691591ffed84ecb1c23abdd72ad2321cb758f` |
| Python 3.10 dummy | `Python 3.10.8 empty dummy replay` | 5/66 | 0 | 0 | `logs/dummy_py310_replay.json` | `e8be421754886b1b308dfca0e5cee7ae28f7614b4053bbacd1f63bdab8e77aa0` |

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
