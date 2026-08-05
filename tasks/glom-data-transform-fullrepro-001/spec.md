# glom Nested Transformation Behavior

## Product Overview

This package describes the deterministic public Python behavior of glom at
fixed commit `30b477ab65560914a38f331614947d0894701044`. glom transforms
nested mappings, sequences, and ordinary objects through composable
specifications.

## Scope

The covered surface includes `glom`, `Path`, `T`, `S`, `A`, `Val`, `Spec`,
`Coalesce`, `Invoke`, `Call`, `Inspect`, `Assign`, `Delete`,
`Flatten`, `flatten`, `Match`, `Switch`, `Check`, `Glommer`, and the public
exception classes used by those operations. Checks use local dictionaries,
lists, and classes created by the test runner.

The pinned checkout does not expose a public `glom.build` symbol or a
documented `build` API. That requested name is therefore recorded as an
unavailable surface. It also does not export `Let` from the top-level
package, so scope binding is represented by the public `S` equivalent.
Construction behavior is represented by the public
`Spec`, `Call`, `Invoke`, `Path`, and `Glommer` APIs that are present.

## Installable Surface

The target root supplied to pytest contains the public `glom` package. The
checks import only names exported by `glom`; they do not depend on optional
YAML or TOML support, network features, source tests, or private modules.

## Product State Model

A target is read through path specs and transformed into new mappings,
sequences, scalar values, or object-derived values. `T` refers to the
current target, `S` refers to scope bindings, and `Val` preserves a literal
value. `Spec` provides reusable evaluation. `Assign` and `Delete` mutate
runner-created targets in place. `Coalesce`, `Switch`, `Match`, and `Check`
provide fallback, routing, matching, and validation states.

## Error Semantics

Path failures raise `PathAccessError`, a `GlomError` subtype with public
`exc`, `path`, and `part_idx` attributes. Coalescing failures raise
`CoalesceError` with the attempted spec, skipped results, and path.
Validation failures raise `MatchError`, `TypeMatchError`, or `CheckError`;
`CheckError` exposes `msgs`, `check_obj`, and `path`. Mutation failures use
public assignment or deletion error types. Checks assert types and
structured attributes, not incidental diagnostic text.

## Cross-View Invariants

Equivalent path expressions and `T` expressions project the same nested
values. Scope bindings can feed later output fields. A reusable `Spec` and a
`Glommer` can evaluate the same public transformation. Assignment and
deletion are visible through subsequent reads. Matching and checking preserve
valid values or produce their documented fallback results.

## Representative Workflows

Workflows combine multiple operations such as path selection, scope binding,
literal construction, callable invocation, flattening, matching, validation,
assignment, deletion, fallback, and final projection. Integrations use
runner-created nested dict/list/object data and declare dependencies on
physical atomic checks.

## Non-Goals

The package excludes `glom.build` and top-level `Let` because they are absent
from the pinned public surface, optional YAML/TOML loaders, network or socket behavior, CLI
subprocesses, ambient files and environment state, sleeps, timing behavior,
private imports, upstream tests, exact exception strings, exact reprs, and
whole-output snapshots that would make valid implementations brittle.

## Invocation Protocol

Run pytest against both test files with `--target-root` pointing to the
implementation root. Local evidence may enable `pytest-json-report`.
Integration tests are native pytest tests and do not invoke another test
runner.

## Environment

The reference environment is Python 3.11 on Linux without network access.
Python 3.10 is also used for local replay. The target package is not pre-installed.
Requirements are `pytest` and `pytest-json-report`; the
target checkout supplies its pinned runtime dependencies locally.

## Evaluation Notes

Current evidence is same-process local replay only. It does not establish a
trusted black-box Stage 4 runner, external signature, trusted provenance,
network isolation, final qualification, or a final QUALIFIED status.
