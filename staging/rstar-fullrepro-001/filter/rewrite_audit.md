# Rewrite Audit — rstar-fullrepro-001

Decision: **generated_only** (Track A yields zero keepable tests; Track B
generation is the entire oracle). Upstream tests serve as a behavior
checklist only.

## Why Track A yields nothing

Upstream tests are inline `#[cfg(test)]` modules compiled *inside* the
crate (`rstar/src/**`), not an external test suite. Every module fails the
import audit at file level:

1. **Crate-internal imports.** Test modules import `crate::test_utilities`
   (a `pub(crate)`-visible helper module shipped only in the crate's own
   test builds), `crate::algorithm::rstar::RStarInsertionStrategy` via a
   private path, `crate::algorithm::selection_functions::*`, and node
   internals (`crate::node::RTreeNode` constructors). None of these paths
   exist for an external consumer of the published API.
2. **Seeded-random data generators.** Nearly every behavioral assertion is
   a loop over `create_random_points/integers/lines/rectangles(N, SEED_x)`
   using `rand_hc::Hc128Rng` — a comparison of tree answers against a
   brute-force linear scan on random data. The assertions are self-relative
   (tree vs. scan), not value-pinned; re-expressing them requires carrying
   the exact RNG stack (`rand 0.8` + `rand_hc`) and the two 32-byte seeds,
   which asserts upstream's test data pipeline rather than spec behavior.
3. **Structure assertions.** Several tests assert node fan-out and depth
   after bulk load (`root().children().len()`), which the spec explicitly
   leaves unspecified (implementation partitioning is a non-goal).

## Per-file disposition

| Upstream test module | #[test] fns | Disposition | Reason |
|---|---|---|---|
| `src/rtree.rs::test` | 8 | discard, re-express | seeded-random brute-force comparisons (`test_utilities`), custom-params via internal path; behavioral intents (insert/size/iter/contains/locate/nearest agreement) re-expressed as value-pinned generated tests |
| `src/algorithm/iterators.rs::test` | 7 | discard, re-express | seeded-random locate/selection comparisons vs linear scan; re-expressed with small fixed point sets |
| `src/algorithm/removal.rs::test` | 6 | discard, re-express | seeded-random drain/remove loops; drain laziness and one-of-many removal re-expressed deterministically |
| `src/algorithm/nearest_neighbor.rs::test` | 6 | discard, re-express | seeded-random nearest/pop/iter comparisons vs sorted scan; re-expressed with fixed tie sets and distance sequences |
| `src/primitives/geom_with_data.rs::test` | 4 | discard, re-express | doc-style but written against internal constructors in one case; payload/geom forwarding re-expressed |
| `src/primitives/cached_envelope.rs::test` | 4 | discard, re-express | compares cached vs uncached trees on seeded-random data |
| `src/algorithm/bulk_load/bulk_load_sequential.rs::test` | 3 | discard | asserts internal cluster shapes and node sizes (spec non-goal) |
| `src/aabb.rs::test` | 3 | discard, re-express | seeded-random envelope containment loops; inclusive boundaries re-expressed with exact corner cases |
| `src/point.rs::test` | 2 | discard | `Point::generate`/`nth` unit checks on internal `min_inline`; covered by generated point-trait tests |
| `src/primitives/line.rs::test` | 2 | discard, re-express | one seeded-random distance loop, one value check; re-expressed with exact projection/clamp values |
| `src/algorithm/intersection_iterator.rs::test` | 2 | discard, re-express | seeded-random cross-tree candidate comparison vs nested loop; re-expressed with fixed box grids |
| `src/primitives/rectangle.rs::test` | 1 | discard, re-express | seeded-random distance loop; re-expressed with exact clamp values |
| `src/algorithm/bulk_load/cluster_group_iterator.rs::test` | 1 | discard | internal cluster iterator, no public surface |

Total upstream `#[test]` functions: 49. Kept as-is: 0. Re-expressed intent
coverage is recorded per generated test in `spec_test_map.md`.

## Track B protocol

Generated tests were written against `staging/rstar-fullrepro-001/spec.md`
only, with every expected value produced by running the pinned reference
checkout (`/tmp/refs/rstar` @ c8c5bf9, v0.12.2) through probe binaries —
three probe rounds recorded in `filter_notes.md` and the spec delta header.
No upstream test code was copied; upstream modules were used as a checklist
of behavior families (population, envelope algebra, locate family, nearest
family, removal/drain family, primitives, inspection, cross-tree
candidates, custom params/objects/selection).
