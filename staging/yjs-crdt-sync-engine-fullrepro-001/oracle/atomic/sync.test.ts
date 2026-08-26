// Spec2Repo oracle - atomic tests (updates, events, undo, snapshots, positions) for yjs-crdt-sync-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import * as Y from "yjs";

describe("update exchange", () => {
  test("a full update replays the document on a fresh replica", () => {
    /** Verifies: YJS-UPD-001, YJS-UPD-002 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "payload");
    src.getMap("m").set("k", 42);
    const update = Y.encodeStateAsUpdate(src);
    expect(update).toBeInstanceOf(Uint8Array);
    const dst = new Y.Doc();
    Y.applyUpdate(dst, update);
    expect(dst.getText("t").toString()).toBe("payload");
    expect(dst.getMap("m").get("k")).toBe(42);
  });

  test("encoding against a state vector yields only the missing changes", () => {
    /** Verifies: YJS-UPD-001, YJS-UPD-003 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "first");
    const dst = new Y.Doc();
    Y.applyUpdate(dst, Y.encodeStateAsUpdate(src));
    src.getText("t").insert(5, " second");
    const diff = Y.encodeStateAsUpdate(src, Y.encodeStateVector(dst));
    const full = Y.encodeStateAsUpdate(src);
    expect(diff.length).toBeLessThan(full.length);
    Y.applyUpdate(dst, diff);
    expect(dst.getText("t").toString()).toBe("first second");
  });

  test("encodeStateVector returns a binary version descriptor", () => {
    /** Verifies: YJS-UPD-003 */
    const doc = new Y.Doc();
    doc.getMap("m").set("a", 1);
    const sv = Y.encodeStateVector(doc);
    expect(sv).toBeInstanceOf(Uint8Array);
    expect(sv.length).toBeGreaterThan(0);
  });

  test("applying the same update twice has no second effect", () => {
    /** Verifies: YJS-UPD-005 */
    const src = new Y.Doc();
    src.getArray("a").push([1, 2, 3]);
    const update = Y.encodeStateAsUpdate(src);
    const dst = new Y.Doc();
    Y.applyUpdate(dst, update);
    Y.applyUpdate(dst, update);
    expect(dst.getArray("a").toArray()).toEqual([1, 2, 3]);
    expect(dst.getArray("a").length).toBe(3);
  });

  test("a malformed update payload throws", () => {
    /** Verifies: YJS-UPD-004, YJS-ERR-006 */
    const doc = new Y.Doc();
    expect(() => Y.applyUpdate(doc, new Uint8Array([1, 2, 3, 4]))).toThrow(Error);
  });

  test("mergeUpdates combines payloads into one equivalent update", () => {
    /** Verifies: YJS-UPD-008 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "one ");
    const u1 = Y.encodeStateAsUpdate(src);
    const sv1 = Y.encodeStateVector(src);
    src.getText("t").insert(4, "two");
    const u2 = Y.encodeStateAsUpdate(src, sv1);
    const merged = Y.mergeUpdates([u1, u2]);
    expect(merged).toBeInstanceOf(Uint8Array);
    const dst = new Y.Doc();
    Y.applyUpdate(dst, merged);
    expect(dst.getText("t").toString()).toBe("one two");
  });

  test("encodeStateVectorFromUpdate matches the source document's state vector", () => {
    /** Verifies: YJS-UPD-009 */
    const src = new Y.Doc();
    src.getMap("m").set("a", 1);
    src.getText("t").insert(0, "abc");
    const update = Y.encodeStateAsUpdate(src);
    const svFromUpdate = Y.encodeStateVectorFromUpdate(update);
    const svFromDoc = Y.encodeStateVector(src);
    expect(svFromUpdate.length).toBeGreaterThan(0);
    expect([...svFromUpdate]).toEqual([...svFromDoc]);
  });

  test("diffUpdate extracts the changes a state vector is missing", () => {
    /** Verifies: YJS-UPD-010 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "alpha");
    const u1 = Y.encodeStateAsUpdate(src);
    src.getText("t").insert(5, " beta");
    const full = Y.encodeStateAsUpdate(src);
    const diff = Y.diffUpdate(full, Y.encodeStateVectorFromUpdate(u1));
    const dst = new Y.Doc();
    Y.applyUpdate(dst, u1);
    Y.applyUpdate(dst, diff);
    expect(dst.getText("t").toString()).toBe("alpha beta");
  });

  test("the v2 encoding replays identically", () => {
    /** Verifies: YJS-UPD-011 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "v2 payload");
    src.getMap("m").set("n", 5);
    const updateV2 = Y.encodeStateAsUpdateV2(src);
    expect(updateV2).toBeInstanceOf(Uint8Array);
    const dst = new Y.Doc();
    Y.applyUpdateV2(dst, updateV2);
    expect(dst.getText("t").toString()).toBe("v2 payload");
    expect(dst.getMap("m").get("n")).toBe(5);
  });

  test("format conversions preserve replay in both directions", () => {
    /** Verifies: YJS-UPD-012 */
    const src = new Y.Doc();
    src.getArray("a").push(["x", "y"]);
    const v1 = Y.encodeStateAsUpdate(src);
    const v2 = Y.convertUpdateFormatV1ToV2(v1);
    const dstA = new Y.Doc();
    Y.applyUpdateV2(dstA, v2);
    expect(dstA.getArray("a").toArray()).toEqual(["x", "y"]);
    const v1Back = Y.convertUpdateFormatV2ToV1(v2);
    const dstB = new Y.Doc();
    Y.applyUpdate(dstB, v1Back);
    expect(dstB.getArray("a").toArray()).toEqual(["x", "y"]);
  });
});

describe("events and observation", () => {
  test("observe fires once per transaction with the event and transaction", () => {
    /** Verifies: YJS-EVT-001 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    let calls = 0;
    let sawTarget = false;
    let sawTxn = false;
    m.observe((event, txn) => {
      calls += 1;
      sawTarget = event.target === m;
      sawTxn = txn !== undefined && txn !== null;
    });
    doc.transact(() => {
      m.set("a", 1);
      m.set("b", 2);
    });
    expect(calls).toBe(1);
    expect(sawTarget).toBe(true);
    expect(sawTxn).toBe(true);
  });

  test("unobserve stops event delivery", () => {
    /** Verifies: YJS-EVT-001 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    let calls = 0;
    const handler = () => {
      calls += 1;
    };
    m.observe(handler);
    m.set("a", 1);
    m.unobserve(handler);
    m.set("b", 2);
    expect(calls).toBe(1);
  });

  test("map events report add, update, and delete actions with old values", () => {
    /** Verifies: YJS-EVT-005 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("upd", "before");
    m.set("del", "gone");
    const log: Array<[string, string, unknown]> = [];
    m.observe((event) => {
      for (const [key, change] of event.changes.keys.entries()) {
        log.push([key, change.action, change.oldValue]);
      }
    });
    doc.transact(() => {
      m.set("new", 1);
      m.set("upd", "after");
      m.delete("del");
    });
    log.sort((a, b) => a[0].localeCompare(b[0]));
    expect(log).toEqual([
      ["del", "delete", "gone"],
      ["new", "add", undefined],
      ["upd", "update", "before"],
    ]);
  });

  test("key records describe the net transaction effect from its start state", () => {
    /** Verifies: YJS-EVT-006 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("keep", 0);
    let log: Array<[string, string, unknown]> = [];
    m.observe((event) => {
      log = [...event.changes.keys.entries()].map(([k, c]) => [k, c.action, c.oldValue]);
    });
    doc.transact(() => {
      m.set("keep", 99);
      m.delete("keep");
    });
    expect(log).toEqual([["keep", "delete", 0]]);
  });

  test("keysChanged names the affected keys", () => {
    /** Verifies: YJS-EVT-007 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    let changed: string[] = [];
    m.observe((event) => {
      changed = [...event.keysChanged].sort();
    });
    doc.transact(() => {
      m.set("x", 1);
      m.set("y", 2);
    });
    expect(changed).toEqual(["x", "y"]);
  });

  test("array events expose a retain/insert/delete delta", () => {
    /** Verifies: YJS-EVT-008, YJS-EVT-009 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push([1, 2, 3]);
    let delta: unknown = null;
    a.observe((event) => {
      delta = event.delta;
    });
    doc.transact(() => {
      a.delete(0, 1);
      a.insert(1, ["x"]);
    });
    expect(delta).toEqual([{ delete: 1 }, { retain: 1 }, { insert: ["x"] }]);
  });

  test("text events carry string inserts with attributes", () => {
    /** Verifies: YJS-EVT-008, YJS-EVT-009 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "base");
    let delta: unknown = null;
    t.observe((event) => {
      delta = event.delta;
    });
    t.insert(2, "XY", { bold: true });
    expect(delta).toEqual([{ retain: 2 }, { insert: "XY", attributes: { bold: true } }]);
  });

  test("reading changes or delta after the handler returns throws", () => {
    /** Verifies: YJS-EVT-004, YJS-ERR-007 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    let captured: { changes: unknown; delta: unknown } | null = null;
    a.observe((event) => {
      captured = event;
    });
    a.push([1]);
    expect(captured).not.toBeNull();
    expect(() => captured!.changes).toThrow(Error);
    expect(() => captured!.delta).toThrow(Error);
  });

  test("a directly observed type reports itself with an empty path", () => {
    /** Verifies: YJS-EVT-003 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    let target: unknown = null;
    let path: unknown = null;
    m.observe((event) => {
      target = event.target;
      path = event.path;
    });
    m.set("k", 1);
    expect(target).toBe(m);
    expect(path).toEqual([]);
  });

  test("transactions report origin and local for local edits", () => {
    /** Verifies: YJS-EVT-010, YJS-DOC-007 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const log: Array<[unknown, boolean]> = [];
    t.observe((_event, txn) => {
      log.push([txn.origin, txn.local]);
    });
    t.insert(0, "a");
    doc.transact(() => t.insert(0, "b"), "tagged");
    expect(log).toEqual([
      [null, true],
      ["tagged", true],
    ]);
  });
});

describe("undo and redo", () => {
  test("canUndo and canRedo reflect stack availability", () => {
    /** Verifies: YJS-UNDO-006 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t);
    expect(um.canUndo()).toBe(false);
    expect(um.canRedo()).toBe(false);
    t.insert(0, "x");
    expect(um.canUndo()).toBe(true);
    um.undo();
    expect(um.canRedo()).toBe(true);
  });

  test("undo reverts and redo restores content", () => {
    /** Verifies: YJS-UNDO-005 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t);
    t.insert(0, "hello");
    um.undo();
    expect(t.toString()).toBe("");
    um.redo();
    expect(t.toString()).toBe("hello");
  });

  test("clear empties both stacks", () => {
    /** Verifies: YJS-UNDO-006 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t, { captureTimeout: 0 });
    t.insert(0, "a");
    t.insert(1, "b");
    um.undo();
    um.clear();
    expect(um.canUndo()).toBe(false);
    expect(um.canRedo()).toBe(false);
    expect(t.toString()).toBe("a");
  });

  test("captureTimeout zero keeps each transaction as its own entry", () => {
    /** Verifies: YJS-UNDO-003 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t, { captureTimeout: 0 });
    t.insert(0, "a");
    t.insert(1, "b");
    um.undo();
    expect(t.toString()).toBe("a");
    um.undo();
    expect(t.toString()).toBe("");
  });

  test("rapid edits merge into a single entry by default", () => {
    /** Verifies: YJS-UNDO-003 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t);
    t.insert(0, "a");
    t.insert(1, "b");
    expect(t.toString()).toBe("ab");
    um.undo();
    expect(t.toString()).toBe("");
  });

  test("stopCapturing starts a fresh entry", () => {
    /** Verifies: YJS-UNDO-004 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t);
    t.insert(0, "a");
    um.stopCapturing();
    t.insert(1, "b");
    um.undo();
    expect(t.toString()).toBe("a");
  });

  test("trackedOrigins limits tracking to the listed origins", () => {
    /** Verifies: YJS-UNDO-001, YJS-UNDO-002 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t, { trackedOrigins: new Set(["ui"]) });
    doc.transact(() => t.insert(0, "tracked"), "ui");
    doc.transact(() => t.insert(0, "un-"), "system");
    expect(um.canUndo()).toBe(true);
    um.undo();
    expect(t.toString()).toBe("un-");
  });

  test("by default only untagged transactions are tracked", () => {
    /** Verifies: YJS-UNDO-002 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t);
    doc.transact(() => t.insert(0, "tagged"), "some-origin");
    expect(um.canUndo()).toBe(false);
    t.insert(6, "-plain");
    expect(um.canUndo()).toBe(true);
    um.undo();
    expect(t.toString()).toBe("tagged");
  });

  test("a new tracked edit clears the redo stack", () => {
    /** Verifies: YJS-UNDO-007 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    const um = new Y.UndoManager(t, { captureTimeout: 0 });
    t.insert(0, "a");
    um.undo();
    expect(um.canRedo()).toBe(true);
    t.insert(0, "z");
    expect(um.canRedo()).toBe(false);
  });

  test("undoing map changes restores previous values", () => {
    /** Verifies: YJS-UNDO-008 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("k", "v1");
    const um = new Y.UndoManager(m, { captureTimeout: 0 });
    m.set("k", "v2");
    m.set("k", "v3");
    um.undo();
    expect(m.get("k")).toBe("v2");
    um.undo();
    expect(m.get("k")).toBe("v1");
    um.redo();
    expect(m.get("k")).toBe("v2");
  });

  test("multi-scope managers revert entries across their types", () => {
    /** Verifies: YJS-UNDO-001 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    const a = doc.getArray("a");
    const um = new Y.UndoManager([m, a], { captureTimeout: 0 });
    m.set("k", 1);
    a.push(["v"]);
    um.undo();
    expect(a.toArray()).toEqual([]);
    expect(m.toJSON()).toEqual({ k: 1 });
    um.undo();
    expect(m.toJSON()).toEqual({});
  });
});

describe("snapshots", () => {
  test("snapshots encode, decode, and compare by version", () => {
    /** Verifies: YJS-SNAP-001, YJS-SNAP-002, YJS-SNAP-003 */
    const doc = new Y.Doc({ gc: false });
    doc.getText("t").insert(0, "version one");
    const s1 = Y.snapshot(doc);
    const decoded = Y.decodeSnapshot(Y.encodeSnapshot(s1));
    expect(Y.equalSnapshots(s1, decoded)).toBe(true);
    doc.getText("t").insert(0, "MORE ");
    const s2 = Y.snapshot(doc);
    expect(Y.equalSnapshots(s1, s2)).toBe(false);
  });

  test("createDocFromSnapshot restores the captured content", () => {
    /** Verifies: YJS-SNAP-004 */
    const doc = new Y.Doc({ gc: false });
    const t = doc.getText("t");
    t.insert(0, "first draft");
    const snap = Y.snapshot(doc);
    t.insert(0, "EDITED ");
    const restored = Y.createDocFromSnapshot(doc, snap);
    expect(restored.getText("t").toString()).toBe("first draft");
    expect(t.toString()).toBe("EDITED first draft");
  });

  test("restoring from a gc-enabled document throws", () => {
    /** Verifies: YJS-SNAP-005, YJS-ERR-008 */
    const doc = new Y.Doc();
    doc.getText("t").insert(0, "x");
    const snap = Y.snapshot(doc);
    expect(() => Y.createDocFromSnapshot(doc, snap)).toThrow(Error);
  });

  test("snapshotContainsUpdate distinguishes covered from uncovered updates", () => {
    /** Verifies: YJS-SNAP-006 */
    const doc = new Y.Doc({ gc: false });
    doc.getText("t").insert(0, "early");
    const before = Y.snapshot(doc);
    doc.getText("t").insert(5, " late");
    const after = Y.snapshot(doc);
    const fullUpdate = Y.encodeStateAsUpdate(doc);
    expect(Y.snapshotContainsUpdate(after, fullUpdate)).toBe(true);
    expect(Y.snapshotContainsUpdate(before, fullUpdate)).toBe(false);
  });
});

describe("relative positions", () => {
  test("a position resolves to its index and anchored type", () => {
    /** Verifies: YJS-POS-001, YJS-POS-002 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "hello world");
    const rel = Y.createRelativePositionFromTypeIndex(t, 6);
    const abs = Y.createAbsolutePositionFromRelativePosition(rel, doc);
    expect(abs).not.toBeNull();
    expect(abs!.index).toBe(6);
    expect(abs!.type).toBe(t);
  });

  test("left-associated positions resolve at the same static index", () => {
    /** Verifies: YJS-POS-001 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "static");
    const rel = Y.createRelativePositionFromTypeIndex(t, 3, -1);
    const abs = Y.createAbsolutePositionFromRelativePosition(rel, doc);
    expect(abs).not.toBeNull();
    expect(abs!.index).toBe(3);
  });

  test("JSON round trips compare equal", () => {
    /** Verifies: YJS-POS-005 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "hello");
    const rel = Y.createRelativePositionFromTypeIndex(t, 2);
    const json = Y.relativePositionToJSON(rel);
    const back = Y.createRelativePositionFromJSON(json);
    expect(Y.compareRelativePositions(rel, back)).toBe(true);
  });

  test("binary round trips resolve to the same absolute position", () => {
    /** Verifies: YJS-POS-006 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "hello");
    const rel = Y.createRelativePositionFromTypeIndex(t, 3);
    const encoded = Y.encodeRelativePosition(rel);
    expect(encoded).toBeInstanceOf(Uint8Array);
    const decoded = Y.decodeRelativePosition(encoded);
    const abs = Y.createAbsolutePositionFromRelativePosition(decoded, doc);
    expect(abs).not.toBeNull();
    expect(abs!.index).toBe(3);
    expect(abs!.type).toBe(t);
  });

  test("resolving against an unrelated replica returns null", () => {
    /** Verifies: YJS-POS-002 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "content");
    const rel = Y.createRelativePositionFromTypeIndex(t, 2);
    const stranger = new Y.Doc();
    stranger.getText("t");
    expect(Y.createAbsolutePositionFromRelativePosition(rel, stranger)).toBeNull();
  });

  test("a position whose anchor was deleted collapses to the removal point", () => {
    /** Verifies: YJS-POS-004 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "hello world");
    const rel = Y.createRelativePositionFromTypeIndex(t, 6);
    t.delete(4, 4);
    const abs = Y.createAbsolutePositionFromRelativePosition(rel, doc);
    expect(abs).not.toBeNull();
    expect(abs!.index).toBe(4);
    expect(t.toString()).toBe("hellrld");
  });
});
