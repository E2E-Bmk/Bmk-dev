# RQ Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

RQ is a Python library for enqueueing callable work into Redis-compatible storage and executing it later with worker processes. Producers create durable `Job` records through named `Queue` objects; workers dequeue ready jobs, run the referenced callable, and persist terminal status, results, and registry membership; operators and monitoring code observe the same state through queue views, registries, worker listings, result history, and the `rq` command-line program.

The library stores queue membership, job metadata, worker registration, scheduler state, dependency links, retry and repeat configuration, rate-limit admission, and execution results in a Redis-compatible database. Public Python objects expose that state through methods and properties; workers mutate it during execution; CLI commands read and update the same database for operational tasks.

## Non-Goals

- This specification does not require private helper modules, private Redis key layouts, Lua script bodies, or internal maintenance algorithms.
- This specification does not require exact log message text, warning wording, or rich/text representation formatting.
- This specification does not require external webhook HTTP delivery semantics, webhook payload fields, or webhook network retry behavior.
- This specification does not require worker-pool orchestration, process-manager integration, dashboard integrations, or third-party error-reporting integrations.
- This specification does not require compatibility with Redis connections configured with `decode_responses=True`.
- This specification does not require cron registration internals beyond the `rq cron CONFIG_PATH` invocation and its use of the same Redis-backed job state.
- This specification does not require rate-limit or unique-job reservation behavior when the backing store lacks Redis Lua script support `(non-testable)` on non-Lua fakes.

## Representative Workflows

### Asynchronous enqueue and burst execution

```python
from redis import Redis
from rq import Queue, SimpleWorker

connection = Redis()
queue = Queue("compute", connection=connection)
job = queue.enqueue("builtins.str", "payload", job_id="str-payload")
SimpleWorker([queue], connection=connection).work(burst=True)
job.refresh()
assert job.is_finished
assert job.return_value() == "payload"
```

A producer enqueues work onto a named queue. A worker running in burst mode drains available jobs, persists the same finished state used by long-running workers, and makes the return value visible through the job API.

### Scheduled work with registry inspection

```python
from datetime import timedelta
from redis import Redis
from rq import Queue
from rq.registry import ScheduledJobRegistry

connection = Redis()
queue = Queue(connection=connection)
job = queue.enqueue_in(timedelta(minutes=15), "builtins.str", "later", job_id="later-job")
assert job.get_status().value == "scheduled"
assert job.id not in queue.get_job_ids()
assert job in ScheduledJobRegistry(queue=queue)
```

Delayed enqueueing must keep the job out of the ready queue until it is due while exposing scheduled membership through the scheduled registry.

### Failure inspection and requeue

```python
from redis import Redis
from rq import Queue
from rq.job import Job

connection = Redis()
queue = Queue("reports", connection=connection)
registry = queue.failed_job_registry
for job_id in registry.get_job_ids():
    job = Job.fetch(job_id, connection=connection)
    print(job.latest_result().exc_string)
    registry.requeue(job_id, at_front=True)
```

Failed jobs must remain inspectable through job and result views and must return to the ready queue when requeued from the failed registry.

## Queue and Job Production

`Queue(name="default", connection=None, ...)` represents one named FIFO list of ready job ids backed by a Redis-compatible connection. It must raise `TypeError` when no connection is provided. The default queue name is `default`. Queue names are created on first use.

**Ready-queue views.** `len(queue)` and `queue.count` must report the number of ready queued jobs. `queue.get_job_ids(offset=0, length=-1)` must return queued ids in order. `queue.get_jobs(offset=0, length=-1)` and `queue.jobs` must return the corresponding `Job` objects in the same order. `queue.get_job_position(job_or_id)` must return a zero-based ready-queue index or `None` when the job is not queued. `queue.fetch_job(job_id)` must return the persisted job or `None` when absent. `Queue.all(connection, ...)` must list known queues for the connection.

**Enqueueing.** `Queue.enqueue(f, *args, **kwargs)` and `Queue.enqueue_call(func, args=None, kwargs=None, timeout=None, result_ttl=None, ttl=None, failure_ttl=None, description=None, depends_on=None, job_id=None, at_front=False, meta=None, retry=None, repeat=None, on_success=None, on_failure=None, on_stopped=None, rate_limit=None, pipeline=None, unique=False, webhooks=None)` must create and persist a `Job`, store the callable reference and arguments, set `origin` to the queue name, apply job options, and return the job. RQ-specific keyword arguments must not be forwarded to the target callable; use `args=` and `kwargs=` for callable arguments whose names conflict with RQ options.

When `at_front=False`, enqueueing must append the job id to the ready queue. When `at_front=True`, enqueueing must prepend the job id. Invalid custom job ids must raise `TypeError` when the id is not a string and `ValueError` when it contains characters other than letters, digits, underscores, and dashes.

The target callable must be a Python callable or an importable dotted string. Workers must import dotted references at execution time.

**Batch and prepared enqueueing.** `Queue.prepare_data(...)` must return enqueue data accepted by `Queue.enqueue_many(job_datas, pipeline=None, group_id=None)`. `Queue.enqueue_many()` must enqueue every prepared item on the same queue and return the created jobs in order. When a Redis pipeline is supplied, enqueueing must stage writes into that pipeline and leave pipeline execution to the caller. `Queue.enqueue_job(job, pipeline=None, at_front=False, unique=False)` must persist and queue an existing job object.

**Scheduling enqueue helpers.** `Queue.enqueue_at(datetime, f, *args, **kwargs)` must schedule a job for an absolute time. Naive datetimes must be treated as local time. `Queue.enqueue_in(time_delta, func, *args, **kwargs)` must schedule a job after a relative delay.

**Queue mutation.** `Queue.empty()` must remove ready queued jobs from the queue list. `Queue.delete(delete_jobs=True)` must remove the queue and, when `delete_jobs=True`, delete queued jobs as well. `Queue.remove(job_or_id, pipeline=None)` must remove one ready queued job id.

**Synchronous mode.** When `Queue(is_async=False)` is used, `enqueue()` must execute the job immediately in the producer process, persist the same job and result state used by asynchronous execution, return a finished job on success, and record failed state on exception. Synchronous mode still requires a Redis-compatible connection because job state is stored there.

**Unique jobs.** When `unique=True`, enqueueing must require an explicit `job_id`. If a live unique job with that id already exists, enqueueing must raise `DuplicateJobError`. After the previous job is deleted, the same id becomes available again. Unique jobs with dependencies are unsupported and must raise an error rather than silently enqueueing `(non-testable)` without Lua support.

## Job Lifecycle, Results, and Registries

`Job(id=None, connection=None, serializer=None)` represents persisted job metadata and must raise `TypeError` when no connection is provided. `Job.create(...)` returns an unsent job object. `Job.fetch(id, connection=None, serializer=None)` returns a persisted job and raises `NoSuchJobError` when absent. `Job.fetch_many(job_ids, connection, serializer=None)` returns a list aligned with the input ids, using `None` for missing jobs. `Job.exists(job_id, connection)` reports whether a job key exists.

**Status and metadata.** `Job.get_status(refresh=True)` returns a `JobStatus`. `Job.get_meta(refresh=True)` returns the metadata dictionary. `Job.refresh()` reloads stored fields. `Job.save_meta()` persists `job.meta`. Status values include `created`, `queued`, `started`, `finished`, `failed`, `deferred`, `scheduled`, `stopped`, `canceled`, `rate_limited`, and `ready_to_enqueue`. Boolean properties such as `is_queued`, `is_started`, `is_finished`, `is_failed`, `is_deferred`, `is_scheduled`, `is_canceled`, and `is_stopped` reflect the current status.

**Results and return values.** `Job.return_value(refresh=False)` returns the latest successful return value or `None` before any successful execution. `Job.latest_result(timeout=0)` returns the newest `Result` or `None` when no result is available before the timeout. `Job.results()` returns recorded execution results, newest first, up to the retained result history. `Job.get_executions()` returns current execution records for a started job. `Result` exposes `type`, `created_at`, `return_value`, `exc_string`, `job_id`, `worker_name`, `execution_id`, `execution_started_at`, and `execution_ended_at`. Result types include `SUCCESSFUL`, `FAILED`, `STOPPED`, `RETRIED`, and `MAX_RETRIES_EXCEEDED`.

**Lifecycle transitions.** A newly queued job must have status `queued` unless dependencies, scheduling, or rate limiting place it in `deferred`, `scheduled`, or `rate_limited`. A worker that starts the job must set status `started`, create an execution record, set `worker_name`, update heartbeat fields, and add the execution to `StartedJobRegistry`.

On successful execution, the worker must remove the job from `StartedJobRegistry`, create a `Result` with type `SUCCESSFUL`, set status `finished`, persist the return value, set end time, and add the job to `FinishedJobRegistry`. On exception, the worker must record exception information, create a failed or retried result according to retry configuration, and either retry the job or move it to `FailedJobRegistry`. When no retry remains, status must be `failed` and failure information must be visible through `latest_result()` and historical `results()`.

**Retention.** `result_ttl` controls successful job and result retention; default is 500 seconds. `result_ttl=0` expires successful result data immediately; `result_ttl=-1` keeps successful result data until explicit deletion. `failure_ttl` controls failed job retention and defaults to one year.

**Cancellation and deletion.** `Job.cancel(pipeline=None, enqueue_dependents=False, remove_from_dependencies=False)` and `cancel_job(job_id, connection, serializer=None, enqueue_dependents=False)` must set status `canceled`, remove the job from its ready queue when queued, add it to `CanceledJobRegistry`, and leave the job record available for inspection until normal cleanup or deletion. `Job.delete(delete_dependents=False)` must remove the job record and remove it from its queue and registries.

**Requeueing.** `Job.requeue(at_front=False)`, `requeue_job(job_id, connection, serializer=None)`, and `FailedJobRegistry.requeue(job_or_id, at_front=False)` must move a failed job back to its origin queue with queued status. Requeueing a missing job must raise `NoSuchJobError`. Requeueing a job that is not in a requeueable state must raise an invalid-operation exception.

Every queue must expose `started_job_registry`, `deferred_job_registry`, `finished_job_registry`, `failed_job_registry`, `scheduled_job_registry`, and `canceled_job_registry`. Registry membership checks must accept both `Job` objects and job id strings. `ScheduledJobRegistry.get_scheduled_time(job_or_id)` returns the scheduled datetime. `registry.remove(job, pipeline=None, delete_job=False)` removes the job id from the registry; when `delete_job=True`, it also deletes the job record. Removing an absent id must not create a job or add it to any other view.

## Dependencies, Scheduling, Retries, and Rate Limits

`Dependency(jobs, allow_failure=False, enqueue_at_front=False)` describes one or more prerequisites. It must raise `ValueError` when the list is empty or contains unsupported values. With `allow_failure=False`, the dependent job is queued only after all dependencies finish successfully. With `allow_failure=True`, dependency failure still permits enqueueing. With `enqueue_at_front=True`, the dependent job must enter the front of its queue when it becomes ready.

A job with unsatisfied dependencies must enter `deferred` status and `DeferredJobRegistry` rather than the ready queue. When dependencies satisfy the policy, the dependent job must move to a ready queue.

**Scheduling.** Scheduled jobs must not appear in the ready queue before they are due; they must appear in `ScheduledJobRegistry` with status `scheduled`. A worker started with scheduler support must enqueue due scheduled jobs. Only one active scheduler must work for a given queue at a time.

**Repeat.** `Repeat(times, interval=0)` describes successful-repeat behavior and must raise for `times < 1`. Repeat must run only after successful executions; failed jobs must not be repeated by repeat configuration. If the interval list is shorter than the number of repeats, the last interval must be reused. `job.repeats_left` and `job.repeat_intervals` expose the remaining count and configured intervals.

**Retry.** `Retry(max, interval=0, enqueue_at_front=False)` describes exception retry behavior. `max` is the number of retry attempts. `interval` is zero, a number of seconds, or a list of second intervals; delayed intervals require scheduler processing before another attempt runs. When retry attempts are exhausted, RQ must store a terminal failed outcome. Returning a `Retry` object from a job function requests retry of that execution result; this return-based retry count is separate from enqueue-time exception retry configuration.

**Rate limits.** `RateLimit(key, concurrency)` groups jobs under a shared concurrency cap. `key` must be non-empty; `concurrency` must be at least 1. Only `concurrency` jobs sharing the key may be queued or executing in the same Redis database. Jobs beyond capacity must have status `rate_limited`, must not appear in normal ready queue counts, and must become queued when capacity is released. Completion, failure, cancellation, and deletion must release capacity and admit the next waiting job `(non-testable)` without Lua support.

## Workers, Groups, Serializers, and Commands

`Worker(queues, name=None, connection=None, ...)` consumes jobs from one or more queues. `Worker.work(burst=False, max_jobs=None, max_idle_time=None, with_scheduler=False, dequeue_strategy="default", ...)` starts the processing loop and returns a boolean completion result. With the default dequeue strategy and multiple queues, the worker must consult queues in supplied order and take work from the first non-empty queue. `RoundRobinWorker` rotates across queues; `RandomWorker` selects queues randomly. `SimpleWorker` executes jobs in the same process; the default `Worker` executes jobs in a separate work-horse process where supported; `SpawnWorker` uses spawn-based child execution.

Burst mode must process currently available work and return after queues are empty. A worker must register birth before processing and register death when it exits gracefully. `Worker.all(connection=None, queue=None, ...)` and `Worker.count(connection=None, queue=None)` return registered worker views from Redis.

`send_shutdown_command(connection, worker_name)` asks the named worker to shut down gracefully. `send_kill_horse_command(connection, worker_name)` asks a busy worker to terminate its current work-horse and is ignored by an idle worker. `send_stop_job_command(connection, job_id, serializer=None)` targets a currently executing job and must raise an exception when the job id is invalid or not currently executing.

`get_current_job(connection=None, job_class=None)` returns the currently executing job inside a job function and `None` outside job execution.

**Groups.** `Group.create(connection, name=None)`, `Group.fetch(name, connection)`, `Group.all(connection)`, `group.enqueue_many(queue, job_datas, pipeline=None)`, and `group.get_jobs()` track multiple jobs under one group id. Missing groups must raise `NoSuchGroupError`.

**Serializers.** The default serializer is pickle. The serializer option accepts `pickle`, `json`, a serializer class such as `rq.serializers.JSONSerializer`, or a dotted import path to an object providing `dumps` and `loads`. A serializer used by a producer queue must also be used by workers reading those jobs; mismatched serializers must fail deserialization rather than silently returning incorrect arguments.

**CLI.** The supported console command is `rq`; compatibility entry points `rqinfo` and `rqworker` point to info and worker commands. `python -m rq.cli` exposes the same command group.

`rq enqueue FUNCTION [ARGUMENTS]` enqueues a dotted function reference or importable Python file target. `rq worker [QUEUES]...` starts a worker. `rq info [QUEUES]...` prints queue and worker information; `--only-queues`, `--only-workers`, `--by-queue`, and `--raw` change only the displayed view. `rq requeue --queue QUEUE JOB_IDS...` requeues failed jobs from the named queue's failed registry. `rq empty [QUEUES]...` empties supplied queues. `rq suspend` prevents workers on the selected database from picking up new jobs while running jobs continue; `rq resume` clears suspension. `rq cron CONFIG_PATH` loads a cron configuration and starts the cron scheduler.

CLI help and version requests must exit with status `0`. Invalid commands and usage errors must exit with status `2`. Runtime failures such as import, Redis connection, or job operation errors must exit non-zero.

## State Model

RQ maintains durable job, queue, registry, worker, scheduler, group, and rate-limit state in a Redis-compatible database.

The public projections are:

1. **Producer projection** — `Queue`, `Job`, registry objects, `Result`, `Worker`, and `Group` methods and properties bound to a connection.
2. **Worker projection** — worker registration, dequeue order, execution records, status transitions, and result writes during processing.
3. **Operator projection** — CLI commands that read or mutate the same queues, workers, and registries.

State written through one projection must be observable through the others on the same Redis database. A job enqueued through `Queue.enqueue()` must be visible to `rq info` and to a worker listening on that queue. A job executed by a worker must be visible through `Job.fetch()`, result accessors, and finished or failed registries. A job requeued through the CLI must be visible through the queue API as queued work.

## Error Semantics

| Condition | Required result |
| --- | --- |
| `Queue(...)` or `Job(...)` without a connection | Raise `TypeError` |
| `Job.fetch()` for a missing job id | Raise `NoSuchJobError` |
| `Queue.fetch_job()` for a missing job id | Return `None` |
| Custom job id is not a string | Raise `TypeError` |
| Custom job id contains invalid characters | Raise `ValueError` |
| `Dependency(...)` with empty or unsupported values | Raise `ValueError` |
| `Repeat(times < 1)` | Raise `ValueError` |
| `RateLimit("", concurrency)` or empty key | Raise `ValueError` |
| `RateLimit(key, concurrency < 1)` | Raise `ValueError` |
| `unique=True` with an already reserved live job id | Raise `DuplicateJobError` |
| `send_stop_job_command()` for a non-executing job id | Raise `InvalidJobOperation` |
| `Group.fetch()` for a missing group | Raise `NoSuchGroupError` |
| Requeueing a missing job | Raise `NoSuchJobError` |
| Requeueing a non-failed job | Raise `InvalidJobOperation` |
| CLI help or version succeeds | Exit code `0` |
| Invalid CLI command or usage | Exit code `2` |

Only exception types are specified; message text is not part of the contract.

## Cross-View Invariants

1. A job returned by `Queue.enqueue()` must be fetchable through `Job.fetch(job.id, connection=queue.connection)`.
2. A ready job id returned by `queue.get_job_ids()` must correspond to a `Job` returned by `queue.get_jobs()` at the same position.
3. A job enqueued with `at_front=True` must appear before earlier queued jobs in the queue API and must be the next job selected by a default worker for that queue.
4. A scheduled job returned by `enqueue_in()` or `enqueue_at()` must be absent from the ready queue and present in `ScheduledJobRegistry` until it becomes due.
5. A job being executed by a worker must have status `started` and must appear in `StartedJobRegistry`.
6. A successful worker execution must remove the job from `StartedJobRegistry`, add it to `FinishedJobRegistry`, and make the return value visible through `job.return_value()`.
7. A failed terminal execution must remove the job from `StartedJobRegistry`, add it to `FailedJobRegistry`, and make failure information visible through `job.latest_result()`.
8. A canceled job must have status `canceled`, must be absent from the ready queue, and must be present in `CanceledJobRegistry`.
9. A failed job requeued through `FailedJobRegistry.requeue()`, `Job.requeue()`, `requeue_job()`, or `rq requeue` must become visible as a queued job on its origin queue and must leave `FailedJobRegistry`.
10. The `rq` operator CLI and `python -m rq.cli` must expose the same command group (including `info`, `worker`, and `enqueue`); help and version requests must exit `0` and unknown commands must exit `2`, so operators drive the same job and queue operations exposed to Python callers.
11. A worker processing jobs must be discoverable through `Worker.all(connection)` and `Worker.count(connection)` while it runs and must deregister from those views after a graceful burst exit.
12. A serializer used by a producer queue must also be used by workers reading those jobs; mismatched serializers must fail deserialization rather than silently returning incorrect arguments.

## Public Interface

### Import Surface

The package is installed and imported as `rq`.

```python
import rq
from rq import (
    Queue,
    Worker,
    SimpleWorker,
    SpawnWorker,
    Retry,
    Repeat,
    Callback,
    RateLimit,
    Webhook,
    cancel_job,
    requeue_job,
    get_current_job,
)
from rq.job import Job, Dependency, JobStatus
from rq.registry import (
    StartedJobRegistry,
    FinishedJobRegistry,
    FailedJobRegistry,
    DeferredJobRegistry,
    ScheduledJobRegistry,
    CanceledJobRegistry,
)
from rq.results import Result
from rq.group import Group
from rq.serializers import JSONSerializer
from rq.command import (
    send_shutdown_command,
    send_kill_horse_command,
    send_stop_job_command,
)
from rq.worker import RoundRobinWorker, RandomWorker, WorkerStatus
from rq.decorators import job
```

Compatibility console entry points: `rq`, `rqinfo`, `rqworker`. Supported module invocation: `python -m rq.cli`.

### API Catalog

| Name | Kind | Role |
| --- | --- | --- |
| Queue | class | Named Redis-backed work queue |
| Worker | class | Default multi-process job consumer |
| SimpleWorker | class | In-process job consumer for tests |
| SpawnWorker | class | Spawn-based job consumer |
| RoundRobinWorker | class | Worker that rotates queue priority |
| RandomWorker | class | Worker that chooses queues randomly |
| Job | class | Durable job record and status view |
| Dependency | class | Prerequisite jobs for deferred enqueueing |
| Retry | class | Exception retry configuration |
| Repeat | class | Successful-repeat configuration |
| Callback | class | Success, failure, or stopped callback wrapper |
| RateLimit | class | Shared concurrency cap for jobs |
| Webhook | class | Webhook metadata attached to jobs |
| Group | class | Batch grouping view over multiple jobs |
| Result | class | One execution outcome record |
| JobStatus | enum | Named job status values |
| WorkerStatus | enum | Named worker state values |
| JSONSerializer | class | JSON serializer for job payloads |
| StartedJobRegistry | class | Registry of executing jobs |
| FinishedJobRegistry | class | Registry of successful jobs |
| FailedJobRegistry | class | Registry of terminal failed jobs |
| DeferredJobRegistry | class | Registry of dependency-blocked jobs |
| ScheduledJobRegistry | class | Registry of delayed jobs |
| CanceledJobRegistry | class | Registry of canceled jobs |
| cancel_job | function | Cancel a job by id |
| requeue_job | function | Requeue a failed job by id |
| get_current_job | function | Return the executing job inside worker context |
| send_shutdown_command | function | Request graceful worker shutdown |
| send_kill_horse_command | function | Terminate a worker's active work-horse |
| send_stop_job_command | function | Stop a currently executing job |
| job | decorator | Declare a function as an RQ job |

There is no supported `python -m rq` entry point.

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable: `redis`, `click`, `croniter`, `pytest`, and optionally `fakeredis` for local development.

The project must declare its packaging metadata in a standard `pyproject.toml` (or `setup.py`) at the project root so the package can be installed with pip.

RQ requires a Redis-compatible server: Redis 5 or newer, or Valkey 7.2 or newer. Assessment provides Redis with Lua script support. Local development may use a Redis-compatible fake for workflows that do not depend on Lua; rate-limit admission and unique-job reservation require real Redis Lua support.

## Appendix B: Assessment Notes

Implementations are exercised through public Python imports and the `rq` CLI. Checks cover queue and job production, worker-driven lifecycle transitions, result history, registry membership, dependencies, scheduling, retries, cancellation, requeueing, serializer consistency, worker registration, CLI state commands, and cross-view consistency between Python objects and CLI output.

Assessment focuses on observable public behavior, not private module layout, exact Redis key names, internal script bodies, or exact textual representations. Passing requires durable state, correct registry membership, and specified error types—not a particular internal implementation strategy.
