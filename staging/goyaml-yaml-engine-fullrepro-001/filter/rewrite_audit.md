# Track A rewrite audit — goyaml-yaml-engine-fullrepro-001

Scope: upstream test files at pinned v1.19.2
(92bc79cb5f685e999ad131473168fc45215d12d9), excluding `benchmarks/`:
13 files, 140 `Test*` functions.

## File-level audit

| file | funcs | package decl | decision | reason |
|---|---|---|---|---|
| decode_test.go | 53 | `yaml_test` | DISCARD | imports `github.com/goccy/go-yaml/internal/errors` (private carrier) at module level; the dominant function `TestDecoder` is a ~1,290-line anonymous mega-table (several hundred cases) — at base-function scoring granularity one defect flips the whole decode surface; several funcs bind to fixture dirs (`TestDecoder_AnchorReferenceDirs`, `_AnchorFiles`, `_DecodeFromFile`) |
| encode_test.go | 29 | `yaml_test` | DISCARD | `TestEncoder` is a ~940-line anonymous mega-table with the same granularity failure; remainder heavily golden-string against exact multi-line output including stylistic bytes the spec does not fix |
| testdata/yaml_test.go | 16 | `yaml_test` | DISCARD | lives inside `testdata/` module boundary; asserts `ast.ErrInvalidTokenType`-family internals and unexported helper types; several funcs golden-print full error strings |
| testdata/validate_test.go | 1 | `yaml_test` | DISCARD | binds to `go-playground/validator` (third-party validator implementation detail, not the `StructValidator` contract) |
| yaml_test_suite_test.go | 1 | `yaml_test` | DISCARD | data-driven runner over `testdata/yaml-test-suite` goldens (git submodule); single base function, external fixture tree |
| yaml_test.go | 7 | `yaml_test` | DISCARD | `TestSmartAnchor` exercises an anchor-generation mode the spec declares out of scope (Non-Goals); the rest are recoverable behaviors but 7 < 30 makes Track A non-viable alone; regenerated with tighter granularity |
| path_test.go | 9 | `yaml_test` | DISCARD | mega-tables again (`TestPath` 160 lines of cases in one func); `TestPath_ReservedKeyword` exercises quoted/escaped path lexemes beyond spec scope |
| parser/parser_test.go | 12 | `parser_test` | DISCARD | dominant funcs assert exact golden renderings of every AST level plus token-level `Origin` tables for the whole document set in single functions; granularity failure |
| lexer/lexer_test.go | 5 | `lexer_test` | DISCARD | `TestTokenize` is a ~2,600-line golden token-table mega-runner; per-function scoring cannot attribute failures |
| token/token_test.go | 2 | `token_test` | DISCARD | asserts internal predicate tables (`IsNeedQuoted`) not part of the spec surface |
| ast/ast_test.go | 2 | `ast` | DISCARD | in-package white-box (`package ast`), references unexported escape helper |
| printer/printer_test.go | 3 | `printer_test` | DISCARD | printer package is out of spec scope (Non-Goals: no token/tree-printing package) |
| fuzz_test.go | 0 | `yaml_test` | DISCARD | fuzz harness, no deterministic assertions |

functions_in_scope: 140
functions_kept (Track A): 0
functions_excluded: 140 (100%)

## Track B trigger

Early trigger fires: all upstream files discarded at Step 1 (100% > 50%
threshold). The carrier problems are structural: the highest-value files are
anonymous mega-tables whose base-function granularity cannot support per-test
scoring, the largest file imports a private package at module level, and the
remaining files are golden-table runners, fixture-tree binders, or in-package
white-box tests.

Track B generation targets are enumerated from the spec: 8 behavior sections
(Decoding into Go Values; Anchors, Aliases, and Merge Keys; Encoding from Go
Values; Comment Association; Path Queries; Syntax Tree and Tokens; Format
Conversion; Custom Hooks), the Error Semantics table, 8 Cross-View
Invariants, and 2 Representative Workflows. Assertions are constructed from
observed reference behaviour at v1.19.2 (probe rounds R1–R69 recorded in
PIPELINE_STATE history during spec drafting, plus per-test observation runs
during generation), not from upstream test expectations.
