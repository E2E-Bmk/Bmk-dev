# Spec2Repo oracle - integration tests for kombu-fullrepro-001

from __future__ import annotations

import pytest

from kombu import Connection, Consumer, Exchange, Producer, Queue
from kombu.exceptions import ContentDisallowed
from kombu.serialization import register, unregister

from conftest import filesystem_file_counts


@pytest.mark.depends_on("test_dumps_uses_json_serializer_for_dicts_by_default", "test_queue_declare_returns_queue_name_for_memory_transport")
def test_producer_publish_and_queue_get_round_trip_json_payload(unique_name):
    """Seam: protocol handoff from Producer serialization to Queue message decoding. CVI-1."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("rt-ex"), "direct", durable=False)
        queue = Queue(unique_name("rt-q"), exchange, routing_key="orders.created", durable=False)

        Producer(conn).publish(
            {"order_id": 501, "region": "west"},
            exchange=exchange,
            routing_key="orders.created",
            declare=[queue],
            serializer="json",
        )
        message = queue(conn.default_channel).get(accept=["json"])

        assert message.payload == {"order_id": 501, "region": "west"}
        assert message.delivery_info == {"exchange": exchange.name, "routing_key": "orders.created"}


@pytest.mark.depends_on("test_message_ack_calls_channel_and_sets_acknowledged_flag")
def test_queue_get_with_manual_ack_removes_message_after_ack(unique_name):
    """Seam: state consistency between Queue.get and Message.ack. CVI-2."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("ack-ex"), "direct", durable=False)
        queue = Queue(unique_name("ack-q"), exchange, routing_key="ack.rk", durable=False)
        Producer(conn).publish({"step": "ack"}, exchange=exchange, routing_key="ack.rk", declare=[queue])

        bound = queue(conn.default_channel)
        message = bound.get(accept=["json"])
        message.ack()

        assert message.acknowledged is True
        assert bound.get(no_ack=True) is None


@pytest.mark.depends_on("test_message_reject_calls_channel_and_sets_acknowledged_flag")
def test_queue_get_reject_without_requeue_removes_message(unique_name):
    """Seam: error propagation between delivery state and queue removal. CVI-2."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("reject-ex"), "direct", durable=False)
        queue = Queue(unique_name("reject-q"), exchange, routing_key="reject.rk", durable=False)
        Producer(conn).publish({"step": "reject"}, exchange=exchange, routing_key="reject.rk", declare=[queue])

        bound = queue(conn.default_channel)
        message = bound.get(accept=["json"])
        message.reject(requeue=False)

        assert message.acknowledged is True
        assert bound.get(no_ack=True) is None


@pytest.mark.depends_on("test_message_reject_calls_channel_and_sets_acknowledged_flag")
def test_queue_get_reject_with_requeue_makes_payload_available_again(unique_name):
    """Seam: state consistency for requeue across Message.reject and Queue.get. CVI-2."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("requeue-ex"), "direct", durable=False)
        queue = Queue(unique_name("requeue-q"), exchange, routing_key="requeue.rk", durable=False)
        Producer(conn).publish({"step": "again"}, exchange=exchange, routing_key="requeue.rk", declare=[queue])

        bound = queue(conn.default_channel)
        first = bound.get(accept=["json"])
        first.reject(requeue=True)
        second = bound.get(accept=["json"])

        assert second.payload == {"step": "again"}
        second.ack()


@pytest.mark.depends_on("test_queue_declare_returns_queue_name_for_memory_transport")
def test_queue_purge_returns_number_of_removed_messages(unique_name):
    """Seam: state consistency between Producer writes and Queue.purge projection."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("purge-ex"), "direct", durable=False)
        queue = Queue(unique_name("purge-q"), exchange, routing_key="purge.rk", durable=False)
        producer = Producer(conn)
        producer.publish({"n": 1}, exchange=exchange, routing_key="purge.rk", declare=[queue])
        producer.publish({"n": 2}, exchange=exchange, routing_key="purge.rk", declare=[queue])
        bound = queue(conn.default_channel)

        assert bound.purge() == 2
        assert bound.get(no_ack=True) is None


@pytest.mark.depends_on("test_exchange_as_dict_exposes_public_declaration_options", "test_queue_as_dict_includes_routing_and_consumer_options")
def test_direct_exchange_routes_only_matching_routing_key(unique_name):
    """Seam: protocol handoff between Exchange routing and Queue binding. CVI-3."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("direct-ex"), "direct", durable=False)
        matching = Queue(unique_name("direct-match"), exchange, routing_key="ship.ready", durable=False)
        other = Queue(unique_name("direct-other"), exchange, routing_key="ship.cancelled", durable=False)

        Producer(conn).publish(
            {"shipment": "ready"},
            exchange=exchange,
            routing_key="ship.ready",
            declare=[matching, other],
        )

        assert matching(conn.default_channel).get(accept=["json"]).payload == {"shipment": "ready"}
        assert other(conn.default_channel).get(no_ack=True) is None


@pytest.mark.depends_on("test_exchange_as_dict_exposes_public_declaration_options", "test_queue_as_dict_includes_routing_and_consumer_options")
def test_topic_exchange_star_pattern_matches_single_word(unique_name):
    """Seam: protocol handoff between topic exchange matching and queue delivery. CVI-3."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("topic-ex"), "topic", durable=False)
        queue = Queue(unique_name("topic-q"), exchange, routing_key="order.*", durable=False)
        Producer(conn).publish({"event": "created"}, exchange=exchange, routing_key="order.created", declare=[queue])
        Producer(conn).publish({"event": "other"}, exchange=exchange, routing_key="invoice.created", declare=[queue])
        bound = queue(conn.default_channel)

        assert bound.get(accept=["json"]).payload == {"event": "created"}
        assert bound.get(no_ack=True) is None


@pytest.mark.depends_on("test_exchange_as_dict_exposes_public_declaration_options", "test_queue_as_dict_includes_routing_and_consumer_options")
def test_topic_exchange_hash_pattern_matches_multiple_words(unique_name):
    """Seam: protocol handoff between topic wildcard policy and queue delivery. CVI-3."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("topic-hash-ex"), "topic", durable=False)
        queue = Queue(unique_name("topic-hash-q"), exchange, routing_key="invoice.#", durable=False)
        Producer(conn).publish({"event": "paid"}, exchange=exchange, routing_key="invoice.paid.eu", declare=[queue])

        assert queue(conn.default_channel).get(accept=["json"]).payload == {"event": "paid"}


@pytest.mark.depends_on("test_memory_transport_supports_direct_topic_and_fanout_exchange_types")
def test_fanout_exchange_delivers_copy_to_each_bound_queue(unique_name):
    """Seam: state consistency across multiple queues bound to the same exchange. CVI-3."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("fanout-ex"), "fanout", durable=False)
        first = Queue(unique_name("fanout-a"), exchange, routing_key="", durable=False)
        second = Queue(unique_name("fanout-b"), exchange, routing_key="", durable=False)
        Producer(conn).publish({"broadcast": 8}, exchange=exchange, routing_key="", declare=[first, second])

        assert first(conn.default_channel).get(accept=["json"]).payload == {"broadcast": 8}
        assert second(conn.default_channel).get(accept=["json"]).payload == {"broadcast": 8}


@pytest.mark.depends_on("test_loads_rejects_json_when_accept_list_names_alias_not_mime_type")
def test_consumer_accept_alias_allows_json_callback_delivery(unique_name):
    """Seam: config interaction between Consumer accept aliases and message decoding. CVI-4."""
    received = []
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("consumer-ex"), "direct", durable=False)
        queue = Queue(unique_name("consumer-q"), exchange, routing_key="consumer.rk", durable=False)

        def callback(body, message):
            received.append((body, message.delivery_info))
            message.ack()

        consumer = Consumer(conn, [queue], callbacks=[callback], accept=["json"])
        with consumer:
            Producer(conn).publish({"consumer": "json"}, exchange=exchange, routing_key="consumer.rk", declare=[queue])
            conn.drain_events(timeout=1)

    assert received == [({"consumer": "json"}, {"exchange": exchange.name, "routing_key": "consumer.rk"})]


@pytest.mark.depends_on("test_pickle_content_is_disabled_by_default_for_low_level_loads")
def test_consumer_rejects_unaccepted_pickle_message(unique_name):
    """Seam: error propagation from deserialization policy through Consumer delivery. CVI-4."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("pickle-ex"), "direct", durable=False)
        queue = Queue(unique_name("pickle-q"), exchange, routing_key="pickle.rk", durable=False)
        Producer(conn).publish(
            {"unsafe": True},
            exchange=exchange,
            routing_key="pickle.rk",
            declare=[queue],
            serializer="pickle",
        )

        message = queue(conn.default_channel).get(accept=["json"])
        with pytest.raises(ContentDisallowed):
            _ = message.payload


@pytest.mark.depends_on("test_raw_serializer_keeps_string_as_application_data_bytes")
def test_raw_content_type_round_trips_through_queue(unique_name):
    """Seam: protocol handoff for raw Producer payloads and Queue message metadata. CVI-1."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("raw-ex"), "direct", durable=False)
        queue = Queue(unique_name("raw-q"), exchange, routing_key="raw.rk", durable=False)
        Producer(conn).publish(
            "opaque text",
            exchange=exchange,
            routing_key="raw.rk",
            declare=[queue],
            serializer="raw",
        )
        message = queue(conn.default_channel).get()

        assert message.payload == "opaque text"
        assert message.content_type == "application/data"
        assert message.content_encoding == "utf-8"


@pytest.mark.depends_on("test_dumps_bytes_without_serializer_uses_binary_application_data")
def test_binary_body_round_trips_without_json_serialization(unique_name):
    """Seam: protocol handoff for binary body encoding and Message payload. CVI-1."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("bytes-ex"), "direct", durable=False)
        queue = Queue(unique_name("bytes-q"), exchange, routing_key="bytes.rk", durable=False)
        Producer(conn).publish(b"\x00\x01s2r", exchange=exchange, routing_key="bytes.rk", declare=[queue])
        message = queue(conn.default_channel).get()

        assert message.payload == b"\x00\x01s2r"
        assert message.content_type == "application/data"
        assert message.content_encoding == "binary"


@pytest.mark.depends_on("test_message_payload_decodes_json_body_lazily")
def test_publish_preserves_headers_and_message_properties(unique_name):
    """Seam: protocol handoff between Producer publish options and Message metadata. CVI-1."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("props-ex"), "direct", durable=False)
        queue = Queue(unique_name("props-q"), exchange, routing_key="props.rk", durable=False)
        Producer(conn).publish(
            {"kind": "metadata"},
            exchange=exchange,
            routing_key="props.rk",
            declare=[queue],
            headers={"trace": "T-900"},
            correlation_id="corr-900",
            reply_to="reply.900",
            priority=5,
            delivery_mode=1,
        )
        message = queue(conn.default_channel).get(accept=["json"])

        assert message.headers == {"trace": "T-900"}
        assert message.properties["correlation_id"] == "corr-900"
        assert message.properties["reply_to"] == "reply.900"
        assert message.properties["priority"] == 5
        assert message.properties["delivery_mode"] == 1


@pytest.mark.depends_on("test_connection_channel_establishes_and_release_closes_memory_transport")
def test_connection_producer_shortcut_publishes_to_declared_queue(unique_name):
    """Seam: lifecycle crossing from Connection shortcut to Producer routing. CVI-5."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("shortcut-ex"), "direct", durable=False)
        queue = Queue(unique_name("shortcut-q"), exchange, routing_key="shortcut.rk", durable=False)

        conn.Producer().publish({"shortcut": True}, exchange=exchange, routing_key="shortcut.rk", declare=[queue])

        assert queue(conn.default_channel).get(accept=["json"]).payload == {"shortcut": True}


@pytest.mark.depends_on("test_queue_recursive_projection_embeds_exchange_projection")
def test_connection_consumer_shortcut_receives_published_message(unique_name):
    """Seam: lifecycle crossing from Connection shortcut to Consumer callback. CVI-5."""
    received = []
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("shortcut-cons-ex"), "direct", durable=False)
        queue = Queue(unique_name("shortcut-cons-q"), exchange, routing_key="shortcut.consumer", durable=False)

        def callback(body, message):
            received.append(body)
            message.ack()

        consumer = conn.Consumer([queue], callbacks=[callback], accept=["json"])
        with consumer:
            Producer(conn).publish({"shortcut": "consumer"}, exchange=exchange, routing_key="shortcut.consumer", declare=[queue])
            conn.drain_events(timeout=1)

    assert received == [{"shortcut": "consumer"}]


@pytest.mark.depends_on("test_queue_declare_returns_queue_name_for_memory_transport")
def test_simple_queue_put_get_ack_uses_named_queue(unique_name):
    """Seam: state consistency between SimpleQueue facade and message queue state. CVI-5."""
    with Connection("memory://") as conn:
        simple = conn.SimpleQueue(unique_name("simple"))
        try:
            simple.put({"level": "INFO", "message": "created"}, serializer="json")
            message = simple.get(block=False)
            message.ack()
            assert message.payload == {"level": "INFO", "message": "created"}
            with pytest.raises(simple.Empty):
                simple.get_nowait()
        finally:
            simple.close()


@pytest.mark.depends_on('test_queue_declare_returns_queue_name_for_memory_transport')
def test_simple_queue_clear_removes_buffered_messages(unique_name):
    """Seam: state consistency between SimpleQueue facade and Queue.purge."""
    with Connection("memory://") as conn:
        simple = conn.SimpleQueue(unique_name("simple-clear"))
        try:
            simple.put({"n": 1}, serializer="json")
            simple.put({"n": 2}, serializer="json")
            assert simple.clear() == 2
            with pytest.raises(simple.Empty):
                simple.get_nowait()
        finally:
            simple.close()


@pytest.mark.depends_on("test_queue_declare_returns_queue_name_for_memory_transport")
def test_simple_buffer_is_transient_but_uses_same_get_put_contract(unique_name):
    """Seam: protocol handoff between SimpleBuffer facade and message decoding."""
    with Connection("memory://") as conn:
        simple = conn.SimpleBuffer(unique_name("buffer"))
        try:
            simple.put({"buffered": 3}, serializer="json")
            message = simple.get(block=False)
            message.ack()
            assert message.payload == {"buffered": 3}
        finally:
            simple.close()


@pytest.mark.depends_on("test_filesystem_connection_reports_transport_without_external_broker")
def test_filesystem_transport_publish_creates_file_projection(unique_name, filesystem_transport_options):
    """Seam: state consistency between Producer publish and filesystem file projection. CVI-6."""
    with Connection("filesystem://", transport_options=filesystem_transport_options) as conn:
        exchange = Exchange(unique_name("fs-ex"), "direct", durable=False)
        queue = Queue(unique_name("fs-q"), exchange, routing_key="fs.rk", durable=False)
        Producer(conn).publish({"fs": "written"}, exchange=exchange, routing_key="fs.rk", declare=[queue])

        assert filesystem_file_counts(filesystem_transport_options) == {"data": 1, "processed": 0}


@pytest.mark.depends_on("test_filesystem_connection_reports_transport_without_external_broker")
def test_filesystem_transport_get_moves_file_to_processed_projection(unique_name, filesystem_transport_options):
    """Seam: lifecycle crossing from filesystem write to read and processed projection. CVI-6."""
    with Connection("filesystem://", transport_options=filesystem_transport_options) as conn:
        exchange = Exchange(unique_name("fs-get-ex"), "direct", durable=False)
        queue = Queue(unique_name("fs-get-q"), exchange, routing_key="fs.get", durable=False)
        Producer(conn).publish({"fs": "read"}, exchange=exchange, routing_key="fs.get", declare=[queue])
        message = queue(conn.default_channel).get(accept=["json"])
        message.ack()

        assert message.payload == {"fs": "read"}
        assert filesystem_file_counts(filesystem_transport_options) == {"data": 0, "processed": 1}


@pytest.mark.depends_on("test_filesystem_connection_reports_transport_without_external_broker")
def test_filesystem_transport_persists_message_across_connections(unique_name, filesystem_transport_options):
    """Seam: lifecycle crossing across Connection instances using filesystem state. CVI-6."""
    exchange = Exchange(unique_name("fs-persist-ex"), "direct", durable=False)
    queue = Queue(unique_name("fs-persist-q"), exchange, routing_key="fs.persist", durable=False)

    with Connection("filesystem://", transport_options=filesystem_transport_options) as conn:
        Producer(conn).publish({"fs": "persisted"}, exchange=exchange, routing_key="fs.persist", declare=[queue])

    with Connection("filesystem://", transport_options=filesystem_transport_options) as conn:
        message = queue(conn.default_channel).get(accept=["json"])
        message.ack()

    assert message.payload == {"fs": "persisted"}
    assert filesystem_file_counts(filesystem_transport_options) == {"data": 0, "processed": 1}


@pytest.mark.depends_on("test_register_adds_custom_serializer_and_unregister_removes_it")
def test_registered_serializer_is_used_by_producer_and_consumer(unique_name):
    """Seam: config interaction between serializer registry, Producer, and Queue decoding. CVI-4."""
    serializer_name = unique_name("serializer").replace(".", "-")

    def encode(value):
        return f"{value['code']}|{value['qty']}".encode("utf-8")

    def decode(value):
        code, qty = value.decode("utf-8").split("|")
        return {"code": code, "qty": int(qty)}

    register(serializer_name, encode, decode, f"application/x-{serializer_name}", "utf-8")
    try:
        with Connection("memory://") as conn:
            exchange = Exchange(unique_name("custom-ser-ex"), "direct", durable=False)
            queue = Queue(unique_name("custom-ser-q"), exchange, routing_key="custom.ser", durable=False)
            Producer(conn).publish(
                {"code": "SKU-7", "qty": 13},
                exchange=exchange,
                routing_key="custom.ser",
                declare=[queue],
                serializer=serializer_name,
            )
            message = queue(conn.default_channel).get(accept=[f"application/x-{serializer_name}"])
            assert message.payload == {"code": "SKU-7", "qty": 13}
    finally:
        unregister(serializer_name)


@pytest.mark.depends_on("test_queue_delete_is_idempotent_for_memory_transport")
def test_queue_delete_removes_pending_messages_from_named_queue(unique_name):
    """Seam: state consistency between entity lifecycle and queued message projection."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("delete-ex"), "direct", durable=False)
        queue = Queue(unique_name("delete-q"), exchange, routing_key="delete.rk", durable=False)
        Producer(conn).publish({"delete": 1}, exchange=exchange, routing_key="delete.rk", declare=[queue])
        bound = queue(conn.default_channel)

        assert bound.delete() is None
        assert bound.get(no_ack=True) is None


@pytest.mark.depends_on("test_queue_as_dict_includes_routing_and_consumer_options")
def test_no_ack_queue_get_removes_message_without_explicit_ack(unique_name):
    """Seam: config interaction between Queue no_ack and message removal."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("noack-ex"), "direct", durable=False)
        queue = Queue(unique_name("noack-q"), exchange, routing_key="noack.rk", durable=False, no_ack=True)
        Producer(conn).publish({"auto": "ack"}, exchange=exchange, routing_key="noack.rk", declare=[queue])
        bound = queue(conn.default_channel)
        message = bound.get()

        assert message.payload == {"auto": "ack"}
        assert bound.get(no_ack=True) is None


@pytest.mark.depends_on("test_queue_declare_returns_queue_name_for_memory_transport")
def test_multiple_consumers_on_same_connection_are_drained_by_connection(unique_name):
    """Seam: state consistency across Consumer registrations on one Connection."""
    seen = []
    with Connection("memory://") as conn:
        first_exchange = Exchange(unique_name("multi-a-ex"), "direct", durable=False)
        second_exchange = Exchange(unique_name("multi-b-ex"), "direct", durable=False)
        first_queue = Queue(unique_name("multi-a-q"), first_exchange, routing_key="multi.a", durable=False)
        second_queue = Queue(unique_name("multi-b-q"), second_exchange, routing_key="multi.b", durable=False)

        def first_callback(body, message):
            seen.append(("first", body))
            message.ack()

        def second_callback(body, message):
            seen.append(("second", body))
            message.ack()

        first_consumer = Consumer(conn, [first_queue], callbacks=[first_callback], accept=["json"])
        second_consumer = Consumer(conn, [second_queue], callbacks=[second_callback], accept=["json"])
        with first_consumer, second_consumer:
            Producer(conn).publish({"slot": 1}, exchange=first_exchange, routing_key="multi.a", declare=[first_queue])
            Producer(conn).publish({"slot": 2}, exchange=second_exchange, routing_key="multi.b", declare=[second_queue])
            conn.drain_events(timeout=1)
            conn.drain_events(timeout=1)

    assert seen == [("first", {"slot": 1}), ("second", {"slot": 2})]


@pytest.mark.depends_on("test_connection_as_uri_masks_password_by_default")
def test_connection_context_manager_releases_transport_after_workflow(unique_name):
    """Seam: lifecycle crossing from context manager to transport release."""
    conn = Connection("memory://")
    exchange = Exchange(unique_name("ctx-ex"), "direct", durable=False)
    queue = Queue(unique_name("ctx-q"), exchange, routing_key="ctx.rk", durable=False)

    with conn as active:
        Producer(active).publish({"ctx": True}, exchange=exchange, routing_key="ctx.rk", declare=[queue])
        assert queue(active.default_channel).get(accept=["json"]).payload == {"ctx": True}

    assert conn.connected is False


@pytest.mark.depends_on("test_queue_recursive_projection_embeds_exchange_projection")
def test_bound_queue_projection_remains_consistent_after_declare(unique_name):
    """Seam: state consistency between entity binding, declaration, and public projection."""
    with Connection("memory://") as conn:
        exchange = Exchange(unique_name("projection-ex"), "topic", durable=False)
        queue = Queue(unique_name("projection-q"), exchange, routing_key="projection.*", durable=False)
        bound = queue(conn.default_channel)
        declared_name = bound.declare()
        projection = bound.as_dict(recurse=True)

    assert declared_name == queue.name
    assert projection["exchange"]["name"] == exchange.name
    assert projection["routing_key"] == "projection.*"


@pytest.mark.depends_on('test_message_payload_decodes_json_body_lazily')
def test_reply_to_and_correlation_id_drive_rpc_style_reply_workflow(unique_name):
    """Seam: protocol handoff between request metadata and reply routing. CVI-1."""
    with Connection("memory://") as conn:
        request_exchange = Exchange(unique_name("rpc-req-ex"), "direct", durable=False)
        request_queue = Queue(unique_name("rpc-req-q"), request_exchange, routing_key="rpc.request", durable=False)
        reply_queue = Queue(unique_name("rpc-reply-q"), Exchange("", "direct"), routing_key="", durable=False)
        producer = Producer(conn)
        producer.publish(
            {"n": 6},
            exchange=request_exchange,
            routing_key="rpc.request",
            declare=[request_queue, reply_queue],
            correlation_id="corr-rpc-6",
            reply_to=reply_queue.name,
        )
        request = request_queue(conn.default_channel).get(accept=["json"])
        producer.publish(
            {"result": 8},
            exchange="",
            routing_key=request.properties["reply_to"],
            correlation_id=request.properties["correlation_id"],
            serializer="json",
        )
        reply = reply_queue(conn.default_channel).get(accept=["json"])

    assert request.payload == {"n": 6}
    assert reply.payload == {"result": 8}
    assert reply.properties["correlation_id"] == "corr-rpc-6"
