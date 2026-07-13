# Spec Test Map

oracle_source: generated_only
track_a_source: previous upstream oracle rejected after Stage 4 because tests/conftest.py imported private copier._types through upstream helpers
track_b_source: filter/generated_tests.py public-surface verifier tests

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| `filter/generated_tests.py::test_run_copy_renders_file_contents_and_paths` | generated | integration | `run_copy` | covered | renders templated file contents, templated paths, and recorded answers from one copy workflow |
| `filter/generated_tests.py::test_defaults_mode_uses_question_defaults` | generated | atomic | `run_copy` | covered | defaults mode accepts question defaults without prompting |
| `filter/generated_tests.py::test_api_data_overrides_template_default` | generated | atomic | `run_copy` | covered | API data overrides template question defaults |
| `filter/generated_tests.py::test_settings_defaults_are_used_when_defaults_mode_is_enabled` | generated | integration | `Settings` and `load_settings` | covered | Settings defaults participate in copy rendering when defaults mode is enabled |
| `filter/generated_tests.py::test_custom_answers_file_path_is_used_for_recorded_answers` | generated | integration | Answers Files | covered | custom answers file path controls persisted answers |
| `filter/generated_tests.py::test_exclude_omits_matching_template_files` | generated | atomic | Template Configuration | covered | exclude rules omit matching template files |
| `filter/generated_tests.py::test_skip_if_exists_preserves_existing_destination_file` | generated | integration | Template Configuration | covered | skip-if-exists preserves local destination files |
| `filter/generated_tests.py::test_force_overwrites_existing_destination_file` | generated | integration | `run_copy` | covered | overwrite mode replaces existing destination files |
| `filter/generated_tests.py::test_jinja_environment_settings_change_template_syntax` | generated | integration | Rendering Model | covered | Jinja environment options alter template delimiters |
| `filter/generated_tests.py::test_multiple_config_files_raise_documented_error` | generated | atomic | Error Semantics | covered | multiple config files raise the documented exception type |
| `filter/generated_tests.py::test_minimum_version_blocks_unsupported_template` | generated | atomic | Error Semantics | covered | minimum Copier version guard raises the documented exception type |
| `filter/generated_tests.py::test_secret_answer_can_render_but_is_not_recorded` | generated | integration | Answers Files | covered | secret answers render but are excluded from persisted answers |
| `filter/generated_tests.py::test_subdirectory_template_root_only_copies_that_tree` | generated | integration | Template Configuration | covered | subdirectory setting selects the copied template root |
| `filter/generated_tests.py::test_task_runs_when_template_is_trusted` | generated | system_e2e | Unsafe Features | covered | trusted unsafe task executes as part of the copy workflow |
| `filter/generated_tests.py::test_skip_tasks_avoids_running_trusted_tasks` | generated | system_e2e | Unsafe Features | covered | skip_tasks suppresses trusted task execution while copying files |
| `filter/generated_tests.py::test_load_settings_reads_yaml_defaults_and_trust` | generated | atomic | `Settings` and `load_settings` | covered | load_settings reads configured defaults and trust entries |
| `filter/generated_tests.py::test_invalid_settings_yaml_raises_settings_error` | generated | atomic | Error Semantics | covered | invalid settings YAML raises the documented settings exception |
| `filter/generated_tests.py::test_cli_copy_with_defaults_renders_template` | generated | system_e2e | CLI Behavior | covered | CLI copy with defaults renders a template to a destination |
| `filter/generated_tests.py::test_cli_data_overrides_default` | generated | system_e2e | CLI Behavior | covered | CLI --data overrides a template default |
| `filter/generated_tests.py::test_cli_data_file_is_used_for_answers` | generated | system_e2e | CLI Behavior | covered | CLI --data-file provides answer data |
| `filter/generated_tests.py::test_cli_data_takes_precedence_over_data_file` | generated | system_e2e | CLI Behavior | covered | CLI --data takes precedence over --data-file |
| `filter/generated_tests.py::test_cli_force_overwrites_existing_file` | generated | system_e2e | CLI Behavior | covered | CLI --force overwrites existing destination files |
| `filter/generated_tests.py::test_cli_refuses_unsafe_task_without_trust_exit_4` | generated | system_e2e | Unsafe Features | covered | CLI refuses unsafe tasks without trust and uses the documented exit behavior |
| `filter/generated_tests.py::test_question_type_int_parses_api_data` | generated | atomic | Rendering Model | covered | integer question values are parsed before rendering |
| `filter/generated_tests.py::test_question_type_bool_parses_cli_data` | generated | system_e2e | CLI Behavior | covered | boolean CLI data is parsed before rendering |
| `filter/generated_tests.py::test_question_type_float_parses_api_data` | generated | atomic | Rendering Model | covered | float question values are parsed before rendering |
| `filter/generated_tests.py::test_question_type_yaml_preserves_list_value` | generated | atomic | Rendering Model | covered | YAML question values preserve structured data for rendering |
| `filter/generated_tests.py::test_configuration_defaults_are_available_to_rendering` | generated | atomic | Template Variables | covered | configuration values are exposed to template rendering |
| `filter/generated_tests.py::test_phase_variable_is_render_during_file_render` | generated | atomic | Template Variables | covered | phase variable exposes render during file rendering |
| `filter/generated_tests.py::test_python_variable_points_to_current_interpreter` | generated | atomic | Template Variables | covered | python variable points to the active interpreter |

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_public_import_surface_includes_recopy_update_phase_and_vcsref` | generated | atomic | Installable Surface + Public API + `run_update` + Updates | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_phase_context_manager_restores_previous_phase` | generated | atomic | `Phase` and `VcsRef` | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_vcsref_current_string_is_accepted_by_copy_api` | generated | atomic | `Phase` and `VcsRef` | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_pretend_copy_leaves_destination_unchanged` | generated | integration | `run_copy` | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_custom_answers_file_argument_overrides_template_setting` | generated | integration | Answers Files | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_run_recopy_reuses_recorded_source_and_answers` | generated | system_e2e | `run_recopy` + Cross-View Invariants + Representative Workflows + Create and Update a Git-Versioned Project | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_run_recopy_data_overrides_recorded_answers` | generated | integration | `run_recopy` | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_run_recopy_pretend_leaves_project_files_unchanged` | generated | integration | `run_recopy` | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_recopy_reuses_answers_file` | generated | system_e2e | CLI Behavior | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_pretend_copy_does_not_create_destination` | generated | system_e2e | CLI Behavior | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_quiet_suppresses_normal_copy_output` | generated | system_e2e | CLI Behavior | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_answers_file_option_controls_recorded_path` | generated | system_e2e | Answers Files | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_external_data_requires_trust` | generated | atomic | Unsafe Features | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_external_data_renders_when_template_is_trusted` | generated | atomic | Settings Reference | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_settings_default_factory_isolated_between_instances` | generated | atomic | `Settings` and `load_settings` | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_load_settings_missing_env_path_returns_empty_with_warning` | generated | atomic | `Settings` and `load_settings` | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_skip_option_preserves_existing_file` | generated | system_e2e | CLI Behavior | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_exclude_option_omits_matching_file` | generated | system_e2e | CLI Behavior | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_no_cleanup_preserves_destination_after_error` | generated | system_e2e | CLI Behavior | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_cli_help_lists_copy_recopy_update_and_check_update` | generated | atomic | CLI Behavior + Updates + Check Updates from Automation | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |
| `filter/generated_tests.py::test_error_namespace_exports_documented_base_classes` | generated | atomic | Installable Surface | covered | Retroactive public-behavior oracle supplement for Gate D coverage. |

Total: 51 | kept (covered): 51 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 51

Total: 51 | kept (covered): 51 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 51
