# h2 Specification

## Product Overview

h2 is a pure-Python HTTP/2 protocol stack. It models a single HTTP/2 connection in memory, transforms caller actions into outbound HTTP/2 wire bytes, and transforms inbound HTTP/2 wire bytes into event objects. It does not perform socket I/O, TLS negotiation, scheduling, concurrency control, or application routing.

The central object is `h2.connection.H2Connection`. A caller creates one connection object for each peer connection, calls methods such as `initiate_connection()`, `send_headers()`, `send_data()`, and `update_settings()`, sends the bytes returned by `data_to_send()`, and passes received bytes to `receive_data()` to obtain public event objects.

## Scope

This specification covers the documented public API used to build HTTP/2 clients and servers:

- Connection setup, upgrade setup, outbound byte buffering, and inbound event decoding through `H2Connection`.
- Request, response, trailers, data, settings, ping, priority, reset, GOAWAY, alternative service, unknown-frame, and flow-control events.
- Public configuration options in `H2Configuration`.
- Public settings objects, settings codes, changed-setting records, HTTP/2 error codes, and documented exception classes.
- Stream ID allocation, stream lifecycle, per-stream and connection flow-control queries, and public error behavior.

## Installable Surface

The package is installed as `h2`. The public import paths covered here are:

```python
import h2
from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.errors import ErrorCodes
from h2.events import (
    AlternativeServiceAvailable,
    ConnectionTerminated,
    DataReceived,
    Event,
    InformationalResponseReceived,
    PingAckReceived,
    PingReceived,
    PriorityUpdated,
    PushedStreamReceived,
    RemoteSettingsChanged,
    RequestReceived,
    ResponseReceived,
    SettingsAcknowledged,
    StreamEnded,
    StreamReset,
    TrailersReceived,
    UnknownFrameReceived,
    WindowUpdated,
)
from h2.exceptions import (
    DenialOfServiceError,
    FlowControlError,
    FrameDataMissingError,
    FrameTooLargeError,
    H2Error,
    InvalidBodyLengthError,
    InvalidSettingsValueError,
    NoAvailableStreamIDError,
    NoSuchStreamError,
    ProtocolError,
    RFC1122Error,
    StreamClosedError,
    StreamIDTooLowError,
    TooManyStreamsError,
    UnsupportedFrameError,
)
from h2.settings import ChangedSetting, SettingCodes, Settings
```

`h2.__version__` returns the package version string. The package exposes no console script.

## Public API

### Configuration

```python
H2Configuration(
    client_side: bool = True,
    header_encoding: bool | str | None = None,
    validate_outbound_headers: bool = True,
    normalize_outbound_headers: bool = True,
    split_outbound_cookies: bool = False,
    validate_inbound_headers: bool = True,
    normalize_inbound_headers: bool = True,
    logger: object | None = None,
)
```

`client_side` must control stream-ID parity, connection preface behavior, server-push availability, and request/response interpretation. Boolean configuration fields must raise `ValueError` when assigned a non-boolean value. `header_encoding` must accept `None`, `False`, or a string encoding name, must return headers as bytes when set to `None` or `False`, must decode received header names and values when set to a string encoding, and must raise `ValueError` when set to `True` or to any other unsupported type. Header validation and normalization flags must control whether outbound and inbound header blocks are checked or normalized.

### Connection

```python
H2Connection(config: H2Configuration | None = None)
```

When `config` is omitted, the connection must behave as a client-side connection with default configuration.

`H2Connection` exposes these documented methods and properties:

```python
open_outbound_streams: int
open_inbound_streams: int
initiate_connection() -> None
initiate_upgrade_connection(settings_header: bytes | None = None) -> bytes | None
get_next_available_stream_id() -> int
send_headers(stream_id: int, headers, end_stream: bool = False, priority_weight: int | None = None, priority_depends_on: int | None = None, priority_exclusive: bool | None = None) -> None
send_data(stream_id: int, data: bytes | memoryview, end_stream: bool = False, pad_length=None) -> None
end_stream(stream_id: int) -> None
increment_flow_control_window(increment: int, stream_id: int | None = None) -> None
push_stream(stream_id: int, promised_stream_id: int, request_headers) -> None
ping(opaque_data: bytes) -> None
reset_stream(stream_id: int, error_code: ErrorCodes | int = 0) -> None
close_connection(error_code: ErrorCodes | int = 0, additional_data: bytes | None = None, last_stream_id: int | None = None) -> None
update_settings(new_settings: dict[SettingCodes | int, int]) -> None
advertise_alternative_service(field_value: bytes | str, origin: bytes | None = None, stream_id: int | None = None) -> None
prioritize(stream_id: int, weight: int | None = None, depends_on: int | None = None, exclusive: bool | None = None) -> None
local_flow_control_window(stream_id: int) -> int
remote_flow_control_window(stream_id: int) -> int
acknowledge_received_data(acknowledged_size: int, stream_id: int) -> None
data_to_send(amount: int | None = None) -> bytes
clear_outbound_data_buffer() -> None
receive_data(data) -> list[Event]
```

### Settings and Codes

`ErrorCodes` is an `IntEnum` containing `NO_ERROR`, `PROTOCOL_ERROR`, `INTERNAL_ERROR`, `FLOW_CONTROL_ERROR`, `SETTINGS_TIMEOUT`, `STREAM_CLOSED`, `FRAME_SIZE_ERROR`, `REFUSED_STREAM`, `CANCEL`, `COMPRESSION_ERROR`, `CONNECT_ERROR`, `ENHANCE_YOUR_CALM`, `INADEQUATE_SECURITY`, and `HTTP_1_1_REQUIRED`.

`SettingCodes` is an `IntEnum` containing `HEADER_TABLE_SIZE`, `ENABLE_PUSH`, `MAX_CONCURRENT_STREAMS`, `INITIAL_WINDOW_SIZE`, `MAX_FRAME_SIZE`, `MAX_HEADER_LIST_SIZE`, and `ENABLE_CONNECT_PROTOCOL`.

```python
ChangedSetting(setting: SettingCodes | int, original_value: int | None, new_value: int)
Settings(client: bool = True, initial_values: dict[SettingCodes, int] | None = None)
```

`ChangedSetting` must expose `setting`, `original_value`, and `new_value`. `Settings` must behave as a mutable mapping from `SettingCodes` or integer setting identifiers to integer values. Its properties must read and write the matching settings: `header_table_size`, `enable_push`, `initial_window_size`, `max_frame_size`, `max_concurrent_streams`, `max_header_list_size`, and `enable_connect_protocol`. `Settings.acknowledge()` must apply pending values and return a dictionary of `ChangedSetting` objects for settings whose active value changed. Invalid settings values must raise `InvalidSettingsValueError` with an HTTP/2 error code appropriate to the invalid setting.

### Events

All events inherit from `h2.events.Event`. Event classes must expose the documented attributes below; tests and callers must not rely on exact `repr()` text.

- `RequestReceived`: `stream_id`, `headers`, `stream_ended`, `priority_updated`.
- `ResponseReceived`: `stream_id`, `headers`, `stream_ended`, `priority_updated`.
- `TrailersReceived`: `stream_id`, `headers`, `stream_ended`, `priority_updated`.
- `InformationalResponseReceived`: `stream_id`, `headers`, `priority_updated`.
- `DataReceived`: `stream_id`, `data`, `flow_controlled_length`, `stream_ended`.
- `WindowUpdated`: `stream_id`, `delta`.
- `RemoteSettingsChanged`: `changed_settings`; `from_settings(old_settings, new_settings)` returns a populated event.
- `PingReceived`: `ping_data`.
- `PingAckReceived`: `ping_data`.
- `StreamEnded`: `stream_id`.
- `StreamReset`: `stream_id`, `error_code`, `remote_reset`.
- `PushedStreamReceived`: `pushed_stream_id`, `parent_stream_id`, `headers`.
- `SettingsAcknowledged`: `changed_settings`.
- `PriorityUpdated`: `stream_id`, `weight`, `depends_on`, `exclusive`.
- `ConnectionTerminated`: `error_code`, `last_stream_id`, `additional_data`.
- `AlternativeServiceAvailable`: `origin`, `field_value`.
- `UnknownFrameReceived`: `frame`.

## Product State Model

A connection has three public projections of the same protocol state:

- The outbound byte projection returned and drained by `data_to_send()`.
- The inbound event projection returned by `receive_data()`.
- The public connection/settings/window projection exposed by documented methods, properties, `Settings`, `ChangedSetting`, and event attributes.

These projections must agree. When a caller performs an outbound action, the action must produce bytes retrievable by `data_to_send()` or must raise a documented exception. When those bytes are supplied to a compatible peer connection, that peer must return the corresponding public events and update its public settings or flow-control projections. When a connection receives peer bytes that require automatic protocol acknowledgments, `receive_data()` must return the triggering events and must buffer any automatic response bytes for `data_to_send()`.

## Connection Lifecycle and Byte Buffering

`initiate_connection()` must prepare the initial SETTINGS data for both clients and servers. For client-side connections it must also prepare the HTTP/2 client connection preface. It must not return bytes directly; callers retrieve prepared bytes with `data_to_send()`. Calling `data_to_send()` with no amount must return all currently buffered outbound bytes and empty the buffer. Calling it with an integer amount must return at most that many bytes and retain any remaining bytes for later calls. Calling it when no bytes are buffered must return `b""`. `clear_outbound_data_buffer()` must discard buffered bytes so that the next `data_to_send()` call returns `b""`.

`initiate_upgrade_connection()` must prepare the h2c upgrade state. On a client connection it must return the bytes value to place in the `HTTP2-Settings` header and must buffer the post-upgrade connection bytes. On a server connection it must accept the client settings header bytes, apply those remote settings, set up stream 1 in the appropriate half-closed state, buffer server preface data, and return `None`. A server call without a settings header must still initialize upgrade state, and malformed header bytes must raise a protocol or decoding exception rather than silently accepting invalid input. The exact serialized SETTINGS frame entry order, byte length, and h2c header byte literal are not part of this API contract; callers must treat these values as opaque HTTP/2 protocol bytes and validate them by sending them to a compatible peer.

`receive_data(data)` must accept bytes-like input, process complete HTTP/2 frames, return a list of public event objects, and buffer any automatic protocol response bytes. If data is incomplete, it must retain it until enough bytes arrive to complete a frame. Protocol violations must raise a documented `H2Error` subclass and must buffer connection-closing bytes when the connection is terminated as a result.

## Headers, Data, and Events

`send_headers()` must send request headers when called on a client-initiated stream, response headers when called on a server for an inbound stream, informational response headers for `:status` values in the 100 range, and trailers when called after the main header block on an open stream. Client streams must use odd stream IDs and server-pushed streams must use even stream IDs. Server connections must raise `ProtocolError` when asked to open a new stream by sending response headers on an unused stream.

Header collections must preserve order. Header names and values accepted as text must be encoded for the wire. Received headers must be returned as bytes unless `H2Configuration.header_encoding` is a string, in which case names and values must be decoded with that encoding. If outbound validation is enabled, malformed pseudo-header order, invalid pseudo-header use, uppercase header names, forbidden connection-specific headers, invalid TE values, duplicate pseudo-headers, or missing required request or response pseudo-headers must raise `ProtocolError`.

`send_data()` must buffer DATA bytes for an existing stream. `data` must be bytes-like. When `end_stream=True`, the DATA frame must close the local side of the stream and a compatible peer must receive a `DataReceived` event with a related `StreamEnded` event. Sending data larger than the available stream flow-control window, connection flow-control window, or maximum outbound frame size must raise `FlowControlError` or `FrameTooLargeError` and must not emit the oversized DATA bytes.

`end_stream(stream_id)` must end the local side of a stream without application data. A compatible peer must receive a `StreamEnded` event. Ending or sending on a nonexistent or already closed stream must raise `NoSuchStreamError`, `StreamClosedError`, or `ProtocolError`.

`receive_data()` must translate inbound HEADERS, DATA, SETTINGS, PING, WINDOW_UPDATE, RST_STREAM, GOAWAY, PUSH_PROMISE, PRIORITY, ALTSVC, and unknown extension frames into the matching public events listed in this specification. If one inbound frame causes multiple public events, the primary event's related-event attributes must point to the simultaneous related event and the related event must also appear in the returned event list.

## Stream Lifecycle

`get_next_available_stream_id()` must return the next stream ID this endpoint is allowed to initiate: odd IDs for clients and even IDs for servers. The returned value must not advance until a stream is actually opened by sending or pushing headers. If all stream IDs are exhausted, it must raise `NoAvailableStreamIDError`.

`open_outbound_streams` and `open_inbound_streams` must return counts of currently open streams in the matching direction. Closing streams by ending both sides, resetting, or receiving a terminal close event must reduce those counts after the stream leaves the open state.

`push_stream()` must be available to server-side connections for a stream that permits server push. It must buffer a PUSH_PROMISE for `promised_stream_id` with `request_headers`, and a compatible client peer must receive `PushedStreamReceived` carrying the pushed stream ID, parent stream ID, and headers. It must raise `ProtocolError` when used on a client connection, when push is disabled by peer settings, when the parent stream does not permit push, or when the promised stream ID is invalid.

`reset_stream()` must buffer an RST_STREAM for an existing stream and close local state for that stream. A compatible peer must receive `StreamReset` with the stream ID, error code, and `remote_reset=True`. Resetting a nonexistent or closed stream must raise a documented stream/protocol exception.

`close_connection()` must buffer a GOAWAY frame. A compatible peer must receive `ConnectionTerminated` containing the error code, last stream ID, and additional data. After a connection is closed, attempts to create new streams or send further protocol actions must raise `ProtocolError`.

## Settings Behavior

`Settings` defaults must match HTTP/2 defaults: header table size `4096`, initial window size `65535`, maximum frame size `16384`, enable connect protocol `0`, and enable push equal to `1` for client-owned settings and `0` for server-owned settings. `max_concurrent_streams` must return `2**32 + 1` when unset. `max_header_list_size` must return `None` when unset. `initial_values` must override the matching active defaults when valid.

`H2Connection` must initialize its local advertised settings from those defaults with `MAX_CONCURRENT_STREAMS` set to `100` and `MAX_HEADER_LIST_SIZE` set to `65536`. When a connection sends its initial SETTINGS, a compatible peer must treat those advertised values as that peer's active remote settings after processing the bytes. When that peer later receives an update for the same setting, `RemoteSettingsChanged.changed_settings[setting].original_value` must report the previous active remote value and `new_value` must report the value from the received update.

Assigning a setting through mapping syntax or a property must stage a new value until `acknowledge()` applies it. `acknowledge()` must return only settings whose active value changed, and each returned `ChangedSetting` must report the previous active value and the newly active value. Unknown integer settings must be stored and acknowledged like known settings unless their value is invalid under known validation rules.

`update_settings(new_settings)` must stage local settings, buffer a SETTINGS frame, and leave the new local values pending until the peer acknowledges them. Receiving a non-ACK SETTINGS frame must return `RemoteSettingsChanged` and must buffer a SETTINGS acknowledgement automatically. Receiving a SETTINGS acknowledgement must return `SettingsAcknowledged` containing the local settings that became active. Receiving an invalid setting value must raise `InvalidSettingsValueError`.

## Flow Control

`local_flow_control_window(stream_id)` must return the maximum number of data bytes the local endpoint is currently allowed to send on the stream, constrained by both the stream and connection outbound windows. `remote_flow_control_window(stream_id)` must return the maximum number of flow-controlled bytes the remote peer is currently allowed to send on the stream, constrained by both the stream and connection inbound windows. When a stream has fully closed but the connection still retains that stream's state, `local_flow_control_window(stream_id)` must return the remaining outbound flow-control window for that retained stream. When no stream state exists for the stream ID, or the stream state has been purged, flow-control queries must raise the documented stream exception.

Inbound `DataReceived.flow_controlled_length` must include bytes that count against HTTP/2 flow control, including padding. `acknowledge_received_data(acknowledged_size, stream_id)` must mark received bytes as processed and buffer WINDOW_UPDATE frames when the connection or stream window should be reopened. It must raise `ValueError` for `stream_id <= 0` or negative acknowledged sizes. `increment_flow_control_window(increment, stream_id=None)` must buffer a connection-level WINDOW_UPDATE when `stream_id` is omitted, and a stream-level WINDOW_UPDATE when a stream ID is provided. Invalid increments or invalid stream IDs must raise a documented exception.

Receiving WINDOW_UPDATE frames must return `WindowUpdated` events. A stream-level update must identify that stream; a connection-level update must use stream ID `0`. Receiving changes to `SETTINGS_INITIAL_WINDOW_SIZE` must update existing stream flow-control windows consistently with the new setting.

## Ping, Priority, and Alternative Services

`ping(opaque_data)` must require `opaque_data` to be a `bytes` object of length exactly eight. It must buffer a PING frame, and a compatible peer must return `PingReceived` and buffer a matching acknowledgement. Receiving that acknowledgement must return `PingAckReceived` with the same opaque bytes. Text strings are invalid and must raise `ValueError`, even when they contain eight characters. Bytes objects with any length other than eight and non-`bytes` values such as `bytearray` or `memoryview` must raise `ValueError`.

`prioritize()` must be available on client-side connections and must buffer priority information for the given stream. A compatible server peer must receive `PriorityUpdated` with stream ID, weight, dependency, and exclusivity values. Server-side calls to `prioritize()` must raise `RFC1122Error`. Invalid priority values must raise a documented error.

`advertise_alternative_service()` must buffer an ALTSVC advertisement. Exactly one of `origin` or `stream_id` must identify the advertised origin. `field_value` must be bytes; non-bytes values must raise `ValueError`. Supplying both `origin` and `stream_id` must raise `ValueError`. A compatible client peer must receive `AlternativeServiceAvailable` with the origin and field value.

## Error Semantics

All h2-specific exceptions must inherit from `H2Error`. `ProtocolError` must carry `ErrorCodes.PROTOCOL_ERROR`. `FrameTooLargeError` and `FrameDataMissingError` must carry `ErrorCodes.FRAME_SIZE_ERROR`. `FlowControlError` must carry `ErrorCodes.FLOW_CONTROL_ERROR`. `DenialOfServiceError` must carry `ErrorCodes.ENHANCE_YOUR_CALM`. `InvalidSettingsValueError` must inherit from both `ProtocolError` and `ValueError`, and its `error_code` must match the invalid setting's protocol error.

`StreamIDTooLowError` must expose `stream_id` and `max_stream_id`. `NoSuchStreamError` and `StreamClosedError` must expose `stream_id`; `StreamClosedError` must carry `ErrorCodes.STREAM_CLOSED`. `InvalidBodyLengthError` must expose `expected_length` and `actual_length`.

Malformed inbound frames, invalid header blocks, impossible state transitions, invalid stream ID parity, invalid stream reuse, unsupported frame contexts, invalid flow-control increments, and content-length mismatches must raise the documented exception class that matches the condition. Exact exception message text is not part of the public contract.

## Cross-View Invariants

1. Bytes buffered by one connection through `initiate_connection()`, `send_headers()`, `send_data()`, `update_settings()`, `ping()`, `reset_stream()`, `close_connection()`, `increment_flow_control_window()`, `push_stream()`, `prioritize()`, or `advertise_alternative_service()` must be consumable by another compatible `H2Connection.receive_data()` call as public events or valid state updates.
2. Events returned by `receive_data()` must expose stream IDs, headers, data, settings, error codes, and flow-control deltas that agree with the action that produced the peer bytes.
3. Every automatic acknowledgement caused by inbound SETTINGS or PING bytes must appear as outbound bytes from `data_to_send()` after `receive_data()` returns.
4. Header encoding configuration must affect received event header attributes without changing stream IDs, event class selection, or flow-control accounting.
5. A stream closed by both endpoints must no longer count in `open_outbound_streams` or `open_inbound_streams`, and subsequent sends on that stream must raise a documented stream/protocol exception.
6. SETTINGS acknowledgements must move values from pending to active in `Settings`, and `SettingsAcknowledged.changed_settings` must report the same changes visible through the public settings properties.
7. Flow-control windows reported by `local_flow_control_window()` and `remote_flow_control_window()` must change consistently with DATA, WINDOW_UPDATE, and initial-window-size settings events.
8. If a received frame simultaneously ends a stream or carries priority information, the returned primary event must include the related public event attribute and the returned event list must include the related event object.
9. When an operation raises before emitting bytes, a following `data_to_send()` call must not include a partial frame for the failed user action.
10. Connection-closing errors and explicit GOAWAY actions must be visible to the peer as `ConnectionTerminated` events with the same public error code and debug data.

## Representative Workflows

### Prior-Knowledge Client Request and Server Response

```python
from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.events import DataReceived, RequestReceived, ResponseReceived, StreamEnded

client = H2Connection(H2Configuration(client_side=True, header_encoding="utf-8"))
server = H2Connection(H2Configuration(client_side=False, header_encoding="utf-8"))

client.initiate_connection()
server_events = server.receive_data(client.data_to_send())
client.receive_data(server.data_to_send())

stream_id = client.get_next_available_stream_id()
client.send_headers(
    stream_id,
    [
        (":method", "GET"),
        (":scheme", "https"),
        (":authority", "example.com"),
        (":path", "/"),
    ],
    end_stream=True,
)

server_events = server.receive_data(client.data_to_send())
request = next(event for event in server_events if isinstance(event, RequestReceived))
assert request.stream_id == stream_id
assert request.stream_ended is not None

server.send_headers(stream_id, [(":status", "200"), ("content-length", "2")])
server.send_data(stream_id, b"ok", end_stream=True)

client_events = client.receive_data(server.data_to_send())
assert any(isinstance(event, ResponseReceived) for event in client_events)
assert any(isinstance(event, DataReceived) and event.data == b"ok" for event in client_events)
assert any(isinstance(event, StreamEnded) for event in client_events)
```

### Settings Update and Acknowledgement

```python
from h2.connection import H2Connection
from h2.settings import SettingCodes
from h2.events import RemoteSettingsChanged, SettingsAcknowledged

a = H2Connection()
b = H2Connection()
a.initiate_connection()
b.receive_data(a.data_to_send())
a.receive_data(b.data_to_send())

a.update_settings({SettingCodes.MAX_CONCURRENT_STREAMS: 7})
events = b.receive_data(a.data_to_send())
assert any(isinstance(event, RemoteSettingsChanged) for event in events)

ack_events = a.receive_data(b.data_to_send())
ack = next(event for event in ack_events if isinstance(event, SettingsAcknowledged))
assert ack.changed_settings[SettingCodes.MAX_CONCURRENT_STREAMS].new_value == 7
```

## Non-Goals

- No socket, TLS, ALPN, HTTP/1.1, request routing, coroutine, or thread-safety implementation is required.
- No CLI or `python -m h2` entry point is required.
- No exact `repr()` string, exception message wording, private attribute, internal state-machine class, or private frame-buffer shape is part of the public contract.
- No exact serialized SETTINGS frame entry order, SETTINGS frame byte length, or h2c `HTTP2-Settings` header literal is part of the public contract.
- No public contract is provided for undocumented modules or internal helpers.
- No scheduling policy is required for server priority trees; h2 exposes priority information but does not enforce response scheduling.

## Invocation Protocol

There is no console script. `python -m h2` is not supported. Importing the package and using the documented Python API is the invocation protocol.

| Invocation | Expected result |
|------------|-----------------|
| `import h2` | succeeds and exposes `__version__` |
| `python -m h2` | not supported |

## Implementation Guidance

The test suite exercises public Python behavior only. It checks that independent `H2Connection` objects interoperate through bytes returned by `data_to_send()`, that inbound bytes produce documented event classes and attributes, that settings and flow-control projections agree with events, and that documented exception classes are raised for invalid public operations. Tests avoid exact `repr()` text, private attributes, private modules, and exact exception message wording.
