# Local Artifact Evidence Report

## Identity

- Task: `jupytext-fullrepro-001`
- Repository: `jupytext/jupytext`
- Fixed source commit: `a84c8826228dd99fc4478741736746e7e577a610`
- Status: `ARTIFACT_ONLY`

## Test Inventory

- Atomic: 35
- Integration: 34
- System E2E: 0
- Total: 69

## Current Bound Evidence

| Replay | Interpreter | Result | Pytest warnings | Logger warnings | JSON log | SHA-256 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Python 3.10 reference | `Python 3.10.8 local replay` | 69/69 | 0 | 0 | `logs/reference_py310_after_patch.json` | `caf12cfafa0c6b8149a0bde2a7ff5cee809e3ffed2c496e503adac69c228d66a` |
| Python 3.11 reference | `Python 3.11.15 local replay` | 69/69 | 0 | 0 | `logs/reference_py311_flatdeps_v3.json` | `5cab5211c884776c738c95bffec3e8daa5906fafa460d2cb9839b096648c0d57` |
| Python 3.10 dummy | `Python 3.10.8 empty dummy replay` | 3/69 | 0 | 0 | `logs/dummy_py310_current.json` | `099b877527205bfdf8eed9dc640e21e7fb3db16235953a3edb04392fc5b92a73` |

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
