# Rich Specification

## Product Overview

Rich is a Python library for rendering styled text and structured terminal output. The central abstraction is a console renderable: strings, Rich objects, and user objects that implement the Rich protocol are rendered by a `Console` into `Segment` objects, and those segments are projected to terminal text, ANSI output, captured strings, recorded buffers, HTML, SVG, Jupyter display, progress/live displays, and file output.

Rich is designed for command-line applications and developer diagnostics. It provides high-level printing, logging, inspection, pretty rendering, tables, panels, columns, trees, markdown, syntax highlighting, JSON rendering, progress bars, status spinners, live displays, prompts, tracebacks, styles, themes, markup, and low-level segment APIs.

## Scope

This specification covers the public behavior of:

- Top-level helpers in `rich`: `print`, `print_json`, `inspect`, `get_console`, and `reconfigure`.
- The `Console` rendering surface, including printing, logging, output, input prompts, capture, paging, alternate-screen contexts, render/render-lines APIs, recording, exporting, saving, terminal detection, environment overrides, and color-system handling.
- The Rich render protocol: `__rich__`, `__rich_console__`, `__rich_measure__`, `Group`, `group`, `ConsoleOptions`, `Measurement`, `Segment`, and `Segments`.
- Styles, colors, themes, markup, emoji replacement, hyperlinks, highlighters, and text objects.
- Core renderables: `Text`, `Table`, `Column`, `Row`, `Panel`, `Align`, `Columns`, `Tree`, `Rule`, `Padding`, `Styled`, `Markdown`, `Syntax`, `JSON`, `Pretty`, progress bars, status displays, spinners, bars, live displays, logging handlers, and tracebacks.
- Public module entry points documented for demonstration or file rendering, such as `python -m rich`, `python -m rich.json`, `python -m rich.syntax`, `python -m rich.markdown`, and public demo modules for progress, status, spinner, tree, traceback, themes, default styles, markup, and box styles.

The contract is behavioral: callers should be able to observe the same plain text, ANSI styling decisions, segment structure, exported text/HTML/SVG content, context-manager side effects, and documented error classes for the same public inputs.

## Installable Surface

Rich installs as the `rich` Python package and includes type information via `rich/py.typed`. The package requires the runtime syntax-highlighting and markdown dependencies needed by the documented `Syntax` and `Markdown` renderables.

The primary import paths are:

```python
from rich import get_console, inspect, print, print_json, reconfigure
from rich.console import Capture, Console, ConsoleOptions, Group, RenderResult, group
from rich.errors import (
    LiveError,
    MarkupError,
    MissingStyle,
    NoAltScreen,
    NotRenderableError,
    StyleSyntaxError,
)
from rich.measure import Measurement
from rich.segment import Segment, Segments, ControlType
from rich.style import Style
from rich.color import Color
from rich.theme import Theme
from rich.text import Text
from rich.markup import escape, render
from rich.table import Column, Row, Table
from rich.progress import Progress, track, open, wrap_file
from rich.progress import (
    BarColumn,
    DownloadColumn,
    FileSizeColumn,
    MofNCompleteColumn,
    ProgressColumn,
    RenderableColumn,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TotalFileSizeColumn,
    TransferSpeedColumn,
)
from rich.json import JSON
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.pretty import Pretty, pprint, install
from rich.panel import Panel
from rich.align import Align
from rich.columns import Columns
from rich.tree import Tree
from rich.live import Live
from rich.status import Status
from rich.spinner import Spinner
from rich.logging import RichHandler
from rich.traceback import Traceback, install
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich.filesize import decimal
```

The `rich.box` module exposes preset box-style constants for tables and panels. Public docs also expose reference modules for alignment, bars, colors, controls, emoji, highlighters, layout, measurement, padding, progress bars, prompts, rules, styled renderables, terminal themes, and tracebacks.

Command modules behave as follows:

- `python -m rich` renders a feature demonstration to the current console.
- `python -m rich.json PATH` pretty-prints JSON from a path or `-` for stdin and supports `--indent`.
- `python -m rich.syntax PATH` renders syntax-highlighted code from a path or `-` for stdin, with options for force color, indent guides, line numbers, width, wrapping, soft wrapping, theme, background color, lexer, padding, and highlighted lines.
- `python -m rich.markdown PATH` renders markdown from a path or `-` for stdin, with options for force color, code theme, inline-code lexer, hyperlinks, width, full justification, and paging.

## Public API

Top-level helpers:

```python
get_console() -> Console
reconfigure(*args, **kwargs) -> None
print(*objects, sep=" ", end="\n", file=None, flush=False) -> None
print_json(json=None, *, data=None, indent=2, highlight=True, skip_keys=False,
           ensure_ascii=False, check_circular=True, allow_nan=True,
           default=None, sort_keys=False) -> None
inspect(obj, *, console=None, title=None, help=False, methods=False,
        docs=True, private=False, dunder=False, sort=True, all=False,
        value=True) -> None
```

`get_console()` returns the process-global console used by top-level helpers. `reconfigure()` constructs a replacement `Console` with the supplied arguments and updates the global console in place. Top-level `print()` mirrors the built-in print signature, renders through Rich, always flushes as part of console writing, and uses a temporary `Console(file=file)` when a file object is supplied. `print_json()` delegates to the global console's JSON rendering. `inspect()` renders a report for a Python object and can include methods, full help text, docs, private names, dunder names, sorted attributes, all attributes, and/or values.

Console construction accepts named configuration, including `color_system="auto"`, `force_terminal`, `force_jupyter`, `force_interactive`, `soft_wrap`, `theme`, `stderr`, `file`, `quiet`, `width`, `height`, `style`, `no_color`, `tab_size`, `record`, `markup`, `emoji`, `emoji_variant`, `highlight`, `log_time`, `log_path`, `log_time_format`, `highlighter`, `legacy_windows`, `safe_box`, `get_datetime`, and `get_time`. Explicit constructor arguments take precedence over environment-derived defaults.

Important console methods include:

```python
Console.print(*objects, sep=" ", end="\n", style=None, justify=None,
              overflow=None, no_wrap=None, emoji=None, markup=None,
              highlight=None, width=None, height=None, crop=True,
              soft_wrap=None, new_line_start=False) -> None
Console.log(*objects, sep=" ", end="\n", style=None, justify=None,
            emoji=None, markup=None, highlight=None, log_locals=False) -> None
Console.out(*objects, sep=" ", end="\n", style=None, highlight=None) -> None
Console.render(renderable, options=None) -> Iterable[Segment]
Console.render_lines(renderable, options=None, *, style=None,
                     pad=True, new_lines=False) -> list[list[Segment]]
Console.measure(renderable, *, options=None) -> Measurement
Console.capture() -> Capture
Console.export_text(*, clear=True, styles=False) -> str
Console.export_html(*, theme=None, clear=True, code_format=None,
                    inline_styles=False) -> str
Console.export_svg(*, title="Rich", theme=None, clear=True,
                   code_format=..., font_aspect_ratio=0.61,
                   unique_id=None) -> str
Console.save_text(path, *, clear=True, styles=False) -> None
Console.save_html(path, *, theme=None, clear=True, code_format=...,
                  inline_styles=False) -> None
Console.save_svg(path, *, title="Rich", theme=None, clear=True,
                 code_format=..., font_aspect_ratio=0.61,
                 unique_id=None) -> None
Console.print_json(json=None, *, data=None, indent=2, highlight=True,
                   skip_keys=False, ensure_ascii=False,
                   check_circular=True, allow_nan=True,
                   default=None, sort_keys=False) -> None
Console.input(prompt="", *, markup=True, emoji=True, password=False,
              stream=None) -> str
Console.status(status, *, spinner="dots",
               spinner_style="status.spinner", speed=1.0,
               refresh_per_second=12.5) -> Status
Console.print_exception(*, width=100, extra_lines=3, theme=None,
                        word_wrap=False, show_locals=False,
                        suppress=(), max_frames=100) -> None
```

`Text` is a mutable styled string:

```python
Text(text="", style="", *, justify=None, overflow=None, no_wrap=None,
     end="\n", tab_size=None, spans=None)
Text.from_markup(text, *, style="", emoji=True, emoji_variant=None,
                 justify=None, overflow=None, end="\n") -> Text
Text.from_ansi(text, *, style="", justify=None, overflow=None,
               no_wrap=None, end="\n", tab_size=8) -> Text
Text.assemble(*parts, style="", justify=None, overflow=None,
              no_wrap=None, end="\n", tab_size=8, meta=None) -> Text
Text.append(text, style=None) -> Text
Text.stylize(style, start=0, end=None) -> None
Text.highlight_words(words, style, *, case_sensitive=True) -> int
Text.highlight_regex(pattern, style=None, *, style_prefix="") -> int
```

`Table` and `Column` expose table construction:

```python
Table(*headers, title=None, caption=None, width=None, min_width=None,
      box=..., safe_box=None, padding=(0, 1), collapse_padding=False,
      pad_edge=True, expand=False, show_header=True, show_footer=False,
      show_edge=True, show_lines=False, leading=0, style="none",
      row_styles=None, header_style="table.header",
      footer_style="table.footer", border_style=None,
      title_style=None, caption_style=None, title_justify="center",
      caption_justify="center", highlight=False)
Table.add_column(header="", footer="", *, header_style=None,
                 highlight=None, footer_style=None, style=None,
                 justify="left", vertical="top", overflow="ellipsis",
                 width=None, min_width=None, max_width=None,
                 ratio=None, no_wrap=False) -> None
Table.add_row(*renderables, style=None, end_section=False) -> None
Table.add_section() -> None
Table.grid(*headers, padding=0, collapse_padding=True,
           pad_edge=False, expand=False) -> Table
Column(header="", footer="", header_style="", footer_style="",
       style="", justify="left", vertical="top", overflow="ellipsis",
       width=None, min_width=None, max_width=None, ratio=None,
       no_wrap=False, highlight=False)
```

Progress APIs:

```python
track(sequence, description="Working...", total=None, completed=0,
      auto_refresh=True, console=None, transient=False, get_time=None,
      refresh_per_second=10, style="bar.back",
      complete_style="bar.complete", finished_style="bar.finished",
      pulse_style="bar.pulse", update_period=0.1, disable=False,
      show_speed=True) -> Iterable
Progress(*columns, console=None, auto_refresh=True,
         refresh_per_second=10, speed_estimate_period=30.0,
         transient=False, redirect_stdout=True, redirect_stderr=True,
         get_time=None, disable=False, expand=False)
Progress.add_task(description, start=True, total=100.0,
                  completed=0, visible=True, **fields) -> TaskID
Progress.update(task_id, *, total=None, completed=None, advance=None,
                description=None, visible=None, refresh=False,
                **fields) -> None
Progress.advance(task_id, advance=1) -> None
Progress.reset(task_id, *, start=True, total=None, completed=0,
               visible=None, description=None, **fields) -> None
Progress.track(sequence, total=None, completed=0, task_id=None,
               description="Working...", update_period=0.1) -> Iterable
Progress.open(file, mode="r", buffering=-1, encoding=None, errors=None,
              newline=None, *, total=None, task_id=None,
              description="Reading...")
Progress.wrap_file(file, total=None, *, task_id=None,
                   description="Reading...")
open(file, mode="r", buffering=-1, encoding=None, errors=None,
     newline=None, *, total=None, description="Reading...",
     auto_refresh=True, console=None, transient=False, get_time=None,
     refresh_per_second=10, style="bar.back",
     complete_style="bar.complete", finished_style="bar.finished",
     pulse_style="bar.pulse", disable=False)
wrap_file(file, total, *, description="Reading...", auto_refresh=True,
          console=None, transient=False, get_time=None,
          refresh_per_second=10, style="bar.back",
          complete_style="bar.complete", finished_style="bar.finished",
          pulse_style="bar.pulse", disable=False)
```

Structured renderables and supporting objects include:

```python
JSON(json, indent=2, highlight=True, skip_keys=False, ensure_ascii=False,
     check_circular=True, allow_nan=True, default=None, sort_keys=False)
JSON.from_data(data, indent=2, highlight=True, skip_keys=False,
               ensure_ascii=False, check_circular=True, allow_nan=True,
               default=None, sort_keys=False) -> JSON
Syntax(code, lexer, *, theme="monokai", dedent=False,
       line_numbers=False, start_line=1, line_range=None,
       highlight_lines=None, code_width=None, tab_size=4,
       word_wrap=False, background_color=None,
       indent_guides=False, padding=0)
Syntax.from_path(path, encoding="utf-8", lexer=None, theme="monokai",
                 dedent=False, line_numbers=False, line_range=None,
                 start_line=1, highlight_lines=None, code_width=None,
                 tab_size=4, word_wrap=False, background_color=None,
                 indent_guides=False, padding=0) -> Syntax
Markdown(markup, code_theme="monokai", justify=None, style="none",
         hyperlinks=True, inline_code_lexer=None, inline_code_theme=None)
Pretty(obj, highlighter=None, *, indent_size=4, justify=None,
       overflow=None, no_wrap=False, indent_guides=False,
       max_length=None, max_string=None, max_depth=None,
       expand_all=False, margin=0, insert_line=False)
Live(renderable=None, *, console=None, screen=False, auto_refresh=True,
     refresh_per_second=4, transient=False, redirect_stdout=True,
     redirect_stderr=True, vertical_overflow="ellipsis",
     get_renderable=None)
Live.update(renderable, *, refresh=False) -> None
Traceback(trace=None, *, width=100, code_width=88, extra_lines=3,
          theme=None, word_wrap=False, show_locals=False,
          locals_max_length=10, locals_max_string=80,
          locals_max_depth=None, locals_hide_dunder=True,
          locals_hide_sunder=False, locals_overflow=None,
          indent_guides=True, suppress=(), max_frames=100)
```

`Segment(text, style=None, control=None)` is the low-level rendered unit. Its `cell_length` is the terminal-cell width of `text`, or zero for control segments. Public segment helpers can split lines, crop or pad lines to a cell width, compute line shapes, simplify adjacent same-style segments, strip links/styles/colors, apply a base or post style, and filter control versus printable segments.

`Style` accepts foreground color, background color, boolean attributes, links, and metadata. `Style.parse()` accepts style definitions; styles can be added together and combined. `Theme(styles=None, inherit=True)` maps style names to style definitions or `Style` objects; `Theme.read(path, inherit=True, encoding=None)` loads an INI-style `[styles]` file. `Color.parse()` accepts named colors, numeric color syntax, hex colors, RGB syntax, and the terminal default color.

## Behavioral Sections

### Console Rendering and I/O

`Console.print()` converts each positional object to a Rich renderable. Plain Python containers are pretty-rendered and highlighted; strings are treated as console markup by default; objects with `__rich__`, `__rich_console__`, or `__rich_measure__` participate in the Rich protocol. Objects are separated by `sep` and terminated by `end`, with wrapping, cropping, justification, markup, emoji replacement, highlighting, and style overrides controlled by method arguments or console defaults.

`Console.log()` renders the same kinds of content as `print()` and adds a time column and a source-location column when configured to do so. When `log_locals=True`, the output includes a rendered table of local variables from the call site.

`Console.out()` is lower level: it stringifies positional arguments, joins them with `sep`, writes `end`, and can apply style/highlighting, but it does not pretty print, wrap text, or apply markup.

When writing to a non-terminal file-like object, Rich emits plain text by default and strips terminal control codes. `force_terminal=True` enables terminal escape sequences for file-like outputs. `stderr=True` selects `sys.stderr`; otherwise the console writes to `sys.stdout` unless `file` is provided.

Color systems are `None`, `"auto"`, `"standard"`, `"256"`, `"truecolor"`, and `"windows"`. With `"auto"`, Rich detects terminal capability. `None` disables color. If a requested color is not available in the current color system, output is downgraded to the closest available representation.

Environment variables influence console defaults when constructor arguments do not override them:

- `TERM=dumb` or `TERM=unknown` disables color/style and features that require cursor movement.
- Non-empty `FORCE_COLOR` enables color/styles regardless of `TERM`.
- `NO_COLOR` disables color and takes precedence over `FORCE_COLOR`; non-color attributes such as bold and underline remain meaningful.
- `TTY_COMPATIBLE=1` forces terminal escape compatibility; `TTY_COMPATIBLE=0` forces non-terminal behavior.
- `TTY_INTERACTIVE=1` forces interactive behavior; `TTY_INTERACTIVE=0` disables interactive behavior.
- `COLUMNS` and `LINES` provide width/height defaults. `JUPYTER_COLUMNS` and `JUPYTER_LINES` provide corresponding defaults in Jupyter.

`Console.input()` first renders the prompt with Rich markup and emoji handling, then reads from the supplied stream or standard input, matching built-in `input()` behavior including optional password mode.

### Rendering Protocol and Segments

A custom object may implement `__rich__()` to return another Rich-renderable object. If `__rich__()` returns a string, that string is rendered as console markup unless markup is disabled by the console or call.

A custom object may implement `__rich_console__(console, options)` to yield renderables or `Segment` objects. Yielding strings, `Text`, tables, panels, and other renderables composes normally. Yielding `Segment` objects gives direct control over text, style, and control codes.

A custom object may implement `__rich_measure__(console, options)` to return a `Measurement` with minimum and maximum cell widths. Layout renderables such as tables use this measurement to allocate width.

`Console.render()` returns the segment stream for a renderable. `Console.render_lines()` returns a list of segment lines suitable for layout operations; it can pad lines to the target width, include newline segments, and apply an outer style. Printable segment cell widths ignore style, count double-width characters by terminal cell width, and count control segments as zero width.

`Segments(segments, new_lines=False)` is itself renderable, allowing precomputed segments to be printed. Adjacent printable segments with the same style may be simplified without changing output.

### Recording, Capture, and Export

`Console(record=True)` stores a copy of printed and logged output in a record buffer. `export_text()`, `export_html()`, and `export_svg()` convert the recorded buffer into plain text, HTML, or SVG strings. `save_text()`, `save_html()`, and `save_svg()` write the corresponding export to a path.

Export methods require recorded output to be present. Their `clear` argument defaults to `True`, so an export consumes the current record buffer unless `clear=False` is supplied. `export_text(styles=False)` returns plain text; `styles=True` includes ANSI escape codes. HTML and SVG exports use a terminal theme, preserve styled spans, escape text for the target format, and keep the same visible cell content as the console render.

`Console.capture()` is a context manager. While active, console writes are captured rather than emitted to the console's normal file. Calling `Capture.get()` after the context returns the exact captured string projection for what would have been written.

### Styles, Colors, Themes, Markup, and Highlighting

Style definitions are strings made from color names, `color(number)`, `#rrggbb`, `rgb(r,g,b)`, the special color `default`, background colors prefixed with `on`, attributes such as bold/dim/italic/underline/blink/reverse/strike, and less-common attributes such as double underline, frame, encircle, and overline. Attribute aliases include `b`, `i`, `u`, `r`, `s`, `uu`, and `o`. Prefixing an attribute with `not` turns that attribute off for a span. `link URL` attaches a terminal hyperlink.

`Style.parse()` returns a `Style` object from a style definition and caches parsed definitions. Adding styles applies later settings over earlier ones, with unset attributes leaving previous attributes unchanged. `Style.render()` emits ANSI codes appropriate for the requested color system and legacy-Windows mode.

Theme names must be lower-case, start with a letter, and contain only letters plus `.`, `-`, and `_`. A custom theme inherits Rich's default styles unless `inherit=False`; custom style names override defaults. A console resolves style names through its theme stack and parses style definitions directly when they are not theme names.

Console markup is BBCode-like. `[style]` opens a style, `[/style]` closes the matching named style, and `[/]` closes the most recent open tag. Unclosed tags apply until the end of the string. Tags may overlap; Rich applies the spans implied by the open and close positions rather than requiring strict nesting. `[link=URL]text[/link]` adds a terminal hyperlink style.

Backslash escapes prevent bracketed text from being interpreted as markup. `rich.markup.escape(text)` escapes content for safe insertion into markup and preserves a trailing literal backslash by escaping it as needed. `rich.markup.render()` and `Text.from_markup()` convert markup to `Text`.

Emoji codes in markup are replaced with Unicode characters when emoji handling is enabled. Codes may request a text or emoji variant by suffix. Disabling emoji leaves codes as text.

Rich applies automatic highlighting for common Python-like patterns such as numbers, strings, containers, booleans, `None`, paths, URLs, and UUIDs. `highlight=False` on a console disables this by default; `highlight=True` on a print/log call can re-enable it for that call. `RegexHighlighter` subclasses define named capture groups; matched group names are prefixed by `base_style` to form style names. `Highlighter` subclasses mutate a `Text` object in their `highlight()` method.

### Text

`Text` represents mutable plain text plus styled regions. It can be used anywhere a plain string is accepted by Rich. Most mutating methods operate in place; `append()` returns `self` for chaining.

Constructor options `justify`, `overflow`, `no_wrap`, `end`, and `tab_size` affect rendering when the text is measured or printed. `Text.from_markup()` parses console markup. `Text.from_ansi()` converts ANSI escape sequences into styled text. `Text.assemble()` concatenates strings, `Text` instances, and `(text, style)` pairs into a single `Text`.

`stylize(style, start=0, end=None)` applies a style to the selected character offsets; negative offsets are supported. Word and regex highlighting return the number of matches styled. Regex highlighting can apply one style to the whole match or derive styles from named regex groups.

### Tables and Layout Renderables

A `Table` is constructed, configured, populated with columns and rows, and then printed. Headers may be strings or `Column` instances. Cell values may be strings, `Text`, or any Rich renderable; `None` creates a blank cell. Console markup inside string cells is rendered the same way as markup printed directly.

Rich computes column widths from content, headers, explicit widths, minimum/maximum widths, ratios, no-wrap settings, padding, and available console width. If a table is too narrow for its content, text wraps, crops, or ellipsizes according to the relevant overflow policy. `expand=True` stretches the table to the available width; `width` requests a fixed table width and disables automatic width calculation.

`show_header`, `show_footer`, `show_edge`, `show_lines`, `leading`, `end_section`, and `add_section()` control which separators are visible. By default a table with no columns renders as a blank line. `Table.grid()` creates a borderless layout table with collapsed padding and no outside padding by default.

Box styles are selected with constants from `rich.box`. `box=None` removes table borders. `safe_box=True` forces safer ASCII-compatible drawing when the target terminal should avoid Unicode box characters; `safe_box=False` permits the full box style.

`Panel` draws a border around a renderable and can display title/subtitle text, width/height constraints, padding, highlight handling, and border styles. Panels expand to the available width by default; `expand=False` or `Panel.fit()` creates a panel fitted to its content. `Align` pads a renderable horizontally and optionally vertically. `Columns` lays out renderables in columns with optional equal widths, fixed width, expansion, ordering direction, alignment, and title. `Tree` renders hierarchical labels with guide lines; `Tree.add()` returns the child tree so callers can build nested structures fluently.

### Structured Renderables

`JSON(json, ...)` parses a JSON string, re-dumps it with the configured JSON serialization options, optionally applies JSON highlighting, and renders as no-wrap text. `JSON.from_data(data, ...)` serializes Python data directly. `Console.print_json()` and top-level `print_json()` print a JSON string when `json` is supplied, or serialize `data` when `json is None`; JSON output is printed with soft wrapping enabled so long lines are not hard-wrapped by Rich.

`Syntax` renders code through Pygments. A lexer may be a Pygments lexer object or lexer name. `Syntax.from_path()` reads a file, detects the lexer from the path/content when no lexer is supplied, and applies the same rendering options as the constructor. Line numbers, start line, line ranges, highlighted lines, code width, tab size, word wrap, background color, indent guides, padding, and theme are visible in the rendered output. Themes may be Pygments style names or the special `ansi_dark`/`ansi_light` terminal-aware themes. `background_color="default"` uses the terminal default background.

`Markdown` parses Markdown text and renders terminal-friendly headings, paragraphs, emphasis, lists, block quotes, links, images as text placeholders, tables, rules, and fenced code blocks. Code blocks use syntax highlighting with the configured code theme. Inline code may use an optional inline lexer/theme. Hyperlinks are emitted when enabled and supported by the output projection.

`Pretty`, `pprint()`, and Rich's automatic printing of containers format lists, dicts, sets, dataclasses, attrs-style objects, and objects with a Rich repr protocol. Pretty rendering adapts to console width, can draw indent guides, can expand all containers, and can truncate long containers or long strings while indicating omitted content. An object's `__rich_repr__()` may yield positional values, `(name, value)` pairs, or `(name, value, default)` triples; default-valued keyword entries are omitted. Setting the `angular` attribute on `__rich_repr__` requests angle-bracket repr style. The `rich.repr.auto` decorator can generate a compatible repr from constructor-named attributes.

### Progress, Status, and Live Displays

`track(sequence, ...)` wraps an iterable, yields the same values in order, and updates a transient or persistent progress display as iteration advances. If `total` is omitted and the sequence has a length, that length is used as the total; otherwise callers may supply `total` for indeterminate iterables.

`Progress` is a context manager. Entering starts the live progress display; exiting stops it. Without a context manager, callers must call `start()` and `stop()` themselves. `transient=True` removes the final progress display when stopped; otherwise the final refreshed display remains with the cursor on the following line.

`add_task()` returns a task id. Tasks have descriptions, totals, completed values, visibility, timing information, and arbitrary `fields`. `update()` can replace total, completed, description, visibility, and fields; `advance` adds to the current completed value. Extra fields are available to progress columns through `task.fields`. `start=False` or `total=None` creates an indeterminate/pulsing task until `start_task()` and/or a total are supplied. Task objects are public for reading in columns and callbacks, but user code should mutate tasks through `Progress` methods.

The default progress columns are equivalent to text description, bar, percentage, and time remaining. Custom columns may be format strings evaluated with a single `task` value or `ProgressColumn` instances. Built-in columns render bars, text, elapsed time, remaining time, completed/total counts, file sizes, total file sizes, download counts, transfer speed, spinners, and arbitrary renderables. A column's `table_column` customizes how the progress task table allocates width.

`Progress.open()` and top-level `rich.progress.open()` wrap file reading with a progress bar. Modes are limited to `"r"`, `"rt"`, and `"rb"`. When `total` is omitted for a path, Rich uses the file size. `wrap_file()` wraps an existing binary file object and requires a total unless it can use an existing task total.

Progress and Live displays redirect `stdout` and `stderr` by default so ordinary writes appear above the dynamic display rather than corrupting it. Passing a custom console makes dynamic output share that console. Nested progress displays appear below the outer display and use the outer refresh cadence. In Jupyter, progress auto-refresh is disabled; callers refresh manually or use `track()`.

`Console.status()` creates a context manager showing a spinner and status renderable while the block runs. It does not prevent normal console printing or logging.

`Live` displays a renderable that may be mutated in place or replaced with `Live.update(renderable, refresh=False)`. It defaults to four refreshes per second. With `screen=True`, it uses the alternate screen. With `transient=True`, it clears on exit. `vertical_overflow` controls content taller than the terminal: `"crop"` hides overflow, `"ellipsis"` replaces the last visible line with `"..."`, and `"visible"` permits full output but cannot be cleared reliably. A stopped non-transient live display renders its final frame as visible.

### Logging, Tracebacks, Prompts, and Utilities

`RichHandler` is a standard logging handler. It renders log time, level, message, and path columns according to constructor flags. It highlights messages, can enable markup in log messages, and can render exceptions through Rich traceback formatting when `rich_tracebacks=True`.

`Console.print_exception()` renders the currently handled exception. `Traceback` is a renderable representation of a traceback, and `rich.traceback.install()` installs a global exception hook. Traceback options control width, code width, surrounding source lines, Pygments theme, word wrapping, local variable display, local truncation, dunder/sunder local hiding, indent guides, suppressed modules/paths, and maximum frames. Suppressed frames show only line and file information, without code context. If a traceback exceeds `max_frames`, Rich displays the beginning and end rather than every repeated frame; `max_frames=0` disables that truncation.

Prompts render Rich prompt text and parse responses. `Prompt.ask()`, `IntPrompt.ask()`, `FloatPrompt.ask()`, and `Confirm.ask()` accept `prompt`, `console`, `password`, `choices`, `case_sensitive`, `show_default`, `show_choices`, `default`, and `stream`. `Prompt` returns strings, `IntPrompt` returns integers, `FloatPrompt` returns floats, and `Confirm` returns booleans. When choices are supplied, the prompt loops until a valid response is received; `case_sensitive=False` permits case-insensitive matching. Pressing return with a default returns that default.

`decimal(size, precision=1, separator=" ")` formats byte sizes with SI powers of 1000. Singular and small byte counts render as byte strings; larger values use `kB`, `MB`, `GB`, `TB`, `PB`, `EB`, `ZB`, and `YB` with the configured precision and separator.

## Error Semantics

- `MarkupError` is raised when console markup cannot be matched or parsed, including mismatched explicit closing tags and an implicit `[/]` with no open tag. Markup metadata tags with invalid Python-literal parameters also raise `MarkupError`.
- `StyleSyntaxError` is raised for invalid style definitions, such as a missing color after `on`, an unknown style word in a style definition, a missing URL after `link`, or malformed color syntax.
- `MissingStyle` is raised when a style name cannot be resolved as a theme style and also cannot be parsed as a style definition.
- `NotRenderableError` is raised when a value supplied to rendering or table cells is not renderable by Rich.
- `NoAltScreen` is raised when screen-update APIs are used without an active alternate-screen context.
- `LiveError` represents invalid live-display operations exposed by console/live APIs.
- `Console.print_json()` raises `TypeError` when the positional `json` argument is supplied and is not a string; use `data=` for Python data. Invalid JSON strings and unsupported data serialization propagate the standard `json` module exceptions.
- `Progress.open()` raises `ValueError` for modes other than `"r"`, `"rt"`, and `"rb"`, and for unbuffered text I/O. Binary line buffering emits a runtime warning and uses the default buffer size.
- `Progress.wrap_file()` raises `ValueError` when no total byte count can be determined from arguments or an existing task.
- `Text.append()` raises `TypeError` for values that are neither `str` nor `Text`. Text slicing with a non-unit step raises `TypeError`. Text operations that require matching text segments raise standard `ValueError` for invalid ranges or incompatible inputs.
- `Style.pick_first()` raises `ValueError` if all supplied styles are `None`.
- Public APIs that read files, parse colors, parse JSON, or call Pygments propagate the standard file, JSON, and Pygments exceptions unless Rich documents a more specific exception above.

## Cross-View Invariants

1. The printable text obtained by concatenating non-control segment text from `Console.render()` is the same visible text that appears in `Console.print()` output after markup, emoji, pretty rendering, and render protocol conversion have been applied.
2. `Console.render_lines()` and `Segment.split_lines()` preserve segment styles across line boundaries; adding padding or cropping changes cell width but not the style of original printable content.
3. `Console.capture()` returns the same string projection that would have been written to the console's file for the same console settings.
4. A recorded console's `export_text(styles=False)` contains the same visible text as captured output, without ANSI style codes. With `styles=True`, the visible text remains the same after ANSI codes are stripped.
5. `save_text()`, `save_html()`, and `save_svg()` write the same content that the corresponding `export_*()` method returns for the same buffer, theme, and `clear` setting.
6. `clear=True` on any export or save consumes the current record buffer; a following export sees only later recorded writes. `clear=False` leaves the buffer available for subsequent exports.
7. Disabling markup for a console or print call makes bracketed markup text visible as literal text; escaping markup with `escape()` preserves literal brackets while leaving surrounding markup usable.
8. A `Text` built with `from_markup()` and a string printed with markup enabled produce equivalent styled segment content for the same markup, style base, emoji setting, and emoji variant.
9. A table cell, panel body, tree label, progress column renderable, or markdown/code block that contains another Rich renderable uses that renderable's public segment output rather than stringifying it unless the host API explicitly documents string conversion.
10. Terminal color downgrading affects ANSI/style representation but not the plain text content, segment cell widths, or wrapping decisions based on printable cells.
11. Live, status, and progress displays may use cursor-control segments in interactive terminals; when output is non-interactive, the durable plain-text projection avoids writing animation frames as ordinary transcript content unless interactivity is forced.
12. File, HTML, SVG, Jupyter, and terminal projections derive from the same renderable contract; differences in escape format, theme, and terminal capabilities must not change the semantic text, row/column ordering, task ordering, or traceback frame ordering.

## Representative Workflow(s)

### Rich Console Report

Create a console with deterministic width and recording enabled:

```python
from rich.console import Console
from rich.json import JSON
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console(width=60, record=True, color_system="standard")

title = Text("Build report", style="bold")
title.stylize("cyan", 0, 5)

table = Table(title=title, show_lines=True)
table.add_column("Step", style="cyan", no_wrap=True)
table.add_column("Result", overflow="fold")
table.add_row("parse", "[green]ok[/green]")
table.add_row("payload", JSON.from_data({"items": [1, 2, 3]}, sort_keys=True))

console.rule("[bold]Summary[/bold]")
console.print(table)
console.print(Syntax("print('done')", "python", line_numbers=True))

plain = console.export_text(clear=False)
html = console.export_html(clear=False)
svg = console.export_svg(title="Build report")
```

The rule renders a horizontal divider with styled title text. The table renders two columns, row separators, markup in string cells, and a nested JSON renderable without stringifying the JSON object. The syntax block renders highlighted Python code with a line-number column. The three exports share the same visible text and ordering; HTML and SVG preserve style information according to their themes. Because the first two exports use `clear=False`, they do not consume the record buffer; the final SVG export uses the default `clear=True` and clears it.

### Progress With Console Output

```python
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn

with Progress(
    TextColumn("{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    transient=True,
) as progress:
    task = progress.add_task("reading", total=3, source="local")
    for _ in range(3):
        progress.console.print("processed item")
        progress.advance(task)
```

The progress context starts and stops the live display. The task id returned by `add_task()` identifies the task for updates. The custom field `source` is stored on the task for columns that reference it. Messages printed through `progress.console` appear above the progress display. Because `transient=True`, the progress display is removed when the context exits, while the ordinary printed messages remain.

## Non-Goals

- Reproducing private helpers, private modules, private cache structures, private renderer classes, or any name whose only evidence is internal use.
- Matching undocumented object representation strings, memory addresses, private attributes, or incidental ordering from implementation data structures.
- Rebuilding terminal emulator behavior, operating-system pager behavior, readline editing, shell behavior, or Pygments internals beyond Rich's documented use of them.
- Pixel-perfect visual matching for every terminal font, glyph, or platform; the public contract is terminal-cell text, styles, control behavior, and documented projection semantics.
- Guaranteeing network access for examples, downloads, images, external CSS, sponsorship text, or remote content.
- Implementing Rich CLI as the separate `rich-cli` project; only module entry points provided by the `rich` package are in scope.
- Treating demo output timings, terminal screenshots, animation frame timing, or exact progress refresh cadence as stable beyond the documented default rates and context-manager side effects.

## Evaluation Notes

Evaluation focuses on public behavior from the perspective of Rich users. It checks importability of documented names, method signatures and defaults for the public API, render protocol behavior, segment streams, plain/ANSI output, console wrapping and width handling, markup parsing, style/theme/color parsing, Text mutation, table layout behavior, progress/live/status lifecycle behavior, JSON/Syntax/Markdown/Pretty rendering, recording/export/save behavior, logging/traceback/prompt surfaces, and documented error classes.

The same scenario may be observed through multiple views: direct console output, captured strings, segment lists, exported text, exported HTML/SVG, saved files, and public object methods. Implementations should keep those views consistent according to the invariants above.

The evaluation does not require private module layout, private helper names, hidden implementation algorithms, or exact terminal-specific pixels. It may use deterministic console width, forced terminal settings, non-interactive files, and fixed time callbacks to make observable behavior repeatable without depending on a particular local terminal.
