# Stage 3 Track B Spec Test Map

Task: `dynaconf-settings-fullrepro-001`

filter/oracle_source: generated_only

Expanded on 2026-07-02 from 14 to 50 generated-only tests. Reference gate: 50/50 passed. Dummy gate: 50/50 failed.

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `generated_tests.py::test_public_import_surface_exposes_configured_visible_state` | generated | atomic | ## Public Import Surface | removed-unpromised-surface [20260709] | Public names documented by the spec import from `dynaconf`, and constructor keyword settings are visible through public access/as_dict. |
| `generated_tests.py::test_envvar_overrides_file_and_casts_to_int` | generated | integration | ## Environment Variables | covered | Environment variables override file values and TOML-like values cast before access and as_dict. |
| `generated_tests.py::test_local_file_overrides_base_file` | generated | integration | ## Source Loading Order | covered | Local settings files load after their corresponding base file and override scalar values. |
| `generated_tests.py::test_includes_load_after_regular_settings` | generated | integration | ## Source Loading Order | covered | Constructor includes load after regular settings files and can override earlier values. |
| `generated_tests.py::test_nested_access_as_dict_and_env_dunder_merge` | generated | integration | ## Accessing Settings | covered | Nested envvar dunder keys merge and agree through attribute, item, dotted get, and as_dict views. |
| `generated_tests.py::test_merge_marker_combines_environment_dictionary` | generated | integration | ## Cross-View Invariants | covered | @merge envvar dictionaries merge into existing dictionaries, remain visible through dotted/as_dict views, and hide marker keys. |
| `generated_tests.py::test_environment_default_global_and_active_values` | generated | integration | ## Cross-View Invariants | covered | Active, default, and global environment values project consistently into the final active settings view. |
| `generated_tests.py::test_from_env_returns_isolated_settings_without_changing_original` | generated | integration | ## Layered Environments | covered | from_env returns another environment view without changing the original. |
| `generated_tests.py::test_setenv_and_using_env_restore_active_environment` | generated | integration | ## Layered Environments | covered | setenv and using_env switch active environment consistently and restore context. |
| `generated_tests.py::test_validator_default_and_cast_mutate_visible_state` | generated | atomic | ## Cross-View Invariants | covered | Validator defaults and casts mutate the same visible settings state read by later public accessors. |
| `generated_tests.py::test_validate_all_accumulates_multiple_validation_errors` | generated | atomic | ## Error Semantics | covered | validate_all accumulates multiple validation failures in ValidationError details. |
| `generated_tests.py::test_validate_on_update_rejects_invalid_runtime_value` | generated | integration | ## Runtime Updates | covered | validate_on_update rejects invalid runtime values and permits valid updates. |
| `generated_tests.py::test_custom_converter_composes_with_format_token` | generated | atomic | ## Casting Tokens and Lazy Values | covered | Custom converter tokens compose with @format. |
| `generated_tests.py::test_history_and_inspect_report_file_and_env_sources` | generated | integration | ## Inspection and History | covered | History and inspection expose current values and source metadata. |
| `generated_tests.py::test_cli_get_list_and_inspect_observe_configured_instance` | generated | system_e2e | ## Cross-View Invariants | covered | CLI get/list/inspect agree with an importable configured settings instance and env selection. |
| `generated_tests.py::test_preload_regular_file_and_include_order` | generated | integration | ## Source Loading Order | covered | Preload, settings file, and include order produce deterministic overrides. |
| `generated_tests.py::test_file_declared_dynaconf_include_loads_relative_file` | generated | integration | ## File Loading | covered | dynaconf_include inside a file loads referenced relative files. |
| `generated_tests.py::test_settings_files_accepts_semicolon_separated_paths` | generated | integration | ## Constructing Settings | covered | settings_files accepts multiple paths in a separator string. |
| `generated_tests.py::test_python_settings_file_loads_only_uppercase_names` | generated | integration | ## File Loading | covered | Python settings files expose uppercase variables and ignore lowercase locals. |
| `generated_tests.py::test_multiple_envvar_prefixes_are_loaded` | generated | integration | ## Environment Variables | covered | Comma-separated envvar prefixes load variables from all listed prefixes. |
| `generated_tests.py::test_unprefixed_environment_variables_can_be_settings` | generated | integration | ## Environment Variables | covered | envvar_prefix=False allows unprefixed environment variables to be considered settings. |
| `generated_tests.py::test_ignore_unknown_envvars_keeps_only_preexisting_keys` | generated | integration | ## Environment Variables | covered | ignore_unknown_envvars loads only envvars for preexisting keys. |
| `generated_tests.py::test_sysenv_fallback_reads_unprefixed_missing_key` | generated | integration | ## Environment Variables | covered | sysenv_fallback can read an unprefixed missing key from the process environment. |
| `generated_tests.py::test_sysenv_fallback_list_restricts_allowed_names` | generated | integration | ## Environment Variables | covered | sysenv_fallback list restricts fallback names. |
| `generated_tests.py::test_comma_separated_active_envs_load_in_order` | generated | integration | ## Layered Environments | covered | Comma-separated active environments load in order with later values overriding earlier ones. |
| `generated_tests.py::test_from_env_keep_chains_existing_values` | generated | integration | ## Layered Environments | covered | from_env keep=True chains previous loaded values into the new environment view. |
| `generated_tests.py::test_auto_cast_false_leaves_envvar_tokens_as_strings` | generated | integration | ## Casting Tokens and Lazy Values | covered | auto_cast=False leaves explicit casting tokens uninterpreted while plain env TOML values still parse. |
| `generated_tests.py::test_builtin_cast_tokens_from_file` | generated | atomic | ## Casting Tokens and Lazy Values | covered | Built-in cast tokens convert file values to public Python values. |
| `generated_tests.py::test_get_token_reads_another_setting_and_casts_default` | generated | atomic | ## Casting Tokens and Lazy Values | covered | @get lazily reads another setting and can return a default. |
| `generated_tests.py::test_read_file_token_reads_relative_file` | generated | atomic | ## Casting Tokens and Lazy Values | covered | @read_file reads text from a referenced file. |
| `generated_tests.py::test_string_utility_tokens_transform_values` | generated | atomic | ## Casting Tokens and Lazy Values | covered | String utility tokens transform values at access time. |
| `generated_tests.py::test_insert_token_adds_list_item_at_requested_position` | generated | integration | ## Merge Semantics | covered | @insert adds a list item at the requested position. |
| `generated_tests.py::test_del_token_removes_nested_envvar_value` | generated | integration | ## Merge Semantics | covered | @del removes a nested value through a nested envvar. |
| `generated_tests.py::test_global_merge_enabled_merges_later_dictionaries_and_lists` | generated | integration | ## Merge Semantics | covered | merge_enabled merges later dictionaries and lists into existing values. |
| `generated_tests.py::test_local_file_top_level_merge_marker_merges_environment_section` | generated | integration | ## Merge Semantics | covered | Local file dynaconf_merge marker merges environment sections. |
| `generated_tests.py::test_runtime_set_creates_nested_value_visible_in_all_views` | generated | integration | ## Runtime Updates | covered | runtime set creates nested values visible through attributes, get, and as_dict. |
| `generated_tests.py::test_runtime_update_validate_true_raises_first_error` | generated | atomic | ## Error Semantics | covered | runtime update validate=True raises the first validation error. |
| `generated_tests.py::test_validator_apply_default_on_none_sets_none_value` | generated | atomic | ## Validators | covered | apply_default_on_none allows validator defaults to replace None. |
| `generated_tests.py::test_validator_or_and_and_composition` | generated | atomic | ## Validators | covered | Validator composition accepts documented OR/AND success cases. |
| `generated_tests.py::test_validator_callable_default_can_read_settings_context` | generated | atomic | ## Validators | covered | Callable validator defaults can read the settings context. |
| `generated_tests.py::test_validator_casts_are_ordered_and_mutate_state` | generated | atomic | ## Validators | covered | Multiple validator casts are cumulative and mutate the same setting. |
| `generated_tests.py::test_load_file_adds_runtime_values_and_history` | generated | integration | ## Runtime Updates | covered | load_file adds runtime values and records history. |
| `generated_tests.py::test_load_file_env_false_loads_top_level_without_environment_sections` | generated | integration | ## Runtime Updates | covered | load_file env=False loads file data as top-level values without selecting environments. |
| `generated_tests.py::test_fresh_var_reloads_source_on_access` | generated | integration | ## Runtime Updates | covered | fresh_vars reload source values on access. |
| `generated_tests.py::test_constructor_post_hook_merges_returned_data` | generated | system_e2e | ## Cross-View Invariants | covered | constructor post_hooks merge returned data after source loading and expose it through the final settings view. |
| `generated_tests.py::test_dynaconf_hooks_file_contributes_post_data` | generated | system_e2e | ## Hooks | covered | dynaconf_hooks.py post function contributes post-load data. |
| `generated_tests.py::test_python_settings_post_hook_runs_when_file_loads` | generated | system_e2e | ## Hooks | covered | Python settings-file post_hook contributes data when the file loads. |
| `generated_tests.py::test_cli_get_missing_key_without_default_returns_nonzero` | generated | atomic | ## Error Semantics | covered | CLI get missing key without default exits nonzero. |
| `generated_tests.py::test_cli_get_missing_key_with_default_prints_default` | generated | atomic | ## CLI Behavior | covered | CLI get can print a provided default. |
| `generated_tests.py::test_cli_list_json_filters_by_key` | generated | system_e2e | ## CLI Behavior | removed-unpromised-surface [20260709] | CLI list --json --key filters user-defined settings. |
| `generated_tests.py::test_cli_inspect_prints_json_report` | generated | system_e2e | ## CLI Behavior | covered | CLI inspect prints JSON report data for a selected key. |

Total: 51 | kept (covered): 49 | spec_gap: 0 | source-only: 0 | excluded: 2 + 2 removed-unpromised-surface (2026-07-09) | final_scoreable: 49
Covered by layer: atomic=15 | integration=30 | system_e2e=6

Excluded during expansion: two candidate tests that passed the dummy gate (`test_runtime_update_skips_validation_when_requested`, `test_cli_validate_uses_dynaconf_validators_file`).

Stage 5 coverage audit note (2026-07-02): seven rows were remapped to their stricter behavioral sections (`## Cross-View Invariants` or `## Error Semantics`) without changing test code or oracle membership.

> 2026-07-09 fairness surgery: the two rows marked removed-unpromised-surface were dropped from kept_nodeids/taxonomy because their assertions measure uppercase-constructor-kwarg settings visibility (`Dynaconf(PORT="8000")` projected through attribute/as_dict access and through CLI `list --json`), a mechanism the spec's closed Constructing Settings option list never promises. Four retained validator tests still use uppercase constructor kwargs as fixture plumbing; their assertions target promised validator semantics and their setup leans on the "Explicit constructor defaults" load-order clause, but the constructor-kwarg mechanism itself should be explicitly promised or the fixtures migrated to documented sources at the next respec cycle (flagged as an open item, not surgically changed now).
