import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


PROJECT_NAME = "sample_lib"


def create_tox_ini(path, content):
    fp = path / "tox.ini"
    fp.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return fp


def create_tox_toml(path, content):
    fp = path / "tox.toml"
    fp.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return fp


def create_pyproject_toml(path, content):
    fp = path / "pyproject.toml"
    fp.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return fp


def create_setup_cfg(path, content):
    fp = path / "setup.cfg"
    fp.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return fp


def write_file(path, name, content):
    fp = path / name
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return fp


def run_tox(project, *args, extra_env=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("TOX")}
    env.update({
        "NO_COLOR": "1",
        "PYTHONIOENCODING": "utf-8",
        "TOX_REPORTER_TIMESTAMP": "0",
    })
    if extra_env:
        env.update(extra_env)
    executable = (
        shutil.which("tox", path=str(Path(sys.executable).parent))
        or shutil.which("tox")
    )
    assert executable is not None, "tox console script is not installed"
    return subprocess.run(
        [executable, "--colored", "no", *args],
        cwd=project,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )


def run_tox_main(args):
    from tox import main
    try:
        code = main(args)
    except SystemExit as exc:
        code = exc.code
    return code if code is not None else 0


def parse_json_output(result):
    assert result.returncode == 0, result.stdout + result.stderr
    text = result.stdout
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.index("{")
        return json.loads(text[start:])
