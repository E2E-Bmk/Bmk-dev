# Kombu Messaging Specification

## Product Overview

`kombu` is a Python messaging library that exposes broker connections, exchanges, queues, producers, consumers, message objects, and serializer registration through local Python APIs. This specification covers deterministic, service-free messaging behavior over the memory and filesystem transports, plus serializer and message-state behavior used by those transports.

The central product state is a set of connection settings, exchange declarations, queue declarations, bindings, routed messages, message bodies, headers, delivery properties, acknowledgement state, and serializer registrations. That state is visible through `Connection`, `Exchange`, `Queue`, `Producer`, `Consumer`, `Message`, `SimpleQueue`, `SimpleBuffer`, and the serialization functions.

## Scope

THE system SHALL support local Python use of the memory transport and filesystem transport without requiring an external broker.

THE system SHALL support direct, topic, and fanout exchange routing for messages published by `Producer` and consumed through `Queue`, `Consumer`, `SimpleQueue`, and `SimpleBuffer`.

THE system SHALL support JSON, raw text, raw bytes, and user-registered serializers through `dumps()`, `loads()`, `register()`, `unregister()`, and `registry`.

THE system SHALL expose connection metadata, entity declaration metadata, message metadata, payload decoding, acknowledgement state, and queue lifecycle operations through public attributes and methods.

## Non-Goals

- This specification does not require AMQP, Redis, SQS, Kafka, MongoDB, cloud, or other live broker services.
- This specification does not require socket retry, heartbeat, failover, pooling, asynchronous hub, or event-loop internals.
- This specification does not require private modules, private attributes, private helper functions, exact `repr()` formatting, exact error message wording, or log message wording.
- This specification does not require compression codecs, SSL handshakes, URL forms outside the examples described here, or transport-specific internals beyond the documented memory and filesystem transport options.

## Representative Workflows

**Publish and get a JSON message.**

```python
from kombu import Connection, Exchange, Producer, Queue

with Connection("memory://") as conn:
    exchange = Exchange("orders", "direct", durable=False)
    queue = Queue("orders.created", exchange, routing_key="orders.created", durable=False)
    Producer(conn).publish({"id": 7}, exchange=exchange, routing_key="orders.created", declare=[queue], serializer="json")
    message = queue(conn.default_channel).get(accept=["json"])
    message.ack()
```

**Consume through a callback.**

```python
from kombu import Connection, Consumer, Exchange, Producer, Queue

received = []
with Connection("memory://") as conn:
    exchange = Exchange("events", "direct", durable=False)
    queue = Queue("events.ready", exchange, routing_key="ready", durable=False)

    def callback(body, message):
        received.append((body, message.delivery_info))
        message.ack()

    with Consumer(conn, [queue], callbacks=[callback], accept=["json"]):
        Producer(conn).publish({"ready": True}, exchange=exchange, routing_key="ready", declare=[queue])
        conn.drain_events(timeout=1)
```

**Use a local filesystem transport.**

```python
from kombu import Connection, Exchange, Producer, Queue

options = {
    "data_folder_in": "incoming",
    "data_folder_out": "incoming",
    "processed_folder": "processed",
    "store_processed": True,
}

with Connection("filesystem://", transport_options=options) as conn:
    exchange = Exchange("fs", "direct", durable=False)
    queue = Queue("fs.q", exchange, routing_key="fs.rk", durable=False)
    Producer(conn).publish({"stored": True}, exchange=exchange, routing_key="fs.rk", declare=[queue])
```

## Connection And Transport Behavior

`parse_url()` SHALL parse a broker URL into a dictionary containing public connection fields such as `transport`, `hostname`, `port`, `userid`, `password`, `virtual_host`, and query-string options.

WHEN constructed without a URL, `Connection` SHALL expose default connection information through `info()` with host `localhost`, user `guest`, password `guest`, virtual host `/`, transport `amqp`, and port `5672`.

WHEN constructed with `memory://`, `Connection` SHALL report `transport_cls` as `memory`, `info()["transport"]` as `memory`, and `info()["virtual_host"]` as `/` before a channel is opened.

WHEN `Connection.as_uri()` is called without opting into password display, THE returned URI SHALL mask the password component.

WHEN `Connection.channel()` or `Connection.default_channel` opens a memory transport channel, THE `connected` attribute SHALL become true. WHEN `Connection.release()` completes, THE `connected` attribute SHALL become false.

WHEN `Connection.supports_exchange_type()` is called for `direct`, `topic`, or `fanout` on the memory transport, THE result SHALL be true.

WHEN constructed with `filesystem://` and `transport_options`, `Connection` SHALL report `transport_cls` as `filesystem`, `info()["transport"]` as `filesystem`, and `info()["transport_options"]` as the supplied options mapping.

WHEN used as a context manager, `Connection` SHALL return an active connection object inside the context and release its transport when the context exits.

`Connection.Producer()`, `Connection.Consumer()`, `Connection.SimpleQueue()`, and `Connection.SimpleBuffer()` SHALL create producer, consumer, and simple queue facades bound to that connection.

## Entity Declaration Behavior

`Exchange` SHALL represent a named exchange with public declaration options including `name`, `type`, `durable`, `auto_delete`, `passive`, `arguments`, `delivery_mode`, and `no_declare`.

WHEN `Exchange.as_dict()` is called, THE returned mapping SHALL expose the exchange declaration options. WHERE delivery mode is supplied as `persistent`, THE projected `delivery_mode` SHALL be numeric value `2` and durable delivery SHALL remain enabled.

`Queue` SHALL represent a named queue with an exchange, routing key, durability flag, acknowledgement policy, queue arguments, consumer arguments, and declaration behavior.

WHEN `Queue.as_dict()` is called, THE returned mapping SHALL expose `name`, `exchange`, `routing_key`, `queue_arguments`, `consumer_arguments`, and `no_ack`.

WHEN `Queue.as_dict(recurse=True)` is called, THE returned mapping SHALL include an exchange projection containing the exchange `name` and `type`.

WHEN a `Queue` is called with a channel, THE result SHALL be a bound queue whose `is_bound` attribute is true and whose `channel` is that channel, while the original queue remains unbound.

WHEN a bound queue is declared on the memory transport through `declare()`, THE returned value SHALL be the queue name.

WHEN `Queue.delete()` is called on an existing or already-deleted memory queue, THE operation SHALL complete without returning a count. WHEN pending messages are present in that queue, deletion SHALL make later `get()` calls return no message.

WHEN `Queue.purge()` is called, THE returned value SHALL be the number of pending messages removed from the queue.

## Message State And Payload Behavior

`Message` SHALL expose public attributes `body`, `content_type`, `content_encoding`, `headers`, `properties`, `delivery_tag`, `delivery_info`, and `acknowledged`.

WHEN `Message.payload` is read for a JSON body with UTF-8 encoding, THE body SHALL be decoded into the corresponding Python value and the decoded value SHALL be cached lazily for normal repeated use.

WHEN `Message.payload` is read for raw text or binary application data, THE body SHALL be returned as the corresponding text string or bytes according to its content encoding.

WHEN `Message.ack()` is called, THE message SHALL call the channel `basic_ack` operation with the message `delivery_tag`, forward the `multiple` flag, return `None`, and set `acknowledged` to true.

WHEN `Message.reject()` is called, THE message SHALL call the channel `basic_reject` operation with the message `delivery_tag`, forward the `requeue` flag, return `None`, and set `acknowledged` to true.

IF `Message.ack()` or `Message.reject()` is called after the message has already been acknowledged or rejected, THEN THE system SHALL raise `MessageStateError`.

IF a JSON message body is structurally invalid and `payload` is read, THEN THE system SHALL raise `DecodeError`.

## Serialization Behavior

`dumps()` SHALL encode Python dictionaries through the JSON serializer by default, returning a content type, content encoding, and payload bytes or text compatible with `loads()`.

`dumps()` and `loads()` SHALL preserve `Decimal` values through the JSON round trip supported by Kombu's JSON serializer.

WHEN `dumps()` receives a plain string without an explicit serializer, THE result SHALL use content type `text/plain`, encoding `utf-8`, and UTF-8 bytes.

WHEN `dumps()` receives bytes without an explicit serializer, THE result SHALL use content type `application/data`, encoding `binary`, and the same bytes.

WHEN `dumps()` is called with serializer `raw` for text, THE result SHALL use content type `application/data`, encoding `utf-8`, and UTF-8 bytes.

WHEN `loads()` receives trusted plain text without an accept list, THE result SHALL decode the text payload.

WHEN `loads()` receives an accept list, THE list SHALL contain accepted content types. IF JSON content is supplied with accept list value `json` rather than `application/json`, THEN THE system SHALL raise `ContentDisallowed`.

WHEN `loads()` receives an unknown content type and no accept list blocks it, THE raw decoded payload SHALL be returned.

IF `dumps()` names an unavailable serializer, THEN THE system SHALL raise `SerializerNotInstalled`.

IF `loads()` receives pickle content without explicitly allowing that content type, THEN THE system SHALL raise `ContentDisallowed`.

`register()` SHALL add a named serializer with encoder, decoder, content type, and content encoding to the public serialization registry. `unregister()` SHALL remove that serializer so later `dumps()` calls with the same name raise `SerializerNotInstalled`.

`registry.name_to_type` and `registry.type_to_name` SHALL expose the mapping between serializer names and content types, including JSON and `application/json`.

## Routing And Consumer Behavior

WHEN `Producer.publish()` publishes a JSON payload to a declared direct exchange and matching queue, `Queue.get(accept=["json"])` SHALL return a `Message` whose `payload` is the original Python value and whose `delivery_info` records the exchange name and routing key.

WHEN a message is fetched through `Queue.get()` and acknowledged through `Message.ack()`, THE message SHALL be removed from the queue.

WHEN a message is fetched and rejected with `requeue=False`, THE message SHALL be removed from the queue. WHEN rejected with `requeue=True`, THE same payload SHALL be available from a later `Queue.get()`.

WHEN a direct exchange has multiple queues with distinct routing keys, THE exchange SHALL deliver only to queues whose routing key matches the publish routing key.

WHEN a topic exchange has a `*` binding segment, THE binding SHALL match one routing-key word in the exercised workflow and SHALL not match an unrelated topic prefix. WHEN a topic exchange has a `#` binding suffix, THE binding SHALL match multiple routing-key words.

WHEN a fanout exchange publishes a message to multiple declared queues, THE exchange SHALL deliver a copy to each bound queue.

WHEN `Consumer` is created with queues, callbacks, and accepted serializers, entering the consumer context and calling `Connection.drain_events()` SHALL deliver decoded bodies and `Message` objects to callbacks.

IF a delivered message uses a content type not accepted by the caller, THEN reading the message payload SHALL raise `ContentDisallowed`.

WHEN `Producer.publish()` supplies headers, `correlation_id`, `reply_to`, `priority`, or `delivery_mode`, THE resulting `Message.headers` and `Message.properties` SHALL preserve those values.

WHEN multiple consumers are active on one connection, repeated `Connection.drain_events()` calls SHALL dispatch messages to the callbacks for the queues where the messages were routed.

## Simple Queue And Filesystem Behavior

`SimpleQueue` SHALL provide `put()`, `get()`, `get_nowait()`, `clear()`, `close()`, and public `Empty` behavior over a named queue.

WHEN `SimpleQueue.put()` stores a JSON payload and `SimpleQueue.get(block=False)` retrieves it, THE returned `Message.payload` SHALL match the original value and `Message.ack()` SHALL acknowledge it. WHEN no message remains, `SimpleQueue.get_nowait()` SHALL raise `SimpleQueue.Empty`.

WHEN `SimpleQueue.clear()` removes buffered messages, THE returned value SHALL be the number of removed messages and later `get_nowait()` SHALL raise `SimpleQueue.Empty`.

`SimpleBuffer` SHALL provide the same `put()`, `get()`, acknowledgement, and `close()` workflow for transient buffer use.

WHEN the filesystem transport publishes a declared message, THE configured `data_folder_in` directory SHALL contain one file and `processed_folder` SHALL remain empty before a get operation.

WHEN a filesystem transport message is fetched and acknowledged with `store_processed` enabled, THE data directory SHALL be empty and the processed directory SHALL contain one file.

WHEN a filesystem transport message is published by one `Connection` and read by another `Connection` using the same transport options, THE payload SHALL persist across the connection boundary.

## Product State Model

The product state consists of connection configuration, opened transport channels, exchange declarations, queue declarations, queue bindings, routed message records, serialized body bytes or text, content type, content encoding, message headers, message properties, delivery information, acknowledgement state, registered serializers, and filesystem transport files.

Public projections of this state are:

1. `Connection.info()`, `Connection.as_uri()`, `connected`, `transport_cls`, `default_channel`, `supports_exchange_type()`, and context manager state.
2. `Exchange.as_dict()` and `Queue.as_dict()` declaration mappings.
3. Bound `Queue` operations `declare()`, `get()`, `purge()`, and `delete()`.
4. `Message.payload`, `headers`, `properties`, `delivery_tag`, `delivery_info`, `content_type`, `content_encoding`, and `acknowledged`.
5. `Consumer` callback inputs after `Connection.drain_events()`.
6. `SimpleQueue` and `SimpleBuffer` facade operations.
7. `dumps()`, `loads()`, `register()`, `unregister()`, `registry.name_to_type`, and `registry.type_to_name`.
8. Files present in filesystem transport data and processed directories.

## Error Semantics

| Condition | Required result |
|---|---|
| `Message.ack()` is called after prior acknowledgement or rejection | raises `MessageStateError` |
| `Message.reject()` is called after prior acknowledgement or rejection | raises `MessageStateError` |
| `Message.payload` decodes invalid JSON | raises `DecodeError` |
| `loads()` receives content blocked by the accept list | raises `ContentDisallowed` |
| `loads()` receives pickle content without explicit acceptance | raises `ContentDisallowed` |
| `dumps()` names an unavailable serializer | raises `SerializerNotInstalled` |
| `SimpleQueue.get_nowait()` finds no available message | raises `SimpleQueue.Empty` |

## Cross-View Invariants

1. A message published through `Producer.publish()` to a declared queue must appear through `Queue.get()`, `Consumer` callbacks, and simple queue facades according to the same exchange, queue, and routing-key declarations.
2. The payload visible through `Message.payload` must be the decoded form of the body produced by the selected serializer, and message metadata must preserve content type, content encoding, headers, properties, exchange, and routing key.
3. Acknowledgement and rejection state must be consistent across `Queue.get()`, `Message.ack()`, `Message.reject()`, queue removal, requeue behavior, and simple queue empty behavior.
4. Serializer registration state must be shared by low-level `dumps()` and `loads()` calls and by `Producer.publish()` followed by `Queue.get()`.
5. Connection lifecycle state must be reflected consistently through channels, producer shortcuts, consumer shortcuts, context manager release, and `connected`.
6. Filesystem transport message files must project the same message state that `Queue.get()` and `Message.payload` expose, and processed-file movement must follow successful retrieval and acknowledgement.

## Installable Surface

### Public Import Surface

```python
from kombu import Connection, Consumer, Exchange, Producer, Queue, parse_url
```

```python
from kombu.message import Message
```

```python
from kombu.serialization import dumps, loads, register, registry, unregister
```

```python
from kombu.exceptions import ContentDisallowed, DecodeError, MessageStateError, SerializerNotInstalled
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Connection` | class | Creates and manages broker transport connections and bound helper facades. |
| `Connection.info()` | method | Returns public connection metadata. |
| `Connection.as_uri()` | method | Returns a URI projection with password masking by default. |
| `Connection.channel()` | method | Opens a transport channel. |
| `Connection.release()` | method | Releases an opened transport connection. |
| `Connection.supports_exchange_type()` | method | Reports whether the active transport supports an exchange type. |
| `Connection.Producer()` | method | Creates a producer bound to the connection. |
| `Connection.Consumer()` | method | Creates a consumer bound to the connection. |
| `Connection.SimpleQueue()` | method | Creates a simple named queue facade. |
| `Connection.SimpleBuffer()` | method | Creates a transient simple buffer facade. |
| `Connection.drain_events()` | method | Dispatches pending messages to active consumer callbacks. |
| `Connection.connected` | attribute | Reports whether the connection has an open transport. |
| `Connection.transport_cls` | attribute | Reports the selected transport name. |
| `Connection.default_channel` | attribute | Provides the connection's default channel. |
| `Exchange` | class | Represents an exchange declaration. |
| `Exchange.as_dict()` | method | Projects exchange declaration options. |
| `Exchange.name` | attribute | Stores the exchange name. |
| `Exchange.type` | attribute | Stores the exchange type. |
| `Queue` | class | Represents a queue declaration and binding. |
| `Queue.as_dict()` | method | Projects queue declaration and consumer options. |
| `Queue.declare()` | method | Declares a bound queue. |
| `Queue.delete()` | method | Deletes a bound queue. |
| `Queue.purge()` | method | Removes pending messages and returns a count. |
| `Queue.get()` | method | Retrieves a message or returns no message. |
| `Queue.is_bound` | attribute | Reports whether a queue is bound to a channel. |
| `Queue.channel` | attribute | Stores the bound channel. |
| `Producer` | class | Publishes serialized messages to exchanges and queues. |
| `Producer.publish()` | method | Serializes and routes a message. |
| `Consumer` | class | Registers queues and callbacks for delivery. |
| `Message` | class | Represents a delivered message with body, metadata, payload, and acknowledgement state. |
| `Message.payload` | property | Decodes and returns the message body. |
| `Message.ack()` | method | Acknowledges a delivered message. |
| `Message.reject()` | method | Rejects a delivered message, optionally requeueing it. |
| `Message.headers` | attribute | Stores message headers. |
| `Message.properties` | attribute | Stores message properties. |
| `Message.delivery_tag` | attribute | Stores the broker delivery tag. |
| `Message.delivery_info` | attribute | Stores exchange and routing-key delivery metadata. |
| `Message.content_type` | attribute | Stores the message content type. |
| `Message.content_encoding` | attribute | Stores the message content encoding. |
| `Message.acknowledged` | attribute | Reports acknowledgement or rejection state. |
| `parse_url()` | function | Parses connection URLs into connection fields. |
| `dumps()` | function | Serializes Python values and returns content metadata plus payload. |
| `loads()` | function | Deserializes payloads under content-type acceptance policy. |
| `register()` | function | Adds a named serializer. |
| `unregister()` | function | Removes a named serializer. |
| `registry` | object | Exposes serializer name and content-type mappings. |
| `registry.name_to_type` | attribute | Maps serializer names to content types. |
| `registry.type_to_name` | attribute | Maps content types to serializer names. |
| `ContentDisallowed` | exception | Signals blocked content under deserialization policy. |
| `DecodeError` | exception | Signals payload decoding failure. |
| `MessageStateError` | exception | Signals invalid acknowledgement state transitions. |
| `SerializerNotInstalled` | exception | Signals an unavailable serializer name. |
| `SimpleQueue.put()` | method | Stores a message through a simple queue facade. |
| `SimpleQueue.get()` | method | Retrieves a message through a simple queue facade. |
| `SimpleQueue.get_nowait()` | method | Retrieves without blocking or raises `SimpleQueue.Empty`. |
| `SimpleQueue.clear()` | method | Removes queued messages and returns a count. |
| `SimpleQueue.close()` | method | Closes the facade. |
| `SimpleQueue.Empty` | exception attribute | Signals that no message is available. |
| `SimpleBuffer.put()` | method | Stores a message through a transient buffer facade. |
| `SimpleBuffer.get()` | method | Retrieves a message through a transient buffer facade. |
| `SimpleBuffer.close()` | method | Closes the facade. |

## Invocation Protocol

The implementation is invoked as a Python package named `kombu`. Users import the public symbols listed in the installable surface and exercise them directly from Python. The covered workflows do not require command-line entry points or external services.

Tests are expected to run from an environment where the implementation package is installed or placed on `PYTHONPATH`, then executed with:

```bash
python -m pytest <test-directory> -q
```

## Environment

The working environment runs Python 3.11 on Linux without network access. The support packages `pytest`, `pytest-json-report`, `amqp`, `vine`, and `tzdata` are preinstalled and importable. The target package is not pre-installed. The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so the package can be installed with pip.

## Evaluation Notes

Assertions are limited to documented or publicly importable APIs. The covered behavior intentionally avoids live transports, cloud credentials, private transport tables, asynchronous internals, sleeps, retry timing, exact exception text, exact representation strings, and log wording.

The memory and filesystem transports are used because they provide deterministic local projections of connection, routing, queue, message, acknowledgement, serializer, and file state.
