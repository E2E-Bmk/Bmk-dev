package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleGraph;
import org.junit.jupiter.api.Test;

/** Vertex and edge mutation semantics of the Graph interface. */
class GraphMutationAtomicTest {

    /**
     * Verifies: Graph Structure and Mutation — addVertex inserts and returns
     * true; a present vertex returns false and leaves the graph unchanged.
     */
    @Test
    void addVertexReportsInsertion() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        assertTrue(g.addVertex("a"));
        assertFalse(g.addVertex("a"));
        assertEquals(1, g.vertexSet().size());
        assertTrue(g.containsVertex("a"));
        assertFalse(g.containsVertex("b"));
    }

    /**
     * Verifies: Graph Structure and Mutation — addEdge creates a new edge
     * object connecting the endpoints and returns it.
     */
    @Test
    void addEdgeReturnsNewEdge() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        DefaultEdge e = g.addEdge("a", "b");
        assertEquals("a", g.getEdgeSource(e));
        assertEquals("b", g.getEdgeTarget(e));
        assertEquals(1, g.edgeSet().size());
    }

    /**
     * Verifies: Graph Structure and Mutation — addEdge with an absent
     * endpoint raises IllegalArgumentException.
     */
    @Test
    void addEdgeMissingVertexRaises() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        assertThrows(IllegalArgumentException.class, () -> g.addEdge("a", "nope"));
    }

    /**
     * Verifies: Graph Structure and Mutation — addEdge with a null endpoint
     * raises NullPointerException.
     */
    @Test
    void addEdgeNullVertexRaises() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        assertThrows(NullPointerException.class, () -> g.addEdge("a", null));
    }

    /**
     * Verifies: Graph Structure and Mutation — getEdge returns the connecting
     * edge in either endpoint order for an undirected graph, and null when no
     * edge or vertex matches.
     */
    @Test
    void getEdgeUndirectedIgnoresOrder() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        g.addVertex("c");
        DefaultEdge e = g.addEdge("a", "b");
        assertEquals(e, g.getEdge("a", "b"));
        assertEquals(e, g.getEdge("b", "a"));
        assertNull(g.getEdge("a", "c"));
        assertNull(g.getEdge("a", "zzz"));
    }

    /**
     * Verifies: Graph Structure and Mutation — containsEdge reports whether a
     * connecting edge exists.
     */
    @Test
    void containsEdgeReportsConnection() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        g.addVertex("c");
        g.addEdge("a", "b");
        assertTrue(g.containsEdge("a", "b"));
        assertFalse(g.containsEdge("a", "c"));
    }

    /**
     * Verifies: Graph Structure and Mutation — removeEdge by endpoint pair
     * removes and returns the connecting edge, or returns null when there is
     * none.
     */
    @Test
    void removeEdgeByPairReturnsEdge() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        DefaultEdge e = g.addEdge("a", "b");
        assertEquals(e, g.removeEdge("a", "b"));
        assertNull(g.removeEdge("a", "b"));
        assertEquals(0, g.edgeSet().size());
    }

    /**
     * Verifies: Graph Structure and Mutation — removeEdge by edge object
     * returns whether the graph changed.
     */
    @Test
    void removeEdgeByObjectReportsChange() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        DefaultEdge e = g.addEdge("a", "b");
        assertTrue(g.removeEdge(e));
        assertFalse(g.removeEdge(e));
    }

    /**
     * Verifies: Graph Structure and Mutation — removeVertex removes the
     * vertex with every incident edge and reports whether the graph changed.
     */
    @Test
    void removeVertexRemovesIncidentEdges() {
        Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
        g.addVertex("x");
        g.addVertex("y");
        g.addVertex("z");
        g.addEdge("x", "y");
        g.addEdge("x", "z");
        g.addEdge("y", "x");
        assertTrue(g.removeVertex("x"));
        assertEquals(0, g.edgeSet().size());
        assertFalse(g.containsVertex("x"));
        assertFalse(g.removeVertex("x"));
    }

    /**
     * Verifies: Graph Structure and Mutation — vertexSet iterates in
     * insertion order.
     */
    @Test
    void vertexSetIteratesInInsertionOrder() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        for (String v : Arrays.asList("z", "a", "m", "b")) {
            g.addVertex(v);
        }
        assertEquals(List.of("z", "a", "m", "b"), new ArrayList<>(g.vertexSet()));
    }

    /**
     * Verifies: Graph Structure and Mutation — edgeSet iterates in insertion
     * order.
     */
    @Test
    void edgeSetIteratesInInsertionOrder() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        for (String v : Arrays.asList("z", "a", "m", "b")) {
            g.addVertex(v);
        }
        DefaultEdge first = g.addEdge("m", "b");
        DefaultEdge second = g.addEdge("z", "a");
        assertEquals(List.of(first, second), new ArrayList<>(g.edgeSet()));
    }

    /**
     * Verifies: Graph Structure and Mutation — getEdgeSource and
     * getEdgeTarget return the endpoints the edge was created with.
     */
    @Test
    void edgeEndpointsArePreserved() {
        Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
        g.addVertex("from");
        g.addVertex("to");
        DefaultEdge e = g.addEdge("from", "to");
        assertEquals("from", g.getEdgeSource(e));
        assertEquals("to", g.getEdgeTarget(e));
    }

    /**
     * Verifies: Graph Classes and Structural Rules — DefaultEdge toString
     * renders as (source : target).
     */
    @Test
    void defaultEdgeRendersEndpoints() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        DefaultEdge e = g.addEdge("a", "b");
        assertEquals("(a : b)", e.toString());
    }
}
