from __future__ import annotations

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


@pytest.mark.depends_on("test_zipapp_build_embeds_pex_info_and_main_module")
@pytest.mark.depends_on("test_entry_point_execution_returns_source_and_wheel_markers")
def test_zipapp_build_inspect_and_run_entry_point_workflow(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-zipapp")
    names = zipapp_names(pex)
    report = run_pex_json(pex)

    assert "PEX-INFO" in names
    assert "demo_app/main.py" in names
    assert_main_projection(report)


@pytest.mark.depends_on("test_packed_layout_identifies_as_packed_directory")
@pytest.mark.depends_on("test_packed_layout_contains_top_level_main_and_pex_info")
def test_packed_layout_build_inspect_and_run_directory_workflow(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-packed", layout="packed")
    names = relative_names(pex)
    report = run_pex_json(pex)

    assert Layout.identify(str(pex)) is Layout.PACKED
    assert {"PEX-INFO", "__main__.py"}.issubset(names)
    assert_main_projection(report)


@pytest.mark.depends_on("test_loose_layout_identifies_as_loose_directory")
@pytest.mark.depends_on("test_loose_layout_contains_layout_marker_and_source_files")
def test_loose_layout_build_inspect_and_run_directory_workflow(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-loose", layout="loose")
    names = relative_names(pex)
    report = run_pex_json(pex)

    assert Layout.identify_original(str(pex)) is Layout.LOOSE
    assert {"PEX-INFO", "__main__.py", "demo_app/main.py"}.issubset(names)
    assert_main_projection(report)


@pytest.mark.depends_on("test_console_script_execution_returns_wheel_marker")
@pytest.mark.depends_on("test_console_script_pex_info_records_resolved_entry_point")
def test_console_script_build_info_and_runtime_workflow(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-script",
        script="support-cli",
        include_source=False,
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert info.script is None
    assert info.entry_point == "supportlib.cli:main"
    assert_support_cli_projection(report)


@pytest.mark.depends_on("test_zipapp_archive_contains_source_package_files")
@pytest.mark.depends_on("test_zipapp_archive_contains_dependency_wheel_projection")
def test_source_and_wheel_markers_survive_archive_and_execution_workflow(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-markers")
    names = zipapp_names(pex)
    report = run_pex_json(pex)

    assert "demo_app/__init__.py" in names
    assert any(name.startswith(f".deps/supportlib-{WHEEL_VERSION}-") for name in names)
    assert report["source"] == SOURCE_MARKER
    assert report["wheel"] == WHEEL_MARKER


@pytest.mark.depends_on("test_injected_application_args_are_visible_to_entry_point")
@pytest.mark.depends_on("test_pex_info_roundtrip_from_json_preserves_injected_arguments")
def test_injected_app_args_are_stored_in_info_and_observed_at_runtime(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-app-args",
        inject_args=("--mode", "integration"),
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert info.inject_args == ("--mode", "integration")
    assert_main_projection(report, argv=["--mode", "integration"])


@pytest.mark.depends_on("test_injected_python_args_enable_dev_mode")
@pytest.mark.depends_on("test_pex_info_roundtrip_from_json_preserves_injected_arguments")
def test_injected_python_args_are_stored_and_observed_at_runtime(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-python-args",
        inject_python_args=("-X", "dev"),
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert info.inject_python_args == ("-X", "dev")
    assert_main_projection(report, dev_mode=True)


@pytest.mark.depends_on("test_runtime_pex_root_gets_files_after_zipapp_execution")
@pytest.mark.depends_on("test_entry_point_execution_returns_source_and_wheel_markers")
def test_custom_pex_root_populates_runtime_cache_and_preserves_output(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-root-cache")
    pex_root = tmp_path / "custom-root"
    first = run_pex_json(pex, pex_root=pex_root)
    second = run_pex_json(pex, pex_root=pex_root)

    assert_main_projection(first)
    assert first == second
    assert pex_root_has_runtime_files(pex_root)


@pytest.mark.depends_on("test_venv_mode_executes_with_prefix_under_custom_pex_root")
@pytest.mark.depends_on("test_venv_mode_records_venv_flag_in_pex_info")
def test_venv_pex_root_populates_venv_and_preserves_output(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-venv-cache", venv=True)
    pex_root = tmp_path / "venv-root"
    first = run_pex_json(pex, pex_root=pex_root)
    second = run_pex_json(pex, pex_root=pex_root)

    assert_main_projection(first, prefix_has_venvs_segment=True)
    assert first == second
    assert pex_root_has_runtime_files(pex_root)


@pytest.mark.depends_on("test_build_with_explicit_runtime_pex_root_records_configured_value")
@pytest.mark.depends_on("test_runtime_pex_root_gets_files_after_zipapp_execution")
def test_configured_runtime_pex_root_is_used_for_local_execution(fixture_project, tmp_path):
    configured_root = tmp_path / "configured-root"
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-configured-root",
        runtime_pex_root=configured_root,
    )
    report = run_pex_json(pex)
    info = PexInfo.from_pex(str(pex))

    assert info.raw_pex_root == str(configured_root)
    assert_main_projection(report)
    assert pex_root_has_runtime_files(configured_root)


@pytest.mark.depends_on("test_pex_info_from_pex_matches_raw_pex_info_json")
@pytest.mark.depends_on("test_entry_point_execution_returns_source_and_wheel_markers")
def test_raw_pex_info_api_projection_and_runtime_agree(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-info-agree")
    raw = read_pex_info_json(pex)
    api = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert raw["entry_point"] == api.entry_point
    assert raw["distributions"] == api.distributions
    assert_main_projection(report)


@pytest.mark.depends_on("test_zipapp_layout_identifies_as_zipapp")
@pytest.mark.depends_on("test_packed_layout_identifies_as_packed_directory")
@pytest.mark.depends_on("test_loose_layout_identifies_as_loose_directory")
def test_three_layouts_share_same_entry_point_runtime_projection(fixture_project, tmp_path):
    reports = []
    for layout in ("zipapp", "packed", "loose"):
        pex = build_pex(fixture_project, tmp_path, f"workflow-layout-{layout}", layout=layout)
        reports.append(run_pex_json(pex))

    assert all(report == reports[0] for report in reports)
    assert_main_projection(reports[0])


@pytest.mark.depends_on("test_zipapp_pex_info_lists_local_wheel_distribution")
@pytest.mark.depends_on("test_console_script_execution_returns_wheel_marker")
def test_distribution_projection_and_console_script_runtime_agree(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-dist-script",
        script="support-cli",
        include_source=False,
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert any(name.startswith(f"supportlib-{WHEEL_VERSION}-") for name in info.distributions)
    assert_support_cli_projection(report)


@pytest.mark.depends_on("test_module_entry_point_executes_with_python_m_style")
@pytest.mark.depends_on("test_fixture_source_tree_contains_main_module")
def test_module_style_entry_point_records_module_and_runs_source_code(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-module",
        entry_point="demo_app.main",
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert info.entry_point == "demo_app.main"
    assert_main_projection(report)


@pytest.mark.depends_on("test_console_script_execution_returns_wheel_marker")
@pytest.mark.depends_on("test_injected_application_args_are_visible_to_entry_point")
def test_runtime_args_are_passed_to_console_script_without_source_tree(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-script-runtime-args",
        script="support-cli",
        include_source=False,
    )
    report = run_pex_json(pex, args=("tail", "value"))

    assert_support_cli_projection(report, argv=["tail", "value"])


@pytest.mark.depends_on("test_injected_application_args_are_visible_to_entry_point")
@pytest.mark.depends_on("test_entry_point_execution_returns_source_and_wheel_markers")
def test_runtime_args_are_appended_to_source_entry_point_invocation(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-source-runtime-args")
    report = run_pex_json(pex, args=("runtime", "value"))

    assert_main_projection(report, argv=["runtime", "value"])


@pytest.mark.depends_on("test_injected_application_args_are_visible_to_entry_point")
@pytest.mark.depends_on("test_injected_python_args_enable_dev_mode")
def test_venv_execution_combines_app_args_python_args_and_source_imports(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-venv-injected",
        inject_args=("--stage", "integration"),
        inject_python_args=("-X", "dev"),
        venv=True,
    )
    report = run_pex_json(pex, pex_root=tmp_path / "workflow-venv-injected-root")

    assert_main_projection(
        report,
        argv=["--stage", "integration"],
        dev_mode=True,
        prefix_has_venvs_segment=True,
    )


@pytest.mark.depends_on("test_packed_layout_contains_top_level_main_and_pex_info")
@pytest.mark.depends_on("test_runtime_pex_root_gets_files_after_zipapp_execution")
def test_packed_layout_runs_with_runner_owned_pex_root_workflow(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-packed-root", layout="packed")
    pex_root = tmp_path / "packed-root"
    report = run_pex_json(pex, pex_root=pex_root)

    assert_main_projection(report)
    assert pex_root_has_runtime_files(pex_root)


@pytest.mark.depends_on("test_loose_layout_contains_layout_marker_and_source_files")
@pytest.mark.depends_on("test_entry_point_execution_returns_source_and_wheel_markers")
def test_loose_layout_runs_from_directory_and_keeps_source_projection(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-loose-source", layout="loose")
    names = relative_names(pex)
    report = run_pex_json(pex)

    assert "demo_app/main.py" in names
    assert_main_projection(report)


@pytest.mark.depends_on("test_zipapp_archive_contains_dependency_wheel_projection")
@pytest.mark.depends_on("test_pex_info_from_zipapp_reads_entry_point_and_build_properties")
def test_archive_distribution_file_and_pex_info_distribution_share_name(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-dist-name")
    names = zipapp_names(pex)
    info = PexInfo.from_pex(str(pex))
    dist_names = set(info.distributions)

    assert any(name.startswith(f".deps/{dist}") for dist in dist_names for name in names)
    assert any(name.startswith(f"supportlib-{WHEEL_VERSION}-") for name in dist_names)


@pytest.mark.depends_on("test_venv_mode_records_venv_flag_in_pex_info")
@pytest.mark.depends_on("test_console_script_execution_returns_wheel_marker")
def test_venv_console_script_workflow_uses_wheel_entry_point(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-venv-script",
        script="support-cli",
        include_source=False,
        venv=True,
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex, pex_root=tmp_path / "venv-script-root")

    assert info.venv is True
    assert_support_cli_projection(report)


@pytest.mark.depends_on("test_build_with_explicit_runtime_pex_root_records_configured_value")
@pytest.mark.depends_on("test_venv_mode_executes_with_prefix_under_custom_pex_root")
def test_configured_runtime_root_and_venv_mode_create_runner_owned_venv(fixture_project, tmp_path):
    configured_root = tmp_path / "configured-venv-root"
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-configured-venv",
        runtime_pex_root=configured_root,
        venv=True,
    )
    report = run_pex_json(pex)

    assert_main_projection(report, prefix_has_venvs_segment=True)
    assert pex_root_has_runtime_files(configured_root)


@pytest.mark.depends_on("test_pex_info_roundtrip_from_json_preserves_injected_arguments")
@pytest.mark.depends_on("test_console_script_pex_info_records_resolved_entry_point")
def test_console_script_injected_args_are_stored_and_visible(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-script-injected",
        script="support-cli",
        include_source=False,
        inject_args=("--console", "yes"),
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert info.inject_args == ("--console", "yes")
    assert_support_cli_projection(report, argv=["--console", "yes"])


@pytest.mark.depends_on("test_pex_info_roundtrip_from_json_preserves_injected_arguments")
@pytest.mark.depends_on("test_injected_python_args_enable_dev_mode")
def test_console_script_injected_python_args_are_stored_and_visible(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-script-python-injected",
        script="support-cli",
        include_source=False,
        inject_python_args=("-X", "dev"),
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert info.inject_python_args == ("-X", "dev")
    assert_support_cli_projection(report, dev_mode=True)


@pytest.mark.depends_on("test_zipapp_build_embeds_pex_info_and_main_module")
@pytest.mark.depends_on("test_public_import_surface_exposes_layout_and_pex_info")
def test_zipapp_public_layout_api_archive_listing_and_runtime_align(fixture_project, tmp_path):
    pex = build_pex(fixture_project, tmp_path, "workflow-public-layout")
    names = zipapp_names(pex)
    report = run_pex_json(pex)

    assert Layout.identify(str(pex)) is Layout.ZIPAPP
    assert {"PEX-INFO", "__main__.py"}.issubset(names)
    assert_main_projection(report)


@pytest.mark.depends_on(
    "test_module_entry_point_executes_with_python_m_style",
    "test_injected_application_args_are_visible_to_entry_point",
)
def test_module_entry_point_and_runtime_arguments_share_one_projection(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-module-runtime-args",
        entry_point="demo_app.main",
    )
    report = run_pex_json(pex, args=("from-module", "value"))

    assert_main_projection(report, argv=["from-module", "value"])


@pytest.mark.depends_on(
    "test_build_with_explicit_runtime_pex_root_records_configured_value",
    "test_pex_info_from_pex_matches_raw_pex_info_json",
)
def test_configured_runtime_root_is_shared_by_archive_metadata_and_execution(fixture_project, tmp_path):
    runtime_root = tmp_path / "metadata-runtime-root"
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-metadata-runtime-root",
        runtime_pex_root=runtime_root,
    )
    info = PexInfo.from_pex(str(pex))
    raw = read_pex_info_json(pex)
    report = run_pex_json(pex)

    assert info.raw_pex_root == raw["pex_root"]
    assert info.raw_pex_root == str(runtime_root)
    assert_main_projection(report)
    assert pex_root_has_runtime_files(runtime_root)


@pytest.mark.depends_on(
    "test_console_script_pex_info_records_resolved_entry_point",
    "test_injected_application_args_are_visible_to_entry_point",
)
def test_console_script_archive_metadata_and_injected_runtime_arguments_agree(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-script-metadata-args",
        script="support-cli",
        include_source=False,
        inject_args=("--format", "json"),
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex)

    assert info.entry_point == "supportlib.cli:main"
    assert info.inject_args == ("--format", "json")
    assert_support_cli_projection(report, argv=["--format", "json"])


@pytest.mark.depends_on(
    "test_venv_mode_records_venv_flag_in_pex_info",
    "test_venv_mode_executes_with_prefix_under_custom_pex_root",
)
def test_venv_module_entry_point_keeps_metadata_and_runtime_consistent(fixture_project, tmp_path):
    pex = build_pex(
        fixture_project,
        tmp_path,
        "workflow-venv-module",
        entry_point="demo_app.main",
        venv=True,
    )
    info = PexInfo.from_pex(str(pex))
    report = run_pex_json(pex, pex_root=tmp_path / "venv-module-root")

    assert info.venv is True
    assert info.entry_point == "demo_app.main"
    assert_main_projection(report, prefix_has_venvs_segment=True)


@pytest.mark.depends_on(
    "test_zipapp_pex_info_lists_local_wheel_distribution",
    "test_zipapp_layout_identifies_as_zipapp",
    "test_packed_layout_identifies_as_packed_directory",
    "test_loose_layout_identifies_as_loose_directory",
)
def test_layout_variants_keep_distribution_metadata_and_runtime_markers_aligned(fixture_project, tmp_path):
    projections = []
    for layout in ("zipapp", "packed", "loose"):
        pex = build_pex(fixture_project, tmp_path, f"workflow-distribution-{layout}", layout=layout)
        info = PexInfo.from_pex(str(pex))
        report = run_pex_json(pex)
        projections.append((set(info.distributions), report["combined"], report["version"]))

    assert all(projection == projections[0] for projection in projections)
    assert any(name.startswith(f"supportlib-{WHEEL_VERSION}-") for name in projections[0][0])
    assert projections[0][1] == f"{SOURCE_MARKER}|{WHEEL_MARKER}|{WHEEL_VERSION}"
