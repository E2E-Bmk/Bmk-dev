# Spec2Repo oracle - integration tests for nbformat-notebook-fullrepro-001
from __future__ import annotations

import io

import json

import os

from pathlib import Path

import subprocess

import sys

import pytest

import nbformat

from nbformat import NO_CONVERT, NotebookNode, ValidationError, from_dict

from nbformat import v4

from nbformat.sign import MemorySignatureStore, NotebookNotary

from nbformat.validator import isvalid, iter_validate, normalize

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

from nbformat.validator import isvalid

from nbformat.v3 import parse_filename

from nbformat.v4 import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_output,
    new_raw_cell,
)


_TRUST_COMMAND = None


def _notebook(source="print('ready')", output_text="ready\n"):
    return v4.new_notebook(
        cells=[
            v4.new_markdown_cell("# Analysis"),
            v4.new_code_cell(
                source,
                outputs=[v4.new_output("stream", text=output_text)],
            ),
        ]
    )


def _cli_env(tmp_path):
    env = os.environ.copy()
    for name in ("JUPYTER_CONFIG_DIR", "JUPYTER_DATA_DIR", "JUPYTER_RUNTIME_DIR", "IPYTHONDIR"):
        path = tmp_path / name.lower()
        path.mkdir(exist_ok=True)
        env[name] = str(path)
    return env


def _trust_command(tmp_path):
    global _TRUST_COMMAND
    if _TRUST_COMMAND is not None:
        return _TRUST_COMMAND

    _TRUST_COMMAND = [sys.executable, "-m", "nbformat.sign"]
    return _TRUST_COMMAND


def test_top_level_string_and_bytes_reads_preserve_content():
    text = nbformat.writes(_notebook(), version=NO_CONVERT)
    from_text = nbformat.reads(text, as_version=4)
    from_bytes = nbformat.reads(text.encode("utf-8"), as_version=4)
    assert from_text == from_bytes
    assert from_text.cells[1].source == "print('ready')"


def test_top_level_capture_validation_error_on_reads_and_writes():
    invalid = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": [{"id": "bad", "cell_type": "code", "metadata": {}, "source": "x", "outputs": [], "execution_count": "invalid"}]}
    read_errors = {}
    parsed = nbformat.reads(json.dumps(invalid), 4, capture_validation_error=read_errors)
    assert parsed.cells[0].source == "x"
    assert isinstance(read_errors["ValidationError"], ValidationError)
    write_errors = {}
    serialized = nbformat.writes(parsed, capture_validation_error=write_errors)
    assert json.loads(serialized)["cells"][0]["execution_count"] == "invalid"
    assert isinstance(write_errors["ValidationError"], ValidationError)


def test_top_level_file_like_errors_propagate():
    class BadReader:
        def read(self):
            raise OSError("read failed")

    class BadWriter:
        def write(self, value):
            raise OSError("write failed")

    with pytest.raises(OSError):
        nbformat.read(BadReader(), 4)
    with pytest.raises(OSError):
        nbformat.write(_notebook(), BadWriter())


def test_convert_v3_notebook_to_v4():
    v3 = nbformat.v3
    legacy = v3.new_notebook(
        worksheets=[v3.new_worksheet(cells=[v3.new_text_cell("markdown", source="legacy")])]
    )
    converted = nbformat.convert(legacy, 4)
    assert converted.nbformat == 4
    assert converted.cells[0].cell_type == "markdown"
    assert converted.cells[0].source == "legacy"


def test_normalize_repairs_ids_on_a_deep_copy():
    notebook = _notebook()
    duplicate = notebook.cells[0].id
    notebook.cells[1].id = duplicate
    changes, normalized = normalize(notebook)
    assert changes == 1
    assert notebook.cells[0].id == notebook.cells[1].id
    assert normalized.cells[0].id != normalized.cells[1].id


def test_durable_json_excludes_transient_trust_fields():
    notebook = _notebook()
    notebook.metadata.signature = "old"
    notebook.cells[1].metadata.trusted = True
    disk = json.loads(v4.writes(notebook))
    assert "signature" not in disk["metadata"]
    assert "trusted" not in disk["cells"][1]["metadata"]
    assert disk["cells"][1]["source"] == ["print('ready')"]


def test_trust_state_is_external_to_notebook_json():
    notebook = _notebook()
    notary = NotebookNotary(store_factory=MemorySignatureStore, secret=b"state-secret")
    assert notary.check_signature(notebook) is False
    notary.sign(notebook)
    assert notary.check_signature(notebook) is True
    assert "signature" not in notebook.metadata
    assert "signature" not in json.loads(nbformat.writes(notebook))["metadata"]


def test_v4_reader_rejoins_disk_multiline_lists():
    disk = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": [{"id": "cell", "cell_type": "code", "metadata": {}, "execution_count": None, "source": ["a\n", "b"], "outputs": [{"output_type": "stream", "name": "stdout", "text": ["x\n", "y"]}]}]}
    notebook = v4.reads(json.dumps(disk))
    assert notebook.cells[0].source == "a\nb"
    assert notebook.cells[0].outputs[0].text == "x\ny"


def test_v4_writer_splits_text_but_preserves_json_mime_values():
    output = v4.new_output("display_data", data={"text/plain": "a\nb", "application/json": {"line": "a\nb"}, "application/vnd.example+json": ["a\nb"]})
    notebook = v4.new_notebook(cells=[v4.new_code_cell("x\ny", outputs=[output])])
    disk = json.loads(v4.writes(notebook))
    assert disk["cells"][0]["source"] == ["x\n", "y"]
    assert disk["cells"][0]["outputs"][0]["data"]["text/plain"] == ["a\n", "b"]
    assert disk["cells"][0]["outputs"][0]["data"]["application/json"] == {"line": "a\nb"}
    assert disk["cells"][0]["outputs"][0]["data"]["application/vnd.example+json"] == ["a\nb"]


def test_signature_changes_with_content_and_unsign_removes_it():
    notebook = _notebook()
    notary = NotebookNotary(store_factory=MemorySignatureStore, secret=b"content-secret")
    notary.sign(notebook)
    assert notary.check_signature(notebook) is True
    notebook.cells[0].source = "changed"
    assert notary.check_signature(notebook) is False
    notebook.cells[0].source = "# Analysis"
    assert notary.check_signature(notebook) is True
    notary.unsign(notebook)
    assert notary.check_signature(notebook) is False


def test_mark_and_check_cells_consumes_transient_marker():
    rich = v4.new_output("display_data", data={"text/html": "<b>x</b>"})
    notebook = v4.new_notebook(cells=[v4.new_code_cell(outputs=[rich])])
    notary = NotebookNotary(store_factory=MemorySignatureStore, secret=b"cell-secret")
    assert notary.check_cells(notebook) is False
    notary.mark_cells(notebook, True)
    assert notebook.cells[0].metadata.trusted is True
    assert notary.check_cells(notebook) is True
    assert "trusted" not in notebook.cells[0].metadata


def test_generic_string_round_trip_preserves_notebook_content():
    notebook = _notebook("x = 1\nprint(x)", "1\n")
    text = nbformat.writes(notebook, version=NO_CONVERT)
    restored = nbformat.reads(text, as_version=4)
    assert restored == notebook
    assert isinstance(restored.cells[0], NotebookNode)


def test_generic_path_round_trip_adds_newline(tmp_path):
    path = tmp_path / "roundtrip.ipynb"
    notebook = _notebook()
    assert nbformat.write(notebook, path, version=NO_CONVERT) is None
    raw = path.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert nbformat.read(path, as_version=4) == notebook


def test_representative_in_memory_lifecycle():
    notebook = _notebook()
    assert nbformat.validate(notebook) is None
    restored = nbformat.reads(nbformat.writes(notebook), as_version=4)
    notary = NotebookNotary(store_factory=MemorySignatureStore, secret=b"workflow-secret")
    notary.sign(restored)
    trusted = notary.check_signature(restored)
    notary.mark_cells(restored, trusted)
    assert trusted is True
    assert notary.check_cells(restored) is True


def test_representative_file_lifecycle(tmp_path):
    path = tmp_path / "workflow.ipynb"
    notebook = _notebook("total = 40 + 2", "42\n")
    nbformat.write(notebook, path)
    restored = nbformat.read(path, 4)
    restored.metadata.result = 42
    nbformat.write(restored, path)
    final = nbformat.read(path, 4)
    assert final.metadata.result == 42
    assert final.cells[1].outputs[0].text == "42\n"
    assert nbformat.validate(final) is None


def test_representative_conversion_and_trust_lifecycle():
    legacy = nbformat.v3.new_notebook(
        worksheets=[nbformat.v3.new_worksheet(cells=[nbformat.v3.new_code_cell("print(1)")])]
    )
    current = nbformat.convert(legacy, 4)
    restored = nbformat.reads(nbformat.writes(current), 4)
    notary = NotebookNotary(store_factory=MemorySignatureStore, secret=b"converted-secret")
    notary.sign(restored)
    assert current.nbformat == restored.nbformat == 4
    assert restored.cells[0].source == "print(1)"
    assert notary.check_signature(restored) is True


def test_jupyter_trust_help(tmp_path):
    result = subprocess.run([*_trust_command(tmp_path), "--help"], env=_cli_env(tmp_path), text=True, capture_output=True, timeout=30)
    combined = (result.stdout + result.stderr).lower()
    assert result.returncode == 0
    assert "sign" in combined and "--reset" in combined and "jupyter trust" in combined


def test_jupyter_trust_signs_path_and_rejects_missing_path(tmp_path):
    env = _cli_env(tmp_path)
    path = tmp_path / "cli.ipynb"
    nbformat.write(_notebook(), path)
    command = _trust_command(tmp_path)
    signed = subprocess.run([*command, str(path)], env=env, text=True, capture_output=True, timeout=30)
    missing = subprocess.run([*command, str(tmp_path / "missing.ipynb")], env=env, text=True, capture_output=True, timeout=30)
    assert signed.returncode == 0
    assert missing.returncode != 0
    assert nbformat.read(path, 4).cells[1].source == "print('ready')"


def test_jupyter_trust_stdin_success(tmp_path):
    env = _cli_env(tmp_path)
    result = subprocess.run(
        _trust_command(tmp_path),
        input=nbformat.writes(_notebook()),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0
    data_dir = Path(env["JUPYTER_DATA_DIR"])
    assert any(path.is_file() and path.stat().st_size > 0 for path in data_dir.rglob("*"))


def test_v4_code_cell_with_outputs():
    outputs = [
        new_output("stream", text="hello"),
        new_output("execute_result", {"text/plain": "10"}, execution_count=10),
    ]
    cell = new_code_cell(execution_count=10, outputs=outputs)
    assert cell.execution_count == 10
    assert cell.outputs == outputs


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


def _notary():
    return NotebookNotary(store_factory=MemorySignatureStore, secret=b"secret")


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
