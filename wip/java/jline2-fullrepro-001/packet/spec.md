# JLine Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jline` is a Java console-input library that turns character streams, terminal capabilities, key bindings, history, and completion providers into editable line-oriented sessions.

The installable Maven coordinate is `jline:jline`. One console session exposes the same mutable line state through returned lines, a cursor buffer, history navigation and persistence, completion candidates and replacement offsets, key-map bindings, terminal capability queries, and emitted output.

## Non-Goals

- This specification does not require native operating-system console integration, Jansi behavior, terminal device commands, signal handlers, clipboard access, or platform-specific concrete terminal classes.
- This specification does not define contracts for private implementation packages, console-configuration carriers, terminfo parsing, stty parsing, logging, shutdown-hook layout, or nonblocking-reader implementation details.
- This specification does not require every Emacs or vi editing operation represented by `Operation`; the required editing, history, completion, and binding families are stated below.
- This specification does not require exact exception-message text, log text, object representation strings, thread names, or shutdown timing.
- This specification does not define a console application, Maven plugin goal, or network service.

## Representative Workflows

The first workflow reads two lines through a deterministic, unsupported terminal and observes the accepted lines through both the return value and history.

```java
byte[] input = "first\nsecond\n".getBytes(StandardCharsets.UTF_8);
ByteArrayOutputStream output = new ByteArrayOutputStream();
ConsoleReader reader = new ConsoleReader(
    "demo",
    new ByteArrayInputStream(input),
    output,
    new UnsupportedTerminal(),
    "UTF-8"
);
MemoryHistory history = new MemoryHistory();
reader.setHistory(history);
reader.setExpandEvents(false);

String first = reader.readLine("> ");
String second = reader.readLine("> ");
reader.close();
```

Both return values omit line terminators. The history contains the two accepted values in order, its navigation position is after the last entry, and the cursor buffer is empty after each acceptance.

The second workflow completes a token, accepts it, persists it, and reloads the same history through a separate object.

```java
Path path = Files.createTempFile("console-history", ".txt");
FileHistory history = new FileHistory(path.toFile());
history.clear();

ByteArrayOutputStream output = new ByteArrayOutputStream();
Terminal terminal = new TerminalSupport(true) { };
ConsoleReader reader = new ConsoleReader(
    new ByteArrayInputStream("star\t\n".getBytes(StandardCharsets.UTF_8)),
    output,
    terminal
);
reader.setHistory(history);
reader.addCompleter(new StringsCompleter("start", "status", "stop"));

String accepted = reader.readLine();
history.flush();
FileHistory reloaded = new FileHistory(path.toFile());
```

The completion family supplies sorted prefix candidates and a replacement offset. The completion handler updates the cursor buffer, the accepted value enters history, and `flush` makes the ordered entries available to the reloaded history.

## Console Sessions and Editing

Console sessions coordinate streams, prompts, key bindings, mutable cursor state, accepted-line results, and output.

**Construction and projections.**

- A `ConsoleReader` must accept input and output streams, with overloads for an application name, a `Terminal`, and an encoding name.
- WHEN the supplied `Terminal` is null, THEN `ConsoleReader` must obtain the process terminal from `TerminalFactory`.
- WHEN the supplied terminal implements only `Terminal`, THEN `ConsoleReader.getTerminal()` must return a `Terminal2` wrapper that delegates base terminal operations and supplies default capabilities.
- A newly constructed reader must expose its effective input, output writer, terminal, `CursorBuffer`, current `KeyMap`, empty completer collection, default `MemoryHistory`, and default `CandidateListCompletionHandler` through the named getters.
- IF construction or stream wrapping fails, THEN the constructor must raise `IOException`.

**Line acceptance and stream boundaries.**

- WHEN `readLine` accepts a line, THEN it must return the buffer text without a trailing carriage return or line feed.
- WHEN end-of-stream occurs while the buffer is empty, THEN `readLine` must return null.
- WHEN end-of-stream occurs after characters have entered the buffer, THEN `readLine` must return those characters as the final line.
- WHEN an unsupported terminal receives carriage return followed by line feed, THEN the first call must accept at carriage return and the following call must consume the paired line feed rather than return an extra empty line.
- WHEN a nonempty unmasked line is accepted while history is enabled, THEN the reader must add its history representation, move history to its end position, clear the buffer, and reset the cursor to zero.
- WHEN a line is read in editable terminal mode with a nonnull mask, THEN the reader must echo that character in place of each entered character and must not add the line to history.
- WHEN editable terminal mode uses `ConsoleReader.NULL_MASK`, THEN the reader must emit no character echo for the entered text.
- WHEN history is disabled, THEN accepted lines must still be returned and must not be added to the configured `History`.
- WHEN user-interrupt handling is enabled in editable terminal mode and the interrupt binding is read, THEN `readLine` must raise `UserInterruptException` whose `getPartialLine()` returns the text entered before the interrupt.
- WHEN `close` or deprecated `shutdown` runs, THEN the reader must shut down its input reader and release its blocking-read resource.
- IF an input or output operation fails during reading, drawing, movement, printing, completion, or flushing, THEN the public operation must raise `IOException`.

**History expansion and reader settings.**

- `setExpandEvents`, `setCopyPasteDetection`, `setBellEnabled`, `setHandleUserInterrupt`, `setHandleLitteralNext`, `setCommentBegin`, `setPrompt`, `setEchoCharacter`, `setAutoprintThreshold`, `setPaginationEnabled`, and `setHistoryEnabled` must update the values returned by their corresponding getters.
- WHEN copy/paste detection is enabled and a tab is immediately followed by another input character, THEN editable line reading must insert a literal tab instead of invoking completion.
- WHEN literal-next handling is enabled and the quoted-insert binding precedes an input character, THEN editable line reading must insert that character without applying its normal binding.
- WHEN event expansion is enabled, THEN accepted input must support previous-event, absolute-event, relative-event, prefix-search, substring-search, current-prefix, last-argument, and leading quick-substitution designators, with backslash escaping for event markers.
- IF an enabled event designator does not resolve, THEN line acceptance must emit the configured bell when enabled, return an empty string, clear the buffer, and leave history unchanged.
- WHEN event expansion is disabled, THEN exclamation marks and a leading caret sequence must remain literal in both the returned line and its history entry.
- WHEN `beep` is called while bell output is disabled, THEN the output must remain unchanged.
- WHEN `beep` is called while bell output is enabled, THEN the reader must emit `ConsoleReader.KEYBOARD_BELL` and flush it.

**Cursor buffer and direct editing.**

- A `CursorBuffer` must expose its mutable `buffer` and `cursor`, report `length`, `current`, `nextChar`, `upToCursor`, overtyping mode, and full text, and return an independent state copy from `copy`.
- WHEN `CursorBuffer.write` runs in insertion mode, THEN it must insert at `cursor` and advance the cursor by the inserted character count.
- WHEN `CursorBuffer.write` runs in overtyping mode, THEN it must replace the following existing character range where such characters exist and advance the cursor by the inserted character count.
- WHEN `CursorBuffer.current` is called at cursor zero or `nextChar` is called at the end, THEN it must return the null character.
- WHEN `CursorBuffer.clear` removes content, THEN it must return true and reset cursor and text; WHEN it is already empty, THEN it must return false.
- IF `CursorBuffer.write` receives a null character sequence, THEN it must raise `NullPointerException`.
- WHEN `ConsoleReader.moveCursor` requests a position outside the line, THEN it must clamp movement to the beginning or end and return the signed distance actually moved.
- WHEN `setCursorPosition` requests the current position, THEN it must return true without changing the buffer.
- WHEN `backspace` runs at the beginning or `delete` runs at the end, THEN it must return false without changing text; otherwise it must remove the adjacent character and return true.
- WHEN `killLine` runs before the end, THEN it must remove text from the cursor through the end, add that text to the `KillRing`, and return true; WHEN the cursor is at the end, THEN it must return false.
- WHEN consecutive `KillRing.add` calls are not separated by `resetLastKill`, THEN the ring must concatenate the killed text in forward order; `addBackwards` must concatenate it in reverse-kill order.
- WHEN `yank` runs on an empty ring, THEN it must return null; WHEN `yankPop` does not follow a yank, THEN it must return null.

**Bindings, output, and search.**

- A `KeyMap` must bind character sequences to `Operation`, macro `String`, `ActionListener`, or nested `KeyMap` values and must return the bound value from `getBound`.
- WHEN a bound sequence is extended with a longer sequence, THEN the shorter prefix must project as a nested `KeyMap` and the longer sequence must retain its assigned terminal value.
- WHEN `getBound` receives an unbound, null, or empty sequence, THEN it must return null; WHEN a character above byte range is queried, THEN it must return `Operation.SELF_INSERT`.
- `KeyMap.keyMaps` must return named Emacs and vi insertion/movement maps, including the documented canonical names and aliases, and `ConsoleReader.setKeyMap` must return false for an unknown name.
- WHEN `readBinding` consumes a complete binding, THEN it must return the terminal bound value and `getLastBinding` must return the consumed character sequence.
- WHEN `print`, `println`, `drawLine`, `redrawLine`, `putString`, `resetPromptLine`, `printSearchStatus`, `printForwardSearchStatus`, or `restoreLine` changes visible output, THEN the method must preserve the logical cursor-buffer text except where its contract explicitly replaces that text.
- WHEN `searchBackwards` or `searchForwards` is called with `startsWith` false, THEN it must return the nearest history index containing the search term in the requested direction; WHEN `startsWith` is true, THEN it must require a prefix match; WHEN no match exists, THEN it must return `-1`.

## History and Persistence

History maintains an ordered, bounded sequence together with a navigation cursor and optional file projection.

**Entries, indices, and retention.**

- A new `MemoryHistory` must be empty, use `DEFAULT_MAX_SIZE`, ignore consecutive duplicates, preserve surrounding whitespace, and place its navigation cursor at the end.
- WHEN `setAutoTrim(true)` is active, THEN `add` must trim leading and trailing whitespace before duplicate detection and storage.
- WHEN duplicate suppression is active and an added item equals the current last item, THEN `add` must leave size, entries, and index unchanged.
- WHEN an addition exceeds `maxSize`, THEN history must discard oldest entries until size is within the limit and must retain monotonically increasing public entry indices through the offset.
- `size`, `isEmpty`, `index`, `get`, `set`, `remove`, `removeFirst`, `removeLast`, `replace`, `entries`, `iterator`, and `History.Entry.index/value` must project the current ordered history state.
- WHEN `clear` runs, THEN it must remove every entry and reset public index and offset to zero.
- WHEN `replace` runs on nonempty history, THEN it must replace the last entry through normal add policy.
- IF `add` receives null, THEN it must raise `NullPointerException`.
- IF indexed access is outside the retained history range, THEN it must raise `IndexOutOfBoundsException`.
- IF first, last, or replacement removal is requested from empty history, THEN it must raise `NoSuchElementException`.
- IF a caller invokes mutation on an iterator returned by `entries`, THEN it must raise `UnsupportedOperationException`.

**Navigation.**

- WHEN history is at its end position, THEN `current` must return the empty string.
- WHEN `previous` or `next` reaches a valid adjacent position, THEN it must update the navigation index and return true; WHEN movement would cross a boundary, THEN it must return false without changing position.
- WHEN `moveToFirst`, `moveToLast`, or `moveTo` changes to a valid different entry, THEN it must return true and make that entry current; WHEN the target is absent or already current, THEN it must return false.
- WHEN `moveToEnd` runs, THEN it must set the navigation index immediately after the last retained entry.

**File-backed history.**

- A `FileHistory` must retain the absolute form of its configured `File`, and construction with initialization enabled must load an existing file in line order.
- WHEN construction uses `doInit` false, THEN the object must remain unloaded until `load` is called.
- WHEN `load` receives a `File`, `InputStream`, or `Reader`, THEN it must append each input line through the normal bounded-history retention policy.
- WHEN `load` targets a file that does not exist, THEN it must leave in-memory history unchanged and return normally.
- WHEN `flush` runs, THEN it must create missing parent directories and the target file as needed, replace target contents, and write one retained entry per platform line in iteration order.
- WHEN `purge` runs, THEN it must clear in-memory history and remove the backing file when it exists.
- WHEN backing-file deletion reports failure during `purge`, THEN in-memory history must remain cleared and the method must return normally.
- IF history loading or flushing encounters a filesystem or stream failure, THEN it must raise `IOException`.

## Completion and Argument Tokenization

Completion separates candidate discovery from buffer replacement and supports string, enum, file, aggregate, and argument-aware strategies.

**Completion protocol and reader integration.**

- `Completer.complete` must receive the full buffer, cursor position, and mutable candidate list, append sorted candidates, and return the buffer offset from which replacement applies or `-1` when it supplies no completion.
- WHEN multiple completers are registered on a reader, THEN completion must use the first completer that returns an offset other than `-1` and pass its accumulated candidates and offset to the configured `CompletionHandler`.
- `addCompleter` and `removeCompleter` must report whether the collection changed, and `getCompleters` must return an unmodifiable ordered view.
- IF `setCompletionHandler` receives null, THEN it must raise `NullPointerException`.

**String, enum, null, and aggregate completion.**

- A `StringsCompleter` must retain a sorted unique set exposed by `getStrings`; WHEN the buffer is null, THEN it must append every string; otherwise it must append strings beginning with the buffer.
- WHEN `StringsCompleter` appends at least one candidate, THEN it must return zero; WHEN no candidate matches, THEN it must return `-1`.
- An `AnsiStringsCompleter` must match on ANSI-stripped text while returning original decorated strings in stripped-key sort order.
- An `EnumCompleter` must derive candidates from enum constant names, lowercase them by default, and preserve original case when `toLowerCase` is false.
- `NullCompleter.INSTANCE` must append no candidates and return `-1` for every input.
- WHEN `AggregateCompleter` invokes its child completers, THEN it must return the greatest replacement offset and append results only from children that returned that same greatest offset.
- IF a string or aggregate completer receives a null candidate list, THEN it must raise `NullPointerException`.

**Arguments and delimiters.**

- An `ArgumentCompleter` must accept an `ArgumentDelimiter` and ordered child completers, use the child matching the cursor argument index, and reuse the last child beyond the configured child count.
- WHILE strict mode is true, completion of argument `N` must fail with `-1` unless every earlier argument is an exact candidate of its corresponding child; WHILE strict mode is false, earlier arguments must not gate the current completion.
- WHEN a child returns an argument-relative offset, THEN `ArgumentCompleter` must translate it to the corresponding whole-buffer offset.
- WHEN completion occurs before an existing delimiter in the middle of a buffer, THEN trailing delimiters must be removed from returned candidates before insertion.
- `WhitespaceArgumentDelimiter` must split on unquoted, unescaped `Character.isWhitespace` characters, omit quote and escape markers from tokens, and preserve quoted or escaped whitespace inside a token.
- An `ArgumentList` must expose and update its arguments, cursor argument index, current cursor argument, argument-relative position, and whole-buffer position through its named accessors.
- WHEN the cursor argument index is outside the argument array, THEN `ArgumentList.getCursorArgument` must return null.

**Filesystem candidates and candidate handling.**

- A `FileNameCompleter` must resolve relative input from the current user directory, expand a leading tilde to the user home, return candidates relative to the final path segment, and leave wildcard characters uninterpreted.
- WHEN a matching candidate is a directory and is the sole match, THEN `FileNameCompleter` must append the platform separator; otherwise each file candidate must end with a space.
- WHEN the completion directory is unreadable, THEN `FileNameCompleter` must return `-1`; WHEN the directory is readable but no entry matches, THEN it must return the path-segment replacement offset with an empty candidate list.
- WHEN `CandidateListCompletionHandler` receives one candidate different from the current buffer, THEN it must replace from the supplied offset, strip ANSI decoration, append a space at end-of-buffer when configured, set the cursor after the inserted value, and return true.
- WHEN the sole candidate equals the current buffer, THEN the handler must return false without changing the buffer.
- WHEN the handler receives multiple candidates, THEN it must insert their case-insensitive common prefix from the supplied offset, print distinct candidates in stable first-seen order, redraw the line, and return true.
- WHEN distinct candidates exceed the reader autoprint threshold, THEN candidate printing must request confirmation before printing the list.
- IF candidate rendering or buffer replacement fails, THEN the completion handler must raise `IOException`.

## Terminal and Display Models

Terminal abstractions isolate session logic from platform terminals and provide dimensions, stream wrapping, echo state, and named capabilities.

**Base terminal behavior.**

- `Terminal` must expose initialization, restoration, reset, support, dimensions, ANSI support, input/output wrapping, wrap policy, echo state, interrupt-character control, and output encoding through its public members.
- A `TerminalSupport` subclass must report its constructor-supplied support flag, default width `80`, default height `24`, default weird-wrap true, mutable echo and ANSI flags, passthrough input/output streams, and null output encoding unless overridden.
- WHEN `TerminalSupport.reset` runs, THEN it must perform restoration followed by initialization.
- WHEN `UnsupportedTerminal` is constructed without flags, THEN it must report unsupported, ANSI-disabled, and echo-enabled; WHEN constructed with flags, THEN it must report the supplied ANSI and echo values.
- A `DefaultTerminal2` must delegate every `Terminal` member to its wrapped terminal and expose default named boolean and string capabilities derived from support, ANSI, and weird-wrap projections.
- WHEN `DefaultTerminal2.getNumericCapability` is called, THEN it must return null.

**Factory and capabilities.**

- `TerminalFactory.configure(String)` and `configure(Type)` must set the terminal selector used by later creation, and accepted built-in selectors must include automatic, Unix, OSv, Windows, and none/off/false aliases.
- WHEN the configured selector requests none, off, or false, THEN `TerminalFactory.create` must return an `UnsupportedTerminal`.
- WHEN automatic or custom terminal creation or initialization fails, THEN `TerminalFactory.create` must return an `UnsupportedTerminal` rather than propagate that construction failure.
- `TerminalFactory.get` must cache one process terminal until `reset`, and `resetIf` must clear the cache only when its argument is the cached instance.
- `registerFlavor` must replace the class associated with a `TerminalFactory.Flavor`, and `getFlavor` must instantiate the registered class, using its string constructor when a terminal-device argument is supplied.
- IF `TerminalFactory.configure` receives null, THEN it must raise `NullPointerException`.

**Display width.**

- `WCWidth.wcwidth` must return zero for the null character and nonspacing or enclosing combining characters, `-1` for C0/C1 controls and DEL, two for East Asian wide or full-width code points, and one for remaining printable code points.

## State Model

The core state is one console session composed of stream position, terminal projection, key map, cursor buffer, history sequence and navigation index, completer order, completion handler settings, and output position.

- The accepted-line state must project through `readLine` or `accept`, `CursorBuffer`, configured `History`, and output.
- The editing state must project through `CursorBuffer.buffer`, `CursorBuffer.cursor`, direct editing methods, and key-bound `Operation` results.
- The history state must project through indexed access, entry iteration, navigation, console history search, and file contents after `flush`.
- The completion state must project through completer candidates and offsets, `CompletionHandler` buffer updates, cursor position, and printed candidate output.
- The key-binding state must project through `KeyMap.getBound`, `ConsoleReader.readBinding`, and `getLastBinding`.
- The terminal state must project through capability and dimension getters, stream wrapping, echo behavior, and console output decisions.

## Error Semantics

The following failures are part of the public contract.

| Condition | Required result |
|---|---|
| Console construction or public console I/O fails | IF construction, stream wrapping, reading, drawing, completion output, or flushing fails, THEN the operation must raise `IOException`. |
| Ctrl-C is handled by the reader | WHEN interrupt handling is enabled in editable terminal mode and the interrupt binding is read, THEN `readLine` must raise `UserInterruptException` with the partial line. |
| A required collection, stream, file, item, or handler is null | IF a documented nonnull argument is null, THEN the receiving API must raise `NullPointerException`. |
| A history index is outside the retained range | IF indexed history access is invalid, THEN history must raise `IndexOutOfBoundsException`. |
| Empty history removal or replacement is requested | IF no element exists for first, last, or replacement removal, THEN history must raise `NoSuchElementException`. |
| A history iterator mutation is requested | IF iterator `remove`, `set`, or `add` is called, THEN it must raise `UnsupportedOperationException`. |
| File history I/O fails | IF loading or flushing cannot complete, THEN `FileHistory` must raise `IOException`. |
| Event expansion cannot resolve a designator | IF enabled expansion cannot resolve an event, THEN line acceptance must return an empty string, clear the buffer, signal the configured bell, and preserve history. |

## Cross-View Invariants

1. WHEN a nonempty unmasked line is accepted with expansion disabled and history enabled, THEN the returned line and newest history entry must contain equal text, the history index must be at end, and the cursor buffer must be empty at cursor zero.
2. Every retained `History.Entry` index and value must agree with indexed `History.get`, iterator order, navigation results, and console history-search results for the same history state.
3. WHEN `FileHistory.flush` succeeds, THEN reloading that file must reproduce the retained entry values and order subject to the reloaded object's maximum-size policy.
4. WHEN a completer returns candidates and an offset, THEN the completion handler's replacement must begin at that offset and the reader's cursor buffer, cursor position, and accepted-line result must agree on the resulting text.
5. WHEN `KeyMap.getBound` reports a terminal value for a sequence, THEN `ConsoleReader.readBinding` over the same sequence and map must return that value and `getLastBinding` must report that sequence.
6. `CursorBuffer.length`, `toString`, public `buffer`, `cursor`, `current`, `nextChar`, and `upToCursor` must describe one consistent line state after every write, movement, deletion, kill, yank, or clear operation.
7. A `DefaultTerminal2` projection must preserve every base terminal result while its named capability results must agree with the wrapped terminal's support, ANSI, and weird-wrap state.
8. WHEN an unsupported terminal is used, THEN stream line boundaries, returned lines, history entries, and cursor-buffer reset must remain consistent without native terminal behavior.

## Public Interface

### Import Surface

```java
import jline.Terminal;
import jline.Terminal2;
import jline.TerminalSupport;
import jline.UnsupportedTerminal;
import jline.DefaultTerminal2;
import jline.TerminalFactory;
import jline.TerminalFactory.Type;
import jline.TerminalFactory.Flavor;
import jline.console.ConsoleReader;
import jline.console.CursorBuffer;
import jline.console.KeyMap;
import jline.console.Operation;
import jline.console.KillRing;
import jline.console.UserInterruptException;
import jline.console.WCWidth;
import jline.console.history.History;
import jline.console.history.History.Entry;
import jline.console.history.PersistentHistory;
import jline.console.history.MemoryHistory;
import jline.console.history.FileHistory;
import jline.console.completer.Completer;
import jline.console.completer.CompletionHandler;
import jline.console.completer.StringsCompleter;
import jline.console.completer.AnsiStringsCompleter;
import jline.console.completer.EnumCompleter;
import jline.console.completer.NullCompleter;
import jline.console.completer.AggregateCompleter;
import jline.console.completer.FileNameCompleter;
import jline.console.completer.CandidateListCompletionHandler;
import jline.console.completer.ArgumentCompleter;
import jline.console.completer.ArgumentCompleter.ArgumentDelimiter;
import jline.console.completer.ArgumentCompleter.AbstractArgumentDelimiter;
import jline.console.completer.ArgumentCompleter.WhitespaceArgumentDelimiter;
import jline.console.completer.ArgumentCompleter.ArgumentList;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Terminal` | interface | Defines the platform-independent terminal lifecycle and projections. |
| `Terminal2` | interface | Adds named boolean, numeric, and string capabilities. |
| `TerminalSupport` | abstract class | Supplies default terminal state and pass-through behavior. |
| `UnsupportedTerminal` | class | Provides deterministic stream-only terminal behavior. |
| `DefaultTerminal2` | class | Adapts a base terminal to named capabilities. |
| `TerminalFactory` | class | Configures, creates, registers, and caches terminals. |
| `TerminalFactory.Type` | enum | Names built-in terminal selection modes. |
| `TerminalFactory.Flavor` | enum | Names replaceable native terminal families. |
| `ConsoleReader` | class | Coordinates editable line reading, history, completion, binding, and output. |
| `CursorBuffer` | class | Exposes mutable text, cursor position, and insertion mode. |
| `KeyMap` | class | Maps character sequences to editing operations, macros, callbacks, or nested maps. |
| `Operation` | enum | Names the public editing-operation vocabulary used by key maps. |
| `KillRing` | class | Retains killed text and yank/yank-pop state. |
| `UserInterruptException` | exception | Carries a partial line from a handled user interrupt. |
| `WCWidth` | class | Computes terminal column width for a Unicode code point. |
| `History` | interface | Defines ordered history storage, iteration, and navigation. |
| `History.Entry` | interface | Projects one public history index and value. |
| `PersistentHistory` | interface | Adds flush and purge operations to history. |
| `MemoryHistory` | class | Implements bounded configurable in-memory history. |
| `FileHistory` | class | Adds line-oriented file loading, flushing, and purging. |
| `Completer` | interface | Produces completion candidates and a replacement offset. |
| `CompletionHandler` | interface | Applies and presents completion candidates to a reader. |
| `StringsCompleter` | class | Completes from sorted plain strings. |
| `AnsiStringsCompleter` | class | Matches ANSI-decorated strings by undecorated text. |
| `EnumCompleter` | class | Completes from enum constant names. |
| `NullCompleter` | class | Supplies the shared no-completion sentinel. |
| `AggregateCompleter` | class | Combines results that share the greatest replacement offset. |
| `FileNameCompleter` | class | Completes local filesystem path segments. |
| `CandidateListCompletionHandler` | class | Inserts single/common candidates and prints distinct choices. |
| `ArgumentCompleter` | class | Dispatches completion by delimited argument position. |
| `ArgumentDelimiter` | interface | Splits a command buffer and identifies delimiter positions. |
| `AbstractArgumentDelimiter` | abstract class | Supplies quote and escape-aware delimiter behavior. |
| `WhitespaceArgumentDelimiter` | class | Treats unquoted, unescaped Java whitespace as delimiters. |
| `ArgumentList` | class | Projects token and cursor positions from delimiter parsing. |

### CLI Entry Points

There is no console script for this artifact. Executable-JAR invocation is not supported. Programmatic use is through Java imports.

## Appendix A: Environment

The working environment runs Java 17 and Maven 3.9 on Linux without network access. The offline Maven repository provides Jansi, JUnit, and the remaining transitive artifacts required by the declared build. The assessment environment provides the same runtime and offline artifact set.

The project must declare Maven metadata in `pom.xml` at the project root. The POM must use coordinates `jline:jline`, JAR packaging, a Java 17-compatible build, and every runtime dependency required by the implementation.

## Appendix B: Assessment Notes

Assessment compiles the Maven artifact and invokes the public Java interfaces with in-memory streams, temporary local files, deterministic terminal implementations, custom key bindings, and completion providers. Checks cover line boundaries, cursor and editing state, history retention/navigation/persistence, completion offsets and insertion, key-map decoding, terminal capabilities, Unicode display width, error behavior, and consistency across returned lines, buffer state, history, files, candidates, bindings, and output. Native operating-system console behavior, private packages, exact diagnostic text, and representation formatting are not inspected.


