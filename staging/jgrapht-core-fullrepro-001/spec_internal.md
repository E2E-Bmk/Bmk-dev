<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — jgrapht-core-fullrepro-001

- task_id: jgrapht-core-fullrepro-001
- language: java
- repo: jgrapht/jgrapht (github)
- repo_commit: fe2d4cdfa42073eb1141e789844adc9c1fc8bf36 (tag jgrapht-1.5.2)
- maven_coordinates: org.jgrapht:jgrapht-core
- package root: org.jgrapht
- source boundary: Graph/GraphType/GraphPath/Graphs core surface; the eight
  unweighted structural classes plus three weighted classes; DefaultEdge /
  DefaultWeightedEdge; views AsUnmodifiableGraph / EdgeReversedGraph /
  AsSubgraph / MaskSubgraph; BreadthFirstIterator / DepthFirstIterator /
  TopologicalOrderIterator; DijkstraShortestPath / BellmanFordShortestPath /
  ShortestPathAlgorithm.SingleSourcePaths; ConnectivityInspector;
  NegativeCycleDetectedException / NotDirectedAcyclicGraphException.
  Excludes generators, isomorphism, matching/coloring/clique/flow/spanning/
  centrality algorithms, import/export, listenable/concurrent graphs,
  builders, strong connectivity (Non-Goals).
- spec basis: jgrapht.org user guide / javadoc public documentation and three
  empirical probe rounds against the pinned 1.5.2 artifact (probe programs
  under /tmp/probe during authoring): structural matrix admission behavior
  (loop -> IllegalArgumentException, parallel -> null), view liveness
  (AsSubgraph snapshot vs MaskSubgraph live), traversal orders under
  insertion-order determinism, shortest-path error paths, connectivity
  results including empty-graph isConnected()=false.
- spec_version: v1
- delta: initial version.
