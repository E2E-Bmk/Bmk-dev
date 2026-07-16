# PgQueuer Specification

## Product Overview

PgQueuer is a Python library for building asynchronous background job queues. The production backend stores queue state in PostgreSQL, while the in-memory backend provides the same queue and scheduler programming model without a database. The in-memory backend is suitable for tests, local development, short-lived batch jobs, and proof-of-concept workflows where durability across process restarts is not required.

The queue model has producers that enqueue jobs, consumers that register named async entrypoints, and managers that run registered handlers until the queue is drained or explicitly shut down. A job has an integer id, entrypoint name, payload, priority, status, execution time, attempt count, heartbeat, optional dedupe key, and optional tracing headers. Jobs move through observable statuses such as `queued`, `picked`, `successful`, `exception`, `failed`, `canceled`, and `deleted`.

## Scope

This specification covers the public in-memory workflow: constructing `PgQueuer` with `PgQueuer.in_memory()`, registering queue entrypoints and schedules, using `pgq.qm.queries` to enqueue/dequeue/inspect/cancel/clear/retry/log jobs, running queue jobs with `QueueManager.run()` in drain mode, using public model objects, observing queue state through query projections, and exercising schema-management no-ops on the in-memory adapter.

The PostgreSQL SQL schema, database drivers, CLI commands, tracing provider integrations, Prometheus/FastAPI integrations, and SQL query plan details are outside this task's implementation scope.

## Installable Surface

The package is importable as `pgqueuer`. The public top-level exports are:

```python
from pgqueuer import (
    AsyncpgDriver, AsyncpgPoolDriver, DatabaseRetryEntrypointExecutor,
    InMemoryDriver, InMemoryQueries, Job, JobId, PgQueuer, PsycopgDriver,
    Queries, QueueManager, RetryRequested, SchedulerManager,
)
```

The in-memory workflow also uses these documented public modules:

```python
from pgqueuer.models import Job, Context, Schedule, ScheduleContext
from pgqueuer.types import QueueExecutionMode, JobId
from pgqueuer.errors import RetryRequested
```

## Public API

`PgQueuer.in_memory(channel=None, resources=None) -> PgQueuer` returns a ready-to-use queue object backed by in-process state. The returned object has `.connection`, `.queries`, `.qm`, `.sm`, `.shutdown`, and `.resources` attributes. The `.queries` object must be an `InMemoryQueries` instance, and `.connection` must be an `InMemoryDriver` instance.

`PgQueuer.entrypoint(name, *, concurrency_limit=0, accepts_context=None, on_failure="delete", executor_factory=None)` returns a decorator for async job handlers. The decorator returns the original function and registers it under `name`.

`PgQueuer.schedule(entrypoint, expression, executor_factory=None, clean_old=False, accepts_context=None)` returns a decorator for async scheduled handlers. The decorator returns the original function and registers the `(entrypoint, expression)` schedule.

`QueueManager.run(dequeue_timeout=timedelta(seconds=30), batch_size=10, mode=QueueExecutionMode.continuous, max_concurrent_tasks=None, shutdown_on_listener_failure=False, heartbeat_timeout=timedelta(seconds=30))` processes registered jobs. In drain mode it must return after no eligible queued jobs and no in-flight jobs remain.

`InMemoryQueries.enqueue(entrypoint, payload, priority=0, execute_after=None, dedupe_key=None, headers=None)` accepts either one job (`str`, `bytes | None`, `int`) or parallel lists of entrypoints, payloads, priorities, execute-after delays, dedupe keys, and headers. It returns a list of `JobId` values in enqueue order.

The query object exposes async inspection and mutation methods: `dequeue`, `log_jobs`, `retry_job`, `requeue_jobs`, `list_failed_jobs`, `mark_job_as_cancelled`, `clear_queue`, `queue_size`, `queued_work`, `queue_log`, `job_status`, `log_statistics`, `next_deferred_eta`, `insert_schedule`, `fetch_schedule`, `set_schedule_queued`, `update_schedule_heartbeat`, `peek_schedule`, `delete_schedule`, `clear_schedule`, `clear_statistics_log`, `clear_queue_log`, `install`, `upgrade`, `uninstall`, and schema check methods.

## Product State Model

PgQueuer's in-memory state has three public projections of the same facts:

- the active queue projection returned by `dequeue()`, `queue_size()`, `queued_work()`, `list_failed_jobs()`, and `next_deferred_eta()`;
- the audit projection returned by `queue_log()`, `job_status()`, and `log_statistics()`;
- the handler/scheduler projection produced by `QueueManager.run()`, registered handler calls, schedule registration, `peek_schedule()`, `fetch_schedule()`, and `set_schedule_queued()`.

These projections must remain consistent:

- A job created by `enqueue()` must appear as `queued` in queue statistics and in the audit log before it is processed.
- A job dequeued for processing must move to `picked` and must be visible as `picked` in `job_status()` until a later terminal or retry transition is logged.
- A successful handler run must remove the active job and must append a `successful` audit entry for the same job id.
- A handler that raises `RetryRequested` must keep the same job id, increment attempts, restore status to `queued`, and append a queued retry log entry.
- A handler that raises another exception with `on_failure="delete"` must remove the active job and append an `exception` audit entry.
- A handler that raises another exception with `on_failure="hold"` must keep the active job with status `failed`, make it visible through `list_failed_jobs()`, and release any dedupe key.
- A canceled job must be removed from active queue views and must remain visible through log/status views as `canceled`.
- A schedule registered through `schedule()` must appear in schedule storage after scheduler insertion and must return to `queued` after dispatch.

## Queue And Enqueue Behavior

`enqueue()` must create jobs with monotonically increasing integer ids starting at 1 for a fresh in-memory query object. It must preserve payload bytes or `None`, entrypoint name, priority, headers, and dedupe key. It must set initial status to `queued`, initial attempts to `0`, and execution time to current UTC time plus `execute_after` or zero delay when omitted.

When `enqueue()` receives list inputs, all list-valued arguments must align by position. A batch call must return one `JobId` per input entry in the same order.

Jobs eligible for `dequeue()` are queued jobs whose entrypoint is in the requested entrypoint map and whose `execute_after` is not in the future. Dequeue selection must prefer higher `priority` values and must use lower job id as the tie-breaker within the same priority.

`dequeue(batch_size, ...)` must raise `ValueError` when `batch_size < 1`. It must return an empty list when no entrypoints are supplied or no eligible jobs exist. When jobs are returned, their active status must become `picked`, their `queue_manager_id` must be assigned, and a `picked` log entry must be appended.

Per-entrypoint concurrency limits must be honored when selecting queued jobs. A positive `concurrency_limit` permits at most that many currently picked jobs for the entrypoint. A limit of `0` means unlimited. The global concurrency limit must cap the total number of picked jobs owned by the same queue manager.

`next_deferred_eta(entrypoints)` must return `None` when there are no future queued jobs for the requested entrypoints. When deferred queued jobs exist, it must return a positive `timedelta` until the soonest eligible time.

## Queue Processing Behavior

Handlers registered with `entrypoint()` must be called with the `Job` object. When `accepts_context` is `None`, a handler with a parameter annotated as `Context` must receive a `Context` object as its second argument; otherwise it must receive only the job. Passing `accepts_context=True` must force context injection, and passing `False` must suppress context injection.

The `Context.resources` mapping must be the same user-provided resources mapping passed to `PgQueuer.in_memory(resources=...)`. Mutations visible through that mapping during a handler run must be observable after the run.

In `QueueExecutionMode.drain`, `QueueManager.run()` must process available jobs and return after the queue is empty and active tasks have completed. A normal handler return must append `successful`; a `RetryRequested` exception must requeue the job; any other exception must append `exception` or `failed` according to `on_failure`.

`max_concurrent_tasks` must be at least twice `batch_size` when supplied. Violating this rule must raise `RuntimeError`.

## Retry, Failure, And Cancellation Behavior

`RetryRequested(delay=timedelta(0), reason=None)` must be an exception with `.delay` and `.reason` attributes. With no reason, its string value must be `Retry requested`; with a reason, its string value must be that reason.

When a handler raises `RetryRequested`, the job must remain active with the same id, status `queued`, attempts incremented by one, original payload and priority preserved, and `execute_after` moved by the requested delay. A retry must append an audit entry with status `queued`.

`requeue_jobs(ids)` must change failed jobs back to `queued`, reset attempts to `0`, and append a queued log entry. It must ignore ids that are missing or not currently failed.

`mark_job_as_cancelled(ids)` must remove matching active jobs, append `canceled` log entries, and notify cancellation listeners. It must ignore missing ids without raising.

`clear_queue()` with no entrypoint must remove all active jobs and clear dedupe state without adding deletion log entries. `clear_queue(entrypoint)` must remove only jobs matching one entrypoint, append `deleted` log entries for removed jobs, and leave other entrypoints active. Passing a list of entrypoints must filter by any listed entrypoint.

## Dedupe, Logs, Statistics, And Schema Behavior

When a queued or active job has a `dedupe_key`, a second enqueue with the same key must raise the package's duplicate-job exception while the key is still reserved. The dedupe key must become reusable after the job is logged as `successful`, `exception`, `failed`, `canceled`, or `deleted`.

`queue_size()` must return one count per `(entrypoint, priority, status)` active queue group. It must not report jobs that have already been removed from the active queue.

`queue_log()` must return audit entries in append order. `job_status(ids)` must return the latest logged status for each requested id that appears in the log. `log_statistics(limit, last=None)` must aggregate unaggregated audit entries by entrypoint, priority, status, and second; repeated calls must not double-count entries already aggregated. `clear_statistics_log()` and `clear_queue_log()` must remove data globally or for selected entrypoints.

For the in-memory adapter, schema management methods must not require a database. `install()` and `upgrade()` must complete without side effects. `uninstall()` must clear jobs, logs, schedules, statistics, and dedupe reservations. Schema inspection methods must return `True`.

## Scheduling Behavior

`schedule(entrypoint, expression, clean_old=False, accepts_context=None)` must validate cron expressions and raise `ValueError` for invalid expressions. Duplicate registration of the same normalized `(entrypoint, expression)` pair must raise `RuntimeError`.

PgQueuer supports five-field cron expressions and six-field expressions with the seconds field last. A six-field expression such as `* * * * * */3` represents a second-level schedule.

When scheduler storage is populated, `insert_schedule()` must insert one queued schedule for each registered cron entry and must skip duplicate `(entrypoint, expression)` rows. `fetch_schedule()` must return due queued schedules as `picked`, and `set_schedule_queued(ids)` must return them to `queued` while setting `last_run`.

Handlers registered with `schedule()` must be called with the due `Schedule` object as the first argument. When `accepts_context` is `None`, a scheduled handler with a positionally bindable parameter annotated as `ScheduleContext` must receive a `ScheduleContext` object as its second argument; otherwise it must receive only the schedule. Passing `accepts_context=True` must force schedule-context injection, and passing `False` must suppress schedule-context injection. The injected `ScheduleContext.resources` mapping must mirror the resources passed to `PgQueuer.in_memory(resources=...)`.

## Error Semantics

`entrypoint()` must raise `RuntimeError` when registering a duplicate name. It must raise `ValueError` when `concurrency_limit` is not an integer, when it is negative, when `accepts_context` is neither `None` nor a boolean, or when `on_failure` is not `"delete"` or `"hold"`.

`schedule()` must raise `ValueError` for invalid cron expressions and `RuntimeError` for duplicate normalized schedule registrations.

`dequeue()` must raise `ValueError` when `batch_size` is less than one.

`QueueManager.run()` must raise `RuntimeError` when `max_concurrent_tasks` is less than twice the requested batch size.

The in-memory schema methods must not raise because a PostgreSQL table, enum, trigger, function, or index is absent.

## Cross-View Invariants

- A value written through `enqueue()` must be visible through `dequeue()` for the same entrypoint when the job is eligible.
- A status transition produced by `dequeue()`, `log_jobs()`, `retry_job()`, cancellation, or deletion must be reflected by `job_status()` for that job id.
- A job removed from active state by successful logging, exception logging, cancellation, or deletion must not appear in later `queue_size()` groups.
- A failed job must appear in `list_failed_jobs()` until it is requeued or deleted.
- A dedupe key must block duplicate enqueue while the original job is active and must be reusable after a terminal log/removal path releases it.
- A priority ordering visible through `dequeue()` must agree with the priority values stored on the returned `Job` objects.
- A resource object supplied to `PgQueuer.in_memory()` must be visible through both job `Context` and schedule `ScheduleContext`.
- A schedule fetched as due must return to `queued` after dispatch or `set_schedule_queued()`, and `peek_schedule()` must show the same schedule id.

## Representative Workflows

```python
from pgqueuer import PgQueuer
from pgqueuer.models import Job, Context
from pgqueuer.types import QueueExecutionMode

pgq = PgQueuer.in_memory(resources={"seen": []})

@pgq.entrypoint("send", accepts_context=True)
async def send(job: Job, ctx: Context) -> None:
    ctx.resources["seen"].append(job.payload)

ids = await pgq.qm.queries.enqueue(["send", "send"], [b"a", b"b"], [0, 5])
await pgq.qm.run(mode=QueueExecutionMode.drain, batch_size=2, max_concurrent_tasks=4)
statuses = await pgq.qm.queries.job_status(ids)
```

After this workflow, both jobs must have a latest status of `successful`, the handler must have seen payload `b"b"` before `b"a"` because of priority ordering, and the active queue must be empty.

## Non-Goals

This scoped implementation does not need to provide a real PostgreSQL backend, SQL generation, database migrations, CLI command behavior, process signal handling, Prometheus metrics, OpenTelemetry/Logfire/Sentry integrations, FastAPI or Flask integration, MCP server behavior, Docker/Testcontainers support, or exact internal storage layouts.

## Invocation Protocol

The package must be importable from the candidate solution directory as `pgqueuer`. `python -m pgqueuer` is not required for this scoped task. The `pgq` console script is documented but not evaluated in this scope.

Exit code behavior for the scoped package is limited to pytest execution: passing tests exit with code `0`, assertion or runtime failures exit nonzero.

## Implementation Guidance

The expected implementation focuses on public in-memory behavior: import surface, queue enqueue/dequeue ordering, state transitions, handler dispatch, context resource injection, retry and failure handling, dedupe release, cancellation, schedule registration/storage/dispatch, schema no-op behavior, and cross-view consistency among queue, log, status, statistics, and scheduler projections. Tests are behavioral and use only public imports and public object attributes. They do not require PostgreSQL, Docker, CLI execution, hidden fixtures, internal dictionaries, exact repr strings, or exact exception message wording beyond the public `RetryRequested` default string.
