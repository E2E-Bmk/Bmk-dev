# Spec Test Map

oracle_version: generated_only_20260704_001
filter/oracle_source: generated_only
spec: spec/spec_v1.md
reference_score: filter/reference_score.json
scorer_isolation: use --remove-path cattrs for candidate scoring; reference gate used PYTHONPATH to the reference src checkout on Linux/WSL.

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/generated_tests.py::test_public_surface_exports_converter_core_names | generated | atomic | Installable Surface | covered | reference-observed public behavior |
| filter/generated_tests.py::test_top_level_structure_and_unstructure_use_global_converter | generated | integration | Product State Model | covered | reference-observed public behavior |
| filter/generated_tests.py::test_converter_constructs_with_documented_defaults | generated | atomic | Public API | covered | reference-observed public behavior |
| filter/generated_tests.py::test_primitive_structure_coerces_with_target_type | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_primitive_structure_propagates_conversion_failure | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_any_structure_returns_original_object | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_optional_accepts_none_and_structures_present_value | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_literal_accepts_member_and_rejects_non_member | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_list_structure_accepts_any_iterable_and_converts_elements | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_homogeneous_tuple_structure_converts_each_element | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_heterogeneous_tuple_structure_uses_position_types | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_heterogeneous_tuple_length_mismatch_fails | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_sets_and_frozensets_structure_to_expected_collection_type | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_mapping_structure_converts_keys_and_values | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_enum_structures_from_and_unstructures_to_value | generated | integration | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_attrs_class_structures_from_mapping_with_field_types | generated | integration | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_dataclass_structures_from_mapping_with_field_types | generated | integration | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_missing_required_attrs_field_raises_class_validation_error | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_unknown_keys_are_ignored_by_default_for_attrs_classes | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_forbid_extra_keys_groups_public_error | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_structure_attrs_fromtuple_uses_field_order | generated | atomic | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_as_tuple_strategy_structures_sequence_into_attrs_class | generated | integration | Structuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_attrs_unstructure_defaults_to_dictionary | generated | atomic | Unstructuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_dataclass_unstructure_defaults_to_dictionary | generated | atomic | Unstructuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_as_tuple_strategy_unstructures_attrs_class_to_tuple | generated | atomic | Unstructuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_deque_unstructures_to_list_with_converter | generated | atomic | Unstructuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_unstructure_as_uses_target_type_hooks_for_nested_values | generated | integration | Unstructuring | covered | reference-observed public behavior |
| filter/generated_tests.py::test_explicit_structure_hook_overrides_default_for_type | generated | atomic | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_explicit_unstructure_hook_overrides_default_for_type | generated | atomic | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_structure_hook_decorator_infers_return_type | generated | atomic | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_unstructure_hook_decorator_infers_first_argument_type | generated | atomic | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_structure_hook_func_applies_predicate_rule | generated | atomic | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_unstructure_hook_func_applies_predicate_rule | generated | atomic | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_structure_hook_factory_builds_hook_for_matching_type | generated | integration | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_unstructure_hook_factory_builds_hook_for_matching_type | generated | integration | Hook Registration and Lookup | covered | reference-observed public behavior |
| filter/generated_tests.py::test_get_structure_hook_matches_structure_call | generated | integration | Cross-View Invariants | covered | reference-observed public behavior |
| filter/generated_tests.py::test_get_unstructure_hook_matches_unstructure_call | generated | integration | Cross-View Invariants | covered | reference-observed public behavior |
| filter/generated_tests.py::test_converter_hook_state_is_instance_local | generated | integration | Product State Model | covered | reference-observed public behavior |
| filter/generated_tests.py::test_converter_copy_preserves_then_isolates_hook_state | generated | integration | Product State Model | covered | reference-observed public behavior |
| filter/generated_tests.py::test_override_rename_maps_field_for_both_directions | generated | integration | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_override_omit_skips_field_when_unstructuring | generated | atomic | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_override_omit_skips_input_field_when_default_exists | generated | atomic | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_omit_if_default_skips_default_factory_value | generated | atomic | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_class_level_omit_if_default_can_be_disabled_per_field | generated | atomic | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_converter_omit_if_default_sets_generated_default_behavior | generated | atomic | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_override_struct_hook_controls_single_field | generated | atomic | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_override_unstruct_hook_controls_single_field | generated | atomic | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_use_alias_true_uses_attrs_field_alias | generated | integration | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_annotated_override_rename_is_honored_by_default_converter | generated | integration | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_registered_type_hook_precedes_attrs_converter_by_default | generated | integration | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_prefer_attrib_converters_inverts_type_hook_priority | generated | integration | Attribute Overrides and Defaults | covered | reference-observed public behavior |
| filter/generated_tests.py::test_detailed_validation_groups_class_field_errors_and_paths | generated | system_e2e | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_non_detailed_validation_raises_first_underlying_error | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_iterable_validation_error_is_public_error_group | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_mapping_validation_error_transform_path_contains_key | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_forbidden_extra_key_error_exposes_class_and_extra_fields | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_transform_error_accepts_custom_leaf_formatter | generated | integration | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_missing_structure_handler_raises_public_exception | generated | atomic | Validation and Error Semantics | covered | reference-observed public behavior |
| filter/generated_tests.py::test_nested_custom_type_hook_applies_through_attrs_list_and_mapping | generated | system_e2e | Cross-View Invariants | covered | reference-observed public behavior |
| filter/generated_tests.py::test_global_registration_affects_global_conversion_and_lookup | generated | system_e2e | Cross-View Invariants | covered | reference-observed public behavior |
| filter/generated_tests.py::test_structure_then_unstructure_preserves_supported_public_shape | generated | system_e2e | Cross-View Invariants | covered | reference-observed public behavior |
| filter/generated_tests.py::test_unstructure_then_structure_reconstructs_equivalent_dataclass | generated | system_e2e | Cross-View Invariants | covered | reference-observed public behavior |
Total: 62 | kept (covered): 62 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 62
