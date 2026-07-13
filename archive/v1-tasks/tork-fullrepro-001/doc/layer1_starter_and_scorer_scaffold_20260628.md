# TorkWorkflow Layer1 Starter And Scorer Scaffold

Date: 2026-06-28

## What Changed

Created a candidate-visible starter skeleton under:

`task/tork-fullrepro-001/candidate_task/starter`

The starter has 15+ source modules and public signatures only. It does not
contain a reference implementation.

Public module boundaries:

- `models`
- `clock`
- `parser`
- `datastore`
- `broker`
- `planner`
- `runtime`
- `retry`
- `logs`
- `progress`
- `scheduler`
- `worker`
- `recovery`
- `api`
- `cli`

Created a hidden scorer scaffold:

`task/tork-fullrepro-001/scoring/run_executable_checks.py`

The scorer scaffold records 60 intended checks:

- 20 unit checks;
- 20 integration checks;
- 20 system checks.

It is executable for `--list-checks` and for scoring a solution directory.
Candidate runs remain forbidden until a reference implementation reaches 100%
and a fairness judge approves the suite.

Update: the scorer now has executable check bodies and was run against the
candidate-visible starter skeleton.

Starter baseline result:

- score report:
  `task/tork-fullrepro-001/doc/score_report_starter_baseline_executable_v1.json`
- checks passed: 1/60
- overall weighted score: 0.91%
- unit score: 5%
- integration score: 0%
- system score: 0%

This is a baseline/scorer sanity test, not a candidate model run.

Provisional reference snapshot result:

- score report:
  `runs/tork-fullrepro-001/score_report_reference_executable_v1_provisional.json`
- checks passed: 45/60
- overall weighted score: 73.18%
- unit score: 80%
- integration score: 75%
- system score: 70%

This is a reference-gate debugging run, not a candidate model run. The gate is
still closed until reference reaches 100% and the suite passes fairness judge.

Reference repair result:

- score report:
  `runs/tork-fullrepro-001/score_report_reference_executable_v3_system_invariants.json`
- checks passed: 60/60
- overall weighted score: 100%
- unit score: 100%
- integration score: 100%
- system score: 100%

This scorer revision strengthens the system layer so every system row compares
multiple public projections against one shared workflow history. It opens the
reference gate. Candidate model runs remain forbidden until an independent
fairness judge approves the revised suite.

Created a cleanroom smoke workspace:

`runs/cleanroom/tork-cleanroom-smoke-20260628-v5`

Leakage scan result:

- files scanned: 22
- direct hidden surface: 0
- observed hidden surface: 0
- starter `__pycache__` directories: 0

## Current Gate

Candidate model runs remain forbidden.

Missing before model runs:

- independent fairness judge.

Completed before model runs:

- executable scorer with 60 checks;
- candidate-visible starter baseline sanity score:
  `task/tork-fullrepro-001/doc/score_report_starter_baseline_executable_v3_system_invariants.json`;
- reference implementation score 100%;
- cleanroom workspace creation;
- leakage scan with no direct or observed hidden surface.

## Why This Is Aligned

The starter locks a multi-module public interface derived from Tork's public
surface without copying source internals. It creates room for feature-pure unit
tests and system tests that compare public projections across API, datastore,
broker, scheduler, worker, logs, progress, and recovery.
