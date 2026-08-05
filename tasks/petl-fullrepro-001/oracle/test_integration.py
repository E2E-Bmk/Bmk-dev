from __future__ import annotations

from collections import OrderedDict

import pytest


@pytest.mark.depends_on(
    "test_csv_path_round_trip_preserves_delimited_values",
    "test_convert_applies_callable_to_field",
    "test_select_field_predicate_keeps_matching_rows",
    "test_cut_selects_and_reorders_fields",
)
def test_csv_convert_select_cut_pipeline(sales_table, tmp_path):
    import petl as etl

    source = tmp_path / "sales.csv"
    etl.tocsv(sales_table, str(source))
    loaded = etl.fromcsv(str(source))
    typed = etl.convert(loaded, "amount", int)
    selected = etl.select(typed, "active", lambda value: value == "True")
    result = etl.cut(selected, "customer", "region", "amount")
    assert list(result) == [
        ("customer", "region", "amount"),
        ("Ada", "east", 10),
        ("Noa", "east", 15),
        ("Mia", "west", 5),
    ]


@pytest.mark.depends_on(
    "test_cut_selects_and_reorders_fields",
    "test_convert_applies_callable_to_field",
    "test_cat_appends_compatible_tables",
)
def test_cut_convert_and_cat_combine_batches(sales_table):
    import petl as etl

    first = etl.convert(etl.cut(sales_table, "region", "amount"), "amount", lambda value: value * 2)
    second = [["region", "amount"], ["north", 7]]
    assert list(etl.cat(first, second)) == [
        ("region", "amount"),
        ("east", 20),
        ("west", 40),
        ("east", 30),
        ("west", 10),
        ("north", 7),
    ]


@pytest.mark.depends_on(
    "test_select_field_predicate_keeps_matching_rows",
    "test_aggregate_sums_field_per_key",
)
def test_select_then_aggregate_sales_by_region(sales_table):
    import petl as etl

    active = etl.select(sales_table, "active", bool)
    result = etl.aggregate(active, "region", sum, "amount")
    assert list(result) == [
        ("region", "value"),
        ("east", 25),
        ("west", 5),
    ]


@pytest.mark.depends_on(
    "test_join_matches_rows_on_common_key",
    "test_lookup_collects_duplicate_values",
)
def test_join_then_lookup_manager_names(sales_table, manager_table):
    import petl as etl

    joined = etl.join(sales_table, manager_table, "region")
    assert etl.lookup(joined, "customer", "manager") == {
        "Ada": ["Rae"],
        "Lin": ["Kai"],
        "Noa": ["Rae"],
        "Mia": ["Kai"],
    }


@pytest.mark.depends_on(
    "test_leftjoin_fills_missing_right_values",
    "test_select_field_predicate_keeps_matching_rows",
)
def test_leftjoin_then_select_active_customers(sales_table, manager_table):
    import petl as etl

    enriched = etl.leftjoin(sales_table, manager_table, "region")
    active = etl.select(enriched, "active", bool)
    assert list(etl.cut(active, "customer", "manager")) == [
        ("customer", "manager"),
        ("Ada", "Rae"),
        ("Noa", "Rae"),
        ("Mia", "Kai"),
    ]


@pytest.mark.depends_on(
    "test_convert_applies_callable_to_field",
    "test_aggregate_supports_multiple_named_reductions",
)
def test_converted_amounts_feed_multiple_group_reductions(sales_table):
    import petl as etl

    typed = etl.convert(sales_table, "amount", float)
    aggregations = OrderedDict(
        [
            ("count", len),
            ("total", ("amount", sum)),
            ("customers", ("customer", list)),
        ]
    )
    result = etl.aggregate(typed, "region", aggregations)
    assert list(result) == [
        ("region", "count", "total", "customers"),
        ("east", 2, 25.0, ["Ada", "Noa"]),
        ("west", 2, 25.0, ["Lin", "Mia"]),
    ]


@pytest.mark.depends_on(
    "test_pivot_builds_columns_from_second_field",
    "test_cut_selects_and_reorders_fields",
)
def test_pivot_then_cut_projects_selected_customers(sales_table):
    import petl as etl

    pivoted = etl.pivot(sales_table, "region", "customer", "amount", sum, missing=0)
    result = etl.cut(pivoted, "region", "Ada", "Noa")
    assert list(result) == [
        ("region", "Ada", "Noa"),
        ("east", 10, 15),
        ("west", 0, 0),
    ]


@pytest.mark.depends_on(
    "test_fromdicts_respects_explicit_header",
    "test_convert_applies_callable_to_field",
    "test_select_field_predicate_keeps_matching_rows",
)
def test_fromdicts_then_convert_and_select():
    import petl as etl

    rows = [
        {"customer": "Ada", "amount": "10", "active": "yes"},
        {"customer": "Lin", "amount": "20", "active": "no"},
        {"customer": "Noa", "amount": "15", "active": "yes"},
    ]
    table = etl.fromdicts(rows, header=["customer", "amount", "active"])
    typed = etl.convert(table, "amount", int)
    selected = etl.select(typed, "active", lambda value: value == "yes")
    assert list(selected) == [
        ("customer", "amount", "active"),
        ("Ada", 10, "yes"),
        ("Noa", 15, "yes"),
    ]


@pytest.mark.depends_on(
    "test_transform_view_is_lazy_until_iteration",
    "test_select_field_predicate_keeps_matching_rows",
    "test_aggregate_sums_field_per_key",
)
def test_lazy_view_can_feed_downstream_pipeline(counting_table):
    import petl as etl

    converted = etl.convert(counting_table, "amount", lambda value: value * 2)
    selected = etl.select(converted, "active", bool)
    summary = etl.aggregate(selected, "region", sum, "amount")
    assert counting_table.iterations == 0
    assert list(summary) == [
        ("region", "value"),
        ("east", 50),
        ("west", 10),
    ]
    assert counting_table.iterations >= 1


@pytest.mark.depends_on(
    "test_csv_path_round_trip_preserves_delimited_values",
    "test_transform_view_supports_repeated_iteration",
)
def test_csv_view_supports_two_independent_consumers(sales_table, tmp_path):
    import petl as etl

    source = tmp_path / "sales.csv"
    etl.tocsv(sales_table, str(source))
    view = etl.fromcsv(str(source))
    first = list(view)
    second = list(view)
    assert first == second
    assert first[0] == ("id", "customer", "region", "amount", "category", "active")


@pytest.mark.depends_on(
    "test_csv_path_round_trip_preserves_delimited_values",
    "test_convert_applies_callable_to_field",
)
def test_csv_round_trip_after_transformation(sales_table, tmp_path):
    import petl as etl

    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    etl.tocsv(sales_table, str(source))
    typed = etl.convert(etl.fromcsv(str(source)), "amount", int)
    etl.tocsv(typed, str(output))
    rows = list(etl.fromcsv(str(output)))
    assert rows[0] == ("id", "customer", "region", "amount", "category", "active")
    assert rows[1][3] == "10"
    assert rows[-1][3] == "5"


@pytest.mark.depends_on(
    "test_csv_custom_delimiter_round_trip",
    "test_convert_applies_callable_to_field",
)
def test_custom_delimiter_round_trip_then_convert(tmp_path):
    import petl as etl

    raw = [
        ["customer", "amount"],
        ["Ada", "10"],
        ["Lin", "20"],
    ]
    path = tmp_path / "amounts.psv"
    etl.tocsv(raw, str(path), delimiter=";")
    typed = etl.convert(etl.fromcsv(str(path), delimiter=";"), "amount", int)
    assert list(typed) == [
        ("customer", "amount"),
        ("Ada", 10),
        ("Lin", 20),
    ]


@pytest.mark.depends_on(
    "test_select_field_predicate_keeps_matching_rows",
    "test_convert_applies_callable_to_field",
    "test_cut_selects_and_reorders_fields",
)
def test_table_method_chain_matches_top_level_pipeline(sales_table):
    import petl as etl

    top_level = etl.cut(
        etl.convert(
            etl.select(sales_table, "active", bool),
            "amount",
            lambda value: value + 1,
        ),
        "customer",
        "amount",
    )
    chained = (
        etl.wrap(sales_table)
        .select("active", bool)
        .convert("amount", lambda value: value + 1)
        .cut("customer", "amount")
    )
    assert list(chained) == list(top_level)


@pytest.mark.depends_on(
    "test_select_row_expression_uses_named_fields",
    "test_cut_selects_and_reorders_fields",
    "test_lookstr_uses_string_value_projection",
)
def test_expression_filter_cut_and_lookstr_share_values(sales_table):
    import petl as etl

    selected = etl.select(sales_table, "{region} == 'east' and {amount} > 10")
    projected = etl.cut(selected, "customer", "amount")
    output = str(etl.lookstr(projected))
    assert "customer" in output
    assert "Noa" in output
    assert "15" in output
    assert "Ada" not in output


@pytest.mark.depends_on(
    "test_select_field_predicate_keeps_matching_rows",
    "test_select_complement_inverts_predicate",
    "test_cat_appends_compatible_tables",
)
def test_complementary_selects_can_be_combined_back(sales_table):
    import petl as etl

    active = etl.select(sales_table, "active", bool)
    inactive = etl.select(sales_table, "active", bool, complement=True)
    combined = etl.cat(active, inactive)
    assert sorted(etl.data(combined), key=lambda row: row[0]) == sorted(
        [tuple(row) for row in sales_table[1:]], key=lambda row: row[0]
    )


@pytest.mark.depends_on(
    "test_join_matches_rows_on_common_key",
    "test_lookupone_returns_scalar_values",
)
def test_join_with_different_key_names():
    import petl as etl

    left = [["customer_id", "name"], [1, "Ada"], [2, "Lin"]]
    right = [["id", "segment"], [1, "A"], [2, "B"], [3, "C"]]
    joined = etl.join(left, right, lkey="customer_id", rkey="id")
    assert list(joined) == [
        ("customer_id", "name", "segment"),
        (1, "Ada", "A"),
        (2, "Lin", "B"),
    ]
    assert etl.lookupone(joined, "customer_id", "segment") == {1: "A", 2: "B"}


@pytest.mark.depends_on(
    "test_leftjoin_fills_missing_right_values",
    "test_values_projects_one_field",
)
def test_leftjoin_custom_missing_marker(sales_table, id_label_table):
    import petl as etl

    result = etl.leftjoin(sales_table, id_label_table, key="id", missing="unknown")
    assert list(etl.values(result, "label")) == ["one", "unknown", "three", "unknown"]


@pytest.mark.depends_on(
    "test_join_matches_rows_on_common_key",
    "test_leftjoin_fills_missing_right_values",
    "test_cut_selects_and_reorders_fields",
)
def test_outerjoin_includes_unmatched_keys(sales_table, id_label_table):
    import petl as etl

    result = etl.outerjoin(sales_table, id_label_table, key="id")
    rows = list(result)
    assert rows[0] == ("id", "customer", "region", "amount", "category", "active", "label")
    assert rows[-1] == (5, None, None, None, None, None, "five")
    assert len(rows) == 6
    assert list(etl.cut(result, "id", "label")) == [
        ("id", "label"),
        (1, "one"),
        (2, None),
        (3, "three"),
        (4, None),
        (5, "five"),
    ]


@pytest.mark.depends_on(
    "test_lookup_collects_duplicate_values",
    "test_select_field_predicate_keeps_matching_rows",
)
def test_compound_lookup_groups_by_two_fields(sales_table):
    import petl as etl

    active = etl.select(sales_table, "active", bool)
    result = etl.lookup(active, ("region", "category"), "customer")
    assert result == {
        ("east", "A"): ["Ada", "Noa"],
        ("west", "B"): ["Mia"],
    }


@pytest.mark.depends_on(
    "test_lookupone_returns_scalar_values",
    "test_cut_selects_and_reorders_fields",
)
def test_lookupone_default_rows_can_be_indexed(id_label_table):
    import petl as etl

    projected = etl.cut(id_label_table, "id", "label")
    result = etl.lookupone(projected, "id")
    assert result[3] == (3, "three")
    assert result[5] == (5, "five")


@pytest.mark.depends_on(
    "test_aggregate_sums_field_per_key",
    "test_convert_applies_callable_to_field",
)
def test_aggregate_without_key_returns_one_total(sales_table):
    import petl as etl

    typed = etl.convert(sales_table, "amount", float)
    assert list(etl.aggregate(typed, None, sum, "amount")) == [
        ("value",),
        (50.0,),
    ]


@pytest.mark.depends_on(
    "test_aggregate_sums_field_per_key",
    "test_select_field_predicate_keeps_matching_rows",
)
def test_aggregate_can_collect_compound_values(sales_table):
    import petl as etl

    active = etl.select(sales_table, "active", bool)
    result = etl.aggregate(active, "region", list, ("customer", "amount"))
    assert list(result) == [
        ("region", "value"),
        ("east", [("Ada", 10), ("Noa", 15)]),
        ("west", [("Mia", 5)]),
    ]


@pytest.mark.depends_on(
    "test_pivot_builds_columns_from_second_field",
    "test_cut_selects_and_reorders_fields",
)
def test_pivot_missing_cells_use_explicit_value():
    import petl as etl

    table = [
        ["region", "product", "amount"],
        ["east", "A", 10],
        ["west", "B", 20],
    ]
    pivoted = etl.pivot(table, "region", "product", "amount", sum, missing=-1)
    result = etl.cut(pivoted, "region", "B", "A")
    assert list(result) == [
        ("region", "B", "A"),
        ("east", -1, 10),
        ("west", 20, -1),
    ]


@pytest.mark.depends_on(
    "test_pivot_builds_columns_from_second_field",
    "test_convert_applies_callable_to_field",
    "test_cut_selects_and_reorders_fields",
)
def test_pivot_result_can_be_converted_and_projected(sales_table):
    import petl as etl

    pivoted = etl.pivot(sales_table, "region", "customer", "amount", sum, missing=0)
    adjusted = etl.convert(pivoted, "Ada", lambda value: value + 100)
    result = etl.cut(adjusted, "region", "Ada", "Noa")
    assert list(result) == [
        ("region", "Ada", "Noa"),
        ("east", 110, 15),
        ("west", 100, 0),
    ]


@pytest.mark.depends_on(
    "test_cut_selects_and_reorders_fields",
    "test_html_display_projection_contains_table_cells",
)
def test_html_projection_tracks_transformed_header(sales_table):
    import petl as etl

    projected = etl.cut(sales_table, "customer", "amount")
    html = projected._repr_html_()
    assert "<th>customer</th>" in html
    assert "<th>amount</th>" in html
    assert ">Noa<" in html


@pytest.mark.depends_on(
    "test_look_contains_header_and_values",
    "test_html_display_projection_contains_table_cells",
)
def test_text_and_html_display_projections_agree_on_values(sales_table):
    import petl as etl

    projected = etl.cut(sales_table, "customer", "amount")
    text = str(etl.lookstr(projected))
    html = projected._repr_html_()
    for value in ("customer", "amount", "Ada", "10", "Mia", "5"):
        assert value in text
        assert value in html


@pytest.mark.depends_on(
    "test_header_returns_tuple",
    "test_data_excludes_header",
    "test_values_projects_one_field",
)
def test_header_data_and_values_remain_consistent_after_cut(sales_table):
    import petl as etl

    projected = etl.cut(sales_table, "customer", "region", "amount")
    assert etl.header(projected) == ("customer", "region", "amount")
    assert list(etl.data(projected)) == [
        ("Ada", "east", 10),
        ("Lin", "west", 20),
        ("Noa", "east", 15),
        ("Mia", "west", 5),
    ]
    assert list(etl.values(projected, "amount")) == [10, 20, 15, 5]


@pytest.mark.depends_on(
    "test_transform_view_is_lazy_until_iteration",
    "test_convert_applies_callable_to_field",
)
def test_lazy_conversion_does_not_mutate_source(sales_table):
    import petl as etl

    original = [row[:] for row in sales_table]
    view = etl.convert(sales_table, "amount", lambda value: value + 100)
    assert sales_table == original
    list(view)
    assert sales_table == original


@pytest.mark.depends_on(
    "test_transform_view_supports_repeated_iteration",
    "test_select_field_predicate_keeps_matching_rows",
    "test_cut_selects_and_reorders_fields",
)
def test_reusing_a_pipeline_produces_same_rows(sales_table):
    import petl as etl

    pipeline = etl.cut(
        etl.select(
            etl.convert(sales_table, "amount", lambda value: value * 3),
            "active",
            bool,
        ),
        "id",
        "amount",
    )
    expected = [
        ("id", "amount"),
        (1, 30),
        (3, 45),
        (4, 15),
    ]
    assert list(pipeline) == expected
    assert list(pipeline) == expected


@pytest.mark.depends_on(
    "test_csv_path_round_trip_preserves_delimited_values",
    "test_convert_applies_callable_to_field",
    "test_join_matches_rows_on_common_key",
    "test_aggregate_sums_field_per_key",
)
def test_local_csv_join_and_aggregate_workflow(sales_table, manager_table, tmp_path):
    import petl as etl

    sales_path = tmp_path / "sales.csv"
    manager_path = tmp_path / "manager.csv"
    etl.tocsv(sales_table, str(sales_path))
    etl.tocsv(manager_table, str(manager_path))
    sales = etl.convert(etl.fromcsv(str(sales_path)), "amount", int)
    managers = etl.fromcsv(str(manager_path))
    joined = etl.join(sales, managers, "region")
    summary = etl.aggregate(joined, "manager", sum, "amount")
    assert list(summary) == [
        ("manager", "value"),
        ("Kai", 25),
        ("Rae", 25),
    ]


@pytest.mark.depends_on(
    "test_join_matches_rows_on_common_key",
    "test_lookup_collects_duplicate_values",
)
def test_joined_manager_projection_matches_lookup_projection(sales_table, manager_table):
    import petl as etl

    joined = etl.join(sales_table, manager_table, "region")
    direct = etl.lookup(manager_table, "region", "manager")
    for region in ("east", "west"):
        values = direct[region]
        assert set(etl.values(etl.select(joined, "region", lambda value: value == region), "manager")) == {
            values[0]
        }


@pytest.mark.depends_on(
    "test_csv_path_round_trip_preserves_delimited_values",
    "test_convert_applies_callable_to_field",
    "test_select_field_predicate_keeps_matching_rows",
    "test_join_matches_rows_on_common_key",
    "test_aggregate_sums_field_per_key",
    "test_pivot_builds_columns_from_second_field",
)
def test_end_to_end_sales_workflow_projects_summary_and_pivot(
    sales_table, manager_table, tmp_path
):
    import petl as etl

    path = tmp_path / "sales.csv"
    etl.tocsv(sales_table, str(path))
    typed = etl.convert(etl.fromcsv(str(path)), "amount", int)
    active = etl.select(typed, "active", lambda value: value == "True")
    enriched = etl.join(active, manager_table, "region")
    summary = etl.aggregate(enriched, "manager", sum, "amount")
    grid = etl.pivot(active, "region", "category", "amount", sum, missing=0)
    assert list(summary) == [
        ("manager", "value"),
        ("Kai", 5),
        ("Rae", 25),
    ]
    assert list(grid) == [
        ("region", "A", "B"),
        ("east", 25, 0),
        ("west", 0, 5),
    ]
