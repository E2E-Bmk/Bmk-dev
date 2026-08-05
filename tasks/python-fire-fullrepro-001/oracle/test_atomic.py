from __future__ import annotations


def test_public_import_exposes_fire_callable():
    import fire

    assert callable(fire.Fire)
    assert "Fire" in fire.__all__


def test_function_positional_integer_returns_numeric_result(cli_component, run_fire):
    observation = run_fire(cli_component, ["double", "5"])

    assert observation.result == 10
    assert observation.stdout == "10\n"
    assert observation.exit_code is None


def test_function_named_argument_returns_numeric_result(cli_component, run_fire):
    observation = run_fire(cli_component, ["double", "--value=6"])

    assert observation.result == 12
    assert observation.stdout == "12\n"


def test_command_string_is_split_into_tokens(cli_component, run_fire):
    observation = run_fire(cli_component, "double 7")

    assert observation.result == 14
    assert observation.stdout == "14\n"


def test_boolean_true_argument_uses_python_value(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", "True"])

    assert observation.result is True
    assert observation.stdout == "True\n"


def test_boolean_false_argument_uses_python_value(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", "False"])

    assert observation.result is False
    assert observation.stdout == "False\n"


def test_none_argument_uses_python_none(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", "None"])

    assert observation.result is None
    assert observation.stdout == ""


def test_float_argument_is_converted(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", "3.25"])

    assert observation.result == 3.25
    assert observation.stdout == "3.25\n"


def test_list_literal_argument_is_converted(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", "[1, 2, 3]"])

    assert observation.result == [1, 2, 3]
    assert observation.stdout.splitlines() == ["1", "2", "3"]


def test_dict_literal_argument_is_converted(cli_component, run_fire):
    observation = run_fire(cli_component, ["choose", '{"b": 2, "a": 1}'])

    assert observation.result == {"a": 1, "b": 2}
    assert {"a: 1", "b: 2"} <= set(observation.stdout.splitlines())


def test_tuple_return_uses_json_list_stdout(cli_component, run_fire):
    observation = run_fire(cli_component, ["pair", "L", "--right=R2"])

    assert observation.result == ("L", "R2")
    assert observation.stdout == "[\"L\", \"R2\"]\n"


def test_dict_key_traversal_reaches_nested_value(cli_component, run_fire):
    observation = run_fire(cli_component, ["data", "alpha", "1", "nested-key"])

    assert observation.result == "value"
    assert observation.stdout == "value\n"


def test_single_token_dict_key_with_space_is_supported(cli_component, run_fire):
    observation = run_fire(cli_component, ["data", "spaced key"])

    assert observation.result == "space value"
    assert observation.stdout == "space value\n"


def test_sequence_index_traversal_reaches_tuple_item(cli_component, run_fire):
    observation = run_fire(cli_component, ["data", "numbers", "2"])

    assert observation.result == 13
    assert observation.stdout == "13\n"


def test_hyphenated_member_access_maps_to_underscore_property(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "high-score"])

    assert observation.result == 40
    assert observation.stdout == "40\n"


def test_bound_method_uses_default_argument(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "greet"])

    assert observation.result == "ready!"
    assert observation.stdout == "ready!\n"


def test_bound_method_uses_named_argument(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "greet", "--punctuation=?"])

    assert observation.result == "ready?"
    assert observation.stdout == "ready?\n"


def test_class_instantiation_uses_constructor_flags(cli_component, run_fire):
    observation = run_fire(cli_component, ["record", "--name=Ada", "--size=3"])

    assert observation.result.name == "Ada"
    assert observation.result.size == 3
    assert "Ada" in observation.stdout


def test_class_instantiation_can_continue_to_method(cli_component, run_fire):
    observation = run_fire(cli_component, ["widget", "--name=Ada", "--size=3", "greet", "?"])

    assert observation.result == "Ada?"
    assert observation.stdout == "Ada?\n"


def test_callable_object_accepts_named_call_argument(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "--value=zap"])

    assert observation.result == "ready:zap"
    assert observation.stdout == "ready:zap\n"


def test_default_separator_forces_then_traverses_string_result(cli_component, run_fire):
    observation = run_fire(cli_component, ["display", "hello", "-", "upper"])

    assert observation.result == "HELLO!"
    assert observation.stdout == "HELLO!\n"


def test_custom_separator_allows_default_separator_as_value(cli_component, run_fire):
    observation = run_fire(
        cli_component,
        ["display", "-", "SEP", "upper", "--", "--separator", "SEP"],
    )

    assert observation.result == "-!"
    assert observation.stdout == "-!\n"


def test_varargs_function_consumes_all_unseparated_tokens(cli_component, run_fire):
    observation = run_fire(cli_component, ["collect", "red", "green", "blue"])

    assert observation.result == "red|green|blue"
    assert observation.stdout == "red|green|blue\n"


def test_function_returned_object_can_be_traversed_after_separator(cli_component, run_fire):
    observation = run_fire(cli_component, ["maker", "--name=Lin", "--size=7", "-", "high-score"])

    assert observation.result == 70
    assert observation.stdout == "70\n"


def test_custom_serializer_controls_mapping_stdout(cli_component, run_fire):
    observation = run_fire(
        cli_component,
        ["typed", "2", "4.5", "--flag=True"],
        serialize=stable_json_serializer,
    )

    assert observation.result == {"a": 2, "b": 4.5, "flag": True, "none": None}
    assert observation.stdout == '{"a": 2, "b": 4.5, "flag": true, "none": null}\n'


def test_help_flag_exits_and_lists_public_members(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "--", "--help"])

    assert observation.exit_code == 0
    assert observation.stderr
    assert "greet" in observation.stderr
    assert "high_score" in observation.stderr


def test_trace_flag_exits_and_reports_command_steps(cli_component, run_fire):
    observation = run_fire(cli_component, ["instance", "greet", "--", "--trace"])

    assert observation.exit_code == 0
    assert observation.stderr
    assert "greet" in observation.stderr


def test_bash_completion_contains_top_level_public_commands(cli_component, run_fire):
    observation = run_fire(cli_component, ["--", "--completion", "bash"])

    assert observation.exit_code is None
    assert observation.stdout
    assert "double" in observation.stdout
    assert "instance" in observation.stdout


def test_missing_key_reports_public_error_exit(cli_component, run_fire):
    observation = run_fire(cli_component, ["missing"])

    assert observation.exit_code
    assert observation.stderr


def test_out_of_range_index_reports_public_error_exit(cli_component, run_fire):
    observation = run_fire(cli_component, ["data", "alpha", "9"])

    assert observation.exit_code
    assert observation.stderr


def stable_json_serializer(value):
    import json

    return json.dumps(value, sort_keys=True)
