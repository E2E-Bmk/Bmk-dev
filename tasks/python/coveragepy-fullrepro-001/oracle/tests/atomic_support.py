from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterator


@contextlib.contextmanager
def sandbox() -> Iterator[Path]:
    root = Path(tempfile.mkdtemp(prefix="coveragepy-v2-atomic-"))
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
