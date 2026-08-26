# Specification coverage map — fluent-syntax-fullrepro-001


oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
four rounds, plus full suite runs on both the patched path and the
registry lock; upstream tests and the 36 doc examples served as a
behavioral checklist only — see rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| `atomic::generated_message_ast_shape` | atomic | positive | ## Resource Grammar and Entry Model | covered | full Message node equality for a one-line message |
| `atomic::generated_term_ast_shape` | atomic | positive | ## Resource Grammar and Entry Model | covered | leading `-` stripped from Term::id; required value |
| `atomic::generated_identifier_charset` | atomic | positive | ## Resource Grammar and Entry Model | covered | letters/digits/-/_ accepted; digit start junks with a-zA-Z range |
| `atomic::generated_message_attributes_only` | atomic | positive | ## Resource Grammar and Entry Model | covered | value None with one attribute |
| `atomic::generated_attributes_in_order_varied_indent` | atomic | positive | ## Resource Grammar and Entry Model | covered | attribute order kept across differing indents |
| `atomic::generated_empty_and_blank_inputs` | atomic | positive | ## Resource Grammar and Entry Model | covered | empty and blank-only inputs parse to empty bodies |
| `atomic::generated_entries_in_order` | atomic | positive | ## Resource Grammar and Entry Model | covered | message/term/message input order preserved |
| `atomic::generated_spaces_around_equals` | atomic | positive | ## Resource Grammar and Entry Model | covered | spaces around = skipped on both sides |
| `atomic::generated_common_indent_excess` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | minimum indent stripped; deeper lines keep excess |
| `atomic::generated_blank_line_element` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | interior blank line survives as a line-feed element |
| `atomic::generated_blank_line_excess_spaces` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | blank-line spaces beyond the common indent survive |
| `atomic::generated_inline_then_continuation` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | inline first line verbatim; continuation dedented |
| `atomic::generated_trailing_trim` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | trailing blank lines and spaces trimmed |
| `atomic::generated_zero_column_placeable_continues` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | column-zero `{` continues; pins common indent to zero |
| `atomic::generated_zero_column_text_breaks` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | column-zero text ends the pattern |
| `atomic::generated_bracket_line_breaks_pattern` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | indented `[` line ends the pattern; leftover junks |
| `atomic::generated_placeable_line_indent_dropped` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | indent before line-leading `{` vanishes, no common-indent vote |
| `atomic::generated_crlf_element_split` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | CRLF drops the CR and splits a standalone \n element |
| `atomic::generated_text_around_placeable` | atomic | positive | ## Pattern Text: Lines, Indentation, Dedent | covered | text on both sides of a placeable in one line |
| `atomic::generated_variable_reference_ast` | atomic | positive | ## Placeables and Expressions | covered | $id form |
| `atomic::generated_string_literal_raw` | atomic | positive | ## Placeables and Expressions | covered | escapes stored raw in the literal value |
| `atomic::generated_number_literal_raw` | atomic | positive | ## Placeables and Expressions | covered | raw spelling kept: 007, -0.50 |
| `atomic::generated_message_reference_forms` | atomic | positive | ## Placeables and Expressions | covered | bare and .attr message references |
| `atomic::generated_term_reference_args` | atomic | positive | ## Placeables and Expressions | covered | -id with named call arguments |
| `atomic::generated_function_reference` | atomic | positive | ## Placeables and Expressions | covered | positional + named arguments on an uppercase callee |
| `atomic::generated_nested_placeable_ast` | atomic | positive | ## Placeables and Expressions | covered | {{ … }} boxes an inner expression |
| `atomic::generated_callee_case_rule` | atomic | positive | ## Placeables and Expressions | covered | lowercase callee ForbiddenCallee; GRID-2 accepted |
| `atomic::generated_named_arg_literal_only` | atomic | positive | ## Placeables and Expressions | covered | non-literal named value ExpectedLiteral; literal sibling parses |
| `atomic::generated_arg_ordering_rules` | atomic | failure_path | ## Placeables and Expressions | covered | positional-after-named and duplicate-name rejections |
| `atomic::generated_trailing_comma_empty_args` | atomic | positive | ## Placeables and Expressions | covered | trailing comma legal; () yields empty vectors |
| `atomic::generated_term_attr_placeable_error` | atomic | positive | ## Placeables and Expressions | covered | -id.attr illegal as placeable; message .attr legal |
| `atomic::generated_string_escapes_accepted` | atomic | positive | ## Placeables and Expressions | covered | all five escape forms parse and stay raw |
| `atomic::generated_unknown_escape_err` | atomic | positive | ## Error Semantics | covered | UnknownEscapeSequence junks the entry; escaped sibling parses |
| `atomic::generated_bad_unicode_and_unterminated` | atomic | failure_path | ## Error Semantics | covered | InvalidUnicodeEscapeSequence and UnterminatedStringLiteral kinds |
| `atomic::generated_select_ast` | atomic | positive | ## Select Expressions | covered | selector, variant keys/values, default flag as full nodes |
| `atomic::generated_variant_number_keys` | atomic | positive | ## Select Expressions | covered | negative and fractional number keys; blanks inside brackets |
| `atomic::generated_selector_legality` | atomic | positive | ## Select Expressions | covered | three illegal selector kinds; term.attr selector parses |
| `atomic::generated_default_rules` | atomic | failure_path | ## Select Expressions | covered | no default and two defaults rejected |
| `atomic::generated_variant_order_preserved` | atomic | positive | ## Select Expressions | covered | default position and variant order preserved |
| `atomic::generated_selector_line_end_required` | atomic | failure_path | ## Select Expressions | covered | text after -> rejected with the \n | \r\n range |
| `atomic::generated_variant_missing_value` | atomic | failure_path | ## Select Expressions | covered | valueless variant MissingValue |
| `atomic::generated_comment_levels` | atomic | positive | ## Comments and Attachment | covered | #/##/### map to the three entry kinds |
| `atomic::generated_comment_attaches` | atomic | positive | ## Comments and Attachment | covered | adjacent regular comment lands on message and term nodes |
| `atomic::generated_blank_line_detaches` | atomic | positive | ## Comments and Attachment | covered | blank line keeps the comment standalone |
| `atomic::generated_group_resource_never_attach` | atomic | positive | ## Comments and Attachment | covered | group/resource comments never attach |
| `atomic::generated_comment_block_merge_split` | atomic | positive | ## Comments and Attachment | covered | same-level lines merge; level change splits and detaches |
| `atomic::generated_empty_comment_lines` | atomic | positive | ## Comments and Attachment | covered | bare markers contribute empty content lines |
| `atomic::generated_malformed_comment_junk` | atomic | positive | ## Comments and Attachment | covered | #text junks with ExpectedToken(' ') and exact pos/slice |
| `atomic::generated_runtime_strips_comments` | atomic | positive | ## Comments and Attachment | covered | runtime mode drops all comment levels and fields |
| `atomic::generated_runtime_skips_malformed_comment` | atomic | positive | ## Comments and Attachment | covered | runtime mode silently skips the malformed line |
| `atomic::generated_missing_equals_error` | atomic | positive | ## Error Recovery and Junk | covered | ExpectedToken('=') with exact pos/slice; neighbors survive |
| `atomic::generated_junk_absorbs_trailing_blanks` | atomic | positive | ## Error Recovery and Junk | covered | junk span includes trailing blank lines |
| `atomic::generated_junk_stops_at_entry_starters` | atomic | positive | ## Error Recovery and Junk | covered | letter/-/# lines end the junk span |
| `atomic::generated_missing_field_errors` | atomic | positive | ## Error Recovery and Junk | covered | ExpectedMessageField/ExpectedTermField carry entry ids; spans junk |
| `atomic::generated_unbalanced_brace` | atomic | positive | ## Error Recovery and Junk | covered | stray } junks the whole entry |
| `atomic::generated_error_records_eq_clone` | atomic | failure_path | ## Error Semantics | covered | ParserError full-value equality and clone |
| `atomic::generated_serialize_message_term_canonical` | atomic | positive | ## Serialization | covered | canonical one-line message and term are fixed points |
| `atomic::generated_serialize_normalizes_spacing` | atomic | positive | ## Serialization | covered | spacing and missing newline normalized |
| `atomic::generated_serialize_multiline_form` | atomic | positive | ## Serialization | covered | multiline patterns start on a new line at 4-space indent |
| `atomic::generated_serialize_attributes` | atomic | positive | ## Serialization | covered | attributes one level deep; attribute-only messages |
| `atomic::generated_serialize_select_star_indent` | atomic | positive | ## Serialization | covered | select shape with * drawn into the indent |
| `atomic::generated_serialize_placeable_forms` | atomic | positive | ## Serialization | covered | { e } spacing, {{ e }} collapse, tight text adjacency |
| `atomic::generated_serialize_references` | atomic | positive | ## Serialization | covered | literals and references render in source notation |
| `atomic::generated_serialize_junk_toggle` | atomic | positive | ## Serialization | covered | junk skipped by default, verbatim with with_junk; Options surface |
| `atomic::generated_serialize_comment_framing` | atomic | positive | ## Serialization | covered | attached comments hug; free comments blank-line framed |
| `atomic::generated_serialize_handbuilt_ast` | atomic | positive | ## Serialization | covered | hand-built tree renders canonically |
| `atomic::generated_unescape_basic` | atomic | positive | ## Unicode Unescaping | covered | backslash and quote escapes decode |
| `atomic::generated_unescape_four_and_six` | atomic | positive | ## Unicode Unescaping | covered | \u and \U decode fresh scalar values |
| `atomic::generated_unescape_replacement_rules` | atomic | positive | ## Unicode Unescaping | covered | U+FFFD for unknown/bad-hex/out-of-range/truncated/trailing |
| `atomic::generated_unescape_cow` | atomic | positive | ## Unicode Unescaping | covered | borrowed without backslash, owned with |
| `atomic::generated_unescape_writer` | atomic | positive | ## Unicode Unescaping | covered | writer-based variant decodes into a buffer |
| `integration::round_trip::generated_canonical_fixed_point_document` | integration | positive | ## Cross-View Invariants + ## Serialization | covered | CVI 1: full document fixed point; reparse reproduces the tree |
| `integration::round_trip::generated_normalization_idempotence` | integration | positive | ## Cross-View Invariants | covered | CVI 2: serialize∘parse idempotent over six messy inputs; one pinned |
| `integration::round_trip::generated_handbuilt_serialize_reparse` | integration | positive | ## Cross-View Invariants + ## State Model | covered | CVI 5: hand-built tree → text → identical tree |
| `integration::round_trip::generated_reparse_equality_messy` | integration | positive | ## Cross-View Invariants | covered | render→reparse equality element-for-element on verified inputs |
| `integration::round_trip::generated_junk_fidelity` | integration | positive | ## Cross-View Invariants + ## Error Recovery and Junk | covered | CVI 3: slice range == junk content == embedded with-junk output |
| `integration::round_trip::generated_crlf_lf_equivalence` | integration | positive | ## Cross-View Invariants | covered | CVI 7: CRLF vs LF: same structure/flat text, identical LF output |
| `integration::round_trip::generated_literal_raw_roundtrip` | integration | positive | ## Cross-View Invariants + ## Unicode Unescaping | covered | CVI 6: raw literal serialize-verbatim and unescape-decode |
| `integration::modes::generated_modes_agree_commentfree` | integration | positive | ## Cross-View Invariants + ## Comments and Attachment | covered | CVI 4: equal resources on comment-free input |
| `integration::modes::generated_modes_agree_commentfree_errors` | integration | positive | ## Cross-View Invariants + ## Error Recovery and Junk | covered | CVI 4: equal error vectors and bodies on junk input |
| `integration::modes::generated_runtime_projection` | integration | positive | ## Comments and Attachment + ## Cross-View Invariants | covered | runtime body == full body minus comments with attach nulled |
| `integration::modes::generated_malformed_comment_asymmetry` | integration | positive | ## Comments and Attachment + ## Error Recovery and Junk | covered | same line: junk+error in full mode, silent skip in runtime |
| `integration::modes::generated_comment_attachment_roundtrip` | integration | positive | ## Comments and Attachment + ## Serialization | covered | attachment and standalone framing survive render→reparse |
| `integration::recovery::generated_multi_error_order` | integration | positive | ## Error Recovery and Junk | covered | two junk spans in input order with ascending slices; neighbors survive |
| `integration::recovery::generated_error_positions` | integration | positive | ## Error Recovery and Junk + ## Error Semantics | covered | exact pos/slice byte arithmetic for two failure shapes |
| `integration::recovery::generated_mid_entry_error_junks_whole` | integration | positive | ## Error Recovery and Junk + ## Select Expressions | covered | selector error junks the whole multi-line entry |
| `integration::recovery::generated_missing_field_recovery` | integration | positive | ## Error Recovery and Junk | covered | ExpectedMessageField pos spans the entry incl. blank line |
| `integration::recovery::generated_junk_reconstruction` | integration | positive | ## Error Recovery and Junk + ## Serialization | covered | err slices reconstruct junk; clean remainder serializes |
| `integration::grammar_compose::generated_nested_select_fixed_point` | integration | positive | ## Select Expressions + ## Serialization | covered | select nested in a default variant; canonical fixed point |
| `integration::grammar_compose::generated_dedent_placeable_select_combo` | integration | positive | ## Pattern Text: Lines, Indentation, Dedent + ## Serialization | covered | dedent with placeable and excess-indent line; AST + fixed point |
| `integration::grammar_compose::generated_attribute_select_multiline` | integration | positive | ## Resource Grammar and Entry Model + ## Select Expressions + ## Serialization | covered | select inside an attribute; canonical two-level indent |
| `integration::grammar_compose::generated_term_message_cross_references` | integration | positive | ## Placeables and Expressions + ## Serialization | covered | term/message/attribute references across entries; fixed point |
| `integration::grammar_compose::generated_call_args_in_selector` | integration | positive | ## Placeables and Expressions + ## Select Expressions | covered | function reference with args as selector; canonical text |
| `integration::grammar_compose::generated_document_kind_census` | integration | positive | ## Resource Grammar and Entry Model + ## Serialization | covered | all six entry kinds in one document; junk round trip; frame composition |
| `integration::grammar_compose::generated_owned_string_parse` | integration | positive | ## Public Interface + ## Serialization | covered | owned-String parse agrees with borrowed parse and serializes identically |
| `integration::grammar_compose::generated_empty_document_projections` | integration | positive | ## Resource Grammar and Entry Model + ## Serialization | covered | empty/blank inputs across parse, runtime, serialize |
| `integration::unicode_binding::generated_parse_unescape_pipeline` | integration | positive | ## Unicode Unescaping + ## Placeables and Expressions | covered | raw literals off the tree decode; borrow preserved when escape-free |
| `integration::unicode_binding::generated_parser_vs_unescaper_asymmetry` | integration | positive | ## Unicode Unescaping + ## Error Semantics | covered | \{ parser-legal but unescaper-unknown; \p rejected by parser |

Total: 98 | kept (covered): 98 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 98

Layer counts: atomic 71 / integration 27 / system_e2e 0.
Atomic positive share: 65/71 = 92% (floor 60%). no_check: 0.
depends_on annotation: 27/27 integration tests (oracle/depends_on.json).
