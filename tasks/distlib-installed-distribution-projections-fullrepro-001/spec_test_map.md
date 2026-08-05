# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_distinfo_dirname_normalizes_project_dash` | atomic | Installed Distribution Behavior | covered |
| 2 | `oracle/test_atomic.py::test_distribution_path_discovers_installed_distribution` | atomic | Installed Distribution Behavior | covered |
| 3 | `oracle/test_atomic.py::test_get_distribution_is_case_insensitive` | atomic | Installed Distribution Behavior | covered |
| 4 | `oracle/test_atomic.py::test_installed_distribution_string_uses_name_and_version` | atomic | Installed Distribution Behavior | covered |
| 5 | `oracle/test_atomic.py::test_requested_file_sets_requested_flag` | atomic | Installed Distribution Behavior | covered |
| 6 | `oracle/test_atomic.py::test_list_installed_files_reads_record_rows` | atomic | Installed Distribution Behavior | covered |
| 7 | `oracle/test_atomic.py::test_check_installed_files_accepts_matching_hashes_and_sizes` | atomic | Installed Distribution Behavior | covered |
| 8 | `oracle/test_atomic.py::test_list_distinfo_files_filters_record_to_metadata_directory` | atomic | Installed Distribution Behavior | covered |
| 9 | `oracle/test_atomic.py::test_get_distinfo_file_returns_file_under_distribution_metadata` | atomic | Installed Distribution Behavior | covered |
| 10 | `oracle/test_atomic.py::test_get_distinfo_resource_reads_metadata_bytes` | atomic | Installed Distribution Behavior | covered |
| 11 | `oracle/test_atomic.py::test_get_resource_path_resolves_resources_csv_entry` | atomic | Installed Distribution Behavior | covered |
| 12 | `oracle/test_atomic.py::test_exports_json_returns_named_export_entries` | atomic | Installed Distribution Behavior | covered |
| 13 | `oracle/test_atomic.py::test_distribution_provides_includes_self_and_metadata_alias` | atomic | Installed Distribution Behavior | covered |
| 14 | `oracle/test_atomic.py::test_distribution_matches_requirement_with_version_constraints` | atomic | Installed Distribution Behavior | covered |
| 15 | `oracle/test_atomic.py::test_distribution_path_provides_distribution_finds_alias` | atomic | Installed Distribution Behavior | covered |
| 16 | `oracle/test_atomic.py::test_metadata_mapping_exposes_common_fields` | atomic | Metadata Projection | covered |
| 17 | `oracle/test_atomic.py::test_metadata_keywords_string_becomes_list` | atomic | Metadata Projection | covered |
| 18 | `oracle/test_atomic.py::test_metadata_get_requirements_filters_extras` | atomic | Metadata Projection | covered |
| 19 | `oracle/test_atomic.py::test_metadata_write_json_round_trips_mapping` | atomic | Metadata Projection | covered |
| 20 | `oracle/test_atomic.py::test_manifest_findall_discovers_local_files` | atomic | Manifest Projection | covered |
| 21 | `oracle/test_atomic.py::test_manifest_include_adds_matching_top_level_file` | atomic | Manifest Projection | covered |
| 22 | `oracle/test_atomic.py::test_manifest_recursive_include_and_exclude_filter_tree` | atomic | Manifest Projection | covered |
| 23 | `oracle/test_atomic.py::test_manifest_graft_and_prune_control_subtrees` | atomic | Manifest Projection | covered |
| 24 | `oracle/test_atomic.py::test_manifest_add_many_and_sorted_can_include_directories` | atomic | Manifest Projection | covered |
| 25 | `oracle/test_atomic.py::test_manifest_clear_removes_file_sets` | atomic | Manifest Projection | covered |
| 26 | `oracle/test_atomic.py::test_resource_finder_identifies_container_and_file` | atomic | Resource Projection | covered |
| 27 | `oracle/test_atomic.py::test_resource_finder_iterator_walks_nested_resources` | atomic | Resource Projection | covered |
| 28 | `oracle/test_atomic.py::test_wheel_filename_and_tags_parse_from_filename` | atomic | Wheel Projection | covered |
| 29 | `oracle/test_atomic.py::test_wheel_process_shebang_normalizes_existing_interpreter` | atomic | Wheel Projection | covered |
| 30 | `oracle/test_atomic.py::test_wheel_get_hash_returns_named_digest` | atomic | Wheel Projection | covered |
| 31 | `oracle/test_integration.py::test_distribution_metadata_agrees_with_serialized_metadata_file` | integration | Cross-View Invariants | covered |
| 32 | `oracle/test_integration.py::test_record_rows_distinfo_files_and_integrity_check_share_same_distribution` | integration | Cross-View Invariants | covered |
| 33 | `oracle/test_integration.py::test_resource_csv_path_and_resource_finder_read_same_bytes` | integration | Resource Projection | covered |
| 34 | `oracle/test_integration.py::test_distribution_exports_match_environment_export_lookup` | integration | Cross-View Invariants | covered |
| 35 | `oracle/test_integration.py::test_provides_distribution_and_requirement_matching_project_same_alias` | integration | Installed Distribution Behavior | covered |
| 36 | `oracle/test_integration.py::test_distribution_cache_clear_keeps_public_lookup_consistent` | integration | Installed Distribution Behavior | covered |
| 37 | `oracle/test_integration.py::test_write_installed_files_rebuilds_record_and_check_uses_new_rows` | integration | Installed Distribution Behavior | covered |
| 38 | `oracle/test_integration.py::test_shared_locations_write_and_property_project_same_paths` | integration | Installed Distribution Behavior | covered |
| 39 | `oracle/test_integration.py::test_json_metadata_can_construct_installed_distribution_projection` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_legacy_metadata_write_round_trips_to_public_dictionary` | integration | Metadata Projection | covered |
| 41 | `oracle/test_integration.py::test_manifest_file_selection_matches_filesystem_projection` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_manifest_sorted_with_dirs_preserves_parent_paths_for_selected_files` | integration | Manifest Projection | covered |
| 43 | `oracle/test_integration.py::test_package_resource_finder_matches_imported_filesystem_package` | integration | Resource Projection | covered |
| 44 | `oracle/test_integration.py::test_zip_package_resource_finder_projects_archive_members` | integration | Resource Projection | covered |
| 45 | `oracle/test_integration.py::test_wheel_info_metadata_and_verify_agree_with_archive_record` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_wheel_mount_exposes_package_resource_and_unmount_removes_path` | integration | Wheel Projection | covered |
| 47 | `oracle/test_integration.py::test_wheel_shebang_and_hash_match_recordable_script_content` | integration | Wheel Projection | covered |
| 48 | `oracle/test_integration.py::test_file_path_resource_and_metadata_resource_share_distribution_context` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_named_and_category_export_lookups_return_same_public_entries` | integration | Installed Distribution Behavior | covered |
| 50 | `oracle/test_integration.py::test_distinfo_resource_stream_can_feed_metadata_reader` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_installed_file_integrity_detects_changed_file_through_record_projection` | integration | Error Semantics | covered |
| 52 | `oracle/test_integration.py::test_manifest_over_installed_tree_contains_distribution_record_files` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_distribution_run_requires_projects_legacy_metadata_requirements` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_wheel_metadata_can_be_used_as_installed_distribution_metadata` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_manifest_selected_files_can_be_read_through_resource_finder` | integration | Resource Projection | covered |
| 56 | `oracle/test_integration.py::test_metadata_json_written_into_wheel_archive_round_trips_with_wheel_reader` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_distribution_path_get_distribution_and_provides_distribution_share_object` | integration | Installed Distribution Behavior | covered |
| 58 | `oracle/test_integration.py::test_shared_locations_file_resource_and_property_agree_after_write` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_zip_package_resource_stream_size_and_iterator_agree` | integration | Resource Projection | covered |
| 60 | `oracle/test_integration.py::test_json_wheel_metadata_can_seed_installed_distribution_requirements` | integration | Cross-View Invariants | covered |

final_scoreable: 60
