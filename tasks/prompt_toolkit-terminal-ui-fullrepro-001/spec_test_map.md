# prompt_toolkit Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_upstream_buffer_initial_state | atomic | ### Buffer and Document | covered | public Buffer initial/document projection |
| oracle/test_integration.py::test_upstream_cli_simple_text_input | system_e2e | ### Unit-Test I/O | covered | rewritten with public PromptSession/create_pipe_input/DummyOutput |
| oracle/test_integration.py::test_upstream_cli_accept_default_twice | system_e2e | ### Prompt Sessions | covered | rewritten with public PromptSession accept_default |
| oracle/test_atomic.py::test_upstream_pathcompleter_files_in_current_directory | atomic | ### Completion | covered | rewritten with tmp_path and public PathCompleter |
| oracle/test_atomic.py::test_upstream_pathcompleter_files_in_absolute_directory | atomic | ### Completion | covered | public PathCompleter absolute directory behavior |
| oracle/test_atomic.py::test_upstream_pathcompleter_only_directories | atomic | ### Completion | covered | public only_directories behavior |
| oracle/test_atomic.py::test_upstream_pathcompleter_min_input_len | atomic | ### Completion | covered | public min_input_len behavior |
| oracle/test_atomic.py::test_upstream_pathcompleter_get_paths_constrains_path | atomic | ### Completion | covered | public get_paths behavior |
| oracle/test_atomic.py::test_upstream_word_completer_static_word_list | atomic | ### Completion | covered | public WordCompleter matching behavior |
| oracle/test_atomic.py::test_upstream_word_completer_ignore_case | atomic | ### Completion | covered | public ignore_case behavior |
| oracle/test_atomic.py::test_upstream_word_completer_match_middle | atomic | ### Completion | covered | public match_middle behavior |
| oracle/test_atomic.py::test_upstream_word_completer_sentence | atomic | ### Completion | covered | public sentence behavior |
| oracle/test_atomic.py::test_upstream_word_completer_dynamic_word_list | atomic | ### Completion | covered | public dynamic word provider behavior |
| oracle/test_atomic.py::test_upstream_word_completer_pattern | atomic | ### Completion | covered | public pattern behavior |
| oracle/test_atomic.py::test_upstream_fuzzy_completer | atomic | ### Completion | covered | public FuzzyWordCompleter behavior |
| oracle/test_atomic.py::test_upstream_nested_completer | atomic | ### Completion | covered | public NestedCompleter behavior |
| oracle/test_atomic.py::test_upstream_merge_completers_deduplicate | atomic | ### Completion | covered | public merge_completers deduplicate behavior |
| oracle/test_atomic.py::test_upstream_document_current_char | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_text_before_cursor | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_text_after_cursor | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_lines | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_line_count | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_current_line_before_cursor | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_current_line_after_cursor | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_current_line | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_cursor_position_row_col | atomic | ### Buffer and Document | covered | public Document cursor row/column projection |
| oracle/test_atomic.py::test_upstream_document_translate_index_to_position | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_is_cursor_at_the_end | atomic | ### Buffer and Document | covered | public Document projection/helper behavior |
| oracle/test_atomic.py::test_upstream_document_get_word_before_cursor_pattern | atomic | ### Buffer and Document | covered | public Document word-boundary helper behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_basic_html | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_html_fg_bg | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_ansi_formatting | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_ansi_dim | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_ansi_256_color | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_ansi_true_color | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_template_interpolation | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_html_interpolation | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_merge | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_formatted_text_pygments_tokens | atomic | ### Formatted Text and Printing | covered | public formatted text conversion behavior |
| oracle/test_atomic.py::test_upstream_history_in_memory | atomic | ### History and Validation | covered | public History backend load/store behavior |
| oracle/test_atomic.py::test_upstream_history_file | atomic | ### History and Validation | covered | public History backend load/store behavior |
| oracle/test_atomic.py::test_upstream_history_threaded_file | atomic | ### History and Validation | covered | public History backend load/store behavior |
| oracle/test_atomic.py::test_upstream_history_threaded_in_memory | atomic | ### History and Validation | covered | public History backend load/store behavior |
| oracle/test_atomic.py::test_upstream_print_formatted_text_plain_fragments | atomic | ### Formatted Text and Printing | covered | plain output content, not exact renderer bytes |
| oracle/test_atomic.py::test_upstream_print_formatted_text_carriage_return_text | atomic | ### Formatted Text and Printing | covered | plain output content with carriage return input |
| oracle/test_atomic.py::test_upstream_style_from_dict | atomic | ### Styles and Color Depth | covered | public Style lookup/transformation behavior |
| oracle/test_atomic.py::test_upstream_style_class_combinations_latest_specific_rule | atomic | ### Styles and Color Depth | covered | public Style lookup/transformation behavior |
| oracle/test_atomic.py::test_upstream_style_class_combinations_order_priority | atomic | ### Styles and Color Depth | covered | public Style lookup/transformation behavior |
| oracle/test_atomic.py::test_upstream_style_substyles | atomic | ### Styles and Color Depth | covered | public Style lookup/transformation behavior |
| oracle/test_atomic.py::test_upstream_style_swap_light_and_dark_transformation | atomic | ### Styles and Color Depth | covered | public Style lookup/transformation behavior |
| oracle/test_atomic.py::test_upstream_style_adjust_brightness_transformation | atomic | ### Styles and Color Depth | covered | public brightness transformation behavior |
| oracle/test_atomic.py::test_generated_installable_surface_version_exports_are_consistent | atomic | ## Installable Surface | covered | Track B reference-observed public behavior; public root version exports are available and consistent |
| oracle/test_integration.py::test_generated_application_run_returns_exit_result_and_sets_active_app | integration | ### Application and AppSession | covered | Track B reference-observed public behavior; Application.run/exit active application projection |
| oracle/test_atomic.py::test_generated_application_exit_propagates_exception_instance | atomic | ### Application and AppSession | covered | Track B reference-observed public behavior; Application.exit(exception=...) propagates through run |
| oracle/test_atomic.py::test_generated_application_exit_rejects_result_and_exception_together | atomic | ## Error Semantics | covered | Track B reference-observed public behavior; Application.exit rejects result and exception together |
| oracle/test_integration.py::test_generated_create_app_session_supplies_defaults_for_prompt_and_print | system_e2e | ## Cross-View Invariants | covered | Track B reference-observed public behavior; AppSession input/output drive prompt and print defaults |
| oracle/test_integration.py::test_generated_nested_app_session_inherits_parent_output_when_omitted | integration | ### Application and AppSession | covered | Track B reference-observed public behavior; nested AppSession inherits specified parent output when omitted |
| oracle/test_integration.py::test_generated_prompt_session_accepts_document_default_and_preserves_cursor | integration | ## Cross-View Invariants | covered | Track B reference-observed public behavior; PromptSession default Document resets buffer text/cursor and returned text |
| oracle/test_atomic.py::test_generated_prompt_session_pre_run_exception_is_propagated | atomic | ### Prompt Sessions | covered | Track B reference-observed public behavior; pre_run exceptions propagate from prompt run |
| oracle/test_integration.py::test_generated_prompt_session_uses_supplied_history_object | integration | ## Cross-View Invariants | covered | Track B reference-observed public behavior; PromptSession default buffer uses supplied History object |
| oracle/test_integration.py::test_generated_buffer_document_projection_and_cursor_clamping | integration | ## Cross-View Invariants | covered | Track B reference-observed public behavior; Buffer.document mirrors text/cursor and cursor assignment clamps |
| oracle/test_atomic.py::test_generated_buffer_readonly_blocks_normal_mutation_but_bypass_updates | atomic | ## Error Semantics | covered | Track B reference-observed public behavior; read-only Buffer mutations raise, bypass set_document updates |
| oracle/test_atomic.py::test_generated_completion_state_returns_original_or_selected_projection | atomic | ### Completion | covered | Track B reference-observed public behavior; CompletionState computes original and selected text/cursor projection |
| oracle/test_atomic.py::test_generated_completion_display_meta_and_event_errors | atomic | ## Error Semantics | covered | Track B reference-observed public behavior; Completion display/meta projections and completion event assertion |
| oracle/test_atomic.py::test_generated_completer_variants_delegate_or_suppress_as_documented | atomic | ### Completion | covered | Track B reference-observed public behavior; dummy/dynamic/conditional/fuzzy completer behavior |
| oracle/test_integration.py::test_generated_completer_async_and_threaded_paths_match_sync_results | integration | ### Completion | covered | Track B reference-observed public behavior; async and ThreadedCompleter stream wrapped completions |
| oracle/test_atomic.py::test_generated_nested_fuzzy_and_common_suffix_completion_helpers | atomic | ### Completion | covered | Track B reference-observed public behavior; NestedCompleter, FuzzyWordCompleter, common suffix helpers |
| oracle/test_atomic.py::test_generated_history_backends_load_and_store_public_order | atomic | ### History and Validation | covered | Track B reference-observed public behavior; InMemoryHistory and DummyHistory public ordering/storage |
| oracle/test_atomic.py::test_generated_validator_variants_accept_or_raise_with_public_fields | atomic | ### History and Validation | covered | Track B reference-observed public behavior; Validator.from_callable and DummyValidator public behavior |
| oracle/test_integration.py::test_generated_conditional_and_dynamic_validators_call_wrapped_only_when_needed | integration | ### History and Validation | covered | Track B reference-observed public behavior; Conditional/Dynamic validators delegate only when active/provider exists |
| oracle/test_atomic.py::test_generated_key_bindings_register_remove_and_report_prefixes | atomic | ### Key Bindings | covered | Track B reference-observed public behavior; KeyBindings add/remove and invalid key errors |
| oracle/test_integration.py::test_generated_conditional_and_merged_key_bindings_are_live_views | integration | ### Key Bindings | covered | Track B reference-observed public behavior; ConditionalKeyBindings filters and merged binding live view |
| oracle/test_atomic.py::test_generated_formatted_text_conversion_template_and_plain_text_helpers | atomic | ### Formatted Text and Printing | covered | Track B reference-observed public behavior; formatted text conversion, template, merge and plain text helpers |
| oracle/test_atomic.py::test_generated_print_formatted_text_file_output_and_argument_error | atomic | ### Formatted Text and Printing | covered | Track B reference-observed public behavior; print_formatted_text output and mutually exclusive arguments |
| oracle/test_atomic.py::test_generated_style_color_parsing_merge_and_pygments_classname | atomic | ### Styles and Color Depth | covered | Track B reference-observed public behavior; color parsing, style merge and Pygments class names |
| oracle/test_atomic.py::test_generated_error_semantics_public_constructor_failures | atomic | ## Error Semantics | covered | Track B reference-observed public behavior; Document, WordCompleter and DummyOutput public error behavior |
