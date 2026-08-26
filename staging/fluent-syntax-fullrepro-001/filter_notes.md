# Stage 1 screening — fluent-syntax-fullrepro-001

repo: projectfluent/fluent-rs (workspace member fluent-syntax)
source_path: https://github.com/projectfluent/fluent-rs (local clone /tmp/refs/fluent-rs)
commit: f22da4ea48328b4c617b7666c482634c49fbe0a7 (tag fluent-syntax@0.12.0, released 2025-05-22)
src_loc: 3900 (fluent-syntax/src excluding src/bin fixture-update tool)
test_functions: 24 (6 external under fluent-syntax/tests driving a 37-pair
FTL/JSON fixture corpus + round-trip loops; 18 in-crate incl. unicode unit
tests); plus a large executable doc-test surface (ast/parser/serializer doc
examples assert exact AST values)
test_files: fluent-syntax/tests/{parser_fixtures.rs, serializer_fixtures.rs, unicode.rs} + tests/fixtures/*.{ftl,json}
dominant_test_styles: fixture-compare (parsed AST vs serde-JSON reference), parse->serialize->parse round trips, doc-example assertions
public_docs: docs.rs/fluent-syntax 0.12.0 (parser, ast — every node documented with an FTL snippet and the exact AST it parses to — serializer, unicode module docs), projectfluent.org FTL syntax guide
core_fact_source: one syntax model — the FTL abstract syntax tree (Resource of Message/Term/Comment entries with Patterns, PatternElements, Expressions, Attributes, Variants) generic over the underlying string slice
derived_views: (1) parse — full AST with comment attachment; (2) parse_runtime — same grammar, comments skipped; (3) error recovery — invalid spans become Junk entries with ParserError {pos, slice, kind} records while surrounding entries still parse; (4) serializer (serialize / serialize_with_options with junk toggle) producing canonical FTL text with round-trip stability; (5) unicode unescaping (unescape_unicode / unescape_unicode_to_string) applied to literal text
external_deps: memchr + thiserror only under default features (serde/json optional and out of scope); rust-version 1.64 — builds clean on cargo 1.83
test_import_audit: external tests import only fluent_syntax::{ast, parser, serializer, unicode} public paths, but depend on the serde feature (JSON AST fixtures), the glob crate, and a tests/helper adapter — the fixture-compare harness cannot be retained; in-crate unicode tests use super:: paths; generated-only oracle expected, fixtures as behavioral checklist
docs_test_alignment: aligned — docs assert the same parse/serialize/unescape projections the tests exercise, at the exact-AST level
contamination_note: fluent-syntax@0.12.0, released 2025-05; FTL is an open format with sibling implementations (JS/Python) and a shared upstream fixture corpus — memorization-prone fixtures; oracle uses freshly authored FTL snippets with different vocabulary and assertion angles
decision: keep
reason: a format-rule reimplementation task (FTL grammar: significant whitespace, continuation-line and common-indent stripping rules for multiline patterns, select-expression variants with default markers, string-literal escapes, CRLF handling, comment levels and attachment, structured junk recovery with byte-range errors) projected through parse, parse_runtime, the serializer, and unicode unescaping over one public AST — indentation-sensitive parsing plus recovery spans resist pattern-matching.
risks: upstream test suite is >70% fixture/snapshot style — mitigated by a generated-only oracle asserting small spec-derivable AST fragments (the AST is the documented public data model, so structural assertions are behavioral here); ErrorKind is a wide enum — spec declares the full documented variant list but oracle asserts only well-documented kinds plus pos/slice ranges; serializer output for exotic junk/comment mixes is canonical-form dependent — assert round-trip fixed points and documented shapes only
scope_plan: N/A (3900 LOC, 24 test functions)

Difficulty shapes (selection rationale): reimplementation of a format rule
(the FTL grammar, including indentation-significant multiline dedent and
escape semantics); equivalence judgement (parse -> serialize -> parse fixed
points where distinct inputs normalize to one canonical text); integration
tests spanning >=3 projections (source text -> AST -> canonical text -> AST,
with error records and junk entries as a fourth surface on invalid input).
