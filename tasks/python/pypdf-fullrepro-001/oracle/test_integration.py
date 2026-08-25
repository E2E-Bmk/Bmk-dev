# Spec2Repo oracle tests for pypdf-fullrepro-001

from io import BytesIO

import pytest

from pypdf import PageObject, PageRange, PaperSize, PdfReader, PdfWriter, Transformation, mult, parse_filename_page_ranges
from pypdf.actions import JavaScript, PageTrigger
from pypdf.annotations import FreeText, Link, PolyLine, Rectangle, Text
from pypdf.constants import UserAccessPermissions
from pypdf.errors import PageSizeNotDefinedError, ParseError
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


def _pdf_bytes(writer: PdfWriter) -> bytes:
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.mark.depends_on("test_blank_page_without_known_size_raises")
def test_blank_page_roundtrip_preserves_page_count_and_size():
    """Verifies: PYPDF-WRITE-001, PYPDF-WRITE-007, PYPDF-INV-001."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=100)
    assert isinstance(page, PageObject)
    reader = _roundtrip(writer)
    assert len(reader.pages) == 1
    assert reader.pages[0].mediabox.width == 200
    assert reader.pages[0].mediabox.height == 100


@pytest.mark.depends_on("test_page_scale_by_updates_page_box")
def test_insert_page_controls_page_order():
    """Verifies: PYPDF-WRITE-002, PYPDF-INV-001."""
    first = PageObject.create_blank_page(width=100, height=100)
    second = PageObject.create_blank_page(width=200, height=100)
    writer = PdfWriter()
    writer.add_page(first)
    writer.insert_page(second, 0)
    assert [page.mediabox.width for page in writer.pages] == [200, 100]


@pytest.mark.depends_on("test_generated_create_string_object_text_and_bytes_types")
def test_metadata_add_replace_and_remove_roundtrip():
    """Verifies: PYPDF-FEAT-002, PYPDF-INV-002."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_metadata({"/Title": "First", "/Author": "Author"})
    reader = _roundtrip(writer)
    assert reader.metadata.title == "First"
    assert reader.metadata.author == "Author"

    writer.metadata = {"/Title": "Second"}
    reader = _roundtrip(writer)
    assert reader.metadata.title == "Second"
    assert reader.metadata.author is None

    writer.metadata = None
    reader = _roundtrip(writer)
    assert reader.metadata is None


@pytest.mark.depends_on("test_content_stream_data_roundtrip_on_decoded_stream")
def test_attachment_roundtrip_exposes_mapping_and_object_view():
    """Verifies: PYPDF-FEAT-007, PYPDF-INV-003."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    embedded = writer.add_attachment("notes.txt", b"hello")
    embedded.description = create_string_object("description")
    reader = _roundtrip(writer)
    assert reader.attachments["notes.txt"] == [b"hello"]
    attachment = next(iter(reader.attachment_list))
    assert attachment.name == "notes.txt"
    assert attachment.content == b"hello"
    assert attachment.description == "description"


@pytest.mark.depends_on("test_destination_exposes_title_page_and_fit_fields")
def test_outline_roundtrip_preserves_nested_destination():
    """Verifies: PYPDF-FEAT-006, PYPDF-INV-004."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    parent = writer.add_outline_item("Parent", page_number=0)
    writer.add_outline_item("Child", page_number=0, parent=parent, fit=Fit.fit())
    reader = _roundtrip(writer)
    assert reader.outline[0].title == "Parent"
    assert reader.outline[1][0].title == "Child"
    assert reader.get_destination_page_number(reader.outline[1][0]) == 0


@pytest.mark.depends_on("test_generated_insert_blank_page_uses_previous_dimensions_when_omitted")
def test_page_labels_roundtrip_matches_page_order():
    """Verifies: PYPDF-INV-009."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    writer.set_page_label(0, 1, style="/D", prefix="A-", start=1)
    reader = _roundtrip(writer)
    assert reader.page_labels == ["A-1", "A-2"]


@pytest.mark.depends_on("test_encrypt_rejects_unknown_algorithm")
def test_encrypt_default_owner_password_roundtrip():
    """Verifies: PYPDF-WRITE-009, PYPDF-WRITE-013, PYPDF-INV-005."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    reader = _roundtrip(writer)
    assert reader.is_encrypted is True
    assert reader.decrypt("secret").name != "NOT_DECRYPTED"
    assert len(reader.pages) == 1


@pytest.mark.depends_on("test_annotation_dictionaries_expose_expected_public_entries")
def test_writer_add_annotation_roundtrip():
    """Verifies: PYPDF-FEAT-008."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_annotation(0, Rectangle(rect=(10, 10, 20, 20), interior_color="ff0000"))
    reader = _roundtrip(writer)
    annotations = reader.pages[0].annotations
    assert len(annotations) == 1
    assert annotations[0].get_object()["/Subtype"] == "/Square"


@pytest.mark.depends_on("test_generated_reader_get_page_out_of_range_raises_index_error")
def test_reader_get_page_number_returns_none_for_foreign_page():
    """Verifies: PYPDF-READ-006."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    reader = _roundtrip(writer)
    foreign_page = PageObject.create_blank_page(width=100, height=100)
    assert reader.get_page_number(reader.pages[0]) == 0
    assert reader.get_page_number(foreign_page) is None


@pytest.mark.depends_on("test_generated_insert_blank_page_uses_previous_dimensions_when_omitted")
def test_generated_blank_page_roundtrip_page_number_and_count():
    """Verifies: PYPDF-WRITE-007, PYPDF-INV-001."""
    writer = PdfWriter()
    first = writer.add_blank_page(width=72, height=144)
    second = writer.add_blank_page(width=144, height=72)
    assert first.page_number == 0
    assert second.page_number == 1
    reader = _roundtrip(writer)
    assert len(reader.pages) == 2
    assert reader.pages[1].mediabox.width == 144


@pytest.mark.depends_on("test_generated_insert_blank_page_uses_previous_dimensions_when_omitted")
def test_generated_remove_page_changes_serialized_page_sequence():
    """Verifies: PYPDF-WRITE-015, PYPDF-INV-001."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=200, height=100)
    writer.remove_page(0)
    reader = _roundtrip(writer)
    assert len(reader.pages) == 1
    assert reader.pages[0].mediabox.width == 200


@pytest.mark.depends_on("test_generated_insert_blank_page_uses_previous_dimensions_when_omitted")
def test_generated_append_reader_preserves_page_order():
    """Verifies: PYPDF-WRITE-004, PYPDF-INV-001."""
    source = PdfWriter()
    source.add_blank_page(width=90, height=100)
    source.add_blank_page(width=180, height=100)
    writer = PdfWriter()
    writer.append(_roundtrip(source), pages=[1, 0, 1])
    reader = _roundtrip(writer)
    assert [page.mediabox.width for page in reader.pages] == [180, 90, 180]


@pytest.mark.depends_on("test_generated_insert_blank_page_uses_previous_dimensions_when_omitted")
def test_generated_merge_reader_at_position_inserts_before_existing_page():
    """Verifies: PYPDF-WRITE-005."""
    source = PdfWriter()
    source.add_blank_page(width=50, height=100)
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=200, height=100)
    writer.merge(1, _roundtrip(source))
    reader = _roundtrip(writer)
    assert [page.mediabox.width for page in reader.pages] == [100, 50, 200]


@pytest.mark.depends_on("test_generated_create_string_object_text_and_bytes_types")
def test_generated_metadata_custom_key_survives_roundtrip():
    """Verifies: PYPDF-FEAT-002, PYPDF-INV-002."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_metadata({"/Custom": "Value"})
    assert _roundtrip(writer).metadata["/Custom"] == "Value"


@pytest.mark.depends_on("test_generated_create_string_object_text_and_bytes_types")
def test_generated_xmp_create_assign_and_read_title():
    """Verifies: PYPDF-FEAT-003, PYPDF-INV-004."""
    from pypdf.xmp import XmpInformation

    xmp = XmpInformation.create()
    xmp.dc_title = {"x-default": "Generated title"}
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.xmp_metadata = xmp
    assert _roundtrip(writer).xmp_metadata.dc_title == {"x-default": "Generated title"}


@pytest.mark.depends_on("test_content_stream_data_roundtrip_on_decoded_stream")
def test_generated_duplicate_attachment_names_return_content_list():
    """Verifies: PYPDF-FEAT-007, PYPDF-INV-003."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_attachment("same.txt", b"one")
    writer.add_attachment("same.txt", b"two")
    assert _roundtrip(writer).attachments["same.txt"] == [b"one", b"two"]


@pytest.mark.depends_on("test_content_stream_data_roundtrip_on_decoded_stream")
def test_generated_attachment_delete_removes_writer_attachment():
    """Verifies: PYPDF-FEAT-007."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    attachment = writer.add_attachment("gone.txt", b"x")
    attachment.delete()
    assert list(writer.attachment_list) == []


@pytest.mark.depends_on("test_annotation_dictionaries_expose_expected_public_entries")
def test_generated_text_annotation_roundtrip_and_remove():
    """Verifies: PYPDF-FEAT-008."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_annotation(0, Text(rect=(1, 2, 3, 4), text="note"))
    assert len(_roundtrip(writer).pages[0].annotations) == 1
    writer.remove_annotations("/Text")
    assert _roundtrip(writer).pages[0].annotations == []


@pytest.mark.depends_on("test_annotation_dictionaries_expose_expected_public_entries")
def test_generated_link_annotation_to_url_roundtrip():
    """Verifies: PYPDF-FEAT-008."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_annotation(0, Link(rect=(1, 2, 3, 4), url="https://example.com"))
    annot = _roundtrip(writer).pages[0].annotations[0].get_object()
    assert annot["/Subtype"] == "/Link"
    assert annot["/A"]["/URI"] == "https://example.com"


@pytest.mark.depends_on("test_javascript_action_can_be_added_to_page_trigger")
def test_generated_add_document_javascript_writes_names_entry():
    """Verifies: PYPDF-FEAT-009, PYPDF-READ-010."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_js("this.print();")
    root = _roundtrip(writer).root_object
    assert "/Names" in root
    assert "/JavaScript" in root["/Names"]


@pytest.mark.depends_on("test_encrypt_rejects_unknown_algorithm")
def test_generated_encrypted_reader_wrong_password_does_not_unlock():
    """Verifies: PYPDF-WRITE-013, PYPDF-READ-011, PYPDF-INV-005."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("user", owner_password="owner", algorithm="RC4-40")
    reader = _roundtrip(writer)
    assert reader.is_encrypted is True
    assert reader.decrypt("wrong") == 0


@pytest.mark.depends_on("test_encrypt_rejects_unknown_algorithm")
def test_generated_encrypted_reader_owner_password_unlocks_document():
    """Verifies: PYPDF-WRITE-013, PYPDF-READ-011, PYPDF-INV-005."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("user", owner_password="owner", algorithm="RC4-128")
    reader = _roundtrip(writer)
    assert reader.decrypt("owner") == 2
    assert len(reader.pages) == 1


@pytest.mark.depends_on("test_destination_exposes_title_page_and_fit_fields")
def test_generated_reader_get_destination_page_number_for_outline():
    """Verifies: PYPDF-READ-008, PYPDF-FEAT-006."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_outline_item("Start", 0)
    reader = _roundtrip(writer)
    assert reader.get_destination_page_number(reader.outline[0]) == 0


@pytest.mark.depends_on("test_generated_reader_get_page_out_of_range_raises_index_error")
def test_generated_reader_get_page_returns_zero_based_page():
    """Verifies: PYPDF-READ-004."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=150, height=100)
    reader = _roundtrip(writer)
    assert reader.get_page(1).mediabox.width == 150


@pytest.mark.depends_on("test_page_rotate_accepts_right_angles_and_rejects_other_angles")
def test_generated_page_rotation_roundtrip_preserves_rotation():
    """Verifies: PYPDF-GEOM-002, PYPDF-INV-001."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=100, height=200)
    page.rotate(90)
    reader = _roundtrip(writer)
    assert reader.pages[0].rotation == 90


@pytest.mark.depends_on("test_generated_create_string_object_text_and_bytes_types")
def test_generated_state_model_reader_projections_reflect_document_graph():
    """Verifies: PYPDF-STATE-001."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_metadata({"/Title": "State title"})
    writer.add_attachment("state.txt", b"state bytes")
    writer.add_outline_item("State start", 0)
    writer.set_page_label(0, 0, style="/D", prefix="S-", start=1)
    reader = _roundtrip(writer)
    assert reader.metadata.title == "State title"
    assert reader.attachments["state.txt"] == [b"state bytes"]
    assert reader.outline[0].title == "State start"
    assert reader.page_labels == ["S-1"]


@pytest.mark.depends_on("test_generated_insert_blank_page_uses_previous_dimensions_when_omitted")
def test_generated_state_model_writer_page_sequence_mutations_are_projected():
    """Verifies: PYPDF-STATE-002, PYPDF-WRITE-015."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=300, height=100)
    writer.insert_blank_page(width=200, height=100, index=1)
    writer.remove_page(0)
    assert len(writer.pages) == 2
    reader = _roundtrip(writer)
    assert [page.mediabox.width for page in reader.pages] == [200, 300]


@pytest.mark.depends_on("test_generated_insert_blank_page_uses_previous_dimensions_when_omitted")
def test_generated_state_model_file_projection_roundtrips_written_bytes(tmp_path):
    """Verifies: PYPDF-STATE-005."""
    writer = PdfWriter()
    writer.add_blank_page(width=123, height=234)
    output = tmp_path / "state.pdf"
    with output.open("wb") as stream:
        writer.write(stream)
    reader = PdfReader(output)
    assert len(reader.pages) == 1
    assert reader.pages[0].mediabox.height == 234


@pytest.mark.depends_on(
    "test_generated_insert_blank_page_uses_previous_dimensions_when_omitted",
    "test_generated_transformation_matrix_for_translate_and_scale",
)
def test_generated_workflow_merge_transform_and_append_roundtrip():
    """Verifies: PYPDF-WF-001."""
    base_writer = PdfWriter()
    base_writer.add_blank_page(width=200, height=200)
    stamp_writer = PdfWriter()
    stamp_writer.add_blank_page(width=50, height=50)
    base = PdfReader(BytesIO(_pdf_bytes(base_writer)))
    stamp = PdfReader(BytesIO(_pdf_bytes(stamp_writer)))
    writer = PdfWriter()
    first_page = writer.add_page(base.pages[0])
    first_page.merge_transformed_page(
        stamp.pages[0],
        Transformation().scale(0.5).translate(tx=72, ty=72),
        expand=True,
    )
    writer.append(stamp, pages=(0, 1))
    reader = _roundtrip(writer)
    assert len(reader.pages) == 2
    assert reader.pages[0].mediabox.width >= 200


@pytest.mark.depends_on("test_encrypt_rejects_unknown_algorithm")
def test_generated_workflow_clone_edit_encrypt_and_read_features():
    """Verifies: PYPDF-WF-002."""
    source = PdfWriter()
    source.add_blank_page(width=100, height=100)
    source_reader = PdfReader(BytesIO(_pdf_bytes(source)))
    writer = PdfWriter(clone_from=source_reader)
    writer.add_metadata({"/Title": "Updated title"})
    writer.add_attachment("notes.txt", b"local bytes")
    writer.add_outline_item("Start", page_number=0)
    writer.encrypt("reader-password", algorithm="AES-256")
    encrypted = _roundtrip(writer)
    assert encrypted.is_encrypted is True
    assert encrypted.decrypt("reader-password") != 0
    assert encrypted.metadata.title == "Updated title"
    assert encrypted.attachments["notes.txt"] == [b"local bytes"]


@pytest.mark.depends_on("test_generated_reader_get_page_out_of_range_raises_index_error")
def test_generated_workflow_path_read_append_and_serialize(tmp_path):
    """Verifies: PYPDF-WF-001."""
    source = PdfWriter()
    source.add_blank_page(width=90, height=100)
    source.add_blank_page(width=180, height=100)
    path = tmp_path / "source.pdf"
    path.write_bytes(_pdf_bytes(source))
    reader = PdfReader(path)
    writer = PdfWriter()
    writer.append(reader, pages=(0, 2))
    output = _roundtrip(writer)
    assert len(output.pages) == 2
    assert [page.mediabox.width for page in output.pages] == [90, 180]


@pytest.mark.depends_on("test_generated_create_string_object_text_and_bytes_types")
def test_generated_workflow_feature_preservation_without_encryption():
    """Verifies: PYPDF-WF-002."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_metadata({"/Author": "Workflow author"})
    writer.add_attachment("workflow.txt", b"payload")
    writer.add_outline_item("Workflow start", 0)
    writer.set_page_label(0, 0, style="/D", prefix="W-", start=7)
    reader = _roundtrip(writer)
    assert reader.metadata.author == "Workflow author"
    assert reader.attachments["workflow.txt"] == [b"payload"]
    assert reader.outline[0].title == "Workflow start"
    assert reader.page_labels == ["W-7"]
