# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_application_preserves_custom_settings` | atomic | Application And Request Handling | covered |
| 2 | `oracle/test_atomic.py::test_application_reverse_url_uses_named_urlspec` | atomic | Application And Request Handling | covered |
| 3 | `oracle/test_atomic.py::test_application_reverse_url_escapes_string_arguments` | atomic | Application And Request Handling | covered |
| 4 | `oracle/test_atomic.py::test_path_matches_returns_positional_groups` | atomic | Routing | covered |
| 5 | `oracle/test_atomic.py::test_path_matches_returns_named_groups` | atomic | Routing | covered |
| 6 | `oracle/test_atomic.py::test_path_matches_reverse_escapes_arguments` | atomic | Application And Request Handling | covered |
| 7 | `oracle/test_atomic.py::test_host_matches_accepts_matching_host` | atomic | Application And Request Handling | covered |
| 8 | `oracle/test_atomic.py::test_reversible_rule_router_reverses_named_rule` | atomic | Application And Request Handling | covered |
| 9 | `oracle/test_atomic.py::test_rule_router_add_rules_accepts_string_path_matcher` | atomic | Application And Request Handling | covered |
| 10 | `oracle/test_atomic.py::test_template_generate_substitutes_values` | atomic | Application And Request Handling | covered |
| 11 | `oracle/test_atomic.py::test_template_autoescape_escapes_html` | atomic | Application And Request Handling | covered |
| 12 | `oracle/test_atomic.py::test_template_comment_is_omitted_from_output` | atomic | Options | covered |
| 13 | `oracle/test_atomic.py::test_dict_loader_include_uses_named_template` | atomic | Application And Request Handling | covered |
| 14 | `oracle/test_atomic.py::test_dict_loader_extends_base_template_block` | atomic | Application And Request Handling | covered |
| 15 | `oracle/test_atomic.py::test_template_apply_block_uses_callable` | atomic | Application And Request Handling | covered |
| 16 | `oracle/test_atomic.py::test_template_parse_error_is_public_exception` | atomic | Application And Request Handling | covered |
| 17 | `oracle/test_atomic.py::test_option_parser_command_line_updates_defined_values` | atomic | Application And Request Handling | covered |
| 18 | `oracle/test_atomic.py::test_option_parser_returns_remainder_when_final_false` | atomic | Application And Request Handling | covered |
| 19 | `oracle/test_atomic.py::test_option_parser_config_file_updates_defined_values` | atomic | Options | covered |
| 20 | `oracle/test_atomic.py::test_option_parser_multiple_int_range_expands_values` | atomic | Application And Request Handling | covered |
| 21 | `oracle/test_atomic.py::test_option_parser_groups_and_group_dict_expose_named_group` | atomic | Routing | covered |
| 22 | `oracle/test_atomic.py::test_option_parser_as_dict_and_items_reflect_current_values` | atomic | Application And Request Handling | covered |
| 23 | `oracle/test_atomic.py::test_option_parser_parse_callback_runs_on_final_parse` | atomic | Options | covered |
| 24 | `oracle/test_atomic.py::test_option_parser_rejects_unknown_option` | atomic | Application And Request Handling | covered |
| 25 | `oracle/test_atomic.py::test_request_handler_set_status_and_get_status` | atomic | Application And Request Handling | covered |
| 26 | `oracle/test_atomic.py::test_request_handler_set_header_overwrites_value` | atomic | Application And Request Handling | covered |
| 27 | `oracle/test_atomic.py::test_request_handler_add_header_preserves_multiple_values` | atomic | Application And Request Handling | covered |
| 28 | `oracle/test_atomic.py::test_request_handler_clear_header_removes_value` | atomic | Application And Request Handling | covered |
| 29 | `oracle/test_atomic.py::test_request_handler_get_query_arguments_return_strings` | atomic | Application And Request Handling | covered |
| 30 | `oracle/test_atomic.py::test_request_handler_body_arguments_parse_form_values` | atomic | Application And Request Handling | covered |
| 31 | `oracle/test_atomic.py::test_request_handler_missing_required_argument_raises_public_error` | atomic | Application And Request Handling | covered |
| 32 | `oracle/test_atomic.py::test_request_handler_get_cookie_reads_request_cookie` | atomic | Application And Request Handling | covered |
| 33 | `oracle/test_atomic.py::test_request_handler_signed_cookie_round_trips_value` | atomic | Cookies And Headers | covered |
| 34 | `oracle/test_atomic.py::test_request_handler_signed_cookie_key_version_is_visible` | atomic | Cookies And Headers | covered |
| 35 | `oracle/test_atomic.py::test_request_handler_reverse_url_uses_application_routes` | atomic | Application And Request Handling | covered |
| 36 | `oracle/test_atomic.py::test_request_handler_static_url_includes_version_parameter` | atomic | Application And Request Handling | covered |
| 37 | `oracle/test_atomic.py::test_request_handler_static_url_can_omit_version_parameter` | atomic | Options | covered |
| 38 | `oracle/test_atomic.py::test_request_handler_static_url_can_include_host` | atomic | Application And Request Handling | covered |
| 39 | `oracle/test_atomic.py::test_request_handler_render_string_uses_template_loader` | atomic | Application And Request Handling | covered |
| 40 | `oracle/test_atomic.py::test_request_handler_template_namespace_contains_public_helpers` | atomic | Application And Request Handling | covered |
| 41 | `oracle/test_atomic.py::test_request_handler_header_datetime_value_is_http_date` | atomic | Application And Request Handling | covered |
| 42 | `oracle/test_integration.py::test_http_query_and_body_arguments_are_projected_as_json` | integration | Application And Request Handling | covered |
| 43 | `oracle/test_integration.py::test_http_cookie_set_then_read_round_trip` | integration | Application And Request Handling | covered |
| 44 | `oracle/test_integration.py::test_http_signed_cookie_set_then_read_round_trip` | integration | Cookies And Headers | covered |
| 45 | `oracle/test_integration.py::test_http_signed_cookie_key_version_survives_second_request` | integration | Cookies And Headers | covered |
| 46 | `oracle/test_integration.py::test_http_header_workflow_projects_overwrite_add_and_clear` | integration | Application And Request Handling | covered |
| 47 | `oracle/test_integration.py::test_http_named_route_reversed_inside_handler_can_be_fetched` | integration | Application And Request Handling | covered |
| 48 | `oracle/test_integration.py::test_http_static_url_from_handler_fetches_versioned_asset` | integration | Application And Request Handling | covered |
| 49 | `oracle/test_integration.py::test_http_static_url_without_version_fetches_asset` | integration | Application And Request Handling | covered |
| 50 | `oracle/test_integration.py::test_http_template_render_uses_loader_arguments_and_reverse_url` | integration | Application And Request Handling | covered |
| 51 | `oracle/test_integration.py::test_http_asset_template_uses_static_url_and_static_handler` | integration | Application And Request Handling | covered |
| 52 | `oracle/test_integration.py::test_http_prepare_get_finish_lifecycle_records_public_order` | integration | Application And Request Handling | covered |
| 53 | `oracle/test_integration.py::test_http_initialize_kwargs_are_visible_to_handler_method` | integration | Application And Request Handling | covered |
| 54 | `oracle/test_integration.py::test_http_default_handler_class_handles_missing_route` | integration | Options | covered |
| 55 | `oracle/test_integration.py::test_http_redirect_handler_preserves_query_on_location` | integration | Application And Request Handling | covered |
| 56 | `oracle/test_integration.py::test_http_named_path_argument_is_decoded_before_handler_get` | integration | Application And Request Handling | covered |
| 57 | `oracle/test_integration.py::test_http_positional_path_argument_is_decoded_before_handler_get` | integration | Application And Request Handling | covered |
| 58 | `oracle/test_integration.py::test_http_option_parser_values_can_drive_application_settings` | integration | Application And Request Handling | covered |
| 59 | `oracle/test_integration.py::test_http_current_user_from_cookie_reaches_template_namespace` | integration | Application And Request Handling | covered |
| 60 | `oracle/test_integration.py::test_http_write_dict_sets_json_response_projection` | integration | Application And Request Handling | covered |
| 61 | `oracle/test_integration.py::test_http_static_file_get_and_head_share_content_headers` | integration | Application And Request Handling | covered |
| 62 | `oracle/test_integration.py::test_http_clear_cookie_sets_empty_cookie_response` | integration | Application And Request Handling | covered |
| 63 | `oracle/test_integration.py::test_http_template_include_and_extends_share_loader_context` | integration | Cross-View Invariants | covered |
| 64 | `oracle/test_integration.py::test_http_config_file_option_reaches_application_setting` | integration | Cross-View Invariants | covered |
| 65 | `oracle/test_integration.py::test_http_tampered_signed_cookie_is_rejected` | integration | Cross-View Invariants | covered |
| 66 | `oracle/test_integration.py::test_http_set_clear_and_read_cookie_workflow` | integration | Cross-View Invariants | covered |

final_scoreable: 66
