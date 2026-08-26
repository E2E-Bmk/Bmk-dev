package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.Graphs;
import org.jgrapht.alg.interfaces.ShortestPathAlgorithm;
import org.jgrapht.alg.shortestpath.BellmanFordShortestPath;
import org.jgrapht.alg.shortestpath.DijkstraShortestPath;
import org.jgrapht.alg.shortestpath.NegativeCycleDetectedException;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.jgrapht.graph.SimpleDirectedWeightedGraph;
import org.jgrapht.graph.SimpleWeightedGraph;
import org.junit.jupiter.api.Test;

/** Dijkstra and Bellman-Ford single-source shortest paths. */
class ShortestPathAtomicTest {

    private static Graph<String, DefaultWeightedEdge> weighted() {
        Graph<String, DefaultWeightedEdge> g = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("s", "t", "u", "v"));
        g.setEdgeWeight(g.addEdge("s", "t"), 4.0);
        g.setEdgeWeight(g.addEdge("s", "u"), 1.0);
        g.setEdgeWeight(g.addEdge("u", "t"), 2.0);
        g.setEdgeWeight(g.addEdge("t", "v"), 3.0);
        return g;
    }

    /**
     * Verifies: Shortest Paths — getPath returns the minimum-weight path with
     * its vertices, weight, and edge count.
     */
    @Test
    void dijkstraFindsMinimumWeightPath() {
        DijkstraShortestPath<String, DefaultWeightedEdge> alg =
                new DijkstraShortestPath<>(weighted());
        GraphPath<String, DefaultWeightedEdge> path = alg.getPath("s", "v");
        assertEquals(6.0, path.getWeight());
        assertEquals(List.of("s", "u", "t", "v"), path.getVertexList());
        assertEquals(3, path.getLength());
        assertEquals("s", path.getStartVertex());
        assertEquals("v", path.getEndVertex());
    }

    /**
     * Verifies: Shortest Paths — an unreachable sink yields a null path.
     */
    @Test
    void dijkstraUnreachableYieldsNull() {
        Graph<String, DefaultWeightedEdge> g = weighted();
        g.addVertex("iso");
        assertNull(new DijkstraShortestPath<>(g).getPath("s", "iso"));
    }

    /**
     * Verifies: Shortest Paths — the query getPath(v, v) is the empty path at
     * v: weight 0.0, length 0, vertex list [v], empty edge list.
     */
    @Test
    void dijkstraSelfQueryIsEmptyPath() {
        GraphPath<String, DefaultWeightedEdge> path =
                new DijkstraShortestPath<>(weighted()).getPath("s", "s");
        assertEquals(0.0, path.getWeight());
        assertEquals(0, path.getLength());
        assertEquals(List.of("s"), path.getVertexList());
        assertEquals(0, path.getEdgeList().size());
    }

    /**
     * Verifies: Shortest Paths — getPaths answers per-sink queries; an
     * unreachable sink reports infinite weight and a null path.
     */
    @Test
    void singleSourcePathsAnswersPerSink() {
        Graph<String, DefaultWeightedEdge> g = weighted();
        g.addVertex("iso");
        ShortestPathAlgorithm.SingleSourcePaths<String, DefaultWeightedEdge> paths =
                new DijkstraShortestPath<>(g).getPaths("s");
        assertEquals(3.0, paths.getWeight("t"));
        assertEquals(Double.POSITIVE_INFINITY, paths.getWeight("iso"));
        assertNull(paths.getPath("iso"));
        assertEquals(List.of("s", "u", "t"), paths.getPath("t").getVertexList());
    }

    /**
     * Verifies: Error Semantics — Dijkstra raises IllegalArgumentException on
     * a negative edge weight.
     */
    @Test
    void dijkstraNegativeWeightRaises() {
        Graph<String, DefaultWeightedEdge> g =
                new SimpleDirectedWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("n1", "n2"));
        g.setEdgeWeight(g.addEdge("n1", "n2"), -2.0);
        DijkstraShortestPath<String, DefaultWeightedEdge> alg = new DijkstraShortestPath<>(g);
        assertThrows(IllegalArgumentException.class, () -> alg.getPath("n1", "n2"));
    }

    /**
     * Verifies: Error Semantics — Dijkstra getPath raises
     * IllegalArgumentException when the source or sink is absent.
     */
    @Test
    void dijkstraMissingEndpointRaises() {
        DijkstraShortestPath<String, DefaultWeightedEdge> alg =
                new DijkstraShortestPath<>(weighted());
        assertThrows(IllegalArgumentException.class, () -> alg.getPath("nope", "t"));
        assertThrows(IllegalArgumentException.class, () -> alg.getPath("s", "nope"));
    }

    /**
     * Verifies: Shortest Paths — the static findPathBetween convenience
     * answers a one-shot single-pair query.
     */
    @Test
    void staticFindPathBetween() {
        GraphPath<String, DefaultWeightedEdge> path =
                DijkstraShortestPath.findPathBetween(weighted(), "s", "t");
        assertEquals(3.0, path.getWeight());
    }

    /**
     * Verifies: Shortest Paths — in an undirected graph each edge is
     * traversable in both directions.
     */
    @Test
    void undirectedEdgesTraversableBothWays() {
        GraphPath<String, DefaultWeightedEdge> path =
                new DijkstraShortestPath<>(weighted()).getPath("v", "s");
        assertEquals(6.0, path.getWeight());
        assertEquals(List.of("v", "t", "u", "s"), path.getVertexList());
    }

    /**
     * Verifies: Shortest Paths — Bellman-Ford admits negative edge weights
     * and finds the minimum-weight path.
     */
    @Test
    void bellmanFordHandlesNegativeWeights() {
        Graph<String, DefaultWeightedEdge> g =
                new SimpleDirectedWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("b1", "b2", "b3"));
        g.setEdgeWeight(g.addEdge("b1", "b2"), 5.0);
        g.setEdgeWeight(g.addEdge("b2", "b3"), -3.0);
        g.setEdgeWeight(g.addEdge("b1", "b3"), 4.0);
        GraphPath<String, DefaultWeightedEdge> path =
                new BellmanFordShortestPath<>(g).getPath("b1", "b3");
        assertEquals(2.0, path.getWeight());
        assertEquals(List.of("b1", "b2", "b3"), path.getVertexList());
    }

    /**
     * Verifies: Error Semantics — Bellman-Ford raises
     * NegativeCycleDetectedException on a reachable negative-weight cycle.
     */
    @Test
    void bellmanFordNegativeCycleRaises() {
        Graph<String, DefaultWeightedEdge> g =
                new SimpleDirectedWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("c1", "c2", "c3"));
        g.setEdgeWeight(g.addEdge("c1", "c2"), 1.0);
        g.setEdgeWeight(g.addEdge("c2", "c3"), -5.0);
        g.setEdgeWeight(g.addEdge("c3", "c2"), 2.0);
        BellmanFordShortestPath<String, DefaultWeightedEdge> alg =
                new BellmanFordShortestPath<>(g);
        assertThrows(NegativeCycleDetectedException.class, () -> alg.getPath("c1", "c3"));
    }

    /**
     * Verifies: Shortest Paths — Bellman-Ford yields null for an unreachable
     * sink, as for Dijkstra.
     */
    @Test
    void bellmanFordUnreachableYieldsNull() {
        Graph<String, DefaultWeightedEdge> g =
                new SimpleDirectedWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("b1", "b2"));
        assertNull(new BellmanFordShortestPath<>(g).getPath("b1", "b2"));
    }

    /**
     * Verifies: Shortest Paths — a GraphPath reports the graph it lives in.
     */
    @Test
    void pathReportsItsGraph() {
        Graph<String, DefaultWeightedEdge> g = weighted();
        GraphPath<String, DefaultWeightedEdge> path =
                new DijkstraShortestPath<>(g).getPath("s", "t");
        assertTrue(path.getGraph() == g);
    }
}
