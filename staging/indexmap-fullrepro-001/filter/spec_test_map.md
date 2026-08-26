# Specification coverage map — indexmap-fullrepro-001


oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
three probe rounds during spec drafting, then full-suite runs on both the
patched path and the registry lock; upstream tests served as a behavioral
checklist only — see rewrite_audit.md).

Test IDs are `{crate}::{function}` as reported by cargo-nextest against
the oracle workspace.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| `atomic::generated_new_and_default_empty` | atomic | positive | ## Construction, Hashing, and Capacity | covered | new/default/with_capacity all empty; first() None |
| `atomic::generated_from_iterator_duplicate_law` | atomic | positive | ## Construction, Hashing, and Capacity | covered | first occurrence fixes position, last value wins (map and set) |
| `atomic::generated_from_array_preserves_order` | atomic | positive | ## Construction, Hashing, and Capacity | covered | From<[..]> keeps declaration order |
| `atomic::generated_macros_duplicate_law` | atomic | positive | ## Construction, Hashing, and Capacity | covered | indexmap!/indexset! literals with the duplicate law |
| `atomic::generated_equivalent_borrowed_lookups` | atomic | positive | ## Construction, Hashing, and Capacity | covered | &str queries against String keys via Equivalent |
| `atomic::generated_custom_equivalent_impl` | atomic | both | ## Construction, Hashing, and Capacity | covered | user Equivalent impl: hit and miss through a proxy type |
| `atomic::generated_custom_hashers` | atomic | positive | ## Construction, Hashing, and Capacity | covered | with_hasher/with_capacity_and_hasher/default; hasher() exposed |
| `atomic::generated_capacity_neutrality_and_try_reserve` | atomic | both | ## Construction, Hashing, and Capacity | covered | reserve/shrink don't touch order; try_reserve Ok and Err(usize::MAX) |
| `atomic::generated_clear_resets` | atomic | positive | ## Construction, Hashing, and Capacity | covered | clear empties length, lookups, and the slice view |
| `atomic::generated_insert_appends_and_updates` | atomic | positive | ## Insertion and Lookup | covered | new key appends; existing key keeps position, old value returned |
| `atomic::generated_insert_full_reports_index` | atomic | positive | ## Insertion and Lookup | covered | insert_full: (new index, None) / (kept index, Some(old)) |
| `atomic::generated_insert_keeps_stored_key_instance` | atomic | positive | ## Insertion and Lookup | covered | update keeps original key instance (identity-visible key type) |
| `atomic::generated_lookup_family_agrees` | atomic | both | ## Insertion and Lookup | covered | get/get_key_value/get_full/get_index_of/contains_key agree; absent Nones |
| `atomic::generated_mutable_lookups` | atomic | both | ## Insertion and Lookup | covered | get_mut and get_full_mut write through; absent None |
| `atomic::generated_positional_reads` | atomic | both | ## Insertion and Lookup | covered | get_index/first/last and _mut forms; out-of-bounds None |
| `atomic::generated_indexing_operators` | atomic | both | ## Insertion and Lookup | covered | map[key], map[usize], keys()[usize]; absent-key and OOB panics |
| `atomic::generated_swap_remove_backfill` | atomic | positive | ## Removal and Order Surgery | covered | last entry back-fills the vacated slot; one index changes |
| `atomic::generated_swap_remove_last_moves_nothing` | atomic | positive | ## Removal and Order Surgery | covered | removing the last entry moves no other entry |
| `atomic::generated_swap_remove_variants` | atomic | both | ## Removal and Order Surgery | covered | _entry/_full/_index forms share the law; OOB index None |
| `atomic::generated_shift_remove_preserves_order` | atomic | positive | ## Removal and Order Surgery | covered | later entries shift toward the front; relative order kept |
| `atomic::generated_shift_remove_variants` | atomic | both | ## Removal and Order Surgery | covered | _entry/_full/_index forms share the law; OOB index None |
| `atomic::generated_deprecated_aliases_swap` | atomic | positive | ## Removal and Order Surgery | covered | remove/remove_entry behave exactly as the swap forms |
| `atomic::generated_pop_removes_last` | atomic | both | ## Removal and Order Surgery | covered | pop returns the last pair; None when empty |
| `atomic::generated_failed_removals_leave_map` | atomic | failure_path | ## Error Semantics | covered | absent key: every removal answers None and the map is unchanged |
| `atomic::generated_single_entry_removal` | atomic | positive | ## Removal and Order Surgery | covered | removing the only entry leaves an empty map |
| `atomic::generated_move_index_forward` | atomic | positive | ## Removal and Order Surgery | covered | move_index(0,3): intervening entries shift toward the vacated side |
| `atomic::generated_move_index_backward` | atomic | positive | ## Removal and Order Surgery | covered | move_index(4,1) shifts the block right |
| `atomic::generated_move_index_panics_out_of_bounds` | atomic | failure_path | ## Error Semantics | covered | either position == len panics |
| `atomic::generated_swap_indices_exchanges` | atomic | positive | ## Removal and Order Surgery | covered | positions exchanged; equal indices a no-op |
| `atomic::generated_swap_indices_panics_out_of_bounds` | atomic | failure_path | ## Error Semantics | covered | either position out of bounds panics |
| `atomic::generated_reverse_in_place` | atomic | positive | ## Removal and Order Surgery | covered | whole sequence reversed; indices track |
| `atomic::generated_shift_insert_new_key` | atomic | positive | ## Removal and Order Surgery | covered | new key lands exactly at index; index == len appends |
| `atomic::generated_shift_insert_existing_key_moves` | atomic | positive | ## Removal and Order Surgery | covered | existing key moved to index with value updated; old value returned |
| `atomic::generated_shift_insert_panics` | atomic | failure_path | ## Error Semantics | covered | index == len for an existing key panics; index > len panics |
| `atomic::generated_insert_before_new_key` | atomic | positive | ## Removal and Order Surgery | covered | new key final position is index; index == len appends |
| `atomic::generated_insert_before_existing_key_positions` | atomic | positive | ## Removal and Order Surgery | covered | key before target ends at index-1; key at/after target ends at index |
| `atomic::generated_insert_before_panics_past_len` | atomic | failure_path | ## Error Semantics | covered | index > len panics |
| `atomic::generated_insert_sorted_map` | atomic | positive | ## Removal and Order Surgery | covered | binary-search position for new keys; existing key keeps index |
| `atomic::generated_truncate_keeps_prefix` | atomic | positive | ## Bulk Rewrites and Merging | covered | first n kept; n >= len a no-op; truncate(0) empties |
| `atomic::generated_split_off_returns_tail` | atomic | positive | ## Bulk Rewrites and Merging | covered | tail moves into a new map, order preserved on both sides |
| `atomic::generated_split_off_panics_past_len` | atomic | failure_path | ## Error Semantics | covered | at > len panics |
| `atomic::generated_drain_yields_in_order` | atomic | positive | ## Bulk Rewrites and Merging | covered | positional range drained in order; drain(..) empties |
| `atomic::generated_drain_removes_even_if_dropped` | atomic | positive | ## Bulk Rewrites and Merging | covered | dropping the iterator still removes the whole range |
| `atomic::generated_drain_panics_bad_range` | atomic | failure_path | ## Error Semantics | covered | end > len and start > end panic |
| `atomic::generated_splice_replaces_range` | atomic | positive | ## Bulk Rewrites and Merging | covered | removed entries out in order; replacements in at the splice point |
| `atomic::generated_splice_outside_key_keeps_position` | atomic | positive | ## Bulk Rewrites and Merging | covered | replacement key outside the range keeps position, value updated |
| `atomic::generated_splice_inside_key_reinserted` | atomic | positive | ## Bulk Rewrites and Merging | covered | key inside the range re-enters at the splice position like new |
| `atomic::generated_append_moves_everything` | atomic | positive | ## Bulk Rewrites and Merging | covered | other emptied; duplicates keep position with incoming value |
| `atomic::generated_extend_per_pair_law` | atomic | positive | ## Bulk Rewrites and Merging | covered | extend applies the per-pair insertion law |
| `atomic::generated_retain_preserves_order` | atomic | positive | ## Bulk Rewrites and Merging | covered | predicate filtering with mutable value access; order kept |
| `atomic::generated_sort_keys_in_place` | atomic | positive | ## Sorting and Ordered Search | covered | sort_keys orders by key with values attached |
| `atomic::generated_sort_by_is_stable` | atomic | positive | ## Sorting and Ordered Search | covered | equal-comparing entries keep their relative order |
| `atomic::generated_sort_by_cached_key` | atomic | positive | ## Sorting and Ordered Search | covered | derived sort key (Reverse) computed per entry |
| `atomic::generated_sorted_by_consumes` | atomic | positive | ## Sorting and Ordered Search | covered | consuming sorted iterator without in-place mutation |
| `atomic::generated_unstable_sorts_same_multiset` | atomic | positive | ## Sorting and Ordered Search | covered | unstable family deterministic here (distinct keys) |
| `atomic::generated_binary_search_keys` | atomic | both | ## Sorting and Ordered Search | covered | Ok(index) present; Err(insertion index) absent |
| `atomic::generated_binary_search_by_forms` | atomic | both | ## Sorting and Ordered Search | covered | by-comparator and by-key forms; Err at the end |
| `atomic::generated_partition_point` | atomic | positive | ## Sorting and Ordered Search | covered | first false position; degenerate all-false/all-true |
| `atomic::generated_set_sort_family` | atomic | both | ## Sorting and Ordered Search | covered | set sort/sort_by/sorted_by/sort_unstable/binary_search/partition_point/reverse |
| `atomic::generated_as_slice_and_get_range` | atomic | both | ## Slices and Indexed Views | covered | as_slice; get_range sub-view; reversed/overlong ranges answer None |
| `atomic::generated_range_indexing_and_panics` | atomic | both | ## Slices and Indexed Views | covered | container and slice range indexing; invalid range panics |
| `atomic::generated_slice_positional_reads` | atomic | both | ## Slices and Indexed Views | covered | get_index/first/last; usize indexing yields values, panics OOB |
| `atomic::generated_slice_split_family` | atomic | positive | ## Slices and Indexed Views | covered | split_at/split_first/split_last partition the view |
| `atomic::generated_slice_iterators_and_mutation` | atomic | positive | ## Slices and Indexed Views | covered | slice iter/keys/values; as_mut_slice + get_range_mut write through |
| `atomic::generated_slice_search` | atomic | both | ## Slices and Indexed Views | covered | slice binary_search family and partition_point |
| `atomic::generated_slice_equality_is_order_sensitive` | atomic | both | ## Slices and Indexed Views | covered | containers ==, slices != when order differs |
| `atomic::generated_slice_ord_lexicographic` | atomic | positive | ## Slices and Indexed Views | covered | lexicographic entry order; prefix compares less |
| `atomic::generated_slice_hash_and_debug` | atomic | positive | ## Slices and Indexed Views | covered | equal slices hash equally; Debug prints entry lists |
| `atomic::generated_into_boxed_slice` | atomic | positive | ## Slices and Indexed Views | covered | owned boxed slice; into_keys/into_values consume it |
| `atomic::generated_entry_variants_and_index` | atomic | positive | ## The Entry Interface | covered | Occupied vs Vacant; vacant index == current length |
| `atomic::generated_or_insert_family` | atomic | positive | ## The Entry Interface | covered | or_insert/or_insert_with/or_insert_with_key/or_default insert only when vacant |
| `atomic::generated_and_modify_chain` | atomic | positive | ## The Entry Interface | covered | and_modify runs only on occupied, chains into or_insert |
| `atomic::generated_entry_insert_entry` | atomic | positive | ## The Entry Interface | covered | insert_entry inserts or replaces, returns OccupiedEntry |
| `atomic::generated_occupied_accessors` | atomic | positive | ## The Entry Interface | covered | get/get_mut/into_mut/insert(old back) |
| `atomic::generated_occupied_removals` | atomic | positive | ## The Entry Interface | covered | swap/shift remove and _entry forms mirror container laws |
| `atomic::generated_occupied_reorder` | atomic | positive | ## The Entry Interface | covered | move_index/swap_indices reposition through the entry |
| `atomic::generated_vacant_operations` | atomic | positive | ## The Entry Interface | covered | into_key inserts nothing; insert/insert_entry append |
| `atomic::generated_vacant_positioned_inserts` | atomic | positive | ## The Entry Interface | covered | vacant shift_insert at exact position; insert_sorted among sorted keys |
| `atomic::generated_indexed_entry_reads_and_writes` | atomic | both | ## The Entry Interface | covered | get_index_entry accessors and value replacement; OOB None |
| `atomic::generated_indexed_entry_removals_and_moves` | atomic | positive | ## The Entry Interface | covered | both removal laws and both moves through IndexedEntry |
| `atomic::generated_first_and_last_entry` | atomic | both | ## The Entry Interface | covered | first_entry/last_entry at the ends; None when empty |
| `atomic::generated_set_insert_keeps_original_instance` | atomic | both | ## Sets: Membership and Value Identity | covered | duplicate insert refused; original instance survives; insert_full |
| `atomic::generated_set_replace_swaps_instance` | atomic | positive | ## Sets: Membership and Value Identity | covered | replace keeps position, stores the new instance, returns the old |
| `atomic::generated_set_positioned_insertions` | atomic | positive | ## Sets: Membership and Value Identity | covered | insert_before/shift_insert/insert_sorted mirror the map laws |
| `atomic::generated_set_membership_reads` | atomic | both | ## Sets: Membership and Value Identity | covered | contains/get/get_full/get_index_of/positional reads; OOB panic |
| `atomic::generated_set_swap_and_shift_remove` | atomic | both | ## Sets: Membership and Value Identity | covered | boolean removals follow the two order laws; absent false |
| `atomic::generated_set_take_family` | atomic | both | ## Sets: Membership and Value Identity | covered | swap_take/shift_take return the stored instance; absent None |
| `atomic::generated_set_full_and_index_removals` | atomic | both | ## Sets: Membership and Value Identity | covered | _full and _index removal forms; OOB None |
| `atomic::generated_set_deprecated_aliases` | atomic | positive | ## Sets: Membership and Value Identity | covered | remove/take alias the swap forms |
| `atomic::generated_set_pop_and_clear` | atomic | both | ## Sets: Membership and Value Identity | covered | pop returns the last value, None when empty; clear resets |
| `atomic::generated_set_bulk_mirror` | atomic | both | ## Sets: Membership and Value Identity | covered | truncate/split_off/retain/reverse/move_index/swap_indices; split_off panic |
| `atomic::generated_set_drain_splice_append` | atomic | positive | ## Sets: Membership and Value Identity | covered | drain in order; splice outside-collision law; append/extend dedupe |
| `atomic::generated_intersection_order` | atomic | positive | ## Set Algebra and Comparisons | covered | self's order filtered by other, both directions |
| `atomic::generated_difference_order` | atomic | positive | ## Set Algebra and Comparisons | covered | self's exclusives in self's order |
| `atomic::generated_union_order` | atomic | positive | ## Set Algebra and Comparisons | covered | all of self, then other's exclusives in other's order |
| `atomic::generated_symmetric_difference_order` | atomic | positive | ## Set Algebra and Comparisons | covered | self's exclusives then other's exclusives |
| `atomic::generated_operators_match_iterators` | atomic | positive | ## Set Algebra and Comparisons | covered | & | ^ - build sets equal to the collected lazy iterators |
| `atomic::generated_containment_predicates` | atomic | both | ## Set Algebra and Comparisons | covered | is_subset/is_superset/is_disjoint accept and reject |
| `atomic::generated_map_equality_order_insensitive` | atomic | both | ## Set Algebra and Comparisons | covered | same associations equal across orders; value/length differences reject |
| `atomic::generated_set_equality_order_insensitive` | atomic | both | ## Set Algebra and Comparisons | covered | same members equal across orders; subset rejects |
| `atomic::generated_clone_and_debug` | atomic | positive | ## Set Algebra and Comparisons | covered | clone preserves order; Debug prints map/set notation |
| `atomic::generated_iteration_orders` | atomic | positive | ## Iteration | covered | iter/keys/values and by-ref IntoIterator traverse in sequence order |
| `atomic::generated_mutable_iteration` | atomic | positive | ## Iteration | covered | iter_mut and values_mut write through in order |
| `atomic::generated_consuming_iterators` | atomic | positive | ## Iteration | covered | into_keys/into_values/into_iter consume in order (map and set) |
| `atomic::generated_double_ended_iteration` | atomic | positive | ## Iteration | covered | next_back from the tail interleaved with next; rev() |
| `atomic::generated_exact_size_and_fused` | atomic | both | ## Iteration | covered | len() tracks the remainder; None repeats after exhaustion |
| `integration::generated_config_registry_lifecycle` | integration | positive | ## Representative Workflows | covered | Workflow 1: entry overrides, move_index promotion, shift_remove, range pagination, both indexing views |
| `integration::generated_layered_override_merge` | integration | both | ## Bulk Rewrites and Merging | covered | append + extend layering; order-insensitive == vs order-sensitive slices |
| `integration::generated_priority_reorder_audit` | integration | both | ## Removal and Order Surgery | covered | insert_before/shift_insert arithmetic, stable value sort, key sort + binary search |
| `integration::generated_registry_snapshot_and_rollback` | integration | both | ## Cross-View Invariants | covered | clone snapshot, swap_remove drift, set-difference diff, rollback restores slice equality |
| `integration::generated_word_frequency_pipeline` | integration | positive | ## Representative Workflows | covered | Workflow 2: entry counting, stable sort by count, truncate top-k, range tail |
| `integration::generated_grouping_with_or_default` | integration | positive | ## The Entry Interface | covered | or_default grouping in first-seen order; and_modify only on existing groups |
| `integration::generated_index_stability_ledger` | integration | positive | ## Cross-View Invariants | covered | insert_full indices stable under update; swap vs shift disturbance compared |
| `integration::generated_event_stream_dedup` | integration | positive | ## Representative Workflows | covered | Workflow 3: insert-driven dedup, ordered drain batch, pop newest |
| `integration::generated_tag_algebra_report` | integration | both | ## Set Algebra and Comparisons | covered | all four algebra orders, operators == collected iterators, predicates |
| `integration::generated_lru_like_promotion` | integration | positive | ## Sets: Membership and Value Identity | covered | move_index promotion, front eviction by shift_remove_index, recency order |
| `integration::generated_roster_merge_with_identity` | integration | positive | ## Sets: Membership and Value Identity | covered | append keeps original instances; replace upgrades in place; shift retire |
| `integration::generated_splice_editor_session` | integration | positive | ## Bulk Rewrites and Merging | covered | chained splices: plain replacement, outside-collision, inside re-entry |
| `integration::generated_partial_drain_bookkeeping` | integration | positive | ## Bulk Rewrites and Merging | covered | partially consumed drain dropped early; every view agrees after |
| `integration::generated_sorted_ledger_maintenance` | integration | both | ## Sorting and Ordered Search | covered | insert_sorted upkeep, binary search hit/miss, partition_point + split_off archive |
| `integration::generated_cross_view_consistency` | integration | positive | ## Cross-View Invariants | covered | mixed mutation sequence; iter/slice/index/boxed views report one sequence |

Assertion kinds: atomic — 69 positive, 30 both, 7 failure_path, 0 no_check
(positive share 93%); integration — 11 positive, 4 both, 0 failure_path,
0 no_check.

Coverage notes:
- Every Behavior-layer section holds at least 5 tests; Error Semantics
  holds 8 (7 panic families: indexing OOB, move_index/swap_indices,
  shift_insert, insert_before, split_off, drain ranges — plus the
  absence-form row `generated_failed_removals_leave_map`); every
  Cross-View Invariant is exercised by a dedicated integration workflow
  plus supporting atomic rows.
- Upstream behavior families not re-expressed: rayon/serde/borsh/quickcheck
  feature surfaces (Non-Goals), `no_std`/alloc build matrices, and
  macro-expansion internals (`__count` etc.) — capacity growth *amounts*
  are also unasserted (the spec fixes only neutrality of order and
  content under reserve/shrink).
- All 121 kept tests import exclusively through the spec's Import Surface
  (`indexmap`, `indexmap::map`, `indexmap::set`) plus std.
