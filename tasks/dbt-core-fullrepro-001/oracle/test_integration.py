"""Integration oracle tests for dbt-core-fullrepro-001.

Each test exercises ≥2 API boundaries or cross-validates invariants (CVIs).
Tests are organized by CVI and seam categories.
"""

import json
import time
from pathlib import Path

import pytest

from dbt.cli.main import dbtRunner, dbtRunnerResult

from conftest import (
    PROJECT_NAME,
    MODEL_ALPHA,
    MODEL_BETA,
    MODEL_GAMMA,
    ANALYSIS_NAME,
    SEED_NAME,
    SOURCE_SCHEMA,
    SOURCE_TABLE,
    EXPOSURE_NAME,
    base_args,
    create_dbt_project,
    invoke_dbt,
    load_json,
    write_text,
)


# ---------------------------------------------------------------------------
# Module-scoped fixtures (heavy operations run once per module)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def full_project(tmp_path_factory):
    """Create a multi-model project and return paths."""
    root = tmp_path_factory.mktemp("integ_project")
    project, profiles, target = create_dbt_project(root)
    return {"root": root, "project": project, "profiles": profiles, "target": target}


@pytest.fixture(scope="module")
def parse_env(full_project):
    """Parse the project and cache artifacts."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "parse_artifacts"
    args = base_args(project, profiles, target)
    result = invoke_dbt(["parse", *args])
    return {
        "result": result,
        "target": target,
        "args": args,
        "manifest_path": target / "manifest.json",
    }


@pytest.fixture(scope="module")
def list_env(full_project):
    """Run list with multiple output modes."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "list_artifacts"
    args = base_args(project, profiles, target)

    invoke_dbt(["parse", *args])
    list_names = invoke_dbt(["list", *args, "--output", "name"])
    list_paths = invoke_dbt(["list", *args, "--output", "path"])
    list_json = invoke_dbt([
        "list", *args, "--output", "json",
        "--output-keys", "name", "resource_type", "unique_id", "original_file_path",
    ])
    ls_names = invoke_dbt(["ls", *args, "--output", "name"])
    return {
        "target": target,
        "args": args,
        "project": project,
        "profiles": profiles,
        "manifest_path": target / "manifest.json",
        "list_names": list_names,
        "list_paths": list_paths,
        "list_json": list_json,
        "ls_names": ls_names,
    }


@pytest.fixture(scope="module")
def compile_env(full_project):
    """Compile a model and cache artifacts."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "compile_artifacts"
    args = base_args(project, profiles, target)

    invoke_dbt(["parse", *args])
    compile_result = invoke_dbt(["compile", *args, "--select", MODEL_ALPHA])
    compiled_files = sorted(
        p for p in target.rglob("*.sql") if "compiled" in p.parts
    )
    return {
        "target": target,
        "args": args,
        "compile_result": compile_result,
        "manifest_path": target / "manifest.json",
        "run_results_path": target / "run_results.json",
        "compiled_files": compiled_files,
    }


@pytest.fixture(scope="module")
def run_env(full_project):
    """Run a model and cache results."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "run_artifacts"
    args = base_args(project, profiles, target)

    run_result = invoke_dbt(["run", *args, "--select", MODEL_ALPHA])
    return {
        "target": target,
        "args": args,
        "run_result": run_result,
        "manifest_path": target / "manifest.json",
        "run_results_path": target / "run_results.json",
    }


# ===========================================================================
# CVI-1: parse result manifest matches written manifest.json resource count
# ===========================================================================


def test_cvi1_parse_result_node_count_matches_manifest_json(parse_env):
    """CVI-1: parse result node count matches manifest.json."""
    result = parse_env["result"]
    assert result.success is True
    manifest_json = load_json(parse_env["manifest_path"])
    runner_node_count = len(result.result.nodes)
    file_node_count = len(manifest_json["nodes"])
    assert runner_node_count == file_node_count


# ===========================================================================
# CVI-2: list --output json unique_ids found in manifest.json
# ===========================================================================


def test_cvi2_list_json_unique_ids_exist_in_manifest(list_env):
    """CVI-2: list JSON unique_ids exist in manifest.json."""
    manifest = load_json(list_env["manifest_path"])
    all_manifest_ids = (
        set(manifest["nodes"])
        | set(manifest["sources"])
        | set(manifest["exposures"])
    )
    rows = [json.loads(r) for r in list_env["list_json"].result]
    for row in rows:
        assert row["unique_id"] in all_manifest_ids


# ===========================================================================
# CVI-3: list --output path matches original_file_path in manifest
# ===========================================================================


def test_cvi3_list_path_matches_manifest_original_file_path(list_env):
    """CVI-3: list path output matches manifest original_file_path."""
    manifest = load_json(list_env["manifest_path"])
    manifest_paths = {}
    for node in manifest["nodes"].values():
        manifest_paths[node["unique_id"]] = node["original_file_path"]
    for src in manifest["sources"].values():
        manifest_paths[src["unique_id"]] = src["original_file_path"]

    rows = [json.loads(r) for r in list_env["list_json"].result]
    for row in rows:
        if row["unique_id"] in manifest_paths:
            assert row["original_file_path"] == manifest_paths[row["unique_id"]]


# ===========================================================================
# CVI-4: `dbt ls` == `dbt list` for identical args
# ===========================================================================


def test_cvi4_ls_alias_produces_identical_results_to_list(list_env):
    """CVI-4: dbt ls alias produces identical results to dbt list."""
    assert list_env["ls_names"].success is True
    assert list_env["list_names"].success is True
    assert list_env["ls_names"].result == list_env["list_names"].result


# ===========================================================================
# CVI-5: compile run_results unique_ids found in manifest.json
# ===========================================================================


def test_cvi5_compile_run_results_ids_in_manifest(compile_env):
    """CVI-5: compile run_results unique_ids found in manifest.json."""
    run_results = load_json(compile_env["run_results_path"])
    manifest = load_json(compile_env["manifest_path"])
    for entry in run_results["results"]:
        assert entry["unique_id"] in manifest["nodes"]


# ===========================================================================
# CVI-6: compile written files match compiled_code fields
# ===========================================================================


def test_cvi6_compiled_file_content_matches_manifest_compiled_code(compile_env):
    """CVI-6: compiled file content matches manifest compiled_code."""
    manifest = load_json(compile_env["manifest_path"])
    alpha_id = f"model.{PROJECT_NAME}.{MODEL_ALPHA}"
    compiled_code = manifest["nodes"][alpha_id]["compiled_code"].strip()

    assert compile_env["compiled_files"], "Expected at least one compiled SQL file"
    file_contents = "\n".join(
        p.read_text(encoding="utf-8") for p in compile_env["compiled_files"]
    )
    assert compiled_code in file_contents


# ===========================================================================
# CVI-7: run writes run_results only for executed nodes; manifest has full graph
# ===========================================================================


def test_cvi7_run_results_only_contain_executed_nodes(run_env):
    """CVI-7: run_results only contain executed nodes."""
    run_results = load_json(run_env["run_results_path"])
    executed_ids = {r["unique_id"] for r in run_results["results"]}
    assert f"model.{PROJECT_NAME}.{MODEL_ALPHA}" in executed_ids
    assert f"model.{PROJECT_NAME}.{MODEL_BETA}" not in executed_ids


def test_cvi7_manifest_contains_full_graph_after_run(run_env):
    """CVI-7: manifest retains full graph after selective run."""
    manifest = load_json(run_env["manifest_path"])
    node_names = {n["name"] for n in manifest["nodes"].values()}
    assert {MODEL_ALPHA, MODEL_BETA, MODEL_GAMMA}.issubset(node_names)


# ===========================================================================
# CVI-8: --target-path redirects all artifacts
# ===========================================================================


def test_cvi8_custom_target_path_contains_all_artifacts(full_project):
    """CVI-8: custom --target-path redirects all artifacts."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    custom_target = root / "custom_output_dir"
    args = base_args(project, profiles, custom_target)

    invoke_dbt(["compile", *args, "--select", MODEL_ALPHA])

    expected_files = {"manifest.json", "semantic_manifest.json", "perf_info.json",
                      "partial_parse.msgpack", "run_results.json"}
    actual_files = {p.name for p in custom_target.iterdir() if p.is_file()}
    assert expected_files.issubset(actual_files)


def test_cvi8_compiled_files_reside_under_custom_target(full_project):
    """CVI-8: compiled files reside under custom target path."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    custom_target = root / "custom_output_dir2"
    args = base_args(project, profiles, custom_target)

    invoke_dbt(["compile", *args, "--select", MODEL_ALPHA])

    compiled = [p for p in custom_target.rglob("*.sql") if "compiled" in p.parts]
    assert len(compiled) >= 1
    assert all(str(p).startswith(str(custom_target)) for p in compiled)


# ===========================================================================
# CVI-9: --no-write-json suppresses files but runner result still valid
# ===========================================================================


def test_cvi9_no_write_json_returns_valid_manifest_object(full_project):
    """CVI-9: --no-write-json returns valid manifest object."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "no_json_artifacts"
    args = base_args(project, profiles, target)

    result = invoke_dbt(["parse", *args, "--no-write-json"])
    assert result.success is True
    assert result.result is not None
    assert hasattr(result.result, "nodes")


def test_cvi9_no_write_json_suppresses_all_json_files(full_project):
    """CVI-9: --no-write-json suppresses JSON artifact files."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "no_json_artifacts2"
    args = base_args(project, profiles, target)

    invoke_dbt(["parse", *args, "--no-write-json"])
    assert not (target / "manifest.json").exists()
    assert not (target / "semantic_manifest.json").exists()


# ===========================================================================
# CVI-10: --no-partial-parse produces same manifest for unchanged project
# ===========================================================================


def test_cvi10_no_partial_parse_same_nodes_as_normal_parse(full_project):
    """CVI-10: --no-partial-parse yields same nodes as normal parse."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]

    target_normal = root / "cvi10_normal"
    target_no_pp = root / "cvi10_no_pp"

    normal = invoke_dbt(["parse", *base_args(project, profiles, target_normal)])
    no_pp = invoke_dbt([
        "parse", *base_args(project, profiles, target_no_pp), "--no-partial-parse",
    ])

    assert normal.success is True
    assert no_pp.success is True
    assert set(normal.result.nodes.keys()) == set(no_pp.result.nodes.keys())


# ===========================================================================
# Seam: parse → list with cached manifest (dbtRunner(manifest=...))
# ===========================================================================


def test_seam_cached_manifest_reuse_in_list(full_project):
    """Seam: protocol handoff — cached manifest reuse in list command."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "seam_cached"
    args = base_args(project, profiles, target)

    parse_result = invoke_dbt(["parse", *args])
    assert parse_result.success is True

    runner = dbtRunner(manifest=parse_result.result)
    list_result = runner.invoke(["list", *args, "--output", "name"])
    assert list_result.success is True
    assert MODEL_ALPHA in list_result.result


# ===========================================================================
# Seam: parse → compile → compiled SQL file exists
# ===========================================================================


def test_seam_parse_then_compile_produces_sql_file(full_project):
    """Seam: lifecycle crossing — parse then compile produces SQL file."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "seam_parse_compile"
    args = base_args(project, profiles, target)

    parse_result = invoke_dbt(["parse", *args])
    assert parse_result.success is True

    compile_result = invoke_dbt(["compile", *args, "--select", MODEL_ALPHA])
    assert compile_result.success is True

    compiled = [p for p in target.rglob(f"{MODEL_ALPHA}.sql") if "compiled" in p.parts]
    assert len(compiled) == 1
    assert "42" in compiled[0].read_text(encoding="utf-8")


# ===========================================================================
# Seam: compile → run_results → manifest cross-reference
# ===========================================================================


def test_seam_compile_run_results_cross_references_manifest(compile_env):
    """Seam: state consistency — compile run_results cross-reference manifest."""
    run_results = load_json(compile_env["run_results_path"])
    manifest = load_json(compile_env["manifest_path"])

    for entry in run_results["results"]:
        uid = entry["unique_id"]
        assert uid in manifest["nodes"]
        assert entry["status"] == "success"
        assert entry["compiled"] is True
        assert manifest["nodes"][uid].get("compiled_code")


# ===========================================================================
# Seam: --output-keys filters JSON output fields
# ===========================================================================


def test_seam_output_keys_filters_json_fields(list_env):
    """Seam: protocol handoff — output-keys filters JSON list fields."""
    rows = [json.loads(r) for r in list_env["list_json"].result]
    expected_keys = {"name", "resource_type", "unique_id", "original_file_path"}
    for row in rows:
        assert set(row.keys()) == expected_keys


# ===========================================================================
# Seam: multiple models selected, all appear in results
# ===========================================================================


def test_seam_multiple_models_all_appear_in_compile(full_project):
    """Seam: protocol handoff — multi-model selection appears in compile results."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "seam_multi_select"
    args = base_args(project, profiles, target)

    result = invoke_dbt(["compile", *args, "--select", f"{MODEL_ALPHA} {MODEL_GAMMA}"])
    assert result.success is True

    run_results = load_json(target / "run_results.json")
    compiled_ids = {r["unique_id"] for r in run_results["results"]}
    assert f"model.{PROJECT_NAME}.{MODEL_ALPHA}" in compiled_ids
    assert f"model.{PROJECT_NAME}.{MODEL_GAMMA}" in compiled_ids


# ===========================================================================
# Additional integration: list agrees with manifest on model names
# ===========================================================================


def test_manifest_model_names_subset_of_list_names(list_env):
    """CVI-2: manifest model names are subset of list names."""
    manifest = load_json(list_env["manifest_path"])
    model_names = {
        n["name"] for n in manifest["nodes"].values()
        if n["resource_type"] == "model"
    }
    assert model_names.issubset(set(list_env["list_names"].result))


# ===========================================================================
# Additional integration: partial parse cache is reused
# ===========================================================================


def test_partial_parse_cache_survives_second_invocation(full_project):
    """Seam: lifecycle crossing — partial parse cache survives second invocation."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "partial_parse_test"
    args = base_args(project, profiles, target)

    first = invoke_dbt(["parse", *args])
    assert first.success is True
    cache = target / "partial_parse.msgpack"
    assert cache.is_file()
    first_mtime = cache.stat().st_mtime

    time.sleep(0.02)
    second = invoke_dbt(["parse", *args])
    assert second.success is True
    assert cache.stat().st_mtime >= first_mtime


# ===========================================================================
# Additional integration: run → parse preserves full graph
# ===========================================================================


def test_run_then_parse_returns_full_manifest(full_project):
    """Seam: lifecycle crossing — run then parse returns full manifest."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "run_parse_seam"
    args = base_args(project, profiles, target)

    run_result = invoke_dbt(["run", *args, "--select", MODEL_ALPHA])
    assert run_result.success is True

    parse_result = invoke_dbt(["parse", *args])
    assert parse_result.success is True
    assert f"model.{PROJECT_NAME}.{MODEL_ALPHA}" in parse_result.result.nodes
    assert f"model.{PROJECT_NAME}.{MODEL_BETA}" in parse_result.result.nodes


# ===========================================================================
# Additional integration: list --exclude removes specific model
# ===========================================================================


def test_list_exclude_removes_model_from_output(list_env):
    """Seam: protocol handoff — list --exclude removes model from output."""
    args = base_args(list_env["project"], list_env["profiles"], list_env["target"])
    result = invoke_dbt(["list", *args, "--output", "name", "--exclude", MODEL_ALPHA])
    assert result.success is True
    assert MODEL_ALPHA not in result.result
    assert MODEL_BETA in result.result


# ===========================================================================
# Additional integration: parse artifacts form complete set
# ===========================================================================


def test_parse_target_contains_full_artifact_set(parse_env):
    """CVI-8: parse target contains full artifact set."""
    target = parse_env["target"]
    expected = {"manifest.json", "semantic_manifest.json",
                "perf_info.json", "partial_parse.msgpack"}
    actual = {p.name for p in target.iterdir() if p.is_file()}
    assert expected.issubset(actual)


# ===========================================================================
# Additional integration: compile inline does not persist in manifest nodes
# ===========================================================================


def test_inline_compile_not_persisted_in_manifest_nodes(full_project):
    """Seam: protocol handoff — inline compile not persisted in manifest nodes."""
    root = full_project["root"]
    project = full_project["project"]
    profiles = full_project["profiles"]
    target = root / "inline_seam"
    args = base_args(project, profiles, target)

    result = invoke_dbt([
        "compile", *args, "--inline", "select {{ 3 * 7 }} as twenty_one", "--output", "json",
    ])
    assert result.success is True

    manifest = load_json(target / "manifest.json")
    node_names = {n["name"] for n in manifest["nodes"].values()}
    assert "inline_query" not in node_names


# ===========================================================================
# Additional integration: run results status matches runner result status
# ===========================================================================


def test_run_result_statuses_match_artifact_file(run_env):
    """Seam: state consistency — runner result statuses match artifact file."""
    assert run_env["run_result"].success is True
    runner_statuses = [str(r.status) for r in run_env["run_result"].result.results]
    file_results = load_json(run_env["run_results_path"])
    file_statuses = [r["status"] for r in file_results["results"]]
    assert runner_statuses == file_statuses


# ===========================================================================
# Additional integration: list resource-type filter selects analysis only
# ===========================================================================


def test_list_resource_type_analysis_filters_correctly(list_env):
    """Seam: protocol handoff — resource-type filter selects analysis only."""
    args = base_args(list_env["project"], list_env["profiles"], list_env["target"])
    result = invoke_dbt([
        "list", *args, "--resource-type", "analysis", "--output", "name",
    ])
    assert result.success is True
    assert ANALYSIS_NAME in result.result
    assert MODEL_ALPHA not in result.result
