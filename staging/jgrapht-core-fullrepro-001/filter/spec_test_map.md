# Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| atomic::ConnectivityAtomicTest::isConnectedReportsSingleComponent | atomic | Connectivity | covered | Covers public behavior for `isConnectedReportsSingleComponent`. |
| atomic::ConnectivityAtomicTest::connectedSetsListsComponents | atomic | Connectivity | covered | Covers public behavior for `connectedSetsListsComponents`. |
| atomic::ConnectivityAtomicTest::connectedSetOfFindsComponent | atomic | Connectivity | covered | Covers public behavior for `connectedSetOfFindsComponent`. |
| atomic::ConnectivityAtomicTest::pathExistsReportsCoMembership | atomic | Connectivity | covered | Covers public behavior for `pathExistsReportsCoMembership`. |
| atomic::ConnectivityAtomicTest::degenerateGraphsConnectivity | atomic | Connectivity | covered | Covers public behavior for `degenerateGraphsConnectivity`. |
| atomic::ConnectivityAtomicTest::directedGraphUsesWeakConnectivity | atomic | Connectivity | covered | Covers public behavior for `directedGraphUsesWeakConnectivity`. |
| atomic::GraphMutationAtomicTest::addVertexReportsInsertion | atomic | Graph Structure and Mutation | covered | Covers public behavior for `addVertexReportsInsertion`. |
| atomic::GraphMutationAtomicTest::addEdgeReturnsNewEdge | atomic | Graph Structure and Mutation | covered | Covers public behavior for `addEdgeReturnsNewEdge`. |
| atomic::GraphMutationAtomicTest::addEdgeMissingVertexRaises | atomic | Graph Structure and Mutation | covered | Covers public behavior for `addEdgeMissingVertexRaises`. |
| atomic::GraphMutationAtomicTest::addEdgeNullVertexRaises | atomic | Graph Structure and Mutation | covered | Covers public behavior for `addEdgeNullVertexRaises`. |
| atomic::GraphMutationAtomicTest::getEdgeUndirectedIgnoresOrder | atomic | Graph Structure and Mutation | covered | Covers public behavior for `getEdgeUndirectedIgnoresOrder`. |
| atomic::GraphMutationAtomicTest::containsEdgeReportsConnection | atomic | Graph Structure and Mutation | covered | Covers public behavior for `containsEdgeReportsConnection`. |
| atomic::GraphMutationAtomicTest::removeEdgeByPairReturnsEdge | atomic | Graph Structure and Mutation | covered | Covers public behavior for `removeEdgeByPairReturnsEdge`. |
| atomic::GraphMutationAtomicTest::removeEdgeByObjectReportsChange | atomic | Graph Structure and Mutation | covered | Covers public behavior for `removeEdgeByObjectReportsChange`. |
| atomic::GraphMutationAtomicTest::removeVertexRemovesIncidentEdges | atomic | Graph Structure and Mutation | covered | Covers public behavior for `removeVertexRemovesIncidentEdges`. |
| atomic::GraphMutationAtomicTest::vertexSetIteratesInInsertionOrder | atomic | Graph Structure and Mutation | covered | Covers public behavior for `vertexSetIteratesInInsertionOrder`. |
| atomic::GraphMutationAtomicTest::edgeSetIteratesInInsertionOrder | atomic | Graph Structure and Mutation | covered | Covers public behavior for `edgeSetIteratesInInsertionOrder`. |
| atomic::GraphMutationAtomicTest::edgeEndpointsArePreserved | atomic | Graph Structure and Mutation | covered | Covers public behavior for `edgeEndpointsArePreserved`. |
| atomic::GraphMutationAtomicTest::defaultEdgeRendersEndpoints | atomic | Graph Classes and Structural Rules | covered | Covers public behavior for `defaultEdgeRendersEndpoints`. |
| atomic::GraphsUtilityAtomicTest::addEdgeWithVerticesInsertsEndpoints | atomic | Graph Structure and Mutation | covered | Covers public behavior for `addEdgeWithVerticesInsertsEndpoints`. |
| atomic::GraphsUtilityAtomicTest::addAllVerticesReportsChange | atomic | Graph Structure and Mutation | covered | Covers public behavior for `addAllVerticesReportsChange`. |
| atomic::GraphsUtilityAtomicTest::neighborListOfListsAdjacent | atomic | Graph Structure and Mutation | covered | Covers public behavior for `neighborListOfListsAdjacent`. |
| atomic::GraphsUtilityAtomicTest::successorAndPredecessorLists | atomic | Graph Structure and Mutation | covered | Covers public behavior for `successorAndPredecessorLists`. |
| atomic::ShortestPathAtomicTest::dijkstraFindsMinimumWeightPath | atomic | Shortest Paths | covered | Covers public behavior for `dijkstraFindsMinimumWeightPath`. |
| atomic::ShortestPathAtomicTest::dijkstraUnreachableYieldsNull | atomic | Shortest Paths | covered | Covers public behavior for `dijkstraUnreachableYieldsNull`. |
| atomic::ShortestPathAtomicTest::dijkstraSelfQueryIsEmptyPath | atomic | Shortest Paths | covered | Covers public behavior for `dijkstraSelfQueryIsEmptyPath`. |
| atomic::ShortestPathAtomicTest::singleSourcePathsAnswersPerSink | atomic | Shortest Paths | covered | Covers public behavior for `singleSourcePathsAnswersPerSink`. |
| atomic::ShortestPathAtomicTest::dijkstraNegativeWeightRaises | atomic | Error Semantics | covered | Covers public behavior for `dijkstraNegativeWeightRaises`. |
| atomic::ShortestPathAtomicTest::dijkstraMissingEndpointRaises | atomic | Error Semantics | covered | Covers public behavior for `dijkstraMissingEndpointRaises`. |
| atomic::ShortestPathAtomicTest::staticFindPathBetween | atomic | Shortest Paths | covered | Covers public behavior for `staticFindPathBetween`. |
| atomic::ShortestPathAtomicTest::undirectedEdgesTraversableBothWays | atomic | Shortest Paths | covered | Covers public behavior for `undirectedEdgesTraversableBothWays`. |
| atomic::ShortestPathAtomicTest::bellmanFordHandlesNegativeWeights | atomic | Shortest Paths | covered | Covers public behavior for `bellmanFordHandlesNegativeWeights`. |
| atomic::ShortestPathAtomicTest::bellmanFordNegativeCycleRaises | atomic | Error Semantics | covered | Covers public behavior for `bellmanFordNegativeCycleRaises`. |
| atomic::ShortestPathAtomicTest::bellmanFordUnreachableYieldsNull | atomic | Shortest Paths | covered | Covers public behavior for `bellmanFordUnreachableYieldsNull`. |
| atomic::ShortestPathAtomicTest::pathReportsItsGraph | atomic | Shortest Paths | covered | Covers public behavior for `pathReportsItsGraph`. |
| atomic::structural::undirectedClassesDeclareMatrixRow | atomic | (unmapped) | covered | Covers public behavior for `undirectedClassesDeclareMatrixRow`. |
| atomic::structural::directedClassesDeclareMatrixRow | atomic | (unmapped) | covered | Covers public behavior for `directedClassesDeclareMatrixRow`. |
| atomic::structural::selfLoopRaisesWhereForbidden | atomic | (unmapped) | covered | Covers public behavior for `selfLoopRaisesWhereForbidden`. |
| atomic::structural::selfLoopCreatedWherePermitted | atomic | (unmapped) | covered | Covers public behavior for `selfLoopCreatedWherePermitted`. |
| atomic::structural::parallelEdgeReturnsNullWhereForbidden | atomic | (unmapped) | covered | Covers public behavior for `parallelEdgeReturnsNullWhereForbidden`. |
| atomic::structural::parallelEdgesAccumulateWherePermitted | atomic | (unmapped) | covered | Covers public behavior for `parallelEdgesAccumulateWherePermitted`. |
| atomic::structural::undirectedMultiplicityIgnoresOrder | atomic | (unmapped) | covered | Covers public behavior for `undirectedMultiplicityIgnoresOrder`. |
| atomic::structural::directedMultiplicityDistinguishesOrder | atomic | (unmapped) | covered | Covers public behavior for `directedMultiplicityDistinguishesOrder`. |
| atomic::structural::weightedClassesMirrorStructure | atomic | (unmapped) | covered | Covers public behavior for `weightedClassesMirrorStructure`. |
| atomic::TraversalAtomicTest::breadthFirstLevelOrder | atomic | Traversal Iterators | covered | Covers public behavior for `breadthFirstLevelOrder`. |
| atomic::TraversalAtomicTest::breadthFirstDepthAndParent | atomic | Traversal Iterators | covered | Covers public behavior for `breadthFirstDepthAndParent`. |
| atomic::TraversalAtomicTest::breadthFirstWholeGraph | atomic | Traversal Iterators | covered | Covers public behavior for `breadthFirstWholeGraph`. |
| atomic::TraversalAtomicTest::missingStartVertexRaises | atomic | Error Semantics | covered | Covers public behavior for `missingStartVertexRaises`. |
| atomic::TraversalAtomicTest::depthFirstLifoOrder | atomic | Traversal Iterators | covered | Covers public behavior for `depthFirstLifoOrder`. |
| atomic::TraversalAtomicTest::undirectedTraversalFollowsBothDirections | atomic | Traversal Iterators | covered | Covers public behavior for `undirectedTraversalFollowsBothDirections`. |
| atomic::TraversalAtomicTest::topologicalOrderRespectsEdges | atomic | Traversal Iterators | covered | Covers public behavior for `topologicalOrderRespectsEdges`. |
| atomic::TraversalAtomicTest::topologicalUndirectedRaises | atomic | Error Semantics | covered | Covers public behavior for `topologicalUndirectedRaises`. |
| atomic::TraversalAtomicTest::topologicalCycleRaisesDuringIteration | atomic | Error Semantics | covered | Covers public behavior for `topologicalCycleRaisesDuringIteration`. |
| atomic::ViewsAtomicTest::unmodifiableMutatorsRaise | atomic | Graph Views | covered | Covers public behavior for `unmodifiableMutatorsRaise`. |
| atomic::ViewsAtomicTest::unmodifiableReadsBackingLive | atomic | Graph Views | covered | Covers public behavior for `unmodifiableReadsBackingLive`. |
| atomic::ViewsAtomicTest::unmodifiableTypeReportsUnmodifiable | atomic | Graph Views | covered | Covers public behavior for `unmodifiableTypeReportsUnmodifiable`. |
| atomic::ViewsAtomicTest::reversedViewSwapsEndpoints | atomic | Graph Views | covered | Covers public behavior for `reversedViewSwapsEndpoints`. |
| atomic::ViewsAtomicTest::reversedViewSwapsIncidence | atomic | Graph Views | covered | Covers public behavior for `reversedViewSwapsIncidence`. |
| atomic::ViewsAtomicTest::reversedViewWritesThrough | atomic | Graph Views | covered | Covers public behavior for `reversedViewWritesThrough`. |
| atomic::ViewsAtomicTest::subgraphIsInducedAtConstruction | atomic | Graph Views | covered | Covers public behavior for `subgraphIsInducedAtConstruction`. |
| atomic::ViewsAtomicTest::subgraphNullEdgeSubsetIsInduced | atomic | Graph Views | covered | Covers public behavior for `subgraphNullEdgeSubsetIsInduced`. |
| atomic::ViewsAtomicTest::subgraphTracksOwnWindow | atomic | Graph Views | covered | Covers public behavior for `subgraphTracksOwnWindow`. |
| atomic::ViewsAtomicTest::subgraphRemovalIsLocal | atomic | Graph Views | covered | Covers public behavior for `subgraphRemovalIsLocal`. |
| atomic::ViewsAtomicTest::maskHidesByPredicate | atomic | Graph Views | covered | Covers public behavior for `maskHidesByPredicate`. |
| atomic::ViewsAtomicTest::maskIsLiveAndReadOnly | atomic | Graph Views | covered | Covers public behavior for `maskIsLiveAndReadOnly`. |
| atomic::WeightsAndDegreesAtomicTest::defaultWeightIsOne | atomic | Graph Structure and Mutation | covered | Covers public behavior for `defaultWeightIsOne`. |
| atomic::WeightsAndDegreesAtomicTest::setEdgeWeightAssigns | atomic | Graph Structure and Mutation | covered | Covers public behavior for `setEdgeWeightAssigns`. |
| atomic::WeightsAndDegreesAtomicTest::setEdgeWeightByPairAssigns | atomic | Graph Structure and Mutation | covered | Covers public behavior for `setEdgeWeightByPairAssigns`. |
| atomic::WeightsAndDegreesAtomicTest::setEdgeWeightUnweightedRaises | atomic | Error Semantics | covered | Covers public behavior for `setEdgeWeightUnweightedRaises`. |
| atomic::WeightsAndDegreesAtomicTest::directedDegreesSplitByDirection | atomic | Graph Structure and Mutation | covered | Covers public behavior for `directedDegreesSplitByDirection`. |
| atomic::WeightsAndDegreesAtomicTest::selfLoopCountsTwiceInDegree | atomic | Graph Structure and Mutation | covered | Covers public behavior for `selfLoopCountsTwiceInDegree`. |
| integration::ConnectivityAlgebraIntegrationTest::pathExistsAgreesWithDijkstraReachability | integration | Cross-View Invariants | covered | Covers public behavior for `pathExistsAgreesWithDijkstraReachability`. |
| integration::ConnectivityAlgebraIntegrationTest::connectedSetsPartitionVertexSet | integration | Cross-View Invariants | covered | Covers public behavior for `connectedSetsPartitionVertexSet`. |
| integration::ConnectivityAlgebraIntegrationTest::bridgeEdgeMergesComponents | integration | Cross-View Invariants | covered | Covers public behavior for `bridgeEdgeMergesComponents`. |
| integration::ConnectivityAlgebraIntegrationTest::cutVertexRemovalSplitsComponent | integration | Cross-View Invariants | covered | Covers public behavior for `cutVertexRemovalSplitsComponent`. |
| integration::ConnectivityAlgebraIntegrationTest::subgraphConnectivityIsWindowLocal | integration | Cross-View Invariants | covered | Covers public behavior for `subgraphConnectivityIsWindowLocal`. |
| integration::ConnectivityAlgebraIntegrationTest::maskedBridgeDisconnectsViewOnly | integration | Cross-View Invariants | covered | Covers public behavior for `maskedBridgeDisconnectsViewOnly`. |
| integration::ConnectivityAlgebraIntegrationTest::weakConnectivityIgnoresDirectionPathsRespectIt | integration | Cross-View Invariants | covered | Covers public behavior for `weakConnectivityIgnoresDirectionPathsRespectIt`. |
| integration::ConnectivityAlgebraIntegrationTest::wholeGraphTraversalCoversAllComponents | integration | Cross-View Invariants | covered | Covers public behavior for `wholeGraphTraversalCoversAllComponents`. |
| integration::TraversalPathIntegrationTest::bfsDepthEqualsUnweightedShortestPathLength | integration | Cross-View Invariants | covered | Covers public behavior for `bfsDepthEqualsUnweightedShortestPathLength`. |
| integration::TraversalPathIntegrationTest::bfsParentChainLengthMatchesDepth | integration | Cross-View Invariants | covered | Covers public behavior for `bfsParentChainLengthMatchesDepth`. |
| integration::TraversalPathIntegrationTest::graphPathInternalConsistency | integration | Cross-View Invariants | covered | Covers public behavior for `graphPathInternalConsistency`. |
| integration::TraversalPathIntegrationTest::dijkstraAndBellmanFordAgreeOnNonNegative | integration | Cross-View Invariants | covered | Covers public behavior for `dijkstraAndBellmanFordAgreeOnNonNegative`. |
| integration::TraversalPathIntegrationTest::singleSourceAndSinglePairAgree | integration | Cross-View Invariants | covered | Covers public behavior for `singleSourceAndSinglePairAgree`. |
| integration::TraversalPathIntegrationTest::bfsAndDfsVisitSameVertexSet | integration | Cross-View Invariants | covered | Covers public behavior for `bfsAndDfsVisitSameVertexSet`. |
| integration::TraversalPathIntegrationTest::topologicalOrderRespectsEveryEdge | integration | Cross-View Invariants | covered | Covers public behavior for `topologicalOrderRespectsEveryEdge`. |
| integration::TraversalPathIntegrationTest::bellmanFordAgreesWithBfsOnUnweighted | integration | Cross-View Invariants | covered | Covers public behavior for `bellmanFordAgreesWithBfsOnUnweighted`. |
| integration::TraversalPathIntegrationTest::mutationVisibleToTraversalAndPaths | integration | Cross-View Invariants | covered | Covers public behavior for `mutationVisibleToTraversalAndPaths`. |
| integration::ViewConsistencyIntegrationTest::unmodifiableAgreesAcrossMutations | integration | Cross-View Invariants | covered | Covers public behavior for `unmodifiableAgreesAcrossMutations`. |
| integration::ViewConsistencyIntegrationTest::reversedViewMirrorsAllDirectionalQueries | integration | Cross-View Invariants | covered | Covers public behavior for `reversedViewMirrorsAllDirectionalQueries`. |
| integration::ViewConsistencyIntegrationTest::typeAndSelfLoopBehaviorAgree | integration | Cross-View Invariants | covered | Covers public behavior for `typeAndSelfLoopBehaviorAgree`. |
| integration::ViewConsistencyIntegrationTest::typeAndMultiplicityBehaviorAgree | integration | Cross-View Invariants | covered | Covers public behavior for `typeAndMultiplicityBehaviorAgree`. |
| integration::ViewConsistencyIntegrationTest::degreeSumIsTwiceEdgeCount | integration | Cross-View Invariants | covered | Covers public behavior for `degreeSumIsTwiceEdgeCount`. |
| integration::ViewConsistencyIntegrationTest::vertexRemovalPropagatesToLiveViews | integration | Cross-View Invariants | covered | Covers public behavior for `vertexRemovalPropagatesToLiveViews`. |
| integration::ViewConsistencyIntegrationTest::subgraphInductionIsExact | integration | Cross-View Invariants | covered | Covers public behavior for `subgraphInductionIsExact`. |
| integration::ViewConsistencyIntegrationTest::unmodifiableComposesOverSubgraph | integration | Cross-View Invariants | covered | Covers public behavior for `unmodifiableComposesOverSubgraph`. |
| integration::ViewConsistencyIntegrationTest::maskAndSubgraphAgreeOnSurvivors | integration | Cross-View Invariants | covered | Covers public behavior for `maskAndSubgraphAgreeOnSurvivors`. |
