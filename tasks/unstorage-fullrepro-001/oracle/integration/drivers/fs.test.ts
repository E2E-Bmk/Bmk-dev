import { describe, it, expect, vi, afterEach } from "vitest";
import { resolve } from "node:path";
import { promises as fsPromises } from "node:fs";
import { chmod, stat } from "node:fs/promises";
import { readFile, writeFile, mkdir as ensuredir } from "node:fs/promises";
import { testDriver, type TestContext } from "./utils.ts";
import driver from "unstorage/drivers/fs";
import { createStorage } from "unstorage";

describe("drivers: fs", () => {
  const dir = resolve(__dirname, "tmp/fs");

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
      it("watch filesystem", async () => {
        const watcher = vi.fn();
        await ctx.storage.watch(watcher);
        await ensuredir(resolve(dir, "s1"), { recursive: true });
        await writeFile(resolve(dir, "s1/random_file"), "random", "utf8");
        await new Promise((resolve) => setTimeout(resolve, 500));
        expect(watcher).toHaveBeenCalledWith("update", "s1:random_file");
      });

      const invalidKeys = ["../foobar", "..:foobar", "../", "..:", ".."];
      for (const key of invalidKeys) {
      }


    },
  });

  const ctx = {} as TestContext;




  afterEach(async () => {
    await ctx.storage?.clear();
    await ctx.storage?.dispose();
    await ctx.driver?.dispose?.();
  });
});
