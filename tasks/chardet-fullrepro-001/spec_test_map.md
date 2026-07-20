# Specification-to-Test Map

- oracle_version: `2026-07-20-native-v1`
- source: retained upstream cases rewritten onto public entry points
- mapping: `source_nodeid_map.json`

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| `oracle/test_atomic.py::test_detect_binary_gif_signature` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_accuracy.py::test_detect[None-None/sample-1.gif]` |
| `oracle/test_atomic.py::test_detect_binary_jpeg_signature` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_accuracy.py::test_detect[None-None/sample-1.jpg]` |
| `oracle/test_atomic.py::test_detect_binary_mp4_signature` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_accuracy.py::test_detect[None-None/sample-1.mp4]` |
| `oracle/test_atomic.py::test_detect_binary_gif_with_all_encoding_eras` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_accuracy.py::test_detect_era_filtered[None-None/sample-1.gif]` |
| `oracle/test_atomic.py::test_detect_binary_jpeg_with_all_encoding_eras` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_accuracy.py::test_detect_era_filtered[None-None/sample-1.jpg]` |
| `oracle/test_atomic.py::test_detect_binary_mp4_with_all_encoding_eras` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_accuracy.py::test_detect_era_filtered[None-None/sample-1.mp4]` |
| `oracle/test_atomic.py::test_streaming_gif_matches_direct_detection` | atomic | Streaming Detection; Cross-View Invariants | covered | public rewrite of `tests/test_accuracy.py::test_detect_streaming_parity[None-None/sample-1.gif]` |
| `oracle/test_atomic.py::test_streaming_jpeg_matches_direct_detection` | atomic | Streaming Detection; Cross-View Invariants | covered | public rewrite of `tests/test_accuracy.py::test_detect_streaming_parity[None-None/sample-1.jpg]` |
| `oracle/test_atomic.py::test_streaming_mp4_matches_direct_detection` | atomic | Streaming Detection; Cross-View Invariants | covered | public rewrite of `tests/test_accuracy.py::test_detect_streaming_parity[None-None/sample-1.mp4]` |
| `oracle/test_atomic.py::test_detect_returns_four_field_dictionary` | atomic | Basic Detection | covered | public rewrite of `tests/test_api.py::test_detect_returns_dict` |
| `oracle/test_atomic.py::test_detect_ascii_returns_full_confidence` | atomic | Basic Detection | covered | public rewrite of `tests/test_api.py::test_detect_ascii` |
| `oracle/test_atomic.py::test_detect_utf8_bom_returns_compatibility_name` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_detect_utf8_bom` |
| `oracle/test_atomic.py::test_detect_utf8_multibyte_text` | atomic | Basic Detection | covered | public rewrite of `tests/test_api.py::test_detect_utf8_multibyte` |
| `oracle/test_atomic.py::test_detect_empty_uses_utf8_fallback` | atomic | Basic Detection | covered | public rewrite of `tests/test_api.py::test_detect_empty` |
| `oracle/test_atomic.py::test_detect_accepts_modern_web_encoding_era` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_detect_with_encoding_era` |
| `oracle/test_atomic.py::test_modern_web_era_excludes_legacy_greek_encoding` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_encoding_era_excludes_legacy` |
| `oracle/test_atomic.py::test_detect_respects_max_bytes` | atomic | Basic Detection | covered | public rewrite of `tests/test_api.py::test_detect_with_max_bytes` |
| `oracle/test_atomic.py::test_detect_all_returns_nonempty_list` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_detect_all_returns_list` |
| `oracle/test_atomic.py::test_detect_all_is_sorted_by_descending_confidence` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_detect_all_sorted_by_confidence` |
| `oracle/test_atomic.py::test_detect_all_returns_four_field_dictionaries` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_detect_all_each_is_dict` |
| `oracle/test_atomic.py::test_detect_all_top_matches_detect_for_ascii` | atomic | Encoding Options And Ranking; Cross-View Invariants | covered | public rewrite of `tests/test_api.py::test_detect_all_top_result_matches_detect[ascii]` |
| `oracle/test_atomic.py::test_detect_all_top_matches_detect_for_utf8` | atomic | Encoding Options And Ranking; Cross-View Invariants; Representative Workflow | covered | public rewrite of `tests/test_api.py::test_detect_all_top_result_matches_detect[utf8]` |
| `oracle/test_atomic.py::test_detect_all_top_matches_detect_for_bom` | atomic | BOM Handling; Cross-View Invariants | covered | public rewrite of `tests/test_api.py::test_detect_all_top_result_matches_detect[bom]` |
| `oracle/test_atomic.py::test_version_is_nonempty_and_starts_with_digit` | atomic | Basic Detection | covered | public rewrite of `tests/test_api.py::test_version_exists` |
| `oracle/test_atomic.py::test_legacy_rename_default_keeps_ascii_name` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_rename_legacy_default` |
| `oracle/test_atomic.py::test_legacy_rename_false_keeps_ascii_name` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_rename_legacy_false` |
| `oracle/test_atomic.py::test_legacy_rename_true_maps_ascii_to_windows_1252` | atomic | Encoding Options And Ranking; Error Semantics | covered | public rewrite of `tests/test_api.py::test_rename_legacy_true` |
| `oracle/test_atomic.py::test_legacy_rename_default_with_all_eras_keeps_ascii` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_rename_legacy_default_with_all_era` |
| `oracle/test_atomic.py::test_detect_all_legacy_rename_true_maps_ascii` | atomic | Encoding Options And Ranking; Error Semantics | covered | public rewrite of `tests/test_api.py::test_rename_legacy_detect_all` |
| `oracle/test_atomic.py::test_detect_all_legacy_rename_false_keeps_ascii` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_rename_legacy_detect_all_false` |
| `oracle/test_atomic.py::test_streaming_legacy_rename_true_maps_ascii` | atomic | Streaming Detection; Error Semantics | covered | public rewrite of `tests/test_api.py::test_rename_legacy_detector` |
| `oracle/test_atomic.py::test_streaming_legacy_rename_false_keeps_ascii` | atomic | Streaming Detection | covered | public rewrite of `tests/test_api.py::test_rename_legacy_detector_false` |
| `oracle/test_atomic.py::test_compatibility_name_maps_euc_jis_to_euc_jp` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_compat_names_eucjp` |
| `oracle/test_atomic.py::test_detect_all_default_filters_low_confidence_results` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_ignore_threshold_false_filters` |
| `oracle/test_atomic.py::test_detect_all_ignore_threshold_returns_candidates` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_ignore_threshold_true_returns_all` |
| `oracle/test_atomic.py::test_detect_all_threshold_falls_back_when_everything_is_low` | atomic | Encoding Options And Ranking | covered | public rewrite of `tests/test_api.py::test_ignore_threshold_fallback` |
| `oracle/test_atomic.py::test_non_all_language_filter_emits_deprecation_warning` | atomic | Encoding Options And Ranking; Error Semantics | covered | public rewrite of `tests/test_api.py::test_lang_filter_warning` |
| `oracle/test_atomic.py::test_all_language_filter_emits_no_deprecation_warning` | atomic | Encoding Options And Ranking; Error Semantics | covered | public rewrite of `tests/test_api.py::test_lang_filter_all_no_warning` |
| `oracle/test_atomic.py::test_detect_rejects_boolean_max_bytes` | atomic | Basic Detection; Error Semantics | covered | public rewrite of `tests/test_api.py::test_detect_max_bytes_bool_raises` |
| `oracle/test_atomic.py::test_public_detection_identifies_plain_ascii` | atomic | Basic Detection | covered | public rewrite of `tests/test_ascii.py::test_pure_ascii` |
| `oracle/test_atomic.py::test_public_detection_identifies_ascii_whitespace` | atomic | Basic Detection | covered | public rewrite of `tests/test_ascii.py::test_ascii_with_common_whitespace` |
| `oracle/test_atomic.py::test_public_detection_does_not_label_high_byte_as_ascii` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_ascii.py::test_high_byte_not_ascii` |
| `oracle/test_atomic.py::test_public_detection_does_not_label_utf8_multibyte_as_ascii` | atomic | Basic Detection | covered | public rewrite of `tests/test_ascii.py::test_utf8_multibyte_not_ascii` |
| `oracle/test_atomic.py::test_public_detection_empty_input_is_not_ascii` | atomic | Basic Detection | covered | public rewrite of `tests/test_ascii.py::test_empty_input` |
| `oracle/test_atomic.py::test_public_detection_identifies_single_ascii_byte` | atomic | Basic Detection | covered | public rewrite of `tests/test_ascii.py::test_single_ascii_byte` |
| `oracle/test_atomic.py::test_public_detection_identifies_all_printable_ascii` | atomic | Basic Detection | covered | public rewrite of `tests/test_ascii.py::test_all_printable_ascii` |
| `oracle/test_atomic.py::test_public_detection_does_not_label_dense_nulls_as_ascii` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_ascii.py::test_null_byte_not_ascii` |
| `oracle/test_atomic.py::test_public_detection_identifies_null_separated_paths` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_ascii.py::test_ascii_with_null_separated_paths` |
| `oracle/test_atomic.py::test_public_detection_accepts_ascii_at_five_percent_null_boundary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_ascii.py::test_ascii_with_null_at_boundary` |
| `oracle/test_atomic.py::test_public_detection_rejects_ascii_above_null_boundary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_ascii.py::test_ascii_with_null_just_above_boundary` |
| `oracle/test_atomic.py::test_public_detection_rejects_ascii_with_high_null_fraction` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_ascii.py::test_ascii_with_high_null_fraction` |
| `oracle/test_atomic.py::test_public_detection_rejects_ascii_with_null_and_high_byte` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_ascii.py::test_ascii_with_nulls_and_high_bytes` |
| `oracle/test_atomic.py::test_public_detection_pure_ascii_retains_full_confidence` | atomic | Basic Detection | covered | public rewrite of `tests/test_ascii.py::test_pure_ascii_still_confidence_1` |
| `oracle/test_atomic.py::test_empty_input_is_text_not_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_empty_input_is_not_binary` |
| `oracle/test_atomic.py::test_plain_ascii_is_text_not_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_plain_ascii_is_not_binary` |
| `oracle/test_atomic.py::test_newlines_and_tabs_are_text_not_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_text_with_newlines_tabs_is_not_binary` |
| `oracle/test_atomic.py::test_all_null_bytes_are_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_all_null_bytes_is_binary` |
| `oracle/test_atomic.py::test_high_null_concentration_is_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_high_null_concentration_is_binary` |
| `oracle/test_atomic.py::test_single_null_in_large_text_is_not_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_single_null_in_large_text_is_not_binary` |
| `oracle/test_atomic.py::test_control_characters_indicate_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_control_characters_indicate_binary` |
| `oracle/test_atomic.py::test_few_control_characters_in_large_text_are_not_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_few_control_chars_in_large_text_is_not_binary` |
| `oracle/test_atomic.py::test_jpeg_magic_is_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_jpeg_header_is_binary` |
| `oracle/test_atomic.py::test_utf8_text_is_not_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_utf8_text_is_not_binary` |
| `oracle/test_atomic.py::test_max_bytes_ignores_binary_tail` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_max_bytes_respected` |
| `oracle/test_atomic.py::test_exactly_one_percent_control_bytes_is_not_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_exactly_at_threshold_is_not_binary` |
| `oracle/test_atomic.py::test_above_one_percent_control_bytes_is_binary` | atomic | ASCII And Binary Boundaries | covered | public rewrite of `tests/test_binary.py::test_just_above_threshold_is_binary` |
| `oracle/test_atomic.py::test_utf8_bom_precedes_statistical_detection` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf8_bom` |
| `oracle/test_atomic.py::test_utf16_little_endian_bom` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf16_le_bom` |
| `oracle/test_atomic.py::test_utf16_big_endian_bom` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf16_be_bom` |
| `oracle/test_atomic.py::test_utf32_little_endian_bom` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf32_le_bom` |
| `oracle/test_atomic.py::test_utf32_big_endian_bom` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf32_be_bom` |
| `oracle/test_atomic.py::test_plain_text_has_no_bom_result` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_no_bom` |
| `oracle/test_atomic.py::test_empty_input_has_no_bom_result` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_empty_input` |
| `oracle/test_atomic.py::test_partial_utf8_bom_is_not_treated_as_bom` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_too_short_for_bom` |
| `oracle/test_atomic.py::test_utf32_little_endian_is_checked_before_utf16` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf32_le_checked_before_utf16_le` |
| `oracle/test_atomic.py::test_bare_utf32_little_endian_bom_is_valid` | atomic | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf32_le_bom_only` |
| `oracle/test_atomic.py::test_ebcdic_text_is_not_misdetected_as_gb18030` | atomic | CJK Candidate Gating | covered | public rewrite of `tests/test_cjk_gating.py::test_ebcdic_not_detected_as_gb18030` |
| `oracle/test_atomic.py::test_latin_text_is_not_misdetected_as_cp932` | atomic | CJK Candidate Gating | covered | public rewrite of `tests/test_cjk_gating.py::test_latin_text_not_detected_as_cp932` |
| `oracle/test_atomic.py::test_real_japanese_remains_a_cjk_candidate` | atomic | CJK Candidate Gating | covered | public rewrite of `tests/test_cjk_gating.py::test_real_cjk_still_detected` |
| `oracle/test_atomic.py::test_real_chinese_remains_a_cjk_candidate` | atomic | CJK Candidate Gating | covered | public rewrite of `tests/test_cjk_gating.py::test_real_chinese_still_detected` |
| `oracle/test_atomic.py::test_real_korean_remains_a_cjk_candidate` | atomic | CJK Candidate Gating | covered | public rewrite of `tests/test_cjk_gating.py::test_real_korean_still_detected` |
| `oracle/test_atomic.py::test_german_macroman_is_not_misdetected_as_cjk` | atomic | CJK Candidate Gating | covered | public rewrite of `tests/test_cjk_gating.py::test_german_macroman_not_detected_as_cjk` |
| `oracle/test_integration.py::test_sparse_null_separators_remain_ascii_text` | integration | ASCII And Binary Boundaries; Cross-View Invariants | covered | public rewrite of `tests/test_ascii.py::test_ascii_with_sparse_null_separators` |
| `oracle/test_integration.py::test_misaligned_utf32_little_endian_falls_back_to_utf16` | integration | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf32_le_bom_falls_through_to_utf16_when_payload_not_aligned` |
| `oracle/test_integration.py::test_misaligned_utf32_big_endian_falls_through_to_binary` | integration | BOM Handling | covered | public rewrite of `tests/test_bom.py::test_utf32_be_bom_falls_through_when_payload_not_aligned` |
| `oracle/test_integration.py::test_cli_detects_ascii_file` | system_e2e | Command Line; Cross-View Invariants | covered | public rewrite of `tests/test_cli.py::test_cli_detects_file` |
| `oracle/test_integration.py::test_cli_detects_utf8_file` | system_e2e | Command Line; Cross-View Invariants; Representative Workflow | covered | public rewrite of `tests/test_cli.py::test_cli_detects_utf8_file` |
| `oracle/test_integration.py::test_cli_reads_standard_input` | system_e2e | Command Line; Representative Workflow | covered | public rewrite of `tests/test_cli.py::test_cli_stdin` |
| `oracle/test_integration.py::test_cli_version_has_numeric_version` | system_e2e | Command Line | covered | public rewrite of `tests/test_cli.py::test_cli_version` |
| `oracle/test_integration.py::test_cli_minimal_outputs_only_encoding` | system_e2e | Command Line | covered | public rewrite of `tests/test_cli.py::test_cli_minimal_flag` |

Total: 90 | kept: 90 | spec_gap: 0 | source-only: 0 | excluded: 9163 | final_scoreable: 90
