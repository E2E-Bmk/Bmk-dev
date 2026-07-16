# Spec Test Map - httpx-client-fullrepro-001

oracle_version: 2026-07-10T05:10:23+08:00
filter/oracle_source: generated_only
scorer_isolation: --remove-path httpx
reference_score: filter/reference_score.json (Linux/WSL, 78 passed / 78 total)
dummy_score: filter/dummy_score.json (Linux/WSL, 0 passed / 78 total)

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/generated_tests.py::test_client_close_is_idempotent_and_blocks_later_send | generated | integration | Client Lifecycle | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_context_returns_self_and_closes_transport | generated | integration | Client Lifecycle | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_reentering_open_context_raises | generated | atomic | Client Lifecycle | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_enter_after_close_raises | generated | atomic | Client Lifecycle | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_client_context_and_aclose_are_idempotent | generated | integration | Client Lifecycle | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_build_request_merges_base_url_headers_cookies_and_params | generated | integration | Configuration Merge Rules | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_request_sends_prepared_request_and_reads_body | generated | integration | Request Building and Sending | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_send_stream_true_leaves_response_unread_until_read | generated | integration | Request Building and Sending | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_stream_context_closes_response_on_exit | generated | integration | Request Building and Sending | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_client_request_and_build_request | generated | integration | Request Building and Sending | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_base_url_relative_paths_resolve_under_base_path | generated | atomic | Request Building and Sending | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_invalid_url_construction_raises_public_exception | generated | atomic | Query Parameters and URLs | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_request_level_auth_none_disables_client_auth | generated | integration | Configuration Merge Rules | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_request_level_follow_redirects_overrides_client_default | generated | integration | Configuration Merge Rules | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_headers_case_insensitive_lookup_and_duplicates | generated | atomic | Headers | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_headers_setting_replaces_all_existing_values | generated | atomic | Headers | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_headers_get_and_missing_key_behavior | generated | atomic | Headers | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_headers_split_commas_keeps_ordered_values | generated | atomic | Headers | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_invalid_header_value_is_rejected | generated | atomic | Headers | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_queryparams_lookup_lists_and_string_encoding | generated | atomic | Query Parameters and URLs | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_queryparams_set_add_remove_and_merge_are_immutable | generated | atomic | Query Parameters and URLs | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_url_exposes_normalized_components | generated | atomic | Query Parameters and URLs | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_url_copy_and_param_helpers_return_new_urls | generated | atomic | Query Parameters and URLs | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_url_join_resolves_relative_references | generated | atomic | Query Parameters and URLs | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_cookies_set_get_delete_and_conflict | generated | atomic | Cookies | covered | public API only; reference-observed; dummy-failing; missing-delete expectation removed because it was not aligned with the current spec |
| filter/generated_tests.py::test_cookies_extract_and_send_matching_cookie_header | generated | integration | Cookies | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_cookies_clear_removes_matching_domain_and_path | generated | atomic | Cookies | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_cookie_jar_persists_between_requests | generated | system_e2e | Cross-View Invariants | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_request_model_adds_default_headers_and_content_length | generated | atomic | Request Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_request_json_body_sets_content_type_and_bytes | generated | atomic | Request Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_request_stream_content_requires_read_before_content_access | generated | atomic | Request Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_status_reason_http_version_and_url_projection | generated | atomic | Response Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_request_and_url_require_attached_request | generated | atomic | Response Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_content_text_json_and_cookies | generated | atomic | Response Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_links_are_parsed_by_relation | generated | atomic | Response Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_raise_for_status_returns_self_for_success_and_raises_for_error | generated | atomic | Response Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_status_category_booleans | generated | atomic | Response Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_has_redirect_location_requires_redirect_status_and_location | generated | atomic | Response Model | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_streamed_response_read_caches_content_and_closes_stream | generated | atomic | Streaming and Read State | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_iter_bytes_text_lines_and_raw_consume_streams | generated | atomic | Streaming and Read State | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_closed_before_read_raises_stream_closed | generated | atomic | Streaming and Read State | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_num_bytes_downloaded_tracks_raw_stream_consumption | generated | atomic | Streaming and Read State | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_response_aread_and_aiter_bytes | generated | integration | Streaming and Read State | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_redirect_without_following_exposes_next_request | generated | integration | Redirects and History | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_follow_redirects_populates_history_and_final_request | generated | system_e2e | Redirects and History | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_too_many_redirects_raises_with_request | generated | atomic | Redirects and History | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_post_303_redirect_rewrites_to_get | generated | integration | Redirects and History | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_request_and_response_hooks_run_in_order_and_mutate_request | generated | integration | Event Hooks | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_hook_can_read_streaming_body_before_return | generated | integration | Event Hooks | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_client_event_hooks_property_can_be_mutated | generated | atomic | Event Hooks | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_client_rejects_sync_hook_when_awaited | generated | atomic | Event Hooks | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_basic_auth_tuple_sets_authorization_header | generated | atomic | Authentication | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_callable_auth_mutates_prepared_request | generated | atomic | Authentication | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_custom_auth_flow_can_retry_with_response_history | generated | integration | Authentication | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_auth_flow_reads_request_body_when_required | generated | integration | Authentication | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_mock_transport_calls_sync_handler_with_request | generated | integration | Transports | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_mock_transport_awaits_async_handler | generated | integration | Transports | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_base_transport_without_handle_request_raises_not_implemented | generated | atomic | Transports | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_wsgi_transport_populates_environ_and_returns_response | generated | integration | Transports | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_wsgi_transport_can_return_error_response_when_configured | generated | integration | Transports | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_asgi_transport_populates_scope_and_returns_response | generated | integration | Transports | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_sync_client_with_async_transport_raises_capability_error | generated | atomic | Transports | covered | public API only; reference-observed; dummy-failing; exact exception class is not asserted |
| filter/generated_tests.py::test_public_exception_hierarchy_and_request_attribute | generated | atomic | Error Semantics | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_stream_state_exceptions_are_public_stream_errors | generated | atomic | Error Semantics | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_unsupported_protocol_raises_request_error_subclass | generated | atomic | Error Semantics | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_request_hook_header_visible_to_transport_cross_view | generated | system_e2e | Cross-View Invariants | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_object_seen_by_hook_is_returned_to_caller | generated | system_e2e | Cross-View Invariants | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_built_request_defaults_match_url_header_and_query_views | generated | system_e2e | Cross-View Invariants | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_response_read_bytes_match_content_and_text_cache | generated | system_e2e | Cross-View Invariants | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_mocked_sync_workflow_with_hooks_redirects_and_json | generated | system_e2e | Mocked Sync Request With Hooks and Redirects | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_mocked_sync_workflow_handler_exception_propagates | generated | integration | Mocked Sync Request With Hooks and Redirects | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_mocked_sync_workflow_preserves_client_params_into_redirect | generated | system_e2e | Mocked Sync Request With Hooks and Redirects | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_asgi_representative_workflow | generated | system_e2e | Async ASGI Request | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_asgi_representative_workflow_exception_propagates | generated | integration | Async ASGI Request | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_async_asgi_representative_workflow_can_return_error_response_when_configured | generated | integration | Async ASGI Request | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_cli_help_exits_successfully | generated | system_e2e | Invocation Protocol | covered | public API only; reference-observed; dummy-failing |
| filter/generated_tests.py::test_cli_rejects_invalid_json_before_request | generated | system_e2e | Invocation Protocol | covered | public `httpx.main` only; reference-observed Click parameter failure before request dispatch; dummy-failing |
| filter/generated_tests.py::test_cli_requires_url_argument_before_request | generated | system_e2e | Invocation Protocol | covered | public `httpx.main` only; reference-observed Click usage failure before request dispatch; dummy-failing |
Total: 78 | kept (covered): 78 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 78
