# Spec To Test Map

oracle_version: 2026-08-04-artifact-only-v1
oracle_source: generated_public_contract
oracle_files: oracle/test_atomic.py, oracle/test_integration.py
runtime_requirements: oracle/requirements.txt
reference_source: https://github.com/PyCQA/isort
reference_commit: fd8bd075176d074af69aa6acae7ed89a6a89bb05
stage4_evidence: ARTIFACT_ONLY
counts: atomic=32, integration=34, system_e2e=0, total=66
depends_on_annotation_coverage: 34/34 integration tests; 42 atomic dependency edges
dependency_policy: every dependency target is a physical atomic test; no integration dependencies

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_exports_are_available` | atomic | Installable Surface | covered |
| 2 | `oracle/test_atomic.py::test_code_sorts_stdlib_and_third_party_sections` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_code_sorts_from_import_members` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_check_code_reports_sortedness` | atomic | Error Semantics | covered |
| 5 | `oracle/test_atomic.py::test_stream_writes_sorted_code_and_reports_change` | atomic | Installable Surface | covered |
| 6 | `oracle/test_atomic.py::test_check_stream_reports_sortedness` | atomic | Error Semantics | covered |
| 7 | `oracle/test_atomic.py::test_file_rewrites_and_returns_changed` | atomic | Installable Surface | covered |
| 8 | `oracle/test_atomic.py::test_check_file_reports_sortedness` | atomic | Error Semantics | covered |
| 9 | `oracle/test_atomic.py::test_place_module_identifies_standard_library` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_place_module_identifies_relative_import` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_place_module_with_reason_exposes_category_and_reason` | atomic | Installable Surface | covered |
| 12 | `oracle/test_atomic.py::test_config_profile_black_controls_documented_values` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_config_custom_section_places_known_module` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_config_add_and_remove_imports_transform_code` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_force_to_top_moves_named_import` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_no_sections_merges_import_groups` | atomic | Product State Model | covered |
| 17 | `oracle/test_atomic.py::test_from_first_orders_from_import_before_straight_import` | atomic | Product State Model | covered |
| 18 | `oracle/test_atomic.py::test_force_single_line_splits_from_import` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_length_sort_orders_shorter_modules_first` | atomic | Product State Model | covered |
| 20 | `oracle/test_atomic.py::test_import_heading_is_added_to_its_section` | atomic | Product State Model | covered |
| 21 | `oracle/test_atomic.py::test_vertical_hanging_output_mode_wraps_long_import` | atomic | Product State Model | covered |
| 22 | `oracle/test_atomic.py::test_inline_skip_comment_preserves_the_marked_import` | atomic | Representative Workflow | covered |
| 23 | `oracle/test_atomic.py::test_off_and_on_comments_preserve_only_the_disabled_block` | atomic | Representative Workflow | covered |
| 24 | `oracle/test_atomic.py::test_split_comment_starts_a_new_import_group` | atomic | Representative Workflow | covered |
| 25 | `oracle/test_atomic.py::test_no_inline_sort_preserves_member_order` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_find_imports_in_code_returns_all_imports` | atomic | Installable Surface | covered |
| 27 | `oracle/test_atomic.py::test_find_imports_unique_by_module_removes_duplicate_module_entries` | atomic | Installable Surface | covered |
| 28 | `oracle/test_atomic.py::test_find_imports_top_only_excludes_nested_imports` | atomic | Installable Surface | covered |
| 29 | `oracle/test_atomic.py::test_find_imports_in_stream_reads_the_given_stream` | atomic | Installable Surface | covered |
| 30 | `oracle/test_atomic.py::test_find_imports_in_file_reads_a_source_file` | atomic | Installable Surface | covered |
| 31 | `oracle/test_atomic.py::test_find_imports_in_paths_walks_python_files` | atomic | Installable Surface | covered |
| 32 | `oracle/test_atomic.py::test_file_output_stream_returns_sorted_content_without_rewriting` | atomic | Cross-View Invariants | covered |
| 33 | `oracle/test_integration.py::test_api_code_and_check_round_trip` | integration | Cross-View Invariants | covered |
| 34 | `oracle/test_integration.py::test_api_stream_output_is_checkable` | integration | Cross-View Invariants | covered |
| 35 | `oracle/test_integration.py::test_api_file_rewrite_then_check` | integration | Cross-View Invariants | covered |
| 36 | `oracle/test_integration.py::test_api_output_stream_preserves_source` | integration | Cross-View Invariants | covered |
| 37 | `oracle/test_integration.py::test_api_diff_exposes_unified_changes` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_api_profile_wraps_and_check_code_accepts` | integration | Product State Model | covered |
| 39 | `oracle/test_integration.py::test_custom_section_sort_and_place_agree` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_api_add_remove_and_check_round_trip` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_action_comment_blocks_override_add_imports` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_cli_sorts_single_file_in_place` | integration | Representative Workflow | covered |
| 43 | `oracle/test_integration.py::test_cli_check_clean_file_returns_zero` | integration | Representative Workflow | covered |
| 44 | `oracle/test_integration.py::test_cli_check_dirty_file_returns_one_without_write` | integration | Representative Workflow | covered |
| 45 | `oracle/test_integration.py::test_cli_check_diff_reports_changes_without_write` | integration | Representative Workflow | covered |
| 46 | `oracle/test_integration.py::test_cli_stdin_stdout_sorts_code` | integration | Representative Workflow | covered |
| 47 | `oracle/test_integration.py::test_cli_stdin_check_reports_dirty_input` | integration | Representative Workflow | covered |
| 48 | `oracle/test_integration.py::test_cli_stdout_leaves_file_unchanged` | integration | Representative Workflow | covered |
| 49 | `oracle/test_integration.py::test_cli_black_profile_formats_long_from_import` | integration | Representative Workflow | covered |
| 50 | `oracle/test_integration.py::test_cli_isort_cfg_changes_sectioning` | integration | Representative Workflow | covered |
| 51 | `oracle/test_integration.py::test_cli_pyproject_changes_sectioning` | integration | Representative Workflow | covered |
| 52 | `oracle/test_integration.py::test_cli_setup_cfg_changes_sectioning` | integration | Representative Workflow | covered |
| 53 | `oracle/test_integration.py::test_cli_tox_ini_changes_sectioning` | integration | Representative Workflow | covered |
| 54 | `oracle/test_integration.py::test_cli_editorconfig_changes_sectioning` | integration | Representative Workflow | covered |
| 55 | `oracle/test_integration.py::test_cli_settings_path_uses_custom_file` | integration | Representative Workflow | covered |
| 56 | `oracle/test_integration.py::test_cli_nearest_config_wins_for_nested_file` | integration | Representative Workflow | covered |
| 57 | `oracle/test_integration.py::test_cli_custom_sections_create_named_group` | integration | Representative Workflow | covered |
| 58 | `oracle/test_integration.py::test_cli_action_comments_preserve_off_block_and_sort_rest` | integration | Representative Workflow | covered |
| 59 | `oracle/test_integration.py::test_cli_skip_file_comment_accepts_unsorted_file` | integration | Representative Workflow | covered |
| 60 | `oracle/test_integration.py::test_cli_explicit_skip_requires_filter_files` | integration | Representative Workflow | covered |
| 61 | `oracle/test_integration.py::test_cli_skip_glob_skips_matching_file` | integration | Representative Workflow | covered |
| 62 | `oracle/test_integration.py::test_cli_add_and_remove_imports_update_file` | integration | Representative Workflow | covered |
| 63 | `oracle/test_integration.py::test_cli_append_only_and_force_adds_have_distinct_effects` | integration | Representative Workflow | covered |
| 64 | `oracle/test_integration.py::test_cli_source_path_places_project_module` | integration | Representative Workflow | covered |
| 65 | `oracle/test_integration.py::test_cli_multiline_mode_matches_api_projection` | integration | Representative Workflow | covered |
| 66 | `oracle/test_integration.py::test_cli_force_single_line_matches_documented_mode` | integration | Representative Workflow | covered |

`final_scoreable: 66`
