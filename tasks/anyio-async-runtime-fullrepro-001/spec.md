# AnyIO Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

AnyIO is an asynchronous networking and concurrency library that presents one public API over `asyncio` and Trio. Code written against AnyIO must run on either backend when the selected backend is installed. The library supplies structured concurrency, cancellation scopes, async streams, networking, subprocesses, worker threads, worker processes, subinterpreters, async file and temporary-file APIs, synchronization primitives, testing support, typed attributes and small async variants of `functools` and `itertools`.

## Non-Goals

- This specification does not require Internal backend modules, private helper names, private attributes, private task scheduling details, or exact internal data structures.
- This specification does not require Raw sockets, SCTP, Windows signal behavior beyond Python platform errors, third-party backends that are not installed, or network access outside local resources.
- This specification does not require Exact debug string formattingexcept where an exception class, warning class, return type, or documented status value is part of the public API.

## Representative Workflows

```python
from anyio import (
    TASK_STATUS_IGNORED,
    connect_tcp,
    create_memory_object_stream,
    create_task_group,
    create_tcp_listener,
    move_on_after,
    run,
)
from anyio.abc import SocketAttribute, TaskStatus


async def echo_server(port: int, *, task_status: TaskStatus[int] = TASK_STATUS_IGNORED):
    async def handle(stream):
        async with stream:
            payload = await stream.receive()
            await stream.send(payload[::-1])

    async with await create_tcp_listener(local_host="127.0.0.1", local_port=port) as listener:
        task_status.started(listener.extra(SocketAttribute.local_port))
        await listener.serve(handle)


async def main():
    send, receive = create_memory_object_stream[bytes](1)
    async with create_task_group() as tg:
        handle = await tg.start(echo_server, 0, return_handle=True)
        port = handle.start_value

        async with await connect_tcp("127.0.0.1", port) as stream:
            await stream.send(b"abc")
            await send.send(await stream.receive())

        with move_on_after(1) as scope:
            result = await receive.receive()
            assert result == b"cba"
            assert not scope.cancelled_caught

        tg.cancel_scope.cancel()


run(main)
```

This workflow must start a listener inside a task group, report readiness through `TaskGroup.start()`, connect a client, move data through a memory object stream, observe timeout state, and cancel the serving task group cleanly.

## Running and Structured Concurrency

This section covers event loop entry, timing, cancellation scopes, and structured task management through task groups and task handles.

**Event loop entry.** `run` must call a coroutine function with the supplied positional arguments and return its result. When `backend` names an unrecognized or unavailable backend, `run` must raise `LookupError`. When an async event loop is already running in the current thread, it must raise `RuntimeError`. `get_all_backends` must return `("asyncio", "trio")`. `get_available_backends` must return only built-in backends importable in the current environment, and its result must be a subset of `get_all_backends`.

**Timing and sleep.** `sleep` must suspend the current task for the specified delay. `sleep_forever` must suspend the current task until cancellation. `sleep_until` must suspend until the given monotonic-clock deadline and must return immediately when the deadline is in the past. `current_time` must return the backend's monotonic clock value as a float and must advance across sleep calls. Both `current_time` and `get_cancelled_exc_class` must raise `NoEventLoopError` when no supported event loop is active.

**Cancellation scopes.** `CancelScope` must be a synchronous context manager whose `cancel` method cancels the scope and nested scopes. When `move_on_after` is given a delay, it must return a cancel scope that suppresses its own timeout cancellation and records it via `cancelled_caught`. When `fail_after` is given a delay, it must raise `TimeoutError` when the deadline is reached before the context exits. `current_effective_deadline` must return the nearest active deadline, `inf` when no deadline applies, and `-inf` when the current scope is already effectively cancelled.

**Task groups.** `create_task_group` must return an async context manager with a `cancel_scope`. Leaving the context must wait for every child task. If the context body or any child task raises, the task group must cancel the remaining children and must propagate the raised exception or an exception group when multiple errors occur.

**Task spawning and startup.** `start_soon` and `create_task` on a task group must return a `TaskHandle`. `start` must wait until the target calls `task_status.started` with a value. When `return_handle` is false, `start` must return that value directly. When `return_handle` is true, `start` must return a `TaskHandle` whose `start_value` is that value. If the target exits without calling `started`, `start` must raise `RuntimeError`.

**Task handle lifecycle.** A `TaskHandle` must track statuses `PENDING`, `FINISHED`, `CANCELLING`, `CANCELLED`, and `FAILED`. Awaiting a handle must return the task result when finished, raise `TaskCancelled` when cancelled, and raise `TaskFailed` when the task raised a non-cancellation exception. `return_value` must raise `TaskNotFinished` for pending tasks, `TaskCancelled` for cancelled tasks, and `TaskFailed` for failed tasks. `exception` must return the task exception for failed tasks, return `None` for successful tasks, and raise `TaskNotFinished` or `TaskCancelled` for pending or cancelled tasks. `cancel` must request cancellation and must have no effect after the task has finished. `start_value` must raise `RuntimeError` when the task was not started via `start`.

## Streams and Networking

AnyIO provides stream-based I/O for bytes, typed objects, and networking over TCP, UDP, UNIX sockets, and TLS.

**Byte streams.** Byte streams must send and receive arbitrary chunks of bytes without preserving send boundaries. Reading from a byte stream whose peer closed cleanly must raise `EndOfStream`; it must not return empty bytes as the EOF signal. Object streams must deliver Python objects according to the concrete stream's contract.

**Memory object streams.** `create_memory_object_stream` must return a `(send_stream, receive_stream)` pair. The default buffer size is zero, so `send` must block until a receiver accepts the item. When `max_buffer_size` is a non-negative integer or `math.inf`, the buffer must hold that many items; invalid values including non-integer floats and negative numbers must raise `ValueError`. Passing `item_type` must issue `DeprecationWarning`. Each sent item must be delivered to exactly one receiver even when receive clones exist. The `clone` method on either end must produce an additional independent handle for the same end. Each send or receive end is considered open until all clones of that end are closed. The receive side's async iteration must stop only after all send clones have been closed and buffered items have been consumed. Memory object streams must support synchronous `close` and context manager close in addition to `aclose`. Nowait operations must raise `WouldBlock` when the operation would block, `ClosedResourceError` when the same end is closed, and `BrokenResourceError` when the opposite end is fully closed.

**Buffered byte streams.** `BufferedByteReceiveStream` wraps a byte receive stream and keeps an internal read buffer. `receive_exactly` must return exactly the requested number of bytes or raise `IncompleteRead` when EOF happens first. `receive_until` must return bytes before the delimiter, raise `DelimiterNotFound` when the delimiter is absent from the first `max_bytes` buffered bytes, and raise `IncompleteRead` when EOF arrives first. `feed_data` must prepend externally supplied bytes to subsequent receives according to the buffer order.

**Text and stapled streams.** `TextReceiveStream`, `TextSendStream`, and `TextStream` must decode and encode text over byte streams with the configured `encoding` and error policy. Decode or encode failures must raise the corresponding Python codec exception. `StapledByteStream` and `StapledObjectStream` must expose one bidirectional stream from compatible send and receive halves; closing the stapled stream must close both halves, and send EOF must be forwarded to the send half when supported.

**TLS streams.** `TLSStream.wrap` and `TLSConnectable.connect` must perform a TLS handshake over an existing byte stream. `TLSListener` must wrap accepted byte streams and pass TLS streams to the handler. TLS shutdown must follow the `standard_compatible` setting; TLS handshake or transport failures must propagate to the caller or configured handshake error handler.

**TCP networking.** `connect_tcp` must return a socket byte stream to the specified remote host and port. When `tls` is set to `True`, a non-empty `ssl_context` is provided, or a non-empty `tls_hostname` is supplied, the TCP connection must be wrapped in TLS. `create_tcp_listener` must return a listener whose `serve` method accepts streams and runs the handler for each stream. `connect_unix` and `create_unix_listener` provide the same byte-stream/listener model for filesystem socket paths and must raise the platform's normal errors when UNIX sockets are unsupported or paths are invalid.

**UDP and datagram sockets.** UDP and UNIX datagram factory functions must return async datagram socket objects. Unconnected datagram sockets must yield `(packet, address)` pairs and send with `sendto`. Connected datagram sockets must send and receive packets without requiring a destination per send. UNIX datagram sockets must use filesystem paths, and an unnamed local path must not be relied on for receiving datagrams from other UNIX datagram sockets.

**Connectable helpers.** `as_connectable` must return an existing byte-stream connectable unchanged, must convert `(host, port)` tuples to TCP connectables, and must convert string, bytes or path-like filesystem paths to UNIX connectables. Unsupported values must raise `TypeError` or the relevant constructor error.

## Files, Processes and Workers

AnyIO provides async wrappers for file I/O, subprocess execution, and offloading work to threads, processes, and subinterpreters.

**Async files and paths.** `open_file` must open a file asynchronously and return an `AsyncFile`. `wrap_file` must return an async wrapper around an existing file object, and closing the wrapper must close the wrapped file. Async file methods and `Path` operations that perform disk I/O must run through worker threads. `Path` methods that normally return `pathlib.Path` objects must return `anyio.Path` objects, and directory iteration and globbing must be asynchronous iterators that yield `anyio.Path` entries.

**Temporary files and directories.** Temporary file and directory context managers must mirror the corresponding `tempfile` object lifetimes while making blocking file operations awaitable. `TemporaryDirectory` used as an async context manager must create a directory on entry and remove it on exit. `mkstemp` must return `(fd, path)` and `mkdtemp` must return a path; these low-level functions require the caller to clean up created filesystem entries. `gettempdir` and `gettempdirb` must return the default temporary directory as text and bytes respectively.

**Process execution.** `run_process` must run a command to completion. A string command must run through the default shell, and a sequence command must execute directly with the first item as the executable. It must return a `subprocess.CompletedProcess`-like result containing `returncode` and captured `stdout`. When `check` is `True` and the process exits nonzero, it must raise `CalledProcessError`. `open_process` must return a process object with async stream attributes for configured pipes and async waiting/termination methods.

**Thread workers.** `to_thread.run_sync` must run a synchronous callable in a worker thread and return its result. Waiting tasks must be shielded from cancellation by default. When `abandon_on_cancel` is `True`, cancellation of the waiting task must abandon the result while the thread continues running. `current_default_thread_limiter` must return the limiter used for calls without an explicit limiter, and its default `total_tokens` must be 40.

**Thread-to-event-loop bridge.** `from_thread.run` and `from_thread.run_sync` must let AnyIO worker threads call async or sync functions in the event loop thread. They must raise `NoEventLoopError` when called from a foreign thread without an explicit `EventLoopToken`, and `RunFinishedError` when the token belongs to a finished loop. `from_thread.check_cancelled` must raise the backend cancellation exception when the host task's scope has been cancelled. `BlockingPortal` and `start_blocking_portal` must provide synchronous callers with `call`, `start_task_soon`, `start_task`, `wrap_async_context_manager` and `stop`. Portal-spawned tasks must return `concurrent.futures.Future` objects; cancelling those futures must cancel the corresponding async tasks. `BlockingPortalProvider` must share one on-demand portal among concurrent synchronous callers using the same provider.

**Process workers.** `to_process.run_sync` must run an importable, pickleable callable with pickleable arguments in a worker process and return a pickleable result. When a cancellable call is cancelled during execution, the worker process must be killed. Abrupt worker termination or protocol failure must raise `BrokenWorkerProcess`. Worker process standard input, output and error must be redirected away from the parent process streams, and idle workers must be eligible for shutdown.

**Subinterpreter workers.** `to_interpreter.run_sync` must run a callable in a Python subinterpreter on supported Python versions. It must reject unsupported runtimes through the documented runtime error path, must not support callables from `__main__`, must not share mutable data across interpreters, and must raise `BrokenWorkerInterpreter` when the worker interpreter reports an unexpected uncaught failure.

## Synchronization, Typed Attributes and Low Level APIs

AnyIO provides task-level synchronization primitives, typed attribute lookups, and low-level event loop access.

**Events.** `Event` must wake all waiters when `set` is called and must not be reusable after being set. `statistics` must return an object whose `tasks_waiting` reflects the number of tasks waiting on the event.

**Locks.** `Lock` must allow only the owning task to release it; releasing from a non-owning task must raise `RuntimeError`. `statistics` must return an object whose `locked` field indicates whether the lock is held and whose `tasks_waiting` reports how many tasks are waiting to acquire it.

**Semaphores.** `Semaphore` must limit concurrent holders by its initial value and must raise `ValueError` for invalid initial values such as negative numbers. The `value` property must track the current available count, decreasing on `acquire` and increasing on `release`.

**Conditions.** `Condition` must combine a lock with notifications, and `notify`/`notify_all` must require the condition lock to be held.

**Capacity limiters.** `CapacityLimiter` must allow a borrower to hold at most one token from that limiter at a time; attempting a double acquisition must raise `RuntimeError`. `total_tokens` must reflect the configured capacity. Changing `total_tokens` upward must wake an appropriate number of waiters. `statistics` must return an object whose `borrowed_tokens` and `tasks_waiting` reflect current utilization.

**Resource guards.** `ResourceGuard` must raise `BusyResourceError` when a second operation enters the guarded section concurrently.

**Synchronization constraints.** Synchronization primitives are task-synchronization objects, not thread-safe objects. Direct use from worker threads must be avoided; callers must use `from_thread.run_sync` when a worker thread needs to interact with them. Violating ownership or state preconditions must raise the documented runtime or resource exception rather than silently succeeding.

**Typed attributes.** Typed attributes use keys created by `typed_attribute` on `TypedAttributeSet` subclasses. `TypedAttributeProvider.extra` must return the provider's value for the key, delegate through wrapped providers when the local provider does not define the key, and return the supplied default when no provider supplies the key. It must raise `TypedAttributeLookupError` when the key is absent and no default was supplied. Wrappers must be able to override attributes from wrapped objects.

**Signal handling.** `open_signal_receiver` must return a synchronous context manager whose value is an async iterator of received signal numbers. It must install handlers only where the platform and thread allow it, and platform or main-thread violations must raise the normal Python signal errors.

**Low-level checkpoint and run variables.** `checkpoint` must yield to the event loop and check cancellation. `checkpoint_if_cancelled` must yield only when cancellation is pending. `cancel_shielded_checkpoint` must yield without allowing external cancellation to interrupt that checkpoint. `current_token` must return an `EventLoopToken` for entering the current loop from foreign threads and must raise `NoEventLoopError` outside a supported loop. `RunVar` stores values local to the current event-loop run; `get` must return the current value, an explicit default, or the variable default, and must raise `LookupError` when no value exists. `set` must return a token, and `reset` must restore the previous value for the same variable and run.

## Async Helpers and Testing

AnyIO extends standard library patterns with async-aware caching, reduction, and iteration, and provides a pytest plugin for backend-transparent testing.

**Async caching decorators.** `anyio.functools.cache` and `lru_cache` must cache results of coroutine functions and expose `cache_info`, `cache_parameters` and `cache_clear` on the wrapper. When `maxsize` is supplied, `lru_cache` must honor the maximum cache size. When `typed` is `True`, argument types must be included in cache keys. Invalid use must raise the same category of errors as the standard cache decorators.

**Async reduce.** `anyio.functools.reduce` must consume synchronous or asynchronous iterables and must await the reducing callable.

**Async itertools.** `anyio.itertools` functions must accept synchronous iterables and asynchronous iterables. Functions that take predicates or combining functions must await those callables. They must preserve the ordering, grouping and exhaustion behavior of the corresponding standard-library `itertools` function, and invalid argument counts or values must raise the corresponding Python exceptions.

**Pytest plugin.** The pytest plugin must enable async tests through `anyio_mode = "auto"`, `pytest.mark.anyio`, or direct use of the `anyio_backend` fixture. The default `anyio_backend` fixture must run tests on all available supported backends. A project override of `anyio_backend` must return either a backend name string or `(backend_name, backend_options_dict)`. `anyio_backend_name` must return the selected name, and `anyio_backend_options` must return the selected options dict. Async fixtures used by AnyIO-enabled tests must run inside the AnyIO test runner. Higher-scoped async fixtures require a compatible higher-scoped `anyio_backend` fixture. Within a single async test runner, async fixtures and tests must share context-variable state because they run in the same task; that context must not leak into synchronous tests or separate runners.

**Port factories.** `free_tcp_port_factory` and `free_udp_port_factory` must return `FreePortFactory` callables for unused TCP or UDP port numbers. `free_tcp_port` and `free_udp_port` must return one generated port for function-scoped use. If another process binds a returned port before the caller uses it, the bind operation must raise the platform `OSError`.

## State Model

AnyIO exposes shared runtime and resource state through three public projections:

1. The running backend projection: clocks, cancellation class, current task information, low-level checkpoints and event-loop tokens.
2. The structured concurrency projection: cancel scopes, task groups, task handles and pytest async test runners.
3. The resource projection: streams, listeners, subprocesses, files, synchronization primitives, typed attributes and worker limiters.

These projections must agree. A task spawned in a task group returns a handle whose status and value reflect the same cancellation and exception state seen by the enclosing task group. A deadline set by a timeout scope must be visible through `current_effective_deadline()` while that scope is effective. A stream wrapper must expose its own typed attributes and must delegate missing attributes to the wrapped stream. A worker call made through `to_thread.run_sync()` must copy the caller's context variables into the worker, and `from_thread.run()` or `from_thread.run_sync()` must use the same originating event-loop token when called from that worker. A pytest async fixture and the async test using it must share the same runner task for context-variable propagation within that runner.

## Error Semantics

`BrokenResourceError` must be raised when an externally caused condition makes a resource unusable, such as sending after all receive clones are closed. `ClosedResourceError` must be raised when the caller uses a resource after closing that same resource. `BusyResourceError` must be raised when concurrent operations attempt an exclusive resource action.

`EndOfStream` must signal clean stream EOF from the peer. `IncompleteRead` must be raised by buffered reads when EOF arrives before the requested bytes or delimiter-delimited data are complete. `DelimiterNotFound` must be raised when `receive_until()` reads the configured maximum without seeing the delimiter.

`NoEventLoopError` must be raised by APIs that require a supported running event loop when none exists, including current clock/cancellation APIs and thread-entry APIs without a token. `RunFinishedError` must be raised when a thread-entry token points to a loop that has finished.

`TaskNotFinished`, `TaskCancelled`, and `TaskFailed` must be raised by `TaskHandle` properties or awaits according to pending, cancelled and failed task states. `TaskCancelled` is a subclass of `TaskFailed`.

`ConnectionFailed` must represent failed connection attempts and must inherit from `OSError`. `TypedAttributeLookupError` must inherit from `LookupError`. `WouldBlock` must be raised by nowait operations when the operation would need to block. `BrokenWorkerProcess` and `BrokenWorkerInterpreter` must represent failed worker process and subinterpreter execution respectively.

## Cross-View Invariants

1. A timeout created with `move_on_after()` or `fail_after()` must be reflected by `current_effective_deadline()` while the scope is active.
2. Cancelling a task group's `cancel_scope` must move unfinished child `TaskHandle` objects through cancelling to a cancelled final state unless a child completes first.
3. A value passed to `task_status.started(value)` must be returned by `TaskGroup.start()` and must be visible as `TaskHandle.start_value` when `return_handle=True`.
4. A memory object sent through any send clone must be received by exactly one receive clone, and closing all receive clones must make subsequent sends raise `BrokenResourceError`.
5. A typed attribute supplied by an underlying socket stream must be returned through TLS, text, buffered or stapled wrappers unless the wrapper overrides that key.
6. Closing an `AsyncFile` returned by `wrap_file()` must close the wrapped synchronous file object, and later file operations through the wrapper must raise the closed-file error path.
7. A context variable set before `to_thread.run_sync()` must be readable inside the worker thread, and changes made in that worker must not change the value in the caller task.
8. `from_thread.run_sync()` called from an AnyIO worker thread must execute against the same event-loop run that spawned the worker; the same call from a foreign thread must require an explicit token.
9. A pytest async fixture and async test using the same AnyIO runner must observe the same context-variable state; a separate runner must not inherit that state.
10. A listener returned by a socket factory must expose bound-address typed attributes that a client connection path uses to connect during the same event-loop run.

## Public Interface

### Import Surface

The package must be importable as `anyio`. The top-level namespace must expose:

```python
run, sleep, sleep_forever, sleep_until, current_time
get_all_backends, get_available_backends, get_cancelled_exc_class
CancelScope, move_on_after, fail_after, current_effective_deadline
create_task_group, TaskHandle, TASK_STATUS_IGNORED
create_memory_object_stream
open_file, wrap_file, AsyncFile, Path
TemporaryFile, NamedTemporaryFile, SpooledTemporaryFile, TemporaryDirectory
mkstemp, mkdtemp, gettempdir, gettempdirb
connect_tcp, connect_unix, create_tcp_listener, create_unix_listener
create_udp_socket, create_connected_udp_socket
create_unix_datagram_socket, create_connected_unix_datagram_socket
as_connectable, TCPConnectable, UNIXConnectable
getaddrinfo, getnameinfo, wait_readable, wait_writable
wait_socket_readable, wait_socket_writable, notify_closing
open_process, run_process, open_signal_receiver, aclose_forcefully
Event, Lock, Condition, Semaphore, CapacityLimiter, ResourceGuard
EventStatistics, LockStatistics, ConditionStatistics
SemaphoreStatistics, CapacityLimiterStatistics
TypedAttributeSet, TypedAttributeProvider, typed_attribute
TaskInfo, get_current_task, get_running_tasks, wait_all_tasks_blocked
ContextManagerMixin, AsyncContextManagerMixin
BrokenResourceError, BrokenWorkerInterpreter, BrokenWorkerProcess
BusyResourceError, ClosedResourceError, ConnectionFailed
DelimiterNotFound, EndOfStream, IncompleteRead, NoEventLoopError
RunFinishedError, TaskCancelled, TaskFailed, TaskNotFinished
TypedAttributeLookupError, WouldBlock
```

`anyio.abc` must expose the public resource, task, stream, socket, subprocess and testing ABCs and aliases documented in the API reference, including `AsyncResource`, `TaskGroup`, `TaskStatus`, `Process`, `TestRunner`, `BlockingPortal`, `CancelScope`, `Event`, `Lock`, `Condition`, `Semaphore`, socket ABCs, stream ABCs, connectable ABCs and the `Any*Stream` aliases.

The public stream modules must expose their documented classes from these importable module paths: `anyio.streams.buffered` must expose `BufferedByteReceiveStream` and `BufferedByteStream`; `anyio.streams.file` must expose `FileReadStream`, `FileWriteStream`, and `FileStreamAttribute`; `anyio.streams.memory` must expose `MemoryObjectReceiveStream`, `MemoryObjectSendStream`, and `MemoryObjectStreamStatistics`; `anyio.streams.stapled` must expose `StapledByteStream`, `StapledObjectStream`, and `MultiListener`; `anyio.streams.text` must expose `TextReceiveStream`, `TextSendStream`, `TextStream`, and `TextConnectable`; and `anyio.streams.tls` must expose `TLSStream`, `TLSListener`, `TLSConnectable`, and `TLSAttribute`.

The bridge and helper modules must expose `anyio.to_thread.run_sync`, `anyio.to_thread.current_default_thread_limiter`, `anyio.from_thread.run`, `anyio.from_thread.run_sync`, `anyio.from_thread.check_cancelled`, `anyio.from_thread.start_blocking_portal`, `anyio.from_thread.BlockingPortal`, `anyio.from_thread.BlockingPortalProvider`, `anyio.to_process.run_sync`, `anyio.to_process.current_default_process_limiter`, `anyio.to_interpreter.run_sync`, `anyio.to_interpreter.current_default_interpreter_limiter`, `anyio.lowlevel.checkpoint`, `checkpoint_if_cancelled`, `cancel_shielded_checkpoint`, `current_token`, `RunVar`, `EventLoopToken`, `anyio.functools.cache`, `lru_cache`, `reduce`, and the async iterator functions documented under `anyio.itertools`.

The deprecated top-level spelling `BrokenWorkerIntepreter` must return `BrokenWorkerInterpreter` and must issue `DeprecationWarning` when accessed.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `run` | function | Execute a coroutine on a selected async backend |
| `sleep` | function | Suspend the current task for a duration |
| `sleep_forever` | function | Suspend the current task until cancellation |
| `sleep_until` | function | Suspend until a monotonic-clock deadline |
| `current_time` | function | Return the backend monotonic clock value |
| `get_all_backends` | function | List all recognized backend names |
| `get_available_backends` | function | List importable built-in backend names |
| `get_cancelled_exc_class` | function | Return the backend cancellation exception class |
| `CancelScope` | class | Synchronous context manager for deadline and cancellation |
| `move_on_after` | function | Create a cancel scope that suppresses its own timeout |
| `fail_after` | function | Create a cancel scope that raises on timeout |
| `current_effective_deadline` | function | Return the nearest active deadline |
| `create_task_group` | function | Create an async context manager for structured child tasks |
| `TaskHandle` | class | Handle for observing, awaiting, and cancelling a spawned task |
| `TASK_STATUS_IGNORED` | sentinel | Default task status for functions not using `started()` |
| `create_memory_object_stream` | function | Create a paired send/receive object stream |
| `open_file` | function | Open a file asynchronously returning `AsyncFile` |
| `wrap_file` | function | Wrap a synchronous file in an async interface |
| `AsyncFile` | class | Async wrapper for file objects |
| `Path` | class | Async equivalent of `pathlib.Path` |
| `connect_tcp` | function | Open a TCP byte stream to a remote host |
| `create_tcp_listener` | function | Bind and return a TCP listener |
| `connect_unix` | function | Open a UNIX socket byte stream |
| `create_unix_listener` | function | Bind and return a UNIX socket listener |
| `create_udp_socket` | function | Create an unconnected UDP socket |
| `create_connected_udp_socket` | function | Create a connected UDP socket |
| `open_process` | function | Launch a subprocess with async stream pipes |
| `run_process` | function | Run a command to completion and return its result |
| `Event` | class | One-shot async event signal |
| `Lock` | class | Async mutual-exclusion lock |
| `Condition` | class | Async condition variable with lock |
| `Semaphore` | class | Async counting semaphore |
| `CapacityLimiter` | class | Token-based concurrency limiter |
| `ResourceGuard` | class | Guard against concurrent exclusive-resource access |
| `BlockingPortal` | class | Synchronous entry point into an async event loop |
| `TypedAttributeSet` | class | Base class for typed-attribute key declarations |
| `TypedAttributeProvider` | class | Mixin providing typed-attribute lookups |
| `typed_attribute` | function | Create a typed-attribute key |
| `checkpoint` | function | Yield to the event loop and check cancellation |
| `RunVar` | class | Variable scoped to one event-loop run |

### CLI Entry Points

There is no console script for this package. `python -m anyio` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

The implementation must be delivered as an installable Python package: a `pip install` of the project root must succeed and must place the `anyio` package on the import path. The package must register its pytest plugin through the `[project.entry-points.pytest11]` group in its packaging metadata (or the equivalent `entry_points` declaration of the chosen build backend); without that registration, the async test and fixture behavior described in this specification cannot run under a standard `pytest` invocation.

## Appendix B: Assessment Notes

Validation covers the documented public API, backend compatibility, concurrency and cancellation, resource lifecycles, streams and networking, files and workers, synchronization, helpers, pytest integration, and cross-view invariants. Checks use supported local resources and assess independently observable public behavior, including success, failure, cleanup, context propagation, exceptions, and warnings. Each satisfied behavior contributes independently; private implementation details and exact diagnostic text are not considered unless explicitly required.
