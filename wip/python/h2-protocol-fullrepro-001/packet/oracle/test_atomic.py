"""Atomic tests for h2-protocol-fullrepro-001.

Each test exercises ONE public API entry point with ONE behavior.
Independence: if only the tested API is implemented correctly (others stubbed),
the test should pass.
"""
from __future__ import annotations

import pytest

from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.errors import ErrorCodes
from h2.events import StreamEnded, WindowUpdated
from h2.exceptions import (
    FlowControlError,
    FrameTooLargeError,
    InvalidSettingsValueError,
    NoSuchStreamError,
    ProtocolError,
    RFC1122Error,
    StreamClosedError,
)
from h2.settings import ChangedSetting, SettingCodes, Settings
from conftest import REQ_HEADERS, RESP_HEADERS, make_pair, open_stream, event_of


# =============================================================================
# H2Configuration
# =============================================================================


def test_configuration_boolean_field_rejects_non_boolean():
    with pytest.raises(ValueError):
        H2Configuration(client_side="yes")


def test_header_encoding_none_means_bytes_headers():
    cfg = H2Configuration(header_encoding=None)
    assert cfg.header_encoding is None


def test_header_encoding_true_raises_value_error():
    with pytest.raises(ValueError):
        H2Configuration(header_encoding=True)


def test_header_encoding_accepts_string_encoding():
    cfg = H2Configuration(header_encoding="ascii")
    assert cfg.header_encoding == "ascii"


# =============================================================================
# Connection initiation and byte buffer
# =============================================================================


def test_initiate_connection_buffers_client_preface():
    client = H2Connection()
    client.initiate_connection()
    data = client.data_to_send()
    assert data.startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
    assert len(data) > len(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")


def test_data_to_send_drains_buffer_completely():
    client = H2Connection()
    client.initiate_connection()
    _ = client.data_to_send()
    assert client.data_to_send() == b""


def test_data_to_send_with_amount_returns_at_most_that_many_bytes():
    client = H2Connection()
    client.initiate_connection()
    full = client.data_to_send()
    client2 = H2Connection()
    client2.initiate_connection()
    chunk = client2.data_to_send(10)
    assert len(chunk) <= 10
    rest = client2.data_to_send()
    assert chunk + rest == full


def test_clear_outbound_data_buffer_discards_buffered_bytes():
    client = H2Connection()
    client.initiate_connection()
    client.clear_outbound_data_buffer()
    assert client.data_to_send() == b""


def test_server_initiation_does_not_include_client_preface():
    server = H2Connection(H2Configuration(client_side=False))
    server.initiate_connection()
    data = server.data_to_send()
    assert data
    assert not data.startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")


# =============================================================================
# Stream ID allocation
# =============================================================================


def test_client_next_stream_id_starts_at_one():
    client, _ = make_pair()
    assert client.get_next_available_stream_id() == 1


def test_server_next_stream_id_is_even():
    server = H2Connection(H2Configuration(client_side=False))
    assert server.get_next_available_stream_id() == 2


def test_next_stream_id_stable_until_stream_opened():
    client, server = make_pair()
    assert client.get_next_available_stream_id() == 1
    assert client.get_next_available_stream_id() == 1
    open_stream(client, server)
    assert client.get_next_available_stream_id() == 3


# =============================================================================
# Settings
# =============================================================================


def test_settings_defaults_for_client():
    s = Settings(client=True)
    assert s.header_table_size == 4096
    assert s.initial_window_size == 65535
    assert s.max_frame_size == 16384
    assert s.enable_push == 1
    assert s.max_concurrent_streams == 2**32 + 1
    assert s.max_header_list_size is None


def test_settings_defaults_for_server():
    s = Settings(client=False)
    assert s.enable_push == 0


def test_settings_initial_values_override_defaults():
    s = Settings(initial_values={SettingCodes.MAX_CONCURRENT_STREAMS: 5})
    assert s.max_concurrent_streams == 5


def test_settings_assignment_pending_until_acknowledged():
    s = Settings()
    s[SettingCodes.MAX_FRAME_SIZE] = 20000
    assert s.max_frame_size == 16384
    changes = s.acknowledge()
    assert s.max_frame_size == 20000
    assert changes[SettingCodes.MAX_FRAME_SIZE].original_value == 16384
    assert changes[SettingCodes.MAX_FRAME_SIZE].new_value == 20000


def test_settings_acknowledge_empty_returns_empty_dict():
    s = Settings(client=True)
    assert s.acknowledge() == {}


def test_settings_mapping_access_by_integer_code():
    s = Settings(client=True)
    assert s[0x1] == 4096
    s[0x1] = 8192
    s.acknowledge()
    assert s[0x1] == 8192


def test_invalid_max_frame_size_raises_invalid_settings_value():
    with pytest.raises(InvalidSettingsValueError) as exc_info:
        Settings(initial_values={SettingCodes.MAX_FRAME_SIZE: 100})
    assert exc_info.value.error_code == ErrorCodes.PROTOCOL_ERROR


def test_invalid_initial_window_size_raises_flow_control_error_code():
    s = Settings()
    with pytest.raises(InvalidSettingsValueError) as exc_info:
        s.initial_window_size = 2**31
    assert exc_info.value.error_code == ErrorCodes.FLOW_CONTROL_ERROR


def test_changed_setting_exposes_fields():
    cs = ChangedSetting(SettingCodes.MAX_FRAME_SIZE, 16384, 32768)
    assert cs.setting == SettingCodes.MAX_FRAME_SIZE
    assert cs.original_value == 16384
    assert cs.new_value == 32768


# =============================================================================
# Flow control queries and validation
# =============================================================================


def test_local_flow_control_window_starts_at_default():
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    assert client.local_flow_control_window(sid) == 65535


def test_no_such_stream_error_exposes_stream_id():
    conn = H2Connection()
    with pytest.raises(NoSuchStreamError) as exc_info:
        conn.local_flow_control_window(77)
    assert exc_info.value.stream_id == 77


def test_acknowledge_received_data_rejects_stream_zero():
    conn = H2Connection()
    with pytest.raises(ValueError):
        conn.acknowledge_received_data(10, 0)


def test_acknowledge_received_data_rejects_negative_size():
    conn = H2Connection()
    with pytest.raises(ValueError):
        conn.acknowledge_received_data(-5, 1)


# =============================================================================
# Send data validation
# =============================================================================


def test_send_data_larger_than_frame_size_raises():
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    with pytest.raises(FrameTooLargeError):
        client.send_data(sid, b"x" * 20000)


def test_send_data_reduces_local_flow_window():
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    client.send_data(sid, b"x" * 500)
    assert client.local_flow_control_window(sid) == 65035


# =============================================================================
# Ping validation
# =============================================================================


def test_ping_rejects_text_payload():
    client, _ = make_pair()
    with pytest.raises(ValueError):
        client.ping("abcdefgh")


def test_ping_rejects_non_eight_byte_payload():
    conn = H2Connection()
    with pytest.raises(ValueError):
        conn.ping(b"short")


def test_ping_buffers_frame_for_eight_byte_payload():
    client, _ = make_pair()
    client.ping(b"01234567")
    assert len(client.data_to_send()) > 0


# =============================================================================
# Error condition single-API tests
# =============================================================================


def test_server_prioritize_raises_rfc1122():
    server = H2Connection(H2Configuration(client_side=False))
    with pytest.raises(RFC1122Error):
        server.prioritize(1)


def test_server_cannot_open_stream_with_response_headers():
    server = H2Connection(H2Configuration(client_side=False))
    server.initiate_connection()
    with pytest.raises(ProtocolError):
        server.send_headers(2, RESP_HEADERS)


def test_client_push_stream_raises_protocol_error():
    client = H2Connection(H2Configuration(client_side=True))
    with pytest.raises(ProtocolError):
        client.push_stream(1, 2, REQ_HEADERS)


def test_altsvc_rejects_both_origin_and_stream_id():
    server = H2Connection(H2Configuration(client_side=False))
    with pytest.raises(ValueError):
        server.advertise_alternative_service(
            b'h2=":8443"', origin=b"https://node.example", stream_id=1
        )


def test_altsvc_rejects_text_field_value():
    server = H2Connection(H2Configuration(client_side=False))
    with pytest.raises(ValueError):
        server.advertise_alternative_service('h2=":8443"', origin=b"https://node.example")


def test_close_connection_buffers_goaway_and_blocks_new_streams():
    client, _ = make_pair()
    client.close_connection()
    assert len(client.data_to_send()) > 0
    with pytest.raises(ProtocolError):
        client.send_headers(client.get_next_available_stream_id(), REQ_HEADERS)


def test_reset_stream_reduces_open_outbound_count():
    client, server = make_pair()
    sid, _ = open_stream(client, server)
    assert client.open_outbound_streams == 1
    client.reset_stream(sid, ErrorCodes.CANCEL)
    assert client.open_outbound_streams == 0


def test_connection_defaults_max_concurrent_streams_100():
    client, _ = make_pair()
    assert client.local_settings.max_concurrent_streams == 100


def test_connection_defaults_max_header_list_size_65536():
    client, _ = make_pair()
    assert client.local_settings.max_header_list_size == 65536
