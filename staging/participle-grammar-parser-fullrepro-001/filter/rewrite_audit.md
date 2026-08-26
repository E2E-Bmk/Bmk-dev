# S3A import/rewrite audit — participle-grammar-parser-fullrepro-001

## Upstream test tree at v2.1.4

- 142 `Test*` functions across root (`package participle_test`), `lexer`,
  `lexer/internal/conformance`, and `ebnf` packages.
- Every root and lexer test file imports `github.com/alecthomas/assert/v2`
  (third-party assertion module) — 247 `assert.`/`repr.` call sites.
- Many assertions are golden strings produced by `github.com/alecthomas/repr`
  over parsed ASTs — snapshot checks of struct dumps, brittle against any
  formatting drift and unusable without the repr module.
- `lexer/internal/conformance` is an internal codegen conformance harness
  (references internal packages); `ebnf/` tests target the out-of-scope ebnf
  subpackage.

## Decision

- Track A retention share: 0% — an oracle restricted to target + stdlib
  imports cannot lift any upstream test without rewriting every assertion,
  and repr-golden assertions do not survive rewriting as behavioral checks.
- **Track B triggered**: generate a fresh oracle from the spec, asserting
  observable behavior (parse results, field values, EBNF text, token
  streams, error messages by fragment) with stdlib-only test code.

functions_in_scope: 142
functions_kept (Track A): 0
functions_excluded: 142 (100% discard -> early Track B trigger)
