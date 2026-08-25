# transitions Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`transitions` provides object-oriented finite-state machines. A machine owns state and transition definitions, and manages the state projection of one or more models. A model is either a separate application object or the machine instance itself.

## Non-Goals

- This specification does not require a command-line interface.
- This specification does not require Django integration.
- This specification does not require graph backends beyond the documented graph-object contract.
- This specification does not require undocumented internal helpers, storage layouts, or logging formats.

## Representative Workflows

```python
from transitions import Machine

class Matter:
    def is_hot(self):
        return True

sample = Matter()
machine = Machine(sample, states=['solid', 'liquid', 'gas'], initial='solid')
machine.add_transition('melt', 'solid', 'liquid', conditions='is_hot')

assert sample.is_solid()
assert sample.may_melt()
assert sample.melt() is True
assert sample.state == 'liquid'
```

If `is_hot` returns false, `sample.melt()` must return `False` and `sample.state` must remain `solid`. Calling `sample.melt()` while the model is in an unrelated state must raise `MachineError` unless invalid triggers are configured to be ignored.

## Core Objects

This section defines the fundamental state, transition, event, and error types that compose a finite-state machine.

**State identity.** A `State` represents a persistent machine state. Its `name` attribute must return the public state name and its `value` attribute must return the state value, which equals the name when no separate value is supplied. When `on_enter` or `on_exit` callbacks are provided, they must be invoked during the corresponding state entry and exit phases. When `final` is true, the state must be treated as a final state.

**State callback registration.** `State.add_callback(trigger, func)` must accept `enter` or `exit` as the trigger; other trigger values must raise `AttributeError`.

**Transition structure.** A `Transition` describes one possible state change. Its `source` attribute must expose the configured source state name and its `dest` attribute must expose the destination state name. When `conditions`, `unless`, `before`, `after`, or `prepare` callbacks are provided, they must participate in the documented event processing phases. `Transition.add_callback(trigger, func)` must accept `prepare`, `before`, or `after`; other trigger values must raise `AttributeError`.

**Event and event data.** An `Event` represents a named trigger. Its `name` attribute must return the trigger name. `EventData` exposes the current transition attempt to callbacks, providing `state`, `event`, `machine`, `model`, `args`, and `kwargs` attributes. With `send_event=True`, callbacks must receive an `EventData` instance; otherwise they must receive the trigger's positional and keyword arguments directly.

**Errors.** `MachineError` identifies invalid transition or machine-configuration failures.

## Machine Construction

This section covers how `Machine` creates and initializes a finite-state machine with models, states, transitions, and behavioral options.

**Self as model.** A machine constructed without an explicit model, or with the documented self-literal, must use itself as its model. When `model` is `None` or an empty collection, the machine must register no model until `add_model` is called.

**States.** The `states` parameter must accept strings, enum members, `State` objects, and documented state dictionaries containing at least a `name` key. Unsupported state objects must raise an error when resolved or added.

**Initial state.** When `initial` is omitted, the machine must create a default state named `initial` and set models to it. When `initial` is set to `None`, the machine must require an `initial` argument whenever a model is added via `add_model`; omission must raise `ValueError`.

**Model attribute.** When `model_attribute` is set to a non-default value, the attribute storing model state must use that name. Generated state-check helpers must follow the pattern `is_<attribute>_<state>()` and automatic transition helpers must follow `to_<attribute>_<state>()`. A trigger whose name equals the configured `model_attribute` must be rejected with `ValueError`.

**Event delivery.** When `send_event` is true, callbacks must receive `EventData` instead of direct positional and keyword arguments. Without `send_event`, on-enter, on-exit, before, after, and prepare callbacks must receive the trigger's positional and keyword arguments directly.

**Automatic transitions.** When `auto_transitions` is true, the machine must generate `to_<state>()` and `may_to_<state>()` helpers for every added state.

**Queue and trigger behavior.** When `queued` is true, nested triggers must be queued and processed after the active transition completes, and every queued trigger call must return `True` at queue time. When `queued` is false, nested triggers must run immediately. When `ignore_invalid_triggers` is true, an invalid trigger must return `False` instead of raising `MachineError`.

**Machine-level callbacks.** When `before_state_change`, `after_state_change`, `prepare_event`, `finalize_event`, `on_exception`, or `on_final` callbacks are provided, they must participate in the documented event processing phases. When `ordered_transitions` is true, ordered transitions among the declared states must be created automatically.

## Machine Configuration and Inspection

This section covers model management and state/transition inspection after construction.

**Model management.** `add_model(model, initial=None)` must register one model or a collection of models. When `initial` is provided, the model must start in that state instead of the machine's default initial state. `remove_model(model)` must unregister models and must remove their queued events when a queue is active.

**State lookup.** `get_state(state)` must return the registered state object; an unknown state must raise `ValueError`. `get_model_state(model)` must return the state object for that model's current state. `set_state(state, model=None)` must set the selected model or models to a registered state; an unknown state must raise `ValueError`.

**State definition.** `add_state(states, on_enter=None, on_exit=None, ignore_invalid_triggers=None, **kwargs)` and `add_states(states, on_enter=None, on_exit=None, ignore_invalid_triggers=None, **kwargs)` must add state definitions. State objects passed to a machine must remain persistent rather than being reset by later entries.

**Transition queries.** `get_triggers(*states)` must return the trigger names defined for any supplied source state. `get_transitions(trigger='', source='*', dest='*')` must return transition objects matching the supplied filters; each returned transition must expose `source` and `dest` attributes. It must return an empty list for an unknown requested trigger.

## Transitions and Dynamic Helpers

This section covers transition registration, wildcard sources, reflexive transitions, ordered transitions, and the dynamic helpers generated on models.

**Transition registration.** `add_transition(trigger, source, dest, conditions=None, unless=None, before=None, after=None, prepare=None, **kwargs)` must register a trigger. The `source` parameter must accept one source state, a list of source states, or `'*'`; the wildcard must apply only to states present when the transition is added. When `dest` is `'='`, the transition must preserve the source state while still processing state exit and entry callbacks. When `dest` is `None`, the transition must run transition callbacks without leaving or entering a state.

**Bulk transitions.** `add_transitions(transitions)` must accept documented transition dictionaries or positional transition lists. `add_ordered_transitions()` must create an ordered cycle through the declared states using the trigger name `next_state` by default. When `loop` is true, the cycle must wrap from the last state back to the first. When `loop` is false, triggering from the last state must raise `MachineError`. An order with fewer than two states must raise `ValueError`.

**Transition removal.** `remove_transition(trigger, source='*', dest='*')` must remove matching transitions and must remove the dynamic trigger from registered models when no transitions for that trigger remain.

**Dispatch.** `dispatch(trigger, *args, **kwargs)` must invoke the named trigger helper for every registered model; a missing helper must raise `AttributeError`.

**Dynamic trigger helpers.** For every added trigger, the model must receive a `<trigger>()` helper that fires the transition and returns `True` on success or `False` when conditions fail. A `may_<trigger>()` helper must execute prepare callbacks and evaluate conditions without changing state; it must return `True` when a matching transition would fire and `False` otherwise. The `trigger(name, *args, **kwargs)` helper must fire the named trigger; `may_trigger(name, ...)` must evaluate it without changing state. An unknown named trigger must return `False` when invalid triggers are ignored and must raise `AttributeError` otherwise.

**Automatic state helpers.** When `auto_transitions` is true, every added state must produce `to_<state>()` and `may_to_<state>()` helpers. `to_<state>()` must update the model state and run the documented state-change callbacks. `may_to_<state>()` must report whether the automatic transition would succeed without changing state.

**State-check helpers.** For every added state, the model must receive an `is_<state>()` helper that returns whether the model's current state equals that state.

## Callback and Event Behavior

This section covers callback resolution, event processing phases, condition evaluation, exception handling, and queue semantics.

**Callback references.** Callback references must accept callable objects, model attribute names, and importable dotted names. A callback reference that resolves to neither a model attribute nor an importable callable must raise `AttributeError`.

**Event processing phases.** For a matching transition, the machine must process the documented event preparation, condition, transition, state-entry, final-state, completion, and finalization phases. A final destination must invoke machine `on_final` callbacks.

**Condition evaluation.** All `conditions` must return true, and all `unless` conditions must return false, before a transition changes state. If a possible transition's conditions fail, its trigger must return `False` and must leave the model state unchanged.

**Invalid triggers.** An invalid trigger must raise `MachineError` by default. When the effective `ignore_invalid_triggers` setting is true, it must return `False` instead.

**Exception handling.** A callback exception before state assignment must leave the old state intact; a callback exception after state assignment must retain the new state. `finalize_event` must run after every processed event, including a failed condition or exception, except when the finalizer itself raises. `on_exception` must receive the event data when an event callback raises; without an exception handler, the original exception must be raised.

**Queue semantics.** When `queued` is false, nested triggers must run immediately. When `queued` is true, nested triggers must run after the active transition completes and every trigger call must return `True` at queue time. A queued transition exception must clear the outstanding queue and must be raised.

## Extension Machines

This section covers hierarchical, graph, locked, and asynchronous machine extensions that compose additional behaviors with the base machine.

**Hierarchical machine.** `HierarchicalMachine` accepts the same base machine arguments and supports nested state dictionaries with `children` or `states`, optional `initial`, optional `parallel`, and local `transitions`. `NestedState` provides an explicit nested state object with support for an `initial` child and `on_final` callbacks. Nested state names must use `NestedState.separator`, whose default is `_`. A nested machine using the default separator must treat underscores in state names as hierarchy separators. Entering a nested target with an `initial` child must enter that child recursively. A parallel state must enter every configured branch. A wildcard transition in a hierarchical machine must apply to root states only.

**Hierarchical state checks.** `is_<state>(allow_substates=True)` must return true when the model is in any descendant of that state. With the default `allow_substates=False`, it must require an exact state match and must return false when the model is in a child state.

**Graph machine.** `GraphMachine` accepts the base arguments plus graph-specific options. It must attach `get_graph(show_roi=False)` to models and must return a graph object whose `draw` accepts a filename or stream; a `None` target must return serialized graph content as bytes for Graphviz backends or text for the Mermaid backend. `HierarchicalGraphMachine` combines graph and hierarchy behavior.

**Locked machine.** `LockedMachine` accepts the base arguments plus an optional `machine_context`. It must serialize machine-method and model-trigger access through re-entrant contexts. A supplied context that is not re-entrant must fail during nested machine access. `LockedGraphMachine`, `LockedHierarchicalMachine`, and `LockedHierarchicalGraphMachine` combine their named behaviors.

**Async machine.** `AsyncMachine` accepts the base machine arguments and returns awaitable model event helpers. It must await asynchronous callbacks and must accept synchronous callbacks. With `queued='model'`, it must keep model queues separate and must clear only the queue belonging to a model whose event raises. `HierarchicalAsyncMachine`, `AsyncGraphMachine`, and `HierarchicalAsyncGraphMachine` combine their named behaviors. `AsyncTimeout` supplies the corresponding asynchronous timeout feature for states.

**Factory.** `MachineFactory.get_predefined(graph=False, nested=False, locked=False, asyncio=False)` must return the predefined machine class matching the selected supported feature combination. An unsupported combination must raise `ValueError`.

## State Features and Typed Definitions

This section covers state feature mixins that add runtime behavior to states and model-definition utilities for declarative machine setup.

**Feature decorator.** `@add_state_features(*mixins)` decorates a machine class so its states combine the supplied feature mixins. The decorated class must use the feature state type for subsequent state definitions.

**Tags.** The `Tags` mixin accepts `tags` on state construction and must expose `is_<tag>` attributes that return whether the state has each listed tag.

**Error.** The `Error` mixin accepts `accepted` or an `accepted` tag and, with automatic transitions disabled, must raise `MachineError` when an unaccepted final state cannot be left.

**Timeout.** The `Timeout` mixin accepts `timeout` seconds and `on_timeout` callbacks. Entering such a state must schedule its timeout callback; setting a timeout without `on_timeout` must raise `AttributeError`.

**Volatile and retry.** The `Volatile` mixin accepts `volatile` and `hook='scope'`. Entering the state must assign a new instance of the selected class to the model hook, and leaving it must remove that hook. The `Retry` mixin accepts `retries` and `on_failure`; setting a positive retry limit without `on_failure` must raise `AttributeError`, and exceeding the allowed self-reentries must invoke `on_failure` instead of entering the state.

**Model definition utilities.** `transition(source, dest=None, conditions=None, unless=None, before=None, after=None, prepare=None)` returns a transition definition dictionary. `event(*configs)` and `add_transitions(*configs)` declare transition configurations on a model class. `with_model_definitions(cls)` adapts a machine class to consume those model declarations. `generate_base_model(config)` returns a base-model definition compatible with the supplied machine configuration.

## State Model

Each registered model has a current state value in its configured `model_attribute`, which defaults to `state`. The machine projects the same configuration through its state registry, model helpers, and transition/event operations.

- A model's configured state attribute must return the state selected by the most recently completed state-changing transition.
- `machine.get_state(model.state)` must return the state object representing that model value.
- A generated `is_<state>()` helper must return whether the same model state equals its target state.
- A generated `to_<state>()` helper must update the model state and run the documented state-change callbacks.
- A generated trigger must return `True` when it completes a matching transition and must return `False` when no matching transition passes its conditions, subject to queued-mode rules.
- `machine.dispatch(trigger, ...)` must return the logical conjunction of the results obtained by invoking that trigger for every registered model.

## Error Semantics

- `MachineError` must identify invalid triggers and must be raised when a trigger is fired from a state with no matching transition and invalid triggers are not ignored. When `loop` is false in ordered transitions, it must be raised when triggering from the last state.
- `ValueError` must identify a model added without an initial state when the machine has `initial=None`, an unknown requested state, an illegal trigger equal to the configured state attribute, an ordered sequence with fewer than two states, and an unsupported factory selection.
- `AttributeError` must identify an unresolved callback, unsupported callback category, a missing dynamic trigger when invalid triggers are not ignored, and omitted required state-feature callbacks.

## Cross-View Invariants

1. After a successful trigger, the model state attribute must equal the destination state selected by that trigger.
2. After a successful trigger, `machine.get_model_state(model).name` must equal the model state attribute for string states.
3. After a successful trigger, the matching generated `is_<state>()` helper must return `True` and helpers for other states must return `False`.
4. After `machine.set_state(target, model)`, the model state attribute must equal `target` and `machine.get_state(target)` must return the corresponding state object.
5. After `machine.add_transition(name, source, dest)`, `name` must appear in `machine.get_triggers(source)` and the model trigger helper must select that transition from `source`.
6. When a conditional transition returns `False`, the model state attribute, `get_model_state`, and generated state-check helper must all continue to report the pre-trigger state.
7. When `model_attribute` is customized, its generated `is_<attribute>_<state>()` and `to_<attribute>_<state>()` helpers must observe and update that customized attribute.
8. When multiple models are registered, each model's state must be independent; a trigger on one model must not change another model's state attribute or state-check helpers.
9. `dispatch(trigger)` must return the logical conjunction of per-model trigger results, and each model's final state must reflect its individual trigger outcome.
10. In a hierarchical machine, `is_<parent>(allow_substates=True)` must return `True` when the model is in a child state, while `is_<parent>()` with the default `allow_substates=False` must return `False` for the same child state.

## Public Interface

### Import Surface

Install the package with `pip install transitions`.

```python
from transitions import State, Transition, Event, EventData, Machine, MachineError
from transitions.extensions import (
    GraphMachine, HierarchicalGraphMachine, HierarchicalMachine, LockedMachine,
    MachineFactory, LockedGraphMachine, LockedHierarchicalMachine,
    LockedHierarchicalGraphMachine, AsyncMachine, AsyncGraphMachine,
    HierarchicalAsyncMachine, HierarchicalAsyncGraphMachine,
)
from transitions.extensions.nesting import NestedState
from transitions.extensions.states import (
    Tags, Error, Timeout, Volatile, Retry, add_state_features,
)
from transitions.extensions.asyncio import AsyncTimeout
from transitions.experimental.utils import (
    generate_base_model, with_model_definitions, event, add_transitions, transition,
)
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| State | class | Represent a persistent machine state |
| Transition | class | Describe one possible state transition |
| Event | class | Represent a named trigger |
| EventData | class | Expose current transition attempt to callbacks |
| MachineError | exception | Identify invalid transitions or configuration |
| Machine | class | Create and manage a finite-state machine |
| HierarchicalMachine | class | Machine with nested state support |
| NestedState | class | Explicit nested state object |
| GraphMachine | class | Machine with graph visualization |
| HierarchicalGraphMachine | class | Combined graph and hierarchy machine |
| LockedMachine | class | Machine with thread-safe access |
| LockedGraphMachine | class | Combined locked and graph machine |
| LockedHierarchicalMachine | class | Combined locked and hierarchical machine |
| LockedHierarchicalGraphMachine | class | Combined locked, hierarchical, and graph machine |
| AsyncMachine | class | Machine with async event helpers |
| AsyncGraphMachine | class | Combined async and graph machine |
| HierarchicalAsyncMachine | class | Combined hierarchical and async machine |
| HierarchicalAsyncGraphMachine | class | Combined hierarchical, async, and graph machine |
| MachineFactory | class | Factory for predefined machine classes |
| add_state_features | decorator | Add feature mixins to machine states |
| Tags | state mixin | Expose tag-based state attributes |
| Error | state mixin | Raise on unaccepted final states |
| Timeout | state mixin | Schedule timeout callbacks on entry |
| AsyncTimeout | state mixin | Asynchronous timeout feature |
| Volatile | state mixin | Assign scoped instances on state entry |
| Retry | state mixin | Limit self-reentries with failure callback |
| transition | function | Return a transition definition |
| event | function | Declare transition configurations on a model |
| add_transitions | function | Declare transition configurations on a model |
| with_model_definitions | function | Adapt machine for model declarations |
| generate_base_model | function | Generate base model from machine config |

### CLI Entry Points

There is no console script for this package. `python -m transitions`.` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Assessment observes only the public behavior described in this specification: machine construction, state and transition registration, trigger dispatch, generated model helpers, callback ordering, extension machines, documented error classes, and cross-view invariants. Each checked behavior is observed through public imports, model attributes, returned values, and raised exception classes. Private modules, private attributes, exact `repr` output, exact exception wording, and internal storage layouts are not examined.
