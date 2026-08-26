// Spec2Repo oracle - atomic tests for xstate-statechart-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  createMachine,
  setup,
  createActor,
  getInitialSnapshot,
  getNextSnapshot,
  assign,
  raise,
  and,
  or,
  not,
  stateIn,
  matchesState,
  toPromise,
  SimulatedClock,
} from "xstate";

describe("machine definitions", () => {
  test("a machine interprets from a plain configuration object", () => {
    /** Verifies: XSTA-DEF-001, XSTA-ACT-001 */
    const m = createMachine({
      id: "kiln",
      initial: "cold",
      context: { temp: 20 },
      states: { cold: { on: { FIRE: "hot" } }, hot: {} },
    });
    const a = createActor(m).start();
    expect(a.getSnapshot().value).toBe("cold");
    expect(a.getSnapshot().context).toEqual({ temp: 20 });
    expect(a.getSnapshot().status).toBe("active");
  });

  test("named guards resolve from the second createMachine argument", () => {
    /** Verifies: XSTA-DEF-002, XSTA-GRD-001 */
    const m = createMachine(
      {
        initial: "idle",
        context: { fuel: 3 },
        states: {
          idle: { on: { LAUNCH: [{ guard: "hasFuel", target: "flying" }, { target: "stranded" }] } },
          flying: {},
          stranded: {},
        },
      },
      { guards: { hasFuel: ({ context }: any) => context.fuel > 0 } },
    );
    const a = createActor(m).start();
    a.send({ type: "LAUNCH" });
    expect(a.getSnapshot().value).toBe("flying");
  });

  test("provide returns a machine with overriding implementations", () => {
    /** Verifies: XSTA-DEF-002 */
    const m = createMachine(
      {
        initial: "idle",
        states: { idle: { on: { LAUNCH: [{ guard: "hasFuel", target: "flying" }, { target: "stranded" }] } }, flying: {}, stranded: {} },
      },
      { guards: { hasFuel: () => true } },
    );
    const a = createActor(m.provide({ guards: { hasFuel: () => false } })).start();
    a.send({ type: "LAUNCH" });
    expect(a.getSnapshot().value).toBe("stranded");
  });

  test("setup binds named actions and guards with params", () => {
    /** Verifies: XSTA-DEF-002, XSTA-AXN-002, XSTA-GRD-001 */
    const notes: string[] = [];
    const m = setup({
      actions: { note: (_: any, params: { msg: string }) => notes.push(params.msg) },
      guards: { atLeast: ({ context }: any, params: { min: number }) => context.n >= params.min },
    }).createMachine({
      context: { n: 4 },
      initial: "idle",
      states: {
        idle: {
          on: {
            TRY: {
              guard: { type: "atLeast", params: { min: 3 } },
              target: "ok",
              actions: { type: "note", params: { msg: "passed" } },
            },
          },
        },
        ok: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "TRY" });
    expect(a.getSnapshot().value).toBe("ok");
    expect(notes).toEqual(["passed"]);
  });

  test("an invalid transition target throws at machine creation", () => {
    /** Verifies: XSTA-DEF-004, XSTA-ERR-001 */
    expect(() =>
      createMachine({ initial: "a", states: { a: { on: { GO: "missing" } }, b: {} } }),
    ).toThrowError(Error);
  });

  test("a compound state without an initial key throws at machine creation", () => {
    /** Verifies: XSTA-DEF-005, XSTA-ERR-002 */
    expect(() => createMachine({ states: { a: {} } } as any)).toThrowError(/initial/i);
  });

  test("a context factory receives the actor input", () => {
    /** Verifies: XSTA-DEF-001, XSTA-ACT-007 */
    const m = createMachine({
      context: ({ input }: any) => ({ label: input.name.toUpperCase(), n: 0 }),
      initial: "ready",
      states: { ready: {} },
    });
    const a = createActor(m, { input: { name: "vega" } }).start();
    expect(a.getSnapshot().context).toEqual({ label: "VEGA", n: 0 });
  });
});

describe("actor lifecycle and snapshots", () => {
  const forge = createMachine({
    id: "forge",
    initial: "cool",
    context: { heats: 0 },
    states: {
      cool: { on: { HEAT: "molten" } },
      molten: {
        tags: ["glowing", "unsafe"],
        entry: assign({ heats: ({ context }: any) => context.heats + 1 }),
        on: { QUENCH: "cool" },
      },
    },
  });

  test("send transitions and updates the snapshot", () => {
    /** Verifies: XSTA-ACT-002, XSTA-ACT-005 */
    const a = createActor(forge).start();
    a.send({ type: "HEAT" });
    const s = a.getSnapshot();
    expect(s.value).toBe("molten");
    expect(s.context).toEqual({ heats: 1 });
    expect(s.status).toBe("active");
  });

  test("event payload properties reach guards and actions", () => {
    /** Verifies: XSTA-ACT-002, XSTA-AXN-003 */
    const m = createMachine({
      context: { total: 0 },
      initial: "sum",
      states: {
        sum: {
          on: {
            ADD: {
              guard: ({ event }: any) => event.amount > 0,
              actions: assign({ total: ({ context, event }: any) => context.total + event.amount }),
            },
          },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "ADD", amount: 7 });
    a.send({ type: "ADD", amount: -2 });
    expect(a.getSnapshot().context).toEqual({ total: 7 });
  });

  test("events with no matching transition are ignored", () => {
    /** Verifies: XSTA-ACT-004, XSTA-ERR-003 */
    const a = createActor(forge).start();
    a.send({ type: "NONSENSE" });
    expect(a.getSnapshot().value).toBe("cool");
    expect(a.getSnapshot().context).toEqual({ heats: 0 });
  });

  test("stop freezes the actor with a stopped status", () => {
    /** Verifies: XSTA-ACT-003 */
    const a = createActor(forge).start();
    a.stop();
    expect(a.getSnapshot().status).toBe("stopped");
    a.send({ type: "HEAT" });
    expect(a.getSnapshot().value).toBe("cool");
  });

  test("matches accepts full and partial state values", () => {
    /** Verifies: XSTA-ACT-006, XSTA-HPH-002 */
    const m = createMachine({
      initial: "outer",
      states: { outer: { initial: "one", states: { one: {}, two: {} } }, other: {} },
    });
    const s = createActor(m).start().getSnapshot();
    expect(s.matches("outer")).toBe(true);
    expect(s.matches({ outer: "one" })).toBe(true);
    expect(s.matches({ outer: "two" })).toBe(false);
    expect(s.matches("other")).toBe(false);
  });

  test("can reports whether an event would select a transition", () => {
    /** Verifies: XSTA-ACT-006, XSTA-GRD-003 */
    const a = createActor(forge).start();
    expect(a.getSnapshot().can({ type: "HEAT" })).toBe(true);
    expect(a.getSnapshot().can({ type: "QUENCH" })).toBe(false);
  });

  test("hasTag reflects tags of active states", () => {
    /** Verifies: XSTA-ACT-006 */
    const a = createActor(forge).start();
    expect(a.getSnapshot().hasTag("glowing")).toBe(false);
    a.send({ type: "HEAT" });
    expect(a.getSnapshot().hasTag("glowing")).toBe(true);
    expect(a.getSnapshot().hasTag("unsafe")).toBe(true);
    expect(a.getSnapshot().hasTag("frozen")).toBe(false);
  });

  test("matchesState tests refinement of plain state values", () => {
    /** Verifies: XSTA-ACT-006 */
    expect(matchesState("outer", { outer: "one" })).toBe(true);
    expect(matchesState({ outer: "one" }, { outer: "one" })).toBe(true);
    expect(matchesState({ outer: "two" }, { outer: "one" })).toBe(false);
  });

  test("a top-level leaf renders a string value and a compound renders an object", () => {
    /** Verifies: XSTA-ACT-005, XSTA-HPH-001 */
    const m = createMachine({
      id: "root",
      initial: "outer",
      states: {
        outer: { initial: "one", states: { one: { on: { JUMP: "#root.other" } }, two: {} } },
        other: {},
      },
    });
    const a = createActor(m).start();
    expect(a.getSnapshot().value).toEqual({ outer: "one" });
    a.send({ type: "JUMP" });
    expect(a.getSnapshot().value).toBe("other");
  });

  test("each step returns a fresh snapshot object", () => {
    /** Verifies: XSTA-ACT-005 */
    const a = createActor(forge).start();
    const before = a.getSnapshot();
    a.send({ type: "HEAT" });
    const after = a.getSnapshot();
    expect(before.value).toBe("cool");
    expect(after.value).toBe("molten");
    expect(before).not.toBe(after);
  });
});

describe("transition selection", () => {
  test("an exact descriptor matches its event type", () => {
    /** Verifies: XSTA-TRN-001 */
    const m = createMachine({
      initial: "hub",
      states: { hub: { on: { "cargo.load": "loading" } }, loading: {} },
    });
    const a = createActor(m).start();
    a.send({ type: "cargo.load" });
    expect(a.getSnapshot().value).toBe("loading");
  });

  test("descriptor specificity ranks exact over partial wildcard over star", () => {
    /** Verifies: XSTA-TRN-001 */
    const m = createMachine({
      initial: "hub",
      states: {
        hub: { on: { "cargo.load": "loading", "cargo.*": "cargoish", "*": "misc" } },
        loading: {},
        cargoish: {},
        misc: {},
      },
    });
    const run = (type: string) => {
      const a = createActor(m).start();
      a.send({ type });
      return a.getSnapshot().value;
    };
    expect(run("cargo.load")).toBe("loading");
    expect(run("cargo.dump")).toBe("cargoish");
    expect(run("anything")).toBe("misc");
  });

  test("candidates evaluate in document order with guard fall-through", () => {
    /** Verifies: XSTA-TRN-002 */
    const m = createMachine({
      context: { grade: 2 },
      initial: "sort",
      states: {
        sort: {
          on: {
            ROUTE: [
              { guard: ({ context }: any) => context.grade >= 5, target: "premium" },
              { guard: ({ context }: any) => context.grade >= 2, target: "standard" },
              { target: "reject" },
            ],
          },
        },
        premium: {},
        standard: {},
        reject: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "ROUTE" });
    expect(a.getSnapshot().value).toBe("standard");
  });

  test("an active child transition overrides the ancestor for the same event", () => {
    /** Verifies: XSTA-TRN-003 */
    const m = createMachine({
      initial: "papa",
      states: {
        papa: {
          initial: "kid",
          states: { kid: { on: { SHARED: "sib" } }, sib: {}, px: {} },
          on: { SHARED: ".px" },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "SHARED" });
    expect(a.getSnapshot().value).toEqual({ papa: "sib" });
  });

  test("an ancestor handles events no descendant handles", () => {
    /** Verifies: XSTA-TRN-003 */
    const m = createMachine({
      initial: "papa",
      states: {
        papa: {
          initial: "kid",
          states: { kid: {}, px: {} },
          on: { ESCALATE: ".px" },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "ESCALATE" });
    expect(a.getSnapshot().value).toEqual({ papa: "px" });
  });

  test("a bare string target names a sibling state", () => {
    /** Verifies: XSTA-TRN-004 */
    const m = createMachine({
      initial: "outer",
      states: { outer: { initial: "one", states: { one: { on: { NEXT: "two" } }, two: {} } } },
    });
    const a = createActor(m).start();
    a.send({ type: "NEXT" });
    expect(a.getSnapshot().value).toEqual({ outer: "two" });
  });

  test("a dot-prefixed target names a child of the source", () => {
    /** Verifies: XSTA-TRN-004 */
    const m = createMachine({
      initial: "outer",
      states: {
        outer: {
          initial: "one",
          states: { one: { on: { NEXT: "two" } }, two: {} },
          on: { RESET: ".one" },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "NEXT" });
    a.send({ type: "RESET" });
    expect(a.getSnapshot().value).toEqual({ outer: "one" });
  });

  test("a hash-prefixed target resolves by absolute id", () => {
    /** Verifies: XSTA-TRN-004, XSTA-DEF-003 */
    const m = createMachine({
      id: "root",
      initial: "outer",
      states: {
        outer: { initial: "one", states: { one: { on: { JUMP: "#root.other" } }, two: {} } },
        other: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "JUMP" });
    expect(a.getSnapshot().value).toBe("other");
  });

  test("a targetless transition runs actions without changing state", () => {
    /** Verifies: XSTA-TRN-005 */
    const log: string[] = [];
    const m = createMachine({
      initial: "spin",
      states: {
        spin: {
          entry: () => log.push("enter"),
          exit: () => log.push("exit"),
          on: { BUMP: { actions: () => log.push("bump") } },
        },
      },
    });
    const a = createActor(m).start();
    log.length = 0;
    a.send({ type: "BUMP" });
    expect(a.getSnapshot().value).toBe("spin");
    expect(log).toEqual(["bump"]);
  });

  test("a self-targeting transition does not re-enter by default", () => {
    /** Verifies: XSTA-TRN-006 */
    const log: string[] = [];
    const m = createMachine({
      initial: "spin",
      states: {
        spin: {
          entry: () => log.push("enter"),
          exit: () => log.push("exit"),
          on: { SOFT: { target: "spin" } },
        },
      },
    });
    const a = createActor(m).start();
    log.length = 0;
    a.send({ type: "SOFT" });
    expect(a.getSnapshot().value).toBe("spin");
    expect(log).toEqual([]);
  });

  test("reenter true forces exit and re-entry of the source", () => {
    /** Verifies: XSTA-TRN-006 */
    const log: string[] = [];
    const m = createMachine({
      initial: "spin",
      states: {
        spin: {
          entry: () => log.push("enter"),
          exit: () => log.push("exit"),
          on: { HARD: { target: "spin", reenter: true } },
        },
      },
    });
    const a = createActor(m).start();
    log.length = 0;
    a.send({ type: "HARD" });
    expect(log).toEqual(["exit", "enter"]);
  });

  test("always transitions resolve immediately on entry", () => {
    /** Verifies: XSTA-TRN-007 */
    const m = createMachine({
      context: { n: 5 },
      initial: "check",
      states: {
        check: {
          always: [
            { guard: ({ context }: any) => context.n > 3, target: "big" },
            { target: "small" },
          ],
        },
        big: {},
        small: {},
      },
    });
    expect(createActor(m).start().getSnapshot().value).toBe("big");
  });

  test("raise enqueues an internal event processed before external events", () => {
    /** Verifies: XSTA-TRN-008 */
    const m = createMachine({
      initial: "p",
      states: {
        p: { on: { KICK: { target: "q", actions: raise({ type: "PING" }) } } },
        q: { on: { PING: "r" } },
        r: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "KICK" });
    expect(a.getSnapshot().value).toBe("r");
  });

  test("multiple raised events process in first-in first-out order", () => {
    /** Verifies: XSTA-TRN-008 */
    const seen: string[] = [];
    const m = createMachine({
      initial: "a",
      states: {
        a: { on: { KICK: { target: "b", actions: [raise({ type: "ONE" }), raise({ type: "TWO" })] } } },
        b: {
          on: {
            ONE: { actions: () => seen.push("one") },
            TWO: { actions: () => seen.push("two") },
          },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "KICK" });
    expect(seen).toEqual(["one", "two"]);
  });
});

describe("actions and context", () => {
  test("actions run as exit then transition then entry", () => {
    /** Verifies: XSTA-AXN-001 */
    const log: string[] = [];
    const m = createMachine({
      initial: "a",
      states: {
        a: {
          exit: () => log.push("exit a"),
          on: { GO: { target: "b", actions: () => log.push("t action") } },
        },
        b: { entry: () => log.push("entry b") },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "GO" });
    expect(log).toEqual(["exit a", "t action", "entry b"]);
  });

  test("start runs entry actions from the machine node inward", () => {
    /** Verifies: XSTA-ACT-001, XSTA-AXN-001 */
    const order: string[] = [];
    const m = createMachine({
      initial: "outer",
      entry: () => order.push("machine"),
      states: {
        outer: {
          entry: () => order.push("outer"),
          initial: "inner",
          states: { inner: { entry: () => order.push("inner") } },
        },
      },
    });
    createActor(m).start();
    expect(order).toEqual(["machine", "outer", "inner"]);
  });

  test("assign accepts property updaters and plain values", () => {
    /** Verifies: XSTA-AXN-003 */
    const m = createMachine({
      context: { count: 1, label: "x" },
      initial: "s",
      states: {
        s: { on: { GO: { actions: assign({ count: ({ context }: any) => context.count + 9, label: "done" }) } } },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "GO" });
    expect(a.getSnapshot().context).toEqual({ count: 10, label: "done" });
  });

  test("assign accepts a single function returning partial context", () => {
    /** Verifies: XSTA-AXN-003 */
    const m = createMachine({
      context: { a: 1, b: 2 },
      initial: "s",
      states: { s: { on: { GO: { actions: assign(({ context }: any) => ({ b: context.b * 10 })) } } } },
    });
    const a = createActor(m).start();
    a.send({ type: "GO" });
    expect(a.getSnapshot().context).toEqual({ a: 1, b: 20 });
  });

  test("sequential assigns each see the previous result", () => {
    /** Verifies: XSTA-AXN-003 */
    const m = createMachine({
      context: { s: "" },
      initial: "x",
      states: {
        x: {
          on: {
            GO: {
              actions: [
                assign({ s: ({ context }: any) => context.s + "1" }),
                assign({ s: ({ context }: any) => context.s + "2" }),
              ],
            },
          },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "GO" });
    expect(a.getSnapshot().context).toEqual({ s: "12" });
  });

  test("an exit assign is visible to transition and entry actions", () => {
    /** Verifies: XSTA-AXN-003, XSTA-AXN-001 */
    const seq: string[] = [];
    const m = createMachine({
      context: { v: 0 },
      initial: "a",
      states: {
        a: {
          exit: assign({ v: () => 1 }),
          on: { GO: { target: "b", actions: ({ context }: any) => seq.push("t=" + context.v) } },
        },
        b: { entry: ({ context }: any) => seq.push("e=" + context.v) },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "GO" });
    expect(seq).toEqual(["t=1", "e=1"]);
  });

  test("entry actions observe the event that caused the entry", () => {
    /** Verifies: XSTA-AXN-002 */
    const m = createMachine({
      context: { last: "" },
      initial: "a",
      states: {
        a: { on: { MOVE: "b" } },
        b: { entry: assign({ last: ({ event }: any) => event.type }) },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "MOVE" });
    expect(a.getSnapshot().context).toEqual({ last: "MOVE" });
  });

  test("raised event payloads reach the triggered transition", () => {
    /** Verifies: XSTA-AXN-004, XSTA-TRN-008 */
    const m = createMachine({
      context: { got: 0 },
      initial: "a",
      states: {
        a: { on: { KICK: { target: "b", actions: raise({ type: "CARRY", load: 33 } as any) } } },
        b: { on: { CARRY: { actions: assign({ got: ({ event }: any) => event.load }) } } },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "KICK" });
    expect(a.getSnapshot().context).toEqual({ got: 33 });
  });
});

describe("guards", () => {
  test("an inline guard blocks the transition when false", () => {
    /** Verifies: XSTA-GRD-001, XSTA-GRD-003 */
    const m = createMachine({
      context: { ok: false },
      initial: "s",
      states: { s: { on: { TRY: { guard: ({ context }: any) => context.ok, target: "t" } } }, t: {} },
    });
    const a = createActor(m).start();
    a.send({ type: "TRY" });
    expect(a.getSnapshot().value).toBe("s");
  });

  test("guards read the event payload", () => {
    /** Verifies: XSTA-GRD-001 */
    const m = createMachine({
      initial: "gate",
      states: { gate: { on: { PASS: { guard: ({ event }: any) => event.code === 7, target: "open" } } }, open: {} },
    });
    const a = createActor(m).start();
    a.send({ type: "PASS", code: 3 });
    expect(a.getSnapshot().value).toBe("gate");
    a.send({ type: "PASS", code: 7 });
    expect(a.getSnapshot().value).toBe("open");
  });

  test("and or and not combine guards", () => {
    /** Verifies: XSTA-GRD-002 */
    const m = createMachine({
      context: { fuel: 5, locked: false },
      initial: "idle",
      states: {
        idle: {
          on: {
            GO: {
              guard: and([
                ({ context }: any) => context.fuel > 0,
                or([({ context }: any) => context.fuel > 10, not(({ context }: any) => context.locked)]),
              ]),
              target: "running",
            },
          },
        },
        running: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "GO" });
    expect(a.getSnapshot().value).toBe("running");
  });

  test("stateIn gates a transition on another parallel region", () => {
    /** Verifies: XSTA-GRD-002, XSTA-HPH-003 */
    const m = createMachine({
      type: "parallel",
      states: {
        power: { initial: "off", states: { off: { on: { SWITCH: "on" } }, on: {} } },
        arm: {
          initial: "safe",
          states: { safe: { on: { FIRE: { guard: stateIn({ power: "on" }), target: "fired" } } }, fired: {} },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "FIRE" });
    expect(a.getSnapshot().value).toEqual({ power: "off", arm: "safe" });
    a.send({ type: "SWITCH" });
    a.send({ type: "FIRE" });
    expect(a.getSnapshot().value).toEqual({ power: "on", arm: "fired" });
  });

  test("stateIn accepts an absolute id string", () => {
    /** Verifies: XSTA-GRD-002, XSTA-DEF-003 */
    const m = createMachine({
      id: "rig",
      type: "parallel",
      states: {
        power: { initial: "on", states: { on: {}, off: {} } },
        arm: {
          initial: "safe",
          states: { safe: { on: { FIRE: { guard: stateIn("#rig.power.on"), target: "fired" } } }, fired: {} },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "FIRE" });
    expect(a.getSnapshot().value).toEqual({ power: "on", arm: "fired" });
  });

  test("can returns false when every candidate is guarded off", () => {
    /** Verifies: XSTA-GRD-003 */
    const m = createMachine({
      context: { ok: false },
      initial: "s",
      states: { s: { on: { TRY: { guard: ({ context }: any) => context.ok, target: "t" } } }, t: {} },
    });
    const a = createActor(m).start();
    expect(a.getSnapshot().value).toBe("s");
    expect(a.getSnapshot().can({ type: "TRY" })).toBe(false);
    a.send({ type: "TRY" });
    expect(a.getSnapshot().value).toBe("s");
  });
});

describe("hierarchy parallel and history", () => {
  test("entering a compound state descends through initial defaults", () => {
    /** Verifies: XSTA-HPH-001 */
    const m = createMachine({
      initial: "run",
      states: {
        run: { initial: "gear", states: { gear: { initial: "first", states: { first: {}, second: {} } } } },
      },
    });
    expect(createActor(m).start().getSnapshot().value).toEqual({ run: { gear: "first" } });
  });

  test("matches accepts every prefix of the active path", () => {
    /** Verifies: XSTA-HPH-002 */
    const m = createMachine({
      initial: "run",
      states: {
        run: { initial: "gear", states: { gear: { initial: "first", states: { first: {}, second: {} } } } },
      },
    });
    const s = createActor(m).start().getSnapshot();
    expect(s.matches("run")).toBe(true);
    expect(s.matches({ run: "gear" })).toBe(true);
    expect(s.matches({ run: { gear: "first" } })).toBe(true);
    expect(s.matches({ run: { gear: "second" } })).toBe(false);
  });

  test("a parallel state activates every region", () => {
    /** Verifies: XSTA-HPH-003 */
    const m = createMachine({
      type: "parallel",
      states: {
        lights: { initial: "off", states: { off: { on: { TOGGLE: "on" } }, on: {} } },
        doors: { initial: "closed", states: { closed: { on: { OPEN: "opened" } }, opened: {} } },
      },
    });
    const a = createActor(m).start();
    expect(a.getSnapshot().value).toEqual({ lights: "off", doors: "closed" });
    a.send({ type: "TOGGLE" });
    expect(a.getSnapshot().value).toEqual({ lights: "on", doors: "closed" });
    a.send({ type: "OPEN" });
    expect(a.getSnapshot().value).toEqual({ lights: "on", doors: "opened" });
  });

  test("a finished region keeps its final key while others continue", () => {
    /** Verifies: XSTA-HPH-004 */
    const m = createMachine({
      initial: "work",
      states: {
        work: {
          type: "parallel",
          states: {
            a: { initial: "going", states: { going: { on: { DONE_A: "fin" } }, fin: { type: "final" } } },
            b: { initial: "going", states: { going: { on: { DONE_B: "fin" } }, fin: { type: "final" } } },
          },
          onDone: "celebrate",
        },
        celebrate: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "DONE_A" });
    expect(a.getSnapshot().value).toEqual({ work: { a: "fin", b: "going" } });
  });

  test("shallow history re-enters the remembered child through its initial defaults", () => {
    /** Verifies: XSTA-HPH-005 */
    const m = createMachine({
      initial: "run",
      states: {
        run: {
          initial: "gear",
          states: {
            gear: { initial: "first", states: { first: { on: { SHIFT: "second" } }, second: {} } },
            hist: { type: "history" },
          },
          on: { STOP: "halt" },
        },
        halt: { on: { RESUME: "run.hist" } },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "SHIFT" });
    a.send({ type: "STOP" });
    a.send({ type: "RESUME" });
    expect(a.getSnapshot().value).toEqual({ run: { gear: "first" } });
  });

  test("deep history restores the remembered leaf configuration", () => {
    /** Verifies: XSTA-HPH-005 */
    const m = createMachine({
      initial: "run",
      states: {
        run: {
          initial: "gear",
          states: {
            gear: { initial: "first", states: { first: { on: { SHIFT: "second" } }, second: {} } },
            deep: { type: "history", history: "deep" },
          },
          on: { STOP: "halt" },
        },
        halt: { on: { RESUME: "run.deep" } },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "SHIFT" });
    a.send({ type: "STOP" });
    a.send({ type: "RESUME" });
    expect(a.getSnapshot().value).toEqual({ run: { gear: "second" } });
  });

  test("history without a stored configuration enters the default initial path", () => {
    /** Verifies: XSTA-HPH-005 */
    const m = createMachine({
      initial: "off",
      states: {
        off: { on: { BOOT: "on.hist" } },
        on: {
          initial: "low",
          states: { low: {}, high: {}, hist: { type: "history" } },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "BOOT" });
    expect(a.getSnapshot().value).toEqual({ on: "low" });
  });

  test("history memory updates on every parent exit", () => {
    /** Verifies: XSTA-HPH-005 */
    const m = createMachine({
      initial: "run",
      states: {
        run: {
          initial: "gear",
          states: {
            gear: { initial: "first", states: { first: { on: { SHIFT: "second" } }, second: { on: { BACK: "first" } } } },
            hist: { type: "history", history: "deep" },
          },
          on: { STOP: "halt" },
        },
        halt: { on: { RESUME: "run.hist" } },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "SHIFT" });
    a.send({ type: "STOP" });
    a.send({ type: "RESUME" });
    expect(a.getSnapshot().value).toEqual({ run: { gear: "second" } });
    a.send({ type: "BACK" });
    a.send({ type: "STOP" });
    a.send({ type: "RESUME" });
    expect(a.getSnapshot().value).toEqual({ run: { gear: "first" } });
  });
});

describe("final states and output", () => {
  test("a top-level final state completes the machine", () => {
    /** Verifies: XSTA-FIN-001 */
    const m = createMachine({
      initial: "w",
      states: { w: { on: { END: "f", OTHER: "z" } }, z: {}, f: { type: "final" } },
    });
    const a = createActor(m).start();
    a.send({ type: "END" });
    expect(a.getSnapshot().status).toBe("done");
    expect(a.getSnapshot().value).toBe("f");
    a.send({ type: "OTHER" });
    expect(a.getSnapshot().value).toBe("f");
  });

  test("a compound onDone fires when its child reaches final", () => {
    /** Verifies: XSTA-FIN-002 */
    const m = createMachine({
      initial: "stage",
      states: {
        stage: {
          initial: "s1",
          states: { s1: { on: { STEP: "s2" } }, s2: { type: "final" } },
          onDone: "wrap",
        },
        wrap: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "STEP" });
    expect(a.getSnapshot().value).toBe("wrap");
  });

  test("a parallel onDone fires only when every region is final", () => {
    /** Verifies: XSTA-FIN-002, XSTA-HPH-004 */
    const m = createMachine({
      initial: "work",
      states: {
        work: {
          type: "parallel",
          states: {
            a: { initial: "going", states: { going: { on: { DONE_A: "fin" } }, fin: { type: "final" } } },
            b: { initial: "going", states: { going: { on: { DONE_B: "fin" } }, fin: { type: "final" } } },
          },
          onDone: "celebrate",
        },
        celebrate: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "DONE_A" });
    expect(a.getSnapshot().value).not.toBe("celebrate");
    a.send({ type: "DONE_B" });
    expect(a.getSnapshot().value).toBe("celebrate");
  });

  test("a final state's output reaches onDone as event.output", () => {
    /** Verifies: XSTA-FIN-003 */
    const m = createMachine({
      context: { got: null as any },
      initial: "phase",
      states: {
        phase: {
          initial: "p1",
          states: { p1: { on: { NEXT: "p2" } }, p2: { type: "final", output: () => ({ mark: 42 }) } },
          onDone: { target: "after", actions: assign({ got: ({ event }: any) => event.output }) },
        },
        after: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "NEXT" });
    expect(a.getSnapshot().value).toBe("after");
    expect(a.getSnapshot().context).toEqual({ got: { mark: 42 } });
  });

  test("machine output maps the completion event and defaults to undefined", () => {
    /** Verifies: XSTA-FIN-004 */
    const withMapper = createMachine({
      initial: "w",
      states: { w: { on: { END: "f" } }, f: { type: "final", output: () => ({ grade: "A" }) } },
      output: ({ event }: any) => ({ sawGrade: event.output.grade }),
    });
    const a1 = createActor(withMapper).start();
    a1.send({ type: "END" });
    expect(a1.getSnapshot().output).toEqual({ sawGrade: "A" });

    const withoutMapper = createMachine({
      initial: "w",
      states: { w: { on: { END: "f" } }, f: { type: "final", output: () => ({ grade: "A" }) } },
    });
    const a2 = createActor(withoutMapper).start();
    a2.send({ type: "END" });
    expect(a2.getSnapshot().status).toBe("done");
    expect(a2.getSnapshot().output).toBeUndefined();
  });

  test("toPromise resolves with the snapshot output at completion", async () => {
    /** Verifies: XSTA-FIN-005 */
    const m = createMachine({
      initial: "w",
      states: { w: { on: { END: "f" } }, f: { type: "final" } },
      output: () => ({ ok: 1 }),
    });
    const actor = createActor(m);
    const p = toPromise(actor);
    actor.start();
    actor.send({ type: "END" });
    expect(await p).toEqual({ ok: 1 });
  });
});

describe("timed transitions", () => {
  const lightMachine = createMachine({
    initial: "green",
    states: {
      green: { after: { 500: "yellow" } },
      yellow: { after: { 300: "red" }, on: { PANIC: "green" } },
      red: {},
    },
  });

  test("an after transition fires at its threshold and not before", () => {
    /** Verifies: XSTA-TMR-001, XSTA-TMR-002 */
    const clock = new SimulatedClock();
    const a = createActor(lightMachine, { clock }).start();
    clock.increment(499);
    expect(a.getSnapshot().value).toBe("green");
    clock.increment(1);
    expect(a.getSnapshot().value).toBe("yellow");
  });

  test("delays accumulate across several increments", () => {
    /** Verifies: XSTA-TMR-002 */
    const clock = new SimulatedClock();
    const a = createActor(lightMachine, { clock }).start();
    clock.increment(200);
    clock.increment(200);
    expect(a.getSnapshot().value).toBe("green");
    clock.increment(100);
    expect(a.getSnapshot().value).toBe("yellow");
  });

  test("exiting a state cancels its pending timer", () => {
    /** Verifies: XSTA-TMR-001 */
    const clock = new SimulatedClock();
    const a = createActor(lightMachine, { clock }).start();
    clock.increment(500);
    clock.increment(299);
    a.send({ type: "PANIC" });
    clock.increment(1);
    expect(a.getSnapshot().value).toBe("green");
  });

  test("re-entering a state re-arms its timer from zero", () => {
    /** Verifies: XSTA-TMR-001 */
    const clock = new SimulatedClock();
    const a = createActor(lightMachine, { clock }).start();
    clock.increment(500);
    a.send({ type: "PANIC" });
    clock.increment(499);
    expect(a.getSnapshot().value).toBe("green");
    clock.increment(1);
    expect(a.getSnapshot().value).toBe("yellow");
  });

  test("one large increment advances a delayed chain by a single step", () => {
    /** Verifies: XSTA-TMR-002 */
    const clock = new SimulatedClock();
    const m = createMachine({
      initial: "s1",
      states: { s1: { after: { 200: "s2" } }, s2: { after: { 300: "s3" } }, s3: {} },
    });
    const a = createActor(m, { clock }).start();
    clock.increment(600);
    expect(a.getSnapshot().value).toBe("s2");
    clock.increment(300);
    expect(a.getSnapshot().value).toBe("s3");
  });
});

describe("pure stepping and persistence", () => {
  const stepper = createMachine({
    initial: "cold",
    context: { temp: 20 },
    states: {
      cold: { on: { FIRE: "heating" } },
      heating: {
        entry: assign({ temp: ({ context }: any) => context.temp + 100 }),
        on: { READY: "soaking" },
      },
      soaking: {},
    },
  });

  test("getInitialSnapshot resolves the initial configuration and context", () => {
    /** Verifies: XSTA-PUR-001 */
    const s = getInitialSnapshot(stepper);
    expect(s.value).toBe("cold");
    expect(s.context).toEqual({ temp: 20 });
    expect(s.status).toBe("active");
  });

  test("getInitialSnapshot passes input to the context factory", () => {
    /** Verifies: XSTA-PUR-001 */
    const m = createMachine({
      context: ({ input }: any) => ({ seed: input.seed * 2 }),
      initial: "a",
      states: { a: {} },
    });
    expect(getInitialSnapshot(m, { seed: 21 }).context).toEqual({ seed: 42 });
  });

  test("getNextSnapshot returns the successor without mutating its input", () => {
    /** Verifies: XSTA-PUR-001, XSTA-PUR-002 */
    const s0 = getInitialSnapshot(stepper);
    const s1 = getNextSnapshot(stepper, s0, { type: "FIRE" });
    expect(s1.value).toBe("heating");
    expect(s1.context).toEqual({ temp: 120 });
    expect(s0.value).toBe("cold");
    expect(s0.context).toEqual({ temp: 20 });
  });

  test("pure steps apply assigns but never run side-effecting actions", () => {
    /** Verifies: XSTA-PUR-002 */
    const fx: string[] = [];
    const m = createMachine({
      context: { n: 0 },
      initial: "a",
      states: {
        a: { on: { GO: "b" } },
        b: { entry: [() => fx.push("effect"), assign({ n: () => 5 })] },
      },
    });
    const s = getNextSnapshot(m, getInitialSnapshot(m), { type: "GO" });
    expect(s.value).toBe("b");
    expect(s.context).toEqual({ n: 5 });
    expect(fx).toEqual([]);
  });

  test("pure steps process raised events and always transitions to quiescence", () => {
    /** Verifies: XSTA-PUR-001, XSTA-TRN-007, XSTA-TRN-008 */
    const m = createMachine({
      context: { hops: 0 },
      initial: "a",
      states: {
        a: { on: { GO: { target: "b", actions: raise({ type: "HOP" }) } } },
        b: { entry: assign({ hops: ({ context }: any) => context.hops + 1 }), on: { HOP: "c" } },
        c: { always: { guard: ({ context }: any) => context.hops > 0, target: "d" } },
        d: {},
      },
    });
    const s = getNextSnapshot(m, getInitialSnapshot(m), { type: "GO" });
    expect(s.value).toBe("d");
    expect(s.context).toEqual({ hops: 1 });
  });

  test("stepping a done snapshot keeps it done and unchanged", () => {
    /** Verifies: XSTA-PUR-003 */
    const m = createMachine({
      initial: "w",
      states: { w: { on: { END: "f" } }, f: { type: "final" } },
    });
    const done = getNextSnapshot(m, getInitialSnapshot(m), { type: "END" });
    expect(done.status).toBe("done");
    const after = getNextSnapshot(m, done, { type: "END" });
    expect(after.status).toBe("done");
    expect(after.value).toBe("f");
  });

  test("a persisted snapshot restores value and context in a new actor", () => {
    /** Verifies: XSTA-PUR-004 */
    const a1 = createActor(stepper).start();
    a1.send({ type: "FIRE" });
    const saved = a1.getPersistedSnapshot();
    a1.stop();
    const roundTripped = JSON.parse(JSON.stringify(saved));
    const a2 = createActor(stepper, { snapshot: roundTripped }).start();
    expect(a2.getSnapshot().value).toBe("heating");
    expect(a2.getSnapshot().context).toEqual({ temp: 120 });
    a2.send({ type: "READY" });
    expect(a2.getSnapshot().value).toBe("soaking");
  });
});
