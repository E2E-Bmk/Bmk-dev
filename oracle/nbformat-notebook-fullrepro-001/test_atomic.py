# Spec2Repo oracle - atomic tests for nbformat-notebook-fullrepro-001
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
from nbformat.v2 import parse_filename as parse_filename_v2

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
    env.pop("PYTHONPATH", None)
    for name in ("JUPYTER_CONFIG_DIR", "JUPYTER_DATA_DIR", "JUPYTER_RUNTIME_DIR", "IPYTHONDIR"):
        path = tmp_path / name.lower()
        path.mkdir(exist_ok=True)
        env[name] = str(path)
    return env


def _trust_command(tmp_path):
    global _TRUST_COMMAND
    if _TRUST_COMMAND is not None:
        return _TRUST_COMMAND

    assert sys.version_info[:2] == (3, 11)
    assert sys.prefix != sys.base_prefix, "CLI scoring requires an isolated Python environment"
    package_file = Path(nbformat.__file__).resolve()
    project_root = next(
        (
            parent
            for parent in package_file.parents
            if any((parent / marker).is_file() for marker in ("pyproject.toml", "setup.py", "setup.cfg"))
        ),
        None,
    )
    assert project_root is not None, f"no installable project owns {package_file}"

    venv_root = Path(sys.prefix).resolve()
    venv_python = Path(sys.executable)
    scripts_dir = venv_python.parent
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--force-reinstall",
            "--no-deps",
            str(project_root),
        ],
        check=True,
        text=True,
        capture_output=True,
        timeout=120,
    )

    probe = subprocess.run(
        [
            str(venv_python),
            "-c",
            (
                "import json, sys; from importlib.metadata import distribution; "
                "from pathlib import Path; import nbformat; "
                "d=distribution('nbformat'); "
                "ep=next(e for e in d.entry_points if e.group=='console_scripts' and e.name=='jupyter-trust'); "
                "print(json.dumps({'package_file': str(Path(nbformat.__file__).resolve()), "
                "'prefix': str(Path(sys.prefix).resolve()), 'entry_point': ep.value}))"
            ),
        ],
        env=_cli_env(tmp_path),
        check=True,
        text=True,
        capture_output=True,
        timeout=30,
    )
    provenance = json.loads(probe.stdout)
    installed_package = Path(provenance["package_file"])
    script = scripts_dir / ("jupyter-trust.exe" if os.name == "nt" else "jupyter-trust")
    assert Path(provenance["prefix"]) == venv_root
    assert installed_package.is_relative_to(venv_root)
    assert script.is_file() and script.resolve().is_relative_to(venv_root)
    assert provenance["entry_point"]
    print(
        "CLI_PROVENANCE "
        + json.dumps(
            {
                **provenance,
                "project_root": str(project_root),
                "script": str(script.resolve()),
            },
            sort_keys=True,
        )
    )
    _TRUST_COMMAND = [str(script)]
    return _TRUST_COMMAND


def test_notebooknode_update_accepts_dictionary_patterns():
    node = NotebookNode()
    node.update({"a": {"x": 1}})
    node.update([("b", {"y": 2})])
    node.update(c={"z": 3})
    assert (node.a.x, node.b.y, node.c.z) == (1, 2, 3)
    with pytest.raises(TypeError):
        node.update({"d": 4}, {"e": 5})


def test_from_dict_converts_lists_tuples_and_scalars():
    converted = from_dict([{"a": 1}, ({"b": 2},)])
    assert isinstance(converted, list)
    assert converted[0].a == 1
    assert converted[1][0].b == 2
    marker = object()
    assert from_dict(marker) is marker


def test_convert_existing_major_is_same_object():
    notebook = _notebook()
    converted = nbformat.convert(notebook, 4)
    assert converted is notebook
    converted.metadata.answer = 42
    assert notebook.metadata.answer == 42


def test_convert_unknown_version_raises_value_error():
    with pytest.raises(ValueError):
        nbformat.convert(_notebook(), 99)


def test_validation_accepts_nbjson_alias_and_requires_input():
    notebook = _notebook()
    assert nbformat.validate(nbjson=notebook) is None
    assert nbformat.validate(notebook, version=4, version_minor=notebook.nbformat_minor) is None
    with pytest.raises(TypeError):
        nbformat.validate()


def test_isvalid_reports_schema_result_without_mutation():
    valid = _notebook()
    invalid = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": [{"id": "ok", "cell_type": "code", "metadata": {}, "source": "", "outputs": [], "execution_count": "bad"}]}
    before = json.loads(json.dumps(invalid))
    assert isvalid(valid) is True
    assert isvalid(invalid) is False
    assert invalid == before


def test_iter_validate_returns_validation_errors():
    invalid = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": [{"id": "ok", "cell_type": "code", "metadata": {}, "source": "", "outputs": [], "execution_count": "bad"}]}
    errors = list(iter_validate(nbjson=invalid))
    assert errors
    assert all(isinstance(error, ValidationError) for error in errors)


def test_v4_constructors_supply_valid_defaults():
    cells = [v4.new_code_cell(), v4.new_markdown_cell(), v4.new_raw_cell()]
    notebook = v4.new_notebook(cells=cells)
    assert notebook.nbformat == v4.nbformat == 4
    assert notebook.nbformat_minor == v4.nbformat_minor
    assert cells[0].execution_count is None and cells[0].outputs == []
    assert [cell.cell_type for cell in cells] == ["code", "markdown", "raw"]
    assert all(1 <= len(cell.id) <= 64 for cell in cells)
    assert nbformat.validate(notebook) is None


def test_v4_new_output_defaults_and_invalid_type():
    stream = v4.new_output("stream")
    display = v4.new_output("display_data")
    result = v4.new_output("execute_result")
    error = v4.new_output("error")
    assert (stream.name, stream.text) == ("stdout", "")
    assert display.data == {} and display.metadata == {}
    assert result.execution_count is None and result.data == {}
    assert (error.ename, error.evalue, error.traceback) == ("NotImplementedError", "", [])
    with pytest.raises(ValidationError):
        v4.new_output("stream", name=3)


def test_output_from_msg_converts_execute_result():
    msg = {"header": {"msg_type": "execute_result"}, "content": {"data": {"text/plain": "7"}, "metadata": {}, "execution_count": 2}}
    output = v4.output_from_msg(msg)
    assert output.output_type == "execute_result"
    assert output.execution_count == 2
    assert output.data["text/plain"] == "7"


def test_output_from_msg_converts_stream_display_and_error():
    stream = v4.output_from_msg({"header": {"msg_type": "stream"}, "content": {"name": "stderr", "text": "oops"}})
    display = v4.output_from_msg({"header": {"msg_type": "display_data"}, "content": {"data": {"text/plain": "x"}, "metadata": {}, "transient": {"display_id": "d"}}})
    error = v4.output_from_msg({"header": {"msg_type": "error"}, "content": {"ename": "E", "evalue": "bad", "traceback": ["line"]}})
    assert (stream.output_type, stream.name, stream.text) == ("stream", "stderr", "oops")
    assert display.output_type == "display_data" and display.data["text/plain"] == "x"
    assert (error.output_type, error.ename, error.traceback) == ("error", "E", ["line"])
    with pytest.raises(ValueError):
        v4.output_from_msg({"header": {"msg_type": "status"}, "content": {}})


def test_dictionary_and_attribute_mutations_share_one_projection():
    notebook = _notebook()
    notebook["metadata"]["owner"] = {"name": "Ada"}
    assert notebook.metadata.owner.name == "Ada"
    notebook.metadata.owner.name = "Grace"
    assert notebook["metadata"]["owner"]["name"] == "Grace"


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


def test_v4_stream_override():
    output = new_output("stream", name="stderr", text="hello there")
    assert output.name == "stderr"
    assert output.text == "hello there"


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


def test_v2_parse_filename_adds_json_notebook_extension():
    assert parse_filename_v2("legacy") == ("legacy.ipynb", "legacy", "json")


def _notary():
    return NotebookNotary(store_factory=MemorySignatureStore, secret=b"secret")


def test_notary_secret_changes_signature():
    nb = new_notebook(cells=[new_code_cell("1 + 1")])
    first = _notary().compute_signature(nb)
    second = NotebookNotary(store_factory=MemorySignatureStore, secret=b"other").compute_signature(nb)
    assert first != second


def test_memory_signature_store_lifecycle():
    store = MemorySignatureStore()
    digest = "0123456789abcdef"
    algorithm = "sha256"
    assert store.check_signature(digest, algorithm) is False
    store.store_signature(digest, algorithm)
    assert store.check_signature(digest, algorithm) is True
    store.remove_signature(digest, algorithm)
    assert store.check_signature(digest, algorithm) is False
