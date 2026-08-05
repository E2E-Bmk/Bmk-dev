# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_script_can_open_local_project_file` | atomic | Scope | covered |
| 2 | `oracle/test_atomic.py::test_infer_resolves_local_factory_to_instance` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_infer_resolves_repeat_alias_to_local_function` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_goto_without_follow_imports_stays_at_local_reference` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_goto_follow_imports_reaches_local_definition` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_name_public_attributes_describe_a_local_definition` | atomic | Public Import Surface | covered |
| 7 | `oracle/test_atomic.py::test_name_definition_positions_cover_the_function` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_name_raw_docstring_is_the_local_function_documentation` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_name_get_line_code_returns_the_definition_line` | atomic | Public Import Surface | covered |
| 10 | `oracle/test_atomic.py::test_name_parent_reports_the_module_scope` | atomic | Public Import Surface | covered |
| 11 | `oracle/test_atomic.py::test_class_name_defined_names_lists_public_members` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_reference_result_exposes_its_source_line` | atomic | Public Import Surface | covered |
| 13 | `oracle/test_atomic.py::test_name_module_path_points_to_the_local_module` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_script_search_returns_public_name_results` | atomic | Public Import Surface | covered |
| 15 | `oracle/test_atomic.py::test_script_search_imported_factory_keeps_import_location` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_script_complete_search_returns_a_completion_remainder` | atomic | Public Import Surface | covered |
| 17 | `oracle/test_atomic.py::test_completion_exposes_name_remainder_and_prefix` | atomic | Public Import Surface | covered |
| 18 | `oracle/test_atomic.py::test_fuzzy_completion_has_no_literal_remainder` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_signature_exposes_index_bracket_and_text` | atomic | Public Import Surface | covered |
| 20 | `oracle/test_atomic.py::test_signature_parameters_expose_names_and_kinds` | atomic | Public Import Surface | covered |
| 21 | `oracle/test_atomic.py::test_signature_parameter_defaults_infer_public_types` | atomic | Product State Model | covered |
| 22 | `oracle/test_atomic.py::test_signature_parameter_annotations_infer_public_types` | atomic | Product State Model | covered |
| 23 | `oracle/test_atomic.py::test_get_context_identifies_the_application_module` | atomic | Public Import Surface | covered |
| 24 | `oracle/test_atomic.py::test_get_names_returns_top_level_definitions` | atomic | Product State Model | covered |
| 25 | `oracle/test_atomic.py::test_get_names_all_scopes_includes_class_members` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_syntax_error_result_exposes_public_positions` | atomic | Error Semantics | covered |
| 27 | `oracle/test_atomic.py::test_valid_local_source_has_no_syntax_errors` | atomic | Error Semantics | covered |
| 28 | `oracle/test_atomic.py::test_interpreter_completion_reads_a_namespace_value` | atomic | Scope | covered |
| 29 | `oracle/test_atomic.py::test_interpreter_infer_reads_a_namespace_value` | atomic | Scope | covered |
| 30 | `oracle/test_atomic.py::test_project_properties_preserve_explicit_configuration` | atomic | Public Import Surface | covered |
| 31 | `oracle/test_integration.py::test_file_and_project_views_agree_on_factory` | integration | Cross-View Invariants | covered |
| 32 | `oracle/test_integration.py::test_completion_and_inference_share_local_class_member` | integration | Cross-View Invariants | covered |
| 33 | `oracle/test_integration.py::test_reference_search_matches_local_assignment_and_use` | integration | Cross-View Invariants | covered |
| 34 | `oracle/test_integration.py::test_project_search_finds_definition_used_by_script` | integration | Cross-View Invariants | covered |
| 35 | `oracle/test_integration.py::test_repeat_alias_inference_matches_project_factory_search` | integration | Cross-View Invariants | covered |
| 36 | `oracle/test_integration.py::test_project_and_script_complete_search_share_local_members` | integration | Cross-View Invariants | covered |
| 37 | `oracle/test_integration.py::test_project_search_all_scopes_finds_a_class_method` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_project_save_load_round_trip_preserves_public_properties` | integration | Representative Workflow | covered |
| 39 | `oracle/test_integration.py::test_project_search_module_and_class_views_share_a_file` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_interpreter_and_script_views_agree_on_string_members` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_interpreter_signature_and_script_signature_share_parameter_shape` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_signature_defaults_and_annotations_project_the_same_types` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_search_and_goto_share_docstring_and_definition_position` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_refactor_rename_changes_all_local_references` | integration | Representative Workflow | covered |
| 45 | `oracle/test_integration.py::test_refactor_rename_diff_describes_the_changed_file` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_refactor_rename_apply_updates_file_and_references` | integration | Representative Workflow | covered |
| 47 | `oracle/test_integration.py::test_refactor_extract_variable_projects_statement_and_diff` | integration | Representative Workflow | covered |
| 48 | `oracle/test_integration.py::test_refactor_extract_variable_apply_updates_file` | integration | Representative Workflow | covered |
| 49 | `oracle/test_integration.py::test_refactor_extract_function_projects_helper_and_call` | integration | Representative Workflow | covered |
| 50 | `oracle/test_integration.py::test_refactor_extract_function_apply_updates_file` | integration | Representative Workflow | covered |
| 51 | `oracle/test_integration.py::test_changed_file_methods_expose_code_and_no_renames` | integration | Public Import Surface | covered |
| 52 | `oracle/test_integration.py::test_refactoring_without_a_path_raises_the_public_error_type` | integration | Error Semantics | covered |
| 53 | `oracle/test_integration.py::test_saved_project_still_resolves_local_imports` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_file_search_and_completion_share_the_written_module` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_import_search_and_completion_share_factory_identity` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_reference_scope_distinguishes_file_and_project_views` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_search_and_reference_results_share_factory_identity` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_project_completion_exposes_public_result_attributes` | integration | Public Import Surface | covered |
| 59 | `oracle/test_integration.py::test_project_search_and_script_goto_share_module_identity` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_search_and_goto_ranges_are_consistent` | integration | Cross-View Invariants | covered |

final_scoreable: 60
