package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.graph.AsSubgraph;
import org.jgrapht.graph.AsUnmodifiableGraph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.EdgeReversedGraph;
import org.jgrapht.graph.MaskSubgraph;
import org.jgrapht.graph.SimpleGraph;
import org.junit.jupiter.api.Test;

/** Views: unmodifiable, edge-reversed, subgraph window, masked. */
class ViewsAtomicTest {

    /**
     * Verifies: Graph Views — every mutator of AsUnmodifiableGraph raises
     * UnsupportedOperationException.
     */
    @Test
    void unmodifiableMutatorsRaise() {
        Graph<String, DefaultEdge> base = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("a", "b"));
        DefaultEdge e = base.addEdge("a", "b");
        Graph<String, DefaultEdge> unmod = new AsUnmodifiableGraph<>(base);
        assertThrows(UnsupportedOperationException.class, () -> unmod.addVertex("z"));
        assertThrows(UnsupportedOperationException.class, () -> unmod.addEdge("a", "b"));
        assertThrows(UnsupportedOperationException.class, () -> unmod.removeVertex("a"));
        assertThrows(UnsupportedOperationException.class, () -> unmod.removeEdge(e));
    }

    /**
     * Verifies: Graph Views — AsUnmodifiableGraph reads the backing graph
     * live: backing mutations are visible immediately.
     */
    @Test
    void unmodifiableReadsBackingLive() {
        Graph<String, DefaultEdge> base = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("a", "b", "c"));
        base.addEdge("a", "b");
        Graph<String, DefaultEdge> unmod = new AsUnmodifiableGraph<>(base);
        assertEquals(1, unmod.edgeSet().size());
        base.addEdge("b", "c");
        assertEquals(2, unmod.edgeSet().size());
        assertTrue(unmod.containsEdge("b", "c"));
    }

    /**
     * Verifies: Graph Views — the unmodifiable view's type reports
     * isModifiable false.
     */
    @Test
    void unmodifiableTypeReportsUnmodifiable() {
        Graph<String, DefaultEdge> base = new SimpleGraph<>(DefaultEdge.class);
        assertFalse(new AsUnmodifiableGraph<>(base).getType().isModifiable());
        assertTrue(base.getType().isModifiable());
    }

    /**
     * Verifies: Graph Views — EdgeReversedGraph swaps getEdgeSource and
     * getEdgeTarget for every backing edge.
     */
    @Test
    void reversedViewSwapsEndpoints() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("1", "2"));
        DefaultEdge e = base.addEdge("1", "2");
        Graph<String, DefaultEdge> rev = new EdgeReversedGraph<>(base);
        assertEquals("2", rev.getEdgeSource(e));
        assertEquals("1", rev.getEdgeTarget(e));
        assertEquals(e, rev.getEdge("2", "1"));
    }

    /**
     * Verifies: Graph Views — EdgeReversedGraph swaps incoming and outgoing
     * incidence and degree accounting.
     */
    @Test
    void reversedViewSwapsIncidence() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("1", "2", "3"));
        base.addEdge("1", "2");
        base.addEdge("2", "3");
        Graph<String, DefaultEdge> rev = new EdgeReversedGraph<>(base);
        assertEquals(base.incomingEdgesOf("2"), rev.outgoingEdgesOf("2"));
        assertEquals(base.outgoingEdgesOf("2"), rev.incomingEdgesOf("2"));
        assertEquals(base.inDegreeOf("2"), rev.outDegreeOf("2"));
        assertEquals(base.outDegreeOf("2"), rev.inDegreeOf("2"));
    }

    /**
     * Verifies: Graph Views — EdgeReversedGraph is writable: addEdge on the
     * view creates the reversed backing edge.
     */
    @Test
    void reversedViewWritesThrough() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("1", "2"));
        Graph<String, DefaultEdge> rev = new EdgeReversedGraph<>(base);
        assertNotNull(rev.addEdge("1", "2"));
        assertNotNull(base.getEdge("2", "1"));
        assertTrue(base.getEdge("1", "2") == null);
    }

    /**
     * Verifies: Graph Views — AsSubgraph over a vertex subset materializes
     * the induced subgraph at construction.
     */
    @Test
    void subgraphIsInducedAtConstruction() {
        Graph<String, DefaultEdge> big = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(big, Arrays.asList("u", "v", "w", "x"));
        big.addEdge("u", "v");
        big.addEdge("v", "w");
        big.addEdge("w", "x");
        Graph<String, DefaultEdge> sub =
                new AsSubgraph<>(big, new HashSet<>(Arrays.asList("u", "v", "w")));
        assertEquals(Set.of("u", "v", "w"), sub.vertexSet());
        assertEquals(2, sub.edgeSet().size());
        assertTrue(sub.containsEdge("u", "v"));
        assertTrue(sub.containsEdge("v", "w"));
        assertFalse(sub.containsEdge("w", "x"));
    }

    /**
     * Verifies: Graph Views — the three-argument AsSubgraph with a null edge
     * subset selects the induced form.
     */
    @Test
    void subgraphNullEdgeSubsetIsInduced() {
        Graph<String, DefaultEdge> big = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(big, Arrays.asList("u", "v", "w"));
        big.addEdge("u", "v");
        big.addEdge("v", "w");
        Graph<String, DefaultEdge> sub =
                new AsSubgraph<>(big, new HashSet<>(Arrays.asList("u", "v", "w")), null);
        assertEquals(2, sub.edgeSet().size());
    }

    /**
     * Verifies: Graph Views — AsSubgraph does not absorb backing edges added
     * after construction; addEdge on the subgraph admits the backing edge and
     * raises IllegalArgumentException when the backing graph has none.
     */
    @Test
    void subgraphTracksOwnWindow() {
        Graph<String, DefaultEdge> big = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(big, Arrays.asList("u", "v", "w"));
        big.addEdge("u", "v");
        Graph<String, DefaultEdge> sub =
                new AsSubgraph<>(big, new HashSet<>(Arrays.asList("u", "v", "w")));
        assertThrows(IllegalArgumentException.class, () -> sub.addEdge("u", "w"));
        big.addEdge("u", "w");
        assertFalse(sub.containsEdge("u", "w"));
        assertNotNull(sub.addEdge("u", "w"));
        assertTrue(sub.containsEdge("u", "w"));
    }

    /**
     * Verifies: Graph Views — removeEdge on an AsSubgraph removes the edge
     * from the window while leaving the backing graph untouched.
     */
    @Test
    void subgraphRemovalIsLocal() {
        Graph<String, DefaultEdge> big = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(big, Arrays.asList("u", "v"));
        big.addEdge("u", "v");
        Graph<String, DefaultEdge> sub =
                new AsSubgraph<>(big, new HashSet<>(Arrays.asList("u", "v")));
        assertNotNull(sub.removeEdge("u", "v"));
        assertFalse(sub.containsEdge("u", "v"));
        assertTrue(big.containsEdge("u", "v"));
    }

    /**
     * Verifies: Graph Views — MaskSubgraph hides masked vertices, masked
     * edges, and edges with a hidden endpoint.
     */
    @Test
    void maskHidesByPredicate() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("k", "l", "m"));
        base.addEdge("k", "l");
        DefaultEdge lm = base.addEdge("l", "m");
        Graph<String, DefaultEdge> masked =
                new MaskSubgraph<>(base, v -> v.equals("m"), e -> false);
        assertEquals(Set.of("k", "l"), masked.vertexSet());
        assertEquals(1, masked.edgeSet().size());
        assertFalse(masked.edgeSet().contains(lm));

        Graph<String, DefaultEdge> edgeMasked =
                new MaskSubgraph<>(base, v -> false, e -> e == lm);
        assertEquals(3, edgeMasked.vertexSet().size());
        assertEquals(1, edgeMasked.edgeSet().size());
    }

    /**
     * Verifies: Graph Views — MaskSubgraph is evaluated live over the backing
     * graph and its own mutators raise UnsupportedOperationException.
     */
    @Test
    void maskIsLiveAndReadOnly() {
        Graph<String, DefaultEdge> base = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(base, Arrays.asList("k", "l", "m", "n"));
        base.addEdge("k", "l");
        Graph<String, DefaultEdge> masked =
                new MaskSubgraph<>(base, v -> v.equals("m"), e -> false);
        assertEquals(1, masked.edgeSet().size());
        base.addEdge("l", "n");
        assertEquals(2, masked.edgeSet().size());
        base.addVertex("o");
        assertTrue(masked.containsVertex("o"));
        assertThrows(UnsupportedOperationException.class, () -> masked.addVertex("q"));
    }
}
