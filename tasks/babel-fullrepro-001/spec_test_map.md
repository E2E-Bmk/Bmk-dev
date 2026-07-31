# Spec Test Map — babel-fullrepro-001

oracle_version: 2026-07-31-stage3-mixed-v4-commandfix
oracle_source: upstream_plus_generated
oracle_files: test_atomic.py, test_integration.py
runtime_requirements: requirements.txt
scorer_isolation: --remove-path babel --pytest-arg=--rootdir=.
track_a_upstream_kept: 20
track_b_generated_kept: 71
depends_on_annotation_coverage: 37/37 integration+system_e2e tests
scope_plan: target_subdomain=message catalog lifecycle; expected_oracle_max=95; actual_oracle=91

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| test_atomic.py::test_message_percent_format_flag_is_added | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_message_brace_format_flag_is_added | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_message_non_format_flags_are_absent | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_plural_message_gets_empty_plural_translation_tuple | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_message_clone_is_independent_copy | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_message_is_identical_rejects_non_message | generated | atomic | failure_path | Error Semantics | covered | generated public test |
| test_atomic.py::test_message_check_returns_translation_errors_for_bad_plural | generated | atomic | failure_path | Error Semantics | covered | generated public test |
| test_atomic.py::test_setup_message_extractors_validation_rejects_non_mapping | generated | atomic | failure_path | Command and Setup Workflows | covered | generated public setup-workflow test |
| test_atomic.py::test_catalog_accepts_domain_and_metadata_without_locale | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_catalog_rejects_invalid_locale_type | generated | atomic | failure_path | Error Semantics | covered | generated public test |
| test_atomic.py::test_catalog_add_returns_and_stores_message | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_catalog_delete_missing_id_is_noop | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_catalog_context_keys_are_distinct | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_catalog_iteration_starts_with_header_message | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_catalog_assignment_merges_message_metadata_without_duplicates | generated | atomic | positive | State Model | covered | generated public test |
| test_atomic.py::test_catalog_empty_message_updates_header_state | generated | atomic | positive | State Model | covered | generated public test |
| test_atomic.py::test_catalog_plural_forms_follow_locale | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_catalog_mime_headers_include_default_plural_free_metadata | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_integration.py::test_catalog_update_preserves_existing_translation | generated | integration | positive | State Model | covered | generated public test |
| test_integration.py::test_catalog_update_moves_removed_message_to_obsolete | generated | integration | positive | State Model | covered | generated public test |
| test_integration.py::test_catalog_update_fuzzy_matches_changed_id | generated | integration | positive | Cross-View Invariants | covered | generated public test |
| test_integration.py::test_catalog_update_can_disable_fuzzy_matching | generated | integration | positive | State Model | covered | generated public test |
| test_integration.py::test_catalog_update_can_copy_template_header_comment | generated | integration | positive | State Model | covered | generated public test |
| test_atomic.py::test_catalog_is_identical_requires_catalog | generated | atomic | failure_path | Error Semantics | covered | generated public test |
| test_atomic.py::test_escape_and_unescape_po_string_round_trip | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_normalize_and_denormalize_multiline_text | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_atomic.py::test_normalize_width_zero_disables_wrapping | generated | atomic | positive | Catalog State and Message Objects | covered | generated public test |
| test_integration.py::test_write_po_omits_header_when_requested | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_write_po_suppresses_locations_when_requested | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_write_po_can_omit_line_numbers | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_write_po_includes_previous_ids_when_requested | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_generate_po_emits_string_fragments | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_read_po_reads_comments_flags_locations_and_plural | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_read_po_reads_context_as_lookup_key | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_read_po_obsolete_messages_can_be_kept_or_ignored | generated | integration | positive | State Model | covered | generated public test |
| test_integration.py::test_read_po_invalid_input_can_abort | generated | integration | failure_path | Error Semantics | covered | generated public test |
| test_integration.py::test_read_po_header_updates_catalog_metadata | generated | integration | positive | State Model | covered | generated public test |
| test_integration.py::test_po_round_trip_preserves_message_context_and_flags | generated | integration | positive | Cross-View Invariants | covered | generated public test |
| test_integration.py::test_mo_round_trip_preserves_singular_message | generated | integration | positive | Cross-View Invariants | covered | generated public test |
| test_integration.py::test_mo_round_trip_preserves_plural_message | generated | integration | positive | Cross-View Invariants | covered | generated public test |
| test_integration.py::test_mo_round_trip_preserves_context_message | generated | integration | positive | Cross-View Invariants | covered | generated public test |
| test_integration.py::test_mo_omits_fuzzy_messages_by_default | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_mo_includes_fuzzy_messages_when_requested | generated | integration | positive | PO and MO File Interchange | covered | generated public test |
| test_integration.py::test_mo_invalid_bytes_raise_parsing_exception | generated | integration | failure_path | Error Semantics | covered | generated public test |
| test_atomic.py::test_extract_unknown_method_raises_value_error | generated | atomic | failure_path | Error Semantics | covered | generated public test |
| test_atomic.py::test_extract_callable_method_is_used | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_python_finds_gettext_call | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_python_combines_adjacent_string_literals | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_python_handles_plural_keyword_spec | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_python_handles_context_keyword_spec | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_python_collects_translator_comments | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_strips_comment_tags_when_requested | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_python_respects_source_encoding_comment | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_javascript_finds_gettext_call | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_javascript_collects_line_comment | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_javascript_template_string_tag | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_extract_javascript_block_comment_is_returned | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_integration.py::test_extract_from_file_uses_named_method | generated | system_e2e | positive | Cross-View Invariants | covered | generated public test |
| test_integration.py::test_extract_from_dir_returns_relative_filenames | generated | system_e2e | positive | Cross-View Invariants | covered | generated public test |
| test_integration.py::test_extract_from_dir_callback_receives_file_method_and_options | generated | system_e2e | positive | Message Extraction and Mapping | covered | generated public test |
| test_integration.py::test_extract_from_dir_directory_filter_blocks_subtree | generated | system_e2e | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_default_directory_filter_skips_hidden_directory | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_parse_mapping_cfg_returns_methods_and_options | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_parse_mapping_deprecated_alias_matches_cfg | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_parse_keywords_handles_context_plural_and_arity | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_parse_mapping_cfg_rejects_malformed_ini | generated | atomic | failure_path | Error Semantics | covered | generated public test |
| test_atomic.py::test_listify_value_splits_strings | generated | atomic | positive | Message Extraction and Mapping | covered | generated public test |
| test_atomic.py::test_public_extraction_constants_are_available | generated | atomic | positive | Import Surface | covered | generated public test |
| test_integration.py::test_cli_help_lists_core_commands | generated | system_e2e | positive | CLI Entry Points | covered | generated public test |
| test_integration.py::test_cli_extract_requires_output_file | generated | system_e2e | failure_path | Command and Setup Workflows | covered | generated public test |
| test_integration.py::test_cli_extract_writes_pot_file | generated | system_e2e | positive | Command and Setup Workflows | covered | generated public test |
| test_atomic.py::test_public_constants_have_expected_roles | generated | atomic | positive | API Catalog | covered | generated public test |
| test_atomic.py::test_upstream_message_python_format_patterns | upstream | atomic | positive | Catalog State and Message Objects | covered | rewritten upstream |
| test_atomic.py::test_upstream_message_translator_comments_are_stored | upstream | atomic | positive | Catalog State and Message Objects | covered | rewritten upstream |
| test_atomic.py::test_upstream_message_clone_does_not_share_mutable_state | upstream | atomic | positive | Catalog State and Message Objects | covered | rewritten upstream |
| test_atomic.py::test_upstream_catalog_add_returns_message_instance | upstream | atomic | positive | Catalog State and Message Objects | covered | rewritten upstream |
| test_atomic.py::test_upstream_catalog_two_messages_with_same_singular_merge | upstream | atomic | positive | Catalog State and Message Objects | covered | rewritten upstream |
| test_atomic.py::test_upstream_catalog_deduplicates_comments_and_locations | upstream | atomic | positive | Catalog State and Message Objects | covered | rewritten upstream |
| test_integration.py::test_upstream_catalog_update_message_changed_to_plural | upstream | integration | positive | Cross-View Invariants | covered | rewritten upstream |
| test_integration.py::test_upstream_catalog_update_without_fuzzy_matching_obsoletes_old | upstream | integration | positive | State Model | covered | rewritten upstream |
| test_integration.py::test_upstream_catalog_update_no_template_mutation | upstream | integration | positive | State Model | covered | rewritten upstream |
| test_atomic.py::test_upstream_catalog_setitem_merges_locations | upstream | atomic | positive | Catalog State and Message Objects | covered | rewritten upstream |
| test_atomic.py::test_upstream_extract_invalid_method_raises | upstream | atomic | failure_path | Error Semantics | covered | rewritten upstream |
| test_atomic.py::test_upstream_extract_allows_callable_method | upstream | atomic | positive | Message Extraction and Mapping | covered | rewritten upstream |
| test_integration.py::test_upstream_extract_different_signatures_filter_invalid_calls | upstream | integration | failure_path | Message Extraction and Mapping | covered | rewritten upstream |
| test_atomic.py::test_upstream_extract_future_unicode_literal | upstream | atomic | positive | Message Extraction and Mapping | covered | rewritten upstream |
| test_atomic.py::test_upstream_extract_python_default_encoding_utf8 | upstream | atomic | positive | Message Extraction and Mapping | covered | rewritten upstream |
| test_atomic.py::test_upstream_extract_python_multiline_plural_call | upstream | atomic | positive | Message Extraction and Mapping | covered | rewritten upstream |
| test_integration.py::test_upstream_pofile_join_locations | upstream | integration | positive | PO and MO File Interchange | covered | rewritten upstream |
| test_integration.py::test_upstream_pofile_duplicate_auto_comments_written_once | upstream | integration | positive | PO and MO File Interchange | covered | rewritten upstream |
| test_integration.py::test_upstream_pofile_obsolete_message_can_be_ignored | upstream | integration | positive | PO and MO File Interchange | covered | rewritten upstream |
| test_integration.py::test_upstream_pofile_previous_msgid_is_included_when_requested | upstream | integration | positive | PO and MO File Interchange | covered | rewritten upstream |
| tests/benchmarks/benchmark_core.py::test_locale_parse_language | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_locale_parse_full_tag | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_locale_parse_with_variant | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_locale_parse_likely_subtags | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_locale_construct | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_negotiate_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_parse_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_get_locale_identifier | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_get_global | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_core.py::test_locale_get_display_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_date_standalone_month | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_locale_deep_data_read | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_datetime_medium | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_time_with_tzinfo | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_timedelta_long | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_timedelta_short_hours | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_skeleton | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_skeleton_fuzzy | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_format_interval_same_day | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_parse_pattern_cached | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_parse_pattern_uncached | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_parse_date_short | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_dates.py::test_get_timezone_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_languages.py::test_get_official_languages | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_languages.py::test_get_official_languages_regional | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_languages.py::test_get_territory_language_info | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_lists.py::test_format_list_two | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_lists.py::test_format_list_five | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_lists.py::test_format_list_or | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_lists.py::test_format_list_style_fallback | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_catalog_add | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_catalog_iter | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_catalog_get | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_read_po | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_write_po | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_write_mo | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_read_mo | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_extract_python | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_messages.py::test_extract_method_python | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_format_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_format_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_format_currency_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_format_compact_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_format_compact_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_format_percent | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_format_scientific | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_parse_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_get_currency_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_numbers.py::test_get_territory_currencies | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_plural.py::test_plural_rule_parse | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_plural.py::test_plural_rule_call_int | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_plural.py::test_plural_rule_call_float | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_plural.py::test_locale_plural_form | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_plural.py::test_to_gettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_support.py::test_format_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_support.py::test_format_date | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_support.py::test_lazy_proxy | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_support.py::test_translations_gettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_support.py::test_translations_ngettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_units.py::test_format_unit_long | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_units.py::test_format_unit_short | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_units.py::test_format_unit_length_fallback | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_units.py::test_format_compound_unit_predefined | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_units.py::test_format_compound_unit_constructed | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/benchmarks/benchmark_units.py::test_get_unit_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/interop/test_jinja2_interop.py::test_jinja2_interop | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/messages/frontend/test_cli.py::test_usage | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_list_locales | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_no_duplicated_output_for_multiple_runs | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_frontend_can_log_to_predefined_handler | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_help | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_extract_with_default_mapping | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_extract_with_mapping_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_extract_with_exact_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_init_with_output_dir | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_init_singular_plural_forms | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_init_more_than_2_plural_forms | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_compile_catalog | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_compile_fuzzy_catalog | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_compile_catalog_with_more_than_2_plural_forms | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_compile_catalog_multidomain | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_update | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_update_pot_creation_date | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_check | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_check_pot_creation_date | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_update_init_missing | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_cli.py::test_update_init_missing_creates_dest_dir | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_compile.py::test_no_directory_or_output_file_specified | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_compile.py::test_no_directory_or_input_file_specified | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_neither_default_nor_custom_keywords | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_no_output_file_specified | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_both_sort_output_and_sort_by_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_invalid_file_or_dir_input_path | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_input_paths_is_treated_as_list | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_input_paths_handle_spaces_after_comma | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_input_dirs_is_alias_for_input_paths | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_input_dirs_is_mutually_exclusive_with_input_paths | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_extraction_with_default_mapping | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_extraction_with_mapping_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_extraction_with_mapping_dict | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_extraction_add_location_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_extraction_with_mapping_file_with_keywords | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_extract.py::test_extraction_with_mapping_file_with_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_parse_mapping | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_parse_keywords | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_parse_keywords_with_t | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_messages_with_t | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_keyword_args_384 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_update_catalog_boolean_args | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_compile_catalog_dir | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_compile_catalog_explicit | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_update_dir | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_cli_knows_dash_s | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_cli_knows_dash_dash_last_dash_translator | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_add_location | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_error_code | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_ignore_dirs | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_extract_header_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_frontend.py::test_pr_1121 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_no_input_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_no_locale | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_with_output_dir | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_keeps_catalog_non_fuzzy | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_correct_init_more_than_2_plurals | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_correct_init_singular_plural_forms | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_supports_no_wrap | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/frontend/test_init.py::test_supports_width | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_message_python_brace_format | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_duplicate_user_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_duplicate_location | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_message_changed_to_simple | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_message_updates_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_fuzzy_matching_with_case_change | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_fuzzy_matching_with_char_change | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_fuzzy_matching_no_msgstr | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_fuzzy_matching_with_new_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_fuzzy_matching_with_changed_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_fuzzy_matching_no_cascading | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_fuzzy_matching_long_string | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_fuzzy_matching_regarding_plurals | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_po_updates_pot_creation_date | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_po_ignores_pot_creation_date | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update_po_keeps_po_revision_date | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_stores_datetime_correctly | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_mime_headers_contain_same_information_as_attributes | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_message_fuzzy | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_message_pluralizable | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_message_python_format_2 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_message_python_brace_format_2 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_mime_headers | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_mime_headers_set_locale | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_mime_headers_type_coercion | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_num_plurals | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_plural_expr | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_plural_forms | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_add | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_update | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_datetime_parsing | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_update_catalog_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_catalog.py::test_catalog_tz_pickleable | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_1_num_plurals_checkers | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_2_num_plurals_checkers | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_3_num_plurals_checkers | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_4_num_plurals_checkers | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_5_num_plurals_checkers | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_6_num_plurals_checkers | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_python_format_invalid | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test_python_format_valid | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test__validate_format_invalid | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_checkers.py::test__validate_format_valid | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract.py::test_invalid_filter | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract.py::test_empty_string_msgid | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract.py::test_warn_if_empty_string_msgid_found_in_context_aware_extraction_method | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract.py::test_f_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract.py::test_f_strings_non_utf8 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract.py::test_issue_1195 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract.py::test_issue_1195_2 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_nested_calls | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_extract_default_encoding_ascii | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_nested_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_comments_with_calls_that_spawn_multiple_lines | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_declarations | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_dpgettext | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_npgettext | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_dnpgettext | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_triple_quoted_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_multiline_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_concatenated_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_unicode_string_arg | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_comment_tag | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_comment_tag_multiline | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_translator_comments_with_previous_non_translator_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_comment_tags_not_on_start_of_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_multiple_comment_tags | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_two_succeeding_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_invalid_translator_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_invalid_translator_comments2 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_invalid_translator_comments3 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_comment_tag_with_leading_space | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_different_signatures | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_utf8_message | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_utf8_message_with_magic_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_utf8_message_with_utf8_bom | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_utf8_message_with_utf8_bom_and_magic_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_utf8_bom_with_latin_magic_comment_fails | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_utf8_raw_strings_match_unicode_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_extract_strip_comment_tags | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_extract_python.py::test_nested_messages | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_simple_extract | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_various_calls | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_message_with_line_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_message_with_multiline_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_ignore_function_definitions | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_misplaced_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_jsx_extraction | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_dotted_keyword_extract | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_template_string_standard_usage | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_template_string_tag_usage | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_inside_template_string | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_inside_template_string_with_linebreaks | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_js_extract.py::test_inside_nested_template_string | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_jslexer.py::test_unquote | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_jslexer.py::test_dollar_in_identifier | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_jslexer.py::test_dotted_name | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_jslexer.py::test_dotted_name_end | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_jslexer.py::test_template_string | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_jslexer.py::test_jsx | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_mofile.py::test_basics | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_mofile.py::test_sorting | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_mofile.py::test_more_plural_forms | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_mofile.py::test_empty_translation_with_fallback | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_mofile.py::test_read_mo_decodes_message_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_plurals.py::test_get_plural_selection | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_plurals.py::test_get_plural_accepts_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_plurals.py::test_get_plural_falls_back_to_default | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_plurals.py::test_get_plural | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_enclosed_filenames_in_location_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_unescape | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_unescape_of_quoted_newline | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_denormalize_on_msgstr_without_empty_first_line | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_extract_locations_valid_location_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_extract_locations_invalid_location_comment | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_enclose_filename_if_necessary_no_change | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_enclose_filename_if_necessary_enclosed | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_unknown_language_roundtrip | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_unknown_language_write | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_iterable_of_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_iterable_of_mismatching_strings | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_issue_1087 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile.py::test_issue_1134 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_preserve_locale | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_locale_gets_overridden_by_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_preserve_domain | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_applies_specified_encoding_during_read | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_encoding_header_read | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_plural_forms_header_parsed | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_read_multiline | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_fuzzy_header | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_not_fuzzy_header | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_header_entry | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_obsolete_message | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_obsolete_message_ignored | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_multi_line_obsolete_message | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_unit_following_multi_line_obsolete_message | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_unit_before_obsolete_is_not_obsoleted | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_with_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_obsolete_message_with_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_obsolete_messages_with_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_obsolete_messages_roundtrip | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_multiline_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_with_context_two | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_singular_plural_form | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_more_than_two_plural_forms | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_plural_with_square_brackets | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_obsolete_plural_with_square_brackets | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_missing_plural | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_missing_plural_in_the_middle | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_with_location | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_abort_invalid_po_file | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_read.py::test_invalid_pofile_with_abort_flag | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_write_po_file_with_specified_charset | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_wrap_long_lines | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_wrap_long_lines_with_long_word | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_wrap_long_lines_in_header | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_wrap_locations_with_hyphens | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_no_wrap_and_width_behaviour_on_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_pot_with_translator_comments | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_po_with_obsolete_message | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_po_with_multiline_obsolete_message | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_po_with_previous_msgid_plural | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_sorted_po | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_sorted_po_context | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_file_sorted_po | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_file_with_no_lineno | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_silent_location_fallback | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_include_lineno | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_no_include_lineno | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_white_space_in_location | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_white_space_in_location_already_enclosed | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_tab_in_location | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_tab_in_location_already_enclosed | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_pofile_write.py::test_wrap_with_enclosed_file_locations | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_setuptools_frontend.py::test_extract_distutils_keyword_arg_388 | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_setuptools_frontend.py::test_setuptools_commands | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_toml_config.py::test_toml_mapping_multiple_patterns | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_toml_config.py::test_toml_mapping_keywords_parsing | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_toml_config.py::test_toml_mapping_add_comments_parsing | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/messages/test_toml_config.py::test_bad_toml_test_case | upstream | - | - | - | excluded | not rewritten after per-function audit: helper fixture, exact output/prose, private helper, locale-data dependency, or behavior superseded by generated public oracle |
| tests/test_core.py::test_locale_provides_access_to_cldr_locale_data | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_locale_repr | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_locale_comparison | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_can_return_default_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_ignore_invalid_locales_in_lc_ctype | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_zone_aliases_and_territories | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_hash | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_attributes | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_default | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_negotiate | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_negotiate_custom_separator | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_parse | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_parse_likely_subtags | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_get_display_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_display_name_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_english_name_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_languages_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_scripts_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_territories_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_variants_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_currencies_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_currency_symbols_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_number_symbols_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_other_numbering_systems_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_default_numbering_systems_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_all_locales_have_default_numbering_system | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_decimal_formats | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_currency_formats_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_percent_formats_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_scientific_formats_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_periods_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_days_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_months_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_quarters_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_eras_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_time_zones_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_meta_zones_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_zone_formats_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_first_week_day_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_weekend_start_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_weekend_end_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_min_week_days_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_date_formats_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_time_formats_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_datetime_formats_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_datetime_skeleton_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::TestLocaleClass::test_plural_form_property | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_default_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_default_locale_multiple_args | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_default_locale_bad_arg | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_negotiate_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_parse_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_compatible_classes_in_global_and_localedata | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_issue_601_no_language_name_but_has_variant | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_issue_814 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_issue_1112 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_language_alt_official_not_used | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_locale_parse_empty | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_core.py::test_get_cldr_version | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_same_instant_1 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_same_instant_2 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_same_instant_3 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_same_instant_4 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_no_difference | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_in_tz | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_12_hour | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_format_interval_invalid_skeleton | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_date_intervals.py::test_issue_825 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_quarter_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_month_context | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_abbreviated_month_alias | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_week_of_year_first | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_week_of_year_first_with_year | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_week_of_year_last | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_week_of_year_last_us_extra_week | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_week_of_year_de_first_us_last_with_year | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_week_of_month_first | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_week_of_month_last | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_day_of_year | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_day_of_year_works_with_datetime | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_day_of_year_first | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_day_of_year_last | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_day_of_week_in_month | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_day_of_week_in_month_first | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_day_of_week_in_month_last | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_local_day_of_week | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_local_day_of_week_standalone | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_pattern_day_of_week | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_fractional_seconds | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_fractional_seconds_zero | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_milliseconds_in_day | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_milliseconds_in_day_zero | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_timezone_rfc822 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_timezone_gmt | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_timezone_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_timezone_location_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_timezone_walltime_short | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_timezone_walltime_long | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::DateTimeFormatTestCase::test_hour_formatting | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatDateTestCase::test_with_time_fields_in_pattern | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatDateTestCase::test_with_time_fields_in_pattern_and_datetime_param | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatDateTestCase::test_with_day_of_year_in_pattern_and_datetime_param | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatDatetimeTestCase::test_with_float | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatDatetimeTestCase::test_timezone_formats_los_angeles | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatDatetimeTestCase::test_timezone_formats_utc | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatDatetimeTestCase::test_timezone_formats_kolkata | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimeTestCase::test_with_naive_datetime_and_tzinfo | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimeTestCase::test_with_float | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimeTestCase::test_with_date_fields_in_pattern | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimeTestCase::test_with_date_fields_in_pattern_and_datetime_param | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimedeltaTestCase::test_zero_seconds | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimedeltaTestCase::test_small_value_with_granularity | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimedeltaTestCase::test_direction_adding | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimedeltaTestCase::test_format_narrow | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::FormatTimedeltaTestCase::test_format_invalid | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::TimeZoneAdjustTestCase::test_can_format_time_with_custom_timezone | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_period_names | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_day_names | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_month_names | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_quarter_names | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_era_names | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_date_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_datetime_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_time_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_timezone_gmt | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_timezone_location | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_timezone_name_tzinfo | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_timezone_name_time_pytz | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_get_timezone_name_misc | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_format_date | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_format_datetime | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_format_time | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_format_skeleton | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_match_skeleton_alternate_characters | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_format_timedelta | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_date | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_date_custom_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_time | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_time_no_seconds_in_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_time_alternate_characters | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_date_alternate_characters | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_time_custom_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_errors | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_datetime_format_get_week_number | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_parse_pattern | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_lithuanian_long_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_zh_TW_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_format_current_moment | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_no_inherit_metazone_marker_never_in_output | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_no_inherit_metazone_formatting | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_russian_week_numbering | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_week_numbering_isocalendar | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_week_numbering_monday_mindays_4 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_week_numbering_monday_mindays_1 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_week_numbering_sunday_mindays_1 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_week_numbering_sunday_mindays_4 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_week_numbering_friday_mindays_1 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_week_numbering_saturday_mindays_1 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_en_gb_first_weekday | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_issue_798 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_issue_892 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_issue_1089 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_issue_1162 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_issue_1192 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_dates.py::test_issue_1192_fmt | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_day_periods.py::test_day_period_rules | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_languages.py::test_official_languages | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_languages.py::test_get_language_info | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_lists.py::test_format_list | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_lists.py::test_format_list_error | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_lists.py::test_issue_1098 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_lists.py::test_lists_default_locale_deprecation | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_merge_items | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_merge_nested_dict | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_merge_nested_dict_no_overlap | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_merge_with_alias_and_resolve | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_load | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_no_cross_locale_contamination | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_manual_locale_data_writes | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_load_inheritance | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_merge | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_locale_identification | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_unique_ids | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_mixedcased_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_locale_argument_acceptance | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_locale_identifiers_cache | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_locale_name_cleanup | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localedata.py::test_reserved_locale_names | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localtime.py::test_issue_1092_without_pytz | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localtime.py::test_issue_1092_with_pytz | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_localtime.py::test_issue_990 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_list_currencies | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_validate_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_is_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_normalize_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_currency_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_currency_symbol | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_currency_precision | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_currency_unit_pattern | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_territory_currencies | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_decimal_symbol | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_plus_sign_symbol | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_minus_sign_symbol | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_exponential_symbol | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_group_symbol | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_get_infinity_symbol | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_decimal_precision | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_decimal_precision | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_decimal_quantization | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_format_type | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_compact_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_compact_currency_invalid_format_type | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_precision | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_quantization | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_long_display_name | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_long_display_name_all | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_long_display_name_custom_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_percent | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_percent_precision | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_percent_quantization | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_scientific | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_default_scientific_format | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_scientific_precision | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_scientific_quantization | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_number | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_number_group_separator_can_be_any_space | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_decimal_group_separator_can_be_any_space | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_grouping | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_pattern | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_pattern_negative | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_numberpattern_repr | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_static_pattern | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_parse_decimal_nbsp_heuristics | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_very_small_decimal_no_quantization | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_single_quotes_in_pattern | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_with_none_locale_with_default | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_currency_with_none_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_decimal_with_none_locale_with_default | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers.py::test_format_decimal_with_none_locale | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_patterns | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_subpatterns | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_default_rounding | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_significant_digits | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_decimals | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_scientific_notation | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_formatting_of_very_small_decimals | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_nan_and_infinity | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_group_separator | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_format_decimal.py::test_compact | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_parsing.py::test_can_parse_decimals | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_numbers_parsing.py::test_parse_decimal_strict_mode | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_rule | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_rule_operands_i | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_rule_operands_v | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_rule_operands_w | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_rule_operands_f | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_rule_operands_t | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_other_is_ignored | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_to_javascript | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_to_python | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_to_gettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_in_range_list | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_within_range_list | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_cldr_modulo | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_plural_within_rules | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_locales_with_no_plural_rules_have_default | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_tokenize_well_formed | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_tokenize_malformed | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_next_token_empty | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_next_token_type_ok_and_no_value | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_next_token_type_ok_and_not_value | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_next_token_type_ok_and_value_ok | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_next_token_type_not_ok_and_value_ok | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_extract_operands | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural.py::test_gettext_compilation | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural_rule_parser.py::test_error_when_unexpected_end | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural_rule_parser.py::test_eq_relation | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural_rule_parser.py::test_in_range_relation | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural_rule_parser.py::test_negate | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural_rule_parser.py::test_or | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural_rule_parser.py::test_and | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_plural_rule_parser.py::test_or_and | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_smoke.py::test_smoke_dates | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_smoke.py::test_smoke_numbers | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_smoke.py::test_smoke_units | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_datetime | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_time | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_number | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_compact_decimal | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_compact_currency | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_percent | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_format.py::test_format_scientific | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_lazy_proxy.py::test_proxy_caches_result_of_function_call | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_lazy_proxy.py::test_can_disable_proxy_cache | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_lazy_proxy.py::test_can_copy_proxy | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_lazy_proxy.py::test_handle_attribute_error | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_lazy_proxy.py::test_lazy_proxy | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_pgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_pgettext_fallback | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_upgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_lpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_npgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_unpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_lnpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_dpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_dupgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_ldpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_dnpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_dunpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_ldnpgettext | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_load | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_null_translations_have_same_methods | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_null_translations_method_signature_compatibility | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_null_translations_same_return_values | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_support_translations.py::test_catalog_merge_files | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_units.py::test_new_cldr46_units | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_units.py::test_issue_1217 | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_units.py::test_deprecated_unit_ids | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_distinct | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_pathmatch | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_fixed_zone_negative_offset | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_fixed_zone_zero_offset | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_fixed_zone_positive_offset | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_parse_encoding_defined | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_parse_encoding_undefined | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_parse_encoding_non_ascii | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |
| tests/test_util.py::test_parse_future | upstream | - | - | - | excluded | outside Stage 1 message-catalog lifecycle scope |

Total: 733 | kept (covered): 92 | spec_gap: 0 | source-only: 0 | excluded: 641 | final_scoreable: 92
