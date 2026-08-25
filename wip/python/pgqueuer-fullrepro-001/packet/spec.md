# PgQueuer Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

PgQueuer is a Python library for building asynchronous background job queues with async producers, consumers, and schedulers. This specification defines the in-memory adapter, which provides the full queue and scheduler programming model without external services. The in-memory backend is suitable for tests, local development, short-lived batch jobs, and proof-of-concept workflows where durability across process restarts is not required.

The queue model has producers that enqueue jobs, consumers that register named async entrypoints, and managers that run registered handlers until the queue is drained or explicitly shut down. A job has an integer id, entrypoint name, payload, priority, status, execution time, attempt count, heartbeat, optional dedupe key, and optional tracing headers. Jobs move through observable statuses such as `queued`, `picked`, `successful`, `exception`, `failed`, `canceled`, and `deleted`.

## Non-Goals

- Persistent database-backed queue storage is excluded; the in-memory adapter is the specified production surface for this contract.
- Command-line entry points, process signal handling, and metrics export are not part of the contract.
- Web-framework integration helpers and container orchestration utilities are excluded.
- Exact internal storage field layout and private helper modules are not specified.

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

## Queue and Enqueue Behavior

`PgQueuer.in_memory()` returns a ready-to-use queue object backed by in-process state.

**Factory wiring.** The returned object must expose `.connection` as an `InMemoryDriver` instance, `.queries` as an `InMemoryQueries` instance, `.qm` as a `QueueManager` whose `.queries` is the same object as the top-level `.queries`, `.sm` as a `SchedulerManager` whose `.queries` is the same object, `.shutdown` as a shutdown event, and `.resources` as the user-provided resources mapping. When `resources` is passed to `in_memory()`, both `.qm.resources` and `.sm.resources` must expose that same mapping. Each call to `in_memory()` must create an independent instance with its own id counter starting at 1.

**Handler registration.** `PgQueuer.entrypoint()` and `PgQueuer.schedule()` must return decorators that register handlers and return the original function unchanged, so applying the decorator must not wrap or alter the function object.

**Enqueue behavior.** `enqueue()` must create jobs with monotonically increasing integer ids starting at 1 for a fresh in-memory query object. It must preserve payload bytes or `None`, entrypoint name, priority, headers, and dedupe key. It must set initial status to `queued`, initial attempts to `0`, and execution time to current UTC time plus the `execute_after` delay or zero delay when omitted.

**Batch enqueue.** When `enqueue()` receives list inputs, all list-valued arguments must align by position. A batch call must return one `JobId` per input entry in the same order. For example, enqueueing three entrypoints with three payloads and three priorities must return `[JobId(1), JobId(2), JobId(3)]`.

**Dequeue selection.** Jobs eligible for `dequeue()` are queued jobs whose entrypoint is in the requested entrypoint map and whose `execute_after` is not in the future. Dequeue selection must prefer higher `priority` values and must use lower job id as the tie-breaker within the same priority.

**Dequeue constraints.** `dequeue()` must raise `ValueError` when `batch_size` is less than 1. It must return an empty list when no entrypoints are supplied or no eligible jobs exist. When jobs are returned, their active status must become `picked`, their `queue_manager_id` must be assigned, and a `picked` log entry must be appended. A dequeued `Job` must expose `status` as `"picked"`.

**Concurrency limits.** Per-entrypoint concurrency limits must be honored when selecting queued jobs. A positive `concurrency_limit` permits at most that many currently picked jobs for the entrypoint. A limit of `0` means unlimited. The global concurrency limit via `max_concurrent_tasks` must cap the total number of concurrently running tasks owned by the same queue manager.

**Deferred jobs.** `next_deferred_eta()` must return `None` when there are no future queued jobs for the requested entrypoints. When deferred queued jobs exist whose `execute_after` is in the future, it must return a positive `timedelta` until the soonest eligible time. Immediately eligible queued jobs must not affect the deferred eta.

## Queue Processing Behavior

Handlers registered with `entrypoint()` receive jobs for processing, and the queue manager orchestrates dispatch.

**Handler invocation.** Handlers must be called with the `Job` object as the first argument. When `accepts_context` is `None`, a handler with a parameter annotated as `Context` must receive a `Context` object as its second argument; otherwise it must receive only the job. Passing `accepts_context` as `True` must force context injection. Passing `accepts_context` as `False` must suppress context injection even when the handler has a `Context` annotation.

**Context resources.** The `Context.resources` mapping must be the same user-provided resources mapping passed to `PgQueuer.in_memory(resources=...)`. Mutations visible through that mapping during a handler run must be observable after the run through the top-level `pgq.resources` reference.

**Drain mode.** In `QueueExecutionMode.drain`, `QueueManager.run()` must process available jobs and return after the queue is empty and active tasks have completed. A normal handler return must append a `successful` log entry and remove the job from the active queue. A `RetryRequested` exception must requeue the job. Any other exception must append `exception` or `failed` according to the entrypoint's `on_failure` policy.

**Run parameters.** `QueueManager.run()` accepts `dequeue_timeout`, `batch_size`, `mode`, `max_concurrent_tasks`, and other settings. In drain mode it must return after no eligible queued jobs and no in-flight jobs remain. When `max_concurrent_tasks` is less than twice `batch_size`, `run()` must raise `RuntimeError`.

## Retry, Failure, and Cancellation Behavior

These mechanisms control what happens when a handler cannot complete normally.

**RetryRequested exception.** `RetryRequested` must be an exception with `.delay` and `.reason` attributes. When created with no arguments, `delay` must be `timedelta(0)` and `reason` must be `None`. With no reason, `str()` must return `"Retry requested"`; with a reason, `str()` must return that reason string. When created with a delay and reason, both must be stored on the corresponding attributes.

**Retry behavior.** When a handler raises `RetryRequested`, the job must remain active with the same id, status `queued`, attempts incremented by one, original payload and priority preserved, and `execute_after` moved by the requested delay. A retry must append an audit entry with status `queued`. On the retry execution, the handler must observe the incremented `attempts` value.

**Requeue failed jobs.** `requeue_jobs()` must change failed jobs back to `queued`, reset attempts to `0`, and append a queued log entry. It must ignore ids that are missing or not currently in failed status, leaving them unchanged.

**Cancellation.** `mark_job_as_cancelled()` must remove matching active jobs, append `canceled` log entries, and release any held dedupe keys. It must ignore missing ids without raising. After cancellation, the job must not appear in `queue_size()` results but must appear as `"canceled"` in `job_status()`.

**Clear queue.** `clear_queue()` with no entrypoint must remove all active jobs, clear dedupe state, and must not add deletion log entries. `clear_queue()` with a single entrypoint name must remove only jobs matching that entrypoint, append `deleted` log entries for removed jobs, and leave other entrypoints active. Passing a list of entrypoints must filter by any listed entrypoint. Clearing without a filter must release dedupe keys for all removed jobs.

**Failure policies.** When `on_failure` is `"delete"` (the default), an unhandled exception must remove the active job and append an `exception` audit entry. When `on_failure` is `"hold"`, an unhandled exception must keep the active job with status `failed`, make it visible through `list_failed_jobs()`, and release any dedupe key so the same key can be reused.

## Dedupe, Logs, Statistics, and Schema Behavior

These features provide deduplication, audit trails, aggregated statistics, and schema management.

**Deduplication.** When a queued or active job has a `dedupe_key`, a second enqueue with the same key must raise the package's duplicate-job exception while the key is still reserved. The dedupe key must become reusable after the job is logged as `successful`, `exception`, `failed`, `canceled`, or `deleted`, or after `clear_queue()` removes the job. Cancellation via `mark_job_as_cancelled` must also release the dedupe key.

**Queue size.** `queue_size()` must return one entry per `(entrypoint, priority, status)` active queue group. Each entry must expose `.entrypoint`, `.priority`, `.status`, and `.count`. It must not report jobs that have already been removed from the active queue. When no active jobs exist, it must return an empty list.

**Queue log.** `queue_log()` must return audit entries in append order. Each entry must expose `.job_id`, `.entrypoint`, `.status`, and `.priority`. The log must record the full lifecycle: a job enqueued, picked, and completed must appear as three ordered entries with statuses `queued`, `picked`, and `successful` respectively.

**Job status.** `job_status()` must return the latest logged status for each requested id that appears in the log. After a job transitions through `queued` → `picked` → `successful`, requesting its status must return `"successful"`.

**Log statistics.** `log_statistics()` must aggregate unaggregated audit entries by entrypoint, priority, status, and second. Each result entry must expose `.entrypoint`, `.priority`, `.status`, and `.count`. Repeated calls must not double-count entries already aggregated. When `limit` is provided, it must cap the number of result entries returned.

**Clearing logs and statistics.** `clear_statistics_log()` must remove aggregated statistics globally or for a selected entrypoint. `clear_queue_log()` must remove audit log entries globally or for a selected entrypoint, leaving entries for other entrypoints intact.

**Schema management.** For the in-memory adapter, `install()` and `upgrade()` must complete without side effects. `uninstall()` must clear jobs, logs, schedules, statistics, and dedupe reservations, resetting the adapter to a clean state (though the id counter may continue from its previous value). Schema inspection methods `has_table`, `table_has_column`, `table_has_index`, `has_user_defined_enum`, `has_function`, and `has_trigger` must all return `True` for any input, since the in-memory adapter does not require database schema objects.

## Scheduling Behavior

The scheduler registers cron-driven handlers and dispatches them when their schedules become due.

**Schedule registration.** `schedule()` must validate cron expressions and raise `ValueError` for invalid expressions. Duplicate registration of the same normalized `(entrypoint, expression)` pair must raise `RuntimeError`. PgQueuer must support five-field cron expressions and six-field expressions with the seconds field last; for example, `"* * * * * */3"` represents a schedule that fires every three seconds.

**Schedule storage.** When scheduler storage is populated via `insert_schedule()`, it must insert one queued schedule for each registered cron entry and must skip duplicate `(entrypoint, expression)` rows on subsequent insertions. `fetch_schedule()` must return due queued schedules as `picked`. `set_schedule_queued()` must return them to `queued` while setting `last_run`.

**Schedule object access.** A `Schedule` object passed to a handler or returned by `peek_schedule()` must expose `.id`, `.entrypoint`, `.status`, `.heartbeat`, and `.last_run`. After a schedule is dispatched and returned to queued, `last_run` must be set to a non-`None` value.

**Schedule handler invocation.** Handlers registered with `schedule()` must be called with the due `Schedule` object as the first argument. When `accepts_context` is `None`, a scheduled handler with a positionally bindable parameter annotated as `ScheduleContext` must receive a `ScheduleContext` object as its second argument; otherwise it must receive only the schedule. Passing `accepts_context` as `True` must force schedule-context injection, and passing `False` must suppress it. The injected `ScheduleContext.resources` mapping must mirror the resources passed to `PgQueuer.in_memory(resources=...)`.

**Schedule lifecycle.** After the scheduler manager dispatches a due schedule, the handler must observe `schedule.status` as `"picked"`. After dispatch completes, the schedule must be returned to `queued` status. `peek_schedule()` must show the schedule with its current status.

**Schedule management.** `delete_schedule()` must remove matching schedules by id set or by entrypoint set. After deletion, the removed schedules must not appear in `peek_schedule()`. `clear_schedule()` must remove all schedule registrations.

**Schedule heartbeat.** `update_schedule_heartbeat()` must update the heartbeat timestamp for the specified schedule ids without changing their status. After the update, the schedule's `heartbeat` must be greater than or equal to its previous value.

## State Model

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

## Error Semantics

`entrypoint()` must raise `RuntimeError` when registering a duplicate name. It must raise `ValueError` when `concurrency_limit` is not an integer, when it is negative, when `accepts_context` is neither `None` nor a boolean, or when `on_failure` is not `"delete"` or `"hold"`.

`schedule()` must raise `ValueError` for invalid cron expressions and `RuntimeError` for duplicate normalized schedule registrations.

`dequeue()` must raise `ValueError` when `batch_size` is less than one.

`QueueManager.run()` must raise `RuntimeError` when `max_concurrent_tasks` is less than twice the requested batch size.

The in-memory schema methods must not raise because a database table, enum, trigger, function, or index is absent.

## Cross-View Invariants

1. A value written through `enqueue()` must be visible through `dequeue()` for the same entrypoint when the job is eligible.
2. A status transition produced by `dequeue()`, `log_jobs()`, `retry_job()`, cancellation, or deletion must be reflected by `job_status()` for that job id.
3. A job removed from active state by successful logging, exception logging, cancellation, or deletion must not appear in later `queue_size()` groups.
4. A failed job must appear in `list_failed_jobs()` until it is requeued or deleted.
5. A dedupe key must block duplicate enqueue while the original job is active and must be reusable after a terminal log/removal path releases it.
6. A priority ordering visible through `dequeue()` must agree with the priority values stored on the returned `Job` objects.
7. A resource object supplied to `PgQueuer.in_memory()` must be visible through both job `Context` and schedule `ScheduleContext`.
8. A schedule fetched as due must return to `queued` after dispatch or `set_schedule_queued()`, and `peek_schedule()` must show the same schedule id.

## Public Interface

### Import Surface

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

### API Catalog

| Name | Kind | Role |
|------|------|------|
| PgQueuer | class | Queue application root; registers handlers and schedules |
| PgQueuer.in_memory | classmethod | Construct an in-memory queue with optional shared resources |
| PgQueuer.entrypoint | method | Register an async job handler under a named entrypoint |
| PgQueuer.schedule | method | Register a cron-driven scheduled handler |
| QueueManager | class | Dequeue, dispatch, and run registered job handlers |
| QueueManager.run | method | Process queued jobs until drain or shutdown |
| InMemoryQueries | class | In-memory enqueue, dequeue, log, schedule, and schema queries |
| InMemoryDriver | class | In-memory connection adapter for query operations |
| InMemoryQueries.enqueue | method | Create one or many queued jobs |
| InMemoryQueries.dequeue | method | Select eligible jobs for processing |
| InMemoryQueries.log_jobs | method | Append audit entries for job status transitions |
| InMemoryQueries.retry_job | method | Requeue a job after a retry request |
| InMemoryQueries.requeue_jobs | method | Move failed jobs back to queued state |
| InMemoryQueries.list_failed_jobs | method | List jobs in failed status |
| InMemoryQueries.mark_job_as_cancelled | method | Cancel active jobs by id |
| InMemoryQueries.clear_queue | method | Remove active jobs globally or by entrypoint |
| InMemoryQueries.queue_size | method | Count active jobs grouped by entrypoint, priority, and status |
| InMemoryQueries.queued_work | method | Summarize queued work by entrypoint |
| InMemoryQueries.queue_log | method | Return audit entries in append order |
| InMemoryQueries.job_status | method | Return latest logged status per job id |
| InMemoryQueries.log_statistics | method | Aggregate audit entries into statistics |
| InMemoryQueries.next_deferred_eta | method | Return delay until the next deferred job is eligible |
| InMemoryQueries.insert_schedule | method | Populate scheduler storage from registered cron entries |
| InMemoryQueries.fetch_schedule | method | Return due schedules as picked |
| InMemoryQueries.set_schedule_queued | method | Return fetched schedules to queued state |
| InMemoryQueries.peek_schedule | method | Inspect registered schedules without dispatch |
| InMemoryQueries.delete_schedule | method | Remove schedule registrations by id or entrypoint |
| InMemoryQueries.clear_schedule | method | Remove all schedule registrations |
| InMemoryQueries.update_schedule_heartbeat | method | Update heartbeat timestamp for schedules |
| InMemoryQueries.clear_statistics_log | method | Clear aggregated or raw statistics |
| InMemoryQueries.clear_queue_log | method | Clear audit log entries |
| InMemoryQueries.install | method | No-op schema install for the in-memory adapter |
| InMemoryQueries.upgrade | method | No-op schema upgrade for the in-memory adapter |
| InMemoryQueries.uninstall | method | Clear in-memory jobs, logs, schedules, and dedupe state |
| InMemoryQueries.has_table | method | Schema inspection; always returns True for in-memory adapter |
| InMemoryQueries.table_has_column | method | Schema inspection; always returns True for in-memory adapter |
| InMemoryQueries.table_has_index | method | Schema inspection; always returns True for in-memory adapter |
| InMemoryQueries.has_user_defined_enum | method | Schema inspection; always returns True for in-memory adapter |
| InMemoryQueries.has_function | method | Schema inspection; always returns True for in-memory adapter |
| InMemoryQueries.has_trigger | method | Schema inspection; always returns True for in-memory adapter |
| SchedulerManager | class | Run scheduled handlers against stored cron entries |
| Job | class | Public job record with id, entrypoint, payload, and status fields |
| JobId | type alias | Integer identifier for a queued or processed job |
| Context | class | Handler context exposing shared resources |
| Schedule | class | Scheduled job record passed to schedule handlers |
| ScheduleContext | class | Schedule handler context exposing shared resources |
| RetryRequested | exception | Signal a handler-initiated retry with delay and reason |
| QueueExecutionMode | enum | Select continuous or drain queue processing |

### CLI Entry Points

The package is imported as `pgqueuer`. `python -m pgqueuer` is not a supported interface for this scope, and no console command is required. Queue operations are used through the documented asynchronous Python API.

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. The in-memory adapter must operate without external databases, containers, or external services.

## Appendix B: Assessment Notes

The expected implementation focuses on public in-memory behavior: import surface, queue enqueue/dequeue ordering, state transitions, handler dispatch, context resource injection, retry and failure handling, dedupe release, cancellation, schedule registration/storage/dispatch, schema no-op behavior, and cross-view consistency among queue, log, status, statistics, and scheduler projections. Tests are behavioral and use only public imports and public object attributes. They do not require external databases, containers, CLI execution, hidden fixtures, internal dictionaries, exact repr strings, or exact exception message wording beyond the public `RetryRequested` default string.
