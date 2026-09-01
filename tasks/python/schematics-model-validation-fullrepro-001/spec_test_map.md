# Spec Test Map — schematics-model-validation-fullrepro-001

The task oracle contains only public, behavioral checks. Every nodeid maps to a
heading in `spec.md`; the GeoPoint container-shape check removed during the
fairness repair is not present.

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_string_converts_integer_to_text | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_string_min_length_rejects_short_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_string_regex_rejects_nonmatching_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_int_converts_decimal_text | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_int_rejects_out_of_range_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_decimal_has_native_decimal_and_primitive_text | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_boolean_accepts_true_text | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_boolean_accepts_false_digit | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_boolean_rejects_unrecognized_text | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_uuid_has_uuid_native_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_uuid_has_text_primitive_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_date_has_iso_primitive_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_datetime_rejects_invalid_text | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_timedelta_converts_seconds | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_geopoint_rejects_out_of_range_coordinate | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_list_type_converts_each_element | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_list_type_enforces_maximum_size | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_dict_type_converts_each_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_dict_type_rejects_non_mapping_input | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_email_rejects_malformed_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_url_rejects_malformed_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_ipv4_rejects_malformed_value | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_atomic.py::test_md5_rejects_wrong_digest_length | atomic | Field options and scalar types | covered | upstream rewrite |
| oracle/test_integration.py::test_attribute_and_mapping_read_same_native_value | integration | Cross-View Invariants | covered | upstream rewrite |
| oracle/test_integration.py::test_attribute_assignment_updates_mapping_and_native_export | integration | Cross-View Invariants | covered | upstream rewrite |
| oracle/test_integration.py::test_mapping_assignment_updates_attribute_and_native_export | integration | Cross-View Invariants | covered | upstream rewrite |
| oracle/test_integration.py::test_export_uses_serialized_field_name | integration | Cross-View Invariants | covered | upstream rewrite |
| oracle/test_integration.py::test_declared_input_key_wins_over_alternate_keys | integration | Product State Model | covered | upstream rewrite |
| oracle/test_integration.py::test_serialized_input_key_wins_over_deserialize_from_key | integration | Product State Model | covered | upstream rewrite |
| oracle/test_integration.py::test_unknown_mapping_assignment_raises_documented_error | integration | Error Semantics | covered | upstream rewrite |
| oracle/test_integration.py::test_strict_constructor_rejects_unknown_input_key | integration | Error Semantics | covered | upstream rewrite |
| oracle/test_integration.py::test_non_partial_validation_reports_missing_required_field | integration | Model declarations and construction | covered | upstream rewrite |
| oracle/test_integration.py::test_partial_constructor_allows_missing_required_field | integration | Model declarations and construction | covered | upstream rewrite |
| oracle/test_integration.py::test_literal_default_is_available_in_native_export | integration | Model declarations and construction | covered | upstream rewrite |
| oracle/test_integration.py::test_callable_default_is_evaluated_for_each_model | integration | Model declarations and construction | covered | upstream rewrite |
| oracle/test_integration.py::test_modeltype_turns_mapping_into_nested_model | integration | Model declarations and construction | covered | upstream rewrite |
| oracle/test_integration.py::test_modeltype_accepts_nested_model_instance | integration | Model declarations and construction | covered | upstream rewrite |
| oracle/test_integration.py::test_modeltype_rejects_non_model_non_mapping_value | integration | Error Semantics | covered | upstream rewrite |
| oracle/test_integration.py::test_list_of_models_exports_nested_primitive_mapping | integration | Model declarations and construction | covered | upstream rewrite |
| oracle/test_integration.py::test_whitelist_role_exports_only_named_field_in_both_views | integration | Compound and calculated fields | covered | upstream rewrite |
| oracle/test_integration.py::test_blacklist_role_omits_named_field_in_both_views | integration | Compound and calculated fields | covered | upstream rewrite |
| oracle/test_integration.py::test_default_role_applies_when_no_role_is_requested | integration | Compound and calculated fields | covered | upstream rewrite |
| oracle/test_integration.py::test_import_data_updates_and_returns_same_instance | integration | Compound and calculated fields | covered | upstream rewrite |
| oracle/test_integration.py::test_primitive_export_uses_decimal_primitive_value | integration | Cross-View Invariants | covered | upstream rewrite |
| oracle/test_integration.py::test_validate_reports_nested_field_errors_structurally | integration | Error Semantics | covered | upstream rewrite |
| oracle/test_integration.py::test_model_validate_returns_instance_when_valid | integration | Validation, export, and roles | covered | upstream rewrite |
| oracle/test_integration.py::test_boolean_accepts_numeric_true_value | integration | Validation, export, and roles | covered | upstream rewrite |
| oracle/test_integration.py::test_date_rejects_unparseable_value | integration | Error Semantics | covered | upstream rewrite |
| oracle/test_integration.py::test_primitive_export_is_mapping_with_scalar_values | integration | Validation, export, and roles | covered | upstream rewrite |
| oracle/test_integration.py::test_product_state_workflow_binds_instance_native_and_primitive_views | system_e2e | Product State Model | covered | generated |
| oracle/test_integration.py::test_representative_workflow_applies_role_to_both_export_views | system_e2e | Representative Workflow | covered | generated |
| oracle/test_integration.py::test_representative_workflow_exports_nested_state_after_validation | system_e2e | Representative Workflow | covered | generated |
| oracle/test_integration.py::test_representative_workflow_recovers_after_structured_validation_failure | system_e2e | Representative Workflow | covered | generated |

Total: 53 (23 atomic, 26 integration, 4 system_e2e).
