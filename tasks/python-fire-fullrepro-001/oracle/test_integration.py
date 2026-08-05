from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest


@pytest.mark.depends_on(
    "test_function_positional_integer_returns_numeric_result",
    "test_function_named_argument_returns_numeric_result",
)
def test_positional_and_named_numeric_dispatch_share_stdout_projection(cli_component, run_fire):
    positional = run_fire(cli_component, ["double", "9"])
    named = run_fire(cli_component, ["double", "--value=9"])

    assert positional.result == named.result == 18
    assert positional.stdout == named.stdout == "18\n"


@pytest.mark.depends_on(
    "test_float_argument_is_converted",
    "test_boolean_true_argument_uses_python_value",
    "test_none_argument_uses_python_none",
)
def test_typed_arguments_project_to_return_dict_and_serialized_lines(cli_component, run_fire):
    observation = run_fire(cli_component, ["typed", "3", "4.5", "--flag=True", "--none=None"])

    assert observation.result == {"a": 3, "b": 4.5, "flag": True, "none": None}
    assert "a:" in observation.stdout
    assert "3" in observation.stdout
    assert "b:" in observation.stdout
    assert "4.5" in observation.stdout
    assert "flag: true" in observation.stdout
    assert "none: null" in observation.stdout


@pytest.mark.depends_on(
    "test_dict_key_traversal_reaches_nested_value",
    "test_list_literal_argument_is_converted",
)
def test_function_returned_list_can_be_indexed_then_mapped(cli_component, run_fire):
    observation = run_fire(cli_component, ["table", "-", "1", "name"])

    assert observation.result == "Lin"
    assert observation.stdout == "Lin\n"


@pytest.mark.depends_on(
    "test_function_returned_object_can_be_traversed_after_separator",
    "test_hyphenated_member_access_maps_to_underscore_property",
)
def test_constructed_object_dict_property_can_be_traversed_to_scalar(cli_component, run_fire):
    observation = run_fire(cli_component, ["maker", "--name=Lin", "--size=7", "-", "score-card", "score"])

    assert observation.result == 70
    assert observation.stdout == "70\n"


@pytest.mark.depends_on(
    "test_class_instantiation_uses_constructor_flags",
    "test_class_instantiation_can_continue_to_method",
)
def test_class_constructor_flags_and_method_arguments_form_one_command(cli_component, run_fire):
    observation = run_fire(cli_component, ["widget", "--name=Ada", "--size=3", "combine", "left", "--right=right"])

    assert observation.result == "Ada:left:right"
    assert observation.stdout == "Ada:left:right\n"


@pytest.mark.depends_on(
    "test_help_flag_exits_and_lists_public_members",
    "test_hyphenated_member_access_maps_to_underscore_property",
)
def test_help_for_object_mentions_values_and_commands_from_same_state(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "--", "--help"], name="python-fire-tool")

    assert observation.exit_code == 0
    assert observation.stderr
    assert "greet" in observation.stderr
    assert "size" in observation.stderr


@pytest.mark.depends_on(
    "test_bash_completion_contains_top_level_public_commands",
    "test_help_flag_exits_and_lists_public_members",
)
def test_completion_and_help_expose_the_same_top_level_commands(cli_component, run_fire):
    completion = run_fire(cli_component, ["--", "--completion", "bash"])
    help_view = run_fire(cli_component, ["--", "--help"])

    for command in ["double", "typed", "display", "instance", "widget"]:
        assert command in completion.stdout
        assert command in help_view.stderr


@pytest.mark.depends_on(
    "test_trace_flag_exits_and_reports_command_steps",
    "test_bound_method_uses_default_argument",
)
def test_trace_for_bound_method_reports_traversal_without_stdout_value(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "greet", "--", "--trace"])

    assert observation.exit_code == 0
    assert observation.stdout == ""
    assert observation.stderr
    assert "greet" in observation.stderr


@pytest.mark.depends_on(
    "test_default_separator_forces_then_traverses_string_result",
    "test_bound_method_uses_named_argument",
)
def test_separator_result_can_use_public_string_method_after_invocation(cli_component, run_fire):
    observation = run_fire(cli_component, ["display", "hello", "-", "replace", "h", "H", "--count=-1"])

    assert observation.result == "Hello!"
    assert observation.stdout == "Hello!\n"


@pytest.mark.depends_on(
    "test_custom_separator_allows_default_separator_as_value",
    "test_default_separator_forces_then_traverses_string_result",
)
def test_custom_separator_changes_only_fire_boundary_not_function_result(cli_component, run_fire):
    observation = run_fire(
        cli_component,
        ["display", "-", "SEP", "replace", "-", "dash", "--count=-1", "--", "--separator", "SEP"],
    )

    assert observation.result == "dash!"
    assert observation.stdout == "dash!\n"


@pytest.mark.depends_on(
    "test_list_literal_argument_is_converted",
    "test_sequence_index_traversal_reaches_tuple_item",
)
def test_parsed_list_result_can_be_traversed_after_separator(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", "[10, 20, 30]", "-", "1"])

    assert observation.result == 20
    assert observation.stdout == "20\n"


@pytest.mark.depends_on(
    "test_dict_literal_argument_is_converted",
    "test_dict_key_traversal_reaches_nested_value",
)
def test_parsed_dict_result_can_be_traversed_after_separator(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", '{"outer": {"inner": 5}}', "-", "outer", "inner"])

    assert observation.result == 5
    assert observation.stdout == "5\n"


@pytest.mark.depends_on(
    "test_custom_serializer_controls_mapping_stdout",
    "test_boolean_true_argument_uses_python_value",
)
def test_custom_serializer_sees_converted_mapping_return(cli_component, run_fire):
    observation = run_fire(
        cli_component,
        ["typed", "2", "4.5", "--flag=True"],
        serialize=json_serializer,
    )

    assert observation.result["flag"] is True
    assert json.loads(observation.stdout) == {"a": 2, "b": 4.5, "flag": True, "none": None}


@pytest.mark.depends_on(
    "test_class_instantiation_uses_constructor_flags",
    "test_custom_serializer_controls_mapping_stdout",
)
def test_custom_serializer_can_project_public_object_return(cli_component, run_fire):
    observation = run_fire(
        cli_component,
        ["record", "--name=Ivy", "--size=9"],
        serialize=widget_serializer,
    )

    assert observation.result.name == "Ivy"
    assert observation.result.size == 9
    assert observation.stdout == "Widget<Ivy:9>\n"


@pytest.mark.depends_on(
    "test_varargs_function_consumes_all_unseparated_tokens",
    "test_default_separator_forces_then_traverses_string_result",
)
def test_varargs_result_can_be_forced_before_string_method_traversal(cli_component, run_fire):
    observation = run_fire(cli_component, ["collect", "red", "green", "-", "upper"])

    assert observation.result == "RED|GREEN"
    assert observation.stdout == "RED|GREEN\n"


@pytest.mark.depends_on(
    "test_bound_method_uses_named_argument",
    "test_callable_object_accepts_named_call_argument",
)
def test_bound_method_and_callable_object_use_same_instance_state(cli_component, run_fire):
    method = run_fire(cli_component, ["instance", "combine", "left", "--right=right"])
    called = run_fire(cli_component, ["instance", "--value=left"])

    assert method.result == "ready:left:right"
    assert called.result == "ready:left"
    assert "ready" in method.stdout
    assert "ready" in called.stdout


@pytest.mark.depends_on(
    "test_missing_key_reports_public_error_exit",
    "test_help_flag_exits_and_lists_public_members",
)
def test_missing_member_error_includes_help_path_for_same_component(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "absent"])

    assert observation.exit_code
    assert observation.stdout == ""
    assert observation.stderr


@pytest.mark.depends_on(
    "test_out_of_range_index_reports_public_error_exit",
    "test_dict_key_traversal_reaches_nested_value",
)
def test_index_error_on_nested_collection_reports_public_help_path(cli_component, run_fire):
    observation = run_fire(cli_component, ["data", "alpha", "9"])

    assert observation.exit_code
    assert observation.stdout == ""
    assert observation.stderr


@pytest.mark.depends_on(
    "test_hyphenated_member_access_maps_to_underscore_property",
    "test_bound_method_uses_default_argument",
)
def test_scalar_projection_can_continue_to_public_builtin_method(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "high-score", "bit-length"])

    assert observation.result == 6
    assert observation.stdout == "6\n"


@pytest.mark.depends_on(
    "test_hyphenated_member_access_maps_to_underscore_property",
    "test_dict_key_traversal_reaches_nested_value",
)
def test_object_dict_property_serializes_and_traverses_consistently(cli_component, run_fire):
    whole = run_fire(cli_component, ["instance", "score-card"])
    score = run_fire(cli_component, ["instance", "score-card", "score"])

    assert whole.result == {"name": "ready", "score": 40}
    assert "name:" in whole.stdout
    assert "ready" in whole.stdout
    assert "score: 40" in whole.stdout
    assert score.result == 40
    assert score.stdout == "40\n"


@pytest.mark.depends_on(
    "test_command_string_is_split_into_tokens",
    "test_tuple_return_uses_json_list_stdout",
)
def test_command_string_supports_named_flags_and_tuple_serialization(cli_component, run_fire):
    observation = run_fire(cli_component, "pair left --right=right")

    assert observation.result == ("left", "right")
    assert observation.stdout == "[\"left\", \"right\"]\n"


@pytest.mark.depends_on(
    "test_help_flag_exits_and_lists_public_members",
    "test_missing_key_reports_public_error_exit",
)
def test_public_name_argument_is_reflected_in_help_and_error_guidance(cli_component, run_fire):
    help_view = run_fire(cli_component, ["instance", "--", "--help"], name="custom-tool")
    error_view = run_fire(cli_component, ["instance", "absent"], name="custom-tool")

    assert "custom-tool" in help_view.stderr
    assert "custom-tool" in error_view.stderr


@pytest.mark.depends_on(
    "test_bash_completion_contains_top_level_public_commands",
    "test_hyphenated_member_access_maps_to_underscore_property",
)
def test_fish_completion_contains_commands_and_hyphenated_members(cli_component, run_fire):
    observation = run_fire(cli_component, ["--", "--completion", "fish"])

    assert observation.exit_code is None
    assert observation.stdout
    assert "double" in observation.stdout
    assert "high-score" in observation.stdout


@pytest.mark.depends_on(
    "test_public_import_exposes_fire_callable",
    "test_help_flag_exits_and_lists_public_members",
)
def test_root_component_without_command_returns_mapping_and_prints_grouped_help(cli_component, run_fire):
    observation = run_fire(cli_component, [])

    assert observation.result is cli_component
    assert observation.exit_code is None
    assert observation.stdout
    assert "data" in observation.stdout
    assert "double" in observation.stdout


@pytest.mark.depends_on(
    "test_list_literal_argument_is_converted",
    "test_dict_key_traversal_reaches_nested_value",
)
def test_table_function_projects_list_stdout_and_supports_nested_selection(cli_component, run_fire):
    whole = run_fire(cli_component, ["table"])
    selected = run_fire(cli_component, ["table", "-", "0", "score"])

    assert whole.result == [{"name": "Ada", "score": 8}, {"name": "Lin", "score": 13}]
    assert "Ada" in whole.stdout
    assert "Lin" in whole.stdout
    assert selected.result == 8
    assert selected.stdout == "8\n"


@pytest.mark.depends_on("test_public_import_exposes_fire_callable")
def test_file_path_invocation_exposes_module_commands(tmp_path):
    script = tmp_path / "commands.py"
    script.write_text(
        "def greet(name='World'):\n"
        "    return f'Hello {name}'\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "fire", str(script), "greet", "--name=Ada"],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )

    assert result.returncode == 0
    assert result.stdout == "Hello Ada\n"
    assert result.stderr == ""


@pytest.mark.depends_on("test_public_import_exposes_fire_callable")
def test_module_name_invocation_exposes_module_commands(tmp_path):
    module = tmp_path / "commands.py"
    module.write_text(
        "def greet(name='World'):\n"
        "    return f'Hello {name}'\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    paths = [str(tmp_path)]
    if existing_pythonpath:
        paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(paths)

    result = subprocess.run(
        [sys.executable, "-m", "fire", "commands", "greet", "--name=Ada"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout == "Hello Ada\n"
    assert result.stderr == ""


@pytest.mark.depends_on(
    "test_command_string_is_split_into_tokens",
    "test_tuple_return_uses_json_list_stdout",
)
def test_command_string_preserves_quoted_arguments_before_tuple_projection(cli_component, run_fire):
    observation = run_fire(cli_component, 'pair "left side" --right="right side"')

    assert observation.result == ("left side", "right side")
    assert observation.stdout == "[\"left side\", \"right side\"]\n"


@pytest.mark.depends_on(
    "test_class_instantiation_uses_constructor_flags",
    "test_hyphenated_member_access_maps_to_underscore_property",
    "test_dict_key_traversal_reaches_nested_value",
)
def test_class_result_can_cross_separator_to_mapping_value_and_string_method(cli_component, run_fire):
    observation = run_fire(cli_component, ["widget", "--name=Neo", "--size=6", "-", "score-card", "name", "upper"])

    assert observation.result == "NEO"
    assert observation.stdout == "NEO\n"


@pytest.mark.depends_on(
    "test_public_import_exposes_fire_callable",
    "test_tuple_return_uses_json_list_stdout",
)
def test_direct_file_and_module_invocation_share_tuple_projection(cli_component, run_fire, tmp_path):
    script = tmp_path / "tuple_commands.py"
    script.write_text(
        "def pair(left, right='R'):\n"
        "    return (left, right)\n",
        encoding="utf-8",
    )
    direct = run_fire(cli_component, ["pair", "left", "--right=right"])

    file_result = subprocess.run(
        [sys.executable, "-m", "fire", str(script), "pair", "left", "--right=right"],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    paths = [str(tmp_path)]
    if existing_pythonpath:
        paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    module_result = subprocess.run(
        [sys.executable, "-m", "fire", "tuple_commands", "pair", "left", "--right=right"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env=env,
    )

    assert direct.result == ("left", "right")
    assert file_result.returncode == module_result.returncode == 0
    assert file_result.stdout == module_result.stdout == direct.stdout == "[\"left\", \"right\"]\n"
    assert file_result.stderr == module_result.stderr == ""


def json_serializer(value):
    return json.dumps(value, sort_keys=True)


def widget_serializer(value):
    return f"Widget<{value.name}:{value.size}>"
