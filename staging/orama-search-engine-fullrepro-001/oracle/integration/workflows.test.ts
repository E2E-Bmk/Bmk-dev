// Spec2Repo oracle - integration tests for orama-search-engine-fullrepro-001
import { expect, test } from "vitest";
import {
  create,
  insert,
  insertMultiple,
  update,
  upsert,
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

function freshDocs() {
  return guideDocs.map((d) => ({ ...d, topics: [...d.topics], extra: { ...d.extra } }));
}

async function makeCatalog() {
  const db = create({ schema: guideSchema as any });
  await insertMultiple(db, freshDocs());
  return db;
}

function ids(result: any): string[] {
  return result.hits.map((h: any) => h.id);
}

test("an inserted document is visible across count getByID search facets and groups", async () => {
  /** Seam: state consistency. Verifies: ORAMA-CVI-001 */
  const db = await makeCatalog();
  await insert(db, { id: "g6", title: "Granite Bays Almanac", body: "shorelines of granite bays", series: "summit", pages: 200, digital: true, shelf: "geology", topics: ["rocks"], extra: { weight: 2 } });
  expect(await count(db)).toBe(6);
  expect((await getByID(db, "g6") as any).title).toBe("Granite Bays Almanac");
  expect(ids(await search(db, { term: "granite" })).sort()).toEqual(["g1", "g6"]);
  const faceted = await search(db, { facets: { shelf: {} } as any });
  expect(faceted.facets!.shelf.values).toEqual({ geology: 3, wildlife: 2, botany: 1 });
  const grouped = await search(db, { groupBy: { properties: ["series"], maxResult: 10 } as any });
  const summit = (grouped.groups as any[]).find((g) => g.values[0] === "summit");
  expect(summit.result.map((h: any) => h.id).sort()).toEqual(["g4", "g5", "g6"]);
});

test("a removed document disappears from every projection simultaneously", async () => {
  /** Seam: state consistency. Verifies: ORAMA-CVI-002 */
  const db = await makeCatalog();
  await remove(db, "g3");
  expect(await count(db)).toBe(4);
  expect(await getByID(db, "g3")).toBeUndefined();
  expect(ids(await search(db, { term: "otter" }))).toEqual(["g5"]);
  const faceted = await search(db, { facets: { shelf: {} } as any });
  expect(faceted.facets!.shelf.values).toEqual({ geology: 2, wildlife: 1, botany: 1 });
  const grouped = await search(db, { groupBy: { properties: ["series"], maxResult: 10 } as any });
  const trail = (grouped.groups as any[]).find((g) => g.values[0] === "trail");
  expect(trail.result.map((h: any) => h.id).sort()).toEqual(["g1", "g2"]);
});

test("count stays the unsliced total across limit offset preflight and distinct", async () => {
  /** Seam: state consistency. Verifies: ORAMA-CVI-003 */
  const db = await makeCatalog();
  const full = await search(db, {} as any);
  expect(full.count).toBe(5);
  expect(ids(full).length).toBe(5);
  const sliced = await search(db, { limit: 2, offset: 2 } as any);
  expect(sliced.count).toBe(5);
  expect(sliced.hits.length).toBe(2);
  const preflight = await search(db, { preflight: true } as any);
  expect(preflight.count).toBe(5);
  expect(preflight.hits).toEqual([]);
  const distinct = await search(db, { distinctOn: "series", sortBy: { property: "pages" } } as any);
  expect(distinct.count).toBe(5);
  expect(distinct.hits.length).toBe(2);
});

test("hit documents deep-equal getByID lookups", async () => {
  /** Seam: state consistency. Verifies: ORAMA-CVI-004 */
  const db = await makeCatalog();
  const result = await search(db, { term: "otter" });
  expect(result.hits.length).toBeGreaterThan(0);
  for (const hit of result.hits) {
    expect(hit.document).toEqual(await getByID(db, hit.id as string));
  }
});

test("facet bucket totals equal the matched documents carrying the property", async () => {
  /** Seam: state consistency. Verifies: ORAMA-CVI-005 */
  const db = await makeCatalog();
  const result = await search(db, { term: "otter", facets: { shelf: {}, digital: {} } as any });
  expect(result.count).toBe(2);
  const shelfTotal = Object.values(result.facets!.shelf.values as Record<string, number>).reduce((a, b) => a + b, 0);
  expect(shelfTotal).toBe(2);
  expect(result.facets!.digital.values).toEqual({ true: 1, false: 1 });
});

test("update redirects full-text matching filters and facets to the new content", async () => {
  /** Seam: state consistency. Verifies: ORAMA-CVI-006 */
  const db = await makeCatalog();
  await update(db, "g4", { id: "g4", title: "Alpine Ferns Primer", body: "ferns of shaded alpine gullies", series: "summit", pages: 300, digital: false, shelf: "botany", topics: ["plants"], extra: { weight: 3 } });
  expect((await search(db, { term: "mosses" })).count).toBe(0);
  expect(ids(await search(db, { term: "ferns" }))).toEqual(["g4"]);
  expect(ids(await search(db, { where: { pages: { gte: 260 } } })).sort()).toEqual(["g2", "g4"]);
  const faceted = await search(db, { facets: { digital: {} } as any });
  expect(faceted.facets!.digital.values).toEqual({ true: 2, false: 3 });
});

test("save and load preserve count lookups and ranked order", async () => {
  /** Seam: lifecycle crossing. Verifies: ORAMA-CVI-007, ORAMA-PER-002 */
  const source = await makeCatalog();
  const rankedBefore = ids(await search(source, { term: "otter" }));
  const snapshot = save(source);
  const restored = create({ schema: guideSchema as any });
  load(restored, snapshot);
  expect(await count(restored)).toBe(5);
  expect(await getByID(restored, "g2")).toEqual(await getByID(source, "g2"));
  expect(ids(await search(restored, { term: "otter" }))).toEqual(rankedBefore);
  expect(ids(await search(restored, { where: { shelf: { eq: "wildlife" } } })).sort()).toEqual(["g3", "g5"]);
});

test("documents inserted after load join restored ones in results", async () => {
  /** Seam: lifecycle crossing. Verifies: ORAMA-CVI-007, ORAMA-PER-002 */
  const source = await makeCatalog();
  const restored = create({ schema: guideSchema as any });
  load(restored, save(source));
  await insert(restored, { id: "g7", title: "Otter Dens Survey", body: "dens along quiet banks", series: "trail", pages: 110, digital: true, shelf: "wildlife", topics: ["mammals"], extra: { weight: 2 } });
  expect(await count(restored)).toBe(6);
  expect(ids(await search(restored, { term: "otter" })).sort()).toEqual(["g3", "g5", "g7"]);
  const faceted = await search(restored, { facets: { shelf: {} } as any });
  expect(faceted.facets!.shelf.values).toEqual({ geology: 2, wildlife: 3, botany: 1 });
});

test("groupBy places every matched document in exactly one group", async () => {
  /** Seam: state consistency. Verifies: ORAMA-CVI-008 */
  const db = await makeCatalog();
  const result = await search(db, { groupBy: { properties: ["series", "digital"], maxResult: 10 } as any });
  const seen: string[] = [];
  for (const group of result.groups as any[]) {
    for (const hit of group.result) {
      seen.push(hit.id);
    }
  }
  expect(seen.sort()).toEqual(["g1", "g2", "g3", "g4", "g5"]);
  const combos = (result.groups as any[]).map((g) => g.values.join("|")).sort();
  expect(combos).toEqual(["summit|false", "summit|true", "trail|false", "trail|true"]);
});

test("term and where filters combine conjunctively", async () => {
  /** Seam: config interaction. Verifies: ORAMA-STR-006 */
  const db = await makeCatalog();
  const result = await search(db, { term: "otter", where: { digital: true } });
  expect(ids(result)).toEqual(["g3"]);
  expect(result.count).toBe(1);
});

test("multiple where clauses form a conjunction", async () => {
  /** Seam: config interaction. Verifies: ORAMA-STR-006 */
  const db = await makeCatalog();
  const result = await search(db, { where: { digital: true, pages: { gte: 90 } } });
  expect(ids(result).sort()).toEqual(["g1", "g3"]);
});

test("facets aggregate only over filtered matches", async () => {
  /** Seam: config interaction. Verifies: ORAMA-CVI-005, ORAMA-STR-008 */
  const db = await makeCatalog();
  const result = await search(db, { where: { shelf: { eq: "wildlife" } }, facets: { digital: {} } as any });
  expect(result.facets!.digital.values).toEqual({ true: 1, false: 1 });
});

test("boost reorders title and body matches without changing the match set", async () => {
  /** Seam: config interaction. Verifies: ORAMA-FTS-011 */
  const db = create({ schema: { title: "string", body: "string" } as any });
  await insertMultiple(db, [
    { id: "t1", title: "lantern making", body: "wax and wicks" },
    { id: "t2", title: "workshop crafts", body: "a lantern for every porch and garden path" },
  ]);
  const titleBoosted = await search(db, { term: "lantern", boost: { title: 10 } });
  expect(ids(titleBoosted)).toEqual(["t1", "t2"]);
  const bodyBoosted = await search(db, { term: "lantern", boost: { body: 10 } });
  expect(ids(bodyBoosted)).toEqual(["t2", "t1"]);
  expect(ids(titleBoosted).sort()).toEqual(ids(bodyBoosted).sort());
});

test("threshold composes with filters", async () => {
  /** Seam: config interaction. Verifies: ORAMA-FTS-010, ORAMA-STR-006 */
  const db = await makeCatalog();
  const anyToken = await search(db, { term: "otter tracking", where: { shelf: { eq: "wildlife" } } });
  expect(ids(anyToken).sort()).toEqual(["g3", "g5"]);
  const allTokens = await search(db, { term: "otter tracking", threshold: 0, where: { shelf: { eq: "wildlife" } } });
  expect(ids(allTokens)).toEqual(["g5"]);
});

test("sortBy with distinctOn keeps the first sorted hit per distinct value", async () => {
  /** Seam: config interaction. Verifies: ORAMA-STR-011, ORAMA-STR-015 */
  const db = await makeCatalog();
  const ascending = await search(db, { distinctOn: "series", sortBy: { property: "pages" } } as any);
  expect(ids(ascending)).toEqual(["g4", "g3"]);
  const descending = await search(db, { distinctOn: "series", sortBy: { property: "pages", order: "DESC" } } as any);
  expect(ids(descending)).toEqual(["g2", "g5"]);
});

test("offset windows partition the sorted hit sequence", async () => {
  /** Seam: protocol handoff. Verifies: ORAMA-FTS-012, ORAMA-STR-011 */
  const db = await makeCatalog();
  const first = await search(db, { sortBy: { property: "pages" }, limit: 2, offset: 0 } as any);
  const second = await search(db, { sortBy: { property: "pages" }, limit: 2, offset: 2 } as any);
  const third = await search(db, { sortBy: { property: "pages" }, limit: 2, offset: 4 } as any);
  expect([...ids(first), ...ids(second), ...ids(third)]).toEqual(["g4", "g3", "g1", "g5", "g2"]);
});

test("insertMultiple and repeated insert produce equivalent projections", async () => {
  /** Seam: protocol handoff. Verifies: ORAMA-DOC-001, ORAMA-DOC-002 */
  const batch = create({ schema: guideSchema as any });
  await insertMultiple(batch, freshDocs());
  const oneByOne = create({ schema: guideSchema as any });
  for (const doc of freshDocs()) {
    await insert(oneByOne, doc);
  }
  expect(await count(oneByOne)).toBe(await count(batch));
  expect(ids(await search(oneByOne, { term: "otter" }))).toEqual(ids(await search(batch, { term: "otter" })));
  const facetsA = await search(batch, { facets: { shelf: {} } as any });
  const facetsB = await search(oneByOne, { facets: { shelf: {} } as any });
  expect(facetsB.facets!.shelf.values).toEqual(facetsA.facets!.shelf.values);
});

test("a failed search leaves the instance usable", async () => {
  /** Seam: error propagation. Verifies: ORAMA-STR-007, ORAMA-ERR-005 */
  const db = await makeCatalog();
  let code = "";
  try {
    await search(db, { where: { phantom: { eq: 3 } } as any });
  } catch (e: any) {
    code = e.code;
  }
  expect(code).toBe("UNKNOWN_FILTER_PROPERTY");
  expect((await search(db, { term: "granite" })).count).toBe(1);
  expect(await count(db)).toBe(5);
});

test("a rejected insert leaves all projections unchanged", async () => {
  /** Seam: error propagation. Verifies: ORAMA-DOC-004, ORAMA-ERR-002 */
  const db = await makeCatalog();
  let code = "";
  try {
    await insert(db, { id: "bad1", title: "Broken Entry", body: "text", series: "trail", pages: "many", digital: true, shelf: "geology", topics: [], extra: { weight: 1 } } as any);
  } catch (e: any) {
    code = e.code;
  }
  expect(code).toBe("SCHEMA_VALIDATION_FAILURE");
  expect(await count(db)).toBe(5);
  expect(await getByID(db, "bad1")).toBeUndefined();
  expect((await search(db, { term: "broken" })).count).toBe(0);
});

test("upsert replacement makes stale content unmatchable", async () => {
  /** Seam: state consistency. Verifies: ORAMA-DOC-012, ORAMA-CVI-006 */
  const db = await makeCatalog();
  await upsert(db, { id: "g1", title: "Slate Ridges Field Guide", body: "survey of slate ridge formations", series: "trail", pages: 120, digital: true, shelf: "geology", topics: ["rocks"], extra: { weight: 2 } });
  expect((await search(db, { term: "granite" })).count).toBe(0);
  expect(ids(await search(db, { term: "slate" }))).toEqual(["g1"]);
  expect(await count(db)).toBe(5);
});

test("removeMultiple recomputes facets and groups", async () => {
  /** Seam: state consistency. Verifies: ORAMA-DOC-009, ORAMA-CVI-002 */
  const db = await makeCatalog();
  await removeMultiple(db, ["g3", "g5"]);
  const faceted = await search(db, { facets: { shelf: {}, topics: {} } as any });
  expect(faceted.facets!.shelf.values).toEqual({ geology: 2, botany: 1 });
  expect(faceted.facets!.topics.values).toEqual({ rocks: 1, maps: 1, soil: 1, plants: 1 });
  const grouped = await search(db, { groupBy: { properties: ["series"], maxResult: 10 } as any });
  const bySeries = Object.fromEntries((grouped.groups as any[]).map((g) => [g.values[0], g.result.map((h: any) => h.id).sort()]));
  expect(bySeries).toEqual({ trail: ["g1", "g2"], summit: ["g4"] });
});

test("nested dot path agrees across where facets and sortBy", async () => {
  /** Seam: config interaction. Verifies: ORAMA-CRE-002, ORAMA-STR-001, ORAMA-STR-009, ORAMA-STR-011 */
  const db = await makeCatalog();
  const filtered = await search(db, { where: { "extra.weight": { between: [2, 4] } } });
  expect(ids(filtered).sort()).toEqual(["g1", "g4", "g5"]);
  const faceted = await search(db, { facets: { "extra.weight": { ranges: [{ from: 1, to: 2 }, { from: 3, to: 5 }] } } as any });
  expect(faceted.facets!["extra.weight"].values).toEqual({ "1-2": 2, "3-5": 3 });
  const sorted = await search(db, { sortBy: { property: "extra.weight" } } as any);
  expect(ids(sorted)).toEqual(["g3", "g1", "g4", "g5", "g2"]);
});

test("a loaded instance accepts update and remove like a native one", async () => {
  /** Seam: lifecycle crossing. Verifies: ORAMA-PER-002, ORAMA-DOC-010 */
  const source = await makeCatalog();
  const restored = create({ schema: guideSchema as any });
  load(restored, save(source));
  await update(restored, "g4", { id: "g4", title: "Alpine Sedges Primer", body: "sedges of wet alpine soil", series: "summit", pages: 55, digital: true, shelf: "botany", topics: ["plants"], extra: { weight: 3 } });
  expect(ids(await search(restored, { term: "sedges" }))).toEqual(["g4"]);
  expect(await remove(restored, "g2")).toBe(true);
  expect(await count(restored)).toBe(4);
  expect((await search(restored, { term: "granular" })).count).toBe(0);
});

test("distinct results survive a save load round trip", async () => {
  /** Seam: lifecycle crossing. Verifies: ORAMA-CVI-007, ORAMA-STR-015 */
  const source = await makeCatalog();
  const before = await search(source, { distinctOn: "series", sortBy: { property: "pages" } } as any);
  const restored = create({ schema: guideSchema as any });
  load(restored, save(source));
  const after = await search(restored, { distinctOn: "series", sortBy: { property: "pages" } } as any);
  expect(ids(after)).toEqual(ids(before));
  expect(after.count).toBe(before.count);
});

test("multi-token queries rank documents matching more tokens first", async () => {
  /** Seam: protocol handoff. Verifies: ORAMA-FTS-002, ORAMA-FTS-010 */
  const db = await makeCatalog();
  const result = await search(db, { term: "otter tracking" });
  expect(ids(result).sort()).toEqual(["g3", "g5"]);
  expect(result.hits[0].id).toBe("g5");
  expect(result.hits[0].score).toBeGreaterThan(result.hits[1].score);
});

test("exact and threshold compose on the same query", async () => {
  /** Seam: config interaction. Verifies: ORAMA-FTS-008, ORAMA-FTS-010 */
  const db = await makeCatalog();
  const whole = await search(db, { term: "granite formations", exact: true, threshold: 0 });
  expect(ids(whole)).toEqual(["g1"]);
  const prefixOnly = await search(db, { term: "granite formation", exact: true, threshold: 0 });
  expect(prefixOnly.count).toBe(0);
});
