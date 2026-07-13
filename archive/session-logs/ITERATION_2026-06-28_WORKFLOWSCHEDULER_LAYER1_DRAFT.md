# WorkflowScheduler Layer-1 Draft

Date: 2026-06-28

## Scope

This iteration advances `workflowscheduler-fullrepro-001` after Layer-0 judge
changed the verdict from `BUILD` to `BUILD_WITH_RESCOPE`. The task is now a
benchmark-owned local workflow scheduler named FlowLedger, sourced from Dagu
evidence but not a Dagu clone.

## Created Artifacts

- `task/workflowscheduler-fullrepro-001/prd.md`
- `task/workflowscheduler-fullrepro-001/doc/source_repo.md`
- `task/workflowscheduler-fullrepro-001/doc/requirement_map.md`
- `task/workflowscheduler-fullrepro-001/doc/harness.md`
- `task/workflowscheduler-fullrepro-001/candidate_task/public_packet.md`
- `task/workflowscheduler-fullrepro-001/candidate_task/starter/`
- `task/workflowscheduler-fullrepro-001/rubric.json`

## Starter Skeleton

The candidate-visible starter has 13 Python modules:

- `__init__.py`
- `api.py`
- `cli.py`
- `export.py`
- `history.py`
- `logs.py`
- `models.py`
- `queue.py`
- `recovery.py`
- `retry.py`
- `runner.py`
- `scheduler.py`
- `spec.py`

The skeleton locks interfaces only. It is not a reference implementation.

## Rubric Draft

`rubric.json` contains 50 check intents:

- unit: 20
- integration: 15
- system: 15

Status: `draft_contract_ready_requires_executable_test_code`.

These rows must be converted into executable hidden checks before any candidate
model run. They are not sufficient scoring evidence by themselves.

## Cleanroom Smoke

Cleanroom workspace:

- `runs/cleanroom/workflowscheduler-cleanroom-smoke-20260628-v1`

Tool change:

- `tools/create_cleanroom_packet.py` no longer copies `doc/source_repo.md` by
  default. This fixes a leakage risk for source-repo-derived full-reproduction
  tasks.

Leakage scan:

- report: `runs/cleanroom/workflowscheduler-cleanroom-smoke-20260628-v1/leakage_scan.json`
- files scanned: 18
- direct hidden-surface hits: 0
- observed hidden-surface hits: 0
- `public_packet/source_repo.md`: absent

## Current Gate Status

Passes:

- Layer-0 source scale and architecture audit;
- independent Layer-0 judge with `BUILD_WITH_RESCOPE`;
- public packet exists;
- source notes and requirement map exist;
- starter skeleton exists;
- 50-row rubric intent draft exists;
- cleanroom leakage smoke is clean.

Still missing:

- executable hidden tests;
- reference implementation;
- reference unit/integration/system = 100%;
- candidate model runs;
- gap analysis and fairness judge.

Do not run Codex, DeepSeek, Qwen, OpenHands, or mini-SWE-agent candidates yet.
