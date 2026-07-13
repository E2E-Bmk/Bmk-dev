# Spec Test Map

oracle_source: upstream_and_generated
track_a_source: filter/rewritten_upstream_tests.py
track_b_source: filter/generated_tests.py

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| `filter/rewritten_upstream_tests.py::test_annotate_report_marks_missing_lines` | upstream | integration | Report Semantics | covered | Annotated report marks executed and missing lines semantically. |
| `filter/rewritten_upstream_tests.py::test_branch_measurement_records_arcs` | upstream | atomic | Measurement Semantics | covered | Branch measurement records arcs and branch stats. |
| `filter/rewritten_upstream_tests.py::test_cli_combine_merges_parallel_data_files` | upstream | system_e2e | `coverage combine` and `coverage erase` | covered | combine merges parallel data files into one data file. |
| `filter/rewritten_upstream_tests.py::test_cli_erase_removes_configured_data_file` | upstream | atomic | `coverage combine` and `coverage erase` | covered | erase removes the configured data file. |
| `filter/rewritten_upstream_tests.py::test_cli_help_and_version_exit_successfully` | upstream | atomic | `coverage help` | covered | Help and version CLI commands succeed. |
| `filter/rewritten_upstream_tests.py::test_cli_report_fail_under_returns_status_two` | upstream | system_e2e | `coverage report` | covered | report --fail-under returns status 2 below threshold. |
| `filter/rewritten_upstream_tests.py::test_cli_run_module_passes_program_arguments` | upstream | system_e2e | `coverage run` | covered | coverage run -m executes a module and passes program arguments. |
| `filter/rewritten_upstream_tests.py::test_cli_run_report_and_json_share_data_file` | upstream | system_e2e | Cross-View Invariants | covered | CLI run, report, and JSON read the same data file. |
| `filter/rewritten_upstream_tests.py::test_coverage_current_tracks_collecting_instance` | upstream | atomic | Coverage | covered | Coverage.current() tracks the active public Coverage collector. |
| `filter/rewritten_upstream_tests.py::test_coverage_data_add_arcs_round_trips_to_disk` | upstream | atomic | CoverageData | covered | CoverageData arc data write/read round-trip. |
| `filter/rewritten_upstream_tests.py::test_coverage_data_add_lines_round_trips_to_disk` | upstream | atomic | CoverageData | covered | CoverageData line data write/read round-trip. |
| `filter/rewritten_upstream_tests.py::test_coverage_data_dumps_and_loads_preserve_lines` | upstream | atomic | CoverageData | covered | CoverageData serialization preserves line data. |
| `filter/rewritten_upstream_tests.py::test_coverage_data_query_context_filters_lines` | upstream | integration | CoverageData | covered | CoverageData context queries filter visible lines. |
| `filter/rewritten_upstream_tests.py::test_coverage_data_update_merges_measured_files` | upstream | integration | CoverageData | covered | CoverageData.update merges measured files from another data object. |
| `filter/rewritten_upstream_tests.py::test_coverage_file_environment_selects_data_file` | upstream | integration | Configuration | covered | COVERAGE_FILE selects the command data file. |
| `filter/rewritten_upstream_tests.py::test_data_file_none_keeps_measurement_in_memory` | upstream | atomic | Coverage | covered | data_file=None keeps measurement accessible without writing default data file. |
| `filter/rewritten_upstream_tests.py::test_exclusion_rules_remove_lines_from_missing_report` | upstream | integration | Measurement Semantics | covered | Exclusion rules remove excluded lines from missing-line reporting. |
| `filter/rewritten_upstream_tests.py::test_html_report_writes_index_and_source_page` | upstream | system_e2e | `coverage json`, `coverage xml`, and `coverage html` | covered | HTML report writes an index and source pages. |
| `filter/rewritten_upstream_tests.py::test_include_and_omit_filters_affect_measured_files` | upstream | integration | Cross-View Invariants | covered | Include/omit filters affect measured files. |
| `filter/rewritten_upstream_tests.py::test_invalid_config_file_raises_config_error` | upstream | atomic | Error Semantics | covered | Invalid configuration raises ConfigError. |
| `filter/rewritten_upstream_tests.py::test_json_report_contains_totals_and_file_details` | upstream | system_e2e | `coverage json`, `coverage xml`, and `coverage html` | covered | JSON report exposes totals and per-file data from measured execution. |
| `filter/rewritten_upstream_tests.py::test_lcov_report_mentions_source_file_and_lines` | upstream | system_e2e | Report Semantics | covered | LCOV report includes source-file and line execution records. |
| `filter/rewritten_upstream_tests.py::test_missing_source_raises_public_no_source` | upstream | atomic | Error Semantics | covered | Missing measured source raises NoSource. |
| `filter/rewritten_upstream_tests.py::test_no_data_error_for_report_without_measurement` | upstream | atomic | Error Semantics | covered | Reporting without data raises NoDataError. |
| `filter/rewritten_upstream_tests.py::test_public_report_methods_return_same_total_for_same_data` | upstream | system_e2e | Cross-View Invariants | covered | Programmatic report methods agree on totals for the same data. |
| `filter/rewritten_upstream_tests.py::test_rcfile_config_controls_branch_and_report_output` | upstream | integration | Configuration | covered | Configuration controls branch measurement and report missing output. |
| `filter/rewritten_upstream_tests.py::test_statement_measurement_records_executed_lines` | upstream | atomic | Measurement Semantics | covered | Statement measurement records executed lines and no arcs. |
| `filter/rewritten_upstream_tests.py::test_xml_report_writes_cobertura_style_document` | upstream | system_e2e | `coverage json`, `coverage xml`, and `coverage html` | covered | XML report writes Cobertura-style file and class elements. |
| `filter/generated_tests.py::test_cli_branch_context_json_and_total_report_agree` | generated | system_e2e | Cross-View Invariants + Representative Workflow | covered | CLI branch run, JSON contexts, and total report agree on the same data. |
| `filter/generated_tests.py::test_cli_xml_report_exposes_branch_totals_and_missing_branch` | generated | system_e2e | `coverage json`, `coverage xml`, and `coverage html` | covered | XML report exposes branch totals and partial branch coverage. |
| `filter/generated_tests.py::test_configured_data_file_is_shared_by_cli_and_coveragedata` | generated | integration | Data Files | covered | Configured CLI data file can be read through CoverageData. |
| `filter/generated_tests.py::test_programmatic_branch_contexts_survive_serialization` | generated | integration | CoverageData | covered | Branch arcs and contexts survive CoverageData serialization. |
| `filter/generated_tests.py::test_coverage_collect_context_manager_records_lines` | generated | integration | Public API + Coverage | covered | Coverage.collect records executed statement lines through the public context manager. |
| `filter/generated_tests.py::test_coverage_analysis_and_analysis2_report_missing_lines` | generated | integration | Measurement Semantics | covered | Programmatic analysis methods report executable and missing line data. |
| `filter/generated_tests.py::test_exclude_and_clear_exclude_change_missing_line_analysis` | generated | integration | Measurement Semantics | covered | Exclusion rules alter missing-line analysis and can be cleared. |
| `filter/generated_tests.py::test_switch_context_filters_coveragedata_queries` | generated | integration | Cross-View Invariants | covered | Switching contexts records queryable context-specific line data. |
| `filter/generated_tests.py::test_include_omit_measurement_controls_measured_files` | generated | integration | Configuration | covered | Include and omit settings control which files are measured. |
| `filter/generated_tests.py::test_programmatic_json_xml_html_and_lcov_reports_share_total` | generated | system_e2e | Cross-View Invariants | covered | Programmatic JSON, XML, HTML, and LCOV reports agree on total coverage for the same data. |
| `filter/generated_tests.py::test_combine_keep_preserves_parallel_input_files` | generated | system_e2e | `coverage combine` and `coverage erase` | covered | Combine --keep merges parallel data while preserving input files. |
| `filter/generated_tests.py::test_cli_erase_removes_coverage_file_and_report_has_no_data` | generated | integration | `coverage combine` and `coverage erase` | covered | Erase removes persisted data and later reporting has no measured data. |
| `filter/generated_tests.py::test_coverage_data_update_merges_line_data_objects` | generated | atomic | CoverageData | covered | CoverageData.update merges measured files and line data. |
| `filter/generated_tests.py::test_coverage_data_file_tracer_and_touch_file_roundtrip` | generated | atomic | CoverageData | covered | CoverageData touch_file records measured empty file and file tracer metadata. |
| `filter/generated_tests.py::test_coverage_data_purge_files_removes_measured_file` | generated | atomic | CoverageData | covered | CoverageData.purge_files clears queryable data for selected files. |
| `filter/generated_tests.py::test_invalid_rcfile_reports_config_error_via_cli_and_api` | generated | atomic | Error Semantics | covered | Invalid config is reported as a CLI failure and ConfigError through the API. |
| `filter/generated_tests.py::test_report_without_data_raises_no_data_error` | generated | atomic | Error Semantics | covered | Programmatic report without measured data raises NoDataError. |
| `filter/generated_tests.py::test_missing_source_file_raises_no_source` | generated | atomic | Error Semantics | covered | Reporting a measured file whose source is gone raises NoSource. |
| `filter/generated_tests.py::test_cli_run_missing_script_fails_nonzero` | generated | atomic | Error Semantics | covered | coverage run for a missing script fails nonzero. |
| `filter/generated_tests.py::test_cli_run_module_passes_program_arguments` | generated | system_e2e | `coverage run` | covered | coverage run -m executes a module and passes program arguments. |
| `filter/generated_tests.py::test_cli_debug_data_reports_measured_file` | generated | integration | Command-Line Behavior + `coverage debug` | covered | coverage debug data reports measured data for a public diagnostic topic. |
| `filter/generated_tests.py::test_coverage_file_environment_is_used_by_report_command` | generated | integration | Data Files | covered | COVERAGE_FILE is used consistently by run and report commands. |

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_installable_surface_imports_version_and_module_cli` | generated | atomic | Installable Surface | covered | Retroactive public Coverage.py installable surface test for Gate D coverage. |
Total: 51 | kept (covered): 51 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 51
