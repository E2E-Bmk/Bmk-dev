# Spec Test Map

oracle_source: upstream_and_generated
track_a_source: filter/rewritten_upstream_tests.py
track_b_source: filter/generated_tests.py

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| `filter/rewritten_upstream_tests.py::test_ini_env_var_substitution_uses_default_when_missing` | upstream | integration | Substitutions and Conditional Values | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_posargs_default_is_used_without_extra_arguments` | upstream | integration | Substitutions and Conditional Values | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_posargs_override_default_after_separator` | upstream | integration | Substitutions and Conditional Values | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_generative_ini_env_list_expands_factor_product` | upstream | integration | Environment Selection | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_factor_filter_selects_matching_environments` | upstream | integration | Environment Selection | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_tox_ini_takes_precedence_over_setup_cfg` | upstream | integration | Configuration Files | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_pyproject_legacy_tox_ini_defines_environments` | upstream | integration | Configuration Files | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_tox_toml_env_run_base_values_are_inherited` | upstream | integration | Configuration Files | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_toml_labels_select_same_envs_in_list_and_config` | upstream | integration | Environment Selection | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_toxfile_plugin_can_add_env_config_key` | upstream | integration | Public API | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_depends_lists_dependency_edges` | upstream | system_e2e | Parallel and Failure Behavior | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_list_no_desc_outputs_only_environment_names` | upstream | integration | Environment Selection | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_schema_command_includes_core_sections` | upstream | atomic | Cross-View Invariants | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_config_output_file_writes_json_without_stdout` | upstream | atomic | Cross-View Invariants | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_module_invocation_prints_version` | upstream | atomic | Installable Surface | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_public_version_is_nonempty_string` | upstream | atomic | Installable Surface | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_pep723_runner_rejects_base_python_override` | upstream | system_e2e | Error Semantics | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_ci_environment_variable_can_be_passed_to_command` | upstream | system_e2e | Environment Variables and Commands | covered | public-surface rewritten upstream behavior |
| `filter/rewritten_upstream_tests.py::test_recreate_flag_recreates_environment` | upstream | system_e2e | Environment Lifecycle | covered | public-surface rewritten upstream behavior |
| `filter/generated_tests.py::test_public_import_surface_exposes_main_version_and_plugin_marker` | generated | atomic | Installable Surface | covered | Public import surface exposes version, entry point, plugin marker, and CLI version behavior. |
| `filter/generated_tests.py::test_tox_ini_is_discovered_before_tox_toml` | generated | integration | Configuration Files | covered | Configuration discovery prefers tox.ini over tox.toml when both are present. |
| `filter/generated_tests.py::test_pyproject_native_toml_is_preferred_over_legacy_tox_ini` | generated | integration | Configuration Files | covered | Native pyproject TOML configuration takes precedence over embedded legacy tox.ini. |
| `filter/generated_tests.py::test_pyproject_legacy_tox_ini_is_used_without_native_env_table` | generated | integration | Configuration Files | covered | Embedded legacy tox.ini is used when no native tox table defines environments. |
| `filter/generated_tests.py::test_ini_generative_env_list_expands_and_substitutes_env_name` | generated | integration | Environment Selection | covered | Generative INI env lists expand factors and substitute the selected environment name. |
| `filter/generated_tests.py::test_label_selection_matches_between_list_and_config` | generated | integration | Environment Selection | covered | Label selection is reflected consistently by list and config views. |
| `filter/generated_tests.py::test_config_json_preserves_native_types_and_inherited_values` | generated | integration | Cross-View Invariants | covered | JSON config output preserves native values and inherited settings. |
| `filter/generated_tests.py::test_config_core_json_includes_env_list_only_when_core_is_requested` | generated | atomic | Cross-View Invariants | covered | Core configuration appears in JSON output only when requested. |
| `filter/generated_tests.py::test_config_toml_output_file_writes_selected_env_without_stdout` | generated | atomic | Cross-View Invariants | covered | TOML config output can be written to a file without stdout content. |
| `filter/generated_tests.py::test_schema_command_outputs_json_schema_for_tox_configuration` | generated | atomic | Cross-View Invariants | covered | Schema command exposes tox configuration schema as JSON. |
| `filter/generated_tests.py::test_depends_reports_dependency_order_for_default_environment_set` | generated | system_e2e | Environment Selection | covered | Depends view reports dependency ordering for selected environments. |
| `filter/generated_tests.py::test_mutually_exclusive_no_capture_and_result_json_fails_before_writing_json` | generated | atomic | Error Semantics | covered | Mutually exclusive CLI options fail without producing result JSON. |

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_main_returns_success_for_version_query` | generated | atomic | Public API | covered | Public main supports version query with success status. |
| `filter/generated_tests.py::test_plugin_hook_marker_decorates_public_hook_function` | generated | atomic | Public API | covered | Public plugin marker records hook implementation metadata. |
| `filter/generated_tests.py::test_common_subcommands_are_advertised_in_help` | generated | atomic | Public API | covered | CLI help exposes core documented commands and parallel mode. |
| `filter/generated_tests.py::test_config_option_selects_explicit_tox_file` | generated | integration | Configuration Files | covered | Explicit config path selects that file over project discovery. |
| `filter/generated_tests.py::test_setup_cfg_is_used_when_tox_ini_is_absent` | generated | integration | Configuration Files | covered | setup.cfg tox section is discovered when tox.ini is absent. |
| `filter/generated_tests.py::test_tox_toml_is_used_when_earlier_config_files_are_absent` | generated | integration | Configuration Files | covered | tox.toml is discovered when earlier config files are absent. |
| `filter/generated_tests.py::test_toml_product_env_list_expands_to_cartesian_product` | generated | integration | Environment Selection | covered | Native TOML product env lists expand to generated environments. |
| `filter/generated_tests.py::test_env_base_template_generates_factor_environments` | generated | integration | Environment Selection | covered | env_base templates generate factor environments and descriptions. |
| `filter/generated_tests.py::test_toml_conditional_replacement_uses_else_branch_when_env_is_missing` | generated | integration | Substitutions and Conditional Values | covered | TOML conditional replacement resolves branch from host environment state. |
| `filter/generated_tests.py::test_posargs_are_rendered_only_in_commands` | generated | integration | Substitutions and Conditional Values | covered | Positional args affect command substitution without changing other config keys. |
| `filter/generated_tests.py::test_set_env_pass_env_and_disallow_pass_env_are_visible_in_config` | generated | integration | Environment Variables and Commands | covered | Environment pass/disallow/set variables are visible in resolved config. |
| `filter/generated_tests.py::test_package_modes_remain_visible_in_verbose_configuration` | generated | integration | Packaging | covered | Verbose config exposes configured package modes. |
| `filter/generated_tests.py::test_explicit_package_environment_is_listed_separately` | generated | integration | Packaging | covered | Explicit package environment is listed as a separate environment. |
| `filter/generated_tests.py::test_run_with_skip_pkg_install_executes_configured_command` | generated | system_e2e | Environment Lifecycle + Representative Workflows | covered | Run command executes configured command while skipping package installation. |
| `filter/generated_tests.py::test_command_prefixes_ignore_and_invert_failures` | generated | system_e2e | Environment Variables and Commands | covered | Command prefixes ignore and invert nonzero command results. |
| `filter/generated_tests.py::test_exec_runs_supplied_command_without_configured_commands` | generated | system_e2e | Public API | covered | tox exec runs supplied command without configured command phase. |
| `filter/generated_tests.py::test_failing_command_returns_nonzero_and_skips_later_commands` | generated | system_e2e | Error Semantics | covered | Unignored failing command returns nonzero and stops later commands. |
| `filter/generated_tests.py::test_skip_missing_interpreters_reports_skip_for_missing_python` | generated | system_e2e | Error Semantics | covered | Missing interpreter with skip option reports a skipped environment. |
| `filter/generated_tests.py::test_depends_does_not_add_unselected_dependencies` | generated | integration | Parallel and Failure Behavior | covered | Depends view reports dependency edges for configured environments. |
| `filter/generated_tests.py::test_pylock_and_deps_are_mutually_exclusive` | generated | atomic | Error Semantics | covered | pylock and deps conflict is reported as a handled error. |

Total: 51 | kept (covered): 51 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 51
