import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def run_tox(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("TOX")}
    env.update({"NO_COLOR": "1", "PYTHONIOENCODING": "utf-8", "TOX_REPORTER_TIMESTAMP": "0"})
    return subprocess.run(
        [sys.executable, "-m", "tox", "--colored", "no", *args],
        cwd=project,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90,
        check=False,
    )


def write(project: Path, name: str, content: str) -> Path:
    path = project / name
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def json_config(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_ini_env_var_substitution_uses_default_when_missing(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = py

        [testenv]
        package = skip
        skip_install = true
        description = {env:TOX_MISSING:default-value}
        commands = python -c "print('ok')"
        """,
    )
    data = json_config(run_tox(tmp_path, "config", "-k", "description", "--format", "json"))
    assert data["env"]["py"]["description"] == "default-value"


def test_posargs_default_is_used_without_extra_arguments(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = py

        [testenv]
        package = skip
        skip_install = true
        commands = python -c "print('{posargs:default text}')"
        """,
    )
    data = json_config(run_tox(tmp_path, "config", "-k", "commands", "--format", "json"))
    assert data["env"]["py"]["commands"] == ['python -c "print(\'default text\')"']


def test_posargs_override_default_after_separator(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = py

        [testenv]
        package = skip
        skip_install = true
        commands = python -c "print('{posargs:default}')"
        """,
    )
    data = json_config(run_tox(tmp_path, "config", "-k", "commands", "--format", "json", "--", "custom"))
    assert data["env"]["py"]["commands"] == ["python -c print('custom')"]


def test_generative_ini_env_list_expands_factor_product(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = py{310,311}-django{42,50}

        [testenv]
        package = skip
        skip_install = true
        commands = python -c "print('{env_name}')"
        """,
    )
    result = run_tox(tmp_path, "list", "--no-desc")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        "py310-django42",
        "py310-django50",
        "py311-django42",
        "py311-django50",
    ]


def test_factor_filter_selects_matching_environments(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = py310-unit, py311-unit, py311-integration

        [testenv]
        package = skip
        skip_install = true
        commands = python -c "print('{env_name}')"
        """,
    )
    data = json_config(run_tox(tmp_path, "config", "-f", "py311", "-k", "commands", "--format", "json"))
    assert set(data["env"]) == {"py311-unit", "py311-integration"}


def test_tox_ini_takes_precedence_over_setup_cfg(tmp_path):
    write(
        tmp_path,
        "setup.cfg",
        """
        [tox]
        env_list = from_setup_cfg
        [testenv:from_setup_cfg]
        package = skip
        skip_install = true
        description = setup cfg
        """,
    )
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = from_tox_ini
        [testenv:from_tox_ini]
        package = skip
        skip_install = true
        description = tox ini
        """,
    )
    result = run_tox(tmp_path, "list")
    assert "from_tox_ini -> tox ini" in result.stdout
    assert "from_setup_cfg" not in result.stdout


def test_pyproject_legacy_tox_ini_defines_environments(tmp_path):
    write(
        tmp_path,
        "pyproject.toml",
        '''
        [tool.tox]
        legacy_tox_ini = """
        [tox]
        env_list = legacy
        [testenv:legacy]
        package = skip
        skip_install = true
        description = legacy config
        """
        ''',
    )
    result = run_tox(tmp_path, "list")
    assert "legacy -> legacy config" in result.stdout


def test_tox_toml_env_run_base_values_are_inherited(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]
        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('base')"]]
        [env.lint]
        description = "lint"
        """,
    )
    data = json_config(run_tox(tmp_path, "config", "-k", "description", "commands", "package", "--format", "json"))
    assert data["env"]["lint"]["description"] == "lint"
    assert data["env"]["lint"]["commands"] == ["python -c print('base')"]
    assert data["env"]["lint"]["package"] == "skip"


def test_toml_labels_select_same_envs_in_list_and_config(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", "type", "docs"]
        labels.check = ["lint", "type"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.lint]
        labels = ["check"]
        [env.type]
        labels = ["check"]
        [env.docs]
        description = "docs"
        """,
    )
    listing = run_tox(tmp_path, "list", "-m", "check", "--no-desc")
    data = json_config(run_tox(tmp_path, "config", "-m", "check", "-k", "labels", "--format", "json"))
    assert listing.stdout.splitlines() == ["lint", "type"]
    assert set(data["env"]) == {"lint", "type"}


def test_toxfile_plugin_can_add_env_config_key(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["py"]
        [env.py]
        package = "skip"
        skip_install = true
        custom_value = "plugin-value"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    write(
        tmp_path,
        "toxfile.py",
        """
        from tox.plugin import impl

        @impl
        def tox_add_env_config(env_conf, state):
            env_conf.add_config(keys=['custom_value'], of_type=str, default='fallback', desc='custom')
        """,
    )
    data = json_config(run_tox(tmp_path, "config", "-k", "custom_value", "--format", "json"))
    assert data["env"]["py"]["custom_value"] == "plugin-value"


def test_depends_lists_dependency_edges(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", "type"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.lint]
        description = "lint"
        [env.type]
        description = "type"
        depends = ["lint"]
        """,
    )
    result = run_tox(tmp_path, "depends")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "type" in result.stdout
    assert "lint" in result.stdout
    assert result.stdout.index("lint") < result.stdout.index("type")


def test_list_no_desc_outputs_only_environment_names(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", "docs"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.lint]
        description = "lint"
        [env.docs]
        description = "docs"
        """,
    )
    result = run_tox(tmp_path, "list", "--no-desc")
    assert result.stdout.splitlines() == ["lint", "docs"]


def test_schema_command_includes_core_sections(tmp_path):
    write(tmp_path, "tox.toml", 'env_list = ["py"]\n[env.py]\npackage = "skip"\nskip_install = true\n')
    schema = json_config(run_tox(tmp_path, "schema"))
    assert schema["title"] == "tox configuration"
    assert "env" in schema["properties"]
    assert "env_list" in schema["properties"]


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


def test_module_invocation_prints_version(tmp_path):
    result = run_tox(tmp_path, "--version")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tox" in result.stdout.lower()


def test_public_version_is_nonempty_string():
    from tox import __version__

    assert isinstance(__version__, str)
    assert __version__


def test_pep723_runner_rejects_base_python_override(tmp_path):
    write(
        tmp_path,
        "script.py",
        """
        # /// script
        # requires-python = ">=3.11"
        # ///
        print("hello")
        """,
    )
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["py"]
        [env.py]
        runner = "virtualenv-pep-723"
        base_python = ["python3.11"]
        commands = [["python", "script.py"]]
        """,
    )
    result = run_tox(tmp_path, "run", "-e", "py")
    assert result.returncode != 0
    assert "base_python" in result.stdout + result.stderr


def test_ci_environment_variable_can_be_passed_to_command(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["py"]
        [env.py]
        package = "skip"
        skip_install = true
        pass_env = ["CI"]
        commands = [["python", "-c", "import os; print(os.environ.get('CI'))"]]
        """,
    )
    env = os.environ.copy()
    env["CI"] = "true"
    result = subprocess.run(
        [sys.executable, "-m", "tox", "--colored", "no", "run", "-e", "py"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "true" in result.stdout


def test_recreate_flag_recreates_environment(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["py"]
        [env.py]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('run')"]]
        """,
    )
    first = run_tox(tmp_path, "run", "-e", "py")
    second = run_tox(tmp_path, "run", "-r", "-e", "py")
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert (tmp_path / ".tox" / "py").exists()
