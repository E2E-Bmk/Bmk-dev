# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_database_mapping_creates_declared_entities` | atomic | Scope | covered |
| 2 | `oracle/test_atomic.py::test_required_optional_and_default_values_round_trip` | atomic | Scope | covered |
| 3 | `oracle/test_atomic.py::test_primary_key_lookup_and_identity` | atomic | Cross-View Invariants | covered |
| 4 | `oracle/test_atomic.py::test_auto_primary_key_assigns_value` | atomic | Scope | covered |
| 5 | `oracle/test_atomic.py::test_entity_get_and_exists_report_rows` | atomic | Scope | covered |
| 6 | `oracle/test_atomic.py::test_select_returns_entities_in_requested_order` | atomic | Scope | covered |
| 7 | `oracle/test_atomic.py::test_select_scalar_projection_returns_values` | atomic | Scope | covered |
| 8 | `oracle/test_atomic.py::test_filter_lambda_restricts_query` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_filter_kwargs_restricts_query` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_order_by_ascending_and_descending` | atomic | Scope | covered |
| 11 | `oracle/test_atomic.py::test_query_slice_and_first_return_positioned_rows` | atomic | Scope | covered |
| 12 | `oracle/test_atomic.py::test_count_aggregate_counts_entities` | atomic | Scope | covered |
| 13 | `oracle/test_atomic.py::test_sum_and_avg_aggregates` | atomic | Scope | covered |
| 14 | `oracle/test_atomic.py::test_min_max_and_empty_aggregates` | atomic | Scope | covered |
| 15 | `oracle/test_atomic.py::test_related_filter_joins_forward_relationship` | atomic | Cross-View Invariants | covered |
| 16 | `oracle/test_atomic.py::test_reverse_set_iteration_and_count` | atomic | Cross-View Invariants | covered |
| 17 | `oracle/test_atomic.py::test_many_to_many_add_is_idempotent` | atomic | Cross-View Invariants | covered |
| 18 | `oracle/test_atomic.py::test_many_to_many_remove_and_clear` | atomic | Cross-View Invariants | covered |
| 19 | `oracle/test_atomic.py::test_optional_relationship_can_be_null` | atomic | Cross-View Invariants | covered |
| 20 | `oracle/test_atomic.py::test_to_dict_contains_scalar_and_foreign_key_values` | atomic | Cross-View Invariants | covered |
| 21 | `oracle/test_atomic.py::test_to_dict_includes_collections_when_requested` | atomic | Cross-View Invariants | covered |
| 22 | `oracle/test_atomic.py::test_to_dict_can_emit_related_objects` | atomic | Cross-View Invariants | covered |
| 23 | `oracle/test_atomic.py::test_to_dict_only_and_exclude_are_respected` | atomic | Cross-View Invariants | covered |
| 24 | `oracle/test_atomic.py::test_json_field_round_trips_and_tracks_mutation` | atomic | Scope | covered |
| 25 | `oracle/test_atomic.py::test_entity_set_updates_persisted_fields` | atomic | Scope | covered |
| 26 | `oracle/test_atomic.py::test_entity_delete_removes_row` | atomic | Scope | covered |
| 27 | `oracle/test_atomic.py::test_query_delete_removes_matching_rows` | atomic | Scope | covered |
| 28 | `oracle/test_atomic.py::test_set_collection_create_links_child` | atomic | Cross-View Invariants | covered |
| 29 | `oracle/test_atomic.py::test_required_validation_raises_value_error` | atomic | Error Semantics | covered |
| 30 | `oracle/test_atomic.py::test_invalid_value_and_unknown_attribute_raise_public_errors` | atomic | Error Semantics | covered |
| 31 | `oracle/test_atomic.py::test_duplicate_primary_key_raises_public_error` | atomic | Error Semantics | covered |
| 32 | `oracle/test_atomic.py::test_db_session_success_commits` | atomic | Product State Model | covered |
| 33 | `oracle/test_atomic.py::test_db_session_exception_rolls_back` | atomic | Product State Model | covered |
| 34 | `oracle/test_atomic.py::test_allowed_exception_commits` | atomic | Product State Model | covered |
| 35 | `oracle/test_atomic.py::test_strict_session_expires_objects` | atomic | Product State Model | covered |
| 36 | `oracle/test_integration.py::test_seed_projection_agrees_across_entity_and_scalar_queries` | integration | Scope | covered |
| 37 | `oracle/test_integration.py::test_ordering_projection_and_aggregate_share_the_same_rows` | integration | Scope | covered |
| 38 | `oracle/test_integration.py::test_create_update_delete_sequence_updates_counts_and_lookup` | integration | Scope | covered |
| 39 | `oracle/test_integration.py::test_filter_order_and_slice_preserve_the_same_projection` | integration | Scope | covered |
| 40 | `oracle/test_integration.py::test_failed_transaction_preserves_the_committed_projection` | integration | Product State Model | covered |
| 41 | `oracle/test_integration.py::test_allowed_transaction_exception_keeps_public_state` | integration | Product State Model | covered |
| 42 | `oracle/test_integration.py::test_session_identity_cache_tracks_entity_mutations` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_forward_relation_and_serialization_agree` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_reverse_relation_and_forward_filter_agree` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_many_to_many_relation_and_collection_serialization_agree` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_many_to_many_mutations_change_both_relation_views` | integration | Cross-View Invariants | covered |
| 47 | `oracle/test_integration.py::test_optional_editor_relation_updates_reverse_collection` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_grouped_count_aggregate_matches_author_collections` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_grouped_sum_aggregate_matches_filtered_pages` | integration | Scope | covered |
| 50 | `oracle/test_integration.py::test_get_exists_and_identity_form_one_lookup_contract` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_query_built_before_insert_evaluates_current_database_state` | integration | Scope | covered |
| 52 | `oracle/test_integration.py::test_chained_filters_and_descending_order_compose` | integration | Scope | covered |
| 53 | `oracle/test_integration.py::test_select_kwargs_and_scalar_projection_agree` | integration | Scope | covered |
| 54 | `oracle/test_integration.py::test_collection_create_is_visible_from_entity_and_reverse_queries` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_to_dict_scalar_and_related_modes_preserve_row_identity` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_json_and_optional_values_survive_a_new_session` | integration | Product State Model | covered |
| 57 | `oracle/test_integration.py::test_validation_failure_does_not_create_a_partial_entity` | integration | Error Semantics | covered |
| 58 | `oracle/test_integration.py::test_duplicate_primary_key_failure_preserves_original_row` | integration | Error Semantics | covered |
| 59 | `oracle/test_integration.py::test_auto_primary_key_and_to_dict_share_the_inserted_identity` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_explicit_commit_preserves_later_entity_updates` | integration | Product State Model | covered |
| 61 | `oracle/test_integration.py::test_rollback_on_exception_restores_json_and_scalar_values` | integration | Product State Model | covered |
| 62 | `oracle/test_integration.py::test_nested_db_sessions_share_the_outer_cache` | integration | Cross-View Invariants | covered |
| 63 | `oracle/test_integration.py::test_collection_query_and_global_query_return_the_same_children` | integration | Cross-View Invariants | covered |
| 64 | `oracle/test_integration.py::test_optional_relation_query_matches_reverse_editor_collection` | integration | Cross-View Invariants | covered |
| 65 | `oracle/test_integration.py::test_end_to_end_library_projection_remains_consistent_after_mutations` | integration | Representative Workflow | covered |
| 66 | `oracle/test_integration.py::test_prefetched_relation_is_readable_inside_strict_session_only` | integration | Cross-View Invariants | covered |

final_scoreable: 66
