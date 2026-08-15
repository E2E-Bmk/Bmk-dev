# NetworkX Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

NetworkX is a Python package for creating, manipulating, inspecting, and converting graphs whose nodes are ordinary hashable Python objects and whose graph, node, and edge data are user-controlled attribute dictionaries. The core data model is intentionally Pythonic: graph objects are mutable containers; reporting APIs expose live views instead of snapshots; conversions and text output project the same graph state into common Python and human-readable forms.

## Non-Goals

This specification does not cover the full NetworkX algorithm catalogue, including shortest paths, traversal algorithms, centrality, clustering, connectivity, flow, matching, planarity, isomorphism, approximation, community detection, tree algorithms, DAG algorithms, and graph hashing.

This specification does not cover graph generator behavior beyond helper mutations such as `add_path`, `add_star`, and `add_cycle`.

This specification does not cover NumPy, SciPy, pandas, PyGraphviz, pydot, matplotlib, or backend-dispatch integration beyond rejecting or delegating inputs as described for the pure-Python core.

This specification does not cover exact serialization contracts for adjacency list, multiline adjacency list, edge list files, GML, GraphML, GEXF, LEDA, Pajek, graph6, sparse6, matrix market, JSON graph formats, or drawing/image output. The only read/write format covered here is network text.

This specification does not require performance parity, memory-layout parity, private attributes, private helper functions, cache internals, subclass factory customization, or exact `repr` strings for view objects.

## Representative Workflows

```python
import networkx as nx

G = nx.MultiDiGraph(name="routes")
G.add_node("A", kind="station")
G.add_nodes_from([("B", {"kind": "station"}), ("C", {"kind": "depot"})], zone=1)
first = G.add_edge("A", "B", route="red", weight=2)
second = G.add_edge("A", "B", route="blue", weight=3)
G.add_edge("B", "C", route="red", weight=5)

assert first == 0
assert second == 1
assert list(G.successors("A")) == ["B"]
assert G.pred["B"]["A"][0]["route"] == "red"
assert G.edges["A", "B", 1]["route"] == "blue"
assert G.degree["B"] == G.in_degree["B"] + G.out_degree["B"]

red_view = nx.subgraph_view(
    G,
    filter_edge=lambda u, v, k: G[u][v][k].get("route") == "red",
)
assert list(red_view.edges(keys=True)) == [("A", "B", 0), ("B", "C", 0)]

H = nx.MultiDiGraph(red_view)
assert H.edges["A", "B", 0]["weight"] == 2

lines = list(nx.generate_network_text(H, sources=["A"], ascii_only=True))
assert lines == [
    "+-- A",
    "    L-> B",
    "        L-> C",
]
```

## Graph Construction and Mutation

This section covers how graphs are created, how nodes and edges are added and removed, and how attribute precedence works.

**Graph types.** `Graph` stores undirected edges, permits self-loops, and does not store parallel edges. `DiGraph` stores directed edges, permits self-loops, and does not store parallel edges. `MultiGraph` stores undirected parallel edges distinguished by keys. `MultiDiGraph` stores directed parallel edges distinguished by keys.

**Constructors.** Constructors must create an empty graph when `incoming_graph_data` is `None`. Constructors must load edge lists, dict-of-dicts, dict-of-lists, and other NetworkX graph objects through `to_networkx_graph` when data is supplied. Constructor keyword attributes must update `G.graph` after incoming data has been loaded. Passing `backend="networkx"` as a constructor keyword must not create a graph attribute named `backend`.

**Node constraints.** Nodes must be hashable Python objects other than `None`. `add_node(None)` and edge insertion with `None` as either endpoint must raise `ValueError`. A missing node lookup through `G[n]` or `G.nodes[n]` must raise `KeyError`. Membership checks such as `n in G` and `G.has_node(n)` must return `False` instead of raising when `n` is unhashable.

**Adding nodes.** `add_node(node, **attr)` must insert a new node with attributes or update attributes when the node already exists. `add_nodes_from(nodes, **attr)` must accept plain nodes and `(node, attrdict)` pairs. For pairs, values from the pair's attribute dictionary must override same-named keyword attributes, and keyword attributes must still be applied for keys absent from the pair. Removing a missing node with `remove_node` must raise `NetworkXError`; `remove_nodes_from` must silently ignore missing nodes.

**Adding simple edges.** `add_edge(u, v, **attr)` on simple graphs must automatically add missing endpoint nodes. Adding an already existing simple edge must update its attribute dictionary without increasing the edge count. `add_edges_from(ebunch, **attr)` must accept `(u, v)` and `(u, v, attrdict)` entries; tuple lengths other than 2 or 3 must raise `NetworkXError`. Edge attributes from an ebunch entry must override same-named keyword attributes. Removing a missing simple edge must raise `NetworkXError`; `remove_edges_from` must silently ignore missing simple edges.

**Adding multi-edges.** `MultiGraph.add_edge` and `MultiDiGraph.add_edge` must return the assigned key. When `key` is `None`, the first edge between a pair must receive key `0`, and later default keys must be the lowest unused nonnegative integer. When a key is supplied and already exists, the existing edge data must be updated rather than creating another edge. `add_edges_from` on multigraphs must accept `(u, v)`, `(u, v, attrdict)`, `(u, v, key)`, and `(u, v, key, attrdict)` entries and must return the list of assigned keys.

**Removing multi-edges.** `remove_edge(u, v, key=None)` on multigraphs must remove the specified keyed edge when `key` is provided. When `key` is `None`, it must remove one edge, choosing the most recently inserted surviving key. Missing endpoint pairs or keys must raise `NetworkXError`. `remove_edges_from` must silently ignore missing pairs and keys.

## Reporting Views and Attribute Access

This section covers how graph state is inspected through live views.

**Node views.** `G.nodes` must behave as a live set-like and dict-like view. Iterating must return nodes. `G.nodes(data=True)` must return `(node, attrdict)` pairs. `G.nodes(data=name, default=value)` must return `(node, value)` pairs where missing attributes return the supplied default. A called node data view must support lookup by node. Assigning into `G.nodes[n][key]` must mutate the node attribute dictionary; assigning `G.nodes[new_node] = ...` must fail because the view itself is read-only.

**Edge views.** `G.edges` must behave as a live set-like and dict-like view. For simple graphs, `G.edges[u, v]` must return the edge attribute dictionary. For multigraphs, `G.edges[u, v, key]` must return the keyed edge attribute dictionary. `G.edges(data=True)` must include full attribute dictionaries. `G.edges(data=name, default=value)` must include the named value or default. Multigraph edge views must include duplicate `(u, v)` pairs when `keys=False` and `(u, v, key)` tuples when `keys=True`.

**Adjacency.** `G.adj` and `G[n]` must return the same adjacency projection. In simple graphs, `G[u][v]` must return the edge attribute dictionary. In multigraphs, `G[u][v]` must return a mapping of edge keys to attribute dictionaries. A missing adjacency source node must raise `KeyError`.

**Degree.** `G.degree` must report the number of incident edges when `weight=None`. Weighted degree must sum the named edge attribute, treating edges without that attribute as weight `1`. A self-loop must contribute two to unweighted degree in undirected graphs. In directed graphs, `G.degree[n]` must equal `G.in_degree[n] + G.out_degree[n]`.

**Directed adjacency.** Directed graphs must expose outgoing adjacency through `G.adj` and `G.succ`. `G.neighbors(n)` and `G.successors(n)` must return the same iterator. `G.predecessors(n)` must iterate incoming neighbors. Missing nodes passed to `successors`, `predecessors`, or `neighbors` on directed graphs must raise `NetworkXError`. `has_successor(u, v)` and `has_predecessor(u, v)` must return booleans and must not raise for missing nodes.

**Module-level helpers.** `nx.nodes(G)`, `nx.edges(G)`, `nx.degree(G)`, `nx.neighbors(G, n)`, `nx.number_of_nodes(G)`, and `nx.number_of_edges(G)` must delegate to graph methods. `nx.add_path`, `nx.add_cycle`, and `nx.add_star` must mutate `G` by adding corresponding nodes, edges, and edge attributes. A single-node cycle must add one self-loop. Empty inputs must not add nodes or edges.

**Attribute helpers.** `nx.set_node_attributes`, `nx.get_node_attributes`, `nx.set_edge_attributes`, and `nx.get_edge_attributes` must read and write through the same attribute dictionaries. Setting for missing nodes or edges must ignore those missing targets. `get_node_attributes` with a `default` parameter must return the default for nodes that lack the named attribute.

**Freezing.** `nx.freeze(G)` must make structural mutation methods raise `NetworkXError` while preserving read access and attribute-dictionary mutation. `nx.is_frozen(G)` must return whether the graph has been frozen.

## Graph Transformation and Conversion

This section covers how graphs are copied, viewed, and converted between representations.

**Copy.** `G.copy(as_view=False)` must return an independent graph with copied structure and attributes. `G.copy(as_view=True)` must return a read-only live view.

**Subgraph views.** `G.subgraph(nodes)` must return a read-only live node-induced view whose attributes are shared with the original. Structural mutation must raise `NetworkXError`. `G.edge_subgraph(edges)` must return a read-only live view containing only selected edges and their endpoints; attribute changes through the view must be visible from the original.

**Direction conversion.** `G.to_directed(as_view=False)` must return a directed graph; each undirected non-loop edge must produce both directed arcs. `G.to_undirected(as_view=False)` must return an undirected graph. When `reciprocal=True`, only edges whose reverse also exists must be kept. `as_view=True` must return a read-only live view.

**Generic graph view.** `nx.graphviews.generic_graph_view(G)` must return a frozen, read-only view sharing all state with `G`. Mutations to `G` must be reflected in the view. Attribute mutations through returned dictionaries must be reflected in `G`.

**Subgraph view with filters.** `subgraph_view(G, filter_node=..., filter_edge=...)` must return a frozen, read-only view that evaluates filters as elements are queried. For simple graphs, `filter_edge` receives `(u, v)`. For multigraphs, `filter_edge` receives `(u, v, key)`. Exceptions raised by filter functions must propagate.

**Reverse view.** `reverse_view(G)` must return a frozen, read-only directed view with reversed edge directions. Calling it on an undirected graph must raise `NetworkXNotImplemented`.

**Dict-of-lists conversion.** `to_dict_of_lists(G, nodelist=None)` must return adjacency lists ignoring edge data and multiedge multiplicity. `from_dict_of_lists(d, create_using=None)` must create the requested graph type from adjacency lists. For undirected multigraph targets, reciprocal entries must not create duplicate parallel edges.

**Dict-of-dicts conversion.** `to_dict_of_dicts(G, nodelist=None, edge_data=None)` must return nested adjacency dictionaries. When `edge_data` is `None`, simple graphs return edge-data mappings and multigraphs return key-to-data mappings. When `edge_data` is supplied, every edge value must be that scalar. `from_dict_of_dicts(d, create_using=None, multigraph_input=False)` must create graphs from nested data; when `multigraph_input=True`, nested values must be key-to-data mappings.

**Edge list conversion.** `to_edgelist(G)` must return edges with `data=True`. `from_edgelist(edgelist, create_using=None)` must add all edge tuples and raise `NetworkXError` for invalid tuple lengths.

**to_networkx_graph.** `to_networkx_graph(data, create_using=None)` must return a graph from known data shapes. When `create_using` is a graph instance, that instance must be cleared and populated. Converting from a graph must preserve graph, node, and edge attributes.

## Network Text and Configuration

This section covers tree-style text rendering and the global configuration object.

**generate_network_text.** `generate_network_text` must yield one string per displayed line. For an empty graph with `ascii_only=True`, it must yield `["+"]`. When `max_depth == 0`, it must yield the root glyph followed by an ellipsis. When `sources` is provided, only nodes reachable from those sources must be displayed. When `sources` is omitted, enough sources must be chosen to reach every node.

**Label and collapse behavior.** When `with_labels=True`, node display text must use each node's `"label"` attribute when present. When `with_labels` is a string, that attribute name must be used. When `with_labels=False`, node values must be used. A node with truthy `"collapse"` attribute must replace its children with an ellipsis.

**ASCII glyphs.** `ascii_only=True` must use ASCII tree and arrow glyphs. Directed graphs must use `+-- ` for roots, `|-> ` for middle children, `L-> ` for last children, and `<-` for backedges. Undirected graphs must use `+-- ` for roots, `|-- ` for middle children, `L-- ` for last children, and `-` for backedges.

**write_network_text.** `write_network_text` must write every generated line followed by `end`. When `path` is `None`, it must write to standard output. When `path` has a `write` method, it must call that method. When `path` is callable, it must call the callable once per line. Any other `path` value must raise `TypeError`.

**Config objects.** `Config(**kwargs)` must create a mapping-like configuration object. A `Config` subclass with annotations must create strict configuration keys from those annotations. Strict configs must permit modification of existing keys and must reject new keys: attribute assignment must raise `AttributeError` and item assignment must raise `KeyError`. Strict config deletion must raise `TypeError`. Flexible subclasses declared with `strict=False` must permit adding and deleting configuration items.

**Config mapping protocol.** Config objects must support `key in cfg`, iteration, `len(cfg)`, `reversed(cfg)`, `cfg[key]`, `cfg.get`, `cfg.keys`, `cfg.values`, and `cfg.items`. Missing item lookup must raise `KeyError`.

**Config context manager.** Calling a config object with keyword values must set those values immediately and return the config as a context manager. Entering must keep the temporary values active. Exiting must restore the previous values. Entering without first calling with values must raise `RuntimeError`.

**Global config.** `nx.config` must be a global `NetworkXConfig` instance. `cache_converted_graphs` and `fallback_to_nx` assignments must require booleans; non-boolean types must raise `TypeError`. `warnings_to_ignore` must require a set of strings and must reject unknown warning names with `ValueError`.

## State Model

A graph has three public projections of the same mutable state:

- The structural projection returns nodes and edges through membership, iteration, length, `number_of_nodes`, `number_of_edges`, adjacency lookup, and neighbor iteration.
- The attribute projection returns mutable graph, node, and edge attribute dictionaries through `G.graph`, `G.nodes[...]`, `G.edges[...]`, and adjacency lookup.
- The reporting projection returns live views through `G.nodes`, `G.edges`, `G.adj`, `G.degree`, and, for directed graphs, `G.pred`, `G.succ`, `G.in_edges`, `G.out_edges`, `G.in_degree`, and `G.out_degree`.

These projections must stay coherent. A node inserted through `add_node` must appear in iteration, `G.nodes`, and `len(G)`. An edge inserted through `add_edge` must appear in adjacency lookup, edge views, and degree views. Attribute changes made through any access path must return through every other path for the same object.

## Error Semantics

All public NetworkX exceptions must inherit from `NetworkXException`.

- `NetworkXError` must represent serious user-facing graph and conversion errors.
- `NetworkXPointlessConcept` must represent algorithms given a null graph where the concept is undefined.
- `NetworkXAlgorithmError` must represent unexpected algorithm termination.
- `NetworkXUnfeasible`, `NetworkXNoPath`, and `NetworkXNoCycle` must represent infeasible requests.
- `NetworkXUnbounded` must represent unbounded optimization problems.
- `NetworkXNotImplemented` must represent operations not implemented for a graph type.
- `NodeNotFound` must represent requests for an absent node.
- `AmbiguousSolution` must represent cases with more than one valid solution.
- `ExceededMaxIterations` must represent exceeded iteration limits.
- `PowerIterationFailedConvergence(num_iterations)` must inherit from `ExceededMaxIterations` and must create an error message stating the iteration count.

Graph mutation and conversion methods must use these exception classes where specified. Python container protocol errors such as missing view keys must use `KeyError`.

## Cross-View Invariants

1. A node added through `G.add_node(n, **attrs)` must appear through `n in G`, iteration, `G.nodes`, `G.adj`, `G.degree`, and `G.nodes[n]` must return the same attributes.
2. An edge added through `G.add_edge(u, v, **attrs)` must appear through `G.has_edge(u, v)`, `G.edges`, `G.adj[u]`, `G[u][v]`, and degree views, and all attribute access paths must return the same attributes.
3. A node removed through `G.remove_node(n)` must disappear from all views, and all incident edges must disappear.
4. A simple edge attribute written through `G[u][v][name]` must return through `G.edges[u, v][name]`, `G.get_edge_data(u, v)[name]`, and `to_dict_of_dicts(G)[u][v][name]`.
5. A multigraph edge attribute written through `G[u][v][key][name]` must return through `G.edges[u, v, key][name]`, `G.get_edge_data(u, v, key)[name]`, and `to_dict_of_dicts(G)[u][v][key][name]`.
6. In directed graphs, an edge `u -> v` must appear in `G.succ[u]`, `G.pred[v]`, `G.out_edges(u)`, `G.in_edges(v)`, `G.successors(u)`, and `G.predecessors(v)`.
7. A live graph view must reflect later structural changes made to the original graph whenever those changes pass the view's filters.
8. A successful conversion produced by `to_dict_of_lists`, `to_dict_of_dicts`, or `to_edgelist` must reflect graph state at call time; later mutation must not affect returned containers.
9. A frozen graph or read-only view must continue returning current data while structural mutation attempts raise `NetworkXError`.

## Public Interface

### Import Surface

The covered API is available from the root package:

```python
import networkx as nx
```

Covered graph classes:

```python
nx.Graph
nx.DiGraph
nx.MultiGraph
nx.MultiDiGraph
```

Covered root-level functions:

```python
nx.to_networkx_graph
nx.to_dict_of_dicts
nx.from_dict_of_dicts
nx.to_dict_of_lists
nx.from_dict_of_lists
nx.to_edgelist
nx.from_edgelist
nx.graphviews.generic_graph_view
nx.subgraph_view
nx.reverse_view
nx.generate_network_text
nx.write_network_text
nx.freeze
nx.is_frozen
nx.add_path
nx.add_star
nx.add_cycle
nx.set_node_attributes
nx.get_node_attributes
nx.set_edge_attributes
nx.get_edge_attributes
nx.nodes
nx.edges
nx.degree
nx.neighbors
nx.number_of_nodes
nx.number_of_edges
```

The root package also exports `nx.config` and exception classes including `NetworkXException`, `NetworkXError`, `NetworkXNotImplemented`, `NodeNotFound`, `NetworkXNoPath`, `NetworkXNoCycle`, `NetworkXUnfeasible`, `NetworkXUnbounded`, `AmbiguousSolution`, `ExceededMaxIterations`, and `PowerIterationFailedConvergence`. The configuration base classes are importable from `networkx.utils.configs`:

```python
from networkx.utils.configs import Config, NetworkXConfig
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| Graph | class | Undirected simple graph |
| DiGraph | class | Directed simple graph |
| MultiGraph | class | Undirected multigraph with keyed parallel edges |
| MultiDiGraph | class | Directed multigraph with keyed parallel edges |
| to_networkx_graph | function | Convert known data shapes into a NetworkX graph |
| to_dict_of_dicts | function | Convert a graph to nested adjacency dictionaries |
| from_dict_of_dicts | function | Create a graph from nested adjacency dictionaries |
| to_dict_of_lists | function | Convert a graph to adjacency lists |
| from_dict_of_lists | function | Create a graph from adjacency lists |
| to_edgelist | function | Convert a graph to an edge list |
| from_edgelist | function | Create a graph from an edge list |
| generic_graph_view | function | Create a frozen read-only view sharing graph state |
| subgraph_view | function | Create a filtered read-only graph view |
| reverse_view | function | Create a direction-reversed read-only view |
| generate_network_text | function | Yield text lines for a tree-style graph rendering |
| write_network_text | function | Write tree-style graph rendering to a path or stream |
| freeze | function | Make structural mutation raise NetworkXError |
| is_frozen | function | Return whether a graph is frozen |
| Config | class | Mapping-like configuration object |
| NetworkXConfig | class | Global configuration for the package |

### CLI Entry Points

There is no console script for this package. `python -m networkx` is not supported. Programmatic use is through Python imports.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Check behavior through public imports and public APIs only. It exercises graph construction, mutation, attribute propagation, live views, conversion round-trips, graph views, network text output, config mapping behavior, and documented error paths. Assessment observes user-observable compatibility: correct returned values, correct mutations, correct live-view coherence, and correct exception classes.

Tests do not require private storage layouts, optional numerical or plotting dependencies, backend implementations, or exhaustive graph algorithms outside this scope.
