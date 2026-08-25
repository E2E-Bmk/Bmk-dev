# filter_notes — chevrotain-parser-toolkit-fullrepro-001

```
repo: Chevrotain/chevrotain
source_path: https://github.com/Chevrotain/chevrotain (wip/repo-cache/chevrotain-src, packages/chevrotain)
commit: 221fff76526021a3abba1068130f5e8a343fbaaf (npm chevrotain@13.2.0 gitHead)
language: typescript
src_loc: 10231 (packages/chevrotain/src/**/*.ts; 12228 incl. runtime workspace deps gast/regexp-to-ast/cst-dts-gen/utils)
test_functions: ~504 (it/test callbacks)
test_files: 45 (packages/chevrotain/test/**/*.ts)
dominant_test_styles: unit + full-flow integration (grammar -> lexer -> parser -> CST); behavioral assertions via chai
public_docs: https://chevrotain.io/docs/ (tutorial, guide: lexer/parser/cst/fault-tolerance/content-assist, API docs)
core_fact_source: a grammar definition — token types created by createToken (patterns, categories, longer_alt, groups, modes) plus parser rules declared with RULE/CONSUME/SUBRULE/OR/OPTION/MANY/AT_LEAST_ONE
derived_views: (1) token stream projection via Lexer.tokenize (tokens, groups, errors, positions);
  (2) CST projection via CstParser rule invocation (children keyed by token/rule name and labels);
  (3) parse-error projection (structured errors: MismatchedTokenException etc. with resync recovery);
  (4) grammar introspection projection (getGAstProductions / getSerializedGastProductions);
  (5) content-assist projection (computeContentAssist over the same grammar);
  (6) generated d.ts projection (generateCstDts from the GAst).
external_deps: none at runtime beyond its own @chevrotain/* workspace packages; tests need only vitest
test_import_audit: HIGH_RISK for Track A portability — upstream tests import "../../src/scan/tokens_public.js" and other monorepo-relative paths (not the published package root); 100% of suites affected -> Track A discarded, oracle generated (Track B)
docs_test_alignment: aligned — docs cover lexing, parsing DSL, CST shape, error recovery, grammar validation and content assist; the same projections the tests exercise
contamination_note: chevrotain@13.2.0, released 2026-08-01, relative to training cutoff: after (likely) — v13 is a fresh major line; widely memorized docs cover v10/v11 era
decision: keep
reason: rule-engine reimplementation (LL(k) lookahead computation, grammar validation, lexer mode automaton, error recovery) with >=6 public projections over one grammar fact source, 10k LOC, active test suite.
risks: (1) upstream tests non-portable -> generated_only oracle; mitigated by probing the pinned release for every asserted behavior;
  (2) error-message text is an implementation detail -> assert structured fields (token images, exception names, ruleStack) not full sentences;
  (3) grammar-recording runs at construction -> tests must construct parsers inside functions to observe validation errors as thrown TypeError/Errors.
scope_plan: target_subdomain=core lexing (createToken patterns/categories/longer_alt/groups/modes/positions/lexer errors), CstParser grammar DSL (CONSUME/SUBRULE/OR/OPTION/MANY/AT_LEAST_ONE/labels/args), CST structure, structured parse errors + resync recovery, grammar validation errors at construction, GAst introspection + serialization, content assist; expected_oracle_max=100
excluded: EmbeddedActionsParser beyond one contrast test, generateCstDts text output, syntax diagrams, performance/regexp-optimization internals, backtracking (BACKTRACK), GATE beyond one test, custom token patterns beyond payload basics, serializer round-trip via createSyntaxDiagramsCode
```

## Difficulty shapes (candidate-selector heuristic)

- **Reimplementation of a language/format rule**: the parser must compute LL(k)
  lookahead functions from the grammar recording, detect ambiguities, validate
  left recursion / duplicate alternatives — deriving rules, not calling them.
- **Multi-projection state**: one grammar definition projects to token streams,
  CSTs, structured error lists, serialized GAst, and content-assist suggestion
  sets; integration tests span >=3 projections.
- **Equivalence judgement**: grammar validation must judge whether alternatives
  are ambiguous (same-prefix lookahead) — a false alarm is as wrong as a miss.
- **Lazily resolved reference graph**: token categories form an inheritance
  graph resolved at lexer build time (tokenMatcher / categories chains).

## Layer plan

- atomic: single component behavior — token creation/categories, tokenize output
  fields, single-rule parse, one validation error, one introspection call.
- integration: >=2 components — lexer feeding parser, recovery producing partial
  CST plus errors, content assist over a multi-rule grammar, GAst reflecting the
  full DSL surface.
- system_e2e: full workflows — define grammar, lex, parse, recover, introspect,
  content-assist in one scenario.
