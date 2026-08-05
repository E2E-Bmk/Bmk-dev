# Jedi Public Behavior Specification

## Product Overview

Jedi is a Python static-analysis library used by editors and interactive
tools. Its public API analyzes Python source text and small local project
trees, exposing completions, definitions, inferred values, references,
signatures, names, syntax positions, search results, and refactoring edits.

## Scope

This package covers the documented `jedi.Script`, `jedi.Interpreter`, and
`jedi.Project` entry points over a small local project containing `app.py`,
`lib.py`, and `calc.py`. It also covers the public `jedi.RefactoringError`
exception and the documented attributes and methods of the result objects
returned by those entry points.

The tested public methods are `Script.complete`, `infer`, `goto`, `search`,
`complete_search`, `get_references`, `get_signatures`, `get_context`,
`get_names`, `get_syntax_errors`, `rename`, `extract_variable`, and
`extract_function`. `Interpreter` supports the same analysis methods while
using supplied namespace dictionaries. `Project` supports `search`,
`complete_search`, `save`, and `load`, and exposes its documented `path`,
`sys_path`, `smart_sys_path`, and `load_unsafe_extensions` properties.

## Public Import Surface

The public imports used here are `Script`, `Interpreter`, `Project`, and
`RefactoringError` from `jedi`. Results are consumed through documented
public members rather than concrete implementation modules. Name results
expose `name`, `type`, `full_name`, `module_name`, `module_path`, `line`,
`column`, `description`, `docstring`, `get_definition_start_position`,
`get_definition_end_position`, `get_line_code`, `parent`, and
`defined_names`. Completion results expose `name`, `type`, `complete`,
`name_with_symbols`, `docstring`, and `get_completion_prefix_length`.
Signature results expose `name`, `type`, `index`, `bracket_start`, `params`,
and `to_string`; parameter results expose `name`, `kind`, `to_string`,
`infer_default`, and `infer_annotation`. Syntax-error results expose
`line`, `column`, `until_line`, and `until_column`.

Refactoring results expose `get_changed_files`, `get_renames`, `get_diff`,
and `apply`. Values returned by `get_changed_files` expose `get_new_code`,
`get_diff`, and `apply`.

## Product State Model

The local project has the following public source facts:

- `lib.Greeter` is a class with public `__init__` and `greet` members.
- `lib.make_greeter` is a function with a documented signature containing
  `name: str = "Ada"` and returning `Greeter`.
- `app.person` is inferred as an instance of `lib.Greeter`.
- `app.message` calls `person.greet("Hi")`, and `app.repeat` references
  `lib.make_greeter`.
- Searching `app.py` for `make_greeter` exposes the import-site result, and
  inference of `app.repeat` resolves to the `lib.make_greeter` function.
- `Greeter.greet` has the raw docstring `Return a greeting.` and
  `make_greeter` has the raw docstring `Build a greeter.`.
- `calc.py` contains `result = first + second`, which is the source range
  used for extraction refactorings.

Source positions use one-based lines and zero-based columns. Local module
names, result types, completion suffixes, signature text, and the source
positions asserted by the tests are part of this behavior.

## Error Semantics

Applying a refactoring produced from a source string without a file path
raises the public `RefactoringError` type. Syntax analysis reports structured
position objects through `get_syntax_errors`; the tests do not require a
particular human-readable diagnostic string. No exact exception text is
required.

## Cross-View Invariants

Script inference, goto, references, search, completion search, and project
search identify the same local names with consistent public names, types,
module paths, module names, positions, docstrings, and definition ranges.
File-scope references stay within the current file, while project-scope
references can include the local imported module. Script and Interpreter
completion results expose the same documented completion shape for equivalent
string values.
Script search and completion search identify the same imported factory name,
while alias inference agrees with project search for the library definition.

Saving and loading a `Project` preserves its path and explicit search-path
configuration. Refactoring projections agree across changed-file code, diff
text, renames, and applied local file contents. Rename changes both the
assignment and its use; extraction introduces the named statement or helper
and rewrites the selected expression.

## Representative Workflow

A client creates a `Project` for a temporary local tree, opens `app.py` with
`Script`, follows a factory to `lib.py`, inspects the inferred instance and
its public result attributes, searches the project for the same definition,
and completes a method name. The client then inspects a signature and its
parameter defaults and annotations, uses `Interpreter` with a supplied
namespace, persists and reloads the project, and applies rename or extraction
refactorings to a temporary file.

## Non-Goals

The package does not require private implementation modules or attributes,
internal inference objects, parser helpers, source test modules, third-party
stubs, external services, network access, environment discovery details,
machine-specific paths, timing guarantees, or exact human-readable diagnostic
strings. It does not require full completion snapshots, compiled extension
analysis, unsafe extension loading, notebook support, or the documented
`inline` refactoring path.

## Invocation Protocol

Install the requirements listed below, make the pinned Jedi source importable
as `jedi`, and run:

```bash
python -m pytest -q -W error --json-report --json-report-file=logs/result.json
```

The tests create all project files below a temporary directory. They do not
need a database, a service process, a shell command, or network access.

## Environment

The intended environment is Linux with Python 3.11 and without network access
during the test run. The target package is not pre-installed; the
implementation under test must provide the `jedi` package. Required packages
are `pytest`, `pytest-json-report`, and `parso`.

## Evaluation Notes

There are 30 atomic tests and 30 integration tests, for 60 physical tests.
Integration tests combine independent public views such as search with
inference, completion with project state, signatures with namespace
execution, persistence with import resolution, and refactoring code with
diffs and applied files. A deliberately weak import-compatible implementation
is expected to pass fewer than ten percent of the tests.
