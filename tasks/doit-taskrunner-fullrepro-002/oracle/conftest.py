"""Shared helpers for doit-taskrunner-fullrepro-002 oracle tests."""
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def write_dodo(tmp_path, source):
    dodo = tmp_path / "dodo.py"
    dodo.write_text(textwrap.dedent(source), encoding="utf-8")
    return dodo


def doit_env():
    env = os.environ.copy()
    current = env.get("PYTHONPATH")
    entries = [str(entry) for entry in sys.path if entry]
    if current:
        entries.append(current)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


def run_doit(tmp_path, *args, check=True):
    proc = subprocess.run(
        [sys.executable, "-m", "doit", *args],
        cwd=tmp_path,
        env=doit_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"doit exited with {proc.returncode}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


COMMON_ACTIONS = """
        from pathlib import Path

        def write_text(path, text):
            Path(path).write_text(str(text), encoding="utf-8")
            return None

        def append_text(path, text):
            with Path(path).open("a", encoding="utf-8") as stream:
                stream.write(str(text))
            return None

        def copy_upper(dependencies, targets):
            Path(targets[0]).write_text(
                Path(dependencies[0]).read_text(encoding="utf-8").upper(),
                encoding="utf-8",
            )
            return None

        def count_run(path):
            p = Path(path)
            value = int(p.read_text(encoding="utf-8")) if p.exists() else 0
            p.write_text(str(value + 1), encoding="utf-8")
            return {"count": value + 1}
"""


def common_actions():
    return COMMON_ACTIONS
