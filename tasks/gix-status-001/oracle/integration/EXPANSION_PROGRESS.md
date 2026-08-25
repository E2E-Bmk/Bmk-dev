# gix-status-001 Integration Test Expansion Progress

Target: 25 integration tests (currently 10, need +15)

## Atomic tests available for DependsOn

1. a_clean_tracked_file_produces_no_status
2. changed_content_is_reported_as_a_modification
3. a_content_comparison_that_reads_the_file_counts_its_bytes
4. fast_eq_reports_a_size_difference_without_reading_the_file
5. a_missing_worktree_file_is_reported_as_removed
6. a_directory_in_place_of_a_file_is_reported_as_removed
7. a_path_reached_through_a_symlink_is_reported_as_removed
8. a_symlink_in_place_of_a_file_is_reported_as_a_type_change
9. a_skip_worktree_entry_is_never_visited
10. an_intent_to_add_entry_is_reported_without_a_content_comparison
11. identical_content_behind_a_stale_stat_asks_for_an_index_update
12. a_flipped_executable_bit_is_a_modification_without_a_content_change
13. a_racy_entry_whose_content_changed_is_reported_and_counted
14. a_fresh_index_timestamp_makes_the_same_entry_clean
15. an_interrupt_stops_the_walk_without_making_it_an_error
16. a_pathspec_prefix_skips_entries_before_the_pathspec_is_consulted
17. an_exclude_pathspec_skips_an_entry_the_prefix_admitted
18. pathspecs_without_a_common_prefix_skip_nothing_by_prefix
19. skipped_sums_the_three_skip_counters
20. a_base_stage_on_its_own_is_both_deleted
21. an_ours_stage_on_its_own_is_added_by_us
22. a_base_and_an_ours_stage_are_deleted_by_them
23. a_theirs_stage_on_its_own_is_added_by_them
24. a_base_and_a_theirs_stage_are_deleted_by_us
25. an_ours_and_a_theirs_stage_are_both_added
26. all_three_stages_are_both_modified
27. a_conflict_carries_the_index_entry_of_every_stage_present
28. try_from_entry_summarizes_the_stages_it_consumes
29. try_from_entry_declines_an_unconflicted_entry
30. a_multi_stage_conflict_counts_as_one_processed_entry
31. hash_eq_reports_the_object_id_of_the_worktree_content
32. a_submodule_entry_is_delegated_and_its_answer_is_reported
33. a_submodule_delegate_that_reports_nothing_produces_no_status
34. verified_path_returns_the_absolute_path_of_an_existing_file
35. verified_path_refuses_to_step_through_a_symlink
36. verified_path_reports_a_missing_path_as_not_found
37. verified_path_allow_nonexisting_accepts_a_path_that_does_not_exist
38. verified_path_allow_nonexisting_still_refuses_a_symlinked_component
39. symlink_check_exposes_the_working_tree_root

## Existing 10 integration tests

1. a_mixed_index_reports_every_entry_once_and_accounts_for_all_of_them
2. the_thread_limit_never_changes_what_is_reported
3. a_conflict_does_not_disturb_the_entries_around_it
4. applying_every_needs_update_stat_makes_the_next_run_silent
5. zeroing_the_recorded_size_keeps_a_racy_modification_visible
6. a_pathspec_changes_which_entries_are_seen_and_not_what_is_said_about_them
7. a_run_leaves_the_working_tree_the_index_and_the_database_alone
8. without_a_dirwalk_or_rewrites_the_renames_entry_point_is_the_plain_scan
9. a_directory_walk_adds_untracked_files_to_the_tracked_report
10. rewrite_tracking_replaces_a_removal_and_an_addition_with_one_rename

## 15 new tests to write

### Batch 1 (tests 11-15): cross-entry in one run

- [x] 11. an_all_clean_index_produces_an_empty_report_and_zero_updates
  - DependsOn: a_clean_tracked_file_produces_no_status
  - INV-2: multiple clean entries → empty records, entries_to_update=0
- [x] 12. stat_accurate_entries_are_never_read_from_disk
  - DependsOn: a_content_comparison_that_reads_the_file_counts_its_bytes
  - INV-3: worktree_files_read=0 when all stat data is accurate
- [x] 13. multiple_conflict_shapes_coexist_in_one_run
  - DependsOn: all_three_stages_are_both_modified
  - DependsOn: a_base_stage_on_its_own_is_both_deleted
  - Multiple conflict types in one index, each gets correct summary
- [x] 14. hash_eq_reports_every_changed_file_in_one_pass
  - DependsOn: hash_eq_reports_the_object_id_of_the_worktree_content
  - Multiple files with HashEq, all get correct OIDs
- [x] 15. a_submodule_and_a_file_change_are_reported_independently
  - DependsOn: a_submodule_entry_is_delegated_and_its_answer_is_reported
  - DependsOn: changed_content_is_reported_as_a_modification
  - Both appear in same run without interference

ALL BATCH 1 WRITTEN TO integration/src/lib.rs

### Batch 2 (tests 16-20): two-run comparisons and invariants

- [x] 16. a_delegate_switch_changes_the_output_type_but_not_which_paths_are_seen
  - DependsOn: hash_eq_reports_the_object_id_of_the_worktree_content
  - DependsOn: changed_content_is_reported_as_a_modification
  - Same fixture, FastEq vs HashEq: same paths, different T
- [x] 17. an_executable_bit_change_and_a_content_change_are_independent_axes
  - DependsOn: a_flipped_executable_bit_is_a_modification_without_a_content_change
  - DependsOn: changed_content_is_reported_as_a_modification
  - Three entries: bit-only, content-only, both — independent axes
- [x] 18. racy_clean_count_matches_the_number_of_entries_that_were_racy
  - DependsOn: a_racy_entry_whose_content_changed_is_reported_and_counted
  - Multiple racy entries, racy_clean matches exactly
- [x] 19. an_intent_to_add_entry_has_its_own_summary_in_the_renames_report
  - DependsOn: an_intent_to_add_entry_is_reported_without_a_content_comparison
  - IntentToAdd → Summary::IntentToAdd in renames
- [x] 20. a_type_change_in_the_renames_report_carries_the_type_change_summary
  - DependsOn: a_symlink_in_place_of_a_file_is_reported_as_a_type_change
  - Type change → Summary::TypeChange in renames

### Batch 3 (tests 21-25): renames composition and sorting

- [ ] 21. sorting_by_path_orders_mixed_tracked_and_untracked_entries
  - DependsOn: a_missing_worktree_file_is_reported_as_removed
  - With sorting, all entries interleave by path
- [ ] 22. without_sorting_the_tracked_report_precedes_the_walk_report
  - DependsOn: a_clean_tracked_file_produces_no_status
  - Without sorting, tracked modifications come before dirwalk entries
- [ ] 23. a_needs_update_entry_has_no_summary_in_the_renames_report
  - DependsOn: identical_content_behind_a_stale_stat_asks_for_an_index_update
  - NeedsUpdate → summary() returns None per spec
- [ ] 24. a_conflict_in_the_renames_report_carries_the_conflict_summary
  - DependsOn: all_three_stages_are_both_modified
  - Conflict in renames → Summary::Conflict
- [ ] 25. the_dirwalk_outcome_reports_its_own_counts_beside_the_tracked_outcome
  - DependsOn: a_clean_tracked_file_produces_no_status
  - Dirwalk outcome is populated with its own counters
