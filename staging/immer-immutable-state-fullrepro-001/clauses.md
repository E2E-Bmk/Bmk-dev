# Clause index — immer-immutable-state-fullrepro-001

Clause ID → verbatim spec sentence (anchor section). Sidecar for traceability;
not part of the candidate-visible packet.

## Producing State (IMM-PROD)

- IMM-PROD-001 (§Producing State): "The recipe's mutations must never be visible on the base state."
- IMM-PROD-002 (§Producing State): "When the recipe performs no effective change, `produce` must return the base state itself (reference identity)."
- IMM-PROD-003 (§Producing State): "When part of the tree changes, every ancestor object of a changed node must be a new object in the next state, and every branch not touched by a change must be shared by reference with the base."
- IMM-PROD-004 (§Producing State): "`produce` also accepts non-object bases — primitives, `null`, and `undefined` — and passes them to the recipe as-is; producing over a primitive base returns the recipe's result (or the base when the recipe returns nothing)."
- IMM-PROD-005 (§Producing State): "If the base is an object that is not draftable — for example an unmarked class instance or a `Date` — `produce` must throw an `Error`."
- IMM-PROD-006 (§Producing State): "Returning `undefined` (or not returning) means 'use the draft': the next state is the finalized draft. Returning the draft itself is equivalent and allowed even after modifying it."
- IMM-PROD-007 (§Producing State): "If a recipe both modifies its draft and returns a new value (including a promise), `produce` must throw an `Error`."
- IMM-PROD-008 (§Producing State): "Returning the exported sentinel `nothing` produces the value `undefined` as the next state."
- IMM-PROD-009 (§Producing State): "While automatic freezing is enabled (the default), the produced next state must be deeply frozen."
- IMM-PROD-010 (§Producing State): "a previously frozen base remains a legal input, and producing from it works normally."
- IMM-PROD-011 (§Producing State): "Inside the recipe, nested objects read from the draft are drafts themselves, mutations are visible through subsequent draft reads within the same recipe, and reads of unmodified leaves return the base's values."
- IMM-PROD-012 (§Producing State): "Drafts of a producer scope are revoked when the producer returns: reading or writing a draft that escaped its recipe must throw an `Error` or `TypeError`."
- IMM-PROD-013 (§Producing State): "A nested `produce` call over a draft or over a snapshot of a draft returns a value that can be assigned back into the outer draft, and the outer production finalizes it like any other value."
- IMM-PROD-014 (§Producing State): "Returning any other value means 'replace the state': the returned value becomes the next state."

## Curried Producers (IMM-CURRY)

- IMM-CURRY-001 (§Curried Producers): "When the first argument of `produce` is a function, `produce` returns a curried producer."
- IMM-CURRY-002 (§Curried Producers): "calling `curried(state, a, b)` invokes the recipe as `recipe(draft, a, b)` and returns the produced next state."
- IMM-CURRY-003 (§Curried Producers): "`produce(recipe, initialState)` attaches a default base: when the curried producer is called with `undefined` as its first argument, the recipe runs over a draft of `initialState`."
- IMM-CURRY-004 (§Curried Producers): "`produceWithPatches` accepts a recipe as its first argument the same way and returns a curried variant whose result is the `[nextState, patches, inversePatches]` triple."

## Draft Lifecycle And Inspection (IMM-LIFE)

- IMM-LIFE-001 (§Draft Lifecycle And Inspection): "`createDraft` accepts a draftable base and returns a live draft that records mutations exactly like a recipe draft."
- IMM-LIFE-002 (§Draft Lifecycle And Inspection): "`finishDraft` accepts such a draft, finalizes it, and returns the next state with the same identity, sharing, and freezing rules as `produce`."
- IMM-LIFE-003 (§Draft Lifecycle And Inspection): "`finishDraft` accepts an optional patch listener, called with the forward and inverse patches of the finished change set."
- IMM-LIFE-004 (§Draft Lifecycle And Inspection): "After `finishDraft`, the draft is revoked: any further read or write of it must throw."
- IMM-LIFE-005 (§Draft Lifecycle And Inspection): "`createDraft` must throw an `Error` when its argument is not draftable, and `finishDraft` must throw an `Error` when its argument is not a draft produced by `createDraft`."
- IMM-LIFE-006 (§Draft Lifecycle And Inspection): "`isDraft` returns `true` exactly for live draft proxies — the recipe's root draft, nested drafts read from it, and drafts made by `createDraft` — and `false` for plain values, finalized results, and bases."
- IMM-LIFE-007 (§Draft Lifecycle And Inspection): "`current` accepts a draft and returns a plain, finalized copy of the draft's present state: the snapshot reflects all mutations recorded so far, contains no draft proxies, is not frozen, and is decoupled from the draft."
- IMM-LIFE-008 (§Draft Lifecycle And Inspection): "Calling `current` on a value that is not a draft must throw an `Error`."
- IMM-LIFE-009 (§Draft Lifecycle And Inspection): "By default, finalization of a snapshot skips symbol-keyed children (a draft stored under a symbol key remains a draft inside the snapshot); while strict iteration is enabled (see Configuration), symbol-keyed children are finalized like string-keyed ones."
- IMM-LIFE-010 (§Draft Lifecycle And Inspection): "`original` accepts a draft and returns the base value that the draft wraps — for the root draft the producer's base argument itself, for a nested draft the corresponding nested base object, with reference identity."
- IMM-LIFE-011 (§Draft Lifecycle And Inspection): "`original` on a value that is not a draft must throw an `Error`."

## Draftability And Freezing (IMM-DRAFT)

- IMM-DRAFT-001 (§Draftability And Freezing): "`isDraftable` returns `true` for plain objects (prototype `Object.prototype` or `null`), arrays, `Map` and `Set` instances, and class instances whose class carries a truthy `immerable` marker. It returns `false` for `null`, primitives, functions, `Date`, and unmarked class instances."
- IMM-DRAFT-002 (§Draftability And Freezing): "Setting the exported `immerable` symbol to `true` on a class (statically or on its prototype) makes its instances draftable."
- IMM-DRAFT-003 (§Draftability And Freezing): "Producing over a marked instance must preserve the prototype: the next state is an instance of the same class, own enumerable fields are copied, the changed instance is a new object, and the base instance is untouched."
- IMM-DRAFT-004 (§Draftability And Freezing): "`freeze` freezes a value in place and returns it. With no second argument or `false`, only the value itself is frozen (own nested objects stay mutable); with `true`, freezing applies recursively to the entire tree."
- IMM-DRAFT-005 (§Draftability And Freezing): "`castDraft` and `castImmutable` return their argument unchanged at runtime (identity functions)."

## Patches (IMM-PATCH)

- IMM-PATCH-001 (§Patches): "Before the plugin is loaded, calling `produceWithPatches`, `applyPatches`, or passing a patch listener to `produce`/`finishDraft` must throw an `Error`."
- IMM-PATCH-002 (§Patches): "A patch is a plain object with an `op` field of `\"add\"`, `\"replace\"`, or `\"remove\"`, a `path` array of string or number keys addressing a location from the root, and — for `add` and `replace` — a `value` field carrying the new value."
- IMM-PATCH-003 (§Patches): "Adding a new object key yields `add`; changing an existing key or index yields `replace`; deleting a key yields `remove`."
- IMM-PATCH-004 (§Patches): "Appending to an array via `push` yields `add` patches at the new indices; truncating an array via its `length` yields `remove` patches for the dropped indices."
- IMM-PATCH-005 (§Patches): "`produceWithPatches` runs like `produce` but returns a three-element array `[nextState, patches, inversePatches]`. The forward stream transforms the base into the next state; the inverse stream transforms the next state back into the base."
- IMM-PATCH-006 (§Patches): "Replacing the whole state by returning a fresh value from the recipe yields a single patch with `op: \"replace\"` and an empty `path` whose `value` is the new state; producing `undefined` via `nothing` yields the same empty-path `replace` patch with the value `undefined`."
- IMM-PATCH-007 (§Patches): "`produce` accepts an optional third argument, a patch listener, invoked after the recipe completes with the forward patch array and the inverse patch array."
- IMM-PATCH-008 (§Patches): "`applyPatches` accepts a base state and an array of patches, and returns the state that results from applying them in order, produced under the same rules as `produce`."
- IMM-PATCH-009 (§Patches): "`add` on an object path sets the key; `add` on an array index splices the value in at that position (existing elements shift right); the array index `\"-\"` appends at the end."
- IMM-PATCH-010 (§Patches): "a `replace` with an empty `path` replaces the whole state with the patch's `value` (including replacing it with `undefined`)."
- IMM-PATCH-011 (§Patches): "removing a key that does not exist is a no-op."
- IMM-PATCH-012 (§Patches): "When a patch's `path` traverses a key that does not resolve to an existing container, `applyPatches` must throw an `Error`. When a patch carries any other `op` value, `applyPatches` must throw an `Error`."
- IMM-PATCH-013 (§Patches): "Applying patches to a live draft mutates that draft in place and returns the draft itself."

## Map And Set Drafts (IMM-MAPSET)

- IMM-MAPSET-001 (§Map And Set Drafts): "Before the plugin is loaded, producing over a `Map` or `Set` base must throw an `Error`."
- IMM-MAPSET-002 (§Map And Set Drafts): "A drafted `Map` supports `get`, `set`, `delete`, `clear`, `has`, `size`, `forEach`, and iteration (`keys`, `values`, `entries`, and the iterator protocol)."
- IMM-MAPSET-003 (§Map And Set Drafts): "`get` on a draftable value returns a draft of it, so nested mutation through `map.get(k).field = v` is recorded."
- IMM-MAPSET-004 (§Map And Set Drafts): "The finalized map preserves insertion order, is an instance of `Map`, and — under automatic freezing — is locked: calling `set`, `delete`, or `clear` on a finalized frozen map must throw an `Error`."
- IMM-MAPSET-005 (§Map And Set Drafts): "A production that changes nothing returns the base map itself."
- IMM-MAPSET-006 (§Map And Set Drafts): "Iterating a set draft yields drafts of draftable members, so members can be mutated during iteration and the mutations are recorded."
- IMM-MAPSET-007 (§Map And Set Drafts): "Map patches address entries by map key: setting a new key yields `add`, overwriting yields `replace`, and deleting yields `remove`, each with the key as the final `path` element."
- IMM-MAPSET-008 (§Map And Set Drafts): "Set patches address members by their position in iteration order with `add` and `remove` operations. Both round-trip through `applyPatches`."
- IMM-MAPSET-009 (§Map And Set Drafts): "`current` and `original` work on map drafts with the same semantics as on object drafts, and `original` likewise works on set drafts."

## Array Methods Plugin (IMM-ARR)

- IMM-ARR-001 (§Array Methods Plugin): "Without the plugin, array methods on drafts run the standard JavaScript implementations over the draft proxy, so search callbacks (for example the predicate of `find`) receive draft elements."
- IMM-ARR-002 (§Array Methods Plugin): "an element that has not been drafted during the recipe is passed as its plain (non-draft) value, and an element that was already drafted is passed as that existing draft. Callbacks therefore observe mutations recorded earlier in the same recipe."
- IMM-ARR-003 (§Array Methods Plugin): "`find` and `findLast` return a draft of the matched element (or `undefined`), and `filter` and `slice` return arrays of drafts."
- IMM-ARR-004 (§Array Methods Plugin): "Transforming methods (`concat`, `flat`) return new structures of base values whose mutation is not recorded."
- IMM-ARR-005 (§Array Methods Plugin): "Primitive-returning methods (`findIndex`, `findLastIndex`, `indexOf`, `lastIndexOf`, `includes`, `some`, `every`, `join`, `toString`, `toLocaleString`) return ordinary primitives."
- IMM-ARR-006 (§Array Methods Plugin): "`push`, `pop`, `shift`, `unshift`, `splice`, `reverse`, and `sort` on a drafted array must behave observably like the standard methods (same return values, same resulting array content) while recording their effect in the draft."

## Configuration (IMM-CFG)

- IMM-CFG-001 (§Configuration): "`setAutoFreeze` toggles deep freezing of finalized results. It defaults to enabled. While disabled, produced results must not be frozen."
- IMM-CFG-002 (§Configuration): "In default (loose) mode, copying keeps only own enumerable properties: non-enumerable own properties are dropped from the copy, and an own getter is read once at copy time and stored as a plain data property with the value it returned."
- IMM-CFG-003 (§Configuration): "In strict mode (`true`), non-enumerable own properties are preserved on the copy with their enumerability, and own getters are likewise materialized as data values."
- IMM-CFG-004 (§Configuration): "With `\"class_only\"`, plain objects copy in loose mode while `immerable`-marked class instances copy in strict mode."
- IMM-CFG-005 (§Configuration): "`setUseStrictIteration` accepts a boolean and defaults to `false`. It controls whether finalization walks symbol-keyed properties."
- IMM-CFG-006 (§Configuration): "The `Immer` class constructs an independent engine whose constructor accepts an options object with `autoFreeze`, `useStrictShallowCopy`, and `useStrictIteration` fields."
- IMM-CFG-007 (§Configuration): "an instance constructed with `autoFreeze: false` produces unfrozen results while the package-level functions continue to freeze, and vice versa."

## Error Semantics (IMM-ERR)

- IMM-ERR-001 (§Error Semantics): the condition→thrown table rows (each row one clause; referenced as IMM-ERR-001 collectively with the row named in test notes).

## Cross-View Invariants (IMM-CVI)

- IMM-CVI-001 (§Cross-View Invariants): "Patch round trip."
- IMM-CVI-002 (§Cross-View Invariants): "Snapshot equals finalization."
- IMM-CVI-003 (§Cross-View Invariants): "Identity tracks change."
- IMM-CVI-004 (§Cross-View Invariants): "Listener and triple agree."
- IMM-CVI-005 (§Cross-View Invariants): "Plugin gating is uniform."
- IMM-CVI-006 (§Cross-View Invariants): "Freezing follows configuration everywhere."
- IMM-CVI-007 (§Cross-View Invariants): "Drafts never leak into results."
