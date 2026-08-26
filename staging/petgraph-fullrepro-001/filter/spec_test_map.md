# Specification coverage map — petgraph-fullrepro-001

oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary
plus full suite runs on both the patched path and the registry lock;
upstream tests served as a behavioral checklist only — see
rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::generated_add_edge_indices_ascend_parallel_allowed` | atomic | ## Graph Construction and Mutation | covered | add_edge indices ascend; parallel edges allowed |
| `atomic::generated_add_edge_missing_endpoint_panics` | atomic | ## Error Semantics | covered | add_edge with missing endpoint panics |
| `atomic::generated_add_node_indices_ascend` | atomic | ## Graph Construction and Mutation | covered | add_node indices count up from zero |
| `atomic::generated_astar_returns_cost_and_path` | atomic | ## Path Finding and Spanning Trees | covered | astar returns total cost and full path |
| `atomic::generated_astar_unreachable_none` | atomic | ## Path Finding and Spanning Trees | covered | astar None when no goal reachable |
| `atomic::generated_bellman_ford_distances_and_predecessors` | atomic | ## Path Finding and Spanning Trees | covered | Paths distances/predecessors by node position |
| `atomic::generated_bellman_ford_negative_cycle_error` | atomic | ## Error Semantics | covered | bellman_ford Err(NegativeCycle) + positive sibling |
| `atomic::generated_bellman_ford_negative_edge_ok` | atomic | ## Path Finding and Spanning Trees | covered | negative edge without negative cycle supported |
| `atomic::generated_bfs_start_then_layers_in_neighbor_order` | atomic | ## Traversal Visitors and View Adapters | covered | Bfs start first, layers in neighbor order |
| `atomic::generated_clear_and_clear_edges` | atomic | ## Graph Construction and Mutation | covered | clear vs clear_edges |
| `atomic::generated_condensation_acyclic_drops_intra_edges` | atomic | ## Graph Analysis | covered | condensation make_acyclic drops intra edges |
| `atomic::generated_condensation_keeps_all_edges_when_not_acyclic` | atomic | ## Graph Analysis | covered | condensation false preserves every edge |
| `atomic::generated_connected_components_undirected` | atomic | ## Graph Analysis | covered | connected_components on undirected graph |
| `atomic::generated_connected_components_weak_and_isolated` | atomic | ## Graph Analysis | covered | connected_components weak on directed; isolated node |
| `atomic::generated_dfs_move_to_keeps_visit_map` | atomic | ## Traversal Visitors and View Adapters | covered | move_to keeps visit map, no repeats |
| `atomic::generated_dfs_postorder_children_before_parent` | atomic | ## Traversal Visitors and View Adapters | covered | DfsPostOrder children before parent |
| `atomic::generated_dfs_preorder_explores_earliest_edge_first` | atomic | ## Traversal Visitors and View Adapters | covered | Dfs preorder; earliest edge descended first |
| `atomic::generated_dijkstra_costs_and_unreachable_absent` | atomic | ## Path Finding and Spanning Trees | covered | dijkstra cost map; unreachable absent |
| `atomic::generated_dijkstra_with_goal_contains_goal` | atomic | ## Path Finding and Spanning Trees | covered | dijkstra with goal contains goal cost |
| `atomic::generated_direction_opposite` | atomic | ## Indices, Direction, and Adjacency Queries | covered | Direction variants and opposite |
| `atomic::generated_edge_endpoints` | atomic | ## Indices, Direction, and Adjacency Queries | covered | edge_endpoints Some/None |
| `atomic::generated_edge_filtered_from_fn_hides_edges` | atomic | ## Traversal Visitors and View Adapters | covered | EdgeFiltered::from_fn hides failing edges |
| `atomic::generated_edge_index_roundtrip` | atomic | ## Indices, Direction, and Adjacency Queries | covered | EdgeIndex new/index; ordered |
| `atomic::generated_edge_type_reports_directedness` | atomic | ## Indices, Direction, and Adjacency Queries | covered | EdgeType::is_directed on markers and graphs |
| `atomic::generated_edges_connecting_lists_parallel` | atomic | ## Indices, Direction, and Adjacency Queries | covered | edges_connecting newest first; contains_edge |
| `atomic::generated_edges_directed_incoming_sources` | atomic | ## Indices, Direction, and Adjacency Queries | covered | edges_directed Incoming yields sources newest first |
| `atomic::generated_edges_edgeref_accessors` | atomic | ## Indices, Direction, and Adjacency Queries | covered | EdgeRef source/target/id/weight |
| `atomic::generated_extend_with_edges_creates_missing_nodes` | atomic | ## Graph Construction and Mutation | covered | extend_with_edges creates missing nodes with defaults |
| `atomic::generated_externals_by_direction` | atomic | ## Indices, Direction, and Adjacency Queries | covered | externals per direction in index order |
| `atomic::generated_filter_map_drops_edges_only` | atomic | ## Graph Construction and Mutation | covered | filter_map edge closure None drops edge |
| `atomic::generated_filter_map_drops_node_and_reindexes` | atomic | ## Graph Construction and Mutation | covered | filter_map drops node + edges, reindexes compactly |
| `atomic::generated_find_edge_parallel_prefers_most_recent` | atomic | ## Indices, Direction, and Adjacency Queries | covered | find_edge picks most recently added parallel edge |
| `atomic::generated_find_edge_undirected_graph_ignores_order` | atomic | ## Indices, Direction, and Adjacency Queries | covered | find_edge on undirected graph ignores query order |
| `atomic::generated_find_edge_undirected_reports_direction` | atomic | ## Indices, Direction, and Adjacency Queries | covered | find_edge_undirected reports stored direction |
| `atomic::generated_from_edges_builds_graph` | atomic | ## Graph Construction and Mutation | covered | from_edges builder |
| `atomic::generated_from_elements_materializes_tree` | atomic | ## Path Finding and Spanning Trees | covered | from_elements materializes spanning tree |
| `atomic::generated_graphmap_add_edge_implicit_endpoints` | atomic | ## Stable and Keyed Graphs | covered | add_edge inserts missing endpoint keys |
| `atomic::generated_graphmap_add_edge_none_then_replace` | atomic | ## Stable and Keyed Graphs | covered | add_edge None when new, Some(old) on replace |
| `atomic::generated_graphmap_add_node_idempotent` | atomic | ## Stable and Keyed Graphs | covered | GraphMap add_node returns key; re-add no-op |
| `atomic::generated_graphmap_all_edges_in_insertion_order` | atomic | ## Stable and Keyed Graphs | covered | all_edges in edge-insertion order |
| `atomic::generated_graphmap_edge_weight_mut` | atomic | ## Stable and Keyed Graphs | covered | edge_weight between keys + _mut |
| `atomic::generated_graphmap_from_edges` | atomic | ## Stable and Keyed Graphs | covered | GraphMap::from_edges builder |
| `atomic::generated_graphmap_into_graph_insertion_order` | atomic | ## Stable and Keyed Graphs | covered | into_graph: keys become node weights in insertion order |
| `atomic::generated_graphmap_neighbors_directed` | atomic | ## Stable and Keyed Graphs | covered | GraphMap neighbors/neighbors_directed semantics |
| `atomic::generated_graphmap_nodes_in_insertion_order` | atomic | ## Stable and Keyed Graphs | covered | nodes iterate in insertion order |
| `atomic::generated_graphmap_remove_edge_returns_weight` | atomic | ## Stable and Keyed Graphs | covered | remove_edge returns weight; keys remain |
| `atomic::generated_graphmap_remove_node_and_edges` | atomic | ## Stable and Keyed Graphs | covered | remove_node returns presence, drops edges |
| `atomic::generated_graphmap_self_loop` | atomic | ## Stable and Keyed Graphs | covered | GraphMap self-loops allowed |
| `atomic::generated_graphmap_undirected_normalizes_endpoints` | atomic | ## Stable and Keyed Graphs | covered | undirected endpoints normalized smaller-first |
| `atomic::generated_graphmap_undirected_same_edge_both_orders` | atomic | ## Stable and Keyed Graphs | covered | undirected edge identical in both orientations |
| `atomic::generated_has_path_connecting_follows_direction` | atomic | ## Graph Analysis | covered | has_path_connecting follows direction; self-reach |
| `atomic::generated_index_iterators_ascend` | atomic | ## Indices, Direction, and Adjacency Queries | covered | node_indices/edge_indices/edge_references ascend |
| `atomic::generated_index_operator_panics_on_invalid` | atomic | ## Error Semantics | covered | Index impl panics on invalid index |
| `atomic::generated_is_cyclic_directed_detects` | atomic | ## Graph Analysis | covered | is_cyclic_directed detects directed cycle |
| `atomic::generated_is_cyclic_directed_self_loop` | atomic | ## Graph Analysis | covered | self-loop counts as directed cycle |
| `atomic::generated_is_cyclic_undirected` | atomic | ## Graph Analysis | covered | is_cyclic_undirected |
| `atomic::generated_kosaraju_partitions_by_mutual_reachability` | atomic | ## Graph Analysis | covered | kosaraju_scc partitions correctly |
| `atomic::generated_map_preserves_structure` | atomic | ## Graph Construction and Mutation | covered | map produces identical structure with new weights |
| `atomic::generated_min_spanning_tree_element_stream` | atomic | ## Path Finding and Spanning Trees | covered | element stream: nodes then edges of MST |
| `atomic::generated_neighbors_directed_incoming` | atomic | ## Indices, Direction, and Adjacency Queries | covered | neighbors_directed restricts by Direction |
| `atomic::generated_neighbors_missing_node_empty` | atomic | ## Error Semantics | covered | queries on nonexistent nodes yield empty iterators |
| `atomic::generated_neighbors_reverse_insertion_order` | atomic | ## Indices, Direction, and Adjacency Queries | covered | neighbors most-recently-added first |
| `atomic::generated_neighbors_undirected_outgoing_then_incoming` | atomic | ## Indices, Direction, and Adjacency Queries | covered | neighbors_undirected: outgoing first then incoming |
| `atomic::generated_new_graph_empty_and_directedness` | atomic | ## Graph Construction and Mutation | covered | new/new_undirected empty; is_directed |
| `atomic::generated_node_filtered_hides_node_and_edges` | atomic | ## Traversal Visitors and View Adapters | covered | NodeFiltered hides node and touching edges |
| `atomic::generated_node_index_roundtrip_ord_hash` | atomic | ## Indices, Direction, and Adjacency Queries | covered | NodeIndex new/index; ordered + hashable |
| `atomic::generated_remove_edge_swap_relocates_last` | atomic | ## Graph Construction and Mutation | covered | remove_edge swap contract for edge indices |
| `atomic::generated_remove_missing_returns_none` | atomic | ## Error Semantics | covered | remove on missing elements returns None |
| `atomic::generated_remove_node_drops_incident_edges` | atomic | ## Graph Construction and Mutation | covered | remove_node removes incident edges first |
| `atomic::generated_remove_node_swap_relocates_last` | atomic | ## Graph Construction and Mutation | covered | remove_node swap contract: last node adopts index |
| `atomic::generated_retain_edges_keeps_predicate_survivors` | atomic | ## Graph Construction and Mutation | covered | retain_edges removes rejected edges |
| `atomic::generated_retain_nodes_keeps_predicate_survivors` | atomic | ## Graph Construction and Mutation | covered | retain_nodes removes rejected nodes |
| `atomic::generated_reverse_flips_edges` | atomic | ## Graph Construction and Mutation | covered | reverse flips every edge in place |
| `atomic::generated_reversed_neighbors_swapped` | atomic | ## Traversal Visitors and View Adapters | covered | Reversed presents swapped edges to walkers |
| `atomic::generated_scc_postorder_sink_component_first` | atomic | ## Graph Analysis | covered | SCC lists in postorder: sink component first |
| `atomic::generated_self_loop_allowed` | atomic | ## Graph Construction and Mutation | covered | self-loops allowed; neighbor includes self |
| `atomic::generated_stable_counts_and_indices_skip_vacancies` | atomic | ## Stable and Keyed Graphs | covered | counts live-only; iterators skip vacancies |
| `atomic::generated_stable_edge_index_reuse_lifo` | atomic | ## Stable and Keyed Graphs | covered | edge vacancies reused last-freed-first |
| `atomic::generated_stable_node_index_reuse_lifo` | atomic | ## Stable and Keyed Graphs | covered | node vacancies reused last-freed-first |
| `atomic::generated_stable_remove_edge_keeps_other_edge_indices` | atomic | ## Stable and Keyed Graphs | covered | remove_edge leaves other edge indices intact |
| `atomic::generated_stable_remove_keeps_other_indices` | atomic | ## Stable and Keyed Graphs | covered | StableGraph removal invalidates only removed index |
| `atomic::generated_stable_undirected_container` | atomic | ## Stable and Keyed Graphs | covered | StableUnGraph undirected find_edge |
| `atomic::generated_stable_vacancy_accessors` | atomic | ## Stable and Keyed Graphs | covered | vacancy: weight None, contains_node false, Index panics |
| `atomic::generated_tarjan_partitions_by_mutual_reachability` | atomic | ## Graph Analysis | covered | tarjan_scc partitions correctly |
| `atomic::generated_topo_skips_cycle_members` | atomic | ## Traversal Visitors and View Adapters | covered | Topo never yields nodes on cycles |
| `atomic::generated_topo_yields_valid_order` | atomic | ## Traversal Visitors and View Adapters | covered | Topo order satisfies successor rule |
| `atomic::generated_toposort_cycle_error_names_participant` | atomic | ## Error Semantics | covered | toposort Err(Cycle); node_id names participant |
| `atomic::generated_toposort_ok_successor_rule` | atomic | ## Graph Analysis | covered | toposort Ok order satisfies successor rule |
| `atomic::generated_toposort_self_loop_is_cycle` | atomic | ## Error Semantics | covered | toposort self-loop is a cycle |
| `atomic::generated_undirected_neighbors_all_adjacent` | atomic | ## Indices, Direction, and Adjacency Queries | covered | undirected neighbors ignore direction |
| `atomic::generated_update_edge_replaces_or_adds` | atomic | ## Graph Construction and Mutation | covered | update_edge replaces found edge else adds |
| `atomic::generated_visitor_yields_nodes_once_on_diamond` | atomic | ## Traversal Visitors and View Adapters | covered | visit map yields each node at most once |
| `atomic::generated_weight_accessors_and_mut` | atomic | ## Graph Construction and Mutation | covered | node_weight/edge_weight Some/None + _mut |
| `atomic::generated_weight_iterators_in_index_order` | atomic | ## Graph Construction and Mutation | covered | node_weights/edge_weights in index order + _mut |
| `atomic::generated_with_capacity_starts_empty` | atomic | ## Graph Construction and Mutation | covered | with_capacity starts empty |
| `integration::containers::generated_extend_with_edges_then_analysis` | integration | ## State Model | covered | builder feeds analysis: components, toposort, externals |
| `integration::containers::generated_filter_map_matches_hand_built_subgraph` | integration | ## State Model | covered | filter_map projection agrees with hand-built subgraph across queries + algorithms |
| `integration::containers::generated_graph_vs_stable_removal_contract` | integration | ## Cross-View Invariants | covered | CVI 6: swap-remove vs stable removal on identical builds |
| `integration::containers::generated_map_scales_dijkstra_costs` | integration | ## State Model | covered | map transform reflected in algorithm projection |
| `integration::containers::generated_retain_edges_changes_reachability` | integration | ## State Model | covered | retain_edges mutation propagates to reachability and dijkstra |
| `integration::containers::generated_reverse_matches_reversed_view` | integration | ## Cross-View Invariants | covered | in-place reverse equals Reversed view for dijkstra |
| `integration::scc_condensation::generated_condensation_keep_edges_counts` | integration | ## Graph Analysis | covered | edge preservation across both condensation modes |
| `integration::scc_condensation::generated_condensation_partitions_and_toposorts` | integration | ## Cross-View Invariants | covered | CVI 4: condensation acyclic + toposort Ok + partition |
| `integration::scc_condensation::generated_cycle_collapse_enables_toposort` | integration | ## Error Semantics | covered | Cycle error then success after breaking cycles |
| `integration::scc_condensation::generated_scc_invariant_under_reversal` | integration | ## State Model | covered | SCC partition invariant under Reversed adapter |
| `integration::scc_condensation::generated_scc_matches_mutual_reachability` | integration | ## Graph Analysis | covered | same component iff mutual reachability |
| `integration::scc_condensation::generated_scc_partitions_agree` | integration | ## Cross-View Invariants | covered | CVI 4: kosaraju and tarjan partition equally |
| `integration::scc_condensation::generated_scc_postorder_respects_linkage` | integration | ## Graph Analysis | covered | postorder: target component precedes source component |
| `integration::shortest_paths::generated_astar_admissible_heuristic_same_cost` | integration | ## Path Finding and Spanning Trees | covered | admissible heuristic returns minimal cost |
| `integration::shortest_paths::generated_astar_path_is_valid_walk` | integration | ## Path Finding and Spanning Trees | covered | astar path edges exist and sum to total |
| `integration::shortest_paths::generated_astar_zero_heuristic_matches_dijkstra` | integration | ## Cross-View Invariants | covered | CVI 5: astar zero heuristic equals dijkstra per goal |
| `integration::shortest_paths::generated_bellman_ford_agrees_with_dijkstra` | integration | ## Path Finding and Spanning Trees | covered | bellman_ford distances match dijkstra; predecessor chain consistent |
| `integration::shortest_paths::generated_dijkstra_unit_costs_equal_bfs_depth` | integration | ## Cross-View Invariants | covered | CVI 5: unit-cost dijkstra equals BFS depth |
| `integration::shortest_paths::generated_edge_filtered_dijkstra_matches_subgraph` | integration | ## Traversal Visitors and View Adapters | covered | EdgeFiltered dijkstra equals hand-built subgraph |
| `integration::shortest_paths::generated_reachability_views_agree` | integration | ## State Model | covered | dijkstra keys equal has_path_connecting set |
| `integration::spanning_convert::generated_from_elements_stream_reindexes_positions` | integration | ## Path Finding and Spanning Trees | covered | element positions map to emitted node order |
| `integration::spanning_convert::generated_graphmap_and_graph_dijkstra_agree` | integration | ## State Model | covered | keyed and indexed containers agree under dijkstra |
| `integration::spanning_convert::generated_graphmap_into_graph_consistency` | integration | ## Cross-View Invariants | covered | CVI 7: into_graph keys/edges correspond to all_edges |
| `integration::spanning_convert::generated_mst_beats_alternative_spanning_edges` | integration | ## Path Finding and Spanning Trees | covered | MST minimal vs alternative; edges from source |
| `integration::spanning_convert::generated_mst_of_tree_is_identity` | integration | ## Path Finding and Spanning Trees | covered | MST of a tree keeps every edge |
| `integration::spanning_convert::generated_mst_roundtrip_preserves_components` | integration | ## Cross-View Invariants | covered | CVI 8: MST roundtrip components/edges/weight |
| `integration::spanning_convert::generated_stable_graph_algorithms_after_removals` | integration | ## Stable and Keyed Graphs | covered | algorithms over StableGraph with vacancies |
| `integration::traversal::generated_dfs_move_to_covers_forest_without_repeats` | integration | ## Traversal Visitors and View Adapters | covered | move_to across components keeps visit map |
| `integration::traversal::generated_node_filtered_walk_matches_hand_built_subgraph` | integration | ## Traversal Visitors and View Adapters | covered | NodeFiltered walk equals hand-built subgraph walk |
| `integration::traversal::generated_postorder_reversed_is_topological_for_reachable` | integration | ## Traversal Visitors and View Adapters | covered | reversed postorder topological on reachable DAG |
| `integration::traversal::generated_reversed_walk_equals_reachability_set` | integration | ## Cross-View Invariants | covered | CVI 2: reversed walk set equals has_path_connecting set |
| `integration::traversal::generated_topo_walker_and_toposort_agree_on_rule` | integration | ## Cross-View Invariants | covered | CVI 3: Topo and toposort both satisfy successor rule |
| `integration::traversal::generated_visitor_interleaves_with_weight_mutation` | integration | ## Traversal Visitors and View Adapters | covered | walker borrows per step; mutation between steps observed |
| `integration::traversal::generated_walkers_and_dijkstra_agree_on_reachable_set` | integration | ## State Model | covered | walkers and dijkstra project the same reachable set |

Total: 129 | kept (covered): 129 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 129

Layer counts: atomic 95 | integration 34 | system_e2e 0

Upstream disposition (378 upstream test functions, all excluded before
this map — structurally out of scope or out-of-scope imports at file
level) is recorded in rewrite_audit.md; this map covers the generated
oracle only.
