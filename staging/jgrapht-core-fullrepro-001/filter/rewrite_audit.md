# Rewrite Audit — jgrapht-core-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~2070 test functions across ~500 files,
dominated by algorithm families outside this spec's scope) was used only as a
behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 1.5.2 artifact before being pinned:

- 71 atomic tests across eight files covering Graph mutation and query
  semantics (vertex/edge insertion and removal returns, endpoint lookups,
  insertion-order iteration), the eight-class structural matrix and its two
  distinct refusal behaviors (self-loop raises, duplicate pair returns null),
  weights and the DEFAULT_EDGE_WEIGHT constant, degree accounting including
  self-loop double counting, the Graphs bulk helpers, the four views
  (unmodifiable, edge-reversed, subgraph window, masked) with their liveness
  and write-through rules, breadth-first / depth-first / topological
  iteration with depth and parent reporting, Dijkstra and Bellman-Ford
  shortest paths with their declared error paths, and weak-connectivity
  reporting including the empty-graph and single-vertex cases.
- 24 integration tests across three files covering view/backing agreement
  under mutation sequences, type-declaration/admission agreement across the
  full class matrix, degree-sum identities, BFS-depth versus unweighted
  shortest-path agreement, GraphPath internal consistency, Dijkstra versus
  Bellman-Ford agreement, topological order validity on both a DAG and its
  reversed view, and connectivity agreement with reachability across
  subgraphs, masks, and bridge/cut mutations.

Assertions pin only behavior stated in the spec: the structural matrix, the
documented refusal semantics, insertion-order determinism, traversal
disciplines (level order, LIFO), declared exception classes
(`IllegalArgumentException`, `NullPointerException`,
`UnsupportedOperationException`, `NotDirectedAcyclicGraphException`,
`NegativeCycleDetectedException`), and the documented null/infinity returns.

Every test imports only `org.jgrapht` symbols listed in the spec's Public
Interface (enforced by the import lint; see `lint_result.txt`).
