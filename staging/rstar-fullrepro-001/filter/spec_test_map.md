# Specification coverage map — rstar-fullrepro-001


oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
three probe rounds during spec drafting, then full-suite runs on both the
patched path and the registry lock; upstream tests served as a behavioral
checklist only — see rewrite_audit.md).

Test IDs are `{crate}::{function}` as reported by cargo-nextest against
the oracle workspace.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| `atomic::generated_from_point_zero_extent` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | from_point: lower=upper=p, zero area, contains only p |
| `atomic::generated_from_corners_normalizes_in_any_order` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | corner order irrelevant; lower=min, upper=max; equality |
| `atomic::generated_from_points_folds_smallest_box` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | smallest box containing an iterator of points |
| `atomic::generated_from_points_empty_equals_new_empty` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | empty iterator folds to new_empty |
| `atomic::generated_new_empty_merge_identity` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | empty envelope: zero area, contains nothing, merge identity |
| `atomic::generated_contains_point_inclusive_boundaries` | atomic | both | ## Envelopes and AABB Arithmetic | covered | interior/corner/face contained; outside not |
| `atomic::generated_contains_envelope_boundaries_included` | atomic | both | ## Envelopes and AABB Arithmetic | covered | shared-face containment; self-containment; overhang rejected |
| `atomic::generated_intersects_inclusive_touch` | atomic | both | ## Envelopes and AABB Arithmetic | covered | corner/face touch intersect; disjoint does not |
| `atomic::generated_merge_grows_in_place_and_by_copy` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | merge mutates, merged copies |
| `atomic::generated_area_and_intersection_area` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | side product; overlap area; touch/disjoint clamp to zero |
| `atomic::generated_center_and_perimeter_value` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | componentwise midpoint; side-length sum = 7 example |
| `atomic::generated_min_point_clamps_and_distance_2` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | clamp outside, identity inside, squared distances |
| `atomic::generated_min_max_dist_matches_corner_distance` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | min-max bound equals distance to the min-max corner |
| `atomic::generated_value_semantics_eq_ord_hash` | atomic | positive | ## Envelopes and AABB Arithmetic | covered | Eq over normalized corners; Ord/Hash over integer scalar |
| `atomic::generated_new_tree_is_empty` | atomic | both | ## Tree Construction and Population | covered | new/default: size 0, no elements, nearest None |
| `atomic::generated_bulk_load_exact_content` | atomic | positive | ## Tree Construction and Population | covered | bulk_load keeps exact multiset incl. duplicates |
| `atomic::generated_bulk_load_empty_vector` | atomic | positive | ## Tree Construction and Population | covered | bulk load of empty vector is an empty tree |
| `atomic::generated_insert_increments_and_duplicates_accumulate` | atomic | positive | ## Tree Construction and Population | covered | size +1 per insert; duplicates all locatable |
| `atomic::generated_contains_by_equality` | atomic | both | ## Tree Construction and Population | covered | contains via ==; near-miss rejected |
| `atomic::generated_iteration_by_ref_and_by_value` | atomic | positive | ## Tree Construction and Population | covered | (&tree).into_iter and consuming into_iter |
| `atomic::generated_iter_mut_updates_payload` | atomic | positive | ## Tree Construction and Population | covered | iter_mut mutates non-spatial payloads in place |
| `atomic::generated_custom_params_do_not_change_answers` | atomic | positive | ## Tree Construction and Population | covered | custom RTreeParams: identical query results |
| `atomic::generated_params_panic_max_below_four` | atomic | failure_path | ## Error Semantics | covered | MAX_SIZE < 4 panics at construction |
| `atomic::generated_params_panic_min_zero` | atomic | failure_path | ## Error Semantics | covered | MIN_SIZE = 0 panics at construction |
| `atomic::generated_params_panic_min_above_half_max` | atomic | failure_path | ## Error Semantics | covered | MIN_SIZE > (MAX+1)/2 panics at construction |
| `atomic::generated_params_panic_reinsertion_count` | atomic | failure_path | ## Error Semantics | covered | REINSERTION_COUNT >= MAX-MIN panics at construction |
| `atomic::generated_dimension_below_two_panics` | atomic | failure_path | ## Error Semantics | covered | 1-dimensional point type panics at construction |
| `atomic::generated_construction_path_equivalence` | atomic | positive | ## Tree Construction and Population | covered | bulk vs incremental: equal multisets and distance sequences |
| `atomic::generated_locate_at_point_exact_equality` | atomic | both | ## Spatial Queries | covered | bare points: containment is exact coordinate equality |
| `atomic::generated_locate_all_at_point_with_duplicates` | atomic | positive | ## Spatial Queries | covered | all containing elements, duplicates counted |
| `atomic::generated_locate_at_point_mut_updates_payload` | atomic | positive | ## Spatial Queries | covered | _mut point location mutates payload in place |
| `atomic::generated_locate_in_envelope_inclusive_corners` | atomic | positive | ## Spatial Queries | covered | full containment, boundary points included (workflow example) |
| `atomic::generated_locate_in_envelope_intersecting_includes_touch` | atomic | positive | ## Spatial Queries | covered | touching envelopes selected; contained subset relation |
| `atomic::generated_locate_within_distance_inclusive` | atomic | positive | ## Spatial Queries | covered | inclusive squared-distance boundary at 4.0 |
| `atomic::generated_internal_iteration_break_and_continue` | atomic | positive | ## Spatial Queries | covered | ControlFlow protocol: Break stops, Continue visits all |
| `atomic::generated_locate_at_point_int_returns_option` | atomic | both | ## Spatial Queries | covered | _int point location returns Option directly |
| `atomic::generated_custom_selection_function` | atomic | positive | ## Spatial Queries | covered | SelectionFunction parent+leaf hooks drive selection |
| `atomic::generated_custom_selection_function_mut` | atomic | positive | ## Spatial Queries | covered | default leaf hook accepts all; _mut variant mutates |
| `atomic::generated_intersection_candidates_same_type` | atomic | positive | ## Spatial Queries | covered | cross-tree pairs on zero-extent point envelopes |
| `atomic::generated_intersection_candidates_cross_type` | atomic | positive | ## Spatial Queries | covered | differing element types over one envelope type |
| `atomic::generated_nearest_neighbor_basic_and_empty` | atomic | both | ## Nearest-Neighbor Queries | covered | minimal-distance element; empty tree None |
| `atomic::generated_nearest_neighbor_tie_returns_member` | atomic | positive | ## Nearest-Neighbor Queries | covered | tie: any member of the tie set |
| `atomic::generated_nearest_neighbors_full_tie_set` | atomic | both | ## Nearest-Neighbor Queries | covered | all equally-nearest elements; empty vector on empty tree |
| `atomic::generated_nearest_neighbors_construction_independent` | atomic | positive | ## Nearest-Neighbor Queries | covered | tie set does not depend on construction path |
| `atomic::generated_nearest_neighbor_iter_nondecreasing` | atomic | positive | ## Nearest-Neighbor Queries | covered | exact nondecreasing distance sequence; all elements once |
| `atomic::generated_nearest_neighbor_iter_distance_agrees` | atomic | positive | ## Nearest-Neighbor Queries | covered | reported distance equals element distance_2; first = minimum |
| `atomic::generated_deprecated_distance_alias_same_contract` | atomic | positive | ## Nearest-Neighbor Queries | covered | deprecated _with_distance alias, identical contract |
| `atomic::generated_pop_nearest_neighbor_removes_in_order` | atomic | both | ## Nearest-Neighbor Queries | covered | repeated popping drains in nondecreasing order; None at end |
| `atomic::generated_pop_nearest_neighbor_tie_removes_one` | atomic | positive | ## Nearest-Neighbor Queries | covered | tie: exactly one member removed, other survives |
| `atomic::generated_remove_one_of_many` | atomic | both | ## Mutation and Removal | covered | duplicates removed one per call until None |
| `atomic::generated_remove_no_match_leaves_tree_unchanged` | atomic | both | ## Error Semantics | covered | failed removal: None, tree unchanged |
| `atomic::generated_remove_at_point` | atomic | both | ## Mutation and Removal | covered | removal by contained point; second call None |
| `atomic::generated_remove_with_selection_function` | atomic | both | ## Mutation and Removal | covered | one element accepted by the predicate; no-match None |
| `atomic::generated_drain_everything` | atomic | positive | ## Mutation and Removal | covered | drain() empties the tree, returns all by value |
| `atomic::generated_drain_in_envelope_only_contained` | atomic | positive | ## Mutation and Removal | covered | drains contained elements only |
| `atomic::generated_drain_in_envelope_intersecting` | atomic | positive | ## Mutation and Removal | covered | drains touching envelopes too |
| `atomic::generated_drain_within_distance_inclusive` | atomic | positive | ## Mutation and Removal | covered | inclusive squared-distance boundary drained |
| `atomic::generated_drain_is_lazy` | atomic | positive | ## Mutation and Removal | covered | dropped iterator removed only the yielded element |
| `atomic::generated_drain_with_selection_function` | atomic | positive | ## Mutation and Removal | covered | drains exactly the predicate-selected elements |
| `atomic::generated_line_fields_length_envelope` | atomic | positive | ## Geometric Primitives | covered | from/to fields, length_2, corner-normalized envelope |
| `atomic::generated_line_nearest_point_projection` | atomic | positive | ## Geometric Primitives | covered | interior foot vs endpoint clamp; squared distances |
| `atomic::generated_rectangle_corners_and_conversions` | atomic | positive | ## Geometric Primitives | covered | corner normalization, from_aabb/From, envelope round trip |
| `atomic::generated_rectangle_nearest_point_and_distance` | atomic | positive | ## Geometric Primitives | covered | contained query at distance zero; componentwise clamp |
| `atomic::generated_geom_with_data_forwards_geometry` | atomic | positive | ## Geometric Primitives | covered | payload rides along; envelope/distance forwarded |
| `atomic::generated_geom_with_data_line_geometry` | atomic | positive | ## Geometric Primitives | covered | non-point geometry with payload in queries |
| `atomic::generated_point_with_data_deprecated_predecessor` | atomic | positive | ## Geometric Primitives | covered | deprecated new(data, point); data + position() |
| `atomic::generated_cached_envelope_forwards` | atomic | positive | ## Geometric Primitives | covered | envelope captured at construction; Deref to inner |
| `atomic::generated_object_ref_forwards` | atomic | positive | ## Geometric Primitives | covered | by-reference storage answers as referent would |
| `atomic::generated_custom_object_custom_metric` | atomic | positive | ## Points, Scalars, and Object Traits | covered | caller RTreeObject + PointDistance drives nearest/filter |
| `atomic::generated_point_distance_defaults` | atomic | both | ## Points, Scalars, and Object Traits | covered | contains_point default (d2 <= 0); distance_2_if_less_or_equal |
| `atomic::generated_custom_object_point_location` | atomic | both | ## Points, Scalars, and Object Traits | covered | locate_at_point goes through the custom contains_point |
| `atomic::generated_integer_and_tuple_points` | atomic | positive | ## Points, Scalars, and Object Traits | covered | i32 arrays and f64 tuples as points |
| `atomic::generated_empty_tree_root` | atomic | positive | ## Tree Inspection | covered | empty root: no children, empty envelope |
| `atomic::generated_leaf_multiset_equals_content` | atomic | positive | ## Tree Inspection | covered | leaves reachable from root equal stored multiset |
| `atomic::generated_envelope_containment_up_the_tree` | atomic | positive | ## Tree Inspection | covered | child envelopes contained; root = minimal merged envelope |
| `atomic::generated_root_envelope_tracks_removal` | atomic | positive | ## Tree Inspection | covered | root envelope shrinks to content after removal |
| `integration::generated_station_map_lifecycle` | integration | positive | ## Geometric Primitives + ## Mutation and Removal | covered | payload tree: query, mutate in place, insert, remove by point |
| `integration::generated_region_enumeration_consistency` | integration | positive | ## Cross-View Invariants | covered | CVI 4: within-distance set equals neighbor-iter prefix |
| `integration::generated_bulk_vs_incremental_pipeline` | integration | positive | ## Tree Construction and Population + ## Cross-View Invariants | covered | CVI 3: construction paths agree across four query families |
| `integration::generated_custom_params_pipeline` | integration | positive | ## Tree Construction and Population | covered | parameter sets invisible through query+mutation pipeline |
| `integration::generated_rectangle_field_collision` | integration | positive | ## Geometric Primitives + ## Mutation and Removal | covered | solid boxes: containment counts, drain intersecting, root envelope |
| `integration::generated_cross_tree_candidate_join` | integration | positive | ## Spatial Queries | covered | candidate join equals nested-loop envelope intersection |
| `integration::generated_line_network_routing` | integration | positive | ## Geometric Primitives + ## Nearest-Neighbor Queries | covered | segment metric decides nearest; schedule 0.25/2.25/9 |
| `integration::generated_wrapper_transparency` | integration | positive | ## Cross-View Invariants | covered | CVI 7: plain vs CachedEnvelope vs ObjectRef identical answers |
| `integration::generated_insert_remove_lifecycle_consistency` | integration | positive | ## Cross-View Invariants | covered | CVI 1: size = iter count = leaf count after every step |
| `integration::generated_partial_drain_bookkeeping` | integration | positive | ## Cross-View Invariants | covered | CVI 6: k of n yielded, drop, remainder locatable, then finish |
| `integration::generated_failed_removal_leaves_state` | integration | both | ## Cross-View Invariants + ## Error Semantics | covered | CVI 5: three failing removal entry points change nothing |
| `integration::generated_pop_drain_schedule` | integration | both | ## Nearest-Neighbor Queries + ## Tree Inspection | covered | pop to empty: 1/4/9/16/25 schedule, empty root envelope |
| `integration::generated_sensor_coverage_workflow` | integration | both | ## Points, Scalars, and Object Traits | covered | disc metric: coverage location, nearest, filter, decommission |
| `integration::generated_selection_function_maintenance` | integration | positive | ## Spatial Queries + ## Mutation and Removal | covered | one predicate drives locate, single removal, and drain |
| `integration::generated_integer_grid_workflow` | integration | positive | ## Points, Scalars, and Object Traits + ## Mutation and Removal | covered | i32 grid: envelope query, integer distances, removal, root box |

```
Total: 91 | kept (covered): 91 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 91
```

Layer counts: atomic 76, integration 15.
Assertion kinds: atomic — 57 positive, 14 both, 5 failure_path, 0 no_check
(positive share 93%); integration — 12 positive, 3 both, 0 failure_path,
0 no_check.

Coverage notes:
- Every Behavior-layer section holds at least 4 tests; Error Semantics
  holds 7 (5 construction panics + 2 absence-value rows); every
  Cross-View Invariant (1–7) is exercised by at least one dedicated
  integration workflow plus supporting atomic rows.
- Upstream behavior families not re-expressed: node fan-out/depth
  assertions (spec non-goal: internal partitioning), seeded-random
  brute-force comparisons (self-relative, carry upstream's RNG stack),
  and the serde/mint feature surfaces (Non-Goals).
- All 91 kept tests import exclusively through the spec's Import Surface
  (`rstar`, `rstar::primitives`, `rstar::iterators`) plus std.
