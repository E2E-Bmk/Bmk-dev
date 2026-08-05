# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_uuid_type_coerces_string_to_uuid` | atomic | Scope | covered |
| 2 | `oracle/test_atomic.py::test_uuid_type_round_trips_through_sqlite` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_uuid_type_exposes_binary_storage_option` | atomic | Public Import Surface | covered |
| 4 | `oracle/test_atomic.py::test_url_type_coerces_string_to_furl` | atomic | Scope | covered |
| 5 | `oracle/test_atomic.py::test_url_type_round_trips_as_furl` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_password_type_coerces_secret_to_password` | atomic | Scope | covered |
| 7 | `oracle/test_atomic.py::test_password_type_round_trips_and_verifies_secret` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_choice_type_coerces_code_to_choice` | atomic | Scope | covered |
| 9 | `oracle/test_atomic.py::test_choice_type_round_trips_code_and_label` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_scalar_list_type_coerces_text_items_on_load` | atomic | Scope | covered |
| 11 | `oracle/test_atomic.py::test_scalar_list_type_coerces_integer_items_on_load` | atomic | Scope | covered |
| 12 | `oracle/test_atomic.py::test_json_type_round_trips_nested_data` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_nullable_custom_values_round_trip_as_none` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_choice_type_rejects_unknown_code` | atomic | Error Semantics | covered |
| 15 | `oracle/test_atomic.py::test_scalar_list_type_rejects_separator_in_item` | atomic | Error Semantics | covered |
| 16 | `oracle/test_atomic.py::test_model_table_exposes_public_columns` | atomic | Public Import Surface | covered |
| 17 | `oracle/test_atomic.py::test_get_columns_returns_mapped_columns` | atomic | Cross-View Invariants | covered |
| 18 | `oracle/test_atomic.py::test_get_primary_keys_returns_ordered_primary_key` | atomic | Cross-View Invariants | covered |
| 19 | `oracle/test_atomic.py::test_get_type_handles_column_and_relationship` | atomic | Cross-View Invariants | covered |
| 20 | `oracle/test_atomic.py::test_get_mapper_handles_class_instance_and_table` | atomic | Cross-View Invariants | covered |
| 21 | `oracle/test_atomic.py::test_get_tables_handles_model_and_attribute` | atomic | Cross-View Invariants | covered |
| 22 | `oracle/test_atomic.py::test_table_name_handles_model_and_attribute` | atomic | Cross-View Invariants | covered |
| 23 | `oracle/test_atomic.py::test_get_column_key_resolves_database_column_alias` | atomic | Cross-View Invariants | covered |
| 24 | `oracle/test_atomic.py::test_get_declarative_base_returns_registry_base` | atomic | Cross-View Invariants | covered |
| 25 | `oracle/test_atomic.py::test_get_bind_returns_connection_bind` | atomic | Cross-View Invariants | covered |
| 26 | `oracle/test_atomic.py::test_index_helpers_distinguish_indexed_and_unique_columns` | atomic | Cross-View Invariants | covered |
| 27 | `oracle/test_atomic.py::test_database_exists_accepts_sqlite_memory_urls` | atomic | Scope | covered |
| 28 | `oracle/test_atomic.py::test_escape_like_escapes_wildcards_and_escape_character` | atomic | Scope | covered |
| 29 | `oracle/test_atomic.py::test_identity_and_naturally_equivalent_use_persisted_values` | atomic | Cross-View Invariants | covered |
| 30 | `oracle/test_atomic.py::test_get_class_by_table_finds_declarative_model` | atomic | Cross-View Invariants | covered |
| 31 | `oracle/test_integration.py::test_coercion_types_survive_flush_expire_and_reload` | integration | Representative Workflow | covered |
| 32 | `oracle/test_integration.py::test_uuid_identity_and_primary_key_projection_agree` | integration | Cross-View Invariants | covered |
| 33 | `oracle/test_integration.py::test_url_query_mutation_persists_as_public_url_object` | integration | Representative Workflow | covered |
| 34 | `oracle/test_integration.py::test_password_update_rehashes_and_keeps_row_identity` | integration | Representative Workflow | covered |
| 35 | `oracle/test_integration.py::test_choice_filter_and_projection_agree_after_round_trip` | integration | Cross-View Invariants | covered |
| 36 | `oracle/test_integration.py::test_scalar_lists_update_as_typed_python_collections` | integration | Representative Workflow | covered |
| 37 | `oracle/test_integration.py::test_json_payload_update_is_visible_in_query_and_instance_views` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_nullable_values_can_be_cleared_without_losing_required_values` | integration | Error Semantics | covered |
| 39 | `oracle/test_integration.py::test_model_and_column_inspection_agree_on_schema` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_inspection_reports_scalar_and_relationship_types_together` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_mapper_and_class_lookup_round_trip_through_table` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_bind_helper_matches_engine_used_for_sqlite_queries` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_index_helpers_match_declared_schema_constraints` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_sqlite_file_lifecycle_reports_exists_then_missing` | integration | Representative Workflow | covered |
| 45 | `oracle/test_integration.py::test_sqlite_database_helper_creates_a_usable_file` | integration | Representative Workflow | covered |
| 46 | `oracle/test_integration.py::test_escaped_like_pattern_selects_literal_wildcards` | integration | Representative Workflow | covered |
| 47 | `oracle/test_integration.py::test_natural_equivalence_compares_two_loaded_value_objects` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_deterministic_projection_orders_choice_and_list_values` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_new_model_values_are_coerced_before_session_add` | integration | Product State Model | covered |
| 50 | `oracle/test_integration.py::test_engine_and_session_bind_support_same_round_trip` | integration | Representative Workflow | covered |
| 51 | `oracle/test_integration.py::test_primary_key_and_columns_remain_stable_after_flush` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_file_database_round_trip_preserves_custom_values` | integration | Representative Workflow | covered |
| 53 | `oracle/test_integration.py::test_invalid_choice_does_not_insert_a_partial_row` | integration | Error Semantics | covered |
| 54 | `oracle/test_integration.py::test_scalar_list_validation_keeps_existing_rows_intact` | integration | Error Semantics | covered |
| 55 | `oracle/test_integration.py::test_default_active_value_is_persisted_alongside_custom_types` | integration | Product State Model | covered |
| 56 | `oracle/test_integration.py::test_update_and_reload_preserve_uuid_and_json_contract` | integration | Representative Workflow | covered |
| 57 | `oracle/test_integration.py::test_category_relationship_uses_public_class_and_table_helpers` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_schema_helpers_agree_after_metadata_creation` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_end_to_end_public_utility_workflow` | integration | Representative Workflow | covered |
| 60 | `oracle/test_integration.py::test_connection_bind_and_schema_inspection_share_sqlite_state` | integration | Representative Workflow | covered |

final_scoreable: 60
