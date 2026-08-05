# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_surface_exposes_diff_search_hash_delta_and_paths` | atomic | Dictionary Conversion | covered |
| 2 | `oracle/test_atomic.py::test_equal_nested_objects_have_empty_diff` | atomic | Dictionary Conversion | covered |
| 3 | `oracle/test_atomic.py::test_nested_dictionary_value_change_reports_old_new_values_and_path` | atomic | Dictionary Conversion | covered |
| 4 | `oracle/test_atomic.py::test_dictionary_addition_and_removal_use_distinct_categories` | atomic | Dictionary Conversion | covered |
| 5 | `oracle/test_atomic.py::test_list_addition_and_removal_report_index_paths` | atomic | Dictionary Conversion | covered |
| 6 | `oracle/test_atomic.py::test_tuple_value_change_and_append_are_structural` | atomic | Typed Values And Collections | covered |
| 7 | `oracle/test_atomic.py::test_set_membership_changes_are_reported_at_the_set_path` | atomic | Dictionary Conversion | covered |
| 8 | `oracle/test_atomic.py::test_custom_object_attributes_are_compared` | atomic | Dictionary Conversion | covered |
| 9 | `oracle/test_atomic.py::test_type_changes_include_type_objects_and_values` | atomic | Dictionary Conversion | covered |
| 10 | `oracle/test_atomic.py::test_ignore_numeric_type_changes_suppresses_int_float_only_change` | atomic | Dictionary Conversion | covered |
| 11 | `oracle/test_atomic.py::test_ignore_string_case_suppresses_case_only_change` | atomic | Dictionary Conversion | covered |
| 12 | `oracle/test_atomic.py::test_significant_digits_suppresses_small_decimal_difference` | atomic | Dictionary Conversion | covered |
| 13 | `oracle/test_atomic.py::test_significant_digits_reports_difference_beyond_precision` | atomic | Dictionary Conversion | covered |
| 14 | `oracle/test_atomic.py::test_math_epsilon_suppresses_flat_numeric_difference` | atomic | Dictionary Conversion | covered |
| 15 | `oracle/test_atomic.py::test_include_paths_limits_comparison_to_selected_branch` | atomic | Dictionary Conversion | covered |
| 16 | `oracle/test_atomic.py::test_exclude_paths_removes_selected_branch_from_comparison` | atomic | Field Metadata And Configuration | covered |
| 17 | `oracle/test_atomic.py::test_exclude_regex_paths_removes_matching_nested_path` | atomic | Field Metadata And Configuration | covered |
| 18 | `oracle/test_atomic.py::test_ignore_order_suppresses_reordering_of_scalar_list` | atomic | Dictionary Conversion | covered |
| 19 | `oracle/test_atomic.py::test_ignore_order_matches_nested_dictionaries_by_content` | atomic | Dictionary Conversion | covered |
| 20 | `oracle/test_atomic.py::test_ignore_order_can_report_repetition_changes` | atomic | Dictionary Conversion | covered |
| 21 | `oracle/test_atomic.py::test_ignore_order_without_repetition_reporting_ignores_duplicate_positions` | atomic | Dictionary Conversion | covered |
| 22 | `oracle/test_atomic.py::test_tree_view_exposes_path_objects_and_text_view_has_same_path` | atomic | Dictionary Conversion | covered |
| 23 | `oracle/test_atomic.py::test_affected_paths_projects_changed_paths` | atomic | Dictionary Conversion | covered |
| 24 | `oracle/test_atomic.py::test_affected_root_keys_projects_top_level_keys` | atomic | Dictionary Conversion | covered |
| 25 | `oracle/test_atomic.py::test_verbose_level_zero_keeps_change_paths_without_values` | atomic | Dictionary Conversion | covered |
| 26 | `oracle/test_atomic.py::test_custom_base_operator_can_accept_small_numeric_variation` | atomic | Dictionary Conversion | covered |
| 27 | `oracle/test_atomic.py::test_custom_base_operator_reports_large_numeric_variation` | atomic | Dictionary Conversion | covered |
| 28 | `oracle/test_atomic.py::test_prefix_or_suffix_operator_accepts_prefix_relationship` | atomic | Dictionary Conversion | covered |
| 29 | `oracle/test_atomic.py::test_deepsearch_finds_case_insensitive_string_paths` | atomic | Dictionary Conversion | covered |
| 30 | `oracle/test_atomic.py::test_deepsearch_can_match_values_and_dictionary_keys` | atomic | Dictionary Conversion | covered |
| 31 | `oracle/test_atomic.py::test_deepsearch_regexp_mode_matches_selected_strings` | atomic | Dictionary Conversion | covered |
| 32 | `oracle/test_atomic.py::test_grep_operator_searches_an_object_with_pipe_syntax` | atomic | Dictionary Conversion | covered |
| 33 | `oracle/test_atomic.py::test_parse_path_and_extract_round_trip_nested_value` | atomic | Dictionary Conversion | covered |
| 34 | `oracle/test_atomic.py::test_deephash_is_stable_for_equal_nested_values` | atomic | Dictionary Conversion | covered |
| 35 | `oracle/test_atomic.py::test_delta_applies_value_addition_and_set_changes` | atomic | Dictionary Conversion | covered |
| 36 | `oracle/test_atomic.py::test_delta_mutate_false_preserves_input_identity` | atomic | Dictionary Conversion | covered |
| 37 | `oracle/test_atomic.py::test_delta_dumps_are_deterministic_for_same_diff` | atomic | Dictionary Conversion | covered |
| 38 | `oracle/test_atomic.py::test_delta_bytes_restore_and_apply_to_original` | atomic | Typed Values And Collections | covered |
| 39 | `oracle/test_atomic.py::test_deepdiff_json_is_parseable_and_contains_semantic_change_fields` | atomic | Typed Codecs | covered |
| 40 | `oracle/test_integration.py::test_diff_then_extract_changed_nested_value` | integration | Dictionary Conversion | covered |
| 41 | `oracle/test_integration.py::test_diff_delta_pipeline_reconstructs_nested_mapping` | integration | Pipelines And Groups | covered |
| 42 | `oracle/test_integration.py::test_json_projection_round_trips_diff_categories` | integration | Typed Codecs | covered |
| 43 | `oracle/test_integration.py::test_tree_and_text_views_preserve_affected_path_projection` | integration | Dictionary Conversion | covered |
| 44 | `oracle/test_integration.py::test_include_then_exclude_workflow_selects_only_allowed_branch` | integration | Field Metadata And Configuration | covered |
| 45 | `oracle/test_integration.py::test_ignore_order_workflow_distinguishes_reordering_from_repetition` | integration | Dictionary Conversion | covered |
| 46 | `oracle/test_integration.py::test_custom_object_diff_and_delta_preserve_object_type` | integration | Dictionary Conversion | covered |
| 47 | `oracle/test_integration.py::test_custom_operator_workflow_combines_numeric_and_string_rules` | integration | Dictionary Conversion | covered |
| 48 | `oracle/test_integration.py::test_search_workflow_finds_literal_then_regexp_matches` | integration | Typed Values And Collections | covered |
| 49 | `oracle/test_integration.py::test_grep_search_paths_can_be_extracted_from_source_object` | integration | Dictionary Conversion | covered |
| 50 | `oracle/test_integration.py::test_tuple_list_set_workflow_reports_and_applies_container_changes` | integration | Typed Values And Collections | covered |
| 51 | `oracle/test_integration.py::test_type_policy_workflow_can_strictly_report_or_ignore_numeric_types` | integration | Dictionary Conversion | covered |
| 52 | `oracle/test_integration.py::test_precision_workflow_changes_diff_visibility_and_json_projection` | integration | Typed Codecs | covered |
| 53 | `oracle/test_integration.py::test_case_and_order_policies_apply_together_to_nested_lists` | integration | Dictionary Conversion | covered |
| 54 | `oracle/test_integration.py::test_delta_serialization_workflow_is_repeatable_and_reversible` | integration | Dictionary Conversion | covered |
| 55 | `oracle/test_integration.py::test_hash_and_diff_workflow_agree_on_equal_nested_content` | integration | Dictionary Conversion | covered |
| 56 | `oracle/test_integration.py::test_affected_path_workflow_groups_changes_by_top_level_key` | integration | Pipelines And Groups | covered |
| 57 | `oracle/test_integration.py::test_regex_exclusion_workflow_leaves_json_public_branch_only` | integration | Typed Codecs | covered |
| 58 | `oracle/test_integration.py::test_custom_object_workflow_uses_mapping_for_json_serialization` | integration | Typed Values And Collections | covered |
| 59 | `oracle/test_integration.py::test_branch_selection_workflow_is_consistent_for_nested_changes` | integration | Dictionary Conversion | covered |
| 60 | `oracle/test_integration.py::test_numeric_policy_workflow_combines_epsilon_and_precision` | integration | Dictionary Conversion | covered |
| 61 | `oracle/test_integration.py::test_delta_workflow_replays_same_serialized_patch_twice` | integration | Field Metadata And Configuration | covered |
| 62 | `oracle/test_integration.py::test_repetition_report_can_be_serialized_as_a_semantic_delta` | integration | Field Metadata And Configuration | covered |
| 63 | `oracle/test_integration.py::test_search_workflow_cross_checks_literal_and_key_matches` | integration | Typed Values And Collections | covered |
| 64 | `oracle/test_integration.py::test_path_extract_and_delta_workflow_targets_same_nested_location` | integration | Dictionary Conversion | covered |
| 65 | `oracle/test_integration.py::test_ordered_tuple_and_unordered_set_hash_diff_workflow` | integration | Typed Values And Collections | covered |
| 66 | `oracle/test_integration.py::test_verbose_projection_workflow_preserves_paths_at_two_detail_levels` | integration | Dictionary Conversion | covered |
| 67 | `oracle/test_integration.py::test_custom_operator_then_delta_workflow_changes_only_unaccepted_value` | integration | Dictionary Conversion | covered |
| 68 | `oracle/test_integration.py::test_prefix_operator_then_delta_workflow_preserves_accepted_text` | integration | Dictionary Conversion | covered |
| 69 | `oracle/test_integration.py::test_json_diff_and_binary_delta_serve_distinct_restore_projections` | integration | Typed Codecs | covered |

final_scoreable: 69
