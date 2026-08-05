# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_metamodel_from_str_parses_minimal_project` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_model_from_str_projects_single_value_fields` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_repeated_state_order_is_preserved` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_boolean_assignment_sets_true_and_false` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_integer_terminal_converts_event_codes` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_string_terminal_unquotes_message` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_abstract_action_instantiates_send_variant` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_abstract_action_instantiates_log_variant` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_state_references_resolve_to_named_objects` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_event_reference_resolves_to_named_object` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_get_children_of_type_returns_contained_states` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_get_children_predicate_can_select_events` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_children_first_traversal_places_root_after_children` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_get_parent_of_type_finds_workflow_for_transition` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_get_model_returns_root_for_nested_action` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_get_metamodel_returns_originating_metamodel` | atomic | Product State Model | covered |
| 17 | `oracle/test_atomic.py::test_get_location_exposes_public_position_keys` | atomic | Product State Model | covered |
| 18 | `oracle/test_atomic.py::test_textx_isinstance_accepts_dynamic_rule_class` | atomic | Public Import Surface | covered |
| 19 | `oracle/test_atomic.py::test_invalid_syntax_raises_public_syntax_error` | atomic | Error Semantics | covered |
| 20 | `oracle/test_atomic.py::test_unresolved_reference_raises_public_semantic_error` | atomic | Error Semantics | covered |
| 21 | `oracle/test_atomic.py::test_object_processor_receives_completed_object` | atomic | Cross-Component Invariants | covered |
| 22 | `oracle/test_atomic.py::test_object_processor_can_add_public_derived_attribute` | atomic | Cross-Component Invariants | covered |
| 23 | `oracle/test_atomic.py::test_model_processor_receives_completed_model_and_metamodel` | atomic | Cross-Component Invariants | covered |
| 24 | `oracle/test_atomic.py::test_object_processor_return_replaces_public_object_value` | atomic | Cross-Component Invariants | covered |
| 25 | `oracle/test_atomic.py::test_custom_scope_provider_can_resolve_case_insensitive_reference` | atomic | Cross-Component Invariants | covered |
| 26 | `oracle/test_atomic.py::test_metamodel_from_file_uses_local_grammar_file` | atomic | Cross-Component Invariants | covered |
| 27 | `oracle/test_atomic.py::test_registration_error_is_public_exception` | atomic | Error Semantics | covered |
| 28 | `oracle/test_atomic.py::test_metamodel_rule_lookup_exposes_dynamic_rule_class` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_ignore_case_accepts_keyword_case_without_changing_identifier` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_custom_user_class_receives_parent_and_typed_values` | atomic | Product State Model | covered |
| 31 | `oracle/test_atomic.py::test_model_from_str_file_name_projects_public_location_filename` | atomic | Product State Model | covered |
| 32 | `oracle/test_integration.py::test_file_based_model_preserves_values_and_filename` | integration | Cross-Component Invariants | covered |
| 33 | `oracle/test_integration.py::test_model_from_file_and_str_share_object_graph_projection` | integration | Cross-Component Invariants | covered |
| 34 | `oracle/test_integration.py::test_metamodel_dot_export_contains_model_classes` | integration | Cross-Component Invariants | covered |
| 35 | `oracle/test_integration.py::test_metamodel_plantuml_export_contains_action_variants` | integration | Cross-Component Invariants | covered |
| 36 | `oracle/test_integration.py::test_model_dot_export_contains_runtime_values` | integration | Cross-Component Invariants | covered |
| 37 | `oracle/test_integration.py::test_language_registration_finds_pattern_and_parses_file` | integration | Cross-Component Invariants | covered |
| 38 | `oracle/test_integration.py::test_languages_for_file_returns_all_matching_public_descriptors` | integration | Scope | covered |
| 39 | `oracle/test_integration.py::test_metamodel_for_file_uses_registered_language` | integration | Scope | covered |
| 40 | `oracle/test_integration.py::test_processors_and_children_projection_share_event_order` | integration | Cross-Component Invariants | covered |
| 41 | `oracle/test_integration.py::test_processor_derived_event_values_are_visible_through_references` | integration | Cross-Component Invariants | covered |
| 42 | `oracle/test_integration.py::test_custom_scope_provider_combines_with_default_target_resolution` | integration | Cross-Component Invariants | covered |
| 43 | `oracle/test_integration.py::test_invalid_model_does_not_prevent_independent_metamodel_export` | integration | Error Semantics | covered |
| 44 | `oracle/test_integration.py::test_state_parent_links_and_child_collection_agree` | integration | Product State Model | covered |
| 45 | `oracle/test_integration.py::test_nested_action_projects_root_and_metamodel` | integration | Product State Model | covered |
| 46 | `oracle/test_integration.py::test_should_follow_limits_containment_traversal` | integration | Scope | covered |
| 47 | `oracle/test_integration.py::test_plantuml_export_and_runtime_model_share_rule_names` | integration | Cross-Component Invariants | covered |
| 48 | `oracle/test_integration.py::test_file_model_export_keeps_same_public_transition_names` | integration | Cross-Component Invariants | covered |
| 49 | `oracle/test_integration.py::test_generator_registration_uses_parsed_model_projection` | integration | Cross-Component Invariants | covered |
| 50 | `oracle/test_integration.py::test_any_generator_fallback_uses_public_generator_lookup` | integration | Cross-Component Invariants | covered |
| 51 | `oracle/test_integration.py::test_duplicate_language_registration_raises_without_altering_first_entry` | integration | Cross-Component Invariants | covered |
| 52 | `oracle/test_integration.py::test_duplicate_generator_registration_keeps_first_generator` | integration | Cross-Component Invariants | covered |
| 53 | `oracle/test_integration.py::test_cross_references_are_not_duplicated_by_containment_traversal` | integration | Product State Model | covered |
| 54 | `oracle/test_integration.py::test_action_variants_share_transition_projection` | integration | Scope | covered |
| 55 | `oracle/test_integration.py::test_state_flags_and_order_survive_file_round_trip` | integration | Cross-Component Invariants | covered |
| 56 | `oracle/test_integration.py::test_locations_align_with_project_and_transition_lines` | integration | Product State Model | covered |
| 57 | `oracle/test_integration.py::test_processor_can_raise_public_semantic_error_for_model_policy` | integration | Error Semantics | covered |
| 58 | `oracle/test_integration.py::test_cli_check_accepts_grammar_and_valid_model` | integration | Representative Workflow | covered |
| 59 | `oracle/test_integration.py::test_cli_check_rejects_invalid_model` | integration | Representative Workflow | covered |
| 60 | `oracle/test_integration.py::test_cli_check_validates_a_grammar_file` | integration | Representative Workflow | covered |

final_scoreable: 60
