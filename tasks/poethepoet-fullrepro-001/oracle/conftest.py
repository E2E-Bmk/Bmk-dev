from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


RUNNER = r"""
import json
import os
from pathlib import Path
import sys


def emit(value):
    print(json.dumps(value, sort_keys=True))


def append_event(label):
    path = Path("events.log")
    prior = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(prior + label + "\n", encoding="utf-8")


def main():
    mode = sys.argv[1]
    if mode == "argv":
        emit({"args": sys.argv[2:]})
    elif mode == "env":
        emit({name: os.environ.get(name) for name in sys.argv[2:]})
    elif mode == "cwd":
        emit({
            "cwd": Path.cwd().name,
            "root": Path(os.environ.get("POE_ROOT", "")).name,
            "conf": Path(os.environ.get("POE_CONF_DIR", "")).name,
            "pwd": Path(os.environ.get("POE_PWD", "")).name,
        })
    elif mode == "record":
        append_event(sys.argv[2])
        emit({"recorded": sys.argv[2]})
    elif mode == "emit":
        print(" ".join(sys.argv[2:]))
    elif mode == "envlines":
        print("FROM_USE=alpha")
        print("SECOND=beta")
    elif mode == "fail":
        raise SystemExit(int(sys.argv[2]))
    elif mode == "touch":
        Path(sys.argv[2]).write_text(sys.argv[3] + "\n", encoding="utf-8")
    else:
        raise SystemExit(64)


if __name__ == "__main__":
    main()
"""


TASKSMOD = r"""
from __future__ import annotations

import json
from pathlib import Path
import sys


def _emit(value):
    print(json.dumps(value, sort_keys=True))


def emit(name="anon", count=0, flag=False, ratio=0.0, items=None, _extra_args=None):
    _emit({
        "name": name,
        "count": count,
        "flag": flag,
        "ratio": ratio,
        "items": items,
        "extra": _extra_args or [],
    })


def record(label):
    path = Path("events.log")
    prior = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(prior + label + "\n", encoding="utf-8")
    _emit({"script_recorded": label})


def result(value="ok"):
    return "RESULT:" + str(value)


def argv_probe(subject="none", _extra_args=None):
    _emit({"subject": subject, "argv": sys.argv[1:], "extra": _extra_args or []})
"""


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


class PoeRun:
    def __init__(self, returncode: int, stdout: str, stderr: str, cwd: Path):
        self.returncode = returncode
        self.stdout = stdout.replace("\r\n", "\n")
        self.stderr = stderr.replace("\r\n", "\n")
        self.cwd = cwd

    @property
    def json_objects(self):
        result = []
        for line in self.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                result.append(json.loads(stripped))
        return result

    @property
    def plain_lines(self):
        return [
            line.strip()
            for line in self.stdout.splitlines()
            if line.strip() and not line.startswith("Poe ")
        ]


def write_project(root: Path, config: str, *, filename: str = "pyproject.toml") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / filename).write_text(textwrap.dedent(config).lstrip(), encoding="utf-8")
    (root / "runner.py").write_text(RUNNER, encoding="utf-8")
    src = root / "src"
    src.mkdir(exist_ok=True)
    (src / "tasksmod.py").write_text(TASKSMOD, encoding="utf-8")
    return root


@pytest.fixture
def poe_project(tmp_path: Path):
    def factory(config: str, *, filename: str = "pyproject.toml") -> Path:
        return write_project(tmp_path / "project", config, filename=filename)

    return factory


def poe_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get("POE_ORACLE_PYTHONPATH", ""),
        "PYTHON": sys.executable,
        "NO_COLOR": "1",
        "POETRY_VIRTUALENVS_CREATE": "false",
    }
    if extra:
        env.update(extra)
    return env


def run_poe(project: Path, *args: str, env: dict[str, str] | None = None) -> PoeRun:
    completed = subprocess.run(
        [sys.executable, "-m", "poethepoet", *args],
        cwd=project,
        env=poe_env(env),
        text=True,
        capture_output=True,
        timeout=30,
    )
    return PoeRun(completed.returncode, completed.stdout, completed.stderr, project)


@pytest.fixture
def poe_runner():
    return run_poe
