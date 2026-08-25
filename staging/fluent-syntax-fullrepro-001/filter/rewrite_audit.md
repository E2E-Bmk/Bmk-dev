# Rewrite Audit — fluent-syntax-fullrepro-001

Upstream commit: projectfluent/fluent-rs @ f22da4ea48328b4c617b7666c482634c49fbe0a7
(tag fluent-syntax@0.12.0), workspace member `fluent-syntax`.
Upstream test inventory: 18 test functions — 6 in external `tests/` files, 12
in-crate in `src/serializer.rs`'s `#[cfg(test)]` module — plus a 37-pair
FTL/JSON fixture corpus under `tests/fixtures/` and 36 executable doc examples.

## Why the oracle is generated-only

1. **The parser suite is feature-gated and corpus-driven.**
   `tests/parser_fixtures.rs` (3 fns) deserializes reference ASTs from JSON via
   `serde_json` and the crate's `serde` feature (declared
   `required-features = ["json"]` in the manifest), walks the fixture corpus
   with the `glob` crate, and adapts CRLF cases through a `tests/helper`
   module. The spec scopes out the serde/json features; without them the file
   does not compile, and the assertion source (the JSON snapshots) is exactly
   the snapshot style the oracle must avoid.
2. **The serializer round-trip suite is corpus-driven.**
   `tests/serializer_fixtures.rs` (2 fns) globs the same fixture corpus and an
   IGNORE_LIST of known non-round-tripping files. The round-trip *intent* is
   fully in scope (spec: Serialization > Stability; Cross-View Invariants 1–3)
   and is re-expressed over fresh inline FTL snippets with the ignore-listed
   behaviors (CRLF element splitting) asserted per spec instead of skipped.
3. **The in-crate serializer tests are structurally unavailable.** The 12
   `#[cfg(test)]` functions in `src/serializer.rs` test the private
   `TextWriter` directly (1 fn) and mutate parsed ASTs through test-local
   `impl` blocks on crate types (11 fns); they compile only inside the crate.
   The AST-mutation intent (parse → edit public fields → serialize) is
   re-expressed through the public AST, whose fields are all public.
4. **The unicode test is public-API but memorization-prone.**
   `tests/unicode.rs` (1 fn) imports only `fluent_syntax::unicode` public
   paths and would compile externally; its fixture values (`\uA0Pl`, `\d Foo`)
   are shared verbatim with sibling Fluent implementations. The intent (escape
   decoding, replacement-character fallbacks, borrow-vs-own) is re-expressed
   with fresh values covering the same and additional edge classes (six-digit
   escapes, out-of-range scalars, trailing backslash).
5. **Anti-memorization.** The upstream fixture corpus (hello-world, Firefox
   brand terms, `foo`/`bar` keys) recurs across fluent.js, python-fluent, and
   this crate's docs. All oracle fixtures use fresh vocabulary (harbor/orbital
   station domain), fresh escape values, and assertion angles that bind AST
   fragments, canonical text, and error records together rather than
   snapshot-comparing whole trees.

Decision: `oracle_source: generated_only`. Upstream tests and the 36 doc
examples serve as a behavioral checklist; every oracle test is authored fresh
against the spec and validated by executing the pinned reference.

## Per-file disposition

| file | fns | disposition | reason |
|---|---|---|---|
| tests/parser_fixtures.rs | 3 | discard, re-express in-scope intent | requires serde/json features (out of scope) + glob + JSON snapshot corpus; parse intent covered by generated grammar/AST tests with fresh FTL |
| tests/serializer_fixtures.rs | 2 | discard, re-express in-scope intent | glob + fixture corpus; round-trip intent covered by generated fixed-point/reparse tests on inline snippets |
| tests/unicode.rs | 1 | discard, re-express in-scope intent | public-API but fixture values shared across Fluent implementations; unescape intent covered with fresh values |
| src/serializer.rs `mod test` | 12 | discard, re-express in-scope intent | in-crate: private TextWriter + test-local impl blocks; AST-mutation→serialize intent covered via public AST fields |

functions_in_scope: 18
functions_kept: 0 (generated-only)
functions_excluded: 18

## Dummy-passable patterns avoided in generation

- Every parse-error test pairs the error-kind assertion with positive
  assertions on the recovered tree (the junk content and the surviving
  sibling entries), so a parser that rejects everything cannot collect
  failure-path points disproportionately.
- Pattern assertions compare full element vectors (`Vec<PatternElement>`)
  or complete node equality, never just lengths or `is_ok()`.
- No test asserts `Debug` output, error `Display` wording, or the payload
  text of the two escape-sequence error kinds (spec-excluded).
- Round-trip tests assert the intermediate canonical string and the reparsed
  tree, so a serializer echoing its input fails the canonical-string check
  and a parser-only implementation fails the reparse check.
