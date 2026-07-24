# Spec2Repo oracle - atomic tests for dvc-fullrepro-001
import os
import subprocess
import sys
from pathlib import Path

import yaml

from dvc.repo import Repo


def _run_python(cwd, code):
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=90,
    )


def _run_dvc(cwd, *args):
    env = os.environ.copy()
    env["DVC_TEST"] = "true"
    env["DVC_NO_ANALYTICS"] = "1"
    return subprocess.run(
        ["dvc", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=env,
        timeout=90,
    )


def test_top_level_dvc_metadata_names_are_importable(tmp_path):
    result = _run_python(
        tmp_path,
        "import dvc\n"
        "assert isinstance(dvc.__version__, str) and dvc.__version__\n"
        "assert isinstance(dvc.version_tuple, tuple) and dvc.version_tuple\n"
        "assert hasattr(dvc, 'PKG')\n",
    )
    assert result.returncode == 0, result.stderr


def test_dvc_api_public_names_are_importable(tmp_path):
    result = _run_python(
        tmp_path,
        "from dvc.api import (\n"
        "    DVCFileSystem, all_branches, all_commits, all_tags,\n"
        "    artifacts_show, exp_save, exp_show, get_dataset, get_url,\n"
        "    metrics_show, open, params_show, read,\n"
        ")\n"
        "exports = (\n"
        "    DVCFileSystem, all_branches, all_commits, all_tags,\n"
        "    artifacts_show, exp_save, exp_show, get_dataset, get_url,\n"
        "    metrics_show, open, params_show, read,\n"
        ")\n"
        "assert all(callable(item) for item in exports)\n",
    )
    assert result.returncode == 0, result.stderr


def test_installed_dvc_console_entry_point_launches(tmp_path):
    result = _run_dvc(tmp_path, "--help")
    assert result.returncode == 0


def _load_stage(root, name="build"):
    data = yaml.safe_load((root / "dvc.yaml").read_text(encoding="utf-8"))
    return data["stages"][name]


def _repo_run(root, **kwargs):
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root), uninitialized=True).run(no_exec=True, **kwargs)
    finally:
        os.chdir(old_cwd)


def _repo_freeze(root, target):
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root), uninitialized=True).freeze(target)
    finally:
        os.chdir(old_cwd)


def _repo_unfreeze(root, target):
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root), uninitialized=True).unfreeze(target)
    finally:
        os.chdir(old_cwd)


def test_repo_run_no_exec_records_command(tmp_path):
    _repo_run(tmp_path, name="build", cmd="echo hello")
    assert _load_stage(tmp_path)["cmd"] == "echo hello"


def test_repo_run_no_exec_records_description(tmp_path):
    _repo_run(tmp_path, name="build", cmd="echo ok", desc="public note")
    assert _load_stage(tmp_path)["desc"] == "public note"


def test_repo_run_no_exec_records_working_directory(tmp_path):
    (tmp_path / "subdir").mkdir()
    _repo_run(tmp_path, name="build", cmd="echo ok", wdir="subdir")
    assert _load_stage(tmp_path)["wdir"] == "subdir"


def test_repo_run_no_exec_records_dependency(tmp_path):
    (tmp_path / "input.txt").write_text("input", encoding="utf-8")
    _repo_run(tmp_path, name="build", cmd="echo ok", deps=["input.txt"])
    assert _load_stage(tmp_path)["deps"] == ["input.txt"]


def test_repo_run_no_exec_records_default_params_file_key(tmp_path):
    (tmp_path / "params.yaml").write_text("alpha: red\n", encoding="utf-8")
    _repo_run(tmp_path, name="build", cmd="echo ok", params=["alpha"])
    assert _load_stage(tmp_path)["params"] == ["alpha"]


def test_repo_run_no_exec_records_cached_output(tmp_path):
    _repo_run(tmp_path, name="build", cmd="echo ok", outs=["result.txt"])
    assert _load_stage(tmp_path)["outs"] == ["result.txt"]


def test_repo_run_no_exec_records_metric(tmp_path):
    _repo_run(tmp_path, name="build", cmd="echo ok", metrics=["metric.json"])
    assert _load_stage(tmp_path)["metrics"] == ["metric.json"]


def test_repo_run_no_exec_records_plot(tmp_path):
    _repo_run(tmp_path, name="build", cmd="echo ok", plots=["plot.csv"])
    assert _load_stage(tmp_path)["plots"] == ["plot.csv"]


def test_repo_run_no_exec_records_always_changed(tmp_path):
    _repo_run(tmp_path, name="build", cmd="echo ok", always_changed=True)
    assert _load_stage(tmp_path)["always_changed"] is True


def test_repo_run_force_replaces_existing_stage_command(tmp_path):
    (tmp_path / "dvc.yaml").write_text(
        yaml.safe_dump({"stages": {"build": {"cmd": "echo old"}}}, sort_keys=False),
        encoding="utf-8",
    )
    _repo_run(tmp_path, name="build", cmd="echo new", force=True)
    assert _load_stage(tmp_path)["cmd"] == "echo new"


def test_repo_freeze_marks_selected_stage_frozen(tmp_path):
    (tmp_path / "dvc.yaml").write_text(
        yaml.safe_dump(
            {
                "stages": {
                    "prepare": {"cmd": "echo prepare"},
                    "train": {"cmd": "echo train"},
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _repo_freeze(tmp_path, "train")
    data = yaml.safe_load((tmp_path / "dvc.yaml").read_text(encoding="utf-8"))
    assert data["stages"]["train"]["frozen"] is True
    assert "frozen" not in data["stages"]["prepare"]


def test_repo_unfreeze_removes_selected_stage_frozen_flag(tmp_path):
    (tmp_path / "dvc.yaml").write_text(
        yaml.safe_dump(
            {
                "stages": {
                    "prepare": {"cmd": "echo prepare", "frozen": True},
                    "train": {"cmd": "echo train", "frozen": True},
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _repo_unfreeze(tmp_path, "train")
    data = yaml.safe_load((tmp_path / "dvc.yaml").read_text(encoding="utf-8"))
    assert "frozen" not in data["stages"]["train"]
    assert data["stages"]["prepare"]["frozen"] is True
