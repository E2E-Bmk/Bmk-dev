# Spec2Repo oracle - atomic tests for kombu-fullrepro-001

from __future__ import annotations

from decimal import Decimal

import pytest

from kombu import Connection, Exchange, Queue, parse_url
from kombu.exceptions import ContentDisallowed, DecodeError, MessageStateError, SerializerNotInstalled
from kombu.message import Message
from kombu.serialization import dumps, loads, register, registry, unregister

from conftest import RecordingChannel


def test_parse_url_extracts_memory_transport_credentials_and_options():
    parsed = parse_url("memory://user-a:pass-b@broker.test:4321/vhost-a?ssl=1&heartbeat=7")

    assert parsed == {
        "transport": "memory",
        "hostname": "broker.test",
        "port": 4321,
        "userid": "user-a",
        "password": "pass-b",
        "virtual_host": "vhost-a",
        "ssl": "1",
        "heartbeat": "7",
    }


def test_connection_without_url_uses_documented_default_connection_fields():
    conn = Connection()

    info = conn.info()
    assert info["hostname"] == "localhost"
    assert info["userid"] == "guest"
    assert info["password"] == "guest"
    assert info["virtual_host"] == "/"
    assert info["transport"] == "amqp"
    assert info["port"] == 5672


def test_memory_connection_reports_transport_and_virtual_host_without_connecting():
    conn = Connection("memory://localhost//")

    assert conn.connected is False
    assert conn.transport_cls == "memory"
    assert conn.info()["transport"] == "memory"
    assert conn.info()["virtual_host"] == "/"


def test_connection_as_uri_masks_password_by_default():
    conn = Connection("memory://alpha:secret@localhost//")

    assert conn.as_uri() == "memory://alpha:**@localhost//"


def test_connection_channel_establishes_and_release_closes_memory_transport():
    conn = Connection("memory://")

    channel = conn.channel()
    assert conn.connected is True
    channel.close()
    conn.release()
    assert conn.connected is False


def test_exchange_as_dict_exposes_public_declaration_options():
    exchange = Exchange("orders.atomic", type="direct", durable=False, auto_delete=True)

    assert exchange.as_dict() == {
        "name": "orders.atomic",
        "type": "direct",
        "arguments": None,
        "durable": False,
        "passive": False,
        "auto_delete": True,
        "delivery_mode": None,
        "no_declare": False,
    }


def test_exchange_persistent_delivery_mode_maps_to_numeric_value():
    exchange = Exchange("orders.persist", type="direct", delivery_mode="persistent")

    assert exchange.as_dict()["delivery_mode"] == 2
    assert exchange.as_dict()["durable"] is True


def test_queue_as_dict_includes_routing_and_consumer_options():
    exchange = Exchange("entity.atomic", type="topic", durable=False)
    queue = Queue(
        "entity.atomic.queue",
        exchange,
        routing_key="entity.*",
        durable=False,
        no_ack=True,
        queue_arguments={"x-max-priority": 4},
        consumer_arguments={"x-priority": 9},
    )

    projection = queue.as_dict()
    assert projection["name"] == "entity.atomic.queue"
    assert projection["exchange"] is exchange
    assert projection["routing_key"] == "entity.*"
    assert projection["queue_arguments"] == {"x-max-priority": 4}
    assert projection["consumer_arguments"] == {"x-priority": 9}
    assert projection["no_ack"] is True


def test_queue_recursive_projection_embeds_exchange_projection():
    exchange = Exchange("entity.recursive", type="direct", durable=False)
    queue = Queue("entity.recursive.queue", exchange, routing_key="rk", durable=False)

    projection = queue.as_dict(recurse=True)
    assert projection["exchange"]["name"] == "entity.recursive"
    assert projection["exchange"]["type"] == "direct"
    assert projection["routing_key"] == "rk"


def test_queue_call_binds_queue_to_channel_without_mutating_original():
    conn = Connection("memory://")
    queue = Queue("entity.bound", durable=False)

    bound = queue(conn.default_channel)
    assert bound.is_bound is True
    assert bound.channel is conn.default_channel
    assert queue.is_bound is False
    conn.release()


def test_message_payload_decodes_json_body_lazily():
    message = Message(
        body='{"sku": "A-17", "count": 3}',
        content_type="application/json",
        content_encoding="utf-8",
        headers={"trace": "trace-17"},
        properties={"correlation_id": "corr-17"},
        delivery_tag="tag-17",
    )

    assert message.payload == {"sku": "A-17", "count": 3}
    assert message.headers == {"trace": "trace-17"}
    assert message.properties == {"correlation_id": "corr-17"}
    assert message.delivery_tag == "tag-17"


def test_message_ack_calls_channel_and_sets_acknowledged_flag():
    channel = RecordingChannel()
    message = Message(channel=channel, delivery_tag="ack-17")

    assert message.ack() is None
    assert channel.calls == [("ack", "ack-17", False)]
    assert message.acknowledged is True


def test_message_ack_with_multiple_forwards_multiple_flag():
    channel = RecordingChannel()
    message = Message(channel=channel, delivery_tag="ack-many")

    message.ack(multiple=True)
    assert channel.calls == [("ack", "ack-many", True)]


def test_message_reject_calls_channel_and_sets_acknowledged_flag():
    channel = RecordingChannel()
    message = Message(channel=channel, delivery_tag="reject-17")

    assert message.reject(requeue=True) is None
    assert channel.calls == [("reject", "reject-17", True)]
    assert message.acknowledged is True


def test_message_second_ack_raises_message_state_error():
    message = Message(channel=RecordingChannel(), delivery_tag="double-ack")
    message.ack()

    with pytest.raises(MessageStateError):
        message.ack()


def test_message_reject_after_ack_raises_message_state_error():
    message = Message(channel=RecordingChannel(), delivery_tag="ack-reject")
    message.ack()

    with pytest.raises(MessageStateError):
        message.reject()


def test_message_invalid_json_payload_raises_decode_error():
    message = Message(body="{broken", content_type="application/json", content_encoding="utf-8")

    with pytest.raises(DecodeError):
        _ = message.payload


def test_dumps_uses_json_serializer_for_dicts_by_default():
    content_type, content_encoding, payload = dumps({"answer": 42, "ok": True})

    assert content_type == "application/json"
    assert content_encoding == "utf-8"
    assert loads(payload, content_type, content_encoding, accept=[content_type]) == {
        "answer": 42,
        "ok": True,
    }


def test_dumps_preserves_decimal_values_through_json_round_trip():
    content_type, content_encoding, payload = dumps({"price": Decimal("12.30")})

    decoded = loads(payload, content_type, content_encoding, accept=[content_type])
    assert decoded == {"price": Decimal("12.30")}


def test_dumps_plain_string_without_serializer_uses_text_plain_bytes():
    content_type, content_encoding, payload = dumps("plain text value")

    assert (content_type, content_encoding, payload) == (
        "text/plain",
        "utf-8",
        b"plain text value",
    )


def test_dumps_bytes_without_serializer_uses_binary_application_data():
    content_type, content_encoding, payload = dumps(b"\x00payload")

    assert (content_type, content_encoding, payload) == (
        "application/data",
        "binary",
        b"\x00payload",
    )


def test_raw_serializer_keeps_string_as_application_data_bytes():
    assert dumps("raw payload", serializer="raw") == (
        "application/data",
        "utf-8",
        b"raw payload",
    )


def test_loads_allows_untrusted_text_plain_without_accept_list():
    assert loads(b"plain payload", "text/plain", "utf-8") == "plain payload"


def test_loads_rejects_json_when_accept_list_names_alias_not_mime_type():
    with pytest.raises(ContentDisallowed):
        loads('{"x": 1}', "application/json", "utf-8", accept=["json"])


def test_loads_accepts_json_when_accept_list_names_content_type():
    assert loads('{"x": 1}', "application/json", "utf-8", accept=["application/json"]) == {"x": 1}


def test_loads_returns_raw_payload_for_unknown_content_type():
    assert loads("raw-ish", "application/x-s2r-unknown", "utf-8") == "raw-ish"


def test_unknown_serializer_name_raises_serializer_not_installed():
    with pytest.raises(SerializerNotInstalled):
        dumps({"payload": 1}, serializer="s2r-missing")


def test_pickle_content_is_disabled_by_default_for_low_level_loads():
    with pytest.raises(ContentDisallowed):
        loads(b"not-a-pickle", "application/x-python-serialize", "binary")


def test_register_adds_custom_serializer_and_unregister_removes_it():
    name = "s2r-upper-atomic"

    def encode(value):
        return value.upper().encode("utf-8")

    def decode(value):
        return value.decode("utf-8").lower()

    register(name, encode, decode, "application/x-s2r-upper", "utf-8")
    try:
        content_type, content_encoding, payload = dumps("MixedCase", serializer=name)
        assert (content_type, content_encoding, payload) == (
            "application/x-s2r-upper",
            "utf-8",
            b"MIXEDCASE",
        )
        assert loads(payload, content_type, content_encoding, accept=[content_type]) == "mixedcase"
    finally:
        unregister(name)

    with pytest.raises(SerializerNotInstalled):
        dumps("again", serializer=name)


def test_registry_maps_json_name_and_content_type():
    assert registry.name_to_type["json"] == "application/json"
    assert registry.type_to_name["application/json"] == "json"


def test_memory_transport_supports_direct_topic_and_fanout_exchange_types():
    conn = Connection("memory://")

    assert conn.supports_exchange_type("direct") is True
    assert conn.supports_exchange_type("topic") is True
    assert conn.supports_exchange_type("fanout") is True


def test_filesystem_connection_reports_transport_without_external_broker(filesystem_transport_options):
    conn = Connection("filesystem://localhost//", transport_options=filesystem_transport_options)

    assert conn.transport_cls == "filesystem"
    assert conn.info()["transport"] == "filesystem"
    assert conn.info()["transport_options"] == filesystem_transport_options


def test_queue_declare_returns_queue_name_for_memory_transport(unique_name):
    conn = Connection("memory://")
    queue = Queue(unique_name("declare"), Exchange(unique_name("declare-ex"), "direct"), "rk", durable=False)

    assert queue(conn.default_channel).declare() == queue.name
    conn.release()


def test_queue_delete_is_idempotent_for_memory_transport(unique_name):
    conn = Connection("memory://")
    queue = Queue(unique_name("delete"), Exchange(unique_name("delete-ex"), "direct"), "rk", durable=False)
    bound = queue(conn.default_channel)
    bound.declare()

    assert bound.delete() is None
    assert bound.delete() is None
    conn.release()
