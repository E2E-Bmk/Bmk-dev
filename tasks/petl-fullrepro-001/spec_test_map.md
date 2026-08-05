# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_exposes_documented_table_entry_points` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_wrap_preserves_table_rows` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_table_iterators_are_independent` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_header_returns_tuple` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_fieldnames_stringifies_headers` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_data_excludes_header` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_values_projects_one_field` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_fromdicts_respects_explicit_header` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_cut_selects_and_reorders_fields` | atomic | Scope | covered |
| 10 | `oracle/test_atomic.py::test_cut_pads_short_rows_with_missing` | atomic | Scope | covered |
| 11 | `oracle/test_atomic.py::test_convert_applies_callable_to_field` | atomic | Scope | covered |
| 12 | `oracle/test_atomic.py::test_convertall_applies_callable_to_each_data_field` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_select_field_predicate_keeps_matching_rows` | atomic | Scope | covered |
| 14 | `oracle/test_atomic.py::test_select_row_expression_uses_named_fields` | atomic | Scope | covered |
| 15 | `oracle/test_atomic.py::test_select_complement_inverts_predicate` | atomic | Scope | covered |
| 16 | `oracle/test_atomic.py::test_cat_appends_compatible_tables` | atomic | Scope | covered |
| 17 | `oracle/test_atomic.py::test_join_matches_rows_on_common_key` | atomic | Representative Workflows | covered |
| 18 | `oracle/test_atomic.py::test_leftjoin_fills_missing_right_values` | atomic | Representative Workflows | covered |
| 19 | `oracle/test_atomic.py::test_aggregate_sums_field_per_key` | atomic | Representative Workflows | covered |
| 20 | `oracle/test_atomic.py::test_aggregate_supports_multiple_named_reductions` | atomic | Representative Workflows | covered |
| 21 | `oracle/test_atomic.py::test_pivot_builds_columns_from_second_field` | atomic | Representative Workflows | covered |
| 22 | `oracle/test_atomic.py::test_lookup_collects_duplicate_values` | atomic | Scope | covered |
| 23 | `oracle/test_atomic.py::test_lookupone_returns_scalar_values` | atomic | Representative Workflows | covered |
| 24 | `oracle/test_atomic.py::test_lookupone_strict_rejects_duplicate_key` | atomic | Scope | covered |
| 25 | `oracle/test_atomic.py::test_transform_view_is_lazy_until_iteration` | atomic | Cross-View Invariants | covered |
| 26 | `oracle/test_atomic.py::test_transform_view_supports_repeated_iteration` | atomic | Cross-View Invariants | covered |
| 27 | `oracle/test_atomic.py::test_csv_path_round_trip_preserves_delimited_values` | atomic | Scope | covered |
| 28 | `oracle/test_atomic.py::test_csv_custom_delimiter_round_trip` | atomic | Scope | covered |
| 29 | `oracle/test_atomic.py::test_look_contains_header_and_values` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_lookstr_uses_string_value_projection` | atomic | Cross-View Invariants | covered |
| 31 | `oracle/test_atomic.py::test_html_display_projection_contains_table_cells` | atomic | Cross-View Invariants | covered |
| 32 | `oracle/test_atomic.py::test_missing_field_raises_public_selection_error` | atomic | Scope | covered |
| 33 | `oracle/test_integration.py::test_csv_convert_select_cut_pipeline` | integration | Scope | covered |
| 34 | `oracle/test_integration.py::test_cut_convert_and_cat_combine_batches` | integration | Scope | covered |
| 35 | `oracle/test_integration.py::test_select_then_aggregate_sales_by_region` | integration | Scope | covered |
| 36 | `oracle/test_integration.py::test_join_then_lookup_manager_names` | integration | Representative Workflows | covered |
| 37 | `oracle/test_integration.py::test_leftjoin_then_select_active_customers` | integration | Scope | covered |
| 38 | `oracle/test_integration.py::test_converted_amounts_feed_multiple_group_reductions` | integration | Scope | covered |
| 39 | `oracle/test_integration.py::test_pivot_then_cut_projects_selected_customers` | integration | Scope | covered |
| 40 | `oracle/test_integration.py::test_fromdicts_then_convert_and_select` | integration | Product State Model | covered |
| 41 | `oracle/test_integration.py::test_lazy_view_can_feed_downstream_pipeline` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_csv_view_supports_two_independent_consumers` | integration | Scope | covered |
| 43 | `oracle/test_integration.py::test_csv_round_trip_after_transformation` | integration | Scope | covered |
| 44 | `oracle/test_integration.py::test_custom_delimiter_round_trip_then_convert` | integration | Scope | covered |
| 45 | `oracle/test_integration.py::test_table_method_chain_matches_top_level_pipeline` | integration | Scope | covered |
| 46 | `oracle/test_integration.py::test_expression_filter_cut_and_lookstr_share_values` | integration | Scope | covered |
| 47 | `oracle/test_integration.py::test_complementary_selects_can_be_combined_back` | integration | Scope | covered |
| 48 | `oracle/test_integration.py::test_join_with_different_key_names` | integration | Representative Workflows | covered |
| 49 | `oracle/test_integration.py::test_leftjoin_custom_missing_marker` | integration | Representative Workflows | covered |
| 50 | `oracle/test_integration.py::test_outerjoin_includes_unmatched_keys` | integration | Representative Workflows | covered |
| 51 | `oracle/test_integration.py::test_compound_lookup_groups_by_two_fields` | integration | Representative Workflows | covered |
| 52 | `oracle/test_integration.py::test_lookupone_default_rows_can_be_indexed` | integration | Representative Workflows | covered |
| 53 | `oracle/test_integration.py::test_aggregate_without_key_returns_one_total` | integration | Representative Workflows | covered |
| 54 | `oracle/test_integration.py::test_aggregate_can_collect_compound_values` | integration | Representative Workflows | covered |
| 55 | `oracle/test_integration.py::test_pivot_missing_cells_use_explicit_value` | integration | Representative Workflows | covered |
| 56 | `oracle/test_integration.py::test_pivot_result_can_be_converted_and_projected` | integration | Scope | covered |
| 57 | `oracle/test_integration.py::test_html_projection_tracks_transformed_header` | integration | Product State Model | covered |
| 58 | `oracle/test_integration.py::test_text_and_html_display_projections_agree_on_values` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_header_data_and_values_remain_consistent_after_cut` | integration | Product State Model | covered |
| 60 | `oracle/test_integration.py::test_lazy_conversion_does_not_mutate_source` | integration | Cross-View Invariants | covered |
| 61 | `oracle/test_integration.py::test_reusing_a_pipeline_produces_same_rows` | integration | Cross-View Invariants | covered |
| 62 | `oracle/test_integration.py::test_local_csv_join_and_aggregate_workflow` | integration | Scope | covered |
| 63 | `oracle/test_integration.py::test_joined_manager_projection_matches_lookup_projection` | integration | Representative Workflows | covered |
| 64 | `oracle/test_integration.py::test_end_to_end_sales_workflow_projects_summary_and_pivot` | integration | Representative Workflows | covered |

final_scoreable: 64
