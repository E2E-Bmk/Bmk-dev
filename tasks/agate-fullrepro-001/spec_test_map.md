# Public Test Map

| test | layer | section | status |
| --- | --- | --- | --- |
| `oracle/test_atomic.py::test_table_constructor_casts_rows_and_types` | atomic | construction and types | covered |
| `oracle/test_atomic.py::test_table_short_row_is_padded_with_null` | atomic | construction and types | covered |
| `oracle/test_atomic.py::test_table_row_names_can_come_from_column` | atomic | row metadata | covered |
| `oracle/test_atomic.py::test_table_row_names_can_come_from_function` | atomic | row metadata | covered |
| `oracle/test_atomic.py::test_table_columns_expose_public_metadata` | atomic | column metadata | covered |
| `oracle/test_atomic.py::test_rows_support_keyed_and_indexed_access` | atomic | row metadata | covered |
| `oracle/test_atomic.py::test_columns_expose_distinct_and_sorted_values` | atomic | column metadata | covered |
| `oracle/test_atomic.py::test_mapped_sequences_are_immutable_and_named` | atomic | public containers | covered |
| `oracle/test_atomic.py::test_table_length_and_iteration_follow_rows` | atomic | construction and types | covered |
| `oracle/test_atomic.py::test_type_tester_infers_controlled_public_types` | atomic | type inference | covered |
| `oracle/test_atomic.py::test_type_tester_force_overrides_inference` | atomic | type inference | covered |
| `oracle/test_atomic.py::test_type_tester_limit_changes_inference_sample` | atomic | type inference | covered |
| `oracle/test_atomic.py::test_type_tester_custom_types_and_null_values` | atomic | type inference | covered |
| `oracle/test_atomic.py::test_text_cast_respects_null_policy` | atomic | data types | covered |
| `oracle/test_atomic.py::test_boolean_cast_respects_custom_literals` | atomic | data types | covered |
| `oracle/test_atomic.py::test_number_cast_uses_explicit_locale` | atomic | data types | covered |
| `oracle/test_atomic.py::test_date_cast_uses_explicit_format` | atomic | data types | covered |
| `oracle/test_atomic.py::test_datetime_cast_uses_explicit_format` | atomic | data types | covered |
| `oracle/test_atomic.py::test_timedelta_casts_duration_without_locale` | atomic | data types | covered |
| `oracle/test_atomic.py::test_select_preserves_requested_column_order` | atomic | table transforms | covered |
| `oracle/test_atomic.py::test_exclude_removes_named_columns` | atomic | table transforms | covered |
| `oracle/test_atomic.py::test_where_preserves_matching_rows_and_metadata` | atomic | table transforms | covered |
| `oracle/test_atomic.py::test_order_by_places_nulls_last` | atomic | table transforms | covered |
| `oracle/test_atomic.py::test_limit_accepts_start_stop_step` | atomic | table transforms | covered |
| `oracle/test_atomic.py::test_distinct_keeps_first_keyed_row` | atomic | table transforms | covered |
| `oracle/test_atomic.py::test_find_returns_first_matching_row` | atomic | table transforms | covered |
| `oracle/test_atomic.py::test_left_join_adds_right_projection` | atomic | joins | covered |
| `oracle/test_atomic.py::test_inner_join_drops_unmatched_rows` | atomic | joins | covered |
| `oracle/test_atomic.py::test_full_outer_join_retains_dangling_rows` | atomic | joins | covered |
| `oracle/test_atomic.py::test_join_columns_limits_right_projection` | atomic | joins | covered |
| `oracle/test_atomic.py::test_group_by_builds_public_tableset` | atomic | table sets | covered |
| `oracle/test_atomic.py::test_tableset_proxy_select_preserves_group_keys` | atomic | table sets | covered |
| `oracle/test_atomic.py::test_table_aggregate_returns_named_values` | atomic | aggregation | covered |
| `oracle/test_atomic.py::test_numeric_aggregations_return_typed_values` | atomic | aggregation | covered |
| `oracle/test_atomic.py::test_compute_formula_adds_typed_column` | atomic | computation | covered |
| `oracle/test_atomic.py::test_compute_replace_replaces_existing_column` | atomic | computation | covered |
| `oracle/test_atomic.py::test_percent_and_percent_change_add_columns` | atomic | computation | covered |
| `oracle/test_atomic.py::test_rank_and_slug_add_stable_projections` | atomic | computation | covered |
| `oracle/test_atomic.py::test_pivot_count_uses_key_and_pivot_columns` | atomic | pivot | covered |
| `oracle/test_atomic.py::test_pivot_sum_uses_numeric_aggregation` | atomic | pivot | covered |
| `oracle/test_atomic.py::test_normalize_emits_key_property_value_rows` | atomic | reshape | covered |
| `oracle/test_atomic.py::test_denormalize_restores_sparse_properties` | atomic | reshape | covered |
| `oracle/test_atomic.py::test_table_from_object_flattens_public_rows` | atomic | local input | covered |
| `oracle/test_atomic.py::test_table_csv_round_trip_reads_local_file` | atomic | local CSV | covered |
| `oracle/test_atomic.py::test_table_json_round_trip_reads_local_file` | atomic | local JSON | covered |
| `oracle/test_atomic.py::test_table_newline_json_round_trip_reads_local_file` | atomic | local JSON | covered |
| `oracle/test_atomic.py::test_tableset_csv_round_trip_reads_local_directory` | atomic | table-set I/O | covered |
| `oracle/test_atomic.py::test_tableset_nested_json_round_trip_reads_local_file` | atomic | table-set I/O | covered |
| `oracle/test_atomic.py::test_print_structure_reports_columns_and_types` | atomic | text projections | covered |
| `oracle/test_atomic.py::test_print_table_reports_headers_and_values` | atomic | text projections | covered |
| `oracle/test_atomic.py::test_print_bars_reports_labels_and_counts` | atomic | text projections | covered |
| `oracle/test_integration.py::test_select_where_compute_pipeline_preserves_fact_projection` | integration | cross-view invariants | covered |
| `oracle/test_integration.py::test_order_limit_distinct_pipeline_reduces_rows_consistently` | integration | cross-view invariants | covered |
| `oracle/test_integration.py::test_join_group_aggregate_pipeline_matches_manual_totals` | integration | joins and aggregation | covered |
| `oracle/test_integration.py::test_group_aggregate_and_pivot_agree_on_counts` | integration | cross-view invariants | covered |
| `oracle/test_integration.py::test_group_by_select_merge_round_trip_recreates_group_column` | integration | table-set workflow | covered |
| `oracle/test_integration.py::test_having_filters_aggregated_groups_before_merge` | integration | table-set workflow | covered |
| `oracle/test_integration.py::test_nested_grouping_aggregate_preserves_two_keys` | integration | table-set workflow | covered |
| `oracle/test_integration.py::test_tableset_proxy_compute_then_aggregate_projects_new_column` | integration | table-set workflow | covered |
| `oracle/test_integration.py::test_join_then_compute_taxed_revenue` | integration | joins and computation | covered |
| `oracle/test_integration.py::test_inner_join_then_group_by_category` | integration | joins and aggregation | covered |
| `oracle/test_integration.py::test_full_outer_join_then_where_identifies_missing_side` | integration | joins and filtering | covered |
| `oracle/test_integration.py::test_normalize_then_denormalize_round_trip_preserves_profiles` | integration | reshape invariants | covered |
| `oracle/test_integration.py::test_normalize_custom_column_names_round_trip` | integration | reshape invariants | covered |
| `oracle/test_integration.py::test_pivot_then_denormalize_matches_grouped_counts` | integration | reshape invariants | covered |
| `oracle/test_integration.py::test_pivot_percent_computation_sums_each_group` | integration | pivot and computation | covered |
| `oracle/test_integration.py::test_table_csv_round_trip_then_select_projection` | integration | CSV projections | covered |
| `oracle/test_integration.py::test_table_json_round_trip_then_compute_projection` | integration | JSON projections | covered |
| `oracle/test_integration.py::test_newline_json_round_trip_then_order_projection` | integration | JSON projections | covered |
| `oracle/test_integration.py::test_print_csv_can_feed_from_csv` | integration | text and CSV | covered |
| `oracle/test_integration.py::test_print_json_can_feed_from_json` | integration | text and JSON | covered |
| `oracle/test_integration.py::test_tableset_csv_round_trip_then_aggregate` | integration | table-set I/O | covered |
| `oracle/test_integration.py::test_tableset_nested_json_round_trip_then_proxy` | integration | table-set I/O | covered |
| `oracle/test_integration.py::test_temporal_table_json_round_trip_preserves_public_types` | integration | typed I/O | covered |
| `oracle/test_integration.py::test_type_tester_csv_route_agrees_with_explicit_types` | integration | type and CSV | covered |
| `oracle/test_integration.py::test_join_csv_sources_then_aggregate` | integration | local I/O workflow | covered |
| `oracle/test_integration.py::test_text_projections_follow_transformed_metadata` | integration | text projections | covered |
| `oracle/test_integration.py::test_print_bars_follows_pivot_counts` | integration | text projections | covered |
| `oracle/test_integration.py::test_aggregate_summary_matches_column_projection` | integration | cross-view invariants | covered |
| `oracle/test_integration.py::test_table_merge_preserves_group_order_after_select` | integration | table-set workflow | covered |
| `oracle/test_integration.py::test_required_match_reports_unmatched_join` | integration | error semantics | covered |
| `oracle/test_integration.py::test_invalid_join_mode_reports_public_value_error` | integration | error semantics | covered |
| `oracle/test_integration.py::test_compute_then_csv_round_trip_preserves_formula` | integration | computation and CSV | covered |
| `oracle/test_integration.py::test_local_json_round_trip_with_row_names_projection` | integration | row metadata and JSON | covered |
| `oracle/test_integration.py::test_table_set_workflow_group_compute_having_merge` | integration | table-set workflow | covered |

final_scoreable: 85
