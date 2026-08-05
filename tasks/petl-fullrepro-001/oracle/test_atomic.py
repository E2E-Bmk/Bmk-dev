from __future__ import annotations

from collections import OrderedDict
import csv

import pytest


def test_public_import_exposes_documented_table_entry_points():
    import petl as etl

    assert isinstance(etl.__version__, str)
    assert callable(etl.wrap)
    assert callable(etl.fromcsv)
    assert callable(etl.tocsv)
    assert callable(etl.cut)
    assert callable(etl.convert)
    assert callable(etl.select)
    assert callable(etl.cat)
    assert callable(etl.join)
    assert callable(etl.aggregate)
    assert callable(etl.pivot)
    assert callable(etl.lookup)


def test_wrap_preserves_table_rows(sales_table):
    import petl as etl

    assert list(etl.wrap(sales_table)) == sales_table


def test_table_iterators_are_independent(sales_table):
    import petl as etl

    table = etl.wrap(sales_table)
    first = iter(table)
    second = iter(table)
    assert next(first) == next(second) == sales_table[0]
    assert next(first) == next(second) == sales_table[1]


def test_header_returns_tuple(sales_table):
    import petl as etl

    assert etl.header(sales_table) == (
        "id",
        "customer",
        "region",
        "amount",
        "category",
        "active",
    )


def test_fieldnames_stringifies_headers(sales_table):
    import petl as etl

    assert etl.fieldnames(sales_table) == (
        "id",
        "customer",
        "region",
        "amount",
        "category",
        "active",
    )


def test_data_excludes_header(sales_table):
    import petl as etl

    assert list(etl.data(sales_table)) == sales_table[1:]


def test_values_projects_one_field(sales_table):
    import petl as etl

    assert list(etl.values(sales_table, "customer")) == ["Ada", "Lin", "Noa", "Mia"]


def test_fromdicts_respects_explicit_header():
    import petl as etl

    records = [
        {"customer": "Ada", "id": 1, "region": "east"},
        {"region": "west", "customer": "Lin", "id": 2},
    ]
    table = etl.fromdicts(records, header=["id", "customer", "region"])
    assert list(table) == [
        ("id", "customer", "region"),
        (1, "Ada", "east"),
        (2, "Lin", "west"),
    ]


def test_cut_selects_and_reorders_fields(sales_table):
    import petl as etl

    result = etl.cut(sales_table, "customer", "amount", "id")
    assert list(result) == [
        ("customer", "amount", "id"),
        ("Ada", 10, 1),
        ("Lin", 20, 2),
        ("Noa", 15, 3),
        ("Mia", 5, 4),
    ]


def test_cut_pads_short_rows_with_missing():
    import petl as etl

    table = [["id", "customer", "amount"], [1, "Ada"], [2, "Lin", 8]]
    result = etl.cut(table, "customer", "amount", missing="NA")
    assert list(result) == [
        ("customer", "amount"),
        ("Ada", "NA"),
        ("Lin", 8),
    ]


def test_convert_applies_callable_to_field(sales_table):
    import petl as etl

    result = etl.convert(sales_table, "amount", lambda value: value * 2)
    assert list(result) == [
        ("id", "customer", "region", "amount", "category", "active"),
        (1, "Ada", "east", 20, "A", True),
        (2, "Lin", "west", 40, "B", False),
        (3, "Noa", "east", 30, "A", True),
        (4, "Mia", "west", 10, "B", True),
    ]


def test_convertall_applies_callable_to_each_data_field(text_table):
    import petl as etl

    result = etl.convertall(text_table, str.upper)
    assert list(result) == [
        ("first", "second"),
        ("ADA", "EAST"),
        ("LIN", "WEST"),
    ]


def test_select_field_predicate_keeps_matching_rows(sales_table):
    import petl as etl

    result = etl.select(sales_table, "region", lambda value: value == "east")
    assert list(result) == [
        ("id", "customer", "region", "amount", "category", "active"),
        (1, "Ada", "east", 10, "A", True),
        (3, "Noa", "east", 15, "A", True),
    ]


def test_select_row_expression_uses_named_fields(sales_table):
    import petl as etl

    result = etl.select(sales_table, "{amount} >= 15 and {active}")
    assert list(result) == [
        ("id", "customer", "region", "amount", "category", "active"),
        (3, "Noa", "east", 15, "A", True),
    ]


def test_select_complement_inverts_predicate(sales_table):
    import petl as etl

    result = etl.selectgt(sales_table, "amount", 10, complement=True)
    assert list(result) == [
        ("id", "customer", "region", "amount", "category", "active"),
        (1, "Ada", "east", 10, "A", True),
        (4, "Mia", "west", 5, "B", True),
    ]


def test_cat_appends_compatible_tables(sales_table):
    import petl as etl

    extra = [["id", "customer", "region", "amount", "category", "active"], [5, "Oli", "east", 8, "A", False]]
    assert list(etl.cat(sales_table, extra)) == [
        ("id", "customer", "region", "amount", "category", "active"),
        (1, "Ada", "east", 10, "A", True),
        (2, "Lin", "west", 20, "B", False),
        (3, "Noa", "east", 15, "A", True),
        (4, "Mia", "west", 5, "B", True),
        (5, "Oli", "east", 8, "A", False),
    ]


def test_join_matches_rows_on_common_key(sales_table, manager_table):
    import petl as etl

    result = etl.join(sales_table, manager_table, key="region")
    assert list(result) == [
        ("id", "customer", "region", "amount", "category", "active", "manager"),
        (1, "Ada", "east", 10, "A", True, "Rae"),
        (3, "Noa", "east", 15, "A", True, "Rae"),
        (2, "Lin", "west", 20, "B", False, "Kai"),
        (4, "Mia", "west", 5, "B", True, "Kai"),
    ]


def test_leftjoin_fills_missing_right_values(sales_table, id_label_table):
    import petl as etl

    result = etl.leftjoin(sales_table, id_label_table, key="id")
    assert list(result) == [
        ("id", "customer", "region", "amount", "category", "active", "label"),
        (1, "Ada", "east", 10, "A", True, "one"),
        (2, "Lin", "west", 20, "B", False, None),
        (3, "Noa", "east", 15, "A", True, "three"),
        (4, "Mia", "west", 5, "B", True, None),
    ]


def test_aggregate_sums_field_per_key(sales_table):
    import petl as etl

    result = etl.aggregate(sales_table, "region", sum, "amount")
    assert list(result) == [
        ("region", "value"),
        ("east", 25),
        ("west", 25),
    ]


def test_aggregate_supports_multiple_named_reductions(sales_table):
    import petl as etl

    aggregations = OrderedDict(
        [
            ("count", len),
            ("total", ("amount", sum)),
            ("customers", ("customer", list)),
        ]
    )
    result = etl.aggregate(sales_table, "region", aggregations)
    assert list(result) == [
        ("region", "count", "total", "customers"),
        ("east", 2, 25, ["Ada", "Noa"]),
        ("west", 2, 25, ["Lin", "Mia"]),
    ]


def test_pivot_builds_columns_from_second_field(sales_table):
    import petl as etl

    result = etl.pivot(sales_table, "region", "customer", "amount", sum, missing=0)
    assert list(result) == [
        ("region", "Ada", "Lin", "Mia", "Noa"),
        ("east", 10, 0, 0, 15),
        ("west", 0, 20, 5, 0),
    ]


def test_lookup_collects_duplicate_values(sales_table):
    import petl as etl

    assert etl.lookup(sales_table, "region", "customer") == {
        "east": ["Ada", "Noa"],
        "west": ["Lin", "Mia"],
    }


def test_lookupone_returns_scalar_values(id_label_table):
    import petl as etl

    assert etl.lookupone(id_label_table, "id", "label") == {
        1: "one",
        3: "three",
        5: "five",
    }


def test_lookupone_strict_rejects_duplicate_key():
    import petl as etl

    duplicate_keys = [["id", "label"], [1, "one"], [1, "uno"]]
    with pytest.raises(etl.DuplicateKeyError):
        etl.lookupone(duplicate_keys, "id", "label", strict=True)


def test_transform_view_is_lazy_until_iteration(counting_table):
    import petl as etl

    view = etl.convert(counting_table, "amount", lambda value: value + 1)
    assert counting_table.iterations == 0
    assert next(iter(view)) == (
        "id",
        "customer",
        "region",
        "amount",
        "category",
        "active",
    )
    assert counting_table.iterations == 1


def test_transform_view_supports_repeated_iteration(counting_table):
    import petl as etl

    view = etl.cut(counting_table, "id", "customer")
    expected = [
        ("id", "customer"),
        (1, "Ada"),
        (2, "Lin"),
        (3, "Noa"),
        (4, "Mia"),
    ]
    assert list(view) == expected
    assert list(view) == expected
    assert counting_table.iterations >= 2


def test_csv_path_round_trip_preserves_delimited_values(sales_table, tmp_path):
    import petl as etl

    path = tmp_path / "sales.csv"
    etl.tocsv(sales_table, str(path))
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == sales_table[0]
    assert rows[1] == ["1", "Ada", "east", "10", "A", "True"]
    assert list(etl.fromcsv(str(path))) == [
        ("id", "customer", "region", "amount", "category", "active"),
        ("1", "Ada", "east", "10", "A", "True"),
        ("2", "Lin", "west", "20", "B", "False"),
        ("3", "Noa", "east", "15", "A", "True"),
        ("4", "Mia", "west", "5", "B", "True"),
    ]


def test_csv_custom_delimiter_round_trip(text_table, tmp_path):
    import petl as etl

    path = tmp_path / "names.psv"
    etl.tocsv(text_table, str(path), delimiter=";")
    assert list(etl.fromcsv(str(path), delimiter=";")) == [
        ("first", "second"),
        ("Ada", "east"),
        ("Lin", "west"),
    ]


def test_look_contains_header_and_values(sales_table):
    import petl as etl

    output = str(etl.look(sales_table))
    assert "customer" in output
    assert "Ada" in output
    assert "20" in output


def test_lookstr_uses_string_value_projection(sales_table):
    import petl as etl

    output = str(etl.lookstr(sales_table))
    assert "customer" in output
    assert "Ada" in output
    assert "'Ada'" not in output


def test_html_display_projection_contains_table_cells(sales_table):
    import petl as etl

    html = etl.wrap(sales_table)._repr_html_()
    assert "<table" in html
    assert "<th>customer</th>" in html
    assert ">Ada<" in html


def test_missing_field_raises_public_selection_error(sales_table):
    import petl as etl

    with pytest.raises(etl.FieldSelectionError):
        list(etl.cut(sales_table, "missing-field"))
