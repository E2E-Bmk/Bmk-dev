# AnyIO Specification

## Product Overview

AnyIO is an asynchronous networking and concurrency library that presents one public API over `asyncio` and Trio. Code written against AnyIO must run on either backend when the selected backend is installed. The library supplies structured concurrency, cancellation scopes, async streams, networking, subprocesses, worker threads, worker processes, subinterpreters, async file and temporary-file APIs, synchronization primitives, testing support, typed attributes and small async variants of `functools` and `itertools`.

## Scope

This specification covers the public Python APIs exported from `anyio`, `anyio.abc`, `anyio.streams.*`, `anyio.from_thread`, `anyio.to_thread`, `anyio.to_process`, `anyio.to_interpreter`, `anyio.lowlevel`, `anyio.functools`, `anyio.itertools`, and the pytest plugin fixtures and marker/config behavior.

The covered behavior includes backend selection, task groups and task handles, cancellation and deadlines, memory object streams, byte/object stream wrappers, socket/listener factories, subprocess handles, worker bridges, async file/path/tempfile wrappers, synchronization primitives, typed attributes, signal receivers, async test runners and the public exception classes.

## Installable Surface

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

The public stream modules must expose `BufferedByteReceiveStream`, `BufferedByteStream`, `FileReadStream`, `FileWriteStream`, `FileStreamAttribute`, `MemoryObjectReceiveStream`, `MemoryObjectSendStream`, `MemoryObjectStreamStatistics`, `StapledByteStream`, `StapledObjectStream`, `MultiListener`, `TextReceiveStream`, `TextSendStream`, `TextStream`, `TextConnectable`, `TLSStream`, `TLSListener`, `TLSConnectable` and `TLSAttribute`.

The bridge and helper modules must expose `anyio.to_thread.run_sync`, `anyio.to_thread.current_default_thread_limiter`, `anyio.from_thread.run`, `anyio.from_thread.run_sync`, `anyio.from_thread.check_cancelled`, `anyio.from_thread.start_blocking_portal`, `anyio.from_thread.BlockingPortal`, `anyio.from_thread.BlockingPortalProvider`, `anyio.to_process.run_sync`, `anyio.to_process.current_default_process_limiter`, `anyio.to_interpreter.run_sync`, `anyio.to_interpreter.current_default_interpreter_limiter`, `anyio.lowlevel.checkpoint`, `checkpoint_if_cancelled`, `cancel_shielded_checkpoint`, `current_token`, `RunVar`, `EventLoopToken`, `anyio.functools.cache`, `lru_cache`, `reduce`, and the async iterator functions documented under `anyio.itertools`.

The deprecated top-level spelling `BrokenWorkerIntepreter` must return `BrokenWorkerInterpreter` and must issue `DeprecationWarning` when accessed.

## Public API

`run(func, *args, backend="asyncio", backend_options=None)` must call the coroutine function with the supplied positional arguments and return its result. It must raise `RuntimeError` when an async event loop is already running in the current thread. It must raise `LookupError` when the backend name is unknown or when a built-in backend such as Trio is requested but unavailable. `get_all_backends()` returns `("asyncio", "trio")`; `get_available_backends()` returns only built-in backends importable in the current environment.

`sleep(delay)`, `sleep_forever()`, and `sleep_until(deadline)` must suspend the current task through the active backend. `sleep_forever()` must behave as an infinite sleep until cancellation. `sleep_until(deadline)` must use the backend's monotonic clock and must return immediately when the deadline is in the past. `current_time()` and `get_cancelled_exc_class()` must raise `NoEventLoopError` when no supported event loop is active.

`CancelScope(deadline=inf, shield=False)` must be a synchronous context manager whose `cancel(reason=None)` cancels the scope and nested scopes. `move_on_after(delay, shield=False)` returns a cancel scope that suppresses its own timeout cancellation and records it via `cancelled_caught`. `fail_after(delay, shield=False)` must raise `TimeoutError` when its own deadline is reached before the context exits. `current_effective_deadline()` returns the nearest effective deadline, `inf` when no deadline applies, and `-inf` when the current scope is already effectively cancelled.

`create_task_group()` returns an async context manager with a `cancel_scope`. Leaving the context must wait for every child task. If the context body or any child task raises, the task group must cancel the remaining children and must propagate the raised exception or an exception group when multiple errors occur.

`TaskGroup.start_soon(func, *args, name=None)` and `TaskGroup.create_task(coro, name=None)` return `TaskHandle`. `TaskGroup.start(func, *args, name=None, return_handle=False)` must wait until the target calls `task_status.started(value)`. It returns that value when `return_handle` is false and returns a `TaskHandle` whose `start_value` is that value when `return_handle` is true. It must raise `RuntimeError` when the target exits without calling `started()`.

`TaskHandle` has statuses `PENDING`, `FINISHED`, `CANCELLING`, `CANCELLED`, and `FAILED`. Awaiting a handle returns the task result when finished, raises `TaskCancelled` when cancelled, and raises `TaskFailed` when the task raised a non-cancellation exception. `return_value` must raise `TaskNotFinished`, `TaskCancelled`, or `TaskFailed` for pending, cancelled, or failed tasks respectively. `exception` returns the task exception for failed tasks, returns `None` for successful tasks, and raises `TaskNotFinished` or `TaskCancelled` for pending or cancelled tasks. `cancel()` must request cancellation and must have no effect after the task has finished. `wait()` must return after completion regardless of the final status. `start_value` must raise `RuntimeError` when the task was not started via `TaskGroup.start()`.

## Product State Model

AnyIO exposes shared runtime and resource state through three public projections:

1. The running backend projection: clocks, cancellation class, current task information, low-level checkpoints and event-loop tokens.
2. The structured concurrency projection: cancel scopes, task groups, task handles and pytest async test runners.
3. The resource projection: streams, listeners, subprocesses, files, synchronization primitives, typed attributes and worker limiters.

These projections must agree. A task spawned in a task group returns a handle whose status and value reflect the same cancellation and exception state seen by the enclosing task group. A deadline set by a timeout scope must be visible through `current_effective_deadline()` while that scope is effective. A stream wrapper must expose its own typed attributes and must delegate missing attributes to the wrapped stream. A worker call made through `to_thread.run_sync()` must copy the caller's context variables into the worker, and `from_thread.run()` or `from_thread.run_sync()` must use the same originating event-loop token when called from that worker. A pytest async fixture and the async test using it must share the same runner task for context-variable propagation within that runner.

## Streams and Networking

Byte streams must send and receive arbitrary chunks of bytes without preserving send boundaries. Reading from a byte stream whose peer closed cleanly must raise `EndOfStream`; it must not return empty bytes as the EOF signal. Object streams must deliver Python objects according to the concrete stream's contract.

`create_memory_object_stream[T](max_buffer_size=0, item_type=None)` returns `(send_stream, receive_stream)`. The default buffer size is zero, so `send()` must block until a receiver accepts the item. `max_buffer_size` must be a non-negative integer or `math.inf`; invalid values must raise `ValueError`. Passing `item_type` must issue `DeprecationWarning`. Each sent item must be delivered to exactly one receiver even when receive clones exist. Each send or receive end is considered open until all clones of that end are closed. The receive side's async iteration must stop only after all send clones have been closed and buffered items have been consumed. Memory object streams must support synchronous `close()` and context manager close in addition to `aclose()`. Nowait operations must raise `WouldBlock` when the operation would block, `ClosedResourceError` when the same end is closed, and `BrokenResourceError` when the opposite end is fully closed.

`BufferedByteReceiveStream` wraps a byte receive stream and keeps an internal read buffer. `receive_exactly(nbytes)` returns exactly that many bytes or raises `IncompleteRead` when EOF happens first. `receive_until(delimiter, max_bytes)` returns bytes before the delimiter, raises `DelimiterNotFound` when the delimiter is absent from the first `max_bytes` buffered bytes, and raises `IncompleteRead` when EOF arrives first. `feed_data(data)` must prepend externally supplied bytes to subsequent receives according to the buffer order.

`TextReceiveStream`, `TextSendStream`, and `TextStream` must decode and encode text over byte streams with the configured encoding and error policy. Decode or encode failures must raise the corresponding Python codec exception. `StapledByteStream` and `StapledObjectStream` must expose one bidirectional stream from compatible send and receive halves; closing the stapled stream must close both halves, and send EOF must be forwarded to the send half when supported.

`TLSStream.wrap(...)` and `TLSConnectable.connect()` must perform a TLS handshake over an existing byte stream. `TLSListener` must wrap accepted byte streams and pass TLS streams to the handler. TLS shutdown must follow the `standard_compatible` setting: when standard-compatible shutdown is enabled, EOF and unwrap behavior must follow TLS close-notify semantics; TLS handshake or transport failures must propagate to the caller or configured handshake error handler.

`connect_tcp(remote_host, remote_port, *, local_host=None, tls=False, ssl_context=None, tls_hostname=None, happy_eyeballs_delay=0.25)` returns a socket byte stream. Passing `tls=True`, a non-empty `ssl_context`, or a non-empty `tls_hostname` must wrap the TCP connection in TLS. `create_tcp_listener(...)` returns a listener whose `serve(handler, task_group=None)` accepts streams and runs the handler for each stream. `connect_unix()` and `create_unix_listener()` provide the same byte-stream/listener model for filesystem socket paths and must raise the platform's normal errors when UNIX sockets are unsupported or paths are invalid.

UDP and UNIX datagram factory functions return async datagram socket objects. Unconnected datagram sockets must yield `(packet, address)` pairs and send with `sendto`. Connected datagram sockets must send and receive packets without requiring a destination per send. UNIX datagram sockets must use filesystem paths, and an unnamed local path must not be relied on for receiving datagrams from other UNIX datagram sockets.

`as_connectable(value, tls=False)` must return an existing byte-stream connectable unchanged, must convert `(host, port)` tuples to TCP connectables, and must convert string, bytes or path-like filesystem paths to UNIX connectables. Unsupported values must raise `TypeError` or the relevant constructor error.

## Files, Processes and Workers

`open_file()` opens a file asynchronously and returns `AsyncFile`. `wrap_file(file)` returns an async wrapper around an existing file object, and closing the wrapper must close the wrapped file. Async file methods and `Path` operations that perform disk I/O must run through worker threads and must honor an explicit `CapacityLimiter` when supplied. `Path` methods that normally return `pathlib.Path` objects must return `anyio.Path` objects, and directory iteration and globbing must be asynchronous iterators.

Temporary file and directory context managers must mirror the corresponding `tempfile` object lifetimes while making blocking file operations awaitable. `mkstemp()` returns `(fd, path)` and `mkdtemp()` returns a path; these low-level functions require the caller to clean up created filesystem entries. `gettempdir()` and `gettempdirb()` return the default temporary directory as text and bytes respectively.

`run_process(command, *, input=None, stdin=None, stdout=-1, stderr=-1, check=True, cwd=None, env=None, startupinfo=None, creationflags=0, start_new_session=False, pass_fds=(), user=None, group=None, extra_groups=None, umask=-1)` runs a command to completion. A string command must run through the default shell, and a sequence command must execute directly with the first item as the executable. It returns a `subprocess.CompletedProcess`-like result containing return code and captured output. It must raise `CalledProcessError` when `check=True` and the process exits nonzero. `open_process(...)` returns a process object with async stream attributes for configured pipes and async waiting/termination methods.

`to_thread.run_sync(func, *args, abandon_on_cancel=False, cancellable=None, limiter=None)` runs a synchronous callable in a worker thread. Waiting tasks must be shielded from cancellation by default. When `abandon_on_cancel=True`, cancellation of the waiting task must abandon the result while the thread continues running. `current_default_thread_limiter()` returns the limiter used for calls without an explicit limiter, and its default total tokens must be 40.

`from_thread.run()` and `from_thread.run_sync()` must let AnyIO worker threads call async or sync functions in the event loop thread. They must raise `NoEventLoopError` when called from a foreign thread without an explicit `EventLoopToken`, and `RunFinishedError` when the token belongs to a finished loop. `from_thread.check_cancelled()` must raise the backend cancellation exception when the host task's scope has been cancelled. `BlockingPortal` and `start_blocking_portal()` must provide synchronous callers with `call()`, `start_task_soon()`, `start_task()`, `wrap_async_context_manager()` and `stop()`. Portal-spawned tasks must return `concurrent.futures.Future` objects; cancelling those futures must cancel the corresponding async tasks. `BlockingPortalProvider` must share one on-demand portal among concurrent synchronous callers using the same provider.

`to_process.run_sync(func, *args, cancellable=False, limiter=None)` runs an importable, pickleable callable with pickleable arguments in a worker process and returns a pickleable result. When a cancellable call is cancelled during execution, the worker process must be killed. Abrupt worker termination or protocol failure must raise `BrokenWorkerProcess`. Worker process standard input, output and error must be redirected away from the parent process streams, and idle workers must be eligible for shutdown.

`to_interpreter.run_sync(func, *args, limiter=None)` runs a callable in a Python subinterpreter on supported Python versions. It must reject unsupported runtimes through the documented runtime error path, must not support callables from `__main__`, must not share mutable data across interpreters, and must raise `BrokenWorkerInterpreter` when the worker interpreter reports an unexpected uncaught failure.

## Synchronization, Typed Attributes and Low Level APIs

`Event` must wake all waiters when set and must not be reusable after being set. `Lock` must allow only the owning task to release it. `Semaphore` must limit concurrent holders by its value and must raise for invalid initial values. `Condition` must combine a lock with notifications, and `notify()`/`notify_all()` must require the condition lock to be held. `CapacityLimiter` must allow a borrower to hold at most one token from that limiter at a time; changing `total_tokens` upward must wake an appropriate number of waiters. `ResourceGuard` must raise `BusyResourceError` when a second operation enters the guarded section concurrently. Statistics objects return observable counts for waiting tasks, owners, borrowers and available tokens according to the primitive type.

Synchronization primitives are task-synchronization objects, not thread-safe objects. Direct use from worker threads must be avoided; callers must use `from_thread.run_sync()` when a worker thread needs to interact with them. Violating ownership or state preconditions must raise the documented runtime or resource exception rather than silently succeeding.

Typed attributes use keys created by `typed_attribute()` on `TypedAttributeSet` subclasses. `TypedAttributeProvider.extra(attribute, default=...)` must return the provider's value for the key, delegate through wrapped providers when the local provider does not define the key, and return the supplied default when no provider supplies the key. It must raise `TypedAttributeLookupError` when the key is absent and no default was supplied. Wrappers must be able to override attributes from wrapped objects.

`open_signal_receiver(*signals)` returns a synchronous context manager whose value is an async iterator of received signal numbers. It must install handlers only where the platform and thread allow it, and platform or main-thread violations must raise the normal Python signal errors.

`checkpoint()` must yield to the event loop and check cancellation. `checkpoint_if_cancelled()` must yield only when cancellation is pending. `cancel_shielded_checkpoint()` must yield without allowing external cancellation to interrupt that checkpoint. `current_token()` returns an `EventLoopToken` for entering the current loop from foreign threads and must raise `NoEventLoopError` outside a supported loop. `RunVar(name, default=...)` stores values local to the current event-loop run; `get()` must return the current value, an explicit default, or the variable default, and must raise `LookupError` when no value exists. `set()` returns a token, and `reset(token)` must restore the previous value for the same variable and run.

## Async Helpers and Testing

`anyio.functools.cache` and `lru_cache` must cache results of coroutine functions and expose `cache_info()`, `cache_parameters()` and `cache_clear()` on the wrapper. `lru_cache(maxsize=128, typed=False, always_checkpoint=False, ttl=None)` must honor max size, typed keys and TTL expiration; invalid use must raise the same category of errors as the standard cache decorators. `anyio.functools.reduce()` must consume synchronous or asynchronous iterables and must await the reducing callable.

`anyio.itertools` functions must accept synchronous iterables and asynchronous iterables. Functions that take predicates or combining functions must await those callables. They must preserve the ordering, grouping and exhaustion behavior of the corresponding standard-library `itertools` function, and invalid argument counts or values must raise the corresponding Python exceptions.

The pytest plugin must enable async tests through `anyio_mode = "auto"`, `pytest.mark.anyio`, or direct use of the `anyio_backend` fixture. The default `anyio_backend` fixture must run tests on all available supported backends. A project override of `anyio_backend` returns either a backend name string or `(backend_name, backend_options_dict)`. `anyio_backend_name` returns the selected name, and `anyio_backend_options` returns the selected options dict.

Async fixtures used by AnyIO-enabled tests must run inside the AnyIO test runner. Higher-scoped async fixtures require a compatible higher-scoped `anyio_backend` fixture. Within a single async test runner, async fixtures and tests must share context-variable state because they run in the same task; that context must not leak into synchronous tests or separate runners.

`free_tcp_port_factory` and `free_udp_port_factory` return `FreePortFactory` callables for unused TCP or UDP port numbers. `free_tcp_port` and `free_udp_port` return one generated port for function-scoped use. If another process binds a returned port before the caller uses it, the bind operation must raise the platform `OSError`.

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

## Non-Goals

This specification does not require re-creating internal backend modules, private helper names, private attributes, private task scheduling details, or exact internal data structures. It does not require support for raw sockets, SCTP, Windows signal behavior beyond Python platform errors, optional third-party backends that are not installed, or network access outside local resources. It does not require exact debug string formatting except where an exception class, warning class, return type or documented status value is part of the public API.
