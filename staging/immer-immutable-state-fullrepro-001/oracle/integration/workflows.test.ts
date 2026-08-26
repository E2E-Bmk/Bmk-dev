// Oracle - integration tests for the immer immutable-state specification (plugins loaded).
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
  freeze,
  nothing,
  immerable,
  setUseStrictShallowCopy,
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
  tags: string[];
}
interface Board {
  todos: Todo[];
  filter: string;
  stats: { open: number };
}

function board(): Board {
  return {
    todos: [
      { title: "write", done: false, tags: ["docs"] },
      { title: "review", done: false, tags: [] },
    ],
    filter: "all",
    stats: { open: 2 },
  };
}

describe("immutable update workflows", () => {
  test("a store evolves through produce steps with sharing preserved at every step", () => {
    const v0 = board();
    const v1 = produce(v0, (d) => {
      d.todos[0]!.done = true;
      d.stats.open = 1;
    });
    const v2 = produce(v1, (d) => {
      d.filter = "open";
    });
    expect(v1.todos[1]).toBe(v0.todos[1]);
    expect(v2.todos).toBe(v1.todos);
    expect(v2.stats).toBe(v1.stats);
    expect(v2.filter).toBe("open");
    expect(v0.filter).toBe("all");
    expect(v0.stats.open).toBe(2);
  });

  test("inverse patches implement undo and forward patches implement redo", () => {
    const v0 = { text: "", cursor: 0 };
    const history: { patches: Patch[]; inverse: Patch[] }[] = [];
    let state = v0;
    for (const edit of ["a", "ab", "abc"]) {
      const [next, patches, inverse] = produceWithPatches(state, (d) => {
        d.text = edit;
        d.cursor = edit.length;
      });
      history.push({ patches: patches as Patch[], inverse: inverse as Patch[] });
      state = next;
    }
    expect(state).toEqual({ text: "abc", cursor: 3 });
    const undone = applyPatches(state, history[2]!.inverse);
    expect(undone).toEqual({ text: "ab", cursor: 2 });
    const redone = applyPatches(undone, history[2]!.patches);
    expect(redone).toEqual(state);
    const backToStart = history
      .slice()
      .reverse()
      .reduce((s, entry) => applyPatches(s, entry.inverse), state);
    expect(backToStart).toEqual(v0);
  });

  test("patch replay composes with an open manual draft", () => {
    const staged: Patch[] = [
      { op: "replace", path: ["n"], value: 5 },
      { op: "add", path: ["log", 0], value: "replayed" },
    ];
    const draft = createDraft({ n: 1, log: [] as string[] });
    applyPatches(draft, staged);
    draft.log.push("manual");
    let reported: Patch[] | undefined;
    const next = finishDraft(draft, (p) => {
      reported = p as Patch[];
    });
    expect(next).toEqual({ n: 5, log: ["replayed", "manual"] });
    expect(applyPatches({ n: 1, log: [] as string[] }, reported!)).toEqual(next);
  });

  test("curried producers drive a reducer loop", () => {
    type CounterState = { count: number; history: number[] };
    const apply = produce((d: CounterState, delta: number) => {
      d.count += delta;
      d.history.push(d.count);
    });
    const final = [1, 2, -1].reduce((s, delta) => apply(s, delta), {
      count: 0,
      history: [] as number[],
    });
    expect(final).toEqual({ count: 2, history: [1, 3, 2] });
    expect(Object.isFrozen(final)).toBe(true);
  });

  test("a marked class graph produces new instances with prototypes and patches intact", () => {
    class Account {
      static [immerable] = true;
      constructor(
        public owner: string,
        public balance: number,
      ) {}
    }
    class Bank {
      static [immerable] = true;
      accounts: Account[] = [];
    }
    const bank = new Bank();
    bank.accounts.push(new Account("a", 10), new Account("b", 20));
    const [next, patches, inverse] = produceWithPatches(bank, (d) => {
      d.accounts[0]!.balance += 5;
    });
    expect(next).toBeInstanceOf(Bank);
    expect(next.accounts[0]).toBeInstanceOf(Account);
    expect(next.accounts[0]!.balance).toBe(15);
    expect(next.accounts[1]).toBe(bank.accounts[1]);
    expect(bank.accounts[0]!.balance).toBe(10);
    expect(applyPatches(bank, patches).accounts[0]!.balance).toBe(15);
    expect(applyPatches(next, inverse).accounts[0]!.balance).toBe(10);
  });

  test("nested containers draft through map values into sets", () => {
    const base = new Map<string, Set<string>>([
      ["read", new Set(["alice"])],
      ["write", new Set()],
    ]);
    const next = produce(base, (d) => {
      d.get("read")!.add("bob");
      d.get("write")!.add("alice");
    });
    expect([...next.get("read")!]).toEqual(["alice", "bob"]);
    expect([...next.get("write")!]).toEqual(["alice"]);
    expect([...base.get("read")!]).toEqual(["alice"]);
    expect(base.get("write")!.size).toBe(0);
  });

  test("array-method mutations are recorded as patches that replay", () => {
    const base = { items: [{ id: 1, qty: 1 }, { id: 2, qty: 2 }, { id: 3, qty: 3 }] };
    const [step1, patches1] = produceWithPatches(base, (d) => {
      d.items.find((it) => it.id === 2)!.qty = 20;
      d.items.push({ id: 4, qty: 4 });
    });
    expect(step1.items.map((i) => i.qty)).toEqual([1, 20, 3, 4]);
    const [step2, patches2] = produceWithPatches(step1, (d) => {
      const heavy = d.items.filter((it) => it.qty >= 3 && it.qty < 10);
      heavy.forEach((it) => {
        it.qty *= 10;
      });
    });
    expect(step2.items.map((i) => i.qty)).toEqual([1, 20, 30, 40]);
    const replayed = applyPatches(applyPatches(base, patches1), patches2);
    expect(replayed).toEqual(step2);
    expect(base.items.map((i) => i.qty)).toEqual([1, 2, 3]);
  });

  test("a nested produce precomputes a branch that outer patches capture", () => {
    const base = { config: { retries: 1 }, data: [1] };
    const [next, patches] = produceWithPatches(base, (d) => {
      d.config = produce(current(d.config), (c) => {
        c.retries = 5;
      });
    });
    expect(next.config.retries).toBe(5);
    expect(next.data).toBe(base.data);
    expect(applyPatches(base, patches)).toEqual(next);
  });

  test("producing nothing round-trips through patches on optional state", () => {
    const session: { user: string } | undefined = { user: "alice" };
    const [next, patches, inverse] = produceWithPatches(session, () => nothing as never);
    expect(next).toBeUndefined();
    expect(applyPatches(session, patches)).toBeUndefined();
    const restored = applyPatches(undefined as unknown as typeof session, inverse);
    expect(restored).toEqual({ user: "alice" });
  });

  test("class_only strict copying differentiates classes from plain objects in one tree", () => {
    setUseStrictShallowCopy("class_only");
    try {
      class Meta {
        static [immerable] = true;
        visible = 1;
        constructor() {
          Object.defineProperty(this, "secret", {
            value: 42,
            enumerable: false,
            writable: true,
            configurable: true,
          });
        }
      }
      const base = { meta: new Meta(), plain: { visible: 1 } as Record<string, number> };
      Object.defineProperty(base.plain, "secret", {
        value: 42,
        enumerable: false,
        writable: true,
        configurable: true,
      });
      const next = produce(base, (d) => {
        d.meta.visible = 2;
        d.plain.visible = 2;
      });
      expect(Object.getOwnPropertyDescriptor(next.meta, "secret")!.value).toBe(42);
      expect(Object.getOwnPropertyDescriptor(next.plain, "secret")).toBeUndefined();
    } finally {
      setUseStrictShallowCopy(false);
    }
  });

  test("manual drafts and producers work independently over one base", () => {
    const base = board();
    const draft = createDraft(base);
    draft.filter = "done";
    const viaProduce = produce(base, (d) => {
      d.stats.open = 0;
    });
    const viaDraft = finishDraft(draft);
    expect(viaDraft.filter).toBe("done");
    expect(viaDraft.stats).toBe(base.stats);
    expect(viaProduce.filter).toBe("all");
    expect(viaProduce.stats.open).toBe(0);
    expect(viaProduce.todos).toBe(base.todos);
    expect(viaDraft.todos).toBe(base.todos);
    expect(base.filter).toBe("all");
    expect(base.stats.open).toBe(2);
  });

  test("a patch log replays onto a diverged base when its paths still resolve", () => {
    const origin = { items: ["a"], count: 1 };
    const [, patches] = produceWithPatches(origin, (d) => {
      d.items.push("b");
      d.count = 2;
    });
    const diverged = { items: ["z"], count: 9, extra: true };
    const merged = applyPatches(diverged, patches);
    expect(merged).toEqual({ items: ["z", "b"], count: 2, extra: true });
    expect(diverged.items).toEqual(["z"]);
  });

  test("primitive set membership flows through snapshots and patches", () => {
    const base = new Set(["read"]);
    const [next, patches, inverse] = produceWithPatches(base, (d) => {
      d.add("write");
      const snap = current(d);
      expect(snap).toBeInstanceOf(Set);
      expect([...snap]).toEqual(["read", "write"]);
      expect(isDraft(snap)).toBe(false);
    });
    expect([...next]).toEqual(["read", "write"]);
    expect([...applyPatches(base, patches)]).toEqual([...next]);
    expect([...applyPatches(next, inverse)]).toEqual([...base]);
  });

  test("a marked class with container fields drafts through both plugins", () => {
    class Registry {
      static [immerable] = true;
      entries = new Map<string, { hits: number }>();
      tags = new Set<string>();
    }
    const base = new Registry();
    base.entries.set("home", { hits: 1 });
    base.tags.add("v1");
    const next = produce(base, (d) => {
      d.entries.get("home")!.hits += 1;
      d.entries.set("about", { hits: 0 });
      d.tags.add("v2");
    });
    expect(next).toBeInstanceOf(Registry);
    expect(next.entries.get("home")!.hits).toBe(2);
    expect([...next.entries.keys()]).toEqual(["home", "about"]);
    expect([...next.tags]).toEqual(["v1", "v2"]);
    expect(base.entries.get("home")!.hits).toBe(1);
    expect(base.entries.has("about")).toBe(false);
    expect([...base.tags]).toEqual(["v1"]);
  });

  test("map productions share untouched values by reference", () => {
    const alpha = { hits: 1 };
    const beta = { hits: 2 };
    const base = new Map([
      ["alpha", alpha],
      ["beta", beta],
    ]);
    const [next, patches] = produceWithPatches(base, (d) => {
      d.get("alpha")!.hits = 10;
    });
    expect(next.get("alpha")).not.toBe(alpha);
    expect(next.get("beta")).toBe(beta);
    expect([...applyPatches(base, patches)]).toEqual([...next]);
  });
});

describe("cross-view invariants", () => {
  test("patches and inverse patches round-trip one mixed production", () => {
    /** Verifies: IMM-CVI-001 */
    const base = {
      list: [1, 2, 3],
      meta: { owner: "a", labels: new Map([["x", 1]]) },
      flags: new Set(["draft"]),
    };
    const [next, patches, inverse] = produceWithPatches(base, (d) => {
      d.list.splice(1, 1);
      d.meta.owner = "b";
      d.meta.labels.set("y", 2);
      d.flags.add("live");
      d.flags.delete("draft");
    });
    const forward = applyPatches(base, patches);
    expect(forward.list).toEqual(next.list);
    expect(forward.meta.owner).toBe(next.meta.owner);
    expect([...forward.meta.labels]).toEqual([...next.meta.labels]);
    expect([...forward.flags]).toEqual([...next.flags]);
    const back = applyPatches(next, inverse);
    expect(back.list).toEqual(base.list);
    expect(back.meta.owner).toBe(base.meta.owner);
    expect([...back.meta.labels]).toEqual([...base.meta.labels]);
    expect([...back.flags]).toEqual([...base.flags]);
  });

  test("mid-recipe snapshots equal the eventual finalization", () => {
    /** Verifies: IMM-CVI-002 */
    const base = board();
    let snapAfterFirst: Board | undefined;
    const afterFirst = produce(base, (d) => {
      d.todos[0]!.done = true;
      snapAfterFirst = current(d) as Board;
    });
    expect(snapAfterFirst).toEqual(afterFirst);
    produce(base, (d) => {
      d.stats.open = 0;
      expect(original(d)).toBe(base);
      expect(current(d).stats.open).toBe(0);
      expect(original(d)!.stats.open).toBe(2);
    });
  });

  test("no effective change means base identity and empty patches in every projection", () => {
    /** Verifies: IMM-CVI-003 */
    const base = board();
    expect(produce(base, () => {})).toBe(base);
    const [same, patches, inverse] = produceWithPatches(base, (d) => {
      void d.todos[0]!.title;
    });
    expect(same).toBe(base);
    expect(patches).toEqual([]);
    expect(inverse).toEqual([]);
    const draft = createDraft(base);
    void draft.filter;
    expect(finishDraft(draft)).toBe(base);
    const curried = produce(() => {});
    expect(curried(base)).toBe(base);
  });

  test("listener streams equal the produceWithPatches triple for a complex change set", () => {
    /** Verifies: IMM-CVI-004 */
    const base = { counts: new Map([["a", 1]]), order: [1, 2] };
    const recipe = (d: { counts: Map<string, number>; order: number[] }) => {
      d.counts.set("b", 2);
      d.order.push(3);
    };
    let listened: [Patch[], Patch[]] | undefined;
    const viaListener = produce(base, recipe, (p, ip) => {
      listened = [p as Patch[], ip as Patch[]];
    });
    const [viaTriple, patches, inverse] = produceWithPatches(base, recipe);
    expect([...viaListener.counts]).toEqual([...viaTriple.counts]);
    expect(viaListener.order).toEqual(viaTriple.order);
    expect(listened![0]).toEqual(patches);
    expect(listened![1]).toEqual(inverse);
  });

  test("freezing follows the finalizing engine's configuration in all projections", () => {
    /** Verifies: IMM-CVI-006 */
    const engine = new Immer({ autoFreeze: false });
    const recipe = (d: { a: { b: number } }) => {
      d.a.b = 2;
    };
    expect(Object.isFrozen(produce({ a: { b: 1 } }, recipe))).toBe(true);
    expect(Object.isFrozen(engine.produce({ a: { b: 1 } }, recipe))).toBe(false);
    const globalDraft = createDraft({ a: { b: 1 } });
    globalDraft.a.b = 2;
    expect(Object.isFrozen(finishDraft(globalDraft))).toBe(true);
    const engineDraft = engine.createDraft({ a: { b: 1 } });
    engineDraft.a.b = 2;
    expect(Object.isFrozen(engine.finishDraft(engineDraft))).toBe(false);
    const patch: Patch[] = [{ op: "replace", path: ["a"], value: { b: 3 } }];
    expect(Object.isFrozen(applyPatches({ a: { b: 1 } }, patch))).toBe(true);
    expect(Object.isFrozen(engine.applyPatches({ a: { b: 1 } }, patch))).toBe(false);
  });

  test("no live drafts leak into results, snapshots, or patch values", () => {
    /** Verifies: IMM-CVI-007 */
    const base = { arr: [{ v: 1 }], obj: { k: { deep: 1 } } };
    let snapshot: typeof base | undefined;
    const [next, patches] = produceWithPatches(base, (d) => {
      d.arr.push({ v: 2 });
      d.obj.k.deep = 9;
      snapshot = current(d) as typeof base;
    });
    const walk = (value: unknown): boolean => {
      if (isDraft(value)) return false;
      if (value && typeof value === "object") {
        return Object.values(value).every(walk);
      }
      return true;
    };
    expect(walk(next)).toBe(true);
    expect(walk(snapshot)).toBe(true);
    expect(patches.every((p) => walk((p as Patch).value))).toBe(true);
  });
});

describe("end to end", () => {
  test("a document editing session with staged patches, undo, and redo", () => {
    const empty = { title: "", body: [] as string[], saved: false };
    const draft = createDraft(empty);
    draft.title = "Notes";
    draft.body.push("first line");
    let sessionPatches: Patch[] | undefined;
    let sessionInverse: Patch[] | undefined;
    const v1 = finishDraft(draft, (p, ip) => {
      sessionPatches = p as Patch[];
      sessionInverse = ip as Patch[];
    });
    expect(v1).toEqual({ title: "Notes", body: ["first line"], saved: false });
    expect(() => void draft.title).toThrow();
    const [v2, savePatches, saveInverse] = produceWithPatches(v1, (d) => {
      d.saved = true;
      d.body.push("second line");
    });
    const undone = applyPatches(v2, saveInverse);
    expect(undone).toEqual(v1);
    const redone = applyPatches(undone, savePatches);
    expect(redone).toEqual(v2);
    const replayedFromEmpty = applyPatches(applyPatches(empty, sessionPatches!), savePatches);
    expect(replayedFromEmpty).toEqual(v2);
    expect(applyPatches(v1, sessionInverse!)).toEqual(empty);
  });

  test("a mixed-container store replays its full patch log onto the original base", () => {
    class Session {
      static [immerable] = true;
      constructor(public user: string) {}
    }
    const base = {
      users: new Map([["u1", { name: "alice", roles: new Set(["reader"]) }]]),
      log: [] as string[],
      session: new Session("nobody"),
    };
    const log: Patch[] = [];
    const step1 = produce(
      base,
      (d) => {
        d.users.get("u1")!.roles.add("writer");
        d.log.push("granted writer");
      },
      (p) => log.push(...(p as Patch[])),
    );
    const step2 = produce(
      step1,
      (d) => {
        d.users.set("u2", { name: "bob", roles: new Set() });
        d.session.user = "alice";
      },
      (p) => log.push(...(p as Patch[])),
    );
    const step3 = produce(
      step2,
      (d) => {
        d.log.push("session started");
      },
      (p) => log.push(...(p as Patch[])),
    );
    const replayed = applyPatches(base, log);
    expect([...replayed.users.keys()]).toEqual([...step3.users.keys()]);
    expect([...replayed.users.get("u1")!.roles]).toEqual([...step3.users.get("u1")!.roles]);
    expect(replayed.log).toEqual(step3.log);
    expect(replayed.session).toBeInstanceOf(Session);
    expect(replayed.session.user).toBe("alice");
    expect(base.log).toEqual([]);
    expect(base.session.user).toBe("nobody");
  });

  test("two engines process one base with configuration-scoped results that interoperate", () => {
    const relaxed = new Immer({ autoFreeze: false });
    const base = freeze({ items: [{ sku: "a", qty: 1 }], total: 1 }, true);
    const [viaRelaxed, relaxedPatches] = relaxed.produceWithPatches(base, (d) => {
      d.items.push({ sku: "b", qty: 2 });
      d.total = 3;
    });
    const viaGlobal = produce(base, (d) => {
      d.items.push({ sku: "b", qty: 2 });
      d.total = 3;
    });
    expect(viaRelaxed).toEqual(viaGlobal);
    expect(Object.isFrozen(viaRelaxed)).toBe(false);
    expect(Object.isFrozen(viaGlobal)).toBe(true);
    const replayed = applyPatches(base, relaxedPatches);
    expect(replayed).toEqual(viaGlobal);
    expect(Object.isFrozen(replayed)).toBe(true);
    expect(base.items).toHaveLength(1);
  });
});
