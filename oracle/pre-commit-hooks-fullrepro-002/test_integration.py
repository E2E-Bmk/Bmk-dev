# Spec2Repo oracle - integration tests for pre-commit-hooks-fullrepro-002
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from pre_commit.main import main


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


def _assert_nonzero_status(argv):
    status = main(argv)
    assert isinstance(status, int)
    assert status != 0


def test_cli_install_and_uninstall_manage_selected_hook_script(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: ok\n"
            "    name: Ok\n"
            "    entry: identity\n"
            "    language: meta\n"
        ),
    )
    hook_path = repo / ".git" / "hooks" / "pre-commit"
    assert main(("install", "--config", str(cfg), "--hook-type", "pre-commit")) == 0
    hook_text = hook_path.read_text(encoding="UTF-8", errors="ignore")
    assert hook_path.exists()
    assert "hook-impl" in hook_text
    assert "pre-commit" in hook_text
    assert main(("uninstall", "--hook-type", "pre-commit")) == 0
    assert not hook_path.exists()


def test_cli_run_fail_language_fails_and_reports_hook_id(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: block\n"
            "    name: Block\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = _run_pre_commit_module(repo, "run", "--all-files", "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    out = result.stdout
    assert "block" in out
    assert "block-msg" in out
    assert "tracked.txt" in out


def test_cli_run_skip_environment_skips_hook_id(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: block\n"
            "    name: Block\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    monkeypatch.setenv("SKIP", "block")
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0


def test_cli_run_skip_environment_accepts_alias(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: block\n"
            "    alias: alias-block\n"
            "    name: Block\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    monkeypatch.setenv("SKIP", "alias-block")
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0


def test_cli_run_pygrep_fails_when_pattern_matches(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: grep-alpha\n"
            "    name: Grep Alpha\n"
            "    entry: Alpha\n"
            "    language: pygrep\n"
            "    files: \\.txt$\n"
        ),
        contents="Alpha\nBeta\n",
    )
    result = _run_pre_commit_module(repo, "run", "--all-files", "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    out = result.stdout
    assert "grep-alpha" in out
    assert "tracked.txt" in out
    assert "Alpha" in out


def test_cli_run_pygrep_negate_passes_when_pattern_matches(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: grep-alpha\n"
            "    name: Grep Alpha\n"
            "    entry: Alpha\n"
            "    language: pygrep\n"
            "    args: [--negate]\n"
            "    files: \\.txt$\n"
        ),
        contents="Alpha\nBeta\n",
    )
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0


def test_cli_run_always_run_executes_even_without_matching_files(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: always\n"
            "    name: Always\n"
            "    entry: must-run\n"
            "    language: fail\n"
            "    files: \\.py$\n"
            "    always_run: true\n"
        ),
    )
    _assert_nonzero_status(
        ("run", "--all-files", "--config", str(cfg), "--color", "never")
    )


def test_cli_run_pass_filenames_false_omits_selected_filenames(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: no-files\n"
            "    name: No Files\n"
            "    entry: no-files-entry\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "    pass_filenames: false\n"
        ),
    )
    result = _run_pre_commit_module(
        repo, "run", "--files", "tracked.txt", "--config", str(cfg), "--color", "never"
    )
    assert result.returncode != 0
    out = result.stdout
    assert "no-files-entry" in out
    assert "tracked.txt" not in out


def test_cli_run_manual_stage_selects_manual_hooks(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: manual-block\n"
            "    name: Manual Block\n"
            "    entry: manual-block-entry\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "    stages: [manual]\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0
    _assert_nonzero_status(
        (
            "run",
            "--all-files",
            "--hook-stage",
            "manual",
            "--config",
            str(cfg),
            "--color",
            "never",
        )
    )


def test_cli_run_files_limits_hook_input_to_explicit_files(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: block\n"
            "    name: Block\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    _write(repo / "other.txt", "other\n")
    _git(repo, "add", "other.txt")
    result = _run_pre_commit_module(
        repo, "run", "--files", "tracked.txt", "--config", str(cfg), "--color", "never"
    )
    assert result.returncode != 0
    out = result.stdout
    assert "tracked.txt" in out
    assert "other.txt" not in out


def test_cli_migrate_config_wraps_legacy_repo_list(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    monkeypatch.chdir(repo)
    config = _write(
        repo / ".pre-commit-config.yaml",
        "- repo: local\n"
        "  hooks:\n"
        "  - id: h\n"
        "    name: Hook\n"
        "    entry: echo hi\n"
        "    language: system\n",
    )
    assert main(("migrate-config", "--config", str(config))) == 0
    migrated = yaml.safe_load(config.read_text(encoding="UTF-8"))
    assert isinstance(migrated, dict)
    assert migrated["repos"][0]["repo"] == "local"
    assert migrated["repos"][0]["hooks"][0]["id"] == "h"


def test_cli_migrate_config_rewrites_sha_key_to_rev(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    monkeypatch.chdir(repo)
    config = _write(
        repo / ".pre-commit-config.yaml",
        "repos:\n"
        "- repo: https://example.invalid/repo.git\n"
        "  sha: abc123\n"
        "  hooks:\n"
        "  - id: h\n",
    )
    assert main(("migrate-config", "--config", str(config))) == 0
    migrated = yaml.safe_load(config.read_text(encoding="UTF-8"))
    repository = migrated["repos"][0]
    assert repository["rev"] == "abc123"
    assert "sha" not in repository


def test_cli_migrate_config_rewrites_legacy_stage_names(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    monkeypatch.chdir(repo)
    config = _write(
        repo / ".pre-commit-config.yaml",
        "default_stages: [commit, push, merge-commit]\n"
        "repos:\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: h\n"
        "    name: Hook\n"
        "    entry: echo hi\n"
        "    language: system\n"
        "    stages: [commit]\n",
    )
    assert main(("migrate-config", "--config", str(config))) == 0
    migrated = yaml.safe_load(config.read_text(encoding="UTF-8"))
    assert migrated["default_stages"] == [
        "pre-commit",
        "pre-push",
        "pre-merge-commit",
    ]
    assert migrated["repos"][0]["hooks"][0]["stages"] == ["pre-commit"]


def test_cli_run_single_hook_id_limits_execution(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: first\n"
            "    name: First\n"
            "    entry: first-message\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "  - id: second\n"
            "    name: Second\n"
            "    entry: second-message\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = _run_pre_commit_module(repo, "run", "first", "--all-files", "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "first-message" in result.stdout
    assert "second-message" not in result.stdout


def test_cli_run_fail_fast_stops_after_first_failing_hook(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        "fail_fast: true\n"
        + _local_config(
            "  - id: first\n"
            "    name: First\n"
            "    entry: first-message\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "  - id: second\n"
            "    name: Second\n"
            "    entry: second-message\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = _run_pre_commit_module(
        repo, "run", "--all-files", "--config", str(cfg), "--color", "never"
    )
    assert result.returncode != 0
    assert "first-message" in result.stdout
    assert "second-message" not in result.stdout


def test_cli_run_skips_non_matching_files_without_always_run(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: py-only\n"
            "    name: Py Only\n"
            "    entry: should-not-run\n"
            "    language: fail\n"
            "    files: \\.py$\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0


def test_cli_run_default_stage_ignores_manual_only_hooks(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: manual-only\n"
            "    name: Manual Only\n"
            "    entry: manual-only-message\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "    stages: [manual]\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0


def test_cli_install_writes_each_selected_hook_type(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: ok\n"
            "    name: Ok\n"
            "    entry: no-match\n"
            "    language: pygrep\n"
        ),
    )

    assert main(
        (
            "install",
            "--config",
            str(cfg),
            "--hook-type",
            "pre-commit",
            "--hook-type",
            "pre-push",
        )
    ) == 0
    assert (repo / ".git" / "hooks" / "pre-commit").exists()
    assert (repo / ".git" / "hooks" / "pre-push").exists()


def test_cli_uninstall_restores_existing_legacy_hook(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: ok\n"
            "    name: Ok\n"
            "    entry: python -c \"import sys; sys.exit(0)\"\n"
            "    language: system\n"
        ),
    )
    hook_path = repo / ".git" / "hooks" / "pre-commit"
    legacy = "#!/bin/sh\necho legacy\n"
    _write(hook_path, legacy)

    assert main(("install", "--config", str(cfg), "--hook-type", "pre-commit")) == 0
    assert hook_path.read_text(encoding="UTF-8") != legacy
    assert main(("uninstall", "--hook-type", "pre-commit")) == 0
    assert hook_path.read_text(encoding="UTF-8") == legacy


def test_cli_init_templatedir_writes_selected_hook_script(tmp_path, monkeypatch):
    repo, _ = _simple_repo(tmp_path, monkeypatch, "repos: []\n")
    template = tmp_path / "template"

    assert main(("init-templatedir", str(template), "--hook-type", "pre-push")) == 0
    hook = template / "hooks" / "pre-push"
    assert hook.exists()
    assert "hook-impl" in hook.read_text(encoding="UTF-8", errors="ignore")
    assert repo.exists()


def test_cli_run_creates_and_clean_removes_configured_store(tmp_path, monkeypatch):
    _, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: ok\n"
            "    name: Ok\n"
            "    entry: no-match\n"
            "    language: pygrep\n"
        ),
    )
    store = tmp_path / "pre_commit_home"

    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0
    assert store.is_dir()
    assert any(store.iterdir())
    assert main(("clean",)) == 0
    assert not store.exists()


def test_cli_run_meta_identity_hook_resolves_and_passes(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        "repos:\n- repo: meta\n  hooks:\n  - id: identity\n",
    )

    result = _run_pre_commit_module(
        repo, "run", "identity", "--all-files", "--config", str(cfg), "--color", "never"
    )
    assert result.returncode == 0
    assert "identity" in result.stdout.lower()


def test_cli_validate_install_and_run_local_hook_workflow(tmp_path, monkeypatch):
    repo, cfg = _simple_repo(
        tmp_path,
        monkeypatch,
        _local_config(
            "  - id: ok\n"
            "    name: Ok\n"
            "    entry: no-match\n"
            "    language: pygrep\n"
            "    files: \\.txt$\n"
        ),
    )

    assert main(("validate-config", str(cfg))) == 0
    assert main(("install", "--config", str(cfg), "--hook-type", "pre-commit")) == 0
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 0
    assert (repo / ".git" / "hooks" / "pre-commit").exists()


def _hook_repository(tmp_path, *, hooks):
    hook_repo = tmp_path / "hook-repo"
    hook_repo.mkdir()
    _init_git_repo(hook_repo)
    _write(hook_repo / ".pre-commit-hooks.yaml", hooks)
    _git(hook_repo, "add", ".pre-commit-hooks.yaml")
    _git(hook_repo, "commit", "-m", "add hooks")
    return hook_repo


def test_cli_try_repo_runs_valid_local_manifest_hook(tmp_path, monkeypatch):
    hook_repo = _hook_repository(
        tmp_path,
        hooks=(
            "- id: block\n"
            "  name: Block\n"
            "  entry: manifest-block\n"
            "  language: fail\n"
            "  files: \\.txt$\n"
        ),
    )
    consumer_root = tmp_path / "consumer"
    consumer_root.mkdir()
    consumer, _ = _simple_repo(consumer_root, monkeypatch, "repos: []\n")

    result = _run_pre_commit_module(
        consumer, "try-repo", str(hook_repo), "--all-files", "--color", "never"
    )
    assert result.returncode != 0
    assert "block" in result.stdout.lower()
    assert "tracked.txt" in result.stdout


def test_cli_try_repo_selects_requested_manifest_hook(tmp_path, monkeypatch):
    hook_repo = _hook_repository(
        tmp_path,
        hooks=(
            "- id: first\n"
            "  name: First\n"
            "  entry: first-manifest-message\n"
            "  language: fail\n"
            "- id: second\n"
            "  name: Second\n"
            "  entry: second-manifest-message\n"
            "  language: fail\n"
        ),
    )
    consumer_root = tmp_path / "consumer"
    consumer_root.mkdir()
    consumer, _ = _simple_repo(consumer_root, monkeypatch, "repos: []\n")

    result = _run_pre_commit_module(
        consumer,
        "try-repo",
        str(hook_repo),
        "first",
        "--all-files",
        "--color",
        "never",
    )
    assert result.returncode != 0
    assert "first-manifest-message" in result.stdout
    assert "second-manifest-message" not in result.stdout
