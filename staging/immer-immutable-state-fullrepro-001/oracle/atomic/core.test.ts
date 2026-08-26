// Oracle - atomic tests for the immer immutable-state specification (plugins loaded).
import { describe, expect, test } from "vitest";
import {
  produce,
  produceWithPatches,
  applyPatches,
  createDraft,
  finishDraft,
  current,
  original,
  isDraft,
  isDraftable,
  freeze,
  nothing,
  immerable,
  castDraft,
  castImmutable,
  setAutoFreeze,
  setUseStrictShallowCopy,
  setUseStrictIteration,
  enablePatches,
  enableMapSet,
  enableArrayMethods,
  Immer,
  type Patch,
} from "immer";

enablePatches();
enableMapSet();
enableArrayMethods();

interface Todo {
  title: string;
  done: boolean;
}
interface Store {
  todos: Todo[];
  settings: { theme: string };
}

function baseStore(): Store {
  return {
    todos: [
      { title: "write", done: false },
      { title: "review", done: false },
    ],
    settings: { theme: "dark" },
  };
}

describe("producing state", () => {
  test("produce returns the next state and never mutates the base", () => {
    /** Verifies: IMM-PROD-001 */
    const base = baseStore();
    const next = produce(base, (d) => {
      d.todos[0]!.done = true;
      d.todos.push({ title: "ship", done: false });
    });
    expect(next.todos.map((t) => t.done)).toEqual([true, false, false]);
    expect(next.todos).toHaveLength(3);
    expect(base.todos).toHaveLength(2);
    expect(base.todos[0]!.done).toBe(false);
  });

  test("a recipe that changes nothing returns the base by reference", () => {
    /** Verifies: IMM-PROD-002 */
    const base = baseStore();
    const next = produce(base, (d) => {
      void d.todos[0]!.title;
      void d.settings.theme;
    });
    expect(next).toBe(base);
  });

  test("changed branches are new objects while untouched branches keep identity", () => {
    /** Verifies: IMM-PROD-003 */
    const base = baseStore();
    const next = produce(base, (d) => {
      d.todos[0]!.done = true;
    });
    expect(next).not.toBe(base);
    expect(next.todos).not.toBe(base.todos);
    expect(next.todos[0]).not.toBe(base.todos[0]);
    expect(next.todos[1]).toBe(base.todos[1]);
    expect(next.settings).toBe(base.settings);
  });

  test("primitive and null bases pass through the producer", () => {
    /** Verifies: IMM-PROD-004 */
    expect(produce(3 as unknown as object, () => {})).toBe(3);
    expect(produce("s" as unknown as object, () => "t" as unknown as object)).toBe("t");
    expect(produce(null as unknown as object, () => {})).toBe(null);
  });

  test("producing over a non-draftable object base throws", () => {
    /** Verifies: IMM-PROD-005 */
    class Unmarked {
      v = 1;
    }
    expect(() => produce(new Date(0) as unknown as object, () => {})).toThrow(Error);
    expect(() => produce(new Unmarked() as unknown as object, () => {})).toThrow(Error);
  });

  test("produced results are deeply frozen by default and reject strict-mode mutation", () => {
    /** Verifies: IMM-PROD-009 */
    const next = produce(baseStore(), (d) => {
      d.todos[0]!.done = true;
    });
    expect(Object.isFrozen(next)).toBe(true);
    expect(Object.isFrozen(next.todos)).toBe(true);
    expect(Object.isFrozen(next.todos[0])).toBe(true);
    expect(() => {
      (next.todos[0] as Todo).done = false;
    }).toThrow(TypeError);
  });

  test("a pre-frozen base is a legal input", () => {
    /** Verifies: IMM-PROD-010 */
    const base = freeze({ a: { x: 1 } }, true);
    const next = produce(base, (d) => {
      d.a.x = 9;
    });
    expect(next.a.x).toBe(9);
    expect(base.a.x).toBe(1);
  });

  test("nested reads inside a recipe are drafts and mutations are visible immediately", () => {
    /** Verifies: IMM-PROD-011, IMM-LIFE-006 */
    const base = baseStore();
    produce(base, (d) => {
      expect(isDraft(d)).toBe(true);
      expect(isDraft(d.todos)).toBe(true);
      expect(isDraft(d.todos[0])).toBe(true);
      expect(isDraft(base)).toBe(false);
      d.settings.theme = "light";
      expect(d.settings.theme).toBe("light");
      expect(d.todos[1]!.title).toBe("review");
    });
  });

  test("a draft that escapes its recipe is revoked", () => {
    /** Verifies: IMM-PROD-012 */
    let leaked: { theme: string } | undefined;
    produce(baseStore(), (d) => {
      leaked = d.settings;
    });
    expect(() => void leaked!.theme).toThrow();
  });

  test("nested produce composes with the outer draft", () => {
    /** Verifies: IMM-PROD-013 */
    const next = produce({ out: { n: 1 }, other: { m: 1 } }, (d) => {
      d.out = produce(current(d.out), (inner) => {
        inner.n = 5;
      });
    });
    expect(next.out.n).toBe(5);
    expect(next.other.m).toBe(1);
  });
});

describe("recipe return rules", () => {
  test("returning undefined finalizes the draft", () => {
    /** Verifies: IMM-PROD-006 */
    const base = { n: 1 };
    expect(produce(base, () => undefined)).toBe(base);
    const next = produce(base, (d) => {
      d.n = 2;
      return undefined;
    });
    expect(next.n).toBe(2);
  });

  test("returning a fresh value replaces the state", () => {
    /** Verifies: IMM-PROD-014 */
    const base = { n: 1 };
    const next = produce(base, () => ({ replaced: true }) as unknown as typeof base);
    expect(next).toEqual({ replaced: true });
    expect(base.n).toBe(1);
  });

  test("returning the modified draft itself is allowed", () => {
    /** Verifies: IMM-PROD-006 */
    const next = produce({ n: 1 }, (d) => {
      d.n = 5;
      return d;
    });
    expect(next.n).toBe(5);
  });

  test("modifying the draft and returning a new value throws", () => {
    /** Verifies: IMM-PROD-007 */
    expect(() =>
      produce({ n: 1 }, (d) => {
        d.n = 2;
        return { z: 1 } as unknown as { n: number };
      }),
    ).toThrow(Error);
  });

  test("returning a promise while modifying the draft throws", () => {
    /** Verifies: IMM-PROD-007 */
    expect(() =>
      produce({ n: 1 }, (async (d: { n: number }) => {
        d.n = 2;
      }) as unknown as (d: { n: number }) => void),
    ).toThrow(Error);
  });

  test("returning nothing produces undefined", () => {
    /** Verifies: IMM-PROD-008 */
    const next = produce({ n: 1 }, () => nothing as unknown as { n: number });
    expect(next).toBeUndefined();
  });
});

describe("curried producers", () => {
  test("currying returns a reusable producer that forwards extra arguments", () => {
    /** Verifies: IMM-CURRY-001, IMM-CURRY-002 */
    const add = produce((d: { n: number }, by: number) => {
      d.n += by;
    });
    expect(add({ n: 1 }, 5)).toEqual({ n: 6 });
    expect(add({ n: 10 }, 1)).toEqual({ n: 11 });
  });

  test("a curried producer with a default state uses it for an undefined base", () => {
    /** Verifies: IMM-CURRY-003 */
    const bump = produce(
      (d: { n: number }) => {
        d.n += 1;
      },
      { n: 100 },
    );
    expect(bump(undefined)).toEqual({ n: 101 });
  });

  test("an explicit base overrides the curried default", () => {
    /** Verifies: IMM-CURRY-003 */
    const bump = produce(
      (d: { n: number }, by: number) => {
        d.n += by;
      },
      { n: 100 },
    );
    expect(bump({ n: 5 }, 2)).toEqual({ n: 7 });
    expect(bump(undefined, 5)).toEqual({ n: 105 });
  });

  test("curried produceWithPatches returns the state-and-patches triple", () => {
    /** Verifies: IMM-CURRY-004 */
    const curried = produceWithPatches((d: { n: number }) => {
      d.n = 9;
    });
    const [next, patches, inverse] = curried({ n: 1 });
    expect(next).toEqual({ n: 9 });
    expect(patches).toEqual([{ op: "replace", path: ["n"], value: 9 }]);
    expect(inverse).toEqual([{ op: "replace", path: ["n"], value: 1 }]);
  });
});

describe("manual draft lifecycle", () => {
  test("createDraft opens a live draft that records mutations", () => {
    /** Verifies: IMM-LIFE-001 */
    const draft = createDraft({ count: 0, log: [] as string[] });
    expect(isDraft(draft)).toBe(true);
    draft.count += 1;
    draft.log.push("incremented");
    expect(draft.count).toBe(1);
    expect(draft.log).toHaveLength(1);
  });

  test("finishDraft finalizes with produce identity, sharing, and freezing rules", () => {
    /** Verifies: IMM-LIFE-002 */
    const base = { a: 1, nested: { b: 2 } };
    const draft = createDraft(base);
    draft.a = 10;
    const next = finishDraft(draft);
    expect(next).toEqual({ a: 10, nested: { b: 2 } });
    expect(next.nested).toBe(base.nested);
    expect(Object.isFrozen(next)).toBe(true);
    const untouched = createDraft(base);
    expect(finishDraft(untouched)).toBe(base);
  });

  test("finishDraft reports patches through its listener", () => {
    /** Verifies: IMM-LIFE-003 */
    const draft = createDraft({ a: 1 });
    draft.a = 99;
    let seen: [Patch[], Patch[]] | undefined;
    finishDraft(draft, (patches, inverse) => {
      seen = [patches as Patch[], inverse as Patch[]];
    });
    expect(seen![0]).toEqual([{ op: "replace", path: ["a"], value: 99 }]);
    expect(seen![1]).toEqual([{ op: "replace", path: ["a"], value: 1 }]);
  });

  test("a finished draft is revoked", () => {
    /** Verifies: IMM-LIFE-004 */
    const draft = createDraft({ a: 1 });
    draft.a = 2;
    finishDraft(draft);
    expect(() => void draft.a).toThrow();
  });

  test("createDraft and finishDraft reject invalid arguments", () => {
    /** Verifies: IMM-LIFE-005 */
    expect(() => createDraft(3 as unknown as object)).toThrow(Error);
    expect(() => finishDraft({} as unknown as ReturnType<typeof createDraft>)).toThrow(Error);
  });
});

describe("snapshots and originals", () => {
  test("current returns an unfrozen finalized snapshot of the draft so far", () => {
    /** Verifies: IMM-LIFE-007 */
    produce({ a: { x: 1 }, arr: [1] }, (d) => {
      d.a.x = 2;
      const snap = current(d);
      expect(snap).toEqual({ a: { x: 2 }, arr: [1] });
      expect(isDraft(snap)).toBe(false);
      expect(isDraft(snap.a)).toBe(false);
      expect(Object.isFrozen(snap)).toBe(false);
      expect(Object.isFrozen(snap.a)).toBe(false);
    });
  });

  test("a snapshot is decoupled from later draft mutations", () => {
    /** Verifies: IMM-LIFE-007 */
    produce({ a: { x: 1 } }, (d) => {
      d.a.x = 2;
      const snap = current(d);
      d.a.x = 3;
      expect(snap.a.x).toBe(2);
      expect(current(d).a.x).toBe(3);
    });
  });

  test("current on a non-draft throws", () => {
    /** Verifies: IMM-LIFE-008 */
    expect(() => current({} as never)).toThrow(Error);
  });

  test("original returns the underlying base with reference identity", () => {
    /** Verifies: IMM-LIFE-010 */
    const base = { a: { x: 1 } };
    produce(base, (d) => {
      d.a.x = 2;
      expect(original(d)).toBe(base);
      expect(original(d.a)).toBe(base.a);
      expect(original(d.a)!.x).toBe(1);
    });
  });

  test("original on a non-draft throws", () => {
    /** Verifies: IMM-LIFE-011 */
    expect(() => original({} as never)).toThrow(Error);
  });

  test("symbol-keyed children stay drafts in snapshots unless strict iteration is on", () => {
    /** Verifies: IMM-LIFE-009, IMM-CFG-005 */
    const SYM = Symbol("k");
    const base = { [SYM]: { n: 1 }, plain: { m: 1 } };
    produce(base, (d) => {
      d[SYM].n = 2;
      d.plain.m = 2;
      const snap = current(d);
      expect(isDraft(snap.plain)).toBe(false);
      expect(isDraft(snap[SYM])).toBe(true);
    });
    setUseStrictIteration(true);
    try {
      produce(base, (d) => {
        d[SYM].n = 3;
        const snap = current(d);
        expect(isDraft(snap[SYM])).toBe(false);
        expect(snap[SYM]).toEqual({ n: 3 });
      });
    } finally {
      setUseStrictIteration(false);
    }
  });
});

describe("draftability and freezing", () => {
  test("isDraftable accepts plain objects, arrays, maps, sets, and null-prototype objects", () => {
    /** Verifies: IMM-DRAFT-001 */
    expect(isDraftable({})).toBe(true);
    expect(isDraftable([])).toBe(true);
    expect(isDraftable(new Map())).toBe(true);
    expect(isDraftable(new Set())).toBe(true);
    expect(isDraftable(Object.create(null))).toBe(true);
    expect(isDraftable(new Date())).toBe(false);
    expect(isDraftable(null)).toBe(false);
    expect(isDraftable("x")).toBe(false);
    expect(isDraftable(() => {})).toBe(false);
  });

  test("the immerable marker makes class instances draftable with prototypes preserved", () => {
    /** Verifies: IMM-DRAFT-002, IMM-DRAFT-003 */
    class Counter {
      static [immerable] = true;
      n = 1;
    }
    const base = new Counter();
    expect(isDraftable(base)).toBe(true);
    const next = produce(base, (d) => {
      d.n = 2;
    });
    expect(next).toBeInstanceOf(Counter);
    expect(next.n).toBe(2);
    expect(base.n).toBe(1);
    expect(next).not.toBe(base);
    expect(Object.isFrozen(next)).toBe(true);
  });

  test("marking the prototype works the same as marking the class", () => {
    /** Verifies: IMM-DRAFT-002 */
    class ProtoMarked {
      v = 1;
    }
    (ProtoMarked.prototype as unknown as Record<symbol, unknown>)[immerable] = true;
    const next = produce(new ProtoMarked(), (d) => {
      d.v = 2;
    });
    expect(next).toBeInstanceOf(ProtoMarked);
    expect(next.v).toBe(2);
  });

  test("an unmarked class instance is not draftable", () => {
    /** Verifies: IMM-DRAFT-001, IMM-PROD-005 */
    class Unmarked {
      v = 1;
    }
    expect(isDraftable(new Unmarked())).toBe(false);
    expect(() => produce(new Unmarked() as unknown as object, () => {})).toThrow(Error);
  });

  test("freeze is shallow by default and deep on request", () => {
    /** Verifies: IMM-DRAFT-004 */
    const shallow = freeze({ a: { b: 1 } });
    expect(Object.isFrozen(shallow)).toBe(true);
    expect(Object.isFrozen(shallow.a)).toBe(false);
    const deep = freeze({ a: { b: 1 } }, true);
    expect(Object.isFrozen(deep)).toBe(true);
    expect(Object.isFrozen(deep.a)).toBe(true);
  });

  test("cast helpers return their argument unchanged", () => {
    /** Verifies: IMM-DRAFT-005 */
    const obj = { a: 1 };
    expect(castDraft(obj)).toBe(obj);
    expect(castImmutable(obj)).toBe(obj);
  });
});

describe("patch records", () => {
  test("object mutations record add, replace, and remove operations", () => {
    /** Verifies: IMM-PATCH-002, IMM-PATCH-003 */
    const base = { obj: { k: "v" }, n: 1 };
    const [next, patches, inverse] = produceWithPatches(base, (d) => {
      (d.obj as Record<string, string>).k2 = "v2";
      delete (d.obj as Record<string, string>).k;
      d.n = 2;
    });
    expect(next).toEqual({ obj: { k2: "v2" }, n: 2 });
    expect(patches).toContainEqual({ op: "add", path: ["obj", "k2"], value: "v2" });
    expect(patches).toContainEqual({ op: "remove", path: ["obj", "k"] });
    expect(patches).toContainEqual({ op: "replace", path: ["n"], value: 2 });
    expect(inverse).toContainEqual({ op: "remove", path: ["obj", "k2"] });
    expect(inverse).toContainEqual({ op: "add", path: ["obj", "k"], value: "v" });
    expect(inverse).toContainEqual({ op: "replace", path: ["n"], value: 1 });
  });

  test("array appends record add patches at the new indices", () => {
    /** Verifies: IMM-PATCH-004 */
    const [, patches] = produceWithPatches({ a: [1, 2] }, (d) => {
      d.a.push(3);
    });
    expect(patches).toEqual([{ op: "add", path: ["a", 2], value: 3 }]);
    const [, indexPatches] = produceWithPatches({ a: [1, 2] }, (d) => {
      d.a[0] = 5;
    });
    expect(indexPatches).toEqual([{ op: "replace", path: ["a", 0], value: 5 }]);
  });

  test("array length truncation records remove patches for dropped indices", () => {
    /** Verifies: IMM-PATCH-004 */
    const [next, patches] = produceWithPatches({ a: [1, 2, 3] }, (d) => {
      d.a.length = 1;
    });
    expect(next.a).toEqual([1]);
    expect(patches).toEqual([
      { op: "remove", path: ["a", 2] },
      { op: "remove", path: ["a", 1] },
    ]);
  });

  test("splice records patches that round-trip", () => {
    /** Verifies: IMM-PATCH-003, IMM-CVI-001 */
    const base = { a: [1, 2, 3, 4] };
    const [next, patches, inverse] = produceWithPatches(base, (d) => {
      d.a.splice(1, 2);
    });
    expect(next.a).toEqual([1, 4]);
    expect(applyPatches(base, patches)).toEqual(next);
    expect(applyPatches(next, inverse)).toEqual(base);
  });

  test("replacing the whole state records one empty-path replace patch", () => {
    /** Verifies: IMM-PATCH-006 */
    const base = { n: 1 };
    const [next, patches, inverse] = produceWithPatches(base, () => ({ fresh: 1 }) as unknown as typeof base);
    expect(next).toEqual({ fresh: 1 });
    expect(patches).toEqual([{ op: "replace", path: [], value: { fresh: 1 } }]);
    expect(inverse).toEqual([{ op: "replace", path: [], value: { n: 1 } }]);
  });

  test("producing undefined via nothing records an empty-path replace with undefined", () => {
    /** Verifies: IMM-PATCH-006 */
    const base = { n: 1 };
    const [next, patches] = produceWithPatches(base, () => nothing as unknown as typeof base);
    expect(next).toBeUndefined();
    expect(patches).toHaveLength(1);
    expect(patches[0]!.op).toBe("replace");
    expect(patches[0]!.path).toEqual([]);
    expect(patches[0]!.value).toBeUndefined();
    expect(applyPatches(base, patches)).toBeUndefined();
  });

  test("the patch listener of produce sees the same streams as produceWithPatches", () => {
    /** Verifies: IMM-PATCH-007, IMM-CVI-004 */
    const base = { list: [1], meta: { owner: "a" } };
    const recipe = (d: typeof base) => {
      d.list.push(2);
      d.meta.owner = "b";
    };
    let listened: [Patch[], Patch[]] | undefined;
    const viaListener = produce(base, recipe, (p, ip) => {
      listened = [p as Patch[], ip as Patch[]];
    });
    const [viaTriple, patches, inverse] = produceWithPatches(base, recipe);
    expect(viaListener).toEqual(viaTriple);
    expect(listened![0]).toEqual(patches);
    expect(listened![1]).toEqual(inverse);
  });

  test("a production that changes nothing emits empty patch streams", () => {
    /** Verifies: IMM-CVI-003 */
    const base = { s: 1 };
    const [same, patches, inverse] = produceWithPatches(base, () => {});
    expect(same).toBe(base);
    expect(patches).toEqual([]);
    expect(inverse).toEqual([]);
  });
});

describe("patch application", () => {
  test("applyPatches builds a new frozen state and leaves the base untouched", () => {
    /** Verifies: IMM-PATCH-008 */
    const base = { a: 1 };
    const out = applyPatches(base, [{ op: "replace", path: ["a"], value: 2 }]);
    expect(out).toEqual({ a: 2 });
    expect(base.a).toBe(1);
    expect(Object.isFrozen(out)).toBe(true);
  });

  test("add on an array index inserts and the dash index appends", () => {
    /** Verifies: IMM-PATCH-009 */
    expect(applyPatches([1, 3], [{ op: "add", path: [1], value: 2 }])).toEqual([1, 2, 3]);
    expect(applyPatches([1], [{ op: "add", path: ["-"], value: 2 }])).toEqual([1, 2]);
    expect(applyPatches({}, [{ op: "add", path: ["x"], value: 1 }])).toEqual({ x: 1 });
  });

  test("an empty-path replace substitutes the whole state", () => {
    /** Verifies: IMM-PATCH-010 */
    expect(applyPatches({ a: 1 }, [{ op: "replace", path: [], value: { b: 2 } }])).toEqual({ b: 2 });
    expect(applyPatches({ a: 1 }, [{ op: "replace", path: [], value: undefined }])).toBeUndefined();
  });

  test("removing a missing key is a no-op", () => {
    /** Verifies: IMM-PATCH-011 */
    expect(applyPatches({ a: 1 }, [{ op: "remove", path: ["b"] }])).toEqual({ a: 1 });
  });

  test("an unresolvable path throws", () => {
    /** Verifies: IMM-PATCH-012 */
    expect(() => applyPatches({}, [{ op: "add", path: ["x", "y"], value: 1 }])).toThrow(Error);
  });

  test("an unsupported op throws", () => {
    /** Verifies: IMM-PATCH-012 */
    expect(() =>
      applyPatches({}, [{ op: "move", path: ["x"], value: 1 } as unknown as Patch]),
    ).toThrow(Error);
  });

  test("applying patches to a live draft mutates it in place and returns it", () => {
    /** Verifies: IMM-PATCH-013 */
    const next = produce({ a: 1 }, (d) => {
      const returned = applyPatches(d, [{ op: "replace", path: ["a"], value: 7 }]);
      expect(isDraft(returned)).toBe(true);
      expect(returned).toBe(d);
    });
    expect(next).toEqual({ a: 7 });
  });
});

describe("map and set drafts", () => {
  test("map drafts support reads, writes, deletes, and clear while the base stays intact", () => {
    /** Verifies: IMM-MAPSET-002 */
    const base = new Map<string, number>([
      ["a", 1],
      ["b", 2],
    ]);
    const next = produce(base, (d) => {
      expect(d.size).toBe(2);
      expect(d.has("a")).toBe(true);
      expect(d.get("b")).toBe(2);
      d.set("c", 3);
      d.delete("a");
    });
    expect([...next]).toEqual([
      ["b", 2],
      ["c", 3],
    ]);
    expect([...base.keys()]).toEqual(["a", "b"]);
    const cleared = produce(base, (d) => {
      d.clear();
    });
    expect(cleared.size).toBe(0);
    expect(base.size).toBe(2);
  });

  test("map get returns drafts so nested mutation is recorded", () => {
    /** Verifies: IMM-MAPSET-003 */
    const base = new Map([["a", { v: 1 }]]);
    const next = produce(base, (d) => {
      expect(isDraft(d.get("a"))).toBe(true);
      d.get("a")!.v = 2;
    });
    expect(next.get("a")!.v).toBe(2);
    expect(base.get("a")!.v).toBe(1);
  });

  test("finalized maps preserve insertion order and are instances of Map", () => {
    /** Verifies: IMM-MAPSET-004 */
    const base = new Map([
      ["a", 1],
      ["b", 2],
    ]);
    const next = produce(base, (d) => {
      d.set("c", 3);
    });
    expect(next).toBeInstanceOf(Map);
    expect([...next.keys()]).toEqual(["a", "b", "c"]);
  });

  test("a finalized frozen map rejects mutation", () => {
    /** Verifies: IMM-MAPSET-004 */
    const next = produce(new Map([["a", 1]]), (d) => {
      d.set("b", 2);
    });
    expect(next.get("b")).toBe(2);
    expect(next.size).toBe(2);
    expect(() => next.set("c", 3)).toThrow(Error);
    expect(() => next.delete("a")).toThrow(Error);
    expect(() => next.clear()).toThrow(Error);
  });

  test("map and set productions that change nothing return the base", () => {
    /** Verifies: IMM-MAPSET-005 */
    const map = new Map([["a", 1]]);
    const set = new Set([1]);
    expect(produce(map, () => {})).toBe(map);
    expect(produce(set, () => {})).toBe(set);
  });

  test("set drafts record membership changes without touching the base", () => {
    /** Verifies: IMM-MAPSET-006 */
    const base = new Set([1, 2]);
    const next = produce(base, (d) => {
      expect(d.has(1)).toBe(true);
      expect(d.size).toBe(2);
      d.add(3);
      d.delete(1);
    });
    expect(next).toBeInstanceOf(Set);
    expect([...next]).toEqual([2, 3]);
    expect([...base]).toEqual([1, 2]);
  });

  test("iterating a set draft yields drafts whose mutations are recorded", () => {
    /** Verifies: IMM-MAPSET-006 */
    const base = new Set([{ id: 1 }, { id: 2 }]);
    const next = produce(base, (d) => {
      for (const member of d) {
        expect(isDraft(member)).toBe(true);
        if (member.id === 2) member.id = 20;
      }
    });
    expect([...next].map((m) => m.id)).toEqual([1, 20]);
    expect([...base].map((m) => m.id)).toEqual([1, 2]);
  });

  test("map patches are keyed by map key and round-trip", () => {
    /** Verifies: IMM-MAPSET-007 */
    const base = new Map<string, number>([["k", 1]]);
    const [next, patches, inverse] = produceWithPatches(base, (d) => {
      d.set("j", 3);
      d.delete("k");
    });
    expect(patches).toContainEqual({ op: "add", path: ["j"], value: 3 });
    expect(patches).toContainEqual({ op: "remove", path: ["k"] });
    expect([...applyPatches(base, patches)]).toEqual([...next]);
    expect([...applyPatches(next, inverse)]).toEqual([...base]);
  });

  test("current and original work on map drafts", () => {
    /** Verifies: IMM-MAPSET-009 */
    const base = new Map([["b", { v: 2 }]]);
    produce(base, (d) => {
      d.get("b")!.v = 99;
      const snap = current(d);
      expect([...snap]).toEqual([["b", { v: 99 }]]);
      expect(original(d)).toBe(base);
    });
  });
});

describe("array methods plugin", () => {
  test("search callbacks receive stored values, not fresh drafts", () => {
    /** Verifies: IMM-ARR-002 */
    const base = { arr: [{ v: 1 }, { v: 2 }] };
    produce(base, (d) => {
      const seen: boolean[] = [];
      d.arr.find((item) => {
        seen.push(isDraft(item));
        return item.v === 2;
      });
      expect(seen).toEqual([false, false]);
    });
    produce(base, (d) => {
      const first = d.arr.find((item) => item.v === 1)!;
      expect(isDraft(first)).toBe(true);
      const everySeen: boolean[] = [];
      d.arr.every((item) => {
        everySeen.push(isDraft(item));
        return true;
      });
      expect(everySeen).toEqual([true, false]);
    });
  });

  test("find returns a draft whose mutation is recorded", () => {
    /** Verifies: IMM-ARR-003 */
    const base = { arr: [{ v: 1 }, { v: 2 }, { v: 3 }] };
    const next = produce(base, (d) => {
      const found = d.arr.find((it) => it.v === 2)!;
      expect(isDraft(found)).toBe(true);
      found.v = 20;
    });
    expect(next.arr.map((x) => x.v)).toEqual([1, 20, 3]);
    expect(base.arr.map((x) => x.v)).toEqual([1, 2, 3]);
  });

  test("filter and slice return arrays of drafts", () => {
    /** Verifies: IMM-ARR-003 */
    const base = { arr: [{ v: 1 }, { v: 2 }, { v: 3 }] };
    const next = produce(base, (d) => {
      const subset = d.arr.filter((it) => it.v > 1);
      expect(subset.every((x) => isDraft(x))).toBe(true);
      subset[0]!.v = 99;
      const sliced = d.arr.slice(0, 1);
      expect(sliced.every((x) => isDraft(x))).toBe(true);
    });
    expect(next.arr.map((x) => x.v)).toEqual([1, 99, 3]);
  });

  test("concat and flat return non-draft structures", () => {
    /** Verifies: IMM-ARR-004 */
    produce({ arr: [{ v: 1 }] }, (d) => {
      expect(isDraft(d.arr)).toBe(true);
      const combined = d.arr.concat([{ v: 4 }]);
      expect(combined.every((x) => !isDraft(x))).toBe(true);
    });
    produce({ arr: [[{ v: 1 }], [{ v: 2 }]] }, (d) => {
      expect(isDraft(d.arr)).toBe(true);
      const flattened = d.arr.flat();
      expect(flattened.every((x) => !isDraft(x))).toBe(true);
    });
  });

  test("primitive-returning methods yield ordinary values", () => {
    /** Verifies: IMM-ARR-005 */
    produce({ arr: [{ v: 1 }, { v: 2 }, { v: 3 }] }, (d) => {
      expect(isDraft(d.arr)).toBe(true);
      expect(d.arr.findIndex((x) => x.v === 3)).toBe(2);
      expect(d.arr.some((x) => x.v === 3)).toBe(true);
      expect(d.arr.every((x) => x.v > 0)).toBe(true);
      expect([1, 2, 3].includes(2)).toBe(true);
      expect(d.arr.map((x) => x.v).join(",")).toBe("1,2,3");
    });
  });

  test("mutating methods behave like the standard implementations", () => {
    /** Verifies: IMM-ARR-006 */
    const next = produce([3, 1, 2], (d) => {
      expect(d.push(4)).toBe(4);
      expect(d.pop()).toBe(4);
      expect(d.shift()).toBe(3);
      d.unshift(0);
      d.sort();
      d.reverse();
      d.splice(1, 1);
    });
    expect(next).toEqual([2, 0]);
  });
});

describe("configuration", () => {
  test("setAutoFreeze disables freezing of later productions", () => {
    /** Verifies: IMM-CFG-001 */
    setAutoFreeze(false);
    try {
      const next = produce({ a: { b: 1 } }, (d) => {
        d.a.b = 2;
      });
      expect(Object.isFrozen(next)).toBe(false);
      expect(Object.isFrozen(next.a)).toBe(false);
    } finally {
      setAutoFreeze(true);
    }
    expect(Object.isFrozen(produce({ z: 1 }, (d) => void (d.z = 2)))).toBe(true);
  });

  test("loose copying drops non-enumerable own properties and flattens getters", () => {
    /** Verifies: IMM-CFG-002 */
    const base: Record<string, number> = { shown: 1 };
    Object.defineProperty(base, "hidden", {
      value: 1,
      enumerable: false,
      writable: true,
      configurable: true,
    });
    const next = produce(base, (d) => {
      d.shown = 2;
    });
    expect(Object.getOwnPropertyDescriptor(next, "hidden")).toBeUndefined();
    const withGetter = {
      _v: 1,
      get v() {
        return this._v;
      },
    };
    const g = produce(withGetter, (d) => {
      d._v = 2;
    });
    const descriptor = Object.getOwnPropertyDescriptor(g, "v")!;
    expect(descriptor.get).toBeUndefined();
    expect(g.v).toBe(1);
  });

  test("strict copying preserves non-enumerable own properties", () => {
    /** Verifies: IMM-CFG-003 */
    setUseStrictShallowCopy(true);
    try {
      const base: Record<string, number> = { shown: 1 };
      Object.defineProperty(base, "hidden", {
        value: 1,
        enumerable: false,
        writable: true,
        configurable: true,
      });
      const next = produce(base, (d) => {
        d.shown = 2;
      });
      const descriptor = Object.getOwnPropertyDescriptor(next, "hidden")!;
      expect(descriptor.value).toBe(1);
      expect(descriptor.enumerable).toBe(false);
    } finally {
      setUseStrictShallowCopy(false);
    }
  });

  test("class_only strict copying applies to marked classes but not plain objects", () => {
    /** Verifies: IMM-CFG-004 */
    setUseStrictShallowCopy("class_only");
    try {
      class Marked {
        static [immerable] = true;
        shown = 1;
        constructor() {
          Object.defineProperty(this, "hidden", {
            value: 7,
            enumerable: false,
            writable: true,
            configurable: true,
          });
        }
      }
      const nextClass = produce(new Marked(), (d) => {
        d.shown = 2;
      });
      expect(Object.getOwnPropertyDescriptor(nextClass, "hidden")!.value).toBe(7);
      const plain: Record<string, number> = { shown: 1 };
      Object.defineProperty(plain, "hidden", {
        value: 7,
        enumerable: false,
        writable: true,
        configurable: true,
      });
      const nextPlain = produce(plain, (d) => {
        d.shown = 2;
      });
      expect(Object.getOwnPropertyDescriptor(nextPlain, "hidden")).toBeUndefined();
    } finally {
      setUseStrictShallowCopy(false);
    }
  });

  test("an Immer instance isolates autoFreeze from the package-level engine", () => {
    /** Verifies: IMM-CFG-006, IMM-CFG-007 */
    const engine = new Immer({ autoFreeze: false });
    const viaInstance = engine.produce({ a: { b: 1 } }, (d) => {
      d.a.b = 2;
    });
    expect(Object.isFrozen(viaInstance)).toBe(false);
    expect(Object.isFrozen(viaInstance.a)).toBe(false);
    const viaGlobal = produce({ a: { b: 1 } }, (d) => {
      d.a.b = 2;
    });
    expect(Object.isFrozen(viaGlobal)).toBe(true);
  });

  test("an Immer instance exposes the full production surface with its own config", () => {
    /** Verifies: IMM-CFG-006 */
    const engine = new Immer({ autoFreeze: false });
    const [next, patches, inverse] = engine.produceWithPatches({ x: 1 }, (d) => {
      d.x = 2;
    });
    expect(next).toEqual({ x: 2 });
    expect(patches).toEqual([{ op: "replace", path: ["x"], value: 2 }]);
    expect(inverse).toEqual([{ op: "replace", path: ["x"], value: 1 }]);
    expect(Object.isFrozen(next)).toBe(false);
    const applied = engine.applyPatches({ x: 1 }, patches);
    expect(applied).toEqual({ x: 2 });
    expect(Object.isFrozen(applied)).toBe(false);
    const draft = engine.createDraft({ q: 1 });
    draft.q = 3;
    const finished = engine.finishDraft(draft);
    expect(finished).toEqual({ q: 3 });
    expect(Object.isFrozen(finished)).toBe(false);
  });
});
