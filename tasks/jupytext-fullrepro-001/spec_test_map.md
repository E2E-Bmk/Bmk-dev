# Spec Test Map - jupytext-fullrepro-001

oracle_version: 2026-08-04-artifact-only-v1
oracle_source: generated_public_api
oracle_files: oracle/test_atomic.py, oracle/test_integration.py
runtime_requirements: oracle/requirements.txt
reference_source: https://github.com/jupytext/jupytext
reference_commit: a84c8826228dd99fc4478741736746e7e577a610
stage4_evidence: ARTIFACT_ONLY
counts: atomic=35, integration=34, system_e2e=0, total=69
depends_on_annotation_coverage: 34/34 integration tests
final_scoreable: 69

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| oracle/test_atomic.py::test_public_version_is_string | generated | atomic | positive | Format Detection And Public API | covered | version string |
| oracle/test_atomic.py::test_notebook_extensions_include_core_text_and_ipynb_formats | generated | atomic | positive | Format Detection And Public API | covered | extension registry |
| oracle/test_atomic.py::test_guess_format_detects_percent_script_marker | generated | atomic | positive | Format Detection And Public API | covered | percent format detection |
| oracle/test_atomic.py::test_guess_format_uses_light_for_plain_python_script | generated | atomic | positive | Format Detection And Public API | covered | light format detection |
| oracle/test_atomic.py::test_guess_format_detects_myst_code_cell_directive | generated | atomic | positive | Format Detection And Public API | covered | MyST format detection |
| oracle/test_atomic.py::test_get_format_implementation_resolves_extension_and_name | generated | atomic | positive | Format Detection And Public API | covered | implementation resolution |
| oracle/test_atomic.py::test_get_format_implementation_rejects_unknown_extension | generated | atomic | failure_path | Error Semantics | covered | unknown extension |
| oracle/test_atomic.py::test_reads_percent_script_preserves_markdown_and_code_cells | generated | atomic | positive | Script Notebook Formats | covered | percent reader cells |
| oracle/test_atomic.py::test_reads_percent_script_parses_title_type_and_metadata | generated | atomic | positive | Script Notebook Formats | covered | percent reader metadata |
| oracle/test_atomic.py::test_reads_percent_script_restores_raw_cell_source | generated | atomic | positive | Script Notebook Formats | covered | percent raw cell |
| oracle/test_atomic.py::test_reads_percent_script_uncomments_python_magic_lines | generated | atomic | positive | Script Notebook Formats | covered | percent magic lines |
| oracle/test_atomic.py::test_reads_light_script_splits_markdown_and_code_paragraphs | generated | atomic | positive | Script Notebook Formats | covered | light reader cells |
| oracle/test_atomic.py::test_reads_light_script_parses_explicit_cell_metadata | generated | atomic | positive | Script Notebook Formats | covered | light reader metadata |
| oracle/test_atomic.py::test_reads_markdown_code_fence_with_cell_metadata | generated | atomic | positive | Markdown Notebook Formats | covered | Markdown code fence |
| oracle/test_atomic.py::test_reads_markdown_raw_cell_markers | generated | atomic | positive | Markdown Notebook Formats | covered | Markdown raw markers |
| oracle/test_atomic.py::test_reads_markdown_noeval_fence_as_markdown | generated | atomic | positive | Markdown Notebook Formats | covered | noeval fence |
| oracle/test_atomic.py::test_reads_markdown_active_md_fence_as_raw_cell | generated | atomic | positive | Markdown Notebook Formats | covered | active md fence |
| oracle/test_atomic.py::test_reads_myst_code_cell_with_short_metadata | generated | atomic | positive | Markdown Notebook Formats | covered | MyST code cell |
| oracle/test_atomic.py::test_reads_myst_raw_cell_with_metadata_option | generated | atomic | positive | Markdown Notebook Formats | covered | MyST raw cell |
| oracle/test_atomic.py::test_reads_rmarkdown_code_chunk_metadata | generated | atomic | positive | Markdown Notebook Formats | covered | R Markdown chunk metadata |
| oracle/test_atomic.py::test_writes_percent_script_includes_cell_markers | generated | atomic | positive | Script Notebook Formats | covered | percent writer markers |
| oracle/test_atomic.py::test_writes_percent_script_comments_markdown_and_raw_sources | generated | atomic | positive | Script Notebook Formats | covered | percent writer comments |
| oracle/test_atomic.py::test_writes_percent_script_comments_magic_by_default | generated | atomic | positive | Script Notebook Formats | covered | magic line output |
| oracle/test_atomic.py::test_writes_light_script_uses_plus_cell_markers | generated | atomic | positive | Script Notebook Formats | covered | light writer markers |
| oracle/test_atomic.py::test_writes_markdown_includes_yaml_header_and_python_fence | generated | atomic | positive | Markdown Notebook Formats | covered | Markdown writer header |
| oracle/test_atomic.py::test_writes_markdown_uses_raw_cell_comment_markers | generated | atomic | positive | Markdown Notebook Formats | covered | Markdown raw writer |
| oracle/test_atomic.py::test_writes_myst_uses_code_cell_directive | generated | atomic | positive | Markdown Notebook Formats | covered | MyST writer directive |
| oracle/test_atomic.py::test_writes_rmarkdown_uses_chunk_options | generated | atomic | positive | Markdown Notebook Formats | covered | R Markdown writer options |
| oracle/test_atomic.py::test_writes_ipynb_returns_json_notebook_text | generated | atomic | positive | Format Detection And Public API | covered | ipynb JSON writer |
| oracle/test_atomic.py::test_reads_with_as_version_returns_requested_notebook_version | generated | atomic | positive | Format Detection And Public API | covered | requested notebook version |
| oracle/test_atomic.py::test_reads_rejects_unknown_text_format | generated | atomic | failure_path | Error Semantics | covered | unknown text format |
| oracle/test_atomic.py::test_read_uses_path_extension_to_select_script_format | generated | atomic | positive | Format Detection And Public API | covered | extension based read |
| oracle/test_atomic.py::test_read_rejects_missing_file | generated | atomic | failure_path | Error Semantics | covered | missing file |
| oracle/test_atomic.py::test_write_uses_output_extension_when_format_is_absent | generated | atomic | positive | Format Detection And Public API | covered | extension based write |
| oracle/test_atomic.py::test_write_with_explicit_format_creates_text_file | generated | atomic | positive | Format Detection And Public API | covered | explicit format write |
| oracle/test_integration.py::test_percent_string_round_trip_preserves_cell_types_sources_and_tags | generated | integration | positive | Cross-View Invariants | covered | CVI-1 percent round trip |
| oracle/test_integration.py::test_light_string_round_trip_preserves_cell_types_sources_and_tags | generated | integration | positive | Cross-View Invariants | covered | CVI-1 light round trip |
| oracle/test_integration.py::test_markdown_string_round_trip_preserves_cell_types_sources_and_tags | generated | integration | positive | Cross-View Invariants | covered | CVI-2 Markdown round trip |
| oracle/test_integration.py::test_myst_string_round_trip_preserves_cell_types_sources_and_tags | generated | integration | positive | Cross-View Invariants | covered | CVI-2 MyST round trip |
| oracle/test_integration.py::test_rmarkdown_string_round_trip_preserves_code_cell_metadata | generated | integration | positive | Cross-View Invariants | covered | CVI-2 R Markdown round trip |
| oracle/test_integration.py::test_file_write_then_read_percent_script_uses_same_notebook_inputs | generated | integration | positive | Cross-View Invariants | covered | CVI-3 file write/read |
| oracle/test_integration.py::test_ipynb_file_write_then_read_preserves_outputs | generated | integration | positive | Cross-View Invariants | covered | CVI-4 ipynb outputs |
| oracle/test_integration.py::test_guess_format_result_can_drive_reads_for_percent_text | generated | integration | positive | Cross-View Invariants | covered | CVI-5 guess to reads |
| oracle/test_integration.py::test_format_implementation_metadata_matches_written_text_representation | generated | integration | positive | Cross-View Invariants | covered | CVI-6 implementation to writes |
| oracle/test_integration.py::test_markdown_metadata_filter_round_trip_keeps_kernelspec_but_omits_custom_top_level | generated | integration | positive | Cross-View Invariants | covered | CVI-7 metadata filters |
| oracle/test_integration.py::test_magic_line_round_trip_restores_original_code_source | generated | integration | positive | Cross-View Invariants | covered | percent magic round trip |
| oracle/test_integration.py::test_raw_markdown_cell_round_trip_preserves_source_and_metadata | generated | integration | positive | Cross-View Invariants | covered | Markdown raw round trip |
| oracle/test_integration.py::test_cli_version_reports_installed_package_version | generated | integration | positive | Command Line Conversion And Pairing | covered | version command |
| oracle/test_integration.py::test_cli_converts_ipynb_file_to_percent_script | generated | integration | positive | Command Line Conversion And Pairing | covered | CVI-8 ipynb to percent |
| oracle/test_integration.py::test_cli_converts_percent_script_to_ipynb_file | generated | integration | positive | Command Line Conversion And Pairing | covered | CVI-8 percent to ipynb |
| oracle/test_integration.py::test_cli_output_dash_writes_converted_text_to_stdout | generated | integration | positive | Command Line Conversion And Pairing | covered | output dash |
| oracle/test_integration.py::test_cli_reads_ipynb_from_stdin_and_writes_percent_to_stdout | generated | integration | positive | Command Line Conversion And Pairing | covered | stdin to stdout |
| oracle/test_integration.py::test_cli_set_formats_updates_notebook_pairing_metadata | generated | integration | positive | Command Line Conversion And Pairing | covered | CVI-9 set formats |
| oracle/test_integration.py::test_cli_sync_creates_missing_text_pair_from_ipynb | generated | integration | positive | Command Line Conversion And Pairing | covered | CVI-9 sync creates pair |
| oracle/test_integration.py::test_cli_sync_uses_newer_text_pair_to_update_ipynb_inputs | generated | integration | positive | Command Line Conversion And Pairing | covered | CVI-10 newer text pair |
| oracle/test_integration.py::test_cli_update_to_ipynb_preserves_existing_outputs_while_replacing_inputs | generated | integration | positive | Command Line Conversion And Pairing | covered | CVI-10 update preserves outputs |
| oracle/test_integration.py::test_cli_test_round_trip_percent_conversion_exits_success | generated | integration | positive | Command Line Conversion And Pairing | covered | round-trip test |
| oracle/test_integration.py::test_cli_option_notebook_metadata_filter_controls_markdown_header | generated | integration | positive | Configuration And Metadata Filters | covered | CVI-7 CLI metadata option |
| oracle/test_integration.py::test_jupytext_toml_global_formats_drive_sync_pair_creation | generated | integration | positive | Configuration And Metadata Filters | covered | jupytext.toml formats |
| oracle/test_integration.py::test_pyproject_tool_jupytext_formats_drive_sync_pair_creation | generated | integration | positive | Configuration And Metadata Filters | covered | pyproject formats |
| oracle/test_integration.py::test_configured_markdown_pair_sync_uses_requested_format | generated | integration | positive | Configuration And Metadata Filters | covered | configured Markdown pair |
| oracle/test_integration.py::test_cli_converts_myst_markdown_to_ipynb | generated | integration | positive | Command Line Conversion And Pairing | covered | MyST CLI conversion |
| oracle/test_integration.py::test_cli_converts_rmarkdown_to_ipynb | generated | integration | positive | Command Line Conversion And Pairing | covered | R Markdown CLI conversion |
| oracle/test_integration.py::test_cli_stdout_markdown_can_be_read_by_python_api | generated | integration | positive | Cross-View Invariants | covered | CVI-8 stdout to API |
| oracle/test_integration.py::test_cli_chained_conversion_py_to_ipynb_to_markdown_preserves_inputs | generated | integration | positive | Cross-View Invariants | covered | CVI-8 chained conversion |
| oracle/test_integration.py::test_cli_test_strict_reports_success_for_stable_percent_conversion | generated | integration | positive | Command Line Conversion And Pairing | covered | strict round-trip test |
| oracle/test_integration.py::test_cli_invalid_requested_format_exits_nonzero_without_output_file | generated | integration | failure_path | Error Semantics | covered | unknown CLI format |
| oracle/test_integration.py::test_cli_set_formats_to_single_ipynb_disables_text_pair_metadata | generated | integration | positive | Command Line Conversion And Pairing | covered | single format pairing |
| oracle/test_integration.py::test_paired_sync_keeps_ipynb_outputs_when_text_inputs_are_newer | generated | integration | positive | Cross-View Invariants | covered | CVI-10 paired output preservation |
