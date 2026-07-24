# Spec2Repo oracle - integration tests for dbt-core-fullrepro-001
import json
import os
import time
from pathlib import Path

import pytest

from dbt.cli.main import dbtRunner, dbtRunnerResult


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
def project_env(tmp_path_factory):
    root = tmp_path_factory.mktemp("dbt_project")
    project, profiles, _ = _make_project(root)
    return {"root": root, "project": project, "profiles": profiles}


@pytest.fixture(scope="module")
def parse_state(project_env):
    root = project_env["root"]
    project = project_env["project"]
    profiles = project_env["profiles"]
    target = root / "parse_target"
    base = _base_args(project, profiles, target)
    parse_result = _invoke(["parse", *base])
    return {
        "project": project,
        "profiles": profiles,
        "target": target,
        "parse_result": parse_result,
        "manifest_path": target / "manifest.json",
        "semantic_manifest_path": target / "semantic_manifest.json",
        "perf_info_path": target / "perf_info.json",
        "partial_parse_path": target / "partial_parse.msgpack",
    }


@pytest.fixture(scope="module")
def list_state(project_env):
    root = project_env["root"]
    project = project_env["project"]
    profiles = project_env["profiles"]
    target = root / "list_target"
    base = _base_args(project, profiles, target)
    parse_result = _invoke(["parse", *base])
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
    return {
        "project": project,
        "profiles": profiles,
        "target": target,
        "parse_result": parse_result,
        "manifest_path": target / "manifest.json",
        "list_names": list_names,
        "list_paths": list_paths,
        "list_json": list_json,
        "ls_names": ls_names,
    }


@pytest.fixture(scope="module")
def compile_state(project_env):
    root = project_env["root"]
    project = project_env["project"]
    profiles = project_env["profiles"]
    target = root / "compile_target"
    base = _base_args(project, profiles, target)
    parse_result = _invoke(["parse", *base])
    compile_alpha = _invoke(["compile", *base, "--select", "alpha"])
    return {
        "project": project,
        "profiles": profiles,
        "target": target,
        "parse_result": parse_result,
        "compile_alpha": compile_alpha,
        "manifest_path": target / "manifest.json",
        "run_results_path": target / "run_results.json",
        "compiled_files": sorted(
            p for p in target.rglob("*.sql") if "compiled" in p.parts
        ),
    }


@pytest.fixture(scope="module")
def inline_state(project_env):
    root = project_env["root"]
    project = project_env["project"]
    profiles = project_env["profiles"]
    target = root / "inline_target"
    base = _base_args(project, profiles, target)
    inline_compile = _invoke(
        ["compile", *base, "--inline", "select {{ 1 + 1 }} as two", "--output", "json"]
    )
    return {
        "target": target,
        "inline_compile": inline_compile,
        "manifest_path": target / "manifest.json",
    }


@pytest.fixture(scope="module")
def no_json_state(project_env):
    root = project_env["root"]
    project = project_env["project"]
    profiles = project_env["profiles"]
    target = root / "no_json_target"
    result = _invoke(
        ["parse", *_base_args(project, profiles, target), "--no-write-json"]
    )
    return {"target": target, "result": result}


@pytest.fixture(scope="module")
def partial_state(project_env):
    root = project_env["root"]
    project = project_env["project"]
    profiles = project_env["profiles"]
    target = root / "partial_target"
    base = _base_args(project, profiles, target)
    first_result = _invoke(["parse", *base])
    cache_path = target / "partial_parse.msgpack"
    first_mtime = cache_path.stat().st_mtime if cache_path.is_file() else None
    time.sleep(0.01)
    second_result = _invoke(["parse", *base])
    second_mtime = cache_path.stat().st_mtime if cache_path.is_file() else None
    no_partial_target = root / "no_partial_target"
    no_partial_result = _invoke(
        [
            "parse",
            *_base_args(project, profiles, no_partial_target),
            "--no-partial-parse",
        ]
    )
    return {
        "cache_path": cache_path,
        "first_result": first_result,
        "second_result": second_result,
        "first_mtime": first_mtime,
        "second_mtime": second_mtime,
        "no_partial_result": no_partial_result,
    }


@pytest.fixture(scope="module")
def invalid_ref_result(project_env):
    invalid_root = project_env["root"] / "invalid_ref"
    invalid_project, invalid_profiles, invalid_target = _make_project(
        invalid_root, "broken"
    )
    _write_text(invalid_project / "models" / "broken.sql", "select * from {{ ref('missing_model') }}\n")
    return _invoke(
        ["parse", *_base_args(invalid_project, invalid_profiles, invalid_target)]
    )


@pytest.fixture(scope="module")
def invalid_combo_result(project_env):
    return _invoke(
        [
            "list",
            *_base_args(
                project_env["project"],
                project_env["profiles"],
                project_env["root"] / "invalid_combo_target",
            ),
            "--models",
            "alpha",
            "--select",
            "beta",
        ]
    )


@pytest.fixture(scope="module")
def missing_project_result(project_env):
    root = project_env["root"]
    return _invoke(
        [
            "parse",
            "--project-dir",
            str(root / "missing"),
            "--profiles-dir",
            str(project_env["profiles"]),
            "--target-path",
            str(root / "missing_target"),
            "--no-version-check",
            "--quiet",
        ]
    )


def _manifest(state):
    return _load_json(state["manifest_path"])


def _model_node(state, name):
    return next(
        node for node in _manifest(state)["nodes"].values() if node["name"] == name
    )


def _json_rows(list_state):
    return [json.loads(row) for row in list_state["list_json"].result]


def test_invalid_ref_parse_fails(invalid_ref_result):
    assert invalid_ref_result.success is False


def test_missing_project_fails(missing_project_result):
    assert missing_project_result.success is False


def test_models_and_select_are_mutually_exclusive(invalid_combo_result):
    assert invalid_combo_result.success is False
    assert invalid_combo_result.exception is not None


def test_usage_failure_has_no_result(invalid_combo_result):
    assert invalid_combo_result.result is None


def test_parse_runner_succeeds(parse_state):
    assert parse_state["parse_result"].success is True
    assert parse_state["parse_result"].exception is None


def test_parse_runner_returns_manifest_like_result(parse_state):
    result = parse_state["parse_result"].result
    assert result is not None
    assert hasattr(result, "nodes")


def test_parse_runner_returns_runner_result_object(parse_state):
    assert isinstance(parse_state["parse_result"], dbtRunnerResult)


def test_parse_writes_manifest_json(parse_state):
    assert parse_state["manifest_path"].is_file()


def test_parse_writes_semantic_manifest_json(parse_state):
    assert parse_state["semantic_manifest_path"].is_file()


def test_parse_writes_perf_info_json(parse_state):
    assert parse_state["perf_info_path"].is_file()


def test_parse_writes_partial_parse_cache(parse_state):
    assert parse_state["partial_parse_path"].is_file()


def test_manifest_has_public_resource_collections(parse_state):
    manifest = _manifest(parse_state)
    for key in ["nodes", "sources", "exposures", "macros", "parent_map", "child_map", "disabled"]:
        assert key in manifest


def test_manifest_contains_enabled_models(parse_state):
    names = {node["name"] for node in _manifest(parse_state)["nodes"].values()}
    assert {"alpha", "beta"}.issubset(names)


def test_manifest_model_identity_fields_are_public(parse_state):
    alpha = _model_node(parse_state, "alpha")
    for key in ["name", "unique_id", "package_name", "path", "original_file_path", "resource_type"]:
        assert alpha[key]


def test_manifest_source_identity_is_written(parse_state):
    sources = list(_manifest(parse_state)["sources"].values())
    assert any(source["name"] == "orders" and source["source_name"] == "raw" for source in sources)


def test_manifest_exposure_identity_is_written(parse_state):
    exposures = list(_manifest(parse_state)["exposures"].values())
    assert any(exposure["name"] == "weekly_dashboard" for exposure in exposures)


def test_parse_only_does_not_compile_model_code(parse_state):
    assert not _model_node(parse_state, "beta").get("compiled_code")


def test_list_output_name_succeeds(list_state):
    assert list_state["list_names"].success is True
    assert isinstance(list_state["list_names"].result, list)


def test_list_output_name_includes_models(list_state):
    assert {"alpha", "beta"}.issubset(set(list_state["list_names"].result))


def test_list_output_name_includes_source(list_state):
    assert "raw.orders" in set(list_state["list_names"].result)


def test_list_output_name_includes_exposure(list_state):
    assert "weekly_dashboard" in set(list_state["list_names"].result)


def test_ls_alias_matches_list_names(list_state):
    assert list_state["ls_names"].success is True
    assert list_state["ls_names"].result == list_state["list_names"].result


def test_list_output_path_returns_original_model_paths(list_state):
    paths = set(list_state["list_paths"].result)
    assert "models/alpha.sql" in paths
    assert "models/beta.sql" in paths


def test_list_json_rows_are_json_objects(list_state):
    rows = _json_rows(list_state)
    assert rows
    assert all(isinstance(row, dict) for row in rows)


def test_list_json_honors_requested_output_keys(list_state):
    row = next(row for row in _json_rows(list_state) if row["name"] == "alpha")
    assert set(row) == {"name", "resource_type", "unique_id", "original_file_path"}


def test_list_json_unique_ids_resolve_in_manifest(list_state):
    manifest = _manifest(list_state)
    manifest_ids = set(manifest["nodes"]) | set(manifest["sources"]) | set(manifest["exposures"])
    assert all(row["unique_id"] in manifest_ids for row in _json_rows(list_state))


def test_list_output_exclude_removes_selected_model(list_state):
    result = _invoke(["list", *_base_args(list_state["project"], list_state["profiles"], list_state["target"]), "--output", "name", "--exclude", "alpha"])
    assert result.success is True
    assert "alpha" not in result.result


def test_list_resource_type_analysis_can_select_analysis(list_state):
    result = _invoke(["list", *_base_args(list_state["project"], list_state["profiles"], list_state["target"]), "--resource-type", "analysis", "--output", "name"])
    assert result.success is True
    assert result.result == ["rollup"]


def test_list_default_does_not_include_analysis(list_state):
    assert "rollup" not in set(list_state["list_names"].result)


def test_list_models_flag_selects_models_only(list_state):
    result = _invoke(["list", *_base_args(list_state["project"], list_state["profiles"], list_state["target"]), "--models", "alpha", "--output", "name"])
    assert result.success is True
    assert result.result == ["alpha"]


def test_empty_selection_returns_empty_list(list_state):
    result = _invoke(["list", *_base_args(list_state["project"], list_state["profiles"], list_state["target"]), "--select", "tag:does_not_exist", "--output", "name"])
    assert result.success is True
    assert result.result == []


def test_compile_selected_model_succeeds(compile_state):
    assert compile_state["compile_alpha"].success is True
    assert compile_state["compile_alpha"].exception is None


def test_compile_writes_run_results(compile_state):
    assert compile_state["run_results_path"].is_file()


def test_compile_run_results_only_include_selected_node(compile_state):
    rows = _load_json(compile_state["run_results_path"])["results"]
    names = {row["unique_id"].split(".")[-1] for row in rows}
    assert "alpha" in names
    assert "beta" not in names


def test_compile_result_status_is_success(compile_state):
    rows = _load_json(compile_state["run_results_path"])["results"]
    assert rows[0]["status"] == "success"


def test_compile_result_maps_to_manifest(compile_state):
    unique_id = _load_json(compile_state["run_results_path"])["results"][0]["unique_id"]
    assert unique_id in _manifest(compile_state)["nodes"]


def test_compile_result_is_marked_compiled(compile_state):
    rows = _load_json(compile_state["run_results_path"])["results"]
    assert rows[0]["compiled"] is True


def test_compile_manifest_has_compiled_code_for_selected_model(compile_state):
    alpha_id = _model_node(compile_state, "alpha")["unique_id"]
    assert "select 1 as id" in _manifest(compile_state)["nodes"][alpha_id]["compiled_code"]


def test_compile_writes_compiled_sql_file(compile_state):
    assert compile_state["compiled_files"]


def test_compiled_file_matches_manifest_compiled_code(compile_state):
    compiled_text = "\n".join(path.read_text(encoding="utf-8") for path in compile_state["compiled_files"])
    alpha_id = _model_node(compile_state, "alpha")["unique_id"]
    assert _manifest(compile_state)["nodes"][alpha_id]["compiled_code"].strip() in compiled_text


def test_compile_inline_succeeds(inline_state):
    assert inline_state["inline_compile"].success is True


def test_compile_inline_result_contains_inline_query(inline_state):
    text = json.dumps(inline_state["inline_compile"].result, default=str)
    assert "inline_query" in text


def test_inline_query_is_not_persisted_in_manifest_nodes(inline_state):
    names = {node["name"] for node in _manifest(inline_state)["nodes"].values()}
    assert "inline_query" not in names


def test_no_write_json_preserves_runner_result(no_json_state):
    assert no_json_state["result"].success is True
    assert no_json_state["result"].result is not None


def test_no_write_json_suppresses_manifest_file(no_json_state):
    assert no_json_state["result"].success is True
    assert not (no_json_state["target"] / "manifest.json").exists()


def test_partial_parse_first_invocation_succeeds(partial_state):
    assert partial_state["first_result"].success is True


def test_partial_parse_second_invocation_succeeds(partial_state):
    assert partial_state["second_result"].success is True


def test_partial_parse_cache_persists_across_invocations(partial_state):
    assert partial_state["cache_path"].is_file()
    assert partial_state["first_mtime"] is not None
    assert partial_state["second_mtime"] >= partial_state["first_mtime"]


def test_no_partial_parse_still_returns_manifest(partial_state):
    assert partial_state["no_partial_result"].success is True
    assert hasattr(partial_state["no_partial_result"].result, "nodes")


def test_target_path_contains_all_parse_artifacts(compile_state):
    names = {path.name for path in compile_state["target"].iterdir()}
    assert {"manifest.json", "semantic_manifest.json", "perf_info.json", "partial_parse.msgpack", "run_results.json"}.issubset(names)


def test_target_path_redirects_compiled_files(compile_state):
    assert compile_state["compiled_files"]
    assert all(str(path).startswith(str(compile_state["target"])) for path in compile_state["compiled_files"])


def test_manifest_and_list_agree_on_model_names(list_state):
    manifest_model_names = {node["name"] for node in _manifest(list_state)["nodes"].values() if node["resource_type"] == "model"}
    assert manifest_model_names.issubset(set(list_state["list_names"].result))


def test_manifest_and_list_json_agree_on_original_paths(list_state):
    manifest_paths = {node["unique_id"]: node["original_file_path"] for node in _manifest(list_state)["nodes"].values()}
    for row in _json_rows(list_state):
        if row["unique_id"] in manifest_paths:
            assert row["original_file_path"] == manifest_paths[row["unique_id"]]


def test_runner_list_matches_cli_alias_projection(list_state):
    runner = dbtRunner(manifest=list_state["parse_result"].result)
    result = runner.invoke(["list", *_base_args(list_state["project"], list_state["profiles"], list_state["target"]), "--output", "name"])
    assert result.success is True
    assert result.result == list_state["list_names"].result
