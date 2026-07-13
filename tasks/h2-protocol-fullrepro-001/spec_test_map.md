# Spec Test Map - h2-protocol-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-07-10T00:00:00Z
reference_observation: WSL Python 3.11 reference scorer passed 55/55 with --remove-path h2 after spec_v2 filter correction

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| generated_tests.py::test_client_initiate_connection_buffers_preface_and_settings | generated | integration | section Connection Lifecycle and Byte Buffering | covered | client preface plus opaque SETTINGS bytes accepted by compatible peer |
| generated_tests.py::test_server_initiate_connection_buffers_settings_without_client_preface | generated | integration | section Connection Lifecycle and Byte Buffering | covered | server initial SETTINGS bytes exclude client preface and are accepted by compatible peer |
| generated_tests.py::test_data_to_send_amount_drains_in_chunks | generated | atomic | section Connection Lifecycle and Byte Buffering | covered | chunked reads preserve opaque buffered bytes and drain the buffer |
| generated_tests.py::test_clear_outbound_data_buffer_discards_pending_bytes | generated | atomic | section Connection Lifecycle and Byte Buffering | covered | clear outbound buffer |
| generated_tests.py::test_receive_data_retains_incomplete_frame_until_remaining_bytes_arrive | generated | integration | section Connection Lifecycle and Byte Buffering | covered | incomplete frame buffering |
| generated_tests.py::test_client_upgrade_returns_header_value_and_buffers_connection_bytes | generated | integration | section Connection Lifecycle and Byte Buffering | covered | h2c header is opaque bytes consumable by a compatible server |
| generated_tests.py::test_server_upgrade_accepts_client_header_and_returns_none | generated | integration | section Public API | covered | server h2c upgrade setup |
| generated_tests.py::test_settings_defaults_for_client_and_server | generated | atomic | section Settings Behavior | covered | settings defaults |
| generated_tests.py::test_settings_initial_values_override_active_defaults | generated | atomic | section Settings Behavior | covered | initial setting overrides |
| generated_tests.py::test_settings_assignment_is_pending_until_acknowledged | generated | atomic | section Settings Behavior | covered | pending settings acknowledgement |
| generated_tests.py::test_invalid_max_frame_size_raises_invalid_settings_value | generated | atomic | section Error Semantics | covered | invalid max frame setting error code |
| generated_tests.py::test_invalid_initial_window_size_raises_flow_control_error_code | generated | atomic | section Error Semantics | covered | invalid initial window setting error code |
| generated_tests.py::test_client_rejects_server_enable_push_one_setting_update | generated | integration | section Settings Behavior | covered | invalid peer SETTINGS update through documented connection APIs |
| generated_tests.py::test_remote_settings_changed_event_from_peer_update | generated | integration | section Settings Behavior | covered | original MAX_CONCURRENT_STREAMS value derives from documented H2Connection advertised default |
| generated_tests.py::test_settings_acknowledged_event_applies_local_pending_value | generated | integration | section Settings Behavior | covered | settings ack applies local value |
| generated_tests.py::test_simple_request_event_uses_text_headers_when_configured | generated | system_e2e | section Configuration | covered | request event with decoded headers |
| generated_tests.py::test_default_header_encoding_returns_bytes_headers | generated | integration | section Configuration | covered | default header encoding behavior |
| generated_tests.py::test_response_headers_are_returned_to_client | generated | system_e2e | section Headers, Data, and Events | covered | response headers event |
| generated_tests.py::test_informational_response_is_separate_event | generated | integration | section Headers, Data, and Events | covered | informational response event |
| generated_tests.py::test_data_received_event_has_data_and_flow_control_length | generated | integration | section Headers, Data, and Events | covered | data event attributes |
| generated_tests.py::test_data_received_with_end_stream_links_stream_ended_event | generated | system_e2e | section Cross-View Invariants | covered | data event related stream end |
| generated_tests.py::test_response_trailers_end_stream_and_link_event | generated | system_e2e | section Headers, Data, and Events | covered | trailers event related stream end |
| generated_tests.py::test_send_headers_priority_information_yields_related_priority_event | generated | integration | section Cross-View Invariants | covered | headers related priority event |
| generated_tests.py::test_get_next_available_stream_id_is_stable_until_stream_is_opened | generated | atomic | section Public API | covered | stream id stability |
| generated_tests.py::test_server_next_available_stream_id_is_even | generated | atomic | section Stream Lifecycle | covered | server stream id parity |
| generated_tests.py::test_open_stream_counts_follow_request_response_lifecycle | generated | system_e2e | section Stream Lifecycle | covered | open stream counts lifecycle |
| generated_tests.py::test_server_cannot_open_new_stream_with_response_headers | generated | atomic | section Error Semantics | covered | server invalid stream open |
| generated_tests.py::test_uppercase_outbound_header_is_normalized_when_enabled | generated | integration | section Configuration | covered | outbound header normalization |
| generated_tests.py::test_local_flow_control_window_starts_at_default_for_open_stream | generated | atomic | section Flow Control | covered | default local flow window |
| generated_tests.py::test_sending_data_reduces_sender_local_flow_control_window | generated | integration | section Flow Control | covered | data consumes sender flow window |
| generated_tests.py::test_stream_window_update_event_is_public | generated | integration | section Flow Control | covered | stream window update event |
| generated_tests.py::test_connection_window_update_event_uses_stream_zero | generated | integration | section Flow Control | covered | connection window update event |
| generated_tests.py::test_acknowledge_received_data_rejects_stream_zero | generated | atomic | section Error Semantics | covered | invalid acknowledge stream id |
| generated_tests.py::test_acknowledge_received_data_rejects_negative_sizes | generated | atomic | section Error Semantics | covered | invalid acknowledge size |
| generated_tests.py::test_send_data_larger_than_frame_size_raises_frame_too_large | generated | atomic | section Error Semantics | covered | oversized data frame error |
| generated_tests.py::test_send_data_larger_than_flow_window_raises_flow_control_error | generated | integration | section Flow Control | covered | peer SETTINGS_INITIAL_WINDOW_SIZE constrains sender flow window |
| generated_tests.py::test_ping_round_trip_returns_ping_and_ack_events | generated | system_e2e | section Ping, Priority, and Alternative Services | covered | ping round trip |
| generated_tests.py::test_ping_rejects_text_payload_even_when_eight_characters | generated | atomic | section Error Semantics | covered | invalid ping type |
| generated_tests.py::test_ping_rejects_non_eight_byte_payload | generated | atomic | section Error Semantics | covered | invalid ping length |
| generated_tests.py::test_reset_stream_is_visible_to_peer | generated | integration | section Stream Lifecycle | covered | reset stream peer event |
| generated_tests.py::test_close_connection_is_visible_as_connection_terminated | generated | integration | section Stream Lifecycle | covered | GOAWAY peer event |
| generated_tests.py::test_client_prioritize_yields_priority_updated_on_server | generated | integration | section Ping, Priority, and Alternative Services | covered | client priority event |
| generated_tests.py::test_server_prioritize_raises_rfc1122_error | generated | atomic | section Error Semantics | covered | server priority forbidden |
| generated_tests.py::test_explicit_alternative_service_event_reaches_client | generated | integration | section Ping, Priority, and Alternative Services | covered | alternative service event |
| generated_tests.py::test_alternative_service_rejects_both_origin_and_stream_id | generated | atomic | section Error Semantics | covered | invalid alternative service arguments |
| generated_tests.py::test_alternative_service_rejects_text_field_value | generated | atomic | section Error Semantics | covered | invalid alternative service field type |
| generated_tests.py::test_no_such_stream_error_exposes_stream_id_from_query | generated | atomic | section Error Semantics | covered | missing stream query error |
| generated_tests.py::test_closed_stream_query_returns_remaining_window_until_state_is_purged | generated | integration | section Flow Control | covered | closed stream flow projection |
| generated_tests.py::test_reusing_closed_stream_for_headers_raises_protocol_error | generated | atomic | section Error Semantics | covered | closed stream send error |
| generated_tests.py::test_client_push_stream_raises_protocol_error | generated | atomic | section Error Semantics | covered | client push forbidden |
| generated_tests.py::test_server_push_stream_reaches_client_when_push_is_enabled | generated | system_e2e | section Stream Lifecycle | covered | server push peer event |
| generated_tests.py::test_initial_window_update_event_is_constrained_by_connection_window | generated | integration | section Cross-View Invariants | covered | settings and flow window projection agreement |
| generated_tests.py::test_data_received_padding_counts_in_flow_control_length | generated | integration | section Flow Control | covered | padding counts in flow-controlled length |
| generated_tests.py::test_connection_close_prevents_new_streams | generated | integration | section Cross-View Invariants | covered | GOAWAY prevents new stream actions |
| generated_tests.py::test_memoryview_data_is_sent_as_bytes_to_peer | generated | integration | section Cross-View Invariants | covered | memoryview send_data input |

Total: 55 | kept (covered): 55 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 55
Layer summary: atomic=22 | integration=26 | system_e2e=7
