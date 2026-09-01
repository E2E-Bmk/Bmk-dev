# Curio service workflow runtime

## Overview

This package is a compact structured-concurrency runtime for services that move
framed data through real local sockets, perform bounded work in ordinary
threads, propagate task-local context, finalize asynchronous generators, and
coordinate restartable work across Curio tasks and foreign threads.

One public fact has one lifecycle even when it is projected through several
objects.  Socket flow-control credit, worker ownership, context snapshots,
generator finalization, queue obligations, cleanup failures, and workflow
leases must stay consistent through cancellation, half-close, retirement, and
restart.

Filesystem I/O, TLS, subprocesses, signals, command-line tools, remote network
services, and private scheduler inspection are outside this contract.

## Public surface and call forms

The ordinary Curio names below remain importable and retain their usual public
behavior:

```text
run, spawn, run_in_thread, Task, TaskGroup,
Event, Lock, Queue, UniversalQueue, Result,
timeout_after, disable_cancellation, check_cancellation,
CurioError, CancelledError, TaskCancelled, TaskTimeout, TaskError
```

The service-workflow surface is also importable directly from `curio`:

```text
StreamEOF, BrokenStreamError, ClosedStreamError,
SocketStreamStatistics, open_socket_stream_pair,
WorkerCancelled, WorkerJobError, WorkerPoolStatistics,
ThreadWorkerPool, WorkerJob,
TaskLocal, ContextSnapshot, capture_context,
GeneratorCleanupError, AsyncGeneratorScope,
CleanupError, AsyncResourceStack,
WorkLease, WorkflowSnapshot, WorkflowCoordinator
```

`run(corofunc, *args)` is synchronous.  Runtime operations, socket operations,
worker-pool operations, workflow operations, and cleanup are awaited unless
explicitly named as a synchronous projection or `*_sync` method.

## Runtime, tasks, cancellation, and ownership

`run()` returns the exact top-level value and reraises the exact top-level
failure.  It enables context-variable-aware tasks by default.  A spawned child
inherits the parent's context snapshot; changes made by one child do not leak
to its parent or siblings.

`Task.join()` returns a child result.  A crashed child raises `TaskError` whose
cause is the exact child failure.  An explicit cancellation exception instance
is delivered unchanged.  Cancellation rolls back a wait that has not committed
and does not undo a committed transfer.

Task groups own their children until group exit has completed child finalizers.
A child failure cancels remaining children, waits for their `finally` blocks,
and preserves the outward failure object.

## Local and universal coordination

Events, locks, queues, timeouts, and cancellation masks retain their normal
Curio semantics.  Queue capacity and unfinished-work accounting are independent:
successful `put()` creates an obligation, `get()` transfers without acknowledging,
`task_done()` acknowledges once, and `join()` waits for all obligations.

`UniversalQueue` has one FIFO and one unfinished-work ledger shared by Curio
tasks, ordinary threads, and an asyncio loop in another operating-system thread.
A cancelled uncommitted getter leaves no ghost consumer.

## Real framed socket streams

`await open_socket_stream_pair(frame_limit=1)` returns two connected full-duplex
endpoints backed by real local stream sockets.  `frame_limit` is a positive
integer and applies independently in each direction.  Each endpoint exposes a
live non-negative `fileno()` until closed.

`await endpoint.send_frame(data)` accepts a bytes-like value, freezes it as
`bytes`, and transmits one length-delimited frame.  `receive_frame()` returns one
complete frame, preserving boundaries and FIFO order.  A frame consumes one
directional credit from admission until its peer receives the complete frame.
Later senders apply backpressure while credit is exhausted.

`statistics()` returns `SocketStreamStatistics` with the endpoint's file
descriptor, outbound admitted-frame count, outbound blocked-sender count,
send-half state, receive-half state, peer receive state, and receive generation.
`wait_backpressured()` waits until at least one outbound sender is queued and
returns the current blocked-sender count.  It is a diagnostic lifecycle wait,
not a scheduling hint.

Cancelling a sender while it is waiting for credit commits no bytes or frame and
does not consume later credit.  Cancelling a receiver before any byte of its
next frame is available consumes no future frame.  `restart_receive()` starts a
new receive generation after such interruption and returns the new generation
number without replacing the socket.

`send_eof()` is idempotent and half-closes only the endpoint's send direction.
Already admitted frames drain before the peer raises `StreamEOF`; the reverse
direction remains usable.  `aclose_receive()` discards the endpoint's inbound
protocol state and makes blocked or future peer sends raise
`BrokenStreamError`.  Operations initiated on an endpoint direction already
closed by itself raise `ClosedStreamError` when no peer failure controls them.
`aclose()` closes both directions, is idempotent, and wakes blocked peers.

## Bounded thread-worker lifecycle

`ThreadWorkerPool(limit=1)` is an asynchronous context manager.  `limit` is a
positive integer bounding concurrently executing ordinary threads.
`await submit(callable, *args, context=None)` waits for capacity, starts the
callable in a real worker thread, and returns a `WorkerJob`.  By default the job
captures the submitter's context at admission.  A supplied `ContextSnapshot`
replaces that default.  Subsequent context changes do not affect admitted work.

Jobs remain owned by their pool until pool close has waited for every underlying
thread, including retired work.  `jobs` is persistent creation order and
`completed` is underlying thread-completion order.  `WorkerJob.join()` returns a
successful result.  Failure raises `WorkerJobError` whose cause is the exact
worker exception.

`await job.cancel(exc=None)` publishes cancellation immediately.  The supplied
`WorkerCancelled` instance is preserved; otherwise a fresh one is made.  Python
threads are not forcibly stopped: running work becomes retiring, its eventual
value or exception is stored only in `late_result` or `late_exception`, and it
never replaces the published cancellation.  `wait_retired()` waits for the real
thread to finish.

Pool `statistics()` reports generation, limit, active thread count, submitters
waiting for capacity, job count, retired count, closing, and closed.  The public
`wait_for_submitters(count=1)` and `wait_closing()` lifecycle waits allow service
controllers to coordinate without sleeps.  `aclose()` rejects new submissions,
waits for all admitted work, and releases ownership.  `restart()` is permitted
after close, advances the generation, and admits new work while preserving job
history.

## Task-local context and snapshots

`TaskLocal(name, default=...)` wraps a real `contextvars.ContextVar`.
`get()`, `set(value)`, and `reset(token)` have the corresponding context-variable
semantics.  `bind(value)` returns an asynchronous context manager that restores
the previous value on exit, including exceptional exit.

`capture_context(*locals)` returns an immutable `ContextSnapshot`.  With no
arguments it captures the complete current context.  With explicit `TaskLocal`
objects it captures those bindings.  A snapshot can be supplied to worker
submission and its `run(callable, *args)` executes synchronous code under the
captured bindings without changing the caller's context.

## Asynchronous-generator finalization

`AsyncGeneratorScope` is an asynchronous context manager.  `track(generator)`
registers an asynchronous generator and returns it.  Registrations finalize
exactly once in reverse registration order.  Each generator is finalized under
the task-local context captured when it was registered.  Cancellation and body
failure do not skip finalization.

`finalization_errors` is the tuple of original failures in finalization attempt
order.  A body failure remains outward.  Without a body failure, one finalizer
failure is reraised unchanged and multiple failures raise
`GeneratorCleanupError`, whose `exceptions` tuple contains the originals.
Repeated `aclose()` is a no-op.

## Deterministic asynchronous resource cleanup

`AsyncResourceStack` is an asynchronous context manager.  `push()` registers an
object with `aclose()` or a zero-argument callback.  `push_concurrent(*items)`
registers a non-empty concurrent cleanup phase.  Entries unwind once in LIFO
phase order.  Every member of a concurrent phase starts and is attempted even if
another fails.  Concurrent-phase errors are recorded in registration order;
the overall `cleanup_errors` tuple follows LIFO phase order.

Cleanup is cancellation-shielded.  A body exception remains outward while
cleanup failures stay observable.  With no body exception, one cleanup error is
reraised unchanged and multiple errors raise `CleanupError` with an `exceptions`
tuple.  Repeated close is a no-op.

## Restartable workflow coordination

`WorkflowCoordinator(limit=0)` owns universal ingress and result queues.  Zero
means unbounded.  `await submit(payload)` and `submit_sync(payload)` assign a
stable integer work id and create one ingress obligation.  `claim()` returns a
`WorkLease` containing id, payload, current epoch, and attempt number.

`ack(lease, result)` accepts only the currently active lease, acknowledges its
ingress obligation, publishes one result record, and makes the work terminal.
`retire(lease, requeue=True)` acknowledges the current attempt; when requeued it
creates a new obligation for the same id with a higher attempt number.  `restart()`
advances the epoch; already queued work is claimed in the new epoch.  Stale,
duplicate, or foreign leases raise `RuntimeError` without changing accounting.

`receive_result()` returns and acknowledges the next `(work_id, result)` pair.
`join()` waits until ingress obligations are zero.  `snapshot()` returns a
`WorkflowSnapshot` with epoch, queued, active, finished, retired, and total
submission counts.  The queues remain available through `ingress` and `results`
for universal observation, but workflow state changes go through coordinator
methods.

## Cross-component invariants

1. Socket credit is released only by complete peer receive or peer-side teardown.
2. Half-close, receive close, full close, and receive generation are distinct.
3. Worker cancellation publishes before the real thread retires; pool close still
   owns and waits for the late completion.
4. Task-local inheritance, worker snapshots, and generator-registration snapshots
   are independent projections of context at their documented commit points.
5. Generator and resource cleanup are complete, one-shot, and preserve outward
   body or cancellation failures.
6. Workflow lease retirement transfers obligation exactly once before retry.
7. System shutdown includes socket wakeup, worker retirement, task-group
   finalizers, resource cleanup, and universal acknowledgement.
8. Correctness never depends on wall-clock sleeps, exact scheduler turns, private
   queues, or exact error text.

