// Spec2Repo oracle - integration tests for tanstack-table-core-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  constructTable,
  tableFeatures,
  createCoreRowModel,
  createFilteredRowModel,
  createSortedRowModel,
  createPaginatedRowModel,
  createExpandedRowModel,
  createGroupedRowModel,
  createFacetedRowModel,
  createFacetedUniqueValues,
  createFacetedMinMaxValues,
  columnFilteringFeature,
  columnFacetingFeature,
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
  sortFns,
  filterFns,
  aggregationFns,
  createColumnHelper,
} from "@tanstack/table-core";
import { storeReactivityBindings } from "@tanstack/table-core/store-reactivity-bindings";

type Rec = Record<string, unknown>;

const inventory: Rec[] = [
  { cat: "fruit", name: "banana", qty: 5 },
  { cat: "veg", name: "beet", qty: 2 },
  { cat: "fruit", name: "apple", qty: 8 },
  { cat: "veg", name: "daikon", qty: 4 },
  { cat: "fruit", name: "cherry", qty: 9 },
  { cat: "grain", name: "barley", qty: 6 },
];

function fullTable(extra: Rec = {}, data: Rec[] = inventory) {
  return constructTable({
    features: tableFeatures({
      coreReactivityFeature: storeReactivityBindings(),
      columnFilteringFeature,
      columnFacetingFeature,
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
      coreRowModel: createCoreRowModel(),
      filteredRowModel: createFilteredRowModel(),
      groupedRowModel: createGroupedRowModel(),
      sortedRowModel: createSortedRowModel(),
      expandedRowModel: createExpandedRowModel(),
      paginatedRowModel: createPaginatedRowModel(),
      facetedRowModel: createFacetedRowModel(),
      facetedUniqueValues: createFacetedUniqueValues(),
      facetedMinMaxValues: createFacetedMinMaxValues(),
      sortFns,
      filterFns,
      aggregationFns,
    }),
    columns: [
      { accessorKey: "cat" },
      { accessorKey: "name" },
      { accessorKey: "qty", aggregationFn: "sum" },
    ],
    data: data as any,
    ...(extra as object),
  } as any) as any;
}

describe("pipeline integration", () => {
  test("filtering, sorting, and pagination compose in pipeline order", () => {
    /** Verifies: TBL-PIP-001, TBL-PIP-003, TBL-PIP-004, TBL-CVI-002 */
    const table = fullTable();
    table.setColumnFilters([{ id: "cat", value: "fruit" }]);
    table.setSorting([{ id: "qty", desc: false }]);
    table.setPagination({ pageIndex: 0, pageSize: 2 });
    expect(table.getPreFilteredRowModel().rows.length).toBe(6);
    expect(table.getFilteredRowModel().rows.length).toBe(3);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["banana", "apple", "cherry"]);
    expect(
      table.getPaginatedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["banana", "apple"]);
    expect(table.getRowModel().rows).toEqual(table.getPaginatedRowModel().rows);
    table.nextPage();
    expect(
      table.getPaginatedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["cherry"]);
  });

  test("every pre-model equals the previous stage output across an active pipeline", () => {
    /** Verifies: TBL-PIP-003, TBL-CVI-002 */
    const table = fullTable();
    table.setColumnFilters([{ id: "cat", value: "veg" }]);
    table.setSorting([{ id: "name", desc: false }]);
    expect(table.getPreFilteredRowModel().rows).toEqual(
      table.getCoreRowModel().rows,
    );
    expect(table.getPreGroupedRowModel().rows).toEqual(
      table.getFilteredRowModel().rows,
    );
    expect(table.getPreSortedRowModel().rows).toEqual(
      table.getGroupedRowModel().rows,
    );
    expect(table.getPreExpandedRowModel().rows).toEqual(
      table.getSortedRowModel().rows,
    );
    expect(table.getPrePaginatedRowModel().rows).toEqual(
      table.getExpandedRowModel().rows,
    );
    expect(
      table.getFilteredRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "daikon"]);
  });

  test("state transitions stay consistent across store, atoms, and projections", () => {
    /** Verifies: TBL-STA-004, TBL-STA-008, TBL-CVI-001 */
    const table = fullTable();
    table.setSorting([{ id: "qty", desc: true }]);
    table.setColumnFilters([{ id: "cat", value: "fruit" }]);
    table.setColumnVisibility({ cat: false });
    for (const key of Object.keys(table.atoms)) {
      expect(table.store.state[key]).toEqual(table.atoms[key].get());
    }
    expect(table.store.state.sorting).toEqual([{ id: "qty", desc: true }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("qty")),
    ).toEqual([9, 8, 5]);
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "name",
      "qty",
    ]);
  });

  test("grouping and sorting interact: groups sort by aggregated values", () => {
    /** Verifies: TBL-GRP-005, TBL-SRT-001, TBL-PIP-001 */
    const table = fullTable();
    table.setGrouping(["cat"]);
    table.setSorting([{ id: "qty", desc: true }]);
    const rows = table.getSortedRowModel().rows;
    // veg and grain tie at 6; the sort is stable so first-encounter order holds
    expect(rows.map((r: any) => r.getValue("cat"))).toEqual([
      "fruit",
      "veg",
      "grain",
    ]);
    expect(rows.map((r: any) => r.getValue("qty"))).toEqual([22, 6, 6]);
  });

  test("expanding grouped rows surfaces leaf rows through pagination", () => {
    /** Verifies: TBL-EXP-003, TBL-GRP-001, TBL-PAG-001, TBL-PIP-001 */
    const table = fullTable();
    table.setGrouping(["cat"]);
    table.setPagination({ pageIndex: 0, pageSize: 4 });
    expect(
      table.getPaginatedRowModel().rows.map((r: any) => r.id),
    ).toEqual(["cat:fruit", "cat:veg", "cat:grain"]);
    table.toggleAllRowsExpanded(true);
    const page = table.getPaginatedRowModel().rows.map((r: any) => r.id);
    expect(page.length).toBe(4);
    expect(page[0]).toBe("cat:fruit");
    expect(table.getPrePaginatedRowModel().rows.length).toBe(9);
  });
});

describe("cross-view consistency", () => {
  test("hiding a column updates leaf views, cells, and header spans together", () => {
    /** Verifies: TBL-VIS-003, TBL-HDR-003, TBL-CVI-003 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        columnVisibilityFeature,
        coreRowModel: createCoreRowModel(),
      }),
      columns: [
        {
          id: "info",
          columns: [{ accessorKey: "cat" }, { accessorKey: "name" }],
        },
        { accessorKey: "qty" },
      ],
      data: inventory,
    } as any) as any;
    expect(table.getVisibleLeafColumns().length).toBe(3);
    table.setColumnVisibility({ name: false });
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "cat",
      "qty",
    ]);
    const row = table.getCoreRowModel().rows[0];
    expect(row.getVisibleCells().map((c: any) => c.column.id)).toEqual([
      "cat",
      "qty",
    ]);
    for (const group of table.getHeaderGroups()) {
      const span = group.headers.reduce(
        (acc: number, h: any) => acc + h.colSpan,
        0,
      );
      expect(span).toBe(2);
    }
    expect(table.getIsAllColumnsVisible()).toBe(false);
  });

  test("pinning regions partition the visible leaves under visibility changes", () => {
    /** Verifies: TBL-VIS-007, TBL-VIS-009, TBL-CVI-004 */
    const table = fullTable();
    table.setColumnPinning({ start: ["qty"], end: ["cat"] });
    table.setColumnVisibility({ name: false });
    const start = table.getStartVisibleLeafColumns().map((c: any) => c.id);
    const center = table.getCenterVisibleLeafColumns().map((c: any) => c.id);
    const end = table.getEndVisibleLeafColumns().map((c: any) => c.id);
    expect(start).toEqual(["qty"]);
    expect(center).toEqual([]);
    expect(end).toEqual(["cat"]);
    const all = table
      .getVisibleLeafColumns()
      .map((c: any) => c.id)
      .sort();
    expect([...start, ...center, ...end].sort()).toEqual(all);
  });

  test("selection membership survives filtering; the filtered variant intersects", () => {
    /** Verifies: TBL-SEL-005, TBL-SEL-003, TBL-CVI-005 */
    const table = fullTable();
    table.toggleAllRowsSelected(true);
    expect(table.getIsAllRowsSelected()).toBe(true);
    table.setColumnFilters([{ id: "cat", value: "veg" }]);
    expect(table.getSelectedRowModel().rows.length).toBe(6);
    expect(
      table
        .getFilteredSelectedRowModel()
        .rows.map((r: any) => r.getValue("name"))
        .sort(),
    ).toEqual(["beet", "daikon"]);
    for (const row of table.getFilteredSelectedRowModel().rows) {
      expect(row.getIsSelected()).toBe(true);
    }
  });

  test("group leaf rows partition the filtered set and aggregate consistently", () => {
    /** Verifies: TBL-GRP-003, TBL-GRP-005, TBL-CVI-006 */
    const table = fullTable();
    table.setGrouping(["cat"]);
    const groups = table.getGroupedRowModel().rows;
    expect(groups.length).toBe(3);
    const leafIds = groups.flatMap((g: any) =>
      g.getLeafRows().map((r: any) => r.id),
    );
    expect(leafIds.length).toBe(6);
    expect(leafIds.sort()).toEqual(
      table.getFilteredRowModel().rows.map((r: any) => r.id).sort(),
    );
    expect(groups.map((g: any) => g.getValue("qty"))).toEqual([22, 6, 6]);
    for (const group of groups) {
      const sum = group
        .getLeafRows()
        .reduce((acc: number, r: any) => acc + (r.getValue("qty") as number), 0);
      expect(group.getValue("qty")).toBe(sum);
    }
  });

  test("page arithmetic tracks the filtered row count", () => {
    /** Verifies: TBL-PAG-002, TBL-CVI-007 */
    const table = fullTable();
    table.setPagination({ pageIndex: 0, pageSize: 2 });
    expect(table.getRowCount()).toBe(6);
    expect(table.getPageCount()).toBe(3);
    table.setColumnFilters([{ id: "cat", value: "fruit" }]);
    expect(table.getRowCount()).toBe(3);
    expect(table.getPageCount()).toBe(2);
    expect(table.getPageOptions()).toEqual([0, 1]);
    table.lastPage();
    expect(table.getPaginatedRowModel().rows.length).toBe(1);
  });

  test("facets react to other columns' filters but not their own", () => {
    /** Verifies: TBL-FAC-001, TBL-FAC-002, TBL-CVI-008 */
    const table = fullTable();
    const catFacets = () => table.getColumn("cat").getFacetedUniqueValues();
    expect(catFacets().size).toBe(3);
    table.setColumnFilters([{ id: "cat", value: "fruit" }]);
    expect(catFacets().size).toBe(3);
    table.setColumnFilters([
      { id: "cat", value: "fruit" },
      { id: "qty", value: [8, 9] },
    ]);
    // qty in [8, 9] keeps only apple and cherry, both fruit
    expect(catFacets().size).toBe(1);
    expect(catFacets().get("fruit")).toBe(2);
    // qty's own facet ignores the qty filter but applies cat=fruit: {5, 8, 9}
    expect(table.getColumn("qty").getFacetedMinMaxValues()).toEqual([5, 9]);
  });
});

describe("state workflows", () => {
  test("controlled and uncontrolled slices coexist", () => {
    /** Verifies: TBL-STA-007, TBL-STA-005 */
    const table = fullTable({
      state: { sorting: [{ id: "name", desc: false }] },
    });
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["apple", "banana", "barley", "beet", "cherry", "daikon"]);
    table.setColumnFilters([{ id: "cat", value: "veg" }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "daikon"]);
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: false }]);
  });

  test("initialState seeds several slices and resets return to it", () => {
    /** Verifies: TBL-STA-002, TBL-STA-006 */
    const table = fullTable({
      initialState: {
        sorting: [{ id: "qty", desc: true }],
        pagination: { pageIndex: 1, pageSize: 3 },
        columnVisibility: { cat: false },
      },
    });
    expect(table.store.state.pagination).toEqual({ pageIndex: 1, pageSize: 3 });
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "name",
      "qty",
    ]);
    table.setPagination({ pageIndex: 0, pageSize: 10 });
    table.setSorting([]);
    table.resetPagination();
    table.resetSorting();
    expect(table.store.state.pagination).toEqual({ pageIndex: 1, pageSize: 3 });
    expect(table.store.state.sorting).toEqual([{ id: "qty", desc: true }]);
    table.resetPagination(true);
    expect(table.store.state.pagination).toEqual({
      pageIndex: 0,
      pageSize: 10,
    });
  });

  test("one subscriber observes transitions from several features", () => {
    /** Verifies: TBL-STA-003, TBL-STA-005 */
    const table = fullTable();
    const seen: string[] = [];
    table.store.subscribe(() => {
      seen.push(JSON.stringify(table.store.state.sorting));
    });
    table.setSorting([{ id: "name", desc: false }]);
    table.setColumnFilters([{ id: "cat", value: "veg" }]);
    table.setRowSelection({ "0": true });
    expect(seen.length).toBeGreaterThanOrEqual(3);
    expect(table.store.state.rowSelection).toEqual({ "0": true });
    expect(table.getFilteredRowModel().rows.length).toBe(2);
  });

  test("swapping data through setOptions preserves active state", () => {
    /** Verifies: TBL-CON-009, TBL-STA-008 */
    const table = fullTable();
    table.setSorting([{ id: "qty", desc: true }]);
    table.setOptions((old: any) => ({
      ...old,
      data: [
        { cat: "fruit", name: "kiwi", qty: 1 },
        { cat: "fruit", name: "mango", qty: 7 },
      ],
    }));
    expect(table.store.state.sorting).toEqual([{ id: "qty", desc: true }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["mango", "kiwi"]);
  });

  test("custom row ids key selection and expansion state", () => {
    /** Verifies: TBL-ROW-001, TBL-SEL-001, TBL-CVI-005 */
    const table = fullTable({
      getRowId: (row: Rec) => `sku-${row.name}`,
    });
    table.getRow("sku-beet").toggleSelected();
    expect(table.store.state.rowSelection).toEqual({ "sku-beet": true });
    expect(
      table.getSelectedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet"]);
  });
});

describe("feature workflows", () => {
  test("global and column filters intersect before sorting applies", () => {
    /** Verifies: TBL-FLT-007, TBL-FLT-001, TBL-SRT-001 */
    const table = fullTable();
    table.setGlobalFilter("b");
    table.setColumnFilters([{ id: "qty", value: [3, 9] }]);
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["banana", "barley"]);
    table.resetGlobalFilter();
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["apple", "banana", "barley", "cherry", "daikon"]);
  });

  test("a registry extension, ordering, and visibility compose on one table", () => {
    /** Verifies: TBL-CON-004, TBL-VIS-004, TBL-VIS-001 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        columnOrderingFeature,
        columnVisibilityFeature,
        coreRowModel: createCoreRowModel(),
        sortedRowModel: createSortedRowModel(),
        sortFns: {
          ...sortFns,
          reverseText: (a: any, b: any, columnId: string) =>
            String(b.getValue(columnId)).localeCompare(
              String(a.getValue(columnId)),
            ),
        },
      } as any),
      columns: [
        { accessorKey: "cat" },
        { accessorKey: "name", sortFn: "reverseText" },
        { accessorKey: "qty" },
      ],
      data: inventory,
    } as any) as any;
    table.setSorting([{ id: "name", desc: false }]);
    expect(table.getSortedRowModel().rows[0].getValue("name")).toBe("daikon");
    table.setColumnOrder(["name"]);
    table.setColumnVisibility({ qty: false });
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "name",
      "cat",
    ]);
  });

  test("the column helper drives a grouped table end to end", () => {
    /** Verifies: TBL-COL-007, TBL-HDR-002, TBL-COL-008 */
    const helper = (createColumnHelper as any)() as any;
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        coreRowModel: createCoreRowModel(),
      }),
      columns: helper.columns([
        helper.group({
          id: "profile",
          columns: [
            helper.accessor("name", {}),
            helper.accessor((row: Rec) => String(row.cat).toUpperCase(), {
              id: "cat_upper",
            }),
          ],
        }),
        helper.accessor("qty", {}),
      ]),
      data: inventory,
      defaultColumn: { footer: "total" },
    } as any) as any;
    expect(table.getAllLeafColumns().map((c: any) => c.id)).toEqual([
      "name",
      "cat_upper",
      "qty",
    ]);
    expect(table.getHeaderGroups().length).toBe(2);
    expect(table.getHeaderGroups()[0].headers[0].colSpan).toBe(2);
    expect(table.getCoreRowModel().rows[0].getValue("cat_upper")).toBe("FRUIT");
    expect(table.getColumn("qty").columnDef.footer).toBe("total");
  });

  test("row lookup stays coherent across pipeline stages", () => {
    /** Verifies: TBL-ROW-003, TBL-PIP-006, TBL-GRP-002 */
    const table = fullTable();
    table.setGrouping(["cat"]);
    const grouped = table.getGroupedRowModel();
    expect(grouped.rowsById["cat:veg"].getValue("cat")).toBe("veg");
    expect(table.getRow("cat:fruit").getLeafRows().length).toBe(3);
    expect(() => table.getRow("cat:missing")).toThrow(Error);
  });

  test("sort auto-inference picks distinct comparators per column type", () => {
    /** Verifies: TBL-SRT-006, TBL-SRT-003 */
    const data: Rec[] = [
      { label: "row10", num: 3, when: new Date("2024-06-01") },
      { label: "row2", num: 11, when: new Date("2022-03-01") },
      { label: "row1", num: 7, when: new Date("2023-09-01") },
    ];
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortedRowModel: createSortedRowModel(),
        sortFns,
      }),
      columns: [
        { accessorKey: "label" },
        { accessorKey: "num" },
        { accessorKey: "when" },
      ],
      data: data as any,
    } as any) as any;
    table.setSorting([{ id: "label", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("label")),
    ).toEqual(["row1", "row2", "row10"]);
    table.setSorting([{ id: "when", desc: false }]);
    expect(
      table
        .getSortedRowModel()
        .rows.map((r: any) => (r.getValue("when") as Date).getFullYear()),
    ).toEqual([2022, 2023, 2024]);
    table.setSorting([]);
    table.getColumn("num").toggleSorting();
    expect(table.store.state.sorting).toEqual([{ id: "num", desc: true }]);
  });
});
