# Rewrite audit — similar-fullrepro-001

Upstream 2.7.0 ships ~50 inline `#[cfg(test)]` functions (no `tests/`
directory). 33 were kept after adaptation (prefix `test_`); the rest of the
oracle (58 functions, prefix `generated_`) was written against the spec with
expected values probed from the reference build. Suite total: 91 base test
functions (64 atomic, 27 integration).

## Removed upstream tests

| upstream test | location | reason |
|---------------|----------|--------|
| `test_find_middle_snake` | `algorithms/myers.rs` | asserts private `find_middle_snake` internals; not part of the public contract |
| `test_shortcut` (udiff modules) | `udiff.rs` | duplicated by kept `generated_unified_quick_fn_equals_pipeline` without snapshot dependency |
| `test_deadline_reached` | `text/mod.rs` | timing-sensitive: asserts a diff aborts within a wall-clock deadline; nondeterministic under load |
| `test_serde_*` | `types.rs`, `text/mod.rs` | `serde` feature is out of spec scope |
| byte/`bstr` tests | `text/mod.rs`, `utils.rs` | `bytes` feature is out of spec scope |

## Rewritten upstream tests

| oracle test | change | reason |
|-------------|--------|--------|
| `atomic::test_myers_raw_capture_minimal_script` | was `test_diff` asserting the exact raw callback sequence from `myers::diff` into `Capture` | raw callback granularity is unspecified; now asserts the captured stream is a valid, minimal edit script that reconstructs the new sequence |
| `atomic::test_lcs_same_single_equal` | was asserting raw `lcs::diff` callbacks on identical inputs | moved to `capture_diff_slices`, whose single-`Equal` guarantee the spec declares |
| `atomic::test_captured_ops`, `test_char_diff`, `test_ratio`, `test_get_close_matches`, `test_remapper`, `test_virtual_newlines`, `test_split_*` | were `insta::assert_snapshot!` / debug-snapshot assertions | snapshots inlined as explicit `assert_eq!` on values probed from the reference build; no `insta` dependency in the oracle |
| `integration::udiff::test_unified_diff_*` | were snapshot assertions on rendered diffs | rendered text inlined as explicit expected strings; inputs re-worded so expected strings differ from upstream snapshot fixtures (anti-memorization) |
| `integration::inline::test_line_ops_inline` | was a debug-snapshot of `InlineChange` vectors | now asserts tag/index skeleton plus segment-level values and the concatenation invariant |
| `atomic::test_lifetimes_on_iter` | kept, minus the commented-out borrow-check section | the commented section documents a compile failure, not runtime behaviour |

## Generated additions

- Algorithm dispatch equivalence (`generated_algorithm_selection`),
  hook error propagation, `NoFinishHook`, default `ops_replace` splitting.
- `DiffOp` accessor family (`tag`, `as_tag_tuple`, ranges, `iter_slices`,
  `iter_changes` ordering, `apply_to_hook` replay).
- Tokenizer behaviour for all five text modes plus `DiffableStr` inspection
  helpers and owned-string entry (`DiffableStrRef`).
- Grouping (`group_diff_ops`, `grouped_ops`, `Capture::into_grouped_ops`
  agreement), similarity (`get_diff_ratio`, close-match cutoff behaviour).
- Unified diff: header suppression without hunks, `to_writer` vs `Display`,
  hunk/grouped-ops alignment, `UnifiedHunkHeader` formatting.
- Inline emphasis: word-replace emphasis, coverage invariant, deadline
  variant agreement, `From<Change>`.
- Cross-view invariants: op-replay reconstruction for all three algorithms,
  `TextDiff` vs generic capture equality, `iter_all_changes` vs flat-map,
  ratio equality, `IdentifyDistinct` equivalence, manual hook stack vs
  `capture_diff`, utils concatenation coverage, remapper coverage.

## Anti-memorization

All generated tests use fresh input texts (fruit/instrument/workshop word
lists, re-worded prose) rather than upstream fixture strings; expected op
streams, ratios, and rendered diffs were captured from the reference build
via a probe binary, then verified by the full oracle run.
