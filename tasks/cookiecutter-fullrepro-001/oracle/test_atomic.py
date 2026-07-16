# Spec2Repo oracle - atomic tests for cookiecutter-fullrepro-001
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from cookiecutter.main import cookiecutter


def write_template(root: Path, config: dict, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cookiecutter.json").write_text(json.dumps(config), encoding="utf-8")
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def test_jsonify_extension_is_available_without_configuration(tmp_path):
    template = write_template(
        tmp_path / "template",
        {"project_slug": "json_demo", "data": {"a": 1}},
        {"{{cookiecutter.project_slug}}/data.json": "{{ cookiecutter.data | jsonify }}\n"},
    )

    cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))

    data = json.loads((tmp_path / "out" / "json_demo" / "data.json").read_text(encoding="utf-8"))
    assert data == {"a": "1"}


def test_random_string_extension_generates_requested_length(tmp_path):
    template = write_template(
        tmp_path / "template",
        {"project_slug": "random_demo"},
        {"{{cookiecutter.project_slug}}/token.txt": "{{ random_ascii_string(12) }}\n"},
    )

    cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))

    token = (tmp_path / "out" / "random_demo" / "token.txt").read_text(encoding="utf-8").strip()
    assert len(token) == 12
    assert token.isascii()
