from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): integration tests depend on public atomic contracts",
    )


def rows_of(table):
    return [tuple(row) for row in table.rows]


def type_names(table):
    return tuple(type(data_type).__name__ for data_type in table.column_types)


def make_sales_table():
    from agate import Boolean, Number, Table, Text

    rows = [
        ("east", "alpha", "Ada", "2", "10.50", "yes"),
        ("east", "beta", "Ben", "3", "20.00", "no"),
        ("east", "alpha", "Cy", "1", "5.50", "yes"),
        ("west", "alpha", "Ada", "4", "30.00", "yes"),
        ("west", "beta", "Ben", "2", "15.00", "no"),
        ("west", "gamma", "Cy", "5", "25.00", "yes"),
    ]
    return Table(
        rows,
        ["region", "product", "rep", "units", "revenue", "active"],
        [
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
        ],
        row_names=["ea1", "eb1", "ea2", "wa1", "wb1", "wg1"],
    )


def make_regions_table():
    from agate import Number, Table, Text

    return Table(
        [
            ("east", "Ellen", "0.10"),
            ("west", "Wes", "0.15"),
            ("central", "Cara", "0.05"),
        ],
        ["region", "manager", "tax_rate"],
        [Text(), Text(), Number(locale="en_US")],
    )


def make_products_table():
    from agate import Table, Text

    return Table(
        [
            ("alpha", "hardware"),
            ("beta", "software"),
            ("gamma", "service"),
        ],
        ["sku", "category"],
        [Text(), Text()],
    )


def make_profiles_table():
    from agate import Table, Text

    return Table(
        [
            ("p1", "Ada", "NY", "gold"),
            ("p2", "Ben", "SF", "silver"),
        ],
        ["id", "name", "city", "tier"],
        [Text(), Text(), Text(), Text()],
        row_names="id",
    )


def make_temporal_table():
    from agate import Date, DateTime, Number, Table, Text, TimeDelta

    return Table(
        [
            (
                "morning",
                "2024-01-02",
                "2024-01-02T03:04:05",
                "1h 30m",
                "10.5",
            ),
            (
                "evening",
                "2024-01-03",
                "2024-01-03T18:20:00",
                "2h 15m",
                "20.0",
            ),
        ],
        ["label", "day", "created", "elapsed", "amount"],
        [
            Text(),
            Date(date_format="%Y-%m-%d"),
            DateTime(datetime_format="%Y-%m-%dT%H:%M:%S"),
            TimeDelta(),
            Number(locale="en_US"),
        ],
    )


def make_sparse_table():
    from agate import Number, Table, Text

    return Table(
        [("r1", "3"), ("r2", None), ("r3", "1"), ("r4", "2")],
        ["label", "value"],
        [Text(), Number(locale="en_US")],
        row_names="label",
    )


def make_small_join_tables():
    from agate import Number, Table, Text

    left = Table(
        [("A", "1"), ("B", "2")],
        ["key", "left_value"],
        [Text(), Number(locale="en_US")],
    )
    right = Table(
        [("A", "ready"), ("C", "new")],
        ["key", "right_value"],
        [Text(), Text()],
    )
    return left, right


def make_normalized_profiles():
    from agate import Table, Text

    return Table(
        [
            ("p1", "city", "NY"),
            ("p1", "tier", "gold"),
            ("p2", "city", "SF"),
        ],
        ["id", "property", "value"],
        [Text(), Text(), Text()],
    )


@pytest.fixture
def sales_table():
    return make_sales_table()


@pytest.fixture
def regions_table():
    return make_regions_table()


@pytest.fixture
def products_table():
    return make_products_table()


@pytest.fixture
def profiles_table():
    return make_profiles_table()


@pytest.fixture
def temporal_table():
    return make_temporal_table()


@pytest.fixture
def sparse_table():
    return make_sparse_table()


@pytest.fixture
def normalized_profiles():
    return make_normalized_profiles()


__all__ = [
    "Decimal",
    "date",
    "datetime",
    "timedelta",
    "make_normalized_profiles",
    "make_products_table",
    "make_regions_table",
    "make_sales_table",
    "make_small_join_tables",
    "make_temporal_table",
    "rows_of",
    "type_names",
]
