from __future__ import annotations

import os
import re
from asyncio import run
from contextlib import contextmanager

from prompt_toolkit.formatted_text import (
    ANSI,
    HTML,
    FormattedText,
    PygmentsTokens,
    Template,
    merge_formatted_text,
    to_formatted_text,
)
from prompt_toolkit import print_formatted_text
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import (
    CompleteEvent,
    FuzzyWordCompleter,
    NestedCompleter,
    PathCompleter,
    WordCompleter,
    merge_completers,
)
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory, InMemoryHistory, ThreadedHistory
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Attrs, Style, SwapLightAndDarkStyleTransformation
from prompt_toolkit.styles import AdjustBrightnessStyleTransformation


def _document_fixture() -> Document:
    return Document(
        "line 1\n" + "line 2\n" + "line 3\n" + "line 4\n", len("line 1\n" + "lin")
    )


@contextmanager
def _chdir(directory):
    old = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(old)


def _write_test_files(test_dir, names=None):
    for name in names or range(10):
        (test_dir / str(name)).write_bytes(b"")


async def _load_history(history):
    result = []
    async for item in history.load():
        result.append(item)
    return result


class _Capture:
    def __init__(self):
        self._data = []

    def write(self, data):
        self._data.append(data)

    @property
    def data(self):
        return "".join(self._data)

    def flush(self):
        pass

    def isatty(self):
        return True

    def fileno(self):
        return -1

import asyncio

import pytest
from pygments.token import Token

from prompt_toolkit import PromptSession, __version__, VERSION, print_formatted_text, prompt
from prompt_toolkit.application import (
    Application,
    create_app_session,
    get_app,
    get_app_or_none,
    get_app_session,
)
from prompt_toolkit.buffer import Buffer, CompletionState, EditReadOnlyBuffer
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    ConditionalCompleter,
    DummyCompleter,
    DynamicCompleter,
    FuzzyCompleter,
    FuzzyWordCompleter,
    NestedCompleter,
    ThreadedCompleter,
    WordCompleter,
    get_common_complete_suffix,
)
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import (
    FormattedText,
    HTML,
    Template,
    fragment_list_to_text,
    merge_formatted_text,
    to_formatted_text,
    to_plain_text,
)
from prompt_toolkit.history import DummyHistory, InMemoryHistory
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.key_binding import ConditionalKeyBindings, KeyBindings, merge_key_bindings
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.styles import Style, merge_styles, parse_color, pygments_token_to_classname
from prompt_toolkit.validation import (
    ConditionalValidator,
    DummyValidator,
    DynamicValidator,
    ValidationError,
    Validator,
)


class CaptureOutput(DummyOutput):
    def __init__(self):
        self.data: list[str] = []

    def write(self, data: str) -> None:
        self.data.append(data)

    def write_raw(self, data: str) -> None:
        self.data.append(data)

    def flush(self) -> None:
        pass


class SmallCompleter(Completer):
    def get_completions(self, document, complete_event):
        yield Completion("abc", start_position=-1)
        yield Completion("ax", start_position=-1)


class FormattedObject:
    def __pt_formatted_text__(self):
        return [("class:object", "OBJ")]

def test_upstream_cli_simple_text_input():
    with create_pipe_input() as inp:
        inp.send_text("hello\r")
        session = PromptSession(input=inp, output=DummyOutput())
        result = session.prompt()
    assert result == "hello"
    assert session.default_buffer.document.text == "hello"

def test_upstream_cli_accept_default_twice():
    with create_pipe_input() as inp:
        session = PromptSession(input=inp, output=DummyOutput())
        assert session.prompt(default="hello", accept_default=True) == "hello"
        assert session.prompt(default="world", accept_default=True) == "world"

def test_generated_application_run_returns_exit_result_and_sets_active_app():
    with create_pipe_input() as pipe_input:
        app = Application(input=pipe_input, output=DummyOutput())
        seen = []

        def pre_run():
            seen.append(get_app() is app)
            seen.append(get_app_or_none() is app)
            app.exit(result="finished")

        assert app.run(pre_run=pre_run) == "finished"
        assert seen == [True, True]
    assert get_app_or_none() is None

def test_generated_create_app_session_supplies_defaults_for_prompt_and_print():
    captured = CaptureOutput()
    with create_pipe_input() as pipe_input:
        pipe_input.send_text("typed\r")
        with create_app_session(input=pipe_input, output=captured):
            assert get_app_session().input is pipe_input
            assert get_app_session().output is captured
            assert prompt("> ") == "typed"
            print_formatted_text("hello", "world", sep="-", end="!")
    assert "".join(captured.data).endswith("hello-world!")

def test_generated_nested_app_session_inherits_parent_output_when_omitted():
    parent = CaptureOutput()
    child = CaptureOutput()
    with create_app_session(output=parent):
        with create_app_session():
            assert get_app_session().output is parent
            print_formatted_text("parent", end="")
        with create_app_session(output=child):
            assert get_app_session().output is child
            print_formatted_text("child", end="")
    assert "".join(parent.data) == "parent"
    assert "".join(child.data) == "child"

def test_generated_prompt_session_accepts_document_default_and_preserves_cursor():
    with create_pipe_input() as pipe_input:
        session = PromptSession(input=pipe_input, output=DummyOutput())
        result = session.prompt(default=Document("hello", 2), accept_default=True)
    assert result == "hello"
    assert session.default_buffer.document.text == "hello"
    assert session.default_buffer.document.cursor_position == 2

def test_generated_prompt_session_uses_supplied_history_object():
    history = InMemoryHistory(["old command"])
    session = PromptSession(history=history, output=DummyOutput())
    assert session.default_buffer.history is history

def test_generated_buffer_document_projection_and_cursor_clamping():
    buffer = Buffer(document=Document("abc", 1))
    assert buffer.document.text == buffer.text == "abc"
    assert buffer.document.cursor_position == buffer.cursor_position == 1
    buffer.cursor_position = 99
    assert buffer.cursor_position == 3
    buffer.cursor_position = -5
    assert buffer.cursor_position == 0
    buffer.text = "x"
    assert buffer.document.text == "x"
    assert buffer.document.cursor_position == 0

def test_generated_completer_async_and_threaded_paths_match_sync_results():
    async def collect():
        direct = []
        async for completion in SmallCompleter().get_completions_async(Document("a"), CompleteEvent()):
            direct.append((completion.text, completion.start_position))
        threaded = []
        async for completion in ThreadedCompleter(SmallCompleter()).get_completions_async(Document("a"), CompleteEvent()):
            threaded.append(completion.text)
        return direct, threaded

    assert asyncio.run(collect()) == ([("abc", -1), ("ax", -1)], ["abc", "ax"])

def test_generated_conditional_and_dynamic_validators_call_wrapped_only_when_needed():
    calls = []
    wrapped = Validator.from_callable(lambda text: calls.append(text) or False, error_message="invalid")
    ConditionalValidator(wrapped, filter=False).validate(Document("skip"))
    assert calls == []
    with pytest.raises(ValidationError):
        ConditionalValidator(wrapped, filter=True).validate(Document("hit"))
    assert calls == ["hit"]
    assert DynamicValidator(lambda: None).validate(Document("ignored")) is None
    with pytest.raises(ValidationError):
        DynamicValidator(lambda: wrapped).validate(Document("dynamic"))
    assert calls == ["hit", "dynamic"]

def test_generated_conditional_and_merged_key_bindings_are_live_views():
    first = KeyBindings()
    second = KeyBindings()

    @first.add("c-a")
    def first_handler(event):
        return None

    merged = merge_key_bindings([first, second])
    assert len(merged.get_bindings_for_keys(("c-a",))) == 1

    @second.add("c-b")
    def second_handler(event):
        return None

    assert len(merged.get_bindings_for_keys(("c-b",))) == 1
    conditional = ConditionalKeyBindings(first, filter=False)
    wrapped_binding = conditional.get_bindings_for_keys(("c-a",))[0]
    assert wrapped_binding.filter() is False
