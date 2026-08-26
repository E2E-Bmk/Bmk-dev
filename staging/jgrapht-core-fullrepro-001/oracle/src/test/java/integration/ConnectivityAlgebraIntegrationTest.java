package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.alg.connectivity.ConnectivityInspector;
import org.jgrapht.alg.shortestpath.DijkstraShortestPath;
import org.jgrapht.graph.AsSubgraph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.MaskSubgraph;
import org.jgrapht.graph.SimpleGraph;
import org.jgrapht.traverse.BreadthFirstIterator;
import org.junit.jupiter.api.Test;
import support.GraphsFixtures;

/** Connectivity agreement with paths, views, and mutation. */
class ConnectivityAlgebraIntegrationTest {

    private static Graph<String, DefaultEdge> twoIslands() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("a", "b", "c", "x", "y"));
        g.addEdge("a", "b");
        g.addEdge("b", "c");
        g.addEdge("x", "y");
        return g;
    }

    /**
     * Verifies: Cross-View Invariants — pathExists is true exactly when
     * Dijkstra finds a non-null path over the same undirected graph, for
     * every vertex pair.
     * Depends-On: pathExistsReportsCoMembership, dijkstraUnreachableYieldsNull.
     */
    @Test
    void pathExistsAgreesWithDijkstraReachability() {
        Graph<String, DefaultEdge> g = twoIslands();
        ConnectivityInspector<String, DefaultEdge> ci = new ConnectivityInspector<>(g);
        DijkstraShortestPath<String, DefaultEdge> alg = new DijkstraShortestPath<>(g);
        for (String u : g.vertexSet()) {
            for (String v : g.vertexSet()) {
                assertEquals(ci.pathExists(u, v), alg.getPath(u, v) != null);
            }
        }
    }

    /**
     * Verifies: Cross-View Invariants — connectedSets partitions the vertex
     * set: the union is vertexSet and the sets are pairwise disjoint.
     * Depends-On: connectedSetsListsComponents.
     */
    @Test
    void connectedSetsPartitionVertexSet() {
        Graph<String, DefaultEdge> g = twoIslands();
        List<Set<String>> sets = new ConnectivityInspector<>(g).connectedSets();
        Set<String> union = new HashSet<>();
        int total = 0;
        for (Set<String> component : sets) {
            union.addAll(component);
            total += component.size();
        }
        assertEquals(g.vertexSet(), union);
        assertEquals(g.vertexSet().size(), total);
    }

    /**
     * Verifies: Cross-View Invariants — adding a bridge edge merges two
     * components as observed by a fresh inspector.
     * Depends-On: isConnectedReportsSingleComponent, addEdgeReturnsNewEdge.
     */
    @Test
    void bridgeEdgeMergesComponents() {
        Graph<String, DefaultEdge> g = twoIslands();
        assertFalse(new ConnectivityInspector<>(g).isConnected());
        g.addEdge("c", "x");
        ConnectivityInspector<String, DefaultEdge> after = new ConnectivityInspector<>(g);
        assertTrue(after.isConnected());
        assertEquals(1, after.connectedSets().size());
        assertTrue(after.pathExists("a", "y"));
    }

    /**
     * Verifies: Cross-View Invariants — removing a cut vertex splits a
     * component as observed by a fresh inspector.
     * Depends-On: removeVertexRemovesIncidentEdges, connectedSetOfFindsComponent.
     */
    @Test
    void cutVertexRemovalSplitsComponent() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("l", "mid", "r"));
        g.addEdge("l", "mid");
        g.addEdge("mid", "r");
        assertTrue(new ConnectivityInspector<>(g).isConnected());
        g.removeVertex("mid");
        ConnectivityInspector<String, DefaultEdge> after = new ConnectivityInspector<>(g);
        assertFalse(after.isConnected());
        assertEquals(Set.of("l"), after.connectedSetOf("l"));
        assertEquals(Set.of("r"), after.connectedSetOf("r"));
    }

    /**
     * Verifies: Cross-View Invariants — connectivity computed over an induced
     * subgraph reflects only the window's structure, not the backing graph's.
     * Depends-On: subgraphIsInducedAtConstruction, isConnectedReportsSingleComponent.
     */
    @Test
    void subgraphConnectivityIsWindowLocal() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("a", "b", "c", "d"));
        g.addEdge("a", "b");
        g.addEdge("b", "c");
        g.addEdge("c", "d");
        assertTrue(new ConnectivityInspector<>(g).isConnected());
        Graph<String, DefaultEdge> sub =
                new AsSubgraph<>(g, new HashSet<>(Arrays.asList("a", "b", "d")));
        ConnectivityInspector<String, DefaultEdge> sci = new ConnectivityInspector<>(sub);
        assertFalse(sci.isConnected());
        assertTrue(sci.pathExists("a", "b"));
        assertFalse(sci.pathExists("a", "d"));
    }

    /**
     * Verifies: Cross-View Invariants — masking a bridge edge disconnects the
     * masked view while the backing graph stays connected.
     * Depends-On: maskHidesByPredicate, isConnectedReportsSingleComponent.
     */
    @Test
    void maskedBridgeDisconnectsViewOnly() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("a", "b", "c"));
        g.addEdge("a", "b");
        DefaultEdge bridge = g.addEdge("b", "c");
        Graph<String, DefaultEdge> masked = new MaskSubgraph<>(g, v -> false, e -> e == bridge);
        assertTrue(new ConnectivityInspector<>(g).isConnected());
        assertFalse(new ConnectivityInspector<>(masked).isConnected());
    }

    /**
     * Verifies: Cross-View Invariants — a one-way directed graph is weakly
     * connected while Dijkstra respects direction, so pathExists and directed
     * reachability diverge exactly on direction.
     * Depends-On: directedGraphUsesWeakConnectivity, dijkstraUnreachableYieldsNull.
     */
    @Test
    void weakConnectivityIgnoresDirectionPathsRespectIt() {
        Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("d1", "d2"));
        g.addEdge("d1", "d2");
        ConnectivityInspector<String, DefaultEdge> ci = new ConnectivityInspector<>(g);
        DijkstraShortestPath<String, DefaultEdge> alg = new DijkstraShortestPath<>(g);
        assertTrue(ci.pathExists("d2", "d1"));
        assertTrue(alg.getPath("d1", "d2") != null);
        assertTrue(alg.getPath("d2", "d1") == null);
    }

    /**
     * Verifies: Cross-View Invariants — the whole-graph breadth-first
     * traversal visits every component that connectedSets reports.
     * Depends-On: breadthFirstWholeGraph, connectedSetsListsComponents.
     */
    @Test
    void wholeGraphTraversalCoversAllComponents() {
        Graph<String, DefaultEdge> g = twoIslands();
        List<String> visited = GraphsFixtures.drain(new BreadthFirstIterator<>(g));
        assertEquals(g.vertexSet(), new HashSet<>(visited));
        assertEquals(g.vertexSet().size(), visited.size());
    }
}
