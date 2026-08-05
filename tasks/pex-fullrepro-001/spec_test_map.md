# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_surface_exposes_layout_and_pex_info` | atomic | Layout Projections | covered |
| 2 | `oracle/test_atomic.py::test_layout_for_value_rejects_unknown_layout_name` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_default_pex_info_exposes_empty_runtime_projection` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_default_pex_info_exposes_non_venv_distribution_projection` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_default_pex_info_dump_round_trips_public_build_fields` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_layout_values_have_stable_public_string_projection` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_fixture_support_wheel_has_dist_info_and_console_script` | atomic | Entry Point Execution | covered |
| 8 | `oracle/test_atomic.py::test_fixture_source_tree_contains_main_module` | atomic | Local Source Fixture | covered |
| 9 | `oracle/test_atomic.py::test_zipapp_build_embeds_pex_info_and_main_module` | atomic | Layout Projections | covered |
| 10 | `oracle/test_atomic.py::test_zipapp_layout_identifies_as_zipapp` | atomic | Layout Projections | covered |
| 11 | `oracle/test_atomic.py::test_packed_layout_identifies_as_packed_directory` | atomic | Layout Projections | covered |
| 12 | `oracle/test_atomic.py::test_loose_layout_identifies_as_loose_directory` | atomic | Layout Projections | covered |
| 13 | `oracle/test_atomic.py::test_pex_info_from_zipapp_reads_entry_point_and_build_properties` | atomic | Entry Point Execution | covered |
| 14 | `oracle/test_atomic.py::test_pex_info_roundtrip_from_json_preserves_injected_arguments` | atomic | Interpreter And Application Arguments | covered |
| 15 | `oracle/test_atomic.py::test_zipapp_pex_info_lists_local_wheel_distribution` | atomic | Layout Projections | covered |
| 16 | `oracle/test_atomic.py::test_zipapp_archive_contains_source_package_files` | atomic | Layout Projections | covered |
| 17 | `oracle/test_atomic.py::test_zipapp_archive_contains_dependency_wheel_projection` | atomic | Layout Projections | covered |
| 18 | `oracle/test_atomic.py::test_entry_point_execution_returns_source_and_wheel_markers` | atomic | Entry Point Execution | covered |
| 19 | `oracle/test_atomic.py::test_console_script_execution_returns_wheel_marker` | atomic | Entry Point Execution | covered |
| 20 | `oracle/test_atomic.py::test_injected_application_args_are_visible_to_entry_point` | atomic | Interpreter And Application Arguments | covered |
| 21 | `oracle/test_atomic.py::test_injected_python_args_enable_dev_mode` | atomic | Interpreter And Application Arguments | covered |
| 22 | `oracle/test_atomic.py::test_runtime_pex_root_gets_files_after_zipapp_execution` | atomic | Runner-Owned Runtime Side Effects | covered |
| 23 | `oracle/test_atomic.py::test_venv_mode_records_venv_flag_in_pex_info` | atomic | Runner-Owned Runtime Side Effects | covered |
| 24 | `oracle/test_atomic.py::test_venv_mode_executes_with_prefix_under_custom_pex_root` | atomic | Runner-Owned Runtime Side Effects | covered |
| 25 | `oracle/test_atomic.py::test_packed_layout_contains_top_level_main_and_pex_info` | atomic | Layout Projections | covered |
| 26 | `oracle/test_atomic.py::test_loose_layout_contains_layout_marker_and_source_files` | atomic | Layout Projections | covered |
| 27 | `oracle/test_atomic.py::test_module_entry_point_executes_with_python_m_style` | atomic | Entry Point Execution | covered |
| 28 | `oracle/test_atomic.py::test_build_with_explicit_runtime_pex_root_records_configured_value` | atomic | Runner-Owned Runtime Side Effects | covered |
| 29 | `oracle/test_atomic.py::test_pex_info_from_pex_matches_raw_pex_info_json` | atomic | PEX-INFO Metadata | covered |
| 30 | `oracle/test_atomic.py::test_console_script_pex_info_records_resolved_entry_point` | atomic | Entry Point Execution | covered |
| 31 | `oracle/test_integration.py::test_zipapp_build_inspect_and_run_entry_point_workflow` | integration | Entry Point Execution | covered |
| 32 | `oracle/test_integration.py::test_packed_layout_build_inspect_and_run_directory_workflow` | integration | Layout Projections | covered |
| 33 | `oracle/test_integration.py::test_loose_layout_build_inspect_and_run_directory_workflow` | integration | Layout Projections | covered |
| 34 | `oracle/test_integration.py::test_console_script_build_info_and_runtime_workflow` | integration | Entry Point Execution | covered |
| 35 | `oracle/test_integration.py::test_source_and_wheel_markers_survive_archive_and_execution_workflow` | integration | Layout Projections | covered |
| 36 | `oracle/test_integration.py::test_injected_app_args_are_stored_in_info_and_observed_at_runtime` | integration | Interpreter And Application Arguments | covered |
| 37 | `oracle/test_integration.py::test_injected_python_args_are_stored_and_observed_at_runtime` | integration | Interpreter And Application Arguments | covered |
| 38 | `oracle/test_integration.py::test_custom_pex_root_populates_runtime_cache_and_preserves_output` | integration | Runner-Owned Runtime Side Effects | covered |
| 39 | `oracle/test_integration.py::test_venv_pex_root_populates_venv_and_preserves_output` | integration | Runner-Owned Runtime Side Effects | covered |
| 40 | `oracle/test_integration.py::test_configured_runtime_pex_root_is_used_for_local_execution` | integration | Runner-Owned Runtime Side Effects | covered |
| 41 | `oracle/test_integration.py::test_raw_pex_info_api_projection_and_runtime_agree` | integration | PEX-INFO Metadata | covered |
| 42 | `oracle/test_integration.py::test_three_layouts_share_same_entry_point_runtime_projection` | integration | Entry Point Execution | covered |
| 43 | `oracle/test_integration.py::test_distribution_projection_and_console_script_runtime_agree` | integration | Entry Point Execution | covered |
| 44 | `oracle/test_integration.py::test_module_style_entry_point_records_module_and_runs_source_code` | integration | Entry Point Execution | covered |
| 45 | `oracle/test_integration.py::test_runtime_args_are_passed_to_console_script_without_source_tree` | integration | Interpreter And Application Arguments | covered |
| 46 | `oracle/test_integration.py::test_runtime_args_are_appended_to_source_entry_point_invocation` | integration | Interpreter And Application Arguments | covered |
| 47 | `oracle/test_integration.py::test_venv_execution_combines_app_args_python_args_and_source_imports` | integration | Runner-Owned Runtime Side Effects | covered |
| 48 | `oracle/test_integration.py::test_packed_layout_runs_with_runner_owned_pex_root_workflow` | integration | Runner-Owned Runtime Side Effects | covered |
| 49 | `oracle/test_integration.py::test_loose_layout_runs_from_directory_and_keeps_source_projection` | integration | Layout Projections | covered |
| 50 | `oracle/test_integration.py::test_archive_distribution_file_and_pex_info_distribution_share_name` | integration | Layout Projections | covered |
| 51 | `oracle/test_integration.py::test_venv_console_script_workflow_uses_wheel_entry_point` | integration | Runner-Owned Runtime Side Effects | covered |
| 52 | `oracle/test_integration.py::test_configured_runtime_root_and_venv_mode_create_runner_owned_venv` | integration | Runner-Owned Runtime Side Effects | covered |
| 53 | `oracle/test_integration.py::test_console_script_injected_args_are_stored_and_visible` | integration | Interpreter And Application Arguments | covered |
| 54 | `oracle/test_integration.py::test_console_script_injected_python_args_are_stored_and_visible` | integration | Interpreter And Application Arguments | covered |
| 55 | `oracle/test_integration.py::test_zipapp_public_layout_api_archive_listing_and_runtime_align` | integration | Layout Projections | covered |
| 56 | `oracle/test_integration.py::test_module_entry_point_and_runtime_arguments_share_one_projection` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_configured_runtime_root_is_shared_by_archive_metadata_and_execution` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_console_script_archive_metadata_and_injected_runtime_arguments_agree` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_venv_module_entry_point_keeps_metadata_and_runtime_consistent` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_layout_variants_keep_distribution_metadata_and_runtime_markers_aligned` | integration | Cross-View Invariants | covered |

final_scoreable: 60
