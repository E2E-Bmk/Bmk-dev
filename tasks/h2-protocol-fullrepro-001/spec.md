# h2 Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

This package is a pure-Python HTTP/2 protocol stack. It models a single HTTP/2 connection in memory, transforms caller actions into outbound HTTP/2 wire bytes, and transforms inbound HTTP/2 wire bytes into event objects. Socket I/O, TLS negotiation, scheduling, concurrency control, and application routing are not covered.

The central object is `h2.connection.H2Connection`. A caller creates one connection object for each peer connection, calls methods such as `initiate_connection()`, `send_headers()`, `send_data()`, and `update_settings()`, sends the bytes returned by `data_to_send()`, and passes received bytes to `receive_data()` to obtain public event objects.

## Non-Goals

- This specification does not require Socket, TLS, ALPN, HTTP/1.1, request routing, coroutine, or thread-safety layers.
- This specification does not require A CLI or `python -m h2` entry point.
- This specification does not require Exact `repr()` strings, exception message wording, private attributes, internal state-machine classes, or private frame-buffer shapes.
- This specification does not require Exact serialized SETTINGS frame entry order, SETTINGS frame byte length, or h2c `HTTP2-Settings` header literals.
- This specification does not require Undocumented modules or internal helpers.
- This specification does not require Server priority scheduling policy; the stack exposes priority information but does not enforce response scheduling.

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

## Connection Lifecycle and Byte Buffering

A connection progresses through initialization, active exchange, and optional upgrade or termination phases, with all outbound bytes flowing through an internal buffer.

**Initialization.** `initiate_connection()` must prepare the initial SETTINGS data for both clients and servers. For client-side connections it must also prepare the HTTP/2 client connection preface (the magic string `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n` followed by a SETTINGS frame). It must not return bytes directly; callers retrieve prepared bytes with `data_to_send()`.

**Byte buffer.** Calling `data_to_send()` with no amount must return all currently buffered outbound bytes and empty the buffer. Calling it with an integer amount must return at most that many bytes and retain any remaining bytes for later calls. Calling it when no bytes are buffered must return `b""`. `clear_outbound_data_buffer()` must discard buffered bytes so that the next `data_to_send()` call returns `b""`.

**Upgrade.** `initiate_upgrade_connection()` must prepare the h2c upgrade state. On a client connection it must return the bytes value to place in the `HTTP2-Settings` header and must buffer the post-upgrade connection bytes. On a server connection it must accept the client settings header bytes, apply those remote settings, set up stream 1 in the appropriate half-closed state, buffer server preface data, and return `None`. A server call without a settings header must still initialize upgrade state, and malformed header bytes must raise a protocol or decoding exception rather than silently accepting invalid input. The exact serialized SETTINGS frame entry order, byte length, and h2c header byte literal are not part of this API contract; callers must treat these values as opaque HTTP/2 protocol bytes and validate them by sending them to a compatible peer.

**Receiving data.** `receive_data` must accept bytes-like input, process complete HTTP/2 frames, return a list of public event objects, and buffer any automatic protocol response bytes. If data is incomplete, it must retain it until enough bytes arrive to complete a frame. Protocol violations must raise a documented `H2Error` subclass and must buffer connection-closing bytes when the connection is terminated as a result.

## Headers, Data, and Events

Header and data transmission produces outbound wire bytes, while inbound wire bytes are decoded into typed event objects describing each protocol interaction.

**Sending headers.** `send_headers()` must send request headers when called on a client-initiated stream, response headers when called on a server for an inbound stream, informational response headers for `:status` values in the 100 range, and trailers when called after the main header block on an open stream. Client streams must use odd stream IDs and server-pushed streams must use even stream IDs. Server connections must raise `ProtocolError` when asked to open a new stream by sending response headers on an unused stream. When priority information is provided through `priority_weight`, `priority_depends_on`, and `priority_exclusive`, the resulting `RequestReceived` event must include a related `PriorityUpdated` event exposing those values.

**Header encoding.** Header collections must preserve order. Header names and values accepted as text must be encoded for the wire. Received headers must be returned as bytes unless `H2Configuration.header_encoding` is a string, in which case names and values must be decoded with that encoding. If outbound validation is enabled, malformed pseudo-header order, invalid pseudo-header use, uppercase header names, forbidden connection-specific headers, invalid TE values, duplicate pseudo-headers, or missing required request or response pseudo-headers must raise `ProtocolError`.

**Sending data.** `send_data()` must buffer DATA bytes for an existing stream. The `data` argument must be bytes-like, including `memoryview`. When `end_stream` is true, the DATA frame must close the local side of the stream and a compatible peer must receive a `DataReceived` event with a related `StreamEnded` event. Sending data larger than the available stream flow-control window, connection flow-control window, or maximum outbound frame size must raise `FlowControlError` or `FrameTooLargeError` and must not emit the oversized DATA bytes. When `pad_length` is provided, padding bytes must be included and must count toward `flow_controlled_length`.

**Ending streams.** `end_stream` must end the local side of a stream without application data. A compatible peer must receive a `StreamEnded` event. Ending or sending on a nonexistent or already closed stream must raise `NoSuchStreamError`, `StreamClosedError`, or `ProtocolError`.

`receive_data()` must translate inbound HEADERS, DATA, SETTINGS, PING, WINDOW_UPDATE, RST_STREAM, GOAWAY, PUSH_PROMISE, PRIORITY, ALTSVC, and unknown extension frames into the matching public events listed in this specification. If one inbound frame causes multiple public events, the primary event's related-event attributes must point to the simultaneous related event and the related event must also appear in the returned event list.

## Stream Lifecycle

Stream lifecycle management controls how streams are created, tracked, and closed across both endpoints.

**Stream ID allocation.** `get_next_available_stream_id()` must return the next stream ID this endpoint is allowed to initiate: odd IDs for clients and even IDs for servers. The returned value must not advance until a stream is actually opened by sending or pushing headers. If all stream IDs are exhausted, it must raise `NoAvailableStreamIDError`.

**Stream counts.** `open_outbound_streams` and `open_inbound_streams` must return counts of currently open streams in the matching direction. Closing streams by ending both sides, resetting, or receiving a terminal close event must reduce those counts after the stream leaves the open state.

**Server push.** `push_stream()` must be available to server-side connections for a stream that permits server push. It must buffer a PUSH_PROMISE for `promised_stream_id` with `request_headers`, and a compatible client peer must receive `PushedStreamReceived` carrying the pushed stream ID, parent stream ID, and headers. It must raise `ProtocolError` when used on a client connection, when push is disabled by peer settings, when the parent stream does not permit push, or when the promised stream ID is invalid.

**Stream reset.** `reset_stream()` must buffer an RST_STREAM for an existing stream and close local state for that stream. A compatible peer must receive `StreamReset` with the stream ID, error code, and `remote_reset=True`. Resetting a nonexistent or closed stream must raise a documented stream/protocol exception.

**Connection close.** `close_connection()` must buffer a GOAWAY frame. A compatible peer must receive `ConnectionTerminated` containing the error code, last stream ID, and additional data. After a connection is closed, attempts to create new streams or send further protocol actions must raise `ProtocolError`.

## Settings Behavior

Settings control connection-level parameters negotiated between peers through SETTINGS frames and their acknowledgements.

**Defaults.** `Settings` defaults must match HTTP/2 defaults: `header_table_size` is `4096`, `initial_window_size` is `65535`, `max_frame_size` is `16384`, `enable_connect_protocol` is `0`, and `enable_push` is `1` for client-owned settings and `0` for server-owned settings. `max_concurrent_streams` must return `2**32 + 1` when unset. `max_header_list_size` must return `None` when unset. When `initial_values` is provided, it must override the matching active defaults when valid.

**Connection defaults.** `H2Connection` must initialize its local advertised settings from those defaults with `MAX_CONCURRENT_STREAMS` set to `100` and `MAX_HEADER_LIST_SIZE` set to `65536`. When a connection sends its initial SETTINGS, a compatible peer must treat those advertised values as that peer's active remote settings after processing the bytes. When that peer later receives an update for the same setting, `RemoteSettingsChanged.changed_settings[setting].original_value` must report the previous active remote value and `new_value` must report the value from the received update.

**Pending and acknowledgement.** Assigning a setting through mapping syntax or a property must stage a new value until `acknowledge()` applies it. `acknowledge()` must return only settings whose active value changed, and each returned `ChangedSetting` must report the previous active value and the newly active value. When `acknowledge()` is called with no pending changes, it must return an empty dictionary. Unknown integer settings must be stored and acknowledged like known settings unless their value is invalid under known validation rules. Settings must support both mapping-style access by `SettingCodes` and by raw integer code.

**Update protocol.** `update_settings` must stage local settings, buffer a SETTINGS frame, and leave the new local values pending until the peer acknowledges them. Receiving a non-ACK SETTINGS frame must return `RemoteSettingsChanged` and must buffer a SETTINGS acknowledgement automatically. Receiving a SETTINGS acknowledgement must return `SettingsAcknowledged` containing the local settings that became active. Receiving an invalid setting value must raise `InvalidSettingsValueError`.

## Flow Control

Flow control regulates the rate of data transmission between peers through per-stream and connection-level windows.

**Window queries.** `local_flow_control_window(stream_id)` must return the maximum number of data bytes the local endpoint is currently allowed to send on the stream, constrained by both the stream and connection outbound windows. Sending data must reduce this window by the exact number of bytes sent, and this reduction must also affect subsequent streams opened on the same connection. `remote_flow_control_window(stream_id)` must return the maximum number of flow-controlled bytes the remote peer is currently allowed to send on the stream, constrained by both the stream and connection inbound windows. When a stream has fully closed but the connection still retains that stream's state, `local_flow_control_window(stream_id)` must return the remaining outbound flow-control window for that retained stream. When no stream state exists for the stream ID, or the stream state has been purged, flow-control queries must raise the documented stream exception.

**Data acknowledgement.** Inbound `DataReceived.flow_controlled_length` must include bytes that count against HTTP/2 flow control, including padding. `acknowledge_received_data` must mark received bytes as processed and buffer WINDOW_UPDATE frames when the connection or stream window should be reopened. When acknowledgement restores the full window, both connection-level (stream ID `0`) and stream-level `WindowUpdated` events must be emitted to the peer with the acknowledged delta. It must raise `ValueError` when `stream_id` is zero or negative, or when the acknowledged size is negative.

**Window increment.** `increment_flow_control_window` must buffer a connection-level WINDOW_UPDATE when `stream_id` is omitted, and a stream-level WINDOW_UPDATE when a stream ID is provided. The peer must receive a `WindowUpdated` event with the corresponding stream ID and delta. Invalid increments or invalid stream IDs must raise a documented exception.

Receiving WINDOW_UPDATE frames must return `WindowUpdated` events. A stream-level update must identify that stream; a connection-level update must use stream ID `0`. Receiving changes to `SETTINGS_INITIAL_WINDOW_SIZE` must update existing stream flow-control windows consistently with the new setting.

## Ping, Priority, and Alternative Services

Ping, priority, and alternative service operations provide connection health checks, stream scheduling hints, and service discovery.

**Ping.** `ping` must require its `opaque_data` argument to be a `bytes` object of length exactly eight. It must buffer a PING frame, and a compatible peer must return `PingReceived` and buffer a matching acknowledgement. Receiving that acknowledgement must return `PingAckReceived` with the same opaque bytes. Text strings are invalid and must raise `ValueError`, even when they contain eight characters. Bytes objects with any length other than eight and non-`bytes` values such as `bytearray` or `memoryview` must raise `ValueError`.

**Priority.** `prioritize()` must be available on client-side connections and must buffer priority information for the given stream. A compatible server peer must receive `PriorityUpdated` with stream ID, weight, dependency, and exclusivity values. Server-side calls to `prioritize()` must raise `RFC1122Error`. Invalid priority values must raise a documented error.

**Alternative services.** `advertise_alternative_service()` must buffer an ALTSVC advertisement. Exactly one of `origin` or `stream_id` must identify the advertised origin. The `field_value` argument must be bytes; non-bytes values must raise `ValueError`. Supplying both `origin` and `stream_id` must raise `ValueError`. A compatible client peer must receive `AlternativeServiceAvailable` with the `origin` and `field_value` attributes matching the advertised values.

## State Model

A connection has three public projections of the same protocol state:

- The outbound byte projection returned and drained by `data_to_send()`.
- The inbound event projection returned by `receive_data()`.
- The public connection/settings/window projection exposed by documented methods, properties, `Settings`, `ChangedSetting`, and event attributes.

These projections must agree. When a caller performs an outbound action, the action must produce bytes retrievable by `data_to_send()` or must raise a documented exception. When those bytes are supplied to a compatible peer connection, that peer must return the corresponding public events and update its public settings or flow-control projections. When a connection receives peer bytes that require automatic protocol acknowledgments, `receive_data()` must return the triggering events and must buffer any automatic response bytes for `data_to_send()`.

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

## Public Interface

### Import Surface

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

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `H2Configuration` | class | Connection-side and header-encoding configuration |
| `H2Connection` | class | HTTP/2 connection state machine and wire-byte buffer |
| `ErrorCodes` | enum | HTTP/2 error code constants |
| `SettingCodes` | enum | HTTP/2 setting identifier constants |
| `ChangedSetting` | class | One setting transition from old to new value |
| `Settings` | class | Mutable mapping of active and pending connection settings |
| `Event` | class | Base class for inbound protocol events |
| `RequestReceived` | class | Inbound request headers on a stream |
| `ResponseReceived` | class | Inbound response headers on a stream |
| `TrailersReceived` | class | Inbound trailer headers on a stream |
| `InformationalResponseReceived` | class | Inbound informational response headers |
| `DataReceived` | class | Inbound DATA payload on a stream |
| `WindowUpdated` | class | Inbound WINDOW_UPDATE delta |
| `RemoteSettingsChanged` | class | Peer SETTINGS update with changed values |
| `PingReceived` | class | Inbound PING frame |
| `PingAckReceived` | class | Inbound PING acknowledgement |
| `StreamEnded` | class | Stream half-closed or fully closed event |
| `StreamReset` | class | Stream reset with error code |
| `PushedStreamReceived` | class | Server push promise with headers |
| `SettingsAcknowledged` | class | Local settings acknowledged by peer |
| `PriorityUpdated` | class | Stream priority update |
| `ConnectionTerminated` | class | Connection GOAWAY termination |
| `AlternativeServiceAvailable` | class | ALTSVC advertisement from peer |
| `UnknownFrameReceived` | class | Unrecognized extension frame |
| `H2Error` | exception | Base class for h2-specific errors |
| `ProtocolError` | exception | Protocol rule violation |
| `FlowControlError` | exception | Flow-control window violation |
| `FrameTooLargeError` | exception | Frame exceeds maximum size |
| `FrameDataMissingError` | exception | Incomplete frame data |
| `DenialOfServiceError` | exception | Connection closed under load policy |
| `InvalidSettingsValueError` | exception | Invalid SETTINGS value |
| `NoAvailableStreamIDError` | exception | No stream IDs remain |
| `NoSuchStreamError` | exception | Unknown stream identifier |
| `StreamClosedError` | exception | Operation on closed stream |
| `StreamIDTooLowError` | exception | Stream ID below allowed minimum |
| `TooManyStreamsError` | exception | Concurrent stream limit exceeded |
| `UnsupportedFrameError` | exception | Frame type unsupported in context |
| `RFC1122Error` | exception | Priority use forbidden on server side |

`H2Configuration` controls client versus server behavior, header encoding, outbound and inbound header validation and normalization, cookie splitting, and optional logging. Boolean configuration fields must raise `ValueError` when assigned a non-boolean value. `header_encoding` must accept `None`, `False`, or a string encoding name, must return headers as bytes when set to `None` or `False`, must decode received header names and values when set to a string encoding, and must raise `ValueError` when set to `True` or to any other unsupported type.

`H2Connection` exposes open-stream counts, connection initiation, h2c upgrade setup, stream ID allocation, header and data transmission, stream closure, flow-control window queries and updates, server push, ping, reset, connection close, settings updates, alternative-service advertisement, priority updates, outbound byte retrieval, buffer clearing, and inbound event processing. When constructed without an explicit configuration object, it must behave as a client-side connection with default configuration.

`ChangedSetting` exposes the setting identifier, previous active value, and newly active value. `Settings` behaves as a mutable mapping from setting codes to integer values and exposes property accessors for each known setting. `Settings.acknowledge()` applies pending values and returns a dictionary of `ChangedSetting` objects for settings whose active value changed. Invalid settings values must raise `InvalidSettingsValueError` with an HTTP/2 error code appropriate to the invalid setting.

All event classes inherit from `Event` and expose the documented public attributes listed in the behavior sections; callers must not rely on exact `repr()` text.

### CLI Entry Points

There is no console script. `python -m h2` is not supported. Importing the package and using the documented Python API is the invocation protocol.

| Invocation | Expected result |
|------------|-----------------|
| `import h2` | succeeds and exposes `__version__` |
| `python -m h2` | not supported |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Independent `H2Connection` objects must interoperate through bytes returned by `data_to_send()`. Inbound bytes must produce the documented event classes and attributes, settings and flow-control projections must agree with events, and invalid public operations must raise the documented exception classes. Exact `repr()` text, private attributes, private modules, and exact exception wording are outside this contract.
