# Stage 1 screening — rstar-fullrepro-001

repo: georust/rstar (crate `rstar`)
source_path: https://github.com/georust/rstar (local checkout /tmp/refs/rstar)
commit: c8c5bf9ce9d127f6ac0e0f0475cf0dd0d0b2f398 ("Update to 0.12.2", manifest version 0.12.2; the v0.12.2 git tag itself points one commit earlier at a 0.12.1 manifest, so the version-bump commit is pinned instead)
src_loc: 4560 (rstar/src, 5594 total lines minus 1034 inline #[cfg(test)] module lines)
test_functions: 49 (all in-src #[cfg(test)] modules; no tests/ directory)
test_files: 13 in-src test modules (rtree, aabb, point, primitives/{geom_with_data,cached_envelope,line,rectangle}, algorithm/{intersection_iterator,nearest_neighbor,removal,iterators,bulk_load/*})
dominant_test_styles: seeded-random property checks (rand_hc HC128 with fixed seeds via src/test_utilities.rs) + exact unit assertions on envelope math and small trees
public_docs: docs.rs/rstar rustdoc (crate root guide, RTree method docs incl. complexity notes, AABB/Envelope trait contracts, primitives docs, RTreeParams/InsertionStrategy docs), README
core_fact_source: one spatial fact set — the multiset of inserted objects and their envelopes; the R*-tree is an index over it with a single geometric metric (min/max corner AABB arithmetic over Point scalars)
derived_views: (1) population/lookup: size/iter/locate_at_point/contains, (2) envelope queries: locate_in_envelope{,_intersecting}, intersection candidates between two trees, (3) metric queries: nearest_neighbor{,s,_iter,_iter_with_distance_2}, within_distance, pop_nearest_neighbor, (4) mutation: insert/remove{,_at_point}/drain_* with SelectionFunction, (5) construction: bulk_load vs incremental insertion (identical query semantics), (6) AABB/Envelope public arithmetic (merge/intersects/contains_point/area/distance_2), (7) primitives layer (Line/Rectangle distance+envelope, GeomWithData, CachedEnvelope, PointWithData) over the same trait contracts
external_deps: heapless, smallvec, num-traits (libm) — all build-time only, no isolation needed; dev-only rand/rand_hc/approx/nalgebra not used by the oracle
test_import_audit: HIGH_RISK for direct import (100% of upstream tests are in-src modules with private access and seeded rand data) — handled as generated_only re-expression, same as prior packets on this branch
docs_test_alignment: aligned — rustdoc documents the same public query/mutation surfaces the in-src tests exercise; geometric results are math-verifiable without internals
contamination_note: rstar@0.12.2, released 2024-11-05, relative to training cutoff: likely before (same situation as fst/textwrap/ignore packets; noted, tolerated for fullrepro tier). v0.13.0 (2026-05-24) was rejected: rust-version 1.85 exceeds the scorer toolchain cargo 1.83.
decision: keep
reason: multi-component spatial rule engine (trait-driven envelope contract + tree construction strategies + branch-and-bound metric queries + selection-function mutation) whose observable behavior is exactly derivable from documented geometry, resisting pattern-matching while staying probe-verifiable.
risks: iteration order and tree shape are implementation-defined — the spec and oracle must only assert set/multiset semantics and documented orderings (nearest_neighbor_iter distance order); f64 distance arithmetic needs exactly-representable coordinates to keep assertions robust; upstream removal/selection APIs (drain_*) have subtle contracts to probe.
scope_plan: N/A (src_loc 4560 < 15000, test_functions 49 < 300)

## Difficulty shapes (selection rationale)

- equivalence judgement: bulk_load-built and incrementally built trees must
  answer every query identically — set-equality across construction paths.
- rule reimplementation: R*-tree insertion/split/reinsertion and
  branch-and-bound nearest-neighbor are algorithm rules the candidate must
  re-derive from documented behavior, not call into.
- >= 3 public projections of one state: population, envelope queries, metric
  queries, mutation, and envelope arithmetic all project the same object set.
