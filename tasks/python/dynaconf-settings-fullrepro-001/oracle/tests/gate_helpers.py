from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from contextlib import contextmanager
from pathlib import Path


_MISSING = object()


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
    return path


def write_json(path: Path, value) -> Path:
    return write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True))


@contextmanager
def patched_environ(values: dict[str, str], remove: tuple[str, ...] = ()):
    keys = set(values) | set(remove)
    before = {key: os.environ.get(key, _MISSING) for key in keys}
    try:
        for key in remove:
            os.environ.pop(key, None)
        os.environ.update(values)
        yield
    finally:
        for key, value in before.items():
            if value is _MISSING:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_module(cwd: Path, module: str, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "NO_COLOR": "1",
        }
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-m", module, *args],
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    return subprocess.CompletedProcess(
        completed.args,
        completed.returncode,
        completed.stdout.decode("utf-8", "strict"),
        completed.stderr.decode("utf-8", "strict"),
    )


def environment_file(root: Path) -> Path:
    return write_text(
        root / "environments.toml",
        """
        [default]
        SHARED = "base"
        [alpha]
        VALUE = "alpha"
        PORT = 4101
        [beta]
        VALUE = "beta"
        PORT = 4201
        [gamma]
        VALUE = "gamma"
        PORT = 4301
        [delta]
        VALUE = "delta"
        PORT = 4401
        """,
    )


def public_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.name.startswith(".tmp-")
    }

