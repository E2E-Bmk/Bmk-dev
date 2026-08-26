# Specification coverage map — similar-fullrepro-001

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::generated_algorithm_selection` | atomic | ## Diff Algorithms and the Hook Protocol | covered | diff dispatch equals per-module entry points |
| `atomic::generated_capture_diff_matches_slices_shortcut` | atomic | ## Captured Operation Streams | covered | capture_diff equals slices shortcut |
| `atomic::generated_capture_diff_slices_doc` | atomic | ## Captured Operation Streams | covered | documented capture example |
| `atomic::generated_capture_empty_and_equal` | atomic | ## Captured Operation Streams | covered | empty inputs and identical inputs |
| `atomic::generated_change_accessors_and_display` | atomic | ## Text Diffing | covered | Change accessor family and Display |
| `atomic::generated_change_tag_display` | atomic | ## Text Diffing | covered | ChangeTag Display forms |
| `atomic::generated_close_matches_below_cutoff_empty` | atomic | ## Grouping and Similarity | covered | cutoff excludes weak candidates |
| `atomic::generated_default_replace_splits_into_delete_insert` | atomic | ## Diff Algorithms and the Hook Protocol | covered | DiffHook default ops_replace |
| `atomic::generated_diff_lines_doc` | atomic | ## Convenience Diff Functions and Remapping | covered | documented diff_lines example |
| `atomic::generated_diffable_str_inspection` | atomic | ## Text Diffing | covered | DiffableStr inspection helpers |
| `atomic::generated_diffable_str_ref_owned` | atomic | ## Text Diffing | covered | owned String accepted via DiffableStrRef |
| `atomic::generated_diffop_apply_to_hook` | atomic | ## Captured Operation Streams | covered | apply_to_hook replays an op |
| `atomic::generated_diffop_iter_changes_replace_order` | atomic | ## Captured Operation Streams | covered | Replace yields deletes then inserts |
| `atomic::generated_diffop_iter_slices` | atomic | ## Captured Operation Streams | covered | iter_slices tagged token slices |
| `atomic::generated_diffop_tag_tuples` | atomic | ## Captured Operation Streams | covered | tag/as_tag_tuple/ranges accessors |
| `atomic::generated_from_graphemes_changes` | atomic | ## Text Diffing | covered | from_graphemes change stream |
| `atomic::generated_from_slices_changes` | atomic | ## Text Diffing | covered | from_slices over arbitrary Eq+Hash tokens |
| `atomic::generated_from_unicode_words_changes` | atomic | ## Text Diffing | covered | from_unicode_words change stream |
| `atomic::generated_from_words_changes` | atomic | ## Text Diffing | covered | from_words change stream |
| `atomic::generated_get_diff_ratio_direct` | atomic | ## Grouping and Similarity | covered | get_diff_ratio free function |
| `atomic::generated_group_diff_ops_empty_and_all_equal` | atomic | ## Grouping and Similarity | covered | all-equal and empty op groups drop |
| `atomic::generated_group_diff_ops_small` | atomic | ## Grouping and Similarity | covered | grouping splits on large Equal gaps |
| `atomic::generated_hook_error_propagates` | atomic | ## Diff Algorithms and the Hook Protocol | covered | custom hook error propagates out of diff |
| `atomic::generated_hunk_header_formats` | atomic | ## Unified Diff Output | covered | UnifiedHunkHeader Display forms |
| `atomic::generated_inline_equal_single_unemphasized` | atomic | ## Inline Change Emphasis | covered | equal line: single unemphasized segment |
| `atomic::generated_inline_from_change` | atomic | ## Inline Change Emphasis | covered | InlineChange From<Change> |
| `atomic::generated_newline_terminated_flags` | atomic | ## Text Diffing | covered | newline_terminated flag per mode |
| `atomic::generated_nofinish_hook_swallows_finish` | atomic | ## Diff Algorithms and the Hook Protocol | covered | NoFinishHook blocks finish forwarding |
| `atomic::generated_old_new_slices_expose_tokens` | atomic | ## Text Diffing | covered | old_slices/new_slices token exposure |
| `atomic::generated_tokenize_lines_and_newlines` | atomic | ## Text Diffing | covered | lines vs newline-split forms |
| `atomic::generated_tokenize_unicode_words` | atomic | ## Text Diffing | covered | unicode-word segmentation |
| `atomic::generated_utils_diff_chars` | atomic | ## Convenience Diff Functions and Remapping | covered | diff_chars slices |
| `atomic::generated_utils_diff_graphemes` | atomic | ## Convenience Diff Functions and Remapping | covered | diff_graphemes slices |
| `atomic::generated_utils_diff_lines` | atomic | ## Convenience Diff Functions and Remapping | covered | diff_lines slices |
| `atomic::generated_utils_diff_slices` | atomic | ## Convenience Diff Functions and Remapping | covered | diff_slices over token arrays |
| `atomic::generated_utils_diff_unicode_words` | atomic | ## Convenience Diff Functions and Remapping | covered | diff_unicode_words slices |
| `atomic::generated_utils_diff_words_values` | atomic | ## Convenience Diff Functions and Remapping | covered | diff_words slices |
| `atomic::test_captured_ops` | atomic | ## Captured Operation Streams | covered | capture_diff_slices op stream |
| `atomic::test_char_diff` | atomic | ## Text Diffing | covered | from_chars change stream |
| `atomic::test_empty_unified_diff` | atomic | ## Unified Diff Output | covered | equal inputs render empty diff |
| `atomic::test_get_close_matches` | atomic | ## Grouping and Similarity | covered | close-match selection |
| `atomic::test_lcs_bad_range_regression` | atomic | ## Diff Algorithms and the Hook Protocol | covered | LCS range regression stays panic-free |
| `atomic::test_lcs_contiguous_ops` | atomic | ## Diff Algorithms and the Hook Protocol | covered | LCS op ranges are contiguous |
| `atomic::test_lcs_diff_ops` | atomic | ## Diff Algorithms and the Hook Protocol | covered | LCS via capture on slices |
| `atomic::test_lcs_finish_called` | atomic | ## Diff Algorithms and the Hook Protocol | covered | finish forwarded once |
| `atomic::test_lcs_same_single_equal` | atomic | ## Diff Algorithms and the Hook Protocol | covered | identical inputs -> single Equal |
| `atomic::test_lifetimes_on_iter` | atomic | ## Text Diffing | covered | iterators outlive the TextDiff borrow |
| `atomic::test_myers_contiguous_ops` | atomic | ## Diff Algorithms and the Hook Protocol | covered | Myers op ranges are contiguous |
| `atomic::test_myers_diff_ops` | atomic | ## Diff Algorithms and the Hook Protocol | covered | Myers via capture on slices |
| `atomic::test_myers_finish_called` | atomic | ## Diff Algorithms and the Hook Protocol | covered | finish forwarded once |
| `atomic::test_myers_raw_capture_minimal_script` | atomic | ## Diff Algorithms and the Hook Protocol | covered | raw hook stream is a valid minimal script |
| `atomic::test_non_string_iter_change` | atomic | ## Text Diffing | covered | iter_changes over non-string slices |
| `atomic::test_patience_diff_ops` | atomic | ## Diff Algorithms and the Hook Protocol | covered | Patience via capture on slices |
| `atomic::test_patience_finish_called` | atomic | ## Diff Algorithms and the Hook Protocol | covered | finish forwarded once |
| `atomic::test_patience_shrink_ops` | atomic | ## Diff Algorithms and the Hook Protocol | covered | Patience unique-anchor split |
| `atomic::test_ratio` | atomic | ## Grouping and Similarity | covered | TextDiff ratio |
| `atomic::test_remapper` | atomic | ## Convenience Diff Functions and Remapping | covered | TextDiffRemapper maps tokens back to slices |
| `atomic::test_replace_merges_delete_insert` | atomic | ## Diff Algorithms and the Hook Protocol | covered | Replace merges adjacent delete+insert |
| `atomic::test_replace_merges_on_line_slices` | atomic | ## Diff Algorithms and the Hook Protocol | covered | Replace on line slices |
| `atomic::test_split_chars` | atomic | ## Text Diffing | covered | char tokenizer |
| `atomic::test_split_graphemes` | atomic | ## Text Diffing | covered | grapheme tokenizer keeps clusters whole |
| `atomic::test_split_lines` | atomic | ## Text Diffing | covered | line tokenizer retains terminators |
| `atomic::test_split_words` | atomic | ## Text Diffing | covered | whitespace-word tokenizer round trip |
| `atomic::test_virtual_newlines` | atomic | ## Text Diffing | covered | missing trailing newline handling in changes |
| `integration::cross_view::generated_close_matches_agree_with_char_ratio` | integration | ## Cross-View Invariants | covered | close matches respect cutoff and ordering |
| `integration::cross_view::generated_deadline_still_valid_script` | integration | ## Cross-View Invariants | covered | deadline run still yields valid script |
| `integration::cross_view::generated_identify_distinct_equivalence` | integration | ## Cross-View Invariants | covered | IdentifyDistinct produces identical ops |
| `integration::cross_view::generated_iter_all_changes_equals_flat_map` | integration | ## Cross-View Invariants | covered | iter_all_changes equals per-op flat map |
| `integration::cross_view::generated_manual_stack_equals_capture_diff` | integration | ## Cross-View Invariants | covered | manual Replace/Capture stack equals capture_diff |
| `integration::cross_view::generated_ratio_equals_get_diff_ratio` | integration | ## Cross-View Invariants | covered | ratio equals get_diff_ratio on same ops |
| `integration::cross_view::generated_reconstruction_all_algorithms` | integration | ## Cross-View Invariants | covered | ops replay reconstructs new sequence, all algorithms |
| `integration::cross_view::generated_remapper_iter_slices_cover` | integration | ## Cross-View Invariants | covered | remapped slices cover both originals |
| `integration::cross_view::generated_text_vs_generic_ops_large` | integration | ## Cross-View Invariants | covered | same equivalence on larger input |
| `integration::cross_view::generated_text_vs_generic_ops_small` | integration | ## Cross-View Invariants | covered | TextDiff ops equal generic capture ops |
| `integration::cross_view::generated_utils_concat_covers_inputs` | integration | ## Cross-View Invariants | covered | utils outputs concatenate to inputs |
| `integration::cross_view::generated_workflow_line_diff_signs` | integration | ## Cross-View Invariants | covered | workflow: sign-rendered line diff |
| `integration::grouping::generated_grouped_ops_matches_free_function` | integration | ## Grouping and Similarity | covered | TextDiff::grouped_ops equals group_diff_ops |
| `integration::grouping::generated_into_grouped_ops_matches_group_diff_ops` | integration | ## Grouping and Similarity | covered | Capture grouping equals free function |
| `integration::grouping::test_capture_hook_grouping` | integration | ## Grouping and Similarity | covered | Capture::into_grouped_ops on captured stream |
| `integration::inline::generated_inline_coverage_invariant` | integration | ## Inline Change Emphasis | covered | segments concatenate to underlying line |
| `integration::inline::generated_inline_deadline_variant_agrees` | integration | ## Inline Change Emphasis | covered | deadline variant agrees without deadline |
| `integration::inline::generated_inline_simple_word_replace` | integration | ## Inline Change Emphasis | covered | changed words emphasized |
| `integration::inline::test_line_ops_inline` | integration | ## Inline Change Emphasis | covered | inline emphasis over multi-line diff |
| `integration::udiff::generated_unified_hunks_match_grouped_ops` | integration | ## Unified Diff Output | covered | iter_hunks aligns with grouped_ops |
| `integration::udiff::generated_unified_no_hunks_no_header` | integration | ## Unified Diff Output | covered | no hunks -> headers suppressed |
| `integration::udiff::generated_unified_quick_fn_equals_pipeline` | integration | ## Unified Diff Output | covered | udiff() equals TextDiff pipeline output |
| `integration::udiff::generated_unified_to_writer_matches_display` | integration | ## Unified Diff Output | covered | to_writer equals Display |
| `integration::udiff::test_unified_diff_newline_hint` | integration | ## Unified Diff Output | covered | missing-newline hint toggling |
| `integration::udiff::test_unified_diff_simple` | integration | ## Unified Diff Output | covered | full unified rendering with headers |
| `integration::udiff::test_unified_diff_two_hunks` | integration | ## Unified Diff Output | covered | two-hunk rendering with context radius |
| `integration::udiff::test_unified_diff_zero_radius_empty_ranges` | integration | ## Unified Diff Output | covered | zero-radius empty-range hunk headers |

## Section coverage summary

- ## Captured Operation Streams: 8 tests
- ## Convenience Diff Functions and Remapping: 8 tests
- ## Cross-View Invariants: 12 tests
- ## Diff Algorithms and the Hook Protocol: 18 tests
- ## Grouping and Similarity: 9 tests
- ## Inline Change Emphasis: 6 tests
- ## Text Diffing: 20 tests
- ## Unified Diff Output: 10 tests

Sections without dedicated rows (## Product Overview, ## Non-Goals,
## Representative Workflows, ## State Model, ## Error Semantics,
## Public Interface, appendices) are narrative or are exercised
indirectly: State Model borrow/lifetime rules by
`atomic::test_lifetimes_on_iter`, Error Semantics by
`atomic::generated_hook_error_propagates` and the unified-diff
formatting error path, and the Import Surface by every `use` line in
the oracle.
