"""Shared fixtures, helpers, and constants for pre-commit oracle tests."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from pre_commit.main import main  # noqa: F401 – re-exported for test files


# ── Constants ──────────────────────────────────────────────────────────────

EMPTY_CONFIG_YAML = "repos: []\n"

MINIMAL_MANIFEST_YAML = (
    "- id: scan-markers\n"
    "  name: Scan For Markers\n"
    "  entry: echo scan\n"
    "  language: system\n"
)

MINIMAL_LOCAL_CONFIG_YAML = (
    "repos:\n"
    "- repo: local\n"
    "  hooks:\n"
    "  - id: check-echo\n"
    "    name: Check Echo\n"
    "    entry: echo check\n"
    "    language: system\n"
)


# ── File helpers ───────────────────────────────────────────────────────────

def write_file(path, contents):
    """Write UTF-8 text to *path* and return the ``Path`` object."""
    p = Path(path)
    p.write_text(contents, encoding="UTF-8")
    return p


def write_config(path, config_dict):
    """Serialize *config_dict* as YAML and write to *path*."""
    return write_file(path, yaml.dump(config_dict, default_flow_style=False))


def write_manifest(path, hooks_list):
    """Serialize *hooks_list* as YAML and write to *path*."""
    return write_file(path, yaml.dump(hooks_list, default_flow_style=False))


# ── Git helpers ────────────────────────────────────────────────────────────

def git_cmd(repo, *args):
    """Run a git command in *repo*; skip the test when ``git`` is absent."""
    if shutil.which("git") is None:
        pytest.skip("git is required")
    subprocess.run(
        ("git",) + args,
        cwd=str(repo),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def init_git_repo(path):
    """``git init`` + user config (no initial commit)."""
    git_cmd(path, "init")
    git_cmd(path, "config", "user.email", "oracle@test.example")
    git_cmd(path, "config", "user.name", "Oracle Test")


# ── Subprocess helper ──────────────────────────────────────────────────────

def run_pre_commit(repo, *args):
    """Invoke ``python -m pre_commit`` as a child process; return *CompletedProcess*."""
    return subprocess.run(
        (sys.executable, "-m", "pre_commit") + args,
        cwd=str(repo),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


# ── Config / manifest builder helpers ──────────────────────────────────────

def make_local_hook(hook_id, name, entry, language, **kwargs):
    """Return a hook dict suitable for a ``repo: local`` config entry."""
    hook = {"id": hook_id, "name": name, "entry": entry, "language": language}
    hook.update(kwargs)
    return hook


def local_config_yaml(hook_body):
    """Return a YAML string wrapping *hook_body* inside ``repo: local``."""
    return "repos:\n- repo: local\n  hooks:\n" + hook_body


def validation_local_yaml(*, repo_extra="", hook_extra=""):
    """Minimal valid local-repo config with optional extras injected."""
    return (
        "repos:\n"
        "- repo: local\n"
        f"{repo_extra}"
        "  hooks:\n"
        "  - id: check-echo\n"
        "    name: Check Echo\n"
        "    entry: echo check\n"
        "    language: system\n"
        f"{hook_extra}"
    )


def manifest_yaml(*, extra=""):
    """Minimal valid manifest YAML with optional extras appended."""
    return (
        "- id: scan-markers\n"
        "  name: Scan For Markers\n"
        "  entry: echo scan\n"
        "  language: system\n"
        f"{extra}"
    )


# ── Assertion helpers ──────────────────────────────────────────────────────

def assert_nonzero(argv):
    """Assert that ``main(argv)`` returns a nonzero integer status."""
    status = main(argv)
    assert isinstance(status, int)
    assert status != 0


# ── Repo-with-config setup ─────────────────────────────────────────────────

def setup_repo(tmp_path, monkeypatch, config_text,
               filename="tracked.txt", contents="hello\n"):
    """Create a git repo with one staged file and a config, return ``(repo, cfg)``."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    write_file(repo / filename, contents)
    git_cmd(repo, "add", filename)
    cfg = write_file(repo / ".pre-commit-config.yaml", config_text)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "store"))
    return repo, cfg


def create_hook_repo(tmp_path, hooks_yaml):
    """Create a bare git repo containing a ``.pre-commit-hooks.yaml``."""
    hook_repo = tmp_path / "hook-repo"
    hook_repo.mkdir()
    init_git_repo(hook_repo)
    write_file(hook_repo / ".pre-commit-hooks.yaml", hooks_yaml)
    git_cmd(hook_repo, "add", ".pre-commit-hooks.yaml")
    git_cmd(hook_repo, "commit", "-m", "hooks")
    return hook_repo
