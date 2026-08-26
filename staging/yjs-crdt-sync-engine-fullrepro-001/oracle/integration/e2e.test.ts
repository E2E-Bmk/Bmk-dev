// Spec2Repo oracle - system_e2e tests for yjs-crdt-sync-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import * as Y from "yjs";

const sync = (a: Y.Doc, b: Y.Doc): void => {
  Y.applyUpdate(a, Y.encodeStateAsUpdate(b), "sync");
  Y.applyUpdate(b, Y.encodeStateAsUpdate(a), "sync");
};

describe("collaborative sessions end to end", () => {
  test("two clients edit, sync, and undo with cursors surviving", () => {
    /** Verifies: YJS-CVI-001, YJS-CVI-004, YJS-CVI-006 */
    const alice = new Y.Doc();
    const bob = new Y.Doc();
    const aliceUndo = new Y.UndoManager(alice.getText("doc"), { captureTimeout: 0 });

    alice.getText("doc").insert(0, "The quick fox");
    sync(alice, bob);
    // bob keeps a cursor before "fox"
    const bobCursor = Y.createRelativePositionFromTypeIndex(bob.getText("doc"), 10);

    // concurrent edits: alice inserts "brown " before fox, bob appends
    alice.getText("doc").insert(10, "brown ");
    bob.getText("doc").insert(13, " jumps");
    sync(alice, bob);

    expect(alice.getText("doc").toString()).toBe(bob.getText("doc").toString());
    expect(alice.getText("doc").toString()).toBe("The quick brown fox jumps");

    // bob's cursor still points at the f of fox on both replicas
    const absOnBob = Y.createAbsolutePositionFromRelativePosition(bobCursor, bob);
    expect(absOnBob).not.toBeNull();
    expect(bob.getText("doc").toString()[absOnBob!.index]).toBe("f");

    // alice undoes her last tracked edit; remote content stays
    aliceUndo.undo();
    sync(alice, bob);
    expect(alice.getText("doc").toString()).toBe("The quick fox jumps");
    expect(bob.getText("doc").toString()).toBe("The quick fox jumps");

    // redo brings it back everywhere
    aliceUndo.redo();
    sync(alice, bob);
    expect(bob.getText("doc").toString()).toBe("The quick brown fox jumps");
  });

  test("offline client catches up through a merging relay", () => {
    /** Verifies: YJS-CVI-001, YJS-CVI-002, YJS-UPD-007 */
    const online = new Y.Doc();
    const offline = new Y.Doc();
    const relayLog: Uint8Array[] = [];
    online.on("update", (u: Uint8Array) => {
      relayLog.push(u);
    });

    // shared starting point
    online.getMap("state").set("title", "kickoff");
    Y.applyUpdate(offline, Y.encodeStateAsUpdate(online));

    // the online client keeps working; the offline client works locally
    online.getArray("tasks").push(["spec", "tests"]);
    online.getMap("state").set("title", "sprint 1");
    online.getText("notes").insert(0, "remember the edge cases");
    offline.getArray("tasks").push(["offline-idea"]);

    // the relay compacts its log before the offline client reconnects
    const compacted = Y.mergeUpdates(relayLog);
    const need = Y.diffUpdate(compacted, Y.encodeStateVector(offline));
    Y.applyUpdate(offline, need);
    // and the relay learns what the offline client did
    Y.applyUpdate(online, Y.encodeStateAsUpdate(offline, Y.encodeStateVector(online)));

    expect(offline.getMap("state").toJSON()).toEqual(online.getMap("state").toJSON());
    expect(offline.getText("notes").toString()).toBe("remember the edge cases");
    const tasks = online.getArray("tasks").toArray();
    expect(offline.getArray("tasks").toArray()).toEqual(tasks);
    expect([...tasks].sort()).toEqual(["offline-idea", "spec", "tests"]);
  });

  test("a versioned document restores an old release while editing continues", () => {
    /** Verifies: YJS-CVI-005, YJS-SNAP-003, YJS-SNAP-006 */
    const doc = new Y.Doc({ gc: false });
    const body = doc.getText("body");
    const meta = doc.getMap("meta");

    body.insert(0, "v1 body");
    meta.set("release", "1.0");
    const rel1 = Y.snapshot(doc);
    const rel1Encoded = Y.encodeSnapshot(rel1);
    const updateAtRel1 = Y.encodeStateAsUpdate(doc);

    body.delete(0, 2);
    body.insert(0, "v2");
    meta.set("release", "2.0");
    const rel2 = Y.snapshot(doc);

    // versions are distinguishable and serializable
    expect(Y.equalSnapshots(rel1, rel2)).toBe(false);
    expect(Y.equalSnapshots(Y.decodeSnapshot(rel1Encoded), rel1)).toBe(true);

    // coverage: rel2 covers the v1-era update, rel1 does not cover current history
    expect(Y.snapshotContainsUpdate(rel2, updateAtRel1)).toBe(true);
    expect(Y.snapshotContainsUpdate(rel1, Y.encodeStateAsUpdate(doc))).toBe(false);

    // restore the old release into a fresh document
    const restored = Y.createDocFromSnapshot(doc, Y.decodeSnapshot(rel1Encoded));
    expect(restored.getText("body").toString()).toBe("v1 body");
    expect(restored.getMap("meta").toJSON()).toEqual({ release: "1.0" });

    // the live document is unaffected and continues forward
    expect(body.toString()).toBe("v2 body");
    body.insert(7, " (final)");
    expect(body.toString()).toBe("v2 body (final)");
  });

  test("a shared board converges across three replicas with deep observers", () => {
    /** Verifies: YJS-CVI-001, YJS-CVI-003, YJS-EVT-002 */
    const a = new Y.Doc();
    const b = new Y.Doc();
    const c = new Y.Doc();

    // replica A builds the board structure
    const board = a.getMap("board");
    const todo = new Y.Map();
    board.set("todo", todo);
    const cards = new Y.Array();
    todo.set("cards", cards);
    const card = new Y.Map();
    cards.push([card]);
    card.set("title", "bootstrap");

    Y.applyUpdate(b, Y.encodeStateAsUpdate(a));
    Y.applyUpdate(c, Y.encodeStateAsUpdate(a));

    // replica B watches deeply and receives remote changes with paths
    const seenPaths: unknown[] = [];
    b.getMap("board").observeDeep((events) => {
      for (const event of events) seenPaths.push(event.path);
    });

    // replica C edits the nested card; replica A adds a second card concurrently
    const cCard = ((c.getMap("board").get("todo") as Y.Map<unknown>).get("cards") as Y.Array<Y.Map<unknown>>).get(0);
    cCard.set("done", true);
    const second = new Y.Map();
    second.set("title", "review");
    cards.push([second]);

    // full mesh exchange
    const exchange = (x: Y.Doc, y: Y.Doc) => {
      Y.applyUpdate(y, Y.encodeStateAsUpdate(x, Y.encodeStateVector(y)));
      Y.applyUpdate(x, Y.encodeStateAsUpdate(y, Y.encodeStateVector(x)));
    };
    exchange(a, b);
    exchange(b, c);
    exchange(a, c);
    exchange(a, b);

    const expected = {
      todo: { cards: [{ title: "bootstrap", done: true }, { title: "review" }] },
    };
    expect(a.getMap("board").toJSON()).toEqual(expected);
    expect(b.getMap("board").toJSON()).toEqual(expected);
    expect(c.getMap("board").toJSON()).toEqual(expected);

    // deep observation on B saw the nested card path from the remote edit
    expect(seenPaths).toContainEqual(["todo", "cards", 0]);
  });
});
