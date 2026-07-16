# Spec2Repo oracle - integration tests for tox-envrunner-fullrepro-001
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


def test_tox_ini_is_discovered_before_tox_toml(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = ini_env

        [testenv:ini_env]
        package = skip
        skip_install = true
        description = from ini
        commands = python -c "print('ini')"
        """,
    )
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["toml_env"]

        [env.toml_env]
        package = "skip"
        skip_install = true
        description = "from toml"
        commands = [["python", "-c", "print('toml')"]]
        """,
    )

    result = run_tox(tmp_path, "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "ini_env -> from ini" in result.stdout
    assert "toml_env" not in result.stdout


def test_pyproject_native_toml_is_preferred_over_legacy_tox_ini(tmp_path):
    write(
        tmp_path,
        "pyproject.toml",
        '''
        [tool.tox]
        env_list = ["native"]
        legacy_tox_ini = """
        [tox]
        env_list = legacy

        [testenv:legacy]
        package = skip
        skip_install = true
        description = legacy env
        commands = python -c "print('legacy')"
        """

        [tool.tox.env.native]
        package = "skip"
        skip_install = true
        description = "native env"
        commands = [["python", "-c", "print('native')"]]
        ''',
    )

    listing = run_tox(tmp_path, "list")
    config = run_tox(tmp_path, "config", "-e", "native", "-k", "description", "commands", "--format", "json")

    assert listing.returncode == 0, listing.stdout + listing.stderr
    assert "native -> native env" in listing.stdout
    assert "legacy" not in listing.stdout
    data = load_json_output(config)
    assert data["env"]["native"] == {
        "description": "native env",
        "commands": ["python -c print('native')"],
    }


def test_pyproject_legacy_tox_ini_is_used_without_native_env_table(tmp_path):
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
        description = legacy env
        commands = python -c "print('legacy')"
        """
        ''',
    )

    listing = run_tox(tmp_path, "list")
    config = run_tox(tmp_path, "config", "-e", "legacy", "-k", "description", "commands", "--format", "json")

    assert listing.returncode == 0, listing.stdout + listing.stderr
    assert "legacy -> legacy env" in listing.stdout
    data = load_json_output(config)
    assert data["env"]["legacy"]["description"] == "legacy env"
    assert data["env"]["legacy"]["commands"] == ["python -c print('legacy')"]


def test_ini_generative_env_list_expands_and_substitutes_env_name(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        r'''
        [tox]
        env_list = py{310,311}-django{42,50}, lint

        [testenv]
        package = skip
        skip_install = true
        description = run {env_name}
        commands = python -c "print('{env_name}')"

        [testenv:lint]
        description = lint commands
        commands = python -c "print('lint')"
        ''',
    )

    listing = run_tox(tmp_path, "list", "--no-desc")
    config = run_tox(
        tmp_path,
        "config",
        "-f",
        "django42",
        "-k",
        "description",
        "commands",
        "--format",
        "json",
    )

    assert listing.returncode == 0, listing.stdout + listing.stderr
    assert listing.stdout.splitlines() == [
        "py310-django42",
        "py310-django50",
        "py311-django42",
        "py311-django50",
        "lint",
    ]
    data = load_json_output(config)
    assert set(data["env"]) == {"py310-django42", "py311-django42"}
    assert data["env"]["py310-django42"]["description"] == "run py310-django42"
    assert data["env"]["py310-django42"]["commands"] == ["python -c print('py310-django42')"]


def test_label_selection_matches_between_list_and_config(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", "type", "docs"]
        labels.check = ["lint", "type"]

        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('base')"]]

        [env.lint]
        description = "lint only"
        labels = ["check"]

        [env.type]
        description = "type check"
        labels = ["check"]

        [env.docs]
        description = "docs build"
        """,
    )

    listing = run_tox(tmp_path, "list", "-m", "check")
    config = run_tox(tmp_path, "config", "-m", "check", "-k", "description", "--format", "json")

    assert listing.returncode == 0, listing.stdout + listing.stderr
    assert "lint -> lint only" in listing.stdout
    assert "type -> type check" in listing.stdout
    assert "docs" not in listing.stdout
    data = load_json_output(config)
    assert data["env"] == {
        "lint": {"description": "lint only"},
        "type": {"description": "type check"},
    }


def test_config_json_preserves_native_types_and_inherited_values(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", "type"]

        [env_run_base]
        package = "skip"
        skip_install = true
        description = "base command runner"
        commands = [["python", "-c", "print('base')"]]

        [env.lint]
        description = "lint only"
        commands = [["python", "-c", "print('lint')"]]

        [env.type]
        description = "type check"
        depends = ["lint"]
        labels = ["check"]
        """,
    )

    result = run_tox(
        tmp_path,
        "config",
        "-e",
        "type",
        "-k",
        "description",
        "skip_install",
        "package",
        "commands",
        "depends",
        "labels",
        "--format",
        "json",
    )

    data = load_json_output(result)
    env = data["env"]["type"]
    assert env["description"] == "type check"
    assert env["skip_install"] is True
    assert env["package"] == "skip"
    assert env["commands"] == ["python -c print('base')"]
    assert env["depends"] == ["lint"]
    assert env["labels"] == ["check"]


def test_schema_command_outputs_json_schema_for_tox_configuration(tmp_path):
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

    result = run_tox(tmp_path, "schema")

    schema = load_json_output(result)
    assert schema["title"] == "tox configuration"
    assert schema["type"] == "object"
    assert "env_list" in schema["properties"]
    assert "env_run_base" in schema["properties"]
    assert "env" in schema["properties"]


def test_depends_reports_dependency_order_for_default_environment_set(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", "type", "docs"]

        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('base')"]]

        [env.lint]
        description = "lint"

        [env.type]
        description = "type"
        depends = ["lint"]

        [env.docs]
        description = "docs"
        depends = ["type"]
        """,
    )

    result = run_tox(tmp_path, "depends")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.index("lint") < result.stdout.index("type") < result.stdout.index("docs")
    assert "type\n      lint" in result.stdout
    assert "docs\n      type" in result.stdout


def test_mutually_exclusive_no_capture_and_result_json_fails_before_writing_json(tmp_path):
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
    result_json = tmp_path / "result.json"

    result = run_tox(tmp_path, "config", "-i", "--result-json", str(result_json))

    assert result.returncode != 0
    assert not result_json.exists()
    combined = result.stdout + result.stderr
    assert "--no-capture" in combined
    assert "--result-json" in combined


def test_config_option_selects_explicit_tox_file(tmp_path):
    explicit = write(
        tmp_path,
        "custom.ini",
        """
        [tox]
        env_list = custom

        [testenv:custom]
        package = skip
        skip_install = true
        description = explicit config
        commands = python -c "print('custom')"
        """,
    )
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = default

        [testenv:default]
        package = skip
        skip_install = true
        description = default config
        commands = python -c "print('default')"
        """,
    )

    result = run_tox(tmp_path, "-c", str(explicit), "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "custom -> explicit config" in result.stdout
    assert "default -> default config" not in result.stdout


def test_setup_cfg_is_used_when_tox_ini_is_absent(tmp_path):
    write(
        tmp_path,
        "setup.cfg",
        """
        [tox:tox]
        env_list = cfg

        [testenv:cfg]
        package = skip
        skip_install = true
        description = from setup cfg
        commands = python -c "print('cfg')"
        """,
    )

    result = run_tox(tmp_path, "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "cfg -> from setup cfg" in result.stdout


def test_tox_toml_is_used_when_earlier_config_files_are_absent(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["tomlonly"]

        [env.tomlonly]
        package = "skip"
        skip_install = true
        description = "from tox toml"
        commands = [["python", "-c", "print('tomlonly')"]]
        """,
    )

    result = run_tox(tmp_path, "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "tomlonly -> from tox toml" in result.stdout


def test_toml_product_env_list_expands_to_cartesian_product(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = [{ product = [{ prefix = "3.", start = 10, stop = 12 }, ["django42", "django50"]] }]

        [env_run_base]
        package = "skip"
        skip_install = true
        description = "generated"
        commands = [["python", "-c", "print('generated')"]]
        """,
    )

    result = run_tox(tmp_path, "list", "--no-desc")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        "3.10-django42",
        "3.10-django50",
        "3.11-django42",
        "3.11-django50",
        "3.12-django42",
        "3.12-django50",
    ]


def test_env_base_template_generates_factor_environments(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]

        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('base')"]]

        [env_base.test]
        factors = ["py310", "py311"]
        description = "test {env_name}"

        [env.lint]
        description = "lint"
        """,
    )

    result = run_tox(tmp_path, "list")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "test-py310 -> test test-py310" in result.stdout
    assert "test-py311 -> test test-py311" in result.stdout
    assert "test ->" not in result.stdout


def test_toml_conditional_replacement_uses_else_branch_when_env_is_missing(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        '''
        env_list = ["lint"]

        [env.lint]
        package = "skip"
        skip_install = true
        description = { replace = "if", condition = "env.TOX_RETRO_MODE == 'ci'", then = "ci mode", else = "local mode" }
        commands = [["python", "-c", "print('lint')"]]
        ''',
    )

    result = run_tox(tmp_path, "config", "-e", "lint", "-k", "description", "--format", "json")

    data = load_json_output(result)
    assert data["env"]["lint"]["description"] == "local mode"


def test_posargs_are_rendered_only_in_commands(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]

        [env.lint]
        package = "skip"
        skip_install = true
        description = "lint"
        commands = [["python", "-c", "print('args')", { replace = "posargs", default = ["default"], extend = true }]]
        """,
    )

    result = run_tox(tmp_path, "config", "-e", "lint", "-k", "description", "commands", "--format", "json", "--", "custom")

    data = load_json_output(result)
    assert data["env"]["lint"]["description"] == "lint"
    assert data["env"]["lint"]["commands"] == ["python -c print('args') custom"]


def test_set_env_pass_env_and_disallow_pass_env_are_visible_in_config(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]

        [env.lint]
        package = "skip"
        skip_install = true
        pass_env = ["RETRO_*"]
        disallow_pass_env = ["RETRO_SECRET"]
        set_env.RETRO_MODE = "configured"
        commands = [["python", "-c", "print('env')"]]
        """,
    )

    result = run_tox(
        tmp_path,
        "config",
        "-e",
        "lint",
        "-k",
        "pass_env",
        "disallow_pass_env",
        "set_env",
        "--format",
        "json",
    )

    data = load_json_output(result)["env"]["lint"]
    assert "RETRO_*" in data["pass_env"]
    assert data["disallow_pass_env"] == ["RETRO_SECRET"]
    assert data["set_env"]["RETRO_MODE"] == "configured"


def test_package_modes_remain_visible_in_verbose_configuration(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["wheel", "editable", "skip"]

        [env_run_base]
        commands = [["python", "-c", "print('package')"]]

        [env.wheel]
        package = "wheel"
        skip_install = true

        [env.editable]
        package = "editable"
        skip_install = true

        [env.skip]
        package = "skip"
        skip_install = true
        """,
    )

    result = run_tox(tmp_path, "config", "-k", "package", "-vv")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "wheel" in result.stdout
    assert "editable" in result.stdout
    assert "skip" in result.stdout


def test_explicit_package_environment_is_listed_separately(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", ".pkg"]

        [env_run_base]
        skip_install = true
        description = "run base"
        commands = [["python", "-c", "print('run')"]]

        [env_pkg_base]
        description = "package base"
        commands = [["python", "-c", "print('pkg')"]]

        [env.lint]
        package = "skip"
        description = "lint"
        """,
    )

    listing = run_tox(tmp_path, "list")
    run_result = run_tox(tmp_path, "config", "-e", "lint", "-k", "description", "commands", "--format", "json")

    assert listing.returncode == 0, listing.stdout + listing.stderr
    assert ".pkg" in listing.stdout
    assert ".pkg -> run base" in listing.stdout
    assert load_json_output(run_result)["env"]["lint"]["description"] == "lint"
    assert load_json_output(run_result)["env"]["lint"]["commands"] == ["python -c print('run')"]


def test_run_with_skip_pkg_install_executes_configured_command(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]

        [env.lint]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('RETRO_RUN_OK')"]]
        """,
    )

    result = run_tox(tmp_path, "run", "-e", "lint", "--skip-pkg-install")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "RETRO_RUN_OK" in result.stdout


def test_command_prefixes_ignore_and_invert_failures(tmp_path):
    write(
        tmp_path,
        "tox.ini",
        """
        [tox]
        env_list = prefixed

        [testenv:prefixed]
        package = skip
        skip_install = true
        commands =
            - python -c "raise SystemExit(7)"
            ! python -c "raise SystemExit(3)"
            python -c "print('after prefixes')"
        """,
    )

    result = run_tox(tmp_path, "run", "-e", "prefixed", "--skip-pkg-install")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "after prefixes" in result.stdout


def test_exec_runs_supplied_command_without_configured_commands(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint"]

        [env.lint]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('CONFIGURED_COMMAND')"]]
        """,
    )

    result = run_tox(tmp_path, "exec", "-e", "lint", "--skip-pkg-install", "--", "python", "-c", "print('EXEC_COMMAND')")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "EXEC_COMMAND" in result.stdout
    assert "CONFIGURED_COMMAND" not in result.stdout


def test_failing_command_returns_nonzero_and_skips_later_commands(tmp_path):
    marker = tmp_path / "later.txt"
    write(
        tmp_path,
        "tox.toml",
        f"""
        env_list = ["fail"]

        [env.fail]
        package = "skip"
        skip_install = true
        commands = [
            ["python", "-c", "raise SystemExit(5)"],
            ["python", "-c", "from pathlib import Path; Path({str(marker)!r}).write_text('ran')"],
        ]
        """,
    )

    result = run_tox(tmp_path, "run", "-e", "fail", "--skip-pkg-install")

    assert result.returncode != 0
    assert not marker.exists()


def test_skip_missing_interpreters_reports_skip_for_missing_python(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["missing"]
        skip_missing_interpreters = true

        [env.missing]
        base_python = ["python9.99"]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('missing')"]]
        """,
    )

    result = run_tox(tmp_path, "run", "-e", "missing", "--skip-pkg-install")

    assert result.returncode != 0
    assert "skip" in result.stdout.lower() or "skip" in result.stderr.lower()


def test_depends_does_not_add_unselected_dependencies(tmp_path):
    write(
        tmp_path,
        "tox.toml",
        """
        env_list = ["lint", "coverage"]

        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('base')"]]

        [env.lint]
        description = "lint"

        [env.coverage]
        description = "coverage"
        depends = ["lint"]
        """,
    )

    result = run_tox(tmp_path, "depends")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "coverage" in result.stdout
    assert "lint" in result.stdout


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


def test_module_invocation_prints_version(tmp_path):
    result = run_tox(tmp_path, "--version")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tox" in result.stdout.lower()


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
