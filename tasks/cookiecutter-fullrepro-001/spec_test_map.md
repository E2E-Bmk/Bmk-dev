# Spec Test Map

oracle_source: upstream_filtered
track_a_source: wip/filter/oracle_candidates/test_taxonomy.csv

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `tests/test_abort_generate_on_hook_error.py::test_hooks_raises_errors` | upstream | system_e2e | Hooks | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_version` | upstream | system_e2e | Public Interfaces + CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_error_on_existing_output_directory` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_verbose` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_replay` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_replay_file` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_replay_generated` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_exit_on_noinput_and_replay` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_run_cookiecutter_on_overwrite_if_exists_and_replay` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_overwrite_if_exists_when_output_dir_does_not_exist` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_overwrite_if_exists_when_output_dir_exists` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_output_dir` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_help` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_user_config` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_default_user_config_overwrite` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_default_user_config` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_echo_undefined_variable_error` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_echo_unknown_extension_error` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_local_extension` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_local_extension_not_available` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_extra_context` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_extra_context_invalid_format` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_debug_file_non_verbose` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_debug_file_verbose` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_debug_list_installed_templates` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_debug_list_installed_templates_failure` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_directory_repo` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_accept_hooks` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_with_json_decoding_error` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cli.py::test_cli_with_pre_prompt_hook` | upstream | system_e2e | CLI | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_no_input.py::test_cookiecutter_no_input_return_project_dir` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_no_input.py::test_cookiecutter_no_input_extra_context` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_no_input.py::test_cookiecutter_templated_context` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_no_input.py::test_cookiecutter_no_input_return_rendered_file` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_no_input.py::test_cookiecutter_dict_values_in_context` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_no_input.py::test_cookiecutter_template_cleanup` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_with_input.py::test_cookiecutter_local_with_input` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_local_with_input.py::test_cookiecutter_input_extra_context` | upstream | system_e2e | Cross-View Invariants | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_cookiecutter_nested_templates.py::test_cookiecutter_nested_templates` | upstream | integration | Template Structure + cookiecutter.json Variable Types + `templates` Key (Nested Config, v2.5+) | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_custom_extensions_in_hooks.py::test_hook_with_extension` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_default_extensions.py::test_jinja2_time_extension` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_default_extensions.py::test_jinja2_slugify_extension` | upstream | integration | `cookiecutter.extensions.SlugifyExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_default_extensions.py::test_jinja2_uuid_extension` | upstream | integration | `cookiecutter.extensions.UUIDExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_environment.py::test_env_should_raise_for_unknown_extension` | upstream | atomic | `_extensions` Key + Built-in Template Extensions + Custom Extensions via `_extensions` | covered | single public behavior or bounded helper API |
| `tests/test_environment.py::test_env_should_come_with_default_extensions` | upstream | atomic | Custom Extensions via `_extensions` | covered | single public behavior or bounded helper API |
| `tests/test_exceptions.py::test_undefined_variable_to_str` | upstream | atomic | Exceptions | covered | single public behavior or bounded helper API |
| `tests/test_find.py::test_find_template` | upstream | atomic | Template Directories and Archives | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_generate_context` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_generate_context_with_json_decoding_error` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_default_context_replacement_in_generate_context` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_generate_context_decodes_non_ascii_chars` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_does_include_unused_variables` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_sets_non_list_value` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_does_not_modify_choices_for_invalid_overwrite` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_invalid_overwrite` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_sets_multichoice_values` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_invalid_multichoice_values` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_error_additional_values` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_in_dictionaries` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_sets_default_for_choice_variable` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_in_nested_dict` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrite_context_as_in_nested_dict_with_additional_values` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_in_nested_dict_additional_values` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_overwrite_value_as_boolean_string` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_context.py::test_apply_overwrites_error_overwrite_value_as_boolean_string` | upstream | atomic | Context Building Pipeline | covered | single public behavior or bounded helper API |
| `tests/test_generate_copy_without_render.py::test_generate_copy_without_render_extensions` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_copy_without_render_override.py::test_generate_copy_without_render_extensions` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_file.py::test_generate_file` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_jsonify_filter` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_random_ascii_string` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_with_true_condition` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_with_false_condition` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_verbose_template_syntax_error` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_does_not_translate_lf_newlines_to_crlf` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_does_not_translate_crlf_newlines_to_lf` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_file.py::test_generate_file_handles_mixed_line_endings` | upstream | atomic | Rendering and File Generation | covered | single public behavior or bounded helper API |
| `tests/test_generate_files.py::test_generate_files_nontemplated_exception` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_linux_newline` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_jinja2_environment` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_trailing_newline_forced_to_linux_by_context` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_windows_newline` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_windows_newline_forced_to_linux_by_context` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_binaries` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_absolute_path` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_output_dir` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_permissions` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_overwrite_if_exists_with_skip_if_file_exists` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_skip_if_file_exists` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_generate_files_with_overwrite_if_exists` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_raise_undefined_variable_file_name` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_raise_undefined_variable_file_name_existing_project` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_raise_undefined_variable_file_content` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_raise_undefined_variable_dir_name` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_keep_project_dir_on_failure` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_raise_undefined_variable_dir_name_existing_project` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_raise_undefined_variable_project_dir` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_files.py::test_raise_empty_dir_name` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_ignore_hooks_dirs` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_run_python_hooks` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_run_python_hooks_cwd` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_empty_hooks` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_oserror_hooks` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_run_failing_hook_removes_output_directory` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_run_failing_hook_preserves_existing_output_directory` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_run_shell_hooks` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_run_shell_hooks_win` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_ignore_shell_hooks` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_generate_hooks.py::test_deprecate_run_hook_from_repo_dir` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_get_config.py::test_get_config_does_not_exist` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_config.py::test_invalid_config` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_config.py::test_get_config_empty_config_file` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_config.py::test_get_config_invalid_file_with_array_as_top_level_element` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_config.py::test_get_config_invalid_file_with_multiple_docs` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_get_user_config_valid` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_get_user_config_invalid` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_get_user_config_nonexistent` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_specify_config_path` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_default_config_path` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_force_default_config` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_expand_user_for_directories_in_config` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_get_user_config.py::test_specify_config_values` | upstream | atomic | User Configuration | covered | single public behavior or bounded helper API |
| `tests/test_hooks.py::test_ignore_hook_backup_files` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestFindHooks.test_find_hook` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestFindHooks.test_no_hooks` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestFindHooks.test_unknown_hooks_dir` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestFindHooks.test_hook_not_found` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestExternalHooks.test_run_script` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestExternalHooks.test_run_failing_script` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestExternalHooks.test_run_failing_script_enoexec` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestExternalHooks.test_run_script_cwd` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestExternalHooks.test_run_script_with_context` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestExternalHooks.test_run_hook` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_hooks.py::TestExternalHooks.test_run_failing_hook` | upstream | integration | Hooks | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_log.py::test_info_stdout_logging` | upstream | atomic | Logging | covered | single public behavior or bounded helper API |
| `tests/test_log.py::test_debug_stdout_logging` | upstream | atomic | Logging | covered | single public behavior or bounded helper API |
| `tests/test_log.py::test_debug_file_logging` | upstream | atomic | Logging | covered | single public behavior or bounded helper API |
| `tests/test_main.py::test_original_cookiecutter_options_preserved_in__cookiecutter` | upstream | system_e2e | Python API | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_main.py::test_replay_dump_template_name` | upstream | system_e2e | Python API | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_main.py::test_replay_load_template_name` | upstream | system_e2e | Python API | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_main.py::test_custom_replay_file` | upstream | system_e2e | Python API | covered | end-to-end generation workflow through CLI or top-level API |
| `tests/test_output_folder.py::test_output_folder` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_output_folder.py::test_exception_when_output_folder_exists` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_pre_prompt_hooks.py::test_run_pre_prompt_python_hook` | upstream | integration | `__prompts__` Key | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_pre_prompt_hooks.py::test_run_pre_prompt_shell_hook` | upstream | integration | `__prompts__` Key | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_prompt.py::test_undefined_variable` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_cookiecutter_nested_templates` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_cookiecutter_nested_templates_invalid_paths` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_cookiecutter_nested_templates_invalid_win_paths` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_prompt_should_ask_and_rm_repo_dir` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_prompt_should_ask_and_exit_on_user_no_answer` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_prompt_should_ask_and_rm_repo_file` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_prompt_should_ask_and_keep_repo_on_no_reuse` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_prompt_should_ask_and_keep_repo_on_reuse` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_prompt_should_not_ask_if_no_input_and_rm_repo_dir` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::test_prompt_should_not_ask_if_no_input_and_rm_repo_file` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestRenderVariable.test_convert_to_str` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestRenderVariable.test_convert_to_str_complex_variables` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_prompt_for_config` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_prompt_for_config_with_human_prompts` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_prompt_for_config_with_human_choices` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_prompt_for_config_dict` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_should_render_dict` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_should_render_deep_dict` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_should_render_deep_dict_with_human_prompts` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_internal_use_no_human_prompts` | upstream | atomic | `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_prompt_for_templated_config` | upstream | atomic | cookiecutter.json Variable Types + Templated Default Values + `__prompts__` Key | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_dont_prompt_for_private_context_var` | upstream | atomic | Private Variables (Single Underscore Prefix) | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_should_render_private_variables_with_two_underscores` | upstream | atomic | Private Rendered Variables (Double Underscore Prefix) | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPrompt.test_should_not_render_private_variables` | upstream | atomic | Private Rendered Variables (Double Underscore Prefix) | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestReadUserChoice.test_should_invoke_read_user_choice` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestReadUserChoice.test_should_invoke_read_user_variable` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestReadUserChoice.test_should_render_choices` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPromptChoiceForConfig.test_should_return_first_option_if_no_input` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPromptChoiceForConfig.test_should_read_user_choice` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestPromptChoiceForConfig.test_empty_list_returns_empty_string` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestReadUserYesNo.test_should_invoke_read_user_yes_no` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_prompt.py::TestReadUserYesNo.test_boolean_parameter_no_input` | upstream | atomic | Boolean Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_repo_password.py::test_click_invocation` | upstream | atomic | CLI + Password-Protected Zip Files | covered | single public behavior or bounded helper API |
| `tests/test_read_user_choice.py::test_click_invocation` | upstream | atomic | CLI | covered | single public behavior or bounded helper API |
| `tests/test_read_user_choice.py::test_raise_if_options_is_not_a_non_empty_list` | upstream | atomic | Choice Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_process_json_invalid_json` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_process_json_non_dict` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_process_json_valid_json` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_process_json_deep_dict` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_should_raise_type_error` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_should_call_prompt_with_process_json` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_should_not_load_json_from_sentinel` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_read_user_dict_default_value` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_dict.py::test_json_prompt_process_response` | upstream | atomic | Dictionary Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_variable.py::test_click_invocation` | upstream | atomic | CLI | covered | single public behavior or bounded helper API |
| `tests/test_read_user_variable.py::test_input_loop_with_null_default_value` | upstream | atomic | String Variables | covered | single public behavior or bounded helper API |
| `tests/test_read_user_yes_no.py::test_click_invocation` | upstream | atomic | CLI | covered | single public behavior or bounded helper API |
| `tests/test_read_user_yes_no.py::test_yesno_prompt_process_response` | upstream | atomic | Boolean Variables | covered | single public behavior or bounded helper API |
| `tests/test_repo_not_found.py::test_should_raise_error_if_repo_does_not_exist` | upstream | atomic | Template Directories and Archives | covered | single public behavior or bounded helper API |
| `tests/test_specify_output_dir.py::test_api_invocation` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_specify_output_dir.py::test_default_output_dir` | upstream | integration | Rendering and File Generation | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_templates.py::test_build_templates` | upstream | integration | `templates` Key (Nested Config, v2.5+) | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_time_extension.py::test_tz_is_required` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_time_extension.py::test_utc_default_datetime_format` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_time_extension.py::test_accept_valid_timezones` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_time_extension.py::test_environment_datetime_format` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_time_extension.py::test_add_time` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_time_extension.py::test_substract_time` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_time_extension.py::test_offset_with_format` | upstream | integration | `cookiecutter.extensions.TimeExtension` | covered | combines context, rendering, files, hooks, extensions, or output policy |
| `tests/test_utils.py::test_force_delete` | upstream | atomic | Public Modules | covered | single public behavior or bounded helper API |
| `tests/test_utils.py::test_rmtree` | upstream | atomic | Public Modules | covered | single public behavior or bounded helper API |
| `tests/test_utils.py::test_make_sure_path_exists` | upstream | atomic | Public Modules | covered | single public behavior or bounded helper API |
| `tests/test_utils.py::test_make_sure_path_exists_correctly_handle_os_error` | upstream | atomic | Exceptions | covered | single public behavior or bounded helper API |
| `tests/test_utils.py::test_work_in` | upstream | atomic | Public Modules | covered | single public behavior or bounded helper API |
| `tests/test_utils.py::test_work_in_without_path` | upstream | atomic | Public Modules | covered | single public behavior or bounded helper API |
| `tests/test_utils.py::test_create_tmp_repo_dir` | upstream | atomic | Public Modules | covered | single public behavior or bounded helper API |

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_copy_without_render_preserves_raw_jinja_content` | generated | integration | Template Structure + `_copy_without_render` Key | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_replay_file_reuses_recorded_answers` | generated | system_e2e | Replay + Cross-View Invariants | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_directory_option_selects_template_subdirectory` | generated | system_e2e | Template Directories and Archives + `--directory` Option | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_zip_archive_template_generates_project` | generated | system_e2e | Template Directories and Archives + Zip Archives | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_jsonify_extension_is_available_without_configuration` | generated | atomic | Built-in Template Extensions + `cookiecutter.extensions.JsonifyExtension` | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_random_string_extension_generates_requested_length` | generated | atomic | Built-in Template Extensions + `cookiecutter.extensions.RandomStringExtension` | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_local_extension_filter_can_be_loaded_from_template_root` | generated | integration | `_extensions` Key + Local Extensions | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_legacy_template_key_selects_old_nested_template_format` | generated | system_e2e | Template Structure + cookiecutter.json Variable Types + `template` Key (Nested Config, v2.2 Old Format) | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_cli_version_reports_cookiecutter_entry_point` | generated | system_e2e | CLI | covered | Retroactive public Cookiecutter behavior test for Gate D coverage. |

Total: 222 | kept (covered): 222 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 222
