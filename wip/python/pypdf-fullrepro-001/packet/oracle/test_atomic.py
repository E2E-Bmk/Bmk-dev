# Spec2Repo oracle tests for pypdf-fullrepro-001

from io import BytesIO

import pytest

from pypdf import PageObject, PageRange, PaperSize, PdfReader, PdfWriter, Transformation, mult, parse_filename_page_ranges
from pypdf.actions import JavaScript, PageTrigger
from pypdf.annotations import FreeText, Link, PolyLine, Rectangle, Text
from pypdf.constants import UserAccessPermissions
from pypdf.errors import EmptyFileError, PageSizeNotDefinedError, ParseError
from pypdf.generic import (
    DecodedStreamObject,
    Destination,
    Fit,
    NameObject,
    NumberObject,
    RectangleObject,
    create_string_object,
    hex_to_rgb,
)


def _roundtrip(writer: PdfWriter) -> PdfReader:
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return PdfReader(buffer)


def test_pagerange_string_inputs_normalize_to_slices():
    """Verifies: PYPDF-SUP-001."""
    assert PageRange("42").to_slice() == slice(42, 43)
    assert PageRange("1:5").to_slice() == slice(1, 5)
    assert PageRange("1:5:2").to_slice() == slice(1, 5, 2)


def test_pagerange_invalid_syntax_is_rejected():
    """Verifies: PYPDF-SUP-002."""
    assert PageRange.valid("1-5") is False
    with pytest.raises(ParseError):
        PageRange("1-5")


def test_parse_filename_page_ranges_assigns_default_all_pages():
    """Verifies: PYPDF-SUP-001, PYPDF-SUP-008, PYPDF-SUP-009."""
    parsed = parse_filename_page_ranges(["first.pdf", "1:3", "second.pdf"])
    assert parsed == [("first.pdf", PageRange("1:3")), ("second.pdf", PageRange(":"))]


def test_parse_filename_page_ranges_rejects_leading_range():
    """Verifies: PYPDF-SUP-010."""
    with pytest.raises(ValueError):
        parse_filename_page_ranges(["1:3", "first.pdf"])


def test_user_access_permissions_roundtrip_named_flags():
    """Verifies: PYPDF-WRITE-016."""
    data = {
        "add_or_modify": True,
        "assemble_doc": False,
        "extract": False,
        "extract_text_and_graphics": True,
        "fill_form_fields": False,
        "modify": True,
        "print": False,
        "print_to_representation": True,
    }
    assert UserAccessPermissions.from_dict(data).to_dict() == data


def test_user_access_permissions_rejects_unknown_names():
    """Verifies: PYPDF-WRITE-017."""
    with pytest.raises(ValueError):
        UserAccessPermissions.from_dict({"print": True, "not_a_permission": True})


def test_papersize_a4_exposes_positive_dimensions():
    """Verifies: PYPDF-SUP-014."""
    assert PaperSize.A4.width > 0
    assert PaperSize.A4.height > PaperSize.A4.width


def test_blank_page_without_known_size_raises():
    """Verifies: PYPDF-WRITE-003."""
    writer = PdfWriter()
    with pytest.raises(PageSizeNotDefinedError):
        writer.add_blank_page()


def test_encrypt_rejects_unknown_algorithm():
    """Verifies: PYPDF-WRITE-011."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with pytest.raises(ValueError):
        writer.encrypt("secret", algorithm="unknown")


def test_rectangle_object_coordinates_are_mutable():
    """Verifies: PYPDF-PAGE-001."""
    rect = RectangleObject((0, 0, 100, 200))
    rect.upper_right = (150, 250)
    rect.lower_left = (10, 20)
    assert rect.left == 10
    assert rect.bottom == 20
    assert rect.right == 150
    assert rect.top == 250


def test_page_rotate_accepts_right_angles_and_rejects_other_angles():
    """Verifies: PYPDF-PAGE-002."""
    page = PageObject.create_blank_page(width=100, height=200)
    assert page.rotate(90) is page
    assert page.rotation == 90
    with pytest.raises(ValueError):
        page.rotate(45)


def test_transformation_translate_scale_and_apply_on_point():
    """Verifies: PYPDF-PAGE-003."""
    transformed = Transformation().scale(2).translate(tx=10, ty=5)
    assert transformed.apply_on((3, 4)) == (16, 13)


def test_page_scale_by_updates_page_box():
    """Verifies: PYPDF-PAGE-003, PYPDF-INV-002."""
    page = PageObject.create_blank_page(width=200, height=100)
    page.scale_by(0.5)
    assert page.mediabox.width == 100
    assert page.mediabox.height == 50


def test_annotation_dictionaries_expose_expected_public_entries():
    """Verifies: PYPDF-FEAT-008, PYPDF-FEAT-010."""
    text = Text(rect=(0, 0, 100, 100), text="hello", open=True)
    assert text["/Subtype"] == "/Text"
    assert text["/Contents"] == "hello"
    assert text["/Open"] == True

    link = Link(rect=(0, 0, 100, 100), url="https://example.com")
    assert link["/Subtype"] == "/Link"
    assert link["/A"]["/URI"] == "https://example.com"


def test_polyline_rejects_empty_vertices():
    """Verifies: PYPDF-FEAT-012."""
    with pytest.raises(ValueError):
        PolyLine(vertices=[])


def test_free_text_font_style_entry_reflects_constructor_options():
    """Verifies: PYPDF-FEAT-011."""
    annotation = FreeText(
        text="Hello",
        rect=(0, 0, 100, 100),
        font="Arial",
        bold=True,
        italic=True,
        font_size="20pt",
        font_color="00ff00",
    )
    assert annotation["/Subtype"] == "/FreeText"
    assert "italic bold 20pt Arial" in annotation["/DS"]
    assert "#00ff00" in annotation["/DS"]


def test_content_stream_data_roundtrip_on_decoded_stream():
    """Verifies: PYPDF-SUP-003."""
    stream = DecodedStreamObject()
    stream.set_data(b"abc")
    assert stream.get_data() == b"abc"


def test_destination_exposes_title_page_and_fit_fields():
    """Verifies: PYPDF-SUP-011."""
    page_ref = NumberObject(0)
    destination = Destination("Intro", page_ref, Fit.xyz(left=1, top=2, zoom=3))
    assert destination.title == "Intro"
    assert destination.page == page_ref
    assert destination.left == 1
    assert destination.top == 2
    assert destination.zoom == 3


def test_hex_to_rgb_normalizes_channels():
    """Verifies: PYPDF-SUP-007."""
    assert hex_to_rgb("#ff8000") == (1.0, 128 / 255, 0.0)


def test_javascript_action_can_be_added_to_page_trigger():
    """Verifies: PYPDF-FEAT-009, PYPDF-FEAT-013."""
    from pypdf.actions import JavaScript, PageTrigger

    page = PageObject.create_blank_page(width=100, height=100)
    page.add_action(PageTrigger.OPEN, JavaScript("app.alert('opened');"))
    assert page["/AA"]["/O"]["/S"] == "/JavaScript"
    assert page["/AA"]["/O"]["/JS"] == "app.alert('opened');"


def test_generated_pagerange_negative_single_page_indices():
    """Verifies: PYPDF-SUP-001."""
    assert PageRange("-1").to_slice() == slice(-1, None)
    assert PageRange("-1").indices(10) == (9, 10, 1)


def test_generated_pagerange_reverse_all_indices():
    """Verifies: PYPDF-SUP-001."""
    assert PageRange("::-1").indices(4) == (3, -1, -1)


def test_generated_pagerange_empty_string_is_invalid():
    """Verifies: PYPDF-SUP-002."""
    assert PageRange.valid("") is False
    with pytest.raises(ParseError):
        PageRange("")


def test_generated_transformation_matrix_for_translate_and_scale():
    """Verifies: PYPDF-PAGE-003."""
    assert Transformation().translate(2, 3).matrix == ((1, 0, 0), (0, 1, 0), (2, 3, 1))
    assert Transformation().scale(2, 3).matrix == ((2.0, 0.0, 0), (0.0, 3.0, 0), (0.0, 0.0, 1))


def test_generated_matrix_multiplication_combines_translation():
    """Verifies: PYPDF-PAGE-003."""
    assert mult([1, 0, 0, 1, 2, 3], [1, 0, 0, 1, 4, 5]) == [1, 0, 0, 1, 6, 8]


def test_generated_zero_permissions_verbose_mapping_is_all_false():
    """Verifies: PYPDF-WRITE-008."""
    assert UserAccessPermissions(0).to_dict() == {
        "print": False,
        "modify": False,
        "extract": False,
        "add_or_modify": False,
        "fill_form_fields": False,
        "extract_text_and_graphics": False,
        "assemble_doc": False,
        "print_to_representation": False,
    }


def test_generated_create_string_object_text_and_bytes_types():
    """Verifies: PYPDF-SUP-003, PYPDF-SUP-013."""
    assert create_string_object("hello") == "hello"
    assert create_string_object(b"abc").original_bytes == b"abc"


def test_generated_decoded_stream_stores_replaced_bytes():
    """Verifies: PYPDF-SUP-003."""
    stream = DecodedStreamObject()
    stream.set_data(b"first")
    stream.set_data(b"second")
    assert stream.get_data() == b"second"


def test_generated_destination_fit_horizontally_exposes_top():
    """Verifies: PYPDF-SUP-011, PYPDF-SUP-012."""
    dest = Destination("Heading", NumberObject(0), Fit.fit_horizontally(top=144))
    assert dest.title == "Heading"
    assert dest.top == 144
    assert dest.typ == "/FitH"


def test_generated_reader_empty_stream_raises_empty_file_error():
    """Verifies: PYPDF-READ-002, PYPDF-ERR-001."""
    with pytest.raises(EmptyFileError):
        PdfReader(BytesIO())


def test_generated_insert_blank_page_uses_previous_dimensions_when_omitted():
    """Verifies: PYPDF-WRITE-014."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    inserted = writer.insert_blank_page(index=0)
    assert inserted.mediabox.width == 100
    assert inserted.mediabox.height == 200


def test_generated_page_action_delete_removes_action_dictionary():
    """Verifies: PYPDF-FEAT-013."""
    page = PageObject.create_blank_page(width=100, height=100)
    page.add_action(PageTrigger.OPEN, JavaScript("app.alert('opened');"))
    page.delete_action(PageTrigger.OPEN)
    assert page.get("/AA") is None


def test_generated_page_scale_to_updates_both_dimensions():
    """Verifies: PYPDF-PAGE-003."""
    page = PageObject.create_blank_page(width=200, height=100)
    page.scale_to(50, 150)
    assert page.mediabox.width == 50
    assert page.mediabox.height == 150


def test_generated_add_transformation_without_expand_keeps_page_box():
    """Verifies: PYPDF-PAGE-003."""
    page = PageObject.create_blank_page(width=100, height=100)
    page.add_transformation(Transformation().translate(tx=500, ty=500), expand=False)
    assert page.mediabox.width == 100
    assert page.mediabox.height == 100


def test_generated_transfer_rotation_to_content_resets_rotation():
    """Verifies: PYPDF-PAGE-003."""
    page = PageObject.create_blank_page(width=100, height=200)
    page.rotate(90)
    page.transfer_rotation_to_content()
    assert page.rotation == 0


def test_generated_reader_get_page_out_of_range_raises_index_error():
    """Verifies: PYPDF-READ-004."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    reader = _roundtrip(writer)
    with pytest.raises(IndexError):
        reader.get_page(3)
