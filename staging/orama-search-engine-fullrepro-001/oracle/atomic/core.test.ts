// Spec2Repo oracle - atomic tests for orama-search-engine-fullrepro-001
import { expect, test } from "vitest";
import {
  create,
  insert,
  insertMultiple,
  update,
  updateMultiple,
  upsert,
  upsertMultiple,
  remove,
  removeMultiple,
  count,
  getByID,
  search,
  save,
  load,
} from "@orama/orama";

const guideSchema = {
  title: "string",
  body: "string",
  series: "string",
  pages: "number",
  digital: "boolean",
  shelf: "enum",
  topics: "string[]",
  extra: { weight: "number" },
} as const;

const guideDocs = [
  { id: "g1", title: "Granite Ridges Field Guide", body: "survey of granite ridge formations", series: "trail", pages: 120, digital: true, shelf: "geology", topics: ["rocks", "maps"], extra: { weight: 2 } },
  { id: "g2", title: "Granular Soils Handbook", body: "classification of granular soil profiles", series: "trail", pages: 260, digital: false, shelf: "geology", topics: ["soil"], extra: { weight: 5 } },
  { id: "g3", title: "River Otters Atlas", body: "habitats of river otters and wetland mammals", series: "trail", pages: 90, digital: true, shelf: "wildlife", topics: ["mammals", "maps"], extra: { weight: 1 } },
  { id: "g4", title: "Alpine Mosses Primer", body: "mosses of alpine meadows", series: "summit", pages: 45, digital: true, shelf: "botany", topics: ["plants"], extra: { weight: 3 } },
  { id: "g5", title: "Otter Tracking Notes", body: "tracking notes for otter surveys", series: "summit", pages: 150, digital: false, shelf: "wildlife", topics: ["mammals", "field"], extra: { weight: 4 } },
];

async function makeCatalog() {
  const db = create({ schema: guideSchema as any });
  await insertMultiple(db, guideDocs.map((d) => ({ ...d, topics: [...d.topics], extra: { ...d.extra } })));
  return db;
}

function ids(result: any): string[] {
  return result.hits.map((h: any) => h.id);
}

test("create yields an empty instance with zero count", async () => {
  /** Verifies: ORAMA-CRE-001 */
  const db = create({ schema: { name: "string", size: "number" } as any });
  expect(await count(db)).toBe(0);
  const all = await search(db, {} as any);
  expect(all.count).toBe(0);
  expect(all.hits).toEqual([]);
});

test("create rejects an unknown schema type string", async () => {
  /** Verifies: ORAMA-CRE-003, ORAMA-ERR-001 */
  let code = "";
  try {
    create({ schema: { when: "timestamp" } as any });
  } catch (e: any) {
    code = e.code;
    expect(e).toBeInstanceOf(Error);
  }
  expect(code).toBe("INVALID_SCHEMA_TYPE");
});

test("insert returns a generated string id when the document has none", async () => {
  /** Verifies: ORAMA-DOC-001 */
  const db = create({ schema: { name: "string" } as any });
  const id = await insert(db, { name: "brass sundial" });
  expect(typeof id).toBe("string");
  expect(id.length).toBeGreaterThan(0);
  expect((await getByID(db, id) as any).name).toBe("brass sundial");
});

test("insert uses the document id property as the stored id", async () => {
  /** Verifies: ORAMA-DOC-001 */
  const db = create({ schema: { name: "string" } as any });
  const id = await insert(db, { id: "sundial-7", name: "brass sundial" });
  expect(id).toBe("sundial-7");
  expect((await getByID(db, "sundial-7") as any).name).toBe("brass sundial");
});

test("insertMultiple returns the assigned ids in document order", async () => {
  /** Verifies: ORAMA-DOC-002 */
  const db = create({ schema: { name: "string" } as any });
  const out = await insertMultiple(db, [
    { id: "k1", name: "north gate" },
    { id: "k2", name: "south gate" },
    { id: "k3", name: "west gate" },
  ]);
  expect(out).toEqual(["k1", "k2", "k3"]);
  expect(await count(db)).toBe(3);
});

test("insert rejects a document whose value contradicts the schema type", async () => {
  /** Verifies: ORAMA-DOC-004, ORAMA-ERR-002 */
  const db = create({ schema: { name: "string", size: "number" } as any });
  let code = "";
  try {
    await insert(db, { name: "ladder", size: "tall" });
  } catch (e: any) {
    code = e.code;
  }
  expect(code).toBe("SCHEMA_VALIDATION_FAILURE");
  expect(await count(db)).toBe(0);
});

test("insert rejects a duplicate document id", async () => {
  /** Verifies: ORAMA-DOC-003, ORAMA-ERR-003 */
  const db = create({ schema: { name: "string" } as any });
  await insert(db, { id: "dup-1", name: "first" });
  let code = "";
  try {
    await insert(db, { id: "dup-1", name: "second" });
  } catch (e: any) {
    code = e.code;
  }
  expect(code).toBe("DOCUMENT_ALREADY_EXISTS");
  expect(await count(db)).toBe(1);
});

test("documents keep omitted schema fields absent and extra fields verbatim", async () => {
  /** Verifies: ORAMA-DOC-005, ORAMA-DOC-007 */
  const db = create({ schema: { name: "string", size: "number" } as any });
  const id = await insert(db, { name: "half filled", note: "not in schema" });
  const doc = await getByID(db, id) as any;
  expect(doc).toEqual({ name: "half filled", note: "not in schema" });
});

test("count reflects the number of stored documents", async () => {
  /** Verifies: ORAMA-DOC-006 */
  const db = await makeCatalog();
  expect(await count(db)).toBe(5);
});

test("getByID returns undefined for an unknown id", async () => {
  /** Verifies: ORAMA-DOC-007, ORAMA-ERR-007 */
  const db = await makeCatalog();
  expect((await getByID(db, "g1") as any).title).toBe("Granite Ridges Field Guide");
  expect(await getByID(db, "ghost-id")).toBeUndefined();
});

test("remove returns true for a present id and decrements count", async () => {
  /** Verifies: ORAMA-DOC-008 */
  const db = await makeCatalog();
  expect(await remove(db, "g3")).toBe(true);
  expect(await count(db)).toBe(4);
  expect(await getByID(db, "g3")).toBeUndefined();
});

test("remove returns false for a missing id and leaves the store unchanged", async () => {
  /** Verifies: ORAMA-DOC-008, ORAMA-ERR-008 */
  const db = await makeCatalog();
  expect(await remove(db, "ghost-id")).toBe(false);
  expect(await count(db)).toBe(5);
});

test("removeMultiple returns the number of documents actually removed", async () => {
  /** Verifies: ORAMA-DOC-009 */
  const db = await makeCatalog();
  const removed = await removeMultiple(db, ["g1", "ghost-id", "g4"]);
  expect(removed).toBe(2);
  expect(await count(db)).toBe(3);
});

test("update replaces the stored document and returns the new id", async () => {
  /** Verifies: ORAMA-DOC-010 */
  const db = await makeCatalog();
  const newId = await update(db, "g4", { id: "g4b", title: "Alpine Lichens Primer", body: "lichens of alpine boulders", series: "summit", pages: 50, digital: true, shelf: "botany", topics: ["plants"], extra: { weight: 3 } });
  expect(newId).toBe("g4b");
  expect(await count(db)).toBe(5);
  expect(await getByID(db, "g4")).toBeUndefined();
  expect((await getByID(db, "g4b") as any).title).toBe("Alpine Lichens Primer");
});

test("updateMultiple replaces several documents and returns the new ids", async () => {
  /** Verifies: ORAMA-DOC-011 */
  const db = await makeCatalog();
  const out = await updateMultiple(db, ["g1", "g2"], [
    { id: "h1", title: "Basalt Cliffs Field Guide", body: "survey of basalt cliffs", series: "trail", pages: 130, digital: true, shelf: "geology", topics: ["rocks"], extra: { weight: 2 } },
    { id: "h2", title: "Clay Soils Handbook", body: "classification of clay soils", series: "trail", pages: 250, digital: false, shelf: "geology", topics: ["soil"], extra: { weight: 5 } },
  ]);
  expect(out).toEqual(["h1", "h2"]);
  expect(await count(db)).toBe(5);
  expect(await getByID(db, "g1")).toBeUndefined();
  expect(await getByID(db, "g2")).toBeUndefined();
});

test("upsert inserts a new document when the id is absent", async () => {
  /** Verifies: ORAMA-DOC-012 */
  const db = await makeCatalog();
  const id = await upsert(db, { id: "g9", title: "Canyon Winds Reader", body: "wind patterns in canyons", series: "summit", pages: 75, digital: true, shelf: "geology", topics: ["maps"], extra: { weight: 1 } });
  expect(id).toBe("g9");
  expect(await count(db)).toBe(6);
});

test("upsert replaces an existing document without changing the count", async () => {
  /** Verifies: ORAMA-DOC-012 */
  const db = await makeCatalog();
  const id = await upsert(db, { id: "g5", title: "Otter Tracking Journal", body: "journal for otter tracking", series: "summit", pages: 160, digital: false, shelf: "wildlife", topics: ["mammals"], extra: { weight: 4 } });
  expect(id).toBe("g5");
  expect(await count(db)).toBe(5);
  expect((await getByID(db, "g5") as any).title).toBe("Otter Tracking Journal");
});

test("upsertMultiple mixes inserts and replacements and returns the ids", async () => {
  /** Verifies: ORAMA-DOC-013 */
  const db = await makeCatalog();
  const out = await upsertMultiple(db, [
    { id: "g5", title: "Otter Tracking Journal", body: "journal for otter tracking", series: "summit", pages: 160, digital: false, shelf: "wildlife", topics: ["mammals"], extra: { weight: 4 } },
    { id: "g10", title: "Meadow Bees Primer", body: "bees of open meadows", series: "summit", pages: 60, digital: true, shelf: "wildlife", topics: ["insects"], extra: { weight: 2 } },
  ]);
  expect(out).toEqual(["g5", "g10"]);
  expect(await count(db)).toBe(6);
});

test("search result carries hits with id score and document plus count and elapsed", async () => {
  /** Verifies: ORAMA-FTS-001 */
  const db = await makeCatalog();
  const result = await search(db, { term: "granite" });
  expect(result.count).toBe(1);
  expect(result.hits[0].id).toBe("g1");
  expect(typeof result.hits[0].score).toBe("number");
  expect(result.hits[0].score).toBeGreaterThan(0);
  expect((result.hits[0].document as any).title).toBe("Granite Ridges Field Guide");
  expect(typeof result.elapsed.raw).toBe("number");
  expect(typeof result.elapsed.formatted).toBe("string");
});

test("term matching is case-insensitive", async () => {
  /** Verifies: ORAMA-FTS-003 */
  const db = await makeCatalog();
  const result = await search(db, { term: "OTTER" });
  expect(ids(result).sort()).toEqual(["g3", "g5"]);
});

test("a query token matches indexed tokens by prefix", async () => {
  /** Verifies: ORAMA-FTS-004 */
  const db = await makeCatalog();
  const result = await search(db, { term: "gran" });
  expect(ids(result).sort()).toEqual(["g1", "g2"]);
});

test("omitting the term matches every stored document", async () => {
  /** Verifies: ORAMA-FTS-005 */
  const db = await makeCatalog();
  const result = await search(db, {} as any);
  expect(result.count).toBe(5);
  expect(ids(result).sort()).toEqual(["g1", "g2", "g3", "g4", "g5"]);
});

test("properties restricts full-text matching to the named string properties", async () => {
  /** Verifies: ORAMA-FTS-006 */
  const db = await makeCatalog();
  const inBody = await search(db, { term: "survey", properties: ["body"] });
  expect(ids(inBody).sort()).toEqual(["g1", "g5"]);
  const inTitle = await search(db, { term: "survey", properties: ["title"] });
  expect(inTitle.count).toBe(0);
});

test("searching an unknown property raises UNKNOWN_INDEX", async () => {
  /** Verifies: ORAMA-FTS-007, ORAMA-ERR-004 */
  const db = await makeCatalog();
  let code = "";
  try {
    await search(db, { term: "granite", properties: ["missing"] as any });
  } catch (e: any) {
    code = e.code;
  }
  expect(code).toBe("UNKNOWN_INDEX");
});

test("exact matching excludes prefix-only matches", async () => {
  /** Verifies: ORAMA-FTS-008 */
  const db = await makeCatalog();
  const loose = await search(db, { term: "otter" });
  expect(ids(loose).sort()).toEqual(["g3", "g5"]);
  const strict = await search(db, { term: "otter", exact: true });
  expect(ids(strict)).toEqual(["g5"]);
});

test("exact matching suppresses tolerance", async () => {
  /** Verifies: ORAMA-FTS-008 */
  const db = await makeCatalog();
  const result = await search(db, { term: "granate", tolerance: 1, exact: true });
  expect(result.count).toBe(0);
});

test("tolerance admits tokens within the edit distance", async () => {
  /** Verifies: ORAMA-FTS-009 */
  const db = await makeCatalog();
  const result = await search(db, { term: "granate", tolerance: 1 });
  expect(ids(result)).toEqual(["g1"]);
});

test("a misspelled token without tolerance matches nothing", async () => {
  /** Verifies: ORAMA-FTS-009 */
  const db = await makeCatalog();
  const result = await search(db, { term: "granate" });
  expect(result.count).toBe(0);
});

test("threshold zero returns only documents matching every token", async () => {
  /** Verifies: ORAMA-FTS-010 */
  const db = await makeCatalog();
  const result = await search(db, { term: "otter tracking", threshold: 0 });
  expect(ids(result)).toEqual(["g5"]);
});

test("default threshold returns documents matching any token", async () => {
  /** Verifies: ORAMA-FTS-010 */
  const db = await makeCatalog();
  const result = await search(db, { term: "otter tracking" });
  expect(ids(result).sort()).toEqual(["g3", "g5"]);
});

test("limit and offset slice ranked hits while count stays total", async () => {
  /** Verifies: ORAMA-FTS-012 */
  const db = await makeCatalog();
  const page = await search(db, { term: "otter", limit: 1, offset: 1 });
  expect(page.count).toBe(2);
  expect(page.hits.length).toBe(1);
  const full = await search(db, { term: "otter" });
  expect(page.hits[0].id).toBe(full.hits[1].id);
});

test("preflight reports the matched count with empty hits", async () => {
  /** Verifies: ORAMA-FTS-013 */
  const db = await makeCatalog();
  const result = await search(db, { term: "otter", preflight: true });
  expect(result.count).toBe(2);
  expect(result.hits).toEqual([]);
});

test("number filters support comparison operators", async () => {
  /** Verifies: ORAMA-STR-001 */
  const db = await makeCatalog();
  expect(ids(await search(db, { where: { pages: { gte: 120 } } })).sort()).toEqual(["g1", "g2", "g5"]);
  expect(ids(await search(db, { where: { pages: { lt: 90 } } })).sort()).toEqual(["g4"]);
  expect(ids(await search(db, { where: { pages: { eq: 150 } } })).sort()).toEqual(["g5"]);
});

test("number between filter is inclusive on both ends", async () => {
  /** Verifies: ORAMA-STR-001 */
  const db = await makeCatalog();
  const result = await search(db, { where: { pages: { between: [45, 120] } } });
  expect(ids(result).sort()).toEqual(["g1", "g3", "g4"]);
});

test("boolean filters accept a direct boolean value", async () => {
  /** Verifies: ORAMA-STR-002 */
  const db = await makeCatalog();
  expect(ids(await search(db, { where: { digital: true } })).sort()).toEqual(["g1", "g3", "g4"]);
  expect(ids(await search(db, { where: { digital: false } })).sort()).toEqual(["g2", "g5"]);
});

test("enum filters support eq in and nin operators", async () => {
  /** Verifies: ORAMA-STR-003 */
  const db = await makeCatalog();
  expect(ids(await search(db, { where: { shelf: { eq: "wildlife" } } })).sort()).toEqual(["g3", "g5"]);
  expect(ids(await search(db, { where: { shelf: { in: ["geology", "botany"] } } })).sort()).toEqual(["g1", "g2", "g4"]);
  expect(ids(await search(db, { where: { shelf: { nin: ["geology"] } } })).sort()).toEqual(["g3", "g4", "g5"]);
});

test("string filters match whole tokens without prefix expansion", async () => {
  /** Verifies: ORAMA-STR-004 */
  const db = await makeCatalog();
  expect(ids(await search(db, { where: { body: "otter" } as any }))).toEqual(["g5"]);
  expect(ids(await search(db, { where: { body: "otters" } as any }))).toEqual(["g3"]);
  expect(ids(await search(db, { where: { series: "trail" } as any })).sort()).toEqual(["g1", "g2", "g3"]);
});

test("string array filters match documents containing the element", async () => {
  /** Verifies: ORAMA-STR-005 */
  const db = await makeCatalog();
  const result = await search(db, { where: { topics: "maps" } as any });
  expect(ids(result).sort()).toEqual(["g1", "g3"]);
});

test("nested dot path properties participate in filters", async () => {
  /** Verifies: ORAMA-CRE-002, ORAMA-STR-001 */
  const db = await makeCatalog();
  const result = await search(db, { where: { "extra.weight": { gte: 4 } } });
  expect(ids(result).sort()).toEqual(["g2", "g5"]);
});

test("filtering on an unknown property raises UNKNOWN_FILTER_PROPERTY", async () => {
  /** Verifies: ORAMA-STR-007, ORAMA-ERR-005 */
  const db = await makeCatalog();
  let code = "";
  try {
    await search(db, { where: { ghost: { eq: 1 } } as any });
  } catch (e: any) {
    code = e.code;
  }
  expect(code).toBe("UNKNOWN_FILTER_PROPERTY");
});

test("enum facets report distinct value buckets and their count", async () => {
  /** Verifies: ORAMA-STR-008 */
  const db = await makeCatalog();
  const result = await search(db, { facets: { shelf: {} } as any });
  expect(result.facets!.shelf.values).toEqual({ geology: 2, wildlife: 2, botany: 1 });
  expect(result.facets!.shelf.count).toBe(3);
});

test("boolean facets bucket documents under true and false string keys", async () => {
  /** Verifies: ORAMA-STR-008 */
  const db = await makeCatalog();
  const result = await search(db, { facets: { digital: {} } as any });
  expect(result.facets!.digital.values).toEqual({ true: 3, false: 2 });
});

test("string array facets count documents per distinct element", async () => {
  /** Verifies: ORAMA-STR-008 */
  const db = await makeCatalog();
  const result = await search(db, { facets: { topics: {} } as any });
  expect(result.facets!.topics.values).toEqual({ rocks: 1, maps: 2, soil: 1, mammals: 2, plants: 1, field: 1 });
});

test("number facets bucket matched documents into inclusive ranges", async () => {
  /** Verifies: ORAMA-STR-009 */
  const db = await makeCatalog();
  const result = await search(db, { facets: { pages: { ranges: [{ from: 0, to: 100 }, { from: 101, to: 300 }] } } as any });
  expect(result.facets!.pages.values).toEqual({ "0-100": 2, "101-300": 3 });
});

test("string facets honor sort and limit options", async () => {
  /** Verifies: ORAMA-STR-010 */
  const db = await makeCatalog();
  const result = await search(db, { facets: { series: { sort: "ASC", limit: 1 } } as any });
  expect(result.facets!.series.values).toEqual({ summit: 2 });
  expect(result.facets!.series.count).toBe(2);
});

test("sortBy orders hits by a number property in both directions", async () => {
  /** Verifies: ORAMA-STR-011 */
  const db = await makeCatalog();
  expect(ids(await search(db, { sortBy: { property: "pages" } }))).toEqual(["g4", "g3", "g1", "g5", "g2"]);
  expect(ids(await search(db, { sortBy: { property: "pages", order: "DESC" } }))).toEqual(["g2", "g5", "g1", "g3", "g4"]);
});

test("sortBy orders hits by a nested dot path property", async () => {
  /** Verifies: ORAMA-STR-011 */
  const db = await makeCatalog();
  expect(ids(await search(db, { sortBy: { property: "extra.weight", order: "DESC" } }))).toEqual(["g2", "g5", "g4", "g1", "g3"]);
});

test("sortBy accepts a comparator over id score document triples", async () => {
  /** Verifies: ORAMA-STR-012 */
  const db = await makeCatalog();
  const result = await search(db, { sortBy: (a: any, b: any) => (a[2].extra.weight as number) - (b[2].extra.weight as number) });
  expect(ids(result)).toEqual(["g3", "g1", "g4", "g5", "g2"]);
});

test("groupBy partitions matched documents and bounds results per group", async () => {
  /** Verifies: ORAMA-STR-013 */
  const db = await makeCatalog();
  const result = await search(db, { groupBy: { properties: ["series"], maxResult: 2 } as any, sortBy: { property: "pages" } });
  const groups = (result.groups as any[]).map((g) => ({ values: g.values, n: g.result.length }));
  expect(groups.length).toBe(2);
  const bySeries = Object.fromEntries(groups.map((g) => [g.values[0], g.n]));
  expect(bySeries).toEqual({ trail: 2, summit: 2 });
});

test("groupBy rejects enum properties", async () => {
  /** Verifies: ORAMA-STR-014, ORAMA-ERR-006 */
  const db = await makeCatalog();
  let code = "";
  try {
    await search(db, { groupBy: { properties: ["shelf"], maxResult: 3 } as any });
  } catch (e: any) {
    code = e.code;
  }
  expect(code).toBe("INVALID_GROUP_BY_PROPERTY");
});

test("distinctOn keeps the first hit per distinct value while count stays total", async () => {
  /** Verifies: ORAMA-STR-015 */
  const db = await makeCatalog();
  const result = await search(db, { distinctOn: "series", sortBy: { property: "pages" } } as any);
  expect(ids(result)).toEqual(["g4", "g3"]);
  expect(result.count).toBe(5);
});

test("save returns a JSON-serializable snapshot", async () => {
  /** Verifies: ORAMA-PER-001 */
  const db = await makeCatalog();
  const snapshot = save(db);
  const rehydrated = JSON.parse(JSON.stringify(snapshot));
  expect(typeof rehydrated).toBe("object");
  expect(rehydrated).not.toBeNull();
});
