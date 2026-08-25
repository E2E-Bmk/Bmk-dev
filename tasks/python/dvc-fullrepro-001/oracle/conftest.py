"""Shared helpers, fixtures, and constants for dvc-fullrepro-001 oracle tests."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from dvc.exceptions import DvcException  # noqa: F401 — re-exported for test files
from dvc.repo import Repo

REMOTE_URL = "https://storage.example.test/datasets"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic tests this integration test depends on",
    )


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def run_dvc(cwd, *args, check=True):
    """Run the installed ``dvc`` console command in *cwd*."""
    env = os.environ.copy()
    env["DVC_TEST"] = "true"
    env["DVC_NO_ANALYTICS"] = "1"
    result = subprocess.run(
        ["dvc", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        env=env,
        timeout=120,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"dvc {' '.join(args)} rc={result.returncode}\n{result.stderr}"
        )
    return result


def load_yaml(path):
    """Read and parse a YAML file."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def write_yaml(path, data):
    """Serialize *data* as YAML into *path*."""
    Path(path).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def make_script(root, name, code):
    """Write a Python helper script into *root*."""
    Path(root, name).write_text(code, encoding="utf-8")


def init_repo(path):
    """Create *path*, call ``Repo.init(no_scm=True)``, and return the Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    Repo.init(root_dir=str(p), no_scm=True)
    return p


# ---------------------------------------------------------------------------
# Thin wrappers that set cwd before calling Repo methods
# ---------------------------------------------------------------------------

def repo_run(root, **kwargs):
    """``Repo.run(no_exec=True, **kwargs)`` with cwd = *root*."""
    old = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root), uninitialized=True).run(no_exec=True, **kwargs)
    finally:
        os.chdir(old)


def repo_freeze(root, target):
    old = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root), uninitialized=True).freeze(target)
    finally:
        os.chdir(old)


def repo_unfreeze(root, target):
    old = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root), uninitialized=True).unfreeze(target)
    finally:
        os.chdir(old)


def repo_status(root):
    old = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root)).status()
    finally:
        os.chdir(old)


def repo_reproduce(root, **kwargs):
    old = Path.cwd()
    os.chdir(root)
    try:
        return Repo(str(root)).reproduce(**kwargs)
    finally:
        os.chdir(old)


# ---------------------------------------------------------------------------
# Pre-built stage setups (used by integration tests)
# ---------------------------------------------------------------------------

def add_single_stage(root):
    """source.txt → artifact.txt  (stage name ``transform``)."""
    (root / "source.txt").write_text("gamma\n", encoding="utf-8")
    make_script(
        root, "copy_upper.py",
        "from pathlib import Path\nimport sys\n"
        "Path(sys.argv[2]).write_text("
        "Path(sys.argv[1]).read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "transform",
        "-d", "source.txt", "-d", "copy_upper.py",
        "-o", "artifact.txt",
        sys.executable, "copy_upper.py", "source.txt", "artifact.txt",
    )


def add_counting_stage(root):
    """Like *add_single_stage* but writes ``run_tally.txt`` to count runs."""
    (root / "source.txt").write_text("delta\n", encoding="utf-8")
    make_script(
        root, "counting.py",
        "from pathlib import Path\nimport sys\n"
        "c = Path('run_tally.txt')\n"
        "n = int(c.read_text(encoding='utf-8')) if c.exists() else 0\n"
        "c.write_text(str(n + 1), encoding='utf-8')\n"
        "Path(sys.argv[2]).write_text("
        "Path(sys.argv[1]).read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "transform",
        "-d", "source.txt", "-d", "counting.py",
        "-o", "artifact.txt",
        sys.executable, "counting.py", "source.txt", "artifact.txt",
    )


def add_two_stage_pipeline(root):
    """transform (source→intermediate) → assemble (intermediate→artifact)."""
    (root / "source.txt").write_text("gamma", encoding="utf-8")
    make_script(
        root, "upper.py",
        "from pathlib import Path\n"
        "Path('intermediate.txt').write_text("
        "Path('source.txt').read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
    )
    make_script(
        root, "combine.py",
        "from pathlib import Path\n"
        "Path('artifact.txt').write_text("
        "Path('intermediate.txt').read_text(encoding='utf-8') + ':done', encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "transform",
        "-d", "source.txt", "-d", "upper.py",
        "-o", "intermediate.txt",
        sys.executable, "upper.py",
    )
    run_dvc(
        root, "stage", "add", "-n", "assemble",
        "-d", "intermediate.txt", "-d", "combine.py",
        "-o", "artifact.txt",
        sys.executable, "combine.py",
    )
