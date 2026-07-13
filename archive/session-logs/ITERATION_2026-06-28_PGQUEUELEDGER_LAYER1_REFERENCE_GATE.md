# PgQueueLedger Layer1 Reference Gate

Date: 2026-06-28

## What Changed

PgQueueLedger advanced from Layer0 network scout to a Layer1 reference-gated
task candidate.

Artifacts:

- source evidence: `task/pgqueuer-fullrepro-001/doc/source_repo.md`
- requirement map seed: `task/pgqueuer-fullrepro-001/doc/requirement_map.md`
- public packet: `task/pgqueuer-fullrepro-001/candidate_task/public_packet.md`
- starter skeleton: `task/pgqueuer-fullrepro-001/candidate_task/starter`
- hidden rubric: `task/pgqueuer-fullrepro-001/rubric.json`
- executable scorer: `task/pgqueuer-fullrepro-001/scoring/run_executable_checks.py`
- harness note: `task/pgqueuer-fullrepro-001/doc/harness.md`
- reference: `runs/pgqueuer-fullrepro-001/solution-reference`
- reference score: `runs/pgqueuer-fullrepro-001/score_report_reference_v1.json`
- starter baseline: `runs/pgqueuer-fullrepro-001/score_report_starter_baseline_v1.json`
- task skill: `skills/pgqueuer-task-builder/SKILL.md`

## Source-Repo Principle

The reference implementation is only a calibration implementation for the
public packet and hidden scorer. It is not evidence of task scale.

Task scale remains anchored to upstream PgQueuer:

- source repo: `janbjorge/pgqueuer`
- pinned commit: `b475e4b9afbed1834cd7c478f1eec9d59ec0c5cd`
- upstream tracked files: 190
- upstream nonblank LOC: 21154

## Executable Suite

Total checks: 53

- unit: 32
- integration: 12
- system: 9

Reference result:

- passed: 53/53
- score: 100%

Starter baseline:

- passed: 4/53
- score: 7.55%
- interpretation: scorer is not empty; the starter only passes import/model
  shape checks.

## Agreement Surface

The suite currently tests these surfaces:

- claim ordering and eligibility;
- transaction rollback visibility;
- retry delay and terminal failure materialization;
- schedule due-work creation;
- completion watcher terminal boundaries;
- metrics/dashboard aggregation;
- stale heartbeat recovery;
- file-backed replay.

System checks assert cross-projection consistency for success, retry,
retry-then-success, cancel, schedule, recovery, rollback, commit, and reopen
workflows.

## Gates Passed

- source candidate gate exists and passes objective scale/doc/test/example
  signals;
- public packet and starter skeleton exist;
- cleanroom smoke exists and leakage scan is clean;
- hidden executable scorer exists;
- reference implementation passes the scorer at 100%;
- task-specific skill exists and validates.

## Gates Not Passed

Candidate model runs remain blocked until a fairness judge audits:

- whether 53 checks are sufficiently source-derived from PgQueuer docs/tests;
- whether the public packet fully specifies the hidden oracle choices;
- whether unit checks are feature-pure and not private-shape assertions;
- whether system checks measure real cross-feature consistency rather than
  final-result recomputation;
- whether the current surface is broad enough to avoid another mini-task.

## Next Action

Run a judge subagent over `pgqueuer-fullrepro-001` before any OpenHands,
mini-swe-agent, DeepSeek, Qwen, or Codex candidate run.
