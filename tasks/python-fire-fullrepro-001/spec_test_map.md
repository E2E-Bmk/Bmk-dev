# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_exposes_fire_callable` | atomic | Component Traversal | covered |
| 2 | `oracle/test_atomic.py::test_function_positional_integer_returns_numeric_result` | atomic | Fire Entry Point And Public Import Surface | covered |
| 3 | `oracle/test_atomic.py::test_function_named_argument_returns_numeric_result` | atomic | Fire Entry Point And Public Import Surface | covered |
| 4 | `oracle/test_atomic.py::test_command_string_is_split_into_tokens` | atomic | Fire Entry Point And Public Import Surface | covered |
| 5 | `oracle/test_atomic.py::test_boolean_true_argument_uses_python_value` | atomic | Argument Parsing And Result Projection | covered |
| 6 | `oracle/test_atomic.py::test_boolean_false_argument_uses_python_value` | atomic | Argument Parsing And Result Projection | covered |
| 7 | `oracle/test_atomic.py::test_none_argument_uses_python_none` | atomic | Argument Parsing And Result Projection | covered |
| 8 | `oracle/test_atomic.py::test_float_argument_is_converted` | atomic | Argument Parsing And Result Projection | covered |
| 9 | `oracle/test_atomic.py::test_list_literal_argument_is_converted` | atomic | Argument Parsing And Result Projection | covered |
| 10 | `oracle/test_atomic.py::test_dict_literal_argument_is_converted` | atomic | Argument Parsing And Result Projection | covered |
| 11 | `oracle/test_atomic.py::test_tuple_return_uses_json_list_stdout` | atomic | Argument Parsing And Result Projection | covered |
| 12 | `oracle/test_atomic.py::test_dict_key_traversal_reaches_nested_value` | atomic | Fire Entry Point And Public Import Surface | covered |
| 13 | `oracle/test_atomic.py::test_single_token_dict_key_with_space_is_supported` | atomic | Fire Entry Point And Public Import Surface | covered |
| 14 | `oracle/test_atomic.py::test_sequence_index_traversal_reaches_tuple_item` | atomic | Fire Entry Point And Public Import Surface | covered |
| 15 | `oracle/test_atomic.py::test_hyphenated_member_access_maps_to_underscore_property` | atomic | Component Traversal | covered |
| 16 | `oracle/test_atomic.py::test_bound_method_uses_default_argument` | atomic | Component Traversal | covered |
| 17 | `oracle/test_atomic.py::test_bound_method_uses_named_argument` | atomic | Component Traversal | covered |
| 18 | `oracle/test_atomic.py::test_class_instantiation_uses_constructor_flags` | atomic | Component Traversal | covered |
| 19 | `oracle/test_atomic.py::test_class_instantiation_can_continue_to_method` | atomic | Component Traversal | covered |
| 20 | `oracle/test_atomic.py::test_callable_object_accepts_named_call_argument` | atomic | Component Traversal | covered |
| 21 | `oracle/test_atomic.py::test_default_separator_forces_then_traverses_string_result` | atomic | Command Evaluation And Separator Semantics | covered |
| 22 | `oracle/test_atomic.py::test_custom_separator_allows_default_separator_as_value` | atomic | Command Evaluation And Separator Semantics | covered |
| 23 | `oracle/test_atomic.py::test_varargs_function_consumes_all_unseparated_tokens` | atomic | Command Evaluation And Separator Semantics | covered |
| 24 | `oracle/test_atomic.py::test_function_returned_object_can_be_traversed_after_separator` | atomic | Command Evaluation And Separator Semantics | covered |
| 25 | `oracle/test_atomic.py::test_custom_serializer_controls_mapping_stdout` | atomic | Argument Parsing And Result Projection | covered |
| 26 | `oracle/test_atomic.py::test_help_flag_exits_and_lists_public_members` | atomic | Flags, Help, Trace, Completion, And Errors | covered |
| 27 | `oracle/test_atomic.py::test_trace_flag_exits_and_reports_command_steps` | atomic | Flags, Help, Trace, Completion, And Errors | covered |
| 28 | `oracle/test_atomic.py::test_bash_completion_contains_top_level_public_commands` | atomic | Flags, Help, Trace, Completion, And Errors | covered |
| 29 | `oracle/test_atomic.py::test_missing_key_reports_public_error_exit` | atomic | Flags, Help, Trace, Completion, And Errors | covered |
| 30 | `oracle/test_atomic.py::test_out_of_range_index_reports_public_error_exit` | atomic | Flags, Help, Trace, Completion, And Errors | covered |
| 31 | `oracle/test_integration.py::test_positional_and_named_numeric_dispatch_share_stdout_projection` | integration | Argument Parsing And Result Projection | covered |
| 32 | `oracle/test_integration.py::test_typed_arguments_project_to_return_dict_and_serialized_lines` | integration | Argument Parsing And Result Projection | covered |
| 33 | `oracle/test_integration.py::test_function_returned_list_can_be_indexed_then_mapped` | integration | Command Evaluation And Separator Semantics | covered |
| 34 | `oracle/test_integration.py::test_constructed_object_dict_property_can_be_traversed_to_scalar` | integration | Component Traversal | covered |
| 35 | `oracle/test_integration.py::test_class_constructor_flags_and_method_arguments_form_one_command` | integration | Component Traversal | covered |
| 36 | `oracle/test_integration.py::test_help_for_object_mentions_values_and_commands_from_same_state` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 37 | `oracle/test_integration.py::test_completion_and_help_expose_the_same_top_level_commands` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 38 | `oracle/test_integration.py::test_trace_for_bound_method_reports_traversal_without_stdout_value` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 39 | `oracle/test_integration.py::test_separator_result_can_use_public_string_method_after_invocation` | integration | Command Evaluation And Separator Semantics | covered |
| 40 | `oracle/test_integration.py::test_custom_separator_changes_only_fire_boundary_not_function_result` | integration | Command Evaluation And Separator Semantics | covered |
| 41 | `oracle/test_integration.py::test_parsed_list_result_can_be_traversed_after_separator` | integration | Command Evaluation And Separator Semantics | covered |
| 42 | `oracle/test_integration.py::test_parsed_dict_result_can_be_traversed_after_separator` | integration | Command Evaluation And Separator Semantics | covered |
| 43 | `oracle/test_integration.py::test_custom_serializer_sees_converted_mapping_return` | integration | Argument Parsing And Result Projection | covered |
| 44 | `oracle/test_integration.py::test_custom_serializer_can_project_public_object_return` | integration | Component Traversal | covered |
| 45 | `oracle/test_integration.py::test_varargs_result_can_be_forced_before_string_method_traversal` | integration | Command Evaluation And Separator Semantics | covered |
| 46 | `oracle/test_integration.py::test_bound_method_and_callable_object_use_same_instance_state` | integration | Component Traversal | covered |
| 47 | `oracle/test_integration.py::test_missing_member_error_includes_help_path_for_same_component` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 48 | `oracle/test_integration.py::test_index_error_on_nested_collection_reports_public_help_path` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 49 | `oracle/test_integration.py::test_scalar_projection_can_continue_to_public_builtin_method` | integration | Fire Entry Point And Public Import Surface | covered |
| 50 | `oracle/test_integration.py::test_object_dict_property_serializes_and_traverses_consistently` | integration | Component Traversal | covered |
| 51 | `oracle/test_integration.py::test_command_string_supports_named_flags_and_tuple_serialization` | integration | Fire Entry Point And Public Import Surface | covered |
| 52 | `oracle/test_integration.py::test_public_name_argument_is_reflected_in_help_and_error_guidance` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 53 | `oracle/test_integration.py::test_fish_completion_contains_commands_and_hyphenated_members` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 54 | `oracle/test_integration.py::test_root_component_without_command_returns_mapping_and_prints_grouped_help` | integration | Flags, Help, Trace, Completion, And Errors | covered |
| 55 | `oracle/test_integration.py::test_table_function_projects_list_stdout_and_supports_nested_selection` | integration | Command Evaluation And Separator Semantics | covered |
| 56 | `oracle/test_integration.py::test_file_path_invocation_exposes_module_commands` | integration | Module And File Invocation | covered |
| 57 | `oracle/test_integration.py::test_module_name_invocation_exposes_module_commands` | integration | Module And File Invocation | covered |
| 58 | `oracle/test_integration.py::test_command_string_preserves_quoted_arguments_before_tuple_projection` | integration | Fire Entry Point And Public Import Surface | covered |
| 59 | `oracle/test_integration.py::test_class_result_can_cross_separator_to_mapping_value_and_string_method` | integration | Command Evaluation And Separator Semantics | covered |
| 60 | `oracle/test_integration.py::test_direct_file_and_module_invocation_share_tuple_projection` | integration | Module And File Invocation | covered |

final_scoreable: 60
