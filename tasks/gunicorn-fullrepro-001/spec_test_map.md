# Gunicorn Spec-Test Map

| oracle_nodeid | source_type | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `oracle/test_atomic.py::test_config_known_settings_are_available_and_validated` | upstream_rewrite | atomic | Configuration objects and logging | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_config_boolean_and_callable_validation` | upstream_rewrite | atomic | Configuration objects and logging | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_config_forwarded_allow_ips_parsing_and_rejection` | upstream_rewrite | atomic | Principal settings | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_base_application_wsgi_callable_is_cached` | upstream_rewrite | atomic | Application targets and runners | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_wsgi_application_direct_cli_target_wins_over_config_wsgi_app` | upstream_rewrite | integration | Sources and precedence | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_wsgi_application_uses_config_wsgi_app_when_cli_target_is_absent` | upstream_rewrite | integration | Application targets and runners | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_wsgi_application_requires_an_application_target` | upstream_rewrite | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_cli_arguments_override_gunicorn_cmd_args` | upstream_rewrite | integration | Sources and precedence | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_direct_cli_config_file_wins_over_env_config_file` | upstream_rewrite | integration | Sources and precedence | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_configuration_values_and_validation` | upstream_rewrite | atomic | Application lifecycle and allocation | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_hook_settings_accept_matching_callables_and_reject_invalid_arity` | upstream_rewrite | atomic | Principal settings | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_app_dispatches_public_actions_and_persists_instance_state` | upstream_rewrite | atomic | Application lifecycle and allocation | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_app_rejects_missing_and_underscore_prefixed_actions` | upstream_rewrite | atomic | Application lifecycle and allocation | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_app_worker_limit_attribute_is_inherited_or_overridden` | upstream_rewrite | atomic | Application lifecycle and allocation | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_client_execute_reports_connection_failure` | upstream_rewrite | atomic | Clients and execution | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_client_getter_uses_thread_local_client_and_close_resets` | upstream_rewrite | integration | Clients and execution | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_client_getter_is_thread_local` | upstream_rewrite | integration | Clients and execution | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_client_getter_requires_socket_configuration` | upstream_rewrite | atomic | Clients and execution | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_async_dirty_client_getter_reuses_context_client_and_close_is_idempotent` | upstream_rewrite | integration | Clients and execution | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_dirty_no_workers_error_preserves_app_path_and_base_type` | upstream_rewrite | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_stash_errors_preserve_table_and_key_details` | upstream_rewrite | atomic | Stash tables | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_control_client_send_command_reports_missing_socket` | upstream_rewrite | atomic | Control client | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_control_client_context_manager_reports_connection_failure` | upstream_rewrite | atomic | Control client | covered | public observable assertion; reference and dummy gated |
| `oracle/test_atomic.py::test_control_client_close_is_idempotent` | upstream_rewrite | atomic | Control client | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_version_info_matches_public_version_string` | generated | atomic | Installable Surface | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_http2_capability_reports_installed_h2_version` | generated | atomic | HTTP/2 capability queries | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_config_principal_defaults_are_visible` | generated | atomic | Principal settings | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_config_accepts_public_protocol_selection` | generated | atomic | Principal settings | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_config_control_socket_disable_uses_boolean_validation` | generated | atomic | Principal settings | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_config_dirty_and_runtime_timeouts_accept_zero_as_documented_disable` | generated | atomic | Principal settings | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_config_request_limit_settings_reject_negative_values` | generated | atomic | Request and Protocol Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_config_reload_and_capture_output_use_boolean_validation` | generated | atomic | Principal settings | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_loads_default_application_name` | generated | atomic | Application targets and runners | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_loads_named_callable` | generated | atomic | Application targets and runners | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_invokes_factory_with_literal_arguments` | generated | atomic | Application targets and runners | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_rejects_missing_callable` | generated | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_rejects_non_callable_result` | generated | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_rejects_non_literal_factory_argument` | generated | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_rejects_malformed_target_expression` | generated | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_application_rejects_non_simple_factory_reference` | generated | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_dirty_error_subclasses_preserve_base_type` | generated | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_dirty_app_not_found_error_is_catchable_as_dirty_error` | generated | atomic | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_control_client_error_is_raised_for_send_to_missing_socket` | generated | atomic | Control client | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_python_module_help_exits_successfully` | generated | system_e2e | Installable Surface | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgiapp_module_help_exits_successfully` | generated | system_e2e | Installable Surface | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_check_config_accepts_valid_wsgi_application` | generated | system_e2e | Sources and precedence | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_check_config_rejects_missing_application_target` | generated | system_e2e | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_check_config_rejects_invalid_setting_value` | generated | system_e2e | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_check_config_rejects_missing_explicit_config_file` | generated | system_e2e | Sources and precedence | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_check_config_ignores_unknown_python_config_names` | generated | system_e2e | Sources and precedence | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_print_config_reports_direct_cli_precedence_over_environment_args` | generated | system_e2e | Sources and precedence | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_server_returns_application_body` | generated | system_e2e | Request and Protocol Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_server_exposes_path_query_and_scheme` | generated | system_e2e | Request and Protocol Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_server_exposes_method_headers_and_body_length` | generated | system_e2e | Cross-View Invariants | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_server_ignores_forwarded_scheme_from_untrusted_peer` | generated | system_e2e | Cross-View Invariants | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_server_reports_application_exception_as_server_error` | generated | system_e2e | Error Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_wsgi_server_closes_returned_iterable` | generated | system_e2e | Request and Protocol Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_control_socket_show_config_reports_runtime_projection` | generated | system_e2e | Configured WSGI server with runtime inspection | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_control_socket_disable_prevents_socket_creation` | generated | system_e2e | Runtime and Control Semantics | covered | public observable assertion; reference and dummy gated |
| `oracle/test_integration.py::test_repeated_wsgi_requests_observe_same_running_service` | generated | system_e2e | Product State Model | covered | public observable assertion; reference and dummy gated |

Total: 60 | upstream_rewrite: 24 | generated: 36 | final_scoreable: 60
