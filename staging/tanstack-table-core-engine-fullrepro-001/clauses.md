# Clause sidecar — tanstack-table-core-engine-fullrepro-001

Clause ID → section anchor + verbatim behavioral statement (EARS shape noted).
Spec: `spec.md` (candidate-visible body). IDs are internal; the candidate never sees them.

## Table Construction And Feature Composition (TBL-CON)

- TBL-CON-001 (Ubiquitous): "`constructTable` accepts a table options object and returns the table instance. The options object must carry a `features` value produced by `tableFeatures`, a `columns` array of column definitions, and a `data` array of row records."
- TBL-CON-002 (Optional feature): "Each registered feature contributes its state slice, its default options, and its table/column/row/cell APIs. When a feature is absent, its state slice, setters, and accessors must not exist on the table."
- TBL-CON-003 (Optional feature): "Row-model factories under the keys `coreRowModel`, `filteredRowModel`, `groupedRowModel`, `sortedRowModel`, `expandedRowModel`, `paginatedRowModel`, `facetedRowModel`, `facetedUniqueValues`, and `facetedMinMaxValues`, each produced by the matching `create*` factory export. A pipeline stage without its factory passes the previous stage through unchanged."
- TBL-CON-004 (Ubiquitous): "Function registries under the keys `sortFns`, `filterFns`, and `aggregationFns`. Registries are plain objects mapping names to functions; the package exports prebuilt registries of the same names bundling every built-in. Column definitions reference registry entries by name; a name that was never registered must not resolve. Callers extend a registry by spreading it and adding their own named entries."
- TBL-CON-005 (Ubiquitous): "The store bindings are produced by calling `storeReactivityBindings()` (imported from `@tanstack/table-core/store-reactivity-bindings`) and must be registered [under the key `coreReactivityFeature`] for the state graph to function."
- TBL-CON-006 (Ubiquitous): "The `stockFeatures` export is a prebuilt object bundling every stock feature object; spreading it into `tableFeatures` registers them all at once. It contains no reactivity binding, no row-model factories, and no function registries."
- TBL-CON-007 (Optional feature): "the options object accepts `initialState` (partial state merged over feature defaults), `state` (controlled state), `defaultColumn` (a partial column definition merged under every column definition), `getRowId`, `getSubRows`, `renderFallbackValue`, and `pageCount`."
- TBL-CON-008 (Ubiquitous): "The `tableOptions` export is an identity helper that returns the options object it receives."
- TBL-CON-009 (Event-driven): "After construction, `table.options` returns the merged options and `table.setOptions` replaces them; when new options carry a different `data` array, every row model must re-derive from the new records on next read."
- TBL-CON-010 (Ubiquitous): "`functionalUpdate(updater, previous)` returns `updater(previous)` when the updater is a function and the updater itself otherwise."
- TBL-CON-011 (Ubiquitous): "`isFunction(value)` returns true exactly when the value is callable."
- TBL-CON-012 (Ubiquitous): "`flattenBy(items, getChildren)` returns a depth-first flattened array of every node in the forest; `getChildren` must return an array (possibly empty) for every node."
- TBL-CON-013 (Ubiquitous): "`getInitialTableState(features, initialState)` returns the state object that construction would produce for that features bag: every registered feature's default slice, overlaid with the supplied partial initial state."

## Table State And Reactivity (TBL-STA)

- TBL-STA-001 (Ubiquitous): "Table state is a keyed graph of reactive atoms; the engine never exposes a monolithic mutable state object and there is no `getState` method."
- TBL-STA-002 (Ubiquitous): "The slice keys and their registered defaults are: `sorting` (empty array), `columnFilters` (empty array), `globalFilter` (undefined), `pagination` (object with `pageIndex` 0 and `pageSize` 10), `columnVisibility` (empty object), `columnOrder` (empty array), `columnPinning` (object with empty `start` and `end` arrays), `rowSelection` (empty object), `expanded` (empty object), and `grouping` (empty array). `initialState` values overlay these defaults key by key."
- TBL-STA-003 (Ubiquitous): "`table.store` is a reactive store whose `state` property returns the snapshot object of every registered slice, and whose `subscribe(listener)` registers a listener invoked after state transitions."
- TBL-STA-004 (Ubiquitous): "`table.atoms` maps each slice key to a readable atom whose `get()` returns that slice's current value. The snapshot read through `table.store.state` must agree with every per-key atom read."
- TBL-STA-005 (Ubiquitous): "Each feature contributes a setter named `set` plus the capitalized slice key. Every setter accepts either the next value or an updater function of the previous value."
- TBL-STA-006 (Event-driven): "Each feature also contributes a reset method: called with no argument or a false argument it restores the slice to its `initialState` value, and called with `true` it restores the slice to the feature's registered default."
- TBL-STA-007 (State-driven): "When the options object carries a `state` object that owns a slice key, reads of that slice return the controlled value instead of the internally stored one; a controlled key whose value is undefined falls back to the `initialState` value for that key."
- TBL-STA-008 (Event-driven): "Row models, column views, and header groups are derived lazily and memoized; after any state transition through a setter, the next read of any affected projection must reflect the new state."

## Column Definitions And The Column Tree (TBL-COL)

- TBL-COL-001 (Ubiquitous): "A column definition resolves its id in this order: an explicit `id` property; else an `accessorKey` with every `.` replaced by `_`; else a string-valued `header`."
- TBL-COL-002 (Unwanted behavior): "A definition that resolves no id must cause an Error to be thrown when the column tree is first materialized (for example by `getAllColumns`); construction itself succeeds because columns are derived lazily."
- TBL-COL-003 (Ubiquitous): "An `accessorKey` names a record property; a key containing `.` traverses nested objects level by level (a literal property whose name contains a dot is not consulted), and value reads use the derived id."
- TBL-COL-004 (Ubiquitous): "An `accessorFn` receives the original record and the row index and returns the cell value; it requires an explicit `id`."
- TBL-COL-005 (Ubiquitous): "A definition with neither accessor is a display column: it appears in the column tree and produces cells, but `row.getValue` returns undefined for it."
- TBL-COL-006 (Ubiquitous): "A `columns` array inside a definition makes it a group column whose entries become child columns."
- TBL-COL-007 (Ubiquitous): "`createColumnHelper()` returns a builder with `accessor`, `display`, `group`, and `columns` members. `accessor(keyOrFn, definition)` returns the definition extended with `accessorKey` (string form) or `accessorFn` (function form, id required in the definition); `display(definition)` and `group(definition)` return the definition typed for their role; `columns(definitions)` returns the array unchanged."
- TBL-COL-008 (Ubiquitous): "The `defaultColumn` option is merged under every column definition property by property, with the explicit definition winning per property."
- TBL-COL-009 (Ubiquitous): "`table.getAllColumns()` returns the top-level columns in definition order; `table.getAllFlatColumns()` flattens the whole tree including group columns; `table.getAllLeafColumns()` returns only leaf columns."
- TBL-COL-010 (Ubiquitous): "Each column exposes `id`, `columnDef`, `columns` (children, empty for leaves), `parent` (the group column or undefined at top level), and `depth` (0 at top level, increasing downward)."
- TBL-COL-011 (Unwanted behavior): "`table.getColumn(id)` returns the column with that id or undefined when no such column exists."

## Rows And Cells (TBL-ROW)

- TBL-ROW-001 (Ubiquitous): "Without `getRowId`, a top-level row's id is the string form of its index in `data`, and a child row's id appends its index to the parent id with a `.` separator. With `getRowId`, the id is whatever the function returns."
- TBL-ROW-002 (Ubiquitous): "Each row exposes `id`, `index` (position among its siblings), `depth` (0 for top level), `original` (the source record), `subRows` (child rows resolved through `getSubRows`, empty when none), and `getParentRow()` (undefined at top level)."
- TBL-ROW-003 (Unwanted behavior): "`table.getRow(id)` returns the row with that id and must throw an Error for an unknown id; passing `true` as the second argument guarantees the lookup covers every core row even when later pipeline stages exclude it."
- TBL-ROW-004 (Ubiquitous): "`row.getValue(columnId)` returns the accessor result for that column, caching it after the first read for the life of the row instance; for an unknown column id or a display column it returns undefined."
- TBL-ROW-005 (Ubiquitous): "`row.getUniqueValues(columnId)` returns the array of values used for faceting (the accessor result, or its elements when the column declares `getUniqueValues`)."
- TBL-ROW-006 (Ubiquitous): "`row.getAllCells()` returns one cell per leaf column."
- TBL-ROW-007 (Ubiquitous): "A cell's id is the row id and column id joined with `_`. Each cell exposes `row`, `column`, `getValue()`, and `renderValue()` (the same value, or the table's `renderFallbackValue` when the value is undefined)."

## Headers And Footer Groups (TBL-HDR)

- TBL-HDR-001 (Ubiquitous): "`table.getHeaderGroups()` returns the header group rows. The number of groups equals the depth of the column tree."
- TBL-HDR-002 (Ubiquitous): "Each header exposes `column`, `colSpan` (the number of leaf columns beneath it), `isPlaceholder` (true when the slot exists only to keep the matrix rectangular), and `subHeaders`."
- TBL-HDR-003 (Ubiquitous): "In every group, the colSpan values sum to the number of visible leaf columns."
- TBL-HDR-004 (Ubiquitous): "`table.getFlatHeaders()` returns all headers of all groups flattened; `table.getLeafHeaders()` returns the bottom-most headers. `table.getFooterGroups()` returns the same matrix in reverse group order."

## Row Model Pipeline (TBL-PIP)

- TBL-PIP-001 (Ubiquitous): "The order is: core, then filtering, then grouping, then sorting, then expanding, then pagination."
- TBL-PIP-002 (Ubiquitous): "`getCoreRowModel()` returns one row per record (plus sub-rows resolved through `getSubRows`)."
- TBL-PIP-003 (Ubiquitous): "Every stage also exposes the model it consumed: `getPreFilteredRowModel()` returns the core model, `getPreGroupedRowModel()` the filtered model, `getPreSortedRowModel()` the grouped model, `getPreExpandedRowModel()` the sorted model, and `getPrePaginatedRowModel()` the expanded model."
- TBL-PIP-004 (Ubiquitous): "`getRowModel()` returns the final pipeline output (the paginated model when pagination is registered, otherwise the last registered stage)."
- TBL-PIP-005 (State-driven): "When a stage's factory is not registered, or the matching manual option (`manualFiltering`, `manualGrouping`, `manualSorting`, `manualExpanding`, `manualPagination`) is true, the stage returns its pre-model unchanged."
- TBL-PIP-006 (Ubiquitous): "Every row model exposes `rows` (the top-level rows of that stage), `flatRows` (rows plus all descendants, depth-first), and `rowsById` (a map from row id to row)."

## Row Sorting (TBL-SRT)

- TBL-SRT-001 (Ubiquitous): "Sorting orders the filtered rows by the `sorting` state, an ordered array of entries with a column `id` and a boolean `desc`; later entries break ties left by earlier ones."
- TBL-SRT-002 (Event-driven): "`column.toggleSorting(desc, multi)` with no arguments cycles the column through ascending, then descending, then unsorted, replacing any other sorted columns; a boolean `desc` argument forces that direction."
- TBL-SRT-003 (State-driven): "A column whose `sortDescFirst` definition is true — and any column whose auto-resolved values are numbers — starts its cycle at descending."
- TBL-SRT-004 (Event-driven): "`column.clearSorting()` removes only that column's entry."
- TBL-SRT-005 (Ubiquitous): "`column.getIsSorted()` returns false, `\"asc\"`, or `\"desc\"`; `column.getSortIndex()` returns the column's position within the sorting state or -1."
- TBL-SRT-006 (Ubiquitous): "Resolution order: a function value is used directly; `\"auto\"` inspects leading filtered values — Date values resolve to `\"datetime\"`, strings containing both alphabetic and numeric runs to `\"alphanumeric\"`, other strings to `\"text\"`, everything else to the built-in basic comparator; a registry name is looked up in the registered `sortFns`."
- TBL-SRT-007 (Unwanted behavior): "A name (including an auto-resolved one) missing from the registry falls back to the built-in basic comparator, which is always available without registration."
- TBL-SRT-008 (Ubiquitous): "The `sortFns` registry bundles `alphanumeric` and `alphanumericCaseSensitive`, `text` and `textCaseSensitive`, `datetime`, and `basic`. Each is also exported individually as `sortFn_` plus the registry name."
- TBL-SRT-009 (Ubiquitous): "A comparator receives two rows and the column id and returns a negative, zero, or positive number."

## Column And Global Filtering (TBL-FLT)

- TBL-FLT-001 (Ubiquitous): "`columnFilters` is an array of entries with a column `id` and a `value`."
- TBL-FLT-002 (Unwanted behavior): "An entry whose id names no column, or whose column resolves no filter function, leaves the rows unfiltered."
- TBL-FLT-003 (Ubiquitous): "`column.getFilterValue()` returns the column's current filter value; `column.setFilterValue(value)` upserts that column's entry; `column.getIsFiltered()` returns whether an entry for the column exists."
- TBL-FLT-004 (Ubiquitous): "A predicate receives the row, the column id, and the filter value, and returns whether the row stays."
- TBL-FLT-005 (Ubiquitous): "`\"auto\"` resolves from the first non-null value in the column: strings to `\"includesString\"`, numbers to `\"inNumberRange\"`, booleans to `\"equals\"`, arrays to `\"arrIncludes\"`, Date values to `\"inDateRange\"`, other objects to `\"equals\"`, anything else to `\"weakEquals\"` — then looks the resolved name up in the registered `filterFns`; a missing name resolves to no filter function."
- TBL-FLT-006 (Ubiquitous): "The `filterFns` registry bundles: `includesString` (case-insensitive substring) and `includesStringSensitive`; `equalsString` and `equalsStringSensitive`; `equals` and `weakEquals`; `startsWith` and `endsWith`; `arrIncludes`, `arrIncludesAll`, and `arrIncludesSome`; `arrHas`; `inNumberRange` (value within a two-element `[min, max]` bound, inclusive, with a null bound meaning open); `between` and `betweenInclusive`; `greaterThan`, `greaterThanOrEqualTo`, `lessThan`, and `lessThanOrEqualTo`; `inDateRange`; `empty` and `notEmpty`."
- TBL-FLT-007 (Ubiquitous): "A row survives global filtering when at least one globally filterable column matches."
- TBL-FLT-008 (Ubiquitous): "A column participates exactly when it has an accessor and neither its `enableGlobalFilter` definition nor the table's `enableGlobalFilter`/`enableFilters` options disable it."
- TBL-FLT-009 (Ubiquitous): "The `globalFilterFn` option accepts a predicate, a registry name, or `\"auto\"`; `\"auto\"` resolves to the built-in case-insensitive substring match without requiring registration."

## Row Pagination (TBL-PAG)

- TBL-PAG-001 (Ubiquitous): "`getPaginatedRowModel().rows` returns the current page's rows."
- TBL-PAG-002 (Ubiquitous): "`getPageCount()` returns the `pageCount` option when supplied, otherwise the ceiling of pre-paginated row count divided by `pageSize`; `getRowCount()` returns the pre-paginated row count."
- TBL-PAG-003 (Ubiquitous): "`getPageOptions()` returns the array of valid page indexes. `getCanPreviousPage()` is true while `pageIndex` exceeds 0; `getCanNextPage()` is true while a later page exists."
- TBL-PAG-004 (Event-driven): "`setPageIndex(indexOrUpdater)` clamps below at 0, and above at the last page only when the `pageCount` option is supplied."
- TBL-PAG-005 (Event-driven): "`nextPage()` and `previousPage()` step by one; `firstPage()` goes to index 0 and `lastPage()` to the final page."
- TBL-PAG-006 (Event-driven): "`setPageSize(size)` applies a new page size and resets `pageIndex` to 0."

## Column Visibility, Ordering, And Pinning (TBL-VIS)

- TBL-VIS-001 (Ubiquitous): "`columnVisibility` maps column ids to booleans; an id absent from the map is visible, and false hides."
- TBL-VIS-002 (Ubiquitous): "`column.getIsVisible()` reads the flag; `column.toggleVisibility(value)` sets or flips it; `table.toggleAllColumnsVisible(value)` writes every leaf column at once; `table.getIsAllColumnsVisible()` reports the conjunction."
- TBL-VIS-003 (Ubiquitous): "`table.getVisibleLeafColumns()` returns the visible leaf columns, and `row.getVisibleCells()` returns exactly the cells of those columns."
- TBL-VIS-004 (Ubiquitous): "`columnOrder` is an array of column ids: listed ids come first in that order, unlisted columns follow in definition order."
- TBL-VIS-005 (Event-driven): "`column.pin(region)` with `\"start\"` or `\"end\"` moves the column's id into that region's array (removing it from the other), and with false removes it from both."
- TBL-VIS-006 (Ubiquitous): "`column.getIsPinned()` returns `\"start\"`, `\"end\"`, or false; `column.getPinnedIndex()` returns the column's position inside its region."
- TBL-VIS-007 (Ubiquitous): "`table.getStartVisibleLeafColumns()`, `table.getCenterVisibleLeafColumns()` (unpinned), and `table.getEndVisibleLeafColumns()` partition the visible leaf columns by region."
- TBL-VIS-008 (Ubiquitous): "`table.getIsSomeColumnsPinned(region)` reports whether anything is pinned, restricted to one region when the argument is given."
- TBL-VIS-009 (Ubiquitous): "`getVisibleLeafColumns()` membership is unaffected by pinning; region views are the reordering projection."

## Row Selection (TBL-SEL)

- TBL-SEL-001 (Ubiquitous): "Selection marks rows by id in the `rowSelection` slice (an object whose keys are the ids of selected rows mapping to true)."
- TBL-SEL-002 (Ubiquitous): "`row.getIsSelected()` reads membership; `row.toggleSelected(value)` sets or flips it."
- TBL-SEL-003 (Ubiquitous): "`table.getIsAllRowsSelected()` is true exactly when every selectable row of the filtered model is selected; `table.getIsSomeRowsSelected()` is true while at least one row is selected."
- TBL-SEL-004 (Event-driven): "`table.toggleAllRowsSelected(value)` selects or deselects every selectable row of the filtered model (flipping the all-selected state when called without a value); `setRowSelection` writes the slice directly (an empty object clears)."
- TBL-SEL-005 (Ubiquitous): "`table.getSelectedRowModel()` returns the row model containing the selected rows of the core model — selection membership survives filtering; `table.getFilteredSelectedRowModel()` returns its intersection with the filtered model."

## Row Expanding (TBL-EXP)

- TBL-EXP-001 (Ubiquitous): "the `expanded` slice — either an object mapping row ids to true, or the literal value true meaning every row is expanded."
- TBL-EXP-002 (Ubiquitous): "`row.getCanExpand()` is true while the row has sub-rows; `row.getIsExpanded()` reads the flag (true for every row while the slice is the literal true); `row.toggleExpanded(value)` sets or flips it."
- TBL-EXP-003 (Ubiquitous): "The expanded model's `rows` interleave each expanded row's `subRows` immediately beneath it, recursively; collapsed descendants stay out of `rows` while remaining reachable through `flatRows` and row lookup."
- TBL-EXP-004 (Event-driven): "`table.toggleAllRowsExpanded(value)` expands (writing the literal true) or collapses everything; `table.getIsAllRowsExpanded()` reports whether every expandable row is expanded."

## Grouping And Aggregation (TBL-GRP)

- TBL-GRP-001 (Ubiquitous): "`grouping` is an ordered array of column ids. With grouping active, the grouped model's top-level `rows` are group rows in first-encounter order of their values."
- TBL-GRP-002 (Ubiquitous): "A group row's id is the grouping column id and the group value joined with `:`, and deeper levels append with `>`."
- TBL-GRP-003 (Ubiquitous): "A group row exposes `groupingColumnId`, `groupingValue`, `getIsGrouped()` (true), `getValue(groupingColumnId)` (the group value), `subRows` (next-level rows), and `getLeafRows()` (every original row in the group)."
- TBL-GRP-004 (Ubiquitous): "`column.getIsGrouped()` reports whether that column id is in the grouping state."
- TBL-GRP-005 (Ubiquitous): "For a non-grouping column, a group row's `getValue(columnId)` returns the aggregation result over the group's rows."
- TBL-GRP-006 (Ubiquitous): "`\"auto\"` resolves numeric columns to `\"sum\"` and Date columns to `\"extent\"`, then looks the name up in the registered `aggregationFns`; a name missing from the registry — including an auto-resolved one — yields undefined aggregated values. There is no unregistered fallback for aggregation."
- TBL-GRP-007 (Ubiquitous): "The `aggregationFns` registry bundles `sum`, `min`, `max`, `extent`, `mean`, `median`, `unique`, `uniqueCount`, `count`, `first`, and `last`."
- TBL-GRP-008 (Ubiquitous): "On a group row, the grouping column's cell reports `getIsGrouped()` true; other cells of the group row report `getIsAggregated()` true when their column resolves an aggregation function. On a leaf row beneath a group, the grouping column's cell reports `getIsPlaceholder()` true."

## Column Faceting (TBL-FAC)

- TBL-FAC-001 (Ubiquitous): "`column.getFacetedRowModel()` returns the filtered model recomputed with the column's own filter entry ignored (all other filters still applied)."
- TBL-FAC-002 (Ubiquitous): "`column.getFacetedUniqueValues()` returns a Map from each distinct faceted value to its occurrence count."
- TBL-FAC-003 (Ubiquitous): "`column.getFacetedMinMaxValues()` returns a two-element array of the minimum and maximum faceted values."

## Error Semantics (TBL-ERR)

- TBL-ERR-001 (Unwanted behavior): "A column definition resolves no id (no `id`, no `accessorKey`, header not a string) → reading the column tree (for example `getAllColumns`) throws an `Error`."
- TBL-ERR-002 (Unwanted behavior): "A column definition supplies `accessorFn` without `id` → reading the column tree (for example `getAllColumns`) throws an `Error`."
- TBL-ERR-003 (Unwanted behavior): "`table.getRow(id)` with an id no row has → throws an `Error`."
- TBL-ERR-004 (Unwanted behavior): "A sorting entry names a column id that does not exist → that entry is ignored; remaining rows keep their order."
- TBL-ERR-005 (Ubiquitous): "Thrown errors are instances of `Error`; message text is not part of this contract."

## Cross-View Invariants (TBL-CVI)

- TBL-CVI-001: spec section "Cross-View Invariants" item 1 (state agreement across store/atoms/projections).
- TBL-CVI-002: item 2 (stage/pre-stage identity and final model).
- TBL-CVI-003: item 3 (visibility across leaf views, cells, headers).
- TBL-CVI-004: item 4 (pinning regions partition visible leaves).
- TBL-CVI-005: item 5 (selected model and all-selected agreement).
- TBL-CVI-006: item 6 (group leafRows partition and aggregation agreement).
- TBL-CVI-007: item 7 (page count arithmetic and page slice).
- TBL-CVI-008: item 8 (facet excludes own filter).
