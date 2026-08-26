// Spec2Repo oracle - atomic tests (construction, state, columns, rows, headers, pipeline) for tanstack-table-core-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  constructTable,
  tableFeatures,
  tableOptions,
  createColumnHelper,
  getInitialTableState,
  stockFeatures,
  createCoreRowModel,
  createFilteredRowModel,
  createSortedRowModel,
  createPaginatedRowModel,
  createExpandedRowModel,
  columnFilteringFeature,
  columnVisibilityFeature,
  rowSortingFeature,
  rowPaginationFeature,
  rowSelectionFeature,
  rowExpandingFeature,
  sortFns,
  filterFns,
  functionalUpdate,
  isFunction,
  flattenBy,
} from "@tanstack/table-core";
import { storeReactivityBindings } from "@tanstack/table-core/store-reactivity-bindings";

type Rec = Record<string, unknown>;

const people: Rec[] = [
  { name: "beet", qty: 4 },
  { name: "apple", qty: 2 },
  { name: "cherry", qty: 9 },
];

function coreOnly(columns: Rec[], data: Rec[], extra: Rec = {}) {
  return constructTable({
    features: tableFeatures({
      coreReactivityFeature: storeReactivityBindings(),
      coreRowModel: createCoreRowModel(),
    }),
    columns: columns as any,
    data: data as any,
    ...(extra as object),
  } as any) as any as any;
}

describe("construction and composition", () => {
  test("constructTable projects the data array through the core row model", () => {
    /** Verifies: TBL-CON-001, TBL-PIP-002 */
    const table = coreOnly([{ accessorKey: "name" }], people);
    const rows = table.getCoreRowModel().rows;
    expect(rows.length).toBe(3);
    expect(rows.map((r: any) => r.getValue("name"))).toEqual([
      "beet",
      "apple",
      "cherry",
    ]);
  });

  test("an unregistered feature contributes no state slice and no setter", () => {
    /** Verifies: TBL-CON-002 */
    const table = coreOnly([{ accessorKey: "name" }], people);
    expect(table.store.state.sorting).toBeUndefined();
    expect((table as any).setSorting).toBeUndefined();
    expect(Object.keys(table.atoms)).not.toContain("sorting");
  });

  test("a registered feature contributes its state slice and setter", () => {
    /** Verifies: TBL-CON-002 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortedRowModel: createSortedRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
    } as any) as any;
    expect(table.store.state.sorting).toEqual([]);
    table.setSorting([{ id: "name", desc: false }]);
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: false }]);
  });

  test("a pipeline stage without its factory passes the previous stage through", () => {
    /** Verifies: TBL-CON-003, TBL-PIP-005 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
    } as any) as any;
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "apple", "cherry"]);
  });

  test("stockFeatures spreads into tableFeatures and registers stock features", () => {
    /** Verifies: TBL-CON-006 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        ...stockFeatures,
        coreRowModel: createCoreRowModel(),
      } as any),
      columns: [{ accessorKey: "name" }, { accessorKey: "qty" }],
      data: people,
    } as any) as any;
    expect(table.store.state.columnVisibility).toEqual({});
    table.setColumnVisibility({ qty: false });
    expect(table.getVisibleLeafColumns().map((c: any) => c.id)).toEqual([
      "name",
    ]);
  });

  test("tableOptions returns the options object it receives", () => {
    /** Verifies: TBL-CON-008 */
    const opts = tableOptions({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        coreRowModel: createCoreRowModel(),
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
    } as any) as any;
    expect(opts.columns).toEqual([{ accessorKey: "name" }]);
    const table = constructTable(opts) as any;
    expect(table.getCoreRowModel().rows.length).toBe(3);
  });

  test("setOptions with a new data array re-derives the row models", () => {
    /** Verifies: TBL-CON-009 */
    const table = coreOnly([{ accessorKey: "name" }], people);
    expect(table.getCoreRowModel().rows.length).toBe(3);
    table.setOptions((old: any) => ({
      ...old,
      data: [...people, { name: "daikon", qty: 1 }],
    }));
    expect(table.getCoreRowModel().rows.length).toBe(4);
    expect(table.getCoreRowModel().rows[3].getValue("name")).toBe("daikon");
  });

  test("initialState values overlay the feature defaults", () => {
    /** Verifies: TBL-CON-007, TBL-STA-002 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        rowPaginationFeature,
        coreRowModel: createCoreRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
      initialState: {
        sorting: [{ id: "name", desc: true }],
        pagination: { pageIndex: 2, pageSize: 25 },
      },
    } as any) as any;
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: true }]);
    expect(table.store.state.pagination).toEqual({
      pageIndex: 2,
      pageSize: 25,
    });
  });

  test("functionalUpdate applies an updater function or returns the plain value", () => {
    /** Verifies: TBL-CON-010 */
    expect(functionalUpdate((x: number) => x + 1, 4)).toBe(5);
    expect(functionalUpdate(9 as any, 4)).toBe(9);
  });

  test("isFunction accepts callables and rejects plain values", () => {
    /** Verifies: TBL-CON-011 */
    expect(isFunction(() => 1)).toBe(true);
    expect(isFunction({})).toBe(false);
    expect(isFunction("fn")).toBe(false);
  });

  test("flattenBy flattens a forest depth-first through the children accessor", () => {
    /** Verifies: TBL-CON-012 */
    type N = { v: number; kids: N[] };
    const forest: N[] = [
      { v: 1, kids: [{ v: 2, kids: [{ v: 3, kids: [] }] }] },
      { v: 4, kids: [] },
    ];
    expect(flattenBy(forest, (n) => n.kids).map((n) => n.v)).toEqual([
      1, 2, 3, 4,
    ]);
  });

  test("getInitialTableState merges feature defaults with the supplied overrides", () => {
    /** Verifies: TBL-CON-013 */
    const state = getInitialTableState(
      tableFeatures({ rowSortingFeature, rowPaginationFeature } as any),
      { sorting: [{ id: "x", desc: false }] } as any,
    ) as any;
    expect(state.sorting).toEqual([{ id: "x", desc: false }]);
    expect(state.pagination).toEqual({ pageIndex: 0, pageSize: 10 });
  });

  test("getRowId customizes row identity", () => {
    /** Verifies: TBL-ROW-001 */
    const table = coreOnly([{ accessorKey: "name" }], people, {
      getRowId: (row: Rec) => `key-${row.name}`,
    });
    expect(table.getCoreRowModel().rows.map((r: any) => r.id)).toEqual([
      "key-beet",
      "key-apple",
      "key-cherry",
    ]);
    expect(table.getRow("key-apple").getValue("name")).toBe("apple");
  });

  test("renderValue substitutes renderFallbackValue for undefined cell values", () => {
    /** Verifies: TBL-CON-007, TBL-ROW-007 */
    const table = coreOnly([{ accessorKey: "missing" }], [{ name: "x" }], {
      renderFallbackValue: "N/A",
    });
    const cell = table.getCoreRowModel().rows[0].getAllCells()[0];
    expect(cell.getValue()).toBeUndefined();
    expect(cell.renderValue()).toBe("N/A");
  });
});

describe("state and reactivity", () => {
  function statefulTable() {
    return constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        columnFilteringFeature,
        rowPaginationFeature,
        rowSelectionFeature,
        coreRowModel: createCoreRowModel(),
        sortedRowModel: createSortedRowModel(),
        filteredRowModel: createFilteredRowModel(),
        paginatedRowModel: createPaginatedRowModel(),
        sortFns,
        filterFns,
      }),
      columns: [{ accessorKey: "name" }, { accessorKey: "qty" }],
      data: people,
    } as any) as any;
  }

  test("registered slices expose their documented defaults", () => {
    /** Verifies: TBL-STA-002 */
    const table = statefulTable();
    expect(table.store.state.sorting).toEqual([]);
    expect(table.store.state.columnFilters).toEqual([]);
    expect(table.store.state.pagination).toEqual({ pageIndex: 0, pageSize: 10 });
    expect(table.store.state.rowSelection).toEqual({});
  });

  test("there is no getState method; the snapshot lives on the store", () => {
    /** Verifies: TBL-STA-001, TBL-STA-003 */
    const table = statefulTable();
    expect((table as any).getState).toBeUndefined();
    expect(table.store.state.sorting).toEqual([]);
  });

  test("setters accept a plain value or an updater of the previous value", () => {
    /** Verifies: TBL-STA-005 */
    const table = statefulTable();
    table.setSorting([{ id: "qty", desc: true }]);
    expect(table.store.state.sorting).toEqual([{ id: "qty", desc: true }]);
    table.setSorting((old: any[]) =>
      old.map((entry) => ({ ...entry, desc: !entry.desc })),
    );
    expect(table.store.state.sorting).toEqual([{ id: "qty", desc: false }]);
  });

  test("the store snapshot agrees with every per-key atom", () => {
    /** Verifies: TBL-STA-004 */
    const table = statefulTable();
    table.setSorting([{ id: "name", desc: false }]);
    table.setPagination({ pageIndex: 1, pageSize: 2 });
    for (const key of Object.keys(table.atoms)) {
      expect(table.store.state[key]).toEqual(table.atoms[key].get());
    }
    expect(table.atoms.sorting.get()).toEqual([{ id: "name", desc: false }]);
  });

  test("store.subscribe observes state transitions", () => {
    /** Verifies: TBL-STA-003 */
    const table = statefulTable();
    let notified = 0;
    table.store.subscribe(() => {
      notified += 1;
    });
    table.setSorting([{ id: "name", desc: false }]);
    expect(notified).toBeGreaterThan(0);
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: false }]);
  });

  test("reset with no argument restores the initialState value", () => {
    /** Verifies: TBL-STA-006 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
      initialState: { sorting: [{ id: "name", desc: true }] },
    } as any) as any;
    table.setSorting([{ id: "name", desc: false }]);
    table.resetSorting();
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: true }]);
  });

  test("reset with true restores the feature default", () => {
    /** Verifies: TBL-STA-006 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
      initialState: { sorting: [{ id: "name", desc: true }] },
    } as any) as any;
    table.setSorting([{ id: "name", desc: false }]);
    table.resetSorting(true);
    expect(table.store.state.sorting).toEqual([]);
  });

  test("a controlled slice overrides the internally stored value", () => {
    /** Verifies: TBL-STA-007 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortedRowModel: createSortedRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
      state: { sorting: [{ id: "name", desc: true }] },
    } as any) as any;
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: true }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["cherry", "beet", "apple"]);
  });

  test("a controlled key holding undefined falls back to the initialState value", () => {
    /** Verifies: TBL-STA-007 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
      initialState: { sorting: [{ id: "name", desc: false }] },
      state: { sorting: undefined },
    } as any) as any;
    expect(table.store.state.sorting).toEqual([{ id: "name", desc: false }]);
  });

  test("projections reflect a setter transition on the next read", () => {
    /** Verifies: TBL-STA-008 */
    const table = statefulTable();
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "apple", "cherry"]);
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["apple", "beet", "cherry"]);
  });
});

describe("columns and the column tree", () => {
  test("an explicit id wins over the accessor-derived id", () => {
    /** Verifies: TBL-COL-001 */
    const table = coreOnly([{ id: "label", accessorKey: "name" }], people);
    expect(table.getAllColumns().map((c: any) => c.id)).toEqual(["label"]);
    expect(table.getCoreRowModel().rows[0].getValue("label")).toBe("beet");
  });

  test("a dotted accessorKey derives an underscore id and traverses nested records", () => {
    /** Verifies: TBL-COL-003 */
    const table = coreOnly(
      [{ accessorKey: "user.name.first" }],
      [{ user: { name: { first: "ada" } } }],
    );
    expect(table.getAllColumns()[0].id).toBe("user_name_first");
    const row = table.getCoreRowModel().rows[0];
    expect(row.getValue("user_name_first")).toBe("ada");
    expect(row.getValue("user.name.first")).toBeUndefined();
  });

  test("a dotted accessorKey does not consult a literal dotted property", () => {
    /** Verifies: TBL-COL-003 */
    const table = coreOnly([{ accessorKey: "a.b" }], [{ "a.b": "literal" }]);
    expect(table.getCoreRowModel().rows[0].getValue("a_b")).toBeUndefined();
  });

  test("a string header serves as the column id when no accessor id exists", () => {
    /** Verifies: TBL-COL-001 */
    const table = coreOnly([{ header: "Actions" }], people);
    expect(table.getAllColumns().map((c: any) => c.id)).toEqual(["Actions"]);
  });

  test("a definition that resolves no id throws when the column tree materializes", () => {
    /** Verifies: TBL-COL-002, TBL-ERR-001 */
    const table = coreOnly([{ header: () => "x" }], people);
    expect(() => table.getAllColumns()).toThrow(Error);
  });

  test("an accessorFn without an explicit id throws when the column tree materializes", () => {
    /** Verifies: TBL-COL-004, TBL-ERR-002 */
    const table = coreOnly([{ accessorFn: (row: Rec) => row.name }], people);
    expect(() => table.getAllColumns()).toThrow(Error);
  });

  test("an accessorFn column computes values through the function", () => {
    /** Verifies: TBL-COL-004 */
    const table = coreOnly(
      [
        {
          id: "upper",
          accessorFn: (row: Rec) => String(row.name).toUpperCase(),
        },
      ],
      people,
    );
    expect(
      table.getCoreRowModel().rows.map((r: any) => r.getValue("upper")),
    ).toEqual(["BEET", "APPLE", "CHERRY"]);
  });

  test("a display column produces cells but no values", () => {
    /** Verifies: TBL-COL-005 */
    const table = coreOnly([{ id: "actions" }, { accessorKey: "name" }], people);
    const row = table.getCoreRowModel().rows[0];
    expect(row.getAllCells().map((c: any) => c.column.id)).toEqual([
      "actions",
      "name",
    ]);
    expect(row.getValue("actions")).toBeUndefined();
    expect(row.getValue("name")).toBe("beet");
  });

  test("a columns array creates a group column with child columns", () => {
    /** Verifies: TBL-COL-006, TBL-COL-010 */
    const table = coreOnly(
      [
        {
          id: "info",
          columns: [{ accessorKey: "name" }, { accessorKey: "qty" }],
        },
      ],
      people,
    );
    const info = table.getColumn("info");
    expect(info.columns.map((c: any) => c.id)).toEqual(["name", "qty"]);
    expect(info.depth).toBe(0);
    expect(table.getColumn("name").parent.id).toBe("info");
    expect(table.getColumn("name").depth).toBe(1);
  });

  test("createColumnHelper builds accessor, display, and group definitions", () => {
    /** Verifies: TBL-COL-007 */
    const helper = (createColumnHelper as any)() as any;
    expect(helper.accessor("name", { header: "Name" })).toEqual({
      header: "Name",
      accessorKey: "name",
    });
    expect(helper.display({ id: "actions" })).toEqual({ id: "actions" });
    const grouped = helper.group({
      id: "grp",
      columns: [helper.accessor("qty", {})],
    });
    expect(grouped.id).toBe("grp");
    expect(grouped.columns).toEqual([{ accessorKey: "qty" }]);
    const fnDef = helper.accessor((row: Rec) => row.name, { id: "alias" });
    expect(fnDef.id).toBe("alias");
    expect(typeof fnDef.accessorFn).toBe("function");
  });

  test("defaultColumn merges under each definition property by property", () => {
    /** Verifies: TBL-COL-008 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortFns,
      }),
      columns: [
        { accessorKey: "name" },
        { accessorKey: "qty", sortDescFirst: false },
      ],
      data: people,
      defaultColumn: { sortDescFirst: true, header: "H" },
    } as any) as any;
    expect(table.getColumn("name").columnDef.sortDescFirst).toBe(true);
    expect(table.getColumn("qty").columnDef.sortDescFirst).toBe(false);
    expect(table.getColumn("name").columnDef.header).toBe("H");
  });

  test("all, flat, and leaf column views expose the tree at different depths", () => {
    /** Verifies: TBL-COL-009 */
    const table = coreOnly(
      [
        { id: "info", columns: [{ accessorKey: "name" }] },
        { accessorKey: "qty" },
      ],
      people,
    );
    expect(table.getAllColumns().map((c: any) => c.id)).toEqual([
      "info",
      "qty",
    ]);
    expect(table.getAllFlatColumns().map((c: any) => c.id)).toEqual([
      "info",
      "name",
      "qty",
    ]);
    expect(table.getAllLeafColumns().map((c: any) => c.id)).toEqual([
      "name",
      "qty",
    ]);
  });

  test("getColumn returns undefined for an unknown id", () => {
    /** Verifies: TBL-COL-011 */
    const table = coreOnly([{ accessorKey: "name" }], people);
    expect(table.getColumn("nope")).toBeUndefined();
    expect(table.getColumn("name").id).toBe("name");
  });
});

describe("rows and cells", () => {
  const tree: Rec[] = [
    {
      name: "root1",
      kids: [{ name: "kid1", kids: [{ name: "grand1" }] }, { name: "kid2" }],
    },
    { name: "root2" },
  ];

  function treeTable() {
    return coreOnly([{ accessorKey: "name" }], tree, {
      getSubRows: (row: Rec) => row.kids,
    });
  }

  test("default row ids are index-based and children join with a dot", () => {
    /** Verifies: TBL-ROW-001 */
    const table = treeTable();
    expect(table.getCoreRowModel().rows.map((r: any) => r.id)).toEqual([
      "0",
      "1",
    ]);
    expect(table.getCoreRowModel().flatRows.map((r: any) => r.id)).toEqual([
      "0",
      "0.0",
      "0.0.0",
      "0.1",
      "1",
    ]);
  });

  test("rows expose index, depth, original, subRows, and getParentRow", () => {
    /** Verifies: TBL-ROW-002 */
    const table = treeTable();
    const root = table.getCoreRowModel().rows[0];
    const kid = root.subRows[1];
    expect(root.depth).toBe(0);
    expect(root.original.name).toBe("root1");
    expect(root.getParentRow()).toBeUndefined();
    expect(kid.id).toBe("0.1");
    expect(kid.index).toBe(1);
    expect(kid.depth).toBe(1);
    expect(kid.getParentRow().id).toBe("0");
    expect(root.subRows.length).toBe(2);
  });

  test("getRow resolves a known id and throws for an unknown id", () => {
    /** Verifies: TBL-ROW-003, TBL-ERR-003 */
    const table = treeTable();
    expect(table.getRow("1").original.name).toBe("root2");
    expect(() => table.getRow("99")).toThrow(Error);
  });

  test("getRow with true reaches rows excluded by later stages", () => {
    /** Verifies: TBL-ROW-003 */
    const table = constructTable({
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
    expect(
      table.getExpandedRowModel().rows.map((r: any) => r.id),
    ).toEqual(["0", "1"]);
    expect(table.getRow("0.0.0", true).original.name).toBe("grand1");
  });

  test("getValue caches the first read for the life of the row", () => {
    /** Verifies: TBL-ROW-004 */
    const data = [{ n: 1 }];
    const table = coreOnly([{ accessorKey: "n" }], data);
    const row = table.getCoreRowModel().rows[0];
    expect(row.getValue("n")).toBe(1);
    (data[0] as any).n = 999;
    expect(row.getValue("n")).toBe(1);
  });

  test("getValue returns undefined for an unknown column id", () => {
    /** Verifies: TBL-ROW-004 */
    const table = coreOnly([{ accessorKey: "name" }], people);
    expect(table.getCoreRowModel().rows[0].getValue("nope")).toBeUndefined();
  });

  test("getUniqueValues returns the value array used for faceting", () => {
    /** Verifies: TBL-ROW-005 */
    const table = coreOnly([{ accessorKey: "name" }], people);
    expect(table.getCoreRowModel().rows[0].getUniqueValues("name")).toEqual([
      "beet",
    ]);
  });

  test("cells join a row and a leaf column with a composite id", () => {
    /** Verifies: TBL-ROW-006, TBL-ROW-007 */
    const table = coreOnly(
      [{ accessorKey: "name" }, { accessorKey: "qty" }],
      people,
    );
    const row = table.getCoreRowModel().rows[1];
    const cells = row.getAllCells();
    expect(cells.length).toBe(2);
    expect(cells.map((c: any) => c.id)).toEqual(["1_name", "1_qty"]);
    expect(cells[0].getValue()).toBe("apple");
    expect(cells[0].renderValue()).toBe("apple");
    expect(cells[0].row).toBe(row);
    expect(cells[0].column.id).toBe("name");
  });
});

describe("headers and footer groups", () => {
  function groupedTable() {
    return coreOnly(
      [
        {
          id: "info",
          columns: [{ accessorKey: "name" }, { accessorKey: "cat" }],
        },
        { accessorKey: "qty" },
      ],
      [{ name: "a", cat: "x", qty: 1 }],
    );
  }

  test("a flat column list produces a single header group", () => {
    /** Verifies: TBL-HDR-001 */
    const table = coreOnly(
      [{ accessorKey: "name" }, { accessorKey: "qty" }],
      people,
    );
    const groups = table.getHeaderGroups();
    expect(groups.length).toBe(1);
    expect(groups[0].headers.map((h: any) => h.column.id)).toEqual([
      "name",
      "qty",
    ]);
    expect(groups[0].headers.every((h: any) => h.colSpan === 1)).toBe(true);
  });

  test("nested definitions produce one group per depth with spans and placeholders", () => {
    /** Verifies: TBL-HDR-001, TBL-HDR-002 */
    const table = groupedTable();
    const groups = table.getHeaderGroups();
    expect(groups.length).toBe(2);
    const top = groups[0].headers;
    expect(top.map((h: any) => h.column.id)).toEqual(["info", "qty"]);
    expect(top[0].colSpan).toBe(2);
    expect(top[0].isPlaceholder).toBe(false);
    expect(top[1].colSpan).toBe(1);
    expect(top[1].isPlaceholder).toBe(true);
    const bottom = groups[1].headers;
    expect(bottom.map((h: any) => h.column.id)).toEqual([
      "name",
      "cat",
      "qty",
    ]);
    expect(bottom.every((h: any) => h.isPlaceholder === false)).toBe(true);
  });

  test("colSpan values in every group sum to the visible leaf count", () => {
    /** Verifies: TBL-HDR-003 */
    const table = groupedTable();
    const leafCount = table.getVisibleLeafColumns
      ? table.getVisibleLeafColumns().length
      : table.getAllLeafColumns().length;
    expect(leafCount).toBe(3);
    const groups = table.getHeaderGroups();
    expect(groups.length).toBe(2);
    for (const group of groups) {
      const sum = group.headers.reduce(
        (acc: number, h: any) => acc + h.colSpan,
        0,
      );
      expect(sum).toBe(leafCount);
    }
  });

  test("flat and leaf header views expose the matrix without grouping", () => {
    /** Verifies: TBL-HDR-004 */
    const table = groupedTable();
    const flat = table.getFlatHeaders();
    expect(flat.length).toBe(5);
    const leaves = table.getLeafHeaders();
    const leafColumnIds = leaves.map((h: any) => h.column.id);
    expect(leafColumnIds).toContain("name");
    expect(leafColumnIds).toContain("cat");
    expect(leafColumnIds).toContain("qty");
  });

  test("footer groups mirror the header matrix in reverse order", () => {
    /** Verifies: TBL-HDR-004 */
    const table = groupedTable();
    const headerIds = table.getHeaderGroups().map((g: any) => g.id);
    const footerIds = table.getFooterGroups().map((g: any) => g.id);
    expect(headerIds.length).toBe(2);
    expect(footerIds.length).toBe(2);
    expect(footerIds).toEqual([...headerIds].reverse());
  });

  test("subHeaders link a group header to the headers beneath it", () => {
    /** Verifies: TBL-HDR-002 */
    const table = groupedTable();
    const top = table.getHeaderGroups()[0].headers[0];
    expect(top.subHeaders.map((h: any) => h.column.id)).toEqual([
      "name",
      "cat",
    ]);
  });
});

describe("row model pipeline", () => {
  function pipelineTable() {
    return constructTable({
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
        { name: "apricot", qty: 7 },
      ],
    } as any) as any;
  }

  test("each pre-model accessor returns the previous stage's output", () => {
    /** Verifies: TBL-PIP-001, TBL-PIP-003 */
    const table = pipelineTable();
    table.setColumnFilters([{ id: "name", value: "ap" }]);
    table.setSorting([{ id: "qty", desc: true }]);
    expect(table.getPreFilteredRowModel().rows.length).toBe(4);
    expect(
      table.getPreSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["apple", "apricot"]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["apricot", "apple"]);
    expect(table.getPrePaginatedRowModel().rows).toEqual(
      table.getExpandedRowModel().rows,
    );
  });

  test("getRowModel returns the final registered stage", () => {
    /** Verifies: TBL-PIP-004 */
    const table = pipelineTable();
    table.setPagination({ pageIndex: 0, pageSize: 2 });
    expect(table.getRowModel().rows.length).toBe(2);
    expect(table.getRowModel().rows).toEqual(table.getPaginatedRowModel().rows);
  });

  test("a manual stage option makes that stage pass through", () => {
    /** Verifies: TBL-PIP-005 */
    const table = constructTable({
      features: tableFeatures({
        coreReactivityFeature: storeReactivityBindings(),
        rowSortingFeature,
        coreRowModel: createCoreRowModel(),
        sortedRowModel: createSortedRowModel(),
        sortFns,
      }),
      columns: [{ accessorKey: "name" }],
      data: people,
      manualSorting: true,
    } as any) as any;
    table.setSorting([{ id: "name", desc: false }]);
    expect(
      table.getSortedRowModel().rows.map((r: any) => r.getValue("name")),
    ).toEqual(["beet", "apple", "cherry"]);
  });

  test("row models expose rows, flatRows, and rowsById", () => {
    /** Verifies: TBL-PIP-006 */
    const table = coreOnly(
      [{ accessorKey: "name" }],
      [{ name: "root", kids: [{ name: "kid" }] }],
      { getSubRows: (row: Rec) => row.kids },
    );
    const model = table.getCoreRowModel();
    expect(model.rows.map((r: any) => r.id)).toEqual(["0"]);
    expect(model.flatRows.map((r: any) => r.id)).toEqual(["0", "0.0"]);
    expect(model.rowsById["0.0"].original.name).toBe("kid");
  });

  test("the core model resolves sub-rows through getSubRows", () => {
    /** Verifies: TBL-PIP-002 */
    const table = coreOnly(
      [{ accessorKey: "name" }],
      [{ name: "root", kids: [{ name: "kid1" }, { name: "kid2" }] }],
      { getSubRows: (row: Rec) => row.kids },
    );
    const root = table.getCoreRowModel().rows[0];
    expect(root.subRows.map((r: any) => r.original.name)).toEqual([
      "kid1",
      "kid2",
    ]);
  });
});
