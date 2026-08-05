from __future__ import annotations

from contextlib import redirect_stdout
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO
import json

import pytest

from conftest import make_small_join_tables, rows_of, type_names


@pytest.mark.depends_on(
    "test_select_preserves_requested_column_order",
    "test_where_preserves_matching_rows_and_metadata",
    "test_compute_formula_adds_typed_column",
    "test_order_by_places_nulls_last",
)
def test_select_where_compute_pipeline_preserves_fact_projection(sales_table):
    from agate import Formula, Number

    projected = (
        sales_table.where(lambda row: row["active"])
        .select(["region", "product", "units", "revenue"])
        .compute(
            [
                (
                    "line_total",
                    Formula(
                        Number(locale="en_US"),
                        lambda row: row["units"] * row["revenue"],
                    ),
                )
            ]
        )
        .order_by("line_total", reverse=True)
    )
    assert projected.column_names == (
        "region",
        "product",
        "units",
        "revenue",
        "line_total",
    )
    assert projected.rows[0]["line_total"] == Decimal("125.00")
    assert len(projected) == 4


@pytest.mark.depends_on(
    "test_order_by_places_nulls_last",
    "test_limit_accepts_start_stop_step",
    "test_distinct_keeps_first_keyed_row",
)
def test_order_limit_distinct_pipeline_reduces_rows_consistently(sales_table):
    reduced = sales_table.order_by("revenue", reverse=True).limit(3).distinct("rep")
    assert len(reduced) == 3
    assert [row["rep"] for row in reduced.rows] == ["Ada", "Cy", "Ben"]
    assert reduced.rows[0]["revenue"] == Decimal("30.00")


@pytest.mark.depends_on(
    "test_left_join_adds_right_projection",
    "test_group_by_builds_public_tableset",
    "test_numeric_aggregations_return_typed_values",
)
def test_join_group_aggregate_pipeline_matches_manual_totals(sales_table, regions_table):
    from agate import Sum

    summary = (
        sales_table.join(regions_table, "region")
        .group_by("manager")
        .aggregate([("revenue", Sum("revenue"))])
    )
    assert rows_of(summary) == [
        ("Ellen", Decimal("36.00")),
        ("Wes", Decimal("70.00")),
    ]
    assert summary.row_names == ("Ellen", "Wes")


@pytest.mark.depends_on(
    "test_group_by_builds_public_tableset",
    "test_table_aggregate_returns_named_values",
    "test_pivot_count_uses_key_and_pivot_columns",
)
def test_group_aggregate_and_pivot_agree_on_counts(sales_table):
    from agate import Count

    grouped = sales_table.group_by("region").aggregate([("rows", Count())])
    pivoted = sales_table.pivot("region", "product")
    pivot_counts = {
        row["region"]: sum(row[name] for name in ("alpha", "beta", "gamma"))
        for row in pivoted.rows
    }
    assert {row["region"]: row["rows"] for row in grouped.rows} == pivot_counts


@pytest.mark.depends_on(
    "test_tableset_proxy_select_preserves_group_keys",
    "test_group_by_builds_public_tableset",
)
def test_group_by_select_merge_round_trip_recreates_group_column(sales_table):
    grouped = sales_table.group_by("region").select(
        ["product", "rep", "units", "revenue", "active"]
    )
    merged = grouped.merge()
    assert merged.column_names == (
        "region",
        "product",
        "rep",
        "units",
        "revenue",
        "active",
    )
    assert len(merged) == len(sales_table)
    assert [row["region"] for row in merged.rows[:3]] == ["east", "east", "east"]


@pytest.mark.depends_on(
    "test_group_by_builds_public_tableset",
    "test_numeric_aggregations_return_typed_values",
)
def test_having_filters_aggregated_groups_before_merge(sales_table):
    from agate import Sum

    groups = sales_table.group_by("region")
    kept = groups.having(
        [("total", Sum("revenue"))],
        lambda values: values["total"] > Decimal("50"),
    )
    assert kept.keys() == ("west",)
    assert rows_of(kept["west"]) == rows_of(groups["west"])


@pytest.mark.depends_on("test_group_by_builds_public_tableset")
def test_nested_grouping_aggregate_preserves_two_keys(sales_table):
    from agate import Count

    summary = sales_table.group_by("region").group_by("product").aggregate(
        [("rows", Count())]
    )
    assert summary.column_names == ("region", "product", "rows")
    assert summary.row_names == (
        ("east", "alpha"),
        ("east", "beta"),
        ("west", "alpha"),
        ("west", "beta"),
        ("west", "gamma"),
    )
    assert sum(row["rows"] for row in summary.rows) == Decimal("6")


@pytest.mark.depends_on(
    "test_group_by_builds_public_tableset",
    "test_compute_formula_adds_typed_column",
)
def test_tableset_proxy_compute_then_aggregate_projects_new_column(sales_table):
    from agate import Formula, Number, Sum

    computed = sales_table.group_by("region").compute(
        [
            (
                "double_revenue",
                Formula(
                    Number(locale="en_US"),
                    lambda row: row["revenue"] * 2,
                ),
            )
        ]
    )
    summary = computed.aggregate([("total", Sum("double_revenue"))])
    assert rows_of(summary) == [
        ("east", Decimal("72.00")),
        ("west", Decimal("140.00")),
    ]


@pytest.mark.depends_on(
    "test_left_join_adds_right_projection",
    "test_compute_formula_adds_typed_column",
)
def test_join_then_compute_taxed_revenue(sales_table, regions_table):
    from agate import Formula, Number

    joined = sales_table.join(regions_table, "region")
    taxed = joined.compute(
        [
            (
                "with_tax",
                Formula(
                    Number(locale="en_US"),
                    lambda row: row["revenue"] * (1 + row["tax_rate"]),
                ),
            )
        ]
    )
    assert taxed.rows[0]["with_tax"] == Decimal("11.55")
    assert taxed.rows[3]["with_tax"] == Decimal("34.50")


@pytest.mark.depends_on(
    "test_inner_join_drops_unmatched_rows",
    "test_group_by_builds_public_tableset",
    "test_numeric_aggregations_return_typed_values",
)
def test_inner_join_then_group_by_category(sales_table, products_table):
    from agate import Sum

    summary = (
        sales_table.join(products_table, "product", "sku", inner=True)
        .group_by("category")
        .aggregate([("units", Sum("units"))])
    )
    assert rows_of(summary) == [
        ("hardware", Decimal("7")),
        ("software", Decimal("5")),
        ("service", Decimal("5")),
    ]


@pytest.mark.depends_on(
    "test_full_outer_join_retains_dangling_rows",
    "test_where_preserves_matching_rows_and_metadata",
)
def test_full_outer_join_then_where_identifies_missing_side():
    left, right = make_small_join_tables()
    joined = left.join(right, "key", full_outer=True)
    missing = joined.where(
        lambda row: row["left_value"] is None or row["right_value"] is None
    )
    assert rows_of(missing) == [
        ("B", Decimal("2"), None, None),
        (None, None, "C", "new"),
    ]


@pytest.mark.depends_on(
    "test_normalize_emits_key_property_value_rows",
    "test_denormalize_restores_sparse_properties",
)
def test_normalize_then_denormalize_round_trip_preserves_profiles(profiles_table):
    normalized = profiles_table.normalize("id", ["name", "city", "tier"])
    restored = normalized.denormalize("id")
    assert restored.column_names == ("id", "name", "city", "tier")
    assert rows_of(restored) == rows_of(profiles_table)
    assert restored.row_names == ("p1", "p2")


@pytest.mark.depends_on(
    "test_normalize_emits_key_property_value_rows",
    "test_denormalize_restores_sparse_properties",
)
def test_normalize_custom_column_names_round_trip(profiles_table):
    normalized = profiles_table.normalize(
        "id",
        ["city", "tier"],
        property_column="field",
        value_column="entry",
    )
    restored = normalized.denormalize("id", "field", "entry")
    assert restored.column_names == ("id", "city", "tier")
    assert rows_of(restored) == [
        ("p1", "NY", "gold"),
        ("p2", "SF", "silver"),
    ]


@pytest.mark.depends_on(
    "test_pivot_count_uses_key_and_pivot_columns",
    "test_normalize_emits_key_property_value_rows",
    "test_denormalize_restores_sparse_properties",
)
def test_pivot_then_denormalize_matches_grouped_counts(sales_table):
    pivoted = sales_table.pivot("region", "product")
    restored = pivoted.normalize(
        "region", ["alpha", "beta", "gamma"]
    ).denormalize("region")
    assert restored.column_names == pivoted.column_names
    assert rows_of(restored) == rows_of(pivoted)


@pytest.mark.depends_on(
    "test_pivot_count_uses_key_and_pivot_columns",
    "test_percent_and_percent_change_add_columns",
)
def test_pivot_percent_computation_sums_each_group(sales_table):
    from agate import Percent

    pivoted = sales_table.pivot(
        "region",
        "product",
        computation=Percent("Count"),
    )
    totals = [
        sum(row[name] for name in ("alpha", "beta", "gamma")).quantize(
            Decimal("0.01")
        )
        for row in pivoted.rows
    ]
    assert totals == [Decimal("50.00"), Decimal("50.00")]


@pytest.mark.depends_on(
    "test_table_csv_round_trip_reads_local_file",
    "test_select_preserves_requested_column_order",
)
def test_table_csv_round_trip_then_select_projection(tmp_path, sales_table):
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
    )
    projected = restored.select(["rep", "revenue"])
    assert rows_of(projected) == [
        ("Ada", Decimal("10.50")),
        ("Ben", Decimal("20.00")),
        ("Cy", Decimal("5.50")),
        ("Ada", Decimal("30.00")),
        ("Ben", Decimal("15.00")),
        ("Cy", Decimal("25.00")),
    ]


@pytest.mark.depends_on(
    "test_table_json_round_trip_reads_local_file",
    "test_compute_formula_adds_typed_column",
)
def test_table_json_round_trip_then_compute_projection(tmp_path, sales_table):
    from agate import Boolean, Formula, Number, Table, Text

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
    projected = restored.compute(
        [
            (
                "double_units",
                Formula(
                    Number(locale="en_US"),
                    lambda row: row["units"] * 2,
                ),
            )
        ]
    )
    assert projected.rows[0]["double_units"] == Decimal("4")
    assert projected.rows[-1]["double_units"] == Decimal("10")


@pytest.mark.depends_on(
    "test_table_newline_json_round_trip_reads_local_file",
    "test_order_by_places_nulls_last",
)
def test_newline_json_round_trip_then_order_projection(tmp_path, sales_table):
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
    ordered = restored.order_by("revenue", reverse=True)
    assert ordered.rows[0]["revenue"] == Decimal("30.00")
    assert ordered.rows[-1]["revenue"] == Decimal("5.50")


@pytest.mark.depends_on(
    "test_table_csv_round_trip_reads_local_file",
    "test_table_from_object_flattens_public_rows",
)
def test_print_csv_can_feed_from_csv(sales_table):
    from agate import Boolean, Number, Table, Text

    output = StringIO()
    with redirect_stdout(output):
        sales_table.print_csv()
    output.seek(0)
    restored = Table.from_csv(
        output,
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


@pytest.mark.depends_on(
    "test_table_json_round_trip_reads_local_file",
    "test_table_from_object_flattens_public_rows",
)
def test_print_json_can_feed_from_json(sales_table):
    from agate import Boolean, Number, Table, Text

    output = StringIO()
    with redirect_stdout(output):
        sales_table.print_json()
    output.seek(0)
    restored = Table.from_json(
        output,
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


@pytest.mark.depends_on(
    "test_tableset_csv_round_trip_reads_local_directory",
    "test_group_by_builds_public_tableset",
)
def test_tableset_csv_round_trip_then_aggregate(tmp_path, sales_table):
    from agate import Boolean, Count, Number, TableSet, Text

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
    summary = restored.aggregate([("rows", Count())])
    assert rows_of(summary) == [("east", Decimal("3")), ("west", Decimal("3"))]


@pytest.mark.depends_on(
    "test_tableset_nested_json_round_trip_reads_local_file",
    "test_tableset_proxy_select_preserves_group_keys",
)
def test_tableset_nested_json_round_trip_then_proxy(tmp_path, sales_table):
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
    active = restored.where(lambda row: row["active"])
    assert active.keys() == ("east", "west")
    assert [len(table) for table in active.values()] == [2, 2]


@pytest.mark.depends_on(
    "test_datetime_cast_uses_explicit_format",
    "test_timedelta_casts_duration_without_locale",
    "test_table_json_round_trip_reads_local_file",
)
def test_temporal_table_json_round_trip_preserves_public_types(tmp_path, temporal_table):
    from agate import Date, DateTime, Number, Table, Text, TimeDelta

    path = tmp_path / "temporal.json"
    temporal_table.to_json(str(path))
    restored = Table.from_json(
        str(path),
        column_types=[
            Text(),
            Date(date_format="%Y-%m-%d"),
            DateTime(datetime_format="%Y-%m-%dT%H:%M:%S"),
            TimeDelta(),
            Number(locale="en_US"),
        ],
    )
    assert type_names(restored) == (
        "Text",
        "Date",
        "DateTime",
        "TimeDelta",
        "Number",
    )
    assert rows_of(restored) == rows_of(temporal_table)
    assert restored.rows[0]["day"] == date(2024, 1, 2)
    assert restored.rows[0]["created"] == datetime(2024, 1, 2, 3, 4, 5)
    assert restored.rows[0]["elapsed"] == timedelta(hours=1, minutes=30)


@pytest.mark.depends_on(
    "test_type_tester_infers_controlled_public_types",
    "test_table_csv_round_trip_reads_local_file",
)
def test_type_tester_csv_route_agrees_with_explicit_types(tmp_path):
    from agate import Date, Number, Table, Text, TypeTester

    path = tmp_path / "typed.csv"
    path.write_text(
        "id,amount,day,note\np1,10.50,2024-01-02,alpha\np2,20.00,2024-01-03,beta\n"
    )
    tester = TypeTester(
        types=[
            Number(locale="en_US"),
            Date(date_format="%Y-%m-%d"),
            Text(),
        ]
    )
    restored = Table.from_csv(str(path), column_types=tester)
    assert type_names(restored) == ("Text", "Number", "Date", "Text")
    assert rows_of(restored)[0] == (
        "p1",
        Decimal("10.50"),
        date(2024, 1, 2),
        "alpha",
    )


@pytest.mark.depends_on(
    "test_table_csv_round_trip_reads_local_file",
    "test_left_join_adds_right_projection",
    "test_table_aggregate_returns_named_values",
)
def test_join_csv_sources_then_aggregate(tmp_path, sales_table, regions_table):
    from agate import Boolean, Number, Sum, Table
    from agate import Text

    sales_path = tmp_path / "sales.csv"
    regions_path = tmp_path / "regions.csv"
    sales_table.to_csv(str(sales_path))
    regions_table.to_csv(str(regions_path))
    sales = Table.from_csv(
        str(sales_path),
        column_types=[
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
        ],
    )
    regions = Table.from_csv(
        str(regions_path),
        column_types=[Text(), Text(), Number(locale="en_US")],
    )
    summary = sales.join(regions, "region").group_by("manager").aggregate(
        [("revenue", Sum("revenue"))]
    )
    assert rows_of(summary) == [
        ("Ellen", Decimal("36.00")),
        ("Wes", Decimal("70.00")),
    ]


@pytest.mark.depends_on(
    "test_compute_formula_adds_typed_column",
    "test_print_structure_reports_columns_and_types",
    "test_print_table_reports_headers_and_values",
)
def test_text_projections_follow_transformed_metadata(sales_table):
    from agate import Formula, Number

    computed = sales_table.compute(
        [
            (
                "line_total",
                Formula(
                    Number(locale="en_US"),
                    lambda row: row["units"] * row["revenue"],
                ),
            )
        ]
    )
    structure = StringIO()
    computed.print_structure(output=structure)
    table_text = StringIO()
    computed.select(["region", "line_total"]).print_table(
        output=table_text, locale="en_US"
    )
    assert "| line_total | Number" in structure.getvalue()
    assert "line_total" in table_text.getvalue()
    assert "revenue" not in table_text.getvalue()


@pytest.mark.depends_on(
    "test_print_bars_reports_labels_and_counts",
    "test_pivot_count_uses_key_and_pivot_columns",
)
def test_print_bars_follows_pivot_counts(sales_table):
    output = StringIO()
    counts = sales_table.pivot(lambda row: row["region"])
    counts.print_bars(output=output, width=40, printable=True)
    lines = output.getvalue().splitlines()
    assert any("east" in line and "3" in line for line in lines)
    assert any("west" in line and "3" in line for line in lines)
    assert "3.00" in lines[-1]


@pytest.mark.depends_on(
    "test_table_aggregate_returns_named_values",
    "test_columns_expose_distinct_and_sorted_values",
)
def test_aggregate_summary_matches_column_projection(sales_table):
    from agate import Count, Max, Min, Sum

    summary = sales_table.aggregate(
        [
            ("count", Count("revenue")),
            ("sum", Sum("revenue")),
            ("min", Min("revenue")),
            ("max", Max("revenue")),
        ]
    )
    revenue = sales_table.columns["revenue"]
    assert summary["count"] == len(revenue.values_without_nulls())
    assert summary["sum"] == sum(revenue.values_without_nulls())
    assert summary["min"] == min(revenue.values_without_nulls())
    assert summary["max"] == max(revenue.values_without_nulls())


@pytest.mark.depends_on(
    "test_group_by_builds_public_tableset",
    "test_tableset_proxy_select_preserves_group_keys",
    "test_order_by_places_nulls_last",
)
def test_table_merge_preserves_group_order_after_select(sales_table):
    ordered = sales_table.order_by(["region", "product"])
    merged = ordered.group_by("region").select(["product", "units"]).merge()
    assert [row["region"] for row in merged.rows[:3]] == ["east", "east", "east"]
    assert [row["region"] for row in merged.rows[3:]] == ["west", "west", "west"]
    assert merged.rows[0]["product"] == "alpha"


@pytest.mark.depends_on(
    "test_left_join_adds_right_projection",
    "test_select_preserves_requested_column_order",
)
def test_required_match_reports_unmatched_join():
    left, right = make_small_join_tables()
    projected = left.select(["key", "left_value"])
    with pytest.raises(ValueError):
        projected.join(right, "key", require_match=True)


@pytest.mark.depends_on(
    "test_inner_join_drops_unmatched_rows",
    "test_full_outer_join_retains_dangling_rows",
    "test_select_preserves_requested_column_order",
)
def test_invalid_join_mode_reports_public_value_error():
    left, right = make_small_join_tables()
    projected = right.select(["key", "right_value"])
    with pytest.raises(ValueError):
        left.join(projected, "key", inner=True, full_outer=True)


@pytest.mark.depends_on(
    "test_compute_formula_adds_typed_column",
    "test_table_csv_round_trip_reads_local_file",
)
def test_compute_then_csv_round_trip_preserves_formula(tmp_path, sales_table):
    from agate import Boolean, Formula, Number, Table, Text

    computed = sales_table.compute(
        [
            (
                "line_total",
                Formula(
                    Number(locale="en_US"),
                    lambda row: row["units"] * row["revenue"],
                ),
            )
        ]
    )
    path = tmp_path / "computed.csv"
    computed.to_csv(str(path))
    restored = Table.from_csv(
        str(path),
        column_types=[
            Text(),
            Text(),
            Text(),
            Number(locale="en_US"),
            Number(locale="en_US"),
            Boolean(),
            Number(locale="en_US"),
        ],
    )
    assert restored.column_names[-1] == "line_total"
    assert restored.columns["line_total"].values() == computed.columns["line_total"].values()


@pytest.mark.depends_on(
    "test_table_json_round_trip_reads_local_file",
    "test_table_row_names_can_come_from_column",
)
def test_local_json_round_trip_with_row_names_projection(tmp_path, profiles_table):
    from agate import Table, Text

    path = tmp_path / "profiles.json"
    profiles_table.to_json(str(path))
    restored = Table.from_json(
        str(path),
        row_names="id",
        column_types=[Text(), Text(), Text(), Text()],
    )
    assert restored.row_names == ("p1", "p2")
    assert restored.rows["p2"]["name"] == "Ben"


@pytest.mark.depends_on(
    "test_group_by_builds_public_tableset",
    "test_compute_formula_adds_typed_column",
)
def test_table_set_workflow_group_compute_having_merge(sales_table):
    from agate import Formula, Number, Sum

    groups = sales_table.group_by("region").compute(
        [
            (
                "gross",
                Formula(
                    Number(locale="en_US"),
                    lambda row: row["revenue"] * 2,
                ),
            )
        ]
    )
    kept = groups.having(
        [("gross_total", Sum("gross"))],
        lambda values: values["gross_total"] > Decimal("100"),
    )
    merged = kept.select(["product", "gross"]).merge()
    assert kept.keys() == ("west",)
    assert merged.column_names == ("region", "product", "gross")
    assert len(merged) == 3
