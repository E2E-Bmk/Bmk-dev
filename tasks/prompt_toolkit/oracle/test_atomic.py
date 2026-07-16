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

def test_upstream_buffer_initial_state():
    buffer = Buffer()
    assert buffer.text == ""
    assert buffer.cursor_position == 0
    assert buffer.document.text == ""
    assert buffer.document.cursor_position == 0

def test_upstream_pathcompleter_files_in_current_directory(tmp_path):
    _write_test_files(tmp_path)
    with _chdir(tmp_path):
        completions = PathCompleter().get_completions(Document(""), CompleteEvent())
        assert sorted(c.text for c in completions) == [str(i) for i in range(10)]

def test_upstream_pathcompleter_files_in_absolute_directory(tmp_path):
    _write_test_files(tmp_path)
    text = str(tmp_path) + os.path.sep
    completions = PathCompleter().get_completions(Document(text), CompleteEvent())
    assert sorted(c.text for c in completions) == [str(i) for i in range(10)]

def test_upstream_pathcompleter_only_directories(tmp_path):
    _write_test_files(tmp_path)
    (tmp_path / "subdir").mkdir()
    with _chdir(tmp_path):
        completer = PathCompleter(only_directories=True)
        assert [c.text for c in completer.get_completions(Document(""), CompleteEvent())] == [
            "subdir"
        ]
        assert list(completer.get_completions(Document("1"), CompleteEvent())) == []

def test_upstream_pathcompleter_min_input_len(tmp_path):
    _write_test_files(tmp_path)
    with _chdir(tmp_path):
        assert list(PathCompleter(min_input_len=1).get_completions(Document(""), CompleteEvent())) == []
        assert [c.text for c in PathCompleter(min_input_len=1).get_completions(Document("1"), CompleteEvent())] == [""]
    for i in range(10):
        (tmp_path / (str(i) * 2)).write_bytes(b"")
    with _chdir(tmp_path):
        assert sorted(c.text for c in PathCompleter(min_input_len=1).get_completions(Document("2"), CompleteEvent())) == ["", "2"]
        assert list(PathCompleter(min_input_len=2).get_completions(Document("2"), CompleteEvent())) == []

def test_upstream_pathcompleter_get_paths_constrains_path(tmp_path):
    _write_test_files(tmp_path)
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    _write_test_files(subdir, "abcdefghij")
    with _chdir(tmp_path):
        completer = PathCompleter(get_paths=lambda: ["subdir"])
        assert [c.text for c in completer.get_completions(Document(""), CompleteEvent())] == list("abcdefghij")

def test_upstream_word_completer_static_word_list():
    completer = WordCompleter(["abc", "def", "aaa"])
    assert [c.text for c in completer.get_completions(Document(""), CompleteEvent())] == ["abc", "def", "aaa"]
    assert [c.text for c in completer.get_completions(Document("a"), CompleteEvent())] == ["abc", "aaa"]
    assert [c.text for c in completer.get_completions(Document("A"), CompleteEvent())] == []
    assert [c.text for c in completer.get_completions(Document("test "), CompleteEvent())] == ["abc", "def", "aaa"]
    assert [c.text for c in completer.get_completions(Document("test a"), CompleteEvent())] == ["abc", "aaa"]

def test_upstream_word_completer_ignore_case():
    completer = WordCompleter(["abc", "def", "aaa"], ignore_case=True)
    assert [c.text for c in completer.get_completions(Document("a"), CompleteEvent())] == ["abc", "aaa"]
    assert [c.text for c in completer.get_completions(Document("A"), CompleteEvent())] == ["abc", "aaa"]

def test_upstream_word_completer_match_middle():
    completer = WordCompleter(["abc", "def", "abca"], match_middle=True)
    assert [c.text for c in completer.get_completions(Document("bc"), CompleteEvent())] == ["abc", "abca"]

def test_upstream_word_completer_sentence():
    completer = WordCompleter(["hello world", "www", "hello www", "hello there"], sentence=True)
    assert [c.text for c in completer.get_completions(Document("hello w"), CompleteEvent())] == [
        "hello world",
        "hello www",
    ]
    completer = WordCompleter(["hello world", "www", "hello www", "hello there"], sentence=False)
    assert [c.text for c in completer.get_completions(Document("hello w"), CompleteEvent())] == ["www"]

def test_upstream_word_completer_dynamic_word_list():
    calls = [0]

    def get_words():
        calls[0] += 1
        return ["abc", "def", "aaa"]

    completer = WordCompleter(get_words)
    assert [c.text for c in completer.get_completions(Document(""), CompleteEvent())] == ["abc", "def", "aaa"]
    assert calls[0] == 1
    assert [c.text for c in completer.get_completions(Document("a"), CompleteEvent())] == ["abc", "aaa"]
    assert calls[0] == 2

def test_upstream_word_completer_pattern():
    completer = WordCompleter(
        ["abc", "a.b.c", "a.b", "xyz"],
        pattern=re.compile(r"^([a-zA-Z0-9_.]+|[^a-zA-Z0-9_.\s]+)"),
    )
    assert [c.text for c in completer.get_completions(Document("a."), CompleteEvent())] == ["a.b.c", "a.b"]
    assert [c.text for c in WordCompleter(["abc", "a.b.c", "a.b", "xyz"]).get_completions(Document("a."), CompleteEvent())] == []

def test_upstream_fuzzy_completer():
    collection = [
        "migrations.py",
        "django_migrations.py",
        "django_admin_log.py",
        "api_user.doc",
        "user_group.doc",
        "users.txt",
        "accounts.txt",
        "123.py",
        "test123test.py",
    ]
    completer = FuzzyWordCompleter(collection)
    assert [c.text for c in completer.get_completions(Document("txt"), CompleteEvent())] == ["users.txt", "accounts.txt"]
    assert [c.text for c in completer.get_completions(Document("djmi"), CompleteEvent())] == [
        "django_migrations.py",
        "django_admin_log.py",
    ]
    assert [c.text for c in completer.get_completions(Document("mi"), CompleteEvent())] == [
        "migrations.py",
        "django_migrations.py",
        "django_admin_log.py",
    ]
    assert [c.text for c in completer.get_completions(Document("test "), CompleteEvent())] == collection

def test_upstream_nested_completer():
    completer = NestedCompleter.from_nested_dict(
        {"show": {"version": None, "clock": None, "interfaces": None, "ip": {"interface": {"brief"}}}, "exit": None}
    )
    assert {c.text for c in completer.get_completions(Document(""), CompleteEvent())} == {"show", "exit"}
    assert {c.text for c in completer.get_completions(Document("s"), CompleteEvent())} == {"show"}
    assert {c.text for c in completer.get_completions(Document("show "), CompleteEvent())} == {"version", "clock", "interfaces", "ip"}
    assert {c.text for c in completer.get_completions(Document("show i"), CompleteEvent())} == {"ip", "interfaces"}
    assert {c.text for c in completer.get_completions(Document("show ip interface br"), CompleteEvent())} == {"brief"}

def test_upstream_merge_completers_deduplicate():
    def create(deduplicate):
        return merge_completers(
            [WordCompleter(["hello", "world", "abc", "def"]), WordCompleter(["xyz", "xyz", "abc", "def"])],
            deduplicate=deduplicate,
        )

    assert len(list(create(False).get_completions(Document(""), CompleteEvent()))) == 8
    assert len(list(create(True).get_completions(Document(""), CompleteEvent()))) == 5

def test_upstream_document_current_char():
    document = _document_fixture()
    assert document.current_char == "e"
    assert document.char_before_cursor == "n"

def test_upstream_document_text_before_cursor():
    assert _document_fixture().text_before_cursor == "line 1\nlin"

def test_upstream_document_text_after_cursor():
    assert _document_fixture().text_after_cursor == "e 2\n" + "line 3\n" + "line 4\n"

def test_upstream_document_lines():
    assert _document_fixture().lines == ["line 1", "line 2", "line 3", "line 4", ""]

def test_upstream_document_line_count():
    assert _document_fixture().line_count == 5

def test_upstream_document_current_line_before_cursor():
    assert _document_fixture().current_line_before_cursor == "lin"

def test_upstream_document_current_line_after_cursor():
    assert _document_fixture().current_line_after_cursor == "e 2"

def test_upstream_document_current_line():
    assert _document_fixture().current_line == "line 2"

def test_upstream_document_cursor_position_row_col():
    document = _document_fixture()
    assert document.cursor_position_row == 1
    assert document.cursor_position_col == 3
    empty = Document("", 0)
    assert empty.cursor_position_row == 0
    assert empty.cursor_position_col == 0

def test_upstream_document_translate_index_to_position():
    document = _document_fixture()
    assert document.translate_index_to_position(len("line 1\nline 2\nlin")) == (2, 3)
    assert document.translate_index_to_position(0) == (0, 0)

def test_upstream_document_is_cursor_at_the_end():
    assert Document("hello", 5).is_cursor_at_the_end
    assert not Document("hello", 4).is_cursor_at_the_end

def test_upstream_document_get_word_before_cursor_pattern():
    document = Document(text="foobar ", cursor_position=len("foobar "))
    pattern = re.compile(r"([a-zA-Z0-9_]+|[^a-zA-Z0-9_\s]+)")
    assert document.get_word_before_cursor() == ""
    assert document.get_word_before_cursor(pattern=pattern) == ""

def test_upstream_formatted_text_basic_html():
    html = HTML("<i><b>hello</b>world<strong>test</strong></i>after")
    assert to_formatted_text(html) == [
        ("class:i,b", "hello"),
        ("class:i", "world"),
        ("class:i,strong", "test"),
        ("", "after"),
    ]
    assert isinstance(to_formatted_text(html), FormattedText)

def test_upstream_formatted_text_html_fg_bg():
    html = HTML('<style bg="ansired" fg="#ff0000">hello <world fg="ansiblue">world</world></style>')
    assert to_formatted_text(html) == [
        ("fg:#ff0000 bg:ansired", "hello "),
        ("class:world fg:ansiblue bg:ansired", "world"),
    ]

def test_upstream_formatted_text_ansi_formatting():
    value = ANSI("\x1b[32mHe\x1b[45mllo")
    assert to_formatted_text(value) == [
        ("ansigreen", "H"),
        ("ansigreen", "e"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "o"),
    ]
    assert isinstance(to_formatted_text(value), FormattedText)

def test_upstream_formatted_text_ansi_dim():
    assert to_formatted_text(ANSI("\x1b[2mhello\x1b[0m")) == [
        ("dim", "h"),
        ("dim", "e"),
        ("dim", "l"),
        ("dim", "l"),
        ("dim", "o"),
    ]

def test_upstream_formatted_text_ansi_256_color():
    assert to_formatted_text(ANSI("\x1b[38;5;124mtest")) == [
        ("#af0000", "t"),
        ("#af0000", "e"),
        ("#af0000", "s"),
        ("#af0000", "t"),
    ]

def test_upstream_formatted_text_ansi_true_color():
    assert to_formatted_text(ANSI("\033[38;2;144;238;144m$\033[0;39;49m ")) == [
        ("#90ee90", "$"),
        ("ansidefault bg:ansidefault", " "),
    ]

def test_upstream_formatted_text_template_interpolation():
    value = Template("a{}b{}c").format(HTML("<b>hello</b>"), "world")
    assert to_formatted_text(value) == [
        ("", "a"),
        ("class:b", "hello"),
        ("", "b"),
        ("", "world"),
        ("", "c"),
    ]

def test_upstream_formatted_text_html_interpolation():
    value = HTML("<b>{:02d}</b><u>{:.3f}</u>").format(3, 3.14159)
    assert to_formatted_text(value) == [("class:b", "03"), ("class:u", "3.142")]

def test_upstream_formatted_text_merge():
    result = merge_formatted_text([HTML("<u>hello</u>"), HTML("<b>world</b>")])
    assert to_formatted_text(result) == [("class:u", "hello"), ("class:b", "world")]

def test_upstream_formatted_text_pygments_tokens():
    text = [(("A", "B"), "hello"), (("C", "D", "E"), "hello"), ((), "world")]
    assert to_formatted_text(PygmentsTokens(text)) == [
        ("class:pygments.a.b", "hello"),
        ("class:pygments.c.d.e", "hello"),
        ("class:pygments", "world"),
    ]

def test_upstream_history_in_memory():
    history = InMemoryHistory()
    history.append_string("hello")
    history.append_string("world")
    assert run(_load_history(history)) == ["world", "hello"]
    assert run(_load_history(history)) == ["world", "hello"]
    history.append_string("test3")
    assert run(_load_history(history)) == ["test3", "world", "hello"]
    assert run(_load_history(InMemoryHistory(["abc", "def"]))) == ["def", "abc"]

def test_upstream_history_file(tmp_path):
    histfile = tmp_path / "history"
    history = FileHistory(str(histfile))
    history.append_string("hello")
    history.append_string("world")
    assert run(_load_history(history)) == ["world", "hello"]
    history.append_string("test3")
    assert run(_load_history(FileHistory(str(histfile)))) == ["test3", "world", "hello"]

def test_upstream_history_threaded_file(tmp_path):
    histfile = tmp_path / "history"
    history = ThreadedHistory(FileHistory(str(histfile)))
    history.append_string("hello")
    history.append_string("world")
    assert run(_load_history(history)) == ["world", "hello"]
    history.append_string("test3")
    assert run(_load_history(ThreadedHistory(FileHistory(str(histfile))))) == ["test3", "world", "hello"]

def test_upstream_history_threaded_in_memory():
    history = ThreadedHistory(InMemoryHistory())
    history.append_string("hello")
    history.append_string("world")
    assert run(_load_history(history)) == ["world", "hello"]
    history.append_string("test3")
    assert run(_load_history(history)) == ["test3", "world", "hello"]
    assert run(_load_history(ThreadedHistory(InMemoryHistory(["abc", "def"])))) == ["def", "abc"]

def test_upstream_print_formatted_text_plain_fragments():
    capture = _Capture()
    print_formatted_text([("", "hello"), ("", "world")], file=capture)
    assert "hello" in capture.data
    assert "world" in capture.data

def test_upstream_print_formatted_text_carriage_return_text():
    capture = _Capture()
    print_formatted_text("hello\r\n", file=capture)
    assert "hello" in capture.data

def test_upstream_style_from_dict():
    style = Style.from_dict({"a": "#ff0000 bold underline strike italic", "b": "bg:#00ff00 blink reverse"})
    assert style.get_attrs_for_style_str("class:a") == Attrs("ff0000", "", True, True, True, True, False, False, False, False)
    assert style.get_attrs_for_style_str("class:b") == Attrs("", "00ff00", False, False, False, False, True, True, False, False)
    assert style.get_attrs_for_style_str("class:a #00ff00") == Attrs("00ff00", "", True, True, True, True, False, False, False, False)

def test_upstream_style_class_combinations_latest_specific_rule():
    style = Style([("a", "#0000ff"), ("b", "#00ff00"), ("a b", "#ff0000")])
    expected = Attrs("ff0000", "", False, False, False, False, False, False, False, False)
    assert style.get_attrs_for_style_str("class:a class:b") == expected
    assert style.get_attrs_for_style_str("class:b,a") == expected

def test_upstream_style_class_combinations_order_priority():
    style = Style([("a b", "#ff0000"), ("b", "#00ff00"), ("a", "#0000ff")])
    assert style.get_attrs_for_style_str("class:a class:b") == Attrs("00ff00", "", False, False, False, False, False, False, False, False)
    assert style.get_attrs_for_style_str("class:b class:a") == Attrs("0000ff", "", False, False, False, False, False, False, False, False)

def test_upstream_style_substyles():
    style = Style([("a.b", "#ff0000 bold"), ("a", "#0000ff"), ("b", "#00ff00"), ("b.c", "#0000ff italic")])
    assert style.get_attrs_for_style_str("class:a") == Attrs("0000ff", "", False, False, False, False, False, False, False, False)
    assert style.get_attrs_for_style_str("class:a.b.c") == Attrs("ff0000", "", True, False, False, False, False, False, False, False)
    assert style.get_attrs_for_style_str("class:b.c.d") == Attrs("0000ff", "", False, False, False, True, False, False, False, False)

def test_upstream_style_swap_light_and_dark_transformation():
    transformation = SwapLightAndDarkStyleTransformation()
    before = Attrs("440000", "888844", True, True, True, True, False, False, False, False)
    after = Attrs("ffbbbb", "bbbb76", True, True, True, True, False, False, False, False)
    assert transformation.transform_attrs(before) == after
    before = Attrs("ansired", "ansiblack", True, True, True, True, False, False, False, False)
    after = Attrs("ansibrightred", "ansiwhite", True, True, True, True, False, False, False, False)
    assert transformation.transform_attrs(before) == after

def test_upstream_style_adjust_brightness_transformation():
    default = Attrs("", "", False, False, False, False, False, False, False, False)
    tr = AdjustBrightnessStyleTransformation(0.5, 1.0)
    assert tr.transform_attrs(default._replace(color="ff0000")).color == "ff7f7f"
    assert tr.transform_attrs(default._replace(color="00ffaa")).color == "7fffd4"
    assert tr.transform_attrs(default._replace(color="00ffaa", bgcolor="white")).color == "00ffaa"
    assert tr.transform_attrs(default._replace(color="ansidefault")).color == "ansidefault"

def test_generated_installable_surface_version_exports_are_consistent():
    assert isinstance(__version__, str)
    assert isinstance(VERSION, tuple)
    assert __version__.split(".")[:3] == [str(part) for part in VERSION[:3]]

def test_generated_application_exit_propagates_exception_instance():
    with create_pipe_input() as pipe_input:
        app = Application(input=pipe_input, output=DummyOutput())

        def pre_run():
            app.exit(exception=RuntimeError("stop"))

        with pytest.raises(RuntimeError):
            app.run(pre_run=pre_run)

def test_generated_application_exit_rejects_result_and_exception_together():
    with create_pipe_input() as pipe_input:
        app = Application(input=pipe_input, output=DummyOutput())
        with pytest.raises(AssertionError):
            app.exit(result="value", exception=RuntimeError)

def test_generated_prompt_session_pre_run_exception_is_propagated():
    with create_pipe_input() as pipe_input:
        session = PromptSession(input=pipe_input, output=DummyOutput())
        with pytest.raises(RuntimeError):
            session.prompt(pre_run=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

def test_generated_buffer_readonly_blocks_normal_mutation_but_bypass_updates():
    buffer = Buffer(read_only=True)
    with pytest.raises(EditReadOnlyBuffer):
        buffer.text = "blocked"
    with pytest.raises(EditReadOnlyBuffer):
        buffer.document = Document("blocked")
    buffer.set_document(Document("allowed"), bypass_readonly=True)
    assert buffer.text == "allowed"

def test_generated_completion_state_returns_original_or_selected_projection():
    state = CompletionState(Document("hel", 3), [Completion("hello", -3), Completion("help", -3)])
    assert state.new_text_and_position() == ("hel", 3)
    state.go_to_index(0)
    assert state.new_text_and_position() == ("hello", 5)

def test_generated_completion_display_meta_and_event_errors():
    completion = Completion("inserted", display="Shown", display_meta=lambda: "Meta")
    assert Completion("plain").display_text == "plain"
    assert completion.display_text == "Shown"
    assert completion.display_meta_text == "Meta"
    with pytest.raises(AssertionError):
        Completion("bad", start_position=1)
    with pytest.raises(AssertionError):
        CompleteEvent(text_inserted=True, completion_requested=True)

def test_generated_completer_variants_delegate_or_suppress_as_documented():
    assert list(DummyCompleter().get_completions(Document("a"), CompleteEvent())) == []
    assert list(DynamicCompleter(lambda: None).get_completions(Document("a"), CompleteEvent())) == []
    assert list(ConditionalCompleter(WordCompleter(["abc"]), filter=False).get_completions(Document("a"), CompleteEvent())) == []
    assert [c.text for c in FuzzyCompleter(WordCompleter(["alpha", "beta"]), enable_fuzzy=False).get_completions(Document("a"), CompleteEvent())] == ["alpha"]
    with pytest.raises(AssertionError):
        FuzzyCompleter(WordCompleter(["x"]), pattern="abc")

def test_generated_nested_fuzzy_and_common_suffix_completion_helpers():
    nested = NestedCompleter.from_nested_dict({"show": {"version": None, "clock": None}, "exit": None})
    assert [c.text for c in nested.get_completions(Document(""), CompleteEvent())] == ["show", "exit"]
    assert [c.text for c in nested.get_completions(Document("show v"), CompleteEvent())] == ["version"]
    assert [c.text for c in FuzzyWordCompleter(["alpha", "alpine", "beta"]).get_completions(Document("ap"), CompleteEvent())] == ["alpha", "alpine"]
    assert get_common_complete_suffix(Document("he"), [Completion("hello", -2), Completion("help", -2)]) == "l"
    assert get_common_complete_suffix(Document("he"), [Completion("Xhello", -1), Completion("Yhelp", -1)]) == ""

def test_generated_history_backends_load_and_store_public_order():
    history = InMemoryHistory(["one", "two"])

    async def load_all(hist):
        return [item async for item in hist.load()]

    assert asyncio.run(load_all(history)) == ["two", "one"]
    assert history.get_strings() == ["one", "two"]
    history.append_string("three")
    assert asyncio.run(load_all(history)) == ["three", "two", "one"]
    assert history.get_strings() == ["one", "two", "three"]
    assert asyncio.run(load_all(DummyHistory())) == []

def test_generated_validator_variants_accept_or_raise_with_public_fields():
    validator = Validator.from_callable(lambda text: text.startswith("ok"), error_message="bad", move_cursor_to_end=True)
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(Document("nope"))
    assert exc_info.value.cursor_position == 4
    assert exc_info.value.message == "bad"
    assert DummyValidator().validate(Document("anything")) is None

def test_generated_key_bindings_register_remove_and_report_prefixes():
    bindings = KeyBindings()
    with pytest.raises(AssertionError):
        bindings.add()
    with pytest.raises(ValueError):
        bindings.add("invalid-key-name")

    @bindings.add("c-a")
    def handler(event):
        return "handled"

    assert len(bindings.get_bindings_for_keys(("c-a",))) == 1
    assert len(bindings.get_bindings_starting_with_keys(())) == 1
    bindings.remove(handler)
    assert bindings.get_bindings_for_keys(("c-a",)) == []
    with pytest.raises(ValueError):
        bindings.remove(handler)

def test_generated_formatted_text_conversion_template_and_plain_text_helpers():
    assert to_formatted_text(None) == FormattedText([])
    assert to_formatted_text("abc") == FormattedText([("", "abc")])
    assert to_formatted_text(FormattedObject()) == FormattedText([("class:object", "OBJ")])
    assert to_formatted_text(lambda: "abc") == FormattedText([("", "abc")])
    assert to_formatted_text("abc", style="class:root") == FormattedText([("class:root ", "abc")])
    with pytest.raises(ValueError):
        to_formatted_text(object(), auto_convert=False)
    assert to_plain_text(to_formatted_text(123, auto_convert=True)) == "123"
    assert to_plain_text(Template("A {} B {}").format("x", HTML("<b>y</b>"))) == "A x B y"
    with pytest.raises(AssertionError):
        to_formatted_text(Template("A {}").format("x", "y"))
    assert merge_formatted_text(["a", FormattedText([("class:b", "b")])])() == FormattedText([("", "a"), ("class:b", "b")])
    assert fragment_list_to_text([("style", "a"), ("", "b")]) == "ab"

def test_generated_print_formatted_text_file_output_and_argument_error():
    captured = CaptureOutput()
    print_formatted_text("a", "b", sep="-", end="!", output=captured)
    assert "".join(captured.data) == "a-b!"
    with pytest.raises(AssertionError):
        print_formatted_text("x", output=CaptureOutput(), file=object())

def test_generated_style_color_parsing_merge_and_pygments_classname():
    assert parse_color("ansired") == "ansired"
    assert parse_color("red") == "ff0000"
    assert parse_color("#abc") == "aabbcc"
    assert parse_color("#aabbcc") == "aabbcc"
    assert parse_color("default") == "default"
    assert parse_color("") == ""
    with pytest.raises(ValueError):
        parse_color("not a color")
    style = merge_styles([Style.from_dict({"a": "ansired"}), Style.from_dict({"a": "ansiblue bold"})])
    attrs = style.get_attrs_for_style_str("class:a")
    assert attrs.color == "ansiblue"
    assert attrs.bold is True
    assert pygments_token_to_classname(Token.Name.Function) == "pygments.name.function"

def test_generated_error_semantics_public_constructor_failures():
    with pytest.raises(AssertionError):
        Document("abc", 4)
    with pytest.raises(AssertionError):
        WordCompleter(["x"], WORD=True, sentence=True)
    with pytest.raises(NotImplementedError):
        DummyOutput().fileno()
