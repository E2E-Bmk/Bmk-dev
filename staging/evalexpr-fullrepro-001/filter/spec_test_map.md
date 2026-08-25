# Specification coverage map — evalexpr-fullrepro-001

Test IDs are `{crate}::{module path}::{function}` as reported by cargo-nextest
against the oracle workspace (`atomic` and `integration` member crates).

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::test_unary_examples` | atomic | ## Operators and Type Rules | covered | unary `-` and `!` on literals and precedence vs `^` |
| `atomic::test_binary_examples` | atomic | ## Operators and Type Rules | covered | all binary operators on int/float/bool/string operand pairs |
| `atomic::test_arithmetic_precedence_examples` | atomic | ## Operators and Type Rules | covered | precedence ordering of `+ - * / % ^` and unary minus |
| `atomic::test_braced_examples` | atomic | ## Expression Syntax and Literals | covered | parenthesized grouping overrides precedence |
| `atomic::test_mod_examples` | atomic | ## Operators and Type Rules | covered | `%` on int and mixed operands |
| `atomic::test_pow_examples` | atomic | ## Operators and Type Rules | covered | `^` always evaluates as float, right associativity |
| `atomic::test_boolean_examples` | atomic | ## Operators and Type Rules | covered | `&& \|\| == != < <= > >=` truth tables and comparisons |
| `atomic::test_builtin_functions` | atomic | ## Functions: Builtin and User-Defined | covered | builtin function library results (math, string, tuple, bitwise) |
| `atomic::test_errors` | atomic | ## Error Semantics | covered | `Expected…` type errors carrying the actual value |
| `atomic::test_no_panic` | atomic | ## Error Semantics | covered | malformed inputs return errors, never panic |
| `atomic::test_whitespace` | atomic | ## Expression Syntax and Literals | covered | whitespace-insensitive tokenization |
| `atomic::test_string_escaping` | atomic | ## Expression Syntax and Literals | covered | `\\` and `\"` escape sequences in string literals |
| `atomic::test_tuple_definitions` | atomic | ## Expression Syntax and Literals | covered | `,` aggregation building flat and nested tuples |
| `atomic::test_implicit_context` | atomic | ## Contexts and Bindings | covered | `eval` uses a fresh temporary context per call |
| `atomic::test_type_errors_in_binary_operators` | atomic | ## Error Semantics | covered | `WrongTypeCombination` carries the actual operand types |
| `atomic::test_error_constructors` | atomic | ## Error Semantics | covered | `Expected…` variants and `UnmatchedPartialToken` from entry points |
| `atomic::test_same_operator_chains` | atomic | ## Operators and Type Rules | covered | left associativity of `/` and `-` chains |
| `atomic::test_value_type` | atomic | ## Values, Types, and Conversions | covered | `ValueType` from `&Value`; `as_float`/`as_tuple`/`as_fixed_len_tuple`/`as_empty` |
| `atomic::test_parenthese_combinations` | atomic | ## Error Semantics | covered | `MissingOperatorOutsideOfBrace` on value-adjacent braces |
| `atomic::test_try_from` | atomic | ## Values, Types, and Conversions | covered | `TryFrom<Value>` for String/bool/tuple/unit with `Expected…` errors |
| `atomic::test_negative_power` | atomic | ## Operators and Type Rules | covered | unary minus binds looser than `^`, `3^-2` shapes |
| `atomic::test_hex` | atomic | ## Expression Syntax and Literals | covered | `0x` literals and `VariableIdentifierNotFound` for bare `0x` |
| `atomic::test_binary` | atomic | ## Expression Syntax and Literals | covered | `0b` literals and error for illegal digits |
| `atomic::test_octal` | atomic | ## Expression Syntax and Literals | covered | `0o` literals and error for illegal digits |
| `atomic::test_broken_string` | atomic | ## Error Semantics | covered | `UnmatchedDoubleQuote` on unterminated strings |
| `atomic::test_comments` | atomic | ## Expression Syntax and Literals | covered | `//` line and `/* */` inline comments; unmatched comment error |
| `atomic::test_compare_different_numeric_types` | atomic | ## Operators and Type Rules | covered | cross-type int/float comparisons |
| `atomic::test_escape_sequences` | atomic | ## Error Semantics | covered | `IllegalEscapeSequence` carrying the sequence |
| `atomic::test_unmatched_partial_tokens` | atomic | ## Error Semantics | covered | single `\|` produces `UnmatchedPartialToken` |
| `integration::contexts::test_builtin_functions_context` | integration | ## Functions: Builtin and User-Defined | covered | builtins available through `HashMapContext` evaluation |
| `integration::contexts::test_clear` | integration | ## Contexts and Bindings | covered | `clear` / `clear_variables` / `clear_functions` erasure semantics |
| `integration::contexts::test_empty_context` | integration | ## Contexts and Bindings | covered | `EmptyContext` has no variables, no functions, no builtins |
| `integration::contexts::test_empty_context_builtin_functions` | integration | ## Contexts and Bindings | covered | builtin-disabled flags of the two empty context types |
| `integration::contexts::test_empty_context_with_builtin_functions` | integration | ## Contexts and Bindings | covered | `EmptyContextWithBuiltinFunctions` dispatches builtins only |
| `integration::contexts::test_hashmap_context_clone` | integration | ## Contexts and Bindings | covered | cloned `HashMapContext` reproduces variables and functions |
| `integration::contexts::test_hashmap_context_type_safety` | integration | ## Contexts and Bindings | covered | assignment type-safety: same-type reassignment only |
| `integration::contexts::test_iter_empty_contexts` | integration | ## Contexts and Bindings | covered | variable iteration of empty context types is empty |
| `integration::contexts::test_with_context` | integration | ## Contexts and Bindings | covered | variables and functions bound via `context_map!` resolve in eval |
| `integration::functions::test_capturing_functions` | integration | ## Functions: Builtin and User-Defined | covered | closures capturing environment values as context functions |
| `integration::functions::test_functions` | integration | ## Functions: Builtin and User-Defined | covered | single-argument user functions over int/float arguments |
| `integration::functions::test_n_ary_functions` | integration | ## Functions: Builtin and User-Defined | covered | tuple-argument dispatch and `WrongFunctionArgumentAmount` |
| `integration::generated::generated_cross_view_agreement_on_one_expression` | integration | ## Cross-View Invariants | covered | eval / eval_int / tree eval / tree eval_int / context eval agree |
| `integration::generated::generated_math_consts_context_default_bindings` | integration | ## Contexts and Bindings | covered | `math_consts_context!()` binds `core::f64::consts` names |
| `integration::generated::generated_math_consts_context_selected_names_only` | integration | ## Contexts and Bindings | covered | `math_consts_context!(names…)` binds exactly the listed names |
| `integration::generated::generated_precompiled_tree_recomputes_under_mutated_context` | integration | ## Cross-View Invariants | covered | precompiled tree tracks context mutation and assignment write-back |
| `integration::generated::generated_typed_shortcut_error_agrees_with_tree_shortcut` | integration | ## Cross-View Invariants | covered | `ExpectedInt` agreement between free and tree typed shortcuts |
| `integration::scripts::test_assignment` | integration | ## Assignment, Chaining, and Scripts | covered | `=` returns empty, writes the context, honors type safety |
| `integration::scripts::test_expression_chaining` | integration | ## Assignment, Chaining, and Scripts | covered | `;` chains evaluate to the last expression's value |
| `integration::scripts::test_operator_assignments` | integration | ## Assignment, Chaining, and Scripts | covered | `+=` `-=` `*=` `/=` `%=` `^=` `&&=` `\|\|=` semantics |
| `integration::scripts::test_strings` | integration | ## Assignment, Chaining, and Scripts | covered | string assignment, concatenation, comparison in scripts |
| `integration::scripts::test_variable_assignment_and_iteration` | integration | ## Contexts and Bindings | covered | `iter_variables` / `iter_variable_names` read-back after scripts |
| `integration::shortcuts::test_shortcut_functions` | integration | ## Cross-View Invariants | covered | every typed shortcut × context form agrees on value and error |
| `integration::trees::assignment_lhs_is_identifier` | integration | ## Precompiled Expressions and Tree Introspection | covered | write-identifier iteration and assignment effect of a parsed tree |
| `integration::trees::test_iterators` | integration | ## Precompiled Expressions and Tree Introspection | covered | five identifier iterators in source order |
| `integration::trees::test_long_expression_i89` | integration | ## Precompiled Expressions and Tree Introspection | covered | large mixed expression evaluated through a precompiled tree |
| `integration::trees::test_node_mutable_access` | integration | ## Precompiled Expressions and Tree Introspection | covered | `children_mut` / `operator_mut` root node access |

## Layer balance

- atomic: 29 (single entry point, literal/operator/value/error behavior)
- integration: 27 (contexts, user functions, scripts, trees, shortcuts, cross-view)
- system_e2e: 0 (library-only task; no CLI surface in scope)

## Dummy-gate audit

Every test calls at least one `evalexpr` public entry point and asserts a
produced value, a context state transition, or a specific `EvalexprError`
variant. No `#[should_panic]` tests are present, so a stub crate whose public
items panic cannot pass any test.
