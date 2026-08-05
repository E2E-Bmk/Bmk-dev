from __future__ import annotations

from datetime import datetime, timezone

import pytest

from conftest import decoded_pdf, fixed_datetime, make_pdf, page_count, rendered_bytes


def test_default_document_geometry_and_margins():
    pdf = make_pdf()
    assert pdf.page_no() == 0
    assert pdf.pages_count == 0
    assert pdf.w > pdf.h / 2
    assert pdf.l_margin == pytest.approx(10)
    assert pdf.t_margin == pytest.approx(10)
    assert pdf.r_margin == pytest.approx(10)
    assert pdf.b_margin == pytest.approx(20)
    assert pdf.epw == pytest.approx(pdf.w - 20)


def test_custom_unit_and_format_geometry():
    pdf = make_pdf(unit="pt", format=(200, 100))
    assert pdf.w == pytest.approx(200)
    assert pdf.h == pytest.approx(100)
    assert pdf.k == pytest.approx(1)
    assert pdf.default_page_dimensions == pytest.approx((200, 100))


def test_orientation_changes_page_dimensions():
    pdf = make_pdf(orientation="landscape", format=(148, 210))
    assert pdf.w > pdf.h
    pdf.add_page()
    assert pdf.cur_orientation.value == "L"
    assert pdf.w_pt > pdf.h_pt


def test_add_page_initializes_page_and_position():
    pdf = make_pdf()
    pdf.add_page()
    assert pdf.page_no() == 1
    assert pdf.pages_count == 1
    assert pdf.x == pytest.approx(pdf.l_margin)
    assert pdf.y == pytest.approx(pdf.t_margin)
    assert 1 in pdf.pages


def test_multiple_pages_track_count_and_page_no():
    pdf = make_pdf()
    pdf.add_page()
    pdf.add_page(orientation="landscape")
    assert pdf.page_no() == 2
    assert pdf.pages_count == 2
    assert pdf.cur_orientation.value == "L"


def test_set_margins_updates_effective_area_and_position():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_margins(15, 18, 12)
    assert pdf.l_margin == pytest.approx(15)
    assert pdf.t_margin == pytest.approx(18)
    assert pdf.r_margin == pytest.approx(12)
    assert pdf.x == pytest.approx(15)
    assert pdf.y == pytest.approx(18)
    assert pdf.epw == pytest.approx(pdf.w - 27)


def test_set_individual_margins_updates_state():
    pdf = make_pdf()
    pdf.set_left_margin(14)
    pdf.set_top_margin(16)
    pdf.set_right_margin(11)
    pdf.set_auto_page_break(False, 7)
    assert (pdf.l_margin, pdf.t_margin, pdf.r_margin) == pytest.approx((14, 16, 11))
    assert pdf.auto_page_break is False
    assert pdf.b_margin == pytest.approx(7)
    assert pdf.page_break_trigger == pytest.approx(pdf.h - 7)


def test_auto_page_break_controls_trigger():
    pdf = make_pdf(format=(100, 100))
    pdf.add_page()
    pdf.set_auto_page_break(True, 10)
    assert pdf.will_page_break(5) is False
    pdf.set_y(85)
    assert pdf.will_page_break(10) is True
    pdf.set_auto_page_break(False)
    assert pdf.will_page_break(50) is False


def test_set_xy_and_ln_update_coordinates():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_xy(25, 30)
    assert (pdf.x, pdf.y) == pytest.approx((25, 30))
    pdf.set_font("helvetica", size=10)
    pdf.ln(7)
    assert pdf.y == pytest.approx(37)
    assert pdf.x == pytest.approx(pdf.l_margin)


def test_set_font_selects_builtin_font_and_size():
    pdf = make_pdf()
    pdf.set_font("times", style="BI", size=14)
    assert pdf.font_family == "times"
    assert pdf.font_style == "BI"
    assert pdf.font_size_pt == pytest.approx(14)
    assert pdf.font_size == pytest.approx(14 / 72 * 25.4)


def test_builtin_font_name_is_case_insensitive():
    pdf = make_pdf()
    pdf.set_font("Helvetica", size=11)
    assert pdf.font_family == "helvetica"
    assert pdf.current_font is not None
    assert pdf.get_string_width("alias") > 0


def test_string_width_is_positive_and_size_sensitive():
    pdf = make_pdf()
    pdf.set_font("helvetica", size=10)
    small = pdf.get_string_width("layout")
    pdf.set_font_size(20)
    large = pdf.get_string_width("layout")
    assert small > 0
    assert large == pytest.approx(small * 2)


def test_text_emits_literal_content():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.text(20, 30, "Anchor")
    data = rendered_bytes(pdf)
    assert b"(Anchor) Tj" in data


def test_cell_moves_to_requested_coordinates():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    start = (pdf.x, pdf.y)
    pdf.cell(25, 8, "Cell", new_x="RIGHT", new_y="TOP")
    assert pdf.x == pytest.approx(start[0] + 25)
    assert pdf.y == pytest.approx(start[1])
    pdf.cell(25, 8, "Next", new_x="LMARGIN", new_y="NEXT")
    assert pdf.x == pytest.approx(pdf.l_margin)
    assert pdf.y == pytest.approx(start[1] + 8)


def test_cell_border_and_fill_emit_drawing_commands():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(30, 10, "Box", border=1, fill=True)
    text = decoded_pdf(rendered_bytes(pdf))
    assert " re " in text
    assert " B" in text or " f" in text


def test_multi_cell_wraps_and_returns_to_margin():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(25, 5, "one two three", border=1)
    assert pdf.x == pytest.approx(pdf.l_margin + 25)
    assert pdf.y > pdf.t_margin
    assert page_count(rendered_bytes(pdf)) == 1


def test_multi_cell_dry_run_reports_lines_without_writing():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    before = (pdf.x, pdf.y, pdf.pages_count)
    lines = pdf.multi_cell(20, 5, "one two three", dry_run=True, output="LINES")
    assert lines == ["one two", "three"]
    assert (pdf.x, pdf.y, pdf.pages_count) == before


def test_multi_cell_new_x_new_y_controls_position():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.set_xy(20, 30)
    pdf.multi_cell(30, 5, "wrapped", new_x="RIGHT", new_y="TOP")
    assert pdf.x == pytest.approx(50)
    assert pdf.y == pytest.approx(30)


def test_write_advances_vertical_position():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    start = pdf.y
    pdf.write(5, "A short paragraph.")
    assert pdf.y == pytest.approx(start)
    pdf.write(5, "Second line\n")
    assert pdf.y > start


def test_line_and_rect_emit_path_operators():
    pdf = make_pdf()
    pdf.add_page()
    pdf.line(10, 20, 40, 20)
    pdf.rect(10, 25, 30, 12)
    text = decoded_pdf(rendered_bytes(pdf))
    assert " m " in text and " l S" in text
    assert " re " in text


def test_color_setters_change_graphics_state():
    pdf = make_pdf()
    pdf.set_draw_color(255, 0, 0)
    pdf.set_fill_color(0, 255, 0)
    pdf.set_text_color(0, 0, 255)
    assert (pdf.draw_color.r, pdf.draw_color.g, pdf.draw_color.b) == pytest.approx(
        (1, 0, 0)
    )
    assert (pdf.fill_color.r, pdf.fill_color.g, pdf.fill_color.b) == pytest.approx(
        (0, 1, 0)
    )
    assert (pdf.text_color.r, pdf.text_color.g, pdf.text_color.b) == pytest.approx(
        (0, 0, 1)
    )


def test_external_link_adds_annotation():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(35, 8, "Visit", link="https://example.test")
    data = rendered_bytes(pdf)
    assert data.count(b"/Subtype /Link") == 1
    assert b"/S /URI" in data
    assert b"https://example.test" in data


def test_link_method_accepts_alt_text():
    pdf = make_pdf()
    pdf.add_page()
    annotation = pdf.link(10, 20, 30, 8, "https://example.test", alt_text="More")
    assert annotation is not None
    data = rendered_bytes(pdf)
    assert b"/Subtype /Link" in data
    assert b"More" in data


def test_internal_link_targets_page():
    pdf = make_pdf()
    pdf.add_page()
    target = pdf.add_link(page=1)
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(30, 8, "Back", link=target)
    data = rendered_bytes(pdf)
    assert data.count(b"/Subtype /Link") == 1
    assert b"/Dest [3 0 R" in data


def test_named_destination_can_be_referenced():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_link(name="chapter")
    assert pdf.get_named_destination("chapter") == "#chapter"
    pdf.set_font("helvetica", size=10)
    pdf.cell(35, 8, "Chapter", link="#chapter")
    data = rendered_bytes(pdf)
    assert b"/Dest (chapter)" in data


def test_metadata_fields_appear_in_info_dictionary():
    pdf = make_pdf()
    pdf.set_title("Layout Report")
    pdf.set_subject("Document geometry")
    pdf.set_author("Ada Lovelace")
    pdf.set_keywords("pdf layout")
    pdf.set_creator("oracle")
    pdf.set_producer("producer")
    pdf.set_lang("en-US")
    data = rendered_bytes(pdf)
    text = decoded_pdf(data)
    for marker in (
        "/Title (Layout Report)",
        "/Subject (Document geometry)",
        "/Author (Ada Lovelace)",
        "/Keywords (pdf layout)",
        "/Creator (oracle)",
        "/Producer (producer)",
        "/Lang (en-US)",
    ):
        assert marker in text


def test_creation_date_can_be_set_deterministically():
    pdf = make_pdf()
    pdf.set_creation_date(fixed_datetime())
    data = decoded_pdf(rendered_bytes(pdf))
    assert "/CreationDate (D:20240102030405Z)" in data


def test_alias_nb_pages_is_substituted_on_output():
    pdf = make_pdf()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(text="Page {nb}")
    pdf.add_page()
    pdf.cell(text="Page {nb}")
    data = rendered_bytes(pdf)
    assert b"(Page ) Tj" in data
    assert b"(2) Tj" in data
    assert b"{nb}" not in data


def test_start_section_records_outline():
    pdf = make_pdf()
    pdf.add_page()
    pdf.start_section("Introduction")
    pdf.start_section("Details", level=1)
    data = decoded_pdf(rendered_bytes(pdf))
    assert "/Outlines" in data
    assert "/Title (Introduction)" in data
    assert "/Title (Details)" in data


def test_invalid_outline_level_raises_value_error():
    pdf = make_pdf()
    pdf.add_page()
    pdf.start_section("Top")
    with pytest.raises(ValueError):
        pdf.start_section("Too deep", level=3)


def test_table_context_renders_rows_and_headers():
    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    with pdf.table() as table:
        for values in (("Name", "Value"), ("Ada", "10")):
            row = table.row()
            for value in values:
                row.cell(value)
    data = rendered_bytes(pdf)
    assert b"(Name) Tj" in data
    assert b"(Ada) Tj" in data
    assert data.count(b" re S") >= 4


def test_fontface_context_changes_and_restores_font():
    from fpdf import FontFace

    pdf = make_pdf()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    before = (pdf.font_family, pdf.font_style, pdf.font_size_pt)
    with pdf.use_font_face(FontFace(emphasis="BOLD", size_pt=16)):
        assert (pdf.font_family, pdf.font_style, pdf.font_size_pt) == (
            "helvetica",
            "B",
            16,
        )
        pdf.cell(text="Styled")
    assert (pdf.font_family, pdf.font_style, pdf.font_size_pt) == before
