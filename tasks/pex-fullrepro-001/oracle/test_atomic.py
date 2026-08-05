from __future__ import annotations

import json

import pytest

from pex.layout import Layout
from pex.pex_info import PexInfo

from conftest import (
    SOURCE_MARKER,
    WHEEL_MARKER,
    WHEEL_VERSION,
    assert_main_projection,
    assert_support_cli_projection,
    build_pex,
    pex_root_has_runtime_files,
    read_pex_info_json,
    relative_names,
    run_pex_json,
    zipapp_names,
)


def test_public_import_surface_exposes_layout_and_pex_info():
    assert Layout.for_value("zipapp") is Layout.ZIPAPP
    assert Layout.for_value("packed") is Layout.PACKED
    assert PexInfo.default().build_properties["pex_version"]


def test_layout_for_value_rejects_unknown_layout_name():
    with pytest.raises(ValueError):
        Layout.for_value("unsupported-layout")


def test_default_pex_info_exposes_empty_runtime_projection():
    info = PexInfo.default()

    assert info.entry_point is None
    assert info.script is None
    assert info.inject_args == ()
    assert info.inject_python_args == ()


def test_default_pex_info_exposes_non_venv_distribution_projection():
    info = PexInfo.default()

    assert info.venv is False
    assert info.includes_tools is False
    assert info.distributions == {}


def test_default_pex_info_dump_round_trips_public_build_fields():
    info = PexInfo.default()
    restored = PexInfo.from_json(info.dump())

    assert restored.build_properties == info.build_properties
    assert restored.requirements == info.requirements
    assert restored.distributions == info.distributions


def test_layout_values_have_stable_public_string_projection():
    assert str(Layout.for_value("zipapp")) == "zipapp"
    assert str(Layout.for_value("packed")) == "packed"
    assert str(Layout.for_value("loose")) == "loose"


def test_fixture_support_wheel_has_dist_info_and_console_script(fixture_project):
    names = zipapp_names(fixture_project.wheel)

    assert f"supportlib-{WHEEL_VERSION}.dist-info/METADATA" in names
    assert f"supportlib-{WHEEL_VERSION}.dist-info/entry_points.txt" in names


def test_fixture_source_tree_contains_main_module(fixture_project):
    source = fixture_project.source_root / "demo_app" / "main.py"
    package = fixture_project.source_root / "demo_app" / "__init__.py"

    assert source.is_file()
    assert SOURCE_MARKER in package.read_text(encoding="utf-8")


def test_zipapp_build_embeds_pex_info_and_main_module(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "zipapp-contents")
    names = zipapp_names(pex)

    assert "PEX-INFO" in names
    assert "__main__.py" in names


def test_zipapp_layout_identifies_as_zipapp(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "zipapp-layout")

    assert Layout.identify(str(pex)) is Layout.ZIPAPP


def test_packed_layout_identifies_as_packed_directory(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "packed-layout", layout="packed")

    assert pex.is_dir()
    assert Layout.identify(str(pex)) is Layout.PACKED


def test_loose_layout_identifies_as_loose_directory(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "loose-layout", layout="loose")

    assert pex.is_dir()
    assert Layout.identify_original(str(pex)) is Layout.LOOSE


def test_pex_info_from_zipapp_reads_entry_point_and_build_properties(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "entry-info")
    info = PexInfo.from_pex(str(pex))

    assert info.entry_point == "demo_app.main:main"
    assert info.build_properties["pex_version"]


def test_pex_info_roundtrip_from_json_preserves_injected_arguments(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "inject-info",
        inject_args=("--mode", "atomic"),
        inject_python_args=("-X", "dev"),
    )
    raw = json.dumps(read_pex_info_json(pex))
    info = PexInfo.from_json(raw)

    assert info.inject_args == ("--mode", "atomic")
    assert info.inject_python_args == ("-X", "dev")


def test_zipapp_pex_info_lists_local_wheel_distribution(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "dist-info")
    info = PexInfo.from_pex(str(pex))

    assert any(name.startswith(f"supportlib-{WHEEL_VERSION}-") for name in info.distributions)


def test_zipapp_archive_contains_source_package_files(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "source-files")
    names = zipapp_names(pex)

    assert "demo_app/__init__.py" in names
    assert "demo_app/main.py" in names


def test_zipapp_archive_contains_dependency_wheel_projection(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "wheel-projection")
    names = zipapp_names(pex)

    assert any(name.startswith(f".deps/supportlib-{WHEEL_VERSION}-") for name in names)


def test_entry_point_execution_returns_source_and_wheel_markers(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "entry-run")
    report = run_pex_json(pex)

    assert_main_projection(report)


def test_console_script_execution_returns_wheel_marker(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "script-run",
        script="support-cli",
        include_source=False,
    )
    report = run_pex_json(pex)

    assert_support_cli_projection(report)


def test_injected_application_args_are_visible_to_entry_point(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "app-args",
        inject_args=("--color", "blue"),
    )
    report = run_pex_json(pex)

    assert_main_projection(report, argv=["--color", "blue"])


def test_injected_python_args_enable_dev_mode(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "python-args",
        inject_python_args=("-X", "dev"),
    )
    report = run_pex_json(pex)

    assert_main_projection(report, dev_mode=True)


def test_runtime_pex_root_gets_files_after_zipapp_execution(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "runtime-root")
    pex_root = tmp_path / "runner-pex-root"
    report = run_pex_json(pex, pex_root=pex_root)

    assert_main_projection(report)
    assert pex_root_has_runtime_files(pex_root)


def test_venv_mode_records_venv_flag_in_pex_info(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "venv-info", venv=True)
    info = PexInfo.from_pex(str(pex))

    assert info.venv is True
    assert info.includes_tools is True


def test_venv_mode_executes_with_prefix_under_custom_pex_root(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "venv-run", venv=True)
    pex_root = tmp_path / "venv-pex-root"
    report = run_pex_json(pex, pex_root=pex_root)

    assert_main_projection(report, prefix_has_venvs_segment=True)
    assert pex_root_has_runtime_files(pex_root)


def test_packed_layout_contains_top_level_main_and_pex_info(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "packed-files", layout="packed")
    names = relative_names(pex)

    assert "__main__.py" in names
    assert "PEX-INFO" in names
    assert ".bootstrap" in names


def test_loose_layout_contains_layout_marker_and_source_files(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "loose-files", layout="loose")
    names = relative_names(pex)

    assert "PEX-INFO" in names
    assert "__main__.py" in names
    assert "demo_app/main.py" in names


def test_module_entry_point_executes_with_python_m_style(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "module-entry",
        entry_point="demo_app.main",
    )
    report = run_pex_json(pex)

    assert_main_projection(report)


def test_build_with_explicit_runtime_pex_root_records_configured_value(fixture_project, tmp_path):
    runtime_root = tmp_path / "configured-runtime-root"
    pex = build_pex(
        fixture_project,
        tmp_path,
        "configured-runtime",
        runtime_pex_root=runtime_root,
    )
    info = PexInfo.from_pex(str(pex))

    assert info.raw_pex_root == str(runtime_root)


def test_pex_info_from_pex_matches_raw_pex_info_json(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "info-json")
    from_api = PexInfo.from_pex(str(pex))
    from_archive = read_pex_info_json(pex)

    assert from_api.entry_point == from_archive["entry_point"]
    assert from_api.distributions == from_archive["distributions"]
    assert from_api.build_properties == from_archive["build_properties"]


def test_console_script_pex_info_records_resolved_entry_point(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "script-info",
        script="support-cli",
        include_source=False,
    )
    info = PexInfo.from_pex(str(pex))

    assert info.script is None
    assert info.entry_point == "supportlib.cli:main"
    assert any(name.startswith(f"supportlib-{WHEEL_VERSION}-") for name in info.distributions)
