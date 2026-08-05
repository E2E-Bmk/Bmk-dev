from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import BytesIO, StringIO, TextIOWrapper
import os
from pathlib import Path
import sys
import textwrap
from typing import Callable, Iterator, Sequence

import pytest


@dataclass(frozen=True)
class RunResult:
    code: int
    stdout: str
    stderr: str


class TargetOnlyPylintFinder:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "pylint" or fullname.startswith("pylint."):
            raise ModuleNotFoundError(
                "pylint is not available from the selected target root"
            )
        return None


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the pylint package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic public behaviors used by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return

    target_root = Path(configured_root).resolve()
    for name in list(sys.modules):
        if name == "pylint" or name.startswith("pylint."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))
    if not (target_root / "pylint").is_dir():
        sys.meta_path.insert(0, TargetOnlyPylintFinder())


def write_python(base: Path, relative: str, content: str) -> Path:
    path = base / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def relative_to(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


@contextmanager
def local_run_state(cwd: Path, stdin_text: str | None = None) -> Iterator[None]:
    old_cwd = Path.cwd()
    old_stdin = sys.stdin
    saved_env = {key: os.environ.get(key) for key in (
        "HOME",
        "PYLINTRC",
        "PYLINTHOME",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
    )}
    local_home = cwd / ".home"
    local_home.mkdir(exist_ok=True)
    os.environ["HOME"] = str(local_home)
    os.environ.pop("PYLINTRC", None)
    os.environ["PYLINTHOME"] = str(cwd / ".pylint-home")
    os.environ["XDG_CACHE_HOME"] = str(cwd / ".cache")
    os.environ["XDG_CONFIG_HOME"] = str(cwd / ".config")
    if stdin_text is not None:
        sys.stdin = TextIOWrapper(BytesIO(stdin_text.encode("utf-8")), encoding="utf-8")
    os.chdir(cwd)
    try:
        yield
    finally:
        os.chdir(old_cwd)
        sys.stdin = old_stdin
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _code(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    return 1


def capture_runner(
    runner: Callable[[Sequence[str] | None], object],
    args: Sequence[str],
    cwd: Path,
    *,
    stdin_text: str | None = None,
) -> RunResult:
    stdout = StringIO()
    stderr = StringIO()
    with local_run_state(cwd, stdin_text=stdin_text):
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                returned = runner(list(args))
            except SystemExit as exc:
                code = _code(exc.code)
            else:
                code = _code(returned)
    return RunResult(code, stdout.getvalue(), stderr.getvalue())


def invoke_pylint(
    args: Sequence[str],
    cwd: Path,
    *,
    stdin_text: str | None = None,
    persistent: bool = False,
) -> RunResult:
    from pylint import run_pylint

    final_args = list(args)
    if not persistent:
        final_args = ["--persistent=no", *final_args]
    return capture_runner(run_pylint, final_args, cwd, stdin_text=stdin_text)


def invoke_pyreverse(args: Sequence[str], cwd: Path) -> RunResult:
    from pylint import run_pyreverse

    return capture_runner(run_pyreverse, list(args), cwd)


def invoke_symilar(args: Sequence[str], cwd: Path) -> RunResult:
    from pylint import run_symilar

    return capture_runner(run_symilar, list(args), cwd)
