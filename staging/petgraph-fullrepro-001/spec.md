<!-- INTERNAL
task_id: petgraph-fullrepro-001
spec_version: v1
delta: initial version; DFS child-exploration order corrected to reverse
neighbor order (probe-verified) before oracle authorship
source_boundary: docs.rs/petgraph 0.8.3 (crate root, graph/stable_graph/graphmap module docs, visit module docs, algo module and per-function docs, data module docs), README at pinned commit; reference behavior observed by running the pinned checkout (probe binary)
-->

# Graph Data Structure Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`petgraph` is a Rust graph library built around one fact source — a store
of weighted nodes and weighted edges with a directionality parameter — and
several public projections of it: an index-based adjacency-list graph, a
stable-index variant that preserves indices across removals, a keyed graph
whose nodes are their own identifiers, a family of lazy traversal visitors,
view adapters that reverse or filter a graph without copying it, and an
algorithm suite (connectivity, cycle detection, topological sorting,
strongly connected components, condensation, shortest paths, minimum
spanning trees) that consumes any of those views through a common trait
layer.

Graphs are parameterized over node weights, edge weights, and edge type
(`Directed` or `Undirected`). The library's contracts are precise about
index semantics: which operations invalidate which indices, in what order
neighbors are produced, and how stable and keyed containers differ from the
compact index-based one. Algorithms are generic: anything that implements
the visit traits — including reversed and filtered adapters wrapping another
graph — is a valid input.

## Non-Goals

- This specification does not require matrix-backed, CSR, adjacency-list
  (`adj`), or acyclic-enforcing graph containers; only the three containers
  described below are in scope.
- This specification does not require graph isomorphism, matching, maximum
  flow, PageRank, Steiner trees, dominators, bridges, articulation points,
  coloring, transitive reduction, simple-path enumeration, k-shortest
  paths, Floyd–Warshall, Johnson, SPFA, or feedback-arc-set algorithms.
- This specification does not require DOT-format export or parsing, graph6
  encoding, serde serialization, rayon parallelism, quickcheck integration,
  or random graph generators.
- This specification does not require cargo feature gates: every behavior
  described here must be available with the crate's default configuration.
- This specification does not define the iteration order of hash-map-valued
  algorithm results; only their contents are contractual.

## Representative Workflows

**Build, mutate, and query an index-based graph.** Nodes and edges are
created through the mutation API, addressed by the returned indices, and
inspected through weight accessors and adjacency queries:

```rust
use petgraph::prelude::*;

let mut g: DiGraph<&str, u32> = DiGraph::new();
let hub = g.add_node("hub");
let east = g.add_node("east");
let west = g.add_node("west");
g.add_edge(hub, east, 5);
g.add_edge(hub, west, 9);
assert_eq!(g[hub], "hub");
assert_eq!(g.node_count(), 3);
// Most recently added edge's neighbor is listed first.
let order: Vec<_> = g.neighbors(hub).collect();
assert_eq!(order, vec![west, east]);
```

**Run algorithms over the same store.** The algorithm layer projects the
container's state without mutating it; topological order and shortest-path
costs are two views of one edge set:

```rust
use petgraph::algo::{dijkstra, toposort};
use petgraph::prelude::*;

let mut g: DiGraph<(), u32> = DiGraph::new();
let a = g.add_node(());
let b = g.add_node(());
let c = g.add_node(());
g.add_edge(a, b, 4);
g.add_edge(b, c, 3);
g.add_edge(a, c, 10);
let order = toposort(&g, None).unwrap();
assert_eq!(order.len(), 3);
let costs = dijkstra(&g, a, None, |e| *e.weight());
assert_eq!(costs.get(&c), Some(&7));
```

**Traverse through a view adapter.** Visitors are lazy walkers that borrow
the graph only per step; adapters like `Reversed` change the edge direction
every consumer sees without copying the graph:

```rust
use petgraph::prelude::*;
use petgraph::visit::Reversed;

let mut g: DiGraph<(), ()> = DiGraph::new();
let s = g.add_node(());
let t = g.add_node(());
g.add_edge(s, t, ());
let mut walker = Bfs::new(Reversed(&g), t);
let mut seen = Vec::new();
while let Some(n) = walker.next(Reversed(&g)) {
    seen.push(n);
}
assert_eq!(seen, vec![t, s]);
```

## Graph Construction and Mutation

This section defines the compact index-based container `Graph` and its
mutation contract, including the index-invalidation rules that distinguish
it from the stable variant.

**The container.** `Graph` is parameterized over a node weight type, an
edge weight type, an edge type (`Directed`, the default, or `Undirected`),
and an index size type defaulting to 32-bit. The type aliases `DiGraph` and
`UnGraph` fix the edge type to directed and undirected respectively.
`Graph::new` creates an empty directed graph; `Graph::new_undirected`
creates an empty undirected one; `with_capacity` accepts expected node and
edge counts. `node_count` and `edge_count` return the current totals;
`is_directed` reports the edge type. Node weights need no trait bounds for
the container itself; weights are owned by the graph and returned by
removal. Parallel (duplicate) edges between the same endpoints are allowed;
self-loops are allowed.

**Adding.** `add_node` accepts a weight and returns the new `NodeIndex`;
indices count up from zero in insertion order. `add_edge` accepts a source
index, target index, and weight, and returns a new `EdgeIndex`, also
counting up from zero; it always creates a new edge, even when a parallel
edge already exists. If either endpoint does not exist, `add_edge` must
panic. `update_edge` accepts the same arguments but first looks for an
existing edge between the endpoints (the edge that `find_edge` would
return); when found, it replaces that edge's weight and returns the
existing index, otherwise it adds a new edge. `extend_with_edges` accepts
an iterable of edge descriptors — `(a, b)` pairs or `(a, b, weight)`
triples, with node references given as indices or as unsigned integers —
and creates any missing nodes with default node weights up to the largest
mentioned index. `from_edges` builds a new graph the same way.

**Removing and the swap contract.** `remove_node` accepts a node index and
returns the node's weight, or `None` when no such node exists. Removal
first removes every edge with an endpoint in the node, then removes the
node by swapping the last node into the vacated index: apart from the
removed index, the index of the previously-last node is invalidated — that
node adopts the removed node's index — and node count shrinks by one.
`remove_edge` returns the edge's weight (or `None`) and applies the same
swap rule to edge indices: the last edge adopts the removed edge index.
Any code holding indices across a removal must account for both rules.
`clear` removes all nodes and edges; `clear_edges` removes all edges and
keeps nodes. `retain_nodes` and `retain_edges` accept a predicate over the
graph and an index, and remove every element the predicate rejects,
applying the same swap-removal semantics element by element.

**Transforming.** `map` accepts two closures, one mapping each node index
and weight to a new node weight and one mapping each edge index and weight
to a new edge weight, and returns a new graph with identical structure.
`filter_map` accepts closures returning options; a node mapped to `None` is
dropped together with all its edges, and an edge mapped to `None` is
dropped; surviving nodes are re-indexed compactly in their original order.
`reverse` flips the direction of every edge in place. `into_graph` does not
exist on `Graph`; conversions belong to the keyed container described
below.

**Weight access.** `node_weight` and `edge_weight` return `Some(&weight)`
for live indices and `None` otherwise, with `_mut` variants for mutable
access. The graph implements `Index` so `g[node_index]` and
`g[edge_index]` return weight references directly and panic on invalid
indices. `node_weights` and `edge_weights` iterate all weights in index
order, with `_mut` variants. `node_references` yields `(index, &weight)`
pairs in index order.

## Indices, Direction, and Adjacency Queries

This section defines the index types, the direction vocabulary, and the
read-only adjacency surface shared by the containers.

**Indices.** `NodeIndex` and `EdgeIndex` are copyable, ordered, hashable
wrappers over an unsigned index. `NodeIndex::new` and `EdgeIndex::new`
construct them from a `usize`; the `index` method returns the `usize`
back. Indices are container-position identifiers, not stable names: the
swap rules above define their lifetime in `Graph`.

**Direction.** `Direction` is an enum with variants `Outgoing` and
`Incoming`, re-exported at the crate root; `opposite` returns the other
variant. `Directed` and `Undirected` are the edge-type markers; the
`EdgeType` trait's `is_directed` reports which one a graph uses.

**Neighbor queries.** `neighbors` returns an iterator of the node's
neighbor indices: for a directed graph, targets of outgoing edges; for an
undirected graph, all adjacent nodes. `neighbors_directed` accepts a
`Direction` and restricts to outgoing or incoming edges (for undirected
graphs it is equivalent to `neighbors`). `neighbors_undirected` ignores
direction on any graph. Neighbor iteration order is contractual: neighbors
appear in reverse order of edge insertion — the most recently added edge's
neighbor first. For `neighbors_undirected` on a directed graph, all
outgoing-edge neighbors come first (most recent first), then incoming-edge
neighbors (most recent first). A query on a nonexistent node returns an
empty iterator.

**Edge queries.** `edges` returns edge references for the node (outgoing
for directed graphs), most recently added first; `edges_directed` accepts
a direction. An edge reference exposes `source()`, `target()`, `id()`, and
`weight()` through the `EdgeRef` trait. `find_edge` returns
`Some(EdgeIndex)` of an edge from `a` to `b` — when parallel edges exist,
the one found is the most recently added — or `None`; on undirected graphs
the direction of the query does not matter. `find_edge_undirected` ignores
direction on any graph and also reports the direction the stored edge
points relative to the query. `edges_connecting` iterates every edge from
`a` to `b`, most recently added first. `contains_edge` reports whether at
least one such edge exists. `edge_endpoints` returns the `(source, target)`
pair for an edge index, or `None`. `externals` accepts a direction and
iterates nodes that have no edge in that direction (for undirected graphs:
no edge at all), in index order.

**Whole-container iteration.** `node_indices` and `edge_indices` iterate
all live indices in ascending order. `edge_references` yields all edges as
edge references in index order.

## Stable and Keyed Graphs

This section defines the two alternative containers over the same fact
source: one that never reassigns indices, and one whose nodes are their own
keys.

**StableGraph.** `StableGraph` (aliases `StableDiGraph`, `StableUnGraph`)
has the same construction, mutation, weight-access, and adjacency surface
as `Graph`, with one different removal contract: `remove_node` invalidates
only the removed index — no other node index changes — and `remove_edge`
likewise invalidates only the removed edge index. Removed positions become
vacancies. `node_count` and `edge_count` report live elements only, and
`node_indices`/`edge_indices` skip vacancies. `contains_node` reports
whether a node index is live. A subsequent `add_node` reuses the most
recently freed node index before growing the container (last freed, first
reused); `add_edge` reuses freed edge indices the same way. Weight
accessors return `None` for vacant indices, and indexing a vacancy with
`g[i]` must panic.

**GraphMap.** `GraphMap` (aliases `DiGraphMap`, `UnGraphMap`) is an
associative container whose node identifiers are the node values
themselves: the node type must be copyable, ordered, and hashable (the
`NodeTrait` bundle). There are no node or edge indices. `add_node` inserts
a key and returns it; adding an existing key is a no-op. `add_edge`
accepts two keys and a weight, implicitly adding missing endpoint keys; it
returns `None` when the edge is new, or `Some(old_weight)` when an edge
between those keys already existed and its weight was replaced — parallel
edges do not exist in this container. Self-loops are allowed.
`remove_node` removes a key and all its edges and returns whether the key
was present; `remove_edge` returns the removed weight. `contains_node` and
`contains_edge` report membership; `edge_weight` (and `_mut`) return the
weight between two keys. On an undirected map, an edge between `a` and `b`
is the same edge as between `b` and `a`, and its stored endpoint pair is
normalized to the ordered pair (smaller key first) as reported by edge
iteration. `nodes` iterates keys in insertion order; `all_edges` iterates
`(a, b, &weight)` triples in edge-insertion order; `neighbors` and
`neighbors_directed` mirror the directed/undirected semantics of `Graph`.
`from_edges` builds a map from edge descriptors. `into_graph` converts the
map into a `Graph` whose node weights are the keys, in insertion order.

## Traversal Visitors and View Adapters

This section defines the lazy walkers and the non-copying graph views they
(and the algorithms) operate over.

**Visitors are lazy and resumable.** `Bfs::new` and `Dfs::new` accept a
graph reference and a start node; `DfsPostOrder::new` the same; `Topo::new`
accepts only the graph. Each visitor exposes a `next` method that takes the
graph again and returns `Some(node)` or `None` when exhausted; because the
graph is only borrowed per call, the caller must be able to mutate the
graph between steps or walk one visitor over multiple compatible views. A
visitor tracks its own visit map: nodes are yielded at most once.

**Order contracts.** `Bfs` yields the start node first, then nodes in
breadth-first layers; within a layer, neighbor order follows the graph's
neighbor iteration order. `Dfs` yields nodes in depth-first preorder
(a node is yielded when first discovered); `DfsPostOrder` yields nodes in
depth-first postorder (a node is yielded after all its descendants). Both
depth-first walkers push newly discovered neighbors onto a stack in the
graph's neighbor iteration order and explore the most recently pushed
first, so among a node's unvisited children the one whose edge was added
earliest is descended into first — the reverse of the neighbor iteration
order. `Topo`
yields every node of an acyclic directed graph in a topological order —
each node before all of its successors — starting from the nodes with no
incoming edges; nodes on cycles are never yielded. `Dfs::move_to` (also on
`DfsPostOrder`) repositions the walker on a new start while keeping the
visit map, so already-visited nodes are not repeated.

**View adapters.** `Reversed` wraps a graph reference and presents every
edge with source and target swapped; traversals and algorithms over
`Reversed(&g)` behave as if the graph had been reversed, without copying.
`NodeFiltered` wraps a graph and a node predicate; nodes failing the
predicate (and every edge touching them) disappear from every query on the
view. `EdgeFiltered` wraps a graph and an edge-reference predicate
(`EdgeFiltered::from_fn` constructs it from a closure); edges failing the
predicate disappear. Both filters are constructible as tuple structs from
the graph reference and the predicate. All three adapters implement the
same visit traits the algorithms consume, so any in-scope algorithm must
accept them wherever its trait bounds allow.

## Graph Analysis

This section defines the structural algorithms: connectivity, cycles,
topological order, strongly connected components, and condensation. All of
them take the graph by reference (or any adapter view) and mutate nothing.

**Connectivity.** `connected_components` returns the number of connected
components, treating edges as undirected regardless of the graph's edge
type (weak connectivity for directed graphs); an isolated node is its own
component. `has_path_connecting` accepts a graph, two nodes, and an
optional reusable workspace (`None` for a fresh one), and returns whether
a path following edge directions leads from the first node to the second;
every node reaches itself.

**Cycle detection.** `is_cyclic_directed` reports whether a directed graph
contains a directed cycle; self-loops count as cycles.
`is_cyclic_undirected` reports whether the graph, viewed as undirected,
contains a cycle.

**Topological sort.** `toposort` accepts a directed graph and an optional
workspace and returns `Ok(order)` — a vector containing every node exactly
once, each node positioned before all of its successors — or
`Err(Cycle)` when the graph has a directed cycle (self-loops included).
The `Cycle` error's `node_id` method returns a node that participates in a
cycle. Multiple orders are often valid; any order satisfying the successor
rule is correct.

**Strongly connected components.** `kosaraju_scc` and `tarjan_scc` each
return a vector of components, every component a vector of node ids;
every node appears in exactly one component, and two nodes share a
component exactly when each can reach the other. The order of components
is contractual for both functions: components appear in postorder — the
reverse of a topological order of the condensation — so a component always
appears before any component that links to it. The order of nodes within a
component is arbitrary.

**Condensation.** `condensation` consumes an owned directed graph and a
boolean `make_acyclic`, and returns a new directed graph whose node
weights are vectors of the original node weights, one vector per strongly
connected component. When `make_acyclic` is true, edges inside a component
are dropped and multiple edges between two components collapse into the
edges that existed (intra-component edges removed); when false, every
original edge is preserved, re-targeted to the component nodes (edges
inside a component become self-loops or parallel edges on the component
node).

## Path Finding and Spanning Trees

This section defines the weighted-path algorithms and the spanning-tree
element stream.

**Dijkstra.** `dijkstra` accepts a graph, a start node, an optional goal
node, and an edge-cost closure mapping an edge reference to a non-negative
cost. It returns a hash map from node id to minimum path cost, containing
the start node (cost zero) and every node reached; nodes unreachable from
the start are absent. When a goal is given, the search terminates once the
goal's cost is final — the returned map must contain the goal (when
reachable) but is not required to contain every reachable node.

**A-star.** `astar` accepts a graph, a start node, a goal predicate over
node ids, an edge-cost closure, and a heuristic closure estimating the
remaining cost from a node. It returns `Some((total_cost, path))` for the
first node satisfying the predicate, where `path` is the full node
sequence from start to goal inclusive, or `None` when no goal is
reachable. With a heuristic that never overestimates, the returned cost is
minimal; with the zero heuristic it agrees with `dijkstra`.

**Bellman–Ford.** `bellman_ford` accepts a graph whose edge weights are
floating-point measures and a source node, and returns
`Ok(paths)` or `Err(NegativeCycle)` when a cycle with negative total
weight is reachable. The `Paths` result is a struct with two public
fields, both indexed by node position in the graph: `distances`, the
minimum cost per node (infinity for unreachable nodes), and
`predecessors`, the previous node on a shortest path (`None` for the
source and for unreachable nodes). Negative edge weights without a
negative cycle are supported.

**Minimum spanning tree.** `min_spanning_tree` accepts an undirected
graph and returns a lazy iterator of `Element` values — `Element::Node`
carrying a weight, then `Element::Edge` carrying source and target
positions (as `usize`, referring to the order nodes were emitted) and the
edge weight — describing a minimum-total-weight spanning forest: a
spanning tree per connected component. `Element` lives in the `data`
module. `from_elements` (the `FromElements` trait, `data` module)
constructs a graph from such an element stream, so a spanning tree is
materialized by feeding the iterator to the target graph type. For a
connected graph with `n` nodes, the materialized tree has exactly `n - 1`
edges and the minimal possible total edge weight.

## State Model

One store of weighted nodes and weighted edges, plus a directionality
marker, underlies every projection:

- **Containers** project the store through three addressing schemes:
  compact indices with swap-removal (`Graph`), stable indices with
  vacancies and last-freed-first-reused allocation (`StableGraph`), and
  self-identifying keys with no parallel edges (`GraphMap`).
- **Adjacency queries** (neighbors, edges, find/contains, endpoints,
  externals) project local structure, with the reverse-insertion neighbor
  order as a shared contract.
- **Visitors** project reachability lazily (`Bfs`, `Dfs`, `DfsPostOrder`,
  `Topo`), one node per `next` call, resumable and interleavable with
  mutation.
- **Adapters** (`Reversed`, `NodeFiltered`, `EdgeFiltered`) project a
  transformed view of the same store that every visitor and algorithm must
  accept in place of the graph itself.
- **Algorithms** project global structure: component counts, cycle
  existence, topological orders, strongly connected components and their
  condensation, shortest-path cost maps and predecessor arrays, and
  spanning-forest element streams.

Mutating a container changes what every projection reports; no projection
caches state across calls except the visitors' own visit maps, which is
their documented contract.

## Error Semantics

The failure surface is small and precise; everything else is total.

| Condition | Outcome |
|---|---|
| `add_edge`/`update_edge` with a missing endpoint (`Graph`, `StableGraph`) | panic |
| Indexing `g[index]` with an invalid or vacant index | panic |
| Adding nodes/edges beyond the index type's capacity | panic |
| `toposort` on a graph with a directed cycle (self-loops included) | returns `Err(Cycle)`; `node_id()` names a participant |
| `bellman_ford` with a reachable negative cycle | returns `Err(NegativeCycle)` |
| `remove_node`/`remove_edge`/weight accessors on missing elements | return `None`, no panic |
| Adjacency queries on nonexistent nodes | empty iterator, no panic |

`Cycle` and `NegativeCycle` are plain data types in the `algo` module;
`NegativeCycle` is a unit-like struct, and both are debug-printable.

## Cross-View Invariants

1. For every graph and node, the multiset of `neighbors(n)` on a directed
   graph must equal the targets of `edges(n)`, in the same order, and
   `neighbors_directed(n, Incoming)` must equal the sources of
   `edges_directed(n, Incoming)`.
2. A `Bfs`/`Dfs` walk over `Reversed(&g)` from `t` must visit exactly the
   set of nodes from which `has_path_connecting(&g, n, t, None)` holds.
3. For an acyclic directed graph, the order produced by `Topo` and the
   order returned by `toposort` must both satisfy: for every edge, the
   source appears before the target; and both must contain every node
   exactly once.
4. `kosaraju_scc` and `tarjan_scc` must partition the node set into the
   same components (equal as sets of sets), and `condensation` with
   `make_acyclic = true` must produce one node per such component with an
   acyclic edge structure (`is_cyclic_directed` false, `toposort` Ok).
5. `dijkstra` with unit costs from `s` must assign every reachable node a
   cost equal to its BFS layer depth from `s`, and `astar` with the zero
   heuristic must return the same cost `dijkstra` reports for the goal.
6. Removing a node from a `StableGraph` must leave every other node's
   index, weight, and surviving adjacency unchanged, while the same
   removal on a `Graph` built identically must relocate the last node to
   the removed index with its weight and adjacency intact.
7. `GraphMap::into_graph` must produce a `Graph` whose node weights are
   the map's keys in insertion order and whose edge set corresponds
   one-to-one with `all_edges`.
8. Materializing `min_spanning_tree` through `from_elements` must yield a
   graph with one component per component of the input,
   `nodes − components` edges, and the minimum achievable total weight;
   `connected_components` of the result must equal that of the input.

## Public Interface

### Import Surface

```rust
// crate root
use petgraph::{Directed, Direction, EdgeType, Graph, Incoming, Outgoing, Undirected};

// index-based graph module
use petgraph::graph::{DiGraph, EdgeIndex, Graph as G, NodeIndex, UnGraph};

// stable and keyed containers
use petgraph::stable_graph::{StableDiGraph, StableGraph, StableUnGraph};
use petgraph::graphmap::{DiGraphMap, GraphMap, NodeTrait, UnGraphMap};

// prelude (re-exports the common names above plus the visitors and EdgeRef)
use petgraph::prelude::*;

// traversal and adapters
use petgraph::visit::{Bfs, Dfs, DfsPostOrder, EdgeFiltered, EdgeRef, NodeFiltered, Reversed, Topo};

// algorithms
use petgraph::algo::{
    astar, bellman_ford, condensation, connected_components, dijkstra,
    has_path_connecting, is_cyclic_directed, is_cyclic_undirected,
    kosaraju_scc, min_spanning_tree, tarjan_scc, toposort, Cycle, NegativeCycle,
};
use petgraph::algo::bellman_ford::Paths;

// element streams
use petgraph::data::{Element, FromElements};
```

The prelude re-exports `Graph`, `DiGraph`, `UnGraph`, `StableGraph`,
`StableDiGraph`, `StableUnGraph`, `GraphMap`, `DiGraphMap`, `UnGraphMap`,
`NodeIndex`, `EdgeIndex`, `Direction`, `Incoming`, `Outgoing`, `Directed`,
`Undirected`, `Bfs`, `Dfs`, `DfsPostOrder`, and `EdgeRef`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Graph` / `DiGraph` / `UnGraph` | struct / aliases | compact index-based graph with swap-removal |
| `StableGraph` / `StableDiGraph` / `StableUnGraph` | struct / aliases | stable-index graph with vacancies |
| `GraphMap` / `DiGraphMap` / `UnGraphMap` | struct / aliases | keyed graph; nodes are their own identifiers |
| `NodeIndex` / `EdgeIndex` | structs | positional identifiers for index-based graphs |
| `NodeTrait` | trait | key bundle (Copy + Ord + Hash) for `GraphMap` nodes |
| `Direction` (`Outgoing`, `Incoming`) | enum | edge direction selector; `opposite` flips it |
| `Directed` / `Undirected` / `EdgeType` | markers / trait | edge-type parameter vocabulary |
| `Bfs` / `Dfs` / `DfsPostOrder` / `Topo` | structs | lazy resumable traversal visitors |
| `Reversed` | struct | direction-flipping view adapter |
| `NodeFiltered` / `EdgeFiltered` | structs | predicate-based view adapters |
| `EdgeRef` | trait | edge reference accessors: source, target, id, weight |
| `connected_components` | function | count components (edges viewed undirected) |
| `is_cyclic_directed` / `is_cyclic_undirected` | functions | cycle existence tests |
| `has_path_connecting` | function | directed reachability between two nodes |
| `toposort` | function | topological order or `Cycle` error |
| `kosaraju_scc` / `tarjan_scc` | functions | strongly connected components in postorder |
| `condensation` | function | contract each component to one node |
| `dijkstra` | function | non-negative shortest-path cost map |
| `astar` | function | heuristic-guided shortest path with node sequence |
| `bellman_ford` | function | shortest paths allowing negative weights |
| `Paths` | struct | distances and predecessors per node position |
| `Cycle` / `NegativeCycle` | structs | error payloads of `toposort` / `bellman_ford` |
| `min_spanning_tree` | function | lazy element stream of a minimum spanning forest |
| `Element` | enum | node/edge element of a graph stream |
| `FromElements` | trait | build a graph from an element stream |

### CLI Entry Points

There is no console script for this package. Programmatic use is through
the Rust crate API.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `petgraph` with its default configuration
  providing every behavior described here; the assessment suite depends on
  the crate as `petgraph = { version = "*" }`.
- The `fixedbitset`, `indexmap` (2.7 line), and `hashbrown` (0.15 line)
  crates are available as data-structure primitives; the containers, index
  contracts, visit layer, adapters, and algorithms are the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Container mutation: index assignment order, swap-removal relocation,
  stable-graph vacancies and last-freed-first-reused allocation, keyed-map
  identity and edge-weight replacement, parallel-edge and self-loop rules,
  retain/clear/reverse/map/filter_map, extend and from-edges builders.
- Adjacency queries: neighbor and edge iteration with the
  reverse-insertion order contract, direction handling on directed and
  undirected graphs, find/contains/endpoints/connecting/externals.
- Traversal: BFS/DFS/postorder/topological walkers, laziness and
  resumability, visit-map behavior, `move_to`.
- Adapters: reversed and filtered views consumed by walkers and
  algorithms.
- Algorithms: connectivity and cycle predicates, topological sort and its
  error, component structure and postorder of SCC results, condensation
  in both modes, cost maps, path reconstruction, negative-cycle error,
  spanning-forest materialization. Results with several valid answers are
  checked against their defining property rather than one fixed answer.
- Cross-view consistency: the invariants listed above, exercised jointly
  across containers, views, and algorithms.

Scoring runs the suite against the delivered crate; each test either
passes or fails, and the score is the fraction passed. Tests use fresh
fixture graphs; memorized outputs from any similarly-named library will
not match.
