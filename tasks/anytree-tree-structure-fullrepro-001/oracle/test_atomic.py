from __future__ import annotations

import pytest

from conftest import named_tree


def test_public_imports_expose_requested_surface():
    import anytree
    from anytree import AnyNode, LightNodeMixin, Node, NodeMixin, Resolver, RenderTree
    from anytree.exporter import DictExporter, JsonExporter
    from anytree.importer import DictImporter, JsonImporter

    assert all(
        cls is not None
        for cls in (
            anytree.PreOrderIter,
            anytree.PostOrderIter,
            anytree.LevelOrderIter,
            anytree.ZigZagGroupIter,
            AnyNode,
            LightNodeMixin,
            Node,
            NodeMixin,
            Resolver,
            RenderTree,
            DictExporter,
            JsonExporter,
            DictImporter,
            JsonImporter,
        )
    )


def test_node_stores_name_and_extra_attributes():
    from anytree import Node

    node = Node("item", score=7, tags=["a"])
    assert node.name == "item"
    assert node.score == 7
    assert node.tags == ["a"]
    assert node.parent is None
    assert node.children == ()


def test_anynode_stores_arbitrary_attributes():
    from anytree import AnyNode

    node = AnyNode(identifier="item", score=7)
    assert node.identifier == "item"
    assert node.score == 7
    assert node.parent is None
    assert node.children == ()


def test_nodemixin_adds_tree_behavior_to_user_class():
    from anytree import NodeMixin

    class Record(NodeMixin):
        def __init__(self, label, parent=None):
            self.label = label
            self.parent = parent

    root = Record("root")
    child = Record("child", parent=root)
    assert child.parent is root
    assert root.children == (child,)
    assert child.path == (root, child)


def test_lightnodemixin_supports_slots_and_tree_behavior():
    from anytree import LightNodeMixin

    class SlotNode(LightNodeMixin):
        __slots__ = ("name",)

        def __init__(self, name, parent=None):
            self.name = name
            self.parent = parent

    root = SlotNode("root")
    child = SlotNode("child", parent=root)
    assert child.root is root
    assert root.children == (child,)
    assert child.depth == 1


def test_parent_assignment_reattaches_and_preserves_identity():
    from anytree import Node

    first = Node("first")
    second = Node("second")
    child = Node("child", parent=first)
    child.parent = second
    assert first.children == ()
    assert second.children == (child,)
    assert child.parent is second


def test_parent_none_detaches_node():
    from anytree import Node

    root = Node("root")
    child = Node("child", parent=root)
    child.parent = None
    assert root.children == ()
    assert child.is_root
    assert child.root is child


def test_children_assignment_reorders_and_detaches_old_children():
    from anytree import Node

    root = Node("root")
    first = Node("first", parent=root)
    second = Node("second", parent=root)
    third = Node("third")
    root.children = (second, third)
    assert root.children == (second, third)
    assert first.parent is None
    assert second.parent is root
    assert third.parent is root


def test_children_deleter_detaches_all_children():
    from anytree import Node

    root = Node("root", children=[Node("a"), Node("b")])
    children = root.children
    del root.children
    assert root.children == ()
    assert all(child.parent is None for child in children)


def test_path_and_reverse_path_have_opposite_order():
    from anytree import Node

    root = Node("root")
    middle = Node("middle", parent=root)
    leaf = Node("leaf", parent=middle)
    assert leaf.path == (root, middle, leaf)
    assert tuple(leaf.iter_path_reverse()) == (leaf, middle, root)


def test_relationship_properties_report_tree_membership():
    from anytree import Node

    root = Node("root")
    branch = Node("branch", parent=root)
    leaf = Node("leaf", parent=branch)
    sibling = Node("sibling", parent=branch)
    assert branch.ancestors == (root,)
    assert root.descendants == (branch, leaf, sibling)
    assert leaf.root is root
    assert leaf.siblings == (sibling,)


def test_leaf_root_height_depth_and_size_properties():
    from anytree import Node

    root = Node("root")
    branch = Node("branch", parent=root)
    leaf = Node("leaf", parent=branch)
    assert root.is_root and not root.is_leaf
    assert leaf.is_leaf and not leaf.is_root
    assert root.height == 2
    assert branch.depth == 1
    assert root.size == 3


def test_self_parent_is_rejected_with_loop_error():
    from anytree import LoopError, Node

    node = Node("node")
    with pytest.raises(LoopError):
        node.parent = node


def test_descendant_parent_is_rejected_with_loop_error():
    from anytree import LoopError, Node

    root = Node("root")
    child = Node("child", parent=root)
    with pytest.raises(LoopError):
        root.parent = child


def test_non_node_parent_is_rejected_with_tree_error():
    from anytree import Node, TreeError

    with pytest.raises(TreeError):
        Node("child", parent=object())


def test_duplicate_children_are_rejected_with_tree_error():
    from anytree import Node, TreeError

    root = Node("root")
    child = Node("child")
    with pytest.raises(TreeError):
        root.children = [child, child]
    assert root.children == ()
    assert child.parent is None


def test_children_assignment_rolls_back_after_attach_failure():
    from anytree import Node

    root = Node("root")
    original = Node("original", parent=root)
    foreign = Node("foreign")
    foreign_child = Node("foreign_child", parent=foreign)
    from anytree import LoopError

    with pytest.raises(LoopError):
        root.children = [foreign_child, root]
    assert root.children == (original,)
    assert foreign_child.parent is None
    assert foreign_child not in foreign.children


def test_preorder_iterator_is_depth_first():
    from anytree import PreOrderIter
    from conftest import names

    assert names(PreOrderIter(named_tree())) == [
        "root",
        "left",
        "left_a",
        "left_b",
        "right",
        "right_a",
        "right_b",
        "right_b_1",
    ]


def test_postorder_iterator_visits_children_before_parent():
    from anytree import PostOrderIter
    from conftest import names

    assert names(PostOrderIter(named_tree())) == [
        "left_a",
        "left_b",
        "left",
        "right_a",
        "right_b_1",
        "right_b",
        "right",
        "root",
    ]


def test_levelorder_iterator_is_breadth_first():
    from anytree import LevelOrderIter
    from conftest import names

    assert names(LevelOrderIter(named_tree())) == [
        "root",
        "left",
        "right",
        "left_a",
        "left_b",
        "right_a",
        "right_b",
        "right_b_1",
    ]


def test_levelorder_group_iterator_groups_by_depth():
    from anytree import LevelOrderGroupIter
    from conftest import names

    assert [names(group) for group in LevelOrderGroupIter(named_tree())] == [
        ["root"],
        ["left", "right"],
        ["left_a", "left_b", "right_a", "right_b"],
        ["right_b_1"],
    ]


def test_zigzag_group_iterator_reverses_alternating_levels():
    from anytree import ZigZagGroupIter
    from conftest import names

    assert [names(group) for group in ZigZagGroupIter(named_tree())] == [
        ["root"],
        ["right", "left"],
        ["left_a", "left_b", "right_a", "right_b"],
        ["right_b_1"],
    ]


def test_iterator_filter_stop_and_maxlevel_are_composable():
    from anytree import PreOrderIter
    from conftest import names

    root = named_tree()
    filtered = names(PreOrderIter(root, filter_=lambda node: node.name != "left_b"))
    stopped = names(PreOrderIter(root, stop=lambda node: node.name == "right"))
    shallow = names(PreOrderIter(root, maxlevel=2))
    assert filtered == ["root", "left", "left_a", "right", "right_a", "right_b", "right_b_1"]
    assert stopped == ["root", "left", "left_a", "left_b"]
    assert shallow == ["root", "left", "right"]


def test_findall_returns_matching_nodes_in_preorder():
    from anytree import findall
    from conftest import named_tree, names

    root = named_tree()
    assert names(findall(root, filter_=lambda node: node.name.endswith("a"))) == [
        "left_a",
        "right_a",
    ]


def test_find_by_attr_and_findall_by_attr_use_named_attributes():
    from anytree import AnyNode, find_by_attr, findall_by_attr

    root = AnyNode(key="root")
    first = AnyNode(key="first", parent=root)
    second = AnyNode(key="same", parent=root)
    assert find_by_attr(root, "same", name="key") is second
    assert findall_by_attr(root, "same", name="key") == (second,)


def test_search_count_constraints_raise_count_error():
    from anytree import CountError, findall

    from anytree import Node

    root = Node("root")
    Node("a", parent=root)
    Node("b", parent=root)
    with pytest.raises(CountError):
        findall(root, filter_=lambda node: node.is_leaf, mincount=3)


def test_resolver_get_handles_relative_and_absolute_paths():
    from anytree import Node, Resolver

    root = Node("root")
    branch = Node("branch", parent=root)
    leaf = Node("leaf", parent=branch)
    resolver = Resolver()
    assert resolver.get(root, "branch/leaf") is leaf
    assert resolver.get(leaf, "/root/branch") is branch
    assert resolver.get(leaf, "..") is branch


def test_resolver_glob_matches_single_level_wildcards():
    from anytree import Node, Resolver

    root = Node("root")
    branch = Node("branch", parent=root)
    Node("leaf_a", parent=branch)
    Node("leaf_b", parent=branch)
    assert [node.name for node in Resolver().glob(root, "branch/leaf_?")] == ["leaf_a", "leaf_b"]


def test_render_tree_rows_expose_prefix_fill_and_nodes():
    from anytree import RenderTree

    root = named_tree()
    rows = list(RenderTree(root))
    assert [row.node.name for row in rows] == [
        "root",
        "left",
        "left_a",
        "left_b",
        "right",
        "right_a",
        "right_b",
        "right_b_1",
    ]
    assert rows[0].pre == ""
    assert rows[1].pre
    assert rows[2].fill


def test_render_by_attr_uses_semantic_node_values():
    from anytree import Node, RenderTree

    root = Node("root", label="R")
    Node("child", label="C", parent=root)
    rendered = RenderTree(root).by_attr("label").splitlines()
    assert [line[-1] for line in rendered] == ["R", "C"]
