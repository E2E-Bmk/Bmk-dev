# table-core Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`@tanstack/table-core` is a headless table engine that turns an array of data records and a list of column definitions into every projection a table UI needs: a staged row-model pipeline (filtering, grouping, sorting, expanding, pagination), a column tree with visibility, ordering, and pinning, a header/footer group matrix with spans and placeholders, and per-row projections such as cells, selection flags, and expansion state. It renders nothing itself; callers read the projections and draw them with any UI layer.

The engine is assembled from explicit building blocks. A table is constructed from a composed bag of features, row-model factories, and named function registries, and holds its state in a graph of reactive atoms — one atom per registered state slice — with a combined snapshot store on top. Only what a caller registers exists: an unregistered feature contributes no state slice and no APIs, an unregistered row-model factory makes its pipeline stage a pass-through, and an unregistered sorting/filtering/aggregation function cannot be referenced by name.

The installable package name is `@tanstack/table-core`. All functionality is reachable through named exports of the package root, except the store reactivity bindings, which are exported from the subpath `@tanstack/table-core/store-reactivity-bindings`.

## Non-Goals

- This specification does not require column sizing or interactive column resizing.
- This specification does not require row pinning, cell-level selection, or cell spanning.
- This specification does not require web-worker execution, table serialization across threads, or devtools integration.
- This specification does not require rendering helpers, framework adapters, or DOM event handler factories beyond the state APIs described here.
- This specification does not require wrapping externally supplied atoms passed through table options, or reactivity schedulers other than the store bindings described here.
- This specification does not define right-to-left layout interpretation; pinning regions are named `start` and `end` and carry no directional meaning of their own.

## Representative Workflows

**Filter, sort, and paginate a data set.** A table is constructed with the features and row-model factories it needs, plus the built-in function registries. State transitions go through setters; projections are read back from row models:

```ts
import {
  constructTable,
  tableFeatures,
  createCoreRowModel,
  createFilteredRowModel,
  createSortedRowModel,
  createPaginatedRowModel,
  columnFilteringFeature,
  rowSortingFeature,
  rowPaginationFeature,
  filterFns,
  sortFns,
} from "@tanstack/table-core";
import { storeReactivityBindings } from "@tanstack/table-core/store-reactivity-bindings";

const table = constructTable({
  features: tableFeatures({
    coreReactivityFeature: storeReactivityBindings(),
    columnFilteringFeature,
    rowSortingFeature,
    rowPaginationFeature,
    coreRowModel: createCoreRowModel(),
    filteredRowModel: createFilteredRowModel(),
    sortedRowModel: createSortedRowModel(),
    paginatedRowModel: createPaginatedRowModel(),
    filterFns,
    sortFns,
  }),
  columns: [{ accessorKey: "name" }, { accessorKey: "qty" }],
  data: [
    { name: "beet", qty: 4 },
    { name: "apple", qty: 2 },
    { name: "cherry", qty: 9 },
  ],
});

table.setColumnFilters([{ id: "qty", value: [2, 9] }]);
table.setSorting([{ id: "name", desc: false }]);
const pageRows = table.getRowModel().rows; // filtered, sorted, first page
const names = pageRows.map((row) => row.getValue("name"));
```

**Group, aggregate, and expand.** Grouping replaces leaf rows with group rows; aggregation summarizes leaf values; expansion surfaces children:

```ts
import {
  constructTable,
  tableFeatures,
  createCoreRowModel,
  createGroupedRowModel,
  createExpandedRowModel,
  columnGroupingFeature,
  rowAggregationFeature,
  rowExpandingFeature,
  aggregationFns,
} from "@tanstack/table-core";
import { storeReactivityBindings } from "@tanstack/table-core/store-reactivity-bindings";

const table = constructTable({
  features: tableFeatures({
    coreReactivityFeature: storeReactivityBindings(),
    columnGroupingFeature,
    rowAggregationFeature,
    rowExpandingFeature,
    coreRowModel: createCoreRowModel(),
    groupedRowModel: createGroupedRowModel(),
    expandedRowModel: createExpandedRowModel(),
    aggregationFns,
  }),
  columns: [
    { accessorKey: "cat" },
    { accessorKey: "qty", aggregationFn: "sum" },
  ],
  data: [
    { cat: "fruit", qty: 5 },
    { cat: "veg", qty: 2 },
    { cat: "fruit", qty: 8 },
  ],
});

table.setGrouping(["cat"]);
const groups = table.getGroupedRowModel().rows;   // one group row per distinct cat
const fruitTotal = groups[0].getValue("qty");     // 13 via the "sum" aggregation
groups[0].toggleExpanded();                       // leaf rows surface beneath the group
```

## Table Construction And Feature Composition

Every capability of a table is declared at construction; the engine has no global registry and no implicit defaults beyond what registered features contribute. `constructTable` accepts a table options object and returns the table instance. The options object must carry a `features` value produced by `tableFeatures`, a `columns` array of column definitions, and a `data` array of row records.

**The features bag.** `tableFeatures` composes one object out of three kinds of entries, all passed under well-known keys of a single argument object:

- *Feature objects* under their own names — `rowSortingFeature`, `columnFilteringFeature`, `globalFilteringFeature`, `rowPaginationFeature`, `columnVisibilityFeature`, `columnOrderingFeature`, `columnPinningFeature`, `rowSelectionFeature`, `rowExpandingFeature`, `columnGroupingFeature`, `rowAggregationFeature`, `columnFacetingFeature`. Each registered feature contributes its state slice, its default options, and its table/column/row/cell APIs. When a feature is absent, its state slice, setters, and accessors must not exist on the table.
- *Row-model factories* under the keys `coreRowModel`, `filteredRowModel`, `groupedRowModel`, `sortedRowModel`, `expandedRowModel`, `paginatedRowModel`, `facetedRowModel`, `facetedUniqueValues`, and `facetedMinMaxValues`, each produced by the matching `create*` factory export (`createCoreRowModel()` and so on). A pipeline stage without its factory passes the previous stage through unchanged.
- *Function registries* under the keys `sortFns`, `filterFns`, and `aggregationFns`. Registries are plain objects mapping names to functions; the package exports prebuilt registries of the same names bundling every built-in. Column definitions reference registry entries by name; a name that was never registered must not resolve (the per-domain sections define each fallback). Callers extend a registry by spreading it and adding their own named entries.
- The *reactivity binding* under the key `coreReactivityFeature`. The store bindings are produced by calling `storeReactivityBindings()` (imported from `@tanstack/table-core/store-reactivity-bindings`) and must be registered for the state graph described in Table State And Reactivity to function.

The `stockFeatures` export is a prebuilt object bundling every stock feature object (including sizing/resizing/pinning features this specification does not otherwise cover); spreading it into `tableFeatures` registers them all at once. It contains no reactivity binding, no row-model factories, and no function registries — those must always be registered explicitly.

**Options.** Beyond `features`, `columns`, and `data`, the options object accepts `initialState` (partial state merged over feature defaults), `state` (controlled state, described under Table State And Reactivity), `defaultColumn` (a partial column definition merged under every column definition), `getRowId` (a function from original record, index, and parent row to a row id string), `getSubRows` (a function from an original record to its child records array), `renderFallbackValue` (substituted by `cell.renderValue()` when the cell value is undefined), and `pageCount` (an externally known total page count; -1 or absent means unknown). The `tableOptions` export is an identity helper that returns the options object it receives, for ergonomic typing at call sites. After construction, `table.options` returns the merged options and `table.setOptions` replaces them; when new options carry a different `data` array, every row model must re-derive from the new records on next read.

**Utilities.** `functionalUpdate(updater, previous)` returns `updater(previous)` when the updater is a function and the updater itself otherwise. `isFunction(value)` returns true exactly when the value is callable. `flattenBy(items, getChildren)` returns a depth-first flattened array of every node in the forest; `getChildren` must return an array (possibly empty) for every node. `getInitialTableState(features, initialState)` returns the state object that construction would produce for that features bag: every registered feature's default slice, overlaid with the supplied partial initial state.

## Table State And Reactivity

Table state is a keyed graph of reactive atoms; the engine never exposes a monolithic mutable state object and there is no `getState` method. Each registered feature contributes exactly one state slice under a fixed key at construction.

**State slices and defaults.** The slice keys and their registered defaults are: `sorting` (empty array), `columnFilters` (empty array), `globalFilter` (undefined), `pagination` (object with `pageIndex` 0 and `pageSize` 10), `columnVisibility` (empty object), `columnOrder` (empty array), `columnPinning` (object with empty `start` and `end` arrays), `rowSelection` (empty object), `expanded` (empty object), and `grouping` (empty array). `initialState` values overlay these defaults key by key.

**Reading state.** `table.store` is a reactive store whose `state` property returns the snapshot object of every registered slice, and whose `subscribe(listener)` registers a listener invoked after state transitions. `table.atoms` maps each slice key to a readable atom whose `get()` returns that slice's current value. The snapshot read through `table.store.state` must agree with every per-key atom read.

**Writing state.** Each feature contributes a setter named `set` plus the capitalized slice key (`setSorting`, `setColumnFilters`, `setGlobalFilter`, `setPagination`, `setColumnVisibility`, `setColumnOrder`, `setColumnPinning`, `setRowSelection`, `setExpanded`, `setGrouping`). Every setter accepts either the next value or an updater function of the previous value. Each feature also contributes a reset method (`resetSorting`, `resetColumnFilters`, and so on): called with no argument or a false argument it restores the slice to its `initialState` value, and called with `true` it restores the slice to the feature's registered default.

**Controlled state.** When the options object carries a `state` object that owns a slice key, reads of that slice return the controlled value instead of the internally stored one; a controlled key whose value is undefined falls back to the `initialState` value for that key. Setters still run and still notify, but reads keep following the controlled value while the key remains present.

**Derived recomputation.** Row models, column views, and header groups are derived lazily and memoized; after any state transition through a setter, the next read of any affected projection must reflect the new state.

## Column Definitions And The Column Tree

Columns declare how values are read from records and how the column tree is shaped; the engine derives identity, accessors, and tree structure from each definition.

**Identity and accessors.** A column definition resolves its id in this order: an explicit `id` property; else an `accessorKey` with every `.` replaced by `_`; else a string-valued `header`. A definition that resolves no id must cause an Error to be thrown when the column tree is first materialized (for example by `getAllColumns`); construction itself succeeds because columns are derived lazily. An `accessorKey` names a record property; a key containing `.` traverses nested objects level by level (a literal property whose name contains a dot is not consulted), and value reads use the derived id (`row.getValue("user_name_first")` for `accessorKey` `"user.name.first"`). An `accessorFn` receives the original record and the row index and returns the cell value; it requires an explicit `id`. A definition with neither accessor is a display column: it appears in the column tree and produces cells, but `row.getValue` returns undefined for it. A `columns` array inside a definition makes it a group column whose entries become child columns.

**Column helper.** `createColumnHelper()` returns a builder with `accessor`, `display`, `group`, and `columns` members. `accessor(keyOrFn, definition)` returns the definition extended with `accessorKey` (string form) or `accessorFn` (function form, id required in the definition); `display(definition)` and `group(definition)` return the definition typed for their role; `columns(definitions)` returns the array unchanged.

**Default column.** The `defaultColumn` option is merged under every column definition property by property, with the explicit definition winning per property.

**Tree views.** `table.getAllColumns()` returns the top-level columns in definition order; `table.getAllFlatColumns()` flattens the whole tree including group columns; `table.getAllLeafColumns()` returns only leaf columns. Each column exposes `id`, `columnDef` (the resolved definition), `columns` (children, empty for leaves), `parent` (the group column or undefined at top level), and `depth` (0 at top level, increasing downward). `table.getColumn(id)` returns the column with that id or undefined when no such column exists.

## Rows And Cells

Rows wrap the original records; cells join one row with one leaf column and cache the accessor result.

**Row identity and shape.** Without `getRowId`, a top-level row's id is the string form of its index in `data`, and a child row's id appends its index to the parent id with a `.` separator (`"0.1"`). With `getRowId`, the id is whatever the function returns. Each row exposes `id`, `index` (position among its siblings), `depth` (0 for top level), `original` (the source record), `subRows` (child rows resolved through `getSubRows`, empty when none), and `getParentRow()` (undefined at top level). `table.getRow(id)` returns the row with that id and must throw an Error for an unknown id; passing `true` as the second argument guarantees the lookup covers every core row even when later pipeline stages exclude it.

**Value access.** `row.getValue(columnId)` returns the accessor result for that column, caching it after the first read for the life of the row instance; for an unknown column id or a display column it returns undefined. `row.getUniqueValues(columnId)` returns the array of values used for faceting (the accessor result, or its elements when the column declares `getUniqueValues`). `row.getAllCells()` returns one cell per leaf column.

**Cells.** A cell's id is the row id and column id joined with `_` (`"0_name"`). Each cell exposes `row`, `column`, `getValue()` (the row's cached value for the cell's column), and `renderValue()` (the same value, or the table's `renderFallbackValue` when the value is undefined).

## Headers And Footer Groups

The header matrix is derived from the column tree: one header group per tree depth, top-down, each holding one header per rendered slot.

**Header groups.** `table.getHeaderGroups()` returns the header group rows. The number of groups equals the depth of the column tree. Each header exposes `column` (the column it renders), `colSpan` (the number of leaf columns beneath it), `isPlaceholder` (true when the slot exists only to keep the matrix rectangular — a leaf column surfacing in a group row, or padding under a shallow branch), and `subHeaders` (the headers beneath it). In every group, the colSpan values sum to the number of visible leaf columns.

**Flat views and footers.** `table.getFlatHeaders()` returns all headers of all groups flattened; `table.getLeafHeaders()` returns the bottom-most headers. `table.getFooterGroups()` returns the same matrix in reverse group order (bottom-up).

## Row Model Pipeline

Row data flows through a fixed pipeline; each stage is materialized by its registered factory and readable per stage. The order is: core, then filtering, then grouping, then sorting, then expanding, then pagination.

**Stage accessors.** `getCoreRowModel()` returns one row per record (plus sub-rows resolved through `getSubRows`). `getFilteredRowModel()`, `getGroupedRowModel()`, `getSortedRowModel()`, `getExpandedRowModel()`, and `getPaginatedRowModel()` return each stage's output. Every stage also exposes the model it consumed: `getPreFilteredRowModel()` returns the core model, `getPreGroupedRowModel()` the filtered model, `getPreSortedRowModel()` the grouped model, `getPreExpandedRowModel()` the sorted model, and `getPrePaginatedRowModel()` the expanded model. `getRowModel()` returns the final pipeline output (the paginated model when pagination is registered, otherwise the last registered stage).

**Pass-through.** When a stage's factory is not registered, or the matching manual option (`manualFiltering`, `manualGrouping`, `manualSorting`, `manualExpanding`, `manualPagination`) is true, the stage returns its pre-model unchanged.

**Model shape.** Every row model exposes `rows` (the top-level rows of that stage), `flatRows` (rows plus all descendants, depth-first), and `rowsById` (a map from row id to row).

## Row Sorting

Sorting orders the filtered rows by the `sorting` state, an ordered array of entries with a column `id` and a boolean `desc`; later entries break ties left by earlier ones.

**State transitions.** `setSorting` and `resetSorting` follow the state rules above. `column.toggleSorting(desc, multi)` with no arguments cycles the column through ascending, then descending, then unsorted, replacing any other sorted columns; a boolean `desc` argument forces that direction. A column whose `sortDescFirst` definition is true — and any column whose auto-resolved values are numbers — starts its cycle at descending. `column.clearSorting()` removes only that column's entry. `column.getIsSorted()` returns false, `"asc"`, or `"desc"`; `column.getSortIndex()` returns the column's position within the sorting state or -1.

**Sort function resolution.** A column's `sortFn` definition accepts a comparator function, a registry name, or `"auto"` (the default). A comparator receives two rows and the column id and returns a negative, zero, or positive number. Resolution order: a function value is used directly; `"auto"` inspects leading filtered values — Date values resolve to `"datetime"`, strings containing both alphabetic and numeric runs to `"alphanumeric"`, other strings to `"text"`, everything else to the built-in basic comparator; a registry name is looked up in the registered `sortFns`. A name (including an auto-resolved one) missing from the registry falls back to the built-in basic comparator, which is always available without registration.

**Built-in sort functions.** The `sortFns` registry bundles `alphanumeric` and `alphanumericCaseSensitive` (mixed text/number aware), `text` and `textCaseSensitive` (string comparison), `datetime` (Date ordering), and `basic` (relational comparison). Each is also exported individually as `sortFn_` plus the registry name.

## Column And Global Filtering

Column filtering keeps the rows every active filter accepts; global filtering matches one search value across all globally filterable columns. Both run in the filtering stage.

**Column filter state.** `columnFilters` is an array of entries with a column `id` and a `value`. `setColumnFilters` and `resetColumnFilters` follow the state rules. An entry whose id names no column, or whose column resolves no filter function, leaves the rows unfiltered. `column.getFilterValue()` returns the column's current filter value; `column.setFilterValue(value)` upserts that column's entry; `column.getIsFiltered()` returns whether an entry for the column exists.

**Filter function resolution.** A column's `filterFn` definition accepts a predicate function, a registry name, or `"auto"` (the default). A predicate receives the row, the column id, and the filter value, and returns whether the row stays. `"auto"` resolves from the first non-null value in the column: strings to `"includesString"`, numbers to `"inNumberRange"`, booleans to `"equals"`, arrays to `"arrIncludes"`, Date values to `"inDateRange"`, other objects to `"equals"`, anything else to `"weakEquals"` — then looks the resolved name up in the registered `filterFns`; a missing name resolves to no filter function.

**Built-in filter functions.** The `filterFns` registry bundles: `includesString` (case-insensitive substring) and `includesStringSensitive`; `equalsString` (case-insensitive string equality) and `equalsStringSensitive`; `equals` (strict equality) and `weakEquals` (loose equality); `startsWith` and `endsWith` (case-insensitive affix match); `arrIncludes`, `arrIncludesAll`, and `arrIncludesSome` (array membership); `arrHas` (value contained in an array-valued filter value); `inNumberRange` (value within a two-element `[min, max]` bound, inclusive, with a null bound meaning open); `between` and `betweenInclusive` (exclusive and inclusive range); `greaterThan`, `greaterThanOrEqualTo`, `lessThan`, and `lessThanOrEqualTo` (relational); `inDateRange` (Date within bounds); `empty` and `notEmpty` (blank-value tests). Each is also exported individually as `filterFn_` plus the registry name.

**Global filtering.** The `globalFilter` slice holds the search value; `setGlobalFilter` and `resetGlobalFilter` follow the state rules. A row survives global filtering when at least one globally filterable column matches. A column participates exactly when it has an accessor and neither its `enableGlobalFilter` definition nor the table's `enableGlobalFilter`/`enableFilters` options disable it. The `globalFilterFn` option accepts a predicate, a registry name, or `"auto"`; `"auto"` resolves to the built-in case-insensitive substring match without requiring registration.

## Row Pagination

Pagination slices the expanded model into pages driven by the `pagination` slice (`pageIndex`, `pageSize`).

**Reads.** `getPaginatedRowModel().rows` returns the current page's rows. `getPageCount()` returns the `pageCount` option when supplied, otherwise the ceiling of pre-paginated row count divided by `pageSize`; `getRowCount()` returns the pre-paginated row count. `getPageOptions()` returns the array of valid page indexes. `getCanPreviousPage()` is true while `pageIndex` exceeds 0; `getCanNextPage()` is true while a later page exists.

**Transitions.** `setPageIndex(indexOrUpdater)` clamps below at 0, and above at the last page only when the `pageCount` option is supplied. `nextPage()` and `previousPage()` step by one; `firstPage()` goes to index 0 and `lastPage()` to the final page. `setPageSize(size)` applies a new page size and resets `pageIndex` to 0.

## Column Visibility, Ordering, And Pinning

Three slices reshape which leaf columns appear and where: `columnVisibility` hides, `columnOrder` reorders, `columnPinning` assigns region membership.

**Visibility.** `columnVisibility` maps column ids to booleans; an id absent from the map is visible, and false hides. `column.getIsVisible()` reads the flag; `column.toggleVisibility(value)` sets or flips it; `table.toggleAllColumnsVisible(value)` writes every leaf column at once; `table.getIsAllColumnsVisible()` reports the conjunction. `table.getVisibleLeafColumns()` returns the visible leaf columns, and `row.getVisibleCells()` returns exactly the cells of those columns.

**Ordering.** `columnOrder` is an array of column ids: listed ids come first in that order, unlisted columns follow in definition order. `setColumnOrder` writes the slice, and `getVisibleLeafColumns()` reflects the order on next read.

**Pinning.** `columnPinning` holds two id arrays, `start` and `end`. `column.pin(region)` with `"start"` or `"end"` moves the column's id into that region's array (removing it from the other), and with false removes it from both. `column.getIsPinned()` returns `"start"`, `"end"`, or false; `column.getPinnedIndex()` returns the column's position inside its region. `table.getStartVisibleLeafColumns()`, `table.getCenterVisibleLeafColumns()` (unpinned), and `table.getEndVisibleLeafColumns()` partition the visible leaf columns by region. `table.getIsSomeColumnsPinned(region)` reports whether anything is pinned, restricted to one region when the argument is given. `getVisibleLeafColumns()` membership is unaffected by pinning; region views are the reordering projection.

## Row Selection

Selection marks rows by id in the `rowSelection` slice (an object whose keys are the ids of selected rows mapping to true).

**Per-row API.** `row.getIsSelected()` reads membership; `row.toggleSelected(value)` sets or flips it. `table.getIsAllRowsSelected()` is true exactly when every selectable row of the filtered model is selected; `table.getIsSomeRowsSelected()` is true while at least one row is selected.

**Bulk API.** `table.toggleAllRowsSelected(value)` selects or deselects every selectable row of the filtered model (flipping the all-selected state when called without a value); `setRowSelection` writes the slice directly (an empty object clears). `table.getSelectedRowModel()` returns the row model containing the selected rows of the core model — selection membership survives filtering; `table.getFilteredSelectedRowModel()` returns its intersection with the filtered model.

## Row Expanding

Expansion controls which descendant rows the expanded stage surfaces, driven by the `expanded` slice — either an object mapping row ids to true, or the literal value true meaning every row is expanded.

**Per-row API.** `row.getCanExpand()` is true while the row has sub-rows; `row.getIsExpanded()` reads the flag (true for every row while the slice is the literal true); `row.toggleExpanded(value)` sets or flips it.

**Model effect.** The expanded model's `rows` interleave each expanded row's `subRows` immediately beneath it, recursively; collapsed descendants stay out of `rows` while remaining reachable through `flatRows` and row lookup. `table.toggleAllRowsExpanded(value)` expands (writing the literal true) or collapses everything; `table.getIsAllRowsExpanded()` reports whether every expandable row is expanded; `setExpanded` writes the slice directly.

## Grouping And Aggregation

Grouping folds the filtered rows into one group row per distinct value of each grouping column; aggregation computes summary values for group rows.

**Grouping state and shape.** `grouping` is an ordered array of column ids; `setGrouping` writes it. With grouping active, the grouped model's top-level `rows` are group rows in first-encounter order of their values. A group row's id is the grouping column id and the group value joined with `:` (`"cat:fruit"`), and deeper levels append with `>` (`"cat:fruit>name:apple"`). A group row exposes `groupingColumnId`, `groupingValue`, `getIsGrouped()` (true), `getValue(groupingColumnId)` (the group value), `subRows` (next-level rows), and `getLeafRows()` (every original row in the group). `column.getIsGrouped()` reports whether that column id is in the grouping state.

**Aggregated values.** For a non-grouping column, a group row's `getValue(columnId)` returns the aggregation result over the group's rows. A column's `aggregationFn` definition accepts an aggregation definition object, a registry name, or `"auto"` (the default). `"auto"` resolves numeric columns to `"sum"` and Date columns to `"extent"`, then looks the name up in the registered `aggregationFns`; a name missing from the registry — including an auto-resolved one — yields undefined aggregated values. There is no unregistered fallback for aggregation.

**Built-in aggregation functions.** The `aggregationFns` registry bundles `sum`, `min`, `max`, `extent` (two-element min/max pair), `mean`, `median`, `unique` (array of distinct values), `uniqueCount`, `count`, `first`, and `last`. Each is also exported individually as `aggregationFn_` plus the registry name.

**Cell flags.** On a group row, the grouping column's cell reports `getIsGrouped()` true; other cells of the group row report `getIsAggregated()` true when their column resolves an aggregation function. On a leaf row beneath a group, the grouping column's cell reports `getIsPlaceholder()` true.

## Column Faceting

Faceting summarizes the values a column could filter on, computed against the rows that remain after every other column's filter.

**Per-column reads.** `column.getFacetedRowModel()` returns the filtered model recomputed with the column's own filter entry ignored (all other filters still applied); it requires the `facetedRowModel` factory. `column.getFacetedUniqueValues()` returns a Map from each distinct faceted value to its occurrence count (requires the `facetedUniqueValues` factory). `column.getFacetedMinMaxValues()` returns a two-element array of the minimum and maximum faceted values (requires the `facetedMinMaxValues` factory).

## State Model

One table instance owns two inputs — the `data` array and the resolved column definitions — plus one reactive state graph with a slice per registered feature. Every public projection derives from these:

1. The row-model pipeline (core → filtered → grouped → sorted → expanded → paginated), each stage memoized and readable individually together with its pre-model.
2. The column tree views (all/flat/leaf), narrowed by visibility, ordered by `columnOrder`, and partitioned by pinning regions.
3. The header/footer group matrix derived from the visible column tree.
4. Per-row projections: cached values, cells, visible cells, selection/expansion/grouping flags.
5. The state snapshot (`table.store.state`), the per-slice atoms, and the setter/reset transition surface.
6. The faceted models summarizing filterable values per column.

State transitions are synchronous: a setter call immediately changes what every subsequent read returns. Derived projections are lazy and memoized between transitions.

## Error Semantics

Thrown errors are instances of `Error`; message text is not part of this contract (production builds strip messages).

| Condition | Outcome |
|---|---|
| A column definition resolves no id (no `id`, no `accessorKey`, header not a string) | reading the column tree (for example `getAllColumns`) throws an `Error` |
| A column definition supplies `accessorFn` without `id` | reading the column tree (for example `getAllColumns`) throws an `Error` |
| `table.getRow(id)` with an id no row has | throws an `Error` |
| `table.getColumn(id)` with an id no column has | returns undefined (no throw) |
| `row.getValue(columnId)` for an unknown or display column | returns undefined (no throw) |
| A sorting entry names a column id that does not exist | that entry is ignored; remaining rows keep their order |
| A column filter entry whose column resolves no filter function (unknown id or unregistered name) | rows pass through unfiltered |
| A named `sortFn` missing from the registry | falls back to the built-in basic comparator |
| A named or auto-resolved `aggregationFn` missing from the registry | aggregated values are undefined |

## Cross-View Invariants

1. After any setter call, the corresponding slice read through `table.store.state`, through `table.atoms` for that key, and through every projection derived from it must agree on the same value — there must be no read path that observes a stale slice.
2. Every pipeline stage accessor must return exactly what the next stage's pre-model accessor returns, and `getRowModel()` must return the final registered stage's model; a stage whose factory is absent must return its pre-model unchanged through both paths.
3. A column hidden through any visibility API must simultaneously disappear from `getVisibleLeafColumns()`, from every `row.getVisibleCells()`, and from the header matrix colSpan sums, and `getIsAllColumnsVisible()` must be false while any leaf column is hidden.
4. The `start`, `center`, and `end` visible leaf column views must partition `getVisibleLeafColumns()` — the same column ids, each in exactly one region view.
5. `getSelectedRowModel()` must contain exactly the core-model rows whose `getIsSelected()` is true, `getFilteredSelectedRowModel()` must be that set intersected with the filtered model, and `getIsAllRowsSelected()` must be true exactly when every selectable filtered row is selected.
6. Every leaf row of a grouped model must appear in exactly one group row's `getLeafRows()` per grouping level, and a group row's aggregated `getValue` must equal the registered aggregation applied to those leaf rows' values.
7. `getPageCount()` must equal the ceiling of `getRowCount()` divided by the current `pageSize` (when no external `pageCount` option is supplied), and the paginated `rows` must be the corresponding contiguous slice of the pre-paginated model.
8. A column's faceted row model must reflect every active column filter except that column's own entry, so clearing another column's filter must change the facet while editing the column's own filter must not.

## Public Interface

### Import Surface

```ts
import {
  // construction & composition
  constructTable,
  tableFeatures,
  tableOptions,
  createColumnHelper,
  getInitialTableState,
  stockFeatures,
  // feature objects
  columnFacetingFeature,
  columnFilteringFeature,
  columnGroupingFeature,
  columnOrderingFeature,
  columnPinningFeature,
  columnVisibilityFeature,
  globalFilteringFeature,
  rowAggregationFeature,
  rowExpandingFeature,
  rowPaginationFeature,
  rowSelectionFeature,
  rowSortingFeature,
  // row-model factories
  createCoreRowModel,
  createFilteredRowModel,
  createGroupedRowModel,
  createSortedRowModel,
  createExpandedRowModel,
  createPaginatedRowModel,
  createFacetedRowModel,
  createFacetedUniqueValues,
  createFacetedMinMaxValues,
  // function registries
  sortFns,
  filterFns,
  aggregationFns,
  // individual sort functions
  sortFn_alphanumeric,
  sortFn_alphanumericCaseSensitive,
  sortFn_basic,
  sortFn_datetime,
  sortFn_text,
  sortFn_textCaseSensitive,
  // individual filter functions
  filterFn_arrHas,
  filterFn_arrIncludes,
  filterFn_arrIncludesAll,
  filterFn_arrIncludesSome,
  filterFn_between,
  filterFn_betweenInclusive,
  filterFn_empty,
  filterFn_endsWith,
  filterFn_equals,
  filterFn_equalsString,
  filterFn_equalsStringSensitive,
  filterFn_greaterThan,
  filterFn_greaterThanOrEqualTo,
  filterFn_inDateRange,
  filterFn_inNumberRange,
  filterFn_includesString,
  filterFn_includesStringSensitive,
  filterFn_lessThan,
  filterFn_lessThanOrEqualTo,
  filterFn_notEmpty,
  filterFn_startsWith,
  filterFn_weakEquals,
  // individual aggregation functions
  aggregationFn_count,
  aggregationFn_extent,
  aggregationFn_first,
  aggregationFn_last,
  aggregationFn_max,
  aggregationFn_mean,
  aggregationFn_median,
  aggregationFn_min,
  aggregationFn_sum,
  aggregationFn_unique,
  aggregationFn_uniqueCount,
  // utilities
  functionalUpdate,
  isFunction,
  flattenBy,
} from "@tanstack/table-core";

import { storeReactivityBindings } from "@tanstack/table-core/store-reactivity-bindings";
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `constructTable` | function | Builds a table instance from composed options |
| `tableFeatures` | function | Composes features, row-model factories, and registries into one bag |
| `tableOptions` | function | Identity helper for typed options objects |
| `createColumnHelper` | function | Returns a builder for accessor/display/group column definitions |
| `getInitialTableState` | function | Computes the merged initial state for a features bag |
| `stockFeatures` | constant | Prebuilt bundle of every stock feature object |
| `storeReactivityBindings` | function | Produces the reactivity binding registered under `coreReactivityFeature` |
| `columnFacetingFeature` | constant | Feature: per-column faceted summaries |
| `columnFilteringFeature` | constant | Feature: per-column filtering state and APIs |
| `columnGroupingFeature` | constant | Feature: grouping state and group-row APIs |
| `columnOrderingFeature` | constant | Feature: column order state |
| `columnPinningFeature` | constant | Feature: start/end pinning state and region views |
| `columnVisibilityFeature` | constant | Feature: visibility state and visible views |
| `globalFilteringFeature` | constant | Feature: global search state and APIs |
| `rowAggregationFeature` | constant | Feature: aggregated values on group rows |
| `rowExpandingFeature` | constant | Feature: expansion state and APIs |
| `rowPaginationFeature` | constant | Feature: pagination state and APIs |
| `rowSelectionFeature` | constant | Feature: selection state and APIs |
| `rowSortingFeature` | constant | Feature: sorting state and APIs |
| `createCoreRowModel` | function | Factory for the core row-model stage |
| `createFilteredRowModel` | function | Factory for the filtering stage |
| `createGroupedRowModel` | function | Factory for the grouping stage |
| `createSortedRowModel` | function | Factory for the sorting stage |
| `createExpandedRowModel` | function | Factory for the expanding stage |
| `createPaginatedRowModel` | function | Factory for the pagination stage |
| `createFacetedRowModel` | function | Factory for per-column faceted row models |
| `createFacetedUniqueValues` | function | Factory for faceted distinct-value counts |
| `createFacetedMinMaxValues` | function | Factory for faceted min/max bounds |
| `sortFns` | constant | Registry of every built-in sort function |
| `filterFns` | constant | Registry of every built-in filter function |
| `aggregationFns` | constant | Registry of every built-in aggregation function |
| `sortFn_*` | function | Individual built-in sort functions (6 exports) |
| `filterFn_*` | function | Individual built-in filter functions (22 exports) |
| `aggregationFn_*` | constant | Individual built-in aggregation definitions (11 exports) |
| `functionalUpdate` | function | Applies a value-or-updater to a previous value |
| `isFunction` | function | Callable type guard |
| `flattenBy` | function | Depth-first forest flattening by a children accessor |

### CLI Entry Points

There is no console script for this package. Programmatic use is through TypeScript/JavaScript imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. The following third-party packages are preinstalled and importable: `@tanstack/store`, `typescript`, `vitest`, and `@types/node`. The assessment environment provides the same runtime and package set.

The project must declare its packaging metadata in a standard `package.json` at the project root, expose the package root as `@tanstack/table-core` with named ESM exports, and expose the subpath export `@tanstack/table-core/store-reactivity-bindings`.

## Appendix B: Assessment Notes

Assessment exercises the behaviors described in this document through the public API only. Test dimensions include: table construction and feature composition (including the consequences of omitting features, factories, and registries); state reads, writes, resets, controlled state, and store subscription; column identity, accessors, the column tree, and header/footer groups; the row-model pipeline order and per-stage pass-through; sorting, filtering, global filtering, pagination, visibility, ordering, pinning, selection, expansion, grouping, aggregation, and faceting semantics; the documented error outcomes; and cross-view consistency of the projections listed under Cross-View Invariants. Scoring runs the accompanying test suite against your implementation; each test passes or fails independently, and no test inspects internal module structure or private state.
