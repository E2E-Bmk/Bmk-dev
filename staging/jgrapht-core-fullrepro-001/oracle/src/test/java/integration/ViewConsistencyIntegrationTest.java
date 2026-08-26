package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.graph.AsSubgraph;
import org.jgrapht.graph.AsUnmodifiableGraph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.DefaultUndirectedGraph;
import org.jgrapht.graph.DirectedMultigraph;
import org.jgrapht.graph.DirectedPseudograph;
import org.jgrapht.graph.EdgeReversedGraph;
import org.jgrapht.graph.MaskSubgraph;
import org.jgrapht.graph.Multigraph;
import org.jgrapht.graph.Pseudograph;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleGraph;
import org.junit.jupiter.api.Test;

/** Consistency between views, types, and the backing graph. */
class ViewConsistencyIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — a query through AsUnmodifiableGraph
     * equals the same query on the backing graph at the same moment, across a
     * mutation sequence.
     * Depends-On: unmodifiableReadsBackingLive, removeVertexRemovesIncidentEdges.
     */
    @Test
    void unmodifiableAgreesAcrossMutations() {
        Graph<String, DefaultEdge> base = new SimpleGraph<>(DefaultEdge.class);
        Graph<String, DefaultEdge> unmod = new AsUnmodifiableGraph<>(base);
        Graphs.addAllVertices(base, Arrays.asList("a", "b", "c"));
        base.addEdge("a", "b");
        assertEquals(base.vertexSet(), unmod.vertexSet());
        assertEquals(base.edgeSet(), unmod.edgeSet());
        base.addEdge("b", "c");
        base.removeVertex("a");
        assertEquals(base.vertexSet(), unmod.vertexSet());
        assertEquals(base.edgeSet(), unmod.edgeSet());
        assertEquals(base.degreeOf("b"), unmod.degreeOf("b"));
    }

    /**
     * Verifies: Cross-View Invariants — EdgeReversedGraph answers each
     * directional query exactly as the backing graph answers the opposite
     * member of the pair, for every vertex and edge.
     * Depends-On: reversedViewSwapsEndpoints, reversedViewSwapsIncidence.
     */
    @Test
    void reversedViewMirrorsAllDirectionalQueries() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("1", "2", "3", "4"));
        base.addEdge("1", "2");
        base.addEdge("2", "3");
        base.addEdge("3", "1");
        base.addEdge("2", "4");
        Graph<String, DefaultEdge> rev = new EdgeReversedGraph<>(base);
        for (String v : base.vertexSet()) {
            assertEquals(base.incomingEdgesOf(v), rev.outgoingEdgesOf(v));
            assertEquals(base.outgoingEdgesOf(v), rev.incomingEdgesOf(v));
            assertEquals(base.inDegreeOf(v), rev.outDegreeOf(v));
            assertEquals(base.outDegreeOf(v), rev.inDegreeOf(v));
            assertEquals(base.degreeOf(v), rev.degreeOf(v));
        }
        for (DefaultEdge e : base.edgeSet()) {
            assertEquals(base.getEdgeSource(e), rev.getEdgeTarget(e));
            assertEquals(base.getEdgeTarget(e), rev.getEdgeSource(e));
        }
    }

    /**
     * Verifies: Cross-View Invariants — the structural declaration and
     * addEdge behavior agree in every unweighted class: self-loops raise
     * exactly where the type forbids them.
     * Depends-On: selfLoopRaisesWhereForbidden, selfLoopCreatedWherePermitted, undirectedClassesDeclareMatrixRow.
     */
    @Test
    void typeAndSelfLoopBehaviorAgree() {
        List<Graph<String, DefaultEdge>> all = List.of(
                new SimpleGraph<>(DefaultEdge.class),
                new SimpleDirectedGraph<>(DefaultEdge.class),
                new Multigraph<>(DefaultEdge.class),
                new DirectedMultigraph<>(DefaultEdge.class),
                new Pseudograph<>(DefaultEdge.class),
                new DirectedPseudograph<>(DefaultEdge.class),
                new DefaultUndirectedGraph<>(DefaultEdge.class),
                new DefaultDirectedGraph<>(DefaultEdge.class));
        for (Graph<String, DefaultEdge> g : all) {
            g.addVertex("a");
            if (g.getType().isAllowingSelfLoops()) {
                assertNotNull(g.addEdge("a", "a"));
            } else {
                assertThrows(IllegalArgumentException.class, () -> g.addEdge("a", "a"));
            }
        }
    }

    /**
     * Verifies: Cross-View Invariants — the structural declaration and
     * addEdge behavior agree in every unweighted class: duplicate pairs
     * return null exactly where the type forbids multiple edges.
     * Depends-On: parallelEdgeReturnsNullWhereForbidden, parallelEdgesAccumulateWherePermitted.
     */
    @Test
    void typeAndMultiplicityBehaviorAgree() {
        List<Graph<String, DefaultEdge>> all = List.of(
                new SimpleGraph<>(DefaultEdge.class),
                new SimpleDirectedGraph<>(DefaultEdge.class),
                new Multigraph<>(DefaultEdge.class),
                new DirectedMultigraph<>(DefaultEdge.class),
                new Pseudograph<>(DefaultEdge.class),
                new DirectedPseudograph<>(DefaultEdge.class),
                new DefaultUndirectedGraph<>(DefaultEdge.class),
                new DefaultDirectedGraph<>(DefaultEdge.class));
        for (Graph<String, DefaultEdge> g : all) {
            g.addVertex("a");
            g.addVertex("b");
            assertNotNull(g.addEdge("a", "b"));
            DefaultEdge second = g.addEdge("a", "b");
            if (g.getType().isAllowingMultipleEdges()) {
                assertNotNull(second);
                assertEquals(2, g.edgeSet().size());
            } else {
                assertNull(second);
                assertEquals(1, g.edgeSet().size());
            }
        }
    }

    /**
     * Verifies: Cross-View Invariants — the sum of degreeOf over all vertices
     * equals twice the edge count, with self-loops counted twice, in classes
     * of every structural row.
     * Depends-On: selfLoopCountsTwiceInDegree, directedDegreesSplitByDirection.
     */
    @Test
    void degreeSumIsTwiceEdgeCount() {
        Graph<String, DefaultEdge> g = new DirectedPseudograph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("a", "b", "c"));
        g.addEdge("a", "b");
        g.addEdge("a", "b");
        g.addEdge("a", "a");
        g.addEdge("b", "c");
        int degreeSum = 0;
        for (String v : g.vertexSet()) {
            degreeSum += g.degreeOf(v);
            assertEquals(g.degreeOf(v), g.inDegreeOf(v) + g.outDegreeOf(v));
        }
        assertEquals(2 * g.edgeSet().size(), degreeSum);

        Graph<String, DefaultEdge> u = new Pseudograph<>(DefaultEdge.class);
        Graphs.addAllVertices(u, Arrays.asList("x", "y"));
        u.addEdge("x", "y");
        u.addEdge("x", "x");
        int uSum = 0;
        for (String v : u.vertexSet()) {
            uSum += u.degreeOf(v);
        }
        assertEquals(2 * u.edgeSet().size(), uSum);
    }

    /**
     * Verifies: Cross-View Invariants — removing a vertex through the Graph
     * interface removes its incident edges from every live view over that
     * graph.
     * Depends-On: removeVertexRemovesIncidentEdges, unmodifiableReadsBackingLive, maskIsLiveAndReadOnly.
     */
    @Test
    void vertexRemovalPropagatesToLiveViews() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("a", "b", "c"));
        base.addEdge("a", "b");
        base.addEdge("b", "c");
        Graph<String, DefaultEdge> unmod = new AsUnmodifiableGraph<>(base);
        Graph<String, DefaultEdge> masked = new MaskSubgraph<>(base, v -> false, e -> false);
        assertEquals(2, unmod.edgeSet().size());
        assertEquals(2, masked.edgeSet().size());
        base.removeVertex("b");
        assertEquals(0, unmod.edgeSet().size());
        assertEquals(0, masked.edgeSet().size());
        assertFalse(masked.containsVertex("b"));
    }

    /**
     * Verifies: Cross-View Invariants — a fresh AsSubgraph holds a backing
     * edge if and only if both endpoints are in the vertex subset.
     * Depends-On: subgraphIsInducedAtConstruction.
     */
    @Test
    void subgraphInductionIsExact() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("a", "b", "c", "d"));
        base.addEdge("a", "b");
        base.addEdge("b", "c");
        base.addEdge("c", "d");
        base.addEdge("d", "a");
        base.addEdge("a", "c");
        HashSet<String> subset = new HashSet<>(Arrays.asList("a", "b", "c"));
        Graph<String, DefaultEdge> sub = new AsSubgraph<>(base, subset);
        for (DefaultEdge e : base.edgeSet()) {
            boolean bothIn = subset.contains(base.getEdgeSource(e))
                    && subset.contains(base.getEdgeTarget(e));
            assertEquals(bothIn, sub.edgeSet().contains(e));
        }
    }

    /**
     * Verifies: Cross-View Invariants — views compose: an unmodifiable view
     * over an induced subgraph answers the subgraph's queries and refuses
     * mutation.
     * Depends-On: unmodifiableMutatorsRaise, subgraphIsInducedAtConstruction.
     */
    @Test
    void unmodifiableComposesOverSubgraph() {
        Graph<String, DefaultEdge> base = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("a", "b", "c", "d"));
        base.addEdge("a", "b");
        base.addEdge("b", "c");
        base.addEdge("c", "d");
        Graph<String, DefaultEdge> sub =
                new AsSubgraph<>(base, new HashSet<>(Arrays.asList("a", "b", "c")));
        Graph<String, DefaultEdge> frozen = new AsUnmodifiableGraph<>(sub);
        assertEquals(sub.vertexSet(), frozen.vertexSet());
        assertEquals(sub.edgeSet(), frozen.edgeSet());
        assertTrue(frozen.containsEdge("a", "b"));
        assertThrows(UnsupportedOperationException.class, () -> frozen.addVertex("z"));
        assertThrows(UnsupportedOperationException.class, () -> frozen.removeEdge("a", "b"));
    }

    /**
     * Verifies: Cross-View Invariants — a masked view and an induced subgraph
     * over the complement selection agree on the surviving structure.
     * Depends-On: maskHidesByPredicate, subgraphIsInducedAtConstruction.
     */
    @Test
    void maskAndSubgraphAgreeOnSurvivors() {
        Graph<String, DefaultEdge> base = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("a", "b", "c", "d"));
        base.addEdge("a", "b");
        base.addEdge("b", "c");
        base.addEdge("c", "d");
        Graph<String, DefaultEdge> masked = new MaskSubgraph<>(base, v -> v.equals("d"), e -> false);
        Graph<String, DefaultEdge> sub =
                new AsSubgraph<>(base, new HashSet<>(Arrays.asList("a", "b", "c")));
        assertEquals(sub.vertexSet(), masked.vertexSet());
        assertEquals(sub.edgeSet(), masked.edgeSet());
        assertTrue(masked.containsEdge("b", "c"));
        assertFalse(masked.containsEdge("c", "d"));
    }
}
