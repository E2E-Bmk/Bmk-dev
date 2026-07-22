# Spec2Repo oracle - atomic tests for tox-envrunner-fullrepro-001
import json

import os
import shutil

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
    executable = shutil.which("tox", path=str(Path(sys.executable).parent)) or shutil.which("tox")
    assert executable is not None, "the documented tox console script is not installed"
    return subprocess.run(
        [executable, "--colored", "no", *args],
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


def test_list_reports_configured_environment_and_description(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint"]\n[env.lint]\npackage = "skip"\nskip_install = true\ndescription = "check style"\n',
    )

    result = run_tox(tmp_path, "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "lint" in result.stdout
    assert "check style" in result.stdout


def test_config_json_selects_named_environment(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint", "docs"]\n[env.lint]\npackage = "skip"\nskip_install = true\n[env.docs]\npackage = "skip"\nskip_install = true\n',
    )

    result = run_tox(tmp_path, "config", "-e", "docs", "--format", "json")
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout[result.stdout.index("{"):])

    assert set(data["env"]) == {"docs"}


def test_config_keyword_filter_limits_environment_projection(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint"]\n[env.lint]\npackage = "skip"\nskip_install = true\ndescription = "style"\ncommands = [["python", "-c", "print(1)"]]\n',
    )

    data = load_json_output(run_tox(tmp_path, "config", "-e", "lint", "-k", "description", "--format", "json"))

    assert data["env"]["lint"] == {"description": "style"}


def test_config_core_projection_reports_environment_list(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint"]\n[env.lint]\npackage = "skip"\nskip_install = true\n',
    )

    data = load_json_output(run_tox(tmp_path, "config", "--core", "-k", "env_list", "--format", "json"))

    assert data["tox"]["env_list"] == ["lint"]


def test_unknown_environment_selection_returns_nonzero(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint"]\n[env.lint]\npackage = "skip"\nskip_install = true\n',
    )

    result = run_tox(tmp_path, "config", "-e", "missing")

    assert result.returncode != 0


def test_misspelled_python_environment_selection_returns_nonzero(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["py311"]\n[env.py311]\npackage = "skip"\nskip_install = true\n',
    )

    result = run_tox(tmp_path, "config", "-e", "py999")

    assert result.returncode != 0


def test_list_reports_all_configured_environments(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint", "docs"]\n[env.lint]\npackage = "skip"\nskip_install = true\n[env.docs]\npackage = "skip"\nskip_install = true\n',
    )

    result = run_tox(tmp_path, "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "docs" in result.stdout
    assert "lint" in result.stdout


def test_config_json_preserves_boolean_values(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint"]\n[env.lint]\npackage = "skip"\nskip_install = true\n',
    )

    data = load_json_output(run_tox(tmp_path, "config", "-e", "lint", "-k", "skip_install", "--format", "json"))

    assert data["env"]["lint"]["skip_install"] is True


def test_config_json_reports_environment_description(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        'env_list = ["lint"]\n[env.lint]\npackage = "skip"\nskip_install = true\ndescription = "static checks"\n',
    )

    data = load_json_output(run_tox(tmp_path, "config", "-e", "lint", "-k", "description", "--format", "json"))

    assert data["env"]["lint"]["description"] == "static checks"


def test_explicit_config_path_works_outside_project_directory(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    config = write(
        project,
        "tox.toml",
        'env_list = ["lint"]\n[env.lint]\npackage = "skip"\nskip_install = true\n',
    )
    outside = tmp_path / "outside"
    outside.mkdir()

    result = run_tox(outside, "-c", str(config), "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "lint" in result.stdout


def test_version_command_matches_public_version(tmp_path):
    from tox import __version__

    result = run_tox(tmp_path, "--version")

    assert result.returncode == 0, result.stdout + result.stderr
    assert __version__ in result.stdout


def test_help_command_returns_success_and_usage(tmp_path):
    result = run_tox(tmp_path, "--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage" in result.stdout.lower()
