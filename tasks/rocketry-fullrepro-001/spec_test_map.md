# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_surface_exposes_application_session_task_condition_and_args` | atomic | Installable Surface | covered |
| 2 | `oracle/test_atomic.py::test_rocketry_constructs_session_with_fixed_main_execution` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_task_decorator_returns_function_and_registers_lookup_by_name_and_function` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_task_declaration_stores_public_metadata` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_functask_constructor_registers_on_supplied_session` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_boolean_conditions_observe_without_context` | atomic | Cross-View Invariants | covered |
| 7 | `oracle/test_atomic.py::test_condition_or_algebra_observes_any_true_branch` | atomic | Cross-View Invariants | covered |
| 8 | `oracle/test_atomic.py::test_condition_and_algebra_requires_all_true_branches` | atomic | Cross-View Invariants | covered |
| 9 | `oracle/test_atomic.py::test_condition_inversion_flips_public_state` | atomic | Cross-View Invariants | covered |
| 10 | `oracle/test_atomic.py::test_nested_condition_algebra_preserves_parenthesized_meaning` | atomic | Cross-View Invariants | covered |
| 11 | `oracle/test_atomic.py::test_custom_condition_observes_wrapped_function_result` | atomic | Cross-View Invariants | covered |
| 12 | `oracle/test_atomic.py::test_custom_condition_accepts_positional_arguments` | atomic | Cross-View Invariants | covered |
| 13 | `oracle/test_atomic.py::test_custom_condition_can_receive_current_task_argument` | atomic | Cross-View Invariants | covered |
| 14 | `oracle/test_atomic.py::test_daily_condition_is_true_for_never_run_task_at_fixed_time` | atomic | Cross-View Invariants | covered |
| 15 | `oracle/test_atomic.py::test_daily_condition_becomes_false_after_success_in_same_fixed_day` | atomic | Cross-View Invariants | covered |
| 16 | `oracle/test_atomic.py::test_time_of_day_between_uses_session_time_function` | atomic | Scope | covered |
| 17 | `oracle/test_atomic.py::test_weekly_condition_matches_fixed_weekday` | atomic | Cross-View Invariants | covered |
| 18 | `oracle/test_atomic.py::test_hourly_after_matches_minute_second_inside_hour` | atomic | Scope | covered |
| 19 | `oracle/test_atomic.py::test_session_level_arg_is_injected_during_direct_run` | atomic | Scope | covered |
| 20 | `oracle/test_atomic.py::test_function_parameter_arg_is_materialized_during_run` | atomic | Scope | covered |
| 21 | `oracle/test_atomic.py::test_simplearg_and_funcarg_are_task_level_values` | atomic | Scope | covered |
| 22 | `oracle/test_atomic.py::test_meta_arguments_expose_session_task_and_config` | atomic | Scope | covered |
| 23 | `oracle/test_atomic.py::test_direct_run_records_return_value_for_string_and_function_return_args` | atomic | Scope | covered |
| 24 | `oracle/test_atomic.py::test_successful_direct_run_updates_status_and_last_success_projection` | atomic | Cross-View Invariants | covered |
| 25 | `oracle/test_atomic.py::test_successful_direct_run_writes_run_and_success_log_actions` | atomic | Cross-View Invariants | covered |
| 26 | `oracle/test_atomic.py::test_task_logger_filter_counts_are_projected_by_action` | atomic | Cross-View Invariants | covered |
| 27 | `oracle/test_atomic.py::test_log_records_share_run_id_between_run_and_success` | atomic | Cross-View Invariants | covered |
| 28 | `oracle/test_atomic.py::test_obey_cond_true_leaves_false_condition_task_unrun` | atomic | Cross-View Invariants | covered |
| 29 | `oracle/test_atomic.py::test_after_success_condition_is_false_before_source_task_succeeds` | atomic | Cross-View Invariants | covered |
| 30 | `oracle/test_atomic.py::test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success` | atomic | Cross-View Invariants | covered |
| 31 | `oracle/test_atomic.py::test_succeeded_status_condition_observes_success_log_in_fixed_period` | atomic | Cross-View Invariants | covered |
| 32 | `oracle/test_atomic.py::test_one_cycle_scheduler_start_uses_public_shutdown_condition` | atomic | Cross-View Invariants | covered |
| 33 | `oracle/test_atomic.py::test_memory_repository_task_records_contain_stable_task_action_and_time_fields` | atomic | Scope | covered |
| 34 | `oracle/test_integration.py::test_priority_pipeline_passes_return_between_two_tasks_in_one_scheduler_cycle` | integration | Representative Workflows | covered |
| 35 | `oracle/test_integration.py::test_session_parameter_and_return_pipeline_produce_joined_payload` | integration | Representative Workflows | covered |
| 36 | `oracle/test_integration.py::test_custom_condition_combines_with_fixed_time_window_to_gate_task` | integration | Cross-View Invariants | covered |
| 37 | `oracle/test_integration.py::test_task_meta_arguments_and_task_sensitive_condition_agree_on_current_task` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_daily_task_runs_once_and_same_day_observation_prevents_second_due_state` | integration | Scope | covered |
| 39 | `oracle/test_integration.py::test_two_successful_tasks_keep_separate_log_run_ids_and_action_counts` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_downstream_condition_is_consumed_after_pipeline_task_runs` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_funcarg_simplearg_and_return_can_build_multistep_payload` | integration | Scope | covered |
| 42 | `oracle/test_integration.py::test_one_cycle_scheduler_skips_false_condition_and_runs_true_condition` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_status_condition_and_log_projection_share_same_success_fact` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_decorated_function_lookup_status_and_return_are_consistent` | integration | Representative Workflows | covered |
| 45 | `oracle/test_integration.py::test_weekly_condition_and_session_parameter_drive_task_payload` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_hourly_window_task_runs_and_projects_log_counts` | integration | Scope | covered |
| 47 | `oracle/test_integration.py::test_condition_algebra_selects_one_of_two_workflow_branches` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_condition_closes_over_session_parameter_mutation_before_run` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_after_success_and_succeeded_conditions_observe_same_upstream_run` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_functask_and_decorator_tasks_share_session_parameters_and_returns` | integration | Product State Model | covered |
| 51 | `oracle/test_integration.py::test_explicit_scheduler_start_runs_declared_tasks_with_fixed_time` | integration | Representative Workflows | covered |
| 52 | `oracle/test_integration.py::test_daily_and_time_of_day_combination_runs_then_becomes_not_due` | integration | Scope | covered |
| 53 | `oracle/test_integration.py::test_three_task_success_chain_projects_status_return_and_logs` | integration | Representative Workflows | covered |
| 54 | `oracle/test_integration.py::test_task_can_return_current_log_count_from_meta_task_argument` | integration | Scope | covered |
| 55 | `oracle/test_integration.py::test_app_param_function_feeds_two_downstream_consumers` | integration | Scope | covered |
| 56 | `oracle/test_integration.py::test_unlisted_downstream_task_remains_unrun_when_manual_run_targets_source_only` | integration | Scope | covered |
| 57 | `oracle/test_integration.py::test_custom_condition_arguments_can_block_scheduler_without_logs` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_return_value_log_time_and_status_survive_same_workflow_projection` | integration | Representative Workflows | covered |
| 59 | `oracle/test_integration.py::test_pipeline_condition_can_be_combined_with_negated_false_condition` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_after_finish_pipeline_passes_return_and_source_log_projection` | integration | Representative Workflows | covered |

final_scoreable: 60
