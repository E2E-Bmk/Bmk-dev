# Stage 1 screening — similar-fullrepro-001

```
repo: mitsuhiko/similar
source_path: https://github.com/mitsuhiko/similar
commit: 28c146b628119065e9a4dae569eaa570a4632c17 (tag 2.7.0, released 2025-01-19)
src_loc: ~5009 non-test (5815 total in src/ incl. inline #[test] tails)
test_functions: 50 inline #[test] fns (algorithms 23, text 22, common 1, udiff 3, utils 1)
test_files: tests live inline in src/ modules; no tests/ dir; 3 insta .snap files
dominant_test_styles: unit asserts on op vectors/changes (84 plain asserts) + 28 insta snapshot asserts (25% of asserts; all rewritable to explicit expected values)
public_docs: docs.rs/similar 2.7.0 (crate root + algorithms/udiff/utils module docs, all public items documented under #![warn(missing_docs)]), README
core_fact_source: the computed DiffOp sequence (Equal/Delete/Insert/Replace index ranges) produced by an algorithm run (Myers/Patience/LCS) plus Replace/Compact postprocessing over two indexable sequences
derived_views: (1) ops()/grouped_ops() structured op vectors; (2) iter_changes()/iter_all_changes() per-item Change stream with tags and missing-newline handling; (3) unified_diff text rendering with hunk headers and newline hint; (4) ratio() similarity metric; (5) iter_inline_changes word-level emphasis within line diffs (inline feature); (6) utils: get_close_matches ranking + TextDiffRemapper mapping tokenized changes back to original slices; (7) generic DiffHook layer (Capture/Replace/Compact/NoFinishHook/IdentifyDistinct) reachable directly
external_deps: unicode-segmentation (unicode feature; keep), bstr (bytes feature; scope out), serde (scope out), web-time (wasm only; scope out); dev-deps insta/console/serde_json not carried into the oracle — snapshot asserts rewritten to explicit expected op vectors
test_import_audit: clean for oracle purposes with rewrites — tests are inline unit tests so a handful reach private internals (myers::find_middle_snake/V/max_d, text::utils); those are dropped or rewritten onto the public surface; the majority already drive public paths (algorithms::myers::diff + Capture/Replace, TextDiff builders, udiff)
docs_test_alignment: aligned — module docs describe exactly the projections the tests exercise (op capture, changes, grouping, unified output, inline changes, ratio, close_matches)
contamination_note: similar@2.7.0, released 2025-01-19, relative to training cutoff: likely before (mitigation: snapshot values recomputed, generated tests use novel inputs, spec written from docs not source)
decision: keep
reason: diff engine with one fact source (postprocessed DiffOp stream) projected through 7 public surfaces, three interchangeable algorithms plus two composable postprocessing hooks, and format-rule reimplementation (unified hunk headers, missing-newline hint, grapheme segmentation) that resists pattern-matching beyond textbook Myers.
risks: Myers itself is textbook (mitigated: the oracle weight sits on postprocessing, grouping, unified rendering, inline emphasis, remapping — library-specific rules); 50 upstream tests is thin (mitigated: generated cross-view tests); insta snapshots must be materialized as explicit values (done during Stage 3 rewrite).
scope_plan: N/A (5009 LOC, 50 test fns; features scoped to text+inline+unicode, bytes/serde/wasm32_web_time out)
```

## Rule-engine shapes observed (selection rationale)

- **Multiple projections of one state**: the op stream feeds ops, grouped_ops,
  changes, unified rendering, ratio, and inline emphasis; integration tests can
  span >= 3 projections of one diff.
- **Reimplementation of a format rule**: unified diff hunk headers
  (`@@ -a,b +c,d @@`), context radius grouping, and the
  `\ No newline at end of file` hint are format rules the delivery must
  reproduce, not call into.
- **Equivalence judgement**: `ratio()` and `get_close_matches` produce ranked
  similarity judgements where a false alarm is as wrong as a miss.

## Toolchain pin

Sandbox rustc is 1.83. similar 3.x requires edition 2024 / rust-version 1.85 —
unbuildable here. Pinned 2.7.0 (edition 2018, rust-version 1.60), the last 2.x
release. Only optional dependency kept is unicode-segmentation (pure Rust,
builds on 1.83).
