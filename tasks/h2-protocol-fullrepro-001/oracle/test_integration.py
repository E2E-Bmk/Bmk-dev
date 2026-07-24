"""Integration tests for h2-protocol-fullrepro-001.

Each test exercises ≥2 public API boundaries working together.
All tests follow the Cross-View Invariants: bytes buffered by one connection
must be consumable by another compatible connection as public events.
"""
from __future__ import annotations

import pytest

from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.errors import ErrorCodes
from h2.events import (
    AlternativeServiceAvailable,
    ConnectionTerminated,
    DataReceived,
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
    WindowUpdated,
)
from h2.exceptions import (
    FlowControlError,
    FrameTooLargeError,
    InvalidSettingsValueError,
    ProtocolError,
)
from h2.settings import SettingCodes
from conftest import (
    REQ_HEADERS,
    RESP_HEADERS,
    POST_HEADERS,
    make_pair,
    open_stream,
    event_of,
    events_of,
)


# =============================================================================
# CVI-1: Bytes from one connection consumable by peer as events
# Seam: protocol handoff — outbound bytes → peer inbound events
# =============================================================================


@pytest.mark.depends_on("test_initiate_connection_buffers_client_preface")
def test_client_preface_accepted_by_server_as_settings_event():
    """Seam: protocol handoff — client preface accepted as RemoteSettingsChanged."""
    client = H2Connection(H2Configuration(client_side=True))
    client.initiate_connection()
    server = H2Connection(H2Configuration(client_side=False))
    events = server.receive_data(client.data_to_send())
    assert any(isinstance(e, RemoteSettingsChanged) for e in events)


@pytest.mark.depends_on("test_server_initiation_does_not_include_client_preface")
def test_server_preface_accepted_by_client_as_settings_event():
    """Seam: protocol handoff — server preface accepted as RemoteSettingsChanged."""
    server = H2Connection(H2Configuration(client_side=False))
    server.initiate_connection()
    client = H2Connection(H2Configuration(client_side=True))
    events = client.receive_data(server.data_to_send())
    assert any(isinstance(e, RemoteSettingsChanged) for e in events)


def test_request_headers_reach_server_as_request_received():
    """Seam: protocol handoff — request headers reach peer as RequestReceived."""
    client, server = make_pair()
    sid, events = open_stream(client, server, end_stream=True)
    req = event_of(events, RequestReceived)
    assert req.stream_id == sid
    assert req.headers == REQ_HEADERS


def test_response_headers_reach_client_as_response_received():
    """Seam: protocol handoff — response headers reach peer as ResponseReceived."""
    client, server = make_pair()
    sid, _ = open_stream(client, server, end_stream=True)
    server.send_headers(sid, RESP_HEADERS)
    events = client.receive_data(server.data_to_send())
    resp = event_of(events, ResponseReceived)
    assert resp.stream_id == sid
    assert resp.headers == RESP_HEADERS


def test_data_reaches_peer_as_data_received_event():
    """Seam: protocol handoff — DATA frames reach peer as DataReceived."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    client.send_data(sid, b"payload")
    events = server.receive_data(client.data_to_send())
    data_ev = event_of(events, DataReceived)
    assert data_ev.stream_id == sid
    assert data_ev.data == b"payload"
    assert data_ev.flow_controlled_length == 7


# =============================================================================
# CVI-2: Event attributes agree with producing action
# =============================================================================


def test_informational_response_event_carries_correct_status():
    """CVI-2: informational response event attributes match sent headers."""
    client, server = make_pair()
    sid, _ = open_stream(client, server, end_stream=True)
    server.send_headers(sid, [(":status", "103"), ("link", "</app.css>")])
    events = client.receive_data(server.data_to_send())
    info = event_of(events, InformationalResponseReceived)
    assert info.stream_id == sid
    assert info.headers == [(":status", "103"), ("link", "</app.css>")]


def test_trailers_event_carries_correct_headers():
    """CVI-2: trailers event headers match sent trailer block."""
    client, server = make_pair()
    sid, _ = open_stream(client, server, end_stream=True)
    server.send_headers(sid, RESP_HEADERS)
    server.send_data(sid, b"body")
    client.receive_data(server.data_to_send())
    server.send_headers(sid, [("x-checksum", "abc123")], end_stream=True)
    events = client.receive_data(server.data_to_send())
    trailers = event_of(events, TrailersReceived)
    assert trailers.headers == [("x-checksum", "abc123")]


# =============================================================================
# CVI-3: Automatic acknowledgements appear as outbound bytes
# =============================================================================


def test_settings_auto_ack_is_buffered_after_receive_data():
    """CVI-3: settings auto-ack buffered as outbound bytes after receive_data."""
    client, server = make_pair()
    client.update_settings({SettingCodes.MAX_CONCURRENT_STREAMS: 9})
    server.receive_data(client.data_to_send())
    ack_bytes = server.data_to_send()
    assert len(ack_bytes) > 0
    events = client.receive_data(ack_bytes)
    assert any(isinstance(e, SettingsAcknowledged) for e in events)


def test_ping_auto_ack_is_buffered_after_receive_data():
    """CVI-3: ping auto-ack buffered as outbound bytes after receive_data."""
    client, server = make_pair()
    client.ping(b"12345678")
    server.receive_data(client.data_to_send())
    ack_bytes = server.data_to_send()
    assert len(ack_bytes) > 0
    events = client.receive_data(ack_bytes)
    ack = event_of(events, PingAckReceived)
    assert ack.ping_data == b"12345678"


# =============================================================================
# CVI-4: Header encoding affects attributes without changing stream/flow
# =============================================================================


def test_bytes_encoding_returns_bytes_headers():
    """CVI-4: bytes header encoding returns bytes header tuples."""
    client, server = make_pair(client_encoding=None, server_encoding=None)
    _, events = open_stream(client, server, end_stream=True)
    req = event_of(events, RequestReceived)
    assert req.headers[0] == (b":method", b"GET")


def test_utf8_encoding_returns_str_headers():
    """CVI-4: UTF-8 header encoding returns str header tuples."""
    client, server = make_pair()
    _, events = open_stream(client, server, end_stream=True)
    req = event_of(events, RequestReceived)
    assert req.headers[0] == (":method", "GET")


# =============================================================================
# CVI-5: Closed stream counts and subsequent send errors
# =============================================================================


@pytest.mark.depends_on("test_next_stream_id_stable_until_stream_opened")
def test_stream_counts_follow_full_lifecycle():
    """CVI-5: open stream counts follow full open-to-close lifecycle."""
    client, server = make_pair()
    sid, _ = open_stream(client, server, end_stream=False)
    assert client.open_outbound_streams == 1
    assert server.open_inbound_streams == 1
    server.send_headers(sid, RESP_HEADERS)
    server.send_data(sid, b"ok", end_stream=True)
    client.receive_data(server.data_to_send())
    client.end_stream(sid)
    server.receive_data(client.data_to_send())
    assert client.open_outbound_streams == 0
    assert server.open_inbound_streams == 0


def test_sending_on_closed_stream_raises():
    """CVI-5: sending on closed stream raises ProtocolError."""
    client, server = make_pair()
    open_stream(client, server, end_stream=True)
    with pytest.raises(ProtocolError):
        client.send_headers(1, REQ_HEADERS)


# =============================================================================
# CVI-6: Settings acknowledgement moves pending to active
# =============================================================================


@pytest.mark.depends_on("test_settings_assignment_pending_until_acknowledged")
def test_update_settings_pending_until_peer_ack():
    """CVI-6: updated settings pending until peer acknowledgement."""
    client, server = make_pair()
    client.update_settings({SettingCodes.MAX_CONCURRENT_STREAMS: 11})
    assert client.local_settings.max_concurrent_streams == 100
    server.receive_data(client.data_to_send())
    events = client.receive_data(server.data_to_send())
    ack = event_of(events, SettingsAcknowledged)
    assert ack.changed_settings[SettingCodes.MAX_CONCURRENT_STREAMS].new_value == 11
    assert client.local_settings.max_concurrent_streams == 11


def test_remote_settings_changed_reports_original_and_new():
    """CVI-6: RemoteSettingsChanged reports original and new values."""
    client, server = make_pair()
    client.update_settings({SettingCodes.MAX_CONCURRENT_STREAMS: 13})
    events = server.receive_data(client.data_to_send())
    change = event_of(events, RemoteSettingsChanged)
    cs = change.changed_settings[SettingCodes.MAX_CONCURRENT_STREAMS]
    assert cs.original_value == 100
    assert cs.new_value == 13


def test_peer_advertised_settings_applied_after_handshake():
    """CVI-6: peer-advertised settings applied after handshake."""
    client, server = make_pair()
    assert server.remote_settings.max_concurrent_streams == 100
    assert server.remote_settings.max_header_list_size == 65536
    assert client.remote_settings.enable_push == 0


# =============================================================================
# CVI-7: Flow-control windows consistent with DATA and WINDOW_UPDATE
# =============================================================================


@pytest.mark.depends_on("test_send_data_reduces_local_flow_window")
def test_send_data_reduces_both_sender_and_connection_windows():
    """CVI-7: send_data reduces sender and connection flow windows."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    client.send_data(sid, b"x" * 1000)
    assert client.local_flow_control_window(sid) == 64535
    sid2 = client.get_next_available_stream_id()
    client.send_headers(sid2, REQ_HEADERS)
    assert client.local_flow_control_window(sid2) == 64535


def test_remote_flow_window_decreases_on_data_receipt():
    """CVI-7: remote flow window decreases on data receipt."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    assert server.remote_flow_control_window(sid) == 65535
    client.send_data(sid, b"x" * 2000)
    server.receive_data(client.data_to_send())
    assert server.remote_flow_control_window(sid) == 63535


def test_acknowledge_received_data_restores_windows():
    """CVI-7: acknowledge_received_data restores flow windows."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    client.send_data(sid, b"x" * 16000)
    server.receive_data(client.data_to_send())
    server.acknowledge_received_data(16000, sid)
    events = client.receive_data(server.data_to_send())
    deltas = {(e.stream_id, e.delta) for e in events if isinstance(e, WindowUpdated)}
    assert (0, 16000) in deltas
    assert (sid, 16000) in deltas
    assert client.local_flow_control_window(sid) == 65535


def test_increment_flow_control_window_emits_window_updated():
    """CVI-7: increment_flow_control_window emits WindowUpdated."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    server.increment_flow_control_window(256, sid)
    events = client.receive_data(server.data_to_send())
    wu = event_of(events, WindowUpdated)
    assert wu.stream_id == sid
    assert wu.delta == 256


def test_connection_level_window_update_uses_stream_zero():
    """CVI-7: connection-level window update uses stream zero."""
    client, server = make_pair()
    server.increment_flow_control_window(512)
    events = client.receive_data(server.data_to_send())
    wu = event_of(events, WindowUpdated)
    assert wu.stream_id == 0
    assert wu.delta == 512


def test_send_data_exceeding_flow_window_raises():
    """CVI-7: send_data exceeding flow window raises FlowControlError."""
    client, server = make_pair()
    server.update_settings({SettingCodes.INITIAL_WINDOW_SIZE: 10})
    client.receive_data(server.data_to_send())
    server.receive_data(client.data_to_send())
    sid, _ = open_stream(client, server)
    with pytest.raises(FlowControlError):
        client.send_data(sid, b"x" * 11)


def test_padding_counted_in_flow_controlled_length():
    """CVI-7: padding counted in flow_controlled_length."""
    client, server = make_pair()
    sid, _ = open_stream(client, server, end_stream=True)
    server.send_headers(sid, RESP_HEADERS)
    server.send_data(sid, b"hi", pad_length=4)
    events = client.receive_data(server.data_to_send())
    data_ev = event_of(events, DataReceived)
    assert data_ev.data == b"hi"
    assert data_ev.flow_controlled_length == 7


# =============================================================================
# CVI-8: Related events linked and present in list
# =============================================================================


def test_end_stream_data_links_stream_ended():
    """CVI-8: end-stream DATA links DataReceived to StreamEnded."""
    client, server = make_pair()
    sid, _ = open_stream(client, server, end_stream=True)
    server.send_headers(sid, RESP_HEADERS)
    server.send_data(sid, b"fin", end_stream=True)
    events = client.receive_data(server.data_to_send())
    data_ev = event_of(events, DataReceived)
    ended = event_of(events, StreamEnded)
    assert data_ev.stream_ended is ended
    assert ended.stream_id == sid


def test_request_with_priority_links_priority_updated():
    """CVI-8: request with priority links RequestReceived to PriorityUpdated."""
    client, server = make_pair()
    _, events = open_stream(
        client, server, end_stream=True,
        priority_weight=64, priority_depends_on=0, priority_exclusive=False,
    )
    req = event_of(events, RequestReceived)
    pri = event_of(events, PriorityUpdated)
    assert req.priority_updated is pri
    assert pri.weight == 64
    assert pri.depends_on == 0
    assert pri.exclusive is False


def test_request_end_stream_links_stream_ended():
    """CVI-8: request end_stream links RequestReceived to StreamEnded."""
    client, server = make_pair()
    _, events = open_stream(client, server, end_stream=True)
    req = event_of(events, RequestReceived)
    assert req.stream_ended is not None
    assert req.stream_ended.stream_id == req.stream_id


# =============================================================================
# CVI-9: Failed operation does not emit partial frame
# =============================================================================


def test_failed_send_data_does_not_leak_bytes():
    """CVI-9: failed send_data does not leak partial frame bytes."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    _ = client.data_to_send()
    with pytest.raises(FrameTooLargeError):
        client.send_data(sid, b"x" * 20000)
    assert client.data_to_send() == b""


# =============================================================================
# CVI-10: GOAWAY visible to peer as ConnectionTerminated
# =============================================================================


def test_close_connection_peer_sees_connection_terminated():
    """CVI-10: GOAWAY visible to peer as ConnectionTerminated."""
    client, server = make_pair()
    client.close_connection(ErrorCodes.NO_ERROR, additional_data=b"done", last_stream_id=0)
    events = server.receive_data(client.data_to_send())
    term = event_of(events, ConnectionTerminated)
    assert term.error_code == ErrorCodes.NO_ERROR
    assert term.last_stream_id == 0
    assert term.additional_data == b"done"


# =============================================================================
# Ping round-trip (client ping → server PingReceived → auto ack → client PingAckReceived)
# =============================================================================


def test_ping_round_trip():
    """Seam: protocol handoff — ping round-trip through PingReceived and PingAckReceived."""
    client, server = make_pair()
    client.ping(b"ABCDEFGH")
    svr_events = server.receive_data(client.data_to_send())
    ping_ev = event_of(svr_events, PingReceived)
    assert ping_ev.ping_data == b"ABCDEFGH"
    cli_events = client.receive_data(server.data_to_send())
    ack_ev = event_of(cli_events, PingAckReceived)
    assert ack_ev.ping_data == b"ABCDEFGH"


# =============================================================================
# Reset stream visible to peer
# =============================================================================


def test_reset_stream_peer_sees_stream_reset():
    """Seam: protocol handoff — reset_stream visible as StreamReset."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    client.reset_stream(sid, ErrorCodes.CANCEL)
    events = server.receive_data(client.data_to_send())
    rst = event_of(events, StreamReset)
    assert rst.stream_id == sid
    assert rst.error_code == ErrorCodes.CANCEL
    assert rst.remote_reset is True


# =============================================================================
# Server push
# =============================================================================


def test_push_stream_peer_sees_pushed_stream_received():
    """Seam: protocol handoff — push_stream visible as PushedStreamReceived."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    server.push_stream(sid, 2, REQ_HEADERS)
    events = client.receive_data(server.data_to_send())
    pushed = event_of(events, PushedStreamReceived)
    assert pushed.parent_stream_id == sid
    assert pushed.pushed_stream_id == 2
    assert pushed.headers == REQ_HEADERS


# =============================================================================
# Alternative service
# =============================================================================


def test_altsvc_reaches_client():
    """Seam: protocol handoff — ALTSVC frame reaches client event."""
    client, server = make_pair()
    server.advertise_alternative_service(b'h2=":8443"', origin=b"https://node.example")
    events = client.receive_data(server.data_to_send())
    alt = event_of(events, AlternativeServiceAvailable)
    assert alt.origin == b"https://node.example"
    assert alt.field_value == b'h2=":8443"'


# =============================================================================
# Priority
# =============================================================================


def test_prioritize_reaches_server():
    """Seam: protocol handoff — prioritize frame reaches server event."""
    client, server = make_pair()
    client.prioritize(5, weight=128, depends_on=0, exclusive=True)
    events = server.receive_data(client.data_to_send())
    pri = event_of(events, PriorityUpdated)
    assert pri.stream_id == 5
    assert pri.weight == 128
    assert pri.depends_on == 0
    assert pri.exclusive is True


# =============================================================================
# Upgrade protocol
# =============================================================================


def test_client_upgrade_returns_settings_header_and_buffers_preface():
    """Seam: protocol handoff — client upgrade returns settings and buffers preface."""
    client = H2Connection(H2Configuration(client_side=True))
    header = client.initiate_upgrade_connection()
    assert isinstance(header, bytes) and len(header) > 0
    assert client.data_to_send().startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")


def test_server_upgrade_accepts_client_header_returns_none():
    """Seam: protocol handoff — server upgrade accepts client header."""
    client = H2Connection(H2Configuration(client_side=True))
    header = client.initiate_upgrade_connection()
    server = H2Connection(H2Configuration(client_side=False))
    assert server.initiate_upgrade_connection(header) is None
    assert server.data_to_send()


# =============================================================================
# Incomplete frame buffering
# =============================================================================


def test_receive_data_buffers_incomplete_frames():
    """Seam: lifecycle crossing — receive_data buffers incomplete frames."""
    client, server = make_pair()
    client.send_headers(1, REQ_HEADERS, end_stream=True)
    data = client.data_to_send()
    assert server.receive_data(data[:5]) == []
    events = server.receive_data(data[5:])
    req = event_of(events, RequestReceived)
    assert req.stream_id == 1


# =============================================================================
# memoryview data
# =============================================================================


def test_memoryview_data_transmitted_to_peer():
    """Seam: state consistency — memoryview payload transmitted to peer."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    client.send_data(sid, memoryview(b"mem"))
    events = server.receive_data(client.data_to_send())
    assert event_of(events, DataReceived).data == b"mem"


# =============================================================================
# end_stream without data
# =============================================================================


def test_end_stream_delivers_stream_ended():
    """Seam: protocol handoff — end_stream delivers StreamEnded event."""
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    client.end_stream(sid)
    events = server.receive_data(client.data_to_send())
    ended = event_of(events, StreamEnded)
    assert ended.stream_id == sid


# =============================================================================
# Invalid settings from peer
# =============================================================================


def test_invalid_settings_value_from_peer_raises():
    """Seam: error propagation — invalid peer settings raise InvalidSettingsValueError."""
    client, server = make_pair()
    server.update_settings({SettingCodes.ENABLE_PUSH: 1})
    with pytest.raises(InvalidSettingsValueError) as exc_info:
        client.receive_data(server.data_to_send())
    assert exc_info.value.error_code == ErrorCodes.PROTOCOL_ERROR
