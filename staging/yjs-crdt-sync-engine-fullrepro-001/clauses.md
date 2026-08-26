# Clause sidecar — yjs-crdt-sync-engine-fullrepro-001

Stable clause IDs for spec.md behavioral statements. Format: ID (§section): verbatim clause.

## Documents And Root Types

- YJS-DOC-001 (§Documents And Root Types): "A `Doc` accepts an optional options object with a `guid` (string identifier, randomly generated when omitted) and `gc` (boolean, defaults to `true`) controlling whether deleted content may be garbage-collected."
- YJS-DOC-002 (§Documents And Root Types): "Every document instance must carry a numeric `clientID`; two independently constructed documents must receive different `clientID` values."
- YJS-DOC-003 (§Documents And Root Types): "When a `guid` is supplied, the document's `guid` property must equal it."
- YJS-DOC-004 (§Documents And Root Types): "`getMap(name)`, `getArray(name)`, and `getText(name)` return the root shared type registered under `name`, creating it on first access. Repeated calls with the same name must return the same instance (reference identity)."
- YJS-DOC-005 (§Documents And Root Types): "If a root name already designated by one typed accessor is requested through an accessor of a different type, then the call must throw an `Error`."
- YJS-DOC-006 (§Documents And Root Types): "`doc.transact(fn, origin)` runs `fn` inside a single transaction and returns `fn`'s return value; the optional `origin` (any value) tags the transaction and is visible to observers."
- YJS-DOC-007 (§Documents And Root Types): "Mutations made outside an explicit `transact` call run in an implicit transaction with a `null` origin."
- YJS-DOC-008 (§Documents And Root Types): "When a `transact` call is nested inside another, the inner call must not open a new transaction: all mutations belong to the outermost transaction and produce a single change notification and a single update event."
- YJS-DOC-009 (§Documents And Root Types): "When a transaction completes without any effective change, the document must not emit an `\"update\"` event."
- YJS-DOC-010 (§Documents And Root Types): "The document emits an `\"update\"` event for every transaction that changed content. The handler is invoked with the encoded update (`Uint8Array`) describing exactly that transaction's changes, the transaction origin, the document, and the transaction object."
- YJS-DOC-011 (§Documents And Root Types): "Applying these per-transaction updates to a peer replica in order must reproduce the content changes."
- YJS-DOC-012 (§Documents And Root Types): "`destroy()` tears the document down and emits a `\"destroy\"` event; afterwards the document's `isDestroyed` property must be `true`."
- YJS-DOC-013 (§Documents And Root Types): "Event registration uses `on(name, handler)`, `off(name, handler)`, and `once(name, handler)` on the document."

## Shared Maps

- YJS-MAP-001 (§Shared Maps): "`set(key, value)` stores a value under a key and returns the value. `get(key)` returns the stored value, or `undefined` when the key is absent."
- YJS-MAP-002 (§Shared Maps): "`has(key)` reports presence, `delete(key)` removes an entry, `clear()` removes all entries, and the `size` property counts current entries."
- YJS-MAP-003 (§Shared Maps): "Storing `null` is allowed and must be preserved as `null` (distinct from an absent key)."
- YJS-MAP-004 (§Shared Maps): "Concurrent `set` calls to the same key on different replicas must converge: after exchanging updates, all replicas must report the same value for the key, and that value must be one of the concurrently written values."
- YJS-MAP-005 (§Shared Maps): "Plain objects and arrays are stored and replicated as plain values: after a round trip through update encoding, they must compare deeply equal and remain plain (not shared types)."
- YJS-MAP-006 (§Shared Maps): "`Uint8Array` values must survive replication as `Uint8Array` with identical bytes."
- YJS-MAP-007 (§Shared Maps): "If a value that cannot be represented — for example a function — is stored, then `set` must throw an `Error`."
- YJS-MAP-008 (§Shared Maps): "`keys()`, `values()`, and `entries()` return iterators that visit every current entry exactly once; `forEach(fn)` invokes `fn(value, key, map)` for each entry; the map itself is iterable over `[key, value]` pairs."
- YJS-MAP-009 (§Shared Maps): "`toJSON()` returns a plain object with one property per entry, converting nested shared types recursively to their JSON forms."
- YJS-MAP-010 (§Shared Maps): "`clone()` returns a new, unintegrated shared map holding the same entries."
- YJS-MAP-011 (§Shared Maps): "A standalone map is created with the `Map` constructor, optionally seeded from an iterable of entries."
- YJS-MAP-012 (§Shared Maps): "A standalone type may be mutated before it is integrated into a document; once inserted (for example via `parentMap.set(key, childType)`), the pre-integration content must be observable through the child."
- YJS-MAP-013 (§Shared Maps): "After integration, the child's `parent` property must be the containing type and its `doc` property the containing document; a root type's `parent` is `null`."
- YJS-MAP-014 (§Shared Maps): "A shared type instance must be integrated at most once: if an already-integrated type is inserted at a second location, then the call must throw."

## Shared Arrays

- YJS-ARR-001 (§Shared Arrays): "`insert(index, content)` inserts the items of the `content` array at `index`; `push(content)` appends and returns `undefined`; `unshift(content)` prepends."
- YJS-ARR-002 (§Shared Arrays): "`delete(index, length)` removes `length` consecutive items starting at `index` (the length defaults to 1)."
- YJS-ARR-003 (§Shared Arrays): "`get(index)` returns the item at an index, the `length` property counts items, and `slice(start, end)` returns a plain-array copy of the range with the usual end-exclusive semantics and optional arguments."
- YJS-ARR-004 (§Shared Arrays): "If `insert` targets an index greater than the current length, or `delete` addresses a range extending past the end, then the call must throw an `Error`."
- YJS-ARR-005 (§Shared Arrays): "`toArray()` returns a plain array of the current items; `toJSON()` does the same while converting nested shared types recursively."
- YJS-ARR-006 (§Shared Arrays): "`map(fn)` and `forEach(fn)` invoke `fn(item, index, array)`; the array itself is iterable in index order."
- YJS-ARR-007 (§Shared Arrays): "The static `Array.from(items)` builds a standalone shared array seeded with `items`."
- YJS-ARR-008 (§Shared Arrays): "The legal item values are the same as for shared maps, including nested shared types constructed standalone and integrated by insertion."
- YJS-ARR-009 (§Shared Arrays): "Concurrent insertions from different replicas must converge to the same sequence on all replicas after update exchange, with every inserted item preserved exactly once."

## Shared Text

- YJS-TXT-001 (§Shared Text): "`insert(index, text, attributes)` inserts a string at a character index, optionally formatted with an attributes object; when `index` exceeds the current length, the text must be appended at the end rather than throwing."
- YJS-TXT-002 (§Shared Text): "`delete(index, length)` removes a character range; a range extending past the end must be clamped to the available content rather than throwing."
- YJS-TXT-003 (§Shared Text): "`format(index, length, attributes)` applies formatting attributes to an existing range; an attribute set to `null` removes that attribute from the range."
- YJS-TXT-004 (§Shared Text): "`insertEmbed(index, embed, attributes)` inserts an embedded object (for example an image descriptor) that occupies exactly one unit of length."
- YJS-TXT-005 (§Shared Text): "The `length` property counts characters plus one per embed."
- YJS-TXT-006 (§Shared Text): "`toString()` returns the concatenated plain text, skipping embeds; `toJSON()` returns the same string."
- YJS-TXT-007 (§Shared Text): "`toDelta()` returns the rich content as an array of operation objects: each op is `{ insert }` carrying a string run or an embed object, plus an `attributes` object when the run is formatted; adjacent runs with identical formatting must be reported as a single op."
- YJS-TXT-008 (§Shared Text): "`applyDelta(ops)` applies an array of delta operations against the current content: `{ insert }` ops (with optional `attributes`) insert content at the running position, `{ retain }` ops skip over existing content — applying `attributes` on the retained range when present — and `{ delete }` ops remove content."
- YJS-TXT-009 (§Shared Text): "The delta projection must round-trip: the content after `applyDelta` must be observable through `toDelta`, `toString`, and `length` consistently."
- YJS-TXT-010 (§Shared Text): "A standalone text is created with the `Text` constructor, optionally seeded with an initial string that becomes observable once the type is integrated."
- YJS-TXT-011 (§Shared Text): "Concurrent inserts at the same position on different replicas must converge to the same character sequence on all replicas, with both inserted runs preserved intact (not interleaved character-by-character)."
- YJS-TXT-012 (§Shared Text): "Formatting applied on one replica must be visible in the `toDelta` projection of every replica after update exchange."

## Update Exchange

- YJS-UPD-001 (§Update Exchange): "`encodeStateAsUpdate(doc, encodedTargetStateVector)` returns a `Uint8Array` update covering the document's whole history, or — when the optional encoded state vector of a target replica is supplied — only the changes that replica has not seen."
- YJS-UPD-002 (§Update Exchange): "`applyUpdate(doc, update, origin)` integrates an update into a document; the optional `origin` tags the resulting transaction."
- YJS-UPD-003 (§Update Exchange): "`encodeStateVector(doc)` returns the document's version descriptor as a `Uint8Array`."
- YJS-UPD-004 (§Update Exchange): "If `applyUpdate` receives a malformed payload, then it must throw an `Error`."
- YJS-UPD-005 (§Update Exchange): "Applying the same update twice must leave the second application without effect (idempotency)."
- YJS-UPD-006 (§Update Exchange): "Applying a set of updates in any order and grouping must yield the same content on every replica (commutativity)."
- YJS-UPD-007 (§Update Exchange): "When an update depends on changes the receiving document has not yet seen, the document must buffer it without visible effect and integrate it automatically once the missing updates arrive."
- YJS-UPD-008 (§Update Exchange): "`mergeUpdates(updates)` combines an array of updates (in any order, tolerating overlap and duplicates) into one update that replays to the same content"
- YJS-UPD-009 (§Update Exchange): "`encodeStateVectorFromUpdate(update)` computes the state vector describing an update's coverage, equal to the state vector of a document that applied it"
- YJS-UPD-010 (§Update Exchange): "`diffUpdate(update, encodedStateVector)` extracts from an update only the changes not covered by the given state vector, such that applying the diff on top of the covered prefix reproduces the full content."
- YJS-UPD-011 (§Update Exchange): "A second binary format is available through `encodeStateAsUpdateV2(doc, encodedTargetStateVector)` and `applyUpdateV2(doc, update, origin)`."
- YJS-UPD-012 (§Update Exchange): "`convertUpdateFormatV1ToV2(update)` and `convertUpdateFormatV2ToV1(update)` translate payloads between the two formats. Replaying a document's history through either format, or through a conversion round trip, must produce identical content on the receiving replica."

## Events And Observation

- YJS-EVT-001 (§Events And Observation): "Every shared type supports `observe(handler)` and `unobserve(handler)`. The handler is invoked once per transaction that changed the type, receiving an event object and the transaction. After `unobserve`, the handler must not be invoked again."
- YJS-EVT-002 (§Events And Observation): "`observeDeep(handler)` (with `unobserveDeep`) additionally covers all nested shared types beneath the observed one: the handler receives an array of event objects — one per changed type — and the transaction."
- YJS-EVT-003 (§Events And Observation): "Every event exposes `target` (the changed shared type) and `path` (the route from the observed type to the target: map keys as strings and array indices as numbers)."
- YJS-EVT-004 (§Events And Observation): "Change descriptions are computed lazily and must be read inside the handler: if `changes` or `delta` is first accessed after the handler has returned, then the access must throw an `Error`."
- YJS-EVT-005 (§Events And Observation): "A map event's `changes.keys` is a JavaScript `Map` from each affected key to a record with an `action` (`\"add\"`, `\"update\"`, or `\"delete\"`) and an `oldValue`."
- YJS-EVT-006 (§Events And Observation): "The record describes the net effect of the whole transaction measured against its start state: a key that is set and then deleted inside one transaction reports a single `\"delete\"` with the pre-transaction value as `oldValue`, and a key that did not exist before reports `\"add\"` with an `oldValue` of `undefined`."
- YJS-EVT-007 (§Events And Observation): "The event's `keysChanged` set names the affected keys."
- YJS-EVT-008 (§Events And Observation): "Array and text events expose `delta`: an array of `{ retain }`, `{ insert }`, and `{ delete }` operations describing the transaction's net change against the pre-transaction sequence."
- YJS-EVT-009 (§Events And Observation): "For text events, `insert` carries strings (with `attributes` for formatted runs); for array events, `insert` carries an array of inserted items."
- YJS-EVT-010 (§Events And Observation): "The transaction passed to observers and document events exposes `origin` (the tag given to `transact` or `applyUpdate`, `null` for untagged local edits) and `local` (`true` for transactions created by local mutations, `false` for transactions created by applying updates)."
- YJS-EVT-011 (§Events And Observation): "Remote and local changes must fire the same observers with the same event shapes."

## Undo And Redo

- YJS-UNDO-001 (§Undo And Redo): "`UndoManager` is constructed with a scope — one shared type or an array of shared types — and an options object supporting `captureTimeout` (milliseconds, default 500) and `trackedOrigins` (a `Set` of origins). Only changes to the scoped types are tracked and reverted."
- YJS-UNDO-002 (§Undo And Redo): "By default, only transactions with a `null` origin (untagged local edits) are tracked; when `trackedOrigins` is supplied, exactly the transactions whose origin is in the set are tracked, and untagged edits are tracked only if `null` is in the set."
- YJS-UNDO-003 (§Undo And Redo): "Tracked transactions that occur within `captureTimeout` of each other merge into a single undo entry; a `captureTimeout` of 0 keeps every transaction as its own entry."
- YJS-UNDO-004 (§Undo And Redo): "`stopCapturing()` ends the current entry so the next tracked change starts a new one, regardless of timing."
- YJS-UNDO-005 (§Undo And Redo): "`undo()` reverts the most recent undo entry; `redo()` re-applies the most recently undone entry."
- YJS-UNDO-006 (§Undo And Redo): "`canUndo()` and `canRedo()` report whether entries are available, and `clear()` empties both stacks."
- YJS-UNDO-007 (§Undo And Redo): "A new tracked change after an undo must clear the redo stack."
- YJS-UNDO-008 (§Undo And Redo): "Undoing a map change must restore the previous value of each affected key (or its absence)."
- YJS-UNDO-009 (§Undo And Redo): "Undoing must revert only tracked changes: content produced by untracked or remote transactions interleaved with the tracked ones must survive an undo, and a subsequent redo must restore exactly the undone content."
- YJS-UNDO-010 (§Undo And Redo): "The manager emits `\"stack-item-added\"` when an entry is created (and when an undo pushes the corresponding redo entry) and `\"stack-item-popped\"` when an entry is applied. Handlers receive an event with the `stackItem` and a `type` field (`\"undo\"` or `\"redo\"`)."
- YJS-UNDO-011 (§Undo And Redo): "Each stack item carries a `meta` property — a JavaScript `Map` for arbitrary user data — and the meta content attached when an item is added must be readable when the same item is popped."

## Snapshots

- YJS-SNAP-001 (§Snapshots): "`snapshot(doc)` returns a snapshot describing the document's current version."
- YJS-SNAP-002 (§Snapshots): "`encodeSnapshot(snapshot)` serializes it to a `Uint8Array` and `decodeSnapshot(data)` restores it; `equalSnapshots(a, b)` reports whether two snapshots describe the same version."
- YJS-SNAP-003 (§Snapshots): "A decode of an encode must compare equal to the original, and snapshots taken before and after a content change must compare unequal."
- YJS-SNAP-004 (§Snapshots): "`createDocFromSnapshot(originDoc, snapshot)` builds a new document whose shared types contain exactly the content the origin document had when the snapshot was taken."
- YJS-SNAP-005 (§Snapshots): "if the origin document was created with garbage collection enabled (the default `gc: true`), then `createDocFromSnapshot` must throw an `Error`"
- YJS-SNAP-006 (§Snapshots): "`snapshotContainsUpdate(snapshot, update)` returns `true` exactly when every change carried by the update is covered by the snapshot's version: it must return `true` for a snapshot taken after the update's changes and `false` for a snapshot taken before them."

## Relative Positions

- YJS-POS-001 (§Relative Positions): "`createRelativePositionFromTypeIndex(type, index, assoc)` creates a position anchored at a character index of a sequence type; the optional `assoc` (default 0) associates the position with the character to the right, or with the character to the left when negative."
- YJS-POS-002 (§Relative Positions): "`createAbsolutePositionFromRelativePosition(relPos, doc)` resolves a relative position against a document, returning an object with `index` (the current character index) and `type` (the resolved shared type, reference-identical to the anchored type) — or `null` when the position cannot be resolved in that document (for example against an unrelated replica that never saw the anchored content)."
- YJS-POS-003 (§Relative Positions): "After concurrent or remote edits elsewhere in the sequence are applied, a relative position must resolve to the index of the same character it was anchored to, even when that character's absolute index has shifted."
- YJS-POS-004 (§Relative Positions): "When the anchored character has been deleted, the position must resolve to the index where the removed range collapsed rather than returning `null`."
- YJS-POS-005 (§Relative Positions): "`relativePositionToJSON(relPos)` and `createRelativePositionFromJSON(json)` round-trip a position through a JSON-compatible object; `compareRelativePositions(a, b)` must report `true` for a position and its JSON round trip."
- YJS-POS-006 (§Relative Positions): "`encodeRelativePosition(relPos)` and `decodeRelativePosition(data)` round-trip through a `Uint8Array`; a binary round trip must resolve to the same absolute position as the original, though it is not required to compare equal through `compareRelativePositions`."

## Error Semantics

- YJS-ERR-001 (§Error Semantics): "Root type accessor for a name already registered with a different type -> Error"
- YJS-ERR-002 (§Error Semantics): "`insert` on a shared array with an index greater than the current length -> Error"
- YJS-ERR-003 (§Error Semantics): "`delete` on a shared array addressing a range past the end -> Error"
- YJS-ERR-004 (§Error Semantics): "Storing a non-representable value (for example a function) in a shared type -> Error"
- YJS-ERR-005 (§Error Semantics): "Inserting an already-integrated shared type at a second location -> Error"
- YJS-ERR-006 (§Error Semantics): "`applyUpdate`/`applyUpdateV2` with a malformed payload -> Error"
- YJS-ERR-007 (§Error Semantics): "First access of an event's `changes` or `delta` after the handler returned -> Error"
- YJS-ERR-008 (§Error Semantics): "`createDocFromSnapshot` on a document created with garbage collection enabled -> Error"

## Cross-View Invariants

- YJS-CVI-001 (§Cross-View Invariants): "Any two documents that have received the same set of updates — in any order, grouping, or duplication — must expose identical content through every content projection: map `toJSON`, array `toArray`, and text `toString`/`toDelta` all agree between the replicas."
- YJS-CVI-002 (§Cross-View Invariants): "For any document history, applying `mergeUpdates` over its per-transaction updates, applying a `diffUpdate` on top of the state-vector-covered prefix, or replaying through the v2 format or a format conversion must each produce a replica whose content equals a replica that applied the original updates directly."
- YJS-CVI-003 (§Cross-View Invariants): "For every transaction, the event projections must describe exactly the net change measured from the transaction's start state: replaying an array or text event `delta` against the pre-transaction content yields the post-transaction content, and each `changes.keys` record's `action`/`oldValue` matches the key's pre- and post-transaction values."
- YJS-CVI-004 (§Cross-View Invariants): "After interleaved tracked and untracked (or remote) transactions, `undo()` followed by content inspection must show untracked content intact and tracked content reverted, and `redo()` must restore the exact pre-undo content — on the local replica and, after update exchange, on every peer."
- YJS-CVI-005 (§Cross-View Invariants): "For a `gc: false` document, `createDocFromSnapshot` must produce content equal to what the content projections reported at snapshot time, `equalSnapshots` must distinguish versions with different content, and `snapshotContainsUpdate` must be consistent with the update's position in history."
- YJS-CVI-006 (§Cross-View Invariants): "A relative position created at a character must, after any sequence of remote updates is applied, resolve to that character's current index — and the resolution must be identical whether the position traveled as a live object, as JSON, or as binary."
- YJS-CVI-007 (§Cross-View Invariants): "`encodeStateVectorFromUpdate(encodeStateAsUpdate(doc))` must describe the same coverage as `encodeStateVector(doc)`: diffs computed against either leave a receiving replica with identical content."
