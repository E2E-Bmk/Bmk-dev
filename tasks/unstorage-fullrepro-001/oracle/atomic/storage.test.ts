import { describe, it, expect, vi } from "vitest";
import { resolve } from "node:path";
import { createStorage, snapshot, restoreSnapshot, prefixStorage } from "unstorage";
import memory from "unstorage/drivers/memory";
import fs from "unstorage/drivers/fs";

const data = {
  "etc:conf": "test",
  "data:foo": 123,
};

describe("storage", () => {


  it("snapshot", async () => {
    const storage = createStorage();
    await restoreSnapshot(storage, data);
    expect(await snapshot(storage, "")).toMatchObject(data);
  });




});

describe("utils", () => {



  it("has aliases", async () => {
    const storage = createStorage();

    await storage.setItem("foo", "bar");
    expect(await storage.has("foo")).toBe(true);
    expect(await storage.get("foo")).toBe("bar");
    expect(await storage.keys()).toEqual(["foo"]);
    await storage.del("foo");
    expect(await storage.has("foo")).toBe(false);
    await storage.setItem("bar", "baz");
    await storage.remove("bar");
    expect(await storage.has("bar")).toBe(false);
  });
});

describe("Regression", () => {
  it("setItems doeesn't upload twice", async () => {
    /**
     * https://github.com/unjs/unstorage/pull/392
     */

    const setItem = vi.fn();
    const setItems = vi.fn();

    const driver = memory();
    const storage = createStorage({
      driver: {
        ...driver,
        setItem: (...args) => {
          setItem(...args);
          return driver.setItem?.(...args);
        },
        setItems: (...args) => {
          setItems(...args);
          return driver.setItems?.(...args);
        },
      },
    });

    await storage.setItems([{ key: "foo.txt", value: "bar" }]);
    expect(setItem).toHaveBeenCalledTimes(0);
    expect(setItems).toHaveBeenCalledTimes(1);
  });




});
