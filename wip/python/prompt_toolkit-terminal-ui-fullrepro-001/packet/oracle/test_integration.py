import asyncio
from asyncio import run

import pytest

from conftest import CaptureOutput, SmallCompleter, _load_history
from prompt_toolkit import PromptSession, prompt, print_formatted_text
from prompt_toolkit.application import (
    Application,
    create_app_session,
    get_app,
    get_app_or_none,
    get_app_session,
)
from prompt_toolkit.buffer import Buffer, CompletionState
from prompt_toolkit.completion import CompleteEvent, Completion, ThreadedCompleter, WordCompleter, merge_completers
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML, Template, merge_formatted_text, to_formatted_text
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.key_binding import ConditionalKeyBindings, KeyBindings, merge_key_bindings
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.validation import ConditionalValidator, DynamicValidator, ValidationError, Validator

@pytest.mark.depends_on("test_upstream_buffer_initial_state")
def test_upstream_cli_simple_text_input():
    """Seam: state consistency — upstream cli simple text input."""
    with create_pipe_input() as inp:
        inp.send_text("hello\r")
        session = PromptSession(input=inp, output=DummyOutput())
        result = session.prompt()
    assert result == "hello"
    assert session.default_buffer.document.text == "hello"

@pytest.mark.depends_on("test_upstream_buffer_initial_state")
def test_upstream_cli_accept_default_twice():
    """Seam: state consistency — upstream cli accept default twice."""
    with create_pipe_input() as inp:
        session = PromptSession(input=inp, output=DummyOutput())
        assert session.prompt(default="hello", accept_default=True) == "hello"
        assert session.prompt(default="world", accept_default=True) == "world"

@pytest.mark.depends_on("test_generated_application_exit_propagates_exception_instance")
def test_generated_application_run_returns_exit_result_and_sets_active_app():
    """Seam: lifecycle crossing — generated application run returns exit result and sets active app."""
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

@pytest.mark.depends_on("test_upstream_buffer_initial_state", "test_generated_print_formatted_text_file_output_and_argument_error")
def test_generated_create_app_session_supplies_defaults_for_prompt_and_print():
    """Seam: lifecycle crossing — generated create app session supplies defaults for prompt and print."""
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
    """Seam: config interaction — generated nested app session inherits parent output when omitted."""
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

@pytest.mark.depends_on("test_upstream_buffer_initial_state")
def test_generated_prompt_session_accepts_document_default_and_preserves_cursor():
    """Seam: state consistency — generated prompt session accepts document default and preserves cursor."""
    with create_pipe_input() as pipe_input:
        session = PromptSession(input=pipe_input, output=DummyOutput())
        result = session.prompt(default=Document("hello", 2), accept_default=True)
    assert result == "hello"
    assert session.default_buffer.document.text == "hello"
    assert session.default_buffer.document.cursor_position == 2

@pytest.mark.depends_on("test_upstream_history_in_memory")
def test_generated_prompt_session_uses_supplied_history_object():
    """Seam: lifecycle crossing — generated prompt session uses supplied history object."""
    history = InMemoryHistory(["old command"])
    session = PromptSession(history=history, output=DummyOutput())
    assert session.default_buffer.history is history

@pytest.mark.depends_on("test_upstream_buffer_initial_state")
def test_generated_buffer_document_projection_and_cursor_clamping():
    """Seam: state consistency — generated buffer document projection and cursor clamping."""
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

@pytest.mark.depends_on("test_upstream_word_completer_static_word_list")
def test_generated_completer_async_and_threaded_paths_match_sync_results():
    """Seam: state consistency — generated completer async and threaded paths match sync results."""
    async def collect():
        direct = []
        async for completion in SmallCompleter().get_completions_async(Document("a"), CompleteEvent()):
            direct.append((completion.text, completion.start_position))
        threaded = []
        async for completion in ThreadedCompleter(SmallCompleter()).get_completions_async(Document("a"), CompleteEvent()):
            threaded.append(completion.text)
        return direct, threaded

    assert asyncio.run(collect()) == ([("abc", -1), ("ax", -1)], ["abc", "ax"])

@pytest.mark.depends_on("test_generated_validator_from_callable_raises_with_cursor_and_message")
def test_generated_conditional_and_dynamic_validators_call_wrapped_only_when_needed():
    """Seam: state consistency — generated conditional and dynamic validators call wrapped only when needed."""
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

@pytest.mark.depends_on("test_generated_key_bindings_register_remove_and_report_prefixes")
def test_generated_conditional_and_merged_key_bindings_are_live_views():
    """Seam: state consistency — generated conditional and merged key bindings are live views."""
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

# --- composition fix additions (2026-07-20) ---

@pytest.mark.depends_on("test_generated_completion_state_returns_original_or_selected_projection")
def test_generated_completion_state_projects_selected_completion_into_text():
    """Seam: protocol handoff — generated completion state projects selected completion into text."""
    document = Document("ab", 2)
    completions = [Completion("abc", start_position=-2), Completion("ax", start_position=-2)]
    unselected = CompletionState(document, completions, complete_index=None)
    assert unselected.new_text_and_position() == ("ab", 2)
    selected = CompletionState(document, completions, complete_index=0)
    assert selected.new_text_and_position() == ("abc", 3)
    second = CompletionState(document, completions, complete_index=1)
    assert second.new_text_and_position() == ("ax", 2)

@pytest.mark.depends_on("test_upstream_history_in_memory")
@pytest.mark.depends_on("test_upstream_history_file")
def test_generated_file_history_round_trips_across_sessions(tmp_path):
    """Seam: state consistency — generated file history round trips across sessions."""
    filename = str(tmp_path / "history.txt")
    first = FileHistory(filename)
    first.append_string("multi\nline entry")
    first.append_string("plain entry")
    second = FileHistory(filename)
    loaded = run(_load_history(second))
    assert loaded == ["plain entry", "multi\nline entry"]
    assert second.get_strings() == ["multi\nline entry", "plain entry"]

@pytest.mark.depends_on("test_upstream_formatted_text_basic_html", "test_upstream_style_from_dict")
def test_generated_print_formatted_text_renders_html_through_style_pipeline():
    """Seam: protocol handoff — generated print formatted text renders html through style pipeline."""
    fragments = to_formatted_text(HTML("plain <warning>styled</warning>"))
    assert ("", "plain ") in fragments
    assert ("class:warning", "styled") in fragments
    captured = CaptureOutput()
    style = Style.from_dict({"warning": "#ff0000 bold"})
    print_formatted_text(HTML("plain <warning>styled</warning> tail"), style=style, output=captured, end="")
    rendered = "".join(captured.data)
    assert "plain " in rendered
    assert "styled" in rendered
    assert "tail" in rendered

@pytest.mark.depends_on("test_generated_validator_from_callable_raises_with_cursor_and_message")
def test_generated_prompt_validator_receives_current_buffer_document():
    """Seam: state consistency — generated prompt validator receives current buffer document."""
    observed = []
    validator = Validator.from_callable(lambda text: observed.append(text) or True)
    with create_pipe_input() as pipe_input:
        pipe_input.send_text("valid input\r")
        session = PromptSession(
            input=pipe_input,
            output=DummyOutput(),
            validator=validator,
            validate_while_typing=False,
        )
        assert session.prompt() == "valid input"
    assert observed == ["valid input"]


@pytest.mark.depends_on("test_upstream_history_in_memory", "test_upstream_buffer_initial_state")
def test_buffer_reset_appends_to_history_and_reloads():
    """Seam: lifecycle crossing — Buffer.reset appends to history and reload preserves order."""
    history = InMemoryHistory()
    buffer = Buffer(history=history, document=Document("first command"))
    buffer.reset(append_to_history=True)
    buffer.document = Document("second command")
    buffer.reset(append_to_history=True)
    assert history.get_strings() == ["first command", "second command"]
    loaded = run(_load_history(history))
    assert loaded == ["second command", "first command"]


@pytest.mark.depends_on("test_upstream_word_completer_static_word_list", "test_generated_validator_from_callable_raises_with_cursor_and_message")
def test_prompt_with_completer_validator_history_and_test_io_workflow():
    """Seam: lifecycle crossing — prompt session integrates completer, validator, history, and I/O."""
    history = InMemoryHistory(["deploy staging"])
    completer = WordCompleter(["deploy", "destroy"], ignore_case=True)
    validator = Validator.from_callable(
        lambda text: text.startswith("deploy"),
        error_message="command must deploy",
    )
    style = Style.from_dict({"prompt": "ansigreen bold"})

    with create_pipe_input() as inp:
        inp.send_text("deploy prod\r")
        session = PromptSession(
            HTML("<prompt>$ </prompt>"),
            completer=completer,
            history=history,
            validator=validator,
            style=style,
            input=inp,
            output=DummyOutput(),
        )
        result = session.prompt()

    assert result == "deploy prod"
    assert session.default_buffer.history is history


@pytest.mark.depends_on("test_generated_merge_styles_later_overrides_earlier", "test_upstream_formatted_text_basic_html")
def test_style_merge_resolves_through_html_print_pipeline():
    """CVI-N: merged styles resolve HTML class attributes through print pipeline."""
    base_style = Style.from_dict({"warning": "bold"})
    override_style = Style.from_dict({"warning": "#ff0000"})
    merged = merge_styles([base_style, override_style])

    attrs_result = merged.get_attrs_for_style_str("class:warning")
    assert attrs_result.color == "ff0000"
    assert attrs_result.bold is True

    html_fragments = to_formatted_text(HTML("<warning>alert</warning>"))
    assert ("class:warning", "alert") in html_fragments

    captured = CaptureOutput()
    print_formatted_text(HTML("<warning>alert</warning>"), style=merged, output=captured, end="")
    assert "alert" in "".join(captured.data)


def test_buffer_delete_operations_maintain_document_projection():
    """CVI-N: buffer delete operations keep document text and cursor aligned."""
    buffer = Buffer(document=Document("hello world", 5))
    assert buffer.document.text == buffer.text == "hello world"
    assert buffer.document.cursor_position == buffer.cursor_position == 5

    deleted = buffer.delete_before_cursor(3)
    assert deleted == "llo"
    assert buffer.document.text == buffer.text == "he world"
    assert buffer.document.cursor_position == buffer.cursor_position == 2

    deleted_after = buffer.delete(2)
    assert deleted_after == " w"
    assert buffer.document.text == buffer.text == "heorld"
    assert buffer.document.cursor_position == buffer.cursor_position == 2


def test_buffer_editing_preserves_document_text_split_invariant():
    """CVI-N: buffer edits preserve text_before_cursor + text_after_cursor == text."""
    buf = Buffer()
    buf.insert_text("alpha bravo charlie")
    buf.cursor_position = 5
    doc = buf.document
    assert doc.text_before_cursor + doc.text_after_cursor == doc.text
    assert doc.text_before_cursor == "alpha"
    assert doc.text_after_cursor == " bravo charlie"

    buf.insert_text("_extra")
    doc2 = buf.document
    assert doc2.text_before_cursor + doc2.text_after_cursor == doc2.text
    assert "alpha_extra" in doc2.text


# --- new integration tests ---

@pytest.mark.depends_on("test_upstream_formatted_text_template_interpolation")
def test_template_html_fragments_resolve_through_style_pipeline():
    """Seam: protocol handoff — Template+HTML fragments resolve through style pipeline."""
    tmpl = Template("Status: {}")
    fragments = to_formatted_text(tmpl.format(HTML("<b>OK</b>")))
    assert ("", "Status: ") in fragments
    assert ("class:b", "OK") in fragments
    style = Style.from_dict({"b": "bold #00ff00"})
    attrs = style.get_attrs_for_style_str("class:b")
    assert attrs.bold is True
    assert attrs.color == "00ff00"


@pytest.mark.depends_on("test_upstream_formatted_text_basic_html")
def test_merge_formatted_text_through_print_pipeline():
    """Seam: lifecycle crossing — merged formatted text prints through output pipeline."""
    merged = merge_formatted_text([HTML("<b>bold</b>"), " ", HTML("<i>italic</i>")])
    fragments = to_formatted_text(merged)
    assert fragments == [
        ("class:b", "bold"),
        ("", " "),
        ("class:i", "italic"),
    ]
    captured = CaptureOutput()
    print_formatted_text(merged, output=captured, end="")
    rendered = "".join(captured.data)
    assert "bold" in rendered
    assert "italic" in rendered


@pytest.mark.depends_on("test_upstream_word_completer_static_word_list")
def test_merged_completers_match_buffer_document_state():
    """Seam: state consistency — merged completers produce results matching buffer document."""
    c1 = WordCompleter(["alpha", "apex"])
    c2 = WordCompleter(["alpine"])
    merged = merge_completers([c1, c2])
    buf = Buffer()
    buf.insert_text("al")
    doc = buf.document
    completions = list(merged.get_completions(doc, CompleteEvent()))
    assert [(c.text, c.start_position) for c in completions] == [
        ("alpha", -2),
        ("alpine", -2),
    ]
    assert doc.text == buf.text == "al"


@pytest.mark.depends_on("test_upstream_formatted_text_html_fg_bg")
def test_html_format_escapes_values_through_app_session_print():
    """Seam: lifecycle crossing — HTML.format escapes values and prints through app session."""
    html = HTML("<b>{}</b>").format("<script>")
    fragments = to_formatted_text(html)
    assert fragments == [("class:b", "<script>")]
    captured = CaptureOutput()
    with create_app_session(output=captured):
        print_formatted_text(html, end="")
    assert "<script>" in "".join(captured.data)


@pytest.mark.depends_on("test_upstream_history_in_memory")
def test_preloaded_history_buffer_reset_reload_consistency():
    """Seam: state consistency — preloaded history survives buffer reset and reload."""
    history = InMemoryHistory(["old1", "old2"])
    assert run(_load_history(history)) == ["old2", "old1"]
    buf = Buffer(history=history, document=Document("new_entry"))
    buf.reset(append_to_history=True)
    assert history.get_strings() == ["old1", "old2", "new_entry"]
    loaded = run(_load_history(history))
    assert loaded == ["new_entry", "old2", "old1"]
