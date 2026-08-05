"""Shared deterministic fixtures for public anytree behavior tests."""
from __future__ import annotations

import pytest


def named_tree():
    from anytree import Node

    root = Node("root")
    left = Node("left", parent=root)
    right = Node("right", parent=root)
    Node("left_a", parent=left)
    Node("left_b", parent=left)
    Node("right_a", parent=right)
    Node("right_b", parent=right)
    Node("right_b_1", parent=right.children[1])
    return root


def names(nodes):
    return [node.name for node in nodes]


def identifiers(nodes):
    return [
        getattr(node, "name", getattr(node, "key", getattr(node, "label", None)))
        for node in nodes
    ]


@pytest.fixture
def tree():
    return named_tree()


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*tests): document atomic behavior dependencies")
