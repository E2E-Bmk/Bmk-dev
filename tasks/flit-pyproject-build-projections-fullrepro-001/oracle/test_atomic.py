from __future__ import annotations

import base64
import csv
import hashlib
import io
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

import pytest


def _build_wheel(project, output, monkeypatch, *, editable=False):
    from flit_core import buildapi

    monkeypatch.chdir(project["root"])
    output.mkdir()
    if editable:
        filename = buildapi.build_editable(str(output))
    else:
        filename = buildapi.build_wheel(str(output))
    return output / filename


def _build_sdist(project, output, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(project["root"])
    output.mkdir()
    filename = buildapi.build_sdist(str(output))
    return output / filename


def _dist_info_name(names):
    return next(name for name in names if ".dist-info/" in name)


def _metadata_from_wheel(path):
    with zipfile.ZipFile(path) as archive:
        name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        return Parser().parsestr(archive.read(name).decode("utf-8"))


def _wheel_record(path):
    with zipfile.ZipFile(path) as archive:
        record_name = next(name for name in archive.namelist() if name.endswith("/RECORD"))
        rows = list(csv.reader(io.StringIO(archive.read(record_name).decode("utf-8"))))
    return rows


def _record_digest(data):
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return "sha256=" + digest.decode("ascii")


def test_static_build_hooks_report_no_extra_requirements(static_project, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])

    assert buildapi.get_requires_for_build_wheel() == []
    assert buildapi.get_requires_for_build_editable() == []
    assert buildapi.get_requires_for_build_sdist() == []


def test_prepare_metadata_returns_dist_info_directory(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()

    dirname = buildapi.prepare_metadata_for_build_wheel(str(metadata_dir))

    assert dirname == "aurora_tools-1.2.3.dist-info"
    assert (metadata_dir / dirname / "METADATA").is_file()
    assert (metadata_dir / dirname / "WHEEL").is_file()


def test_prepared_metadata_exposes_project_identity(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    dirname = buildapi.prepare_metadata_for_build_wheel(str(metadata_dir))
    message = Parser().parsestr(
        (metadata_dir / dirname / "METADATA").read_text(encoding="utf-8")
    )

    assert message["Name"] == "aurora-tools"
    assert message["Version"] == "1.2.3"
    assert message["Summary"] == "Aurora static toolkit."


def test_prepared_metadata_contains_readme_description(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    dirname = buildapi.prepare_metadata_for_build_wheel(str(metadata_dir))
    text = (metadata_dir / dirname / "METADATA").read_text(encoding="utf-8")

    assert "Description-Content-Type: text/markdown" in text
    assert "\n# Aurora Tools\n\nA longer project description.\n" in text


def test_prepared_metadata_contains_authors_and_dependencies(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    dirname = buildapi.prepare_metadata_for_build_wheel(str(metadata_dir))
    message = Parser().parsestr(
        (metadata_dir / dirname / "METADATA").read_text(encoding="utf-8")
    )

    assert message["Author"] == "Ada Lovelace"
    assert message["Author-email"] == "ada@example.test"
    assert message["Maintainer"] == "Grace Hopper"
    assert message["Maintainer-email"] == "grace@example.test"
    assert message.get_all("Requires-Dist") == [
        "tomli >= 2",
        'click >= 8 ; extra == "cli"',
    ]


def test_prepared_metadata_contains_urls_and_license(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    dirname = buildapi.prepare_metadata_for_build_wheel(str(metadata_dir))
    text = (metadata_dir / dirname / "METADATA").read_text(encoding="utf-8")

    assert "License-Expression: MIT" in text
    assert "License-File: LICENSE" in text
    assert "Project-URL: Documentation, https://docs.example.test/aurora" in text
    assert "Project-URL: Source, https://code.example.test/aurora" in text


def test_prepared_metadata_writes_scripts_and_entry_points(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    dirname = buildapi.prepare_metadata_for_build_wheel(str(metadata_dir))
    entry_points = (metadata_dir / dirname / "entry_points.txt").read_text(encoding="utf-8")

    assert "[aurora.plugins]\njson=aurora_tools.plugins:json_plugin\n" in entry_points
    assert "[console_scripts]\naurora=aurora_tools.cli:main\n" in entry_points
    assert "[gui_scripts]\naurora-gui=aurora_tools.cli:main\n" in entry_points


def test_wheel_filename_normalizes_distribution_name(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    assert wheel.name == "aurora_tools-1.2.3-py3-none-any.whl"


def test_wheel_contains_package_files(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    assert {
        "aurora_tools/__init__.py",
        "aurora_tools/cli.py",
        "aurora_tools/plugins.py",
        "aurora_tools/data.json",
        "aurora_tools/nested/info.txt",
    } <= names
    assert "aurora_tools/__pycache__/ignored.pyc" not in names


def test_wheel_contains_external_data_mapping(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        data_path = "aurora_tools-1.2.3.data/data/share/config.ini"
        assert archive.read(data_path) == b"[fixture]\nvalue = seven\n"


def test_wheel_contains_license_file(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        assert archive.read("aurora_tools-1.2.3.dist-info/licenses/LICENSE") == (
            b"MIT license text for the fixture.\n"
        )


def test_wheel_metadata_declares_pure_python_tag(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        wheel_text = archive.read("aurora_tools-1.2.3.dist-info/WHEEL").decode("utf-8")

    assert "Wheel-Version: 1.0\n" in wheel_text
    assert "Root-Is-Purelib: true\n" in wheel_text
    assert "Tag: py3-none-any\n" in wheel_text


def test_wheel_record_lists_every_archive_member(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        archive_names = set(archive.namelist())
    record_paths = {row[0] for row in _wheel_record(wheel)}

    assert record_paths == archive_names


def test_wheel_record_hashes_match_archive_bytes(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    rows = _wheel_record(wheel)

    for path, digest, size in rows:
        if path.endswith("/RECORD"):
            assert digest == ""
            assert size == ""
        else:
            assert digest == _record_digest(members[path])
            assert size == str(len(members[path]))


def test_editable_wheel_uses_source_path_file(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(
        static_project,
        tmp_path / "editable",
        monkeypatch,
        editable=True,
    )

    with zipfile.ZipFile(wheel) as archive:
        pth_text = archive.read("aurora_tools.pth").decode("utf-8")

    assert pth_text == str(static_project["root"].resolve())


def test_editable_wheel_omits_copied_package_files(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(
        static_project,
        tmp_path / "editable",
        monkeypatch,
        editable=True,
    )

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    assert "aurora_tools.pth" in names
    assert "aurora_tools/__init__.py" not in names
    assert "aurora_tools-1.2.3.dist-info/METADATA" in names


def test_sdist_has_normalized_filename_and_single_root(static_project, tmp_path, monkeypatch):
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)

    assert sdist.name == "aurora_tools-1.2.3.tar.gz"
    with tarfile.open(sdist, "r:gz") as archive:
        roots = {member.name.split("/", 1)[0] for member in archive.getmembers()}
    assert roots == {"aurora_tools-1.2.3"}


def test_sdist_contains_build_inputs_and_package_files(static_project, tmp_path, monkeypatch):
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)

    with tarfile.open(sdist, "r:gz") as archive:
        names = {member.name for member in archive.getmembers()}

    prefix = "aurora_tools-1.2.3/"
    assert {
        prefix + "pyproject.toml",
        prefix + "README.md",
        prefix + "LICENSE",
        prefix + "aurora_tools/__init__.py",
        prefix + "data/share/config.ini",
        prefix + "PKG-INFO",
    } <= names


def test_sdist_excludes_bytecode_cache(static_project, tmp_path, monkeypatch):
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)

    with tarfile.open(sdist, "r:gz") as archive:
        names = {member.name for member in archive.getmembers()}

    assert all("__pycache__" not in name and not name.endswith(".pyc") for name in names)


def test_editable_metadata_hook_creates_metadata(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(static_project["root"])
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()

    dirname = buildapi.prepare_metadata_for_build_editable(str(metadata_dir))

    assert dirname == "aurora_tools-1.2.3.dist-info"
    assert (metadata_dir / dirname / "METADATA").is_file()


def test_src_layout_wheel_uses_configured_module(src_project, tmp_path, monkeypatch):
    wheel = _build_wheel(src_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    assert "actual_pkg/__init__.py" in names
    assert "src_distribution-1.2.3.dist-info/METADATA" in names
    assert "src_distribution.py" not in names


def test_namespace_layout_wheel_preserves_package_path(namespace_project, tmp_path, monkeypatch):
    wheel = _build_wheel(namespace_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata = archive.read("acme_widgets-1.2.3.dist-info/METADATA").decode("utf-8")

    assert "acme/widgets/__init__.py" in names
    assert "Import-Name: acme.widgets" in metadata
    assert "Import-Namespace: acme" in metadata


def test_dynamic_metadata_reads_module_docstring_and_version(dynamic_project, tmp_path, monkeypatch):
    wheel = _build_wheel(dynamic_project, tmp_path / "wheel", monkeypatch)
    metadata = _metadata_from_wheel(wheel)

    assert metadata["Name"] == "aurora-tools"
    assert metadata["Version"] == "2.4.1"
    assert metadata["Summary"] == "Aurora dynamic toolkit."


def test_dynamic_build_hooks_need_no_extra_requirements(dynamic_project, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(dynamic_project["root"])

    assert buildapi.get_requires_for_build_wheel() == []
    assert buildapi.get_requires_for_build_editable() == []
    assert buildapi.get_requires_for_build_sdist() == []


def test_inline_readme_and_license_file_are_serialized(
    inline_metadata_project, tmp_path, monkeypatch
):
    wheel = _build_wheel(inline_metadata_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        metadata = archive.read("aurora_tools-1.2.3.dist-info/METADATA").decode("utf-8")
        license_text = archive.read("aurora_tools-1.2.3.dist-info/licenses/COPYING.txt")

    assert "Description-Content-Type: text/markdown" in metadata
    assert "\n# Inline Aurora\n" in metadata
    assert "License-File: COPYING.txt" in metadata
    assert license_text == b"Copyright 2026 Aurora\n"


def test_sdist_include_and_exclude_patterns(rules_project, tmp_path, monkeypatch):
    sdist = _build_sdist(rules_project, tmp_path / "sdist", monkeypatch)

    with tarfile.open(sdist, "r:gz") as archive:
        names = {member.name for member in archive.getmembers()}

    assert "aurora_tools-1.2.3/docs/guide.md" in names
    assert "aurora_tools-1.2.3/docs/skip.md" not in names


def test_wheel_normalizes_non_executable_permissions(static_project, tmp_path, monkeypatch):
    static_project["package_data"].chmod(0o600)
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        mode = (archive.getinfo("aurora_tools/data.json").external_attr >> 16) & 0o777
    assert mode == 0o644


def test_wheel_normalizes_executable_permissions(static_project, tmp_path, monkeypatch):
    static_project["package_data"].chmod(0o700)
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        mode = (archive.getinfo("aurora_tools/data.json").external_attr >> 16) & 0o777
    assert mode == 0o755


def test_buildapi_wheel_is_a_valid_zip_archive(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    assert zipfile.is_zipfile(wheel)
    with zipfile.ZipFile(wheel) as archive:
        assert archive.testzip() is None


def test_buildapi_sdist_is_a_valid_tar_archive(static_project, tmp_path, monkeypatch):
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)

    assert tarfile.is_tarfile(sdist)
    with tarfile.open(sdist, "r:gz") as archive:
        assert archive.getmember("aurora_tools-1.2.3/PKG-INFO").size > 0
