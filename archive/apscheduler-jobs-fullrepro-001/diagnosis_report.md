# APScheduler Jobs Fullrepro Diagnosis

Verdict: QUALIFIED

## Preflight output

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-apscheduler-specv1-20260704-001/output/apscheduler/__init__.py
```

The preflight import points inside the candidate solution directory. The score run was executed on WSL/Linux, and `score_result.json` records `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`.

## Anti-Cheat Scan

No forbidden source, test, score, or prior-attempt access was used during the clean candidate implementation. Scoring used `--remove-path src/apscheduler`, so the oracle worktree's source package was removed before candidate imports.

## Solvability

Reference score: 60/60.

Dummy gate: 0/60 passed; the dummy implementation timed out on all 60 tests and did not satisfy any scoring row.

Candidate score: 60/60.

Layer summary:

| layer | candidate | reference |
|---|---:|---:|
| atomic | 23/23 | 23/23 |
| integration | 23/23 | 23/23 |
| system_e2e | 14/14 | 14/14 |

## Gate A - Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| tests/test_generated_core.py::test_configure_task_merges_defaults_decorator_and_direct_metadata | task defaults, decorator defaults, and direct metadata merge by priority | ## Task Configuration | derivable |
| tests/test_generated_core.py::test_conflict_policy_exception_raises_conflicting_id_error | duplicate schedule ID with exception policy raises the public conflict error | ## Error Semantics | derivable |
| tests/test_generated_core.py::test_job_events_are_emitted_in_lifecycle_order | direct job publishes added, acquired, and released events with matching IDs | ## Cross-View Invariants | derivable |
| tests/test_generated_core.py::test_interval_trigger_returns_start_then_interval_steps_until_end | interval trigger returns start, interval steps, and then exhaustion | ## Triggers | derivable |
| tests/test_generated_core.py::test_direct_job_representative_workflow_events_and_result | direct job workflow stores, runs, emits events, and returns result | ## Representative Workflows | derivable |

## Gate C - Generated-Only Oracle Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| tests/test_generated_core.py::test_schedule_metadata_inherits_task_metadata_and_overrides_top_level | schedule metadata reflects task/default inheritance and explicit override | ## Cross-View Invariants | spec-driven behavioral |
| tests/test_generated_core.py::test_paused_due_schedule_does_not_create_job_until_unpaused | paused due schedule remains visible but does not run until unpaused | ## Cross-View Invariants | spec-driven behavioral |
| tests/test_generated_core.py::test_local_event_broker_filters_event_types | event broker delivers only requested event types | ## Events | spec-driven behavioral |
| tests/test_generated_core.py::test_memory_datastore_get_next_schedule_run_time_tracks_earliest | schedules are ordered by earliest next fire time | ## Memory Data Store | spec-driven behavioral |
| tests/test_generated_core.py::test_state_model_views_agree_for_task_schedule_and_job | task, schedule, job, and event views agree on the same facts | ## Product State Model | spec-driven behavioral |

No sampled generated test asserts on private attributes, exact repr strings, private module paths, or exact exception message wording.

## Gate D - Coverage Gap Audit

Coverage verdict: PARTIAL.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| ## Product Overview | narrative overview only | no behavioral scoring impact | acceptable |
| ## Scope | boundary description only | no behavioral scoring impact | acceptable |
| ## Installable Surface | public imports are exercised indirectly by every test module import | no zero-coverage API risk | acceptable |
| ## Non-Goals | exclusions only | no behavioral scoring impact | acceptable |
| ## Invocation Protocol | no CLI is in scope | no behavioral scoring impact | acceptable |
| ## Evaluation Notes | protocol text only | no behavioral scoring impact | acceptable |

All core behavior sections have coverage, including Product State Model, Task Configuration, Schedule Lifecycle, Job Lifecycle, Scheduler Lifecycle, Memory Data Store, Events, Triggers, Job Executors And Context Variables, Error Semantics, Cross-View Invariants, and Representative Workflows. Cross-View Invariants has 5 mapped rows; Error Semantics has 9 mapped rows.

## Failure Analysis

There are no candidate failures in the accepted run. Because the candidate scored 100% with a compact implementation, this task is labeled `trivially-solved` and `saturated-candidate-score`. The pattern is consistent with the scoped oracle being solvable from the public packet by the current candidate model, so it is valid but low-discrimination for this model.

## Labels

`generated-only-oracle`, `core-scheduler-lifecycle`, `trivially-solved`, `saturated-candidate-score`, `low-discrimination-current-candidate`

