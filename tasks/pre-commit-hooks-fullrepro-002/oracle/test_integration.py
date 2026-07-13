# Spec2Repo oracle - integration tests for pre-commit-hooks-fullrepro-002
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


def test_load_manifest_applies_hook_defaults(tmp_path):
    manifest = _write(
        tmp_path / ".pre-commit-hooks.yaml",
        "- id: h\n  name: Hook\n  entry: echo hi\n  language: system\n",
    )
    (hook,) = load_manifest(str(manifest))
    assert hook["id"] == "h"
    assert hook["language"] == "unsupported"
    assert hook["alias"] == ""
    assert hook["files"] == ""
    assert hook["exclude"] == "^$"
    assert hook["types"] == ["file"]
    assert hook["types_or"] == []
    assert hook["exclude_types"] == []
    assert hook["additional_dependencies"] == []
    assert hook["args"] == []
    assert hook["always_run"] is False
    assert hook["fail_fast"] is False
    assert hook["pass_filenames"] is True
    assert hook["require_serial"] is False
    assert hook["stages"] == []
    assert hook["verbose"] is False


def test_load_manifest_normalizes_script_language(tmp_path):
    manifest = _write(
        tmp_path / ".pre-commit-hooks.yaml",
        "- id: h\n  name: Hook\n  entry: script.sh\n  language: script\n",
    )
    (hook,) = load_manifest(str(manifest))
    assert hook["language"] == "unsupported_script"


def test_load_config_applies_top_level_defaults(tmp_path):
    config = _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    loaded = load_config(str(config))
    assert loaded["repos"] == []
    assert loaded["default_install_hook_types"] == ["pre-commit"]
    assert loaded["default_stages"] == list(STAGES)
    assert loaded["files"] == ""
    assert loaded["exclude"] == "^$"
    assert loaded["fail_fast"] is False
    assert loaded["minimum_pre_commit_version"] == "0"


def test_load_config_accepts_ci_mapping_without_changing_local_hooks(tmp_path):
    config = _write(
        tmp_path / ".pre-commit-config.yaml",
        "ci:\n  skip: [h]\nrepos:\n- repo: local\n  hooks:\n"
        "  - id: h\n    name: Hook\n    entry: echo hi\n    language: system\n",
    )
    loaded = load_config(str(config))
    assert loaded["ci"] == {"skip": ["h"]}
    assert loaded["repos"][0]["hooks"][0]["id"] == "h"


def test_load_config_normalizes_local_hook_defaults(tmp_path):
    config = _write(
        tmp_path / ".pre-commit-config.yaml",
        _local_config(
            "  - id: h\n"
            "    name: Hook\n"
            "    entry: echo hi\n"
            "    language: system\n"
        ),
    )
    hook = load_config(str(config))["repos"][0]["hooks"][0]
    assert hook["language"] == "unsupported"
    assert hook["language_version"] == "default"
    assert hook["minimum_pre_commit_version"] == "0"
    assert hook["log_file"] == ""
    assert hook["description"] == ""


def test_load_config_preserves_explicit_hook_overrides(tmp_path):
    config = _write(
        tmp_path / ".pre-commit-config.yaml",
        _local_config(
            "  - id: h\n"
            "    alias: alias-h\n"
            "    name: Hook\n"
            "    entry: echo hi\n"
            "    language: system\n"
            "    args: [one, two]\n"
            "    always_run: true\n"
            "    fail_fast: true\n"
            "    pass_filenames: false\n"
            "    require_serial: true\n"
            "    stages: [manual]\n"
            "    verbose: true\n"
        ),
    )
    hook = load_config(str(config))["repos"][0]["hooks"][0]
    assert hook["alias"] == "alias-h"
    assert hook["args"] == ["one", "two"]
    assert hook["always_run"] is True
    assert hook["fail_fast"] is True
    assert hook["pass_filenames"] is False
    assert hook["require_serial"] is True
    assert hook["stages"] == ["manual"]
    assert hook["verbose"] is True


def test_invalid_config_without_repos_raises_invalid_config_error(tmp_path):
    config = _write(tmp_path / ".pre-commit-config.yaml", "files: ''\n")
    with pytest.raises(InvalidConfigError):
        load_config(str(config))


def test_invalid_config_requires_rev_for_normal_repositories(tmp_path):
    config = _write(
        tmp_path / ".pre-commit-config.yaml",
        "repos:\n- repo: https://example.invalid/repo.git\n  hooks: []\n",
    )
    with pytest.raises(InvalidConfigError):
        load_config(str(config))


def test_invalid_config_rejects_rev_for_local_repositories(tmp_path):
    config = _write(
        tmp_path / ".pre-commit-config.yaml",
        "repos:\n- repo: local\n  rev: v1\n  hooks: []\n",
    )
    with pytest.raises(InvalidConfigError):
        load_config(str(config))


def test_invalid_manifest_missing_required_keys_raises_invalid_manifest_error(tmp_path):
    manifest = _write(tmp_path / ".pre-commit-hooks.yaml", "- id: h\n  name: Hook\n")
    with pytest.raises(InvalidManifestError):
        load_manifest(str(manifest))


def test_type_tag_validation_accepts_file_and_rejects_unknown_tags():
    assert check_type_tag("file") is None
    with pytest.raises(Exception):
        check_type_tag("not-a-real-type")


def test_minimum_version_validation_accepts_zero_and_rejects_future_versions():
    assert check_min_version("0") is None
    with pytest.raises(Exception):
        check_min_version("999999.0.0")


def test_format_color_can_be_disabled_or_enabled():
    assert format_color("hello", "\x1b[31m", False) == "hello"
    colored = format_color("hello", "\x1b[31m", True)
    assert colored.startswith("\x1b[31m")
    assert colored.endswith("\x1b[m")
    assert "hello" in colored


def test_prefix_joins_paths_checks_existence_and_lists_suffixes(tmp_path):
    prefix = Prefix(str(tmp_path))
    _write(tmp_path / "one.txt", "1")
    _write(tmp_path / "two.py", "2")
    assert prefix.path("nested", "file.txt") == os.path.normpath(
        str(tmp_path / "nested" / "file.txt")
    )
    assert prefix.exists("one.txt") is True
    assert prefix.exists("missing.txt") is False
    assert prefix.star(".txt") == ("one.txt",)


def test_store_uses_pre_commit_home_and_creates_cache_files(tmp_path, monkeypatch):
    home = tmp_path / "cache"
    monkeypatch.setenv("PRE_COMMIT_HOME", str(home))
    store = Store()
    assert store.directory == str(home)
    assert home.exists()
    assert (home / "db.db").exists()


def test_store_make_local_reuses_matching_dependency_sets(tmp_path):
    store = Store(str(tmp_path / "store"))
    first = store.make_local(("dep-one",))
    second = store.make_local(("dep-one",))
    other = store.make_local(("dep-two",))
    assert first == second
    assert first != other
    assert os.path.isdir(first)
    assert os.path.isdir(other)


def test_normalize_cmd_uses_script_shebang(tmp_path):
    script = _write(tmp_path / "tool.py", "#!/usr/bin/env python\nprint('ok')\n")
    normalized = normalize_cmd((str(script), "arg"))
    assert os.path.basename(normalized[-2]) == "tool.py"
    assert normalized[-1] == "arg"
    assert "python" in os.path.basename(normalized[0]).lower()


def test_xargs_combines_successful_command_output():
    code, stdout = xargs(
        (sys.executable, "-c", "import sys; print('|'.join(sys.argv[1:]))"),
        ["a", "b"],
        target_concurrency=1,
        _max_length=10000,
    )
    assert code == 0
    assert stdout.strip() == b"a|b"


def test_xargs_returns_nonzero_when_command_fails():
    code, stdout = xargs(
        (sys.executable, "-c", "import sys; sys.exit(3)"),
        ["a"],
        target_concurrency=1,
        _max_length=10000,
    )
    assert code == 3
    assert stdout == b""


def test_all_hooks_resolves_local_hook_public_attributes(tmp_path, monkeypatch):
    config = _write(
        tmp_path / ".pre-commit-config.yaml",
        _local_config(
            "  - id: h\n"
            "    alias: alias-h\n"
            "    name: Hook\n"
            "    entry: echo hi\n"
            "    language: system\n"
            "    args: [one]\n"
            "    stages: [manual]\n"
        ),
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "home"))
    (hook,) = all_hooks(load_config(str(config)), Store(str(tmp_path / "store")))
    assert hook.id == "h"
    assert hook.alias == "alias-h"
    assert hook.name == "Hook"
    assert hook.entry == "echo hi"
    assert hook.language == "unsupported"
    assert hook.args == ["one"]
    assert hook.stages == ["manual"]


def test_all_hooks_resolves_meta_identity_hook(tmp_path, monkeypatch):
    config = _write(
        tmp_path / ".pre-commit-config.yaml",
        "repos:\n- repo: meta\n  hooks:\n  - id: identity\n",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "home"))
    (hook,) = all_hooks(load_config(str(config)), Store(str(tmp_path / "store")))
    assert hook.id == "identity"
    assert hook.name == "identity"
    assert set(hook.stages) == set(STAGES)


def test_cli_clean_removes_the_configured_store(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("PRE_COMMIT_HOME", str(home))
    Store()
    _write(home / "marker.txt", "x")
    assert home.exists()
    assert main(("clean",)) == 0
    assert not home.exists()


def test_cli_install_and_uninstall_manage_selected_hook_script(tmp_path, monkeypatch):
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
    assert main(("install", "--config", str(cfg), "--hook-type", "pre-commit", "--color", "never")) == 0
    hook_text = hook_path.read_text(encoding="UTF-8", errors="ignore")
    assert hook_path.exists()
    assert "hook-impl" in hook_text
    assert "pre-commit" in hook_text
    assert main(("uninstall", "--hook-type", "pre-commit", "--color", "never")) == 0
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
    assert result.returncode == 1
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
    assert result.returncode == 1
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
    assert main(("run", "--all-files", "--config", str(cfg), "--color", "never")) == 1


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
    assert result.returncode == 1
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
    assert (
        main(
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
        == 1
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
    assert result.returncode == 1
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
    migrated = config.read_text(encoding="UTF-8")
    assert migrated.startswith("repos:\n- repo: local\n")
    assert "hooks:" in migrated


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
    migrated = config.read_text(encoding="UTF-8")
    assert "  rev: abc123\n" in migrated
    assert "  sha: abc123\n" not in migrated


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
    migrated = config.read_text(encoding="UTF-8")
    assert "pre-commit" in migrated
    assert "pre-push" in migrated
    assert "pre-merge-commit" in migrated
    assert "[commit" not in migrated


def test_cli_migrate_config_rewrites_python_venv_language(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    monkeypatch.chdir(repo)
    config = _write(
        repo / ".pre-commit-config.yaml",
        "repos:\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: h\n"
        "    name: Hook\n"
        "    entry: python -V\n"
        "    language: python_venv\n",
    )
    assert main(("migrate-config", "--config", str(config))) == 0
    migrated = config.read_text(encoding="UTF-8")
    assert "language: python\n" in migrated
    assert "python_venv" not in migrated


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
    assert result.returncode == 1
    assert "first-message" in result.stdout
    assert "second-message" not in result.stdout


def test_cli_run_fail_fast_stops_after_first_failing_hook(tmp_path, monkeypatch):
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
    result = _run_pre_commit_module(repo, "run", "--all-files", "--fail-fast", "--config", str(cfg), "--color", "never")
    assert result.returncode == 1
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
