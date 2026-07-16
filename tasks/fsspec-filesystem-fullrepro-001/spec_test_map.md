# Spec Test Map

oracle_version: generated_only_20260704_filterfix1
oracle_source: generated_only
scorer_isolation: score_pytest_original.py --remove-path fsspec
fairness_revision: internal memory resets, private helper calls, cache_size assertion, and root-inclusion find assertion removed

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/generated_tests.py::test_top_level_public_exports_and_protocols | generated | atomic | section Installable Surface | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_filesystem_factory_returns_expected_builtin_classes | generated | atomic | section Public API | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_register_custom_filesystem_and_clobber_behavior | generated | atomic | section Public API | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_unknown_protocol_raises_value_error | generated | atomic | section Error Semantics | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_write_read_info_and_listing_views_agree | generated | system_e2e | section Cross-View Invariants | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_global_store_shared_between_instances | generated | integration | section Memory and Local Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_path_protocol_stripping_and_url_to_fs | generated | integration | section URL and OpenFile Behavior | covered | Public url_to_fs and fsspec.open behavior only; private protocol stripping assertion removed. |
| filter/generated_tests.py::test_memory_text_helpers_round_trip_unicode | generated | atomic | section Memory and Local Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_mkdir_parent_and_error_semantics | generated | integration | section Error Semantics | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_cat_file_slicing_and_missing_error | generated | atomic | section Error Semantics | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_pipe_multiple_and_cat_multiple | generated | atomic | section Memory and Local Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_touch_and_rm_update_all_views | generated | system_e2e | section Cross-View Invariants | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_find_walk_and_du_nested_tree | generated | integration | section Tree Operations | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_walk_topdown_can_prune_directories | generated | atomic | section Tree Operations | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_walk_error_modes | generated | atomic | section Tree Operations | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_copy_move_and_aliases | generated | integration | section Public API | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_recursive_get_put_round_trip | generated | system_e2e | section Tree Operations | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_local_auto_mkdir_and_recursive_remove | generated | integration | section Memory and Local Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_local_copy_move_touch_and_listing | generated | integration | section Memory and Local Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_openfile_is_lazy_context_manager | generated | atomic | section URL and OpenFile Behavior | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_open_text_mode_and_compression | generated | integration | section URL and OpenFile Behavior | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_open_files_read_glob_and_write_expansion | generated | integration | section URL and OpenFile Behavior | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_open_files_write_rejects_multiple_stars | generated | atomic | section Error Semantics | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_get_fs_token_paths_list_and_protocol_mismatch | generated | atomic | section Public API | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_fsmap_basic_mutation_reflects_underlying_memory_fs | generated | system_e2e | section FSMap Mapping View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_get_mapper_memory_and_pickle_round_trip | generated | integration | section FSMap Mapping View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_fsmap_getitems_error_modes | generated | atomic | section FSMap Mapping View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_fsmap_pop_clear_len_keys_items_and_defaults | generated | atomic | section FSMap Mapping View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_fsmap_value_conversion_for_buffer_protocol | generated | atomic | section FSMap Mapping View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_fsmap_local_leading_slash_key_equivalence | generated | atomic | section FSMap Mapping View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_fsmap_memory_leading_slash_key_distinction | generated | atomic | section FSMap Mapping View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_dirfs_relative_view_reads_and_writes_under_root | generated | system_e2e | section DirFileSystem Prefix View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_dirfs_listing_detail_and_cat_list_are_relative | generated | integration | section DirFileSystem Prefix View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_dirfs_find_walk_glob_and_du_translate_paths | generated | integration | section DirFileSystem Prefix View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_dirfs_local_rejects_paths_escaping_root | generated | atomic | section Error Semantics | covered | Exercises local root escape rejection through public exists, pipe, and cat operations. |
| filter/generated_tests.py::test_dirfs_non_local_keeps_dotdot_literal | generated | atomic | section DirFileSystem Prefix View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_url_to_fs_dir_chain_memory_relative_view | generated | system_e2e | section DirFileSystem Prefix View | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_zip_write_close_and_read_members | generated | system_e2e | section Zip Filesystem | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_zip_find_withdirs_maxdepth_and_exact_file | generated | integration | section Zip Filesystem | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_zip_chained_open_reads_archive_member | generated | system_e2e | section URL and OpenFile Behavior | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_zip_missing_member_and_invalid_mode_errors | generated | atomic | section Error Semantics | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_simplecache_chained_read_populates_local_cache | generated | system_e2e | section Cache Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_open_local_simplecache_returns_cached_local_path | generated | integration | section Cache Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_simplecache_write_uploads_to_target_on_close | generated | integration | section Cache Filesystems | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_simplecache_transaction_defers_target_visibility | generated | system_e2e | section Transactions | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_simplecache_transaction_rollback_discards_target_write | generated | system_e2e | section Transactions | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_wholefilecache_cat_populates_same_name_cache | generated | integration | section Cache Filesystems | covered | Checks whole-file cache read behavior and same-name cached bytes; cache_size assertion removed. |
| filter/generated_tests.py::test_memory_transaction_commit_updates_all_views | generated | system_e2e | section Transactions | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_memory_transaction_exception_rolls_back_all_writes | generated | system_e2e | section Transactions | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_remove_file_updates_mapper_and_listing_views | generated | system_e2e | section Cross-View Invariants | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_cross_view_url_token_open_and_mapper_agree | generated | system_e2e | section Cross-View Invariants | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_copy_between_dirfs_view_and_base_memory_view | generated | system_e2e | section Cross-View Invariants | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_zip_member_written_then_opened_through_top_level_helper | generated | system_e2e | section Cross-View Invariants | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_cache_read_matches_target_and_open_local_path | generated | system_e2e | section Cross-View Invariants | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_find_exact_file_and_withdirs_child_behavior | generated | atomic | section Tree Operations | covered | Checks exact-file find and withdirs child inclusion without requiring the queried root itself. |
| filter/generated_tests.py::test_du_and_find_maxdepth_reject_zero | generated | atomic | section Error Semantics | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_openfile_pickle_reopens_read_location | generated | atomic | section URL and OpenFile Behavior | covered | Public generated verifier row mapped during Stage 3. |
| filter/generated_tests.py::test_open_files_context_closes_all_files | generated | integration | section URL and OpenFile Behavior | covered | Public generated verifier row mapped during Stage 3. |

Total: 58 | kept (covered): 58 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 58
