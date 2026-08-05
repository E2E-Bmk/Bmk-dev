from __future__ import annotations

import csv
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
    builder = buildapi.build_editable if editable else buildapi.build_wheel
    return output / builder(str(output))


def _build_sdist(project, output, monkeypatch):
    from flit_core import buildapi

    monkeypatch.chdir(project["root"])
    output.mkdir()
    return output / buildapi.build_sdist(str(output))


def _wheel_metadata(path):
    with zipfile.ZipFile(path) as archive:
        name = next(name for name in archive.namelist() if name.endswith("/METADATA"))
        return Parser().parsestr(archive.read(name).decode("utf-8"))


def _wheel_dist_info(path):
    with zipfile.ZipFile(path) as archive:
        return next(name.split("/", 1)[0] for name in archive.namelist() if name.endswith("/METADATA"))


def _sdist_members(path):
    with tarfile.open(path, "r:gz") as archive:
        return {member.name for member in archive.getmembers()}


@pytest.mark.depends_on(
    "test_prepare_metadata_returns_dist_info_directory",
    "test_wheel_filename_normalizes_distribution_name",
)
def test_wheel_metadata_matches_prepared_metadata(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)
    metadata_dir = tmp_path / "prepared"
    metadata_dir.mkdir()
    monkeypatch.chdir(static_project["root"])
    dirname = buildapi.prepare_metadata_for_build_wheel(str(metadata_dir))
    built = _wheel_metadata(wheel)
    prepared = Parser().parsestr(
        (metadata_dir / dirname / "METADATA").read_text(encoding="utf-8")
    )

    assert built.as_string() == prepared.as_string()


@pytest.mark.depends_on(
    "test_sdist_has_normalized_filename_and_single_root",
    "test_prepared_metadata_exposes_project_identity",
)
def test_wheel_metadata_matches_sdist_pkg_info(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)

    with tarfile.open(sdist, "r:gz") as archive:
        pkg_info = archive.extractfile("aurora_tools-1.2.3/PKG-INFO").read()
    wheel_metadata = _wheel_metadata(wheel)
    sdist_metadata = Parser().parsestr(pkg_info.decode("utf-8"))

    for field in ("Name", "Version", "Summary", "Requires-Python", "License-Expression"):
        assert wheel_metadata[field] == sdist_metadata[field]
    assert wheel_metadata.get_all("Requires-Dist") == sdist_metadata.get_all("Requires-Dist")


@pytest.mark.depends_on(
    "test_wheel_record_lists_every_archive_member",
    "test_wheel_contains_external_data_mapping",
)
def test_wheel_record_covers_license_and_external_data(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        record_name = "aurora_tools-1.2.3.dist-info/RECORD"
        rows = list(csv.reader(io.StringIO(archive.read(record_name).decode("utf-8"))))
        by_path = {row[0]: row for row in rows}

    assert by_path["aurora_tools-1.2.3.dist-info/licenses/LICENSE"][1].startswith("sha256=")
    assert by_path["aurora_tools-1.2.3.data/data/share/config.ini"][2] == "24"


@pytest.mark.depends_on(
    "test_wheel_record_hashes_match_archive_bytes",
    "test_wheel_contains_package_files",
)
def test_wheel_record_reconstructs_package_file_projection(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        rows = list(
            csv.reader(
                io.StringIO(
                    archive.read("aurora_tools-1.2.3.dist-info/RECORD").decode("utf-8")
                )
            )
        )
        package_paths = {
            row[0]
            for row in rows
            if row[0].startswith("aurora_tools/") and not row[0].endswith(".pyc")
        }

    assert package_paths == {
        "aurora_tools/__init__.py",
        "aurora_tools/cli.py",
        "aurora_tools/plugins.py",
        "aurora_tools/data.json",
        "aurora_tools/nested/info.txt",
    }


@pytest.mark.depends_on(
    "test_editable_wheel_uses_source_path_file",
    "test_editable_wheel_omits_copied_package_files",
)
def test_regular_and_editable_wheels_project_two_install_modes(static_project, tmp_path, monkeypatch):
    regular = _build_wheel(static_project, tmp_path / "regular", monkeypatch)
    editable = _build_wheel(static_project, tmp_path / "editable", monkeypatch, editable=True)

    with zipfile.ZipFile(regular) as regular_archive, zipfile.ZipFile(editable) as editable_archive:
        regular_names = set(regular_archive.namelist())
        editable_names = set(editable_archive.namelist())

    assert "aurora_tools/__init__.py" in regular_names
    assert "aurora_tools/__init__.py" not in editable_names
    assert "aurora_tools.pth" in editable_names
    assert {
        "aurora_tools-1.2.3.dist-info/METADATA",
        "aurora_tools-1.2.3.dist-info/WHEEL",
    } <= regular_names & editable_names


@pytest.mark.depends_on(
    "test_sdist_contains_build_inputs_and_package_files",
    "test_wheel_contains_package_files",
)
def test_sdist_can_feed_a_second_backend_wheel(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with tarfile.open(sdist, "r:gz") as archive:
        archive.extractall(extracted)
    source_root = extracted / "aurora_tools-1.2.3"
    output = tmp_path / "rebuilt"
    output.mkdir()
    monkeypatch.chdir(source_root)
    rebuilt = output / buildapi.build_wheel(str(output))

    original = _build_wheel(static_project, tmp_path / "original", monkeypatch)
    with zipfile.ZipFile(original) as original_archive, zipfile.ZipFile(rebuilt) as rebuilt_archive:
        assert set(original_archive.namelist()) == set(rebuilt_archive.namelist())
        assert original_archive.read("aurora_tools/data.json") == rebuilt_archive.read(
            "aurora_tools/data.json"
        )


@pytest.mark.depends_on(
    "test_sdist_contains_build_inputs_and_package_files",
    "test_wheel_contains_package_files",
)
def test_sdist_roundtrip_preserves_package_file_bytes(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with tarfile.open(sdist, "r:gz") as archive:
        archive.extractall(extracted)
    source_root = extracted / "aurora_tools-1.2.3"
    rebuilt_dir = tmp_path / "rebuilt"
    rebuilt_dir.mkdir()
    monkeypatch.chdir(source_root)
    rebuilt = rebuilt_dir / buildapi.build_wheel(str(rebuilt_dir))
    original = _build_wheel(static_project, tmp_path / "original", monkeypatch)

    package_paths = {
        "aurora_tools/__init__.py",
        "aurora_tools/cli.py",
        "aurora_tools/plugins.py",
        "aurora_tools/data.json",
        "aurora_tools/nested/info.txt",
    }
    with zipfile.ZipFile(original) as original_archive, zipfile.ZipFile(rebuilt) as rebuilt_archive:
        for path in package_paths:
            assert original_archive.read(path) == rebuilt_archive.read(path)


@pytest.mark.depends_on(
    "test_prepare_metadata_returns_dist_info_directory",
    "test_wheel_filename_normalizes_distribution_name",
)
def test_build_wheel_accepts_prepared_metadata_directory(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    prepared_dir = tmp_path / "prepared"
    wheel_dir = tmp_path / "wheel"
    prepared_dir.mkdir()
    wheel_dir.mkdir()
    monkeypatch.chdir(static_project["root"])
    dirname = buildapi.prepare_metadata_for_build_wheel(str(prepared_dir))
    wheel = wheel_dir / buildapi.build_wheel(
        str(wheel_dir),
        metadata_directory=str(prepared_dir / dirname),
    )

    prepared_metadata = (prepared_dir / dirname / "METADATA").read_bytes()
    with zipfile.ZipFile(wheel) as archive:
        built_metadata = archive.read("aurora_tools-1.2.3.dist-info/METADATA")

    assert wheel.name == "aurora_tools-1.2.3-py3-none-any.whl"
    assert built_metadata == prepared_metadata


@pytest.mark.depends_on(
    "test_editable_metadata_hook_creates_metadata",
    "test_editable_wheel_omits_copied_package_files",
)
def test_editable_prepared_metadata_matches_built_editable_wheel(
    static_project, tmp_path, monkeypatch
):
    from flit_core import buildapi

    prepared_dir = tmp_path / "prepared-editable"
    prepared_dir.mkdir()
    monkeypatch.chdir(static_project["root"])
    dirname = buildapi.prepare_metadata_for_build_editable(str(prepared_dir))
    editable = _build_wheel(
        static_project,
        tmp_path / "editable",
        monkeypatch,
        editable=True,
    )

    prepared_metadata = (prepared_dir / dirname / "METADATA").read_bytes()
    with zipfile.ZipFile(editable) as archive:
        built_metadata = archive.read("aurora_tools-1.2.3.dist-info/METADATA")
        names = set(archive.namelist())

    assert built_metadata == prepared_metadata
    assert "aurora_tools.pth" in names


@pytest.mark.depends_on(
    "test_wheel_filename_normalizes_distribution_name",
    "test_wheel_contains_package_files",
)
def test_cli_wheel_only_matches_backend_projection(static_project, tmp_path, monkeypatch):
    from flit import main

    monkeypatch.chdir(static_project["root"])
    main(
        [
            "-f",
            str(static_project["pyproject"]),
            "build",
            "--no-use-vcs",
            "--format",
            "wheel",
        ]
    )
    cli_wheel = next((static_project["root"] / "dist").glob("*.whl"))
    backend_wheel = _build_wheel(static_project, tmp_path / "backend", monkeypatch)

    assert cli_wheel.name == backend_wheel.name
    with zipfile.ZipFile(cli_wheel) as cli_archive, zipfile.ZipFile(backend_wheel) as backend_archive:
        assert cli_archive.read("aurora_tools/data.json") == backend_archive.read(
            "aurora_tools/data.json"
        )
        assert cli_archive.read("aurora_tools-1.2.3.dist-info/METADATA") == backend_archive.read(
            "aurora_tools-1.2.3.dist-info/METADATA"
        )


@pytest.mark.depends_on(
    "test_sdist_has_normalized_filename_and_single_root",
    "test_sdist_contains_build_inputs_and_package_files",
)
def test_cli_sdist_only_matches_backend_projection(static_project, tmp_path, monkeypatch):
    from flit import main

    monkeypatch.chdir(static_project["root"])
    main(
        [
            "-f",
            str(static_project["pyproject"]),
            "build",
            "--no-use-vcs",
            "--format",
            "sdist",
        ]
    )
    cli_sdist = next((static_project["root"] / "dist").glob("*.tar.gz"))
    backend_sdist = _build_sdist(static_project, tmp_path / "backend", monkeypatch)

    assert cli_sdist.name == backend_sdist.name
    assert _sdist_members(cli_sdist) == _sdist_members(backend_sdist)


@pytest.mark.depends_on(
    "test_wheel_filename_normalizes_distribution_name",
    "test_sdist_has_normalized_filename_and_single_root",
)
def test_cli_default_build_produces_both_projections(static_project, monkeypatch):
    from flit import main

    monkeypatch.chdir(static_project["root"])
    main(["-f", str(static_project["pyproject"]), "build", "--no-use-vcs"])

    dist_names = {path.name for path in (static_project["root"] / "dist").iterdir()}
    assert dist_names == {
        "aurora_tools-1.2.3-py3-none-any.whl",
        "aurora_tools-1.2.3.tar.gz",
    }


@pytest.mark.depends_on("test_static_build_hooks_report_no_extra_requirements")
def test_cli_help_exposes_build_and_publish_commands(capsys):
    from flit import main

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "build" in output
    assert "publish" in output


@pytest.mark.depends_on("test_static_build_hooks_report_no_extra_requirements")
def test_cli_version_reports_public_version(capsys):
    from flit import main

    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == "Flit 4.0.0"


@pytest.mark.depends_on(
    "test_src_layout_wheel_uses_configured_module",
    "test_sdist_has_normalized_filename_and_single_root",
)
def test_src_layout_sdist_and_wheel_share_distribution_identity(src_project, tmp_path, monkeypatch):
    wheel = _build_wheel(src_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(src_project, tmp_path / "sdist", monkeypatch)

    assert wheel.name.startswith("src_distribution-1.2.3-")
    assert sdist.name == "src_distribution-1.2.3.tar.gz"
    members = _sdist_members(sdist)
    assert "src_distribution-1.2.3/src/actual_pkg/__init__.py" in members


@pytest.mark.depends_on(
    "test_namespace_layout_wheel_preserves_package_path",
    "test_sdist_contains_build_inputs_and_package_files",
)
def test_namespace_metadata_and_archive_path_agree(namespace_project, tmp_path, monkeypatch):
    wheel = _build_wheel(namespace_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(namespace_project, tmp_path / "sdist", monkeypatch)

    metadata = _wheel_metadata(wheel)
    members = _sdist_members(sdist)
    assert metadata["Name"] == "acme-widgets"
    assert "acme/widgets/__init__.py" in zipfile.ZipFile(wheel).namelist()
    assert "acme_widgets-1.2.3/acme/widgets/__init__.py" in members


@pytest.mark.depends_on(
    "test_dynamic_metadata_reads_module_docstring_and_version",
    "test_dynamic_build_hooks_need_no_extra_requirements",
)
def test_dynamic_metadata_agrees_across_wheel_and_sdist(dynamic_project, tmp_path, monkeypatch):
    wheel = _build_wheel(dynamic_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(dynamic_project, tmp_path / "sdist", monkeypatch)
    with tarfile.open(sdist, "r:gz") as archive:
        pkg_info = archive.extractfile("aurora_tools-2.4.1/PKG-INFO").read()

    wheel_metadata = _wheel_metadata(wheel)
    sdist_metadata = Parser().parsestr(pkg_info.decode("utf-8"))
    assert wheel_metadata["Name"] == sdist_metadata["Name"] == "aurora-tools"
    assert wheel_metadata["Version"] == sdist_metadata["Version"] == "2.4.1"
    assert wheel_metadata["Summary"] == sdist_metadata["Summary"] == "Aurora dynamic toolkit."


@pytest.mark.depends_on("test_dynamic_metadata_reads_module_docstring_and_version")
def test_dynamic_project_wheel_is_reproducible(dynamic_project, tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1609459200")
    first = _build_wheel(dynamic_project, tmp_path / "first", monkeypatch)
    second = _build_wheel(dynamic_project, tmp_path / "second", monkeypatch)

    assert first.read_bytes() == second.read_bytes()


@pytest.mark.depends_on("test_wheel_filename_normalizes_distribution_name")
def test_static_project_wheel_is_reproducible(static_project, tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1609459200")
    first = _build_wheel(static_project, tmp_path / "first", monkeypatch)
    second = _build_wheel(static_project, tmp_path / "second", monkeypatch)

    assert first.read_bytes() == second.read_bytes()


@pytest.mark.depends_on("test_sdist_has_normalized_filename_and_single_root")
def test_static_project_sdist_is_reproducible(static_project, tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1609459200")
    first = _build_sdist(static_project, tmp_path / "first", monkeypatch)
    second = _build_sdist(static_project, tmp_path / "second", monkeypatch)

    assert first.read_bytes() == second.read_bytes()


@pytest.mark.depends_on("test_inline_readme_and_license_file_are_serialized")
def test_license_file_projection_agrees_across_wheel_and_sdist(
    inline_metadata_project, tmp_path, monkeypatch
):
    wheel = _build_wheel(inline_metadata_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(inline_metadata_project, tmp_path / "sdist", monkeypatch)
    with tarfile.open(sdist, "r:gz") as archive:
        metadata = Parser().parsestr(
            archive.extractfile("aurora_tools-1.2.3/PKG-INFO").read().decode("utf-8")
        )
        names = {member.name for member in archive.getmembers()}

    assert "License-File: COPYING.txt" in _wheel_metadata(wheel).as_string()
    assert metadata["License-File"] == "COPYING.txt"
    assert "aurora_tools-1.2.3/COPYING.txt" in names


@pytest.mark.depends_on(
    "test_inline_readme_and_license_file_are_serialized",
    "test_prepared_metadata_exposes_project_identity",
)
def test_inline_readme_projection_agrees_in_metadata_and_pkg_info(
    inline_metadata_project, tmp_path, monkeypatch
):
    wheel = _build_wheel(inline_metadata_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(inline_metadata_project, tmp_path / "sdist", monkeypatch)
    with tarfile.open(sdist, "r:gz") as archive:
        pkg_info = archive.extractfile("aurora_tools-1.2.3/PKG-INFO").read().decode("utf-8")

    wheel_text = _wheel_metadata(wheel).as_string()
    assert "Description-Content-Type: text/markdown" in wheel_text
    assert "\n# Inline Aurora\n" in wheel_text
    assert "\n# Inline Aurora\n" in pkg_info


@pytest.mark.depends_on(
    "test_wheel_contains_external_data_mapping",
    "test_sdist_contains_build_inputs_and_package_files",
)
def test_external_data_projection_agrees_in_wheel_and_sdist(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)

    with zipfile.ZipFile(wheel) as archive:
        wheel_data = archive.read("aurora_tools-1.2.3.data/data/share/config.ini")
    with tarfile.open(sdist, "r:gz") as archive:
        sdist_data = archive.extractfile(
            "aurora_tools-1.2.3/data/share/config.ini"
        ).read()

    assert wheel_data == sdist_data == b"[fixture]\nvalue = seven\n"


@pytest.mark.depends_on("test_sdist_include_and_exclude_patterns")
def test_sdist_rules_keep_only_configured_documentation(rules_project, tmp_path, monkeypatch):
    sdist = _build_sdist(rules_project, tmp_path / "sdist", monkeypatch)
    members = _sdist_members(sdist)

    assert "aurora_tools-1.2.3/docs/guide.md" in members
    assert "aurora_tools-1.2.3/docs/skip.md" not in members
    assert "aurora_tools-1.2.3/docs" not in members


@pytest.mark.depends_on(
    "test_prepared_metadata_writes_scripts_and_entry_points",
    "test_wheel_contains_package_files",
)
def test_entry_points_match_prepared_and_built_metadata(static_project, tmp_path, monkeypatch):
    from flit_core import buildapi

    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)
    prepared_dir = tmp_path / "prepared"
    prepared_dir.mkdir()
    monkeypatch.chdir(static_project["root"])
    dirname = buildapi.prepare_metadata_for_build_wheel(str(prepared_dir))
    prepared = (prepared_dir / dirname / "entry_points.txt").read_bytes()
    with zipfile.ZipFile(wheel) as archive:
        built = archive.read("aurora_tools-1.2.3.dist-info/entry_points.txt")

    assert built == prepared


@pytest.mark.depends_on(
    "test_wheel_record_hashes_match_archive_bytes",
    "test_wheel_contains_license_file",
)
def test_record_digest_cross_view_matches_license_content(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)
    with zipfile.ZipFile(wheel) as archive:
        license_bytes = archive.read("aurora_tools-1.2.3.dist-info/licenses/LICENSE")
        record = archive.read("aurora_tools-1.2.3.dist-info/RECORD").decode("utf-8")

    license_row = next(
        row for row in csv.reader(io.StringIO(record)) if row[0].endswith("/licenses/LICENSE")
    )
    import base64
    import hashlib

    digest = base64.urlsafe_b64encode(hashlib.sha256(license_bytes).digest()).rstrip(b"=")
    assert license_row[1] == "sha256=" + digest.decode("ascii")


@pytest.mark.depends_on(
    "test_wheel_filename_normalizes_distribution_name",
    "test_editable_metadata_hook_creates_metadata",
    "test_sdist_has_normalized_filename_and_single_root",
)
def test_all_backend_outputs_share_normalized_distribution_name(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)
    editable = _build_wheel(static_project, tmp_path / "editable", monkeypatch, editable=True)
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)

    assert _wheel_dist_info(wheel) == "aurora_tools-1.2.3.dist-info"
    assert _wheel_dist_info(editable) == "aurora_tools-1.2.3.dist-info"
    assert sdist.name.startswith("aurora_tools-1.2.3")


@pytest.mark.depends_on(
    "test_sdist_excludes_bytecode_cache",
    "test_wheel_contains_package_files",
)
def test_both_archive_projections_exclude_bytecode_cache(static_project, tmp_path, monkeypatch):
    wheel = _build_wheel(static_project, tmp_path / "wheel", monkeypatch)
    sdist = _build_sdist(static_project, tmp_path / "sdist", monkeypatch)
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())

    sdist_names = _sdist_members(sdist)
    assert all("__pycache__" not in name and not name.endswith(".pyc") for name in wheel_names)
    assert all("__pycache__" not in name and not name.endswith(".pyc") for name in sdist_names)


@pytest.mark.depends_on("test_wheel_filename_normalizes_distribution_name")
def test_cli_wheel_only_leaves_no_sdist(static_project, monkeypatch):
    from flit import main

    monkeypatch.chdir(static_project["root"])
    main(
        [
            "-f",
            str(static_project["pyproject"]),
            "build",
            "--no-use-vcs",
            "--format",
            "wheel",
        ]
    )

    assert [path.suffix for path in (static_project["root"] / "dist").iterdir()] == [".whl"]


@pytest.mark.depends_on("test_sdist_has_normalized_filename_and_single_root")
def test_cli_sdist_only_leaves_no_wheel(static_project, monkeypatch):
    from flit import main

    monkeypatch.chdir(static_project["root"])
    main(
        [
            "-f",
            str(static_project["pyproject"]),
            "build",
            "--no-use-vcs",
            "--format",
            "sdist",
        ]
    )

    assert [path.name for path in (static_project["root"] / "dist").iterdir()] == [
        "aurora_tools-1.2.3.tar.gz"
    ]
