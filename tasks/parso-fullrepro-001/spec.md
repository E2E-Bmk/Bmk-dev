# Parso Compatibility Specification

## Product Overview

Provide an importable `parso` package that parses Python source into a concrete
syntax tree. The tree must preserve every source character, including spacing,
comments, line endings, incomplete constructs, and invalid tokens, so editors
can inspect and reproduce code even while it is being changed.

The implementation must run from the solution directory without relying on
another installed copy of Parso.

## Installable Surface

The following imports must succeed:

```python
import parso
from parso import Grammar, ParserSyntaxError, load_grammar, parse
from parso.file_io import FileIO, KnownContentFileIO
from parso.utils import PythonVersionInfo, python_bytes_to_unicode, split_lines
```

`parso.__version__` is a string. `parso.grammar`, `parso.file_io`,
`parso.tree`, and `parso.utils` are importable modules.

## Parsing Entry Points

`parse(code=None, version=None, **options)` loads a Python grammar and delegates
to its `parse` method. `code` may be `str` or encoded `bytes`. Calling without
code, a path, or a file object raises `TypeError`.

`load_grammar(version=None)` returns a reusable Python `Grammar`. Version
strings such as `3.6`, `3.7`, and `3.8` select compatible syntax. A bare major
version selects that family's default compatible grammar. Versions older than
the supported Python family raise `NotImplementedError`; malformed strings or
non-string version values raise `ValueError` or `TypeError` respectively.

By default, parsing uses error recovery and returns a module for valid,
incomplete, or invalid source. With `error_recovery=False`, invalid syntax
raises `ParserSyntaxError`.

## Concrete Tree Model

The returned module and all descendants provide the public node/leaf behavior
used by concrete-syntax-tree consumers:

- `type` identifies syntax categories such as `file_input`, `funcdef`,
  `if_stmt`, `name`, `operator`, `error_node`, and `error_leaf`;
- `children` preserves grammatical order for non-leaf nodes;
- leaves expose `value` and `prefix`;
- `parent` links each descendant to its containing node while the module's
  parent is `None`;
- `start_pos` and `end_pos` use one-based lines and zero-based columns;
- `get_first_leaf`, `get_last_leaf`, `get_next_leaf`, and `get_previous_leaf`
  navigate source order;
- `get_code(include_prefix=True)` reconstructs the exact represented source.

`module.get_code()` must equal the original input for valid code, malformed
code, comments, blank lines, carriage returns, trailing whitespace, unfinished
strings, and unfinished f-strings. A final newline changes the module end
position to the beginning of the following line, while source without one ends
at the last source column.

## Error Recovery And Diagnostics

Recovery represents unparseable regions with `error_node` and `error_leaf`
objects while preserving surrounding valid statements. Invalid standalone
characters retain their original value. Mis-indentation may produce an
`error_leaf` whose token type identifies an indentation problem.

`Grammar.iter_errors(module)` yields public issue objects for syntax problems;
each issue has at least `message`, `start_pos`, and `code` information. Valid
modules yield no issues.

Python f-strings are preserved as `fstring` nodes when valid. Unmatched braces,
empty expressions, and malformed conversion or format sections raise
`ParserSyntaxError` when recovery is disabled and remain round-trippable when
recovery is enabled.

Passing undecodable bytes raises `UnicodeDecodeError`. Source encoding cookies
and UTF-8 byte-order marks are honored by `python_bytes_to_unicode` and by
parsing byte input.

## Tree Dumping

Every node and leaf supports `dump(indent=4)`. The result is a constructor-like
representation containing public node class names, leaf values, positions,
prefixes where non-empty, and children in source order.

- `indent=None` produces a compact single-line representation.
- An integer uses that many spaces per nesting level.
- A string uses that string per nesting level.
- A non-integer, non-string indentation value raises `TypeError`.

Dumping an intermediate node or leaf represents only that object. Rebuilding a
tree from an equivalent dump must restore parent links and exact code.

## Files, Lines, And Incremental Parsing

`FileIO(path)` stores the path, returns file bytes from `read()`, reports the
file modification timestamp, and returns `None` when the path does not exist.
`KnownContentFileIO(path, content)` has the same path behavior but returns the
provided content without reading the filesystem.

`split_lines(text, keepends=False)` splits only Python line endings (`\n`,
`\r`, and `\r\n`), preserves form feeds and other Unicode line separators as
ordinary content, and returns `[""]` for empty input. With `keepends=True`,
line terminators remain attached and a terminal empty line is represented.

`Grammar.parse` and top-level `parse` accept `path`, `file_io`, `cache`,
`diff_cache`, and `cache_path`. Re-parsing changed text with the same path and
`diff_cache=True` updates and returns the cached module object. The resulting
tree must be observationally equivalent to a fresh parse: exact code, node
types, positions, navigation, and diagnostics all reflect the new text.

## Behavioral Invariants

- Parsing and then calling `get_code()` is lossless.
- Tree positions and leaf navigation agree with source order.
- Recovery never drops text before, inside, or after an error.
- Incremental and fresh parsing of the same text expose equivalent trees.
- Grammar selection affects syntax recognition but not source preservation.
- Public failures use the documented exception classes.

## Non-Goals

Jedi integration, private tokenizer and diff algorithms, cache-file naming,
pickle formats, repository tooling, and performance equivalence are outside
this compatibility surface.
