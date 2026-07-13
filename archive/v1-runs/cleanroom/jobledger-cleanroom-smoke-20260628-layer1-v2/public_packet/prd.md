# JobLedger Full-Reproduction PRD

## Product Overview

JobLedger is a durable local job-processing subsystem for applications that
need inspectable background work without a distributed cluster. It is inspired
by retained job queues such as Oban, but it is a benchmark-owned product with
custom APIs, schemas, and command names.

The system keeps job rows, attempts, cron insertions, uniqueness windows,
events, queue projections, metrics, and recovery records coherent across API
calls, CLI commands, process restarts, export/import, and interrupted writes.

## Audience

The target user is an application developer or operator who wants to:

- enqueue immediate and scheduled jobs;
- claim and finish work deterministically;
- retry failures with bounded attempts;
- avoid duplicate work through uniqueness windows;
- run cron-like recurring jobs;
- inspect retained history, queue counts, metrics, and event streams;
- recover from interrupted operations.

## Non-Goals

- No Oban/Ecto/Postgres-compatible API.
- No Celery, Sidekiq, or Temporal clone.
- No distributed cluster protocol.
- No real wall-clock timing in tests; all scheduling uses an explicit virtual
  UTC clock.
- No worker code execution sandbox. Job execution is represented by public
  claim/complete/fail/cancel API calls.
- No hidden dependency on private storage layout.

## Required Artifact Shape

Candidates must implement an installable Python package named `jobledger` with
the public files in the provided starter skeleton:

```text
pyproject.toml
src/jobledger/
  __init__.py
  api.py
  cli.py
  models.py
  store.py
  scheduler.py
  retry.py
  uniqueness.py
  cron.py
  events.py
  metrics.py
  recovery.py
  export.py
```

## Interface-Locked Architecture

This is an interface-defined architecture task. Candidates may add private
helpers, but they must preserve the public module names, classes, functions,
arguments, and return-shape intent from the starter skeleton.

The purpose of the fixed architecture is measurement: unit tests can isolate
each public module with direct fixtures or mocks, while system tests integrate
all modules through `JobLedger` and the CLI to test cross-module invariants.

The public module responsibilities are:

- `models.py`: public records, state names, uniqueness policy, public error.
- `retry.py`: retry delay and retry/discard decision.
- `scheduler.py`: due-time and claim-order primitives.
- `uniqueness.py`: uniqueness keys and conflict detection.
- `cron.py`: deterministic schedule-slot materialization.
- `events.py`: public event validation and event totals.
- `metrics.py`: event-replay metrics and queue counts.
- `store.py`: durable store protocol and store opener.
- `recovery.py`: recovery marker classification and reports.
- `export.py`: public export/import payload validation and canonicalization.
- `api.py`: integrated `JobLedger` facade.
- `cli.py`: JSON CLI over the integrated facade.

The package must expose:

- an importable API in `jobledger.api`;
- documented primitive modules for unit-level behavior:
  `jobledger.models`, `jobledger.scheduler`, `jobledger.retry`,
  `jobledger.uniqueness`, `jobledger.cron`, `jobledger.events`,
  `jobledger.metrics`, `jobledger.store`, `jobledger.recovery`,
  and `jobledger.export`;
- a CLI command runnable as `python -m jobledger.cli`;
- durable state in a user-provided directory;
- JSON-compatible public reports.

SQLite or filesystem JSONL storage is allowed. The exact storage schema is not
public API except for exported snapshots and documented report schemas.

## State Model

### Job Record

Each job has:

- `id`: stable string assigned by the ledger;
- `queue`: non-empty string, default `default`;
- `kind`: worker or job kind string;
- `args`: JSON object;
- `state`: one of `available`, `scheduled`, `executing`, `retryable`,
  `completed`, `cancelled`, `discarded`;
- `priority`: integer, lower value claims first, default `0`;
- `max_attempts`: positive integer, default `3`;
- `attempt`: current attempt count;
- `scheduled_at`: virtual UTC timestamp or null;
- `created_at`, `updated_at`: virtual UTC timestamps;
- `unique`: optional uniqueness policy;
- `last_error`: optional public error summary.

### Durable Ledgers

The product must retain these public logical ledgers:

- job rows;
- attempt ledger;
- event stream;
- cron ledger;
- uniqueness windows;
- metrics rollups;
- recovery records.

Implementations may store these in one database or multiple files, but public
reports must behave as if these ledgers exist independently and remain
consistent.

## Lifecycle Semantics

### Enqueue And Schedule

Immediate jobs enter `available`. Jobs with `scheduled_at` in the future enter
`scheduled`. When the virtual clock reaches `scheduled_at`, the job becomes
claimable and appears in queue counts as available.

### Claim

`claim(queue, worker, limit=1, now=None)` moves claimable jobs to `executing`.
Claim order is deterministic:

1. queue match;
2. state is `available` or due `scheduled`/`retryable`;
3. lower priority first;
4. earlier `scheduled_at` or `created_at`;
5. stable job ID.

Claim emits events and updates metrics.

### Complete, Fail, Cancel

Completing an executing job moves it to `completed`.

Failing an executing job appends an attempt record and either:

- moves it to `retryable` with a future `scheduled_at` if attempts remain; or
- moves it to `discarded` if attempts are exhausted.

Cancelling a non-terminal job moves it to `cancelled`. Terminal jobs remain
retained for history and metrics.

### Retry

The default retry delay is deterministic:

```text
delay_seconds = 10 * 2 ** (attempt - 1)
```

No random jitter is used. Custom retry policies are out of scope.

### Uniqueness

A uniqueness policy may specify:

- fields: any subset of `kind`, `queue`, `args`;
- period seconds;
- states to consider;
- on conflict: `reject` or `replace`.

The uniqueness window must agree with job rows, conflict reports, events, and
metrics. Expired windows no longer block new jobs.

### Cron

Cron entries are named schedules with:

- `name`;
- `queue`;
- `kind`;
- `args`;
- `every_seconds`;
- optional uniqueness policy.

`tick(now)` inserts at most one job per schedule slot. Re-running `tick` after
restart or import must not duplicate already materialized slots.

### Metrics And Events

Events are append-only public records with stable ordering. Metrics are public
rollups derived from event semantics but must be materialized or replayable so
they survive restart/export/import.

Required metrics:

- counts by state;
- counts by queue;
- counts by kind;
- success/failure/discard/cancel totals;
- retry scheduled totals.

Metrics may be stored as materialized rollups or replayed from the retained
event stream, but they must not be recomputed only from current job rows. The
event stream is the public source for metric replay.

### Retention And Prune

Terminal jobs remain visible until pruned. `prune(retain_seconds, now)` may
remove detailed rows for terminal jobs older than the retention window, but it
must preserve enough public summary data for metrics, event history, and prune
reports. Non-terminal jobs are never pruned.

The prune report must list:

- pruned job IDs;
- retained terminal job IDs;
- blocked non-terminal job IDs;
- metrics summary before and after.

### Recovery

Interrupted operations may leave recovery markers. `recover()` must either roll
forward or roll back incomplete operations. After recovery, job rows, queue
counts, events, metrics, uniqueness windows, cron ledger, and recovery report
must agree.

## Public API

The importable API should provide a `JobLedger` class:

```python
from jobledger.api import JobLedger, JobLedgerError

ledger = JobLedger(path)
ledger.enqueue(kind, args=None, queue="default", priority=0, max_attempts=3,
               scheduled_at=None, unique=None, now=None)
ledger.claim(queue="default", worker="worker-1", limit=1, now=None)
ledger.complete(job_id, result=None, now=None)
ledger.fail(job_id, error, now=None)
ledger.cancel(job_id, reason=None, now=None)
ledger.tick(now)
ledger.configure_cron(name, every_seconds, kind, args=None, queue="default",
                      unique=None)
ledger.jobs(filters=None)
ledger.history(job_id)
ledger.queue_report()
ledger.conflict_report()
ledger.metrics()
ledger.events(after=None)
ledger.recover()
ledger.prune(retain_seconds, now=None)
ledger.export_state()
JobLedger.import_state(path, data)
```

API outputs must be JSON-compatible dictionaries/lists.

## CLI Contract

The CLI is a black-box public surface. It must support:

```text
python -m jobledger.cli init PATH
python -m jobledger.cli enqueue PATH --kind KIND [--queue Q] [--args JSON]
python -m jobledger.cli claim PATH --queue Q --worker W [--limit N] [--now TS]
python -m jobledger.cli complete PATH JOB_ID [--result JSON] [--now TS]
python -m jobledger.cli fail PATH JOB_ID --error TEXT [--now TS]
python -m jobledger.cli cancel PATH JOB_ID [--reason TEXT] [--now TS]
python -m jobledger.cli cron-set PATH NAME --every SECONDS --kind KIND
python -m jobledger.cli tick PATH --now TS
python -m jobledger.cli jobs PATH [--state STATE] [--queue Q]
python -m jobledger.cli queue-report PATH
python -m jobledger.cli conflict-report PATH
python -m jobledger.cli metrics PATH
python -m jobledger.cli events PATH
python -m jobledger.cli prune PATH --retain-seconds N --now TS
python -m jobledger.cli recover PATH
python -m jobledger.cli export PATH
python -m jobledger.cli import PATH JSON_FILE
```

CLI output is JSON unless the command fails. Failure output must include a
public error code and message.

## Ordering And Determinism

- All timestamps are ISO-8601 UTC strings or integer epoch seconds; the API must
  accept both if documented.
- Tests use explicit `now`; implementations must not depend on wall clock when
  `now` is provided.
- Report ordering must be deterministic: sort by public keys or stable event
  order.
- Export/import must preserve public behavior even if private IDs differ, as
  long as job IDs in exported data remain stable.

## Error Semantics

Invalid operations raise `JobLedgerError` or return CLI error JSON. Failed
operations must be atomic from the public API perspective.

Examples:

- unknown job ID;
- completing a non-executing job;
- invalid queue/kind;
- invalid cron interval;
- uniqueness conflict under `reject`;
- malformed import data.

## Workflow Examples

### Failure And Retry

1. Enqueue job `send_email`.
2. Claim it.
3. Fail it at attempt 1.
4. Job becomes `retryable` with future `scheduled_at`.
5. Metrics show one failure and one retry scheduled.
6. Event stream and history include enqueue, claim, fail, retry scheduled.

### Cron Idempotence

1. Configure `daily_digest` every 86400 seconds.
2. Tick at slot `T`.
3. Restart or import/export.
4. Tick again at the same `T`.
5. Exactly one job exists for that schedule slot.

### Recovery

1. Begin an operation that writes a job row and event.
2. Simulate interruption before metrics update.
3. Run `recover()`.
4. Job rows, events, metrics, queue report, and recovery report agree.

## Ambiguity Boundaries

The PRD intentionally defines deterministic retry delay, virtual time, and
claim ordering. Hidden tests must not require private storage layout, exact
internal event IDs, or a particular database backend.
