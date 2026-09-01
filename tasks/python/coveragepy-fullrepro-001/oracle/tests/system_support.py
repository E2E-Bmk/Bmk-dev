from __future__ import annotations

import contextlib
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator


@contextlib.contextmanager
def sandbox() -> Iterator[Path]:
    root = Path(tempfile.mkdtemp(prefix="coveragepy-v2-system-"))
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def write_py(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def exec_source(path: Path) -> None:
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), {})


def close_data(*objects: Any) -> None:
    for obj in objects:
        try:
            obj.close()
        except Exception:
            pass


def close_coverage(cov: Any) -> None:
    try:
        from coverage import Coverage

        while Coverage.current() is cov:
            cov.stop()
    except Exception:
        pass
    try:
        cov.get_data().close()
    except Exception:
        pass


def directory_snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def trace_identity() -> object | None:
    return sys.gettrace()

