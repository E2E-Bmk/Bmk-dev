// Spec2Repo oracle - integration tests for tinybase-reactive-store-fullrepro-001
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

test("metrics exclude non numeric values from numeric aggregation", () => {
    /** Verifies: TBASE-METRIC-001, TBASE-METRIC-002, TBASE-METRIC-003 */
    const store = createStore().setTable("pets", {
      a: { price: 2 },
      b: { price: "no" },
      c: { price: 5 },
      d: { price: null },
      e: { price: Infinity },
    });
    const metrics = createMetrics(store)
      .setMetricDefinition("total", "pets", "sum", "price")
      .setMetricDefinition("avg", "pets", "avg", "price")
      .setMetricDefinition("min", "pets", "min", "price")
      .setMetricDefinition("max", "pets", "max", "price");
    expect(metrics.getMetricIds()).toEqual(["total", "avg", "min", "max"]);
    expect([metrics.getMetric("total"), metrics.getMetric("avg"), metrics.getMetric("min"), metrics.getMetric("max")]).toEqual([
      7,
      7 / 3,
      0,
      5,
    ]);
  });

test("index definitions group rows into slice ids", () => {
    /** Verifies: TBASE-INDEX-001, TBASE-INDEX-002 */
    const store = createStore().setTable("pets", petRows());
    const indexes = createIndexes(store).setIndexDefinition("bySpecies", "pets", "species");
    expect(indexes.getSliceIds("bySpecies")).toEqual(["dog", "cat"]);
    expect(indexes.getSliceRowIds("bySpecies", "dog")).toEqual(["fido", "rex"]);
    expect(indexes.getSliceRowIds("bySpecies", "cat")).toEqual(["felix"]);
  });

test("relationships expose remote and local row projections", () => {
    /** Verifies: TBASE-REL-001, TBASE-REL-002, TBASE-REL-003 */
    const store = createStore()
      .setTable("pets", petRows())
      .setTable("owners", { "1": { name: "Ann" }, "2": { name: "Ben" } });
    const relationships = createRelationships(store).setRelationshipDefinition("owners", "pets", "owners", "ownerId");
    expect(relationships.getRemoteRowId("owners", "fido")).toBe("1");
    expect(relationships.getLocalRowIds("owners", "2")).toEqual(["rex", "felix"]);
    expect(relationships.getLinkedRowIds("owners", "fido")).toEqual(["fido"]);
  });

test("query definitions select and group source rows", () => {
    /** Verifies: TBASE-QUERY-001, TBASE-QUERY-002, TBASE-QUERY-003 */
    const store = createStore().setTable("pets", petRows());
    const queries = createQueries(store).setQueryDefinition("prices", "pets", ({ select, group }) => {
      select("species");
      select("price");
      group("price", "avg").as("avgPrice");
    });
    expect(queries.getResultTable("prices")).toEqual({
      "0": { species: "dog", avgPrice: 6 },
      "1": { species: "cat", avgPrice: 3 },
    });
  });

test("cell writes are consistent across readers listeners and transaction changes", () => {
    /** Verifies: TBASE-STORE-006, TBASE-TXN-003, TBASE-LISTEN-002 */
    const store = createStore();
    const calls: unknown[] = [];
    store.addCellListener("pets", "fido", "price", (_store, tableId, rowId, cellId, newCell) => {
      calls.push([tableId, rowId, cellId, newCell, store.getCell(tableId, rowId, cellId)]);
    });
    let changes: unknown;
    store.transaction(() => {
      store.setCell("pets", "fido", "price", 5);
      changes = store.getTransactionChanges();
    });
    expect(store.getTable("pets")).toEqual({ fido: { price: 5 } });
    expect(calls).toEqual([["pets", "fido", "price", 5, 5]]);
    expect(changes).toEqual([{ pets: { fido: { price: 5 } } }, {}, 1]);
  });

test("value writes are consistent across readers JSON listeners and transaction changes", () => {
    /** Verifies: TBASE-STORE-006, TBASE-STORE-010, TBASE-TXN-003, TBASE-LISTEN-002 */
    const store = createStore();
    const calls: unknown[] = [];
    store.addValueListener("open", () => calls.push([store.getValues(), JSON.parse(store.getValuesJson())]));
    let changes: unknown;
    store.transaction(() => {
      store.setValue("open", true);
      changes = store.getTransactionChanges();
    });
    expect(calls).toEqual([[{ open: true }, { open: true }]]);
    expect(changes).toEqual([{}, { open: true }, 1]);
  });

test("schema defaults appear in JSON and derived metrics", () => {
    /** Verifies: TBASE-STORE-014, TBASE-METRIC-002 */
    const store = createStore()
      .setTablesSchema({ pets: { price: { type: "number", default: 4 }, species: { type: "string", default: "unknown" } } })
      .setRow("pets", "fido", {});
    const metrics = createMetrics(store).setMetricDefinition("total", "pets", "sum", "price");
    expect(JSON.parse(store.getTablesJson())).toEqual({ pets: { fido: { price: 4, species: "unknown" } } });
    expect(metrics.getMetric("total")).toBe(4);
  });

test("metric listeners and iteration see recomputed values after store mutations", () => {
    /** Verifies: TBASE-METRIC-002, TBASE-DERIVED-001 */
    const store = createStore().setTable("pets", petRows());
    const metrics = createMetrics(store).setMetricDefinition("total", "pets", "sum", "price");
    const calls: unknown[] = [];
    metrics.addMetricListener("total", (_metrics, metricId, newMetric) => calls.push([metricId, newMetric]));
    store.setCell("pets", "felix", "price", 9);
    const iterated: unknown[] = [];
    metrics.forEachMetric((metricId, metric) => iterated.push([metricId, metric]));
    expect(calls).toEqual([["total", 21]]);
    expect(iterated).toEqual([["total", 21]]);
  });

test("index listeners and iteration see rows move between slices", () => {
    /** Verifies: TBASE-INDEX-002, TBASE-DERIVED-001 */
    const store = createStore().setTable("pets", petRows());
    const indexes = createIndexes(store).setIndexDefinition("bySpecies", "pets", "species");
    const calls: unknown[] = [];
    indexes.addSliceIdsListener("bySpecies", (idx, indexId) => calls.push([indexId, idx.getSliceIds(indexId)]));
    store.setCell("pets", "felix", "species", "dog");
    const iterated: unknown[] = [];
    indexes.forEachSlice("bySpecies", (sliceId, forEachRow) => {
      const rowIds: string[] = [];
      forEachRow((rowId) => rowIds.push(rowId));
      iterated.push([sliceId, rowIds]);
    });
    expect(calls.at(-1)).toEqual(["bySpecies", ["dog"]]);
    expect(iterated).toEqual([["dog", ["fido", "rex", "felix"]]]);
  });

test("relationship readers update when a remote row id source changes", () => {
    /** Verifies: TBASE-REL-002, TBASE-REL-003 */
    const store = createStore()
      .setTable("pets", petRows())
      .setTable("owners", { "1": { name: "Ann" }, "2": { name: "Ben" } });
    const relationships = createRelationships(store).setRelationshipDefinition("owners", "pets", "owners", "ownerId");
    store.setCell("pets", "fido", "ownerId", "2");
    expect(relationships.getRemoteRowId("owners", "fido")).toBe("2");
    expect(relationships.getLocalRowIds("owners", "2")).toEqual(["rex", "felix", "fido"]);
  });

test("query result readers update when source rows change", () => {
    /** Verifies: TBASE-QUERY-002, TBASE-QUERY-003 */
    const store = createStore().setTable("pets", petRows());
    const queries = createQueries(store).setQueryDefinition("prices", "pets", ({ select, group }) => {
      select("species");
      select("price");
      group("price", "avg").as("avgPrice");
    });
    store.setCell("pets", "felix", "price", 9);
    expect(queries.getResultTable("prices")).toEqual({
      "0": { species: "dog", avgPrice: 6 },
      "1": { species: "cat", avgPrice: 9 },
    });
    expect(queries.getResultSortedRowIds("prices", "avgPrice")).toEqual(["0", "1"]);
  });

test("query result listeners observe recomputed result tables", () => {
    /** Verifies: TBASE-QUERY-003 */
    const store = createStore().setTable("pets", petRows());
    const queries = createQueries(store).setQueryDefinition("dogs", "pets", ({ select, where }) => {
      select("species");
      select("price");
      where("species", "dog");
    });
    const calls: unknown[] = [];
    queries.addResultTableListener("dogs", (q, queryId) => calls.push(q.getResultTable(queryId)));
    store.setCell("pets", "felix", "species", "dog");
    expect(calls.at(-1)).toEqual({
      fido: { species: "dog", price: 5 },
      rex: { species: "dog", price: 7 },
      felix: { species: "dog", price: 3 },
    });
  });

test("checkpoint navigation restores derived metric projections", () => {
    /** Verifies: TBASE-CP-002, TBASE-METRIC-002 */
    const store = createStore().setTable("pets", { fido: { price: 5 } });
    const metrics = createMetrics(store).setMetricDefinition("total", "pets", "sum", "price");
    const checkpoints = createCheckpoints(store);
    const first = checkpoints.addCheckpoint("first");
    store.setCell("pets", "fido", "price", 9);
    checkpoints.addCheckpoint("second");
    expect(metrics.getMetric("total")).toBe(9);
    checkpoints.goTo(first);
    expect(store.getCell("pets", "fido", "price")).toBe(5);
    expect(metrics.getMetric("total")).toBe(5);
  });

test("checkpoint backward and forward navigation restores value projections", () => {
    /** Verifies: TBASE-CP-002 */
    const store = createStore().setValue("count", 1);
    const checkpoints = createCheckpoints(store);
    checkpoints.addCheckpoint("one");
    store.setValue("count", 2);
    checkpoints.addCheckpoint("two");
    store.setValue("count", 3);
    checkpoints.goBackward();
    expect(store.getValue("count")).toBe(2);
    checkpoints.goForward();
    expect(store.getValue("count")).toBe(3);
  });

test("middleware transformed writes are visible to readers listeners and metrics", () => {
    /** Verifies: TBASE-MW-002, TBASE-METRIC-002 */
    const store = createStore();
    const middleware = createMiddleware(store);
    const calls: unknown[] = [];
    middleware.addWillSetCellCallback((_tableId, _rowId, _cellId, cell) => Number(cell) * 2, "pets", null, "price");
    store.addCellListener("pets", "fido", "price", () => calls.push(store.getCell("pets", "fido", "price")));
    const metrics = createMetrics(store).setMetricDefinition("total", "pets", "sum", "price");
    store.setCell("pets", "fido", "price", 5);
    expect(store.getCell("pets", "fido", "price")).toBe(10);
    expect(calls).toEqual([10]);
    expect(metrics.getMetric("total")).toBe(10);
  });

test("destroyed metrics detach listeners from later store mutations", () => {
    /** Verifies: TBASE-DERIVED-001 */
    const store = createStore().setTable("pets", { fido: { price: 5 } });
    const metrics = createMetrics(store).setMetricDefinition("total", "pets", "sum", "price");
    const calls: unknown[] = [];
    metrics.addMetricListener("total", () => calls.push(metrics.getMetric("total")));
    metrics.destroy();
    store.setCell("pets", "fido", "price", 9);
    expect(metrics.getMetric("total")).toBeUndefined();
    expect(calls).toEqual([]);
  });

test("destroyed indexes clear definitions and detach from later store mutations", () => {
    /** Verifies: TBASE-DERIVED-001 */
    const store = createStore().setTable("pets", petRows());
    const indexes = createIndexes(store).setIndexDefinition("bySpecies", "pets", "species");
    indexes.destroy();
    store.setCell("pets", "felix", "species", "dog");
    expect(indexes.getSliceIds("bySpecies")).toEqual([]);
  });

test("destroyed relationships clear definitions and detach from later store mutations", () => {
    /** Verifies: TBASE-DERIVED-001 */
    const store = createStore()
      .setTable("pets", petRows())
      .setTable("owners", { "1": { name: "Ann" }, "2": { name: "Ben" } });
    const relationships = createRelationships(store).setRelationshipDefinition("owners", "pets", "owners", "ownerId");
    relationships.destroy();
    store.setCell("pets", "fido", "ownerId", "2");
    expect(relationships.getRemoteRowId("owners", "fido")).toBeUndefined();
  });

test("destroyed queries clear definitions and detach from later store mutations", () => {
    /** Verifies: TBASE-DERIVED-001 */
    const store = createStore().setTable("pets", petRows());
    const queries = createQueries(store).setQueryDefinition("dogs", "pets", ({ select, where }) => {
      select("species");
      where("species", "dog");
    });
    queries.destroy();
    store.setCell("pets", "felix", "species", "dog");
    expect(queries.getResultRowIds("dogs")).toEqual([]);
  });

test("destroyed checkpoints detach from later store mutations", () => {
    /** Verifies: TBASE-DERIVED-001, TBASE-CP-001 */
    const store = createStore().setValue("count", 1);
    const checkpoints = createCheckpoints(store);
    checkpoints.addCheckpoint("one");
    checkpoints.destroy();
    store.setValue("count", 2);
    expect(checkpoints.getCheckpointIds()).toEqual([[], "0", []]);
  });

test("destroyed middleware no longer transforms writes", () => {
    /** Verifies: TBASE-MW-001 */
    const store = createStore();
    const middleware = createMiddleware(store);
    middleware.addWillSetValueCallback((_valueId, value) => String(value).toUpperCase(), "name");
    middleware.destroy();
    store.setValue("name", "fido");
    expect(store.getValue("name")).toBe("fido");
  });

test("merge reconciles later store content and hash projections", () => {
    /** Verifies: TBASE-MERGE-003 */
    const left = createMergeableStore("left").setCell("pets", "fido", "name", "Fido").setValue("open", false);
    const right = createMergeableStore("right").setCell("pets", "fido", "name", "Rex").setValue("open", true);
    left.merge(right);
    expect(left.getContent()).toEqual([{ pets: { fido: { name: "Rex" } } }, { open: true }]);
    expect(left.getMergeableContentHashes().every((hash) => typeof hash === "number")).toBe(true);
  });

test("setDefaultContent installs mergeable content without exposing local mutation stamps", () => {
    /** Verifies: TBASE-MERGE-001, TBASE-MERGE-002 */
    const store = createMergeableStore("left").setCell("pets", "fido", "name", "Fido");
    store.setDefaultContent([{ pets: { rex: { name: "Rex" } } }, { open: true }]);
    expect(store.getContent()).toEqual([{ pets: { rex: { name: "Rex" } } }, { open: true }]);
  });

test("row sorting agrees with table readers after schema defaults are applied", () => {
    /** Verifies: TBASE-STORE-009, TBASE-STORE-014 */
    const store = createStore()
      .setTablesSchema({ pets: { price: { type: "number", default: 4 } } })
      .setTable("pets", { fido: { price: 5 }, rex: {}, felix: { price: 3 } });
    expect(store.getRow("pets", "rex")).toEqual({ price: 4 });
    expect(store.getSortedRowIds("pets", "price")).toEqual(["felix", "rex", "fido"]);
  });

test("JSON full content round trip updates derived index and query projections", () => {
    /** Verifies: TBASE-STORE-011, TBASE-INDEX-002, TBASE-QUERY-003 */
    const store = createStore().setTable("pets", { fido: { species: "dog" } });
    const indexes = createIndexes(store).setIndexDefinition("bySpecies", "pets", "species");
    const queries = createQueries(store).setQueryDefinition("allPets", "pets", ({ select }) => {
      select("species");
    });
    store.setJson(JSON.stringify([{ pets: { felix: { species: "cat" }, polly: { species: "bird" } } }, {}]));
    expect(indexes.getSliceIds("bySpecies")).toEqual(["cat", "bird"]);
    expect(queries.getResultTable("allPets")).toEqual({ felix: { species: "cat" }, polly: { species: "bird" } });
  });
