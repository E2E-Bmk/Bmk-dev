# NetworkX Specification

## Product Overview

NetworkX is a Python package for creating, manipulating, inspecting, and converting graphs whose nodes are ordinary hashable Python objects and whose graph, node, and edge data are user-controlled attribute dictionaries. The core data model is intentionally Pythonic: graph objects are mutable containers; reporting APIs expose live views instead of snapshots; conversions and text output project the same graph state into common Python and human-readable forms.

## Scope

This specification covers the core in-memory graph contract:

- `Graph`, `DiGraph`, `MultiGraph`, and `MultiDiGraph` construction, mutation, inspection, attributes, and graph-type conversion.
- Live node, edge, adjacency, predecessor, successor, and degree views exposed by graph instances.
- Public graph helper functions for nodes, edges, attributes, empty copies, directedness, density, paths, stars, cycles, freezing, subgraphs, and restricted views.
- Pure-Python conversions through dictionaries, lists, edge lists, and `to_networkx_graph`.
- Read-only graph views from `generic_graph_view`, `subgraph_view`, and `reverse_view`.
- Network text generation through `generate_network_text` and `write_network_text`.
- Public NetworkX exception classes and `Config` mapping/context behavior.

## Installable Surface

The covered API is available from the root package:

```python
import networkx as nx

nx.Graph(incoming_graph_data=None, **attr)
nx.DiGraph(incoming_graph_data=None, **attr)
nx.MultiGraph(incoming_graph_data=None, multigraph_input=None, **attr)
nx.MultiDiGraph(incoming_graph_data=None, multigraph_input=None, **attr)
```

Covered root-level functions are:

```python
nx.to_networkx_graph(data, create_using=None, multigraph_input=False)
nx.to_dict_of_dicts(G, nodelist=None, edge_data=None)
nx.from_dict_of_dicts(d, create_using=None, multigraph_input=False)
nx.to_dict_of_lists(G, nodelist=None)
nx.from_dict_of_lists(d, create_using=None)
nx.to_edgelist(G, nodelist=None)
nx.from_edgelist(edgelist, create_using=None)
nx.graphviews.generic_graph_view(G, create_using=None)
nx.subgraph_view(G, *, filter_node=nx.filters.no_filter, filter_edge=nx.filters.no_filter)
nx.reverse_view(G)
nx.generate_network_text(graph, with_labels=True, sources=None, max_depth=None, ascii_only=False, vertical_chains=False)
nx.write_network_text(graph, path=None, with_labels=True, sources=None, max_depth=None, ascii_only=False, end="\n", vertical_chains=False)
```

The root package also exports `nx.config` and exception classes including `NetworkXException`, `NetworkXError`, `NetworkXNotImplemented`, `NodeNotFound`, `NetworkXNoPath`, `NetworkXNoCycle`, `NetworkXUnfeasible`, `NetworkXUnbounded`, `AmbiguousSolution`, `ExceededMaxIterations`, and `PowerIterationFailedConvergence`. The configuration base classes are importable from `networkx.utils.configs`:

```python
from networkx.utils.configs import Config, NetworkXConfig
```

## Public API

### Product State Model

A graph has three public projections of the same mutable state:

- The structural projection returns nodes and edges through membership, iteration, length, `number_of_nodes`, `number_of_edges`, adjacency lookup, and neighbor iteration.
- The attribute projection returns mutable graph, node, and edge attribute dictionaries through `G.graph`, `G.nodes[...]`, `G.edges[...]`, and adjacency lookup.
- The reporting projection returns live views through `G.nodes`, `G.edges`, `G.adj`, `G.degree`, and, for directed graphs, `G.pred`, `G.succ`, `G.in_edges`, `G.out_edges`, `G.in_degree`, and `G.out_degree`.

These projections must stay coherent. A node inserted through `add_node` must appear in iteration, `G.nodes`, and `len(G)`. An edge inserted through `add_edge` must appear in adjacency lookup, edge views, and degree views. Attribute changes made through `G.nodes[n]`, `G.edges[...]`, or `G[u][v]` must return through every other public attribute access path for the same object.

### Graph Classes

`Graph` stores undirected edges, permits self-loops, and does not store parallel edges. `DiGraph` stores directed edges, permits self-loops, and does not store parallel edges. `MultiGraph` stores undirected parallel edges distinguished by keys. `MultiDiGraph` stores directed parallel edges distinguished by keys.

Constructors must create an empty graph when `incoming_graph_data` is `None`. Constructors must load edge lists, dict-of-dicts, dict-of-lists, and other NetworkX graph objects through `to_networkx_graph` when data is supplied. Constructor keyword attributes must update `G.graph` after incoming data has been loaded. Passing `backend="networkx"` as a constructor keyword must not create a graph attribute named `backend`.

Nodes must be hashable Python objects other than `None`. `add_node(None)` and edge insertion with `None` as either endpoint must raise `ValueError`. A missing node lookup through `G[n]` or `G.nodes[n]` must raise `KeyError`. Membership checks such as `n in G` and `G.has_node(n)` must return `False` instead of raising when `n` is unhashable.

`add_node(node, **attr)` must insert a new node with attributes or update attributes when the node already exists. `add_nodes_from(nodes, **attr)` must accept plain nodes and `(node, attrdict)` pairs. For `(node, attrdict)` pairs, values from the pair's attribute dictionary must override same-named keyword attributes, and keyword attributes must still be applied for keys absent from the pair dictionary. Removing a missing node with `remove_node` must raise `NetworkXError`; removing missing nodes with `remove_nodes_from` must silently ignore them.

`add_edge(u, v, **attr)` on `Graph` and `DiGraph` must automatically add missing endpoint nodes. Adding an already existing simple edge must update its edge attribute dictionary and must not increase the edge count. `add_edges_from(ebunch, **attr)` must accept `(u, v)` and `(u, v, attrdict)` entries; tuple lengths other than 2 or 3 must raise `NetworkXError`. Edge attributes supplied inside an ebunch entry must override same-named keyword attributes, and keyword attributes must still be applied for keys absent from the entry dictionary. Removing a missing simple edge with `remove_edge` must raise `NetworkXError`; removing missing simple edges with `remove_edges_from` must silently ignore them.

`MultiGraph.add_edge(u, v, key=None, **attr)` and `MultiDiGraph.add_edge(u, v, key=None, **attr)` must return the assigned key. When `key` is `None`, the first edge between a pair must receive key `0`, and later default keys must be the lowest unused nonnegative integer at the time of insertion. When a key is supplied and already exists for that pair, the existing edge data for that key must be updated rather than creating another keyed edge. `add_edges_from` on multigraphs must accept `(u, v)`, `(u, v, attrdict)`, `(u, v, key)`, and `(u, v, key, attrdict)` entries and must return the list of assigned keys. Invalid multiedge tuple lengths must raise `NetworkXError`.

`MultiGraph.remove_edge(u, v, key=None)` and `MultiDiGraph.remove_edge(u, v, key=None)` must remove the specified keyed edge when `key` is provided. When `key` is `None`, they must remove one edge between the endpoints, choosing the most recently inserted surviving key for that endpoint pair. Missing endpoint pairs or missing keys must raise `NetworkXError`. `remove_edges_from` on multigraphs must silently ignore missing endpoint pairs and missing keys.

### Reporting Views

`G.nodes` must behave as a live set-like and dict-like view over nodes. Iterating `G.nodes` must return nodes. Calling `G.nodes(data=True)` must return `(node, attrdict)` pairs. Calling `G.nodes(data=name, default=value)` must return `(node, value)` pairs where missing attributes return the supplied default. A called node data view must support lookup by node: `G.nodes(data=True)[n]` must return the node attribute dictionary, and `G.nodes(data=name, default=value)[n]` must return the named attribute value or the default. A called node data view lookup for a missing node must raise `KeyError`. Assigning into `G.nodes[n][key]` must mutate the node attribute dictionary for an existing node; assigning `G.nodes[new_node] = ...` must fail because the view itself is read-only.

`G.edges` must behave as a live set-like and dict-like view over edges. For simple graphs, `G.edges[u, v]` must return the edge attribute dictionary. For multigraphs, `G.edges[u, v, key]` must return the keyed edge attribute dictionary. Calling `G.edges(data=True)` must include full edge attribute dictionaries. Calling `G.edges(data=name, default=value)` must include the named attribute value or the default. Multigraph edge views must include duplicate `(u, v)` pairs when parallel edges exist and `keys=False`; they must include `(u, v, key)` or `(u, v, key, data)` tuples when `keys=True`.

`G.adj` and `G[n]` must return the same adjacency projection for node `n`. In simple graphs, `G[u][v]` must return the edge attribute dictionary. In multigraphs, `G[u][v]` must return a mapping of edge keys to edge attribute dictionaries. A missing adjacency source node must raise `KeyError`.

`G.degree` must report the number of incident edges when `weight=None`. Weighted degree must sum the named edge attribute for incident edges, treating edges without that attribute as weight `1`. In an undirected graph, a self-loop must contribute two to unweighted degree. In a directed graph, `G.degree[n]` must equal `G.in_degree[n] + G.out_degree[n]`.

Directed graphs must expose outgoing adjacency through `G.adj` and `G.succ`. `G.neighbors(n)` and `G.successors(n)` must return the same iterator. `G.predecessors(n)` must iterate incoming neighbors. Missing nodes passed to `successors`, `predecessors`, or `neighbors` on directed graphs must raise `NetworkXError`. `has_successor(u, v)` and `has_predecessor(u, v)` must return booleans and must not raise for missing nodes.

### Copying, Subgraphs, And Graph Type Conversion

`G.copy(as_view=False)` must return an independent graph object with copied structure and copied attribute dictionaries. Mutating attributes or structure on the copy must not mutate the original. `G.copy(as_view=True)` must return a read-only live view of the original graph.

`G.subgraph(nodes)` must return a read-only live node-induced view whose graph, node, and edge attributes are shared with the original graph. The view must include only nodes present in both `nodes` and the original graph. Structural mutation through the view must raise `NetworkXError`. Calling `.copy()` on a subgraph view must return a mutable independent graph.

`G.edge_subgraph(edges)` and `nx.edge_subgraph(G, edges)` must return a read-only live view containing only selected edges and their endpoint nodes. Missing selected edges must be ignored. Attribute changes made through the view's returned attribute dictionaries must be visible from the original graph.

`G.to_directed(as_view=False)` must return a directed graph with corresponding nodes, graph attributes, node attributes, and edges. For undirected simple graphs, each non-loop edge must produce both directed arcs. For undirected multigraphs, each keyed non-loop edge must produce corresponding arcs with the same key. `G.to_directed(as_view=True)` must return a read-only live directed view.

`G.to_undirected(as_view=False)` must return an undirected graph with corresponding nodes, attributes, and edges. `DiGraph.to_undirected(reciprocal=True)` and `MultiDiGraph.to_undirected(reciprocal=True)` must keep only edges whose reverse edge also exists. `as_view=True` must return a read-only live undirected view. Invalid structural mutation through any read-only view must raise `NetworkXError`.

### Public Helper Functions

`nx.nodes(G)`, `nx.edges(G, nbunch=None)`, `nx.degree(G, nbunch=None, weight=None)`, `nx.neighbors(G, n)`, `nx.number_of_nodes(G)`, and `nx.number_of_edges(G)` must delegate to the corresponding graph methods and return the same public results. Missing nodes in `nx.neighbors(G, n)` must raise `NetworkXError`.

`nx.add_path(G, nodes_for_path, **attr)`, `nx.add_cycle(G, nodes_for_cycle, **attr)`, and `nx.add_star(G, nodes_for_star, **attr)` must mutate `G` by adding the corresponding nodes, edges, and edge attributes. Empty path, cycle, and star inputs must not add nodes or edges. A single-node path or star must add the node and no edge. A single-node cycle must add the node and one self-loop.

`nx.set_node_attributes`, `nx.get_node_attributes`, `nx.set_edge_attributes`, and `nx.get_edge_attributes` must read and write through the same node and edge attribute dictionaries exposed by graph views. Attribute setting for missing nodes or edges must ignore those missing targets rather than creating them. Attribute lookup with a requested name must return only graph elements that have that attribute unless a default is supplied by the public function.

`nx.freeze(G)` must make structural mutation methods on `G` raise `NetworkXError` while preserving read access and attribute-dictionary mutation. `nx.is_frozen(G)` must return whether the graph has been frozen.

### Conversions

`to_networkx_graph(data, create_using=None, multigraph_input=False)` must return a NetworkX graph created from known public data shapes: NetworkX graph objects, dict-of-dicts, dict-of-lists, edge containers, edge iterators, and edge generators. When `create_using` is a graph instance, that instance must be cleared before it is populated and returned. Unknown data types must raise `NetworkXError`. Invalid edge-list data must raise `NetworkXError`.

Converting from a NetworkX graph object must preserve graph attributes, node attributes, edge attributes, directedness requested by `create_using`, and multigraph edge keys when the target supports them. A malformed object that merely looks graph-like must raise `NetworkXError`.

`to_dict_of_lists(G, nodelist=None)` must return a dictionary mapping each selected node to a list of selected neighbors. It must ignore all edge data and all multiedge multiplicity. When `nodelist` is supplied, only nodes in that list and neighbors also present in that list must appear. Missing nodes in `nodelist` must raise through graph neighbor lookup.

`from_dict_of_lists(d, create_using=None)` must create the requested graph type, add all keys of `d` as nodes, and add edges from each key to each listed neighbor. For undirected multigraph targets, reciprocal entries in the dictionary must not create duplicate parallel edges for the same undirected pair. Malformed node values that cannot be added must raise the same errors as graph mutation.

`to_dict_of_dicts(G, nodelist=None, edge_data=None)` must return nested dictionaries keyed by node and neighbor for `Graph`, `DiGraph`, `MultiGraph`, and `MultiDiGraph` inputs. When `edge_data is None`, the returned values must be the public edge-data mappings for simple graphs and key-to-data mappings for multigraphs. When `edge_data` is not `None`, every represented edge value must be exactly that scalar and multiedge key detail must be omitted. When `nodelist` is supplied, only selected nodes and selected neighbors must appear.

`from_dict_of_dicts(d, create_using=None, multigraph_input=False)` must create the requested graph type, add all keys of `d` as nodes, and add edges from nested adjacency data. When `multigraph_input=True`, nested values must be interpreted as key-to-edge-data mappings. When `multigraph_input=False`, nested values must be interpreted as edge-attribute dictionaries. Invalid nested data must raise the same graph-construction errors that direct edge insertion would raise.

`to_edgelist(G, nodelist=None)` must return the graph's edge view with `data=True`; with `nodelist`, it must return only edges incident to the selected nodes using the same nbunch semantics as `G.edges`. `from_edgelist(edgelist, create_using=None)` must add all supplied edge tuples through `add_edges_from` and must raise `NetworkXError` for invalid tuple lengths.

### Graph Views

`nx.graphviews.generic_graph_view(G, create_using=None)` must return a frozen, read-only graph view that shares graph, node, edge, and adjacency state with `G`. Mutations to `G` after view creation must be reflected in the view. Attribute dictionary mutations performed through returned dictionaries must be reflected in `G`. If `create_using` changes multigraph status relative to `G`, the function must raise `NetworkXError`.

`subgraph_view(G, *, filter_node, filter_edge)` must return a frozen, read-only graph view that evaluates filters as graph elements are queried. `filter_node(node)` must decide whether a node appears. For simple graphs, `filter_edge(u, v)` must decide whether an edge appears. For multigraphs, `filter_edge(u, v, key)` must decide whether a keyed edge appears. Edges incident to filtered-out nodes must not appear. Exceptions raised by filter functions must propagate to the caller.

`reverse_view(G)` must return a frozen, read-only directed view with edge directions reversed. It must be equivalent to `G.reverse(copy=False)` for directed graph classes. Calling `reverse_view` on an undirected graph must raise `NetworkXNotImplemented`.

### Network Text

`generate_network_text` must yield one string per displayed line. For an empty graph it must yield a single root glyph line: with `ascii_only=True`, an empty graph returns `["+"]`. When `max_depth == 0`, it must yield the root glyph followed by one space and an ellipsis: with `ascii_only=True`, the result returns `["+ ..."]`. When `sources` is provided, traversal must start from those nodes and nodes unreachable from those sources must not be displayed. When `sources` is omitted, traversal must choose enough sources to reach every node in the graph.

When `with_labels=True`, node display text must use each node's `"label"` attribute when present and the node value otherwise. When `with_labels` is a string, that attribute name must be used. When `with_labels=False`, node values must be used. A node with truthy `"collapse"` attribute must display itself and must replace its children with an ellipsis when children exist.

`ascii_only=False` must use Unicode tree and arrow glyphs. `ascii_only=True` must use ASCII glyphs according to graph directedness. Undirected ASCII roots must use `+-- `, middle children must use `|-- `, last children must use `L-- `, backedges must use `-`, and vertical chain edges must use `|`. Directed ASCII roots must use `+-- `, middle children must use `|-> `, last children must use `L-> `, backedges must use `<-`, and vertical chain edges must use `!`. Indentation must use four-character prefixes that preserve the visible tree: continuing tree levels use `"|   "`, continuing forest levels use `":   "`, and closed levels use four spaces.

For a directed graph with edges `A -> B`, `A -> C`, and `B -> D`, with node `A` labeled `"root"` and node `B` marked with truthy `"collapse"`, ASCII output from source `A` returns:

```python
[
    "+-- root",
    "    |-> B",
    "    |   L->  ...",
    "    L-> C",
]
```

`vertical_chains=True` must draw a single-child chain vertically where the text format supports it.

`write_network_text` must write every generated line followed by `end`. When `path is None`, it must write to standard output. When `path` has a `write` method, it must call that method. When `path` is callable, it must call the callable once per line. Any other `path` value must raise `TypeError`.

### Config

`Config(**kwargs)` must create a mapping-like configuration object whose keys are the supplied keyword names. A `Config` subclass with annotations must create strict configuration keys from those annotations. Strict configs must permit modification of existing keys through attribute or item assignment and must reject new keys: attribute assignment must raise `AttributeError`, and item assignment must raise `KeyError`.

Config objects must support `key in cfg`, iteration over keys, `len(cfg)`, `reversed(cfg)`, `cfg[key]`, `cfg.get`, `cfg.keys`, `cfg.values`, and `cfg.items` with Mapping semantics. Missing item lookup must raise `KeyError`. Strict config deletion must raise `TypeError` through attribute deletion and item deletion. Flexible subclasses declared with `strict=False` must permit adding and deleting configuration items.

Calling a config object with keyword values must set those values immediately and return the config as a context manager. Entering the context must keep the temporary values active. Exiting the context must restore the previous values. Entering a config object as a context manager without first calling it with keyword values must raise `RuntimeError`.

`nx.config` must be a global `NetworkXConfig` instance with mapping and attribute access. `cache_converted_graphs` and `fallback_to_nx` assignments must require booleans. `warnings_to_ignore` must require a set of strings and must reject unknown warning names with `ValueError`.

## Error Semantics

All public NetworkX exceptions must inherit from `NetworkXException`.

- `NetworkXError` must represent serious user-facing graph and conversion errors.
- `NetworkXPointlessConcept` must represent algorithms given a null graph where the concept is undefined.
- `NetworkXAlgorithmError` must represent unexpected algorithm termination.
- `NetworkXUnfeasible`, `NetworkXNoPath`, and `NetworkXNoCycle` must represent infeasible path, cycle, or solution requests.
- `NetworkXUnbounded` must represent unbounded optimization problems.
- `NetworkXNotImplemented` must represent operations not implemented for a graph type.
- `NodeNotFound` must represent requests for a node that is absent from the graph.
- `AmbiguousSolution` must represent cases with more than one valid intermediate solution where guessing would be wrong.
- `ExceededMaxIterations` must represent iterative procedures that exceed their iteration limit.
- `PowerIterationFailedConvergence(num_iterations)` must inherit from `ExceededMaxIterations` and must create an error message stating that power iteration failed to converge within the supplied number of iterations.

Graph mutation and conversion methods must use these exception classes where specified above. Python container protocol errors such as missing view keys must use `KeyError` where the public API behaves like a mapping.

## Cross-View Invariants

1. A node added through `G.add_node(n, **attrs)` must appear through `n in G`, iteration over `G`, `G.nodes`, `G.adj`, and `G.degree`, and `G.nodes[n]` must return the same node attributes.
2. An edge added through `G.add_edge(u, v, **attrs)` must appear through `G.has_edge(u, v)`, `G.edges`, `G.adj[u]`, `G[u][v]`, and the relevant degree views, and all edge-attribute access paths must return the same attributes.
3. A node removed through `G.remove_node(n)` must disappear from node views, adjacency views, edge views, and degree views, and all incident edges must disappear from edge views.
4. A simple edge attribute written through `G[u][v][name]` must return through `G.edges[u, v][name]`, `G.get_edge_data(u, v)[name]`, and `to_dict_of_dicts(G)[u][v][name]`.
5. A multigraph edge attribute written through `G[u][v][key][name]` must return through `G.edges[u, v, key][name]`, `G.get_edge_data(u, v, key)[name]`, and `to_dict_of_dicts(G)[u][v][key][name]`.
6. In directed graphs, an edge `u -> v` must appear in `G.succ[u]`, `G.pred[v]`, `G.out_edges(u)`, `G.in_edges(v)`, `G.successors(u)`, and `G.predecessors(v)`.
7. A live graph view returned by `subgraph_view`, `generic_graph_view`, `reverse_view`, `G.subgraph`, or `G.edge_subgraph` must reflect later structural changes made to the original graph whenever those changes pass the view's filters.
8. A successful conversion produced by `to_dict_of_lists`, `to_dict_of_dicts`, or `to_edgelist` must reflect the graph state at the time the conversion function is called; later graph mutation must not mutate plain Python containers already returned by conversion functions.
9. A frozen graph or read-only graph view must continue returning current graph data through views and mappings, and structural mutation attempts through that object must raise `NetworkXError`.

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

## Non-Goals

This specification does not cover the full NetworkX algorithm catalogue, including shortest paths, traversal algorithms, centrality, clustering, connectivity, flow, matching, planarity, isomorphism, approximation, community detection, tree algorithms, DAG algorithms, and graph hashing.

This specification does not cover graph generator behavior beyond helper mutations such as `add_path`, `add_star`, and `add_cycle`.

This specification does not cover NumPy, SciPy, pandas, PyGraphviz, pydot, matplotlib, or backend-dispatch integration beyond rejecting or delegating inputs as described for the pure-Python core.

This specification does not cover exact serialization contracts for adjacency list, multiline adjacency list, edge list files, GML, GraphML, GEXF, LEDA, Pajek, graph6, sparse6, matrix market, JSON graph formats, or drawing/image output. The only read/write format covered here is network text.

This specification does not require performance parity, memory-layout parity, private attributes, private helper functions, cache internals, subclass factory customization, or exact `repr` strings for view objects.

## Evaluation Notes

Evaluation checks behavior through public imports and public APIs only. It exercises graph construction, mutation, attribute propagation, live views, conversion round-trips, graph views, network text output, config mapping behavior, and documented error paths. Scoring rewards user-observable compatibility: correct returned values, correct mutations, correct live-view coherence, and correct exception classes.

Tests do not require private storage layouts, optional numerical or plotting dependencies, backend implementations, or exhaustive graph algorithms outside this scope. Inputs are chosen to cover ordinary graphs, directed graphs, multigraphs, self-loops, duplicate edges, filtered views, missing nodes, missing edges, and conversion edge cases.
