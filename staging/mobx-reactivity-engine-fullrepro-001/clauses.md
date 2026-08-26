# Clause IDs — mobx-reactivity-engine-fullrepro-001

Sidecar mapping of clause IDs to spec statements (section anchors in parentheses).

## Observable State (MOBX-OBS)

- MOBX-OBS-001: `observable(value)` converts by type: plain object → observable proxy (new reference, `isObservableObject` true), array → observable array (`isObservableArray` and `Array.isArray` true), Map → observable map, Set → observable set, primitive → boxed observable (`isBoxedObservable` true); explicit forms `observable.object/.array/.map/.set/.box`; `ObservableMap`/`ObservableSet` directly constructible; observable maps/sets are not `instanceof` built-in Map/Set.
- MOBX-OBS-002: Conversion is deep by default; stored plain objects/arrays/maps/sets are converted on creation and later assignment; `{ deep: false }` keeps stored values unconverted.
- MOBX-OBS-003: A boxed observable exposes tracked `get()` and `set(next)`; a box `equals` comparer suppresses propagation for equal-judged sets.
- MOBX-OBS-004: Observable proxy objects support adding properties by plain assignment and removing with `delete`; both are structure changes visible to `keys()` trackers and `observe` (`add`/`remove` events).
- MOBX-OBS-005: `isObservableProp(obj, key)` reports observability; returns `false` and never throws for plain objects.
- MOBX-OBS-006: JSON serialization of observable objects/arrays equals that of their plain counterparts; writes judged identical by the governing comparer do not propagate (no reaction, no event).

## Class Annotations (MOBX-ANN)

- MOBX-ANN-001: `makeObservable(target, annotations)` applies tokens `observable`, `observableRef`, `observableShallow`, `observableStruct`, `computed`, `computedStruct`, `action`, `actionBound`, `false` per member.
- MOBX-ANN-002: `makeAutoObservable(target, overrides?)` infers observable for fields, computed for getters, action for methods; `overrides` replaces per key; `false` excludes.
- MOBX-ANN-003: WHEN `makeAutoObservable` is applied to an instance whose class has a superclass, it raises an `Error`.
- MOBX-ANN-004: Plain `action` methods are not `this`-bound when detached; `actionBound` binds to the instance.
- MOBX-ANN-005: WHEN an object literal passed to `observable` contains a getter, the getter becomes computed and `isComputedProp` reports `true`.
- MOBX-ANN-006: Annotating a nonexistent field raises an `Error` naming the field; re-annotating an annotated member raises an `Error`.

## Derived Values (MOBX-CMP)

- MOBX-CMP-001: `computed(expression, options?)` returns a computed with `get()`; `isComputed` true; class/literal getters annotated computed behave identically via property access.
- MOBX-CMP-002: A computed is lazy (no evaluation before first read); WHILE observed it caches (repeat reads no re-evaluation; dependency change re-evaluates once); WHILE unobserved it suspends and evaluates on every read.
- MOBX-CMP-003: The `equals` option cuts off propagation when previous and next results are judged equal; comparers `compareDefault` (identity + NaN), `compareIdentity`, `compareShallow` (one level), `compareStructural` (deep); `computedStruct` is the structural shorthand.
- MOBX-CMP-004: If a computed expression reads its own value (directly or via a chain), reading raises an `Error` mentioning a detected cycle.
- MOBX-CMP-005: `untracked(fn)` runs `fn` without recording dependencies; observables read only inside it do not re-run the surrounding context.

## Effects (MOBX-EFF)

- MOBX-EFF-001: `autorun(fn)` runs immediately, re-runs synchronously on tracked changes, re-records dependencies each run, returns a disposer that stops future runs.
- MOBX-EFF-002: `reaction(expression, effect)` tracks only the expression; the initial evaluation does not run the effect; on unequal change the effect gets (newValue, oldValue, handle-with-dispose); `fireImmediately: true` also runs the effect initially with `undefined` oldValue; an `equals` option replaces the default comparer; effect-only reads are untracked.
- MOBX-EFF-003: `when(predicate, effect)` runs the effect exactly once when the predicate first turns true, then disposes; `when(predicate)` returns a promise with `cancel()`; cancellation rejects with `Error` message `WHEN_CANCELLED`.
- MOBX-EFF-004: Mutations to untracked observables re-run nothing; disposed effects never re-run.

## Actions And Batching (MOBX-ACT)

- MOBX-ACT-001: Mutations inside an action defer effect re-runs to outermost action end; each affected effect then runs exactly once seeing final state; net-equal expression values suppress `reaction` effects while `autorun` (no value comparison) re-runs once when any dependency changed; unbatched mutations propagate synchronously at the statement.
- MOBX-ACT-002: `action(fn)` wraps (isAction true; plain functions false); `action(name, fn)` sets the wrapper name; `runInAction(fn)` executes immediately returning fn's result; `transaction(fn)` batches without marking.
- MOBX-ACT-003: `configure({ enforceActions })` sets write policy: `"never"` allows all; initial `"observed"` requires actions for observed observables; `"always"` for all writes; violations emit a console warning identifying the observable while the write still applies; never throws.

## Collections (MOBX-COL)

- MOBX-COL-001: Observable arrays track the full built-in interface (index reads/writes, length, iteration, search methods); out-of-bounds reads return `undefined`; writing past the end extends the array.
- MOBX-COL-002: Array extras: `replace(items)` swaps contents as one change; `remove(value)` returns whether removed; `clear()` returns removed items; `splice` returns the removed section.
- MOBX-COL-003: Observable maps expose Map semantics plus `merge(other)`, `replace(other)`, `toJSON()` (entries array); `has(k)` readers re-run on add/delete of `k`; iteration readers re-run on structural change.
- MOBX-COL-004: Observable sets expose Set semantics; adding a present element is not a change.
- MOBX-COL-005: Generic `keys`/`values`/`entries`/`get`/`set`/`has`/`remove` operate uniformly on observable objects, arrays, maps; `get` on absent keys returns `undefined`; `has` never throws; `keys()` readers track structure.

## Mutation Events And Interception (MOBX-EVT)

- MOBX-EVT-001: `observe(target, listener)` subscribes and returns a disposer; event shapes: object update/add/remove (`name`, `newValue`, `oldValue`, `object`), array update (`index`, `newValue`, `oldValue`) and splice (`index`, `added`, `removed`), map add/update/delete (`name`, `newValue`, `oldValue`), set add (`newValue`) / delete (`oldValue`), box update (`newValue`, `oldValue`).
- MOBX-EVT-002: `observe(object, key, listener)` fires only for that property's updates.
- MOBX-EVT-003: `intercept(target, handler)` and `intercept(object, key, handler)` run before application; returning the change (optionally with rewritten `newValue`) applies it; returning `null` vetoes: value unchanged, no events, no effect runs.

## Snapshots And Introspection (MOBX-SNP)

- MOBX-SNP-001: `toJS` deep-copies to plain data: objects→plain, arrays→plain, maps→built-in Map, sets→built-in Set, top-level box unwraps; nothing returned is observable; plain input passes through structurally unchanged.
- MOBX-SNP-002: Predicates `isObservable`, `isObservableObject/Array/Map/Set`, `isBoxedObservable`, `isObservableProp`, `isComputedProp`, `isAction`, `isComputed` return booleans and never throw on plain inputs.

## Observability Lifecycle (MOBX-LFC)

- MOBX-LFC-001: `onBecomeObserved`/`onBecomeUnobserved` register on observables, boxes, or computed values, fire on every zero↔nonzero observer transition, and return disposers; the hooks expose computed suspension externally.

## Error Semantics (MOBX-ERR)

- MOBX-ERR-001: Computed cycle → `Error` at read mentioning cycle detection.
- MOBX-ERR-002: `makeAutoObservable` with superclass → `Error`; unknown annotated field → `Error` naming it; re-annotation → `Error`.
- MOBX-ERR-003: `when` cancel → rejection with `Error` message `WHEN_CANCELLED`.
- MOBX-ERR-004: Policy-violating writes warn and apply; absent-key reads return `undefined`/`false`; double disposal is a no-op; predicates never throw.

## Cross-View Invariants (MOBX-INV)

- MOBX-INV-001: After any mutation completes, all projections agree (effects, events, snapshots, generic views, direct reads).
- MOBX-INV-002: A comparer-equal write produces no run, no event, no invalidation.
- MOBX-INV-003: A vetoed mutation is invisible everywhere.
- MOBX-INV-004: Evaluation counts: observed computed evaluates initial + once per distinct propagation; unobserved computed evaluates once per read.
- MOBX-INV-005: Nested actions flush once at outermost end; triggered effect runs depend only on net change given equality cut-offs.
- MOBX-INV-006: `toJS` snapshot and observable source serialize to identical JSON for plain-data content.
- MOBX-INV-007: Disposal is total: no post-disposal runs; lifecycle hooks observe the release.
