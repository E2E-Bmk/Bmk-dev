# spec_test_map — tanstack-table-core-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-26

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::construction and composition::constructTable projects the data array through the core row model | atomic | positive | section Table Construction And Feature Composition + section Row Model Pipeline | covered | TBL-CON-001, TBL-PIP-002 |
| atomic::construction and composition::an unregistered feature contributes no state slice and no setter | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-002 |
| atomic::construction and composition::a registered feature contributes its state slice and setter | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-002 |
| atomic::construction and composition::a pipeline stage without its factory passes the previous stage through | atomic | positive | section Table Construction And Feature Composition + section Row Model Pipeline | covered | TBL-CON-003, TBL-PIP-005 |
| atomic::construction and composition::stockFeatures spreads into tableFeatures and registers stock features | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-006 |
| atomic::construction and composition::tableOptions returns the options object it receives | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-008 |
| atomic::construction and composition::setOptions with a new data array re-derives the row models | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-009 |
| atomic::construction and composition::initialState values overlay the feature defaults | atomic | positive | section Table Construction And Feature Composition + section Table State And Reactivity | covered | TBL-CON-007, TBL-STA-002 |
| atomic::construction and composition::functionalUpdate applies an updater function or returns the plain value | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-010 |
| atomic::construction and composition::isFunction accepts callables and rejects plain values | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-011 |
| atomic::construction and composition::flattenBy flattens a forest depth-first through the children accessor | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-012 |
| atomic::construction and composition::getInitialTableState merges feature defaults with the supplied overrides | atomic | positive | section Table Construction And Feature Composition | covered | TBL-CON-013 |
| atomic::construction and composition::getRowId customizes row identity | atomic | positive | section Rows And Cells | covered | TBL-ROW-001 |
| atomic::construction and composition::renderValue substitutes renderFallbackValue for undefined cell values | atomic | positive | section Table Construction And Feature Composition + section Rows And Cells | covered | TBL-CON-007, TBL-ROW-007 |
| atomic::state and reactivity::registered slices expose their documented defaults | atomic | positive | section Table State And Reactivity | covered | TBL-STA-002 |
| atomic::state and reactivity::there is no getState method; the snapshot lives on the store | atomic | positive | section Table State And Reactivity | covered | TBL-STA-001, TBL-STA-003 |
| atomic::state and reactivity::setters accept a plain value or an updater of the previous value | atomic | positive | section Table State And Reactivity | covered | TBL-STA-005 |
| atomic::state and reactivity::the store snapshot agrees with every per-key atom | atomic | positive | section Table State And Reactivity | covered | TBL-STA-004 |
| atomic::state and reactivity::store.subscribe observes state transitions | atomic | positive | section Table State And Reactivity | covered | TBL-STA-003 |
| atomic::state and reactivity::reset with no argument restores the initialState value | atomic | positive | section Table State And Reactivity | covered | TBL-STA-006 |
| atomic::state and reactivity::reset with true restores the feature default | atomic | positive | section Table State And Reactivity | covered | TBL-STA-006 |
| atomic::state and reactivity::a controlled slice overrides the internally stored value | atomic | positive | section Table State And Reactivity | covered | TBL-STA-007 |
| atomic::state and reactivity::a controlled key holding undefined falls back to the initialState value | atomic | positive | section Table State And Reactivity | covered | TBL-STA-007 |
| atomic::state and reactivity::projections reflect a setter transition on the next read | atomic | positive | section Table State And Reactivity | covered | TBL-STA-008 |
| atomic::columns and the column tree::an explicit id wins over the accessor-derived id | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-001 |
| atomic::columns and the column tree::a dotted accessorKey derives an underscore id and traverses nested records | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-003 |
| atomic::columns and the column tree::a dotted accessorKey does not consult a literal dotted property | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-003 |
| atomic::columns and the column tree::a string header serves as the column id when no accessor id exists | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-001 |
| atomic::columns and the column tree::a definition that resolves no id throws when the column tree materializes | atomic | failure_path | section Column Definitions And The Column Tree + section Error Semantics | covered | TBL-COL-002, TBL-ERR-001 |
| atomic::columns and the column tree::an accessorFn without an explicit id throws when the column tree materializes | atomic | failure_path | section Column Definitions And The Column Tree + section Error Semantics | covered | TBL-COL-004, TBL-ERR-002 |
| atomic::columns and the column tree::an accessorFn column computes values through the function | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-004 |
| atomic::columns and the column tree::a display column produces cells but no values | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-005 |
| atomic::columns and the column tree::a columns array creates a group column with child columns | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-006, TBL-COL-010 |
| atomic::columns and the column tree::createColumnHelper builds accessor, display, and group definitions | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-007 |
| atomic::columns and the column tree::defaultColumn merges under each definition property by property | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-008 |
| atomic::columns and the column tree::all, flat, and leaf column views expose the tree at different depths | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-009 |
| atomic::columns and the column tree::getColumn returns undefined for an unknown id | atomic | positive | section Column Definitions And The Column Tree | covered | TBL-COL-011 |
| atomic::rows and cells::default row ids are index-based and children join with a dot | atomic | positive | section Rows And Cells | covered | TBL-ROW-001 |
| atomic::rows and cells::rows expose index, depth, original, subRows, and getParentRow | atomic | positive | section Rows And Cells | covered | TBL-ROW-002 |
| atomic::rows and cells::getRow resolves a known id and throws for an unknown id | atomic | failure_path | section Rows And Cells + section Error Semantics | covered | TBL-ROW-003, TBL-ERR-003 |
| atomic::rows and cells::getRow with true reaches rows excluded by later stages | atomic | positive | section Rows And Cells | covered | TBL-ROW-003 |
| atomic::rows and cells::getValue caches the first read for the life of the row | atomic | positive | section Rows And Cells | covered | TBL-ROW-004 |
| atomic::rows and cells::getValue returns undefined for an unknown column id | atomic | positive | section Rows And Cells | covered | TBL-ROW-004 |
| atomic::rows and cells::getUniqueValues returns the value array used for faceting | atomic | positive | section Rows And Cells | covered | TBL-ROW-005 |
| atomic::rows and cells::cells join a row and a leaf column with a composite id | atomic | positive | section Rows And Cells | covered | TBL-ROW-006, TBL-ROW-007 |
| atomic::headers and footer groups::a flat column list produces a single header group | atomic | positive | section Headers And Footer Groups | covered | TBL-HDR-001 |
| atomic::headers and footer groups::nested definitions produce one group per depth with spans and placeholders | atomic | positive | section Headers And Footer Groups | covered | TBL-HDR-001, TBL-HDR-002 |
| atomic::headers and footer groups::colSpan values in every group sum to the visible leaf count | atomic | positive | section Headers And Footer Groups | covered | TBL-HDR-003 |
| atomic::headers and footer groups::flat and leaf header views expose the matrix without grouping | atomic | positive | section Headers And Footer Groups | covered | TBL-HDR-004 |
| atomic::headers and footer groups::footer groups mirror the header matrix in reverse order | atomic | positive | section Headers And Footer Groups | covered | TBL-HDR-004 |
| atomic::headers and footer groups::subHeaders link a group header to the headers beneath it | atomic | positive | section Headers And Footer Groups | covered | TBL-HDR-002 |
| atomic::row model pipeline::each pre-model accessor returns the previous stage's output | atomic | positive | section Row Model Pipeline | covered | TBL-PIP-001, TBL-PIP-003 |
| atomic::row model pipeline::getRowModel returns the final registered stage | atomic | positive | section Row Model Pipeline | covered | TBL-PIP-004 |
| atomic::row model pipeline::a manual stage option makes that stage pass through | atomic | positive | section Row Model Pipeline | covered | TBL-PIP-005 |
| atomic::row model pipeline::row models expose rows, flatRows, and rowsById | atomic | positive | section Row Model Pipeline | covered | TBL-PIP-006 |
| atomic::row model pipeline::the core model resolves sub-rows through getSubRows | atomic | positive | section Row Model Pipeline | covered | TBL-PIP-002 |
| atomic::row sorting::setSorting orders rows ascending and descending | atomic | positive | section Row Sorting | covered | TBL-SRT-001 |
| atomic::row sorting::later sorting entries break ties left by earlier ones | atomic | positive | section Row Sorting | covered | TBL-SRT-001 |
| atomic::row sorting::toggleSorting cycles a text column through asc, desc, unsorted | atomic | positive | section Row Sorting | covered | TBL-SRT-002 |
| atomic::row sorting::an explicit desc argument forces the direction | atomic | positive | section Row Sorting | covered | TBL-SRT-002 |
| atomic::row sorting::numeric columns and sortDescFirst columns start their cycle descending | atomic | positive | section Row Sorting | covered | TBL-SRT-003 |
| atomic::row sorting::clearSorting removes only that column's entry | atomic | positive | section Row Sorting | covered | TBL-SRT-004 |
| atomic::row sorting::getIsSorted and getSortIndex report per-column sort status | atomic | positive | section Row Sorting | covered | TBL-SRT-005 |
| atomic::row sorting::an inline comparator sorts through the function directly | atomic | positive | section Row Sorting | covered | TBL-SRT-006, TBL-SRT-009 |
| atomic::row sorting::a custom registry entry is reachable by name | atomic | positive | section Row Sorting | covered | TBL-SRT-006 |
| atomic::row sorting::an unregistered sort name falls back to the basic comparator | atomic | positive | section Row Sorting | covered | TBL-SRT-007 |
| atomic::row sorting::the sortFns registry bundles the six built-ins as individual exports | atomic | positive | section Row Sorting | covered | TBL-SRT-008 |
| atomic::row sorting::auto resolution picks datetime ordering for Date columns | atomic | positive | section Row Sorting | covered | TBL-SRT-006 |
| atomic::row sorting::auto resolution orders mixed alphanumeric strings numerically | atomic | positive | section Row Sorting | covered | TBL-SRT-006 |
| atomic::column and global filtering::a string column filters by case-insensitive substring by default | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-005, TBL-FLT-006 |
| atomic::column and global filtering::a number column filters by inclusive range with open bounds by default | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-005, TBL-FLT-006 |
| atomic::column and global filtering::named registry filters apply their documented predicate | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-006 |
| atomic::column and global filtering::an inline predicate receives row, column id, and filter value | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-004 |
| atomic::column and global filtering::an unknown column id or unregistered name leaves rows unfiltered | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-002 |
| atomic::column and global filtering::per-column filter accessors upsert and report the entry | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-003 |
| atomic::column and global filtering::global filtering keeps rows where any filterable column matches | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-007, TBL-FLT-009 |
| atomic::column and global filtering::enableGlobalFilter false excludes a column from global matching | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-008 |
| atomic::column and global filtering::a display column never participates in global filtering | atomic | positive | section Column And Global Filtering | covered | TBL-FLT-008 |
| atomic::row pagination::the default page holds the first ten rows | atomic | positive | section Row Pagination + section Table State And Reactivity | covered | TBL-PAG-001, TBL-STA-002 |
| atomic::row pagination::page count and row count derive from the pre-paginated model | atomic | positive | section Row Pagination | covered | TBL-PAG-002 |
| atomic::row pagination::navigation methods step, jump to first, and jump to last | atomic | positive | section Row Pagination | covered | TBL-PAG-005 |
| atomic::row pagination::setPageSize applies the size and resets the index | atomic | positive | section Row Pagination | covered | TBL-PAG-006 |
| atomic::row pagination::setPageIndex clamps at zero, and above only with a supplied pageCount | atomic | positive | section Row Pagination | covered | TBL-PAG-004 |
| atomic::row pagination::page options and can-navigate flags follow the page window | atomic | positive | section Row Pagination | covered | TBL-PAG-003 |
| atomic::column visibility and ordering::false in columnVisibility hides; absent ids stay visible | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-001, TBL-VIS-002 |
| atomic::column visibility and ordering::toggleVisibility flips one column; toggleAllColumnsVisible writes all | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-002 |
| atomic::column visibility and ordering::visible cells track visible leaf columns | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-003 |
| atomic::column visibility and ordering::columnOrder lists ids first; unlisted columns keep definition order | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-004 |
| atomic::column pinning::setColumnPinning assigns start and end regions | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-007 |
| atomic::column pinning::column.pin moves between regions and false unpins | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-005 |
| atomic::column pinning::getIsPinned, getPinnedIndex, and getIsSomeColumnsPinned report regions | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-006, TBL-VIS-008 |
| atomic::column pinning::pinning never changes visible leaf membership | atomic | positive | section Column Visibility, Ordering, And Pinning | covered | TBL-VIS-009 |
| atomic::row selection::toggleSelected marks a row in the rowSelection slice | atomic | positive | section Row Selection | covered | TBL-SEL-001, TBL-SEL-002 |
| atomic::row selection::all-rows and some-rows flags follow the selected set | atomic | positive | section Row Selection | covered | TBL-SEL-003 |
| atomic::row selection::toggleAllRowsSelected selects everything and no argument flips | atomic | positive | section Row Selection | covered | TBL-SEL-004 |
| atomic::row selection::getSelectedRowModel returns exactly the selected rows | atomic | positive | section Row Selection | covered | TBL-SEL-005 |
| atomic::row expanding::toggleExpanded surfaces a row's children in the expanded model | atomic | positive | section Row Expanding | covered | TBL-EXP-002, TBL-EXP-003 |
| atomic::row expanding::collapsed descendants stay reachable through flatRows | atomic | positive | section Row Expanding | covered | TBL-EXP-003 |
| atomic::row expanding::toggleAllRowsExpanded writes the literal true and expands every level | atomic | positive | section Row Expanding | covered | TBL-EXP-001, TBL-EXP-004 |
| atomic::row expanding::a leaf row cannot expand; getIsExpanded is true under the literal true | atomic | positive | section Row Expanding | covered | TBL-EXP-001, TBL-EXP-002 |
| atomic::grouping and aggregation::grouping folds rows into one group row per distinct value | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-001, TBL-GRP-002 |
| atomic::grouping and aggregation::two-level grouping appends deeper ids with the > separator | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-002 |
| atomic::grouping and aggregation::group rows expose grouping metadata and leaf rows | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-003, TBL-GRP-004 |
| atomic::grouping and aggregation::a named aggregation summarizes group values | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-005, TBL-GRP-007 |
| atomic::grouping and aggregation::auto aggregation resolves numeric columns to sum when registered | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-006 |
| atomic::grouping and aggregation::without a registered aggregation the aggregated value is undefined | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-006 |
| atomic::grouping and aggregation::an inline aggregation definition object applies directly | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-006, TBL-GRP-007 |
| atomic::grouping and aggregation::the aggregationFns registry bundles the eleven built-ins | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-007 |
| atomic::grouping and aggregation::cells report grouped, aggregated, and placeholder roles | atomic | positive | section Grouping And Aggregation | covered | TBL-GRP-008 |
| atomic::column faceting::faceted unique values map each distinct value to its count | atomic | positive | section Column Faceting | covered | TBL-FAC-002 |
| atomic::column faceting::faceted min-max returns the value bounds | atomic | positive | section Column Faceting | covered | TBL-FAC-003 |
| atomic::column faceting::a column's faceted model ignores its own filter but applies others | atomic | positive | section Column Faceting | covered | TBL-FAC-001 |
| integration::pipeline integration::filtering, sorting, and pagination compose in pipeline order | integration | positive | section Row Model Pipeline + section Cross-View Invariants | covered | TBL-PIP-001, TBL-PIP-003, TBL-PIP-004, TBL-CVI-002 |
| integration::pipeline integration::every pre-model equals the previous stage output across an active pipeline | integration | positive | section Row Model Pipeline + section Cross-View Invariants | covered | TBL-PIP-003, TBL-CVI-002 |
| integration::pipeline integration::state transitions stay consistent across store, atoms, and projections | integration | positive | section Table State And Reactivity + section Cross-View Invariants | covered | TBL-STA-004, TBL-STA-008, TBL-CVI-001 |
| integration::pipeline integration::grouping and sorting interact: groups sort by aggregated values | integration | positive | section Grouping And Aggregation + section Row Sorting + section Row Model Pipeline | covered | TBL-GRP-005, TBL-SRT-001, TBL-PIP-001 |
| integration::pipeline integration::expanding grouped rows surfaces leaf rows through pagination | integration | positive | section Row Expanding + section Grouping And Aggregation + section Row Pagination + section Row Model Pipeline | covered | TBL-EXP-003, TBL-GRP-001, TBL-PAG-001, TBL-PIP-001 |
| integration::cross-view consistency::hiding a column updates leaf views, cells, and header spans together | integration | positive | section Column Visibility, Ordering, And Pinning + section Headers And Footer Groups + section Cross-View Invariants | covered | TBL-VIS-003, TBL-HDR-003, TBL-CVI-003 |
| integration::cross-view consistency::pinning regions partition the visible leaves under visibility changes | integration | positive | section Column Visibility, Ordering, And Pinning + section Cross-View Invariants | covered | TBL-VIS-007, TBL-VIS-009, TBL-CVI-004 |
| integration::cross-view consistency::selection membership survives filtering; the filtered variant intersects | integration | positive | section Row Selection + section Cross-View Invariants | covered | TBL-SEL-005, TBL-SEL-003, TBL-CVI-005 |
| integration::cross-view consistency::group leaf rows partition the filtered set and aggregate consistently | integration | positive | section Grouping And Aggregation + section Cross-View Invariants | covered | TBL-GRP-003, TBL-GRP-005, TBL-CVI-006 |
| integration::cross-view consistency::page arithmetic tracks the filtered row count | integration | positive | section Row Pagination + section Cross-View Invariants | covered | TBL-PAG-002, TBL-CVI-007 |
| integration::cross-view consistency::facets react to other columns' filters but not their own | integration | positive | section Column Faceting + section Cross-View Invariants | covered | TBL-FAC-001, TBL-FAC-002, TBL-CVI-008 |
| integration::state workflows::controlled and uncontrolled slices coexist | integration | positive | section Table State And Reactivity | covered | TBL-STA-007, TBL-STA-005 |
| integration::state workflows::initialState seeds several slices and resets return to it | integration | positive | section Table State And Reactivity | covered | TBL-STA-002, TBL-STA-006 |
| integration::state workflows::one subscriber observes transitions from several features | integration | positive | section Table State And Reactivity | covered | TBL-STA-003, TBL-STA-005 |
| integration::state workflows::swapping data through setOptions preserves active state | integration | positive | section Table Construction And Feature Composition + section Table State And Reactivity | covered | TBL-CON-009, TBL-STA-008 |
| integration::state workflows::custom row ids key selection and expansion state | integration | positive | section Rows And Cells + section Row Selection + section Cross-View Invariants | covered | TBL-ROW-001, TBL-SEL-001, TBL-CVI-005 |
| integration::feature workflows::global and column filters intersect before sorting applies | integration | positive | section Column And Global Filtering + section Row Sorting | covered | TBL-FLT-007, TBL-FLT-001, TBL-SRT-001 |
| integration::feature workflows::a registry extension, ordering, and visibility compose on one table | integration | positive | section Table Construction And Feature Composition + section Column Visibility, Ordering, And Pinning | covered | TBL-CON-004, TBL-VIS-004, TBL-VIS-001 |
| integration::feature workflows::the column helper drives a grouped table end to end | integration | positive | section Column Definitions And The Column Tree + section Headers And Footer Groups | covered | TBL-COL-007, TBL-HDR-002, TBL-COL-008 |
| integration::feature workflows::row lookup stays coherent across pipeline stages | integration | positive | section Rows And Cells + section Row Model Pipeline + section Grouping And Aggregation | covered | TBL-ROW-003, TBL-PIP-006, TBL-GRP-002 |
| integration::feature workflows::sort auto-inference picks distinct comparators per column type | integration | positive | section Row Sorting | covered | TBL-SRT-006, TBL-SRT-003 |
| integration::system workflows::a full dashboard session: filter, group, aggregate, expand, select, paginate | system_e2e | positive | section Cross-View Invariants | covered | TBL-CVI-001, TBL-CVI-002, TBL-CVI-005, TBL-CVI-006, TBL-CVI-007 |
| integration::system workflows::an inventory browser: controlled sorting, faceted narrowing, and resets | system_e2e | positive | section Cross-View Invariants + section Table State And Reactivity | covered | TBL-CVI-001, TBL-CVI-007, TBL-CVI-008, TBL-STA-006, TBL-STA-007 |
| integration::system workflows::a tree explorer: custom ids, expansion, visibility, and header integrity | system_e2e | positive | section Cross-View Invariants + section Row Expanding + section Rows And Cells + section Headers And Footer Groups | covered | TBL-CVI-002, TBL-CVI-003, TBL-EXP-003, TBL-ROW-001, TBL-HDR-003 |
| integration::system workflows::a search screen: global filter, column order, pinning, and page walk | system_e2e | positive | section Cross-View Invariants + section Column And Global Filtering + section Column Visibility, Ordering, And Pinning + section Row Pagination | covered | TBL-CVI-001, TBL-CVI-004, TBL-FLT-007, TBL-VIS-004, TBL-PAG-005 |

Total: 137 | kept (covered): 137 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 137

Layers: atomic 112 | integration 21 | system_e2e 4
Assertion kinds: positive 134 (98%) | failure_path 3 | shape 0 | no_check 0
Atomic positive share: 97%
