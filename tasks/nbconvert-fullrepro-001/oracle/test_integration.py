import json

import nbformat
import pytest

from nbconvert import HTMLExporter, MarkdownExporter, NotebookExporter, PythonExporter, export
from nbconvert.exporters import Exporter, get_exporter
from nbconvert.filters import DataTypeFilter, add_anchor, ansi2html, markdown2html, path2url
from nbconvert.preprocessors import (
    ClearMetadataPreprocessor,
    ClearOutputPreprocessor,
    CoalesceStreamsPreprocessor,
    ExtractOutputPreprocessor,
    HighlightMagicsPreprocessor,
    RegexRemovePreprocessor,
    TagRemovePreprocessor,
)
from nbconvert.writers import FilesWriter


@pytest.mark.depends_on(
    "test_markdown_exporter_projects_markdown_and_code_cells",
    "test_tag_remove_preprocessor_removes_tagged_cells",
)
def test_markdown_export_with_tagged_cell_removal_combines_preprocessor_and_template(
    notebook_factory, markdown_cell, code_cell
):
    nb = notebook_factory(
        [
            markdown_cell("# Keep"),
            code_cell("hidden = 1", metadata={"tags": ["drop"]}),
            code_cell("shown = 2"),
        ]
    )
    exporter = MarkdownExporter()
    exporter.register_preprocessor(TagRemovePreprocessor(remove_cell_tags={"drop"}), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    assert "# Keep" in body
    assert "shown = 2" in body
    assert "hidden = 1" not in body
    assert resources["output_extension"] == ".md"


@pytest.mark.depends_on(
    "test_python_exporter_comments_markdown_and_emits_code",
    "test_tag_remove_preprocessor_marks_tagged_input_for_omission",
)
def test_python_export_with_removed_input_tag_keeps_outputless_cell_metadata_projection(
    notebook_factory, code_cell
):
    nb = notebook_factory([code_cell("secret()", metadata={"tags": ["hide"]})])
    exporter = PythonExporter()
    exporter.register_preprocessor(TagRemovePreprocessor(remove_input_tags={"hide"}), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    assert "secret()" not in body
    assert resources["output_extension"] == ".py"


@pytest.mark.depends_on(
    "test_notebook_exporter_returns_notebook_json_string",
    "test_clear_output_preprocessor_removes_outputs_counts_and_output_metadata",
)
def test_notebook_export_with_clear_output_projects_clean_notebook_json(
    notebook_factory, code_cell, stream_output
):
    nb = notebook_factory([code_cell("print('x')", outputs=[stream_output("x")], execution_count=5)])
    exporter = NotebookExporter()
    exporter.register_preprocessor(ClearOutputPreprocessor(), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    data = json.loads(body)
    assert data["cells"][0]["outputs"] == []
    assert data["cells"][0]["execution_count"] is None
    assert resources["output_extension"] == ".ipynb"


@pytest.mark.depends_on(
    "test_markdown_exporter_projects_markdown_and_code_cells",
    "test_coalesce_streams_preprocessor_merges_adjacent_same_named_streams",
)
def test_markdown_export_with_coalesced_streams_projects_single_output_block(
    notebook_factory, code_cell, stream_output
):
    nb = notebook_factory([code_cell("print('ab')", outputs=[stream_output("a"), stream_output("b")])])
    exporter = MarkdownExporter()
    exporter.register_preprocessor(CoalesceStreamsPreprocessor(), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    assert "ab" in body
    assert "a\nb" not in body
    assert resources["output_extension"] == ".md"


@pytest.mark.depends_on(
    "test_markdown_exporter_projects_markdown_and_code_cells",
    "test_regex_remove_preprocessor_removes_matching_source_cells",
)
def test_markdown_export_with_regex_removed_cell_keeps_unmatched_cells(
    notebook_factory, markdown_cell
):
    nb = notebook_factory([markdown_cell("keep this"), markdown_cell("REMOVE this")])
    exporter = MarkdownExporter()
    exporter.register_preprocessor(RegexRemovePreprocessor(patterns=["REMOVE"]), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    assert "keep this" in body
    assert "REMOVE this" not in body
    assert resources["output_extension"] == ".md"


@pytest.mark.depends_on(
    "test_notebook_exporter_returns_notebook_json_string",
    "test_clear_metadata_preprocessor_preserves_configured_notebook_key",
)
def test_notebook_export_with_metadata_clear_preserves_language_name_only(
    notebook_factory, code_cell
):
    nb = notebook_factory(
        [code_cell("x = 1", metadata={"remove": True})],
        metadata={"language_info": {"name": "python", "version": "3.11"}, "extra": "drop"},
    )
    exporter = NotebookExporter()
    exporter.register_preprocessor(ClearMetadataPreprocessor(), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    data = json.loads(body)
    assert data["metadata"] == {"language_info": {"name": "python"}}
    assert data["cells"][0]["metadata"] == {}
    assert resources["output_extension"] == ".ipynb"


@pytest.mark.depends_on(
    "test_html_exporter_returns_html_document_with_rendered_markdown",
    "test_extract_output_preprocessor_writes_binary_resource_and_cell_filename",
)
def test_html_export_extracts_png_output_resource_and_references_filename(
    notebook_factory, code_cell, png_output
):
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "assets", "unique_key": "nb"}
    exporter = HTMLExporter(template_name="classic")
    exporter.register_preprocessor(ExtractOutputPreprocessor(), enabled=True)
    body, new_resources = exporter.from_notebook_node(
        notebook_factory(
            [
                code_cell(
                    "",
                    outputs=[png_output(b"PNGDATA", metadata={"image/png": {"alt": "output image"}})],
                )
            ]
        ),
        resources,
    )
    assert new_resources["outputs"] == {"assets/nb_0_0.png": b"PNGDATA"}
    assert "assets/nb_0_0.png" in body
    assert new_resources["output_extension"] == ".html"


@pytest.mark.depends_on(
    "test_html_exporter_returns_html_document_with_rendered_markdown",
    "test_extract_output_preprocessor_writes_binary_resource_and_cell_filename",
    "test_files_writer_writes_main_output_and_resource_files",
)
def test_html_export_resources_can_be_written_by_files_writer(
    tmp_path, notebook_factory, markdown_cell, code_cell, png_output
):
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "assets", "unique_key": "page"}
    exporter = HTMLExporter(template_name="classic")
    exporter.register_preprocessor(ExtractOutputPreprocessor(), enabled=True)
    body, new_resources = exporter.from_notebook_node(
        notebook_factory(
            [
                markdown_cell("# Persisted HTML"),
                code_cell(
                    "",
                    outputs=[png_output(b"HTMLPNG", metadata={"image/png": {"alt": "saved image"}})],
                ),
            ]
        ),
        resources,
    )
    destination = FilesWriter(build_directory=str(tmp_path)).write(
        body, new_resources, notebook_name="page"
    )
    assert destination == tmp_path / "page.html"
    assert "Persisted HTML" in destination.read_text(encoding="utf-8")
    assert "assets/page_1_0.png" in destination.read_text(encoding="utf-8")
    assert (tmp_path / "assets" / "page_1_0.png").read_bytes() == b"HTMLPNG"


@pytest.mark.depends_on(
    "test_markdown_exporter_projects_markdown_and_code_cells",
    "test_extract_attachments_preprocessor_rewrites_attachment_references",
)
def test_markdown_export_extracts_attachment_and_rewrites_public_reference(
    notebook_factory, markdown_cell
):
    attachment = {"image.png": {"image/png": "UE5H"}}
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "files", "unique_key": "nb"}
    exporter = MarkdownExporter()
    body, new_resources = exporter.from_notebook_node(
        notebook_factory([markdown_cell("![x](attachment:image.png)", attachments=attachment)]),
        resources,
    )
    assert "![x](files/image.png)" in body
    assert new_resources["outputs"] == {"files/image.png": b"PNG"}
    assert new_resources["output_extension"] == ".md"


@pytest.mark.depends_on(
    "test_files_writer_writes_main_output_and_resource_files",
    "test_extract_output_preprocessor_writes_binary_resource_and_cell_filename",
)
def test_markdown_export_resources_can_be_written_by_files_writer(
    tmp_path, notebook_factory, code_cell, png_output
):
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "out", "unique_key": "demo"}
    exporter = MarkdownExporter()
    body, new_resources = exporter.from_notebook_node(
        notebook_factory([code_cell("", outputs=[png_output(b"DATA")])]),
        resources,
    )
    destination = FilesWriter(build_directory=str(tmp_path)).write(
        body, new_resources, notebook_name="demo"
    )
    assert destination == tmp_path / "demo.md"
    assert "out/demo_0_0.png" in destination.read_text(encoding="utf-8")
    assert (tmp_path / "out" / "demo_0_0.png").read_bytes() == b"DATA"


@pytest.mark.depends_on(
    "test_export_function_accepts_exporter_class_and_notebook_node",
    "test_get_exporter_resolves_public_local_exporters",
)
def test_public_get_exporter_class_feeds_public_export_function(notebook_factory, markdown_cell):
    exporter_class = get_exporter("markdown")
    body, resources = export(exporter_class, notebook_factory([markdown_cell("from registry")]))
    assert "from registry" in body
    assert resources["output_extension"] == ".md"


@pytest.mark.depends_on(
    "test_exporter_from_file_reads_notebook_stream",
    "test_notebook_exporter_returns_notebook_json_string",
)
def test_from_filename_sets_metadata_and_exports_file_contents(tmp_path, notebook_factory, code_cell):
    path = tmp_path / "sample.ipynb"
    nbformat.write(notebook_factory([code_cell("from_file = 1")]), path)
    body, resources = NotebookExporter().from_filename(str(path))
    data = json.loads(body)
    assert data["cells"][0]["source"] == ["from_file = 1"]
    assert resources["metadata"]["name"] == "sample"
    assert resources["metadata"]["path"] == str(tmp_path)


@pytest.mark.depends_on(
    "test_python_exporter_comments_markdown_and_emits_code",
    "test_highlight_magics_preprocessor_marks_magic_language",
)
def test_python_export_with_magic_highlighting_keeps_code_and_metadata_side_effect(
    notebook_factory, code_cell
):
    nb = notebook_factory([code_cell("%%bash\necho hi")])
    exporter = PythonExporter()
    exporter.register_preprocessor(HighlightMagicsPreprocessor(), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    assert "run_cell_magic('bash'" in body
    assert "echo hi" in body
    assert resources["output_extension"] == ".py"


@pytest.mark.depends_on(
    "test_html_exporter_returns_html_document_with_rendered_markdown",
    "test_markdown_filter_renders_basic_html_without_pandoc",
    "test_add_anchor_adds_header_id_and_anchor_link",
)
def test_markdown_filter_anchor_result_is_embedded_in_html_export_resource_flow(
    notebook_factory, markdown_cell
):
    anchored = add_anchor(markdown2html("## Linked Header").strip(), "#")
    nb = notebook_factory([markdown_cell(anchored)])
    body, resources = HTMLExporter().from_notebook_node(nb)
    assert "Linked Header" in body
    assert "Linked-Header" in body
    assert resources["output_extension"] == ".html"


@pytest.mark.depends_on('test_data_type_filter_selects_first_available_priority', 'test_html_exporter_returns_html_document_with_rendered_markdown', 'test_extract_output_preprocessor_writes_binary_resource_and_cell_filename')
def test_data_type_selection_agrees_with_exported_rich_output_resources(
    notebook_factory, code_cell, png_output
):
    output = png_output(b"PNG", metadata={"image/png": {"alt": "rich output"}})
    selector = DataTypeFilter(display_data_priority=["image/png", "text/plain"])
    assert selector(output.data) == ["image/png"]
    exporter = HTMLExporter(template_name="classic")
    exporter.register_preprocessor(ExtractOutputPreprocessor(), enabled=True)
    body, resources = exporter.from_notebook_node(
        notebook_factory([code_cell("", outputs=[output])]),
        {"metadata": {}, "outputs": {}, "output_files_dir": "out", "unique_key": "rich"},
    )
    assert resources["outputs"] == {"out/rich_0_0.png": b"PNG"}
    assert "out/rich_0_0.png" in body


@pytest.mark.depends_on(
    "test_ansi_filters_strip_and_wrap_colored_text",
    "test_markdown_exporter_projects_markdown_and_code_cells",
)
def test_ansi_html_filter_output_survives_markdown_export_as_html_text(
    notebook_factory, markdown_cell
):
    fragment = ansi2html("\x1b[31mred\x1b[0m")
    body, resources = MarkdownExporter().from_notebook_node(notebook_factory([markdown_cell(fragment)]))
    assert "ansi-red-fg" in body
    assert "red" in body
    assert resources["output_extension"] == ".md"


@pytest.mark.depends_on('test_string_filters_project_paths_base64_and_ascii', 'test_markdown_exporter_projects_markdown_and_code_cells', 'test_extract_attachments_preprocessor_rewrites_attachment_references')
def test_path_filter_matches_attachment_resource_path_projection(notebook_factory, markdown_cell):
    attachment = {"a b.png": {"image/png": "UE5H"}}
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "files", "unique_key": "nb"}
    exporter = MarkdownExporter()
    body, new_resources = exporter.from_notebook_node(
        notebook_factory([markdown_cell("![x](attachment:a b.png)", attachments=attachment)]),
        resources,
    )
    assert "files/a b.png" in body
    assert path2url("files/a b.png") == "files/a%20b.png"
    assert new_resources["outputs"]["files/a b.png"] == b"PNG"


@pytest.mark.depends_on(
    "test_notebook_exporter_returns_notebook_json_string",
    "test_tag_remove_preprocessor_removes_tagged_single_outputs",
)
def test_notebook_export_reflects_single_output_tag_removal_in_json(
    notebook_factory, code_cell, stream_output
):
    keep = stream_output("keep")
    drop = stream_output("drop")
    drop.metadata = {"tags": ["hide"]}
    exporter = NotebookExporter()
    exporter.register_preprocessor(TagRemovePreprocessor(remove_single_output_tags={"hide"}), enabled=True)
    body, resources = exporter.from_notebook_node(notebook_factory([code_cell("x", outputs=[keep, drop])]))
    data = json.loads(body)
    assert [output["text"] for output in data["cells"][0]["outputs"]] == [["keep"]]
    assert resources["output_extension"] == ".ipynb"


@pytest.mark.depends_on(
    "test_html_exporter_returns_html_document_with_rendered_markdown",
    "test_clear_output_preprocessor_removes_outputs_counts_and_output_metadata",
)
def test_html_export_after_clear_output_omits_stream_text_but_keeps_source(
    notebook_factory, code_cell, stream_output
):
    exporter = HTMLExporter()
    exporter.register_preprocessor(ClearOutputPreprocessor(), enabled=True)
    body, resources = exporter.from_notebook_node(
        notebook_factory([code_cell("print('visible source')", outputs=[stream_output("hidden output")])])
    )
    assert "visible source" in body
    assert "hidden output" not in body
    assert resources["output_extension"] == ".html"


@pytest.mark.depends_on(
    "test_markdown_exporter_projects_markdown_and_code_cells",
    "test_clear_metadata_preprocessor_preserves_configured_notebook_key",
    "test_tag_remove_preprocessor_removes_tagged_cells",
)
def test_multiple_preprocessors_run_in_registration_order_for_markdown_export(
    notebook_factory, markdown_cell, code_cell
):
    nb = notebook_factory(
        [
            markdown_cell("# Keep"),
            code_cell("drop()", metadata={"tags": ["drop"], "other": "x"}),
            code_cell("show()", metadata={"other": "x"}),
        ],
        metadata={"language_info": {"name": "python", "version": "3.11"}, "drop": "yes"},
    )
    exporter = MarkdownExporter()
    exporter.register_preprocessor(TagRemovePreprocessor(remove_cell_tags={"drop"}), enabled=True)
    exporter.register_preprocessor(ClearMetadataPreprocessor(), enabled=True)
    body, resources = exporter.from_notebook_node(nb)
    assert "drop()" not in body
    assert "show()" in body
    assert resources["output_extension"] == ".md"


@pytest.mark.depends_on(
    "test_files_writer_writes_main_output_and_resource_files",
    "test_extract_attachments_preprocessor_rewrites_attachment_references",
    "test_extract_output_preprocessor_writes_binary_resource_and_cell_filename",
)
def test_files_writer_persists_combined_attachment_and_output_resources(
    tmp_path, notebook_factory, markdown_cell, code_cell, png_output
):
    attachment = {"note.txt": {"text/plain": "bm90ZQ=="}}
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "files", "unique_key": "demo"}
    exporter = MarkdownExporter()
    body, new_resources = exporter.from_notebook_node(
        notebook_factory(
            [
                markdown_cell("[note](attachment:note.txt)", attachments=attachment),
                code_cell("", outputs=[png_output(b"IMG")]),
            ]
        ),
        resources,
    )
    destination = FilesWriter(build_directory=str(tmp_path)).write(
        body, new_resources, notebook_name="demo"
    )
    assert destination.read_text(encoding="utf-8").count("files/") >= 2
    assert (tmp_path / "files" / "note.txt").read_bytes() == b"note"
    assert (tmp_path / "files" / "demo_1_0.png").read_bytes() == b"IMG"


@pytest.mark.depends_on(
    "test_export_function_accepts_exporter_class_and_notebook_node",
    "test_files_writer_writes_main_output_and_resource_files",
)
def test_export_function_body_and_resources_can_drive_files_writer(
    tmp_path, notebook_factory, markdown_cell
):
    body, resources = export(MarkdownExporter, notebook_factory([markdown_cell("writer body")]))
    destination = FilesWriter(build_directory=str(tmp_path)).write(
        body, resources, notebook_name="written"
    )
    assert destination == tmp_path / "written.md"
    assert "writer body" in destination.read_text(encoding="utf-8")


@pytest.mark.depends_on(
    "test_exporter_from_file_reads_notebook_stream",
    "test_python_exporter_comments_markdown_and_emits_code",
)
def test_python_exporter_from_file_stream_projects_same_code(notebook_factory, code_cell, notebook_bytes):
    stream = notebook_bytes(notebook_factory([code_cell("via_stream = 5")]))
    body, resources = PythonExporter().from_file(stream)
    assert "via_stream = 5" in body
    assert resources["output_extension"] == ".py"


@pytest.mark.depends_on(
    "test_markdown_exporter_projects_markdown_and_code_cells",
    "test_notebook_exporter_returns_notebook_json_string",
)
def test_markdown_and_notebook_exporters_project_same_cell_order(
    notebook_factory, markdown_cell, code_cell
):
    nb = notebook_factory([markdown_cell("first"), code_cell("second = 2"), markdown_cell("third")])
    markdown_body, markdown_resources = MarkdownExporter().from_notebook_node(nb)
    notebook_body, notebook_resources = NotebookExporter().from_notebook_node(nb)
    data = json.loads(notebook_body)
    assert markdown_body.index("first") < markdown_body.index("second = 2") < markdown_body.index("third")
    assert [cell["cell_type"] for cell in data["cells"]] == ["markdown", "code", "markdown"]
    assert markdown_resources["output_extension"] == ".md"
    assert notebook_resources["output_extension"] == ".ipynb"


@pytest.mark.depends_on(
    "test_html_exporter_returns_html_document_with_rendered_markdown",
    "test_python_exporter_comments_markdown_and_emits_code",
)
def test_html_and_python_exporters_project_same_code_source_differently(
    notebook_factory, markdown_cell, code_cell
):
    nb = notebook_factory([markdown_cell("# Shared"), code_cell("shared = 10")])
    html_body, html_resources = HTMLExporter().from_notebook_node(nb)
    python_body, python_resources = PythonExporter().from_notebook_node(nb)
    assert "Shared" in html_body
    assert "shared" in html_body
    assert "10" in html_body
    assert "# # Shared" in python_body
    assert "shared = 10" in python_body
    assert html_resources["output_extension"] == ".html"
    assert python_resources["output_extension"] == ".py"


@pytest.mark.depends_on(
    "test_get_exporter_resolves_public_local_exporters",
    "test_notebook_exporter_returns_notebook_json_string",
)
def test_ipynb_alias_exporter_round_trips_public_notebook_json(notebook_factory, code_cell):
    exporter_class = get_exporter("ipynb")
    body, resources = exporter_class().from_notebook_node(notebook_factory([code_cell("alias = 1")]))
    data = json.loads(body)
    assert data["cells"][0]["source"] == ["alias = 1"]
    assert resources["output_extension"] == ".ipynb"


@pytest.mark.depends_on(
    "test_resources_dict_returns_empty_string_for_missing_keys",
    "test_markdown_exporter_projects_markdown_and_code_cells",
)
def test_exporter_initializes_missing_resource_metadata_for_template_export(
    notebook_factory, markdown_cell
):
    body, resources = MarkdownExporter().from_notebook_node(
        notebook_factory([markdown_cell("resource default")]),
        resources={},
    )
    assert "resource default" in body
    assert resources["metadata"]["name"] == "Notebook"
    assert resources["output_extension"] == ".md"


@pytest.mark.depends_on(
    "test_writer_base_requires_subclass_write_implementation",
    "test_exporter_from_file_reads_notebook_stream",
)
def test_base_exporter_with_custom_preprocessor_projects_modified_notebook_node(
    notebook_factory, code_cell
):
    class PublicCallablePreprocessor:
        enabled = True

        def __call__(self, nb, resources):
            nb.cells.append(nbformat.v4.new_markdown_cell("added by public callable"))
            resources["added"] = True
            return nb, resources

    exporter = Exporter()
    exporter.register_preprocessor(PublicCallablePreprocessor(), enabled=True)
    nb, resources = exporter.from_notebook_node(notebook_factory([code_cell("x = 1")]))
    assert [cell.cell_type for cell in nb.cells] == ["code", "markdown"]
    assert nb.cells[1].source == "added by public callable"
    assert resources["added"] is True
