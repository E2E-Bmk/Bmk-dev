# Spec2Repo oracle - atomic tests for pre-commit-hooks-fullrepro-002
import os
import shutil
import subprocess
import sys

import pytest

from pre_commit.clientlib import (
    HOOK_TYPES,
    STAGES,
    InvalidConfigError,
    InvalidManifestError,
    check_min_version,
    check_type_tag,
    load_config,
    load_manifest,
    transform_stage,
)
from pre_commit.color import format_color, use_color
from pre_commit.main import main
from pre_commit.parse_shebang import ExecutableNotFoundError, normalize_cmd
from pre_commit.prefix import Prefix
from pre_commit.repository import all_hooks
from pre_commit.store import Store
from pre_commit.util import CalledProcessError, cmd_output, cmd_output_b
from pre_commit.xargs import ArgumentTooLongError, partition, xargs


def _write(path, contents):
    path.write_text(contents, encoding="UTF-8")
    return path


def _git(repo, *args):
    if shutil.which("git") is None:
        pytest.skip("git is required for repository workflow tests")
    subprocess.run(
        ("git",) + args,
        cwd=str(repo),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _init_git_repo(path):
    _git(path, "init")
    _git(path, "config", "user.email", "precommit@example.com")
    _git(path, "config", "user.name", "Pre Commit")


def _local_config(hook_body):
    return "repos:\n- repo: local\n  hooks:\n" + hook_body


def _simple_repo(tmp_path, monkeypatch, config_text, filename="tracked.txt", contents="hello\n"):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _write(repo / filename, contents)
    _git(repo, "add", filename)
    cfg = _write(repo / ".pre-commit-config.yaml", config_text)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "pre_commit_home"))
    return repo, cfg


def _run_pre_commit_module(repo, *args):
    return subprocess.run(
        (sys.executable, "-m", "pre_commit") + args,
        cwd=str(repo),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def test_hook_types_are_documented_git_hook_types():
    assert set(HOOK_TYPES) == {
        "commit-msg",
        "post-checkout",
        "post-commit",
        "post-merge",
        "post-rewrite",
        "pre-commit",
        "pre-merge-commit",
        "pre-push",
        "pre-rebase",
        "prepare-commit-msg",
    }
    assert "manual" not in HOOK_TYPES


def test_stages_extend_hook_types_with_manual():
    assert set(STAGES) == set(HOOK_TYPES) | {"manual"}


def test_legacy_stage_names_are_normalized():
    assert transform_stage("commit") == "pre-commit"
    assert transform_stage("push") == "pre-push"
    assert transform_stage("merge-commit") == "pre-merge-commit"
    assert transform_stage("pre-commit") == "pre-commit"


def test_use_color_resolves_always_and_never():
    assert use_color("always") is True
    assert use_color("never") is False


def test_normalize_cmd_resolves_existing_executable():
    normalized = normalize_cmd((sys.executable, "-c", "print('ok')"))
    assert normalized[0] == os.path.normpath(sys.executable)
    assert normalized[1:] == ("-c", "print('ok')")


def test_normalize_cmd_raises_for_missing_executable():
    with pytest.raises(ExecutableNotFoundError):
        normalize_cmd(("definitely_missing_pre_commit_executable_zz",))


def test_cmd_output_returns_text_streams():
    code, stdout, stderr = cmd_output(sys.executable, "-c", "print('abc')", check=True)
    assert code == 0
    assert stdout.strip() == "abc"
    assert stderr == ""


def test_cmd_output_b_returns_bytes_streams():
    code, stdout, stderr = cmd_output_b(
        sys.executable,
        "-c",
        "import sys; sys.stdout.buffer.write(b'abc')",
        check=True,
    )
    assert code == 0
    assert stdout == b"abc"
    assert stderr == b""


def test_cmd_output_can_return_nonzero_without_checking():
    code, stdout, stderr = cmd_output(
        sys.executable,
        "-c",
        "import sys; sys.exit(7)",
        check=False,
    )
    assert code == 7
    assert stdout == ""
    assert stderr == ""


def test_cmd_output_checked_nonzero_raises_called_process_error():
    with pytest.raises(CalledProcessError) as excinfo:
        cmd_output(sys.executable, "-c", "import sys; sys.exit(7)", check=True)
    assert excinfo.value.returncode == 7
    assert excinfo.value.cmd


def test_partition_returns_executable_batches_and_handles_empty_args():
    assert partition(("cmd",), [], target_concurrency=2, _max_length=100) == (("cmd",),)
    assert partition(("cmd",), ["a", "b"], target_concurrency=2, _max_length=100) == (
        ("cmd", "a", "b"),
    )


def test_partition_rejects_argument_lists_that_cannot_fit():
    with pytest.raises(ArgumentTooLongError):
        partition(("verylongcommand",), ["verylongargument"], target_concurrency=1, _max_length=5)


def test_cli_validate_config_returns_zero_for_valid_and_nonzero_for_invalid(tmp_path):
    good = _write(tmp_path / "good.yaml", "repos: []\n")
    bad = _write(tmp_path / "bad.yaml", _local_config("  - id: h\n"))
    assert main(("validate-config", str(good))) == 0
    assert main(("validate-config", str(bad))) != 0


def test_cli_validate_manifest_returns_zero_for_valid_and_nonzero_for_invalid(tmp_path):
    good = _write(
        tmp_path / "manifest.yaml",
        "- id: h\n  name: Hook\n  entry: echo hi\n  language: system\n",
    )
    bad = _write(tmp_path / "bad-manifest.yaml", "- id: h\n")
    assert main(("validate-manifest", str(good))) == 0
    assert main(("validate-manifest", str(bad))) != 0


def test_cli_sample_config_prints_yaml_example(capsys):
    assert main(("sample-config",)) == 0
    out = capsys.readouterr().out
    assert "repos:" in out
    assert "hooks:" in out


def test_cli_validate_config_accepts_multiple_valid_files(tmp_path):
    first = _write(tmp_path / "first.yaml", "repos: []\n")
    second = _write(tmp_path / "second.yaml", "repos: []\n")
    assert main(("validate-config", str(first), str(second))) == 0


def test_cli_validate_config_fails_when_any_file_is_invalid(tmp_path):
    good = _write(tmp_path / "good.yaml", "repos: []\n")
    bad = _write(tmp_path / "bad.yaml", "minimum_pre_commit_version: '0'\n")
    assert main(("validate-config", str(good), str(bad))) == 1


def test_cli_validate_manifest_accepts_multiple_valid_files(tmp_path):
    contents = "- id: h\n  name: Hook\n  entry: echo hi\n  language: system\n"
    first = _write(tmp_path / "first.yaml", contents)
    second = _write(tmp_path / "second.yaml", contents)
    assert main(("validate-manifest", str(first), str(second))) == 0


def test_cli_validate_manifest_fails_when_any_file_is_invalid(tmp_path):
    good = _write(
        tmp_path / "good.yaml",
        "- id: h\n  name: Hook\n  entry: echo hi\n  language: system\n",
    )
    bad = _write(tmp_path / "bad.yaml", "- id: h\n")
    assert main(("validate-manifest", str(good), str(bad))) == 1
