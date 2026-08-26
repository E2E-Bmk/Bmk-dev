package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.Graphs;
import org.jgrapht.alg.interfaces.ShortestPathAlgorithm;
import org.jgrapht.alg.shortestpath.BellmanFordShortestPath;
import org.jgrapht.alg.shortestpath.DijkstraShortestPath;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.jgrapht.graph.EdgeReversedGraph;
import org.jgrapht.graph.SimpleWeightedGraph;
import org.jgrapht.traverse.BreadthFirstIterator;
import org.jgrapht.traverse.DepthFirstIterator;
import org.jgrapht.traverse.TopologicalOrderIterator;
import org.junit.jupiter.api.Test;
import support.GraphsFixtures;

/** Agreement between traversals, shortest paths, and path values. */
class TraversalPathIntegrationTest {

    private static Graph<String, DefaultEdge> dag() {
        Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("A", "B", "C", "D", "E"));
        g.addEdge("A", "B");
        g.addEdge("A", "C");
        g.addEdge("B", "D");
        g.addEdge("C", "D");
        g.addEdge("D", "E");
        return g;
    }

    /**
     * Verifies: Cross-View Invariants — breadth-first getDepth equals the
     * Dijkstra path length on an unweighted graph, for every reachable
     * vertex.
     * Depends-On: breadthFirstDepthAndParent, dijkstraFindsMinimumWeightPath.
     */
    @Test
    void bfsDepthEqualsUnweightedShortestPathLength() {
        Graph<String, DefaultEdge> g = dag();
        BreadthFirstIterator<String, DefaultEdge> it = new BreadthFirstIterator<>(g, "A");
        GraphsFixtures.drain(it);
        DijkstraShortestPath<String, DefaultEdge> alg = new DijkstraShortestPath<>(g);
        for (String v : g.vertexSet()) {
            GraphPath<String, DefaultEdge> path = alg.getPath("A", v);
            assertEquals(path.getLength(), it.getDepth(v));
        }
    }

    /**
     * Verifies: Cross-View Invariants — following getParent links from any
     * vertex back to the start produces a path of exactly getDepth edges.
     * Depends-On: breadthFirstDepthAndParent, breadthFirstLevelOrder.
     */
    @Test
    void bfsParentChainLengthMatchesDepth() {
        Graph<String, DefaultEdge> g = dag();
        BreadthFirstIterator<String, DefaultEdge> it = new BreadthFirstIterator<>(g, "A");
        GraphsFixtures.drain(it);
        for (String v : g.vertexSet()) {
            int hops = 0;
            String cursor = v;
            while (it.getParent(cursor) != null) {
                cursor = it.getParent(cursor);
                hops++;
            }
            assertEquals("A", cursor);
            assertEquals(it.getDepth(v), hops);
        }
    }

    /**
     * Verifies: Cross-View Invariants — a GraphPath is internally consistent:
     * length equals edge count, the vertex list frames start and end, and the
     * weight is the sum of edge weights.
     * Depends-On: dijkstraFindsMinimumWeightPath, setEdgeWeightAssigns.
     */
    @Test
    void graphPathInternalConsistency() {
        Graph<String, DefaultWeightedEdge> g = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("s", "t", "u", "v"));
        g.setEdgeWeight(g.addEdge("s", "t"), 4.0);
        g.setEdgeWeight(g.addEdge("s", "u"), 1.0);
        g.setEdgeWeight(g.addEdge("u", "t"), 2.0);
        g.setEdgeWeight(g.addEdge("t", "v"), 3.0);
        GraphPath<String, DefaultWeightedEdge> path =
                new DijkstraShortestPath<>(g).getPath("s", "v");
        List<DefaultWeightedEdge> edges = path.getEdgeList();
        assertEquals(edges.size(), path.getLength());
        assertEquals(path.getLength() + 1, path.getVertexList().size());
        assertEquals(path.getStartVertex(), path.getVertexList().get(0));
        assertEquals(path.getEndVertex(), path.getVertexList().get(path.getLength()));
        double sum = 0.0;
        for (DefaultWeightedEdge e : edges) {
            sum += g.getEdgeWeight(e);
        }
        assertEquals(sum, path.getWeight());
    }

    /**
     * Verifies: Cross-View Invariants — Dijkstra and Bellman-Ford agree on
     * every pair of a non-negative weighted graph.
     * Depends-On: dijkstraFindsMinimumWeightPath, bellmanFordHandlesNegativeWeights.
     */
    @Test
    void dijkstraAndBellmanFordAgreeOnNonNegative() {
        Graph<String, DefaultWeightedEdge> g = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("s", "t", "u", "v"));
        g.setEdgeWeight(g.addEdge("s", "t"), 4.0);
        g.setEdgeWeight(g.addEdge("s", "u"), 1.0);
        g.setEdgeWeight(g.addEdge("u", "t"), 2.0);
        g.setEdgeWeight(g.addEdge("t", "v"), 3.0);
        DijkstraShortestPath<String, DefaultWeightedEdge> dij = new DijkstraShortestPath<>(g);
        BellmanFordShortestPath<String, DefaultWeightedEdge> bf = new BellmanFordShortestPath<>(g);
        for (String a : g.vertexSet()) {
            for (String b : g.vertexSet()) {
                assertEquals(dij.getPath(a, b).getWeight(), bf.getPath(a, b).getWeight());
            }
        }
    }

    /**
     * Verifies: Cross-View Invariants — per-sink answers from getPaths agree
     * with the single-pair getPath answers.
     * Depends-On: singleSourcePathsAnswersPerSink, dijkstraFindsMinimumWeightPath.
     */
    @Test
    void singleSourceAndSinglePairAgree() {
        Graph<String, DefaultWeightedEdge> g = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("s", "t", "u", "v"));
        g.setEdgeWeight(g.addEdge("s", "t"), 4.0);
        g.setEdgeWeight(g.addEdge("s", "u"), 1.0);
        g.setEdgeWeight(g.addEdge("u", "t"), 2.0);
        g.setEdgeWeight(g.addEdge("t", "v"), 3.0);
        DijkstraShortestPath<String, DefaultWeightedEdge> alg = new DijkstraShortestPath<>(g);
        ShortestPathAlgorithm.SingleSourcePaths<String, DefaultWeightedEdge> paths =
                alg.getPaths("s");
        for (String sink : g.vertexSet()) {
            assertEquals(alg.getPath("s", sink).getWeight(), paths.getWeight(sink));
            assertEquals(alg.getPath("s", sink).getVertexList(),
                    paths.getPath(sink).getVertexList());
        }
    }

    /**
     * Verifies: Cross-View Invariants — breadth-first and depth-first visit
     * exactly the same vertex set from the same start, each vertex once.
     * Depends-On: breadthFirstLevelOrder, depthFirstLifoOrder.
     */
    @Test
    void bfsAndDfsVisitSameVertexSet() {
        Graph<String, DefaultEdge> g = dag();
        List<String> bfs = GraphsFixtures.drain(new BreadthFirstIterator<>(g, "A"));
        List<String> dfs = GraphsFixtures.drain(new DepthFirstIterator<>(g, "A"));
        assertEquals(bfs.size(), dfs.size());
        assertEquals(new HashSet<>(bfs), new HashSet<>(dfs));
        assertEquals(bfs.size(), new HashSet<>(bfs).size());
    }

    /**
     * Verifies: Cross-View Invariants — a topological order respects every
     * edge of the DAG, and remains valid over an edge-reversed reading with
     * the direction flipped.
     * Depends-On: topologicalOrderRespectsEdges, reversedViewSwapsEndpoints.
     */
    @Test
    void topologicalOrderRespectsEveryEdge() {
        Graph<String, DefaultEdge> g = dag();
        List<String> order = GraphsFixtures.drain(new TopologicalOrderIterator<>(g));
        for (DefaultEdge e : g.edgeSet()) {
            assertTrue(order.indexOf(g.getEdgeSource(e)) < order.indexOf(g.getEdgeTarget(e)));
        }
        Graph<String, DefaultEdge> rev = new EdgeReversedGraph<>(g);
        List<String> revOrder = GraphsFixtures.drain(new TopologicalOrderIterator<>(rev));
        for (DefaultEdge e : rev.edgeSet()) {
            assertTrue(revOrder.indexOf(rev.getEdgeSource(e))
                    < revOrder.indexOf(rev.getEdgeTarget(e)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — on an unweighted graph, where every
     * edge behaves as weight 1.0, the Bellman-Ford path weight equals the
     * breadth-first depth for every reachable vertex.
     * Depends-On: bellmanFordHandlesNegativeWeights, breadthFirstDepthAndParent, defaultWeightIsOne.
     */
    @Test
    void bellmanFordAgreesWithBfsOnUnweighted() {
        Graph<String, DefaultEdge> g = dag();
        BreadthFirstIterator<String, DefaultEdge> it = new BreadthFirstIterator<>(g, "A");
        GraphsFixtures.drain(it);
        BellmanFordShortestPath<String, DefaultEdge> alg = new BellmanFordShortestPath<>(g);
        for (String v : g.vertexSet()) {
            assertEquals((double) it.getDepth(v), alg.getPath("A", v).getWeight());
        }
    }

    /**
     * Verifies: Cross-View Invariants — traversal and shortest paths read
     * mutations made through the Graph interface: adding a shortcut edge
     * changes both the breadth-first depth and the Dijkstra answer.
     * Depends-On: breadthFirstDepthAndParent, dijkstraFindsMinimumWeightPath, addEdgeReturnsNewEdge.
     */
    @Test
    void mutationVisibleToTraversalAndPaths() {
        Graph<String, DefaultEdge> g = dag();
        BreadthFirstIterator<String, DefaultEdge> before = new BreadthFirstIterator<>(g, "A");
        GraphsFixtures.drain(before);
        assertEquals(3, before.getDepth("E"));
        assertEquals(3, new DijkstraShortestPath<>(g).getPath("A", "E").getLength());

        g.addEdge("A", "E");
        BreadthFirstIterator<String, DefaultEdge> after = new BreadthFirstIterator<>(g, "A");
        GraphsFixtures.drain(after);
        assertEquals(1, after.getDepth("E"));
        assertEquals(1, new DijkstraShortestPath<>(g).getPath("A", "E").getLength());
    }
}
