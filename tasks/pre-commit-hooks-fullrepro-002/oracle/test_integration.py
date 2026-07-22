"""Integration oracle tests for pre-commit-hooks-fullrepro-002.

Each test exercises ≥2 public API boundaries or cross-view invariants.
"""
import yaml

import pytest

from pre_commit.main import main

from conftest import (
    assert_nonzero,
    create_hook_repo,
    git_cmd,
    init_git_repo,
    local_config_yaml,
    run_pre_commit,
    setup_repo,
    write_file,
)


# =====================================================================
# CVI-1  hook id in config → resolves and runs (local hook)
# =====================================================================

def test_cvi1_local_hook_resolves_and_runs(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
            "    files: \\.txt$\n"
        ),
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode == 0
    assert "verify" in result.stdout.lower()


# =====================================================================
# CVI-2  installed hook script dispatches hook-impl
# =====================================================================

def test_cvi2_installed_hook_dispatches_hook_impl(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    hook = repo / ".git" / "hooks" / "pre-commit"
    assert main(("install", "--config", str(cfg),
                 "--hook-type", "pre-commit")) == 0
    assert hook.exists()
    text = hook.read_text(encoding="UTF-8", errors="ignore")
    assert "hook-impl" in text
    assert "pre-commit" in text
    assert main(("uninstall", "--hook-type", "pre-commit")) == 0
    assert not hook.exists()


# =====================================================================
# CVI-3  default_install_hook_types controls installed scripts
# =====================================================================

def test_cvi3_default_install_hook_types_controls_scripts(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        "default_install_hook_types: [pre-commit, pre-push]\n"
        + local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    assert main(("install", "--config", str(cfg))) == 0
    assert (repo / ".git" / "hooks" / "pre-commit").exists()
    assert (repo / ".git" / "hooks" / "pre-push").exists()


# =====================================================================
# CVI-4  global exclude prevents file from reaching any hook
# =====================================================================

def test_cvi4_global_exclude_prevents_file_reaching_hook(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        "exclude: 'tracked\\.txt'\n"
        + local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0


# =====================================================================
# CVI-5  always_run=true runs even without matching files
# =====================================================================

def test_cvi5_always_run_executes_without_matching_files(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: always-check\n"
            "    name: Always Check\n"
            "    entry: always-msg\n"
            "    language: fail\n"
            "    files: \\.py$\n"
            "    always_run: true\n"
        ),
    )
    assert_nonzero(("run", "--all-files", "--config", str(cfg),
                    "--color", "never"))


# =====================================================================
# CVI-6  Store reuses cached entry for same tuple
# =====================================================================

def test_cvi6_store_reused_across_runs(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    store = tmp_path / "store"
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0
    assert store.is_dir()
    first = set(p.name for p in store.iterdir())
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0
    second = set(p.name for p in store.iterdir())
    assert first.issubset(second)


# =====================================================================
# CVI-7  validate-config agrees with run on validity
# =====================================================================

def test_cvi7_validate_and_run_agree_on_invalid_config(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    write_file(repo / "tracked.txt", "hello\n")
    git_cmd(repo, "add", "tracked.txt")
    bad_cfg = write_file(
        repo / ".pre-commit-config.yaml",
        "repos:\n- repo: local\n  hooks:\n  - id: check-echo\n",
    )
    monkeypatch.chdir(repo)
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "store"))
    assert main(("validate-config", str(bad_cfg))) != 0
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(bad_cfg), "--color", "never")
    assert result.returncode != 0


# =====================================================================
# CVI-8  migrate-config output passes validate-config
# =====================================================================

def test_cvi8_migrate_config_output_passes_validation(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    cfg = write_file(
        repo / ".pre-commit-config.yaml",
        "- repo: local\n"
        "  hooks:\n"
        "  - id: check-echo\n"
        "    name: Check Echo\n"
        "    entry: echo check\n"
        "    language: system\n"
        "    stages: [commit]\n",
    )
    assert main(("migrate-config", "--config", str(cfg))) == 0
    assert main(("validate-config", str(cfg))) == 0
    migrated = yaml.safe_load(cfg.read_text(encoding="UTF-8"))
    assert migrated["repos"][0]["hooks"][0]["stages"] == ["pre-commit"]


# =====================================================================
# CVI-9  hook failure (nonzero exit) reported in output with hook id
# =====================================================================

def test_cvi9_hook_failure_reported_with_hook_id(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "block-content" in result.stdout.lower()
    assert "block-msg" in result.stdout


# =====================================================================
# CVI-10  SKIP env var skips hook in direct run
# =====================================================================

def test_cvi10_skip_env_skips_hook(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    monkeypatch.setenv("SKIP", "block-content")
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0


# =====================================================================
# CVI-11  Store created on run, removable by clean
# =====================================================================

def test_cvi11_store_created_and_removable_by_clean(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    store = tmp_path / "store"
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0
    assert store.is_dir()
    assert any(store.iterdir())
    assert main(("clean",)) == 0
    assert not store.exists()


# =====================================================================
# Seam: config load → hook resolution → run (full local-hook pipeline)
# =====================================================================

def test_seam_validate_install_run_pipeline(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
            "    files: \\.txt$\n"
        ),
    )
    assert main(("validate-config", str(cfg))) == 0
    assert main(("install", "--config", str(cfg),
                 "--hook-type", "pre-commit")) == 0
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0
    assert (repo / ".git" / "hooks" / "pre-commit").exists()


# =====================================================================
# Seam: install → uninstall restores legacy hook
# =====================================================================

def test_seam_uninstall_restores_legacy_hook(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: \"python -c \\\"import sys; sys.exit(0)\\\"\"\n"
            "    language: system\n"
        ),
    )
    hook = repo / ".git" / "hooks" / "pre-commit"
    legacy = "#!/bin/sh\necho legacy-marker\n"
    write_file(hook, legacy)
    assert main(("install", "--config", str(cfg),
                 "--hook-type", "pre-commit")) == 0
    assert hook.read_text(encoding="UTF-8") != legacy
    assert main(("uninstall", "--hook-type", "pre-commit")) == 0
    assert hook.read_text(encoding="UTF-8") == legacy


# =====================================================================
# Seam: install --overwrite → uninstall removes completely
# =====================================================================

def test_seam_overwrite_uninstall_removes_completely(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    hook = repo / ".git" / "hooks" / "pre-commit"
    write_file(hook, "#!/bin/sh\necho custom-marker\n")
    assert main(("install", "--config", str(cfg),
                 "--hook-type", "pre-commit", "--overwrite")) == 0
    text = hook.read_text(encoding="UTF-8", errors="ignore")
    assert "hook-impl" in text
    assert "custom-marker" not in text
    assert main(("uninstall", "--hook-type", "pre-commit")) == 0
    assert not hook.exists()


# =====================================================================
# Seam: pass_filenames=false runs without filenames
# =====================================================================

def test_seam_pass_filenames_false_omits_filenames(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: no-files-hook\n"
            "    name: No Files Hook\n"
            "    entry: no-files-entry\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "    pass_filenames: false\n"
        ),
    )
    result = run_pre_commit(repo, "run", "--files", "tracked.txt",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "no-files-entry" in result.stdout
    assert "tracked.txt" not in result.stdout


# =====================================================================
# Seam: pygrep matches pattern in file content
# =====================================================================

def test_seam_pygrep_matches_pattern(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: grep-delta\n"
            "    name: Grep Delta\n"
            "    entry: Delta\n"
            "    language: pygrep\n"
            "    files: \\.txt$\n"
        ),
        contents="Delta\nGamma\n",
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "grep-delta" in result.stdout.lower()
    assert "tracked.txt" in result.stdout
    assert "Delta" in result.stdout


# =====================================================================
# Seam: pygrep --negate inverts match logic
# =====================================================================

def test_seam_pygrep_negate_inverts_match(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: grep-delta\n"
            "    name: Grep Delta\n"
            "    entry: Delta\n"
            "    language: pygrep\n"
            "    args: [--negate]\n"
            "    files: \\.txt$\n"
        ),
        contents="Delta\nGamma\n",
    )
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0


# =====================================================================
# Seam: pygrep --ignore-case matches regardless of case
# =====================================================================

def test_seam_pygrep_ignore_case(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: grep-delta\n"
            "    name: Grep Delta\n"
            "    entry: delta\n"
            "    language: pygrep\n"
            "    args: [--ignore-case]\n"
            "    files: \\.txt$\n"
        ),
        contents="DELTA\nGamma\n",
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "tracked.txt" in result.stdout


# =====================================================================
# Seam: pygrep --multiline matches across lines
# =====================================================================

def test_seam_pygrep_multiline(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: grep-multi\n"
            "    name: Grep Multi\n"
            "    entry: hello.*world\n"
            "    language: pygrep\n"
            "    args: [--multiline]\n"
            "    files: \\.txt$\n"
        ),
        contents="hello\nworld\n",
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "tracked.txt" in result.stdout


# =====================================================================
# Seam: fail language always fails
# =====================================================================

def test_seam_fail_language_always_fails(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "block-msg" in result.stdout
    assert "tracked.txt" in result.stdout


# =====================================================================
# Seam: fail_fast at config level stops after first failure
# =====================================================================

def test_seam_fail_fast_config_stops_after_first(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        "fail_fast: true\n"
        + local_config_yaml(
            "  - id: first-block\n"
            "    name: First Block\n"
            "    entry: first-block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "  - id: second-block\n"
            "    name: Second Block\n"
            "    entry: second-block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "first-block-msg" in result.stdout
    assert "second-block-msg" not in result.stdout


# =====================================================================
# Seam: hook-level fail_fast prevents later hooks
# =====================================================================

def test_seam_hook_level_fail_fast(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: first-block\n"
            "    name: First Block\n"
            "    entry: first-block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "    fail_fast: true\n"
            "  - id: second-block\n"
            "    name: Second Block\n"
            "    entry: second-block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "first-block-msg" in result.stdout
    assert "second-block-msg" not in result.stdout


# =====================================================================
# Seam: --all-files selects all tracked files
# =====================================================================

def test_seam_all_files_selects_all_tracked(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    write_file(repo / "other.txt", "other\n")
    git_cmd(repo, "add", "other.txt")
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "tracked.txt" in result.stdout
    assert "other.txt" in result.stdout


# =====================================================================
# Seam: --files limits input to explicit files
# =====================================================================

def test_seam_files_flag_limits_input(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    write_file(repo / "other.txt", "other\n")
    git_cmd(repo, "add", "other.txt")
    result = run_pre_commit(repo, "run", "--files", "tracked.txt",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "tracked.txt" in result.stdout
    assert "other.txt" not in result.stdout


# =====================================================================
# Seam: hook-level files/exclude further filters
# =====================================================================

def test_seam_hook_files_exclude_filters(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    write_file(repo / "tracked.txt", "hello\n")
    write_file(repo / "tracked.py", "print('hi')\n")
    git_cmd(repo, "add", "tracked.txt", "tracked.py")
    cfg = write_file(
        repo / ".pre-commit-config.yaml",
        "files: '\\.py$'\n"
        + local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
        ),
    )
    monkeypatch.chdir(repo)
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "store"))
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "tracked.py" in result.stdout
    assert "tracked.txt" not in result.stdout


# =====================================================================
# Seam: stage inheritance from default_stages
# =====================================================================

def test_seam_default_stages_inheritance(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        "default_stages: [manual]\n"
        + local_config_yaml(
            "  - id: block-content\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0
    assert_nonzero(("run", "--all-files", "--hook-stage", "manual",
                    "--config", str(cfg), "--color", "never"))


# =====================================================================
# Seam: manual stage selects only manual hooks
# =====================================================================

def test_seam_manual_stage_selects_manual_hooks(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: manual-block\n"
            "    name: Manual Block\n"
            "    entry: manual-block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "    stages: [manual]\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0
    assert_nonzero(("run", "--all-files", "--hook-stage", "manual",
                    "--config", str(cfg), "--color", "never"))


# =====================================================================
# Seam: multiple hooks, only selected id runs
# =====================================================================

def test_seam_single_hook_id_limits_execution(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: first-block\n"
            "    name: First Block\n"
            "    entry: first-block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "  - id: second-block\n"
            "    name: Second Block\n"
            "    entry: second-block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    result = run_pre_commit(repo, "run", "first-block", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0
    assert "first-block-msg" in result.stdout
    assert "second-block-msg" not in result.stdout


# =====================================================================
# Seam: sample-config output passes validate-config
# =====================================================================

def test_seam_sample_config_passes_validate(tmp_path, capsys):
    assert main(("sample-config",)) == 0
    sample = capsys.readouterr().out
    cfg = write_file(tmp_path / "sampled.yaml", sample)
    assert main(("validate-config", str(cfg))) == 0


# =====================================================================
# Seam: SKIP env accepts alias
# =====================================================================

def test_seam_skip_accepts_alias(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: block-content\n"
            "    alias: alias-block\n"
            "    name: Block Content\n"
            "    entry: block-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
        ),
    )
    monkeypatch.setenv("SKIP", "alias-block")
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0


# =====================================================================
# Seam: non-matching files skipped without always_run
# =====================================================================

def test_seam_nonmatching_files_skipped(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: py-only\n"
            "    name: Py Only\n"
            "    entry: should-not-run\n"
            "    language: fail\n"
            "    files: \\.py$\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0


# =====================================================================
# Seam: install writes each selected hook type
# =====================================================================

def test_seam_install_writes_each_hook_type(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    assert main(("install", "--config", str(cfg),
                 "--hook-type", "pre-commit",
                 "--hook-type", "pre-push")) == 0
    assert (repo / ".git" / "hooks" / "pre-commit").exists()
    assert (repo / ".git" / "hooks" / "pre-push").exists()


# =====================================================================
# Seam: installed hook script references config and hook type
# =====================================================================

def test_seam_installed_hook_references_type(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    assert main(("install", "--config", str(cfg),
                 "--hook-type", "pre-push")) == 0
    hook = repo / ".git" / "hooks" / "pre-push"
    text = hook.read_text(encoding="UTF-8", errors="ignore")
    assert "hook-impl" in text
    assert "pre-push" in text


# =====================================================================
# Seam: init-templatedir writes hook script
# =====================================================================

def test_seam_init_templatedir_writes_script(tmp_path, monkeypatch):
    repo, _ = setup_repo(tmp_path, monkeypatch, "repos: []\n")
    tpl = tmp_path / "template"
    assert main(("init-templatedir", str(tpl),
                 "--hook-type", "pre-push")) == 0
    hook = tpl / "hooks" / "pre-push"
    assert hook.exists()
    assert "hook-impl" in hook.read_text(encoding="UTF-8", errors="ignore")


# =====================================================================
# Seam: migrate-config wraps legacy repo list
# =====================================================================

def test_seam_migrate_wraps_legacy_list(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    cfg = write_file(
        repo / ".pre-commit-config.yaml",
        "- repo: local\n"
        "  hooks:\n"
        "  - id: check-echo\n"
        "    name: Check Echo\n"
        "    entry: echo check\n"
        "    language: system\n",
    )
    assert main(("migrate-config", "--config", str(cfg))) == 0
    migrated = yaml.safe_load(cfg.read_text(encoding="UTF-8"))
    assert isinstance(migrated, dict)
    assert migrated["repos"][0]["repo"] == "local"
    assert migrated["repos"][0]["hooks"][0]["id"] == "check-echo"


# =====================================================================
# Seam: migrate-config rewrites sha to rev
# =====================================================================

def test_seam_migrate_rewrites_sha_to_rev(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    cfg = write_file(
        repo / ".pre-commit-config.yaml",
        "repos:\n"
        "- repo: https://example.invalid/repo.git\n"
        "  sha: def456\n"
        "  hooks:\n"
        "  - id: check-markers\n",
    )
    assert main(("migrate-config", "--config", str(cfg))) == 0
    migrated = yaml.safe_load(cfg.read_text(encoding="UTF-8"))
    entry = migrated["repos"][0]
    assert entry["rev"] == "def456"
    assert "sha" not in entry


# =====================================================================
# Seam: migrate-config rewrites legacy stage names
# =====================================================================

def test_seam_migrate_rewrites_legacy_stages(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    cfg = write_file(
        repo / ".pre-commit-config.yaml",
        "default_stages: [commit, push, merge-commit]\n"
        "repos:\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: check-echo\n"
        "    name: Check Echo\n"
        "    entry: echo check\n"
        "    language: system\n"
        "    stages: [commit]\n",
    )
    assert main(("migrate-config", "--config", str(cfg))) == 0
    migrated = yaml.safe_load(cfg.read_text(encoding="UTF-8"))
    assert migrated["default_stages"] == [
        "pre-commit", "pre-push", "pre-merge-commit",
    ]
    assert migrated["repos"][0]["hooks"][0]["stages"] == ["pre-commit"]


# =====================================================================
# Seam: migrate-config idempotent for current config
# =====================================================================

def test_seam_migrate_idempotent_for_current_config(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    cfg = write_file(
        repo / ".pre-commit-config.yaml",
        "repos:\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: check-echo\n"
        "    name: Check Echo\n"
        "    entry: echo check\n"
        "    language: system\n"
        "    stages: [pre-commit]\n",
    )
    assert main(("migrate-config", "--config", str(cfg))) == 0
    migrated = yaml.safe_load(cfg.read_text(encoding="UTF-8"))
    assert migrated["repos"][0]["hooks"][0]["stages"] == ["pre-commit"]
    assert migrated["repos"][0]["hooks"][0]["id"] == "check-echo"


# =====================================================================
# Seam: meta identity hook resolves and passes
# =====================================================================

def test_seam_meta_identity_resolves_and_passes(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        "repos:\n- repo: meta\n  hooks:\n  - id: identity\n",
    )
    result = run_pre_commit(repo, "run", "identity", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode == 0
    assert "identity" in result.stdout.lower()


# =====================================================================
# Seam: mixed local and meta repos in single config
# =====================================================================

def test_seam_mixed_local_and_meta_repos(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        "repos:\n"
        "- repo: meta\n"
        "  hooks:\n"
        "  - id: identity\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: block-content\n"
        "    name: Block Content\n"
        "    entry: block-msg\n"
        "    language: fail\n"
        "    files: \\.never$\n",
    )
    result = run_pre_commit(repo, "run", "--all-files",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode == 0
    assert "identity" in result.stdout.lower()


# =====================================================================
# Seam: try-repo runs manifest hook
# =====================================================================

def test_seam_try_repo_runs_manifest_hook(tmp_path, monkeypatch):
    hook_repo = create_hook_repo(
        tmp_path,
        "- id: block-content\n"
        "  name: Block Content\n"
        "  entry: manifest-block-msg\n"
        "  language: fail\n"
        "  files: \\.txt$\n",
    )
    consumer_root = tmp_path / "consumer"
    consumer_root.mkdir()
    consumer, _ = setup_repo(consumer_root, monkeypatch, "repos: []\n")
    result = run_pre_commit(consumer, "try-repo", str(hook_repo),
                            "--all-files", "--color", "never")
    assert result.returncode != 0
    assert "block" in result.stdout.lower()
    assert "tracked.txt" in result.stdout


# =====================================================================
# Seam: try-repo selects requested hook
# =====================================================================

def test_seam_try_repo_selects_hook(tmp_path, monkeypatch):
    hook_repo = create_hook_repo(
        tmp_path,
        "- id: first-scan\n"
        "  name: First Scan\n"
        "  entry: first-manifest-msg\n"
        "  language: fail\n"
        "- id: second-scan\n"
        "  name: Second Scan\n"
        "  entry: second-manifest-msg\n"
        "  language: fail\n",
    )
    consumer_root = tmp_path / "consumer"
    consumer_root.mkdir()
    consumer, _ = setup_repo(consumer_root, monkeypatch, "repos: []\n")
    result = run_pre_commit(consumer, "try-repo", str(hook_repo), "first-scan",
                            "--all-files", "--color", "never")
    assert result.returncode != 0
    assert "first-manifest-msg" in result.stdout
    assert "second-manifest-msg" not in result.stdout


# =====================================================================
# Seam: --from-ref and --to-ref must be supplied together
# =====================================================================

def test_seam_from_ref_and_to_ref_required_together(tmp_path, monkeypatch):
    repo, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: verify-headers\n"
            "    name: Verify Headers\n"
            "    entry: no-match-pattern\n"
            "    language: pygrep\n"
        ),
    )
    result = run_pre_commit(repo, "run", "--from-ref", "HEAD",
                            "--config", str(cfg), "--color", "never")
    assert result.returncode != 0


# =====================================================================
# Seam: default stage ignores manual-only hooks
# =====================================================================

def test_seam_default_stage_ignores_manual_only(tmp_path, monkeypatch):
    _, cfg = setup_repo(
        tmp_path, monkeypatch,
        local_config_yaml(
            "  - id: manual-only\n"
            "    name: Manual Only\n"
            "    entry: manual-only-msg\n"
            "    language: fail\n"
            "    files: \\.txt$\n"
            "    stages: [manual]\n"
        ),
    )
    assert main(("run", "--all-files", "--config", str(cfg),
                 "--color", "never")) == 0
