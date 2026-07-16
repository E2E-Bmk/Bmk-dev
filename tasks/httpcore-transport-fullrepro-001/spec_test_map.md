# spec_test_map.md
oracle_version: 20260704T114845Z
spec_version: v2
filter/oracle_source: generated_only
scorer_isolation: score_pytest_original.py --remove-path httpcore

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| tests/test_transport_fullrepro.py::test_pool_request_returns_status_headers_content_and_extensions | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_request_line_uses_path_and_query_from_url | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_empty_url_path_is_sent_as_slash | generated | integration | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_default_http_port_is_omitted_from_host_header | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_non_default_http_port_is_included_in_host_header | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_user_supplied_host_header_is_not_replaced | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_mapping_headers_are_sent_as_http_headers | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_sequence_headers_preserve_duplicate_names | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_bytes_method_and_url_are_accepted | generated | integration | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_bytes_content_adds_content_length_and_body | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_empty_bytes_content_adds_zero_content_length | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_iterable_content_uses_chunked_transfer_encoding | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_explicit_content_length_is_preserved | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_explicit_transfer_encoding_prevents_auto_content_length | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_stream_response_iterates_body_chunks_without_preloading_content | generated | integration | HTTP/1.1 Response Handling and Streaming | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_stream_response_read_makes_content_available | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_response_iter_stream_can_only_be_consumed_once | generated | atomic | HTTP/1.1 Response Handling and Streaming | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_response_read_caches_content_for_repeated_access | generated | atomic | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_response_close_calls_stream_close_when_available | generated | atomic | HTTP/1.1 Response Handling and Streaming | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_same_origin_reuses_connection_after_response_is_read | generated | system_e2e | Connection Pool Lifecycle | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_different_origins_open_distinct_connections | generated | system_e2e | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_pool_close_closes_idle_connections | generated | system_e2e | Connection Pool Lifecycle | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_pool_context_manager_closes_idle_connections_on_exit | generated | system_e2e | Connection Pool Lifecycle | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_zero_keepalive_limit_closes_connection_after_response_body | generated | system_e2e | Connection Pool Lifecycle | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_unsupported_protocol_raises_public_exception | generated | integration | Error Semantics | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_missing_protocol_raises_public_exception | generated | integration | Error Semantics | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_local_address_is_passed_to_tcp_connect | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_socket_options_are_passed_to_tcp_connect | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_unix_domain_socket_uses_connect_unix_socket | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_connect_timeout_extension_is_passed_to_backend_connect | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_read_timeout_extension_is_passed_to_stream_reads | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_write_timeout_extension_is_passed_to_stream_writes | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_https_request_connects_to_default_tls_port_and_starts_tls | generated | integration | TLS, UDS, Timeouts, and Retries | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_https_request_uses_sni_hostname_extension_when_present | generated | integration | TLS, UDS, Timeouts, and Retries | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_https_non_default_port_is_used_for_connect_and_host_header | generated | integration | TLS, UDS, Timeouts, and Retries | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_connect_error_is_retried_when_retries_are_available | generated | system_e2e | TLS, UDS, Timeouts, and Retries | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_connect_error_is_raised_when_no_retries_remain | generated | system_e2e | TLS, UDS, Timeouts, and Retries | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_multiple_retries_use_exponential_backoff_sequence | generated | system_e2e | TLS, UDS, Timeouts, and Retries | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_http_connection_direct_handle_request_returns_response | generated | integration | Direct HTTP Connections | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_http_connection_rejects_requests_for_other_origins | generated | integration | Direct HTTP Connections | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_http_connection_close_closes_the_underlying_stream | generated | integration | Direct HTTP Connections | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_http_connection_reuses_its_stream_for_same_origin_requests | generated | system_e2e | Connection Pool Lifecycle | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_request_target_extension_overrides_url_target_on_the_wire | generated | integration | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_request_object_target_extension_changes_url_target | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_url_from_string_exposes_components_and_default_origin_port | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_url_from_explicit_components_round_trips_to_bytes | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_url_target_allows_options_star_request | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_absolute_form_target_is_sent_unchanged | generated | integration | HTTP/1.1 Request Serialization | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_request_rejects_non_ascii_method_strings | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_request_rejects_non_ascii_header_values | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_url_rejects_non_ascii_url_strings | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_response_header_mapping_is_normalized_to_byte_pairs | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_proxy_auth_adds_basic_proxy_authorization_header | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_proxy_preserves_custom_headers_after_authorization_header | generated | atomic | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_mock_backend_can_serve_documented_http11_response | generated | integration | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_mock_stream_read_returns_configured_chunks_then_empty_bytes | generated | atomic | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_mock_stream_start_tls_returns_stream_itself | generated | atomic | Network Backends and Mock Streams | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_network_stream_extra_info_defaults_to_none | generated | atomic | Network Backends and Mock Streams | excluded | dummy implementation passes this structural default; not scoreable |
| tests/test_transport_fullrepro.py::test_trace_extension_reports_started_and_complete_events | generated | system_e2e | Trace Events and Extensions | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_trace_extension_reports_failed_connection_event | generated | system_e2e | Trace Events and Extensions | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_premature_server_disconnect_raises_remote_protocol_error | generated | integration | HTTP/1.1 Response Handling and Streaming | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_invalid_response_header_raises_remote_protocol_error | generated | integration | URL, Request, Response Models | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_connect_response_exposes_network_stream_extension | generated | system_e2e | HTTP/1.1 Response Handling and Streaming | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_pool_connections_property_returns_a_list_snapshot | generated | system_e2e | Connection Pool Lifecycle | covered | public local backend behavior |
| tests/test_transport_fullrepro.py::test_connection_available_state_is_publicly_queryable | generated | system_e2e | Direct HTTP Connections | covered | public local backend behavior |

Total: 65 | kept (covered): 64 | spec_gap: 0 | source-only: 0 | excluded: 1 | final scoreable: 64
