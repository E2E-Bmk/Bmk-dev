import json

from conftest import (
    create_tox_ini,
    create_tox_toml,
    create_pyproject_toml,
    create_setup_cfg,
    run_tox,
    run_tox_main,
    parse_json_output,
    write_file,
)


# ---------------------------------------------------------------------------
# main() and plugin surface
# ---------------------------------------------------------------------------


def test_main_version_returns_zero():
    code = run_tox_main(["--version"])
    assert code == 0


def test_main_help_returns_zero():
    code = run_tox_main(["--help"])
    assert code == 0


def test_list_subcommand_help_returns_zero():
    code = run_tox_main(["list", "--help"])
    assert code == 0


def test_config_subcommand_help_returns_zero():
    code = run_tox_main(["config", "--help"])
    assert code == 0


def test_plugin_name_constant_equals_tox():
    from tox.plugin import NAME

    assert NAME == "tox"


def test_impl_sets_tox_impl_attribute():
    from tox.plugin import impl

    @impl
    def tox_add_option(parser):
        pass

    assert getattr(tox_add_option, "tox_impl", None) is not None


# ---------------------------------------------------------------------------
# list subcommand
# ---------------------------------------------------------------------------


def test_list_shows_configured_environments(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = "run checks"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "list")
    assert result.returncode == 0
    assert "check" in result.stdout
    assert "run checks" in result.stdout


def test_list_no_desc_returns_names_only(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["verify", "audit"]
        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        [env.verify]
        description = "first"
        [env.audit]
        description = "second"
        """,
    )
    result = run_tox(tmp_path, "list", "--no-desc")
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert "verify" in lines
    assert "audit" in lines
    assert "first" not in result.stdout
    assert "second" not in result.stdout


# ---------------------------------------------------------------------------
# config subcommand
# ---------------------------------------------------------------------------


def test_config_accepts_valid_environment(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "config", "-e", "check")
    assert result.returncode == 0


def test_config_json_produces_valid_output(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = "json check"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "config", "-e", "check", "-k", "description", "--format", "json")
    data = parse_json_output(result)
    assert data["env"]["check"]["description"] == "json check"


def test_config_toml_format_returns_success(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = "toml check"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "config", "-e", "check", "-k", "description", "--format", "toml")
    assert result.returncode == 0
    assert "toml check" in result.stdout


def test_schema_returns_zero(tmp_path):
    result = run_tox(tmp_path, "schema")
    assert result.returncode == 0
    assert result.stdout.strip() != ""


# ---------------------------------------------------------------------------
# config discovery
# ---------------------------------------------------------------------------


def test_tox_ini_discovered_as_config(tmp_path):
    create_tox_ini(
        tmp_path,
        """
        [tox]
        env_list = verify

        [testenv:verify]
        package = skip
        skip_install = true
        description = ini source
        commands = python -c "print('ok')"
        """,
    )
    result = run_tox(tmp_path, "list")
    assert result.returncode == 0
    assert "verify" in result.stdout


def test_pyproject_native_toml_discovery(tmp_path):
    create_pyproject_toml(
        tmp_path,
        """
        [tool.tox]
        env_list = ["verify"]

        [tool.tox.env.verify]
        package = "skip"
        skip_install = true
        description = "native toml"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "list")
    assert result.returncode == 0
    assert "verify" in result.stdout


def test_setup_cfg_tox_section_discovery(tmp_path):
    create_setup_cfg(
        tmp_path,
        """
        [tox:tox]
        env_list = verify

        [testenv:verify]
        package = skip
        skip_install = true
        description = cfg source
        commands = python -c "print('ok')"
        """,
    )
    result = run_tox(tmp_path, "list")
    assert result.returncode == 0
    assert "verify" in result.stdout


# ---------------------------------------------------------------------------
# environment generation
# ---------------------------------------------------------------------------


def test_ini_factor_groups_expand_to_cartesian_product(tmp_path):
    create_tox_ini(
        tmp_path,
        r"""
        [tox]
        env_list = py{311,312}-feat{A,B}

        [testenv]
        package = skip
        skip_install = true
        commands = python -c "print('{env_name}')"
        """,
    )
    result = run_tox(tmp_path, "list", "--no-desc")
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert "py311-featA" in lines
    assert "py311-featB" in lines
    assert "py312-featA" in lines
    assert "py312-featB" in lines
    assert len(lines) == 4


def test_toml_product_generates_environments(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = [{ product = [{ prefix = "3.", start = 11, stop = 13 }, ["unit", "lint"]] }]
        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "list", "--no-desc")
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    expected = {"3.11-unit", "3.11-lint", "3.12-unit", "3.12-lint"}
    assert set(lines) == expected


# ---------------------------------------------------------------------------
# error semantics
# ---------------------------------------------------------------------------


def test_unknown_env_returns_nonzero(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "config", "-e", "nonexistent")
    assert result.returncode != 0


def test_pylock_deps_mutual_exclusion_error(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        deps = ["pytest"]
        pylock = "pylock.toml"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    write_file(tmp_path, "pylock.toml", "")
    result = run_tox(tmp_path, "config", "-e", "check")
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "pylock" in combined.lower()


# ---------------------------------------------------------------------------
# output modes and flags
# ---------------------------------------------------------------------------


def test_colored_no_disables_ansi_codes(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = "ansi test"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "list")
    assert result.returncode == 0
    assert "\x1b[" not in result.stdout
    assert "check" in result.stdout


def test_config_keyword_filter_limits_output_keys(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = "filtered output"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-e", "check", "-k", "description", "--format", "json")
    )
    assert data["env"]["check"] == {"description": "filtered output"}


def test_config_core_flag_adds_tox_section(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    without = parse_json_output(
        run_tox(tmp_path, "config", "-k", "env_list", "--format", "json")
    )
    with_core = parse_json_output(
        run_tox(tmp_path, "config", "--core", "-k", "env_list", "--format", "json")
    )
    assert "tox" not in without
    assert "tox" in with_core
    assert with_core["tox"]["env_list"] == ["check"]


def test_config_output_file_writes_no_stdout(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = "to file"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    outfile = tmp_path / "output.json"
    result = run_tox(
        tmp_path, "config", "-e", "check", "-k", "description",
        "--format", "json", "-o", str(outfile),
    )
    assert result.returncode == 0
    assert result.stdout == ""
    data = json.loads(outfile.read_text(encoding="utf-8"))
    assert data["env"]["check"]["description"] == "to file"


# ---------------------------------------------------------------------------
# substitutions and conditional values
# ---------------------------------------------------------------------------


def test_toml_conditional_selects_else_when_env_unset(tmp_path):
    create_tox_toml(
        tmp_path,
        '''
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = { replace = "if", condition = "env.SAMPLE_UNDEFINED_XYZ == 'yes'", then = "active mode", else = "fallback mode" }
        commands = [["python", "-c", "print('ok')"]]
        ''',
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-e", "check", "-k", "description", "--format", "json")
    )
    assert data["env"]["check"]["description"] == "fallback mode"


def test_env_var_substitution_uses_default_when_unset(tmp_path):
    create_tox_ini(
        tmp_path,
        """
        [tox]
        env_list = check

        [testenv:check]
        package = skip
        skip_install = true
        description = {env:SAMPLE_UNDEFINED_XYZ:fallback_val}
        commands = python -c "print('ok')"
        """,
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-e", "check", "-k", "description", "--format", "json")
    )
    assert data["env"]["check"]["description"] == "fallback_val"


def test_posargs_default_substituted_without_extra_args(tmp_path):
    create_tox_ini(
        tmp_path,
        """
        [tox]
        env_list = check

        [testenv:check]
        package = skip
        skip_install = true
        commands = python -c "print('{posargs:sample_default}')"
        """,
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-e", "check", "-k", "commands", "--format", "json")
    )
    command = data["env"]["check"]["commands"][0]
    assert "sample_default" in command


# ---------------------------------------------------------------------------
# label and factor selection
# ---------------------------------------------------------------------------


def test_label_m_flag_selects_labeled_environments(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check", "verify", "docs"]
        labels.quality = ["check", "verify"]
        [env_run_base]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        [env.check]
        labels = ["quality"]
        [env.verify]
        labels = ["quality"]
        [env.docs]
        description = "docs"
        """,
    )
    result = run_tox(tmp_path, "list", "-m", "quality", "--no-desc")
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert "check" in lines
    assert "verify" in lines
    assert "docs" not in lines


def test_factor_f_flag_filters_environments(tmp_path):
    create_tox_ini(
        tmp_path,
        r"""
        [tox]
        env_list = py311-unit, py312-unit, py312-integ

        [testenv]
        package = skip
        skip_install = true
        commands = python -c "print('{env_name}')"
        """,
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-f", "py312", "-k", "commands", "--format", "json")
    )
    assert set(data["env"]) == {"py312-unit", "py312-integ"}


# ---------------------------------------------------------------------------
# set_env / boolean preservation
# ---------------------------------------------------------------------------


def test_set_env_visible_in_config_json(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        set_env.SAMPLE_TAG = "beta"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-e", "check", "-k", "set_env", "--format", "json")
    )
    assert data["env"]["check"]["set_env"]["SAMPLE_TAG"] == "beta"


def test_config_json_preserves_boolean_values(tmp_path):
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-e", "check", "-k", "skip_install", "--format", "json")
    )
    assert data["env"]["check"]["skip_install"] is True
