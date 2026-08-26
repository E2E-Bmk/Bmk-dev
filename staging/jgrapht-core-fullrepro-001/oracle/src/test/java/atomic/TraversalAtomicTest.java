package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;
import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleGraph;
import org.jgrapht.traverse.BreadthFirstIterator;
import org.jgrapht.traverse.DepthFirstIterator;
import org.jgrapht.traverse.NotDirectedAcyclicGraphException;
import org.jgrapht.traverse.TopologicalOrderIterator;
import org.junit.jupiter.api.Test;
import support.GraphsFixtures;

/** Breadth-first, depth-first, and topological iteration. */
class TraversalAtomicTest {

    private static Graph<String, DefaultEdge> diamond() {
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
     * Verifies: Traversal Iterators — breadth-first returns vertices in
     * nondecreasing distance from the start, discovering same-depth vertices
     * in edge insertion order.
     */
    @Test
    void breadthFirstLevelOrder() {
        BreadthFirstIterator<String, DefaultEdge> it =
                new BreadthFirstIterator<>(diamond(), "A");
        assertEquals(List.of("A", "B", "C", "D", "E"), GraphsFixtures.drain(it));
    }

    /**
     * Verifies: Traversal Iterators — getDepth reports distance in edges and
     * getParent the discovering vertex; the start reports 0 and null.
     */
    @Test
    void breadthFirstDepthAndParent() {
        BreadthFirstIterator<String, DefaultEdge> it =
                new BreadthFirstIterator<>(diamond(), "A");
        GraphsFixtures.drain(it);
        assertEquals(0, it.getDepth("A"));
        assertNull(it.getParent("A"));
        assertEquals(1, it.getDepth("B"));
        assertEquals("A", it.getParent("B"));
        assertEquals(2, it.getDepth("D"));
        assertEquals("B", it.getParent("D"));
        assertEquals(3, it.getDepth("E"));
    }

    /**
     * Verifies: Traversal Iterators — the single-argument breadth-first form
     * covers the whole graph starting from the first vertex in insertion
     * order.
     */
    @Test
    void breadthFirstWholeGraph() {
        Graph<String, DefaultEdge> g = diamond();
        g.addVertex("ISO");
        BreadthFirstIterator<String, DefaultEdge> it = new BreadthFirstIterator<>(g);
        assertEquals(List.of("A", "B", "C", "D", "E", "ISO"), GraphsFixtures.drain(it));
    }

    /**
     * Verifies: Error Semantics — a traversal start vertex not in the graph
     * raises IllegalArgumentException.
     */
    @Test
    void missingStartVertexRaises() {
        Graph<String, DefaultEdge> g = diamond();
        assertThrows(IllegalArgumentException.class,
                () -> new BreadthFirstIterator<>(g, "ZZ"));
    }

    /**
     * Verifies: Traversal Iterators — depth-first explores under LIFO
     * discipline: among unvisited neighbors, the one whose edge was inserted
     * last is returned first.
     */
    @Test
    void depthFirstLifoOrder() {
        DepthFirstIterator<String, DefaultEdge> it =
                new DepthFirstIterator<>(diamond(), "A");
        assertEquals(List.of("A", "C", "D", "E", "B"), GraphsFixtures.drain(it));
    }

    /**
     * Verifies: Traversal Iterators — breadth-first and depth-first treat an
     * undirected edge as traversable in both directions.
     */
    @Test
    void undirectedTraversalFollowsBothDirections() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("a", "b", "c"));
        g.addEdge("a", "b");
        g.addEdge("c", "b");
        assertEquals(List.of("b", "a", "c"),
                GraphsFixtures.drain(new BreadthFirstIterator<>(g, "b")));
        assertEquals(List.of("a", "b", "c"),
                GraphsFixtures.drain(new DepthFirstIterator<>(g, "a")));
    }

    /**
     * Verifies: Traversal Iterators — topological iteration returns every
     * vertex after all vertices with an edge into it.
     */
    @Test
    void topologicalOrderRespectsEdges() {
        Graph<String, DefaultEdge> g = diamond();
        List<String> order = GraphsFixtures.drain(new TopologicalOrderIterator<>(g));
        assertEquals(5, order.size());
        for (DefaultEdge e : g.edgeSet()) {
            String u = g.getEdgeSource(e);
            String v = g.getEdgeTarget(e);
            assertTrue(order.indexOf(u) < order.indexOf(v));
        }
    }

    /**
     * Verifies: Error Semantics — topological iteration over an undirected
     * graph raises IllegalArgumentException at construction.
     */
    @Test
    void topologicalUndirectedRaises() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("u");
        assertThrows(IllegalArgumentException.class,
                () -> new TopologicalOrderIterator<>(g));
    }

    /**
     * Verifies: Error Semantics — topological iteration over a cyclic
     * directed graph raises NotDirectedAcyclicGraphException during
     * iteration.
     */
    @Test
    void topologicalCycleRaisesDuringIteration() {
        Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("p", "q", "r"));
        g.addEdge("p", "q");
        g.addEdge("q", "r");
        g.addEdge("r", "p");
        assertThrows(NotDirectedAcyclicGraphException.class,
                () -> GraphsFixtures.drain(new TopologicalOrderIterator<>(g)));
    }
}
