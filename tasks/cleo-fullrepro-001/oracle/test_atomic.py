from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

import pytest

from cleo.application import Application
from cleo.commands.command import Command
from cleo.exceptions import CleoCommandNotFoundError
from cleo.exceptions import CleoLogicError
from cleo.exceptions import CleoValueError
from cleo.helpers import argument
from cleo.helpers import option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.argv_input import ArgvInput
from cleo.io.inputs.definition import Definition
from cleo.io.inputs.option import Option
from cleo.loaders.factory_command_loader import FactoryCommandLoader


# Source: tests/io/inputs/test_argument.py
def test_optional_non_list_argument() -> None:
    argument_ = Argument(
        "foo",
        required=False,
        is_list=False,
        description="Foo description",
        default="bar",
    )

    assert argument_.name == "foo"
    assert not argument_.is_required()
    assert not argument_.is_list()
    assert argument_.description == "Foo description"
    assert argument_.default == "bar"


def test_required_non_list_argument() -> None:
    argument_ = Argument("foo", is_list=False, description="Foo description")

    assert argument_.name == "foo"
    assert argument_.is_required()
    assert not argument_.is_list()
    assert argument_.description == "Foo description"
    assert argument_.default is None


def test_list_argument() -> None:
    argument_ = Argument("foo", is_list=True, description="Foo description")

    assert argument_.name == "foo"
    assert argument_.is_required()
    assert argument_.is_list()
    assert argument_.description == "Foo description"
    assert argument_.default == []


# Source: tests/io/inputs/test_argv_input.py
def test_parse_arguments() -> None:
    input_ = ArgvInput(["cli.py", "foo"])
    input_.bind(Definition([Argument("name")]))

    assert input_.arguments == {"name": "foo"}


@pytest.mark.parametrize(
    ["args", "options", "expected_options"],
    [
        (["cli.py", "--foo"], lambda: [Option("--foo")], {"foo": True}),
        (
            ["cli.py", "--foo=bar"],
            lambda: [Option("--foo", "-f", flag=False, requires_value=True)],
            {"foo": "bar"},
        ),
        (
            ["cli.py", "--foo", "bar"],
            lambda: [Option("--foo", "-f", flag=False, requires_value=True)],
            {"foo": "bar"},
        ),
        (
            ["cli.py", "--foo="],
            lambda: [Option("--foo", "-f", flag=False, requires_value=False)],
            {"foo": ""},
        ),
        (
            ["cli.py", "--foo=", "bar"],
            lambda: [
                Option("--foo", "-f", flag=False, requires_value=False),
                Argument("name"),
            ],
            {"foo": ""},
        ),
        (
            ["cli.py", "bar", "--foo="],
            lambda: [
                Option("--foo", "-f", flag=False, requires_value=False),
                Argument("name"),
            ],
            {"foo": ""},
        ),
        (
            ["cli.py", "--foo"],
            lambda: [Option("--foo", "-f", flag=False, requires_value=False)],
            {"foo": None},
        ),
        (["cli.py", "-f"], lambda: [Option("--foo", "-f")], {"foo": True}),
        (
            ["cli.py", "-fbar"],
            lambda: [Option("--foo", "-f", flag=False, requires_value=True)],
            {"foo": "bar"},
        ),
        (
            ["cli.py", "-f", "bar"],
            lambda: [Option("--foo", "-f", flag=False, requires_value=True)],
            {"foo": "bar"},
        ),
        (
            ["cli.py", "-f", ""],
            lambda: [Option("--foo", "-f", flag=False, requires_value=False)],
            {"foo": ""},
        ),
        (
            ["cli.py", "-f", "", "foo"],
            lambda: [
                Option("--foo", "-f", flag=False, requires_value=False),
                Argument("name"),
            ],
            {"foo": ""},
        ),
        (
            ["cli.py", "-f", "", "-b"],
            lambda: [
                Option("--foo", "-f", flag=False, requires_value=False),
                Option("--bar", "-b"),
            ],
            {"foo": "", "bar": True},
        ),
        (
            ["cli.py", "-f", "-b", "foo"],
            lambda: [
                Option("--foo", "-f", flag=False, requires_value=False),
                Option("--bar", "-b"),
                Argument("name"),
            ],
            {"foo": None, "bar": True},
        ),
        (
            ["cli.py", "-fb"],
            lambda: [Option("--foo", "-f"), Option("--bar", "-b")],
            {"foo": True, "bar": True},
        ),
        (
            ["cli.py", "-fb", "bar"],
            lambda: [
                Option("--foo", "-f"),
                Option("--bar", "-b", flag=False, requires_value=True),
            ],
            {"foo": True, "bar": "bar"},
        ),
        (
            ["cli.py", "-fbbar"],
            lambda: [
                Option("--foo", "-f", flag=False, requires_value=False),
                Option("--bar", "-b", flag=False, requires_value=False),
            ],
            {"foo": "bbar", "bar": None},
        ),
    ],
    ids=[f"args{i}-options{i}-expected_options{i}" for i in range(17)],
)
def test_parse_options(
    args: list[str],
    options: Callable[[], list[Argument | Option]],
    expected_options: dict[str, str | bool | None],
) -> None:
    input_ = ArgvInput(args)
    input_.bind(Definition(options()))

    assert input_.options == expected_options


# Source: tests/io/inputs/test_option.py
def test_create() -> None:
    opt = Option("option")

    assert opt.name == "option"
    assert opt.shortcut is None
    assert opt.is_flag()
    assert not opt.accepts_value()
    assert not opt.requires_value()
    assert not opt.is_list()
    assert not opt.default


def test_dashed_name() -> None:
    opt = Option("--option")

    assert opt.name == "option"


def test_fail_if_name_is_empty() -> None:
    with pytest.raises(CleoValueError):
        Option("")


def test_fail_if_default_value_provided_for_flag() -> None:
    with pytest.raises(CleoLogicError):
        Option("option", flag=True, default="default")


def test_fail_if_wrong_default_value_for_list_option() -> None:
    with pytest.raises(CleoLogicError):
        Option("option", flag=False, is_list=True, default="default")


def test_shortcut() -> None:
    opt = Option("option", "o")

    assert opt.shortcut == "o"


def test_dashed_shortcut() -> None:
    opt = Option("option", "-o")

    assert opt.shortcut == "o"


def test_multiple_shortcuts() -> None:
    opt = Option("option", "-o|oo|-ooo")

    assert opt.shortcut == "o|oo|ooo"


def test_fail_if_shortcut_is_empty() -> None:
    with pytest.raises(CleoValueError):
        Option("option", "")


def test_optional_value() -> None:
    opt = Option("option", flag=False, requires_value=False)

    assert not opt.is_flag()
    assert opt.accepts_value()
    assert not opt.requires_value()
    assert not opt.is_list()
    assert opt.default is None


def test_optional_value_with_default() -> None:
    opt = Option("option", flag=False, requires_value=False, default="Default")

    assert not opt.is_flag()
    assert opt.accepts_value()
    assert not opt.requires_value()
    assert not opt.is_list()
    assert opt.default == "Default"


def test_required_value() -> None:
    opt = Option("option", flag=False, requires_value=True)

    assert not opt.is_flag()
    assert opt.accepts_value()
    assert opt.requires_value()
    assert not opt.is_list()
    assert opt.default is None


def test_required_value_with_default() -> None:
    opt = Option("option", flag=False, requires_value=True, default="Default")

    assert not opt.is_flag()
    assert opt.accepts_value()
    assert opt.requires_value()
    assert not opt.is_list()
    assert opt.default == "Default"


def test_list() -> None:
    opt = Option("option", flag=False, is_list=True)

    assert not opt.is_flag()
    assert opt.accepts_value()
    assert opt.requires_value()
    assert opt.is_list()
    assert opt.default == []


def test_multi_valued_with_default() -> None:
    opt = Option("option", flag=False, is_list=True, default=["foo", "bar"])

    assert not opt.is_flag()
    assert opt.accepts_value()
    assert opt.requires_value()
    assert opt.is_list()
    assert opt.default == ["foo", "bar"]


# Source: tests/loaders/test_factory_command_loader.py
def command(name: str) -> Command:
    command_ = Command()
    command_.name = name

    return command_


def test_has() -> None:
    loader = FactoryCommandLoader(
        {"foo": lambda: command("foo"), "bar": lambda: command("bar")}
    )

    assert loader.has("foo")
    assert loader.has("bar")
    assert not loader.has("baz")


def test_get() -> None:
    loader = FactoryCommandLoader(
        {"foo": lambda: command("foo"), "bar": lambda: command("bar")}
    )

    assert isinstance(loader.get("foo"), Command)
    assert isinstance(loader.get("bar"), Command)


def test_get_invalid_command_raises_error() -> None:
    loader = FactoryCommandLoader(
        {"foo": lambda: command("foo"), "bar": lambda: command("bar")}
    )

    with pytest.raises(CleoCommandNotFoundError):
        loader.get("baz")


def test_names() -> None:
    loader = FactoryCommandLoader(
        {"foo": lambda: command("foo"), "bar": lambda: command("bar")}
    )

    assert loader.names == ["foo", "bar"]


# Sources: tests/commands/test_command.py and tests/test_application.py
def test_set_application() -> None:
    application = Application()
    command_ = Command()
    command_.set_application(application)

    assert command_.application == application


def test_name_version_getters() -> None:
    application = Application("foo", "bar")

    assert application.name == "foo"
    assert application.display_name == "Foo"
    assert application.version == "bar"


def test_name_version_setter() -> None:
    application = Application("foo", "bar")

    application.set_name("bar")
    application.set_version("foo")

    assert application.name == "bar"
    assert application.display_name == "Bar"
    assert application.version == "foo"

    application.set_display_name("Baz")

    assert application.display_name == "Baz"


# Source: tests/test_helpers.py
def test_argument() -> None:
    arg = argument("foo", "Foo")

    assert arg.description == "Foo"
    assert arg.is_required()
    assert not arg.is_list()
    assert arg.default is None

    arg = argument("foo", "Foo", optional=True, default="bar")

    assert not arg.is_required()
    assert not arg.is_list()
    assert arg.default == "bar"

    arg = argument("foo", "Foo", multiple=True)

    assert arg.is_required()
    assert arg.is_list()
    assert arg.default == []

    arg = argument("foo", "Foo", optional=True, multiple=True, default=["bar"])

    assert not arg.is_required()
    assert arg.is_list()
    assert arg.default == ["bar"]


def test_option() -> None:
    opt = option("foo", "f", "Foo")

    assert opt.description == "Foo"
    assert not opt.accepts_value()
    assert not opt.requires_value()
    assert not opt.is_list()
    assert opt.default is False

    opt = option("foo", "f", "Foo", flag=False)

    assert opt.description == "Foo"
    assert opt.accepts_value()
    assert opt.requires_value()
    assert not opt.is_list()
    assert opt.default is None

    opt = option("foo", "f", "Foo", flag=False, value_required=False)

    assert opt.description == "Foo"
    assert opt.accepts_value()
    assert not opt.requires_value()
    assert not opt.is_list()

    opt = option("foo", "f", "Foo", flag=False, multiple=True)

    assert opt.description == "Foo"
    assert opt.accepts_value()
    assert opt.requires_value()
    assert opt.is_list()
    assert opt.default == []

    opt = option("foo", "f", "Foo", flag=False, default="bar")

    assert opt.description == "Foo"
    assert opt.accepts_value()
    assert opt.requires_value()
    assert not opt.is_list()
    assert opt.default == "bar"
