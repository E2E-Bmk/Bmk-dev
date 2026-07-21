import os

import pytest

import click
from click.testing import CliRunner


def test_basic_command_help_and_execution():
    calls = []

    @click.command()
    def cli():
        """Hello World!"""
        calls.append(True)
        click.echo("I EXECUTED")

    runner = CliRunner()
    help_result = runner.invoke(cli, ["--help"])
    assert help_result.exit_code == 0
    assert "Hello World!" in help_result.output
    assert "Show this message and exit." in help_result.output
    assert calls == []

    run_result = runner.invoke(cli, [])
    assert run_result.exit_code == 0
    assert run_result.output == "I EXECUTED\n"
    assert calls == [True]


def test_variadic_sources_leave_final_destination():
    @click.command()
    @click.argument("sources", nargs=-1)
    @click.argument("destination")
    def copy(sources, destination):
        return sources, destination

    result = CliRunner().invoke(copy, ["a.txt", "b.txt", "out"], standalone_mode=False)
    assert result.return_value == (("a.txt", "b.txt"), "out")


def test_fixed_tuple_argument_converts_each_item():
    @click.command()
    @click.argument("name")
    @click.argument("point", nargs=2, type=click.INT)
    def locate(name, point):
        return name, point

    result = CliRunner().invoke(locate, ["origin", "1", "2"], standalone_mode=False)
    assert result.return_value == ("origin", (1, 2))


def test_unexpected_extra_argument_is_usage_error():
    @click.command()
    @click.argument("value")
    def cli(value):
        click.echo(value)

    result = CliRunner().invoke(cli, ["one", "two"])
    assert result.exit_code == 2
    assert "Got unexpected extra argument (two)" in result.output


@pytest.mark.parametrize(
    ("nargs", "environment", "expected"),
    [
        (2, "a b", ("a", "b")),
        (-1, "a b c", ("a", "b", "c")),
        (-1, "", ()),
    ],
    ids=["fixed", "variadic", "empty-variadic"],
)
def test_environment_variable_values(nargs, environment, expected):
    decorator = click.argument("value", envvar="VALUE", nargs=nargs) if nargs == -1 else click.option("--value", envvar="VALUE", nargs=nargs)

    @click.command()
    @decorator
    def cli(value):
        return value

    result = CliRunner().invoke(cli, env={"VALUE": environment}, standalone_mode=False)
    assert result.return_value == expected


def test_explicit_values_override_environment():
    @click.command()
    @click.argument("value", envvar="VALUE", nargs=-1)
    def cli(value):
        return value

    runner = CliRunner()
    explicit = runner.invoke(cli, ["one", "two"], env={"VALUE": "environment"}, standalone_mode=False)
    inherited = runner.invoke(cli, env={"VALUE": "environment"}, standalone_mode=False)
    assert explicit.return_value == ("one", "two")
    assert inherited.return_value == ("environment",)


def test_fixed_environment_value_enforces_arity():
    @click.command()
    @click.option("--point", envvar="POINT", nargs=2)
    def cli(point):
        return point

    result = CliRunner().invoke(cli, env={"POINT": "only-one"}, standalone_mode=False)
    assert isinstance(result.exception, click.BadParameter)
    assert "Takes 2 values but 1 was given" in result.exception.format_message()


@pytest.mark.parametrize(
    ("value", "expected"),
    [("", ""), ("  ", "  "), ("value", "value")],
    ids=["empty", "spaces", "text"],
)
def test_required_argument_accepts_supplied_text(value, expected):
    @click.command()
    @click.argument("value", required=True)
    def cli(value):
        return value

    result = CliRunner().invoke(cli, [value], standalone_mode=False)
    assert result.return_value == expected


def test_missing_required_argument_is_usage_error():
    @click.command()
    @click.argument("value", required=True)
    def cli(value):
        return value

    result = CliRunner().invoke(cli, [])
    assert result.exit_code == 2
    assert "Missing argument 'VALUE'" in result.output


def test_group_runs_parent_then_subcommand():
    @click.group()
    def cli():
        click.echo("root")

    @cli.command()
    def child():
        click.echo("child")

    result = CliRunner().invoke(cli, ["child"])
    assert result.exit_code == 0
    assert result.output == "root\nchild\n"


@pytest.mark.parametrize("container", ["mapping", "iterable"], ids=["mapping", "iterable"])
def test_group_constructor_registers_commands(container):
    @click.command()
    def child():
        click.echo("child", nl=False)

    commands = {"other": child} if container == "mapping" else [child]
    group = click.Group(commands=commands)
    command_name = "other" if container == "mapping" else "child"
    result = CliRunner().invoke(group, [command_name])
    assert result.exit_code == 0
    assert result.output == "child"


def test_nested_group_decorators_without_parentheses():
    @click.group
    def root():
        click.echo("root")

    @root.group
    def nested():
        click.echo("nested")

    @nested.command
    def leaf():
        click.echo("leaf")

    result = CliRunner().invoke(root, ["nested", "leaf"])
    assert result.exit_code == 0
    assert result.output == "root\nnested\nleaf\n"


def test_chained_commands_run_left_to_right():
    @click.group(chain=True)
    def cli():
        pass

    @cli.command()
    def first():
        click.echo("first")

    @cli.command()
    def second():
        click.echo("second")

    result = CliRunner().invoke(cli, ["second", "first", "second"])
    assert result.exit_code == 0
    assert result.output.splitlines() == ["second", "first", "second"]


def test_chained_commands_receive_own_options():
    @click.group(chain=True)
    def cli():
        pass

    @cli.command()
    @click.option("--format")
    def first(format):
        click.echo(f"first:{format}")

    @cli.command()
    @click.argument("value")
    def second(value):
        click.echo(f"second:{value}")

    result = CliRunner().invoke(cli, ["first", "--format=zip", "second", "payload"])
    assert result.exit_code == 0
    assert result.output.splitlines() == ["first:zip", "second:payload"]


@pytest.mark.parametrize(("chain", "expected"), [(False, "1"), (True, "[]")], ids=["normal", "chain"])
def test_result_callback_shape_without_command(chain, expected):
    @click.group(invoke_without_command=True, chain=chain)
    def cli():
        return 1

    @cli.result_callback()
    def process(value):
        click.echo(value, nl=False)

    assert CliRunner().invoke(cli, []).output == expected


def test_chain_result_callback_builds_pipeline():
    @click.group(chain=True, invoke_without_command=True)
    @click.option("--prefix", default="")
    def cli(prefix):
        pass

    @cli.command()
    def upper():
        return str.upper

    @cli.command()
    def strip():
        return str.strip

    @cli.result_callback()
    def process(processors, prefix):
        value = "  hello  "
        for processor in processors:
            value = processor(value)
        click.echo(prefix + value)

    result = CliRunner().invoke(cli, ["--prefix=>", "strip", "upper"])
    assert result.exit_code == 0
    assert result.output == ">HELLO\n"


@pytest.mark.parametrize("kwargs", [{"required": False}, {"nargs": -1}], ids=["optional", "variadic"])
def test_chained_group_rejects_ambiguous_arguments(kwargs):
    with pytest.raises(RuntimeError):
        decorator = click.argument("value", **kwargs)

        @click.group(chain=True)
        @decorator
        def cli(value):
            pass


def test_context_invoke_and_forward():
    group = click.Group()

    @group.command()
    @click.option("--count", default=1)
    def target(count):
        click.echo(f"count:{count}")

    @group.command()
    @click.option("--count", default=1)
    @click.pass_context
    def source(context, count):
        context.forward(target)
        context.invoke(target, count=42)

    result = CliRunner().invoke(group, ["source"])
    assert result.exit_code == 0
    assert result.output == "count:1\ncount:42\n"


def test_nested_default_map_supplies_option_default():
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name", default="normal")
    def child(name):
        click.echo(name)

    runner = CliRunner()
    mapped = runner.invoke(cli, ["child"], default_map={"child": {"name": "mapped"}})
    explicit = runner.invoke(cli, ["child", "--name", "explicit"], default_map={"child": {"name": "mapped"}})
    assert mapped.output == "mapped\n"
    assert explicit.output == "explicit\n"


def test_argument_help_section_and_optional_metavar():
    @click.command()
    @click.argument("name", required=False, help="The name to print")
    @click.option("--count", default=1, help="number of greetings")
    def cli(name, count):
        pass

    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] [NAME]" in result.output
    assert "Positional arguments:" in result.output
    assert "The name to print" in result.output
    assert result.output.index("Positional arguments:") < result.output.index("Options:")


def test_deprecated_argument_help_label():
    @click.command()
    @click.argument("old", required=False, deprecated="use new instead", help="old value")
    def cli(old):
        pass

    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "[OLD!]" in result.output
    assert "(DEPRECATED: use new instead)" in result.output


def test_no_args_is_help_uses_usage_exit_code():
    result = CliRunner().invoke(click.Command("cli", no_args_is_help=True))
    assert result.exit_code == 2
    assert "Show this message and exit." in result.output


def test_group_argument_then_missing_or_selected_command():
    @click.group()
    @click.argument("object_name")
    def cli(object_name):
        click.echo(f"object={object_name}")

    @cli.command()
    def move():
        click.echo("move")

    runner = CliRunner()
    missing = runner.invoke(cli, ["box"])
    selected = runner.invoke(cli, ["box", "move"])
    assert missing.exit_code == 2
    assert "Missing command" in missing.output
    assert selected.output == "object=box\nmove\n"


def test_file_dash_copies_stdin_to_file_and_back():
    @click.command()
    @click.argument("source", type=click.File("rb"))
    @click.argument("destination", type=click.File("wb"))
    def copy(source, destination):
        destination.write(source.read())

    runner = CliRunner()
    with runner.isolated_filesystem():
        write_result = runner.invoke(copy, ["-", "message.txt"], input="hello")
        read_result = runner.invoke(copy, ["message.txt", "-"])
    assert write_result.exit_code == 0
    assert read_result.exit_code == 0
    assert read_result.output == "hello"


def test_atomic_file_replaces_only_after_callback():
    observed = []

    @click.command()
    @click.argument("destination", type=click.File("wb", atomic=True))
    def write(destination):
        destination.write(b"new\n")
        destination.flush()
        with open(destination.name, "rb") as stream:
            observed.append(stream.read())

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("value.txt", "wb") as stream:
            stream.write(b"old\n")
        result = runner.invoke(write, ["value.txt"])
        with open("value.txt", "rb") as stream:
            final = stream.read()
    assert result.exit_code == 0
    assert observed == [b"old\n"]
    assert final == b"new\n"


def test_path_allow_dash_and_isolated_filesystem():
    @click.command()
    @click.argument("path", type=click.Path(allow_dash=True))
    def cli(path):
        click.echo(f"{path}:{os.path.isdir('.')}")

    result = CliRunner().invoke(cli, ["-"])
    assert result.exit_code == 0
    assert result.output == "-:True\n"
