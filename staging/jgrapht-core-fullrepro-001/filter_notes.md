repo: jgrapht/jgrapht
source_path: /tmp/refs (shallow clone at tag jgrapht-1.5.2)
commit: fe2d4cdfa42073eb1141e789844adc9c1fc8bf36
src_loc: 89827
test_functions: 2070
test_files: ~500 files under jgrapht-core/src/test/java
dominant_test_styles: unit + algorithm result checks
public_docs: https://jgrapht.org/guide/UserOverview, javadoc
core_fact_source: graph structure (vertex/edge sets, weights, directedness) shared by builders, views, traversals and algorithms
derived_views: graph mutation API; graph views (unmodifiable, edge-reversed, subgraph, masked); iterators (BFS/DFS/topological); shortest-path algorithms returning GraphPath; connectivity inspectors; GraphType introspection
external_deps: jheaps (runtime dep of target)
test_import_audit: clean ~10% — most core tests use public API; volume too large, Track B generated-only oracle planned
docs_test_alignment: aligned — user guide + javadoc document graph contracts (IllegalArgumentException on missing vertices, loops/multi-edge rules per graph class)
contamination_note: jgrapht@1.5.2, released 2023-07, relative to training cutoff: before
decision: keep
reason: multi-component graph framework: one fact source (graph) with many public projections; strict structural rules per graph class (SimpleGraph vs Multigraph vs Pseudograph) resist stub implementations
risks: classic algorithms are public knowledge (Dijkstra); difficulty carried by per-class structural rules, views that write through, and iterator event contracts; scope excludes generators/isomorphism/flow
scope_plan: target_subdomain=core graph classes + views + BFS/DFS/topological iterators + Dijkstra/BellmanFord shortest paths + connectivity, expected_oracle_max=120
difficulty_shapes: equivalence judgements (view vs backing graph consistency); rule reimplementation (per-class edge admission rules); >=3 cooperating objects (graph, view, iterator, algorithm)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
