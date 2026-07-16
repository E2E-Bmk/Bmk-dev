# prompt_toolkit Specification

## Product Overview

`prompt_toolkit` is a pure Python library for building interactive command-line prompts and terminal applications. It provides a high-level `prompt()` function, reusable `PromptSession` objects, a full-screen `Application` object, and public building blocks for editable text buffers, immutable document views, completions, validation, history, key bindings, formatted text, styling, and testable input/output.

The library is designed around explicit objects instead of process-wide prompt state. A caller must be able to create multiple independent sessions, applications, histories, styles, and I/O sessions in one Python process.

## Scope

This specification covers:

- Prompt input through `prompt()` and `PromptSession`.
- Full-screen application lifecycle through `Application.run()` and `Application.exit()`.
- Current application/session helpers in `prompt_toolkit.application`.
- Editable text state through `Buffer` and immutable text views through `Document`.
- Completion objects and completers, including word, nested, fuzzy, path, dynamic, conditional, threaded, merged, and dummy completers.
- History backends, including memory, file, threaded, and dummy histories.
- Validation objects and `ValidationError`.
- Key binding registration, filtering, merging, eager handling, key aliases, and handler invocation.
- Formatted text inputs, conversion, plain-text projection, HTML/ANSI/Pygments adapters, and formatted printing.
- Style sheets, color parsing, class expansion, style merging, color-depth names, and documented style transformations.
- Unit-test I/O helpers through `create_pipe_input`, `PipeInput`, `DummyOutput`, and `create_app_session`.

## Installable Surface

The package is installed as `prompt_toolkit` and is imported from Python. The primary top-level imports are:

```python
from prompt_toolkit import Application, PromptSession, prompt
from prompt_toolkit import print_formatted_text, HTML, ANSI
from prompt_toolkit import __version__, VERSION
```

Documented subpackage imports include:

```python
from prompt_toolkit.application import (
    AppSession, create_app_session, create_app_session_from_tty,
    get_app, get_app_or_none, get_app_session, in_terminal, run_in_terminal,
)
from prompt_toolkit.buffer import Buffer, CompletionState, EditReadOnlyBuffer
from prompt_toolkit.completion import (
    CompleteEvent, Completer, Completion, ConditionalCompleter,
    DummyCompleter, DynamicCompleter, FuzzyCompleter, FuzzyWordCompleter,
    NestedCompleter, PathCompleter, ThreadedCompleter, WordCompleter,
    get_common_complete_suffix, merge_completers,
)
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import (
    ANSI, HTML, FormattedText, PygmentsTokens, Template,
    fragment_list_to_text, merge_formatted_text, to_formatted_text, to_plain_text,
)
from prompt_toolkit.history import (
    DummyHistory, FileHistory, History, InMemoryHistory, ThreadedHistory,
)
from prompt_toolkit.input import create_input, create_pipe_input
from prompt_toolkit.key_binding import (
    ConditionalKeyBindings, KeyBindings, KeyBindingsBase,
    KeyPress, KeyPressEvent, merge_key_bindings,
)
from prompt_toolkit.output import ColorDepth, DummyOutput
from prompt_toolkit.styles import (
    ANSI_COLOR_NAMES, Attrs, Priority, Style,
    AdjustBrightnessStyleTransformation, SwapLightAndDarkStyleTransformation,
    merge_styles, parse_color, pygments_token_to_classname,
    style_from_pygments_cls, style_from_pygments_dict,
)
from prompt_toolkit.validation import (
    ConditionalValidator, DummyValidator, DynamicValidator,
    ThreadedValidator, ValidationError, Validator,
)
```

There is no required command-line entry point for the covered surface.

## Public API

### Prompt and Application

`prompt(message=None, *, history=None, editing_mode=None, refresh_interval=None, vi_mode=None, lexer=None, completer=None, complete_in_thread=None, is_password=None, key_bindings=None, bottom_toolbar=None, style=None, color_depth=None, cursor=None, include_default_pygments_style=None, style_transformation=None, swap_light_and_dark_colors=None, rprompt=None, multiline=None, prompt_continuation=None, wrap_lines=None, enable_history_search=None, search_ignore_case=None, complete_while_typing=None, validate_while_typing=None, complete_style=None, auto_suggest=None, validator=None, clipboard=None, mouse_support=None, input_processors=None, placeholder=None, reserve_space_for_menu=None, enable_system_prompt=None, enable_suspend=None, enable_open_in_editor=None, tempfile_suffix=None, tempfile=None, show_frame=None, default="", accept_default=False, pre_run=None, set_exception_handler=True, handle_sigint=True, in_thread=False, inputhook=None) -> str`

`PromptSession(message="", *, multiline=False, wrap_lines=True, is_password=False, vi_mode=False, editing_mode=EditingMode.EMACS, complete_while_typing=True, validate_while_typing=True, enable_history_search=False, search_ignore_case=False, lexer=None, enable_system_prompt=False, enable_suspend=False, enable_open_in_editor=False, validator=None, completer=None, complete_in_thread=False, reserve_space_for_menu=8, complete_style=CompleteStyle.COLUMN, auto_suggest=None, style=None, style_transformation=None, swap_light_and_dark_colors=False, color_depth=None, cursor=None, include_default_pygments_style=True, history=None, clipboard=None, prompt_continuation=None, rprompt=None, bottom_toolbar=None, mouse_support=False, input_processors=None, placeholder=None, key_bindings=None, erase_when_done=False, tempfile_suffix=".txt", tempfile=None, refresh_interval=0, show_frame=False, input=None, output=None, interrupt_exception=KeyboardInterrupt, eof_exception=EOFError)`

`PromptSession.prompt(...)` accepts the same prompt options as `prompt()`, except `history` belongs to the session constructor. It also accepts `default`, `accept_default`, `pre_run`, `set_exception_handler`, `handle_sigint`, `in_thread`, and `inputhook`.

`Application(layout=None, key_bindings=None, clipboard=None, full_screen=False, color_depth=None, erase_when_done=False, reverse_vi_search_direction=False, min_redraw_interval=None, max_render_postpone_time=0.01, refresh_interval=None, terminal_size_polling_interval=0.5, mouse_support=False, paste_mode=False, editing_mode=EditingMode.EMACS, enable_page_navigation_bindings=None, input=None, output=None, ...)` glues layout, key bindings, style, input, output, and event-loop lifecycle. `Application.run(pre_run=None, set_exception_handler=True, handle_sigint=True, in_thread=False, inputhook=None)` blocks until `Application.exit()` completes the run. `Application.exit(result=None, exception=None, style="")` ends the active run with either a result or an exception.

### Buffer and Document

`Document(text="", cursor_position=None, selection=None)` is an immutable text/cursor view. It exposes `text`, `cursor_position`, `selection`, `current_char`, `char_before_cursor`, `text_before_cursor`, `text_after_cursor`, `current_line`, `current_line_before_cursor`, `current_line_after_cursor`, `lines`, `line_count`, `cursor_position_row`, `cursor_position_col`, cursor movement helpers, search helpers, word-boundary helpers, and selection-range helpers.

`Buffer(completer=None, auto_suggest=None, history=None, validator=None, tempfile_suffix="", tempfile="", name="", complete_while_typing=False, validate_while_typing=False, enable_history_search=False, document=None, accept_handler=None, read_only=False, multiline=True, max_number_of_completions=10000, on_text_changed=None, on_text_insert=None, on_cursor_position_changed=None, on_completions_changed=None, on_suggestion_set=None)` holds editable text, cursor position, history, completion state, validation state, suggestion state, selection state, and undo/redo state. Its `document` property returns a `Document` projection of current `text`, `cursor_position`, and selection.

### Completion

`Completion(text, start_position=0, display=None, display_meta=None, style="", selected_style="")` describes a candidate insertion. `Completer.get_completions(document, complete_event)` returns an iterable of `Completion` objects. `Completer.get_completions_async(document, complete_event)` returns an async stream of completions.

`CompleteEvent(text_inserted=False, completion_requested=False)` tells a completer whether completion was requested by typing or by an explicit completion action. `WordCompleter`, `NestedCompleter`, `FuzzyCompleter`, `FuzzyWordCompleter`, `PathCompleter`, `ThreadedCompleter`, `DynamicCompleter`, `ConditionalCompleter`, `DummyCompleter`, `merge_completers`, and `get_common_complete_suffix` provide the documented completion helpers.

### History and Validation

`History` implementations provide `load()`, `get_strings()`, `append_string(string)`, `load_history_strings()`, and `store_string(string)`. `InMemoryHistory`, `FileHistory`, `ThreadedHistory`, and `DummyHistory` are public history backends.

`ValidationError(cursor_position=0, message="")` is raised by validators and exposes `cursor_position` and `message`. `Validator.validate(document)` must return `None` for valid input and raise `ValidationError` for invalid input. `Validator.from_callable(validate_func, error_message="Invalid input", move_cursor_to_end=False)` creates a validator from a string predicate.

### Key Bindings

`KeyBindings.add(*keys, filter=True, eager=False, is_global=False, save_before=lambda event: True, record_in_macro=True)` returns a decorator that registers a key handler. `KeyBindings.remove(handler_or_key_sequence)` removes a registered binding. `ConditionalKeyBindings(key_bindings, filter=True)` wraps a set of bindings behind a filter. `merge_key_bindings([bindings1, bindings2, ...])` returns a registry view over multiple registries.

### Formatted Text, Printing, and Styles

Formatted text inputs are strings, `HTML`, `ANSI`, `FormattedText` lists of `(style, text)` fragments, `PygmentsTokens`, objects implementing `__pt_formatted_text__`, callables returning formatted text, and `None`.

`to_formatted_text(value, style="", auto_convert=False)` returns a `FormattedText` instance. `print_formatted_text(*values, sep=" ", end="\n", file=None, flush=False, style=None, output=None, color_depth=None, style_transformation=None, include_default_pygments_style=True)` prints plain or formatted values, following Python `print` conventions while applying terminal styles.

`Style(style_rules)` accepts ordered `(class_names, style_string)` rules. `Style.from_dict(style_dict, priority=Priority.DICT_KEY_ORDER)` builds a style from a dictionary. `merge_styles(styles)` combines styles. `parse_color(text)` validates and normalizes ANSI names, named colors, and three- or six-digit `#`-prefixed hex colors.

`Attrs(color, bgcolor, bold, underline, strike, italic, blink, reverse, hidden, dim)` is the public resolved-style value returned by style lookups and accepted by style transformations. Its fields use field-wise equality and namedtuple-style `_replace(...)` updates.

## Product State Model

The core public state is visible through three projections:

1. The interaction projection: `Application`, `PromptSession`, `AppSession`, `Input`, and `Output` describe where events come from, where rendering goes, and how a run starts and finishes.
2. The editable-text projection: `Buffer`, `Document`, `History`, `CompletionState`, `Completion`, `Validator`, and `KeyBindings` describe the current input text, cursor, history, completion, validation, and key-driven mutations.
3. The presentation projection: formatted text, styles, color depth, bottom toolbar, right prompt, placeholder, completion display text, and printed output describe how text is converted and rendered.

Cross-view invariants at this level:

- A `Buffer.document` projection must return the same text and cursor position that the `Buffer.text` and `Buffer.cursor_position` projection exposes.
- A `PromptSession.prompt(default=...)` call must reset the session default buffer to that default before the prompt run starts.
- A completion accepted through `CompletionState` must update the same buffer text that `PromptSession.prompt()` eventually returns when the buffer is accepted.
- A `History` object passed to `PromptSession` must be the same history object used by that session's default buffer.
- A `Validator` attached to a prompt or buffer must receive a `Document` projection of the current buffer text.
- A `Style` passed to `prompt()` or `print_formatted_text()` must resolve classes used by formatted text fragments in that prompt or print call.

## Behavioral Sections

### Prompt Sessions

- `prompt()` must create a new `PromptSession` for every call. It must pass `history` to the session constructor because `history` is session state. It must return the string returned by that session's `prompt()` method.
- `PromptSession` must create an `InMemoryHistory` when `history` is `None`. It must create an in-memory clipboard when `clipboard` is `None`.
- `PromptSession` must set `editing_mode` to Vi when `vi_mode=True`; otherwise it must use the given `editing_mode`.
- `PromptSession.prompt()` must when an option argument is not `None` store that value on the session, so the value applies to the current prompt and later prompts. It must when an option argument is `None` keep the session's existing value.
- `PromptSession.prompt()` must when `vi_mode=True` set the session editing mode to Vi for the current and later prompts.
- `PromptSession.prompt()` must when `default` is a string reset the default buffer with a `Document(default)` before running. It must when `default` is a `Document` reset the buffer with that document.
- `PromptSession.prompt()` must when `accept_default=True` accept the default input without requiring user editing and return that default text after the application run completes.
- `PromptSession.prompt()` must when `pre_run` is provided call it at the start of the application run. If `pre_run` raises, the prompt run must raise that exception.
- `PromptSession.prompt()` must when the user sends the configured interrupt action exit by raising `interrupt_exception`, defaulting to `KeyboardInterrupt`.
- `PromptSession.prompt()` must when the user sends the configured EOF action exit by raising `eof_exception`, defaulting to `EOFError`.
- `PromptSession` must when `complete_in_thread=True` and a completer exists wrap the completer in a `ThreadedCompleter` for the default buffer. It must when `complete_style` is `CompleteStyle.READLINE_LIKE` not enable typing-time completion.
- `PromptSession` must when `enable_history_search=True` make typing-time completion inactive, even if `complete_while_typing=True`.
- `PromptSession` must when `placeholder` is present and the default buffer text is empty display placeholder text without making placeholder text part of the returned input.
- `PromptSession` must when `bottom_toolbar` or `rprompt` is a callable call it during rendering to obtain formatted text. It must when the callable raises propagate the exception through the application run.
- `prompt_continuation` must when it is a callable receive `prompt_width`, `line_number`, and `wrap_count` and return formatted text for multiline continuation. It must when `None` use spaces matching the prompt width.

### Application and AppSession

- `Application.run()` must block until `Application.exit()` resolves the active run. It must return the `result` supplied to `exit(result=...)`.
- `Application.run(in_thread=True)` must run the application in a background thread and block the caller until the background run terminates. It must re-raise any exception raised in the background run.
- `Application.exit()` must accept either `result` or `exception`, not both. It must raise `AssertionError` when both are supplied.
- `Application.exit(exception=...)` must make the active run raise that exception. It must accept either an exception instance or an exception class.
- `get_app()` must return the active application during an application run. It must return a dummy application when no application is active.
- `get_app_or_none()` must return the active application during an application run. It must return `None` when no application is active.
- `create_app_session(input=None, output=None)` must create and activate an `AppSession` for the `with` block. It must restore the previous app session after leaving the block.
- `AppSession.input` and `AppSession.output` must lazily create default input/output objects when they were not supplied. They must return the supplied objects when they were supplied.
- `create_app_session` must when `input` or `output` is omitted inherit the parent session's already-specified object without forcing creation of a new parent object.
- `print_formatted_text()` and prompts must use the current `AppSession` output when no explicit output is supplied.

### Buffer and Document

- `Document(text, cursor_position=None, selection=None)` must when `cursor_position` is `None` set the cursor at the end of `text`. It must raise `AssertionError` when `cursor_position` is greater than `len(text)`.
- `Document.current_char` and `Document.char_before_cursor` must return an empty string when no such character exists.
- `Document.lines` must split text on newline characters. `Document.line_count` must count a trailing newline as the start of a new empty line.
- `Document.translate_index_to_position(index)` must return a zero-based `(row, column)` pair. `translate_row_col_to_index(row, col)` must clamp negative rows/columns to the first line/column and out-of-range rows/columns to the nearest valid text position.
- `Document.find(...)`, `find_backwards(...)`, word search helpers, and bracket helpers must return positions relative to the cursor when they find a match and `None` or `0` as documented by each helper when no match exists.
- `Buffer` must use an `InMemoryHistory` when no history is supplied. It must expose a `document` whose `text`, `cursor_position`, and selection match the current buffer state.
- Assigning `Buffer.text` must clamp `cursor_position` to the new text length. It must raise `EditReadOnlyBuffer` when the buffer is read-only.
- Assigning `Buffer.cursor_position` must clamp values below zero to zero and values past the end of text to `len(text)`.
- Assigning `Buffer.document` must atomically update text and cursor before firing change events. It must raise `EditReadOnlyBuffer` when the buffer is read-only.
- `Buffer.set_document(document, bypass_readonly=True)` must update a read-only buffer without raising `EditReadOnlyBuffer`.
- `Buffer.reset(document=None, append_to_history=False)` must reset validation, selection, completion, suggestion, undo/redo, paste, preferred-column, and working-line state. It must when `append_to_history=True` append the current input to history before resetting.
- `Buffer.delete_before_cursor(count)` and `Buffer.delete(count)` must return deleted text. They must return an empty string when no text exists on the requested side of the cursor.
- `Buffer.complete_next()` and `complete_previous()` must return without changing text when no completion state exists. They must wrap through the original text unless `disable_wrap_around=True`.
- `CompletionState.new_text_and_position()` must return the original document text and cursor when no completion is selected. It must return text with the selected completion inserted relative to the original cursor when a completion is selected.

### Completion

- `Completion.start_position` must be zero or negative. `Completion(...)` must raise `AssertionError` when `start_position` is positive.
- `Completion.display` must default to `text` when no display value is supplied. `display_text` must return the plain-text projection of `display`.
- `Completion.display_meta` must return formatted text for `display_meta` and must evaluate callable meta lazily. `display_meta_text` must return the plain-text projection.
- `CompleteEvent` must raise `AssertionError` when both `text_inserted=True` and `completion_requested=True`.
- `Completer.get_completions(document, complete_event)` must return completion objects. `get_completions_async` must by default stream the same completions asynchronously.
- `DummyCompleter` must return an empty completion list.
- `DynamicCompleter` must call its provider for each completion request. It must use `DummyCompleter` behavior when the provider returns `None`.
- `ConditionalCompleter` must return wrapped completions when its filter is true. It must return no completions when its filter is false.
- `ThreadedCompleter` must delegate synchronous completion to the wrapped completer and must provide async completion without requiring the wrapped completer to be async.
- `merge_completers(completers, deduplicate=False)` must yield completions from each completer in the supplied order. It must when `deduplicate=True` remove completions that produce the same resulting text.
- `get_common_complete_suffix(document, completions)` must return an empty string when any completion changes text before the cursor. It must return the common suffix portion for completions that only extend the current text.
- `WordCompleter(words, ignore_case=False, display_dict=None, meta_dict=None, WORD=False, sentence=False, match_middle=False, pattern=None)` must raise `AssertionError` when both `WORD` and `sentence` are true. It must complete the word before the cursor by prefix matching unless `sentence=True` or `match_middle=True` changes the matching scope.
- `NestedCompleter.from_nested_dict(data)` must treat `None` as a terminal completion node, a `set` as keys with terminal nodes, a nested dictionary as a nested completer, and an existing `Completer` as the completer for that node.
- `NestedCompleter` must use the first word before the cursor to select a child completer when the input contains spaces. It must complete top-level words when there is no space in the current input.
- `FuzzyCompleter` must when enabled match characters from the word before the cursor as an ordered subsequence of candidate completion text. It must sort matches by earliest start and then shortest match. It must raise `AssertionError` when `pattern` is supplied and does not start with `^`.
- `FuzzyCompleter` must when disabled delegate directly to the wrapped completer.
- `FuzzyWordCompleter` must behave as `WordCompleter` wrapped in `FuzzyCompleter`.
- `PathCompleter` must complete filesystem entries under `get_paths()` for relative input, must append `/` to displayed directory names, must omit non-directories when `only_directories=True`, must not yield completions when the input length is below `min_input_len`, and must suppress `OSError` by returning no completions.

### History and Validation

- `History.load()` must yield loaded entries newest first. It must cache loaded entries so repeated loads include stored and appended entries.
- `History.get_strings()` must return loaded history strings oldest first.
- `History.append_string(string)` must add the string to loaded history and call `store_string(string)`.
- `InMemoryHistory(history_strings=None)` must store strings in memory. It must when initialized with strings load them newest first and return them oldest first through `get_strings()` after load.
- `DummyHistory` must load no strings and must ignore stored or appended strings.
- `FileHistory(filename)` must persist appended strings to `filename`. It must load persisted multiline strings as whole history entries and yield newest entries first. It must return no strings when the file does not exist.
- `ThreadedHistory(history)` must proxy storing to the wrapped history and must make loaded entries available as the wrapped loader produces them.
- `Validator.validate(document)` must return `None` for valid input and raise `ValidationError` for invalid input.
- `Validator.validate_async(document)` must by default call `validate(document)` and propagate `ValidationError`.
- `Validator.from_callable(func, error_message, move_cursor_to_end)` must call `func(document.text)`. It must raise `ValidationError(message=error_message, cursor_position=0)` when the function returns false and `move_cursor_to_end=False`. It must use `cursor_position=len(document.text)` when `move_cursor_to_end=True`.
- `DummyValidator` must accept every input.
- `ConditionalValidator` must validate through the wrapped validator when its filter is true. It must accept without calling the wrapped validator when its filter is false.
- `DynamicValidator` must call its provider for each validation. It must accept input when the provider returns `None`.
- `ThreadedValidator.validate_async(document)` must run the wrapped validator without blocking the prompt event loop and must propagate `ValidationError`.

### Key Bindings

- `KeyBindings.add(*keys, ...)` must raise `AssertionError` when no keys are supplied.
- Key strings must accept documented names such as `escape`, arrow names, navigation names, control-key names like `c-a`, aliases such as `backspace`, `enter`, `tab`, `c-space`, the wildcard `<any>`, and one-character literal keys.
- `KeyBindings.add()` must raise `ValueError` for an invalid multi-character key name.
- `KeyBindings.add()` must return a decorator. The decorator must return the original handler or binding object after registration.
- A binding filter that is permanently false must leave the handler unregistered and return the handler unchanged.
- `KeyBindings.remove(handler_or_sequence)` must remove matching bindings and raise `ValueError` when no matching binding exists.
- `get_bindings_for_keys(keys)` must return bindings for exact key sequences and include inactive bindings so callers evaluate filters. It must return wildcard matches after more specific matches.
- `get_bindings_starting_with_keys(keys)` must return bindings whose sequences are longer than the supplied prefix.
- `Binding.call(event)` must call the handler. It must schedule coroutine handlers as background tasks. It must invalidate the application unless the handler result is `NotImplemented`.
- `ConditionalKeyBindings` must expose wrapped bindings with the wrapper filter combined with each binding filter.
- `merge_key_bindings()` must expose bindings from registries in the supplied order and must reflect later changes made to those registries.
- An eager binding must be treated as ready to handle a prefix match without waiting for longer active matches.
- A binding with `record_in_macro=False` must not be recorded in macros.

### Formatted Text and Printing

- `to_formatted_text(None)` must return an empty `FormattedText`.
- `to_formatted_text(str_value)` must return one fragment with empty style and the string value.
- `to_formatted_text(list_value)` must treat the list as style/text fragments.
- `to_formatted_text(value)` must call `value.__pt_formatted_text__()` when present.
- `to_formatted_text(callable_value)` must call the callable and convert its return value.
- `to_formatted_text(value, style=style)` must prefix the supplied style to every returned fragment.
- `to_formatted_text(value, auto_convert=True)` must convert unsupported values to their string representation. It must raise `ValueError` for unsupported values when `auto_convert=False`.
- `FormattedText` must behave like a list of fragments and must return itself from `__pt_formatted_text__()`.
- `Template(text).format(*values)` must return callable formatted text that splits `text` on literal `{}` placeholders, emits each plain template part as an empty-style fragment, and replaces each placeholder with the formatted projection of the matching supplied value. It must preserve later `to_formatted_text(..., style=...)` prefixes by concatenating the prefix style, one space, and the fragment's existing style for every returned fragment. It must raise `AssertionError` when the placeholder count does not match the supplied values.
- `merge_formatted_text(items)` must return callable formatted text that, when evaluated, converts each item with `to_formatted_text()` in the supplied order and concatenates the exact fragment lists. It must return an empty fragment list when `items` is empty.
- `fragment_list_to_text()` and `to_plain_text()` must return text without style metadata.
- `HTML` must parse each element name except the root and `style` element as a class name. A text node inside `<b>`, `<strong>`, `<i>`, `<u>`, or `<s>` must use style strings such as `class:b`, `class:strong`, `class:i`, `class:u`, or `class:s`. Nested element names must be comma-combined in nesting order, so text inside `<strong><i>...</i></strong>` returns style `class:strong,i`.
- `HTML` must when an element has `fg`, `color`, or `bg` attributes append `fg:<value>` or `bg:<value>` tokens to the fragment style. The `color` attribute must be an alias for `fg`. A `<style fg="red" bg="#00ff00">x</style>` fragment must use style `fg:red bg:#00ff00`; a named element with attributes must combine class and color tokens, such as `class:name fg:ansired bg:ansiblue`. It must raise `ValueError` when an `fg` or `bg` attribute contains a space.
- `HTML.format(...)` and `%` interpolation must escape inserted values as HTML text before parsing, so inserted `<`, `>`, `&`, and quote characters become literal text instead of tags. Interpolation must return an `HTML` object.
- `ANSI` must parse ANSI escape sequences into formatted fragments whose style string is composed from the active attributes in this order: foreground color, `bg:` background color, `bold`, `dim`, `underline`, `strike`, `italic`, `blink`, `reverse`, `hidden`. SGR `1` must add `bold`, `2` must add `dim`, `22` must clear both bold and dim, and `0` must reset all style attributes.
- `ANSI` must represent 8/16-color foregrounds as ANSI color names such as `ansired`, 8/16-color backgrounds as `bg:<ansi-name>`, 256-color foregrounds as `#rrggbb`, 256-color backgrounds as `bg:#rrggbb`, true-color foregrounds as `#rrggbb`, and true-color backgrounds as `bg:#rrggbb`. `ANSI("\x1b[38;5;196mX")` must produce a foreground style of `#ff0000`, and `ANSI("\x1b[38;2;1;2;3mX")` must produce `#010203`.
- `ANSI.format(...)` and `%` interpolation must escape inserted ANSI escape and backspace characters so inserted values cannot inject formatting. Interpolation must return an `ANSI` object.
- `PygmentsTokens` must map each `(token, text)` pair to a fragment whose style is `class:` plus `pygments_token_to_classname(token)`. `pygments_token_to_classname(Token.Name.Function)` returns `pygments.name.function`, so the fragment style is `class:pygments.name.function`.
- `print_formatted_text()` must insert `sep` between values and append `end` after the last value. It must treat a normal Python list that is not `FormattedText` as printable plain text. It must raise `AssertionError` when both `output` and `file` are supplied.
- `print_formatted_text()` must when an application is running print above the application and then allow the application to render again. It must when no output is supplied use the current `AppSession` output.

### Styles and Color Depth

- A style string must accept foreground color tokens, `fg:` colors, `bg:` colors, `bold`, `italic`, `underline`, `blink`, `reverse`, `hidden`, `dim`, and the matching negative forms.
- `Attrs(color, bgcolor, bold, underline, strike, italic, blink, reverse, hidden, dim)` must be the public value object for resolved style attributes. The positional constructor order and `_fields` order must be `color`, `bgcolor`, `bold`, `underline`, `strike`, `italic`, `blink`, `reverse`, `hidden`, `dim`.
- The default resolved `Attrs` value must be `Attrs(color="", bgcolor="", bold=False, underline=False, strike=False, italic=False, blink=False, reverse=False, hidden=False, dim=False)`. The empty inherited `Attrs` value must use `None` for every field. Public resolved lookups must return concrete default values for unspecified fields.
- `Attrs` equality must compare field-by-field. `_replace(...)` must return a new `Attrs` value with the named fields replaced and all other fields preserved.
- `parse_color(text)` must return ANSI color names unchanged, normalize ANSI aliases, normalize named colors to lowercase hex without `#`, expand three-digit `#` hex colors to six digits, accept six-digit `#` hex colors, and accept `""` and `"default"`. It must raise `ValueError` for an invalid color format.
- The standard prompt_toolkit named color table is part of the public color-normalization contract. Common named colors must normalize to their RGB hex values, including `red -> ff0000`, `blue -> 0000ff`, `green -> 008000`, `black -> 000000`, `white -> ffffff`, and case-insensitive names such as `LightSkyBlue -> 87cefa`.
- `Style(style_rules)` must apply later rules with higher priority than earlier rules. It must raise `AssertionError` for class-name strings outside the accepted lowercase letter, digit, dot, space, underscore, and hyphen vocabulary.
- `Style.from_dict(style_dict, priority=Priority.DICT_KEY_ORDER)` must preserve dictionary iteration order. `Style.from_dict(..., priority=Priority.MOST_PRECISE)` must sort rules so more precise class paths receive higher priority.
- `Style.get_attrs_for_style_str(style_str)` must return an `Attrs` value. It must evaluate the style string from left to right. It must expand `class:a.b.c` into `a`, `a.b`, and `a.b.c`. It must combine comma-separated classes and repeated `class:` prefixes.
- `Style.get_attrs_for_style_str(style_str)` must resolve class rules and inline style tokens into `Attrs` fields. `red bold` must set `color="ff0000"` and `bold=True`; `bg:blue italic` must set `bgcolor="0000ff"` and `italic=True`; unspecified fields must retain resolved defaults.
- Inline style tokens appearing later in a style string must override earlier resolved attributes.
- `merge_styles([style1, style2, ...])` must combine style rules in the supplied order, so later styles override earlier styles for conflicting rules.
- `pygments_token_to_classname(Token.Name.Function)` must return a dotted lowercase classname beginning with `pygments`.
- `SwapLightAndDarkStyleTransformation.transform_attrs(attrs)` must accept an `Attrs` value and return an `Attrs` value with foreground and background colors individually mapped to their opposite light/dark color. It must preserve non-color fields.
- `AdjustBrightnessStyleTransformation(min_brightness=0.0, max_brightness=1.0).transform_attrs(attrs)` must accept an `Attrs` value and return an `Attrs` value. It must return the input unchanged when the brightness range is `0.0..1.0`. It must when a foreground color is present and no background color is present adjust only the foreground color into a six-digit lowercase hex value. It must assert that both brightness bounds are between `0.0` and `1.0`.
- `ColorDepth` must expose `DEPTH_1_BIT`/`MONOCHROME`, `DEPTH_4_BIT`/`ANSI_COLORS_ONLY`, `DEPTH_8_BIT`/`DEFAULT`, and `DEPTH_24_BIT`/`TRUE_COLOR`.
- `DummyOutput` must ignore writes and terminal-control calls. It must return UTF-8 encoding, size 40 rows by 80 columns, 40 rows below the cursor, and 1-bit default color depth. It must raise `NotImplementedError` from `fileno()`.

### Unit-Test I/O

- `create_pipe_input()` must return a context manager. Entering it must return a `PipeInput` object whose `send_text(text)` feeds key input to prompts and applications.
- A prompt or application created with `input=pipe_input` and `output=DummyOutput()` must consume text sent through the pipe without rendering visible output.
- A `create_app_session(input=pipe_input, output=DummyOutput())` context must make its input and output the defaults for prompts, applications, and `print_formatted_text()` calls inside the context.
- `DummyOutput` must be safe for tests that assert returned values or object state instead of terminal bytes.

## Error Semantics

- `Document(text, cursor_position)` raises `AssertionError` when the cursor position is greater than the text length.
- `Completion(text, start_position)` raises `AssertionError` when `start_position` is positive.
- `CompleteEvent(text_inserted=True, completion_requested=True)` raises `AssertionError`.
- `WordCompleter(WORD=True, sentence=True)` raises `AssertionError`.
- `FuzzyCompleter(pattern=...)` raises `AssertionError` when the pattern does not start with `^`.
- `Buffer.text = ...`, `Buffer.document = ...`, and `Buffer.set_document(..., bypass_readonly=False)` raise `EditReadOnlyBuffer` when the buffer is read-only.
- `Validator.validate(document)` raises `ValidationError` for invalid input. The exception exposes `cursor_position` and `message`.
- `PromptSession.prompt()` raises the configured interrupt exception for the interrupt action and the configured EOF exception for the EOF action.
- `KeyBindings.add()` raises `AssertionError` with no keys and `ValueError` for invalid key names.
- `KeyBindings.remove()` raises `ValueError` when no matching binding exists.
- `to_formatted_text()` raises `ValueError` for unsupported values unless `auto_convert=True`.
- `parse_color()` raises `ValueError` for invalid color strings.
- `print_formatted_text()` raises `AssertionError` when both `output` and `file` are supplied.
- `Application.exit(result=..., exception=...)` raises `AssertionError` when both are supplied.
- `DummyOutput.fileno()` raises `NotImplementedError`.
- `PathCompleter` returns no completions instead of raising when filesystem listing raises `OSError`.

## Cross-View Invariants

1. `Buffer.document.text` must equal `Buffer.text`, and `Buffer.document.cursor_position` must equal `Buffer.cursor_position`.
2. Assigning `Buffer.document` must update `Buffer.text` and `Buffer.cursor_position` together before listeners observe the change.
3. `PromptSession.default_buffer.history` must be the `History` object passed to `PromptSession(history=...)`, or a new `InMemoryHistory` when omitted.
4. Text accepted by a prompt must be the current text in the session default buffer at the time the application exits with a result.
5. A validator attached to a prompt must receive a `Document` whose text is the current buffer text at validation time.
6. A completer attached to a prompt must receive a `Document` whose text and cursor match the current buffer state at completion time.
7. `CompletionState.new_text_and_position()` returns a text/cursor pair that the buffer must expose after `go_to_completion()` selects the same completion.
8. A string appended through `History.append_string()` must appear in the next `History.load()` result and in `get_strings()` after loading.
9. Formatted text accepted by prompts, toolbars, completions, styles, and `print_formatted_text()` must pass through the same `to_formatted_text()` conversion rules.
10. A `Style` class used in `HTML`, `FormattedText`, completion display text, prompt message, bottom toolbar, or right prompt must resolve through the same style sheet rules.
11. `print_formatted_text()` without explicit output must use the current `AppSession.output`, the same default output projection used by applications in that session.
12. `create_pipe_input()` text and `DummyOutput` no-render output must drive the same `PromptSession.prompt()` state transitions as terminal input/output, except for visible terminal rendering.

## Representative Workflows

### Prompt With Completion, Validation, History, Styling, and Test I/O

```python
from prompt_toolkit import HTML, PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator

history = InMemoryHistory(["deploy staging"])
completer = WordCompleter(["deploy", "destroy"], ignore_case=True)
validator = Validator.from_callable(
    lambda text: text.startswith("deploy"),
    error_message="command must deploy",
)
style = Style.from_dict({"prompt": "ansigreen bold"})

with create_pipe_input() as inp:
    inp.send_text("deploy prod\n")
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
```

The prompt must read from the pipe, render nothing visible through `DummyOutput`, validate the current buffer document, complete against the word before the cursor when completion is requested, return the accepted buffer text, and keep using the same history object for later prompts in the session.

### Running a Full-Screen Application With a Key Binding

```python
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings

kb = KeyBindings()

@kb.add("c-q")
def _(event):
    event.app.exit(result="done")

app = Application(key_bindings=kb, full_screen=True)
```

When the application is run and the `c-q` binding is invoked, the handler must receive a `KeyPressEvent` whose `app` is the running application, `Application.exit(result="done")` must complete the run, and `Application.run()` must return `"done"`.

## Non-Goals

- The specification does not require reproducing every layout container, window, margin, processor, menu, widget, dialog, or progress-bar detail.
- The specification does not require byte-for-byte terminal renderer output, VT100 escape sequence ordering, or Win32 API behavior.
- The specification does not require private helpers, private attributes, caches, internal coroutine structure, or undocumented module paths.
- The specification does not require exact visual placement of completion menus, toolbars, frames, or full-screen layouts beyond the public state and conversion behavior stated above.
- The specification does not require support for optional clipboard integrations that need third-party clipboard packages.
- The specification does not require implementing shell commands, external editors, terminal suspension, or OS-specific terminal probing beyond the documented public errors and no-render test I/O behavior.
