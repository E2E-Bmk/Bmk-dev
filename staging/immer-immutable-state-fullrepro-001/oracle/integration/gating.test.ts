// Oracle - integration test for uniform plugin gating; this file never loads any plugin.
import { describe, expect, test } from "vitest";
import { produce, produceWithPatches, applyPatches, createDraft, finishDraft } from "immer";

describe("plugin gating across projections", () => {
  test("every patch and container entry point gates on its plugin uniformly", () => {
    /** Verifies: IMM-CVI-005 */
    expect(() =>
      produceWithPatches({ a: 1 }, (d) => {
        d.a = 2;
      }),
    ).toThrow(Error);
    expect(() => applyPatches({ a: 1 }, [{ op: "replace", path: ["a"], value: 2 }])).toThrow(Error);
    expect(() =>
      produce(
        { a: 1 },
        (d) => {
          d.a = 2;
        },
        () => {},
      ),
    ).toThrow(Error);
    const draft = createDraft({ a: 1 });
    draft.a = 2;
    expect(() => finishDraft(draft, () => {})).toThrow(Error);
    expect(() => produce(new Map([["k", 1]]), (d) => void d.set("j", 2))).toThrow(Error);
    expect(() => produce(new Set([1]), (d) => void d.add(2))).toThrow(Error);
    expect(() => produce({ m: new Map() }, (d) => void d.m.set("k", 1))).toThrow(Error);
    const plainStillWorks = produce({ a: 1 }, (d) => {
      d.a = 3;
    });
    expect(plainStillWorks).toEqual({ a: 3 });
  });
});
