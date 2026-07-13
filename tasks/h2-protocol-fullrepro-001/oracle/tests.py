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
    H2Error,
    InvalidSettingsValueError,
    NoSuchStreamError,
    ProtocolError,
    RFC1122Error,
    StreamClosedError,
    StreamIDTooLowError,
)
from h2.settings import ChangedSetting, SettingCodes, Settings


REQ_HEADERS_TEXT = [
    (":method", "GET"),
    (":scheme", "https"),
    (":authority", "example.com"),
    (":path", "/resource"),
]
RESP_HEADERS_TEXT = [(":status", "200"), ("server", "unit")]


def make_pair(client_encoding: str | None = "utf-8", server_encoding: str | None = "utf-8"):
    client = H2Connection(H2Configuration(client_side=True, header_encoding=client_encoding))
    server = H2Connection(H2Configuration(client_side=False, header_encoding=server_encoding))
    client.initiate_connection()
    server.initiate_connection()
    server_events_1 = server.receive_data(client.data_to_send())
    client_events = client.receive_data(server.data_to_send())
    server_events_2 = server.receive_data(client.data_to_send())
    return client, server, server_events_1, client_events, server_events_2


def open_request(client: H2Connection, server: H2Connection, *, end_stream: bool = False, headers=None, **priority):
    stream_id = client.get_next_available_stream_id()
    client.send_headers(stream_id, headers or REQ_HEADERS_TEXT, end_stream=end_stream, **priority)
    events = server.receive_data(client.data_to_send())
    return stream_id, events


def event_of(events, event_type):
    return next(event for event in events if isinstance(event, event_type))


def drain_handshake(client: H2Connection, server: H2Connection) -> None:
    if client.data_to_send():
        server.receive_data(client.data_to_send())
    if server.data_to_send():
        client.receive_data(server.data_to_send())


def test_client_initiate_connection_buffers_preface_and_settings():
    client = H2Connection(H2Configuration(client_side=True))
    client.initiate_connection()
    data = client.data_to_send()
    assert data.startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    assert data[len(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n") :]
    server = H2Connection(H2Configuration(client_side=False))
    events = server.receive_data(data)
    assert event_of(events, RemoteSettingsChanged).changed_settings
    assert client.data_to_send() == b""


def test_server_initiate_connection_buffers_settings_without_client_preface():
    server = H2Connection(H2Configuration(client_side=False))
    server.initiate_connection()
    data = server.data_to_send()
    assert data
    assert not data.startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    client = H2Connection(H2Configuration(client_side=True))
    events = client.receive_data(data)
    assert event_of(events, RemoteSettingsChanged).changed_settings


def test_data_to_send_amount_drains_in_chunks():
    full_client = H2Connection()
    full_client.initiate_connection()
    expected = full_client.data_to_send()

    client = H2Connection()
    client.initiate_connection()
    first = client.data_to_send(5)
    second = client.data_to_send(7)
    rest = client.data_to_send()
    assert first
    assert second
    assert len(first) <= 5
    assert len(second) <= 7
    assert first + second + rest == expected
    assert client.data_to_send() == b""


def test_clear_outbound_data_buffer_discards_pending_bytes():
    client = H2Connection()
    client.initiate_connection()
    assert client.data_to_send(1) == b"P"
    client.clear_outbound_data_buffer()
    assert client.data_to_send() == b""


def test_receive_data_retains_incomplete_frame_until_remaining_bytes_arrive():
    client, server, _, _, _ = make_pair()
    stream_id = client.get_next_available_stream_id()
    client.send_headers(stream_id, REQ_HEADERS_TEXT, end_stream=True)
    data = client.data_to_send()
    assert server.receive_data(data[:5]) == []
    events = server.receive_data(data[5:])
    request = event_of(events, RequestReceived)
    assert request.stream_id == 1
    assert request.stream_ended.stream_id == 1


def test_client_upgrade_returns_header_value_and_buffers_connection_bytes():
    client = H2Connection(H2Configuration(client_side=True))
    settings_header = client.initiate_upgrade_connection()
    assert isinstance(settings_header, bytes)
    assert settings_header
    assert client.data_to_send().startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    server = H2Connection(H2Configuration(client_side=False))
    assert server.initiate_upgrade_connection(settings_header) is None
    server_bytes = server.data_to_send()
    assert server_bytes
    assert not server_bytes.startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")


def test_server_upgrade_accepts_client_header_and_returns_none():
    client = H2Connection(H2Configuration(client_side=True))
    settings_header = client.initiate_upgrade_connection()
    server = H2Connection(H2Configuration(client_side=False))
    assert server.initiate_upgrade_connection(settings_header) is None
    assert server.data_to_send()


def test_settings_defaults_for_client_and_server():
    client_settings = Settings(client=True)
    server_settings = Settings(client=False)
    assert client_settings.header_table_size == 4096
    assert client_settings.enable_push == 1
    assert server_settings.enable_push == 0
    assert client_settings.initial_window_size == 65535
    assert client_settings.max_frame_size == 16384
    assert client_settings.max_concurrent_streams == 2**32 + 1
    assert client_settings.max_header_list_size is None


def test_settings_initial_values_override_active_defaults():
    settings = Settings(initial_values={SettingCodes.MAX_CONCURRENT_STREAMS: 3})
    assert settings.max_concurrent_streams == 3


def test_settings_assignment_is_pending_until_acknowledged():
    settings = Settings()
    settings[SettingCodes.MAX_FRAME_SIZE] = 20000
    assert settings.max_frame_size == 16384
    changes = settings.acknowledge()
    assert settings.max_frame_size == 20000
    assert changes[SettingCodes.MAX_FRAME_SIZE].original_value == 16384
    assert changes[SettingCodes.MAX_FRAME_SIZE].new_value == 20000


def test_invalid_max_frame_size_raises_invalid_settings_value():
    with pytest.raises(InvalidSettingsValueError) as excinfo:
        Settings(initial_values={SettingCodes.MAX_FRAME_SIZE: 100})
    assert excinfo.value.error_code == ErrorCodes.PROTOCOL_ERROR


def test_invalid_initial_window_size_raises_flow_control_error_code():
    settings = Settings()
    with pytest.raises(InvalidSettingsValueError) as excinfo:
        settings.initial_window_size = 2**31
    assert excinfo.value.error_code == ErrorCodes.FLOW_CONTROL_ERROR


def test_client_rejects_server_enable_push_one_setting_update():
    client, server, _, _, _ = make_pair()
    server.update_settings({SettingCodes.ENABLE_PUSH: 1})
    with pytest.raises(InvalidSettingsValueError) as excinfo:
        client.receive_data(server.data_to_send())
    assert excinfo.value.error_code == ErrorCodes.PROTOCOL_ERROR


def test_remote_settings_changed_event_from_peer_update():
    client, server, _, _, _ = make_pair()
    client.update_settings({SettingCodes.MAX_CONCURRENT_STREAMS: 7})
    events = server.receive_data(client.data_to_send())
    event = event_of(events, RemoteSettingsChanged)
    change = event.changed_settings[SettingCodes.MAX_CONCURRENT_STREAMS]
    assert change.original_value == 100
    assert change.new_value == 7


def test_settings_acknowledged_event_applies_local_pending_value():
    client, server, _, _, _ = make_pair()
    client.update_settings({SettingCodes.MAX_CONCURRENT_STREAMS: 7})
    server.receive_data(client.data_to_send())
    events = client.receive_data(server.data_to_send())
    ack = event_of(events, SettingsAcknowledged)
    assert ack.changed_settings[SettingCodes.MAX_CONCURRENT_STREAMS].new_value == 7
    assert client.local_settings.max_concurrent_streams == 7


def test_simple_request_event_uses_text_headers_when_configured():
    client, server, _, _, _ = make_pair()
    stream_id, events = open_request(client, server, end_stream=True)
    request = event_of(events, RequestReceived)
    assert request.stream_id == stream_id
    assert request.headers == REQ_HEADERS_TEXT
    assert request.stream_ended.stream_id == stream_id


def test_default_header_encoding_returns_bytes_headers():
    client, server, _, _, _ = make_pair(client_encoding=None, server_encoding=None)
    _, events = open_request(client, server, end_stream=True)
    request = event_of(events, RequestReceived)
    assert request.headers[0] == (b":method", b"GET")


def test_response_headers_are_returned_to_client():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=True)
    server.send_headers(stream_id, RESP_HEADERS_TEXT)
    events = client.receive_data(server.data_to_send())
    response = event_of(events, ResponseReceived)
    assert response.stream_id == stream_id
    assert response.headers == RESP_HEADERS_TEXT


def test_informational_response_is_separate_event():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=True)
    server.send_headers(stream_id, [(":status", "103"), ("link", "</style.css>")])
    events = client.receive_data(server.data_to_send())
    info = event_of(events, InformationalResponseReceived)
    assert info.stream_id == stream_id
    assert info.headers == [(":status", "103"), ("link", "</style.css>")]


def test_data_received_event_has_data_and_flow_control_length():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=True)
    server.send_headers(stream_id, RESP_HEADERS_TEXT)
    server.send_data(stream_id, b"hello")
    events = client.receive_data(server.data_to_send())
    data_event = event_of(events, DataReceived)
    assert data_event.stream_id == stream_id
    assert data_event.data == b"hello"
    assert data_event.flow_controlled_length == 5
    assert data_event.stream_ended is None


def test_data_received_with_end_stream_links_stream_ended_event():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=True)
    server.send_headers(stream_id, RESP_HEADERS_TEXT)
    server.send_data(stream_id, b"ok", end_stream=True)
    events = client.receive_data(server.data_to_send())
    data_event = event_of(events, DataReceived)
    ended = event_of(events, StreamEnded)
    assert data_event.stream_ended is ended
    assert ended.stream_id == stream_id


def test_response_trailers_end_stream_and_link_event():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=True)
    server.send_headers(stream_id, RESP_HEADERS_TEXT)
    server.send_data(stream_id, b"part")
    client.receive_data(server.data_to_send())
    server.send_headers(stream_id, [("x-trailer", "done")], end_stream=True)
    events = client.receive_data(server.data_to_send())
    trailers = event_of(events, TrailersReceived)
    ended = event_of(events, StreamEnded)
    assert trailers.headers == [("x-trailer", "done")]
    assert trailers.stream_ended is ended


def test_send_headers_priority_information_yields_related_priority_event():
    client, server, _, _, _ = make_pair()
    _, events = open_request(
        client,
        server,
        end_stream=True,
        priority_weight=32,
        priority_depends_on=0,
        priority_exclusive=True,
    )
    request = event_of(events, RequestReceived)
    priority = event_of(events, PriorityUpdated)
    assert request.priority_updated is priority
    assert priority.weight == 32
    assert priority.depends_on == 0
    assert priority.exclusive is True


def test_get_next_available_stream_id_is_stable_until_stream_is_opened():
    client, server, _, _, _ = make_pair()
    assert client.get_next_available_stream_id() == 1
    assert client.get_next_available_stream_id() == 1
    open_request(client, server)
    assert client.get_next_available_stream_id() == 3


def test_server_next_available_stream_id_is_even():
    server = H2Connection(H2Configuration(client_side=False))
    assert server.get_next_available_stream_id() == 2


def test_open_stream_counts_follow_request_response_lifecycle():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=False)
    assert client.open_outbound_streams == 1
    assert server.open_inbound_streams == 1
    server.send_headers(stream_id, RESP_HEADERS_TEXT)
    server.send_data(stream_id, b"ok", end_stream=True)
    client.receive_data(server.data_to_send())
    client.end_stream(stream_id)
    server.receive_data(client.data_to_send())
    assert client.open_outbound_streams == 0
    assert server.open_inbound_streams == 0


def test_server_cannot_open_new_stream_with_response_headers():
    server = H2Connection(H2Configuration(client_side=False))
    server.initiate_connection()
    with pytest.raises(ProtocolError):
        server.send_headers(2, RESP_HEADERS_TEXT)


def test_uppercase_outbound_header_is_normalized_when_enabled():
    client, server, _, _, _ = make_pair()
    _, events = open_request(
        client,
        server,
        headers=[(":method", "GET"), (":scheme", "https"), (":authority", "example.com"), (":path", "/"), ("Bad", "x")],
    )
    request = event_of(events, RequestReceived)
    assert ("bad", "x") in request.headers


def test_local_flow_control_window_starts_at_default_for_open_stream():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    assert client.local_flow_control_window(stream_id) == 65535


def test_sending_data_reduces_sender_local_flow_control_window():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    before = client.local_flow_control_window(stream_id)
    client.send_data(stream_id, b"abc")
    assert client.local_flow_control_window(stream_id) == before - 3


def test_stream_window_update_event_is_public():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    server.increment_flow_control_window(123, stream_id)
    events = client.receive_data(server.data_to_send())
    event = event_of(events, WindowUpdated)
    assert event.stream_id == stream_id
    assert event.delta == 123


def test_connection_window_update_event_uses_stream_zero():
    client, server, _, _, _ = make_pair()
    server.increment_flow_control_window(456)
    events = client.receive_data(server.data_to_send())
    event = event_of(events, WindowUpdated)
    assert event.stream_id == 0
    assert event.delta == 456


def test_acknowledge_received_data_rejects_stream_zero():
    conn = H2Connection()
    with pytest.raises(ValueError):
        conn.acknowledge_received_data(1, 0)


def test_acknowledge_received_data_rejects_negative_sizes():
    conn = H2Connection()
    with pytest.raises(ValueError):
        conn.acknowledge_received_data(-1, 1)


def test_send_data_larger_than_frame_size_raises_frame_too_large():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    with pytest.raises(FrameTooLargeError):
        client.send_data(stream_id, b"x" * 20000)


def test_send_data_larger_than_flow_window_raises_flow_control_error():
    client, server, _, _, _ = make_pair()
    server.update_settings({SettingCodes.INITIAL_WINDOW_SIZE: 10})
    client.receive_data(server.data_to_send())
    server.receive_data(client.data_to_send())
    stream_id, _ = open_request(client, server)
    with pytest.raises(FlowControlError):
        client.send_data(stream_id, b"x" * 11)


def test_ping_round_trip_returns_ping_and_ack_events():
    client, server, _, _, _ = make_pair()
    client.ping(b"abcdefgh")
    server_events = server.receive_data(client.data_to_send())
    ping = event_of(server_events, PingReceived)
    assert ping.ping_data == b"abcdefgh"
    client_events = client.receive_data(server.data_to_send())
    ack = event_of(client_events, PingAckReceived)
    assert ack.ping_data == b"abcdefgh"


def test_ping_rejects_text_payload_even_when_eight_characters():
    client, _, _, _, _ = make_pair()
    with pytest.raises(ValueError):
        client.ping("abcdefgh")


def test_ping_rejects_non_eight_byte_payload():
    conn = H2Connection()
    with pytest.raises(ValueError):
        conn.ping(b"short")


def test_reset_stream_is_visible_to_peer():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    client.reset_stream(stream_id, ErrorCodes.CANCEL)
    events = server.receive_data(client.data_to_send())
    reset = event_of(events, StreamReset)
    assert reset.stream_id == stream_id
    assert reset.error_code == ErrorCodes.CANCEL
    assert reset.remote_reset is True


def test_close_connection_is_visible_as_connection_terminated():
    client, server, _, _, _ = make_pair()
    client.close_connection(ErrorCodes.NO_ERROR, additional_data=b"bye", last_stream_id=0)
    events = server.receive_data(client.data_to_send())
    terminated = event_of(events, ConnectionTerminated)
    assert terminated.error_code == ErrorCodes.NO_ERROR
    assert terminated.last_stream_id == 0
    assert terminated.additional_data == b"bye"


def test_client_prioritize_yields_priority_updated_on_server():
    client, server, _, _, _ = make_pair()
    client.prioritize(3, weight=20, depends_on=1, exclusive=False)
    events = server.receive_data(client.data_to_send())
    priority = event_of(events, PriorityUpdated)
    assert priority.stream_id == 3
    assert priority.weight == 20
    assert priority.depends_on == 1
    assert priority.exclusive is False


def test_server_prioritize_raises_rfc1122_error():
    server = H2Connection(H2Configuration(client_side=False))
    with pytest.raises(RFC1122Error):
        server.prioritize(1)


def test_explicit_alternative_service_event_reaches_client():
    client, server, _, _, _ = make_pair()
    server.advertise_alternative_service(b'h2=":443"', origin=b"https://example.com")
    events = client.receive_data(server.data_to_send())
    alt = event_of(events, AlternativeServiceAvailable)
    assert alt.origin == b"https://example.com"
    assert alt.field_value == b'h2=":443"'


def test_alternative_service_rejects_both_origin_and_stream_id():
    server = H2Connection(H2Configuration(client_side=False))
    with pytest.raises(ValueError):
        server.advertise_alternative_service(b'h2=":443"', origin=b"https://example.com", stream_id=1)


def test_alternative_service_rejects_text_field_value():
    server = H2Connection(H2Configuration(client_side=False))
    with pytest.raises(ValueError):
        server.advertise_alternative_service('h2=":443"', origin=b"https://example.com")


def test_no_such_stream_error_exposes_stream_id_from_query():
    conn = H2Connection()
    with pytest.raises(NoSuchStreamError) as excinfo:
        conn.local_flow_control_window(99)
    assert excinfo.value.stream_id == 99


def test_closed_stream_query_returns_remaining_window_until_state_is_purged():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=True)
    server.send_headers(stream_id, RESP_HEADERS_TEXT)
    server.send_data(stream_id, b"ok", end_stream=True)
    client.receive_data(server.data_to_send())
    assert client.local_flow_control_window(stream_id) == 65535


def test_reusing_closed_stream_for_headers_raises_protocol_error():
    client, server, _, _, _ = make_pair()
    open_request(client, server, headers=REQ_HEADERS_TEXT, end_stream=True)
    with pytest.raises(ProtocolError):
        client.send_headers(1, REQ_HEADERS_TEXT)


def test_client_push_stream_raises_protocol_error():
    client = H2Connection(H2Configuration(client_side=True))
    with pytest.raises(ProtocolError):
        client.push_stream(1, 2, REQ_HEADERS_TEXT)


def test_server_push_stream_reaches_client_when_push_is_enabled():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    server.push_stream(stream_id, 2, REQ_HEADERS_TEXT)
    events = client.receive_data(server.data_to_send())
    pushed = event_of(events, PushedStreamReceived)
    assert pushed.parent_stream_id == stream_id
    assert pushed.pushed_stream_id == 2
    assert pushed.headers == REQ_HEADERS_TEXT


def test_initial_window_update_event_is_constrained_by_connection_window():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    before = client.local_flow_control_window(stream_id)
    server.update_settings({SettingCodes.INITIAL_WINDOW_SIZE: 70000})
    events = client.receive_data(server.data_to_send())
    assert event_of(events, RemoteSettingsChanged).changed_settings[SettingCodes.INITIAL_WINDOW_SIZE].new_value == 70000
    server.receive_data(client.data_to_send())
    assert client.local_flow_control_window(stream_id) == before


def test_data_received_padding_counts_in_flow_control_length():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server, end_stream=True)
    server.send_headers(stream_id, RESP_HEADERS_TEXT)
    server.send_data(stream_id, b"hi", pad_length=5)
    events = client.receive_data(server.data_to_send())
    data_event = event_of(events, DataReceived)
    assert data_event.data == b"hi"
    assert data_event.flow_controlled_length == 8


def test_connection_close_prevents_new_streams():
    client, server, _, _, _ = make_pair()
    client.close_connection(ErrorCodes.NO_ERROR)
    server.receive_data(client.data_to_send())
    with pytest.raises(ProtocolError):
        client.send_headers(1, REQ_HEADERS_TEXT)


def test_memoryview_data_is_sent_as_bytes_to_peer():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    client.send_data(stream_id, memoryview(b"abc"))
    events = server.receive_data(client.data_to_send())
    assert event_of(events, DataReceived).data == b"abc"
