# Stage 1 evidence brief — mvdansh-shell-syntax-fullrepro-001

```
repo: mvdan/sh (module mvdan.cc/sh/v3)
source_path: https://github.com/mvdan/sh
commit: 2f3f5e36d9b0f8f14c998d50aa20a28832205ae8 (tag v3.13.1)
language: go
src_loc: 9123 in scope (syntax package 8806 non-test + syntax/typedjson 317);
         whole module 16185 — scope_plan applies
test_functions: 52 in scope (51 in syntax/*_test.go + 1 in typedjson) plus the
                fileTests mega-table shared by parser and printer runners
                (~900 table cases); 105 module-wide
test_files: syntax: filetests_test.go, parser_test.go, printer_test.go,
            quote_test.go, simplify_test.go, walk_test.go, fuzz_test.go,
            bench_test.go, example_test.go, parser_{linux,other}_test.go;
            typedjson/json_test.go
dominant_test_styles: in-package white-box mega-tables (fileTests: source string
    -> hand-built AST literal -> exact printed output), exact-output printer
    tables, error-message tables; only example_test.go and typedjson use
    external test packages
public_docs: pkg.go.dev/mvdan.cc/sh/v3/syntax (extensive doc comments on every
    node type, parser/printer option, and function), pkg.go.dev/mvdan.cc/sh/v3/
    syntax/typedjson, repo README
core_fact_source: the shell AST (File/Stmt/Command/Word node graph with exact
    Pos/End offsets, line and column for every node) produced from source text
    under a selected language variant (Bash/POSIX/MirBSDKorn/Bats)
derived_views: (1) Parser: text -> AST with exact positions, keyword/token
    classification, heredoc bodies, error recovery (RecoverErrors, IsIncomplete);
    (2) Printer: AST -> canonical formatted text (shfmt style) under 8+ options
    (Indent, BinaryNextLine, SwitchCaseIndent, SpaceRedirects, KeepPadding,
    FunctionNextLine, Minify, SingleLine); (3) typedjson: AST -> typed JSON and
    back (Encode/Decode round trip); (4) Walk traversal over every node;
    (5) Quote: string -> shell literal per variant; (6) Simplify: AST rewrite;
    (7) parser sub-modes: Stmts/Words/Document/Arithmetic incremental APIs
external_deps: none at runtime — syntax imports only stdlib + in-module
    fileutil; go.mod requires (qt, go-cmp, pty, renameio) are test/CLI-only and
    out of scope
test_import_audit: HIGH_RISK — 10 of 12 syntax test files declare `package
    syntax` (white-box; build AST literals via unexported helpers, touch
    unexported parser fields); retention of upstream tests is not viable,
    expect Track B
docs_test_alignment: aligned — pkg.go.dev documents the same parse/print/walk/
    quote/json projections the tests exercise
contamination_note: mvdan/sh@v3.13.1, released 2026-04-06, after known
    training cutoffs; the library itself (shfmt) is long-standing and
    well-known, so API shape is likely memorized while v3.13-specific
    behaviours are not
decision: keep
reason: a language-rule reimplementation engine (full shell grammar with exact
    position bookkeeping) whose one fact source projects into 7 public views,
    with round-trip invariants (parse->print->reparse, encode->decode) that
    make integration tests span >= 3 projections
risks: shell syntax is POSIX-standardized and shfmt is famous — mitigate by
    binding the oracle to observable v3.13.1 behaviours (exact positions,
    canonical output, error text, JSON shape) rather than generic shell
    knowledge; large node-type surface makes the dummy stub laborious
scope_plan: target_subdomain=syntax package + syntax/typedjson (parser,
    printer, walk, quote, typed JSON; excludes interp/expand/shell/pattern/
    fileutil and the simplify minifier-adjacent extras beyond Simplify itself),
    expected_oracle_max=170
```

## Difficulty shapes (selection rationale, candidate-selector heuristic)

- **Reimplementation of a language rule**: the parser must implement the shell
  grammar (quoting, heredocs, arithmetic, parameter expansion, extended globs,
  case/if/for constructs) per dialect, not call into an existing shell.
- **Equivalence judgement**: printer output is canonical — parse(print(ast))
  must equal ast semantically, and printing an already-canonical file must be
  a fixpoint; typedjson Encode/Decode must round-trip including positions.
- **Integration spanning >= 3 projections**: one source string flows through
  parse -> walk -> print -> reparse -> typedjson, all agreeing on structure
  and positions.
- (No lazily-resolved reference graph; three of four shapes present.)

## source_boundary (recorded here; spec.md ships without internal header)

- Candidate implements module path `mvdan.cc/sh/v3` packages `syntax` and
  `syntax/typedjson` only.
- Oracle imports `mvdan.cc/sh/v3/syntax` and `mvdan.cc/sh/v3/syntax/typedjson`
  exclusively; behaviours verified against upstream v3.13.1
  (commit 2f3f5e36d9b0f8f14c998d50aa20a28832205ae8).
- interp/expand/shell/pattern/fileutil/cmd are out of scope and must not be
  referenced by spec or oracle.
