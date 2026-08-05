from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path
from typing import Callable

import isort
import pytest


UNSORTED_CODE = "import z\nfrom third import b, a\nimport os\nimport sys\n"
SORTED_CODE = "import os\nimport sys\n\nimport z\nfrom third import a, b\n"
SIMPLE_UNSORTED = "import z\nimport os\n"
SIMPLE_SORTED = "import os\n\nimport z\n"
LONG_FROM = "from package import zeta, alpha, beta, gamma, delta\n"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")
    config.addinivalue_line("filterwarnings", "error")


@pytest.fixture
def base_config() -> isort.Config:
    return isort.Config()


@pytest.fixture
def unsorted_code() -> str:
    return UNSORTED_CODE


@pytest.fixture
def sorted_code() -> str:
    return SORTED_CODE


@pytest.fixture
def simple_unsorted() -> str:
    return SIMPLE_UNSORTED


@pytest.fixture
def simple_sorted() -> str:
    return SIMPLE_SORTED


@pytest.fixture
def long_from() -> str:
    return LONG_FROM


@pytest.fixture
def make_file(tmp_path: Path) -> Callable[[str, str], Path]:
    def _make_file(name: str, content: str) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    return _make_file


@pytest.fixture
def run_cli() -> Callable[..., subprocess.CompletedProcess[str]]:
    def _run_cli(
        args: list[object],
        *,
        input_text: str | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "isort", *(str(arg) for arg in args)]
        environment = os.environ.copy()
        support_path = environment.get("ISORT_SUPPORT_PATH")
        if support_path:
            python_path = environment.get("PYTHONPATH")
            entries = [support_path]
            if python_path:
                entries.append(python_path)
            environment["PYTHONPATH"] = os.pathsep.join(entries)
        return subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            cwd=cwd,
            env=environment,
            check=False,
        )

    return _run_cli
