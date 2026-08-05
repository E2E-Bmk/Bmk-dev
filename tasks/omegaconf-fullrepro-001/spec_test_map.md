# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_create_empty_dict_config` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_create_list_config_preserves_nested_values` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_create_yaml_string_parses_scalars` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_attribute_and_item_access_agree` | atomic | Public Import Surface | covered |
| 5 | `oracle/test_atomic.py::test_default_get_returns_fallback` | atomic | Public Import Surface | covered |
| 6 | `oracle/test_atomic.py::test_missing_sentinel_is_reported_publicly` | atomic | Validation And Error Reporting | covered |
| 7 | `oracle/test_atomic.py::test_interpolation_resolves_lazily` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_is_interpolation_and_is_config_views` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_from_dotlist_builds_nested_paths` | atomic | Scope | covered |
| 10 | `oracle/test_atomic.py::test_from_dotlist_escapes_literal_key_delimiters` | atomic | Scope | covered |
| 11 | `oracle/test_atomic.py::test_from_cli_accepts_explicit_arguments` | atomic | Scope | covered |
| 12 | `oracle/test_atomic.py::test_select_supports_dot_and_bracket_paths` | atomic | Public Import Surface | covered |
| 13 | `oracle/test_atomic.py::test_select_returns_default_for_absent_path` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_can_select_distinguishes_missing_and_none` | atomic | Validation And Error Reporting | covered |
| 15 | `oracle/test_atomic.py::test_update_changes_scalar_path` | atomic | Cross-Component Invariants | covered |
| 16 | `oracle/test_atomic.py::test_update_merges_or_replaces_mapping` | atomic | Cross-Component Invariants | covered |
| 17 | `oracle/test_atomic.py::test_merge_replaces_lists_by_default` | atomic | Cross-Component Invariants | covered |
| 18 | `oracle/test_atomic.py::test_merge_extends_lists_with_public_mode` | atomic | Cross-Component Invariants | covered |
| 19 | `oracle/test_atomic.py::test_merge_extends_unique_lists` | atomic | Cross-Component Invariants | covered |
| 20 | `oracle/test_atomic.py::test_structured_creates_dictconfig_and_type` | atomic | Product State Model | covered |
| 21 | `oracle/test_atomic.py::test_structured_coerces_assignable_scalar` | atomic | Product State Model | covered |
| 22 | `oracle/test_atomic.py::test_structured_rejects_invalid_scalar_type` | atomic | Validation And Error Reporting | covered |
| 23 | `oracle/test_atomic.py::test_structured_optional_accepts_none` | atomic | Product State Model | covered |
| 24 | `oracle/test_atomic.py::test_structured_missing_field_requires_assignment` | atomic | Validation And Error Reporting | covered |
| 25 | `oracle/test_atomic.py::test_set_struct_reports_state_and_blocks_new_key` | atomic | Validation And Error Reporting | covered |
| 26 | `oracle/test_atomic.py::test_open_dict_temporarily_allows_new_keys` | atomic | Product State Model | covered |
| 27 | `oracle/test_atomic.py::test_set_readonly_blocks_mutation` | atomic | Validation And Error Reporting | covered |
| 28 | `oracle/test_atomic.py::test_read_write_temporarily_allows_mutation` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_to_container_preserves_unresolved_and_resolves_option` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_to_object_instantiates_structured_dataclass` | atomic | Product State Model | covered |
| 31 | `oracle/test_atomic.py::test_to_yaml_emits_sorted_yaml_projection` | atomic | Cross-Component Invariants | covered |
| 32 | `oracle/test_atomic.py::test_register_resolver_evaluates_and_has_resolver` | atomic | Product State Model | covered |
| 33 | `oracle/test_atomic.py::test_save_and_load_path_round_trip` | atomic | Cross-Component Invariants | covered |
| 34 | `oracle/test_atomic.py::test_save_accepts_file_object` | atomic | Scope | covered |
| 35 | `oracle/test_integration.py::test_dotlist_to_merge_to_select_pipeline` | integration | Representative Workflows | covered |
| 36 | `oracle/test_integration.py::test_cli_override_merges_with_base_config` | integration | Representative Workflows | covered |
| 37 | `oracle/test_integration.py::test_yaml_string_round_trip_preserves_interpolation_projection` | integration | Cross-Component Invariants | covered |
| 38 | `oracle/test_integration.py::test_save_load_file_object_and_path_agree` | integration | Cross-Component Invariants | covered |
| 39 | `oracle/test_integration.py::test_yaml_flow_style_and_sorted_keys_are_public_options` | integration | Scope | covered |
| 40 | `oracle/test_integration.py::test_yaml_load_list_root_round_trips_as_list_config` | integration | Product State Model | covered |
| 41 | `oracle/test_integration.py::test_merge_structured_schema_validates_plain_yaml` | integration | Cross-Component Invariants | covered |
| 42 | `oracle/test_integration.py::test_merge_structured_schema_rejects_wrong_type` | integration | Validation And Error Reporting | covered |
| 43 | `oracle/test_integration.py::test_structured_nested_to_container_modes_agree` | integration | Cross-Component Invariants | covered |
| 44 | `oracle/test_integration.py::test_to_object_resolves_structured_interpolation` | integration | Cross-Component Invariants | covered |
| 45 | `oracle/test_integration.py::test_structured_list_and_dict_types_validate_updates` | integration | Validation And Error Reporting | covered |
| 46 | `oracle/test_integration.py::test_structured_literal_and_enum_values_round_trip` | integration | Product State Model | covered |
| 47 | `oracle/test_integration.py::test_readonly_and_struct_flags_interact_with_contexts` | integration | Representative Workflows | covered |
| 48 | `oracle/test_integration.py::test_update_force_add_respects_struct_context` | integration | Cross-Component Invariants | covered |
| 49 | `oracle/test_integration.py::test_select_and_update_share_escaped_key_paths` | integration | Cross-Component Invariants | covered |
| 50 | `oracle/test_integration.py::test_missing_keys_matches_nested_plain_and_list_values` | integration | Product State Model | covered |
| 51 | `oracle/test_integration.py::test_missing_keys_follows_node_interpolations` | integration | Cross-Component Invariants | covered |
| 52 | `oracle/test_integration.py::test_resolve_and_to_container_views_agree` | integration | Cross-Component Invariants | covered |
| 53 | `oracle/test_integration.py::test_relative_interpolations_follow_nested_scope` | integration | Product State Model | covered |
| 54 | `oracle/test_integration.py::test_nested_interpolation_reselects_after_source_change` | integration | Product State Model | covered |
| 55 | `oracle/test_integration.py::test_custom_resolver_variadic_and_nested_arguments` | integration | Representative Workflows | covered |
| 56 | `oracle/test_integration.py::test_custom_resolver_cache_reuses_literal_arguments` | integration | Product State Model | covered |
| 57 | `oracle/test_integration.py::test_custom_resolver_replace_and_clear_lifecycle` | integration | Scope | covered |
| 58 | `oracle/test_integration.py::test_custom_resolver_parent_context_reads_sibling` | integration | Public Import Surface | covered |
| 59 | `oracle/test_integration.py::test_builtin_select_resolver_supplies_default` | integration | Product State Model | covered |
| 60 | `oracle/test_integration.py::test_builtin_decode_resolver_parses_scalar_and_list` | integration | Product State Model | covered |
| 61 | `oracle/test_integration.py::test_builtin_create_resolver_returns_config_container` | integration | Product State Model | covered |
| 62 | `oracle/test_integration.py::test_builtin_dict_resolvers_project_keys_and_values` | integration | Cross-Component Invariants | covered |
| 63 | `oracle/test_integration.py::test_escaped_interpolation_literal_is_not_resolved` | integration | Product State Model | covered |
| 64 | `oracle/test_integration.py::test_merged_config_serialization_matches_public_views` | integration | Representative Workflows | covered |

final_scoreable: 64
