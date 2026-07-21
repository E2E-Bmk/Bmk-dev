# Native Test Mapping

| Native test | Layer | Spec basis | Status |
|---|---|---|---|
| `oracle/test_cli.py::test_help_is_available` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_version_is_available` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_invalid_cli_arguments_fail[args0]` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_invalid_cli_arguments_fail[args1]` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_formats_stdin[args0-SELECT 1]` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_formats_stdin[args1-select 1]` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_formats_stdin[args2-from foo]` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_formats_stdin[args3-select 1]` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_writes_outfile` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_in_place_updates_file` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_multiple_files_requires_in_place` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_in_place_rejects_stdin` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_missing_file_fails` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_cli.py::test_cli_preserves_utf8_file` | system_e2e | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[-0]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[   -0]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[select 1-1]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[select 1;-1]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[select 1; select 2;-2]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[select ';'; select 2-2]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[select 1 -- ;\n; select 2-2]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_statement_count[/* ; */ select 1; select 2-2]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[select 1]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[SELECT a, b FROM table_name WHERE a = 2]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[insert into t values (1, 'x')]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[update t set a = 3 where id = 1]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[delete from t where id in (1, 2)]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[select case when a > 1 then 'yes' else 'no' end from t]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[select count(*) from t group by a order by a desc]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parse_preserves_sql_text[with x as (select 1) select * from x]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_statements[select 1; select 2;-expected0]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_statements[select 1; select 2;-expected1]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_statements[select ';'; select 2-expected2]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_statements[select 1 -- ;\n; select 2-expected3]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_statements[-expected4]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_round_trip[select 1]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_round_trip[select 1;]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_round_trip[select ';']` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_round_trip[/* comment */ select 1]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_split_round_trip[select (1 + 2)]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_case_options[option0-SELECT * FROM foo]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_case_options[option1-select * from foo]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_case_options[option2-Select * From foo]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_case_options[option3-select * from FOO]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_case_options[option4-select * from foo]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_case_options[option5-select * from Foo]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_options_return_text[option0]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_options_return_text[option1]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_options_return_text[option2]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_options_return_text[option3]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_options_return_text[option4]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_format_options_return_text[option5]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_invalid_format_options_raise_public_error[invalid]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_invalid_format_options_raise_public_error[3]` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_parsestream_accepts_text_stream` | integration | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_tokenize_yields_token_type_and_value[select 1]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_tokenize_yields_token_type_and_value[select a from t]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_tokenize_yields_token_type_and_value[insert into t values (1)]` | atomic | Public behavior in `spec.md` | covered |
| `oracle/test_public_api.py::test_public_tokens_are_available` | atomic | Public behavior in `spec.md` | covered |

Total: 59 | kept: 59 | excluded: 8 | final_scoreable: 59
