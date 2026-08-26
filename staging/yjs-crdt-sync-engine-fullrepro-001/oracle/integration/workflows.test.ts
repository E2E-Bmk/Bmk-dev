// Spec2Repo oracle - integration tests for yjs-crdt-sync-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import * as Y from "yjs";

const sync = (a: Y.Doc, b: Y.Doc): void => {
  Y.applyUpdate(a, Y.encodeStateAsUpdate(b));
  Y.applyUpdate(b, Y.encodeStateAsUpdate(a));
};

describe("replica convergence", () => {
  test("bidirectional update exchange converges text replicas", () => {
    /** Verifies: YJS-CVI-001, YJS-TXT-011 */
    const alice = new Y.Doc();
    const bob = new Y.Doc();
    alice.getText("note").insert(0, "hello");
    Y.applyUpdate(bob, Y.encodeStateAsUpdate(alice));
    bob.getText("note").insert(5, " world");
    alice.getText("note").insert(0, ">> ");
    sync(alice, bob);
    expect(alice.getText("note").toString()).toBe(bob.getText("note").toString());
    expect(alice.getText("note").toString()).toBe(">> hello world");
  });

  test("concurrent same-position text inserts stay intact and converge", () => {
    /** Verifies: YJS-TXT-011, YJS-CVI-001 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    a.getText("t").insert(0, "base");
    Y.applyUpdate(b, Y.encodeStateAsUpdate(a));
    a.getText("t").insert(4, "-one");
    b.getText("t").insert(4, "-two");
    sync(a, b);
    const result = a.getText("t").toString();
    expect(result).toBe(b.getText("t").toString());
    expect(result).toContain("-one");
    expect(result).toContain("-two");
    expect(result.startsWith("base")).toBe(true);
    expect(result.length).toBe("base-one-two".length);
  });

  test("concurrent map writes converge on one of the written values", () => {
    /** Verifies: YJS-MAP-004 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    a.getMap("m").set("k", "from-a");
    b.getMap("m").set("k", "from-b");
    sync(a, b);
    const winner = a.getMap("m").get("k");
    expect(b.getMap("m").get("k")).toBe(winner);
    expect(["from-a", "from-b"]).toContain(winner);
  });

  test("concurrent array insertions preserve every item exactly once", () => {
    /** Verifies: YJS-ARR-009, YJS-CVI-001 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    a.getArray("l").push(["shared"]);
    Y.applyUpdate(b, Y.encodeStateAsUpdate(a));
    a.getArray("l").push(["from-a1", "from-a2"]);
    b.getArray("l").unshift(["from-b"]);
    sync(a, b);
    const left = a.getArray("l").toArray();
    const right = b.getArray("l").toArray();
    expect(left).toEqual(right);
    expect([...left].sort()).toEqual(["from-a1", "from-a2", "from-b", "shared"]);
  });

  test("an update with missing dependencies is buffered until they arrive", () => {
    /** Verifies: YJS-UPD-007 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "one");
    const u1 = Y.encodeStateAsUpdate(src);
    const sv1 = Y.encodeStateVector(src);
    src.getText("t").insert(3, " two");
    const u2 = Y.encodeStateAsUpdate(src, sv1);
    const dst = new Y.Doc();
    Y.applyUpdate(dst, u2);
    expect(dst.getText("t").toString()).toBe("");
    Y.applyUpdate(dst, u1);
    expect(dst.getText("t").toString()).toBe("one two");
  });

  test("shuffled and duplicated update sets converge to the same content", () => {
    /** Verifies: YJS-UPD-006, YJS-CVI-001 */
    const src = new Y.Doc();
    const updates: Uint8Array[] = [];
    src.on("update", (u: Uint8Array) => {
      updates.push(u);
    });
    src.getText("t").insert(0, "abc");
    src.getMap("m").set("k", 1);
    src.getText("t").insert(3, "def");
    src.getArray("a").push([true, null]);
    expect(updates.length).toBe(4);
    const ordered = new Y.Doc();
    for (const u of updates) Y.applyUpdate(ordered, u);
    const shuffled = new Y.Doc();
    for (const u of [updates[3], updates[1], updates[0], updates[2], updates[1]]) {
      Y.applyUpdate(shuffled, u);
    }
    expect(shuffled.getText("t").toString()).toBe(ordered.getText("t").toString());
    expect(shuffled.getMap("m").toJSON()).toEqual(ordered.getMap("m").toJSON());
    expect(shuffled.getArray("a").toArray()).toEqual(ordered.getArray("a").toArray());
  });

  test("state-vector diff exchange syncs two diverged replicas minimally", () => {
    /** Verifies: YJS-UPD-001, YJS-UPD-003, YJS-CVI-007 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    a.getMap("m").set("a-key", "a-value");
    b.getMap("m").set("b-key", "b-value");
    const diffForB = Y.encodeStateAsUpdate(a, Y.encodeStateVector(b));
    const diffForA = Y.encodeStateAsUpdate(b, Y.encodeStateVector(a));
    Y.applyUpdate(b, diffForB);
    Y.applyUpdate(a, diffForA);
    expect(a.getMap("m").toJSON()).toEqual({ "a-key": "a-value", "b-key": "b-value" });
    expect(b.getMap("m").toJSON()).toEqual(a.getMap("m").toJSON());
  });

  test("merge and diff over per-transaction updates equal direct replay", () => {
    /** Verifies: YJS-UPD-008, YJS-UPD-009, YJS-UPD-010, YJS-CVI-002 */
    const src = new Y.Doc();
    const updates: Uint8Array[] = [];
    src.on("update", (u: Uint8Array) => {
      updates.push(u);
    });
    src.getText("t").insert(0, "start");
    src.getText("t").insert(5, " middle");
    src.getMap("m").set("done", true);
    expect(updates.length).toBe(3);
    const merged = Y.mergeUpdates(updates);
    const direct = new Y.Doc();
    Y.applyUpdate(direct, Y.encodeStateAsUpdate(src));
    expect(direct.getText("t").toString()).toBe("start middle");
    expect(direct.getMap("m").toJSON()).toEqual({ done: true });
    const viaMerge = new Y.Doc();
    Y.applyUpdate(viaMerge, merged);
    expect(viaMerge.getText("t").toString()).toBe(direct.getText("t").toString());
    expect(viaMerge.getMap("m").toJSON()).toEqual(direct.getMap("m").toJSON());
    const svFirst = Y.encodeStateVectorFromUpdate(updates[0]);
    const rest = Y.diffUpdate(merged, svFirst);
    const staged = new Y.Doc();
    Y.applyUpdate(staged, updates[0]);
    Y.applyUpdate(staged, rest);
    expect(staged.getText("t").toString()).toBe(direct.getText("t").toString());
    expect(staged.getMap("m").toJSON()).toEqual(direct.getMap("m").toJSON());
  });

  test("v1 and v2 histories replay to identical replicas", () => {
    /** Verifies: YJS-UPD-011, YJS-UPD-012, YJS-CVI-002 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "mixed formats");
    src.getText("t").format(0, 5, { bold: true });
    src.getArray("a").push([1, "two", null]);
    const viaV1 = new Y.Doc();
    Y.applyUpdate(viaV1, Y.encodeStateAsUpdate(src));
    const viaV2 = new Y.Doc();
    Y.applyUpdateV2(viaV2, Y.encodeStateAsUpdateV2(src));
    const viaConversion = new Y.Doc();
    Y.applyUpdate(viaConversion, Y.convertUpdateFormatV2ToV1(Y.convertUpdateFormatV1ToV2(Y.encodeStateAsUpdate(src))));
    for (const replica of [viaV1, viaV2, viaConversion]) {
      expect(replica.getText("t").toString()).toBe("mixed formats");
      expect(replica.getText("t").toDelta()).toEqual([
        { insert: "mixed", attributes: { bold: true } },
        { insert: " formats" },
      ]);
      expect(replica.getArray("a").toArray()).toEqual([1, "two", null]);
    }
  });

  test("per-transaction update events replayed in order rebuild the peer", () => {
    /** Verifies: YJS-DOC-010, YJS-DOC-011 */
    const src = new Y.Doc();
    const peer = new Y.Doc();
    src.on("update", (u: Uint8Array) => {
      Y.applyUpdate(peer, u);
    });
    src.transact(() => {
      src.getMap("m").set("phase", 1);
      src.getArray("log").push(["created"]);
    });
    src.transact(() => {
      src.getMap("m").set("phase", 2);
      src.getArray("log").push(["updated"]);
    });
    expect(peer.getMap("m").toJSON()).toEqual({ phase: 2 });
    expect(peer.getArray("log").toArray()).toEqual(["created", "updated"]);
  });
});

describe("events across replicas and nesting", () => {
  test("remote transactions fire observers with local false and the applyUpdate origin", () => {
    /** Verifies: YJS-EVT-010, YJS-EVT-011 */
    const src = new Y.Doc();
    src.getText("t").insert(0, "remote content");
    const dst = new Y.Doc();
    const seen: Array<[unknown, boolean, string]> = [];
    dst.getText("t").observe((event, txn) => {
      seen.push([txn.origin, txn.local, event.delta.map((op) => ("insert" in op ? op.insert : "")).join("")]);
    });
    Y.applyUpdate(dst, Y.encodeStateAsUpdate(src), "provider");
    expect(seen).toEqual([["provider", false, "remote content"]]);
  });

  test("observeDeep reports paths across map and array nesting", () => {
    /** Verifies: YJS-EVT-002, YJS-EVT-003 */
    const doc = new Y.Doc();
    const root = doc.getMap("root");
    const inner = new Y.Map();
    root.set("inner", inner);
    const list = new Y.Array();
    inner.set("list", list);
    const item = new Y.Map();
    list.push([item]);
    const paths: unknown[] = [];
    root.observeDeep((events) => {
      for (const event of events) paths.push(event.path);
    });
    doc.transact(() => {
      item.set("x", 1);
      inner.set("flag", true);
    });
    expect(paths).toContainEqual(["inner", "list", 0]);
    expect(paths).toContainEqual(["inner"]);
  });

  test("unobserveDeep stops nested delivery", () => {
    /** Verifies: YJS-EVT-002 */
    const doc = new Y.Doc();
    const root = doc.getMap("root");
    const inner = new Y.Map();
    root.set("inner", inner);
    let calls = 0;
    const handler = () => {
      calls += 1;
    };
    root.observeDeep(handler);
    inner.set("a", 1);
    root.unobserveDeep(handler);
    inner.set("b", 2);
    expect(calls).toBe(1);
  });

  test("an array event delta replayed over the pre-state yields the post-state", () => {
    /** Verifies: YJS-CVI-003, YJS-EVT-008 */
    const doc = new Y.Doc();
    const a = doc.getArray("a");
    a.push(["a", "b", "c", "d"]);
    const pre = a.toArray();
    let replayed: unknown[] = [];
    a.observe((event) => {
      const out: unknown[] = [];
      let cursor = 0;
      for (const op of event.delta) {
        if ("retain" in op && typeof op.retain === "number") {
          out.push(...pre.slice(cursor, cursor + op.retain));
          cursor += op.retain;
        } else if ("delete" in op && typeof op.delete === "number") {
          cursor += op.delete;
        } else if ("insert" in op && Array.isArray(op.insert)) {
          out.push(...op.insert);
        }
      }
      out.push(...pre.slice(cursor));
      replayed = out;
    });
    doc.transact(() => {
      a.delete(1, 2);
      a.insert(1, ["X", "Y"]);
      a.push(["end"]);
    });
    expect(replayed).toEqual(a.toArray());
    expect(a.toArray()).toEqual(["a", "X", "Y", "d", "end"]);
  });

  test("map key records agree with pre- and post-transaction values", () => {
    /** Verifies: YJS-CVI-003, YJS-EVT-006 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    m.set("stays", "old");
    m.set("leaves", "bye");
    const pre = m.toJSON();
    let records: Array<[string, string, unknown]> = [];
    m.observe((event) => {
      records = [...event.changes.keys.entries()].map(([k, c]) => [k, c.action, c.oldValue]);
    });
    doc.transact(() => {
      m.set("stays", "new");
      m.delete("leaves");
      m.set("appears", 1);
    });
    const post = m.toJSON();
    records.sort((x, y) => x[0].localeCompare(y[0]));
    expect(records).toEqual([
      ["appears", "add", undefined],
      ["leaves", "delete", pre.leaves],
      ["stays", "update", pre.stays],
    ]);
    expect(post).toEqual({ stays: "new", appears: 1 });
  });

  test("nested standalone types replicate wholesale through one update", () => {
    /** Verifies: YJS-MAP-009, YJS-ARR-005, YJS-CVI-001 */
    const src = new Y.Doc();
    const board = src.getMap("board");
    const column = new Y.Map();
    board.set("todo", column);
    const cards = new Y.Array();
    column.set("cards", cards);
    const card = new Y.Map();
    cards.push([card]);
    card.set("title", "write tests");
    const note = new Y.Text("body text");
    card.set("note", note);
    const dst = new Y.Doc();
    Y.applyUpdate(dst, Y.encodeStateAsUpdate(src));
    expect(dst.getMap("board").toJSON()).toEqual({
      todo: { cards: [{ title: "write tests", note: "body text" }] },
    });
    expect(dst.getMap("board").toJSON()).toEqual(src.getMap("board").toJSON());
  });

  test("formatting applied on one replica appears in the peer's delta view", () => {
    /** Verifies: YJS-TXT-012, YJS-CVI-001 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    a.getText("t").insert(0, "sync me");
    Y.applyUpdate(b, Y.encodeStateAsUpdate(a));
    a.getText("t").format(0, 4, { underline: true });
    Y.applyUpdate(b, Y.encodeStateAsUpdate(a, Y.encodeStateVector(b)));
    expect(b.getText("t").toDelta()).toEqual([
      { insert: "sync", attributes: { underline: true } },
      { insert: " me" },
    ]);
    expect(b.getText("t").toDelta()).toEqual(a.getText("t").toDelta());
  });
});

describe("undo, snapshots, and positions across documents", () => {
  test("undo reverts local content while preserving interleaved remote content", () => {
    /** Verifies: YJS-UNDO-009, YJS-CVI-004 */
    const local = new Y.Doc();
    const remote = new Y.Doc();
    const lt = local.getText("t");
    const um = new Y.UndoManager(lt);
    lt.insert(0, "local");
    Y.applyUpdate(remote, Y.encodeStateAsUpdate(local), "sync");
    remote.getText("t").insert(0, "remote-");
    Y.applyUpdate(local, Y.encodeStateAsUpdate(remote), "sync");
    expect(lt.toString()).toBe("remote-local");
    um.undo();
    expect(lt.toString()).toBe("remote-");
    um.redo();
    expect(lt.toString()).toBe("remote-local");
  });

  test("undone state propagates to peers like any other edit", () => {
    /** Verifies: YJS-CVI-004 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    const um = new Y.UndoManager(a.getText("t"), { captureTimeout: 0 });
    a.getText("t").insert(0, "keep ");
    um.stopCapturing();
    a.getText("t").insert(5, "drop");
    um.undo();
    sync(a, b);
    expect(b.getText("t").toString()).toBe("keep ");
    um.redo();
    sync(a, b);
    expect(b.getText("t").toString()).toBe("keep drop");
    expect(a.getText("t").toString()).toBe(b.getText("t").toString());
  });

  test("tracked origins separate user edits from provider updates", () => {
    /** Verifies: YJS-UNDO-002, YJS-UNDO-009 */
    const doc = new Y.Doc();
    const m = doc.getMap("m");
    const um = new Y.UndoManager(m, { trackedOrigins: new Set(["user"]), captureTimeout: 0 });
    doc.transact(() => m.set("color", "red"), "user");
    doc.transact(() => m.set("server-flag", true), "server");
    doc.transact(() => m.set("color", "blue"), "user");
    um.undo();
    expect(m.get("color")).toBe("red");
    expect(m.get("server-flag")).toBe(true);
    um.undo();
    expect(m.has("color")).toBe(false);
    expect(um.canUndo()).toBe(false);
  });

  test("stack item meta persists from added to popped for cursor restoration", () => {
    /** Verifies: YJS-UNDO-010, YJS-UNDO-011, YJS-POS-003 */
    const doc = new Y.Doc();
    const t = doc.getText("t");
    t.insert(0, "hello world");
    const um = new Y.UndoManager(t, { captureTimeout: 0 });
    const popped: Array<[string, unknown]> = [];
    um.on("stack-item-added", (event: { stackItem: { meta: Map<string, unknown> }; type: string }) => {
      event.stackItem.meta.set("cursor", Y.createRelativePositionFromTypeIndex(t, 5));
    });
    um.on("stack-item-popped", (event: { stackItem: { meta: Map<string, unknown> }; type: string }) => {
      popped.push([event.type, event.stackItem.meta.get("cursor")]);
    });
    t.insert(11, "!");
    um.undo();
    expect(popped.length).toBe(1);
    expect(popped[0][0]).toBe("undo");
    const rel = popped[0][1] as Parameters<typeof Y.createAbsolutePositionFromRelativePosition>[0];
    const abs = Y.createAbsolutePositionFromRelativePosition(rel, doc);
    expect(abs).not.toBeNull();
    expect(abs!.index).toBe(5);
  });

  test("snapshot restoration reproduces the version while history moves on", () => {
    /** Verifies: YJS-SNAP-004, YJS-SNAP-006, YJS-CVI-005 */
    const doc = new Y.Doc({ gc: false });
    const t = doc.getText("t");
    const m = doc.getMap("meta");
    t.insert(0, "draft one");
    m.set("version", 1);
    const v1 = Y.snapshot(doc);
    const updateAtV1 = Y.encodeStateAsUpdate(doc);
    t.insert(0, "REVISED ");
    m.set("version", 2);
    const v2 = Y.snapshot(doc);
    expect(Y.equalSnapshots(v1, v2)).toBe(false);
    const restored = Y.createDocFromSnapshot(doc, v1);
    expect(restored.getText("t").toString()).toBe("draft one");
    expect(restored.getMap("meta").toJSON()).toEqual({ version: 1 });
    expect(Y.snapshotContainsUpdate(v1, updateAtV1)).toBe(true);
    expect(Y.snapshotContainsUpdate(v1, Y.encodeStateAsUpdate(doc))).toBe(false);
    expect(Y.snapshotContainsUpdate(v2, Y.encodeStateAsUpdate(doc))).toBe(true);
  });

  test("relative positions track their character across remote edits and codecs", () => {
    /** Verifies: YJS-POS-003, YJS-CVI-006 */
    const home = new Y.Doc();
    const t = home.getText("t");
    t.insert(0, "hello world");
    const rel = Y.createRelativePositionFromTypeIndex(t, 6);
    const json = Y.relativePositionToJSON(rel);
    const bin = Y.encodeRelativePosition(rel);
    const peer = new Y.Doc();
    Y.applyUpdate(peer, Y.encodeStateAsUpdate(home));
    peer.getText("t").insert(0, ">>> ");
    Y.applyUpdate(home, Y.encodeStateAsUpdate(peer, Y.encodeStateVector(home)));
    expect(t.toString()).toBe(">>> hello world");
    const fromLive = Y.createAbsolutePositionFromRelativePosition(rel, home);
    const fromJson = Y.createAbsolutePositionFromRelativePosition(Y.createRelativePositionFromJSON(json), home);
    const fromBin = Y.createAbsolutePositionFromRelativePosition(Y.decodeRelativePosition(bin), home);
    for (const abs of [fromLive, fromJson, fromBin]) {
      expect(abs).not.toBeNull();
      expect(abs!.index).toBe(10);
    }
    expect(t.toString()[10]).toBe("w");
  });

  test("map undo interleaved with remote updates keeps remote keys", () => {
    /** Verifies: YJS-UNDO-009, YJS-UNDO-008 */
    const local = new Y.Doc();
    const remote = new Y.Doc();
    const lm = local.getMap("m");
    const um = new Y.UndoManager(lm, { captureTimeout: 0 });
    lm.set("mine", 1);
    Y.applyUpdate(remote, Y.encodeStateAsUpdate(local), "sync");
    remote.getMap("m").set("theirs", 2);
    Y.applyUpdate(local, Y.encodeStateAsUpdate(remote), "sync");
    um.undo();
    expect(lm.has("mine")).toBe(false);
    expect(lm.get("theirs")).toBe(2);
  });
});
