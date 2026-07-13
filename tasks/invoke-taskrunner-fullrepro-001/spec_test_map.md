# Spec Test Map

oracle_source: upstream
track_a_source: filter/rewritten_upstream_tests.py
track_b_source: none
oracle_version: 2026-07-03-s3-track-a

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| `filter/rewritten_upstream_tests.py::test_task_decorator_bare_wraps_callable_with_public_name` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_task_decorator_options_set_name_aliases_and_default` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_task_decorator_rejects_positional_pretasks_and_pre_keyword` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_task_call_requires_context_as_first_argument` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_task_call_marks_task_as_called_after_success` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_task_arguments_drop_context_and_dash_underscores` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_task_boolean_true_default_creates_inverse_flag` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_task_optional_iterable_and_incrementable_argument_metadata` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_call_helper_stores_task_args_and_kwargs` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_call_clone_is_independent_and_can_replace_data` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_call_make_context_uses_config_and_remainder` | upstream | atomic | Tasks | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_add_task_binds_name_alias_and_lookup` | upstream | atomic | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_empty_lookup_returns_default_task` | upstream | atomic | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_rejects_second_default_task` | upstream | atomic | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_dotted_subcollection_lookup_and_default` | upstream | atomic | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_task_names_include_dotted_names_aliases_and_defaults` | upstream | atomic | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_configuration_merges_parent_over_child_for_path` | upstream | atomic | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_from_module_prefers_explicit_namespace` | upstream | integration | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_collection_from_module_uses_top_level_tasks_without_namespace` | upstream | integration | Collections and Namespaces | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_config_supports_dict_and_attribute_access` | upstream | atomic | Configuration | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_config_real_attributes_take_precedence_over_config_keys` | upstream | atomic | Configuration | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_config_clone_preserves_values_without_sharing_runtime_changes` | upstream | atomic | Configuration | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_config_load_overrides_beats_defaults` | upstream | atomic | Configuration | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_config_environment_casts_existing_boolean_and_numeric_defaults` | upstream | integration | Configuration | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_config_unknown_runtime_file_extension_raises` | upstream | atomic | Configuration | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_run_uses_configured_local_runner_class` | upstream | integration | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_invoke_run_creates_anonymous_context_and_returns_result` | upstream | integration | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_run_warn_true_returns_failed_result` | upstream | integration | Error Semantics | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_run_warn_false_raises_unexpected_exit` | upstream | integration | Error Semantics | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_run_dry_returns_success_without_running_command` | upstream | integration | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_cd_changes_cwd_for_command` | upstream | integration | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_prefix_runs_before_command` | upstream | integration | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_result_truth_return_code_and_default_env` | upstream | atomic | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_result_tail_returns_requested_stream_lines` | upstream | atomic | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_mock_context_returns_prepared_string_and_boolean_results` | upstream | atomic | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_mock_context_raises_when_no_prepared_result_matches` | upstream | atomic | Contexts, Runners, and Results | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_stream_watcher_base_submit_is_not_implemented` | upstream | atomic | Watchers and Prompt Responses | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_responder_yields_response_for_regex_match` | upstream | atomic | Watchers and Prompt Responses | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_responder_consumes_each_stream_segment_once` | upstream | atomic | Watchers and Prompt Responses | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_failing_responder_raises_after_response_sentinel` | upstream | atomic | Watchers and Prompt Responses | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_run_watcher_responds_to_prompt_and_preserves_output` | upstream | integration | Watchers and Prompt Responses | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_run_wraps_failing_watcher_in_failure` | upstream | integration | Watchers and Prompt Responses | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_json_list_reports_tasks_aliases_and_default` | upstream | integration | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_invokes_default_task_when_no_task_name_is_given` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_explicit_collection_module_replaces_tasks_default` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_delivers_dashed_flag_to_underscored_python_argument` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_inverse_boolean_flag_sets_false` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_optional_argument_accepts_bare_flag_and_value` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_iterable_argument_accumulates_repeated_values` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_incrementable_argument_counts_repetitions` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_runs_pre_and_post_tasks_around_requested_task` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_dedupes_repeated_task_calls_by_default` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_no_dedupe_allows_repeated_task_calls` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_remainder_after_double_dash_reaches_context` | upstream | system_e2e | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_project_config_is_visible_to_task_context` | upstream | system_e2e | Cross-View Invariants | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_environment_variable_overrides_existing_config_key` | upstream | system_e2e | Cross-View Invariants | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_runtime_config_file_overrides_project_config` | upstream | system_e2e | Cross-View Invariants | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_run_flag_overrides_config_for_task_commands` | upstream | system_e2e | Cross-View Invariants | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_help_for_task_includes_docstring_and_task_option` | upstream | integration | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_unknown_task_exits_unsuccessfully` | upstream | integration | Error Semantics | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_python_module_invocation_runs_same_program` | upstream | integration | Invocation Protocol | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_program_run_string_argv_and_exit_false_do_not_raise_system_exit` | upstream | integration | Invocation Protocol | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_program_run_unknown_task_with_exit_false_returns_without_system_exit` | upstream | integration | Invocation Protocol | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_flat_list_uses_dotted_names_for_nested_collections` | upstream | integration | CLI Behavior | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_cli_list_depth_with_json_is_an_error` | upstream | integration | Error Semantics | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_context_sudo_runtime_password_builds_prompt_responder` | upstream | integration | Watchers and Prompt Responses | covered | public-API rewrite of upstream behavior |
| `filter/rewritten_upstream_tests.py::test_sudo_rejected_response_translates_to_auth_failure` | upstream | integration | Error Semantics | covered | public-API rewrite of upstream behavior |

Total: 67 | kept (covered): 67 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 67
