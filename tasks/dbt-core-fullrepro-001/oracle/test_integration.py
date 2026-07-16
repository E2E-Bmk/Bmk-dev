# Spec2Repo oracle - integration tests for dbt-core-fullrepro-001
import json
import os
import time
from pathlib import Path

import pytest

from dbt.cli import dbt_cli
from dbt.cli.main import cli, dbtRunner, dbtRunnerResult


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_project(root: Path, name: str = "sample"):
    project = root / name
    profiles = root / "profiles"
    target = root / "target"
    profiles.mkdir(parents=True, exist_ok=True)
    _write_text(
        project / "dbt_project.yml",
        "\n".join(
            [
                f"name: {name}",
                "version: 1.0",
                f"profile: {name}",
                "model-paths: [models]",
                "analysis-paths: [analyses]",
                "test-paths: [tests]",
                "seed-paths: [seeds]",
                "models:",
                f"  {name}:",
                "    +materialized: view",
            ]
        )
        + "\n",
    )
    _write_text(
        profiles / "profiles.yml",
        "\n".join(
            [
                f"{name}:",
                "  target: dev",
                "  outputs:",
                "    dev:",
                "      type: duckdb",
                f"      path: {root / 'warehouse.duckdb'}",
                "      schema: main",
                "      threads: 2",
            ]
        )
        + "\n",
    )
    _write_text(project / "models" / "alpha.sql", "select 1 as id, 'alpha' as label\n")
    _write_text(project / "models" / "beta.sql", "select * from {{ ref('alpha') }}\n")
    _write_text(project / "analyses" / "rollup.sql", "select count(*) as n from {{ ref('alpha') }}\n")
    _write_text(project / "tests" / "assert_alpha.sql", "select * from {{ ref('alpha') }} where id != 1\n")
    _write_text(project / "seeds" / "seed_table.csv", "id,name\n1,Ada\n2,Grace\n")
    _write_text(
        project / "models" / "schema.yml",
        "\n".join(
            [
                "version: 2",
                "models:",
                "  - name: alpha",
                "    description: Alpha model",
                "    columns:",
                "      - name: id",
                "        tests:",
                "          - not_null",
                "  - name: beta",
                "sources:",
                "  - name: raw",
                "    schema: main",
                "    tables:",
                "      - name: orders",
                "exposures:",
                "  - name: weekly_dashboard",
                "    type: dashboard",
                "    maturity: low",
                "    url: https://example.invalid/dashboard",
                "    depends_on:",
                "      - ref('alpha')",
                "    owner:",
                "      name: Analytics",
                "      email: analytics@example.invalid",
            ]
        )
        + "\n",
    )
    return project, profiles, target


def _base_args(project: Path, profiles: Path, target: Path):
    return [
        "--project-dir",
        str(project),
        "--profiles-dir",
        str(profiles),
        "--target-path",
        str(target),
        "--no-version-check",
        "--quiet",
    ]


def _invoke(args):
    return dbtRunner().invoke(args)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def project_state(tmp_path_factory):
    root = tmp_path_factory.mktemp("dbt_project")
    project, profiles, target = _make_project(root)
    base = _base_args(project, profiles, target)

    parse_result = _invoke(["parse", *base])
    manifest_path = target / "manifest.json"
    semantic_manifest_path = target / "semantic_manifest.json"
    perf_info_path = target / "perf_info.json"
    partial_parse_path = target / "partial_parse.msgpack"
    manifest = _load_json(manifest_path)

    list_names = _invoke(["list", *base, "--output", "name"])
    list_paths = _invoke(["list", *base, "--output", "path"])
    list_json = _invoke(
        [
            "list",
            *base,
            "--output",
            "json",
            "--output-keys",
            "name",
            "resource_type",
            "unique_id",
            "original_file_path",
        ]
    )
    ls_names = _invoke(["ls", *base, "--output", "name"])

    compile_alpha = _invoke(["compile", *base, "--select", "alpha"])
    compiled_manifest = _load_json(target / "manifest.json")
    run_results = _load_json(target / "run_results.json")
    compiled_files = sorted(p for p in target.rglob("*.sql") if "compiled" in p.parts)

    inline_target = root / "inline_target"
    inline_base = _base_args(project, profiles, inline_target)
    inline_compile = _invoke(
        ["compile", *inline_base, "--inline", "select {{ 1 + 1 }} as two", "--output", "json"]
    )
    inline_manifest = _load_json(inline_target / "manifest.json")

    no_json_target = root / "no_json_target"
    no_json_result = _invoke(["parse", *_base_args(project, profiles, no_json_target), "--no-write-json"])

    second_target = root / "second_target"
    second_base = _base_args(project, profiles, second_target)
    first_partial = _invoke(["parse", *second_base])
    cache_path = second_target / "partial_parse.msgpack"
    first_mtime = cache_path.stat().st_mtime
    time.sleep(0.01)
    second_partial = _invoke(["parse", *second_base])
    second_mtime = cache_path.stat().st_mtime
    no_partial_target = root / "no_partial_target"
    no_partial_result = _invoke(["parse", *_base_args(project, profiles, no_partial_target), "--no-partial-parse"])

    invalid_root = tmp_path_factory.mktemp("invalid_dbt_project")
    invalid_project, invalid_profiles, invalid_target = _make_project(invalid_root, "broken")
    _write_text(invalid_project / "models" / "broken.sql", "select * from {{ ref('missing_model') }}\n")
    invalid_parse = _invoke(["parse", *_base_args(invalid_project, invalid_profiles, invalid_target)])
    invalid_combo = _invoke(["list", *base, "--models", "alpha", "--select", "beta"])
    missing_project = _invoke(
        [
            "parse",
            "--project-dir",
            str(root / "missing"),
            "--profiles-dir",
            str(profiles),
            "--target-path",
            str(root / "missing_target"),
            "--no-version-check",
            "--quiet",
        ]
    )

    json_rows = [json.loads(row) for row in list_json.result]
    nodes_by_name = {node["name"]: node for node in manifest["nodes"].values()}

    return {
        "project": project,
        "profiles": profiles,
        "target": target,
        "parse_result": parse_result,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "semantic_manifest_path": semantic_manifest_path,
        "perf_info_path": perf_info_path,
        "partial_parse_path": partial_parse_path,
        "list_names": list_names,
        "list_paths": list_paths,
        "list_json": list_json,
        "json_rows": json_rows,
        "ls_names": ls_names,
        "compile_alpha": compile_alpha,
        "run_results": run_results,
        "compiled_manifest": compiled_manifest,
        "compiled_files": compiled_files,
        "inline_compile": inline_compile,
        "inline_manifest": inline_manifest,
        "no_json_result": no_json_result,
        "no_json_target": no_json_target,
        "first_partial": first_partial,
        "second_partial": second_partial,
        "no_partial_result": no_partial_result,
        "cache_path": cache_path,
        "first_mtime": first_mtime,
        "second_mtime": second_mtime,
        "invalid_parse": invalid_parse,
        "invalid_combo": invalid_combo,
        "missing_project": missing_project,
        "nodes_by_name": nodes_by_name,
    }


def _model_node(state, name):
    return state["nodes_by_name"][name]


def test_parse_runner_succeeds(project_state):
    assert project_state["parse_result"].success is True
    assert project_state["parse_result"].exception is None


def test_parse_runner_returns_manifest_like_result(project_state):
    result = project_state["parse_result"].result
    assert result is not None
    assert hasattr(result, "nodes")


def test_parse_runner_returns_runner_result_object(project_state):
    assert isinstance(project_state["parse_result"], dbtRunnerResult)


def test_parse_writes_manifest_json(project_state):
    assert project_state["manifest_path"].is_file()


def test_parse_writes_semantic_manifest_json(project_state):
    assert project_state["semantic_manifest_path"].is_file()


def test_parse_writes_perf_info_json(project_state):
    assert project_state["perf_info_path"].is_file()


def test_parse_writes_partial_parse_cache(project_state):
    assert project_state["partial_parse_path"].is_file()


def test_manifest_has_public_resource_collections(project_state):
    manifest = project_state["manifest"]
    for key in ["nodes", "sources", "exposures", "macros", "parent_map", "child_map", "disabled"]:
        assert key in manifest


def test_manifest_contains_enabled_models(project_state):
    names = {node["name"] for node in project_state["manifest"]["nodes"].values()}
    assert {"alpha", "beta"}.issubset(names)


def test_manifest_model_identity_fields_are_public(project_state):
    alpha = _model_node(project_state, "alpha")
    for key in ["name", "unique_id", "package_name", "path", "original_file_path", "resource_type"]:
        assert alpha[key]


def test_manifest_source_identity_is_written(project_state):
    sources = list(project_state["manifest"]["sources"].values())
    assert any(source["name"] == "orders" and source["source_name"] == "raw" for source in sources)


def test_manifest_exposure_identity_is_written(project_state):
    exposures = list(project_state["manifest"]["exposures"].values())
    assert any(exposure["name"] == "weekly_dashboard" for exposure in exposures)


def test_parse_only_does_not_compile_model_code(project_state):
    beta = _model_node(project_state, "beta")
    assert not beta.get("compiled_code")


def test_list_output_name_succeeds(project_state):
    assert project_state["list_names"].success is True
    assert isinstance(project_state["list_names"].result, list)


def test_list_output_name_includes_models(project_state):
    assert {"alpha", "beta"}.issubset(set(project_state["list_names"].result))


def test_list_output_name_includes_source(project_state):
    assert "raw.orders" in set(project_state["list_names"].result)


def test_list_output_name_includes_exposure(project_state):
    assert "weekly_dashboard" in set(project_state["list_names"].result)


def test_ls_alias_matches_list_names(project_state):
    assert project_state["ls_names"].success is True
    assert project_state["ls_names"].result == project_state["list_names"].result


def test_list_output_path_returns_original_model_paths(project_state):
    paths = set(project_state["list_paths"].result)
    assert "models/alpha.sql" in paths
    assert "models/beta.sql" in paths


def test_list_json_rows_are_json_objects(project_state):
    assert project_state["json_rows"]
    assert all(isinstance(row, dict) for row in project_state["json_rows"])


def test_list_json_honors_requested_output_keys(project_state):
    row = next(row for row in project_state["json_rows"] if row["name"] == "alpha")
    assert set(row) == {"name", "resource_type", "unique_id", "original_file_path"}


def test_list_json_unique_ids_resolve_in_manifest(project_state):
    manifest_ids = set(project_state["manifest"]["nodes"]) | set(project_state["manifest"]["sources"]) | set(project_state["manifest"]["exposures"])
    assert all(row["unique_id"] in manifest_ids for row in project_state["json_rows"])


def test_list_output_exclude_removes_selected_model(project_state):
    result = _invoke(["list", *_base_args(project_state["project"], project_state["profiles"], project_state["target"]), "--output", "name", "--exclude", "alpha"])
    assert result.success is True
    assert "alpha" not in result.result


def test_list_resource_type_analysis_can_select_analysis(project_state):
    result = _invoke(["list", *_base_args(project_state["project"], project_state["profiles"], project_state["target"]), "--resource-type", "analysis", "--output", "name"])
    assert result.success is True
    assert result.result == ["rollup"]


def test_list_default_does_not_include_analysis(project_state):
    assert "rollup" not in set(project_state["list_names"].result)


def test_list_models_flag_selects_models_only(project_state):
    result = _invoke(["list", *_base_args(project_state["project"], project_state["profiles"], project_state["target"]), "--models", "alpha", "--output", "name"])
    assert result.success is True
    assert result.result == ["alpha"]


def test_empty_selection_returns_empty_list(project_state):
    result = _invoke(["list", *_base_args(project_state["project"], project_state["profiles"], project_state["target"]), "--select", "tag:does_not_exist", "--output", "name"])
    assert result.success is True
    assert result.result == []


def test_compile_selected_model_succeeds(project_state):
    assert project_state["compile_alpha"].success is True
    assert project_state["compile_alpha"].exception is None


def test_compile_writes_run_results(project_state):
    assert (project_state["target"] / "run_results.json").is_file()


def test_compile_run_results_only_include_selected_node(project_state):
    names = {row["unique_id"].split(".")[-1] for row in project_state["run_results"]["results"]}
    assert "alpha" in names
    assert "beta" not in names


def test_compile_result_status_is_success(project_state):
    assert project_state["run_results"]["results"][0]["status"] == "success"


def test_compile_result_maps_to_manifest(project_state):
    unique_id = project_state["run_results"]["results"][0]["unique_id"]
    assert unique_id in project_state["manifest"]["nodes"]


def test_compile_result_is_marked_compiled(project_state):
    assert project_state["run_results"]["results"][0]["compiled"] is True


def test_compile_manifest_has_compiled_code_for_selected_model(project_state):
    alpha_id = _model_node(project_state, "alpha")["unique_id"]
    assert "select 1 as id" in project_state["compiled_manifest"]["nodes"][alpha_id]["compiled_code"]


def test_compile_writes_compiled_sql_file(project_state):
    assert project_state["compiled_files"]


def test_compiled_file_matches_manifest_compiled_code(project_state):
    compiled_text = "\n".join(path.read_text(encoding="utf-8") for path in project_state["compiled_files"])
    alpha_id = _model_node(project_state, "alpha")["unique_id"]
    assert project_state["compiled_manifest"]["nodes"][alpha_id]["compiled_code"].strip() in compiled_text


def test_compile_inline_succeeds(project_state):
    assert project_state["inline_compile"].success is True


def test_compile_inline_result_contains_inline_query(project_state):
    result = project_state["inline_compile"].result
    text = json.dumps(result, default=str)
    assert "inline_query" in text


def test_inline_query_is_not_persisted_in_manifest_nodes(project_state):
    names = {node["name"] for node in project_state["inline_manifest"]["nodes"].values()}
    assert "inline_query" not in names


def test_no_write_json_preserves_runner_result(project_state):
    assert project_state["no_json_result"].success is True
    assert project_state["no_json_result"].result is not None


def test_no_write_json_suppresses_manifest_file(project_state):
    assert not (project_state["no_json_target"] / "manifest.json").exists()


def test_partial_parse_first_invocation_succeeds(project_state):
    assert project_state["first_partial"].success is True


def test_partial_parse_second_invocation_succeeds(project_state):
    assert project_state["second_partial"].success is True


def test_partial_parse_cache_persists_across_invocations(project_state):
    assert project_state["cache_path"].is_file()
    assert project_state["second_mtime"] >= project_state["first_mtime"]


def test_no_partial_parse_still_returns_manifest(project_state):
    assert project_state["no_partial_result"].success is True
    assert hasattr(project_state["no_partial_result"].result, "nodes")


def test_target_path_contains_all_parse_artifacts(project_state):
    names = {path.name for path in project_state["target"].iterdir()}
    assert {"manifest.json", "semantic_manifest.json", "perf_info.json", "partial_parse.msgpack", "run_results.json"}.issubset(names)


def test_target_path_redirects_compiled_files(project_state):
    assert all(str(path).startswith(str(project_state["target"])) for path in project_state["compiled_files"])


def test_manifest_and_list_agree_on_model_names(project_state):
    manifest_model_names = {node["name"] for node in project_state["manifest"]["nodes"].values() if node["resource_type"] == "model"}
    assert manifest_model_names.issubset(set(project_state["list_names"].result))


def test_manifest_and_list_json_agree_on_original_paths(project_state):
    manifest_paths = {node["unique_id"]: node["original_file_path"] for node in project_state["manifest"]["nodes"].values()}
    for row in project_state["json_rows"]:
        if row["unique_id"] in manifest_paths:
            assert row["original_file_path"] == manifest_paths[row["unique_id"]]


def test_runner_list_matches_cli_alias_projection(project_state):
    runner = dbtRunner(manifest=project_state["parse_result"].result)
    result = runner.invoke(["list", *_base_args(project_state["project"], project_state["profiles"], project_state["target"]), "--output", "name"])
    assert result.success is True
    assert result.result == project_state["list_names"].result
