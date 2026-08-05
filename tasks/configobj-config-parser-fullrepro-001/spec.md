# ConfigObj Public Configuration Specification

## Product Overview

ConfigObj is a local configuration parser and writer for INI-like files. It
represents scalar values, list values, and arbitrarily nested sections while
retaining member order and comments. The public workflow is deterministic:
parse controlled in-memory or local-file inputs, inspect semantic values, apply
documented section operations, validate against a configspec, and write a
round-trip representation.

## Scope

This package covers:

- `configobj.ConfigObj` construction from lines, mappings, file-like objects,
  `pathlib.Path` objects, and local filenames.
- Ordered scalar members, list values, nested sections, comments, inline
  comments, initial/final comments, and plain-dictionary projections.
- ConfigParser-style and Template-style interpolation, disabled interpolation,
  and interpolation in list members where supported by the pinned revision.
- `unrepr`, `list_values`, `stringify`, `write_empty_values`, indentation,
  newline tracking, UTF-8 encoding, and UTF-8 BOM handling.
- `write`, `reload`, `reset`, `merge`, `rename`, `walk`, conversion helpers,
  and documented public parsing errors.
- `configobj.validate.Validator`, built-in conversion checks, custom checks,
  defaults, `ConfigObj.validate`, copy mode, preserved errors,
  `SimpleVal`, `flatten_errors`, and `get_extra_values`.
- Deterministic in-memory and temporary-local-file semantic round trips.

The pinned revision's binary line-oriented file loader does not provide a
stable UTF-16 path round trip across its `readlines` behavior, so UTF-16 path
decoding is excluded. UTF-8 files, explicit UTF-8 output, and UTF-8 BOM
detection are the supported encoding contracts here.

## Installable Surface

The primary import is `configobj`. Public names include `ConfigObj`, `Section`,
the documented configuration exception classes, `SimpleVal`,
`flatten_errors`, and `get_extra_values`. Validation is available from
`configobj.validate` and the compatibility import `validate`; this package
uses the public `Validator` class and its public check functions.

## Product State Model

A `ConfigObj` is an ordered section mapping. Scalar names and subsection names
are tracked separately but expose a single ordered public key sequence. A
section contains values or further sections, has a parent/depth relationship,
and exposes comment, inline-comment, configspec, default, and extra-value
state. Fetching values may apply interpolation without changing the stored
semantic structure. `dict()` returns a detached plain mapping.

Validation consumes a configspec and may replace string values with converted
Python values. Missing values with defaults are tracked in `defaults`; copy
mode materializes values without marking them as defaults. Writing omits
ordinary defaulted values unless they have been explicitly materialized.

## Error Semantics

Malformed configuration lines raise documented `ConfigObjError` subclasses,
including `ParseError`, `NestingError`, and interpolation errors. A missing
local file with `file_error=True` raises an I/O error, and reload without a
usable filename raises `ReloadError`. Validator failures raise public
`validate` exception classes. Assertions check exception classes and resulting
state, not incidental diagnostic wording.

## Cross-View Invariants

- Parsing, `dict()`, ordered keys, and a write/reparse cycle describe the same
  scalar, list, and nested-section semantics.
- Comments and inline comments remain attached to the corresponding members
  through a local write/reparse workflow.
- Enabled, disabled, and Template interpolation expose the documented value
  projection while preserving the stored reference when writing.
- `unrepr` write/reparse preserves supported basic Python types.
- UTF-8 and UTF-8 BOM inputs decode to equivalent values, and explicit UTF-8
  output can be read back with the same semantic values.
- Validator conversion, defaults, error flattening, extra-value discovery, and
  default restoration agree across nested sections.
- Section mutations through merge, rename, walk, reset, and reload preserve
  their documented ordering and state transitions.

## Representative Workflow

```python
from configobj import ConfigObj
from configobj.validate import Validator

values = ConfigObj(
    ["port = 8080", "[database]", "host = localhost"],
    configspec=[
        "port = integer(1, 65535)",
        "[database]",
        "host = string",
    ],
)
assert values.validate(Validator()) is True
values.filename = "settings.ini"
values.write()
reloaded = ConfigObj(values.filename)
```

The package uses equivalent workflows with in-memory line lists and temporary
local paths, and compares semantic structures rather than incidental
whitespace.

## Non-Goals

This package does not cover private implementation modules, source tests,
network access, sockets, remote services, sleeps, timing, ambient host state,
platform-specific paths, exact whole-output snapshots, or undocumented
exception text. UTF-16 path loading is recorded as a pinned-revision
limitation, not asserted as a portable behavior.

## Invocation Protocol

Run from the package directory with the pinned source checkout supplied on
`PYTHONPATH`:

```text
PYTHONPATH=<fixed-source-checkout> PYTHONDONTWRITEBYTECODE=1 LC_ALL=C LANG=C TZ=UTC
python -m pytest <public-test-directory> -q -W error -p no:cacheprovider --json-report
```

The two public test files run in one local process. Temporary files are
created through pytest's temporary-path fixture and are outside the package
after the run.

## Environment

The intended environment is Python 3.11 on Linux without network access. The
target package is not pre-installed; the fixed source checkout is supplied as
the import surface. Required support packages are `pytest` and
`pytest-json-report`. A separate Python 3.10 replay uses the same deterministic
requirements. Locale and timezone variables are fixed to C and UTC.

## Evaluation Notes

The atomic cases establish public parsing, writing, section, option, encoding,
and validation contracts. Integration cases compose multiple operations and
compare independent semantic projections. The UTF-16 path-loader limitation is
explicitly excluded because it cannot meet a stable local contract in this
source revision. Local replay evidence is reproducibility evidence only and
does not establish a trusted black-box runner, external signature, or final
qualification status.
