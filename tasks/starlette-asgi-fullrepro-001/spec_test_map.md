# Spec Test Map - starlette-asgi-fullrepro-001

oracle_version: 2026-07-10T18:20:45+08:00
oracle_source: upstream_rewritten
track_b: not_triggered
scorer_isolation: --remove-path starlette
dummy_gate: retained 64 are a strict subset of the 66 tests that failed the dummy; 0 collection errors
reference_gate: 64/64 passed on Linux/WSL with --remove-path starlette; 0 collection errors
spec_gap: 0

## Coverage Quotas

| spec_section | covered_tests | minimum | result |
|---|---:|---:|---|
| Public API | 4 | 3 | pass |
| Product State Model | 4 | 3 | pass |
| Application And Lifespan Behavior | 5 | 3 | pass |
| Routing Behavior | 7 | 3 | pass |
| Request Behavior | 5 | 3 | pass |
| Response Behavior | 12 | 3 | pass |
| WebSocket Behavior | 6 | 3 | pass |
| Static Files Behavior | 6 | 3 | pass |
| Middleware Behavior | 5 | 3 | pass |
| Error Semantics | 8 | 3 | pass |
| Cross-View Invariants | 5 | 5 | pass |
| Representative Workflow | 3 | 3 | pass |

## Oracle Map

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| filter/rewritten_upstream_tests.py::test_application_route_is_visible_through_testclient | upstream | integration | Public API; Application And Lifespan Behavior | covered | public rewrite of tests/test_applications.py::test_func_route |
| filter/rewritten_upstream_tests.py::test_application_places_itself_on_request_scope | upstream | integration | Application And Lifespan Behavior | covered | public rewrite of tests/test_applications.py::test_request_state |
| filter/rewritten_upstream_tests.py::test_application_rejects_middleware_added_after_first_call | upstream | atomic | Application And Lifespan Behavior | covered | public rewrite of tests/test_applications.py::test_middleware_stack_init |
| filter/rewritten_upstream_tests.py::test_testclient_context_runs_lifespan_startup_and_shutdown | upstream | system_e2e | Application And Lifespan Behavior | covered | public rewrite of tests/test_applications.py::test_app_async_cm_lifespan |
| filter/rewritten_upstream_tests.py::test_testclient_construction_alone_does_not_run_lifespan | upstream | integration | Application And Lifespan Behavior | covered | public rewrite of tests/test_testclient.py::test_use_testclient_as_contextmanager |
| filter/rewritten_upstream_tests.py::test_lifespan_state_is_shallow_copied_between_requests | upstream | system_e2e | Product State Model | covered | public rewrite of tests/test_routing.py::test_lifespan_state_async_cm |
| filter/rewritten_upstream_tests.py::test_routing_uses_first_matching_route | upstream | integration | Routing Behavior | covered | public rewrite of tests/test_routing.py::test_router_duplicate_path |
| filter/rewritten_upstream_tests.py::test_routing_converts_integer_path_parameter | upstream | integration | Routing Behavior | covered | public rewrite of tests/test_routing.py::test_route_converters |
| filter/rewritten_upstream_tests.py::test_routing_path_convertor_captures_slashes | upstream | integration | Routing Behavior | covered | public rewrite of tests/test_applications.py::test_mounted_route_path_params |
| filter/rewritten_upstream_tests.py::test_route_requires_leading_slash | upstream | atomic | Routing Behavior | covered | public rewrite of tests/test_routing.py::test_standalone_route_does_not_match |
| filter/rewritten_upstream_tests.py::test_route_rejects_duplicate_parameter_names | upstream | atomic | Error Semantics | covered | public rewrite of tests/test_routing.py::test_duplicated_param_names |
| filter/rewritten_upstream_tests.py::test_route_rejects_unknown_convertor | upstream | atomic | Error Semantics | covered | public rewrite of tests/test_routing.py::test_route_name |
| filter/rewritten_upstream_tests.py::test_route_get_implies_head_and_method_error_has_allow_header | upstream | integration | Routing Behavior | covered | public rewrite of tests/test_applications.py::test_405 |
| filter/rewritten_upstream_tests.py::test_router_reverse_lookup_and_missing_name | upstream | atomic | Routing Behavior | covered | public rewrite of tests/test_routing.py::test_url_path_for |
| filter/rewritten_upstream_tests.py::test_host_route_ignores_port_when_matching | upstream | integration | Routing Behavior | covered | public rewrite of tests/test_routing.py::test_host_routing |
| filter/rewritten_upstream_tests.py::test_request_is_mapping_over_scope | upstream | atomic | Request Behavior | covered | public rewrite of tests/test_requests.py::test_request_scope_interface |
| filter/rewritten_upstream_tests.py::test_request_url_and_query_params_follow_scope | upstream | atomic | Request Behavior | covered | public rewrite of tests/test_requests.py::test_request_url |
| filter/rewritten_upstream_tests.py::test_request_headers_are_case_insensitive_and_immutable | upstream | atomic | Request Behavior | covered | public rewrite of tests/test_requests.py::test_request_headers |
| filter/rewritten_upstream_tests.py::test_public_multidict_views_preserve_repeated_values | upstream | atomic | Public API | covered | public rewrite of tests/test_datastructures.py::test_queryparams |
| filter/rewritten_upstream_tests.py::test_request_body_is_cached | upstream | atomic | Request Behavior | covered | public rewrite of tests/test_requests.py::test_request_body |
| filter/rewritten_upstream_tests.py::test_request_invalid_json_raises_decoder_error | upstream | atomic | Error Semantics | covered | public rewrite of tests/test_requests.py::test_request_json |
| filter/rewritten_upstream_tests.py::test_request_client_projection_handles_present_and_missing_client | upstream | atomic | Request Behavior | covered | public rewrite of tests/test_requests.py::test_request_client |
| filter/rewritten_upstream_tests.py::test_response_none_renders_empty_body | upstream | atomic | Public API; Response Behavior | covered | public rewrite of tests/test_responses.py::test_empty_response |
| filter/rewritten_upstream_tests.py::test_response_adds_content_length_and_text_charset | upstream | atomic | Response Behavior | covered | public rewrite of tests/test_responses.py::test_text_response |
| filter/rewritten_upstream_tests.py::test_response_204_omits_content_length | upstream | atomic | Response Behavior | covered | public rewrite of tests/test_responses.py::test_empty_204_response |
| filter/rewritten_upstream_tests.py::test_response_preserves_caller_content_headers | upstream | atomic | Response Behavior | covered | public rewrite of tests/test_responses.py::test_response_headers |
| filter/rewritten_upstream_tests.py::test_json_response_is_compact_utf8_and_preserves_unicode | upstream | atomic | Response Behavior | covered | public rewrite of tests/test_responses.py::test_json_none_response |
| filter/rewritten_upstream_tests.py::test_json_response_rejects_non_finite_numbers | upstream | atomic | Error Semantics | covered | public rewrite of tests/test_responses.py::test_non_empty_response |
| filter/rewritten_upstream_tests.py::test_redirect_response_quotes_location | upstream | atomic | Response Behavior | covered | public rewrite of tests/test_responses.py::test_quoting_redirect_response |
| filter/rewritten_upstream_tests.py::test_response_cookie_set_and_delete_are_observable | upstream | atomic | Response Behavior | covered | public rewrite of tests/test_responses.py::test_set_cookie |
| filter/rewritten_upstream_tests.py::test_background_tasks_execute_in_insertion_order | upstream | integration | Response Behavior | covered | public rewrite of tests/test_background.py::test_multiple_tasks |
| filter/rewritten_upstream_tests.py::test_streaming_response_streams_sync_iterable | upstream | integration | Response Behavior | covered | public rewrite of tests/test_responses.py::test_sync_streaming_response |
| filter/rewritten_upstream_tests.py::test_file_response_headers_and_body | upstream | integration | Response Behavior | covered | public rewrite of tests/test_responses.py::test_file_response |
| filter/rewritten_upstream_tests.py::test_file_response_missing_file_raises_at_call_time | upstream | atomic | Response Behavior | covered | public rewrite of tests/test_responses.py::test_file_response_with_missing_file_raises_error |
| filter/rewritten_upstream_tests.py::test_file_response_supports_byte_range_and_head | upstream | integration | Response Behavior | covered | public rewrite of tests/test_responses.py::test_file_response_range |
| filter/rewritten_upstream_tests.py::test_websocket_text_round_trip | upstream | integration | Public API; WebSocket Behavior | covered | public rewrite of tests/test_websockets.py::test_websocket_send_and_receive_text |
| filter/rewritten_upstream_tests.py::test_websocket_json_text_and_binary_modes | upstream | integration | WebSocket Behavior | covered | public rewrite of tests/test_websockets.py::test_websocket_binary_json |
| filter/rewritten_upstream_tests.py::test_websocket_disconnect_preserves_code_and_reason | upstream | integration | WebSocket Behavior | covered | public rewrite of tests/test_websockets.py::test_websocket_close_reason |
| filter/rewritten_upstream_tests.py::test_websocket_close_before_accept_disconnects_client | upstream | integration | WebSocket Behavior | covered | public rewrite of tests/test_websockets.py::test_rejected_connection |
| filter/rewritten_upstream_tests.py::test_websocket_accept_selects_subprotocol | upstream | integration | WebSocket Behavior | covered | public rewrite of tests/test_websockets.py::test_subprotocol |
| filter/rewritten_upstream_tests.py::test_websocket_path_params_and_query_are_public_views | upstream | integration | WebSocket Behavior | covered | public rewrite of tests/test_websockets.py::test_websocket_query_params |
| filter/rewritten_upstream_tests.py::test_staticfiles_serves_file_bytes | upstream | integration | Static Files Behavior | covered | public rewrite of tests/test_staticfiles.py::test_staticfiles |
| filter/rewritten_upstream_tests.py::test_staticfiles_head_returns_headers_without_body | upstream | integration | Static Files Behavior | covered | public rewrite of tests/test_staticfiles.py::test_staticfiles_head_with_middleware |
| filter/rewritten_upstream_tests.py::test_staticfiles_rejects_post_method | upstream | integration | Static Files Behavior | covered | public rewrite of tests/test_staticfiles.py::test_staticfiles_post |
| filter/rewritten_upstream_tests.py::test_staticfiles_html_directory_redirects_and_serves_index | upstream | system_e2e | Static Files Behavior | covered | public rewrite of tests/test_staticfiles.py::test_staticfiles_html_normal |
| filter/rewritten_upstream_tests.py::test_staticfiles_html_custom_404 | upstream | integration | Static Files Behavior | covered | public rewrite of tests/test_staticfiles.py::test_staticfiles_html_without_index |
| filter/rewritten_upstream_tests.py::test_staticfiles_conditional_request_returns_304 | upstream | integration | Static Files Behavior | covered | public rewrite of tests/test_staticfiles.py::test_staticfiles_304_with_etag_match |
| filter/rewritten_upstream_tests.py::test_https_redirect_preserves_path_and_query | upstream | integration | Middleware Behavior | covered | public rewrite of tests/middleware/test_https_redirect.py::test_https_redirect_middleware |
| filter/rewritten_upstream_tests.py::test_trusted_host_rejects_unknown_host | upstream | integration | Middleware Behavior | covered | public rewrite of tests/middleware/test_trusted_host.py::test_trusted_host_middleware |
| filter/rewritten_upstream_tests.py::test_gzip_compresses_large_response_and_skips_small_response | upstream | integration | Middleware Behavior | covered | public rewrite of tests/middleware/test_gzip.py::test_gzip_responses |
| filter/rewritten_upstream_tests.py::test_cors_preflight_allows_configured_origin_and_method | upstream | integration | Middleware Behavior | covered | public rewrite of tests/middleware/test_cors.py::test_cors_allow_specific_origin |
| filter/rewritten_upstream_tests.py::test_cors_simple_response_echoes_origin_with_credentials | upstream | integration | Middleware Behavior | covered | public rewrite of tests/middleware/test_cors.py::test_cors_allow_all_except_credentials |
| filter/rewritten_upstream_tests.py::test_http_exception_default_handler_preserves_status_detail_and_headers | upstream | integration | Error Semantics | covered | public rewrite of tests/test_exceptions.py::test_with_headers |
| filter/rewritten_upstream_tests.py::test_custom_status_exception_handler_is_used | upstream | integration | Error Semantics | covered | public rewrite of tests/test_exceptions.py::test_not_acceptable |
| filter/rewritten_upstream_tests.py::test_unhandled_error_uses_registered_500_handler | upstream | integration | Error Semantics | covered | public rewrite of tests/test_applications.py::test_500 |
| filter/rewritten_upstream_tests.py::test_request_missing_session_auth_and_user_raise_assertion | upstream | atomic | Error Semantics | covered | public rewrite of tests/test_applications.py::test_400 |
| filter/rewritten_upstream_tests.py::test_cross_view_response_matches_raw_asgi_and_client | upstream | system_e2e | Product State Model; Cross-View Invariants | covered | public rewrite of tests/test_responses.py::test_populate_headers |
| filter/rewritten_upstream_tests.py::test_cross_view_route_parameter_matches_reverse_generation | upstream | system_e2e | Product State Model; Cross-View Invariants | covered | public rewrite of tests/test_routing.py::test_url_for |
| filter/rewritten_upstream_tests.py::test_cross_view_lifespan_state_visible_to_http_and_websocket | upstream | system_e2e | Product State Model; Cross-View Invariants | covered | public rewrite of tests/test_applications.py::test_websocket_state |
| filter/rewritten_upstream_tests.py::test_cross_view_static_reverse_url_serves_same_file | upstream | system_e2e | Cross-View Invariants | covered | public rewrite of tests/test_routing.py::test_reverse_mount_urls |
| filter/rewritten_upstream_tests.py::test_cross_view_middleware_header_visible_to_client_and_raw_asgi | upstream | system_e2e | Cross-View Invariants | covered | public rewrite of tests/middleware/test_base.py::test_custom_middleware |
| filter/rewritten_upstream_tests.py::test_workflow_route_middleware_and_reverse_url | upstream | system_e2e | Representative Workflow | covered | public rewrite of tests/test_applications.py::test_url_path_for |
| filter/rewritten_upstream_tests.py::test_workflow_lifespan_http_and_websocket_share_state | upstream | system_e2e | Representative Workflow | covered | public rewrite of tests/test_applications.py::test_app_async_gen_lifespan |
| filter/rewritten_upstream_tests.py::test_workflow_file_mount_link_and_conditional_fetch | upstream | system_e2e | Representative Workflow | covered | public rewrite of tests/test_staticfiles.py::test_staticfiles_200_with_etag_mismatch |

Total: 64 | kept (covered): 64 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 64
Layers: atomic=22 | integration=31 | system_e2e=11
