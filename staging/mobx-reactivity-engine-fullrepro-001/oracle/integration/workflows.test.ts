// Spec2Repo oracle - integration tests for mobx-reactivity-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  observable,
  makeObservable, makeAutoObservable,
  observableShallow,
  computed, computedStruct,
  action, actionBound, runInAction, untracked,
  autorun, reaction, when,
  observe, intercept,
  onBecomeObserved, onBecomeUnobserved,
  configure,
  toJS, keys, set, has, remove,
  compareStructural,
  isObservable, isAction, isComputedProp, isObservableProp,
} from "mobx";

configure({ enforceActions: "never" });

describe("cross-projection agreement", () => {
  test("one mutation is reflected identically in every projection", () => {
    /** Verifies: MOBX-INV-001, MOBX-EVT-001, MOBX-SNP-001. Seam: effects x events x snapshots x generic views */
    const store = observable({ bays: 2, label: "north" });
    const runsSeen: number[] = [];
    const events: any[] = [];
    const s1 = autorun(() => runsSeen.push(store.bays));
    const s2 = observe(store, "bays", (c: any) => events.push([c.oldValue, c.newValue]));
    runInAction(() => (store.bays = 5));
    expect(runsSeen).toEqual([2, 5]);
    expect(events).toEqual([[2, 5]]);
    expect(toJS(store)).toEqual({ bays: 5, label: "north" });
    expect(store.bays).toBe(5);
    expect(JSON.stringify(store)).toBe('{"bays":5,"label":"north"}');
    s1(); s2();
  });

  test("a comparer-equal write is invisible in every projection", () => {
    /** Verifies: MOBX-INV-002, MOBX-OBS-003, MOBX-EVT-001. Seam: comparers x effects x events */
    const b = observable.box({ depth: 4 }, { equals: compareStructural });
    let runs = 0;
    const events: any[] = [];
    const s1 = autorun(() => { b.get(); runs++; });
    const s2 = observe(b, (c: any) => events.push(c.type));
    b.set({ depth: 4 });
    expect(runs).toBe(1);
    expect(events).toEqual([]);
    b.set({ depth: 9 });
    expect(runs).toBe(2);
    expect(events).toEqual(["update"]);
    s1(); s2();
  });

  test("a vetoed map addition never reaches computeds, effects or snapshots", () => {
    /** Verifies: MOBX-INV-003, MOBX-EVT-003, MOBX-COL-003. Seam: interception x derivation x snapshots */
    const stock = observable.map<string, number>({ bolts: 5 });
    const total = computed(() => [...stock.values()].reduce((a, b) => a + b, 0));
    const totals: number[] = [];
    const s1 = autorun(() => totals.push(total.get()));
    const s2 = intercept(stock, (c: any) => (c.type === "add" && c.newValue < 0 ? null : c));
    stock.set("scrap", -10);
    expect(stock.has("scrap")).toBe(false);
    expect(totals).toEqual([5]);
    expect(toJS(stock).get("scrap")).toBeUndefined();
    stock.set("nuts", 3);
    expect(totals).toEqual([5, 8]);
    s1(); s2();
  });

  test("computed evaluation counts follow observation state and batching", () => {
    /** Verifies: MOBX-INV-004, MOBX-CMP-002, MOBX-ACT-001. Seam: derivation cache x actions */
    const src = observable({ x: 1, y: 2 });
    let evals = 0;
    const sum = computed(() => { evals++; return src.x + src.y; });
    sum.get();
    sum.get();
    expect(evals).toBe(2);
    const stop = autorun(() => sum.get());
    expect(evals).toBe(3);
    sum.get();
    expect(evals).toBe(3);
    runInAction(() => { src.x = 10; src.y = 20; });
    expect(evals).toBe(4);
    expect(sum.get()).toBe(30);
    expect(evals).toBe(4);
    stop();
  });

  test("nested actions flush once through a computed into a reaction", () => {
    /** Verifies: MOBX-INV-005, MOBX-ACT-001, MOBX-CMP-002. Seam: nested batching x derivation x reaction */
    const ledger = observable({ credit: 10, debit: 4 });
    const net = computed(() => ledger.credit - ledger.debit);
    const observed: number[][] = [];
    const stop = reaction(() => net.get(), (nv: number, ov: number) => observed.push([nv, ov]));
    const addCredit = action((n: number) => (ledger.credit += n));
    const addDebit = action((n: number) => (ledger.debit += n));
    const settle = action(() => { addCredit(6); addDebit(2); });
    settle();
    expect(observed).toEqual([[10, 6]]);
    stop();
  });

  test("toJS snapshots serialize identically to the live store", () => {
    /** Verifies: MOBX-INV-006, MOBX-SNP-001. Seam: snapshots x live proxies */
    const store = observable({ crates: [{ id: 1, mass: 4 }], open: true });
    runInAction(() => {
      store.crates.push({ id: 2, mass: 9 });
      store.open = false;
    });
    const snap = toJS(store);
    expect(JSON.stringify(snap)).toBe(JSON.stringify(store));
    expect(isObservable(snap.crates)).toBe(false);
    snap.crates[0].mass = 999;
    expect(store.crates[0].mass).toBe(4);
  });

  test("disposal is total and the lifecycle hooks witness the release", () => {
    /** Verifies: MOBX-INV-007, MOBX-LFC-001, MOBX-EFF-004. Seam: effects x lifecycle hooks */
    const b = observable.box(1);
    const hookLog: string[] = [];
    onBecomeObserved(b, () => hookLog.push("on"));
    onBecomeUnobserved(b, () => hookLog.push("off"));
    let runs = 0;
    const stop = autorun(() => { b.get(); runs++; });
    stop();
    b.set(2);
    b.set(3);
    expect(runs).toBe(1);
    expect(hookLog).toEqual(["on", "off"]);
  });
});

describe("annotated store workflows", () => {
  test("an explicit class store routes actions through computeds into reactions", () => {
    /** Verifies: MOBX-ANN-001, MOBX-CMP-002, MOBX-ACT-001, MOBX-EFF-002. Seam: annotations x derivation x batching x reaction */
    class Depot {
      crates: { mass: number }[] = [{ mass: 40 }];
      factor = 2;
      constructor() {
        makeObservable(this, { crates: observable, factor: observable, load: computed, restock: action });
      }
      get load() { return this.crates.reduce((s, c) => s + c.mass, 0) * this.factor; }
      restock(mass: number, factor: number) {
        this.crates.push({ mass });
        this.factor = factor;
      }
    }
    const d = new Depot();
    const changes: number[][] = [];
    const stop = reaction(() => d.load, (nv: number, ov: number) => changes.push([nv, ov]));
    d.restock(10, 3);
    expect(changes).toEqual([[150, 80]]);
    expect(d.load).toBe(150);
    stop();
  });

  test("an inferred store keeps working through a detached bound action", () => {
    /** Verifies: MOBX-ANN-002, MOBX-ANN-004, MOBX-CMP-002. Seam: inference x binding x derivation */
    class Tank {
      level = 100;
      constructor() { makeAutoObservable(this, { drain: actionBound }); }
      get pct() { return this.level / 200; }
      drain(n: number) { this.level -= n; }
    }
    const t = new Tank();
    expect(isComputedProp(t, "pct")).toBe(true);
    expect(isAction(t.drain)).toBe(true);
    const seen: number[] = [];
    const stop = autorun(() => seen.push(t.pct));
    const detached = t.drain;
    detached(50);
    expect(seen).toEqual([0.5, 0.25]);
    stop();
  });

  test("class property interception rewrites and audits through observe", () => {
    /** Verifies: MOBX-EVT-002, MOBX-EVT-003, MOBX-ANN-001. Seam: interception x events x annotations */
    class Gauge {
      psi = 30;
      constructor() { makeObservable(this, { psi: observable }); }
    }
    const g = new Gauge();
    const audit: number[][] = [];
    const s1 = intercept(g, "psi", (c: any) => {
      c.newValue = Math.min(c.newValue, 100);
      return c;
    });
    const s2 = observe(g, "psi", (c: any) => audit.push([c.oldValue, c.newValue]));
    runInAction(() => (g.psi = 250));
    expect(g.psi).toBe(100);
    expect(audit).toEqual([[30, 100]]);
    s1(); s2();
  });

  test("a structural computed in the middle of a chain cuts propagation", () => {
    /** Verifies: MOBX-CMP-003, MOBX-CMP-002, MOBX-ANN-001. Seam: derivation chain x comparers */
    class Board {
      cells = [1, 2, 3];
      constructor() { makeObservable(this, { cells: observable, shape: computedStruct }); }
      get shape() { return { n: this.cells.length }; }
    }
    const b = new Board();
    const sizes: number[] = [];
    const stop = autorun(() => sizes.push(b.shape.n));
    runInAction(() => (b.cells[0] = 99));
    expect(sizes).toEqual([3]);
    runInAction(() => b.cells.push(4));
    expect(sizes).toEqual([3, 4]);
    stop();
  });
});

describe("collection workflows", () => {
  test("a map catalog stays consistent across merge, replace, events and effects", () => {
    /** Verifies: MOBX-COL-003, MOBX-EVT-001, MOBX-EFF-001. Seam: map API x events x effects */
    const catalog = observable.map<string, number>({ rope: 2 });
    const rosters: string[] = [];
    const events: string[] = [];
    const s1 = autorun(() => rosters.push([...catalog.keys()].join("+")));
    const s2 = observe(catalog, (c: any) => events.push(`${c.type}:${c.name}`));
    runInAction(() => catalog.merge({ tar: 1, net: 4 }));
    expect(rosters).toEqual(["rope", "rope+tar+net"]);
    expect(events).toEqual(["add:tar", "add:net"]);
    runInAction(() => catalog.replace({ sail: 7 }));
    expect(rosters[rosters.length - 1]).toBe("sail");
    expect(catalog.toJSON()).toEqual([["sail", 7]]);
    s1(); s2();
  });

  test("an array pipeline aggregates through computed while events audit each step", () => {
    /** Verifies: MOBX-COL-002, MOBX-EVT-001, MOBX-CMP-002. Seam: array extras x events x derivation */
    const masses = observable([5, 10]);
    const total = computed(() => masses.reduce((a, b) => a + b, 0));
    const totals: number[] = [];
    const spliceLog: any[] = [];
    const s1 = autorun(() => totals.push(total.get()));
    const s2 = observe(masses, (c: any) => { if (c.type === "splice") spliceLog.push([c.index, [...c.added], [...c.removed]]); });
    runInAction(() => masses.replace([1, 2, 3]));
    expect(totals).toEqual([15, 6]);
    runInAction(() => masses.splice(1, 1, 9));
    expect(totals).toEqual([15, 6, 13]);
    expect(spliceLog).toEqual([
      [0, [1, 2, 3], [5, 10]],
      [1, [9], [2]],
    ]);
    s1(); s2();
  });

  test("when observes a threshold crossed by a batched action", async () => {
    /** Verifies: MOBX-EFF-003, MOBX-ACT-001, MOBX-CMP-002. Seam: one-shot effects x batching x derivation */
    const bin = observable({ items: 0, limit: 3 });
    const full = computed(() => bin.items >= bin.limit);
    let firedAt = -1;
    when(() => full.get(), () => (firedAt = bin.items));
    const p = when(() => full.get());
    runInAction(() => { bin.items = 2; });
    expect(firedAt).toBe(-1);
    runInAction(() => { bin.items = 5; bin.limit = 4; });
    expect(firedAt).toBe(5);
    await p;
    expect(full.get()).toBe(true);
  });

  test("deep stores react to nested mutation while shallow stores do not", () => {
    /** Verifies: MOBX-OBS-002, MOBX-EFF-001, MOBX-ANN-001. Seam: conversion depth x effects */
    const deepStore = observable({ rows: [{ v: 1 }] });
    let deepRuns = 0;
    const s1 = autorun(() => { deepStore.rows[0].v; deepRuns++; });
    runInAction(() => (deepStore.rows[0].v = 2));
    expect(deepRuns).toBe(2);
    s1();

    class ShallowStore {
      rows: { v: number }[] = [{ v: 1 }];
      constructor() { makeObservable(this, { rows: observableShallow }); }
    }
    const shallow = new ShallowStore();
    let shallowRuns = 0;
    const s2 = autorun(() => { shallow.rows[0].v; shallowRuns++; });
    runInAction(() => (shallow.rows[0].v = 2));
    expect(shallowRuns).toBe(1);
    runInAction(() => (shallow.rows[0] = { v: 3 }));
    expect(shallowRuns).toBe(2);
    s2();
  });

  test("dynamic object shape flows through the generic API and the event stream", () => {
    /** Verifies: MOBX-OBS-004, MOBX-COL-005, MOBX-EVT-001. Seam: dynamic shape x generic views x events */
    const bag = observable({ seed: 1 } as Record<string, number>);
    const shapes: string[] = [];
    const events: string[] = [];
    const s1 = autorun(() => shapes.push(keys(bag).join(",")));
    const s2 = observe(bag, (c: any) => events.push(`${c.type}:${c.name}`));
    set(bag, "bloom", 2);
    remove(bag, "seed");
    expect(shapes).toEqual(["seed", "seed,bloom", "bloom"]);
    expect(events).toEqual(["add:bloom", "remove:seed"]);
    expect(has(bag, "seed")).toBe(false);
    s1(); s2();
  });

  test("same-value writes across containers emit no events and no runs", () => {
    /** Verifies: MOBX-OBS-006, MOBX-COL-004, MOBX-EVT-001. Seam: change detection x containers x events */
    const o = observable({ v: 5 });
    const m = observable.map({ k: 1 });
    const s = observable.set([2]);
    const events: string[] = [];
    let runs = 0;
    const d1 = observe(o, (c: any) => events.push("obj:" + c.type));
    const d2 = observe(m, (c: any) => events.push("map:" + c.type));
    const d3 = observe(s, (c: any) => events.push("set:" + c.type));
    const d4 = autorun(() => { o.v; m.get("k"); s.has(2); runs++; });
    o.v = 5;
    m.set("k", 1);
    s.add(2);
    expect(events).toEqual([]);
    expect(runs).toBe(1);
    d1(); d2(); d3(); d4();
  });
});

describe("tracking control workflows", () => {
  test("untracked sections keep reaction expressions selective", () => {
    /** Verifies: MOBX-CMP-005, MOBX-EFF-002. Seam: tracking exemption x reactions */
    const o = observable({ tracked: 1, loose: 10 });
    const outputs: number[] = [];
    const stop = reaction(
      () => o.tracked + untracked(() => o.loose),
      (nv: number) => outputs.push(nv),
    );
    runInAction(() => (o.loose = 20));
    expect(outputs).toEqual([]);
    runInAction(() => (o.tracked = 2));
    expect(outputs).toEqual([22]);
    stop();
  });

  test("enforceActions observed only warns for writes to observed state", () => {
    /** Verifies: MOBX-ACT-003, MOBX-EFF-001. Seam: write policy x observation state */
    configure({ enforceActions: "observed" });
    try {
      const free = observable({ v: 1 });
      const watched = observable({ v: 1 });
      const stop = autorun(() => watched.v);
      const warnings: string[] = [];
      const original = console.warn;
      console.warn = (msg: any) => { warnings.push(String(msg)); };
      free.v = 2;
      const afterFree = warnings.length;
      watched.v = 2;
      console.warn = original;
      stop();
      expect(afterFree).toBe(0);
      expect(warnings.length).toBe(1);
      expect(free.v).toBe(2);
      expect(watched.v).toBe(2);
    } finally {
      configure({ enforceActions: "never" });
    }
  });

  test("a self-disposing reaction stops mid-stream while observers keep auditing", () => {
    /** Verifies: MOBX-EFF-002, MOBX-EVT-001, MOBX-EFF-004. Seam: reaction lifecycle x event stream */
    const b = observable.box(0);
    const reacted: number[] = [];
    const audited: number[] = [];
    const stopObs = observe(b, (c: any) => audited.push(c.newValue));
    reaction(() => b.get(), (nv: number, _ov: number, r: any) => {
      reacted.push(nv);
      if (nv >= 2) r.dispose();
    });
    b.set(1);
    b.set(2);
    b.set(3);
    expect(reacted).toEqual([1, 2]);
    expect(audited).toEqual([1, 2, 3]);
    stopObs();
  });

  test("a structurally compared box coordinates events and lifecycle hooks", () => {
    /** Verifies: MOBX-OBS-003, MOBX-EVT-001, MOBX-LFC-001. Seam: comparers x events x lifecycle */
    const b = observable.box({ lane: 1 }, { equals: compareStructural });
    const events: any[] = [];
    const hooks: string[] = [];
    onBecomeObserved(b, () => hooks.push("on"));
    onBecomeUnobserved(b, () => hooks.push("off"));
    const d1 = observe(b, (c: any) => events.push(c.newValue.lane));
    const d2 = autorun(() => b.get());
    b.set({ lane: 1 });
    b.set({ lane: 2 });
    d2();
    expect(events).toEqual([2]);
    expect(hooks).toEqual(["on", "off"]);
    d1();
  });
});

describe("end-to-end workflows", () => {
  test("an inventory store lifecycle keeps every projection in agreement", () => {
    /** Verifies: MOBX-ANN-001, MOBX-ACT-001, MOBX-CMP-002, MOBX-EVT-001, MOBX-SNP-001, MOBX-INV-001. Seam: annotations x actions x derivation x events x snapshots */
    class Inventory {
      crates: { sku: string; qty: number }[] = [];
      unitMass = 3;
      constructor() {
        makeObservable(this, {
          crates: observable, unitMass: observable, totalMass: computed, receive: action, adjustMass: action,
        });
      }
      get totalMass() { return this.crates.reduce((s, c) => s + c.qty, 0) * this.unitMass; }
      receive(sku: string, qty: number) { this.crates.push({ sku, qty }); }
      adjustMass(m: number) { this.unitMass = m; }
    }
    const inv = new Inventory();
    const massLog: number[] = [];
    const spliceLog: string[] = [];
    const s1 = autorun(() => massLog.push(inv.totalMass));
    const s2 = observe(inv.crates, (c: any) => { if (c.type === "splice") spliceLog.push(c.added.map((a: any) => a.sku).join()); });
    inv.receive("TILE", 4);
    inv.receive("PIPE", 2);
    inv.adjustMass(5);
    expect(massLog).toEqual([0, 12, 18, 30]);
    expect(spliceLog).toEqual(["TILE", "PIPE"]);
    const snap = toJS(inv.crates);
    expect(snap).toEqual([{ sku: "TILE", qty: 4 }, { sku: "PIPE", qty: 2 }]);
    expect(isObservable(snap)).toBe(false);
    expect(JSON.stringify(inv.crates)).toBe(JSON.stringify(snap));
    expect(isObservableProp(inv, "unitMass")).toBe(true);
    s1(); s2();
  });

  test("a guarded ledger enforces rules through interception while a promise watches the balance", async () => {
    /** Verifies: MOBX-EVT-003, MOBX-EVT-002, MOBX-EFF-003, MOBX-ACT-001, MOBX-INV-003. Seam: interception x events x one-shot effects x batching */
    const ledger = observable({ balance: 100 });
    const audit: number[][] = [];
    const s1 = intercept(ledger, "balance", (c: any) => (c.newValue < 0 ? null : c));
    const s2 = observe(ledger, "balance", (c: any) => audit.push([c.oldValue, c.newValue]));
    const solvent = when(() => ledger.balance >= 250);
    runInAction(() => (ledger.balance = -50));
    expect(ledger.balance).toBe(100);
    expect(audit).toEqual([]);
    runInAction(() => (ledger.balance = 180));
    runInAction(() => (ledger.balance = 260));
    await solvent;
    expect(audit).toEqual([[100, 180], [180, 260]]);
    expect(toJS(ledger)).toEqual({ balance: 260 });
    s1(); s2();
  });

  test("a catalog sync propagates one source of truth across map, set and array views", () => {
    /** Verifies: MOBX-COL-003, MOBX-COL-004, MOBX-EFF-002, MOBX-ACT-001, MOBX-INV-001. Seam: containers x reactions x batching */
    const prices = observable.map<string, number>({ rope: 4 });
    const expensive = observable.set<string>();
    const names = observable<string>([]);
    const s1 = reaction(
      () => [...prices.entries()],
      (pairs: [string, number][]) => {
        runInAction(() => {
          expensive.clear();
          names.replace(pairs.map(([k]) => k));
          for (const [k, v] of pairs) if (v >= 10) expensive.add(k);
        });
      },
    );
    runInAction(() => prices.merge({ anchor: 25, tar: 3 }));
    expect(names.slice().sort()).toEqual(["anchor", "rope", "tar"]);
    expect([...expensive]).toEqual(["anchor"]);
    runInAction(() => { prices.set("rope", 12); prices.delete("tar"); });
    expect(names.slice().sort()).toEqual(["anchor", "rope"]);
    expect([...expensive].sort()).toEqual(["anchor", "rope"]);
    const snap = toJS(prices);
    expect(snap instanceof Map).toBe(true);
    expect([...snap.entries()].sort()).toEqual([["anchor", 25], ["rope", 12]]);
    s1();
  });

  test("a demand-driven cache suspends and resumes across observation cycles", () => {
    /** Verifies: MOBX-CMP-002, MOBX-LFC-001, MOBX-CMP-005, MOBX-INV-004, MOBX-INV-007. Seam: derivation cache x lifecycle hooks x tracking exemption */
    const feed = observable({ raw: 2, noise: 0 });
    const hooks: string[] = [];
    let evals = 0;
    const refined = computed(() => {
      evals++;
      return feed.raw * 10 + untracked(() => feed.noise);
    });
    onBecomeObserved(refined, () => hooks.push("on"));
    onBecomeUnobserved(refined, () => hooks.push("off"));
    refined.get();
    refined.get();
    expect(evals).toBe(2);
    expect(hooks).toEqual([]);
    const stop = autorun(() => refined.get());
    expect(hooks).toEqual(["on"]);
    expect(evals).toBe(3);
    refined.get();
    expect(evals).toBe(3);
    runInAction(() => (feed.noise = 7));
    expect(evals).toBe(3);
    runInAction(() => (feed.raw = 3));
    expect(evals).toBe(4);
    stop();
    expect(hooks).toEqual(["on", "off"]);
    expect(refined.get()).toBe(37);
    expect(evals).toBe(5);
  });
});
