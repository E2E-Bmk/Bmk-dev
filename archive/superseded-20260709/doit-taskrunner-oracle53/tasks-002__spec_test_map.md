---
task_id: doit-taskrunner-fullrepro-001
spec: spec_v1.md
filter/oracle_source: generated_only
track_a_upstream_nodeids: 0
track_b_generated_nodeids: 53
---

# Spec Test Map

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| generated_tests.py::test_get_var_reads_cli_variable_during_task_loading | generated | atomic | Command Line | covered | name=value CLI variables are visible through the public get_var API during dodo loading. |
| generated_tests.py::test_get_var_uses_default_for_absent_initialized_variable | generated | atomic | Public API | covered | get_var returns the declared default when the variable is absent. |
| generated_tests.py::test_task_params_long_option_is_injected_into_task_creator | generated | atomic | Public API | covered | task_params exposes public task parameters as CLI options passed into the task creator. |
| generated_tests.py::test_create_after_materializes_selected_delayed_task | generated | integration | Task Definitions | covered | create_after materializes delayed tasks after the prerequisite task executes and preserves target dependency behavior. |
| generated_tests.py::test_module_task_loader_runs_dictionary_namespace_with_doitmain | generated | integration | Extension Surfaces | covered | ModuleTaskLoader and DoitMain run tasks supplied through a public dictionary namespace. |
| generated_tests.py::test_generator_subtasks_are_runnable_and_visible_when_requested | generated | integration | Task Definitions | covered | Generator tasks expose named subtasks and selected subtasks run independently. |
| generated_tests.py::test_invalid_task_dictionary_returns_command_error_without_running | generated | atomic | Error Semantics | covered | Invalid task dictionaries produce a command error instead of executing an invalid task. |
| generated_tests.py::test_python_action_dictionary_result_feeds_getargs | generated | integration | Actions and Results | covered | Dictionary results from one task action are made available to another task through getargs. |
| generated_tests.py::test_cmdaction_save_out_stores_stdout_for_later_getargs | generated | integration | Actions and Results | covered | CmdAction(save_out=...) stores stdout for later getargs consumption. |
| generated_tests.py::test_python_action_receives_declared_dependencies_and_targets | generated | atomic | Actions and Results | covered | Python actions receive declared dependency and target path lists. |
| generated_tests.py::test_file_dependency_unchanged_second_run_is_reported_up_to_date | generated | integration | Dependencies and Up-To-Date Status | covered | Unchanged file dependencies and existing targets make a second run up to date. |
| generated_tests.py::test_file_dependency_content_change_reruns_task | generated | integration | Dependencies and Up-To-Date Status | covered | Changing a file dependency causes the dependent task to rerun and refresh its target. |
| generated_tests.py::test_modifying_target_without_input_change_does_not_force_rerun | generated | integration | Dependencies and Up-To-Date Status | covered | Target content changes alone do not force rerun when dependency state is unchanged. |
| generated_tests.py::test_missing_target_forces_rerun_and_restores_file | generated | integration | Dependencies and Up-To-Date Status | covered | Missing targets force a rerun even when dependencies are unchanged. |
| generated_tests.py::test_setup_task_runs_only_when_selected_task_will_execute | generated | integration | Task Definitions | covered | Setup tasks run as part of executing a selected task that will execute. |
| generated_tests.py::test_implicit_target_dependency_runs_producer_before_consumer | generated | system_e2e | Cross-View Invariants | covered | A file target produced by one task satisfies another task file dependency and orders execution. |
| generated_tests.py::test_reset_dep_records_changed_dependency_state_without_action_execution | generated | integration | Command Line | covered | reset-dep updates dependency state without running the task action. |
| generated_tests.py::test_clean_dry_run_reports_without_removing_target | generated | integration | Command Line | covered | Clean dry-run reports removable targets while preserving files. |
| generated_tests.py::test_clean_callable_receives_dryrun_when_declared | generated | atomic | Task Definitions | covered | Callable clean actions that accept dryrun receive the dry-run flag. |
| generated_tests.py::test_list_status_changes_from_run_to_up_to_date | generated | integration | Command Line | covered | list --status reflects run-needed and up-to-date task states. |
| generated_tests.py::test_info_reports_missing_target_as_reason_to_run | generated | atomic | Command Line | covered | info reports missing targets as reasons a task must run. |
| generated_tests.py::test_ignore_persists_skip_and_forget_clears_it | generated | integration | Command Line | covered | ignore persists a skipped task state and forget clears it. |
| generated_tests.py::test_forget_makes_successful_task_run_again | generated | integration | Command Line | covered | forget removes successful run state so the task executes again. |
| generated_tests.py::test_dumpdb_exposes_success_state_and_saved_values | generated | atomic | Command Line | covered | dumpdb exposes recorded task success state and saved action values. |
| generated_tests.py::test_default_command_and_explicit_run_execute_same_default_task | generated | system_e2e | Command Line | covered | Default invocation and explicit run execute configured default tasks consistently. |
| generated_tests.py::test_selecting_by_target_runs_owning_task | generated | integration | Command Line | covered | Selecting an output target runs the task that owns the target. |
| generated_tests.py::test_wildcard_selection_runs_matching_tasks_only | generated | integration | Command Line | covered | Wildcard task selection runs matching tasks and does not run nonmatching tasks. |
| generated_tests.py::test_single_option_skips_task_dependencies | generated | integration | Command Line | covered | run --single executes only the selected task and skips dependencies. |
| generated_tests.py::test_json_reporter_reports_same_task_success_as_console_side_effect | generated | system_e2e | Cross-View Invariants | covered | JSON reporter output agrees with the file side effect of the executed task. |
| generated_tests.py::test_run_once_skips_after_success_but_missing_target_still_runs | generated | integration | Built-In Tools | covered | run_once records success, but missing targets still force execution. |
| generated_tests.py::test_config_changed_treats_same_dictionary_content_as_up_to_date | generated | atomic | Built-In Tools | covered | config_changed treats equal dictionary content as unchanged regardless of insertion order. |
| generated_tests.py::test_config_changed_reruns_when_configuration_changes | generated | atomic | Built-In Tools | covered | config_changed reruns tasks when the tracked configuration value changes. |
| generated_tests.py::test_result_dep_reruns_consumer_when_producer_result_changes | generated | system_e2e | Dependencies and Up-To-Date Status | covered | result_dep connects producer result changes to consumer rerun behavior. |
| generated_tests.py::test_create_folder_action_helper_creates_nested_directory | generated | atomic | Built-In Tools | covered | create_folder creates nested directories as a public action helper. |
| generated_tests.py::test_string_command_action_creates_target_file | generated | atomic | Actions and Results | covered | String shell actions execute and produce their declared target file. |
| generated_tests.py::test_list_command_action_without_shell_accepts_pathlike_arguments | generated | atomic | Actions and Results | covered | List-form command actions execute without shell formatting and accept pathlib targets. |
| generated_tests.py::test_python_action_returning_false_reports_task_failure | generated | atomic | Error Semantics | covered | A Python action returning False reports a task failure with return code 1. |
| generated_tests.py::test_python_action_exception_reports_task_error | generated | atomic | Error Semantics | covered | A Python action raising an exception reports a task error with return code 2. |
| generated_tests.py::test_command_action_nonzero_exit_reports_failure | generated | atomic | Error Semantics | covered | A command action exiting nonzero up to 125 reports task failure. |
| generated_tests.py::test_verbosity_two_displays_python_action_stdout | generated | integration | Actions and Results | covered | Task verbosity 2 displays Python action stdout immediately. |
| generated_tests.py::test_positional_arguments_are_passed_to_declared_action_name | generated | integration | Command Line | covered | Task positional arguments are passed to the action argument named by pos_arg. |
| generated_tests.py::test_task_params_short_boolean_inverse_can_disable_default | generated | atomic | Configuration | covered | Boolean task parameters with an inverse flag can disable the default value. |
| generated_tests.py::test_list_hides_private_tasks_until_requested | generated | integration | Command Line | covered | list hides private tasks by default and shows them when requested. |
| generated_tests.py::test_help_task_prints_supported_task_dictionary_fields | generated | atomic | Command Line | covered | help task prints documented task dictionary fields. |
| generated_tests.py::test_always_execute_forces_rerun_even_when_up_to_date | generated | integration | Command Line | covered | run --always-execute forces execution even when freshness says up-to-date. |
| generated_tests.py::test_continue_runs_independent_task_after_failure | generated | system_e2e | Command Line | covered | run --continue schedules independent work after a selected task fails. |
| generated_tests.py::test_clean_true_removes_target_file | generated | integration | Command Line | covered | clean=True removes an existing generated target file. |
| generated_tests.py::test_clean_forget_clears_success_state_so_task_runs_again | generated | integration | Cross-View Invariants | covered | clean --forget removes output and stored success state so the task runs again. |
| generated_tests.py::test_doit_config_verbosity_changes_action_output_capture | generated | integration | Configuration | covered | DOIT_CONFIG verbosity affects CLI action output capture. |
| generated_tests.py::test_pyproject_default_tasks_selects_configured_task | generated | system_e2e | Configuration | covered | Configured default_tasks selects the default task graph for bare doit invocation. |
| generated_tests.py::test_action_string_new_format_uses_dependencies_placeholder | generated | integration | Actions and Results | covered | New action string formatting substitutes dependencies into command strings. |
| generated_tests.py::test_calc_dep_adds_late_file_dependency | generated | system_e2e | Dependencies and Up-To-Date Status | covered | calc_dep adds late file dependency metadata that affects later freshness checks. |
| generated_tests.py::test_teardown_runs_after_selected_task | generated | integration | Task Definitions | covered | Teardown actions run after the selected task action completes. |

Total: 53 | kept (covered): 53 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 53
Covered by layer: atomic=18 | integration=28 | system_e2e=7

2026-07-02 rescue note: expanded generated-only oracle from 34 to 53 behavioral tests after repairing the JSON reporter overconstraint; reference gate is 53/53 and dummy gate is 0/53.
