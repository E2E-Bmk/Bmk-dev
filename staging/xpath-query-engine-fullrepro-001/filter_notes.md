# Stage 1 evidence brief — xpath-query-engine-fullrepro-001

```
repo: antchfx/xpath
source_path: https://github.com/antchfx/xpath
commit: d666d4b6f3b570811b144144414971401472b83c (tag v1.3.8)
language: go
src_loc: 4729 (build.go, cache.go, func.go, func_go110.go, func_pre_go110.go,
         operator.go, parse.go, query.go, xpath.go; excludes tests)
test_functions: 83 across 9 test files (heavy table-driven bodies inside)
test_files: xpath_test.go, xpath_axes_test.go, xpath_expression_test.go,
            xpath_function_test.go, xpath_predicate_test.go,
            numeric_context_test.go, operator_test.go, cache_test.go,
            doc_test.go, assert_test.go (helpers)
dominant_test_styles: in-package white-box tables driven by a hand-built TNode
    tree + TNodeNavigator implementing NodeNavigator; helper asserts on
    element positions, values, tags, counts, Evaluate results; only
    doc_test.go uses the external test package
public_docs: pkg.go.dev/github.com/antchfx/xpath (doc comments on every
    exported symbol), README with supported-syntax tables (axes, node tests,
    operators, function catalog per version)
core_fact_source: a compiled XPath 1.0 expression (lexer -> AST -> query
    plan) evaluated against a caller-supplied document tree behind the
    NodeNavigator cursor interface
derived_views: (1) Expr.Select -> NodeIterator streaming matched nodes in
    document order; (2) Expr.Evaluate -> typed result (bool/float64/string/
    *NodeIterator) under XPath 1.0 coercion rules; (3) compile-time error
    surface (Compile/CompileWithNS/MustCompile); (4) Expr.String round-trip
    of the source expression; (5) the engine's function library (position,
    count, string ops, math incl. v1.3.8 round/mod fixes) observable through
    both Select predicates and Evaluate; (6) namespace binding via
    CompileWithNS
external_deps: none — go.mod has no requires (go 1.14); oracle supplies its
    own NodeNavigator tree implementation, which doubles as the isolation
    boundary
test_import_audit: HIGH_RISK — 9 of 10 test files declare `package xpath`
    and reach unexported symbols (testQuery hooks the unexported iterator
    interface, assert helpers, createNode/TNode fixtures); retention not
    viable, expect Track B
docs_test_alignment: aligned — pkg.go.dev + README document the same
    compile/select/evaluate projections the tests exercise
contamination_note: antchfx/xpath@v1.3.8, released 2026-07-20, after known
    training cutoffs; XPath 1.0 itself is a closed W3C standard so generic
    semantics are memorized, but v1.3.8 carries recent behaviour fixes
    (name*expr lexing per §3.7, undeclared-variable errors, round()/mod
    numeric fixes) that generic recall gets wrong
decision: keep
reason: a language-rule reimplementation engine (XPath 1.0 grammar, axes,
    coercions, function library) evaluated through a caller-supplied cursor
    interface, with Select/Evaluate/error projections over one compiled
    expression enabling >= 3-projection integration tests
risks: closed-standard saturation — mitigated as with mvdan/sh by binding
    the oracle to v1.3.8-specific observables (exact error texts, document-
    order iteration, coercion edge cases, numeric-context behaviour, the
    fixed lexing/round/mod quirks) rather than generic XPath knowledge;
    NewLoadingCache returns an unexported type, so cache behaviour is
    specified only through its public effects
scope_plan: N/A (4729 LOC < 15000, 83 test funcs < 300); soft oracle target
    ~150 tests in line with prior packets
```

## Difficulty shapes (selection rationale, candidate-selector heuristic)

- **Reimplementation of a language rule**: full XPath 1.0 lexer/parser and
  evaluation semantics (axes, node tests, predicates with positional
  filtering, operator precedence, string/number/boolean coercions, the core
  function library) — not a call into an existing engine.
- **Equivalence judgement**: Evaluate and Select must agree on the same
  compiled expression (count(E) equals the number of nodes Select(E)
  yields; boolean(E) matches non-emptiness; string(E) is the first node's
  value), and document order must hold regardless of axis direction.
- **Integration spanning >= 3 projections**: one expression flows through
  compile -> Select iteration -> Evaluate coercion -> error surface, all
  against the same caller-built tree.
- (No lazily-resolved reference graph; three of four shapes present.)

## Stage 2 spec sources (source_boundary detail)

Spec v1 was written from: `go doc -all github.com/antchfx/xpath` (doc
comments on all exported symbols), the upstream README syntax/function
tables, and 58 probe rounds against pinned v1.3.8 executed from a
scratch module with a purpose-built in-memory NodeNavigator
(`wip/probe/xpath/`): compile-error catalog (R1, R53), MustCompile no-op
contract (R2, R13), axes and document order (R3, R21, R26, R30-R33, R50),
Evaluate typing and coercions (R4, R12, R17, R23, R36-R38, R57),
predicates and positions (R5, R16, R22, R27, R31, R42, R51), the function
library (R7-R9, R19, R39, R43, R52, R55-R56), namespace matching (R14,
R18, R20, R55), iterator semantics (R15, R48), operator precedence
(R44-R45), and unions (R6, R58). Upstream source consulted for rule
confirmation only (name-test predicate in build.go, sum/namespace-uri in
func.go, Select/Evaluate/MustCompile in xpath.go).

Deliberately excluded from spec scope (upstream panics or unstatable
interactions, observed in probes): mixed boolean comparisons
(`true() > 0`, `'true' = true()` — nil-dereference panics), `substring`
with NaN or +Inf bounds (slice-bounds panics), `position()`/`last()`
comparisons on reverse axes (inconsistent with bare numeric predicates),
`processing-instruction()` (compiles, no public node type), zero-arg
`boolean()`/`position(1)`/`last(1)`/`string-length('a','b')`/
`count(a, b)`/`..[1]`/`book]`/`a b` (compile-accepted oddities with
unprobed evaluation), and `NewLoadingCache`/`RegexpCache` (auxiliary
cache exports returning/holding unexported types).

## source_boundary (recorded here; spec.md ships without internal header)

- Candidate implements module path `github.com/antchfx/xpath` (single
  package).
- Oracle imports `github.com/antchfx/xpath` exclusively and provides its own
  in-memory NodeNavigator implementation; behaviours verified against
  upstream v1.3.8 (commit d666d4b6f3b570811b144144414971401472b83c).
- The htmlquery/xmlquery/jsonquery sibling repos are out of scope and must
  not be referenced by spec or oracle.
