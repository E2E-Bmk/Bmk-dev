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


def test_copy_without_render_preserves_raw_jinja_content(tmp_path):
    template = write_template(
        tmp_path / "template",
        {"project_slug": "demo", "_copy_without_render": ["*.txt"]},
        {
            "{{cookiecutter.project_slug}}/rendered.md": "{{ cookiecutter.project_slug }}\n",
            "{{cookiecutter.project_slug}}/raw.txt": "{{ cookiecutter.project_slug }}\n",
        },
    )

    cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))

    project = tmp_path / "out" / "demo"
    assert (project / "rendered.md").read_text(encoding="utf-8") == "demo\n"
    assert (project / "raw.txt").read_text(encoding="utf-8") == "{{ cookiecutter.project_slug }}\n"


def test_replay_file_reuses_recorded_answers(tmp_path):
    template = write_template(
        tmp_path / "template",
        {"project_slug": "demo"},
        {"{{cookiecutter.project_slug}}/name.txt": "{{ cookiecutter.project_slug }}\n"},
    )
    replay = tmp_path / "replay.json"
    replay.write_text(json.dumps({"cookiecutter": {"project_slug": "from_replay"}}), encoding="utf-8")

    cookiecutter(str(template), replay=str(replay), output_dir=str(tmp_path / "out"))

    assert (tmp_path / "out" / "from_replay" / "name.txt").read_text(encoding="utf-8") == "from_replay\n"


def test_directory_option_selects_template_subdirectory(tmp_path):
    repo = tmp_path / "repo"
    write_template(
        repo / "nested",
        {"project_slug": "nested_demo"},
        {"{{cookiecutter.project_slug}}/selected.txt": "ok\n"},
    )
    (repo / "ignored.txt").write_text("ignored\n", encoding="utf-8")

    cookiecutter(str(repo), no_input=True, directory="nested", output_dir=str(tmp_path / "out"))

    assert (tmp_path / "out" / "nested_demo" / "selected.txt").read_text(encoding="utf-8") == "ok\n"


def test_zip_archive_template_generates_project(tmp_path):
    source = write_template(
        tmp_path / "source",
        {"project_slug": "zip_demo"},
        {"{{cookiecutter.project_slug}}/zip.txt": "{{ cookiecutter.project_slug }}\n"},
    )
    archive = tmp_path / "template.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("template/", "")
        for path in source.rglob("*"):
            if path.is_file():
                zf.write(path, f"template/{path.relative_to(source).as_posix()}")

    cookiecutter(str(archive), no_input=True, output_dir=str(tmp_path / "out"))

    assert (tmp_path / "out" / "zip_demo" / "zip.txt").read_text(encoding="utf-8") == "zip_demo\n"


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


def test_local_extension_filter_can_be_loaded_from_template_root(tmp_path):
    template = write_template(
        tmp_path / "template",
        {"project_slug": "local_demo", "_extensions": ["local_extensions.ReverseExtension"]},
        {
            "local_extensions.py": "from cookiecutter.utils import simple_filter\n\n@simple_filter\ndef reverse(value):\n    return value[::-1]\n\nReverseExtension = reverse\n",
            "{{cookiecutter.project_slug}}/value.txt": "{{ 'abc' | reverse }}\n",
        },
    )

    cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))

    assert (tmp_path / "out" / "local_demo" / "value.txt").read_text(encoding="utf-8") == "cba\n"


def test_legacy_template_key_selects_old_nested_template_format(tmp_path):
    repo = tmp_path / "repo"
    write_template(
        repo,
        {"template": ["Old (./old)"]},
        {},
    )
    write_template(
        repo / "old",
        {"project_slug": "old_demo"},
        {"{{cookiecutter.project_slug}}/old.txt": "old\n"},
    )

    cookiecutter(str(repo), no_input=True, output_dir=str(tmp_path / "out"))

    assert (tmp_path / "out" / "old_demo" / "old.txt").read_text(encoding="utf-8") == "old\n"


def test_cli_version_reports_cookiecutter_entry_point():
    result = subprocess.run(
        [sys.executable, "-m", "cookiecutter", "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Cookiecutter" in result.stdout or "cookiecutter" in result.stdout
