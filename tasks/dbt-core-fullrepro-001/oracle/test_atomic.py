"""Atomic oracle tests for dbt-core-fullrepro-001.

Each test exercises ONE public API and ONE behavior.
Independently solvable: passes if only the tested API is correctly implemented.
"""

import json
import subprocess
import sys
from pathlib import Path

from dbt.cli.main import cli, dbtRunner, dbtRunnerResult
from dbt.cli import dbt_cli

from conftest import (
    PROJECT_NAME,
    MODEL_ALPHA,
    MODEL_BETA,
    MODEL_GAMMA,
    base_args,
    create_dbt_project,
    invoke_dbt,
    write_text,
)


# ---------------------------------------------------------------------------
# Helper: single-model project for atomic isolation
# ---------------------------------------------------------------------------


def _atomic_project(root: Path) -> list:
    """Minimal one-model project returning base CLI args."""
    project = root / PROJECT_NAME
    profiles = root / "profiles"
    target = root / "target"

    write_text(
        project / "dbt_project.yml",
        f"name: {PROJECT_NAME}\nversion: '2.0'\nprofile: {PROJECT_NAME}\n"
        f"model-paths: [models]\n",
    )
    write_text(
        profiles / "profiles.yml",
        "\n".join([
            f"{PROJECT_NAME}:",
            "  target: dev",
            "  outputs:",
            "    dev:",
            "      type: duckdb",
            f"      path: {root / 'atomic.duckdb'}",
            "      schema: main",
            "      threads: 1",
        ]) + "\n",
    )
    write_text(
        project / "models" / f"{MODEL_ALPHA}.sql",
        "select 42 as region_id, 'north' as region_name\n",
    )
    return base_args(project, profiles, target)


# ===========================================================================
# Runner instantiation and API surface
# ===========================================================================


def test_runner_instantiation_returns_runner_object():
    runner = dbtRunner()
    assert runner is not None
    assert isinstance(runner, dbtRunner)
    outcome = runner.invoke(["--version"])
    assert outcome.success is True


def test_runner_accepts_manifest_keyword_argument():
    runner = dbtRunner(manifest=None)
    outcome = runner.invoke(["--version"])
    assert outcome.success is True


def test_runner_result_exposes_success_attribute():
    outcome = dbtRunnerResult(success=True)
    assert outcome.success is True


def test_runner_result_exposes_exception_attribute():
    outcome = dbtRunnerResult(success=True)
    assert outcome.exception is None


def test_runner_result_exposes_result_attribute():
    outcome = dbtRunnerResult(success=True)
    assert outcome.result is None


def test_runner_result_preserves_attached_exception():
    err = RuntimeError("test_error_sentinel")
    outcome = dbtRunnerResult(success=False, exception=err)
    assert outcome.exception is err
    assert outcome.success is False


def test_dbt_cli_is_same_object_as_cli():
    assert dbt_cli is cli


def test_runner_supports_repeated_invocations():
    runner = dbtRunner()
    first = runner.invoke(["--version"])
    second = runner.invoke(["--version"])
    assert first.success is True
    assert second.success is True


# ===========================================================================
# Parse command — single behaviors
# ===========================================================================


def test_parse_valid_project_returns_success(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["parse", *args])
    assert isinstance(outcome, dbtRunnerResult)
    assert outcome.success is True


def test_parse_result_contains_project_model(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["parse", *args])
    assert outcome.success is True
    assert f"model.{PROJECT_NAME}.{MODEL_ALPHA}" in outcome.result.nodes


def test_parse_invalid_project_dir_fails(tmp_path):
    outcome = invoke_dbt([
        "parse",
        "--project-dir", str(tmp_path / "nonexistent_project"),
        "--no-version-check", "--quiet",
    ])
    assert outcome.success is False


def test_parse_writes_manifest_json(tmp_path):
    args = _atomic_project(tmp_path)
    invoke_dbt(["parse", *args])
    assert (tmp_path / "target" / "manifest.json").is_file()


def test_parse_writes_semantic_manifest_json(tmp_path):
    args = _atomic_project(tmp_path)
    invoke_dbt(["parse", *args])
    assert (tmp_path / "target" / "semantic_manifest.json").is_file()


def test_parse_writes_perf_info_json(tmp_path):
    args = _atomic_project(tmp_path)
    invoke_dbt(["parse", *args])
    assert (tmp_path / "target" / "perf_info.json").is_file()


def test_parse_writes_partial_parse_msgpack(tmp_path):
    args = _atomic_project(tmp_path)
    invoke_dbt(["parse", *args])
    assert (tmp_path / "target" / "partial_parse.msgpack").is_file()


def test_parse_no_write_json_suppresses_manifest(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["parse", *args, "--no-write-json"])
    assert outcome.success is True
    assert not (tmp_path / "target" / "manifest.json").exists()


def test_parse_no_partial_parse_still_succeeds(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["parse", *args, "--no-partial-parse"])
    assert outcome.success is True
    assert outcome.result is not None
    assert f"model.{PROJECT_NAME}.{MODEL_ALPHA}" in outcome.result.nodes


def test_parse_accepts_threads_option(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["parse", *args, "--threads", "4"])
    assert outcome.success is True


# ===========================================================================
# List command — output modes
# ===========================================================================


def test_list_output_name_returns_model_name(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["list", *args, "--output", "name"])
    assert outcome.success is True
    assert MODEL_ALPHA in outcome.result


def test_list_output_path_returns_file_path(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["list", *args, "--output", "path"])
    assert outcome.success is True
    assert any(MODEL_ALPHA in p for p in outcome.result)


def test_list_output_json_returns_parseable_json(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["list", *args, "--output", "json"])
    assert outcome.success is True
    rows = [json.loads(r) for r in outcome.result]
    assert all(isinstance(r, dict) for r in rows)
    assert len(rows) >= 1


def test_list_output_selector_returns_fqn_strings(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["list", *args, "--output", "selector"])
    assert outcome.success is True
    assert f"{PROJECT_NAME}.{MODEL_ALPHA}" in outcome.result


def test_list_output_json_respects_output_keys(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt([
        "list", *args, "--output", "json",
        "--output-keys", "name", "unique_id",
    ])
    assert outcome.success is True
    row = json.loads(outcome.result[0])
    assert set(row.keys()) == {"name", "unique_id"}


# ===========================================================================
# Error semantics — usage rejections
# ===========================================================================


def test_list_models_and_select_conflict(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["list", *args, "--models", MODEL_ALPHA, "--select", MODEL_BETA])
    assert outcome.success is False
    assert isinstance(outcome.exception, BaseException)


def test_unknown_command_fails():
    outcome = invoke_dbt(["nonexistent_subcommand_xyz"])
    assert outcome.success is False
    assert isinstance(outcome.exception, BaseException)


def test_invalid_output_choice_fails(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["list", *args, "--output", "xml"])
    assert outcome.success is False


def test_empty_selection_returns_empty_result(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["list", *args, "--select", "tag:nonexistent_tag_xyz", "--output", "name"])
    assert outcome.success is True
    assert outcome.result == []


# ===========================================================================
# Compile command — single behaviors
# ===========================================================================


def test_compile_selected_model_succeeds(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt(["compile", *args, "--select", MODEL_ALPHA])
    assert outcome.success is True
    assert outcome.exception is None


def test_compile_writes_run_results_json(tmp_path):
    args = _atomic_project(tmp_path)
    invoke_dbt(["compile", *args, "--select", MODEL_ALPHA])
    rr_path = tmp_path / "target" / "run_results.json"
    assert rr_path.is_file()


def test_compile_inline_query_succeeds(tmp_path):
    args = _atomic_project(tmp_path)
    outcome = invoke_dbt([
        "compile", *args,
        "--inline", "select {{ 2 + 3 }} as five",
        "--output", "json",
    ])
    assert outcome.success is True


# ===========================================================================
# Module-level execution
# ===========================================================================


def test_version_flag_succeeds_without_project():
    outcome = invoke_dbt(["--version"])
    assert isinstance(outcome, dbtRunnerResult)
    assert outcome.success is True
    assert outcome.exception is None


def test_module_execution_returns_zero_exit():
    proc = subprocess.run(
        [sys.executable, "-m", "dbt.cli.main", "--version"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    assert len(proc.stdout.strip()) > 0
