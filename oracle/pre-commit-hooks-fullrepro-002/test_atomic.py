# Spec2Repo oracle - atomic tests for pre-commit-hooks-fullrepro-002
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
    document = yaml.safe_load(capsys.readouterr().out)
    assert isinstance(document, dict)
    assert isinstance(document["repos"], list)
    assert document["repos"]
    assert isinstance(document["repos"][0]["hooks"], list)


def test_cli_validate_config_accepts_multiple_valid_files(tmp_path):
    first = _write(tmp_path / "first.yaml", "repos: []\n")
    second = _write(tmp_path / "second.yaml", "repos: []\n")
    assert main(("validate-config", str(first), str(second))) == 0


def test_cli_validate_config_fails_when_any_file_is_invalid(tmp_path):
    good = _write(tmp_path / "good.yaml", "repos: []\n")
    bad = _write(tmp_path / "bad.yaml", "minimum_pre_commit_version: '0'\n")
    _assert_nonzero_status(("validate-config", str(good), str(bad)))


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
    _assert_nonzero_status(("validate-manifest", str(good), str(bad)))


def _assert_nonzero_status(argv):
    status = main(argv)
    assert isinstance(status, int)
    assert status != 0


def _validation_local_config(*, repo_extra="", hook_extra=""):
    return (
        "repos:\n"
        "- repo: local\n"
        f"{repo_extra}"
        "  hooks:\n"
        "  - id: h\n"
        "    name: Hook\n"
        "    entry: echo hi\n"
        "    language: system\n"
        f"{hook_extra}"
    )


def test_cli_validate_config_uses_default_filename(tmp_path, monkeypatch):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    monkeypatch.chdir(tmp_path)
    assert main(("validate-config",)) == 0


def test_cli_validate_manifest_uses_default_filename(tmp_path, monkeypatch):
    _write(
        tmp_path / ".pre-commit-hooks.yaml",
        "- id: h\n  name: Hook\n  entry: echo hi\n  language: system\n",
    )
    monkeypatch.chdir(tmp_path)
    assert main(("validate-manifest",)) == 0


def test_cli_validate_config_rejects_sequence_at_document_root(tmp_path):
    config = _write(tmp_path / "config.yaml", "[]\n")
    _assert_nonzero_status(("validate-config", str(config)))


def test_cli_validate_config_rejects_non_list_repos(tmp_path):
    config = _write(tmp_path / "config.yaml", "repos: {}\n")
    _assert_nonzero_status(("validate-config", str(config)))


def test_cli_validate_manifest_rejects_mapping_at_document_root(tmp_path):
    manifest = _write(
        tmp_path / "manifest.yaml",
        "id: h\nname: Hook\nentry: echo hi\nlanguage: system\n",
    )
    _assert_nonzero_status(("validate-manifest", str(manifest)))


def test_cli_validate_config_rejects_normal_repository_without_rev(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos:\n"
        "- repo: https://example.invalid/hooks\n"
        "  hooks:\n"
        "  - id: h\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_cli_validate_config_accepts_local_repository_without_rev(tmp_path):
    config = _write(tmp_path / "config.yaml", _validation_local_config())
    assert main(("validate-config", str(config))) == 0


def test_cli_validate_config_accepts_supported_meta_hook_without_rev(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos:\n- repo: meta\n  hooks:\n  - id: identity\n",
    )
    assert main(("validate-config", str(config))) == 0


def test_cli_validate_config_rejects_unknown_meta_hook(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos:\n- repo: meta\n  hooks:\n  - id: not-a-meta-hook\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_cli_validate_config_rejects_meta_entry_override(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos:\n"
        "- repo: meta\n"
        "  hooks:\n"
        "  - id: identity\n"
        "    entry: echo changed\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_cli_validate_config_rejects_unknown_type_tag(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        _validation_local_config(hook_extra="    types: [not-a-real-type]\n"),
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_cli_validate_config_rejects_too_new_minimum_version(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\nminimum_pre_commit_version: '999.0.0'\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_cli_validate_config_accepts_manual_stage(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        _validation_local_config(hook_extra="    stages: [manual]\n"),
    )
    assert main(("validate-config", str(config))) == 0


def test_cli_validate_config_accepts_legacy_commit_stage(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        _validation_local_config(hook_extra="    stages: [commit]\n"),
    )
    assert main(("validate-config", str(config))) == 0


def test_cli_validate_config_accepts_ci_mapping(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\nci:\n  skip: [h]\n",
    )
    assert main(("validate-config", str(config))) == 0


def test_cli_clean_removes_configured_store_directory(tmp_path, monkeypatch):
    store = tmp_path / "pre-commit-home"
    store.mkdir()
    _write(store / "sentinel", "cached\n")
    monkeypatch.setenv("PRE_COMMIT_HOME", str(store))
    monkeypatch.chdir(tmp_path)
    assert main(("clean",)) == 0
    assert not store.exists()


def _supplement_local_config(*, repo_extra="", hook_extra=""):
    return (
        "repos:\n"
        "- repo: local\n"
        f"{repo_extra}"
        "  hooks:\n"
        "  - id: h\n"
        "    name: Hook\n"
        "    entry: echo hi\n"
        "    language: system\n"
        f"{hook_extra}"
    )


def _manifest(*, extra=""):
    return (
        "- id: h\n"
        "  name: Hook\n"
        "  entry: echo hi\n"
        "  language: system\n"
        f"{extra}"
    )


def test_validate_config_accepts_normal_repository_with_rev(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos:\n"
        "- repo: https://example.invalid/hooks\n"
        "  rev: v1.0.0\n"
        "  hooks:\n"
        "  - id: h\n",
    )
    assert main(("validate-config", str(config))) == 0


def test_validate_config_rejects_local_repository_with_rev(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        _supplement_local_config(repo_extra="  rev: v1.0.0\n"),
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_rejects_meta_repository_with_rev(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos:\n"
        "- repo: meta\n"
        "  rev: v1.0.0\n"
        "  hooks:\n"
        "  - id: identity\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_accepts_supported_default_install_hook_types(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\n"
        "default_install_hook_types: [pre-commit, pre-push, commit-msg]\n",
    )
    assert main(("validate-config", str(config))) == 0


def test_validate_config_rejects_manual_as_default_install_hook_type(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\ndefault_install_hook_types: [manual]\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_accepts_supported_default_stages(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\ndefault_stages: [manual, pre-push, commit-msg]\n",
    )
    assert main(("validate-config", str(config))) == 0


def test_validate_config_rejects_unknown_default_stage(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\ndefault_stages: [not-a-stage]\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_rejects_invalid_global_files_regex(tmp_path):
    config = _write(tmp_path / "config.yaml", "repos: []\nfiles: '[unterminated'\n")
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_rejects_invalid_global_exclude_regex(tmp_path):
    config = _write(tmp_path / "config.yaml", "repos: []\nexclude: '(unterminated'\n")
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_rejects_invalid_hook_files_regex(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        _supplement_local_config(hook_extra="    files: '[unterminated'\n"),
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_manifest_rejects_invalid_hook_exclude_regex(tmp_path):
    manifest = _write(
        tmp_path / "manifest.yaml",
        _manifest(extra="  exclude: '(unterminated'\n"),
    )
    _assert_nonzero_status(("validate-manifest", str(manifest)))


def test_validate_config_accepts_fail_language(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        _supplement_local_config().replace("language: system", "language: fail"),
    )
    assert main(("validate-config", str(config))) == 0


def test_validate_config_rejects_hooks_mapping_instead_of_list(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos:\n- repo: local\n  hooks: {}\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_manifest_rejects_unknown_type_tag(tmp_path):
    manifest = _write(
        tmp_path / "manifest.yaml",
        _manifest(extra="  types: [not-a-real-type]\n"),
    )
    _assert_nonzero_status(("validate-manifest", str(manifest)))


def test_validate_config_rejects_non_mapping_default_language_version(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\ndefault_language_version: python3\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_rejects_non_list_default_install_hook_types(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\ndefault_install_hook_types: pre-commit\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))


def test_validate_config_rejects_non_list_default_stages(tmp_path):
    config = _write(
        tmp_path / "config.yaml",
        "repos: []\ndefault_stages: manual\n",
    )
    _assert_nonzero_status(("validate-config", str(config)))
