from __future__ import annotations

import pytest


class CountingTable:
    def __init__(self, rows):
        self.rows = rows
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        yield from self.rows


@pytest.fixture
def sales_table():
    return [
        ["id", "customer", "region", "amount", "category", "active"],
        [1, "Ada", "east", 10, "A", True],
        [2, "Lin", "west", 20, "B", False],
        [3, "Noa", "east", 15, "A", True],
        [4, "Mia", "west", 5, "B", True],
    ]


@pytest.fixture
def text_table():
    return [
        ["first", "second"],
        ["Ada", "east"],
        ["Lin", "west"],
    ]


@pytest.fixture
def manager_table():
    return [
        ["region", "manager"],
        ["east", "Rae"],
        ["west", "Kai"],
        ["north", "Tao"],
    ]


@pytest.fixture
def id_label_table():
    return [
        ["id", "label"],
        [1, "one"],
        [3, "three"],
        [5, "five"],
    ]


@pytest.fixture
def counting_table(sales_table):
    return CountingTable(sales_table)


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): atomic dependency metadata")
