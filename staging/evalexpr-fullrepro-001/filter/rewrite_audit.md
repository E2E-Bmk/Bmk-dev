# Rewrite audit — evalexpr-fullrepro-001

Source: `tests/integration.rs` at 92d99f4 (v13.1.0), split into the oracle's
`atomic` crate (single-entry-point behavior) and `integration` crate modules
(`contexts`, `functions`, `scripts`, `shortcuts`, `trees`). Excluded upstream
suites: `rand.rs`, `regex.rs`, `serde.rs` (optional features, out of spec
scope) and the inline `#[cfg(test)]` units in `src/` (private surface).

## Removals (undeclared surface — spec is never widened for a test)

| test | removal | reason |
|------|---------|--------|
| `test_error_constructors` | `expect_function_argument_amount` asserts | free helper not declared by the spec |
| `test_error_constructors` | exact `PartialToken::Ampersand` equality → `matches!(… UnmatchedPartialToken { .. })` | spec declares the variant, not `PartialToken`'s own variant names |
| `test_unmatched_partial_tokens` | exact `PartialToken::VerticalBar` equality → `matches!` | same |
| `test_type_errors_in_binary_operators` | `wrong_type_combination(Operator::Add, …)` equality → `matches!` guard on `actual` types | `Operator::Add` variant not declared; the carried `ValueType` list is |
| `test_value_type` | `ValueType::from(&mut Value…)` block | spec declares `From<&Value>` only |
| `test_value_type` | `is_number` / `is_empty` predicate blocks | predicates not declared |
| `test_value_type` | `Result::from(Value…)` assert | conversion not declared |
| `test_negative_power` | `println!("{:?}", tree)` | spec scopes out `Debug` output; a delivery without `derive(Debug)` on `Node` must not fail to compile |
| `test_hashmap_context_clone_debug` → `test_hashmap_context_clone` | `format!("{:?}")` clone-equality assert | `Debug` scoped out; behavioral clone asserts kept |
| `trees::assignment_lhs_is_identifier` | operator-shape `matches!` on `Assign` / `VariableIdentifierWrite` / `Const` → write/read identifier iteration + context effect | non-`RootNode` operator variants not declared; replacement asserts the same behavior through declared iterators |
| `trees::test_node_mutable_access` | `assert_eq!(*operator_mut(), Operator::RootNode)` → `matches!` | avoids requiring `PartialEq` on `Operator`, which the spec does not declare |
| `contexts::test_clear` | `format!("{input}")` closures → `as_int()? + 1` closures | `Display` for `Value` scoped out; expected values adjusted (`"5"` → `6`) |

## Deduplication (split artifacts)

`test_clear`, `test_iter_empty_contexts`, `test_empty_context_builtin_functions`
were emitted into both crates by the splitter; the atomic copies were removed
(context mutation is integration behavior). A duplicated tail block in
`atomic/src/lib.rs` (`test_comments`, `test_compare_different_numeric_types`,
`test_escape_sequences` twice) was collapsed to one copy each.

## Generated additions (coverage gaps)

- `generated_math_consts_context_default_bindings`, 
  `generated_math_consts_context_selected_names_only` — `math_consts_context!`
  was declared by the spec but untested upstream.
- `generated_cross_view_agreement_on_one_expression`,
  `generated_precompiled_tree_recomputes_under_mutated_context`,
  `generated_typed_shortcut_error_agrees_with_tree_shortcut` — direct tests of
  the spec's Cross-View Invariants section with values distinct from upstream
  (`7 * 6 - 13`, `a * 3 + b` with 4/9/11, `4.25`).

## Fairness audit

Identifier sweep of all oracle sources against the spec vocabulary: after the
removals above, every flagged identifier is a test function name, a local
binding, or a std item; every reached crate root (`evalexpr`) is named in the
spec's Import Surface. `filter/lint_result.txt` holds the machine check.
