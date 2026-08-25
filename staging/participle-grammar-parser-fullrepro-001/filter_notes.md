# Stage 1 evidence brief — participle-grammar-parser-fullrepro-001

## Identity

| field | value |
|-------|-------|
| repo | alecthomas/participle |
| module | `github.com/alecthomas/participle/v2` (+ `/lexer` subpackage) |
| pinned version | v2.1.4 |
| pinned commit | bcbb39153e17f8018257f17aba8eac628d396b64 (2025-03-24) |
| language | go |
| task_id | participle-grammar-parser-fullrepro-001 |

## Hard gates

| gate | result | evidence |
|------|--------|----------|
| LOC >= 3000 | PASS | 3403 non-blank/non-comment LOC at v2.1.4 across root + `lexer/` + `ebnf/`, excluding tests, `cmd/`, `_examples/` |
| not single-file implementable | PASS | grammar compiler (struct-tag parse), node evaluator, capture/reflection layer, lexer runtime (simple + stateful), EBNF projection are separable engines |
| shared fact source, >= 2 projections | PASS | one compiled grammar drives: (1) `Parse*` struct population, (2) `String()` EBNF rendering, (3) build-time grammar errors, (4) parse-time errors with `lexer.Position`, (5) `Tokens` capture / `Pos`/`EndPos` recording |
| test suite usable | PASS | 146 upstream `Test*` funcs, all in external test packages (`package participle_test`), no network, table-driven behavioral checks |
| not closed standard / high saturation | PASS | the struct-tag grammar language is participle-specific (not PEG/EBNF standard input); no other implementation shares its capture semantics |
| evaluator needs no private details | PASS | all assertions expressible through exported API (`Build`, `Parse*`, `String`, `participle.Error`, `lexer.*`) |
| docs-test projection match | PASS | README + TUTORIAL.md + godoc document the tag language, capture rules, options, lexers; tests exercise the same public surface |

## Soft gates / difficulty shapes

- **Reimplementation of a language rule:** the delivery must implement the struct-tag
  grammar mini-language itself — `@` capture, `|` alternation, `( )` grouping,
  `?` `*` `+` `!` `~` modifiers, token references, string literals, case-insensitive
  references — including its two-level semantics (match vs capture).
- **Lazily resolved reference graph:** grammars are recursive struct types; the
  compiler must resolve self-referential and mutually recursive node graphs and
  reject left-recursive or empty-match cycles at build time.
- **Equivalence judgement:** `String()` renders the compiled grammar back to EBNF —
  a normalised projection whose shape must agree with the accepted input language.
- **Integration across >= 3 projections:** build errors, parse results, captured
  positions, and EBNF must stay consistent for one grammar definition.

## Upstream test audit (pre-screen)

- All root-package tests are `package participle_test` (external, public API only).
- Tests depend on `github.com/alecthomas/assert/v2` (third-party assert library)
  and `github.com/alecthomas/repr` (golden `repr` strings) — an oracle cannot lift
  them verbatim without importing non-target third-party modules; many assertions
  are golden-string reprs of internal AST shapes. Track decision deferred to S3A;
  Track B expected.
- `lexer/internal/conformance` is an internal conformance harness — excluded.

## External dependencies

Runtime deps of the target module: none outside stdlib (assert/repr are
test-only). Oracle can depend on the target module alone.

## Contamination

v2.1.4 released 2025-03-24. The library is public and popular (~4k stars), so the
model may know its API shape; the task measures reconstruction of behavior from
the spec, and assertions avoid golden internal reprs.

## Selection rationale

Parser-builder engine with a bespoke input language (struct tags), a reflection
capture layer with type-directed rules (kind-specific capture into string, int,
float, bool, slices, pointers, custom `Capture`/`TextUnmarshaler` types), two
lexer engines (text/scanner-based simple lexer, regex-based stateful lexer), and
a grammar-to-EBNF renderer. Multiple cooperating objects per scenario (lexer
definition + grammar structs + parser options + parse context). Clear behavioral
docs (README, TUTORIAL, godoc). Fixture-free: all inputs are Go string literals.

## Scope plan

In scope: `participle` root package (Build, MustBuild, Parser methods, options,
error types) + `lexer` package public surface (Definition, MustSimple,
MustStateful, Rules, Position, Token, symbol tables, PeekingLexer as used by
custom captures). Out of scope: `ebnf/` subpackage (standalone EBNF parser—
separate fact source), `cmd/`, `_examples/`, generated lexer codegen
(`participle/experimental`, none at this tag), railroad diagram generation.
