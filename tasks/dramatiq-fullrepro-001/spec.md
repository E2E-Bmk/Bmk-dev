# Dramatiq Specification

=== Context Layer ===

## Product Overview

`dramatiq` is a Python task-processing library built around actors, immutable messages, broker queues, workers, middleware, result backends, and composition helpers. Applications decorate callables as actors, create or enqueue messages, process those messages with workers, and optionally observe callbacks, retries, stored results, pipelines, groups, and local rate-limit state.

The package provides a deterministic in-process route through `StubBroker`, `StubBackend`, and a normal `Worker`. This route preserves the same public actor, message, middleware, result, and composition contracts used by service-backed deployments while requiring no external broker.

## Non-Goals

- Live RabbitMQ, Redis, Prometheus, gevent, eventlet, process forking, command-line process supervision, and file watching are outside this specification.
- Network transports, TLS, distributed persistence, cross-process locking, and deployment configuration are not required.
- Exact logging prose, exception message prose, stack traces, thread names, generated UUID values, and wall-clock timing are not defined.
- Private modules, private attributes, undocumented worker internals, and upstream source-test helpers are not part of the required surface.
- Delayed-message wall-clock delivery, periodic scheduling, cancellation, shutdown signals, and high-contention stress behavior are not required beyond the metadata and local synchronization contracts stated below.

## Scope

This specification covers actor declaration and invocation, message creation and encoding, global broker and encoder selection, local queue operations through `StubBroker`, single-worker processing, middleware hooks, callbacks, retries, dead letters, result storage, pipelines, groups, generic actors, local barriers, and concurrent rate limiting.

All covered workflows are local and deterministic. Message processing may use worker threads supplied by `Worker`, but it must not require a network service or another process.

=== Orientation Layer ===

## Representative Workflows

A basic actor can be called directly or sent through the active broker:

```python
import dramatiq
from dramatiq.brokers.stub import StubBroker

broker = StubBroker()
broker.emit_after("process_boot")
dramatiq.set_broker(broker)

@dramatiq.actor(queue_name="jobs")
def add(left, right):
    return left + right

assert add(2, 5) == 7
message = add.send(2, 5)
assert message.actor_name == "add"
assert message.queue_name == "jobs"
```

Results are enabled by attaching result middleware and opting an actor into storage:

```python
from dramatiq.results import Results
from dramatiq.results.backends import StubBackend

backend = StubBackend(namespace="local-results")
broker.add_middleware(Results(backend=backend))

@dramatiq.actor(store_results=True)
def identify(value):
    return {"value": value}

message = identify.send(12)
# After a Worker processes the queue, message.get_result() returns {"value": 12}.
```

Composition connects message results and aggregates independent work:

```python
from dramatiq import group

chain = add.message(1, 2) | add.message(3) | add.message(4)
batch = group([add.message(2, 3), add.message(5, 8)])
chain.run()
batch.run()
```

=== Behavior Layer ===

## Actors And Messages

**Actor declaration.** `dramatiq.actor` accepts a callable directly or as a configured decorator and returns an `Actor`. Declaring an actor registers it with the active broker. The public `actor_name`, `queue_name`, `priority`, `options`, and `broker` attributes reflect declaration parameters. The default actor name is the function name and the default queue is `default`. `actor_class` selects an `Actor` subclass for the decorated callable.

Actor names and queue names must use the supported identifier form. Invalid queue names raise `ValueError`. Actor options are accepted only when a broker middleware component advertises the option through `actor_options`; unsupported options raise `ValueError`.

**Direct calls and message creation.** Calling an actor invokes its underlying callable and returns that callable's result. `Actor.message(*args, **kwargs)` creates a `Message` without enqueueing it. Positional arguments are stored as a tuple, keyword arguments as a dictionary, and declaration options as message options when applicable. `message_with_options` accepts message-specific options. Actor values supplied to `on_success` and `on_failure` are normalized to actor names; non-actor callback objects raise `TypeError`.

**Sending.** `Actor.send` creates and immediately enqueues a message. `send_with_options` additionally accepts message options such as `delay`. A `datetime.timedelta` delay is converted to milliseconds, the message is placed on the queue's `.DQ` delay queue, and an integer `eta` no earlier than the message timestamp is stored in its options.

**Message fields.** `Message` exposes `queue_name`, `actor_name`, `args`, `kwargs`, `options`, `message_id`, and `message_timestamp`. A supplied argument sequence is normalized to a tuple. `asdict()` returns those public fields in a serializable mapping. `copy()` replaces selected fields, merges replacement options with existing options, and retains identity fields unless explicitly replaced.

**Encoding and time.** `Message.encode()` serializes the public message mapping with the active encoder, and `Message.decode()` reconstructs an equal message. Invalid encoded bytes raise `DecodeError`. `message_datetime` converts the millisecond timestamp into a timezone-aware UTC `datetime`.

**Message proxy.** `MessageProxy` forwards public message fields. `fail()` marks the proxy failed. `stuff_exception()` records an exception for middleware handling, and `clear_exception()` removes that transient failure state.

**Generic actors.** A concrete `GenericActor` subclass is callable through its `perform` method and exposes an actor through `__actor__`. Its nested `Meta` class forwards actor settings such as `queue_name` and retry options. A `Meta.abstract = True` class is not registered as an actor. Calling a concrete subclass that does not implement `perform` raises `NotImplementedError`.

## Encoders And Global Configuration

`JSONEncoder.encode` and `decode` round-trip JSON-compatible mappings, sequences, strings, numbers, booleans, and null values. `PickleEncoder` round-trips Python values that JSON cannot represent, including sets. Both encoders produce bytes and restore the original value on decode.

`get_encoder()` returns the current process-wide encoder and `set_encoder(encoder)` replaces it for later message encoding and decoding. `get_broker()` and `set_broker(broker)` provide the equivalent process-wide broker selection. Actors declared after broker selection register with that broker, and compositions created from their messages expose the same broker.

## Broker And Worker

**Declarations.** `StubBroker.declare_queue(name)` declares both `name` and its delay queue `name.DQ`. `get_declared_queues()` and `get_declared_delay_queues()` report those sets. Actor declaration registers the actor, `get_actor(name)` returns it, and `get_declared_actors()` reports actor names. Looking up an unknown actor raises `ActorNotFound`.

**Queue operations.** Enqueueing or consuming an undeclared queue, or joining an unknown queue, raises `QueueNotFound`. `consume(queue_name)` returns a consumer that yields `MessageProxy` values. Acknowledging a received message removes its unfinished state. Negatively acknowledging it adds the underlying message to `dead_letters`. `flush_all()` clears queued, unfinished, and dead-letter state.

**Worker processing.** `Worker(broker, worker_threads=..., worker_timeout=...)` processes messages from declared broker queues after `start()`. It invokes actors with the message's positional and keyword arguments, including actors on custom queues. `Broker.join(queue_name, fail_fast=...)` waits for queue work and `Worker.join()` waits for worker activity to settle. `Worker.stop()` releases worker resources.

Message identity, actor name, queue, arguments, keyword arguments, and options must survive the actor-to-broker-to-consumer or worker path.

## Middleware Lifecycle And Retry

`Middleware.actor_options` defaults to an empty set and `Middleware.forks` defaults to an empty list. Adding middleware places it in `broker.middleware`. `add_middleware(item, before=Type)` or `after=Type` locates the requested anchor; a missing anchor raises `ValueError`.

Middleware declaration and processing hooks receive the broker plus public actor or message values. `after_declare_actor` runs for actor declaration. `before_process_message` runs before actor invocation. `after_process_message` receives the result or exception after invocation. Middleware-specific options advertised through `actor_options` become legal actor options.

If `before_process_message` raises `SkipMessage`, the worker does not invoke the actor, acknowledges the message, and invokes `after_skip_message`. `SkipMessage` is an exception type intended for middleware control flow.

An actor may define `on_success` and `on_failure` callbacks. After successful processing, the success callback receives the original message mapping and actor result. After failed processing, the failure callback receives the original message mapping and exception metadata containing at least the exception type.

Raising `Retry(delay=...)` requests another attempt. The requested delay is publicly available as `delay`, and its default is `None`. Retry middleware requeues while the actor's retry limit permits. Once retries are exhausted, the failed message enters `dead_letters`. An actor configured with `max_retries=0` moves an unhandled failure directly to dead letters.

## Results

`Results(backend=...)` attaches result storage to a broker. The broker exposes that backend through `get_results_backend()`. An actor with `store_results=True` stores its return value after successful processing. `Message.get_result(backend=...)` retrieves the value, and when no backend argument is given it may infer the backend from the active broker. An actor that did not enable result storage has no retrievable result through the implicit route and raises `RuntimeError`.

`ResultStubBackend.store_result(message, value, ttl)` stores by message identity and `get_result(message)` restores the value, including through another message object with the same identifying fields. A missing record raises `ResultMissing`. `store_exception` causes retrieval to raise `ResultFailure`, whose `orig_exc_type` names the original exception class.

When namespace-prefix keys are enabled, `build_message_key` returns `namespace:queue_name:actor_name:message_id`. In legacy mode it returns a 32-character lowercase hexadecimal key. The public `Missing` marker is distinct from `None`.

## Pipelines And Groups

**Pipelines.** The `|` operator chains messages into a pipeline. `pipeline(iterable)` also constructs a pipeline and flattens nested pipelines while retaining execution order. `run()` enqueues the initial work and returns the same pipeline. By default each downstream message receives the previous result as an additional argument. A downstream message with `pipe_ignore=True` uses only its own arguments and still becomes the source for the next link.

With stored results available, `get_results()` yields each link result in order and `get_result()` returns the final result. `completed_count` is the number of completed links and `completed` is true only when all links have completed. An unprocessed pipeline is incomplete, and requesting its final missing result raises `ResultMissing`.

**Groups.** `group(iterable)` preserves child order and may contain messages, pipelines, or nested groups. `run()` enqueues all children and returns the same group. `get_results()` yields message results, final pipeline results, and nested result lists in the corresponding shape. `completed_count`, `completed`, and `wait()` project completion state.

`add_completion_callback(message)` registers a callback that runs once after all group children finish. Running such a group requires `GroupCallbacks` middleware configured with a rate-limit backend and barrier TTL; otherwise `run()` raises `RuntimeError`.

## Rate Limiting

`Barrier(backend, key, ttl=...)` coordinates a fixed positive party count. `create(parties)` rejects zero or negative counts with `AssertionError`. Each nonblocking `wait(block=False)` consumes one arrival and returns false until the final party arrives; the final call returns true.

`ConcurrentRateLimiter(backend, key, limit=..., ttl=...)` exposes `acquire()` as a context manager. When capacity exists it yields true. When capacity is exhausted and `raise_on_failure=False`, it yields false. Leaving a successful context releases capacity so a later acquisition can succeed.

=== Contract Layer ===

## Product State Model

The central state consists of actor declarations, queue declarations, queued messages, in-flight consumer or worker messages, dead letters, middleware registrations, result records, composition metadata, and local rate-limit records. A message carries stable identity plus actor, queue, arguments, keyword arguments, options, and creation timestamp.

Actors project callable behavior and message factories over the same declaration. Brokers project queued state. Workers transition messages from queued to acknowledged, retried, skipped, or dead-letter state. Result middleware projects completed return values or failures by message identity. Pipelines and groups project aggregate completion and result order over their child messages.

## Error Semantics

| Condition | Required result |
|---|---|
| Invalid actor queue name | Raise `ValueError` |
| Unsupported actor option | Raise `ValueError` |
| Non-actor callback supplied to message options | Raise `TypeError` |
| Invalid encoded message bytes | Raise `DecodeError` |
| Unknown actor name | Raise `ActorNotFound` |
| Enqueue, consume, or join on an unknown queue | Raise `QueueNotFound` |
| Missing middleware insertion anchor | Raise `ValueError` |
| Missing result record | Raise `ResultMissing` |
| Stored actor exception retrieved as a result | Raise `ResultFailure` |
| Result requested implicitly when no result backend is available | Raise `RuntimeError` |
| Group callback used without `GroupCallbacks` middleware | Raise `RuntimeError` |
| Nonpositive barrier party count | Raise `AssertionError` |
| Concrete generic actor lacks `perform` | Raise `NotImplementedError` |

## Cross-View Invariants

1. Actor declaration metadata must match the actor's generated messages and broker registration.
2. Message identity and public fields must survive copies, encoding round trips, broker delivery, consumer acknowledgement, worker processing, and result lookup.
3. The active broker used to register an actor must also be the broker used by messages and compositions created from that actor.
4. A message must leave normal queued state exactly once through acknowledgement, skip, successful processing, retry transition, or dead-letter transition.
5. Middleware hooks must observe the same actor name, message data, result, and failure type exposed by actors, callbacks, and result retrieval.
6. Stored results and failures must be keyed by message identity, independent of the particular `Message` object used for retrieval.
7. Pipeline result order must match flattened message order, and each nonignored downstream input must derive from the immediately preceding result.
8. Group result shape and order must match its child message, pipeline, group structure.
9. Composition completion counts must agree with child result availability.
10. A successful concurrent-rate acquisition must release its slot when its context exits.

=== Reference Layer ===

## Installable Surface

### Public Import Surface

```python
import dramatiq
from dramatiq import Actor, GenericActor, Message, MessageProxy, Middleware, Worker
from dramatiq import actor, get_broker, get_encoder, group, pipeline, set_broker, set_encoder
from dramatiq.brokers.stub import StubBroker
from dramatiq.encoder import JSONEncoder, PickleEncoder
from dramatiq.errors import ActorNotFound, DecodeError, DramatiqError, QueueNotFound, Retry
from dramatiq.middleware import GroupCallbacks, SkipMessage
from dramatiq.rate_limits import Barrier, ConcurrentRateLimiter
from dramatiq.rate_limits.backends import StubBackend as RateLimitStubBackend
from dramatiq.results import Missing, ResultFailure, ResultMissing, Results
from dramatiq.results.backends import StubBackend as ResultStubBackend
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `actor` | decorator | Converts and registers a callable as an actor. |
| `Actor` | class | Callable actor plus message creation and sending API. |
| `GenericActor` | class | Class-oriented actor whose work is implemented by `perform`. |
| `Message` | class | Immutable task payload, identity, encoding, and composition unit. |
| `MessageProxy` | class | Delivery wrapper carrying acknowledgement and failure state. |
| `StubBroker` | class | In-process queue and dead-letter broker. |
| `Worker` | class | Executes broker messages against registered actors. |
| `Middleware` | class | Base lifecycle extension surface. |
| `Results` | middleware | Stores actor return values and failures. |
| `ResultStubBackend` | class | In-memory result backend. |
| `ResultMissing` | exception | Signals that no result record exists. |
| `ResultFailure` | exception | Projects a stored actor failure. |
| `group` | function | Builds an ordered aggregate of messages or compositions. |
| `pipeline` | function | Builds an ordered result-passing message chain. |
| `GroupCallbacks` | middleware | Runs callbacks after group completion. |
| `Retry` | exception | Requests another actor attempt. |
| `SkipMessage` | exception | Skips actor execution from middleware. |
| `JSONEncoder` | class | Encodes JSON-compatible message data. |
| `PickleEncoder` | class | Encodes general Python message data. |
| `Barrier` | class | Coordinates a fixed local party count. |
| `ConcurrentRateLimiter` | class | Limits concurrent local acquisitions. |
| `RateLimitStubBackend` | class | In-memory rate-limit state backend. |

### CLI Entry Points

The installed distribution may provide a `dramatiq` worker command, but command-line worker startup, process supervision, and service-backed configuration are outside this specification. The required workflows use the Python API.

## Invocation Protocol

Install the project as a normal Python distribution, import the public modules listed above, select a `StubBroker` with `set_broker`, declare actors, then invoke them directly or process their queued messages with `Worker`. Result and group-callback behavior is enabled by adding the corresponding middleware before declaring or sending work. All covered calls use ordinary Python values and local process resources.

=== Meta Layer ===

## Environment

The working environment runs Python 3.11 on Linux without network access. The third-party package `pytest` is preinstalled and importable. The target package is not pre-installed. No RabbitMQ, Redis, or other external service is available.

The project must include standard packaging metadata in `pyproject.toml` or `setup.py` so it can be installed with pip. Its imports must not depend on undeclared optional service clients for the local surface described here.

## Evaluation Notes

The implementation is exercised only through the public imports and deterministic local workflows listed above. Checks use fresh brokers, actors, queues, messages, result backends, and rate-limit backends. Worker runs use one worker thread and bounded joins. They do not depend on network access, live services, exact exception prose, exact log text, generated identifier values, private modules, or arbitrary delays.
