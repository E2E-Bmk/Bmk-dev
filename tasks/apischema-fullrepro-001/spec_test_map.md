# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_deserialize_int_accepts_integer_data` | atomic | Dictionary Conversion | covered |
| 2 | `oracle/test_atomic.py::test_deserialize_float_coerces_integer_value` | atomic | Dictionary Conversion | covered |
| 3 | `oracle/test_atomic.py::test_deserialize_optional_none_returns_none` | atomic | Typed Values And Collections | covered |
| 4 | `oracle/test_atomic.py::test_deserialize_list_structures_each_element` | atomic | Dictionary Conversion | covered |
| 5 | `oracle/test_atomic.py::test_deserialize_fixed_tuple_uses_position_types` | atomic | Typed Values And Collections | covered |
| 6 | `oracle/test_atomic.py::test_deserialize_mapping_structures_keys_and_values` | atomic | Typed Values And Collections | covered |
| 7 | `oracle/test_atomic.py::test_deserialize_literal_accepts_declared_value` | atomic | Typed Values And Collections | covered |
| 8 | `oracle/test_atomic.py::test_deserialize_enum_uses_member_value` | atomic | Typed Values And Collections | covered |
| 9 | `oracle/test_atomic.py::test_deserialize_new_type_uses_base_type` | atomic | Typed Values And Collections | covered |
| 10 | `oracle/test_atomic.py::test_deserialize_bytes_uses_base64_text` | atomic | Typed Values And Collections | covered |
| 11 | `oracle/test_atomic.py::test_deserialize_date_uses_iso_text` | atomic | Typed Values And Collections | covered |
| 12 | `oracle/test_atomic.py::test_deserialize_uuid_uses_string_form` | atomic | Typed Values And Collections | covered |
| 13 | `oracle/test_atomic.py::test_deserialize_any_returns_original_object` | atomic | Typed Values And Collections | covered |
| 14 | `oracle/test_atomic.py::test_deserialize_with_coerce_converts_string_integer` | atomic | Dictionary Conversion | covered |
| 15 | `oracle/test_atomic.py::test_deserialize_additional_properties_accepts_unknown_keys` | atomic | Field Metadata And Configuration | covered |
| 16 | `oracle/test_atomic.py::test_serialize_fixed_tuple_as_json_list` | atomic | Typed Values And Collections | covered |
| 17 | `oracle/test_atomic.py::test_serialize_any_recurses_through_runtime_mapping` | atomic | Typed Values And Collections | covered |
| 18 | `oracle/test_atomic.py::test_serialize_aliaser_changes_dataclass_keys` | atomic | Field Metadata And Configuration | covered |
| 19 | `oracle/test_atomic.py::test_serialize_exclude_none_removes_none_fields` | atomic | Field Metadata And Configuration | covered |
| 20 | `oracle/test_atomic.py::test_serialize_exclude_defaults_removes_default_fields` | atomic | Field Metadata And Configuration | covered |
| 21 | `oracle/test_atomic.py::test_serialize_no_copy_can_return_original_mapping` | atomic | Dictionary Conversion | covered |
| 22 | `oracle/test_atomic.py::test_deserialization_schema_exposes_dataclass_properties` | atomic | Schema Projection | covered |
| 23 | `oracle/test_atomic.py::test_serialization_schema_exposes_array_items` | atomic | Schema Projection | covered |
| 24 | `oracle/test_atomic.py::test_schema_constraint_appears_in_json_schema` | atomic | Schema Projection | covered |
| 25 | `oracle/test_atomic.py::test_field_alias_appears_in_schema_properties` | atomic | Schema Projection | covered |
| 26 | `oracle/test_atomic.py::test_json_schema_draft_seven_uses_definitions_keyword` | atomic | Schema Projection | covered |
| 27 | `oracle/test_atomic.py::test_type_name_changes_schema_reference_name` | atomic | Schema Projection | covered |
| 28 | `oracle/test_atomic.py::test_definitions_schema_returns_referenced_definition` | atomic | Schema Projection | covered |
| 29 | `oracle/test_atomic.py::test_undefined_default_is_omitted_from_serialization` | atomic | Field Metadata And Configuration | covered |
| 30 | `oracle/test_atomic.py::test_serialized_property_is_added_to_output` | atomic | Field Metadata And Configuration | covered |
| 31 | `oracle/test_atomic.py::test_order_decorator_controls_serialized_key_order` | atomic | Field Metadata And Configuration | covered |
| 32 | `oracle/test_atomic.py::test_deserialization_method_returns_callable_for_repeated_use` | atomic | Dictionary Conversion | covered |
| 33 | `oracle/test_atomic.py::test_serialization_method_returns_callable_for_repeated_use` | atomic | Dictionary Conversion | covered |
| 34 | `oracle/test_atomic.py::test_validation_error_exposes_public_error_locations` | atomic | Validation And Errors | covered |
| 35 | `oracle/test_atomic.py::test_unsupported_class_raises_public_unsupported` | atomic | Validation And Errors | covered |
| 36 | `oracle/test_atomic.py::test_as_names_uses_enum_names_for_both_projections` | atomic | Typed Values And Collections | covered |
| 37 | `oracle/test_integration.py::test_user_round_trip_connects_deserialization_and_serialization` | integration | Dictionary Conversion | covered |
| 38 | `oracle/test_integration.py::test_nested_dataclass_round_trip_preserves_both_object_levels` | integration | Dictionary Conversion | covered |
| 39 | `oracle/test_integration.py::test_list_of_dataclasses_round_trip_preserves_order` | integration | Dictionary Conversion | covered |
| 40 | `oracle/test_integration.py::test_mapping_of_dataclasses_round_trip_preserves_mapping_keys` | integration | Typed Values And Collections | covered |
| 41 | `oracle/test_integration.py::test_absent_default_fields_deserialize_and_serialize_consistently` | integration | Field Metadata And Configuration | covered |
| 42 | `oracle/test_integration.py::test_exclude_none_output_deserializes_back_to_default` | integration | Field Metadata And Configuration | covered |
| 43 | `oracle/test_integration.py::test_exclude_defaults_output_deserializes_back_to_defaults` | integration | Field Metadata And Configuration | covered |
| 44 | `oracle/test_integration.py::test_field_alias_is_shared_by_round_trip_and_schema` | integration | Schema Projection | covered |
| 45 | `oracle/test_integration.py::test_runtime_aliaser_is_shared_by_deserialization_serialization_and_schema` | integration | Schema Projection | covered |
| 46 | `oracle/test_integration.py::test_user_schema_properties_match_serialized_keys` | integration | Schema Projection | covered |
| 47 | `oracle/test_integration.py::test_nested_schema_and_serialization_share_child_property_names` | integration | Schema Projection | covered |
| 48 | `oracle/test_integration.py::test_nested_validation_error_location_matches_model_path` | integration | Validation And Errors | covered |
| 49 | `oracle/test_integration.py::test_default_strictness_rejects_unknown_property_and_schema_disallows_it` | integration | Schema Projection | covered |
| 50 | `oracle/test_integration.py::test_additional_properties_mode_accepts_input_but_serializes_known_model` | integration | Field Metadata And Configuration | covered |
| 51 | `oracle/test_integration.py::test_coercion_flows_through_dataclass_then_serializes_typed_values` | integration | Dictionary Conversion | covered |
| 52 | `oracle/test_integration.py::test_reusable_methods_round_trip_multiple_dataclass_values` | integration | Dictionary Conversion | covered |
| 53 | `oracle/test_integration.py::test_named_enum_round_trip_and_schema_use_member_names` | integration | Schema Projection | covered |
| 54 | `oracle/test_integration.py::test_value_enum_round_trip_and_schema_use_member_values` | integration | Schema Projection | covered |
| 55 | `oracle/test_integration.py::test_named_type_reference_and_definition_describe_round_trip_model` | integration | Schema Projection | covered |
| 56 | `oracle/test_integration.py::test_serialized_method_is_present_only_in_output_projection` | integration | Field Metadata And Configuration | covered |
| 57 | `oracle/test_integration.py::test_declared_order_controls_payload_and_output_schema_property_order` | integration | Schema Projection | covered |
| 58 | `oracle/test_integration.py::test_constrained_field_accepts_valid_data_and_projects_schema_bounds` | integration | Schema Projection | covered |
| 59 | `oracle/test_integration.py::test_constrained_field_rejects_out_of_range_data_at_field_location` | integration | Validation And Errors | covered |
| 60 | `oracle/test_integration.py::test_standard_wire_types_round_trip_through_one_model` | integration | Typed Values And Collections | covered |
| 61 | `oracle/test_integration.py::test_standard_wire_type_schema_matches_string_payload_projection` | integration | Schema Projection | covered |
| 62 | `oracle/test_integration.py::test_literal_field_round_trip_and_schema_share_allowed_values` | integration | Schema Projection | covered |
| 63 | `oracle/test_integration.py::test_newtype_field_round_trip_and_schema_use_underlying_integer` | integration | Schema Projection | covered |
| 64 | `oracle/test_integration.py::test_fixed_tuple_field_round_trip_and_schema_preserve_positions` | integration | Schema Projection | covered |
| 65 | `oracle/test_integration.py::test_optional_field_round_trips_none_and_integer_and_schema_allows_null` | integration | Schema Projection | covered |
| 66 | `oracle/test_integration.py::test_integer_key_mapping_coerces_input_and_preserves_typed_output_keys` | integration | Typed Values And Collections | covered |
| 67 | `oracle/test_integration.py::test_undefined_field_round_trip_preserves_absence` | integration | Field Metadata And Configuration | covered |
| 68 | `oracle/test_integration.py::test_set_field_round_trip_and_schema_require_unique_items` | integration | Schema Projection | covered |
| 69 | `oracle/test_integration.py::test_any_field_preserves_json_shape_across_both_projections` | integration | Typed Values And Collections | covered |
| 70 | `oracle/test_integration.py::test_fall_back_on_default_recovers_invalid_field_then_serializes_default` | integration | Field Metadata And Configuration | covered |
| 71 | `oracle/test_integration.py::test_input_and_output_schema_share_shape_with_directional_required_fields` | integration | Schema Projection | covered |

final_scoreable: 71
