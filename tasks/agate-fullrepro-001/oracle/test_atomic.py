from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO
import json

import pytest

from conftest import rows_of, type_names


def test_table_constructor_casts_rows_and_types():
    from agate import Boolean, Number, Table, Text

    table = Table(
        [("001", "2.50", "yes")],
        ["id", "amount", "active"],
        [Text(), Number(locale="en_US"), Boolean()],
    )
    assert rows_of(table) == [("001", Decimal("2.50"), True)]
    assert type_names(table) == ("Text", "Number", "Boolean")


def test_table_short_row_is_padded_with_null():
    from agate import Number, Table, Text

    table = Table(
        [("first", "1"), ("second",)],
        ["label", "value"],
        [Text(), Number(locale="en_US")],
    )
    assert rows_of(table)[1] == ("second", None)


def test_table_row_names_can_come_from_column():
    from agate import Table, Text

    table = Table(
        [("a1", "Ada"), ("b2", "Ben")],
        ["code", "name"],
        [Text(), Text()],
        row_names="code",
    )
    assert table.row_names == ("a1", "b2")
    assert table.rows["b2"]["name"] == "Ben"


def test_table_row_names_can_come_from_function():
    from agate import Table, Text

    table = Table(
        [("east", "alpha"), ("west", "beta")],
        ["region", "product"],
        [Text(), Text()],
        row_names=lambda row: f"{row['region']}-{row['product']}",
    )
    assert table.row_names == ("east-alpha", "west-beta")
    assert table.columns["product"].keys() == table.row_names


def test_table_columns_expose_public_metadata(sales_table):
    from agate import Number, Text

    column = sales_table.columns["revenue"]
    assert column.index == 4
    assert column.name == "revenue"
    assert isinstance(column.data_type, Number)
    assert isinstance(sales_table.columns["region"].data_type, Text)
    assert sales_table.column_names == (
        "region",
        "product",
        "rep",
        "units",
        "revenue",
        "active",
    )


def test_rows_support_keyed_and_indexed_access(sales_table):
    row = sales_table.rows["ea1"]
    assert row[0] == "east"
    assert row["product"] == "alpha"
    assert row.keys() == sales_table.column_names
    assert row.dict()["rep"] == "Ada"
    assert row.items()[0] == ("region", "east")


def test_columns_expose_distinct_and_sorted_values(sparse_table):
    column = sparse_table.columns["value"]
    assert set(column.values_distinct()) == {None, Decimal("1"), Decimal("2"), Decimal("3")}
    assert column.values_without_nulls() == (Decimal("3"), Decimal("1"), Decimal("2"))
    assert column.values_sorted() == [Decimal("1"), Decimal("2"), Decimal("3"), None]
    assert column.values_without_nulls_sorted() == [Decimal("1"), Decimal("2"), Decimal("3")]


def test_mapped_sequences_are_immutable_and_named():
    from agate import MappedSequence

    sequence = MappedSequence(("Ada", "Ben"), ("first", "second"))
    assert sequence["first"] == "Ada"
    assert sequence.get("missing", "fallback") == "fallback"
    assert sequence.dict() == {"first": "Ada", "second": "Ben"}
    with pytest.raises(TypeError):
        sequence["first"] = "Changed"


def test_table_length_and_iteration_follow_rows(sales_table):
    assert len(sales_table) == 6
    assert [row["rep"] for row in sales_table] == ["Ada", "Ben", "Cy", "Ada", "Ben", "Cy"]
    assert sales_table[2]["product"] == "alpha"


def test_type_tester_infers_controlled_public_types():
    from agate import Boolean, Date, DateTime, Number, Text, TimeDelta, TypeTester

    tester = TypeTester(
        types=[
            Boolean(),
            Number(locale="en_US"),
            Date(date_format="%Y-%m-%d"),
            DateTime(datetime_format="%Y-%m-%dT%H:%M:%S"),
            TimeDelta(),
            Text(),
        ]
    )
    inferred = tester.run(
        [
            (
                "yes",
                "1,200.50",
                "2024-01-02",
                "2024-01-02T03:04:05",
                "1:30",
                "memo",
            )
        ],
        ["flag", "amount", "day", "created", "elapsed", "note"],
    )
    assert type_names(type("TypeHolder", (), {"column_types": inferred})()) == (
        "Boolean",
        "Number",
        "Date",
        "DateTime",
        "TimeDelta",
        "Text",
    )


def test_type_tester_force_overrides_inference():
    from agate import Number, Text, TypeTester

    tester = TypeTester(force={"value": Text()})
    inferred = tester.run([("12.5",)], ["value"])
    assert isinstance(inferred[0], Text)
    assert inferred[0].cast("12.5") == "12.5"
    assert not isinstance(inferred[0], Number)


def test_type_tester_limit_changes_inference_sample():
    from agate import Number, Text, TypeTester

    rows = [("12.5",), ("free form",)]
    assert isinstance(TypeTester(limit=1).run(rows, ["value"])[0], Number)
    assert isinstance(TypeTester(limit=2).run(rows, ["value"])[0], Text)


def test_type_tester_custom_types_and_null_values():
    from agate import Table, Text, TypeTester

    tester = TypeTester(types=[Text(null_values=("missing",))])
    table = Table([("missing",), ("kept",)], ["value"], tester)
    assert rows_of(table) == [(None,), ("kept",)]
    assert type_names(table) == ("Text",)


def test_text_cast_respects_null_policy():
    from agate import Text

    assert Text().cast("N/A") is None
    assert Text(cast_nulls=False).cast("N/A") == "N/A"
    assert Text(null_values=("blank",)).cast("blank") is None
    assert Text().cast(Decimal("2.5")) == "2.5"


def test_boolean_cast_respects_custom_literals():
    from agate import Boolean

    boolean = Boolean(
        true_values=("on",),
        false_values=("off",),
        null_values=("unknown",),
    )
    assert boolean.cast("on") is True
    assert boolean.cast("off") is False
    assert boolean.cast("unknown") is None


def test_number_cast_uses_explicit_locale():
    from agate import Number

    number = Number(locale="en_US")
    assert number.cast("$1,234.50") == Decimal("1234.50")
    assert number.cast("-$75") == Decimal("-75")


def test_date_cast_uses_explicit_format():
    from agate import Date

    date_type = Date(date_format="%Y-%m-%d")
    assert date_type.cast("2024-01-02") == date(2024, 1, 2)
    assert date_type.csvify(date(2024, 1, 2)) == "2024-01-02"


def test_datetime_cast_uses_explicit_format():
    from agate import DateTime

    datetime_type = DateTime(datetime_format="%Y-%m-%dT%H:%M:%S")
    value = datetime_type.cast("2024-01-02T03:04:05")
    assert value == datetime(2024, 1, 2, 3, 4, 5)
    assert datetime_type.jsonify(value) == "2024-01-02T03:04:05"


def test_timedelta_casts_duration_without_locale():
    from agate import TimeDelta

    value = TimeDelta().cast("1h 30m")
    assert value == timedelta(hours=1, minutes=30)


def test_select_preserves_requested_column_order(sales_table):
    selected = sales_table.select(["revenue", "region", "rep"])
    assert selected.column_names == ("revenue", "region", "rep")
    assert rows_of(selected)[0] == (Decimal("10.50"), "east", "Ada")


def test_exclude_removes_named_columns(sales_table):
    excluded = sales_table.exclude(["active", "rep"])
    assert excluded.column_names == ("region", "product", "units", "revenue")
    assert len(excluded.rows[0]) == 4


def test_where_preserves_matching_rows_and_metadata(sales_table):
    filtered = sales_table.where(lambda row: row["active"] and row["units"] >= 2)
    assert filtered.row_names == ("ea1", "wa1", "wg1")
    assert [row["region"] for row in filtered.rows] == ["east", "west", "west"]
    assert filtered.column_names == sales_table.column_names
    assert len(sales_table) == 6


def test_order_by_places_nulls_last(sparse_table):
    ordered = sparse_table.order_by("value")
    assert [row["label"] for row in ordered.rows] == ["r3", "r4", "r1", "r2"]
    reversed_order = sparse_table.order_by("value", reverse=True)
    assert [row["label"] for row in reversed_order.rows] == ["r2", "r1", "r4", "r3"]


def test_limit_accepts_start_stop_step(sales_table):
    window = sales_table.limit(1, 6, 2)
    assert [row["rep"] for row in window.rows] == ["Ben", "Ada", "Cy"]
    assert window.row_names == ("eb1", "wa1", "wg1")


def test_distinct_keeps_first_keyed_row(sales_table):
    distinct = sales_table.distinct("product")
    assert [row["product"] for row in distinct.rows] == ["alpha", "beta", "gamma"]
    assert distinct.row_names == ("ea1", "eb1", "wg1")


def test_find_returns_first_matching_row(sales_table):
    found = sales_table.find(lambda row: row["revenue"] > 20)
    assert found["rep"] == "Ada"
    assert found["revenue"] == Decimal("30.00")
    assert sales_table.find(lambda row: row["region"] == "missing") is None


def test_left_join_adds_right_projection(sales_table, regions_table):
    joined = sales_table.join(regions_table, "region")
    assert joined.column_names == (
        "region",
        "product",
        "rep",
        "units",
        "revenue",
        "active",
        "manager",
        "tax_rate",
    )
    assert joined.rows[0]["manager"] == "Ellen"
    assert joined.rows[-1]["tax_rate"] == Decimal("0.15")


def test_inner_join_drops_unmatched_rows():
    from conftest import make_small_join_tables

    left, right = make_small_join_tables()
    joined = left.join(right, "key", inner=True)
    assert rows_of(joined) == [("A", Decimal("1"), "ready")]


def test_full_outer_join_retains_dangling_rows():
    from conftest import make_small_join_tables

    left, right = make_small_join_tables()
    joined = left.join(right, "key", full_outer=True)
    assert joined.column_names == ("key", "left_value", "key2", "right_value")
    assert rows_of(joined) == [
        ("A", Decimal("1"), "A", "ready"),
        ("B", Decimal("2"), None, None),
        (None, None, "C", "new"),
    ]


def test_join_columns_limits_right_projection(sales_table, regions_table):
    joined = sales_table.join(regions_table, "region", columns=["manager"])
    assert joined.column_names[-1] == "manager"
    assert "tax_rate" not in joined.column_names
    assert [row["manager"] for row in joined.rows[:2]] == ["Ellen", "Ellen"]


def test_group_by_builds_public_tableset(sales_table):
    from agate import TableSet, Text

    groups = sales_table.group_by("region")
    assert isinstance(groups, TableSet)
    assert groups.keys() == ("east", "west")
    assert groups.key_name == "region"
    assert isinstance(groups.key_type, Text)
    assert len(groups["east"]) == 3


def test_tableset_proxy_select_preserves_group_keys(sales_table):
    groups = sales_table.group_by("region").select(["product", "revenue"])
    assert groups.keys() == ("east", "west")
    assert groups.column_names == ("product", "revenue")
    assert rows_of(groups["west"])[0] == ("alpha", Decimal("30.00"))


def test_table_aggregate_returns_named_values(sales_table):
    from agate import Count, Sum

    summary = sales_table.aggregate(
        [("rows", Count()), ("revenue", Sum("revenue"))]
    )
    assert summary == {"rows": 6, "revenue": Decimal("106.00")}


def test_numeric_aggregations_return_typed_values(sales_table):
    from agate import Count, Max, Mean, Min, Sum

    summary = sales_table.aggregate(
        [
            ("count", Count("active", True)),
            ("sum", Sum("units")),
            ("mean", Mean("revenue")),
            ("min", Min("revenue")),
            ("max", Max("revenue")),
        ]
    )
    assert summary["count"] == 4
    assert summary["sum"] == Decimal("17")
    assert summary["mean"] == Decimal("17.66666666666666666666666667")
    assert summary["min"] == Decimal("5.50")
    assert summary["max"] == Decimal("30.00")


def test_compute_formula_adds_typed_column(sales_table):
    from agate import Formula, Number

    computed = sales_table.compute(
        [("line_total", Formula(Number(locale="en_US"), lambda row: row["units"] * row["revenue"]))]
    )
    assert computed.column_names[-1] == "line_total"
    assert isinstance(computed.column_types[-1], Number)
    assert computed.rows[0]["line_total"] == Decimal("21.00")


def test_compute_replace_replaces_existing_column(sales_table):
    from agate import Formula, Number

    replaced = sales_table.compute(
        [("units", Formula(Number(locale="en_US"), lambda row: row["units"] + 1))],
        replace=True,
    )
    assert replaced.column_names == sales_table.column_names
    assert [row["units"] for row in replaced.rows[:2]] == [Decimal("3"), Decimal("4")]


def test_percent_and_percent_change_add_columns(sales_table):
    from agate import Percent, PercentChange

    computed = sales_table.compute(
        [
            ("share", Percent("revenue")),
            ("change", PercentChange("units", "revenue")),
        ]
    )
    share_total = sum(computed.columns["share"].values()).quantize(Decimal("0.01"))
    assert share_total == Decimal("100.00")
    assert computed.rows[0]["change"] == Decimal("425.0")


def test_rank_and_slug_add_stable_projections(sales_table):
    from agate import Rank, Slug

    computed = sales_table.compute(
        [("rank", Rank("revenue")), ("rep_slug", Slug("rep"))]
    )
    assert computed.columns["rank"].values() == (Decimal("2"), Decimal("4"), Decimal("1"), Decimal("6"), Decimal("3"), Decimal("5"))
    assert computed.columns["rep_slug"].values() == ("ada", "ben", "cy", "ada", "ben", "cy")


def test_pivot_count_uses_key_and_pivot_columns(sales_table):
    pivoted = sales_table.pivot("region", "product")
    assert pivoted.column_names == ("region", "alpha", "beta", "gamma")
    assert rows_of(pivoted) == [
        ("east", Decimal("2"), Decimal("1"), Decimal("0")),
        ("west", Decimal("1"), Decimal("1"), Decimal("1")),
    ]
    assert pivoted.row_names == ("east", "west")


def test_pivot_sum_uses_numeric_aggregation(sales_table):
    from agate import Sum

    pivoted = sales_table.pivot("region", "product", Sum("revenue"))
    assert rows_of(pivoted) == [
        ("east", Decimal("16.00"), Decimal("20.00"), Decimal("0")),
        ("west", Decimal("30.00"), Decimal("15.00"), Decimal("25.00")),
    ]


def test_normalize_emits_key_property_value_rows(profiles_table):
    normalized = profiles_table.normalize("id", ["city", "tier"])
    assert normalized.column_names == ("id", "property", "value")
    assert rows_of(normalized) == [
        ("p1", "city", "NY"),
        ("p1", "tier", "gold"),
        ("p2", "city", "SF"),
        ("p2", "tier", "silver"),
    ]


def test_denormalize_restores_sparse_properties(normalized_profiles):
    denormalized = normalized_profiles.denormalize("id", default_value="unknown")
    assert denormalized.column_names == ("id", "city", "tier")
    assert rows_of(denormalized) == [
        ("p1", "NY", "gold"),
        ("p2", "SF", "unknown"),
    ]
    assert denormalized.row_names == ("p1", "p2")


def test_table_from_object_flattens_public_rows():
    from agate import Table

    table = Table.from_object(
        [
            {"person": {"name": "Ada"}, "scores": [1, 2]},
            {"person": {"name": "Ben"}},
        ]
    )
    assert table.column_names == ("person/name", "scores/0", "scores/1")
    assert rows_of(table)[0][0] == "Ada"
    assert rows_of(table)[1][1:] == (None, None)


def test_table_csv_round_trip_reads_local_file(tmp_path, sales_table):
    from agate import Boolean, Number, Table, Text

    path = tmp_path / "sales.csv"
    sales_table.to_csv(str(path))
    restored = Table.from_csv(
        str(path),
        column_types=[
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
        ],
        row_names="rep",
    )
    assert restored.column_names == sales_table.column_names
    assert rows_of(restored) == rows_of(sales_table)
    assert restored.row_names == ("Ada", "Ben", "Cy", "Ada", "Ben", "Cy")


def test_table_json_round_trip_reads_local_file(tmp_path, sales_table):
    from agate import Boolean, Number, Table, Text

    path = tmp_path / "sales.json"
    sales_table.to_json(str(path))
    restored = Table.from_json(
        str(path),
        column_types=[
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
        ],
    )
    assert rows_of(restored) == rows_of(sales_table)
    payload = json.loads(path.read_text())
    assert isinstance(payload, list)
    assert payload[0]["region"] == "east"


def test_table_newline_json_round_trip_reads_local_file(tmp_path, sales_table):
    from agate import Boolean, Number, Table, Text

    path = tmp_path / "sales.ndjson"
    sales_table.to_json(str(path), newline=True)
    restored = Table.from_json(
        str(path),
        newline=True,
        column_types=[
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
        ],
    )
    assert rows_of(restored) == rows_of(sales_table)
    assert len(path.read_text().splitlines()) == len(sales_table)


def test_tableset_csv_round_trip_reads_local_directory(tmp_path, sales_table):
    from agate import Boolean, Number, TableSet, Text

    source = sales_table.group_by("region")
    directory = tmp_path / "groups"
    source.to_csv(str(directory))
    restored = TableSet.from_csv(
        str(directory),
        column_types=[
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
        ],
    )
    assert set(restored.keys()) == {"east", "west"}
    assert rows_of(restored["east"]) == rows_of(source["east"])


def test_tableset_nested_json_round_trip_reads_local_file(tmp_path, sales_table):
    from agate import Boolean, Number, TableSet, Text

    source = sales_table.group_by("region")
    path = tmp_path / "groups.json"
    source.to_json(str(path), nested=True)
    restored = TableSet.from_json(
        str(path),
        column_types=[
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
        ],
    )
    assert restored.keys() == ("east", "west")
    assert rows_of(restored["west"]) == rows_of(source["west"])


def test_print_structure_reports_columns_and_types(sales_table):
    output = StringIO()
    sales_table.print_structure(output=output)
    text = output.getvalue()
    assert "| column  | data_type |" in text
    assert "| revenue | Number" in text
    assert "| active  | Boolean" in text


def test_print_table_reports_headers_and_values(sales_table):
    output = StringIO()
    sales_table.print_table(output=output, locale="en_US")
    text = output.getvalue()
    assert text.startswith("| region")
    assert "| product" in text
    assert "east" in text
    assert "10.5" in text


def test_print_bars_reports_labels_and_counts(sales_table):
    output = StringIO()
    counts = sales_table.pivot(lambda row: row["region"])
    counts.print_bars(output=output, width=40, printable=True)
    text = output.getvalue()
    assert text.startswith("group Count")
    assert "east" in text
    assert "west" in text
    assert "+" in text
