# python-statemachine Public Behavior Specification

## Product Overview

python-statemachine is a Python library for declaring finite state machines and
statecharts as classes. Applications define `State` objects, transition
expressions, and `Event` objects, then drive an instance with `send()` or event
method calls. Observable runtime facts include the active configuration,
configuration values, event availability, callback return values, listener
side effects, model mutations, termination status, and public validation
exceptions.

## Scope

The supported surface in this package is the documented public runtime API:
`StateChart`, `StateMachine`, `State`, `HistoryState`, `Event`, declarative
transitions, guards, validators, actions, listener registration, model binding,
compound states, parallel states, history pseudo-states, automatic events,
error events, async callbacks, and public class or instance validation errors.

## Public Import Surface

Applications may import `StateChart`, `StateMachine`, `State`, `HistoryState`,
`Event`, and `TModel` from `statemachine`. Public exception classes such as
`InvalidDefinition` and `TransitionNotAllowed` are imported from
`statemachine.exceptions`, as shown in the documentation. The tests do not
import private engine modules, source test helpers, or implementation-only
objects.

## Product State Model

A declared machine has named states, named events, transition topology, and
runtime configuration. A flat machine has one active state, while compound and
parallel statecharts can have multiple active states. `configuration` exposes
active `State` objects and `configuration_values` exposes each state's custom
value or identifier. Guards and validators select transitions before state
changes; actions, state enter and exit callbacks, and listeners observe or
mutate public state during the transition lifecycle.

## Error Semantics

Invalid machine declarations and invalid callback wiring raise
`InvalidDefinition`. `StateMachine` rejects unmatched events with
`TransitionNotAllowed`, while `StateChart` tolerates unmatched events by
default. Validator exceptions propagate to the caller and leave the active
configuration unchanged. Runtime action errors may be handled through the
documented `error.execution` event when the statechart defines a matching
transition. Tests assert exception types and public state rather than exact
wording.

## Cross-View Invariants

The same declared workflow must agree across runtime views: event objects expose
the identifiers used by `send()`, allowed and enabled event projections match
the current configuration and guard arguments, listener records match the
transition source and target observed through configuration, model-facing
callbacks mutate the same object passed to the constructor, and formatted table
output names the same states and events declared on the class.

## Representative Workflow

A representative client declares an order workflow with draft, reserved,
approved, and rejected states. The machine uses a model guard to decide whether
items exist, an action to reserve item totals, a listener to record transitions,
and a later review event to route approval or rejection. Related workflows cover
compound document editing, deployment pipelines with parallel regions, history
restoration, automatic completion events, and async callback execution.

## Non-Goals

This package does not require external diagram rendering, GraphViz binaries,
network access, delayed-event timing, sleeps, database integrations, Django
integration behavior, private parser or engine APIs, source test modules,
performance measurement behavior, or exact undocumented exception text. It also avoids
asserting generated image bytes or execution through external services.

## Invocation Protocol

Install the requirements file that accompanies the public behavior tests and
make an implementation importable as `statemachine`. Run the tests with:

```bash
python -m pytest <test-directory> -q -W error
```

The public behavior tests use deterministic in-memory models and temporary
process state only. They do not require network access, a database, Docker,
external executables, sleeps, or asynchronous timing races.

## Environment

The intended evaluation environment is Linux with Python 3.11 and without network access
during the test run. The target package is not pre-installed; the implementation
under evaluation must provide the `statemachine` package. Required runtime and
test packages are `pytest` and `pytest-json-report`.

## Evaluation Notes

The tests are split into atomic checks for individual public features and
integration checks that combine independent projections of the same statechart
facts. Integration dependency markers are informational and refer only to
atomic public behaviors. A minimal import-only implementation should collect
the tests while passing well below ten percent, showing that the tests require
substantive public state machine behavior.
