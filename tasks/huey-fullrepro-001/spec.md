# Huey Specification

=== Context Layer ===

## Product Overview

`huey` is a Python task queue library that turns functions into task wrappers, serializes task messages into storage, executes queued or scheduled work, stores results, and exposes composition, signals, retries, revocation, locks, and rate limiting. `MemoryHuey` and `MemoryStorage` provide a complete in-process route for these workflows without an external service.

An application creates a Huey instance, decorates functions with `task()` or `periodic_task()`, invokes task wrappers to enqueue work, and receives `Result` handles. Work may execute immediately or be dequeued and passed to `execute()`. The same task state is observable through queue, schedule, result, signal, storage, and composition APIs.

## Non-Goals

- Redis, SQLite, filesystem, PostgreSQL, Django, Flask, greenlet, and other optional integrations are outside this specification.
- The `huey_consumer` command, worker processes, process signals, health checks, live reload, and deployment configuration are not required.
- Network access, cross-process durability, distributed locking, and multi-process contention behavior are not required.
- Exact exception prose, traceback text, logging text, generated task identifiers, random instance names, and elapsed execution time are not defined.
- Private modules, private attributes, source-test helpers, and undocumented storage internals are not part of the required surface.
- Wall-clock waiting, delayed delivery by a background scheduler, and concurrency stress are excluded; scheduled behavior is driven with explicit timestamps.

## Scope

This specification covers `MemoryHuey`, `MemoryStorage`, task wrappers and messages, immediate and queued execution, result lifecycle, groups, pipelines, chords, scheduling, periodic crontab matching, serialization and signing, lifecycle signals, execution hooks, retries, expiration, priorities, revocation, local locks, local rate limiting, and public storage introspection.

All workflows are deterministic and execute in one Python process. Queue and schedule transitions are advanced by explicit `dequeue`, `read_schedule`, and `execute` calls rather than background workers.

=== Orientation Layer ===

## Representative Workflows

A queued task returns a result handle before it is executed:

```python
from huey import MemoryHuey

huey = MemoryHuey("example", immediate=False, utc=False)

@huey.task()
def add(left, right):
    return left + right

result = add(4, 7)
assert result.is_ready() is False
task = huey.dequeue()
assert huey.execute(task) == 11
assert result.get() == 11
```

Immediate mode performs the same workflow synchronously:

```python
immediate = MemoryHuey("immediate", immediate=True, utc=False)

@immediate.task()
def square(value):
    return value * value

assert square(5).get() == 25
```

A composition passes values between tasks and collects grouped results:

```python
from huey import group

pipeline = add.s(1, 2).then(add, 4)
pipeline_result = immediate.enqueue(pipeline)

batch = group([square.s(2), square.s(3), square.s(5)])
batch_result = immediate.enqueue(batch)
assert batch_result.get() == [4, 9, 25]
```

=== Behavior Layer ===

## Tasks And Execution

**Huey instances.** `MemoryHuey(name, immediate=..., utc=..., results=..., store_none=..., serializer=...)` uses `MemoryStorage`. It exposes its nonempty `name`, `storage`, and mutable `immediate` property. A new instance has zero pending, scheduled, and stored-result counts, and `len(huey)` equals the pending count.

**Task declaration.** `huey.task()` decorates a callable and returns a task wrapper. The wrapper is callable, exposes `call_local`, `s`, `schedule`, and `map`, and retains declaration options such as task name, priority, retries, context, and result handling. `call_local(*args, **kwargs)` invokes the original callable without enqueueing and returns its value.

**Task messages.** `wrapper.s(*args, **kwargs)` builds an unenqueued task with public `id`, `name`, `args`, `kwargs`, and `data`; `data` is the `(args, kwargs)` pair. A configured task name replaces the function name. `huey.serialize_task(task)` and `deserialize_task(data)` preserve identity, name, positional arguments, and keyword arguments.

**Queued execution.** Calling a wrapper while `immediate` is false enqueues one task and returns a result handle. `pending_count()` reflects queued tasks. `dequeue()` returns the next task, and `execute(task, timestamp=...)` invokes it, stores its result when enabled, emits lifecycle signals, and returns the callable result. After execution, the pending count decreases. `pending(limit=...)` returns deserialized queued tasks in dequeue order without removing them and honors its limit.

**Immediate execution.** Calling a wrapper while `immediate` is true executes synchronously and returns a ready result handle. Toggling `huey.immediate` changes later calls between queueing and synchronous execution. Work queued before a flush does not later acquire a result merely because immediate mode was enabled.

**Context tasks.** A wrapper declared with `context=True` receives its executing public task object in a `task` keyword argument. That object has the same task `id` and `name` visible through dequeue and result handling.

**Optional results.** A `MemoryHuey` created with `results=False` executes immediate work but returns no result handle and stores no results. With `store_none=True`, a callable returning `None` yields a ready result whose `get()` returns `None`.

## Results

Every normal task invocation returns a `Result` with a stable nonempty `id`. `is_ready()` is false before queued execution and true once a result or failure record is available. `get()` returns the stored value and normally consumes its storage entry. `get(preserve=True)` reads without consuming. `reset()` resets local read state so a preserved value can be read again.

`huey.result(identifier)` reads a completed value by identifier. `huey.all_results()` returns the identifiers of all currently stored results. `result_count()` reflects the current result store and decreases when results are consumed or flushed.

If task execution raises an exception, `execute()` returns `None` and result retrieval raises `TaskException`. Its public `metadata` is a dictionary containing at least the key formed by `"task" + "_id"` and an `error` description. The `Error` value type exposes its supplied metadata through `metadata`.

`ResultGroup` preserves member order. It supports `len`, iteration over member result handles, integer indexing that resolves the selected member value, and `get()` that resolves all member values as a list.

## Pipelines And Groups

`Task.then(next_task, *args, **kwargs)` attaches completion work and returns the original task. If a task returns a tuple, its elements become positional arguments to the next task. If it returns a dictionary, its items become keyword arguments. Other return values are passed as a single leading positional argument. Pipeline result retrieval preserves every stage result in execution order.

`Task.error(handler)` attaches error handling and returns the original task. The public `on_complete` and `on_error` links reflect attached completion and error work.

`Task.map(iterable)` creates one task per input item and returns an ordered `ResultGroup`. `group(tasks)` groups distinct tasks; enqueueing it returns a group result whose order matches the input task order.

`chord(tasks, callback)` executes member tasks, collects their result values in order, and passes that list to the callback. The returned chord result exposes `results` for the members, `callback` for the callback result, and `get()` for the final callback value. Calling `then` on a chord extends its callback pipeline, and `pipeline_results` exposes all callback-pipeline values in order.

## Scheduling And Periodic Tasks

`TaskWrapper.schedule(args=None, kwargs=None, eta=None, delay=None)` requires either `eta` or `delay`; omitting both raises `ValueError`. A scheduled invocation first appears in pending storage, moves to schedule storage when executed before its ETA, and becomes executable after `read_schedule(timestamp)` returns it. `scheduled()`, `scheduled_count()`, and `flush()` project or clear scheduled state.

`Result.reschedule(eta=..., delay=...)` revokes the original task and creates a replacement with a different identifier. The original result reports revoked state.

`crontab()` returns a callable timestamp matcher. Wildcards match every valid value. Expressions such as `*/15`, ranges such as `9-11`, and comma-separated lists are supported for the corresponding fields. With `strict=True`, unsupported expressions raise `ValueError`. `crontab.daily()` matches midnight and `crontab.hourly()` matches minute zero.

`huey.periodic_task(matcher, name=...)` registers a periodic task. `read_periodic(timestamp)` returns task messages whose matchers accept that explicit timestamp, preserving their configured names. Returned messages may be enqueued and executed like normal tasks.

## Storage And Introspection

`MemoryStorage(name)` starts with empty queue, schedule, data, result, and counter state. `enqueue(data, priority=...)` and `dequeue()` implement FIFO order among equal priorities while higher numeric priority dequeues first. `enqueued_items()` reports queued payloads in dequeue order. Empty dequeue returns `None`.

`add_to_schedule(data, timestamp)` inserts scheduled payloads. `read_schedule(timestamp)` returns and removes only entries due at or before the supplied timestamp. `scheduled_items()` reports remaining payloads and `schedule_size()` reports their count.

`put_data(key, value, is_result=False)`, `peek_data`, `pop_data`, and `has_data_for_key` expose key/value state. `put_if_empty` writes only when absent and reports whether it wrote. `incr(key, amount=1)` updates counters, and `delete_counter` removes counter state. Result entries are projected through `result_items()` and `result_store_size()`.

`flush_queue`, `flush_schedule`, and `flush_results` clear their respective views. `flush_all` clears all storage views. At the Huey level, `put`, `get(peek=...)`, and `delete` serialize and expose arbitrary data. `huey.flush()` clears pending tasks, scheduled tasks, results, arbitrary data, and held locks.

`huey.lock_task(name)` returns a local task lock. `huey.flush_locks(*names)` releases selected known locks and returns the set of names it released. When no names are provided it releases all discovered task locks.

## Serialization And Signing

`Serializer.serialize(value)` and `deserialize(data)` round-trip nested Python values. With `compression=True`, gzip compression is used by default. With `use_zlib=True`, zlib compression is used. Both compressed routes preserve bytes, mappings, and task payloads.

`SignedSerializer(secret=..., salt=...)` signs serialized payloads and returns the original value when the signature is valid. Altering signed bytes causes `deserialize` to raise `ValueError`. `constant_time_compare(left, right)` returns true for equal byte strings and false for unequal byte strings.

A `MemoryHuey` configured with a compressed serializer must preserve task arguments and stored results through enqueue, dequeue, execution, and result retrieval.

## Signals And Hooks

`huey.signal(*signals)` registers a receiver. With no explicit signal list, it receives all signals. For a successful queued task, signal order is `SIGNAL_ENQUEUED`, `SIGNAL_EXECUTING`, then `SIGNAL_COMPLETE`. `disconnect_signal(receiver, signal)` stops only the selected signal delivery while leaving other registrations active.

`huey.pre_execute()` registers a hook called with the task before invocation. `huey.post_execute()` registers a hook called with task, result value, and exception after invocation. Successful execution passes the returned value and `None` exception.

Failed execution emits `SIGNAL_ERROR` with the original exception object, and the result exposes a `TaskException`. Expired work emits `SIGNAL_EXPIRED`. Revoked work emits `SIGNAL_REVOKED`. Lock rejection emits `SIGNAL_LOCKED`. Receivers observe the same public task name and identity used by queue and result APIs.

## Execution Controls

**Retries.** A task configured with `retries=N` is requeued after failure while attempts remain. A retrying execution returns `None`; a later successful execution stores the successful value. `RetryTask(eta=..., delay=...)` exposes its scheduling options, and `CancelExecution(retry=True)` exposes its retry request.

**Revocation.** `TaskWrapper.revoke()` prevents execution, `is_revoked()` reports state, and `restore()` removes revocation. With `revoke_once=True`, only the next task instance is blocked. A `Result` can revoke and restore its own queued task. Revoked execution returns `None` and produces no normal result value.

**Expiration and priority.** A task whose `expires` timestamp is earlier than the explicit execution timestamp does not invoke its callable or store a result. Among queued tasks, a larger numeric priority executes first.

**Locks.** `lock_task(name)` can be used directly or as a callable decorator. `acquire`, `release`, and `is_locked` project lock state. If a locked decorated task is executed, normal execution is skipped and retrieving its result raises `TaskException`. Leaving a lock context releases the lock so later work may run.

## Rate Limiting

`huey.rate_limit(name, limit=..., per=..., retry=...)` returns a callable rate limiter and decorator. `current_usage()` reports acquired capacity, `acquire()` consumes capacity, and `reset()` clears usage. A decorated task exceeding its limit with `retry=False` does not invoke the callable, returns `None` from execution, and raises `TaskException` on result retrieval.

=== Contract Layer ===

## Product State Model

The central state consists of registered task types, serialized pending messages, scheduled messages with timestamps, result and error records, arbitrary key/value records, counters, lock keys, rate-limit counters, signal receivers, hooks, revocations, and composition links. Each task message carries a stable identifier, registered name, positional arguments, keyword arguments, priority, retry state, and optional scheduling or expiration metadata.

Calling a wrapper creates a message and result handle. Queue and schedule APIs project message location. `execute` transitions a message to success, failure, retry, revoked, expired, locked, or scheduled state. Results, signals, hooks, and compositions project those transitions through independent public views.

## Error Semantics

| Condition | Required result |
|---|---|
| `schedule` called without ETA or delay | Raise `ValueError` |
| Strict crontab receives unsupported expression | Raise `ValueError` |
| Signed payload is altered | Raise `ValueError` |
| Failed task result is retrieved | Raise `TaskException` with public metadata |
| Decorated task cannot acquire its task lock | Retrieval raises `TaskException` |
| Decorated task exceeds a nonretrying rate limit | Retrieval raises `TaskException` |
| Empty memory queue is dequeued | Return `None` |

## Cross-View Invariants

1. A task identifier, name, arguments, and keyword arguments must agree across wrapper creation, serialization, pending views, dequeue, execution, signals, and result lookup.
2. Pending, scheduled, result, lock, and rate-limit counts must reflect the corresponding storage state after every public transition.
3. Immediate and queued modes must invoke the same underlying callable with equivalent arguments and produce equivalent values.
4. A successful queued execution must remove the task from pending state, store its value when enabled, mark its result ready, and emit executing then complete signals.
5. A failed, revoked, expired, locked, or rate-limited task must not expose a normal successful value.
6. Pipeline output must become the next task's input according to tuple, dictionary, or scalar shape, and result order must match execution order.
7. Group and chord member result order must match input task order; chord callbacks must receive the complete ordered member list.
8. Scheduled work must execute only after an explicit due-time read or execution timestamp transition.
9. Consuming a result must update result storage unless preservation was requested.
10. Flush methods must clear exactly the public state they advertise, and all public counts and lock views must agree afterward.

=== Reference Layer ===

## Installable Surface

### Public Import Surface

```python
from huey import CancelExecution, Error, MemoryHuey, RetryTask
from huey import chord, crontab, group
from huey.exceptions import RateLimitExceeded, TaskException, TaskLockedException
from huey.serializer import Serializer, SignedSerializer, constant_time_compare
from huey.signals import (
    SIGNAL_COMPLETE,
    SIGNAL_ENQUEUED,
    SIGNAL_ERROR,
    SIGNAL_EXECUTING,
    SIGNAL_EXPIRED,
    SIGNAL_LOCKED,
    SIGNAL_REVOKED,
)
from huey.storage import MemoryStorage
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `MemoryHuey` | class | In-process task registry, queue, executor, schedule, and result facade. |
| `MemoryStorage` | class | In-memory queue, schedule, data, result, and counter backend. |
| `task` | method/decorator | Registers a callable and returns a task wrapper. |
| `periodic_task` | method/decorator | Registers timestamp-matched periodic work. |
| `Result` | returned object | Tracks task identity, readiness, result, revocation, and rescheduling. |
| `ResultGroup` | returned object | Resolves an ordered set of member results. |
| `group` | function | Builds an ordered collection of tasks. |
| `chord` | function | Builds grouped work followed by a callback. |
| `crontab` | callable helper | Builds timestamp matchers for periodic work. |
| `Serializer` | class | Serializes and optionally compresses Python values. |
| `SignedSerializer` | class | Signs serialized values and validates integrity. |
| `Error` | value type | Stores public task failure metadata. |
| `TaskException` | exception | Exposes failed task metadata on result retrieval. |
| `RetryTask` | exception | Requests retry with optional ETA or delay. |
| `CancelExecution` | exception | Cancels current execution with optional retry. |
| signal constants | constants | Name enqueue, execution, completion, error, expiry, lock, and revocation events. |

### CLI Entry Points

The distribution may install `huey_consumer`, but command-line consumers and background workers are outside this specification. Required workflows use explicit in-process API calls.

## Invocation Protocol

Install the project as a normal Python distribution, create a `MemoryHuey`, declare tasks through its decorators, and drive work through immediate invocation or explicit enqueue, dequeue, schedule-read, and execute calls. Use returned result objects and public counts, storage methods, signals, hooks, and composition objects to observe state. No daemon or external service is involved.

=== Meta Layer ===

## Environment

The working environment runs Python 3.11 on Linux without network access. The third-party package `pytest` is preinstalled and importable. The target package is not pre-installed. Redis, PostgreSQL, and other external services are unavailable.

The project must include standard packaging metadata in `pyproject.toml` or `setup.py` so it installs with pip. Importing the in-process surface must not require optional service clients.

## Evaluation Notes

The implementation is exercised through public imports and deterministic in-process workflows. Checks use unique in-memory instance names, fixed naive timestamps with `utc=False`, explicit queue and schedule transitions, and no sleeps. They do not use network access, external services, background consumers, subprocesses, exact exception prose, exact log text, generated identifier values, private modules, or arbitrary wall-clock delays.
