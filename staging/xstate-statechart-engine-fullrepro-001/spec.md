# xstate Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`xstate` is a statechart engine for JavaScript and TypeScript. A caller defines a machine — a tree of states with transitions, guards, actions, and an extended-state object called context — and the engine interprets it: it resolves the initial configuration, selects transitions for incoming events according to statechart semantics (deepest handler first, document order, guard evaluation), computes exit and entry sets, applies context updates, processes internally raised events to a stable configuration, and reports each step as an immutable snapshot.

One machine definition projects into several public views: a running actor that receives events and exposes snapshots; pure step functions that compute initial and successor snapshots with no actor lifecycle and no side effects; a snapshot query surface (`matches`, `can`, `hasTag`); a persistence form that can be captured from a live actor and used to resume a new one; a deterministic timed view in which delayed transitions are driven by an externally controlled clock; and a completion view in which final states produce a status, an output value, and a promise.

The installable package name is `xstate`. All functionality is reachable through named exports of the package root.

## Non-Goals

- This specification does not require invoked or spawned child actors, nor actor logic creators for promises, callbacks, observables, or transition functions.
- This specification does not define inter-actor messaging (`sendTo`, `sendParent`, `forwardTo`, `emit`) or actor systems and inspection.
- This specification does not define the behavior of actions that throw, nor error-status propagation from user code.
- This specification does not require built-in actions other than `assign` and `raise`, and does not define `log`, `cancel`, `stopChild`, or `spawnChild`.
- This specification does not require real-timer scheduling. Delayed transitions are defined only relative to the clock supplied to the actor; wall-clock behavior is unobserved.
- This specification does not define deprecated aliases from earlier major versions, graph utilities, or state-node introspection beyond the snapshot surface described here.
- This specification does not require a command-line interface.

## Representative Workflows

A machine is defined once and interpreted by an actor; snapshots answer queries about the current configuration.

```ts
import { createMachine, createActor, assign } from 'xstate'

const brewer = createMachine({
  id: 'brewer',
  initial: 'idle',
  context: { fills: 0 },
  states: {
    idle: { on: { INSERT: 'selecting' } },
    selecting: {
      tags: ['interactive'],
      on: {
        PICK: {
          guard: ({ event }) => event.slot >= 1,
          target: 'pouring',
          actions: assign({ fills: ({ context }) => context.fills + 1 }),
        },
        EJECT: 'idle',
      },
    },
    pouring: { on: { DONE_POUR: 'idle' } },
  },
})

const actor = createActor(brewer).start()
actor.getSnapshot().value            // 'idle'
actor.send({ type: 'INSERT' })
actor.getSnapshot().hasTag('interactive')  // true
actor.send({ type: 'PICK', slot: 2 })
actor.getSnapshot().value            // 'pouring'
actor.getSnapshot().context          // { fills: 1 }
actor.getSnapshot().can({ type: 'DONE_POUR' })  // true
```

The same definition steps purely — no actor, no side effects — and persists across actor instances:

```ts
import { getInitialSnapshot, getNextSnapshot } from 'xstate'

const s0 = getInitialSnapshot(brewer)
const s1 = getNextSnapshot(brewer, s0, { type: 'INSERT' })
s1.value   // 'selecting'; s0 is unchanged

const running = createActor(brewer).start()
running.send({ type: 'INSERT' })
const saved = running.getPersistedSnapshot()
running.stop()

const resumed = createActor(brewer, { snapshot: saved }).start()
resumed.getSnapshot().value  // 'selecting'
```

## Machine Definitions

A machine definition is a declarative statechart configuration validated when the machine is created.

**Configuration shape.** `createMachine` accepts a configuration object with: an optional `id` naming the root; `initial`, the key of the starting child state; `context`, either a plain object or a factory function receiving `{ input }` and returning the initial context; `states`, a mapping of state keys to state definitions; machine-level `on` transitions, `entry` and `exit` actions, and an optional `output` mapper used when the machine completes. Each state definition accepts `on` (event transitions), `entry`/`exit` actions, `initial` and `states` for compound states, `type` (`'parallel'`, `'final'`, or `'history'`), `tags` (a string array), `after` (delayed transitions), `always` (eventless transitions), `onDone`, and `output` on final states. A second argument to `createMachine` supplies named implementations (`actions`, `guards`), and `setup({ actions, guards })` returns an object whose `createMachine` builds machines that resolve those named implementations. An existing machine's `provide` method returns a new machine with the given implementations overriding the originals.

**State identity.** Every state node has an id: the machine `id` (or a generated root id) joined with the dot-separated path of state keys. Transition targets reference states by sibling key, by relative child key prefixed with a dot, or by absolute id prefixed with `#` (for example `#brewer.idle`).

**Definition-time validation.** WHEN a transition target names a state that does not exist, THEN `createMachine` must throw an `Error` identifying the invalid transition. WHEN a compound state (including the root) declares child `states` but no `initial` key, THEN `createMachine` must throw an `Error` whose message names the state node missing the initial state.

## Actors And Snapshots

An actor interprets one machine instance: it holds the current snapshot, receives events, and exposes the observation surface.

**Lifecycle.** `createActor(machine)` builds an actor; an options object accepts `input` (passed to the context factory), `snapshot` (a persisted snapshot to resume from), and `clock` (the timer source for delayed transitions). `start()` enters the initial configuration, running entry actions from the outermost node inward, and returns the actor. `send(event)` processes one event object synchronously; an event is a plain object with a string `type` and any additional payload properties, and guards and actions read the payload from the `event` argument. `stop()` halts the actor: the snapshot `status` becomes `'stopped'` and subsequently sent events must not change the snapshot. Events whose type matches no transition in the current configuration are ignored without error.

**Snapshots.** `getSnapshot()` returns the current snapshot, a new value per step with: `value`, the configuration in collapsed form (a bare string for a top-level leaf state, a nested object for compound states, an object keyed by region for parallel states, collapsing again to a string at each leaf); `context`, the current extended state; `status`, one of `'active'`, `'done'`, or `'stopped'`; and `output`, defined once the machine completes. Three query methods answer without mutating: `matches(value)` tests whether the current configuration is or refines the given full or partial state value; `can(event)` returns whether sending the event would select any transition (guards evaluated against the current snapshot); `hasTag(tag)` returns whether any active state declares the tag. The standalone `matchesState(parentValue, childValue)` helper applies the same refinement test to two plain state values.

**Input.** WHEN `context` is a factory function, THEN the actor must build the initial context by calling it with the `input` supplied in actor options; the factory form is required for input-dependent context.

## Transition Selection

Event processing selects at most one transition per state level according to fixed rules, then applies it as an exit/action/entry sequence.

**Descriptor matching.** A state's `on` mapping is keyed by event descriptors. An exact descriptor matches its event type. A partial wildcard descriptor of the form `prefix.*` matches every event whose type begins with `prefix.`. The bare wildcard `*` matches any event. WHEN several descriptors in the same state match one event, THEN the most specific descriptor wins: exact over partial wildcard over `*`.

**Candidate order and depth.** A descriptor's value is one transition or an array of candidates; candidates are evaluated in document order and the first whose guard passes is taken. WHEN a guarded candidate fails, THEN evaluation falls through to the next candidate in the same array. Deeper states take precedence: WHEN both an active child and its ancestor define a transition for the same event, THEN the child's transition must be selected and the ancestor's ignored; the ancestor's transition applies only when no descendant handles the event.

**Targets.** A string target names a sibling state; a target starting with `.` names a child of the transition's source; a target starting with `#` is an absolute id reference followed by optional dot-separated descendants. A transition without a target executes its actions and leaves the configuration unchanged. A self-targeting transition must not exit and re-enter its source by default; `reenter: true` forces the exit and re-entry, re-running exit and entry actions and re-resolving initial states.

**Eventless and raised events.** `always` transitions are evaluated whenever a state of the configuration is entered or a step completes, before any further external event; their candidates follow the same guard and document-order rules. The `raise(event)` action enqueues an internal event that is processed to completion before the actor accepts the next external event.

## Actions And Context

Actions run in a fixed order around a transition, and `assign` is the only way context changes.

**Execution order.** For a transition from one state to another, the engine must run: exit actions of exited states (deepest exited state first), then the transition's own `actions`, then entry actions of entered states (outermost entered state first). On `start()`, entry actions run from the machine node inward to the initial leaf. Action functions receive an object with `context` and `event` among its properties; named actions declared as `{ type, params }` receive their resolved `params` as a second argument.

**Assign.** `assign` takes an object whose keys map to either plain values or updater functions receiving `{ context, event }`, or a single function returning a partial context. Multiple `assign` actions in one step apply in listed order, each seeing the previous one's result. Context updates become visible immediately to subsequent actions in the same step: an `assign` in an exit action is visible to the transition's actions and to entry actions of the same step. Snapshot context values are replaced, never merged deeply — each assigned key overwrites.

**Raise.** The `raise` action enqueues the given event object as an internal event for the same actor; its payload properties are visible to the guards and actions of the transition it triggers.

## Guards

Guards decide transition eligibility and never mutate state.

**Forms.** A guard is either an inline predicate receiving an object with `context` and `event`, a named guard referenced by string, or a named guard with parameters referenced as `{ type, params }` whose implementation receives the resolved `params` as a second argument. Named implementations come from the second argument of `createMachine`, from `setup`, or from `provide`.

**Combinators.** `and([...])` passes when every member guard passes; `or([...])` passes when at least one member passes; `not(guard)` inverts a guard. `stateIn(value)` passes when the current configuration matches the given state value or `#id` string; it is the supported way to make one parallel region's transitions conditional on another region's state.

**Observability.** WHEN a transition's guard returns false and no later candidate passes, THEN the event must leave the snapshot unchanged. `can(event)` must return true exactly when at least one transition candidate for the event has a passing guard, and false when all candidates are guarded off or no descriptor matches.

## Hierarchy, Parallel And History

The configuration is a tree; compound, parallel, and history nodes shape how it is entered, represented, and restored.

**Compound states.** Entering a compound state enters its `initial` child recursively down to leaves. The snapshot `value` for a compound state is an object keyed by the state name whose value is the child's collapsed form (`{ outer: 'one' }`, or `'other'` once a top-level leaf is active). `matches` accepts partial values: an active `{ outer: { deep: 'leaf' } }` configuration matches `'outer'`, `{ outer: 'deep' }`... exactly when each given segment lies on the active path.

**Parallel states.** A state with `type: 'parallel'` activates all of its child regions simultaneously; its value is an object with one key per region. Events are offered to every region; each region selects independently. WHEN a region reaches a final child, THEN that region's value keeps the final state's key while other regions continue.

**History states.** A child with `type: 'history'` is a history pseudo-state. Targeting it re-enters the parent at its remembered configuration: with the default shallow history, the remembered immediate child is entered and descends through that child's own `initial` defaults; with `history: 'deep'`, the full remembered leaf configuration is restored. The remembered configuration updates every time the parent exits. WHEN the parent has never been exited with stored history, THEN targeting the history state enters the parent's default initial path.

## Final States And Output

Final states terminate regions, complete machines, and carry output values.

**Completion.** WHEN a top-level final state is entered, THEN the snapshot `status` becomes `'done'` and further events must not change the snapshot. WHEN every region of a parallel state has reached a final child, THEN the parallel state is done and its `onDone` transition fires. WHEN a compound state's active child is a final state, THEN the compound state's `onDone` transition fires in the same step.

**Output values.** A final state's `output` mapper (receiving `{ context, event }`) computes a value attached to the completion event: the `onDone` transition of the parent observes it as `event.output`. The machine-level `output` mapper computes the snapshot's `output` when the machine completes, receiving the completion event — so a root final state's `output` value is visible to the machine mapper as `event.output`. WHEN the machine has no top-level `output` mapper, THEN the completed snapshot's `output` is `undefined`.

**Promise view.** `toPromise(actor)` returns a promise that resolves with the snapshot `output` when the actor's machine completes. The promise resolves after completion regardless of whether it was created before or after the final event.

## Timed Transitions

Delayed transitions arm timers on state entry and fire through the actor's clock.

**After.** A state's `after` mapping is keyed by delay in milliseconds; each value is a transition (or candidate array) taken when the state has remained active for that long. The timer arms when the state is entered, must be cancelled when the state is exited before expiry, and re-arms on re-entry.

**Clock.** The actor options accept a `clock` with `setTimeout`/`clearTimeout` semantics. `SimulatedClock` is an exported deterministic clock: its `increment(ms)` method advances simulated time, firing every already-armed timer whose deadline falls within the advanced window in deadline order. Timers armed while an increment is being processed measure their delay from the already-advanced time, so one large increment advances a chain of delayed states by at most one step. With a `SimulatedClock`, delayed behavior is fully synchronous and reproducible: advancing to the threshold (across one or several increments) fires the transition; advancing to just before it does not.

## Pure Stepping And Persistence

The interpretation semantics are available without an actor, and actor state is portable across instances.

**Pure step functions.** `getInitialSnapshot(machine, input?)` returns the initial snapshot: the resolved initial configuration with entry-time `assign` updates applied. `getNextSnapshot(machine, snapshot, event)` returns the successor snapshot for one event under the same selection, guard, assign, eventless, and raised-event rules as an actor step. Both functions must be pure with respect to observable effects: they must not run side-effecting action functions and must not mutate the given snapshot — the input snapshot compares unchanged after the call. WHEN the given snapshot's status is `'done'`, THEN `getNextSnapshot` returns a snapshot that is still done with the same value.

**Persistence.** `getPersistedSnapshot()` on an actor returns a plain serializable object capturing at least the configuration value, context, and status. `createActor(machine, { snapshot })` resumes from a persisted snapshot: the restored actor's first snapshot reports the persisted value and context, and subsequent events transition exactly as if the original actor had continued.

## State Model

The core state is the machine definition (immutable after `createMachine`) plus, per actor, the current snapshot: configuration value, context, status, and armed timers. Snapshots are immutable values; every step produces a new snapshot.

Public projections of one machine definition:

1. **Actor interpretation** — `createActor`/`start`/`send`/`stop` with `getSnapshot()`.
2. **Pure stepping** — `getInitialSnapshot`/`getNextSnapshot` with no lifecycle and no side effects.
3. **Query surface** — `matches`, `can`, `hasTag` on snapshots, and `matchesState` on plain values.
4. **Persistence** — `getPersistedSnapshot` and resumption via the `snapshot` actor option.
5. **Timed view** — `after` transitions driven deterministically through `SimulatedClock`.
6. **Completion view** — `status`, `output`, `onDone` events, and `toPromise`.

## Error Semantics

| Condition | Outcome |
|---|---|
| `createMachine` configuration contains a transition target naming a nonexistent state | `createMachine` throws an `Error` identifying the invalid transition |
| `createMachine` configuration has a compound state with child `states` but no `initial` | `createMachine` throws an `Error` naming the state node missing an initial state |

Runtime event processing is total for the surface described here: unknown event types, guarded-off events, events after `stop()`, and events after completion are ignored without throwing.

## Cross-View Invariants

1. For any machine and event sequence, driving an actor with `send` and folding the same events with `getNextSnapshot` from `getInitialSnapshot` must produce the same `value` and `context` at every step.
2. `can(event)` must return true exactly when sending that event would change the snapshot or execute transition actions — a false `can` implies `send` of that event leaves `value` and `context` unchanged.
3. `matches(v)` on a snapshot must agree with `matchesState(v, snapshot.value)` for every state value `v`.
4. A persisted-and-resumed actor must be observationally equivalent to the original: same `value`, `context`, and `status` at resumption, and the same responses to subsequent events.
5. Under a `SimulatedClock`, a delayed transition must fire exactly when accumulated increments reach its delay while the armed state stayed active — exiting the state before the threshold and re-entering restarts the delay from zero.
6. Once `status` is `'done'`, the snapshot is frozen for every projection: further `send` calls, pure steps from the done snapshot, and query methods must all report the same terminal `value`, and `toPromise` resolves with exactly the snapshot's `output`.

## Public Interface

### Import Surface

```ts
import {
  createMachine,
  setup,
  createActor,
  getInitialSnapshot,
  getNextSnapshot,
  assign,
  raise,
  and,
  or,
  not,
  stateIn,
  matchesState,
  toPromise,
  SimulatedClock,
} from 'xstate'
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `createMachine` | function | Build a validated machine definition from a configuration object |
| `setup` | function | Bind named action/guard implementations, returning a `createMachine` factory |
| `createActor` | function | Build an actor for a machine, with `input`, `snapshot`, and `clock` options |
| `getInitialSnapshot` | function | Pure initial snapshot of a machine |
| `getNextSnapshot` | function | Pure successor snapshot for one event |
| `assign` | function | Action creator for context updates |
| `raise` | function | Action creator enqueueing an internal event |
| `and` | function | Guard combinator: all members pass |
| `or` | function | Guard combinator: any member passes |
| `not` | function | Guard combinator: inversion |
| `stateIn` | function | Guard passing when the configuration matches a state value or id |
| `matchesState` | function | Test whether one state value refines another |
| `toPromise` | function | Promise of the actor's output at completion |
| `SimulatedClock` | class | Deterministic clock with `increment(ms)` for delayed transitions |

### CLI Entry Points

There is no console script for this package. Programmatic use is through the package's named exports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. Tests execute with `vitest` under TypeScript (`typescript`, `@types/node` available). No third-party runtime dependencies are required or available to the implementation at runtime; the package must function self-contained.

The project must be an installable npm package named `xstate` whose root entry point provides the named exports listed in Public Interface, resolvable by Node.js under both ESM `import` and TypeScript `NodeNext` resolution. The assessment environment provides the same runtime and module resolution.

## Appendix B: Assessment Notes

Assessment exercises the public API only, in three dimensions: (1) atomic behavior — machine definition and validation, actor lifecycle, snapshot fields and query methods, descriptor matching, target resolution, action ordering, assign and raise, guard forms and combinators, hierarchy/parallel/history value shapes, final-state completion, delayed transitions under a simulated clock, pure stepping, and persistence primitives; (2) integration — combinations that span projections, such as actor-versus-pure-step agreement over event sequences, guard-driven branching with context accumulated across microsteps, history restoration after timed exits, parallel completion driving `onDone`, and persistence round-trips that continue transitioning; (3) end-to-end workflows — full machine lifecycles from definition through interpretation, timed progression, persistence, resumption, and completion with output. Expected values are concrete snapshot values, context objects, and orderings computed from the rules in this document. Each test is assessed independently.
