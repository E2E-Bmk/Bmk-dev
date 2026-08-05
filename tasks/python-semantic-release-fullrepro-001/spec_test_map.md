# Specification Test Map

Each physical test function below maps to one public contract row. The final
scoreable inventory is the union of the two canonical test modules.

| # | Node ID | Layer | Contract area | Status |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_package_reports_documented_distribution_version` | atomic | Public Import Surface | covered |
| 2 | `oracle/test_atomic.py::test_public_version_parse_preserves_number_text` | atomic | Public Import Surface | covered |
| 3 | `oracle/test_atomic.py::test_public_version_parse_preserves_prerelease_text` | atomic | Public Import Surface | covered |
| 4 | `oracle/test_atomic.py::test_public_version_parse_preserves_build_metadata_text` | atomic | Public Import Surface | covered |
| 5 | `oracle/test_atomic.py::test_public_level_bump_exports_semantic_names` | atomic | Public Import Surface | covered |
| 6 | `oracle/test_atomic.py::test_generate_config_toml_uses_plain_semantic_release_root` | atomic | Configuration | covered |
| 7 | `oracle/test_atomic.py::test_generate_config_pyproject_uses_tool_root` | atomic | Configuration | covered |
| 8 | `oracle/test_atomic.py::test_generate_config_json_uses_top_level_semantic_release_key` | atomic | Configuration | covered |
| 9 | `oracle/test_atomic.py::test_main_help_lists_release_commands` | atomic | Invocation Protocol | covered |
| 10 | `oracle/test_atomic.py::test_version_help_lists_print_and_local_side_effect_toggles` | atomic | Invocation Protocol | covered |
| 11 | `oracle/test_atomic.py::test_last_released_version_prints_plain_version` | atomic | Release History | covered |
| 12 | `oracle/test_atomic.py::test_last_released_tag_prints_configured_tag` | atomic | Release History | covered |
| 13 | `oracle/test_atomic.py::test_custom_tag_format_selects_matching_release_tag` | atomic | Release History | covered |
| 14 | `oracle/test_atomic.py::test_fix_commit_projects_patch_release` | atomic | Commit Parsing And Bumps | covered |
| 15 | `oracle/test_atomic.py::test_feat_commit_projects_minor_release` | atomic | Commit Parsing And Bumps | covered |
| 16 | `oracle/test_atomic.py::test_breaking_change_footer_projects_major_release` | atomic | Commit Parsing And Bumps | covered |
| 17 | `oracle/test_atomic.py::test_docs_commit_does_not_force_release` | atomic | Commit Parsing And Bumps | covered |
| 18 | `oracle/test_atomic.py::test_unknown_commit_does_not_force_release` | atomic | Commit Parsing And Bumps | covered |
| 19 | `oracle/test_atomic.py::test_forced_major_overrides_patch_history` | atomic | Version Options | covered |
| 20 | `oracle/test_atomic.py::test_forced_minor_overrides_patch_history` | atomic | Version Options | covered |
| 21 | `oracle/test_atomic.py::test_forced_patch_overrides_no_release_history` | atomic | Version Options | covered |
| 22 | `oracle/test_atomic.py::test_build_metadata_is_appended_to_printed_version` | atomic | Version Options | covered |
| 23 | `oracle/test_atomic.py::test_print_tag_uses_custom_tag_format` | atomic | Version Options | covered |
| 24 | `oracle/test_atomic.py::test_json_configuration_file_is_accepted` | atomic | Configuration | covered |
| 25 | `oracle/test_atomic.py::test_noop_version_does_not_update_project_file` | atomic | No-op Mode | covered |
| 26 | `oracle/test_atomic.py::test_no_commit_no_tag_updates_version_without_git_tag` | atomic | Local Projections | covered |
| 27 | `oracle/test_atomic.py::test_no_changelog_keeps_existing_changelog_body` | atomic | Local Projections | covered |
| 28 | `oracle/test_atomic.py::test_allow_zero_version_keeps_minor_bump_under_zero_major` | atomic | Version Options | covered |
| 29 | `oracle/test_atomic.py::test_prerelease_print_uses_configured_token` | atomic | Version Options | covered |
| 30 | `oracle/test_atomic.py::test_prerelease_token_option_overrides_branch_token` | atomic | Version Options | covered |
| 31 | `oracle/test_integration.py::test_release_command_updates_project_version_changelog_commit_and_tag` | integration | Release Workflow | covered |
| 32 | `oracle/test_integration.py::test_release_commit_includes_version_variable_file_replacements` | integration | Version Variables | covered |
| 33 | `oracle/test_integration.py::test_changelog_groups_feature_and_fix_sections_from_same_history` | integration | Changelog Projection | covered |
| 34 | `oracle/test_integration.py::test_breaking_change_section_is_rendered_for_major_release` | integration | Changelog Projection | covered |
| 35 | `oracle/test_integration.py::test_print_projection_and_release_side_effect_agree` | integration | Cross-View Invariants | covered |
| 36 | `oracle/test_integration.py::test_print_tag_projection_and_git_tag_agree_for_custom_format` | integration | Cross-View Invariants | covered |
| 37 | `oracle/test_integration.py::test_last_released_projection_moves_after_local_release` | integration | Release History | covered |
| 38 | `oracle/test_integration.py::test_no_commit_workflow_stamps_files_without_release_commit` | integration | Local Projections | covered |
| 39 | `oracle/test_integration.py::test_no_tag_workflow_creates_release_commit_without_new_tag` | integration | Local Projections | covered |
| 40 | `oracle/test_integration.py::test_no_changelog_release_updates_version_and_tag_only` | integration | Local Projections | covered |
| 41 | `oracle/test_integration.py::test_noop_workflow_preserves_files_tags_and_head` | integration | No-op Mode | covered |
| 42 | `oracle/test_integration.py::test_version_toml_and_version_variable_views_stay_in_sync` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_json_config_release_updates_toml_project_file` | integration | Configuration | covered |
| 44 | `oracle/test_integration.py::test_changelog_command_renders_history_without_version_command` | integration | Changelog Projection | covered |
| 45 | `oracle/test_integration.py::test_changelog_noop_leaves_existing_changelog_unchanged` | integration | No-op Mode | covered |
| 46 | `oracle/test_integration.py::test_prerelease_release_creates_prerelease_tag_and_version` | integration | Release Workflow | covered |
| 47 | `oracle/test_integration.py::test_build_metadata_release_stamps_metadata_in_tag_and_project` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_release_commit_message_template_uses_new_version` | integration | Release Workflow | covered |
| 49 | `oracle/test_integration.py::test_release_history_ignores_unmatched_tag_format` | integration | Release History | covered |
| 50 | `oracle/test_integration.py::test_release_history_uses_highest_matching_semver_tag` | integration | Release History | covered |
| 51 | `oracle/test_integration.py::test_multiple_patch_commits_roll_up_to_one_patch_release` | integration | Commit Parsing And Bumps | covered |
| 52 | `oracle/test_integration.py::test_minor_release_wins_over_patch_commits` | integration | Commit Parsing And Bumps | covered |
| 53 | `oracle/test_integration.py::test_major_release_wins_over_minor_and_patch_commits` | integration | Commit Parsing And Bumps | covered |
| 54 | `oracle/test_integration.py::test_docs_only_workflow_makes_no_release_side_effects` | integration | Error Semantics | covered |
| 55 | `oracle/test_integration.py::test_end_to_end_local_release_views_agree` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_perf_commit_projects_patch_release` | integration | Commit Parsing And Bumps | covered |
| 57 | `oracle/test_integration.py::test_scope_and_pull_request_are_rendered_in_release_history` | integration | Changelog Projection | covered |
| 58 | `oracle/test_integration.py::test_release_notice_is_rendered_in_additional_information` | integration | Changelog Projection | covered |
| 59 | `oracle/test_integration.py::test_exclude_commit_pattern_removes_matching_history_from_changelog` | integration | Changelog Projection | covered |
| 60 | `oracle/test_integration.py::test_update_mode_preserves_manual_changelog_history` | integration | Changelog Projection | covered |
| 61 | `oracle/test_integration.py::test_prerelease_print_increments_existing_same_version_prerelease` | integration | Release History | covered |
| 62 | `oracle/test_integration.py::test_default_bump_level_changes_allowed_chore_commit` | integration | Commit Parsing And Bumps | covered |
| 63 | `oracle/test_integration.py::test_squashed_conventional_messages_use_highest_bump` | integration | Commit Parsing And Bumps | covered |
| 64 | `oracle/test_integration.py::test_strict_mode_rejects_a_history_with_no_release` | integration | Error Semantics | covered |
| 65 | `oracle/test_integration.py::test_strict_mode_rejects_a_non_release_branch` | integration | Error Semantics | covered |

final_scoreable: 65
