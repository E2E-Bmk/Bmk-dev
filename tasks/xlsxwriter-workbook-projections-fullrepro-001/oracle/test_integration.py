from __future__ import annotations

from datetime import datetime

import pytest
import xlsxwriter

from conftest import NS, cells, finish, relationships, shared_texts, xml_part


@pytest.mark.depends_on("test_add_worksheet_projects_names_in_workbook_xml", "test_write_string_projects_shared_string_cell")
def test_named_sheets_and_strings_form_a_workbook_workflow(workbook_factory):
    stream, workbook = workbook_factory()
    summary = workbook.add_worksheet("Summary")
    details = workbook.add_worksheet("Details")
    summary.write_string("A1", "Report")
    details.write_string("A1", "Rows")
    data = finish(stream, workbook)
    root = xml_part(data, "xl/workbook.xml")
    assert [n.attrib["name"] for n in root.findall("x:sheets/x:sheet", NS)] == ["Summary", "Details"]
    assert set(shared_texts(data)) == {"Report", "Rows"}


@pytest.mark.depends_on("test_write_number_projects_numeric_value", "test_write_formula_projects_formula_and_cached_value")
def test_scalar_cells_and_formula_project_together(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_number("A1", 4)
    sheet.write_number("B1", 6)
    sheet.write_formula("C1", "=A1+B1", None, 10)
    cell_map = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))
    assert cell_map["A1"].findtext("x:v", namespaces=NS) == "4"
    assert cell_map["C1"].findtext("x:f", namespaces=NS) == "A1+B1"
    assert cell_map["C1"].findtext("x:v", namespaces=NS) == "10"


@pytest.mark.depends_on("test_write_datetime_projects_excel_serial_and_format", "test_add_format_bold_and_number_format_reach_styles_xml")
def test_formatted_datetime_and_numeric_cells_share_style_projection(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    fmt = workbook.add_format({"bold": True, "num_format": "0.00"})
    sheet.write_number("A1", 4.5, fmt)
    sheet.write_datetime("B1", datetime(2020, 1, 2), fmt)
    cell_map = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))
    assert cell_map["A1"].attrib["s"] == cell_map["B1"].attrib["s"]


@pytest.mark.depends_on("test_write_boolean_projects_boolean_cell_type", "test_write_column_projects_values_down_rows")
def test_column_data_and_boolean_flag_form_rows(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_column("A1", ["ready", "pending"])
    sheet.write_boolean("B1", True)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert set(cells(root)) == {"A1", "A2", "B1"}
    assert cells(root)["B1"].attrib["t"] == "b"


@pytest.mark.depends_on("test_write_rich_string_projects_multiple_runs", "test_write_string_projects_shared_string_cell")
def test_rich_and_plain_strings_keep_distinct_shared_string_entries(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    bold = workbook.add_format({"bold": True})
    sheet.write_rich_string("A1", bold, "rich", " text")
    sheet.write_string("A2", "plain")
    data = finish(stream, workbook)
    texts = shared_texts(data)
    assert any("rich" in value and "text" in value for value in texts)
    assert "plain" in texts


@pytest.mark.depends_on("test_write_array_formula_projects_range_reference", "test_write_formula_projects_formula_and_cached_value")
def test_array_and_scalar_formula_ranges_remain_separate(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_array_formula("A1:A2", "=ROW(A1:A2)", None, 1)
    sheet.write_formula("B1", "=A1+1", None, 2)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find(".//x:c[@r='A1']/x:f", NS).attrib["ref"] == "A1:A2"
    assert root.find(".//x:c[@r='B1']/x:f", NS).text == "A1+1"


@pytest.mark.depends_on("test_write_dynamic_array_formula_projects_dynamic_marker", "test_write_number_projects_numeric_value")
def test_dynamic_formula_and_source_number_form_spill_projection(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_number("D1", 2)
    sheet.write_dynamic_array_formula("A1:B2", "=SEQUENCE(D1,2)", None, 1)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find(".//x:c[@r='A1']", NS).attrib["cm"] == "1"
    assert root.find(".//x:c[@r='D1']/x:v", NS).text == "2"


@pytest.mark.depends_on("test_write_row_projects_mixed_values_across_columns", "test_write_column_projects_values_down_rows")
def test_row_and_column_writes_build_a_rectangular_data_block(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_row("A1", ["Item", "Count"])
    sheet.write_column("A2", ["one", "two"])
    sheet.write_column("B2", [1, 2])
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert set(cells(root)) == {"A1", "B1", "A2", "A3", "B2", "B3"}


@pytest.mark.depends_on("test_write_blank_with_format_projects_style_only_cell", "test_set_column_projects_width_and_custom_width")
def test_blank_format_and_column_width_preserve_layout_metadata(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_blank("C3", None, workbook.add_format({"border": 1}))
    sheet.set_column("C:C", 16)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find(".//x:c[@r='C3']", NS).attrib.get("s")
    assert root.find("x:cols/x:col", NS).attrib["min"] == "3"


@pytest.mark.depends_on("test_set_row_projects_height_and_hidden_state", "test_freeze_panes_projects_frozen_view")
def test_hidden_rows_and_frozen_header_form_view_state(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.set_row(0, 22, None, {"hidden": True})
    sheet.freeze_panes(1, 0)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find("x:sheetData/x:row", NS).attrib["hidden"] == "1"
    assert root.find("x:sheetViews/x:sheetView/x:pane", NS).attrib["state"] == "frozen"


@pytest.mark.depends_on("test_merge_range_projects_merge_cell_ref", "test_write_string_projects_shared_string_cell")
def test_merged_label_and_cell_projection_form_one_section(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().merge_range("A1:C1", "Section")
    data = finish(stream, workbook)
    root = xml_part(data, "xl/worksheets/sheet1.xml")
    assert root.find("x:mergeCells/x:mergeCell", NS).attrib["ref"] == "A1:C1"
    assert "Section" in shared_texts(data)


@pytest.mark.depends_on("test_autofilter_projects_filter_range", "test_write_row_projects_mixed_values_across_columns")
def test_header_row_and_autofilter_form_filterable_data(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_row("A1", ["Name", "State", "Score"])
    sheet.write_row("A2", ["Ada", "ok", 9])
    sheet.autofilter("A1:C2")
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find("x:autoFilter", NS).attrib["ref"] == "A1:C2"
    assert len(root.findall(".//x:c", NS)) == 6


@pytest.mark.depends_on("test_define_name_projects_global_and_local_names", "test_add_worksheet_projects_names_in_workbook_xml")
def test_global_and_local_names_track_two_sheet_workflow(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet("Data")
    workbook.add_worksheet("Report")
    workbook.define_name("DataRange", "=Data!$A$1:$A$3")
    workbook.define_name("Report!PrintArea", "=Report!$A$1:$C$8")
    root = xml_part(finish(stream, workbook), "xl/workbook.xml")
    names = root.findall("x:definedNames/x:definedName", NS)
    assert [node.attrib["name"] for node in names] == ["DataRange", "PrintArea"]
    assert names[1].attrib["localSheetId"] == "1"


@pytest.mark.depends_on("test_add_table_projects_table_part_and_reference", "test_write_row_projects_mixed_values_across_columns")
def test_table_data_and_table_part_reference_same_range(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_row("A1", ["Product", "Qty"])
    sheet.write_row("A2", ["Widget", 3])
    sheet.add_table("A1:B2", {"name": "Inventory", "columns": [{"header": "Product"}, {"header": "Qty"}]})
    data = finish(stream, workbook)
    table = xml_part(data, "xl/tables/table1.xml")
    sheet_root = xml_part(data, "xl/worksheets/sheet1.xml")
    assert table.attrib["ref"] == "A1:B2"
    assert sheet_root.find("x:tableParts/x:tablePart", NS) is not None


@pytest.mark.depends_on("test_add_table_projects_table_part_and_reference", "test_write_comment_projects_comment_author_and_cell_ref")
def test_table_and_comment_parts_have_distinct_relationship_types(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_row("A1", ["Product", "Qty"])
    sheet.add_table("A1:B2", {"name": "Inventory"})
    sheet.write_comment("A1", "Header note")
    data = finish(stream, workbook)
    types = {entry["type"].rsplit("/", 1)[-1] for entry in relationships(data, "xl/worksheets/_rels/sheet1.xml.rels")}
    assert {"table", "comments", "vmlDrawing"} <= types


@pytest.mark.depends_on("test_write_external_url_projects_hyperlink_relationship", "test_write_internal_url_projects_location_without_external_target")
def test_external_and_internal_hyperlinks_use_different_projections(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Links")
    sheet.write_url("A1", "https://example.test", None, "External")
    sheet.write_url("A2", "internal:Links!A1", None, "Internal")
    data = finish(stream, workbook)
    root = xml_part(data, "xl/worksheets/sheet1.xml")
    links = root.findall("x:hyperlinks/x:hyperlink", NS)
    assert links[0].attrib["ref"] == "A1" and "{%s}id" % NS["r"] in links[0].attrib
    assert links[1].attrib["location"] == "Links!A1"
    assert len(relationships(data, "xl/worksheets/_rels/sheet1.xml.rels")) == 1


@pytest.mark.depends_on("test_write_comment_projects_comment_author_and_cell_ref", "test_set_properties_projects_title_without_asserting_timestamps")
def test_comment_author_and_core_author_are_independent_metadata(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.set_properties({"author": "Book Author"})
    sheet = workbook.add_worksheet()
    sheet.write_comment("B2", "Cell note", {"author": "Cell Author"})
    data = finish(stream, workbook)
    comment = xml_part(data, "xl/comments1.xml")
    core = xml_part(data, "docProps/core.xml")
    assert comment.find("x:authors/x:author", NS).text == "Cell Author"
    assert core.find("{http://purl.org/dc/elements/1.1/}creator").text == "Book Author"


@pytest.mark.depends_on("test_insert_chart_projects_chart_xml_and_drawing_relationship", "test_write_number_projects_numeric_value")
def test_chart_series_cache_projects_written_numeric_source(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("ChartData")
    sheet.write_column("A1", [5, 8, 13])
    chart = workbook.add_chart({"type": "column"})
    chart.add_series({"values": "=ChartData!$A$1:$A$3"})
    sheet.insert_chart("C1", chart)
    root = xml_part(finish(stream, workbook), "xl/charts/chart1.xml")
    series = root.find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}ser")
    assert series.find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}f").text == "ChartData!$A$1:$A$3"
    assert [node.text for node in series.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}numCache/{http://schemas.openxmlformats.org/drawingml/2006/chart}pt/{http://schemas.openxmlformats.org/drawingml/2006/chart}v")] == ["5", "8", "13"]


@pytest.mark.depends_on("test_insert_chart_projects_chart_xml_and_drawing_relationship", "test_define_name_projects_global_and_local_names")
def test_chart_and_defined_name_parts_coexist_in_package(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Data")
    sheet.write_number("A1", 7)
    workbook.define_name("ChartValue", "=Data!$A$1")
    chart = workbook.add_chart({"type": "line"})
    chart.add_series({"values": "=Data!$A$1:$A$1"})
    sheet.insert_chart("C3", chart)
    data = finish(stream, workbook)
    assert xml_part(data, "xl/workbook.xml").find("x:definedNames/x:definedName", NS).text == "Data!$A$1"
    assert xml_part(data, "xl/charts/chart1.xml").find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}lineChart") is not None


@pytest.mark.depends_on("test_set_calc_mode_projects_calculation_policy", "test_write_formula_projects_formula_and_cached_value")
def test_manual_calc_mode_and_formula_cache_form_recalculation_workflow(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_number("A1", 10)
    sheet.write_formula("B1", "=A1*2", None, 20)
    workbook.set_calc_mode("manual")
    root = xml_part(finish(stream, workbook), "xl/workbook.xml")
    formula_root = xml_part(stream.getvalue(), "xl/worksheets/sheet1.xml")
    assert root.find("x:calcPr", NS).attrib["calcMode"] == "manual"
    assert cells(formula_root)["B1"].findtext("x:v", namespaces=NS) == "20"


@pytest.mark.depends_on("test_workbook_projection_has_stable_required_parts", "test_add_worksheet_projects_names_in_workbook_xml")
def test_two_identical_sheet_builds_have_same_structural_member_set(workbook_factory):
    def build():
        stream, workbook = workbook_factory()
        workbook.add_worksheet("Stable")
        data = finish(stream, workbook)
        from zipfile import ZipFile
        from io import BytesIO
        with ZipFile(BytesIO(data)) as archive:
            return sorted(archive.namelist())

    assert build() == build()


@pytest.mark.depends_on("test_write_datetime_projects_excel_serial_and_format", "test_set_properties_projects_title_without_asserting_timestamps")
def test_date_cell_and_properties_keep_timestamp_sensitive_fields_out_of_projection(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.set_properties({"title": "Dates"})
    sheet = workbook.add_worksheet()
    sheet.write_datetime("A1", datetime(2020, 1, 2), workbook.add_format({"num_format": "yyyy-mm-dd"}))
    data = finish(stream, workbook)
    core = xml_part(data, "docProps/core.xml")
    cell = cells(xml_part(data, "xl/worksheets/sheet1.xml"))["A1"]
    assert core.find("{http://purl.org/dc/elements/1.1/}title").text == "Dates"
    assert cell.findtext("x:v", namespaces=NS) == "43832"


@pytest.mark.depends_on("test_write_fraction_projects_as_numeric_value", "test_write_formula_projects_formula_and_cached_value")
def test_numeric_fraction_and_formula_values_share_numeric_cell_contract(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write("A1", 0.5)
    sheet.write("B1", 0.25)
    sheet.write_formula("C1", "=A1+B1", None, 0.75)
    cell_map = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))
    assert [cell_map[name].findtext("x:v", namespaces=NS) for name in ("A1", "B1", "C1")] == ["0.5", "0.25", "0.75"]


@pytest.mark.depends_on("test_set_column_projects_width_and_custom_width", "test_set_row_projects_height_and_hidden_state")
def test_row_and_column_layout_settings_survive_with_written_cells(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_string("B3", "layout")
    sheet.set_column("B:B", 22)
    sheet.set_row(2, 30)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find("x:cols/x:col", NS).attrib["width"] == "22.7109375"
    assert root.find("x:sheetData/x:row", NS).attrib["ht"] == "30"


@pytest.mark.depends_on("test_merge_range_projects_merge_cell_ref", "test_add_table_projects_table_part_and_reference")
def test_merged_title_and_table_form_non_overlapping_structural_parts(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.merge_range("A1:B1", "Inventory")
    sheet.write_row("A3", ["Item", "Qty"])
    sheet.write_row("A4", ["Bolt", 4])
    sheet.add_table("A3:B4", {"name": "InventoryTable"})
    data = finish(stream, workbook)
    sheet_root = xml_part(data, "xl/worksheets/sheet1.xml")
    assert sheet_root.find("x:mergeCells/x:mergeCell", NS).attrib["ref"] == "A1:B1"
    assert xml_part(data, "xl/tables/table1.xml").attrib["ref"] == "A3:B4"


@pytest.mark.depends_on("test_write_external_url_projects_hyperlink_relationship", "test_write_comment_projects_comment_author_and_cell_ref")
def test_linked_and_annotated_cell_has_both_sheet_and_relationship_projections(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_url("A1", "https://example.test/item", None, "Item")
    sheet.write_comment("A1", "Open item")
    data = finish(stream, workbook)
    sheet_root = xml_part(data, "xl/worksheets/sheet1.xml")
    assert sheet_root.find("x:hyperlinks/x:hyperlink", NS).attrib["ref"] == "A1"
    relation_types = {item["type"].rsplit("/", 1)[-1] for item in relationships(data, "xl/worksheets/_rels/sheet1.xml.rels")}
    assert {"hyperlink", "comments"} <= relation_types


@pytest.mark.depends_on("test_insert_chart_projects_chart_xml_and_drawing_relationship", "test_set_column_projects_width_and_custom_width")
def test_chart_anchor_and_column_layout_form_dashboard_structure(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Dashboard")
    sheet.set_column("A:A", 14)
    sheet.write_column("A1", [1, 2, 3])
    chart = workbook.add_chart({"type": "pie"})
    chart.add_series({"values": "=Dashboard!$A$1:$A$3"})
    sheet.insert_chart("C2", chart)
    data = finish(stream, workbook)
    drawing = xml_part(data, "xl/drawings/drawing1.xml")
    assert drawing.find(".//{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}from/{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}col").text == "2"
    assert xml_part(data, "xl/worksheets/sheet1.xml").find("x:cols/x:col", NS).attrib["width"] == "14.7109375"


@pytest.mark.depends_on("test_add_table_projects_table_part_and_reference", "test_define_name_projects_global_and_local_names")
def test_table_and_name_refer_to_different_public_workbook_ranges(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Data")
    sheet.write_row("A1", ["Name", "Value"])
    sheet.write_row("A2", ["A", 1])
    sheet.add_table("A1:B2", {"name": "DataTable"})
    workbook.define_name("ValueCell", "=Data!$B$2")
    data = finish(stream, workbook)
    assert xml_part(data, "xl/tables/table1.xml").attrib["name"] == "DataTable"
    assert xml_part(data, "xl/workbook.xml").find("x:definedNames/x:definedName", NS).text == "Data!$B$2"


@pytest.mark.depends_on("test_get_worksheet_by_name_returns_the_public_sheet_object", "test_write_string_projects_shared_string_cell")
def test_sheet_lookup_and_written_content_form_named_sheet_workflow(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Lookup")
    assert workbook.get_worksheet_by_name("Lookup") is sheet
    sheet.write_string("A1", "found")
    data = finish(stream, workbook)
    assert "found" in shared_texts(data)
    assert xml_part(data, "xl/workbook.xml").find("x:sheets/x:sheet", NS).attrib["name"] == "Lookup"


@pytest.mark.depends_on("test_write_internal_url_projects_location_without_external_target", "test_merge_range_projects_merge_cell_ref")
def test_internal_navigation_and_merged_heading_form_local_workflow(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Home")
    sheet.merge_range("A1:B1", "Home")
    sheet.write_url("A2", "internal:Home!A1", None, "Top")
    data = finish(stream, workbook)
    root = xml_part(data, "xl/worksheets/sheet1.xml")
    assert root.find("x:mergeCells/x:mergeCell", NS).attrib["ref"] == "A1:B1"
    assert root.find("x:hyperlinks/x:hyperlink", NS).attrib["location"] == "Home!A1"


@pytest.mark.depends_on("test_public_import_exposes_workbook_and_version", "test_workbook_closes_to_a_zip_stream")
def test_public_workbook_import_and_close_support_repeated_local_runs(workbook_factory):
    results = []
    for name in ("First", "Second"):
        stream, workbook = workbook_factory()
        workbook.add_worksheet(name)
        data = finish(stream, workbook)
        results.append(xml_part(data, "xl/workbook.xml").find("x:sheets/x:sheet", NS).attrib["name"])
    assert results == ["First", "Second"]


@pytest.mark.depends_on("test_set_calc_mode_projects_calculation_policy", "test_set_properties_projects_title_without_asserting_timestamps")
def test_workbook_policy_and_properties_are_present_together(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.set_calc_mode("manual")
    workbook.set_properties({"title": "Policy"})
    workbook.add_worksheet()
    data = finish(stream, workbook)
    assert xml_part(data, "xl/workbook.xml").find("x:calcPr", NS).attrib["calcMode"] == "manual"
    assert xml_part(data, "docProps/core.xml").find("{http://purl.org/dc/elements/1.1/}title").text == "Policy"


@pytest.mark.depends_on("test_write_formula_projects_formula_and_cached_value", "test_add_table_projects_table_part_and_reference")
def test_formula_summary_and_table_detail_are_separate_parts(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_row("A1", ["Item", "Value"])
    sheet.write_row("A2", ["x", 2])
    sheet.write_formula("D1", "=B2*3", None, 6)
    sheet.add_table("A1:B2", {"name": "Details"})
    data = finish(stream, workbook)
    root = xml_part(data, "xl/worksheets/sheet1.xml")
    assert root.find(".//x:c[@r='D1']/x:f", NS).text == "B2*3"
    assert xml_part(data, "xl/tables/table1.xml").attrib["ref"] == "A1:B2"


@pytest.mark.depends_on("test_write_row_projects_mixed_values_across_columns", "test_autofilter_projects_filter_range", "test_freeze_panes_projects_frozen_view")
def test_filterable_frozen_data_sheet_forms_a_multi_view_workflow(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Data")
    sheet.write_row("A1", ["Name", "Score", "Active"])
    sheet.write_row("A2", ["Ada", 10, True])
    sheet.autofilter("A1:C2")
    sheet.freeze_panes(1, 0)
    data = finish(stream, workbook)
    root = xml_part(data, "xl/worksheets/sheet1.xml")
    assert root.find("x:autoFilter", NS).attrib["ref"] == "A1:C2"
    assert root.find("x:sheetViews/x:sheetView/x:pane", NS).attrib["ySplit"] == "1"


@pytest.mark.depends_on("test_write_rich_string_projects_multiple_runs", "test_insert_chart_projects_chart_xml_and_drawing_relationship")
def test_rich_caption_and_chart_form_visual_report_parts(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Report")
    bold = workbook.add_format({"bold": True})
    sheet.write_rich_string("A1", bold, "Report", " detail")
    sheet.write_column("A2", [2, 4, 6])
    chart = workbook.add_chart({"type": "line"})
    chart.add_series({"values": "=Report!$A$2:$A$4"})
    sheet.insert_chart("C2", chart)
    data = finish(stream, workbook)
    assert any("Report" in text for text in shared_texts(data))
    assert xml_part(data, "xl/charts/chart1.xml").find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}lineChart") is not None
