# RQ Specification

## Product Overview

RQ is a Python library for enqueueing function calls into Redis or Valkey and processing them later with worker processes. The package provides Python objects for producing work, observing job state, processing queues, inspecting registries and results, scheduling delayed work, retrying failed work, and controlling the same state through a command line program named `rq`.

RQ stores queue, job, worker, registry, scheduler, and result state in Redis-compatible storage. A producer process creates `Job` records through a `Queue`; a worker process consumes queued jobs, executes the referenced callable, and records the terminal state and result; monitoring code reads the same state through queue, registry, worker, result, and CLI views.

## Scope

This specification covers the core job lifecycle: queue creation, enqueueing, synchronous execution for tests, worker execution, job status transitions, dependencies, callbacks as stored job metadata, retry configuration, repeat configuration, concurrency rate limits, scheduled jobs, registries, results, manual cancellation and requeueing, worker commands, serializers, and CLI state commands.

This specification covers Redis/Valkey-backed behavior through the public Python API and the `rq` CLI. It describes observable contracts, not Redis key names or internal implementation sequences.

## Installable Surface

The package is installed and imported as `rq`. The console entry point is `rq`; compatibility entry points `rqinfo` and `rqworker` point to the info and worker commands.

The top-level `rq` package exports `Queue`, `Worker`, `SimpleWorker`, `SpawnWorker`, `Retry`, `Repeat`, `Callback`, `RateLimit`, `Webhook`, `cancel_job`, `requeue_job`, and `get_current_job`. Documented public modules also expose `rq.job.Job`, `rq.job.Dependency`, `rq.job.JobStatus`, `rq.registry` registry classes, `rq.results.Result`, `rq.group.Group`, `rq.command` worker command helpers, `rq.serializers.JSONSerializer`, `rq.decorators.job`, and `rq.worker.WorkerStatus`, `RoundRobinWorker`, and `RandomWorker`.

The default serializer is pickle. The serializer option accepts `pickle`, `json`, a serializer class such as `rq.serializers.JSONSerializer`, or a dotted import path to an object that provides `dumps` and `loads`.

## Public API

`Queue(name="default", connection=None, default_timeout=None, is_async=True, job_class=None, serializer=None, death_penalty_class=UnixSignalDeathPenalty, **kwargs)` represents a named Redis queue. It raises `TypeError` when no connection is provided. `Queue.all(connection, ...)` returns all known queues for a connection. `Queue.from_queue_key(queue_key, connection, ...)` returns a queue for a valid RQ queue key and raises `ValueError` for an invalid key.

`Queue.enqueue(f, *args, **kwargs)` and `Queue.enqueue_call(func, args=None, kwargs=None, timeout=None, result_ttl=None, ttl=None, failure_ttl=None, description=None, depends_on=None, job_id=None, at_front=False, meta=None, retry=None, repeat=None, on_success=None, on_failure=None, on_stopped=None, rate_limit=None, pipeline=None, unique=False, webhooks=None)` return a `Job`. RQ-specific keyword arguments are consumed by RQ; use `args=` and `kwargs=` when the target callable needs argument names that conflict with RQ option names.

`Queue.prepare_data(...)` returns an enqueue data object accepted by `Queue.enqueue_many(job_datas, pipeline=None, group_id=None)`. `Queue.enqueue_job(job, pipeline=None, at_front=False, unique=False)` persists and queues an existing `Job`. `Queue.enqueue_at(datetime, f, *args, **kwargs)` schedules a job for an absolute time, and `Queue.enqueue_in(time_delta, func, *args, **kwargs)` schedules a job after a delay.

`Queue.fetch_job(job_id)` returns the job from the queue's connection or `None` when no job exists. `Queue.get_job_ids(offset=0, length=-1)` returns queued job ids, `Queue.get_jobs(offset=0, length=-1)` returns queued `Job` objects, `queue.job_ids` and `queue.jobs` return the same full views, `len(queue)` and `queue.count` return queued job count, and `queue.get_job_position(job_or_id)` returns a zero-based queue position or `None` when the job is not queued.

`Queue.empty()` removes queued jobs from the queue. `Queue.delete(delete_jobs=True)` removes the queue; when `delete_jobs` is true it also deletes queued jobs. `Queue.remove(job_or_id, pipeline=None)` removes one queued job id from that queue.

`Job(id=None, connection=None, serializer=None)` represents job metadata and raises `TypeError` when no connection is provided. `Job.create(func, args=None, kwargs=None, connection=None, result_ttl=None, ttl=None, status=None, description=None, depends_on=None, timeout=None, retry=None, id=None, origin="", meta=None, failure_ttl=None, serializer=None, group_id=None, on_success=None, on_failure=None, on_stopped=None, webhooks=None)` returns an unsent job object. Custom job ids must contain only letters, numbers, underscores, and dashes.

`Job.fetch(id, connection=None, serializer=None)` returns a persisted job and raises `NoSuchJobError` when it is absent. `Job.fetch_many(job_ids, connection, serializer=None)` returns a list aligned with the input ids, using `None` for missing jobs. `Job.exists(job_id, connection)` returns whether a job key exists.

`Job.get_status(refresh=True)` returns a `JobStatus`; `Job.get_meta(refresh=True)` returns the job metadata dictionary; `Job.refresh()` reloads stored fields; `Job.save_meta()` persists `job.meta`. Job status values are `created`, `queued`, `started`, `finished`, `failed`, `deferred`, `scheduled`, `stopped`, `canceled`, `rate_limited`, and `ready_to_enqueue`. Boolean properties such as `is_queued`, `is_started`, `is_finished`, `is_failed`, `is_deferred`, `is_scheduled`, `is_canceled`, and `is_stopped` reflect the current status.

`Job.return_value(refresh=False)` returns the latest successful return value or `None` when there is no successful result. The `job.result` property returns the same delayed-result value for compatibility. `Job.latest_result(timeout=0)` returns the newest `Result` or `None` when no result is available before the timeout. `Job.results()` returns recorded execution results, newest first, up to RQ's retained result history. `Job.get_executions()` returns current execution records for a started job.

`Job.cancel(pipeline=None, enqueue_dependents=False, remove_from_dependencies=False)` marks the job canceled, removes it from its queue, and adds it to the canceled registry. `cancel_job(job_id, connection, serializer=None, enqueue_dependents=False)` performs the same operation after fetching by id. `Job.requeue(at_front=False)`, `requeue_job(job_id, connection, serializer=None)`, and `FailedJobRegistry.requeue(job_or_id, at_front=False)` return the requeued job.

`Dependency(jobs, allow_failure=False, enqueue_at_front=False)` describes one or more prerequisites. It raises `ValueError` when the list is empty or contains values other than job ids or `Job` objects. With `allow_failure=False`, the dependent job is queued only after all dependencies finish successfully. With `allow_failure=True`, dependency failure still permits enqueueing.

`Retry(max, interval=0, enqueue_at_front=False)` describes exception retry behavior. `max` is the number of retry attempts. `interval` is zero, a number of seconds, or a list of second intervals; a delayed interval requires a scheduler-enabled worker to become due. `Repeat(times, interval=0)` describes successful-repeat behavior and raises for `times < 1`.

`Callback(func, timeout=None)` wraps a success, failure, or stopped callback. Success callbacks receive `job`, `connection`, and `result`; failure callbacks receive `job`, `connection`, exception type, exception value, and traceback; stopped callbacks receive `job` and `connection`.

`RateLimit(key, concurrency)` groups jobs under a shared concurrency cap. `key` is the shared capacity name and `concurrency` is the maximum number of queued or executing jobs holding capacity for that key.

Registry classes are constructed as `Registry(name="default", connection=None, job_class=None, queue=None, serializer=None, death_penalty_class=None)`. `StartedJobRegistry`, `FinishedJobRegistry`, `FailedJobRegistry`, `DeferredJobRegistry`, `ScheduledJobRegistry`, and `CanceledJobRegistry` expose `count`, `get_job_ids(start=0, end=-1, desc=False, cleanup=True)`, containment by job or id, `remove(job, pipeline=None, delete_job=False)`, `get_queue()`, and where meaningful `requeue(job_or_id, at_front=False)`. `ScheduledJobRegistry.get_scheduled_time(job_or_id)` returns the scheduled datetime.

`Result` records one execution outcome. Public attributes include `type`, `created_at`, `return_value`, `exc_string`, `job_id`, `worker_name`, `execution_id`, `execution_started_at`, and `execution_ended_at`. Result types are `SUCCESSFUL`, `FAILED`, `STOPPED`, `RETRIED`, and `MAX_RETRIES_EXCEEDED`.

`Worker(queues, name=None, default_result_ttl=500, connection=None, exception_handlers=None, maintenance_interval=600, worker_ttl=None, job_class=None, queue_class=None, log_job_description=True, job_monitoring_interval=30, disable_default_exception_handler=False, prepare_for_work=True, serializer=None, work_horse_killed_handler=None)` consumes jobs. `Worker.work(burst=False, logging_level=None, date_format="%H:%M:%S", log_format="%(asctime)s %(message)s", max_jobs=None, max_idle_time=None, with_scheduler=False, dequeue_strategy="default")` starts the loop and returns a boolean completion result. `Worker.all(connection=None, queue=None, ...)` returns registered workers and `Worker.count(connection=None, queue=None)` returns their count. `SimpleWorker` runs jobs in the same process, `SpawnWorker` uses `os.spawn`, `RoundRobinWorker` rotates across queues, and `RandomWorker` selects queues randomly.

`send_shutdown_command(connection, worker_name)`, `send_kill_horse_command(connection, worker_name)`, and `send_stop_job_command(connection, job_id, serializer=None)` send Redis pubsub commands to workers. Stopping a running job moves it to failed state rather than applying normal retry behavior.

`Group.create(connection, name=None)`, `Group.fetch(name, connection)`, `Group.all(connection)`, `group.enqueue_many(queue, job_datas, pipeline=None)`, and `group.get_jobs()` provide a public grouping view for multiple jobs under one group id.

`get_current_job(connection=None, job_class=None)` returns the currently executing job inside a job function and returns `None` outside job execution.

## Product State Model

RQ has three public projections of the same state.

The producer projection is the Python API view: `Queue`, `Job`, `Registry`, `Result`, `Worker`, and `Group` objects bound to a Redis connection. Methods on these objects read and write persisted state and return Python objects representing the current view.

The worker projection is the execution view: workers register themselves, dequeue jobs, create execution records, update job status, write results, and move jobs among registries. A worker has states including suspended, started, busy, and idle.

The operator projection is the CLI view: `rq enqueue`, `rq worker`, `rq info`, `rq requeue`, `rq empty`, `rq suspend`, `rq resume`, and `rq cron` read or mutate the same Redis-backed queues, workers, and registries.

State written through one projection must be observable through the others on the same Redis database. A job enqueued through `Queue.enqueue()` must be visible to `rq info` and to a worker listening on that queue. A job executed by a worker must be visible through `Job.fetch()`, result accessors, and finished or failed registries. A job requeued through the CLI must be visible through the queue API as queued work.

## Queueing and Job Creation

A queue name identifies a FIFO list of ready jobs. The default queue name is `default`. Queue names are created on demand when jobs are enqueued.

`Queue.enqueue()` must create and persist a `Job`, store the callable reference and arguments, set `origin` to the queue name, apply job options, and return the job object. It must push the job id to the back of the queue when `at_front=False`; it must push the job id to the front when `at_front=True`. It must raise `ValueError` or `TypeError` when a custom job id is invalid.

The target callable must be a Python callable or an importable dotted string reference. A worker must import dotted string references at execution time. RQ-specific enqueue options must not be passed to the target callable; arguments supplied through `args=` and `kwargs=` must be passed to the target callable exactly as job arguments.

`Queue.enqueue_many()` must enqueue every prepared job data item using the same queue and return the created jobs. It must honor a provided Redis pipeline by staging writes into that pipeline and leaving execution of the pipeline to the caller.

When `unique=True`, enqueueing must require an explicit `job_id`. If a live unique job with that id already exists, enqueueing must raise `DuplicateJobError`; after the previous job is deleted, the same id is available again. Unique jobs with dependencies are unsupported and must raise an error rather than silently enqueueing.

When `Queue(is_async=False)` is used, `enqueue()` must execute the job immediately in the producer process, persist the same job/result state used by asynchronous execution, return a finished job on success, and record failed state on exception. It must still require a Redis-compatible connection because job state is stored there.

## Job Lifecycle and Results

A newly queued job must have status `queued` unless dependencies, scheduling, or rate limiting place it in `deferred`, `scheduled`, or `rate_limited`. A worker that starts the job must set status `started`, create an execution record, set `worker_name`, update heartbeat fields, and add the execution to `StartedJobRegistry`.

On successful execution, the worker must remove the execution from `StartedJobRegistry`, create a `Result` with type `SUCCESSFUL`, set job status `finished`, persist the return value, set end time, and add the job to `FinishedJobRegistry`. `job.return_value()` must return the latest successful return value; before any successful result exists it must return `None`.

On exception, the worker must record exception information, create a failed or retried result according to retry configuration, and either retry the job or move it to `FailedJobRegistry`. If no retry remains, job status must be `failed`, `job.exc_info` must contain the failure information, and `FailedJobRegistry` must contain the job id.

RQ stores up to 10 recent execution results for a job. `job.results()` must return the recorded history, `job.latest_result()` must return the newest result, and `job.latest_result(timeout=N)` must wait up to `N` seconds for a result before returning `None`.

`result_ttl` controls how long successful job and result data remain. The default is 500 seconds. A `result_ttl` of `0` must expire successful result data immediately; a value of `-1` must keep successful result data until explicit deletion. `failure_ttl` controls failed job retention and defaults to one year.

## Dependencies, Cancellation, and Requeueing

A job with dependencies must enter the deferred state and `DeferredJobRegistry` rather than the ready queue. When all dependencies satisfy the dependency policy, the dependent job must move to a ready queue. With `Dependency(..., enqueue_at_front=True)`, the dependent job must enter the front of its queue when it becomes ready.

Canceling a job must set status `canceled`, remove it from its ready queue when queued, put it in `CanceledJobRegistry`, and leave the job record available for inspection until normal cleanup or deletion. Canceling must not delete the job unless the caller explicitly deletes it. If `enqueue_dependents=True`, canceling must enqueue eligible dependents according to the dependency policy.

Requeueing a failed job must remove it from `FailedJobRegistry`, put it back on its origin queue, set it to queued state, and return the job. Requeueing a missing job must raise `NoSuchJobError`. Requeueing a job that is not in a requeueable state must raise an invalid-operation exception.

Deleting a job must remove the job record and remove it from its queue and registries. With `delete_dependents=True`, deletion must also delete dependent jobs.

## Scheduling, Repeating, Retries, and Rate Limits

`Queue.enqueue_at()` must accept a `datetime` and create a scheduled job. A naive datetime must be treated as local time. `Queue.enqueue_in()` must accept a `timedelta`. Scheduled jobs must not appear in the ready queue before they are due; they must appear in `ScheduledJobRegistry` and have status `scheduled`.

A worker started with scheduler support must enqueue due scheduled jobs. Only one active scheduler must work for a given queue at a time. Idle scheduler-capable workers must be able to take over scheduling for a queue when no active scheduler remains.

`Repeat(times, interval)` must repeat a job only after successful executions. Failed jobs must not be repeated by repeat configuration. If the interval list is shorter than the number of repeats, the last interval in the list must be reused for remaining repeats. `job.repeats_left` and `job.repeat_intervals` must expose the remaining count and configured intervals.

`Retry(max, interval)` passed at enqueue time must retry failed attempts caused by exceptions. With `interval=0`, the retry must be queued immediately. With a positive interval or list of intervals, the retry must be scheduled and requires scheduler processing before another attempt runs. When retry attempts are exhausted, RQ must store a terminal failed outcome.

Returning a `Retry` object from a job function must request retry of that execution result. This return-based retry count is separate from the exception-retry configuration passed to enqueueing.

`RateLimit(key, concurrency)` must allow only `concurrency` jobs sharing the key to be queued or executing in the same Redis database. Jobs beyond capacity must have status `rate_limited`, must not appear in normal queue counts, and must become queued when capacity is released. Completion, failure, cancellation, and deletion must release capacity and admit the next waiting job.

## Workers and Worker Commands

A worker must process one job at a time. With multiple queue names under the default dequeue strategy, the worker must consult queues in the supplied order and take work from the first non-empty queue. `RoundRobinWorker` must rotate across queues, and `RandomWorker` must select among queues randomly.

`Worker.work(burst=True)` must process currently available work and return after the queues are empty. Without burst mode, a worker must wait for new work until stopped, `max_jobs` is reached, or `max_idle_time` expires. A worker must register birth before processing and register death when it exits gracefully.

The default `Worker` must execute jobs in a separate work-horse process on platforms that support fork. `SimpleWorker` must execute jobs in the same process and must not provide periodic heartbeats during long job execution. `SpawnWorker` must use spawn-based child execution for platforms where fork is not available.

Workers must update observable runtime fields including name, hostname, process id, queues, state, last heartbeat, birth date, successful job count, failed job count, current execution count, and total working time. `Worker.all()` and `Worker.count()` must return those registered worker views from Redis.

`send_shutdown_command()` must ask the named worker to shut down gracefully. `send_kill_horse_command()` must ask a busy worker to terminate its current work-horse and must be ignored by an idle worker. `send_stop_job_command()` must target a currently executing job and must raise an exception when the job id is invalid or not currently executing.

Custom exception handlers must receive `(job, exc_type, exc_value, traceback)`. A handler returning `False` must stop the handler chain. A handler returning `True` or `None` must allow the next handler to run. When the default exception handler is disabled, RQ must not run its built-in failed-job handler after custom handlers.

## Registries, Groups, and Monitoring Views

Every queue must expose `started_job_registry`, `deferred_job_registry`, `finished_job_registry`, `failed_job_registry`, `scheduled_job_registry`, and `canceled_job_registry`. Registry membership must accept both `Job` objects and job id strings.

`StartedJobRegistry` must contain currently executing jobs and must remove them when execution ends. `FinishedJobRegistry` must contain successful jobs. `FailedJobRegistry` must contain jobs that ended unsuccessfully and are not awaiting retry. `DeferredJobRegistry` must contain jobs waiting for dependencies. `ScheduledJobRegistry` must contain delayed jobs. `CanceledJobRegistry` must contain canceled jobs.

`registry.remove(job_id, delete_job=False)` must remove the job id from the registry. When `delete_job=True`, it must also delete the job record. Removing an absent id must not create a job or add it to any other view.

A `Group` must track a set of jobs under one group id. `group.enqueue_many()` must enqueue all provided job data through the supplied queue and attach them to the group. `group.get_jobs()` must return the group's live jobs. When all group jobs expire or are deleted, the group must be removable from Redis cleanup.

`rq info` must report queue and worker state from the same Redis database used by the Python API. Its queue counts must count ready queued jobs, not deferred, scheduled, or rate-limited jobs.

## CLI Behavior

`rq enqueue FUNCTION [ARGUMENTS]` must enqueue a dotted function reference or importable Python file target. Argument tokens without markers are strings; `key=value` passes string keyword arguments; `:value` and `key:=value` parse JSON; `%value` and `key%=value` parse Python literals; values beginning with `@` read from a file path. Invalid parsing or import failures must produce a non-zero command exit.

`rq worker [QUEUES]...` must start a worker for the supplied queues or for the configured queues. It must accept options for burst mode, Redis URL, import path, config module, serializer, worker class, job class, queue class, scheduler support, dequeue strategy, max jobs, max idle time, and logging.

`rq info [QUEUES]...` must print queue and worker information and exit by default. With `--interval`, it must refresh repeatedly at the requested second interval. `--only-queues`, `--only-workers`, `--by-queue`, and `--raw` must change only the displayed view, not stored state.

`rq requeue --queue QUEUE JOB_IDS...` must requeue the listed failed jobs from the named queue's failed registry. With `--all`, it must requeue all failed jobs for that queue. Missing required queue or job selection must exit with usage error.

`rq empty [QUEUES]...` must empty the supplied queues. With `--all`, it must empty all known queues in the selected Redis database. `rq suspend` must prevent workers on the selected Redis database from picking up new jobs while letting already running jobs continue. `rq suspend --duration SECONDS` must expire the suspension after that duration. `rq resume` must clear suspension.

`rq cron CONFIG_PATH` must load a Python file or module path defining cron jobs and start the cron scheduler. This specification covers invocation and interaction with Redis state; it does not define cron registration internals.

## Error Semantics

`Queue(...)` and `Job(...)` must raise `TypeError` when no Redis-compatible connection is provided.

`Job.fetch()` must raise `NoSuchJobError` when the job id does not exist. `Queue.fetch_job()` must return `None` for an absent job id.

Custom job ids must raise `TypeError` when the id is not a string and `ValueError` when it contains characters other than letters, numbers, underscores, and dashes.

`Dependency(...)` must raise `ValueError` when given an empty dependency list or unsupported dependency values.

`unique=True` must raise `DuplicateJobError` when the same live job id is already reserved by another unique job.

`send_stop_job_command()` must raise an exception when the job id is invalid or not currently executing.

Invalid timeout formats must raise `TimeoutFormatError` where timeout parsing is exposed. Missing groups must raise `NoSuchGroupError`. Missing schedulers must raise `SchedulerNotFound`. Duplicate scheduler registration must raise `DuplicateSchedulerError`.

CLI help must exit with status `0`. Invalid commands, missing required arguments, and usage errors must exit with status `2`. Runtime failures such as import, Redis connection, or job operation errors must exit non-zero and must not report success.

## Cross-View Invariants

1. A job returned by `Queue.enqueue()` must be fetchable through `Job.fetch(job.id, connection=queue.connection)`.
2. A ready job id returned by `queue.get_job_ids()` must correspond to a `Job` returned by `queue.get_jobs()` at the same position.
3. A job pushed with `at_front=True` must appear before earlier queued jobs in the queue API and must be the next job selected by a default worker for that queue.
4. A scheduled job returned by `enqueue_in()` or `enqueue_at()` must return `False` for ready queue membership and must return `True` for `job in ScheduledJobRegistry(queue=queue)` until it becomes due.
5. A job being executed by a worker must have status `started`, must appear in `StartedJobRegistry`, and must appear in the worker's current execution view.
6. A successful worker execution must remove the job from `StartedJobRegistry`, must add it to `FinishedJobRegistry`, and must make the return value visible through `job.return_value()`.
7. A failed terminal execution must remove the job from `StartedJobRegistry`, must add it to `FailedJobRegistry`, and must make exception information visible through `job.exc_info`.
8. A canceled job must have status `canceled`, must be absent from the ready queue, and must be present in `CanceledJobRegistry`.
9. A failed job requeued through `registry.requeue()`, `Job.requeue()`, `requeue_job()`, or `rq requeue` must become visible as a queued job on its origin queue and must leave `FailedJobRegistry`.
10. `rq info` queue counts must match `len(Queue(name, connection=same_connection))` for ready jobs in the same Redis database.
11. A worker listed by `Worker.all(connection)` must be represented in the worker portion of `rq info` for the same Redis database.
12. A serializer used by a producer queue must also be used by workers reading those jobs; mismatched serializers must fail deserialization rather than silently returning incorrect arguments.

## Representative Workflows

Basic asynchronous processing:

```python
from redis import Redis
from rq import Queue, Worker
connection = Redis()
queue = Queue("default", connection=connection)
job = queue.enqueue("myapp.tasks.add", 2, 5, job_id="add_2_5")
worker = Worker([queue], connection=connection)
worker.work(burst=True)
job.refresh()
assert job.is_finished
assert job.return_value() == 7
```

Scheduled retry workflow:

```python
from datetime import timedelta
from redis import Redis
from rq import Queue, Retry, Worker
from rq.registry import ScheduledJobRegistry
connection = Redis()
queue = Queue(connection=connection)
job = queue.enqueue_in(timedelta(seconds=30), "myapp.tasks.unstable_task",
                       retry=Retry(max=3, interval=[10, 30, 60]))
assert job in ScheduledJobRegistry(queue=queue)
Worker([queue], connection=connection).work(burst=True, with_scheduler=True)
```

Failure inspection and requeue workflow:

```python
from redis import Redis
from rq import Queue
from rq.job import Job
connection = Redis()
queue = Queue("reports", connection=connection)
registry = queue.failed_job_registry
for job_id in registry.get_job_ids():
    job = Job.fetch(job_id, connection=connection)
    print(job.exc_info)
    registry.requeue(job_id, at_front=True)
```

## Non-Goals

This specification does not define private module helpers, private Redis key layouts, Lua script bodies, internal maintenance algorithms, or process supervision.

This specification does not define external webhook HTTP delivery, response payload exact fields, or retry behavior for webhook network failures.

This specification does not define worker-pool orchestration, subprocess count management, process manager integration, Sentry integration, or dashboard integrations.

This specification does not require compatibility with Redis connections using `decode_responses=True`.

This specification does not define cron registration internals beyond the `rq cron CONFIG_PATH` invocation and its use of the same Redis-backed job state.

## Invocation Protocol

The supported console command is `rq`. `rqinfo` and `rqworker` are compatibility entry points. `python -m rq` is not supported because the package has no module entry point. `python -m rq.cli` is supported and exposes the same command group as `rq`.

Exit codes:

| Invocation outcome | Exit code |
| --- | --- |
| `--help` or `--version` succeeds | 0 |
| A command completes successfully | 0 |
| Invalid command or invalid CLI usage | 2 |
| Redis connection failure, import failure, or job operation failure | non-zero |

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

RQ requires a Redis-compatible server: Redis 5 or newer, or Valkey 7.2 or newer. Tests and local development are allowed to use a Redis-compatible fake only when it preserves the public behavior described here.

## Evaluation Notes

Assessment focuses on public behavior through the documented Python imports and the `rq` command line program. Checks exercise queue/job lifecycle behavior, worker-visible state transitions, result records, registries, retry and scheduling behavior, cancellation and requeueing, serializer selection, rate-limit admission, CLI state commands, and cross-view consistency between Python objects and command output.

Private helpers, private module organization, exact Redis key names, internal script contents, and unsupported carrier details are not assessed. Passing behavior requires durable observable state and correct errors, not matching a particular internal implementation.
