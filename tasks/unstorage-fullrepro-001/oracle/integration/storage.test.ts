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
  it("mount/unmount", async () => {
    const storage = createStorage().mount("/mnt", memory());
    await restoreSnapshot(storage, data, "mnt");
    expect(await snapshot(storage, "/mnt")).toMatchObject(data);
  });



  it("watch", async () => {
    const onChange = vi.fn();
    const storage = createStorage().mount("/mnt", memory());
    await storage.watch(onChange);
    await restoreSnapshot(storage, data, "mnt");
    expect(onChange).toHaveBeenCalledWith("update", "mnt:etc:conf");
    expect(onChange).toHaveBeenCalledWith("update", "mnt:data:foo");
    expect(onChange).toHaveBeenCalledTimes(2);
  });

  it("unwatch return", async () => {
    const onChange = vi.fn();
    const storage = createStorage().mount("/mnt", memory());
    const unwatch = await storage.watch(onChange);
    await storage.setItem("mnt:data:foo", 42);
    await unwatch();
    await storage.setItem("mnt:data:foo", 41);
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("unwatch all", async () => {
    const onChange = vi.fn();
    const storage = createStorage().mount("/mnt", memory());
    await storage.watch(onChange);
    await storage.setItem("mnt:data:foo", 42);
    await storage.unwatch();
    await storage.setItem("mnt:data:foo", 41);
    expect(onChange).toHaveBeenCalledTimes(1);
  });

});

describe("utils", () => {
  it("prefixStorage", async () => {
    const storage = createStorage();
    const pStorage = prefixStorage(storage, "foo");
    await pStorage.setItem("x", "bar");
    await pStorage.setItem("y", "baz");
    expect(await storage.getItem("foo:x")).toBe("bar");
    expect(await pStorage.getItem("x")).toBe("bar");
    expect(await pStorage.getKeys()).toStrictEqual(["x", "y"]);

    // Higher order storage
    const secondStorage = createStorage();
    secondStorage.mount("/mnt", storage);
    const mntStorage = prefixStorage(secondStorage, "mnt");

    expect(await mntStorage.getKeys()).toStrictEqual(["foo:x", "foo:y"]);
    // Get keys from sub-storage
    expect(await mntStorage.getKeys("foo")).toStrictEqual(["foo:x", "foo:y"]);
  });

  it("prefixStorage watch strips base from callback key", async () => {
    const storage = createStorage();
    const pStorage = prefixStorage(storage, "foo");
    const onChange = vi.fn();

    await pStorage.watch(onChange);
    await pStorage.setItem("x", "bar");
    await storage.setItem("foo:y", "baz");
    await storage.setItem("bar:x", "ignored");
    await pStorage.removeItem("x");

    expect(onChange).toHaveBeenCalledWith("update", "x");
    expect(onChange).toHaveBeenCalledWith("update", "y");
    expect(onChange).toHaveBeenCalledWith("remove", "x");
    expect(onChange).toHaveBeenCalledTimes(3);
  });


});

describe("Regression", () => {

  it("prefixed storage supports aliases", async () => {
    const storage = createStorage();
    const pStorage = prefixStorage(storage, "foo");

    await pStorage.set("x", "foo");
    await pStorage.set("y", "bar");

    expect(await pStorage.get("x")).toBe("foo");
    expect(await pStorage.get("x")).toBe("foo");
    expect(await pStorage.has("x")).toBe(true);
    expect(await pStorage.get("y")).toBe("bar");

    expect(await pStorage.keys()).toStrictEqual(["x", "y"]);

    await pStorage.del("x");
    expect(await pStorage.has("x")).toBe(false);

    await pStorage.remove("y");
    expect(await pStorage.has("y")).toBe(false);
  });

  it("getKeys supports maxDepth with mixed native support", async () => {
    const base = resolve(__dirname, "tmp/fs");
    const mainStorage = memory();
    const secondaryStorage = fs({ base });
    const storage = createStorage({ driver: mainStorage });

    storage.mount("/storage_b", secondaryStorage);

    try {
      await storage.setItem("/storage_a/file_depth1", "contents");
      await storage.setItem("/storage_a/depth1/file_depth2", "contents");
      await storage.setItem("/storage_b/file_depth1", "contents");
      await storage.setItem("/storage_b/depth1/file_depth2", "contents");

      const keys = await storage.getKeys(undefined, { maxDepth: 1 });

      expect(keys.sort()).toMatchObject(["storage_a:file_depth1", "storage_b:file_depth1"]);
    } finally {
      await storage.clear();
    }
  });

  it("prefixStorage getItems to not returns null (issue #396)", async () => {
    const storage = createStorage();
    await storage.setItem("namespace:key", "value");

    const plainResult = await storage.getItems(["namespace:key"]);
    expect(plainResult).toEqual([{ key: "namespace:key", value: "value" }]);

    const prefixed = prefixStorage(storage, "namespace");

    const prefixedResult = await prefixed.getItems(["key"]);
    expect(prefixedResult).toEqual([{ key: "key", value: "value" }]);
  });

  it("prefixStorage setItems works correctly (related to issue #396)", async () => {
    const storage = createStorage();

    const prefixed = prefixStorage(storage, "namespace");

    await prefixed.setItems([
      { key: "key1", value: "value1" },
      { key: "key2", value: "value2" },
    ]);

    const plainResult = await storage.getItems(["namespace:key1", "namespace:key2"]);
    expect(plainResult).toEqual([
      { key: "namespace:key1", value: "value1" },
      { key: "namespace:key2", value: "value2" },
    ]);

    const prefixedResult = await prefixed.getItems(["key1", "key2"]);
    expect(prefixedResult).toEqual([
      { key: "key1", value: "value1" },
      { key: "key2", value: "value2" },
    ]);
  });
});
