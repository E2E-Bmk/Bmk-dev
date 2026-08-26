// Oracle - atomic tests for plugin gating; this file never loads any plugin.
import { describe, expect, test } from "vitest";
import { produce, produceWithPatches, applyPatches, isDraft } from "immer";

describe("plugin gating", () => {
  test("produceWithPatches throws before the patches plugin is loaded", () => {
    /** Verifies: IMM-PATCH-001 */
    expect(() =>
      produceWithPatches({ a: 1 }, (d) => {
        d.a = 2;
      }),
    ).toThrow(Error);
  });

  test("applyPatches throws before the patches plugin is loaded", () => {
    /** Verifies: IMM-PATCH-001 */
    expect(() => applyPatches({ a: 1 }, [])).toThrow(Error);
  });

  test("a patch listener on produce throws before the patches plugin is loaded", () => {
    /** Verifies: IMM-PATCH-001 */
    expect(() =>
      produce(
        { a: 1 },
        (d) => {
          d.a = 2;
        },
        () => {},
      ),
    ).toThrow(Error);
  });

  test("producing over a Map throws before the map-set plugin is loaded", () => {
    /** Verifies: IMM-MAPSET-001 */
    expect(() => produce(new Map(), () => {})).toThrow(Error);
  });

  test("producing over a Set throws before the map-set plugin is loaded", () => {
    /** Verifies: IMM-MAPSET-001 */
    expect(() => produce(new Set(), () => {})).toThrow(Error);
  });

  test("without the array-methods plugin search callbacks receive drafts", () => {
    /** Verifies: IMM-ARR-001 */
    const base = { arr: [{ v: 1 }, { v: 2 }] };
    const next = produce(base, (d) => {
      const seen: boolean[] = [];
      const found = d.arr.find((item) => {
        seen.push(isDraft(item));
        return item.v === 2;
      })!;
      expect(seen).toEqual([true, true]);
      expect(isDraft(found)).toBe(true);
      found.v = 20;
    });
    expect(next.arr.map((x) => x.v)).toEqual([1, 20]);
    expect(base.arr.map((x) => x.v)).toEqual([1, 2]);
  });
});
