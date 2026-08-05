from __future__ import annotations

import io
import json

import pytest

from conftest import identifiers, names, named_tree


@pytest.mark.depends_on("test_parent_assignment_reattaches_and_preserves_identity", "test_leaf_root_height_depth_and_size_properties")
def test_mutation_workflow_recomputes_paths_and_sizes():
    from anytree import Node

    root = Node("root")
    left = Node("left", parent=root)
    right = Node("right", parent=root)
    leaf = Node("leaf", parent=left)
    leaf.parent = right
    Node("new", parent=left)
    assert names(root.descendants) == ["left", "new", "right", "leaf"]
    assert leaf.path == (root, right, leaf)
    assert root.size == 5


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_public_imports_expose_requested_surface")
def test_anynode_dict_export_preserves_attributes_and_shape():
    from anytree import AnyNode
    from anytree.exporter import DictExporter

    root = AnyNode(key="root", count=1)
    branch = AnyNode(key="branch", count=2, parent=root)
    AnyNode(key="leaf", count=3, parent=branch)
    data = DictExporter().export(root)
    assert data == {
        "key": "root",
        "count": 1,
        "children": [
            {
                "key": "branch",
                "count": 2,
                "children": [{"key": "leaf", "count": 3}],
            }
        ],
    }


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_public_imports_expose_requested_surface")
def test_json_export_roundtrip_is_verified_from_parsed_data():
    from anytree import AnyNode, PreOrderIter
    from anytree.exporter import JsonExporter
    from anytree.importer import JsonImporter

    root = AnyNode(key="root", count=1)
    AnyNode(key="child", count=2, parent=root)
    payload = JsonExporter(sort_keys=True).export(root)
    parsed = json.loads(payload)
    restored = JsonImporter().import_(payload)
    assert parsed["key"] == "root"
    assert [node.key for node in PreOrderIter(restored)] == ["root", "child"]
    assert restored.children[0].count == 2


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_children_assignment_reorders_and_detaches_old_children")
def test_dict_importer_builds_custom_node_class_and_parent_links():
    from anytree import Node, PreOrderIter
    from anytree.importer import DictImporter

    data = {"name": "root", "children": [{"name": "a"}, {"name": "b", "children": [{"name": "c"}]}]}
    root = DictImporter(nodecls=Node).import_(data)
    assert isinstance(root, Node)
    assert names(PreOrderIter(root)) == ["root", "a", "b", "c"]
    assert root.children[1].children[0].parent is root.children[1]


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_public_imports_expose_requested_surface")
def test_json_file_like_write_and_read_preserve_tree_values():
    from anytree import AnyNode, PreOrderIter
    from anytree.exporter import JsonExporter
    from anytree.importer import JsonImporter

    root = AnyNode(key="root")
    AnyNode(key="child", parent=root)
    buffer = io.StringIO()
    assert JsonExporter().write(root, buffer) is None
    buffer.seek(0)
    restored = JsonImporter().read(buffer)
    assert [node.key for node in PreOrderIter(restored)] == ["root", "child"]


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes")
def test_dict_exporter_can_filter_attributes_and_children():
    from anytree import AnyNode
    from anytree.exporter import DictExporter

    root = AnyNode(key="root", private="drop")
    AnyNode(key="keep", include=True, parent=root)
    AnyNode(key="drop", include=False, parent=root)
    exporter = DictExporter(
        attriter=lambda attrs: [(key, value) for key, value in attrs if key != "private"],
        childiter=lambda children: [child for child in children if child.include],
    )
    assert exporter.export(root) == {
        "key": "root",
        "children": [{"key": "keep", "include": True}],
    }


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes")
def test_exporter_maxlevel_limits_nested_children():
    from anytree.exporter import DictExporter, JsonExporter
    from anytree import AnyNode

    root = AnyNode(key="root")
    branch = AnyNode(key="branch", parent=root)
    AnyNode(key="leaf", parent=branch)
    assert DictExporter(maxlevel=2).export(root) == {
        "key": "root",
        "children": [{"key": "branch"}],
    }
    assert json.loads(JsonExporter(maxlevel=2).export(root))["children"][0] == {"key": "branch"}


@pytest.mark.depends_on("test_resolver_get_handles_relative_and_absolute_paths", "test_node_stores_name_and_extra_attributes")
def test_resolver_custom_path_attribute_survives_tree_navigation():
    from anytree import AnyNode, Resolver

    root = AnyNode(code="R")
    branch = AnyNode(code="B", parent=root)
    leaf = AnyNode(code="L", parent=branch)
    resolver = Resolver(pathattr="code")
    assert resolver.get(root, "B/L") is leaf
    assert resolver.get(leaf, "/R/B") is branch


@pytest.mark.depends_on("test_resolver_get_handles_relative_and_absolute_paths")
def test_resolver_ignorecase_and_relax_change_lookup_policy():
    from anytree import Node, Resolver

    root = Node("Root")
    Node("Child", parent=root)
    assert Resolver(ignorecase=True).get(root, "child").name == "Child"
    assert Resolver(relax=True).get(root, "missing") is None
    assert Resolver(relax=True).glob(root, "missing/*") == []


@pytest.mark.depends_on("test_resolver_glob_matches_single_level_wildcards")
def test_resolver_recursive_glob_finds_nested_matches_once():
    from anytree import Resolver

    root = named_tree()
    matches = Resolver().glob(root, "**/right_b_1")
    assert [node.name for node in matches] == ["right_b_1"]


@pytest.mark.depends_on("test_render_tree_rows_expose_prefix_fill_and_nodes", "test_render_by_attr_uses_semantic_node_values")
def test_render_child_order_can_be_reversed_without_mutating_tree():
    from anytree import RenderTree

    root = named_tree()
    rows = list(RenderTree(root, childiter=reversed))
    assert [row.node.name for row in rows] == [
        "root",
        "right",
        "right_b",
        "right_b_1",
        "right_a",
        "left",
        "left_b",
        "left_a",
    ]
    assert names(root.children) == ["left", "right"]


@pytest.mark.depends_on("test_render_tree_rows_expose_prefix_fill_and_nodes")
def test_render_multiline_attribute_uses_fill_for_continuation_lines():
    from anytree import Node, RenderTree

    root = Node("root", lines=["r1", "r2"])
    Node("child", lines=["c1", "c2"], parent=root)
    rendered = RenderTree(root).by_attr("lines").splitlines()
    assert rendered[:2] == ["r1", "r2"]
    assert rendered[2].endswith("c1")
    assert rendered[3].endswith("c2")


@pytest.mark.depends_on("test_render_tree_rows_expose_prefix_fill_and_nodes")
def test_render_maxlevel_keeps_requested_depth_only():
    from anytree import RenderTree

    root = named_tree()
    assert names(row.node for row in RenderTree(root, maxlevel=2)) == ["root", "left", "right"]


@pytest.mark.depends_on("test_nodemixin_adds_tree_behavior_to_user_class", "test_parent_none_detaches_node")
def test_node_mixin_hooks_observe_attach_and_detach_workflow():
    from anytree import NodeMixin

    class HookNode(NodeMixin):
        def __init__(self, label, parent=None):
            self.label = label
            self.events = []
            self.parent = parent

        def _pre_attach(self, parent):
            self.events.append(("pre_attach", parent.label))

        def _post_attach(self, parent):
            self.events.append(("post_attach", parent.label))

        def _pre_detach(self, parent):
            self.events.append(("pre_detach", parent.label))

        def _post_detach(self, parent):
            self.events.append(("post_detach", parent.label))

    root = HookNode("root")
    child = HookNode("child", parent=root)
    child.parent = None
    assert child.events == [
        ("pre_attach", "root"),
        ("post_attach", "root"),
        ("pre_detach", "root"),
        ("post_detach", "root"),
    ]


@pytest.mark.depends_on("test_lightnodemixin_supports_slots_and_tree_behavior", "test_anynode_stores_arbitrary_attributes")
def test_light_node_mixin_tree_can_be_exported_with_public_attributes():
    from anytree import LightNodeMixin, PreOrderIter

    class SlotNode(LightNodeMixin):
        __slots__ = ("name",)

        def __init__(self, name, parent=None):
            self.name = name
            self.parent = parent

    root = SlotNode("root")
    SlotNode("child", parent=root)
    assert names(PreOrderIter(root)) == ["root", "child"]


@pytest.mark.depends_on("test_parent_assignment_reattaches_and_preserves_identity", "test_resolver_get_handles_relative_and_absolute_paths")
def test_search_and_resolver_follow_a_reparented_subtree():
    from anytree import Node, Resolver, find_by_attr

    root = Node("root")
    left = Node("left", parent=root)
    right = Node("right", parent=root)
    leaf = Node("leaf", parent=left)
    leaf.parent = right
    assert find_by_attr(root, "leaf") is leaf
    assert Resolver().get(root, "right/leaf") is leaf


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_parent_none_detaches_node")
def test_detach_mutate_reattach_and_export_is_consistent():
    from anytree import AnyNode
    from anytree.exporter import DictExporter

    root = AnyNode(key="root")
    branch = AnyNode(key="branch", parent=root)
    leaf = AnyNode(key="leaf", parent=branch)
    branch.parent = None
    leaf.key = "renamed"
    branch.parent = root
    assert DictExporter().export(root) == {
        "key": "root",
        "children": [{"key": "branch", "children": [{"key": "renamed"}]}],
    }


@pytest.mark.depends_on("test_children_assignment_reorders_and_detaches_old_children", "test_path_and_reverse_path_have_opposite_order")
def test_children_reordering_updates_paths_without_recreating_nodes():
    from anytree import Node

    root = Node("root")
    first = Node("first", parent=root)
    second = Node("second", parent=root)
    first_leaf = Node("first_leaf", parent=first)
    root.children = [second, first]
    assert root.children == (second, first)
    assert first_leaf.path == (root, first, first_leaf)
    assert first_leaf.parent is first


@pytest.mark.depends_on("test_nodemixin_adds_tree_behavior_to_user_class", "test_anynode_stores_arbitrary_attributes")
def test_custom_mixin_nodes_and_anynodes_can_share_one_tree():
    from anytree import AnyNode, NodeMixin, PreOrderIter

    class Item(NodeMixin):
        def __init__(self, label, parent=None):
            self.label = label
            self.parent = parent

    root = Item("root")
    AnyNode(key="child", parent=root)
    Item("other", parent=root)
    assert identifiers(PreOrderIter(root)) == ["root", "child", "other"]


@pytest.mark.depends_on("test_iterator_filter_stop_and_maxlevel_are_composable", "test_anynode_stores_arbitrary_attributes")
def test_filtered_iteration_and_filtered_export_agree_on_selected_children():
    from anytree import AnyNode, PreOrderIter
    from anytree.exporter import DictExporter

    root = AnyNode(key="root")
    AnyNode(key="keep", enabled=True, parent=root)
    AnyNode(key="drop", enabled=False, parent=root)
    selected = identifiers(PreOrderIter(root, filter_=lambda node: getattr(node, "enabled", True)))
    data = DictExporter(childiter=lambda children: [child for child in children if child.enabled]).export(root)
    assert selected == ["root", "keep"]
    assert [child["key"] for child in data["children"]] == ["keep"]


@pytest.mark.depends_on("test_render_tree_rows_expose_prefix_fill_and_nodes", "test_levelorder_iterator_is_breadth_first")
def test_sorted_child_workflow_has_matching_render_and_breadth_order():
    from anytree import LevelOrderIter, RenderTree

    root = named_tree()
    sorted_names = names(LevelOrderIter(root, filter_=lambda node: True))
    rendered_names = names(row.node for row in RenderTree(root, childiter=lambda children: sorted(children, key=lambda n: n.name)))
    assert sorted_names == ["root", "left", "right", "left_a", "left_b", "right_a", "right_b", "right_b_1"]
    assert rendered_names == ["root", "left", "left_a", "left_b", "right", "right_a", "right_b", "right_b_1"]


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_public_imports_expose_requested_surface")
def test_json_sort_keys_is_a_serialization_option_not_a_tree_order_change():
    from anytree import AnyNode
    from anytree.exporter import JsonExporter

    root = AnyNode(z=1, a=2)
    child = AnyNode(z=3, a=4, parent=root)
    parsed = json.loads(JsonExporter(sort_keys=True).export(root))
    assert list(parsed) == ["a", "children", "z"]
    assert parsed["children"][0]["a"] == child.a
    assert root.children == (child,)


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes")
def test_custom_dict_class_receives_exported_attribute_pairs():
    from collections import OrderedDict

    from anytree import AnyNode
    from anytree.exporter import DictExporter

    root = AnyNode(first=1, second=2)
    result = DictExporter(dictcls=OrderedDict).export(root)
    assert isinstance(result, OrderedDict)
    assert list(result.items()) == [("first", 1), ("second", 2)]


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_children_deleter_detaches_all_children")
def test_imported_tree_can_be_mutated_then_reexported():
    from anytree.exporter import DictExporter
    from anytree.importer import DictImporter

    root = DictImporter().import_({"key": "root", "children": [{"key": "a"}, {"key": "b"}]})
    first, second = root.children
    first.parent = second
    second.key = "branch"
    assert DictExporter().export(root) == {
        "key": "root",
        "children": [{"key": "branch", "children": [{"key": "a"}]}],
    }


@pytest.mark.depends_on("test_resolver_glob_matches_single_level_wildcards", "test_children_assignment_reorders_and_detaches_old_children")
def test_resolver_glob_reflects_order_after_children_replacement():
    from anytree import Node, Resolver

    root = Node("root")
    one = Node("one", parent=root)
    two = Node("two", parent=root)
    root.children = [two, one]
    assert [node.name for node in Resolver().glob(root, "*")] == ["two", "one"]


@pytest.mark.depends_on("test_leaf_root_height_depth_and_size_properties", "test_postorder_iterator_visits_children_before_parent")
def test_leaf_properties_and_postorder_agree_after_growth():
    from anytree import Node, PostOrderIter

    root = Node("root")
    branch = Node("branch", parent=root)
    leaf = Node("leaf", parent=branch)
    assert names(root.leaves) == ["leaf"]
    Node("other", parent=branch)
    assert names(root.leaves) == ["leaf", "other"]
    assert names(PostOrderIter(branch))[-1] == "branch"
    assert root.height == 2 and root.size == 4


@pytest.mark.depends_on("test_levelorder_group_iterator_groups_by_depth", "test_zigzag_group_iterator_reverses_alternating_levels")
def test_grouped_iterator_views_share_the_same_level_membership():
    root = named_tree()
    from anytree import LevelOrderGroupIter, ZigZagGroupIter

    levels = [set(names(group)) for group in LevelOrderGroupIter(root)]
    zigzag_levels = [set(names(group)) for group in ZigZagGroupIter(root)]
    assert levels == zigzag_levels
    assert levels[0] == {"root"}
    assert levels[-1] == {"right_b_1"}


@pytest.mark.depends_on("test_resolver_get_handles_relative_and_absolute_paths", "test_anynode_stores_arbitrary_attributes")
def test_custom_attribute_tree_roundtrips_through_json_and_resolver():
    from anytree import AnyNode, Resolver
    from anytree.exporter import JsonExporter
    from anytree.importer import JsonImporter

    root = AnyNode(code="R")
    AnyNode(code="B", parent=root)
    restored = JsonImporter().import_(JsonExporter().export(root))
    assert Resolver(pathattr="code").get(restored, "B").code == "B"
    assert restored.children[0].parent is restored


@pytest.mark.depends_on("test_render_tree_rows_expose_prefix_fill_and_nodes", "test_render_by_attr_uses_semantic_node_values")
def test_render_workflow_keeps_row_nodes_and_attribute_projection_aligned():
    from anytree import Node, RenderTree

    root = Node("root", label="R")
    child = Node("child", label="C", parent=root)
    leaf = Node("leaf", label="L", parent=child)
    rows = list(RenderTree(root, maxlevel=2))
    projection = RenderTree(root, maxlevel=2).by_attr("label").splitlines()
    assert [row.node for row in rows] == [root, child]
    assert projection[-1] == "└── C"
    assert leaf not in [row.node for row in rows]


@pytest.mark.depends_on("test_nodemixin_adds_tree_behavior_to_user_class", "test_parent_assignment_reattaches_and_preserves_identity")
def test_custom_mixin_workflow_reparents_and_searches_by_domain_field():
    from anytree import NodeMixin, findall_by_attr

    class Entry(NodeMixin):
        def __init__(self, key, parent=None):
            self.key = key
            self.parent = parent

    root = Entry("root")
    first = Entry("first", parent=root)
    second = Entry("second", parent=root)
    leaf = Entry("leaf", parent=first)
    leaf.parent = second
    assert findall_by_attr(root, "leaf", name="key") == (leaf,)
    assert leaf.path == (root, second, leaf)


@pytest.mark.depends_on("test_search_count_constraints_raise_count_error", "test_anynode_stores_arbitrary_attributes")
def test_search_cardinality_and_export_state_remain_consistent_after_mutation():
    from anytree import findall
    from anytree.exporter import DictExporter
    from anytree.importer import DictImporter

    root = DictImporter().import_({"key": "root", "children": [{"key": "a"}, {"key": "b"}]})
    root.children = (root.children[1],)
    leaves = findall(root, filter_=lambda node: node.is_leaf)
    assert len(leaves) == 1
    assert DictExporter().export(root) == {"key": "root", "children": [{"key": "b"}]}


@pytest.mark.depends_on("test_anynode_stores_arbitrary_attributes", "test_resolver_glob_matches_single_level_wildcards")
def test_full_public_workflow_mutates_exports_resolves_and_renders():
    from anytree import Node, Resolver, RenderTree, find_by_attr
    from anytree.exporter import JsonExporter
    from anytree.importer import JsonImporter

    root = Node("root", kind="container")
    branch = Node("branch", kind="folder", parent=root)
    leaf = Node("leaf", kind="file", parent=branch)
    branch.children = [leaf, Node("extra", kind="file")]
    payload = JsonExporter(sort_keys=True).export(root)
    restored = JsonImporter().import_(payload)
    assert find_by_attr(restored, "extra", name="name").name == "extra"
    assert Resolver().get(restored, "branch/leaf").kind == "file"
    assert names(row.node for row in RenderTree(restored)) == ["root", "branch", "leaf", "extra"]
