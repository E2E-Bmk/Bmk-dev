"""Shared fixtures, helpers, and constants for luigi-workflow-fullrepro-001 oracle."""
import enum
import os
import subprocess
import sys
import textwrap

import pytest


# ── Shared enum types (anti-memorization: values differ from upstream) ──

class Flavor(enum.Enum):
    VANILLA = 1
    CHOCOLATE = 2
    STRAWBERRY = 3


# ── Subprocess helpers ──────────────────────────────────────────────────

def run_script(tmp_path, code, extra_env=None, timeout=20):
    """Execute a dedented Python snippet in a fresh subprocess under *tmp_path*."""
    script = tmp_path / "probe.py"
    script.write_text(textwrap.dedent(code), encoding="utf-8")
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def run_cli(tmp_path, args, extra_env=None, timeout=30):
    """Execute ``python -m luigi`` with *args* under *tmp_path*."""
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "luigi"] + list(args),
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def write_module(tmp_path, name, code):
    """Write a dedented Python module to *tmp_path/{name}.py* and return its path."""
    path = tmp_path / f"{name}.py"
    path.write_text(textwrap.dedent(code), encoding="utf-8")
    return path
