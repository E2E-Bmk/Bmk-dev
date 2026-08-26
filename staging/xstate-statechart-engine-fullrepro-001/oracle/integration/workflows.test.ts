// Spec2Repo oracle - integration tests for xstate-statechart-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  createMachine,
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

describe("cross-projection invariants", () => {
  test("actor interpretation and pure stepping agree over a mixed event sequence", () => {
    /** Verifies: XSTA-INV-001, XSTA-PUR-001, XSTA-TRN-008. Seam: actor loop x pure step functions */
    const m = createMachine({
      context: { tally: 0 },
      initial: "collect",
      states: {
        collect: {
          on: {
            ADD: { actions: assign({ tally: ({ context, event }: any) => context.tally + event.n }) },
            CLOSE: { target: "route", actions: raise({ type: "DECIDE" }) },
          },
        },
        route: {
          on: {
            DECIDE: [
              { guard: ({ context }: any) => context.tally >= 10, target: "bulk" },
              { target: "retail" },
            ],
          },
        },
        bulk: {},
        retail: {},
      },
    });
    const events = [
      { type: "ADD", n: 4 },
      { type: "ADD", n: 7 },
      { type: "CLOSE" },
    ];
    const actor = createActor(m).start();
    let pure = getInitialSnapshot(m);
    for (const e of events) {
      actor.send(e as any);
      pure = getNextSnapshot(m, pure, e as any);
      expect(pure.value).toEqual(actor.getSnapshot().value);
      expect(pure.context).toEqual(actor.getSnapshot().context);
    }
    expect(actor.getSnapshot().value).toBe("bulk");
    expect(actor.getSnapshot().context).toEqual({ tally: 11 });
  });

  test("a false can implies the event leaves value and context unchanged", () => {
    /** Verifies: XSTA-INV-002, XSTA-GRD-003, XSTA-ACT-006. Seam: query surface x interpretation */
    const m = createMachine({
      context: { armed: false },
      initial: "silo",
      states: {
        silo: {
          on: {
            ARM: { actions: assign({ armed: () => true }) },
            FIRE: { guard: ({ context }: any) => context.armed, target: "launched" },
          },
        },
        launched: {},
      },
    });
    const a = createActor(m).start();
    expect(a.getSnapshot().can({ type: "FIRE" })).toBe(false);
    a.send({ type: "FIRE" });
    expect(a.getSnapshot().value).toBe("silo");
    expect(a.getSnapshot().context).toEqual({ armed: false });
    a.send({ type: "ARM" });
    expect(a.getSnapshot().can({ type: "FIRE" })).toBe(true);
    a.send({ type: "FIRE" });
    expect(a.getSnapshot().value).toBe("launched");
  });

  test("matches agrees with matchesState across a nested run", () => {
    /** Verifies: XSTA-INV-003, XSTA-ACT-006, XSTA-HPH-002. Seam: snapshot query x value utility */
    const m = createMachine({
      initial: "mill",
      states: {
        mill: {
          initial: "grind",
          states: { grind: { on: { SIFT: "sieve" } }, sieve: {} },
        },
      },
    });
    const a = createActor(m).start();
    const probes: any[] = ["mill", { mill: "grind" }, { mill: "sieve" }];
    for (const p of probes) {
      expect(a.getSnapshot().matches(p)).toBe(matchesState(p, a.getSnapshot().value as any));
    }
    a.send({ type: "SIFT" });
    for (const p of probes) {
      expect(a.getSnapshot().matches(p)).toBe(matchesState(p, a.getSnapshot().value as any));
    }
    expect(a.getSnapshot().matches({ mill: "sieve" })).toBe(true);
  });

  test("a resumed actor continues exactly like the original", () => {
    /** Verifies: XSTA-INV-004, XSTA-PUR-004. Seam: persistence x interpretation */
    const m = createMachine({
      context: { steps: [] as string[] },
      initial: "one",
      states: {
        one: { on: { HOP: { target: "two", actions: assign({ steps: ({ context }: any) => [...context.steps, "a"] }) } } },
        two: { on: { HOP: { target: "three", actions: assign({ steps: ({ context }: any) => [...context.steps, "b"] }) } } },
        three: {},
      },
    });
    const original = createActor(m).start();
    original.send({ type: "HOP" });
    const saved = JSON.parse(JSON.stringify(original.getPersistedSnapshot()));
    original.send({ type: "HOP" });

    const resumed = createActor(m, { snapshot: saved }).start();
    resumed.send({ type: "HOP" });
    expect(resumed.getSnapshot().value).toEqual(original.getSnapshot().value);
    expect(resumed.getSnapshot().context).toEqual(original.getSnapshot().context);
    expect(resumed.getSnapshot().context).toEqual({ steps: ["a", "b"] });
  });
});

describe("guarded routing workflows", () => {
  test("a triage machine routes by combinator guards over payload and context", () => {
    /** Verifies: XSTA-GRD-002, XSTA-TRN-002, XSTA-AXN-003. Seam: guard combinators x candidate order x context */
    const m = createMachine({
      context: { staffed: true },
      initial: "intake",
      states: {
        intake: {
          on: {
            CASE: [
              {
                guard: and([({ event }: any) => event.severity >= 8, ({ context }: any) => context.staffed]),
                target: "surgery",
              },
              {
                guard: or([({ event }: any) => event.severity >= 4, not(({ context }: any) => context.staffed)]),
                target: "ward",
              },
              { target: "clinic" },
            ],
          },
        },
        surgery: {},
        ward: {},
        clinic: {},
      },
    });
    const route = (severity: number) => {
      const a = createActor(m).start();
      a.send({ type: "CASE", severity });
      return a.getSnapshot().value;
    };
    expect(route(9)).toBe("surgery");
    expect(route(5)).toBe("ward");
    expect(route(1)).toBe("clinic");
  });

  test("provide swaps a named guard without touching the source machine", () => {
    /** Verifies: XSTA-DEF-002, XSTA-GRD-001. Seam: implementation resolution x interpretation */
    const m = createMachine(
      {
        initial: "gate",
        states: { gate: { on: { ENTER: [{ guard: "vip", target: "lounge" }, { target: "hall" }] } }, lounge: {}, hall: {} },
      },
      { guards: { vip: () => false } },
    );
    const plain = createActor(m).start();
    plain.send({ type: "ENTER" });
    expect(plain.getSnapshot().value).toBe("hall");

    const upgraded = createActor(m.provide({ guards: { vip: () => true } })).start();
    upgraded.send({ type: "ENTER" });
    expect(upgraded.getSnapshot().value).toBe("lounge");

    const plainAgain = createActor(m).start();
    plainAgain.send({ type: "ENTER" });
    expect(plainAgain.getSnapshot().value).toBe("hall");
  });

  test("wildcard descriptors and child precedence route a hierarchical dispatcher", () => {
    /** Verifies: XSTA-TRN-001, XSTA-TRN-003. Seam: descriptor matching x hierarchy */
    const m = createMachine({
      id: "d",
      initial: "desk",
      states: {
        desk: {
          initial: "focus",
          states: {
            focus: { on: { "job.run": "#d.working" } },
            paused: {},
            misc: {},
          },
          on: { "job.*": ".paused", "*": ".misc" },
        },
        working: {},
      },
    });
    const run = (type: string) => {
      const a = createActor(m).start();
      a.send({ type });
      return a.getSnapshot().value;
    };
    expect(run("job.run")).toBe("working");
    expect(run("job.pause")).toEqual({ desk: "paused" });
    expect(run("coffee")).toEqual({ desk: "misc" });
  });

  test("raised events cascade through guards to a quiescent state", () => {
    /** Verifies: XSTA-TRN-008, XSTA-AXN-004, XSTA-TRN-007. Seam: internal queue x guards x eventless transitions */
    const m = createMachine({
      context: { path: "" },
      initial: "start",
      states: {
        start: {
          on: {
            KICK: {
              target: "sortA",
              actions: [raise({ type: "TAG", label: "red" } as any), raise({ type: "TAG", label: "blue" } as any)],
            },
          },
        },
        sortA: {
          on: {
            TAG: [
              {
                guard: ({ event }: any) => event.label === "red",
                target: "sortB",
                actions: assign({ path: ({ context }: any) => context.path + "r" }),
              },
            ],
          },
        },
        sortB: {
          on: {
            TAG: {
              guard: ({ event }: any) => event.label === "blue",
              target: "check",
              actions: assign({ path: ({ context }: any) => context.path + "b" }),
            },
          },
        },
        check: {
          always: [{ guard: ({ context }: any) => context.path === "rb", target: "ok" }, { target: "bad" }],
        },
        ok: {},
        bad: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "KICK" });
    expect(a.getSnapshot().value).toBe("ok");
    expect(a.getSnapshot().context).toEqual({ path: "rb" });
  });
});

describe("parallel coordination", () => {
  test("stateIn gates one region on another across a workflow", () => {
    /** Verifies: XSTA-GRD-002, XSTA-HPH-003. Seam: parallel regions x cross-region guards */
    const m = createMachine({
      type: "parallel",
      states: {
        oven: { initial: "cold", states: { cold: { on: { PREHEAT: "hot" } }, hot: {} } },
        dough: {
          initial: "proofing",
          states: {
            proofing: { on: { LOAD: { guard: stateIn({ oven: "hot" }), target: "baking" } } },
            baking: {},
          },
        },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "LOAD" });
    expect(a.getSnapshot().value).toEqual({ oven: "cold", dough: "proofing" });
    a.send({ type: "PREHEAT" });
    a.send({ type: "LOAD" });
    expect(a.getSnapshot().value).toEqual({ oven: "hot", dough: "baking" });
  });

  test("regions finish independently and onDone fires only at full completion", () => {
    /** Verifies: XSTA-HPH-004, XSTA-FIN-002. Seam: parallel completion x final states */
    const m = createMachine({
      initial: "audit",
      states: {
        audit: {
          type: "parallel",
          states: {
            ledger: { initial: "open", states: { open: { on: { BALANCE: "closed" } }, closed: { type: "final" } } },
            stock: { initial: "open", states: { open: { on: { COUNT: "closed" } }, closed: { type: "final" } } },
          },
          onDone: "signed",
        },
        signed: {},
      },
    });
    const a = createActor(m).start();
    a.send({ type: "COUNT" });
    expect(a.getSnapshot().value).toEqual({ audit: { ledger: "open", stock: "closed" } });
    a.send({ type: "BALANCE" });
    expect(a.getSnapshot().value).toBe("signed");
  });

  test("independent timers in parallel regions fire from one simulated clock", () => {
    /** Verifies: XSTA-TMR-001, XSTA-TMR-002, XSTA-HPH-003. Seam: delayed transitions x parallel regions */
    const m = createMachine({
      type: "parallel",
      states: {
        brew: { initial: "steeping", states: { steeping: { after: { 200: "ready" } }, ready: {} } },
        toast: { initial: "toasting", states: { toasting: { after: { 500: "popped" } }, popped: {} } },
      },
    });
    const clock = new SimulatedClock();
    const a = createActor(m, { clock }).start();
    clock.increment(200);
    expect(a.getSnapshot().value).toEqual({ brew: "ready", toast: "toasting" });
    clock.increment(300);
    expect(a.getSnapshot().value).toEqual({ brew: "ready", toast: "popped" });
  });
});

describe("history workflows", () => {
  test("shallow and deep history nodes in one parent restore different depths", () => {
    /** Verifies: XSTA-HPH-005. Seam: history resolution x nested hierarchy */
    const m = createMachine({
      initial: "run",
      states: {
        run: {
          initial: "mode",
          states: {
            mode: {
              initial: "auto",
              states: {
                auto: { initial: "eco", states: { eco: { on: { BOOST: "sport" } }, sport: {} } },
                manual: {},
              },
            },
            flat: { type: "history" },
            full: { type: "history", history: "deep" },
          },
          on: { STOP: "halt" },
        },
        halt: { on: { SHALLOW: "run.flat", DEEP: "run.full" } },
      },
    });
    const viaShallow = createActor(m).start();
    viaShallow.send({ type: "BOOST" });
    viaShallow.send({ type: "STOP" });
    viaShallow.send({ type: "SHALLOW" });
    expect(viaShallow.getSnapshot().value).toEqual({ run: { mode: { auto: "eco" } } });

    const viaDeep = createActor(m).start();
    viaDeep.send({ type: "BOOST" });
    viaDeep.send({ type: "STOP" });
    viaDeep.send({ type: "DEEP" });
    expect(viaDeep.getSnapshot().value).toEqual({ run: { mode: { auto: "sport" } } });
  });

  test("deep history memory survives a persistence round trip", () => {
    /** Verifies: XSTA-HPH-005, XSTA-PUR-004. Seam: history x persistence */
    const m = createMachine({
      initial: "edit",
      states: {
        edit: {
          initial: "mode",
          states: {
            mode: { initial: "draft", states: { draft: { on: { POLISH: "finalizing" } }, finalizing: {} } },
            hist: { type: "history", history: "deep" },
          },
          on: { LEAVE: "menu" },
        },
        menu: { on: { BACK: "edit.hist" } },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "POLISH" });
    a.send({ type: "LEAVE" });
    const saved = JSON.parse(JSON.stringify(a.getPersistedSnapshot()));
    a.stop();
    const b = createActor(m, { snapshot: saved }).start();
    expect(b.getSnapshot().value).toBe("menu");
    b.send({ type: "BACK" });
    expect(b.getSnapshot().value).toEqual({ edit: { mode: "finalizing" } });
  });
});

describe("timed workflows", () => {
  test("a reenter self-transition re-arms the timer while a plain one does not", () => {
    /** Verifies: XSTA-TRN-006, XSTA-TMR-001. Seam: self-transition semantics x timers */
    const m = createMachine({
      initial: "watch",
      states: {
        watch: {
          after: { 300: "expired" },
          on: { NUDGE: { target: "watch", reenter: true }, TAP: { target: "watch" } },
        },
        expired: {},
      },
    });
    const c1 = new SimulatedClock();
    const nudged = createActor(m, { clock: c1 }).start();
    c1.increment(200);
    nudged.send({ type: "NUDGE" });
    c1.increment(200);
    expect(nudged.getSnapshot().value).toBe("watch");
    c1.increment(100);
    expect(nudged.getSnapshot().value).toBe("expired");

    const c2 = new SimulatedClock();
    const tapped = createActor(m, { clock: c2 }).start();
    c2.increment(200);
    tapped.send({ type: "TAP" });
    c2.increment(100);
    expect(tapped.getSnapshot().value).toBe("expired");
  });

  test("an escalation ladder climbs one rung per accumulated threshold", () => {
    /** Verifies: XSTA-TMR-002, XSTA-INV-005, XSTA-AXN-001. Seam: chained delays x entry actions */
    const m = createMachine({
      context: { pings: [] as string[] },
      initial: "calm",
      states: {
        calm: { after: { 250: "alert" } },
        alert: {
          entry: assign({ pings: ({ context }: any) => [...context.pings, "alert"] }),
          after: { 350: "critical" },
        },
        critical: { entry: assign({ pings: ({ context }: any) => [...context.pings, "critical"] }) },
      },
    });
    const clock = new SimulatedClock();
    const a = createActor(m, { clock }).start();
    clock.increment(249);
    expect(a.getSnapshot().value).toBe("calm");
    clock.increment(1);
    expect(a.getSnapshot().value).toBe("alert");
    clock.increment(349);
    expect(a.getSnapshot().value).toBe("alert");
    clock.increment(1);
    expect(a.getSnapshot().value).toBe("critical");
    expect(a.getSnapshot().context).toEqual({ pings: ["alert", "critical"] });
  });
});

describe("completion pipelines", () => {
  test("final output routes through guarded onDone into machine output", () => {
    /** Verifies: XSTA-FIN-003, XSTA-FIN-004, XSTA-FIN-002. Seam: final output x onDone guards x machine output */
    const m = createMachine({
      context: { verdict: "" },
      initial: "review",
      states: {
        review: {
          initial: "collect",
          states: {
            collect: { on: { SUBMIT: "assess" } },
            assess: {
              on: {
                SCORE: [
                  { guard: ({ event }: any) => event.pts >= 60, target: "passed" },
                  { target: "failed" },
                ],
              },
            },
            passed: { type: "final", output: () => ({ grade: "pass" }) },
            failed: { type: "final", output: () => ({ grade: "fail" }) },
          },
          onDone: [
            {
              guard: ({ event }: any) => event.output.grade === "pass",
              target: "archive",
              actions: assign({ verdict: ({ event }: any) => event.output.grade }),
            },
            { target: "escalate", actions: assign({ verdict: ({ event }: any) => event.output.grade }) },
          ],
        },
        archive: { type: "final" },
        escalate: { type: "final" },
      },
      output: ({ context }: any) => ({ verdict: context.verdict }),
    });
    const pass = createActor(m).start();
    pass.send({ type: "SUBMIT" });
    pass.send({ type: "SCORE", pts: 72 });
    expect(pass.getSnapshot().value).toBe("archive");
    expect(pass.getSnapshot().output).toEqual({ verdict: "pass" });

    const fail = createActor(m).start();
    fail.send({ type: "SUBMIT" });
    fail.send({ type: "SCORE", pts: 12 });
    expect(fail.getSnapshot().value).toBe("escalate");
    expect(fail.getSnapshot().output).toEqual({ verdict: "fail" });
  });

  test("toPromise observes a completion driven by raised events", async () => {
    /** Verifies: XSTA-FIN-005, XSTA-TRN-008. Seam: promise projection x internal queue */
    const m = createMachine({
      initial: "a",
      states: {
        a: { on: { GO: { target: "b", actions: raise({ type: "FINISH" }) } } },
        b: { on: { FINISH: "f" } },
        f: { type: "final" },
      },
      output: () => ({ landed: true }),
    });
    const actor = createActor(m);
    const settled = toPromise(actor);
    actor.start();
    actor.send({ type: "GO" });
    expect(await settled).toEqual({ landed: true });
    expect(actor.getSnapshot().status).toBe("done");
  });

  test("input shapes context and the completion output derives from it", () => {
    /** Verifies: XSTA-ACT-007, XSTA-FIN-004, XSTA-AXN-003. Seam: input x context factory x output */
    const m = createMachine({
      context: ({ input }: any) => ({ crate: input.crate, weight: input.weight, sealed: false }),
      initial: "open",
      states: {
        open: { on: { SEAL: { target: "shipped", actions: assign({ sealed: () => true }) } } },
        shipped: { type: "final" },
      },
      output: ({ context }: any) => ({ label: context.crate + ":" + context.weight, sealed: context.sealed }),
    });
    const a = createActor(m, { input: { crate: "K-9", weight: 40 } }).start();
    a.send({ type: "SEAL" });
    expect(a.getSnapshot().status).toBe("done");
    expect(a.getSnapshot().output).toEqual({ label: "K-9:40", sealed: true });
  });
});

describe("pure stepping pipelines", () => {
  test("a pure fold reaches done with computed output", () => {
    /** Verifies: XSTA-PUR-001, XSTA-PUR-003, XSTA-FIN-004. Seam: pure step x completion */
    const m = createMachine({
      context: { n: 0 },
      initial: "a",
      states: {
        a: { on: { GO: { target: "b", actions: assign({ n: () => 7 }) } } },
        b: { on: { END: "f" } },
        f: { type: "final", output: ({ context }: any) => ({ half: context.n }) },
      },
      output: ({ event }: any) => ({ total: event.output.half * 2 }),
    });
    let s = getInitialSnapshot(m);
    for (const e of [{ type: "GO" }, { type: "END" }]) s = getNextSnapshot(m, s, e as any);
    expect(s.status).toBe("done");
    expect(s.value).toBe("f");
    expect(s.output).toEqual({ total: 14 });
    const after = getNextSnapshot(m, s, { type: "END" } as any);
    expect(after.status).toBe("done");
    expect(after.value).toBe("f");
  });

  test("pure steps replay a raise pipeline applying assigns but no effects", () => {
    /** Verifies: XSTA-PUR-002, XSTA-TRN-008, XSTA-AXN-004. Seam: pure step x internal queue x actions */
    const fx: string[] = [];
    const m = createMachine({
      context: { path: "" },
      initial: "start",
      states: {
        start: {
          on: { KICK: { target: "mid", actions: [() => fx.push("boom"), raise({ type: "STEP", mark: "z" } as any)] } },
        },
        mid: {
          on: {
            STEP: {
              target: "endpoint",
              actions: assign({ path: ({ context, event }: any) => context.path + event.mark }),
            },
          },
        },
        endpoint: {},
      },
    });
    const s = getNextSnapshot(m, getInitialSnapshot(m), { type: "KICK" } as any);
    expect(s.value).toBe("endpoint");
    expect(s.context).toEqual({ path: "z" });
    expect(fx).toEqual([]);
  });
});

describe("persistence workflows", () => {
  test("a restored snapshot answers tags, can and matches like the original", () => {
    /** Verifies: XSTA-PUR-004, XSTA-ACT-006. Seam: persistence x query surface */
    const m = createMachine({
      initial: "docked",
      states: {
        docked: { on: { CAST_OFF: "sailing" } },
        sailing: { tags: ["underway"], on: { DOCK: "docked" } },
      },
    });
    const a = createActor(m).start();
    a.send({ type: "CAST_OFF" });
    const saved = JSON.parse(JSON.stringify(a.getPersistedSnapshot()));
    a.stop();
    const b = createActor(m, { snapshot: saved }).start();
    const s = b.getSnapshot();
    expect(s.hasTag("underway")).toBe(true);
    expect(s.matches("sailing")).toBe(true);
    expect(s.can({ type: "DOCK" })).toBe(true);
    expect(s.can({ type: "CAST_OFF" })).toBe(false);
  });
});

describe("end-to-end workflows", () => {
  test("an order fulfilment machine runs from input to completion across every projection", async () => {
    /** Verifies: XSTA-ACT-007, XSTA-GRD-001, XSTA-AXN-003, XSTA-HPH-001, XSTA-FIN-002, XSTA-FIN-004, XSTA-FIN-005, XSTA-ACT-006. Seam: input x guards x hierarchy x completion x promise */
    const m = createMachine({
      context: ({ input }: any) => ({ sku: input.sku, qty: input.qty, picked: 0 }),
      initial: "intake",
      states: {
        intake: {
          on: {
            APPROVE: [
              { guard: ({ context }: any) => context.qty > 0, target: "fulfil" },
              { target: "rejected" },
            ],
          },
        },
        fulfil: {
          initial: "picking",
          states: {
            picking: {
              tags: ["busy"],
              on: {
                PICK: [
                  {
                    guard: ({ context, event }: any) => context.picked + event.n >= context.qty,
                    target: "packing",
                    actions: assign({ picked: ({ context, event }: any) => context.picked + event.n }),
                  },
                  { actions: assign({ picked: ({ context, event }: any) => context.picked + event.n }) },
                ],
              },
            },
            packing: { on: { SEAL: "shipped" } },
            shipped: { type: "final" },
          },
          onDone: "closed",
        },
        rejected: { type: "final" },
        closed: { type: "final" },
      },
      output: ({ context }: any) => ({ sku: context.sku, picked: context.picked }),
    });
    const actor = createActor(m, { input: { sku: "TILE-7", qty: 5 } });
    const settled = toPromise(actor);
    actor.start();
    expect(actor.getSnapshot().value).toBe("intake");
    actor.send({ type: "APPROVE" });
    expect(actor.getSnapshot().value).toEqual({ fulfil: "picking" });
    expect(actor.getSnapshot().hasTag("busy")).toBe(true);
    actor.send({ type: "PICK", n: 2 });
    expect(actor.getSnapshot().matches({ fulfil: "picking" })).toBe(true);
    expect(actor.getSnapshot().context).toEqual({ sku: "TILE-7", qty: 5, picked: 2 });
    actor.send({ type: "PICK", n: 3 });
    expect(actor.getSnapshot().value).toEqual({ fulfil: "packing" });
    expect(actor.getSnapshot().can({ type: "SEAL" })).toBe(true);
    actor.send({ type: "SEAL" });
    expect(actor.getSnapshot().value).toBe("closed");
    expect(actor.getSnapshot().status).toBe("done");
    expect(await settled).toEqual({ sku: "TILE-7", picked: 5 });
  });

  test("a batch pipeline persists mid-flight and finishes on a simulated clock", () => {
    /** Verifies: XSTA-PUR-004, XSTA-INV-004, XSTA-TMR-001, XSTA-TMR-002, XSTA-FIN-004. Seam: persistence x timers x completion */
    const m = createMachine({
      context: { loads: 0 },
      initial: "load",
      states: {
        load: {
          on: {
            ADD: { actions: assign({ loads: ({ context }: any) => context.loads + 1 }) },
            SEAL: "bake",
          },
        },
        bake: { after: { 500: "cool" } },
        cool: { after: { 200: "unload" } },
        unload: { type: "final" },
      },
      output: ({ context }: any) => ({ loads: context.loads }),
    });
    const first = createActor(m).start();
    first.send({ type: "ADD" });
    first.send({ type: "ADD" });
    const saved = JSON.parse(JSON.stringify(first.getPersistedSnapshot()));
    first.stop();

    const clock = new SimulatedClock();
    const second = createActor(m, { clock, snapshot: saved }).start();
    expect(second.getSnapshot().value).toBe("load");
    expect(second.getSnapshot().context).toEqual({ loads: 2 });
    second.send({ type: "SEAL" });
    clock.increment(499);
    expect(second.getSnapshot().value).toBe("bake");
    clock.increment(1);
    expect(second.getSnapshot().value).toBe("cool");
    clock.increment(200);
    expect(second.getSnapshot().status).toBe("done");
    expect(second.getSnapshot().output).toEqual({ loads: 2 });
  });

  test("a launch checklist coordinates parallel regions, timers and completion output", () => {
    /** Verifies: XSTA-HPH-003, XSTA-GRD-002, XSTA-TMR-001, XSTA-FIN-002, XSTA-FIN-003, XSTA-FIN-004. Seam: parallel x stateIn x timers x completion */
    const m = createMachine({
      initial: "prep",
      states: {
        prep: {
          type: "parallel",
          states: {
            fueling: {
              initial: "pumping",
              states: { pumping: { after: { 300: "fueled" } }, fueled: { type: "final" } },
            },
            crew: {
              initial: "waiting",
              states: {
                waiting: {
                  on: { BOARD: { guard: stateIn({ prep: { fueling: "fueled" } }), target: "seated" } },
                },
                seated: { type: "final" },
              },
            },
          },
          onDone: "countdown",
        },
        countdown: { after: { 100: "liftoff" } },
        liftoff: { type: "final", output: () => ({ mission: "go" }) },
      },
      output: ({ event }: any) => ({ verdict: event.output.mission }),
    });
    const clock = new SimulatedClock();
    const a = createActor(m, { clock }).start();
    a.send({ type: "BOARD" });
    expect(a.getSnapshot().value).toEqual({ prep: { fueling: "pumping", crew: "waiting" } });
    clock.increment(300);
    expect(a.getSnapshot().value).toEqual({ prep: { fueling: "fueled", crew: "waiting" } });
    a.send({ type: "BOARD" });
    expect(a.getSnapshot().value).toBe("countdown");
    clock.increment(100);
    expect(a.getSnapshot().value).toBe("liftoff");
    expect(a.getSnapshot().status).toBe("done");
    expect(a.getSnapshot().output).toEqual({ verdict: "go" });
  });

  test("pure stepping replays an actor's full run to an identical terminal snapshot", () => {
    /** Verifies: XSTA-INV-001, XSTA-PUR-001, XSTA-PUR-003, XSTA-FIN-004. Seam: pure step x actor loop x completion */
    const m = createMachine({
      context: { hops: [] as string[] },
      initial: "gate",
      states: {
        gate: {
          on: {
            TOKEN: [
              {
                guard: ({ event }: any) => event.kind === "gold",
                target: "vault",
                actions: assign({ hops: ({ context }: any) => [...context.hops, "gold"] }),
              },
              { actions: assign({ hops: ({ context }: any) => [...context.hops, "dud"] }) },
            ],
          },
        },
        vault: { on: { LOCK: { target: "sealed", actions: raise({ type: "AUDIT" }) } }, },
        sealed: { on: { AUDIT: "certified" } },
        certified: { type: "final" },
      },
      output: ({ context }: any) => ({ trail: context.hops }),
    });
    const events = [
      { type: "TOKEN", kind: "lead" },
      { type: "TOKEN", kind: "gold" },
      { type: "LOCK" },
    ];
    const actor = createActor(m).start();
    let pure = getInitialSnapshot(m);
    for (const e of events) {
      actor.send(e as any);
      pure = getNextSnapshot(m, pure, e as any);
    }
    const live = actor.getSnapshot();
    expect(pure.value).toEqual(live.value);
    expect(pure.context).toEqual(live.context);
    expect(pure.status).toBe(live.status);
    expect(pure.output).toEqual(live.output);
    expect(live.value).toBe("certified");
    expect(live.status).toBe("done");
    expect(live.output).toEqual({ trail: ["dud", "gold"] });
  });
});
