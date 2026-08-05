# Specification Test Map

Every physical test listed below is covered by the public behavior specification.

| Test | Layer | Spec Area | Status |
| --- | --- | --- | --- |
| `oracle/test_atomic.py::test_public_imports_expose_requested_surface` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_node_stores_name_and_extra_attributes` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_anynode_stores_arbitrary_attributes` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_nodemixin_adds_tree_behavior_to_user_class` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_lightnodemixin_supports_slots_and_tree_behavior` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_parent_assignment_reattaches_and_preserves_identity` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_parent_none_detaches_node` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_children_assignment_reorders_and_detaches_old_children` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_children_deleter_detaches_all_children` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_path_and_reverse_path_have_opposite_order` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_relationship_properties_report_tree_membership` | atomic | Cross-View Invariants | covered |
| `oracle/test_atomic.py::test_leaf_root_height_depth_and_size_properties` | atomic | Cross-View Invariants | covered |
| `oracle/test_atomic.py::test_self_parent_is_rejected_with_loop_error` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_descendant_parent_is_rejected_with_loop_error` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_non_node_parent_is_rejected_with_tree_error` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_duplicate_children_are_rejected_with_tree_error` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_children_assignment_rolls_back_after_attach_failure` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_preorder_iterator_is_depth_first` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_postorder_iterator_visits_children_before_parent` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_levelorder_iterator_is_breadth_first` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_levelorder_group_iterator_groups_by_depth` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_zigzag_group_iterator_reverses_alternating_levels` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_iterator_filter_stop_and_maxlevel_are_composable` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_findall_returns_matching_nodes_in_preorder` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_find_by_attr_and_findall_by_attr_use_named_attributes` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_search_count_constraints_raise_count_error` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_resolver_get_handles_relative_and_absolute_paths` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_resolver_glob_matches_single_level_wildcards` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_render_tree_rows_expose_prefix_fill_and_nodes` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_render_by_attr_uses_semantic_node_values` | atomic | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_mutation_workflow_recomputes_paths_and_sizes` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_anynode_dict_export_preserves_attributes_and_shape` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_json_export_roundtrip_is_verified_from_parsed_data` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_dict_importer_builds_custom_node_class_and_parent_links` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_json_file_like_write_and_read_preserve_tree_values` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_dict_exporter_can_filter_attributes_and_children` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_exporter_maxlevel_limits_nested_children` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_resolver_custom_path_attribute_survives_tree_navigation` | integration | Public Import Surface | covered |
| `oracle/test_integration.py::test_resolver_ignorecase_and_relax_change_lookup_policy` | integration | Error Semantics | covered |
| `oracle/test_integration.py::test_resolver_recursive_glob_finds_nested_matches_once` | integration | Public Import Surface | covered |
| `oracle/test_integration.py::test_render_child_order_can_be_reversed_without_mutating_tree` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_render_multiline_attribute_uses_fill_for_continuation_lines` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_render_maxlevel_keeps_requested_depth_only` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_node_mixin_hooks_observe_attach_and_detach_workflow` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_light_node_mixin_tree_can_be_exported_with_public_attributes` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_search_and_resolver_follow_a_reparented_subtree` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_detach_mutate_reattach_and_export_is_consistent` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_children_reordering_updates_paths_without_recreating_nodes` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_custom_mixin_nodes_and_anynodes_can_share_one_tree` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_filtered_iteration_and_filtered_export_agree_on_selected_children` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_sorted_child_workflow_has_matching_render_and_breadth_order` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_json_sort_keys_is_a_serialization_option_not_a_tree_order_change` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_custom_dict_class_receives_exported_attribute_pairs` | integration | Public Import Surface | covered |
| `oracle/test_integration.py::test_imported_tree_can_be_mutated_then_reexported` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_resolver_glob_reflects_order_after_children_replacement` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_leaf_properties_and_postorder_agree_after_growth` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_grouped_iterator_views_share_the_same_level_membership` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_custom_attribute_tree_roundtrips_through_json_and_resolver` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_render_workflow_keeps_row_nodes_and_attribute_projection_aligned` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_custom_mixin_workflow_reparents_and_searches_by_domain_field` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_search_cardinality_and_export_state_remain_consistent_after_mutation` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_full_public_workflow_mutates_exports_resolves_and_renders` | integration | Representative Workflow | covered |

final_scoreable: 62
