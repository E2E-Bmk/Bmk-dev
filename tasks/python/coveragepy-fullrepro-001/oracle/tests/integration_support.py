from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator


@contextlib.contextmanager
def sandbox() -> Iterator[Path]:
    root = Path(tempfile.mkdtemp(prefix="coveragepy-v2-integration-"))
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


@contextlib.contextmanager
def working_directory(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def write_py(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def exec_source(path: Path) -> None:
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), {})


def measured_file(data: Any, suffix: str) -> str:
    suffix = suffix.replace("\\", "/")
    matches = [name for name in data.measured_files() if name.replace("\\", "/").endswith(suffix)]
    assert len(matches) == 1, matches
    return matches[0]


def close_data(*objects: Any) -> None:
    for obj in objects:
        try:
            obj.close()
        except Exception:
            pass


def close_coverage(cov: Any) -> None:
    try:
        from coverage import Coverage

        if Coverage.current() is cov:
            cov.stop()
    finally:
        try:
            cov.get_data().close()
        except Exception:
            pass


def collect_program(
    root: Path,
    text: str,
    *,
    filename: str = "program.py",
    branch: bool = False,
    context: str | None = None,
    data_file: Path | None = None,
):
    from coverage import Coverage

    program = write_py(root / filename, text)
    target = data_file or (root / ".coverage")
    cov = Coverage(
        data_file=str(target),
        branch=branch,
        context=context,
        source=[str(root)],
        config_file=False,
    )
    cov.start()
    try:
        exec_source(program)
    finally:
        cov.stop()
    cov.save()
    return cov, program


def cli_env(root: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("COVERAGE_"):
            env.pop(name)
    home = root / ".home"
    config = root / ".config"
    home.mkdir(exist_ok=True)
    config.mkdir(exist_ok=True)
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "XDG_CONFIG_HOME": str(config),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "NO_COLOR": "1",
        }
    )
    env.update(extra or {})
    return env


def run_cli(root: Path, *args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-m", "coverage", *args],
        cwd=root,
        env=cli_env(root, extra_env),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
        check=False,
    )


def logical_snapshot(data: Any) -> dict[str, Any]:
    files = sorted(data.measured_files())
    arcs = data.has_arcs()
    return {
        "has_arcs": arcs,
        "files": files,
        "payload": {name: sorted((data.arcs(name) if arcs else data.lines(name)) or []) for name in files},
        "contexts": {name: data.contexts_by_lineno(name) for name in files},
        "tracers": {name: data.file_tracer(name) for name in files},
        "blob": data.dumps(),
    }


def directory_snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def json_total(path: Path) -> tuple[int, int, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    totals = payload["totals"]
    return totals["covered_lines"], totals["num_statements"], totals["percent_covered"]
