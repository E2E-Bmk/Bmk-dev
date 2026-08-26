# Specification coverage map — ignore-fullrepro-001

oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
three rounds, plus full suite runs on both the patched path and the
registry lock; upstream tests served as a behavioral checklist only — see
rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::generated_gitignore_absolute_path_stripped_to_relative` | atomic | ## Ignore Pattern Matching | covered | absolute path under root stripped |
| `atomic::generated_gitignore_add_unreadable_file_reports_error` | atomic | ## Error Semantics | covered | add unreadable file Some(Error) is_io + sibling |
| `atomic::generated_gitignore_case_insensitive_applies_to_later_lines` | atomic | ## Ignore Pattern Matching | covered | case_insensitive affects patterns added afterward |
| `atomic::generated_gitignore_comments_and_blanks_add_nothing` | atomic | ## Ignore Pattern Matching | covered | comments/blank lines add no patterns |
| `atomic::generated_gitignore_counters_and_root_path` | atomic | ## Ignore Pattern Matching | covered | num_ignores/num_whitelists/len/is_empty/path |
| `atomic::generated_gitignore_double_star_middle_spans_components` | atomic | ## Ignore Pattern Matching | covered | a/**/b spans zero or more components |
| `atomic::generated_gitignore_double_star_prefix_all_depths` | atomic | ## Ignore Pattern Matching | covered | **/name matches every depth including root |
| `atomic::generated_gitignore_empty_matcher_answers_none` | atomic | ## Ignore Pattern Matching | covered | Gitignore::empty answers None everywhere |
| `atomic::generated_gitignore_escaped_hash_matches_literal` | atomic | ## Ignore Pattern Matching | covered | \# escapes the comment marker |
| `atomic::generated_gitignore_glob_provenance_fields` | atomic | ## Ignore Pattern Matching | covered | Glob original/from/is_whitelist/is_only_dir |
| `atomic::generated_gitignore_ignore_after_whitelist_wins` | atomic | ## Ignore Pattern Matching | covered | later ignore beats earlier whitelist |
| `atomic::generated_gitignore_invalid_glob_line_is_error` | atomic | ## Error Semantics | covered | invalid glob Err + builder usable sibling |
| `atomic::generated_gitignore_mid_slash_anchors_and_star_stays_in_component` | atomic | ## Ignore Pattern Matching | covered | mid slash anchors; * stays inside a component |
| `atomic::generated_gitignore_name_pattern_matches_any_depth` | atomic | ## Ignore Pattern Matching | covered | no-slash pattern matches final component at any depth |
| `atomic::generated_gitignore_negation_last_match_wins` | atomic | ## Ignore Pattern Matching | covered | later whitelist beats earlier ignore |
| `atomic::generated_gitignore_new_reads_file_and_roots_at_parent` | atomic | ## Ignore Pattern Matching | covered | Gitignore::new roots at file parent |
| `atomic::generated_gitignore_parent_dir_rule_hits_descendants` | atomic | ## Ignore Pattern Matching | covered | matched_path_or_any_parents sees ancestor dir rules |
| `atomic::generated_gitignore_partial_error_for_multiple_bad_lines` | atomic | ## Error Semantics | covered | is_partial aggregates several bad globs |
| `atomic::generated_gitignore_slash_prefix_anchors_to_root` | atomic | ## Ignore Pattern Matching | covered | leading / anchors to matcher root |
| `atomic::generated_gitignore_trailing_slash_directory_only` | atomic | ## Ignore Pattern Matching | covered | trailing / restricts to directories via is_dir |
| `atomic::generated_gitignore_trailing_space_trimmed_unless_escaped` | atomic | ## Ignore Pattern Matching | covered | trailing whitespace trimmed unless backslash-escaped |
| `atomic::generated_match_inner_payload` | atomic | ## Ignore Pattern Matching | covered | inner returns Some(payload) unless None |
| `atomic::generated_match_invert_swaps` | atomic | ## Ignore Pattern Matching | covered | invert swaps Ignore and Whitelist |
| `atomic::generated_match_map_transforms_payload` | atomic | ## Ignore Pattern Matching | covered | map transforms the payload, None unchanged |
| `atomic::generated_match_or_prefers_receiver` | atomic | ## Ignore Pattern Matching | covered | or returns receiver unless it is None |
| `atomic::generated_match_variant_predicates` | atomic | ## Ignore Pattern Matching | covered | is_none/is_ignore/is_whitelist across all three variants |
| `atomic::generated_override_case_insensitive_toggle` | atomic | ## Override Globs | covered | case-insensitive override globs |
| `atomic::generated_override_counters_inverted_and_invalid_glob` | atomic | ## Override Globs | covered | inverted counters + invalid glob Err |
| `atomic::generated_override_empty_answers_none` | atomic | ## Override Globs | covered | empty override matches nothing |
| `atomic::generated_override_negated_glob_ignores` | atomic | ## Override Globs | covered | ! glob ignores matching file |
| `atomic::generated_override_only_negations_leave_unmatched_none` | atomic | ## Override Globs | covered | no blanket rule without plain globs |
| `atomic::generated_override_plain_glob_whitelists_match` | atomic | ## Override Globs | covered | plain glob whitelists matching file |
| `atomic::generated_override_unmatched_directory_none` | atomic | ## Override Globs | covered | directories stay undecided |
| `atomic::generated_override_unmatched_file_ignored_when_plain_glob_exists` | atomic | ## Override Globs | covered | blanket ignore for unmatched files |
| `atomic::generated_parallel_delivers_full_entry_set` | atomic | ## Parallel Walking | covered | parallel run delivers the full set |
| `atomic::generated_parallel_quit_stops_early` | atomic | ## Parallel Walking | covered | WalkState::Quit cuts the walk short |
| `atomic::generated_parallel_skip_prevents_descent` | atomic | ## Parallel Walking | covered | WalkState::Skip stops descent |
| `atomic::generated_types_accumulate_globs_and_sorted_definitions` | atomic | ## File Type Filters | covered | repeated add accumulates; definitions sorted |
| `atomic::generated_types_add_def_include_composite` | atomic | ## File Type Filters | covered | include composite inherits member globs |
| `atomic::generated_types_add_def_malformed_strings_error` | atomic | ## Error Semantics | covered | segment-count/middle/empty/include validation |
| `atomic::generated_types_add_def_name_colon_glob` | atomic | ## File Type Filters | covered | two-segment name:glob format |
| `atomic::generated_types_build_unknown_name_errors` | atomic | ## Error Semantics | covered | unknown selection fails build; Types::empty |
| `atomic::generated_types_glob_payload_names_owning_definition` | atomic | ## File Type Filters | covered | file_type_def provenance; blanket has none |
| `atomic::generated_types_name_validation_rules` | atomic | ## Error Semantics | covered | alphanumeric-only names, all reserved |
| `atomic::generated_types_negate_produces_ignore` | atomic | ## File Type Filters | covered | negated type glob ignores |
| `atomic::generated_types_no_selection_matches_none` | atomic | ## File Type Filters | covered | no selections answers None |
| `atomic::generated_types_only_negations_leave_unmatched_none` | atomic | ## File Type Filters | covered | negations alone leave unmatched at None |
| `atomic::generated_types_select_all_and_clear` | atomic | ## File Type Filters | covered | select all; clear removes the definition |
| `atomic::generated_types_selected_matching_whitelist_unmatched_ignore` | atomic | ## File Type Filters | covered | select whitelist + blanket ignore + dir None |
| `atomic::generated_walk_add_ignore_applies_to_whole_walk` | atomic | ## Directory Walking | covered | add_ignore file applies to whole walk |
| `atomic::generated_walk_add_ignore_unreadable_reports_error` | atomic | ## Error Semantics | covered | add_ignore unreadable Some(Error) + walk sibling |
| `atomic::generated_walk_custom_ignore_filename_rules_apply` | atomic | ## Directory Walking | covered | custom ignore filename read per directory |
| `atomic::generated_walk_default_constructor_equivalent` | atomic | ## Directory Walking | covered | Walk::new equals default WalkBuilder |
| `atomic::generated_walk_direntry_accessors_agree` | atomic | ## Directory Walking | covered | path/file_name/depth/file_type/metadata/into_path |
| `atomic::generated_walk_dot_ignore_applies_without_git` | atomic | ## Directory Walking | covered | .ignore needs no repo |
| `atomic::generated_walk_file_root_yields_exactly_that_file` | atomic | ## Directory Walking | covered | file root yields the file itself |
| `atomic::generated_walk_filter_entry_prunes_directory` | atomic | ## Directory Walking | covered | predicate false prunes the subtree |
| `atomic::generated_walk_git_exclude_applies_and_toggles` | atomic | ## Directory Walking | covered | .git/info/exclude applies; toggle disables |
| `atomic::generated_walk_git_ignore_toggle_disables` | atomic | ## Directory Walking | covered | git_ignore(false) disables .gitignore |
| `atomic::generated_walk_gitignore_applies_inside_repo` | atomic | ## Directory Walking | covered | .gitignore rules apply inside a repo |
| `atomic::generated_walk_gitignore_needs_repo_by_default` | atomic | ## Directory Walking | covered | require_git default gates .gitignore |
| `atomic::generated_walk_hidden_default_skips_dot_entries` | atomic | ## Directory Walking | covered | hidden filter on by default |
| `atomic::generated_walk_hidden_disabled_yields_dot_entries` | atomic | ## Directory Walking | covered | hidden(false) yields dot entries |
| `atomic::generated_walk_ignore_toggle_disables_dot_ignore` | atomic | ## Directory Walking | covered | ignore(false) disables .ignore |
| `atomic::generated_walk_max_depth_limits_yield` | atomic | ## Directory Walking | covered | max_depth cuts deeper entries |
| `atomic::generated_walk_max_filesize_skips_large_files_only` | atomic | ## Directory Walking | covered | size limit skips files, never directories |
| `atomic::generated_walk_multiple_roots_visited_in_order` | atomic | ## Directory Walking | covered | roots visited in the order added |
| `atomic::generated_walk_nonexistent_root_yields_single_io_error` | atomic | ## Error Semantics | covered | single Err item, is_io + io_error |
| `atomic::generated_walk_overrides_restrict_files` | atomic | ## Directory Walking | covered | override installed on a walk |
| `atomic::generated_walk_parents_toggle_stops_upward_discovery` | atomic | ## Directory Walking | covered | parents(false) stops upward rule search |
| `atomic::generated_walk_require_git_false_applies_everywhere` | atomic | ## Directory Walking | covered | require_git(false) lifts the gate |
| `atomic::generated_walk_sort_by_file_name_orders_siblings` | atomic | ## Directory Walking | covered | comparator order on flat tree |
| `atomic::generated_walk_sort_by_file_path_orders_siblings` | atomic | ## Directory Walking | covered | path comparator order on flat tree |
| `atomic::generated_walk_types_restrict_files` | atomic | ## Directory Walking | covered | types installed on a walk |
| `atomic::generated_walk_yields_root_first_at_depth_zero` | atomic | ## Directory Walking | covered | root first, depth 0 |
| `integration::limits_sorting::generated_filter_entry_sees_hidden_when_disabled` | integration | ## Directory Walking | covered | predicate applies to dot entries |
| `integration::limits_sorting::generated_max_depth_is_subset` | integration | ## Cross-View Invariants | covered | CVI 7: depth accounting and depth-limited subset |
| `integration::limits_sorting::generated_max_filesize_with_types` | integration | ## Directory Walking | covered | size limit composes with type filter |
| `integration::limits_sorting::generated_multi_root_depths_reset` | integration | ## Directory Walking | covered | depth counts from each entry's own root |
| `integration::limits_sorting::generated_sorted_multiset_unchanged` | integration | ## Cross-View Invariants | covered | CVI 8: sorting preserves the set, parents first |
| `integration::limits_sorting::generated_standard_filters_equivalence` | integration | ## Cross-View Invariants | covered | CVI 6: bundle == individual toggles |
| `integration::matcher_walk::generated_case_insensitive_matcher_and_walk_agree` | integration | ## Cross-View Invariants | covered | case-insensitive matcher and walk agree |
| `integration::matcher_walk::generated_mpap_equals_ancestor_fold` | integration | ## Cross-View Invariants | covered | CVI 4: ancestor fold equality |
| `integration::matcher_walk::generated_override_inverts_gitignore` | integration | ## Cross-View Invariants | covered | CVI 5: override inverts gitignore + blanket rule |
| `integration::matcher_walk::generated_two_build_routes_agree` | integration | ## Ignore Pattern Matching | covered | file route and line route build equal matchers |
| `integration::matcher_walk::generated_walk_agrees_with_matcher_stack` | integration | ## Cross-View Invariants | covered | CVI 2: walk membership == parent-aware matcher verdicts |
| `integration::override_types::generated_override_and_types_compose` | integration | ## Directory Walking | covered | negation-only override falls through to types |
| `integration::override_types::generated_override_verdict_bypasses_types` | integration | ## Directory Walking | covered | decisive override verdict is final |
| `integration::override_types::generated_override_whitelist_rescues_gitignored_file` | integration | ## Directory Walking | covered | override whitelist rescues gitignored file |
| `integration::override_types::generated_types_ignore_beats_ignore_file_whitelist` | integration | ## Directory Walking | covered | types consulted after ignore-file whitelist |
| `integration::override_types::generated_types_include_composite_on_walk` | integration | ## File Type Filters | covered | include composite drives a walk |
| `integration::override_types::generated_types_negate_on_walk` | integration | ## File Type Filters | covered | select all + negate drives a walk |
| `integration::override_types::generated_walk_matches_override_verdicts` | integration | ## Cross-View Invariants | covered | CVI 3: override walk == matcher verdicts |
| `integration::override_types::generated_walk_matches_types_verdicts` | integration | ## Cross-View Invariants | covered | CVI 3: types walk == matcher verdicts |
| `integration::parallel::generated_parallel_equals_serial_full_config` | integration | ## Cross-View Invariants | covered | CVI 1: parallel set equals serial set |
| `integration::parallel::generated_parallel_quit_delivers_subset` | integration | ## Parallel Walking | covered | Quit delivers a subset containing the trigger |
| `integration::parallel::generated_parallel_sees_rule_stack` | integration | ## Parallel Walking | covered | parallel walk applies the same rule stack |
| `integration::parallel::generated_parallel_skip_equals_serial_filter` | integration | ## Parallel Walking | covered | Skip equals filter_entry modulo the dir entry |
| `integration::parallel::generated_parallel_thread_counts_agree` | integration | ## Cross-View Invariants | covered | CVI 1: thread count never changes the set |
| `integration::precedence::generated_add_ignore_lowest_rank` | integration | ## Directory Walking | covered | .gitignore whitelist beats add_ignore rules |
| `integration::precedence::generated_custom_file_outranks_dotignore` | integration | ## Directory Walking | covered | custom ignore file outranks .ignore |
| `integration::precedence::generated_deeper_file_outranks_shallower` | integration | ## Directory Walking | covered | deeper .gitignore re-includes |
| `integration::precedence::generated_dotignore_whitelist_rescues_gitignored` | integration | ## Directory Walking | covered | .ignore whitelist outranks .gitignore ignore |
| `integration::precedence::generated_last_match_wins_through_walker` | integration | ## Directory Walking | covered | last-match-wins seen through matcher and walk |
| `integration::precedence::generated_override_outranks_all_sources` | integration | ## Directory Walking | covered | override rank beats every ignore file |
| `integration::precedence::generated_whitelist_cannot_rescue_inside_ignored_dir` | integration | ## Directory Walking | covered | matcher Whitelist vs walker non-descent |

Total: 106 | kept (covered): 106 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 106

Layer counts: atomic 75, integration 31.
