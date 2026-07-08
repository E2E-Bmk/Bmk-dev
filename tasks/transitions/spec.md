# Transitions Specification

## Product Overview

`transitions` is a lightweight, object-oriented finite state machine library for Python. A `Machine` owns state and transition definitions, decorates one or more model objects with trigger/check/helper methods, and keeps each model's current state in a configurable model attribute.

The core library covers flat state machines. Extension machines add hierarchical and parallel states, graph/markup projections, locking, asynchronous callbacks, state feature mixins, and predefined feature combinations.

## Scope

This specification covers:

- Core state, transition, event, callback, condition, and model-binding behavior.
- Dynamic model helpers such as `trigger`, `may_trigger`, trigger methods, `may_<trigger>`, `is_<state>`, and automatic `to_<state>` transitions.
- Multiple models, custom `model_attribute`, queued processing, final states, enum states, ordered/reflexive/internal/wildcard transitions, pickling, and public introspection methods.
- Hierarchical and parallel state machines, nested state naming, custom separators, local transitions, machine reuse, remapping, and hierarchical final callbacks.
- Async, locking, graph, mermaid/graphviz/pygraphviz, markup, state feature, factory, and experimental typing/model-definition utilities.

This specification does not require matching private helper classes, private attributes, exact object `repr` strings, or backend-specific diagram text byte-for-byte.

## Installable Surface

Install the package with:

```bash
pip install transitions
```

Diagram support can be installed with:

```bash
pip install transitions[diagrams]
```

The package has no command-line interface. Public import paths include:

```python
from transitions import Machine, State, Transition, Event, EventData, MachineError, __version__
from transitions.extensions import (
    GraphMachine, HierarchicalGraphMachine, HierarchicalMachine, LockedMachine,
    MachineFactory, LockedHierarchicalGraphMachine, LockedHierarchicalMachine,
    LockedGraphMachine, AsyncMachine, HierarchicalAsyncMachine,
    AsyncGraphMachine, HierarchicalAsyncGraphMachine,
)
from transitions.extensions.nesting import HierarchicalMachine, NestedState
from transitions.extensions.asyncio import AsyncMachine, HierarchicalAsyncMachine, AsyncTimeout
from transitions.extensions.diagrams import GraphMachine, HierarchicalGraphMachine
from transitions.extensions.markup import MarkupMachine, HierarchicalMarkupMachine
from transitions.extensions.states import (
    add_state_features, Tags, Timeout, Error, Volatile, Retry, VolatileObject,
)
from transitions.extensions.factory import MachineFactory
from transitions.experimental.utils import (
    generate_base_model, with_model_definitions, event, add_transitions, transition,
)
```

`AsyncMachine` and async feature combinations are available on Python versions that support the async extension.

## Public API

Core constructor signatures:

```python
State(
    name, on_enter=None, on_exit=None,
    ignore_invalid_triggers=None, final=False,
)

Transition(
    source, dest, conditions=None, unless=None,
    before=None, after=None, prepare=None,
)

EventData(state, event, machine, model, args, kwargs)

Event(name, machine)

Machine(
    model=Machine.self_literal, states=None, initial="initial", transitions=None,
    send_event=False, auto_transitions=True, ordered_transitions=False,
    ignore_invalid_triggers=None, before_state_change=None,
    after_state_change=None, name=None, queued=False,
    prepare_event=None, finalize_event=None, model_attribute="state",
    model_override=False, on_exception=None, on_final=None, **kwargs,
)
```

Core public methods and properties:

```python
machine.add_model(model, initial=None)
machine.remove_model(model)
machine.model
machine.initial
machine.has_queue
machine.get_state(state)
machine.get_model_state(model)
machine.is_state(state, model)
machine.set_state(state, model=None)
machine.add_state(states, on_enter=None, on_exit=None, ignore_invalid_triggers=None, **kwargs)
machine.add_states(states, on_enter=None, on_exit=None, ignore_invalid_triggers=None, **kwargs)
machine.add_transition(
    trigger, source, dest, conditions=None, unless=None,
    before=None, after=None, prepare=None, **kwargs,
)
machine.add_transitions(transitions)
machine.add_ordered_transitions(
    states=None, trigger="next_state", loop=True,
    loop_includes_initial=True, conditions=None, unless=None,
    before=None, after=None, prepare=None, **kwargs,
)
machine.get_triggers(*states)
machine.get_transitions(trigger="", source="*", dest="*")
machine.remove_transition(trigger, source="*", dest="*")
machine.dispatch(trigger, *args, **kwargs)
machine.callback(func, event_data)
machine.callbacks(funcs, event_data)
machine.resolve_callable(func, event_data)
```

`State` exposes `name`, `value`, `final`, `ignore_invalid_triggers`, `on_enter`, `on_exit`, `enter(event_data)`, `exit(event_data)`, and `add_callback("enter" | "exit", func)`. If `name` is an enum member, `State.name` is the enum member name and `State.value` is the enum member.

`Transition` exposes `source`, `dest`, `prepare`, `before`, `after`, `conditions`, `execute(event_data)`, and `add_callback("prepare" | "before" | "after", func)`. `dest=None` means an internal transition. `dest="="` in `Machine.add_transition` creates a reflexive transition for each source.

`EventData` exposes `state`, `event`, `machine`, `model`, `args`, `kwargs`, `transition`, `error`, and `result`. With `send_event=True`, the same `EventData` object shape is passed as the only callback argument. With `send_event=False`, trigger positional and keyword arguments are forwarded directly to callbacks and conditions.

Extension constructor signatures follow the core `Machine` signature unless noted:

```python
HierarchicalMachine(..., queued=False, model_attribute="state", model_override=False, on_exception=None, on_final=None, **kwargs)

NestedState(
    name, on_enter=None, on_exit=None, ignore_invalid_triggers=None,
    final=False, initial=None, on_final=None,
)

AsyncMachine(..., queued=False | True | "model", model_override=False, on_exception=None, on_final=None, **kwargs)
HierarchicalAsyncMachine(..., queued=False | True | "model", on_exception=None, **kwargs)

LockedMachine(..., machine_context=None, **kwargs)
locked_machine.add_model(model, initial=None, model_context=None)

GraphMachine(
    ..., title="State Machine", show_conditions=False,
    show_state_attributes=False, show_auto_transitions=False,
    use_pygraphviz=True, graph_engine="pygraphviz", **kwargs,
)
graph_model.get_graph(title=None, force_new=False, show_roi=False)
graph.draw(filename, format=None, prog="dot", args="")

MarkupMachine(..., markup=None, auto_transitions_markup=False, **kwargs)
markup_machine.markup
markup_machine.get_markup_config()

MachineFactory.get_predefined(graph=False, nested=False, locked=False, asyncio=False)
```

State feature APIs:

```python
@add_state_features(Tags, Timeout, Error, Volatile, Retry, ...)
class CustomMachine(Machine):
    pass

Tags(..., tags=None)
Timeout(..., timeout=0, on_timeout=None)
Error(..., accepted=False, tags=None)
Volatile(..., volatile=VolatileObject, hook="scope")
Retry(..., retries=0, on_failure=None)
AsyncTimeout(..., timeout=0, on_timeout=None)
```

Experimental typing helpers:

```python
generate_base_model(config_or_markup_machine) -> str
with_model_definitions(machine_class) -> machine_class
event(*transition_configs)
add_transitions(*transition_configs)
transition(source, dest=None, conditions=None, unless=None, before=None, after=None, prepare=None) -> dict
```

## Behavioral Sections

### Machine and Model Binding

If `model` is omitted, the machine instance is used as its own model. Passing `model=None` or an empty list creates a machine without models; models can later be added with `add_model`. Passing a list registers every model. Passing `Machine.self_literal` inside a model list registers the machine itself alongside other models.

When a model is added, the machine assigns the current state value to `model.<model_attribute>`, binds `trigger(name, *args, **kwargs)`, binds `may_trigger(name, *args, **kwargs)`, binds every known trigger method, binds every `may_<trigger>` method, and binds every state-check helper. With the default `model_attribute="state"`, state checks are named `is_<state>()`; with another model attribute, they are named `is_<model_attribute>_<state>()`. Automatic transitions use `to_<state>()` by default and `to_<model_attribute>_<state>()` with a custom model attribute.

By default, helpers are only assigned when the model does not already have an attribute with that name. With `model_override=True`, only already-defined model attributes are replaced; missing convenience methods are not added, while the state attribute is still maintained.

`machine.model` returns the single registered model object when exactly one model is attached, otherwise it returns the list of registered models. `remove_model` stops future state/transition updates for that model but does not remove helper attributes already attached to it. If a queue is active, queued events for removed models are removed from the queue.

If the machine has no configured initial state, adding a model without an explicit `initial` raises an error. If `initial=None` is passed to the constructor, no default `"initial"` state is created and each later model addition must provide an initial state.

### States, Enums, and Final States

States may be declared as strings, enum members, `State` objects, dictionaries of state constructor arguments, or lists mixing those forms. A state object is initialized once when added and remains persistent; changes made to the state object are not reset when models leave and re-enter that state.

String states store their string name in the model attribute. Enum states store the enum member as the model state value, while state lookup and helper names use the enum member name. String and enum states may be mixed, but a string state whose name matches an enum member name conflicts because transitions are keyed by state name.

`on_enter` and `on_exit` callbacks can be passed in state definitions or added later through dynamically resolved machine methods `on_enter_<state>(callback)` and `on_exit_<state>(callback)`. These callback registration helpers live on the machine, not on the model. If a model already defines a bound method named `on_enter_<state>` or `on_exit_<state>`, it is automatically registered as a state callback unless already listed.

Entering the initial state during machine/model initialization does not fire `on_enter` callbacks. A state with `final=True` triggers the machine's `on_final` callbacks when entered after a transition.

### Transitions and Triggers

Transitions may be passed as dictionaries, as positional lists in `trigger, source, dest, ...` order, or added after construction. A single trigger name can have multiple transitions. When a trigger fires, transitions for the current source are evaluated in the order they were added; execution stops after the first transition that completes successfully. Later matching transitions for the same source are not executed.

`source="*"` expands to all states that exist when `add_transition` is called. States added later are not automatically covered by that wildcard transition. `dest="="` creates reflexive transitions whose destination is each source state. `dest=None` creates an internal transition: transition-level callbacks still run, but state exit/enter callbacks and state reassignment do not.

When `auto_transitions=True`, every state receives a `to_<state>()` trigger that can move to that target from any currently known state. Disabling `auto_transitions` suppresses these automatic triggers and their `may_to_<state>` helpers.

Each trigger can be invoked either through the bound model method or through `model.trigger("name", *args, **kwargs)`. `machine.dispatch("name", *args, **kwargs)` calls the named trigger on all registered models and returns the logical AND of their results.

`get_triggers(*states)` returns trigger names that have transitions from any of the supplied source states. `get_transitions(trigger="", source="*", dest="*")` returns transition objects matching the optional trigger/source/destination filters. `remove_transition(trigger, source="*", dest="*")` removes matching transitions; when no transitions remain for a trigger, the trigger method is removed from registered models and the event is removed from the machine.

`add_ordered_transitions` creates a linear sequence over the supplied states, or over all registered states when `states=None`. By default it creates a loop from the last state back to the first. With `loop=False`, that last transition is omitted. Callback/condition arguments can be a single value applied to every generated transition or a list whose length matches the number of generated transitions. Ordering is rotated so the machine's initial state is first when the initial state is present in the ordered state list.

### Conditions, Callbacks, and EventData

`conditions` are predicates that must all return `True`. `unless` predicates are inverted and must all return `False`. Conditions run after `prepare_event` and transition `prepare` callbacks, before state-change callbacks. Failed conditions return `False` without changing state and without running before/exit/enter/after callbacks.

Callback references may be callables, model method names, model properties/attributes, or dotted module function paths. Non-callable model attributes are wrapped as zero-argument predicates. Lists and tuples of callbacks are executed in the order provided.

The callback order for a successful external transition is:

```text
machine.prepare_event
transition.prepare
transition.conditions and transition.unless
machine.before_state_change
transition.before
source_state.on_exit
state value update
destination_state.on_enter
transition.after
machine.on_final, when the destination state is final
machine.after_state_change
machine.finalize_event
```

For internal transitions, `source_state.on_exit`, state value update, `destination_state.on_enter`, and final-state callbacks are skipped, but transition and machine callbacks still run. `after_state_change` still runs after internal transitions.

If a callback raises before the state value is updated, the transition stops and no rollback is needed. If an exception is raised after the state value has changed, the state change persists. If `on_exception` callbacks are configured, the exception is attached to `event_data.error` and handled there; otherwise it is re-raised. `finalize_event` callbacks run after every trigger attempt, including failed conditions, invalid transitions that are represented as an event attempt, and exceptions, unless a finalizing callback itself raises.

`may_<trigger>(*args, **kwargs)` and `may_trigger(trigger, *args, **kwargs)` check whether a transition could currently run. These checks execute `prepare_event`, transition `prepare`, and condition checks for matching transitions, skip matches whose destination state is not yet registered, and return `True` only if a match can pass.

### Queued Transitions

Without queuing, a trigger called inside a callback is processed immediately, even before the outer transition reaches its `after` callbacks. With `queued=True`, nested trigger calls are queued until the currently running transition finishes, so outer `after` and finalization behavior complete before queued events are processed.

In queued mode, trigger calls return `True` when the event is accepted into the queue. This is true even if the queued transition later fails conditions. If an exception escapes while processing queued events, the queue is cleared and the exception behavior follows the machine's normal `on_exception`/raise rules.

Attempting to process a non-queued event synchronously while another transition is already in the internal queue raises `MachineError`.

### Multiple Models and Custom State Attributes

A single machine can manage multiple models. Each model has an independent value in the configured model attribute, but all models share the machine's state and transition definitions. Adding states or transitions after models are registered decorates all current models. `dispatch` applies one trigger to all current models.

Multiple machines can be attached to the same model by using different `model_attribute` values. Each machine's state helpers and automatic transitions include the model attribute in their method names so that the helpers do not collide.

### Hierarchical and Parallel Machines

`HierarchicalMachine` uses `NestedState` behavior for hierarchical state trees. A standard `State` object cannot be added as a nested state; nested machines require `NestedState` or subclasses. Nested states can be defined with dictionaries containing `name`, `children`, `states`, `initial`, `parallel`, `transitions`, `final`, and `on_final`. If both `children` and `states` are present, `children` is used.

The default nested separator is `NestedState.separator == "_"`. A substate named `bar` under `foo` is addressed as `foo_bar`, and deeper states concatenate the same way. With the default separator, nested state names must not contain underscores because the library cannot distinguish an underscore in a flat name from the parent/child separator.

Changing `NestedState.separator` changes helper behavior. With a non-underscore separator, nested automatic transition and check helpers are represented by callable attribute chains such as `to_C.s3.a()` and `is_C.s3.a()`. Substate path segments beginning with digits receive an `s` prefix in helper attributes. The direct `to("C<sep>3<sep>a")` helper remains available for non-interactive state targeting. Dynamic callback registration uses `machine.on_enter(state_name, callback)` and `machine.on_exit(state_name, callback)` when separator-based method names are unsuitable.

When a nested state with an `initial` child is entered by name, the machine recursively enters its initial child until a leaf without an initial child is reached. Passing an initial list represents parallel active states and is used as-is without recursive initial resolution. A model's hierarchical state is a string for a single active branch and a list of strings for parallel active branches.

Entering a substate enters parent states before child states. Exiting a substate exits children before parents. If a trigger is not known in the current nested state, it is delegated to parent states. More deeply nested transitions are considered before parent transitions. Wildcard transitions in a hierarchical machine apply to root states unless a more specific nested form is used.

`parallel` is shorthand for a state whose children are all active at the same time; each parallel child should define its direct initial state. Local `transitions` inside a nested state are valid only in that local scope. When a parent exits, all active children are exited.

`is_<state>(allow_substates=True)` returns `True` when the model is in a substate of the requested state. With `allow_substates=False`, it only returns `True` for an exact active state. `get_nested_state_names`, `get_nested_triggers`, `get_nested_transitions`, `get_global_name`, and hierarchical `get_transitions(..., delegate=True)` expose the nested public view.

HSM final callbacks fire when a final leaf state is entered, or when every child in a compound/parallel state is final and at least one child has just become final. Child `on_final` callbacks fire before parent and machine `on_final` callbacks.

Previously created `HierarchicalMachine` instances may be reused as children. Reused `(Nested)State`, events, and transitions are referenced, so later changes to one reused machine's state/event collection can be visible through another machine that shares those objects. Models and current model state are not shared. Using `remap` copies events/transitions that must be rewritten and removes remapped child states from the embedded machine view. Passing `initial=False` for a reused child machine keeps entry at the parent state rather than entering the reused machine's initial child.

### Async Machines

`AsyncMachine` and `HierarchicalAsyncMachine` mirror the core and hierarchical APIs but their trigger methods, `dispatch`, and `may_*` checks must be awaited. Callback lists may mix synchronous and asynchronous callables. Awaitable callback results are awaited; synchronous callbacks run normally and may block the event loop if they perform blocking work.

Async conditions are evaluated concurrently within the condition group. Async callbacks in the same callback phase are gathered concurrently and complete before the next phase begins. Event queue modes are `False`, `True`, and `"model"`. With `queued=True`, one global queue serializes events. With `queued="model"`, events for the same model are serialized while events for different models can progress independently; an exception clears only the queue for the model that raised it.

Async processing uses context variables to isolate running transitions. New events that reach the `before` phase or later can cancel already running tasks for the same model. `prepare` and condition checks are not treated as ongoing transitions for cancellation purposes; once conditions pass, the transition proceeds even if another event has already happened. Queue mode is a construction-time choice and should not be changed after initialization.

`AsyncTimeout` is an async state feature. On entry, it creates an asyncio task that sleeps for `timeout` seconds and then processes `on_timeout` callbacks. Exiting the state cancels the pending task. Timeout callback errors are passed through async `on_exception` callbacks when configured.

### Locked Machines

`LockedMachine` synchronizes public machine method access and model-bound event trigger access with reentrant context managers. By default it creates a picklable lock. User-provided `machine_context` values are entered for machine methods and event triggers. `add_model(..., model_context=...)` appends per-model contexts for that model's triggers.

Locks protect machine methods and bound trigger execution. They do not protect arbitrary direct mutation of model attributes, state objects, or machine internals by user code. User-provided context managers must be reentrant because the machine can enter them multiple times during a single trigger.

Locked machines can be pickled. Lock objects and model context maps are restored in a usable form after unpickling.

### Graphs, Mermaid, Graphviz, and Markup

`GraphMachine` extends `MarkupMachine` and binds `get_graph(title=None, force_new=False, show_roi=False)` to each model. If the machine itself is the model, `machine.get_graph` returns a graph for the first model. Adding states, adding transitions, removing transitions, and successful transitions refresh or restyle graph projections.

The graph backend selection order for `graph_engine="pygraphviz"` is pygraphviz first, graphviz second, mermaid fallback. Passing `graph_engine="graphviz"` skips pygraphviz and falls back to mermaid if graphviz is unavailable. Passing `graph_engine="mermaid"` uses mermaid directly. `use_pygraphviz=False` is accepted for compatibility and selects graphviz behavior.

The graph object exposes `draw(filename, format=None, prog="dot", args="")`. For graphviz backends, drawing to a file path writes an image file and returns `None`; drawing to `None` or a file-like object requires a `format` and returns/writes bytes. For the mermaid backend, drawing to `None` returns a mermaid state diagram string; drawing to a path writes text; drawing to a stream writes encoded text.

`show_conditions=True` includes condition and unless labels on transition edges. `show_auto_transitions=True` includes automatic `to_*` transitions in the graph/markup. `show_state_attributes=True` includes supported state attributes such as callbacks, tags, and timeouts in labels. `show_roi=True` returns a region-of-interest projection containing active states, reachable states, and the previous transition styling.

`GraphMachine.format_references` controls how callable callback/condition references are represented in diagrams and markup. Returning `None` omits the reference. Callback partials are represented as callable names plus their bound arguments when possible.

`MarkupMachine.markup` returns a dictionary representation containing states, transitions, machine callback lists, model metadata, `model_attribute`, `model_override`, `send_event`, `auto_transitions`, `ignore_invalid_triggers`, and `queued`. The `models` entry is refreshed whenever `markup` is accessed. `get_markup_config()` returns the machine configuration without re-adding model entries. Passing `markup=<dict>` to `MarkupMachine` reconstructs the machine from the dictionary and then reconstructs listed models by importing their recorded classes; a model class name of `"self"` reuses the machine as its own model.

Graph machines omit graph cache objects during pickling and recreate model graphs after unpickling when possible.

### State Feature Mixins

`add_state_features` decorates a machine class by building a custom `state_cls` from the supplied mixins and the machine's existing state class. Dynamic callback names contributed by mixins are collected so helper methods can be resolved. Dynamically generated state classes are not picklable; use a dedicated state class when pickling decorated machines is required.

`Tags` accepts `tags` and exposes `state.is_<tag>` boolean attributes. Missing tags return `False`.

`Timeout` accepts `timeout` and `on_timeout`. When `timeout > 0`, `on_timeout` is required. Entering the state starts a per-model daemon timer; exiting the state cancels that model's timer. When the timer fires, `on_timeout` callbacks run through the machine's callback resolution. Timeout callbacks run in a thread.

`Error` builds on `Tags`. `accepted=True` adds the `accepted` tag. Entering an Error state raises `MachineError` when the state has no leaving triggers and is not accepted. This feature is most meaningful when automatic transitions are disabled, because automatic transitions otherwise provide leaving triggers.

`Volatile` accepts `volatile` and `hook`. Entering the state creates a new instance of the `volatile` class, or `VolatileObject` when omitted, and assigns it to `model.<hook>`; exiting the state deletes that model attribute if present.

`Retry` accepts `retries` and `on_failure`. The first entry from a different source is not counted as a retry. Self re-entries increment a per-model counter. When the retry limit is exceeded, the state is not entered normally and `on_failure` is called instead. If `retries > 0`, `on_failure` is required.

### Factory and Feature Combinations

`MachineFactory.get_predefined` returns a machine class for supported combinations of four booleans: `graph`, `nested`, `locked`, and `asyncio`.

Supported combinations are:

```text
Machine
GraphMachine
HierarchicalMachine
LockedMachine
HierarchicalGraphMachine
LockedGraphMachine
LockedHierarchicalMachine
LockedHierarchicalGraphMachine
AsyncMachine
AsyncGraphMachine
HierarchicalAsyncMachine
HierarchicalAsyncGraphMachine
```

Locked async combinations are not supported by the predefined factory. Asking for an unsupported combination raises an error.

### Typing and Model Definition Utilities

`generate_base_model(config)` returns Python source code for an abstract `BaseModel` matching the machine configuration. It emits the configured model attribute, `trigger`, trigger methods, `may_*` methods, state check methods, automatic transition methods when enabled, and abstract callback methods inferred from machine and transition callback lists. With `send_event=True`, generated callbacks accept `event_data`; otherwise they accept `*args, **kwargs`. A plain `Machine` instance is not accepted; machine instances must be `MarkupMachine` or `HierarchicalMarkupMachine` compatible.

`transition(...)` returns a transition configuration dictionary without a trigger name. `event(*configs)` creates a placeholder attribute for a model-defined trigger. `add_transitions(*configs)` decorates a model method or placeholder with transition configs. `with_model_definitions` decorates a `Machine` subclass so that, when models are added, placeholder definitions found on the model class are added as machine transitions and `model_override` is enabled. Calling an unresolved placeholder directly before proper machine initialization raises an error.

### Restoring, Pickling, and Logging

Core machines are picklable and preserve states, transitions, models, and current state values across pickle round trips. Graph machines rebuild graph caches after unpickling. Locked machines rebuild usable lock/context mappings after unpickling. Decorated machines produced by `add_state_features` are not picklable because their generated custom state class is dynamic.

The library logs state changes, transition triggers, condition checks, graph backend fallback, and callback processing through the standard `logging` package under `transitions` module loggers. Logging content is informational and not a stable API surface.

## Error Semantics

- `MachineError` is raised when a known trigger is fired from a state for which no matching transition exists and invalid triggers are not ignored.
- Unknown trigger names passed to `model.trigger(name)` raise `AttributeError` when invalid triggers are not ignored. If invalid triggers are ignored for the current state or machine, unknown trigger names return `False`.
- If `ignore_invalid_triggers=True` is set on the current state, it takes precedence for that state. Otherwise the machine-level `ignore_invalid_triggers` setting is used.
- `get_state` raises `ValueError` for unregistered states.
- `add_model` raises `ValueError` when no initial state is configured and none is supplied.
- `add_transition` raises `ValueError` when the trigger name equals the machine's `model_attribute`.
- `add_ordered_transitions` raises `ValueError` with fewer than two states, or when a callback/condition argument list length is neither one nor the number of generated transitions.
- Callback resolution raises `AttributeError` when a string cannot be found on the model and cannot be imported as a dotted module function.
- Without `on_exception`, exceptions raised by callbacks, conditions, or state feature behavior are re-raised. With `on_exception`, the exception is assigned to `event_data.error` and the configured handlers run.
- `Timeout` and `AsyncTimeout` raise `AttributeError` when `timeout > 0` and no `on_timeout` callback is provided.
- `Retry` raises `AttributeError` when `retries > 0` and no `on_failure` callback is provided.
- `Error` raises `MachineError` when a non-accepted terminal error state is entered.
- `HierarchicalMachine` raises `ValueError` when a standard `State` object is added instead of a `NestedState`, when a duplicate nested state is added, when a state path cannot be resolved, or when an enum state name contains the active nested separator.
- In a hierarchical machine, a known trigger that cannot run from the current active state raises `MachineError`; an unknown trigger raises `AttributeError`, unless invalid triggers are ignored.
- `to(state_name)` on a hierarchical model raises `MachineError` when called from a parallel state.
- `GraphMachine.add_model` raises `AttributeError` when the model already has a `get_graph` attribute.
- Graphviz-backed `draw(None, format=None)` or stream drawing without `format` raises `ValueError`.
- `MachineFactory.get_predefined` raises `ValueError` for unsupported feature combinations.
- `generate_base_model` raises `ValueError` when passed a machine instance that is not markup-capable.
- Async triggers must be awaited. Directly using synchronous processing internals on an `AsyncMachine` raises `RuntimeError`.

## Cross-View Invariants

1. A model's stored state value, its `is_*` helpers, `machine.get_model_state(model)`, and `machine.get_state(model.<model_attribute>)` describe the same active state.
2. For enum states, the model stores enum members, `State.value` preserves the enum member, and helper/lookup names use the enum member's `name`.
3. Every transition added to a machine is visible through its event trigger, matching model helper method, `may_<trigger>` helper, `get_triggers`, and `get_transitions` filters until it is removed.
4. `model.trigger(name, *args, **kwargs)` and the bound `model.<name>(*args, **kwargs)` follow the same transition selection, callback execution, return-value, and exception behavior.
5. In queued mode, the state sequence observed after all queued events complete is the same as processing those accepted events sequentially after the outer transition finishes, even though each queued trigger initially returns `True`.
6. The callback view and `EventData` view agree: callbacks for one trigger attempt receive the same model, machine, event, source state, active transition, arguments, result, and error information for that attempt.
7. With multiple models, state definitions, transition definitions, graph/markup definitions, and trigger methods are shared, while each model's current state value remains independent.
8. With a custom `model_attribute`, all state storage and generated `is_*/to_*` helpers are namespaced by that attribute and do not change the default `state` attribute unless another machine owns it.
9. In hierarchical machines, a nested state path, `get_nested_state_names`, parent/substate `is_*` checks, and the model's string or list state value all represent the same active tree.
10. In parallel HSM states, the model state list, graph/markup active state projection, and final-state detection all refer to the same set of active child branches.
11. Graph and markup projections reflect public machine definitions after state/transition mutations; graph layout details may differ by backend, but visible states, triggers, labels, active state, previous transition, and auto-transition inclusion settings remain consistent.
12. Pickling and unpickling preserve public machine behavior: triggers, state values, callbacks by reference/name, and model registration continue to work, while backend caches and locks may be regenerated.

## Representative Workflow(s)

### Core Model Workflow

```python
from transitions import Machine, State

class Matter:
    def __init__(self):
        self.log = []

    def heat_up(self, event):
        self.log.append(("prepare", event.kwargs["temp"]))

    def hot_enough(self, event):
        return event.kwargs["temp"] >= 100

    def entered_liquid(self, event):
        self.log.append(("entered", event.state.name))

states = [
    State("solid"),
    {"name": "liquid", "on_enter": "entered_liquid"},
    {"name": "gas", "final": True},
]
transitions = [
    {"trigger": "melt", "source": "solid", "dest": "liquid",
     "prepare": "heat_up", "conditions": "hot_enough"},
    ["evaporate", "liquid", "gas"],
]

model = Matter()
machine = Machine(
    model,
    states=states,
    transitions=transitions,
    initial="solid",
    send_event=True,
    on_final=lambda event: event.model.log.append(("final", event.state.name)),
)

assert model.state == "solid"
assert model.may_melt(temp=50) is False
assert model.melt(temp=100) is True
assert model.is_liquid()
assert model.trigger("evaporate") is True
assert model.state == "gas"
assert model.log == [("prepare", 50), ("prepare", 100), ("entered", "liquid"), ("final", "gas")]
```

### Hierarchical Graph Workflow

```python
from transitions.extensions.diagrams import HierarchicalGraphMachine

states = [
    "idle",
    {"name": "work", "parallel": [
        {"name": "left", "children": ["start", {"name": "done", "final": True}], "initial": "start"},
        {"name": "right", "children": ["start", {"name": "done", "final": True}], "initial": "start"},
    ]},
    "finished",
]
transitions = [
    ["begin", "idle", "work"],
    ["finish_left", "work_left_start", "work_left_done"],
    ["finish_right", "work_right_start", "work_right_done"],
    ["reset", "work", "idle"],
]

machine = HierarchicalGraphMachine(
    states=states,
    transitions=transitions,
    initial="idle",
    graph_engine="mermaid",
    auto_transitions=False,
)

machine.begin()
assert machine.state == ["work_left_start", "work_right_start"]
assert machine.is_work(allow_substates=True)
source = machine.get_graph(show_roi=True).draw(None)
assert "stateDiagram-v2" in source
```

## Non-Goals

- Exact memory addresses, `repr` strings, log wording, warning wording, and private attribute names are not stable API requirements.
- Private helpers and support classes whose names start with an underscore are not part of the required public contract.
- Backend-specific graph layout, indentation, color values, DOT/Mermaid line ordering, and snapshot text are not required beyond the semantic graph behavior described above.
- Installing external system packages such as Graphviz, pygraphviz build tooling, notebook tooling, or Django integration is outside the core library contract.
- The library does not promise to protect arbitrary user mutation of model attributes, machine attributes, state objects, or transition objects.
- The library does not provide a CLI.
- Python packaging metadata, release badges, local development test layout, and development workflow files are not part of the runtime API.

## Evaluation Notes

Implementations are evaluated through public behavior: importability of documented public names, model decoration, transition execution, callback order, error handling, queues, enum behavior, multiple models, hierarchical and parallel machines, async/locked variants, graph/markup projections, state feature mixins, factory combinations, experimental typing helpers, and serialization/restoration.

Optional graph backends are evaluated by their public fallback and draw semantics rather than by requiring a particular external renderer to be installed. Diagram and markup checks focus on represented states, transitions, labels, active/previous state semantics, and configuration switches, not on exact backend formatting.

Scoring should reward observable API compatibility and cross-view consistency. Tests should avoid depending on private helpers, exact object identities after serialization, exact logging text, generated graph snapshot formatting, or example-specific object shapes that are not part of the public API.
