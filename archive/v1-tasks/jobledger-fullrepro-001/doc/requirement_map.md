# JobLedger Requirement Map

## Source Evidence

- `oban-bg/oban/README.md`: reliability, consistency, observability, retained
  job data, isolated queues, scheduled jobs, periodic jobs, unique jobs,
  historic metrics, graceful shutdown, telemetry.
- `guides/learning/job_lifecycle.md`: public job states and transitions from
  inserted to terminal states.
- `guides/learning/error_handling.md`: failures record error details, retries
  occur until max attempts, final discard after exhaustion.
- `guides/learning/instrumentation.md`: lifecycle events can drive logging and
  metrics.

The benchmark variant uses custom Python APIs, custom CLI names, deterministic
virtual time, deterministic retry delay, and benchmark-owned persistence
semantics to avoid cloning Oban/Ecto/Postgres.

## Requirements

| Requirement | Public behavior | Evidence |
|---|---|---|
| REQ-artifact-shape | Candidate implements installable package with API, CLI, durable state, and reports. | Benchmark full-reproduction policy. |
| REQ-job-model | Jobs have stable ID, queue, kind, args, priority, state, attempts, schedule, uniqueness, and timestamps. | Oban retained job model and lifecycle docs; benchmark variant. |
| REQ-state-lifecycle | Jobs move through available, scheduled, executing, retryable, completed, cancelled, discarded. | Oban job lifecycle guide; benchmark variant excludes suspended. |
| REQ-claim-order | Claim order is deterministic by queue, state/due time, priority, time, ID. | Oban queue isolation/priority concepts; benchmark deterministic variant. |
| REQ-retry | Failure appends attempt, schedules retry until max attempts, then discards. | Oban error handling guide; deterministic benchmark backoff. |
| REQ-uniqueness | Configured uniqueness windows reject or replace duplicate work and appear in conflict reports. | Oban README unique jobs; benchmark variant. |
| REQ-cron | Cron schedules insert at most one job per slot and survive restart/replay. | Oban README periodic jobs; benchmark deterministic variant. |
| REQ-events | Lifecycle events are append-only and ordered. | Oban instrumentation guide; benchmark event stream. |
| REQ-metrics | Retained jobs and events produce queue/state/kind/success/failure/retry metrics. | Oban README historic metrics and telemetry. |
| REQ-prune | Pruning removes only old terminal job detail while retaining public metric/event summaries and prune report. | Oban lifecycle guide notes pruner removes final state jobs; benchmark variant. |
| REQ-api-cli-consistency | API and CLI expose the same public state and reports. | Benchmark full-reproduction policy. |
| REQ-persistence | Durable state survives new JobLedger instances and export/import. | Oban database-backed reliability; benchmark variant. |
| REQ-recovery | Interrupted operations are recoverable without projection drift. | Oban reliability/graceful shutdown inspiration; benchmark variant. |
| REQ-atomicity | Failed public operations do not partially mutate visible state. | Oban transactional control inspiration; benchmark variant. |
| REQ-errors | Invalid operations fail with public error semantics. | Oban error handling inspiration; benchmark variant. |
| REQ-determinism | Explicit virtual time controls scheduling, retries, cron, ordering, and tests. | Benchmark variant to avoid flaky wall-clock behavior. |

## Hidden Rubric Coverage

- Unit rows cover REQ-job-model, REQ-state-lifecycle primitives, REQ-retry,
  REQ-uniqueness, REQ-cron, REQ-events, REQ-metrics, REQ-errors, and
  REQ-atomicity.
- Integration rows cover REQ-api-cli-consistency, REQ-persistence, queue
  projection, event/metric projection, and import/export boundaries.
- System rows cover cross-feature lifecycle invariants for retry, cron,
  uniqueness, recovery, metrics, event stream, queue reports, prune, and replay.
