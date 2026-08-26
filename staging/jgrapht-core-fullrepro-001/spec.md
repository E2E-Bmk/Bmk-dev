# Graph Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jgrapht-core` is a graph-theory library that models directed and undirected graphs over arbitrary vertex and edge object types and provides views, traversals, and algorithms over them. A graph holds one authoritative structure — a vertex set, an edge set, per-edge endpoints, and per-edge weights — and every other public object is a projection of that structure: unmodifiable and reversed views, subgraph windows, breadth-first / depth-first / topological iterators, shortest-path results, and connectivity reports.

The library enforces a per-class structural discipline. Each concrete graph class declares whether it is directed, whether it permits self-loops, whether it permits multiple edges between the same endpoint pair, and whether it is weighted; every mutation is admitted or refused according to that declaration. Collections the library maintains iterate in deterministic insertion order, so graph traversal results are reproducible run to run.

The installable artifact is the Maven coordinate `org.jgrapht:jgrapht-core`.

## Non-Goals

- This specification does not require graph generators, random graphs, or graph products.
- This specification does not require isomorphism testing, matching, coloring, clique, flow, spanning-tree, or centrality algorithms.
- This specification does not require import/export in GraphML, DOT, CSV, or any serialization format.
- This specification does not require listenable graphs, concurrent graphs, graph builders, or the fluent type-builder facility.
- This specification does not require shortest-path algorithms beyond the two named in this document, nor strong-connectivity inspection of directed graphs.
- This specification does not define thread-safety guarantees; graphs are single-threaded structures.

## Representative Workflows

**Build a weighted graph and query a shortest path.**

```java
Graph<String, DefaultWeightedEdge> g = new SimpleWeightedGraph<>(DefaultWeightedEdge.class);
g.addVertex("a");
g.addVertex("b");
g.addVertex("c");
g.setEdgeWeight(g.addEdge("a", "b"), 1.0);
g.setEdgeWeight(g.addEdge("b", "c"), 2.0);
g.setEdgeWeight(g.addEdge("a", "c"), 9.0);

DijkstraShortestPath<String, DefaultWeightedEdge> alg = new DijkstraShortestPath<>(g);
GraphPath<String, DefaultWeightedEdge> path = alg.getPath("a", "c");
path.getWeight();      // 3.0
path.getVertexList();  // [a, b, c]
path.getLength();      // 2 (edge count)
```

**Traverse a directed graph and inspect connectivity.**

```java
Graph<String, DefaultEdge> g = new DefaultDirectedGraph<>(DefaultEdge.class);
Graphs.addEdgeWithVertices(g, "root", "left");
Graphs.addEdgeWithVertices(g, "root", "right");
Graphs.addEdgeWithVertices(g, "left", "leaf");

BreadthFirstIterator<String, DefaultEdge> it = new BreadthFirstIterator<>(g, "root");
while (it.hasNext()) {
    String v = it.next();          // root, left, right, leaf
}
it.getDepth("leaf");               // 2
it.getParent("leaf");              // left

ConnectivityInspector<String, DefaultEdge> ci = new ConnectivityInspector<>(g);
ci.isConnected();                  // true (weak connectivity)
ci.connectedSets();                // [[root, left, right, leaf]]
```

## Graph Structure and Mutation

The `Graph<V, E>` interface is the single mutation and query surface shared by every graph class and view; vertices and edges are caller-supplied objects tracked by the graph.

**Vertices.** `addVertex(V v)` inserts a vertex and returns `true`; when the vertex is already present it returns `false` and the graph is unchanged. `containsVertex(V v)` reports membership. `removeVertex(V v)` removes the vertex together with every edge that touches it and returns `true`, or returns `false` when the vertex was not present. `vertexSet()` returns the set of vertices, iterating in insertion order.

**Edges.** `addEdge(V sourceVertex, V targetVertex)` creates a new edge object, connects it, and returns it. Both endpoints must already be vertices of the graph: if either endpoint is absent, the call must raise `IllegalArgumentException`; if either endpoint is `null`, it must raise `NullPointerException`. When the class-level structural rules refuse the edge silently (a duplicate endpoint pair in a class that forbids multiple edges), `addEdge` returns `null` and the graph is unchanged. `getEdge(V sourceVertex, V targetVertex)` returns the connecting edge or `null` when no such edge (or either vertex) exists; in an undirected graph the endpoint order is irrelevant. `containsEdge(V sourceVertex, V targetVertex)` reports whether a connecting edge exists. `removeEdge(V sourceVertex, V targetVertex)` removes and returns the connecting edge, or returns `null` when there is none; `removeEdge(E e)` removes the given edge object and returns whether the graph changed. `edgeSet()` returns all edges in insertion order. `getEdgeSource(E e)` and `getEdgeTarget(E e)` return the endpoints an edge was created with.

**Incidence and degree.** `edgesOf(V v)` returns every edge touching the vertex. In a directed graph, `incomingEdgesOf(V v)` and `outgoingEdgesOf(V v)` split that set by direction, `inDegreeOf(V v)` and `outDegreeOf(V v)` count each side, and `degreeOf(V v)` is their sum. A self-loop contributes 2 to `degreeOf` in every graph class (one incoming plus one outgoing in the directed case) while appearing exactly once in `edgesOf`.

**Weights.** Every edge carries a `double` weight, and `getEdgeWeight(E e)` returns it; an edge that has never been assigned a weight reports the constant `Graph.DEFAULT_EDGE_WEIGHT` (1.0). On a weighted graph, `setEdgeWeight(E e, double weight)` assigns a weight, and `setEdgeWeight(V sourceVertex, V targetVertex, double weight)` assigns it to the edge connecting the pair. On an unweighted graph, `setEdgeWeight` must raise `UnsupportedOperationException`.

**Type introspection.** `getType()` returns a `GraphType` describing the class-level discipline: `isDirected()`, `isUndirected()`, `isWeighted()`, `isAllowingSelfLoops()`, `isAllowingMultipleEdges()`, and `isModifiable()`.

**Bulk helpers.** The `Graphs` utility class provides `addEdgeWithVertices(Graph<V, E> g, V sourceVertex, V targetVertex)`, which inserts missing endpoints before connecting them and returns the new edge; `addAllVertices(Graph<V, E> g, Collection<? extends V> vertices)`, which inserts each vertex and returns whether the graph changed; `neighborListOf(Graph<V, E> g, V vertex)`, listing adjacent vertices; and, for directed graphs, `successorListOf(Graph<V, E> g, V vertex)` and `predecessorListOf(Graph<V, E> g, V vertex)`.

## Graph Classes and Structural Rules

Each concrete class fixes one row of the structural matrix; all classes share the `Graph` interface behavior above. Every class in scope is constructed from the edge class, as in `new SimpleGraph<>(DefaultEdge.class)`.

**The structural matrix.** The eight unweighted classes must declare and enforce exactly these rules:

| Class | Directed | Self-loops | Multiple edges |
|---|---|---|---|
| `SimpleGraph` | no | no | no |
| `SimpleDirectedGraph` | yes | no | no |
| `Multigraph` | no | no | yes |
| `DirectedMultigraph` | yes | no | yes |
| `Pseudograph` | no | yes | yes |
| `DirectedPseudograph` | yes | yes | yes |
| `DefaultUndirectedGraph` | no | yes | no |
| `DefaultDirectedGraph` | yes | yes | no |

**Enforcement.** The two refusals behave differently, in every class:

- WHEN `addEdge(v, v)` proposes a self-loop and the class forbids self-loops, THEN the call must raise `IllegalArgumentException`.
- WHEN `addEdge(u, v)` proposes a second edge over an endpoint pair already connected and the class forbids multiple edges, THEN the call must return `null` and leave the graph unchanged.
- Where the class permits the structure, the edge is created normally: a multigraph accumulates parallel edges (each a distinct edge object counted separately in `edgeSet()`), and a pseudograph additionally accepts self-loops.

In an undirected class, the pair (u, v) and the pair (v, u) are the same endpoint pair for multiplicity purposes.

**Weighted classes.** `SimpleWeightedGraph`, `SimpleDirectedWeightedGraph`, and `DefaultDirectedWeightedGraph` mirror `SimpleGraph`, `SimpleDirectedGraph`, and `DefaultDirectedGraph` respectively, with `isWeighted()` true and `setEdgeWeight` enabled. They are used with the `DefaultWeightedEdge` edge class. A newly added edge carries weight 1.0 until assigned.

**Edge classes.** `DefaultEdge` and `DefaultWeightedEdge` are library-provided edge types whose `toString()` renders as `(source : target)`. Callers treat them as opaque handles; identity, not value equality, distinguishes parallel edges.

**Determinism.** `vertexSet()` and `edgeSet()` iterate in insertion order in every graph class in scope. Traversal iterators examine the outgoing edges of a vertex in edge insertion order, which makes the traversal orders in the next sections reproducible.

## Graph Views

A view is a `Graph` that presents a transformed reading of a backing graph without copying it. Views share the backing graph's vertex and edge objects.

**Unmodifiable view.** `AsUnmodifiableGraph(Graph<V, E> g)` presents the backing graph read-only: every mutator (`addVertex`, `addEdge`, `removeVertex`, `removeEdge`, `setEdgeWeight`) must raise `UnsupportedOperationException`, all queries delegate to the backing graph, and mutations applied directly to the backing graph are visible through the view immediately. Its `getType().isModifiable()` reports `false`.

**Edge-reversed view.** `EdgeReversedGraph(Graph<V, E> g)` presents a directed backing graph with every edge's direction flipped: `getEdgeSource` and `getEdgeTarget` swap, `incomingEdgesOf` and `outgoingEdgesOf` swap (as do the corresponding degree methods), and `getEdge(u, v)` on the view finds the backing edge from `v` to `u`. The view is a live, writable window: `addEdge(u, v)` on the view creates the backing edge from `v` to `u`.

**Subgraph window.** `AsSubgraph(Graph<V, E> g, Set<? extends V> vertexSubset)` materializes the induced subgraph over the given vertices: it contains each backing edge whose two endpoints are both in the subset, computed at construction time. A three-argument form `AsSubgraph(Graph<V, E> g, Set<? extends V> vertexSubset, Set<? extends E> edgeSubset)` restricts the edge set further; passing `null` for the edge subset selects the induced form. The subgraph tracks its own membership sets after construction: backing-graph edges added later are not absorbed automatically, `addEdge(u, v)` on the subgraph admits the backing edge connecting that pair into the window (if the backing graph has no such edge the call must raise `IllegalArgumentException`), and `removeEdge` on the subgraph removes the edge from the window while leaving the backing graph untouched.

**Masked view.** `MaskSubgraph(Graph<V, E> g, Predicate<V> vertexMask, Predicate<E> edgeMask)` presents the backing graph with every vertex satisfying the vertex mask hidden, every edge satisfying the edge mask hidden, and every edge with a hidden endpoint hidden as well. The mask is evaluated live: mutations to the backing graph are visible through the mask immediately, subject to the predicates. The masked view itself is read-only — its mutators must raise `UnsupportedOperationException`.

## Traversal Iterators

Traversal iterators implement `java.util.Iterator<V>` over the vertices of a graph and follow outgoing edges in edge insertion order.

**Breadth-first.** `BreadthFirstIterator(Graph<V, E> g, V startVertex)` returns vertices in nondecreasing distance from the start: the start first, then all vertices one edge away in discovery order, and so on. After a vertex has been returned, `getDepth(V v)` reports its distance in edges from the start (0 for the start itself) and `getParent(V v)` reports the vertex from which it was discovered (`null` for the start). The single-argument form `BreadthFirstIterator(Graph<V, E> g)` covers the whole graph, starting from the first vertex in insertion order and restarting on each remaining unvisited component. If the given start vertex is not in the graph, the constructor must raise `IllegalArgumentException`.

**Depth-first.** `DepthFirstIterator(Graph<V, E> g, V startVertex)` returns vertices in depth-first order under LIFO discipline: the vertex discovered most recently is expanded next, so among several unvisited neighbors of a vertex, the one whose connecting edge was inserted last is returned first. A single-argument whole-graph form exists as for breadth-first. Each reachable vertex is returned exactly once.

**Topological.** `TopologicalOrderIterator(Graph<V, E> g)` returns the vertices of a directed acyclic graph in an order where every vertex appears after all vertices with an edge into it. If the graph is undirected, the constructor must raise `IllegalArgumentException`. If the graph contains a cycle, iteration must raise `NotDirectedAcyclicGraphException` — an `IllegalArgumentException` subclass — when the cycle makes further ordering impossible.

**Traversal over undirected graphs.** Breadth-first and depth-first iterators treat an undirected edge as traversable in both directions.

## Shortest Paths

Shortest-path algorithms consume a graph and produce `GraphPath` results; edge weights are read through `getEdgeWeight`, so unweighted graphs behave as uniformly weighted at 1.0.

**Dijkstra.** `DijkstraShortestPath(Graph<V, E> graph)` answers single-pair and single-source queries on graphs with non-negative weights. `getPath(V source, V sink)` returns the minimum-weight path as a `GraphPath`, or `null` when the sink is unreachable. WHEN the query is `getPath(v, v)`, THEN the result is the empty path at `v`: weight 0.0, length 0, vertex list `[v]`, empty edge list. `getPaths(V source)` returns a `ShortestPathAlgorithm.SingleSourcePaths` handle whose `getPath(V sink)` and `getWeight(V sink)` answer per-sink queries; for an unreachable sink, `getWeight` returns `Double.POSITIVE_INFINITY` and `getPath` returns `null`. If a negative edge weight is encountered, the algorithm must raise `IllegalArgumentException`. If the source or sink vertex is not in the graph, `getPath` must raise `IllegalArgumentException`. The static convenience `DijkstraShortestPath.findPathBetween(Graph<V, E> graph, V source, V sink)` answers a one-shot single-pair query. In an undirected graph each edge is traversable in both directions.

**Bellman-Ford.** `BellmanFordShortestPath(Graph<V, E> graph)` supports the same `getPath` / `getPaths` surface but admits negative edge weights. If the graph contains a negative-weight cycle reachable from the queried source, the algorithm must raise `NegativeCycleDetectedException`. An unreachable sink yields `null`, as for Dijkstra.

**Path objects.** A `GraphPath<V, E>` reports `getStartVertex()`, `getEndVertex()`, `getVertexList()` (start to end inclusive), `getEdgeList()` (the traversed edges in order), `getLength()` (the edge count), `getWeight()` (the sum of traversed edge weights), and `getGraph()` (the graph the path lives in).

## Connectivity

`ConnectivityInspector(Graph<V, E> g)` reports the connected components of a graph, treating directed edges as traversable both ways (weak connectivity).

**Queries.** `isConnected()` returns whether the graph has exactly one connected component; an empty graph reports `false` and a single-vertex graph reports `true`. `connectedSets()` returns the list of components, each a vertex set. `connectedSetOf(V vertex)` returns the component containing the given vertex. `pathExists(V sourceVertex, V targetVertex)` returns whether the two vertices lie in the same component. An isolated vertex forms its own singleton component.

## State Model

The graph — vertex set, edge set, endpoints, weights, plus the class-level structural declaration — is the single authoritative state. All other objects project it:

- Views (`AsUnmodifiableGraph`, `EdgeReversedGraph`, `MaskSubgraph`) read the backing graph live; `AsSubgraph` snapshots membership at construction and tracks its own window afterwards.
- Iterators and algorithms read the graph at traversal/query time; they never mutate it.
- `GraphPath` and connectivity results are values computed from the graph state at call time.
- Mutations flow through the `Graph` interface only, and each is admitted or refused per the owning class's structural declaration before any state changes.

## Error Semantics

| Condition | Required result |
|---|---|
| `addEdge` with an endpoint not in the graph | `IllegalArgumentException` |
| `addEdge` with a `null` endpoint | `NullPointerException` |
| `addEdge` proposing a self-loop where forbidden | `IllegalArgumentException` |
| `addEdge` proposing a parallel edge where forbidden | returns `null` (no exception) |
| `setEdgeWeight` on an unweighted graph | `UnsupportedOperationException` |
| Mutator on `AsUnmodifiableGraph` or `MaskSubgraph` | `UnsupportedOperationException` |
| `AsSubgraph.addEdge` for a pair with no backing edge | `IllegalArgumentException` |
| Traversal start vertex not in the graph | `IllegalArgumentException` |
| `TopologicalOrderIterator` over an undirected graph | `IllegalArgumentException` |
| `TopologicalOrderIterator` over a cyclic directed graph | `NotDirectedAcyclicGraphException` during iteration |
| Dijkstra encountering a negative edge weight | `IllegalArgumentException` |
| Dijkstra `getPath` with source or sink absent | `IllegalArgumentException` |
| Bellman-Ford with a reachable negative cycle | `NegativeCycleDetectedException` |

Non-error conditions: `addVertex` of a present vertex returns `false`; `addEdge` refused by multiplicity returns `null`; `getEdge` / `removeEdge(V, V)` with no connecting edge return `null`; `removeVertex` / `removeEdge(E)` of absent elements return `false`; an unreachable shortest-path sink yields `null` (and `Double.POSITIVE_INFINITY` from `SingleSourcePaths.getWeight`).

## Cross-View Invariants

1. Every view agrees with its backing graph: a query answered through `AsUnmodifiableGraph` must equal the same query on the backing graph at the same moment, and `EdgeReversedGraph` must answer `getEdgeSource`/`getEdgeTarget`/`incomingEdgesOf`/`outgoingEdgesOf` exactly as the backing graph answers the opposite member of each pair.
2. The structural matrix and `getType()` must agree with `addEdge` behavior: a class whose type reports `isAllowingSelfLoops()` false must raise on self-loop insertion, and one whose type reports `isAllowingMultipleEdges()` false must return `null` on duplicate insertion.
3. For every graph, `degreeOf(v)` must equal `inDegreeOf(v) + outDegreeOf(v)` in directed classes, and the sum of `degreeOf` over all vertices must equal twice `edgeSet().size()` (self-loops counted twice) in every class.
4. A breadth-first traversal must agree with shortest paths on unweighted graphs: `getDepth(v)` must equal the `getLength()` of the Dijkstra path to `v` in the same graph, and following `getParent` links from `v` back to the start must produce a path of exactly `getDepth(v)` edges.
5. `ConnectivityInspector.pathExists(u, v)` must be true exactly when Dijkstra (over the undirected reading of the graph) finds a non-`null` path from `u` to `v`, and the union of `connectedSets()` must equal `vertexSet()` with the sets pairwise disjoint.
6. A `GraphPath` must be internally consistent: `getLength()` equals the size of `getEdgeList()`, `getVertexList()` has exactly `getLength() + 1` elements beginning with `getStartVertex()` and ending with `getEndVertex()`, and `getWeight()` equals the sum of `getEdgeWeight` over `getEdgeList()`.
7. A topological order must respect every edge: for each edge (u, v) of a DAG, u must appear before v in the iteration; and removing a vertex through the `Graph` interface must remove its incident edges from every live view over that graph.
8. `AsSubgraph` construction must be exactly induced: an edge of the backing graph belongs to the fresh subgraph if and only if both endpoints are in the vertex subset (when no edge subset is given).

## Public Interface

### Import Surface

```java
import org.jgrapht.Graph;
import org.jgrapht.GraphPath;
import org.jgrapht.GraphType;
import org.jgrapht.Graphs;
import org.jgrapht.alg.connectivity.ConnectivityInspector;
import org.jgrapht.alg.interfaces.ShortestPathAlgorithm;
import org.jgrapht.alg.shortestpath.BellmanFordShortestPath;
import org.jgrapht.alg.shortestpath.DijkstraShortestPath;
import org.jgrapht.alg.shortestpath.NegativeCycleDetectedException;
import org.jgrapht.graph.AsSubgraph;
import org.jgrapht.graph.AsUnmodifiableGraph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultDirectedWeightedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.DefaultUndirectedGraph;
import org.jgrapht.graph.DefaultWeightedEdge;
import org.jgrapht.graph.DirectedMultigraph;
import org.jgrapht.graph.DirectedPseudograph;
import org.jgrapht.graph.EdgeReversedGraph;
import org.jgrapht.graph.MaskSubgraph;
import org.jgrapht.graph.Multigraph;
import org.jgrapht.graph.Pseudograph;
import org.jgrapht.graph.SimpleDirectedGraph;
import org.jgrapht.graph.SimpleDirectedWeightedGraph;
import org.jgrapht.graph.SimpleGraph;
import org.jgrapht.graph.SimpleWeightedGraph;
import org.jgrapht.traverse.BreadthFirstIterator;
import org.jgrapht.traverse.DepthFirstIterator;
import org.jgrapht.traverse.NotDirectedAcyclicGraphException;
import org.jgrapht.traverse.TopologicalOrderIterator;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `Graph<V, E>` | `boolean addVertex(V v)`; `E addEdge(V sourceVertex, V targetVertex)`; `boolean containsVertex(V v)`; `boolean containsEdge(V sourceVertex, V targetVertex)`; `E getEdge(V sourceVertex, V targetVertex)`; `boolean removeVertex(V v)`; `E removeEdge(V sourceVertex, V targetVertex)`; `boolean removeEdge(E e)`; `Set<V> vertexSet()`; `Set<E> edgeSet()`; `Set<E> edgesOf(V vertex)`; `Set<E> incomingEdgesOf(V vertex)`; `Set<E> outgoingEdgesOf(V vertex)`; `int degreeOf(V vertex)`; `int inDegreeOf(V vertex)`; `int outDegreeOf(V vertex)`; `V getEdgeSource(E e)`; `V getEdgeTarget(E e)`; `double getEdgeWeight(E e)`; `void setEdgeWeight(E e, double weight)`; `void setEdgeWeight(V sourceVertex, V targetVertex, double weight)`; `GraphType getType()`; constant `double DEFAULT_EDGE_WEIGHT = 1.0` |
| `GraphType` | `boolean isDirected()`; `boolean isUndirected()`; `boolean isWeighted()`; `boolean isAllowingSelfLoops()`; `boolean isAllowingMultipleEdges()`; `boolean isModifiable()` |
| `Graphs` | `static <V, E> E addEdgeWithVertices(Graph<V, E> g, V sourceVertex, V targetVertex)`; `static <V, E> boolean addAllVertices(Graph<V, E> g, Collection<? extends V> vertices)`; `static <V, E> List<V> neighborListOf(Graph<V, E> g, V vertex)`; `static <V, E> List<V> successorListOf(Graph<V, E> g, V vertex)`; `static <V, E> List<V> predecessorListOf(Graph<V, E> g, V vertex)` |
| concrete graph classes | each is constructed as `ClassName(Class<? extends E> edgeClass)`, e.g. `new SimpleGraph<>(DefaultEdge.class)` |
| `DefaultEdge` / `DefaultWeightedEdge` | no-argument construction by the graph; `String toString()` renders `(source : target)` |
| `AsUnmodifiableGraph<V, E>` | `AsUnmodifiableGraph(Graph<V, E> g)` |
| `EdgeReversedGraph<V, E>` | `EdgeReversedGraph(Graph<V, E> g)` |
| `AsSubgraph<V, E>` | `AsSubgraph(Graph<V, E> base, Set<? extends V> vertexSubset)`; `AsSubgraph(Graph<V, E> base, Set<? extends V> vertexSubset, Set<? extends E> edgeSubset)` |
| `MaskSubgraph<V, E>` | `MaskSubgraph(Graph<V, E> base, Predicate<V> vertexMask, Predicate<E> edgeMask)` |
| `BreadthFirstIterator<V, E>` | `BreadthFirstIterator(Graph<V, E> g)`; `BreadthFirstIterator(Graph<V, E> g, V startVertex)`; `boolean hasNext()`; `V next()`; `int getDepth(V v)`; `V getParent(V v)` |
| `DepthFirstIterator<V, E>` | `DepthFirstIterator(Graph<V, E> g)`; `DepthFirstIterator(Graph<V, E> g, V startVertex)`; `boolean hasNext()`; `V next()` |
| `TopologicalOrderIterator<V, E>` | `TopologicalOrderIterator(Graph<V, E> g)`; `boolean hasNext()`; `V next()` |
| `DijkstraShortestPath<V, E>` | `DijkstraShortestPath(Graph<V, E> graph)`; `GraphPath<V, E> getPath(V source, V sink)`; `ShortestPathAlgorithm.SingleSourcePaths<V, E> getPaths(V source)`; `static <V, E> GraphPath<V, E> findPathBetween(Graph<V, E> graph, V source, V sink)` |
| `BellmanFordShortestPath<V, E>` | `BellmanFordShortestPath(Graph<V, E> graph)`; `GraphPath<V, E> getPath(V source, V sink)`; `ShortestPathAlgorithm.SingleSourcePaths<V, E> getPaths(V source)` |
| `ShortestPathAlgorithm.SingleSourcePaths<V, E>` | `GraphPath<V, E> getPath(V sink)`; `double getWeight(V sink)` |
| `GraphPath<V, E>` | `V getStartVertex()`; `V getEndVertex()`; `List<V> getVertexList()`; `List<E> getEdgeList()`; `int getLength()`; `double getWeight()`; `Graph<V, E> getGraph()` |
| `ConnectivityInspector<V, E>` | `ConnectivityInspector(Graph<V, E> g)`; `boolean isConnected()`; `List<Set<V>> connectedSets()`; `Set<V> connectedSetOf(V vertex)`; `boolean pathExists(V sourceVertex, V targetVertex)` |
| `NegativeCycleDetectedException` | unchecked; raised on reachable negative-weight cycles |
| `NotDirectedAcyclicGraphException` | extends `IllegalArgumentException`; raised on cyclic topological iteration |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Graph` | interface | Mutation and query surface of every graph. |
| `GraphType` | interface | Class-level structural declaration. |
| `Graphs` | class | Static bulk helpers over graphs. |
| `SimpleGraph` | class | Undirected; no loops; no multiple edges. |
| `SimpleDirectedGraph` | class | Directed; no loops; no multiple edges. |
| `Multigraph` | class | Undirected; no loops; multiple edges. |
| `DirectedMultigraph` | class | Directed; no loops; multiple edges. |
| `Pseudograph` | class | Undirected; loops; multiple edges. |
| `DirectedPseudograph` | class | Directed; loops; multiple edges. |
| `DefaultUndirectedGraph` | class | Undirected; loops; no multiple edges. |
| `DefaultDirectedGraph` | class | Directed; loops; no multiple edges. |
| `SimpleWeightedGraph` | class | Weighted `SimpleGraph`. |
| `SimpleDirectedWeightedGraph` | class | Weighted `SimpleDirectedGraph`. |
| `DefaultDirectedWeightedGraph` | class | Weighted `DefaultDirectedGraph`. |
| `DefaultEdge` | class | Unweighted edge object. |
| `DefaultWeightedEdge` | class | Weighted edge object. |
| `AsUnmodifiableGraph` | class | Read-only live view. |
| `EdgeReversedGraph` | class | Direction-flipped live view. |
| `AsSubgraph` | class | Vertex/edge-subset window. |
| `MaskSubgraph` | class | Predicate-masked live view. |
| `BreadthFirstIterator` | class | Level-order vertex iterator with depth/parent queries. |
| `DepthFirstIterator` | class | Depth-first vertex iterator. |
| `TopologicalOrderIterator` | class | DAG precedence-order iterator. |
| `DijkstraShortestPath` | class | Non-negative-weight shortest paths. |
| `BellmanFordShortestPath` | class | Negative-weight-tolerant shortest paths. |
| `ShortestPathAlgorithm` | interface | Algorithm surface; hosts `SingleSourcePaths`. |
| `GraphPath` | interface | Path value: vertices, edges, length, weight. |
| `ConnectivityInspector` | class | Weak-connectivity component reporting. |
| `NegativeCycleDetectedException` | exception | Reachable negative cycle. |
| `NotDirectedAcyclicGraphException` | exception | Cycle found during topological iteration. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; the target artifact's own declared dependencies resolve through Maven. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.jgrapht:jgrapht-core`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the documented behaviors through the public API: per-class structural rule enforcement across the full matrix, mutation and query semantics of the `Graph` interface, view consistency with backing graphs, traversal orders and depth/parent reporting, shortest-path results and their declared error paths, connectivity reporting, and the cross-view invariants above. Tests construct their own small graphs through the documented constructors; no fixture files are involved. Both individual behaviors and multi-step scenarios (mutate, view, traverse, query) are measured.
