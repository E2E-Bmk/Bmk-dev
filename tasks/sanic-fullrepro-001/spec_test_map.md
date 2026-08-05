# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_config_env_casts_basic_types` | atomic | config loading and conversion | covered |
| 2 | `oracle/test_atomic.py::test_config_custom_env_prefix` | atomic | config loading and conversion | covered |
| 3 | `oracle/test_atomic.py::test_config_env_prefix_none_disables_autoload` | atomic | config loading and conversion | covered |
| 4 | `oracle/test_atomic.py::test_config_loads_uppercase_from_mapping_and_instance` | atomic | config loading and conversion | covered |
| 5 | `oracle/test_atomic.py::test_config_loads_uppercase_from_file` | atomic | config loading and conversion | covered |
| 6 | `oracle/test_atomic.py::test_config_register_type_casts_custom_value` | atomic | config loading and conversion | covered |
| 7 | `oracle/test_atomic.py::test_config_detailed_converter_uses_defaults` | atomic | config loading and conversion | covered |
| 8 | `oracle/test_atomic.py::test_config_update_config_only_keeps_uppercase_and_setters` | atomic | config loading and conversion | covered |
| 9 | `oracle/test_atomic.py::test_request_json_body_args_token_and_path` | atomic | request helpers | covered |
| 10 | `oracle/test_atomic.py::test_request_form_fields_and_file_upload` | atomic | request helpers | covered |
| 11 | `oracle/test_atomic.py::test_request_raw_body_and_headers` | atomic | request helpers | covered |
| 12 | `oracle/test_atomic.py::test_request_query_lists_and_path_parameters` | atomic | request helpers | covered |
| 13 | `oracle/test_atomic.py::test_request_ip_method_and_safe_flags` | atomic | request helpers | covered |
| 14 | `oracle/test_atomic.py::test_response_text_html_json_raw_helpers` | atomic | response helpers | covered |
| 15 | `oracle/test_atomic.py::test_response_empty_and_redirect_helpers` | atomic | response helpers | covered |
| 16 | `oracle/test_atomic.py::test_response_json_mutators_update_array_and_object` | atomic | response helpers | covered |
| 17 | `oracle/test_atomic.py::test_response_file_helper_reads_local_path` | atomic | response helpers | covered |
| 18 | `oracle/test_atomic.py::test_response_add_and_delete_cookie_headers` | atomic | response helpers | covered |
| 19 | `oracle/test_atomic.py::test_route_get_post_and_method_not_allowed` | atomic | routing and url_for | covered |
| 20 | `oracle/test_atomic.py::test_blueprint_route_prefix_and_name_lookup` | atomic | routing and url_for | covered |
| 21 | `oracle/test_atomic.py::test_blueprint_group_merges_prefixes_and_name_prefix` | atomic | routing and url_for | covered |
| 22 | `oracle/test_atomic.py::test_url_for_builds_query_and_anchor_paths` | atomic | routing and url_for | covered |
| 23 | `oracle/test_atomic.py::test_url_for_builds_static_filename_path` | atomic | routing and url_for | covered |
| 24 | `oracle/test_atomic.py::test_static_serves_file_with_content_type` | atomic | static serving | covered |
| 25 | `oracle/test_atomic.py::test_static_directory_serves_multiple_files` | atomic | static serving | covered |
| 26 | `oracle/test_atomic.py::test_request_and_response_middleware_run_in_order` | atomic | request helpers | covered |
| 27 | `oracle/test_atomic.py::test_request_middleware_can_short_circuit_with_response` | atomic | request helpers | covered |
| 28 | `oracle/test_atomic.py::test_listener_hooks_run_around_asgi_request` | atomic | middleware and listeners | covered |
| 29 | `oracle/test_atomic.py::test_blueprint_middleware_modifies_headers` | atomic | routing and url_for | covered |
| 30 | `oracle/test_atomic.py::test_multiple_middleware_priorities_affect_order` | atomic | middleware and listeners | covered |
| 31 | `oracle/test_integration.py::test_config_file_load_and_route_reads_setting` | integration | multi-operation workflow | covered |
| 32 | `oracle/test_integration.py::test_env_config_and_detailed_converter_drive_handler_response` | integration | multi-operation workflow | covered |
| 33 | `oracle/test_integration.py::test_blueprint_group_route_names_and_asgi_client_calls` | integration | multi-operation workflow | covered |
| 34 | `oracle/test_integration.py::test_static_file_url_for_and_content_round_trip` | integration | multi-operation workflow | covered |
| 35 | `oracle/test_integration.py::test_request_and_response_helpers_work_together` | integration | multi-operation workflow | covered |
| 36 | `oracle/test_integration.py::test_form_upload_and_response_cookie_workflow` | integration | multi-operation workflow | covered |
| 37 | `oracle/test_integration.py::test_middleware_gate_and_header_workflow` | integration | multi-operation workflow | covered |
| 38 | `oracle/test_integration.py::test_listener_and_middleware_order_with_multiple_requests` | integration | multi-operation workflow | covered |
| 39 | `oracle/test_integration.py::test_blueprint_middleware_applies_to_blueprint_route_only` | integration | multi-operation workflow | covered |
| 40 | `oracle/test_integration.py::test_url_for_query_blueprint_and_static_paths_from_one_app` | integration | multi-operation workflow | covered |
| 41 | `oracle/test_integration.py::test_config_custom_converter_and_handler_json_workflow` | integration | multi-operation workflow | covered |
| 42 | `oracle/test_integration.py::test_config_file_and_instance_merge_before_request` | integration | multi-operation workflow | covered |
| 43 | `oracle/test_integration.py::test_response_json_mutation_survives_handler_round_trip` | integration | multi-operation workflow | covered |
| 44 | `oracle/test_integration.py::test_empty_and_redirect_endpoints_share_route_table` | integration | multi-operation workflow | covered |
| 45 | `oracle/test_integration.py::test_static_directory_serves_multiple_entries_by_url_for` | integration | multi-operation workflow | covered |
| 46 | `oracle/test_integration.py::test_request_fields_and_raw_body_available_in_handler` | integration | multi-operation workflow | covered |
| 47 | `oracle/test_integration.py::test_blueprint_route_and_request_url_for_projection` | integration | multi-operation workflow | covered |
| 48 | `oracle/test_integration.py::test_file_response_can_set_cookie_header` | integration | multi-operation workflow | covered |
| 49 | `oracle/test_integration.py::test_multiple_routes_use_shared_config_and_request_context` | integration | multi-operation workflow | covered |
| 50 | `oracle/test_integration.py::test_nested_blueprint_and_static_routes_coexist` | integration | multi-operation workflow | covered |
| 51 | `oracle/test_integration.py::test_cookie_response_and_followup_request_round_trip` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_dynamic_route_url_generation_and_match_info_agree` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_accept_and_content_type_drive_handler_representation` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_basic_credentials_and_route_name_project_into_response` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_exception_handler_projects_public_error_response` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_query_args_keep_blank_values_and_order_in_handler` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_patch_and_delete_named_routes_share_url_projection` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_blueprint_route_reads_app_config_and_request_context` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_html_and_raw_endpoints_preserve_semantic_response_fields` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_typed_route_projects_method_flags_and_uri_template` | integration | Cross-View Invariants | covered |

final_scoreable: 60
