import io

import pytest
import networkx as nx
from networkx.utils.configs import Config


def test_scope_core_graph_classes_are_available():
    assert nx.Graph().is_directed() is False
    assert nx.DiGraph().is_directed() is True
    assert nx.MultiGraph().is_multigraph() is True
    assert nx.MultiDiGraph().is_directed() is True


def test_scope_pure_python_conversion_and_text_are_available():
    G = nx.from_edgelist([("A", "B")])
    assert nx.to_dict_of_lists(G) == {"A": ["B"], "B": ["A"]}
    assert list(nx.generate_network_text(G, sources=["A"], ascii_only=True))[0] == "+-- A"


def test_scope_config_and_exceptions_are_public():
    assert issubclass(nx.NetworkXError, nx.NetworkXException)
    assert "cache_converted_graphs" in nx.config


def test_installable_surface_root_exports_graph_classes():
    for graph_type in [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]:
        G = graph_type(name="root")
        assert G.graph["name"] == "root"


def test_installable_surface_root_exports_conversion_functions():
    G = nx.from_dict_of_lists({"A": ["B"], "B": []})
    assert sorted(G.nodes) == ["A", "B"]
    assert list(nx.to_edgelist(G)) == [("A", "B", {})]


def test_installable_surface_network_text_and_config_imports():
    stream = io.StringIO()
    nx.write_network_text(nx.Graph(), path=stream, ascii_only=True)
    assert stream.getvalue().endswith("\n")
    assert Config(alpha=1)["alpha"] == 1


def test_public_api_root_helper_delegates_to_graph_methods():
    G = nx.Graph()
    G.add_edge("A", "B")
    assert nx.number_of_nodes(G) == G.number_of_nodes() == 2
    assert nx.number_of_edges(G) == G.number_of_edges() == 1
    assert list(nx.neighbors(G, "A")) == list(G.neighbors("A")) == ["B"]


def test_public_api_graphviews_module_is_public():
    G = nx.Graph()
    G.add_edge("A", "B")
    view = nx.graphviews.generic_graph_view(G)
    assert list(view.edges) == [("A", "B")]
    assert nx.is_frozen(view)


def test_public_api_exception_classes_constructible():
    exc = nx.PowerIterationFailedConvergence(4)
    assert isinstance(exc, nx.ExceededMaxIterations)
    assert isinstance(exc, nx.NetworkXException)
    with pytest.raises(nx.NetworkXNotImplemented):
        nx.reverse_view(nx.Graph())


def test_graph_classes_constructor_empty_and_graph_attrs():
    G = nx.Graph(owner="team", backend="networkx")
    assert len(G) == 0
    assert G.graph["owner"] == "team"
    assert "backend" not in G.graph


def test_graph_classes_constructor_loads_incoming_edge_list():
    G = nx.DiGraph([("A", "B"), ("B", "C")], name="path")
    assert list(G.edges) == [("A", "B"), ("B", "C")]
    assert G.graph["name"] == "path"


def test_graph_classes_none_nodes_are_rejected():
    G = nx.Graph()
    with pytest.raises(ValueError):
        G.add_node(None)
    with pytest.raises(ValueError):
        G.add_edge("A", None)


def test_graph_classes_unhashable_membership_returns_false():
    G = nx.Graph()
    assert [] not in G
    assert G.has_node([]) is False


def test_graph_classes_add_node_updates_existing_attrs():
    G = nx.Graph()
    G.add_node("A", color="red")
    G.add_node("A", size=3)
    assert G.nodes["A"] == {"color": "red", "size": 3}


def test_graph_classes_add_nodes_from_attr_precedence():
    G = nx.Graph()
    G.add_nodes_from([("A", {"color": "red"}), "B"], color="blue", zone=1)
    assert G.nodes["A"] == {"color": "red", "zone": 1}
    assert G.nodes["B"] == {"color": "blue", "zone": 1}


def test_graph_classes_simple_edge_update_does_not_increase_count():
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    G.add_edge("A", "B", color="red")
    assert G.number_of_edges() == 1
    assert G.edges["A", "B"] == {"weight": 1, "color": "red"}


def test_graph_classes_add_edges_from_attr_precedence_and_invalid_length():
    G = nx.Graph()
    G.add_edges_from([("A", "B", {"weight": 3}), ("B", "C")], weight=1, color="red")
    assert G.edges["A", "B"] == {"weight": 3, "color": "red"}
    assert G.edges["B", "C"] == {"weight": 1, "color": "red"}
    with pytest.raises(nx.NetworkXError):
        G.add_edges_from([("bad",)])


def test_graph_classes_remove_missing_simple_edge_errors_but_bulk_ignores():
    G = nx.Graph()
    with pytest.raises(nx.NetworkXError):
        G.remove_edge("A", "B")
    G.remove_edges_from([("A", "B")])
    assert G.number_of_edges() == 0


def test_graph_classes_multigraph_default_keys_lowest_unused():
    G = nx.MultiGraph()
    assert G.add_edge("A", "B") == 0
    assert G.add_edge("A", "B") == 1
    assert sorted(G["A"]["B"]) == [0, 1]


def test_graph_classes_multigraph_supplied_key_updates_existing_edge():
    G = nx.MultiDiGraph()
    assert G.add_edge("A", "B", key="r1", color="red") == "r1"
    assert G.add_edge("A", "B", key="r1", weight=4) == "r1"
    assert G.number_of_edges() == 1
    assert G.edges["A", "B", "r1"] == {"color": "red", "weight": 4}


def test_graph_classes_multigraph_remove_edge_without_key_removes_latest():
    G = nx.MultiGraph()
    G.add_edge("A", "B", key="first")
    G.add_edge("A", "B", key="second")
    G.remove_edge("A", "B")
    assert list(G["A"]["B"].keys()) == ["first"]


def test_reporting_views_nodes_data_and_default():
    G = nx.Graph()
    G.add_node("A", color="red")
    G.add_node("B")
    assert list(G.nodes(data=True)) == [("A", {"color": "red"}), ("B", {})]
    assert dict(G.nodes(data="color", default="none")) == {"A": "red", "B": "none"}


def test_reporting_views_node_view_is_read_only_mapping_shell():
    G = nx.Graph()
    G.add_node("A")
    G.nodes["A"]["color"] = "blue"
    assert G.nodes["A"]["color"] == "blue"
    with pytest.raises(TypeError):
        G.nodes["B"] = {}


def test_reporting_views_simple_edges_data_and_default():
    G = nx.Graph()
    G.add_edge("A", "B", weight=2)
    G.add_edge("B", "C")
    assert list(G.edges(data="weight", default=1)) == [("A", "B", 2), ("B", "C", 1)]


def test_reporting_views_multigraph_edges_keys_and_duplicate_pairs():
    G = nx.MultiGraph()
    G.add_edge("A", "B", key="r1")
    G.add_edge("A", "B", key="r2")
    assert list(G.edges(keys=False)) == [("A", "B"), ("A", "B")]
    assert list(G.edges(keys=True)) == [("A", "B", "r1"), ("A", "B", "r2")]


def test_reporting_views_adjacency_projection_matches_getitem():
    G = nx.Graph()
    G.add_edge("A", "B", weight=8)
    assert G.adj["A"] == G["A"]
    assert G["A"]["B"] == {"weight": 8}
    with pytest.raises(KeyError):
        G["missing"]


def test_reporting_views_degree_unweighted_weighted_and_self_loop():
    G = nx.Graph()
    G.add_edge("A", "B", weight=2)
    G.add_edge("A", "A", weight=5)
    assert G.degree["A"] == 3
    assert G.degree("A", weight="weight") == 12


def test_reporting_views_directed_successor_predecessor_and_degree():
    G = nx.DiGraph()
    G.add_edge("A", "B", weight=3)
    assert G.adj == G.succ
    assert list(G.neighbors("A")) == list(G.successors("A")) == ["B"]
    assert list(G.predecessors("B")) == ["A"]
    assert G.degree["B"] == G.in_degree["B"] + G.out_degree["B"]
    assert G.has_successor("missing", "B") is False


def test_public_helper_functions_add_path_star_cycle_edge_cases():
    G = nx.Graph()
    nx.add_path(G, ["A"])
    nx.add_star(G, [])
    nx.add_cycle(G, ["B"])
    assert "A" in G
    assert G.has_edge("B", "B")
    nx.add_star(G, ["S", "L1", "L2"], color="red")
    assert set(G.edges("S")) >= {("S", "L1"), ("S", "L2")}
    assert G.edges["S", "L1"]["color"] == "red"


def test_public_helper_functions_attribute_set_get_ignore_missing_nodes():
    G = nx.Graph()
    G.add_nodes_from(["A", "B"])
    nx.set_node_attributes(G, {"A": 1, "missing": 2}, "rank")
    assert nx.get_node_attributes(G, "rank") == {"A": 1}
    assert nx.get_node_attributes(G, "rank", default=0) == {"A": 1, "B": 0}


def test_public_helper_functions_attribute_set_get_ignore_missing_edges():
    G = nx.Graph()
    G.add_edge("A", "B")
    nx.set_edge_attributes(G, {("A", "B"): 5, ("X", "Y"): 9}, "weight")
    assert nx.get_edge_attributes(G, "weight") == {("A", "B"): 5}
    assert nx.get_edge_attributes(G, "weight", default=1) == {("A", "B"): 5}


def test_public_helper_functions_freeze_blocks_structure_not_attrs():
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    nx.freeze(G)
    assert nx.is_frozen(G)
    G.edges["A", "B"]["weight"] = 2
    assert G.edges["A", "B"]["weight"] == 2
    with pytest.raises(nx.NetworkXError):
        G.add_node("C")


def test_network_text_empty_graph_and_ascii_root():
    assert list(nx.generate_network_text(nx.Graph(), ascii_only=True)) == ["+"]


def test_network_text_max_depth_zero_uses_ellipsis():
    G = nx.Graph()
    nx.add_path(G, ["A", "B", "C"])
    lines = list(nx.generate_network_text(G, sources=["A"], max_depth=0, ascii_only=True))
    assert lines == ["+ ..."]


def test_network_text_sources_limit_displayed_component():
    G = nx.Graph()
    G.add_edge("A", "B")
    G.add_edge("X", "Y")
    lines = list(nx.generate_network_text(G, sources=["A"], ascii_only=True))
    assert any("A" in line for line in lines)
    assert all("X" not in line and "Y" not in line for line in lines)


def test_network_text_labels_collapse_and_ascii_observed_output():
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("A", "C")
    G.add_edge("B", "D")
    G.nodes["A"]["label"] = "root"
    G.nodes["B"]["collapse"] = True
    assert list(nx.generate_network_text(G, sources=["A"], ascii_only=True)) == [
        "+-- root",
        "    |-> B",
        "    |   L->  ...",
        "    L-> C",
    ]


def test_network_text_with_labels_named_attribute_and_false():
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.nodes["A"]["title"] = "Alpha"
    named = list(nx.generate_network_text(G, sources=["A"], with_labels="title", ascii_only=True))
    raw = list(nx.generate_network_text(G, sources=["A"], with_labels=False, ascii_only=True))
    assert named[0] == "+-- Alpha"
    assert raw[0] == "+-- A"


def test_network_text_write_to_file_like_callable_and_stdout(capsys):
    G = nx.Graph()
    stream = io.StringIO()
    nx.write_network_text(G, path=stream, ascii_only=True, end="|")
    assert stream.getvalue() == "+|"
    calls = []
    nx.write_network_text(G, path=calls.append, ascii_only=True)
    assert calls == ["+\n"]
    nx.write_network_text(G, path=None, ascii_only=True)
    assert capsys.readouterr().out == "+\n"


def test_network_text_invalid_path_raises_type_error():
    with pytest.raises(TypeError):
        nx.write_network_text(nx.Graph(), path=object())


def test_config_flexible_mapping_semantics():
    cfg = Config(alpha=1, beta="x")
    assert "alpha" in cfg
    assert list(cfg) == ["alpha", "beta"]
    assert len(cfg) == 2
    assert list(reversed(cfg)) == ["beta", "alpha"]
    assert cfg.get("missing", 9) == 9
    assert list(cfg.items()) == [("alpha", 1), ("beta", "x")]


def test_config_strict_annotations_reject_unknown_keys():
    class Strict(Config):
        alpha: int
        beta: str
    cfg = Strict(alpha=1, beta="x")
    cfg.alpha = 2
    cfg["beta"] = "y"
    assert list(cfg.items()) == [("alpha", 2), ("beta", "y")]
    with pytest.raises(AttributeError):
        cfg.gamma = 3
    with pytest.raises(KeyError):
        cfg["gamma"] = 3


def test_config_strict_deletion_errors_and_flexible_deletion():
    class Strict(Config):
        alpha: int
    cfg = Strict(alpha=1)
    with pytest.raises(TypeError):
        del cfg.alpha
    with pytest.raises(TypeError):
        del cfg["alpha"]
    class Flexible(Config, strict=False):
        alpha: int
    flex = Flexible(alpha=1)
    del flex["alpha"]
    assert list(flex.items()) == []


def test_config_context_manager_restores_values_and_rejects_uncalled_enter():
    cfg = Config(alpha=1, beta=2)
    with cfg(alpha=5):
        assert cfg.alpha == 5
        assert cfg.beta == 2
    assert cfg.alpha == 1
    with pytest.raises(RuntimeError):
        with cfg:
            pass


def test_config_global_networkx_config_validates_assignment_types():
    original_cache = nx.config.cache_converted_graphs
    original_fallback = nx.config.fallback_to_nx
    original_warnings = set(nx.config.warnings_to_ignore)
    try:
        nx.config.cache_converted_graphs = not original_cache
        nx.config.fallback_to_nx = not original_fallback
        nx.config.warnings_to_ignore = set()
        assert isinstance(nx.config.cache_converted_graphs, bool)
        with pytest.raises(TypeError):
            nx.config.cache_converted_graphs = "yes"
        with pytest.raises(TypeError):
            nx.config.warnings_to_ignore = ["cache"]
        with pytest.raises(ValueError):
            nx.config.warnings_to_ignore = {"not-a-networkx-warning"}
    finally:
        nx.config.cache_converted_graphs = original_cache
        nx.config.fallback_to_nx = original_fallback
        nx.config.warnings_to_ignore = original_warnings


def test_error_semantics_public_exceptions_share_base_class():
    public_errors = [
        nx.NetworkXError,
        nx.NetworkXNotImplemented,
        nx.NodeNotFound,
        nx.NetworkXNoPath,
        nx.NetworkXNoCycle,
        nx.NetworkXUnfeasible,
        nx.NetworkXUnbounded,
        nx.AmbiguousSolution,
        nx.ExceededMaxIterations,
    ]
    assert all(issubclass(err, nx.NetworkXException) for err in public_errors)
    with pytest.raises(nx.NetworkXError):
        nx.Graph().remove_edge("missing", "edge")


def test_error_semantics_missing_nodes_and_edges_use_documented_classes():
    G = nx.Graph()
    with pytest.raises(nx.NetworkXError):
        G.remove_node("missing")
    with pytest.raises(nx.NetworkXError):
        nx.neighbors(G, "missing")
    with pytest.raises(KeyError):
        G.nodes["missing"]


def test_error_semantics_directed_missing_neighbor_methods_raise_networkxerror():
    G = nx.DiGraph()
    with pytest.raises(nx.NetworkXError):
        list(G.successors("missing"))
    with pytest.raises(nx.NetworkXError):
        list(G.predecessors("missing"))


def test_error_semantics_power_iteration_exception_is_specific():
    exc = nx.PowerIterationFailedConvergence(7)
    assert isinstance(exc, nx.ExceededMaxIterations)
    assert isinstance(exc, nx.NetworkXException)
    with pytest.raises(nx.NetworkXError):
        nx.Graph().remove_node("missing")


def test_error_semantics_missing_mapping_view_keys_raise_key_error():
    G = nx.Graph()
    G.add_node("A")
    with pytest.raises(KeyError):
        G.nodes["missing"]
    with pytest.raises(KeyError):
        G.adj["missing"]


def test_non_goals_core_graph_behavior_does_not_require_algorithm_catalogue():
    G = nx.Graph()
    nx.add_path(G, ["A", "B", "C"])
    assert list(G.edges) == [("A", "B"), ("B", "C")]


def test_non_goals_pure_python_conversion_does_not_require_optional_numeric_types():
    G = nx.from_dict_of_dicts({"A": {"B": {"weight": 2}}})
    assert nx.to_dict_of_dicts(G)["A"]["B"]["weight"] == 2


def test_non_goals_behavioral_views_without_repr_contract():
    G = nx.Graph()
    G.add_nodes_from(["A", "B"])
    assert set(G.nodes) == {"A", "B"}
    assert list(G.nodes(data="missing", default=None)) == [("A", None), ("B", None)]


def test_evaluation_notes_public_imports_only_workflow():
    import networkx as public_nx
    G = public_nx.Graph()
    G.add_edge("A", "B")
    assert public_nx.number_of_edges(G) == 1


def test_evaluation_notes_no_private_storage_needed_for_attribute_checks():
    G = nx.Graph()
    G.add_edge("A", "B", weight=3)
    assert G.edges["A", "B"]["weight"] == 3
    assert list(nx.to_edgelist(G)) == [("A", "B", {"weight": 3})]


def test_evaluation_notes_error_paths_use_public_exception_types():
    G = nx.Graph()
    with pytest.raises(nx.NetworkXError):
        G.remove_edge("A", "B")


