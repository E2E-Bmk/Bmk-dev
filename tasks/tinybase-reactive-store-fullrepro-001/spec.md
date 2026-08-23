# TinyBase Reactive Store Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`tinybase` is a JavaScript and TypeScript reactive in-memory data store that maintains key-value data, tabular data, schemas, listeners, derived views, query results, undo checkpoints, mutation middleware, and mergeable conflict-resolution metadata.

The package centers on a `Store` object. A store exposes its state as two projections: `Tables` for nested table-row-cell data, and `Values` for top-level keyed values. Derived objects such as `Metrics`, `Indexes`, `Relationships`, `Queries`, and `Checkpoints` attach to a store, recompute from store mutations, and expose listeners for their own projections.

## Non-Goals

- This specification does not require browser UI bindings, React components, Solid primitives, Svelte components, DOM table views, chart components, or inspector overlays.
- This specification does not require filesystem, browser storage, database, CRDT document, WebSocket, BroadcastChannel, PartyKit, or remote HTTP persistence.
- This specification does not require schema adapter modules for Zod, TypeBox, Valibot, ArkType, Yup, or Effect.
- This specification does not define private modules, private fields, internal helper names, generated build files, or exact object freezing mechanics.
- This specification does not define exact human-readable error messages, stack traces, listener identifier text, hash implementation internals, or performance characteristics.
- This specification does not require a command-line program.

## Representative Workflows

### Store Data And React To Changes

```ts
import { createStore } from "tinybase";

const store = createStore()
  .setValues({ open: true, employees: 3 })
  .setTable("pets", { fido: { species: "dog" } });

const events: string[] = [];
const listenerId = store.addCellListener("pets", "fido", "color", () => {
  events.push(String(store.getCell("pets", "fido", "color")));
});

store.setCell("pets", "fido", "color", "brown");
store.delListener(listenerId);
```

The store mutation writes tabular data, calls matching listeners after the transaction has finished, and leaves the value projection unchanged.

### Maintain Derived Views

```ts
import { createIndexes, createMetrics, createRelationships, createStore } from "tinybase";

const store = createStore().setTable("pets", {
  fido: { species: "dog", ownerId: "1", price: 5 },
  rex: { species: "dog", ownerId: "2", price: 4 },
  felix: { species: "cat", ownerId: "2", price: 3 },
});

const metrics = createMetrics(store).setMetricDefinition("highestPrice", "pets", "max", "price");
const indexes = createIndexes(store).setIndexDefinition("bySpecies", "pets", "species");
const relationships = createRelationships(store).setRelationshipDefinition("owners", "pets", "owners", "ownerId");

store.setCell("pets", "polly", "species", "parrot");
```

Each derived object reads from the same store. The metric, index, and relationship projections update when the underlying rows or cells change.

### Query Results And Undo Points

```ts
import { createCheckpoints, createQueries, createStore } from "tinybase";

const store = createStore().setTable("pets", {
  fido: { species: "dog", price: 5 },
  rex: { species: "dog", price: 4 },
});

const queries = createQueries(store).setQueryDefinition("prices", "pets", ({ select, group }) => {
  select("species");
  group("price", "avg").as("avgPrice");
});
const checkpoints = createCheckpoints(store);
const before = checkpoints.addCheckpoint("before edit");

store.setCell("pets", "fido", "price", 7);
checkpoints.goTo(before);
```

Query results are a reactive projection of store rows. Checkpoints record reversible store deltas and restore the store to a previous checkpoint when navigation succeeds.

## Store Content And Schemas

The store content API owns the base state that every other object observes.

**Content Shape.** The store must represent content as `[tables, values]`. `Tables` must be an object keyed by table id, each table must be keyed by row id, and each row must be keyed by cell id. `Values` must be an object keyed by value id. A `Cell` or `Value` must be a string, number, boolean, `null`, plain object, or array. Missing tables, rows, cells, and values must be reported as empty collections or `undefined` according to the accessor being called.

**Creation And Reading.** `createStore` must return an empty `Store`. `getContent`, `getTables`, `getTableIds`, `getTable`, `getTableCellIds`, `getRowCount`, `getRowIds`, `getSortedRowIds`, `getRow`, `getCellIds`, `getCell`, `getValues`, `getValueIds`, and `getValue` must return clones or primitive values that reflect the current content. `hasTables`, `hasTable`, `hasTableCell`, `hasRow`, `hasCell`, `hasValues`, and `hasValue` must return boolean existence projections for the same content.

**Writing And Deleting.** `setContent`, `setTables`, `setTable`, `setRow`, `setPartialRow`, `setCell`, `setValues`, `setPartialValues`, and `setValue` must mutate the relevant projection and return the store for fluent chaining, except that `addRow` returns the assigned row id or `undefined` when no id is available. `setCell` and `setValue` must accept either a direct value or a mapping callback that receives the current value and returns the new value. `delTables`, `delTable`, `delRow`, `delCell`, `delValues`, and `delValue` must remove the named projection and return the store.

**Identifier Ordering And Sorting.** Id-list accessors must return ids in store insertion order unless a sorting method is used. `getSortedRowIds` must sort row ids by a selected cell value when `cellId` is supplied, or by row id when it is not supplied. The `descending`, `offset`, `limit`, and `sorter` inputs must control reverse ordering, slicing, and custom comparison. A missing sort cell must participate as `undefined` in the comparison.

**JSON Projections.** `getTablesJson`, `getValuesJson`, and `getJson` must serialize tables, values, or the full `[tables, values]` content to JSON strings. `setTablesJson`, `setValuesJson`, and `setJson` must parse JSON strings and apply the corresponding projection. If a JSON string is malformed or does not describe valid content, then the method must leave existing valid content unchanged and must not expose partially applied state.

**Schemas And Defaults.** `setTablesSchema`, `setValuesSchema`, and `setSchema` must install schema definitions for table cells and values. Schema definitions must accept `type`, `default`, `allowNull`, and `values` constraints. When valid content omits a schema-defined item with a default, reads and stored content must expose the defaulted value. When a value violates an installed schema, the store must reject the invalid value, keep the previous valid projection, and call matching invalid listeners. `delTablesSchema`, `delValuesSchema`, and `delSchema` must remove the corresponding schema constraints.

## Store Transactions And Listeners

The reactive API reports content changes through granular listeners and transaction boundaries.

**Transactions.** `transaction` must execute an action inside a single mutation boundary and return the action result. `startTransaction` and `finishTransaction` must open and close an explicit transaction. `getTransactionChanges` must return the accumulated table and value changes for the active or most recently finishing transaction, and `getTransactionLog` must return a log with old and new values. When a rollback callback returns `true`, the store must restore the pre-transaction content and still finish the transaction consistently.

**Listener Matching.** Listener registration methods must return listener ids accepted by `delListener` and `callListener`. `addTablesListener`, `addTableListener`, `addRowListener`, `addCellListener`, `addValuesListener`, and `addValueListener` must call listeners after matching content changes. The `Has*`, `Ids`, `RowCount`, `SortedRowIds`, `CellIds`, `InvalidCell`, `InvalidValue`, `StartTransaction`, `WillFinishTransaction`, and `DidFinishTransaction` listener families must observe the projection named by their method. A listener registered with `null` id arguments must match all ids at that position.

**Mutator Listeners.** When a listener is registered with `mutator` set to true, mutations performed by that listener must be treated as part of the same notification cycle. Non-mutator listeners must observe the stable post-mutation state. Recursive listener activity must not leave the store in a partially notified state.

**Iteration.** `forEachTable`, `forEachTableCell`, `forEachRow`, `forEachCell`, and `forEachValue` must iterate over the current projection using callbacks with the documented ids and values. Mutations performed during iteration must not corrupt the iteration of already selected entries.

**Listener Lifecycle.** `delListener` must remove a listener id so later matching changes no longer call it. `callListener` must immediately call the registered listener against the current projection. `getListenerStats` must return counts grouped by listener family. Deleting an unknown listener id must leave the object usable.

## Derived Views

Derived objects attach to one store and maintain deterministic projections over that store.

**Metrics.** `createMetrics` must attach a `Metrics` object to a store. `setMetricDefinition` must define a metric over one table using `sum` when the aggregate is omitted, or using `sum`, `avg`, `min`, `max`, or a custom aggregate when supplied. The number source must be either a cell id or a callback over a row. Non-finite, boolean, empty-string, missing, and non-numeric values must be excluded from the numeric aggregation. `getMetricIds`, `hasMetric`, `getTableId`, `getMetric`, `forEachMetric`, `addMetricIdsListener`, and `addMetricListener` must expose and observe the metric projection. `delMetricDefinition` must remove the definition and derived value.

**Indexes.** `createIndexes` must attach an `Indexes` object to a store. `setIndexDefinition` must group rows from one table into slices. The slice source must be a cell id or a callback returning one slice id or several slice ids. A missing slice value must use the empty string slice id. `getSortKey`, `sliceIdSorter`, and `rowIdSorter` must control slice ordering and row ordering. `getSliceIds`, `getSliceRowIds`, `hasIndex`, `hasSlice`, `forEachIndex`, `forEachSlice`, and listener methods must expose the same index projection. `delIndexDefinition` must remove the definition and projection.

**Relationships.** `createRelationships` must attach a `Relationships` object to a store. `setRelationshipDefinition` must define a link from a local table to a remote table using a remote row id cell or callback. `getRemoteRowId` must return the remote row id for a local row. `getLocalRowIds` must return all local rows linked to a remote row. `getLinkedRowIds` must follow a same-table chain from the first row until no remote row exists or a cycle is reached; for cross-table relationships it must return the first row id. Relationship ids, local table ids, remote table ids, and listeners must update when the definition or source cells change. `delRelationshipDefinition` must remove the definition and projection.

**Queries.** `createQueries` must attach a `Queries` object to a store. `setQueryDefinition` must define a result table from a source table with builder functions named `select`, `selectAll`, `join`, `where`, `group`, `having`, and `param`. Selected cells must form result rows, joins must resolve related source rows, `where` must filter source rows, `group` must aggregate selected cells, and `having` must filter grouped result rows. `getResultTable`, `getResultTableCellIds`, `getResultRowCount`, `getResultRowIds`, `getResultSortedRowIds`, `getResultRow`, `getResultCellIds`, `getResultCell`, `hasResultTable`, `hasResultRow`, `hasResultCell`, and result listener methods must expose the result store projection. `setParamValues` and `setParamValue` must update parameter values and recompute dependent queries. `delQueryDefinition` must remove the definition and projection.

**Derived Lifecycle.** Each derived object must return the source store from `getStore`. `destroy` must detach store listeners so later store mutations no longer update that object or call its listeners. `delListener` must remove derived listeners. `getListenerStats` must report listener counts for that derived object.

## Checkpoints, Middleware, And Mergeable Stores

State-management helpers extend a store with undo, mutation interception, and merge semantics.

**Checkpoints.** `createCheckpoints` must track reversible deltas for one store. `addCheckpoint` must create or reuse the current checkpoint and store its optional label. `getCheckpointIds` must return `[backwardIds, currentId, forwardIds]`. `goBackward`, `goForward`, and `goTo` must restore the store content associated with the target checkpoint when navigation is possible and must leave content unchanged when it is not possible. `setSize` must limit the number of backward checkpoints retained. `clear`, `clearForward`, `setCheckpoint`, `getCheckpoint`, `hasCheckpoint`, `forEachCheckpoint`, listeners, `destroy`, and `getListenerStats` must expose the checkpoint projection.

**Middleware.** `createMiddleware` must attach mutation callbacks to one store. `addWillSetContentCallback`, `addWillSetTablesCallback`, `addWillSetTableCallback`, `addWillSetRowCallback`, `addWillSetCellCallback`, `addWillSetValuesCallback`, `addWillSetValueCallback`, and `addWillApplyChangesCallback` must run before the matching write and must replace the pending value with the callback result. If a set callback returns `undefined`, then the pending write must be rejected. `addWillDelTablesCallback`, `addWillDelTableCallback`, `addWillDelRowCallback`, `addWillDelCellCallback`, `addWillDelValuesCallback`, and `addWillDelValueCallback` must run before the matching deletion; deletion must proceed only when every matching callback returns true. `destroy` must detach all middleware callbacks.

**Mergeable Stores.** `createMergeableStore` must return a `MergeableStore` that also satisfies the `Store` contract. `isMergeable` must return true for mergeable stores and false for ordinary stores. A mergeable store must maintain hybrid logical clock stamps for tables, rows, cells, and values. `getMergeableContent`, hash accessors, and diff accessors must expose mergeable content and only the portions that differ from supplied hashes. `setMergeableContent` must replace the mergeable content when the supplied stamps are valid. `setDefaultContent` must install content without treating it as local user mutation. `merge` must reconcile another mergeable store so later stamps win deterministically and deletion stamps remove older values.

## Common Utilities

Utility exports provide deterministic ids, sorting, hashes, and hybrid logical clocks used by store projections.

**Sorting And Ids.** `defaultSorter` must compare two sort keys with stable ordering for strings, numbers, booleans, `null`, arrays, objects, and `undefined`. `getUniqueId` must return a string id of the requested length, using a default length when omitted, and repeated calls must not deliberately reuse ids.

**Hashes.** `getHash` must return a deterministic numeric hash for a string. `addOrRemoveHash` must combine two hash values so applying the same second hash twice restores the first hash. `getTablesHash`, `getTableInTablesHash`, `getTableHash`, `getRowInTableHash`, `getRowHash`, `getCellInRowHash`, `getCellHash`, `getValuesHash`, `getValueInValuesHash`, and `getValueHash` must produce deterministic hashes for the corresponding projections.

**Hybrid Logical Clocks.** `getHlcFunctions` must return functions for generating and observing HLC strings. Generated HLC strings must be monotonic for one function pair. Observing a valid external HLC must advance later generated HLC values beyond that timestamp. If a generated or observed HLC is invalid or too far in the future, then the HLC helper must raise an `Error`.

## State Model

The core state is an in-memory content tuple `[tables, values]`, plus optional schema definitions and a transaction frame while a transaction is active.

The public projections of this state are:

- Store readers and JSON readers for tables, rows, cells, values, schemas, and full content.
- Store mutation methods, transaction changes, transaction logs, iteration callbacks, and listener families.
- Derived projections from metrics, indexes, relationships, queries, and checkpoints.
- Middleware callbacks that transform or reject pending writes and deletions.
- Mergeable content stamps, hashes, diffs, and merge results.
- Common utility outputs for ids, sorting, hashes, and HLC timestamps.

## Error Semantics

| Condition | Required result |
|---|---|
| A JSON setter receives malformed JSON or JSON with an invalid content shape | The method must leave prior valid state unchanged and must not expose partial content. |
| A write violates an installed table or values schema | The invalid item must be rejected, prior valid data must remain visible, and matching invalid listeners must be called. |
| A mapping callback or listener throws | The exception must propagate through the initiating call after transaction cleanup has completed. |
| A rollback callback returns true at transaction finish | The transaction must restore the pre-transaction content and still call finish listeners with rollback state. |
| A query definition contains a `selectAll` cycle whose mapped cells depend on the same query result | `setQueryDefinition` must raise an `Error`. |
| A mergeable content setter receives an invalid stamp structure or invalid HLC | The mergeable store must reject it and keep existing mergeable content. |
| An HLC helper observes or generates an invalid timestamp | The helper must raise an `Error`. |
| A deletion or listener removal names a missing id | The method must leave the object usable and must not raise solely because the id is absent. |

## Cross-View Invariants

1. A value written with `setValue` must appear in `getValues`, `getValueIds`, `getValue`, `getJson`, value listeners, and transaction changes until it is deleted.
2. A cell written with `setCell` must appear in `getTables`, `getTable`, `getRow`, `getCellIds`, `getCell`, `getSortedRowIds`, table listeners, row listeners, cell listeners, and transaction changes until it is deleted.
3. Schema defaults must be visible through ordinary readers, JSON readers, listeners, derived views, and transaction logs as the same value.
4. A store mutation that changes a metric's source rows must update `getMetric`, metric listeners, and `forEachMetric` consistently.
5. A store mutation that changes an index's slice source or sort key must update `getSliceIds`, `getSliceRowIds`, slice listeners, and index iteration consistently.
6. A store mutation that changes a relationship's remote row id source must update `getRemoteRowId`, `getLocalRowIds`, `getLinkedRowIds`, and relationship listeners consistently.
7. A store mutation that changes rows used by a query must update result table readers, sorted result row ids, parameter-sensitive results, and result listeners consistently.
8. Navigating checkpoints must restore the store projection observed by store readers and must cause dependent metrics, indexes, relationships, and queries to reflect the restored content.
9. Middleware that transforms a write must affect the store readers, JSON projections, listeners, transaction logs, and derived views as if the transformed value had been supplied directly.
10. Merging two mergeable stores must produce store content readers, mergeable content, hashes, and later diffs that agree on the same resolved cells and values.

## Public Interface

### Import Surface

```ts
import {
  createStore,
  createMergeableStore,
  createMetrics,
  createIndexes,
  createRelationships,
  createQueries,
  createCheckpoints,
  createMiddleware,
  defaultSorter,
  getUniqueId,
  getHlcFunctions,
  getHash,
  addOrRemoveHash,
  getTablesHash,
  getTableInTablesHash,
  getTableHash,
  getRowInTableHash,
  getRowHash,
  getCellInRowHash,
  getCellHash,
  getValuesHash,
  getValueInValuesHash,
  getValueHash,
} from "tinybase";

import { createStore as createStoreFromStore } from "tinybase/store";
import { createMergeableStore as createMergeableStoreFromModule } from "tinybase/mergeable-store";
import { createMetrics as createMetricsFromModule } from "tinybase/metrics";
import { createIndexes as createIndexesFromModule } from "tinybase/indexes";
import { createRelationships as createRelationshipsFromModule } from "tinybase/relationships";
import { createQueries as createQueriesFromModule } from "tinybase/queries";
import { createCheckpoints as createCheckpointsFromModule } from "tinybase/checkpoints";
import { createMiddleware as createMiddlewareFromModule } from "tinybase/middleware";
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `createStore` | function | Creates an empty reactive store for table and value content. |
| `Store` | interface | Exposes readers, writers, JSON projections, schemas, transactions, iteration, and listeners for base content. |
| `createMergeableStore` | function | Creates a store with mergeable CRDT-style stamp metadata. |
| `MergeableStore` | interface | Extends store behavior with mergeable content, hash, diff, default-content, and merge operations. |
| `createMetrics` | function | Creates derived numeric aggregations from rows in a store table. |
| `Metrics` | interface | Exposes metric definitions, values, iteration, listeners, lifecycle, and listener statistics. |
| `createIndexes` | function | Creates derived slice-to-row-id indexes from rows in a store table. |
| `Indexes` | interface | Exposes index definitions, slice ids, slice row ids, iteration, listeners, lifecycle, and listener statistics. |
| `createRelationships` | function | Creates derived local-to-remote row relationships from store tables. |
| `Relationships` | interface | Exposes relationship definitions, remote row ids, local row ids, linked row chains, listeners, lifecycle, and listener statistics. |
| `createQueries` | function | Creates reactive result tables from query definitions over store tables. |
| `Queries` | interface | Exposes query definitions, parameter values, result readers, result listeners, lifecycle, and listener statistics. |
| `createCheckpoints` | function | Creates undo and redo checkpoint state for a store. |
| `Checkpoints` | interface | Exposes checkpoint creation, labels, navigation, clearing, listeners, lifecycle, and listener statistics. |
| `createMiddleware` | function | Creates mutation callbacks that transform or reject store writes and deletions. |
| `Middleware` | interface | Exposes middleware callback registration, source-store access, and lifecycle. |
| `defaultSorter` | function | Provides the default comparison used by sorted row id readers. |
| `getUniqueId` | function | Generates string ids for listener ids and row ids. |
| `getHlcFunctions` | function | Creates HLC generation and observation helpers. |
| `getHash` | function | Hashes strings for mergeable projections. |
| `addOrRemoveHash` | function | Combines hash values reversibly. |
| `getTablesHash` | function | Computes a hash for a tables projection from table hashes. |
| `getTableInTablesHash` | function | Computes a table contribution inside a tables hash. |
| `getTableHash` | function | Computes a table hash from row hashes. |
| `getRowInTableHash` | function | Computes a row contribution inside a table hash. |
| `getRowHash` | function | Computes a row hash from cell hashes. |
| `getCellInRowHash` | function | Computes a cell contribution inside a row hash. |
| `getCellHash` | function | Computes a hash for one cell and its HLC. |
| `getValuesHash` | function | Computes a hash for a values projection from value hashes. |
| `getValueInValuesHash` | function | Computes a value contribution inside a values hash. |
| `getValueHash` | function | Computes a hash for one value and its HLC. |

### CLI Entry Points

There is no console script for this package. Programmatic use is through ECMAScript module imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Debian Linux without network access during behavioral checks. The assessment environment provides TypeScript, Vitest, and tsx as installable dependencies. The target `tinybase` module and its subpath modules are not preinstalled from a registry.

The project must declare ECMAScript module mode, exported module entry points, and every runtime dependency in `package.json`. Each module entry point listed above must be reachable after a local install.

## Appendix B: Assessment Notes

Assessment checks cover store content readers and writers, schemas and defaults, transaction rollback, listener matching, JSON projections, metrics, indexes, relationships, queries, checkpoints, middleware, mergeable content, common utilities, import surfaces, and cross-view consistency. Checks compare structured values and observable state transitions; they do not require private module layout, exact error text, exact listener id text, optional UI packages, external storage systems, or network services.
