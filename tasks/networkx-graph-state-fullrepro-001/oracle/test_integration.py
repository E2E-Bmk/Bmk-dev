import io

import pytest
import networkx as nx
from networkx.utils.configs import Config


def test_product_overview_mutable_graph_node_and_edge_attributes():
    """Seam: state consistency — product overview mutable graph node and edge attributes."""
    G = nx.Graph(project="demo")
    G.add_node(("station", 1), zone=2)
    G.add_edge(("station", 1), "B", weight=7)
    assert G.graph["project"] == "demo"
    assert G.nodes[("station", 1)]["zone"] == 2
    assert G.edges[("station", 1), "B"]["weight"] == 7


def test_product_overview_graph_is_python_container():
    """Seam: state consistency — product overview graph is python container."""
    G = nx.Graph()
    G.add_nodes_from(["A", "B"])
    assert "A" in G
    assert len(G) == 2
    assert list(G) == ["A", "B"]


def test_product_overview_reporting_views_are_live():
    """Seam: state consistency — product overview reporting views are live."""
    G = nx.Graph()
    nodes = G.nodes
    edges = G.edges
    G.add_edge("A", "B", color="red")
    assert "A" in nodes
    assert ("A", "B") in edges
    assert edges["A", "B"]["color"] == "red"


def test_product_state_model_node_projection_coherence():
    """Seam: state consistency — product state model node projection coherence."""
    G = nx.Graph()
    G.add_node("A", color="red")
    assert "A" in G
    assert "A" in list(G)
    assert "A" in G.nodes
    assert "A" in G.adj
    assert G.degree["A"] == 0
    assert G.nodes["A"]["color"] == "red"


def test_product_state_model_edge_projection_coherence():
    """Seam: state consistency — product state model edge projection coherence."""
    G = nx.Graph()
    G.add_edge("A", "B", weight=2)
    assert G.has_edge("A", "B")
    assert ("A", "B") in G.edges
    assert "B" in G.adj["A"]
    assert G["A"]["B"]["weight"] == 2
    assert G.degree["A"] == 1


def test_product_state_model_attribute_mutation_through_views():
    """Seam: state consistency — product state model attribute mutation through views."""
    G = nx.Graph()
    G.add_edge("A", "B", weight=2)
    G.nodes["A"]["color"] = "blue"
    G.edges["A", "B"]["weight"] = 5
    assert G.nodes(data="color")["A"] == "blue"
    assert G["A"]["B"]["weight"] == 5


def test_copying_subgraphs_copy_is_independent():
    """Seam: state consistency — copying subgraphs copy is independent."""
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    H = G.copy()
    H.edges["A", "B"]["weight"] = 5
    H.add_edge("B", "C")
    assert G.edges["A", "B"]["weight"] == 1
    assert "C" not in G


def test_copying_subgraphs_copy_as_view_is_readonly_and_live():
    """Seam: state consistency — copying subgraphs copy as view is readonly and live."""
    G = nx.Graph()
    G.add_edge("A", "B")
    view = G.copy(as_view=True)
    G.add_edge("B", "C")
    assert ("B", "C") in view.edges
    with pytest.raises(nx.NetworkXError):
        view.add_node("D")


def test_copying_subgraphs_node_induced_subgraph_shares_attrs():
    """Seam: state consistency — copying subgraphs node induced subgraph shares attrs."""
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    G.add_edge("B", "C", weight=2)
    view = G.subgraph(["A", "B"])
    view.nodes["A"]["color"] = "red"
    assert list(view.edges) == [("A", "B")]
    assert G.nodes["A"]["color"] == "red"
    with pytest.raises(nx.NetworkXError):
        view.add_edge("A", "C")


def test_copying_subgraphs_edge_subgraph_filters_edges_and_shares_attrs():
    """Seam: state consistency — copying subgraphs edge subgraph filters edges and shares attrs."""
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    G.add_edge("B", "C", weight=2)
    view = G.edge_subgraph([("A", "B"), ("X", "Y")])
    assert list(view.nodes) == ["A", "B"]
    view.edges["A", "B"]["weight"] = 9
    assert G.edges["A", "B"]["weight"] == 9


def test_copying_subgraphs_to_directed_copies_attrs_and_arcs():
    """Seam: state consistency — copying subgraphs to directed copies attrs and arcs."""
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    H = G.to_directed()
    assert sorted(H.edges) == [("A", "B"), ("B", "A")]
    assert H.edges["A", "B"]["weight"] == 1


def test_copying_subgraphs_to_undirected_reciprocal_keeps_mutual_edges():
    """Seam: state consistency — copying subgraphs to undirected reciprocal keeps mutual edges."""
    G = nx.DiGraph()
    G.add_edge("A", "B", weight=1)
    G.add_edge("B", "A", weight=2)
    G.add_edge("B", "C", weight=3)
    H = G.to_undirected(reciprocal=True)
    assert set(H.edges) == {("A", "B")}
    assert "C" in H


def test_copying_subgraphs_as_view_conversion_is_readonly_live():
    """Seam: state consistency — copying subgraphs as view conversion is readonly live."""
    G = nx.Graph()
    G.add_edge("A", "B")
    H = G.to_directed(as_view=True)
    G.add_edge("B", "C")
    assert ("B", "C") in H.edges
    with pytest.raises(nx.NetworkXError):
        H.add_edge("C", "D")


def test_conversions_to_networkx_graph_clears_supplied_instance():
    """Seam: lifecycle crossing — conversions to networkx graph clears supplied instance."""
    target = nx.Graph()
    target.add_edge("old", "node")
    result = nx.to_networkx_graph([("A", "B")], create_using=target)
    assert result is target
    assert set(target.edges) == {("A", "B")}
    assert "old" not in target


def test_conversions_from_graph_preserves_attrs_and_multikeys():
    """Seam: state consistency — conversions from graph preserves attrs and multikeys."""
    G = nx.MultiDiGraph(name="routes")
    G.add_node("A", kind="station")
    G.add_edge("A", "B", key="red", weight=2)
    H = nx.Graph(G)
    assert H.graph["name"] == "routes"
    assert H.nodes["A"]["kind"] == "station"
    assert H.edges["A", "B"]["weight"] == 2


def test_conversions_dict_of_lists_round_trip_and_nodelist_filter():
    """Seam: state consistency — conversions dict of lists round trip and nodelist filter."""
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("B", "C")])
    assert nx.to_dict_of_lists(G, nodelist=["A", "B"]) == {"A": ["B"], "B": ["A"]}
    H = nx.from_dict_of_lists({"A": ["B"], "B": ["A"]}, create_using=nx.MultiGraph())
    assert H.number_of_edges("A", "B") == 1


def test_conversions_dict_of_dicts_round_trip_simple_and_multigraph():
    """Seam: state consistency — conversions dict of dicts round trip simple and multigraph."""
    G = nx.MultiGraph()
    G.add_edge("A", "B", key="r1", weight=2)
    data = nx.to_dict_of_dicts(G)
    assert data["A"]["B"]["r1"] == {"weight": 2}
    H = nx.from_dict_of_dicts(data, create_using=nx.MultiGraph(), multigraph_input=True)
    assert H.edges["A", "B", "r1"]["weight"] == 2


def test_conversions_to_dict_of_dicts_scalar_edge_data_omits_multikeys():
    """Seam: state consistency — conversions to dict of dicts scalar edge data omits multikeys."""
    G = nx.MultiGraph()
    G.add_edge("A", "B", key="r1", weight=2)
    assert nx.to_dict_of_dicts(G, edge_data=1) == {"A": {"B": 1}, "B": {"A": 1}}


def test_conversions_edgelist_round_trip_and_invalid_tuple_error():
    """Seam: state consistency — conversions edgelist round trip and invalid tuple error."""
    G = nx.from_edgelist([("A", "B", {"weight": 2})])
    assert list(nx.to_edgelist(G)) == [("A", "B", {"weight": 2})]
    with pytest.raises(nx.NetworkXError):
        nx.from_edgelist([("bad",)])


def test_graph_views_generic_view_is_frozen_shared_and_live():
    """Seam: state consistency — graph views generic view is frozen shared and live."""
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    view = nx.graphviews.generic_graph_view(G)
    view.edges["A", "B"]["weight"] = 3
    G.add_edge("B", "C")
    assert G.edges["A", "B"]["weight"] == 3
    assert ("B", "C") in view.edges
    assert nx.is_frozen(view)


def test_graph_views_subgraph_view_filters_nodes_and_edges():
    """Seam: state consistency — graph views subgraph view filters nodes and edges."""
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
    view = nx.subgraph_view(
        G,
        filter_node=lambda n: n != "D",
        filter_edge=lambda u, v: {u, v} != {"A", "B"},
    )
    assert list(view.nodes) == ["A", "B", "C"]
    assert list(view.edges) == [("B", "C")]
    with pytest.raises(nx.NetworkXError):
        view.add_edge("A", "C")


def test_graph_views_subgraph_view_filter_exceptions_propagate():
    """Seam: error propagation — graph views subgraph view filter exceptions propagate."""
    G = nx.Graph()
    G.add_edge("A", "B")
    def bad_filter(node):
        raise RuntimeError("boom")
    view = nx.subgraph_view(G, filter_node=bad_filter)
    with pytest.raises(RuntimeError):
        list(view.nodes)


def test_graph_views_multigraph_edge_filter_receives_key():
    """Seam: state consistency — graph views multigraph edge filter receives key."""
    G = nx.MultiGraph()
    G.add_edge("A", "B", key="keep")
    G.add_edge("A", "B", key="drop")
    view = nx.subgraph_view(G, filter_edge=lambda u, v, k: k == "keep")
    assert list(view.edges(keys=True)) == [("A", "B", "keep")]


def test_graph_views_reverse_view_reverses_directed_edges_and_rejects_undirected():
    """Seam: error propagation — graph views reverse view reverses directed edges and rejects undirected."""
    G = nx.DiGraph()
    G.add_edge("A", "B")
    view = nx.reverse_view(G)
    assert list(view.edges) == [("B", "A")]
    with pytest.raises(nx.NetworkXNotImplemented):
        nx.reverse_view(nx.Graph())


def test_cross_view_invariant_node_removed_from_all_public_views():
    """CVI-N: node removed from all public views."""
    G = nx.Graph()
    G.add_edge("A", "B")
    G.remove_node("A")
    assert "A" not in G
    assert "A" not in G.nodes
    assert "A" not in G.adj
    assert list(G.edges) == []


def test_cross_view_invariant_simple_edge_attribute_paths_agree():
    """CVI-N: simple edge attribute paths agree."""
    G = nx.Graph()
    G.add_edge("A", "B")
    G["A"]["B"]["color"] = "red"
    assert G.edges["A", "B"]["color"] == "red"
    assert G.get_edge_data("A", "B")["color"] == "red"
    assert nx.to_dict_of_dicts(G)["A"]["B"]["color"] == "red"


def test_cross_view_invariant_multigraph_edge_attribute_paths_agree():
    """CVI-N: multigraph edge attribute paths agree."""
    G = nx.MultiGraph()
    key = G.add_edge("A", "B")
    G["A"]["B"][key]["route"] = "blue"
    assert G.edges["A", "B", key]["route"] == "blue"
    assert G.get_edge_data("A", "B", key)["route"] == "blue"
    assert nx.to_dict_of_dicts(G)["A"]["B"][key]["route"] == "blue"


def test_cross_view_invariant_directed_edge_public_projections_agree():
    """CVI-N: directed edge public projections agree."""
    G = nx.DiGraph()
    G.add_edge("A", "B")
    assert "B" in G.succ["A"]
    assert "A" in G.pred["B"]
    assert list(G.out_edges("A")) == [("A", "B")]
    assert list(G.in_edges("B")) == [("A", "B")]
    assert list(G.successors("A")) == ["B"]
    assert list(G.predecessors("B")) == ["A"]


def test_cross_view_invariant_plain_conversion_snapshots_are_not_live():
    """CVI-N: plain conversion snapshots are not live."""
    G = nx.Graph()
    G.add_edge("A", "B")
    data = nx.to_dict_of_lists(G)
    G.add_edge("B", "C")
    assert data == {"A": ["B"], "B": ["A"]}


def test_representative_workflow_multidigraph_routes_and_red_view():
    """Seam: lifecycle crossing — representative workflow multidigraph routes and red view."""
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
    red_view = nx.subgraph_view(G, filter_edge=lambda u, v, k: G[u][v][k].get("route") == "red")
    assert list(red_view.edges(keys=True)) == [("A", "B", 0), ("B", "C", 0)]


def test_representative_workflow_filtered_view_copy_and_text():
    """Seam: lifecycle crossing — representative workflow filtered view copy and text."""
    G = nx.MultiDiGraph()
    G.add_edge("A", "B", route="red", weight=2)
    G.add_edge("A", "B", route="blue", weight=3)
    G.add_edge("B", "C", route="red", weight=5)
    red_view = nx.subgraph_view(G, filter_edge=lambda u, v, k: G[u][v][k].get("route") == "red")
    H = nx.MultiDiGraph(red_view)
    assert H.edges["A", "B", 0]["weight"] == 2
    assert list(nx.generate_network_text(H, sources=["A"], ascii_only=True)) == [
        "+-- A",
        "    L-> B",
        "        L-> C",
    ]


def test_representative_workflow_conversion_roundtrip_preserves_public_state():
    """Seam: state consistency — representative workflow conversion roundtrip preserves public state."""
    G = nx.MultiDiGraph()
    G.add_edge("A", "B", key="red", weight=2)
    data = nx.to_dict_of_dicts(G)
    H = nx.from_dict_of_dicts(data, create_using=nx.MultiDiGraph(), multigraph_input=True)
    assert list(H.edges(keys=True, data="weight")) == [("A", "B", "red", 2)]


