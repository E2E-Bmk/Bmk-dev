"""Shared fixtures, helpers, and constants for dynaconf oracle tests."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def _write(path: Path, text: str) -> Path:
    """Write dedented text to a file and return the path."""
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
    return path


def _run_dynaconf_cli(tmp_path: Path, *args: str, env=None, input_text=None):
    """Run the dynaconf CLI as a subprocess."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "dynaconf", *args],
        cwd=tmp_path,
        env=run_env,
        text=True,
        capture_output=True,
        input=input_text,
        timeout=60,
    )
