# Stage 1 screening — ropey-fullrepro-001

```
repo: cessen/ropey
source_path: https://github.com/cessen/ropey (local clone /tmp/refs/ropey)
commit: d41ee247f2f097c7f9c8e4730b7dd884734f1ee5 (tag v1.6.1)
language: rust
src_loc: 8328 (non-test lines in src/, inline #[cfg(test)] modules excluded; 14373 raw)
test_functions: ~415 (334 inline unit tests in src/, ~49 in tests/, 32 proptest properties)
test_files: inline modules in rope.rs/slice.rs/iter.rs/rope_builder.rs/str_utils.rs/crlf.rs/tree/*; tests/{clone_rope,crlf,fix_tree,from_reader,from_str,hash,lifetimes,non_ascii_comparison,shrink_to_fit,small_random_inserts,proptest_tests}.rs
dominant_test_styles: deterministic unit asserts over fixed texts (dominant); ~32 proptest properties (excluded from oracle); zero snapshot tests; no network
public_docs: docs.rs/ropey/1.6.1 (all public items documented with panics/complexity notes), README, examples/
core_fact_source: one immutable-persistent B-tree rope holding UTF-8 text with cached byte/char/line/utf16 metrics per node
derived_views: (1) byte/char/line/utf16 coordinate projections and cross-conversions on Rope and RopeSlice; (2) editing surface insert/remove/split_off/append preserving invariants; (3) four bidirectional iterators (Bytes/Chars/Lines/Chunks) with at_-offset constructors and reverse; (4) RopeSlice sub-view mirroring the read surface incl. re-slicing; (5) chunk-level access (chunk_at_byte/char/line_break) + RopeBuilder streaming construction; (6) io surface from_reader/write_to; (7) cross-type PartialEq/Ord/Hash agreement with str/String and between Rope/RopeSlice; (8) str_utils public index-conversion functions
external_deps: smallvec, str_indices (both MSRV-compatible with rustc 1.83); dev-deps rand/proptest/criterion NOT carried into the oracle
test_import_audit: clean — inline test modules use `use super::*`/`crate::Rope`/`crate::str_utils::*`, all of which are public exports; tree-internal tests (node_children/node_text) touch private types and are excluded; no undocumented carrier modules
docs_test_alignment: aligned — docs.rs documents exactly the projections the tests exercise (indexing, conversion, panics on out-of-bounds, iterator semantics, try_* fallible twins)
contamination_note: ropey@1.6.1, released 2023-09-05, before training cutoff; anti-memorization via fresh test texts and values in generated tests
decision: keep
reason: coordinate-system rule engine (byte/char/line/utf16 boundary math incl. CRLF and Unicode line breaks) over a persistent tree with 8 public projections of one fact source; wrong-by-one index math is exactly the equivalence-judgement shape models miss
risks: central type is one Rope class (mitigated: slices/iterators/builder are genuinely separate cooperating surfaces); huge inline test count needs scoping; proptest suites must be converted or dropped; feature flags (unicode_lines/cr_lines) change line-break semantics and must be pinned in the spec
scope_plan: target_subdomain=public rope surface (Rope/RopeSlice/RopeBuilder/iter/str_utils with default features incl. unicode_lines), tree internals and proptest excluded; expected_oracle_max=110
```

Difficulty shapes (candidate-selector heuristic): reimplementation of a
format rule (UTF-8 char boundaries, utf16 surrogate accounting, Unicode line
breaks per feature); ≥3 cooperating objects per scenario (Rope + slice +
iterator, builder + rope + io); integration tests can span editing +
slicing + iteration + comparison of one text state. Not an equivalence
judgement or lazy reference graph.

Toolchain check: `rust-version = "1.65"`, edition 2021, deps smallvec 1.x and
str_indices 0.4 build on sandbox rustc 1.83 (verified via cargo build of the
checkout). Default features `unicode_lines` + `simd` retained.
