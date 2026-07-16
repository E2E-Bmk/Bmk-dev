# Spec2Repo oracle - atomic tests for tox-envrunner-fullrepro-001
import json

import os

import subprocess

import sys

import textwrap

from pathlib import Path

def run_tox(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("TOX")}
    env.update(
        {
            "NO_COLOR": "1",
            "PYTHONIOENCODING": "utf-8",
            "TOX_REPORTER_TIMESTAMP": "0",
        },
    )
    return subprocess.run(
        [sys.executable, "-m", "tox", "--colored", "no", *args],
        cwd=project,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )


def write(project: Path, name: str, content: str) -> Path:
    path = project / name
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def load_json_output(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def json_config(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_public_import_surface_exposes_main_version_and_plugin_marker(tmp_path):
    from tox import __version__, main
    from tox.plugin import NAME, impl

    assert isinstance(__version__, str)
    assert __version__
    assert callable(main)
    assert NAME == "tox"
    assert callable(impl)
    result = run_tox(tmp_path, "--version")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tox" in result.stdout.lower()


def test_config_core_json_includes_env_list_only_when_core_is_requested(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]

        [env.lint]
        package = "skip"
        skip_install = true
        description = "lint"
        commands = [["python", "-c", "print('lint')"]]
        """,
    )

    without_core = run_tox(tmp_path, "config", "-k", "env_list", "--format", "json")
    with_core = run_tox(tmp_path, "config", "--core", "-k", "env_list", "--format", "json")

    assert "tox" not in load_json_output(without_core)
    data = load_json_output(with_core)
    assert data["tox"]["env_list"] == ["lint"]
    assert set(data["env"]) == {"lint"}


def test_config_toml_output_file_writes_selected_env_without_stdout(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        r'''
        [tox]
        env_list = py310-django42

        [testenv]
        package = skip
        skip_install = true
        description = run {env_name}
        commands = python -c "print('{env_name}')"
        ''',
    )
    output = tmp_path / "selected.toml"

    result = run_tox(
        tmp_path,
        "config",
        "-e",
        "py310-django42",
        "-k",
        "description",
        "--format",
        "toml",
        "-o",
        str(output),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""
    assert output.read_text(encoding="utf-8") == '[env.py310-django42]\ndescription = "run py310-django42"\n'


def test_main_returns_success_for_version_query():
    from tox import main

    try:
        result = main(["--version"])
    except SystemExit as exc:
        result = exc.code
    assert result == 0


def test_plugin_hook_marker_decorates_public_hook_function():
    from tox.plugin import impl

    @impl
    def tox_extend_envs():
        return ["extra"]

    assert getattr(tox_extend_envs, "tox_impl", None) is not None


def test_common_subcommands_are_advertised_in_help(tmp_path):
    result = run_tox(tmp_path, "--help")

    assert result.returncode == 0, result.stdout + result.stderr
    for name in ["run", "list", "config", "exec"]:
        assert name in result.stdout
    assert "parallel" in result.stdout


def test_pylock_and_deps_are_mutually_exclusive(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]

        [env.lint]
        package = "skip"
        skip_install = true
        deps = ["pytest"]
        pylock = "pylock.toml"
        commands = [["python", "-c", "print('lint')"]]
        """,
    )
    write(tmp_path, "pylock.toml", "")

    result = run_tox(tmp_path, "config", "-e", "lint")

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "pylock" in combined.lower()
    assert "deps" in combined.lower()


def test_config_output_file_writes_json_without_stdout(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["py"]
        [env.py]
        package = "skip"
        skip_install = true
        description = "written"
        """,
    )
    output = tmp_path / "config.json"
    result = run_tox(tmp_path, "config", "-k", "description", "--format", "json", "-o", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""
    assert json.loads(output.read_text(encoding="utf-8"))["env"]["py"]["description"] == "written"


def test_public_version_is_nonempty_string():
    from tox import __version__

    assert isinstance(__version__, str)
    assert __version__
