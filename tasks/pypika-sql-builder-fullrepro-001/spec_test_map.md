# Behavior Map

Each physical check below is covered by the corresponding public behavior section.
The final scoreable count is 74.

| Layer | Test | Scope section | Coverage |
| --- | --- | --- | --- |
| atomic | test_public_import_surface_exposes_query_table_field_and_dialects | Public SQL Builder Surface | covered |
| atomic | test_query_select_from_strings_builds_quoted_select | Public SQL Builder Surface | covered |
| atomic | test_table_fields_project_namespaced_columns | Public SQL Builder Surface | covered |
| atomic | test_table_alias_changes_from_projection_namespace | Public SQL Builder Surface | covered |
| atomic | test_field_alias_is_rendered_after_an_expression | Public SQL Builder Surface | covered |
| atomic | test_schema_and_database_namespace_tables | Public SQL Builder Surface | covered |
| atomic | test_string_conversion_and_get_sql_share_stable_semantics | Public SQL Builder Surface | covered |
| atomic | test_arithmetic_expression_preserves_operator_precedence | Public SQL Builder Surface | covered |
| atomic | test_comparison_criteria_render_documented_comparators | Public SQL Builder Surface | covered |
| atomic | test_boolean_criteria_support_and_or_xor_and_not | Public SQL Builder Surface | covered |
| atomic | test_membership_and_between_criteria_render_sql | Public SQL Builder Surface | covered |
| atomic | test_null_and_negated_null_criteria_render_sql | Public SQL Builder Surface | covered |
| atomic | test_string_criteria_render_like_ilike_and_regex | Public SQL Builder Surface | covered |
| atomic | test_bitwise_criteria_use_documented_operators | Public SQL Builder Surface | covered |
| atomic | test_repeated_where_calls_accumulate_with_and | Public SQL Builder Surface | covered |
| atomic | test_join_on_adds_join_type_and_criterion | Public SQL Builder Surface | covered |
| atomic | test_join_using_projects_shared_field | Public SQL Builder Surface | covered |
| atomic | test_join_helpers_render_left_and_cross_joins | Public SQL Builder Surface | covered |
| atomic | test_group_by_and_having_filter_aggregates | Public SQL Builder Surface | covered |
| atomic | test_order_limit_and_offset_are_composed_in_order | Public SQL Builder Surface | covered |
| atomic | test_distinct_removes_duplicate_projection_semantics | Public SQL Builder Surface | covered |
| atomic | test_builtin_functions_render_arguments_and_aliases | Public SQL Builder Surface | covered |
| atomic | test_aggregate_distinct_and_filter_render_sql | Public SQL Builder Surface | covered |
| atomic | test_case_expression_renders_ordered_branches_and_else | Public SQL Builder Surface | covered |
| atomic | test_custom_function_uses_declared_parameters | Public SQL Builder Surface | covered |
| atomic | test_analytic_function_renders_partition_and_order | Public SQL Builder Surface | covered |
| atomic | test_tuple_criteria_render_pairwise_comparisons | Public SQL Builder Surface | covered |
| atomic | test_cte_and_aliased_query_render_a_named_subquery | Public SQL Builder Surface | covered |
| atomic | test_set_operations_render_union_all_intersect_and_except | Public SQL Builder Surface | covered |
| atomic | test_insert_values_and_multiple_rows_render_sql | Public SQL Builder Surface | covered |
| atomic | test_insert_from_select_preserves_target_columns | Public SQL Builder Surface | covered |
| atomic | test_update_query_renders_assignments_filter_and_limit | Public SQL Builder Surface | covered |
| atomic | test_delete_query_renders_filter_and_limit | Public SQL Builder Surface | covered |
| atomic | test_parameter_object_collects_values_with_qmark_placeholders | Public SQL Builder Surface | covered |
| atomic | test_mysql_dialect_uses_backticks_and_duplicate_handlers | Public SQL Builder Surface | covered |
| atomic | test_postgresql_dialect_supports_conflict_and_returning | Public SQL Builder Surface | covered |
| atomic | test_oracle_and_mssql_dialects_render_fetch_pagination | Public SQL Builder Surface | covered |
| atomic | test_clickhouse_dialect_supports_final_sample_and_limit_by | Public SQL Builder Surface | covered |
| integration | test_select_where_order_workflow | Representative Workflows | covered |
| integration | test_alias_arithmetic_filter_workflow | Representative Workflows | covered |
| integration | test_composed_criteria_workflow | Representative Workflows | covered |
| integration | test_join_on_filter_projection_workflow | Representative Workflows | covered |
| integration | test_join_using_aggregate_workflow | Representative Workflows | covered |
| integration | test_left_join_null_preservation_workflow | Representative Workflows | covered |
| integration | test_group_having_order_limit_workflow | Representative Workflows | covered |
| integration | test_distinct_offset_workflow | Representative Workflows | covered |
| integration | test_function_case_workflow | Representative Workflows | covered |
| integration | test_custom_function_cte_workflow | Representative Workflows | covered |
| integration | test_analytic_qualify_workflow | Representative Workflows | covered |
| integration | test_tuple_membership_filter_workflow | Representative Workflows | covered |
| integration | test_cte_join_workflow | Representative Workflows | covered |
| integration | test_union_all_order_limit_workflow | Representative Workflows | covered |
| integration | test_intersect_and_except_composition_workflow | Representative Workflows | covered |
| integration | test_multirow_insert_workflow | Representative Workflows | covered |
| integration | test_insert_select_join_workflow | Representative Workflows | covered |
| integration | test_update_join_filter_limit_workflow | Representative Workflows | covered |
| integration | test_delete_filter_limit_workflow | Representative Workflows | covered |
| integration | test_parameterized_composed_filter_workflow | Representative Workflows | covered |
| integration | test_mysql_duplicate_update_workflow | Representative Workflows | covered |
| integration | test_postgresql_conflict_update_returning_workflow | Representative Workflows | covered |
| integration | test_oracle_and_mssql_pagination_workflow | Representative Workflows | covered |
| integration | test_clickhouse_sampling_and_projection_workflow | Representative Workflows | covered |
| integration | test_namespace_table_filter_workflow | Representative Workflows | covered |
| integration | test_immutable_builder_branching_workflow | Representative Workflows | covered |
| integration | test_correlated_subquery_expression_workflow | Representative Workflows | covered |
| integration | test_composed_summary_workflow | Representative Workflows | covered |
| integration | test_join_window_and_order_workflow | Representative Workflows | covered |
| integration | test_cte_aggregate_and_order_workflow | Representative Workflows | covered |
| integration | test_insert_parameter_workflow | Representative Workflows | covered |
| integration | test_postgresql_distinct_on_and_returning_workflow | Representative Workflows | covered |
| integration | test_cte_union_workflow | Representative Workflows | covered |
| integration | test_delete_parameter_workflow | Representative Workflows | covered |
| integration | test_date_interval_function_workflow | Representative Workflows | covered |
| integration | test_multi_join_filter_workflow | Representative Workflows | covered |

final_scoreable: 74
