# Spec Test Map: pre-commit-hooks-fullrepro-001

Generated-only oracle rebuilt after rescue expansion. All rows are conftest-free generated behavioral tests that pass the reference gate.

| nodeid | source | layer | spec_section | status | rationale |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_hook_types_are_documented_git_hook_types` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_stages_extend_hook_types_with_manual` | generated | atomic | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_legacy_stage_names_are_normalized` | generated | atomic | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_load_manifest_applies_hook_defaults` | generated | integration | ## Hook Manifest | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_load_manifest_normalizes_script_language` | generated | integration | ## Hook Manifest | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_load_config_applies_top_level_defaults` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_load_config_accepts_ci_mapping_without_changing_local_hooks` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_load_config_normalizes_local_hook_defaults` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_load_config_preserves_explicit_hook_overrides` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_invalid_config_without_repos_raises_invalid_config_error` | generated | integration | ## Error Semantics | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_invalid_config_requires_rev_for_normal_repositories` | generated | integration | ## Error Semantics | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_invalid_config_rejects_rev_for_local_repositories` | generated | integration | ## Error Semantics | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_invalid_manifest_missing_required_keys_raises_invalid_manifest_error` | generated | integration | ## Hook Manifest | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_use_color_resolves_always_and_never` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_store_uses_pre_commit_home_and_creates_cache_files` | generated | integration | ## Store And Cache | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_store_make_local_reuses_matching_dependency_sets` | generated | integration | ## Store And Cache | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_normalize_cmd_resolves_existing_executable` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_normalize_cmd_raises_for_missing_executable` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cmd_output_returns_text_streams` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cmd_output_b_returns_bytes_streams` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cmd_output_can_return_nonzero_without_checking` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cmd_output_checked_nonzero_raises_called_process_error` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_partition_returns_executable_batches_and_handles_empty_args` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_partition_rejects_argument_lists_that_cannot_fit` | generated | atomic | ## Validation And Utility Behavior | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_all_hooks_resolves_local_hook_public_attributes` | generated | integration | ## Hook Resolution | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_all_hooks_resolves_meta_identity_hook` | generated | integration | ## Hook Resolution | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_validate_config_returns_zero_for_valid_and_nonzero_for_invalid` | generated | atomic | ## Error Semantics | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_validate_manifest_returns_zero_for_valid_and_nonzero_for_invalid` | generated | atomic | ## Hook Manifest | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_sample_config_prints_yaml_example` | generated | atomic | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_clean_removes_the_configured_store` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_install_and_uninstall_manage_selected_hook_script` | generated | system_e2e | ## Installing Git Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_fail_language_fails_and_reports_hook_id` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_skip_environment_skips_hook_id` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_skip_environment_accepts_alias` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_pygrep_fails_when_pattern_matches` | generated | system_e2e | ## Bounded Local Languages | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_pygrep_negate_passes_when_pattern_matches` | generated | system_e2e | ## Bounded Local Languages | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_always_run_executes_even_without_matching_files` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_pass_filenames_false_omits_selected_filenames` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_manual_stage_selects_manual_hooks` | generated | system_e2e | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_files_limits_hook_input_to_explicit_files` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_validate_config_accepts_multiple_valid_files` | generated | atomic | ## Error Semantics | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_validate_config_fails_when_any_file_is_invalid` | generated | atomic | ## Error Semantics | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_validate_manifest_accepts_multiple_valid_files` | generated | atomic | ## Hook Manifest | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_validate_manifest_fails_when_any_file_is_invalid` | generated | atomic | ## Hook Manifest | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_migrate_config_wraps_legacy_repo_list` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_migrate_config_rewrites_sha_key_to_rev` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_migrate_config_rewrites_legacy_stage_names` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_migrate_config_rewrites_python_venv_language` | generated | integration | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_single_hook_id_limits_execution` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_fail_fast_stops_after_first_failing_hook` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_skips_non_matching_files_without_always_run` | generated | system_e2e | ## Running Hooks | covered | conftest-free generated behavioral test; reference observed pass |
| `filter/generated_tests.py::test_cli_run_default_stage_ignores_manual_only_hooks` | generated | system_e2e | ## Configuration File | covered | conftest-free generated behavioral test; reference observed pass |

Oracle source marker: filter/oracle_source: generated_only

Total: 52 | kept (covered): 52 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 52
Covered by layer: atomic=18 | integration=23 | system_e2e=12

2026-07-02 rescue note: expanded generated-only oracle from 41 to 53 behavioral tests after removing the six Stage-5 over-specific generated tests; reference gate is 53/53 and dummy gate is 0/53.
