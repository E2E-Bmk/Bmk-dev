// Spec2Repo oracle - atomic tests (documents and shared types) for yjs-crdt-sync-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import * as Y from "yjs";

describe("documents", () => {
  test("clientID is numeric and differs between instances", () => {
    /** Verifies: YJS-DOC-002 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    expect(typeof a.clientID).toBe("number");
    expect(typeof b.clientID).toBe("number");
    expect(a.clientID).not.toBe(b.clientID);
  });

  test("guid option is honored and defaults to a string", () => {
    /** Verifies: YJS-DOC-001, YJS-DOC-003 */
    const fixed = new Y.Doc({ guid: "my-fixed-guid" });
    expect(fixed.guid).toBe("my-fixed-guid");
    const fresh = new Y.Doc();
    expect(typeof fresh.guid).toBe("string");
    expect(fresh.guid.length).toBeGreaterThan(0);
  });

  test("root accessors create on first access and cache the instance", () => {
    /** Verifies: YJS-DOC-004 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    const a = doc.getArray("a");
    const t = doc.getText("t");
    expect(doc.getMap("m")).toBe(m);
    expect(doc.getArray("a")).toBe(a);
    expect(doc.getText("t")).toBe(t);
  });

  test("re-declaring a root name with a different type throws", () => {
    /** Verifies: YJS-DOC-005, YJS-ERR-001 */
    const doc = new Y.Doc();
    doc.getMap("shared").set("k", 1);
    expect(() => doc.getArray("shared")).toThrow(Error);
    const doc2 = new Y.Doc();
    doc2.getText("t").insert(0, "x");
    expect(() => doc2.getMap("t")).toThrow(Error);
  });

  test("transact returns the callback's return value", () => {
    /** Verifies: YJS-DOC-006 */
    const doc = new Y.Doc();
    const out = doc.transact(() => {
      doc.getMap("m").set("k", 1);
      return "result-value";
    });
    expect(out).toBe("result-value");
  });

  test("a transaction batches mutations into one update event", () => {
    /** Verifies: YJS-DOC-006, YJS-DOC-010 */
    const doc = new Y.Doc();
    let count = 0;
    doc.on("update", () => {
      count += 1;
    });
    doc.transact(() => {
      doc.getMap("m").set("a", 1);
      doc.getMap("m").set("b", 2);
      doc.getArray("l").push([1, 2, 3]);
    });
    expect(count).toBe(1);
  });

  test("nested transact calls flatten into the outer transaction", () => {
    /** Verifies: YJS-DOC-008 */
    const doc = new Y.Doc();
    let count = 0;
    doc.on("update", () => {
      count += 1;
    });
    doc.transact(() => {
      doc.getMap("m").set("a", 1);
      doc.transact(() => {
        doc.getMap("m").set("b", 2);
      }, "inner-origin");
    });
    expect(count).toBe(1);
    expect(doc.getMap("m").get("b")).toBe(2);
  });

  test("a transaction without effective change emits no update event", () => {
    /** Verifies: YJS-DOC-009, YJS-DOC-010 */
    const doc = new Y.Doc();
    let count = 0;
    doc.on("update", () => {
      count += 1;
    });
    doc.getMap("m").set("k", 1);
    expect(count).toBe(1);
    doc.transact(() => {});
    expect(count).toBe(1);
  });

  test("destroy emits the destroy event and flags the doc", () => {
    /** Verifies: YJS-DOC-012 */
    const doc = new Y.Doc();
    doc.getMap("m").set("k", 1);
    let destroyed = false;
    doc.on("destroy", () => {
      destroyed = true;
    });
    doc.destroy();
    expect(destroyed).toBe(true);
    expect(doc.isDestroyed).toBe(true);
  });

  test("off unregisters and once fires a single time", () => {
    /** Verifies: YJS-DOC-013 */
    const doc = new Y.Doc();
    let onCount = 0;
    let onceCount = 0;
    const handler = () => {
      onCount += 1;
    };
    doc.on("update", handler);
    doc.once("update", () => {
      onceCount += 1;
    });
    doc.getMap("m").set("a", 1);
    doc.off("update", handler);
    doc.getMap("m").set("b", 2);
    expect(onCount).toBe(1);
    expect(onceCount).toBe(1);
  });
});

describe("shared maps", () => {
  test("set returns the value and get reads it back", () => {
    /** Verifies: YJS-MAP-001 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    expect(m.set("k", "stored")).toBe("stored");
    expect(m.get("k")).toBe("stored");
    expect(m.get("missing")).toBeUndefined();
  });

  test("has, delete, and size track current entries", () => {
    /** Verifies: YJS-MAP-002 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("a", 1);
    m.set("b", 2);
    expect(m.size).toBe(2);
    expect(m.has("a")).toBe(true);
    expect(m.has("zz")).toBe(false);
    m.delete("a");
    expect(m.has("a")).toBe(false);
    expect(m.size).toBe(1);
  });

  test("clear removes every entry", () => {
    /** Verifies: YJS-MAP-002 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("a", 1);
    m.set("b", 2);
    expect(m.size).toBe(2);
    m.clear();
    expect(m.size).toBe(0);
    expect(m.toJSON()).toEqual({});
  });

  test("null values are preserved and distinct from absence", () => {
    /** Verifies: YJS-MAP-003 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("n", null);
    expect(m.has("n")).toBe(true);
    expect(m.get("n")).toBeNull();
    expect(m.get("absent")).toBeUndefined();
    expect(m.has("absent")).toBe(false);
  });

  test("iterators visit every current entry exactly once", () => {
    /** Verifies: YJS-MAP-008 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("a", 1);
    m.set("b", 2);
    m.set("c", 3);
    m.delete("b");
    expect([...m.keys()].sort()).toEqual(["a", "c"]);
    expect([...m.values()].sort()).toEqual([1, 3]);
    const entries = [...m.entries()].sort((x, y) => x[0].localeCompare(y[0]));
    expect(entries).toEqual([
      ["a", 1],
      ["c", 3],
    ]);
    const pairs = [...m].sort((x, y) => x[0].localeCompare(y[0]));
    expect(pairs).toEqual([
      ["a", 1],
      ["c", 3],
    ]);
  });

  test("forEach passes value, key, and the map", () => {
    /** Verifies: YJS-MAP-008 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("x", 10);
    m.set("y", 20);
    const seen: Array<[string, unknown, boolean]> = [];
    m.forEach((value, key, target) => {
      seen.push([key, value, target === m]);
    });
    seen.sort((a, b) => a[0].localeCompare(b[0]));
    expect(seen).toEqual([
      ["x", 10, true],
      ["y", 20, true],
    ]);
  });

  test("toJSON converts nested shared types recursively", () => {
    /** Verifies: YJS-MAP-009 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    const inner = new Y.Map();
    m.set("inner", inner);
    const list = new Y.Array();
    inner.set("list", list);
    list.push(["x", "y"]);
    inner.set("flag", true);
    m.set("plain", 7);
    expect(m.toJSON()).toEqual({ inner: { list: ["x", "y"], flag: true }, plain: 7 });
  });

  test("clone returns an unintegrated copy with the same entries", () => {
    /** Verifies: YJS-MAP-010 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("a", 1);
    m.set("b", "two");
    const copy = m.clone();
    expect(copy.doc).toBeNull();
    doc.getMap("holder").set("copy", copy);
    expect(copy.toJSON()).toEqual({ a: 1, b: "two" });
    m.set("c", 3);
    expect(copy.has("c")).toBe(false);
  });

  test("the constructor seeds entries from an iterable", () => {
    /** Verifies: YJS-MAP-011 */
    const seeded = new Y.Map<number>([
      ["one", 1],
      ["two", 2],
    ]);
    const doc = new Y.Doc();
    doc.getMap("root").set("seeded", seeded);
    expect(seeded.toJSON()).toEqual({ one: 1, two: 2 });
  });

  test("pre-integration mutations become observable after insertion", () => {
    /** Verifies: YJS-MAP-012, YJS-MAP-013 */
    const doc = new Y.Doc();
    const root = doc.getMap("root");
    const child = new Y.Map();
    child.set("early", "yes");
    expect(child.doc).toBeNull();
    root.set("child", child);
    expect(root.get("child")).toBe(child);
    expect(child.get("early")).toBe("yes");
    expect(child.parent).toBe(root);
    expect(child.doc).toBe(doc);
    expect(root.parent).toBeNull();
  });

  test("inserting an integrated type at a second location throws", () => {
    /** Verifies: YJS-MAP-014, YJS-ERR-005 */
    const doc = new Y.Doc();
    const child = new Y.Map();
    doc.getMap("first").set("c", child);
    expect(() => doc.getMap("second").set("again", child)).toThrow();
  });

  test("storing a function throws", () => {
    /** Verifies: YJS-MAP-007, YJS-ERR-004 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    expect(() => m.set("fn", (() => 1) as never)).toThrow(Error);
  });

  test("plain objects and arrays replicate as plain deep-equal values", () => {
    /** Verifies: YJS-MAP-005 */
    const src = new Y.Doc();
    src.getMap("m").set("obj", { a: [1, 2], b: { c: true }, d: "str" });
    const dst = new Y.Doc();
    Y.applyUpdate(dst, Y.encodeStateAsUpdate(src));
    const round = dst.getMap("m").get("obj") as Record<string, unknown>;
    expect(round).toEqual({ a: [1, 2], b: { c: true }, d: "str" });
    expect(round.constructor).toBe(Object);
    expect(Array.isArray((round as { a: unknown }).a)).toBe(true);
  });

  test("Uint8Array values replicate with identical bytes", () => {
    /** Verifies: YJS-MAP-006 */
    const src = new Y.Doc();
    src.getMap("m").set("bin", new Uint8Array([7, 8, 9]));
    const dst = new Y.Doc();
    Y.applyUpdate(dst, Y.encodeStateAsUpdate(src));
    const bin = dst.getMap("m").get("bin") as Uint8Array;
    expect(bin).toBeInstanceOf(Uint8Array);
    expect([...bin]).toEqual([7, 8, 9]);
  });
});

describe("shared arrays", () => {
  test("insert, push, and unshift place items in order", () => {
    /** Verifies: YJS-ARR-001 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    expect(a.push([2, 3])).toBeUndefined();
    a.unshift([0]);
    a.insert(1, [1]);
    expect(a.toArray()).toEqual([0, 1, 2, 3]);
  });

  test("delete removes one item by default and a count when given", () => {
    /** Verifies: YJS-ARR-002 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push(["a", "b", "c", "d"]);
    a.delete(1);
    expect(a.toArray()).toEqual(["a", "c", "d"]);
    a.delete(0, 2);
    expect(a.toArray()).toEqual(["d"]);
  });

  test("get and length address current items", () => {
    /** Verifies: YJS-ARR-003 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push([10, 20, 30]);
    expect(a.length).toBe(3);
    expect(a.get(0)).toBe(10);
    expect(a.get(2)).toBe(30);
  });

  test("slice returns end-exclusive plain-array copies", () => {
    /** Verifies: YJS-ARR-003 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push(["a", "b", "c", "d"]);
    expect(a.slice(1, 3)).toEqual(["b", "c"]);
    expect(a.slice(2)).toEqual(["c", "d"]);
    expect(Array.isArray(a.slice(0, 1))).toBe(true);
  });

  test("insert past the end throws", () => {
    /** Verifies: YJS-ARR-004, YJS-ERR-002 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push([1, 2]);
    expect(() => a.insert(3, ["x"])).toThrow(Error);
  });

  test("delete past the end throws", () => {
    /** Verifies: YJS-ARR-004, YJS-ERR-003 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push([1, 2]);
    expect(() => a.delete(1, 5)).toThrow(Error);
  });

  test("toArray and toJSON convert content, toJSON recursing into shared types", () => {
    /** Verifies: YJS-ARR-005 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    const child = new Y.Map();
    a.push(["lead", child]);
    child.set("k", "v");
    expect(a.toArray()[0]).toBe("lead");
    expect(a.toArray()[1]).toBe(child);
    expect(a.toJSON()).toEqual(["lead", { k: "v" }]);
  });

  test("map, forEach, and iteration walk items in index order", () => {
    /** Verifies: YJS-ARR-006 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push([1, 2, 3]);
    expect(a.map((v, i) => (v as number) * 10 + i)).toEqual([10, 21, 32]);
    const seen: Array<[number, unknown, boolean]> = [];
    a.forEach((v, i, target) => {
      seen.push([i, v, target === a]);
    });
    expect(seen).toEqual([
      [0, 1, true],
      [1, 2, true],
      [2, 3, true],
    ]);
    expect([...a]).toEqual([1, 2, 3]);
  });

  test("Array.from seeds a standalone array", () => {
    /** Verifies: YJS-ARR-007 */
    const seeded = Y.Array.from(["x", "y", "z"]);
    const doc = new Y.Doc();
    doc.getMap("root").set("list", seeded);
    expect(seeded.toArray()).toEqual(["x", "y", "z"]);
  });

  test("nested standalone types integrate through array insertion", () => {
    /** Verifies: YJS-ARR-008 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    const item = new Y.Map();
    item.set("title", "card");
    a.push([item]);
    expect(item.doc).toBe(doc);
    expect(item.parent).toBe(a);
    expect(a.toJSON()).toEqual([{ title: "card" }]);
  });
});

describe("shared text", () => {
  test("insert places text at a character index", () => {
    /** Verifies: YJS-TXT-001 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "hd");
    t.insert(1, "ello worl");
    expect(t.toString()).toBe("hello world");
    expect(t.length).toBe(11);
  });

  test("insert beyond the current length appends at the end", () => {
    /** Verifies: YJS-TXT-001 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "ab");
    t.insert(99, "X");
    expect(t.toString()).toBe("abX");
  });

  test("delete removes a range and clamps past the end", () => {
    /** Verifies: YJS-TXT-002 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "abcdef");
    t.delete(1, 2);
    expect(t.toString()).toBe("adef");
    t.delete(2, 99);
    expect(t.toString()).toBe("ad");
  });

  test("format applies attributes visible in toDelta", () => {
    /** Verifies: YJS-TXT-003, YJS-TXT-007 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "hello world");
    t.format(0, 5, { bold: true });
    expect(t.toDelta()).toEqual([
      { insert: "hello", attributes: { bold: true } },
      { insert: " world" },
    ]);
    expect(t.toString()).toBe("hello world");
  });

  test("formatting with a null value removes the attribute", () => {
    /** Verifies: YJS-TXT-003 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "plain", { bold: true });
    t.format(0, 5, { bold: null });
    expect(t.toDelta()).toEqual([{ insert: "plain" }]);
  });

  test("insert accepts attributes for the inserted run", () => {
    /** Verifies: YJS-TXT-001, YJS-TXT-007 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "ab");
    t.insert(2, "!", { italic: true });
    expect(t.toDelta()).toEqual([
      { insert: "ab" },
      { insert: "!", attributes: { italic: true } },
    ]);
  });

  test("embeds occupy one length unit and are skipped by toString", () => {
    /** Verifies: YJS-TXT-004, YJS-TXT-005, YJS-TXT-006 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "ab");
    t.insertEmbed(1, { image: "pic.png" });
    expect(t.length).toBe(3);
    expect(t.toString()).toBe("ab");
    expect(t.toDelta()).toEqual([
      { insert: "a" },
      { insert: { image: "pic.png" } },
      { insert: "b" },
    ]);
  });

  test("toJSON returns the same string as toString", () => {
    /** Verifies: YJS-TXT-006 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "same text");
    expect(t.toJSON()).toBe("same text");
    expect(t.toJSON()).toBe(t.toString());
  });

  test("adjacent runs with identical formatting merge into one op", () => {
    /** Verifies: YJS-TXT-007 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "abc", { bold: true });
    t.insert(3, "def", { bold: true });
    expect(t.toDelta()).toEqual([{ insert: "abcdef", attributes: { bold: true } }]);
  });

  test("applyDelta inserts plain and formatted runs", () => {
    /** Verifies: YJS-TXT-008 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.applyDelta([{ insert: "abc" }, { insert: "def", attributes: { bold: true } }]);
    expect(t.toDelta()).toEqual([
      { insert: "abc" },
      { insert: "def", attributes: { bold: true } },
    ]);
  });

  test("applyDelta retain and delete edit existing content", () => {
    /** Verifies: YJS-TXT-008, YJS-TXT-009 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "abcdef");
    t.applyDelta([{ retain: 3 }, { delete: 2 }, { insert: "X" }]);
    expect(t.toString()).toBe("abcXf");
    expect(t.length).toBe(5);
    expect(t.toDelta()).toEqual([{ insert: "abcXf" }]);
  });

  test("applyDelta retain with attributes formats the retained range", () => {
    /** Verifies: YJS-TXT-008 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "abcdef");
    t.applyDelta([{ retain: 3, attributes: { bold: true } }]);
    expect(t.toDelta()).toEqual([
      { insert: "abc", attributes: { bold: true } },
      { insert: "def" },
    ]);
  });

  test("a seeded standalone text materializes on integration", () => {
    /** Verifies: YJS-TXT-010 */
    const seeded = new Y.Text("seed content");
    const doc = new Y.Doc();
    doc.getMap("root").set("t", seeded);
    expect((doc.getMap("root").get("t") as Y.Text).toString()).toBe("seed content");
  });
});
