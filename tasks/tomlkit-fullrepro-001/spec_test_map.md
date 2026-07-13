# tomlkit spec-test map v4

oracle_version: 20260704-repair-v4
oracle_source: upstream_plus_generated
scorer_isolation: score_pytest_original.py with --remove-path tomlkit
base_nodeids: 96
upstream_base_nodeids: 51
generated_base_nodeids: 45
layers_base: atomic=39, integration=38, system_e2e=19

This repair keeps the v3 public upstream surface and adds a benchmark-owned generated carrier for public item/document behavior lost when upstream `tests/test_items.py` and `tests/test_parser.py` were excluded for collection-time `tomlkit.parser.Parser` imports.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `tests/test_api.py::test_parse_can_parse_valid_toml_files` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_load_from_file_object` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_parsed_document_are_properly_json_representable` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files` | atomic | ## Error Semantics | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_a_raw_dict_can_be_dumped` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_mapping_types_can_be_dumped` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_parsed_document_can_be_dumped_with_sorted_keys` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_dumps_weird_object` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_dump_tuple_value_as_array` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_dump_to_file_object` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_dump_nested_dotted_table` | integration | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_integer` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_float` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_boolean` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_date` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_time` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_datetime` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_array` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_table` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_inline_table` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_aot` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_key` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_key_value` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_string` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_item_dict_to_table` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_item_mixed_aray` | atomic | ### Parsing and Loading + ### Dumping and Writing | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_build_super_table` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_add_dotted_key` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_value_parses_boolean` | integration | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start` | atomic | ## Error Semantics | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_value_rejects_values_having_true_prefix` | atomic | ## Error Semantics | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_value_rejects_values_having_false_prefix` | atomic | ## Error Semantics | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_value_rejects_values_with_appendage` | atomic | ## Error Semantics | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_create_super_table_with_table` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_create_super_table_with_aot` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_create_string` | atomic | ### Item Creation Helpers | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_create_string_with_invalid_characters` | atomic | ## Error Semantics | covered | upstream public API test retained from filter v3 |
| `tests/test_api.py::test_parse_empty_quoted_table_name` | integration | ## Error Semantics | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_toml_file` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_keep_old_eol` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_keep_old_eol_2` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_mixed_eol` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_consistent_eol` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_consistent_eol_2` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_default_eol_is_os_linesep` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_toml_file.py::test_readwrite_eol_windows` | system_e2e | ### TOMLFile + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_write.py::test_write_backslash` | integration | ### Dumping and Writing + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_write.py::test_escape_special_characters_in_key` | integration | ### Dumping and Writing + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_write.py::test_write_inline_table_in_nested_arrays` | integration | ### Dumping and Writing + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `tests/test_write.py::test_serialize_aot_with_nested_tables` | integration | ### Dumping and Writing + ### Style Preservation | covered | upstream public API test retained from filter v3 |
| `filter/generated_tests.py::test_generated_scalar_items_unwrap_to_plain_values` | atomic | ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_array_unwraps_nested_values` | atomic | ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_table_unwraps_nested_mapping` | atomic | ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_inline_table_unwraps_mapping` | atomic | ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_array_behaves_like_mutable_list` | integration | ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_array_clear_round_trips_empty_array` | atomic | ### Item Creation Helpers | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_multiline_array_append_preserves_layout` | system_e2e | ### Style Preservation + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_array_comment_survives_append` | system_e2e | ### Style Preservation + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_array_remove_keeps_valid_toml` | system_e2e | ### Document Mutation + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_inline_table_deletion_removes_separator` | integration | ### Document Mutation + ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_parsed_inline_table_delete_and_append` | system_e2e | ### Style Preservation + ### Document Mutation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_inline_table_update_trims_item_comment` | integration | ### Public Items + ### Style Preservation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_key_escapes_control_characters` | atomic | ### Item Creation Helpers | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_dump_escapes_special_mapping_keys` | integration | ### Dumping and Writing + ### TOML Data Model | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_dotted_key_helper_serializes_in_table` | integration | ### Item Creation Helpers + ### TOML Data Model | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_document_adds_comment_newline_and_table` | system_e2e | ### Document Creation + ### Style Preservation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_document_setdefault_preserves_mapping_semantics` | integration | ### TOMLDocument | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_document_pop_removes_serialized_key` | integration | ### TOMLDocument + ### Document Mutation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_document_copy_is_independent_mapping` | atomic | ### TOMLDocument | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_nested_table_assignment_serializes_header` | integration | ### TOMLDocument + ### TOML Data Model | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_replacing_table_with_scalar_keeps_valid_document` | system_e2e | ### Document Mutation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_dotted_keys_are_accessible_as_nested_values` | integration | ### TOML Data Model + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_out_of_order_table_edit_updates_correct_section` | system_e2e | ### Document Mutation + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_item_dict_converts_to_table` | integration | ### Sorting and Plain Mapping Conversion | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_item_dict_conversion_can_sort_keys` | integration | ### Sorting and Plain Mapping Conversion | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_array_of_dicts_converts_to_aot` | integration | ### Sorting and Plain Mapping Conversion + ### TOML Data Model | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_aot_helper_appends_tables` | integration | ### Item Creation Helpers + ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_custom_encoder_for_decimal_item` | integration | ### Custom Encoders | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_custom_encoder_receives_context_kwargs` | integration | ### Custom Encoders | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_custom_encoder_unregister_restores_conversion_error` | atomic | ### Custom Encoders + ## Error Semantics | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_unsupported_object_raises_conversion_error` | atomic | ## Error Semantics | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_missing_table_key_raises_public_error` | atomic | ## Error Semantics | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_duplicate_key_parse_raises_tomlkit_error` | atomic | ## Error Semantics | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_invalid_scalar_value_raises_tomlkit_error` | atomic | ## Error Semantics | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_string_append_preserves_escape` | integration | ### Public Items + ### Style Preservation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_integer_arithmetic_updates_serialized_value` | integration | ### Public Items + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_float_arithmetic_updates_serialized_value` | integration | ### Public Items + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_string_mutation_keeps_inline_comment` | system_e2e | ### Style Preservation + ### Document Mutation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_table_update_replaces_existing_key` | integration | ### Public Items + ### Document Mutation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_table_get_and_setdefault_match_mapping_behavior` | atomic | ### Public Items | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_file_style_cycle_via_string_projection` | system_e2e | ## Representative Workflows + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_inline_table_array_round_trip` | system_e2e | ### TOML Data Model + ## Cross-View Invariants | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_super_table_headers_are_not_redundant` | system_e2e | ### Document Mutation + ### Style Preservation | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_dump_sorted_plain_mapping_is_deterministic` | integration | ### Sorting and Plain Mapping Conversion | covered | generated public carrier; no private tomlkit.parser import |
| `filter/generated_tests.py::test_generated_nested_array_with_inline_table_dumps_and_loads` | integration | ### Dumping and Writing + ### TOML Data Model | covered | generated public carrier; no private tomlkit.parser import |

Total: 96 | kept (covered): 96 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 96
