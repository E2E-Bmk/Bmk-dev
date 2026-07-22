"""Atomic tests for dvc-fullrepro-001.

Every test exercises exactly ONE public API entry-point and is independently
solvable: if only that API is correctly implemented the test passes.
"""

import pytest

import dvc
from conftest import (
    DvcException,
    init_repo,
    load_yaml,
    repo_freeze,
    repo_run,
    repo_status,
    repo_unfreeze,
    run_dvc,
    write_yaml,
)


# ===================================================================
# dvc module attributes
# ===================================================================

def test_version_attribute_is_nonempty_string():
    assert isinstance(dvc.__version__, str)
    assert len(dvc.__version__) > 0


def test_version_tuple_is_tuple_with_components():
    assert isinstance(dvc.version_tuple, tuple)
    assert len(dvc.version_tuple) >= 2


def test_pkg_attribute_is_nonempty_string():
    assert isinstance(dvc.PKG, str)
    assert len(dvc.PKG) > 0


# ===================================================================
# Repo.init
# ===================================================================

def test_init_no_scm_creates_dvc_directory(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    from dvc.repo import Repo
    Repo.init(root_dir=str(root), no_scm=True)
    assert (root / ".dvc").is_dir()


def test_init_no_scm_returns_repo_object(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    from dvc.repo import Repo
    result = Repo.init(root_dir=str(root), no_scm=True)
    assert result is not None
    assert isinstance(result, Repo)
    assert str(result.root_dir) == str(root)


# ===================================================================
# Repo constructor
# ===================================================================

def test_repo_opens_with_uninitialized_flag(tmp_path):
    from dvc.repo import Repo
    repo = Repo(str(tmp_path), uninitialized=True)
    assert repo is not None
    assert isinstance(repo, Repo)
    assert str(repo.root_dir) == str(tmp_path)


# ===================================================================
# Repo.run  no_exec — field recording
# ===================================================================

def test_run_no_exec_records_command_in_yaml(tmp_path):
    repo_run(tmp_path, name="compile", cmd="echo build-step")
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["cmd"] == "echo build-step"


def test_run_no_exec_records_dependency_list(tmp_path):
    (tmp_path / "data.csv").write_text("x", encoding="utf-8")
    repo_run(tmp_path, name="compile", cmd="echo ok", deps=["data.csv"])
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["deps"] == ["data.csv"]


def test_run_no_exec_records_params_key(tmp_path):
    (tmp_path / "params.yaml").write_text("gamma: violet\n", encoding="utf-8")
    repo_run(tmp_path, name="compile", cmd="echo ok", params=["gamma"])
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["params"] == ["gamma"]


def test_run_no_exec_records_output_list(tmp_path):
    repo_run(tmp_path, name="compile", cmd="echo ok", outs=["artifact.bin"])
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["outs"] == ["artifact.bin"]


def test_run_no_exec_records_metric_output(tmp_path):
    repo_run(tmp_path, name="compile", cmd="echo ok", metrics=["scores.json"])
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["metrics"] == ["scores.json"]


def test_run_no_exec_records_plot_output(tmp_path):
    repo_run(tmp_path, name="compile", cmd="echo ok", plots=["chart.csv"])
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["plots"] == ["chart.csv"]


def test_run_no_exec_records_description_text(tmp_path):
    repo_run(tmp_path, name="compile", cmd="echo ok", desc="builds the package")
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["desc"] == "builds the package"


def test_run_no_exec_records_working_directory(tmp_path):
    (tmp_path / "sub").mkdir()
    repo_run(tmp_path, name="compile", cmd="echo ok", wdir="sub")
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["wdir"] == "sub"


def test_run_no_exec_records_always_changed_flag(tmp_path):
    repo_run(tmp_path, name="compile", cmd="echo ok", always_changed=True)
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["always_changed"] is True


def test_run_no_exec_records_command_list(tmp_path):
    repo_run(tmp_path, name="compile", cmd=["echo first", "echo second"])
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["cmd"] == ["echo first", "echo second"]


# ===================================================================
# Repo.run  no_exec — output & return value
# ===================================================================

def test_run_no_exec_does_not_create_output_file(tmp_path):
    repo_run(tmp_path, name="compile", cmd="echo ok", outs=["artifact.bin"])
    assert not (tmp_path / "artifact.bin").exists()


def test_run_no_exec_returns_stage_with_correct_name(tmp_path):
    stage = repo_run(tmp_path, name="compile", cmd="echo ok")
    assert stage.name == "compile"


def test_run_no_exec_returns_stage_with_correct_cmd(tmp_path):
    stage = repo_run(tmp_path, name="compile", cmd="echo build-step")
    assert stage.cmd == "echo build-step"


# ===================================================================
# Repo.run  force / duplicate-name
# ===================================================================

def test_run_force_replaces_existing_stage(tmp_path):
    write_yaml(tmp_path / "dvc.yaml", {"stages": {"compile": {"cmd": "echo old"}}})
    repo_run(tmp_path, name="compile", cmd="echo replacement", force=True)
    stage = load_yaml(tmp_path / "dvc.yaml")["stages"]["compile"]
    assert stage["cmd"] == "echo replacement"


def test_run_without_force_on_existing_stage_raises(tmp_path):
    write_yaml(tmp_path / "dvc.yaml", {"stages": {"compile": {"cmd": "echo old"}}})
    with pytest.raises(DvcException):
        repo_run(tmp_path, name="compile", cmd="echo replacement")


# ===================================================================
# Repo.freeze / Repo.unfreeze
# ===================================================================

def test_freeze_writes_frozen_true_to_target_stage(tmp_path):
    write_yaml(tmp_path / "dvc.yaml", {
        "stages": {
            "digest": {"cmd": "echo digest"},
            "bundle": {"cmd": "echo bundle"},
        },
    })
    repo_freeze(tmp_path, "digest")
    data = load_yaml(tmp_path / "dvc.yaml")
    assert data["stages"]["digest"]["frozen"] is True


def test_freeze_does_not_affect_other_stages(tmp_path):
    write_yaml(tmp_path / "dvc.yaml", {
        "stages": {
            "digest": {"cmd": "echo digest"},
            "bundle": {"cmd": "echo bundle"},
        },
    })
    repo_freeze(tmp_path, "digest")
    data = load_yaml(tmp_path / "dvc.yaml")
    assert "frozen" not in data["stages"]["bundle"]


def test_unfreeze_removes_frozen_flag_from_target(tmp_path):
    write_yaml(tmp_path / "dvc.yaml", {
        "stages": {
            "digest": {"cmd": "echo digest", "frozen": True},
            "bundle": {"cmd": "echo bundle", "frozen": True},
        },
    })
    repo_unfreeze(tmp_path, "digest")
    data = load_yaml(tmp_path / "dvc.yaml")
    assert data["stages"]["digest"].get("frozen") is not True


def test_unfreeze_does_not_affect_other_frozen_stages(tmp_path):
    write_yaml(tmp_path / "dvc.yaml", {
        "stages": {
            "digest": {"cmd": "echo digest", "frozen": True},
            "bundle": {"cmd": "echo bundle", "frozen": True},
        },
    })
    repo_unfreeze(tmp_path, "digest")
    data = load_yaml(tmp_path / "dvc.yaml")
    assert data["stages"]["bundle"]["frozen"] is True


# ===================================================================
# Repo.status (pre-built state, no reproduction needed)
# ===================================================================

def test_status_returns_dict_on_initialized_repo(tmp_path):
    root = init_repo(tmp_path / "proj")
    result = repo_status(root)
    assert isinstance(result, dict)
    assert result == {}


def test_status_reports_stage_without_lockfile_entry(tmp_path):
    root = init_repo(tmp_path / "proj")
    write_yaml(root / "dvc.yaml", {
        "stages": {"compute": {"cmd": "echo hi", "outs": ["result.txt"]}},
    })
    result = repo_status(root)
    assert isinstance(result, dict)
    assert "compute" in result


# ===================================================================
# CLI single-command tests
# ===================================================================

def test_cli_version_exits_zero_with_output(tmp_path):
    result = run_dvc(tmp_path, "--version", check=False)
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


def test_cli_help_exits_zero_with_output(tmp_path):
    result = run_dvc(tmp_path, "--help", check=False)
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


def test_cli_stage_add_writes_stage_to_yaml(tmp_path):
    root = init_repo(tmp_path / "proj")
    result = run_dvc(
        root, "stage", "add", "-n", "compile",
        "-o", "output.bin",
        "echo", "compile",
    )
    assert result.returncode == 0
    stages = load_yaml(root / "dvc.yaml")["stages"]
    assert "compile" in stages
    assert stages["compile"]["cmd"] == "echo compile"


def test_cli_stage_list_reports_stages_from_existing_yaml(tmp_path):
    root = init_repo(tmp_path / "proj")
    write_yaml(root / "dvc.yaml", {
        "stages": {
            "digest": {"cmd": "echo digest"},
            "bundle": {"cmd": "echo bundle"},
        },
    })
    result = run_dvc(root, "stage", "list", "--name-only")
    names = sorted(result.stdout.strip().splitlines())
    assert names == ["bundle", "digest"]


# ===================================================================
# Error paths (CLI)
# ===================================================================

def test_invalid_stage_name_rejected_by_cli(tmp_path):
    root = init_repo(tmp_path / "proj")
    result = run_dvc(
        root, "stage", "add", "-n", "inv@lid",
        "-o", "bad.txt", "echo", "bad",
        check=False,
    )
    assert result.returncode != 0
    assert not (root / "dvc.yaml").exists() or \
        "inv@lid" not in load_yaml(root / "dvc.yaml").get("stages", {})


def test_duplicate_output_path_rejected_by_cli(tmp_path):
    root = init_repo(tmp_path / "proj")
    write_yaml(root / "dvc.yaml", {
        "stages": {"first": {"cmd": "echo first", "outs": ["shared.bin"]}},
    })
    before = (root / "dvc.yaml").read_bytes()
    result = run_dvc(
        root, "stage", "add", "-n", "second",
        "-o", "shared.bin", "echo", "second",
        check=False,
    )
    assert result.returncode != 0
    assert (root / "dvc.yaml").read_bytes() == before
