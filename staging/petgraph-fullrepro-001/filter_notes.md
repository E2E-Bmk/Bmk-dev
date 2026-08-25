# Stage 1 screening — petgraph-fullrepro-001

repo: petgraph/petgraph
source_path: https://github.com/petgraph/petgraph (local clone /tmp/refs/petgraph)
commit: 162903562ce5b00cdba390a0d9c1bb80f1c75bf5 (tag petgraph@v0.8.3)
src_loc: 27183 (src/**/*.rs incl. in-file test mods; well above the 3000 floor even after scoping)
test_functions: ~300 external under tests/ (graph.rs 67, stable_graph.rs 31, iso.rs 22, graphmap.rs 18, quickcheck.rs 18, + ~20 algorithm files) plus in-crate mods
test_files: tests/{graph,stable_graph,graphmap,list,adjacency_matrix,iso,quickcheck,...}.rs — external, public-API imports
dominant_test_styles: unit + integration through public API; one quickcheck property file (feature-gated); iso uses res/ fixture files
public_docs: docs.rs/petgraph 0.8.3 (crate root, graph/stable_graph/graphmap modules, visit module, algo module docs), README
core_fact_source: one node/edge store (weights + directionality + adjacency) behind three container shapes (Graph, StableGraph, GraphMap)
derived_views: (1) container queries: counts/weights/neighbors/edges/Direction filters; (2) index-stability semantics across removals (swap-remove vs holes); (3) traversal visitors (Bfs, Dfs, DfsPostOrder, Topo) as lazy walkers; (4) algorithm projections: connectivity, cycle detection, toposort, SCCs, shortest paths (dijkstra/astar/bellman_ford), MST element stream; (5) transforms: map/filter_map/retain/reverse/extend/from_edges/from_elements; (6) visit-trait adapters (Reversed, node/edge filtering) consumed by the same algorithms
external_deps: fixedbitset 0.5, indexmap 2.x, hashbrown 0.15 — pure data-structure crates, no services; oracle lock must pin indexmap =2.7.1 (2.14 pulls hashbrown 0.17 which needs edition2024, unavailable on cargo 1.83)
test_import_audit: clean — external tests import only petgraph public paths; quickcheck.rs behind non-default feature; iso res/ fixtures excluded with the iso scope
docs_test_alignment: aligned — docs.rs documents the exact container/algorithm surface the external tests exercise
contamination_note: petgraph@0.8.3, released 2025; API core is long-stable and widely known — mitigated by fresh fixtures, checker-style assertions for multi-valid outputs, and spec-authority divergence framing
decision: keep
reason: one adjacency fact source projected through six public surfaces, with petgraph-specific non-derivable contracts (swap-remove index remapping on Graph::remove_node, StableGraph hole semantics and index reuse, GraphMap key-based identity, most-recently-added-first neighbor order, algorithm return shapes and error types) — a rule-engine-shaped reconstruction target that resists textbook pattern-matching at the contract level.
risks: graph algorithms themselves are high-saturation textbook material (mitigation: oracle weight on container/index/traversal contracts and cross-view agreement, checker-style validation for orders with multiple correct answers); large repo (mitigated by scope_plan); v0.8 sealed-trait changes are recent
scope_plan: target_subdomain = core containers (Graph, StableGraph, GraphMap) + index/removal contract + traversal visitors + bounded algo set (connected_components, is_cyclic_directed, has_path_connecting, toposort, kosaraju_scc, tarjan_scc, condensation, dijkstra, astar, bellman_ford, min_spanning_tree/FromElements) + Direction/prelude surface; matrix_graph/csr/adj/acyclic/graph6/dot/isomorphism/matching/flows/page_rank/serde/rayon/quickcheck scoped out; expected_oracle_max = 130

Difficulty shapes (selection rationale): equivalence judgement (toposort/SCC results validated as *a* correct order, not *the* order); language-rule reimplementation flavor in the swap-remove index remap and StableGraph vacancy reuse; integration tests spanning >=3 projections (mutate container -> traverse via adapter -> algorithm result -> container state agreement).
