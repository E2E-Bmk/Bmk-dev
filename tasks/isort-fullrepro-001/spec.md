# isort Public Contract

## Product Overview
isort is a Python import sorter and formatter. Given Python or Cython source text, it classifies imports into ordered sections, sorts modules and imported names, applies configured formatting, and returns or writes the resulting source.

The fixed implementation supports Python 3.10 and Python 3.11. The covered behavior is deterministic for the same source text, configuration, file names, and command arguments.

## Scope
This contract covers:

- The documented top-level Python API for sorting, checking, file and stream handling, import discovery, configuration, and module placement.
- The `isort` command-line entry point for sorting files, checking files, showing diffs, reading standard input, writing standard output, and applying the documented options used below.
- Configuration from `.isort.cfg`, `pyproject.toml`, `setup.cfg`, `tox.ini`, `.editorconfig`, and an explicitly selected settings file.
- Profiles, custom sections, section headings, action comments, import addition and removal, skip rules, source paths, and selected wrapping modes.

For the basic input `import z\nimport os\n`, the default formatted result is `import os\n\nimport z\n`. A clean result remains unchanged when checked.

## Installable Surface
The public Python names used here are:

- `isort.Config`
- `isort.ImportKey`, including the public selector `ImportKey.MODULE`
- `isort.code` and `isort.check_code`
- `isort.stream` and `isort.check_stream`
- `isort.file` and `isort.check_file`
- `isort.find_imports_in_code`, `isort.find_imports_in_stream`, `isort.find_imports_in_file`, and `isort.find_imports_in_paths`
- `isort.place_module` and `isort.place_module_with_reason`

`isort.code` returns formatted text. `isort.check_code` returns `True` only when no formatting change is needed. `isort.stream` writes formatted text to its output stream and returns whether the input changed. `isort.check_stream` returns the corresponding boolean. `isort.file` formats a file in place and returns whether it changed; passing an output stream returns the formatted text without replacing the file. `isort.check_file` returns the file check boolean.

The import discovery functions return iterators over the imports found in code, streams, files, or recursively supplied paths. `unique=True` and the public `ImportKey` values select de-duplication keys, and `top_only=True` limits discovery to imports before the first function or class.

`isort.place_module` returns a section name such as `STDLIB`, `THIRDPARTY`, `FIRSTPARTY`, or `LOCALFOLDER`. `isort.place_module_with_reason` returns that section together with a non-empty explanation.

The command-line entry point is `isort`; the same package entry point is invoked in the local checks as `python -m isort`. A leading `-` selects standard input.

## Product State Model
Formatting preserves non-import source text while changing import groups according to configuration. The default section order is `FUTURE`, `STDLIB`, `THIRDPARTY`, `FIRSTPARTY`, `LOCALFOLDER`, with blank lines between distinct sections. Relative imports are placed in `LOCALFOLDER`.

The `Config` class accepts documented options including `profile`, `line_length`, `multi_line_output`, `include_trailing_comma`, `use_parentheses`, `known_first_party`, `known_third_party`, `known_django`, `sections`, `add_imports`, `remove_imports`, `force_to_top`, `no_sections`, `from_first`, `force_single_line`, `length_sort`, `import_heading_stdlib`, `no_inline_sort`, `skip`, `skip_glob`, `append_only`, `force_adds`, and `src_paths`.

The built-in `black` profile has line length `88`, vertical hanging output, trailing commas, and parentheses. With line length `30`, the long import used by this contract is formatted as:

```python
from package import (
    alpha,
    beta,
    delta,
    gamma,
    zeta,
)
```

Custom section names are declared with matching `known_<section>` values and an explicit `sections` order. A configured `known_django=["django"]` with `DJANGO` in that order places `django` imports in `DJANGO`.

## Error Semantics
API checks report state with booleans: unsorted input is `False`, and already formatted input is `True`. Sorting operations report whether a change occurred. `--check` exits with `0` for clean input and `1` when formatting would change a file or stream; it does not rewrite a checked file.

`--diff` reports a unified diff for a required change and does not rewrite the input file. A file containing `# isort: skip_file` is accepted by a check without being rewritten.

## Cross-View Invariants
The following views describe the same formatting state:

- Formatting with `isort.code` and then checking with `isort.check_code` yields `True`.
- Formatting through `isort.stream` or `isort.file` produces text that the corresponding check operation accepts.
- File sorting changes the file once; a second sort reports no change.
- API and command-line formatting agree for the same source and options.
- A diff contains unified-diff markers and changed import lines while leaving the source file unchanged.
- `--stdout` returns formatted content and leaves the file unchanged.
- `place_module` and formatted section placement agree for configured known modules.

## Representative Workflow
Create a temporary source file containing unsorted imports. It can be formatted through the Python API or with `isort path`. The resulting file can be checked with `isort.check_file` or `isort path --check`. A dirty check returns `1`, while a clean check returns `0`.

For stream workflows, send source text to `isort - --stdout` and compare the returned text with `isort.code`. Send the same text to `isort - --check` to inspect its clean or dirty status.

Configuration may be discovered from the nearest supported configuration file. An explicit `--settings-path` selects a named settings file. A nearer nested configuration takes precedence over a parent configuration.

Action comments control a file locally: `# isort: skip` protects one import, `# isort: off` through `# isort: on` preserves a disabled block, and `# isort: split` starts a new import group. `# isort: dont-add-imports` prevents configured additions for that file.

`--add-import` adds an import, `--remove-import` removes one, `--append-only` declines to add to a file with no existing imports, and `--force-adds` permits an addition to such a file. `--skip` and `--skip-glob` skip matching files when used with `--filter-files`.

## Non-Goals
This contract does not cover network or service access, cloned projects, randomized or property-based behavior, performance timing, interactive prompts, image rendering, private implementation modules, the private version carrier, or broad exact-output assertions for `--show-config`.

It does not require behavior for undocumented options, unsupported file types, platform-specific path conventions, locale-dependent output, or exact diagnostic paths and timestamps.

## Invocation Protocol
The checks are collected from `test_atomic.py` and `test_integration.py` with pytest. Every check is a top-level physical test function. Temporary files and streams are created inside the test run; no repository tests or source files are imported as test helpers.

The command-line cases use `python -m isort` with the leading `-` convention for standard input. Assertions use stable formatted source, boolean results, exit codes, and unified-diff markers. Temporary absolute paths and diff timestamps are not part of the contract.

## Environment
Run on Linux with Python 3.11 and without network access. `pytest` and `pytest-json-report` are required and are installed for the local replay. The target package is not pre-installed; the checks resolve the package from the fixed source checkout. The package has no runtime network or service dependency.

## Evaluation Notes
There are 32 atomic checks and 34 integration checks, for 66 physical checks. The atomic layer isolates public API and configuration behaviors. The integration layer combines API views, file state, command-line projections, configuration discovery, and workflow transitions.

This is artifact-only packaging. Local replay logs record reproducibility results for the fixed source and a deliberately weak local substitute; they do not establish protected execution, service isolation proof, external attestation, container execution, acceptance, or a delivered status.
