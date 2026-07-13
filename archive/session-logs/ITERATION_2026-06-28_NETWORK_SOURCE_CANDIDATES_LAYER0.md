# Network Source Candidates Layer-0

Date: 2026-06-28

This pass applies the corrected source-repo pipeline: upstream repository first,
public packet later, no hand-written reference LOC as evidence. Each candidate
below has a generated `source_candidate_gate.md` with commit, scale, docs,
tests, and example signals.

## Objective Gate Results

| Candidate | Source repo | Commit | Files | Nonblank LOC | Verdict |
|---|---|---:|---:|---:|---|
| HatchetWorkflow | `hatchet-dev/hatchet` | `f34b10a` | 4196 | 616639 | `BUILD_WITH_RESCOPE` |
| PgQueueLedger | `janbjorge/pgqueuer` | `b475e4b` | 190 | 21154 | `BUILD` |
| AsynqQueue | `hibiken/asynq` | `d135f14` | 111 | 36466 | `BUILD_WITH_RESCOPE` |
| TorkWorkflow | `runabol/tork` | `7c126fc` | 217 | 30056 | `BUILD` |

All four pass the objective scale/doc/test/example gate. Passing this gate only
means Layer1 design may be considered; it does not authorize candidate model
runs.

## HatchetWorkflow

- Source: `https://github.com/hatchet-dev/hatchet`
- Product surface: durable workflow/task orchestration platform with workers,
  background tasks, durable sleeps/events, cron/scheduled runs, rate limits,
  worker routing, logs, metrics, and multi-tenant API/UI state.
- Shared fact source: workflow run records, task attempts, event-wait state,
  cron/scheduled run records, worker assignments, rate-limit/concurrency
  ledgers, logs, and observability records.
- Public projections: run status, task attempt history, worker/slot state,
  event wait list, schedule/cron next-run views, logs, metrics, API/UI run
  summaries.
- Local free choices: event-wait materialization, retry/backoff recording,
  rate-limit ledger granularity, worker affinity matching, cron catch-up,
  log ordering, recovery boundary.
- Global invariants: task/run status, attempt ledger, worker assignment,
  event-wait state, logs, metrics, and schedule views must agree after enqueue,
  retry, cancellation, worker loss, event delivery, cron tick, and restart.
- Contamination risk: high. Hatchet is a public durable-workflow platform and
  overlaps Temporal/DBOS/Celery/BullMQ patterns. A benchmark-owned local API
  and reduced deterministic runtime are mandatory.
- Feature-pure risks: SDK/decorator mechanics, rate-limit policy parsing, and
  worker routing can become primitive cascades.
- Collapse risk: low if ledgers/logs/rate limits/event waits are materialized
  projections, not recomputed from a single current-state dict.
- Verdict: `BUILD_WITH_RESCOPE`.
- Next action: reserve behind PgQueueLedger/Tork unless we need a larger
  workflow platform. Do not copy Hatchet API names or cloud/service concepts.

## PgQueueLedger

- Source: `https://github.com/janbjorge/pgqueuer`
- Product surface: database-backed job queue with transactional enqueue,
  worker claiming, scheduling, concurrency controls, completion tracking,
  dashboard/metrics, in-memory adapter, and framework integration.
- Shared fact source: job rows, entrypoint registry, status transitions,
  claim/lock records, scheduling/defer records, completion records, metrics,
  and dashboard snapshots.
- Public projections: queue dashboard, job detail/status, completion watcher,
  entrypoint/concurrency reports, metrics/tracing events, in-memory vs durable
  adapter behavior.
- Local free choices: claim ordering, notification vs polling fallback,
  completion materialization, retry/executor policy, concurrency key scoping,
  dashboard aggregation timing.
- Global invariants: enqueue/claim/complete/fail/cancel/schedule operations
  must leave job status, dashboard counts, completion watcher, metrics, and
  adapter behavior consistent.
- Contamination risk: medium/low. PostgreSQL queue idioms are known, but this
  can be benchmark-owned by avoiding exact SQL, `SKIP LOCKED`, and PgQueuer
  public names.
- Feature-pure risks: async/DB mechanics and cron parsing can dominate if not
  frontloaded. Use deterministic fake clock and a local SQLite/file adapter in
  reference tests unless strict Postgres is intentionally part of the task.
- Collapse risk: medium. Require retained completion history, dashboard
  snapshots, metrics, and recovery so the task cannot be solved as a one-dict
  current queue.
- Verdict: `BUILD`.
- Next action: best new Layer1 candidate. Build `PgQueueLedger` as a
  source-derived but benchmark-owned queue system with 10+ starter modules and
  50+ checks.

## AsynqQueue

- Source: `https://github.com/hibiken/asynq`
- Product surface: Redis-backed distributed task queue with scheduling,
  retries, recovery after worker crash, weighted/strict priority, uniqueness,
  timeout/deadline, task aggregation, pause/resume, metrics, CLI, and web UI.
- Shared fact source: task payloads, queue state, scheduled/retry/deadline
  sets, uniqueness keys, aggregation groups, worker heartbeats, metrics, and
  inspector views.
- Public projections: task lookup, queue stats, inspector CLI/UI, retry
  schedule, unique task conflicts, paused queue state, aggregation batches,
  worker heartbeat/recovery reports.
- Local free choices: priority arbitration, retry materialization, uniqueness
  TTL behavior, heartbeat expiry, aggregation flush policy, paused visibility.
- Global invariants: queue stats, inspector results, scheduled/retry sets,
  uniqueness conflicts, aggregation output, and worker recovery must agree
  after enqueue, duplicate, pause, timeout, crash, retry, and aggregation flush.
- Contamination risk: medium/high. Asynq is well known in Go task queues and
  exact Redis/Lua scripts would be implementation-specific.
- Feature-pure risks: Redis/Lua behavior and priority scheduling can become
  primitive failures. Unit tests must isolate uniqueness, priority, retry,
  timeout, and aggregation.
- Collapse risk: low if recovery/heartbeat/inspector/aggregation are durable
  projections.
- Verdict: `BUILD_WITH_RESCOPE`.
- Next action: viable queue reserve. Use a custom local broker/inspector API,
  not exact Asynq Redis schema or commands.

## TorkWorkflow

- Source: `https://github.com/runabol/tork`
- Product surface: workflow/job engine with REST API, coordinator/worker
  split, datastore, broker, recovery, retries, timeouts, pre/post tasks,
  conditional/parallel/each/subjob tasks, middleware, webhooks, search, CLI,
  and web UI.
- Shared fact source: job definitions, task nodes, task attempts, coordinator
  assignments, broker messages, datastore rows, runtime outputs, webhook
  deliveries, search index, and schedule records.
- Public projections: REST job status, task status/history, broker queue,
  coordinator state, webhook audit, search output, CLI summaries, schedule
  views.
- Local free choices: task dependency ordering, recovery materialization,
  webhook delivery retries, search indexing timing, timeout transition,
  broker redelivery, subjob parent/child status rollup.
- Global invariants: REST status, task history, broker/coordinator state,
  webhook audit, search index, and CLI output must agree after submit, retry,
  timeout, cancel, worker loss, subjob completion, and restart.
- Contamination risk: medium. Tork is less iconic than Temporal/Airflow but
  workflow engines are common. Use benchmark-owned schemas and deterministic
  shell/fake runtime; do not require Docker.
- Feature-pure risks: expression language, YAML parsing, and container runtime
  semantics must be frontloaded or stubbed.
- Collapse risk: low if broker, datastore, search, webhooks, and runtime
  outputs are materialized.
- Verdict: `BUILD`.
- Next action: strong Layer1 candidate alongside PgQueueLedger. Prefer if we
  want workflow-specific composition rather than queue-specific composition.

## Priority After This Pass

1. `PgQueueLedger`: best near-term source-derived queue task with manageable
   harness.
2. `TorkWorkflow`: best workflow-engine alternative, but broader than queue.
3. `BuildCache`: already judged Layer0-ready; proceed to Layer1 when cache
   domain is preferred.
4. `AsynqQueue`: useful queue reserve; rescope away from Redis internals.
5. `HatchetWorkflow`: strong but high contamination and scope risk.
6. `WorkflowScheduler`: pause candidate runs; repair provenance first.

## Required Next Gate

Before any candidate model run:

- write exact upstream evidence map with file/test/example citations;
- write public packet from source behavior, not from local prototype code;
- provide candidate-visible starter skeleton only after module boundaries are
  justified by product surface;
- implement 50+ executable hidden checks;
- build a reference package that passes 100%;
- create a cleanroom workspace and leakage scan;
- save full agent trajectory.
