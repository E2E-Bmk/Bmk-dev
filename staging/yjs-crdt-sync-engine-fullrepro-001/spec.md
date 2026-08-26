# yjs Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`yjs` is a conflict-free replicated data type (CRDT) engine for building collaborative applications. Each participant holds a *document* — an independent replica containing named shared types (maps, arrays, and rich text) that behave like their ordinary mutable counterparts. Every change to a shared type is recorded in the document's internal operation store and can be encoded as a compact binary *update*. Applying the updates of one document to another synchronizes them: any two documents that have received the same set of updates expose identical content through every public view, regardless of the order or grouping in which the updates arrived, and re-applying an update a replica has already seen changes nothing.

On top of this convergence core, the same operation store powers further projections: transaction-scoped change events with per-key and per-range deltas, update algebra that merges and diffs update payloads without instantiating a document, scoped undo/redo that respects the boundary between local and remote edits, immutable snapshots that capture and restore a document version, and relative positions — cursor-like markers that keep pointing at the same character while concurrent edits move it around.

The installable package name is `yjs`. All functionality is reachable through named exports of the package root; the conventional import style is a namespace import (`import * as Y from "yjs"`).

## Non-Goals

- This specification does not require XML-shaped shared types, subdocument nesting, permanent user data, or any network provider or awareness protocol.
- This specification does not define the binary layout of updates, state vectors, snapshots, or encoded positions; only their observable round-trip and algebraic properties are contracted, together with the payloads being `Uint8Array` instances.
- This specification does not require any particular wording of thrown error messages; only the error conditions and the thrown value being an `Error` instance are contracted.
- This specification does not require a deterministic winner for concurrent writes to the same map key; it requires that all replicas converge on the same winner, chosen from the concurrently written values.
- This specification does not require a document-level JSON projection; JSON conversion is defined per shared type.
- This specification does not require garbage-collection tuning beyond the `gc` document option's effect on snapshot restoration.

## Representative Workflows

**Synchronize two documents.** Each document edits its own shared types; exchanging encoded updates makes the replicas converge:

```ts
import * as Y from "yjs";

const alice = new Y.Doc();
const bob = new Y.Doc();

alice.getText("note").insert(0, "hello");
Y.applyUpdate(bob, Y.encodeStateAsUpdate(alice));

bob.getText("note").insert(5, " world");
alice.getText("note").insert(0, ">> ");

// exchange both directions
Y.applyUpdate(alice, Y.encodeStateAsUpdate(bob));
Y.applyUpdate(bob, Y.encodeStateAsUpdate(alice));

// alice.getText("note").toString() === bob.getText("note").toString()
```

**Ship only what the peer is missing.** A state vector describes what a replica has seen; encoding against it yields a minimal difference update:

```ts
import * as Y from "yjs";

const server = new Y.Doc();
server.getMap("config").set("theme", "dark");

const client = new Y.Doc();
const clientView = Y.encodeStateVector(client);
const diff = Y.encodeStateAsUpdate(server, clientView);
Y.applyUpdate(client, diff);
// client.getMap("config").get("theme") === "dark"
```

**Undo local edits without reverting remote ones.** An undo manager scoped to a shared type reverts tracked local transactions while preserving interleaved remote content:

```ts
import * as Y from "yjs";

const doc = new Y.Doc();
const text = doc.getText("t");
const undoManager = new Y.UndoManager(text);

text.insert(0, "local");             // tracked (untagged local transaction)
// ... a remote update arrives via Y.applyUpdate(doc, update, "remote") ...
undoManager.undo();                  // removes "local", keeps the remote content
```

## Documents And Root Types

A document is one replica of the collaborative state; root-level shared types live inside it under stable string names.

**Construction.** A `Doc` accepts an optional options object with a `guid` (string identifier, randomly generated when omitted) and `gc` (boolean, defaults to `true`) controlling whether deleted content may be garbage-collected. Every document instance must carry a numeric `clientID`; two independently constructed documents must receive different `clientID` values. When a `guid` is supplied, the document's `guid` property must equal it.

**Root type accessors.** `getMap(name)`, `getArray(name)`, and `getText(name)` return the root shared type registered under `name`, creating it on first access. Repeated calls with the same name must return the same instance (reference identity). If a root name already designated by one typed accessor is requested through an accessor of a different type, then the call must throw an `Error`.

**Transactions.** Every mutation of a shared type happens inside a transaction. `doc.transact(fn, origin)` runs `fn` inside a single transaction and returns `fn`'s return value; the optional `origin` (any value) tags the transaction and is visible to observers. Mutations made outside an explicit `transact` call run in an implicit transaction with a `null` origin. When a `transact` call is nested inside another, the inner call must not open a new transaction: all mutations belong to the outermost transaction and produce a single change notification and a single update event. When a transaction completes without any effective change, the document must not emit an `"update"` event.

**Document updates.** The document emits an `"update"` event for every transaction that changed content. The handler is invoked with the encoded update (`Uint8Array`) describing exactly that transaction's changes, the transaction origin, the document, and the transaction object. Applying these per-transaction updates to a peer replica in order must reproduce the content changes.

**Lifecycle.** `destroy()` tears the document down and emits a `"destroy"` event; afterwards the document's `isDestroyed` property must be `true`. Event registration uses `on(name, handler)`, `off(name, handler)`, and `once(name, handler)` on the document.

## Shared Maps

A shared map is a key-value container with string keys that replicates like the rest of the document.

**Reading and writing.** `set(key, value)` stores a value under a key and returns the value. `get(key)` returns the stored value, or `undefined` when the key is absent. `has(key)` reports presence, `delete(key)` removes an entry, `clear()` removes all entries, and the `size` property counts current entries. Storing `null` is allowed and must be preserved as `null` (distinct from an absent key). Concurrent `set` calls to the same key on different replicas must converge: after exchanging updates, all replicas must report the same value for the key, and that value must be one of the concurrently written values.

**Stored values.** Legal values are JSON-serializable primitives and structures (booleans, numbers, strings, `null`, plain objects, plain arrays), `Uint8Array` payloads, and shared types. Plain objects and arrays are stored and replicated as plain values: after a round trip through update encoding, they must compare deeply equal and remain plain (not shared types). `Uint8Array` values must survive replication as `Uint8Array` with identical bytes. If a value that cannot be represented — for example a function — is stored, then `set` must throw an `Error`.

**Iteration and conversion.** `keys()`, `values()`, and `entries()` return iterators that visit every current entry exactly once; `forEach(fn)` invokes `fn(value, key, map)` for each entry; the map itself is iterable over `[key, value]` pairs. No visiting order is contracted. `toJSON()` returns a plain object with one property per entry, converting nested shared types recursively to their JSON forms. `clone()` returns a new, unintegrated shared map holding the same entries.

**Construction and nesting.** A standalone map is created with the `Map` constructor, optionally seeded from an iterable of entries. A standalone type may be mutated before it is integrated into a document; once inserted (for example via `parentMap.set(key, childType)`), the pre-integration content must be observable through the child. After integration, the child's `parent` property must be the containing type and its `doc` property the containing document; a root type's `parent` is `null`. A shared type instance must be integrated at most once: if an already-integrated type is inserted at a second location, then the call must throw.

## Shared Arrays

A shared array is an index-addressed sequence that replicates insertions and deletions.

**Reading and writing.** `insert(index, content)` inserts the items of the `content` array at `index`; `push(content)` appends and returns `undefined`; `unshift(content)` prepends. `delete(index, length)` removes `length` consecutive items starting at `index` (the length defaults to 1). `get(index)` returns the item at an index, the `length` property counts items, and `slice(start, end)` returns a plain-array copy of the range with the usual end-exclusive semantics and optional arguments. If `insert` targets an index greater than the current length, or `delete` addresses a range extending past the end, then the call must throw an `Error`.

**Iteration and conversion.** `toArray()` returns a plain array of the current items; `toJSON()` does the same while converting nested shared types recursively. `map(fn)` and `forEach(fn)` invoke `fn(item, index, array)`; the array itself is iterable in index order. The static `Array.from(items)` builds a standalone shared array seeded with `items`.

**Values and convergence.** The legal item values are the same as for shared maps, including nested shared types constructed standalone and integrated by insertion. Concurrent insertions from different replicas must converge to the same sequence on all replicas after update exchange, with every inserted item preserved exactly once.

## Shared Text

Shared text models collaborative rich text: a character sequence with optional formatting attributes and embedded objects.

**Editing.** `insert(index, text, attributes)` inserts a string at a character index, optionally formatted with an attributes object; when `index` exceeds the current length, the text must be appended at the end rather than throwing. `delete(index, length)` removes a character range; a range extending past the end must be clamped to the available content rather than throwing. `format(index, length, attributes)` applies formatting attributes to an existing range; an attribute set to `null` removes that attribute from the range. `insertEmbed(index, embed, attributes)` inserts an embedded object (for example an image descriptor) that occupies exactly one unit of length. The `length` property counts characters plus one per embed.

**Reading.** `toString()` returns the concatenated plain text, skipping embeds; `toJSON()` returns the same string. `toDelta()` returns the rich content as an array of operation objects: each op is `{ insert }` carrying a string run or an embed object, plus an `attributes` object when the run is formatted; adjacent runs with identical formatting must be reported as a single op.

**Delta application.** `applyDelta(ops)` applies an array of delta operations against the current content: `{ insert }` ops (with optional `attributes`) insert content at the running position, `{ retain }` ops skip over existing content — applying `attributes` on the retained range when present — and `{ delete }` ops remove content. The delta projection must round-trip: the content after `applyDelta` must be observable through `toDelta`, `toString`, and `length` consistently.

**Construction and convergence.** A standalone text is created with the `Text` constructor, optionally seeded with an initial string that becomes observable once the type is integrated. Concurrent inserts at the same position on different replicas must converge to the same character sequence on all replicas, with both inserted runs preserved intact (not interleaved character-by-character). Formatting applied on one replica must be visible in the `toDelta` projection of every replica after update exchange.

## Update Exchange

Updates are the replication currency: binary payloads that carry changes between replicas and can be manipulated without a document.

**Encoding and applying.** `encodeStateAsUpdate(doc, encodedTargetStateVector)` returns a `Uint8Array` update covering the document's whole history, or — when the optional encoded state vector of a target replica is supplied — only the changes that replica has not seen. `applyUpdate(doc, update, origin)` integrates an update into a document; the optional `origin` tags the resulting transaction. `encodeStateVector(doc)` returns the document's version descriptor as a `Uint8Array`. If `applyUpdate` receives a malformed payload, then it must throw an `Error`.

**Convergence laws.** Applying the same update twice must leave the second application without effect (idempotency). Applying a set of updates in any order and grouping must yield the same content on every replica (commutativity). When an update depends on changes the receiving document has not yet seen, the document must buffer it without visible effect and integrate it automatically once the missing updates arrive.

**Update algebra.** Three functions operate on update payloads directly, with no document involved: `mergeUpdates(updates)` combines an array of updates (in any order, tolerating overlap and duplicates) into one update that replays to the same content; `encodeStateVectorFromUpdate(update)` computes the state vector describing an update's coverage, equal to the state vector of a document that applied it; and `diffUpdate(update, encodedStateVector)` extracts from an update only the changes not covered by the given state vector, such that applying the diff on top of the covered prefix reproduces the full content.

**Alternate encoding.** A second binary format is available through `encodeStateAsUpdateV2(doc, encodedTargetStateVector)` and `applyUpdateV2(doc, update, origin)`. `convertUpdateFormatV1ToV2(update)` and `convertUpdateFormatV2ToV1(update)` translate payloads between the two formats. Replaying a document's history through either format, or through a conversion round trip, must produce identical content on the receiving replica.

## Events And Observation

Observers deliver transaction-scoped change descriptions on shared types and let applications react to local and remote edits uniformly.

**Registering observers.** Every shared type supports `observe(handler)` and `unobserve(handler)`. The handler is invoked once per transaction that changed the type, receiving an event object and the transaction. After `unobserve`, the handler must not be invoked again. `observeDeep(handler)` (with `unobserveDeep`) additionally covers all nested shared types beneath the observed one: the handler receives an array of event objects — one per changed type — and the transaction.

**Event objects.** Every event exposes `target` (the changed shared type) and `path` (the route from the observed type to the target: map keys as strings and array indices as numbers). Change descriptions are computed lazily and must be read inside the handler: if `changes` or `delta` is first accessed after the handler has returned, then the access must throw an `Error`.

**Map events.** A map event's `changes.keys` is a JavaScript `Map` from each affected key to a record with an `action` (`"add"`, `"update"`, or `"delete"`) and an `oldValue`. The record describes the net effect of the whole transaction measured against its start state: a key that is set and then deleted inside one transaction reports a single `"delete"` with the pre-transaction value as `oldValue`, and a key that did not exist before reports `"add"` with an `oldValue` of `undefined`. The event's `keysChanged` set names the affected keys.

**Sequence events.** Array and text events expose `delta`: an array of `{ retain }`, `{ insert }`, and `{ delete }` operations describing the transaction's net change against the pre-transaction sequence. For text events, `insert` carries strings (with `attributes` for formatted runs); for array events, `insert` carries an array of inserted items.

**Transaction metadata.** The transaction passed to observers and document events exposes `origin` (the tag given to `transact` or `applyUpdate`, `null` for untagged local edits) and `local` (`true` for transactions created by local mutations, `false` for transactions created by applying updates). Remote and local changes must fire the same observers with the same event shapes.

## Undo And Redo

An undo manager provides scoped, origin-aware undo/redo over one or more shared types.

**Construction and scope.** `UndoManager` is constructed with a scope — one shared type or an array of shared types — and an options object supporting `captureTimeout` (milliseconds, default 500) and `trackedOrigins` (a `Set` of origins). Only changes to the scoped types are tracked and reverted. By default, only transactions with a `null` origin (untagged local edits) are tracked; when `trackedOrigins` is supplied, exactly the transactions whose origin is in the set are tracked, and untagged edits are tracked only if `null` is in the set.

**Capturing.** Tracked transactions that occur within `captureTimeout` of each other merge into a single undo entry; a `captureTimeout` of 0 keeps every transaction as its own entry. `stopCapturing()` ends the current entry so the next tracked change starts a new one, regardless of timing.

**Undoing and redoing.** `undo()` reverts the most recent undo entry; `redo()` re-applies the most recently undone entry. `canUndo()` and `canRedo()` report whether entries are available, and `clear()` empties both stacks. A new tracked change after an undo must clear the redo stack. Undoing a map change must restore the previous value of each affected key (or its absence). Undoing must revert only tracked changes: content produced by untracked or remote transactions interleaved with the tracked ones must survive an undo, and a subsequent redo must restore exactly the undone content.

**Stack item events.** The manager emits `"stack-item-added"` when an entry is created (and when an undo pushes the corresponding redo entry) and `"stack-item-popped"` when an entry is applied. Handlers receive an event with the `stackItem` and a `type` field (`"undo"` or `"redo"`). Each stack item carries a `meta` property — a JavaScript `Map` for arbitrary user data — and the meta content attached when an item is added must be readable when the same item is popped.

## Snapshots

A snapshot captures a document version so it can be compared, serialized, and restored.

**Capturing and codecs.** `snapshot(doc)` returns a snapshot describing the document's current version. `encodeSnapshot(snapshot)` serializes it to a `Uint8Array` and `decodeSnapshot(data)` restores it; `equalSnapshots(a, b)` reports whether two snapshots describe the same version. A decode of an encode must compare equal to the original, and snapshots taken before and after a content change must compare unequal.

**Restoring.** `createDocFromSnapshot(originDoc, snapshot)` builds a new document whose shared types contain exactly the content the origin document had when the snapshot was taken. Restoration requires history: if the origin document was created with garbage collection enabled (the default `gc: true`), then `createDocFromSnapshot` must throw an `Error`; documents intended for snapshot restoration must be constructed with `gc: false`.

**Coverage tests.** `snapshotContainsUpdate(snapshot, update)` returns `true` exactly when every change carried by the update is covered by the snapshot's version: it must return `true` for a snapshot taken after the update's changes and `false` for a snapshot taken before them.

## Relative Positions

Relative positions are stable markers into sequence content — the building block for cursors and annotations that survive concurrent editing.

**Creating and resolving.** `createRelativePositionFromTypeIndex(type, index, assoc)` creates a position anchored at a character index of a sequence type; the optional `assoc` (default 0) associates the position with the character to the right, or with the character to the left when negative. `createAbsolutePositionFromRelativePosition(relPos, doc)` resolves a relative position against a document, returning an object with `index` (the current character index) and `type` (the resolved shared type, reference-identical to the anchored type) — or `null` when the position cannot be resolved in that document (for example against an unrelated replica that never saw the anchored content).

**Stability.** After concurrent or remote edits elsewhere in the sequence are applied, a relative position must resolve to the index of the same character it was anchored to, even when that character's absolute index has shifted. When the anchored character has been deleted, the position must resolve to the index where the removed range collapsed rather than returning `null`.

**Codecs and comparison.** `relativePositionToJSON(relPos)` and `createRelativePositionFromJSON(json)` round-trip a position through a JSON-compatible object; `compareRelativePositions(a, b)` must report `true` for a position and its JSON round trip. `encodeRelativePosition(relPos)` and `decodeRelativePosition(data)` round-trip through a `Uint8Array`; a binary round trip must resolve to the same absolute position as the original, though it is not required to compare equal through `compareRelativePositions`.

## State Model

The core state is one operation store per document: an append-only log of integrated operations attributed to `(clientID, clock)` pairs, together with tombstones for deletions. All public behavior is a projection of this store:

- **Content projection** — shared maps, arrays, and texts expose the store's current resolution through `get`/`toArray`/`toString`/`toDelta`/`toJSON`.
- **Update projection** — `encodeStateAsUpdate`/`applyUpdate` (v1 and v2) and the document's `"update"` events move store segments between replicas; state vectors describe coverage; `mergeUpdates`/`diffUpdate`/`encodeStateVectorFromUpdate` operate on encoded segments directly.
- **Event projection** — observers translate each transaction's store delta into per-key records and sequence deltas.
- **Undo projection** — the undo manager groups tracked store segments into entries and inverts them on demand.
- **Snapshot projection** — snapshots name a store version; restoration replays the store up to that version.
- **Position projection** — relative positions name a store location; resolution maps it to a current index.

A standalone shared type begins unintegrated (its `doc` is `null`), may buffer content, and becomes live when inserted into a document; root types are permanently bound to their document. Documents converge exactly when their stores contain the same operations; every projection above must agree between converged replicas.

## Error Semantics

All errors below are thrown synchronously as `Error` instances. Message wording is not contracted.

| Condition | Thrown |
|---|---|
| Root type accessor for a name already registered with a different type | `Error` |
| `insert` on a shared array with an index greater than the current length | `Error` |
| `delete` on a shared array addressing a range past the end | `Error` |
| Storing a non-representable value (for example a function) in a shared type | `Error` |
| Inserting an already-integrated shared type at a second location | `Error` |
| `applyUpdate`/`applyUpdateV2` with a malformed payload | `Error` |
| First access of an event's `changes` or `delta` after the handler returned | `Error` |
| `createDocFromSnapshot` on a document created with garbage collection enabled | `Error` |

## Cross-View Invariants

1. **Update-set determinism.** Any two documents that have received the same set of updates — in any order, grouping, or duplication — must expose identical content through every content projection: map `toJSON`, array `toArray`, and text `toString`/`toDelta` all agree between the replicas.
2. **Algebra preserves replay.** For any document history, applying `mergeUpdates` over its per-transaction updates, applying a `diffUpdate` on top of the state-vector-covered prefix, or replaying through the v2 format or a format conversion must each produce a replica whose content equals a replica that applied the original updates directly.
3. **Events describe the transaction.** For every transaction, the event projections must describe exactly the net change measured from the transaction's start state: replaying an array or text event `delta` against the pre-transaction content yields the post-transaction content, and each `changes.keys` record's `action`/`oldValue` matches the key's pre- and post-transaction values.
4. **Undo round trip respects provenance.** After interleaved tracked and untracked (or remote) transactions, `undo()` followed by content inspection must show untracked content intact and tracked content reverted, and `redo()` must restore the exact pre-undo content — on the local replica and, after update exchange, on every peer.
5. **Snapshots pin versions.** For a `gc: false` document, `createDocFromSnapshot` must produce content equal to what the content projections reported at snapshot time, `equalSnapshots` must distinguish versions with different content, and `snapshotContainsUpdate` must be consistent with the update's position in history.
6. **Positions track characters.** A relative position created at a character must, after any sequence of remote updates is applied, resolve to that character's current index — and the resolution must be identical whether the position traveled as a live object, as JSON, or as binary.
7. **State vectors measure coverage.** `encodeStateVectorFromUpdate(encodeStateAsUpdate(doc))` must describe the same coverage as `encodeStateVector(doc)`: diffs computed against either leave a receiving replica with identical content.

## Public Interface

### Import Surface

The package exposes a single module entry point with named exports; namespace import is the conventional style:

```ts
import * as Y from "yjs";

// equivalent named imports for the surface described in this document
import {
  Doc,
  Map,
  Array,
  Text,
  UndoManager,
  applyUpdate,
  applyUpdateV2,
  encodeStateAsUpdate,
  encodeStateAsUpdateV2,
  encodeStateVector,
  encodeStateVectorFromUpdate,
  mergeUpdates,
  diffUpdate,
  convertUpdateFormatV1ToV2,
  convertUpdateFormatV2ToV1,
  snapshot,
  encodeSnapshot,
  decodeSnapshot,
  equalSnapshots,
  createDocFromSnapshot,
  snapshotContainsUpdate,
  createRelativePositionFromTypeIndex,
  createRelativePositionFromJSON,
  relativePositionToJSON,
  encodeRelativePosition,
  decodeRelativePosition,
  createAbsolutePositionFromRelativePosition,
  compareRelativePositions,
} from "yjs";
```

The shared-type named exports `Map`, `Array`, and `Text` shadow the JavaScript globals of the same names; the namespace style (`Y.Map`, `Y.Array`, `Y.Text`) avoids the collision.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Doc` | class | One replica: holds root shared types, transactions, and update events. |
| `Map` | class | Shared key-value container with string keys. |
| `Array` | class | Shared index-addressed sequence; static `from` seeds one from items. |
| `Text` | class | Shared rich text with formatting attributes, embeds, and deltas. |
| `UndoManager` | class | Scoped, origin-aware undo/redo over shared types. |
| `applyUpdate` | function | Integrates a binary update into a document, optionally tagged with an origin. |
| `applyUpdateV2` | function | Same as `applyUpdate` for the alternate encoding. |
| `encodeStateAsUpdate` | function | Encodes a document's history, optionally only the part a state vector is missing. |
| `encodeStateAsUpdateV2` | function | Same as `encodeStateAsUpdate` for the alternate encoding. |
| `encodeStateVector` | function | Encodes a document's version descriptor. |
| `encodeStateVectorFromUpdate` | function | Computes the state vector covering an update payload. |
| `mergeUpdates` | function | Combines update payloads into one equivalent update. |
| `diffUpdate` | function | Extracts from an update the changes a state vector has not covered. |
| `convertUpdateFormatV1ToV2` | function | Translates an update payload to the alternate encoding. |
| `convertUpdateFormatV2ToV1` | function | Translates an alternate-encoding payload back. |
| `snapshot` | function | Captures a document's current version. |
| `encodeSnapshot` | function | Serializes a snapshot to binary. |
| `decodeSnapshot` | function | Restores a snapshot from binary. |
| `equalSnapshots` | function | Compares two snapshots for version equality. |
| `createDocFromSnapshot` | function | Builds a document containing a snapshot's content (requires `gc: false`). |
| `snapshotContainsUpdate` | function | Tests whether a snapshot covers an update's changes. |
| `createRelativePositionFromTypeIndex` | function | Anchors a stable position at a character index of a sequence type. |
| `createRelativePositionFromJSON` | function | Restores a relative position from its JSON form. |
| `relativePositionToJSON` | function | Converts a relative position to a JSON-compatible object. |
| `encodeRelativePosition` | function | Serializes a relative position to binary. |
| `decodeRelativePosition` | function | Restores a relative position from binary. |
| `createAbsolutePositionFromRelativePosition` | function | Resolves a relative position to a current index and type, or `null`. |
| `compareRelativePositions` | function | Tests two relative positions for equality. |

### CLI Entry Points

There is no console script for this package. Programmatic use is through module imports only.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. TypeScript sources are executed through a test runner that supports TypeScript natively; the package under construction must be importable as `yjs` from test files via standard Node module resolution (an installable package with a `package.json` whose exports resolve the module entry point).

No third-party runtime dependencies are available; the implementation must be self-contained. The assessment environment provides the same interpreter and module-resolution setup.

## Appendix B: Assessment Notes

Assessment exercises the documented behavior through the public module surface only. Dimensions covered include: document construction and root-type management, shared map/array/text semantics (values, iteration, conversion, bounds behavior, standalone construction and nesting), transaction batching and origins, update encoding and application in both formats (idempotency, order independence, buffering of out-of-order updates), update algebra without documents, observer events (per-key records, sequence deltas, deep observation paths, lazy-computation errors), undo/redo (capturing, tracked origins, remote preservation, stack-item events), snapshots (codecs, restoration, coverage tests), relative positions (stability, codecs, resolution), and the error conditions tabulated above. Tests assert observable values, reference identities, thrown error types, convergence between replicas, and cross-view equivalences; they do not assert error message wording, binary payload layout, or private state.
