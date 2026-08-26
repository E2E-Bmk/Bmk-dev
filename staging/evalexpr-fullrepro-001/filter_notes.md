# filter_notes — evalexpr-fullrepro-001

```
repo: ISibboI/evalexpr
source_path: https://github.com/ISibboI/evalexpr (local: /tmp/refs/evalexpr)
commit: 92d99f4a3d67d97ac94c365602214a20fad1d650 (tag v13.1.0)
language: rust
target_crates: evalexpr
src_loc: 3811 net (5912 raw) across src/, excluding tests/, benches/
test_functions: 56 external (tests/integration.rs 51, rand.rs 2, regex.rs 1,
  serde.rs 2) + 9 inline #[cfg(test)] units in src/
test_files: tests/integration.rs (2612 lines), tests/rand.rs, tests/regex.rs,
  tests/serde.rs
dominant_test_styles: dense value-equality unit/integration asserts on the
  public API (eval*, contexts, Node); zero snapshot tests; no golden files
public_docs: README.md (operator precedence table, builtin function table,
  context semantics, value syntax table, variable/function call grammar,
  comment syntax, assignment/type-safety rules) == docs.rs crate root docs
  (cargo-sync-readme), plus docs.rs item-level API docs (#![deny(missing_docs)])
core_fact_source: the operator tree (Node) produced from an expression string,
  plus the variable/function bindings held by a Context implementation
derived_views: (1) untyped evaluation results (eval / eval_with_context[_mut]);
  (2) typed shortcut results (eval_int/_float/_number/_string/_boolean/_tuple/
  _empty and their _with_context[_mut] forms); (3) context state read back via
  Context::get_value / iterate_variables after assignment expressions;
  (4) tree introspection via Node::iter_identifiers / iter_read/write_variable
  identifiers and children; (5) the EvalexprError taxonomy raised across all
  entry points
external_deps: none for the core feature set (regex/serde/rand are optional
  features, excluded from scope); oracle needs no third-party test deps
test_import_audit: clean — tests import only `use evalexpr::{error::*, *}`;
  no private-module imports (0% of files affected)
docs_test_alignment: aligned — README documents exactly the projections the
  test suite exercises (operators, builtins, contexts, typed shortcuts,
  error taxonomy)
contamination_note: evalexpr@13.1.0, released 2025-11-26, relative to training
  cutoff: near/after for most 2025-era models; the crate has existed since
  2019 so older-version semantics (pre-generic API, v11 and earlier) are
  likely memorized — v13's generic EvalexprNumericTypes API diverges from them
decision: keep
reason: rule-engine shape (reimplementation of a language rule: tokenizer,
  precedence-climbing tree construction, operator/type semantics) with >=5
  public projections of one fact source and a fully doc-traceable surface.
risks: expression evaluators are a common pattern; mitigated because the
  error taxonomy (~40 library-specific variants), Int/Float typing rules, and
  the v13 generic API are library-specific and non-derivable; CLI binary is
  out of scope (spec covers the library only)
scope_plan: N/A (src_loc < 15000, test_functions < 300)
```

## Difficulty shapes (candidate-selector heuristic)

- **Reimplementation of a language rule**: tokenizer + operator-precedence
  tree building (precedence 0–200 table, unary vs binary '-', function
  application by juxtaposition), not a call into an existing engine.
- **Rule engine resisting pattern-matching**: type rules (int-preserving
  arithmetic except `/` and `%` mixed cases, `^` always float), assignment
  type-safety in `HashMapContext`, builtin-function dispatch that can be
  disabled per context.
- **Multi-projection integration**: one expression string must agree across
  direct eval, typed shortcuts, precompiled `Node` re-evaluation under a
  mutated context, and context state read-back — 4+ public projections.
- **Equivalence judgement**: `Value` equality semantics across numeric types
  (`3 > 2.5` style cross-type comparisons) and tuple nesting.

## Dummy-gate audit note (Rust)

A stub crate whose public items all `unimplemented!()` panics on the first
call into the crate; every kept test calls at least one `evalexpr` entry point
and asserts a produced value or a specific `EvalexprError` variant, and no
`#[should_panic]` test is kept, so no kept test can pass against a stub.
Verified statically over the merged oracle (see spec_test_map.md).
