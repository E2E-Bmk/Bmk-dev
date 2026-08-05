# Spec Test Map - kombu-fullrepro-001

oracle_version: 2026-08-04-artifact-only-v1
oracle_source: generated_public_api
oracle_files: oracle/test_atomic.py, oracle/test_integration.py
runtime_requirements: oracle/requirements.txt
reference_source: https://github.com/celery/kombu
reference_commit: bb4c7755641ca274efa45969e71a2b93bb53ca1a
stage4_evidence: ARTIFACT_ONLY
counts: atomic=34, integration=29, system_e2e=0, total=63
depends_on_annotation_coverage: 29/29 integration tests
final_scoreable: 63

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| oracle/test_atomic.py::test_parse_url_extracts_memory_transport_credentials_and_options | generated | atomic | positive | Connection And Transport Behavior | covered | URL parsing public contract |
| oracle/test_atomic.py::test_connection_without_url_uses_documented_default_connection_fields | generated | atomic | positive | Connection And Transport Behavior | covered | default connection metadata |
| oracle/test_atomic.py::test_memory_connection_reports_transport_and_virtual_host_without_connecting | generated | atomic | positive | Connection And Transport Behavior | covered | memory transport metadata |
| oracle/test_atomic.py::test_connection_as_uri_masks_password_by_default | generated | atomic | positive | Connection And Transport Behavior | covered | URI password masking |
| oracle/test_atomic.py::test_connection_channel_establishes_and_release_closes_memory_transport | generated | atomic | positive | Connection And Transport Behavior | covered | connection lifecycle |
| oracle/test_atomic.py::test_exchange_as_dict_exposes_public_declaration_options | generated | atomic | positive | Entity Declaration Behavior | covered | exchange projection |
| oracle/test_atomic.py::test_exchange_persistent_delivery_mode_maps_to_numeric_value | generated | atomic | positive | Entity Declaration Behavior | covered | delivery mode projection |
| oracle/test_atomic.py::test_queue_as_dict_includes_routing_and_consumer_options | generated | atomic | positive | Entity Declaration Behavior | covered | queue projection |
| oracle/test_atomic.py::test_queue_recursive_projection_embeds_exchange_projection | generated | atomic | positive | Entity Declaration Behavior | covered | recursive queue projection |
| oracle/test_atomic.py::test_queue_call_binds_queue_to_channel_without_mutating_original | generated | atomic | positive | Entity Declaration Behavior | covered | queue binding |
| oracle/test_atomic.py::test_message_payload_decodes_json_body_lazily | generated | atomic | positive | Message State And Payload Behavior | covered | JSON payload decoding |
| oracle/test_atomic.py::test_message_ack_calls_channel_and_sets_acknowledged_flag | generated | atomic | positive | Message State And Payload Behavior | covered | ack state transition |
| oracle/test_atomic.py::test_message_ack_with_multiple_forwards_multiple_flag | generated | atomic | positive | Message State And Payload Behavior | covered | ack multiple flag |
| oracle/test_atomic.py::test_message_reject_calls_channel_and_sets_acknowledged_flag | generated | atomic | positive | Message State And Payload Behavior | covered | reject state transition |
| oracle/test_atomic.py::test_message_second_ack_raises_message_state_error | generated | atomic | failure_path | Error Semantics | covered | duplicate ack error |
| oracle/test_atomic.py::test_message_reject_after_ack_raises_message_state_error | generated | atomic | failure_path | Error Semantics | covered | reject after ack error |
| oracle/test_atomic.py::test_message_invalid_json_payload_raises_decode_error | generated | atomic | failure_path | Error Semantics | covered | invalid JSON error |
| oracle/test_atomic.py::test_dumps_uses_json_serializer_for_dicts_by_default | generated | atomic | positive | Serialization Behavior | covered | default JSON serializer |
| oracle/test_atomic.py::test_dumps_preserves_decimal_values_through_json_round_trip | generated | atomic | positive | Serialization Behavior | covered | Decimal round trip |
| oracle/test_atomic.py::test_dumps_plain_string_without_serializer_uses_text_plain_bytes | generated | atomic | positive | Serialization Behavior | covered | plain text serialization |
| oracle/test_atomic.py::test_dumps_bytes_without_serializer_uses_binary_application_data | generated | atomic | positive | Serialization Behavior | covered | bytes serialization |
| oracle/test_atomic.py::test_raw_serializer_keeps_string_as_application_data_bytes | generated | atomic | positive | Serialization Behavior | covered | raw serializer |
| oracle/test_atomic.py::test_loads_allows_untrusted_text_plain_without_accept_list | generated | atomic | positive | Serialization Behavior | covered | text loads |
| oracle/test_atomic.py::test_loads_rejects_json_when_accept_list_names_alias_not_mime_type | generated | atomic | failure_path | Serialization Behavior | covered | accept content-type policy |
| oracle/test_atomic.py::test_loads_accepts_json_when_accept_list_names_content_type | generated | atomic | positive | Serialization Behavior | covered | accepted JSON content type |
| oracle/test_atomic.py::test_loads_returns_raw_payload_for_unknown_content_type | generated | atomic | positive | Serialization Behavior | covered | unknown content fallback |
| oracle/test_atomic.py::test_unknown_serializer_name_raises_serializer_not_installed | generated | atomic | failure_path | Error Semantics | covered | missing serializer |
| oracle/test_atomic.py::test_pickle_content_is_disabled_by_default_for_low_level_loads | generated | atomic | failure_path | Error Semantics | covered | pickle disabled |
| oracle/test_atomic.py::test_register_adds_custom_serializer_and_unregister_removes_it | generated | atomic | positive | Serialization Behavior | covered | serializer registry lifecycle |
| oracle/test_atomic.py::test_registry_maps_json_name_and_content_type | generated | atomic | positive | Serialization Behavior | covered | registry mappings |
| oracle/test_atomic.py::test_memory_transport_supports_direct_topic_and_fanout_exchange_types | generated | atomic | positive | Connection And Transport Behavior | covered | exchange type support |
| oracle/test_atomic.py::test_filesystem_connection_reports_transport_without_external_broker | generated | atomic | positive | Connection And Transport Behavior | covered | filesystem transport metadata |
| oracle/test_atomic.py::test_queue_declare_returns_queue_name_for_memory_transport | generated | atomic | positive | Entity Declaration Behavior | covered | queue declaration |
| oracle/test_atomic.py::test_queue_delete_is_idempotent_for_memory_transport | generated | atomic | positive | Entity Declaration Behavior | covered | queue delete idempotence |
| oracle/test_integration.py::test_producer_publish_and_queue_get_round_trip_json_payload | generated | integration | positive | Routing And Consumer Behavior | covered | producer to queue seam |
| oracle/test_integration.py::test_queue_get_with_manual_ack_removes_message_after_ack | generated | integration | positive | Routing And Consumer Behavior | covered | get and ack seam |
| oracle/test_integration.py::test_queue_get_reject_without_requeue_removes_message | generated | integration | positive | Routing And Consumer Behavior | covered | reject removal seam |
| oracle/test_integration.py::test_queue_get_reject_with_requeue_makes_payload_available_again | generated | integration | positive | Routing And Consumer Behavior | covered | reject requeue seam |
| oracle/test_integration.py::test_queue_purge_returns_number_of_removed_messages | generated | integration | positive | Entity Declaration Behavior | covered | publish and purge seam |
| oracle/test_integration.py::test_direct_exchange_routes_only_matching_routing_key | generated | integration | positive | Routing And Consumer Behavior | covered | direct routing seam |
| oracle/test_integration.py::test_topic_exchange_star_pattern_matches_single_word | generated | integration | positive | Routing And Consumer Behavior | covered | topic star routing seam |
| oracle/test_integration.py::test_topic_exchange_hash_pattern_matches_multiple_words | generated | integration | positive | Routing And Consumer Behavior | covered | topic hash routing seam |
| oracle/test_integration.py::test_fanout_exchange_delivers_copy_to_each_bound_queue | generated | integration | positive | Routing And Consumer Behavior | covered | fanout copy seam |
| oracle/test_integration.py::test_consumer_accept_alias_allows_json_callback_delivery | generated | integration | positive | Routing And Consumer Behavior | covered | consumer accept seam |
| oracle/test_integration.py::test_consumer_rejects_unaccepted_pickle_message | generated | integration | failure_path | Error Semantics | covered | content policy seam |
| oracle/test_integration.py::test_raw_content_type_round_trips_through_queue | generated | integration | positive | Routing And Consumer Behavior | covered | raw content seam |
| oracle/test_integration.py::test_binary_body_round_trips_without_json_serialization | generated | integration | positive | Routing And Consumer Behavior | covered | binary content seam |
| oracle/test_integration.py::test_publish_preserves_headers_and_message_properties | generated | integration | positive | Message State And Payload Behavior | covered | publish metadata seam |
| oracle/test_integration.py::test_connection_producer_shortcut_publishes_to_declared_queue | generated | integration | positive | Connection And Transport Behavior | covered | producer shortcut seam |
| oracle/test_integration.py::test_connection_consumer_shortcut_receives_published_message | generated | integration | positive | Connection And Transport Behavior | covered | consumer shortcut seam |
| oracle/test_integration.py::test_simple_queue_put_get_ack_uses_named_queue | generated | integration | positive | Simple Queue And Filesystem Behavior | covered | SimpleQueue put/get seam |
| oracle/test_integration.py::test_simple_queue_clear_removes_buffered_messages | generated | integration | positive | Simple Queue And Filesystem Behavior | covered | SimpleQueue clear seam |
| oracle/test_integration.py::test_simple_buffer_is_transient_but_uses_same_get_put_contract | generated | integration | positive | Simple Queue And Filesystem Behavior | covered | SimpleBuffer seam |
| oracle/test_integration.py::test_filesystem_transport_publish_creates_file_projection | generated | integration | positive | Simple Queue And Filesystem Behavior | covered | filesystem publish projection |
| oracle/test_integration.py::test_filesystem_transport_get_moves_file_to_processed_projection | generated | integration | positive | Simple Queue And Filesystem Behavior | covered | filesystem processed projection |
| oracle/test_integration.py::test_filesystem_transport_persists_message_across_connections | generated | integration | positive | Simple Queue And Filesystem Behavior | covered | filesystem lifecycle seam |
| oracle/test_integration.py::test_registered_serializer_is_used_by_producer_and_consumer | generated | integration | positive | Serialization Behavior | covered | registry and producer seam |
| oracle/test_integration.py::test_queue_delete_removes_pending_messages_from_named_queue | generated | integration | positive | Entity Declaration Behavior | covered | queue delete message seam |
| oracle/test_integration.py::test_no_ack_queue_get_removes_message_without_explicit_ack | generated | integration | positive | Routing And Consumer Behavior | covered | no_ack policy seam |
| oracle/test_integration.py::test_multiple_consumers_on_same_connection_are_drained_by_connection | generated | integration | positive | Routing And Consumer Behavior | covered | multiple consumer seam |
| oracle/test_integration.py::test_connection_context_manager_releases_transport_after_workflow | generated | integration | positive | Connection And Transport Behavior | covered | context manager lifecycle seam |
| oracle/test_integration.py::test_bound_queue_projection_remains_consistent_after_declare | generated | integration | positive | Entity Declaration Behavior | covered | bound projection seam |
| oracle/test_integration.py::test_reply_to_and_correlation_id_drive_rpc_style_reply_workflow | generated | integration | positive | Message State And Payload Behavior | covered | reply metadata seam |
