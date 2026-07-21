# transitions Specification

## Product Overview

`transitions` provides object-oriented finite-state machines. A machine owns state and transition definitions, and manages the state projection of one or more models. A model is either a separate application object or the machine instance itself.

## Scope

This specification covers basic machines, state and transition callbacks, dynamic model helpers, multiple models, hierarchical, graph, locking, asynchronous, state-feature, and typed-definition extensions.

## Installable Surface

Install the package with `pip install transitions`.

The following imports are part of the supported surface:

- `from transitions import State, Transition, Event, EventData, Machine, MachineError`
- `from transitions.extensions import GraphMachine, HierarchicalGraphMachine, HierarchicalMachine, LockedMachine, MachineFactory, LockedGraphMachine, LockedHierarchicalMachine, LockedHierarchicalGraphMachine, AsyncMachine, AsyncGraphMachine, HierarchicalAsyncMachine, HierarchicalAsyncGraphMachine`
- `from transitions.extensions.nesting import NestedState`
- `from transitions.extensions.states import Tags, Error, Timeout, Volatile, Retry, add_state_features`
- `from transitions.extensions.asyncio import AsyncTimeout`
- `from transitions.experimental.utils import generate_base_model, with_model_definitions, event, add_transitions, transition`

## Product State Model

Each registered model has a current state value in its configured `model_attribute`, which defaults to `state`. The machine projects the same configuration through its state registry, model helpers, and transition/event operations.

- A model's configured state attribute must return the state selected by the most recently completed state-changing transition.
- `machine.get_state(model.state)` must return the state object representing that model value.
- A generated `is_<state>()` helper must return whether the same model state equals its target state.
- A generated `to_<state>()` helper must update the model state and run the documented state-change callbacks.
- A generated trigger must return `True` when it completes a matching transition and must return `False` when no matching transition passes its conditions, subject to queued-mode rules.
- `machine.dispatch(trigger, ...)` must return the logical conjunction of the results obtained by invoking that trigger for every registered model.

## Public API

### Core objects

`State(name, on_enter=None, on_exit=None, ignore_invalid_triggers=None, final=False)` represents a persistent machine state. Its `name` returns the public state name and its `value` returns the supplied state value. `add_callback(trigger, func)` must accept `enter` or `exit`; other trigger values must raise `AttributeError`.

`Transition(source, dest, conditions=None, unless=None, before=None, after=None, prepare=None)` describes one possible transition. `add_callback(trigger, func)` must accept `prepare`, `before`, or `after`; other trigger values must raise `AttributeError`.

`Event(name, machine)` represents a named trigger, and `EventData(state, event, machine, model, args, kwargs)` exposes the current attempt to callbacks. With `send_event=True`, callbacks must receive `EventData`; otherwise they must receive the trigger's positional and keyword arguments directly.

`MachineError(value)` identifies invalid transition or machine-configuration failures.

### Machine construction

`Machine(model=Machine.self_literal, states=None, initial='initial', transitions=None, send_event=False, auto_transitions=True, ordered_transitions=False, ignore_invalid_triggers=None, before_state_change=None, after_state_change=None, name=None, queued=False, prepare_event=None, finalize_event=None, model_attribute='state', model_override=False, on_exception=None, on_final=None, **kwargs)` creates a state machine.

- `states` must accept strings, enum members, `State` objects, and documented state dictionaries. Unsupported state objects must raise an error when they are resolved or added.
- A machine with no explicit model must use itself as its model. A machine created with `model=None` or an empty model collection must register no model until `add_model` runs.
- A machine with omitted `initial` must create the documented default `initial` state. A machine with `initial=None` must require an `initial` argument whenever a model is added; omission must raise `ValueError`.
- `model_attribute` must choose the attribute that stores each model state. Generated state-check and automatic-transition helpers must include that attribute name when it is not `state`.

### Machine configuration and inspection

`add_model(model, initial=None)` registers one model or a collection of models. `remove_model(model)` unregisters them and must remove their queued events when a queue is active.

`get_state(state)` returns the registered state object. An unknown state must raise `ValueError`. `get_model_state(model)` returns the state object for that model, and `set_state(state, model=None)` must set the selected model or models to a registered state; an unknown state must raise `ValueError`.

`add_state(states, on_enter=None, on_exit=None, ignore_invalid_triggers=None, **kwargs)` and `add_states(states, on_enter=None, on_exit=None, ignore_invalid_triggers=None, **kwargs)` add state definitions. State objects passed to a machine must remain persistent rather than being reset by later entries.

`get_triggers(*states)` returns the trigger names defined for any supplied source state. `get_transitions(trigger='', source='*', dest='*')` returns transitions matching the supplied filters and must return an empty list for an unknown requested trigger.

### Transitions and dynamic helpers

`add_transition(trigger, source, dest, conditions=None, unless=None, before=None, after=None, prepare=None, **kwargs)` registers a trigger. `source` must accept one source, a list of sources, or `'*'`; the wildcard must apply only to states present when the transition is added. `dest='='` must preserve each source state while still processing state exit and entry callbacks. `dest=None` must run transition callbacks without leaving or entering a state. A trigger equal to `model_attribute` must raise `ValueError`.

`add_transitions(transitions)` accepts documented transition dictionaries or positional transition lists. `add_ordered_transitions(states=None, trigger='next_state', loop=True, loop_includes_initial=True, conditions=None, unless=None, before=None, after=None, prepare=None, **kwargs)` creates the documented ordered cycle; an order with fewer than two states must raise `ValueError`.

`remove_transition(trigger, source='*', dest='*')` removes matching transitions and must remove the dynamic trigger from registered models when no transitions remain. `dispatch(trigger, *args, **kwargs)` invokes the named helper for every model; a missing helper must raise `AttributeError`.

For every added state, automatic transitions must add `to_<state>()` and `may_to_<state>()` helpers when `auto_transitions=True`. For every added trigger, the model must receive `<trigger>()`, `may_<trigger>()`, and `trigger(name, *args, **kwargs)` helpers unless the selected override policy preserves an existing attribute. `may_<trigger>()` and `may_trigger(name, ...)` must execute prepare callbacks and evaluate conditions without changing state; an unknown named trigger must return `False` when invalid triggers are ignored and must raise `AttributeError` otherwise.

### Callback and event behavior

Callback references must accept callable objects, model attribute names, and importable dotted names. A callback reference that resolves to neither a model attribute nor an importable callable must raise `AttributeError`.

For a matching transition, the machine must process the documented event preparation, condition, transition, state-entry, final-state, completion, and finalization phases. A final destination must invoke machine `on_final` callbacks.

Conditions must all return true, and `unless` conditions must all return false, before a transition changes state. If a possible transition's conditions fail, its trigger must return `False` and must leave the model state unchanged.

An invalid trigger must raise `MachineError` by default. When the effective `ignore_invalid_triggers` setting is true, it must return `False` instead. A callback exception before state assignment must leave the old state intact; a callback exception after state assignment must retain the new state. `finalize_event` must run after every processed event, including a failed condition or exception, except when the finalizer itself raises. `on_exception` must receive the event data when an event callback raises; without an exception handler, the original exception must be raised.

When `queued=False`, nested triggers must run immediately. When `queued=True`, nested triggers must run after the active transition completes and every trigger call must return `True` at queue time. A queued transition exception must clear the outstanding queue and must be raised.

### Extension machines

`HierarchicalMachine` accepts the same base machine arguments and supports nested state dictionaries with `children` or `states`, optional `initial`, optional `parallel`, and local `transitions`. `NestedState(name, on_enter=None, on_exit=None, ignore_invalid_triggers=None, final=False, initial=None, on_final=None)` provides an explicit nested state object.

- Nested state names must use `NestedState.separator`, whose default is `_`. A nested machine using the default separator must treat underscores in state names as hierarchy separators.
- Entering a nested target with an `initial` child must enter that child recursively. A parallel state must enter every configured branch.
- A wildcard transition in a hierarchical machine must apply to root states only.
- `is_<state>(allow_substates=True)` must return true for an active descendant; with the default `allow_substates=False`, it must require an exact state match.

`GraphMachine` accepts the base arguments plus `title='State Machine'`, `show_conditions=False`, `show_state_attributes=False`, `show_auto_transitions=False`, `use_pygraphviz=True`, and `graph_engine='pygraphviz'`. It must attach `get_graph(show_roi=False)` to models and must return a graph object whose `draw` accepts a filename or binary stream; a `None` target must return graph bytes. `HierarchicalGraphMachine` combines graph and hierarchy behavior.

`LockedMachine` accepts the base arguments plus `machine_context=None`. It must serialize machine-method and model-trigger access through re-entrant contexts. A supplied context that is not re-entrant must fail during nested machine access. `LockedGraphMachine`, `LockedHierarchicalMachine`, and `LockedHierarchicalGraphMachine` combine their named behaviors.

`AsyncMachine` accepts the base machine arguments and returns awaitable model event helpers. It must await asynchronous callbacks and must accept synchronous callbacks. With `queued='model'`, it must keep model queues separate and must clear only the queue belonging to a model whose event raises. `HierarchicalAsyncMachine`, `AsyncGraphMachine`, and `HierarchicalAsyncGraphMachine` combine their named behaviors.

`MachineFactory.get_predefined(graph=False, nested=False, locked=False, asyncio=False)` returns the predefined machine class matching the selected supported feature combination. An unsupported combination must raise `ValueError`.

### State features and typed definitions

`@add_state_features(*mixins)` decorates a machine class so its states combine the supplied feature mixins. The decorated class must use the feature state type for subsequent state definitions.

`Tags` accepts `tags` and must expose `is_<tag>` attributes that return whether the state has that tag. `Error` accepts `accepted` or an `accepted` tag and, with automatic transitions disabled, must raise `MachineError` when an unaccepted final state cannot be left.

`Timeout` accepts `timeout` seconds and `on_timeout`. Entering such a state must schedule its timeout callback; setting a timeout without `on_timeout` must raise `AttributeError`. `AsyncTimeout` supplies the corresponding asynchronous timeout feature.

`Volatile` accepts `volatile` and `hook='scope'`. Entering the state must assign a new instance of the selected class to the model hook, and leaving it must remove that hook. `Retry` accepts `retries` and `on_failure`; setting a positive retry limit without `on_failure` must raise `AttributeError`, and exceeding the allowed self-reentries must invoke `on_failure` instead of entering the state.

`transition(source, dest=None, conditions=None, unless=None, before=None, after=None, prepare=None)` returns a transition definition. `event(*configs)` and `add_transitions(*configs)` declare transition configurations on a model. `with_model_definitions(cls)` adapts a machine class to consume those declarations. `generate_base_model(config)` returns a base-model definition compatible with the supplied machine configuration.

## Error Semantics

- `MachineError` must identify invalid triggers.
- `ValueError` must identify a model added without an initial state when the machine has `initial=None`, an unknown requested state, an illegal trigger equal to the configured state attribute, an ordered sequence with fewer than two states, and an unsupported factory selection.
- `AttributeError` must identify an unresolved callback, unsupported callback category, a missing dynamic trigger when invalid triggers are not ignored, and omitted required state-feature callbacks.

## Cross-View Invariants

- After a successful trigger, the model state attribute must equal the destination state selected by that trigger.
- After a successful trigger, `machine.get_model_state(model).name` must equal the model state attribute for string states.
- After a successful trigger, the matching generated `is_<state>()` helper must return `True` and helpers for other states must return `False`.
- After `machine.set_state(target, model)`, the model state attribute must equal `target` and `machine.get_state(target)` must return the corresponding state object.
- After `machine.add_transition(name, source, dest)`, `name` must appear in `machine.get_triggers(source)` and the model trigger helper must select that transition from `source`.
- When a conditional transition returns `False`, the model state attribute, `get_model_state`, and generated state-check helper must all continue to report the pre-trigger state.
- When `model_attribute` is customized, its generated `is_<attribute>_<state>()` and `to_<attribute>_<state>()` helpers must observe and update that customized attribute.

## Representative Workflow

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

## Non-Goals

- This specification does not require a command-line interface.
- This specification does not require Django integration.
- This specification does not require graph backends beyond the documented graph-object contract.
- This specification does not require undocumented internal helpers, storage layouts, or logging formats.

## Invocation Protocol

- Console script name: `TBD`
- `python -m transitions`: `not supported`
- Exit codes:
  - `0`: success
  - `1`: `python -m transitions` cannot execute because the package has no `__main__` module

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.
