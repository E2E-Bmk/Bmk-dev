# APScheduler Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

APScheduler is an in-process Python scheduler and job queue. It lets applications define tasks, create schedules that turn trigger fire times into jobs, queue jobs directly, run jobs through named executors, observe lifecycle events, and read job results for a limited time.

The scheduler owns three cooperating services:

- a data store that holds tasks, schedules, jobs, and job results;
- an event broker that publishes task, schedule, job, and scheduler lifecycle events;
- job executors that call the Python callable associated with a job.

Schedulers are available in asynchronous and synchronous forms. `AsyncScheduler` is the async-native scheduler. `Scheduler` is a synchronous wrapper that runs an `AsyncScheduler` in a background event loop thread and exposes the same public task, schedule, job, event, and cleanup operations.

## Non-Goals

- This specification does not require Remote-service data stores, message brokers, GUI framework integrations, or format-specific serializer edge cases.
- This specification does not require Full cron expressions, calendar-interval triggers, trigger combination logic, or custom trigger implementations; only the public trigger names and exception classes listed here apply.
- This specification does not require Exact `repr()` strings, exact exception message text, private attributes, private helper modules, database schema layout, network protocols, or multi-process event delivery.

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

## Task Configuration

Task configuration defines what callable a scheduler manages, along with defaults for scheduling and execution.

**The task decorator.** The `task` decorator must attach scheduling defaults such as `id`, `job_executor`, `max_running_jobs`, `misfire_grace_time`, and `metadata` to a function. It must raise `ValueError` when applied to a non-callable or when the function already has APScheduler task parameters. It must not wrap or replace the function object.

**Configuring tasks on a scheduler.** `configure_task` accepts a task ID string, a callable, or a `Task` object. It must raise `TypeError` when the first argument is neither a non-empty string, a callable, nor a `Task`. When a callable is used as a task without an explicit task ID, the task ID must be the callable's fully qualified reference in `module:qualname` form when such a reference can be created, and the resulting `Task.func` must end with the callable's qualified name. When a local callable cannot be serialized as a reference, the scheduler must still keep the callable available in the current scheduler instance after it has been configured explicitly.

**Task field inheritance.** For a new task, unset settings are resolved in descending priority: arguments passed to `configure_task`, defaults attached by `@task`, then the scheduler's `task_defaults`. For an existing task, omitted arguments must preserve the existing task values. Metadata is merged by top-level keys in the same priority order, with more explicit levels overriding less explicit levels. The default `job_executor` must be `"threadpool"` when no other source supplies it.

**Task object attributes.** A `Task` returned by `configure_task` must expose `id`, `func`, `job_executor`, `max_running_jobs`, `misfire_grace_time`, `metadata`, and `running_jobs`. A newly configured task must have `running_jobs` equal to zero and `metadata` equal to the merged result. Tasks with the same `id` must compare as equal and produce the same hash. `get_tasks` must return tasks sorted by task ID.

**Task events.** When a task is created, the event stream must publish `TaskAdded` with a `task_id` matching the configured identifier. When a task's stored definition changes, the event stream must publish `TaskUpdated` with the `task_id`.

## Schedule Lifecycle

Schedules bind a task to a trigger, producing jobs at trigger fire times while the schedule remains active.

**Creating schedules.** `add_schedule` creates or updates a schedule for an existing task ID, a `Task`, or a callable. If a callable is passed, the scheduler must implicitly create or update the associated task before storing the schedule. When `id` is omitted, `add_schedule` must assign a generated string ID and return it. When `id` is supplied, the returned value must be that ID.

**Stored schedule attributes.** The stored schedule must preserve the provided `args`, `kwargs`, `paused`, `coalesce`, `misfire_grace_time`, `max_jitter`, `job_executor`, `job_result_expiration_time`, and `metadata` values after the applicable task/default inheritance has been applied. The `task_id` must reference the associated task. When `coalesce` is not explicitly set, it must default to `CoalescePolicy.latest`. When adding a schedule, the scheduler must ask the trigger for its first fire time and store it as `next_fire_time` unless the schedule is created paused.

**Conflict policies.** When a schedule ID already exists, `ConflictPolicy.do_nothing` must leave the existing schedule unchanged and return the same ID, `ConflictPolicy.replace` must replace it and publish `ScheduleUpdated`, and `ConflictPolicy.exception` must raise `ConflictingIdError`.

**Lookup and removal.** `get_schedule` must return the matching schedule and must raise `ScheduleLookupError` if no schedule has that ID. `get_schedules` must return the currently stored schedules ordered by `next_fire_time`. `remove_schedule` must remove a matching schedule, publish `ScheduleRemoved` with `finished` set to `False`, and must not raise when the schedule is already absent. Removing a schedule must not cancel jobs that have already been created from it.

**Pausing and unpausing.** `pause_schedule` must mark a schedule as paused and publish `ScheduleUpdated`. `unpause_schedule` must mark it as active and publish `ScheduleUpdated`. When `resume_from` is a `datetime` or `"now"`, unpausing must advance the schedule trigger until `next_fire_time` is at or after the requested resume time or until the trigger is exhausted. A paused schedule must not be acquired for schedule processing while it remains paused.

**Schedule events.** When a schedule is created, `ScheduleAdded` must be published with `schedule_id`, `task_id`, and `next_fire_time`. When a schedule is modified, `ScheduleUpdated` must be published. When a schedule is removed, `ScheduleRemoved` must be published with `schedule_id` and `finished`.

## Job Lifecycle

Jobs represent individual callable executions queued directly or created from schedule fire times.

**Queuing jobs.** `add_job` queues a job immediately. It accepts an existing task ID, a `Task`, or a callable. If a callable is passed, the scheduler must implicitly create or update the associated task before storing the job.

**Job attributes.** The returned value from `add_job` must be the job UUID. The queued job must be visible from `get_jobs` until a worker acquires and releases it. Each job must expose `id`, `task_id`, `args`, `kwargs`, `executor`, `result_expiration_time`, `schedule_id`, `scheduled_fire_time`, `original_scheduled_time`, `jitter`, and `metadata`. For direct jobs, `schedule_id` must be `None`. When `result_expiration_time` is provided as a number, it must be stored as a `timedelta`. The default `executor` must be `"threadpool"` when inherited from task defaults.

**Job events.** `JobAdded` must be published with `job_id` and `schedule_id` set to `None` for direct jobs. When a worker acquires a job, `JobAcquired` must be published. When it releases the job, `JobReleased` must be published with `job_id`, `task_id`, `outcome`, and other job metadata. Events must be published in lifecycle order: `JobAdded`, then `JobAcquired`, then `JobReleased`.

**Running jobs synchronously.** `run_job` must queue and run a job, wait for its completion, and return the callable's return value when the job succeeds. If the job callable raises an exception, `run_job` must raise that exception to the caller. When `job_executor` is specified, it must route the job to that executor.

**Job results.** `get_job_result` must raise `JobLookupError` when the job exists but no result has been stored yet and `wait` is `False`. With the default `wait=True`, it must wait until the result becomes available. A successful job must store a `JobResult` with `JobOutcome.success` and the callable return value when the result expiration time is positive. A job whose callable raises an exception must store `JobOutcome.error` and the exception object when the result expiration time is positive. When a stored result is retrieved from the memory data store, the result must be removed from storage so a subsequent non-waiting retrieval for the same job ID raises `JobLookupError`. `JobResult.from_job` must construct a result whose `job_id` matches the job and whose `expires_at` equals `finished_at` plus `result_expiration_time`.

**Job outcome edge cases.** If a job's `start_deadline` is before acquisition time, the data store must release it with `JobOutcome.missed_start_deadline` instead of handing it to an executor. If a running job is cancelled because the scheduler stops, it must be released with `JobOutcome.cancelled`. If a scheduler restarts and finds jobs it had acquired but not released, it must release them with `JobOutcome.abandoned`. `original_scheduled_time` must equal `scheduled_fire_time` minus `jitter` for schedule-created jobs.

## Scheduler Lifecycle

The scheduler manages its own lifecycle through context management, background start/stop, and periodic cleanup.

**Initialization and context management.** `AsyncScheduler` must be used as an async context manager before calling service-dependent methods. `Scheduler` initializes its services when used as a context manager or lazily when a public method needs the background portal. Both schedulers must expose `data_store` (defaulting to `MemoryDataStore`), `event_broker` (defaulting to `LocalEventBroker`), `role` (defaulting to `SchedulerRole.both`), `identity` (a non-empty string), `max_concurrent_jobs` (defaulting to 100), and `state` (a `RunState` value).

**Starting and stopping.** `start_in_background` must start schedule and/or job processing according to `role` and must publish `SchedulerStarted`. `stop` must request shutdown. `wait_until_stopped` must return after the scheduler has stopped, and `state` must be `RunState.stopped` at that point. `run_until_stopped` must run the scheduler until it is explicitly stopped. Stopping must publish `SchedulerStopped`, with an exception attached when the scheduler stops because of an error.

**Scheduler roles.** When a scheduler is running with `SchedulerRole.scheduler`, it must process due schedules but not execute jobs—jobs created from schedules must remain visible in `get_jobs`. With `SchedulerRole.worker`, it must execute queued jobs but not process schedules. With `SchedulerRole.both`, it must do both.

**Cleanup.** `cleanup` must remove expired job results and remove finished schedules whose `next_fire_time` is `None` once they no longer have associated jobs. When `cleanup_interval` is set to a non-`None` value, the scheduler must perform cleanup periodically while running. When `cleanup_interval` is `None`, automatic cleanup is disabled and the caller must invoke `cleanup` manually.

**Context variables during initialization.** While a synchronous `Scheduler` is used as a context manager, `current_scheduler.get()` must return that scheduler instance. The synchronous scheduler must raise `RuntimeError` from `start_in_background` when running under uWSGI with threads disabled.

## Memory Data Store

The in-process memory data store manages task, schedule, job, and result storage with event-driven notifications.

**Storage and events.** `MemoryDataStore` stores tasks, schedules, jobs, and job results in process memory. It must publish events through its event broker for task additions, task updates, task removals, schedule additions, schedule updates, schedule removals, job additions, job acquisitions, and job releases.

**Task and schedule queries.** `get_tasks` must return tasks sorted by task ID. `get_task` must return a task by ID and must raise `TaskLookupError` when no task has that ID. `get_schedules` must return all schedules ordered by next fire time, placing exhausted schedules after schedules with a next fire time. `get_next_schedule_run_time` must return the earliest stored `next_fire_time`, or `None` when there are no schedules.

**Schedule acquisition and release.** `acquire_schedules` must return due, unpaused schedules whose leases are absent, expired, or already owned by the same scheduler. It must mark returned schedules with the scheduler ID and a lease deadline equal to the current time plus the lease duration. `release_schedules` must update each schedule's `last_fire_time`, `next_fire_time`, and acquisition fields from the supplied `ScheduleResult`, then publish `ScheduleUpdated`.

**Job acquisition and release.** `acquire_jobs` must skip jobs whose non-expired acquisition lease belongs to another worker, must skip jobs for tasks already at `max_running_jobs`, must release missed-deadline jobs with `JobOutcome.missed_start_deadline`, and must mark returned jobs with the scheduler ID and lease deadline. It must increment the task's `running_jobs` count for each acquired job. `release_job` must remove the job from the queued job views, decrement the task's running count when appropriate, store the result only when its `expires_at` is after its `finished_at`, and publish `JobReleased`.

**Cleanup.** `cleanup` must delete expired job results, release expired acquired jobs as abandoned, and remove finished schedules that no longer have jobs.

## Events

The event system provides observable lifecycle notifications for tasks, schedules, jobs, and the scheduler itself.

**Event hierarchy.** Every event has a timezone-aware `timestamp`. `DataStoreEvent` is the base for task, schedule, and job storage events. `SchedulerEvent` is the base for scheduler and worker lifecycle events.

**Subscribing to events.** `subscribe` returns a subscription object whose `unsubscribe` method removes the callback. When `event_types` is omitted, all events are delivered. When a single event class is passed as a set, only that class is delivered. When an iterable of event classes is passed, any matching class is delivered. When `one_shot` is `True`, the subscription must remove itself after the first matching delivery and must not deliver subsequent events of that type.

**Waiting for events.** `get_next_event` must wait for and return the next event matching the requested event type or types.

**Local event broker.** `LocalEventBroker` must deliver events only within the current process and must not serialize events.

## Triggers

Triggers determine when schedules produce jobs by generating fire-time sequences.

**Date trigger.** `DateTrigger` must convert the supplied run time to a timezone-aware `datetime`; a naive datetime must be converted using the local timezone. Its first `next` call must return that run time. Later `next` calls must return `None`. Its state round-trip through pickle must preserve both the run time and whether it has already fired: a freshly restored trigger that has not fired must return the run time, while a restored trigger that has already fired must return `None`.

**Interval trigger.** `IntervalTrigger` accepts interval components such as `weeks`, `days`, `hours`, `minutes`, `seconds`, and `microseconds`. It must raise `ValueError` when the combined interval is not positive. It must raise `ValueError` when `end_time` is earlier than `start_time`. Its first `next` call must return `start_time`, and each later call must return the previous fire time plus the interval until that value would exceed `end_time`, at which point it returns `None`. Its state round-trip through pickle must preserve interval fields, start and end times, and the last returned fire time, so that a restored trigger continues from the last fired position.

**General trigger contract.** Trigger `next` results must be timezone-aware datetimes or `None`.

## Job Executors and Context Variables

Executors determine how job callables are invoked, and context variables expose the active scheduler and job to running code.

**Async executor.** `AsyncJobExecutor` must call the job function on the event loop thread. If the function returns an awaitable, it must await it and use the awaited value as the result. The executor must run the callable on the same thread as the event loop, so `threading.get_ident` inside an async job must equal the event loop thread identifier.

**Thread pool executor.** `ThreadPoolJobExecutor` must run the job function in a worker thread and return the callable result. The worker thread must be distinct from the calling thread.

**Process pool executor.** `ProcessPoolJobExecutor` must run the job function in a worker process and return the callable result.

**Context variables.** While a synchronous scheduler is initialized, `current_scheduler.get()` must return that scheduler instance, and its `identity` must match the configured scheduler identity. While an asynchronous job function is being executed by `AsyncScheduler`, `current_async_scheduler.get()` must identify the scheduler that is running the job, and its `identity` must match. While any job function is being executed by a scheduler, `current_job.get()` must return the `Job` object being run, and its `id` must match the job ID visible through the job and result projections.

## State Model

The core scheduler state is the set of tasks, schedules, queued jobs, stored job results, and emitted events associated with one data store and one event broker.

This state has four public projections:

- scheduler methods such as `get_tasks()`, `get_schedules()`, `get_jobs()`, and `get_job_result()`;
- data store operations on `MemoryDataStore`;
- event objects delivered through `subscribe()` and `get_next_event()`;
- context variables visible while a scheduler or job is running.

The scheduler must keep these projections consistent. A task configured through a scheduler must be visible through `get_tasks()` and must publish a `TaskAdded` or `TaskUpdated` event. A schedule added through a scheduler must be visible through `get_schedule()` and `get_schedules()` and must publish `ScheduleAdded`. A job queued directly must be visible through `get_jobs()`, must publish `JobAdded`, and must later publish `JobAcquired` and `JobReleased` when a running worker processes it. A stored result returned by `get_job_result()` must correspond to the same job ID that appeared in the job and event projections.

## Error Semantics

`TaskLookupError` must be raised when a requested task ID is not found. `ScheduleLookupError` must be raised when a requested schedule ID is not found. `JobLookupError` must be raised when a requested job ID is not found or a non-waiting result lookup is attempted before the result is ready.

`CallableLookupError` must be raised when a persisted task requires a callable reference that cannot be resolved or when a locally defined callable is required but has not been configured in the current scheduler instance.

`JobCancelled` must be raised by job result retrieval when the stored outcome is `cancelled`. `JobDeadlineMissed` must be raised by job result retrieval when the stored outcome is `missed_start_deadline`. When the stored outcome is `error`, result retrieval must raise the original exception. `JobResultNotReady` must be constructible from a job ID and must be a public exception class.

`JobOutcome` must expose the members `success`, `error`, `missed_start_deadline`, `deserialization_failed`, `cancelled`, and `abandoned`. `RunState` must expose the members `starting`, `started`, `stopping`, and `stopped`. `SchedulerRole` must expose the members `scheduler`, `worker`, and `both`.

`ConflictingIdError` must be raised when adding a schedule whose ID already exists and `ConflictPolicy.exception` is used.

`SerializationError` and `DeserializationError` represent serializer failures. `MaxIterationsReached` represents trigger combination exhaustion; combination trigger behavior is outside this scope except for the public exception name.

## Cross-View Invariants

- A task created through `configure_task()` must appear in `get_tasks()` and must emit exactly one task-add or task-update event for the stored change.
- A schedule created through `add_schedule()` must appear through `get_schedule()` and `get_schedules()` with the same ID, task ID, trigger-derived next fire time, pause state, and metadata visible in the corresponding schedule event.
- A schedule removed through `remove_schedule()` must disappear from scheduler schedule views and must emit `ScheduleRemoved` without cancelling already queued jobs from that schedule.
- A direct job created through `add_job()` must appear in `get_jobs()` before processing and must emit `JobAdded` with `schedule_id=None`.
- A job processed by a running worker must emit `JobAcquired` before `JobReleased`, and the job ID and task ID in both events must match the job result retrieved for that job.
- A stored successful job result must return the callable's return value through `get_job_result()` and must raise `JobLookupError` on a second non-waiting retrieval from the memory data store.
- The task `running_jobs` count must increase when a job is acquired and must return to zero when the job is released, cancelled, abandoned, or missed its start deadline.
- A paused schedule must remain visible in schedule views but must not create new jobs until it is unpaused.
- Metadata values must agree across task, schedule, and job projections according to the documented inheritance rule: more explicit top-level keys override less explicit top-level keys.
- Context variables observed inside a job must identify the scheduler and job that are actually running that callable.

## Public Interface

### Import Surface

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
from apscheduler.abc import DataStore, EventBroker, JobExecutor, Serializer, Subscription, Trigger
from apscheduler.datastores.memory import MemoryDataStore
from apscheduler.eventbrokers.local import LocalEventBroker
from apscheduler.executors.async_ import AsyncJobExecutor
from apscheduler.executors.thread import ThreadPoolJobExecutor
from apscheduler.executors.subprocess import ProcessPoolJobExecutor
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
```

There is no console command covered by this specification. Running `python -m apscheduler` is not supported by this specification.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `AsyncScheduler` | class | Async-native scheduler managing tasks, schedules, and jobs |
| `Scheduler` | class | Synchronous scheduler wrapping `AsyncScheduler` in a background thread |
| `SchedulerRole` | enum | Scheduler processing mode: scheduler-only, worker-only, or both |
| `RunState` | enum | Scheduler lifecycle states: starting, started, stopping, stopped |
| `ConflictPolicy` | enum | Schedule-ID conflict resolution: replace, do_nothing, or exception |
| `CoalescePolicy` | enum | Accumulated fire-time handling: latest, earliest, or all |
| `JobOutcome` | enum | Job completion status: success, error, missed, cancelled, abandoned |
| `Task` | class | Callable definition with scheduling defaults |
| `TaskDefaults` | class | Default values for task creation parameters |
| `Schedule` | class | Trigger-bound task with fire-time state |
| `ScheduleResult` | class | Per-schedule result used during schedule release |
| `Job` | class | Queued callable run request |
| `JobResult` | class | Stored outcome and return value for a completed job |
| `Event` | class | Base event with timezone-aware timestamp |
| `DataStoreEvent` | class | Base for task, schedule, and job storage events |
| `SchedulerEvent` | class | Base for scheduler lifecycle events |
| `TaskAdded` | class | Event published when a task is created |
| `TaskUpdated` | class | Event published when a task definition changes |
| `TaskRemoved` | class | Event published when a task is removed |
| `ScheduleAdded` | class | Event published when a schedule is created |
| `ScheduleUpdated` | class | Event published when a schedule is modified |
| `ScheduleRemoved` | class | Event published when a schedule is removed |
| `JobAdded` | class | Event published when a job is queued |
| `JobAcquired` | class | Event published when a worker acquires a job |
| `JobReleased` | class | Event published when a worker releases a job |
| `SchedulerStarted` | class | Event published when the scheduler starts processing |
| `SchedulerStopped` | class | Event published when the scheduler stops |
| `MemoryDataStore` | class | In-process task, schedule, job, and result storage |
| `LocalEventBroker` | class | In-process event delivery broker |
| `AsyncJobExecutor` | class | Executor running jobs on the event loop thread |
| `ThreadPoolJobExecutor` | class | Executor running jobs in a worker thread pool |
| `ProcessPoolJobExecutor` | class | Executor running jobs in a worker process pool |
| `DateTrigger` | class | Trigger firing once at a specified time |
| `IntervalTrigger` | class | Trigger firing at regular intervals |
| `task` | decorator | Attach scheduling defaults to a callable |
| `current_scheduler` | context var | The active synchronous scheduler |
| `current_async_scheduler` | context var | The active async scheduler |
| `current_job` | context var | The job being executed |

### CLI Entry Points

There is no console script in scope. `python -m apscheduler` is not supported.

Exit code behavior is therefore not applicable for this package-level API specification.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Implementations are exercised through public imports and public methods. The checks cover task configuration and inheritance, schedule lifecycle, direct job queueing and result retrieval, scheduler state transitions, in-memory data store consistency, local event delivery, date and interval triggers, job executors, context variables, and documented exception types. Tests use observable return values, stored public objects, and delivered public events.
