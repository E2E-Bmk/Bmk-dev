# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_model_classes_expose_public_field_metadata` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_describe_models_is_json_serializable` | atomic | Cross-View Invariants | covered |
| 3 | `oracle/test_atomic.py::test_generate_schemas_allows_create` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_create_assigns_explicit_primary_key_and_reads_pk` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_save_inserts_and_updates_single_row` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_filter_equality_selects_matching_rows` | atomic | Scope | covered |
| 7 | `oracle/test_atomic.py::test_filter_comparison_and_string_lookups` | atomic | Scope | covered |
| 8 | `oracle/test_atomic.py::test_exclude_removes_matching_rows` | atomic | Scope | covered |
| 9 | `oracle/test_atomic.py::test_order_by_supports_ascending_and_descending` | atomic | Scope | covered |
| 10 | `oracle/test_atomic.py::test_values_returns_selected_dict_fields` | atomic | Scope | covered |
| 11 | `oracle/test_atomic.py::test_values_supports_alias_for_related_field` | atomic | Cross-View Invariants | covered |
| 12 | `oracle/test_atomic.py::test_values_list_returns_tuples_and_flat_values` | atomic | Scope | covered |
| 13 | `oracle/test_atomic.py::test_count_and_exists_reflect_rows` | atomic | Scope | covered |
| 14 | `oracle/test_atomic.py::test_first_and_get_or_none_return_expected_rows` | atomic | Scope | covered |
| 15 | `oracle/test_atomic.py::test_get_or_create_reports_created_flag` | atomic | Cross-View Invariants | covered |
| 16 | `oracle/test_atomic.py::test_update_or_create_updates_existing_row` | atomic | Cross-View Invariants | covered |
| 17 | `oracle/test_atomic.py::test_queryset_update_returns_affected_count` | atomic | Product State Model | covered |
| 18 | `oracle/test_atomic.py::test_queryset_delete_removes_rows` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_bulk_create_inserts_multiple_rows` | atomic | Product State Model | covered |
| 20 | `oracle/test_atomic.py::test_bulk_update_changes_selected_fields` | atomic | Product State Model | covered |
| 21 | `oracle/test_atomic.py::test_nullable_and_boolean_values_round_trip` | atomic | Product State Model | covered |
| 22 | `oracle/test_atomic.py::test_json_values_round_trip` | atomic | Product State Model | covered |
| 23 | `oracle/test_atomic.py::test_foreign_key_filter_uses_related_field` | atomic | Cross-View Invariants | covered |
| 24 | `oracle/test_atomic.py::test_prefetch_related_populates_forward_relation` | atomic | Public Import Surface | covered |
| 25 | `oracle/test_atomic.py::test_reverse_relation_prefetch_returns_children` | atomic | Public Import Surface | covered |
| 26 | `oracle/test_atomic.py::test_many_to_many_add_and_prefetch` | atomic | Public Import Surface | covered |
| 27 | `oracle/test_atomic.py::test_many_to_many_remove_and_clear` | atomic | Public Import Surface | covered |
| 28 | `oracle/test_atomic.py::test_model_describe_names_fields_and_table` | atomic | Cross-View Invariants | covered |
| 29 | `oracle/test_atomic.py::test_tortoise_describe_models_names_registered_models` | atomic | Cross-View Invariants | covered |
| 30 | `oracle/test_atomic.py::test_file_database_creates_persistent_sqlite_path` | atomic | Product State Model | covered |
| 31 | `oracle/test_integration.py::test_create_save_filter_and_values_share_row_projection` | integration | Cross-View Invariants | covered |
| 32 | `oracle/test_integration.py::test_ordering_and_values_list_preserve_projection_order` | integration | Cross-View Invariants | covered |
| 33 | `oracle/test_integration.py::test_exclude_and_isnull_partition_nullable_rows` | integration | Cross-View Invariants | covered |
| 34 | `oracle/test_integration.py::test_get_or_create_then_update_or_create_preserve_identity` | integration | Cross-View Invariants | covered |
| 35 | `oracle/test_integration.py::test_bulk_create_filter_and_bulk_update_workflow` | integration | Cross-View Invariants | covered |
| 36 | `oracle/test_integration.py::test_delete_workflow_updates_count_and_exists` | integration | Cross-View Invariants | covered |
| 37 | `oracle/test_integration.py::test_forward_prefetch_and_values_related_name_agree` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_reverse_prefetch_and_related_filter_agree` | integration | Cross-View Invariants | covered |
| 39 | `oracle/test_integration.py::test_many_to_many_prefetch_and_values_list_agree` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_relation_mutations_change_prefetched_projection` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_nested_relation_filter_and_order_projection` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_model_metadata_matches_relation_projection` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_schema_generation_supports_repeated_safe_initialization` | integration | Product State Model | covered |
| 44 | `oracle/test_integration.py::test_file_database_round_trip_from_insert_to_read` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_first_last_and_limit_offset_share_ordered_rows` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_range_in_and_case_insensitive_filters_compose` | integration | Scope | covered |
| 47 | `oracle/test_integration.py::test_boolean_and_numeric_filters_compose` | integration | Scope | covered |
| 48 | `oracle/test_integration.py::test_save_update_refreshes_filtered_values` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_instance_delete_removes_from_relation_projection` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_get_or_none_returns_none_for_missing_row` | integration | Error Semantics | covered |
| 51 | `oracle/test_integration.py::test_values_default_projection_contains_database_fields` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_values_list_default_projection_contains_database_fields` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_prefetch_then_instance_fetch_related_keeps_relations` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_many_to_many_duplicate_add_is_idempotent` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_related_creation_sets_foreign_key` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_model_describe_and_tortoise_describe_models_agree` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_file_database_schema_and_query_are_independent_views` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_chained_queryset_is_lazy_until_awaited` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_queryset_reuse_produces_same_values` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_end_to_end_library_projection` | integration | Representative Workflow | covered |

final_scoreable: 60
