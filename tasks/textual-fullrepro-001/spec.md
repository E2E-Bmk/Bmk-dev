# Textual Public Behavior Specification

## Product Overview

Textual is a Python framework for terminal user interfaces. An application is
an `App` with a public widget tree, message dispatch, key and pointer
interaction, Textual CSS styling, and deterministic headless testing through
`App.run_test` and `Pilot`.

## Scope

The supported surface in this package is the public application workflow around
`App.run_test`, `Pilot.press`, `Pilot.click`, `DataTable`, `Tree`, `Input`,
`Tabs`, public messages and events, and deterministic CSS layout and style
projections. The checks use small applications that compose these widgets,
drive keyboard and pointer interactions, and inspect public widget state and
messages.

## Public Import Surface

Applications may import public names from `textual`, `textual.app`,
`textual.containers`, `textual.coordinate`, `textual.events`,
`textual.geometry`, `textual.message`, and `textual.widgets`. The exercised
imports include `on`, `App`, `ComposeResult`, `Vertical`, `Coordinate`, `Key`,
`Offset`, `Message`, `Button`, `DataTable`, `Input`, `Tab`, `Tabs`, and `Tree`.

## Product State Model

An app composes widgets into a DOM-like hierarchy. `Input` stores editable text,
cursor position, selection state, value restriction, maximum length, and submit
or blur messages. `DataTable` stores ordered columns, ordered rows, public row
and column keys, cell values, cursor mode, coordinates, and selection messages.
`Tree` stores a root node, ordered child nodes, parent links, cursor node,
expansion state, and selection messages. `Tabs` stores tab count, active tab,
visibility, enabled state, labels, and activation messages.

CSS rules project into public style values and widget regions after layout.
Headless interaction through `Pilot` must update the same app and widget state
that programmatic public APIs expose.

## Error Semantics

The selected behavior avoids exact exception text. Invalid user input that is
blocked by `Input` restrictions or maximum length leaves the public value
unchanged except for accepted edits. Public methods for clearing, resetting,
adding, removing, sorting, updating, hiding, showing, disabling, and enabling
widgets must leave the exposed state internally consistent after each operation.

## Cross-Component Invariants

Keyboard input, pointer clicks, widget methods, public messages, and CSS layout
must agree on the same application state. Data table row identity must remain
available after coordinate lookup, selection, sorting, row removal, and column
removal. Tree node labels, parent links, and cursor state must agree after
navigation, expansion, collapse, clear, reset, and repopulation. Tab activation,
visibility, enabled state, removal, clear, and keyboard navigation must share a
single active-tab model. Layout regions must remain stable after non-layout
interactions in a fixed-size headless run.

## Representative Workflow

A representative client builds a dashboard containing tabs, an input, a data
table, and a tree. The client starts the app with `run_test`, types and submits
input text, moves focus with clicks, selects table cells, navigates tree nodes,
changes tabs, mutates table and tree contents from a submitted value, and then
checks public widget values, messages, and CSS-derived regions.

## Non-Goals

This package does not require private driver modules, private helper modules,
imports from source test suites, terminal snapshot image comparison, bulk SVG
matching, exact full-frame render text, wall-clock animation behavior, sleeps,
network behavior, host resource access, or external services. It does not
require compatibility with undocumented internals.

## Invocation Protocol

Install the requirements file that accompanies the public behavior checks and
make a Textual implementation importable as `textual`. Run the checks with:

```bash
python -m pytest <test-directory> -q -W error
```

The checks use headless app runs and temporary in-process state only. They do
not require a database, Docker, live terminal capture, or an external service.

## Environment

The intended evaluation environment is Linux with Python 3.11 and without network access
during the test run. The target package is not pre-installed; the implementation
under evaluation must provide the `textual` package. Required runtime and test
packages are `pytest` and `pytest-asyncio`.

## Evaluation Notes

The checks are split into atomic public API cases and integration cases that
combine independent public projections of the same app, widget, message, and
layout facts. Integration dependency markers are informational and point only
to atomic behaviors. A minimal import-only package should collect the checks
while passing well below ten percent, demonstrating that real public behavior
is required rather than import availability alone.
