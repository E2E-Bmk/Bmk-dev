# SQL Parsing And Formatting

`sqlparse` is a non-validating SQL parser for Python. It provides public APIs
for splitting statements, parsing text, formatting SQL, tokenizing text, and
running the `sqlformat` command-line interface.

## Scope

The scoreable behavior is the public Python API and the documented command-line
workflow: statement splitting, parsing and round trips, stream parsing,
tokenization, public utility helpers, formatting options, public error types,
and CLI input/output, option handling, encoding, and file workflows.

Internal token-tree positions, private attributes, object repr addresses,
implementation caches, exact diagnostic wording, and machine-dependent timing
are not part of this contract.

## Installable Surface

The package exports `sqlparse.parse`, `sqlparse.parsestream`, `sqlparse.split`,
`sqlparse.format`, `sqlparse.cli`, `sqlparse.engine`, `sqlparse.filters`,
`sqlparse.formatter`, `sqlparse.sql`, `sqlparse.tokens`, `sqlparse.lexer`,
`sqlparse.utils`, and `sqlparse.exceptions.SQLParseError`.

```python
import sqlparse
from sqlparse import cli, lexer, tokens, utils
```

The documented CLI is available as `python -m sqlparse` and through
`sqlparse.cli.create_parser`.

## Public Behavior

`parse` returns one statement value per SQL statement and preserves the source
text when converted to text. `parsestream` accepts a text stream. `split`
handles semicolons outside quoted strings/comments and supports removing
trailing semicolons. `lexer.tokenize` yields token-type/value pairs whose values
reconstruct the input.

`format` supports documented keyword and identifier case, comment and
whitespace stripping, reindentation, operator spacing, and indentation options.
Invalid formatter options raise `SQLParseError`.

The CLI supports help/version, stdin and files, output files, in-place updates,
encoding selection, formatting options, and meaningful nonzero failure status
for invalid or incompatible invocations.

## Error Semantics

Invalid public formatter options use `SQLParseError`. CLI failures use a
nonzero process status. Error message wording is intentionally not required.
