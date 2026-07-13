# Spec2Repo oracle - atomic tests for dbt-core-fullrepro-001
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


def test_invalid_ref_parse_fails(project_state):
    assert project_state["invalid_parse"].success is False


def test_missing_project_fails(project_state):
    assert project_state["missing_project"].success is False


def test_models_and_select_are_mutually_exclusive(project_state):
    assert project_state["invalid_combo"].success is False
    assert project_state["invalid_combo"].exception is not None


def test_usage_failure_has_no_result(project_state):
    assert project_state["invalid_combo"].result is None
