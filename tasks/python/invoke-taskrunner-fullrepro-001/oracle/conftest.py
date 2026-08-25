"""Shared fixtures, helpers, and constants for invoke oracle tests."""
import os
import subprocess
import sys
import textwrap

import pytest
from invoke import Config, Result, Runner

PYTHON = sys.executable


def write_file(path, body):
    """Write dedented text to *path*, stripping common leading whitespace."""
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def run_invoke(tmp_path, *args, env=None):
    """Run ``python -m invoke`` in *tmp_path* and return CompletedProcess."""
    cmd = [PYTHON, "-m", "invoke", *args]
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(tmp_path),
        env=merged,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class RecordingRunner(Runner):
    """Runner that records invocations instead of executing commands."""

    seen = []

    def run(self, command, **kwargs):
        self.__class__.seen.append((command, kwargs, self.context))
        return Result(command=command, stdout="captured\n", exited=0)


@pytest.fixture
def fresh_runner():
    """Yield a clean RecordingRunner and reset after use."""
    RecordingRunner.seen.clear()
    yield RecordingRunner
    RecordingRunner.seen.clear()
