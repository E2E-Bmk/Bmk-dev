import { describe, it, expect } from "vitest";
import vercelRuntimeCacheDriver from "unstorage/drivers/vercel-runtime-cache";
import { testDriver } from "./utils.ts";

describe("drivers: vercel-runtime-cache", async () => {
  testDriver({
    driver: vercelRuntimeCacheDriver({
      base: Math.round(Math.random() * 1_000_000).toString(16),
      // Configure tags so clear() can expire them
      tags: ["unstorage-test"],
    }),
    noKeysSupport: true,
    additionalTests: (c) => {
      it("set/get/has/remove", async () => {
        expect(await c.storage.hasItem("k1")).toBe(false);
        await c.storage.setItem("k1", "v1");
        expect(await c.storage.hasItem("k1")).toBe(true);
        expect(await c.storage.getItem("k1")).toBe("v1");
        await c.storage.removeItem("k1");
        expect(await c.storage.hasItem("k1")).toBe(false);
        expect(await c.storage.getItem("k1")).toBe(null);
      });



    },
  });
});
