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

      const invalidKeys = ["../foobar", "..:foobar", "../", "..:", ".."];
      for (const key of invalidKeys) {
      }


      it("natively supports maxDepth in getKeys", async () => {
        await ctx.storage.setItem("file0.md", "boop");
        await ctx.storage.setItem("depth-test/file1.md", "boop");
        await ctx.storage.setItem("depth-test/depth0/file2.md", "boop");
        await ctx.storage.setItem("depth-test/depth0/depth1/file3.md", "boop");
        await ctx.storage.setItem("depth-test/depth0/depth1/file4.md", "boop");

        expect(
          (
            await ctx.driver.getKeys("", {
              maxDepth: 0,
            })
          ).sort(),
        ).toMatchObject(["file0.md"]);
        expect(
          (
            await ctx.driver.getKeys("", {
              maxDepth: 1,
            })
          ).sort(),
        ).toMatchObject(["depth-test/file1.md", "file0.md"]);
        expect(
          (
            await ctx.driver.getKeys("", {
              maxDepth: 2,
            })
          ).sort(),
        ).toMatchObject(["depth-test/depth0/file2.md", "depth-test/file1.md", "file0.md"]);
      });
    },
  });
});
