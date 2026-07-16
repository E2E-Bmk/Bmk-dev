# NetworkX Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_integration.py::test_product_overview_mutable_graph_node_and_edge_attributes | integration | Product Overview | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_product_overview_graph_is_python_container | integration | Product Overview | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_product_overview_reporting_views_are_live | integration | Product Overview | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_scope_core_graph_classes_are_available | atomic | Scope | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_scope_pure_python_conversion_and_text_are_available | atomic | Scope | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_scope_config_and_exceptions_are_public | atomic | Scope | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_installable_surface_root_exports_graph_classes | atomic | Installable Surface | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_installable_surface_root_exports_conversion_functions | atomic | Installable Surface | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_installable_surface_network_text_and_config_imports | atomic | Installable Surface | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_public_api_root_helper_delegates_to_graph_methods | atomic | Public API | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_public_api_graphviews_module_is_public | atomic | Public API | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_public_api_exception_classes_constructible | atomic | Public API | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_product_state_model_node_projection_coherence | integration | Product State Model | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_product_state_model_edge_projection_coherence | integration | Product State Model | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_product_state_model_attribute_mutation_through_views | integration | Product State Model | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_constructor_empty_and_graph_attrs | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_constructor_loads_incoming_edge_list | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_none_nodes_are_rejected | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_unhashable_membership_returns_false | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_add_node_updates_existing_attrs | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_add_nodes_from_attr_precedence | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_simple_edge_update_does_not_increase_count | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_add_edges_from_attr_precedence_and_invalid_length | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_remove_missing_simple_edge_errors_but_bulk_ignores | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_multigraph_default_keys_lowest_unused | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_multigraph_supplied_key_updates_existing_edge | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_graph_classes_multigraph_remove_edge_without_key_removes_latest | atomic | Graph Classes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_reporting_views_nodes_data_and_default | atomic | Reporting Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_reporting_views_node_view_is_read_only_mapping_shell | atomic | Reporting Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_reporting_views_simple_edges_data_and_default | atomic | Reporting Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_reporting_views_multigraph_edges_keys_and_duplicate_pairs | atomic | Reporting Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_reporting_views_adjacency_projection_matches_getitem | atomic | Reporting Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_reporting_views_degree_unweighted_weighted_and_self_loop | atomic | Reporting Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_reporting_views_directed_successor_predecessor_and_degree | atomic | Reporting Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_copying_subgraphs_copy_is_independent | integration | Copying, Subgraphs, And Graph Type Conversion | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_copying_subgraphs_copy_as_view_is_readonly_and_live | integration | Copying, Subgraphs, And Graph Type Conversion | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_copying_subgraphs_node_induced_subgraph_shares_attrs | integration | Copying, Subgraphs, And Graph Type Conversion | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_copying_subgraphs_edge_subgraph_filters_edges_and_shares_attrs | integration | Copying, Subgraphs, And Graph Type Conversion | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_copying_subgraphs_to_directed_copies_attrs_and_arcs | integration | Copying, Subgraphs, And Graph Type Conversion | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_copying_subgraphs_to_undirected_reciprocal_keeps_mutual_edges | integration | Copying, Subgraphs, And Graph Type Conversion | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_copying_subgraphs_as_view_conversion_is_readonly_live | integration | Copying, Subgraphs, And Graph Type Conversion | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_public_helper_functions_add_path_star_cycle_edge_cases | atomic | Public Helper Functions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_public_helper_functions_attribute_set_get_ignore_missing_nodes | atomic | Public Helper Functions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_public_helper_functions_attribute_set_get_ignore_missing_edges | atomic | Public Helper Functions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_public_helper_functions_freeze_blocks_structure_not_attrs | atomic | Public Helper Functions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_conversions_to_networkx_graph_clears_supplied_instance | integration | Conversions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_conversions_from_graph_preserves_attrs_and_multikeys | integration | Conversions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_conversions_dict_of_lists_round_trip_and_nodelist_filter | integration | Conversions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_conversions_dict_of_dicts_round_trip_simple_and_multigraph | integration | Conversions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_conversions_to_dict_of_dicts_scalar_edge_data_omits_multikeys | integration | Conversions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_conversions_edgelist_round_trip_and_invalid_tuple_error | integration | Conversions | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_graph_views_generic_view_is_frozen_shared_and_live | integration | Graph Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_graph_views_subgraph_view_filters_nodes_and_edges | integration | Graph Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_graph_views_subgraph_view_filter_exceptions_propagate | integration | Graph Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_graph_views_multigraph_edge_filter_receives_key | integration | Graph Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_graph_views_reverse_view_reverses_directed_edges_and_rejects_undirected | integration | Graph Views | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_network_text_empty_graph_and_ascii_root | atomic | Network Text | covered | Track B public API verifier; exact text assertion is specified or derivable from spec_v2 Network Text |
| oracle/test_atomic.py::test_network_text_max_depth_zero_uses_ellipsis | atomic | Network Text | covered | Track B public API verifier; setup uses nx.Graph plus nx.add_path per spec_v2; exact output is specified by Network Text |
| oracle/test_atomic.py::test_network_text_sources_limit_displayed_component | atomic | Network Text | covered | Track B public API verifier; exact text assertion is specified or derivable from spec_v2 Network Text |
| oracle/test_atomic.py::test_network_text_labels_collapse_and_ascii_observed_output | atomic | Network Text | covered | Track B public API verifier; exact text assertion is specified or derivable from spec_v2 Network Text |
| oracle/test_atomic.py::test_network_text_with_labels_named_attribute_and_false | atomic | Network Text | covered | Track B public API verifier; exact text assertion is specified or derivable from spec_v2 Network Text |
| oracle/test_atomic.py::test_network_text_write_to_file_like_callable_and_stdout | atomic | Network Text | covered | Track B public API verifier; exact text assertion is specified or derivable from spec_v2 Network Text |
| oracle/test_atomic.py::test_network_text_invalid_path_raises_type_error | atomic | Network Text | covered | Track B public API verifier; exact text assertion is specified or derivable from spec_v2 Network Text |
| oracle/test_atomic.py::test_config_flexible_mapping_semantics | atomic | Config | covered | Track B public API verifier; Config behavior matches spec_v2 public mapping/context contract |
| oracle/test_atomic.py::test_config_strict_annotations_reject_unknown_keys | atomic | Config | covered | Track B public API verifier; Config behavior matches spec_v2 public mapping/context contract |
| oracle/test_atomic.py::test_config_strict_deletion_errors_and_flexible_deletion | atomic | Config | covered | Track B public API verifier; Config behavior matches spec_v2 public mapping/context contract |
| oracle/test_atomic.py::test_config_context_manager_restores_values_and_rejects_uncalled_enter | atomic | Config | covered | Track B public API verifier; Config behavior matches spec_v2 public mapping/context contract |
| oracle/test_atomic.py::test_config_global_networkx_config_validates_assignment_types | atomic | Config | covered | Track B public API verifier; Config behavior matches spec_v2 public mapping/context contract |
| oracle/test_atomic.py::test_error_semantics_public_exceptions_share_base_class | atomic | Error Semantics | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_error_semantics_missing_nodes_and_edges_use_documented_classes | atomic | Error Semantics | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_error_semantics_directed_missing_neighbor_methods_raise_networkxerror | atomic | Error Semantics | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_error_semantics_power_iteration_exception_is_specific | atomic | Error Semantics | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_error_semantics_missing_mapping_view_keys_raise_key_error | atomic | Error Semantics | covered | Track B public API verifier; missing mapping-view keys use public KeyError semantics |
| oracle/test_integration.py::test_cross_view_invariant_node_removed_from_all_public_views | integration | Cross-View Invariants | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_cross_view_invariant_simple_edge_attribute_paths_agree | integration | Cross-View Invariants | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_cross_view_invariant_multigraph_edge_attribute_paths_agree | integration | Cross-View Invariants | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_cross_view_invariant_directed_edge_public_projections_agree | integration | Cross-View Invariants | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_cross_view_invariant_plain_conversion_snapshots_are_not_live | integration | Cross-View Invariants | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_integration.py::test_representative_workflow_multidigraph_routes_and_red_view | system_e2e | Representative Workflows | covered | Track B public API verifier; workflow assertion is derivable from spec_v2 Representative Workflows |
| oracle/test_integration.py::test_representative_workflow_filtered_view_copy_and_text | system_e2e | Representative Workflows | covered | Track B public API verifier; workflow assertion is derivable from spec_v2 Representative Workflows |
| oracle/test_integration.py::test_representative_workflow_conversion_roundtrip_preserves_public_state | system_e2e | Representative Workflows | covered | Track B public API verifier; workflow assertion is derivable from spec_v2 Representative Workflows |
| oracle/test_atomic.py::test_non_goals_core_graph_behavior_does_not_require_algorithm_catalogue | atomic | Non-Goals | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_non_goals_pure_python_conversion_does_not_require_optional_numeric_types | atomic | Non-Goals | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_non_goals_behavioral_views_without_repr_contract | atomic | Non-Goals | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_evaluation_notes_public_imports_only_workflow | atomic | Evaluation Notes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_evaluation_notes_no_private_storage_needed_for_attribute_checks | atomic | Evaluation Notes | covered | Track B public API verifier; assertion uses public behavior only |
| oracle/test_atomic.py::test_evaluation_notes_error_paths_use_public_exception_types | atomic | Evaluation Notes | covered | Track B public API verifier; assertion uses public behavior only |

Total: 87 | kept (covered): 87 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 87
