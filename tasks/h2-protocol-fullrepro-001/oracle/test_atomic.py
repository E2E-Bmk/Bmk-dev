# Spec2Repo oracle - atomic tests for h2-protocol-fullrepro-001
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


def test_get_next_available_stream_id_is_stable_until_stream_is_opened():
    client, server, _, _, _ = make_pair()
    assert client.get_next_available_stream_id() == 1
    assert client.get_next_available_stream_id() == 1
    open_request(client, server)
    assert client.get_next_available_stream_id() == 3


def test_server_next_available_stream_id_is_even():
    server = H2Connection(H2Configuration(client_side=False))
    assert server.get_next_available_stream_id() == 2


def test_server_cannot_open_new_stream_with_response_headers():
    server = H2Connection(H2Configuration(client_side=False))
    server.initiate_connection()
    with pytest.raises(ProtocolError):
        server.send_headers(2, RESP_HEADERS_TEXT)


def test_local_flow_control_window_starts_at_default_for_open_stream():
    client, server, _, _, _ = make_pair()
    stream_id, _ = open_request(client, server)
    assert client.local_flow_control_window(stream_id) == 65535


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


def test_ping_rejects_text_payload_even_when_eight_characters():
    client, _, _, _, _ = make_pair()
    with pytest.raises(ValueError):
        client.ping("abcdefgh")


def test_ping_rejects_non_eight_byte_payload():
    conn = H2Connection()
    with pytest.raises(ValueError):
        conn.ping(b"short")


def test_server_prioritize_raises_rfc1122_error():
    server = H2Connection(H2Configuration(client_side=False))
    with pytest.raises(RFC1122Error):
        server.prioritize(1)


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


def test_reusing_closed_stream_for_headers_raises_protocol_error():
    client, server, _, _, _ = make_pair()
    open_request(client, server, headers=REQ_HEADERS_TEXT, end_stream=True)
    with pytest.raises(ProtocolError):
        client.send_headers(1, REQ_HEADERS_TEXT)


def test_client_push_stream_raises_protocol_error():
    client = H2Connection(H2Configuration(client_side=True))
    with pytest.raises(ProtocolError):
        client.push_stream(1, 2, REQ_HEADERS_TEXT)
