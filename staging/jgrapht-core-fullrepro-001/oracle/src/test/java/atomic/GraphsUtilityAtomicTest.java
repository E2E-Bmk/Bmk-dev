package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleGraph;
import org.junit.jupiter.api.Test;

/** Static bulk helpers of the Graphs utility class. */
class GraphsUtilityAtomicTest {

    /**
     * Verifies: Graph Structure and Mutation — addEdgeWithVertices inserts
     * missing endpoints before connecting them and returns the new edge.
     */
    @Test
    void addEdgeWithVerticesInsertsEndpoints() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        DefaultEdge e = Graphs.addEdgeWithVertices(g, "m", "n");
        assertNotNull(e);
        assertTrue(g.containsVertex("m"));
        assertTrue(g.containsVertex("n"));
        assertEquals(1, g.edgeSet().size());
    }

    /**
     * Verifies: Graph Structure and Mutation — addAllVertices inserts each
     * vertex and returns whether the graph changed.
     */
    @Test
    void addAllVerticesReportsChange() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        assertTrue(Graphs.addAllVertices(g, Arrays.asList("a", "b")));
        assertEquals(2, g.vertexSet().size());
        assertFalse(Graphs.addAllVertices(g, Arrays.asList("a", "b")));
    }

    /**
     * Verifies: Graph Structure and Mutation — neighborListOf lists the
     * adjacent vertices of a vertex.
     */
    @Test
    void neighborListOfListsAdjacent() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("m", "n", "o"));
        g.addEdge("m", "n");
        g.addEdge("n", "o");
        assertEquals(List.of("m", "o"), Graphs.neighborListOf(g, "n"));
    }

    /**
     * Verifies: Graph Structure and Mutation — successorListOf and
     * predecessorListOf split adjacency by direction in a directed graph.
     */
    @Test
    void successorAndPredecessorLists() {
        Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addEdgeWithVertices(g, "1", "2");
        Graphs.addEdgeWithVertices(g, "3", "1");
        assertEquals(List.of("2"), Graphs.successorListOf(g, "1"));
        assertEquals(List.of("3"), Graphs.predecessorListOf(g, "1"));
    }
}
