# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_field_options_preserves_standard_and_extra_metadata` | atomic | Field Metadata And Configuration | covered |
| 2 | `oracle/test_atomic.py::test_pass_through_strategy_returns_original_objects` | atomic | Strategies And Dialects | covered |
| 3 | `oracle/test_atomic.py::test_rounded_decimal_quantizes_and_deserializes_strings` | atomic | Strategies And Dialects | covered |
| 4 | `oracle/test_atomic.py::test_discriminator_requires_at_least_one_inclusion_direction` | atomic | Strategies And Dialects | covered |
| 5 | `oracle/test_atomic.py::test_alias_compares_by_name_and_hashes_by_name` | atomic | Strategies And Dialects | covered |
| 6 | `oracle/test_atomic.py::test_to_dict_serializes_primitive_dataclass_fields` | atomic | Dictionary Conversion | covered |
| 7 | `oracle/test_atomic.py::test_from_dict_deserializes_primitive_dataclass_fields` | atomic | Dictionary Conversion | covered |
| 8 | `oracle/test_atomic.py::test_from_dict_missing_required_field_raises_missing_field` | atomic | Dictionary Conversion | covered |
| 9 | `oracle/test_atomic.py::test_from_dict_invalid_integer_value_raises_invalid_field_value` | atomic | Dictionary Conversion | covered |
| 10 | `oracle/test_atomic.py::test_nested_dataclass_to_dict_serializes_nested_public_shape` | atomic | Dictionary Conversion | covered |
| 11 | `oracle/test_atomic.py::test_nested_dataclass_from_dict_builds_nested_objects` | atomic | Dictionary Conversion | covered |
| 12 | `oracle/test_atomic.py::test_list_of_dataclasses_rounds_through_basic_form` | atomic | Dictionary Conversion | covered |
| 13 | `oracle/test_atomic.py::test_datetime_and_date_values_use_iso_basic_form` | atomic | Dictionary Conversion | covered |
| 14 | `oracle/test_atomic.py::test_datetime_and_date_values_deserialize_from_iso_strings` | atomic | Dictionary Conversion | covered |
| 15 | `oracle/test_atomic.py::test_enum_fields_serialize_and_deserialize_by_value` | atomic | Dictionary Conversion | covered |
| 16 | `oracle/test_atomic.py::test_tuple_and_set_fields_use_basic_collection_forms` | atomic | Dictionary Conversion | covered |
| 17 | `oracle/test_atomic.py::test_namedtuple_defaults_to_list_representation` | atomic | Field Metadata And Configuration | covered |
| 18 | `oracle/test_atomic.py::test_namedtuple_as_dict_config_uses_keyed_representation` | atomic | Field Metadata And Configuration | covered |
| 19 | `oracle/test_atomic.py::test_field_option_alias_controls_input_key` | atomic | Field Metadata And Configuration | covered |
| 20 | `oracle/test_atomic.py::test_field_option_serialize_callable_controls_output_value` | atomic | Field Metadata And Configuration | covered |
| 21 | `oracle/test_atomic.py::test_field_option_deserialize_callable_controls_input_value` | atomic | Field Metadata And Configuration | covered |
| 22 | `oracle/test_atomic.py::test_config_aliases_and_serialize_by_alias_control_output_keys` | atomic | Field Metadata And Configuration | covered |
| 23 | `oracle/test_atomic.py::test_allow_deserialization_not_by_alias_accepts_field_names` | atomic | Field Metadata And Configuration | covered |
| 24 | `oracle/test_atomic.py::test_omit_none_config_removes_none_fields_from_output` | atomic | Field Metadata And Configuration | covered |
| 25 | `oracle/test_atomic.py::test_omit_default_config_removes_default_equal_fields` | atomic | Field Metadata And Configuration | covered |
| 26 | `oracle/test_atomic.py::test_sort_keys_config_orders_serialized_mapping_keys` | atomic | Field Metadata And Configuration | covered |
| 27 | `oracle/test_atomic.py::test_forbid_extra_keys_config_raises_extra_keys_error` | atomic | Field Metadata And Configuration | covered |
| 28 | `oracle/test_atomic.py::test_config_serialization_strategy_applies_to_registered_type` | atomic | Strategies And Dialects | covered |
| 29 | `oracle/test_atomic.py::test_serialization_strategy_match_subclasses_handles_enum_subclass` | atomic | Strategies And Dialects | covered |
| 30 | `oracle/test_atomic.py::test_serializable_type_uses_custom_serialize_deserialize_methods` | atomic | Strategies And Dialects | covered |
| 31 | `oracle/test_atomic.py::test_serializable_type_with_annotations_transforms_nested_values` | atomic | Strategies And Dialects | covered |
| 32 | `oracle/test_atomic.py::test_basic_encoder_serializes_typed_shape_to_basic_form` | atomic | Dictionary Conversion | covered |
| 33 | `oracle/test_atomic.py::test_basic_decoder_deserializes_typed_shape_from_basic_form` | atomic | Dictionary Conversion | covered |
| 34 | `oracle/test_atomic.py::test_json_encoder_and_decoder_handle_dataclass_lists` | atomic | Typed Codecs | covered |
| 35 | `oracle/test_atomic.py::test_json_convenience_functions_encode_and_decode_typed_values` | atomic | Typed Codecs | covered |
| 36 | `oracle/test_atomic.py::test_json_schema_for_primitive_types_uses_expected_type_names` | atomic | Schema Projection | covered |
| 37 | `oracle/test_atomic.py::test_json_schema_for_dataclass_includes_properties_and_required_fields` | atomic | Schema Projection | covered |
| 38 | `oracle/test_atomic.py::test_json_schema_annotations_apply_validation_keywords` | atomic | Schema Projection | covered |
| 39 | `oracle/test_atomic.py::test_json_schema_field_metadata_adds_descriptions_and_constraints` | atomic | Schema Projection | covered |
| 40 | `oracle/test_integration.py::test_dict_round_trip_preserves_nested_dataclass_values` | integration | Dictionary Conversion | covered |
| 41 | `oracle/test_integration.py::test_alias_config_round_trip_uses_external_key_projection` | integration | Field Metadata And Configuration | covered |
| 42 | `oracle/test_integration.py::test_omit_none_and_default_config_compose_in_single_projection` | integration | Field Metadata And Configuration | covered |
| 43 | `oracle/test_integration.py::test_namedtuple_as_dict_round_trip_inside_nested_collection` | integration | Field Metadata And Configuration | covered |
| 44 | `oracle/test_integration.py::test_config_strategy_applies_through_basic_codec_encoder_and_decoder` | integration | Typed Codecs | covered |
| 45 | `oracle/test_integration.py::test_json_codec_round_trip_respects_dataclass_field_aliases` | integration | Typed Codecs | covered |
| 46 | `oracle/test_integration.py::test_json_mixin_round_trip_uses_to_dict_and_from_dict_rules` | integration | Typed Codecs | covered |
| 47 | `oracle/test_integration.py::test_json_mixin_custom_encoder_decoder_still_wraps_dict_conversion` | integration | Typed Codecs | covered |
| 48 | `oracle/test_integration.py::test_yaml_mixin_round_trip_preserves_date_conversion` | integration | Typed Codecs | covered |
| 49 | `oracle/test_integration.py::test_toml_mixin_omits_none_and_round_trips_date_values` | integration | Typed Codecs | covered |
| 50 | `oracle/test_integration.py::test_messagepack_mixin_round_trip_preserves_binary_fields` | integration | Typed Codecs | covered |
| 51 | `oracle/test_integration.py::test_field_alias_takes_precedence_over_config_alias` | integration | Field Metadata And Configuration | covered |
| 52 | `oracle/test_integration.py::test_alias_input_mode_accepts_alias_and_field_name_but_still_requires_one` | integration | Field Metadata And Configuration | covered |
| 53 | `oracle/test_integration.py::test_forbid_extra_keys_checks_alias_aware_input_projection` | integration | Field Metadata And Configuration | covered |
| 54 | `oracle/test_integration.py::test_strategy_annotations_convert_before_custom_deserialize_and_after_serialize` | integration | Strategies And Dialects | covered |
| 55 | `oracle/test_integration.py::test_more_specific_strategy_overrides_matching_base_strategy` | integration | Strategies And Dialects | covered |
| 56 | `oracle/test_integration.py::test_dialect_argument_overrides_config_when_code_generation_option_enabled` | integration | Strategies And Dialects | covered |
| 57 | `oracle/test_integration.py::test_by_alias_keyword_overrides_config_when_option_enabled` | integration | Field Metadata And Configuration | covered |
| 58 | `oracle/test_integration.py::test_omit_none_keyword_overrides_config_when_option_enabled` | integration | Field Metadata And Configuration | covered |
| 59 | `oracle/test_integration.py::test_serialization_context_reaches_pre_and_post_hooks_when_enabled` | integration | Field Metadata And Configuration | covered |
| 60 | `oracle/test_integration.py::test_deserialization_and_serialization_hooks_wrap_nested_conversion` | integration | Field Metadata And Configuration | covered |
| 61 | `oracle/test_integration.py::test_schema_builder_builds_refs_and_later_definitions_from_same_context` | integration | Schema Projection | covered |
| 62 | `oracle/test_integration.py::test_schema_generation_combines_dataclass_fields_and_annotated_constraints` | integration | Schema Projection | covered |
| 63 | `oracle/test_integration.py::test_schema_overlay_keeps_regular_type_and_adds_content_keywords` | integration | Schema Projection | covered |
| 64 | `oracle/test_integration.py::test_schema_and_json_codec_project_same_dataclass_field_names` | integration | Schema Projection | covered |
| 65 | `oracle/test_integration.py::test_custom_strategy_changes_dict_and_json_but_schema_keeps_declared_type` | integration | Schema Projection | covered |
| 66 | `oracle/test_integration.py::test_basic_codec_and_dict_mixin_agree_on_nested_basic_form` | integration | Typed Codecs | covered |
| 67 | `oracle/test_integration.py::test_json_mixin_and_dict_mixin_agree_on_alias_projection` | integration | Typed Codecs | covered |
| 68 | `oracle/test_integration.py::test_dialect_merge_combines_strategy_and_omit_policy` | integration | Strategies And Dialects | covered |
| 69 | `oracle/test_integration.py::test_codec_default_dialect_applies_without_per_call_dialect` | integration | Typed Codecs | covered |
| 70 | `oracle/test_integration.py::test_json_decoder_propagates_field_conversion_errors` | integration | Typed Codecs | covered |
| 71 | `oracle/test_integration.py::test_schema_generation_uses_alias_metadata_for_property_names` | integration | Schema Projection | covered |
| 72 | `oracle/test_integration.py::test_json_mixin_propagates_forbid_extra_keys_errors_from_dict_layer` | integration | Typed Codecs | covered |
| 73 | `oracle/test_integration.py::test_sort_keys_config_is_reflected_in_json_output_order` | integration | Typed Codecs | covered |
| 74 | `oracle/test_integration.py::test_serializable_type_projection_is_shared_by_dict_and_basic_codec` | integration | Typed Codecs | covered |
| 75 | `oracle/test_integration.py::test_schema_builder_definitions_keep_annotation_constraints` | integration | Schema Projection | covered |
| 76 | `oracle/test_integration.py::test_schema_with_dialect_uri_and_ref_prefix_controls_public_reference_view` | integration | Schema Projection | covered |
| 77 | `oracle/test_integration.py::test_schema_required_list_tracks_alias_names_for_required_fields` | integration | Schema Projection | covered |
| 78 | `oracle/test_integration.py::test_binary_model_uses_format_specific_wire_types_consistently` | integration | Typed Codecs | covered |

final_scoreable: 78
