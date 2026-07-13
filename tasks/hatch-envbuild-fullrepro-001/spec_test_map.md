# Spec Test Map

task_id: hatch-envbuild-fullrepro-001
spec_version: v1
oracle_version: 2026-07-03-user-authorized-exception-lockfile-v4
oracle_source: upstream_rewritten_plus_user_authorized_exception
exception_note: user-authorized exception on 2026-07-03; RETIRED was reopened and filter_iter reset to 0 by explicit user instruction, not by normal SKILL rescue rules.
dummy_gate: original real pytest invocation against importable dummy hatch package; retro lockfile additions are behavioral validation/error checks added under user-authorized exception on 2026-07-03 and must be covered by the WSL reference gate before promotion.

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/rewritten_upstream_tests.py::test_root_version_option_reports_version | upstream | atomic | Public API | covered | root option behavior |
| filter/rewritten_upstream_tests.py::test_root_module_help_reports_usage | upstream | atomic | Public API | covered | module invocation and help |
| filter/rewritten_upstream_tests.py::test_config_find_prints_active_config_path | upstream | atomic | Project And Configuration Behavior | covered | config find |
| filter/rewritten_upstream_tests.py::test_config_restore_rewrites_config_file | upstream | atomic | Project And Configuration Behavior | covered | config restore |
| filter/rewritten_upstream_tests.py::test_config_set_mode_project_persists_value | upstream | integration | Project And Configuration Behavior | covered | config set persists mode |
| filter/rewritten_upstream_tests.py::test_config_set_project_name_persists_value | upstream | integration | Project And Configuration Behavior | covered | config set persists project |
| filter/rewritten_upstream_tests.py::test_config_set_env_directory_affects_env_find | upstream | system_e2e | Cross-View Invariants | covered | config affects env path |
| filter/rewritten_upstream_tests.py::test_config_command_line_config_overrides_env_config | upstream | integration | Public API | covered | root --config precedence |
| filter/rewritten_upstream_tests.py::test_status_reports_project_name_and_location | upstream | atomic | Project And Configuration Behavior | covered | project status path across output streams |
| filter/rewritten_upstream_tests.py::test_status_outside_project_reports_no_project | upstream | atomic | Project And Configuration Behavior | covered | environment-management-only project status |
| filter/rewritten_upstream_tests.py::test_project_metadata_all_includes_name_and_version | upstream | atomic | Project Metadata Behavior | covered | metadata JSON |
| filter/rewritten_upstream_tests.py::test_project_metadata_name_field | upstream | atomic | Project Metadata Behavior | covered | metadata field |
| filter/rewritten_upstream_tests.py::test_project_metadata_version_field | upstream | atomic | Project Metadata Behavior | covered | metadata version |
| filter/rewritten_upstream_tests.py::test_project_metadata_readme_field | upstream | atomic | Project Metadata Behavior | covered | readme field |
| filter/rewritten_upstream_tests.py::test_project_metadata_unknown_field_fails | upstream | atomic | Error Semantics | covered | unknown metadata field |
| filter/rewritten_upstream_tests.py::test_project_metadata_rejects_direct_reference_by_default | upstream | atomic | Project Metadata Behavior | covered | direct references rejected by default |
| filter/rewritten_upstream_tests.py::test_hatch_toml_takes_precedence_for_env_scripts | upstream | system_e2e | Project And Configuration Behavior | covered | hatch.toml precedence visible in resolved script list |
| filter/rewritten_upstream_tests.py::test_env_show_json_synthesizes_default_virtual | upstream | atomic | Environment Configuration Behavior | covered | default env synthesis |
| filter/rewritten_upstream_tests.py::test_env_show_json_includes_configured_env | upstream | atomic | Environment Command Behavior | covered | env show JSON |
| filter/rewritten_upstream_tests.py::test_env_show_json_includes_env_vars | upstream | integration | Environment Command Behavior | covered | resolved env vars projection |
| filter/rewritten_upstream_tests.py::test_env_show_json_includes_scripts | upstream | integration | Environment Command Behavior | covered | resolved scripts projection as command list |
| filter/rewritten_upstream_tests.py::test_env_show_specific_env_filters_output | upstream | atomic | Environment Command Behavior | covered | named env appears in JSON projection |
| filter/rewritten_upstream_tests.py::test_env_show_matrix_expands_generated_names | upstream | integration | Matrix And Override Behavior | covered | matrix expansion |
| filter/rewritten_upstream_tests.py::test_env_show_default_matrix_has_unprefixed_names | upstream | integration | Matrix And Override Behavior | covered | default matrix names |
| filter/rewritten_upstream_tests.py::test_env_show_matrix_py_variable_first | upstream | integration | Matrix And Override Behavior | covered | py variable naming |
| filter/rewritten_upstream_tests.py::test_env_show_matrix_name_format_applies_value | upstream | integration | Matrix And Override Behavior | covered | matrix-name-format |
| filter/rewritten_upstream_tests.py::test_env_show_matrix_with_py_and_python_fails | upstream | atomic | Error Semantics | covered | invalid matrix variables |
| filter/rewritten_upstream_tests.py::test_env_show_invalid_matrix_name_format_fails | upstream | atomic | Error Semantics | covered | invalid matrix-name-format |
| filter/rewritten_upstream_tests.py::test_env_find_default_prints_path | upstream | atomic | Environment Command Behavior | covered | env find default |
| filter/rewritten_upstream_tests.py::test_env_find_configured_env_prints_path | upstream | atomic | Environment Command Behavior | covered | env find named |
| filter/rewritten_upstream_tests.py::test_env_find_unknown_env_fails | upstream | atomic | Error Semantics | covered | unknown env find |
| filter/rewritten_upstream_tests.py::test_env_run_system_executes_command_in_project_root | upstream | system_e2e | Invocation Protocol | covered | commands run from project root |
| filter/rewritten_upstream_tests.py::test_hatch_run_empty_prefix_selects_system_environment | upstream | integration | Environment Command Behavior | covered | empty run prefix selects system |
| filter/rewritten_upstream_tests.py::test_hatch_run_env_prefix_for_unknown_env_fails | upstream | atomic | Error Semantics | covered | unknown run env |
| filter/rewritten_upstream_tests.py::test_hatch_run_without_command_fails | upstream | atomic | Environment Command Behavior | covered | missing command validation without exact diagnostic wording |
| filter/rewritten_upstream_tests.py::test_env_run_filter_non_mapping_json_fails | upstream | atomic | Error Semantics | covered | filter must be JSON mapping |
| filter/rewritten_upstream_tests.py::test_env_run_duplicate_include_vars_fail | upstream | atomic | Error Semantics | covered | duplicate matrix include variables fail |
| filter/rewritten_upstream_tests.py::test_shell_matrix_parent_fails_before_entering_shell | upstream | integration | Environment Command Behavior | covered | shell requires generated env choice |
| filter/rewritten_upstream_tests.py::test_env_remove_unknown_env_fails | upstream | atomic | Error Semantics | covered | unknown env remove |
| filter/rewritten_upstream_tests.py::test_env_prune_unknown_type_fails_before_removal | upstream | integration | Error Semantics | covered | unknown env type blocks prune |
| filter/rewritten_upstream_tests.py::test_env_lock_default_check_reports_default_lockfile | user_authorized_exception_generated | atomic | Environment Lockfile Behavior | covered | default environment --check uses pylock.toml |
| filter/rewritten_upstream_tests.py::test_env_lock_named_check_reports_named_lockfile | user_authorized_exception_generated | atomic | Environment Lockfile Behavior | covered | named environment --check uses pylock.<env>.toml |
| filter/rewritten_upstream_tests.py::test_env_lock_custom_filename_check_uses_override | user_authorized_exception_generated | atomic | Environment Lockfile Behavior | covered | lock-filename overrides the selected lockfile path |
| filter/rewritten_upstream_tests.py::test_env_lock_export_and_export_all_are_mutually_exclusive | user_authorized_exception_generated | atomic | Environment Lockfile Behavior | covered | --export and --export-all fail when combined |
| filter/rewritten_upstream_tests.py::test_env_lock_unknown_environment_fails | user_authorized_exception_generated | atomic | Environment Lockfile Behavior | covered | unknown env lock selection fails |
| filter/rewritten_upstream_tests.py::test_env_lock_without_name_uses_global_lock_envs_and_skips_opt_out | user_authorized_exception_generated | integration | Environment Lockfile Behavior | covered | lock-envs true selects locked environments and locked false opts out |
| filter/rewritten_upstream_tests.py::test_dep_lock_uses_active_root_environment | user_authorized_exception_generated | integration | Environment Lockfile Behavior | covered | dep lock uses root active environment |
| filter/rewritten_upstream_tests.py::test_lock_alias_uses_active_root_environment | user_authorized_exception_generated | integration | Environment Lockfile Behavior | covered | lock alias uses root active environment |
| filter/rewritten_upstream_tests.py::test_version_static_displays_value | upstream | atomic | Version Behavior | covered | static version display |
| filter/rewritten_upstream_tests.py::test_version_static_set_fails | upstream | atomic | Error Semantics | covered | static version cannot be set without exact diagnostic wording |
| filter/rewritten_upstream_tests.py::test_version_no_project_fails | upstream | atomic | Error Semantics | covered | version requires project |
| filter/rewritten_upstream_tests.py::test_version_dynamic_regex_reads_file | upstream | integration | Version Behavior | covered | dynamic regex version display |
| filter/rewritten_upstream_tests.py::test_version_dynamic_custom_pattern_without_group_fails | upstream | atomic | Error Semantics | covered | regex pattern must expose version group |
| filter/rewritten_upstream_tests.py::test_build_wheel_creates_artifact | upstream | system_e2e | Build And Clean Behavior | covered | wheel artifact side effect |
| filter/rewritten_upstream_tests.py::test_build_custom_location_writes_artifact | upstream | system_e2e | Build And Clean Behavior | covered | custom build output location |
| filter/rewritten_upstream_tests.py::test_build_unknown_target_fails | upstream | atomic | Error Semantics | covered | unsupported target fails |
| filter/rewritten_upstream_tests.py::test_build_force_include_missing_source_fails | upstream | atomic | Error Semantics | covered | missing force-include source fails |
| filter/rewritten_upstream_tests.py::test_clean_custom_location_removes_build_artifacts | upstream | system_e2e | Cross-View Invariants | covered | build output cleaned by same location |
| filter/rewritten_upstream_tests.py::test_clean_default_dist_removes_build_artifacts | upstream | system_e2e | Build And Clean Behavior | covered | default dist clean |

Total: 59 | kept (covered): 59 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 59
