from __future__ import annotations

import sys

from typing import TYPE_CHECKING
from typing import ClassVar

import pytest

from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import argument
from cleo.helpers import option
from cleo.io.io import IO
from cleo.io.outputs.stream_output import StreamOutput
from cleo.testers.application_tester import ApplicationTester
from cleo.testers.command_tester import CommandTester


if TYPE_CHECKING:
    from collections.abc import Iterator

    from cleo.io.inputs.argument import Argument
    from cleo.io.inputs.option import Option


class SignatureCommand(Command):
    name = "signature:command"
    options: ClassVar[list[Option]] = [
        option("baz", "z", description="Baz"),
        option("bazz", "Z", description="Bazz"),
    ]
    arguments: ClassVar[list[Argument]] = [
        argument("foo", description="Foo"),
        argument("bar", description="Bar", optional=True),
    ]
    help = "help"
    description = "description"

    def handle(self) -> int:
        self.line("handle called")
        return 0


def test_with_signature() -> None:
    command = SignatureCommand()

    assert command.name == "signature:command"
    assert command.description == "description"
    assert command.help == "help"
    assert len(command.definition.arguments) == 2
    assert len(command.definition.options) == 2


class FooCommand(Command):
    name = "foo bar"
    description = "The foo bar command"
    aliases: ClassVar[list[str]] = ["afoobar"]

    def interact(self, io: IO) -> None:
        io.write_line("interact called")

    def handle(self) -> int:
        self.line("called")
        return 0


class Foo1Command(Command):
    name = "foo bar1"
    description = "The foo bar1 command"
    aliases: ClassVar[list[str]] = ["afoobar1"]

    def handle(self) -> int:
        return 0


class Foo2Command(Command):
    name = "foo1 bar"
    description = "The foo1 bar command"
    aliases: ClassVar[list[str]] = ["afoobar2"]

    def handle(self) -> int:
        return 0


class Foo3Command(Command):
    name = "foo3"
    description = "The foo3 bar command"
    aliases: ClassVar[list[str]] = ["foo3"]

    def handle(self) -> int:
        value = self.ask("echo:", default="default input")
        self.line(value)
        return 0


class FooSubNamespaced1Command(Command):
    name = "foo bar baz"
    description = "The foo bar baz command"
    aliases: ClassVar[list[str]] = ["foobarbaz"]

    def handle(self) -> int:
        return 0


class FooSubNamespaced2Command(Command):
    name = "foo baz bam"
    description = "The foo baz bam command"
    aliases: ClassVar[list[str]] = ["foobazbam"]

    def handle(self) -> int:
        return 0


class FooSubNamespaced3Command(Command):
    name = "foo bar"
    description = "The foo bar command"
    aliases: ClassVar[list[str]] = ["foobar"]

    def handle(self) -> int:
        value = self.ask("", default="default input")
        self.line(value)
        return 0


@pytest.fixture()
def app() -> Application:
    return Application()


@pytest.fixture()
def application_tester(app: Application) -> ApplicationTester:
    app.catch_exceptions(False)
    return ApplicationTester(app)


@pytest.fixture()
def argv() -> Iterator[None]:
    current_argv = sys.argv[:]
    yield
    sys.argv = current_argv


def test_all(app: Application) -> None:
    commands = app.all()

    assert isinstance(commands["help"], Command)

    app.add(FooCommand())

    assert len(app.all("foo")) == 1


def test_add(app: Application) -> None:
    foo = FooCommand()
    app.add(foo)
    commands = app.all()

    assert [commands["foo bar"]] == [foo]

    foo1 = Foo1Command()
    app.add(foo1)

    commands = app.all()

    assert [commands["foo bar"], commands["foo bar1"]] == [foo, foo1]


def test_has_get(app: Application) -> None:
    assert app.has("list")
    assert not app.has("afoobar")

    foo = FooCommand()
    app.add(foo)

    assert app.has("foo bar")
    assert app.has("afoobar")
    assert app.get("foo bar") == foo
    assert app.get("afoobar") == foo


def test_silent_help(app: Application) -> None:
    app.catch_exceptions(False)

    tester = ApplicationTester(app)
    tester.execute("-h -q", decorated=False)

    assert tester.io.fetch_output() == ""


def test_get_namespaces(app: Application) -> None:
    app.add(FooCommand())
    app.add(Foo1Command())

    assert app.get_namespaces() == ["foo"]


def test_find_namespace(app: Application) -> None:
    app.add(FooCommand())

    assert app.find_namespace("foo") == "foo"


def test_find_namespace_with_sub_namespaces(app: Application) -> None:
    app.add(FooSubNamespaced1Command())
    app.add(FooSubNamespaced2Command())

    assert app.find_namespace("foo") == "foo"


def test_find(app: Application) -> None:
    app.add(FooCommand())

    assert isinstance(app.find("foo bar"), FooCommand)
    assert isinstance(app.find("afoobar"), FooCommand)


def test_auto_exit(app: Application) -> None:
    app.auto_exits(False)
    assert not app.is_auto_exit_enabled()

    app.auto_exits()
    assert app.is_auto_exit_enabled()


def test_run(app: Application, argv: None) -> None:
    app.catch_exceptions(False)
    app.auto_exits(False)
    command = Foo1Command()
    app.add(command)

    sys.argv = ["console", "foo bar1"]
    app.run()

    assert isinstance(command.io, IO)
    assert isinstance(command.io.output, StreamOutput)
    assert isinstance(command.io.error_output, StreamOutput)
    assert command.io.output.stream == sys.stdout
    assert command.io.error_output.stream == sys.stderr


def test_run_removes_all_output_if_quiet(
    application_tester: ApplicationTester,
) -> None:
    application_tester.execute("list --quiet")

    assert application_tester.io.fetch_output() == ""

    application_tester.execute("list -q")

    assert application_tester.io.fetch_output() == ""


def test_run_with_verbosity(application_tester: ApplicationTester) -> None:
    application_tester.execute("list --verbose")

    assert application_tester.io.is_verbose()

    application_tester.execute("list -v")

    assert application_tester.io.is_verbose()

    application_tester.execute("list -vv")

    assert application_tester.io.is_very_verbose()

    application_tester.execute("list -vvv")

    assert application_tester.io.is_debug()


def test_run_with_input() -> None:
    app = Application()
    command = Foo3Command()
    app.add(command)

    tester = ApplicationTester(app)
    status_code = tester.execute("foo3", inputs="Hello world!")

    assert status_code == 0
    assert tester.io.fetch_output() == "Hello world!\n"


def test_run_namespaced_with_input() -> None:
    app = Application()
    command = FooSubNamespaced3Command()
    app.add(command)

    tester = ApplicationTester(app)
    status_code = tester.execute("foo bar", inputs="Hello world!")

    assert status_code == 0
    assert tester.io.fetch_output() == "Hello world!\n"


@pytest.mark.parametrize(
    "cmd",
    (Foo3Command(), FooSubNamespaced3Command()),
    ids=("cmd0", "cmd1"),
)
def test_run_with_input_and_non_interactive(cmd: Command) -> None:
    app = Application()
    app.add(cmd)

    tester = ApplicationTester(app)
    status_code = tester.execute(f"--no-interaction {cmd.name}", inputs="Hello world!")

    assert status_code == 0
    assert tester.io.fetch_output() == "default input\n"


def test_invalid_shell() -> None:
    app = Application()
    command = app.find("completions")
    tester = CommandTester(command)

    with pytest.raises(ValueError):
        tester.execute("pomodoro")
