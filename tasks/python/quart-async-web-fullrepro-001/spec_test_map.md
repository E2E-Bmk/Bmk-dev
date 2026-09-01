# Quart Oracle Coverage Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_integration.py::test_index[/-GET] | integration | Application and registration | covered | Registers an async route and dispatches it through the bound client. |
| oracle/test_integration.py::test_index[/sync-GET] | integration | Application and registration | covered | Registers a synchronous route and dispatches it through the bound client. |
| oracle/test_integration.py::test_iri | integration | HTTP requests and responses | covered | Client GET exposes the route handler's text response body. |
| oracle/test_integration.py::test_json | integration | HTTP requests and responses | covered | JSON request body is read by the handler and returned as JSON. |
| oracle/test_integration.py::test_implicit_json | integration | HTTP requests and responses | covered | A dict handler result converts to a JSON response. |
| oracle/test_integration.py::test_implicit_json_list | integration | HTTP requests and responses | covered | A list handler result converts to a JSON response. |
| oracle/test_integration.py::test_not_found_error | integration | Error Semantics | covered | An absent HTTP rule returns 404. |
| oracle/test_atomic.py::test_make_response_str | atomic | HTTP requests and responses | covered | `make_response` converts text and applies documented tuple status and headers. |
| oracle/test_atomic.py::test_make_response_response | atomic | HTTP requests and responses | covered | `make_response` retains a Response body and applies tuple headers/status. |
| oracle/test_atomic.py::test_make_response_errors | atomic | Error Semantics | covered | Invalid response values and tuple length raise TypeError. |
| oracle/test_integration.py::test_websocket | system_e2e | Cross-View Invariants | covered | A binary test-client frame reaches the handler and returns with its bytes kind preserved. |
| oracle/test_integration.py::test_websocket_abort | integration | Error Semantics | covered | Pre-accept `abort(401)` raises WebsocketResponseError exposing status 401. |
| oracle/test_integration.py::test_stream | integration | HTTP requests and responses | covered | An async generator handler result becomes a concatenated response body. |
| oracle/test_integration.py::test_has_request_context | integration | Context, sessions, and messages | covered | Request and app context predicates are true only inside the request context. |
| oracle/test_atomic.py::test_has_app_context | atomic | Context, sessions, and messages | covered | The app-context predicate is true only while the app context is active. |
| oracle/test_integration.py::test_copy_current_app_context | integration | Context, sessions, and messages | covered | A copied app context retains access to `g` in a created task. |
| oracle/test_integration.py::test_copy_current_request_context | integration | Context, sessions, and messages | covered | A copied request context retains the request path in a created task. |
| oracle/test_integration.py::test_copy_current_websocket_context | integration | Context, sessions, and messages | covered | A copied WebSocket context retains documented request headers in a created task. |
| oracle/test_atomic.py::test_template_render | atomic | Templates and streamed context | covered | Rendering a template string uses explicitly supplied context. |
| oracle/test_integration.py::test_default_template_context | integration | Cross-View Invariants | covered | Templates see the active request, session, and `g` projections. |
| oracle/test_integration.py::test_simple_stream | integration | Templates and streamed context | covered | A streamed template produces its rendered response text. |
| oracle/test_integration.py::test_methods | integration | HTTP requests and responses | covered | Bound client convenience methods dispatch their corresponding HTTP methods. |
| oracle/test_integration.py::test_testing_json | integration | HTTP requests and responses | covered | Client JSON submission and response JSON decoding round-trip. |
| oracle/test_integration.py::test_data | integration | HTTP requests and responses | covered | Request bytes are available to the handler and response bytes to the client. |
| oracle/test_integration.py::test_query_string | integration | HTTP requests and responses | covered | A mapping supplied as `query_string` is observed by the active handler through `request.args`, exactly as the v3 HTTP contract requires. |
| oracle/test_integration.py::test_cookie_jar | integration | Cross-View Invariants | covered | A cookie-preserving client observes a session value on its next request. |
| oracle/test_integration.py::test_websocket_bad_request | integration | Error Semantics | covered | An HTTP WebSocket rejection raises WebsocketResponseError with its public status/body. |
| oracle/test_integration.py::test_websocket_json | system_e2e | WebSockets | covered | Test-client JSON send/receive mirrors the WebSocket JSON message behavior. |
| oracle/test_atomic.py::test_unmatched_http_rule_returns_404 | atomic | Error Semantics | covered | An unmatched client HTTP request returns 404. |
| oracle/test_integration.py::test_disallowed_http_method_returns_405 | integration | Error Semantics | covered | A method not accepted by a matching rule returns 405. |
| oracle/test_integration.py::test_int_converter_rejects_non_integer_path_text | integration | Error Semantics | covered | An int converter rejecting non-integer path text returns 404. |
| oracle/test_integration.py::test_path_converter_accepts_slashes | integration | Routing and URL generation | covered | The path converter passes slash-containing text to the handler. |
| oracle/test_integration.py::test_default_string_converter_does_not_accept_slashes | integration | Routing and URL generation | covered | The default string converter does not match a slash. |
| oracle/test_integration.py::test_string_handler_result_becomes_text_response | integration | HTTP requests and responses | covered | A string handler result becomes the client-visible text body. |
| oracle/test_integration.py::test_dict_handler_result_becomes_json_response | integration | HTTP requests and responses | covered | A dict handler result becomes a client-visible JSON response. |
| oracle/test_integration.py::test_list_handler_result_becomes_json_response | integration | HTTP requests and responses | covered | A list handler result becomes a client-visible JSON response. |
| oracle/test_integration.py::test_tuple_response_applies_status_and_headers | integration | HTTP requests and responses | covered | A three-item response tuple applies text, status, and headers. |
| oracle/test_atomic.py::test_jsonify_returns_json_response | atomic | HTTP requests and responses | covered | `jsonify` returns a Response whose JSON value can be read publicly. |
| oracle/test_atomic.py::test_make_response_rejects_none_value | atomic | Error Semantics | covered | `make_response(None)` raises TypeError. |
| oracle/test_atomic.py::test_make_response_rejects_invalid_length_tuple | atomic | Error Semantics | covered | An invalid-length response tuple raises TypeError. |
| oracle/test_integration.py::test_request_get_data_returns_text_when_requested | integration | HTTP requests and responses | covered | `request.get_data(as_text=True)` exposes submitted bytes as text. |
| oracle/test_integration.py::test_request_cache_false_drains_subsequent_body_access | integration | HTTP requests and responses | covered | A cache-false body read drains later body access. |
| oracle/test_integration.py::test_request_non_json_body_returns_none_without_force | integration | HTTP requests and responses | covered | Non-JSON request data returns None without `force=True`. |
| oracle/test_integration.py::test_request_malformed_json_returns_none_when_silent | integration | HTTP requests and responses | covered | Malformed JSON returns None when `silent=True`. |
| oracle/test_integration.py::test_url_for_honors_external_scheme_and_anchor | integration | Routing and URL generation | covered | With `_external=True` and `SERVER_NAME="example.test"`, `url_for` uses that authority; `_scheme` and `_anchor` select the documented external scheme and fragment. |
| oracle/test_integration.py::test_url_for_missing_required_value_raises | integration | Error Semantics | covered | `url_for` raises when a required route variable is absent. |
| oracle/test_integration.py::test_blueprint_registration_exposes_handler_and_qualified_url | system_e2e | Application and registration | covered | Blueprint registration exposes its handler and blueprint-qualified relative URL. |
| oracle/test_atomic.py::test_app_context_exposes_current_app_and_g | atomic | Context, sessions, and messages | covered | App context exposes `current_app` and `g` while active. |
| oracle/test_atomic.py::test_request_context_exposes_request_and_ends_cleanly | atomic | Context, sessions, and messages | covered | Request context exposes method/path and the proxy raises after exit. |
| oracle/test_integration.py::test_cookie_preserving_client_keeps_session_across_requests | system_e2e | Cross-View Invariants | covered | A session value written in one HTTP handler is visible in a later handler. |
| oracle/test_integration.py::test_session_write_without_secret_key_is_error_response | integration | Error Semantics | covered | A session update without a persistent secret-key configuration is an error response. |
| oracle/test_integration.py::test_flash_messages_are_consumed_by_a_later_request | system_e2e | Context, sessions, and messages | covered | Flash messages are stored in session then consumed by a later request. |
| oracle/test_integration.py::test_template_receives_request_g_and_config_values | system_e2e | Templates and streamed context | covered | A request template receives its documented request, `g`, and configuration context values. |
| oracle/test_integration.py::test_stream_with_context_keeps_request_available_during_iteration | integration | Cross-View Invariants | covered | A context-preserving stream reads the creating request while iterated. |
| oracle/test_integration.py::test_websocket_text_round_trip_preserves_text_kind | system_e2e | WebSockets | covered | Test-client text send/receive mirrors the WebSocket text message behavior. |
| oracle/test_integration.py::test_websocket_binary_round_trip_preserves_binary_kind | system_e2e | WebSockets | covered | Test-client binary send/receive mirrors the WebSocket binary message behavior. |
| oracle/test_integration.py::test_websocket_json_round_trip_decodes_json_value | system_e2e | WebSockets | covered | Test-client JSON send/receive mirrors the WebSocket JSON message behavior. |
| oracle/test_integration.py::test_websocket_abort_before_accept_returns_public_rejection_response | integration | Error Semantics | covered | Pre-accept `abort(418)` produces WebsocketResponseError with status 418. |
| oracle/test_integration.py::test_websocket_http_response_raises_websocket_response_error | integration | Error Semantics | covered | An HTTP response from a WebSocket handler raises WebsocketResponseError. |
| oracle/test_integration.py::test_representative_workflow_combines_json_routing_session_and_url_for | system_e2e | Representative Workflow | covered | The documented create/fetch workflow combines routing, JSON, session persistence, URL generation, and status. |
| oracle/test_atomic.py::test_from_prefixed_env_applies_loads_to_prefixed_values | atomic | Configuration | covered | `from_prefixed_env` selects names with the requested prefix, drops that prefix for the key, and applies its public `loads` function. |
| oracle/test_atomic.py::test_from_prefixed_env_keeps_original_string_when_loads_fails | atomic | Configuration | covered | `from_prefixed_env` retains the original environment string when the supplied public `loads` function raises. |
| oracle/test_atomic.py::test_from_prefixed_env_creates_nested_keys_and_ignores_other_prefixes | atomic | Configuration | covered | `from_prefixed_env` creates nested mapping keys for a double underscore and leaves values without the required prefix unchanged. |
