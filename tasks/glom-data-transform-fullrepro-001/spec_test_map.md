# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_surface_exposes_transformers_and_errors` | atomic | Dictionary Conversion | covered |
| 2 | `oracle/test_atomic.py::test_path_accesses_literal_keys_and_list_positions` | atomic | Typed Values And Collections | covered |
| 3 | `oracle/test_atomic.py::test_path_supports_length_values_items_and_slicing` | atomic | Dictionary Conversion | covered |
| 4 | `oracle/test_atomic.py::test_t_and_s_project_target_and_scope_values` | atomic | Dictionary Conversion | covered |
| 5 | `oracle/test_atomic.py::test_t_can_call_object_methods_and_slice_values` | atomic | Dictionary Conversion | covered |
| 6 | `oracle/test_atomic.py::test_val_preserves_literal_strings_in_constructed_output` | atomic | Typed Values And Collections | covered |
| 7 | `oracle/test_atomic.py::test_stop_stops_list_spec_iteration` | atomic | Dictionary Conversion | covered |
| 8 | `oracle/test_atomic.py::test_coalesce_uses_first_available_path` | atomic | Dictionary Conversion | covered |
| 9 | `oracle/test_atomic.py::test_coalesce_supports_default_and_default_factory` | atomic | Actors And Messages | covered |
| 10 | `oracle/test_atomic.py::test_coalesce_can_skip_values` | atomic | Dictionary Conversion | covered |
| 11 | `oracle/test_atomic.py::test_coalesce_error_exposes_spec_skipped_values_and_path` | atomic | Dictionary Conversion | covered |
| 12 | `oracle/test_atomic.py::test_s_binds_values_for_later_scope_access` | atomic | Dictionary Conversion | covered |
| 13 | `oracle/test_atomic.py::test_invoke_combines_constants_and_specs` | atomic | Dictionary Conversion | covered |
| 14 | `oracle/test_atomic.py::test_invoke_supports_starred_positional_specs` | atomic | Dictionary Conversion | covered |
| 15 | `oracle/test_atomic.py::test_spec_compiles_a_reusable_public_transformation` | atomic | Dictionary Conversion | covered |
| 16 | `oracle/test_atomic.py::test_glommer_provides_an_isolated_public_runner` | atomic | Dictionary Conversion | covered |
| 17 | `oracle/test_atomic.py::test_inspect_echo_false_preserves_transformation_result` | atomic | Results | covered |
| 18 | `oracle/test_atomic.py::test_assign_updates_nested_dict_and_list_in_place` | atomic | Dictionary Conversion | covered |
| 19 | `oracle/test_atomic.py::test_assign_can_create_missing_nested_dicts` | atomic | Dictionary Conversion | covered |
| 20 | `oracle/test_atomic.py::test_assign_can_copy_a_value_with_spec` | atomic | Dictionary Conversion | covered |
| 21 | `oracle/test_atomic.py::test_assign_reports_semantic_path_assign_error` | atomic | Dictionary Conversion | covered |
| 22 | `oracle/test_atomic.py::test_delete_removes_nested_dict_key_and_list_item` | atomic | Dictionary Conversion | covered |
| 23 | `oracle/test_atomic.py::test_delete_can_ignore_missing_paths` | atomic | Dictionary Conversion | covered |
| 24 | `oracle/test_atomic.py::test_delete_reports_path_delete_error_for_missing_list_item` | atomic | Dictionary Conversion | covered |
| 25 | `oracle/test_atomic.py::test_flatten_spec_and_function_flatten_one_level` | atomic | Dictionary Conversion | covered |
| 26 | `oracle/test_atomic.py::test_flatten_supports_levels_and_custom_initializer` | atomic | Dictionary Conversion | covered |
| 27 | `oracle/test_atomic.py::test_flatten_lazy_mode_returns_an_iterator` | atomic | Dictionary Conversion | covered |
| 28 | `oracle/test_atomic.py::test_match_validates_nested_mapping_and_list_shapes` | atomic | Typed Values And Collections | covered |
| 29 | `oracle/test_atomic.py::test_match_default_and_matches_methods` | atomic | Field Metadata And Configuration | covered |
| 30 | `oracle/test_atomic.py::test_match_failure_exposes_public_error_types` | atomic | Dictionary Conversion | covered |
| 31 | `oracle/test_atomic.py::test_switch_routes_matching_cases_and_default` | atomic | Field Metadata And Configuration | covered |
| 32 | `oracle/test_atomic.py::test_check_passes_through_valid_value_and_can_default` | atomic | Field Metadata And Configuration | covered |
| 33 | `oracle/test_atomic.py::test_check_error_exposes_messages_check_object_and_path` | atomic | Actors And Messages | covered |
| 34 | `oracle/test_atomic.py::test_match_boolean_combinators_and_regex_are_composable` | atomic | Dictionary Conversion | covered |
| 35 | `oracle/test_atomic.py::test_path_access_error_exposes_public_path_attributes` | atomic | Dictionary Conversion | covered |
| 36 | `oracle/test_atomic.py::test_glom_default_handles_a_path_access_error` | atomic | Field Metadata And Configuration | covered |
| 37 | `oracle/test_atomic.py::test_glom_wraps_non_glom_errors_as_glom_error` | atomic | Dictionary Conversion | covered |
| 38 | `oracle/test_integration.py::test_nested_path_projection_combines_literal_key_and_list_access` | integration | Typed Values And Collections | covered |
| 39 | `oracle/test_integration.py::test_scope_binding_and_literal_values_build_a_summary` | integration | Typed Values And Collections | covered |
| 40 | `oracle/test_integration.py::test_object_method_and_invoke_transform_one_record` | integration | Dictionary Conversion | covered |
| 41 | `oracle/test_integration.py::test_stop_and_flatten_process_nested_batches` | integration | Dictionary Conversion | covered |
| 42 | `oracle/test_integration.py::test_coalesce_selects_a_contact_fallback_then_projects_it` | integration | Dictionary Conversion | covered |
| 43 | `oracle/test_integration.py::test_coalesce_skip_and_failure_modes_are_distinct` | integration | Dictionary Conversion | covered |
| 44 | `oracle/test_integration.py::test_s_and_spec_reuse_transform_two_records` | integration | Dictionary Conversion | covered |
| 45 | `oracle/test_integration.py::test_inspect_can_wrap_a_scoped_projection_without_changing_result` | integration | Results | covered |
| 46 | `oracle/test_integration.py::test_assign_then_read_back_a_created_nested_record` | integration | Dictionary Conversion | covered |
| 47 | `oracle/test_integration.py::test_assign_copy_then_delete_restructures_a_mapping` | integration | Typed Values And Collections | covered |
| 48 | `oracle/test_integration.py::test_mutation_errors_leave_the_original_container_observable` | integration | Dictionary Conversion | covered |
| 49 | `oracle/test_integration.py::test_delete_optional_cleanup_can_follow_a_present_cleanup` | integration | Typed Values And Collections | covered |
| 50 | `oracle/test_integration.py::test_flatten_two_levels_then_lazily_flatten_followup_batches` | integration | Dictionary Conversion | covered |
| 51 | `oracle/test_integration.py::test_match_then_project_only_verified_fields` | integration | Dictionary Conversion | covered |
| 52 | `oracle/test_integration.py::test_match_combinators_validate_an_event_record` | integration | Dictionary Conversion | covered |
| 53 | `oracle/test_integration.py::test_switch_routes_event_kinds_into_normalized_records` | integration | Dictionary Conversion | covered |
| 54 | `oracle/test_integration.py::test_check_validates_a_projected_score_and_supplies_fallback` | integration | Dictionary Conversion | covered |
| 55 | `oracle/test_integration.py::test_path_error_can_be_recovered_inside_a_composed_projection` | integration | Dictionary Conversion | covered |
| 56 | `oracle/test_integration.py::test_default_recovery_handles_both_path_and_callable_failures` | integration | Field Metadata And Configuration | covered |
| 57 | `oracle/test_integration.py::test_mixed_path_and_t_projection_restructures_nested_data` | integration | Dictionary Conversion | covered |
| 58 | `oracle/test_integration.py::test_invoke_and_flatten_normalize_matrix_rows` | integration | Dictionary Conversion | covered |
| 59 | `oracle/test_integration.py::test_compiled_spec_and_glommer_agree_on_nested_output` | integration | Dictionary Conversion | covered |
| 60 | `oracle/test_integration.py::test_object_attribute_workflow_reads_then_removes_a_field` | integration | Dictionary Conversion | covered |
| 61 | `oracle/test_integration.py::test_stop_and_val_filter_a_list_into_literal_labeled_rows` | integration | Typed Values And Collections | covered |
| 62 | `oracle/test_integration.py::test_coalesce_and_check_form_a_tolerant_score_pipeline` | integration | Pipelines And Groups | covered |
| 63 | `oracle/test_integration.py::test_switch_then_invoke_formats_a_status_label` | integration | Dictionary Conversion | covered |
| 64 | `oracle/test_integration.py::test_assign_builds_then_match_verifies_a_local_payload` | integration | Dictionary Conversion | covered |
| 65 | `oracle/test_integration.py::test_cleanup_and_default_access_leave_a_stable_summary` | integration | Field Metadata And Configuration | covered |
| 66 | `oracle/test_integration.py::test_flattened_events_are_routed_into_categories` | integration | Dictionary Conversion | covered |
| 67 | `oracle/test_integration.py::test_regex_match_and_check_validate_a_user_projection` | integration | Dictionary Conversion | covered |
| 68 | `oracle/test_integration.py::test_path_metadata_and_assignment_copy_keep_source_data_intact` | integration | Dictionary Conversion | covered |

final_scoreable: 68
