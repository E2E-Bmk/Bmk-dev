"""Shared fixtures, helpers, and constants for copier oracle tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def build_template(tmp_path: Path, copier_yml: str, files: dict[str, str] | None = None) -> Path:
    """Create a template directory with copier.yml and optional template files.

    Returns the template source path.
    """
    src = tmp_path / "tpl"
    src.mkdir(parents=True, exist_ok=True)
    (src / "copier.yml").write_text(copier_yml, encoding="utf-8")
    if files:
        for rel, content in files.items():
            fpath = src / rel
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content, encoding="utf-8")
    return src


def build_git_template(
    tmp_path: Path,
    copier_yml: str,
    files: dict[str, str] | None = None,
    tag: str = "v1.0.0",
) -> Path:
    """Create a git-versioned template with a tag. Returns the template path."""
    src = build_template(tmp_path, copier_yml, files)
    subprocess.run(["git", "init", "-q"], cwd=src, check=True)
    subprocess.run(
        ["git", "config", "user.email", "oracle@test.invalid"], cwd=src, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Oracle"], cwd=src, check=True
    )
    subprocess.run(["git", "add", "."], cwd=src, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"release {tag}"], cwd=src, check=True)
    subprocess.run(["git", "tag", tag], cwd=src, check=True)
    return src


def git_init_project(dst: Path) -> None:
    """Initialize destination as a git repo with one commit (needed for update)."""
    subprocess.run(["git", "init", "-q"], cwd=dst, check=True)
    subprocess.run(
        ["git", "config", "user.email", "oracle@test.invalid"], cwd=dst, check=True
    )
    subprocess.run(["git", "config", "user.name", "Oracle"], cwd=dst, check=True)
    subprocess.run(["git", "add", "."], cwd=dst, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=dst, check=True)


def add_git_tag(repo: Path, tag: str, message: str = "next") -> None:
    """Stage all, commit, and tag inside an existing git repo."""
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)
    subprocess.run(["git", "tag", tag], cwd=repo, check=True)


def read_yaml(path: Path) -> dict:
    """Load a YAML file and return its contents as a dict."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run_copier_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke copier CLI and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "copier", *args],
        text=True,
        capture_output=True,
        check=False,
    )


ANSWERS_TEMPLATE = "{{ _copier_answers|to_nice_yaml -}}\n"

ANSWERS_FILE_ENTRY = "{{ _copier_conf.answers_file }}.jinja"

SIMPLE_COPIER_YML = """\
billing_svc:
  type: str
  default: payments
"""

MULTI_QUESTION_YML = """\
billing_svc:
  type: str
  default: payments
region_code:
  type: str
  default: us-west-2
replica_count:
  type: int
  default: 3
"""
