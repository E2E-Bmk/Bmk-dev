# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_testapp_accepts_explicit_label` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_testapp_preserves_explicit_argv` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_debug_property_follows_debug_argument` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_quiet_property_follows_quiet_argument` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_add_arg_populates_parsed_arguments` | atomic | Invocation Protocol | covered |
| 6 | `oracle/test_atomic.py::test_context_setup_exposes_core_interfaces` | atomic | Public Import Surface | covered |
| 7 | `oracle/test_atomic.py::test_context_setup_instantiates_default_handlers` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_config_defaults_are_available_through_config_interface` | atomic | Scope | covered |
| 9 | `oracle/test_atomic.py::test_config_merge_without_override_keeps_existing_value` | atomic | Cross-View Invariants | covered |
| 10 | `oracle/test_atomic.py::test_config_merge_with_override_replaces_value` | atomic | Cross-View Invariants | covered |
| 11 | `oracle/test_atomic.py::test_config_manager_exposes_sections_and_dict` | atomic | Scope | covered |
| 12 | `oracle/test_atomic.py::test_config_parse_file_returns_false_for_missing_path` | atomic | Error Semantics | covered |
| 13 | `oracle/test_atomic.py::test_config_parse_file_loads_local_ini` | atomic | Scope | covered |
| 14 | `oracle/test_atomic.py::test_interface_manager_reports_defined_and_fallback` | atomic | Scope | covered |
| 15 | `oracle/test_atomic.py::test_interface_manager_lists_core_interfaces` | atomic | Public Import Surface | covered |
| 16 | `oracle/test_atomic.py::test_custom_interface_can_be_defined_at_runtime` | atomic | Scope | covered |
| 17 | `oracle/test_atomic.py::test_handler_registered_in_app_metadata_is_visible` | atomic | Scope | covered |
| 18 | `oracle/test_atomic.py::test_handler_get_returns_registered_class` | atomic | Scope | covered |
| 19 | `oracle/test_atomic.py::test_handler_list_returns_classes_for_interface` | atomic | Scope | covered |
| 20 | `oracle/test_atomic.py::test_handler_resolve_label_creates_instance` | atomic | Cross-View Invariants | covered |
| 21 | `oracle/test_atomic.py::test_handler_resolve_class_registers_and_creates_instance` | atomic | Cross-View Invariants | covered |
| 22 | `oracle/test_atomic.py::test_handler_get_uses_fallback_for_unknown_label` | atomic | Error Semantics | covered |
| 23 | `oracle/test_atomic.py::test_handler_manager_rejects_unknown_interface` | atomic | Error Semantics | covered |
| 24 | `oracle/test_atomic.py::test_handler_force_replaces_same_label` | atomic | Scope | covered |
| 25 | `oracle/test_atomic.py::test_hook_manager_orders_registered_callbacks_by_weight` | atomic | Cross-View Invariants | covered |
| 26 | `oracle/test_atomic.py::test_hook_manager_flattens_generator_results` | atomic | Scope | covered |
| 27 | `oracle/test_atomic.py::test_hook_registration_for_unknown_name_returns_false` | atomic | Error Semantics | covered |
| 28 | `oracle/test_atomic.py::test_framework_hook_names_are_defined` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_extension_loader_expands_short_names` | atomic | Scope | covered |
| 30 | `oracle/test_atomic.py::test_extension_loader_skips_duplicate_full_names` | atomic | Cross-View Invariants | covered |
| 31 | `oracle/test_atomic.py::test_json_extension_registers_json_output_handler` | atomic | Scope | covered |
| 32 | `oracle/test_atomic.py::test_json_output_handler_returns_parseable_object` | atomic | Cross-View Invariants | covered |
| 33 | `oracle/test_atomic.py::test_print_extension_renders_only_out_field` | atomic | Scope | covered |
| 34 | `oracle/test_atomic.py::test_render_without_output_handler_returns_empty_string` | atomic | Error Semantics | covered |
| 35 | `oracle/test_atomic.py::test_last_rendered_records_data_and_text` | atomic | Cross-View Invariants | covered |
| 36 | `oracle/test_atomic.py::test_app_extend_adds_a_public_callable` | atomic | Scope | covered |
| 37 | `oracle/test_atomic.py::test_template_handler_renders_scalar_placeholders` | atomic | Scope | covered |
| 38 | `oracle/test_atomic.py::test_template_handler_loads_file_from_template_directory` | atomic | Scope | covered |
| 39 | `oracle/test_atomic.py::test_template_handler_copy_creates_local_project_file` | atomic | Representative Workflows | covered |
| 40 | `oracle/test_atomic.py::test_template_handler_rejects_missing_template` | atomic | Error Semantics | covered |
| 41 | `oracle/test_atomic.py::test_local_plugin_loads_and_reports_name` | atomic | Scope | covered |
| 42 | `oracle/test_atomic.py::test_missing_local_plugin_raises_framework_error` | atomic | Error Semantics | covered |
| 43 | `oracle/test_integration.py::test_lifecycle_hooks_span_setup_run_and_close` | integration | Product State Model | covered |
| 44 | `oracle/test_integration.py::test_config_defaults_and_argv_are_merged_into_run_state` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_config_file_can_select_json_extension_and_output` | integration | Representative Workflows | covered |
| 46 | `oracle/test_integration.py::test_config_files_apply_deterministic_sorted_directory_precedence` | integration | Scope | covered |
| 47 | `oracle/test_integration.py::test_custom_interface_handler_round_trip_through_manager` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_handler_resolution_forms_share_handler_behavior` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_handler_override_option_selects_overridable_output` | integration | Scope | covered |
| 50 | `oracle/test_integration.py::test_weighted_hook_pipeline_changes_rendered_data` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_hook_generator_and_post_render_form_one_pipeline` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_base_controller_dispatches_command_arguments` | integration | Scope | covered |
| 53 | `oracle/test_integration.py::test_controller_command_alias_dispatches_same_function` | integration | Scope | covered |
| 54 | `oracle/test_integration.py::test_nested_controller_dispatches_subcommand` | integration | Scope | covered |
| 55 | `oracle/test_integration.py::test_embedded_controller_shares_base_namespace` | integration | Scope | covered |
| 56 | `oracle/test_integration.py::test_controller_and_command_arguments_reach_command` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_controller_result_can_be_rendered_as_json` | integration | Representative Workflows | covered |
| 58 | `oracle/test_integration.py::test_print_extension_adds_app_print_after_argument_parse` | integration | Scope | covered |
| 59 | `oracle/test_integration.py::test_multiple_extensions_share_one_app_handler_graph` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_extension_loaded_from_config_section_uses_custom_section` | integration | Scope | covered |
| 61 | `oracle/test_integration.py::test_template_copy_renders_directory_and_file_names` | integration | Representative Workflows | covered |
| 62 | `oracle/test_integration.py::test_template_copy_honors_exclude_and_ignore_rules` | integration | Scope | covered |
| 63 | `oracle/test_integration.py::test_template_copy_requires_force_for_existing_files` | integration | Error Semantics | covered |
| 64 | `oracle/test_integration.py::test_template_load_prefers_added_local_directory` | integration | Scope | covered |
| 65 | `oracle/test_integration.py::test_plugin_directory_load_extends_application` | integration | Scope | covered |
| 66 | `oracle/test_integration.py::test_enabled_plugin_from_config_is_loaded` | integration | Cross-View Invariants | covered |
| 67 | `oracle/test_integration.py::test_plugin_can_register_controller_before_dispatch` | integration | Representative Workflows | covered |
| 68 | `oracle/test_integration.py::test_bootstrap_module_can_extend_application` | integration | Scope | covered |
| 69 | `oracle/test_integration.py::test_reload_rebuilds_core_managers_and_drops_runtime_extensions` | integration | Product State Model | covered |
| 70 | `oracle/test_integration.py::test_close_runs_pre_and_post_close_hooks_and_sets_code` | integration | Product State Model | covered |
| 71 | `oracle/test_integration.py::test_context_manager_closes_application_after_run` | integration | Product State Model | covered |
| 72 | `oracle/test_integration.py::test_config_section_override_drives_extensions_and_output` | integration | Cross-View Invariants | covered |
| 73 | `oracle/test_integration.py::test_render_handler_argument_can_bypass_default_output` | integration | Scope | covered |
| 74 | `oracle/test_integration.py::test_json_render_to_file_round_trips_structured_data` | integration | Cross-View Invariants | covered |
| 75 | `oracle/test_integration.py::test_app_add_config_file_then_parse_updates_config` | integration | Scope | covered |
| 76 | `oracle/test_integration.py::test_template_handler_copy_and_load_round_trip` | integration | Cross-View Invariants | covered |
| 77 | `oracle/test_integration.py::test_plugin_load_and_controller_dispatch_share_app_state` | integration | Cross-View Invariants | covered |
| 78 | `oracle/test_integration.py::test_full_local_app_workflow_connects_config_controller_hook_output` | integration | Representative Workflows | covered |

final_scoreable: 78
