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


def test_convert_existing_major_is_same_object():
    notebook = _notebook()
    converted = nbformat.convert(notebook, 4)
    assert converted is notebook
    converted.metadata.answer = 42
    assert notebook.metadata.answer == 42


def test_convert_v3_notebook_to_v4():
    v3 = nbformat.v3
    legacy = v3.new_notebook(
        worksheets=[v3.new_worksheet(cells=[v3.new_text_cell("markdown", source="legacy")])]
    )
    converted = nbformat.convert(legacy, 4)
    assert converted.nbformat == 4
    assert converted.cells[0].cell_type == "markdown"
    assert converted.cells[0].source == "legacy"


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


def test_normalize_repairs_ids_on_a_deep_copy():
    notebook = _notebook()
    duplicate = notebook.cells[0].id
    notebook.cells[1].id = duplicate
    changes, normalized = normalize(notebook)
    assert changes == 1
    assert notebook.cells[0].id == notebook.cells[1].id
    assert normalized.cells[0].id != normalized.cells[1].id


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


def test_dictionary_and_attribute_mutations_share_one_projection():
    notebook = _notebook()
    notebook["metadata"]["owner"] = {"name": "Ada"}
    assert notebook.metadata.owner.name == "Ada"
    notebook.metadata.owner.name = "Grace"
    assert notebook["metadata"]["owner"]["name"] == "Grace"


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
    result = subprocess.run(
        _trust_command(tmp_path),
        input=nbformat.writes(_notebook()),
        env=_cli_env(tmp_path),
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0
