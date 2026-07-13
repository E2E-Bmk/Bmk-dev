"""Candidate-safe rewrites retained from the upstream nbformat test suite."""

from __future__ import annotations

import json
import os

import pytest

from nbformat import (
    NO_CONVERT,
    NotebookNode,
    ValidationError,
    convert,
    from_dict,
    read,
    reads,
    validate,
    write,
    writes,
)
from nbformat.sign import MemorySignatureStore, NotebookNotary
from nbformat.validator import isvalid
from nbformat.v3 import parse_filename
from nbformat.v4 import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_output,
    new_raw_cell,
)


def test_v4_empty_notebook():
    nb = new_notebook()
    assert nb.cells == []
    assert nb.metadata == NotebookNode()
    assert nb.nbformat == 4


def test_v4_markdown_cell_defaults():
    cell = new_markdown_cell()
    assert cell.cell_type == "markdown"
    assert cell.source == ""
    assert cell.metadata == {}
    assert isinstance(cell.id, str)


def test_v4_markdown_cell_source():
    cell = new_markdown_cell("some markdown")
    assert cell.source == "some markdown"


def test_v4_raw_cell_defaults():
    cell = new_raw_cell()
    assert cell.cell_type == "raw"
    assert cell.source == ""
    assert cell.metadata == {}
    assert isinstance(cell.id, str)


def test_v4_raw_cell_source():
    assert new_raw_cell("raw text").source == "raw text"


def test_v4_code_cell_defaults():
    cell = new_code_cell("print('ok')")
    assert cell.cell_type == "code"
    assert cell.source == "print('ok')"
    assert cell.execution_count is None
    assert cell.outputs == []
    assert cell.metadata == {}
    assert isinstance(cell.id, str)


def test_v4_display_data_defaults():
    output = new_output("display_data")
    assert output.output_type == "display_data"
    assert output.data == {}
    assert output.metadata == {}


def test_v4_stream_defaults():
    output = new_output("stream")
    assert output.output_type == "stream"
    assert output.name == "stdout"
    assert output.text == ""


def test_v4_execute_result_defaults():
    output = new_output("execute_result")
    assert output.output_type == "execute_result"
    assert output.data == {}
    assert output.metadata == {}
    assert output.execution_count is None


def test_v4_display_data_payload():
    payload = {"text/plain": "some text", "application/json": {"key": "value"}}
    output = new_output("display_data", payload)
    assert output.data == payload


def test_v4_execute_result_payload():
    payload = {"text/plain": "42", "application/json": {"answer": 42}}
    output = new_output("execute_result", payload, execution_count=10)
    assert output.data == payload
    assert output.execution_count == 10


def test_v4_error_output():
    output = new_output(
        "error",
        ename="NameError",
        evalue="missing name",
        traceback=["frame 0", "frame 1"],
    )
    assert output.output_type == "error"
    assert output.ename == "NameError"
    assert output.evalue == "missing name"
    assert output.traceback == ["frame 0", "frame 1"]


def test_v4_code_cell_with_outputs():
    outputs = [
        new_output("stream", text="hello"),
        new_output("execute_result", {"text/plain": "10"}, execution_count=10),
    ]
    cell = new_code_cell(execution_count=10, outputs=outputs)
    assert cell.execution_count == 10
    assert cell.outputs == outputs


def test_v4_stream_override():
    output = new_output("stream", name="stderr", text="hello there")
    assert output.name == "stderr"
    assert output.text == "hello there"


def test_v4_invalid_code_cell():
    cell = new_code_cell()
    cell.source = 5
    with pytest.raises(ValidationError):
        validate(cell, ref="code_cell", version=4)


def test_v4_invalid_markdown_cell():
    cell = new_markdown_cell()
    del cell["metadata"]
    with pytest.raises(ValidationError):
        validate(cell, ref="markdown_cell", version=4)


def test_v4_invalid_raw_cell():
    cell = new_raw_cell()
    del cell["source"]
    with pytest.raises(ValidationError):
        validate(cell, ref="raw_cell", version=4)


def test_v4_sample_notebook_validates():
    nb = new_notebook(cells=[new_markdown_cell("title"), new_code_cell("1 + 1")])
    assert validate(nb) is None
    assert isvalid(nb)


def test_notebooknode_nested_item_assignment():
    node = NotebookNode()
    node["metadata"] = {"kernel": {"name": "python"}}
    assert isinstance(node.metadata, NotebookNode)
    assert isinstance(node.metadata.kernel, NotebookNode)
    assert node.metadata.kernel.name == "python"


def test_notebooknode_update_nested_mapping():
    node = NotebookNode()
    node.update({"metadata": {"language": "python"}})
    assert node["metadata"]["language"] == "python"
    assert node.metadata.language == "python"


def test_from_dict_recursively_converts():
    node = from_dict({"cells": [{"source": "x"}], "metadata": {"name": "demo"}})
    assert isinstance(node, NotebookNode)
    assert isinstance(node.cells[0], NotebookNode)
    assert node.cells[0].source == "x"
    assert node.metadata.name == "demo"


def test_v4_splitlines_preserve_json_mime_data():
    output = new_output(
        "display_data",
        {"text/plain": "alpha\nbeta\n", "application/json": {"items": [1, 2]}},
    )
    nb = new_notebook(cells=[new_code_cell(outputs=[output])])
    raw = json.loads(writes(nb, split_lines=True))
    data = raw["cells"][0]["outputs"][0]["data"]
    assert data["text/plain"] == ["alpha\n", "beta\n"]
    assert data["application/json"] == {"items": [1, 2]}


def test_write_read_path_roundtrip_and_newline(tmp_path):
    nb = new_notebook(cells=[new_code_cell("print('ready')")])
    path = tmp_path / "roundtrip.ipynb"
    assert write(nb, path) is None
    assert path.read_text(encoding="utf-8").endswith("\n")
    assert read(path, as_version=4) == nb


def test_capture_validation_error_on_write():
    nb = new_notebook(cells=[new_markdown_cell("invalid")])
    del nb.cells[0]["source"]
    captured = {}
    text = writes(nb, capture_validation_error=captured)
    assert isinstance(text, str)
    assert isinstance(captured["ValidationError"], ValidationError)


def test_read_missing_path_raises_oserror(tmp_path):
    with pytest.raises(OSError):
        read(tmp_path / "missing.ipynb", as_version=4)


def test_convert_unknown_version_raises_valueerror():
    with pytest.raises(ValueError):
        convert(new_notebook(), 99)


def test_validate_empty_notebook_raises():
    with pytest.raises(ValidationError):
        validate({})


def test_isvalid_reports_false_for_invalid_notebook():
    assert isvalid({}) is False


def test_parse_filename_ipynb():
    assert parse_filename("test.ipynb") == ("test.ipynb", "test", "json")


def test_parse_filename_python():
    assert parse_filename("test.py") == ("test.py", "test", "py")


def test_parse_filename_extensionless():
    assert parse_filename("test.nb") == ("test.nb.ipynb", "test.nb", "json")


def test_parse_filename_absolute_path(tmp_path):
    path = os.path.abspath(tmp_path / "test.ipynb")
    basename, _ = os.path.splitext(path)
    assert parse_filename(path) == (path, basename, "json")


def _notary():
    return NotebookNotary(store_factory=MemorySignatureStore, secret=b"secret")


def test_notary_secret_changes_signature():
    nb = new_notebook(cells=[new_code_cell("1 + 1")])
    first = _notary().compute_signature(nb)
    second = NotebookNotary(store_factory=MemorySignatureStore, secret=b"other").compute_signature(nb)
    assert first != second


def test_notary_sign_and_check():
    notary = _notary()
    nb = new_notebook(cells=[new_code_cell("1 + 1")])
    assert not notary.check_signature(nb)
    notary.sign(nb)
    assert notary.check_signature(nb)


def test_notary_content_change_invalidates_signature():
    notary = _notary()
    nb = new_notebook(cells=[new_code_cell("1 + 1")])
    notary.sign(nb)
    nb.cells[0].source = "2 + 2"
    assert not notary.check_signature(nb)


def test_notary_mark_and_check_cells_removes_marker():
    notary = _notary()
    nb = new_notebook(cells=[new_code_cell(outputs=[new_output("display_data", {"text/html": "<b>x</b>"})])])
    notary.mark_cells(nb, True)
    assert nb.cells[0].metadata.trusted is True
    assert notary.check_cells(nb) is True
    assert "trusted" not in nb.cells[0].metadata


def test_notary_untrusted_safe_empty_output_cell():
    notary = _notary()
    nb = new_notebook(cells=[new_code_cell(outputs=[])])
    notary.mark_cells(nb, False)
    assert notary.check_cells(nb) is True


def test_memory_signature_store_lifecycle():
    store = MemorySignatureStore()
    digest = "0123456789abcdef"
    algorithm = "sha256"
    assert store.check_signature(digest, algorithm) is False
    store.store_signature(digest, algorithm)
    assert store.check_signature(digest, algorithm) is True
    store.remove_signature(digest, algorithm)
    assert store.check_signature(digest, algorithm) is False
