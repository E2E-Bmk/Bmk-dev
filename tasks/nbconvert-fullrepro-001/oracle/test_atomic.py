import base64
import json

import nbformat
import pytest

from nbconvert import HTMLExporter, MarkdownExporter, NotebookExporter, PythonExporter, export
from nbconvert.exporters import Exporter, ResourcesDict, get_export_names, get_exporter
from nbconvert.filters import (
    DataTypeFilter,
    add_anchor,
    add_prompts,
    ansi2html,
    ascii_only,
    comment_lines,
    get_lines,
    get_metadata,
    markdown2html,
    path2url,
    posix_path,
    strip_ansi,
    strip_files_prefix,
    strip_trailing_newline,
    text_base64,
    wrap_text,
)
from nbconvert.preprocessors import (
    ClearMetadataPreprocessor,
    ClearOutputPreprocessor,
    CoalesceStreamsPreprocessor,
    ExtractAttachmentsPreprocessor,
    ExtractOutputPreprocessor,
    HighlightMagicsPreprocessor,
    RegexRemovePreprocessor,
    TagRemovePreprocessor,
)
from nbconvert.writers import FilesWriter, StdoutWriter, WriterBase


def test_get_exporter_resolves_public_local_exporters():
    assert issubclass(get_exporter("markdown"), MarkdownExporter)
    assert issubclass(get_exporter("python"), PythonExporter)
    assert issubclass(get_exporter("ipynb"), NotebookExporter)


def test_get_export_names_includes_local_textual_formats():
    names = set(get_export_names())
    assert {"html", "markdown", "notebook", "python"}.issubset(names)


def test_export_function_accepts_exporter_class_and_notebook_node(notebook_factory, markdown_cell):
    nb = notebook_factory([markdown_cell("# Public Title")])
    body, resources = export(MarkdownExporter, nb)
    assert "# Public Title" in body
    assert resources["output_extension"] == ".md"


def test_resources_dict_returns_empty_string_for_missing_keys():
    resources = ResourcesDict()
    resources["known"] = "value"
    assert resources["known"] == "value"
    assert resources["missing"] == ""


def test_markdown_exporter_projects_markdown_and_code_cells(
    notebook_factory, markdown_cell, code_cell
):
    nb = notebook_factory([markdown_cell("# Heading"), code_cell("answer = 42")])
    body, resources = MarkdownExporter().from_notebook_node(nb)
    assert "# Heading" in body
    assert "```python" in body
    assert "answer = 42" in body
    assert resources["output_extension"] == ".md"


def test_python_exporter_comments_markdown_and_emits_code(
    notebook_factory, markdown_cell, code_cell
):
    nb = notebook_factory([markdown_cell("# Heading"), code_cell("answer = 42")])
    body, resources = PythonExporter().from_notebook_node(nb)
    assert "# # Heading" in body
    assert "answer = 42" in body
    assert resources["output_extension"] == ".py"


def test_notebook_exporter_returns_notebook_json_string(notebook_factory, code_cell):
    nb = notebook_factory([code_cell("value = 3")])
    body, resources = NotebookExporter().from_notebook_node(nb)
    data = json.loads(body)
    assert data["nbformat"] == 4
    assert data["cells"][0]["source"] == ["value = 3"]
    assert resources["output_extension"] == ".ipynb"


def test_html_exporter_returns_html_document_with_rendered_markdown(
    notebook_factory, markdown_cell
):
    nb = notebook_factory([markdown_cell("# HTML Heading")])
    body, resources = HTMLExporter().from_notebook_node(nb)
    assert body.lstrip().startswith("<!DOCTYPE html>")
    assert "HTML Heading" in body
    assert resources["output_extension"] == ".html"


def test_exporter_from_file_reads_notebook_stream(notebook_factory, code_cell, notebook_bytes):
    nb = notebook_factory([code_cell("streamed = True")])
    exported, resources = Exporter().from_file(notebook_bytes(nb))
    assert exported.cells[0].source == "streamed = True"
    assert resources["output_extension"] == ""


def test_data_type_filter_selects_first_available_priority():
    selector = DataTypeFilter(display_data_priority=["text/markdown", "text/plain"])
    assert selector({"text/plain": "plain", "text/html": "<b>html</b>"}) == ["text/plain"]


def test_data_type_filter_warns_and_returns_empty_for_unavailable_format():
    selector = DataTypeFilter(display_data_priority=["image/png"])
    with pytest.warns(UserWarning):
        result = selector({"text/plain": "plain"})
    assert result == []


def test_get_metadata_prefers_mimetype_metadata_then_top_level():
    output = {
        "metadata": {
            "width": 400,
            "image/png": {"width": 200},
        }
    }
    assert get_metadata(output, "width", "image/png") == 200
    assert get_metadata(output, "height", "image/png") is None
    assert get_metadata(output, "width") == 400


def test_ansi_filters_strip_and_wrap_colored_text():
    colored = "\x1b[31mred\x1b[0m and plain"
    assert strip_ansi(colored) == "red and plain"
    html = ansi2html(colored)
    assert "ansi-red-fg" in html
    assert "red" in html


def test_string_filters_project_wrapping_prompts_and_slices():
    assert wrap_text("alpha beta gamma", width=8) == "alpha\nbeta\ngamma"
    assert add_prompts("first\nsecond") == ">>> first\n... second"
    assert get_lines("a\nb\nc\nd", 1, 3) == "b\nc"


def test_string_filters_project_paths_base64_and_ascii():
    assert strip_files_prefix('src="files/image.png" and [x](/files/a b.txt)') == (
        'src="image.png" and [x](a b.txt)'
    )
    assert path2url("folder/a b+c.txt") == "folder/a%20b%2Bc.txt"
    assert posix_path("a/b") == "a/b"
    assert ascii_only("pi=\u03c0") == "pi=?"
    assert text_base64("hello") == "aGVsbG8="


def test_markdown_filter_renders_basic_html_without_pandoc():
    html = markdown2html("# Title\n\n- one")
    assert "<h1" in html
    assert "Title" in html
    assert "<li>one</li>" in html


def test_add_anchor_adds_header_id_and_anchor_link():
    anchored = add_anchor("<h2>My Header</h2>", "#")
    assert 'id="My-Header"' in anchored
    assert 'href="#My-Header"' in anchored
    assert ">#</a>" in anchored


def test_comment_and_trailing_newline_filters_are_stable():
    assert comment_lines("one\ntwo", prefix="// ") == "// one\n// two"
    assert strip_trailing_newline("line\n") == "line"
    assert strip_trailing_newline("line") == "line"


def test_clear_output_preprocessor_removes_outputs_counts_and_output_metadata(
    notebook_factory, code_cell, stream_output
):
    cell = code_cell(
        "print('x')",
        outputs=[stream_output("x")],
        metadata={"collapsed": True, "keep": "yes"},
        execution_count=7,
    )
    nb, resources = ClearOutputPreprocessor(enabled=True)(
        notebook_factory([cell]), {"metadata": {}, "outputs": {}}
    )
    assert nb.cells[0].outputs == []
    assert nb.cells[0].execution_count is None
    assert nb.cells[0].metadata == {"keep": "yes"}
    assert resources["outputs"] == {}


def test_coalesce_streams_preprocessor_merges_adjacent_same_named_streams(
    notebook_factory, code_cell, stream_output
):
    cell = code_cell(
        "print('x')",
        outputs=[stream_output("a"), stream_output("b"), stream_output("err", name="stderr")],
    )
    nb, resources = CoalesceStreamsPreprocessor(enabled=True)(
        notebook_factory([cell]), {"metadata": {}, "outputs": {}}
    )
    assert [output.text for output in nb.cells[0].outputs] == ["ab", "err"]
    assert resources["outputs"] == {}


def test_clear_metadata_preprocessor_preserves_configured_notebook_key(
    notebook_factory, code_cell
):
    nb = notebook_factory(
        [code_cell("x", metadata={"remove": True, "keep": {"inner": 1}})],
        metadata={"language_info": {"name": "python", "version": "3"}, "extra": "drop"},
    )
    preprocessor = ClearMetadataPreprocessor(
        enabled=True,
        preserve_cell_metadata_mask={("keep", "inner")},
    )
    new_nb, resources = preprocessor(nb, {"metadata": {}, "outputs": {}})
    assert new_nb.metadata == {"language_info": {"name": "python"}}
    assert new_nb.cells[0].metadata == {"keep": {"inner": 1}}
    assert resources["metadata"] == {}


def test_regex_remove_preprocessor_removes_matching_source_cells(
    notebook_factory, markdown_cell
):
    nb = notebook_factory([markdown_cell("keep"), markdown_cell("REMOVE me")])
    new_nb, resources = RegexRemovePreprocessor(enabled=True, patterns=["REMOVE"])(
        nb, {"metadata": {}, "outputs": {}}
    )
    assert [cell.source for cell in new_nb.cells] == ["keep"]
    assert resources["outputs"] == {}


def test_tag_remove_preprocessor_removes_tagged_cells(notebook_factory, markdown_cell):
    nb = notebook_factory(
        [
            markdown_cell("keep"),
            markdown_cell("secret", metadata={"tags": ["drop-cell"]}),
        ]
    )
    new_nb, resources = TagRemovePreprocessor(enabled=True, remove_cell_tags={"drop-cell"})(
        nb, {"metadata": {}, "outputs": {}}
    )
    assert [cell.source for cell in new_nb.cells] == ["keep"]
    assert resources["outputs"] == {}


def test_tag_remove_preprocessor_marks_tagged_input_for_omission(
    notebook_factory, code_cell
):
    nb = notebook_factory([code_cell("hidden()", metadata={"tags": ["hide-input"]})])
    new_nb, resources = TagRemovePreprocessor(enabled=True, remove_input_tags={"hide-input"})(
        nb, {"metadata": {}, "outputs": {}}
    )
    assert new_nb.cells[0].metadata["transient"] == {"remove_source": True}
    assert resources["outputs"] == {}


def test_tag_remove_preprocessor_removes_tagged_single_outputs(
    notebook_factory, code_cell, stream_output
):
    keep = stream_output("keep")
    drop = stream_output("drop")
    drop.metadata = {"tags": ["hide-output"]}
    nb = notebook_factory([code_cell("x", outputs=[keep, drop])])
    new_nb, resources = TagRemovePreprocessor(
        enabled=True,
        remove_single_output_tags={"hide-output"},
    )(nb, {"metadata": {}, "outputs": {}})
    assert [output.text for output in new_nb.cells[0].outputs] == ["keep"]
    assert resources["outputs"] == {}


def test_highlight_magics_preprocessor_marks_magic_language(notebook_factory, code_cell):
    nb, resources = HighlightMagicsPreprocessor(enabled=True)(
        notebook_factory([code_cell("%%bash\necho hi")]),
        {"metadata": {}, "outputs": {}},
    )
    assert nb.cells[0].metadata["magics_language"] == "bash"
    assert resources["outputs"] == {}


def test_extract_output_preprocessor_writes_binary_resource_and_cell_filename(
    notebook_factory, code_cell, png_output
):
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "outputs", "unique_key": "demo"}
    nb, new_resources = ExtractOutputPreprocessor(enabled=True)(
        notebook_factory([code_cell("", outputs=[png_output(b"abc")])]),
        resources,
    )
    assert new_resources["outputs"] == {"outputs/demo_0_0.png": b"abc"}
    assert nb.cells[0].outputs[0].metadata["filenames"]["image/png"] == "outputs/demo_0_0.png"


def test_extract_output_preprocessor_respects_public_filename_metadata(
    notebook_factory, code_cell, png_output
):
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "files", "unique_key": "demo"}
    output = png_output(b"named", metadata={"filename": "plot"})
    nb, new_resources = ExtractOutputPreprocessor(enabled=True)(
        notebook_factory([code_cell("", outputs=[output])]),
        resources,
    )
    assert new_resources["outputs"] == {"files/plot.png": b"named"}
    assert nb.cells[0].outputs[0].metadata["filenames"]["image/png"] == "files/plot.png"


def test_extract_attachments_preprocessor_rewrites_attachment_references(
    notebook_factory, markdown_cell
):
    attachments = {"picture.png": {"image/png": base64.b64encode(b"PNG").decode("ascii")}}
    resources = {"metadata": {}, "outputs": {}, "output_files_dir": "files", "unique_key": "demo"}
    nb, new_resources = ExtractAttachmentsPreprocessor(enabled=True)(
        notebook_factory([markdown_cell("![alt](attachment:picture.png)", attachments=attachments)]),
        resources,
    )
    assert nb.cells[0].source == "![alt](files/picture.png)"
    assert new_resources["outputs"] == {"files/picture.png": b"PNG"}


def test_files_writer_writes_main_output_and_resource_files(tmp_path):
    writer = FilesWriter(build_directory=str(tmp_path))
    destination = writer.write(
        "main body",
        {
            "output_extension": ".txt",
            "outputs": {"assets/a.bin": b"A"},
            "attachments": {"attachments/b.bin": b"B"},
            "metadata": {},
        },
        notebook_name="demo",
    )
    assert destination == tmp_path / "demo.txt"
    assert destination.read_text(encoding="utf-8") == "main body"
    assert (tmp_path / "assets" / "a.bin").read_bytes() == b"A"
    assert (tmp_path / "attachments" / "b.bin").read_bytes() == b"B"


def test_stdout_writer_writes_output_to_stdout(capsys):
    StdoutWriter().write("visible output", {"metadata": {}, "outputs": {}})
    assert capsys.readouterr().out == "visible output"


def test_writer_base_requires_subclass_write_implementation():
    with pytest.raises(NotImplementedError):
        WriterBase().write("body", {"metadata": {}, "outputs": {}})
