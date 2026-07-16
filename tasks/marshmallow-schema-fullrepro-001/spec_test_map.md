# Spec Test Map - marshmallow-schema-fullrepro-001

oracle_version: generated_public_20260704_v1
filter/oracle_source: generated_reference_observed
reference_gate: 69/69 passed on WSL with scorer isolation --remove-path marshmallow
dummy_gate: 0/69 passed on WSL with scorer isolation --remove-path marshmallow

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/generated_tests.py::test_top_level_exports_are_importable | generated | atomic | - | excluded | passed dummy gate as import-only smoke test |
| filter/generated_tests.py::test_schema_declared_fields_dump_mapping_and_object | generated | integration | Product State Model | covered | public behavior; reference observed |
| filter/generated_tests.py::test_schema_from_dict_creates_usable_schema_class | generated | integration | Schema Declaration and Field Binding | covered | public behavior; reference observed |
| filter/generated_tests.py::test_only_limits_dump_and_load_views | generated | atomic | Product State Model | covered | public behavior; reference observed |
| filter/generated_tests.py::test_exclude_removes_fields_from_dump_and_load | generated | atomic | Schema Declaration and Field Binding | covered | public behavior; reference observed |
| filter/generated_tests.py::test_unknown_field_rejected_by_default | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_unknown_exclude_omits_extra_input | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_unknown_include_preserves_extra_input | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_load_unknown_argument_overrides_instance_policy | generated | integration | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_instance_unknown_overrides_meta_policy | generated | integration | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_required_field_error_skipped_by_partial_true | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_partial_tuple_skips_only_named_required_fields | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_load_default_and_dump_default_are_applied | generated | atomic | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_callable_load_default_runs_for_each_load | generated | atomic | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_load_default_none_allows_none_by_default | generated | atomic | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_allow_none_false_rejects_none_even_with_default | generated | atomic | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_data_key_changes_external_key_and_error_key | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_attribute_reads_different_internal_name_on_dump | generated | atomic | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_dump_only_is_omitted_from_load_and_load_only_from_dump | generated | atomic | Serialization and Deserialization | covered | public behavior; reference observed |
| filter/generated_tests.py::test_many_instance_dumps_and_loads_collections | generated | system_e2e | Serialization and Deserialization | covered | public behavior; reference observed |
| filter/generated_tests.py::test_dump_and_load_accept_many_argument | generated | system_e2e | Serialization and Deserialization | covered | public behavior; reference observed |
| filter/generated_tests.py::test_dumps_and_loads_match_dump_and_load | generated | system_e2e | Cross-View Invariants | covered | public behavior; reference observed |
| filter/generated_tests.py::test_schema_validate_returns_errors_without_raising | generated | integration | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_validation_error_exposes_messages_and_valid_data | generated | atomic | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_collection_errors_are_keyed_by_index | generated | atomic | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_string_integer_float_decimal_boolean_conversions | generated | atomic | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_date_time_datetime_and_timedelta_fields | generated | atomic | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_uuid_ip_url_and_email_fields | generated | atomic | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_list_tuple_dict_and_mapping_fields | generated | atomic | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_constant_field_returns_constant_on_dump_and_load | generated | atomic | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_enum_field_by_value_loads_and_dumps | generated | system_e2e | JSON and Context Projections | covered | public behavior; reference observed |
| filter/generated_tests.py::test_function_and_method_fields_dump_computed_values | generated | atomic | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_field_pre_and_post_load_processors_transform_value | generated | atomic | Processor and Validator Decorators | covered | public behavior; reference observed |
| filter/generated_tests.py::test_field_processor_validation_error_attaches_to_field | generated | atomic | Processor and Validator Decorators | covered | public behavior; reference observed |
| filter/generated_tests.py::test_range_length_and_oneof_validators_accept_valid_values | generated | atomic | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_builtin_validators_report_field_errors | generated | atomic | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_noneof_contains_only_equal_regexp_predicate_and_and_validators | generated | atomic | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_multiple_validators_collect_multiple_failures_for_field | generated | atomic | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_validates_decorator_validates_multiple_fields | generated | integration | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_validates_schema_reports_schema_key_by_default | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_validates_schema_can_report_field_errors | generated | integration | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_schema_validator_skips_when_field_errors_exist_by_default | generated | system_e2e | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_schema_validator_can_run_when_field_errors_exist | generated | system_e2e | Validation and Error Reporting | covered | public behavior; reference observed |
| filter/generated_tests.py::test_pre_load_and_post_load_transform_data | generated | system_e2e | Processor and Validator Decorators | covered | public behavior; reference observed |
| filter/generated_tests.py::test_pre_dump_and_post_dump_transform_data | generated | system_e2e | Processor and Validator Decorators | covered | public behavior; reference observed |
| filter/generated_tests.py::test_pass_collection_hooks_receive_whole_collection | generated | system_e2e | Processor and Validator Decorators | covered | public behavior; reference observed |
| filter/generated_tests.py::test_post_load_pass_original_receives_original_input | generated | atomic | Processor and Validator Decorators | covered | public behavior; reference observed |
| filter/generated_tests.py::test_nested_schema_dumps_and_loads_object | generated | system_e2e | Cross-View Invariants | covered | public behavior; reference observed |
| filter/generated_tests.py::test_nested_only_uses_nested_field_subset | generated | system_e2e | Nested Data and Collection Handling | covered | public behavior; reference observed |
| filter/generated_tests.py::test_dotted_only_limits_nested_output | generated | system_e2e | Nested Data and Collection Handling | covered | public behavior; reference observed |
| filter/generated_tests.py::test_list_of_nested_schemas_reports_indexed_errors | generated | system_e2e | Nested Data and Collection Handling | covered | public behavior; reference observed |
| filter/generated_tests.py::test_pluck_dumps_scalar_and_loads_nested_dict | generated | system_e2e | Nested Data and Collection Handling | covered | public behavior; reference observed |
| filter/generated_tests.py::test_pluck_many_dumps_list_and_loads_list_of_nested_dicts | generated | system_e2e | Nested Data and Collection Handling | covered | public behavior; reference observed |
| filter/generated_tests.py::test_nested_partial_dotted_path_skips_required_child_field | generated | system_e2e | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_nested_self_schema_dumps_recursive_relationship | generated | system_e2e | Nested Data and Collection Handling | covered | public behavior; reference observed |
| filter/generated_tests.py::test_context_get_returns_active_context_and_restores_default | generated | system_e2e | JSON and Context Projections | covered | public behavior; reference observed |
| filter/generated_tests.py::test_context_get_without_default_raises_when_missing | generated | system_e2e | JSON and Context Projections | covered | public behavior; reference observed |
| filter/generated_tests.py::test_function_field_reads_current_context | generated | system_e2e | JSON and Context Projections | covered | public behavior; reference observed |
| filter/generated_tests.py::test_load_validate_and_loads_agree_on_unknown_errors | generated | system_e2e | Cross-View Invariants | covered | public behavior; reference observed |
| filter/generated_tests.py::test_dump_and_dumps_use_same_external_data_key | generated | system_e2e | Cross-View Invariants | covered | public behavior; reference observed |
| filter/generated_tests.py::test_load_and_loads_apply_same_defaults_and_conversion | generated | system_e2e | Cross-View Invariants | covered | public behavior; reference observed |
| filter/generated_tests.py::test_dump_does_not_run_field_validators | generated | atomic | Serialization and Deserialization | covered | public behavior; reference observed |
| filter/generated_tests.py::test_unknown_exclude_validate_returns_no_errors | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_schema_fields_reflect_only_and_exclude_projection | generated | integration | Product State Model | covered | public behavior; reference observed |
| filter/generated_tests.py::test_invalid_only_field_raises_at_schema_creation | generated | integration | Schema Declaration and Field Binding | covered | public behavior; reference observed |
| filter/generated_tests.py::test_raw_field_passes_values_through | generated | atomic | Field Types and Conversion | covered | public behavior; reference observed |
| filter/generated_tests.py::test_missing_required_and_unknown_errors_can_coexist | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_post_dump_pass_original_receives_original_object | generated | atomic | Processor and Validator Decorators | covered | public behavior; reference observed |
| filter/generated_tests.py::test_validates_receives_external_data_key | generated | integration | Unknown, Partial, Defaults, and Key Mapping | covered | public behavior; reference observed |
| filter/generated_tests.py::test_nested_unknown_policy_is_applied_inside_nested_schema | generated | system_e2e | Nested Data and Collection Handling | covered | public behavior; reference observed |

Total: 70 | kept (covered): 69 | spec_gap: 0 | source-only: 0 | excluded: 1 | final scoreable: 69
