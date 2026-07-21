# Spec-Test Map

oracle_version: 2026-07-20-native-v1
spec_version: v1
filter/oracle_source: upstream_rewritten
scorer_isolation: task-local native tests with the selected package first on PYTHONPATH

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_atomic.py::test_lex_exception | upstream_rewritten | atomic | Reader Errors And Source Positions | covered | source: tests/test_reader.py::test_lex_exception |
| oracle/test_atomic.py::test_unbalanced_exception | upstream_rewritten | atomic | Reader Errors And Source Positions | covered | source: tests/test_reader.py::test_unbalanced_exception |
| oracle/test_atomic.py::test_lex_single_quote_err | upstream_rewritten | atomic | Reader Errors And Source Positions | covered | source: tests/test_reader.py::test_lex_single_quote_err |
| oracle/test_atomic.py::test_lex_expression_symbols | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_lex_expression_symbols |
| oracle/test_atomic.py::test_symbol_and_sugar | upstream_rewritten | atomic | Reader Sugar And Dotted Identifiers | covered | source: tests/test_reader.py::test_symbol_and_sugar |
| oracle/test_atomic.py::test_lex_expression_strings | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_lex_expression_strings |
| oracle/test_atomic.py::test_lex_expression_integer | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_lex_expression_integer |
| oracle/test_atomic.py::test_lex_symbols | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_lex_symbols |
| oracle/test_atomic.py::test_lex_strings | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_lex_strings |
| oracle/test_atomic.py::test_lex_strings_exception | upstream_rewritten | atomic | Reader Errors And Source Positions | covered | source: tests/test_reader.py::test_lex_strings_exception |
| oracle/test_atomic.py::test_lex_bracket_strings | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_lex_bracket_strings |
| oracle/test_atomic.py::test_lex_integers | upstream_rewritten | atomic | Reader Numeric Syntax | covered | source: tests/test_reader.py::test_lex_integers |
| oracle/test_atomic.py::test_lex_expression_float | upstream_rewritten | atomic | Reader Numeric Syntax | covered | source: tests/test_reader.py::test_lex_expression_float |
| oracle/test_atomic.py::test_lex_big_float | upstream_rewritten | atomic | Reader Numeric Syntax | covered | source: tests/test_reader.py::test_lex_big_float |
| oracle/test_atomic.py::test_lex_nan_and_inf | upstream_rewritten | atomic | Reader Numeric Syntax | covered | source: tests/test_reader.py::test_lex_nan_and_inf |
| oracle/test_atomic.py::test_lex_expression_complex | upstream_rewritten | atomic | Reader Numeric Syntax | covered | source: tests/test_reader.py::test_lex_expression_complex |
| oracle/test_atomic.py::test_lex_digit_separators | upstream_rewritten | atomic | Reader Numeric Syntax | covered | source: tests/test_reader.py::test_lex_digit_separators |
| oracle/test_atomic.py::test_leading_zero | upstream_rewritten | atomic | Reader Numeric Syntax | covered | source: tests/test_reader.py::test_leading_zero |
| oracle/test_atomic.py::test_dotted_identifiers | upstream_rewritten | atomic | Reader Sugar And Dotted Identifiers | covered | source: tests/test_reader.py::test_dotted_identifiers |
| oracle/test_atomic.py::test_lex_bad_attrs | upstream_rewritten | atomic | Reader Sugar And Dotted Identifiers | covered | source: tests/test_reader.py::test_lex_bad_attrs |
| oracle/test_atomic.py::test_lists | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_lists |
| oracle/test_atomic.py::test_dicts | upstream_rewritten | atomic | Reader Forms And Literal Conversion | covered | source: tests/test_reader.py::test_dicts |
| oracle/test_atomic.py::test_lex_column_counting | upstream_rewritten | atomic | Reader Errors And Source Positions | covered | source: tests/test_reader.py::test_lex_column_counting |
| oracle/test_atomic.py::test_lex_column_counting_with_literal_newline | upstream_rewritten | atomic | Reader Errors And Source Positions | covered | source: tests/test_reader.py::test_lex_column_counting_with_literal_newline |
| oracle/test_atomic.py::test_lex_line_counting_multi | upstream_rewritten | atomic | Reader Errors And Source Positions | covered | source: tests/test_reader.py::test_lex_line_counting_multi |
| oracle/test_models.py::test_symbol_or_keyword | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_symbol_or_keyword |
| oracle/test_models.py::test_wrap_int | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_wrap_int |
| oracle/test_models.py::test_wrap_tuple | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_wrap_tuple |
| oracle/test_models.py::test_wrap_nested_expr | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_wrap_nested_expr |
| oracle/test_models.py::test_replace_int | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_replace_int |
| oracle/test_models.py::test_invalid_bracket_strings | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_invalid_bracket_strings |
| oracle/test_models.py::test_replace_str | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_replace_str |
| oracle/test_models.py::test_replace_tuple | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_replace_tuple |
| oracle/test_models.py::test_list_add | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_list_add |
| oracle/test_models.py::test_list_slice | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_list_slice |
| oracle/test_models.py::test_hydict_methods | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_hydict_methods |
| oracle/test_models.py::test_set | upstream_rewritten | atomic | Model Construction And Collection Behavior | covered | source: tests/test_models.py::test_set |
| oracle/test_system.py::test_basics | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_basics |
| oracle/test_system.py::test_runpy | upstream_rewritten | system_e2e | Runtime Execution And Python Interoperation | covered | source: tests/importer/test_importer.py::test_runpy |
| oracle/test_system.py::test_stringer | upstream_rewritten | system_e2e | Runtime Execution And Python Interoperation | covered | source: tests/importer/test_importer.py::test_stringer |
| oracle/test_system.py::test_imports | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_imports |
| oracle/test_system.py::test_import_error_reporting | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_import_error_reporting |
| oracle/test_system.py::test_import_error_cleanup | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_import_error_cleanup |
| oracle/test_system.py::test_import_autocompiles | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_import_autocompiles |
| oracle/test_system.py::test_eval | upstream_rewritten | system_e2e | Runtime Execution And Python Interoperation | covered | source: tests/importer/test_importer.py::test_eval |
| oracle/test_system.py::test_reload | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_reload |
| oracle/test_system.py::test_reload_reexecute | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_reload_reexecute |
| oracle/test_system.py::test_circular | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_circular |
| oracle/test_system.py::test_shadowed_basename | upstream_rewritten | system_e2e | Import Hooks And Module Execution | covered | source: tests/importer/test_importer.py::test_shadowed_basename |
| oracle/test_integration.py::test_ast_bad_type | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_bad_type |
| oracle/test_integration.py::test_empty_expr | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_empty_expr |
| oracle/test_integration.py::test_dot_unpacking | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_dot_unpacking |
| oracle/test_integration.py::test_ast_bad_if | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_bad_if |
| oracle/test_integration.py::test_ast_valid_if | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_valid_if |
| oracle/test_integration.py::test_ast_bad_while | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_bad_while |
| oracle/test_integration.py::test_ast_good_do | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_good_do |
| oracle/test_integration.py::test_ast_good_raise | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_good_raise |
| oracle/test_integration.py::test_ast_raise_from | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_raise_from |
| oracle/test_integration.py::test_ast_bad_raise | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_bad_raise |
| oracle/test_integration.py::test_ast_good_try | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_good_try |
| oracle/test_integration.py::test_ast_bad_try | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_bad_try |
| oracle/test_integration.py::test_ast_good_except | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_good_except |
| oracle/test_integration.py::test_ast_bad_except | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_bad_except |
| oracle/test_integration.py::test_ast_good_assert | upstream_rewritten | integration | Compilation Forms And Errors | covered | source: tests/compilers/test_ast.py::test_ast_good_assert |

Total: 64 | kept: 64 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 64
