# Specification coverage map — ropey-fullrepro-001

oracle_source: generated_only (all tests written against the spec with
expected values verified on the pinned reference; upstream inline suites
served as a behavioral checklist only — see rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::generated_append_cases` | atomic | ## Editing | covered | append incl. empty either side |
| `atomic::generated_builder_matches_from_str` | atomic | ## Building and Persisting Text | covered | builder pieces incl. empty; Default |
| `atomic::generated_byte_and_char_accessors` | atomic | ## Reading Content | covered | byte()/char() and get_ twins |
| `atomic::generated_byte_slice_and_boundaries` | atomic | ## Slicing | covered | byte_slice; non-boundary endpoints rejected |
| `atomic::generated_byte_to_char_boundaries_and_interior` | atomic | ## Metrics and Coordinate Conversion | covered | interior byte floors; one-past-end maps |
| `atomic::generated_bytes_iter_and_len` | atomic | ## Iterators | covered | bytes stream + exact-size len |
| `atomic::generated_capacity_and_shrink_preserve_content` | atomic | ## Building and Persisting Text | covered | capacity>=len; shrink preserves content |
| `atomic::generated_char_to_byte_positions` | atomic | ## Metrics and Coordinate Conversion | covered | char->byte positions |
| `atomic::generated_chars_iter_and_len` | atomic | ## Iterators | covered | chars stream + exact-size len |
| `atomic::generated_chunk_accessor_fallible_twins` | atomic | ## Error Semantics | covered | get_chunk_* None; slice try_chunk_at_byte Err |
| `atomic::generated_chunk_at_byte_invariants` | atomic | ## Reading Content | covered | chunk tuple start coords + containment |
| `atomic::generated_chunk_at_char_and_line_break` | atomic | ## Reading Content | covered | chunk lookup by char and break index |
| `atomic::generated_chunks_at_byte_positions` | atomic | ## Iterators | covered | chunks_at_byte coords incl. end position |
| `atomic::generated_chunks_concat_is_content` | atomic | ## Iterators | covered | chunk concat reassembly |
| `atomic::generated_clone_is_independent_of_edits` | atomic | ## Editing | covered | persistence under edits |
| `atomic::generated_crlf_is_single_break` | atomic | ## Line Semantics | covered | CRLF single break; conversions agree |
| `atomic::generated_edit_error_payloads` | atomic | ## Error Semantics | covered | edit try_ twins; content untouched on failure |
| `atomic::generated_empty_rope_chunks` | atomic | ## Reading Content | covered | empty content: no chunks; zero-coord tuple |
| `atomic::generated_eq_matrix` | atomic | ## Comparison, Ordering, and Hashing | covered | eq across rope/slice/str/String/Cow both ways |
| `atomic::generated_error_display_names_index_and_length` | atomic | ## Error Semantics | covered | Display/Debug name index+length; Copy/Clone/Error |
| `atomic::generated_from_conversions_agree` | atomic | ## Building and Persisting Text | covered | From<&str>/String/Cow/RopeSlice agree |
| `atomic::generated_from_iterator_concatenates_in_order` | atomic | ## Building and Persisting Text | covered | FromIterator over three item types |
| `atomic::generated_from_reader_invalid_utf8_is_invalid_data` | atomic | ## Error Semantics | covered | io InvalidData on bad utf8 |
| `atomic::generated_from_reader_reads_all` | atomic | ## Building and Persisting Text | covered | from_reader content equality |
| `atomic::generated_from_str_content_and_display` | atomic | ## Building and Persisting Text | covered | from_str + Display + String conversion |
| `atomic::generated_hash_ignores_construction_path` | atomic | ## Comparison, Ordering, and Hashing | covered | hash equal across construction paths |
| `atomic::generated_insert_empty_and_char` | atomic | ## Editing | covered | empty insert no-op; insert_char multibyte |
| `atomic::generated_insert_positions` | atomic | ## Editing | covered | insert at start/middle/end |
| `atomic::generated_is_instance_distinguishes_clone_from_equal` | atomic | ## Building and Persisting Text | covered | identity vs content equality |
| `atomic::generated_iterators_on_slices` | atomic | ## Iterators | covered | all four families on a sub-view |
| `atomic::generated_len_metrics_ascii` | atomic | ## Metrics and Coordinate Conversion | covered | all four length metrics, ascii+lines |
| `atomic::generated_len_metrics_mixed_width` | atomic | ## Metrics and Coordinate Conversion | covered | metrics on multibyte + supplementary plane |
| `atomic::generated_line_accessor_includes_terminator` | atomic | ## Reading Content | covered | line() includes break; empty last line |
| `atomic::generated_line_conversions` | atomic | ## Metrics and Coordinate Conversion | covered | byte/char<->line incl. one-past-end and len_lines input |
| `atomic::generated_line_partition_rules` | atomic | ## Line Semantics | covered | partition rules incl. trailing break, empty |
| `atomic::generated_lines_at_end_prev_returns_last_line` | atomic | ## Iterators | covered | end-positioned lines walk back |
| `atomic::generated_lines_iter_matches_line_accessor` | atomic | ## Iterators | covered | lines() equals line(i) sequence |
| `atomic::generated_new_and_default_are_empty` | atomic | ## Building and Persisting Text | covered | empty rope metrics incl. len_lines==1 |
| `atomic::generated_ord_is_bytewise_lexicographic` | atomic | ## Comparison, Ordering, and Hashing | covered | byte-lexicographic Ord; PartialOrd |
| `atomic::generated_positioned_iterators` | atomic | ## Iterators | covered | *_at starts, at-end None, get twins |
| `atomic::generated_prev_walks_backward` | atomic | ## Iterators | covered | prev inverse of next |
| `atomic::generated_remove_range_forms` | atomic | ## Editing | covered | all RangeBounds forms incl. inclusive and full |
| `atomic::generated_reverse_and_reversed` | atomic | ## Iterators | covered | reverse/reversed semantics |
| `atomic::generated_ropeslice_from_str_backed` | atomic | ## Slicing | covered | From<&str> slice; as_str Some cases |
| `atomic::generated_slice_basicforms` | atomic | ## Slicing | covered | slice ranges, full, empty |
| `atomic::generated_slice_conversions_out` | atomic | ## Slicing | covered | String/Cow/Rope out of a slice |
| `atomic::generated_slice_error_twins` | atomic | ## Slicing | covered | get_slice None on reversed/OOB |
| `atomic::generated_slice_of_slice_composes` | atomic | ## Slicing | covered | nested slice composition |
| `atomic::generated_slice_read_surface_local_coords` | atomic | ## Slicing | covered | local coordinates on sub-view |
| `atomic::generated_split_off_boundaries` | atomic | ## Editing | covered | split at 0/mid/len |
| `atomic::generated_str_utils_byte_char_clamp` | atomic | ## Metrics and Coordinate Conversion | covered | flat-string byte<->char clamping |
| `atomic::generated_str_utils_line_conversions` | atomic | ## Metrics and Coordinate Conversion | covered | flat-string line conversions clamp; LS break |
| `atomic::generated_string_and_cow_conversions` | atomic | ## Building and Persisting Text | covered | String/Cow out-conversions |
| `atomic::generated_try_conversion_error_payloads` | atomic | ## Error Semantics | covered | OOB variants with payloads |
| `atomic::generated_try_conversions_match_panicking_twins` | atomic | ## Metrics and Coordinate Conversion | covered | try_ twins agree on success |
| `atomic::generated_unicode_line_breaks_recognized` | atomic | ## Line Semantics | covered | VT/FF/NEL/LS/PS/CR/CRLF/LF set |
| `atomic::generated_utf16_conversions` | atomic | ## Metrics and Coordinate Conversion | covered | char<->utf16 incl. surrogate interior |
| `atomic::generated_write_to_emits_exact_bytes` | atomic | ## Building and Persisting Text | covered | write_to exact byte stream |
| `integration::cross_view::generated_content_determines_all_projections` | integration | ## Cross-View Invariants | covered | invariant 6 across three build paths |
| `integration::cross_view::generated_conversion_round_trips` | integration | ## Cross-View Invariants | covered | invariant 2 at every position |
| `integration::cross_view::generated_counts_match_iterators_everywhere` | integration | ## Cross-View Invariants | covered | invariant 1 over four documents |
| `integration::cross_view::generated_hash_agreement_rope_and_slices` | integration | ## Comparison, Ordering, and Hashing | covered | invariant: sub-slice hash == standalone |
| `integration::cross_view::generated_ordering_sorts_like_strings` | integration | ## Comparison, Ordering, and Hashing | covered | sorting ropes == sorting strings |
| `integration::cross_view::generated_segment_projections_reassemble` | integration | ## Cross-View Invariants | covered | invariant 3: chunks/lines/chars reassemble |
| `integration::cross_view::generated_utf16_cursor_mapping_workflow` | integration | ## Metrics and Coordinate Conversion | covered | utf16 cursor mapping + edit workflow |
| `integration::cross_view::generated_workflow_replace_word_across_views` | integration | ## Cross-View Invariants | covered | workflow: edit verified through 4 views |
| `integration::editing::generated_builder_vs_edit_vs_reader_equivalence` | integration | ## Building and Persisting Text | covered | four construction paths converge |
| `integration::editing::generated_edit_session_matches_string_model` | integration | ## Editing | covered | 10-step session vs flat-string model |
| `integration::editing::generated_edit_session_multibyte_boundaries` | integration | ## Editing | covered | multibyte edit session vs model |
| `integration::editing::generated_io_round_trip_after_edits` | integration | ## Building and Persisting Text | covered | read->edit->write->reread round trip |
| `integration::editing::generated_large_document_edit_consistency` | integration | ## Editing | covered | multi-chunk document: edits, chunks, conversions |
| `integration::editing::generated_persistent_snapshots_across_session` | integration | ## Building and Persisting Text | covered | snapshot clones survive edits |
| `integration::editing::generated_split_append_round_trip` | integration | ## Editing | covered | split_off+append restores original |
| `integration::iter_consistency::generated_chunks_at_walk_agrees_with_chunk_at` | integration | ## Reading Content | covered | chunk walk == chunk_at_byte at all starts |
| `integration::iter_consistency::generated_chunks_prev_walks_back_to_start` | integration | ## Iterators | covered | end-positioned chunk walk rebuilds text |
| `integration::iter_consistency::generated_exact_size_tracks_direction` | integration | ## Iterators | covered | len() tracks direction and movement |
| `integration::iter_consistency::generated_iterators_agree_between_rope_and_slice` | integration | ## Iterators | covered | rope *_at equals slice iterators |
| `integration::iter_consistency::generated_next_prev_alternation_is_stable` | integration | ## Iterators | covered | next/prev inverse at one position |
| `integration::iter_consistency::generated_positioned_sweep_bytes_chars` | integration | ## Iterators | covered | chars_at at every position vs model |
| `integration::iter_consistency::generated_reverse_walk_equals_forward_reversed` | integration | ## Iterators | covered | reversed == forward.rev() |
| `integration::lines_engine::generated_crlf_break_and_slice_split` | integration | ## Line Semantics | covered | slicing between CR and LF |
| `integration::lines_engine::generated_every_break_partitions_identically` | integration | ## Line Semantics | covered | all 8 break forms partition alike |
| `integration::lines_engine::generated_line_edits_move_breaks` | integration | ## Line Semantics | covered | join/split lines via edits |
| `integration::lines_engine::generated_lines_at_bidirectional_sweep` | integration | ## Iterators | covered | lines_at forward+backward at every start |
| `integration::lines_engine::generated_lines_reassemble_document` | integration | ## Line Semantics | covered | invariant 3 over mixed breaks |
| `integration::views::generated_edit_agrees_with_slice_reassembly` | integration | ## Cross-View Invariants | covered | invariant 4: edit == slice reassembly |
| `integration::views::generated_get_slice_boundary_matrix` | integration | ## Error Semantics | covered | nested slice failure values; slice-local lengths |
| `integration::views::generated_nested_slices_compose_deeply` | integration | ## Slicing | covered | three-level composition + byte_slice |
| `integration::views::generated_slice_conversion_round_trip` | integration | ## Slicing | covered | slice -> Rope/String round trip |
| `integration::views::generated_slice_local_coordinates_full_surface` | integration | ## Slicing | covered | full read surface on a line-anchored view |
| `integration::views::generated_str_backed_slice_matches_rope_backed` | integration | ## Slicing | covered | str-backed vs rope-backed parity |

## Section coverage summary

- ## Building and Persisting Text: 13 tests
- ## Comparison, Ordering, and Hashing: 5 tests
- ## Cross-View Invariants: 6 tests
- ## Editing: 10 tests
- ## Error Semantics: 6 tests
- ## Iterators: 17 tests
- ## Line Semantics: 7 tests
- ## Metrics and Coordinate Conversion: 10 tests
- ## Reading Content: 6 tests
- ## Slicing: 11 tests

All behavior sections, Error Semantics, and Cross-View Invariants meet
their per-section minimums. Narrative sections (Product Overview,
Non-Goals, Representative Workflows, State Model, Public Interface,
appendices) are exercised indirectly: the State Model's persistence
rules by the snapshot/clone tests, Representative Workflows by
`cross_view::generated_workflow_replace_word_across_views`, and the
Import Surface by every `use` line in the oracle.

Total: 91 | kept (covered): 91 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 91
