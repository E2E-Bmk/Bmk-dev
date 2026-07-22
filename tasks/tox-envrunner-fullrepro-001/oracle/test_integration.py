from conftest import (
    create_tox_ini,
    create_tox_toml,
    create_pyproject_toml,
    create_setup_cfg,
    run_tox,
    parse_json_output,
    write_file,
)


# ===========================================================================
# Cross-View Invariant tests (CVI 1–10)
# ===========================================================================


def test_cvi1_list_name_matches_run_config_exec(tmp_path):
    """CVI-1: name visible in list is accepted by run -e, config -e, exec -e."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["verify"]
        [env.verify]
        package = "skip"
        skip_install = true
        description = "verification suite"
        commands = [["python", "-c", "print('VERIFY_CMD')"]]
        """,
    )
    listing = run_tox(tmp_path, "list")
    config = run_tox(tmp_path, "config", "-e", "verify", "-k", "description", "--format", "json")
    run_result = run_tox(tmp_path, "run", "-e", "verify", "--skip-pkg-install")
    exec_result = run_tox(
        tmp_path, "exec", "-e", "verify", "--skip-pkg-install",
        "--", "python", "-c", "print('EXEC_OK')",
    )

    assert listing.returncode == 0
    assert "verify" in listing.stdout

    data = parse_json_output(config)
    assert data["env"]["verify"]["description"] == "verification suite"

    assert run_result.returncode == 0
    assert "VERIFY_CMD" in run_result.stdout

    assert exec_result.returncode == 0
    assert "EXEC_OK" in exec_result.stdout


def test_cvi2_config_deps_used_during_run(tmp_path):
    """CVI-2: deps shown by config are installed during run."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["verify"]
        [env.verify]
        package = "skip"
        skip_install = true
        deps = ["pip"]
        commands = [["python", "-c", "import pip; print('DEPS_OK')"]]
        """,
    )
    data = parse_json_output(
        run_tox(tmp_path, "config", "-e", "verify", "-k", "deps", "--format", "json")
    )
    assert "pip" in str(data["env"]["verify"]["deps"])

    result = run_tox(tmp_path, "run", "-e", "verify")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DEPS_OK" in result.stdout


def test_cvi3_json_toml_formats_expose_same_values(tmp_path):
    """CVI-3: JSON and TOML config formats show the same resolved value."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["verify"]
        [env.verify]
        package = "skip"
        skip_install = true
        description = "sample verification"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    json_result = run_tox(
        tmp_path, "config", "-e", "verify", "-k", "description", "--format", "json",
    )
    toml_result = run_tox(
        tmp_path, "config", "-e", "verify", "-k", "description", "--format", "toml",
    )
    json_data = parse_json_output(json_result)
    desc = json_data["env"]["verify"]["description"]
    assert desc == "sample verification"

    assert toml_result.returncode == 0
    assert desc in toml_result.stdout


def test_cvi4_depends_ordering_honored_in_run(tmp_path):
    """CVI-4: depends ordering consistent between depends subcommand and run."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["build", "analyze"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.build]
        commands = [["python", "-c", "print('BUILD_DONE')"]]
        [env.analyze]
        depends = ["build"]
        commands = [["python", "-c", "print('ANALYZE_DONE')"]]
        """,
    )
    depends = run_tox(tmp_path, "depends")
    assert depends.returncode == 0
    assert depends.stdout.index("build") < depends.stdout.index("analyze")

    result = run_tox(tmp_path, "run", "-e", "build,analyze", "--skip-pkg-install")
    assert result.returncode == 0
    assert result.stdout.index("BUILD_DONE") < result.stdout.index("ANALYZE_DONE")


def test_cvi5_env_var_composition_in_execution(tmp_path):
    """CVI-5: pass_env + set_env from config match variables in execution."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["verify"]
        [env.verify]
        package = "skip"
        skip_install = true
        pass_env = ["SAMPLE_HOST_VAR"]
        set_env.SAMPLE_CONFIG_VAR = "configured"
        commands = [["python", "-c", "import os; print('HOST=' + os.environ.get('SAMPLE_HOST_VAR', 'MISSING')); print('CFG=' + os.environ.get('SAMPLE_CONFIG_VAR', 'MISSING'))"]]
        """,
    )
    data = parse_json_output(
        run_tox(
            tmp_path, "config", "-e", "verify",
            "-k", "pass_env", "set_env", "--format", "json",
        )
    )
    assert "SAMPLE_HOST_VAR" in data["env"]["verify"]["pass_env"]
    assert data["env"]["verify"]["set_env"]["SAMPLE_CONFIG_VAR"] == "configured"

    result = run_tox(
        tmp_path, "run", "-e", "verify", "--skip-pkg-install",
        extra_env={"SAMPLE_HOST_VAR": "from_host"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "HOST=from_host" in result.stdout
    assert "CFG=configured" in result.stdout


def test_cvi6_package_mode_config_reflects_packaging(tmp_path):
    """CVI-6: package mode determines package_env in config and TOX_PACKAGE in run."""
    create_pyproject_toml(
        tmp_path,
        """
        [build-system]
        requires = ["setuptools>=64"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "sample-lib"
        version = "0.1.0"
        """,
    )
    (tmp_path / "sample_lib").mkdir()
    write_file(tmp_path, "sample_lib/__init__.py", "")
    create_tox_toml(
        tmp_path,
        """
        env_list = ["verify"]
        [env.verify]
        commands = [["python", "-c", "import os; v=os.environ.get('TOX_PACKAGE','ABSENT'); print('PKG=' + v)"]]
        """,
    )

    data = parse_json_output(
        run_tox(
            tmp_path, "config", "-e", "verify",
            "-k", "package", "package_env", "--format", "json",
        )
    )
    assert data["env"]["verify"]["package"] == "sdist"
    assert data["env"]["verify"]["package_env"] == ".pkg"

    result = run_tox(tmp_path, "run", "-e", "verify")
    assert result.returncode == 0, result.stdout + result.stderr
    found_pkg = False
    for line in result.stdout.splitlines():
        if "PKG=" in line:
            assert "ABSENT" not in line
            found_pkg = True
            break
    assert found_pkg, "TOX_PACKAGE was not printed"


def test_cvi7_posargs_visible_only_in_commands(tmp_path):
    """CVI-7: positional args change commands but not unrelated keys like description."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        description = "check task"
        commands = [["python", "-c", "print('ok')", { replace = "posargs", default = ["fallback_arg"], extend = true }]]
        """,
    )
    data = parse_json_output(
        run_tox(
            tmp_path, "config", "-e", "check",
            "-k", "description", "commands", "--format", "json",
            "--", "injected_arg",
        )
    )
    assert data["env"]["check"]["description"] == "check task"
    command = data["env"]["check"]["commands"][0]
    assert "injected_arg" in command
    assert "fallback_arg" not in command


def test_cvi8_labels_consistent_across_list_and_run_m(tmp_path):
    """CVI-8: list -m and run -m select the same environments."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["lint", "format", "docs"]
        labels.quality = ["lint", "format"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.lint]
        labels = ["quality"]
        commands = [["python", "-c", "print('LINT_OK')"]]
        [env.format]
        labels = ["quality"]
        commands = [["python", "-c", "print('FORMAT_OK')"]]
        [env.docs]
        commands = [["python", "-c", "print('DOCS_OK')"]]
        """,
    )
    listing = run_tox(tmp_path, "list", "-m", "quality", "--no-desc")
    assert set(listing.stdout.strip().splitlines()) == {"lint", "format"}

    result = run_tox(tmp_path, "run", "-m", "quality", "--skip-pkg-install")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "LINT_OK" in result.stdout
    assert "FORMAT_OK" in result.stdout
    assert "DOCS_OK" not in result.stdout


def test_cvi9_unused_key_visible_in_config(tmp_path):
    """CVI-9: an unused/misplaced config key is surfaced in config output."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        stale_setting = "leftover"
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    result = run_tox(tmp_path, "config")
    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "stale_setting" in combined


def test_cvi10_exit_status_matches_env_outcomes(tmp_path):
    """CVI-10: all-pass → 0, any-fail → nonzero."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["alpha", "bravo"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.alpha]
        commands = [["python", "-c", "print('A')"]]
        [env.bravo]
        commands = [["python", "-c", "print('B')"]]
        """,
    )
    ok = run_tox(tmp_path, "run", "--skip-pkg-install")
    assert ok.returncode == 0

    create_tox_toml(
        tmp_path,
        """
        env_list = ["good", "bad"]
        [env.good]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('GOOD')"]]
        [env.bad]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "raise SystemExit(3)"]]
        """,
    )
    fail = run_tox(tmp_path, "run", "--skip-pkg-install")
    assert fail.returncode != 0


# ===========================================================================
# Seam tests — composition boundaries
# ===========================================================================


def test_seam_discovery_tox_ini_over_tox_toml(tmp_path):
    """Seam: config interaction — tox.ini discovery precedence ↔ list and run use ini env."""
    create_tox_ini(
        tmp_path,
        """
        [tox]
        env_list = from_ini

        [testenv:from_ini]
        package = skip
        skip_install = true
        description = ini source
        commands = python -c "print('INI_CMD')"
        """,
    )
    create_tox_toml(
        tmp_path,
        """
        env_list = ["from_toml"]
        [env.from_toml]
        package = "skip"
        skip_install = true
        description = "toml source"
        commands = [["python", "-c", "print('TOML_CMD')"]]
        """,
    )
    listing = run_tox(tmp_path, "list")
    assert listing.returncode == 0
    assert "from_ini" in listing.stdout
    assert "from_toml" not in listing.stdout

    result = run_tox(tmp_path, "run", "-e", "from_ini", "--skip-pkg-install")
    assert result.returncode == 0
    assert "INI_CMD" in result.stdout


def test_seam_env_run_base_inheritance_in_config_and_run(tmp_path):
    """Seam: config interaction — env_run_base inheritance ↔ config JSON and run output."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env_run_base]
        package = "skip"
        skip_install = true
        description = "base template"
        commands = [["python", "-c", "print('BASE_CMD')"]]
        [env.check]
        description = "check override"
        """,
    )
    data = parse_json_output(
        run_tox(
            tmp_path, "config", "-e", "check",
            "-k", "description", "commands", "package", "--format", "json",
        )
    )
    env = data["env"]["check"]
    assert env["description"] == "check override"
    assert "BASE_CMD" in env["commands"][0]
    assert env["package"] == "skip"

    result = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert result.returncode == 0
    assert "BASE_CMD" in result.stdout


def test_seam_dash_prefix_ignores_failure(tmp_path):
    """Seam: error propagation — dash-prefixed command failure ↔ env still passes and next command runs."""
    create_tox_ini(
        tmp_path,
        """
        [tox]
        env_list = check

        [testenv:check]
        package = skip
        skip_install = true
        commands =
            - python -c "raise SystemExit(5)"
            python -c "print('AFTER_IGNORE')"
        """,
    )
    result = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "AFTER_IGNORE" in result.stdout


def test_seam_bang_prefix_inverts_success(tmp_path):
    """Seam: error propagation — bang-prefixed nonzero exit ↔ treated as success and next command runs."""
    create_tox_ini(
        tmp_path,
        """
        [tox]
        env_list = check

        [testenv:check]
        package = skip
        skip_install = true
        commands =
            ! python -c "raise SystemExit(7)"
            python -c "print('AFTER_INVERT')"
        """,
    )
    result = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "AFTER_INVERT" in result.stdout


def test_seam_recreate_forces_fresh_env(tmp_path):
    """Seam: lifecycle crossing — --recreate ↔ env directory deletion and recreation."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('RUN_OK')"]]
        """,
    )
    first = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert first.returncode == 0

    env_dir = tmp_path / ".tox" / "check"
    sentinel = env_dir / "test_sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")

    reuse = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert reuse.returncode == 0
    assert sentinel.exists()

    recreated = run_tox(tmp_path, "run", "-r", "-e", "check", "--skip-pkg-install")
    assert recreated.returncode == 0
    assert not sentinel.exists()


def test_seam_skip_install_runs_commands_without_build(tmp_path):
    """Seam: lifecycle crossing — --skip-pkg-install ↔ commands without packaging."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        commands = [["python", "-c", "print('COMMANDS_RAN')"]]
        """,
    )
    result = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "COMMANDS_RAN" in result.stdout


def test_seam_parallel_runs_environments(tmp_path):
    """Seam: protocol handoff — run-parallel ↔ multiple env completion."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["alpha", "bravo"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.alpha]
        commands = [["python", "-c", "print('ALPHA_DONE')"]]
        [env.bravo]
        commands = [["python", "-c", "print('BRAVO_DONE')"]]
        """,
    )
    result = run_tox(
        tmp_path, "run-parallel", "--parallel", "2",
        "-e", "alpha,bravo", "--skip-pkg-install",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "alpha" in combined.lower()
    assert "bravo" in combined.lower()


def test_seam_fail_fast_stops_scheduling(tmp_path):
    """Seam: error propagation — fail_fast ↔ later envs not scheduled after failure."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["fail_first", "pass_second"]
        fail_fast = true

        [env.fail_first]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "raise SystemExit(1)"]]

        [env.pass_second]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('SECOND_RAN')"]]
        """,
    )
    result = run_tox(tmp_path, "run", "--skip-pkg-install")
    assert result.returncode != 0
    assert "SECOND_RAN" not in result.stdout


def test_seam_depends_delays_but_does_not_add_unselected(tmp_path):
    """Seam: config interaction — depends ordering ↔ selected env run sequence only."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["build", "analyze"]
        [env_run_base]
        package = "skip"
        skip_install = true
        [env.build]
        commands = [["python", "-c", "print('BUILD_CMD')"]]
        [env.analyze]
        depends = ["build"]
        commands = [["python", "-c", "print('ANALYZE_CMD')"]]
        """,
    )
    only_analyze = run_tox(tmp_path, "run", "-e", "analyze", "--skip-pkg-install")
    assert only_analyze.returncode == 0, only_analyze.stdout + only_analyze.stderr
    assert "ANALYZE_CMD" in only_analyze.stdout
    assert "BUILD_CMD" not in only_analyze.stdout

    both = run_tox(tmp_path, "run", "-e", "build,analyze", "--skip-pkg-install")
    assert both.returncode == 0
    assert both.stdout.index("BUILD_CMD") < both.stdout.index("ANALYZE_CMD")


def test_seam_exec_runs_only_given_command(tmp_path):
    """Seam: protocol handoff — tox exec ↔ ad-hoc command instead of configured commands."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('CONFIGURED')"]]
        """,
    )
    result = run_tox(
        tmp_path, "exec", "-e", "check", "--skip-pkg-install",
        "--", "python", "-c", "print('EXEC_ONLY')",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EXEC_ONLY" in result.stdout
    assert "CONFIGURED" not in result.stdout


def test_seam_command_failure_skips_later_commands(tmp_path):
    """Seam: error propagation — failed command ↔ subsequent commands skipped in env."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [
            ["python", "-c", "raise SystemExit(3)"],
            ["python", "-c", "print('LATER_CMD')"],
        ]
        """,
    )
    result = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert result.returncode != 0
    assert "LATER_CMD" not in result.stdout


def test_seam_parallel_failure_nonzero(tmp_path):
    """Seam: error propagation — parallel env failure ↔ nonzero exit status."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["good", "bad"]
        [env.good]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('GOOD')"]]
        [env.bad]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "raise SystemExit(2)"]]
        """,
    )
    result = run_tox(
        tmp_path, "run-parallel", "--parallel", "2",
        "-e", "good,bad", "--skip-pkg-install",
    )
    assert result.returncode != 0


def test_seam_generative_envs_factor_filter_and_config(tmp_path):
    """Seam: config interaction — generative env list + factor filter ↔ list and config agreement."""
    create_tox_ini(
        tmp_path,
        r"""
        [tox]
        env_list = py{311,312}-unit, lint

        [testenv]
        package = skip
        skip_install = true
        description = run {env_name}
        commands = python -c "print('{env_name}')"

        [testenv:lint]
        description = lint check
        commands = python -c "print('lint')"
        """,
    )
    listing = run_tox(tmp_path, "list", "--no-desc")
    assert listing.returncode == 0
    lines = listing.stdout.strip().splitlines()
    assert "py311-unit" in lines
    assert "py312-unit" in lines
    assert "lint" in lines

    data = parse_json_output(
        run_tox(
            tmp_path, "config", "-f", "py312",
            "-k", "description", "--format", "json",
        )
    )
    assert set(data["env"]) == {"py312-unit"}
    assert data["env"]["py312-unit"]["description"] == "run py312-unit"


def test_seam_toxfile_plugin_adds_config_key(tmp_path):
    """Seam: config interaction — toxfile plugin ↔ custom key visible in config JSON."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        audit_level = "strict"
        commands = [["python", "-c", "print('ok')"]]
        """,
    )
    write_file(
        tmp_path,
        "toxfile.py",
        """
        from tox.plugin import impl

        @impl
        def tox_add_env_config(env_conf, state):
            env_conf.add_config(
                keys=["audit_level"],
                of_type=str,
                default="normal",
                desc="audit strictness level",
            )
        """,
    )
    data = parse_json_output(
        run_tox(
            tmp_path, "config", "-e", "check",
            "-k", "audit_level", "--format", "json",
        )
    )
    assert data["env"]["check"]["audit_level"] == "strict"


def test_seam_repeated_run_reuses_recreate_replaces(tmp_path):
    """Seam: lifecycle crossing — repeated run reuse ↔ -r recreate removes sentinel."""
    create_tox_toml(
        tmp_path,
        """
        env_list = ["check"]
        [env.check]
        package = "skip"
        skip_install = true
        commands = [["python", "-c", "print('RUN_OK')"]]
        """,
    )
    first = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert first.returncode == 0

    sentinel = tmp_path / ".tox" / "check" / "sentinel.txt"
    sentinel.write_text("marker", encoding="utf-8")

    second = run_tox(tmp_path, "run", "-e", "check", "--skip-pkg-install")
    assert second.returncode == 0
    assert sentinel.read_text(encoding="utf-8") == "marker"

    recreated = run_tox(tmp_path, "run", "-r", "-e", "check", "--skip-pkg-install")
    assert recreated.returncode == 0
    assert not sentinel.exists()


def test_seam_pyproject_native_over_legacy(tmp_path):
    """Seam: config interaction — native [tool.tox] ↔ precedence over legacy_tox_ini."""
    create_pyproject_toml(
        tmp_path,
        '''
        [tool.tox]
        env_list = ["native_env"]
        legacy_tox_ini = """
        [tox]
        env_list = legacy_env

        [testenv:legacy_env]
        package = skip
        skip_install = true
        description = legacy source
        commands = python -c "print('LEGACY')"
        """

        [tool.tox.env.native_env]
        package = "skip"
        skip_install = true
        description = "native source"
        commands = [["python", "-c", "print('NATIVE')"]]
        ''',
    )
    listing = run_tox(tmp_path, "list")
    assert listing.returncode == 0
    assert "native_env" in listing.stdout
    assert "legacy_env" not in listing.stdout

    data = parse_json_output(
        run_tox(
            tmp_path, "config", "-e", "native_env",
            "-k", "description", "--format", "json",
        )
    )
    assert data["env"]["native_env"]["description"] == "native source"
