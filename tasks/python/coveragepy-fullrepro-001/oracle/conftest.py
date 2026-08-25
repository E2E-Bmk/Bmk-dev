"""Shared fixtures, helpers, and constants for coveragepy-fullrepro-001 oracle."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from coverage import Coverage, CoverageData


def write_py(path: Path, text: str) -> Path:
    """Write a Python source file."""
    path.write_text(text, encoding="utf-8")
    return path


def run_cli(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run the coverage CLI."""
    run_env = os.environ.copy()
    if env:
        extra_env = dict(env)
        if "PYTHONPATH" in extra_env and run_env.get("PYTHONPATH"):
            extra_env["PYTHONPATH"] = extra_env["PYTHONPATH"] + os.pathsep + run_env["PYTHONPATH"]
        run_env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "coverage", *args],
        cwd=cwd, text=True, capture_output=True, env=run_env, timeout=30,
    )


def measured_file(data: CoverageData, suffix: str) -> str:
    """Find a measured file by suffix."""
    return next(name for name in data.measured_files() if name.endswith(suffix))


def collect_file(
    tmp_path: Path, source: str, *, branch: bool = False, context: str | None = None
) -> tuple[Coverage, Path]:
    """Run coverage on a source string and return (Coverage, program_path)."""
    program = write_py(tmp_path / "sample.py", source)
    cov = Coverage(
        data_file=str(tmp_path / ".coverage"),
        source=[str(tmp_path)], branch=branch, context=context,
    )
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()
    return cov, program
