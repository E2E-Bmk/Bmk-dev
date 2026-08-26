// Spec2Repo oracle - atomic tests (state features) for tanstack-table-core-engine-fullrepro-001
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
  aggregationFn_mean,
  sortFn_basic,
  filterFn_startsWith,
} from "@tanstack/table-core";
import { storeReactivityBindings } from "@tanstack/table-core/store-reactivity-bindings";

type Rec = Record<string, unknown>;

const produce: Rec[] = [
  { cat: "fruit", name: "banana", qty: 5 },
  { cat: "veg", name: "beet", qty: 2 },
  { cat: "fruit", name: "apple", qty: 8 },
  { cat: "veg", name: "daikon", qty: 4 },
];

function sortingTable(columns: Rec[], data: Rec[] = produce, extra: Rec = {}) {
  return constructTable({
    features: tableFeatures({
      coreReactivityFeature: storeReactivityBindings(),
      rowSortingFeature,
      coreRowModel: createCoreRowModel(),
      sortedRowModel: createSortedRowModel(),
      sortFns,
    }),
    columns: columns as any,
    data: data as any,
    ...(extra as object),
  } as any) as any;
}

function filteringTable(columns: Rec[], data: Rec[] = produce, extra: Rec = {}) {
  return constructTable({
    features: tableFeatures({
      coreReactivityFeature: storeReactivityBindings(),
      columnFilteringFeature,
      globalFilteringFeature,
      coreRowModel: createCoreRowModel(),
      filteredRowModel: createFilteredRowModel(),
      filterFns,
    }),
    columns: columns as any,
    data: data as any,
    ...(extra as object),
  } as any) as any;
}

describe("row sorting", () => {
  test("setSorting orders rows ascending and descending", () => {
    /** Verifies: TBL-SRT-001 */
    const table = sortingTable([{ accessorKey: "name" }]);
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["apple", "banana", "beet", "daikon"]);
    table.setSorting([{ id: "name", desc: true }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["daikon", "beet", "banana", "apple"]);
  });

  test("later sorting entries break ties left by earlier ones", () => {
    /** Verifies: TBL-SRT-001 */
    const table = sortingTable([{ accessorKey: "cat" }, { accessorKey: "qty" }]);
    table.setSorting([
      { id: "cat", desc: false },
      { id: "qty", desc: true },
    ]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("qty")),
    ).toEqual([8, 5, 4, 2]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("cat")),
    ).toEqual(["fruit", "fruit", "veg", "veg"]);
  });

  test("toggleSorting cycles a text column through asc, desc, unsorted", () => {
    /** Verifies: TBL-SRT-002 */
    const table = sortingTable([{ accessorKey: "name" }]);
    const col = table.getColumn("name");
    col.toggleSorting();
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: false }]);
    col.toggleSorting();
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: true }]);
    col.toggleSorting();
    expect(table.store.state.sorting).toEqual([]);
  });

  test("an explicit desc argument forces the direction", () => {
    /** Verifies: TBL-SRT-002 */
    const table = sortingTable([{ accessorKey: "name" }]);
    table.getColumn("name").toggleSorting(true);
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: true }]);
  });

  test("numeric columns and sortDescFirst columns start their cycle descending", () => {
    /** Verifies: TBL-SRT-003 */
    const numeric = sortingTable([{ accessorKey: "qty" }]);
    numeric.getColumn("qty").toggleSorting();
    expect(numeric.store.state.sorting).toEqual([{ id: "qty", desc: true }]);
    const flagged = sortingTable([
      { accessorKey: "name", sortDescFirst: true },
    ]);
    flagged.getColumn("name").toggleSorting();
    expect(flagged.store.state.sorting).toEqual([{ id: "name", desc: true }]);
  });

  test("clearSorting removes only that column's entry", () => {
    /** Verifies: TBL-SRT-004 */
    const table = sortingTable([{ accessorKey: "cat" }, { accessorKey: "qty" }]);
    table.setSorting([
      { id: "cat", desc: false },
      { id: "qty", desc: true },
    ]);
    table.getColumn("cat").clearSorting();
    expect(table.store.state.sorting).toEqual([{ id: "qty", desc: true }]);
  });

  test("getIsSorted and getSortIndex report per-column sort status", () => {
    /** Verifies: TBL-SRT-005 */
    const table = sortingTable([{ accessorKey: "cat" }, { accessorKey: "qty" }]);
    table.setSorting([
      { id: "cat", desc: false },
      { id: "qty", desc: true },
    ]);
    expect(table.getColumn("cat").getIsSorted()).toBe("asc");
    expect(table.getColumn("qty").getIsSorted()).toBe("desc");
    expect(table.getColumn("cat").getSortIndex()).toBe(0);
    expect(table.getColumn("qty").getSortIndex()).toBe(1);
    table.setSorting([]);
    expect(table.getColumn("cat").getIsSorted()).toBe(false);
    expect(table.getColumn("cat").getSortIndex()).toBe(-1);
  });

  test("an inline comparator sorts through the function directly", () => {
    /** Verifies: TBL-SRT-006, TBL-SRT-009 */
    const table = sortingTable([
      {
        accessorKey: "name",
        sortFn: (a: any, b: any, columnId: string) =>
          String(a.getValue(columnId)).length -
          String(b.getValue(columnId)).length,
      },
    ]);
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "apple", "banana", "daikon"]);
  });

  test("a custom registry entry is reachable by name", () => {
    /** Verifies: TBL-SRT-006 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortedRowModel: createSortedRowModel(),
        sortFns: {
          ...sortFns,
          byLen: (a: any, b: any, columnId: string) =>
            String(a.getValue(columnId)).length -
            String(b.getValue(columnId)).length,
        },
      } as any),
      columns: [{ accessorKey: "name", sortFn: "byLen" }],
      data: produce,
    } as any) as any;
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "apple", "banana", "daikon"]);
  });

  test("an unregistered sort name falls back to the basic comparator", () => {
    /** Verifies: TBL-SRT-007 */
    const table = sortingTable([{ accessorKey: "name", sortFn: "missing" }]);
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["apple", "banana", "beet", "daikon"]);
  });

  test("the sortFns registry bundles the six built-ins as individual exports", () => {
    /** Verifies: TBL-SRT-008 */
    expect(Object.keys(sortFns).sort()).toEqual([
      "alphanumeric",
      "alphanumericCaseSensitive",
      "basic",
      "datetime",
      "text",
      "textCaseSensitive",
    ]);
    expect(sortFns.basic).toBe(sortFn_basic);
  });

  test("auto resolution picks datetime ordering for Date columns", () => {
    /** Verifies: TBL-SRT-006 */
    const table = sortingTable(
      [{ accessorKey: "when" }],
      [
        { when: new Date("2024-05-01") },
        { when: new Date("2023-01-15") },
        { when: new Date("2025-02-20") },
      ],
    );
    table.setSorting([{ id: "when", desc: false }]);
    expect(
      table
        .getSortedRowModel()
        .rows.map((r: any) => (r.getValue("when") as Date).getFullYear()),
    ).toEqual([2023, 2024, 2025]);
  });

  test("auto resolution orders mixed alphanumeric strings numerically", () => {
    /** Verifies: TBL-SRT-006 */
    const table = sortingTable(
      [{ accessorKey: "tag" }],
      [{ tag: "item10" }, { tag: "item2" }, { tag: "item1" }],
    );
    table.setSorting([{ id: "tag", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("tag")),
    ).toEqual(["item1", "item2", "item10"]);
  });
});

describe("column and global filtering", () => {
  test("a string column filters by case-insensitive substring by default", () => {
    /** Verifies: TBL-FLT-005, TBL-FLT-006 */
    const table = filteringTable([{ accessorKey: "name" }]);
    table.setColumnFilters([{ id: "name", value: "AN" }]);
    expect(
      table.getFilteredRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["banana"]);
  });

  test("a number column filters by inclusive range with open bounds by default", () => {
    /** Verifies: TBL-FLT-005, TBL-FLT-006 */
    const table = filteringTable([{ accessorKey: "qty" }]);
    table.setColumnFilters([{ id: "qty", value: [4, 8] }]);
    expect(
      table
        .getFilteredRowModel()
        .rows.map((r: any) => r.getValue("qty"))
        .sort((a: number, b: number) => a - b),
    ).toEqual([4, 5, 8]);
    table.setColumnFilters([{ id: "qty", value: [null, 4] }]);
    expect(
      table
        .getFilteredRowModel()
        .rows.map((r: any) => r.getValue("qty"))
        .sort((a: number, b: number) => a - b),
    ).toEqual([2, 4]);
  });

  test("named registry filters apply their documented predicate", () => {
    /** Verifies: TBL-FLT-006 */
    const table = filteringTable([
      { accessorKey: "name", filterFn: "startsWith" },
      { accessorKey: "qty", filterFn: "equals" },
    ]);
    table.setColumnFilters([{ id: "name", value: "ba" }]);
    expect(
      table.getFilteredRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["banana"]);
    table.setColumnFilters([{ id: "qty", value: 2 }]);
    expect(
      table.getFilteredRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet"]);
  });

  test("an inline predicate receives row, column id, and filter value", () => {
    /** Verifies: TBL-FLT-004 */
    const table = filteringTable([
      {
        accessorKey: "name",
        filterFn: (row: any, columnId: string, value: number) =>
          String(row.getValue(columnId)).length === value,
      },
    ]);
    table.setColumnFilters([{ id: "name", value: 4 }]);
    expect(
      table.getFilteredRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet"]);
  });

  test("an unknown column id or unregistered name leaves rows unfiltered", () => {
    /** Verifies: TBL-FLT-002 */
    const t1 = filteringTable([{ accessorKey: "name" }]);
    t1.setColumnFilters([{ id: "nope", value: "x" }]);
    expect(t1.getFilteredRowModel().rows.length).toBe(4);
    const t2 = filteringTable([{ accessorKey: "name", filterFn: "missing" }]);
    t2.setColumnFilters([{ id: "name", value: "x" }]);
    expect(t2.getFilteredRowModel().rows.length).toBe(4);
  });

  test("per-column filter accessors upsert and report the entry", () => {
    /** Verifies: TBL-FLT-003 */
    const table = filteringTable([
      { accessorKey: "name" },
      { accessorKey: "qty" },
    ]);
    const col = table.getColumn("name");
    expect(col.getIsFiltered()).toBe(false);
    col.setFilterValue("be");
    expect(col.getIsFiltered()).toBe(true);
    expect(col.getFilterValue()).toBe("be");
    expect(table.store.state.columnFilters).toEqual([
      { id: "name", value: "be" },
    ]);
    col.setFilterValue("da");
    expect(table.store.state.columnFilters).toEqual([
      { id: "name", value: "da" },
    ]);
  });

  test("global filtering keeps rows where any filterable column matches", () => {
    /** Verifies: TBL-FLT-007, TBL-FLT-009 */
    const table = filteringTable([
      { accessorKey: "cat" },
      { accessorKey: "name" },
    ]);
    table.setGlobalFilter("ee");
    expect(
      table.getFilteredRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet"]);
    table.setGlobalFilter("fruit");
    expect(
      table
        .getFilteredRowModel()
        .rows.map((r: any) => r.getValue("name"))
        .sort(),
    ).toEqual(["apple", "banana"]);
  });

  test("enableGlobalFilter false excludes a column from global matching", () => {
    /** Verifies: TBL-FLT-008 */
    const table = filteringTable([
      { accessorKey: "cat", enableGlobalFilter: false },
      { accessorKey: "name" },
    ]);
    table.setGlobalFilter("beet");
    expect(
      table.getFilteredRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet"]);
    table.setGlobalFilter("fruit");
    expect(table.getFilteredRowModel().rows.length).toBe(0);
  });

  test("a display column never participates in global filtering", () => {
    /** Verifies: TBL-FLT-008 */
    const table = filteringTable([{ id: "actions" }, { accessorKey: "name" }]);
    expect(table.getColumn("actions").getCanGlobalFilter()).toBe(false);
    expect(table.getColumn("name").getCanGlobalFilter()).toBe(true);
  });
});

describe("row pagination", () => {
  const numbers: Rec[] = Array.from({ length: 25 }, (_, i) => ({ n: i }));

  function pagedTable(extra: Rec = {}) {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowPaginationFeature,
        coreRowModel: createCoreRowModel(),
        paginatedRowModel: createPaginatedRowModel(),
      }),
      columns: [{ accessorKey: "n" }],
      data: numbers,
      ...(extra as object),
    } as any) as any;
  }

  test("the default page holds the first ten rows", () => {
    /** Verifies: TBL-PAG-001, TBL-STA-002 */
    const table = pagedTable();
    expect(table.store.state.pagination).toEqual({ pageIndex: 0, pageSize: 10 });
    expect(
      table.getPaginatedRowModel().rows.map((r: any) => r.getValue("n")),
    ).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
  });

  test("page count and row count derive from the pre-paginated model", () => {
    /** Verifies: TBL-PAG-002 */
    const table = pagedTable();
    expect(table.getPageCount()).toBe(3);
    expect(table.getRowCount()).toBe(25);
    table.setPageSize(20);
    expect(table.getPageCount()).toBe(2);
  });

  test("navigation methods step, jump to first, and jump to last", () => {
    /** Verifies: TBL-PAG-005 */
    const table = pagedTable();
    table.nextPage();
    expect(table.store.state.pagination.pageIndex).toBe(1);
    expect(table.getPaginatedRowModel().rows[0].getValue("n")).toBe(10);
    table.previousPage();
    expect(table.store.state.pagination.pageIndex).toBe(0);
    table.lastPage();
    expect(table.store.state.pagination.pageIndex).toBe(2);
    expect(table.getPaginatedRowModel().rows.length).toBe(5);
    table.firstPage();
    expect(table.store.state.pagination.pageIndex).toBe(0);
  });

  test("setPageSize applies the size and resets the index", () => {
    /** Verifies: TBL-PAG-006 */
    const table = pagedTable();
    table.nextPage();
    table.setPageSize(20);
    expect(table.store.state.pagination).toEqual({
      pageIndex: 0,
      pageSize: 20,
    });
  });

  test("setPageIndex clamps at zero, and above only with a supplied pageCount", () => {
    /** Verifies: TBL-PAG-004 */
    const free = pagedTable();
    free.setPageIndex(-5);
    expect(free.store.state.pagination.pageIndex).toBe(0);
    free.setPageIndex(99);
    expect(free.store.state.pagination.pageIndex).toBe(99);
    const bounded = pagedTable({ pageCount: 3 });
    bounded.setPageIndex(99);
    expect(bounded.store.state.pagination.pageIndex).toBe(2);
  });

  test("page options and can-navigate flags follow the page window", () => {
    /** Verifies: TBL-PAG-003 */
    const table = pagedTable();
    expect(table.getPageOptions()).toEqual([0, 1, 2]);
    expect(table.getCanPreviousPage()).toBe(false);
    expect(table.getCanNextPage()).toBe(true);
    table.lastPage();
    expect(table.getCanPreviousPage()).toBe(true);
    expect(table.getCanNextPage()).toBe(false);
  });
});

describe("column visibility and ordering", () => {
  function visTable() {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        columnVisibilityFeature,
        columnOrderingFeature,
        coreRowModel: createCoreRowModel(),
      }),
      columns: [
        { accessorKey: "cat" },
        { accessorKey: "name" },
        { accessorKey: "qty" },
      ],
      data: produce,
    } as any) as any;
  }

  test("false in columnVisibility hides; absent ids stay visible", () => {
    /** Verifies: TBL-VIS-001, TBL-VIS-002 */
    const table = visTable();
    table.setColumnVisibility({ name: false });
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "cat",
      "qty",
    ]);
    expect(table.getColumn("name").getIsVisible()).toBe(false);
    expect(table.getColumn("cat").getIsVisible()).toBe(true);
  });

  test("toggleVisibility flips one column; toggleAllColumnsVisible writes all", () => {
    /** Verifies: TBL-VIS-002 */
    const table = visTable();
    table.getColumn("name").toggleVisibility();
    expect(table.getColumn("name").getIsVisible()).toBe(false);
    table.getColumn("name").toggleVisibility();
    expect(table.getColumn("name").getIsVisible()).toBe(true);
    table.toggleAllColumnsVisible(false);
    expect(table.getVisibleLeafColumns().length).toBe(0);
    expect(table.getIsAllColumnsVisible()).toBe(false);
    table.toggleAllColumnsVisible(true);
    expect(table.getVisibleLeafColumns().length).toBe(3);
    expect(table.getIsAllColumnsVisible()).toBe(true);
  });

  test("visible cells track visible leaf columns", () => {
    /** Verifies: TBL-VIS-003 */
    const table = visTable();
    table.setColumnVisibility({ name: false });
    const row = table.getCoreRowModel().rows[0];
    expect(row.getVisibleCells().map((c: any) => c.column.id)).toEqual([
      "cat",
      "qty",
    ]);
    expect(row.getAllCells().length).toBe(3);
  });

  test("columnOrder lists ids first; unlisted columns keep definition order", () => {
    /** Verifies: TBL-VIS-004 */
    const table = visTable();
    table.setColumnOrder(["qty", "cat", "name"]);
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "qty",
      "cat",
      "name",
    ]);
    table.setColumnOrder(["qty"]);
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "qty",
      "cat",
      "name",
    ]);
    table.setColumnOrder([]);
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "cat",
      "name",
      "qty",
    ]);
  });
});

describe("column pinning", () => {
  function pinTable() {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        columnPinningFeature,
        columnVisibilityFeature,
        coreRowModel: createCoreRowModel(),
      }),
      columns: [
        { accessorKey: "cat" },
        { accessorKey: "name" },
        { accessorKey: "qty" },
      ],
      data: produce,
    } as any) as any;
  }

  test("setColumnPinning assigns start and end regions", () => {
    /** Verifies: TBL-VIS-007 */
    const table = pinTable();
    table.setColumnPinning({ start: ["qty"], end: ["cat"] });
    expect(table.getStartVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "qty",
    ]);
    expect(table.getCenterVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "name",
    ]);
    expect(table.getEndVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "cat",
    ]);
  });

  test("column.pin moves between regions and false unpins", () => {
    /** Verifies: TBL-VIS-005 */
    const table = pinTable();
    table.getColumn("name").pin("start");
    expect(table.store.state.columnPinning).toEqual({
      start: ["name"],
      end: [],
    });
    table.getColumn("name").pin("end");
    expect(table.store.state.columnPinning).toEqual({
      start: [],
      end: ["name"],
    });
    table.getColumn("name").pin(false);
    expect(table.store.state.columnPinning).toEqual({ start: [], end: [] });
  });

  test("getIsPinned, getPinnedIndex, and getIsSomeColumnsPinned report regions", () => {
    /** Verifies: TBL-VIS-006, TBL-VIS-008 */
    const table = pinTable();
    expect(table.getIsSomeColumnsPinned()).toBe(false);
    table.setColumnPinning({ start: ["qty", "cat"], end: [] });
    expect(table.getColumn("qty").getIsPinned()).toBe("start");
    expect(table.getColumn("name").getIsPinned()).toBe(false);
    expect(table.getColumn("qty").getPinnedIndex()).toBe(0);
    expect(table.getColumn("cat").getPinnedIndex()).toBe(1);
    expect(table.getIsSomeColumnsPinned()).toBe(true);
    expect(table.getIsSomeColumnsPinned("start")).toBe(true);
    expect(table.getIsSomeColumnsPinned("end")).toBe(false);
  });

  test("pinning never changes visible leaf membership", () => {
    /** Verifies: TBL-VIS-009 */
    const table = pinTable();
    const before = table.getVisibleLeafColumns().map((c: any) => c.id);
    expect(before).toEqual(["cat", "name", "qty"]);
    table.setColumnPinning({ start: ["qty"], end: ["cat"] });
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual(before);
  });
});

describe("row selection", () => {
  function selTable() {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSelectionFeature,
        coreRowModel: createCoreRowModel(),
      }),
      columns: [{ accessorKey: "name" }],
      data: produce,
    } as any) as any;
  }

  test("toggleSelected marks a row in the rowSelection slice", () => {
    /** Verifies: TBL-SEL-001, TBL-SEL-002 */
    const table = selTable();
    const row = table.getCoreRowModel().rows[0];
    expect(row.getIsSelected()).toBe(false);
    row.toggleSelected();
    expect(row.getIsSelected()).toBe(true);
    expect(table.store.state.rowSelection).toEqual({ "0": true });
    row.toggleSelected(false);
    expect(table.store.state.rowSelection).toEqual({});
  });

  test("all-rows and some-rows flags follow the selected set", () => {
    /** Verifies: TBL-SEL-003 */
    const table = selTable();
    expect(table.getIsAllRowsSelected()).toBe(false);
    expect(table.getIsSomeRowsSelected()).toBe(false);
    table.getCoreRowModel().rows[0].toggleSelected();
    expect(table.getIsAllRowsSelected()).toBe(false);
    expect(table.getIsSomeRowsSelected()).toBe(true);
    table.toggleAllRowsSelected(true);
    expect(table.getIsAllRowsSelected()).toBe(true);
    expect(table.getIsSomeRowsSelected()).toBe(true);
  });

  test("toggleAllRowsSelected selects everything and no argument flips", () => {
    /** Verifies: TBL-SEL-004 */
    const table = selTable();
    table.toggleAllRowsSelected();
    expect(table.getIsAllRowsSelected()).toBe(true);
    expect(Object.keys(table.store.state.rowSelection).length).toBe(4);
    table.toggleAllRowsSelected(false);
    expect(table.store.state.rowSelection).toEqual({});
  });

  test("getSelectedRowModel returns exactly the selected rows", () => {
    /** Verifies: TBL-SEL-005 */
    const table = selTable();
    table.setRowSelection({ "1": true, "3": true });
    expect(
      table.getSelectedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "daikon"]);
    table.setRowSelection({});
    expect(table.getSelectedRowModel().rows.length).toBe(0);
  });
});

describe("row expanding", () => {
  const tree: Rec[] = [
    {
      name: "root1",
      kids: [{ name: "kid1", kids: [{ name: "grand1" }] }, { name: "kid2" }],
    },
    { name: "root2" },
  ];

  function expTable() {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowExpandingFeature,
        coreRowModel: createCoreRowModel(),
        expandedRowModel: createExpandedRowModel(),
      }),
      columns: [{ accessorKey: "name" }],
      data: tree,
      getSubRows: (row: Rec) => row.kids,
    } as any) as any;
  }

  test("toggleExpanded surfaces a row's children in the expanded model", () => {
    /** Verifies: TBL-EXP-002, TBL-EXP-003 */
    const table = expTable();
    const root = table.getRow("0");
    expect(root.getCanExpand()).toBe(true);
    expect(root.getIsExpanded()).toBe(false);
    expect(table.getExpandedRowModel().rows.map((r: any) => r.id)).toEqual([
      "0",
      "1",
    ]);
    root.toggleExpanded();
    expect(table.store.state.expanded).toEqual({ "0": true });
    expect(table.getExpandedRowModel().rows.map((r: any) => r.id)).toEqual([
      "0",
      "0.0",
      "0.1",
      "1",
    ]);
  });

  test("collapsed descendants stay reachable through flatRows", () => {
    /** Verifies: TBL-EXP-003 */
    const table = expTable();
    expect(table.getExpandedRowModel().rows.map((r: any) => r.id)).toEqual([
      "0",
      "1",
    ]);
    expect(
      table.getCoreRowModel().flatRows.map((r: any) => r.id),
    ).toContain("0.0.0");
  });

  test("toggleAllRowsExpanded writes the literal true and expands every level", () => {
    /** Verifies: TBL-EXP-001, TBL-EXP-004 */
    const table = expTable();
    table.toggleAllRowsExpanded(true);
    expect(table.store.state.expanded).toBe(true);
    expect(table.getExpandedRowModel().rows.map((r: any) => r.id)).toEqual([
      "0",
      "0.0",
      "0.0.0",
      "0.1",
      "1",
    ]);
    expect(table.getIsAllRowsExpanded()).toBe(true);
    table.toggleAllRowsExpanded(false);
    expect(table.getExpandedRowModel().rows.map((r: any) => r.id)).toEqual([
      "0",
      "1",
    ]);
  });

  test("a leaf row cannot expand; getIsExpanded is true under the literal true", () => {
    /** Verifies: TBL-EXP-001, TBL-EXP-002 */
    const table = expTable();
    expect(table.getRow("1").getCanExpand()).toBe(false);
    table.setExpanded(true);
    expect(table.getRow("0").getIsExpanded()).toBe(true);
    expect(table.getRow("0.0", true).getIsExpanded()).toBe(true);
  });
});

describe("grouping and aggregation", () => {
  function groupTable(columns: Rec[]) {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        columnGroupingFeature,
        rowAggregationFeature,
        coreRowModel: createCoreRowModel(),
        groupedRowModel: createGroupedRowModel(),
        aggregationFns,
      }),
      columns: columns as any,
      data: produce,
    } as any) as any;
  }

  test("grouping folds rows into one group row per distinct value", () => {
    /** Verifies: TBL-GRP-001, TBL-GRP-002 */
    const table = groupTable([{ accessorKey: "cat" }, { accessorKey: "name" }]);
    table.setGrouping(["cat"]);
    const rows = table.getGroupedRowModel().rows;
    expect(rows.map((r: any) => r.id)).toEqual(["cat:fruit", "cat:veg"]);
    expect(rows.map((r: any) => r.getValue("cat"))).toEqual(["fruit", "veg"]);
  });

  test("two-level grouping appends deeper ids with the > separator", () => {
    /** Verifies: TBL-GRP-002 */
    const table = groupTable([{ accessorKey: "cat" }, { accessorKey: "name" }]);
    table.setGrouping(["cat", "name"]);
    const fruit = table.getGroupedRowModel().rows[0];
    expect(fruit.id).toBe("cat:fruit");
    expect(fruit.subRows.map((r: any) => r.id)).toEqual([
      "cat:fruit>name:banana",
      "cat:fruit>name:apple",
    ]);
  });

  test("group rows expose grouping metadata and leaf rows", () => {
    /** Verifies: TBL-GRP-003, TBL-GRP-004 */
    const table = groupTable([{ accessorKey: "cat" }, { accessorKey: "name" }]);
    table.setGrouping(["cat"]);
    const fruit = table.getGroupedRowModel().rows[0];
    expect(fruit.getIsGrouped()).toBe(true);
    expect(fruit.groupingColumnId).toBe("cat");
    expect(fruit.groupingValue).toBe("fruit");
    expect(
      fruit.getLeafRows().map((r: any) => r.original.name),
    ).toEqual(["banana", "apple"]);
    expect(table.getColumn("cat").getIsGrouped()).toBe(true);
    expect(table.getColumn("name").getIsGrouped()).toBe(false);
  });

  test("a named aggregation summarizes group values", () => {
    /** Verifies: TBL-GRP-005, TBL-GRP-007 */
    const table = groupTable([
      { accessorKey: "cat" },
      { accessorKey: "name", aggregationFn: "unique" },
      { accessorKey: "qty", aggregationFn: "sum" },
    ]);
    table.setGrouping(["cat"]);
    const fruit = table.getGroupedRowModel().rows[0];
    expect(fruit.getValue("qty")).toBe(13);
    expect(fruit.getValue("name")).toEqual(["banana", "apple"]);
  });

  test("auto aggregation resolves numeric columns to sum when registered", () => {
    /** Verifies: TBL-GRP-006 */
    const table = groupTable([{ accessorKey: "cat" }, { accessorKey: "qty" }]);
    table.setGrouping(["cat"]);
    expect(table.getGroupedRowModel().rows[0].getValue("qty")).toBe(13);
  });

  test("without a registered aggregation the aggregated value is undefined", () => {
    /** Verifies: TBL-GRP-006 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        columnGroupingFeature,
        rowAggregationFeature,
        coreRowModel: createCoreRowModel(),
        groupedRowModel: createGroupedRowModel(),
      }),
      columns: [{ accessorKey: "cat" }, { accessorKey: "qty" }],
      data: produce,
    } as any) as any;
    table.setGrouping(["cat"]);
    expect(table.getGroupedRowModel().rows[0].getValue("qty")).toBeUndefined();
  });

  test("an inline aggregation definition object applies directly", () => {
    /** Verifies: TBL-GRP-006, TBL-GRP-007 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        columnGroupingFeature,
        rowAggregationFeature,
        coreRowModel: createCoreRowModel(),
        groupedRowModel: createGroupedRowModel(),
      }),
      columns: [
        { accessorKey: "cat" },
        { accessorKey: "qty", aggregationFn: aggregationFn_mean },
      ],
      data: produce,
    } as any) as any;
    table.setGrouping(["cat"]);
    expect(table.getGroupedRowModel().rows[0].getValue("qty")).toBe(6.5);
  });

  test("the aggregationFns registry bundles the eleven built-ins", () => {
    /** Verifies: TBL-GRP-007 */
    expect(Object.keys(aggregationFns).sort()).toEqual([
      "count",
      "extent",
      "first",
      "last",
      "max",
      "mean",
      "median",
      "min",
      "sum",
      "unique",
      "uniqueCount",
    ]);
  });

  test("cells report grouped, aggregated, and placeholder roles", () => {
    /** Verifies: TBL-GRP-008 */
    const table = groupTable([
      { accessorKey: "cat" },
      { accessorKey: "qty", aggregationFn: "sum" },
    ]);
    table.setGrouping(["cat"]);
    const fruit = table.getGroupedRowModel().rows[0];
    const catCell = fruit
      .getAllCells()
      .find((c: any) => c.column.id === "cat");
    const qtyCell = fruit
      .getAllCells()
      .find((c: any) => c.column.id === "qty");
    expect(catCell.getIsGrouped()).toBe(true);
    expect(qtyCell.getIsAggregated()).toBe(true);
    const leaf = fruit.subRows[0];
    const leafCatCell = leaf
      .getAllCells()
      .find((c: any) => c.column.id === "cat");
    expect(leafCatCell.getIsPlaceholder()).toBe(true);
  });
});

describe("column faceting", () => {
  function facetTable() {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        columnFilteringFeature,
        columnFacetingFeature,
        coreRowModel: createCoreRowModel(),
        filteredRowModel: createFilteredRowModel(),
        facetedRowModel: createFacetedRowModel(),
        facetedUniqueValues: createFacetedUniqueValues(),
        facetedMinMaxValues: createFacetedMinMaxValues(),
        filterFns,
      }),
      columns: [
        { accessorKey: "cat" },
        { accessorKey: "name" },
        { accessorKey: "qty" },
      ],
      data: produce,
    } as any) as any;
  }

  test("faceted unique values map each distinct value to its count", () => {
    /** Verifies: TBL-FAC-002 */
    const table = facetTable();
    const facets = table.getColumn("cat").getFacetedUniqueValues();
    expect(facets.get("fruit")).toBe(2);
    expect(facets.get("veg")).toBe(2);
    expect(facets.size).toBe(2);
  });

  test("faceted min-max returns the value bounds", () => {
    /** Verifies: TBL-FAC-003 */
    const table = facetTable();
    expect(table.getColumn("qty").getFacetedMinMaxValues()).toEqual([2, 8]);
  });

  test("a column's faceted model ignores its own filter but applies others", () => {
    /** Verifies: TBL-FAC-001 */
    const table = facetTable();
    table.setColumnFilters([{ id: "cat", value: "fruit" }]);
    expect(table.getFilteredRowModel().rows.length).toBe(2);
    expect(table.getColumn("cat").getFacetedRowModel().rows.length).toBe(4);
    table.setColumnFilters([
      { id: "cat", value: "fruit" },
      { id: "name", value: "app" },
    ]);
    expect(table.getColumn("cat").getFacetedRowModel().rows.length).toBe(1);
  });
});
