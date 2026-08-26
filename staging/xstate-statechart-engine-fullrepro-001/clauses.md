# Clause IDs — xstate-statechart-engine-fullrepro-001

Sidecar mapping of clause IDs to spec statements (section anchors in parentheses).

## Machine Definitions (XSTA-DEF)

- XSTA-DEF-001: `createMachine` accepts a configuration with `id`, `initial`, `context` (object or `{ input }` factory), `states`, machine-level `on`/`entry`/`exit`, and an `output` mapper; state definitions accept `on`, `entry`/`exit`, `initial`/`states`, `type` (`parallel`/`final`/`history`), `tags`, `after`, `always`, `onDone`, and `output` on final states.
- XSTA-DEF-002: A second `createMachine` argument supplies named `actions`/`guards`; `setup({ actions, guards })` returns a bound `createMachine`; `machine.provide(impls)` returns a new machine with overriding implementations.
- XSTA-DEF-003: Every state node's id is the machine id joined with dot-separated state keys; targets reference sibling keys, dot-prefixed child keys, or `#id` absolute references.
- XSTA-DEF-004: WHEN a transition target names a nonexistent state, `createMachine` throws an `Error` identifying the invalid transition.
- XSTA-DEF-005: WHEN a compound state declares child `states` but no `initial`, `createMachine` throws an `Error` naming the node missing the initial state.

## Actors And Snapshots (XSTA-ACT)

- XSTA-ACT-001: `createActor(machine, options?)` accepts `input`, `snapshot`, `clock`; `start()` enters the initial configuration running entry actions outermost-first and returns the actor.
- XSTA-ACT-002: `send(event)` processes one plain event object (string `type` plus payload properties) synchronously; guards and actions read the payload from `event`.
- XSTA-ACT-003: `stop()` sets snapshot `status` to `'stopped'`; events sent afterwards must not change the snapshot.
- XSTA-ACT-004: Events whose type matches no transition in the current configuration are ignored without error.
- XSTA-ACT-005: Snapshots expose `value` (collapsed configuration: string leaf, nested objects, per-region object for parallel), `context`, `status` (`active`/`done`/`stopped`), and `output`.
- XSTA-ACT-006: `matches(value)` tests configuration refinement; `can(event)` reports whether any transition would be selected; `hasTag(tag)` reports whether an active state declares the tag; `matchesState(parent, child)` applies the refinement test to plain values.
- XSTA-ACT-007: WHEN `context` is a factory, the actor builds initial context by calling it with the options' `input`.

## Transition Selection (XSTA-TRN)

- XSTA-TRN-001: Descriptors match exactly, by `prefix.*` partial wildcard, or by bare `*`; the most specific matching descriptor wins.
- XSTA-TRN-002: Transition candidates in an array evaluate in document order; the first with a passing guard is taken; failing guards fall through.
- XSTA-TRN-003: WHEN an active child and its ancestor both handle an event, the child's transition is selected; the ancestor's applies only when no descendant handles it.
- XSTA-TRN-004: A string target names a sibling; `.child` names a child of the source; `#id[.path]` is absolute.
- XSTA-TRN-005: A targetless transition executes actions and leaves the configuration unchanged.
- XSTA-TRN-006: A self-targeting transition does not exit/re-enter by default; `reenter: true` forces exit and re-entry, re-running exit/entry actions and re-resolving initial states.
- XSTA-TRN-007: `always` transitions are evaluated on entry and after each step before further external events.
- XSTA-TRN-008: `raise(event)` enqueues an internal event processed to completion before the next external event.

## Actions And Context (XSTA-AXN)

- XSTA-AXN-001: Transition execution order is: exit actions (deepest first), transition actions, entry actions (outermost first).
- XSTA-AXN-002: Action functions receive `{ context, event, ... }`; named `{ type, params }` actions receive resolved `params` as a second argument.
- XSTA-AXN-003: `assign` accepts an object of values/updaters or a single function returning partial context; multiple assigns in a step apply in order, each seeing the previous result; updates are visible to later actions in the same step; assigned keys overwrite.
- XSTA-AXN-004: `raise` payload properties are visible to the guards and actions of the transition the internal event triggers.

## Guards (XSTA-GRD)

- XSTA-GRD-001: Guards are inline predicates over `{ context, event }`, named strings, or `{ type, params }` with the implementation receiving `params` second.
- XSTA-GRD-002: `and([...])`, `or([...])`, `not(g)` combine guards; `stateIn(value-or-#id)` passes when the configuration matches, enabling cross-region conditions in parallel states.
- XSTA-GRD-003: WHEN all candidates for an event are guarded off, the snapshot is unchanged; `can(event)` is true exactly when at least one candidate's guard passes.

## Hierarchy, Parallel And History (XSTA-HPH)

- XSTA-HPH-001: Entering a compound state enters its `initial` child recursively; the value form is `{ parent: childForm }`, collapsing to strings at leaves.
- XSTA-HPH-002: `matches` accepts partial values: a value matches when each given segment lies on the active path.
- XSTA-HPH-003: A `parallel` state activates all regions; its value has one key per region; events are offered to every region independently.
- XSTA-HPH-004: WHEN a region reaches a final child, that region's value keeps the final key while other regions continue.
- XSTA-HPH-005: Shallow history re-enters the remembered immediate child descending through its `initial` defaults; deep history restores the remembered leaf configuration; the memory updates on each parent exit; with no stored history the default initial path is entered.

## Final States And Output (XSTA-FIN)

- XSTA-FIN-001: Entering a top-level final state sets `status` to `'done'`; further events do not change the snapshot.
- XSTA-FIN-002: WHEN every region of a parallel state reaches a final child, the parallel state's `onDone` fires; WHEN a compound state's active child is final, its `onDone` fires in the same step.
- XSTA-FIN-003: A final state's `output` mapper computes the completion event's `output` observed by `onDone` as `event.output`.
- XSTA-FIN-004: The machine-level `output` mapper computes snapshot `output` at completion, receiving the completion event (a root final state's output is `event.output` there); without a machine-level mapper, completed `output` is `undefined`.
- XSTA-FIN-005: `toPromise(actor)` resolves with the snapshot `output` at completion, whether created before or after the final event.

## Timed Transitions (XSTA-TMR)

- XSTA-TMR-001: `after` maps millisecond delays to transitions taken when the state stays active that long; timers arm on entry, cancel on exit before expiry, and re-arm on re-entry.
- XSTA-TMR-002: The `clock` actor option supplies the timer source; `SimulatedClock.increment(ms)` advances simulated time, firing already-armed timers whose deadlines fall in the window in deadline order; timers armed mid-increment measure from the advanced time (one large increment advances a delayed chain by at most one step); behavior is synchronous and reproducible.

## Pure Stepping And Persistence (XSTA-PUR)

- XSTA-PUR-001: `getInitialSnapshot(machine, input?)` returns the initial snapshot with entry-time assigns applied; `getNextSnapshot(machine, snapshot, event)` returns the successor under actor-step rules.
- XSTA-PUR-002: Pure step functions do not run side-effecting actions and do not mutate the given snapshot.
- XSTA-PUR-003: WHEN the given snapshot is done, `getNextSnapshot` returns a snapshot still done with the same value.
- XSTA-PUR-004: `getPersistedSnapshot()` returns a plain serializable object with at least value, context, status; `createActor(machine, { snapshot })` resumes reporting the persisted value/context and transitions exactly as a continuation.

## Error Semantics (XSTA-ERR)

- XSTA-ERR-001: Invalid transition target → `createMachine` throws `Error`.
- XSTA-ERR-002: Compound state without `initial` → `createMachine` throws `Error`.
- XSTA-ERR-003: Runtime event processing is total: unknown types, guarded-off events, events after `stop()` or completion are ignored without throwing.

## Cross-View Invariants (XSTA-INV)

- XSTA-INV-001: Actor interpretation and pure stepping agree on `value`/`context` for the same event sequence.
- XSTA-INV-002: A false `can(event)` implies sending that event leaves `value` and `context` unchanged.
- XSTA-INV-003: `matches(v)` agrees with `matchesState(v, snapshot.value)`.
- XSTA-INV-004: A persisted-and-resumed actor is observationally equivalent to the original continuing.
- XSTA-INV-005: Under `SimulatedClock`, a delayed transition fires exactly at accumulated-delay threshold while armed; exit-and-re-entry restarts the delay.
- XSTA-INV-006: Once done, every projection reports the terminal snapshot and `toPromise` resolves with its `output`.
