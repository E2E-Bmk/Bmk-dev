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

  it("init", async () => {
    await restoreSnapshot(storage, { initial: "works" });
    expect(await storage.getItem("initial")).toBe("works");
    await storage.clear();
  });
});
