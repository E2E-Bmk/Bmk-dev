"""Shared fixtures, helpers, and constants for h2 oracle tests."""
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


# ---------------------------------------------------------------------------
# Constants (anti-memorization: different values from upstream tests)
# ---------------------------------------------------------------------------

REQ_HEADERS = [
    (":method", "GET"),
    (":scheme", "https"),
    (":authority", "testnode.example"),
    (":path", "/resource"),
]

RESP_HEADERS = [(":status", "200"), ("server", "oracle-h2")]

POST_HEADERS = [
    (":method", "POST"),
    (":scheme", "https"),
    (":authority", "testnode.example"),
    (":path", "/submit"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_pair(
    client_encoding: str | None = "utf-8",
    server_encoding: str | None = "utf-8",
) -> tuple[H2Connection, H2Connection]:
    """Create a fully-handshaked client/server connection pair."""
    client = H2Connection(H2Configuration(client_side=True, header_encoding=client_encoding))
    server = H2Connection(H2Configuration(client_side=False, header_encoding=server_encoding))
    client.initiate_connection()
    server.initiate_connection()
    server.receive_data(client.data_to_send())
    client.receive_data(server.data_to_send())
    server.receive_data(client.data_to_send())
    return client, server


def open_stream(
    client: H2Connection,
    server: H2Connection,
    *,
    end_stream: bool = False,
    headers=None,
    **priority,
) -> tuple[int, list]:
    """Open a stream from client and deliver to server, return stream_id and events."""
    stream_id = client.get_next_available_stream_id()
    client.send_headers(stream_id, headers or REQ_HEADERS, end_stream=end_stream, **priority)
    events = server.receive_data(client.data_to_send())
    return stream_id, events


def event_of(events, event_type):
    """Extract a single event of given type from a list."""
    return next(e for e in events if isinstance(e, event_type))


def events_of(events, event_type):
    """Extract all events of given type from a list."""
    return [e for e in events if isinstance(e, event_type)]
