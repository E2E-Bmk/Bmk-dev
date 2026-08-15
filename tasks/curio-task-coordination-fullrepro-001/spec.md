# Curio Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Curio is a coroutine-based concurrency library for programs written with
`async` and `await`. It provides a runtime for top-level coroutines, managed
tasks, timeouts and cancellation, coordination primitives, and queues. Its
universal coordination objects present one shared state to Curio code,
ordinary threads, and asyncio code.

## Non-Goals

This specification does not define network transport, TLS, channel IPC,
asynchronous file objects, worker pools, monitors, debugging hooks, process
execution, asynchronous-thread bridging, platform-specific behavior, timing
or performance guarantees, object representations, or private implementation
details.

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

```python
from curio import run, spawn, sleep, timeout_after, ignore_after, TaskTimeout

async def slow_work():
    await sleep(10)
    return "done"

async def main():
    result = await ignore_after(0.01, slow_work, timeout_result="timed out")
    assert result == "timed out"

    try:
        async with timeout_after(0.01):
            await sleep(10)
    except TaskTimeout:
        pass
    else:
        raise AssertionError("timeout was not raised")

    task = await spawn(slow_work)
    await task.cancel()
    assert task.terminated

run(main)
```

The `ignore_after` call suppresses the timeout and returns the sentinel value instead of raising. The explicit `timeout_after` context raises `TaskTimeout` when the block exceeds its duration. Cancelling a spawned task sets its `terminated` flag before control returns.

## Task Lifecycle

Tasks represent spawned coroutines with observable lifecycle state including creation, execution, cancellation, and termination.

**Runtime entry.** `run` must execute a coroutine function with the supplied arguments in a new Curio runtime and return its final value when every remaining task has terminated. It must raise `RuntimeError` when called while a Curio task is already running.

**Task creation.** `await spawn(corofunc, *args, daemon=False)` must create and return a `Task` that executes the supplied coroutine function concurrently. It must set `Task.daemon` to the provided flag. It must raise `TypeError` when the supplied arguments do not produce an awaitable coroutine.

**Current task.** `await current_task()` must return the `Task` representing the calling coroutine. It must raise `RuntimeError` when no Curio task is active. The returned object must be the same `Task` that `spawn` returned for that coroutine.

**Task attributes.** A `Task` must expose `id`, `coro`, `daemon`, `state`, `cycles`, `cancelled`, and `terminated`. The `id` must be an increasing integer for newly created tasks.

**Waiting and joining.** `await task.wait()` must return `None` when the task terminates. `await task.join()` must return the task's value when it terminates normally; it must raise `TaskError` with the child exception as its cause when the child fails.

**Result access.** `task.result` and `task.exception` must raise `RuntimeError` when read before the task has terminated. After termination, `result` must return the value or reraise the child exception, and `exception` must return the child exception or `None`.

**Cancellation.** `await task.cancel(blocking=True, exc=TaskCancelled)` must request delivery of the cancellation exception to a running task. When `blocking` is true, it must wait for termination. It must return without error when the task has already terminated. After cancellation, `task.cancelled` must be true and `task.terminated` must be true.

## Task Group Coordination

Task groups manage collections of tasks with configurable completion policies.

**Group construction.** `TaskGroup(tasks=(), wait=all)` must manage only the supplied tasks and tasks added through that group. It must not implicitly absorb tasks created by the top-level `spawn`.

**Wait policies.** `wait=all` must wait for all monitored tasks. `wait=any` must stop after one task terminates and must leave all managed tasks terminated after exit. `wait=object` must stop after a task returns a non-`None` value. `wait=None` must cancel running tasks on exit. In every case, `join()` and managed-block exit must leave no managed task running.

**Adding tasks.** `await group.spawn(corofunc, *args, daemon=False)` must create and add a task and return it. `await group.add_task(task)` must add an ungrouped task. Either operation must raise `RuntimeError` when the group has already joined. `add_task` must raise `RuntimeError` when the task already belongs to a group.

**Consuming results.** `await group.next_done()` must return the next completed task and remove it from the group, or must return `None` when no task remains. `await group.next_result()` must return that task's result and must reraise its child exception; it must raise `RuntimeError` when no task remains. `await group.cancel_remaining()` must cancel and remove all remaining non-daemon tasks.

**Group attributes.** `group.completed`, `group.result`, `group.exception`, `group.results`, `group.exceptions`, and `group.tasks` must describe the joined group's non-daemon tasks. `result`, `exception`, `results`, and `exceptions` must raise `RuntimeError` before the group joins. `result` must raise `RuntimeError` when no successful task completed. `results` must reraise a child failure when a retained task failed. A managed block must cancel its tasks and propagate the block exception when its body exits by exception.

## Timeouts and Cancellation Control

Timeout and cancellation mechanisms control how long operations are permitted to run and how pending cancellations are managed.

**Clock and sleep.** `await clock()` must return Curio's monotonic clock value without creating a scheduling yield. `await sleep(seconds)` must wait for the requested duration and return the monotonic clock value at wake-up; `await sleep(0)` must yield to the next ready task. `sleep` must raise the cancellation exception when the caller is cancelled while waiting.

**Timeout after.** `timeout_after(seconds, corofunc=None, *args)` must return an awaitable that returns the coroutine result when a coroutine is supplied, and must return an asynchronous context manager when it is omitted. It must raise `TaskTimeout` at the current blocking operation when the duration expires.

**Nested timeouts.** For nested timeout contexts, the expired context must receive `TaskTimeout`, while an inner context interrupted by an outer expiry must receive `TimeoutCancellationError`. An uncaught timeout that crosses its matching boundary must raise `UncaughtTimeoutError`.

**Ignore after.** `ignore_after(seconds, corofunc=None, *args, timeout_result=None)` must use the same forms as `timeout_after`. When called with a coroutine that finishes before its duration, it must return the coroutine result. When its duration expires in direct-coroutine form, it must return `None`. In context-manager form, it must set `expired` to `True` and `result` to `timeout_result` when its own duration expires; it must set `expired` to `False` when its block finishes before that duration.

**Cancellation shield.** `disable_cancellation` must defer cancellation while its operation or block is active and must deliver the deferred cancellation at the first later blocking operation after the shield ends. `await check_cancellation()` must raise a pending cancellation when enabled; while disabled it must return the pending exception or `None`. `await set_cancellation(exc)` must replace the caller's pending cancellation.

## Coordination Primitives

Task-local coordination objects provide queues, events, locks, and synchronization for Curio tasks.

**Queue types.** `Queue(maxsize=0)`, `PriorityQueue(maxsize=0)`, and `LifoQueue(maxsize=0)` must provide task-local queues. `maxsize=0` must mean no capacity limit. Each queue must provide `empty()`, `full()`, `qsize()`, `await get()`, `await put(item)`, `await join()`, and `await task_done()`.

**Queue ordering.** `Queue` must return items in insertion order. `PriorityQueue` must return the lowest comparable item first. `LifoQueue` must return the most recently inserted item first. A `PriorityQueue` operation must raise the underlying comparison error when items cannot be ordered.

**Queue capacity and work tracking.** `get()` must wait when its queue has no available item. `put(item)` must wait when a positive `maxsize` has been reached and must complete when a consumer makes space. Every successful `put(item)` must create one unfinished-work obligation. `task_done()` must remove one such obligation. `join()` must return only after all obligations have been acknowledged.

**Event.** `Event()` must provide `is_set()`, `clear()`, `await set()`, and `await wait()`. `set()` must make `is_set()` true and wake every current waiter. `clear()` must make it false. `wait()` must return when the event is set and must wait while it is clear.

**Result.** `Result()` must provide `is_set()`, `await set_value(value)`, `await set_exception(exc)`, and `await unwrap()`. A result must become set after a value or exception is supplied. `unwrap()` must return the supplied value and must reraise the supplied exception.

**Lock and RLock.** `Lock()` and `RLock()` must provide `await acquire()`, `await release()`, `locked()`, and asynchronous context-manager support. `Lock.acquire()` must wait while another task holds the lock. `RLock.acquire()` must permit the owning task to acquire recursively and must require a matching number of releases. `RLock.release()` must raise `RuntimeError` when a non-owner releases it.

**Semaphore.** `Semaphore(value=1)` must provide `await acquire()`, `await release()`, `locked()`, and asynchronous context-manager support. `acquire()` must wait when its value is zero. `release()` must make a waiting acquisition eligible to proceed.

**Condition.** `Condition(lock=None)` must use the supplied lock or a new `Lock`. It must provide lock operations plus `await wait()`, `await wait_for(predicate)`, `await notify(n=1)`, and `await notify_all()`. `wait()` must release the lock while waiting and reacquire it before returning. `wait()` and `notify()` must raise `RuntimeError` when their lock is not held. `wait_for(predicate)` must return the predicate's value only when it becomes truthy.

## Universal Coordination

Universal coordination objects expose one shared state to ordinary threads, Curio coroutines, and asyncio coroutines.

**UniversalQueue.** `UniversalQueue(maxsize=0, withfd=False)` must expose one FIFO queue to all three environments. `get`, `put`, `join`, and `task_done` must be synchronous in a thread and awaitable in Curio or asyncio. A call must observe the same items regardless of the environment that supplied them. `fileno()` must return a polling descriptor when `withfd=True` and must raise `AssertionError` when `withfd=False`.

**UniversalEvent.** `UniversalEvent()` must expose one event flag to all three environments. `is_set()` and `clear()` must be synchronous. `set()` and `wait()` must be synchronous in a thread and awaitable in Curio or asyncio. `set()` must wake every current waiter. `clear()` must reset the shared flag.

**UniversalResult.** `UniversalResult()` must expose one value-or-exception outcome to all three environments. `is_set()` must report whether a value or exception has been supplied. `set_value(value)`, `set_exception(exc)`, and `unwrap()` must be synchronous in a thread and awaitable in Curio or asyncio. `unwrap()` must wait for the shared outcome, return its value, or reraise its supplied exception. An exception set in one environment must be reraised unchanged from `unwrap()` in every other environment.

## State Model

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

## Error Semantics

Exception class hierarchy: `CancelledError` must be the base class for cancellation-related failures. `TaskCancelled` must identify direct cancellation. `TaskTimeout` must identify an expired matching timeout. `TimeoutCancellationError` must identify an interruption caused by a different active timeout. `TaskError` must identify a failed joined task and preserve its child exception as the exception cause. `UncaughtTimeoutError` must identify an improperly escaped timeout.

Condition-to-result mappings:

- When `run()` is called while a Curio task is already running, it must raise `RuntimeError`.
- When `spawn` receives a `corofunc(*args)` that does not produce an awaitable coroutine, it must raise `TypeError`.
- When `current_task()` is called with no active Curio task, it must raise `RuntimeError`.
- When `task.result` or `task.exception` is read before the task has terminated, it must raise `RuntimeError`.
- When `task.join()` is awaited and the child task failed, it must raise `TaskError` with the child exception as its cause.
- When `group.spawn()` or `group.add_task()` is called after the group has already joined, it must raise `RuntimeError`.
- When `group.add_task()` is called with a task that already belongs to a group, it must raise `RuntimeError`.
- When `group.next_result()` is called with no remaining task, it must raise `RuntimeError`.
- When `group.result` is read and no successful task completed, it must raise `RuntimeError`.
- When `group.result`, `group.exception`, `group.results`, or `group.exceptions` is read before the group joins, it must raise `RuntimeError`.
- When `group.results` is read and a retained task failed, it must reraise the child failure.
- When a `PriorityQueue` operation encounters items that cannot be ordered, it must raise the underlying comparison error.
- When `UniversalQueue.fileno()` is called with `withfd=False`, it must raise `AssertionError`.
- When `RLock.release()` is called by a non-owner task, it must raise `RuntimeError`.
- When `Condition.wait()` or `Condition.notify()` is called without the lock held, it must raise `RuntimeError`.
- When a timeout context expires, the expired context must receive `TaskTimeout`, while an inner context interrupted by an outer expiry must receive `TimeoutCancellationError`.
- When an uncaught timeout crosses its matching boundary, it must raise `UncaughtTimeoutError`.

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

## Public Interface

### Import Surface

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

### API Catalog

| Name | Kind | Role |
|---|---|---|
| run | function | Execute a coroutine in a new Curio runtime |
| spawn | coroutine | Create and return a concurrent Task |
| current_task | coroutine | Return the Task for the calling coroutine |
| Task | class | Represents a spawned coroutine with lifecycle state |
| TaskGroup | class | Manage a group of tasks with configurable wait policy |
| clock | coroutine | Return monotonic clock value without yielding |
| sleep | coroutine | Suspend for a duration and return wake-up time |
| timeout_after | function | Raise TaskTimeout when a duration expires |
| ignore_after | function | Suppress timeout and return a sentinel on expiry |
| disable_cancellation | function | Defer cancellation during an operation or block |
| check_cancellation | coroutine | Inspect or clear a pending cancellation |
| set_cancellation | coroutine | Replace the caller's pending cancellation |
| Queue | class | Task-local FIFO queue |
| PriorityQueue | class | Task-local priority-ordered queue |
| LifoQueue | class | Task-local last-in-first-out queue |
| Event | class | Task-local event flag for signalling |
| Result | class | One-shot value-or-exception delivery |
| Lock | class | Mutual exclusion lock for Curio tasks |
| RLock | class | Reentrant mutual exclusion lock |
| Semaphore | class | Counting semaphore for Curio tasks |
| Condition | class | Condition variable with an associated lock |
| UniversalQueue | class | Cross-environment FIFO queue |
| UniversalEvent | class | Cross-environment event flag |
| UniversalResult | class | Cross-environment value-or-exception outcome |

### CLI Entry Points

There is no console script for this package. `python -m curio` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Validation covers public imports, runtime execution, task and task-group lifecycles, cancellation and timeouts, queues, synchronization primitives, universal coordination objects, documented errors, and cross-view invariants. Checks exercise independently observable behavior across Curio coroutines, ordinary threads, and asyncio where supported. Network operations, performance guarantees, private implementation details, and exact object representations are not considered.
