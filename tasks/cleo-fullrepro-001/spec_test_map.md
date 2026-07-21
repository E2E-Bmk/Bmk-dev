# Spec-Test Map

oracle_version: 2026-07-20-native-v2-fairness
spec_version: v1
filter/oracle_source: upstream_rewritten
scorer_isolation: task-local native tests with candidate solution first on PYTHONPATH

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_atomic.py::test_optional_non_list_argument | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_argument.py::test_optional_non_list_argument |
| oracle/test_atomic.py::test_required_non_list_argument | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_argument.py::test_required_non_list_argument |
| oracle/test_atomic.py::test_list_argument | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_argument.py::test_list_argument |
| oracle/test_atomic.py::test_parse_arguments | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_arguments |
| oracle/test_atomic.py::test_parse_options[args0-options0-expected_options0] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args0-options0-expected_options0] |
| oracle/test_atomic.py::test_parse_options[args1-options1-expected_options1] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args1-options1-expected_options1] |
| oracle/test_atomic.py::test_parse_options[args2-options2-expected_options2] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args2-options2-expected_options2] |
| oracle/test_atomic.py::test_parse_options[args3-options3-expected_options3] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args3-options3-expected_options3] |
| oracle/test_atomic.py::test_parse_options[args4-options4-expected_options4] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args4-options4-expected_options4] |
| oracle/test_atomic.py::test_parse_options[args5-options5-expected_options5] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args5-options5-expected_options5] |
| oracle/test_atomic.py::test_parse_options[args6-options6-expected_options6] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args6-options6-expected_options6] |
| oracle/test_atomic.py::test_parse_options[args7-options7-expected_options7] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args7-options7-expected_options7] |
| oracle/test_atomic.py::test_parse_options[args8-options8-expected_options8] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args8-options8-expected_options8] |
| oracle/test_atomic.py::test_parse_options[args9-options9-expected_options9] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args9-options9-expected_options9] |
| oracle/test_atomic.py::test_parse_options[args10-options10-expected_options10] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args10-options10-expected_options10] |
| oracle/test_atomic.py::test_parse_options[args11-options11-expected_options11] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args11-options11-expected_options11] |
| oracle/test_atomic.py::test_parse_options[args12-options12-expected_options12] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args12-options12-expected_options12] |
| oracle/test_atomic.py::test_parse_options[args13-options13-expected_options13] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args13-options13-expected_options13] |
| oracle/test_atomic.py::test_parse_options[args14-options14-expected_options14] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args14-options14-expected_options14] |
| oracle/test_atomic.py::test_parse_options[args15-options15-expected_options15] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args15-options15-expected_options15] |
| oracle/test_atomic.py::test_parse_options[args16-options16-expected_options16] | upstream_rewritten | atomic | Input Parsing | covered | source: tests/io/inputs/test_argv_input.py::test_parse_options[args16-options16-expected_options16] |
| oracle/test_atomic.py::test_create | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_create |
| oracle/test_atomic.py::test_dashed_name | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_dashed_name |
| oracle/test_atomic.py::test_fail_if_name_is_empty | upstream_rewritten | atomic | Error Semantics | covered | source: tests/io/inputs/test_option.py::test_fail_if_name_is_empty |
| oracle/test_atomic.py::test_fail_if_default_value_provided_for_flag | upstream_rewritten | atomic | Error Semantics | covered | source: tests/io/inputs/test_option.py::test_fail_if_default_value_provided_for_flag |
| oracle/test_atomic.py::test_fail_if_wrong_default_value_for_list_option | upstream_rewritten | atomic | Error Semantics | covered | source: tests/io/inputs/test_option.py::test_fail_if_wrong_default_value_for_list_option |
| oracle/test_atomic.py::test_shortcut | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_shortcut |
| oracle/test_atomic.py::test_dashed_shortcut | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_dashed_shortcut |
| oracle/test_atomic.py::test_multiple_shortcuts | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_multiple_shortcuts |
| oracle/test_atomic.py::test_fail_if_shortcut_is_empty | upstream_rewritten | atomic | Error Semantics | covered | source: tests/io/inputs/test_option.py::test_fail_if_shortcut_is_empty |
| oracle/test_atomic.py::test_optional_value | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_optional_value |
| oracle/test_atomic.py::test_optional_value_with_default | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_optional_value_with_default |
| oracle/test_atomic.py::test_required_value | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_required_value |
| oracle/test_atomic.py::test_required_value_with_default | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_required_value_with_default |
| oracle/test_atomic.py::test_list | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_list |
| oracle/test_atomic.py::test_multi_valued_with_default | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/io/inputs/test_option.py::test_multi_valued_with_default |
| oracle/test_atomic.py::test_has | upstream_rewritten | atomic | Events, Loaders, and Testers | covered | source: tests/loaders/test_factory_command_loader.py::test_has |
| oracle/test_atomic.py::test_get | upstream_rewritten | atomic | Events, Loaders, and Testers | covered | source: tests/loaders/test_factory_command_loader.py::test_get |
| oracle/test_atomic.py::test_get_invalid_command_raises_error | upstream_rewritten | atomic | Error Semantics | covered | source: tests/loaders/test_factory_command_loader.py::test_get_invalid_command_raises_error |
| oracle/test_atomic.py::test_names | upstream_rewritten | atomic | Events, Loaders, and Testers | covered | source: tests/loaders/test_factory_command_loader.py::test_names |
| oracle/test_atomic.py::test_set_application | upstream_rewritten | atomic | Command | covered | source: tests/commands/test_command.py::test_set_application |
| oracle/test_atomic.py::test_name_version_getters | upstream_rewritten | atomic | Application | covered | source: tests/test_application.py::test_name_version_getters |
| oracle/test_atomic.py::test_name_version_setter | upstream_rewritten | atomic | Application | covered | source: tests/test_application.py::test_name_version_setter |
| oracle/test_atomic.py::test_argument | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/test_helpers.py::test_argument |
| oracle/test_atomic.py::test_option | upstream_rewritten | atomic | Arguments, Options, and Input Definitions | covered | source: tests/test_helpers.py::test_option |
| oracle/test_integration.py::test_dispatch | upstream_rewritten | integration | Events, Loaders, and Testers | covered | source: tests/events/test_event_dispatcher.py::test_dispatch; behaviorally rewritten through Application event dispatch |
| oracle/test_integration.py::test_explicit_multiple_argument | upstream_rewritten | integration | Command | covered | source: tests/commands/test_command.py::test_explicit_multiple_argument |
| oracle/test_integration.py::TestApplicationTester::test_execute | upstream_rewritten | system_e2e | Command With Argument and Flag Option | covered | source: tests/testers/test_application_tester.py::test_execute |
| oracle/test_integration.py::TestApplicationTester::test_execute_namespace_command | upstream_rewritten | system_e2e | Cross-View Invariants | covered | source: tests/testers/test_application_tester.py::test_execute_namespace_command |
| oracle/test_integration.py::TestCommandTester::test_execute | upstream_rewritten | system_e2e | Output, Formatting, and IO | covered | source: tests/testers/test_command_tester.py::test_execute |
| oracle/test_integration.py::TestCommandTester::test_execute_namespace_command | upstream_rewritten | system_e2e | Output, Formatting, and IO | covered | source: tests/testers/test_command_tester.py::test_execute_namespace_command |
| oracle/test_integration.py::test_ask[-True-True] | upstream_rewritten | integration | Interactive Question | covered | source: tests/ui/test_confirmation_question.py::test_ask[-True-True] |
| oracle/test_integration.py::test_ask[-False-False] | upstream_rewritten | integration | Interactive Question | covered | source: tests/ui/test_confirmation_question.py::test_ask[-False-False] |
| oracle/test_integration.py::test_ask[y-True-True] | upstream_rewritten | integration | Interactive Question | covered | source: tests/ui/test_confirmation_question.py::test_ask[y-True-True] |
| oracle/test_integration.py::test_ask[yes-True-True] | upstream_rewritten | integration | Formatting Styles and Helpers | covered | source: tests/ui/test_confirmation_question.py::test_ask[yes-True-True] |
| oracle/test_integration.py::test_ask[n-False-True] | upstream_rewritten | integration | Formatting Styles and Helpers | covered | source: tests/ui/test_confirmation_question.py::test_ask[n-False-True] |
| oracle/test_integration.py::test_ask[no-False-True] | upstream_rewritten | integration | Formatting Styles and Helpers | covered | source: tests/ui/test_confirmation_question.py::test_ask[no-False-True] |
| oracle/test_integration.py::test_ask_with_custom_answer | upstream_rewritten | integration | Formatting Styles and Helpers | covered | source: tests/ui/test_confirmation_question.py::test_ask_with_custom_answer |
| oracle/test_integration.py::test_display_with_quiet_verbosity | upstream_rewritten | integration | Output, Formatting, and IO | covered | source: tests/ui/test_progress_bar.py::test_display_with_quiet_verbosity |
| oracle/test_integration.py::test_ask_and_validate | upstream_rewritten | integration | Formatting Styles and Helpers | covered | source: tests/ui/test_question.py::test_ask_and_validate |
| oracle/test_integration.py::test_no_interaction | upstream_rewritten | integration | Output, Formatting, and IO | covered | source: tests/ui/test_question.py::test_no_interaction |
| oracle/test_application.py::test_with_signature | upstream_rewritten | atomic | Command | covered | source: tests/commands/test_command.py::test_with_signature |
| oracle/test_application.py::test_all | upstream_rewritten | integration | Application | covered | source: tests/test_application.py::test_all |
| oracle/test_application.py::test_add | upstream_rewritten | integration | Product State Model | covered | source: tests/test_application.py::test_add |
| oracle/test_application.py::test_has_get | upstream_rewritten | integration | Product State Model | covered | source: tests/test_application.py::test_has_get |
| oracle/test_application.py::test_silent_help | upstream_rewritten | integration | Output, Formatting, and IO | covered | source: tests/test_application.py::test_silent_help |
| oracle/test_application.py::test_get_namespaces | upstream_rewritten | integration | Application | covered | source: tests/test_application.py::test_get_namespaces |
| oracle/test_application.py::test_find_namespace | upstream_rewritten | integration | Application | covered | source: tests/test_application.py::test_find_namespace |
| oracle/test_application.py::test_find_namespace_with_sub_namespaces | upstream_rewritten | integration | Application | covered | source: tests/test_application.py::test_find_namespace_with_sub_namespaces |
| oracle/test_application.py::test_find | upstream_rewritten | integration | Application | covered | source: tests/test_application.py::test_find |
| oracle/test_application.py::test_auto_exit | upstream_rewritten | atomic | Application | covered | source: tests/test_application.py::test_auto_exit |
| oracle/test_application.py::test_run | upstream_rewritten | system_e2e | Product State Model | covered | source: tests/test_application.py::test_run |
| oracle/test_application.py::test_run_removes_all_output_if_quiet | upstream_rewritten | system_e2e | Cross-View Invariants | covered | source: tests/test_application.py::test_run_removes_all_output_if_quiet |
| oracle/test_application.py::test_run_with_verbosity | upstream_rewritten | system_e2e | Cross-View Invariants | covered | source: tests/test_application.py::test_run_with_verbosity |
| oracle/test_application.py::test_run_with_input | upstream_rewritten | system_e2e | Representative Workflows | covered | source: tests/test_application.py::test_run_with_input |
| oracle/test_application.py::test_run_namespaced_with_input | upstream_rewritten | system_e2e | Representative Workflows | covered | source: tests/test_application.py::test_run_namespaced_with_input |
| oracle/test_application.py::test_run_with_input_and_non_interactive[cmd0] | upstream_rewritten | system_e2e | Cross-View Invariants | covered | source: tests/test_application.py::test_run_with_input_and_non_interactive[cmd0] |
| oracle/test_application.py::test_run_with_input_and_non_interactive[cmd1] | upstream_rewritten | system_e2e | Cross-View Invariants | covered | source: tests/test_application.py::test_run_with_input_and_non_interactive[cmd1] |
| oracle/test_application.py::test_invalid_shell | upstream_rewritten | integration | Error Semantics | covered | source: tests/commands/completion/test_completions_command.py::test_invalid_shell |

Total: 79 | kept: 79 | spec_gap: 0 | source-only: 0 | excluded: 8 | final_scoreable: 79

## Fairness Corrections

- `test_dispatch` is retained as an application-level command/terminate event workflow. It no longer imports or constructs the unpublished `cleo.events.event.Event` base class.
- `test_parse_options` constructs each definition inside the test call. This preserves all parameterized identities while preventing one constructor mismatch from blocking unrelated atomic cases at collection time.

## Excluded Event Cases

| source_nodeid | status | reason |
|---|---|---|
| tests/events/test_event.py::test_is_propagation_not_stopped | excluded | The base `Event` class and its propagation state are not part of the installable surface. |
| tests/events/test_event.py::test_stop_propagation_and_is_propagation_stopped | excluded | The base `Event` class and propagation-control methods are not specified. |
| tests/events/test_event_dispatcher.py::test_initial_state | excluded | Exact listener-map introspection through `get_listeners` and `has_listeners` is not specified behavior. |
| tests/events/test_event_dispatcher.py::test_add_listener | excluded | The source assertion depends on unspecified listener-map introspection; observable dispatch remains exercised by the rewritten case. |
| tests/events/test_event_dispatcher.py::test_get_listeners_sorts_by_priority | excluded | Numeric listener-priority ordering and the `get_listeners` return shape are not specified. |
| tests/events/test_event_dispatcher.py::test_get_all_listeners_sorts_by_priority | excluded | The aggregate listener-map shape and numeric priority semantics are not specified. |
| tests/events/test_event_dispatcher.py::test_get_listener_priority | excluded | Listener-priority introspection is not specified. |
| tests/events/test_event_dispatcher.py::test_stop_event_propagation | excluded | Event propagation-control behavior depends on the unpublished base `Event` API. |
