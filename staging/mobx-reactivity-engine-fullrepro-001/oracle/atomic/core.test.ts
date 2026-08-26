// Spec2Repo oracle - atomic tests for mobx-reactivity-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  observable, ObservableMap, ObservableSet,
  makeObservable, makeAutoObservable,
  observableRef, observableShallow, observableStruct,
  computed, computedStruct,
  action, actionBound, runInAction, transaction, untracked,
  autorun, reaction, when,
  observe, intercept,
  onBecomeObserved, onBecomeUnobserved,
  configure,
  toJS, keys, values, entries, get, set, has, remove,
  compareDefault, compareIdentity, compareShallow, compareStructural,
  isObservable, isObservableObject, isObservableArray, isObservableMap,
  isObservableSet, isBoxedObservable, isObservableProp, isComputedProp,
  isAction, isComputed,
} from "mobx";

configure({ enforceActions: "never" });

describe("observable state", () => {
  test("a plain object converts to a new observable proxy reference", () => {
    /** Verifies: MOBX-OBS-001 */
    const plain = { grain: 12, silo: "east" };
    const obs = observable(plain);
    expect(obs).not.toBe(plain);
    expect(isObservableObject(obs)).toBe(true);
    expect(isObservable(obs)).toBe(true);
    expect(obs.grain).toBe(12);
    expect(isObservableProp(obs, "grain")).toBe(true);
  });

  test("arrays convert to observable arrays that are still real arrays", () => {
    /** Verifies: MOBX-OBS-001 */
    const arr = observable([4, 9]);
    expect(isObservableArray(arr)).toBe(true);
    expect(Array.isArray(arr)).toBe(true);
    expect(arr.length).toBe(2);
  });

  test("maps and sets convert without being instanceof the built-ins", () => {
    /** Verifies: MOBX-OBS-001 */
    const m = observable(new Map([["dock", 3]]));
    const s = observable(new Set([7]));
    expect(isObservableMap(m)).toBe(true);
    expect(isObservableSet(s)).toBe(true);
    expect(m instanceof Map).toBe(false);
    expect(s instanceof Set).toBe(false);
    expect(m.get("dock")).toBe(3);
    expect(s.has(7)).toBe(true);
  });

  test("primitives convert to boxed observables", () => {
    /** Verifies: MOBX-OBS-001 */
    const n = observable(41 as any);
    const t = observable("pier" as any);
    expect(isBoxedObservable(n)).toBe(true);
    expect(isBoxedObservable(t)).toBe(true);
    expect((n as any).get()).toBe(41);
    expect((t as any).get()).toBe("pier");
  });

  test("explicit factory forms and collection constructors agree with the predicates", () => {
    /** Verifies: MOBX-OBS-001 */
    expect(isObservableObject(observable.object({ a: 1 }))).toBe(true);
    expect(isObservableArray(observable.array([1]))).toBe(true);
    expect(isObservableMap(observable.map({ a: 1 }))).toBe(true);
    expect(isObservableSet(observable.set([1]))).toBe(true);
    expect(isBoxedObservable(observable.box(5))).toBe(true);
    const m = new ObservableMap([["quay", 2]]);
    const s = new ObservableSet([8]);
    expect(isObservableMap(m)).toBe(true);
    expect(isObservableSet(s)).toBe(true);
    expect(m.get("quay")).toBe(2);
    expect(s.has(8)).toBe(true);
  });

  test("conversion is deep by default", () => {
    /** Verifies: MOBX-OBS-002 */
    const o = observable({ hold: { crates: [{ mass: 3 }] } });
    expect(isObservableObject(o.hold)).toBe(true);
    expect(isObservableArray(o.hold.crates)).toBe(true);
    expect(isObservableObject(o.hold.crates[0])).toBe(true);
    o.hold = { crates: [] } as any;
    expect(isObservableObject(o.hold)).toBe(true);
  });

  test("deep false keeps stored values unconverted", () => {
    /** Verifies: MOBX-OBS-002 */
    const arr = observable([{ raw: 1 }], { deep: false });
    expect(isObservableArray(arr)).toBe(true);
    expect(isObservable(arr[0])).toBe(false);
    const o = observable({ inner: { raw: 2 } }, {}, { deep: false });
    expect(isObservable(o.inner)).toBe(false);
  });

  test("a box tracks reads and an equals comparer suppresses equal sets", () => {
    /** Verifies: MOBX-OBS-003 */
    const b = observable.box({ depth: 4 }, { equals: compareStructural });
    let runs = 0;
    const stop = autorun(() => { b.get(); runs++; });
    expect(runs).toBe(1);
    b.set({ depth: 4 });
    expect(runs).toBe(1);
    b.set({ depth: 5 });
    expect(runs).toBe(2);
    stop();
  });

  test("adding a property by assignment is an observable structure change", () => {
    /** Verifies: MOBX-OBS-004 */
    const o = observable({ first: 1 } as Record<string, number>);
    const snapshots: string[] = [];
    const stop = autorun(() => snapshots.push(keys(o).join(",")));
    o.second = 2;
    expect(isObservableProp(o, "second")).toBe(true);
    expect(snapshots).toEqual(["first", "first,second"]);
    stop();
  });

  test("the delete keyword removes a property reactively", () => {
    /** Verifies: MOBX-OBS-004 */
    const o = observable({ keep: 1, drop: 2 } as Record<string, number>);
    const counts: number[] = [];
    const stop = autorun(() => counts.push(keys(o).length));
    delete o.drop;
    expect(counts).toEqual([2, 1]);
    expect(toJS(o)).toEqual({ keep: 1 });
    stop();
  });

  test("a same-value write does not propagate", () => {
    /** Verifies: MOBX-OBS-006 */
    const o = observable({ berth: 6 });
    let runs = 0;
    const stop = autorun(() => { o.berth; runs++; });
    o.berth = 6;
    expect(runs).toBe(1);
    o.berth = 7;
    expect(runs).toBe(2);
    stop();
  });

  test("JSON serialization matches the plain counterpart", () => {
    /** Verifies: MOBX-OBS-006 */
    const plain = { rows: [1, 2], label: "ledge" };
    const obs = observable(plain);
    expect(JSON.stringify(obs)).toBe(JSON.stringify(plain));
  });

  test("isObservableProp distinguishes observable members from plain ones", () => {
    /** Verifies: MOBX-OBS-005 */
    expect(isObservableProp({ a: 1 }, "a")).toBe(false);
    expect(isObservableProp(observable({ a: 1 }), "a")).toBe(true);
  });
});

describe("class annotations", () => {
  test("makeObservable wires fields, getters and methods per the annotation map", () => {
    /** Verifies: MOBX-ANN-001 */
    class Kiln {
      temp = 100;
      fuel = 2;
      constructor() {
        makeObservable(this, { temp: observable, fuel: observable, heatIndex: computed, stoke: action });
      }
      get heatIndex() { return this.temp * this.fuel; }
      stoke(n: number) { this.temp += n; }
    }
    const k = new Kiln();
    expect(isObservableProp(k, "temp")).toBe(true);
    expect(isComputedProp(k, "heatIndex")).toBe(true);
    expect(isAction(k.stoke)).toBe(true);
    const seen: number[] = [];
    const stop = autorun(() => seen.push(k.heatIndex));
    k.stoke(50);
    expect(seen).toEqual([200, 300]);
    stop();
  });

  test("observableRef tracks reassignment only and never converts the value", () => {
    /** Verifies: MOBX-ANN-001 */
    class Holder {
      payload: any = { nested: { v: 1 } };
      constructor() { makeObservable(this, { payload: observableRef }); }
    }
    const h = new Holder();
    expect(isObservable(h.payload)).toBe(false);
    let runs = 0;
    const stop = autorun(() => { h.payload; runs++; });
    h.payload.nested.v = 2;
    expect(runs).toBe(1);
    runInAction(() => (h.payload = { nested: { v: 3 } }));
    expect(runs).toBe(2);
    stop();
  });

  test("observableShallow converts one level only", () => {
    /** Verifies: MOBX-ANN-001 */
    class Rack {
      slots: any[] = [{ id: 1 }];
      constructor() { makeObservable(this, { slots: observableShallow }); }
    }
    const r = new Rack();
    expect(isObservableArray(r.slots)).toBe(true);
    expect(isObservable(r.slots[0])).toBe(false);
  });

  test("observableStruct suppresses structurally equal reassignment", () => {
    /** Verifies: MOBX-ANN-001 */
    class Marker {
      point = { x: 2, y: 3 };
      constructor() { makeObservable(this, { point: observableStruct }); }
    }
    const m = new Marker();
    let runs = 0;
    const stop = autorun(() => { m.point; runs++; });
    runInAction(() => (m.point = { x: 2, y: 3 }));
    expect(runs).toBe(1);
    runInAction(() => (m.point = { x: 9, y: 3 }));
    expect(runs).toBe(2);
    stop();
  });

  test("makeAutoObservable infers members and honors false overrides", () => {
    /** Verifies: MOBX-ANN-002 */
    class Vault {
      coins = 5;
      tag = "brass";
      constructor() { makeAutoObservable(this, { tag: false }); }
      get doubled() { return this.coins * 2; }
      deposit(n: number) { this.coins += n; }
    }
    const v = new Vault();
    expect(isObservableProp(v, "coins")).toBe(true);
    expect(isComputedProp(v, "doubled")).toBe(true);
    expect(isAction(v.deposit)).toBe(true);
    expect(isObservableProp(v, "tag")).toBe(false);
  });

  test("makeAutoObservable rejects classes with a superclass", () => {
    /** Verifies: MOBX-ANN-003, MOBX-ERR-002 */
    class Root {}
    class Leaf extends Root {
      x = 1;
      constructor() { super(); makeAutoObservable(this); }
    }
    expect(() => new Leaf()).toThrowError(Error);
  });

  test("actionBound methods survive detachment while plain action methods do not", () => {
    /** Verifies: MOBX-ANN-004 */
    class Pump {
      flow = 3;
      constructor() { makeObservable(this, { flow: observable, boost: actionBound, leakUnbound: action }); }
      boost() { this.flow *= 2; }
      leakUnbound() { return this.flow; }
    }
    const p = new Pump();
    const detached = p.boost;
    detached();
    expect(p.flow).toBe(6);
    const loose = p.leakUnbound;
    expect(() => loose.call(undefined)).toThrowError(TypeError);
  });

  test("a getter in an observable literal becomes computed", () => {
    /** Verifies: MOBX-ANN-005 */
    const order = observable({
      qty: 3,
      unit: 7,
      get total() { return this.qty * this.unit; },
    });
    expect(isComputedProp(order, "total")).toBe(true);
    const seen: number[] = [];
    const stop = autorun(() => seen.push(order.total));
    order.qty = 4;
    expect(seen).toEqual([21, 28]);
    stop();
  });

  test("annotating a missing field or re-annotating an annotated member throws", () => {
    /** Verifies: MOBX-ANN-006, MOBX-ERR-002 */
    class Ghost {
      constructor() { makeObservable(this, { phantom: observable } as any); }
    }
    expect(() => new Ghost()).toThrowError(Error);
    class Twice {
      z = 1;
      constructor() {
        makeObservable(this, { z: observable });
        makeObservable(this, { z: observable });
      }
    }
    expect(() => new Twice()).toThrowError(Error);
  });
});

describe("derived values", () => {
  test("a computed is lazy until first read", () => {
    /** Verifies: MOBX-CMP-002 */
    const src = observable({ n: 5 });
    let evals = 0;
    const c = computed(() => { evals++; return src.n + 1; });
    expect(evals).toBe(0);
    expect(c.get()).toBe(6);
    expect(evals).toBe(1);
    expect(isComputed(c)).toBe(true);
  });

  test("while observed a computed caches between dependency changes", () => {
    /** Verifies: MOBX-CMP-002 */
    const src = observable({ qty: 2, unit: 30 });
    let evals = 0;
    const price = computed(() => { evals++; return src.qty * src.unit; });
    const stop = autorun(() => price.get());
    expect(evals).toBe(1);
    price.get();
    price.get();
    expect(evals).toBe(1);
    src.qty = 3;
    expect(evals).toBe(2);
    expect(price.get()).toBe(90);
    expect(evals).toBe(2);
    stop();
  });

  test("while unobserved a computed evaluates on every read", () => {
    /** Verifies: MOBX-CMP-002 */
    const src = observable({ n: 1 });
    let evals = 0;
    const c = computed(() => { evals++; return src.n; });
    c.get();
    c.get();
    expect(evals).toBe(2);
  });

  test("a computed equals option cuts off propagation", () => {
    /** Verifies: MOBX-CMP-003 */
    const src = observable({ w: 1, tag: "x" });
    const dims = computed(() => ({ w: src.w }), { equals: compareStructural });
    let effectRuns = 0;
    const stop = autorun(() => { dims.get(); effectRuns++; });
    runInAction(() => (src.tag = "y"));
    expect(effectRuns).toBe(1);
    runInAction(() => (src.w = 2));
    expect(effectRuns).toBe(2);
    stop();
  });

  test("the four comparers implement their documented equality", () => {
    /** Verifies: MOBX-CMP-003 */
    expect(compareDefault(NaN, NaN)).toBe(true);
    expect(compareDefault({ a: 1 }, { a: 1 })).toBe(false);
    expect(compareIdentity(3, 3)).toBe(true);
    const same = { z: 1 };
    expect(compareIdentity(same, same)).toBe(true);
    expect(compareShallow({ a: 1, b: 2 }, { a: 1, b: 2 })).toBe(true);
    expect(compareShallow({ a: {} }, { a: {} })).toBe(false);
    expect(compareStructural({ a: [1, { b: 2 }] }, { a: [1, { b: 2 }] })).toBe(true);
    expect(compareStructural({ a: [1] }, { a: [2] })).toBe(false);
  });

  test("computedStruct compares results structurally in a class", () => {
    /** Verifies: MOBX-CMP-003, MOBX-ANN-001 */
    class Grid {
      cols = 2;
      rows = 3;
      pad = 0;
      constructor() { makeObservable(this, { cols: observable, rows: observable, pad: observable, shape: computedStruct }); }
      get shape() { return { c: this.cols, r: this.rows }; }
    }
    const g = new Grid();
    let runs = 0;
    const stop = autorun(() => { g.shape; runs++; });
    runInAction(() => (g.pad = 5));
    expect(runs).toBe(1);
    runInAction(() => (g.cols = 4));
    expect(runs).toBe(2);
    stop();
  });

  test("a computed cycle raises an error at read", () => {
    /** Verifies: MOBX-CMP-004, MOBX-ERR-001 */
    const selfRef: any = computed(() => selfRef.get() + 1);
    expect(() => selfRef.get()).toThrowError(/cycle/i);
  });

  test("untracked reads do not create dependencies", () => {
    /** Verifies: MOBX-CMP-005 */
    const o = observable({ hot: 1, cold: 10 });
    let runs = 0;
    const pairs: number[][] = [];
    const stop = autorun(() => { runs++; pairs.push([o.hot, untracked(() => o.cold)]); });
    runInAction(() => (o.cold = 20));
    expect(runs).toBe(1);
    runInAction(() => (o.hot = 2));
    expect(runs).toBe(2);
    expect(pairs).toEqual([[1, 10], [2, 20]]);
    stop();
  });
});

describe("effects", () => {
  test("autorun runs immediately exactly once", () => {
    /** Verifies: MOBX-EFF-001 */
    const o = observable({ v: 3 });
    const seen: number[] = [];
    const stop = autorun(() => seen.push(o.v));
    expect(seen).toEqual([3]);
    stop();
  });

  test("autorun re-runs on tracked changes and ignores untracked properties", () => {
    /** Verifies: MOBX-EFF-001, MOBX-EFF-004 */
    const o = observable({ used: 1, ignored: 100 });
    let runs = 0;
    const stop = autorun(() => { o.used; runs++; });
    o.ignored = 200;
    expect(runs).toBe(1);
    o.used = 2;
    expect(runs).toBe(2);
    stop();
  });

  test("autorun re-records dependencies from scratch on each run", () => {
    /** Verifies: MOBX-EFF-001 */
    const o = observable({ useLeft: true, left: 1, right: 100 });
    let runs = 0;
    const stop = autorun(() => { runs++; o.useLeft ? o.left : o.right; });
    o.right = 101;
    expect(runs).toBe(1);
    o.useLeft = false;
    expect(runs).toBe(2);
    o.left = 2;
    expect(runs).toBe(2);
    o.right = 102;
    expect(runs).toBe(3);
    stop();
  });

  test("a disposed autorun never runs again", () => {
    /** Verifies: MOBX-EFF-001, MOBX-EFF-004, MOBX-ERR-004 */
    const o = observable({ v: 1 });
    let runs = 0;
    const stop = autorun(() => { o.v; runs++; });
    stop();
    stop();
    o.v = 2;
    expect(runs).toBe(1);
  });

  test("reaction skips the initial run and passes new and old values", () => {
    /** Verifies: MOBX-EFF-002 */
    const o = observable({ level: 5, noise: 1 });
    const calls: number[][] = [];
    const stop = reaction(() => o.level, (nv: number, ov: number) => calls.push([nv, ov]));
    expect(calls).toEqual([]);
    o.level = 8;
    expect(calls).toEqual([[8, 5]]);
    o.noise = 2;
    expect(calls.length).toBe(1);
    stop();
  });

  test("fireImmediately runs the effect once with undefined as the previous value", () => {
    /** Verifies: MOBX-EFF-002 */
    const o = observable({ level: 4 });
    const calls: any[][] = [];
    const stop = reaction(() => o.level, (nv: number, ov: any) => calls.push([nv, ov]), { fireImmediately: true });
    expect(calls).toEqual([[4, undefined]]);
    stop();
  });

  test("the reaction handle disposes from inside the effect", () => {
    /** Verifies: MOBX-EFF-002 */
    const b = observable.box(0);
    const log: number[] = [];
    reaction(() => b.get(), (nv: number, _ov: number, r: any) => {
      log.push(nv);
      if (nv >= 2) r.dispose();
    });
    b.set(1);
    b.set(2);
    b.set(3);
    expect(log).toEqual([1, 2]);
  });

  test("a reaction equals option compares expression results", () => {
    /** Verifies: MOBX-EFF-002 */
    const o = observable({ p: { x: 1 } });
    let runs = 0;
    const stop = reaction(() => ({ x: o.p.x }), () => runs++, { equals: compareStructural });
    o.p = { x: 1 } as any;
    expect(runs).toBe(0);
    o.p = { x: 2 } as any;
    expect(runs).toBe(1);
    stop();
  });

  test("when runs its effect exactly once and then disposes", () => {
    /** Verifies: MOBX-EFF-003 */
    const gate = observable({ open: false });
    let fired = 0;
    when(() => gate.open, () => fired++);
    gate.open = true;
    expect(fired).toBe(1);
    gate.open = false;
    gate.open = true;
    expect(fired).toBe(1);
  });

  test("the when promise resolves when the predicate turns true", async () => {
    /** Verifies: MOBX-EFF-003 */
    const gate = observable({ ready: false });
    const p = when(() => gate.ready);
    expect(typeof (p as any).cancel).toBe("function");
    gate.ready = true;
    await p;
    expect(gate.ready).toBe(true);
  });

  test("cancelling a when promise rejects with WHEN_CANCELLED", async () => {
    /** Verifies: MOBX-EFF-003, MOBX-ERR-003 */
    const gate = observable({ ready: false });
    const p = when(() => gate.ready);
    (p as any).cancel();
    await expect(p).rejects.toThrowError(/WHEN_CANCELLED/);
  });
});

describe("actions and batching", () => {
  test("an action batches several writes into one effect run", () => {
    /** Verifies: MOBX-ACT-001 */
    const o = observable({ a: 1, b: 2 });
    const sums: number[] = [];
    const stop = autorun(() => sums.push(o.a + o.b));
    const shift = action(() => { o.a += 10; o.b += 10; });
    shift();
    expect(sums).toEqual([3, 23]);
    stop();
  });

  test("unbatched writes propagate at each statement", () => {
    /** Verifies: MOBX-ACT-001 */
    const o = observable({ a: 1, b: 2 });
    const sums: number[] = [];
    const stop = autorun(() => sums.push(o.a + o.b));
    o.a += 1;
    o.b += 1;
    expect(sums).toEqual([3, 4, 5]);
    stop();
  });

  test("runInAction executes immediately, batches and returns the result", () => {
    /** Verifies: MOBX-ACT-002, MOBX-ACT-001 */
    const o = observable({ x: 1, y: 1 });
    let runs = 0;
    const stop = autorun(() => { o.x + o.y; runs++; });
    const out = runInAction(() => { o.x = 5; o.y = 6; return o.x * o.y; });
    expect(out).toBe(30);
    expect(runs).toBe(2);
    stop();
  });

  test("transaction batches without marking the function as an action", () => {
    /** Verifies: MOBX-ACT-002 */
    const o = observable({ x: 1, y: 1 });
    let runs = 0;
    const stop = autorun(() => { o.x + o.y; runs++; });
    transaction(() => { o.x = 2; o.y = 3; });
    expect(runs).toBe(2);
    stop();
  });

  test("nested actions flush once at the outermost end", () => {
    /** Verifies: MOBX-ACT-001 */
    const o = observable({ v: 0 });
    const seen: number[] = [];
    const stop = autorun(() => seen.push(o.v));
    const inner = action(() => { o.v += 1; });
    const outer = action(() => { inner(); inner(); o.v += 10; });
    outer();
    expect(seen).toEqual([0, 12]);
    stop();
  });

  test("a net-reverted change suppresses reactions but re-runs autorun", () => {
    /** Verifies: MOBX-ACT-001 */
    const o = observable({ v: 10 });
    let reactionRuns = 0;
    let autorunRuns = 0;
    const s1 = reaction(() => o.v, () => reactionRuns++);
    const s2 = autorun(() => { o.v; autorunRuns++; });
    runInAction(() => { o.v = 99; o.v = 10; });
    expect(reactionRuns).toBe(0);
    expect(autorunRuns).toBe(2);
    s1();
    s2();
  });

  test("isAction distinguishes wrapped functions and names them", () => {
    /** Verifies: MOBX-ACT-002 */
    const wrapped = action(() => {});
    const named = action("refuel", () => {});
    expect(isAction(wrapped)).toBe(true);
    expect(isAction(() => {})).toBe(false);
    expect(named.name).toBe("refuel");
  });

  test("an enforceActions violation warns and still applies the write", () => {
    /** Verifies: MOBX-ACT-003, MOBX-ERR-004 */
    configure({ enforceActions: "always" });
    try {
      const o = observable({ q: 1 });
      const warnings: string[] = [];
      const original = console.warn;
      console.warn = (msg: any) => { warnings.push(String(msg)); };
      o.q = 2;
      console.warn = original;
      expect(o.q).toBe(2);
      expect(warnings.length).toBe(1);
      expect(warnings[0]).toMatch(/action/i);
      runInAction(() => (o.q = 3));
      expect(o.q).toBe(3);
    } finally {
      configure({ enforceActions: "never" });
    }
  });
});

describe("collections", () => {
  test("array index writes and length are tracked", () => {
    /** Verifies: MOBX-COL-001 */
    const arr = observable([3, 1]);
    const lens: number[] = [];
    const stop = autorun(() => lens.push(arr.length));
    arr.push(2);
    expect(lens).toEqual([2, 3]);
    arr[0] = 30;
    expect(arr.slice()).toEqual([30, 1, 2]);
    stop();
  });

  test("out-of-bounds reads return undefined and writes extend the array", () => {
    /** Verifies: MOBX-COL-001 */
    const arr = observable([1, 2]);
    expect(arr[9]).toBeUndefined();
    arr[4] = 9;
    expect(arr.length).toBe(5);
    expect(arr[3]).toBeUndefined();
    expect(arr[4]).toBe(9);
  });

  test("array search results are tracked", () => {
    /** Verifies: MOBX-COL-001 */
    const arr = observable([5, 6, 7]);
    const finds: boolean[] = [];
    const stop = autorun(() => finds.push(arr.includes(6)));
    arr.remove(6);
    expect(finds).toEqual([true, false]);
    stop();
  });

  test("replace, remove, clear and splice return their documented values", () => {
    /** Verifies: MOBX-COL-002 */
    const arr = observable([7, 8, 9]);
    arr.replace([4, 5]);
    expect(arr.slice()).toEqual([4, 5]);
    expect(arr.remove(5)).toBe(true);
    expect(arr.remove(99)).toBe(false);
    const gone = arr.splice(0, 1, 6, 7);
    expect(gone).toEqual([4]);
    expect(arr.slice()).toEqual([6, 7]);
    expect(arr.clear()).toEqual([6, 7]);
    expect(arr.length).toBe(0);
  });

  test("map reads and size are tracked with Map semantics", () => {
    /** Verifies: MOBX-COL-003 */
    const m = observable.map({ ore: 4 });
    const sizes: number[] = [];
    const stop = autorun(() => sizes.push(m.size));
    m.set("coal", 2);
    m.delete("ore");
    expect(sizes).toEqual([1, 2, 1]);
    expect(m.get("coal")).toBe(2);
    expect(m.has("ore")).toBe(false);
    stop();
  });

  test("map merge, replace and toJSON operate on entries", () => {
    /** Verifies: MOBX-COL-003 */
    const m = observable.map({ a: 1 });
    m.merge({ b: 2, c: 3 });
    expect(m.size).toBe(3);
    expect(m.toJSON()).toEqual([["a", 1], ["b", 2], ["c", 3]]);
    m.replace({ z: 9 });
    expect([...m.entries()]).toEqual([["z", 9]]);
  });

  test("a has reader re-runs when the missing key appears", () => {
    /** Verifies: MOBX-COL-003 */
    const m = observable.map({ present: 1 });
    const answers: boolean[] = [];
    const stop = autorun(() => answers.push(m.has("waited")));
    m.set("waited", 5);
    expect(answers).toEqual([false, true]);
    stop();
  });

  test("map iteration readers re-run on structural change", () => {
    /** Verifies: MOBX-COL-003 */
    const m = observable.map({ x: 1 });
    const joined: string[] = [];
    const stop = autorun(() => joined.push([...m.values()].join(",")));
    m.set("y", 2);
    expect(joined).toEqual(["1", "1,2"]);
    stop();
  });

  test("sets track membership and re-adding a present element is not a change", () => {
    /** Verifies: MOBX-COL-004 */
    const s = observable.set([1, 2]);
    let runs = 0;
    const stop = autorun(() => { s.size; runs++; });
    s.add(2);
    expect(runs).toBe(1);
    s.add(3);
    expect(runs).toBe(2);
    s.delete(1);
    expect(runs).toBe(3);
    expect([...s]).toEqual([2, 3]);
    stop();
  });

  test("the generic collection API operates uniformly on objects", () => {
    /** Verifies: MOBX-COL-005 */
    const o = observable({ tin: 3 } as Record<string, number>);
    set(o, "zinc", 5);
    expect(keys(o)).toEqual(["tin", "zinc"]);
    expect(values(o)).toEqual([3, 5]);
    expect(entries(o)).toEqual([["tin", 3], ["zinc", 5]]);
    expect(get(o, "zinc")).toBe(5);
    expect(get(o, "gold")).toBeUndefined();
    expect(has(o, "tin")).toBe(true);
    expect(has(o, "gold")).toBe(false);
    remove(o, "tin");
    expect(keys(o)).toEqual(["zinc"]);
  });

  test("the generic collection API reaches arrays and maps too", () => {
    /** Verifies: MOBX-COL-005 */
    const arr = observable([10, 11]);
    expect(get(arr, 1)).toBe(11);
    expect(has(arr, 0)).toBe(true);
    expect(has(arr, 9)).toBe(false);
    set(arr, 0, 99);
    expect(arr.slice()).toEqual([99, 11]);
    const m = observable.map({ k: 1 });
    expect(get(m, "k")).toBe(1);
    expect(keys(m)).toEqual(["k"]);
    set(m, "j", 2);
    expect(m.get("j")).toBe(2);
  });

  test("a keys reader tracks structure changes", () => {
    /** Verifies: MOBX-COL-005, MOBX-OBS-004 */
    const o = observable({ one: 1 } as Record<string, number>);
    let runs = 0;
    const stop = autorun(() => { keys(o); runs++; });
    set(o, "two", 2);
    expect(runs).toBe(2);
    remove(o, "one");
    expect(runs).toBe(3);
    stop();
  });
});

describe("mutation events and interception", () => {
  test("object observers see update, add and remove events with their fields", () => {
    /** Verifies: MOBX-EVT-001 */
    const o = observable({ k: 1 } as Record<string, number>);
    const ev: any[] = [];
    const stop = observe(o, (c: any) => ev.push({ type: c.type, name: c.name, newValue: c.newValue, oldValue: c.oldValue, sameTarget: c.object === o }));
    o.k = 2;
    set(o, "fresh", 9);
    remove(o, "k");
    expect(ev).toEqual([
      { type: "update", name: "k", newValue: 2, oldValue: 1, sameTarget: true },
      { type: "add", name: "fresh", newValue: 9, oldValue: undefined, sameTarget: true },
      { type: "remove", name: "k", newValue: undefined, oldValue: 2, sameTarget: true },
    ]);
    stop();
  });

  test("array observers see update and splice events", () => {
    /** Verifies: MOBX-EVT-001 */
    const arr = observable([1, 2]);
    const ev: any[] = [];
    const stop = observe(arr, (c: any) => {
      if (c.type === "splice") ev.push({ type: c.type, index: c.index, added: [...c.added], removed: [...c.removed] });
      else ev.push({ type: c.type, index: c.index, newValue: c.newValue, oldValue: c.oldValue });
    });
    arr.push(3);
    arr[0] = 10;
    arr.splice(1, 1);
    expect(ev).toEqual([
      { type: "splice", index: 2, added: [3], removed: [] },
      { type: "update", index: 0, newValue: 10, oldValue: 1 },
      { type: "splice", index: 1, added: [], removed: [2] },
    ]);
    stop();
  });

  test("map observers see add, update and delete events", () => {
    /** Verifies: MOBX-EVT-001 */
    const m = observable.map({ a: 1 });
    const ev: any[] = [];
    const stop = observe(m, (c: any) => ev.push({ type: c.type, name: c.name, newValue: c.newValue, oldValue: c.oldValue }));
    m.set("b", 2);
    m.set("a", 5);
    m.delete("b");
    expect(ev).toEqual([
      { type: "add", name: "b", newValue: 2, oldValue: undefined },
      { type: "update", name: "a", newValue: 5, oldValue: 1 },
      { type: "delete", name: "b", newValue: undefined, oldValue: 2 },
    ]);
    stop();
  });

  test("set observers see add and delete events", () => {
    /** Verifies: MOBX-EVT-001 */
    const s = observable.set([1]);
    const ev: any[] = [];
    const stop = observe(s, (c: any) => ev.push({ type: c.type, newValue: c.newValue, oldValue: c.oldValue }));
    s.add(2);
    s.delete(1);
    s.add(2);
    expect(ev).toEqual([
      { type: "add", newValue: 2, oldValue: undefined },
      { type: "delete", newValue: undefined, oldValue: 1 },
    ]);
    stop();
  });

  test("box observers see update events", () => {
    /** Verifies: MOBX-EVT-001 */
    const b = observable.box(10);
    const ev: any[] = [];
    const stop = observe(b, (c: any) => ev.push({ type: c.type, newValue: c.newValue, oldValue: c.oldValue }));
    b.set(20);
    expect(ev).toEqual([{ type: "update", newValue: 20, oldValue: 10 }]);
    stop();
  });

  test("a property observer fires only for its property", () => {
    /** Verifies: MOBX-EVT-002 */
    const o = observable({ p: 1, q: 2 });
    const ev: any[] = [];
    const stop = observe(o, "p", (c: any) => ev.push([c.type, c.oldValue, c.newValue]));
    o.p = 10;
    o.q = 20;
    expect(ev).toEqual([["update", 1, 10]]);
    stop();
  });

  test("an interceptor veto leaves no trace", () => {
    /** Verifies: MOBX-EVT-003, MOBX-INV-003 */
    const o = observable({ speed: 10 });
    let runs = 0;
    const events: any[] = [];
    const s1 = autorun(() => { o.speed; runs++; });
    const s2 = observe(o, "speed", (c: any) => events.push(c.newValue));
    const s3 = intercept(o, "speed", (c: any) => (c.newValue > 100 ? null : c));
    o.speed = 500;
    expect(o.speed).toBe(10);
    expect(runs).toBe(1);
    expect(events).toEqual([]);
    o.speed = 50;
    expect(o.speed).toBe(50);
    expect(runs).toBe(2);
    expect(events).toEqual([50]);
    s1(); s2(); s3();
  });

  test("an interceptor rewrite stores the rewritten value", () => {
    /** Verifies: MOBX-EVT-003 */
    const o = observable({ level: 1 });
    const stop = intercept(o, "level", (c: any) => { c.newValue = c.newValue * 3; return c; });
    o.level = 4;
    expect(o.level).toBe(12);
    stop();
  });

  test("a whole-object interceptor vetoes property additions", () => {
    /** Verifies: MOBX-EVT-003 */
    const o = observable({ ok: 1 } as Record<string, number>);
    const stop = intercept(o, (c: any) => (c.type === "add" ? null : c));
    (o as any).nope = 5;
    expect(has(o, "nope")).toBe(false);
    expect(toJS(o)).toEqual({ ok: 1 });
    stop();
  });
});

describe("snapshots and introspection", () => {
  test("toJS produces deep plain data including built-in Map and Set", () => {
    /** Verifies: MOBX-SNP-001 */
    const src = observable({
      list: [1, { z: 2 }],
      lookup: observable.map({ q: 1 }),
      bag: observable.set([4]),
    });
    const js: any = toJS(src);
    expect(js.list).toEqual([1, { z: 2 }]);
    expect(js.lookup instanceof Map).toBe(true);
    expect(js.lookup.get("q")).toBe(1);
    expect(js.bag instanceof Set).toBe(true);
    expect([...js.bag]).toEqual([4]);
    expect(isObservable(js)).toBe(false);
    expect(isObservable(js.list)).toBe(false);
    expect(toJS(observable.box(3))).toBe(3);
    expect(toJS({ keep: [1] })).toEqual({ keep: [1] });
  });

  test("the predicate family classifies each kind and never throws on plain input", () => {
    /** Verifies: MOBX-SNP-002 */
    expect(isObservable({})).toBe(false);
    expect(isObservable(observable({}))).toBe(true);
    expect(isObservableArray(observable([]))).toBe(true);
    expect(isObservableArray([])).toBe(false);
    expect(isObservableMap(observable.map())).toBe(true);
    expect(isObservableSet(observable.set())).toBe(true);
    expect(isBoxedObservable(observable.box(1))).toBe(true);
    expect(isBoxedObservable(1)).toBe(false);
    expect(isComputed(computed(() => 1))).toBe(true);
    expect(isComputed(() => 1)).toBe(false);
  });

  test("isObservableProp and isComputedProp classify annotated members", () => {
    /** Verifies: MOBX-SNP-002 */
    class Meter {
      raw = 2;
      constructor() { makeObservable(this, { raw: observable, scaled: computed }); }
      get scaled() { return this.raw * 10; }
    }
    const m = new Meter();
    expect(isObservableProp(m, "raw")).toBe(true);
    expect(isComputedProp(m, "scaled")).toBe(true);
    expect(isComputedProp(m, "raw")).toBe(false);
  });
});

describe("observability lifecycle", () => {
  test("hooks fire on every observer-count transition", () => {
    /** Verifies: MOBX-LFC-001 */
    const b = observable.box(1);
    const events: string[] = [];
    const d1 = onBecomeObserved(b, () => events.push("on"));
    const d2 = onBecomeUnobserved(b, () => events.push("off"));
    const s1 = autorun(() => b.get());
    s1();
    const s2 = autorun(() => b.get());
    s2();
    expect(events).toEqual(["on", "off", "on", "off"]);
    d1();
    d2();
  });

  test("computed suspension is visible through its dependency's hooks", () => {
    /** Verifies: MOBX-LFC-001, MOBX-CMP-002 */
    const dep = observable.box(2);
    const hooks: string[] = [];
    onBecomeObserved(dep, () => hooks.push("on"));
    onBecomeUnobserved(dep, () => hooks.push("off"));
    let evals = 0;
    const doubled = computed(() => { evals++; return dep.get() * 2; });
    doubled.get();
    expect(hooks).toEqual([]);
    expect(evals).toBe(1);
    const stop = autorun(() => doubled.get());
    expect(hooks).toEqual(["on"]);
    expect(evals).toBe(2);
    stop();
    expect(hooks).toEqual(["on", "off"]);
    doubled.get();
    expect(evals).toBe(3);
  });
});
