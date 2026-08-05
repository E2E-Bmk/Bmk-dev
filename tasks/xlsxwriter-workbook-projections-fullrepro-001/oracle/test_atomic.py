from __future__ import annotations

from datetime import datetime
from fractions import Fraction
from io import BytesIO
from zipfile import ZipFile

import pytest
import xlsxwriter

from conftest import NS, cells, finish, relationships, shared_texts, xml_part


def test_public_import_exposes_workbook_and_version(workbook_factory):
    assert callable(xlsxwriter.Workbook)
    assert isinstance(xlsxwriter.__version__, str)
    assert xlsxwriter.__VERSION__ == xlsxwriter.__version__


def test_workbook_closes_to_a_zip_stream(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet("Overview")
    data = finish(stream, workbook)
    assert data[:2] == b"PK"
    with ZipFile(BytesIO(data)) as archive:
        assert "xl/workbook.xml" in archive.namelist()


def test_add_worksheet_projects_names_in_workbook_xml(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet("Overview")
    workbook.add_worksheet("Inputs")
    root = xml_part(finish(stream, workbook), "xl/workbook.xml")
    assert [node.attrib["name"] for node in root.findall("x:sheets/x:sheet", NS)] == [
        "Overview",
        "Inputs",
    ]


def test_get_worksheet_by_name_returns_the_public_sheet_object(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet("Inputs")
    assert workbook.get_worksheet_by_name("Inputs") is sheet
    assert workbook.get_worksheet_by_name("Missing") is None
    finish(stream, workbook)


def test_add_format_bold_and_number_format_reach_styles_xml(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    fmt = workbook.add_format({"bold": True, "num_format": "0.00"})
    sheet.write_number("A1", 12.5, fmt)
    root = xml_part(finish(stream, workbook), "xl/styles.xml")
    assert any(node.find("x:b", NS) is not None for node in root.findall("x:fonts/x:font", NS))
    assert any(node.attrib.get("formatCode") == "0.00" for node in root.findall("x:numFmts/x:numFmt", NS))


def test_write_string_projects_shared_string_cell(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    assert sheet.write_string("B2", "alpha") == 0
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    cell = cells(root)["B2"]
    assert cell.attrib["t"] == "s"
    assert shared_texts(stream.getvalue())[int(cell.findtext("x:v", namespaces=NS))] == "alpha"


def test_write_number_projects_numeric_value(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_number("C3", 42.5)
    cell = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))["C3"]
    assert cell.findtext("x:v", namespaces=NS) == "42.5"
    assert "t" not in cell.attrib


def test_write_boolean_projects_boolean_cell_type(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_boolean("D4", True)
    cell = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))["D4"]
    assert cell.attrib["t"] == "b"
    assert cell.findtext("x:v", namespaces=NS) == "1"


def test_write_datetime_projects_excel_serial_and_format(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_datetime(
        "E5", datetime(2020, 1, 2), workbook.add_format({"num_format": "yyyy-mm-dd"})
    )
    cell = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))["E5"]
    assert cell.findtext("x:v", namespaces=NS) == "43832"
    assert int(cell.attrib["s"]) > 0


def test_write_formula_projects_formula_and_cached_value(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_number("A1", 2)
    sheet.write_number("B1", 3)
    sheet.write_formula("C1", "=A1+B1", None, 5)
    cell = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))["C1"]
    assert cell.findtext("x:f", namespaces=NS) == "A1+B1"
    assert cell.findtext("x:v", namespaces=NS) == "5"


def test_write_array_formula_projects_range_reference(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_array_formula("A1:B2", "=ROW(A1:B2)", None, 1)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    formula = cells(root)["A1"].find("x:f", NS)
    assert formula.attrib["t"] == "array"
    assert formula.attrib["ref"] == "A1:B2"


def test_write_dynamic_array_formula_projects_dynamic_marker(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_dynamic_array_formula("A1:B2", "=SEQUENCE(2,2)", None, 1)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    cell = cells(root)["A1"]
    assert cell.attrib["cm"] == "1"
    assert cell.find("x:f", NS).attrib["t"] == "array"


def test_write_rich_string_projects_multiple_runs(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_rich_string(
        "A1",
        workbook.add_format({"bold": True}),
        "bold",
        workbook.add_format({"italic": True}),
        "italic",
    )
    texts = shared_texts(finish(stream, workbook))
    assert "bold" in texts[0] and "italic" in texts[0]


def test_write_row_projects_mixed_values_across_columns(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_row("A1", ["name", 7, True])
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert set(cells(root)) == {"A1", "B1", "C1"}


def test_write_column_projects_values_down_rows(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_column("A1", ["a", "b", "c"])
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert set(cells(root)) == {"A1", "A2", "A3"}


def test_write_blank_with_format_projects_style_only_cell(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_blank("A1", None, workbook.add_format({"bg_color": "#FFFF00"}))
    cell = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))["A1"]
    assert int(cell.attrib["s"]) > 0
    assert cell.find("x:v", NS) is None


def test_set_column_projects_width_and_custom_width(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().set_column("B:D", 18)
    col = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml").find("x:cols/x:col", NS)
    assert col.attrib["min"] == "2"
    assert col.attrib["max"] == "4"
    assert col.attrib["customWidth"] == "1"


def test_set_row_projects_height_and_hidden_state(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().set_row(2, 25, None, {"hidden": True})
    row = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml").find("x:sheetData/x:row", NS)
    assert row.attrib["r"] == "3"
    assert float(row.attrib["ht"]) == 24.75
    assert row.attrib["hidden"] == "1"


def test_freeze_panes_projects_frozen_view(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().freeze_panes(1, 2)
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    pane = root.find("x:sheetViews/x:sheetView/x:pane", NS)
    assert pane.attrib["state"] == "frozen"
    assert pane.attrib["xSplit"] == "2"
    assert pane.attrib["ySplit"] == "1"


def test_merge_range_projects_merge_cell_ref(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().merge_range("B2:D3", "merged")
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find("x:mergeCells/x:mergeCell", NS).attrib["ref"] == "B2:D3"


def test_autofilter_projects_filter_range(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().autofilter("A1:C5")
    root = xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml")
    assert root.find("x:autoFilter", NS).attrib["ref"] == "A1:C5"


def test_define_name_projects_global_and_local_names(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet("Data")
    workbook.add_worksheet("Other")
    workbook.define_name("GlobalTotal", "=Data!$A$1")
    workbook.define_name("Other!LocalTotal", "=Other!$B$2")
    root = xml_part(finish(stream, workbook), "xl/workbook.xml")
    names = root.findall("x:definedNames/x:definedName", NS)
    assert {(n.attrib["name"], n.attrib.get("localSheetId")) for n in names} == {
        ("GlobalTotal", None),
        ("LocalTotal", "1"),
    }


def test_add_table_projects_table_part_and_reference(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_row("A1", ["Item", "Amount"])
    sheet.write_row("A2", ["one", 10])
    sheet.add_table("A1:B2", {"name": "SalesTable", "style": "Table Style Medium 2"})
    data = finish(stream, workbook)
    root = xml_part(data, "xl/tables/table1.xml")
    assert root.attrib["name"] == "SalesTable"
    assert root.attrib["ref"] == "A1:B2"
    assert "xl/tables/table1.xml" in relationships(data, "xl/worksheets/_rels/sheet1.xml.rels")[0]["target"].replace("../", "xl/")


def test_write_external_url_projects_hyperlink_relationship(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_url("A1", "https://example.test/docs", None, "Docs", "tip")
    data = finish(stream, workbook)
    root = xml_part(data, "xl/worksheets/sheet1.xml")
    link = root.find("x:hyperlinks/x:hyperlink", NS)
    rel = relationships(data, "xl/worksheets/_rels/sheet1.xml.rels")[0]
    assert link.attrib["ref"] == "A1"
    assert rel["target"] == "https://example.test/docs"
    assert rel["mode"] == "External"


def test_write_internal_url_projects_location_without_external_target(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet("Data").write_url("A1", "internal:Other!A1", None, "Jump")
    workbook.add_worksheet("Other")
    data = finish(stream, workbook)
    link = xml_part(data, "xl/worksheets/sheet1.xml").find("x:hyperlinks/x:hyperlink", NS)
    assert link.attrib["location"] == "Other!A1"
    assert "{%s}id" % NS["r"] not in link.attrib


def test_write_comment_projects_comment_author_and_cell_ref(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write_comment("C3", "Review this", {"author": "Reviewer"})
    data = finish(stream, workbook)
    root = xml_part(data, "xl/comments1.xml")
    assert root.find("x:authors/x:author", NS).text == "Reviewer"
    assert root.find("x:commentList/x:comment", NS).attrib["ref"] == "C3"


def test_insert_chart_projects_chart_xml_and_drawing_relationship(workbook_factory):
    stream, workbook = workbook_factory()
    sheet = workbook.add_worksheet()
    sheet.write_column("A1", [1, 2, 3])
    chart = workbook.add_chart({"type": "line"})
    chart.add_series({"values": "=Sheet1!$A$1:$A$3"})
    sheet.insert_chart("C2", chart)
    data = finish(stream, workbook)
    chart_root = xml_part(data, "xl/charts/chart1.xml")
    drawing_root = xml_part(data, "xl/drawings/drawing1.xml")
    assert chart_root.find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}lineChart") is not None
    assert drawing_root.find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}chart") is not None


def test_set_properties_projects_title_without_asserting_timestamps(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.set_properties({"title": "Projection Workbook", "author": "Oracle"})
    data = finish(stream, workbook)
    root = xml_part(data, "docProps/core.xml")
    assert root.find("{http://purl.org/dc/elements/1.1/}title").text == "Projection Workbook"
    assert root.find("{http://purl.org/dc/elements/1.1/}creator").text == "Oracle"


def test_set_calc_mode_projects_calculation_policy(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.set_calc_mode("manual")
    root = xml_part(finish(stream, workbook), "xl/workbook.xml")
    assert root.find("x:calcPr", NS).attrib["calcMode"] == "manual"


def test_write_fraction_projects_as_numeric_value(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet().write("A1", Fraction(1, 2))
    cell = cells(xml_part(finish(stream, workbook), "xl/worksheets/sheet1.xml"))["A1"]
    assert cell.findtext("x:v", namespaces=NS) == "0.5"


def test_workbook_projection_has_stable_required_parts(workbook_factory):
    stream, workbook = workbook_factory()
    workbook.add_worksheet("OnlySheet")
    data = finish(stream, workbook)
    with __import__("zipfile").ZipFile(__import__("io").BytesIO(data)) as archive:
        names = set(archive.namelist())
    assert {"[Content_Types].xml", "xl/workbook.xml", "xl/worksheets/sheet1.xml", "xl/styles.xml"} <= names
