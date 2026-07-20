# Hy Reader, Models, Compiler, and Import Runtime

## Overview

Hy is a Lisp dialect embedded in Python. Hy source is read into model objects,
compiled to Python AST, and executed with ordinary Python runtime facilities.
The package also installs an import hook so `.hy` modules compose with
`importlib`, `runpy`, bytecode caches, and normal module reloading.

## Installable Surface

The solution root provides an importable `hy` package. These imports are part
of the supported surface:

```python
import hy
from hy import PrematureEndOfInput
from hy.compiler import hy_compile
from hy.errors import HyError, HyLanguageError
from hy.importer import HyLoader
from hy.models import (
    Complex, Dict, Expression, FComponent, Float, FString, Integer,
    Keyword, List, Set, String, Symbol, Tuple, as_model, replace_hy_obj,
)
from hy.reader import read_many
from hy.reader.exceptions import LexException
```

`hy.read(source)` reads one form. `hy.eval(model, globals=None, locals=None)`
executes a model and returns its Python value. `read_many(source,
filename="<string>")` returns an
iterable of all forms in the source. `hy_compile(tree, module_name, ...)`
returns Python AST and accepts `import_stdlib`, `filename`, and `source`
keyword arguments.

## Reader Forms And Literal Conversion

Reader output uses the model classes above and compares structurally.

- `(foo bar)` becomes an `Expression` containing two `Symbol` values.
- `(foo "bar")` and `(foo 2)` contain a `String` and an `Integer`
  respectively.
- A bare `foo` is a `Symbol`; `"foo"` is a `String`.
- A backslash immediately before a physical newline joins string content, so
  `"a\` followed by a newline and `bc"` has the value `"abc"`.
- `#[delimiter[text]delimiter]` is a bracket string. The resulting `String`
  contains `text` and exposes the delimiter through `.brackets`. `#[[text]]`
  uses the empty delimiter.
- `[1 2 3 4]` produces `List([Integer(1), ..., Integer(4)])`.
- Dict syntax preserves its flat alternating sequence, including duplicate
  keys. Nested expressions can be keys or values.

Reader sugar is expanded into expressions. Quote, quasiquote, unquote, and
unquote-splice use heads `quote`, `quasiquote`, `unquote`, and
`unquote-splice`; surrounding whitespace does not change the expansion.

## Reader Numeric Syntax

Numeric models preserve the corresponding Python numeric value.

- Decimal, hexadecimal, octal, and binary integers are accepted. Examples:
  `42`, `0x80`, `0o1232`, and `0b1011101` become 42, 128, 666, and 93.
- Leading zeroes do not imply octal: `010` is decimal 10.
- Floats accept forms such as `2.`, `-0.5`, and `1.e7`.
- Complex suffixes accept `j` or `J`, including signed real and imaginary
  components. Bare `j` and `J` remain symbols.
- Capitalized `NaN`, `Inf`, and `-Inf` are numeric. Other case variants such
  as `nan`, `INF`, and `-inf` remain symbols unless they occur in one of the
  explicitly accepted complex forms.
- Underscores and commas are ignored as digit separators inside accepted
  numeric forms, including around base prefixes and in float or complex
  forms. A leading underscore keeps the token a symbol.
- Overflowing float syntax follows Python and yields infinity rather than a
  reader failure.

## Reader Sugar And Dotted Identifiers

`foo.bar` is equivalent to `(. foo bar)`. Additional components extend that
expression. A leading dot inserts `None`, so `.foo` is `(. None foo)` and
`..foo` is `(.. None foo)`.

Every component of a dotted identifier must be symbolic. Numeric values and
keywords followed by `.name` raise `LexException`; `j.foo` is valid because
bare `j` is a symbol.

## Reader Errors And Source Positions

Incomplete forms raise `PrematureEndOfInput`, which is also a `LexException`.
This includes unclosed expressions, dicts, function forms, and strings. A lone
quote followed by whitespace has exact type `PrematureEndOfInput` and its
`.msg` is `Premature end of input while attempting to parse one form`.
Extra or mismatched closing delimiters raise `LexException`.

Malformed `\x` escapes raise `LexException` with the underlying
`unicodeescape` truncation description. A non-symbol dotted component reports
`The parts of a dotted identifier must be symbols`.

Models expose one-based `start_line`, `start_column`, `end_line`, and
`end_column` positions. End columns are inclusive. For `(foo (one two))`, the
outer expression spans columns 1 through 15, `foo` spans 2 through 4, and the
inner expression spans 6 through 14. Physical newlines update subsequent line
and column values, including newlines inside strings.

## Model Construction And Collection Behavior

- `Symbol` accepts nonempty symbolic names, including hyphens, underscores,
  and Unicode. It rejects empty names, names beginning with `:`, numeric names,
  `#` forms, whitespace, and call-like text. `Keyword` exposes `.name`; it is
  more permissive for empty, colon-prefixed, numeric, and `#` names, but still
  rejects whitespace and call-like text.
- `as_model(0)` returns exact type `Integer`. Python tuples become `Tuple`, and
  native values nested in an existing `Expression` are recursively wrapped.
- `replace_hy_obj(value, template)` wraps `value` while carrying source
  metadata from `template`; integers, strings, and tuples become their matching
  Hy model types.
- Invalid bracket delimiters in `String` and `FString` content raise
  `ValueError`, including delimiter text split around an `FComponent`.
- Adding two `List` objects returns a `List`; slicing a `List` also returns a
  `List`, including empty out-of-range slices.
- `Dict.items()`, `.keys()`, and `.values()` preserve flat insertion order and
  duplicate keys.
- `Set` preserves its model sequence, including duplicate elements, when
  iterated.

## Compilation Forms And Errors

`hy_compile` accepts reader output and produces Python `ast.Module` output.
A simple function definition compiles to an `ast.FunctionDef`. Passing an
unrelated Python object instead of reader output raises `TypeError`.

The following form rules apply:

- An empty expression cannot be called, while a quoted empty expression is
  valid.
- Dotted calls may unpack `#*` and `#**` only where an object/call shape is
  valid.
- `if` requires two or three operands after the head. Empty `while` is invalid.
- Empty and nonempty `do` forms compile.
- `raise`, `raise Exception`, `raise e`, and `raise Exception :from NameError`
  compile; two positional exception operands do not.
- `try` supports ordered `except`/`except*`, optional `else`, and optional
  final `finally` clauses. `else` must follow all handlers and precede
  `finally`; normal `except` and `except*` handlers cannot be mixed.
- Exception handler bind/type lists accept empty, one-name, nested type-list,
  and name-plus-type-list shapes. Malformed scalar or overlong shapes fail.
- `assert` accepts a condition and an optional message expression of any
  Python-compatible value.

Forms rejected by the compiler raise a subclass of both `HyError` and
`HyLanguageError` and provide a nonempty `.msg`. `except*` forms are supported
when the running Python version supports exception groups.

## Runtime Execution And Python Interoperation

`hy.eval(hy.read(source))` returns ordinary Python values. Lists, dicts,
tuples, sets, method calls, conditionals, comprehensions, arithmetic, and
Python builtins compose normally. A list comprehension with an `:if` clause
filters before applying its result expression.

## Import Hooks And Module Execution

Importing `hy` activates `.hy` source loading for `importlib` and `runpy`.

- A package may use `__init__.hy` and `__main__.hy`; normal package imports and
  `runpy.run_module` execute them.
- `runpy.run_path` executes a `.hy` file and returns its globals.
- `HyLoader(fullname, path)` participates in the standard loader protocol.
  Runtime errors raised by a loaded module propagate to the caller.
- Invalid Hy import forms raise `HyLanguageError`. A failed first import is
  removed from `sys.modules`.
- Importing a `.hy` file creates normal Python bytecode when bytecode writing
  is enabled, and that cache can subsequently be loaded.
- `importlib.reload` re-executes Hy source. If re-execution fails, the module
  remains in `sys.modules` with assignments completed before the failure and
  prior values for assignments not reached.
- Circular imports behave like Python imports and expose the partially
  initialized module.
- When matching `.hy` and `.py` files share a module basename, the Hy import
  hook selects `.hy` for both package initializers and child modules.

## Non-Goals

Release tooling, documentation builders, editor integration, REPL cosmetics,
private caches, and macros outside the forms described here are not part of
this compatibility surface.
