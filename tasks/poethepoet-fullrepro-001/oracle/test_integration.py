from __future__ import annotations

import json
import io

import pytest


def event_log(project):
    path = project / "events.log"
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


@pytest.mark.depends_on("test_string_task_runs_as_command_and_appends_free_args")
def test_sequence_runs_referenced_tasks_in_declared_order(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        first = "${PYTHON} runner.py record first"
        second = "${PYTHON} runner.py record second"
        all.sequence = ["first", "second"]
        """
    )
    result = poe_runner(project, "all")
    assert result.returncode == 0
    assert event_log(project) == ["first", "second"]


@pytest.mark.depends_on("test_script_task_receives_typed_arguments")
def test_sequence_combines_inline_command_script_and_expression(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.combo]
        sequence = [
          { cmd = "${PYTHON} runner.py record cmd" },
          { script = "tasksmod:record('script')" },
          { expr = "json.dumps({'done': True})", imports = ["json"] },
        ]
        """
    )
    result = poe_runner(project, "combo")
    assert result.returncode == 0
    assert event_log(project) == ["cmd", "script"]
    assert result.json_objects[-1] == {"done": True}


@pytest.mark.depends_on("test_string_task_runs_as_command_and_appends_free_args")
def test_sequence_default_item_type_can_treat_strings_as_commands(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.direct]
        sequence = [
          "${PYTHON} runner.py record one",
          "${PYTHON} runner.py record two",
        ]
        default_item_type = "cmd"
        """
    )
    result = poe_runner(project, "direct")
    assert result.returncode == 0
    assert event_log(project) == ["one", "two"]


@pytest.mark.depends_on("test_string_task_runs_as_command_and_appends_free_args")
def test_parallel_runs_each_local_subtask(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.all]
        parallel = [
          { cmd = "${PYTHON} runner.py touch left.txt left" },
          { cmd = "${PYTHON} runner.py touch right.txt right" },
        ]
        """
    )
    result = poe_runner(project, "all")
    assert result.returncode == 0
    assert (project / "left.txt").read_text(encoding="utf-8") == "left\n"
    assert (project / "right.txt").read_text(encoding="utf-8") == "right\n"


@pytest.mark.depends_on("test_string_task_runs_as_command_and_appends_free_args")
def test_sequence_waits_for_nested_parallel_group(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.workflow]
        sequence = [
          [
            { cmd = "${PYTHON} runner.py touch first.txt first" },
            { cmd = "${PYTHON} runner.py touch second.txt second" },
          ],
          { cmd = "${PYTHON} runner.py touch after.txt after" },
        ]
        """
    )
    result = poe_runner(project, "workflow")
    assert result.returncode == 0
    assert (project / "first.txt").read_text(encoding="utf-8") == "first\n"
    assert (project / "second.txt").read_text(encoding="utf-8") == "second\n"
    assert (project / "after.txt").read_text(encoding="utf-8") == "after\n"


@pytest.mark.depends_on("test_named_argument_default_is_exposed_to_command")
def test_ref_task_passes_arguments_declared_in_reference(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.target]
        cmd = "${PYTHON} runner.py argv ${subject}"
        args = [{ name = "subject", default = "default" }]

        [tool.poe.tasks.alias]
        ref = "target --subject Ada"
        """
    )
    result = poe_runner(project, "alias")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["Ada"]


@pytest.mark.depends_on("test_hidden_task_cannot_be_executed_directly")
def test_ref_task_can_run_hidden_task_through_public_alias(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks]
        _hidden = "${PYTHON} runner.py record hidden"
        public.ref = "_hidden"
        """
    )
    result = poe_runner(project, "public")
    assert result.returncode == 0
    assert event_log(project) == ["hidden"]


@pytest.mark.depends_on("test_expr_task_prints_expression_result")
def test_switch_selects_matching_case_from_control_output(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.pick]
        control.expr = "'green'"
        [[tool.poe.tasks.pick.switch]]
        case = "blue"
        cmd = "${PYTHON} runner.py record blue"
        [[tool.poe.tasks.pick.switch]]
        case = "green"
        cmd = "${PYTHON} runner.py record green"
        """
    )
    result = poe_runner(project, "pick")
    assert result.returncode == 0
    assert event_log(project) == ["green"]


@pytest.mark.depends_on("test_expr_task_prints_expression_result")
def test_switch_uses_default_case_when_no_case_matches(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.pick]
        control.expr = "'other'"
        [[tool.poe.tasks.pick.switch]]
        case = "blue"
        cmd = "${PYTHON} runner.py record blue"
        [[tool.poe.tasks.pick.switch]]
        cmd = "${PYTHON} runner.py record fallback"
        """
    )
    result = poe_runner(project, "pick")
    assert result.returncode == 0
    assert event_log(project) == ["fallback"]


@pytest.mark.depends_on("test_expr_assert_false_returns_nonzero")
def test_switch_default_pass_allows_no_matching_case(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.pick]
        control.expr = "'other'"
        default = "pass"
        [[tool.poe.tasks.pick.switch]]
        case = "blue"
        cmd = "${PYTHON} runner.py record blue"
        """
    )
    result = poe_runner(project, "pick")
    assert result.returncode == 0
    assert event_log(project) == []


@pytest.mark.depends_on("test_choices_reject_unsupported_argument_value")
def test_switch_without_match_fails_without_running_a_case(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.pick]
        control.expr = "'other'"
        [[tool.poe.tasks.pick.switch]]
        case = "green"
        cmd = "${PYTHON} runner.py record green"
        """
    )
    result = poe_runner(project, "pick")
    assert result.returncode != 0
    assert event_log(project) == []


@pytest.mark.depends_on("test_string_task_runs_as_command_and_appends_free_args")
def test_deps_run_before_task_body(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.prepare]
        cmd = "${PYTHON} runner.py record prepare"

        [tool.poe.tasks.main]
        cmd = "${PYTHON} runner.py record main"
        deps = ["prepare"]
        """
    )
    result = poe_runner(project, "main")
    assert result.returncode == 0
    assert event_log(project) == ["prepare", "main"]


@pytest.mark.depends_on("test_command_quotes_keep_whitespace_inside_one_argument")
def test_uses_captures_upstream_output_as_command_variable(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks._value]
        cmd = "${PYTHON} runner.py emit alpha beta"

        [tool.poe.tasks.consume]
        cmd = "${PYTHON} runner.py argv ${VALUE}"
        uses = { VALUE = "_value" }
        """
    )
    result = poe_runner(project, "consume")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["alpha", "beta"]


@pytest.mark.depends_on("test_expected_envfile_loads_variables_for_task")
def test_uses_env_parses_upstream_output_into_environment(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks._vars]
        cmd = "${PYTHON} runner.py envlines"

        [tool.poe.tasks.consume]
        cmd = "${PYTHON} runner.py env FROM_USE SECOND"
        uses_env = "_vars"
        """
    )
    result = poe_runner(project, "consume")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"FROM_USE": "alpha", "SECOND": "beta"}


@pytest.mark.depends_on("test_capture_stdout_writes_task_output_to_project_file")
def test_envfile_args_cwd_and_capture_project_same_projection(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.report]
        cmd = "${PYTHON} ../runner.py env MODE SUBJECT"
        cwd = "work"
        envfile = "local.env"
        capture_stdout = "report.jsonl"
        args = [{ name = "SUBJECT", default = "Ada" }]
        """
    )
    (project / "work").mkdir()
    (project / "local.env").write_text("MODE=integration\n", encoding="utf-8")
    result = poe_runner(project, "report")
    payload = json.loads((project / "report.jsonl").read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert payload == {"MODE": "integration", "SUBJECT": "Ada"}


@pytest.mark.depends_on(
    "test_task_env_values_are_visible_to_subprocess",
    "test_expected_envfile_loads_variables_for_task",
)
def test_task_env_overrides_task_envfile_value(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.precedence]
        cmd = "${PYTHON} runner.py env MODE"
        envfile = "local.env"
        env = { MODE = "task" }
        """
    )
    (project / "local.env").write_text("MODE=file\n", encoding="utf-8")
    result = poe_runner(project, "precedence")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"MODE": "task"}


@pytest.mark.depends_on("test_iter_tasks_returns_public_task_names")
def test_included_toml_file_contributes_tasks(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe]
        include = "included.toml"

        [tool.poe.tasks.local]
        cmd = "${PYTHON} runner.py record local"
        """
    )
    (project / "included.toml").write_text(
        """
        [tool.poe.tasks.included]
        cmd = "${PYTHON} runner.py record included"
        """,
        encoding="utf-8",
    )
    result = poe_runner(project, "included")
    assert result.returncode == 0
    assert event_log(project) == ["included"]


@pytest.mark.depends_on("test_cwd_option_runs_task_from_requested_directory")
def test_include_cwd_changes_conf_dir_for_included_task(poe_project, poe_runner):
    project = poe_project(
        """
        [[tool.poe.include]]
        path = "sub/tasks.toml"
        cwd = "sub"
        """
    )
    sub = project / "sub"
    sub.mkdir()
    (sub / "runner.py").write_text((project / "runner.py").read_text(encoding="utf-8"), encoding="utf-8")
    (sub / "tasks.toml").write_text(
        """
        [tool.poe.tasks.where]
        cmd = "${PYTHON} runner.py cwd"
        """,
        encoding="utf-8",
    )
    result = poe_runner(project, "where")
    assert result.returncode == 0
    assert result.json_objects[-1]["cwd"] == "sub"
    assert result.json_objects[-1]["conf"] == "sub"


@pytest.mark.depends_on("test_poe_tasks_toml_can_define_tasks_without_tool_namespace")
def test_poe_tasks_json_can_define_tasks_without_tool_namespace(tmp_path, poe_runner):
    from conftest import write_project

    project = write_project(
        tmp_path / "json_project",
        '{"tasks": {"json-task": "${PYTHON} runner.py argv json"}}',
        filename="poe_tasks.json",
    )
    result = poe_runner(project, "json-task")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["json"]


@pytest.mark.depends_on("test_poe_tasks_toml_can_define_tasks_without_tool_namespace")
def test_poe_tasks_yaml_can_define_tasks_without_tool_namespace(tmp_path, poe_runner):
    from conftest import write_project

    project = write_project(
        tmp_path / "yaml_project",
        """
        tasks:
          yaml-task:
            cmd: "${PYTHON} runner.py argv yaml"
        """,
        filename="poe_tasks.yaml",
    )
    result = poe_runner(project, "yaml-task")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["yaml"]


@pytest.mark.depends_on("test_optional_envfile_can_be_missing")
def test_recursive_includes_preserve_existing_root_task_definition(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe]
        include = "parent.toml"

        [tool.poe.tasks.shared]
        cmd = "${PYTHON} runner.py record root"
        """
    )
    (project / "parent.toml").write_text(
        """
        [tool.poe]
        include = "child.toml"

        [tool.poe.tasks.parent]
        cmd = "${PYTHON} runner.py record parent"
        """,
        encoding="utf-8",
    )
    (project / "child.toml").write_text(
        """
        [tool.poe.tasks.shared]
        cmd = "${PYTHON} runner.py record child"
        """,
        encoding="utf-8",
    )
    result = poe_runner(project, "shared")
    assert result.returncode == 0
    assert event_log(project) == ["root"]


@pytest.mark.depends_on("test_string_task_runs_as_command_and_appends_free_args")
def test_global_default_array_item_type_changes_sequence_strings(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe]
        default_array_item_task_type = "cmd"

        [tool.poe.tasks]
        flow = [
          "${PYTHON} runner.py record global-one",
          "${PYTHON} runner.py record global-two",
        ]
        """
    )
    result = poe_runner(project, "flow")
    assert result.returncode == 0
    assert event_log(project) == ["global-one", "global-two"]


@pytest.mark.depends_on("test_script_task_receives_typed_arguments")
def test_global_default_task_type_can_make_string_task_a_script(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe]
        default_task_type = "script"

        [tool.poe.tasks]
        scripted = "tasksmod:emit"
        """
    )
    result = poe_runner(project, "scripted")
    assert result.returncode == 0
    assert result.json_objects[-1]["name"] == "anon"


@pytest.mark.depends_on("test_capture_stdout_writes_task_output_to_project_file")
def test_dry_run_reports_without_creating_task_side_effect(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.make-file]
        cmd = "${PYTHON} runner.py touch created.txt made"
        """
    )
    result = poe_runner(project, "--dry-run", "make-file")
    assert result.returncode == 0
    assert not (project / "created.txt").exists()


@pytest.mark.depends_on("test_expr_task_prints_expression_result")
def test_quiet_global_option_suppresses_poe_banner_not_task_output(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.quiet]
        expr = "json.dumps({'still': 'printed'})"
        imports = ["json"]
        """
    )
    result = poe_runner(project, "--quiet", "quiet")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"still": "printed"}
    assert all(not line.startswith("Poe =>") for line in result.stdout.splitlines())


@pytest.mark.depends_on("test_script_task_receives_typed_arguments")
def test_script_task_receives_extra_args_projection(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.probe]
        script = "tasksmod:argv_probe(subject, _extra_args)"
        args = [{ name = "subject", default = "base" }]
        """
    )
    result = poe_runner(project, "probe", "--subject", "Ada", "--", "free", "--literal")
    assert result.returncode == 0
    assert result.json_objects[-1]["subject"] == "Ada"
    assert result.json_objects[-1]["extra"] == ["free", "--literal"]


@pytest.mark.depends_on("test_string_task_runs_as_command_and_appends_free_args")
def test_command_extra_args_can_be_placed_with_poe_extra_args(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.place]
        cmd = "${PYTHON} runner.py argv before $POE_EXTRA_ARGS after"
        """
    )
    result = poe_runner(project, "place", "one", "two")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["before", "one", "two", "after"]


@pytest.mark.depends_on("test_boolean_argument_toggles_environment_presence")
def test_boolean_args_propagate_through_ref_without_host_env(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.child]
        expr = "json.dumps({'flag': flag})"
        imports = ["json"]

        [tool.poe.tasks.parent]
        ref = "child"
        args = [{ name = "flag", type = "boolean" }]
        """
    )
    result = poe_runner(project, "parent", "--flag")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"flag": True}


@pytest.mark.depends_on("test_multiple_option_values_are_joined_for_command_environment")
def test_multiple_args_propagate_from_ref_definition(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.child]
        cmd = "${PYTHON} runner.py env items label"
        args = [
          { name = "items", options = ["--item"], multiple = true },
          { name = "label", default = "child" },
        ]

        [tool.poe.tasks.parent]
        ref = "child --item a b --label parent"
        """
    )
    result = poe_runner(project, "parent")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"items": "a b", "label": "parent"}


@pytest.mark.depends_on("test_choices_reject_unsupported_argument_value")
def test_switch_named_argument_selects_case_and_forwards_extra_args(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.choose]
        control.expr = "flavor"
        args = [{ name = "flavor", choices = ["vanilla", "mint"], default = "vanilla" }]
        [[tool.poe.tasks.choose.switch]]
        case = "mint"
        cmd = "${PYTHON} runner.py argv mint $POE_EXTRA_ARGS"
        [[tool.poe.tasks.choose.switch]]
        case = "vanilla"
        cmd = "${PYTHON} runner.py argv vanilla $POE_EXTRA_ARGS"
        """
    )
    result = poe_runner(project, "choose", "--flavor", "mint", "--", "cone")
    assert result.returncode == 0
    assert result.json_objects[-1]["args"] == ["mint", "cone"]


@pytest.mark.depends_on("test_expr_task_prints_expression_result")
def test_python_interpreter_shell_task_is_deterministic_public_shell_projection(poe_project, poe_runner):
    project = poe_project(
        """
        [tool.poe.tasks.py-shell]
        shell = "import json; print(json.dumps({'shell': 'python'}))"
        interpreter = "python"
        """
    )
    result = poe_runner(project, "py-shell")
    assert result.returncode == 0
    assert result.json_objects[-1] == {"shell": "python"}


@pytest.mark.depends_on("test_library_app_runs_temp_project_with_explicit_output_stream")
def test_library_app_run_and_iter_tasks_share_config_projection(tmp_path):
    from poethepoet import iter_tasks
    from poethepoet.app import PoeThePoet

    project = tmp_path / "library_project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        """
        [tool.poe.tasks]
        alpha.expr = "'A'"
        beta.expr = "'B'"
        _hidden.expr = "'H'"
        """,
        encoding="utf-8",
    )
    output = io.StringIO()
    app = PoeThePoet(cwd=project, output=output, env={"NO_COLOR": "1"})
    assert list(iter_tasks(str(project))) == ["alpha", "beta"]
    assert app(cli_args=["beta"]) == 0
    assert "B" in output.getvalue()
