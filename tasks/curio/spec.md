# Curio Specification

## Product Overview

Curio is a coroutine-based concurrency library for programs written with
`async` and `await`. It provides a runtime for top-level coroutines, managed
tasks, timeouts and cancellation, coordination primitives, and queues. Its
universal coordination objects present one shared state to Curio code,
ordinary threads, and asyncio code.

## Scope

This specification covers top-level execution; task and task-group lifecycle;
cancellation and timeout control; FIFO, priority, and LIFO queues; task-local
synchronization; and universal queues, events, and results. Public operations
must be used from a running Curio coroutine unless the operation is described
as usable synchronously or from asyncio below.

## Installable Surface

Applications import the following names directly from `curio`:

```python
from curio import (
    run, Task, TaskGroup, spawn, current_task,
    clock, sleep, timeout_after, ignore_after,
    disable_cancellation, check_cancellation, set_cancellation,
    Queue, PriorityQueue, LifoQueue, UniversalQueue,
    Event, UniversalEvent, Lock, RLock, Semaphore, Condition,
    Result, UniversalResult,
    CurioError, CancelledError, TaskCancelled, TaskTimeout,
    TimeoutCancellationError, UncaughtTimeoutError, TaskError,
)
```

`run(corofunc, *args, with_monitor=False, selector=None, debug=None)`
must execute `corofunc(*args)` in a new Curio runtime and return its final
value when every remaining task has terminated. It must raise `RuntimeError`
when called while a Curio task is already running.

## Public API

### Product State Model

Curio exposes one coordination state through three public projections:

1. A **task projection** records each spawned coroutine's completion,
   outcome, cancellation state, and group membership.
2. A **coordination projection** records queued items and unfinished work,
   event flags, result delivery, and ownership or availability of task-local
   synchronization primitives.
3. A **universal projection** exposes one queue, event, or result state to
   synchronous threads, Curio coroutines, and asyncio coroutines.

The task projection must report a spawned task as terminated before `wait()`
or `join()` returns for that task. The coordination projection must retain an
item's unfinished-work obligation after `get()` returns it and before
`task_done()` acknowledges it. The universal projection must expose the same
completion or item state regardless of which supported execution environment
writes it.

### Tasks and Task Groups

`await spawn(corofunc, *args, daemon=False)` must create and return a `Task`
that executes `corofunc(*args)` concurrently. It must set `Task.daemon` to the
provided flag; a daemon task's outcome must be disregarded by a task group. It
must raise `TypeError` when `corofunc(*args)` does not produce an awaitable
coroutine.

`await current_task()` must return the `Task` representing the calling
coroutine. It must raise `RuntimeError` when no Curio task is active.

A `Task` must expose `id`, `coro`, `daemon`, `state`, `cycles`, `cancelled`,
and `terminated`. `id` must be an increasing integer for newly created tasks.
`await task.wait()` must return `None` when the task terminates. `await
task.join()` must return the task's value when the task terminates normally;
it must raise `TaskError` with the child exception as its cause when the child
fails. `task.result` and `task.exception` must raise `RuntimeError` when read
before termination; after termination, `result` must return the value or
reraise the child exception, and `exception` must return the child exception
or `None`.

`await task.cancel(*, blocking=True, exc=TaskCancelled)` must request delivery
of `exc` to a running task. It must wait for termination when `blocking` is
true and must return without waiting when `blocking` is false. It must return
without error when the task has already terminated. A repeated cancellation
request must wait for the already-requested cancellation rather than inject a
second one.

`TaskGroup(tasks=(), *, wait=all)` must manage only the supplied tasks and
tasks added through that group; it must not implicitly absorb tasks created by
the top-level `spawn`. `wait=all` must wait for all monitored tasks; `wait=any`
must stop after a task terminates; `wait=object` must stop after a task returns
a non-`None` value; and `wait=None` must cancel running tasks on exit. In every
case, `join()` and managed-block exit must leave no managed task running.

`await group.spawn(corofunc, *args, daemon=False)` must create and add a task
and return it. `await group.add_task(task)` must add an ungrouped task. Either
operation must raise `RuntimeError` when the group has already joined, and
`add_task` must raise `RuntimeError` when the task already belongs to a group.
`await group.next_done()` must return the next completed task and remove it
from the group, or must return `None` when no task remains. `await
group.next_result()` must return that task's result and must reraise its child
exception; it must raise `RuntimeError` when no task remains. `await
group.cancel_remaining()` must cancel and remove all remaining non-daemon
tasks.

`group.completed`, `group.result`, `group.exception`, `group.results`,
`group.exceptions`, and `group.tasks` must describe the joined group's
non-daemon tasks. `result`, `exception`, `results`, and `exceptions` must
raise `RuntimeError` before the group joins. `result` must raise `RuntimeError`
when no successful task completed, and `results` must reraise a child failure
when a retained task failed. A managed block must cancel its tasks and
propagate the block exception when its body exits by exception.

### Timeouts and Cancellation

`await clock()` must return Curio's monotonic clock value without creating a
scheduling yield or delivering cancellation. `await sleep(seconds)` must wait
for the requested duration and return the monotonic clock value at wake-up;
`await sleep(0)` must yield to the next ready task when one exists. `sleep`
must raise the runtime's cancellation exception when the caller is cancelled
while waiting.

`timeout_after(seconds, corofunc=None, *args)` must return an awaitable that
returns `corofunc(*args)` when a coroutine is supplied, and must return an
asynchronous context manager when it is omitted. It must raise `TaskTimeout`
at the current blocking operation when the matching duration expires. For
nested timeout contexts, the expired context must receive `TaskTimeout`, while
an inner context interrupted by an outer expiry must receive
`TimeoutCancellationError`; an uncaught timeout that crosses its matching
boundary must raise `UncaughtTimeoutError`.

`ignore_after(seconds, corofunc=None, *args, timeout_result=None)` must use
the same forms as `timeout_after`. Its direct coroutine form must return the
coroutine result when it finishes before its duration and must return `None`
when its duration expires, including when `timeout_result` is supplied. Its
context-manager form must set `expired` to `True` and `result` to
`timeout_result` when its own duration expires; it must set `expired` to
`False` when its block finishes before that duration.

`disable_cancellation(corofunc=None, *args)` must return an awaitable for a
provided coroutine and an asynchronous context manager otherwise. It must
defer cancellation while its operation or block is active, and it must deliver
the deferred cancellation at the first later blocking operation after the
shield ends. `await check_cancellation(exc_type=None)` must raise a pending
cancellation when cancellation is enabled; while cancellation is disabled it
must return the pending exception or `None`, and it must clear and return it
when `exc_type` matches. `await set_cancellation(exc)` must replace the
caller's pending cancellation, return the previously pending exception or
`None`, and must cause the supplied exception to be raised at the next
blocking operation when cancellation is enabled.

### Queues

`Queue(maxsize=0)`, `PriorityQueue(maxsize=0)`, and `LifoQueue(maxsize=0)`
must provide task-local queues. `maxsize=0` must mean no capacity limit. Each
queue must provide `empty()`, `full()`, `qsize()`, `await get()`, `await
put(item)`, `await join()`, and `await task_done()`.

`get()` must wait when its queue has no available item and must return one item
when an item becomes available. `put(item)` must wait when a positive `maxsize`
has been reached and must complete when a consumer makes space. `Queue` must
return items in insertion order; `PriorityQueue` must return the lowest
comparable item first; `LifoQueue` must return the most recently inserted item
first. A `PriorityQueue` operation must raise the underlying comparison error
when queued items cannot be ordered.

Every successful `put(item)` must create one unfinished-work obligation.
`task_done()` must remove one such obligation. `join()` must return only after
all obligations created before or while it waits have been acknowledged. These
queues must not offer a cross-thread or foreign-event-loop coordination
guarantee.

### Synchronization

`Event()` must provide `is_set()`, `clear()`, `await set()`, and `await wait()`
for Curio tasks. `set()` must make `is_set()` true and wake every current
waiter; `clear()` must make it false. `wait()` must return when the event is
set and must wait while it is clear.

`Result()` must provide `is_set()`, `await set_value(value)`, `await
set_exception(exc)`, and `await unwrap()`. A result must become set after a
value or exception is supplied. `unwrap()` must return the supplied value and
must reraise the supplied exception.

`Lock()`, `RLock()`, and `Semaphore(value=1)` must provide `await acquire()`,
`await release()`, `locked()`, and asynchronous context-manager support.
`Lock.acquire()` must wait while another task holds the lock; `RLock.acquire()`
must permit the owning task to acquire recursively and must require a matching
number of releases; `RLock.release()` must raise `RuntimeError` when a
non-owner releases it. `Semaphore.acquire()` must wait when its value is zero,
and `Semaphore.release()` must make a waiting acquisition eligible to proceed.

`Condition(lock=None)` must use the supplied lock or a new `Lock`, and must
provide lock operations plus `await wait()`, `await wait_for(predicate)`,
`await notify(n=1)`, and `await notify_all()`. `wait()` must release the lock
while waiting and reacquire it before returning. `wait()` and `notify()` must
raise `RuntimeError` when their lock is not held. `wait_for(predicate)` must
return the predicate's value only when it becomes truthy.

### Universal Coordination

`UniversalQueue(*, maxsize=0, withfd=False)` must expose one FIFO queue to
ordinary threads, Curio coroutines, and asyncio coroutines. `get`, `put`,
`join`, and `task_done` must be synchronous in a thread and awaitable in Curio
or asyncio. A call must observe the same items and unfinished-work obligations
regardless of the environment that supplied them. `put` must block or await
when a positive capacity is full; `get` must block or await when no item is
available; and `join` must block or await until every successful put has a
matching `task_done`. `fileno()` must return a polling descriptor when
`withfd=True` and must raise `AssertionError` when `withfd=False`.

`UniversalEvent()` must expose one event flag to ordinary threads, Curio
coroutines, and asyncio coroutines. `is_set()` and `clear()` must be
synchronous. `set()` and `wait()` must be synchronous in a thread and
awaitable in Curio or asyncio. `set()` must wake every current waiter, and
`wait()` must return immediately when the flag is already set.

`UniversalResult()` must expose one value-or-exception outcome to ordinary
threads, Curio coroutines, and asyncio coroutines. `is_set()` must report
whether a value or exception has been supplied. `set_value(value)`,
`set_exception(exc)`, and `unwrap()` must be synchronous in a thread and
awaitable in Curio or asyncio. `unwrap()` must wait for the shared outcome,
return its value, or reraise its supplied exception.

## Error Semantics

`CancelledError` must be the base class for cancellation-related failures.
`TaskCancelled` must identify direct cancellation, and `TaskTimeout` must
identify an expired matching timeout. `TimeoutCancellationError` must identify
an interruption caused by a different active timeout. `TaskError` must identify
a failed joined task and preserve its child exception as the exception cause.
`UncaughtTimeoutError` must identify an improperly escaped timeout.

## Cross-View Invariants

1. A `Task` returned by `spawn` must be the object returned by `current_task`
   while its coroutine is executing.
2. A task's `terminated` flag must be true when a waiter returns from that
   task's `wait()` or `join()`.
3. A child outcome must return through `Task.join()` and through the matching
   `TaskGroup` result projection, with a child failure raising through both.
4. Every successful queue `put` must remain unfinished after `get` returns its
   item and must cease to be unfinished only after `task_done`.
5. A `UniversalQueue` item inserted synchronously must return from an awaited
   `get`, and an item inserted with awaited `put` must return from synchronous
   `get`.
6. A `UniversalEvent` set in one supported environment must make `is_set()`
   return true and must release waiters in every supported environment.
7. A `UniversalResult` value or exception set in one supported environment
   must return or raise unchanged from `unwrap()` in every supported
   environment.
8. A timeout suppressed by `ignore_after` must report expiration through its
   context object and must not escape as `TaskTimeout` from that context.

## Representative Workflows

```python
from curio import Queue, TaskGroup, run

async def worker(queue):
    item = await queue.get()
    try:
        return item * 2
    finally:
        await queue.task_done()

async def main():
    queue = Queue()
    async with TaskGroup() as group:
        await queue.put(21)
        job = await group.spawn(worker, queue)
        await queue.join()
    return job.result

assert run(main) == 42
```

The queue's unfinished work is acknowledged before `join()` returns, and the
task group's managed-block exit leaves the worker terminated before its result
is read.

## Non-Goals

This specification does not define network transport, TLS, channel IPC,
asynchronous file objects, worker pools, monitors, debugging hooks, process
execution, asynchronous-thread bridging, platform-specific behavior, timing
or performance guarantees, object representations, or private implementation
details.
