# APScheduler Specification

## Product Overview

APScheduler is an in-process Python scheduler and job queue. It lets applications define tasks, create schedules that turn trigger fire times into jobs, queue jobs directly, run jobs through named executors, observe lifecycle events, and read job results for a limited time.

Schedulers are available in asynchronous and synchronous forms. `AsyncScheduler` is the AnyIO-native scheduler. `Scheduler` is a synchronous wrapper that runs an `AsyncScheduler` in a background event loop thread and exposes the same public task, schedule, job, event, and cleanup operations.

## Scope

This specification covers APScheduler's core in-process behavior:

- task declaration with `task()` and task configuration through schedulers;
- schedule creation, lookup, pause, unpause, removal, and conflict handling;
- direct job queuing and synchronous result retrieval;
- background and foreground scheduler lifecycle;
- in-memory task, schedule, job, result, and event behavior visible through a scheduler;
- `DateTrigger` and `IntervalTrigger`;
- asynchronous, thread-pool, and process-pool job execution selected through scheduler configuration;
- public data structures, enums, events, exceptions, and context variables used by those workflows.

## Installable Surface

The package name is `apscheduler`.

The following names are importable from `apscheduler`:

```python
from apscheduler import (
    AsyncScheduler,
    Scheduler,
    SchedulerRole,
    RunState,
    JobOutcome,
    ConflictPolicy,
    CoalescePolicy,
    Task,
    TaskDefaults,
    Schedule,
    ScheduleResult,
    Job,
    JobResult,
    Event,
    DataStoreEvent,
    SchedulerEvent,
    TaskAdded,
    TaskUpdated,
    TaskRemoved,
    ScheduleAdded,
    ScheduleUpdated,
    ScheduleRemoved,
    JobAdded,
    JobRemoved,
    JobAcquired,
    JobReleased,
    ScheduleDeserializationFailed,
    JobDeserializationFailed,
    SchedulerStarted,
    SchedulerStopped,
    TaskLookupError,
    ScheduleLookupError,
    JobLookupError,
    CallableLookupError,
    JobResultNotReady,
    JobCancelled,
    JobDeadlineMissed,
    ConflictingIdError,
    SerializationError,
    DeserializationError,
    MaxIterationsReached,
    RetryMixin,
    RetrySettings,
    UnsetValue,
    current_scheduler,
    current_async_scheduler,
    current_job,
    task,
)
```

The following import paths are part of the covered public surface:

```python
from apscheduler.abc import Serializer, Subscription, Trigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
```

There is no console command covered by this specification. Running `python -m apscheduler` is not supported by this specification.

## Public API

### Schedulers

`AsyncScheduler` is constructed as:

```python
AsyncScheduler(
    data_store=None,
    event_broker=None,
    *,
    identity: str = "",
    role: SchedulerRole = SchedulerRole.both,
    task_defaults: TaskDefaults = TaskDefaults(),
    max_concurrent_jobs: int = 100,
    job_executors=None,
    cleanup_interval: float | timedelta | None = timedelta(minutes=15),
    lease_duration: float | timedelta = 30,
    logger: Logger = ...,
)
```

`Scheduler` is constructed as:

```python
Scheduler(
    data_store: DataStore | None = None,
    event_broker: EventBroker | None = None,
    *,
    identity: str = "",
    role: SchedulerRole = SchedulerRole.both,
    max_concurrent_jobs: int = 100,
    cleanup_interval: float | timedelta | None = None,
    lease_duration: timedelta = timedelta(seconds=30),
    job_executors=None,
    task_defaults: TaskDefaults | None = None,
    logger: Logger | None = None,
)
```

Both schedulers expose:

```python
cleanup()
subscribe(callback, event_types=None, *, one_shot=False)
get_next_event(event_types)
configure_task(func_or_identifier, *, func=unset, job_executor=unset,
               misfire_grace_time=unset, max_running_jobs=unset, metadata=unset)
get_tasks()
add_schedule(func_or_identifier, trigger, *, id=None, args=None, kwargs=None,
             paused=False, coalesce=CoalescePolicy.latest, job_executor=unset,
             misfire_grace_time=unset, metadata=unset, max_jitter=None,
             job_result_expiration_time=0,
             conflict_policy=ConflictPolicy.do_nothing)
get_schedule(id)
get_schedules()
remove_schedule(id)
pause_schedule(id)
unpause_schedule(id, *, resume_from=None)
add_job(func_or_identifier, *, args=None, kwargs=None, job_executor=unset,
        metadata=unset, result_expiration_time=0)
get_jobs()
get_job_result(job_id, *, wait=True)
run_job(func_or_identifier, *, args=None, kwargs=None, job_executor=unset,
        metadata=unset)
start_in_background()
stop()
wait_until_stopped()
run_until_stopped()
```

Asynchronous scheduler methods that touch scheduler services must be awaited. Synchronous scheduler methods return the corresponding result directly.

### Data Objects

`Task` represents a callable definition. Its public attributes are `id`, `func`, `job_executor`, `max_running_jobs`, `misfire_grace_time`, `metadata`, and `running_jobs`. Task equality and hashing are based on `id`. `get_tasks()` returns tasks sorted by task ID.

`TaskDefaults` holds defaults for task creation: `job_executor`, `max_running_jobs`, `misfire_grace_time`, and `metadata`. If a scheduler is not given an explicit default executor, `AsyncScheduler` uses the first configured executor and `Scheduler` uses `"threadpool"`.

`Schedule` represents a trigger-bound task. Its public attributes include `id`, `task identifier`, `trigger`, `args`, `kwargs`, `paused`, `coalesce`, `misfire_grace_time`, `max_jitter`, `job_executor`, `job_result_expiration_time`, `metadata`, `next_fire_time`, `last_fire_time`, `acquired_by`, and `acquired_until`. Schedule equality and hashing are based on `id`.

`Job` represents a queued run request. Its public attributes include `id`, `task identifier`, `args`, `kwargs`, `schedule_id`, `scheduled_fire_time`, `executor`, `jitter`, `start_deadline`, `result_expiration_time`, `metadata`, `created_at`, `acquired_by`, and `acquired_until`. `original_scheduled_time` returns `scheduled_fire_time - jitter` when the job came from a schedule and returns `None` when the job has no scheduled fire time.

`JobResult` represents the stored result for a job. `JobResult.from_job(job, outcome, ...)` must set `job_id` from the job, use the provided or current finish time, and set `expires_at` to `finished_at + job.result_expiration_time`. A successful result carries `return_value`; an errored result carries `exception`.

### Enums

`SchedulerRole.scheduler` processes schedules only, `SchedulerRole.worker` runs jobs only, and `SchedulerRole.both` does both.

`RunState` has `starting`, `started`, `stopping`, and `stopped`.

`ConflictPolicy.replace` replaces an existing schedule with the same ID, `ConflictPolicy.do_nothing` keeps the existing schedule and returns the requested ID without changing stored state, and `ConflictPolicy.exception` raises `ConflictingIdError`.

`CoalescePolicy.latest` queues one job using the latest accumulated fire time, `CoalescePolicy.earliest` queues one job using the earliest accumulated fire time, and `CoalescePolicy.all` queues one job for each accumulated fire time.

`JobOutcome` values identify job completion as `success`, `error`, `missed_start_deadline`, `deserialization_failed`, `cancelled`, or `abandoned`.

## Product State Model

The core scheduler state is the set of tasks, schedules, queued jobs, stored job results, and emitted events managed by a scheduler.

This state has four public projections:

- scheduler methods such as `get_tasks()`, `get_schedules()`, `get_jobs()`, and `get_job_result()`;
- event objects delivered through `subscribe()` and `get_next_event()`;
- context variables visible while a scheduler or job is running.

The scheduler must keep these projections consistent. A task configured through a scheduler must be visible through `get_tasks()` and must publish a `TaskAdded` or `TaskUpdated` event. A schedule added through a scheduler must be visible through `get_schedule()` and `get_schedules()` and must publish `ScheduleAdded`. A job queued directly must be visible through `get_jobs()`, must publish `JobAdded`, and must later publish `JobAcquired` and `JobReleased` when a running worker processes it. A stored result returned by `get_job_result()` must correspond to the same job ID that appeared in the job and event projections.

## Task Configuration

`task(id=unset, job_executor=unset, max_running_jobs=unset, misfire_grace_time=unset, metadata=unset)` decorates a function with APScheduler task defaults. It must raise `ValueError` when applied to a non-callable or when the function already has APScheduler task parameters. It must not wrap or replace the function object.

`configure_task()` accepts a task ID string, a callable, or a `Task` object. It must raise `TypeError` when the first argument is neither a non-empty string, a callable, nor a `Task`.

When a callable is used as a task without an explicit task ID, the task ID must be the callable's fully qualified reference in `module:qualname` form when such a reference can be created. When a local callable cannot be serialized as a reference, the scheduler must still keep the callable available in the current scheduler instance after it has been configured explicitly.

For a new task, unset settings are resolved in descending priority: arguments passed to `configure_task()`, defaults attached by `@task`, then the scheduler's `task_defaults`. For an existing task, omitted arguments must preserve the existing task values. Metadata is merged by top-level keys in the same priority order, with more explicit levels overriding less explicit levels.

When a task is created, the event stream must publish `TaskAdded with the task identifier`. When a task's stored definition changes, the event stream must publish `TaskUpdated with the task identifier`.

## Schedule Lifecycle

`add_schedule()` creates or updates a schedule for an existing task ID, a `Task`, or a callable. If a callable is passed, the scheduler must implicitly create or update the associated task before storing the schedule.

If `id` is omitted, `add_schedule()` must assign a generated string ID and return it. If `id` is supplied, the returned value must be that ID. The stored schedule must preserve the provided `args`, `kwargs`, `paused`, `coalesce`, `misfire_grace_time`, `max_jitter`, `job_executor`, `job_result_expiration_time`, and metadata values after the applicable task/default inheritance has been applied.

When adding a schedule, the scheduler must ask the trigger for its first fire time and store it as `next_fire_time` unless the schedule is created paused. A paused schedule must not be acquired for schedule processing while it remains paused.

When a schedule ID already exists, `ConflictPolicy.do_nothing` must leave the existing schedule unchanged, `ConflictPolicy.replace` must replace it and publish `ScheduleUpdated`, and `ConflictPolicy.exception` must raise `ConflictingIdError`.

`get_schedule(id)` must return the matching schedule and must raise `ScheduleLookupError` if no schedule has that ID. `get_schedules()` must return the currently stored schedules. `remove_schedule(id)` must remove a matching schedule, publish `ScheduleRemoved(finished=False)`, and must not raise when the schedule is already absent.

`pause_schedule(id)` must mark a schedule as paused and publish `ScheduleUpdated`. `unpause_schedule(id)` must mark it as active and publish `ScheduleUpdated`. If `resume_from` is a `datetime` or `"now"`, unpausing must advance the schedule trigger until `next_fire_time` is at or after the requested resume time or until the trigger is exhausted.

Removing a schedule must not cancel jobs that have already been created from it.

## Job Lifecycle

`add_job()` queues a job immediately. It accepts an existing task ID, a `Task`, or a callable. If a callable is passed, the scheduler must implicitly create or update the associated task before storing the job.

The returned value from `add_job()` must be the job UUID. The queued job must be visible from `get_jobs()` until a worker acquires and releases it. `JobAdded` must be published with the job ID, task ID, and `schedule_id=None` for direct jobs.

`run_job()` must queue and run a job, wait for its completion, and return the callable's return value when the job succeeds. If the job callable raises an exception, `run_job()` must raise that exception to the caller.

`get_job_result(job_id, wait=False)` must raise `JobLookupError` when the job exists but no result has been stored yet. With the default `wait=True`, it must wait until the result becomes available or the scheduler stops processing it. When a stored result is retrieved, it is consumed so a subsequent non-waiting retrieval for the same job ID raises `JobLookupError`.

When a worker acquires a job, `JobAcquired` must be published. When it releases the job, `JobReleased` must be published with the job ID, scheduler ID, task ID, schedule ID, outcome, scheduled start time, and start time. A successful job must store a `JobResult` with `JobOutcome.success` and the callable return value when the result expiration time is positive. A job whose callable raises an exception must store `JobOutcome.error` and the exception object when the result expiration time is positive.

If a job's `start_deadline` has passed before execution begins, the scheduler must finish it with `JobOutcome.missed_start_deadline` instead of calling the task. If a running job is cancelled because the scheduler stops, its outcome must be `JobOutcome.cancelled`. If a scheduler restarts and encounters work that was claimed but never completed, the observable outcome must be `JobOutcome.abandoned`.

## Scheduler Lifecycle

`AsyncScheduler` must be used as an async context manager before calling service-dependent methods other than `run_until_stopped()`. Calling those methods before initialization must raise `RuntimeError`. `Scheduler` initializes its services when used as a context manager or lazily when a public method needs the background portal.

`start_in_background()` must start schedule and/or job processing according to `role` and must publish `SchedulerStarted`. `stop()` must request shutdown. `wait_until_stopped()` must return after the scheduler has stopped. `run_until_stopped()` must run the scheduler until it is explicitly stopped. Stopping must publish `SchedulerStopped`, with an exception attached when the scheduler stops because of an error.

When a scheduler is running with `SchedulerRole.scheduler`, it must process due schedules but not execute jobs. With `SchedulerRole.worker`, it must execute queued jobs but not process schedules. With `SchedulerRole.both`, it must do both.

`cleanup()` must remove expired job results and remove finished schedules whose `next_fire_time` is `None` once they no longer have associated jobs. A scheduler with a non-`None` `cleanup_interval` must perform cleanup periodically while running.

The synchronous scheduler must raise `RuntimeError` from `start_in_background()` when running under uWSGI with threads disabled.

## In-Memory Scheduler Behavior

The default in-process configuration must keep tasks, schedules, jobs, and retained job results available for the lifetime of the scheduler. `get_tasks()` returns tasks sorted by task ID. `get_schedules()` returns current schedules in next-fire order, with exhausted schedules after schedules that still have a fire time.

Due, unpaused schedules must create jobs without allowing two active scheduler loops to process the same fire time. Jobs must respect `max_running_jobs`, start deadlines, and `max_concurrent_jobs`. While a job is running, the matching task's public `running_jobs` count increases; after success, error, cancellation, abandonment, or missed deadline, it returns to the correct value.

Completing a job removes it from `get_jobs()`, publishes the documented release event, and retains its result only for the configured result expiration time. `cleanup()` removes expired results and finished schedules that no longer have associated jobs.

## Events

Every event has a timezone-aware `timestamp`. `DataStoreEvent` is the base for task, schedule, and job storage events. `SchedulerEvent` is the base for scheduler and worker lifecycle events.

`subscribe(callback, event_types=None, one_shot=False)` returns a subscription object whose `unsubscribe()` method removes the callback. If `event_types` is omitted, all events are delivered. If a single event class is passed, only that class is delivered. If an iterable of event classes is passed, any matching class is delivered. If `one_shot=True`, the subscription must remove itself after the first matching delivery.

`get_next_event(event_types)` must wait for and return the next event matching the requested event type or types.

The default in-process event delivery must invoke subscriptions within the current process and preserve the public event objects without requiring serialization.

## Triggers

`DateTrigger(run_time)` must convert the supplied run time to a timezone-aware `datetime`. Its first `next()` call must return that run time. Later `next()` calls must return `None`. Its state round-trip must preserve both the run time and whether it has already fired.

`IntervalTrigger(weeks=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0, start_time=now, end_time=None)` must raise `ValueError` if the combined interval is not positive. It must raise `ValueError` if `end_time` is earlier than `start_time`. Its first `next()` call must return `start_time`, and each later call must return the previous fire time plus the interval until that value would exceed `end_time`, at which point it returns `None`. Its state round-trip must preserve interval fields, start and end times, and the last returned fire time.

Trigger `next()` results must be timezone-aware datetimes or `None`.

## Job Execution And Context Variables

An asynchronous execution mode must call the job function in the scheduler's event-loop context and await an awaitable result. Thread-pool and process-pool execution modes must run the callable in the selected worker environment and return its result through the same public job-result API. The scheduler may choose its internal executor classes and module layout freely.

While a synchronous scheduler is initialized, `current_scheduler.get()` must return that scheduler in the scheduler's managed context. While an asynchronous job function is being executed by `AsyncScheduler`, `current_async_scheduler.get()` must identify the scheduler that is running the job. While any job function is being executed by a scheduler, `current_job.get()` must return the `Job` object being run.

## Error Semantics

`TaskLookupError` must be raised when a requested task ID is not found. `ScheduleLookupError` must be raised when a requested schedule ID is not found. `JobLookupError` must be raised when a requested job ID is not found or a non-waiting result lookup is attempted before the result is ready.

`CallableLookupError` must be raised when a persisted task requires a callable reference that cannot be resolved or when a locally defined callable is required but has not been configured in the current scheduler instance.

`JobCancelled` must be raised by job result retrieval when the stored outcome is `cancelled`. `JobDeadlineMissed` must be raised by job result retrieval when the stored outcome is `missed_start_deadline`. When the stored outcome is `error`, result retrieval must raise the original exception.

`ConflictingIdError` must be raised when adding a schedule whose ID already exists and `ConflictPolicy.exception` is used.

`SerializationError` and `DeserializationError` represent serializer failures. `MaxIterationsReached` represents trigger combination exhaustion; combination trigger behavior is outside this scope except for the public exception name.

## Cross-View Invariants

- A task created through `configure_task()` must appear in `get_tasks()` and must emit exactly one task-add or task-update event for the stored change.
- A schedule created through `add_schedule()` must appear through `get_schedule()` and `get_schedules()` with the same ID, task ID, trigger-derived next fire time, pause state, and metadata visible in the corresponding schedule event.
- A schedule removed through `remove_schedule()` must disappear from scheduler schedule views and must emit `ScheduleRemoved` without cancelling already queued jobs from that schedule.
- A direct job created through `add_job()` must appear in `get_jobs()` before processing and must emit `JobAdded` with `schedule_id=None`.
- A job processed by a running worker must emit `JobAcquired` before `JobReleased`, and the job ID and task ID in both events must match the job result retrieved for that job.
- A stored successful job result must return the callable's return value through `get_job_result()` and must raise `JobLookupError` on a second non-waiting retrieval.
- The task `running_jobs` count must increase when a job is acquired and must return to zero when the job is released, cancelled, abandoned, or missed its start deadline.
- A paused schedule must remain visible in schedule views but must not create new jobs until it is unpaused.
- Metadata values must agree across task, schedule, and job projections according to the documented inheritance rule: more explicit top-level keys override less explicit top-level keys.
- Context variables observed inside a job must identify the scheduler and job that are actually running that callable.

## Representative Workflows

### Direct Job Queue With Result

```python
from apscheduler import Scheduler, JobAdded, JobAcquired, JobReleased

def add(x, y):
    return x + y

with Scheduler() as scheduler:
    seen = []
    scheduler.subscribe(seen.append, {JobAdded, JobAcquired, JobReleased})
    job_id = scheduler.add_job(add, args=[2, 3], result_expiration_time=30)
    assert scheduler.get_jobs()[0].id == job_id
    scheduler.start_in_background()
    result = scheduler.get_job_result(job_id)
    assert result.return_value == 5
```

The job is first stored, then acquired by the running scheduler, then released with `JobOutcome.success`. The result is retrievable because a positive expiration time was requested.

### Date Schedule Lifecycle

```python
from datetime import datetime, timezone
from apscheduler import Scheduler
from apscheduler.triggers.date import DateTrigger

def touch():
    return "done"

with Scheduler() as scheduler:
    run_time = datetime.now(timezone.utc)
    schedule_id = scheduler.add_schedule(touch, DateTrigger(run_time), id="once")
    assert schedule_id == "once"
    scheduler.pause_schedule("once")
    assert scheduler.get_schedule("once").paused
    scheduler.unpause_schedule("once")
    assert not scheduler.get_schedule("once").paused
    scheduler.remove_schedule("once")
    assert scheduler.get_schedules() == []
```

The same schedule state is visible through the scheduler methods and the event stream.

## Non-Goals

This specification does not require support for PostgreSQL, MySQL, MongoDB, Redis, MQTT, AsyncPG, Psycopg, SQLAlchemy, Qt, CBOR, JSON, or Pickle serializer edge cases. It does not require full Cron, calendar interval, trigger combination, or custom trigger implementations beyond the public names and exception classes listed above. It does not require exact `repr()` strings, exact exception message text, private attributes, private helper modules, database schema layout, network protocols, or multi-process event delivery.

## Invocation Protocol

There is no console script in scope. `python -m apscheduler` is not supported.

Exit code behavior is therefore not applicable for this package-level API specification.

## Evaluation Notes

Implementations are exercised through public imports and public methods. The checks cover task configuration and inheritance, schedule lifecycle, direct job queueing and result retrieval, scheduler state transitions, in-memory data store consistency, local event delivery, date and interval triggers, job executors, context variables, and documented exception types. Tests use observable return values, stored public objects, and delivered public events.
