# Spec Test Map - luigi-workflow-fullrepro-001

oracle_version: 2026-07-10T05:40:05+08:00
oracle_source: generated_only
filter/oracle_source: generated_only
scorer_isolation: score_pytest_original.py --remove-path luigi
expected_oracle_max: 60
reference_gate: 60/60 passed on WSL Python 3.11 after filter_iter=2 fairness repair; see filter/reference_score.json
dummy_gate: retained 60/60 tests failed dummy on WSL Python 3.11 with --remove-path luigi after filter_iter=2 fairness repair; see filter/dummy_pytest_report.json

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| filter/generated_tests.py::test_basic_parameter_types_parse_and_serialize_public_values | generated | atomic | ## Installable Surface | covered | top-level Parameter classes are importable from luigi and expose documented parse/serialize behavior |
| filter/generated_tests.py::test_invalid_basic_parameter_values_raise_value_error | generated | atomic | ## Error Semantics | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_date_parameters_parse_documented_shapes | generated | atomic | ### Parameters | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_date_parameter_invalid_input_raises_value_error | generated | atomic | ## Error Semantics | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_list_tuple_and_dict_parameters_parse_json_publicly | generated | atomic | ### Parameters | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_enum_parameter_round_trips_by_member_name | generated | atomic | ### Parameters | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_choice_parameter_accepts_only_configured_values | generated | atomic | ### Parameters | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_numerical_parameter_enforces_bounds | generated | atomic | ### Parameters | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_path_parameter_normalizes_and_checks_existence | generated | atomic | ### Parameters | covered | spec_v2 PathParameter behavior: parse returns strings unchanged; normalize returns Path and enforces exists=True |
| filter/generated_tests.py::test_optional_parameters_parse_empty_string_as_none | generated | atomic | ### Parameters | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_required_parameter_missing_raises_missing_parameter_exception | generated | atomic | ## Error Semantics | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_unknown_keyword_raises_unknown_parameter_exception | generated | atomic | ## Error Semantics | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_duplicate_positional_and_keyword_parameter_raises | generated | atomic | ## Error Semantics | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_insignificant_parameter_is_omitted_from_identity_and_public_strings | generated | atomic | ### Parameters | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_parameter_visibility_controls_public_serialization_without_changing_attribute | generated | atomic | ## Cross-View Invariants | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_from_str_params_parses_string_mapping_and_falls_back_to_defaults | generated | atomic | ## Installable Surface | covered | top-level Task and Parameter imports interoperate through documented string-parameter construction |
| filter/generated_tests.py::test_task_equality_uses_class_and_significant_public_values | generated | atomic | ## Public API | covered | public Task identity behavior is part of the documented API surface |
| filter/generated_tests.py::test_task_family_uses_namespace_and_class_name | generated | atomic | ### Tasks | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_task_input_preserves_nested_dependency_output_shape | generated | integration | ### Tasks | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_task_complete_false_without_outputs_and_true_when_local_output_exists | generated | atomic | ### Tasks | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_task_complete_raises_when_output_has_no_exists_method | generated | atomic | ## Error Semantics | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_external_task_has_no_run_method_and_missing_output_is_incomplete | generated | atomic | ### Tasks | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_wrapper_task_complete_reflects_requirements | generated | integration | ### Tasks | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_dynamic_requirements_complete_uses_wrapped_requirements | generated | integration | ### Tasks | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_local_target_write_creates_parent_and_commits_on_close | generated | integration | ### Targets | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_local_target_rejects_missing_path_unless_temporary | generated | atomic | ## Error Semantics | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_local_target_move_copy_remove_and_exists | generated | integration | ### Targets | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_build_runs_dependencies_then_downstream_and_reuses_existing_outputs | generated | system_e2e | ### Execution APIs | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_build_detailed_summary_reports_failed_task | generated | system_e2e | ### Execution APIs | covered | uses documented top-level luigi.LuigiStatusCode and documented LuigiRunResult import |
| filter/generated_tests.py::test_build_reports_missing_external_dependency_without_running_dependent | generated | system_e2e | ## Cross-View Invariants | covered | uses documented top-level luigi.LuigiStatusCode |
| filter/generated_tests.py::test_run_accepts_cmdline_args_and_main_task_cls | generated | integration | ### Execution APIs | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_cli_module_invocation_runs_local_scheduler_task | generated | system_e2e | ### Command Line | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_cli_hyphenated_parameter_name_maps_to_underscore_attribute | generated | system_e2e | ### Command Line | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_cli_class_qualified_parameter_supplies_dependency_value | generated | system_e2e | ### Command Line | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_config_file_supplies_task_parameter_default | generated | integration | ### Configuration | covered | observes config-file parameter defaults through documented Task construction |
| filter/generated_tests.py::test_constructor_value_overrides_config_value | generated | integration | ### Configuration | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_config_class_reads_values_from_matching_section | generated | integration | ### Configuration | covered | observes matching config section through documented Config construction |
| filter/generated_tests.py::test_config_environment_interpolation_uses_environment_variable | generated | integration | ### Configuration | covered | observes cfg environment interpolation through documented task config_path resolution |
| filter/generated_tests.py::test_toml_config_parser_reads_luigi_config_path | generated | integration | ### Configuration | covered | observes toml LUIGI_CONFIG_PATH parsing through documented Task construction |
| filter/generated_tests.py::test_failed_run_calls_on_failure_callback_and_reports_failed_status | generated | system_e2e | ## Cross-View Invariants | covered | uses documented top-level luigi.LuigiStatusCode |
| filter/generated_tests.py::test_event_handler_can_be_registered_triggered_and_removed | generated | integration | ## Public API | covered | event registration/removal is exposed through the documented Task public API |
| filter/generated_tests.py::test_priority_affects_ready_task_order_after_dependencies_are_satisfied | generated | system_e2e | ### Execution APIs | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_dynamic_dependency_yield_restarts_task_and_uses_dependency_output | generated | system_e2e | ## Cross-View Invariants | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_representative_workflow_build_and_second_build_agree_on_completion | generated | system_e2e | ## Representative Workflow | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_python_and_cli_projection_create_same_workflow_outputs | generated | system_e2e | ## Product State Model | covered | compares Python and command-line projections of the same workflow state |
| filter/generated_tests.py::test_task_without_declared_output_does_not_unlock_downstream_as_complete | generated | system_e2e | ## Cross-View Invariants | covered | uses documented top-level luigi.LuigiStatusCode |
| filter/generated_tests.py::test_requires_returning_target_is_reported_as_scheduling_failure | generated | atomic | ## Error Semantics | covered | no status-code import required; assertion is public build exception behavior |
| filter/generated_tests.py::test_complete_failure_is_reported_as_scheduling_failure | generated | system_e2e | ## Error Semantics | covered | uses documented top-level luigi.LuigiStatusCode |
| filter/generated_tests.py::test_worker_scheduler_factory_methods_are_used | generated | system_e2e | ### Execution APIs | covered | verifies documented factory hooks using public sentinel exceptions without scheduler/worker module imports |
| filter/generated_tests.py::test_python_module_invocation_matches_luigi_command_shape_for_local_scheduler | generated | system_e2e | ## Invocation Protocol | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_summary_text_and_boolean_result_reflect_successful_workflow | generated | system_e2e | ## Product State Model | covered | uses documented top-level luigi.LuigiStatusCode |
| filter/generated_tests.py::test_private_parameter_is_not_exposed_in_public_str_params_but_remains_attribute | generated | atomic | ## Cross-View Invariants | covered | public reference-observed behavior within scoped Luigi core workflow surface |
| filter/generated_tests.py::test_installable_surface_top_level_task_parameter_target_and_build_work | generated | system_e2e | ## Installable Surface | covered | top-level Task, Parameter, LocalTarget, and build imports execute a local workflow |
| filter/generated_tests.py::test_product_state_model_parameter_identity_visible_across_projections | generated | atomic | ## Product State Model | covered | parameter value is visible through attribute access, serialized task parameters, and representation |
| filter/generated_tests.py::test_installable_surface_documented_parameter_exceptions_match_task_construction | generated | atomic | ## Public API | covered | documented parameter exception imports are raised by public task construction errors |
| filter/generated_tests.py::test_filesystem_target_temporary_path_commits_and_rolls_back | generated | integration | ### Targets | covered | FileSystemTarget temporary_path commits on success and does not commit after an exception |
| filter/generated_tests.py::test_invocation_protocol_python_module_class_qualified_dependency_flag | generated | system_e2e | ## Invocation Protocol | covered | python -m luigi supports module import, root task resolution, local scheduler, and class-qualified dependency flags |
| filter/generated_tests.py::test_invocation_protocol_python_module_hyphenated_root_flag | generated | system_e2e | ## Invocation Protocol | covered | python -m luigi accepts hyphenated task parameters in the documented invocation shape |
| filter/generated_tests.py::test_representative_workflow_input_target_feeds_downstream_task | generated | system_e2e | ## Representative Workflow | covered | dependency output is passed through input() and consumed by downstream local workflow work |
| filter/generated_tests.py::test_representative_workflow_cli_invocation_writes_downstream_output | generated | system_e2e | ## Representative Workflow | covered | representative DailyWords -> CountLetters workflow runs through python -m luigi with local scheduler |

Total: 60 | kept (covered): 60 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 60
Covered by layer: atomic=26 | integration=13 | system_e2e=21

