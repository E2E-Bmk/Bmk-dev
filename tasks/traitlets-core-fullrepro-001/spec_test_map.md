# Spec Test Map - traitlets

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_top_level_installable_surface_exports_core_names | atomic | Installable Surface | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_config_installable_surface_exports_core_names | atomic | Installable Surface | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_loader_installable_surface_exports_loader_names | atomic | Installable Surface | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_trait_constructor_keyword_sets_public_value | atomic | Trait Declaration | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_trait_constructor_accepts_multiple_known_keywords | atomic | Trait Declaration | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_rejected_assignment_preserves_previous_value | atomic | Trait Declaration | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_trait_metadata_tag_visible_through_trait_metadata | atomic | Trait Declaration | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_tag_returns_same_trait_object | atomic | Trait Declaration | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_integer_accepts_int_and_rejects_string | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_float_accepts_int_and_float_rejects_text | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_coercing_numeric_traits_convert_strings | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_unicode_bytes_and_coercing_string_traits | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_bool_and_cbool_store_boolean_values | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_enum_and_caseless_enum_validation | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_fuzzy_enum_accepts_unambiguous_prefix | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_object_name_and_dotted_object_name_validation | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_tcp_address_validates_host_and_port | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_instance_type_this_and_callable_traits | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_container_traits_validate_elements_and_lengths | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_union_any_callable_and_regexp_traits | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_trait_from_string_and_list_from_string_list | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_dict_from_string_list_parses_key_value_pairs | atomic | Built-In Trait Types | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_dynamic_default_is_lazy_and_constructor_overrides_it | integration | Defaults, Observers, and Validators | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_observe_receives_bunch_change_and_unobserve_stops_it | integration | Defaults, Observers, and Validators | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_observe_decorator_registers_class_observer | integration | Defaults, Observers, and Validators | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_validator_transforms_value_before_storage | integration | Defaults, Observers, and Validators | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_validator_rejection_preserves_old_value | integration | Defaults, Observers, and Validators | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_hold_trait_notifications_batches_successful_changes | integration | Defaults, Observers, and Validators | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_hold_trait_notifications_rolls_back_on_validation_error | integration | Defaults, Observers, and Validators | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_trait_introspection_methods_reflect_metadata_and_values | atomic | Introspection and Mutation | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_add_traits_and_set_trait_use_validation_path | atomic | Introspection and Mutation | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_class_trait_views_expose_declared_traits | atomic | Introspection and Mutation | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_bidirectional_link_synchronizes_and_unlink_detaches | integration | Linking | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_directional_link_only_updates_target | integration | Linking | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_link_transform_uses_forward_and_reverse_functions | integration | Linking | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_invalid_link_endpoint_raises_before_linking | integration | Linking | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_bunch_attribute_and_item_views_match | atomic | Utility Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_import_item_imports_modules_and_attributes | atomic | Utility Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_signature_has_traits_allows_trait_keywords | atomic | Utility Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_config_uppercase_attribute_creates_section_and_lowercase_missing_fails | integration | Configuration Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_config_merge_overrides_scalars_and_preserves_nested_values | integration | Configuration Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_config_collisions_reports_conflicting_values | integration | Configuration Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_lazy_config_value_applies_container_updates | integration | Configuration Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_json_config_loader_reads_public_config_values | integration | Configuration Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_py_config_loader_uses_get_config_object | integration | Configuration Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_missing_required_config_file_raises | integration | Configuration Objects | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_configurable_loads_tagged_traits_from_matching_section | integration | Configurable Classes | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_configurable_constructor_keyword_overrides_config_value | integration | Configurable Classes | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_update_config_changes_existing_configurable_trait | integration | Configurable Classes | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_configurable_base_section_applies_to_subclass_and_specific_overrides | integration | Configurable Classes | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_singleton_configurable_instance_lifecycle | integration | Configurable Classes | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_logging_configurable_has_public_logger_trait | integration | Configurable Classes | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_application_cli_alias_and_flag_populate_config | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_application_cli_overrides_loaded_config_file | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_application_json_overrides_python_same_base | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_application_path_priority_prefers_earlier_directory | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_repeated_scalar_cli_option_raises | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_repeated_list_and_dict_cli_values_accumulate | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_boolean_flag_definitions_set_true_and_false | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_subcommand_instantiates_and_initializes_child_app | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_show_config_json_prints_current_config_and_stops_work | system_e2e | Application, Config Files, and CLI | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_error_semantics_invalid_trait_and_import_item | atomic | Error Semantics | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_error_semantics_invalid_config_value_raises_trait_error | atomic | Error Semantics | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_atomic.py::test_error_semantics_bad_cli_option_exits_or_raises | atomic | Error Semantics | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_cross_view_assignment_observer_and_trait_values_agree | integration | Product State Model; Cross-View Invariants | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_cross_view_constructor_override_does_not_call_default | integration | Product State Model; Cross-View Invariants | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_cross_view_metadata_visible_in_traits_and_help_section | integration | Product State Model; Cross-View Invariants | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_cross_view_rejected_validator_value_absent_from_notifications_and_links | integration | Product State Model; Cross-View Invariants | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_cross_view_validator_transform_observer_and_link_agree | integration | Product State Model; Cross-View Invariants | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_cross_view_config_dict_attribute_and_configurable_agree | integration | Product State Model; Cross-View Invariants | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_cross_view_application_cli_overrides_file_for_configurable | system_e2e | Product State Model; Cross-View Invariants | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_workflow_trait_object_defaults_validation_and_observation | integration | Trait Object With Defaults, Validation, and Observation | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_workflow_trait_object_constructor_override_and_rejection_state | integration | Trait Object With Defaults, Validation, and Observation | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_workflow_trait_object_validation_notification_success_path | integration | Trait Object With Defaults, Validation, and Observation | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_workflow_configurable_application_alias_flag_and_worker_state | system_e2e | Configurable Application | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_workflow_configurable_application_file_then_cli_priority | system_e2e | Configurable Application | covered | spec-driven behavioral assertion observed on reference |
| oracle/test_integration.py::test_workflow_configurable_application_flag_can_be_disabled | system_e2e | Configurable Application | covered | spec-driven behavioral assertion observed on reference |

Total: 77 | kept (covered): 77 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 77
