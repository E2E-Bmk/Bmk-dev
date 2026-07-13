# tomlkit spec-test map v1

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[example]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[fruit]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[hard]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[sections_with_same_start]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[pyproject]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[0.5.0]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[test]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[newline_in_strings]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[preserve_quotes_in_string]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[string_slash_whitespace_newline]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_can_parse_valid_toml_files[table_names]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[example]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[fruit]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[hard]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[sections_with_same_start]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[pyproject]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[0.5.0]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[test]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[newline_in_strings]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[preserve_quotes_in_string]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[string_slash_whitespace_newline]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_load_from_file_object[table_names]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parsed_document_are_properly_json_representable[0.5.0]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parsed_document_are_properly_json_representable[pyproject]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parsed_document_are_properly_json_representable[table_names]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[section_with_trailing_characters-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[key_value_with_trailing_chars-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[array_with_invalid_chars-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[invalid_number-InvalidNumberError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[invalid_date-InvalidDateError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[invalid_time-InvalidTimeError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[invalid_datetime-InvalidDateTimeError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[trailing_comma-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[newline_in_singleline_string-InvalidControlChar]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[string_slash_whitespace_char-InvalidCharInStringError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[array_no_comma-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[array_duplicate_comma-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[array_leading_comma-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[inline_table_no_comma-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[inline_table_duplicate_comma-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files[inline_table_leading_comma-UnexpectedCharError]` | atomic | 搂Error Semantics | covered | invalid TOML raises TOMLKit parse/invalid-value errors; exact message not required |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[example]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[fruit]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[hard]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[sections_with_same_start]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[pyproject]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[0.5.0]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[test]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_original_string_and_dumped_string_are_equal[table_names]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_a_raw_dict_can_be_dumped` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_mapping_types_can_be_dumped` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_parsed_document_can_be_dumped_with_sorted_keys` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_dumps_weird_object` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_dump_tuple_value_as_array` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_dump_to_file_object` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_dump_nested_dotted_table` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_integer` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_float` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_boolean` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_date` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_time` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_datetime` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_array` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_table` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_inline_table` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_aot` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_key` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_key_value` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_string` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_item_dict_to_table` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_item_mixed_aray` | atomic | 搂Public API | covered | public top-level API behavior |
| `tests/test_api.py::test_build_super_table` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_add_dotted_key` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_value_parses_boolean[true-True]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_value_parses_boolean[false-False]` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[t]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[f]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[tru]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[fals]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[test]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[friend]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[truthy]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_looking_like_bool_at_start[falsify]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_true_prefix[truee]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_true_prefix[truely]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_true_prefix[true-thoughts]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_true_prefix[true_hip_hop]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_false_prefix[falsee]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_false_prefix[falsely]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_false_prefix[false-ideas]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_having_false_prefix[false_prophet]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage["foo"1.2]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[truefalse]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[1.0false]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[100true]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[truetrue]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[falsefalse]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[1.2.3.4]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[[][]]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[{a=[][]}[]]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[true[]]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_value_rejects_values_with_appendage[false{a=1}]` | atomic | 搂Error Semantics | covered | invalid public value/key input raises TOMLKit error |
| `tests/test_api.py::test_create_super_table_with_table` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_super_table_with_aot` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs0-My\nString-"My\\nString"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs1-My String\t-"My String\t"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs2-My String\t-'My String\t']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs3-My String\t-'My String\t']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs4-My String\x01-"My String\\u0001"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs5-My String\x0b-"My String\\u000b"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs6-My String\x08-"My String\\b"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs7-My String\x0c-"My String\\f"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs8-My String\x01-"My String\\u0001"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs9-My String\x06-"My String\\u0006"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs10-My String\x12-"My String\\u0012"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs11-My String\x7f-"My String\\u007f"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs12-My String\x01-"My String\x01"]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs13-\nMy\nString\n-"""\nMy\nString\n"""]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs14-My"String-"""My"String"""]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs15-My""String-"""My""String"""]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs16-My"""String-"""My""\\"String"""]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs17-My""""String-"""My""\\""String"""]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs18-"""My"""Str"""ing"""-"""""\\"My""\\"Str""\\"ing""\\""""]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs19-My\nString-'''My\nString''']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs20-My'String-'''My'String''']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs21-My\r\nString-'''My\r\nString''']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs22-C:\\Users\\nodejs\\templates-'C:\\Users\\nodejs\\templates']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs23-<\\i\\c*\\s*>-'<\\i\\c*\\s*>']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string[kwargs24-I [dw]on't need \\d{2} apples-'''I [dw]on't need \\d{2} apples''']` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs0-My'String]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs1-My\nString]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs2-My\r\nString]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs3-My\x08String]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs4-My\x08String]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs5-My\x0cString]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs6-My\x7fString]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_create_string_with_invalid_characters[kwargs7-My'''String]` | atomic | 搂Item Creation Helpers | covered | public helper function creates/parses TOML item |
| `tests/test_api.py::test_parse_empty_quoted_table_name` | integration | 搂Parsing and Loading + 搂Dumping and Writing | covered | parse/load/dump public API round trip or error behavior |
| `tests/test_build.py::test_build_example` | system_e2e | 搂Representative Workflows + 搂Document Mutation | covered | building and mutating documents preserves serialized TOML structure |
| `tests/test_build.py::test_add_remove` | system_e2e | 搂Representative Workflows + 搂Document Mutation | covered | building and mutating documents preserves serialized TOML structure |
| `tests/test_build.py::test_append_table_after_multiple_indices` | system_e2e | 搂Representative Workflows + 搂Document Mutation | covered | building and mutating documents preserves serialized TOML structure |
| `tests/test_build.py::test_top_level_keys_are_put_at_the_root_of_the_document` | system_e2e | 搂Representative Workflows + 搂Document Mutation | covered | building and mutating documents preserves serialized TOML structure |
| `tests/test_items.py::test_item_base_has_no_unwrap` | atomic | 鈥?| source-only | asserts abstract/base item behavior not exposed in public packet |
| `tests/test_items.py::test_integer_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_float_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_false_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_true_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_datetime_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_string_unwrap` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_null_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_aot_unwrap` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_aot_set_item` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_time_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_date_unwrap` | atomic | 搂Public Items | covered | item unwrap exposes semantic Python value |
| `tests/test_items.py::test_array_unwrap` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_abstract_table_unwrap` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_key_comparison` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_items_can_be_appended_to_and_removed_from_a_table` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_items_can_be_appended_to_and_removed_from_an_inline_table` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_inf_and_nan_are_supported` | atomic | 搂TOML Data Model | covered | TOML scalar value support |
| `tests/test_items.py::test_hex_octal_and_bin_integers_are_supported` | atomic | 搂TOML Data Model | covered | TOML scalar value support |
| `tests/test_items.py::test_key_automatically_sets_proper_string_type_if_not_bare` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_array_behaves_like_a_list` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_array_multiline` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_array_multiline_modify` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_append_to_empty_array` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_modify_array_with_comment` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_append_to_multiline_array_with_comment` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_append_dict_to_array` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_dicts_are_converted_to_tables` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_array_add_line` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_array_add_line_invalid_value` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_dicts_are_converted_to_tables_and_keep_order` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_dicts_are_converted_to_tables_and_are_sorted_if_requested` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_dicts_with_sub_dicts_are_properly_converted` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_item_array_of_dicts_converted_to_aot` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_add_float_to_int` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_sub_float_from_int` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_sub_int_from_float` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_add_sum_int_with_float` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_integers_behave_like_ints` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_floats_behave_like_floats` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_datetimes_behave_like_datetimes` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_dates_behave_like_dates` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_parse_datetime_followed_by_space` | atomic | 搂TOML Data Model | covered | TOML scalar value support |
| `tests/test_items.py::test_times_behave_like_times` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_strings_behave_like_strs` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_string_add_preserve_escapes` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_tables_behave_like_dicts` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_items_are_pickable` | atomic | 鈥?| source-only | copy/pickle object compatibility not specified by public docs |
| `tests/test_items.py::test_trim_comments_when_building_inline_table` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_deleting_inline_table_element_does_not_leave_trailing_separator` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_deleting_inline_table_element_does_not_leave_trailing_separator2` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_appending_to_parsed_inline_table_preserves_separator` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_booleans_comparison` | atomic | 鈥?| source-only | Python operator compatibility beyond public style-preserving TOML contract |
| `tests/test_items.py::test_table_copy` | atomic | 鈥?| source-only | copy/pickle object compatibility not specified by public docs |
| `tests/test_items.py::test_copy_copy` | atomic | 鈥?| source-only | copy/pickle object compatibility not specified by public docs |
| `tests/test_items.py::test_escape_key[\\-"\\\\"]` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_escape_key["-"\\""]` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_escape_key[\t-"\\t"]` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_escape_key[\x10-"\\u0010"]` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_custom_encoders` | integration | 搂Custom Encoders + 搂Sorting and Plain Mapping Conversion | covered | registered encoders participate in conversion/dumping |
| `tests/test_items.py::test_custom_encoders_with_parent_and_sort_keys` | integration | 搂Custom Encoders + 搂Sorting and Plain Mapping Conversion | covered | registered encoders participate in conversion/dumping |
| `tests/test_items.py::test_custom_encoders_backward_compatibility` | integration | 搂Custom Encoders + 搂Sorting and Plain Mapping Conversion | covered | registered encoders participate in conversion/dumping |
| `tests/test_items.py::test_custom_encoders_with_kwargs` | integration | 搂Custom Encoders + 搂Sorting and Plain Mapping Conversion | covered | registered encoders participate in conversion/dumping |
| `tests/test_items.py::test_custom_encoders_for_complex_objects` | integration | 搂Custom Encoders + 搂Sorting and Plain Mapping Conversion | covered | registered encoders participate in conversion/dumping |
| `tests/test_items.py::test_no_extra_minus_sign` | atomic | 搂Public Items | covered | public item behavior |
| `tests/test_items.py::test_serialize_table_with_dotted_key` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_not_showing_parent_header_for_super_table` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_removal_of_arrayitem_with_extra_whitespace` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_badly_formatted_array_and_item_removal` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_items.py::test_array_item_removal_newline_restore_next` | integration | 搂Public Items + 搂Style Preservation | covered | public item/container mutation and serialization behavior |
| `tests/test_parser.py::test_parser_should_raise_an_internal_error_if_parsing_wrong_type_of_string` | atomic | 鈥?| excluded | internal parser error path, not public behavior |
| `tests/test_parser.py::test_parser_should_raise_an_error_for_empty_tables` | atomic | 鈥?| excluded | parser-specific malformed input detail outside public contract |
| `tests/test_parser.py::test_parser_should_raise_an_error_if_equal_not_found` | atomic | 鈥?| excluded | parser-specific malformed input detail outside public contract |
| `tests/test_parser.py::test_parse_multiline_string_ignore_the_first_newline` | atomic | 搂TOML Data Model + 搂Style Preservation | covered | multiline string parsing and newline preservation are public TOML/style behavior |
| `tests/test_parser.py::test_parse_multiline_basic_string_with_crlf` | atomic | 搂TOML Data Model + 搂Style Preservation | covered | multiline string parsing and newline preservation are public TOML/style behavior |
| `tests/test_parser.py::test_parse_multiline_literal_string_with_crlf` | atomic | 搂TOML Data Model + 搂Style Preservation | covered | multiline string parsing and newline preservation are public TOML/style behavior |
| `tests/test_toml_document.py::test_document_is_a_dict` | atomic | 搂TOMLDocument | covered | document mapping/unwrap behavior |
| `tests/test_toml_document.py::test_toml_document_without_super_tables` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_toml_document_unwrap` | atomic | 搂TOMLDocument | covered | document mapping/unwrap behavior |
| `tests/test_toml_document.py::test_toml_document_with_dotted_keys` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_toml_document_super_table_with_different_sub_sections` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_adding_an_element_to_existing_table_with_ws_remove_ws` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_document_with_aot_after_sub_tables` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_document_with_new_sub_table_after_other_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_document_with_new_sub_table_after_other_table_delete` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_document_with_new_sub_table_after_other_table_replace` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_inserting_after_element_with_no_new_line_adds_a_new_line` | integration | 搂TOMLDocument | covered | document behavior |
| `tests/test_toml_document.py::test_inserting_after_deletion` | integration | 搂TOMLDocument | covered | document behavior |
| `tests/test_toml_document.py::test_toml_document_with_dotted_keys_inside_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_toml_document_with_super_aot_after_super_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_toml_document_has_always_a_new_line_after_table_header` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_toml_document_is_pickable` | atomic | 鈥?| source-only | copy/pickle object compatibility not specified by public docs |
| `tests/test_toml_document.py::test_toml_document_set_super_table_element` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_toml_document_can_be_copied` | atomic | 鈥?| source-only | copy/pickle object compatibility not specified by public docs |
| `tests/test_toml_document.py::test_getting_inline_table_is_still_an_inline_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_declare_sub_table_with_intermediate_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_values_can_still_be_set_for_out_of_order_tables` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_out_of_order_table_can_add_multiple_tables` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_out_of_order_tables_are_still_dicts` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_string_output_order_is_preserved_for_out_of_order_tables` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_remove_from_out_of_order_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_update_nested_out_of_order_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_updating_nested_value_keeps_correct_indent` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_repr` | atomic | 鈥?| source-only | object repr exactness is not public behavior |
| `tests/test_toml_document.py::test_deepcopy` | atomic | 鈥?| source-only | copy/pickle object compatibility not specified by public docs |
| `tests/test_toml_document.py::test_move_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_replace_with_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_replace_table_with_value` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_replace_preserve_sep` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_replace_with_table_of_nested` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_replace_with_aot_of_nested` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_replace_with_comment` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_no_spurious_whitespaces` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_pop_add_whitespace_and_insert_table_work_togheter` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_add_newline_before_super_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_remove_item_from_super_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_nested_table_update_display_name` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_build_table_with_dotted_key` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_parse_subtables_no_extra_indent` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_item_preserves_the_order` | integration | 搂TOMLDocument | covered | document behavior |
| `tests/test_toml_document.py::test_delete_out_of_order_table_key` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_overwrite_out_of_order_table_key` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_set_default_int` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_overwriting_out_of_order_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_delete_key_from_out_of_order_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_parse_aot_without_ending_newline` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_document.py::test_appending_to_super_table` | system_e2e | 搂TOMLDocument + 搂Document Mutation + 搂Cross-View Invariants | covered | document mutation must agree with semantic access and serialized TOML |
| `tests/test_toml_file.py::test_toml_file` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_toml_file.py::test_keep_old_eol` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_toml_file.py::test_keep_old_eol_2` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_toml_file.py::test_mixed_eol` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_toml_file.py::test_consistent_eol` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_toml_file.py::test_consistent_eol_2` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_toml_file.py::test_default_eol_is_os_linesep` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_toml_file.py::test_readwrite_eol_windows` | system_e2e | 搂TOMLFile + 搂Style Preservation | covered | TOMLFile read/write and user-visible whitespace/newline preservation |
| `tests/test_utils.py::test_parse_rfc3339_datetime[1979-05-27T07:32:00-expected0]` | atomic | 搂TOML Data Model | covered | RFC3339 date/time parsing as TOML scalar behavior |
| `tests/test_utils.py::test_parse_rfc3339_datetime[1979-05-27T07:32:00Z-expected1]` | atomic | 搂TOML Data Model | covered | RFC3339 date/time parsing as TOML scalar behavior |
| `tests/test_utils.py::test_parse_rfc3339_datetime[1979-05-27T07:32:00-07:00-expected2]` | atomic | 搂TOML Data Model | covered | RFC3339 date/time parsing as TOML scalar behavior |
| `tests/test_utils.py::test_parse_rfc3339_datetime[1979-05-27T00:32:00.999999-07:00-expected3]` | atomic | 搂TOML Data Model | covered | RFC3339 date/time parsing as TOML scalar behavior |
| `tests/test_utils.py::test_parse_rfc3339_date[1979-05-27-expected0]` | atomic | 搂TOML Data Model | covered | RFC3339 date/time parsing as TOML scalar behavior |
| `tests/test_utils.py::test_parse_rfc3339_time[12:34:56-expected0]` | atomic | 搂TOML Data Model | covered | RFC3339 date/time parsing as TOML scalar behavior |
| `tests/test_utils.py::test_parse_rfc3339_time[12:34:56.123456-expected1]` | atomic | 搂TOML Data Model | covered | RFC3339 date/time parsing as TOML scalar behavior |
| `tests/test_write.py::test_write_backslash` | integration | 搂Dumping and Writing + 搂Style Preservation | covered | serialization of public TOML structures |
| `tests/test_write.py::test_escape_special_characters_in_key` | integration | 搂Dumping and Writing + 搂Style Preservation | covered | serialization of public TOML structures |
| `tests/test_write.py::test_write_inline_table_in_nested_arrays` | integration | 搂Dumping and Writing + 搂Style Preservation | covered | serialization of public TOML structures |
| `tests/test_write.py::test_serialize_aot_with_nested_tables` | integration | 搂Dumping and Writing + 搂Style Preservation | covered | serialization of public TOML structures |

Total: 288 | kept (covered): 266 | spec_gap: 0 | source-only: 19 | excluded: 3 | final scoreable: 266

Total: 266 | kept (covered): 266 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 266
