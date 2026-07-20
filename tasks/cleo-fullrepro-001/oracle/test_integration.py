from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

import pytest

from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import argument
from cleo.helpers import option
from cleo.io.buffered_io import BufferedIO
from cleo.io.inputs.string_input import StringInput
from cleo.io.outputs.output import Verbosity
from cleo.testers.application_tester import ApplicationTester
from cleo.testers.command_tester import CommandTester
from cleo.ui.confirmation_question import ConfirmationQuestion
from cleo.ui.progress_bar import ProgressBar
from cleo.ui.question import Question


if TYPE_CHECKING:
    from cleo.io.inputs.argument import Argument
    from cleo.io.inputs.option import Option


@pytest.fixture()
def io() -> BufferedIO:
    input_ = StringInput("")
    input_.set_stream(StringIO())
    return BufferedIO(input_)


@pytest.fixture()
def ansi_io() -> BufferedIO:
    input_ = StringInput("")
    input_.set_stream(StringIO())
    return BufferedIO(input_, decorated=True)


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any, bool]] = []

    def dispatch(self, first: Any, second: Any) -> Any:
        if isinstance(first, str):
            event_name, event = first, second
        else:
            event, event_name = first, second

        self.calls.append((event_name, event, event.command.handled))
        return event


class EventWorkflowCommand(Command):
    name = "events-probe"
    handled = False

    def handle(self) -> int:
        self.handled = True
        self.line("handled")
        return 0


# Source: tests/events/test_event_dispatcher.py::test_dispatch, behaviorally
# rewritten through Application so no unpublished base event class is required.
def test_dispatch() -> None:
    application = Application()
    command = application.add(EventWorkflowCommand())
    dispatcher = RecordingDispatcher()
    application.set_event_dispatcher(dispatcher)
    tester = ApplicationTester(application)

    assert tester.execute("events-probe") == 0
    assert len(dispatcher.calls) == 2
    assert dispatcher.calls[0][0] != dispatcher.calls[1][0]
    assert [handled for _, _, handled in dispatcher.calls] == [False, True]
    assert all(event.command is command for _, event, _ in dispatcher.calls)
    assert all(event.io.output is tester.io.output for _, event, _ in dispatcher.calls)
    assert tester.io.fetch_output() == "handled\n"


class MultipleArgumentCommand(Command):
    name = "test2"
    description = "Command testing"
    arguments: ClassVar[list[Argument]] = [argument("foo", "Bar", multiple=True)]

    def handle(self) -> int:
        values = self.argument("foo")
        self.line(",".join(values))
        return 0


def test_explicit_multiple_argument() -> None:
    tester = CommandTester(MultipleArgumentCommand())
    tester.execute("1 2 3")

    assert tester.io.fetch_output() == "1,2,3\n"


class ApplicationTesterFooCommand(Command):
    name = "foo"
    description = "Foo command"
    arguments: ClassVar[list[Argument]] = [argument("foo")]
    options: ClassVar[list[Option]] = [option("--bar")]

    def handle(self) -> int:
        self.line(self.argument("foo"))
        if self.option("bar"):
            self.line("--bar activated")
        return 0


class ApplicationTesterFooBarCommand(Command):
    name = "foo bar"
    description = "Foo Bar command"
    arguments: ClassVar[list[Argument]] = [argument("foo")]
    options: ClassVar[list[Option]] = [option("--baz")]

    def handle(self) -> int:
        self.line(self.argument("foo"))
        if self.option("baz"):
            self.line("--baz activated")
        return 0


@pytest.fixture()
def application_tester() -> ApplicationTester:
    application = Application()
    application.add(ApplicationTesterFooCommand())
    application.add(ApplicationTesterFooBarCommand())
    return ApplicationTester(application)


class TestApplicationTester:
    def test_execute(self, application_tester: ApplicationTester) -> None:
        assert application_tester.execute("foo baz --bar") == 0
        assert application_tester.status_code == 0
        assert application_tester.io.fetch_output() == "baz\n--bar activated\n"

    def test_execute_namespace_command(
        self, application_tester: ApplicationTester
    ) -> None:
        application_tester.application.catch_exceptions(False)
        assert application_tester.execute("foo bar baz --baz") == 0
        assert application_tester.status_code == 0
        assert application_tester.io.fetch_output() == "baz\n--baz activated\n"


class CommandTesterFooCommand(Command):
    name = "foo"
    description = "Foo command"
    arguments: ClassVar[list[Argument]] = [
        argument("foo", description="Foo argument")
    ]

    def handle(self) -> int:
        self.line(self.argument("foo"))
        return 0


class CommandTesterFooBarCommand(Command):
    name = "foo bar"

    def handle(self) -> int:
        self.line("foo bar called")
        return 0


@pytest.fixture()
def command_tester() -> CommandTester:
    return CommandTester(CommandTesterFooCommand())


class TestCommandTester:
    def test_execute(self, command_tester: CommandTester) -> None:
        assert command_tester.execute("bar") == 0
        assert command_tester.status_code == 0
        assert command_tester.io.fetch_output() == "bar\n"

    def test_execute_namespace_command(self) -> None:
        application = Application()
        application.add(CommandTesterFooBarCommand())
        tester = CommandTester(application.find("foo bar"))

        assert tester.execute() == 0
        assert tester.status_code == 0
        assert tester.io.fetch_output() == "foo bar called\n"


@pytest.mark.parametrize(
    ("input", "expected", "default"),
    [
        ("", True, True),
        ("", False, False),
        ("y", True, True),
        ("yes", True, True),
        ("n", False, True),
        ("no", False, True),
    ],
)
def test_ask(io: BufferedIO, input: str, expected: bool, default: bool) -> None:
    io.set_user_input(f"{input}\n")
    question = ConfirmationQuestion("Do you like French fries?", default)

    assert question.ask(io) == expected


def test_ask_with_custom_answer(io: BufferedIO) -> None:
    io.set_user_input("j\ny\n")

    question = ConfirmationQuestion(
        "Do you like French fries?", False, r"(?i)^(j|y)"
    )
    assert question.ask(io)

    question = ConfirmationQuestion(
        "Do you like French fries?", False, r"(?i)^(j|y)"
    )
    assert question.ask(io)


def test_display_with_quiet_verbosity(ansi_io: BufferedIO) -> None:
    ansi_io.set_verbosity(Verbosity.QUIET)
    bar = ProgressBar(ansi_io, 50, 0)
    bar.display()

    assert ansi_io.fetch_error() == ""


def test_ask_and_validate(io: BufferedIO) -> None:
    error = "This is not a color!"

    def validator(color: str) -> str:
        if color not in ["white", "black"]:
            raise Exception(error)
        return color

    question = Question("What color was the white horse of Henry IV?", "white")
    question.set_validator(validator)
    question.set_max_attempts(2)

    io.set_user_input("\nblack\n")
    assert question.ask(io) == "white"
    assert question.ask(io) == "black"

    io.set_user_input("green\nyellow\norange\n")
    with pytest.raises(Exception) as exc_info:
        question.ask(io)

    assert str(exc_info.value) == error


def test_no_interaction(io: BufferedIO) -> None:
    io.interactive(False)

    question = Question("Do you have a job?", "not yet")
    assert question.ask(io) == "not yet"
