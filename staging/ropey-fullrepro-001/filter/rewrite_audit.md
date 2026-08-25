# Rewrite audit — ropey-fullrepro-001

Upstream v1.6.1 carries ~334 inline `#[cfg(test)]` functions across
`rope.rs`/`slice.rs`/`iter.rs`/`rope_builder.rs`/`str_utils.rs`/`crlf.rs`/
`tree/*`, plus ~49 functions in `tests/` and 32 proptest properties. The
oracle is **generated-only**: 91 fresh test functions (58 atomic, 33
integration) written against the spec, with expected values verified by
running the pinned reference (probe binary + full suite run). No upstream
function was kept verbatim.

## Why generated-only

1. **Repetition**: the inline suites are dominated by indexed variants
   (`byte_to_char_01..05`, `slice_01..10`, ...) of one behavior each;
   keeping them verbatim would blow past the scope cap (`expected_oracle_max
   = 110`) without adding behavioral coverage. Each variant family is
   covered by one generated test asserting the same rule across positions.
2. **Hidden-surface reliance**: `tests/fix_tree.rs`, `tests/small_random_inserts.rs`
   and several inline tests import `MAX_BYTES`/`MIN_BYTES`/`MAX_CHILDREN`/
   `MIN_CHILDREN` (all `#[doc(hidden)]`, "NOT PART OF THE PUBLIC API") or
   `Lines::from_str_pt`/`assert_integrity`/`assert_invariants` (same). The
   spec does not declare them; every such test is excluded per Q1.
3. **Randomization**: `tests/proptest_tests.rs` (proptest) and
   `tests/small_random_inserts.rs` (rand) are nondeterministic; their
   invariant content (edit == flat-string model; chunk reassembly) is kept
   as deterministic fixed-script tests
   (`integration::editing::generated_edit_session_*`,
   `generated_large_document_edit_consistency`).
4. **Anti-memorization**: upstream fixture constants (`TEXT`, `TEXT_LINES`,
   `TEXT_EMOJI`, `tests/*.txt`) are widely mirrored in public forks; all
   oracle fixtures are fresh texts with hand- or model-verified expected
   values.

## Upstream disposition by file

| upstream file | functions | disposition |
|---------------|-----------|-------------|
| `src/rope.rs` tests | 116 | behaviors consolidated into generated construction/metrics/conversion/edit/chunk tests |
| `src/slice.rs` tests | 98 | consolidated into generated slicing/local-coordinate tests |
| `src/iter.rs` tests | 104 | consolidated into generated iterator tests (positioned, prev, reverse, exact-size) |
| `src/rope_builder.rs` tests | 2 | covered by `generated_builder_matches_from_str` (public `append`/`finish` only; `_append_chunk`/`_finish_no_fix` are private-by-convention and unused) |
| `src/str_utils.rs` tests | 15 | consolidated into two generated `str_utils` tests |
| `src/crlf.rs` tests | 9 | private module internals — excluded; CRLF behavior covered via public line APIs |
| `src/tree/*` tests | 26 | private tree internals — excluded |
| `tests/{clone_rope,clone_rope_to_thread,hash,from_str,from_reader,shrink_to_fit}.rs` | 10 | behaviors re-expressed: clone independence, hash agreement, reader errors, shrink content preservation |
| `tests/{crlf,fix_tree,small_random_inserts,proptest_tests}.rs` | ~39 | use doc(hidden) constants and/or randomness — excluded; deterministic equivalents generated |
| `tests/{lifetimes,non_ascii_comparison}.rs` | 3 | covered by iterator-on-slice and eq-matrix tests |

## Fairness notes

- No test asserts chunk layout (chunk sizes, chunk counts, `Debug` output,
  `as_str()` on rope-backed slices); chunk assertions are invariant-based
  (containment, start-coordinate consistency, reassembly, non-emptiness).
- No `#[should_panic]` tests: every failure path asserts `try_`/`get_`
  values and `Error` variant payloads, which the spec declares.
- Two spec_gap patches were routed to the spec during oracle work (empty
  content chunk behavior; end-position chunk-iterator line coordinate) —
  both grounded in the reference's documented public behavior, neither
  motivated by a failing assertion on undeclared surface.
- Static dummy audit: every test calls into `ropey` and asserts produced
  values; a stub crate panicking with `unimplemented!()` fails all 91.
