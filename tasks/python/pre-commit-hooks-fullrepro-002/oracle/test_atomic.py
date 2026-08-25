"""Atomic oracle tests for pre-commit-hooks-fullrepro-002.

Each test exercises ONE public API entry point and ONE behaviour.
"""
import pytest
import yaml

from pre_commit.main import main

from conftest import (
    assert_nonzero,
    local_config_yaml,
    manifest_yaml,
    run_pre_commit,
    validation_local_yaml,
    write_file,
)


# ---------------------------------------------------------------------------
# CLI: --version
# ---------------------------------------------------------------------------

def test_version_output_starts_with_pre_commit(tmp_path, monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "store"))
    proc = run_pre_commit(tmp_path, "--version")
    assert proc.returncode == 0
    assert proc.stdout.strip().startswith("pre-commit ")


# ---------------------------------------------------------------------------
# CLI: help
# ---------------------------------------------------------------------------

def test_help_prints_usage_and_exits_zero(capfd):
    with pytest.raises(SystemExit) as exc:
        main(("help",))
    assert exc.value.code == 0
    assert "usage: pre-commit" in capfd.readouterr().out


def test_help_run_prints_run_specific_usage(capfd):
    with pytest.raises(SystemExit) as exc:
        main(("help", "run"))
    assert exc.value.code == 0
    assert "usage: pre-commit run" in capfd.readouterr().out


# ---------------------------------------------------------------------------
# CLI: sample-config
# ---------------------------------------------------------------------------

def test_sample_config_returns_valid_yaml_with_repos(capsys):
    assert main(("sample-config",)) == 0
    doc = yaml.safe_load(capsys.readouterr().out)
    assert isinstance(doc, dict)
    assert isinstance(doc["repos"], list)
    assert len(doc["repos"]) >= 1
    assert isinstance(doc["repos"][0]["hooks"], list)


# ---------------------------------------------------------------------------
# CLI: validate-config — acceptance
# ---------------------------------------------------------------------------

def test_validate_config_accepts_valid_empty_repos(tmp_path):
    cfg = write_file(tmp_path / "cfg.yaml", "repos: []\n")
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_multiple_valid_files(tmp_path):
    a = write_file(tmp_path / "a.yaml", "repos: []\n")
    b = write_file(tmp_path / "b.yaml", "repos: []\n")
    assert main(("validate-config", str(a), str(b))) == 0


def test_validate_config_uses_default_filename(tmp_path, monkeypatch):
    write_file(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    monkeypatch.chdir(tmp_path)
    assert main(("validate-config",)) == 0


def test_validate_config_accepts_normal_repo_with_rev(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos:\n"
        "- repo: https://example.invalid/hooks\n"
        "  rev: v2.1.0\n"
        "  hooks:\n"
        "  - id: check-markers\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_local_repo_without_rev(tmp_path):
    cfg = write_file(tmp_path / "cfg.yaml", validation_local_yaml())
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_meta_repo_identity(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos:\n- repo: meta\n  hooks:\n  - id: identity\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_satisfied_minimum_version(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\nminimum_pre_commit_version: '0.1.0'\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_default_language_version(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\ndefault_language_version:\n  python: python3\n  node: system\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_global_filters_and_fail_fast(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\nfail_fast: true\nfiles: '\\.py$'\nexclude: '^vendor/'\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_ci_mapping(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\nci:\n  skip: [check-markers]\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_default_stages_including_manual(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\ndefault_stages: [manual, pre-push, commit-msg]\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_supported_default_install_hook_types(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\ndefault_install_hook_types: [pre-commit, pre-push, commit-msg]\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_fail_language(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        validation_local_yaml().replace("language: system", "language: fail"),
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_legacy_and_current_stages_together(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        validation_local_yaml(
            hook_extra="    stages: [commit, merge-commit, push, pre-push, manual]\n"
        ),
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_full_hook_override_set(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        validation_local_yaml(
            hook_extra=(
                "    alias: aliased-echo\n"
                "    files: '\\.py$'\n"
                "    exclude: '^build/'\n"
                "    types: [python]\n"
                "    types_or: [python, pyi]\n"
                "    exclude_types: [markdown]\n"
                "    args: ['--strict']\n"
                "    stages: [pre-commit, manual]\n"
                "    always_run: true\n"
                "    pass_filenames: false\n"
                "    verbose: true\n"
                "    description: hook override coverage\n"
            )
        ),
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_local_and_meta_repos_together(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        validation_local_yaml()
        + "- repo: meta\n"
        "  hooks:\n"
        "  - id: identity\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_multiple_local_repos_and_hooks(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos:\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: first-scan\n"
        "    name: First Scan\n"
        "    entry: echo first\n"
        "    language: system\n"
        "  - id: second-scan\n"
        "    name: Second Scan\n"
        "    entry: echo second\n"
        "    language: system\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: third-scan\n"
        "    name: Third Scan\n"
        "    entry: echo third\n"
        "    language: fail\n",
    )
    assert main(("validate-config", str(cfg))) == 0


def test_validate_config_accepts_hook_execution_control_fields(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        validation_local_yaml(
            hook_extra=(
                "    language_version: default\n"
                "    require_serial: true\n"
                "    fail_fast: true\n"
                "    log_file: hook.log\n"
            )
        ),
    )
    assert main(("validate-config", str(cfg))) == 0


# ---------------------------------------------------------------------------
# CLI: validate-config — rejection
# ---------------------------------------------------------------------------

def test_validate_config_rejects_incomplete_local_hook(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        local_config_yaml("  - id: check-markers\n"),
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_fails_when_any_file_invalid(tmp_path):
    good = write_file(tmp_path / "good.yaml", "repos: []\n")
    bad = write_file(tmp_path / "bad.yaml", "minimum_pre_commit_version: '0'\n")
    assert_nonzero(("validate-config", str(good), str(bad)))


def test_validate_config_rejects_sequence_at_root(tmp_path):
    cfg = write_file(tmp_path / "cfg.yaml", "[]\n")
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_non_list_repos(tmp_path):
    cfg = write_file(tmp_path / "cfg.yaml", "repos: {}\n")
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_normal_repo_without_rev(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos:\n"
        "- repo: https://example.invalid/hooks\n"
        "  hooks:\n"
        "  - id: check-markers\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_local_repo_with_rev(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        validation_local_yaml(repo_extra="  rev: v2.1.0\n"),
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_unknown_meta_hook(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos:\n- repo: meta\n  hooks:\n  - id: nonexistent-meta\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_meta_entry_override(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos:\n- repo: meta\n  hooks:\n"
        "  - id: identity\n    entry: echo custom\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_too_new_minimum_version(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\nminimum_pre_commit_version: '999.0.0'\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_manual_as_default_install_hook_type(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\ndefault_install_hook_types: [manual]\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_unknown_default_stage(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\ndefault_stages: [not-a-stage]\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_invalid_files_regex(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos: []\nfiles: '[unterminated'\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


def test_validate_config_rejects_hooks_mapping_instead_of_list(tmp_path):
    cfg = write_file(
        tmp_path / "cfg.yaml",
        "repos:\n- repo: local\n  hooks: {}\n",
    )
    assert_nonzero(("validate-config", str(cfg)))


# ---------------------------------------------------------------------------
# CLI: validate-manifest — acceptance
# ---------------------------------------------------------------------------

def test_validate_manifest_accepts_valid_manifest(tmp_path):
    m = write_file(tmp_path / "hooks.yaml", manifest_yaml())
    assert main(("validate-manifest", str(m))) == 0


def test_validate_manifest_accepts_multiple_valid_files(tmp_path):
    a = write_file(tmp_path / "a.yaml", manifest_yaml())
    b = write_file(tmp_path / "b.yaml", manifest_yaml())
    assert main(("validate-manifest", str(a), str(b))) == 0


def test_validate_manifest_uses_default_filename(tmp_path, monkeypatch):
    write_file(tmp_path / ".pre-commit-hooks.yaml", manifest_yaml())
    monkeypatch.chdir(tmp_path)
    assert main(("validate-manifest",)) == 0


def test_validate_manifest_accepts_optional_fields(tmp_path):
    m = write_file(
        tmp_path / "hooks.yaml",
        manifest_yaml(
            extra=(
                "  alias: aliased-scan\n"
                "  files: '\\.py$'\n"
                "  exclude: '^build/'\n"
                "  types: [python]\n"
                "  args: ['--strict']\n"
                "  always_run: false\n"
                "  pass_filenames: true\n"
                "  description: optional fields coverage\n"
                "  minimum_pre_commit_version: '0'\n"
            )
        ),
    )
    assert main(("validate-manifest", str(m))) == 0


def test_validate_manifest_accepts_multiple_hooks_in_one_file(tmp_path):
    m = write_file(
        tmp_path / "hooks.yaml",
        "- id: first-scan\n"
        "  name: First Scan\n"
        "  entry: echo first\n"
        "  language: system\n"
        "- id: second-scan\n"
        "  name: Second Scan\n"
        "  entry: echo second\n"
        "  language: system\n",
    )
    assert main(("validate-manifest", str(m))) == 0


def test_validate_manifest_accepts_type_and_serial_fields(tmp_path):
    m = write_file(
        tmp_path / "hooks.yaml",
        manifest_yaml(
            extra=(
                "  types_or: [python, pyi]\n"
                "  exclude_types: [markdown]\n"
                "  require_serial: true\n"
                "  fail_fast: true\n"
            )
        ),
    )
    assert main(("validate-manifest", str(m))) == 0


def test_validate_manifest_accepts_stage_and_logging_fields(tmp_path):
    m = write_file(
        tmp_path / "hooks.yaml",
        manifest_yaml(
            extra=(
                "  stages: [pre-commit, manual]\n"
                "  log_file: out.log\n"
                "  language_version: default\n"
            )
        ),
    )
    assert main(("validate-manifest", str(m))) == 0


def test_validate_manifest_accepts_additional_deps_and_alias(tmp_path):
    m = write_file(
        tmp_path / "hooks.yaml",
        manifest_yaml(
            extra=(
                "  alias: marker-alias\n"
                "  additional_dependencies: ['example==1.0.0']\n"
            )
        ),
    )
    assert main(("validate-manifest", str(m))) == 0


# ---------------------------------------------------------------------------
# CLI: validate-manifest — rejection
# ---------------------------------------------------------------------------

def test_validate_manifest_rejects_incomplete_manifest(tmp_path):
    m = write_file(tmp_path / "hooks.yaml", "- id: scan-markers\n")
    assert_nonzero(("validate-manifest", str(m)))


def test_validate_manifest_fails_when_any_file_invalid(tmp_path):
    good = write_file(tmp_path / "good.yaml", manifest_yaml())
    bad = write_file(tmp_path / "bad.yaml", "- id: scan-markers\n")
    assert_nonzero(("validate-manifest", str(good), str(bad)))


def test_validate_manifest_rejects_mapping_at_root(tmp_path):
    m = write_file(
        tmp_path / "hooks.yaml",
        "id: scan-markers\nname: Scan\nentry: echo\nlanguage: system\n",
    )
    assert_nonzero(("validate-manifest", str(m)))


def test_validate_manifest_rejects_unknown_type_tag(tmp_path):
    m = write_file(
        tmp_path / "hooks.yaml",
        manifest_yaml(extra="  types: [not-a-real-type]\n"),
    )
    assert_nonzero(("validate-manifest", str(m)))


# ---------------------------------------------------------------------------
# CLI: clean
# ---------------------------------------------------------------------------

def test_clean_removes_store_directory(tmp_path, monkeypatch):
    store = tmp_path / "store-dir"
    store.mkdir()
    write_file(store / "sentinel", "cached\n")
    monkeypatch.setenv("PRE_COMMIT_HOME", str(store))
    monkeypatch.chdir(tmp_path)
    assert main(("clean",)) == 0
    assert not store.exists()


def test_clean_returns_zero_when_store_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "absent-store"))
    monkeypatch.chdir(tmp_path)
    assert main(("clean",)) == 0
    assert not (tmp_path / "absent-store").exists()


# ---------------------------------------------------------------------------
# CLI: gc
# ---------------------------------------------------------------------------

def test_gc_returns_zero_and_preserves_store(tmp_path, monkeypatch):
    store = tmp_path / "store-gc"
    monkeypatch.setenv("PRE_COMMIT_HOME", str(store))
    monkeypatch.chdir(tmp_path)
    assert main(("gc",)) == 0
    assert store.is_dir()


# ---------------------------------------------------------------------------
# Python API: load_config / load_manifest
# ---------------------------------------------------------------------------

def _try_import_clientlib():
    try:
        from pre_commit import clientlib
        return clientlib
    except ImportError:
        return None


def test_load_config_returns_object_with_repos(tmp_path):
    cl = _try_import_clientlib()
    load_config = getattr(cl, "load_config", None) if cl else None
    if load_config is None:
        pytest.skip("load_config not importable from pre_commit.clientlib")
    cfg_file = write_file(tmp_path / "cfg.yaml", validation_local_yaml())
    result = load_config(str(cfg_file))
    assert "repos" in result
    assert isinstance(result["repos"], list)
    assert result["repos"][0]["repo"] == "local"


def test_load_config_raises_invalid_config_error(tmp_path):
    cl = _try_import_clientlib()
    load_config = getattr(cl, "load_config", None) if cl else None
    InvalidConfigError = getattr(cl, "InvalidConfigError", None) if cl else None
    if load_config is None or InvalidConfigError is None:
        pytest.skip("load_config / InvalidConfigError not importable")
    bad = write_file(tmp_path / "bad.yaml", "repos: {}\n")
    with pytest.raises(InvalidConfigError):
        load_config(str(bad))


def test_load_manifest_returns_list_of_hooks(tmp_path):
    cl = _try_import_clientlib()
    load_manifest = getattr(cl, "load_manifest", None) if cl else None
    if load_manifest is None:
        pytest.skip("load_manifest not importable from pre_commit.clientlib")
    m_file = write_file(tmp_path / "hooks.yaml", manifest_yaml())
    result = load_manifest(str(m_file))
    assert isinstance(result, list)
    assert result[0]["id"] == "scan-markers"
    assert result[0]["language"] == "system"


def test_load_manifest_raises_invalid_manifest_error(tmp_path):
    cl = _try_import_clientlib()
    load_manifest = getattr(cl, "load_manifest", None) if cl else None
    InvalidManifestError = getattr(cl, "InvalidManifestError", None) if cl else None
    if load_manifest is None or InvalidManifestError is None:
        pytest.skip("load_manifest / InvalidManifestError not importable")
    bad = write_file(tmp_path / "bad.yaml", "- id: scan-markers\n")
    with pytest.raises(InvalidManifestError):
        load_manifest(str(bad))


# ---------------------------------------------------------------------------
# Python API: format_color
# ---------------------------------------------------------------------------

def _try_import_color():
    try:
        from pre_commit import color
        return color
    except ImportError:
        return None


def test_format_color_wraps_text_when_color_enabled():
    col = _try_import_color()
    fmt = getattr(col, "format_color", None) if col else None
    if fmt is None:
        pytest.skip("format_color not importable from pre_commit.color")
    RED = getattr(col, "RED", "\033[41m")
    result = fmt("alert", RED, True)
    assert "alert" in result
    assert result != "alert"
    assert "\033[" in result


def test_format_color_returns_plain_text_when_color_disabled():
    col = _try_import_color()
    fmt = getattr(col, "format_color", None) if col else None
    if fmt is None:
        pytest.skip("format_color not importable from pre_commit.color")
    RED = getattr(col, "RED", "\033[41m")
    assert fmt("alert", RED, False) == "alert"


# ---------------------------------------------------------------------------
# Python API: normalize_cmd
# ---------------------------------------------------------------------------

def test_normalize_cmd_raises_for_missing_executable():
    exc_type = None
    normalize = None
    for mod_name in ("pre_commit.util", "pre_commit.languages.helpers"):
        try:
            mod = __import__(mod_name, fromlist=["normalize_cmd"])
            fn = getattr(mod, "normalize_cmd", None)
            et = getattr(mod, "ExecutableNotFoundError", None)
            if fn is not None and et is not None:
                normalize, exc_type = fn, et
                break
        except ImportError:
            continue
    if normalize is None or exc_type is None:
        pytest.skip("normalize_cmd / ExecutableNotFoundError not importable")
    with pytest.raises(exc_type):
        normalize(("nonexistent-command-xyz987654",))


# ---------------------------------------------------------------------------
# Store directory selection
# ---------------------------------------------------------------------------

def test_store_respects_pre_commit_home_env(tmp_path, monkeypatch):
    custom = tmp_path / "custom-store-loc"
    monkeypatch.setenv("PRE_COMMIT_HOME", str(custom))
    monkeypatch.chdir(tmp_path)
    assert main(("gc",)) == 0
    assert custom.is_dir()


# ---------------------------------------------------------------------------
# Module invocation
# ---------------------------------------------------------------------------

def test_module_invocation_version_matches_cli(tmp_path, monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "store"))
    proc = run_pre_commit(tmp_path, "--version")
    assert proc.returncode == 0
    assert proc.stdout.strip().startswith("pre-commit ")
