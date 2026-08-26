// Spec2Repo oracle - system_e2e tests for tanstack-table-core-engine-fullrepro-001
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
  createColumnHelper,
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
} from "@tanstack/table-core";
import { storeReactivityBindings } from "@tanstack/table-core/store-reactivity-bindings";

type Rec = Record<string, unknown>;

function allFeatures() {
  return tableFeatures({
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
    sortFns,
    filterFns,
    aggregationFns,
  });
}

describe("system workflows", () => {
  test("a full dashboard session: filter, group, aggregate, expand, select, paginate", () => {
    /** Verifies: TBL-CVI-001, TBL-CVI-002, TBL-CVI-005, TBL-CVI-006, TBL-CVI-007 */
    const orders: Rec[] = [
      { region: "east", product: "widget", amount: 100 },
      { region: "west", product: "widget", amount: 250 },
      { region: "east", product: "gadget", amount: 75 },
      { region: "west", product: "gadget", amount: 300 },
      { region: "east", product: "widget", amount: 50 },
      { region: "north", product: "gizmo", amount: 20 },
    ];
    const table = constructTable({
      features: allFeatures(),
      columns: [
        { accessorKey: "region" },
        { accessorKey: "product" },
        { accessorKey: "amount", aggregationFn: "sum" },
      ],
      data: orders as any,
    } as any) as any;

    // filter out the small order, then group by region
    table.setColumnFilters([{ id: "amount", value: [50, null] }]);
    expect(table.getFilteredRowModel().rows.length).toBe(5);
    table.setGrouping(["region"]);
    const groups = table.getGroupedRowModel().rows;
    expect(groups.map((r: any) => r.id)).toEqual([
      "region:east",
      "region:west",
    ]);
    expect(groups[0].getValue("amount")).toBe(225);
    expect(groups[1].getValue("amount")).toBe(550);

    // sort groups by aggregated amount, expand the top group
    table.setSorting([{ id: "amount", desc: true }]);
    const sorted = table.getSortedRowModel().rows;
    expect(sorted[0].getValue("region")).toBe("west");
    sorted[0].toggleExpanded();
    const expandedIds = table.getExpandedRowModel().rows.map((r: any) => r.id);
    expect(expandedIds[0]).toBe("region:west");
    expect(expandedIds.length).toBe(4);

    // select the expanded leaves, verify selection projections agree
    for (const leaf of sorted[0].getLeafRows()) {
      leaf.toggleSelected(true);
    }
    expect(table.getSelectedRowModel().rows.length).toBe(2);
    expect(
      table
        .getFilteredSelectedRowModel()
        .rows.map((r: any) => r.getValue("amount"))
        .sort((a: number, b: number) => a - b),
    ).toEqual([250, 300]);

    // paginate the expanded view
    table.setPagination({ pageIndex: 0, pageSize: 3 });
    expect(table.getRowModel().rows.length).toBe(3);
    expect(table.getPageCount()).toBe(2);
    expect(table.getRowCount()).toBe(4);

    // state snapshot agrees with atoms across the whole session
    for (const key of Object.keys(table.atoms)) {
      expect(table.store.state[key]).toEqual(table.atoms[key].get());
    }
  });

  test("an inventory browser: controlled sorting, faceted narrowing, and resets", () => {
    /** Verifies: TBL-CVI-001, TBL-CVI-007, TBL-CVI-008, TBL-STA-006, TBL-STA-007 */
    const stock: Rec[] = Array.from({ length: 12 }, (_, i) => ({
      sku: `sku${i}`,
      aisle: i % 3 === 0 ? "a1" : i % 3 === 1 ? "a2" : "a3",
      units: i * 10,
    }));
    const table = constructTable({
      features: allFeatures(),
      columns: [
        { accessorKey: "sku" },
        { accessorKey: "aisle" },
        { accessorKey: "units" },
      ],
      data: stock as any,
      initialState: { pagination: { pageIndex: 0, pageSize: 5 } },
      state: { sorting: [{ id: "units", desc: true }] },
    } as any) as any;

    // controlled sorting applies without any setter call
    expect(table.getSortedRowModel().rows[0].getValue("units")).toBe(110);

    // facet the aisle column, then narrow with a filter on units
    expect(table.getColumn("aisle").getFacetedUniqueValues().get("a1")).toBe(4);
    table.setColumnFilters([{ id: "units", value: [60, null] }]);
    expect(table.getFilteredRowModel().rows.length).toBe(6);
    expect(table.getColumn("units").getFacetedRowModel().rows.length).toBe(12);

    // pagination arithmetic follows the filtered count
    expect(table.getRowCount()).toBe(6);
    expect(table.getPageCount()).toBe(2);
    table.nextPage();
    expect(table.getPaginatedRowModel().rows.length).toBe(1);

    // resets return to initialState, not to feature defaults
    table.resetPagination();
    expect(table.store.state.pagination).toEqual({ pageIndex: 0, pageSize: 5 });
    table.resetColumnFilters();
    expect(table.store.state.columnFilters).toEqual([]);
    expect(table.getRowCount()).toBe(12);
  });

  test("a tree explorer: custom ids, expansion, visibility, and header integrity", () => {
    /** Verifies: TBL-CVI-002, TBL-CVI-003, TBL-EXP-003, TBL-ROW-001, TBL-HDR-003 */
    const fs: Rec[] = [
      {
        path: "/src",
        size: 0,
        children: [
          { path: "/src/index.ts", size: 120 },
          {
            path: "/src/lib",
            size: 0,
            children: [{ path: "/src/lib/util.ts", size: 80 }],
          },
        ],
      },
      { path: "/README.md", size: 10 },
    ];
    const helper = (createColumnHelper as any)() as any;
    const table = constructTable({
      features: allFeatures(),
      columns: helper.columns([
        helper.group({
          id: "file",
          columns: [
            helper.accessor("path", {}),
            helper.accessor("size", {}),
          ],
        }),
        helper.display({ id: "actions" }),
      ]),
      data: fs as any,
      getRowId: (row: Rec) => String(row.path),
      getSubRows: (row: Rec) => row.children as Rec[] | undefined,
    } as any) as any;

    // custom ids flow through the tree
    expect(table.getRow("/src/lib/util.ts", true).getValue("size")).toBe(80);

    // collapsed: only roots render
    expect(table.getRowModel().rows.map((r: any) => r.id)).toEqual([
      "/src",
      "/README.md",
    ]);

    // expand everything: depth-first interleaving
    table.toggleAllRowsExpanded(true);
    expect(table.getRowModel().rows.map((r: any) => r.id)).toEqual([
      "/src",
      "/src/index.ts",
      "/src/lib",
      "/src/lib/util.ts",
      "/README.md",
    ]);
    expect(table.getRow("/src/lib").getParentRow().id).toBe("/src");

    // hide a column: cells and header spans stay consistent
    table.setColumnVisibility({ size: false });
    const row = table.getRowModel().rows[0];
    expect(row.getVisibleCells().map((c: any) => c.column.id)).toEqual([
      "path",
      "actions",
    ]);
    for (const group of table.getHeaderGroups()) {
      const span = group.headers.reduce(
        (acc: number, h: any) => acc + h.colSpan,
        0,
      );
      expect(span).toBe(table.getVisibleLeafColumns().length);
    }
  });

  test("a search screen: global filter, column order, pinning, and page walk", () => {
    /** Verifies: TBL-CVI-001, TBL-CVI-004, TBL-FLT-007, TBL-VIS-004, TBL-PAG-005 */
    const catalog: Rec[] = [
      { title: "blue shirt", brand: "acme", price: 20 },
      { title: "red shirt", brand: "zenith", price: 25 },
      { title: "blue jeans", brand: "acme", price: 40 },
      { title: "green hat", brand: "orbit", price: 15 },
      { title: "blue socks", brand: "zenith", price: 5 },
    ];
    const table = constructTable({
      features: allFeatures(),
      columns: [
        { accessorKey: "title" },
        { accessorKey: "brand" },
        { accessorKey: "price" },
      ],
      data: catalog as any,
    } as any) as any;

    // global search narrows across all columns
    table.setGlobalFilter("blue");
    expect(
      table
        .getFilteredRowModel()
        .rows.map((r: any) => r.getValue("title"))
        .sort(),
    ).toEqual(["blue jeans", "blue shirt", "blue socks"]);

    // order and pin: projections partition consistently
    table.setColumnOrder(["price", "title", "brand"]);
    table.setColumnPinning({ start: ["brand"], end: [] });
    const start = table.getStartVisibleLeafColumns().map((c: any) => c.id);
    const center = table.getCenterVisibleLeafColumns().map((c: any) => c.id);
    expect(start).toEqual(["brand"]);
    expect(center).toEqual(["price", "title"]);
    expect(
      [...start, ...center, ...table.getEndVisibleLeafColumns().map((c: any) => c.id)].sort(),
    ).toEqual(table.getVisibleLeafColumns().map((c: any) => c.id).sort());

    // sort by price and walk pages of two
    table.setSorting([{ id: "price", desc: false }]);
    table.setPagination({ pageIndex: 0, pageSize: 2 });
    expect(
      table.getRowModel().rows.map((r: any) => r.getValue("price")),
    ).toEqual([5, 20]);
    table.nextPage();
    expect(
      table.getRowModel().rows.map((r: any) => r.getValue("price")),
    ).toEqual([40]);
    expect(table.getCanNextPage()).toBe(false);
    expect(table.getCanPreviousPage()).toBe(true);

    // the snapshot reflects the whole session
    expect(table.store.state.globalFilter).toBe("blue");
    expect(table.store.state.columnOrder).toEqual(["price", "title", "brand"]);
    expect(table.store.state.pagination.pageIndex).toBe(1);
  });
});
