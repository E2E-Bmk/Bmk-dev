package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultDirectedWeightedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.jgrapht.graph.DirectedPseudograph;
import org.jgrapht.graph.Pseudograph;
import org.jgrapht.graph.SimpleGraph;
import org.jgrapht.graph.SimpleWeightedGraph;
import org.junit.jupiter.api.Test;

/** Edge weights, degree accounting, and incidence sets. */
class WeightsAndDegreesAtomicTest {

    /**
     * Verifies: Graph Structure and Mutation — an edge never assigned a
     * weight reports the constant DEFAULT_EDGE_WEIGHT of 1.0, on unweighted
     * and weighted graphs alike.
     */
    @Test
    void defaultWeightIsOne() {
        assertEquals(1.0, Graph.DEFAULT_EDGE_WEIGHT);
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        assertEquals(1.0, g.getEdgeWeight(g.addEdge("a", "b")));

        Graph<String, DefaultWeightedEdge> w = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
        w.addVertex("a");
        w.addVertex("b");
        assertEquals(1.0, w.getEdgeWeight(w.addEdge("a", "b")));
    }

    /**
     * Verifies: Graph Structure and Mutation — setEdgeWeight assigns the
     * weight on a weighted graph and getEdgeWeight reads it back.
     */
    @Test
    void setEdgeWeightAssigns() {
        Graph<String, DefaultWeightedEdge> w = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
        w.addVertex("p");
        w.addVertex("q");
        DefaultWeightedEdge e = w.addEdge("p", "q");
        w.setEdgeWeight(e, 3.5);
        assertEquals(3.5, w.getEdgeWeight(e));
    }

    /**
     * Verifies: Graph Structure and Mutation — the endpoint-pair overload of
     * setEdgeWeight assigns to the connecting edge.
     */
    @Test
    void setEdgeWeightByPairAssigns() {
        Graph<String, DefaultWeightedEdge> w =
                new DefaultDirectedWeightedGraph<>(DefaultWeightedEdge.class);
        w.addVertex("x");
        w.addVertex("y");
        DefaultWeightedEdge e = w.addEdge("x", "y");
        w.setEdgeWeight("x", "y", 9.0);
        assertEquals(9.0, w.getEdgeWeight(e));
    }

    /**
     * Verifies: Error Semantics — setEdgeWeight on an unweighted graph raises
     * UnsupportedOperationException.
     */
    @Test
    void setEdgeWeightUnweightedRaises() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        g.addVertex("a");
        g.addVertex("b");
        DefaultEdge e = g.addEdge("a", "b");
        assertThrows(UnsupportedOperationException.class, () -> g.setEdgeWeight(e, 5.0));
    }

    /**
     * Verifies: Graph Structure and Mutation — in a directed graph degreeOf
     * is the sum of inDegreeOf and outDegreeOf, and the incidence sets split
     * by direction.
     */
    @Test
    void directedDegreesSplitByDirection() {
        Graph<String, DefaultEdge> d = new DefaultDirectedGraph<>(DefaultEdge.class);
        d.addVertex("x");
        d.addVertex("y");
        d.addVertex("z");
        d.addEdge("x", "y");
        d.addEdge("x", "z");
        d.addEdge("y", "x");
        assertEquals(3, d.degreeOf("x"));
        assertEquals(1, d.inDegreeOf("x"));
        assertEquals(2, d.outDegreeOf("x"));
        assertEquals(3, d.edgesOf("x").size());
        assertEquals(1, d.incomingEdgesOf("x").size());
        assertEquals(2, d.outgoingEdgesOf("x").size());
    }

    /**
     * Verifies: Graph Structure and Mutation — a self-loop contributes 2 to
     * degreeOf while appearing once in edgesOf, in undirected and directed
     * classes.
     */
    @Test
    void selfLoopCountsTwiceInDegree() {
        Graph<String, DefaultEdge> u = new Pseudograph<>(DefaultEdge.class);
        u.addVertex("s");
        u.addEdge("s", "s");
        assertEquals(2, u.degreeOf("s"));
        assertEquals(1, u.edgesOf("s").size());

        Graph<String, DefaultEdge> d = new DirectedPseudograph<>(DefaultEdge.class);
        d.addVertex("t");
        d.addEdge("t", "t");
        assertEquals(2, d.degreeOf("t"));
        assertEquals(1, d.inDegreeOf("t"));
        assertEquals(1, d.outDegreeOf("t"));
    }
}
