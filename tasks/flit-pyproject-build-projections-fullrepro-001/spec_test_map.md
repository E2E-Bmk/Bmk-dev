# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_static_build_hooks_report_no_extra_requirements` | atomic | Installable Surface | covered |
| 2 | `oracle/test_atomic.py::test_prepare_metadata_returns_dist_info_directory` | atomic | Installable Surface | covered |
| 3 | `oracle/test_atomic.py::test_prepared_metadata_exposes_project_identity` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_prepared_metadata_contains_readme_description` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_prepared_metadata_contains_authors_and_dependencies` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_prepared_metadata_contains_urls_and_license` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_prepared_metadata_writes_scripts_and_entry_points` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_wheel_filename_normalizes_distribution_name` | atomic | Installable Surface | covered |
| 9 | `oracle/test_atomic.py::test_wheel_contains_package_files` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_wheel_contains_external_data_mapping` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_wheel_contains_license_file` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_wheel_metadata_declares_pure_python_tag` | atomic | Installable Surface | covered |
| 13 | `oracle/test_atomic.py::test_wheel_record_lists_every_archive_member` | atomic | Cross-View Invariants | covered |
| 14 | `oracle/test_atomic.py::test_wheel_record_hashes_match_archive_bytes` | atomic | Cross-View Invariants | covered |
| 15 | `oracle/test_atomic.py::test_editable_wheel_uses_source_path_file` | atomic | Installable Surface | covered |
| 16 | `oracle/test_atomic.py::test_editable_wheel_omits_copied_package_files` | atomic | Installable Surface | covered |
| 17 | `oracle/test_atomic.py::test_sdist_has_normalized_filename_and_single_root` | atomic | Installable Surface | covered |
| 18 | `oracle/test_atomic.py::test_sdist_contains_build_inputs_and_package_files` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_sdist_excludes_bytecode_cache` | atomic | Product State Model | covered |
| 20 | `oracle/test_atomic.py::test_editable_metadata_hook_creates_metadata` | atomic | Installable Surface | covered |
| 21 | `oracle/test_atomic.py::test_src_layout_wheel_uses_configured_module` | atomic | Product State Model | covered |
| 22 | `oracle/test_atomic.py::test_namespace_layout_wheel_preserves_package_path` | atomic | Product State Model | covered |
| 23 | `oracle/test_atomic.py::test_dynamic_metadata_reads_module_docstring_and_version` | atomic | Product State Model | covered |
| 24 | `oracle/test_atomic.py::test_dynamic_build_hooks_need_no_extra_requirements` | atomic | Installable Surface | covered |
| 25 | `oracle/test_atomic.py::test_inline_readme_and_license_file_are_serialized` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_sdist_include_and_exclude_patterns` | atomic | Product State Model | covered |
| 27 | `oracle/test_atomic.py::test_wheel_normalizes_non_executable_permissions` | atomic | Product State Model | covered |
| 28 | `oracle/test_atomic.py::test_wheel_normalizes_executable_permissions` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_buildapi_wheel_is_a_valid_zip_archive` | atomic | Installable Surface | covered |
| 30 | `oracle/test_atomic.py::test_buildapi_sdist_is_a_valid_tar_archive` | atomic | Installable Surface | covered |
| 31 | `oracle/test_integration.py::test_wheel_metadata_matches_prepared_metadata` | integration | Cross-View Invariants | covered |
| 32 | `oracle/test_integration.py::test_wheel_metadata_matches_sdist_pkg_info` | integration | Cross-View Invariants | covered |
| 33 | `oracle/test_integration.py::test_wheel_record_covers_license_and_external_data` | integration | Cross-View Invariants | covered |
| 34 | `oracle/test_integration.py::test_wheel_record_reconstructs_package_file_projection` | integration | Cross-View Invariants | covered |
| 35 | `oracle/test_integration.py::test_regular_and_editable_wheels_project_two_install_modes` | integration | Cross-View Invariants | covered |
| 36 | `oracle/test_integration.py::test_sdist_can_feed_a_second_backend_wheel` | integration | Representative Workflow | covered |
| 37 | `oracle/test_integration.py::test_sdist_roundtrip_preserves_package_file_bytes` | integration | Representative Workflow | covered |
| 38 | `oracle/test_integration.py::test_build_wheel_accepts_prepared_metadata_directory` | integration | Cross-View Invariants | covered |
| 39 | `oracle/test_integration.py::test_editable_prepared_metadata_matches_built_editable_wheel` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_cli_wheel_only_matches_backend_projection` | integration | Representative Workflow | covered |
| 41 | `oracle/test_integration.py::test_cli_sdist_only_matches_backend_projection` | integration | Representative Workflow | covered |
| 42 | `oracle/test_integration.py::test_cli_default_build_produces_both_projections` | integration | Representative Workflow | covered |
| 43 | `oracle/test_integration.py::test_cli_help_exposes_build_and_publish_commands` | integration | Representative Workflow | covered |
| 44 | `oracle/test_integration.py::test_cli_version_reports_public_version` | integration | Representative Workflow | covered |
| 45 | `oracle/test_integration.py::test_src_layout_sdist_and_wheel_share_distribution_identity` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_namespace_metadata_and_archive_path_agree` | integration | Cross-View Invariants | covered |
| 47 | `oracle/test_integration.py::test_dynamic_metadata_agrees_across_wheel_and_sdist` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_dynamic_project_wheel_is_reproducible` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_static_project_wheel_is_reproducible` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_static_project_sdist_is_reproducible` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_license_file_projection_agrees_across_wheel_and_sdist` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_inline_readme_projection_agrees_in_metadata_and_pkg_info` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_external_data_projection_agrees_in_wheel_and_sdist` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_sdist_rules_keep_only_configured_documentation` | integration | Product State Model | covered |
| 55 | `oracle/test_integration.py::test_entry_points_match_prepared_and_built_metadata` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_record_digest_cross_view_matches_license_content` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_all_backend_outputs_share_normalized_distribution_name` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_both_archive_projections_exclude_bytecode_cache` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_cli_wheel_only_leaves_no_sdist` | integration | Representative Workflow | covered |
| 60 | `oracle/test_integration.py::test_cli_sdist_only_leaves_no_wheel` | integration | Representative Workflow | covered |

final_scoreable: 60
