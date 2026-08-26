# Rewrite Audit — petgraph-fullrepro-001

Upstream commit: petgraph/petgraph @ 162903562ce5b00cdba390a0d9c1bb80f1c75bf5 (petgraph@v0.8.3)
Upstream test inventory: 378 test functions — 266 external under `tests/`
(23 files), 112 in-crate `#[cfg(test)]` mods under `src/`.

## Why the oracle is generated-only

1. **In-crate unit tests are all out of scope.** The 112 in-crate tests live in
   `matrix_graph.rs` (34), `algo/simple_paths.rs` (21), `csr.rs` (18),
   `dot/` (18), `visit/undirected_adaptor.rs` (4), `algo/steiner_tree.rs` (3),
   `acyclic.rs` (3), and one each in `tred`/`dominators`/`bridges` — every one a
   module the scope plan excludes. Zero in-crate tests target the in-scope
   containers, visitors, or bounded algorithm set.
2. **Out-of-scope external files (142 functions).** `iso.rs` (22, isomorphism +
   res/ fixture files), `quickcheck.rs` (18, non-default feature),
   `list.rs` (12, adjacency list container), `adjacency_matrix.rs` (11),
   `unionfind.rs` (10, internal data structure), `maximal_cliques.rs` (10),
   `matching.rs` (9), `articulation_points.rs` (9), `dinics.rs` (8),
   `graph6.rs` (7), `spfa.rs` (6), `johnson.rs` (5), `floyd_warshall.rs` (5),
   `steiner_trees.rs` (3), `page_rank.rs` (2), `ford_fulkerson.rs` (2),
   `coloring.rs` (2), `k_shortest_path.rs` (1) — all exercise algorithms or
   containers the spec's Non-Goals exclude. Discarded whole.
3. **In-scope external files import out-of-scope surface at file level
   (124 functions).**
   - `graph.rs` (67): imports `algo::{dominators, is_bipartite_undirected,
     is_isomorphic_matching}`, `graph::{GraphError, IndexType}`,
     `algo::DfsSpace`, `dot::Dot`, free helper `graph::node_index`, and visit
     traits (`IntoEdges`, `IntoEdgesDirected`, `IntoNodeIdentifiers`,
     `NodeIndexable`, `VisitMap`, `Walker`) the spec does not declare. Many
     bodies print `Dot::new(&g)` or assert via `NodeIndexable`/`VisitMap`.
   - `stable_graph.rs` (31): depends on `itertools::assert_equal` and the
     `defmac` macro crate; imports `adj::IndexType`, `dot::Dot`,
     `stable_graph::{edge_index, node_index}` free helpers, and visit traits
     (`EdgeIndexable`, `IntoEdgeReferences`, `IntoNodeReferences`,
     `NodeIndexable`); shared helper `assert_graph_consistent` iterates via
     out-of-scope traits.
   - `graphmap.rs` (18): uses `visit::Walker` (out of scope) and
     `dot::{Config, Dot}`; several tests assert Dot output shape.
   - `min_spanning_tree.rs` (7): tests `min_spanning_tree_prim` (out of scope)
     alongside `min_spanning_tree`, and prints `Dot`.
   - `operator.rs` (1): tests `operator::complement`, out of scope.
   Per the file-level rule, the import surface cannot be preserved; the
   behavioral intent of the in-scope subset is re-expressed with fresh
   fixtures through the spec's declared import surface only.
4. **Anti-memorization.** petgraph is among the most-known Rust crates; its
   test fixtures (e.g. the `gr` triangle graphs, "A"/"B"/"C" node labels,
   1000-node iso fixtures) are memorization-prone. All oracle fixtures are
   freshly authored with different vocabularies, sizes, weights, and
   assertion angles.

Decision: `oracle_source: generated_only`. Upstream in-scope tests serve as a
behavioral checklist; every oracle test is authored fresh against the spec and
validated by executing the pinned reference.

## Per-file disposition

| file | fns | disposition | reason |
|---|---|---|---|
| tests/graph.rs | 67 | discard file, re-express in-scope intent | out-of-scope imports (dominators/iso/bipartite/GraphError/IndexType/DfsSpace/Dot/node_index/visit traits); intent covered by generated container+adjacency+algo tests |
| tests/stable_graph.rs | 31 | discard file, re-express in-scope intent | itertools+defmac deps, Dot, index helpers, out-of-scope visit traits; intent covered by generated StableGraph tests |
| tests/graphmap.rs | 18 | discard file, re-express in-scope intent | Walker trait + Dot asserts; intent covered by generated GraphMap tests |
| tests/min_spanning_tree.rs | 7 | discard file, re-express in-scope intent | min_spanning_tree_prim out of scope, Dot prints; MST intent covered by generated tests |
| tests/operator.rs | 1 | discard | operator::complement out of scope |
| tests/iso.rs | 22 | discard | isomorphism out of scope + res/ fixtures |
| tests/quickcheck.rs | 18 | discard | non-default feature |
| tests/list.rs | 12 | discard | adjacency list container out of scope |
| tests/adjacency_matrix.rs | 11 | discard | matrix container out of scope |
| tests/unionfind.rs | 10 | discard | internal data structure out of scope |
| tests/maximal_cliques.rs | 10 | discard | out of scope |
| tests/matching.rs | 9 | discard | out of scope |
| tests/articulation_points.rs | 9 | discard | out of scope |
| tests/dinics.rs | 8 | discard | out of scope |
| tests/graph6.rs | 7 | discard | out of scope |
| tests/spfa.rs | 6 | discard | out of scope |
| tests/johnson.rs | 5 | discard | out of scope |
| tests/floyd_warshall.rs | 5 | discard | out of scope |
| tests/steiner_trees.rs | 3 | discard | out of scope |
| tests/page_rank.rs | 2 | discard | out of scope |
| tests/ford_fulkerson.rs | 2 | discard | out of scope |
| tests/coloring.rs | 2 | discard | out of scope |
| tests/k_shortest_path.rs | 1 | discard | out of scope |
| src/** in-crate mods | 112 | discard | all in out-of-scope modules (matrix_graph/simple_paths/csr/dot/acyclic/tred/dominators/bridges/undirected_adaptor/steiner_tree) |

functions_in_scope: 378 (266 external + 112 in-crate)
functions_kept: 0 (generated-only)
functions_excluded: 378

## Dummy-passable patterns avoided in generation

- Every toposort/SCC/condensation assertion validates the defining property
  (successor-before rule, mutual-reachability partition) or a positive value,
  never just `is_ok()`/`is_err()`.
- `Err(Cycle)`/`Err(NegativeCycle)` tests pair the error assertion with a
  positive sibling (e.g. the acyclic variant of the same fixture returning a
  valid order), so an always-erroring stub cannot collect failure-path points
  disproportionately.
- No test asserts Debug/Display formatting, hash-map iteration order, or
  internal capacity values.
