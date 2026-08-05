# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_get_exporter_resolves_public_local_exporters` | atomic | Dictionary Conversion | covered |
| 2 | `oracle/test_atomic.py::test_get_export_names_includes_local_textual_formats` | atomic | Dictionary Conversion | covered |
| 3 | `oracle/test_atomic.py::test_export_function_accepts_exporter_class_and_notebook_node` | atomic | Dictionary Conversion | covered |
| 4 | `oracle/test_atomic.py::test_resources_dict_returns_empty_string_for_missing_keys` | atomic | Dictionary Conversion | covered |
| 5 | `oracle/test_atomic.py::test_markdown_exporter_projects_markdown_and_code_cells` | atomic | Dictionary Conversion | covered |
| 6 | `oracle/test_atomic.py::test_python_exporter_comments_markdown_and_emits_code` | atomic | Dictionary Conversion | covered |
| 7 | `oracle/test_atomic.py::test_notebook_exporter_returns_notebook_json_string` | atomic | Typed Codecs | covered |
| 8 | `oracle/test_atomic.py::test_html_exporter_returns_html_document_with_rendered_markdown` | atomic | Dictionary Conversion | covered |
| 9 | `oracle/test_atomic.py::test_exporter_from_file_reads_notebook_stream` | atomic | Dictionary Conversion | covered |
| 10 | `oracle/test_atomic.py::test_data_type_filter_selects_first_available_priority` | atomic | Execution Controls | covered |
| 11 | `oracle/test_atomic.py::test_data_type_filter_warns_and_returns_empty_for_unavailable_format` | atomic | Dictionary Conversion | covered |
| 12 | `oracle/test_atomic.py::test_get_metadata_prefers_mimetype_metadata_then_top_level` | atomic | Dictionary Conversion | covered |
| 13 | `oracle/test_atomic.py::test_ansi_filters_strip_and_wrap_colored_text` | atomic | Dictionary Conversion | covered |
| 14 | `oracle/test_atomic.py::test_string_filters_project_wrapping_prompts_and_slices` | atomic | Dictionary Conversion | covered |
| 15 | `oracle/test_atomic.py::test_string_filters_project_paths_base64_and_ascii` | atomic | Dictionary Conversion | covered |
| 16 | `oracle/test_atomic.py::test_markdown_filter_renders_basic_html_without_pandoc` | atomic | Dictionary Conversion | covered |
| 17 | `oracle/test_atomic.py::test_add_anchor_adds_header_id_and_anchor_link` | atomic | Dictionary Conversion | covered |
| 18 | `oracle/test_atomic.py::test_comment_and_trailing_newline_filters_are_stable` | atomic | Dictionary Conversion | covered |
| 19 | `oracle/test_atomic.py::test_clear_output_preprocessor_removes_outputs_counts_and_output_metadata` | atomic | Dictionary Conversion | covered |
| 20 | `oracle/test_atomic.py::test_coalesce_streams_preprocessor_merges_adjacent_same_named_streams` | atomic | Dictionary Conversion | covered |
| 21 | `oracle/test_atomic.py::test_clear_metadata_preprocessor_preserves_configured_notebook_key` | atomic | Field Metadata And Configuration | covered |
| 22 | `oracle/test_atomic.py::test_regex_remove_preprocessor_removes_matching_source_cells` | atomic | Dictionary Conversion | covered |
| 23 | `oracle/test_atomic.py::test_tag_remove_preprocessor_removes_tagged_cells` | atomic | Dictionary Conversion | covered |
| 24 | `oracle/test_atomic.py::test_tag_remove_preprocessor_marks_tagged_input_for_omission` | atomic | Dictionary Conversion | covered |
| 25 | `oracle/test_atomic.py::test_tag_remove_preprocessor_removes_tagged_single_outputs` | atomic | Dictionary Conversion | covered |
| 26 | `oracle/test_atomic.py::test_highlight_magics_preprocessor_marks_magic_language` | atomic | Dictionary Conversion | covered |
| 27 | `oracle/test_atomic.py::test_extract_output_preprocessor_writes_binary_resource_and_cell_filename` | atomic | Typed Codecs | covered |
| 28 | `oracle/test_atomic.py::test_extract_output_preprocessor_respects_public_filename_metadata` | atomic | Dictionary Conversion | covered |
| 29 | `oracle/test_atomic.py::test_extract_attachments_preprocessor_rewrites_attachment_references` | atomic | Dictionary Conversion | covered |
| 30 | `oracle/test_atomic.py::test_files_writer_writes_main_output_and_resource_files` | atomic | Dictionary Conversion | covered |
| 31 | `oracle/test_atomic.py::test_stdout_writer_writes_output_to_stdout` | atomic | Dictionary Conversion | covered |
| 32 | `oracle/test_atomic.py::test_writer_base_requires_subclass_write_implementation` | atomic | Dictionary Conversion | covered |
| 33 | `oracle/test_integration.py::test_markdown_export_with_tagged_cell_removal_combines_preprocessor_and_template` | integration | Dictionary Conversion | covered |
| 34 | `oracle/test_integration.py::test_python_export_with_removed_input_tag_keeps_outputless_cell_metadata_projection` | integration | Dictionary Conversion | covered |
| 35 | `oracle/test_integration.py::test_notebook_export_with_clear_output_projects_clean_notebook_json` | integration | Typed Codecs | covered |
| 36 | `oracle/test_integration.py::test_markdown_export_with_coalesced_streams_projects_single_output_block` | integration | Dictionary Conversion | covered |
| 37 | `oracle/test_integration.py::test_markdown_export_with_regex_removed_cell_keeps_unmatched_cells` | integration | Dictionary Conversion | covered |
| 38 | `oracle/test_integration.py::test_notebook_export_with_metadata_clear_preserves_language_name_only` | integration | Dictionary Conversion | covered |
| 39 | `oracle/test_integration.py::test_html_export_extracts_png_output_resource_and_references_filename` | integration | Dictionary Conversion | covered |
| 40 | `oracle/test_integration.py::test_html_export_resources_can_be_written_by_files_writer` | integration | Dictionary Conversion | covered |
| 41 | `oracle/test_integration.py::test_markdown_export_extracts_attachment_and_rewrites_public_reference` | integration | Dictionary Conversion | covered |
| 42 | `oracle/test_integration.py::test_markdown_export_resources_can_be_written_by_files_writer` | integration | Dictionary Conversion | covered |
| 43 | `oracle/test_integration.py::test_public_get_exporter_class_feeds_public_export_function` | integration | Dictionary Conversion | covered |
| 44 | `oracle/test_integration.py::test_from_filename_sets_metadata_and_exports_file_contents` | integration | Dictionary Conversion | covered |
| 45 | `oracle/test_integration.py::test_python_export_with_magic_highlighting_keeps_code_and_metadata_side_effect` | integration | Dictionary Conversion | covered |
| 46 | `oracle/test_integration.py::test_markdown_filter_anchor_result_is_embedded_in_html_export_resource_flow` | integration | Results | covered |
| 47 | `oracle/test_integration.py::test_data_type_selection_agrees_with_exported_rich_output_resources` | integration | Dictionary Conversion | covered |
| 48 | `oracle/test_integration.py::test_ansi_html_filter_output_survives_markdown_export_as_html_text` | integration | Dictionary Conversion | covered |
| 49 | `oracle/test_integration.py::test_path_filter_matches_attachment_resource_path_projection` | integration | Dictionary Conversion | covered |
| 50 | `oracle/test_integration.py::test_notebook_export_reflects_single_output_tag_removal_in_json` | integration | Typed Codecs | covered |
| 51 | `oracle/test_integration.py::test_html_export_after_clear_output_omits_stream_text_but_keeps_source` | integration | Field Metadata And Configuration | covered |
| 52 | `oracle/test_integration.py::test_multiple_preprocessors_run_in_registration_order_for_markdown_export` | integration | Dictionary Conversion | covered |
| 53 | `oracle/test_integration.py::test_files_writer_persists_combined_attachment_and_output_resources` | integration | Dictionary Conversion | covered |
| 54 | `oracle/test_integration.py::test_export_function_body_and_resources_can_drive_files_writer` | integration | Dictionary Conversion | covered |
| 55 | `oracle/test_integration.py::test_python_exporter_from_file_stream_projects_same_code` | integration | Dictionary Conversion | covered |
| 56 | `oracle/test_integration.py::test_markdown_and_notebook_exporters_project_same_cell_order` | integration | Dictionary Conversion | covered |
| 57 | `oracle/test_integration.py::test_html_and_python_exporters_project_same_code_source_differently` | integration | Dictionary Conversion | covered |
| 58 | `oracle/test_integration.py::test_ipynb_alias_exporter_round_trips_public_notebook_json` | integration | Field Metadata And Configuration | covered |
| 59 | `oracle/test_integration.py::test_exporter_initializes_missing_resource_metadata_for_template_export` | integration | Dictionary Conversion | covered |
| 60 | `oracle/test_integration.py::test_base_exporter_with_custom_preprocessor_projects_modified_notebook_node` | integration | Dictionary Conversion | covered |

final_scoreable: 60
