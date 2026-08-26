# Rewrite Audit — indexmap-fullrepro-001

Decision: **generated_only** (Track A yields too few clean tests to anchor
an oracle; Track B generation is the entire oracle). Upstream tests serve
as a behavior checklist only.

## Why Track A yields (almost) nothing

1. **Inline crate-internal modules.** The two dominant test files —
   `src/map/tests.rs` (35 `#[test]` fns) and `src/set/tests.rs` (30) — are
   `#[cfg(test)]` modules compiled inside the crate with `use super::*`.
   They reach non-public internals (`assert_eq!(map.capacity(), 0)` exact
   capacity growth expectations, internal debug formats under the
   `test_debug` feature, `binary_search`-free positional internals) and
   cannot be lifted into an external test crate as-is.
2. **Property harness.** `tests/quick.rs` is a quickcheck harness (macro
   blocks expanding ~20 properties) with `quickcheck`, `fnv`, and
   `itertools` dev-dependencies, comparing against `HashMap`/`Vec` models
   on random input. The assertions are self-relative, not value-pinned;
   re-expressing them requires carrying the RNG stack.
3. **Tiny external remainder.** `tests/tests.rs` (2), 
   `tests/equivalent_trait.rs` (2), and `tests/macros_full_path.rs` (2)
   are clean public-API tests, but six tests cannot anchor a two-layer
   oracle; their intents (macro construction with the duplicate law,
   caller-defined `Equivalent` lookups) are re-expressed as generated
   tests instead of maintaining a mixed-provenance oracle for six rows.

## Per-file disposition

| Upstream test file | #[test] fns | Disposition | Reason |
|---|---|---|---|
| `src/map/tests.rs` | 35 | discard, re-express | inline `use super::*` module; exact-capacity assertions; behavioral intents (insert/get/swap vs shift/entry/sort/binary_search/splice/append laws) re-expressed value-pinned |
| `src/set/tests.rs` | 30 | discard, re-express | inline module; same pattern for set membership, identity, algebra order laws |
| `tests/quick.rs` | 1 macro block (~20 properties) | discard | quickcheck/fnv/itertools harness, model-comparison on random data |
| `tests/tests.rs` | 2 | discard, re-express | macro construction + ordering smoke; re-expressed with duplicate-law assertions |
| `tests/equivalent_trait.rs` | 2 | discard, re-express | caller-defined `Equivalent` impl lookups; re-expressed |
| `tests/macros_full_path.rs` | 2 | discard, re-express | `::indexmap::indexmap!` full-path invocation; construction covered by macro tests |

Total upstream `#[test]` functions: 72 (counting the quickcheck block as
its expanded properties: ~91). Kept as-is: 0. Re-expressed intent coverage
is recorded per generated test in `spec_test_map.md`.

## Track B protocol

Generated tests were written against `staging/indexmap-fullrepro-001/spec.md`
only, with every expected value produced by running the pinned reference
checkout (`/tmp/refs/indexmap` @ 42e57a3, 2.7.1) through probe binaries —
three probe rounds recorded in `filter_notes.md` and the spec delta header.
No upstream test code was copied; upstream modules were used as a checklist
of behavior families (construction/duplicates, lookup addresses, swap vs
shift removal, order surgery, bulk rewrites, sort/search, slices, entry
interface, set identity, set algebra, iteration).
