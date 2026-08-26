# Specification coverage map — fst-fullrepro-001

oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary
plus a full suite run; upstream tests served as a behavioral checklist
only — see rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::generated_always_match_yields_all` | atomic | ## Automaton Search | covered | AlwaysMatch yields all |
| `atomic::generated_as_bytes_to_vec_agree` | atomic | ## Raw Transducers and Byte Images | covered | as_bytes/to_vec/size agree |
| `atomic::generated_builder_bytes_written_grows` | atomic | ## Building Transducers | covered | bytes_written monotone vs final image |
| `atomic::generated_builder_get_ref_borrows_writer` | atomic | ## Building Transducers | covered | get_ref mid-build prefix of image |
| `atomic::generated_builder_into_inner_reopen` | atomic | ## Building Transducers | covered | into_inner returns writer; reopen |
| `atomic::generated_complement_inverts` | atomic | ## Automaton Search | covered | complement rejects the matched key |
| `atomic::generated_custom_automaton_even_length` | atomic | ## Automaton Search | covered | caller automaton, default can_match/will_always_match |
| `atomic::generated_empty_builder_yields_empty_container` | atomic | ## Querying Containers | covered | empty image: len 0, empty stream, probes false |
| `atomic::generated_empty_op_builder_union_empty` | atomic | ## Set Operations Across Transducers | covered | OpBuilder::new() union is empty |
| `atomic::generated_error_display_and_source` | atomic | ## Error Semantics | covered | Display/Debug non-empty; source() wraps |
| `atomic::generated_error_from_io_variant` | atomic | ## Error Semantics | covered | From conversions into both variants |
| `atomic::generated_intersection_union_combinators` | atomic | ## Automaton Search | covered | intersection/union combinators |
| `atomic::generated_len_and_is_empty_all_containers` | atomic | ## Querying Containers | covered | len/is_empty on all three |
| `atomic::generated_map_builder_duplicate_key_payload` | atomic | ## Error Semantics | covered | DuplicateKey got payload |
| `atomic::generated_map_builder_memory_into_map` | atomic | ## Building Transducers | covered | memory builder into_map |
| `atomic::generated_map_builder_writer_finish_reopen` | atomic | ## Building Transducers | covered | map writer builder round trip |
| `atomic::generated_map_from_iter_duplicate_errors` | atomic | ## Error Semantics | covered | one-shot map DuplicateKey |
| `atomic::generated_map_from_iter_get_and_len` | atomic | ## Building Transducers | covered | one-shot map; get + len |
| `atomic::generated_map_get_zero_value_distinct_from_absent` | atomic | ## Querying Containers | covered | Some(0) distinguishable from None |
| `atomic::generated_map_keys_projection` | atomic | ## Streaming and Ranges | covered | keys() stream |
| `atomic::generated_map_range_carries_values` | atomic | ## Streaming and Ranges | covered | map range yields values |
| `atomic::generated_map_str_helpers_non_utf8_error` | atomic | ## Error Semantics | covered | map str helpers FromUtf8; byte helpers succeed |
| `atomic::generated_map_stream_collection_helpers` | atomic | ## Streaming and Ranges | covered | map stream collection helpers |
| `atomic::generated_map_stream_pairs_in_key_order` | atomic | ## Streaming and Ranges | covered | (key, value) pairs in key order |
| `atomic::generated_map_values_projection` | atomic | ## Streaming and Ranges | covered | values() in key order |
| `atomic::generated_open_garbage_bytes_format_error` | atomic | ## Error Semantics | covered | Format error carries byte length |
| `atomic::generated_output_cat_sums` | atomic | ## Querying Containers | covered | cat returns sum |
| `atomic::generated_output_new_zero_value_is_zero` | atomic | ## Querying Containers | covered | Output new/zero/value/is_zero |
| `atomic::generated_output_prefix_minimum` | atomic | ## Querying Containers | covered | prefix returns min |
| `atomic::generated_output_sub_difference` | atomic | ## Querying Containers | covered | sub returns difference |
| `atomic::generated_output_sub_underflow_panics` | atomic | ## Error Semantics | covered | sub panics on underflow (after positive check) |
| `atomic::generated_range_bound_replacement_last_wins` | atomic | ## Streaming and Ranges | covered | later bound call replaces earlier |
| `atomic::generated_range_empty_selection` | atomic | ## Streaming and Ranges | covered | empty selection is a valid stream |
| `atomic::generated_range_ge_le_inclusive` | atomic | ## Streaming and Ranges | covered | ge/le inclusive bounds |
| `atomic::generated_range_gt_lt_exclusive` | atomic | ## Streaming and Ranges | covered | gt/lt exclusive bounds |
| `atomic::generated_range_unbounded_equals_full_stream` | atomic | ## Streaming and Ranges | covered | no bounds == full stream |
| `atomic::generated_raw_as_inner_into_inner` | atomic | ## Raw Transducers and Byte Images | covered | as_inner/into_inner; reopen |
| `atomic::generated_raw_builder_add_duplicate_noop_insert_errors` | atomic | ## Building Transducers | covered | add no-op vs insert DuplicateKey |
| `atomic::generated_raw_builder_add_zero_outputs` | atomic | ## Building Transducers | covered | raw add: keys carry zero output |
| `atomic::generated_raw_builder_insert_values` | atomic | ## Building Transducers | covered | raw insert with explicit values |
| `atomic::generated_raw_contains_key` | atomic | ## Querying Containers | covered | raw contains_key exact keys |
| `atomic::generated_raw_from_iter_map_values` | atomic | ## Building Transducers | covered | from_iter_map stores values |
| `atomic::generated_raw_from_iter_set_zero_values` | atomic | ## Building Transducers | covered | from_iter_set assigns zero |
| `atomic::generated_raw_get_key_absent_none` | atomic | ## Querying Containers | covered | get_key miss answers None |
| `atomic::generated_raw_get_key_monotonic_lookup` | atomic | ## Querying Containers | covered | get_key on monotonic values |
| `atomic::generated_raw_size_equals_image_len` | atomic | ## Querying Containers | covered | size == as_bytes().len() |
| `atomic::generated_ref_container_into_stream` | atomic | ## Streaming and Ranges | covered | &Set converts into its full stream |
| `atomic::generated_result_alias_round_trip` | atomic | ## Error Semantics | covered | fst::Result alias usable |
| `atomic::generated_set_builder_duplicate_is_noop` | atomic | ## Building Transducers | covered | key-only repeat accepted once |
| `atomic::generated_set_builder_memory_into_set` | atomic | ## Building Transducers | covered | memory builder into_set |
| `atomic::generated_set_builder_out_of_order_payload` | atomic | ## Error Semantics | covered | OutOfOrder previous/got payload |
| `atomic::generated_set_contains_bytes_and_strs` | atomic | ## Querying Containers | covered | contains over AsRef<[u8]> forms |
| `atomic::generated_set_extend_iter` | atomic | ## Building Transducers | covered | extend_iter inserts every item |
| `atomic::generated_set_from_iter_duplicate_is_noop` | atomic | ## Building Transducers | covered | one-shot set repeat accepted once |
| `atomic::generated_set_from_iter_membership_and_len` | atomic | ## Building Transducers | covered | one-shot set; membership + len |
| `atomic::generated_set_from_iter_out_of_order_errors` | atomic | ## Error Semantics | covered | one-shot set OutOfOrder |
| `atomic::generated_set_into_bytes_collects` | atomic | ## Streaming and Ranges | covered | into_bytes collects byte vecs |
| `atomic::generated_set_into_strs_collects` | atomic | ## Streaming and Ranges | covered | into_strs collects Strings |
| `atomic::generated_set_into_strs_non_utf8_error` | atomic | ## Error Semantics | covered | FromUtf8 on non-UTF-8 key |
| `atomic::generated_set_stream_ascending_order` | atomic | ## Streaming and Ranges | covered | byte-lexicographic order incl. case |
| `atomic::generated_starts_with_prefix_filter` | atomic | ## Automaton Search | covered | starts_with prefix filter |
| `atomic::generated_str_empty_matches_only_empty_key` | atomic | ## Automaton Search | covered | Str("") matches only empty key |
| `atomic::generated_str_matches_exactly_one_key` | atomic | ## Automaton Search | covered | Str matches exactly one key |
| `atomic::generated_stream_next_none_at_exhaustion` | atomic | ## Streaming and Ranges | covered | next None at exhaustion, stays None |
| `atomic::generated_subsequence_empty_matches_every_key` | atomic | ## Automaton Search | covered | empty subsequence matches all |
| `atomic::generated_subsequence_gaps_allowed` | atomic | ## Automaton Search | covered | subsequence with gaps |
| `atomic::generated_verify_ok_on_built_images` | atomic | ## Raw Transducers and Byte Images | covered | verify succeeds on built images |
| `atomic::generated_writer_backed_set_builder_finish_reopen` | atomic | ## Building Transducers | covered | writer builder finish; reopen |
| `integration::build_paths::generated_all_map_paths_identical_images` | integration | ## Cross-View Invariants | covered | CVI 6: three map paths, identical images |
| `integration::build_paths::generated_all_set_paths_identical_images` | integration | ## Cross-View Invariants | covered | CVI 6: three set paths, identical images |
| `integration::build_paths::generated_extend_iter_matches_manual_inserts` | integration | ## Building Transducers | covered | extend_iter == per-key inserts |
| `integration::build_paths::generated_extend_stream_copies_source_set` | integration | ## Building Transducers | covered | extend_stream copies a set stream |
| `integration::build_paths::generated_finish_and_into_inner_same_image` | integration | ## Building Transducers | covered | finish and into_inner emit one image |
| `integration::build_paths::generated_map_extend_stream_carries_values` | integration | ## Building Transducers | covered | map extend_stream carries values; order enforced |
| `integration::build_paths::generated_mixed_insert_and_extend_equal_one_shot` | integration | ## Building Transducers | covered | insert+extend batches == one-shot image |
| `integration::cross_view::generated_get_key_roundtrip_whole_map` | integration | ## Querying Containers | covered | reverse lookup across whole monotonic map |
| `integration::cross_view::generated_map_and_raw_view_agree` | integration | ## Cross-View Invariants | covered | CVI 7: map and as_fst agree per key |
| `integration::cross_view::generated_map_keys_values_stream_zip_agree` | integration | ## Cross-View Invariants | covered | keys/values/stream zip agreement |
| `integration::cross_view::generated_range_matrix_agrees_with_filter` | integration | ## Cross-View Invariants | covered | CVI 2: bound matrix == filtered full stream |
| `integration::cross_view::generated_search_and_ops_are_consistent_views` | integration | ## Cross-View Invariants | covered | CVI 3+4: partition union rebuilds the image |
| `integration::cross_view::generated_set_into_fst_projections_agree` | integration | ## Raw Transducers and Byte Images | covered | into_fst view: zero outputs, same keys |
| `integration::cross_view::generated_stream_count_matches_len_and_membership` | integration | ## Cross-View Invariants | covered | CVI 1: enumeration == point queries |
| `integration::cross_view::generated_union_extend_stream_workflow` | integration | ## Representative Workflows | covered | merge workflow: op union -> extend_stream -> one-shot image |
| `integration::images::generated_corrupt_image_checksum_mismatch` | integration | ## Error Semantics | covered | ChecksumMismatch on corrupted image |
| `integration::images::generated_format_error_size_payload` | integration | ## Error Semantics | covered | Format size payload across sizes |
| `integration::images::generated_image_roundtrip_preserves_projections` | integration | ## Cross-View Invariants | covered | CVI 5: reopen preserves every projection |
| `integration::images::generated_into_inner_reopen_projections` | integration | ## Raw Transducers and Byte Images | covered | into_inner data reopens equal |
| `integration::images::generated_set_map_raw_image_interop` | integration | ## Raw Transducers and Byte Images | covered | set/map images opened raw answer consistently |
| `integration::images::generated_verify_survives_roundtrip` | integration | ## Raw Transducers and Byte Images | covered | verify + size across reopen |
| `integration::lattice::generated_map_intersection_provenance_sorted_by_index` | integration | ## Set Operations Across Transducers | covered | provenance sorted by stream index |
| `integration::lattice::generated_map_union_indexed_value_provenance` | integration | ## Set Operations Across Transducers | covered | IndexedValue index/value provenance |
| `integration::lattice::generated_op_over_range_and_search_streams` | integration | ## Set Operations Across Transducers | covered | op inputs are range/search sub-streams |
| `integration::lattice::generated_push_and_add_equivalent` | integration | ## Set Operations Across Transducers | covered | push == add |
| `integration::lattice::generated_raw_predicates_over_keys` | integration | ## Set Operations Across Transducers | covered | raw predicates compare keys only |
| `integration::lattice::generated_subset_superset_disjoint_predicates` | integration | ## Set Operations Across Transducers | covered | whole-container predicates |
| `integration::lattice::generated_three_stream_difference_first_minus_rest` | integration | ## Set Operations Across Transducers | covered | first minus rest over 3 streams |
| `integration::lattice::generated_three_stream_symmetric_difference_odd_count` | integration | ## Set Operations Across Transducers | covered | odd-count rule over 3 streams |
| `integration::lattice::generated_two_set_ops_match_brute_force` | integration | ## Cross-View Invariants | covered | CVI 4: four ops == brute-force algebra |
| `integration::search::generated_automaton_intersection_union_algebra` | integration | ## Cross-View Invariants | covered | CVI 3: combinator algebra observable |
| `integration::search::generated_complement_is_set_difference` | integration | ## Cross-View Invariants | covered | CVI 3: complement partitions key set |
| `integration::search::generated_custom_automaton_with_bounds` | integration | ## Automaton Search | covered | caller automaton with can_match pruning + bounds |
| `integration::search::generated_map_search_carries_values` | integration | ## Automaton Search | covered | map search carries values |
| `integration::search::generated_raw_search_carries_outputs` | integration | ## Automaton Search | covered | raw search carries outputs |
| `integration::search::generated_starts_with_and_range_compose` | integration | ## Automaton Search | covered | search + ge/gt/le/lt one pass |
| `integration::search::generated_subsequence_agrees_with_brute_force` | integration | ## Cross-View Invariants | covered | CVI 3: search == brute-force filter |

## Per-section coverage

- ## Automaton Search: 13 tests
- ## Building Transducers: 22 tests
- ## Cross-View Invariants: 12 tests
- ## Error Semantics: 13 tests
- ## Querying Containers: 13 tests
- ## Raw Transducers and Byte Images: 7 tests
- ## Representative Workflows: 1 tests
- ## Set Operations Across Transducers: 9 tests
- ## Streaming and Ranges: 15 tests

All behavior sections, Error Semantics, and Cross-View Invariants meet
their per-section minimums. Narrative sections (Product Overview,
Non-Goals, State Model, Public Interface, appendices) are exercised
indirectly: the State Model's immutable-image rule by every round-trip
test, Representative Workflows directly by
`integration::cross_view::generated_union_extend_stream_workflow`, and
the Import Surface by every `use` line in the oracle.

Total: 105 | kept (covered): 105 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 105
