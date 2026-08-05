# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_imports_expose_core_types` | atomic | Public Import Surface | covered |
| 2 | `oracle/test_atomic.py::test_resource_inline_descriptor_is_canonical` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_resource_inline_rows_cast_to_declared_schema` | atomic | Cross-View Invariants | covered |
| 4 | `oracle/test_atomic.py::test_integer_field_casts_and_writes_public_values` | atomic | Scope | covered |
| 5 | `oracle/test_atomic.py::test_number_field_supports_decimal_and_float_modes` | atomic | Scope | covered |
| 6 | `oracle/test_atomic.py::test_boolean_field_accepts_custom_true_and_false_values` | atomic | Scope | covered |
| 7 | `oracle/test_atomic.py::test_date_and_datetime_fields_cast_iso_values` | atomic | Scope | covered |
| 8 | `oracle/test_atomic.py::test_array_and_object_fields_parse_json_cells` | atomic | Scope | covered |
| 9 | `oracle/test_atomic.py::test_field_constraints_return_structured_notes` | atomic | Validation And Error Reporting | covered |
| 10 | `oracle/test_atomic.py::test_schema_field_management_and_cell_projection` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_detector_options_are_public_and_configurable` | atomic | Scope | covered |
| 12 | `oracle/test_atomic.py::test_detector_field_names_control_described_schema` | atomic | Scope | covered |
| 13 | `oracle/test_atomic.py::test_resource_descriptor_json_round_trip` | atomic | Cross-View Invariants | covered |
| 14 | `oracle/test_atomic.py::test_resource_descriptor_yaml_round_trip` | atomic | Cross-View Invariants | covered |
| 15 | `oracle/test_atomic.py::test_package_descriptor_manages_named_resources` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_package_descriptor_json_round_trip` | atomic | Cross-View Invariants | covered |
| 17 | `oracle/test_atomic.py::test_package_descriptor_yaml_round_trip` | atomic | Cross-View Invariants | covered |
| 18 | `oracle/test_atomic.py::test_describe_infers_csv_schema` | atomic | Representative Workflows | covered |
| 19 | `oracle/test_atomic.py::test_extract_returns_named_rows_with_cast_values` | atomic | Representative Workflows | covered |
| 20 | `oracle/test_atomic.py::test_validate_valid_inline_resource_has_clean_report` | atomic | Validation And Error Reporting | covered |
| 21 | `oracle/test_atomic.py::test_validate_invalid_rows_exposes_structured_error` | atomic | Validation And Error Reporting | covered |
| 22 | `oracle/test_atomic.py::test_report_flatten_exposes_structured_error_columns` | atomic | Validation And Error Reporting | covered |
| 23 | `oracle/test_atomic.py::test_analyzer_summary_reports_rows_and_fields` | atomic | Scope | covered |
| 24 | `oracle/test_atomic.py::test_analyzer_detailed_reports_variable_types_and_field_stats` | atomic | Scope | covered |
| 25 | `oracle/test_atomic.py::test_pipeline_descriptor_round_trip_preserves_step_types` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_transform_action_adds_a_field` | atomic | Representative Workflows | covered |
| 27 | `oracle/test_atomic.py::test_transform_action_filters_rows` | atomic | Representative Workflows | covered |
| 28 | `oracle/test_atomic.py::test_transform_action_normalizes_string_cells` | atomic | Representative Workflows | covered |
| 29 | `oracle/test_atomic.py::test_list_action_returns_local_resource` | atomic | Scope | covered |
| 30 | `oracle/test_atomic.py::test_package_extract_applies_name_and_limit` | atomic | Representative Workflows | covered |
| 31 | `oracle/test_atomic.py::test_schema_constraints_are_preserved_in_descriptor` | atomic | Product State Model | covered |
| 32 | `oracle/test_atomic.py::test_resource_copy_preserves_descriptor_and_rows` | atomic | Cross-View Invariants | covered |
| 33 | `oracle/test_integration.py::test_inline_descriptor_round_trip_preserves_cast_rows` | integration | Cross-View Invariants | covered |
| 34 | `oracle/test_integration.py::test_local_json_and_yaml_data_resources_preserve_values` | integration | Scope | covered |
| 35 | `oracle/test_integration.py::test_describe_and_extract_share_a_csv_schema_projection` | integration | Cross-View Invariants | covered |
| 36 | `oracle/test_integration.py::test_valid_csv_validation_has_stable_structured_report` | integration | Validation And Error Reporting | covered |
| 37 | `oracle/test_integration.py::test_invalid_csv_validation_projects_type_error_coordinates` | integration | Validation And Error Reporting | covered |
| 38 | `oracle/test_integration.py::test_detector_field_names_and_field_type_compose_on_local_csv` | integration | Representative Workflows | covered |
| 39 | `oracle/test_integration.py::test_custom_csv_dialect_drives_describe_extract_and_validate` | integration | Representative Workflows | covered |
| 40 | `oracle/test_integration.py::test_detector_missing_values_flow_into_rows_and_schema` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_schema_constraints_produce_validation_errors_with_coordinates` | integration | Validation And Error Reporting | covered |
| 42 | `oracle/test_integration.py::test_primary_key_validation_reports_duplicate_row_structure` | integration | Validation And Error Reporting | covered |
| 43 | `oracle/test_integration.py::test_resource_json_descriptor_round_trip_reopens_local_csv` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_resource_yaml_descriptor_round_trip_reopens_local_csv` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_package_local_resources_extract_by_name_after_management` | integration | Representative Workflows | covered |
| 46 | `oracle/test_integration.py::test_package_json_descriptor_round_trip_reopens_csv_resource` | integration | Cross-View Invariants | covered |
| 47 | `oracle/test_integration.py::test_package_yaml_descriptor_round_trip_reopens_csv_resource` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_package_validation_aggregates_two_local_resource_tasks` | integration | Validation And Error Reporting | covered |
| 49 | `oracle/test_integration.py::test_package_extract_supports_all_resources_name_and_limit` | integration | Representative Workflows | covered |
| 50 | `oracle/test_integration.py::test_csv_analysis_matches_described_resource_shape` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_detailed_csv_analysis_projects_numeric_and_categorical_fields` | integration | Scope | covered |
| 52 | `oracle/test_integration.py::test_describe_can_build_a_package_from_two_local_csv_files` | integration | Representative Workflows | covered |
| 53 | `oracle/test_integration.py::test_extract_action_composes_filter_and_process_callbacks` | integration | Representative Workflows | covered |
| 54 | `oracle/test_integration.py::test_validate_action_applies_explicit_schema_and_error_filter` | integration | Validation And Error Reporting | covered |
| 55 | `oracle/test_integration.py::test_transform_pipeline_composes_field_add_and_row_filter` | integration | Representative Workflows | covered |
| 56 | `oracle/test_integration.py::test_transform_pipeline_sorts_rows_after_filtering` | integration | Representative Workflows | covered |
| 57 | `oracle/test_integration.py::test_transform_action_accepts_pipeline_descriptor` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_local_csv_can_be_converted_to_inline_and_back` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_local_json_and_yaml_resources_round_trip_through_write_json` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_schema_json_projection_rehydrates_resource_casting` | integration | Cross-View Invariants | covered |
| 61 | `oracle/test_integration.py::test_dialect_descriptor_round_trip_keeps_csv_control` | integration | Cross-View Invariants | covered |
| 62 | `oracle/test_integration.py::test_report_descriptor_round_trip_preserves_structured_projection` | integration | Validation And Error Reporting | covered |
| 63 | `oracle/test_integration.py::test_error_descriptor_round_trip_keeps_public_coordinates` | integration | Validation And Error Reporting | covered |
| 64 | `oracle/test_integration.py::test_local_data_workflow_describe_transform_extract_validate` | integration | Representative Workflows | covered |

final_scoreable: 64
