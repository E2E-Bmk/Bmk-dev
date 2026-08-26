# Specification coverage map — textwrap-fullrepro-001

oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary
plus full suite runs on both the patched path and the registry lock;
upstream tests served as a behavioral checklist only — see
rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::generated_ascii_space_attaches_runs` | atomic | ## Words, Fragments, and Measurement | covered | AsciiSpace attaches space runs; tab is content |
| `atomic::generated_break_words_only_overlong` | atomic | ## Words, Fragments, and Measurement | covered | break_words replaces only overlong words |
| `atomic::generated_custom_separator_delegates` | atomic | ## Words, Fragments, and Measurement | covered | Custom separator delegates |
| `atomic::generated_custom_splitter_delegates` | atomic | ## Words, Fragments, and Measurement | covered | Custom splitter delegates |
| `atomic::generated_dedent_no_trailing_newline_invented` | atomic | ## Refilling and Indentation | covered | no trailing newline invented |
| `atomic::generated_dedent_removes_common_prefix` | atomic | ## Refilling and Indentation | covered | dedent removes common leading whitespace |
| `atomic::generated_dedent_whitespace_only_lines_emptied` | atomic | ## Refilling and Indentation | covered | whitespace-only lines emptied, non-constraining |
| `atomic::generated_display_width_ascii_cjk_emoji` | atomic | ## Words, Fragments, and Measurement | covered | ASCII/CJK/emoji column widths |
| `atomic::generated_display_width_combining_mark_zero` | atomic | ## Words, Fragments, and Measurement | covered | combining marks zero width |
| `atomic::generated_display_width_skips_csi_sequences` | atomic | ## Words, Fragments, and Measurement | covered | CSI sequences contribute zero width |
| `atomic::generated_display_width_skips_osc_hyperlinks` | atomic | ## Words, Fragments, and Measurement | covered | OSC hyperlink sequences skipped |
| `atomic::generated_fill_inplace_greedy` | atomic | ## Wrapping and Filling | covered | fill_inplace greedy first-fit |
| `atomic::generated_fill_inplace_never_breaks_words` | atomic | ## Wrapping and Filling | covered | fill_inplace never breaks words |
| `atomic::generated_fill_inplace_replaces_last_space_of_run` | atomic | ## Wrapping and Filling | covered | last space of run replaced with newline |
| `atomic::generated_fill_joins_with_crlf` | atomic | ## Wrapping and Filling | covered | fill joins with configured CRLF |
| `atomic::generated_fill_joins_with_lf` | atomic | ## Wrapping and Filling | covered | fill joins with LF default |
| `atomic::generated_fill_keeps_empty_lines` | atomic | ## Wrapping and Filling | covered | fill preserves paragraph separation |
| `atomic::generated_hyphen_splitter_needs_alphanumerics` | atomic | ## Words, Fragments, and Measurement | covered | alphanumeric-surrounded hyphen rule |
| `atomic::generated_hyphen_splitter_offsets` | atomic | ## Words, Fragments, and Measurement | covered | split points after hyphens |
| `atomic::generated_indent_adds_prefix` | atomic | ## Refilling and Indentation | covered | indent adds prefix to lines |
| `atomic::generated_indent_keeps_line_content_and_no_invented_newline` | atomic | ## Refilling and Indentation | covered | content kept; no invented newline |
| `atomic::generated_indent_trims_prefix_on_empty_lines` | atomic | ## Refilling and Indentation | covered | trimmed prefix on empty lines |
| `atomic::generated_indent_whitespace_prefix_keeps_empty_lines_empty` | atomic | ## Refilling and Indentation | covered | whitespace prefix leaves empty lines empty |
| `atomic::generated_line_ending_as_str` | atomic | ## Wrapping Configuration | covered | LineEnding::as_str values |
| `atomic::generated_no_hyphenation_never_splits` | atomic | ## Words, Fragments, and Measurement | covered | NoHyphenation returns no offsets |
| `atomic::generated_optimal_fit_evens_lines` | atomic | ## Line-Breaking Algorithms and the Penalty Model | covered | optimal-fit evens line lengths |
| `atomic::generated_optimal_fit_overflow_error` | atomic | ## Error Semantics | covered | OverflowError on huge widths; Ok on sane |
| `atomic::generated_optimal_fit_short_last_line_penalty` | atomic | ## Line-Breaking Algorithms and the Penalty Model | covered | short-last-line tuning effects |
| `atomic::generated_options_builder_methods_chain` | atomic | ## Wrapping Configuration | covered | chained builder methods replace settings |
| `atomic::generated_options_fields_directly_assignable` | atomic | ## Wrapping Configuration | covered | public fields readable and assignable |
| `atomic::generated_options_from_reference_copies` | atomic | ## Wrapping Configuration | covered | From<&Options> copies settings |
| `atomic::generated_options_from_usize` | atomic | ## Wrapping Configuration | covered | From<usize> conversion |
| `atomic::generated_options_new_defaults` | atomic | ## Wrapping Configuration | covered | Options::new default settings |
| `atomic::generated_penalties_defaults` | atomic | ## Line-Breaking Algorithms and the Penalty Model | covered | Penalties defaults and Default impl |
| `atomic::generated_refill_converts_line_endings` | atomic | ## Refilling and Indentation | covered | refill converts line endings |
| `atomic::generated_refill_rewraps_with_inferred_prefix` | atomic | ## Refilling and Indentation | covered | refill keeps inferred prefixes |
| `atomic::generated_separator_equality` | atomic | ## Words, Fragments, and Measurement | covered | named variants equal; Custom never equal |
| `atomic::generated_split_words_assigns_hyphen_penalty` | atomic | ## Words, Fragments, and Measurement | covered | non-final pieces get '-' penalty |
| `atomic::generated_split_words_hyphen_pieces_no_extra_penalty` | atomic | ## Words, Fragments, and Measurement | covered | pieces already ending '-' get no penalty |
| `atomic::generated_splitter_equality` | atomic | ## Words, Fragments, and Measurement | covered | splitter equality semantics |
| `atomic::generated_unfill_comment_prefix_and_trailing_ending` | atomic | ## Refilling and Indentation | covered | prefix character set; trailing ending kept |
| `atomic::generated_unfill_detects_crlf` | atomic | ## Refilling and Indentation | covered | CRLF detection |
| `atomic::generated_unfill_infers_list_item_prefixes` | atomic | ## Refilling and Indentation | covered | first-line vs common prefix inference |
| `atomic::generated_unfill_joins_and_reports_width` | atomic | ## Refilling and Indentation | covered | unfill joins with single spaces; width report |
| `atomic::generated_unfill_mixed_endings_report_lf` | atomic | ## Refilling and Indentation | covered | mixed endings report LF |
| `atomic::generated_unfill_narrows_common_prefix` | atomic | ## Refilling and Indentation | covered | common prefix narrowed across lines |
| `atomic::generated_unicode_separator_no_break_at_hyphen` | atomic | ## Words, Fragments, and Measurement | covered | no break at hyphen-minus divergence |
| `atomic::generated_unicode_separator_splits_cjk` | atomic | ## Words, Fragments, and Measurement | covered | Unicode breaks between ideographs |
| `atomic::generated_unicode_separator_splits_emoji_run` | atomic | ## Words, Fragments, and Measurement | covered | Unicode breaks between emoji |
| `atomic::generated_unicode_separator_word_joiner_suppresses_break` | atomic | ## Words, Fragments, and Measurement | covered | U+2060 suppresses break |
| `atomic::generated_word_break_apart_pieces` | atomic | ## Words, Fragments, and Measurement | covered | break_apart piece shapes |
| `atomic::generated_word_derefs_to_content` | atomic | ## Words, Fragments, and Measurement | covered | Word derefs to its content |
| `atomic::generated_word_fragment_measurement` | atomic | ## Words, Fragments, and Measurement | covered | Fragment widths of a Word |
| `atomic::generated_word_from_splits_trailing_whitespace` | atomic | ## Words, Fragments, and Measurement | covered | Word::from content/whitespace split |
| `atomic::generated_wrap_accepts_width_options_and_reference` | atomic | ## Wrapping and Filling | covered | width-or-options argument forms |
| `atomic::generated_wrap_algorithm_constructors_and_equality` | atomic | ## Line-Breaking Algorithms and the Penalty Model | covered | constructors and equality semantics |
| `atomic::generated_wrap_algorithm_wrap_repeats_last_width` | atomic | ## Line-Breaking Algorithms and the Penalty Model | covered | usize width slice, last repeated |
| `atomic::generated_wrap_borrows_without_indent` | atomic | ## Wrapping and Filling | covered | borrowed Cow without indent |
| `atomic::generated_wrap_break_words_chunks_long_word` | atomic | ## Wrapping and Filling | covered | break_words=true chunks at character boundaries |
| `atomic::generated_wrap_carriage_return_is_content` | atomic | ## Wrapping and Filling | covered | CR is word content, not a delimiter |
| `atomic::generated_wrap_columns_empty_text_blank_row` | atomic | ## Column Layout | covered | empty text yields one blank row |
| `atomic::generated_wrap_columns_equal_row_widths` | atomic | ## Column Layout | covered | uniform row display width |
| `atomic::generated_wrap_columns_layout` | atomic | ## Column Layout | covered | column arithmetic and distribution |
| `atomic::generated_wrap_columns_zero_columns_panics` | atomic | ## Error Semantics | covered | zero columns panics (positive check first) |
| `atomic::generated_wrap_empty_string_one_empty_line` | atomic | ## Wrapping and Filling | covered | empty string yields one empty line |
| `atomic::generated_wrap_first_fit_custom_fragment_type` | atomic | ## Line-Breaking Algorithms and the Penalty Model | covered | Fragment genericity |
| `atomic::generated_wrap_first_fit_greedy` | atomic | ## Line-Breaking Algorithms and the Penalty Model | covered | greedy first-fit grouping |
| `atomic::generated_wrap_indent_applied_to_empty_output_line` | atomic | ## Wrapping and Filling | covered | indent prepended verbatim to empty output lines |
| `atomic::generated_wrap_indent_counts_toward_width` | atomic | ## Wrapping and Filling | covered | indent width counts toward line width |
| `atomic::generated_wrap_initial_and_subsequent_indents` | atomic | ## Wrapping and Filling | covered | initial vs subsequent indent placement |
| `atomic::generated_wrap_interword_spaces_kept_on_same_line` | atomic | ## Wrapping and Filling | covered | inter-word whitespace preserved verbatim |
| `atomic::generated_wrap_leading_whitespace_kept` | atomic | ## Wrapping and Filling | covered | leading whitespace preserved on first output line |
| `atomic::generated_wrap_lone_newline_two_empty_lines` | atomic | ## Wrapping and Filling | covered | LF-only input splitting |
| `atomic::generated_wrap_no_break_words_overflows` | atomic | ## Wrapping and Filling | covered | break_words=false overflow line |
| `atomic::generated_wrap_owns_with_indent` | atomic | ## Wrapping and Filling | covered | owned Cow with indent prefix |
| `atomic::generated_wrap_plain_width_exact_lines` | atomic | ## Wrapping and Filling | covered | wrap with plain usize width |
| `atomic::generated_wrap_preserves_paragraph_break` | atomic | ## Wrapping and Filling | covered | empty input line survives |
| `atomic::generated_wrap_trailing_break_whitespace_dropped` | atomic | ## Wrapping and Filling | covered | no trailing whitespace from wrapping |
| `atomic::generated_wrap_width_zero_one_word_per_line` | atomic | ## Wrapping and Filling | covered | zero width legal; one-char pieces |
| `integration::columns_layout::generated_columns_match_manual_distribution` | integration | ## Column Layout + ## State Model | covered | documented arithmetic reproduced |
| `integration::columns_layout::generated_columns_of_empty_text_single_blank_row` | integration | ## Column Layout + ## Wrapping and Filling | covered | empty text single blank row |
| `integration::columns_layout::generated_columns_respect_caller_options` | integration | ## Column Layout + ## Wrapping Configuration | covered | caller options pass through |
| `integration::columns_layout::generated_columns_uniform_width_and_gaps` | integration | ## Cross-View Invariants + ## Column Layout | covered | invariant 6: uniform width, gap placement |
| `integration::columns_layout::generated_columns_width_floor_of_one` | integration | ## Column Layout + ## Error Semantics | covered | column width floors at one |
| `integration::consistency::generated_ansi_sequences_consume_no_width` | integration | ## Words, Fragments, and Measurement + ## Wrapping and Filling | covered | ANSI sequences free through wrap |
| `integration::consistency::generated_break_words_false_full_pipeline` | integration | ## Wrapping and Filling + ## Words, Fragments, and Measurement | covered | hyphen split with overflow piece |
| `integration::consistency::generated_cjk_width_discipline` | integration | ## Words, Fragments, and Measurement + ## Wrapping and Filling | covered | double-width discipline through wrap |
| `integration::consistency::generated_hyphenated_wrap_end_to_end` | integration | ## Wrapping and Filling + ## Words, Fragments, and Measurement | covered | default hyphen splitting end to end |
| `integration::consistency::generated_line_ending_only_affects_fill` | integration | ## Wrapping Configuration + ## Wrapping and Filling | covered | line ending affects only fill joining |
| `integration::consistency::generated_options_conversion_equivalence` | integration | ## Cross-View Invariants + ## Wrapping Configuration | covered | invariant 8: conversion equivalence |
| `integration::consistency::generated_width_bound_matrix` | integration | ## Cross-View Invariants + ## Words, Fragments, and Measurement | covered | invariant 7: display-width bound matrix |
| `integration::consistency::generated_wrap_indent_unfill_family` | integration | ## Wrapping and Filling + ## Refilling and Indentation | covered | list-item family across wrap and unfill |
| `integration::fill_refill::generated_fill_equals_wrap_joined` | integration | ## Cross-View Invariants + ## Wrapping and Filling | covered | invariant 1 across texts, widths, endings |
| `integration::fill_refill::generated_fill_equals_wrap_joined_with_indents` | integration | ## Cross-View Invariants + ## Wrapping and Filling | covered | invariant 1 with indents |
| `integration::fill_refill::generated_fill_inplace_matches_restricted_fill` | integration | ## Wrapping and Filling + ## Wrapping Configuration | covered | fill_inplace equals restricted fill |
| `integration::fill_refill::generated_fill_then_unfill_recovers_list_prefixes` | integration | ## Refilling and Indentation + ## Wrapping and Filling | covered | indented fill read back through unfill |
| `integration::fill_refill::generated_refill_equals_fresh_fill` | integration | ## Cross-View Invariants + ## Refilling and Indentation | covered | invariant 3: refill equals fresh fill |
| `integration::fill_refill::generated_refill_line_ending_swap_roundtrip` | integration | ## Refilling and Indentation + ## Wrapping Configuration | covered | line-ending swap roundtrip |
| `integration::fill_refill::generated_unfill_fill_roundtrip` | integration | ## Cross-View Invariants + ## Refilling and Indentation | covered | invariant 3: unfill(fill) roundtrip |
| `integration::fill_refill::generated_unfill_width_reports_widest_line` | integration | ## Refilling and Indentation + ## Wrapping and Filling | covered | unfill width equals widest filled line |
| `integration::indent_dedent::generated_dedent_then_reindent_shifts_margin` | integration | ## Refilling and Indentation | covered | dedent then indent shifts margin |
| `integration::indent_dedent::generated_fill_with_indents_equals_indent_of_fill` | integration | ## Cross-View Invariants + ## Refilling and Indentation | covered | invariant 4: fill+indents equals indent(fill) |
| `integration::indent_dedent::generated_indent_dedent_roundtrip` | integration | ## Cross-View Invariants + ## Refilling and Indentation | covered | invariant 5: dedent(indent) roundtrip |
| `integration::indent_dedent::generated_indent_empty_prefix_identity` | integration | ## Refilling and Indentation + ## Wrapping and Filling | covered | empty prefix identity incl. CR content |
| `integration::indent_dedent::generated_indent_marker_then_dedent_partial` | integration | ## Refilling and Indentation | covered | marker prefixes survive dedent |
| `integration::pipeline::generated_custom_algorithm_drives_wrap` | integration | ## State Model + ## Wrapping Configuration | covered | Custom algorithm drives wrap |
| `integration::pipeline::generated_custom_separator_drives_wrap` | integration | ## State Model + ## Wrapping Configuration | covered | Custom separator drives wrap |
| `integration::pipeline::generated_first_fit_pipeline_matches_wrap` | integration | ## Cross-View Invariants + ## State Model | covered | invariant 2: manual pipeline equals wrap (first-fit matrix) |
| `integration::pipeline::generated_hanging_indent_width_slices` | integration | ## Line-Breaking Algorithms and the Penalty Model + ## Wrapping and Filling | covered | indents become per-line width slices |
| `integration::pipeline::generated_hyphen_splitter_pipeline_matches_wrap` | integration | ## State Model + ## Words, Fragments, and Measurement | covered | split_words stage composes into wrap |
| `integration::pipeline::generated_optimal_fit_pipeline_matches_wrap` | integration | ## Cross-View Invariants + ## Line-Breaking Algorithms and the Penalty Model | covered | manual optimal-fit pipeline equals wrap |

Per-section coverage (a test with `A + B` counts once for each):

- ## Column Layout: 8 tests
- ## Cross-View Invariants: 11 tests
- ## Error Semantics: 3 tests
- ## Line-Breaking Algorithms and the Penalty Model: 9 tests
- ## Refilling and Indentation: 26 tests
- ## State Model: 5 tests
- ## Words, Fragments, and Measurement: 29 tests
- ## Wrapping Configuration: 13 tests
- ## Wrapping and Filling: 37 tests

Total: 111 | kept (covered): 111 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 111
Layers: atomic 79 | integration 32
depends_on annotation coverage: 32/32 integration tests (100%)
