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

      const invalidKeys = ["../foobar", "..:foobar", "../", "..:", ".."];
      for (const key of invalidKeys) {
      }


      it("natively supports maxDepth in getKeys", async () => {
        await ctx.storage.setItem("depth-test/file0.md", "boop");
        await ctx.storage.setItem("depth-test/depth0/file1.md", "boop");
        await ctx.storage.setItem("depth-test/depth0/depth1/file2.md", "boop");
        await ctx.storage.setItem("depth-test/depth0/depth1/file3.md", "boop");

        expect(
          (
            await ctx.driver.getKeys("", {
              maxDepth: 1,
            })
          ).sort(),
        ).toMatchObject(["depth-test/file0.md"]);

        expect(
          (
            await ctx.driver.getKeys("", {
              maxDepth: 2,
            })
          ).sort(),
        ).toMatchObject(["depth-test/depth0/file1.md", "depth-test/file0.md"]);
      });
    },
  });

  const ctx = {} as TestContext;




  afterEach(async () => {
    await ctx.storage?.clear();
    await ctx.storage?.dispose();
    await ctx.driver?.dispose?.();
  });
});
