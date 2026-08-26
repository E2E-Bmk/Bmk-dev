# immer Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`immer` is an immutable-state library that lets callers write ordinary mutating code against a temporary *draft* and turns the recorded mutations into a new immutable value. A *producer* call takes a base state and a *recipe* function; the recipe receives a draft proxy of the base, mutates it freely, and when the recipe finishes the library finalizes the draft into the next state. The base state is never modified, unchanged branches of the tree are shared by reference between base and next state, and a run that changes nothing returns the base itself.

The same recorded mutations feed three simultaneous projections of one change set: the next state, a stream of forward *patches* describing how to transform the base into the next state, and a stream of *inverse patches* describing how to get back. Further views over the same draft mechanism include a manual draft lifecycle (`createDraft`/`finishDraft`), point-in-time snapshots (`current`), access to the underlying base (`original`), and opt-in support for `Map`, `Set`, and optimized array methods through loadable plugins. Global behavior switches (automatic freezing, strict shallow copying, strict iteration) can be set process-wide or scoped to an isolated engine instance.

The installable package name is `immer`. All functionality is reachable through named exports of the package root; there is no default export.

## Non-Goals

- This specification does not require asynchronous recipes: a recipe that returns a promise while also modifying its draft must be rejected as described in Error Semantics, and no promise-returning producer variant is required.
- This specification does not require a `this` binding inside recipes; recipes are invoked without binding the draft to `this`.
- This specification does not require support for drafting class instances that lack the `immerable` marker, `Date` objects, or other non-plain objects; passing such a base to a producer is an error.
- This specification does not require any particular wording of thrown error messages; only the error conditions and the thrown value being an `Error` instance are contracted.
- This specification does not require JSON Patch RFC 6902 compliance beyond the operations described in Patches; `move`, `copy`, and `test` operations are unsupported.
- This specification does not define a command-line interface or any file or network behavior.

## Representative Workflows

**Produce a next state with structural sharing.** A recipe mutates a draft; the produced value is a new frozen state that shares unchanged branches with the base:

```ts
import { produce } from "immer";

const base = {
  todos: [{ title: "write", done: false }],
  settings: { theme: "dark" },
};

const next = produce(base, (draft) => {
  draft.todos.push({ title: "review", done: false });
  draft.todos[0].done = true;
});

// base is untouched, the settings branch is shared by reference
// next.settings === base.settings, next.todos !== base.todos
// next is deeply frozen: attempting to mutate it throws in strict mode
```

**Record and replay changes with patches.** After loading the patches plugin, `produceWithPatches` returns the next state together with forward and inverse patch streams, and `applyPatches` replays them:

```ts
import { enablePatches, produceWithPatches, applyPatches } from "immer";

enablePatches();

const base = { list: [1, 2], meta: { owner: "a" } };
const [next, patches, inversePatches] = produceWithPatches(base, (draft) => {
  draft.list.push(3);
  draft.meta.owner = "b";
});

// applyPatches(base, patches) is structurally equal to next
// applyPatches(next, inversePatches) is structurally equal to base
```

**Manage a draft across multiple steps.** `createDraft` opens a draft outside a recipe; `finishDraft` finalizes it and optionally reports patches:

```ts
import { createDraft, finishDraft } from "immer";

const draft = createDraft({ count: 0, log: [] });
draft.count += 1;
draft.log.push("incremented");
const next = finishDraft(draft);
// next.count === 1; using the draft after finishDraft throws
```

## Producing State

Producing is the core operation: a producer call combines a base state and a recipe into a next state while leaving the base untouched.

**The produce call.** `produce` accepts a base state and a recipe function, invokes the recipe with a draft of the base as the first argument, and returns the finalized next state. The recipe's mutations must never be visible on the base state. When the recipe performs no effective change, `produce` must return the base state itself (reference identity). When part of the tree changes, every ancestor object of a changed node must be a new object in the next state, and every branch not touched by a change must be shared by reference with the base.

**Accepted base states.** A draftable base is a plain object (including objects with a `null` prototype), an array, a `Map` or `Set` (only after the corresponding plugin is loaded, see Map And Set Drafts), or an instance of a class marked with the `immerable` symbol. `produce` also accepts non-object bases — primitives, `null`, and `undefined` — and passes them to the recipe as-is; producing over a primitive base returns the recipe's result (or the base when the recipe returns nothing). If the base is an object that is not draftable — for example an unmarked class instance or a `Date` — `produce` must throw an `Error`.

**Recipe return rules.** A recipe communicates its result in exactly one of two ways, and mixing them is an error:

- Returning `undefined` (or not returning) means "use the draft": the next state is the finalized draft. Returning the draft itself is equivalent and allowed even after modifying it.
- Returning any other value means "replace the state": the returned value becomes the next state, and the recipe must not also have modified the draft. If a recipe both modifies its draft and returns a new value (including a promise), `produce` must throw an `Error`.
- Returning the exported sentinel `nothing` produces the value `undefined` as the next state. This is the only way to produce `undefined`, since a plain `undefined` return means "use the draft".

**Frozen results.** While automatic freezing is enabled (the default), the produced next state must be deeply frozen: `Object.isFrozen` returns `true` for the result and for every nested plain object and array in it, and attempting to assign to a frozen result in strict-mode code throws a `TypeError`. Freezing must not be applied to the base state's untouched copy semantics: a previously frozen base remains a legal input, and producing from it works normally.

**Drafts are proxies of the base.** Inside the recipe, nested objects read from the draft are drafts themselves, mutations are visible through subsequent draft reads within the same recipe, and reads of unmodified leaves return the base's values. Drafts of a producer scope are revoked when the producer returns: reading or writing a draft that escaped its recipe must throw an `Error` or `TypeError`.

**Nested producers.** `produce` may be called from inside a recipe. A nested `produce` call over a draft or over a snapshot of a draft returns a value that can be assigned back into the outer draft, and the outer production finalizes it like any other value.

## Curried Producers

Partial application turns a recipe into a reusable state-updater without repeating the base argument.

**Currying rule.** When the first argument of `produce` is a function, `produce` returns a curried producer. The curried producer takes a base state as its first argument and forwards every additional argument to the recipe after the draft: calling `curried(state, a, b)` invokes the recipe as `recipe(draft, a, b)` and returns the produced next state.

**Default state.** `produce(recipe, initialState)` attaches a default base: when the curried producer is called with `undefined` as its first argument, the recipe runs over a draft of `initialState`. When called with an explicit base, the default is ignored.

**Curried patch production.** `produceWithPatches` accepts a recipe as its first argument the same way and returns a curried variant whose result is the `[nextState, patches, inversePatches]` triple described in Patches.

## Draft Lifecycle And Inspection

The manual lifecycle exposes the same draft mechanism as `produce` for multi-step workflows, together with utilities that inspect a live draft.

**Manual drafts.** `createDraft` accepts a draftable base and returns a live draft that records mutations exactly like a recipe draft. `finishDraft` accepts such a draft, finalizes it, and returns the next state with the same identity, sharing, and freezing rules as `produce`. `finishDraft` accepts an optional patch listener, called with the forward and inverse patches of the finished change set (the patches plugin must be loaded to use it). After `finishDraft`, the draft is revoked: any further read or write of it must throw. `createDraft` must throw an `Error` when its argument is not draftable, and `finishDraft` must throw an `Error` when its argument is not a draft produced by `createDraft`.

**Draft detection.** `isDraft` returns `true` exactly for live draft proxies — the recipe's root draft, nested drafts read from it, and drafts made by `createDraft` — and `false` for plain values, finalized results, and bases.

**Snapshots with current.** `current` accepts a draft and returns a plain, finalized copy of the draft's present state: the snapshot reflects all mutations recorded so far, contains no draft proxies, is not frozen, and is decoupled from the draft — later draft mutations must not change an earlier snapshot. Calling `current` on a value that is not a draft must throw an `Error`. By default, finalization of a snapshot skips symbol-keyed children (a draft stored under a symbol key remains a draft inside the snapshot); while strict iteration is enabled (see Configuration), symbol-keyed children are finalized like string-keyed ones.

**Reading the base with original.** `original` accepts a draft and returns the base value that the draft wraps — for the root draft the producer's base argument itself, for a nested draft the corresponding nested base object, with reference identity. `original` on a value that is not a draft must throw an `Error`.

## Draftability And Freezing

Draftability decides which values the proxy mechanism will wrap; freezing protects finalized values from later mutation.

**The isDraftable predicate.** `isDraftable` returns `true` for plain objects (prototype `Object.prototype` or `null`), arrays, `Map` and `Set` instances, and class instances whose class carries a truthy `immerable` marker. It returns `false` for `null`, primitives, functions, `Date`, and unmarked class instances.

**Marking classes with immerable.** Setting the exported `immerable` symbol to `true` on a class (statically or on its prototype) makes its instances draftable. Producing over a marked instance must preserve the prototype: the next state is an instance of the same class, own enumerable fields are copied, the changed instance is a new object, and the base instance is untouched. Finalized marked instances are frozen under automatic freezing like plain objects.

**Explicit freezing.** `freeze` freezes a value in place and returns it. With no second argument or `false`, only the value itself is frozen (own nested objects stay mutable); with `true`, freezing applies recursively to the entire tree. Frozen values are skipped by the copy-on-write machinery, so pre-freezing large immutable inputs is a legal optimization.

**Cast helpers.** `castDraft` and `castImmutable` return their argument unchanged at runtime (identity functions); they exist for type-level conversions only.

## Patches

Patches are the change-log projection: the same recorded mutations that build the next state also describe themselves as portable operation records.

**Enabling the plugin.** Patch functionality lives in a plugin loaded by calling `enablePatches` once. Before the plugin is loaded, calling `produceWithPatches`, `applyPatches`, or passing a patch listener to `produce`/`finishDraft` must throw an `Error`.

**Patch records.** A patch is a plain object with an `op` field of `"add"`, `"replace"`, or `"remove"`, a `path` array of string or number keys addressing a location from the root, and — for `add` and `replace` — a `value` field carrying the new value. Adding a new object key yields `add`; changing an existing key or index yields `replace`; deleting a key yields `remove`. Appending to an array via `push` yields `add` patches at the new indices; truncating an array via its `length` yields `remove` patches for the dropped indices.

**produceWithPatches.** `produceWithPatches` runs like `produce` but returns a three-element array `[nextState, patches, inversePatches]`. The forward stream transforms the base into the next state; the inverse stream transforms the next state back into the base. Replacing the whole state by returning a fresh value from the recipe yields a single patch with `op: "replace"` and an empty `path` whose `value` is the new state; producing `undefined` via `nothing` yields the same empty-path `replace` patch with the value `undefined`.

**Patch listeners.** `produce` accepts an optional third argument, a patch listener, invoked after the recipe completes with the forward patch array and the inverse patch array. The listener sees exactly the patch streams `produceWithPatches` would have returned for the same change set.

**Applying patches.** `applyPatches` accepts a base state and an array of patches, and returns the state that results from applying them in order, produced under the same rules as `produce` (the base is untouched, results are frozen under automatic freezing). Its behavior per operation:

- `add` on an object path sets the key; `add` on an array index splices the value in at that position (existing elements shift right); the array index `"-"` appends at the end.
- `replace` sets the addressed key or index; a `replace` with an empty `path` replaces the whole state with the patch's `value` (including replacing it with `undefined`).
- `remove` deletes the addressed key; removing a key that does not exist is a no-op.
- When a patch's `path` traverses a key that does not resolve to an existing container, `applyPatches` must throw an `Error`. When a patch carries any other `op` value, `applyPatches` must throw an `Error`.

Applying patches to a live draft mutates that draft in place and returns the draft itself, so patch replay composes with an open recipe or manual draft.

## Map And Set Drafts

Container drafting for `Map` and `Set` is opt-in and mirrors the plain-object rules over container operations.

**Enabling the plugin.** `Map` and `Set` support lives in a plugin loaded by calling `enableMapSet` once. Before the plugin is loaded, producing over a `Map` or `Set` base must throw an `Error`.

**Map drafts.** A drafted `Map` supports `get`, `set`, `delete`, `clear`, `has`, `size`, `forEach`, and iteration (`keys`, `values`, `entries`, and the iterator protocol). `get` on a draftable value returns a draft of it, so nested mutation through `map.get(k).field = v` is recorded. Mutations never touch the base map. The finalized map preserves insertion order, is an instance of `Map`, and — under automatic freezing — is locked: calling `set`, `delete`, or `clear` on a finalized frozen map must throw an `Error`. A production that changes nothing returns the base map itself.

**Set drafts.** A drafted `Set` supports `add`, `delete`, `clear`, `has`, `size`, `forEach`, and iteration. Iterating a set draft yields drafts of draftable members, so members can be mutated during iteration and the mutations are recorded. Finalized sets follow the same identity, freezing, and no-change rules as maps.

**Patches over containers.** Map patches address entries by map key: setting a new key yields `add`, overwriting yields `replace`, and deleting yields `remove`, each with the key as the final `path` element. Set patches address members by their position in iteration order with `add` and `remove` operations. Both round-trip through `applyPatches`.

**Snapshots and bases.** `current` and `original` work on map drafts with the same semantics as on object drafts, and `original` likewise works on set drafts.

## Array Methods Plugin

The array-methods plugin replaces per-element proxying for common array operations with copy-level implementations, changing what callbacks observe.

**Enabling the plugin.** The behavior in this section activates when `enableArrayMethods` is called once. Without the plugin, array methods on drafts run the standard JavaScript implementations over the draft proxy, so search callbacks (for example the predicate of `find`) receive draft elements.

**Callback arguments.** With the plugin enabled, the callbacks of overridden search and iteration methods (`find`, `findLast`, `findIndex`, `findLastIndex`, `filter`, `some`, `every`) are invoked with the elements as currently stored in the working copy rather than with freshly created drafts: an element that has not been drafted during the recipe is passed as its plain (non-draft) value, and an element that was already drafted is passed as that existing draft. Callbacks therefore observe mutations recorded earlier in the same recipe.

**Return values.** Subset-selecting methods must still return drafts so that mutation continues to be recorded: `find` and `findLast` return a draft of the matched element (or `undefined`), and `filter` and `slice` return arrays of drafts. Mutating an element obtained from these return values must be reflected in the produced next state. Transforming methods (`concat`, `flat`) return new structures of base values whose mutation is not recorded. Primitive-returning methods (`findIndex`, `findLastIndex`, `indexOf`, `lastIndexOf`, `includes`, `some`, `every`, `join`, `toString`, `toLocaleString`) return ordinary primitives.

**Mutating methods.** `push`, `pop`, `shift`, `unshift`, `splice`, `reverse`, and `sort` on a drafted array must behave observably like the standard methods (same return values, same resulting array content) while recording their effect in the draft.

## Configuration

Behavior switches apply process-wide through setter functions, or per engine instance through the `Immer` class.

**Automatic freezing.** `setAutoFreeze` toggles deep freezing of finalized results. It defaults to enabled. While disabled, produced results must not be frozen. The switch affects subsequent productions, not previously produced values.

**Strict shallow copying.** `setUseStrictShallowCopy` controls how own properties are copied when a draft's parent is first written. It accepts `true`, `false` (the default), or the string `"class_only"`. In default (loose) mode, copying keeps only own enumerable properties: non-enumerable own properties are dropped from the copy, and an own getter is read once at copy time and stored as a plain data property with the value it returned. In strict mode (`true`), non-enumerable own properties are preserved on the copy with their enumerability, and own getters are likewise materialized as data values. With `"class_only"`, plain objects copy in loose mode while `immerable`-marked class instances copy in strict mode.

**Strict iteration.** `setUseStrictIteration` accepts a boolean and defaults to `false`. It controls whether finalization walks symbol-keyed properties: with strict iteration enabled, `current` finalizes drafts stored under symbol keys; with it disabled, such children are left as-is (see Draft Lifecycle And Inspection).

**Isolated engine instances.** The `Immer` class constructs an independent engine whose constructor accepts an options object with `autoFreeze`, `useStrictShallowCopy`, and `useStrictIteration` fields. An instance exposes `produce`, `produceWithPatches`, `createDraft`, `finishDraft`, `applyPatches`, `setAutoFreeze`, `setUseStrictShallowCopy`, and `setUseStrictIteration` with the semantics defined in this document, but reading and writing only that instance's configuration: an instance constructed with `autoFreeze: false` produces unfrozen results while the package-level functions continue to freeze, and vice versa. Loaded plugins are shared by all instances.

## State Model

The library's core state is a *producer scope*: a draft graph opened over one base value, plus the engine configuration in force (auto-freeze flag, strict-copy mode, strict-iteration flag, loaded plugins). Every public operation is a projection of that scope:

- The **next-state projection** (`produce`, `finishDraft`, `applyPatches`) finalizes the recorded mutations into a new immutable value with structural sharing and no-change identity.
- The **patch projection** (`produceWithPatches`, patch listeners) renders the same recorded mutations as forward and inverse operation streams.
- The **live projections** (`isDraft`, `current`, `original`, draft reads) observe the scope while it is open.
- The **capability projections** (`isDraftable`, `immerable`, `freeze`, plugin loaders, configuration setters, `Immer` instances) determine what may enter a scope and how it finalizes.

All projections must agree: what the patches say happened is exactly the difference between base and next state; what `current` shows mid-recipe is exactly what finalization would produce at that moment; what `original` returns is exactly the untouched base.

## Error Semantics

All errors below are thrown synchronously as `Error` instances (or `TypeError` where noted). Message wording is not contracted.

| Condition | Thrown |
|---|---|
| `produce`/`createDraft` over a non-draftable object base (unmarked class instance, `Date`, etc.) | `Error` |
| Recipe both modifies its draft and returns a new value (including returning a promise) | `Error` |
| `produceWithPatches`, `applyPatches`, or a patch listener used before `enablePatches` | `Error` |
| Producing over a `Map` or `Set` before `enableMapSet` | `Error` |
| Reading or writing a draft after its scope closed (escaped recipe draft, finished manual draft) | `Error` or `TypeError` |
| `current` on a non-draft | `Error` |
| `original` on a non-draft | `Error` |
| `finishDraft` on a value not created by `createDraft` | `Error` |
| `applyPatches` with a path that does not resolve | `Error` |
| `applyPatches` with an unsupported `op` | `Error` |
| Mutating a frozen produced object in strict-mode code | `TypeError` |
| Calling `set`/`delete`/`clear`/`add` on a finalized frozen `Map`/`Set` | `Error` |

## Cross-View Invariants

1. **Patch round trip.** For every production run with patches enabled, `applyPatches(base, patches)` must be structurally equal to the produced next state, and `applyPatches(nextState, inversePatches)` must be structurally equal to the base — for plain objects, arrays, maps, and sets alike.
2. **Snapshot equals finalization.** At any point inside a recipe, `current(draft)` must be structurally equal to the state that finalizing the scope at that moment would produce, while `original(draft)` must be reference-identical to the base — so snapshot, base access, and the eventual next state never disagree.
3. **Identity tracks change.** A production that records no effective mutation must return the base by reference (and emit zero patches); a production that records any effective mutation must return a new root object while every untouched branch keeps reference identity with the base. This holds for `produce`, curried producers, `finishDraft`, and `applyPatches` runs alike.
4. **Listener and triple agree.** For the same base and recipe, the patch arrays passed to a `produce` patch listener must equal the patch arrays returned by `produceWithPatches`, and both must describe the same next state that `produce` returns without a listener.
5. **Plugin gating is uniform.** Every patch-consuming entry point (`produceWithPatches`, `applyPatches`, patch listeners on `produce` and `finishDraft`) must throw before `enablePatches`, and every container production (`Map` or `Set` base, nested or root) must throw before `enableMapSet` — the gate does not depend on which projection touches the feature first.
6. **Freezing follows configuration everywhere.** Under `autoFreeze` enabled, results of `produce`, `finishDraft`, and `applyPatches` are deeply frozen, and frozen containers reject mutation; under an `Immer` instance or global setting with `autoFreeze` disabled, the same runs yield unfrozen results — the freeze decision depends only on the configuration of the engine that finalized the scope.
7. **Drafts never leak into results.** Finalized next states, `current` snapshots (for string-keyed children), and patch `value` fields must contain no live draft proxies: `isDraft` is `false` for every reachable value in them.

## Public Interface

### Import Surface

The package exposes a single module entry point with named exports only:

```ts
import {
  produce,
  produceWithPatches,
  applyPatches,
  createDraft,
  finishDraft,
  current,
  original,
  isDraft,
  isDraftable,
  freeze,
  nothing,
  immerable,
  castDraft,
  castImmutable,
  setAutoFreeze,
  setUseStrictShallowCopy,
  setUseStrictIteration,
  enablePatches,
  enableMapSet,
  enableArrayMethods,
  Immer,
} from "immer";

import type {
  Draft,
  WritableDraft,
  Immutable,
  Patch,
  PatchListener,
  Producer,
  Objectish,
  StrictMode,
} from "immer";
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `produce` | function | Runs a recipe over a draft of a base state and returns the next state; curries when called with a recipe first. |
| `produceWithPatches` | function | Like `produce` but returns `[nextState, patches, inversePatches]`; curries the same way. |
| `applyPatches` | function | Applies an array of patches to a base state (or live draft) and returns the result. |
| `createDraft` | function | Opens a manual draft over a draftable base. |
| `finishDraft` | function | Finalizes a manual draft into the next state, optionally reporting patches. |
| `current` | function | Returns an unfrozen, finalized snapshot of a live draft's present state. |
| `original` | function | Returns the base value underlying a live draft. |
| `isDraft` | function | Tells whether a value is a live draft proxy. |
| `isDraftable` | function | Tells whether a value can be drafted. |
| `freeze` | function | Freezes a value in place, shallowly by default or deeply on request. |
| `nothing` | constant | Sentinel returned from a recipe to produce `undefined`. |
| `immerable` | constant | Symbol that marks a class as draftable. |
| `castDraft` | function | Type-level cast; returns its argument unchanged. |
| `castImmutable` | function | Type-level cast; returns its argument unchanged. |
| `setAutoFreeze` | function | Toggles deep freezing of finalized results. |
| `setUseStrictShallowCopy` | function | Selects loose, strict, or `"class_only"` own-property copying. |
| `setUseStrictIteration` | function | Toggles finalization of symbol-keyed children. |
| `enablePatches` | function | Loads the patches plugin. |
| `enableMapSet` | function | Loads the `Map`/`Set` plugin. |
| `enableArrayMethods` | function | Loads the array-methods plugin. |
| `Immer` | class | Independent engine instance with isolated configuration. |
| `Draft` | type | Mutable view of a state type, as seen inside recipes. |
| `WritableDraft` | type | Object form of `Draft`. |
| `Immutable` | type | Deeply readonly view of a state type. |
| `Patch` | type | One patch record: `op`, `path`, optional `value`. |
| `PatchListener` | type | Callback receiving forward and inverse patch arrays. |
| `Producer` | type | Recipe function type. |
| `Objectish` | type | Union of draftable container types. |
| `StrictMode` | type | `boolean` or `"class_only"`, the strict-copy setting. |

### CLI Entry Points

There is no console script for this package. Programmatic use is through module imports only.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. TypeScript sources are executed through a test runner that supports TypeScript natively; the package under construction must be importable as `immer` from test files via standard Node module resolution (an installable package with a `package.json` whose exports resolve the module entry point).

No third-party runtime dependencies are available or required. The assessment environment provides the same interpreter and module-resolution setup.

## Appendix B: Assessment Notes

Assessment exercises the documented behavior through the public module surface only. Dimensions covered include: production semantics (identity, sharing, recipe return rules, sentinel results, freezing), curried producers and default states, the manual draft lifecycle and revocation, snapshot and base access, draftability and class marking, the patch projection (record shapes, listener/triple agreement, application algebra including error paths), `Map`/`Set` drafting and their patches, array-method plugin semantics, configuration switches and isolated engine instances, and the error conditions tabulated above. Tests assert observable values, reference identities, thrown error types, and cross-view equivalences; they do not assert error message wording, internal object shapes, or private state.
