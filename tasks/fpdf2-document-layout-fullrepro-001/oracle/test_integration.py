from __future__ import annotations

import pytest

from conftest import decoded_pdf, fixed_datetime, make_pdf, page_count, rendered_bytes


@pytest.mark.depends_on(
    "test_set_margins_updates_effective_area_and_position",
    "test_set_font_selects_builtin_font_and_size",
    "test_cell_moves_to_requested_coordinates",
)
def test_margin_font_cell_workflow_emits_one_page():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_margins(15, 18, 12)
    pdf.set_font("times", style="B", size=13)
    pdf.cell(pdf.epw, 9, "Invoice", border=1, align="C")
    data = rendered_bytes(pdf)
    assert page_count(data) == 1
    assert b"(Invoice) Tj" in data
    assert pdf.x == pytest.approx(pdf.l_margin + pdf.epw)


@pytest.mark.depends_on(
    "test_orientation_changes_page_dimensions",
    "test_multiple_pages_track_count_and_page_no",
)
def test_mixed_orientation_pages_preserve_page_inventory():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(text="Portrait")
    pdf.add_page(orientation="landscape")
    pdf.cell(text="Landscape")
    data = rendered_bytes(pdf)
    assert page_count(data) == 2
    assert b"(Portrait) Tj" in data
    assert b"(Landscape) Tj" in data


@pytest.mark.depends_on(
    "test_set_xy_and_ln_update_coordinates",
    "test_text_emits_literal_content",
    "test_line_and_rect_emit_path_operators",
)
def test_precise_drawing_workflow_contains_text_and_shapes():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.set_xy(22, 28)
    pdf.text(pdf.x, pdf.y + 6, "Coordinate")
    pdf.ln(12)
    pdf.line(22, pdf.y, 70, pdf.y)
    pdf.rect(22, pdf.y + 4, 35, 14)
    data = decoded_pdf(rendered_bytes(pdf))
    assert "(Coordinate) Tj" in data
    assert " m " in data and " re " in data


@pytest.mark.depends_on(
    "test_auto_page_break_controls_trigger",
    "test_multi_cell_wraps_and_returns_to_margin",
)
def test_wrapped_content_workflow_triggers_predictable_page_break():
    pdf = make_pdf(format=(80, 80))
    pdf.add_page()
    pdf.set_font("helvetica", size=9)
    pdf.set_auto_page_break(True, 8)
    pdf.set_y(55)
    pdf.multi_cell(pdf.epw, 7, "first block\nsecond block\nthird block")
    pdf.multi_cell(pdf.epw, 7, "continued block\nfinal block")
    data = rendered_bytes(pdf)
    assert page_count(data) >= 2
    assert b"(continued block) Tj" in data


@pytest.mark.depends_on(
    "test_set_font_selects_builtin_font_and_size",
    "test_write_advances_vertical_position",
    "test_string_width_is_positive_and_size_sensitive",
)
def test_write_workflow_uses_font_metrics_and_preserves_content():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("courier", size=12)
    width = pdf.get_string_width("fixed")
    pdf.write(6, "fixed width text ")
    pdf.write(6, "continues\n")
    pdf.write(6, "new line")
    data = rendered_bytes(pdf)
    assert width > 0
    assert b"(fixed width text ) Tj" in data
    assert b"(new line) Tj" in data


@pytest.mark.depends_on(
    "test_multi_cell_dry_run_reports_lines_without_writing",
    "test_multi_cell_new_x_new_y_controls_position",
)
def test_dry_run_then_render_workflow_matches_planned_lines():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    lines = pdf.multi_cell(25, 5, "one two three", dry_run=True, output="LINES")
    pdf.multi_cell(25, 5, "\n".join(lines), border=1)
    data = rendered_bytes(pdf)
    assert all(f"({line}) Tj".encode() in data for line in lines)
    assert pdf.x == pytest.approx(pdf.l_margin + 25)


@pytest.mark.depends_on(
    "test_cell_border_and_fill_emit_drawing_commands",
    "test_color_setters_change_graphics_state",
)
def test_colored_filled_cell_workflow_keeps_stable_geometry():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.set_draw_color(20, 40, 60)
    pdf.set_fill_color(220, 230, 240)
    pdf.cell(50, 12, "Status", border=1, fill=True)
    pdf.cell(30, 12, "OK", border="LTRB", fill=True)
    data = decoded_pdf(rendered_bytes(pdf))
    assert data.count(" re ") >= 2
    assert " rg" in data or " scn" in data


@pytest.mark.depends_on(
    "test_external_link_adds_annotation",
    "test_link_method_accepts_alt_text",
)
def test_external_link_workflow_combines_text_and_rectangle_annotations():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(35, 8, "Website", link="https://example.test")
    pdf.link(50, 10, 30, 8, "https://example.test/docs", alt_text="Docs")
    data = rendered_bytes(pdf)
    assert data.count(b"/Subtype /Link") == 2
    assert data.count(b"/S /URI") == 2
    assert b"Docs" in data


@pytest.mark.depends_on(
    "test_internal_link_targets_page",
    "test_multiple_pages_track_count_and_page_no",
)
def test_internal_link_workflow_jumps_from_summary_to_detail():
    pdf = make_pdf()
    pdf.add_page()
    target = pdf.add_link(page=2)
    pdf.set_font("helvetica", size=10)
    pdf.cell(40, 8, "Summary", link=target)
    pdf.add_page()
    pdf.cell(text="Detail")
    data = rendered_bytes(pdf)
    assert page_count(data) == 2
    assert b"/Dest [" in data
    assert b"/XYZ" in data
    assert b"(Detail) Tj" in data


@pytest.mark.depends_on(
    "test_named_destination_can_be_referenced",
    "test_set_xy_and_ln_update_coordinates",
)
def test_named_destination_workflow_links_labeled_sections():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.set_link(name="details")
    pdf.cell(45, 8, "Jump", link="#details")
    pdf.ln(12)
    pdf.cell(text="Details")
    data = rendered_bytes(pdf)
    assert b"/Dest (details)" in data
    assert b"(Details) Tj" in data


@pytest.mark.depends_on(
    "test_metadata_fields_appear_in_info_dictionary",
    "test_creation_date_can_be_set_deterministically",
)
def test_metadata_workflow_emits_stable_information_dictionary():
    pdf = make_pdf()
    pdf.set_title("Quarterly Layout")
    pdf.set_subject("Coordinates")
    pdf.set_author(("Ada", "Ben"))
    pdf.set_keywords(("pdf", "layout"))
    pdf.set_creator("workflow")
    pdf.set_creation_date(fixed_datetime())
    data = decoded_pdf(rendered_bytes(pdf))
    assert "/Title (Quarterly Layout)" in data
    assert "/Subject (Coordinates)" in data
    assert "/CreationDate (D:20240102030405Z)" in data
    assert "/Creator (workflow)" in data


@pytest.mark.depends_on(
    "test_alias_nb_pages_is_substituted_on_output",
    "test_multiple_pages_track_count_and_page_no",
)
def test_page_alias_workflow_reports_final_page_count():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(text="Sheet {nb}")
    pdf.add_page()
    pdf.cell(text="Sheet {nb}")
    pdf.add_page()
    pdf.cell(text="Sheet {nb}")
    data = rendered_bytes(pdf)
    assert page_count(data) == 3
    assert data.count(b"(Sheet ) Tj") == 3
    assert data.count(b"(3) Tj") == 3
    assert b"{nb}" not in data


@pytest.mark.depends_on(
    "test_start_section_records_outline",
    "test_invalid_outline_level_raises_value_error",
)
def test_outline_workflow_emits_nested_bookmark_titles():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.start_section("Chapter")
    pdf.start_section("Section", level=1)
    pdf.cell(text="Body")
    data = decoded_pdf(rendered_bytes(pdf))
    assert "/Outlines" in data
    assert "/Title (Chapter)" in data
    assert "/Title (Section)" in data
    assert b"(Body) Tj" in data.encode("latin-1")


@pytest.mark.depends_on(
    "test_start_section_records_outline",
    "test_fontface_context_changes_and_restores_font",
)
def test_styled_heading_workflow_renders_outline_and_visible_heading():
    from fpdf import TextStyle

    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.set_section_title_styles(TextStyle(font_size_pt=16, font_style="B"))
    pdf.start_section("Styled heading")
    data = decoded_pdf(rendered_bytes(pdf))
    assert "/Title (Styled heading)" in data
    assert "(Styled heading) Tj" in data
    assert "/Helvetica-Bold" in data


@pytest.mark.depends_on(
    "test_table_context_renders_rows_and_headers",
    "test_cell_border_and_fill_emit_drawing_commands",
)
def test_table_workflow_renders_headers_rows_and_borders():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    with pdf.table(col_widths=(1, 2), text_align=("LEFT", "RIGHT")) as table:
        for values in (("Name", "Value"), ("Ada", "10"), ("Ben", "20")):
            row = table.row()
            for value in values:
                row.cell(value)
    data = decoded_pdf(rendered_bytes(pdf))
    assert all(f"({value}) Tj" in data for value in ("Name", "Value", "Ada", "10", "Ben", "20"))
    assert data.count(" re S") >= 6


@pytest.mark.depends_on(
    "test_multi_cell_wraps_and_returns_to_margin",
    "test_table_context_renders_rows_and_headers",
)
def test_multiline_table_workflow_preserves_wrapped_cell_content():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=9)
    with pdf.table(width=90, col_widths=(1, 1)) as table:
        row = table.row()
        row.cell("Header")
        row.cell("Description")
        row = table.row()
        row.cell("A")
        row.cell("long description that wraps")
    data = decoded_pdf(rendered_bytes(pdf))
    assert "(Header) Tj" in data
    assert "(Description) Tj" in data
    assert "(long description that wraps) Tj" in data or "(long description" in data


@pytest.mark.depends_on(
    "test_auto_page_break_controls_trigger",
    "test_table_context_renders_rows_and_headers",
)
def test_long_table_workflow_can_span_pages_without_losing_rows():
    pdf = make_pdf(format=(80, 90))
    pdf.add_page()
    pdf.set_font("helvetica", size=8)
    with pdf.table(width=pdf.epw, repeat_headings=1) as table:
        for index in range(12):
            row = table.row()
            row.cell("Header" if index == 0 else f"Row {index}")
            row.cell("Value")
    data = rendered_bytes(pdf)
    assert page_count(data) >= 2
    assert b"(Row 11) Tj" in data


@pytest.mark.depends_on(
    "test_write_advances_vertical_position",
    "test_alias_nb_pages_is_substituted_on_output",
)
def test_wrapping_write_workflow_finishes_with_page_alias():
    pdf = make_pdf(format=(90, 100))
    pdf.add_page()
    pdf.set_font("helvetica", size=9)
    pdf.set_y(70)
    pdf.write(5, "A long paragraph " * 100)
    pdf.write(5, "\nEnd on page {nb}")
    data = rendered_bytes(pdf)
    assert page_count(data) >= 2
    assert b"End on page " in data
    assert b"{nb}" not in data


@pytest.mark.depends_on(
    "test_cell_moves_to_requested_coordinates",
    "test_external_link_adds_annotation",
)
def test_linked_cell_sequence_keeps_content_order_and_annotation():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(30, 8, "First")
    pdf.cell(30, 8, "Second", link="https://example.test")
    pdf.cell(30, 8, "Third")
    data = rendered_bytes(pdf)
    assert data.index(b"(First) Tj") < data.index(b"(Second) Tj") < data.index(b"(Third) Tj")
    assert data.count(b"/Subtype /Link") == 1


@pytest.mark.depends_on(
    "test_add_page_initializes_page_and_position",
    "test_text_emits_literal_content",
)
def test_output_workflow_closes_buffer_and_preserves_page_count():
    from fpdf import FPDFException

    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.text(15, 20, "Closed")
    data = rendered_bytes(pdf)
    assert pdf.buffer is not None
    assert pdf.page_no() == 1
    assert b"(Closed) Tj" in data
    with pytest.raises(FPDFException):
        pdf.add_page()


@pytest.mark.depends_on(
    "test_set_margins_updates_effective_area_and_position",
    "test_multi_cell_new_x_new_y_controls_position",
)
def test_margin_reset_workflow_repositions_wrapped_content():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_margins(20, 22, 18)
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(pdf.epw, 6, "Aligned block", new_x="LMARGIN", new_y="NEXT")
    assert pdf.x == pytest.approx(20)
    assert pdf.y > 22
    data = rendered_bytes(pdf)
    assert b"(Aligned block) Tj" in data


@pytest.mark.depends_on(
    "test_color_setters_change_graphics_state",
    "test_line_and_rect_emit_path_operators",
)
def test_drawing_style_workflow_combines_colors_lines_and_rectangles():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_draw_color(0, 80, 160)
    pdf.set_fill_color(240, 240, 240)
    pdf.line(15, 30, 75, 30)
    pdf.rect(15, 35, 60, 20, style="DF")
    data = decoded_pdf(rendered_bytes(pdf))
    assert " m " in data
    assert " re " in data
    assert " B" in data or " B*" in data


@pytest.mark.depends_on(
    "test_metadata_fields_appear_in_info_dictionary",
    "test_start_section_records_outline",
    "test_table_context_renders_rows_and_headers",
    "test_external_link_adds_annotation",
)
def test_report_workflow_combines_metadata_outline_table_and_link():
    pdf = make_pdf()
    pdf.set_title("Operations Report")
    pdf.set_author("Analyst")
    pdf.set_creation_date(fixed_datetime())
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.start_section("Summary")
    pdf.cell(45, 8, "Source", link="https://example.test")
    with pdf.table() as table:
        for values in (("Metric", "Value"), ("Rows", "4")):
            row = table.row()
            for value in values:
                row.cell(value)
    data = decoded_pdf(rendered_bytes(pdf))
    assert "/Title (Operations Report)" in data
    assert "/Title (Summary)" in data
    assert "/Subtype /Link" in data
    assert "(Metric) Tj" in data and "(Rows) Tj" in data
    assert "/CreationDate (D:20240102030405Z)" in data


@pytest.mark.depends_on(
    "test_custom_unit_and_format_geometry",
    "test_multi_cell_dry_run_reports_lines_without_writing",
)
def test_custom_page_workflow_uses_geometry_for_wrapping():
    pdf = make_pdf(unit="pt", format=(120, 160))
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    lines = pdf.multi_cell(50, 12, "alpha beta gamma", dry_run=True, output="LINES")
    pdf.multi_cell(50, 12, "\n".join(lines), border="LTRB")
    data = rendered_bytes(pdf)
    assert len(lines) >= 2
    assert page_count(data) == 1
    assert all(f"({line}) Tj".encode() in data for line in lines)


@pytest.mark.depends_on(
    "test_invalid_outline_level_raises_value_error",
    "test_start_section_records_outline",
)
def test_outline_recovery_workflow_rejects_gap_then_continues():
    pdf = make_pdf()
    pdf.add_page()
    pdf.start_section("Root")
    with pytest.raises(ValueError):
        pdf.start_section("Gap", level=3)
    pdf.start_section("Child", level=1)
    data = rendered_bytes(pdf)
    assert b"/Title (Root)" in data
    assert b"/Title (Child)" in data
    assert b"/Title (Gap)" not in data


@pytest.mark.depends_on(
    "test_builtin_font_name_is_case_insensitive",
    "test_fontface_context_changes_and_restores_font",
)
def test_font_context_workflow_switches_builtin_styles_and_restores():
    from fpdf import FontFace

    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(text="Base")
    with pdf.use_font_face(FontFace(emphasis="ITALICS", size_pt=14)):
        pdf.cell(text="Emphasis")
    pdf.cell(text="Restored")
    data = decoded_pdf(rendered_bytes(pdf))
    assert "(Base) Tj" in data
    assert "(Emphasis) Tj" in data
    assert "(Restored) Tj" in data
    assert "/Helvetica-Oblique" in data


@pytest.mark.depends_on(
    "test_multiple_pages_track_count_and_page_no",
    "test_add_page_initializes_page_and_position",
    "test_text_emits_literal_content",
)
def test_page_state_workflow_outputs_each_page_content():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(text="One")
    pdf.add_page()
    pdf.cell(text="Two")
    pdf.add_page()
    pdf.cell(text="Three")
    data = rendered_bytes(pdf)
    assert page_count(data) == 3
    assert all(token in data for token in (b"(One) Tj", b"(Two) Tj", b"(Three) Tj"))


@pytest.mark.depends_on(
    "test_creation_date_can_be_set_deterministically",
    "test_external_link_adds_annotation",
    "test_alias_nb_pages_is_substituted_on_output",
)
def test_linked_dated_document_workflow_combines_page_and_info_views():
    pdf = make_pdf()
    pdf.set_creation_date(fixed_datetime())
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(text="Index", link="https://example.test")
    pdf.add_page()
    pdf.cell(text="Page {nb}")
    data = decoded_pdf(rendered_bytes(pdf))
    assert page_count(data.encode("latin-1")) == 2
    assert "/CreationDate (D:20240102030405Z)" in data
    assert "/Subtype /Link" in data
    assert "(2) Tj" in data
