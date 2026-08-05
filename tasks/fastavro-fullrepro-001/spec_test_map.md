# Spec Test Map - fastavro-fullrepro-001

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_fullname_combines_namespace_and_name | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | fullname combines namespace and name |
| oracle/test_atomic.py::test_fullname_preserves_already_qualified_name | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | fullname preserves already qualified names |
| oracle/test_atomic.py::test_parse_schema_preserves_aliases_and_field_defaults | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | parse_schema keeps aliases and defaults |
| oracle/test_atomic.py::test_parse_schema_resolves_named_reference_with_shared_mapping | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | parse_schema resolves named references with shared names |
| oracle/test_atomic.py::test_parse_schema_unknown_named_type_raises_unknown_type | atomic | Error Semantics | covered | unresolved named type raises UnknownType |
| oracle/test_atomic.py::test_parse_schema_rejects_duplicate_enum_symbols | atomic | Error Semantics | covered | duplicate enum symbols raise SchemaParseException |
| oracle/test_atomic.py::test_parse_schema_rejects_decimal_scale_larger_than_precision | atomic | Error Semantics | covered | invalid decimal precision and scale raises SchemaParseException |
| oracle/test_atomic.py::test_expand_schema_replaces_named_reference_with_record_body | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | expand_schema exposes referenced schema body |
| oracle/test_atomic.py::test_canonical_form_omits_doc_alias_and_orders_record_keys | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | parsing canonical form omits non-canonical fields |
| oracle/test_atomic.py::test_fingerprint_crc64_avro_returns_hex_string_for_canonical_form | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | CRC-64-AVRO fingerprint is hexadecimal |
| oracle/test_atomic.py::test_fingerprint_unknown_algorithm_raises_value_error | atomic | Error Semantics | covered | unsupported fingerprint algorithm raises ValueError |
| oracle/test_atomic.py::test_flat_dict_repository_loads_schema_by_name | atomic | Schema Names, Parsing, Repositories, And Fingerprints | covered | FlatDictRepository loads name.avsc |
| oracle/test_atomic.py::test_flat_dict_repository_missing_file_raises_repository_error | atomic | Error Semantics | covered | missing repository schema raises SchemaRepositoryError |
| oracle/test_atomic.py::test_validate_accepts_matching_record | atomic | Validation And Record Selection | covered | validate accepts matching record |
| oracle/test_atomic.py::test_validate_returns_false_when_raise_errors_is_false | atomic | Validation And Record Selection | covered | validate returns False for invalid data when requested |
| oracle/test_atomic.py::test_validate_raises_for_invalid_record_by_default | atomic | Error Semantics | covered | validate raises by default for invalid records |
| oracle/test_atomic.py::test_validate_accepts_extra_field_not_declared_in_schema | atomic | Validation And Record Selection | covered | validate does not reject extra undeclared fields |
| oracle/test_atomic.py::test_validate_accepts_missing_defaulted_fields | atomic | Validation And Record Selection | covered | validate accepts omitted defaulted fields |
| oracle/test_atomic.py::test_validate_many_accepts_all_matching_records | atomic | Validation And Record Selection | covered | validate_many accepts all matching records |
| oracle/test_atomic.py::test_validate_many_returns_false_when_any_record_is_invalid | atomic | Validation And Record Selection | covered | validate_many returns False if one record is invalid |
| oracle/test_atomic.py::test_validate_union_accepts_tuple_branch_hint | atomic | Validation And Record Selection | covered | tuple notation selects union branch |
| oracle/test_atomic.py::test_validate_disable_tuple_notation_rejects_tuple_branch_hint | atomic | Validation And Record Selection | covered | disable_tuple_notation rejects tuple hint |
| oracle/test_atomic.py::test_schemaless_writer_encodes_signed_integer_zigzag_bytes | atomic | Binary, Object-Container, Blocks, And Schema Resolution | covered | schemaless_writer encodes signed integer bytes |
| oracle/test_atomic.py::test_schemaless_reader_decodes_signed_integer_zigzag_bytes | atomic | Binary, Object-Container, Blocks, And Schema Resolution | covered | schemaless_reader decodes signed integer bytes |
| oracle/test_atomic.py::test_schemaless_writer_encodes_utf8_string_with_length_prefix | atomic | Binary, Object-Container, Blocks, And Schema Resolution | covered | schemaless_writer encodes UTF-8 string bytes |
| oracle/test_atomic.py::test_schemaless_reader_decodes_utf8_string_payload | atomic | Binary, Object-Container, Blocks, And Schema Resolution | covered | schemaless_reader decodes UTF-8 string bytes |
| oracle/test_atomic.py::test_schemaless_reader_applies_reader_schema_default | atomic | Binary, Object-Container, Blocks, And Schema Resolution | covered | schemaless_reader applies reader default |
| oracle/test_atomic.py::test_schemaless_writer_strict_rejects_missing_required_field | atomic | Error Semantics | covered | schemaless_writer strict rejects missing required field |
| oracle/test_atomic.py::test_json_writer_emits_one_json_object_per_record | atomic | JSON Encoding And Logical Types | covered | json_writer writes record JSON |
| oracle/test_atomic.py::test_json_writer_wraps_union_values_by_default | atomic | JSON Encoding And Logical Types | covered | json_writer wraps union branch values |
| oracle/test_atomic.py::test_json_writer_can_omit_union_type_wrapper | atomic | JSON Encoding And Logical Types | covered | json_writer can omit union wrapper |
| oracle/test_atomic.py::test_json_reader_reads_union_wrapper_payload | atomic | JSON Encoding And Logical Types | covered | json_reader reads wrapped union value |
| oracle/test_atomic.py::test_json_reader_applies_reader_schema_default | atomic | JSON Encoding And Logical Types | covered | json_reader applies reader defaults |
| oracle/test_atomic.py::test_is_avro_returns_false_for_non_avro_buffer | atomic | Binary, Object-Container, Blocks, And Schema Resolution | covered | is_avro rejects non-container bytes |
| oracle/test_atomic.py::test_is_avro_recognizes_object_container_magic_prefix | atomic | Binary, Object-Container, Blocks, And Schema Resolution | covered | is_avro recognizes object-container magic |
| oracle/test_atomic.py::test_version_is_importable_string | atomic | Installable Surface | covered | __version__ is importable string |
| oracle/test_atomic.py::test_public_logical_type_registries_are_mutable_mappings | atomic | JSON Encoding And Logical Types | covered | LOGICAL_READERS and LOGICAL_WRITERS are mutable |
| oracle/test_integration.py::test_writer_reader_round_trip_preserves_records_and_reader_metadata | integration | Cross-View Invariants | covered | writer to reader preserves records and metadata |
| oracle/test_integration.py::test_writer_accepts_generator_and_reader_replays_all_items | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | generator records are written and read in order |
| oracle/test_integration.py::test_writer_with_validator_rejects_invalid_record_before_reading | integration | Validation And Record Selection | covered | writer validator composes with validate |
| oracle/test_integration.py::test_is_avro_recognizes_file_written_by_writer | integration | Cross-View Invariants | covered | is_avro recognizes writer output and reader can consume it |
| oracle/test_integration.py::test_container_reader_schema_adds_default_field | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | reader schema adds default field |
| oracle/test_integration.py::test_container_reader_schema_drops_writer_field | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | reader schema drops writer field |
| oracle/test_integration.py::test_reader_schema_uses_field_alias_to_read_renamed_field | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | field aliases resolve renamed fields |
| oracle/test_integration.py::test_reader_schema_uses_record_alias_to_match_writer_name | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | record aliases resolve writer record names |
| oracle/test_integration.py::test_schemaless_writer_reader_round_trip_nested_record | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | schemaless writer and reader round trip nested data |
| oracle/test_integration.py::test_tuple_notation_selects_specific_record_union_branch | integration | Validation And Record Selection | covered | tuple notation survives binary round trip |
| oracle/test_integration.py::test_record_type_hint_selects_record_branch_without_tuple | integration | Validation And Record Selection | covered | -type hint selects named record branch |
| oracle/test_integration.py::test_disable_tuple_notation_changes_writer_union_acceptance | integration | Error Semantics | covered | writer rejects tuple notation when disabled |
| oracle/test_integration.py::test_block_reader_exposes_blocks_with_records_and_container_metadata | integration | Cross-View Invariants | covered | block_reader records and metadata agree with container |
| oracle/test_integration.py::test_deflate_codec_round_trip_uses_reader_codec_projection | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | deflate codec round trips and exposes codec |
| oracle/test_integration.py::test_json_writer_reader_round_trip_multiple_records | integration | JSON Encoding And Logical Types | covered | json_writer and json_reader round trip multiple records |
| oracle/test_integration.py::test_json_union_wrapper_round_trip_with_reader_schema | integration | JSON Encoding And Logical Types | covered | JSON union wrapper composes with reader schema defaults |
| oracle/test_integration.py::test_unwrapped_union_json_is_readable_with_selected_branch_schema | integration | JSON Encoding And Logical Types | covered | unwrapped union JSON is readable through the selected branch schema |
| oracle/test_integration.py::test_decimal_logical_type_round_trips_through_binary_container | integration | JSON Encoding And Logical Types | covered | decimal logical type round trips through binary container |
| oracle/test_integration.py::test_uuid_and_date_logical_types_round_trip_through_json | integration | JSON Encoding And Logical Types | covered | UUID and date logical types round trip through JSON |
| oracle/test_integration.py::test_custom_logical_type_hooks_apply_to_writer_and_reader | integration | JSON Encoding And Logical Types | covered | custom logical hooks apply to writer and reader |
| oracle/test_integration.py::test_parse_canonical_form_and_fingerprint_stay_stable_after_round_trip | integration | Cross-View Invariants | covered | canonical form and fingerprint stable after container read |
| oracle/test_integration.py::test_load_schema_with_flat_dict_repository_resolves_references | integration | Schema Names, Parsing, Repositories, And Fingerprints | covered | load_schema resolves repository references |
| oracle/test_integration.py::test_load_schema_ordered_resolves_later_schema_files | integration | Schema Names, Parsing, Repositories, And Fingerprints | covered | load_schema_ordered resolves ordered files |
| oracle/test_integration.py::test_load_schema_missing_repository_reference_propagates_repository_error | integration | Error Semantics | covered | repository missing reference propagates public schema error |
| oracle/test_integration.py::test_cli_record_output_matches_reader_projection | integration | Command Line Behavior | covered | CLI record output matches reader records |
| oracle/test_integration.py::test_cli_pretty_print_outputs_json_array_style_records | integration | Command Line Behavior | covered | CLI pretty output prints readable record JSON |
| oracle/test_integration.py::test_cli_schema_output_matches_container_schema | integration | Command Line Behavior | covered | CLI schema output matches reader schema |
| oracle/test_integration.py::test_cli_metadata_output_includes_user_metadata_and_codec | integration | Command Line Behavior | covered | CLI metadata includes user metadata and codec |
| oracle/test_integration.py::test_cli_codecs_lists_required_builtin_codecs | integration | Command Line Behavior | covered | CLI codecs lists built-in codecs |
| oracle/test_integration.py::test_cli_can_read_container_from_stdin | integration | Command Line Behavior | covered | CLI reads object-container bytes from stdin |
| oracle/test_integration.py::test_cli_version_uses_importable_package_version | integration | Command Line Behavior | covered | CLI version agrees with __version__ |
| oracle/test_integration.py::test_schema_parse_error_prevents_container_write | integration | Error Semantics | covered | schema parse error prevents writer use |
| oracle/test_integration.py::test_writer_strict_allow_default_serializes_defaulted_field | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | writer strict_allow_default serializes defaulted fields |
| oracle/test_integration.py::test_writer_strict_rejects_missing_defaulted_field_when_not_allowed | integration | Error Semantics | covered | writer strict rejects omitted defaulted fields when not allowed |
| oracle/test_integration.py::test_return_named_type_marks_selected_named_union_member | integration | Validation And Record Selection | covered | return_named_type marks selected named union member |
| oracle/test_integration.py::test_enum_reader_schema_uses_default_for_unknown_writer_symbol | integration | Binary, Object-Container, Blocks, And Schema Resolution | covered | enum reader default resolves unknown writer symbol |

final_scoreable: 73
