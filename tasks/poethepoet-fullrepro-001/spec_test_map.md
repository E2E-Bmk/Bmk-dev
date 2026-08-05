# Spec Test Map - poethepoet-fullrepro-001

oracle_version: 2026-08-04-artifact-only-v1
oracle_source: generated_public_contract
oracle_files: oracle/test_atomic.py, oracle/test_integration.py
runtime_requirements: oracle/requirements.txt
reference_source: https://github.com/nat-n/poethepoet
reference_commit: e4d032ce63f6a80cef9b7fc9a956c5f4de04c9b2
stage4_evidence: ARTIFACT_ONLY
counts: atomic=33, integration=32, system_e2e=0, total=65
depends_on_annotation_coverage: 32/32 integration tests
final_scoreable: 65

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `oracle/test_atomic.py::test_public_package_exposes_version_and_main` | generated | atomic | shape | Public Import Surface | covered | public package symbols |
| `oracle/test_atomic.py::test_iter_tasks_returns_public_task_names` | generated | atomic | positive | Product State Model | covered | task discovery |
| `oracle/test_atomic.py::test_builtin_list_tasks_excludes_hidden_tasks` | generated | atomic | positive | Product State Model | covered | built-in discovery |
| `oracle/test_atomic.py::test_string_task_runs_as_command_and_appends_free_args` | generated | atomic | positive | Invocation Protocol | covered | command and free args |
| `oracle/test_atomic.py::test_command_quotes_keep_whitespace_inside_one_argument` | generated | atomic | shape | Invocation Protocol | covered | command parsing |
| `oracle/test_atomic.py::test_command_environment_default_operator_supplies_fallback` | generated | atomic | positive | Cross-View Invariants | covered | environment template |
| `oracle/test_atomic.py::test_command_environment_alternate_operator_uses_presence` | generated | atomic | positive | Cross-View Invariants | covered | environment template |
| `oracle/test_atomic.py::test_single_quoted_dollar_is_not_expanded_by_command_parser` | generated | atomic | positive | Cross-View Invariants | covered | quoted template |
| `oracle/test_atomic.py::test_glob_expansion_matches_project_files` | generated | atomic | positive | Scope | covered | local project files |
| `oracle/test_atomic.py::test_empty_glob_null_removes_unmatched_argument` | generated | atomic | positive | Scope | covered | null glob behavior |
| `oracle/test_atomic.py::test_cwd_option_runs_task_from_requested_directory` | generated | atomic | positive | Product State Model | covered | task working directory |
| `oracle/test_atomic.py::test_capture_stdout_writes_task_output_to_project_file` | generated | atomic | positive | Cross-View Invariants | covered | output capture |
| `oracle/test_atomic.py::test_task_env_values_are_visible_to_subprocess` | generated | atomic | positive | Cross-View Invariants | covered | task environment |
| `oracle/test_atomic.py::test_private_env_can_interpolate_without_leaking_to_process` | generated | atomic | positive | Cross-View Invariants | covered | private variable |
| `oracle/test_atomic.py::test_expected_envfile_loads_variables_for_task` | generated | atomic | positive | Scope | covered | expected envfile |
| `oracle/test_atomic.py::test_optional_envfile_can_be_missing` | generated | atomic | positive | Scope | covered | optional envfile |
| `oracle/test_atomic.py::test_named_argument_default_is_exposed_to_command` | generated | atomic | positive | Invocation Protocol | covered | named argument default |
| `oracle/test_atomic.py::test_positional_argument_is_available_by_name` | generated | atomic | positive | Invocation Protocol | covered | positional argument |
| `oracle/test_atomic.py::test_boolean_argument_toggles_environment_presence` | generated | atomic | positive | Invocation Protocol | covered | boolean argument |
| `oracle/test_atomic.py::test_integer_and_float_arguments_reach_expression_as_typed_values` | generated | atomic | positive | Invocation Protocol | covered | typed arguments |
| `oracle/test_atomic.py::test_choices_reject_unsupported_argument_value` | generated | atomic | failure_path | Error Semantics | covered | invalid choice |
| `oracle/test_atomic.py::test_multiple_option_values_are_joined_for_command_environment` | generated | atomic | positive | Invocation Protocol | covered | repeated option |
| `oracle/test_atomic.py::test_expr_task_prints_expression_result` | generated | atomic | positive | Scope | covered | expression task |
| `oracle/test_atomic.py::test_expr_assert_false_returns_nonzero` | generated | atomic | failure_path | Error Semantics | covered | false expression |
| `oracle/test_atomic.py::test_script_task_receives_typed_arguments` | generated | atomic | positive | Scope | covered | script task |
| `oracle/test_atomic.py::test_script_print_result_outputs_return_value` | generated | atomic | positive | Scope | covered | script return value |
| `oracle/test_atomic.py::test_hidden_task_cannot_be_executed_directly` | generated | atomic | failure_path | Error Semantics | covered | hidden task |
| `oracle/test_atomic.py::test_unknown_task_returns_nonzero_without_running_payload` | generated | atomic | failure_path | Error Semantics | covered | unknown task |
| `oracle/test_atomic.py::test_command_ignore_fail_turns_failure_into_success` | generated | atomic | positive | Error Semantics | covered | ignored command failure |
| `oracle/test_atomic.py::test_help_lists_public_task_with_help_text` | generated | atomic | positive | Product State Model | covered | task help |
| `oracle/test_atomic.py::test_poe_tasks_toml_can_define_tasks_without_tool_namespace` | generated | atomic | positive | Scope | covered | standalone TOML |
| `oracle/test_atomic.py::test_library_app_runs_temp_project_with_explicit_output_stream` | generated | atomic | positive | Public Import Surface | covered | library invocation |
| `oracle/test_atomic.py::test_describe_task_args_reports_choices_and_boolean_type` | generated | atomic | positive | Product State Model | covered | argument description |
| `oracle/test_integration.py::test_sequence_runs_referenced_tasks_in_declared_order` | generated | integration | composition | Representative Workflows | covered | ordered sequence |
| `oracle/test_integration.py::test_sequence_combines_inline_command_script_and_expression` | generated | integration | composition | Representative Workflows | covered | mixed sequence |
| `oracle/test_integration.py::test_sequence_default_item_type_can_treat_strings_as_commands` | generated | integration | composition | Product State Model | covered | sequence item type |
| `oracle/test_integration.py::test_parallel_runs_each_local_subtask` | generated | integration | composition | Representative Workflows | covered | local parallel group |
| `oracle/test_integration.py::test_sequence_waits_for_nested_parallel_group` | generated | integration | composition | Cross-View Invariants | covered | nested graph state |
| `oracle/test_integration.py::test_ref_task_passes_arguments_declared_in_reference` | generated | integration | composition | Representative Workflows | covered | reference arguments |
| `oracle/test_integration.py::test_ref_task_can_run_hidden_task_through_public_alias` | generated | integration | composition | Representative Workflows | covered | hidden reference |
| `oracle/test_integration.py::test_switch_selects_matching_case_from_control_output` | generated | integration | composition | Representative Workflows | covered | switch match |
| `oracle/test_integration.py::test_switch_uses_default_case_when_no_case_matches` | generated | integration | composition | Representative Workflows | covered | switch fallback |
| `oracle/test_integration.py::test_switch_default_pass_allows_no_matching_case` | generated | integration | composition | Error Semantics | covered | switch pass default |
| `oracle/test_integration.py::test_switch_without_match_fails_without_running_a_case` | generated | integration | failure_path | Error Semantics | covered | switch failure |
| `oracle/test_integration.py::test_deps_run_before_task_body` | generated | integration | composition | Cross-View Invariants | covered | dependency ordering |
| `oracle/test_integration.py::test_uses_captures_upstream_output_as_command_variable` | generated | integration | composition | Cross-View Invariants | covered | uses output |
| `oracle/test_integration.py::test_uses_env_parses_upstream_output_into_environment` | generated | integration | composition | Cross-View Invariants | covered | uses env |
| `oracle/test_integration.py::test_envfile_args_cwd_and_capture_project_same_projection` | generated | integration | composition | Representative Workflows | covered | combined task options |
| `oracle/test_integration.py::test_task_env_overrides_task_envfile_value` | generated | integration | composition | Cross-View Invariants | covered | environment precedence |
| `oracle/test_integration.py::test_included_toml_file_contributes_tasks` | generated | integration | composition | Representative Workflows | covered | included task |
| `oracle/test_integration.py::test_include_cwd_changes_conf_dir_for_included_task` | generated | integration | composition | Cross-View Invariants | covered | included working directory |
| `oracle/test_integration.py::test_poe_tasks_json_can_define_tasks_without_tool_namespace` | generated | integration | composition | Scope | covered | standalone JSON |
| `oracle/test_integration.py::test_poe_tasks_yaml_can_define_tasks_without_tool_namespace` | generated | integration | composition | Scope | covered | standalone YAML |
| `oracle/test_integration.py::test_recursive_includes_preserve_existing_root_task_definition` | generated | integration | composition | Cross-View Invariants | covered | include precedence |
| `oracle/test_integration.py::test_global_default_array_item_type_changes_sequence_strings` | generated | integration | composition | Product State Model | covered | global sequence option |
| `oracle/test_integration.py::test_global_default_task_type_can_make_string_task_a_script` | generated | integration | composition | Product State Model | covered | global task type |
| `oracle/test_integration.py::test_dry_run_reports_without_creating_task_side_effect` | generated | integration | positive | Non-Goals | covered | local dry-run effect |
| `oracle/test_integration.py::test_quiet_global_option_suppresses_poe_banner_not_task_output` | generated | integration | positive | Invocation Protocol | covered | global verbosity |
| `oracle/test_integration.py::test_script_task_receives_extra_args_projection` | generated | integration | composition | Invocation Protocol | covered | script free args |
| `oracle/test_integration.py::test_command_extra_args_can_be_placed_with_poe_extra_args` | generated | integration | composition | Invocation Protocol | covered | command free args |
| `oracle/test_integration.py::test_boolean_args_propagate_through_ref_without_host_env` | generated | integration | composition | Cross-View Invariants | covered | reference argument state |
| `oracle/test_integration.py::test_multiple_args_propagate_from_ref_definition` | generated | integration | composition | Cross-View Invariants | covered | reference multiple args |
| `oracle/test_integration.py::test_switch_named_argument_selects_case_and_forwards_extra_args` | generated | integration | composition | Cross-View Invariants | covered | switch argument state |
| `oracle/test_integration.py::test_python_interpreter_shell_task_is_deterministic_public_shell_projection` | generated | integration | positive | Non-Goals | covered | Python shell interpreter |
| `oracle/test_integration.py::test_library_app_run_and_iter_tasks_share_config_projection` | generated | integration | composition | Cross-View Invariants | covered | library and discovery |
