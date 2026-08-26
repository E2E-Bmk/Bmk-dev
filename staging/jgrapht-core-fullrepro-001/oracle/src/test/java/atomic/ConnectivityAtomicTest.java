package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;
import java.util.Set;
import org.jgrapht.Graph;
import org.jgrapht.Graphs;
import org.jgrapht.alg.connectivity.ConnectivityInspector;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleGraph;
import org.junit.jupiter.api.Test;

/** Weak-connectivity component reporting. */
class ConnectivityAtomicTest {

    private static Graph<String, DefaultEdge> twoComponents() {
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("g1", "g2", "g3", "g4", "g5"));
        g.addEdge("g1", "g2");
        g.addEdge("g3", "g4");
        return g;
    }

    /**
     * Verifies: Connectivity — isConnected reports whether the graph has
     * exactly one component.
     */
    @Test
    void isConnectedReportsSingleComponent() {
        assertFalse(new ConnectivityInspector<>(twoComponents()).isConnected());
        Graph<String, DefaultEdge> g = new SimpleGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("a", "b"));
        g.addEdge("a", "b");
        assertTrue(new ConnectivityInspector<>(g).isConnected());
    }

    /**
     * Verifies: Connectivity — connectedSets returns the component list and
     * an isolated vertex forms its own singleton component.
     */
    @Test
    void connectedSetsListsComponents() {
        List<Set<String>> sets = new ConnectivityInspector<>(twoComponents()).connectedSets();
        assertEquals(3, sets.size());
        assertTrue(sets.contains(Set.of("g1", "g2")));
        assertTrue(sets.contains(Set.of("g3", "g4")));
        assertTrue(sets.contains(Set.of("g5")));
    }

    /**
     * Verifies: Connectivity — connectedSetOf returns the component
     * containing the given vertex.
     */
    @Test
    void connectedSetOfFindsComponent() {
        ConnectivityInspector<String, DefaultEdge> ci =
                new ConnectivityInspector<>(twoComponents());
        assertEquals(Set.of("g3", "g4"), ci.connectedSetOf("g3"));
        assertEquals(Set.of("g5"), ci.connectedSetOf("g5"));
    }

    /**
     * Verifies: Connectivity — pathExists reports component co-membership.
     */
    @Test
    void pathExistsReportsCoMembership() {
        ConnectivityInspector<String, DefaultEdge> ci =
                new ConnectivityInspector<>(twoComponents());
        assertTrue(ci.pathExists("g1", "g2"));
        assertFalse(ci.pathExists("g1", "g3"));
    }

    /**
     * Verifies: Connectivity — an empty graph reports false and a
     * single-vertex graph reports true.
     */
    @Test
    void degenerateGraphsConnectivity() {
        assertFalse(new ConnectivityInspector<>(
                new SimpleGraph<String, DefaultEdge>(DefaultEdge.class)).isConnected());
        Graph<String, DefaultEdge> single = new SimpleGraph<>(DefaultEdge.class);
        single.addVertex("only");
        assertTrue(new ConnectivityInspector<>(single).isConnected());
    }

    /**
     * Verifies: Connectivity — directed edges are treated as traversable both
     * ways (weak connectivity).
     */
    @Test
    void directedGraphUsesWeakConnectivity() {
        Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
        Graphs.addAllVertices(g, Arrays.asList("d1", "d2"));
        g.addEdge("d1", "d2");
        ConnectivityInspector<String, DefaultEdge> ci = new ConnectivityInspector<>(g);
        assertTrue(ci.isConnected());
        assertTrue(ci.pathExists("d2", "d1"));
    }
}
