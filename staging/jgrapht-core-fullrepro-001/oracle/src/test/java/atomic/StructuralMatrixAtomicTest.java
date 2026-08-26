package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.GraphType;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.DefaultUndirectedGraph;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.jgrapht.graph.DirectedMultigraph;
import org.jgrapht.graph.DirectedPseudograph;
import org.jgrapht.graph.Multigraph;
import org.jgrapht.graph.Pseudograph;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleDirectedWeightedGraph;
import org.jgrapht.graph.SimpleGraph;
import org.jgrapht.graph.SimpleWeightedGraph;
import org.junit.jupiter.api.Test;

/** Per-class structural declarations and admission rules. */
class StructuralMatrixAtomicTest {

    private static void assertType(Graph<String, DefaultEdge> g, boolean directed,
            boolean loops, boolean multi) {
        GraphType t = g.getType();
        assertEquals(directed, t.isDirected());
        assertEquals(!directed, t.isUndirected());
        assertEquals(loops, t.isAllowingSelfLoops());
        assertEquals(multi, t.isAllowingMultipleEdges());
        assertFalse(t.isWeighted());
    }

    /**
     * Verifies: Graph Classes and Structural Rules — the four undirected
     * unweighted classes declare their structural matrix row through
     * getType().
     */
    @Test
    void undirectedClassesDeclareMatrixRow() {
        assertType(new SimpleGraph<>(DefaultEdge.class), false, false, false);
        assertType(new Multigraph<>(DefaultEdge.class), false, false, true);
        assertType(new Pseudograph<>(DefaultEdge.class), false, true, true);
        assertType(new DefaultUndirectedGraph<>(DefaultEdge.class), false, true, false);
    }

    /**
     * Verifies: Graph Classes and Structural Rules — the four directed
     * unweighted classes declare their structural matrix row through
     * getType().
     */
    @Test
    void directedClassesDeclareMatrixRow() {
        assertType(new SimpleDirectedGraph<>(DefaultEdge.class), true, false, false);
        assertType(new DirectedMultigraph<>(DefaultEdge.class), true, false, true);
        assertType(new DirectedPseudograph<>(DefaultEdge.class), true, true, true);
        assertType(new DefaultDirectedGraph<>(DefaultEdge.class), true, true, false);
    }

    /**
     * Verifies: Graph Classes and Structural Rules — a self-loop is refused
     * with IllegalArgumentException in every class that forbids self-loops.
     */
    @Test
    void selfLoopRaisesWhereForbidden() {
        List<Graph<String, DefaultEdge>> forbidding = List.of(
                new SimpleGraph<>(DefaultEdge.class),
                new SimpleDirectedGraph<>(DefaultEdge.class),
                new Multigraph<>(DefaultEdge.class),
                new DirectedMultigraph<>(DefaultEdge.class));
        for (Graph<String, DefaultEdge> g : forbidding) {
            g.addVertex("a");
            assertThrows(IllegalArgumentException.class, () -> g.addEdge("a", "a"));
        }
    }

    /**
     * Verifies: Graph Classes and Structural Rules — a self-loop is created
     * normally in every class that permits self-loops.
     */
    @Test
    void selfLoopCreatedWherePermitted() {
        List<Graph<String, DefaultEdge>> permitting = List.of(
                new Pseudograph<>(DefaultEdge.class),
                new DirectedPseudograph<>(DefaultEdge.class),
                new DefaultUndirectedGraph<>(DefaultEdge.class),
                new DefaultDirectedGraph<>(DefaultEdge.class));
        for (Graph<String, DefaultEdge> g : permitting) {
            g.addVertex("a");
            assertNotNull(g.addEdge("a", "a"));
            assertEquals(1, g.edgeSet().size());
        }
    }

    /**
     * Verifies: Graph Classes and Structural Rules — a duplicate endpoint
     * pair returns null without an exception in every class that forbids
     * multiple edges.
     */
    @Test
    void parallelEdgeReturnsNullWhereForbidden() {
        List<Graph<String, DefaultEdge>> forbidding = List.of(
                new SimpleGraph<>(DefaultEdge.class),
                new SimpleDirectedGraph<>(DefaultEdge.class),
                new DefaultUndirectedGraph<>(DefaultEdge.class),
                new DefaultDirectedGraph<>(DefaultEdge.class));
        for (Graph<String, DefaultEdge> g : forbidding) {
            g.addVertex("a");
            g.addVertex("b");
            assertNotNull(g.addEdge("a", "b"));
            assertNull(g.addEdge("a", "b"));
            assertEquals(1, g.edgeSet().size());
        }
    }

    /**
     * Verifies: Graph Classes and Structural Rules — a multigraph
     * accumulates parallel edges as distinct edge objects.
     */
    @Test
    void parallelEdgesAccumulateWherePermitted() {
        List<Graph<String, DefaultEdge>> permitting = List.of(
                new Multigraph<>(DefaultEdge.class),
                new DirectedMultigraph<>(DefaultEdge.class),
                new Pseudograph<>(DefaultEdge.class),
                new DirectedPseudograph<>(DefaultEdge.class));
        for (Graph<String, DefaultEdge> g : permitting) {
            g.addVertex("a");
            g.addVertex("b");
            DefaultEdge first = g.addEdge("a", "b");
            DefaultEdge second = g.addEdge("a", "b");
            assertNotNull(second);
            assertTrue(first != second);
            assertEquals(2, g.edgeSet().size());
        }
    }

    /**
     * Verifies: Graph Classes and Structural Rules — in an undirected class
     * the pair (u, v) and (v, u) are the same endpoint pair for multiplicity.
     */
    @Test
    void undirectedMultiplicityIgnoresOrder() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("u");
        g.addVertex("v");
        assertNotNull(g.addEdge("u", "v"));
        assertNull(g.addEdge("v", "u"));
    }

    /**
     * Verifies: Graph Classes and Structural Rules — in a directed simple
     * class the reverse pair is a distinct endpoint pair.
     */
    @Test
    void directedMultiplicityDistinguishesOrder() {
        Graph<String, DefaultEdge> g = new SimpleDirectedGraph<>(DefaultEdge.class);
        g.addVertex("u");
        g.addVertex("v");
        assertNotNull(g.addEdge("u", "v"));
        assertNotNull(g.addEdge("v", "u"));
        assertEquals(2, g.edgeSet().size());
    }

    /**
     * Verifies: Graph Classes and Structural Rules — the weighted classes
     * mirror their unweighted counterparts with isWeighted true.
     */
    @Test
    void weightedClassesMirrorStructure() {
        Graph<String, DefaultWeightedEdge> sw = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
        assertTrue(sw.getType().isWeighted());
        assertTrue(sw.getType().isUndirected());
        assertFalse(sw.getType().isAllowingSelfLoops());
        assertFalse(sw.getType().isAllowingMultipleEdges());

        Graph<String, DefaultWeightedEdge> sdw =
                new SimpleDirectedWeightedGraph<>(DefaultWeightedEdge.class);
        assertTrue(sdw.getType().isWeighted());
        assertTrue(sdw.getType().isDirected());
    }
}
