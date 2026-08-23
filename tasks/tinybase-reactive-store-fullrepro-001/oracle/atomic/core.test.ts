// Spec2Repo oracle - atomic tests for tinybase-reactive-store-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  addOrRemoveHash,
  createCheckpoints,
  createIndexes,
  createMergeableStore,
  createMetrics,
  createMiddleware,
  createQueries,
  createRelationships,
  createStore,
  defaultSorter,
  getHash,
  getHlcFunctions,
  getUniqueId,
} from "tinybase";

const petRows = () => ({
  fido: { species: "dog", price: 5, ownerId: "1" },
  rex: { species: "dog", price: 7, ownerId: "2" },
  felix: { species: "cat", price: 3, ownerId: "2" },
});

test("store creation exposes empty content projections", () => {
    /** Verifies: TBASE-STORE-001, TBASE-STORE-003, TBASE-STORE-004, TBASE-STORE-005 */
    const store = createStore();
    expect(store.getContent()).toEqual([{}, {}]);
    expect(store.getTables()).toEqual({});
    expect(store.getValues()).toEqual({});
    expect(store.hasTables()).toBe(false);
    expect(store.hasValues()).toBe(false);
  });

test("store writer methods are fluent and update table projections", () => {
    /** Verifies: TBASE-STORE-004, TBASE-STORE-006 */
    const store = createStore();
    expect(store.setCell("pets", "fido", "species", "dog")).toBe(store);
    expect(store.setCell("pets", "fido", "price", 5)).toBe(store);
    expect(store.getTableIds()).toEqual(["pets"]);
    expect(store.getRowIds("pets")).toEqual(["fido"]);
    expect(store.getCellIds("pets", "fido")).toEqual(["species", "price"]);
    expect(store.getCell("pets", "fido", "price")).toBe(5);
  });

test("store value writer methods are fluent and update value projections", () => {
    /** Verifies: TBASE-STORE-004, TBASE-STORE-006 */
    const store = createStore();
    expect(store.setValues({ open: true })).toBe(store);
    expect(store.setPartialValues({ employees: 3 })).toBe(store);
    expect(store.getValueIds()).toEqual(["open", "employees"]);
    expect(store.getValue("open")).toBe(true);
    expect(store.getValues()).toEqual({ open: true, employees: 3 });
  });

test("mapping callbacks receive current cell and value", () => {
    /** Verifies: TBASE-STORE-007 */
    const store = createStore().setCell("pets", "fido", "visits", 1).setValue("count", 2);
    store.setCell("pets", "fido", "visits", (current) => Number(current) + 4);
    store.setValue("count", (current) => Number(current) * 3);
    expect(store.getCell("pets", "fido", "visits")).toBe(5);
    expect(store.getValue("count")).toBe(6);
  });

test("partial row and partial values preserve unspecified entries", () => {
    /** Verifies: TBASE-STORE-006 */
    const store = createStore()
      .setRow("pets", "fido", { species: "dog", price: 5 })
      .setValues({ open: true, employees: 3 });
    store.setPartialRow("pets", "fido", { color: "brown" });
    store.setPartialValues({ open: false });
    expect(store.getRow("pets", "fido")).toEqual({ species: "dog", price: 5, color: "brown" });
    expect(store.getValues()).toEqual({ open: false, employees: 3 });
  });

test("delete methods remove only the named projection", () => {
    /** Verifies: TBASE-STORE-006 */
    const store = createStore()
      .setTable("pets", { fido: { species: "dog", price: 5 }, rex: { species: "dog" } })
      .setValues({ open: true, count: 2 });
    store.delCell("pets", "fido", "price").delRow("pets", "rex").delValue("count");
    expect(store.getTable("pets")).toEqual({ fido: { species: "dog" } });
    expect(store.getValues()).toEqual({ open: true });
  });

test("readers return clones that do not mutate store state", () => {
    /** Verifies: TBASE-STORE-004 */
    const store = createStore().setRow("pets", "fido", { species: "dog" }).setValue("open", true);
    const tables = store.getTables() as Record<string, Record<string, Record<string, unknown>>>;
    const values = store.getValues() as Record<string, unknown>;
    tables.pets.fido.species = "cat";
    values.open = false;
    expect(store.getCell("pets", "fido", "species")).toBe("dog");
    expect(store.getValue("open")).toBe(true);
  });

test("missing tables rows cells and values have empty or undefined projections", () => {
    /** Verifies: TBASE-STORE-004, TBASE-STORE-005 */
    const store = createStore().setCell("pets", "fido", "species", "dog");
    expect(store.getTable("missing")).toEqual({});
    expect(store.getRow("pets", "missing")).toEqual({});
    expect(store.getCell("pets", "fido", "missing")).toBeUndefined();
    expect(store.getValue("missing")).toBeUndefined();
    expect(store.hasTable("missing")).toBe(false);
    expect(store.hasCell("pets", "fido", "missing")).toBe(false);
  });

test("identifier readers preserve insertion order", () => {
    /** Verifies: TBASE-STORE-008 */
    const store = createStore()
      .setCell("pets", "fido", "species", "dog")
      .setCell("pets", "rex", "species", "dog")
      .setValue("open", true)
      .setValue("employees", 3);
    expect(store.getTableIds()).toEqual(["pets"]);
    expect(store.getRowIds("pets")).toEqual(["fido", "rex"]);
    expect(store.getValueIds()).toEqual(["open", "employees"]);
  });

test("sorted row ids honor descending offset and limit", () => {
    /** Verifies: TBASE-STORE-009 */
    const store = createStore().setTable("pets", {
      fido: { price: 5 },
      rex: { price: 3 },
      felix: {},
      polly: { price: 8 },
    });
    expect(store.getSortedRowIds("pets", "price", true, 1, 2)).toEqual(["fido", "rex"]);
  });

test("sorted row ids can use a custom sorter", () => {
    /** Verifies: TBASE-STORE-009 */
    const store = createStore().setTable("pets", {
      fido: { species: "dog" },
      felix: { species: "cat" },
      polly: { species: "parrot" },
    });
    expect(
      store.getSortedRowIds("pets", "species", false, 0, undefined, (left, right) =>
        String(right).localeCompare(String(left)),
      ),
    ).toEqual(["polly", "fido", "felix"]);
  });

test("JSON readers serialize table value and combined projections", () => {
    /** Verifies: TBASE-STORE-010 */
    const store = createStore().setTable("pets", { fido: { species: "dog" } }).setValue("open", true);
    expect(JSON.parse(store.getTablesJson())).toEqual({ pets: { fido: { species: "dog" } } });
    expect(JSON.parse(store.getValuesJson())).toEqual({ open: true });
    expect(JSON.parse(store.getJson())).toEqual([{ pets: { fido: { species: "dog" } } }, { open: true }]);
  });

test("JSON setters parse and apply their projections", () => {
    /** Verifies: TBASE-STORE-011 */
    const store = createStore();
    store.setTablesJson(JSON.stringify({ pets: { fido: { species: "dog" } } }));
    store.setValuesJson(JSON.stringify({ open: true }));
    expect(store.getContent()).toEqual([{ pets: { fido: { species: "dog" } } }, { open: true }]);
    store.setJson(JSON.stringify([{ people: { "1": { name: "Ann" } } }, { open: false }]));
    expect(store.getContent()).toEqual([{ people: { "1": { name: "Ann" } } }, { open: false }]);
  });

test("malformed JSON setters leave prior valid content unchanged", () => {
    /** Verifies: TBASE-STORE-012 */
    const store = createStore().setTable("pets", { fido: { species: "dog" } }).setValue("open", true);
    store.setTablesJson("{bad");
    store.setValuesJson("[1, 2]");
    expect(store.getContent()).toEqual([{ pets: { fido: { species: "dog" } } }, { open: true }]);
  });

test("schemas expose defaults through row and value readers", () => {
    /** Verifies: TBASE-STORE-013, TBASE-STORE-014 */
    const store = createStore().setSchema(
      { pets: { species: { type: "string", default: "unknown" }, age: { type: "number", default: 0 } } },
      { open: { type: "boolean", default: false } },
    );
    store.setRow("pets", "fido", {});
    expect(store.getRow("pets", "fido")).toEqual({ species: "unknown", age: 0 });
    expect(store.getValues()).toEqual({ open: false });
  });

test("schema violations reject invalid cells and values and notify listeners", () => {
    /** Verifies: TBASE-STORE-013, TBASE-STORE-014 */
    const store = createStore()
      .setTablesSchema({ pets: { price: { type: "number" } } })
      .setValuesSchema({ open: { type: "boolean" } })
      .setCell("pets", "fido", "price", 5)
      .setValue("open", true);
    const invalidCells: unknown[] = [];
    const invalidValues: unknown[] = [];
    store.addInvalidCellListener("pets", null, "price", (_store, tableId, rowId, cellId, cells) => {
      invalidCells.push([tableId, rowId, cellId, cells]);
    });
    store.addInvalidValueListener("open", (_store, valueId, values) => {
      invalidValues.push([valueId, values]);
    });
    store.setCell("pets", "fido", "price", "bad");
    store.setValue("open", "yes");
    expect(store.getCell("pets", "fido", "price")).toBe(5);
    expect(store.getValue("open")).toBe(true);
    expect(invalidCells).toEqual([["pets", "fido", "price", ["bad"]]]);
    expect(invalidValues).toEqual([["open", ["yes"]]]);
  });

test("transaction returns the action result", () => {
    /** Verifies: TBASE-TXN-001 */
    const store = createStore();
    const result = store.transaction(() => {
      store.setValue("open", true);
      return "done";
    });
    expect(result).toBe("done");
    expect(store.getValue("open")).toBe(true);
  });

test("transaction changes include table and value writes", () => {
    /** Verifies: TBASE-TXN-003 */
    const store = createStore().setCell("pets", "fido", "price", 5);
    let changes: unknown;
    store.transaction(() => {
      store.setCell("pets", "fido", "price", 7);
      store.setValue("open", true);
      changes = store.getTransactionChanges();
    });
    expect(changes).toEqual([{ pets: { fido: { price: 7 } } }, { open: true }, 1]);
  });

test("rollback callback restores pre-transaction content", () => {
    /** Verifies: TBASE-TXN-004 */
    const store = createStore().setCell("pets", "fido", "price", 5).setValue("open", true);
    store.transaction(() => {
      store.setCell("pets", "fido", "price", 9);
      store.setValue("open", false);
    }, () => true);
    expect(store.getContent()).toEqual([{ pets: { fido: { price: 5 } } }, { open: true }]);
  });

test("listener exceptions propagate after transaction cleanup", () => {
    /** Verifies: TBASE-LISTEN-001, TBASE-TXN-001 */
    const store = createStore();
    const listenerId = store.addCellListener("pets", "fido", "name", () => {
      throw new Error("listener failed");
    });
    expect(() => store.setCell("pets", "fido", "name", "Fido")).toThrow(Error);
    expect(store.getCell("pets", "fido", "name")).toBe("Fido");
    expect(store.delListener(listenerId).setCell("pets", "fido", "name", "Rex")).toBe(store);
    expect(store.getCell("pets", "fido", "name")).toBe("Rex");
  });

test("cell listeners match null row ids and can be deleted", () => {
    /** Verifies: TBASE-LISTEN-001, TBASE-LISTEN-003, TBASE-LISTEN-005 */
    const store = createStore();
    const calls: unknown[] = [];
    const listenerId = store.addCellListener("pets", null, "color", (_store, tableId, rowId, cellId, newCell, oldCell) => {
      calls.push([tableId, rowId, cellId, newCell, oldCell]);
    });
    store.setCell("pets", "fido", "color", "brown");
    store.setCell("pets", "felix", "color", "black");
    store.delListener(listenerId);
    store.setCell("pets", "fido", "color", "red");
    expect(calls).toEqual([
      ["pets", "fido", "color", "brown", undefined],
      ["pets", "felix", "color", "black", undefined],
    ]);
  });

test("callListener immediately invokes a registered listener", () => {
    /** Verifies: TBASE-LISTEN-001 */
    const store = createStore().setValue("open", true);
    const calls: unknown[] = [];
    const listenerId = store.addValueListener("open", (_store, valueId, newValue) => calls.push([valueId, newValue]));
    store.callListener(listenerId);
    expect(calls).toEqual([["open", true]]);
  });

test("mutator listener writes happen in the same notification cycle", () => {
    /** Verifies: TBASE-LISTEN-004 */
    const store = createStore().setValue("count", 0);
    const calls: unknown[] = [];
    store.addValueListener(
      "count",
      () => {
        if (store.getValue("count") === 1) {
          store.setValue("count", 2);
        }
      },
      true,
    );
    store.addValuesListener(() => calls.push(store.getValues()));
    store.setValue("count", 1);
    expect(store.getValue("count")).toBe(2);
    expect(calls.at(-1)).toEqual({ count: 2 });
  });

test("iteration visits current row cells and values", () => {
    /** Verifies: TBASE-LISTEN-002 */
    const store = createStore().setTable("pets", { fido: { species: "dog" }, rex: { species: "dog" } }).setValues({
      open: true,
      employees: 3,
    });
    const rows: unknown[] = [];
    const values: unknown[] = [];
    store.forEachRow("pets", (rowId, forEachCell) => {
      const cells: unknown[] = [];
      forEachCell((cellId, cell) => cells.push([cellId, cell]));
      rows.push([rowId, cells]);
    });
    store.forEachValue((valueId, value) => values.push([valueId, value]));
    expect(rows).toEqual([
      ["fido", [["species", "dog"]]],
      ["rex", [["species", "dog"]]],
    ]);
    expect(values).toEqual([
      ["open", true],
      ["employees", 3],
    ]);
  });

test("same table relationships stop linked row chains at cycles", () => {
    /** Verifies: TBASE-REL-003 */
    const store = createStore().setTable("people", {
      a: { next: "b" },
      b: { next: "c" },
      c: { next: "a" },
    });
    const relationships = createRelationships(store).setRelationshipDefinition("chain", "people", "people", "next");
    expect(relationships.getLinkedRowIds("chain", "a")).toEqual(["a", "b", "c"]);
  });

test("query definitions filter source rows with where clauses", () => {
    /** Verifies: TBASE-QUERY-002, TBASE-QUERY-003 */
    const store = createStore().setTable("pets", petRows());
    const queries = createQueries(store).setQueryDefinition("dogs", "pets", ({ select, where }) => {
      select("species");
      select("price");
      where("species", "dog");
    });
    expect(queries.getResultTable("dogs")).toEqual({
      fido: { species: "dog", price: 5 },
      rex: { species: "dog", price: 7 },
    });
  });

test("checkpoints expose backward current and forward ids", () => {
    /** Verifies: TBASE-CP-001 */
    const store = createStore().setValue("count", 1);
    const checkpoints = createCheckpoints(store);
    const first = checkpoints.addCheckpoint("first");
    store.setValue("count", 2);
    const second = checkpoints.addCheckpoint("second");
    store.setValue("count", 3);
    expect([first, second, checkpoints.getCheckpointIds()]).toEqual(["0", "1", [["0", "1"], undefined, []]]);
  });

test("checkpoint navigation restores store content", () => {
    /** Verifies: TBASE-CP-002 */
    const store = createStore().setValue("count", 1);
    const checkpoints = createCheckpoints(store);
    const first = checkpoints.addCheckpoint("first");
    store.setValue("count", 2);
    checkpoints.addCheckpoint("second");
    store.setValue("count", 3);
    checkpoints.goTo(first);
    expect(store.getValue("count")).toBe(1);
    expect(checkpoints.getCheckpointIds()).toEqual([[], "0", ["1", "2"]]);
  });

test("set middleware callbacks transform pending cell writes", () => {
    /** Verifies: TBASE-MW-001, TBASE-MW-002 */
    const store = createStore();
    const middleware = createMiddleware(store);
    middleware.addWillSetCellCallback((_tableId, _rowId, _cellId, cell) => String(cell).toUpperCase(), "pets", null, "name");
    store.setCell("pets", "fido", "name", "fido");
    expect(store.getCell("pets", "fido", "name")).toBe("FIDO");
  });

test("set middleware callbacks can reject pending cell writes", () => {
    /** Verifies: TBASE-MW-002 */
    const store = createStore().setCell("pets", "fido", "name", "FIDO");
    const middleware = createMiddleware(store);
    middleware.addWillSetCellCallback(() => undefined, "pets", null, "name");
    store.setCell("pets", "fido", "name", "Rex");
    expect(store.getCell("pets", "fido", "name")).toBe("FIDO");
  });

test("delete middleware callbacks decide whether deletion proceeds", () => {
    /** Verifies: TBASE-MW-003 */
    const store = createStore().setCell("pets", "fido", "name", "FIDO").setCell("pets", "locked", "name", "REX");
    const middleware = createMiddleware(store);
    middleware.addWillDelCellCallback((_tableId, rowId) => rowId !== "locked", "pets", null, "name");
    store.delCell("pets", "fido", "name");
    store.delCell("pets", "locked", "name");
    expect(store.getTable("pets")).toEqual({ locked: { name: "REX" } });
  });

test("missing deletion and listener ids leave the store usable", () => {
    /** Verifies: TBASE-STORE-006, TBASE-LISTEN-005 */
    const store = createStore().setCell("pets", "fido", "name", "Fido").setValue("open", true);
    expect(store.delCell("pets", "rex", "name").delValue("missing").delListener("missing")).toBe(store);
    expect(store.getContent()).toEqual([{ pets: { fido: { name: "Fido" } } }, { open: true }]);
    expect(store.setCell("pets", "rex", "name", "Rex").getRowIds("pets")).toEqual(["fido", "rex"]);
  });

test("mergeable store satisfies ordinary store content contract", () => {
    /** Verifies: TBASE-MERGE-001 */
    const store = createMergeableStore("left").setCell("pets", "fido", "species", "dog").setValue("open", true);
    expect(store.getContent()).toEqual([{ pets: { fido: { species: "dog" } } }, { open: true }]);
  });

test("mergeable content exposes stamped table and value projections", () => {
    /** Verifies: TBASE-MERGE-002 */
    const store = createMergeableStore("left").setCell("pets", "fido", "species", "dog").setValue("open", true);
    const mergeableContent = store.getMergeableContent();
    expect(mergeableContent).toHaveLength(2);
    expect(mergeableContent[0][0].pets[0].fido[0].species[0]).toBe("dog");
    expect(mergeableContent[1][0].open[0]).toBe(true);
  });

test("defaultSorter orders supported primitive categories deterministically", () => {
    /** Verifies: TBASE-COMMON-001 */
    expect([
      defaultSorter(undefined, null),
      defaultSorter(null, false),
      defaultSorter(false, true),
      defaultSorter(2, 10),
      defaultSorter("b", "a"),
    ]).toEqual([1, 1, -1, -1, 1]);
  });

test("getUniqueId returns a string of the requested length", () => {
    /** Verifies: TBASE-COMMON-002 */
    const id = getUniqueId(8);
    expect(typeof id).toBe("string");
    expect(id).toHaveLength(8);
  });

test("hash helpers are deterministic and reversible when combined twice", () => {
    /** Verifies: TBASE-COMMON-003 */
    const hash = getHash("abc");
    expect(hash).toBe(getHash("abc"));
    expect(addOrRemoveHash(addOrRemoveHash(123, hash), hash)).toBe(123);
  });

test("HLC helpers generate monotonic timestamps and observe external values", () => {
    /** Verifies: TBASE-COMMON-004 */
    const [getHlc, seenHlc] = getHlcFunctions("node");
    const first = getHlc();
    const second = getHlc();
    seenHlc(second);
    const third = getHlc();
    expect(first < second).toBe(true);
    expect(second < third).toBe(true);
  });
