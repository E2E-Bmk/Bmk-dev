from __future__ import annotations
from pathlib import Path
import networkx as nx


def test_a01(tmp_path: Path) -> None:
    graph = nx.Graph(project="alpha"); graph.add_node("a", color="red"); graph.add_edge("a", "b", weight=2)
    graph.add_edge("b", "a", label="same")
    assert graph.number_of_edges() == 1 and graph["a"]["b"] == {"weight":2,"label":"same"}
    assert graph.nodes["a"]["color"] == "red" and graph.graph["project"] == "alpha"


def test_a02(tmp_path: Path) -> None:
    graph = nx.DiGraph(); graph.add_edges_from([("a","b"),("c","b"),("b","b")])
    assert list(graph.successors("a")) == ["b"] and set(graph.predecessors("b")) == {"a","b","c"}
    assert graph.in_degree("b") == 3 and graph.out_degree("b") == 1


def test_a03(tmp_path: Path) -> None:
    graph = nx.MultiGraph(); assert graph.add_edge("a","b") == 0 and graph.add_edge("a","b") == 1
    graph.remove_edge("a","b",0); assert graph.add_edge("b","a") == 2
    graph.remove_edge("a","b"); assert sorted(graph["a"]["b"]) == [1]


def test_a04(tmp_path: Path) -> None:
    graph = nx.path_graph(4); live = graph.subgraph([0,1,2]); frozen = live.copy()
    graph.remove_edge(1,2); graph.nodes[1]["mark"] = True
    assert list(live.edges()) == [(0,1)] and live.nodes[1]["mark"] is True
    assert list(frozen.edges()) == [(0,1),(1,2)] and "mark" not in frozen.nodes[1]


def test_a05(tmp_path: Path) -> None:
    graph = nx.MultiDiGraph(); graph.add_edge("a","b",key="k",weight=3)
    payload = nx.node_link_data(graph, edges="links"); rebuilt = nx.node_link_graph(payload, edges="links")
    assert rebuilt.is_directed() and rebuilt.is_multigraph() and rebuilt["a"]["b"]["k"]["weight"] == 3


def test_a06(tmp_path: Path) -> None:
    graph = nx.Graph(); graph.add_weighted_edges_from([("a","b",2),("b","c",1),("a","c",8)])
    assert nx.shortest_path(graph,"a","c",weight="weight") == ["a","b","c"]
    assert nx.single_source_shortest_path_length(graph,"a",cutoff=1) == {"a":0,"b":1,"c":1}


def test_i01(tmp_path: Path) -> None:
    graph = nx.Graph(); graph.add_edges_from([(1,2),(2,3)]); nodes = graph.nodes; edges = graph.edges
    graph.remove_node(2); graph.add_node(2, generation=2); graph.add_edge(3,2, weight=4)
    assert set(nodes) == {1,2,3} and {frozenset(edge) for edge in edges} == {frozenset((2,3))} and nodes[2]["generation"] == 2


def test_i02(tmp_path: Path) -> None:
    graph = nx.MultiDiGraph(); graph.add_edge("a","b",key="x",v=1); graph.add_edge("b","a",key="y",v=2)
    reverse = graph.reverse(copy=False); reverse["b"]["a"]["x"]["v"] = 3
    assert graph["a"]["b"]["x"]["v"] == 3 and sorted(reverse.edges(keys=True)) == [("a","b","y"),("b","a","x")]


def test_i03(tmp_path: Path) -> None:
    graph = nx.DiGraph(); graph.add_edges_from([(0,1),(1,2),(2,3),(3,0)])
    view = nx.subgraph_view(graph, filter_node=lambda node: node != 2)
    reverse = nx.reverse_view(view); graph.add_edge(1,3)
    assert set(reverse.edges()) == {(0,3),(1,0),(3,1)} and set(reverse) == {0,1,3}


def test_i04(tmp_path: Path) -> None:
    graph = nx.from_dict_of_dicts({"a":{"b":{"weight":2}},"b":{"c":{"weight":4}},"c":{}})
    directed = graph.to_directed(); data = nx.to_dict_of_dicts(directed)
    assert data["a"]["b"]["weight"] == 2 and data["b"]["a"]["weight"] == 2
    assert nx.to_numpy_array if hasattr(nx, "to_numpy_array") else True


def test_i05(tmp_path: Path) -> None:
    graph = nx.DiGraph([(1,2),(2,1),(2,3),(3,4),(4,3)])
    components = list(nx.strongly_connected_components(graph)); condensed = nx.condensation(graph, components)
    assert nx.is_directed_acyclic_graph(condensed) and sorted(map(len, components)) == [2,2]
    assert nx.has_path(graph,1,4) and not nx.has_path(graph,4,1)


def test_s01(tmp_path: Path) -> None:
    left = nx.path_graph(["a","b","c"]); right = nx.Graph(); right.add_edge("c","d",kind="join")
    merged = nx.compose(left,right); renamed = nx.relabel_nodes(merged,{"a":"root"},copy=True)
    assert set(renamed) == {"root","b","c","d"} and nx.shortest_path(renamed,"root","d") == ["root","b","c","d"]


def test_s02(tmp_path: Path) -> None:
    graph = nx.MultiDiGraph(); graph.add_edges_from([("a","b",{"x":1}),("b","c",{"x":2})])
    view = nx.restricted_view(graph,["c"],[]); snapshot = nx.freeze(view.copy()); graph.add_edge("b","a",x=3)
    assert set(view.edges()) == {("a","b"),("b","a")} and set(snapshot.edges()) == {("a","b")}
    try: snapshot.add_node("z")
    except nx.NetworkXError: pass
    else: raise AssertionError("frozen snapshot accepted mutation")


def test_s03(tmp_path: Path) -> None:
    dag = nx.DiGraph([(1,3),(2,3),(3,4),(2,5)]); order = list(nx.lexicographical_topological_sort(dag))
    closure = nx.transitive_closure_dag(dag)
    assert order.index(2) < order.index(3) < order.index(4) and closure.has_edge(1,4)
    assert set(nx.ancestors(dag,4)) == {1,2,3}
