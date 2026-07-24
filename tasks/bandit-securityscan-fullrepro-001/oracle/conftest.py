"""Shared fixtures, helpers, and constants for bandit-securityscan-fullrepro-001 oracle."""
import json
import os
import shlex
import subprocess
from pathlib import Path

import pytest


def _tool(name):
    override = os.environ.get(name.upper().replace("-", "_") + "_BIN")
    return override or name


def run_bandit(name, args, *, cwd=None, stdin=None):
    """Run a bandit CLI command."""
    env = os.environ.copy()
    bandit_command = shlex.split(_tool("bandit"))[0]
    if os.path.isabs(bandit_command):
        env["PATH"] = str(Path(bandit_command).parent) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [*shlex.split(_tool(name)), *args],
        cwd=cwd, env=env, input=stdin, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def write_source(tmp_path, name, text):
    """Write a Python source file and return its path."""
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def json_scan(tmp_path, source, *args, name="sample.py"):
    """Run bandit on a source string and return (proc, report, target_path)."""
    target = write_source(tmp_path, name, source)
    proc = run_bandit("bandit", ["-q", "-f", "json", *args, str(target)])
    return proc, json.loads(proc.stdout), target


def one_issue(tmp_path, source, expected_id, *, severity=None, confidence=None, cwe=None):
    """Assert exactly one issue with the expected ID is found."""
    proc, report, _ = json_scan(tmp_path, source, "-t", expected_id)
    assert proc.returncode == 1
    assert len(report["results"]) == 1
    issue = report["results"][0]
    assert issue["test_id"] == expected_id
    if severity:
        assert issue["issue_severity"] == severity
    if confidence:
        assert issue["issue_confidence"] == confidence
    if cwe:
        assert issue["issue_cwe"]["id"] == cwe
    return issue


def ids(report):
    """Extract test_id set from a report."""
    return {item["test_id"] for item in report["results"]}
