# mobx Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`mobx` is a transparent reactive state-management library for JavaScript and TypeScript. A caller marks plain data — objects, arrays, maps, sets, or single boxed values — as observable, derives values from them with computed expressions, and attaches effects (`autorun`, `reaction`, `when`) that re-execute automatically when the observable data they actually read changes. The library maintains one dependency graph connecting observables, computed values, and effects; every state mutation propagates through that graph synchronously, re-running exactly the derivations and effects whose inputs changed.

The same graph is projected through several public surfaces: effect functions that re-run on change; computed values with demand-driven caching; a mutation event stream exposed by `observe` and a veto/rewrite hook exposed by `intercept`; plain-data snapshots produced by `toJS`; a generic collection API (`keys`, `values`, `entries`, `get`, `set`, `has`, `remove`) uniform across objects, arrays, and maps; introspection predicates (`isObservable`, `isComputedProp`, `isAction`, and relatives); and observability lifecycle hooks (`onBecomeObserved`, `onBecomeUnobserved`).

The installable package name is `mobx`. All functionality is reachable through named exports of the package root.

## Non-Goals

- This specification does not require `flow`, generator-based asynchronous actions, or flow cancellation.
- This specification does not define the `spy` diagnostic stream, `trace`, debug names, or dependency-tree inspection utilities.
- This specification does not require decorator syntax; annotations are applied through `makeObservable` and `makeAutoObservable` calls.
- This specification does not define integration with rendering frameworks.
- This specification does not require custom reaction schedulers, delayed reactions, or the `when` timeout option; all effect scheduling described here is synchronous.
- This specification does not define global-state isolation between multiple library copies, nor `configure` options other than `enforceActions`.
- This specification does not require `extendObservable`, `createAtom`, `getAtom`, `Reaction` as a public class, or `onReactionError`.

## Representative Workflows

The following two examples show complete, runnable workflows against the public API.

**Workflow 1 — inventory with computed totals and effects.**

```ts
import {
  observable, computed, autorun, reaction, runInAction, configure, toJS,
} from "mobx";

configure({ enforceActions: "never" });

const depot = observable({
  crates: [{ mass: 40 }, { mass: 25 }],
  factor: 2,
  get shipped() {          // getter in an observable literal becomes computed
    return this.crates.length * this.factor;
  },
});

const totalMass = computed(() =>
  depot.crates.reduce((s, c) => s + c.mass, 0),
);

const seen: number[] = [];
const stop = autorun(() => {
  seen.push(totalMass.get());       // autorun runs once immediately
});
// seen -> [65]

depot.crates.push({ mass: 10 });    // one synchronous re-run
// seen -> [65, 75]

const changes: [number, number][] = [];
const stopR = reaction(
  () => depot.shipped,
  (next, prev) => changes.push([next, prev]),
);
depot.factor = 3;                   // expression changed: 6 -> 9
// changes -> [[9, 6]]

runInAction(() => {                 // batched: effects run once at the end
  depot.crates.pop();
  depot.crates.pop();
});
// seen -> [65, 75, 40]

stop();
stopR();
const snapshot = toJS(depot);       // plain data, deeply de-observed
```

**Workflow 2 — a class store with annotations, events, and interception.**

```ts
import {
  makeObservable, observable, computed, action, observe, intercept,
  runInAction, isComputedProp, when,
} from "mobx";

class Reservoir {
  level = 120;
  capacity = 200;
  constructor() {
    makeObservable(this, {
      level: observable,
      capacity: observable,
      fillRatio: computed,
      drain: action,
    });
  }
  get fillRatio() {
    return this.level / this.capacity;
  }
  drain(amount: number) {
    this.level -= amount;
  }
}

const r = new Reservoir();
isComputedProp(r, "fillRatio");     // true

// veto invalid writes before they reach the graph
intercept(r, "level", (change) => {
  if (change.newValue < 0) return null;   // rejected silently
  return change;
});

const events: string[] = [];
observe(r, "level", (change) => {
  events.push(`${change.type}:${change.oldValue}->${change.newValue}`);
});

r.drain(20);                        // events -> ["update:120->100"]
runInAction(() => { r.level = -5; }); // vetoed; level stays 100

const refilled = when(() => r.fillRatio >= 0.9);  // promise form
runInAction(() => { r.level = 190; });
await refilled;                     // resolves once the predicate turns true
```

## Observable State

This section defines how plain data becomes observable and what the conversion promises. Observability is what connects data to the dependency graph: only reads of observable values inside a tracked context create dependencies, and only writes to observable values propagate.

**The observable factory.** `observable(value)` converts `value` by type. WHEN `value` is a plain object, the call returns a new observable proxy object; the proxy is a different reference from the input and `isObservableObject` returns `true` for it. WHEN `value` is an array, the call returns an observable array for which both `isObservableArray` and `Array.isArray` return `true`. WHEN `value` is a `Map`, the call returns an observable map; WHEN `value` is a `Set`, an observable set. WHEN `value` is a primitive (number, string, boolean), the call returns a boxed observable holding that value, for which `isBoxedObservable` returns `true`. Explicit constructors for each shape exist as `observable.object`, `observable.array`, `observable.map`, `observable.set`, and `observable.box`; `ObservableMap` and `ObservableSet` are also constructible directly and their instances satisfy `isObservableMap` / `isObservableSet`. Observable maps and sets are not `instanceof` the built-in `Map`/`Set`.

**Deep conversion.** Conversion is deep by default: values stored in an observable container (at creation or by later assignment) are themselves converted when they are plain objects, arrays, maps, or sets. WHEN the factory or a collection constructor receives the options argument `{ deep: false }`, stored values are kept as-is (shallow observability): the container itself is observable but elements are not converted.

**Boxed values.** A boxed observable exposes `get()` to read the current value (tracked) and `set(next)` to replace it. `observable.box(value, { equals })` accepts a comparer; WHEN `set` is called with a value the comparer deems equal to the current one, no change propagates.

**Dynamic object shape.** Observable proxy objects support adding new properties by plain assignment and removing them with the `delete` keyword; both are observable structure changes visible to `keys()` trackers and to `observe` listeners (as `add` and `remove` events). `isObservableProp(obj, key)` reports whether a property is observable; it returns `false` (never throws) for plain objects.

**Identity and JSON.** JSON serialization of observable objects and arrays produces the same text as for their plain counterparts. Writes that assign a value the default comparer deems identical to the current one do not propagate: no reaction runs and no event fires.

## Class Annotations

This section defines how class instances join the graph. Annotation happens per instance, in the constructor, through an explicit map or through automatic inference.

**makeObservable.** `makeObservable(target, annotations)` applies an annotation map whose keys are property or method names and whose values are annotation tokens: `observable` (deep observable field), `observableRef` (track only reassignment; the assigned value is not converted), `observableShallow` (convert one level: the collection is observable, its elements are not), `observableStruct` (reassignment propagates only when the new value is not structurally equal to the old), `computed` (a getter becomes a cached derivation), `computedStruct` (a getter whose result is compared structurally), `action` (method wrapped as an action), `actionBound` (action additionally bound to the instance so it survives detachment), and `false` (explicitly not annotated).

**makeAutoObservable.** `makeAutoObservable(target, overrides?)` infers annotations for every own member: fields become `observable`, getters become `computed`, and methods become `action`. The optional `overrides` map replaces the inference per key, and `false` excludes a member. If `makeAutoObservable` is applied to an instance of a class that has a superclass, then it must raise an `Error`. Methods annotated as plain `action` lose reactivity guarantees when detached from the instance (`this` is not bound); `actionBound` (or an `overrides` entry mapping a method to the bound-action token) binds them.

**Literal getters.** WHEN an object literal passed to `observable` contains a getter, the getter becomes a computed member of the resulting observable object, and `isComputedProp` reports `true` for it.

**Annotation errors.** If an annotation map names a key that does not exist on the target, then `makeObservable` must raise an `Error` naming the missing field. If a member that is already annotated is annotated again, then the second call must raise an `Error` describing the re-annotation.

## Derived Values

Computed values are the graph's derivation nodes: pure expressions over observable inputs whose results are cached by observation demand.

**Creation and reading.** `computed(expression, options?)` returns a computed value with a `get()` method; `isComputed` reports `true` for it. Class getters annotated `computed` and literal getters behave the same way through property access.

**Demand-driven caching.** A computed is lazy: the expression does not run before the first read. WHILE at least one active effect or observed computed depends on it, the computed caches its result: repeated reads return the cache without re-evaluating, and a change in a dependency re-evaluates the expression once for the reads and effect runs that follow. WHILE nothing observes it, a computed suspends: it drops its cache and re-evaluates on every read.

**Equality cut-off.** The `equals` option supplies a comparer applied between the previous and next results; WHEN the comparer deems them equal, observers of the computed are not re-run. Four comparers are exported: `compareDefault` (identity with `NaN` equal to `NaN`), `compareIdentity` (reference identity), `compareShallow` (own-key comparison one level deep), and `compareStructural` (deep structural comparison). `computedStruct` is shorthand for a structurally compared computed annotation.

**Cycles.** If a computed's expression reads the computed itself, directly or through other computed values, then reading it must raise an `Error` whose message identifies a detected cycle.

**Tracking exemption.** `untracked(fn)` runs `fn` and returns its result without recording dependencies in the surrounding tracked context; observables read only inside `untracked` do not cause the surrounding computed or effect to re-run.

## Effects

Effects are the graph's outputs: functions the library re-executes when their tracked inputs change. All effect scheduling in this specification is synchronous — a propagating mutation re-runs affected effects before the mutating statement returns.

**autorun.** `autorun(fn)` runs `fn` once immediately, records every observable read during the run, and re-runs `fn` synchronously whenever any recorded dependency changes. Each re-run re-records dependencies from scratch. The call returns a disposer function; after the disposer is called, no further runs occur.

**reaction.** `reaction(expression, effect, options?)` tracks only `expression`. The expression runs once immediately without running the effect. WHEN a later dependency change makes the expression produce a value not equal to the previous one (by the default comparer, or the `equals` option when given), the effect runs with three arguments: the new expression value, the previous expression value, and a reaction handle whose `dispose()` method stops the reaction (usable from inside the effect). WHERE the option `fireImmediately: true` is present, the effect also runs right after the initial expression evaluation, receiving `undefined` as the previous value. Observables read only inside the effect are not tracked. The call returns a disposer function.

**when.** `when(predicate, effect)` evaluates `predicate` immediately and re-evaluates it on dependency changes; WHEN the predicate first returns `true`, the effect runs exactly once and the observer is disposed. The single-argument form `when(predicate)` returns a promise that resolves when the predicate first returns `true`; the returned promise has a `cancel()` method. If `cancel()` is called before resolution, then the promise must reject with an `Error` whose message is `WHEN_CANCELLED`.

**Effect isolation.** A mutation to an observable no effect tracks re-runs nothing. A disposed effect never re-runs, regardless of later mutations.

## Actions And Batching

Actions group mutations into one atomic step of the graph. Without them, every individual mutation propagates immediately.

**Batching rule.** WHEN mutations happen inside an action, reactions and effect re-runs are deferred until the outermost action completes, then each affected effect runs exactly once, seeing the final state. Intermediate states that are established and reverted inside one action do not reach value-compared observers: WHEN the net expression value at action end equals the value at action start, a `reaction` does not run its effect. An `autorun`, which has no expression value to compare, re-runs once whenever any of its dependencies changed inside the action, even when every change was reverted before the action ended. WHEN a mutation happens outside any action (and enforcement permits it), affected effects run synchronously at that statement.

**Forms.** `action(fn)` returns a wrapped function for which `isAction` returns `true` (`isAction` returns `false` for plain functions). `action(name, fn)` additionally sets the wrapper's `name`. `runInAction(fn)` immediately executes `fn` as an action and returns its result. `transaction(fn)` batches like an action without marking the function as one. Class methods annotated `action`/`actionBound` are wrapped the same way.

**Write enforcement.** `configure({ enforceActions: mode })` sets the global write policy. The mode `"never"` allows writes anywhere. The initial mode `"observed"` requires an action for writes to observables that are currently observed by at least one effect; the mode `"always"` requires an action for every observable write. If a write violates the active policy, then the library must emit a console warning identifying the modified observable while still applying the write; violations never throw.

## Collections

Observable collections reimplement their built-in counterparts' interfaces with reactive reads and writes.

**Arrays.** Observable arrays support the full built-in array interface: index reads and writes, `length`, iteration, and search methods are all tracked, so an effect reading `arr.includes(x)` or `arr.length` re-runs when a mutation changes that answer. Reading an out-of-bounds index returns `undefined` without error; writing past the end extends the array (intermediate slots read as `undefined`). Beyond the built-ins: `replace(newItems)` swaps the whole contents in one change; `remove(value)` removes the first occurrence and returns whether something was removed; `clear()` empties the array and returns the removed items as a plain array. `splice` returns the removed section.

**Maps.** Observable maps expose `get`, `set`, `has`, `delete`, `size`, `clear`, `keys`, `values`, `entries`, iteration, and `forEach` with Map semantics, plus `merge(other)` (bulk set from an object, map, or entries) and `replace(other)` (make the contents equal `other`). `toJSON()` returns the entries as an array of `[key, value]` pairs. Reads are tracked at key granularity where observable: an effect that reads `map.has(k)` re-runs when `k` is added or deleted, and iteration-reading effects re-run on any structural change.

**Sets.** Observable sets expose `add`, `delete`, `has`, `size`, `clear`, and iteration with Set semantics; adding an element already present is not a change.

**Generic collection API.** The functions `keys`, `values`, `entries`, `get`, `set`, `has`, and `remove` operate uniformly on observable objects, arrays, and maps: `keys(obj)` returns own enumerable keys (an array-index list for arrays, key list for maps), `values`/`entries` follow, `get(target, key)` reads (returning `undefined` for absent keys), `set(target, key, value)` writes or adds, `has(target, key)` reports presence without throwing, and `remove(target, key)` deletes. Reading `keys()` inside an effect tracks the target's structure: adding or removing entries re-runs the effect.

## Mutation Events And Interception

Every observable exposes its change stream. Listeners see what changed; interceptors decide whether it is applied.

**observe.** `observe(target, listener)` subscribes to changes of an observable object, array, map, set, or box and returns a disposer. Listener events carry a `type` and target-specific fields. Object events: `update` (`name`, `newValue`, `oldValue`), `add` (`name`, `newValue`), `remove` (`name`, `oldValue`); each carries the observed `object`. Array events: `update` (`index`, `newValue`, `oldValue`) for index writes and `splice` (`index`, `added`, `removed`) for insertions, deletions, and pushes. Map events: `add` (`name`, `newValue`), `update` (`name`, `newValue`, `oldValue`), `delete` (`name`, `oldValue`). Set events: `add` (`newValue`), `delete` (`oldValue`). Box events: `update` (`newValue`, `oldValue`). `observe(object, key, listener)` subscribes to a single property; it fires only for that property's updates.

**intercept.** `intercept(target, handler)` (and the per-property form `intercept(object, key, handler)`) installs a hook that runs before a change is applied. The handler receives the pending change object and must return it (possibly with `newValue` rewritten) to let the mutation proceed, or return `null` to veto the mutation entirely. A vetoed mutation leaves the observable untouched, fires no events, and re-runs no effects. A handler that rewrites `newValue` causes the rewritten value to be stored.

## Snapshots And Introspection

The graph projects back to plain data on demand, and every node kind is identifiable.

**toJS.** `toJS(source)` returns a deep plain copy: observable objects become plain objects, observable arrays plain arrays, observable maps built-in `Map` instances, observable sets built-in `Set` instances, and a boxed observable at the top level unwraps to its value. Nothing in the returned structure is observable. Plain inputs pass through structurally unchanged.

**Predicates.** `isObservable` reports whether a value is any observable; `isObservableObject`, `isObservableArray`, `isObservableMap`, `isObservableSet`, and `isBoxedObservable` narrow the kind; `isObservableProp(obj, key)` and `isComputedProp(obj, key)` classify members of an observable object; `isAction` identifies wrapped functions; `isComputed` identifies computed value instances. All predicates return booleans and never throw on plain inputs.

## Observability Lifecycle

`onBecomeObserved(observable, handler)` and `onBecomeUnobserved(observable, handler)` register hooks on an observable, boxed value, or computed value that run when its observer count transitions from zero to nonzero and from nonzero to zero respectively. Each registration returns a disposer. The hooks fire on every transition, not just the first: an observable that is observed, released, and observed again fires observed/unobserved/observed in order. These hooks make the demand-driven lifecycle of the graph — including computed suspension — externally visible.

## State Model

The core state is a single dependency graph. Nodes are observables (object properties, array contents, map entries, set contents, boxed values), computed values, and effects. Edges are recorded by reads that happen inside tracked contexts (computed expressions, `autorun` bodies, `reaction` expressions, `when` predicates) and re-recorded on every run. Writes mark dependents stale and propagate synchronously — immediately for unbatched writes, at outermost-action end for batched ones.

Public projections of this one graph:

1. **Effect runs** — `autorun`/`reaction`/`when` execution counts and arguments.
2. **Computed reads** — values plus the caching/suspension behavior observable through evaluation counts.
3. **Event streams** — `observe` change events and `intercept` veto/rewrite hooks.
4. **Snapshots** — `toJS` plain-data projections and JSON serialization.
5. **Generic collection views** — `keys`/`values`/`entries`/`get`/`set`/`has`/`remove` over any observable container.
6. **Introspection** — the `is*` predicate family.
7. **Demand lifecycle** — `onBecomeObserved`/`onBecomeUnobserved` transitions.

All projections agree after every mutation: an effect re-run, its event, the snapshot, and the collection views all reflect the same post-change state.

## Error Semantics

Failures are signaled with plain `Error` instances whose messages identify the problem.

| Condition | Result |
|---|---|
| Computed expression reads its own value (directly or via a chain) | `Error` mentioning a detected cycle raised at read |
| `makeAutoObservable` on an instance whose class has a superclass | `Error` |
| `makeObservable` annotation names a nonexistent field | `Error` naming the field |
| Re-annotating an already-annotated member | `Error` describing the re-annotation |
| `when` promise cancelled via `cancel()` | promise rejects with `Error` whose message is `WHEN_CANCELLED` |
| Write violating the `enforceActions` policy | console warning; the write still applies; no throw |
| Reading an absent key via `get`, an out-of-bounds index, or `has` on a missing key | `undefined` / `false`; never throws |
| Calling a disposer more than once | no error, no effect |

## Cross-View Invariants

1. After any mutation completes (including at the end of an outermost action), every projection must agree: effect re-runs, `observe` events, `toJS` snapshots, generic collection views, and direct reads all reflect the same state.
2. A write the governing comparer deems equal to the current value must produce no effect run, no `observe` event, and no computed invalidation.
3. A mutation vetoed by an interceptor must be invisible everywhere: the value is unchanged, no event fires, no effect runs.
4. WHILE observed, a computed must not re-evaluate for reads between dependency changes; the number of expression evaluations equals the number of distinct dependency-change propagations plus the initial one. WHILE unobserved, each read must evaluate exactly once.
5. Batching must be composable: nested actions flush once at the outermost end, and the set of effect runs it triggers depends only on the net state change, given equality cut-offs.
6. `toJS` output must be JSON-stable with the observable source for plain-data content: serializing the snapshot and serializing the observable produce identical text.
7. Disposal must be total: after an effect's disposer runs, no future mutation runs that effect, and observer-count hooks must see the release.

## Public Interface

### Import Surface

```ts
import {
  observable, ObservableMap, ObservableSet,
  makeObservable, makeAutoObservable,
  observableRef, observableShallow, observableStruct, observableDeep,
  computed, computedStruct,
  action, actionBound, runInAction, transaction, untracked,
  autorun, reaction, when,
  observe, intercept,
  onBecomeObserved, onBecomeUnobserved,
  configure,
  toJS, keys, values, entries, get, set, has, remove,
  compareDefault, compareIdentity, compareShallow, compareStructural,
  isObservable, isObservableObject, isObservableArray, isObservableMap,
  isObservableSet, isBoxedObservable, isObservableProp, isComputedProp,
  isAction, isComputed,
} from "mobx";
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `observable` | function/namespace | Convert data to observable; `.object`/`.array`/`.map`/`.set`/`.box` explicit forms |
| `ObservableMap` | class | Observable map, directly constructible |
| `ObservableSet` | class | Observable set, directly constructible |
| `makeObservable` | function | Annotate class instance members explicitly |
| `makeAutoObservable` | function | Annotate class instance members by inference with overrides |
| `observableRef` | annotation | Track reassignment only |
| `observableShallow` | annotation | Convert one level only |
| `observableStruct` | annotation | Propagate reassignment only on structural change |
| `observableDeep` | annotation | Explicit deep conversion (the default) |
| `computed` | function/annotation | Cached derivation over observables |
| `computedStruct` | annotation | Computed with structural equality |
| `action` | function/annotation | Mark/wrap a mutating function; batches |
| `actionBound` | annotation | Action bound to the instance |
| `runInAction` | function | Run a one-off action immediately |
| `transaction` | function | Batch without marking a function as action |
| `untracked` | function | Run without recording dependencies |
| `autorun` | function | Effect that re-runs on tracked changes |
| `reaction` | function | Expression/effect pair with change arguments |
| `when` | function | One-shot predicate effect or promise |
| `observe` | function | Subscribe to mutation events |
| `intercept` | function | Veto or rewrite pending mutations |
| `onBecomeObserved` | function | Hook: observer count leaves zero |
| `onBecomeUnobserved` | function | Hook: observer count returns to zero |
| `configure` | function | Set global write-enforcement policy |
| `toJS` | function | Deep plain-data snapshot |
| `keys` / `values` / `entries` | functions | Generic reactive collection views |
| `get` / `set` / `has` / `remove` | functions | Generic reactive collection access |
| `compareDefault` | function | Identity comparer with `NaN` equality |
| `compareIdentity` | function | Reference identity comparer |
| `compareShallow` | function | One-level own-key comparer |
| `compareStructural` | function | Deep structural comparer |
| `isObservable` (family) | functions | Kind predicates; see Snapshots And Introspection |
| `isAction` / `isComputed` | functions | Function and computed-instance predicates |

### CLI Entry Points

There is no console script for this package. Programmatic use is through module imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. TypeScript sources are executed through a test runner with native TypeScript support (`vitest`); `typescript` and `@types/node` are installed. No other third-party runtime packages are available, and none are required. The assessment environment provides the same runtime and package set.

The project must declare its packaging metadata in a standard `package.json` at the project root, exposing the package root as an importable module named `mobx` with the named exports listed under Import Surface.

## Appendix B: Assessment Notes

Delivered implementations are exercised by behavioral tests importing only the public surface listed above. Tests are grouped in two suites: unit tests, each pinning one behavior family from one section (conversion kinds, caching counts, batching, event shapes, veto semantics, comparer behavior, error cases), and workflow tests that span several sections in one scenario (for example: annotate a class store, mutate through actions, and assert the resulting effect runs, events, snapshots, and lifecycle hooks agree). Effect behavior is asserted through observable run counts and recorded arguments, never through timing. Each test is assessed independently.
