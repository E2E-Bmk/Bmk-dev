# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_surface_exposes_version_and_runner_names` | atomic | Public Runner Surface | covered |
| 2 | `oracle/test_atomic.py::test_run_version_prints_pylint_and_astroid_versions` | atomic | Public Runner Surface | covered |
| 3 | `oracle/test_atomic.py::test_generate_rcfile_contains_main_section_and_message_controls` | atomic | CLI And Configuration Discovery | covered |
| 4 | `oracle/test_atomic.py::test_list_msgs_includes_emittable_message_headers` | atomic | CLI And Configuration Discovery | covered |
| 5 | `oracle/test_atomic.py::test_list_msgs_enabled_includes_default_enabled_message_symbol` | atomic | CLI And Configuration Discovery | covered |
| 6 | `oracle/test_atomic.py::test_help_msg_resolves_symbol_and_id` | atomic | CLI And Configuration Discovery | covered |
| 7 | `oracle/test_atomic.py::test_disable_all_without_enabled_messages_exits_with_no_files_to_lint` | atomic | Message Controls | covered |
| 8 | `oracle/test_atomic.py::test_disable_all_enable_unused_import_lints_only_unused_import` | atomic | Message Controls | covered |
| 9 | `oracle/test_atomic.py::test_inline_disable_suppresses_unused_import_message` | atomic | Message Controls | covered |
| 10 | `oracle/test_atomic.py::test_inline_disable_and_enable_restore_message_after_scope` | atomic | Message Controls | covered |
| 11 | `oracle/test_atomic.py::test_missing_module_docstring_can_be_disabled_by_cli` | atomic | Message Controls | covered |
| 12 | `oracle/test_atomic.py::test_missing_function_docstring_can_be_disabled_by_config_file` | atomic | CLI And Configuration Discovery | covered |
| 13 | `oracle/test_atomic.py::test_json_reporter_serializes_message_fields` | atomic | Reporter Projections | covered |
| 14 | `oracle/test_atomic.py::test_json2_reporter_serializes_message_and_statistics_fields` | atomic | Reporter Projections | covered |
| 15 | `oracle/test_atomic.py::test_text_output_reports_line_too_long_with_message_id` | atomic | Reporter Projections | covered |
| 16 | `oracle/test_atomic.py::test_unused_import_message_is_reported_with_symbol_and_category` | atomic | Representative Checker Facts | covered |
| 17 | `oracle/test_atomic.py::test_invalid_name_message_is_reported_for_mixed_case_function` | atomic | Representative Checker Facts | covered |
| 18 | `oracle/test_atomic.py::test_syntax_error_is_reported_as_error_and_nonzero` | atomic | Representative Checker Facts | covered |
| 19 | `oracle/test_atomic.py::test_import_error_message_is_reported_for_missing_local_module` | atomic | Message Controls | covered |
| 20 | `oracle/test_atomic.py::test_undefined_variable_message_reports_error_symbol` | atomic | Representative Checker Facts | covered |
| 21 | `oracle/test_atomic.py::test_fail_under_above_clean_score_exits_nonzero` | atomic | Score And Exit Behavior | covered |
| 22 | `oracle/test_atomic.py::test_exit_zero_overrides_message_status` | atomic | Score And Exit Behavior | covered |
| 23 | `oracle/test_atomic.py::test_score_can_be_suppressed_from_text_output` | atomic | Reporter Projections | covered |
| 24 | `oracle/test_atomic.py::test_json2_score_is_computed_for_clean_module` | atomic | Reporter Projections | covered |
| 25 | `oracle/test_atomic.py::test_output_option_writes_report_to_file` | atomic | Reporter Projections | covered |
| 26 | `oracle/test_atomic.py::test_run_pylint_helper_accepts_explicit_argument_sequence` | atomic | Public Runner Surface | covered |
| 27 | `oracle/test_atomic.py::test_run_pylint_on_package_path_reports_modules_from_package` | atomic | CLI Input Discovery | covered |
| 28 | `oracle/test_atomic.py::test_run_pyreverse_version_emits_version_string` | atomic | Pyreverse Local Projections | covered |
| 29 | `oracle/test_atomic.py::test_run_symilar_reports_zero_duplicates_for_different_files` | atomic | Symilar And Duplicate Projections | covered |
| 30 | `oracle/test_atomic.py::test_run_symilar_reports_duplicate_lines_for_identical_files` | atomic | Symilar And Duplicate Projections | covered |
| 31 | `oracle/test_integration.py::test_config_discovery_from_pylintrc_and_cli_override_share_one_run` | integration | CLI And Configuration Discovery | covered |
| 32 | `oracle/test_integration.py::test_json_and_text_reporters_agree_on_unused_import_fact` | integration | Reporter Projections | covered |
| 33 | `oracle/test_integration.py::test_json2_statistics_match_messages_from_a_small_module` | integration | Reporter Projections | covered |
| 34 | `oracle/test_integration.py::test_from_stdin_linting_and_json_reporting_use_the_provided_virtual_filename` | integration | Reporter Projections | covered |
| 35 | `oracle/test_integration.py::test_list_msgs_enabled_changes_when_config_disables_a_symbol` | integration | CLI And Configuration Discovery | covered |
| 36 | `oracle/test_integration.py::test_cli_output_file_and_stdout_empty_when_report_is_redirected` | integration | Reporter Projections | covered |
| 37 | `oracle/test_integration.py::test_package_linting_combines_init_and_module_messages` | integration | CLI Input Discovery | covered |
| 38 | `oracle/test_integration.py::test_enable_all_then_disable_symbol_restores_specific_message_control` | integration | Message Controls | covered |
| 39 | `oracle/test_integration.py::test_fail_under_and_exit_zero_interact_with_the_same_message_run` | integration | Score And Exit Behavior | covered |
| 40 | `oracle/test_integration.py::test_clean_module_json2_score_and_exit_code_are_consistent` | integration | Reporter Projections | covered |
| 41 | `oracle/test_integration.py::test_pyreverse_dot_projection_creates_class_and_package_files` | integration | Pyreverse Local Projections | covered |
| 42 | `oracle/test_integration.py::test_pyreverse_puml_projection_contains_class_names_and_relationship_tokens` | integration | Pyreverse Local Projections | covered |
| 43 | `oracle/test_integration.py::test_pyreverse_with_source_root_projects_package_names_from_src_layout` | integration | Pyreverse Local Projections | covered |
| 44 | `oracle/test_integration.py::test_symilar_duplicate_workflow_reports_duplicate_blocks_and_totals` | integration | Symilar And Duplicate Projections | covered |
| 45 | `oracle/test_integration.py::test_symilar_ignore_imports_removes_import_only_duplicates` | integration | Symilar And Duplicate Projections | covered |
| 46 | `oracle/test_integration.py::test_symilar_with_duplicates_zero_is_quiet_after_two_files` | integration | Symilar And Duplicate Projections | covered |
| 47 | `oracle/test_integration.py::test_duplicate_code_lint_and_symilar_agree_on_the_same_two_files` | integration | Symilar And Duplicate Projections | covered |
| 48 | `oracle/test_integration.py::test_help_msg_and_json_reporter_share_the_same_message_identity` | integration | Reporter Projections | covered |
| 49 | `oracle/test_integration.py::test_generate_rcfile_and_config_file_round_trip_controls_enabled_messages` | integration | CLI And Configuration Discovery | covered |
| 50 | `oracle/test_integration.py::test_cli_run_on_directory_and_file_paths_preserve_path_projection` | integration | CLI Input Discovery | covered |
| 51 | `oracle/test_integration.py::test_json_reporter_and_json2_reporter_serialize_same_message_core_fields` | integration | Reporter Projections | covered |
| 52 | `oracle/test_integration.py::test_inline_suppression_and_config_disable_compose_without_host_state` | integration | CLI And Configuration Discovery | covered |
| 53 | `oracle/test_integration.py::test_generated_config_and_json2_report_share_disabled_message_state` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_file_and_stdin_json_reports_preserve_the_same_message_identity` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_package_lint_and_pyreverse_share_module_name_projection` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_fail_under_threshold_and_json2_score_agree_on_a_clean_package` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_symilar_ignore_imports_and_duplicate_limit_compose_for_clean_files` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_help_lookup_and_json_report_keep_message_id_for_line_too_long` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_inline_disable_scope_and_json2_report_preserve_only_reenabled_messages` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_output_file_and_stdout_json_reports_preserve_the_same_semantic_message` | integration | Cross-View Invariants | covered |

final_scoreable: 60
