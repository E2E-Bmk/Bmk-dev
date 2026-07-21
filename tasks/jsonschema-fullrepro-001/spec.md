# JSON Schema Validation And Command-Line Compatibility

## Overview

The `jsonschema` package validates Python values against JSON Schema drafts,
supports custom validator classes and format checkers, selects useful errors
from nested failures, and provides the legacy `jsonschema` command workflow.
This document describes the supported compatibility surface, including
deprecated APIs that remain callable with warnings.

## Installable Surface

The solution root provides an importable `jsonschema` package. These imports
are supported:

```python
from jsonschema import (
    Draft202012Validator, FormatChecker, RefResolutionError, RefResolver,
    TypeChecker, cli, exceptions, validators,
)
from jsonschema.exceptions import (
    ErrorTree, FormatError, SchemaError, ValidationError, best_match,
)
from jsonschema.validators import (
    Draft3Validator, Draft4Validator, Draft6Validator, Draft7Validator,
    create, extend, validate, validator_for,
)
```

Validator instances expose `schema`, `iter_errors`, `validate`, `is_valid`,
`is_type`, and `evolve`. Validator classes expose `META_SCHEMA`, `VALIDATORS`,
`TYPE_CHECKER`, `ID_OF`, `FORMAT_CHECKER`, and `check_schema`.

## Format Checking And Registration

`FormatChecker(formats=None)` copies the class-wide checker registry. Passing
`formats=()` creates an empty registry; naming an unknown format raises
`KeyError`.

`checker.checks(name, raises=())` is an instance decorator. The decorated
callable is stored only on that checker. `FormatChecker.cls_checks(...)`
registers class-wide and emits `DeprecationWarning`. A checker callable returns
a truthy value for success. A false result or an exception listed by `raises`
causes `FormatError`; the original exception is available as both `.cause` and
`.__cause__`. Exceptions not listed by `raises` propagate unchanged.

Built-in checkers include IPv4, so `not-an-ipv4` fails the `ipv4` format. A
validator given a format checker converts `FormatError` into
`ValidationError` while preserving the original cause.

The compact representation lists checker names in sorted order:

```text
<FormatChecker checkers=['bar', 'baz', 'foo']>
```

## Validator Construction And Extension

`validators.create(meta_schema, validators=(), version=None,
type_checker=None, id_of=None, applicable_validators=None)` returns a new
validator class.

- The class constants preserve the supplied keyword mapping, meta-schema, and
  `TypeChecker`. An instance preserves the schema in `.schema`.
- A custom keyword callable receives `(validator, keyword_value, instance,
  schema)` and yields `ValidationError` objects. `iter_errors` returns no
  values on success and preserves each yielded error's message, instance,
  schema, validator name/value, and schema path.
- A version such as `my version` produces class name and qualified name
  `MyVersionValidator`; dashes are removed in title-cased names.
- A versioned class is discoverable through `validator_for` using its
  meta-schema identifier. `$id` is used by default. A custom `id_of` can make
  legacy `id` identifiers discoverable. Without a version, no new identifier
  registration occurs.
- With no custom type checker, array, boolean, integer, null, number, object,
  and string recognize `[]`, `True`, `12`, `None`, `12.0`, `{}`, and `"foo"`.
- A meta-schema declaring its own `$schema` is checked with that dialect. A
  custom meta-schema without `$schema` is checked by the newly created class.

Versioned validator representations are stable:

```text
MyVersionValidator(schema={}, format_checker=None)
MyVersionValidator(schema={'a': [0, 1, 2, 3, 4, 5, ...]}, format_checker=None)
Validator(schema={}, format_checker=None)
```

The long form truncates long containers after six displayed values.

`validators.extend(base, validators=None, version=None, type_checker=None,
format_checker=None)` preserves the base meta-schema, type checker, schema-ID
function, and applicable-keyword behavior while merging keyword callables.
In particular, extending `Draft4Validator` keeps Draft 4's `$ref` sibling
rules.

## Validation Error Messages

Schema failures expose a human-readable `.message`. The following wording is
part of this compatibility surface:

- Draft 3 and Draft 7 dependencies use
  `'foo' is a dependency of 'bar'`; `dependentRequired` follows the same form.
- Disallowed additional array items end with `(2 was unexpected)` or
  `(1, 2, 3 were unexpected)`.
- Disallowed object properties identify each quoted property and use
  `was unexpected` or `were unexpected` as appropriate.
- A `const` mismatch includes `12 was expected`.
- Draft 6 `contains` with no match reports
  `None of [2, {}, []] are valid under the given schema`.
- `additionalProperties: false` combined with `patternProperties` names the
  unmatched properties and the configured regular expressions in sorted,
  quoted form.
- Boolean schema `False` reports `False schema does not allow 'something'`.
- `minContains` reports
  `Too few items match the given schema (expected at least N but only M matched)`.
- `maxContains` reports
  `Too many items match the given schema (expected at most N)`.

`check_schema` raises `SchemaError` for invalid schemas. `validate` raises the
most relevant `ValidationError` for an invalid instance.

## Best-Match Error Selection

`exceptions.best_match(errors)` returns `None` for an empty iterable and is
independent of input order for equivalent failures.

Selection favors shallow direct constraints over weak `anyOf`/`oneOf`
failures. When a union contains a uniquely relevant nested branch, selection
descends to its specific failure. It does not descend when all union branches
are equally relevant. A single branch and sibling item failures are descended.
For `allOf`, selection descends to the most relevant required branch.

Type-compatible branches outrank branches whose `type` does not match. This
also applies to union type declarations. Nested union contexts are traversed
recursively. A failure under boolean schema `False` has `validator is None`.

## Legacy Compatibility Warnings

The following behavior remains available but emits `DeprecationWarning` with
the warning attributed to the caller:

- assigning a child with `ErrorTree.__setitem__`;
- `RefResolver.in_scope(...)`;
- passing a second schema argument to `Validator.is_valid` or
  `Validator.iter_errors`;
- importing `RefResolver` from either `jsonschema` or
  `jsonschema.validators`;
- importing `RefResolutionError` from either `jsonschema` or
  `jsonschema.exceptions`;
- calling `FormatChecker.cls_checks`.

The two `RefResolutionError` import paths return the same exception class.
The old two-argument `is_valid` returns a boolean, while `iter_errors` returns
the expected validation failures for the supplied alternate schema.

## Command-Line Validation Workflow

`jsonschema.cli.parse_args(argv)` returns a mapping consumed by
`jsonschema.cli.run(arguments, stdin, stdout, stderr)`. `run` returns `0` on
success and `1` for handled input, schema, or validation failures. It reads a
schema path, repeated `-i/--instance` paths, or standard input when no instance
path is supplied.

Plain output writes failures to stderr as `{instance}: {message}\n`. Multiple
errors and multiple instances retain input order. `--error-format TEMPLATE`
formats each error with fields such as `{error.message}` and
`{error.instance}` and concatenates the results exactly.

`--output pretty` uses blocks of this form:

```text
===[ValidationError]===(instance-name)===

message
-----------------------------
```

Schema and missing-file failures use `SchemaError` and `FileNotFoundError` in
the heading. Pretty JSON-decoding failures include a traceback and identify
only the input that failed. Plain decoding failures begin with
`Failed to parse 'path':` or `Failed to parse <stdin>:` and include Python's
`JSONDecodeError` description. A bad instance does not prevent later instance
paths from being processed. An invalid schema is reported before instance
validation.

Missing instance paths report `'path' does not exist.`. An invalid explicit
base URI may propagate `RefResolutionError`; resolving `foo.json` against
`not@UR1` reports `unknown url type: 'foo.json'`.

Without `$schema`, CLI validation uses `Draft202012Validator`. Draft 7 applies
`const`; Draft 4 ignores `const`. Thus a value different from `"check"` fails
under Draft 7 and the default dialect but succeeds under Draft 4.

## Non-Goals

Remote schema retrieval, optional third-party format packages, generated
documentation, performance suites, and registry storage details are outside
this compatibility surface.
