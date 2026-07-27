# Spec Test Map - pint-fullrepro-001

oracle_version: 2026-07-27-stage3-mixed-v2-oracle-split-specv1
oracle_source: upstream_plus_generated
oracle_files: test_atomic.py, test_integration.py
runtime_requirements: requirements.txt
scorer_isolation: --remove-path pint --pytest-arg=--rootdir=.
track_a_upstream_kept: 14
track_b_generated_kept: 78
depends_on_annotation_coverage: 36/36 integration+system_e2e tests

| test_nodeid | source | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|---|
| test_integration.py::test_upstream_get_application_registry_default_unit | upstream | integration | positive | Application Registry And Utility APIs | covered | source: rewritten upstream; clauses: PINT-APP-002 |
| test_integration.py::test_upstream_pickled_custom_quantity_requires_application_registry_definition | upstream | integration | failure_path | Application Registry And Utility APIs; Error Semantics | covered | source: rewritten upstream; clauses: PINT-APP-005 |
| test_atomic.py::test_upstream_pi_theorem_simple_movement | upstream | atomic | positive | Application Registry And Utility APIs | covered | source: rewritten upstream; clauses: PINT-UTIL-001, PINT-UTIL-003 |
| test_atomic.py::test_upstream_registry_pi_theorem_accepts_public_dimensional_inputs | upstream | atomic | positive | Application Registry And Utility APIs | covered | source: rewritten upstream; clauses: PINT-UTIL-002, PINT-UTIL-003 |
| test_integration.py::test_upstream_register_unit_format_custom_and_rejects_duplicate | upstream | integration | positive | Formatting And Text Output; Error Semantics | covered | source: rewritten upstream; clauses: PINT-FMT-011, PINT-FMT-012 |
| test_integration.py::test_upstream_format_unit_caret_negative_power | upstream | integration | positive | Formatting And Text Output | covered | source: rewritten upstream; clauses: PINT-FMT-002, PINT-FMT-005 |
| test_atomic.py::test_upstream_quantity_creation_from_public_inputs | upstream | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: rewritten upstream; clauses: PINT-QTY-001, PINT-QTY-003 |
| test_atomic.py::test_upstream_quantity_comparison_converts_compatible_units | upstream | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: rewritten upstream; clauses: PINT-QTY-008 |
| test_atomic.py::test_upstream_cross_registry_operations_raise_value_error | upstream | atomic | failure_path | Quantity, Unit, And Measurement Behavior | covered | source: rewritten upstream; clauses: PINT-QTY-009 |
| test_atomic.py::test_upstream_unit_multiplication_creates_quantities | upstream | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: rewritten upstream; clauses: PINT-QTY-002, PINT-QTY-004 |
| test_atomic.py::test_upstream_unit_division_creates_quantities | upstream | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: rewritten upstream; clauses: PINT-QTY-002, PINT-QTY-004 |
| test_atomic.py::test_upstream_unit_power_accepts_numeric_and_rejects_mapping | upstream | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: rewritten upstream; clauses: PINT-QTY-004 |
| test_atomic.py::test_upstream_unit_is_compatible_with_public_inputs | upstream | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: rewritten upstream; clauses: PINT-QTY-024 |
| test_integration.py::test_upstream_application_registry_controls_top_level_quantity | upstream | integration | positive | Application Registry And Utility APIs; Cross-View Invariants | covered | source: rewritten upstream; clauses: PINT-APP-001, PINT-APP-003, PINT-INV-007 |
| test_atomic.py::test_default_registry_loads_bundled_units | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-002, PINT-REG-015 |
| test_atomic.py::test_empty_registry_rejects_unknown_default_unit | generated | atomic | failure_path | Registry Construction And Definitions; Error Semantics | covered | source: generated; clauses: PINT-REG-003, PINT-ERR-001 |
| test_atomic.py::test_iterable_definitions_add_custom_unit_and_plural_alias | generated | atomic | positive | Registry Construction And Definitions; Cross-View Invariants | covered | source: generated; clauses: PINT-REG-001, PINT-REG-004, PINT-INV-001 |
| test_atomic.py::test_invalid_definition_line_raises_definition_syntax_error | generated | atomic | failure_path | Registry Construction And Definitions; Error Semantics | covered | source: generated; clauses: PINT-REG-005, PINT-ERR-005 |
| test_atomic.py::test_redefinition_policy_raise_rejects_reused_name | generated | atomic | failure_path | Registry Construction And Definitions; Error Semantics | covered | source: generated; clauses: PINT-REG-006, PINT-ERR-006 |
| test_atomic.py::test_redefinition_policy_ignore_replaces_definition | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-007 |
| test_atomic.py::test_symbol_placeholder_allows_alias_without_symbol | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-008, PINT-REG-009 |
| test_atomic.py::test_prefix_definition_applies_during_parsing | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-010 |
| test_atomic.py::test_dimension_definition_supports_derived_dimension | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-011 |
| test_atomic.py::test_alias_directive_adds_lookup_name_to_existing_unit | generated | atomic | positive | Registry Construction And Definitions; Cross-View Invariants | covered | source: generated; clauses: PINT-REG-012, PINT-INV-001 |
| test_atomic.py::test_attribute_item_and_parse_units_return_same_bound_unit | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-015 |
| test_atomic.py::test_calling_registry_parses_quantity_expression | generated | atomic | positive | Registry Construction And Definitions; Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-REG-016, PINT-QTY-001 |
| test_atomic.py::test_parse_expression_supports_numbers_powers_and_parentheses | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-017 |
| test_atomic.py::test_parse_expression_supports_implicit_multiplication | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-017, PINT-REG-018 |
| test_atomic.py::test_parse_expression_supports_nan_and_infinity | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-017 |
| test_atomic.py::test_parse_expression_supports_dimensionless | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-017 |
| test_atomic.py::test_parse_units_rejects_scale_factor | generated | atomic | failure_path | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-019 |
| test_atomic.py::test_unknown_unit_token_raises_undefined_unit_error | generated | atomic | failure_path | Registry Construction And Definitions; Error Semantics | covered | source: generated; clauses: PINT-REG-020, PINT-ERR-001 |
| test_atomic.py::test_case_insensitive_registry_resolves_unit_names | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-021 |
| test_atomic.py::test_preprocessor_rewrites_expression_before_parsing | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-027 |
| test_atomic.py::test_non_int_type_controls_parsed_decimal_magnitudes | generated | atomic | positive | Registry Construction And Definitions | covered | source: generated; clauses: PINT-REG-028 |
| test_atomic.py::test_quantity_public_magnitude_and_unit_attributes | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-001, PINT-QTY-003 |
| test_atomic.py::test_number_multiplied_by_unit_returns_quantity | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-002 |
| test_atomic.py::test_unit_arithmetic_combines_unit_expressions | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-004 |
| test_atomic.py::test_quantity_multiplication_division_and_power_combine_units | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-007 |
| test_atomic.py::test_addition_converts_compatible_operands | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-008 |
| test_atomic.py::test_comparison_converts_compatible_operands | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-008 |
| test_atomic.py::test_cross_registry_arithmetic_raises_value_error | generated | atomic | failure_path | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-009 |
| test_atomic.py::test_incompatible_addition_raises_dimensionality_error | generated | atomic | failure_path | Quantity, Unit, And Measurement Behavior; Error Semantics | covered | source: generated; clauses: PINT-QTY-010, PINT-ERR-002 |
| test_atomic.py::test_ambiguous_offset_arithmetic_raises_offset_error | generated | atomic | failure_path | Quantity, Unit, And Measurement Behavior; Error Semantics | covered | source: generated; clauses: PINT-QTY-011, PINT-ERR-003 |
| test_atomic.py::test_to_returns_new_quantity_without_mutating_source | generated | atomic | positive | Quantity, Unit, And Measurement Behavior; Cross-View Invariants | covered | source: generated; clauses: PINT-QTY-012, PINT-INV-003 |
| test_atomic.py::test_ito_mutates_quantity_and_returns_none | generated | atomic | positive | Quantity, Unit, And Measurement Behavior; Cross-View Invariants | covered | source: generated; clauses: PINT-QTY-012, PINT-INV-003 |
| test_atomic.py::test_to_base_units_uses_registry_default_system | generated | atomic | positive | Quantity, Unit, And Measurement Behavior; Conversion Contexts And Unit Systems | covered | source: generated; clauses: PINT-QTY-013, PINT-SYS-002 |
| test_atomic.py::test_to_base_units_accepts_explicit_system | generated | atomic | positive | Quantity, Unit, And Measurement Behavior; Conversion Contexts And Unit Systems | covered | source: generated; clauses: PINT-QTY-013, PINT-SYS-004 |
| test_atomic.py::test_to_root_units_uses_primitive_definition_units | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-014 |
| test_atomic.py::test_to_reduced_units_keeps_named_derived_unit_when_already_reduced | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-015 |
| test_atomic.py::test_to_compact_chooses_human_readable_prefix | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-016 |
| test_atomic.py::test_to_compact_restricted_to_unit_family | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-016 |
| test_atomic.py::test_to_unprefixed_removes_si_prefix | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-017 |
| test_atomic.py::test_to_preferred_uses_caller_supplied_preferred_units | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-018 |
| test_atomic.py::test_unknown_conversion_target_raises_undefined_unit_error | generated | atomic | failure_path | Quantity, Unit, And Measurement Behavior; Error Semantics | covered | source: generated; clauses: PINT-QTY-019, PINT-ERR-001 |
| test_atomic.py::test_m_as_returns_converted_magnitude_only | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-022 |
| test_atomic.py::test_to_timedelta_converts_time_quantities | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-021 |
| test_atomic.py::test_to_timedelta_rejects_non_time_dimensions | generated | atomic | failure_path | Quantity, Unit, And Measurement Behavior; Error Semantics | covered | source: generated; clauses: PINT-QTY-021, PINT-ERR-002 |
| test_atomic.py::test_is_compatible_with_accepts_compatible_strings | generated | atomic | positive | Quantity, Unit, And Measurement Behavior | covered | source: generated; clauses: PINT-QTY-024 |
| test_atomic.py::test_pi_theorem_returns_dimensionless_products | generated | atomic | positive | Application Registry And Utility APIs | covered | source: generated; clauses: PINT-UTIL-001, PINT-UTIL-003 |
| test_atomic.py::test_registry_pi_theorem_resolves_units_through_registry | generated | atomic | positive | Application Registry And Utility APIs | covered | source: generated; clauses: PINT-UTIL-002 |
| test_integration.py::test_quantity_tuple_round_trip_preserves_conversion_behavior | generated | integration | positive | Quantity, Unit, And Measurement Behavior; Cross-View Invariants | covered | source: generated; clauses: PINT-QTY-020, PINT-INV-008 |
| test_integration.py::test_custom_definition_visible_across_lookup_parse_quantity_and_conversion | generated | integration | positive | Cross-View Invariants; Registry Construction And Definitions | covered | source: generated; clauses: PINT-INV-001, PINT-REG-004 |
| test_integration.py::test_loaded_definition_file_mutates_existing_registry | generated | integration | positive | Registry Construction And Definitions; Cross-View Invariants | covered | source: generated; clauses: PINT-REG-004, PINT-INV-001 |
| test_integration.py::test_context_allows_one_off_cross_dimensional_conversion | generated | integration | positive | Conversion Contexts And Unit Systems; Cross-View Invariants | covered | source: generated; clauses: PINT-CTX-005, PINT-INV-005 |
| test_integration.py::test_context_manager_restores_previous_dimensionality_rules | generated | integration | positive | Conversion Contexts And Unit Systems; Cross-View Invariants | covered | source: generated; clauses: PINT-CTX-006, PINT-INV-005 |
| test_integration.py::test_enable_and_disable_contexts_control_later_conversions | generated | integration | positive | Conversion Contexts And Unit Systems; Cross-View Invariants | covered | source: generated; clauses: PINT-CTX-007, PINT-INV-005 |
| test_integration.py::test_context_parameters_override_default_values | generated | integration | positive | Conversion Contexts And Unit Systems | covered | source: generated; clauses: PINT-CTX-011 |
| test_integration.py::test_custom_context_transformation_uses_public_context_api | generated | integration | positive | Conversion Contexts And Unit Systems | covered | source: generated; clauses: PINT-CTX-001, PINT-CTX-002, PINT-CTX-004 |
| test_integration.py::test_later_enabled_context_takes_precedence_for_same_pair | generated | integration | positive | Conversion Contexts And Unit Systems | covered | source: generated; clauses: PINT-CTX-008 |
| test_integration.py::test_unknown_context_name_raises_key_error | generated | integration | failure_path | Conversion Contexts And Unit Systems; Error Semantics | covered | source: generated; clauses: PINT-CTX-009, PINT-ERR-011 |
| test_integration.py::test_context_transformation_exception_is_propagated | generated | integration | positive | Conversion Contexts And Unit Systems | covered | source: generated; clauses: PINT-CTX-010 |
| test_integration.py::test_invalid_context_redefinition_is_rejected | generated | integration | failure_path | Conversion Contexts And Unit Systems | covered | source: generated; clauses: PINT-CTX-015 |
| test_integration.py::test_system_projection_exposes_member_units | generated | integration | positive | Conversion Contexts And Unit Systems; Cross-View Invariants | covered | source: generated; clauses: PINT-SYS-001, PINT-INV-009 |
| test_integration.py::test_default_system_changes_later_base_unit_conversion | generated | integration | positive | Conversion Contexts And Unit Systems; Cross-View Invariants | covered | source: generated; clauses: PINT-SYS-002, PINT-SYS-003, PINT-INV-004 |
| test_integration.py::test_unknown_default_system_raises_value_error | generated | integration | failure_path | Conversion Contexts And Unit Systems; Error Semantics | covered | source: generated; clauses: PINT-SYS-004, PINT-ERR-012 |
| test_integration.py::test_format_short_modifier_uses_unit_symbols | generated | integration | positive | Formatting And Text Output | covered | source: generated; clauses: PINT-FMT-002, PINT-FMT-004 |
| test_integration.py::test_format_negative_exponent_modifier_moves_denominator | generated | integration | positive | Formatting And Text Output | covered | source: generated; clauses: PINT-FMT-002, PINT-FMT-005 |
| test_integration.py::test_format_compact_modifier_compacts_quantity_before_formatting | generated | integration | positive | Formatting And Text Output | covered | source: generated; clauses: PINT-FMT-002, PINT-FMT-006 |
| test_integration.py::test_invalid_format_specification_raises_value_error | generated | integration | failure_path | Formatting And Text Output | covered | source: generated; clauses: PINT-FMT-007 |
| test_integration.py::test_registry_default_format_affects_later_string_projection | generated | integration | positive | Formatting And Text Output; Cross-View Invariants | covered | source: generated; clauses: PINT-FMT-001, PINT-FMT-008, PINT-INV-006 |
| test_integration.py::test_top_level_formatter_formats_numerator_and_denominator_terms | generated | integration | positive | Formatting And Text Output | covered | source: generated; clauses: PINT-FMT-013 |
| test_integration.py::test_register_unit_format_rejects_existing_name | generated | integration | failure_path | Formatting And Text Output; Error Semantics | covered | source: generated; clauses: PINT-FMT-012, PINT-ERR-009 |
| test_integration.py::test_application_registry_controls_top_level_quantity_constructor | generated | integration | positive | Application Registry And Utility APIs; Cross-View Invariants | covered | source: generated; clauses: PINT-APP-001, PINT-APP-003, PINT-INV-007 |
| test_integration.py::test_get_application_registry_returns_current_registry_wrapper | generated | integration | positive | Application Registry And Utility APIs | covered | source: generated; clauses: PINT-APP-002 |
| test_integration.py::test_set_application_registry_rejects_non_registry_object | generated | integration | failure_path | Application Registry And Utility APIs; Error Semantics | covered | source: generated; clauses: PINT-APP-004, PINT-ERR-010 |
| test_integration.py::test_pickled_quantity_uses_application_registry_on_load | generated | integration | positive | Application Registry And Utility APIs; Cross-View Invariants | covered | source: generated; clauses: PINT-APP-005, PINT-INV-007 |
| test_integration.py::test_cli_converts_quantity_to_requested_units | generated | system_e2e | positive | Pint-Convert CLI; Cross-View Invariants | covered | source: generated; clauses: PINT-CLI-001, PINT-CLI-010, PINT-CLI-011, PINT-INV-010 |
| test_integration.py::test_cli_uses_magnitude_one_when_input_has_only_units | generated | system_e2e | positive | Pint-Convert CLI | covered | source: generated; clauses: PINT-CLI-012 |
| test_integration.py::test_cli_without_destination_converts_to_base_units | generated | system_e2e | positive | Pint-Convert CLI | covered | source: generated; clauses: PINT-CLI-002, PINT-CLI-003, PINT-CLI-009 |
| test_integration.py::test_cli_precision_option_controls_significant_digits | generated | system_e2e | positive | Pint-Convert CLI | covered | source: generated; clauses: PINT-CLI-004 |
| test_integration.py::test_cli_argument_error_exits_with_usage_status | generated | system_e2e | failure_path | Pint-Convert CLI; Error Semantics | covered | source: generated; clauses: PINT-CLI-008, PINT-ERR-013 |

Total: 92 | kept (covered): 92 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 92
