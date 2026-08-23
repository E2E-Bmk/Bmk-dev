import { describe, it, expect } from "vitest";
import { resolve } from "node:path";
import { chmod, stat } from "node:fs/promises";
import { readFile } from "node:fs/promises";
import { testDriver } from "./utils.ts";
import driver from "unstorage/drivers/fs-lite";

describe("drivers: fs-lite", () => {
  const dir = resolve(__dirname, "tmp/fs-lite");

  testDriver({
    driver: driver({ base: dir }),
    additionalTests(ctx) {
      it("check filesystem", async () => {
        await ctx.storage.setItem("s1:a", "test_data");
        expect(await readFile(resolve(dir, "s1/a"), "utf8")).toBe("test_data");
      });
      it("native meta", async () => {
        await ctx.storage.setItem("s1:a", "test_data");
        const meta = await ctx.storage.getMeta("/s1/a");
        expect(meta.atime?.constructor.name).toBe("Date");
        expect(meta.mtime?.constructor.name).toBe("Date");
        expect(meta.size).toBeGreaterThan(0);
      });

      const invalidKeys = ["../foobar", "..:foobar", "../", "..:", ".."];
      for (const key of invalidKeys) {
      }


    },
  });
});
