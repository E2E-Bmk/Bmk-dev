from uuid import UUID as UUIDValue

import pytest

import click
from click.testing import CliRunner


@pytest.mark.parametrize(
    "function_name",
    ["init_data", "init_data_command", "init_data_cmd", "init_data_group", "init_data_grp"],
    ids=["plain", "command", "cmd", "group", "grp"],
)
def test_generated_command_names(function_name):
    def callback():
        pass

    callback.__name__ = function_name
    assert click.command(callback).name == "init-data"


def test_command_and_group_repr():
    assert repr(click.Command("build")) == "<Command build>"
    assert repr(click.Group("tools")) == "<Group tools>"


def test_command_callback_return_value():
    @click.command()
    def cli():
        return 42

    with cli.make_context("cli", []) as context:
        assert cli.invoke(context) == 42


def test_explicit_parameters_precede_decorated_parameters():
    first = click.Argument(["first"])

    @click.command(params=[first])
    @click.argument("second")
    def cli(first, second):
        return first, second

    assert [parameter.name for parameter in cli.params] == ["first", "second"]


@pytest.mark.parametrize(
    ("type_", "default", "args", "expected"),
    [
        (str, "no value", [], "no value"),
        (str, "no value", ["--value=hello"], "hello"),
        (int, 42, [], "42"),
        (int, 42, ["--value=23"], "23"),
        (float, 42.0, [], "42.0"),
        (float, 42.0, ["--value=23.5"], "23.5"),
        (click.UUID, "ba122011-349f-423b-873b-9d6a79c688ab", [], "ba122011-349f-423b-873b-9d6a79c688ab"),
        (click.UUID, None, ["--value=821592c1-c50e-4971-9cd6-e89dc6832f86"], "821592c1-c50e-4971-9cd6-e89dc6832f86"),
    ],
    ids=["string-default", "string-explicit", "int-default", "int-explicit", "float-default", "float-explicit", "uuid-default", "uuid-explicit"],
)
def test_scalar_option_conversion(type_, default, args, expected):
    @click.command()
    @click.option("--value", type=type_, default=default)
    def cli(value):
        click.echo(value)

    result = CliRunner().invoke(cli, args)
    assert result.exception is None
    assert result.output == f"{expected}\n"


@pytest.mark.parametrize(
    ("type_", "value", "message"),
    [
        (int, "x", "not a valid integer"),
        (float, "x", "not a valid float"),
        (click.UUID, "x", "not a valid UUID"),
    ],
    ids=["integer", "float", "uuid"],
)
def test_invalid_scalar_option_is_usage_error(type_, value, message):
    @click.command()
    @click.option("--value", type=type_)
    def cli(value):
        click.echo(value)

    result = CliRunner().invoke(cli, ["--value", value])
    assert result.exit_code == 2
    assert message in result.output


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("true", True),
        ("t", True),
        ("yes", True),
        ("y", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("f", False),
        ("no", False),
        ("n", False),
        ("off", False),
    ],
    ids=["one", "true", "t", "yes", "y", "on", "zero", "false", "f", "no", "n", "off"],
)
def test_boolean_option_conversion_is_case_insensitive(value, expected):
    @click.command()
    @click.option("--flag", type=bool)
    def cli(flag):
        return flag

    runner = CliRunner()
    assert runner.invoke(cli, ["--flag", value], standalone_mode=False).return_value is expected
    assert runner.invoke(cli, ["--flag", value.upper()], standalone_mode=False).return_value is expected


@pytest.mark.parametrize(
    ("default", "args", "expected"),
    [
        (True, ["--on"], True),
        (False, ["--on"], True),
        (None, ["--on"], True),
        (True, ["--off"], False),
        (False, [], False),
        (None, [], None),
    ],
    ids=["on-true", "on-false", "on-none", "off", "default-false", "default-none"],
)
def test_dual_boolean_switch(default, args, expected):
    @click.command()
    @click.option("--on/--off", default=default)
    def cli(on):
        return on

    result = CliRunner().invoke(cli, args, standalone_mode=False)
    assert result.return_value is expected


@pytest.mark.parametrize(
    ("default", "args", "expected"),
    [
        (True, ["--upper"], "upper"),
        (True, ["--lower"], "lower"),
        (False, ["--upper", "--lower"], "lower"),
        (None, ["--lower", "--upper"], "upper"),
    ],
    ids=["upper", "lower", "last-lower", "last-upper"],
)
def test_competing_flag_values(default, args, expected):
    @click.command()
    @click.option("--upper", "case", flag_value="upper", default=default)
    @click.option("--lower", "case", flag_value="lower")
    def cli(case):
        return case

    result = CliRunner().invoke(cli, args, standalone_mode=False)
    assert result.return_value == expected


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, "FOO"),
        ({"required": False}, "[FOO]"),
        ({"nargs": -1}, "[FOO]..."),
        ({"nargs": -1, "required": True}, "FOO..."),
    ],
    ids=["required-default", "optional", "variadic-optional", "variadic-required"],
)
def test_argument_usage_metavar(kwargs, expected):
    @click.command()
    @click.argument("foo", **kwargs)
    def cli(foo):
        pass

    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert result.output.splitlines()[0] == f"Usage: cli [OPTIONS] {expected}"


@pytest.mark.parametrize(
    "type_",
    [(str, int), click.Tuple([str, int])],
    ids=["tuple-literal", "tuple-object"],
)
def test_tuple_type_sets_argument_arity(type_):
    @click.command()
    @click.argument("item", type=type_)
    def cli(item):
        return item

    result = CliRunner().invoke(cli, ["peter", "7"], standalone_mode=False)
    assert result.return_value == ("peter", 7)


def test_tuple_type_rejects_conflicting_nargs():
    with pytest.raises(ValueError, match="nargs.*must be 2.*but it was 3"):
        click.Argument(["item"], type=(str, int), nargs=3)


def test_uuid_option_returns_uuid_value():
    @click.command()
    @click.option("--identifier", type=click.UUID)
    def cli(identifier):
        return identifier

    result = CliRunner().invoke(cli, ["--identifier", "821592c1-c50e-4971-9cd6-e89dc6832f86"], standalone_mode=False)
    assert result.return_value == UUIDValue("821592c1-c50e-4971-9cd6-e89dc6832f86")
