# prompt_toolkit Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`prompt_toolkit` is a pure Python library for building interactive command-line prompts and terminal applications. It provides a high-level `prompt()` function, reusable `PromptSession` objects, a full-screen `Application` object, and public building blocks for editable text buffers, immutable document views, completions, validation, history, key bindings, formatted text, styling, and testable input/output.

The library is designed around explicit objects instead of process-wide prompt state. A caller must be able to create multiple independent sessions, applications, histories, styles, and I/O sessions in one Python process.

## Non-Goals

- This specification does not require Full-screen layout containers, windows, margins, processors, menus, widgets, dialogs, or progress-bar details.
- This specification does not require Byte-exact terminal renderer output, VT100 escape-sequence ordering, or Win32 API behavior.
- This specification does not require Private helpers, private attributes, caches, internal coroutine structure, or undocumented module paths.
- This specification does not require Exact visual placement of completion menus, toolbars, frames, or full-screen layouts; only the public state and conversion behavior described in the behavior sections applies.
- This specification does not require Optional clipboard integrations requiring third-party clipboard packages.
- This specification does not require Shell commands, external editors, terminal suspension, or OS-specific terminal probing; the boundary is the documented public errors and no-render test I/O behavior.

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

## Prompt Sessions

This section defines how prompts are created and how session state flows across successive prompt calls.

**One-shot prompt function.** The top-level `prompt` function must create a new `PromptSession` for every call. It must pass `history` to the session constructor because `history` is session state. It must return the string returned by that session's `prompt` method.

**Session creation.** When a `PromptSession` is created without specifying `history`, the session must create an `InMemoryHistory`. When `clipboard` is not supplied, the session must create an in-memory clipboard. When `vi_mode` is true, the session must set `editing_mode` to Vi; otherwise it must use the given `editing_mode`. The session must expose a `default_buffer` attribute that is the buffer used for prompt input.

**Prompt method option persistence.** When an option argument to `PromptSession.prompt()` is not `None`, the session must store that value so it applies to the current prompt and to later prompts. When an option argument is `None`, the session must keep the existing value. When `vi_mode` is true, the session must set the editing mode to Vi for the current and later prompts.

**Default input.** When `default` is a string, the session must reset the default buffer with a document containing that string before running. When `default` is a `Document`, the session must reset the buffer with that document, preserving the cursor position specified in the document. When `accept_default` is true, the session must accept the default input without requiring user editing and return that default text after the application run completes.

**Pre-run callback.** When `pre_run` is provided, the session must call it at the start of the application run. If `pre_run` raises, the prompt run must raise that exception to the caller.

**Interrupt and EOF.** When the user sends the configured interrupt action, the session must exit by raising the configured `interrupt_exception`, defaulting to `KeyboardInterrupt`. When the user sends the configured EOF action, the session must exit by raising the configured `eof_exception`, defaulting to `EOFError`.

**Completion options.** When `complete_in_thread` is true and a completer exists, the session must wrap the completer in a `ThreadedCompleter` for the default buffer. When `complete_style` is `CompleteStyle.READLINE_LIKE`, the session must not enable typing-time completion. When `enable_history_search` is true, typing-time completion must be inactive even if `complete_while_typing` is true.

**Display options.** When `placeholder` is present and the default buffer text is empty, placeholder text must be displayed without making it part of the returned input. When `bottom_toolbar` or `rprompt` is a callable, the session must call it during rendering to obtain formatted text; if the callable raises, the exception must propagate through the application run. When `prompt_continuation` is a callable, it must receive `prompt_width`, `line_number`, and `wrap_count` and return formatted text for multiline continuation; when `None`, the session must use spaces matching the prompt width.

## Application and AppSession

This section defines the full-screen application lifecycle, active application queries, and application session scoping.

**Application lifecycle.** `Application.run()` must block until `Application.exit()` resolves the active run. It must return the `result` supplied to `exit`. When `in_thread` is true, the application must run in a background thread and the caller must block until the background run terminates; any exception raised in the background run must be re-raised to the caller.

**Application exit.** `Application.exit()` must accept either `result` or `exception`, not both. It must raise `AssertionError` when both are supplied. When `exception` is supplied, the active run must raise that exception; the value may be either an exception instance or an exception class.

**Active application queries.** `get_app()` must return the active application during an application run. It must return a dummy application when no application is active. `get_app_or_none()` must return the active application during an application run and `None` when no application is active.

**Application sessions.** `create_app_session(input=None, output=None)` must create and activate an `AppSession` for the `with` block and must restore the previous app session after leaving the block. `AppSession.input` and `AppSession.output` must lazily create default input/output objects when they were not supplied and must return the supplied objects when they were supplied. When `input` or `output` is omitted, the child session must inherit the parent session's already-specified object without forcing creation of a new parent object.

**Session query.** `get_app_session()` must return the current `AppSession`. When called inside a `create_app_session` context, it must return the session created by that context, with `input` and `output` reflecting the objects supplied or inherited.

**Output routing.** `print_formatted_text()` and prompts must use the current `AppSession` output when no explicit output is supplied.

## Buffer and Document

This section defines the immutable document view and the mutable buffer that holds editable text state.

**Document creation.** When a `Document` is created without specifying `cursor_position`, the cursor must be placed at the end of the text. The document must raise `AssertionError` when the cursor position is greater than the text length.

**Character access.** `Document.current_char` must return the character at the cursor position, and `Document.char_before_cursor` must return the character immediately before the cursor. Both must return an empty string when no such character exists.

**Text partitions.** `Document.text_before_cursor` must return all text from the start up to (not including) the cursor position. `Document.text_after_cursor` must return all text from the cursor position to the end.

**Line projections.** `Document.lines` must split text on newline characters. `Document.line_count` must count a trailing newline as the start of a new empty line. `Document.current_line` must return the full line containing the cursor. `Document.current_line_before_cursor` must return the portion of the current line before the cursor. `Document.current_line_after_cursor` must return the portion of the current line after the cursor.

**Cursor position queries.** `Document.cursor_position_row` and `Document.cursor_position_col` must return zero-based row and column values for the cursor position. An empty document with the cursor at position zero must report row zero and column zero. `Document.is_cursor_at_the_end` must return true when the cursor position equals the text length and false otherwise.

**Position translation.** `Document.translate_index_to_position(index)` must return a zero-based `(row, column)` pair. `translate_row_col_to_index(row, col)` must clamp negative rows and columns to the first line and column and must clamp out-of-range rows and columns to the nearest valid text position.

**Search and word helpers.** `Document.find(...)`, `find_backwards(...)`, and bracket helpers must return positions relative to the cursor when they find a match and `None` or `0` as documented by each helper when no match exists. `Document.get_word_before_cursor()` must return the word immediately before the cursor using the default word boundary rules; when a `pattern` parameter is supplied, it must use that compiled regex to determine the word boundary instead.

**Buffer initial state.** When a `Buffer` is created with no arguments, its `text` must be an empty string and its `cursor_position` must be zero. Its `document` must reflect the same empty text and zero cursor position. The buffer must use an `InMemoryHistory` when no history is supplied.

**Buffer text and cursor.** Assigning `Buffer.text` must update the buffer text and must clamp `cursor_position` to the new text length. Assigning `Buffer.cursor_position` must clamp values below zero to zero and values past the end of text to the text length. Both must raise `EditReadOnlyBuffer` when the buffer is read-only.

**Buffer document projection.** `Buffer.document` must expose a `Document` whose `text` and `cursor_position` match the current buffer state. Assigning `Buffer.document` must atomically update text and cursor before firing change events. It must raise `EditReadOnlyBuffer` when the buffer is read-only. `Buffer.set_document` with `bypass_readonly` set to true must update a read-only buffer without raising.

**Buffer reset.** `Buffer.reset()` must reset validation, selection, completion, suggestion, undo/redo, paste, preferred-column, and working-line state. When `append_to_history` is true, it must append the current input text to history before resetting. When a `document` argument is supplied, the buffer must adopt that document after reset.

**Buffer delete operations.** `Buffer.delete_before_cursor(count)` must delete `count` characters before the cursor and return the deleted text. `Buffer.delete(count)` must delete `count` characters after the cursor and return the deleted text. Both must return an empty string when no text exists on the requested side of the cursor.

**Buffer completion cycling.** `Buffer.complete_next()` and `complete_previous()` must return without changing text when no completion state exists. They must wrap through the original text unless `disable_wrap_around` is true.

**CompletionState.** `CompletionState` must hold the original document and a list of completions. When `complete_index` is `None` or not specified, no completion is selected and `new_text_and_position()` must return the original document text and cursor position. When `complete_index` selects a completion by its position in the list, `new_text_and_position()` must return the text with the selected completion inserted relative to the original cursor and the new cursor position. `go_to_index(index)` must update the selected completion index.

## Completion

This section defines completion objects, completion providers, and completion helper functions.

**Completion objects.** A `Completion` must have a `start_position` that is zero or negative; it must raise `AssertionError` when `start_position` is positive. `Completion.display` must default to the completion `text` when no display value is supplied. `display_text` must return the plain-text projection of `display`. `Completion.display_meta` must return formatted text for the metadata and must evaluate callable meta lazily. `display_meta_text` must return the plain-text projection.

**Completion events.** `CompleteEvent` must raise `AssertionError` when both `text_inserted` and `completion_requested` are true.

**Base completer.** `Completer.get_completions(document, complete_event)` must return completion objects. `get_completions_async` must by default stream the same completions asynchronously.

**Delegating completers.** `DummyCompleter` must return an empty completion list. `DynamicCompleter` must call its provider for each completion request; when the provider returns `None`, it must use `DummyCompleter` behavior. `ConditionalCompleter` must return wrapped completions when its filter is true and must return no completions when its filter is false.

**Threaded completer.** `ThreadedCompleter` must delegate synchronous completion to the wrapped completer and must provide async completion without requiring the wrapped completer to be async.

**Merged completers.** `merge_completers(completers)` must yield completions from each completer in the supplied order. When `deduplicate` is true, it must remove completions that produce the same resulting text. `get_common_complete_suffix(document, completions)` must return an empty string when any completion changes text before the cursor and must return the common suffix portion for completions that only extend the current text.

**Word completer.** `WordCompleter` must complete the word before the cursor by prefix matching. When `words` is a callable, it must be called at each completion request to obtain the current word list. When `ignore_case` is true, matching must be case-insensitive. When `match_middle` is true, candidates must match if the input appears anywhere in the candidate text. When `sentence` is true, the entire input line must be matched against candidate phrases. A `WordCompleter` must raise `AssertionError` when both `WORD` and `sentence` are true. When a `pattern` is supplied, it must use that compiled regex to determine the word boundary for the text before the cursor. When no custom pattern is supplied and the input contains spaces, the completer must complete the last word after the final space.

**Nested completer.** `NestedCompleter.from_nested_dict(data)` must treat `None` as a terminal completion node, a `set` as keys with terminal nodes, a nested dictionary as a nested completer, and an existing `Completer` as the completer for that node. `NestedCompleter` must use the first word before the cursor to select a child completer when the input contains spaces. It must complete top-level words when there is no space in the current input.

**Fuzzy completers.** `FuzzyCompleter` must when `enable_fuzzy` is true match characters from the word before the cursor as an ordered subsequence of candidate completion text. It must sort matches by earliest start and then shortest match. It must raise `AssertionError` when a `pattern` is supplied and does not start with `^`. When `enable_fuzzy` is false, it must delegate directly to the wrapped completer without fuzzy filtering. `FuzzyWordCompleter` must behave as a `WordCompleter` wrapped in `FuzzyCompleter`.

**Path completer.** `PathCompleter` must complete filesystem entries under the directories returned by `get_paths()` for relative input. It must append `/` to displayed directory names. When `only_directories` is true, it must omit non-directory entries. When the input length is below `min_input_len`, it must not yield completions. When filesystem listing raises `OSError`, it must suppress the exception and return no completions.

## History and Validation

This section defines history backends for input recall and validators for input checking.

**History interface.** `History.load()` must yield loaded entries newest first. It must cache loaded entries so repeated loads include stored and appended entries. `History.get_strings()` must return loaded history strings oldest first. `History.append_string(string)` must add the string to loaded history and call the storage method.

**In-memory history.** `InMemoryHistory` must store strings in memory. When initialized with a list of strings, it must load them newest first and return them oldest first through `get_strings()` after loading.

**File history.** `FileHistory` must persist appended strings to the specified filename. It must load persisted multiline strings as whole history entries and yield newest entries first. It must return no strings when the file does not exist. A new `FileHistory` instance using the same filename must read entries stored by a previous instance.

**Dummy history.** `DummyHistory` must load no strings and must ignore stored or appended strings.

**Threaded history.** `ThreadedHistory` must proxy storing to the wrapped history and must make loaded entries available as the wrapped loader produces them.

**Validator interface.** `Validator.validate(document)` must return `None` for valid input and raise `ValidationError` for invalid input. `Validator.validate_async(document)` must by default call `validate` and propagate `ValidationError`. `Validator.from_callable` must call the provided function with the document text. When the function returns false and `move_cursor_to_end` is false, it must raise `ValidationError` with `cursor_position` set to zero and the configured `error_message`. When `move_cursor_to_end` is true, it must use `cursor_position` equal to the document text length. The `ValidationError` exception must expose `cursor_position` and `message` attributes.

**Validator variants.** `DummyValidator` must accept every input and return `None`. `ConditionalValidator` must validate through the wrapped validator when its filter is true and must accept without calling the wrapped validator when its filter is false. `DynamicValidator` must call its provider for each validation; when the provider returns `None`, it must accept input. `ThreadedValidator.validate_async(document)` must run the wrapped validator without blocking the prompt event loop and must propagate `ValidationError`.

## Key Bindings

This section defines key binding registration, lookup, invocation, and composition.

**Registration.** `KeyBindings.add(*keys, ...)` must raise `AssertionError` when no keys are supplied. It must raise `ValueError` for an invalid multi-character key name. It must return a decorator, and the decorator must return the original handler or binding object after registration. A binding filter that is permanently false must leave the handler unregistered and return the handler unchanged.

**Key names.** Key strings must accept documented names such as `escape`, arrow names, navigation names, control-key names like `c-a`, aliases such as `backspace`, `enter`, `tab`, `c-space`, the wildcard `<any>`, and one-character literal keys.

**Removal.** `KeyBindings.remove(handler_or_sequence)` must remove matching bindings and must raise `ValueError` when no matching binding exists.

**Binding queries.** `get_bindings_for_keys(keys)` must return bindings for exact key sequences and must include inactive bindings so callers can evaluate filters. It must return wildcard matches after more specific matches. `get_bindings_starting_with_keys(keys)` must return bindings whose sequences are longer than the supplied prefix.

**Binding invocation.** `Binding.call(event)` must call the handler. It must schedule coroutine handlers as background tasks. It must invalidate the application unless the handler result is `NotImplemented`.

**Conditional and merged bindings.** `ConditionalKeyBindings` must expose wrapped bindings with the wrapper filter combined with each binding filter, so when the wrapper filter is false, each exposed binding's own filter must also evaluate to false. `merge_key_bindings()` must expose bindings from registries in the supplied order and must reflect later changes made to those registries, acting as a live view.

**Binding options.** An eager binding must be treated as ready to handle a prefix match without waiting for longer active matches. A binding with `record_in_macro` set to false must not be recorded in macros.

## Formatted Text and Printing

This section defines how values are converted to styled text fragments, how markup languages produce fragments, and how formatted text is printed.

**General conversion.** `to_formatted_text(None)` must return an empty `FormattedText`. `to_formatted_text(str_value)` must return one fragment with empty style and the string value. `to_formatted_text(list_value)` must treat the list as style/text fragments. `to_formatted_text(value)` must call `value.__pt_formatted_text__()` when that method is present. `to_formatted_text(callable_value)` must call the callable and convert its return value. When a `style` argument is supplied, it must prefix the supplied style string followed by a space to every returned fragment's existing style. When `auto_convert` is true, unsupported values must be converted to their string representation; when false, unsupported values must raise `ValueError`.

**FormattedText object.** `FormattedText` must behave like a list of `(style, text)` fragments and must return itself from `__pt_formatted_text__()`.

**Template interpolation.** `Template(text).format(*values)` must return callable formatted text that splits `text` on literal `{}` placeholders, emits each plain template part as an empty-style fragment, and replaces each placeholder with the formatted projection of the matching supplied value. It must preserve later `to_formatted_text(..., style=...)` prefixes by concatenating the prefix style, one space, and the fragment's existing style for every returned fragment. It must raise `AssertionError` when the placeholder count does not match the supplied values.

**Merge.** `merge_formatted_text(items)` must return callable formatted text that, when evaluated, converts each item with `to_formatted_text()` in the supplied order and concatenates the exact fragment lists. It must return an empty fragment list when `items` is empty.

**Plain text extraction.** `fragment_list_to_text()` and `to_plain_text()` must return text without style metadata.

**HTML markup.** `HTML` must parse each element name except the root and `style` element as a class name. A text node inside `<b>`, `<strong>`, `<i>`, `<u>`, or `<s>` must use style strings such as `class:b`, `class:strong`, `class:i`, `class:u`, or `class:s`. Nested element names must be comma-combined in nesting order, so text inside `<strong><i>...</i></strong>` must return style `class:strong,i`. When an element has `fg`, `color`, or `bg` attributes, `HTML` must append `fg:<value>` or `bg:<value>` tokens to the fragment style. The `color` attribute must be an alias for `fg`. A `<style fg="red" bg="#00ff00">x</style>` fragment must use style `fg:red bg:#00ff00`; a named element with attributes must combine class and color tokens, such as `class:name fg:ansired bg:ansiblue`. It must raise `ValueError` when an `fg` or `bg` attribute contains a space. `HTML.format(...)` and `%` interpolation must escape inserted values as HTML text before parsing, so inserted `<`, `>`, `&`, and quote characters become literal text instead of tags. Interpolation must return an `HTML` object.

**ANSI escape parsing.** `ANSI` must parse ANSI escape sequences into formatted fragments whose style string is composed from the active attributes in this order: foreground color, `bg:` background color, `bold`, `dim`, `underline`, `strike`, `italic`, `blink`, `reverse`, `hidden`. SGR `1` must add `bold`, `2` must add `dim`, `22` must clear both bold and dim, and `0` must reset all style attributes. `ANSI` must represent 8/16-color foregrounds as ANSI color names such as `ansired`, 8/16-color backgrounds as `bg:<ansi-name>`, 256-color foregrounds as `#rrggbb`, 256-color backgrounds as `bg:#rrggbb`, true-color foregrounds as `#rrggbb`, and true-color backgrounds as `bg:#rrggbb`. `ANSI("\x1b[38;5;196mX")` must produce a foreground style of `#ff0000`, and `ANSI("\x1b[38;2;1;2;3mX")` must produce `#010203`. `ANSI.format(...)` and `%` interpolation must escape inserted ANSI escape and backspace characters so inserted values cannot inject formatting. Interpolation must return an `ANSI` object.

**Pygments token conversion.** `PygmentsTokens` must map each `(token, text)` pair to a fragment whose style is `class:` plus the dotted classname produced by `pygments_token_to_classname(token)`. For example, `pygments_token_to_classname(Token.Name.Function)` must return `pygments.name.function`, so the fragment style is `class:pygments.name.function`.

**Printing.** `print_formatted_text()` must insert `sep` between values and append `end` after the last value. It must treat a normal Python list that is not `FormattedText` as printable plain text. It must raise `AssertionError` when both `output` and `file` are supplied. When an application is running, it must print above the application and then allow the application to render again. When no output is supplied, it must use the current `AppSession` output.

## Styles and Color Depth

This section defines style strings, style resolution, color parsing, style transformations, color depth levels, and the test output object.

**Style string vocabulary.** A style string must accept foreground color tokens, `fg:` colors, `bg:` colors, `bold`, `italic`, `underline`, `blink`, `reverse`, `hidden`, `dim`, `strike`, and the matching negative forms.

**Attrs value object.** `Attrs` is the public value object for resolved style attributes. Its positional field order must be `color`, `bgcolor`, `bold`, `underline`, `strike`, `italic`, `blink`, `reverse`, `hidden`, `dim`. The default resolved `Attrs` value must have `color=""`, `bgcolor=""`, and all boolean fields set to false. The empty inherited `Attrs` value must use `None` for every field. `Attrs` equality must compare field-by-field. `_replace(...)` must return a new `Attrs` value with the named fields replaced and all other fields preserved.

**Color parsing.** `parse_color(text)` must return ANSI color names unchanged, must normalize ANSI aliases, must normalize named colors to lowercase hex without `#`, must expand three-digit `#` hex colors to six digits, must accept six-digit `#` hex colors, and must accept `""` and `"default"`. It must raise `ValueError` for an invalid color format.

**Named color table.** The standard prompt_toolkit named color table is part of the public color-normalization contract. Common named colors must normalize to their RGB hex values, including `red` to `ff0000`, `blue` to `0000ff`, `green` to `008000`, `black` to `000000`, `white` to `ffffff`, and case-insensitive names such as `LightSkyBlue` to `87cefa`.

**Style creation and priority.** `Style(style_rules)` must apply later rules with higher priority than earlier rules. It must raise `AssertionError` for class-name strings outside the accepted lowercase letter, digit, dot, space, underscore, and hyphen vocabulary. `Style.from_dict(style_dict)` must preserve dictionary iteration order. When `priority` is `Priority.MOST_PRECISE`, rules must be sorted so more precise class paths receive higher priority.

**Style resolution.** `Style.get_attrs_for_style_str(style_str)` must return an `Attrs` value. It must evaluate the style string from left to right. It must expand `class:a.b.c` into `a`, `a.b`, and `a.b.c` for rule matching. It must combine comma-separated classes and repeated `class:` prefixes. Class rules and inline style tokens must resolve into `Attrs` fields: for example, `red bold` must set `color="ff0000"` and `bold=True`; `bg:blue italic` must set `bgcolor="0000ff"` and `italic=True`; unspecified fields must retain resolved defaults. Inline style tokens appearing later in a style string must override earlier resolved attributes.

**Style merging.** `merge_styles([style1, style2, ...])` must combine style rules in the supplied order, so later styles override earlier styles for conflicting rules.

**Pygments class names.** `pygments_token_to_classname(Token.Name.Function)` must return a dotted lowercase classname beginning with `pygments`, specifically `pygments.name.function`.

**Style transformations.** `SwapLightAndDarkStyleTransformation.transform_attrs(attrs)` must accept an `Attrs` value and return an `Attrs` value with foreground and background colors individually mapped to their opposite light/dark color. It must preserve non-color fields. `AdjustBrightnessStyleTransformation` must when the brightness range is `0.0..1.0` return the input unchanged. When a foreground color is present and no background color is present, it must adjust only the foreground color into a six-digit lowercase hex value. It must assert that both brightness bounds are between `0.0` and `1.0`. ANSI default colors must pass through unchanged.

**Color depth.** `ColorDepth` must expose `DEPTH_1_BIT`/`MONOCHROME`, `DEPTH_4_BIT`/`ANSI_COLORS_ONLY`, `DEPTH_8_BIT`/`DEFAULT`, and `DEPTH_24_BIT`/`TRUE_COLOR`.

**DummyOutput.** `DummyOutput` must ignore writes and terminal-control calls. It must return UTF-8 encoding, size 40 rows by 80 columns, 40 rows below the cursor, and 1-bit default color depth. It must raise `NotImplementedError` from `fileno()`.

## Unit-Test I/O

This section defines the test-oriented input and output objects used to drive prompts and applications without a real terminal.

**Pipe input.** `create_pipe_input()` must return a context manager. Entering it must return a `PipeInput` object whose `send_text(text)` feeds key input to prompts and applications.

**Test-driven prompts.** A prompt or application created with `input=pipe_input` and `output=DummyOutput()` must consume text sent through the pipe without rendering visible output. The returned text and buffer state must match the text sent through the pipe.

**App session for tests.** A `create_app_session(input=pipe_input, output=DummyOutput())` context must make its input and output the defaults for prompts, applications, and `print_formatted_text()` calls inside the context.

**DummyOutput safety.** `DummyOutput` must be safe for tests that assert returned values or object state instead of terminal bytes.

## State Model

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

## Error Semantics

- Creating a `Document` with `cursor_position` greater than the text length must raise `AssertionError`.
- Creating a `Completion` with positive `start_position` must raise `AssertionError`.
- Creating a `CompleteEvent` with both `text_inserted` and `completion_requested` set to true must raise `AssertionError`.
- Creating a `WordCompleter` with both `WORD` and `sentence` set to true must raise `AssertionError`.
- Creating a `FuzzyCompleter` with a `pattern` that does not start with `^` must raise `AssertionError`.
- Assigning `Buffer.text`, `Buffer.document`, or calling `Buffer.set_document` without `bypass_readonly` on a read-only buffer must raise `EditReadOnlyBuffer`.
- `Validator.validate(document)` must raise `ValidationError` for invalid input, exposing `cursor_position` and `message`.
- `PromptSession.prompt()` must raise the configured interrupt exception for the interrupt action and the configured EOF exception for the EOF action.
- `KeyBindings.add()` with no keys must raise `AssertionError`; with an invalid key name must raise `ValueError`.
- `KeyBindings.remove()` with no matching binding must raise `ValueError`.
- `to_formatted_text()` must raise `ValueError` for unsupported values unless `auto_convert` is true.
- `parse_color()` must raise `ValueError` for invalid color strings.
- `print_formatted_text()` must raise `AssertionError` when both `output` and `file` are supplied.
- `Application.exit()` with both `result` and `exception` must raise `AssertionError`.
- `DummyOutput.fileno()` must raise `NotImplementedError`.
- `PathCompleter` must return no completions instead of raising when filesystem listing raises `OSError`.

## Cross-View Invariants

1. `Buffer.document.text` must equal `Buffer.text`, and `Buffer.document.cursor_position` must equal `Buffer.cursor_position`.
2. Assigning `Buffer.document` must update `Buffer.text` and `Buffer.cursor_position` together before listeners observe the change.
3. `PromptSession.default_buffer.history` must be the `History` object passed to `PromptSession(history=...)`, or a new `InMemoryHistory` when omitted.
4. Text accepted by a prompt must be the current text in the session default buffer at the time the application exits with a result.
5. A validator attached to a prompt must receive a `Document` whose text is the current buffer text at validation time.
6. A completer attached to a prompt must receive a `Document` whose text and cursor match the current buffer state at completion time.
7. `CompletionState.new_text_and_position()` returns a text/cursor pair that the buffer must expose after `go_to_index()` selects the same completion.
8. A string appended through `History.append_string()` must appear in the next `History.load()` result and in `get_strings()` after loading.
9. Formatted text accepted by prompts, toolbars, completions, styles, and `print_formatted_text()` must pass through the same `to_formatted_text()` conversion rules.
10. A `Style` class used in `HTML`, `FormattedText`, completion display text, prompt message, bottom toolbar, or right prompt must resolve through the same style sheet rules.
11. `print_formatted_text()` without explicit output must use the current `AppSession.output`, the same default output projection used by applications in that session.
12. `create_pipe_input()` text and `DummyOutput` no-render output must drive the same `PromptSession.prompt()` state transitions as terminal input/output, except for visible terminal rendering.

## Public Interface

### Import Surface

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
from prompt_toolkit.shortcuts import PromptSession, prompt, print_formatted_text
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

There is no required command-line entry point for the covered surface. `__version__` must be a string and `VERSION` must be a tuple; the first three dot-separated components of `__version__` must equal the string representations of the first three elements of `VERSION`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `prompt` | function | Create a one-shot prompt session and return accepted input |
| `PromptSession` | class | Reusable prompt session holding configuration, history, and buffer |
| `Application` | class | Full-screen application managing layout, key bindings, and event-loop lifecycle |
| `AppSession` | class | Per-context holder of default input and output |
| `create_app_session` | context manager | Create and activate a scoped application session |
| `get_app` | function | Return the active application or a dummy application |
| `get_app_or_none` | function | Return the active application or `None` |
| `get_app_session` | function | Return the current application session |
| `Buffer` | class | Editable text state with cursor, history, completion, and validation |
| `CompletionState` | class | Snapshot of current completion candidates and selection |
| `EditReadOnlyBuffer` | exception | Raised on mutation of a read-only buffer |
| `Document` | class | Immutable text-and-cursor view for buffer content |
| `Completion` | class | Single completion candidate with insertion text and display metadata |
| `CompleteEvent` | class | Describes whether completion was typed or explicitly requested |
| `Completer` | class | Base class for completion providers |
| `WordCompleter` | class | Prefix-matching completer from a word list |
| `NestedCompleter` | class | Multi-level completer selected by input prefix words |
| `FuzzyCompleter` | class | Ordered-subsequence wrapper around another completer |
| `FuzzyWordCompleter` | class | Word list completer with fuzzy matching |
| `PathCompleter` | class | Filesystem path completer |
| `ThreadedCompleter` | class | Wrapper running a synchronous completer off the event loop |
| `DynamicCompleter` | class | Completer resolved from a callable at each request |
| `ConditionalCompleter` | class | Completer active only when a filter is true |
| `DummyCompleter` | class | Completer that returns no completions |
| `merge_completers` | function | Combine completions from multiple completers |
| `get_common_complete_suffix` | function | Compute shared suffix of active completions |
| `History` | class | Base class for input history backends |
| `InMemoryHistory` | class | History stored in process memory |
| `FileHistory` | class | History persisted to a file |
| `DummyHistory` | class | History that ignores all entries |
| `ThreadedHistory` | class | Wrapper loading and storing history off the event loop |
| `Validator` | class | Base class for input validators |
| `ValidationError` | exception | Raised for invalid input with cursor position and message |
| `DummyValidator` | class | Validator that accepts every input |
| `ConditionalValidator` | class | Validator active only when a filter is true |
| `DynamicValidator` | class | Validator resolved from a callable at each request |
| `ThreadedValidator` | class | Wrapper running validation off the event loop |
| `KeyBindings` | class | Registry of key-sequence-to-handler bindings |
| `KeyBindingsBase` | class | Abstract base for key binding registries |
| `ConditionalKeyBindings` | class | Key bindings active only when a filter is true |
| `merge_key_bindings` | function | Combine multiple key binding registries |
| `KeyPress` | class | Represents a single key press event |
| `KeyPressEvent` | class | Event object passed to key binding handlers |
| `to_formatted_text` | function | Convert any supported value to formatted-text fragments |
| `FormattedText` | class | List of `(style, text)` fragments |
| `HTML` | class | Parse HTML markup into styled fragments |
| `ANSI` | class | Parse ANSI escape sequences into styled fragments |
| `Template` | class | Placeholder-based formatted-text builder |
| `PygmentsTokens` | class | Convert Pygments token pairs to styled fragments |
| `merge_formatted_text` | function | Concatenate formatted-text items |
| `fragment_list_to_text` | function | Extract plain text from formatted fragments |
| `to_plain_text` | function | Extract plain text from a formatted-text value |
| `print_formatted_text` | function | Print styled or plain values to terminal output |
| `Style` | class | Ordered collection of class-to-style rules |
| `Attrs` | namedtuple | Resolved style attributes for one text fragment |
| `Priority` | enum | Rule-ordering strategies for `Style.from_dict` |
| `parse_color` | function | Validate and normalize color names and hex strings |
| `merge_styles` | function | Combine multiple style sheets |
| `pygments_token_to_classname` | function | Convert a Pygments token to a dotted class name |
| `SwapLightAndDarkStyleTransformation` | class | Style transformation swapping light and dark colors |
| `AdjustBrightnessStyleTransformation` | class | Style transformation clamping color brightness |
| `ColorDepth` | enum | Terminal color-depth levels |
| `DummyOutput` | class | No-op output for testing |
| `create_pipe_input` | context manager | Create a pipe-based input for test-driven prompt use |
| `create_input` | function | Create a platform-appropriate input object |
| `ANSI_COLOR_NAMES` | constant | Mapping of ANSI color names |
| `style_from_pygments_cls` | function | Create a style from a Pygments style class |
| `style_from_pygments_dict` | function | Create a style from a Pygments style dictionary |

### CLI Entry Points

There is no console script for this package. `python -m prompt_toolkit` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Assessment observes only the public behavior described in this specification: importable names, prompt and application runs driven through pipe input and `DummyOutput`, buffer and document state, completion, history, validation, key bindings, formatted text conversion, style resolution, and the documented error classes. Each checked behavior is observed through public imports, returned values, raised exception classes, and object state. Private modules, private attributes, exact `repr` output, exact exception wording, and terminal escape-sequence bytes are not examined.
