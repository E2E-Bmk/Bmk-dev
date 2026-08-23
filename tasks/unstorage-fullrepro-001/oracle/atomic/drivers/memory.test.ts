import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { createStorage, restoreSnapshot } from "unstorage";
import memory from "unstorage/drivers/memory";

describe("drivers: memory", () => {
  let driver: ReturnType<typeof memory>;
  let storage: ReturnType<typeof createStorage>;

  beforeAll(() => {
    driver = memory();
    storage = createStorage({ driver });
  });

  afterAll(async () => {
    await driver.dispose?.();
    await storage.dispose?.();
  });

  afterEach(async () => {
    await storage.clear();
  });

  it("initial state", async () => {
    expect(await storage.hasItem("s1:a")).toBe(false);
    expect(await storage.getItem("s2:a")).toBe(null);
    expect(await storage.getKeys()).toMatchObject([]);
  });

  it("setItem", async () => {
    await storage.setItem("s1:a", "test_data");
    await storage.setItem("s2:a", "test_data");
    await storage.setItem("s3:a?q=1", "test_data");
    expect(await storage.hasItem("s1:a")).toBe(true);
    expect(await storage.getItem("s1:a")).toBe("test_data");
    expect(await storage.getItem("s3:a?q=2")).toBe("test_data");
  });

  it("getKeys", async () => {
    await storage.setItem("s1:a", "test_data");
    await storage.setItem("s2:a", "test_data");
    await storage.setItem("s3:a?q=1", "test_data");
    expect(await storage.getKeys().then((k) => k.sort())).toMatchObject(["s1:a", "s2:a", "s3:a"].sort());
    expect(await storage.getKeys("s1").then((k) => k.sort())).toMatchObject(["s1:a"].sort());
  });

  it("getKeys with depth", async () => {
    await storage.setItem("depth0_0", "test_data");
    await storage.setItem("depth0:depth1:depth2_0", "test_data");
    await storage.setItem("depth0:depth1:depth2_1", "test_data");
    await storage.setItem("depth0:depth1_0", "test_data");
    await storage.setItem("depth0:depth1_1", "test_data");
    expect(await storage.getKeys(undefined, { maxDepth: 0 })).toMatchObject(["depth0_0"]);
    expect((await storage.getKeys(undefined, { maxDepth: 1 })).sort()).toMatchObject(["depth0:depth1_0", "depth0:depth1_1", "depth0_0"]);
    expect((await storage.getKeys(undefined, { maxDepth: 2 })).sort()).toMatchObject(["depth0:depth1:depth2_0", "depth0:depth1:depth2_1", "depth0:depth1_0", "depth0:depth1_1", "depth0_0"]);
  });

  it("serialize (object)", async () => {
    await storage.setItem("/data/test.json", { json: "works" });
    expect(await storage.getItem("/data/test.json")).toMatchObject({ json: "works" });
  });

  it("serialize (primitive)", async () => {
    await storage.setItem("/data/true.json", true);
    expect(await storage.getItem("/data/true.json")).toBe(true);
  });

  it("serialize (lossy object with toJSON())", async () => {
    class Test1 { toJSON() { return "SERIALIZED"; } }
    await storage.setItem("/data/serialized1.json", new Test1());
    expect(await storage.getItem("/data/serialized1.json")).toBe("SERIALIZED");
    class Test2 { toJSON() { return { serializedObj: "works" }; } }
    await storage.setItem("/data/serialized2.json", new Test2());
    expect(await storage.getItem("/data/serialized2.json")).toMatchObject({ serializedObj: "works" });
  });

  it("raw support", async () => {
    const value = new Uint8Array([1, 2, 3]);
    await storage.setItemRaw("/data/raw.bin", value);
    const rValue = await storage.getItemRaw("/data/raw.bin");
    const rValueLen = rValue?.length || rValue?.byteLength;
    expect(rValueLen).toBe(value.length);
    expect(Buffer.from(rValue).toString("base64")).toBe(Buffer.from(value).toString("base64"));
  });

  it("setItems", async () => {
    await storage.setItems([{ key: "t:1", value: "test_data_t1" }, { key: "t:2", value: "test_data_t2" }, { key: "t:3", value: "test_data_t3" }]);
    expect(await storage.getItem("t:1")).toBe("test_data_t1");
    expect(await storage.getItem("t:2")).toBe("test_data_t2");
    expect(await storage.getItem("t:3")).toBe("test_data_t3");
  });

  it("getItems", async () => {
    await storage.setItem("v3:a?q=1", "test_data_v3:a?q=1");
    await storage.setItem("v2:a", "test_data_v2:a");
    await storage.setItem("v1:a", "test_data_v1:a");
    expect(await storage.getItems([{ key: "v1:a" }, "v2:a", { key: "v3:a?q=1" }, "v4:undefined"])).toMatchObject([
      { key: "v1:a", value: "test_data_v1:a" },
      { key: "v2:a", value: "test_data_v2:a" },
      { key: "v3:a", value: "test_data_v3:a?q=1" },
      { key: "v4:undefined", value: null },
    ]);
  });

  it("getItem - return falsy values when set in storage", async () => {
    await storage.setItem("zero", 0);
    expect(await storage.getItem("zero")).toBe(0);
    await storage.setItem("my-false-flag", false);
    expect(await storage.getItem("my-false-flag")).toBe(false);
  });

  it("removeItem", async () => {
    await storage.removeItem("s1:a", false);
    expect(await storage.hasItem("s1:a")).toBe(false);
    expect(await storage.getItem("s1:a")).toBe(null);
  });

  it("clear", async () => {
    await storage.clear();
    expect(await storage.getKeys()).toMatchObject([]);
    await storage.clear();
    expect(await storage.getKeys()).toMatchObject([]);
  });
});
