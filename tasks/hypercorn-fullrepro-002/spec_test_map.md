# Hypercorn Spec-Test Map

oracle_version: 2026-07-20-native-v1
spec_version: v1
filter/oracle_source: mixed_upstream_rewritten_and_generated
scorer_isolation: task-local native tests with candidate solution first on PYTHONPATH

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_integration.py::test_config_from_pyfile_loads_public_attributes | upstream_rewrite | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_config_from_toml_loads_public_attributes | upstream_rewrite | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_config_from_object_loads_public_attributes | upstream_rewrite | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_config_response_headers_follow_metadata_flags | upstream_rewrite | atomic | Response Metadata and Metrics | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_http_to_https_redirect_preserves_http_raw_path_and_query[/abc] | upstream_rewrite | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_http_to_https_redirect_preserves_http_raw_path_and_query[/abc%3C] | upstream_rewrite | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_http_to_https_redirect_preserves_websocket_raw_path_and_query[/abc] | upstream_rewrite | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_http_to_https_redirect_preserves_websocket_raw_path_and_query[/abc%3C] | upstream_rewrite | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_http_to_https_redirect_uses_https_scheme_for_http2_websocket | upstream_rewrite | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_http_to_https_redirect_closes_websocket_without_denial_extension | upstream_rewrite | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_http_to_https_redirect_uses_request_host_when_constructor_host_is_none | upstream_rewrite | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_proxy_fix_legacy_restores_trusted_client_scheme_and_host | upstream_rewrite | integration | Restoring Proxy Information | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_proxy_fix_modern_restores_trusted_client_scheme_and_host | upstream_rewrite | integration | Restoring Proxy Information | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_dispatcher_routes_by_insertion_order_and_updates_root_path | upstream_rewrite | integration | Dispatching Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_dispatcher_returns_404_when_no_mount_matches | upstream_rewrite | integration | Dispatching Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_dispatcher_broadcasts_lifespan_to_mounted_applications | upstream_rewrite | integration | Dispatching Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_asyncio_wsgi_middleware_emits_wsgi_response_body | upstream_rewrite | integration | Adapting WSGI Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_asyncio_wsgi_middleware_returns_400_when_body_exceeds_limit | upstream_rewrite | integration | Adapting WSGI Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_asyncio_wsgi_middleware_requires_start_response_before_body | upstream_rewrite | integration | Adapting WSGI Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_integration.py::test_trio_wsgi_middleware_emits_wsgi_response_body | upstream_rewrite | integration | Adapting WSGI Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_documented_defaults_are_visible | generated | atomic | Documented Defaults | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_bind_groups_accept_single_string_assignments | generated | atomic | Binds and TLS | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_root_path_assignment_removes_trailing_slashes | generated | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_from_mapping_applies_keyword_arguments_last | generated | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_from_mapping_accepts_keyword_only_configuration | generated | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_from_object_resolves_dotted_object | generated | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_from_pyfile_propagates_missing_file | generated | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_from_pyfile_propagates_execution_failure | generated | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_from_toml_propagates_parse_failure | generated | atomic | Creating and Loading Configuration | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_ssl_enabled_reflects_certificate_and_key_presence | generated | atomic | Binds and TLS | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_response_headers_include_each_alt_svc_value | generated | atomic | Response Metadata and Metrics | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_statsd_logger_class_requires_statsd_host | generated | atomic | Response Metadata and Metrics | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_config_statsd_logger_class_replaces_default_when_statsd_is_enabled | generated | atomic | Response Metadata and Metrics | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_redirect_without_constructor_or_request_host_raises_value_error | generated | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_redirect_location_includes_root_path_before_raw_path | generated | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_redirect_passes_secure_websocket_to_wrapped_application | generated | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_redirect_passes_non_http_scope_without_requiring_host | generated | integration | Redirecting HTTP to HTTPS | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_proxy_fix_without_forwarded_headers_preserves_scope_values | generated | integration | Restoring Proxy Information | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_proxy_fix_trusted_hops_selects_value_from_the_right | generated | integration | Restoring Proxy Information | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_proxy_fix_modern_mode_falls_back_to_legacy_headers | generated | integration | Restoring Proxy Information | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_proxy_fix_non_http_scope_is_passed_without_copying | generated | integration | Restoring Proxy Information | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_dispatcher_uses_first_matching_mount_even_when_later_mount_is_longer | generated | integration | Dispatching Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_dispatcher_extends_existing_root_path_for_selected_mount | generated | integration | Dispatching Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_wsgi_environment_contains_root_path_path_info_query_and_headers | generated | integration | Adapting WSGI Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_wsgi_path_outside_root_path_returns_404_without_calling_app | generated | integration | Adapting WSGI Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_wsgi_websocket_scope_closes_without_calling_wsgi_app | generated | integration | Adapting WSGI Applications | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_logger_access_logfile_dash_writes_configured_access_record_to_stdout | generated | atomic | Logging | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_logger_missing_access_atom_renders_dash | generated | atomic | Logging | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_logger_errorlog_dash_writes_error_and_warning_to_stderr | generated | atomic | Logging | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_asyncio_serve_warns_when_process_or_loop_settings_do_not_apply | generated | integration | Programmatic Service | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_hypercorn_module_help_exposes_command_line_interface | generated | system_e2e | Command-Line Service | covered | public observable assertion; reference and dummy gated |
| oracle/test_atomic.py::test_hypercorn_module_rejects_unknown_verify_mode | generated | system_e2e | Command-Line Service | covered | public observable assertion; reference and dummy gated |

Total: 52 | upstream_rewrite: 20 | generated: 32 | final_scoreable: 52
