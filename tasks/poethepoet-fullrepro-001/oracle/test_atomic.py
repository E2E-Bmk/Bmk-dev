from __future__ import annotations

import io


def test_public_package_exposes_version_and_main():
    import poethepoet

    assert isinstance(poethepoet.__version__, str)
    assert callable(poethepoet.main)


def test_iter_tasks_returns_public_task_names(poe_project):
    from poethepoet import iter_tasks

    project = poe_project(
        """
        [tool.poe.tasks]
        alpha = "echo alpha"
        _hidden = "echo hidden"
        beta.help = "Beta task"
        beta.cmd = "echo beta"
        """
    )
    assert list(iter_tasks(str(project))) == ["alpha", "beta"]


def test_builtin_list_tasks_excludes_hidden_tasks(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        first = "echo first"
        _secret = "echo secret"
        second = "echo second"
        """
    )
    result = poe_runner(project, "_list_tasks", str(project))
    assert result.returncode == 0
    assert result.plain_lines == ["first second"]


def test_string_task_runs_as_command_and_appends_free_args(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        probe = "${PYTHON} runner.py argv fixed"
        """
    )
    result = poe_runner(project, "probe", "tail", "--flag")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["fixed", "tail", "--flag"]


def test_command_quotes_keep_whitespace_inside_one_argument(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        quote.cmd = "${PYTHON} runner.py argv 'two words' plain"
        """
    )
    result = poe_runner(project, "quote")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["two words", "plain"]


def test_command_environment_default_operator_supplies_fallback(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        region.cmd = "${PYTHON} runner.py argv ${AWS_REGION:-us-east-1}"
        """
    )
    result = poe_runner(project, "region")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["us-east-1"]


def test_command_environment_alternate_operator_uses_presence(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        toggle.cmd = "${PYTHON} runner.py argv ${TOKEN:+present}"
        """
    )
    absent = poe_runner(project, "toggle")
    present = poe_runner(project, "toggle", env={"TOKEN": "abc"})
    assert absent.returncode == 0
    assert present.returncode == 0
    assert absent.json_objects[-1]["args"] == []
    assert present.json_objects[-1]["args"] == ["present"]


def test_single_quoted_dollar_is_not_expanded_by_command_parser(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        literal.cmd = "${PYTHON} runner.py argv '$TOKEN'"
        """
    )
    result = poe_runner(project, "literal", env={"TOKEN": "secret"})
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["$TOKEN"]


def test_glob_expansion_matches_project_files(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        globber.cmd = "${PYTHON} runner.py argv data/*.txt"
        """
    )
    (project / "data").mkdir()
    (project / "data" / "b.txt").write_text("b", encoding="utf-8")
    (project / "data" / "a.txt").write_text("a", encoding="utf-8")
    result = poe_runner(project, "globber")
    assert result.returncode == 0
    assert sorted(path.rsplit("/", 2)[-2:] for path in result.json_objects[-1]["args"]) == [
        ["data", "a.txt"],
        ["data", "b.txt"],
    ]


def test_empty_glob_null_removes_unmatched_argument(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.empty]
        cmd = "${PYTHON} runner.py argv missing/*.txt kept"
        empty_glob = "null"
        """
    )
    result = poe_runner(project, "empty")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["kept"]


def test_cwd_option_runs_task_from_requested_directory(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.where]
        cmd = "${PYTHON} ../runner.py cwd"
        cwd = "subdir"
        """
    )
    (project / "subdir").mkdir()
    result = poe_runner(project, "where")
    assert result.returncode == 0
    assert result.json_objects[-1]["cwd"] == "subdir"
    assert result.json_objects[-1]["root"] == "project"


def test_capture_stdout_writes_task_output_to_project_file(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.capture]
        cmd = "${PYTHON} runner.py emit captured value"
        capture_stdout = "out.txt"
        """
    )
    result = poe_runner(project, "capture")
    assert result.returncode == 0
    assert (project / "out.txt").read_text(encoding="utf-8") == "captured value\n"


def test_task_env_values_are_visible_to_subprocess(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.show]
        cmd = "${PYTHON} runner.py env COLOR SIZE"
        env = { COLOR = "blue", SIZE = "large" }
        """
    )
    result = poe_runner(project, "show")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"COLOR": "blue", "SIZE": "large"}


def test_private_env_can_interpolate_without_leaking_to_process(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.private]
        cmd = "${PYTHON} runner.py argv ${_secret}"
        env = { _secret = "hidden" }
        """
    )
    result = poe_runner(project, "private")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["hidden"]


def test_expected_envfile_loads_variables_for_task(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.fromfile]
        cmd = "${PYTHON} runner.py env MODE LABEL"
        envfile = "local.env"
        """
    )
    (project / "local.env").write_text("MODE=dev\nLABEL='quoted value'\n", encoding="utf-8")
    result = poe_runner(project, "fromfile")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"LABEL": "quoted value", "MODE": "dev"}


def test_optional_envfile_can_be_missing(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.optional]
        cmd = "${PYTHON} runner.py argv ok"
        envfile.optional = ["missing.env"]
        """
    )
    result = poe_runner(project, "optional")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["ok"]


def test_named_argument_default_is_exposed_to_command(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.greet]
        cmd = "${PYTHON} runner.py argv ${NAME}"
        args = [{ name = "NAME", default = "world" }]
        """
    )
    result = poe_runner(project, "greet")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["world"]


def test_positional_argument_is_available_by_name(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.copy]
        cmd = "${PYTHON} runner.py argv ${SRC} ${DEST}"
        args = [
          { name = "SRC", positional = true },
          { name = "DEST", positional = true },
        ]
        """
    )
    result = poe_runner(project, "copy", "input.txt", "output.txt")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["input.txt", "output.txt"]


def test_boolean_argument_toggles_environment_presence(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.flag]
        cmd = "${PYTHON} runner.py env VERBOSE"
        args = [{ name = "VERBOSE", options = ["--verbose"], type = "boolean" }]
        """
    )
    off = poe_runner(project, "flag")
    on = poe_runner(project, "flag", "--verbose")
    assert off.returncode == 0
    assert on.returncode == 0
    assert off.json_objects[-1] == {"VERBOSE": None}
    assert on.json_objects[-1] == {"VERBOSE": "True"}


def test_integer_and_float_arguments_reach_expression_as_typed_values(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.math]
        expr = "json.dumps({'total': count + 2, 'ratio': ratio * 2})"
        imports = ["json"]
        args = [
          { name = "count", type = "integer", default = 3 },
          { name = "ratio", type = "float", default = 1.5 },
        ]
        """
    )
    result = poe_runner(project, "math")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"ratio": 3.0, "total": 5}


def test_choices_reject_unsupported_argument_value(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.pick]
        cmd = "${PYTHON} runner.py argv ${FLAVOR}"
        args = [{ name = "FLAVOR", choices = ["vanilla", "chocolate"], default = "vanilla" }]
        """
    )
    result = poe_runner(project, "pick", "--flavor", "mint")
    assert result.returncode != 0
    assert not result.json_objects


def test_multiple_option_values_are_joined_for_command_environment(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.multi]
        cmd = "${PYTHON} runner.py env ITEM"
        args = [{ name = "ITEM", options = ["--item"], multiple = true }]
        """
    )
    result = poe_runner(project, "multi", "--item", "a", "b", "--item", "c")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"ITEM": "a b c"}


def test_expr_task_prints_expression_result(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.expr]
        expr = "json.dumps({'items': len([1, 2, 3])})"
        imports = ["json"]
        """
    )
    result = poe_runner(project, "expr")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"items": 3}


def test_expr_assert_false_returns_nonzero(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.guard]
        expr = "False"
        assert = true
        """
    )
    result = poe_runner(project, "guard")
    assert result.returncode != 0


def test_script_task_receives_typed_arguments(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.scripted]
        script = "tasksmod:emit(name, count, flag, ratio, items)"
        args = [
          { name = "name", default = "Ada" },
          { name = "count", type = "integer", default = 2 },
          { name = "flag", type = "boolean" },
          { name = "ratio", type = "float", default = 1.25 },
          { name = "items", multiple = true },
        ]
        """
    )
    result = poe_runner(project, "scripted", "--flag", "--items", "x", "y")
    assert result.returncode == 0
    assert result.json_objects[-1] == {
        "count": 2,
        "extra": [],
        "flag": True,
        "items": ["x", "y"],
        "name": "Ada",
        "ratio": 1.25,
    }


def test_script_print_result_outputs_return_value(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.script-result]
        script = "tasksmod:result(value)"
        print_result = true
        args = [{ name = "value", default = "done" }]
        """
    )
    result = poe_runner(project, "script-result")
    assert result.returncode == 0
    assert "RESULT:done" in result.plain_lines


def test_hidden_task_cannot_be_executed_directly(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        _hidden = "${PYTHON} runner.py emit hidden"
        """
    )
    result = poe_runner(project, "_hidden")
    assert result.returncode != 0
    assert "hidden" not in result.plain_lines


def test_unknown_task_returns_nonzero_without_running_payload(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        known = "${PYTHON} runner.py emit known"
        """
    )
    result = poe_runner(project, "missing")
    assert result.returncode != 0
    assert "known" not in result.plain_lines


def test_command_ignore_fail_turns_failure_into_success(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.soft]
        cmd = "${PYTHON} runner.py fail 7"
        ignore_fail = true
        """
    )
    result = poe_runner(project, "soft")
    assert result.returncode == 0


def test_help_lists_public_task_with_help_text(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.documented]
        help = "Run the documented task"
        cmd = "${PYTHON} runner.py emit documented"
        """
    )
    result = poe_runner(project)
    assert result.returncode != 0
    assert "documented" in result.stdout
    assert "Run the documented task" in result.stdout


def test_poe_tasks_toml_can_define_tasks_without_tool_namespace(poe_project, poe_runner):
    project = poe_project(
        """
        [tasks]
        standalone = "${PYTHON} runner.py argv ok"
        """,
        filename="poe_tasks.toml",
    )
    result = poe_runner(project, "standalone")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["ok"]


def test_library_app_runs_temp_project_with_explicit_output_stream(poe_project):
    from poethepoet.app import PoeThePoet

    project = poe_project(
        """
        [tool.poe.tasks.inline]
        expr = "'library-ok'"
        """
    )
    output = io.StringIO()
    app = PoeThePoet(
        cwd=project,
        output=output,
        env={"PATH": "", "PYTHONPATH": "", "NO_COLOR": "1"},
    )
    assert app(cli_args=["inline"]) == 0
    assert "Poe =>" in output.getvalue()


def test_describe_task_args_reports_choices_and_boolean_type(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.pick]
        cmd = "${PYTHON} runner.py argv ${flavor}"
        args = [
          { name = "flavor", options = ["-f", "--flavor"], choices = ["vanilla", "chocolate"], help = "Flavor" },
          { name = "loud", options = ["--loud"], type = "boolean", help = "Loud mode" },
        ]
        """
    )
    result = poe_runner(project, "_describe_task_args", "pick", str(project))
    assert result.returncode == 0
    assert "--flavor" in result.stdout
    assert "vanilla chocolate" in result.stdout
    assert "--loud" in result.stdout
    assert "boolean" in result.stdout
